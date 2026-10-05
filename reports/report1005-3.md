# Execution Report 1005-3

Execution ID:
1005-3

Source Prompt:
prompts/prompt1005-3.txt

Previous Execution:
1005-2

Report:
reports/report1005-3.md

Results:
results/1005-3/

Figures:
figures/1005-3/

Task name: Global Data Feasibility and Scientific Identifiability Audit

**This execution is an EVIDENCE AUDIT, not a data analysis. No global
research data were downloaded, no real-city correlations/regressions/ML
models were fitted, and the candidate hypothesis was not tested. All
findings below are feasibility/identifiability findings about whether a
future study would be possible and well-posed, not results about whether
"history matters" is true.**

---

## 1. Executive Summary

This audit examined whether the candidate scientific question —
"does a city's historical development pathway (H) carry information
about its environmental response (R) beyond what present-day state (S)
and background climate/context (C) already explain?" — is (a)
data-feasible at global scale without unmanageable data volume, (b)
free of fatal circularity/leakage problems as currently specified, and
(c) sufficiently distinct from existing literature to be worth pursuing.

**Headline findings:**

1. **Data feasibility is good.** The GHSL product family (GHS-UCDB,
   GHS-BUILT-S, GHS-BUILT-V, GHS-POP, GHS-AGE, GHS-OBAT) plausibly
   supports a city-level, low-data-volume (Tier 1/Tier 2) research
   architecture — GHS-UCDB alone is a ~1.7GB global vector/table
   product with ~2,600 pre-computed per-city attributes, avoiding most
   raw-raster downloads. A pre-aggregated global SUHI dataset covering
   over 10,000 cities, 20+ years, monthly already exists (Yang/Xu/
   Chakraborty et al. 2024). See Section 3 and
   `results/1005-3/dataset_inventory.csv`.
2. **One circularity problem is confirmed, not just hypothesized.**
   Using "built-up area inside a flood hazard zone" as both a history
   feature (H_where) and a hydrological response (R) is directly
   circular by construction (risk register item B) — and the global
   literature search independently found a 2023 *Nature* paper
   (Rentschler et al.) that documents exactly this quantity at global
   scale, confirming both that it is a real, feasible H_where feature
   and that it cannot simultaneously be an independent R.
3. **A second critical problem was found by direct evidence, not
   speculation.** The official JRC built-stock-age product (GHS-AGE
   R2025A) — the single richest candidate H_when variable — is defined
   by its own documentation as the epoch in which 50% of **the built-up
   surface of 2020** was first exceeded per grid cell. This is a
   real-world, official-product confirmation of risk register item A
   (mathematical coupling: H encoding present-day S by construction).
   Using this product as-is for H_when would be scientifically invalid;
   a custom construction from pre-reference-epoch data is required.
4. **No direct prior-art collision was found**, but several close
   partial collisions were, and must be explicitly differentiated from
   in any future design — most notably a 2025 *Landscape and Urban
   Planning* paper (Jung, Dyson, Alberti) that already tests whether a
   historical-pathway proxy (redlining grade) predicts present LST after
   controlling for present land cover, in 3 US cities. See Section 11.
5. **"Urban environmental memory" is AMBIGUOUS/OVERLOADED as a term** —
   "ecological memory" and "urban memory" both already carry
   well-established, different meanings in adjacent fields (disturbance
   ecology; planning/heritage). See Section 12.
6. **The deepest identifiability problem (risk register item M,
   S–H multicollinearity) cannot be resolved by audit alone** — only a
   real, cheap pilot can determine whether H carries numerically
   separable information from S. This is the central argument for the
   falsification-oriented pilot in Section 16.

No scientific definition (S, H, C, R) was finalized. No pilot cities
were selected. No scientific hypothesis test occurred. All dataset and
literature facts in this audit were obtained via web search and small
documentation-page fetches; several primary domains (JRC/Copernicus
human-settlement portal, ScienceDirect) could not be directly fetched in
this execution's environment, so facts are marked `VERIFIED_SECONDARY`
rather than `VERIFIED_OFFICIAL` throughout — see Section 3 and
`results/1005-3/source_ledger.csv`.

---

## 2. Exact Task Boundaries

This execution operated strictly as a **Research Engineer / Scientific
Feasibility Auditor**, not as Principal Investigator. Permitted actions
(per `prompts/prompt1005-3.txt` Section 1): inspecting official dataset
documentation, metadata, API/download-interface documentation, and small
catalog files; searching scientific literature for feasibility/prior-art
verification; documenting definitions; identifying confounding,
circularity, and leakage risks; estimating data scale; proposing
candidate implementations explicitly labeled as candidates.

Explicitly prohibited (and not performed): finalizing the scientific
design; declaring novelty established; selecting a final response
variable; selecting pilot cities; downloading large/global raster
datasets; running real-data scientific analyses; optimizing a sensing
network; testing the main hypothesis.

All dataset/literature research in this execution was performed via
web search and fetching small HTML documentation/catalog/article pages
only. No bulk/raster/tabular research dataset was downloaded.

---

## 3. Dataset Feasibility Findings

See `results/1005-3/dataset_inventory.csv` for the full per-dataset
machine-readable record (20 datasets; verification status, resolution,
coverage, size, license, city-level-summary availability, etc.) and
`results/1005-3/source_ledger.csv` for the source of every factual claim.

**GHSL family (primary feasibility backbone):** GHS-UCDB R2024A (JRC,
DOI 10.2905/JRC.05RDPR0) is a ~1.7GB global vector/table product
covering 11,422 urban centres with ~2,600 pre-computed attributes across
471 indicators, multi-temporal back to 1975 — this single product
likely satisfies a large share of the audit's S/H table-level needs
without any raster download. GHS-BUILT-S, GHS-BUILT-V, and GHS-POP
(all R2023A) provide multi-epoch (1975–2030, 5-year interval) built-up
surface, built-up volume, and population grids at 100m–1km resolution;
each full global epoch is on the order of 1.9–4.8GB, with **no native
partial-area download** — city-level extraction in practice requires
Google Earth Engine or NASA AppEEARS server-side AOI reduction rather
than direct file download, which is the architecture this audit
recommends (Section 15). **GHS-AGE R2025A** (built-stock age) is
confirmed to exist but, critically, is defined relative to the 2020
endpoint (see Section 13/Executive Summary) and cannot be used directly
as H_when. **GHS-OBAT** (building-level age/height/compactness) and
**GHS-SMOD/GHS-DUC** (degree-of-urbanisation) were confirmed to exist
but not deep-audited; both are `UNVERIFIED` pending follow-up.

**Background context (C):** a Köppen-Geiger 1km global climate
classification (Beck et al. 2018, CC BY 4.0, a single 67.67MB file) is
an ideal Tier-1 candidate. ERA5-Land (ECMWF/Copernicus CDS, 1950–present,
hourly, ~9km) supports small-footprint city-point extraction via the
CDS API without bulk download. WorldClim v2.1 and CHELSA are both
viable ~1km global climatologies, but WorldClim's **license could not be
confirmed** (conflicting CC-BY-NC-SA vs CC-BY claims found — must be
checked directly before use). SRTM, MERIT DEM, and Copernicus DEM
(GLO-30/GLO-90) are all viable global elevation sources with different
coverage/resolution tradeoffs (SRTM: 60°N–56°S gap; MERIT: better
high-latitude coverage; Copernicus DEM: best completeness but with
access-tier restrictions).

**Thermal response (R):** MODIS LST (MOD11A2/MYD11A2, 1km, 8-day,
Terra from 2000, Aqua from 2002) is accessible without bulk download via
AppEEARS/Earth Engine, but **imposes a hard pre-2000 ceiling** on
thermal-response history regardless of sensor choice. VIIRS LST's short
record (NASA's product only since Oct 2023) makes it unsuitable as a
primary multi-decade backbone. **A major finding:** a pre-aggregated
global SUHI dataset already exists (Yang, Xu, Chakraborty et al. 2024,
*Remote Sensing of Environment*, DOI 10.6084/m9.figshare.24821538) —
over 10,000 cities, 20+ years, monthly, already framed as an
urban-rural contrast rather than raw LST. This is simultaneously the
best Tier-1 thermal-R data source found and a significant prior-art
signal (Section 11).

**Hydrological/flood datasets:** JRC/CEMS-GloFAS flood hazard maps and
WRI Aqueduct Floods are both viable HAZARD/EXPOSURE products but, per
Section 9, cannot serve as an independent R. The Global Flood Database
(Tellman et al. 2021, *Nature*) — 250m, MODIS-based, 913 observed flood
events, 2000–2018 — is the only candidate found for a genuinely
independent, realized/observed hydrological response, though its
coverage is uneven (DFO-catalogue-dependent, documented country-level
gaps) and its time series is both short and dated (ends 2018).

**Verification caveat (applies to all findings above):** the primary
JRC/Copernicus human-settlement documentation portal and ScienceDirect
could not be directly fetched in this execution's network environment;
all facts above were obtained via web-search synthesis of official data
catalogues, companion peer-reviewed papers, and Google Earth Engine's
dataset catalog (which mirrors official metadata), and are marked
`VERIFIED_SECONDARY`, not `VERIFIED_OFFICIAL`, in
`results/1005-3/dataset_inventory.csv`. Two specific unresolved
conflicts are flagged: GHS-BUILT-S's DOI (two different strings found)
and WorldClim's license (two different terms found). Both require
direct human/unblocked-network confirmation before being treated as
settled facts.

---

## 4. Urban-Unit Comparison

Four candidate analysis units were audited (full structured comparison
in `results/1005-3/scientific_design_decision_matrix.csv`, category
`analysis_unit`):

| Unit | Temporal consistency | Boundary-artifact risk | Twin-matching suitability | Future-information conditioning risk |
|---|---|---|---|---|
| GHS Urban Centre (UCDB) polygon, fixed at a reference epoch | High internal consistency across cities at that epoch | Medium — depends on which epoch is used as the fixed reference | Good — standardized, globally comparable | **Present if the reference epoch postdates the historical window being summarized** |
| Fixed non-UCDB 2020 footprint (custom threshold) | Medium | Medium-high (threshold-sensitive) | Fair | Same risk as UCDB, with less methodological transparency |
| Time-varying/dynamic footprint (boundary redefined per epoch) | High, by construction | Low | Fair — requires careful "same city" bookkeeping across changing boundaries | Low — this is the designed mitigation |
| Regular global grid cells | High | None (no boundary ambiguity) | Poor — grid cells are not a city-scientific unit | Low, but loses city-level interpretability |

**The explicitly flagged issue — using a 2020-defined urban boundary to
summarize 1975 history — is acceptable only as a documented,
sensitivity-tested simplification, not as the unexamined default.**
It is acceptable when: (a) the historical quantity being summarized is
genuinely a *trajectory feature* (timing, rate, direction) rather than
an absolute historical *level*, and (b) a time-varying-boundary version
of the same quantity is computed and shown not to materially change
conclusions. It is problematic when: (a) the historical "level" itself
(e.g., 1975 built-up area within the 2020 boundary) is used as if it
were an independent historical measurement, since the 2020 boundary
mechanically determines which 1975 land is counted at all, or (b) cities
that annexed, merged, or fragmented between 1975 and 2020 are treated as
a single continuous unit without disclosure. Recommended sensitivity
analyses: recompute key H features under (i) the reference/fixed
boundary, (ii) a boundary fixed at the *start* of the historical window,
and (iii) a fully time-varying boundary; report whether the H–R
relationship (if any) survives across all three.

**No final unit was selected.** This remains `PENDING_SCIENTIFIC_DECISION`.

---

## 5. History-Variable (H) Feasibility

Nine candidate H variables were audited per the source prompt's Section
7 list. Advisory classification (not a PI decision):

| # | Candidate H variable | Source (candidate) | Duplicates S? | Outcome-encoding risk | Advisory classification |
|---|---|---|---|---|---|
| 1 | Built-up surface trajectory | GHS-BUILT-S multi-epoch | High if terminal epoch included (risk A); low if trajectory *shape* only | Low (independent of R) | STRONG CANDIDATE, with mandatory terminal-epoch exclusion |
| 2 | Population trajectory | GHS-POP multi-epoch | High if terminal epoch included | Low | STRONG CANDIDATE, same caveat as #1 |
| 3 | Built-volume trajectory | GHS-BUILT-V multi-epoch (epoch coverage PENDING dataset-audit confirmation) | Medium-high if terminal epoch included | Low | POSSIBLE, pending confirmation of BUILT-V's historical epoch range |
| 4 | Built-stock age distribution | GHSL built-up age product (exact official product name PENDING dataset-audit confirmation) | Medium (most-recent age bin overlaps present composition) | Low | STRONG CANDIDATE if the product's epoch granularity is confirmed adequate; otherwise POSSIBLE |
| 5 | Horizontal-vs-vertical development trajectory | Derived from BUILT-S + BUILT-V ratio over time | Medium | Low | STRONG CANDIDATE — most distinctive H_how feature, pending BUILT-V epoch confirmation |
| 6 | Expansion compactness/fragmentation trajectory | Derived landscape-pattern metrics from built-up grids | Low-medium | Low | POSSIBLE — higher processing burden, better suited to a Tier-2/3 validation role than a Tier-1 default |
| 7 | Directional expansion relative to existing centre | Derived geometric analysis of multi-epoch built-up grids | Low | Low | POSSIBLE — low circularity but unclear a-priori link to R; exploratory |
| 8 | Urbanization relative to elevation/slope | DEM x built-up overlay | Low | Low | STRONG CANDIDATE, provided elevation/slope is not *also* claimed as a C control for the same purpose (bookkeeping requirement) |
| 9 | Urbanization relative to flood-prone space | Flood hazard layer x built-up overlay | Low (vs. S) | **CRITICAL if the same quantity is reused as hydrological R** (risk B) | CONDITIONAL CANDIDATE — acceptable only if hydrological R is defined independently (Section 9) |

The single most important general finding: **every H variable above is
"STRONG CANDIDATE" or better only on the condition that it excludes
information from the terminal/reference epoch** (to avoid risk A,
mathematical coupling with S) **and does not share its underlying raw
layer with whatever is chosen as R** (to avoid risk B, outcome leakage).
Both conditions must be enforced by explicit variable-provenance
bookkeeping, not assumed.

---

## 6. Present-State Variable (S) Audit

The critical question posed by the source prompt — what must be in S so
an apparent "history effect" is not a disguised present-day morphology
effect — was audited as follows:

**Indispensable controls** (must be in S, or any "H adds information"
claim is not credible): present built-up area/fraction, present
population and density, present built volume. These three jointly
capture "how big, how dense, how tall" a city currently is — the
minimal morphology vector needed before any residual-information claim
about H is meaningful (directly addresses risk H, urban-size
confounding).

**Optional controls** (strengthen S but are not strictly required for a
first-pass test): urban footprint area as distinct from built-up area
(footprint includes non-built interstitial space; captures a different
compactness dimension), imperviousness (where a credible global product
exists; otherwise likely redundant with built-up fraction), basic urban
morphology indicators (e.g., building height variance, if obtainable
without large data burden).

**Dangerous controls — likely mediators, not confounders:** present-day
vegetation/greenness is the clearest example. If a city's historical
pathway causally shaped its current green-infrastructure endowment,
and that endowment affects thermal response, then controlling for
present greenness in a naive regression removes part of the very
pathway the study is trying to detect (risk N, post-treatment
overcontrol). This should be treated as a candidate *mediator* requiring
a mediation-analysis framework or an explicit, disclosed
with/without-this-control sensitivity comparison — not folded silently
into S as if it were an obvious confounder.

**Redundant variables:** population density and built-up fraction are
likely to be highly correlated at the urban-centre scale (both
approximate "how intensively is this footprint used"); including both
without checking collinearity risks diluting interpretability without
adding information. A collinearity check (VIF) among S components is a
required step before S is finalized — itself `PENDING_SCIENTIFIC_DECISION`.

**S was not finalized.**

---

## 7. Background-Context (C) Audit

Climate classification (e.g. Köppen-Geiger), continuous climate
normals (e.g. from a reanalysis/climatology product), elevation/slope,
and an aridity index are the primary candidates for C; see
`results/1005-3/dataset_inventory.csv` for per-product verification
status and `results/1005-3/scientific_design_decision_matrix.csv`
(category `C`) for the comparative assessment. The dataset audit
confirmed a strong, low-burden option set for Tier 1/2: the
Köppen-Geiger 1km classification (67.67MB, CC BY 4.0) for categorical
climate; ERA5-Land (city-point extraction via the CDS API, no bulk
download) for continuous climate normals; and any of SRTM/MERIT
DEM/Copernicus DEM for elevation/slope, each with small city-level
extraction footprints despite large global archive sizes. WorldClim and
CHELSA are viable alternatives to ERA5-Land but WorldClim's license is
currently unresolved (Section 3).

**Distinguishing background confounder from mediator from present-day
state variable** (a conceptual clarification independent of which exact
product is chosen): climate/latitude/elevation are background
confounders — they predate and are causally upstream of both H and R,
and must be conditioned on, not treated as outcomes. Present-day
greenness, as discussed in Section 6, is the clearest candidate
*mediator* — a variable potentially caused by H and in turn affecting R,
which must NOT be naively conditioned on in the same way as a
confounder. Present built-up morphology (S) sits conceptually between
these: it is the thing being tested as "possibly disguising" an H
effect, so it is a required control, but its own causal relationship to
H (S is literally produced by the H trajectory) is exactly why the
multicollinearity risk (register item M) and the post-treatment risk
(register item N) are both unavoidable, structural features of this
research design — not fixable by picking better variables, only
manageable by disclosure, sensitivity analysis, and appropriately
scoped (associative, not causal) claims.

---

## 8. Thermal-Response Audit

The dataset audit confirmed MODIS LST (MOD11A2/MYD11A2, NASA LP DAAC,
DOI 10.5067/MODIS/MOD11A2.061) as the primary viable multi-decade
thermal backbone: 1km resolution, 8-day composites, Terra from
2000-02-18 and Aqua from 2002-07-04 to present, accessible via NASA
AppEEARS or Google Earth Engine without bulk archive download — but
with a **hard ceiling of no pre-2000 coverage**, regardless of sensor
choice. VIIRS alternatives exist at finer resolution (375m) but with a
much shorter record (NASA's VNP21IMG product only since October 2023),
making VIIRS unsuitable as a primary historical backbone, though
potentially useful for recent-period cross-sensor validation (risk
register item I). A major, directly relevant finding: **a pre-aggregated
global SUHI dataset already exists** (Yang, Xu, Chakraborty et al.
2024, *Remote Sensing of Environment* 312, DOI
10.6084/m9.figshare.24821538), covering over 10,000 cities, 20+ years,
monthly, as an urban-rural contrast with a companion 1km gridded layer
— this should likely be used or extended as the thermal R data source
rather than rebuilt from raw LST pixels, substantially reducing Tier-2/3
processing burden. See `results/1005-3/dataset_inventory.csv`
(`global-uhi-dataset` row).

**On raw LST vs. anomaly/contrast response:** `R = raw city LST` is
scientifically inferior to an urban-rural anomaly/SUHI-style contrast
response, because raw LST is overwhelmingly determined by background
climate/latitude/season (i.e., by C) rather than by anything
attributable to the city's urban history or present state. A raw-LST
regression would mostly be re-deriving the climate classification, not
testing the candidate question. This conclusion is reinforced, not just
assumed: the field's own highest-profile existing global products
(the Yang/Chakraborty lineage) already operationalize SUHI as an
urban-rural contrast, not raw LST — using raw LST as R would be a step
backward from established practice. The anomaly/contrast formulation
remains subject to the mandatory rural-reference-definition sensitivity
test (risk register item J, falsification plan Section 14).

**No final thermal metric was selected.**

---

## 9. Hydrological-Response Audit

This audit required distinguishing HAZARD, EXPOSURE, VULNERABILITY,
REALIZED IMPACT, and INUNDATION RESPONSE, per the source prompt.

- **HAZARD** (e.g., a static flood-probability/return-period map) and
  **EXPOSURE** (e.g., built-up area or population located inside a
  hazard zone) are properties of *where* development happened relative
  to a hazard map — i.e., they are naturally H_where or S features, not
  independent outcomes.
- **VULNERABILITY** (susceptibility to harm given exposure, e.g.
  building quality, elevation of structures, defense infrastructure) is
  conceptually closer to an outcome but is rarely available as a clean
  global product independent of exposure itself.
- **REALIZED IMPACT** / **INUNDATION RESPONSE** (e.g., observed,
  event-based flood occurrence or damage) is the only category that is
  plausibly a genuinely independent measured response, since it reflects
  an actual physical event rather than a static overlay of the same
  built-up/hazard layers used elsewhere in the design.

**Explicit circularity finding (does not require further literature
search to establish — this is a definitional/mathematical point):**
"built-up area inside a flood hazard zone" cannot simultaneously serve
as an H_where feature (where did development happen) and as a
hydrological R (what is the environmental response) — these are the
same quantity under two names. This is flagged as risk register item B,
severity CRITICAL, and the source prompt's own Section 11 explicitly
anticipated this exact failure mode.

**Whether a scientifically independent R exists at global scale with
manageable data burden:** the dataset audit found exactly **one**
candidate: the **Global Flood Database** (Tellman et al. 2021, *Nature*
596:80–86) — 250m resolution, MODIS-based, 913 discrete *observed* flood
events, 2000–2018, globally distributed but dependent on the Dartmouth
Flood Observatory catalogue with documented coverage gaps (e.g., fewer
than 30% of China's DFO-recorded floods captured). This is a realized/
observed-impact product, genuinely independent of the built-up/hazard
layers used to construct H_where, and is the only product found that
avoids the circularity trap. However, its time series is both
comparatively short relative to a multi-decade H window and now over
seven years stale (ends 2018; its continuation/update status was not
reconfirmed in this execution) and its country-level coverage is
uneven. **This audit's provisional conclusion is that hydrological R is
feasible only in this realized-impact/observed-inundation form, and is
not feasible as exposure-overlap restated as a response** (per the
explicit circularity found in Section 9 above and confirmed
independently by Rentschler et al. 2023 in the literature audit,
Section 11). Given the coverage/currency caveats on the Global Flood
Database, this audit recommends treating hydrological R as
**secondary/optional relative to thermal R**, not as a co-equal primary
response family, pending further confirmation of a current, more
complete realized-inundation product.

---

## 10. Brief Alternative-Response Audit

- **Vegetation/ecological productivity** (e.g., trends in a greenness/
  productivity index): plausible as an independent replication domain
  if a thermal-memory signal is found, since vegetation responds to
  urbanization through a partially distinct physical pathway
  (impervious-surface/microclimate effects on plant growth) from LST
  retrieval. Globally available at low data burden (same underlying
  sensor families as LST in several cases). Caution: as noted in
  Section 6, present vegetation is also a candidate *mediator* for the
  thermal pathway, so it would need a different framing (as an outcome
  in its own right, not as a control) to serve this replication role.
- **Carbon** (e.g., urban carbon flux/stock proxies): conceptually
  interesting but global, city-level, analysis-ready carbon-flux
  products with low data burden are less mature/standardized than LST
  or built-up products; likely higher data burden and lower near-term
  tractability than thermal or vegetation replication domains.
- **Biodiversity**: global, consistently measured, city-level
  biodiversity-response products comparable in maturity to GHSL/MODIS
  are not well established; likely the least tractable of the three
  alternative families at this audit's confidence level without
  dedicated further investigation.

**Provisional ranking for a compelling independent replication domain:**
vegetation/greenness first (data-mature, but requires careful
mediator-vs-outcome framing), carbon second (conceptually appealing,
data-immature), biodiversity third (least globally standardized). This
ranking is advisory only.

---

## 11. Prior-Art Collision Findings

See `results/1005-3/prior_art_matrix.csv` for the full structured
record (13 papers).

**Overall verdict: no DIRECT COLLISION found.** No single paper was
found that performs, at global/multi-city scale, an explicit
information-content comparison of R~S+C vs. R~S+C+H (or an equivalent
present-day-twin/analogue-divergence design) using a continuous,
multi-decade developmental-trajectory H, for either a thermal or
hydrological response. This is an absence-of-evidence finding from a
targeted literature search (not a formal systematic review), and should
not be read as a guarantee that no such study exists anywhere.

**Multiple PARTIAL COLLISIONS require explicit disclosure and
differentiation in any future design:**

1. **Historical-redlining-and-LST literature** (closest conceptual
   match found): Jung, Dyson & Alberti (2025, *Landscape and Urban
   Planning*) test whether historical redlining grade (a categorical
   1930s policy label, used as H) predicts present-day LST (R) after
   controlling for present-day landscape heterogeneity (S-like
   control), in 3 US cities — finding the apparent effect fragments
   once present land-cover heterogeneity is accounted for. Two related
   2025 papers (a *Nature Communications* tree-canopy/redlining study
   and a Philadelphia multi-scale study) extend this same logic. These
   are **structurally the same test as candidate Test A**, just with a
   categorical, single-country H rather than a continuous, global,
   multi-decade trajectory. A future design must explicitly
   differentiate on: (a) continuous vs. categorical H, (b) global vs.
   US-only scope, (c) explicit incremental out-of-sample model
   comparison vs. this literature's in-sample fragmentation analysis.
2. **Global urbanization-into-flood-hazard literature**: Rentschler et
   al. (2023, *Nature*), Chen et al. (2022), and Rajib et al. (2022)
   all document, at global scale, that settlement/impervious growth
   inside flood-hazard zones has accelerated — directly confirming
   H-feasibility for the flood-prone H_where candidate, but also
   independently confirming the circularity this audit flagged for
   hydrological R (Section 9).
3. **City-analogue/climate-twin matching methodology**: a 2019 global
   study (~520 cities) matches *future* city climates to *present* city
   climates using analogue/distance-matching methods — supplying the
   matching machinery candidate Tests B/C would reuse, but answering a
   different question (climate communication, not history-conditioned
   response divergence). The matching technique itself is therefore
   **not novel**; any novelty in Tests B/C rests entirely on matching on
   (S,C) and testing against historical divergence D_H, which this
   prior work does not do.
4. Additional **RELATED** (not overlapping on the core question, but
   directly informative for specific identifiability risks) findings:
   a global study linking climate/vegetation background to SUHI-trend
   sensitivity across 511 cities (relevant to risk F); a study showing
   SUHI intensifies faster in lower-income countries (relevant to risk
   G, development-level confounding); a study showing divergent
   urban-rural greening trends affect SUHI (relevant to risk J,
   rural-reference contamination); a 1,288-cluster China study linking
   present urban form to SUHI (closer to an S-type than H-type
   analysis).

**Conclusion:** the candidate question is not already directly answered
in the literature, but it sits in a crowded neighborhood of closely
related work, and any future proposal/paper must explicitly position
itself relative to the redlining-LST literature (item 1) and the
global flood-growth literature (item 2) specifically, not merely cite
generic "urban heat island" or "urban growth" background.

## 12. Terminology Findings

**Verdict on "urban environmental memory": AMBIGUOUS/OVERLOADED.**

- **"Ecological memory"** is a formally defined term in disturbance
  ecology and has *already* been extended to urban systems in at least
  two distinct technical senses unrelated to the candidate framing:
  (a) social-ecological memory/stewardship capacity in urban green
  space (Barthel et al., *Ecology and Society*), and (b) a quantitative
  term in urban stormwater pollutant wash-off modeling. This makes
  "urban ecological memory" specifically **OVERLOADED**.
- **"Urban memory"** is a well-established term in urban planning,
  architecture, heritage studies, and cultural geography (place-identity
  and collective-memory theory, UNESCO's Historic Urban Landscape
  framework) — entirely about cultural/collective memory and heritage
  identity, with **no relation** to biophysical environmental legacy.
  Using this phrase risks being misread by an entire adjacent field.
- **"Path dependence"** is a decades-old economics/institutional-theory
  term, already widely used in urban climate-*policy*/governance
  literature to mean institutional or political inertia (e.g., carbon
  lock-in) — not a biophysical environmental-response legacy. Usable
  only with explicit qualification.
- **"Urban legacy effect" / "developmental legacy"**: no single
  dominant, pre-claimed technical definition was found in the
  biophysical/remote-sensing literature searched; "legacy effect" is
  used descriptively in the redlining-LST papers (Section 11) but not
  as a formally branded term there either — these phrases carry the
  **lowest collision risk** of the terms audited.

**Recommendation:** avoid branding the candidate effect as "urban
environmental memory." Prefer a plain descriptive technical phrase
(e.g., "historical-pathway effect on environmental response conditional
on present state," or "developmental-trajectory legacy effect") unless
a future PI deliberately chooses to engage with and explicitly
differentiate from the ecological-memory and urban-memory literatures.
**No branded term was adopted as final in this execution.**

---

## 13. Identifiability/Circularity Red-Team

Full structured register (14 risks, A–N) in
`results/1005-3/identifiability_risk_register.csv`. Summary of the most
severe findings:

- **CRITICAL, resolvable by redesign:** Risk B (outcome leakage) — the
  flood-hazard-overlap formulation of hydrological R is directly
  circular with H_where as specified. Must be redefined to a realized/
  observed-inundation measure or dropped.
- **CRITICAL, not resolvable by audit alone:** Risk M (multicollinearity
  between S and H) — because H mechanically produces S, the statistical
  power to distinguish "H adds information" from "H is redundant with
  S" cannot be determined without real data. This is the single
  strongest argument for a cheap, falsification-oriented pilot
  (Section 16) rather than direct global-scale investment.
- **HIGH severity, manageable with disclosed sensitivity analysis:**
  Risk D (2020-boundary-on-1975-history leakage), Risk E (spatial
  autocorrelation inflating cross-validation), Risk F (climate
  confounding history), Risk G (development-level/income confounding),
  Risk J (rural-reference contamination of SUHI), Risk N
  (post-treatment overcontrol from naive S specification).
- **MEDIUM severity:** Risk A (mathematical coupling, manageable by
  excluding the terminal epoch from H), Risk C (temporal leakage,
  manageable by strict windowing), Risk H (urban-size confounding,
  manageable with a rich S), Risk I (sensor/product artifacts,
  manageable via cross-sensor replication), Risk K (survivor/selection
  bias in urban-centre databases, manageable as a disclosed scope
  limitation), Risk L (MAUP, manageable via multi-unit sensitivity
  reporting).

**No risk was found to be fatal to the research program as a whole**,
but two (B and M) are fatal to specific *current formulations* (the
flood-exposure R definition, and any claim that treats a positive M1-
vs-M0 result as settled without power/collinearity diagnostics).

---

## 14. Falsification Strategy

Candidate falsification/negative-control tests, designed so that a
"positive" result (test fails to falsify) is informative, not
guaranteed:

1. **Shuffled history within climate zones** — randomly permute H
   among cities sharing the same climate class, breaking any true
   H–R association while preserving C's marginal distribution; a
   model that still finds an "H effect" under this permutation
   indicates a confounding or leakage problem, not a real signal.
2. **Spatially permuted history** — randomly permute H across all
   cities regardless of climate; a stricter null than (1).
3. **Pseudo-history generated from present state** — construct a fake
   H deterministically from S (e.g., assign "early-urbanizing" to the
   densest present-day cities) and check whether this manufactured,
   by-construction-redundant H appears to "add information" in the
   same pipeline; if it does, the pipeline itself is biased toward
   finding spurious H effects (directly tests risk M/A).
4. **History variables intentionally redundant with S** — deliberately
   include an H feature known to be a near-linear function of an S
   feature; the pipeline should correctly show near-zero marginal
   contribution; if it does not, the evaluation method is suspect.
5. **Geographically blocked / leave-continent-out / leave-climate-zone-
   out validation** — the primary defense against risk E and a partial
   defense against risk F; a true signal should survive held-out
   continents/climate zones, not just random folds.
6. **Alternate city boundaries** (fixed-reference vs. time-varying vs.
   history-start-fixed) — tests risk D; a true signal should be
   qualitatively robust across boundary definitions.
7. **Alternate rural-reference definitions** for SUHI — tests risk J;
   a true signal should not depend on one specific buffer definition.
8. **Alternate history windows and endpoint years** — tests whether
   conclusions are an artifact of one arbitrarily chosen window (e.g.,
   1975–2020 vs. 1990–2020 vs. 2000–2015).
9. **Temporally reversed history, where meaningful** — e.g., testing
   whether a *later* window of growth "predicts" an *earlier* response
   measurement (which should show no effect, or only an effect
   explainable by reverse confounding); a positive result here would
   indicate the pipeline detects spurious associations regardless of
   temporal order.

**What would weaken or falsify the "history matters" claim:** finding
that the H–R association disappears (or is statistically indistinguishable
from the pseudo-history / shuffled-history controls) once spatially
blocked validation and a sufficiently rich S are used; finding that the
apparent effect is not robust across at least two boundary definitions,
two rural-reference definitions, or two history windows; finding that
collinearity diagnostics show H's informative components cannot be
statistically separated from S at any usable sample size. **Tests
designed only to confirm the hypothesis (e.g., reporting only random-CV
performance, or only one boundary/rural-reference definition) were
deliberately excluded from this list.**

---

## 15. Low-Data-Volume Architecture

Three tiers, per the source prompt's required structure:

| Tier | Scope | Order-of-magnitude storage | Compute burden | Scientific capability | Limitations |
|---|---|---|---|---|---|
| **Tier 1 — metadata/city-table only** | Pre-aggregated per-urban-centre attributes (UCDB table fields, any pre-aggregated SUHI/climate-normal city tables) | Tens of MB globally (thousands of cities x tens of attributes x several epochs) | Trivial — fits in memory on a laptop | Sufficient for Tests A and B as *first-pass* feasibility checks using only variables already pre-computed by official products | Limited to whatever attributes official products already pre-compute; cannot construct genuinely novel H_how features (e.g., horizontal-vs-vertical ratio) if the needed raw grids aren't already summarized per city |
| **Tier 2 — city-level extracted raster summaries** | For each city (not globally), extract and summarize small raster windows (built-up/volume/LST/DEM) clipped to the city + buffer, across epochs | Low hundreds of MB to a few GB for a few thousand cities (small per-city clips, not global mosaics) | Modest — batch per-city extraction, parallelizable, no full-globe raster held in memory at once | Supports constructing custom H_how/H_where features (e.g., BUILT-V/BUILT-S ratio, elevation-stratified built-up share) and custom SUHI with alternate rural-reference definitions, at full global city coverage | Still requires a per-city download/extraction step for each raw product used; total volume scales with number of cities and number of raw layers, not with global resolution |
| **Tier 3 — selective pixel-level analysis for validation** | Full-resolution pixel-level analysis restricted to a small, deliberately chosen subset of cities (e.g., the pilot sample in Section 16) for deep validation of Tier-1/2 summaries | Low GB for a few dozen cities' full-resolution stacks | Moderate, bounded by the deliberately small sample size | Validates that city-level summaries (Tier 1/2) are not hiding important within-city heterogeneity or MAUP sensitivity; supports the alternate-unit sensitivity tests in Section 14 | Not globally representative by design; exists only to stress-test the city-level architecture, not to replace it |

**Recommended architecture:** global inference at Tier 1/2 (city-level),
with Tier 3 used only for the falsification pilot and targeted
robustness checks — exactly the structure the source prompt requested
("global inference is city-level… pixel-level data are used only where
necessary for validation"). No large data were downloaded to produce
this assessment; all figures above are order-of-magnitude estimates
based on official product documentation (see
`results/1005-3/dataset_inventory.csv`) and standard city counts in
global urban-centre databases, not measurements from an actual download.

---

## 16. Proposed Hypothesis-Killing Pilot Design (Design Only — Not Executed)

**Purpose:** determine, as cheaply as possible, whether there is enough
independent historical signal to justify global-scale investment — i.e.,
directly probe risk M (multicollinearity) and risk B/N (leakage/
overcontrol) with real numbers, before committing to full global data
engineering.

**Sampling strategy (no named cities selected):**
- Span **at least 4–6 continents/major world regions** to break the
  climate/region confound described in risk F.
- Span **at least 3–4 climate classes** (e.g., tropical, arid,
  temperate, cold) with multiple cities per class, so climate can be
  conditioned on rather than merely spanned.
- Span a **wide range of present-day city sizes** (at least an order of
  magnitude in population/built-up area) to stress-test risk H.
- **Deliberately include "present-day twin" pairs**: pairs of cities
  matched to be as similar as possible in S and C but as different as
  possible in H (per candidate Test B) — this is the single most
  information-dense sampling choice, since it directly targets the
  candidate question's core contrast.
- **Deliberately include at least one "pseudo-history" and one
  "shuffled-history" control batch** (Section 14, tests 1 and 3) using
  the same cities, to calibrate how much apparent "signal" the pipeline
  manufactures from redundant or fake H.

**Candidate sample-size range (not finalized):** on the order of
**40–120 cities**, structured as 10–30 twin-pairs/triplets across the
climate/continent strata above. This range is chosen to be large enough
for basic collinearity/power diagnostics (Section 13, risk M) and
spatially-blocked validation (risk E), while remaining small enough for
Tier-3 pixel-level validation (Section 15) on every pilot city if
needed. The exact number is explicitly `PENDING_SCIENTIFIC_DECISION`.

**Expected data volume:** at the upper end of Tier 2 / lower end of
Tier 3 in Section 15's table — city-level extracted summaries plus
full-resolution pixel validation for a double-digit-to-low-hundreds
city sample, i.e., low single-digit GB, not a global bulk download.

**Pilot success/failure criteria (falsification-oriented, not
publication-oriented):** the pilot should be judged to have *failed to
support* further investment if (a) H's candidate features cannot be
statistically distinguished from S at this sample size (high VIF /
near-zero partial contribution) even before considering out-of-sample
performance, or (b) the pseudo-history/shuffled-history controls produce
"apparent effects" of similar magnitude to the real H, or (c) any
candidate thermal/hydrological R turns out, on inspection of real pilot
data, to be dominated by sensor artifacts or rural-reference choice
(risk I/J) rather than a stable signal. The pilot should be judged
*worth scaling* only if a real H effect survives spatially blocked
validation, multiple boundary/rural-reference/window sensitivity
checks, and is clearly larger than the pseudo-history/shuffled-history
controls.

---

## 17. Decision Matrix Summary

Full matrix (24 candidate choices across 9 design dimensions, 11
qualitative columns each) in
`results/1005-3/scientific_design_decision_matrix.csv`. Headline
pattern: almost every candidate in every dimension carries at least a
MEDIUM confounding or circularity risk, or a PENDING data-availability
confirmation — there is **no "free" design choice** in this candidate
study; every dimension requires an explicit, disclosed tradeoff. The
clearest "avoid as currently stated" entry is hydrological R defined as
flood-hazard-zone overlap (directly circular, Section 9). The clearest
"strong candidate, data permitting" entries are: UCDB-polygon-based
analysis unit paired with a time-varying-boundary sensitivity arm;
built-up/population trajectory and built-stock age distribution for
H_when; horizontal-vs-vertical growth ratio for H_how; a multi-
dimensional morphology vector for S; climate classification plus
continuous climate normals for C; urban-rural SUHI anomaly (not raw
LST) for thermal R; leave-continent-out/leave-climate-zone-out
validation as the primary transferability metric.

---

## 18. Unresolved Scientific Decisions Requiring PI Review

All items below are `PENDING_SCIENTIFIC_DECISION` (consistent with
`reports/PROJECT_MANIFEST.md`):

- Final choice of analysis unit (and whether a time-varying-boundary
  sensitivity arm is mandatory, not optional).
- Final H_when / H_where / H_how component list, and confirmation of
  which are mechanically safe (exclude terminal epoch, no shared raw
  layer with R).
- Final minimal-sufficient S (indispensable vs. optional vs. dangerous/
  mediator controls; collinearity diagnostics among S components).
- Final C component list, and explicit resolution of any variable that
  could play a double role as both C and H_where (e.g., elevation/slope).
- Final thermal R metric (which SUHI definition, which rural-reference
  definition, day vs. night, climatological vs. extreme).
- Whether hydrological R is pursued at all, and if so, in which
  realized-impact/observed-inundation form (pending dataset
  confirmation of feasibility).
- Whether a socioeconomic/development-stage covariate is added to C or
  S to address risk G.
- Final validation strategy as the *primary reported* metric (this
  audit recommends leave-continent-out/leave-climate-zone-out, with
  random-CV reported only as a labeled upper bound).
- Final pilot sample size and exact sampling frame (this audit proposes
  a range of 40–120 cities, not a final number).
- Whether/how to proceed given the prior-art and terminology findings
  in Sections 11–12.

---

## 19. Exact Files Created/Modified

| Path | Type | Status |
|---|---|---|
| `prompts/prompt1005-3.txt` | prompt | Created (verbatim, read back and confirmed before execution) |
| `results/1005-3/identifiability_risk_register.csv` | csv | Created (14 rows, A–N) |
| `results/1005-3/scientific_design_decision_matrix.csv` | csv | Created (24 rows) |
| `results/1005-3/dataset_inventory.csv` | csv | Created (20 rows) |
| `results/1005-3/prior_art_matrix.csv` | csv | Created (13 rows) |
| `results/1005-3/source_ledger.csv` | csv | Created (16 rows) |
| `results/1005-3/run_metadata.json` | json | Created (finalized at end of execution) |
| `reports/report1005-3.md` | report | This report |
| `figures/1005-3/` | dir | Created, left empty (no scientific figures authorized) |

**Explicitly NOT modified** (per hard prohibition and explicit user
instruction): `prompts/prompt1005-1.txt`, `prompts/prompt1005-2.txt`,
`reports/report1005-1.md`, `reports/report1005-2.md`,
`results/1005-1/`, `results/1005-2/`.

---

## 20. Integrity Statement

- Were any large research data downloaded? **No.** Only small HTML
  documentation/catalog pages and article abstract/landing pages were
  fetched.
- Was any real city scientifically analyzed? **No.**
- Was any scientific model fitted? **No.**
- Was any main hypothesis tested? **No.**
- Was any final scientific definition (S/H/C/R) locked? **No** — all
  remain `PENDING_SCIENTIFIC_DECISION`.
- Was any prior-art collision found? **No DIRECT collision.** Several
  PARTIAL collisions were found and disclosed (Section 11), most
  notably the historical-redlining-and-LST literature and the global
  urbanization-into-flood-hazard literature. None were hidden or
  downplayed.
- Was any critical identifiability problem found? **Yes — two** (risk
  register items B and M; see Section 13). Both are disclosed, neither
  is hidden or downplayed.
- Was any historical reviewed artifact altered? **No** —
  `prompts/prompt1005-1.txt`, `prompts/prompt1005-2.txt`,
  `reports/report1005-1.md`, `reports/report1005-2.md`,
  `results/1005-1/`, and `results/1005-2/` were not modified.
- Was any future execution (`prompt1005-4`) started? **No.**

---

## QUESTIONS FOR PI REVIEW

**Q1. Is the candidate scientific question materially different from
existing global urban heat / urban growth studies?**
Based on the literature audit (Section 11): **yes, materially different
from anything found, but not by a wide margin.** No study was found
that performs the exact information-content test (R~S+C vs. R~S+C+H)
at global, multi-decade, multi-city scale for either response family.
The closest match (Jung, Dyson & Alberti 2025 and related
redlining-LST papers) performs structurally the same *logical* test but
with a categorical, single-country H rather than a continuous, global
H, so the candidate question's differentiation must rest explicitly on
scale and on H's continuous/multi-decade operationalization, not on the
basic logical structure of "test H controlling for S," which already
has precedent.

**Q2. Which history component appears most scientifically defensible:
when, where, or how?**
Based on this audit's feasibility/circularity reasoning alone (Section
5): **H_how (specifically the horizontal-vs-vertical growth ratio)**
appears most defensible, because it is the least represented in
existing "urban expansion" literature (lower prior-art collision than
H_when's onset-timing framing) and has comparatively low circularity
risk, *conditional on* GHS-BUILT-V's historical epoch coverage being
confirmed adequate in the dataset audit. H_when (built-stock age
distribution) is the second most defensible if its exact product
epoch-granularity holds up. H_where is defensible for the
elevation/slope framing but requires careful bookkeeping against C, and
is explicitly NOT defensible in its flood-hazard-overlap form (risk B).

**Q3. Can H be defined without trivially reconstructing S?**
Yes, in principle — provided H is restricted to trajectory *shape*,
*timing*, and *directionality* features with the terminal/reference
epoch excluded (Section 5), rather than any feature whose value at the
reference epoch equals or near-equals an S component. Whether this
remains true with *real* data (i.e., whether the surviving H features
still carry statistically distinguishable information from S) is
exactly risk M and cannot be confirmed without the pilot in Section 16.

**Q4. Can thermal R be defined independently enough from H and S?**
Likely yes for an SUHI-style anomaly formulation (Section 8) — LST
retrieval is measured by an independent sensor process unrelated to how
H or S are constructed, so outcome leakage (risk B) is not a concern for
thermal R the way it is for the flood-hazard formulation of hydrological
R. The main open risks for thermal R are confounding (climate, rural-
reference choice) and sensor artifacts (risks I, J), not leakage. One
important qualification from the dataset audit: a pre-aggregated global
SUHI product already exists (Section 8), so "independent enough from
H and S" is confirmed, but "independent enough from existing prior art"
is a separate, open question (Section 11) — any future design should
clarify what it adds beyond applying an H-conditional test to this
existing (or a similarly constructed) SUHI product.

**Q5. Is hydrological R feasible as an independent response, or is it
too circular/data-limited?**
As currently specified (flood-hazard-zone overlap), it is **circular
and not independent** (Section 9, risk B) — this conclusion does not
depend on further research, and is independently confirmed by the
global flood-growth literature (Section 11). A *realized-impact/
observed-inundation* reformulation using the Global Flood Database
(Tellman et al. 2021) is feasible in principle but **data-limited**: its
record is short (2000–2018), dated (ends over seven years ago, currency
unconfirmed), and unevenly covered by country (Section 9). This audit's
view is that hydrological R should be considered **secondary/optional**
relative to thermal R unless a more current, complete realized-inundation
product is confirmed.

**Q6. Which candidate analysis unit creates the least serious temporal
and boundary bias?**
The **time-varying/dynamic footprint** (Section 4) creates the least
boundary bias by construction, but at higher processing burden and with
its own "same city across time" bookkeeping challenge. The most
practical recommendation is to use a **fixed reference-epoch UCDB
polygon as the primary unit, with a mandatory time-varying-boundary
sensitivity arm** — not to rely on either unit alone.

**Q7. What is the single most dangerous threat to causal/scientific
interpretation?**
**The structural tension between risk M (S–H multicollinearity) and
risk N (post-treatment overcontrol).** These two risks pull in opposite
directions: insufficient control of S risks mistaking a disguised
present-state effect for a history effect, while over-control of S
(especially of mediator-like components) risks erasing a true history
effect entirely. No choice of variables resolves this tension — it is a
property of the causal structure itself (history produces the present
state) — and no amount of documentation audit can determine, in
advance of real data and an explicit causal model, which failure mode a
given analysis is closer to. This is this audit's single most important
finding and the primary justification for scoping any future claim as
associative/predictive ("transferability") rather than causal, per the
project's existing governance principle.

**Q8. What result in a future pilot should cause the project to abandon
the "history matters" hypothesis?**
If, in the pilot (Section 16): (a) H's candidate features show VIF/
collinearity with S so high that no meaningful partial contribution can
be estimated at any practical sample size, or (b) the pseudo-history and
shuffled-history negative controls produce apparent "effects" of
comparable magnitude to the real H under the same pipeline, or (c) any
apparent H–R association fails to survive leave-continent-out validation
and at least two alternative boundary/rural-reference definitions — any
one of these should be treated as sufficient grounds to abandon or
substantially re-scope the hypothesis, per Section 14's falsification
design.

**Q9. What is the smallest scientifically meaningful pilot?**
Smaller than the 40–120-city range proposed in Section 16 risks
insufficient power for the collinearity/power diagnostics that are the
pilot's primary purpose; this audit's advisory view is that **roughly
10–15 deliberately matched present-day-twin pairs (20–30 cities) spanning
at least 3 climate zones and 2 continents**, plus the pseudo-history/
shuffled-history control batches, is the smallest configuration likely
to produce an interpretable answer to "is there enough independent
signal to justify scaling" — below this, negative results would be
difficult to distinguish from mere underpowering. This is advisory, not
final.

**Q10. Should the next execution: A. run a small metadata/table-level
pilot, B. acquire a small amount of raster data, C. revise the
scientific question, or D. stop this direction?**

**ADVISORY ONLY — not a PI decision.** Based on this audit: a hybrid of
**A then conditionally B** is recommended — first run the Tier-1
metadata/table-level version of the pilot (Section 16) using only
already-pre-aggregated UCDB/climate-table attributes, specifically to
get an early, cheap read on risk M (S–H collinearity) and the
negative-control calibration (pseudo-history/shuffled-history). If that
cheap pass does **not** immediately kill the hypothesis (i.e., H shows
non-trivial, non-collinear residual association with available R proxies
even at Tier 1), **then** proceed to B (a small, bounded Tier-2/3 raster
acquisition for the same pilot sample) to get a more decisive answer
before considering any larger investment. **C (revise the question)**
is advisable specifically for the hydrological-response arm, which as
currently specified is circular (Section 9) and should be reformulated
or dropped regardless of the thermal-arm outcome. **D (stop entirely)**
is not supported by this audit's findings — no fatal, unfixable problem
was found for the thermal-response arm of the candidate question — but
remains the PI's prerogative, particularly if Section 11's prior-art
findings turn out to show a direct collision.
