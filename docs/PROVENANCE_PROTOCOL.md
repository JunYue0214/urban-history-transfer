# Provenance Protocol

This document defines the permanent provenance mapping for this project and
the rules governing it. It is established during execution 1005-1 and
applies to all subsequent executions unless explicitly superseded by a
future authorized prompt.

## Permanent mapping

```
prompts/promptXXXX-X.txt
        ↓
execution XXXX-X
        ↓
reports/reportXXXX-X.md
results/XXXX-X/
figures/XXXX-X/
```

Each execution is identified by a unique ID of the form `XXXX-X` (e.g.
`1005-1`). The same ID is used consistently across the source prompt file,
the generated report, the results directory, and the figures directory.

## Rules

1. Each execution has a unique ID. IDs are never reused.

2. The prompt, report, results, and figures for a given execution all share
   the same ID (`promptXXXX-X.txt`, `reportXXXX-X.md`, `results/XXXX-X/`,
   `figures/XXXX-X/`).

3. Executed prompts are immutable. Once a prompt file has been executed, its
   content must not be edited. If the scientific intent changes, a new
   prompt with a new ID is created instead.

4. Reviewed reports and results are not silently overwritten. Once a report
   has been produced and is available for human scientific review (or has
   been reviewed), it must not be regenerated in place without explicit
   authorization.

5. Corrections require a new execution ID. If an error is discovered in a
   completed execution, the fix is performed under a new execution ID, not
   by mutating the original.

6. A correction must explicitly identify the execution it corrects (e.g. in
   its report, under "Relationship to prior executions").

7. Every report identifies its source prompt at the top of the document,
   using the exact path (e.g. `prompts/prompt1005-1.txt`).

8. Machine-readable outputs (JSON, CSV, etc.) should contain an
   `execution_id` field where practical, so outputs remain traceable to
   their origin even if separated from their directory context.

9. If an expected report already exists before an execution begins, the
   execution must stop rather than overwrite it, unless a future authorized
   prompt explicitly defines a reproducibility rerun procedure that permits
   regeneration.

## Status at execution 1005-1

No prior executions existed before 1005-1. This protocol document is itself
an output of execution 1005-1 and establishes the rules going forward.
