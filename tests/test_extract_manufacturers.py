"""Regression checks for the data states printed in EPA Tables 3.3 and 3.4."""

import csv
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from scripts.extract_manufacturers import DATA, GROUPS, TYPES


def read_csv(path):
    with path.open(encoding="utf-8", newline="") as source:
        return list(csv.DictReader(source))


class ManufacturerSourceTests(unittest.TestCase):
    def test_printed_zero_differs_from_missing(self):
        rows = read_csv(DATA / "manufacturer_types.csv")
        cells = {(row["manufacturer"], row["vehicle_type"]):
                 (row["production_share_pct"], row["co2_g_per_mile"]) for row in rows}
        self.assertEqual(len(rows), len(GROUPS) * len(TYPES))
        self.assertEqual(set(cells), {(m, t) for m in GROUPS for t in TYPES})
        self.assertEqual(cells["BMW", "Pickup"], ("", ""))
        self.assertEqual(cells["Stellantis", "Car SUV"], ("0.0", "329"))
        self.assertEqual(cells["Tesla", "Sedan/Wagon"], ("36.1", "0"))

    def test_national_rows_match_independent_annual_tables(self):
        types = [(r["vehicle_type"], r["production_share_pct"], r["co2_g_per_mile"])
                 for r in read_csv(DATA / "manufacturer_types.csv")
                 if r["manufacturer"] == "All Manufacturers"]
        annual = [(r["vehicle_type"], r["production_share_pct"], r["co2_g_per_mile"])
                  for r in read_csv(DATA / "vehicle_types.csv") if r["year"] == "2023"]
        self.assertEqual(types, annual)
        by_group = {r["manufacturer"]: r["co2_g_per_mile"]
                    for r in read_csv(DATA / "manufacturers.csv")}
        annual_rates = {r["year"]: r["co2_g_per_mile"] for r in read_csv(DATA / "fleet.csv")}
        self.assertEqual(set(by_group), set(GROUPS))
        self.assertEqual(by_group["All Manufacturers"], annual_rates["2023"])

    @unittest.skipUnless(shutil.which("pdftotext"), "Poppler needed to regenerate source data")
    def test_rebuild_from_another_directory(self):
        script = DATA.parent / "scripts/extract_manufacturers.py"
        with tempfile.TemporaryDirectory() as workdir:
            subprocess.run(
                [sys.executable, str(script), "--output-dir", "regenerated"],
                cwd=workdir, check=True, capture_output=True,
            )
            for filename in ("manufacturers.csv", "manufacturer_types.csv"):
                generated = Path(workdir) / "regenerated" / filename
                self.assertEqual(generated.read_bytes(), (DATA / filename).read_bytes())


if __name__ == "__main__":
    unittest.main()
