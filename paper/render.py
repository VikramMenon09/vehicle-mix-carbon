"""Manuscript and deterministic PDF build for the vehicle mix study."""

import csv
import json

from reportlab.lib.pagesizes import letter
from reportlab.pdfgen.canvas import Canvas

from paper.figures import annual_paths, change_bars
from paper import extensions
from paper.layout import LEFT, LIGHT, MUTED, RIGHT, Page, block

TITLE = "How vehicle mix shaped U.S. tailpipe emissions"
CO2 = "CO<sub>2</sub>"


def read_csv(path):
    with path.open(encoding="utf-8", newline="") as stream:
        return list(csv.DictReader(stream))


def signed(value):
    return f"{float(value):+.1f}"


def source_link(url, label):
    return f'<link href="{url}" color="#006A62"><u>{label}</u></link>'


def overview(c, annual, main, cohort):
    p = Page(c, 1, "Research paper")
    p.para("How vehicle mix shaped<br/>U.S. tailpipe emissions", font="Times-Bold",
           size=36, leading=38, gap=10)
    p.para("New light-duty vehicles delivered for sale, model years 2010–2023",
           font="Helvetica", size=12.2, leading=16, gap=17, color=MUTED)
    p.subhead("Abstract")
    within, mix, net = (float(main[k + "_g_per_mile"]) for k in ("within", "mix", "net"))
    base, end = float(annual[0]["actual_g_per_mile"]), float(annual[-1]["actual_g_per_mile"])
    fixed = float(annual[-1]["fixed_2010_mix_g_per_mile"])
    p.para(f"Every major type of new U.S. vehicle emitted less {CO2} per mile in 2023 than in "
           f"2010. Yet the largest gains in production share went to truck SUVs. Using EPA data "
           f"for five vehicle types, this study separates changes in each type’s emissions rate from "
           f"changes in its share of production. Lower rates within types reduced the fleet average "
           f"by {abs(within):.1f} grams per mile. The changing mix added {mix:.1f} grams back, offsetting "
           f"<b>{mix / abs(within):.1%}</b> of the improvement. The net decline was {abs(net):.1f} grams per mile "
           f"({abs(net)/base:.1%}). Production grew enough that, over an assumed 10,000 miles per vehicle, "
           f"the 2023 cohort would emit {float(cohort[-1]['actual_mix_megatonnes'])/float(cohort[0]['actual_mix_megatonnes'])-1:.1%} "
           "more than the 2010 cohort. Under the same assumption, the 2023 total is "
           f"{1-float(cohort[-1]['actual_mix_megatonnes'])/float(next(r for r in cohort if r['year']=='2013')['actual_mix_megatonnes']):.1%} "
           "below the 2013 total.", gap=15)
    p.figure_title("Figure 1", "Tailpipe emissions per mile with actual and fixed production shares")
    annual_paths(p, annual)
    p.caption("Grams per mile by model year. Both lines use each year’s emissions rates for all five types. "
              "The dashed line weights those rates by 2010 production shares. Source: EPA (2024), Table 3.2.")
    p.subhead("A mile in the 2023 fleet")
    p.para(f"A new vehicle drawn from the 2023 production mix averaged {end:.1f} grams per mile. "
           f"Using the 2010 production shares with 2023 emissions rates brings that figure to {fixed:.1f}. "
           "The gap first exceeded 20 grams per mile in 2019. It narrowed between 2022 and 2023, "
           "when emissions from car SUVs fell sharply.")
    p.finish()


def data_and_types(c, raw, annual, vehicle_results):
    p = Page(c, 2, "Data and measurement")
    p.heading("Which vehicles changed the average?")
    p.para("EPA counts new vehicles produced for sale in the United States, including imports. "
           "Its standardized tests estimate emissions under typical driving conditions. Each new "
           "vehicle therefore carries equal weight in the fleet average, regardless of how far "
           "its owner ultimately drives. [1]")
    p.para("The 2024 edition of the Automotive Trends Report publishes production shares and "
           "tailpipe rates together. Table 3.2 gives 14 consecutive final years, 2010–2023, for "
           "five types. Earlier observations in the printed table come at five-year intervals. "
           "The next row, 2024, was preliminary in this edition. The analysis therefore uses "
           "70 type-year observations from one consistent release.", gap=14)
    p.figure_title("Table 1", "A growing truck SUV share and falling rates in every category")
    lookup = {(int(r["year"]), r["vehicle_type"]): r for r in raw}
    rows = []
    for result in vehicle_results:
        name = result["vehicle_type"]
        first, last = lookup[2010, name], lookup[2023, name]
        rows.append([name, f'{float(first["production_share_pct"]):.1f}%',
                     f'{float(last["production_share_pct"]):.1f}%',
                     first["co2_g_per_mile"], last["co2_g_per_mile"]])
    p.table(["Vehicle type", "2010 share", "2023 share", "2010 g/mi", "2023 g/mi"],
            rows, [154, 90, 90, 83, 83])
    p.caption("Shares are printed at EPA’s precision. The 2010 shares sum to 99.9%. The calculations divide "
              "each year’s shares by their sum before weighting the rates. Source: EPA (2024), Table 3.2.")
    p.subhead("Two SUV markets")
    p.para("Truck SUVs more than doubled their share of production while their rate fell from "
           "452 to 356 g/mi. Car SUVs tell a different story. By 2023 they had the lowest tailpipe "
           "rate of the five types, at 190 g/mi. EPA reports that 36% of new car SUVs were battery "
           "electric that year. These vehicles record zero at the tailpipe. The SUV distinction "
           "follows regulatory car and light-truck classifications, which depend in part on weight "
           "and drive configuration. [1, pp. 17–20]")
    max_gap = max(abs(float(r["actual_minus_epa_g_per_mile"])) for r in annual)
    p.para("Weighting the five rates closely reproduces EPA’s separately published fleet series. "
           f"The largest absolute difference is {max_gap:.2f} g/mi after rounding. This is consistent with "
           "the precision of the source tables. [1, Tables 3.1–3.2]")
    p.finish()


def method(c, main, rates_first, shares_first):
    p = Page(c, 3, "Decomposition")
    p.heading("Cleaner vehicles and a changing mix")
    p.para("Let <i>s</i> be a type’s share of new vehicle production and <i>e</i> its tailpipe "
           "rate in grams per mile. The fleet average is the sum of <i>s × e</i> over the five "
           "types. Changing the weights first gives a different mix contribution than changing the "
           "rates first. The symmetric decomposition averages those two contributions. [2]")
    top = p.y
    block(c, LEFT, top, RIGHT - LEFT, 67, LIGHT)
    p.y += 10
    p.para("<b>Within types</b> = sum of (average share × change in emissions rate)",
           size=12, leading=17, gap=6, indent=12)
    p.para("<b>Production mix</b> = sum of (change in share × average emissions rate)",
           size=12, leading=17, gap=0, indent=12)
    p.y = top + 77
    p.para("Each average is the simple mean of the 2010 and 2023 values for that type. "
           "Changes run from 2010 to 2023. Expanding the two products shows that their "
           "sum equals the change in the fleet average exactly, before rounding.", gap=13)
    p.figure_title("Figure 2", "Contributions to the change in fleet emissions, g/mi")
    change_bars(p, *(float(main[k + "_g_per_mile"]) for k in ("within", "mix", "net")))
    p.caption("A negative contribution lowers the average emissions rate. The net change equals the sum "
              "of the within-type and production-mix contributions. Source: calculations from EPA (2024).")
    p.subhead("Why the two mix estimates differ")
    mix_first, mix_last = float(shares_first["mix_g_per_mile"]), float(rates_first["mix_g_per_mile"])
    p.para(f"Applying the shift in production shares to the 2010 emissions rates raises "
           f"the fleet average by {mix_first:.1f} g/mi. Applying the same shift to the cleaner 2023 "
           f"rates raises it by {mix_last:.1f} g/mi. Their mean is the {float(main['mix_g_per_mile']):.1f} g/mi "
           "mix contribution in Figure 2. The second calculation also gives the gap at the "
           "right edge of Figure 1. It answers the practical question of how much the 2023 "
           "average changes when only its mix is reset.")
    p.para("The within-type component includes changes in the vehicles offered inside each category, "
           "among them a shift to electric powertrains. Knittel documented a related trade-off "
           "between fuel economy and other attributes, including weight and horsepower. "
           "Aggregated vehicle types cannot isolate engineering improvements from changes in "
           "those attributes or identify buyer responses to fuel prices. [3]")
    p.finish()


def sensitivity(c, periods, extra):
    p = Page(c, 5, "Sensitivity analysis")
    p.heading("How stable is the mix estimate?")
    p.para("The endpoint result compares two complete model years. Shorter comparisons "
           "show when the production shift mattered most. A further check adds the 13 "
           "year-to-year decompositions, allowing each year’s mix and emissions rates to "
           "set the weights for the next step.", gap=13)
    p.figure_title("Table 3", "Sensitivity to timing and SUV classification")
    rows = []
    for start, end, method_name, label in [
        (2010, 2023, "symmetric", "2010–2023, endpoints"),
        (2010, 2023, "annual_chained", "2010–2023, annual steps"),
        (2013, 2023, "symmetric", "2013–2023, later start"),
        (2010, 2019, "symmetric", "2010–2019"),
        (2019, 2023, "symmetric", "2019–2023"),
    ]:
        r = periods[start, end, method_name]
        rows.append([label] + [signed(r[k + "_g_per_mile"]) for k in ("within", "mix", "net")])
    pooled = extra["pooled_suv_symmetric_g_per_mile"]
    rows.append(["2010–2023, SUVs combined"] + [signed(pooled[k]) for k in ("within", "mix", "net")])
    p.table(["Comparison", "Within types", "Mix", "Net change"], rows, [228, 98, 77, 97])
    p.caption("Grams per mile. Each row is a separate decomposition. The pooled row first weights the "
              "two SUV rates by their production shares to construct a single SUV rate in each year.")
    before = periods[2010, 2019, "symmetric"]
    after = periods[2019, 2023, "symmetric"]
    p.para(f"The changing mix added {float(before['mix_g_per_mile']):.1f} g/mi over the nine "
           f"years to 2019, compared with {float(after['mix_g_per_mile']):.1f} over the next four. "
           "The later-start result also addresses a break in EPA coverage. In 2011 EPA began "
           "including certain heavier passenger vans and SUVs, integrated alternative-fuel models, "
           "and updated test conversions. EPA puts the first of these changes at 0.3 g/mi for the "
           "2011 fleet. The positive mix effect persists starting in 2013. [1, Appendix D]")
    p.para(f"Combining car and truck SUVs lowers the full-period mix estimate to {pooled['mix']:.1f} "
           "g/mi. In that grouping, shifts between the two SUV classes move into the within-type "
           "term. The fleet total stays the same.", gap=12)
    p.subhead("Precision of the printed data")
    bounds = extra["printed_rounding_mix_bounds_g_per_mile"]
    p.para(f"Allow each share to vary by 0.05 percentage points and each type rate by 0.5 g/mi, "
           f"with true shares summing to 100% in each year. Across all compatible endpoint values, "
           f"the five-type mix term ranges from <b>{bounds['min']:.1f} to {bounds['max']:.1f} g/mi</b>. "
           "The main estimate scales printed shares proportionally. This check uses feasible unrounded shares. The interval excludes uncertainty in EPA’s test "
           "estimates and differences in how people drive.")
    p.finish()


def references(c):
    p = Page(c, 10, "Appendix B · Sources and replication")
    p.heading("Sources and replication")
    p.subhead("Data and literature")
    refs = [
        ("[1] U.S. Environmental Protection Agency. 2024. <i>The 2024 EPA Automotive Trends "
         "Report: Greenhouse Gas Emissions, Fuel Economy, and Technology since 1975.</i> "
         "EPA-420-R-24-022. Table 2.1 supplies production totals to the nearest thousand. "
         "Tables 3.1–3.4 supply national and manufacturer rates and shares. Section 5, p. 93, "
         "supplies the scenario mileage. Appendices D and E document scope and emissions methods.",
         "https://www.epa.gov/automotive-trends/download-2024-automotive-trends-report", "EPA report"),
        ("[2] Kitagawa, E. M. 1955. Components of a Difference Between Two Rates. "
         "<i>Journal of the American Statistical Association</i> 50(272), 1168–1194.",
         "https://doi.org/10.1080/01621459.1955.10501299", "Article"),
        ("[3] Knittel, C. R. 2011. Automobiles on Steroids: Product Attribute Trade-Offs and "
         "Technological Progress in the Automobile Sector. <i>American Economic Review</i> 101(7), 3368–3399.",
         "https://doi.org/10.1257/aer.101.7.3368", "Article"),
        ("[4] Shorrocks, A. F. 2013. Decomposition Procedures for Distributional Analysis: "
         "A Unified Framework Based on the Shapley Value. <i>Journal of Economic Inequality</i> 11, 99–126.",
         "https://doi.org/10.1007/s10888-011-9214-z", "Article"),
        ("[5] Rennert, K., F. Errickson, B. C. Prest, et al. 2022. Comprehensive Evidence Implies a "
         "Higher Social Cost of CO<sub>2</sub>. <i>Nature</i> 610, 687–692.",
         "https://doi.org/10.1038/s41586-022-05224-9", "Article"),
    ]
    for citation, url, label in refs:
        p.para(f"{citation} {source_link(url, label)}.", size=11.5, leading=15, gap=7)
    p.subhead("Reconstructing the study")
    p.para("The repository contains the full EPA release, checksum, machine-readable input tables, "
           "code, figures and result tables. The extraction distinguishes missing manufacturer cells "
           "from measured zero emissions and shares rounded to zero. The build checks each national "
           "average and each manufacturer’s reconstructed rate against the separately tabulated "
           "EPA benchmark.")
    p.para("Independent checks compare the extraction against the original tables and recompute "
           "the headline from exact fractions. A separate implementation verifies the three-factor "
           "decomposition by expanding the products and dividing each interaction among its factors. "
           "The PDF and tables can be rebuilt from the archived report with the following command.")
    p.para("uv run --locked python reproduce.py --from-pdf", font="Courier", size=11, leading=16,
           indent=10, gap=10)
    repo = source_link("https://github.com/VikramMenon09/vehicle-mix-carbon", "Code, data and replication instructions")
    p.para(f"{repo}. The analysis and manuscript were developed with AI assistance.",
           font="Helvetica", size=9.5, leading=13, color=MUTED)
    p.finish()


def render(root):
    data = root / "data"
    results = root / "results"
    annual = read_csv(results / "annual.csv")
    raw = read_csv(data / "vehicle_types.csv")
    types = read_csv(results / "vehicle_types.csv")
    periods = {(int(r["start_year"]), int(r["end_year"]), r["method"]): r
               for r in read_csv(results / "decompositions.csv")}
    extra = json.loads((results / "sensitivity.json").read_text(encoding="utf-8"))
    values = read_csv(results / "valuation.csv")
    output = root / "output/pdf/vehicle-mix-carbon.pdf"
    output.parent.mkdir(parents=True, exist_ok=True)
    c = Canvas(str(output), pagesize=letter, invariant=True, pageCompression=1)
    c.setTitle(TITLE)
    c.setAuthor("Vehicle Mix Carbon project")
    c.setCreator("vehicle-mix-carbon / reproduce.py")
    # Store the publication date across reproducible builds of this edition.
    c.setDateFormatter(lambda *_: "D:20261121120000Z")
    c.setSubject("The contribution of vehicle production mix to US new-vehicle tailpipe CO2, 2010–2023")
    main = periods[2010, 2023, "symmetric"]
    cohort = read_csv(results / "cohorts.csv")
    overview(c, annual, main, cohort)
    data_and_types(c, raw, annual, types)
    method(c, main, periods[2010, 2023, "rates_first"], periods[2010, 2023, "shares_first"])
    extensions.type_attribution(c, types, annual)
    sensitivity(c, periods, extra)
    extensions.firms(c, read_csv(results / "manufacturer_comparisons.csv"),
                     read_csv(results / "manufacturer_pairs.csv"),
                     read_csv(results / "manufacturer_rounded_zero_sensitivity.csv"))
    extensions.cohorts(c, cohort, read_csv(results / "cohort_decomposition.csv"))
    extensions.economics(c, read_csv(results / "lifetime_mileage.csv"),
                         read_csv(results / "carbon_benchmark.csv"), values)
    extensions.broad_firms(c, read_csv(results / "manufacturer_two_types.csv"))
    references(c)
    c.save()
    return output
