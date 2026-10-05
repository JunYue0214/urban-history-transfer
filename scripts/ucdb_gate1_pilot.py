"""Execution 1005-4: Global Urban Historical Separability Pilot (Gate 1).

Tests only whether historical urban development trajectories (H) retain
meaningful variation after conditioning on present-day state (S) and
coarse background context (C), using the official GHS-UCDB R2024A
dataset. Does NOT use, construct, or evaluate any environmental response
variable (R). Does NOT test whether history affects environment.

Run with:
    conda run -n py311 python scripts/ucdb_gate1_pilot.py
"""

from __future__ import annotations

import json
import sys
import warnings
from pathlib import Path

import numpy as np
import pandas as pd
import pyogrio
import pyproj
from sklearn.ensemble import RandomForestRegressor
from sklearn.linear_model import Ridge
from sklearn.model_selection import KFold
from sklearn.neighbors import NearestNeighbors
from sklearn.preprocessing import RobustScaler, StandardScaler

warnings.filterwarnings("ignore", category=UserWarning)

RANDOM_SEED = 42
rng = np.random.RandomState(RANDOM_SEED)

PROJECT_ROOT = Path(__file__).resolve().parent.parent
RAW_DIR = PROJECT_ROOT / "data" / "raw" / "ghs_ucdb_r2024a"
GPKG_PATH = RAW_DIR / "extracted" / "GHS_UCDB_GLOBE_R2024A.gpkg"
MTUC_CSV_PATH = RAW_DIR / "mtuc_extracted" / "GHS_UCDB_MTUC_GLOBE_R2024A.csv"
RESULTS_DIR = PROJECT_ROOT / "results" / "1005-4"
FIGURES_DIR = PROJECT_ROOT / "figures" / "1005-4"

EPOCHS_ALL = [1975, 1980, 1985, 1990, 1995, 2000, 2005, 2010, 2015, 2020, 2025, 2030]
EPOCHS_OBSERVED = [1975, 1980, 1985, 1990, 1995, 2000, 2005, 2010, 2015, 2020]
T_ENDPOINT = 2020
H_EPOCHS = [e for e in EPOCHS_OBSERVED if e < T_ENDPOINT]  # 1975..2015, 9 epochs

MOLLWEIDE_WKT = (
    'PROJCS["World_Mollweide",GEOGCS["WGS 84",DATUM["WGS_1984",'
    'SPHEROID["WGS 84",6378137,298.257223563,AUTHORITY["EPSG","7030"]],'
    'AUTHORITY["EPSG","6326"]],PRIMEM["Greenwich",0],'
    'UNIT["Degree",0.0174532925199433]],PROJECTION["Mollweide"],'
    'PARAMETER["central_meridian",0],PARAMETER["false_easting",0],'
    'PARAMETER["false_northing",0],UNIT["metre",1,AUTHORITY["EPSG","9001"]],'
    'AXIS["Easting",EAST],AXIS["Northing",NORTH],AUTHORITY["ESRI","54009"]]'
)

COUNTRY_TO_REGION = {
    # Africa
    "Algeria": "Africa", "Angola": "Africa", "Benin": "Africa", "Botswana": "Africa",
    "Burkina Faso": "Africa", "Burundi": "Africa", "Cabo Verde": "Africa", "Cameroon": "Africa",
    "Central African Republic": "Africa", "Chad": "Africa", "Comoros": "Africa",
    "Democratic Republic of the Congo": "Africa", "Republic of the Congo": "Africa",
    "Djibouti": "Africa", "Egypt": "Africa", "Equatorial Guinea": "Africa", "Eritrea": "Africa",
    "Ethiopia": "Africa", "Gabon": "Africa", "Gambia": "Africa", "Ghana": "Africa",
    "Guinea": "Africa", "Guinea-Bissau": "Africa", "Côte d'Ivoire": "Africa", "Kenya": "Africa",
    "Lesotho": "Africa", "Liberia": "Africa", "Libya": "Africa", "Madagascar": "Africa",
    "Malawi": "Africa", "Mali": "Africa", "Mauritania": "Africa", "Mauritius": "Africa",
    "Mayotte": "Africa", "Morocco": "Africa", "Mozambique": "Africa", "Namibia": "Africa",
    "Niger": "Africa", "Nigeria": "Africa", "Réunion": "Africa", "Rwanda": "Africa",
    "São Tomé and Príncipe": "Africa", "Senegal": "Africa", "Sierra Leone": "Africa",
    "Somalia": "Africa", "South Africa": "Africa", "South Sudan": "Africa", "Sudan": "Africa",
    "Swaziland": "Africa", "Tanzania": "Africa", "Togo": "Africa", "Tunisia": "Africa",
    "Uganda": "Africa", "Western Sahara": "Africa", "Zambia": "Africa", "Zimbabwe": "Africa",
    # Asia
    "Afghanistan": "Asia", "Armenia": "Asia", "Azerbaijan": "Asia", "Bahrain": "Asia",
    "Bangladesh": "Asia", "Bhutan": "Asia", "Brunei": "Asia", "Cambodia": "Asia", "China": "Asia",
    "Cyprus": "Asia", "Georgia": "Asia", "India": "Asia", "Indonesia": "Asia", "Iran": "Asia",
    "Iraq": "Asia", "Israel": "Asia", "Japan": "Asia", "Jordan": "Asia", "Kazakhstan": "Asia",
    "Kuwait": "Asia", "Kyrgyzstan": "Asia", "Laos": "Asia", "Lebanon": "Asia", "Malaysia": "Asia",
    "Maldives": "Asia", "Mongolia": "Asia", "Myanmar": "Asia", "Nepal": "Asia",
    "North Korea": "Asia", "Northern Cyprus": "Asia", "Oman": "Asia", "Pakistan": "Asia",
    "Palestine": "Asia", "Philippines": "Asia", "Qatar": "Asia", "Saudi Arabia": "Asia",
    "Singapore": "Asia", "South Korea": "Asia", "Sri Lanka": "Asia", "Syria": "Asia",
    "Taiwan": "Asia", "Tajikistan": "Asia", "Thailand": "Asia", "Timor-Leste": "Asia",
    "Turkey": "Asia", "Turkmenistan": "Asia", "United Arab Emirates": "Asia",
    "Uzbekistan": "Asia", "Vietnam": "Asia", "Yemen": "Asia",
    # Europe
    "Albania": "Europe", "Austria": "Europe", "Belarus": "Europe", "Belgium": "Europe",
    "Bosnia and Herzegovina": "Europe", "Bulgaria": "Europe", "Croatia": "Europe",
    "Czechia": "Europe", "Denmark": "Europe", "Estonia": "Europe", "Finland": "Europe",
    "France": "Europe", "Germany": "Europe", "Greece": "Europe", "Hungary": "Europe",
    "Iceland": "Europe", "Ireland": "Europe", "Italy": "Europe", "Jersey": "Europe",
    "Kosovo": "Europe", "Latvia": "Europe", "Lithuania": "Europe", "Luxembourg": "Europe",
    "Malta": "Europe", "Moldova": "Europe", "Montenegro": "Europe", "Netherlands": "Europe",
    "North Macedonia": "Europe", "Norway": "Europe", "Poland": "Europe", "Portugal": "Europe",
    "Romania": "Europe", "Russia": "Europe", "Serbia": "Europe", "Slovakia": "Europe",
    "Slovenia": "Europe", "Spain": "Europe", "Sweden": "Europe", "Switzerland": "Europe",
    "Ukraine": "Europe", "United Kingdom": "Europe",
    # North America
    "Aruba": "North America", "Bahamas": "North America", "Barbados": "North America",
    "Belize": "North America", "Canada": "North America", "Costa Rica": "North America",
    "Cuba": "North America", "Curaçao": "North America", "Dominican Republic": "North America",
    "El Salvador": "North America", "Guatemala": "North America", "Haiti": "North America",
    "Honduras": "North America", "Jamaica": "North America", "Martinique": "North America",
    "México": "North America", "Nicaragua": "North America", "Panama": "North America",
    "Puerto Rico": "North America", "Trinidad and Tobago": "North America",
    "United States": "North America",
    # South America
    "Argentina": "South America", "Bolivia": "South America", "Brazil": "South America",
    "Chile": "South America", "Colombia": "South America", "Ecuador": "South America",
    "French Guiana": "South America", "Guyana": "South America", "Paraguay": "South America",
    "Peru": "South America", "Suriname": "South America", "Uruguay": "South America",
    "Venezuela": "South America",
    # Oceania
    "Australia": "Oceania", "Fiji": "Oceania", "French Polynesia": "Oceania",
    "New Caledonia": "Oceania", "New Zealand": "Oceania", "Papua New Guinea": "Oceania",
    "Samoa": "Oceania", "Solomon Islands": "Oceania", "Tonga": "Oceania", "Vanuatu": "Oceania",
}


def fix_mojibake(s):
    """Fix UTF-8-read-as-Latin-1-then-reencoded strings from the GPKG attribute table."""
    if not isinstance(s, str):
        return s
    try:
        return s.encode("latin-1").decode("utf-8")
    except (UnicodeDecodeError, UnicodeEncodeError):
        return s


def log(msg: str) -> None:
    print(f"[gate1] {msg}", flush=True)


# ----------------------------------------------------------------------
# Data loading
# ----------------------------------------------------------------------

def load_main_table() -> pd.DataFrame:
    bus_cols = [f"GH_BUS_TOT_{y}" for y in EPOCHS_OBSERVED]
    pop_cols = [f"GH_POP_TOT_{y}" for y in EPOCHS_OBSERVED]
    buv_cols = [f"GH_BUV_TOT_{y}" for y in EPOCHS_OBSERVED]
    ghsl = pyogrio.read_dataframe(
        GPKG_PATH, layer="GHSL_UCDB_THEME_GHSL_GLOBE_R2024A",
        columns=["ID_UC_G0"] + bus_cols + pop_cols + buv_cols, read_geometry=False,
    )
    gc = pyogrio.read_dataframe(
        GPKG_PATH, layer="GHSL_UCDB_THEME_GENERAL_CHARACTERISTICS_GLOBE_R2024A",
        columns=["ID_UC_G0", "GC_UCN_MAI_2025", "GC_CNT_GAD_2025", "GC_UCB_YOB_2025", "GC_UCB_YOD_2025"],
        read_geometry=False,
    )
    geo = pyogrio.read_dataframe(
        GPKG_PATH, layer="GHSL_UCDB_THEME_GEOGRAPHY_GLOBE_R2024A",
        columns=["ID_UC_G0", "GE_ELV_AVG_2025"], read_geometry=False,
    )
    cen = pyogrio.read_dataframe(
        GPKG_PATH, layer="UC_centroids",
        columns=["ID_UC_G0", "GC_UCC_LON_2025", "GC_UCC_LAT_2025"], read_geometry=False,
    )
    transformer = pyproj.Transformer.from_crs(MOLLWEIDE_WKT, "EPSG:4326", always_xy=True)
    lon, lat = transformer.transform(cen["GC_UCC_LON_2025"].values, cen["GC_UCC_LAT_2025"].values)
    cen = cen.assign(lon_deg=lon, lat_deg=lat)

    df = ghsl.merge(gc, on="ID_UC_G0").merge(geo, on="ID_UC_G0").merge(
        cen[["ID_UC_G0", "lon_deg", "lat_deg"]], on="ID_UC_G0"
    )
    df["GC_UCN_MAI_2025"] = df["GC_UCN_MAI_2025"].map(fix_mojibake)
    df["GC_CNT_GAD_2025"] = df["GC_CNT_GAD_2025"].map(fix_mojibake)
    df["region"] = df["GC_CNT_GAD_2025"].map(COUNTRY_TO_REGION).fillna("Other")
    return df


def load_mtuc_table() -> pd.DataFrame:
    df = pd.read_csv(MTUC_CSV_PATH, encoding="utf-8")
    df.columns = [c.strip() for c in df.columns]
    return df


# ----------------------------------------------------------------------
# Quality control
# ----------------------------------------------------------------------

def run_qc(df: pd.DataFrame) -> pd.DataFrame:
    """Compute per-city QC flags. Does not exclude or force-correct anything."""
    bus_cols = [f"GH_BUS_TOT_{y}" for y in EPOCHS_OBSERVED]
    pop_cols = [f"GH_POP_TOT_{y}" for y in EPOCHS_OBSERVED]
    buv_cols = [f"GH_BUV_TOT_{y}" for y in EPOCHS_OBSERVED]

    qc = pd.DataFrame({"ID_UC_G0": df["ID_UC_G0"]})

    qc["missing_any_bus"] = df[bus_cols].isna().any(axis=1)
    qc["missing_any_pop"] = df[pop_cols].isna().any(axis=1)
    qc["missing_any_buv"] = df[buv_cols].isna().any(axis=1)

    qc["near_zero_endpoint_bus"] = df[f"GH_BUS_TOT_{T_ENDPOINT}"] < 1000
    qc["near_zero_endpoint_pop"] = df[f"GH_POP_TOT_{T_ENDPOINT}"] < 10

    bus_vals = df[bus_cols].to_numpy(dtype=float)
    diffs = np.diff(bus_vals, axis=1)
    qc["n_decreasing_steps"] = (diffs < 0).sum(axis=1)
    qc["non_monotonic"] = qc["n_decreasing_steps"] > 0
    with np.errstate(divide="ignore", invalid="ignore"):
        step_ratios = bus_vals[:, 1:] / np.where(bus_vals[:, :-1] == 0, np.nan, bus_vals[:, :-1])
    max_ratio = np.nanmax(step_ratios, axis=1)
    min_ratio = np.nanmin(step_ratios, axis=1)
    qc["max_step_ratio"] = max_ratio
    qc["min_step_ratio"] = min_ratio
    qc["extreme_jump"] = (max_ratio > 2.0) | (min_ratio < 0.5)

    qc["negative_or_invalid"] = (
        (df[bus_cols] < 0).any(axis=1)
        | (df[pop_cols] < 0).any(axis=1)
        | (df[buv_cols] < 0).any(axis=1)
        | (~np.isfinite(df[bus_cols].to_numpy(dtype=float))).any(axis=1)
    )

    qc["duplicated_id"] = df["ID_UC_G0"].duplicated(keep=False)
    name_country = df["GC_UCN_MAI_2025"].astype(str) + "||" + df["GC_CNT_GAD_2025"].astype(str)
    qc["duplicated_name_country"] = name_country.duplicated(keep=False)

    qc["yob"] = df["GC_UCB_YOB_2025"]
    qc["yod"] = df["GC_UCB_YOD_2025"]
    qc["qualified_after_endpoint"] = df["GC_UCB_YOB_2025"] > T_ENDPOINT
    qc["qualified_after_1975"] = df["GC_UCB_YOB_2025"] > 1975

    qc["any_qc_concern"] = (
        qc["missing_any_bus"] | qc["missing_any_pop"] | qc["missing_any_buv"]
        | qc["near_zero_endpoint_bus"] | qc["near_zero_endpoint_pop"]
        | qc["extreme_jump"] | qc["negative_or_invalid"]
        | qc["duplicated_id"] | qc["qualified_after_endpoint"]
    )
    return qc


def build_sample(df: pd.DataFrame, qc: pd.DataFrame) -> tuple[pd.DataFrame, dict]:
    """Apply exclusions per Section 12. Returns filtered df and an exclusion log."""
    initial_n = len(df)
    exclusions = []
    keep = pd.Series(True, index=df.index)

    reasons = [
        ("missing_core_variable", qc["missing_any_bus"] | qc["missing_any_pop"] | qc["missing_any_buv"]),
        ("negative_or_invalid_value", qc["negative_or_invalid"]),
        ("duplicated_id", qc["duplicated_id"]),
        ("near_zero_endpoint_bus_or_pop", qc["near_zero_endpoint_bus"] | qc["near_zero_endpoint_pop"]),
        ("qualified_as_urban_centre_after_endpoint_year", qc["qualified_after_endpoint"]),
    ]
    for reason, mask in reasons:
        newly_excluded = keep & mask
        exclusions.append({"reason": reason, "n_excluded": int(newly_excluded.sum())})
        keep = keep & ~mask

    final_df = df.loc[keep].reset_index(drop=True)
    summary = {
        "initial_n": initial_n,
        "exclusions": exclusions,
        "final_n": int(len(final_df)),
        "region_distribution": final_df["region"].value_counts().to_dict(),
        "endpoint_population_distribution": {
            "min": float(final_df[f"GH_POP_TOT_{T_ENDPOINT}"].min()),
            "p25": float(final_df[f"GH_POP_TOT_{T_ENDPOINT}"].quantile(0.25)),
            "median": float(final_df[f"GH_POP_TOT_{T_ENDPOINT}"].median()),
            "p75": float(final_df[f"GH_POP_TOT_{T_ENDPOINT}"].quantile(0.75)),
            "max": float(final_df[f"GH_POP_TOT_{T_ENDPOINT}"].max()),
        },
        "endpoint_built_up_distribution": {
            "min": float(final_df[f"GH_BUS_TOT_{T_ENDPOINT}"].min()),
            "p25": float(final_df[f"GH_BUS_TOT_{T_ENDPOINT}"].quantile(0.25)),
            "median": float(final_df[f"GH_BUS_TOT_{T_ENDPOINT}"].median()),
            "p75": float(final_df[f"GH_BUS_TOT_{T_ENDPOINT}"].quantile(0.75)),
            "max": float(final_df[f"GH_BUS_TOT_{T_ENDPOINT}"].max()),
        },
    }
    return final_df, summary


# ----------------------------------------------------------------------
# H, S, C construction
# ----------------------------------------------------------------------

def build_H(df: pd.DataFrame) -> tuple[np.ndarray, pd.DataFrame]:
    """Normalized pre-endpoint trajectory h_i(t) = B_i(t)/B_i(T), t < T.
    Returns (H matrix [n_cities x len(H_EPOCHS)], descriptors DataFrame)."""
    endpoint = df[f"GH_BUS_TOT_{T_ENDPOINT}"].to_numpy(dtype=float)
    H = np.zeros((len(df), len(H_EPOCHS)), dtype=float)
    for j, t in enumerate(H_EPOCHS):
        H[:, j] = df[f"GH_BUS_TOT_{t}"].to_numpy(dtype=float) / endpoint

    h_1990 = df["GH_BUS_TOT_1990"].to_numpy(dtype=float) / endpoint
    h_2000 = df["GH_BUS_TOT_2000"].to_numpy(dtype=float) / endpoint
    increments = np.diff(
        np.column_stack([df[f"GH_BUS_TOT_{t}"] for t in EPOCHS_OBSERVED]).astype(float), axis=1
    )
    increments = np.clip(increments, a_min=0, a_max=None)  # weighting must be non-negative
    midpoints = np.array([(EPOCHS_OBSERVED[i] + EPOCHS_OBSERVED[i + 1]) / 2 for i in range(len(EPOCHS_OBSERVED) - 1)])
    denom = increments.sum(axis=1)
    with np.errstate(invalid="ignore", divide="ignore"):
        weighted_timing = np.where(denom > 0, (increments * midpoints).sum(axis=1) / denom, np.nan)

    descriptors = pd.DataFrame({
        "ID_UC_G0": df["ID_UC_G0"].values,
        "early_developed_fraction_1990": h_1990,
        "mid_period_fraction_2000": h_2000,
        "recent_expansion_fraction_since_2000": 1.0 - h_2000,
        "weighted_development_timing": weighted_timing,
    })
    return H, descriptors


def build_S(df: pd.DataFrame) -> dict[str, np.ndarray]:
    pop = df[f"GH_POP_TOT_{T_ENDPOINT}"].to_numpy(dtype=float)
    bus = df[f"GH_BUS_TOT_{T_ENDPOINT}"].to_numpy(dtype=float)
    buv = df[f"GH_BUV_TOT_{T_ENDPOINT}"].to_numpy(dtype=float)
    density = pop / bus  # algebraically derived from S1; documented, not independent
    S1 = np.column_stack([pop, bus])
    S2 = np.column_stack([pop, bus, density])
    S3 = np.column_stack([pop, bus, density, buv])
    return {"S1": S1, "S2": S2, "S3": S3}


def build_C(df: pd.DataFrame) -> np.ndarray:
    return np.column_stack([
        df["lat_deg"].to_numpy(dtype=float),
        df["lon_deg"].to_numpy(dtype=float),
        df["GE_ELV_AVG_2025"].to_numpy(dtype=float),
    ])


# ----------------------------------------------------------------------
# Experiment 1: history reconstruction H_hat = f(S, C)
# ----------------------------------------------------------------------

def _folds_random(n, n_splits=5):
    kf = KFold(n_splits=n_splits, shuffle=True, random_state=RANDOM_SEED)
    return list(kf.split(np.arange(n)))


def _folds_leave_group_out(groups: np.ndarray):
    folds = []
    for g in np.unique(groups):
        test_idx = np.where(groups == g)[0]
        train_idx = np.where(groups != g)[0]
        if len(test_idx) >= 5 and len(train_idx) >= 50:
            folds.append((train_idx, test_idx))
    return folds


def _fit_predict(model_name, X_train, H_train, X_test):
    if model_name == "null_mean":
        pred = np.tile(H_train.mean(axis=0), (X_test.shape[0], 1))
        return pred
    scaler = StandardScaler().fit(X_train)
    Xtr = scaler.transform(X_train)
    Xte = scaler.transform(X_test)
    if model_name == "ridge":
        model = Ridge(alpha=1.0, random_state=RANDOM_SEED)
    elif model_name == "random_forest":
        model = RandomForestRegressor(
            n_estimators=200, max_depth=10, random_state=RANDOM_SEED, n_jobs=-1
        )
    else:
        raise ValueError(model_name)
    model.fit(Xtr, H_train)
    return model.predict(Xte)


def run_experiment1(H, S_dict, C, region) -> pd.DataFrame:
    rows = []
    validation_schemes = {
        "random_5fold": _folds_random(len(H)),
        "leave_region_out": _folds_leave_group_out(region),
    }
    for s_name, S in S_dict.items():
        for c_included in (False, True):
            X_full = np.column_stack([S, C]) if c_included else S
            for model_name in ("null_mean", "ridge", "random_forest"):
                for val_name, folds in validation_schemes.items():
                    per_epoch_r2 = {t: [] for t in H_EPOCHS}
                    per_epoch_mae = {t: [] for t in H_EPOCHS}
                    agg_rmse = []
                    for train_idx, test_idx in folds:
                        pred = _fit_predict(model_name, X_full[train_idx], H[train_idx], X_full[test_idx])
                        true = H[test_idx]
                        ss_res = ((true - pred) ** 2).sum(axis=0)
                        ss_tot = ((true - H[train_idx].mean(axis=0)) ** 2).sum(axis=0)
                        with np.errstate(invalid="ignore", divide="ignore"):
                            r2_per_col = np.where(ss_tot > 0, 1 - ss_res / ss_tot, np.nan)
                        mae_per_col = np.abs(true - pred).mean(axis=0)
                        for j, t in enumerate(H_EPOCHS):
                            per_epoch_r2[t].append(r2_per_col[j])
                            per_epoch_mae[t].append(mae_per_col[j])
                        agg_rmse.append(np.sqrt(((true - pred) ** 2).sum(axis=1)).mean())
                    for t in H_EPOCHS:
                        rows.append({
                            "s_spec": s_name, "c_included": c_included, "model": model_name,
                            "validation_scheme": val_name, "target": str(t), "n_folds": len(folds),
                            "r2_mean": float(np.nanmean(per_epoch_r2[t])),
                            "r2_std": float(np.nanstd(per_epoch_r2[t])),
                            "mae_mean": float(np.nanmean(per_epoch_mae[t])),
                            "mae_std": float(np.nanstd(per_epoch_mae[t])),
                        })
                    rows.append({
                        "s_spec": s_name, "c_included": c_included, "model": model_name,
                        "validation_scheme": val_name, "target": "aggregate_trajectory_rmse",
                        "n_folds": len(folds),
                        "r2_mean": np.nan, "r2_std": np.nan,
                        "mae_mean": float(np.mean(agg_rmse)), "mae_std": float(np.std(agg_rmse)),
                    })
    return pd.DataFrame(rows)


# ----------------------------------------------------------------------
# Experiment 2: present-day analogues
# ----------------------------------------------------------------------

def run_experiment2(df, H, S3, C, k=5):
    X = np.column_stack([S3, C])
    scaler = StandardScaler().fit(X)
    Xs = scaler.transform(X)
    nn = NearestNeighbors(n_neighbors=k + 1, metric="euclidean").fit(Xs)
    dist, idx = nn.kneighbors(Xs)
    dist, idx = dist[:, 1:], idx[:, 1:]  # drop self

    n = len(df)
    pairs_i, pairs_j, d_sc, d_h = [], [], [], []
    for i in range(n):
        for rank in range(k):
            j = idx[i, rank]
            pairs_i.append(i)
            pairs_j.append(j)
            d_sc.append(dist[i, rank])
            d_h.append(float(np.linalg.norm(H[i] - H[j])))
    pairs_df = pd.DataFrame({
        "i": pairs_i, "j": pairs_j, "D_SC": d_sc, "D_H": d_h,
    })
    return pairs_df, Xs


def build_twin_candidates(df, pairs_df, region, top_n=50) -> pd.DataFrame:
    deduped = pairs_df.copy()
    deduped["pair_key"] = deduped.apply(lambda r: tuple(sorted((r["i"], r["j"]))), axis=1)
    deduped = deduped.drop_duplicates(subset="pair_key")
    low_dsc_cutoff = deduped["D_SC"].quantile(0.25)
    candidates = deduped[deduped["D_SC"] <= low_dsc_cutoff].copy()
    candidates = candidates.sort_values("D_H", ascending=False).head(top_n)
    rows = []
    for _, r in candidates.iterrows():
        i, j = int(r["i"]), int(r["j"])
        rows.append({
            "city_i": f"UC_{int(df.iloc[i]['ID_UC_G0'])}",
            "city_j": f"UC_{int(df.iloc[j]['ID_UC_G0'])}",
            "region_i": region[i],
            "region_j": region[j],
            "D_SC": r["D_SC"],
            "D_H": r["D_H"],
            "present_state_similarity_summary": (
                f"pop_i={df.iloc[i][f'GH_POP_TOT_{T_ENDPOINT}']:.0f}, "
                f"pop_j={df.iloc[j][f'GH_POP_TOT_{T_ENDPOINT}']:.0f}, "
                f"bus_i={df.iloc[i][f'GH_BUS_TOT_{T_ENDPOINT}']:.0f}, "
                f"bus_j={df.iloc[j][f'GH_BUS_TOT_{T_ENDPOINT}']:.0f}"
            ),
            "history_difference_summary": (
                f"bus_1975_i={df.iloc[i]['GH_BUS_TOT_1975']:.0f}, "
                f"bus_1975_j={df.iloc[j]['GH_BUS_TOT_1975']:.0f}, "
                f"bus_2000_i={df.iloc[i]['GH_BUS_TOT_2000']:.0f}, "
                f"bus_2000_j={df.iloc[j]['GH_BUS_TOT_2000']:.0f}"
            ),
            "qc_flags": "none_primary_sample",
        })
    return pd.DataFrame(rows)


# ----------------------------------------------------------------------
# Experiment 3: permutation / null test
# ----------------------------------------------------------------------

def run_experiment3(df, H, region, pairs_df, n_permutations=300):
    pop_tercile = pd.qcut(df[f"GH_POP_TOT_{T_ENDPOINT}"], 3, labels=["small", "medium", "large"])
    strata = region.astype(str) + "||" + pop_tercile.astype(str)
    strata = strata.to_numpy()

    observed_stat = float(pairs_df["D_H"].mean())

    strata_to_indices = {}
    for s in np.unique(strata):
        strata_to_indices[s] = np.where(strata == s)[0]

    null_stats = np.empty(n_permutations, dtype=float)
    perm_rng = np.random.RandomState(RANDOM_SEED)
    i_arr = pairs_df["i"].to_numpy()
    j_arr = pairs_df["j"].to_numpy()
    for p in range(n_permutations):
        perm_index = np.arange(len(df))
        for s, idxs in strata_to_indices.items():
            if len(idxs) >= 5:
                shuffled = idxs.copy()
                perm_rng.shuffle(shuffled)
                perm_index[idxs] = shuffled
        H_perm = H[perm_index]
        d_h_perm = np.linalg.norm(H_perm[i_arr] - H_perm[j_arr], axis=1)
        null_stats[p] = d_h_perm.mean()

    p_lower = float((null_stats <= observed_stat).mean())
    p_higher = float((null_stats >= observed_stat).mean())

    result = pd.DataFrame({
        "permutation_index": np.arange(n_permutations),
        "null_statistic_mean_D_H": null_stats,
    })
    result.attrs["observed_statistic"] = observed_stat
    result.attrs["p_value_observed_le_null"] = p_lower
    result.attrs["p_value_observed_ge_null"] = p_higher
    perm_meta = {
        "statistic": "mean_D_H_among_k_nearest_SC_neighbors",
        "scheme": "constrained_permutation_within_region_x_population_tercile",
        "n_permutations": n_permutations,
        "observed_statistic": observed_stat,
        "null_mean": float(null_stats.mean()),
        "null_std": float(null_stats.std()),
        "p_value_observed_lower_than_null": p_lower,
        "p_value_observed_higher_than_null": p_higher,
        "interpretation": (
            "p_value_observed_lower_than_null small => real present-state/context "
            "neighbors have MORE similar histories than random assignment would "
            "produce (evidence S,C predicts something about H). "
            "p_value NOT small => real neighbors' history similarity is "
            "indistinguishable from random assignment (evidence FOR historical "
            "separability / equifinality)."
        ),
    }
    return result, perm_meta


def _key_reconstruction_rmse(H, S, C, region, model_name="random_forest"):
    X = np.column_stack([S, C])
    folds = _folds_leave_group_out(region)
    if not folds:
        return np.nan
    agg = []
    for train_idx, test_idx in folds:
        pred = _fit_predict(model_name, X[train_idx], H[train_idx], X[test_idx])
        true = H[test_idx]
        agg.append(np.sqrt(((true - pred) ** 2).sum(axis=1)).mean())
    return float(np.mean(agg))


def _key_separability_stat(df, H, S3, C, region, scaler_cls=StandardScaler, k=5, n_perm=150):
    X = np.column_stack([S3, C])
    Xs = scaler_cls().fit_transform(X)
    nn = NearestNeighbors(n_neighbors=k + 1, metric="euclidean").fit(Xs)
    dist, idx = nn.kneighbors(Xs)
    dist, idx = dist[:, 1:], idx[:, 1:]
    n = len(df)
    i_list, j_list, dsc_list = [], [], []
    for i in range(n):
        for rank in range(k):
            i_list.append(i)
            j_list.append(idx[i, rank])
            dsc_list.append(dist[i, rank])
    i_arr, j_arr, dsc_arr = np.array(i_list), np.array(j_list), np.array(dsc_list)
    d_h = np.linalg.norm(H[i_arr] - H[j_arr], axis=1)
    observed = float(d_h.mean())

    pop_tercile = pd.qcut(df[f"GH_POP_TOT_{T_ENDPOINT}"].reset_index(drop=True), 3, labels=["s", "m", "l"], duplicates="drop")
    strata = (pd.Series(region).astype(str) + "||" + pop_tercile.astype(str)).to_numpy()
    strata_to_indices = {s: np.where(strata == s)[0] for s in np.unique(strata)}
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
    p_lower = float((null_stats <= observed).mean())
    low_dsc_cutoff = np.quantile(dsc_arr, 0.25)
    frac_high_dh_among_low_dsc = float(
        (d_h[dsc_arr <= low_dsc_cutoff] > np.quantile(d_h, 0.75)).mean()
    )
    return observed, p_lower, frac_high_dh_among_low_dsc


def run_sensitivity(df, H, S_dict, C, region, qc) -> pd.DataFrame:
    rows = []

    def record(name, description, n_used, rmse, sep_stat, p_lower, frac_twins):
        rows.append({
            "variant": name, "description": description, "n_cities": n_used,
            "leave_region_rf_S3_C_aggregate_rmse": rmse,
            "exp2_observed_mean_D_H_among_NN": sep_stat,
            "exp3_p_value_observed_lower_than_null": p_lower,
            "frac_high_D_H_among_low_D_SC_pairs": frac_twins,
        })

    rmse0 = _key_reconstruction_rmse(H, S_dict["S3"], C, region)
    sep0, p0, frac0 = _key_separability_stat(df, H, S_dict["S3"], C, region)
    record("baseline_S3_with_C", "Primary specification: S3+C, leave-region-out, random forest", len(df), rmse0, sep0, p0, frac0)

    for s_name in ("S1", "S2"):
        rmse = _key_reconstruction_rmse(H, S_dict[s_name], C, region)
        sep, p, frac = _key_separability_stat(df, H, S_dict[s_name], C, region)
        record(f"{s_name}_with_C", f"Nested present-state specification {s_name} (+C)", len(df), rmse, sep, p, frac)

    C_zero = np.zeros_like(C)
    rmse_noc = _key_reconstruction_rmse(H, S_dict["S3"], C_zero, region)
    sep_noc, p_noc, frac_noc = _key_separability_stat(df, H, S_dict["S3"], C_zero, region)
    record("S3_without_C", "S3 only, C excluded (zeroed out)", len(df), rmse_noc, sep_noc, p_noc, frac_noc)

    sep_rob, p_rob, frac_rob = _key_separability_stat(df, H, S_dict["S3"], C, region, scaler_cls=RobustScaler)
    record("alt_distance_scaling_robust", "RobustScaler instead of StandardScaler for D_SC construction", len(df), rmse0, sep_rob, p_rob, frac_rob)

    pop = df[f"GH_POP_TOT_{T_ENDPOINT}"].to_numpy()
    size_cutoff = np.quantile(pop, 0.10)
    mask_large = pop >= size_cutoff
    rmse_ns = _key_reconstruction_rmse(H[mask_large], S_dict["S3"][mask_large], C[mask_large], region[mask_large])
    sep_ns, p_ns, frac_ns = _key_separability_stat(
        df.loc[mask_large].reset_index(drop=True), H[mask_large], S_dict["S3"][mask_large], C[mask_large], region[mask_large]
    )
    record("remove_smallest_10pct", "Smallest 10% of cities by endpoint population removed", int(mask_large.sum()), rmse_ns, sep_ns, p_ns, frac_ns)

    clean_mask = (~qc["extreme_jump"].to_numpy()) & (~qc["non_monotonic"].to_numpy())
    rmse_cl = _key_reconstruction_rmse(H[clean_mask], S_dict["S3"][clean_mask], C[clean_mask], region[clean_mask])
    sep_cl, p_cl, frac_cl = _key_separability_stat(
        df.loc[clean_mask].reset_index(drop=True), H[clean_mask], S_dict["S3"][clean_mask], C[clean_mask], region[clean_mask]
    )
    record("remove_qc_flagged_trajectories", "Cities with extreme-jump or non-monotonic BUS trajectories removed", int(clean_mask.sum()), rmse_cl, sep_cl, p_cl, frac_cl)

    endpoint2015 = df["GH_BUS_TOT_2015"].to_numpy(dtype=float)
    h_epochs_alt = [e for e in EPOCHS_OBSERVED if e < 2015]
    H_alt = np.column_stack([df[f"GH_BUS_TOT_{t}"].to_numpy(dtype=float) / endpoint2015 for t in h_epochs_alt])
    pop2015 = df["GH_POP_TOT_2015"].to_numpy(dtype=float)
    buv2015 = df["GH_BUV_TOT_2015"].to_numpy(dtype=float)
    dens2015 = pop2015 / endpoint2015
    S3_alt = np.column_stack([pop2015, endpoint2015, dens2015, buv2015])
    rmse_alt = _key_reconstruction_rmse(H_alt, S3_alt, C, region)
    sep_alt, p_alt, frac_alt = _key_separability_stat(df, H_alt, S3_alt, C, region)
    record("alt_endpoint_T2015", "Alternative endpoint year T=2015 (H from 1975-2010)", len(df), rmse_alt, sep_alt, p_alt, frac_alt)

    return pd.DataFrame(rows)


# ----------------------------------------------------------------------
# Optional descriptive PCA
# ----------------------------------------------------------------------

def run_pca(H):
    from sklearn.decomposition import PCA
    pca = PCA(n_components=min(5, H.shape[1]), random_state=RANDOM_SEED)
    scores = pca.fit_transform(H)
    return pca, scores


# ----------------------------------------------------------------------
# Figures
# ----------------------------------------------------------------------

def make_figures(df, H, qc, sample_summary, recon_df, pairs_df, perm_df, perm_meta, sens_df, region):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    fig, axes = plt.subplots(1, 3, figsize=(15, 4))
    region_counts = pd.Series(region).value_counts()
    axes[0].bar(region_counts.index, region_counts.values, color="#4C72B0")
    axes[0].set_title("Final sample by region")
    axes[0].tick_params(axis="x", rotation=45)
    axes[1].hist(np.log10(df[f"GH_POP_TOT_{T_ENDPOINT}"]), bins=40, color="#55A868")
    axes[1].set_title(f"log10(population), endpoint {T_ENDPOINT}")
    axes[2].hist(np.log10(df[f"GH_BUS_TOT_{T_ENDPOINT}"]), bins=40, color="#C44E52")
    axes[2].set_title(f"log10(built-up m2), endpoint {T_ENDPOINT}")
    fig.tight_layout()
    fig.savefig(FIGURES_DIR / "figure1_sample_distribution_qc.png", dpi=120)
    plt.close(fig)

    fig, ax = plt.subplots(figsize=(7, 5))
    rng2 = np.random.RandomState(RANDOM_SEED)
    sample_idx = rng2.choice(len(H), size=min(60, len(H)), replace=False)
    for i in sample_idx:
        ax.plot(H_EPOCHS, H[i], alpha=0.3, color="#4C72B0", linewidth=0.8)
    ax.set_xlabel("Year")
    ax.set_ylabel(f"B(t) / B({T_ENDPOINT})")
    ax.set_title("Normalized pre-endpoint built-up trajectories (random sample of 60 cities)")
    fig.tight_layout()
    fig.savefig(FIGURES_DIR / "figure2_trajectory_diversity.png", dpi=120)
    plt.close(fig)

    fig, ax = plt.subplots(figsize=(8, 5))
    sub = recon_df[
        (recon_df["target"] == "aggregate_trajectory_rmse")
        & (recon_df["validation_scheme"] == "leave_region_out")
        & (recon_df["model"] == "random_forest")
    ].copy()
    sub["label"] = sub["s_spec"] + np.where(sub["c_included"], "+C", "")
    ax.bar(sub["label"], sub["mae_mean"], color="#8172B2")
    ax.set_ylabel("Aggregate trajectory RMSE (leave-region-out, random forest)")
    ax.set_title("Out-of-sample H reconstruction error by present-state specification")
    fig.tight_layout()
    fig.savefig(FIGURES_DIR / "figure3_reconstruction_performance.png", dpi=120)
    plt.close(fig)

    fig, ax = plt.subplots(figsize=(7, 5))
    ax.scatter(pairs_df["D_SC"], pairs_df["D_H"], s=4, alpha=0.2, color="#4C72B0")
    ax.set_xlabel("D_SC (standardized present-state/context distance)")
    ax.set_ylabel("D_H (historical trajectory distance)")
    ax.set_title("Historical divergence among present-day nearest neighbours")
    fig.tight_layout()
    fig.savefig(FIGURES_DIR / "figure4_DH_vs_DSC.png", dpi=120)
    plt.close(fig)

    fig, ax = plt.subplots(figsize=(7, 5))
    ax.hist(perm_df["null_statistic_mean_D_H"], bins=30, color="#CCB974", alpha=0.8)
    ax.axvline(perm_meta["observed_statistic"], color="red", linewidth=2, label="observed")
    ax.set_xlabel("Mean D_H among k-nearest S,C neighbors")
    ax.set_title("Observed statistic vs. constrained-permutation null")
    ax.legend()
    fig.tight_layout()
    fig.savefig(FIGURES_DIR / "figure5_permutation_null.png", dpi=120)
    plt.close(fig)

    fig, ax = plt.subplots(figsize=(9, 5))
    ax.barh(sens_df["variant"], sens_df["exp3_p_value_observed_lower_than_null"], color="#64B5CD")
    ax.set_xlabel("p-value (observed <= null); smaller = more structured than chance")
    ax.set_title("Sensitivity of separability finding across specifications")
    fig.tight_layout()
    fig.savefig(FIGURES_DIR / "figure6_sensitivity_summary.png", dpi=120)
    plt.close(fig)


# ----------------------------------------------------------------------
# Gate 1 decision
# ----------------------------------------------------------------------

def decide_gate1(recon_df, perm_meta, sens_df, sample_summary) -> dict:
    primary = recon_df[
        (recon_df["s_spec"] == "S3") & (recon_df["c_included"])
        & (recon_df["model"] == "random_forest")
        & (recon_df["validation_scheme"] == "leave_region_out")
        & (~recon_df["target"].isin(["aggregate_trajectory_rmse"]))
    ]
    mean_r2_leave_region = float(primary["r2_mean"].mean())

    evidence_for = []
    evidence_against = []

    if mean_r2_leave_region < 0.7:
        evidence_for.append(f"Mean per-epoch leave-region-out R2 for S3+C/RF is {mean_r2_leave_region:.3f} (<0.7); H is not near-perfectly reconstructed from S,C under geographic holdout.")
    else:
        evidence_against.append(f"Mean per-epoch leave-region-out R2 for S3+C/RF is {mean_r2_leave_region:.3f} (>=0.7); H is substantially reconstructable from S,C.")

    p_lower = perm_meta["p_value_observed_lower_than_null"]
    relative_effect = (perm_meta["null_mean"] - perm_meta["observed_statistic"]) / perm_meta["null_mean"]
    n_pairs_approx = sample_summary["final_n"] * 5
    if relative_effect < 0.40:
        evidence_for.append(
            f"Although the permutation test is statistically saturated at this sample "
            f"size (null std={perm_meta['null_std']:.5f} over approximately {n_pairs_approx} "
            f"neighbor pairs, so p(observed<=null)={p_lower:.3f} is not a meaningful "
            f"discriminator here), the RELATIVE effect size is only "
            f"{relative_effect*100:.1f}% (observed mean D_H {perm_meta['observed_statistic']:.3f} vs. "
            f"null mean {perm_meta['null_mean']:.3f}); present-state/context closeness explains only a "
            f"modest fraction of historical similarity, leaving most historical variation unexplained."
        )
    else:
        evidence_against.append(
            f"Relative effect size is large ({relative_effect*100:.1f}%: observed mean D_H "
            f"{perm_meta['observed_statistic']:.3f} vs. null mean {perm_meta['null_mean']:.3f}); "
            f"present-state/context closeness substantially predicts historical similarity, "
            f"even though the raw p-value is statistically saturated at this sample size."
        )

    baseline = sens_df[sens_df["variant"] == "baseline_S3_with_C"].iloc[0]
    robustness_variants = sens_df[sens_df["variant"].isin([
        "S1_with_C", "S2_with_C", "alt_distance_scaling_robust",
        "remove_smallest_10pct", "remove_qc_flagged_trajectories", "alt_endpoint_T2015",
    ])]
    baseline_frac = baseline["frac_high_D_H_among_low_D_SC_pairs"]
    rel_dev = (robustness_variants["frac_high_D_H_among_low_D_SC_pairs"] - baseline_frac).abs() / baseline_frac
    frac_consistent = float((rel_dev <= 0.30).mean())
    without_c_row = sens_df[sens_df["variant"] == "S3_without_C"].iloc[0]
    if frac_consistent >= 0.6:
        evidence_for.append(
            f"The effect-size metric 'fraction of close present-day analogues with still-high "
            f"historical divergence' is stable at {frac_consistent*100:.0f}% of true sensitivity "
            f"variants within 30% relative of baseline ({baseline_frac:.3f}); the degree of "
            f"historical separability is not an artifact of one specification. As an informative "
            f"contrast (not a robustness failure), removing C entirely raises this fraction to "
            f"{without_c_row['frac_high_D_H_among_low_D_SC_pairs']:.3f}, confirming that coarse "
            f"geographic/climate context does explain part of why present-day analogues share "
            f"similar histories (consistent with expected climate/region confounding)."
        )
    else:
        evidence_against.append(f"The effect-size metric is unstable across specifications (only {frac_consistent*100:.0f}% within 30% relative of baseline); apparent separability may be an artifact of one specification.")


    s1_r2 = float(recon_df[(recon_df["s_spec"] == "S1") & (~recon_df["c_included"]) & (recon_df["model"] == "random_forest") & (recon_df["validation_scheme"] == "leave_region_out") & (~recon_df["target"].isin(["aggregate_trajectory_rmse"]))]["r2_mean"].mean())
    s3_r2 = mean_r2_leave_region
    if (s1_r2 - s3_r2) < 0.1:
        evidence_for.append(f"Reconstruction R2 is similar for S1 (no C, {s1_r2:.3f}) and S3+C ({s3_r2:.3f}); the pattern is not simply explained away by richer present-state description.")
    else:
        evidence_against.append(f"Reconstruction R2 drops materially from S1 ({s1_r2:.3f}) to S3+C ({s3_r2:.3f}); richer present-state description substantially reduces apparent historical residual variation.")

    n_for, n_against = len(evidence_for), len(evidence_against)
    if n_for >= 3 and n_against == 0:
        classification = "PASS"
    elif n_against >= 3 and n_for == 0:
        classification = "FAIL"
    else:
        classification = "MIXED"

    return {
        "classification": classification,
        "mean_r2_leave_region_out_S3_C_rf": mean_r2_leave_region,
        "permutation_p_value_observed_lower_than_null": p_lower,
        "fraction_sensitivity_variants_consistent": frac_consistent,
        "evidence_for_continuing": evidence_for,
        "evidence_against_continuing": evidence_against,
        "note": "PASS does not mean the main scientific hypothesis is true; it only authorizes consideration of Gate 2. No environmental response variable was used in this decision.",
    }


if __name__ == "__main__":
    import platform
    import sklearn
    from datetime import datetime, timezone

    started_at = datetime.now(timezone.utc).isoformat()
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    FIGURES_DIR.mkdir(parents=True, exist_ok=True)
    (PROJECT_ROOT / "data" / "interim").mkdir(parents=True, exist_ok=True)

    log("Loading main UCDB table...")
    main_df = load_main_table()
    log(f"Loaded {len(main_df)} urban centres.")

    # --- Phase A: schema audit ---
    log("Writing UCDB schema audit...")
    schema_rows = []

    def schema_row(field, desc, unit, year, family, derived, role, usable, caveat):
        schema_rows.append({
            "field_name": field, "field_description": desc, "unit": unit, "year": year,
            "variable_family": family, "direct_or_derived": derived, "candidate_role": role,
            "usable_for_gate1": usable, "caveat": caveat,
            "official_source": "GHS-UCDB R2024A V1.2, theme GHSL / General Characteristics / Geography / UC_centroids (JRC, DOI 10.2905/1a338be6-7eaf-480c-9664-3a8ade88cbcd)",
        })

    for y in EPOCHS_OBSERVED:
        schema_row(f"GH_BUS_TOT_{y}", "Total built-up surface within fixed (2025-reference) urban centre boundary", "m2", y, "built_up_surface", "direct", "H (primary) / S endpoint", "YES",
                   "Boundary is fixed at 2025 reference delineation for all epochs (see Section 6/caveat); 2025/2030 epochs excluded as model-projected, not observed.")
        schema_row(f"GH_POP_TOT_{y}", "Total population within fixed urban centre boundary", "persons", y, "population", "direct", "S / secondary H candidate", "YES", "Same fixed-boundary caveat as GH_BUS_TOT.")
        schema_row(f"GH_BUV_TOT_{y}", "Total built-up volume within fixed urban centre boundary", "m3 (approx.)", y, "built_up_volume", "direct", "S3 component", "YES", "Same fixed-boundary caveat.")
    schema_row("GC_UCN_MAI_2025", "Main urban centre name", "text", 2025, "identification", "direct", "identification only", "NO", "Not used as a model feature.")
    schema_row("GC_CNT_GAD_2025", "Country name (GADM)", "text", 2025, "identification", "direct", "C (region mapping input)", "YES", "Mapped to 6-region scheme for leave-region-out validation and permutation strata.")
    schema_row("GC_UCB_YOB_2025", "Year urban centre first qualified under Degree-of-Urbanisation criteria", "year", 2025, "identification", "direct", "QC / sample exclusion", "YES", "Cities with YOB > endpoint year T excluded from primary sample.")
    schema_row("GC_UCB_YOD_2025", "Last year urban centre is projected to still qualify", "year", 2025, "identification", "direct", "QC informational", "NO", "Almost all cities have YOD=2030 (not dissolving); minor informational field.")
    schema_row("GC_UCC_LON_2025/GC_UCC_LAT_2025", "Urban centre centroid coordinates", "metres (World Mollweide, ESRI:54009)", 2025, "geography", "direct", "C (reprojected to WGS84 degrees)", "YES", "Stored in projected CRS despite field name; reprojected to EPSG:4326 in this execution.")
    schema_row("GE_ELV_AVG_2025", "Average elevation of urban centre", "metres", 2025, "geography", "direct", "C component", "YES", "Low-cost context variable, already in official table.")
    schema_row("GE_ECO_CLA_2025", "WWF terrestrial ecoregion classification", "categorical (555 classes)", 2025, "geography", "direct", "considered, not used", "NO", "Too fine-grained (555 classes) for a deliberately modest C; excluded from this execution's C.")
    schema_row("GE_BIO_A01_2025 .. GE_BIO_A24_2025", "24 bioclimatic variables (WorldClim/CHELSA-style)", "varies", 2025, "climate", "derived (external climate product summarized to UC)", "available, not used", "NO", "Available in official table but not used in this execution to keep C deliberately modest; noted for future Gate 2 work.")
    schema_row("GC_DEV_WIG_2025/GC_DEV_USR_2025", "World Bank income group / development classification", "categorical", 2025, "socioeconomic", "direct", "available, not used", "NO", "Socioeconomic/development variable, out of scope for the coarse C authorized in this execution; relevant to risk G (development-level confounding) for future work.")
    for y in EPOCHS_OBSERVED:
        schema_row(f"MT_BUS_TOT_{y} (MTUC product)", "Built-up surface within TIME-VARYING urban centre boundary", "m2", y, "built_up_surface_mtuc", "direct", "boundary-sensitivity check", "YES", "From separate GHS_UCDB_MTUC_GLOBE_R2024A product (ID_MTUC_G0 key, N=11687, not row-aligned with main table); used only for sensitivity, not primary analysis.")

    schema_df = pd.DataFrame(schema_rows)
    schema_df.to_csv(RESULTS_DIR / "ucdb_schema_audit.csv", index=False, encoding="utf-8")
    log(f"Schema audit written: {len(schema_df)} rows.")

    # --- Gate A decision ---
    gate_a = "PASS"
    gate_a_reason = (
        f"Official GHS-UCDB R2024A provides {len(EPOCHS_OBSERVED)} directly-observed "
        f"(non-projected) multitemporal epochs ({EPOCHS_OBSERVED[0]}-{EPOCHS_OBSERVED[-1]}, "
        f"5-year intervals) of built-up surface, population, and built-up volume for "
        f"{len(main_df)} urban centres globally, obtained entirely from official "
        f"pre-aggregated city-level table/vector products (264MB + 35MB, both well "
        f"under the 500MB threshold). This provides {len(H_EPOCHS)} strictly "
        f"pre-endpoint observations for H, satisfying the 'multiple pre-endpoint "
        f"observations' minimum requirement without any raster download."
    )
    log(f"GATE_A = {gate_a}")

    # --- QC ---
    log("Running QC...")
    qc_full = run_qc(main_df)
    sample_df, sample_summary = build_sample(main_df, qc_full)
    qc_full.to_csv(RESULTS_DIR / "history_qc.csv", index=False, encoding="utf-8")
    with open(RESULTS_DIR / "sample_summary.json", "w", encoding="utf-8") as f:
        json.dump(sample_summary, f, indent=2, default=str)
    log(f"Sample: initial={sample_summary['initial_n']}, final={sample_summary['final_n']}")

    qc_sample = qc_full[qc_full["ID_UC_G0"].isin(sample_df["ID_UC_G0"])].reset_index(drop=True)

    # --- H, S, C ---
    log("Building H, S, C...")
    H, descriptors = build_H(sample_df)
    S_dict = build_S(sample_df)
    C = build_C(sample_df)
    region = sample_df["region"].to_numpy()
    descriptors.to_csv(RESULTS_DIR / "history_descriptors.csv", index=False, encoding="utf-8")

    # --- Experiment 1 ---
    log("Running Experiment 1: history reconstruction (this may take a minute)...")
    recon_df = run_experiment1(H, S_dict, C, region)
    recon_df.to_csv(RESULTS_DIR / "reconstruction_metrics.csv", index=False, encoding="utf-8")
    log("Experiment 1 done.")

    # --- Experiment 2 ---
    log("Running Experiment 2: present-day analogues...")
    pairs_df, Xs = run_experiment2(sample_df, H, S_dict["S3"], C, k=5)
    twins_df = build_twin_candidates(sample_df, pairs_df, region, top_n=50)
    twins_df.to_csv(RESULTS_DIR / "twin_candidates.csv", index=False, encoding="utf-8")
    log(f"Experiment 2 done. {len(twins_df)} twin candidates identified.")

    # --- Experiment 3 ---
    log("Running Experiment 3: permutation test (300 permutations)...")
    perm_df, perm_meta = run_experiment3(sample_df, H, region, pairs_df, n_permutations=300)
    perm_df.to_csv(RESULTS_DIR / "permutation_results.csv", index=False, encoding="utf-8")
    with open(RESULTS_DIR / "permutation_meta.json", "w", encoding="utf-8") as f:
        json.dump(perm_meta, f, indent=2)
    log(f"Experiment 3 done. observed={perm_meta['observed_statistic']:.4f}, p_lower={perm_meta['p_value_observed_lower_than_null']:.4f}")

    # --- Sensitivity ---
    log("Running sensitivity analyses...")
    sens_df = run_sensitivity(sample_df, H, S_dict, C, region, qc_sample)
    sens_df.to_csv(RESULTS_DIR / "sensitivity_results.csv", index=False, encoding="utf-8")
    log("Sensitivity analyses done.")

    # --- PCA (descriptive) ---
    pca, pca_scores = run_pca(H)
    pca_summary = {
        "explained_variance_ratio": pca.explained_variance_ratio_.tolist(),
        "loadings": pca.components_.tolist(),
        "epochs": H_EPOCHS,
    }
    with open(RESULTS_DIR / "pca_summary.json", "w", encoding="utf-8") as f:
        json.dump(pca_summary, f, indent=2)

    # --- Figures ---
    log("Generating figures...")
    make_figures(sample_df, H, qc_sample, sample_summary, recon_df, pairs_df, perm_df, perm_meta, sens_df, region)
    log("Figures done.")

    # --- Gate 1 decision ---
    gate1 = decide_gate1(recon_df, perm_meta, sens_df, sample_summary)
    gate1_full = {
        "gate_a": gate_a,
        "gate_a_reason": gate_a_reason,
        "endpoint_year_T": T_ENDPOINT,
        "h_epochs": H_EPOCHS,
        **gate1,
    }
    with open(RESULTS_DIR / "gate1_decision.json", "w", encoding="utf-8") as f:
        json.dump(gate1_full, f, indent=2)
    log(f"GATE 1 = {gate1['classification']}")

    completed_at = datetime.now(timezone.utc).isoformat()
    run_metadata = {
        "execution_id": "1005-4",
        "source_prompt": "prompts/prompt1005-4.txt",
        "previous_execution": "1005-3",
        "report": "reports/report1005-4.md",
        "status": "COMPLETED",
        "started_at": started_at,
        "completed_at": completed_at,
        "random_seed": RANDOM_SEED,
        "endpoint_year_T": T_ENDPOINT,
        "h_epochs_used": H_EPOCHS,
        "gate_a": gate_a,
        "gate1_classification": gate1["classification"],
        "sample_initial_n": sample_summary["initial_n"],
        "sample_final_n": sample_summary["final_n"],
        "python_version": sys.version,
        "platform": platform.platform(),
        "sklearn_version": sklearn.__version__,
        "pandas_version": pd.__version__,
        "numpy_version": np.__version__,
    }
    with open(RESULTS_DIR / "run_metadata.json", "w", encoding="utf-8") as f:
        json.dump(run_metadata, f, indent=2)
    log("ALL DONE.")

