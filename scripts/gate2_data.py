"""Execution 1005-9 data assembly: cluster-level S/C/H tables and response join.

Reads only already-local, validated data. The response join (`attach_response`)
is the single place where thermal values enter, and it is only called by the
Gate 2 pipeline.
"""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pyogrio

sys.path.insert(0, str(Path(__file__).resolve().parent))
import gate2_support as g  # noqa: E402
import ucdb_gate1_pilot as p  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
YCEO_SHP = ROOT / "data" / "interim" / "1005-7" / "yceo_suhi_v4" / "All_shp.shp"
LINKS_PATH = ROOT / "results" / "1005-7" / "ucdb_yceo_crosswalk.csv"
PRIMARY_TABLE_1005_8 = ROOT / "results" / "1005-8" / "cluster_level_dataset_primary.csv"
MTUC_XWALK = ROOT / "results" / "1005-5" / "ucdb_mtuc_crosswalk.csv"
EPOCHS = [1975, 1980, 1985, 1990, 1995, 2000, 2005, 2010, 2015, 2020]


def koppen_major(code: float) -> str | float:
    """Beck et al. (2018) class codes 1-30 -> major group (A 1-3, B 4-7, C 8-16, D 17-28, E 29-30)."""
    if not np.isfinite(code):
        return np.nan
    c = int(code)
    return "A" if c <= 3 else "B" if c <= 7 else "C" if c <= 16 else "D" if c <= 28 else "E"


def load_cities() -> pd.DataFrame:
    """The 1005-4 Gate 1 sample (N=10,915) with every field used anywhere in Gate 2."""
    main = p.load_main_table()
    qc = p.run_qc(main)
    sample, _ = p.build_sample(main, qc)
    clim = pyogrio.read_dataframe(
        p.GPKG_PATH, layer="GHSL_UCDB_THEME_CLIMATE_GLOBE_R2024A", read_geometry=False,
        columns=["ID_UC_G0"] + [f"CL_{b}_CUR_{y}" for b in ("B01", "B04", "B12", "B15") for y in (2000, 2010)]
        + ["CL_KOP_CUR_2025"])
    s = sample.merge(clim, on="ID_UC_G0", how="left")
    s["temp_c"] = (s["CL_B01_CUR_2000"] + s["CL_B01_CUR_2010"]) / 2
    s["log_precip"] = np.log((s["CL_B12_CUR_2000"] + s["CL_B12_CUR_2010"]) / 2)
    s["temp_seas"] = (s["CL_B04_CUR_2000"] + s["CL_B04_CUR_2010"]) / 2
    s["precip_seas"] = (s["CL_B15_CUR_2000"] + s["CL_B15_CUR_2010"]) / 2
    s["kop_major"] = s["CL_KOP_CUR_2025"].map(koppen_major)
    return s


def assemble_units(units: pd.DataFrame, cities: pd.DataFrame) -> pd.DataFrame:
    """One row per cluster unit: aggregated S (any epoch), C, B_t sums (aggregate AND dominant city)."""
    ci = cities.set_index("ID_UC_G0")
    ids_long = []
    for r in units.itertuples():
        for i in r.ucdb_ids.split(";"):
            ids_long.append((r.yceo_id, int(i)))
    L = pd.DataFrame(ids_long, columns=["yceo_id", "ucdb_id"])
    L = L.join(ci, on="ucdb_id")
    L["w"] = L["GH_BUS_TOT_2020"]
    L = L.sort_values(["yceo_id", "GH_BUS_TOT_2020", "ucdb_id"], ascending=[True, False, True])
    dom = L.groupby("yceo_id").head(1).set_index("yceo_id")
    sums = {}
    for t in EPOCHS:
        sums[f"B_{t}"] = L.groupby("yceo_id")[f"GH_BUS_TOT_{t}"].sum()
        sums[f"POP_{t}"] = L.groupby("yceo_id")[f"GH_POP_TOT_{t}"].sum()
        sums[f"BUV_{t}"] = L.groupby("yceo_id")[f"GH_BUV_TOT_{t}"].sum()
    A = pd.DataFrame(sums)
    A["n_ucdb"] = L.groupby("yceo_id").size()
    for c in ["lat_deg", "lon_deg", "GE_ELV_AVG_2025", "temp_c", "log_precip", "temp_seas", "precip_seas"]:
        A[c] = L.groupby("yceo_id").apply(lambda d, c=c: float(np.average(d[c], weights=d["w"])), include_groups=False)
    for t in EPOCHS:
        A[f"DB_{t}"] = dom[f"GH_BUS_TOT_{t}"]          # dominant-city built-up
    A["region"] = dom["region"]
    A["kop_major"] = dom["kop_major"]
    A["yob"] = dom["GC_UCB_YOB_2025"]
    A["dominant_ucdb_id"] = dom["ucdb_id"]
    A["ucdb_ids"] = L.groupby("yceo_id")["ucdb_id"].apply(lambda s: ";".join(map(str, sorted(s))))
    A = A.reset_index()
    A["unit_type"] = np.where(A["n_ucdb"] == 1, "single_city", "multi_city_aggregate")
    A = A.merge(units[["yceo_id", "coverage", "unit_iou", "yceo_area_km2"]], on="yceo_id", how="left")
    for t in (2000, 2015, 2020):
        A[f"density_{t}"] = A[f"POP_{t}"] / A[f"B_{t}"]
    return A.sort_values("yceo_id").reset_index(drop=True)


def s_block(A: pd.DataFrame, level: str = "S3", year: int = 2020) -> np.ndarray:
    pop, bus, buv, den = (np.log(A[f"POP_{year}"]), np.log(A[f"B_{year}"]), np.log(A[f"BUV_{year}"]),
                          np.log(A[f"density_{year}"]))
    cols = {"S1": [pop, bus], "S2": [pop, bus, den], "S3": [pop, bus, den, buv]}[level]
    return np.column_stack(cols)


def c_block(A: pd.DataFrame, level: str = "C1") -> np.ndarray:
    c0 = [A["lat_deg"], A["lon_deg"], A["GE_ELV_AVG_2025"]]
    c1 = c0 + [A["temp_c"], A["log_precip"]]
    if level == "C0":
        return np.column_stack(c0)
    if level == "C1":
        return np.column_stack(c1)
    dummies = pd.get_dummies(A["kop_major"]).astype(float)
    for k in "ABCDE":
        if k not in dummies:
            dummies[k] = 0.0
    return np.column_stack(c1 + [A["temp_seas"], A["precip_seas"]] + [dummies[k] for k in "ABCDE"])


def attach_response(A: pd.DataFrame, fields=("Annual_nig", "Summer_day")) -> pd.DataFrame:
    """Join cluster-level R by YCEO `Code`. The only place thermal values are read in Gate 2."""
    import geopandas as gpd
    y = gpd.read_file(YCEO_SHP, columns=["Code", *fields], ignore_geometry=True) if False else None
    y = pyogrio.read_dataframe(YCEO_SHP, columns=["Code", *fields], read_geometry=False)
    y = y.rename(columns={"Code": "yceo_id"})
    out = A.merge(y, on="yceo_id", how="left", validate="one_to_one")
    return out


def folds_for(A: pd.DataFrame, k: int = 5):
    tiles = g.tile_ids(A["lat_deg"].to_numpy(), A["lon_deg"].to_numpy(), 10.0)
    fold, load = g.balanced_group_folds(tiles, k)
    return tiles, fold


def units_for_rule(links: pd.DataFrame, coverage: float, iou: float | None) -> pd.DataFrame:
    return g.units_from_status(g.classify_clusters(links, coverage, iou))
