# Execution Report 1006-3 — Response Data Source Resolution

Execution ID: **1006-3**. Source prompt: `prompts/prompt1006-3.txt`.
Takeover handoff: `results/1006-3/CODEX_HANDOFF.md` (exact archive).
Date: 2026-10-10, Asia/Shanghai. Starting branch/commit: `master`,
`c43de257d7b5d0af8440a62c9b0bc0530a965b46`.

## Final decision

**FULL_SOURCE_LOCKED**.

Lock the original final optimized Xiang–Quan daily-mean LST product at TPDC,
DOI **10.11888/Terre.tpdc.303150**, for the intended UCDB urban-footprint
2018–2023 climatology. The complete public inventory contains **7,670 daily
files for 2003–2023**; the target subset contains **2,191 days**, including
2020-02-29, and **447,653,756,151 bytes (447.654 GB / 416.910 GiB)**.
Every year's expected calendar, filename and summed byte count passed.
Anonymous per-file HTTP returned real TIFF header bytes. Year/day selection
before transfer makes the target practical on D: with bounded-memory processing.

This is a **source and access decision**, not a payload-integrity certificate
or a new empirical finding. Full-source research data remain **PROPOSED**;
large download approval and `READY FOR ANALYSIS` are both false. No Gate 2B
model or climatology was run. The 36 Zenodo TIFFs remain sample data.

## Scope and relationship to prior executions

This was an **exploratory source/engineering audit**, not a confirmatory test
of H→R or causal effects. The takeover ZIP was extracted, and both handoff and
prompt were read in full before source resolution. Governance, provenance,
experiment and environment policies, recent reports, frozen decisions and
relevant reusable code were inspected. No `AGENTS.md` applied. No subagents,
new environment, package installation, external messages or future execution
were created.

The human's already-run `results/python1006_2/` is an input, distinct from
the earlier engineering-only report1006-2. Its four files were preserved
untracked and hashed in `validation_audit.json`. Its archive audit confirms
36 dates and the local sample ZIP hash
`1f706d128bb4a32bf24a700dd7ed93b435ebbe55dc1da6107cd319a7154980f3`.
Its unit decision was `BLOCKED_METADATA`; documented units are now resolved,
but that does not cure its incomplete calendar. The 12/12 successful city
tests establish compatibility for those examples, not worldwide support.

Gate 1 PASS and Gate 2 FAIL were preserved. The two explicit freeze hashes
and all 16 files in `results/1005-9/primary_outputs_sealed.json` match
(18 checks total). No frozen 1005-x or 1006-1 file was edited.

## Authoritative sources and what each verifies

| Source | Verified claim | Saved evidence / boundary |
|---|---|---|
| [Scientific Data descriptor](https://www.nature.com/articles/s41597-026-08223-x?error=cookies_not_supported), DOI [10.1038/s41597-026-08223-x](https://doi.org/10.1038/s41597-026-08223-x) | Xiang, Junhao; Quan, Jinling; Zhan, Wenfeng (2026), *Global gapless 1 km daily mean land surface temperature (70°N–60°S, 2003–2023) via integrated approaches*; methods, final-product meaning and validation | `paper_evidence.json`; 51-page accelerated accepted manuscript, not assumed fully copy-edited |
| Descriptor Data Records, PDF p.17; Data Availability, p.44 | Complete final product is at TPDC/CSTR, year/day organization, daily mean, Kelvin ×100, GeoTIFF, sinusoidal, 1 km | Reference PDF SHA-256 `83fd2321a8ea7cd56c382898394c5ea8e43ff6fee6139ffec295935a47346197`; 3,825,351 bytes; PDF read in memory, not committed |
| [TPDC dataset](https://data.tpdc.ac.cn/en/data/2f302c7f-00bc-4ace-af30-5fa9277ed16e), DOI [10.11888/Terre.tpdc.303150](https://doi.org/10.11888/Terre.tpdc.303150), [CSTR](https://cstr.cn/18406.11.Terre.tpdc.303150) | Full source identity, 2003–2023 dates, 70°N–60°S band, Int16 / 0.01, instructions, citation terms, record update 2026-09-16 | `source_evidence.json` and `tpdc_citation_evidence.json` |
| Actual TPDC public file-tree APIs | All 21 year directories; every dated daily member and size; complete target and full calendars | `daily_file_manifest.csv`, `inventory_audit.json`; metadata completeness, not whole-file checksums |
| Anonymous HTTP request for 2018-01-01 | Real single-band TIFF access without login/application; header schema, grid, nodata; Content-Length matches manifest | HTTP 200, 203,815,887 advertised bytes, only 65,536 application bytes read; timestamp and prefix hash in `source_evidence.json` |
| TPDC public frontend license/policy mappings | Metadata `license=1` means CC BY 4.0; `sharePolicy=A` means Open Access; site's HTTP/FTP size guidance | Versioned JS URL/response hash and short mapping excerpts in `source_evidence.json` |
| [Author repository](https://github.com/Xiang-junhao/Gapless-Daily-Mean-LST-GEE) | Available annual failure-mask inventory; daily observation/Step-1 QA encoding and annual fitting-RMSE scripts | Tree SHA `d3fe5f74c425f21e332587cde5a247a191a8b865`; README/tree saved; no QA TIFF fetched |
| [Zenodo record 17778992](https://zenodo.org/records/17778992) | Explicitly **sample data**; 0.01 scale; cannot supply the target daily climatology | Record metadata/files snapshot in `source_evidence.json`; prior local sample audit retained |

The complete dataset authors listed by TPDC are **XIANG Junhao and QUAN
Jinling**. Cite their dataset title, TPDC and dataset DOI, and separately
cite the three-author Scientific Data descriptor. Data license is **CC BY
4.0**; the descriptor's **CC BY-NC-ND 4.0** license is different. The author
code repository had no LICENSE in the audited tree; dataset licensing does
not establish a license to incorporate its code.

TPDC's generic `spatialResolution="100m - 1km"` is a category; the descriptor
and actual grid establish the nominal 1-km product. TPDC retains a stale
`journalName="Earth System Science Data"` field, but its related-literature
citation and the actual DOI identify **Scientific Data**. Neither discrepancy
is silently treated as a different product.

## Access, completeness, format and subsetting

The public frontend uses these read/download routes (the doubled `/file/file/`
path is intentional):

```text
POST https://data.tpdc.ac.cn/view/metadataView/detail/
     {"metadataId":"2f302c7f-00bc-4ace-af30-5fa9277ed16e","userId":""}
GET  https://data.tpdc.ac.cn/file/file/getRootFileDataList?metadataId=<dataset-id>
GET  https://data.tpdc.ac.cn/file/file/getFileDataList?parentId=<year-directory-id>
POST https://data.tpdc.ac.cn/file/file/batchDownloadByFileId?fileId=<daily-file-id>
     {"noToken":true}
```

These are the site's public Open Access routes; no authentication was bypassed.
HTTP access needs no persistent account, author contact or application in the
observed route. The site's guest-FTP endpoint returned temporary access
information, but both advertised hosts (`ftp2.tpdc.ac.cn`, `ftp3.tpdc.ac.cn`,
port 6201) reset login attempts. Temporary credentials were neither printed
nor persisted. FTP is not required for the source lock: every target daily
file is below 1 GB, while the UI directs files above 1 GB to FTP. A second
exploratory HTTP probe, 2018-05-16, also returned a valid header. That initial
probe and the failed FTP checks are separately labeled in
`exploratory_access_observations.json`, not disguised as reproducible runner
outputs.

**Temporal selection is available before download** via year/day file IDs.
**Server-side spatial cropping was not documented or verified.** The observed
Range request returned 200 with no Content-Range, so assume full daily
transfers and restart an interrupted file. Close the response after a prefix
for source probes. Batch checkpoints can resume by completed file; byte-range
resume and remote COG access are not established.

| Property | Locked/documented value | Verification extent |
|---|---|---|
| Dates | 2003-01-01 through 2023-12-31; target 2018-01-01 through 2023-12-31 | Every listed date against independently expected Gregorian calendar |
| Organization | `YYYY/YYYY_MM_DD_DMLST.tif` | 7,670 canonical names; no missing, extra, duplicate or malformed dates |
| Grid | 32,402 columns × 15,601 rows; one signed-int16 band | Complete-source 2018-01-01 header; consistent with three prior sample headers |
| Encoding | GeoTIFF, LZW, 256×256 tiles, raw nodata 0 | Actual TIFF tags |
| CRS | Sinusoidal, sphere radius 6,371,007.181 m, central longitude 0 | GeoKeys/GeoDouble parameters and prior full WKT |
| Pixel size | 926.6254331387497 m × 926.6254331387497 m | Native MODIS nominal 1-km grid |
| Origin | x = −12,232,382.342864634 m, y = 7,783,653.638365498 m | Actual upper-left tiepoint |
| Units | Mask raw 0, then `T_K = raw * 0.01`; `T_degC = raw * 0.01 - 273.15` | Descriptor + TPDC instructions; inspected TIFFs do not embed the needed scale/unit |
| Geographic extent | Land between 70°N and 60°S | Descriptor and metadata; coverage is not all planetary latitudes |

No whole-file publisher checksums were exposed by the audited listing. Local
payload SHA-256 and successful decoding must therefore be established after
human acquisition. All payload/grid schemas are not certified by one header.
The inventory total equals both every annual directory's sum and TPDC's
reported total: **1,564,747,711,145 bytes**, about **1.565 TB** for all years.

## QA, reconstruction and scientific limits

The descriptor describes: Step 1 linear combinations of two to four MODIS
overpasses; Step 2 EATC with ERA5-Land surface air temperature and NDVI-weighted
spatial interpolation; Step 3 XGBoost optimization against in-situ LST using
preliminary LST, NDVI, albedo, DEM and DOY. This is a reconstructed daily mean
surface temperature, not a direct 24-hour measurement or air temperature.

Available QA is partial:

- Annual EATC failure masks are listed in the author repository, value 1 for
  failed fitting; target-year masks are available but were not downloaded.
- Daily uint16 QA can be generated in GEE: four 3-bit MODIS error fields,
  bits 12–14 observation count, bit 15 Step-1 temporal-upscaling validity.
- Annual EATC fitting RMSE can be generated in GEE.
- These are **not a verified complete final Step-3 imputation/uncertainty
  layer**. The GEE EATC reconstruction should not be substituted for final
  TPDC files. Generating globally stacked QA would itself require a separate
  volume/access plan; prioritize city-relevant aggregation if authorized.

The reported **1.838 K** daily RMSE is an overall evaluation, not independent
city-domain accuracy. Independent-site evaluation reports **2.073 K** daily
RMSE and **1.511 K** monthly RMSE (59 held-out sites). The accepted manuscript
p.39 separately gives **2.060 K** for a reanalysis-comparison evaluation;
preserve the distinction rather than averaging or treating it as an urban
error bound. The p.43 comparison lists cropland, forest, grassland and wetland,
so it does not establish urban-domain calibration. City-specific retrieval
bias, correlated reconstruction error and long-term smoothing require audit.
Repeated daily samples do not imply independent errors that vanish on averaging.

Reanalysis and surface-property inputs could create, suppress or smooth H-R
structure; they may also share climate information with C. Measurement QA and
sensitivity must address this without adding greenness/morphology mediators
to the primary control set. This limits inference from either a positive or
negative Gate 2B result but does not make the original source unavailable.

## Volume and hardware feasibility

All values below are generated from actual public inventories/header dimensions
by `python1006_3.py`, with independent manifest reconciliation in the decision
audit. Storage/throughput scenarios are arithmetic, not benchmarks.

| Target year | Days | Listed bytes | Decimal GB |
|---|---:|---:|---:|
| 2018 | 365 | 74,404,979,612 | 74.405 |
| 2019 | 365 | 74,650,180,964 | 74.650 |
| 2020 | 366 | 74,911,292,098 | 74.911 |
| 2021 | 365 | 74,624,069,230 | 74.624 |
| 2022 | 365 | 74,737,313,642 | 74.737 |
| 2023 | 365 | 74,325,920,605 | 74.326 |
| **Total** | **2,191** | **447,653,756,151** | **447.654** |

At audit time D: had **1,795,106,619,392 bytes** free and C:
**325,585,063,936 bytes** free. Target raw retention on D: would leave
**1,347,452,863,241 bytes** before intermediates/other use. The full 21-year
product is unnecessary and would consume most available HDD space. C: cannot
hold the entire target; use it selectively for an index/month cache.

One uncompressed int16 band is **1,011,007,204 bytes**; a target time stack is
**2,215,116,783,964 bytes**, before masks or float conversion. Never stack it.
The existing 10,915-city ceiling corresponds to **23,914,765 city-days**;
three numeric float64 fields alone need **573,954,360 bytes**, excluding
IDs, QA and table overhead. Yearly city partitions and accumulators are feasible
on the i7-12700 / 16 GB machine. GPU use is unnecessary for raster reduction.

Transfer-only scenarios: **118.59 h at 1 MiB/s; 23.72 h at 5; 11.86 h at 10;
4.74 h at 25**, without request overhead/retries. The actual acquisition and
HDD processing throughput remain unmeasured. A one-month benchmark must resolve
seek/decompression costs, peak RAM and worker count before promising runtime.

This is a serious multi-hundred-GB workflow, but a practical route exists:
six selected years, at most about 75 GB per year, no terabyte raster stack or
second archive copy, and local city-relevant tile reads. No lower-volume
pre-aggregated city product was verified for this exact response. Consequently
there is no reason to substitute a different product in 1006-3. The source lock
does not mean that transfer or modeling has been approved.

## Scientific consequences and macro roadmap

Preserve the central contribution: similar present state/context can retain
different histories (Gate 1), while those histories may or may not retain
transferable environmental-response information. Nature Cities-level quality
requires global city evidence, scientific novelty, falsification, provenance,
spatial generalization and transparent negative outcomes, not a positive result
at any cost. Pixel processing remains an implementation layer; the inference
unit is the city/agglomeration. Document latitude-band and >=9-pixel sample
limitations before claiming global representativeness.

The source lock removes the immediate temporal-data blocker for Pivot A.
It preserves the intended R, H(t)=B(t)/B(2015), t=1975…2010, and provisional
S3/C1 definitions. It does not amend frozen results or interpret Gate 2's
negative ΔR² as evidence that history never matters.

Two limits in the provisional design need explicit treatment:

1. H precedes R, but **S2020 overlaps R2018–2023**. The project asks about
   conditional predictive information beyond current state, not a causal
   total effect. Do not describe every variable as strictly preceding R.
   A preceding-state sensitivity and actual footprint-vintage audit are
   recommended, **PENDING_SCIENTIFIC_DECISION**, not implemented here.
2. New absolute urban LST differs from YCEO SUHI in product, population,
   footprint and time window as well as rural subtraction. A positive Gate
   2B alone cannot identify rural-reference mixing as the cause of Gate 2
   failure; a negative Gate 2B alone cannot rule out that mechanism. The
   strong implication in `results/1006-1/next_gate_design.md` / handoff should
   be treated as a hypothesis. Common-population/period/boundary comparisons
   or paired urban/rural components are needed for a sharper mechanism test.
   Prior design/results remain frozen; this report records the limitation.

Recommended sequence, each subject to its own future prompt:

- **Acquisition/engineering gate:** human-approved fixed one-month pilot;
  payload hashes and calendar/grid validation; index/reference agreement;
  measured memory/time; then approved yearly processing of the full target.
- **Response-validity gate:** prespecify support, missingness, temporal
  weighting, QA/reconstruction sensitivity, boundary/precedence and common
  support. Report exclusions by region/size without using H-R results to
  choose rules. A negative-control outcome remains a scientific decision.
- **Gate 2B:** use the existing untuned RF (500 trees, leaf 5, max_features
  0.5, seed 42), 10° tile 5-fold and leave-region-out validation, pooled OOF
  metrics and 2,000-draw tile bootstrap. Preserve shuffled-H, pseudo-H,
  redundant S-derived history, random matched vectors, H<=2000, C0/C2,
  random/geographic comparisons, support/strata, twins, transfer, Moran's I
  and negative-control obligations. Do not select definitions by significance.
- **Publication/transfer gate:** a robust positive result needs independent
  transfer/falsification evidence and measurement sensitivity. A rigorous
  negative result can support developmental equifinality without demonstrated
  thermal-response separability under tested specifications. Pivot B requires
  a credible independent multi-epoch morphology source and a new decision;
  sensing-network optimization follows valid response/transfer gates. Do not
  launch extra outcomes or paper writing to rescue a hypothesis in this round.

## Recommended next action

Review `results/1006-3/acquisition_plan.md` and authorize a future **human
acquisition plus verification/benchmark** step. It gives the exact public
route, first pilot file, immutable manifest, separate raw location, resumable
file-level workflow, explicit unit conversion and payload checks. The proposed
spatial index is keyed by grid and geometry/ID hashes; each yearly checkpoint
must carry input hashes/configuration. Keep raw data read-only after verification.

Daily/period interpretation of the initial >=9 rule, missing-day/QA policy,
temporal weighting and relevant design sensitivities are marked
**PENDING_SCIENTIFIC_DECISION** in `source_decision.json`. No new prompt,
downloader, large aggregation pipeline or Gate 2B run was started here.

## Files Created / Modified

| File | Purpose |
|---|---|
| `.gitattributes` | Exact-byte preservation for this prompt and 1006-3 evidence despite existing autocrlf=true |
| `prompts/prompt1006-3.txt` | Exact authoritative prompt archive, 4,913 bytes |
| `scripts/python1006_3.py` | Bounded opt-in public metadata/calendar/header audit; no aggregation or model runner |
| `tests/test_python1006_3.py` | Offline safeguards against boundary/leap-day gaps, duplicate replacement and wrong product/year names |
| `reports/report1006-3.md` | This engineering/scientific source decision report |
| `results/1006-3/CODEX_HANDOFF.md` | Exact takeover handoff archive, 14,237 bytes |
| `results/1006-3/daily_file_manifest.csv` | 7,670 rows with date, canonical name, public file ID, bytes and year |
| `results/1006-3/inventory_audit.json` | Every annual calendar/size audit, target/full totals and hardware scenarios |
| `results/1006-3/source_evidence.json` | Public metadata, license mapping, header tags, Zenodo and author QA inventory, timestamped HTTP hashes |
| `results/1006-3/paper_evidence.json` | DOI/version, PDF hash, page-labeled short excerpts; PDF not saved |
| `results/1006-3/tpdc_citation_evidence.json` | Dataset author/citation fields; unnecessary contact details omitted |
| `results/1006-3/exploratory_access_observations.json` | Separately labeled additional header and failed FTP observations, no credentials |
| `results/1006-3/source_decision.json` | Unique decision, locked source/response, access, QA, hardware and pending scientific policies |
| `results/1006-3/validation_audit.json` | Interpreter/package versions, exact targeted commands/results, guards, frozen hashes and prior-input hashes |
| `results/1006-3/acquisition_plan.md` | Minimal future human acquisition/validation/streaming plan |
| `results/1006-3/artifact_manifest.json` | Package/member hashes and immutable prompt/source/plan evidence hashes |
| `results/1006-3/closeout_audit.json` | Verified source push, exact committed archives, completed cleanup, frozen/prior-input rechecks and stop status |

No raw research rasters or archives are committed. All changes are additions
specific to 1006-3; older scripts, reports, results and raw files are unchanged.

## Tests / Smoke Checks

- Authorized interpreter confirmed: Python **3.11.16**, existing conda
  `py311`. Existing requests **2.34.2**, pytest **9.1.1**, rasterio **1.4.4**;
  no packages installed or upgraded. Bundled pypdf was used only to read
  publisher documentation, not for project scientific computation.
- New runner and test syntax: PASS.
- Targeted offline tests: **8 passed** (3 existing archive/date/zonal tests,
  5 new calendar safeguard cases). Four existing rasterio/Affine
  PendingDeprecationWarnings; no scientific failure.
- Network opt-in and nonempty-output refusal guards: PASS, no network calls
  in these guard checks. Audit outputs are not overwritten by reruns.
- Live bounded metadata audit: exit 0; 21/21 complete calendars, all annual
  size sums and total metadata size match. No actual pixels aggregated.
- Independent target manifest reconciliation: exactly 2,191 expected dates,
  unique file IDs, matching totals and representative Content-Length.
- Frozen hashes: **18/18 match**. Prompt/handoff copy hashes match originals.
  The full 129-test suite was not rerun because no frozen analytical code changed.
- Source commit allowlist: **16 files**. All **11** immutable prompt/evidence
  hashes match both disk bytes and committed Git blobs. New source/report/evidence
  whitespace checks pass. After cleanup, all **18** frozen files and **4** prior
  user-run files were rechecked unchanged; `chatgpt` exists with **0 items**.

The reproducible runner consumed 6,350,970 application bytes of metadata and
one bounded header combined. Across source exploration plus the runner,
two 65,536-byte TIFF prefixes were inspected; **zero complete LST or QA
rasters** were acquired. Application read limits are not lower-level network
buffering measurements. Publisher PDFs/HTML were documentation reads.

## Exact Run Command

```powershell
cd D:\claudecode\urban-history-transfer
conda run -n py311 --no-capture-output python scripts/python1006_3.py --refresh-sources
conda run -n py311 python scripts/verify_project_environment.py
conda run -n py311 python -m py_compile scripts/python1006_3.py tests/test_python1006_3.py
conda run -n py311 python -m pytest -q tests/test_python1006_2.py tests/test_python1006_3.py
```

The first command was run once successfully for the final audit. For a
future authorized reproducibility check, add a **new** `--output-dir`;
existing provenance outputs are refused. Direct HTTP sessions used
`trust_env=False`; no global proxy configuration was changed. The listed
commands reproduce the core metadata/calculation and tests; publisher excerpt,
citation and close-out snapshots were supplementary bounded/local checks.

## Known Limitations; Warnings / Failed Attempts

1. Directory/date completeness is verified at metadata level. Whole-file
   integrity, every-file schema, complete spatial city support and measured
   long-running throughput remain pending acquisition/validation.
2. No spatial subset service or HTTP byte-range resume was established;
   reduced local processing does not reduce the daily transfer footprint.
3. FTP guest login reset on both hosts; the verified daily HTTP route is used
   instead. Standard Nature URLs encountered cookie/redirect failures;
   direct reference URLs with `error=cookies_not_supported` worked. An
   initial exploratory inventory print attempted to sort dictionaries and
   failed; the reproducible runner uses numeric year sorting and succeeded.
4. First excerpt selection failed on a PDF line break; whitespace-normalized
   extraction succeeded, with the same PDF hash. No failed empirical run or
   partially downloaded full research file occurred.
5. QA and independent urban calibration limitations are material (§QA).
   The descriptor is an unedited accepted manuscript and has a comparison
   accuracy difference that is recorded, not concealed.
6. The future footprint support and processing runtime are unknown. The
   1006-2 12-city microbenchmark cannot certify 10,915-city performance or
   exclusions. All source claims carry the retrieval snapshot; APIs/file IDs
   may change and must be reconciled before acquisition.
7. The first staged whitespace check treated preserved Windows CRLF as
   trailing whitespace and a prompt section's equals-sign divider as a
   conflict marker. Path-specific `cr-at-eol` handling resolves the former;
   exact prompt/handoff bytes are verified by hash rather than rewritten to
   satisfy a source-code marker heuristic. New code/report/evidence whitespace
   checks are run separately from those immutable input archives.
8. Automatic approval review rejected the initial computed-path cleanup command
   with `blocked by policy`; it executed no deletion. A separate read-only check
   verified the directory, exactly three ordinary files and their hashes.
   Native PowerShell nonrecursive deletion using those three explicit literal
   file paths succeeded, and an independent check confirmed the empty directory.
9. The source commit pushed successfully over direct connectivity. The first
   direct close-out push later failed to connect to github.com:443. A separate
   session-local HTTP/HTTPS proxy check succeeded and confirmed remote master
   still held the source commit. The close-out push uses that authorized local
   proxy; no global Git configuration is changed.

## Project Structure and Code Map

```text
prompts/                     immutable promptXXXX-X.txt
reports/                     engineering reports; PROJECT_MANIFEST.md is historical
results/1005-*; 1006-1/       frozen analytical/design evidence
results/python1006_2/        prior human run, local input, untracked and retained
results/1006-3/              source evidence, decision and acquisition plan
data/raw|interim|processed/  git-ignored research payloads and derived large tables
docs/                       governance, provenance, experiment, environment policies
environment/                recorded py311 environment exports
src/urban_history_transfer/ environment guard
scripts/                    reusable research/verification modules below
tests/                      offline/regression safeguards
```

| Area | Modules / entry points | Reuse boundary |
|---|---|---|
| Environment | `verify_project_environment.py`, `audit_packages.py`, `check_environment.py`, `smoke_test_scientific_stack.py` | Existing py311, explicit identity checks |
| Gate 1 | `ucdb_gate1_pilot.py`: `load_main_table`, `run_qc`, `build_sample`, `build_H/S/C`; `mtuc_boundary_robustness.py` | Reuse sample/IDs; original `build_H` normalization is not the new B2015 history |
| Thermal / crosswalk | `download_thermal_response.py`, `verify_thermal_response.py`, `thermal_design_lock.py`, `yceo_crosswalk.py`, `run_1005_7_pipeline.py` | Provenance/verification patterns; YCEO ontology stays specific to old response |
| Gate 2 support | `gate2_support.py`, `run_1005_8_pipeline.py` | Reuse tiles, balanced folds, matching and scaling; do not force UCDB R into YCEO units |
| Gate 2 data/models | `gate2_data.py`, `gate2_models.py`, `run_1005_9_pipeline.py`, `gate2_decision_1005_9.py`, `posthoc_ridge_followup_1005_9.py` | Reuse generic evaluation; frozen empirical outputs and cluster joins stay intact |
| Pivot raster verification | `aggregate_lst_zonal.py`, `python1006_2.py` | `inspect_raster`, `zonal_mean`, date/grid/hash helpers; archive READY heuristic is not a complete-calendar gate |
| Current audit | `python1006_3.py` | Opt-in metadata inventory and expected-calendar audit only |

## Code Documentation Status

New runner documents its bounded reads, opt-in flag, immutable-output rule,
calendar criteria and header-only scope; CLI `--help` exposes a single audit
entry point. New tests explain why apparent count/range sufficiency can be
false. Existing raster functions have docstrings and synthetic tests; model
utilities have reusable functions/tests, while orchestration is recorded in
the 1005-x reports. No large aggregation framework was prematurely created.

Relevant technical debt for the next step:

- `python1006_2.decide()` does not require the complete **expected** period;
  numeric unit guesses can produce false readiness. Its date-range/gap and
  scale heuristics need a future explicit product-specification gate.
- Existing `zonal_mean` uses metadata scale by default; this product needs
  explicit overrides. Its arbitrary-edge window/inclusion behavior, overlaps
  and coastal masks deserve benchmark fixtures before an optimized index is
  treated as scientifically equivalent. Do not change inclusion semantics
  silently while optimizing.
- Current raster utility has no all-city/calendar driver, verified-file
  ledger, retry/resume downloader or yearly output schema. Build those as
  reusable layers, with a thin per-execution configuration.
- `gate2_data.assemble_units()` is YCEO-cluster-specific. Reuse `load_cities`,
  S/C blocks and generic models through a UCDB schema adapter; do not blindly
  reuse the old response join. Reuse `gate2_models.h_rebased` for the prescribed
  B2015 denominator, not the frozen Gate 1/2 default history.
- Importing date/hash helpers from `python1006_2` brings its scientific-stack
  dependencies into a metadata-only tool. Requests already exists but is not
  declared in pyproject; record/pin this engineering dependency or factor out
  lightweight helpers in a later authorized maintenance step.
- README/PROJECT_MANIFEST are historical and do not present the latest gates;
  this report and source decision are the takeover reference. A future update
  should consolidate status without rewriting frozen conclusions.

## Reuse Map for Next Round

Reuse `parse_date_from_name`, `sha256_file`, `grid_signature`,
`discover_ucdb_polygon_layer` and the Gate 1 sample IDs; add a specification-
driven expected-calendar validator. Use `inspect_raster` and `zonal_mean` as
the inspection/reference path, with scale 0.01 and Celsius offset −273.15.
Reuse the geometry layer/ID mapping already tested by 1006-2.

The main new capability should be a sparse native-grid **tile → pixel/city
membership** cache plus a verified-date ledger and bounded yearly accumulator.
Do not allocate a dense global city-label time stack. Reuse `tile_ids`,
`balanced_group_folds`, `oof_predict`, `delta_metrics`, `tile_bootstrap_delta`,
history nulls, twins, transfer and `morans_i` when a later prompt authorizes
models. Keep H/S/C construction, payload verification and response joining
separate so the same generic validation can serve later scientific rounds.

## Deviations from Authorized Plan

None. The source audit script is justified by enumerating 7,670 files,
independently validating leap-aware completeness, generating exact volumes
and retaining bounded access evidence. Tests specifically protect the source
decision from the sparse-sample and duplicate-day failure modes. Alternatives
were not substituted or expanded into an unnecessary benchmark because the
original complete source was verified and is feasible. Future engineering and
scientific recommendations are planning only.

## Git

Starting branch: `master`; remote:
`https://github.com/JunYue0214/urban-history-transfer.git`.

Source audit commit: **`c5fa8df4baa940f85c2fcdfb856815190931feb8`**,
`1006-3: lock complete TPDC daily LST source and bounded acquisition plan`.
**Push SUCCESS** to `origin master`; `git ls-remote` independently confirmed
that remote master equals that commit. The commit contains only the 16
1006-3-related additions, excluding staging inputs and prior human-run files.
The source push used direct connectivity; no global Git proxy was changed.

The close-out follow-up commit contains only this updated report and
`results/1006-3/closeout_audit.json`. Its hash is obtained from Git history
because a committed file cannot contain its own commit hash. Its final push
and remote equality are verified after committing, then reported to the human.
After the failed direct close-out push, only its retry/check command sessions
set `HTTP_PROXY` and `HTTPS_PROXY` to `http://127.0.0.1:7890` as authorized.
Prior human `results/python1006_2/` remains untracked and untouched.

## Close-out

Prompt archived: **YES**. Exact SHA-256:
`3bab4aad9341867705a0abca62f07dad71659b5d01382c7e65afab27b6a0eac1`.
Handoff exact SHA-256:
`1012703984a9d34dc051ad9420cf82b711471190d761256a3907c625d11e09bc`.

chatgpt staging directory cleaned: **YES**. Only the verified takeover ZIP
and its two extracted input files were removed after the source commit/push;
the directory is preserved and independently verified to contain **0 items**.
`closeout_audit.json` records the exact archives, actual source commit/push,
cleanup and unchanged frozen/prior-user hashes. Tracked worktree was clean
before writing this close-out update, with only prior human results untracked.

Work stops after 1006-3. No large research-data acquisition, Gate 2B,
sample climatology or next execution was started. The unique decision remains
**FULL_SOURCE_LOCKED**, with research data still **PROPOSED**.
