# Replication checks

The study uses a fixed EPA release. A complete build starts from the archived PDF, extracts the national and manufacturer tables, regenerates the result files and typesets the paper. The GitHub workflow removes generated inputs and outputs in its disposable checkout before the build. This catches a missing step that could otherwise leave an old chart or table in place. [Build workflow](.github/workflows/replication.yml)

## 1. Check the source

The extraction verifies the PDF’s SHA-256 checksum. Model years run from 2010 to 2023. Shares, rates, manufacturer labels and missing cells retain the distinctions used in the report. Independent reads of the PDF confirmed the 70 national type rows, 14 fleet benchmarks, 14 production totals, all 16 manufacturer or aggregate benchmarks and all 80 manufacturer/aggregate type cells. The latter include 18 cells printed as dashes. The 2023 national row in Table 3.4 also repeats the five national cells in Table 3.2. [Source notes and archive](data/README.md)

Reconstructing the national fleet rate from the rounded type table gives the largest absolute discrepancy in 2015, 0.7932 g/mi from the published fleet mean. The manufacturer analysis separately checks reconstructed own-mix rates against Table 3.3. A corrupted source fails the checksum check. Missing rates, a printed 0.0% with a measured rate, and actual zero emissions have separate tests. [Manufacturer extraction tests](tests/test_extract_manufacturers.py)

## 2. Check the independent arithmetic

| Check | Comparison |
| --- | --- |
| National result | Exact fractions and four combinations of endpoint shares/rates reproduce −104.4969 g/mi within types and +30.1292 g/mi from mix. Reversing the endpoint order reverses the signs. |
| Rounding | Independently enumerating feasible share vertices yields a mix interval of 29.50850 to 30.69725 g/mi. This constrains shares and rates to Table 3.2’s printed precision. It is a rounding interval, separate from statistical or test-cycle uncertainty. |
| Manufacturer result | Independent computations from EPA Table 3.4 recover the three full-support firms, all pair gaps and all 14 two-type comparisons. The Honda-minus-Toyota standardized gap is +8.753 g/mi. The five type-specific contributions are +2.250, −1.875, +6.795, +3.200 and −1.617 g/mi, in source order. |
| Cohort result | The main code averages six update orders. The independent test expands quantity × share × rate and gives one-half of two-factor interactions and one-third of the three-factor interaction to each participating factor. Both yield +11.0066, +3.7989 and −13.2394 million tonnes for volume, mix and rates. |
| Exposure and dollars | Independent calculations verify the 14 annual cohort totals, both lifetime mileage scenarios and the valuation in 2020 dollars per vehicle. All mass calculations use one million grams per metric tonne. |

The exact-fraction checks for the national, cohort and exposure results run directly against the published CSVs and import no production modules. [Independent calculations](tests/test_replication.py) · [Manufacturer tests](tests/test_manufacturer_analysis.py) · [Rounding tests](tests/test_rounding.py)

## 3. Check the publication

The PDF uses the machine-readable results and vector figures. The revision was reviewed for agreement with its source tables, separation of the two national mix estimates, manufacturer support, starting-year sensitivity, mileage denominators and carbon-price interpretation. All ten pages were rendered for visual review. A fresh rebuild can be compared with the committed tables and PDF using the following commands.

```sh
uv run --locked python reproduce.py --from-pdf
uv run --locked python -m unittest discover -s tests -v
git status --porcelain --untracked-files=all -- data results output/pdf
```

An identical rebuild prints no paths in the final command. [Finished paper](output/pdf/vehicle-mix-carbon.pdf)
