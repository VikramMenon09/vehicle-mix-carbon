"""Check how the endpoint mix estimate depends on SUV groupings and printed precision."""

import json
from pathlib import Path

from scripts.analyze import Group, ROOT, TYPES, decompose, read_panel
from scripts.rounding import mix_bounds


def pool_suvs(groups):
    car, truck = groups["Car SUV"], groups["Truck SUV"]
    share = car.share + truck.share
    rate = (car.rate * car.share + truck.rate * truck.share) / share
    pooled = {k: v for k, v in groups.items() if k not in ("Car SUV", "Truck SUV")}
    pooled["All SUVs"] = Group(share, rate)
    return pooled


def run(data_dir: Path, results_dir: Path):
    panel, totals, _ = read_panel(data_dir)
    start, end = panel[2010], panel[2023]
    within, mix, net = decompose(pool_suvs(start), pool_suvs(end), "symmetric")
    # Restore the original percentages before imposing print-precision constraints.
    low, high = mix_bounds(
        [start[k].share * totals[2010] for k in TYPES],
        [end[k].share * totals[2023] for k in TYPES],
        [start[k].rate for k in TYPES],
        [end[k].rate for k in TYPES],
    )
    results = {
        "pooled_suv_symmetric_g_per_mile": {"within": within, "mix": mix, "net": net},
        "printed_rounding_mix_bounds_g_per_mile": {"min": low, "max": high},
    }
    results_dir.mkdir(parents=True, exist_ok=True)
    (results_dir / "sensitivity.json").write_text(json.dumps(results, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    run(ROOT / "data", ROOT / "results")
