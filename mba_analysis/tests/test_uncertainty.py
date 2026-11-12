import numpy as np
import pandas as pd
import pytest

from src.uncertainty import CI, bootstrap_distribution, cluster_bootstrap, fisher_ci, funnel_limits, wilson_ci


def test_wilson_known_values():
    ci = wilson_ci(8, 10)
    assert isinstance(ci, CI)
    assert ci.est == pytest.approx(0.8)
    assert (ci.lo, ci.hi) == pytest.approx((0.4902, 0.9433), abs=1e-4)
    zero = wilson_ci(0, 5)
    assert (zero.lo, zero.hi) == pytest.approx((0.0, 0.4345), abs=1e-4)


def test_fisher_known_values():
    ci = fisher_ci(0.5, 30)
    assert (ci.lo, ci.hi) == pytest.approx((0.1704, 0.7290), abs=1e-3)
    assert ci.est == 0.5


def _games(values_per_game, rows_per_game=5):
    return pd.DataFrame({
        "game_id": np.repeat(np.arange(len(values_per_game)), rows_per_game),
        "x": np.repeat(values_per_game, rows_per_game).astype(float),
    })


def test_cluster_bootstrap_resamples_groups():
    vals = np.arange(10, dtype=float)
    df = _games(vals)
    ci = cluster_bootstrap(df, "game_id", lambda d: d["x"].mean(), n_boot=500, seed=42)
    rng = np.random.default_rng(42)
    game_level = [vals[rng.integers(0, 10, 10)].mean() for _ in range(500)]
    assert ci.lo == pytest.approx(np.percentile(game_level, 2.5))
    assert ci.hi == pytest.approx(np.percentile(game_level, 97.5))
    assert ci.est == pytest.approx(4.5)


def test_cluster_bootstrap_constant_has_zero_width():
    ci = cluster_bootstrap(_games(np.full(8, 3.0)), "game_id", lambda d: d["x"].mean(), n_boot=200)
    assert ci.lo == ci.hi == ci.est == 3.0


def test_cluster_bootstrap_deterministic():
    df = _games(np.random.default_rng(0).normal(size=20))
    a = cluster_bootstrap(df, "game_id", lambda d: d["x"].mean(), n_boot=300, seed=42)
    b = cluster_bootstrap(df, "game_id", lambda d: d["x"].mean(), n_boot=300, seed=42)
    assert a == b
    assert len(bootstrap_distribution(df, "game_id", lambda d: d["x"].mean(), n_boot=300)) == 300


def test_funnel_limits():
    lo, hi = funnel_limits(0.5, np.array([100]), 1.96)
    assert (lo[0], hi[0]) == pytest.approx((0.402, 0.598), abs=1e-3)
    lo, hi = funnel_limits(0.5, np.array([1]), 3.0)
    assert lo[0] == 0.0 and hi[0] == 1.0
