"""Type, manufacturer and production-cohort results for the expanded study."""

from itertools import combinations

from paper.figures import cohort_indices
from paper.layout import Page


def type_attribution(c, rows, annual):
    p = Page(c, 4, "Vehicle-type contributions")
    p.heading("Where the 30 grams came from")
    p.para("A vehicle type can get cleaner and still push up the fleet average as it gains "
           "share. To see which types did both, the within-type column holds "
           "each type at its average share. The mix column asks whether a growing or shrinking "
           "type emitted more or less than a common fleet benchmark.", gap=12)
    p.figure_title("Table 2", "Vehicle-type contributions to the national change")
    table = []
    for r in rows:
        shift = float(r["end_share_pct"]) - float(r["start_share_pct"])
        table.append([r["vehicle_type"], f"{shift:+.1f}", f"{float(r['within_g_per_mile']):+.1f}",
                      f"{float(r['centered_mix_g_per_mile']):+.1f}"])
    within = sum(float(r["within_g_per_mile"]) for r in rows)
    mix = sum(float(r["centered_mix_g_per_mile"]) for r in rows)
    table.append(["All five types", "0.0", f"{within:+.1f}", f"{mix:+.1f}"])
    p.table(["Vehicle type", "Share change (pp)", "Within (g/mi)", "Mix (g/mi)"],
            table, [154, 120, 112, 114])
    benchmark = (float(annual[0]["actual_g_per_mile"]) + float(annual[-1]["actual_g_per_mile"])) / 2
    p.caption(f"Share changes are percentage points after normalizing the rounded shares. Each mix contribution is its share change × (its average endpoint rate minus {benchmark:.1f} g/mi). "
              "The benchmark is the mean of the two fleet rates. Shares sum to one, so subtracting this "
              "common reference preserves the total mix effect. Individual rows depend on that choice.")
    p.subhead("A shrinking category can raise the average")
    p.para("Sedan/wagons lost nearly 30 percentage points of production. Their average rate sat "
           "below the fleet benchmark, so their declining share contributed positively to the mix "
           "term. Truck SUVs gained share while emitting above the benchmark. Those two shifts "
           "account for most of the net mix contribution. A growing share for car SUVs worked in "
           "the opposite direction.")
    p.subhead("The type that replaces a sedan matters")
    by_type = {r["vehicle_type"]: float(r["end_g_per_mile"]) for r in rows}
    truck = 0.01 * (by_type["Truck SUV"] - by_type["Sedan/Wagon"])
    car = 0.01 * (by_type["Car SUV"] - by_type["Sedan/Wagon"])
    p.para(f"At the published 2023 rates, moving one percentage point of production from "
           f"sedan/wagons to truck SUVs would add {truck:.2f} g/mi to the fleet average. Moving "
           f"that same share to car SUVs would subtract {abs(car):.2f} g/mi. Both exercises hold "
           "the other shares and every rate fixed. A forecast that combines all SUVs can miss "
           "the sign of a specific substitution.")
    p.finish()


def firms(c, comparisons, pairs, extended):
    p = Page(c, 6, "Manufacturer comparison")
    p.heading("Putting manufacturers on the same mix")
    p.para("EPA also reports 2023 shares and emissions rates within each manufacturer. A "
           "firm can have a lower average by building cleaner vehicles within categories, by "
           "building more of the lower-emitting categories, or both. To compare like portfolios, "
           "apply the same five national production shares to each firm’s own type rates. "
           "This cross-section is a separate comparison from the national time series. [1, Tables 3.3–3.4]")
    p.figure_title("Table 4", "Five-type comparison for firms with a positive printed share in every type")
    p.table(["Manufacturer", "Own mix", "National mix", "Change (g/mi)"],
            [[r["manufacturer"], f"{float(r['observed_g_per_mile']):.1f}",
              f"{float(r['standardized_g_per_mile']):.1f}", f"{float(r['standardized_minus_observed_g_per_mile']):+.1f}"]
             for r in comparisons], [157, 103, 118, 122])
    p.caption("Grams per mile. A sum over the five types uses either the firm’s own shares or the "
              "national shares from Table 1. Rows cover three of the 14 named manufacturers. "
              "The residual ‘Other’ group pools smaller manufacturers.")
    p.subhead("Honda and Toyota change places")
    pair = next(r for r in pairs if r["manufacturer_a"] == "Honda" and r["manufacturer_b"] == "Toyota")
    p.para(f"Honda’s reconstructed rate was {abs(float(pair['observed_gap_g_per_mile'])):.1f} g/mi "
           f"below Toyota’s with their actual portfolios. At national weights Honda is "
           f"{float(pair['standardized_gap_g_per_mile']):.1f} g/mi above Toyota. Truck SUVs explain "
           "most of the standardized gap. They made up 45.3% of national production, and Honda’s "
           "truck SUV rate exceeded Toyota’s by 15 g/mi, contributing 6.8 g/mi of that gap.")
    p.para("Rounding cannot explain this reversal. EPA separately reports 314 and 322 g/mi for "
           "Honda and Toyota. For the standardized gap, letting both firms’ rates vary by half a "
           "gram and national shares by 0.05 percentage point changes the estimate by at most "
           "1.1 g/mi. The two comparisons give opposite signs even at those limits.")
    p.subhead("Which firms can be compared?")
    st = next(r for r in extended if r["manufacturer"] == "Stellantis")
    p.para(f"Ten named firms have a missing rate for at least one type. Stellantis reports a car SUV "
           f"rate but a share rounded to 0.0%. Including its rate yields {float(st['standardized_g_per_mile']):.1f} "
           "g/mi under national weights. Even a positive share can be thin. Ford’s sedan/wagon share "
           "was 1.3%, compared with 25.0% nationally. The calculation reweights the models Ford "
           "offered. A large shift could change the models themselves. Appendix A compares all 14 named firms using the two types they all produced.")
    p.finish()


def cohorts(c, annual, changes):
    p = Page(c, 7, "Production and emissions")
    p.heading("A cleaner mile in a larger model year")
    start, end = annual[0], annual[-1]
    first, last = int(start["vehicles"]), int(end["vehicles"])
    a, b = float(start["actual_mix_megatonnes"]), float(end["actual_mix_megatonnes"])
    p.para(f"EPA recorded {first/1e6:.3f} million vehicles in model year 2010 and "
           f"{last/1e6:.3f} million in 2023, an increase of {(last/first-1):.1%}. Give each "
           "vehicle in each cohort 10,000 miles. Although the average vehicle emitted less per mile, "
           f"the larger 2023 cohort produces {b:.2f} million tonnes in this exercise, compared "
           f"with {a:.2f} million in 2010, a rise of {(b/a-1):.1%}. [1, Table 2.1]")
    p.figure_title("Figure 3", "Cohort emissions, production and emissions per mile (2010 = 100)")
    cohort_indices(p, annual)
    p.caption("The scenario multiplies each year’s production count by its own reconstructed fleet rate "
              "and 10,000 miles per vehicle. Index values compare model-year cohorts at the same mileage "
              "threshold. Calendar-year traffic includes many other model years.")
    p.figure_title("Table 5", "Contributions to the change in cohort emissions, 2010–2023")
    names = {"volume": "Number of vehicles", "shares": "Vehicle-type mix",
             "rates": "Rates within types", "net": "Net change"}
    p.table(["Factor", "Million metric tonnes"], [[names[r["factor"]], f"{float(r['megatonnes']):+.2f}"]
            for r in changes], [325, 175], row_height=20)
    p.caption("Each contribution is its average marginal change over all six orders for updating production "
              "volume, type shares and type rates. The Shapley allocation divides interactions among "
              "the factors involved. Totals use unrounded values. [4]")
    gap = float(end["mix_gap_megatonnes"])
    p.para(f"For a different question, hold 2023 production and emissions rates fixed. Applying "
           f"2010 shares to that cohort lowers its 10,000-mile total by {gap:.2f} million tonnes. "
           "This calculation describes what composition alone means at the 2023 scale. "
           "It assumes identical use and leaves pricing, supply and driving responses open.")
    later = next(r for r in annual if int(r["year"]) == 2013)
    alternate = float(later["actual_mix_megatonnes"])
    p.para(f"The sign depends on the starting cohort. Starting in 2013, when output was "
           f"{int(later['vehicles'])/1e6:.3f} million vehicles, the same scenario falls from "
           f"{alternate:.2f} to {b:.2f} million tonnes ({(b/alternate-1):.1%}).")
    p.finish()


def economics(c, life, benchmarks, values):
    p = Page(c, 8, "Mileage and economic value")
    p.heading("What changes when trucks travel farther?")
    p.para("An average over vehicles gives a sedan and a truck one vote each. An average over "
           "miles gives more weight to the vehicle that travels farther. As a sensitivity check, "
           "apply the lifetime distances EPA used in its credit accounting: 195,264 miles for cars "
           "and 225,865 for trucks. Sedan/wagons and car SUVs take the car value. The other three "
           "types take the truck value. These distances are scenario inputs. [1, p. 93]")
    p.figure_title("Table 6", "2023 type rates under two production mixes and class-specific mileage")
    p.table(["2023 vehicles weighted by", "Miles/vehicle", "Tonnes/vehicle", "Grams/mile"],
            [[k, f"{float(r['miles_per_vehicle']):,.0f}", f"{float(r['tonnes_per_vehicle']):.2f}",
              f"{float(r['grams_per_mile']):.1f}"] for k, r in zip(["Actual 2023 mix", "Fixed 2010 mix"], life)],
            [178, 108, 110, 104])
    p.caption("Tonnes per vehicle = sum of (share × type miles × type rate) ÷ 1,000,000. Grams per mile "
              "divides weighted grams by weighted miles. Rates are held fixed over the assumed life.")
    more_miles = float(life[0]["miles_per_vehicle"]) - float(life[1]["miles_per_vehicle"])
    more_tonnes = float(life[0]["tonnes_per_vehicle"]) - float(life[1]["tonnes_per_vehicle"])
    mileage_mass = more_miles * sum(float(r["grams_per_mile"]) for r in life) / 2_000_000
    p.para(f"The actual mix implies {more_tonnes:.2f} more tonnes per vehicle and {more_miles:,.0f} "
           f"more miles of service. Averaging the two update orders as on page 3 assigns "
           f"{mileage_mass:.2f} tonnes of the difference to extra miles and "
           f"{more_tonnes-mileage_mass:.2f} tonnes to the higher mileage-weighted rate. Realized emissions "
           "depend on how long vehicles survive and how much they are driven.")
    p.subhead("Valuing a common distance")
    gap = float(values[1]["tonnes_co2"])
    mean = float(benchmarks[1]["implied_usd_2020_per_vehicle"])
    p.para(f"Return to the same 10,000 miles for each type. The extra {gap:.3f} tonnes in the "
           "actual 2023 mix relative to fixed 2010 shares can be priced with a published damage benchmark. Rennert and colleagues "
           "estimate a mean social cost of $185 per tonne for a 2020 emissions pulse, in 2020 U.S. "
           "dollars, using a 2% near-term discount rate. Applying that value gives "
           f"<b>${mean:.2f} per vehicle</b>. [5]")
    low, high = (float(benchmarks[i]["implied_usd_2020_per_vehicle"]) for i in (0, 2))
    p.para(f"Their 5th and 95th percentile values of $44 and $413 per tonne imply ${low:.2f} "
           f"and ${high:.2f} for the same difference. This range propagates the published carbon "
           "values only. It carries a 2020 damage valuation into a standardized scenario. A "
           "valuation for the fleet’s actual driving years would need the emissions path and "
           "social costs for those years.")
    p.subhead("Economic interpretation")
    p.para("A fleet projection needs assumptions about production volume, vehicle mix and use. A welfare "
           "comparison also needs consumers’ value for vehicle attributes, supply costs and emissions from "
           "fuel, electricity and vehicle manufacturing.")
    p.finish()


def broad_firms(c, rows):
    p = Page(c, 9, "Appendix A · Common types")
    p.heading("A comparison covering 14 manufacturers")
    p.para("Every named manufacturer produced both sedan/wagons and truck SUVs. Together these "
           "two categories represented 70.3% of U.S. production. Restrict each firm to those types, "
           "then weight its rates twice: once by the firm’s split within the pair, and once by the "
           "national split of 25.0/70.3 sedan/wagons and 45.3/70.3 truck SUVs.")
    p.figure_title("Table A1", "2023 tailpipe rates within the two common vehicle types")
    p.table(["Manufacturer", "Firm output covered", "Own split (g/mi)", "U.S. split (g/mi)"],
            [[r["manufacturer"], f"{float(r['within_firm_two_type_share_pct']):.1f}%",
              f"{float(r['observed_g_per_mile']):.1f}", f"{float(r['standardized_g_per_mile']):.1f}"]
             for r in rows], [123, 127, 125, 125], row_height=18)
    p.caption("Coverage is the two categories’ combined share of the firm’s own production. Both rates "
              "condition on these categories. Tesla’s battery-electric models have zero tailpipe emissions. "
              "Sources: EPA (2024), Tables 3.2–3.4, and calculations from the published shares.")
    pairs = list(combinations(rows, 2))
    reversals = sum((float(a["observed_g_per_mile"]) - float(b["observed_g_per_mile"])) *
                    (float(a["standardized_g_per_mile"]) - float(b["standardized_g_per_mile"])) < 0
                    for a, b in pairs)
    p.para(f"With the published values, {reversals} of {len(pairs)} pairwise orderings reverse. "
           "For example, Honda is below Mazda using their own two-type splits. At national weights, "
           "Mazda is below Honda. Close comparisons can change within the source’s rounding "
           "precision. Coverage ranges from 44.9% to 100% of an individual firm’s production, "
           "so these estimates describe only the two common categories.")
    p.finish()
