"""Standardize model-year 2023 manufacturer CO2 rates to a common vehicle mix."""

import argparse
import csv
import math
from itertools import combinations
from pathlib import Path

if __package__:
    from .analyze import ROOT, TYPES, Group, read_panel, write_csv
else:
    from analyze import ROOT, TYPES, Group, read_panel, write_csv

TWO_TYPES = ("Sedan/Wagon", "Truck SUV")
AGGREGATES = {"Other", "All Manufacturers"}


def load_manufacturers(data_dir):
    with (data_dir / "manufacturers.csv").open(encoding="utf-8", newline="") as stream:
        benchmarks = {}
        for row in csv.DictReader(stream):
            firm = row["manufacturer"]
            rate = float(row["co2_g_per_mile"])
            if firm in benchmarks or not math.isfinite(rate) or rate < 0:
                raise ValueError(f"Invalid manufacturer benchmark: {firm}")
            benchmarks[firm] = rate
    if len(benchmarks.keys() - AGGREGATES) != 14 or not AGGREGATES <= benchmarks.keys():
        raise ValueError("Expected 14 named manufacturers and both aggregate rows")

    panel = {firm: {} for firm in benchmarks}
    with (data_dir / "manufacturer_types.csv").open(
        encoding="utf-8", newline=""
    ) as stream:
        for row in csv.DictReader(stream):
            firm, name = row["manufacturer"], row["vehicle_type"]
            if firm not in panel or name not in TYPES or name in panel[firm]:
                raise ValueError(
                    f"Unexpected or duplicate manufacturer cell: {firm}, {name}"
                )
            pct, rate = row["production_share_pct"], row["co2_g_per_mile"]
            if (pct == "") != (rate == ""):
                raise ValueError(f"Partially missing share and rate: {firm}, {name}")
            if pct == "":
                panel[firm][name] = None
                continue
            share, rate = float(pct) / 100, float(rate)
            if not 0 <= share <= 1 or not math.isfinite(rate) or rate < 0:
                raise ValueError(f"Invalid share or rate: {firm}, {name}")
            panel[firm][name] = Group(share, rate)

    for firm, groups in panel.items():
        if set(groups) != set(TYPES):
            raise ValueError(f"Incomplete source rows: {firm}")
        published = {name: group for name, group in groups.items() if group is not None}
        total = sum(g.share for g in published.values())
        if abs(total - 1) > len(published) * 0.0005 + 1e-10:
            raise ValueError(f"Published shares for {firm} sum to {100 * total:.2f}%")
        own_rate = weighted_rate(published, published, published)
        # As with the national tables, allow rounding of both rate columns
        # and of each observed type share at the source's printed precision.
        tolerance = 1 + 0.0005 * sum(abs(g.rate - own_rate) for g in published.values())
        if abs(own_rate - benchmarks[firm]) > tolerance:
            raise ValueError(f"Manufacturer rate disagrees with Table 3.3 for {firm}")
    return panel, benchmarks


def weighted_rate(rates, weights, types):
    """Normalize weights over the selected types before averaging rates."""
    total = math.fsum(weights[name].share for name in types)
    if total <= 0:
        raise ValueError("Selected vehicle types must have positive total share")
    return math.fsum(rates[name].rate * weights[name].share for name in types) / total


def compare(firm, groups, reference, types):
    observed = weighted_rate(groups, groups, types)
    standardized = weighted_rate(groups, reference, types)
    return {
        "manufacturer": firm,
        "observed_g_per_mile": observed,
        "standardized_g_per_mile": standardized,
        "standardized_minus_observed_g_per_mile": standardized - observed,
    }


def rank_rows(rows):
    """Competition rank on unrounded rates. Lower emissions receive rank one."""
    for field in ("observed", "standardized"):
        levels = sorted(row[f"{field}_g_per_mile"] for row in rows)
        for row in rows:
            value = row[f"{field}_g_per_mile"]
            row[f"{field}_rank"] = 1 + sum(other < value - 1e-10 for other in levels)
    return rows


def pair_gaps(rows):
    pairs = []
    for a, b in combinations(rows, 2):
        observed = a["observed_g_per_mile"] - b["observed_g_per_mile"]
        standard = a["standardized_g_per_mile"] - b["standardized_g_per_mile"]
        pairs.append(
            {
                "manufacturer_a": a["manufacturer"],
                "manufacturer_b": b["manufacturer"],
                "observed_gap_g_per_mile": observed,
                "standardized_gap_g_per_mile": standard,
                "gap_change_g_per_mile": standard - observed,
                "rank_reversal": int(observed * standard < 0),
            }
        )
    return pairs


def run(data_dir: Path, results_dir: Path):
    panel, benchmarks = load_manufacturers(data_dir)
    national, totals, _ = read_panel(data_dir)
    reference = national[2023]
    # The independently extracted national row in Table 3.4 repeats Table 3.2.
    for name, group in reference.items():
        repeated = panel["All Manufacturers"][name]
        if (
            repeated is None
            or repeated.rate != group.rate
            or not math.isclose(
                repeated.share, group.share * totals[2023] / 100, abs_tol=1e-10
            )
        ):
            raise ValueError(f"National reference differs between tables for {name}")

    support, main, rounding_sensitivity, two_types = [], [], [], []
    for firm in sorted(panel.keys() - AGGREGATES):
        groups = panel[firm]
        missing = [name for name in TYPES if groups[name] is None]
        rounded_zero = [
            name
            for name in TYPES
            if groups[name] is not None and groups[name].share == 0
        ]
        supported = [name for name in TYPES if name not in missing + rounded_zero]
        support.append(
            {
                "manufacturer": firm,
                "positive_share_types": len(supported),
                "missing_rate_types": "|".join(missing),
                "rounded_zero_share_types_with_rates": "|".join(rounded_zero),
                "national_mix_covered_by_positive_share_types_pct": 100
                * math.fsum(reference[name].share for name in supported),
                "eligible_five_types": int(len(supported) == len(TYPES)),
            }
        )
        if not missing:
            row = compare(firm, groups, reference, TYPES)
            row["epa_g_per_mile"] = benchmarks[firm]
            rounding_sensitivity.append(
                {**row, "rounded_zero_share_types_with_rates": "|".join(rounded_zero)}
            )
            if not rounded_zero:
                main.append(row)
        if not set(TWO_TYPES) <= set(supported):
            raise ValueError(
                f"Common sedan/wagon and truck SUV support missing for {firm}"
            )
        row = compare(firm, groups, reference, TWO_TYPES)
        # Normalize by the sum of printed portfolio shares since some add to 99.9 or 100.1%.
        total = sum(g.share for g in groups.values() if g is not None)
        row["within_firm_two_type_share_pct"] = (
            100 * sum(groups[k].share for k in TWO_TYPES) / total
        )
        two_types.append(row)

    results_dir.mkdir(parents=True, exist_ok=True)
    write_csv(results_dir / "manufacturer_support.csv", support)
    write_csv(results_dir / "manufacturer_comparisons.csv", rank_rows(main))
    write_csv(results_dir / "manufacturer_pairs.csv", pair_gaps(main))
    write_csv(results_dir / "manufacturer_two_types.csv", rank_rows(two_types))
    write_csv(
        results_dir / "manufacturer_rounded_zero_sensitivity.csv",
        rank_rows(rounding_sensitivity),
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data-dir", type=Path, default=ROOT / "data")
    parser.add_argument("--results-dir", type=Path, default=ROOT / "results")
    args = parser.parse_args()
    try:
        run(args.data_dir, args.results_dir)
    except (OSError, ValueError, KeyError) as error:
        parser.exit(1, f"Manufacturer analysis failed: {error}\n")
