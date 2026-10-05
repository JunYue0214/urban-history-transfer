# UCDB <-> thermal-data crosswalk design (execution 1005-6)

Status: PROVISIONAL. The thermal product's attribute schema and geometry type
could not be read in this execution (WebFetch blocked; documentation PDF not
opened). The protocol below is written for the most likely structure
(cluster polygons or points with an ID) and states the fallback for each
possible structure. No matchability N is estimated; none can be honestly
given without the file.

## 1. Identifier audit (from available metadata)

| Key | Thermal product (YCEO v4 cluster means) | Usable? |
|---|---|---|
| Polygon geometry | Probably present in the shapefile (urban clusters from Landscan extents) [INFERRED]; the SEDAC file is a Shapefile [VERIFIED_SINGLE] | **Primary key if present** |
| Coordinate pair (centroid) | Derivable from polygons or present as fields [UNRESOLVED] | Primary fallback |
| Custom cluster ID | Presumably present [INFERRED]; semantics UNRESOLVED | Bookkeeping key only, no external join |
| GHSL ID | Not expected: product is Landscan-based | No |
| City / metro name, country | UNRESOLVED; GEE description speaks of clusters, "not individual cities" | QA corroboration only |
| Yang 2024 DEA product | city coordinates presumably [INFERRED]; IDs UNRESOLVED | Same protocol if a table is confirmed |

UCDB side (verified locally): `ID_UC_G0`, name `GC_UCN_MAI_2025`, country
`GC_CNT_GAD_2025`, centroid, MULTIPOLYGON geometry in World Mollweide
(ESRI:54009), 11,422 cities.

## 2. Principle

Geometry first, names last. Fuzzy name matching is never the primary
strategy and never rescues a failed geometric match. All tolerances below are
fixed before the thermal file is opened; they may be adjusted only to fit the
verified geometry type (logged in the pre-registration amendment log) and
never by inspecting R.

## 3. Protocol A - both products have polygons (preferred)

Reproject both to ESRI:54009 (equal-area). For UCDB city u and thermal
cluster k compute intersection area I(u,k), A_u, A_k.

**ACCEPTED** (enters the primary sample) iff all hold:
1. u's centroid lies inside exactly one cluster k, and k contains exactly one
   UCDB centroid (mutual one-to-one);
2. area ratio A_u / A_k within [0.25, 4.0] (UCDB urban centre and cluster
   comparable in footprint);
3. I(u,k) / min(A_u, A_k) >= 0.5 (substantial overlap);
4. where the product provides a country field, country agrees (names are not
   required to agree);
5. R is non-missing and the product's own validity flag (if any) passes.

**AMBIGUOUS** (excluded from primary; analysed in sensitivity) if any:
* many-to-one: several UCDB centres in one cluster (merged agglomeration);
  sensitivity = aggregate: sum built-up/pop/volume and re-derive H over the
  merged UCDB cities, then analyse at cluster level (addresses MAUP);
* one-to-many: one UCDB polygon spans several clusters;
* centroid in a cluster but area ratio or overlap rule 2-3 fails;
* name or country contradicts an otherwise geometric match.

**REJECTED** if: no intersection and nearest cluster centroid farther than
10 km; country mismatch with no geometric support; R missing; cluster
excluded by the product itself.

## 4. Protocol B - thermal product has points/coordinates only

ACCEPTED iff the UCDB polygon contains the thermal point (or, if points are
cluster centroids, centroid-to-centroid distance <= 10 km) AND the match is
mutual nearest-neighbour AND the second-nearest candidate is at least 2x
farther than the nearest. AMBIGUOUS: mutual-nearest but ratio < 2, or distance
10-25 km, or several UCDB cities claiming one point. REJECTED: distance > 25
km or no mutual match. Same country check as above when available.

## 5. Protocol C - no geometry or coordinates (names only)

If the verified file truly has only names, no primary analysis is permitted;
the design returns to PROVISIONAL/REJECTED for that product. Name+country
matching may then only be reported as an exploratory, non-confirmatory
sensitivity, with the same one-to-one-key-plus-numeric-corroboration logic
used in 1005-5 (not reused as primary).

## 6. Reporting obligations

* Full per-pair audit table (accepted/ambiguous/rejected + reason), like
  `results/1005-5/ucdb_mtuc_crosswalk.csv`.
* Sample flow: 11,422 -> Gate 1 sample 10,915 -> accepted -> non-missing R.
* Balance of accepted vs unmatched cities on region, size, climate (C1),
  YOB, H descriptors; if balance is poor, state it before any model is run.
* Crosswalk uncertainty propagation: rerun primary Exp 1 on (a) accepted only,
  (b) accepted + ambiguous-aggregated, (c) a stricter variant (area ratio
  [0.5, 2.0], overlap >= 0.75).

## 7. Matchability estimate

Cannot be quantified honestly now. Expected qualitative pattern (INFERRED,
not a count): high match rates for isolated mid-to-large cities with compact
footprints; many-to-one ambiguity in dense multi-city agglomerations
(Pearl River Delta, Ruhr, Indo-Gangetic belt); losses for small UCDB centres
that the Landscan-based product does not resolve as clusters. Linking to the
1005-5 MTUC matched subsample is by `ID_UC_G0` through
`results/1005-5/ucdb_mtuc_crosswalk.csv`, i.e. it inherits that crosswalk's
conservative rules and requires no new matching.
