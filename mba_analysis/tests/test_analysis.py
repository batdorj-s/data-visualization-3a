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


def test_run_analysis_writes_reports(tmp_path):
    from src.analysis import run_analysis
    proc, rep = tmp_path / "processed", tmp_path / "reports"
    proc.mkdir()
    rng = np.random.default_rng(0)
    n = 40
    pd.DataFrame({
        "PPG": rng.uniform(0, 25, n), "RPG": rng.uniform(0, 10, n), "APG": rng.uniform(0, 6, n),
        "MIN": rng.uniform(5, 35, n), "ts_pct": rng.uniform(0.3, 0.7, n), "height_cm": rng.uniform(175, 210, n),
        "age": rng.integers(19, 35, n), "eligible": [True] * n, "is_import": [True] * 10 + [False] * 30,
        "position": rng.choice(["PG", "SG", "SF", "PF", "C"], n), "pos_group": "Guard", "team": "A",
        "region": "Улаанбаатар", "scorer_tier": "Дунд",
    }).to_csv(proc / "players_season.csv", index=False)
    pd.DataFrame({"home_pts": [80, 70, 90], "away_pts": [70, 80, 85], "phase": ["regular"] * 3,
                  "quarters_home": ["20|20|20|20"] * 3, "quarters_away": ["20|20|20|10"] * 3}).to_csv(
        proc / "games.csv", index=False)
    run_analysis(proc, rep)
    for name in ["descriptive_numeric", "descriptive_categorical", "descriptive_games", "hypotheses"]:
        assert (rep / f"{name}.csv").exists()
    hyp = pd.read_csv(rep / "hypotheses.csv")
    assert {"H1", "H2", "H4"} <= set(hyp.hid)
    assert list(hyp.columns) == list(HypothesisResult._fields)


def test_extra_hypotheses_h3_h5(tmp_path):
    import json
    from src.analysis import extra_hypotheses
    pd.DataFrame({"feature": ["efg", "tov_pct", "orb_pct", "ftr"], "coef": [3.8, -1.9, 1.6, 1.0],
                  "lo": [3.5, -2.3, 1.2, 0.7], "hi": [4.2, -1.6, 1.9, 1.4], "perm_importance": [0.4, 0.09, 0.07, 0.03],
                  "perm_lo": [0.33, 0.06, 0.05, 0.02], "perm_hi": [0.46, 0.12, 0.09, 0.05]}).to_csv(
        tmp_path / "explanatory.csv", index=False)
    (tmp_path / "metrics.json").write_text(json.dumps({"pythagorean": {
        "exponent": 10.8, "r2": 0.886, "r2_ci": {"est": 0.886, "lo": 0.79, "hi": 0.94}, "n": 33}}), encoding="utf-8")
    res = {r.hid: r for r in extra_hypotheses(tmp_path)}
    assert res["H3"].estimate == 3.8 and res["H3"].ci_lo == 3.5 and "1/4" in res["H3"].method
    assert res["H5"].estimate == 0.886 and res["H5"].n == 33 and res["H5"].ci_hi == 0.94


def test_extra_hypotheses_missing_files(tmp_path):
    from src.analysis import extra_hypotheses
    assert extra_hypotheses(tmp_path) == []
