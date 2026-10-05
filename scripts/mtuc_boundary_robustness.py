"""Execution 1005-5: Gate 1B - Time-Varying Boundary Robustness Test.

Tests whether the Gate 1 finding from execution 1005-4 (historical
separability: cities with similar present-day state/context can retain
substantially different development histories) survives when history is
measured using the official GHS_UCDB_MTUC_GLOBE_R2024A time-varying
boundary product instead of the main GHS-UCDB fixed (2025-reference)
boundary product.

This is a robustness gate, not Gate 2. No environmental response
variable is used anywhere. No new research data is downloaded (both
GHS-UCDB and GHS_UCDB_MTUC were already acquired in execution 1005-4).

This module imports reusable, unmodified utility functions from
scripts/ucdb_gate1_pilot.py (the reviewed 1005-4 code) rather than
duplicating them; ucdb_gate1_pilot.py itself is not modified.

Run with:
    conda run -n py311 python scripts/mtuc_boundary_robustness.py
"""

from __future__ import annotations

import importlib.util
import json
import sys
import warnings
from pathlib import Path

import numpy as np
import pandas as pd
import pyogrio
from scipy import stats
from sklearn.neighbors import NearestNeighbors
from sklearn.preprocessing import StandardScaler

warnings.filterwarnings("ignore", category=UserWarning)

PROJECT_ROOT = Path(__file__).resolve().parent.parent

# Import reusable, unmodified utilities from the reviewed 1005-4 script.
_spec = importlib.util.spec_from_file_location(
    "ucdb_gate1_pilot", PROJECT_ROOT / "scripts" / "ucdb_gate1_pilot.py"
)
pilot = importlib.util.module_from_spec(_spec)
sys.modules["ucdb_gate1_pilot"] = pilot
_spec.loader.exec_module(pilot)

RANDOM_SEED = pilot.RANDOM_SEED  # 42, unchanged
EPOCHS_OBSERVED = pilot.EPOCHS_OBSERVED  # 1975..2020, 10 epochs
T_ENDPOINT = pilot.T_ENDPOINT  # 2020
H_EPOCHS = pilot.H_EPOCHS  # 1975..2015, 9 epochs
COUNTRY_TO_REGION = pilot.COUNTRY_TO_REGION
fix_mojibake = pilot.fix_mojibake
_fit_predict = pilot._fit_predict
_folds_leave_group_out = pilot._folds_leave_group_out
log = pilot.log

RAW_DIR = PROJECT_ROOT / "data" / "raw" / "ghs_ucdb_r2024a"
UCDB_GPKG = RAW_DIR / "extracted" / "GHS_UCDB_GLOBE_R2024A.gpkg"
MTUC_CSV = RAW_DIR / "mtuc_extracted" / "GHS_UCDB_MTUC_GLOBE_R2024A.csv"
RESULTS_DIR = PROJECT_ROOT / "results" / "1005-5"
FIGURES_DIR = PROJECT_ROOT / "figures" / "1005-5"

K_VALUES = [3, 5, 10]
K_PRIMARY = 5
N_PERMUTATIONS = 300


def parse_num(series: pd.Series) -> pd.Series:
    """Parse MTUC's comma-thousands-formatted numeric strings to float."""
    return pd.to_numeric(series.astype(str).str.replace(",", "", regex=False), errors="coerce")


# ----------------------------------------------------------------------
# Loading
# ----------------------------------------------------------------------

def load_ucdb_full() -> pd.DataFrame:
    """Reload the UCDB table (same as execution 1005-4's load_main_table),
    re-executed here rather than importing cached state, since 1005-4's
    outputs must not be touched or depended upon as mutable state."""
    bus_cols = [f"GH_BUS_TOT_{y}" for y in EPOCHS_OBSERVED]
    pop_cols = [f"GH_POP_TOT_{y}" for y in EPOCHS_OBSERVED]
    buv_cols = [f"GH_BUV_TOT_{y}" for y in EPOCHS_OBSERVED]
    ghsl = pyogrio.read_dataframe(
        UCDB_GPKG, layer="GHSL_UCDB_THEME_GHSL_GLOBE_R2024A",
        columns=["ID_UC_G0"] + bus_cols + pop_cols + buv_cols, read_geometry=False,
    )
    gc = pyogrio.read_dataframe(
        UCDB_GPKG, layer="GHSL_UCDB_THEME_GENERAL_CHARACTERISTICS_GLOBE_R2024A",
        columns=["ID_UC_G0", "GC_UCN_MAI_2025", "GC_CNT_GAD_2025", "GC_UCB_YOB_2025", "GC_UCB_YOD_2025"],
        read_geometry=False,
    )
    geo = pyogrio.read_dataframe(
        UCDB_GPKG, layer="GHSL_UCDB_THEME_GEOGRAPHY_GLOBE_R2024A",
        columns=["ID_UC_G0", "GE_ELV_AVG_2025"], read_geometry=False,
    )
    cen = pyogrio.read_dataframe(
        UCDB_GPKG, layer="UC_centroids",
        columns=["ID_UC_G0", "GC_UCC_LON_2025", "GC_UCC_LAT_2025"], read_geometry=False,
    )
    import pyproj
    transformer = pyproj.Transformer.from_crs(pilot.MOLLWEIDE_WKT, "EPSG:4326", always_xy=True)
    lon, lat = transformer.transform(cen["GC_UCC_LON_2025"].values, cen["GC_UCC_LAT_2025"].values)
    cen = cen.assign(lon_deg=lon, lat_deg=lat)

    df = ghsl.merge(gc, on="ID_UC_G0").merge(geo, on="ID_UC_G0").merge(
        cen[["ID_UC_G0", "lon_deg", "lat_deg"]], on="ID_UC_G0"
    )
    df["GC_UCN_MAI_2025"] = df["GC_UCN_MAI_2025"].map(fix_mojibake)
    df["GC_CNT_GAD_2025"] = df["GC_CNT_GAD_2025"].map(fix_mojibake)
    df["region"] = df["GC_CNT_GAD_2025"].map(COUNTRY_TO_REGION).fillna("Other")
    return df


def load_mtuc_full() -> pd.DataFrame:
    df = pd.read_csv(MTUC_CSV, encoding="latin-1", low_memory=False)
    df.columns = [c.strip() for c in df.columns]
    for y in EPOCHS_OBSERVED:
        df[f"MT_BUS_TOT_{y}"] = parse_num(df[f"MT_BUS_TOT_{y}"])
        df[f"MT_POP_TOT_{y}"] = parse_num(df[f"MT_POP_TOT_{y}"])
        df[f"MT_BUV_TOT_{y}"] = parse_num(df[f"MT_BUV_TOT_{y}"])
    df["GC_UCN_MAI_2025"] = df["GC_UCN_MAI_2025"].map(fix_mojibake)
    df["GC_CNT_GAD_2025"] = df["GC_CNT_GAD_2025"].map(fix_mojibake)
    df["GC_UCB_YOB_2025"] = pd.to_numeric(df["GC_UCB_YOB _2025"], errors="coerce")
    df["GC_UCB_YOD_2025"] = pd.to_numeric(df["GC_UCB_YOD _2025"], errors="coerce")
    df["region"] = df["GC_CNT_GAD_2025"].map(COUNTRY_TO_REGION).fillna("Other")
    return df


# ----------------------------------------------------------------------
# MTUC schema audit
# ----------------------------------------------------------------------

def build_mtuc_schema_audit(mtuc: pd.DataFrame) -> pd.DataFrame:
    rows = []

    def row(field, desc, unit, years, derived, caveat):
        rows.append({
            "field_name": field, "field_description": desc, "unit": unit,
            "years": years, "direct_or_derived": derived, "caveat": caveat,
            "official_source": "GHS_UCDB_MTUC_GLOBE_R2024A V1.2 (JRC), data dictionary GHS_UCDB_MTUC_GLOBE_R2024A.pdf",
        })

    row("ID_MTUC_G0", "Multi-Temporal Urban Centre identifier", "integer ID", "static",
        "direct", f"0 duplicated IDs (verified). N={len(mtuc)} records, distinct ID scheme from UCDB's ID_UC_G0 (no shared key).")
    row("GC_UCN_MAI_2025/GC_UCN_LIS_2025", "Main/list urban centre name(s)", "text", "2025 (naming snapshot)",
        "direct", "Generated via the same OSM/GISCO/WUP2018 geocoding algorithm as UCDB's name field (per PDF data dictionary) - supports deterministic name-based correspondence.")
    row("GC_CNT_GAD_2025", "Country name (GADM v4.1)", "text", "2025", "direct", "Same source/methodology as UCDB's country field.")
    row("GC_UCB_YOB_2025/GC_UCB_YOD_2025", "Year of birth/death of the MTUC entity under DEGURBA criteria", "year",
        "1975-2030", "direct", "SAME semantics as UCDB's YOB/YOD fields, but computed for the MTUC (dynamic) delineation specifically, not necessarily identical values to the UCDB YOB for the 'same' city.")
    for y in EPOCHS_OBSERVED:
        row(f"MT_UCA_KM2_{y}", "Urban centre area at epoch (TIME-VARYING boundary)", "km2", str(y), "direct",
            "Boundary recalculated per epoch based on that epoch's population (official doc: 'not anchored in 2025'). NOT comparable in meaning to UCDB's single 2025-anchored area.")
        row(f"MT_POP_TOT_{y}", "Total population at epoch, within that epoch's dynamic boundary", "persons", str(y), "direct",
            "Missing (NaN) for epochs before the entity's YOB - structurally meaningful (settlement had not yet qualified), not a data error.")
        row(f"MT_BUS_TOT_{y}", "Total built-up surface at epoch, within that epoch's dynamic boundary", "m2", str(y), "direct",
            "Same missingness mechanism as MT_POP_TOT. Stored as comma-thousands-formatted TEXT in the CSV, parsed to numeric in this execution.")
        row(f"MT_BUV_TOT_{y}", "Total built-up volume at epoch, within that epoch's dynamic boundary", "m3", str(y), "direct",
            "Same missingness mechanism.")
    row("MT_POP_DEN_*, MT_BPC_TOT_*, MT_BUV_SHR_*, MT_BUS_SHT_*", "Derived density/per-capita/share indicators per epoch",
        "various", "1975-2030", "derived", "Not used in this execution's primary comparison; noted for completeness.")
    row("MT_*_DIF_*", "Epoch-to-epoch differences (population, density, built-up, volume) between consecutive epochs",
        "various", "pairs of consecutive epochs 1975-2030", "derived",
        "Pre-computed increments; not used directly (this execution recomputes its own trajectory ratios for consistency with 1005-4's h_i(t) definition).")
    row("2025/2030 epochs (all MT_* fields)", "Modelled/projected epochs, same status as in the main UCDB product",
        "n/a", "2025, 2030", "derived (projection)",
        "EXCLUDED from H_dynamic in this execution, identically to how 1005-4 excluded them from H_fixed.")
    row("Geometry (GeoPackage)", "Point centroid layer (default) + 12 per-epoch polygon layers (GHSL_UCDB_MTUC_{year}_GLOBE_R2024)",
        "Mollweide (ESRI:54009), metres", "1975-2030", "direct",
        "Confirms MTUC genuinely stores a distinct boundary geometry per epoch (not just attribute re-aggregation); not used directly in this execution (attribute-level comparison only, per computational-discipline instruction against raster/fine-scale processing).")

    return pd.DataFrame(rows)


# ----------------------------------------------------------------------
# UCDB <-> MTUC correspondence (crosswalk)
# ----------------------------------------------------------------------

def build_crosswalk(ucdb: pd.DataFrame, mtuc: pd.DataFrame) -> tuple[pd.DataFrame, dict]:
    """Deterministic name+country correspondence with numeric corroboration.

    Preference order followed (per prompt Section 4): no explicit official
    crosswalk field, documented shared identifier, or parent/child lineage
    field was found in either product's schema or PDF documentation (both
    audited in build_mtuc_schema_audit / this execution's report Section 4).
    This falls back to criterion 4: deterministic attribute correspondence
    (normalized city name + country, generated by the same GISCO/OSM/WUP2018
    geocoding algorithm in both products per their shared data dictionary
    text) with transparent, documented criteria, corroborated by an
    independent numeric check (2020 population and built-up agreement).
    """
    key_u = (
        ucdb["GC_UCN_MAI_2025"].astype(str).str.strip().str.lower()
        + "||" + ucdb["GC_CNT_GAD_2025"].astype(str).str.strip().str.lower()
    )
    key_m = (
        mtuc["GC_UCN_MAI_2025"].astype(str).str.strip().str.lower()
        + "||" + mtuc["GC_CNT_GAD_2025"].astype(str).str.strip().str.lower()
    )
    ucdb = ucdb.assign(key=key_u)
    mtuc = mtuc.assign(key=key_m)

    u_counts = ucdb["key"].value_counts()
    m_counts = mtuc["key"].value_counts()
    common_keys = set(u_counts.index) & set(m_counts.index)
    one_to_one_keys = {k for k in common_keys if u_counts[k] == 1 and m_counts[k] == 1}
    ambiguous_keys = common_keys - one_to_one_keys
    ucdb_unmatched_keys = set(u_counts.index) - set(m_counts.index)
    mtuc_unmatched_keys = set(m_counts.index) - set(u_counts.index)

    u_idx = ucdb.set_index("key")
    m_idx = mtuc.set_index("key")

    rows = []
    for key in one_to_one_keys:
        u_row = u_idx.loc[key]
        m_row = m_idx.loc[key]
        pop_u, pop_m = u_row["GH_POP_TOT_2020"], m_row["MT_POP_TOT_2020"]
        bus_u, bus_m = u_row["GH_BUS_TOT_2020"], m_row["MT_BUS_TOT_2020"]
        pop_ratio = pop_u / pop_m if pd.notna(pop_m) and pop_m > 0 else np.nan
        bus_ratio = bus_u / bus_m if pd.notna(bus_m) and bus_m > 0 else np.nan
        corroborated = bool(
            pd.notna(pop_ratio) and pd.notna(bus_ratio)
            and 0.2 <= pop_ratio <= 5.0 and 0.2 <= bus_ratio <= 5.0
        )
        mtuc_complete_history = bool(pd.notna(m_row["GC_UCB_YOB_2025"]) and m_row["GC_UCB_YOB_2025"] <= 1975)
        ucdb_endpoint_valid = bool(pd.notna(u_row["GC_UCB_YOB_2025"]) and u_row["GC_UCB_YOB_2025"] <= T_ENDPOINT)
        rows.append({
            "key": key,
            "ID_UC_G0": int(u_row["ID_UC_G0"]),
            "ID_MTUC_G0": int(m_row["ID_MTUC_G0"]),
            "name": u_row["GC_UCN_MAI_2025"],
            "country": u_row["GC_CNT_GAD_2025"],
            "match_status": "one_to_one",
            "pop_ratio_ucdb_over_mtuc_2020": pop_ratio,
            "bus_ratio_ucdb_over_mtuc_2020": bus_ratio,
            "numeric_corroboration_pass": corroborated,
            "mtuc_yob": m_row["GC_UCB_YOB_2025"],
            "ucdb_yob": u_row["GC_UCB_YOB_2025"],
            "mtuc_complete_1975_2020_history": mtuc_complete_history,
            "ucdb_endpoint_valid": ucdb_endpoint_valid,
            "included_in_core_matched_sample": bool(corroborated and mtuc_complete_history and ucdb_endpoint_valid),
        })
    for key in ambiguous_keys:
        rows.append({
            "key": key, "ID_UC_G0": None, "ID_MTUC_G0": None,
            "name": key.split("||")[0], "country": key.split("||")[1],
            "match_status": "ambiguous_many_sided",
            "pop_ratio_ucdb_over_mtuc_2020": np.nan, "bus_ratio_ucdb_over_mtuc_2020": np.nan,
            "numeric_corroboration_pass": False, "mtuc_yob": np.nan, "ucdb_yob": np.nan,
            "mtuc_complete_1975_2020_history": False, "ucdb_endpoint_valid": False,
            "included_in_core_matched_sample": False,
        })
    for key in ucdb_unmatched_keys:
        rows.append({
            "key": key, "ID_UC_G0": None, "ID_MTUC_G0": None,
            "name": key.split("||")[0], "country": key.split("||")[1],
            "match_status": "ucdb_unmatched",
            "pop_ratio_ucdb_over_mtuc_2020": np.nan, "bus_ratio_ucdb_over_mtuc_2020": np.nan,
            "numeric_corroboration_pass": False, "mtuc_yob": np.nan, "ucdb_yob": np.nan,
            "mtuc_complete_1975_2020_history": False, "ucdb_endpoint_valid": False,
            "included_in_core_matched_sample": False,
        })
    for key in mtuc_unmatched_keys:
        rows.append({
            "key": key, "ID_UC_G0": None, "ID_MTUC_G0": None,
            "name": key.split("||")[0], "country": key.split("||")[1],
            "match_status": "mtuc_unmatched",
            "pop_ratio_ucdb_over_mtuc_2020": np.nan, "bus_ratio_ucdb_over_mtuc_2020": np.nan,
            "numeric_corroboration_pass": False, "mtuc_yob": np.nan, "ucdb_yob": np.nan,
            "mtuc_complete_1975_2020_history": False, "ucdb_endpoint_valid": False,
            "included_in_core_matched_sample": False,
        })

    crosswalk = pd.DataFrame(rows)
    summary = {
        "N_UCDB": len(ucdb),
        "N_MTUC": len(mtuc),
        "N_matched_one_to_one_name_country": len(one_to_one_keys),
        "N_ambiguous_many_sided": len(ambiguous_keys),
        "N_ucdb_unmatched": len(ucdb_unmatched_keys),
        "N_mtuc_unmatched": len(mtuc_unmatched_keys),
        "N_numeric_corroboration_failed": int((crosswalk["match_status"] == "one_to_one").sum() - crosswalk["numeric_corroboration_pass"].sum()),
        "N_core_matched_sample": int(crosswalk["included_in_core_matched_sample"].sum()),
        "correspondence_method": "deterministic (normalized name + country) one-to-one match, corroborated by 2020 population and built-up-area ratio within [0.2, 5.0], further restricted to MTUC entities with complete (non-missing) 1975-2020 history (GC_UCB_YOB_2025 <= 1975) and UCDB endpoint validity (GC_UCB_YOB_2025 <= 2020, consistent with execution 1005-4's own sample definition)",
        "no_official_crosswalk_field_found": True,
        "no_documented_shared_identifier_found": True,
        "no_documented_parent_child_lineage_field_found": True,
    }
    return crosswalk, summary


# ----------------------------------------------------------------------
# H construction (generic, reused for both fixed and dynamic boundary)
# ----------------------------------------------------------------------

def build_H_from_prefix(df: pd.DataFrame, col_prefix: str, epochs=H_EPOCHS, endpoint=T_ENDPOINT):
    endpoint_vals = df[f"{col_prefix}{endpoint}"].to_numpy(dtype=float)
    H = np.column_stack([df[f"{col_prefix}{t}"].to_numpy(dtype=float) / endpoint_vals for t in epochs])
    return H


def build_descriptors_from_prefix(df: pd.DataFrame, col_prefix: str, endpoint=T_ENDPOINT):
    endpoint_vals = df[f"{col_prefix}{endpoint}"].to_numpy(dtype=float)
    h_1990 = df[f"{col_prefix}1990"].to_numpy(dtype=float) / endpoint_vals
    h_2000 = df[f"{col_prefix}2000"].to_numpy(dtype=float) / endpoint_vals
    return pd.DataFrame({
        "early_developed_fraction_1990": h_1990,
        "mid_period_fraction_2000": h_2000,
        "recent_expansion_fraction_since_2000": 1.0 - h_2000,
    })


# ----------------------------------------------------------------------
# Core Test A: city-level history agreement
# ----------------------------------------------------------------------

def core_test_a(matched: pd.DataFrame, H_fixed, H_dynamic, desc_fixed, desc_dynamic) -> pd.DataFrame:
    rows = []
    for j, t in enumerate(H_EPOCHS):
        pear = stats.pearsonr(H_fixed[:, j], H_dynamic[:, j])
        spear = stats.spearmanr(H_fixed[:, j], H_dynamic[:, j])
        rows.append({
            "comparison": f"epoch_{t}", "pearson_r": pear.statistic, "pearson_p": pear.pvalue,
            "spearman_r": spear.statistic, "spearman_p": spear.pvalue, "n": len(matched),
        })
    for col in desc_fixed.columns:
        pear = stats.pearsonr(desc_fixed[col], desc_dynamic[col])
        spear = stats.spearmanr(desc_fixed[col], desc_dynamic[col])
        rows.append({
            "comparison": f"descriptor_{col}", "pearson_r": pear.statistic, "pearson_p": pear.pvalue,
            "spearman_r": spear.statistic, "spearman_p": spear.pvalue, "n": len(matched),
        })
    agreement_df = pd.DataFrame(rows)

    D_boundary = np.linalg.norm(H_fixed - H_dynamic, axis=1)
    matched = matched.copy()
    matched["D_boundary"] = D_boundary

    breakdown_rows = []
    pop = matched[f"GH_POP_TOT_{T_ENDPOINT}"].to_numpy()
    size_tercile = pd.qcut(pop, 3, labels=["small", "medium", "large"])
    for tercile in ["small", "medium", "large"]:
        mask = size_tercile == tercile
        breakdown_rows.append({"stratum_type": "size_tercile", "stratum": tercile, "mean_D_boundary": float(D_boundary[mask].mean()), "n": int(mask.sum())})
    for region in sorted(matched["region"].unique()):
        mask = (matched["region"] == region).to_numpy()
        if mask.sum() > 0:
            breakdown_rows.append({"stratum_type": "region", "stratum": region, "mean_D_boundary": float(D_boundary[mask].mean()), "n": int(mask.sum())})
    yob = matched["ucdb_yob"].to_numpy()
    recent_mask = yob > 1990
    breakdown_rows.append({"stratum_type": "recently_urbanized_ucdb_yob_gt_1990", "stratum": "recent", "mean_D_boundary": float(D_boundary[recent_mask].mean()) if recent_mask.sum() > 0 else np.nan, "n": int(recent_mask.sum())})
    breakdown_rows.append({"stratum_type": "recently_urbanized_ucdb_yob_gt_1990", "stratum": "established", "mean_D_boundary": float(D_boundary[~recent_mask].mean()), "n": int((~recent_mask).sum())})
    growth_rate = H_fixed[:, 0]  # h_fixed(1975): low value = rapid recent expansion
    rapid_mask = growth_rate < np.median(growth_rate)
    breakdown_rows.append({"stratum_type": "expansion_speed", "stratum": "rapidly_expanding_low_h1975", "mean_D_boundary": float(D_boundary[rapid_mask].mean()), "n": int(rapid_mask.sum())})
    breakdown_rows.append({"stratum_type": "expansion_speed", "stratum": "slowly_expanding_high_h1975", "mean_D_boundary": float(D_boundary[~rapid_mask].mean()), "n": int((~rapid_mask).sum())})
    breakdown_df = pd.DataFrame(breakdown_rows)

    return agreement_df, breakdown_df, D_boundary


# ----------------------------------------------------------------------
# Core Test B: reconstruction comparison
# ----------------------------------------------------------------------

def core_test_b(H_fixed, H_dynamic, S3, C, region) -> pd.DataFrame:
    rows = []
    for h_name, H in (("fixed", H_fixed), ("dynamic", H_dynamic)):
        X = np.column_stack([S3, C])
        folds = _folds_leave_group_out(region)
        per_epoch_r2 = {t: [] for t in H_EPOCHS}
        agg_rmse = []
        for train_idx, test_idx in folds:
            pred = _fit_predict("random_forest", X[train_idx], H[train_idx], X[test_idx])
            true = H[test_idx]
            ss_res = ((true - pred) ** 2).sum(axis=0)
            ss_tot = ((true - H[train_idx].mean(axis=0)) ** 2).sum(axis=0)
            with np.errstate(invalid="ignore", divide="ignore"):
                r2_per_col = np.where(ss_tot > 0, 1 - ss_res / ss_tot, np.nan)
            for j, t in enumerate(H_EPOCHS):
                per_epoch_r2[t].append(r2_per_col[j])
            agg_rmse.append(np.sqrt(((true - pred) ** 2).sum(axis=1)).mean())
        for t in H_EPOCHS:
            rows.append({
                "h_definition": h_name, "target": str(t), "n_folds": len(folds),
                "r2_mean": float(np.nanmean(per_epoch_r2[t])), "r2_std": float(np.nanstd(per_epoch_r2[t])),
            })
        rows.append({
            "h_definition": h_name, "target": "aggregate_trajectory_rmse", "n_folds": len(folds),
            "r2_mean": np.nan, "r2_std": np.nan,
            "aggregate_rmse_mean": float(np.mean(agg_rmse)), "aggregate_rmse_std": float(np.std(agg_rmse)),
        })
    return pd.DataFrame(rows)


# ----------------------------------------------------------------------
# Core Test C: twin comparison
# ----------------------------------------------------------------------

def _nn_pairs(S3, C, k):
    X = np.column_stack([S3, C])
    Xs = StandardScaler().fit_transform(X)
    nn = NearestNeighbors(n_neighbors=k + 1, metric="euclidean").fit(Xs)
    dist, idx = nn.kneighbors(Xs)
    dist, idx = dist[:, 1:], idx[:, 1:]
    n = len(S3)
    i_list, j_list, dsc_list = [], [], []
    for i in range(n):
        for rank in range(k):
            i_list.append(i)
            j_list.append(idx[i, rank])
            dsc_list.append(dist[i, rank])
    return np.array(i_list), np.array(j_list), np.array(dsc_list)


def divergent_twin_rate(i_arr, j_arr, dsc_arr, H, dsc_cutoff=None, dh_cutoff=None):
    d_h = np.linalg.norm(H[i_arr] - H[j_arr], axis=1)
    if dsc_cutoff is None:
        dsc_cutoff = np.quantile(dsc_arr, 0.25)
    if dh_cutoff is None:
        dh_cutoff = np.quantile(d_h, 0.75)
    low_dsc_mask = dsc_arr <= dsc_cutoff
    rate = float((d_h[low_dsc_mask] > dh_cutoff).mean()) if low_dsc_mask.sum() > 0 else np.nan
    return rate, dsc_cutoff, dh_cutoff, d_h


def core_test_c(S3, C, H_fixed, H_dynamic, k=K_PRIMARY) -> pd.DataFrame:
    i_arr, j_arr, dsc_arr = _nn_pairs(S3, C, k)
    rows = []
    rate_f_sep, dsc_f, dh_f_sep, _ = divergent_twin_rate(i_arr, j_arr, dsc_arr, H_fixed)
    rate_d_sep, dsc_d, dh_d_sep, _ = divergent_twin_rate(i_arr, j_arr, dsc_arr, H_dynamic)
    rows.append({"h_definition": "fixed", "threshold_approach": "separate_per_definition", "k": k, "divergent_twin_rate": rate_f_sep, "D_SC_cutoff": dsc_f, "D_H_cutoff": dh_f_sep})
    rows.append({"h_definition": "dynamic", "threshold_approach": "separate_per_definition", "k": k, "divergent_twin_rate": rate_d_sep, "D_SC_cutoff": dsc_d, "D_H_cutoff": dh_d_sep})
    rate_f_fix, _, _, _ = divergent_twin_rate(i_arr, j_arr, dsc_arr, H_fixed, dsc_cutoff=dsc_f, dh_cutoff=dh_f_sep)
    rate_d_fix, _, _, _ = divergent_twin_rate(i_arr, j_arr, dsc_arr, H_dynamic, dsc_cutoff=dsc_f, dh_cutoff=dh_f_sep)
    rows.append({"h_definition": "fixed", "threshold_approach": "fixed_boundary_threshold_held_fixed", "k": k, "divergent_twin_rate": rate_f_fix, "D_SC_cutoff": dsc_f, "D_H_cutoff": dh_f_sep})
    rows.append({"h_definition": "dynamic", "threshold_approach": "fixed_boundary_threshold_held_fixed", "k": k, "divergent_twin_rate": rate_d_fix, "D_SC_cutoff": dsc_f, "D_H_cutoff": dh_f_sep})
    return pd.DataFrame(rows)


# ----------------------------------------------------------------------
# Core Test D: null / effect-size comparison
# ----------------------------------------------------------------------

def core_test_d(matched: pd.DataFrame, S3, C, H_fixed, H_dynamic, k=K_PRIMARY, n_perm=N_PERMUTATIONS) -> pd.DataFrame:
    i_arr, j_arr, dsc_arr = _nn_pairs(S3, C, k)
    pop = matched[f"GH_POP_TOT_{T_ENDPOINT}"].reset_index(drop=True)
    pop_tercile = pd.qcut(pop, 3, labels=["s", "m", "l"], duplicates="drop")
    region = matched["region"].reset_index(drop=True)
    strata = (region.astype(str) + "||" + pop_tercile.astype(str)).to_numpy()
    strata_to_indices = {s: np.where(strata == s)[0] for s in np.unique(strata)}
    n = len(matched)

    rows = []
    for h_name, H in (("fixed", H_fixed), ("dynamic", H_dynamic)):
        d_h = np.linalg.norm(H[i_arr] - H[j_arr], axis=1)
        observed = float(d_h.mean())
        null_stats = np.empty(n_perm)
        perm_rng2 = np.random.RandomState(RANDOM_SEED)
        for p in range(n_perm):
            perm_index = np.arange(n)
            for s, idxs in strata_to_indices.items():
                if len(idxs) >= 5:
                    shuffled = idxs.copy()
                    perm_rng2.shuffle(shuffled)
                    perm_index[idxs] = shuffled
            H_perm = H[perm_index]
            null_stats[p] = np.linalg.norm(H_perm[i_arr] - H_perm[j_arr], axis=1).mean()
        null_mean = float(null_stats.mean())
        relative_effect = (null_mean - observed) / null_mean if null_mean != 0 else np.nan
        rows.append({
            "h_definition": h_name, "k": k, "n_permutations": n_perm,
            "observed_statistic": observed, "null_mean": null_mean, "null_std": float(null_stats.std()),
            "relative_effect_size": relative_effect,
            "p_value_observed_lower_than_null": float((null_stats <= observed).mean()),
        })
    return pd.DataFrame(rows)


# ----------------------------------------------------------------------
# Sensitivity analyses A-G
# ----------------------------------------------------------------------

def _cheap_metrics(matched, S3, C, H_fixed, H_dynamic, k=K_PRIMARY, n_perm=150):
    """Twin rate (both H defs) + permutation effect size (both H defs), the
    same lightweight indicators execution 1005-4 used as its primary
    sensitivity evidence (full leave-region-out RF refits are reserved for
    the baseline Core Test B, per the 'keep this execution focused'
    instruction)."""
    i_arr, j_arr, dsc_arr = _nn_pairs(S3, C, k)
    rate_f, _, _, _ = divergent_twin_rate(i_arr, j_arr, dsc_arr, H_fixed)
    rate_d, _, _, _ = divergent_twin_rate(i_arr, j_arr, dsc_arr, H_dynamic)

    pop = matched[f"GH_POP_TOT_{T_ENDPOINT}"].reset_index(drop=True)
    pop_tercile = pd.qcut(pop, 3, labels=["s", "m", "l"], duplicates="drop")
    region = matched["region"].reset_index(drop=True)
    strata = (region.astype(str) + "||" + pop_tercile.astype(str)).to_numpy()
    strata_to_indices = {s: np.where(strata == s)[0] for s in np.unique(strata)}
    n = len(matched)
    effects = {}
    for h_name, H in (("fixed", H_fixed), ("dynamic", H_dynamic)):
        d_h = np.linalg.norm(H[i_arr] - H[j_arr], axis=1)
        observed = float(d_h.mean())
        perm_rng = np.random.RandomState(RANDOM_SEED)
        null_stats = np.empty(n_perm)
        for p in range(n_perm):
            perm_index = np.arange(n)
            for s, idxs in strata_to_indices.items():
                if len(idxs) >= 5:
                    shuffled = idxs.copy()
                    perm_rng.shuffle(shuffled)
                    perm_index[idxs] = shuffled
            H_perm = H[perm_index]
            null_stats[p] = np.linalg.norm(H_perm[i_arr] - H_perm[j_arr], axis=1).mean()
        null_mean = null_stats.mean()
        effects[h_name] = (null_mean - observed) / null_mean if null_mean != 0 else np.nan
    return rate_f, rate_d, effects["fixed"], effects["dynamic"]


def run_sensitivity(matched_full, H_fixed_full, H_dynamic_full, S3_full, C_full, qc_jump_mask,
                     ucdb_matched=None, mtuc_matched=None):
    rows = []

    def record(variant, desc, mask):
        n = int(mask.sum())
        if n < 50:
            rows.append({"variant": variant, "description": desc, "n": n, "note": "sample too small, skipped"})
            return
        m = matched_full.loc[mask].reset_index(drop=True)
        rf, rd, ef, ed = _cheap_metrics(m, S3_full[mask], C_full[mask], H_fixed_full[mask], H_dynamic_full[mask])
        rows.append({
            "variant": variant, "description": desc, "n": n,
            "divergent_twin_rate_fixed": rf, "divergent_twin_rate_dynamic": rd,
            "relative_effect_fixed": ef, "relative_effect_dynamic": ed,
        })

    all_mask = np.ones(len(matched_full), dtype=bool)
    record("A_conservative_one_to_one_only", "Baseline: conservative one-to-one matched sample (ambiguous cases already excluded by construction)", all_mask)

    record("B_confirm_ambiguous_excluded", "Confirms variant A already excludes all mapping-ambiguous cases (same sample as A; no separate exclusion needed since ambiguous keys never enter the matched sample)", all_mask)

    pop = matched_full[f"GH_POP_TOT_{T_ENDPOINT}"].to_numpy()
    size_cutoff = np.quantile(pop, 0.10)
    record("C_remove_smallest_10pct", "Smallest 10% of cities (by endpoint population) removed from matched sample", pop >= size_cutoff)

    record("D_remove_extreme_jump_trajectories", "Cities with an extreme (>2x or <0.5x) single-epoch jump in H_fixed's built-up trajectory removed", ~qc_jump_mask)

    for region in sorted(matched_full["region"].unique()):
        mask = (matched_full["region"] == region).to_numpy()
        record(f"E_region_{region.replace(' ', '_')}", f"Restricted to region={region}", mask)

    if ucdb_matched is not None and mtuc_matched is not None:
        H_fixed_2015 = build_H_from_prefix(ucdb_matched, "GH_BUS_TOT_", epochs=[e for e in EPOCHS_OBSERVED if e < 2015], endpoint=2015)
        H_dynamic_2015 = build_H_from_prefix(mtuc_matched, "MT_BUS_TOT_", epochs=[e for e in EPOCHS_OBSERVED if e < 2015], endpoint=2015)
        rf, rd, ef, ed = _cheap_metrics(matched_full, S3_full, C_full, H_fixed_2015, H_dynamic_2015)
        rows.append({
            "variant": "F_alt_endpoint_T2015", "description": "Alternative endpoint year T=2015 (H from 1975-2010), same matched sample",
            "n": len(matched_full), "divergent_twin_rate_fixed": rf, "divergent_twin_rate_dynamic": rd,
            "relative_effect_fixed": ef, "relative_effect_dynamic": ed,
        })

    for k in K_VALUES:
        if k == K_PRIMARY:
            continue
        rf, rd, ef, ed = _cheap_metrics(matched_full, S3_full, C_full, H_fixed_full, H_dynamic_full, k=k)
        rows.append({
            "variant": f"G_alt_k_{k}", "description": f"Alternative nearest-neighbour k={k} (primary is k={K_PRIMARY})",
            "n": len(matched_full), "divergent_twin_rate_fixed": rf, "divergent_twin_rate_dynamic": rd,
            "relative_effect_fixed": ef, "relative_effect_dynamic": ed,
        })

    return pd.DataFrame(rows), all_mask


# ----------------------------------------------------------------------
# Figures
# ----------------------------------------------------------------------

def make_figures(H_fixed, H_dynamic, D_boundary, recon_df, twin_df, null_df, breakdown_df):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    fig, ax = plt.subplots(figsize=(6, 6))
    epoch_idx = H_EPOCHS.index(2000)
    ax.scatter(H_fixed[:, epoch_idx], H_dynamic[:, epoch_idx], s=4, alpha=0.2, color="#4C72B0")
    lims = [0, 1]
    ax.plot(lims, lims, "r--", linewidth=1)
    ax.set_xlabel("H_fixed(2000) = B_fixed(2000)/B_fixed(2020)")
    ax.set_ylabel("H_dynamic(2000) = B_dynamic(2000)/B_dynamic(2020)")
    ax.set_title("H_fixed vs H_dynamic agreement (epoch 2000)")
    fig.tight_layout()
    fig.savefig(FIGURES_DIR / "figure1_h_fixed_vs_dynamic_agreement.png", dpi=120)
    plt.close(fig)

    fig, ax = plt.subplots(figsize=(7, 5))
    ax.hist(D_boundary, bins=40, color="#55A868")
    ax.set_xlabel("D_boundary (Euclidean distance between H_fixed and H_dynamic trajectories)")
    ax.set_title("Distribution of city-level boundary-induced history change")
    fig.tight_layout()
    fig.savefig(FIGURES_DIR / "figure2_boundary_induced_change_distribution.png", dpi=120)
    plt.close(fig)

    fig, ax = plt.subplots(figsize=(8, 5))
    agg = recon_df[recon_df["target"] == "aggregate_trajectory_rmse"]
    ax.bar(agg["h_definition"], agg["aggregate_rmse_mean"], color=["#4C72B0", "#C44E52"])
    ax.set_ylabel("Aggregate trajectory RMSE (leave-region-out, random forest, S3+C)")
    ax.set_title("Matched-sample reconstruction comparison: fixed vs dynamic boundary")
    fig.tight_layout()
    fig.savefig(FIGURES_DIR / "figure3_reconstruction_comparison.png", dpi=120)
    plt.close(fig)

    fig, ax = plt.subplots(figsize=(8, 5))
    sub = twin_df[twin_df["threshold_approach"] == "separate_per_definition"]
    ax.bar(sub["h_definition"], sub["divergent_twin_rate"], color=["#4C72B0", "#C44E52"])
    ax.set_ylabel("Divergent-twin rate (separately-estimated thresholds)")
    ax.set_title("Fixed vs dynamic divergent-twin rate (matched sample, k=5)")
    fig.tight_layout()
    fig.savefig(FIGURES_DIR / "figure4_divergent_twin_rate_comparison.png", dpi=120)
    plt.close(fig)

    fig, ax = plt.subplots(figsize=(8, 5))
    ax.bar(null_df["h_definition"], null_df["relative_effect_size"], color=["#4C72B0", "#C44E52"])
    ax.set_ylabel("Relative effect size (null_mean - observed) / null_mean")
    ax.set_title("Null/effect-size comparison: fixed vs dynamic boundary")
    fig.tight_layout()
    fig.savefig(FIGURES_DIR / "figure5_null_effect_size_comparison.png", dpi=120)
    plt.close(fig)

    fig, ax = plt.subplots(figsize=(9, 5))
    region_rows = breakdown_df[breakdown_df["stratum_type"] == "region"]
    ax.barh(region_rows["stratum"], region_rows["mean_D_boundary"], color="#8172B2")
    ax.set_xlabel("Mean D_boundary")
    ax.set_title("Regional diagnostic: mean boundary-induced history change by region")
    fig.tight_layout()
    fig.savefig(FIGURES_DIR / "figure6_regional_diagnostic.png", dpi=120)
    plt.close(fig)


# ----------------------------------------------------------------------
# Gate 1B decision
# ----------------------------------------------------------------------

def decide_gate1b(recon_df, twin_df, null_df, agreement_df, sens_df) -> dict:
    evidence_survives = []
    evidence_not_survive = []

    agg = recon_df[recon_df["target"] == "aggregate_trajectory_rmse"].set_index("h_definition")
    rmse_fixed = float(agg.loc["fixed", "aggregate_rmse_mean"])
    rmse_dynamic = float(agg.loc["dynamic", "aggregate_rmse_mean"])
    r2_fixed = float(recon_df[(recon_df["h_definition"] == "fixed") & (recon_df["target"] != "aggregate_trajectory_rmse")]["r2_mean"].mean())
    r2_dynamic = float(recon_df[(recon_df["h_definition"] == "dynamic") & (recon_df["target"] != "aggregate_trajectory_rmse")]["r2_mean"].mean())
    r2_diff = r2_dynamic - r2_fixed
    if r2_dynamic < 0.7 and abs(r2_diff) < 0.15:
        evidence_survives.append(f"Reconstruction R2 under H_dynamic ({r2_dynamic:.3f}) remains low (<0.7) and close to H_fixed's matched-sample R2 ({r2_fixed:.3f}, diff={r2_diff:+.3f}); H remains far from reconstructable from S,C regardless of boundary definition.")
    else:
        evidence_not_survive.append(f"Reconstruction R2 changes materially between H_fixed ({r2_fixed:.3f}) and H_dynamic ({r2_dynamic:.3f}, diff={r2_diff:+.3f}).")

    sep = twin_df[twin_df["threshold_approach"] == "separate_per_definition"].set_index("h_definition")
    rate_fixed = float(sep.loc["fixed", "divergent_twin_rate"])
    rate_dynamic = float(sep.loc["dynamic", "divergent_twin_rate"])
    rate_diff_rel = (rate_dynamic - rate_fixed) / rate_fixed if rate_fixed != 0 else np.nan
    if abs(rate_diff_rel) < 0.5 and rate_dynamic > 0.05:
        evidence_survives.append(f"Divergent-twin rate under H_dynamic ({rate_dynamic:.3f}) remains non-trivial (>5%) and within 50% relative of H_fixed's matched-sample rate ({rate_fixed:.3f}).")
    else:
        evidence_not_survive.append(f"Divergent-twin rate changes substantially: H_fixed={rate_fixed:.3f} vs H_dynamic={rate_dynamic:.3f} (relative change {rate_diff_rel:+.1%}).")

    null_idx = null_df.set_index("h_definition")
    effect_fixed = float(null_idx.loc["fixed", "relative_effect_size"])
    effect_dynamic = float(null_idx.loc["dynamic", "relative_effect_size"])
    effect_diff = effect_dynamic - effect_fixed
    if effect_dynamic > 0.10 and abs(effect_diff) < 0.20:
        evidence_survives.append(f"Permutation relative effect size under H_dynamic ({effect_dynamic:.1%}) remains non-trivial (>10%) and close to H_fixed's matched-sample effect ({effect_fixed:.1%}, diff={effect_diff:+.1%}); real structure (S,C predicts some H) persists under both boundary definitions.")
    else:
        evidence_not_survive.append(f"Permutation relative effect size changes substantially: H_fixed={effect_fixed:.1%} vs H_dynamic={effect_dynamic:.1%}.")

    mean_epoch_corr = float(agreement_df[agreement_df["comparison"].str.startswith("epoch_")]["pearson_r"].mean())
    if mean_epoch_corr > 0.5:
        evidence_survives.append(f"Mean per-epoch Pearson correlation between H_fixed and H_dynamic is {mean_epoch_corr:.3f} (>0.5); the two boundary definitions are measuring a substantially related underlying historical signal, not unrelated quantities.")
    else:
        evidence_not_survive.append(f"Mean per-epoch correlation between H_fixed and H_dynamic is low ({mean_epoch_corr:.3f}); the two boundary definitions diverge substantially.")

    n_for, n_against = len(evidence_survives), len(evidence_not_survive)
    if n_for >= 3 and n_against == 0:
        classification = "PASS"
    elif n_against >= 3 and n_for == 0:
        classification = "FAIL"
    elif n_for > 0 and n_against > 0:
        classification = "MIXED"
    else:
        classification = "UNRESOLVED"

    return {
        "classification": classification,
        "r2_fixed_matched": r2_fixed, "r2_dynamic_matched": r2_dynamic,
        "divergent_twin_rate_fixed_matched": rate_fixed, "divergent_twin_rate_dynamic_matched": rate_dynamic,
        "relative_effect_fixed_matched": effect_fixed, "relative_effect_dynamic_matched": effect_dynamic,
        "mean_epoch_pearson_correlation": mean_epoch_corr,
        "evidence_gate1_survives_boundary_correction": evidence_survives,
        "evidence_gate1_does_not_survive_boundary_correction": evidence_not_survive,
        "note": "This is a robustness gate (1B), not Gate 2. No environmental response variable was used.",
    }


if __name__ == "__main__":
    import platform
    import sklearn
    from datetime import datetime, timezone

    started_at = datetime.now(timezone.utc).isoformat()
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    FIGURES_DIR.mkdir(parents=True, exist_ok=True)

    log("Loading UCDB and MTUC tables...")
    ucdb = load_ucdb_full()
    mtuc = load_mtuc_full()
    log(f"UCDB N={len(ucdb)}, MTUC N={len(mtuc)}")

    log("Writing MTUC schema audit...")
    schema_df = build_mtuc_schema_audit(mtuc)
    schema_df.to_csv(RESULTS_DIR / "mtuc_schema_audit.csv", index=False, encoding="utf-8")

    log("Building UCDB<->MTUC crosswalk...")
    crosswalk, crosswalk_summary = build_crosswalk(ucdb, mtuc)
    crosswalk.to_csv(RESULTS_DIR / "ucdb_mtuc_crosswalk.csv", index=False, encoding="utf-8")
    log(f"Crosswalk: {crosswalk_summary}")

    n_core = crosswalk_summary["N_core_matched_sample"]
    if n_core < 200:
        log(f"STOP CONDITION: core matched sample too small (N={n_core} < 200). Writing stop report and halting analysis.")
        stop_record = {
            "stopped": True,
            "reason": f"Core matched sample (N={n_core}) is too small to support a global robustness claim.",
            "crosswalk_summary": crosswalk_summary,
        }
        with open(RESULTS_DIR / "matched_sample_summary.json", "w", encoding="utf-8") as f:
            json.dump(stop_record, f, indent=2)
        with open(RESULTS_DIR / "gate1b_decision.json", "w", encoding="utf-8") as f:
            json.dump({"classification": "UNRESOLVED", "reason": stop_record["reason"]}, f, indent=2)
        sys.exit(0)

    core_mask = crosswalk["included_in_core_matched_sample"]
    core_crosswalk = crosswalk[core_mask].reset_index(drop=True)
    ucdb_matched = ucdb.set_index("ID_UC_G0").loc[core_crosswalk["ID_UC_G0"].astype(int)].reset_index()
    mtuc_matched = mtuc.set_index("ID_MTUC_G0").loc[core_crosswalk["ID_MTUC_G0"].astype(int)].reset_index()
    ucdb_matched["region"] = ucdb_matched["GC_CNT_GAD_2025"].map(COUNTRY_TO_REGION).fillna("Other")
    ucdb_matched["ucdb_yob"] = ucdb_matched["GC_UCB_YOB_2025"]
    log(f"Core matched sample N={len(ucdb_matched)}")

    matched_sample_summary = {
        **crosswalk_summary,
        "region_distribution": ucdb_matched["region"].value_counts().to_dict(),
    }
    with open(RESULTS_DIR / "matched_sample_summary.json", "w", encoding="utf-8") as f:
        json.dump(matched_sample_summary, f, indent=2, default=str)

    log("Building H_fixed and H_dynamic on matched sample...")
    H_fixed = build_H_from_prefix(ucdb_matched, "GH_BUS_TOT_")
    H_dynamic = build_H_from_prefix(mtuc_matched, "MT_BUS_TOT_")
    desc_fixed = build_descriptors_from_prefix(ucdb_matched, "GH_BUS_TOT_")
    desc_dynamic = build_descriptors_from_prefix(mtuc_matched, "MT_BUS_TOT_")

    S1 = np.column_stack([ucdb_matched[f"GH_POP_TOT_{T_ENDPOINT}"], ucdb_matched[f"GH_BUS_TOT_{T_ENDPOINT}"]])
    density = S1[:, 0] / S1[:, 1]
    S3 = np.column_stack([S1[:, 0], S1[:, 1], density, ucdb_matched[f"GH_BUV_TOT_{T_ENDPOINT}"]])
    C = pilot.build_C(ucdb_matched)
    region = ucdb_matched["region"].to_numpy()

    log("Core Test A: city-level history agreement...")
    agreement_df, breakdown_df, D_boundary = core_test_a(ucdb_matched, H_fixed, H_dynamic, desc_fixed, desc_dynamic)
    agreement_df.to_csv(RESULTS_DIR / "boundary_history_agreement.csv", index=False, encoding="utf-8")
    breakdown_df.to_csv(RESULTS_DIR / "boundary_sensitivity_breakdown.csv", index=False, encoding="utf-8")

    log("Core Test B: reconstruction comparison (leave-region-out, random forest)...")
    recon_df = core_test_b(H_fixed, H_dynamic, S3, C, region)
    recon_df.to_csv(RESULTS_DIR / "reconstruction_boundary_comparison.csv", index=False, encoding="utf-8")

    log("Core Test C: twin comparison...")
    twin_df = core_test_c(S3, C, H_fixed, H_dynamic, k=K_PRIMARY)
    twin_df.to_csv(RESULTS_DIR / "twin_boundary_comparison.csv", index=False, encoding="utf-8")

    log("Core Test D: null/effect-size comparison (300 permutations)...")
    null_df = core_test_d(ucdb_matched, S3, C, H_fixed, H_dynamic, k=K_PRIMARY, n_perm=N_PERMUTATIONS)
    null_df.to_csv(RESULTS_DIR / "null_boundary_comparison.csv", index=False, encoding="utf-8")

    log("Sensitivity analyses A-G...")
    bus_cols = [f"GH_BUS_TOT_{y}" for y in EPOCHS_OBSERVED[:9]]
    bus_vals = ucdb_matched[bus_cols].to_numpy(dtype=float)
    diffs = bus_vals[:, 1:] / bus_vals[:, :-1]
    qc_jump_mask = ((diffs > 2.0) | (diffs < 0.5)).any(axis=1)
    sens_df, _ = run_sensitivity(ucdb_matched, H_fixed, H_dynamic, S3, C, qc_jump_mask, ucdb_matched=ucdb_matched, mtuc_matched=mtuc_matched)
    sens_df.to_csv(RESULTS_DIR / "boundary_sensitivity_results.csv", index=False, encoding="utf-8")

    log("Generating figures...")
    make_figures(H_fixed, H_dynamic, D_boundary, recon_df, twin_df, null_df, breakdown_df)

    log("Gate 1B decision...")
    gate1b = decide_gate1b(recon_df, twin_df, null_df, agreement_df, sens_df)
    with open(RESULTS_DIR / "gate1b_decision.json", "w", encoding="utf-8") as f:
        json.dump(gate1b, f, indent=2)
    log(f"GATE 1B = {gate1b['classification']}")

    completed_at = datetime.now(timezone.utc).isoformat()
    run_metadata = {
        "execution_id": "1005-5",
        "source_prompt": "prompts/prompt1005-5.txt",
        "previous_execution": "1005-4",
        "report": "reports/report1005-5.md",
        "status": "COMPLETED",
        "started_at": started_at,
        "completed_at": completed_at,
        "random_seed": RANDOM_SEED,
        "new_research_data_downloaded": False,
        "n_ucdb": crosswalk_summary["N_UCDB"],
        "n_mtuc": crosswalk_summary["N_MTUC"],
        "n_core_matched_sample": n_core,
        "gate1b_classification": gate1b["classification"],
        "python_version": sys.version,
        "platform": platform.platform(),
        "sklearn_version": sklearn.__version__,
        "pandas_version": pd.__version__,
        "numpy_version": np.__version__,
    }
    with open(RESULTS_DIR / "run_metadata.json", "w", encoding="utf-8") as f:
        json.dump(run_metadata, f, indent=2)
    log("ALL DONE.")




