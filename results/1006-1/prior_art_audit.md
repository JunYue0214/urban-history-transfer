# Prior-art audit (1006-1)

**Method and limits.** Discovery was by web search only (WebFetch is blocked here), so I saw titles, authors and
snippets, not full texts. "Verified" below means title/authors/venue were returned by search. Anything I
describe from general background and could not confirm is marked *recalled, unverified* and is not relied on.
A search that finds nothing is weak evidence of a gap, not proof.

## Verified items

| Item | What search returned | Relevance |
|---|---|---|
| Lee, Yoo, Son, Cho, Im, Chakraborty (2026), *Nat. Commun.* 17:6445, "Global patterns of urban heat shaped by climate and morphology" | title, six authors, venue, date | Cross-sectional present-day morphology + climate → urban heat, global. Content beyond the title not read; I do not know its H, response definition or data. |
| Frolking, Mahtta, Milliman, Esch, Seto (2024), *Nat. Cities* 1:555, "Global urban structural growth shows a profound shift from spreading out to building up" | authors, >1,550 cities, scatterometer + Landsat built fraction, shift to vertical growth 1990s→2010s | Documents morphological (vertical) trajectories globally; no thermal response in the snippet. |
| Melchiorri et al. (2024), *Sci. Data* 11:82, GHS-UCDB paper | authors, >10,000 centres, 28 variables, epochs | Source of our H/S/C; not a hypothesis test. |
| Xiang & Quan, "Global gapless 1 km daily mean land surface temperature dataset (2003–2023)", Zenodo 10.5281/zenodo.17778992 | 25.2 GB, four zips (2003–07, 08–12, 13–17, 18–23), RMSE 1.84 K | The only concrete city-agnostic LST archive found for Pivot A; **daily mean**, not day/night; modelled/gap-filled; raster. |
| "Global increases in built-up volume indicate more divergent and less dispersed urban expansion patterns", *Nat. Commun.* 2026 | title only | Documents volume trajectories; thermal link unknown. |
| "Divergent urbanization-induced impacts on global SUHI trends since 1980s", *Remote Sens. Environ.* 2023; "SUHI effects intensify more rapidly in lower-income countries", *npj Urban Sustain.* 2025 | titles/snippets | Closest to "development stage vs thermal response"; both study trends or urbanization intensity, not history as a predictor of the present level beyond present state. |
| A Landsat study of 511 cities, 1985–2020 (title not captured) | snippet: SUHI sensitivity per % impervious more than tripled above ~30% impervious cover | Suggests state-dependent response; relevant to stage, not to path dependence. |

## Gap statement (search-limited)

Two targeted searches ("built-up trajectory predicts LST beyond current built-up fraction"; "timing of
urbanization … legacy") returned no study that tests, across many cities, whether trajectory features add
out-of-sample predictive power over present state. Closest are single-city or regional studies in which
development *type* (expansion into new land vs vertical conversion) changed LST. This is consistent with the
question being open, but my search was not systematic.

## Per-pivot collision

* **A (urban-side LST):** the global present-state→LST link exists (Lee et al. 2026 and earlier work). A history
  predictor with urban-side LST as response was not found. Moderate novelty, with the caveat that Gate 2 already
  tested SUHI, so A is a response change, not a new question.
* **B (morphological history):** vertical growth is documented (Frolking 2024; built-volume paper). Linking morphological
  *trajectory* to thermal response, controlling for present state, was not found. High novelty if a morphology
  history source exists. See the data audit: within GHSL, volume and area trajectories are almost redundant.
* **C (dynamic replication):** no prior art applies; it is a replication of our own unconfirmed result.
* **D (other responses):** vegetation/air-quality literature exists but I did not audit it individually and
  recalled citations are not listed. Novelty not assessed beyond "variable by response".

## Removed from the first draft

Citations to specific papers by Zhou, Peng, Manoli, Middel, McKinney and Stewart & Oke were written from
memory with unverified URLs/years and attributed claims; they are deleted rather than carried forward.
