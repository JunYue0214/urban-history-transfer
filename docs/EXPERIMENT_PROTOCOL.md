# Experiment Protocol

This document specifies the minimum procedural requirements for any
scientific or engineering execution in this project. It applies to all
executions from 1005-1 onward.

## Execution identity

- Every execution has a unique execution ID of the form `XXXX-X`.
- Every execution traces back to a single source prompt file
  (`prompts/promptXXXX-X.txt`), recorded in the report and, where
  practical, in machine-readable outputs as `source_prompt`.
- Every execution has an explicit, stated objective, distinct from the
  project's long-term scientific hypothesis.

## Authorized-scope enforcement

- An execution may perform only the actions explicitly authorized by its
  source prompt.
- Any hard prohibitions stated in the source prompt must be treated as
  binding.
- Any deviation from the authorized plan, however minor, must be recorded
  in the execution's report under "Deviations from Authorized Plan".
- No execution may autonomously trigger or create a subsequent prompt or
  execution. Progression to the next prompt requires a human decision.

## Reproducibility recording

Where a step involves randomness, parameters, or external inputs, the
execution must record:

- random seed(s) used
- parameters used
- inputs consumed (paths, versions, hashes where available)
- outputs produced (paths, with a short description)
- the exact commands needed to reproduce the step

All of the above should be persisted to disk (JSON/config/report), never
left only in conversation or terminal history.

## Timestamps and version tracking

- Timestamps should use ISO 8601 format where practical
  (e.g. `2026-10-05T00:00:00Z` or with local offset).
- Git commit hash should be recorded when a Git repository is available.
  If Git is unavailable or the repository has not yet been initialized,
  this must be explicitly noted rather than fabricated.

## Reporting requirements

Every execution's report must include:

- warnings and errors encountered, even if execution still completed
- failed runs, if any, with enough detail to understand what failed
- both significant and non-significant findings, with no selective
  omission of unfavorable results
- a clear statement of whether real scientific data was used, and whether
  the core hypothesis was tested

## Exploratory vs. confirmatory analysis

- Any analysis must be explicitly labeled as either **exploratory** or
  **confirmatory** before being reported.
- Exploratory analyses (including any post-hoc exploration discovered
  while working) must be labeled as such and must not be presented as
  confirmatory evidence for or against the core hypothesis.
- Exclusion rules for observations/data (if any apply in a given
  execution) must be predefined before looking at results, and that
  predefinition must be recorded. Exclusions decided after seeing results
  are not permitted without explicit authorization and disclosure.

## Statistical reporting (for future statistical analyses)

When a future execution performs a statistical analysis, it must report at
minimum:

- the analysis/test used
- sample size
- effect estimate
- uncertainty (e.g. confidence interval or standard error) where applicable
- p-value where applicable
- relevant parameters/settings of the analysis

## No automatic progression

Completing an execution's authorized objective does not authorize starting
the next prompt. Each execution ends with an explicit stop and awaits human
scientific review before any subsequent prompt is created or executed.
