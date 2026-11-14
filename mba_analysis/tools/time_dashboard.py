"""Dashboard-ийн хариу өгөх хугацааг AppTest-ээр хэмжиж reports/dashboard_timing.csv-д бичнэ."""
import statistics
import sys
import time
from pathlib import Path

import pandas as pd
from streamlit.testing.v1 import AppTest

ROOT = Path(__file__).resolve().parents[1]
APP = str(ROOT / "dashboard" / "app.py")


def timed(fn):
    t = time.perf_counter()
    fn()
    return (time.perf_counter() - t) * 1000


def main(n: int = 20) -> pd.DataFrame:
    rows = []
    at = AppTest.from_file(APP, default_timeout=120)
    rows.append(("first_load_ms", timed(at.run)))
    at.switch_page("views/players.py")
    at.run()
    filter_ms = []
    for i in range(n):
        at.session_state["min_gp"] = 3 + i % 10
        filter_ms.append(timed(at.run))
    rows.append(("filter_update_median_ms", statistics.median(filter_ms)))
    rows.append(("filter_update_p90_ms", sorted(filter_ms)[int(0.9 * n) - 1]))
    at.switch_page("views/shots.py")
    rows.append(("shots_page_load_ms", timed(at.run)))
    teams = ["BCH Knights", "SG Apes", "XAC Broncos", "Selenge Bodons"]
    shot_ms = []
    for i in range(n):
        at.session_state["highlight_team"] = teams[i % len(teams)]
        shot_ms.append(timed(at.run))
    rows.append(("shots_page_update_median_ms", statistics.median(shot_ms)))
    sys.path.insert(0, str(ROOT))
    from src.build_dashboard_data import win_probability
    import numpy as np
    coefs = pd.read_parquet(ROOT / "dashboard" / "data" / "elo_coefs.parquet").coef.to_numpy()
    t = time.perf_counter()
    for _ in range(1000):
        win_probability(1550.0, 1480.0, coefs)
    rows.append(("win_probability_ms", (time.perf_counter() - t)))
    out = pd.DataFrame(rows, columns=["metric", "value"])
    out["target"] = ["< 3000", "< 300", "-", "< 3000", "< 300", "< 100"]
    out["value"] = out.value.round(2)
    out.to_csv(ROOT / "reports" / "dashboard_timing.csv", index=False)
    return out


if __name__ == "__main__":
    print(main().to_string(index=False))
