# Official Python Environment

Conda environment:

py311

Required Python major/minor:

3.11

This environment was verified during execution 1005-2 to exist and to run
Python 3.11.16 (`<USER_HOME>\Miniconda3\envs\py311\python.exe`). It is
the user's pre-existing Anaconda/conda environment and was NOT created by
this project. No new conda environment was created, and `base` was not
used for project scientific Python dependencies.

# Execution Rule

Project Python commands should be executed explicitly through:

```
conda run -n py311 ...
```

or through an independently verified active `py311` environment (e.g.
verified via `scripts/verify_project_environment.py`).

Do not rely on `conda activate py311` having persisted across independent
shell invocations — each invocation's interpreter identity should be
confirmed explicitly, since this project's execution model (e.g. tool
calls, CI-style runs) may spawn independent, non-interactive shells.

# Wrong Environment Protection

Scientific/project computation must not silently continue when the
interpreter is not the authorized project environment.

`src/urban_history_transfer/environment.py` provides `check_environment()`
and `require_environment()` to make this check explicit and auditable.
`scripts/verify_project_environment.py` provides a CLI entry point that
exits non-zero when the Python major/minor requirement (3.11) is violated.

# Package Installation

Project Python packages must be installed into `py311`.

Do not install project dependencies into `base` merely for convenience.
Do not create a new conda environment for this project. Do not use an
unrelated interpreter.

The approved foundation package list, audited and installed during
execution 1005-2, is:

```
numpy
pandas
scipy
matplotlib
pyarrow
PyYAML
pytest
geopandas
shapely
pyproj
rasterio
xarray
rioxarray
```

Packages outside this list should not be installed for project scientific
work without being recorded as an explicit, documented engineering or
scientific decision in the relevant execution's report. ML/DL frameworks
(e.g. TensorFlow, PyTorch, JAX) are explicitly out of scope unless a
future authorized prompt says otherwise.

Note: `py311` is a pre-existing general-purpose environment that already
contained other packages (including PyTorch-related tooling) unrelated to
this project before execution 1005-2 began. This project does not depend
on those packages and does not manage, remove, or upgrade them.

# Environment Changes

Material dependency changes must be documented in the corresponding
execution report (which packages were added, by what command, and why).

# Reproducibility

Environment specifications must be exportable and versioned. These are
maintained under `environment/`:

- `environment/py311-conda-explicit.txt` — conda explicit package export
  (conda-managed packages only; this environment's GIS/scientific stack
  is primarily pip-installed, so this file alone does not capture it).
- `environment/py311-packages.txt` — full human-readable package/version
  inventory (`conda list -n py311`), including pip-installed packages.
- `environment/py311-environment.yml` — `conda env export -n py311`
  output, with the machine-specific `prefix:` line removed before being
  version-controlled.

These exports reflect the actual environment at the time of export; they
are not manually constructed or fabricated.

# Non-Python Tooling (Git)

Git is a version-control tool, not a project Python package. It was
installed, where safe to do so, into the conda `base` environment (not
`py311`, and not a newly created environment) during execution 1005-2, to
keep `py311` scoped strictly to project Python dependencies. See the
execution 1005-2 report for details and any limitations encountered.
