"""Generate the structured design-lock artifacts for execution 1005-6 (Gate 2A).

Pure local script: NO network access, NO research data read. It only writes
the audit tables / decision JSON / manifest template into results/1005-6/ so
that they are regenerated deterministically and can be tested.

Every metadata field carries an explicit verification status:
  VERIFIED_MULTI  - consistent across >=2 independent search/metadata results
  VERIFIED_SINGLE - seen in one source only
  INFERRED        - reasoned, not stated by a source
  UNRESOLVED      - could not be established (WebFetch was blocked, landing
                    pages / documentation PDFs were NOT read directly)
"""

from __future__ import annotations

import csv
import json
import platform
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "results" / "1005-6"

# --------------------------------------------------------------------------
# Candidate response definitions (prompt section 5/6)
# --------------------------------------------------------------------------
CANDIDATE_FIELDS = [
    "id", "candidate", "physical_interpretation", "urban_form_relation", "climate_sensitivity",
    "rural_reference_sensitivity", "day_night_note", "seasonal_dependence", "averaging_effect",
    "sensor_or_processing_confound", "state_or_response", "overlap_with_S", "overcontrol_risk",
    "plausibly_influenced_by_H", "cross_climate_comparability", "global_availability_in_verified_product",
    "role", "rationale",
]
CANDIDATES = [
    dict(id="A", candidate="Annual-mean daytime SUHI",
         physical_interpretation="Early-afternoon surface urban-rural LST contrast, dominated by evapotranspiration/albedo/vegetation contrast and solar loading",
         urban_form_relation="Moderate; mixes impervious fraction with the vegetation state of the rural reference",
         climate_sensitivity="High: sign can flip in arid/semi-arid cities (bare rural soil hotter than city); sensitive to precipitation and aridity",
         rural_reference_sensitivity="High: irrigated/green vs dry rural background changes sign and magnitude",
         day_night_note="Daytime: clear-sky sampling bias and solar-geometry dependence",
         seasonal_dependence="Strong; annual mean pools seasons with opposite sign in some climates",
         averaging_effect="Annual averaging dilutes seasonal sign changes (monsoon/dry-season cities)",
         sensor_or_processing_confound="Low for climatology (fixed sensor mix), high for trend",
         state_or_response="Response (a surface-energy-balance outcome of the present urban state)",
         overlap_with_S="Moderate (impervious fraction, built volume)", overcontrol_risk="Moderate if urban greenness is conditioned on",
         plausibly_influenced_by_H="Possible (materials, morphology, green-space legacy) but swamped by rural-reference moisture",
         cross_climate_comparability="Poor to moderate", global_availability_in_verified_product="Yes (YCEO v4 all_daytime_UHI band; Yang 2024 day)",
         role="NOT_SELECTED", rationale="Climate/rural-reference confounding is the most severe of the family; kept only as descriptive context"),
    dict(id="B", candidate="Annual-mean nighttime SUHI",
         physical_interpretation="Night-time surface urban-rural LST contrast, governed by stored heat release, sky-view/morphology, and anthropogenic heat; weak dependence on solar loading and on rural vegetation/moisture",
         urban_form_relation="Strong and comparatively direct (built-up fraction/volume, thermal mass)",
         climate_sensitivity="Moderate: depends on humidity, wind, background temperature, seasonality; smaller aridity sign-flip than daytime",
         rural_reference_sensitivity="Moderate: nocturnal rural cooling depends on land cover but is less moisture-driven than daytime",
         day_night_note="Night: no solar-geometry term, fewer retrieval artifacts from shadowing; MODIS night overpasses ~22:30 (Terra) / ~01:30 (Aqua) [INFERRED from sensor specs; exact product combination UNRESOLVED]",
         seasonal_dependence="Moderate; annual mean is the most globally comparable aggregation (no hemisphere/tropical season definition needed)",
         averaging_effect="Annual averaging loses little physical signal for a night-time storage-driven quantity",
         sensor_or_processing_confound="Low for climatology",
         state_or_response="Response (outcome of present urban state and surroundings), measured not modelled",
         overlap_with_S="Substantial (built density and volume strongly predict it) - this is the purpose of the M0 baseline",
         overcontrol_risk="Low-moderate: S3 includes built volume, a plausible mediator of H; handled by S1/S2/S3 gradient",
         plausibly_influenced_by_H="Plausible via accumulated built form, materials and densification pattern beyond present totals",
         cross_climate_comparability="Best of the family (still needs C)", global_availability_in_verified_product="Yes (YCEO v4 all_nighttime_UHI band expected; Yang 2024 night). Band/field names in the city-level file UNRESOLVED",
         role="PRIMARY", rationale="Cleanest answer to 'does R carry H-information beyond S and C': least contaminated by rural-reference moisture/vegetation and by solar-geometry/cloud-sampling artifacts, annual aggregation avoids season-definition ambiguity across hemispheres/tropics, and it is the response where a present-form-plus-history story is most physical. Not chosen for strongest expected effect."),
    dict(id="C", candidate="Warm-season (summer) daytime SUHI",
         physical_interpretation="Peak-heat-stress daytime contrast, health-relevant",
         urban_form_relation="Moderate; again mixed with rural-reference vegetation state",
         climate_sensitivity="High (aridity, monsoon timing)", rural_reference_sensitivity="High (peak-season vegetation/irrigation contrast)",
         day_night_note="Daytime artifacts as in A", seasonal_dependence="'Summer' in YCEO is hemisphere-defined [winter months VERIFIED_SINGLE; summer months INFERRED]; tropical 'warm season' is ill-defined",
         averaging_effect="Fewer observations per mean -> noisier, more clear-sky bias", sensor_or_processing_confound="Low for climatology",
         state_or_response="Response", overlap_with_S="Moderate", overcontrol_risk="Moderate",
         plausibly_influenced_by_H="Possible", cross_climate_comparability="Poor-moderate",
         global_availability_in_verified_product="Yes (summer_daytime_UHI expected)",
         role="SECONDARY", rationale="Most decision-relevant for heat exposure and an independent physical channel from B; used as the pre-registered alternate thermal outcome (falsification test 8). Not primary because of rural-reference and season-definition confounding"),
    dict(id="D", candidate="Warm-season (summer) nighttime SUHI",
         physical_interpretation="Night contrast in the warm season", urban_form_relation="Strong",
         climate_sensitivity="Moderate", rural_reference_sensitivity="Moderate", day_night_note="Night",
         seasonal_dependence="Hemisphere-defined season; tropical ambiguity", averaging_effect="Noisier than B",
         sensor_or_processing_confound="Low", state_or_response="Response", overlap_with_S="Substantial",
         overcontrol_risk="Low-moderate", plausibly_influenced_by_H="Plausible", cross_climate_comparability="Moderate",
         global_availability_in_verified_product="Yes (summer_nighttime_UHI expected)",
         role="DESCRIPTIVE_ONLY", rationale="Largely redundant with B; reported descriptively, not as a pre-registered outcome (avoid multiplicity)"),
    dict(id="E", candidate="Monthly / seasonal SUHI climatology (12-vector)",
         physical_interpretation="Seasonal cycle of SUHI", urban_form_relation="Mixed",
         climate_sensitivity="Very high (phenology, monsoon)", rural_reference_sensitivity="High",
         day_night_note="Both", seasonal_dependence="Is the seasonal structure", averaging_effect="None (keeps signal) but 24 correlated outcomes",
         sensor_or_processing_confound="Low-moderate", state_or_response="Response", overlap_with_S="Moderate",
         overcontrol_risk="Moderate", plausibly_influenced_by_H="Unclear", cross_climate_comparability="Poor",
         global_availability_in_verified_product="Monthly cluster means listed for YCEO v4 (package size UNRESOLVED); Yang 2024 months 1-12 per GEE catalog",
         role="EXPLORATORY_ONLY", rationale="Multiplicity and climate-phenology confounding; useful only for post-hoc description after the primary test"),
    dict(id="F", candidate="Interannual SUHI variability (SD across years)",
         physical_interpretation="Year-to-year fluctuation of SUHI", urban_form_relation="Weak",
         climate_sensitivity="High (weather variability, cloud sampling)", rural_reference_sensitivity="High",
         day_night_note="Both", seasonal_dependence="n/a", averaging_effect="Dominated by retrieval/sampling noise",
         sensor_or_processing_confound="High (cloud sampling, sensor ageing, product reprocessing)",
         state_or_response="Response/noise", overlap_with_S="Low", overcontrol_risk="Low",
         plausibly_influenced_by_H="Implausible mechanism", cross_climate_comparability="Poor",
         global_availability_in_verified_product="Derivable only from yearly cluster means (package UNRESOLVED)",
         role="REJECTED", rationale="Signal-to-noise too low and no mechanism linking developmental history to variability"),
    dict(id="G", candidate="Long-term SUHI trend (2003-2018)",
         physical_interpretation="Rate of change of SUHI", urban_form_relation="Linked to recent expansion (a form of H itself)",
         climate_sensitivity="Moderate", rural_reference_sensitivity="High (rural greening/browning trends)",
         day_night_note="Both", seasonal_dependence="n/a", averaging_effect="Fits 16 noisy annual points",
         sensor_or_processing_confound="High (Terra/Aqua drift, reprocessing, changing land-cover maps in the reference)",
         state_or_response="Response, but algebraically entangled with recent H", overlap_with_S="Low", overcontrol_risk="High (trend vs recent growth is near-tautological)",
         plausibly_influenced_by_H="Yes, trivially (recent growth)", cross_climate_comparability="Poor",
         global_availability_in_verified_product="Derivable only from yearly cluster means (package UNRESOLVED)",
         role="EXPLORATORY_CONTRAST", rationale="Optional contrast outcome, exploratory and not confirmatory; expected positive association with recent expansion is partly definitional and must not be read as legacy"),
    dict(id="H", candidate="Extreme-heat / upper-tail SUHI",
         physical_interpretation="Peak SUHI (e.g. multi-day extremes)", urban_form_relation="Mixed",
         climate_sensitivity="High", rural_reference_sensitivity="High", day_night_note="Daytime in the known product",
         seasonal_dependence="Warm-season", averaging_effect="Tail statistic", sensor_or_processing_confound="High (clear-sky sampling)",
         state_or_response="Response", overlap_with_S="Moderate", overcontrol_risk="Moderate",
         plausibly_influenced_by_H="Possible", cross_climate_comparability="Poor",
         global_availability_in_verified_product="NO verified city-level pre-aggregated product. Mentaschi et al. 2022 (extremes) is a 1 km daily gridded product, i.e. raster-scale",
         role="REJECTED", rationale="Only available as pixel-level daily rasters - violates the coarse-scale discipline"),
    dict(id="I", candidate="Raw urban LST (no rural contrast)",
         physical_interpretation="Absolute surface temperature", urban_form_relation="Weak relative to climate",
         climate_sensitivity="Overwhelming (latitude, elevation, season)", rural_reference_sensitivity="n/a",
         day_night_note="Both", seasonal_dependence="Dominant seasonal cycle", averaging_effect="n/a",
         sensor_or_processing_confound="Moderate", state_or_response="Mostly climate state", overlap_with_S="Low", overcontrol_risk="n/a",
         plausibly_influenced_by_H="Negligible after C", cross_climate_comparability="Very poor",
         global_availability_in_verified_product="Not in the verified city-level products; would require MODIS raster processing (rejected)",
         role="REJECTED_NEGATIVE_CONTROL_IN_PRINCIPLE", rationale="Would serve as a negative control (H should add nothing beyond C) but obtaining it requires pixel-level MODIS processing; not worth the scale violation"),
    dict(id="J", candidate="Urban-rural difference formulations (SUE vs DEA vs fixed buffer)",
         physical_interpretation="The family of definitions behind A-E", urban_form_relation="n/a",
         climate_sensitivity="Definition-dependent", rural_reference_sensitivity="IS the rural-reference choice",
         day_night_note="n/a", seasonal_dependence="n/a", averaging_effect="n/a", sensor_or_processing_confound="n/a",
         state_or_response="Measurement definition", overlap_with_S="n/a", overcontrol_risk="n/a", plausibly_influenced_by_H="n/a",
         cross_climate_comparability="Definition-dependent", global_availability_in_verified_product="SUE: YCEO v4. DEA: Yang 2024 (access path unresolved)",
         role="SENSITIVITY_AXIS", rationale="Cross-product agreement (SUE vs DEA) is the pre-registered alternate-rural-reference test (falsification test 9), conditional on a city-level DEA table being confirmed"),
]

# --------------------------------------------------------------------------
# Dataset / source audit (prompt section 7)
# --------------------------------------------------------------------------
SOURCE_FIELDS = [
    "source_id", "name", "citation_or_id", "authority_class", "method", "spatial_unit", "n_cities_claimed",
    "temporal_coverage", "temporal_resolution", "day_night", "response_variants", "format_and_access",
    "login_required", "data_volume", "rural_reference", "crosswalk_keys", "same_dataset_as", "verification_summary",
    "unresolved", "scale_discipline_verdict", "role",
]
SOURCES = [
    dict(source_id="S1", name="YCEO Surface Urban Heat Islands v4 (SEDAC archive)",
         citation_or_id="Chakraborty & Lee (2023), NASA SEDAC, DOI 10.7927/S5M5-ZK14 [VERIFIED_MULTI: Earthdata/GEE catalog snippets]; method paper Chakraborty & Lee 2019, Int. J. Appl. Earth Obs. Geoinf. 74:269-280",
         authority_class="Official NASA EOSDIS/SEDAC archive of a peer-reviewed-method product (tier 1)",
         method="Simplified Urban-Extent (SUE): MODIS 8-day Terra+Aqua LST; Landscan urban extents; GMTED2010 elevation; ESA CCI land cover [VERIFIED_MULTI]",
         spatial_unit="Urban CLUSTERS (may merge several cities) from Landscan-derived fixed extents, not individual cities [VERIFIED_MULTI]; also 300 m pixel product",
         n_cities_claimed="'over 10,000' urban clusters/extents in v4 [VERIFIED_MULTI]; earlier versions: ~9,500 (2019 paper) and 7,374 after filtering [VERIFIED_SINGLE] - v4 filtered N UNRESOLVED",
         temporal_coverage="2003-2018 [VERIFIED_MULTI]; ENDS BEFORE Gate-1 endpoint T=2020",
         temporal_resolution="Averaged composite (2003-2018), yearly composites, monthly cluster-mean composites [VERIFIED_SINGLE for package list]",
         day_night="Daytime and nighttime [VERIFIED_MULTI]",
         response_variants="Annual, summer, winter x day/night (cluster-mean 'all averaged'); band names such as All_daytime_UHI, Summer_nighttime_UHI are GeoTIFF band names [VERIFIED_SINGLE]; shapefile field names UNRESOLVED",
         format_and_access="SEDAC data-download page: GeoTIFF (pixel; winter-pixel zip 814 MB) and Shapefile 'UHI (urban cluster means)' 4.7 MB zip [VERIFIED_SINGLE]; also Earth Engine asset YALE/YCEO/UHI/UHI_all_averaged/v4 (+monthly/yearly) [VERIFIED_MULTI]",
         login_required="Free NASA Earthdata login for SEDAC download [VERIFIED_SINGLE]",
         data_volume="City-level shapefile ~4.7 MB zip [VERIFIED_SINGLE]; sizes of monthly/yearly cluster packages UNRESOLVED; pixel GeoTIFFs hundreds of MB each (NOT needed)",
         rural_reference="Non-urban pixels (ESA CCI land cover, yearly) within the same fixed Landscan urban extent; no fixed buffer; filtered for urban/rural elevation difference and urban-area percentage [VERIFIED_MULTI]; exact thresholds UNRESOLVED. Known caveats: generalized reference, irrigation/agriculture/phenology influence, fixed extent cannot follow expansion [VERIFIED_MULTI]",
         crosswalk_keys="Cluster-level shapefile presumably carries polygon geometry and a cluster identifier [INFERRED]; attribute fields, ID, name/country presence UNRESOLVED",
         same_dataset_as="DIFFERENT product from Yang et al. 2024 (S3). Same SUE lineage as the GEE collection YALE/YCEO/UHI (S2 = alternate access path to the same product)",
         verification_summary="Identity, DOI, method, temporal range, day/night/annual/summer/winter availability, archive and approximate city-level file size corroborated by multiple snippets. Landing/documentation pages NOT read directly (WebFetch blocked)",
         unresolved="Shapefile field names; whether annual/summer/winter day/night means are in the 4.7 MB cluster file or a separate package; exact v4 cluster count; geometry type; cluster ID semantics; exact summer/tropical season definition; exact rural-pixel and elevation rules in v4; Terra/Aqua combination for night",
         scale_discipline_verdict="PASS (city-level, ~5 MB; no raster needed)",
         role="PRIMARY_CANDIDATE"),
    dict(source_id="S2", name="YCEO SUHI v4 via Google Earth Engine (YALE/YCEO/UHI/*_v4)",
         citation_or_id="Earth Engine Data Catalog; same DOI as S1", authority_class="Official catalog entry of S1",
         method="As S1", spatial_unit="As S1", n_cities_claimed="As S1", temporal_coverage="2003-2018", temporal_resolution="all/monthly/yearly averaged; pixel yearly",
         day_night="Both", response_variants="As S1", format_and_access="Earth Engine assets (requires GEE account and server-side export)",
         login_required="GEE account", data_volume="Server-side; export size unknown", rural_reference="As S1",
         crosswalk_keys="Feature properties for urban cluster [VERIFIED_SINGLE: 'properties for the urban cluster']; names UNRESOLVED",
         same_dataset_as="Same product as S1", verification_summary="Catalog entries exist for five/six assets", unresolved="Property schema; export route would be an API export of research data (human-only)",
         scale_discipline_verdict="PASS in principle", role="ALTERNATE_ACCESS_PATH_FOR_S1"),
    dict(source_id="S3", name="Global Urban Heat Island Intensity Dataset (Yang, Xu, Chakraborty et al. 2024)",
         citation_or_id="Yang Q., Xu Y., Chakraborty T.C., et al. (2024) Remote Sensing of Environment 312:114343, DOI 10.1016/j.rse.2024.114343; data DOI 10.6084/m9.figshare.24821538 [VERIFIED_MULTI]",
         authority_class="Peer-reviewed publication with persistent DOI (tier 2); community-hosted data (not an institutional archive)",
         method="Dynamic equal-area (DEA): iterative buffering until background reference area equals the central urban area; 8 temperature sources; clear-sky surface, all-sky surface and canopy UHII [VERIFIED_MULTI]",
         spatial_unit="City-centred; 10,196 cities in paper Fig. 1 [VERIFIED_SINGLE]; city definition/boundary source UNRESOLVED",
         n_cities_claimed=">10,000; 10,196 [VERIFIED_MULTI]", temporal_coverage="'over 20 years'; 2003-2020 monthly [VERIFIED_SINGLE for 2003-2020]; end year relative to T=2020 needs confirmation",
         temporal_resolution="Monthly (month 1-12), quarterly (21-24), annual (30); values x0.01 = degC [VERIFIED_SINGLE: GEE community catalog]",
         day_night="Day ('Day') and night ('Nig') [VERIFIED_SINGLE]",
         response_variants="Clear-sky surface, all-sky surface, canopy; eight GEE collections AMOD2, MOD1, MOD2, MYD1, MYD2, SAT, SMOD2, SMYD1 [VERIFIED_SINGLE]",
         format_and_access="Figshare record = README + links to Baidu Cloud Drive and Google Drive; gridded 1 km UHII on Earth Engine community catalog (projects/sat-io/open-datasets/UHII/*) [VERIFIED_MULTI]. NO verified direct city-level table URL",
         login_required="Baidu / Google Drive access (no scriptable stable URL)", data_volume="UNRESOLVED (1 km grids over 20 years x variants may be large; city tables unknown)",
         rural_reference="DEA background reference area equal in size to the urban area - theoretically better matched to urban size than SUE [VERIFIED_SINGLE for equal-area principle]; exact buffer/mask rules UNRESOLVED",
         crosswalk_keys="Coordinates presumably per city [INFERRED from a third-party study that assigned climate zones from lat/lon]; IDs UNRESOLVED",
         same_dataset_as="DIFFERENT from YCEO v4 (S1/S2). Overlapping authors/lineage only",
         verification_summary="Dataset identity and DOI robustly verified; distribution route and file content NOT verified",
         unresolved="Whether any city-level CSV/table exists; file names/sizes; ID and coordinate columns; exact end year; hosting persistence of Baidu/Google Drive links",
         scale_discipline_verdict="UNRESOLVED (city table existence unknown; gridded route would violate scale discipline)",
         role="ALTERNATE_REFERENCE_CANDIDATE (for rural-reference sensitivity)"),
    dict(source_id="S4", name="Chakraborty & Lee 2019 original SUE dataset (Yale Global Surface UHI Explorer, earlier versions)",
         citation_or_id="Int. J. Appl. Earth Obs. Geoinf. 74:269-280 (2019)", authority_class="Peer-reviewed; superseded by S1 (v4)",
         method="SUE", spatial_unit="Urban clusters", n_cities_claimed="~9,500 / 7,374 final [VERIFIED_SINGLE]", temporal_coverage="~15 years before 2017 [VERIFIED_SINGLE]",
         temporal_resolution="Annual/monthly", day_night="Both", response_variants="As S1 (older)", format_and_access="Explorer app / GEE", login_required="n/a",
         data_volume="n/a", rural_reference="MODIS MCD12Q1 land cover (fixed), later ESA CCI (~20% lower mean UHI) [VERIFIED_SINGLE]", crosswalk_keys="n/a",
         same_dataset_as="Predecessor of S1", verification_summary="Superseded", unresolved="n/a", scale_discipline_verdict="n/a", role="REJECTED_SUPERSEDED"),
    dict(source_id="S5", name="Mentaschi et al. 2022 global daily 1 km SUHI",
         citation_or_id="Global Environmental Change 72:102441, DOI 10.1016/j.gloenvcha.2021.102441 [VERIFIED_SINGLE]", authority_class="Peer-reviewed",
         method="MODIS Aqua MYD11A1 v061 daytime LST vs GHSL built-up; extremes", spatial_unit="1 km pixels, daily", n_cities_claimed="Global urban areas", temporal_coverage="2003-2020",
         temporal_resolution="Daily", day_night="Daytime only", response_variants="Warm-season median, 3-day extremes", format_and_access="Gridded; repository link UNRESOLVED",
         login_required="UNRESOLVED", data_volume="Large (daily 1 km global)", rural_reference="UNRESOLVED", crosswalk_keys="Raster", same_dataset_as="Distinct",
         verification_summary="Study verified; repository not", unresolved="Repository, size", scale_discipline_verdict="FAIL (daily 1 km rasters)", role="REJECTED_SCALE"),
    dict(source_id="S6", name="Si et al. 2022 dynamic urban-extent global SUHI",
         citation_or_id="ISPRS J. Photogramm. Remote Sens. 183:321-335 [VERIFIED_SINGLE]", authority_class="Peer-reviewed", method="Dynamic urban extent; MODIS",
         spatial_unit="Urban clusters", n_cities_claimed="UNRESOLVED", temporal_coverage="UNRESOLVED", temporal_resolution="UNRESOLVED", day_night="Both",
         response_variants="UNRESOLVED", format_and_access="No data-availability statement found", login_required="UNRESOLVED", data_volume="UNRESOLVED",
         rural_reference="Dynamic urban extent", crosswalk_keys="UNRESOLVED", same_dataset_as="Distinct", verification_summary="Paper exists; no dataset located",
         unresolved="Whether any data are released", scale_discipline_verdict="UNRESOLVED", role="NOT_USABLE_NO_DATA_FOUND"),
    dict(source_id="S7", name="Peng et al. 2012 (419 global big cities)",
         citation_or_id="Environ. Sci. Technol. (title seen: 'Surface Urban Heat Island Across 419 Global Big Cities') [VERIFIED_SINGLE: title only]", authority_class="Peer-reviewed",
         method="MODIS, buffer-based", spatial_unit="Cities", n_cities_claimed="419", temporal_coverage="UNRESOLVED", temporal_resolution="UNRESOLVED", day_night="UNRESOLVED",
         response_variants="UNRESOLVED", format_and_access="UNRESOLVED", login_required="UNRESOLVED", data_volume="Small", rural_reference="Buffer-based",
         crosswalk_keys="UNRESOLVED", same_dataset_as="Distinct", verification_summary="Coverage far below global scale needed", unresolved="n/a",
         scale_discipline_verdict="PASS (small) but coverage inadequate", role="REJECTED_COVERAGE"),
    dict(source_id="S8", name="Raw MODIS LST (MOD11A2/MYD11A2) processed by this project",
         citation_or_id="NASA LP DAAC", authority_class="Official", method="Would require building SUHI from rasters", spatial_unit="1 km pixels, 8-day",
         n_cities_claimed="n/a", temporal_coverage="2000/2002-present", temporal_resolution="8-day", day_night="Both", response_variants="Any",
         format_and_access="Large HDF/GeoTIFF tiles", login_required="Earthdata", data_volume="Hundreds of GB-TB globally", rural_reference="Project-defined (would add a new design degree of freedom)",
         crosswalk_keys="Raster", same_dataset_as="Underlies S1/S3", verification_summary="n/a", unresolved="n/a",
         scale_discipline_verdict="FAIL (violates global coarse-scale discipline)", role="REJECTED_SCALE"),
    dict(source_id="S9", name="'Global dataset on heat wave exposure due to the urban heat island effect' (Scientific Data, 2026)",
         citation_or_id="Nature Sci Data article s41597-026-06877-1 [VERIFIED_SINGLE: title/summary only]", authority_class="Peer-reviewed data descriptor",
         method="Derived heat-wave exposure; LST from a dataset by Zhang et al. (per snippet)", spatial_unit="Urban settlements", n_cities_claimed="UNRESOLVED", temporal_coverage="2003-2020 [VERIFIED_SINGLE]",
         temporal_resolution="UNRESOLVED", day_night="UNRESOLVED", response_variants="Exposure metrics, not SUHI climatology", format_and_access="UNRESOLVED", login_required="UNRESOLVED", data_volume="UNRESOLVED",
         rural_reference="UNRESOLVED", crosswalk_keys="UNRESOLVED", same_dataset_as="Distinct", verification_summary="Noticed late; not audited in depth",
         unresolved="Everything beyond title/summary", scale_discipline_verdict="UNRESOLVED", role="NOT_AUDITED_IN_DEPTH_FUTURE_CANDIDATE"),
]

# --------------------------------------------------------------------------
# Validity threats (prompt section 16), ranked
# --------------------------------------------------------------------------
THREAT_FIELDS = ["rank", "threat", "severity", "mechanism", "mitigation_in_design", "residual_risk"]
THREATS = [
    (1, "Climate/background confounding (aridity, humidity, seasonality) of SUHI", "CRITICAL",
     "Climate jointly structures development timing by region and SUHI via rural-reference moisture/vegetation; C0 alone is inadequate",
     "Nested C0/C1/C2 from existing UCDB reanalysis bioclimatics + Koppen; nighttime primary; alternate-control-set test; leave-region-out", "Moderate: unmeasured coast/humidity/wind"),
    (2, "Rural-reference definition and contamination (SUE generalized reference; irrigation/agriculture/phenology)", "CRITICAL",
     "SUHI is a difference; the reference LST varies independent of the city; reference may include peri-urban or disturbed land",
     "Nighttime primary; secondary outcome with different physics; alternate-reference product (DEA) if a city table exists; city-size and aridity strata", "High: cannot be eliminated with one product"),
    (3, "Urban-boundary / cluster-definition mismatch between UCDB (GHSL) and thermal product (Landscan clusters)", "HIGH",
     "Clusters may merge several UCDB cities or differ in extent; S/H and R then refer to different footprints",
     "Polygon-based mutual one-to-one crosswalk with area-ratio bounds; merged clusters excluded from primary, aggregated in sensitivity; fixed-boundary H matches fixed Landscan extent", "Moderate"),
    (4, "Crosswalk error / selection into the matched sample", "HIGH",
     "Matched cities may be larger, more regular, and better detected by MODIS", "Pre-registered accept/ambiguous/reject rules; report matched vs unmatched balance; no fuzzy-name primary", "Moderate"),
    (5, "Temporal overlap: response window 2003-2018 overlaps H epochs 2005-2015 and precedes S(2020)", "HIGH",
     "No clean temporal-legacy reading; reverse-causal pathways (heat -> development) cannot be excluded",
     "Claim restricted to predictive association/transfer; strict-precedence sensitivity with H up to 2000 and S/H rebased to 2015", "High by construction"),
    (6, "Overlap/redundancy between H and present state S (density, built volume)", "HIGH",
     "H gain may only reflect nonlinear S structure; conversely S3 (built volume) may be a mediator and overcontrol",
     "Pseudo-history-from-S test; redundant-feature test; S1/S2/S3 gradient; H endpoint ratio excluded as in Gate 1", "Moderate"),
    (7, "Spatial autocorrelation and shared regional processing", "HIGH",
     "Neighbouring cities share rural context, overpass geometry, and climate -> inflated pseudo-replication", "Leave-region-out and leave-continent-out; spatial block bootstrap; random-vs-geographic fold comparison", "Moderate"),
    (8, "Regional imbalance (Asia ~57%, Oceania ~0.5%)", "MEDIUM-HIGH",
     "Pooled metrics dominated by Asia; small-region folds noisy", "Per-region reporting; pooled and region-weighted metrics; region-balanced sensitivity", "Moderate"),
    (9, "MODIS retrieval/cloud-sampling artifacts (clear-sky bias, emissivity, view angle)", "MEDIUM-HIGH (daytime), MEDIUM (night)",
     "Clear-sky-only sampling and emissivity assumptions bias SUHI, more in humid cloudy and arid bare-soil cities", "Nighttime primary; secondary outcome shows daytime sensitivity; cloud-prone climate strata", "Moderate"),
    (10, "Vegetation/greenness as mediator (and as part of the reference)", "MEDIUM-HIGH",
     "Urban greenness lies on the pathway H -> morphology/greening -> SUHI; conditioning removes real history signal; rural greenness confounds the reference",
     "Greenness/LULC excluded from primary C; exploratory C2+greenness variant reported as attenuation, never as primary", "Moderate"),
    (11, "Urban size and present density", "MEDIUM-HIGH", "SUHI scales with city size; size correlated with history", "Size in S; city-size stratified sensitivity", "Low-moderate"),
    (12, "MAUP / product-specific city definitions", "MEDIUM", "Different aggregation units change both R and S/H", "Cluster-level aggregation sensitivity; two boundary definitions for H", "Moderate"),
    (13, "Latitude / solar geometry", "MEDIUM", "Day SUHI depends on insolation; seasonal definitions differ with latitude", "Latitude in C0; night primary; absolute latitude interactions via random forest", "Low-moderate"),
    (14, "Elevation", "MEDIUM", "Urban/rural elevation difference and lapse-rate effects on LST", "Elevation in C0; product filters urban-rural elevation difference", "Low"),
    (15, "Coastal effects", "MEDIUM", "Sea breeze and land-water contrast not in UCDB variables used", "Flagged; distance-to-coast not available without new raster; sensitivity via Koppen/region strata only", "Moderate (unmeasured)"),
    (16, "Recent-urbanization stratum cannot be assessed under dynamic boundary", "MEDIUM", "1005-5 matched sample (N=4,739) contains no cities with YOB>1990", "Fixed-boundary H primary on the full sample; dynamic H only as sensitivity", "Low under chosen design"),
]

# --------------------------------------------------------------------------
# Decision
# --------------------------------------------------------------------------
DECISION = {
    "execution_id": "1005-6",
    "gate": "Gate 2A - Thermal Response Design Lock",
    "THERMAL_DESIGN": "PROVISIONAL",
    "primary_R": {
        "label": "annual-mean nighttime SUHI climatology (mean over 2003-2018)",
        "physical_quantity": "annual-mean night-time surface urban-minus-rural land-surface-temperature contrast (degC) for a fixed urban cluster",
        "product_band_expected": "all_nighttime_UHI (YCEO v4 cluster-mean composite) - field name in the city-level file UNRESOLVED",
    },
    "secondary_R": "summer (warm-season) daytime SUHI climatology, 2003-2018 (summer_daytime_UHI expected)",
    "contrast_R": "none locked; optional exploratory 2003-2018 SUHI trend (high sensor/processing confound; not confirmatory). Raw urban LST rejected (raster scale)",
    "primary_dataset": {
        "name": "YCEO Surface Urban Heat Islands, Version 4, 2003-2018 (SEDAC), urban-cluster-mean shapefile",
        "doi": "10.7927/S5M5-ZK14",
        "doi_status": "VERIFIED_MULTI (search snippets); landing page not read directly",
        "authority": "official NASA SEDAC archive; Chakraborty & Lee (2023)",
    },
    "alternate_reference_dataset": {
        "name": "Global Urban Heat Island Intensity Dataset (Yang, Xu, Chakraborty et al. 2024), DEA rural reference",
        "doi": "10.6084/m9.figshare.24821538",
        "status": "identity verified; city-level table and access route UNRESOLVED; used only for rural-reference sensitivity if a city table is confirmed",
        "is_same_dataset_as_primary": False,
    },
    "temporal_design": {
        "response_window": "2003-2018 (fixed product composite)",
        "relation_to_H_T2020": "overlaps H epochs 2005, 2010, 2015; entirely before T=2020 and before S(2020)",
        "interpretation": "predictive-association / transferability only; NO temporal-legacy claim",
        "strict_precedence_sensitivity": "H truncated at <=2000 (rebased to B(2000)); S/H rebased to T=2015",
    },
    "H_design": "fixed-boundary built-up trajectory primary on the full crosswalk-matched UCDB sample; dynamic-boundary (MTUC) H as sensitivity on the 1005-5 matched subsample; boundary-robust coarse descriptors as secondary representation",
    "C_design": {"C0": ["latitude", "longitude", "GE_ELV_AVG_2025"],
                 "C1": "C0 + mean(CL_B01_CUR_2000, CL_B01_CUR_2010) + log mean(CL_B12_CUR_2000, CL_B12_CUR_2010)",
                 "C2": "C1 + mean CL_B04 + mean CL_B15 + Koppen major group (from CL_KOP_CUR_2025)",
                 "excluded_from_primary_as_possible_mediators": ["GR_AVG_GRN_*", "GR_SQM_*", "GR_SHB_*", "GR_CTH_*", "LU_HEC_*"],
                 "excluded_as_socioeconomic_proxies": ["GC_DEV_WIG_2025", "GC_DEV_USR_2025"]},
    "new_raster_acquisition_needed": False,
    "global_raster_required": False,
    "estimated_data_volume": "~4.7 MB zipped city-level shapefile (single report); monthly/yearly cluster packages UNRESOLVED",
    "estimated_city_coverage": "'over 10,000' urban clusters (product claim); matchable UCDB cities UNKNOWN until schema/geometry inspected",
    "why_not_LOCKED": [
        "Shapefile attribute schema, geometry type and cluster identifier were not verified (landing page, documentation PDF and metadata page could not be read: WebFetch blocked)",
        "Not verified that annual/summer/winter day/night cluster means are in the 4.7 MB cluster-level file rather than a separate package",
        "v4 cluster count and post-filter N unresolved (7,374 reported for 2019 version vs 'over 10,000' for v4)",
        "Summer/warm-season definition for tropical clusters and exact rural-pixel/elevation rules unresolved",
        "Response window ends 2018 (before T=2020): only a predictive-association design is possible",
        "Alternate-reference product (Yang 2024) has no verified scriptable/city-table access",
    ],
    "evidence_resolution_step": "Human reads SEDAC documentation PDF + metadata page (documentation only, no research data) and records the file listing/field table; see results/1005-6/download_plan.md Step 0",
    "PI_acquisition_recommendation": "NOT YET",
    "claude_authorized_download": False,
    "causal_claims": "none; observational comparative design",
}

MANIFEST_FIELDS = [
    "file_id", "dataset_key", "source_landing_page", "doi", "original_filename", "expected_format",
    "expected_bytes_approx", "expected_sha256", "local_path", "downloaded_by", "downloaded_at_utc",
    "download_method", "observed_bytes", "observed_sha256", "verify_ok", "verified_columns",
    "documentation_read", "notes",
]
MANIFEST_ROWS = [
    dict(file_id="THERM-001", dataset_key="yceo_suhi_v4",
         source_landing_page="https://sedac.ciesin.columbia.edu/data/set/sdei-yceo-sfc-uhi-v4/data-download",
         doi="10.7927/S5M5-ZK14", original_filename="<TO BE RECORDED: 'UHI (urban cluster means)' shapefile zip>",
         expected_format="zip (shapefile)", expected_bytes_approx="~4.7 MB (single search report; confirm)", expected_sha256="<unknown until downloaded; record the observed value>",
         local_path="data/raw/thermal_response/yceo_suhi_v4/", notes="Primary candidate. Requires NASA Earthdata login. Record the exact filename and size shown on the page."),
    dict(file_id="THERM-002", dataset_key="yceo_suhi_v4",
         source_landing_page="https://sedac.ciesin.columbia.edu/downloads/docs/sdei/sdei-yceo-sfc-uhi-v4-documentation.pdf",
         doi="10.7927/S5M5-ZK14", original_filename="sdei-yceo-sfc-uhi-v4-documentation.pdf", expected_format="pdf (documentation)",
         expected_bytes_approx="small (unverified)", expected_sha256="<unknown>", local_path="data/raw/thermal_response/yceo_suhi_v4/docs/",
         notes="Documentation, read at Step 0 BEFORE any data file. Contents decide LOCKED vs PROVISIONAL."),
    dict(file_id="THERM-003", dataset_key="yceo_suhi_v4",
         source_landing_page="https://sedac.ciesin.columbia.edu/data/set/sdei-yceo-sfc-uhi-v4/data-download",
         doi="10.7927/S5M5-ZK14", original_filename="<TO BE RECORDED: monthly/yearly cluster-mean packages, only if small and needed>",
         expected_format="unknown", expected_bytes_approx="UNRESOLVED", expected_sha256="<unknown>", local_path="data/raw/thermal_response/yceo_suhi_v4/",
         notes="OPTIONAL and exploratory only. Do NOT download pixel GeoTIFFs (hundreds of MB, not needed)."),
]


def _write_csv(path: Path, fields: list[str], rows: list[dict]) -> None:
    with path.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        for r in rows:
            w.writerow({k: r.get(k, "") for k in fields})


def build(out: Path = OUT) -> dict:
    out.mkdir(parents=True, exist_ok=True)
    _write_csv(out / "thermal_candidate_audit.csv", CANDIDATE_FIELDS, CANDIDATES)
    _write_csv(out / "thermal_source_audit.csv", SOURCE_FIELDS, SOURCES)
    _write_csv(out / "validity_threats.csv", THREAT_FIELDS, [dict(zip(THREAT_FIELDS, t)) for t in THREATS])
    _write_csv(out / "data_manifest_template.csv", MANIFEST_FIELDS, MANIFEST_ROWS)
    (out / "thermal_design_decision.json").write_text(json.dumps(DECISION, indent=2, ensure_ascii=False), encoding="utf-8")
    meta = {
        "execution_id": "1005-6",
        "source_prompt": "prompts/prompt1005-6.txt",
        "previous_execution": "1005-5",
        "report": "reports/report1005-6.md",
        "status": "COMPLETED_AWAITING_PI_REVIEW",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "thermal_design": DECISION["THERMAL_DESIGN"],
        "new_research_data_downloaded": False,
        "real_research_data_network_transfers_by_claude": 0,
        "web_inspection": "WebSearch only; WebFetch was blocked for all domains tried (figshare, sciencedirect, osti, developers.google.com, gee-community-catalog, geospatial.yale.edu)",
        "python_version": sys.version,
        "platform": platform.platform(),
        "random_seed": None,
        "notes": "No stochastic computation in this execution; no research data were read or analysed.",
    }
    (out / "run_metadata.json").write_text(json.dumps(meta, indent=2), encoding="utf-8")
    return meta


if __name__ == "__main__":
    build()
    print("wrote design artifacts to", OUT)
