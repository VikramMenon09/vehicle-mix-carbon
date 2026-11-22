# How vehicle mix shaped U.S. tailpipe emissions

From model year 2010 to 2023, estimated tailpipe CO₂ fell in all five major types of new U.S. light-duty vehicles. Over the same period, truck SUVs grew from 20.7% to 45.3% of production. How much did the change in what manufacturers delivered for sale offset the gains within each vehicle type?

**The changing mix offset 28.8% of the within-type improvement.** Lower emissions rates within types reduced the fleet average by 104.5 grams per mile. Changing production shares added 30.1 g/mi back, leaving a net decline of 74.4 g/mi. [Read the five-page paper](output/pdf/vehicle-mix-carbon.pdf).

| Model year 2023 comparison | Tailpipe CO₂ |
| --- | ---: |
| Using actual production shares | 319.2 g/mi |
| Using model year 2010 production shares | 291.9 g/mi |
| Difference over 10,000 miles at equal mileage per type | 0.273 metric tonnes |

The 27.3 g/mi gap in this comparison holds 2023 emissions rates fixed. The 30.1 g/mi mix contribution averages that gap with the corresponding calculation at 2010 rates.

## Reproduce the study

From the repository root, use Python 3.12 and [uv](https://docs.astral.sh/uv/) to regenerate the tables, charts and PDF from the included CSVs. The first run installs the locked PDF dependencies.

```sh
uv run --locked python reproduce.py
uv run --locked python -m unittest discover -s tests -v
```

The numerical analysis also runs offline with the Python standard library alone.

```sh
python3 reproduce.py --analysis-only
```

To repeat the extraction from the original EPA PDF as well, install Poppler (for `pdftotext`) and run the full pipeline.

```sh
uv run --locked python reproduce.py --from-pdf
```

## Data and results

The source is the 2024 EPA Automotive Trends Report, Tables 3.1 and 3.2. The extract has 70 vehicle-type observations and 14 published fleet averages. The 2024 observation in this edition was preliminary, so the study ends with 2023. The archived source, its checksum, table locations, and units are documented in the [data notes](data/README.md).

| Output | Contents |
| --- | --- |
| [Annual estimates](results/annual.csv) | Reconstructed fleet rates, fixed-2010-share rates and differences from EPA’s published values |
| [Decompositions](results/decompositions.csv) | Within-type, mix and net changes for four periods and four weighting methods |
| [Vehicle types](results/vehicle_types.csv) | Endpoint shares and rates, raw contributions, and contributions centered on the average of the two endpoint fleet rates |
| [Sensitivity checks](results/sensitivity.json) | Results with the two SUV classes combined and bounds implied by the precision of Table 3.2 |
| [Carbon valuation](results/valuation.csv) | Implied dollar value of the fixed-mix gap at three assumed carbon prices |

## Method

Annual emissions are the production-weighted mean of the five type-specific rates. EPA rounds shares to 0.1 percentage point and rates to the nearest gram per mile. The main estimates divide each year’s printed shares by their sum. Across the 14 years, the largest absolute difference from the published fleet series is about 0.79 g/mi, in 2015.

The symmetric decomposition weights each type’s rate change by its average endpoint share and each share change by its average endpoint rate. These two contributions sum to the change in fleet emissions. The sensitivity analysis also updates rates first, updates shares first, sums annual changes, moves the baseline to 2013, and combines car SUVs with truck SUVs.

For the rounding check, the underlying shares must sum to one in each year and fit within their individual rounding intervals. With five types, the five midpoint rates have 32 possible combinations of interval endpoints. At each combination, the code computes the lowest and highest admissible mix contributions by assigning available share to the lowest- or highest-rate types first. The result spans 29.5 to 30.7 g/mi.

This is an accounting study of new vehicles. It uses estimated real-world tailpipe rates and production weights. Mileage by vehicle type, used vehicles, upstream emissions, and behavioral responses to prices fall outside the estimates. The carbon prices are illustrative inputs.

The Python source for the figures and manuscript is in [paper](paper/). This project was developed with AI assistance.
