"""Volume, mileage and carbon-value scenarios for EPA model-year production cohorts."""

import csv
from itertools import permutations
from math import fsum, isclose
from pathlib import Path

from scripts.analyze import ROOT, YEARS, fleet_rate, read_panel, write_csv

MILES = 10_000
GRAMS_PER_TONNE = 1_000_000
GRAMS_PER_MEGATONNE = 1_000_000_000_000
# EPA (2024), printed p.93. These are regulatory lifetime distances.
CAR_MILES, TRUCK_MILES = 195_264, 225_865
CAR_TYPES = {"Sedan/Wagon", "Car SUV"}
# Rennert et al. (2022), 2020 emissions pulse, in 2020 US dollars.
CARBON_VALUES = {"5th percentile": 44, "mean": 185, "95th percentile": 413}


def read_production(path):
    production = {}
    with path.open(encoding="utf-8", newline="") as stream:
        for row in csv.DictReader(stream):
            year, count = int(row["year"]), int(row["vehicles"])
            if year in production or count <= 0:
                raise ValueError(f"Invalid or duplicated production count in {year}")
            production[year] = count
    if set(production) != set(YEARS):
        raise ValueError("The production series must cover all 14 study years")
    return production


def cohort_mass(count, shares, rates):
    """Megatonnes emitted if every vehicle in a production cohort travels 10,000 miles."""
    return count * fleet_rate(rates, shares) * MILES / GRAMS_PER_MEGATONNE


def factor_contributions(first_count, last_count, start, end):
    """Average marginal changes across all six scale, mix and rate update orders."""
    first = {"volume": first_count, "shares": start, "rates": start}
    last = {"volume": last_count, "shares": end, "rates": end}
    increments = {name: [] for name in first}
    for order in permutations(first):
        state = first.copy()
        previous = cohort_mass(state["volume"], state["shares"], state["rates"])
        for factor in order:
            state[factor] = last[factor]
            current = cohort_mass(state["volume"], state["shares"], state["rates"])
            increments[factor].append(current - previous)
            previous = current
    totals = {factor: fsum(changes) / len(changes) for factor, changes in increments.items()}
    net = cohort_mass(last_count, end, end) - cohort_mass(first_count, start, start)
    if not isclose(fsum(totals.values()), net, abs_tol=1e-10, rel_tol=0):
        raise ArithmeticError("Volume, mix and rate contributions do not reconcile")
    return {**totals, "net": net}


def lifetime_scenario(rates, shares):
    """Compare production baskets using class-specific hypothetical lifetime miles."""
    distances = {name: CAR_MILES if name in CAR_TYPES else TRUCK_MILES for name in shares}
    miles = fsum(shares[name].share * distance for name, distance in distances.items())
    grams = fsum(shares[name].share * distance * rates[name].rate for name, distance in distances.items())
    return {
        "miles_per_vehicle": miles,
        "tonnes_per_vehicle": grams / GRAMS_PER_TONNE,
        "grams_per_mile": grams / miles,
    }


def run(data_dir: Path, results_dir: Path):
    panel, _, _ = read_panel(data_dir)
    counts = read_production(data_dir / "production.csv")
    base, end = panel[2010], panel[2023]
    years = []
    for year in YEARS:
        count, types = counts[year], panel[year]
        rate = fleet_rate(types, types)
        fixed_mass = cohort_mass(count, base, types)
        actual_mass = cohort_mass(count, types, types)
        years.append({"year": year, "vehicles": count, "miles_per_vehicle": MILES,
                      "rate_g_per_mile": rate, "actual_mix_megatonnes": actual_mass,
                      "fixed_2010_mix_megatonnes": fixed_mass,
                      "mix_gap_megatonnes": actual_mass - fixed_mass})
    change = factor_contributions(counts[2010], counts[2023], base, end)
    lifetime = [{"production_mix": mix, **lifetime_scenario(end, shares)}
                for mix, shares in (("actual_2023", end), ("fixed_2010", base))]
    gap_tonnes = (fleet_rate(end, end) - fleet_rate(end, base)) * MILES / GRAMS_PER_TONNE
    valuations = [{"published_statistic": label, "usd_2020_per_tonne": price,
                   "extra_tonnes_per_vehicle": gap_tonnes,
                   "implied_usd_2020_per_vehicle": price * gap_tonnes}
                  for label, price in CARBON_VALUES.items()]
    results_dir.mkdir(exist_ok=True, parents=True)
    write_csv(results_dir / "cohorts.csv", years)
    write_csv(results_dir / "cohort_decomposition.csv",
              [{"factor": name, "megatonnes": value} for name, value in change.items()])
    write_csv(results_dir / "lifetime_mileage.csv", lifetime)
    write_csv(results_dir / "carbon_benchmark.csv", valuations)


if __name__ == "__main__":
    run(ROOT / "data", ROOT / "results")
