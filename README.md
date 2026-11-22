# How vehicle mix shaped U.S. tailpipe emissions

New U.S. light-duty vehicles emitted an estimated **18.9% less CO₂ per mile** in model year 2023 than in 2010. Every major vehicle type improved. But truck SUVs rose from 20.7% to 45.3% of production, and the changing mix offset **28.8% of the gains within vehicle types**.

[Read the research paper (PDF)](output/pdf/vehicle-mix-carbon.pdf) · [Source data and definitions](data/README.md) · [Replication checks](REPLICATION.md)

## Results

| Question | Result |
| --- | --- |
| How much did production mix offset lower emissions rates? | Lower rates within the five types reduced the average by 104.5 g/mi. Changing shares added 30.1 g/mi, leaving a net reduction of 74.4 g/mi. |
| What would 2023 look like at the 2010 mix? | At 2023 type-specific rates the average would be 291.9 g/mi, versus 319.2 at the actual mix. This 27.3 g/mi gap uses one set of rates. The 30.1 g/mi figure averages the effects evaluated at 2010 and 2023 rates. |
| Does the mix affect manufacturer comparisons? | Among the three manufacturers with a positive printed share in all five types, Honda’s average was 8.1 g/mi below Toyota’s with their own mixes and 8.8 g/mi above Toyota’s using the same national mix. A second analysis compares all 14 named manufacturers within two common vehicle types. |
| Does a cleaner mile mean lower total emissions for a model-year cohort? | Give each vehicle 10,000 miles. The illustrative total grows from 43.75 million tonnes for the 2010 cohort to 45.32 million for 2023 as production expands. Starting with the larger 2013 cohort yields a decline from 55.86 million tonnes. |
| How large is the carbon difference over a common distance? | Over 10,000 miles, the 2023 actual mix adds 0.273 tonnes per vehicle relative to 2010 shares. Valued at a published 2020 emissions-pulse benchmark of $185 per tonne, this equals $50.59 in 2020 dollars. [Rennert et al. (2022)](https://doi.org/10.1038/s41586-022-05224-9) |

## Reproduce

From the repository root, rebuild the tables, charts and PDF from the included CSVs with Python 3.12 and [uv](https://docs.astral.sh/uv/). The first run installs the locked PDF dependencies.

```sh
uv run --locked python reproduce.py
uv run --locked python -m unittest discover -s tests -v
```

For full source replication, install Poppler so that `pdftotext` is on the path. This command also re-extracts the five input CSVs from the archived EPA PDF.

```sh
uv run --locked python reproduce.py --from-pdf
```

For numerical results alone, use Python’s standard library and the included CSVs. This command runs offline.

```sh
python3 reproduce.py --analysis-only
```

## Data and interpretation

The 2024 EPA Automotive Trends Report provides production counts, shares and estimated real-world tailpipe rates. This edition includes final annual data from 2010 through 2023 in its vehicle-type table, including imports delivered for sale in the U.S. The study covers 70 national type-year observations, 14 annual production counts, and a separate 2023 manufacturer cross-section. The archive includes the complete EPA PDF, its checksum and extraction scripts. [EPA publication](https://www.epa.gov/automotive-trends/download-2024-automotive-trends-report)

The national decomposition holds type-specific rates or production shares fixed in turn. The cohort calculation introduces production volume as a third factor and averages over all six update orders. The paper also checks annual chaining, alternative dates, pooled SUVs, printed-data precision, and different lifetime mileage for regulatory cars and trucks. These are accounting comparisons. They do not identify consumer demand, the effects of fuel-economy policy, or total lifecycle emissions.

## Explore the results

| Result files | Contents |
| --- | --- |
| [Annual rates](results/annual.csv) · [Decompositions](results/decompositions.csv) · [Contributions by type](results/vehicle_types.csv) · [Sensitivity](results/sensitivity.json) | National trajectory, four weighting methods, per-type contributions and source-rounding bounds |
| [Manufacturer eligibility](results/manufacturer_support.csv) · [Five-type comparison](results/manufacturer_comparisons.csv) · [All pairs](results/manufacturer_pairs.csv) | Coverage and manufacturer rates under their own and common national production shares |
| [Two common types](results/manufacturer_two_types.csv) · [Rounded-zero sensitivity](results/manufacturer_rounded_zero_sensitivity.csv) | Comparison among all 14 named firms, plus a separate five-type check that admits a measured rate at a printed share of 0.0% |
| [Annual cohorts](results/cohorts.csv) · [Three-factor decomposition](results/cohort_decomposition.csv) | Hypothetical 10,000-mile emissions and contributions from production volume, mix and rates |
| [Lifetime mileage](results/lifetime_mileage.csv) · [Published carbon values](results/carbon_benchmark.csv) · [Illustrative prices](results/valuation.csv) | Physical exposure and dollar scenarios with their units and mileage assumptions |

The analytical source is in [scripts](scripts/) and the manuscript and vector figures are in [paper](paper/). This project was developed with AI assistance.
