# Execution Report 1005-2

Source Prompt:
prompts/prompt1005-2.txt

Previous Execution:
1005-1

Report:
reports/report1005-2.md

Results:
results/1005-2/

Figures:
figures/1005-2/

## 1. Execution Metadata

- Execution ID: 1005-2
- Date: 2026-10-05
- Prompt file: prompts/prompt1005-2.txt
- Start time: 2026-10-05T04:30:00Z
- Completion time: 2026-10-05T04:59:10Z
- Status: COMPLETED (environment/version-control scope)
- Git commit/hash if available: None. A local Git repository was
  initialized during this execution, but no commit was created because no
  Git user identity (`user.name`/`user.email`) is configured, globally or
  locally, and this execution does not invent one. See Section 16/17 of
  this report.

## 2. Objective

Formally designate the user's pre-existing Anaconda environment `py311`
as the project's sole authorized Python environment; audit and
conservatively complete its scientific/GIS package foundation; verify the
stack actually functions via a smoke test; establish an environment
guard, CLI verification script, and exportable environment snapshot; and
check/establish local Git version control where safely possible. No
scientific analysis was in scope.

## 3. Authorized Scope

Exactly the scope defined in `prompts/prompt1005-2.txt`. All items listed
in Section 24 ("Hard Prohibitions") of the source prompt were out of
scope and were not performed (see Section 19 of this report).

## 4. Inputs

- `prompts/prompt1005-2.txt` (saved verbatim, then read back to confirm
  fidelity, before any other action).
- The pre-existing `py311` conda environment, created and populated by the
  user prior to this project (not created by this project).
- The prior execution's artifacts (`prompts/prompt1005-1.txt`,
  `reports/report1005-1.md`, `results/1005-1/`), inspected but not
  modified.
- Local system state: conda installation, Git availability, project
  directory contents.

No external research datasets, APIs, or network resources were accessed
other than the Python Package Index (for installing the four approved
missing packages) and the Anaconda `defaults` channel (for installing
Git into `base`).

## 5. Methods / Actions Performed

1. Confirmed `prompts/` already existed (from execution 1005-1) and saved
   the authorized prompt verbatim to `prompts/prompt1005-2.txt`, then read
   it back to confirm an exact match before proceeding.
2. Verified the official project environment (Section 4 of the source
   prompt):
   - `conda --version` → `conda 26.7.1` (later updated to `26.7.3` as an
     automatic dependency of the Git installation; see step 12).
   - `conda env list` → environments present: `base` (active, at
     `<USER_HOME>\miniconda3`), `hsi-pytorch`, and `py311` (at
     `<USER_HOME>\Miniconda3\envs\py311`). `py311` exists.
   - `conda run -n py311 python --version` → `Python 3.11.16`.
   - `conda run -n py311 python -c "import sys; print(sys.executable)"` →
     `<USER_HOME>\Miniconda3\envs\py311\python.exe`.
   - `conda run -n py311 python -c "import sys; print(sys.prefix)"` →
     `<USER_HOME>\Miniconda3\envs\py311`.
   - Conclusion: `py311` exists and runs Python 3.11.x. Execution
     continued per Section 4's instruction (no `BLOCKED_*` condition).
3. Created the required new directories: `results/1005-2/`,
   `figures/1005-2/`, `environment/`.
4. Created `scripts/audit_packages.py`, an engineering helper that
   imports each of the 13 approved foundation packages (by their import
   name) in the active interpreter and records installed/not-installed
   status and version, without installing anything.
5. Ran the BEFORE-install audit via
   `conda run -n py311 python scripts/audit_packages.py --out results/1005-2/package_audit_before.json --label before`.
   Result: 9 of 13 approved packages already present (`numpy`, `pandas`,
   `scipy`, `matplotlib`, `PyYAML`, `geopandas`, `shapely`, `pyproj`,
   `rasterio`); 4 missing (`pyarrow`, `pytest`, `xarray`, `rioxarray`).
6. Inspected how the existing packages had been installed
   (`conda list -n py311`): all project-relevant packages (including
   `geopandas`, `shapely`, `pyproj`, `rasterio`) show channel `pypi`,
   i.e. they were installed via pip, not conda-forge. Based on this,
   chose pip (invoked explicitly through `py311`) as the installation
   method for the missing packages, to remain consistent with the
   existing installation method and avoid mixing conda-forge binaries
   with an existing pip-installed GDAL-linked `rasterio`.
7. Installed the 4 missing approved packages with:
   `conda run -n py311 python -m pip install pyarrow pytest xarray rioxarray`.
   Full output logged to `results/1005-2/pip_install_log.txt`. Result:
   `Successfully installed iniconfig-2.3.0 pluggy-1.6.0 pyarrow-25.0.1
   pygments-2.21.0 pytest-9.1.1 rioxarray-0.19.0 xarray-2026.9.0`. No
   dependency conflicts; no already-installed approved package was
   upgraded or touched (pip reported them as "Requirement already
   satisfied").
8. Ran the AFTER-install audit via the same script with `--label after`
   → `results/1005-2/package_audit_after.json`. All 13 approved packages
   now report `installed: true` with real import-time versions.
9. Created `scripts/smoke_test_scientific_stack.py`, which exercises
   numpy, pandas, scipy, matplotlib, shapely, pyproj, geopandas, rasterio,
   xarray, rioxarray, and pyarrow using only synthetic/in-memory or
   local-temporary data (no network access, no external datasets). Ran it
   via `conda run -n py311 python scripts/smoke_test_scientific_stack.py --out results/1005-2/scientific_stack_smoke_test.json`.
   All 11 components reported `PASS`; overall status `PASS`. Any
   temporary files (a PNG from the matplotlib test, a GeoTIFF from the
   rasterio test, a Parquet file from the pyarrow test) were written to
   `tempfile.TemporaryDirectory()` locations and removed automatically
   when each test's `with` block exited. Nothing was written into
   `figures/1005-2/`.
10. Created `src/urban_history_transfer/environment.py`, providing
    `check_environment()` (non-raising) and `require_environment()`
    (raises `RuntimeError` on mismatch). The hard requirement is Python
    major==3, minor==11; `CONDA_DEFAULT_ENV` is recorded for diagnostics
    but is not required to be set (since `conda run` does not reliably
    set it in all invocation contexts — though it was in fact observed to
    be set to `py311` in this execution's own `conda run` invocations).
11. Created `scripts/verify_project_environment.py`, a CLI wrapper around
    `check_environment()` that exits 0 when the policy is satisfied and
    non-zero otherwise. Verified both directions empirically:
    - `conda run -n py311 python scripts/verify_project_environment.py`
      → prints `OK: running under Python 3.11 ...`, exit code 0.
    - running the same script under the system's `base`-environment
      Python (3.14) → prints an `ENVIRONMENT MISMATCH ...` message
      instructing `conda run -n py311 python ...`, exit code 1.
12. Checked Git availability: `git --version` via system PATH failed
    (`git: command not found`), consistent with the 1005-1 finding (which
    is left unmodified). Searched for Git via conda:
    `conda search git` on the `defaults` channel listed many versions,
    up to `2.55.0`. Per Section 16 of the source prompt, this was judged
    installable safely (conda-managed, no admin privileges, does not
    touch `py311`'s Python version). To keep `py311` scoped strictly to
    project Python packages (per the new `docs/ENVIRONMENT_POLICY.md`),
    Git was installed into the conda `base` environment, not `py311`,
    and not into a new environment, via `conda install -n base git -y`.
    Full output logged to `results/1005-2/git_install_log.txt`.
    **Disclosed side effect:** resolving the `git` package also triggered
    conda's dependency resolver to update `conda` itself
    (`26.7.1` → `26.7.3`) and `ca-certificates`/`openssl` within `base`.
    `py311` was not modified by this step.
13. Verified Git works: `git --version` → `git version 2.55.0.windows.1`.
    Checked identity: `git config --global user.name` and
    `git config --global user.email` both returned empty (unset); no
    local repository existed yet, so there was no local identity either.
14. Initialized a local Git repository at the project root with `git init`
    (default branch `master`; no remote configured, no credentials
    requested, no global Git configuration changed).
15. Inspected `.gitignore` (unchanged from 1005-1): confirmed it does not
    broadly ignore `prompts/`, `reports/`, `docs/`, `configs/`, `src/`,
    `tests/`, or the newly added `environment/`; confirmed it does ignore
    Python caches, build artifacts, and raw/interim/processed data
    contents. No changes to `.gitignore` were needed.
16. Staged all tracked-worthy files with `git add -A` and reviewed the
    resulting `git status` (see Section 6/19 below) to confirm nothing
    sensitive, no credentials, and no large research datasets were about
    to be committed.
17. Attempted to create a commit. Blocked: no `user.name`/`user.email` is
    configured (globally or locally). Per the source prompt's explicit
    instruction, did **not** invent an identity and did **not** modify
    global Git configuration. Recorded `GIT_COMMIT_BLOCKED_IDENTITY` (see
    Section 16 of `prompts/prompt1005-2.txt`) and continued with the
    remaining work. The repository remains initialized with all project
    files staged but uncommitted, awaiting the user to configure a Git
    identity (locally, in this repo, is sufficient) before a first commit
    can be made in a future execution or manually.
18. Created `docs/ENVIRONMENT_POLICY.md` as the authoritative environment
    policy document, per Section 6 of the source prompt.
19. Updated `scripts/check_environment.py` (Section 15 of the source
    prompt) to additionally record `python_executable`, `sys_prefix`, and
    `conda_default_env`, and to audit the full approved package list
    (previously a shorter illustrative list from 1005-1). The historical
    `results/1005-1/environment.json` was **not** regenerated or altered;
    the script was run fresh via
    `conda run -n py311 python scripts/check_environment.py --execution-id 1005-2 --out results/1005-2/environment.json`,
    producing a new, separate file. Confirmed by SHA-256 hash comparison
    that `results/1005-1/environment.json` is byte-identical to its state
    before this step.
20. Updated `pyproject.toml`: `requires-python` changed from `>=3.10` to
    `>=3.11,<3.12` (matching the validated policy and avoiding any claim
    of support for untested Python versions), and added a `dependencies`
    list reflecting the 12 approved non-test foundation packages at their
    currently-installed versions as lower bounds, plus an
    `[project.optional-dependencies] test = ["pytest>=9.1.1"]` group. No
    ML/DL dependencies were added.
21. Updated `README.md`: documented `py311` as the official Python
    environment, the `conda run -n py311 ...` execution pattern, that it
    was established in execution 1005-2, updated the execution-status
    table, repository-structure listing, and reproducibility
    cross-references. The core hypothesis status line was left unchanged
    (`UNTESTED`), and "No real research dataset has yet been analyzed" is
    stated explicitly.
22. Created `tests/test_environment.py` (5 new tests for the environment
    guard) without modifying or deleting `tests/test_infrastructure.py`
    from 1005-1.
23. Ran the full test suite via `conda run -n py311 python -m pytest -v`:
    16 passed, 0 failed (11 pre-existing infrastructure tests + 5 new
    environment-guard tests). No compatibility changes were needed to run
    the pre-existing `unittest.TestCase`-based tests under pytest — they
    were collected and run as-is.
24. Created `environment/py311-conda-explicit.txt`
    (`conda list -n py311 --explicit`, conda-managed packages only — this
    environment's scientific/GIS stack is primarily pip-installed, so
    this file alone does not capture it; documented as such in
    `docs/ENVIRONMENT_POLICY.md`), `environment/py311-packages.txt`
    (`conda list -n py311`, full human-readable inventory including pip
    packages), and `environment/py311-environment.yml`
    (`conda env export -n py311`, with the machine-specific `prefix:`
    line removed before saving, per the source prompt's explicit
    instruction; the original stderr warning emitted by `conda env
    export` about pip-installed packages not being reliably lockable was
    preserved separately in
    `environment/py311-environment-export-warnings.txt` rather than
    silently discarded or left mixed into the YAML).
25. Updated `reports/PROJECT_MANIFEST.md`: added `1005-2` to Completed
    Executions, added an "Official Python Environment" section recording
    `OFFICIAL_PYTHON_ENVIRONMENT: py311`, `PYTHON_POLICY: 3.11.x`,
    `ENVIRONMENT_STATUS: VALIDATED`; left the core hypothesis and all
    `PENDING_SCIENTIFIC_DECISION` items from 1005-1 unchanged; kept
    project status `AWAITING_SCIENTIFIC_REVIEW`.
26. Wrote `results/1005-2/run_metadata.json` and
    `results/1005-2/test_summary.json` with actual values, and this
    report, `reports/report1005-2.md`.

No scientific analysis (correlation, regression, significance testing,
clustering, ML/DL training, optimization, historical analogue analysis,
cross-city transfer analysis) was performed at any point. No pilot cities
or scientific variable definitions (S, H, R, D_S, D_H, D_R) were selected
or finalized.

## 6. Outputs

| Output ID | Path | Type | Description |
|-----------|------|------|--------------|
| O1 | docs/ENVIRONMENT_POLICY.md | doc | Authoritative Python environment policy |
| O2 | src/urban_history_transfer/environment.py | code | Environment guard (check_environment/require_environment) |
| O3 | scripts/verify_project_environment.py | script | CLI environment-policy check (exit code semantics) |
| O4 | scripts/audit_packages.py | script | Package audit helper (before/after) |
| O5 | scripts/smoke_test_scientific_stack.py | script | Synthetic-data smoke test of the scientific/GIS stack |
| O6 | scripts/check_environment.py | script | Updated environment-info collector (new fields; 1005-1 output untouched) |
| O7 | tests/test_environment.py | test | New tests for the environment guard |
| O8 | results/1005-2/run_metadata.json | json | Machine-readable execution metadata |
| O9 | results/1005-2/environment.json | json | Environment snapshot for this execution (py311) |
| O10 | results/1005-2/package_audit_before.json | json | Package audit before installation |
| O11 | results/1005-2/package_audit_after.json | json | Package audit after installation |
| O12 | results/1005-2/scientific_stack_smoke_test.json | json | Smoke-test results per component |
| O13 | results/1005-2/test_summary.json | json | pytest run summary |
| O14 | results/1005-2/pip_install_log.txt | log | Full pip install output |
| O15 | results/1005-2/git_install_log.txt | log | Full conda install output for Git |
| O16 | environment/py311-conda-explicit.txt | snapshot | conda explicit export |
| O17 | environment/py311-packages.txt | snapshot | Full human-readable package inventory |
| O18 | environment/py311-environment.yml | snapshot | conda env export (prefix line removed) |
| O19 | environment/py311-environment-export-warnings.txt | log | stderr warnings from the YAML export, preserved |
| O20 | reports/report1005-2.md | report | This report |
| O21 | reports/PROJECT_MANIFEST.md | doc | Updated project manifest |
| O22 | pyproject.toml | config | Updated Python/dependency policy |
| O23 | README.md | doc | Updated with official environment documentation |
| O24 | prompts/prompt1005-2.txt | prompt | Verbatim saved source prompt |
| O25 | (local Git repository at project root) | vcs | Initialized, all files staged, no commit (identity not configured) |

## 7. Quantitative Results

No scientific quantitative results were produced in this execution.

## 8. Figures

None.

`figures/1005-2/` was intentionally left empty. The matplotlib smoke test
wrote its minimal plot to a temporary file outside the project directory,
which was removed after verification; no figure was placed in
`figures/1005-2/`.

## 9. Validation / Tests

- Tests run: 16 (via `conda run -n py311 python -m pytest -v`)
- Passed: 16
- Failed: 0
- Warnings: 2 non-test warnings, both disclosed in
  `results/1005-2/run_metadata.json`: (1) installing Git into `base`
  triggered an automatic conda/ca-certificates/openssl update in `base`
  as a dependency-resolution side effect; (2) no Git identity is
  configured, so no commit was created. No pytest-level warnings were
  emitted.

Additionally, the scientific/GIS smoke test (not a pytest test, but a
separate validation step required by the source prompt) reported 11/11
components `PASS` with `overall_status: PASS`.

## 10. Data Quality

No real research dataset was analyzed in this execution.

## 11. Deviations from Authorized Plan

1. **Installation method choice (engineering decision, documented):** The
   source prompt allowed either conda-compatible package management or
   pip (invoked explicitly through `py311`). Pip was chosen for the 4
   missing packages, for consistency with how the existing 9 approved
   packages were already installed in `py311` (all via pip/pypi, not
   conda-forge).
2. **Git installed into `base`, not `py311` (engineering decision,
   explicitly authorized by Section 16 of the source prompt, documented):**
   The source prompt permits installing Git into "the user's existing
   conda tooling/environment" if safe. To avoid mixing a non-Python
   version-control tool into the scientific environment governed by
   `docs/ENVIRONMENT_POLICY.md` (which restricts `py311` to project
   Python packages), Git was installed into `base` instead. This did not
   require administrator privileges and did not alter `py311`'s Python
   version.
3. **Side effect of Git installation (disclosed, not an authorized
   change in its own right):** Installing `git` into `base` caused
   conda's dependency resolver to also update `conda` itself and
   `ca-certificates`/`openssl` within `base`. This was not a broad,
   intentional "upgrade everything" action — it was conda's own
   dependency resolution for the single `git install` command — but is
   disclosed here in full per the integrity requirements of this
   execution. `py311` was not affected.
4. **No commit created (environmental limitation, not a scope deviation):**
   Section 17 of the source prompt authorizes a commit only if Git
   identity is safely available. It is not. No identity was invented and
   no global configuration was changed, per explicit instruction. This is
   reported as `GIT_COMMIT_BLOCKED_IDENTITY`, not treated as an execution
   failure.

No hard-prohibited action (Section 24 of the source prompt) was performed.

## 12. Failures / Unexpected Results

None of the planned, technically-feasible steps failed. The only unmet
item is the Git commit, which is an environmental/configuration
limitation (missing identity), not a failure of executed logic, and is
documented in Sections 11, 16, and 19 of this report.

## 13. Scientific Decisions Made

None. No scientific definitions, variables, thresholds, models, pilot
cities, or hypotheses were set, chosen, or altered. All scientific
decisions listed in `reports/PROJECT_MANIFEST.md` remain
`PENDING_SCIENTIFIC_DECISION`, unchanged from execution 1005-1.

## 14. Engineering Decisions Made

1. Used pip (via `conda run -n py311 python -m pip install ...`) rather
   than conda-forge for the 4 missing packages, for consistency with the
   existing pip-installed stack and to minimize risk of binary conflicts
   with the existing pip-installed `rasterio`/GDAL.
2. Installed Git into conda `base` rather than `py311`, to keep `py311`
   scoped strictly to project Python dependencies, per the new
   `docs/ENVIRONMENT_POLICY.md`.
3. Did not pin exact versions in `pyproject.toml`; used `>=<installed
   version>` lower bounds reflecting what was actually audited/installed
   and tested in this execution, rather than fabricating or guessing
   compatible ranges.
4. Preserved the stderr output of `conda env export` (which warns that
   pip-installed packages cannot be reliably locked by conda) in a
   separate log file rather than letting it corrupt the YAML file or
   silently discarding it.
5. Extended `scripts/check_environment.py`'s tracked package list from
   the illustrative 1005-1 set to the full 13-package approved foundation
   list, and added `python_executable`/`sys_prefix`/`conda_default_env`
   fields, while leaving the script's existing CLI interface and the
   1005-1 output file untouched.
6. Added a `[project.optional-dependencies] test` group in
   `pyproject.toml` for `pytest`, rather than listing it as a core
   runtime dependency, since it is a test-only tool.

## 15. Decisions NOT Made

- No pilot cities were selected.
- No spatial or temporal resolution was chosen.
- No definitions were finalized for S, H, R, D_S, D_H, or D_R.
- No statistical model, falsification test, or go/no-go criterion was
  chosen.
- No decision was made to resolve the Git identity gap on the user's
  behalf (no identity was invented).
- No decision was made about whether/when the user should configure a
  local or global Git identity — that remains the user's choice.

All scientific items above remain `PENDING_SCIENTIFIC_DECISION` in
`reports/PROJECT_MANIFEST.md`.

## 16. Pending Scientific Review / Pending Decisions

A human reviewer should:

1. Confirm that designating `py311` as the sole project Python
   environment, and the specific package list installed into it, is
   acceptable.
2. Confirm that installing Git into conda `base` (rather than `py311` or
   elsewhere) is an acceptable approach, given its side effect of
   updating `conda`/`ca-certificates`/`openssl` in `base`.
3. Decide whether to configure a Git identity (at minimum locally, in
   this repository) so that a first commit can be made in a future
   execution. This project did not and will not invent one.
4. Continue resolving the scientific `PENDING_SCIENTIFIC_DECISION` items
   listed in `reports/PROJECT_MANIFEST.md` (unchanged from 1005-1).
5. Author and authorize `prompt1005-3` only after the above review. This
   execution did not create or execute any subsequent prompt.

## 17. Reproduction Commands

From the project root (`<PROJECT_ROOT>`):

```powershell
# Verify py311 and its Python version
conda run -n py311 python --version
conda run -n py311 python -c "import sys; print(sys.executable)"

# Audit packages (before/after installation)
conda run -n py311 python scripts/audit_packages.py --out results/1005-2/package_audit_before.json --label before
conda run -n py311 python -m pip install pyarrow pytest xarray rioxarray
conda run -n py311 python scripts/audit_packages.py --out results/1005-2/package_audit_after.json --label after

# Run the scientific/GIS smoke test
conda run -n py311 python scripts/smoke_test_scientific_stack.py --out results/1005-2/scientific_stack_smoke_test.json

# Verify the environment guard
conda run -n py311 python scripts/verify_project_environment.py

# Run the test suite
conda run -n py311 python -m pytest -v

# Regenerate the environment snapshot
conda run -n py311 python scripts/check_environment.py --execution-id 1005-2 --out results/1005-2/environment.json
conda list -n py311 --explicit > environment/py311-conda-explicit.txt
conda list -n py311 > environment/py311-packages.txt
conda env export -n py311 > environment/py311-environment.yml   # then remove the trailing `prefix:` line
```

No random seed was used anywhere in this execution (no stochastic process
was involved in environment/version-control work).

## 18. Environment

See `results/1005-2/environment.json` for the full machine-readable
snapshot of this execution. Summary:

- Official conda environment: `py311`
- Python: 3.11.16 (Anaconda distribution)
- Python executable: `<USER_HOME>\Miniconda3\envs\py311\python.exe`
- sys.prefix: `<USER_HOME>\Miniconda3\envs\py311`
- CONDA_DEFAULT_ENV (as observed under `conda run -n py311 ...`): `py311`
- Platform: Windows-10-10.0.19045-SP0 (Windows 10 Pro for Workstations)
- Git: available, version `2.55.0.windows.1`, installed into conda `base`
  during this execution (not previously available via system PATH)
- Approved package versions (post-install): numpy 2.4.6, pandas 3.0.6,
  scipy 1.17.1, matplotlib 3.11.2, pyarrow 25.0.1, PyYAML 6.0.3, pytest
  9.1.1, geopandas 1.2.0, shapely 2.1.2, pyproj 3.7.2, rasterio 1.4.4,
  xarray 2026.9.0, rioxarray 0.19.0

Note: `py311` is a pre-existing, general-purpose environment that also
contains unrelated packages (e.g. PyTorch/Lightning/TorchGeo/Kornia
tooling), visible in `environment/py311-packages.txt` and
`environment/py311-environment.yml`. These were present before this
execution, are not used by this project, and were not installed, removed,
or modified by this execution.

## 19. Integrity Statement

**Explicit answers requested by Section 27 of the source prompt:**

1. Was py311 found? **Yes.**
2. Exact Python version in py311? **3.11.16**
   (`3.11.16 | packaged by Anaconda, Inc. | (main, Aug 27 2026, 14:36:16)
   [MSC v.1942 64 bit (AMD64)]`).
3. Exact Python executable? **`<USER_HOME>\Miniconda3\envs\py311\python.exe`**
4. Approved packages already installed (before this execution): numpy,
   pandas, scipy, matplotlib, PyYAML, geopandas, shapely, pyproj,
   rasterio (9 of 13).
5. Packages installed during 1005-2: pyarrow, pytest, xarray, rioxarray
   (4 of 13), all via `conda run -n py311 python -m pip install`.
6. Package installations that failed: **None.**
7. Did every scientific/GIS smoke-test component pass? **Yes — all 11
   components (numpy, pandas, scipy, matplotlib, shapely, pyproj,
   geopandas, rasterio, xarray, rioxarray, pyarrow) reported PASS.**
8. Did pytest pass under py311? **Yes — 16/16 passed, 0 failed.**
9. Was Git available? **Not initially (not on system PATH). Installed
   into conda `base` during this execution; available afterward
   (version 2.55.0.windows.1).**
10. Was a repository initialized? **Yes**, via `git init` at the project
    root, immediately after Git became available.
11. Was a commit created? **No.**
12. If not, exactly why not? **No Git user identity
    (`user.name`/`user.email`) is configured, globally or locally on this
    machine. Per explicit governance in the source prompt, this execution
    does not invent an identity and does not modify global Git
    configuration. This is recorded as `GIT_COMMIT_BLOCKED_IDENTITY`.**
13. Were any real scientific data downloaded? **No.**
14. Was any scientific hypothesis tested? **No.**
15. Were any scientific definitions finalized? **No** (S, H, R, D_S, D_H,
    D_R all remain undefined/`PENDING_SCIENTIFIC_DECISION`).

**Explicit disclosures requested by Section 28 of the source prompt:**

- Was any package installed outside `py311`? **Only Git, which is
  explicitly not a project Python package; it was installed into conda
  `base`, as documented and disclosed above and authorized by Section 16
  of the source prompt as a safe, non-admin, non-Python-version-altering
  action. No project Python package was installed outside `py311`.**
- Was `base` modified for scientific Python dependencies? **No.** `base`
  was modified only to add the `git` conda package (and its own
  dependency-resolution side effects on `conda`/`ca-certificates`/
  `openssl`), not any scientific/GIS Python package.
- Was another conda environment created? **No.**
- Was `py311`'s Python version changed? **No** — it remains 3.11.16
  throughout.
- Were previous execution artifacts overwritten? **No.** `prompts/prompt1005-1.txt`,
  `reports/report1005-1.md`, and all files under `results/1005-1/` were
  left untouched (verified for `results/1005-1/environment.json`
  specifically via SHA-256 hash comparison before/after this execution).
- Were real research data used? **No.**
- Was scientific analysis performed? **No.**
- Was future prompt work started? **No.** `prompt1005-3` was not created
  or executed.
