"""Attribute changes in U.S. new-vehicle tailpipe CO2 to rates and production mix."""

import argparse
import csv
import math
import tempfile
from dataclasses import dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
YEARS = range(2010, 2024)
TYPES = ("Sedan/Wagon", "Car SUV", "Truck SUV", "Minivan/Van", "Pickup")
PERIODS = ((2010, 2023), (2010, 2019), (2019, 2023), (2013, 2023))


@dataclass(frozen=True)
class Group:
    share: float  # Fraction, normalized to sum to one within a model year.
    rate: float  # Grams of tailpipe CO2 per mile.


def read_panel(data_dir):
    raw = {year: {} for year in YEARS}
    with (data_dir / "vehicle_types.csv").open(newline="", encoding="utf-8") as stream:
        for row in csv.DictReader(stream):
            year, name = int(row["year"]), row["vehicle_type"]
            if year not in raw or name not in TYPES or name in raw[year]:
                raise ValueError(
                    f"Unexpected or duplicate vehicle group: {year} {name}"
                )
            pct, rate = float(row["production_share_pct"]), float(row["co2_g_per_mile"])
            if not 0 <= pct <= 100 or not math.isfinite(rate) or rate < 0:
                raise ValueError(f"Invalid share or emissions rate: {year} {name}")
            raw[year][name] = (pct, rate)

    panel, totals = {}, {}
    for year, records in raw.items():
        if set(records) != set(TYPES):
            raise ValueError(
                f"Missing vehicle types in {year}: {sorted(set(TYPES) - set(records))}"
            )
        total = math.fsum(pct for pct, _ in records.values())
        # Each of the five printed percentages was rounded to 0.1 percentage point.
        if abs(total - 100) > len(TYPES) * 0.05 + 1e-10:
            raise ValueError(f"Implausible production share sum in {year}: {total}")
        totals[year] = total
        panel[year] = {
            name: Group(pct / total, rate) for name, (pct, rate) in records.items()
        }

    benchmarks = {}
    with (data_dir / "fleet.csv").open(newline="", encoding="utf-8") as stream:
        for row in csv.DictReader(stream):
            year, rate = int(row["year"]), float(row["co2_g_per_mile"])
            if (
                year not in raw
                or year in benchmarks
                or not math.isfinite(rate)
                or rate < 0
            ):
                raise ValueError(f"Invalid or duplicate EPA fleet benchmark: {year}")
            benchmarks[year] = rate
    if set(benchmarks) != set(YEARS):
        raise ValueError(
            "EPA fleet benchmarks must cover every model year from 2010 to 2023"
        )
    return panel, totals, benchmarks


def fleet_rate(groups, weights):
    """Weight the first mapping's rates by the second mapping's production shares."""
    return math.fsum(group.rate * weights[name].share for name, group in groups.items())


def components(first, last, method):
    """Return within-type and mix contributions for a single type and ordering."""
    if method == "rates_first":
        weight, rate = first.share, last.rate
    elif method == "shares_first":
        weight, rate = last.share, first.rate
    elif method == "symmetric":
        weight = (first.share + last.share) / 2
        rate = (first.rate + last.rate) / 2
    else:
        raise ValueError(f"Unknown decomposition method: {method}")
    return weight * (last.rate - first.rate), rate * (last.share - first.share)


def decompose(start, end, method):
    pairs = [components(start[name], end[name], method) for name in start]
    within = math.fsum(pair[0] for pair in pairs)
    mix = math.fsum(pair[1] for pair in pairs)
    net = fleet_rate(end, end) - fleet_rate(start, start)
    if not math.isclose(within + mix, net, abs_tol=1e-10, rel_tol=0):
        raise ArithmeticError("Decomposition failed to reproduce the fleet change")
    return within, mix, net


def annual_series(panel, totals, benchmarks):
    rows = []
    for year, groups in panel.items():
        actual = fleet_rate(groups, groups)
        fixed = fleet_rate(groups, panel[YEARS.start])
        discrepancy = actual - benchmarks[year]
        # Both sets of rates are rounded to 1 g/mi. A reported type share can
        # differ from its true fraction by 0.0005. Centering its rate at
        # 'actual' cancels the normalization term in this error bound.
        rounding_bound = 1 + 0.0005 * sum(
            abs(group.rate - actual) for group in groups.values()
        )
        if abs(discrepancy) > rounding_bound + 1e-10:
            raise ValueError(
                f"Reconstructed rate disagrees with Table 3.1 in {year}: {discrepancy:+.3f} g/mi"
            )
        rows.append(
            {
                "year": year,
                "reported_share_total_pct": totals[year],
                "epa_g_per_mile": benchmarks[year],
                "actual_g_per_mile": actual,
                "fixed_2010_mix_g_per_mile": fixed,
                "actual_minus_fixed_g_per_mile": actual - fixed,
                "actual_minus_epa_g_per_mile": discrepancy,
            }
        )
    return rows


def period_decompositions(panel):
    rows = []
    for start, end in PERIODS:
        changes = {
            method: decompose(panel[start], panel[end], method)
            for method in ("symmetric", "rates_first", "shares_first")
        }
        steps = [
            decompose(panel[y], panel[y + 1], "symmetric") for y in range(start, end)
        ]
        changes["annual_chained"] = tuple(math.fsum(column) for column in zip(*steps))
        for method, (within, mix, net) in changes.items():
            rows.append(
                {
                    "start_year": start,
                    "end_year": end,
                    "method": method,
                    "within_g_per_mile": within,
                    "mix_g_per_mile": mix,
                    "net_g_per_mile": net,
                }
            )
    return rows


def by_vehicle_type(start, end):
    rows = []
    # A common reference gives each changing share a meaningful comparator;
    # all share changes sum to zero, so this leaves the total mix effect intact.
    reference = (fleet_rate(start, start) + fleet_rate(end, end)) / 2
    for name in TYPES:
        first, last = start[name], end[name]
        within, mix = components(first, last, "symmetric")
        centered = mix - reference * (last.share - first.share)
        rows.append(
            {
                "vehicle_type": name,
                "start_share_pct": 100 * first.share,
                "end_share_pct": 100 * last.share,
                "start_g_per_mile": first.rate,
                "end_g_per_mile": last.rate,
                "within_g_per_mile": within,
                "mix_g_per_mile": mix,
                "net_g_per_mile": within + mix,
                "centered_mix_g_per_mile": centered,
            }
        )
    return rows


def valuation(gap):
    miles = 10_000
    tonnes = miles * gap / 1_000_000
    return [
        {
            "miles": miles,
            "price_usd_per_tonne": price,
            "gap_g_per_mile": gap,
            "tonnes_co2": tonnes,
            "implied_value_usd": price * tonnes,
        }
        for price in (50, 100, 200)
    ]


def write_csv(path, rows):
    with tempfile.TemporaryDirectory(dir=path.parent) as working:
        staged = Path(working) / path.name
        with staged.open("w", newline="", encoding="utf-8") as stream:
            writer = csv.DictWriter(
                stream, fieldnames=list(rows[0]), lineterminator="\n"
            )
            writer.writeheader()
            for row in rows:
                writer.writerow(
                    {
                        key: f"{value:.9f}" if isinstance(value, float) else value
                        for key, value in row.items()
                    }
                )
        staged.replace(path)


def run(data_dir, results_dir):
    panel, totals, benchmarks = read_panel(data_dir)
    annual = annual_series(panel, totals, benchmarks)
    outputs = {
        "annual.csv": annual,
        "decompositions.csv": period_decompositions(panel),
        "vehicle_types.csv": by_vehicle_type(panel[2010], panel[2023]),
        "valuation.csv": valuation(annual[-1]["actual_minus_fixed_g_per_mile"]),
    }
    results_dir.mkdir(parents=True, exist_ok=True)
    for filename, rows in outputs.items():
        write_csv(results_dir / filename, rows)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data-dir", type=Path, default=ROOT / "data")
    parser.add_argument("--results-dir", type=Path, default=ROOT / "results")
    args = parser.parse_args()
    try:
        run(args.data_dir, args.results_dir)
    except (OSError, ValueError, KeyError) as error:
        parser.exit(1, f"Analysis failed: {error}\n")
