import time
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from src.build_dashboard_data import EXPECTED, build, player_ci_fast, win_probability

ROOT = Path(__file__).resolve().parents[1]


def test_player_ci_fast_brackets_estimate():
    pts = np.array([10, 20, 30, 15, 25], dtype=float)
    fga = np.array([10, 12, 15, 9, 14], dtype=float)
    fta = np.array([2, 4, 6, 1, 3], dtype=float)
    out = player_ci_fast(pts, fga, fta, n_boot=500)
    assert out["ppg"].est == pytest.approx(20.0)
    assert out["ppg"].lo <= 20.0 <= out["ppg"].hi
    ts = pts.sum() / (2 * (fga.sum() + 0.44 * fta.sum()))
    assert out["ts_pct"].est == pytest.approx(ts)
    assert out["ts_pct"].lo <= ts <= out["ts_pct"].hi


def test_win_probability_symmetric_and_fast():
    coefs = np.random.default_rng(0).normal(0.004, 0.0005, 500)
    p, lo, hi = win_probability(1500, 1500, coefs)
    assert p == 0.5 and lo == 0.5 and hi == 0.5
    p2, lo2, hi2 = win_probability(1600, 1500, coefs)
    assert 0.5 < lo2 <= p2 <= hi2 < 1
    start = time.perf_counter()
    for _ in range(1000):
        win_probability(1550, 1480, coefs)
    assert time.perf_counter() - start < 0.1


def test_build_writes_parquets(tmp_path):
    counts = build(ROOT / "data" / "processed", ROOT / "reports", tmp_path, n_boot=50)
    for name in EXPECTED:
        assert (tmp_path / f"{name}.parquet").exists(), name
    ci = pd.read_parquet(tmp_path / "player_ci.parquet")
    assert (ci.lo <= ci.est + 1e-9).all() and (ci.est <= ci.hi + 1e-9).all()
    assert set(ci.metric) == {"ppg", "ts_pct"}
    total = sum(f.stat().st_size for f in tmp_path.glob("*.parquet"))
    assert total <= 20 * 1024 * 1024
    assert counts["players"] > 200
