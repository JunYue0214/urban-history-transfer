# Urban Development History and Environmental Response Transferability

## Project status

**AWAITING_SCIENTIFIC_REVIEW** (as of execution `1005-2`)

**Executions 1005-1 and 1005-2 are infrastructure/environment only. No
real scientific analysis has been performed.** Scientific definitions
including S, H, R, D_S, D_H, and D_R are intentionally **not finalized**.
Nothing in this repository should be read as a scientific result. See
`reports/report1005-1.md` and `reports/report1005-2.md` for a full account
of what each execution did and did not do.

## Official Python environment

The project's sole authorized Python execution environment is the user's
pre-existing Anaconda / conda environment:

```
py311
```

Required Python version: **3.11.x** (verified as Python 3.11.16).

Recommended explicit execution pattern, to avoid accidentally running
project code under the wrong interpreter:

```
conda run -n py311 python ...
conda run -n py311 python -m pytest ...
```

This environment was formally designated, audited, and documented during
execution 1005-2 (see [`docs/ENVIRONMENT_POLICY.md`](docs/ENVIRONMENT_POLICY.md)
and `reports/report1005-2.md`). `py311` is a pre-existing environment and
was **not** created by this project; no new conda environment was created,
and `base` was not used for project scientific Python dependencies.

No real research dataset has yet been analyzed.

## Scientific motivation

Two urban systems may occupy similar present states but exhibit different
environmental responses because they arrived at those states through
different developmental histories. A possible future conceptual
relationship under investigation is:

```
D_R = f(D_S, D_H)
```

where `D_S` is present-state distance, `D_H` is developmental-history
distance, and `D_R` is environmental-response distance between two urban
systems.

**Hypothesis status: UNTESTED.** This hypothesis has not been tested, and
will not be tested until explicitly authorized by a future prompt.

Potential future topics (contextual only, not yet authorized) include
large-scale remote sensing, GIS, urban environmental change, urban heat,
vegetation, developmental trajectories, cross-city transferability,
historical analogue hindcasting, sensing/evidence allocation, optimization,
crowdsensing, and wireless sensing.

## Current execution status

| Execution | Status | Scope |
|-----------|--------|-------|
| 1005-1 | Completed (infrastructure only) | Repository structure, provenance, governance, experiment protocol, minimal package, environment check, tests, reporting |
| 1005-2 | Completed (environment/version-control only) | Verified/designated `py311` as the official Python environment, audited and installed missing foundation packages, GIS/scientific stack smoke test, environment guard, environment snapshot exports, Git availability check and local repository initialization |

No scientific analysis execution has occurred yet.

## Repository structure

```
prompts/                 Authorized prompt files (immutable once executed)
reports/                 Execution reports, project manifest, report template
results/<execution_id>/  Machine-readable outputs per execution
figures/<execution_id>/  Figures per execution
configs/                 Configuration files
data/raw/                Raw data (none present yet)
data/interim/            Intermediate data (none present yet)
data/processed/          Processed data (none present yet)
docs/                    Governance and protocol documents
environment/             Environment snapshot exports for py311 (conda explicit, package list, environment.yml)
src/urban_history_transfer/  Minimal Python package (no analysis logic yet)
scripts/                 Utility scripts (environment checker, environment guard CLI, smoke test)
tests/                   Automated tests
```

## Execution model

This project follows a strict human-in-the-loop workflow:

```
Scientific design
  -> authorized prompt (prompts/promptXXXX-X.txt)
  -> Claude Code execution
  -> persisted results (results/XXXX-X/, figures/XXXX-X/)
  -> standardized report (reports/reportXXXX-X.md)
  -> human scientific review
  -> next authorized prompt
```

Claude Code executes only the single prompt it has been given, then stops
and awaits human review. It does not autonomously create or execute
subsequent prompts, and does not make scientific decisions on its own
authority.

## Provenance model

Every execution has a unique ID (`XXXX-X`) shared by its prompt, report,
results directory, and figures directory. Executed prompts are immutable;
corrections are made under a new execution ID that references the one it
corrects. Full rules are in
[`docs/PROVENANCE_PROTOCOL.md`](docs/PROVENANCE_PROTOCOL.md).

## Reproducibility approach

Each execution records (where applicable) random seeds, parameters,
inputs/outputs, and reproduction commands in its report and in
`results/<execution_id>/run_metadata.json`. An environment snapshot
(`scripts/check_environment.py` -> `results/<execution_id>/environment.json`)
is captured per execution. Details are in
[`docs/EXPERIMENT_PROTOCOL.md`](docs/EXPERIMENT_PROTOCOL.md) and, for the
official Python environment specifically,
[`docs/ENVIRONMENT_POLICY.md`](docs/ENVIRONMENT_POLICY.md).

## Scientific governance

Human-vs-Claude-Code responsibilities, and a list of autonomous scientific
actions that are always prohibited (e.g. changing the hypothesis, cherry-
picking significant results, suppressing null results), are defined in
[`docs/SCIENTIFIC_GOVERNANCE.md`](docs/SCIENTIFIC_GOVERNANCE.md).

## Experiment protocol

Minimum procedural requirements for any execution (execution IDs, scope
enforcement, reproducibility recording, reporting requirements, and the
distinction between exploratory and confirmatory analysis) are defined in
[`docs/EXPERIMENT_PROTOCOL.md`](docs/EXPERIMENT_PROTOCOL.md).

## Pending scientific decisions

A substantial list of scientific decisions (pilot cities, spatial/temporal
resolution, variable definitions for S/H/R/D_S/D_H/D_R, statistical model,
falsification tests, go/no-go criteria, etc.) remains unresolved and is
tracked in [`reports/PROJECT_MANIFEST.md`](reports/PROJECT_MANIFEST.md),
each marked `PENDING_SCIENTIFIC_DECISION`.

## Integrity note

No results in this repository are fabricated. Where no scientific result
exists, reports say so explicitly rather than inventing one.
