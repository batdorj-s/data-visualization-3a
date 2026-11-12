import numpy as np
import pandas as pd
import pytest

from src.analysis import HypothesisResult, describe_categorical, describe_games, describe_numeric, eval_h1, eval_h2, eval_h4


def test_describe_numeric():
    out = describe_numeric(pd.DataFrame({"x": [1, 2, 2, 3, 10]}), ["x"]).iloc[0]
    assert (out.n, out["mean"], out["median"], out["mode"]) == (5, 3.6, 2, 2)
    assert (out["min"], out["max"], out.q1, out.q2, out.q3, out.iqr) == (1, 10, 2, 2, 3, 1)
    assert out["skew"] > 0
    assert out["std"] == pytest.approx(np.std([1, 2, 2, 3, 10], ddof=1))


def test_describe_numeric_by_group():
    df = pd.DataFrame({"x": [1, 2, 10, 20], "g": ["a", "a", "b", "b"]})
    out = describe_numeric(df, ["x"], by="g").set_index("group")
    assert out.loc["a", "mean"] == 1.5 and out.loc["b", "mean"] == 15
    assert "Бүгд" in out.index


def test_describe_categorical():
    out = describe_categorical(pd.DataFrame({"pos": ["PG", "PG", "C"]}), ["pos"]).set_index("value")
    assert out.loc["PG", "count"] == 2
    assert out.loc["PG", "pct"] == pytest.approx(66.67, abs=0.01)
    assert bool(out.loc["PG", "is_mode"]) is True and bool(out.loc["C", "is_mode"]) is False


def test_describe_games():
    g = pd.DataFrame({"home_pts": [77, 80], "away_pts": [69, 70],
                      "quarters_home": ["18|20|20|19", "20|20|20|20"], "quarters_away": ["17|23|16|13", "10|20|20|20"]})
    out = describe_games(g).set_index("variable")
    assert out.loc["total_pts", "mean"] == 148
    assert out.loc["margin", "mean"] == 9
    assert out.loc["q1_pts", "mean"] == pytest.approx((18 + 17 + 20 + 10) / 4)


def test_h1_direction():
    p = pd.DataFrame({"PPG": [20, 22, 25, 5, 6, 8], "is_import": [True] * 3 + [False] * 3})
    r = eval_h1(p, n_boot=500)
    assert isinstance(r, HypothesisResult) and r.hid == "H1"
    assert r.estimate == 16
    assert r.ci_lo > 0
    assert r.p_value < 0.1
    assert r.null_value == 0


def test_h2_fair_coin():
    g = pd.DataFrame({"home_pts": [80] * 50 + [70] * 50, "away_pts": [70] * 50 + [80] * 50})
    r = eval_h2(g)
    assert r.estimate == 0.5
    assert r.p_value == pytest.approx(1.0, abs=1e-9)
    assert r.null_value == 0.5 and r.ci_lo < 0.5 < r.ci_hi


def test_h4_perfect():
    x = np.arange(30, dtype=float)
    r = eval_h4(pd.DataFrame({"height_cm": x, "RPG": 2 * x}))
    assert r.estimate == pytest.approx(1.0)
