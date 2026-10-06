# Gate 2 failure diagnosis (1006-1)

Evidence used: only results already produced (1005-4…1005-9), the YCEO documentation bundled in the 1005-7 ZIP, and one new
local computation in this execution (volume vs area trajectories in the local UCDB sample). No post-hoc significance is used
as a criterion. Literature claims are limited to what search results confirmed (see `prior_art_audit.md`).

## A. Response mixing (urban LST minus rural reference)

*Documented fact (YCEO documentation §II, VI):* cluster SUHI = mean LST of urban pixels minus mean LST of non-urban, non-water pixels
**within the same cluster**, with rural pixels limited to ±50 m of the urban median elevation; the authors state the result "is a function
of both the urban form and the rural environment".

*Evidence for:* M0 (S+C) has **negative** out-of-region R² for Europe (−0.26), South America (−0.14) and Asia (−0.01) in the leave-region-out
runs, i.e. even the present-state model does not transfer between continents — consistent with region-specific rural references,
though not proof. Residual Moran's I stays 0.16 (k=8) with or without H.

*Evidence against:* both nighttime and summer-daytime SUHI failed; richer climate controls (C2) did not move ΔR² (−0.0003); the one
positive stream (ridge) was reproduced by pseudo-history. None of these directly tests whether removing the reference helps.

**Assessment: plausible, untested, and the only explanation that one inexpensive response change can test.** It is not established.

## B. History representation (area timing only)

*Evidence for (new, computed here on the 10,915-city Gate 1 sample):* implied mean building height (built volume / built area) changes
modestly over time — median ratio to its 2020 value 1.09 in 1975, 1.04 in 2000, 1.01 in 2015; only 2.4% of cities show <1% change. Per-epoch correlation between
the area-ratio and volume-ratio trajectories is 0.977–0.990. So **within GHSL, a volume (verticalization) history is
almost a re-expression of the area history that failed**; GHSL cannot supply an independent morphological H.
Scalar descriptors of the same trajectory were also null (+0.0017, CI −0.0106, +0.0119).

*Evidence against:* nothing tested here shows that an independent morphological, green-space or material history would matter; the claim that
"morphology is the missing signal" remains a hypothesis. No multi-epoch compactness, height or greenness source was verified.

**Assessment: plausible, but not testable with data already local, and no external source was verified.** The point about GHSL redundancy is a result, not an inference.

## C. Scale / ontology mismatch (YCEO clusters vs GHSL centres)

*Evidence for:* only 22% of the Gate 1 sample (2,374 of 10,915 centres) entered the primary sample; included units are larger and older (log-population SMD ≈ 1.0, YOB SMD −0.56);
median unit IoU ≈ 0.5; 146 units are multi-city aggregates.

*Evidence against:* three geometry rules (40%, 60% coverage; no IoU floor) were all null (−0.0014, −0.0057, −0.0022); dominant-city H on all units was null
(−0.0065); the subset analyses showed no positive subgroup. These show the null is not sensitive to the matching thresholds tested; they do not test the
~78% of centres that were never matched.

**Assessment: weaker as an explanation of the null within the population studied, but it limits what the null covers.**

## D. What the dynamic-boundary lead can and cannot say

Dynamic H on 1,274 units: ΔR² +0.0157 (CI +0.0017, +0.0293); fixed H on the same units +0.0106 (CI −0.0067, +0.0251). The two CIs overlap heavily,
so the data do not show that dynamic H beats fixed H on that subset. It is one of seven boundary specifications run, below the 0.02 guidance, and uncorroborated. It is
an unconfirmed lead; it is not used to choose the pivot.

## Synthesis (ranking by what can be tested next)

1. **A (response mixing): leading, testable now** with one external dataset.
2. **B (representation): plausible but blocked** — GHSL volume cannot test it and no other source is verified.
3. **C (ontology): bounded** by the three geometry sensitivities already run.
A fourth possibility, not separable from A and B with current data: there may simply be no history signal at this scale and response.
The failure diagnosis cannot exclude that; Pivot A is partly designed to be able to say so.
