# Acquisition plan (all datasets PROPOSED; nothing downloaded)

| Dataset | State | What is verified | What is not |
|---|---|---|---|
| Xiang & Quan, "Global gapless 1 km daily mean land surface temperature dataset (2003-2023)", Zenodo DOI 10.5281/zenodo.17778992 | **PROPOSED** | via search snippets only: 25.2 GB total in four zips (2003-2007, 2008-2012, 2013-2017, 2018-2023); gap-filled daily-mean LST; validation RMSE 1.838 K | the Zenodo page and the paper were not read (WebFetch blocked): file format, band/variable name, scale factor, nodata, per-zip sizes, licence, spatial extent, whether a day/night split exists |
| YCEO SUHI v4 | LOCAL | validated in 1005-7 | contains SUHI only |
| GHS-UCDB / MTUC | LOCAL | used since 1005-4 | n/a |

A pre-aggregated city-level urban LST table was **not found**; the plan does not assume one exists.

## Step 0 — human reads the record (no data transferred)
Open https://doi.org/10.5281/zenodo.17778992 in a browser and send the PI: (1) exact file names and sizes; (2) the description of the variable
(name, units, scale factor, nodata, daily-mean definition, extent, CRS, format); (3) the licence and citation; (4) whether any quality/imputation flag is provided.

## Step 1 — only after PI approval: one file
Download **only** the 2018-2023 zip (expected ≈ 6 GB on average per zip; unverified), not all four. Use a browser, or the project downloader:

```powershell
cd D:\claudecode\urban-history-transfer
$env:HTTP_PROXY="http://127.0.0.1:7890"; $env:HTTPS_PROXY="http://127.0.0.1:7890"   # session only, if needed
conda run -n py311 python scripts/download_thermal_response.py `
  --url "<EXACT_ZENODO_FILE_URL_FROM_STEP_0>" --dest "data/raw/urban_lst" --confirm-human-operator
```
The downloader refuses non-loopback URLs unless `--confirm-human-operator` is passed, never overwrites, resumes, and logs SHA-256.
The `--dataset-key` option is deliberately omitted: the downloader only knows the two 1005-6 candidates.

## Step 2 — verify
`scripts/verify_thermal_response.py` for zip integrity; then `scripts/aggregate_lst_zonal.py --inspect` (header-only, reads no pixel arrays)
to confirm band count, dtype, nodata, CRS and extent against Step 0.

## Step 3 — aggregation (1006-2, not 1006-1)
`aggregate_lst_zonal.py` computes per-footprint mean over valid pixels, windowed, with valid-pixel counts. It is tested here on a synthetic
GeoTIFF only. If the real data cannot be read within memory limits or lack a usable urban-LST column, report to the PI; do not substitute another dataset silently.

## Storage and hardware
Raw 2018-2023 zip: expected a few GB to ~10 GB; extracted size unknown. Free space on D: is ≈ 1.68 TB; RAM 15.7 GB, so windowed reads are mandatory.
Total expected new raw data: ≤ ~25 GB even if all four zips were wanted; the plan asks for one. This is below the 50 GB flag.

## Fallback
If the archive proves unusable, or the pre-conditions in `next_gate_design.md` fail, stop Pivot A and either (a) search for a multi-epoch morphology source
for Pivot B, or (b) close the history hypothesis and write up Gate 1 + Gate 2 as a negative result.
