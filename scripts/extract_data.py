"""Rebuild the national analysis CSVs from the archived EPA report using Poppler."""

import argparse
import csv
import hashlib
import re
import subprocess
import tempfile
from pathlib import Path


DATA = Path(__file__).resolve().parents[1] / "data"
PDF = DATA / "raw" / "epa-automotive-trends-2024.pdf"
SHA256 = "303e9e3a1124b72fd81c20b5949a40f856469d7b4f5ab6de8b437e92cb7a3c20"
YEARS = range(2010, 2024)
TYPES = ("Sedan/Wagon", "Car SUV", "Truck SUV", "Minivan/Van", "Pickup")


def table_rows(page, title, column_count):
    """Read the annual rows on a single report page and require the full panel."""
    if not page.lstrip().startswith(title):
        raise ValueError(f"Could not locate table {title}")
    rows = {}
    for line in page.splitlines():
        fields = line.split()
        if not fields or not re.fullmatch(r"[0-9]{4}", fields[0]):
            continue
        year = int(fields[0])
        if year not in YEARS:
            continue
        if len(fields) != column_count or year in rows:
            raise ValueError(f"Unexpected row on table {title} for {year}: {line!r}")
        rows[year] = fields[1:]
    if set(rows) != set(YEARS):
        raise ValueError(f"Missing years in table {title}: {sorted(set(YEARS) - rows.keys())}")
    return rows


def read_pages(pdf, first, last):
    """Read physical pages from the pinned archive and keep their table layout."""
    if hashlib.sha256(pdf.read_bytes()).hexdigest() != SHA256:
        raise ValueError(f"Source PDF checksum mismatch. Expected SHA-256 {SHA256}")
    text = subprocess.check_output(
        ["pdftotext", "-layout", "-enc", "UTF-8", "-f", str(first), "-l", str(last), str(pdf), "-"],
        encoding="utf-8",
    )
    return [page for page in text.split("\f") if page.strip()]


def extract(pdf):
    # Printed pages 42 and 43 are file pages 51 and 52.
    fleet_page, type_page = read_pages(pdf, 51, 52)
    fleet_table = table_rows(fleet_page, "Table 3.1.", 9)
    type_table = table_rows(type_page, "Table 3.2.", 16)

    fleet_rows = []
    type_rows = []
    for year in YEARS:
        fleet_rows.append((year, int(fleet_table[year][0])))
        # Each vehicle type has three adjacent columns: share, CO2 rate, mpg.
        for index, vehicle_type in enumerate(TYPES):
            share, co2, mpg = type_table[year][index * 3 : index * 3 + 3]
            if not re.fullmatch(r"\d+\.\d%", share) or not re.fullmatch(r"\d+\.\d", mpg):
                raise ValueError(f"Unexpected column arrangement for {year} {vehicle_type}")
            type_rows.append((year, vehicle_type, share[:-1], int(co2)))
    return fleet_rows, type_rows


def extract_production(pdf, fleet):
    """Read the second block of Table 2.1 and match its rates to Table 3.1."""
    page = subprocess.check_output(
        ["pdftotext", "-layout", "-f", "23", "-l", "23", str(pdf), "-"],
        encoding="utf-8",
    )
    if not page.lstrip().startswith("Table 2.1. Production"):
        raise ValueError("Unexpected title for the production table on PDF page 23")
    benchmark = dict(fleet)
    production = {}
    for line in page.splitlines():
        fields = line.split()
        if len(fields) != 8 or not fields[4].isdigit():
            continue
        year = int(fields[4])
        if year in YEARS:
            if year in production or int(fields[6]) != benchmark[year]:
                raise ValueError(f"Invalid Table 2.1 fleet benchmark in {year}")
            production[year] = int(fields[5].replace(",", "")) * 1000
    if set(production) != set(YEARS) or min(production.values()) <= 0:
        raise ValueError("Incomplete or invalid production series in Table 2.1")
    return sorted(production.items())


def write_csv(path, header, rows):
    with tempfile.TemporaryDirectory(dir=path.parent) as working:
        staged = Path(working) / path.name
        with staged.open("w", encoding="utf-8", newline="") as output:
            writer = csv.writer(output, lineterminator="\n")
            writer.writerow(header)
            writer.writerows(rows)
        staged.replace(path)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--pdf", type=Path, default=PDF, help="Exact archived 2024 EPA report")
    parser.add_argument("--output-dir", type=Path, default=DATA, help="Destination for CSVs")
    args = parser.parse_args()
    try:
        fleet, types = extract(args.pdf)
        production = extract_production(args.pdf, fleet)
        args.output_dir.mkdir(parents=True, exist_ok=True)
        write_csv(args.output_dir / "production.csv", ("year", "vehicles"), production)
        write_csv(args.output_dir / "fleet.csv", ("year", "co2_g_per_mile"), fleet)
        write_csv(
            args.output_dir / "vehicle_types.csv",
            ("year", "vehicle_type", "production_share_pct", "co2_g_per_mile"),
            types,
        )
    except (OSError, ValueError, subprocess.CalledProcessError) as error:
        parser.exit(1, f"Extraction failed: {error}\n")
    print(f"Extracted {len(fleet)} fleet estimates and {len(types)} vehicle-type estimates.")


if __name__ == "__main__":
    main()
