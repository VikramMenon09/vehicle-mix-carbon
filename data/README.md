# EPA source and extraction

The archived source is the U.S. Environmental Protection Agency’s *2024 EPA Automotive Trends Report* (EPA-420-R-24-022, November 2024). The archive preserves the edition that published tailpipe CO₂ rates alongside production shares for each vehicle type. The national study uses the continuous series of final annual observations in Table 3.2, model years 2010 through 2023. The 2024 row in this edition is preliminary. [EPA publication page](https://www.epa.gov/automotive-trends/download-2024-automotive-trends-report) · [Original PDF](https://nepis.epa.gov/Exe/ZyPDF.cgi?Dockey=P101CUU6.pdf)

## Input files

| File | Contents | Units and precision in the source |
| --- | --- | --- |
| [vehicle_types.csv](vehicle_types.csv) | Table 3.2, printed p. 43. One row for each of five types per year (70 rows). | `production_share_pct` is percent of U.S. new light-duty vehicle production by model year, to 0.1 percentage point. `co2_g_per_mile` is estimated real-world tailpipe CO₂, rounded to whole grams per mile. |
| [fleet.csv](fleet.csv) | Table 3.1, printed p. 42. One reported fleet mean per year (14 rows). | `co2_g_per_mile` is the independently tabulated fleetwide rate, in whole grams per mile. |
| [production.csv](production.csv) | Table 2.1, printed p. 14. Annual production for the U.S. market (14 rows). | `vehicles` equals the published count in thousands multiplied by 1,000. These counts retain the precision of the table. |
| [epa-automotive-trends-2024.pdf](raw/epa-automotive-trends-2024.pdf) | Complete, unmodified EPA report. | SHA-256 `303e9e3a1124b72fd81c20b5949a40f856469d7b4f5ab6de8b437e92cb7a3c20` |

The three national CSVs use the EPA model year in the `year` field. The source orders the five `vehicle_type` values as Sedan/Wagon, Car SUV, Truck SUV, Minivan/Van, and Pickup. EPA splits SUVs by regulatory car or truck class. Vehicles manufactured abroad and delivered for sale in the U.S. are within scope. The annual shares preserve the source’s printed precision, so a year’s shares may sum to 99.9% or 100.1%.

EPA estimates the rates from standardized tests and weights output by the number of new vehicles delivered for sale in the U.S. Calendar-year registrations, the mileage of vehicles already in use, upstream emissions, and lifecycle emissions fall outside this measure. Appendix D describes a coverage change in 2011 when the series began to include some medium-duty passenger vans and SUVs as well as alternative-fuel vehicles. EPA estimates the medium-duty inclusion raised the 2011 fleet rate by 0.3 g/mi. The revised derived five-cycle test conversions also apply starting with 2011. See printed pp. 3–4, 17–18, and D-4 to D-6.

## Rebuild the CSVs

With Python and Poppler’s `pdftotext` available, run the following command from the repository root.

```sh
python scripts/extract_data.py
```

Extraction requires no network connection. The script verifies the archive checksum, reads PDF file pages 23, 51 and 52 in layout order, checks the annual data against the expected table layouts, verifies that the reported fleet rate matches across Tables 2.1 and 3.1, and writes the three CSVs with a fixed column order and LF line endings. Use `--output-dir` to extract into a separate directory for comparison. The main analysis can run directly on the included CSVs.

## Manufacturer cross-section

The two manufacturer files cover final model year 2023. Each includes the 14 individual manufacturer groups that EPA identifies in section 1.B. Each group produced at least 150,000 new vehicles for the U.S. market. Together they accounted for more than 97% of national production. `Other` pools the smaller manufacturers, and `All Manufacturers` is the national comparison row. Adding either aggregate to a list of individual firms would double-count observations or mix different units of analysis.

| File | Source and fields |
| --- | --- |
| [manufacturers.csv](manufacturers.csv) | Table 3.3, printed p. 44. Each `manufacturer` has its own fleetwide estimated real-world tailpipe `co2_g_per_mile`. |
| [manufacturer_types.csv](manufacturer_types.csv) | Table 3.4, printed p. 45. Each `manufacturer` has five `vehicle_type` rows. Each `production_share_pct` uses that manufacturer’s production as the denominator. Each `co2_g_per_mile` gives that manufacturer’s rate for that type. |

The tables do not report individual manufacturers’ shares of national production. A dash across a type's three source columns becomes an explicit row with empty share and rate. A printed 0.0% paired with a rate retains both values. For example, Stellantis reports 0.0% car SUVs and 329 g/mi. A reported zero for emissions also survives extraction, including the three vehicle types that Tesla produced in this table.

To rebuild this cross-section from the same archived PDF, run `python scripts/extract_manufacturers.py`. It reads printed pp. 44–45 (PDF file pages 53–54), checks the row and cell layout, and accepts the same `--pdf` and `--output-dir` options as the annual extractor.
