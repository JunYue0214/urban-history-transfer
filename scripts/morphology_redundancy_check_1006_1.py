"""1006-1 diagnostic: is a GHSL built-volume history independent of the built-area history?

Local UCDB attributes only (Gate 1 sample, N=10,915). No thermal data, no network. Writes
results/1006-1/morphology_redundancy_check.json so the numbers quoted in the report are reproducible.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
import ucdb_gate1_pilot as p  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent


def compute(s: pd.DataFrame) -> dict:
    E = p.EPOCHS_OBSERVED
    h = pd.DataFrame({t: s[f"GH_BUV_TOT_{t}"] / s[f"GH_BUS_TOT_{t}"] for t in E})
    rel = h.div(h[2020], axis=0)
    A = np.column_stack([s[f"GH_BUS_TOT_{t}"] / s["GH_BUS_TOT_2020"] for t in E[:-1]])
    V = np.column_stack([s[f"GH_BUV_TOT_{t}"] / s["GH_BUV_TOT_2020"] for t in E[:-1]])
    return {
        "n": int(len(s)),
        "median_ratio_implied_height_to_2020": {str(t): float(rel[t].median()) for t in E},
        "share_cities_height_range_lt_1pct": float(((rel.max(axis=1) - rel.min(axis=1)) < 0.01).mean()),
        "per_epoch_corr_area_ratio_vs_volume_ratio": {str(t): float(np.corrcoef(A[:, i], V[:, i])[0, 1]) for i, t in enumerate(E[:-1])},
        "rms_difference_area_vs_volume_vectors": float(np.sqrt(((A - V) ** 2).mean())),
        "mean_per_epoch_sd_of_area_vector": float(A.std(axis=0).mean()),
    }


def main() -> int:
    main_t = p.load_main_table()
    qc = p.run_qc(main_t)
    sample, _ = p.build_sample(main_t, qc)
    out = compute(sample)
    (ROOT / "results" / "1006-1" / "morphology_redundancy_check.json").write_text(json.dumps(out, indent=2), encoding="utf-8")
    print(json.dumps(out, indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
