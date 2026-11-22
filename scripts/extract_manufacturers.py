"""Extract model year 2023 manufacturer rates and within-manufacturer shares."""

import argparse
import re
import subprocess
from pathlib import Path

if __package__:
    from .extract_data import DATA, PDF, TYPES, read_pages, write_csv
else:
    from extract_data import DATA, PDF, TYPES, read_pages, write_csv


GROUPS = (
    "BMW", "Ford", "GM", "Honda", "Hyundai", "Kia", "Mazda", "Mercedes",
    "Nissan", "Stellantis", "Subaru", "Tesla", "Toyota", "VW", "Other", "All Manufacturers",
)


def manufacturer_rows(page, title, column_count):
    """Collect complete numeric rows, allowing for the two-word national label."""
    if not page.lstrip().startswith(title):
        raise ValueError(f"Could not locate {title}")
    rows = {}
    for line in page.splitlines():
        fields = line.rsplit(None, column_count)
        if len(fields) != column_count + 1:
            continue
        group = fields[0].strip()
        if group in GROUPS:
            if group in rows:
                raise ValueError(f"Duplicate {group} row in {title}")
            rows[group] = fields[1:]
    if set(rows) != set(GROUPS):
        raise ValueError(f"Incomplete rows in {title}: {sorted(set(GROUPS) - rows.keys())}")
    return rows


def extract(pdf):
    # Printed pages 44 and 45 are physical PDF pages 53 and 54.
    fleet_page, type_page = read_pages(pdf, 53, 54)
    fleet_table = manufacturer_rows(fleet_page, "Table 3.3.", 6)
    type_table = manufacturer_rows(type_page, "Table 3.4.", 15)
    manufacturers, types = [], []
    for group in GROUPS:
        manufacturers.append((group, int(fleet_table[group][0])))
        values = type_table[group]
        for i, vehicle_type in enumerate(TYPES):
            share, co2, mpg = values[i * 3 : i * 3 + 3]
            if (share, co2, mpg) == ("-", "-", "-"):
                types.append((group, vehicle_type, None, None))
                continue
            if not (re.fullmatch(r"\d+\.\d%", share) and re.fullmatch(r"\d+", co2)
                    and re.fullmatch(r"\d+\.\d", mpg)):
                raise ValueError(f"Malformed measurement for {group}, {vehicle_type}")
            types.append((group, vehicle_type, share[:-1], int(co2)))
    return manufacturers, types


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--pdf", type=Path, default=PDF, help="Exact archived 2024 EPA report")
    parser.add_argument("--output-dir", type=Path, default=DATA, help="Destination for CSVs")
    args = parser.parse_args()
    try:
        manufacturers, types = extract(args.pdf)
        args.output_dir.mkdir(parents=True, exist_ok=True)
        write_csv(args.output_dir / "manufacturers.csv", ("manufacturer", "co2_g_per_mile"), manufacturers)
        write_csv(
            args.output_dir / "manufacturer_types.csv",
            ("manufacturer", "vehicle_type", "production_share_pct", "co2_g_per_mile"),
            types,
        )
    except (OSError, ValueError, subprocess.CalledProcessError) as error:
        parser.exit(1, f"Extraction failed: {error}\n")
    print(f"Extracted {len(manufacturers)} manufacturer/aggregate rows and {len(types)} type cells.")


if __name__ == "__main__":
    main()
