"""Test portfolio standardization, printed support, and pairwise comparison."""

import csv
import shutil
import tempfile
import unittest
from pathlib import Path

from scripts.analyze import ROOT, Group
from scripts.manufacturer_analysis import compare, load_manufacturers, run


class ManufacturerTests(unittest.TestCase):
    def test_conditional_comparison_normalizes_the_same_types_in_each_mix(self):
        actual = {"a": Group(0.2, 100), "b": Group(0.3, 200), "c": Group(0.5, 500)}
        reference = {"a": Group(0.1, 1), "b": Group(0.3, 1), "c": Group(0.6, 1)}
        row = compare("example", actual, reference, ("a", "b"))
        self.assertAlmostEqual(row["observed_g_per_mile"], 160)
        self.assertAlmostEqual(row["standardized_g_per_mile"], 175)
        self.assertAlmostEqual(row["standardized_minus_observed_g_per_mile"], 15)

    def test_rejects_share_without_a_rate(self):
        with tempfile.TemporaryDirectory() as temp:
            data_dir = Path(temp)
            shutil.copyfile(
                ROOT / "data/manufacturers.csv", data_dir / "manufacturers.csv"
            )
            source = (ROOT / "data/manufacturer_types.csv").read_text(encoding="utf-8")
            broken = source.replace(
                "Stellantis,Car SUV,0.0,329", "Stellantis,Car SUV,0.0,"
            )
            self.assertNotEqual(broken, source)
            (data_dir / "manufacturer_types.csv").write_text(broken, encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "Partially missing"):
                load_manufacturers(data_dir)

    def test_full_support_and_conditional_outputs(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            run(ROOT / "data", root)

            def rows(name):
                with (root / f"manufacturer_{name}.csv").open(
                    encoding="utf-8", newline=""
                ) as stream:
                    return list(csv.DictReader(stream))

            full = {r["manufacturer"]: r for r in rows("comparisons")}
            self.assertEqual(set(full), {"Ford", "Honda", "Toyota"})
            pairs = rows("pairs")
            (reversed_pair,) = [row for row in pairs if row["rank_reversal"] == "1"]
            self.assertEqual(
                (reversed_pair["manufacturer_a"], reversed_pair["manufacturer_b"]),
                ("Honda", "Toyota"),
            )
            self.assertAlmostEqual(
                float(reversed_pair["standardized_gap_g_per_mile"]), 8.753
            )
            support = {r["manufacturer"]: r for r in rows("support")}
            self.assertEqual(support["Stellantis"]["missing_rate_types"], "")
            self.assertEqual(
                support["Stellantis"]["rounded_zero_share_types_with_rates"], "Car SUV"
            )
            self.assertEqual(
                support["Tesla"]["missing_rate_types"], "Minivan/Van|Pickup"
            )
            sensitivity = {
                r["manufacturer"]: r for r in rows("rounded_zero_sensitivity")
            }
            self.assertEqual(set(sensitivity), set(full) | {"Stellantis"})
            self.assertAlmostEqual(
                float(sensitivity["Stellantis"]["standardized_g_per_mile"]), 396.097
            )
            common = {r["manufacturer"]: r for r in rows("two_types")}
            self.assertEqual(len(common), 14)
            self.assertEqual(common["Tesla"]["observed_rank"], "1")
            self.assertAlmostEqual(float(common["Tesla"]["standardized_g_per_mile"]), 0)
            self.assertEqual(
                (
                    common["Mazda"]["observed_rank"],
                    common["Mazda"]["standardized_rank"],
                ),
                ("9", "5"),
            )


if __name__ == "__main__":
    unittest.main()
