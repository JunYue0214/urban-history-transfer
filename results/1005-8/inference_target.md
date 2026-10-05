# Final Gate 2 inference target (execution 1005-8)

## Population Gate 2 claims may generalize to

**YCEO-detectable global urban agglomerations with defensible GHSL overlap**:
urban agglomerations large and spatially coherent enough that (a) they are
resolved as a distinct polygon in the Natural-Earth-derived YCEO cluster
product, and (b) at least 50% of
that polygon's area is explained by one or more GHSL urban centres sharing no
other cluster (unit IoU >= 20%).

Concretely, under the primary rule this is **2107 urban
units (2374 underlying UCDB centres)**, skewed toward
**larger, longer-established** agglomerations (Section 15 of the report) and
present in 5 of 6 broad world regions with N >= 30 (all 6 if Oceania,
N=21, is merged with a neighbouring region
for validation only).

## What this explicitly does NOT cover

* All global urban centres (the GHSL universe, N=10,915) — most small and
  recently urbanized centres are not resolved by the YCEO product and are
  excluded from inference, not merely under-weighted.
* Any claim about recently urbanized cities specifically (they are
  under-represented: 35% of the
  included sample was urbanized after 1975 vs
  59% of the excluded sample).
* Pixel- or neighbourhood-scale claims within a cluster.
* Any causal claim (unchanged from 1005-6).

## Why this wording, not a broader one

Reweighting back to the full 10,915-city population was considered (Section
12 of the report) and rejected as the *primary* strategy because inclusion
probability is structurally near zero for a large share of small/recent
cities (not merely a sampling accident), which would require extreme,
high-variance weights. Stating the restricted target directly is more honest
than claiming a broader population via an unstable weight.
