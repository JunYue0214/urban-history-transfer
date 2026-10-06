# Execution Report 1006-2

Execution ID: 1006-2 · Source prompt: `prompts/prompt1006-2.txt` · Previous: 1006-1
Task: apply the ChatGPT-authored package for the urban-LST archive **verification** step (engineering only)

**No research data were downloaded, no real archive was read, `scripts/python1006_2.py` was not run against real data, no Gate 2B model was fitted, and no H value was inspected. The scientific decision is not made here.**

---

## 1. Files created / modified

| File | Change |
|---|---|
| `prompts/prompt1006-2.txt` | created (authoritative prompt, copied from the package) |
| `scripts/python1006_2.py` | created (verification runner) |
| `tests/test_python1006_2.py` | created (3 synthetic tests) |
| `scripts/aggregate_lst_zonal.py` | **modified** (1006-1 version replaced by the package version) |
| `reports/report1006-2.md` | created (this file) |

Not touched: `results/1005-*`, `results/1006-1/*` (hash of `gate2_negative_result_freeze.md` and `results/1005-9/gate2_decision.json` identical before and after). `chatgpt/` was staging only and is not committed.

## 2. Supplied code used unchanged?

**YES.** All four package files are byte-identical to the package (SHA-256 compared after copy). No compatibility edits were made. The only repository change beyond adding files is the package's own replacement of `scripts/aggregate_lst_zonal.py`.

What the replacement changes (diff against the 1006-1 version): `inspect_raster` now also returns `driver`, `transform`, `units`, `block_shapes`, `compression`, `descriptions`, `tags`, `band_tags`; `zonal_mean` gains a guard for `None`/empty geometries and casts to float64 before averaging; the docstring is expanded. Signatures and the `(index, mean, n_valid, n_pixels)` return format are unchanged, and the 9 existing 1006-1 tests that import this module still pass. The CLI still exposes only `--inspect`.

## 3. Syntax / smoke-test results

* `py_compile` on all three supplied Python files: exit 0.
* `tests/test_python1006_2.py`: **3 passed** (date parsing, synthetic zip + raster inspection + unit inference, synthetic zonal mean).
* Regression: `tests/test_pivot_design_1006_1.py` 9 passed. **Full suite: 129 passed.**
* Extra smoke test, synthetic data only, outputs written to a temp directory and deleted: `main()` run end-to-end on a fake 3-file zip (global 0.05° grids, `units=kelvin`). Exit 0, status SUCCESS, decision `READY_FOR_AGGREGATION`, and all four output files written. It exercised the real UCDB GeoPackage for polygon discovery and CRS reprojection (ESRI:54009 → EPSG:4326). The repository's `results/python1006_2/` was not created.
* Local-only checks of the runner against existing data: the discovered polygon layer is `GHSL_UCDB_THEME_CLIMATE_GLOBE_R2024A`; its 11,422 geometries are identical to the layer used in 1005-8 (same IDs, same order), so the choice is harmless here. The 12 deterministic test IDs come from the Gate 1 sample's latitude/longitude ordering only (no H or R read).

## 4. Exact human run command

```powershell
cd D:\claudecode\urban-history-transfer
conda run -n py311 python scripts/python1006_2.py
```
(Session-only proxy is not needed for this step; it uses no network.)

## 5. Expected raw archive path

`data/raw/urban_lst/2018-2023.zip` (git-ignored; currently **absent**, to be placed by the human).

Outputs: `results/python1006_2/python1006_2_results.md`, `_summary.json`, `_manifest.json`, `_DONE.txt` on success, `_FAILED.txt` on failure.

## 6. Known limitations (found during review; none fixed, per "use as supplied")

1. **Unit inference misses the degree sign.** `infer_units` lower-cases a `json.dumps` of the metadata; `json.dumps` escapes `°` as `\u00b0`, so a raster whose units are `°C` is **not** recognised as metadata Celsius. It then falls to the numeric fallback and returns `degC?` with evidence `numeric_diagnostic_only`. Tested directly: `degC`, `Celsius`, `K`, `kelvin` are recognised; `°C` is not. Consequence: the runner records a caution reason rather than failing, but the human should read the unit line in the results, not rely on the label. (A one-line fix would be `ensure_ascii=False`; not applied.)
2. **Unit checks can produce a false READY.** `decide()` only blocks when a unit is `None`; the numeric fallback (`K?`/`degC?`) is accepted with a note. Temperature units confirmed only by value range are weak evidence.
3. **The `>= 9 valid pixels` column is on the test polygons only** (12 distributed cities), not a prevalence estimate. The synthetic run showed 0 of 12 passing because the fake grid was coarse (0.05° ≈ 5 km), which is not a statement about the real 1 km archive.
4. **Runtime estimate is a naive linear extrapolation** (rasters × 10,915 cities × seconds-per-polygon from 12 polygons on one raster). `decide()` uses a hard-coded 10,915 and treats every raster-extension member as a raster, including any non-LST layers (e.g. QA bands) that share an extension. It is for architecture planning only.
5. **Only three members are inspected** (first, middle, last by detected date); a mid-archive format change would be missed. Date detection is filename-based; archives with differently named files will report no dates, and sampling then falls back to alphabetical order.
6. **Unit/scale semantics are not verified against documentation**: the runner cannot say whether the archive is daily mean LST, nor whether a scale factor is applied.
7. `safe_extract_members` flattens to the file name; two members with the same base name in different folders would overwrite each other in the temp directory.
8. `execution_status` is set to FAILED for a missing archive and `FAILED.txt` is written; the decision is `DATA_MISSING`.
9. The runner imports `ucdb_gate1_pilot` and reads UCDB attribute tables (about 20 s); this loads Gate 1 columns but not H-based analyses.

## 7. Git

Branch: `master`. Code commit `d163666b313c579504ffcb1956152c47982a6271`, pushed to `origin master` (`03bb5b1..d163666`, exit code 0). Details in §11.

---

## Project Structure and Code Map

```
urban-history-transfer/
├─ prompts/            promptXXXX-X.txt   permanent prompt archive (incl. 1006-2)
├─ reports/            reportXXXX-X.md    one report per execution
├─ results/            1005-1 … 1006-1 (frozen); python1006_2/ will be created by the human run
├─ figures/            1005-4, 1005-5, 1005-7, 1005-8, 1005-9
├─ data/raw|interim|processed   git-ignored (UCDB, MTUC, YCEO ZIP; urban_lst/ expected)
├─ docs/               governance, experiment, provenance, environment policies
├─ environment/        py311 lock files
├─ src/urban_history_transfer/environment.py   Python 3.11 guard
├─ scripts/
│   ├─ ucdb_gate1_pilot.py       UCDB loading, QC, sample, H/S/C construction (Gate 1)
│   ├─ mtuc_boundary_robustness.py   dynamic-boundary check (Gate 1B)
│   ├─ yceo_crosswalk.py / run_1005_7_pipeline.py   UCDB<->YCEO geometry crosswalk
│   ├─ gate2_support.py / run_1005_8_pipeline.py    cluster units, folds, twins utilities
│   ├─ gate2_data.py / gate2_models.py / run_1005_9_pipeline.py / gate2_decision_1005_9.py   Gate 2
│   ├─ download_thermal_response.py / verify_thermal_response.py   human-operated download + checks
│   ├─ aggregate_lst_zonal.py    raster header inspection + windowed polygon zonal mean   (updated now)
│   └─ python1006_2.py           archive verification runner                             (new)
└─ tests/              one test module per script family (129 tests)
```

Main entry points: `scripts/python1006_2.py` (this round, human-run), `scripts/run_1005_9_pipeline.py` (Gate 2), `scripts/ucdb_gate1_pilot.py` (Gate 1).
Reusable modules: `ucdb_gate1_pilot` (data + H), `gate2_support` / `gate2_data` / `gate2_models` (units, folds, learners, nulls, bootstrap), `aggregate_lst_zonal` (raster I/O).

Flow of this round: `data/raw/urban_lst/2018-2023.zip` → `archive_audit` (integrity, members, date coverage) → 3 representative members extracted to a temp dir → `inspect_raster` + `tiny_value_diagnostic` (128×128 subsample) → `infer_units` → 12 UCDB polygons reprojected to the raster CRS → `zonal_mean` timing → `decide` → `results/python1006_2/*`.

## Code Documentation Status

Well documented: `aggregate_lst_zonal.py` (numpy-style docstrings), `python1006_2.py` (module and function purpose), `gate2_models.py` / `gate2_support.py` (short docstrings and tests), the 1005-x pipelines (reports).
Opaque or under-documented: the unit-inference heuristics (§6.1–6.2) and the `decide()` thresholds (hard-coded 10,915 cities, 48 h cutoff, ≥ 9 valid pixels); layer discovery scoring in `discover_ucdb_polygon_layer` (all candidates score 0 here, so it falls back to alphabetical order); `ucdb_gate1_pilot.py` is a 900-line script mixing loading, QC, modelling and figures.
Technical debt for the next round: no real-archive test fixtures; `aggregate_lst_zonal.py` has no all-polygons driver or output schema yet; per-polygon window reads will repeat for every raster; the unit-inference false-positive path; the thin early-execution scripts (1005-1/2) have no docs beyond docstrings.

## Reuse Map for Next Round

* Reuse: `aggregate_lst_zonal.inspect_raster` / `zonal_mean`; `python1006_2.archive_audit`, `parse_date_from_name`, `choose_representative_members`, `discover_ucdb_polygon_layer`, `load_gate1_sample_ids`; `ucdb_gate1_pilot.load_main_table/run_qc/build_sample`; `gate2_data.assemble_units` for H/S/C; `gate2_models` for the unchanged evaluation pipeline.
* Safe extension points: add a driver that loops over rasters and writes one table per year; add an `ensure_ascii=False` fix and stricter unit rule in `infer_units`; extend `decide()` with an explicit expected-unit argument.
* Do not duplicate: the Gate 1 sample construction, the H aggregation, the tile folds and the sealing/decision logic already in `gate2_*`; do not re-implement polygon discovery.
* Likely hook for full aggregation: precompute a pixel→polygon index once per grid (the runner records whether representative grids are identical), then take means per raster by sums over that index instead of re-windowing every polygon for every raster; `zonal_mean` is the per-raster fallback and the correctness reference.

---

## 8. Close-out status

Prompt archived: YES
chatgpt staging directory cleaned: YES

(Verified after cleanup; see §10.)

## 9. Integrity statement

Package files applied byte-for-byte. Tests are synthetic and offline (the extra smoke test also ran offline). The real archive was neither present nor requested. Frozen 1005-x and 1006-1 results unchanged (hash check).

## 10. Close-out verification

* `prompts/prompt1006-2.txt` was byte-identical to the package prompt when copied (SHA-256 compared; 3,282 bytes) and is present after cleanup: **Prompt archived: YES**.
* `chatgpt\` was cleaned by deleting its single item, `chatgpt_1006_2_updated.zip` (SHA-256 `F50E4D2E…DC9ABE`, 13,348 bytes). After deletion the directory exists and contains 0 items. The temporary extraction folder was under `%TEMP%`, outside the repository, and was also removed. Nothing outside `chatgpt\` was deleted from the repository: **chatgpt staging directory cleaned: YES**.
* Note: `chatgpt/` had been untracked (never committed), so its removal appears in `git status` only as the folder disappearing from the untracked list.

## 11. Commit and push

* Branch: `master`
* Code commit: `d163666b313c579504ffcb1956152c47982a6271` ("1006-2: apply ChatGPT package for urban-LST archive verification runner (no data, synthetic tests only)"), 5 files: the prompt, the two scripts, the test module and this report.
* Push: **SUCCESS**, `03bb5b1..d163666  master -> master`, exit code 0 (session-only proxy `127.0.0.1:7890`; PowerShell shows git's progress line as an error record, which is cosmetic).
* This report originally said "filled after the push"; this section was added in a small follow-up commit so the report records the real hash. That follow-up commit's own hash is not recorded here (a file cannot contain its own commit hash); see `git log`.
