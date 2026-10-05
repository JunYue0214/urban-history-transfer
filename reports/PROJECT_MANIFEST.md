# Project Manifest

## Project

Urban Development History and Environmental Response Transferability

## Current Execution

1005-2

## Project Status

AWAITING_SCIENTIFIC_REVIEW

## Core Scientific Hypothesis

Two urban systems may occupy similar present states but exhibit different
environmental responses because they arrived at those states through
different developmental histories.

A possible future conceptual relationship is:

D_R = f(D_S, D_H)

where:

- D_S = present-state distance
- D_H = developmental-history distance
- D_R = environmental-response distance

Status:

UNTESTED

## Completed Executions

- 1005-1
- 1005-2

## Official Python Environment

OFFICIAL_PYTHON_ENVIRONMENT:
py311

PYTHON_POLICY:
3.11.x

ENVIRONMENT_STATUS:
VALIDATED

Established and validated during execution 1005-2: `py311` exists, runs
Python 3.11.16, the approved scientific/GIS package foundation is fully
installed, and a smoke test of that stack passed for all 11 tested
components. See [`docs/ENVIRONMENT_POLICY.md`](../docs/ENVIRONMENT_POLICY.md)
and `reports/report1005-2.md`.

## Current Data Status

NO_REAL_RESEARCH_DATA

## Current Scientific Analysis Status

NO_SCIENTIFIC_ANALYSIS

## Current Authorized Scope

Infrastructure, environment establishment, and reproducibility only. No
scientific analysis has been authorized beyond this scope as of execution
1005-2.

## Pending Scientific Decisions

- pilot city selection — PENDING_SCIENTIFIC_DECISION
- number of pilot cities — PENDING_SCIENTIFIC_DECISION
- spatial analysis unit — PENDING_SCIENTIFIC_DECISION
- spatial resolution — PENDING_SCIENTIFIC_DECISION
- temporal epochs — PENDING_SCIENTIFIC_DECISION
- study period — PENDING_SCIENTIFIC_DECISION
- urban boundary definition — PENDING_SCIENTIFIC_DECISION
- rural/background definition — PENDING_SCIENTIFIC_DECISION
- primary environmental outcome — PENDING_SCIENTIFIC_DECISION
- present-state representation S — PENDING_SCIENTIFIC_DECISION
- historical representation H — PENDING_SCIENTIFIC_DECISION
- response representation R — PENDING_SCIENTIFIC_DECISION
- D_S definition — PENDING_SCIENTIFIC_DECISION
- D_H definition — PENDING_SCIENTIFIC_DECISION
- D_R definition — PENDING_SCIENTIFIC_DECISION
- vegetation metric — PENDING_SCIENTIFIC_DECISION
- built-up metric — PENDING_SCIENTIFIC_DECISION
- climate controls — PENDING_SCIENTIFIC_DECISION
- Northern/Southern Hemisphere seasonality treatment — PENDING_SCIENTIFIC_DECISION
- statistical model — PENDING_SCIENTIFIC_DECISION
- falsification tests — PENDING_SCIENTIFIC_DECISION
- historical window lengths — PENDING_SCIENTIFIC_DECISION
- go/no-go criteria — PENDING_SCIENTIFIC_DECISION
- external validation strategy — PENDING_SCIENTIFIC_DECISION
- scaling strategy — PENDING_SCIENTIFIC_DECISION

## Notes

Execution 1005-1 was infrastructure-only. It established repository
structure, provenance/governance/experiment protocols, a minimal Python
package, environment checking, automated tests, and standardized reporting.
No real research data was analyzed and the core scientific hypothesis
remains UNTESTED. See reports/report1005-1.md for full details.

Execution 1005-2 was an environment/version-control execution. It verified
and formally designated the pre-existing Anaconda environment `py311`
(Python 3.11.16) as the project's sole authorized Python environment,
audited its packages, installed the missing approved foundation packages
(`pyarrow`, `pytest`, `xarray`, `rioxarray`), ran a smoke test of the full
scientific/GIS stack (all 11 components PASS), ran the project test suite
under `py311` via pytest (16/16 passed), produced environment snapshot
exports, installed Git into the conda `base` environment (not `py311`)
and initialized a local Git repository. No commit was created because no
Git user identity (`user.name`/`user.email`) was configured and none was
invented, per governance. No real research data was analyzed and the core
scientific hypothesis remains UNTESTED. See reports/report1005-2.md for
full details.
