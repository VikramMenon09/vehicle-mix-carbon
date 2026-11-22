"""Accounting checks and regression tests for the two rounded EPA tables."""

import unittest

from scripts.analyze import (
    ROOT,
    Group,
    annual_series,
    by_vehicle_type,
    decompose,
    read_panel,
    valuation,
)


class DecompositionTests(unittest.TestCase):
    def setUp(self):
        self.start = {"a": Group(0.8, 100), "b": Group(0.2, 300)}
        self.end = {"a": Group(0.5, 80), "b": Group(0.5, 240)}

    def test_two_orderings_and_symmetric_average(self):
        # Fleet rates are 140 and 160. Updating rates first passes through
        # 112, while updating shares first passes through 200.
        for method, expected in (
            ("rates_first", (-28, 48, 20)),
            ("shares_first", (-40, 60, 20)),
            ("symmetric", (-34, 54, 20)),
        ):
            with self.subTest(method=method):
                actual = decompose(self.start, self.end, method)
                for value, target in zip(actual, expected):
                    self.assertAlmostEqual(value, target)

    def test_swapping_endpoints_reverses_symmetric_contributions(self):
        forward = decompose(self.start, self.end, "symmetric")
        backward = decompose(self.end, self.start, "symmetric")
        for first, second in zip(forward, backward):
            self.assertAlmostEqual(first, -second)

    def test_valuation_uses_metric_tonnes(self):
        row = valuation(25)[1]
        self.assertEqual(row["price_usd_per_tonne"], 100)
        self.assertEqual(row["tonnes_co2"], 0.25)
        self.assertEqual(row["implied_value_usd"], 25)


class EPAPanelTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.panel, cls.totals, cls.benchmarks = read_panel(ROOT / "data")

    def test_rounded_shares_are_normalized_before_weighting(self):
        self.assertAlmostEqual(self.totals[2010], 99.9)
        self.assertAlmostEqual(self.panel[2010]["Sedan/Wagon"].share, 54.5 / 99.9)
        series = annual_series(self.panel, self.totals, self.benchmarks)
        self.assertEqual(len(series), 14)
        self.assertEqual(series[0]["actual_minus_fixed_g_per_mile"], 0)
        self.assertAlmostEqual(series[-1]["actual_g_per_mile"], 319.247)
        self.assertAlmostEqual(series[-1]["fixed_2010_mix_g_per_mile"], 291.898898899)

    def test_fleet_benchmark_disagreement_raises_error(self):
        altered = dict(self.benchmarks)
        altered[2015] += 2
        with self.assertRaisesRegex(ValueError, "Table 3.1 in 2015"):
            annual_series(self.panel, self.totals, altered)

    def test_centered_mix_contributions_sum_to_the_same_fleet_mix(self):
        start, end = self.panel[2010], self.panel[2023]
        rows = by_vehicle_type(start, end)
        within, mix, net = decompose(start, end, "symmetric")
        for field, expected in (
            ("within_g_per_mile", within),
            ("mix_g_per_mile", mix),
            ("centered_mix_g_per_mile", mix),
            ("net_g_per_mile", net),
        ):
            self.assertAlmostEqual(sum(row[field] for row in rows), expected)


if __name__ == "__main__":
    unittest.main()
