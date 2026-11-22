"""Recompute published outputs with exact fractions and separate accounting identities.

These end-to-end checks deliberately import no project modules. The cohort check
shares interactions algebraically rather than walking through factor permutations.
"""

import csv
import unittest
from fractions import Fraction as F
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def rows(name):
    with (ROOT / name).open(newline="", encoding="utf-8") as stream:
        return list(csv.DictReader(stream))


class IndependentReplicationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.panel = {}
        for r in rows("data/vehicle_types.csv"):
            cls.panel.setdefault(int(r["year"]), {})[r["vehicle_type"]] = (
                F(r["production_share_pct"]), F(r["co2_g_per_mile"])
            )
        for year, data in cls.panel.items():
            total = sum(s for s, _ in data.values())
            cls.panel[year] = {k: (s / total, e) for k, (s, e) in data.items()}
        cls.volume = {int(r["year"]): int(r["vehicles"]) for r in rows("data/production.csv")}

    def agree(self, got, expected):
        self.assertLess(abs(F(got) - expected), F(1, 10**8))

    def test_national_decomposition_from_four_counterfactual_fleets(self):
        bank = {year: self.panel[year] for year in (2010, 2023)}
        def mean(share_year, rate_year):
            return sum(bank[share_year][k][0] * bank[rate_year][k][1] for k in bank[2010])
        first, last = mean(2010, 2010), mean(2023, 2023)
        old_mix, old_rates = mean(2010, 2023), mean(2023, 2010)
        mix = ((last - old_mix) + (old_rates - first)) / 2
        within = ((old_mix - first) + (last - old_rates)) / 2
        headline = next(r for r in rows("results/decompositions.csv")
                        if (r["start_year"], r["end_year"], r["method"]) == ("2010", "2023", "symmetric"))
        self.agree(headline["mix_g_per_mile"], mix)
        self.agree(headline["within_g_per_mile"], within)
        self.agree(headline["net_g_per_mile"], last - first)
        self.assertEqual(round(mix / -within * 100, 1), F("28.8"))

    def test_annual_counterfactual_and_cohort_mass(self):
        annual = rows("results/cohorts.csv")
        self.assertEqual([int(r["year"]) for r in annual], list(range(2010, 2024)))
        for row in annual:
            year = int(row["year"])
            data = self.panel[year]
            observed = sum(s * e for s, e in data.values())
            fixed = sum(self.panel[2010][k][0] * e for k, (_, e) in data.items())
            factor = F(self.volume[year] * 10_000, 10**12)
            for column, wanted in (("actual_mix_megatonnes", observed * factor),
                                   ("fixed_2010_mix_megatonnes", fixed * factor),
                                   ("mix_gap_megatonnes", (observed - fixed) * factor)):
                self.agree(row[column], wanted)

    def test_three_factor_split_by_interaction_expansion(self):
        first_q = self.volume[2010]
        dq = self.volume[2023] - first_q
        expected = {k: F(0) for k in ["volume", "shares", "rates"]}
        for name, (s0, e0) in self.panel[2010].items():
            s1, e1 = self.panel[2023][name]
            ds, de = s1 - s0, e1 - e0
            joint = dq * ds * de / 3
            expected["volume"] += dq * s0 * e0 + dq * (ds * e0 + s0 * de) / 2 + joint
            expected["shares"] += first_q * ds * e0 + ds * (dq * e0 + first_q * de) / 2 + joint
            expected["rates"] += first_q * s0 * de + de * (dq * s0 + first_q * ds) / 2 + joint
        expected["net"] = sum(expected.values())
        result = {r["factor"]: r["megatonnes"] for r in rows("results/cohort_decomposition.csv")}
        self.assertEqual(set(result), set(expected))
        for factor, value in expected.items():
            self.agree(result[factor], value * F(10_000, 10**12))

    def test_mileage_and_valuation_use_correct_denominators(self):
        run = {r["production_mix"]: r for r in rows("results/lifetime_mileage.csv")}
        total_per_mile = {}
        for mix, year in (("actual_2023", 2023), ("fixed_2010", 2010)):
            miles = grams = total_rate = F(0)
            for name, (share, _) in self.panel[year].items():
                distance = 195264 if name in ("Sedan/Wagon", "Car SUV") else 225865
                rate = self.panel[2023][name][1]
                miles += distance * share
                grams += distance * share * rate
                total_rate += share * rate
            total_per_mile[mix] = total_rate
            self.agree(run[mix]["tonnes_per_vehicle"], grams / 10**6)
            self.agree(run[mix]["grams_per_mile"], grams / miles)
            self.agree(run[mix]["miles_per_vehicle"], miles)
        prices = rows("results/carbon_benchmark.csv")
        self.assertEqual([int(r["usd_2020_per_tonne"]) for r in prices], [44, 185, 413])
        extra = (total_per_mile["actual_2023"] - total_per_mile["fixed_2010"]) / 100
        for r in prices:
            self.agree(r["implied_usd_2020_per_vehicle"], extra * int(r["usd_2020_per_tonne"]))
