# 1006-3: minimal acquisition and verification plan

Source prompt: `prompts/prompt1006-3.txt`.
Decision: **FULL_SOURCE_LOCKED**.
This plan describes future work. It does not authorize or initiate acquisition,
response aggregation, or Gate 2B. Full-source research data remain **PROPOSED**.

## Locked source and acquisition scope

Use Xiang and Quan's **final optimized daily-mean LST product** from TPDC,
DOI [10.11888/Terre.tpdc.303150](https://doi.org/10.11888/Terre.tpdc.303150),
[dataset page](https://data.tpdc.ac.cn/en/data/2f302c7f-00bc-4ace-af30-5fa9277ed16e).
Cite the dataset and its Scientific Data descriptor separately. Data license:
CC BY 4.0. Keep the source/date/version attribution with derived city tables.

The full inventory is `daily_file_manifest.csv`. Select `year` 2018 through
2023 **before transfer**: 2,191 dated files, 447,653,756,151 bytes. Do not fetch
the other 15 years or use the Zenodo sample archive as the response. Local
full-source files should have a separate directory, for example
`data/raw/urban_lst/tpdc_303150/YYYY/YYYY_MM_DD_DMLST.tif`, so the existing
`data/raw/urban_lst/2018-2023.zip` is preserved as sample data.

The verified anonymous public route is:

```text
POST https://data.tpdc.ac.cn/file/file/batchDownloadByFileId?fileId=<file_id>
Content-Type: application/json
Body: {"noToken": true}
```

Use the file IDs and expected bytes in the locked manifest. The tested
2018-01-01 ID is `149b7c59-ec00-49cd-ba66-10be4301b1b1`, expected size
203,815,887 bytes. No account, author contact, or data application was needed
for this route. Individual target files are at most 209,027,206 bytes, below
the site's 1 GB HTTP/FTP guidance. The site also advertises guest FTP; both
FTP login probes reset, so the plan depends on the verified HTTP route.

HTTP Range was ignored in the test. Do not assume byte-range resume, COG
remote reads, or server-side spatial cutouts. Restart a failed daily transfer;
resume a batch by skipping only locally completed, verified files. Check that
the response is TIFF bytes rather than an HTML/JSON error with status 200.
Write to `.part`, validate, then rename atomically. A future human-operated
acquirer should use low concurrency, bounded retries and an explicit scope
and byte budget; it must never expand to the whole product by default.

## Ordered work after a new authorization

1. Obtain explicit PI approval for a fixed **2018-01 engineering pilot** and
   the larger six-year scope, or keep approval limited to the pilot. Advance
   the data state only with evidence:
   `PROPOSED -> PI APPROVED -> HUMAN DOWNLOADED -> HASH VERIFIED -> READY FOR ANALYSIS`.
   A source lock is distinct from these research-data approvals.
2. Human acquisition of the approved daily files to D:, retaining source URL,
   manifest ID, timestamp, actual byte count and SHA-256. No official payload
   checksums were found in the audited listing; a local hash establishes a
   reproducible received copy, not publisher-to-local checksum equivalence.
   Reconcile a refreshed inventory with this snapshot if a file ID or size
   changes; never silently replace a file under an existing hash.
3. Validate every file: independent Gregorian expected-date set, no missing
   or duplicate dates, matching filename/manifest size, successful full tile
   decode, one signed-int16 band, nodata zero, and identical CRS, transform,
   dimensions and grid fingerprint. Use leap day 2020-02-29 explicitly in the
   full target calendar gate. A first/last-date check is insufficient.
4. Apply the documented unit conversion explicitly:
   mask raw zero, then `T_degC = raw_int16 * 0.01 - 273.15`.
   Inspected TIFFs do not embed the 0.01 scale or Kelvin unit. Numeric
   plausibility is a diagnostic, never the unit authority.
5. Before scientific aggregation, record boundary vintage, city IDs,
   raster-polygon inclusion semantics, overlap handling and the response
   support/QA policy. Preserve the initial >=9 valid 1-km pixels rule; its
   per-day/period interpretation, missing-day rule and temporal weighting
   are **PENDING_SCIENTIFIC_DECISION**. Equal-calendar-day city means are the
   proposed way to avoid giving more weight to days with more valid pixels.
   Do not choose these policies after examining H-R associations.
6. Precompute a sparse tile/pixel-to-city membership index in the native
   sinusoidal grid, keyed by both grid and geometry/ID hashes. Reuse
   `aggregate_lst_zonal.zonal_mean` as a correctness reference with explicit
   scale/offset and its pixel-centre convention. Compare optimized and
   reference means and counts on deterministic cities including coastal,
   fragmented, small and large footprints; address overlap/multiple
   memberships without silently assigning a shared pixel to one city.
7. Benchmark the authorized month with deterministic tile order and bounded
   reads. Record peak RAM, wall time, bytes read, disk usage and equality
   tolerances. Start with one I/O worker, a bounded GDAL cache and a proposed
   <=8 GB process RAM budget; increase workers only after measurements show
   a benefit. Compare sorted sparse tile reads against sequential reads on
   the HDD if seeks dominate. The 12-city sample timing is not a full-scale
   runtime estimate. GPU processing is unnecessary for this stage.
8. Only after these checks and authorization, acquire/process the remaining
   days in one-year batches. Keep raw files on D:, optional one-month cache
   and the spatial index on C:, and yearly city-level sums/counts or daily
   Parquet partitions. A checkpoint should name each input hash, grid/index
   hash, configuration and completed date. Never skip a missing day, pool
   incomplete months as a climatology, or construct an in-memory raster
   time stack. Raw deletion/retention is a separate future decision.
9. Release a final city response table only with complete calendar and
   prespecified support/QA reports, exclusions by region/size, source/grid
   lineage and reproducible response uncertainty limitations. Then a new
   scientific prompt may authorize Gate 2B using the existing spatial
   evaluation, nulls, twins, transfer and bootstrap modules.

## Feasibility bounds

The largest target year is 74,911,292,098 bytes. At audit time D: had
1,795,106,619,392 bytes free: retaining all target raw files would leave
1,347,452,863,241 bytes before intermediates and other use. C: had
325,585,063,936 bytes free and should not hold the whole target. Avoid a
second large archive/extraction copy.

The native grid contains 505,503,602 pixels. A single uncompressed int16
band is 1,011,007,204 bytes; the target int16 stack alone is
2,215,116,783,964 bytes. This rules out stacking on a 16 GB machine. The
10,915-city upper bound gives 23,914,765 city-days; three float64 numeric
fields alone occupy 573,954,360 bytes, excluding IDs, masks, table overhead
and QA. Partitioning by year is still preferable.

Transfer-only arithmetic for 447.65 GB is 118.59 h at 1 MiB/s, 23.72 h at
5 MiB/s, 11.86 h at 10 MiB/s or 4.74 h at 25 MiB/s. These are scenarios,
not measured throughput or an aggregation ETA. Availability and throughput
of all payloads have not been verified by downloading them.

## QA and scientific stop conditions

The author repository supplies annual EATC failure masks; daily MODIS/Step-1
QA and annual EATC RMSE require GEE generation. These do not establish a
complete final Step-3 uncertainty or imputation-provenance mask. No QA
raster was downloaded here. GEE reconstruction scripts describe a preliminary
product and must not replace the final TPDC product. The repository has no
LICENSE file in the audited tree; do not assume its source-code reuse license
from the dataset's CC BY license.

Reconstruction uses ERA5-Land air temperature, NDVI, albedo, DEM and DOY.
Before modeling, plan a city-domain/reconstruction audit that addresses
possible climate dependence and smoothing of developmental signals, without
adding likely mediators to the primary C block. If sufficient QA cannot be
obtained, state the resulting limits and seek a scientific decision before
confirmatory modeling. No claim that gap filling provides independent
daily errors or that errors disappear on temporal averaging is justified.

Keep Gate 2 frozen. A difference between old SUHI and new absolute urban LST
can reflect changes in response, period, boundary and population as well as
rural-reference subtraction. It is evidence about response dependence,
not an isolated causal test of rural-reference mixing. S2020 overlaps the
2018-2023 response window, and fixed boundaries may encode later extent;
record these limits and preregister a precedence sensitivity.

The next authorization should resolve these scientific policies and the
acquisition scope. No next execution or model is started by 1006-3.
