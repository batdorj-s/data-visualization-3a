import numpy as np
import pandas as pd
import pytest

from src.elo import run_elo
from src.models import (
    WIN_FEATURES,
    baseline_predict,
    bootstrap_metrics,
    build_game_matrix,
    fit_explanatory,
    fit_pythagorean,
    make_models,
    walk_forward_cv,
)


def synthetic_league(n_games=40, n_teams=6, seed=0, season="2025-2026", start="2025-10-01"):
    rng = np.random.default_rng(seed)
    strength = rng.normal(0, 5, n_teams)
    rows, tg = [], []
    dates = pd.date_range(start, periods=n_games, freq="D")
    for gid, d in enumerate(dates, 1):
        h, a = rng.choice(n_teams, 2, replace=False)
        hp = int(80 + strength[h] + rng.normal(0, 8))
        ap = int(80 + strength[a] + rng.normal(0, 8))
        if hp == ap:
            hp += 1
        rows.append(dict(game_id=gid, season=season, date=d.date().isoformat(), home_key=f"t{h}", away_key=f"t{a}",
                         home_pts=hp, away_pts=ap, phase="regular"))
        for side, t, o, pts, opp in (("home", h, a, hp, ap), ("away", a, h, ap, hp)):
            tg.append(dict(game_id=gid, season=season, date=d.date().isoformat(), side=side, team_key=f"t{t}",
                           opp_key=f"t{o}", PTS=pts, opp_pts=opp, win=pts > opp, net=float(pts - opp),
                           efg=0.45 + (pts - opp) / 400, tov_pct=0.15 - (pts - opp) / 1000,
                           orb_pct=0.3 + rng.normal(0, 0.03), ftr=0.25 + rng.normal(0, 0.03)))
    games = pd.DataFrame(rows)
    elo = run_elo(games)
    games = games.merge(elo[["game_id", "elo_pre_home", "elo_pre_away"]], on="game_id")
    return games, pd.DataFrame(tg)


def test_no_leakage():
    games, tg = synthetic_league()
    base = build_game_matrix(games, tg).set_index("game_id")
    last = games.game_id.max()
    g2, tg2 = games.copy(), tg.copy()
    g2.loc[g2.game_id == last, ["home_pts", "away_pts"]] = g2.loc[g2.game_id == last, ["away_pts", "home_pts"]].values
    tg2.loc[tg2.game_id == last, "win"] = ~tg2.loc[tg2.game_id == last, "win"]
    tg2.loc[tg2.game_id == last, "net"] *= -1
    flipped = build_game_matrix(g2, tg2).set_index("game_id")
    if last in base.index:
        assert base.loc[last, WIN_FEATURES].tolist() == flipped.loc[last, WIN_FEATURES].tolist()
        assert base.loc[last, "y"] != flipped.loc[last, "y"]


def test_same_day_excluded():
    games = pd.DataFrame([
        dict(game_id=i, season="s", date=d, home_key=h, away_key=a, home_pts=hp, away_pts=ap, phase="regular",
             elo_pre_home=1500.0, elo_pre_away=1500.0)
        for i, (d, h, a, hp, ap) in enumerate([
            ("2025-10-01", "a", "b", 80, 70), ("2025-10-02", "a", "c", 80, 70), ("2025-10-03", "b", "c", 80, 70),
            ("2025-10-04", "a", "b", 60, 70), ("2025-10-04", "a", "c", 90, 70)], 1)
    ])
    tg = []
    for g in games.itertuples():
        for side, t, o, p, q in (("home", g.home_key, g.away_key, g.home_pts, g.away_pts),
                                 ("away", g.away_key, g.home_key, g.away_pts, g.home_pts)):
            tg.append(dict(game_id=g.game_id, season="s", date=g.date, side=side, team_key=t, opp_key=o, PTS=p,
                           opp_pts=q, win=p > q, net=float(p - q), efg=0.5, tov_pct=0.1, orb_pct=0.3, ftr=0.2))
    m = build_game_matrix(games, pd.DataFrame(tg), min_prior_games=0, seed=1).set_index("game_id")
    row = m.loc[5]
    a_is_team_a = row.team_a == "a"
    winpct_a = 1.0
    winpct_c = 0.0
    expected = (winpct_a - winpct_c) if a_is_team_a else (winpct_c - winpct_a)
    assert row.winpct_to_date_diff == pytest.approx(expected)


def test_orientation_balanced():
    games, tg = synthetic_league(n_games=200, seed=3)
    m = build_game_matrix(games, tg, min_prior_games=0)
    assert m.game_id.is_unique
    assert 0.4 <= m.y.mean() <= 0.6
    home_as_a = (m.merge(games[["game_id", "home_key"]], on="game_id").eval("team_a == home_key")).mean()
    assert 0.4 <= home_as_a <= 0.6


def test_min_prior_games():
    games, tg = synthetic_league(n_games=60, seed=5)
    m = build_game_matrix(games, tg, min_prior_games=3)
    full = build_game_matrix(games, tg, min_prior_games=0)
    assert len(m) < len(full)
    assert m.columns.tolist()[:6] == ["game_id", "date", "season", "team_a", "team_b", "y"]
    assert set(WIN_FEATURES) <= set(m.columns)


def test_walk_forward_chronological():
    games, tg = synthetic_league(n_games=150, seed=7)
    m = build_game_matrix(games, tg)
    res = walk_forward_cv(m, make_models(), n_folds=5)
    assert set(res.model) >= {"logreg", "rf", "baseline_elo", "baseline_winpct"}
    assert res.fold.nunique() == 5
    assert (pd.to_datetime(res.train_end) < pd.to_datetime(res.test_start)).all()
    assert res.accuracy.between(0, 1).all()


def test_baseline_predict():
    df = pd.DataFrame({"elo_diff": [10, -5, 0], "winpct_to_date_diff": [0.0, 0.2, -0.1]})
    assert baseline_predict(df, "elo").tolist() == [1.0, 0.0, 0.5]
    assert baseline_predict(df, "winpct").tolist() == [0.5, 1.0, 0.0]


def test_bootstrap_metrics_contains_point():
    rng = np.random.default_rng(0)
    y = rng.integers(0, 2, 200)
    p = np.clip(y * 0.7 + rng.normal(0.15, 0.2, 200), 0, 1)
    out = bootstrap_metrics(y, p, n_boot=300)
    for key in ("accuracy", "auc", "brier"):
        assert out[key].lo <= out[key].est <= out[key].hi


def test_pythag_recovers_exponent():
    rng = np.random.default_rng(1)
    pf = rng.uniform(1800, 2300, 40)
    pa = rng.uniform(1800, 2300, 40)
    p = pf ** 14 / (pf ** 14 + pa ** 14)
    st = pd.DataFrame({"PF": pf, "PA": pa, "W": 24 * p, "L": 24 * (1 - p)})
    res = fit_pythagorean(st, n_boot=200)
    assert res["exponent"] == pytest.approx(14, abs=0.5)
    assert res["exponent_ci"].lo <= res["exponent"] <= res["exponent_ci"].hi
    assert res["r2"] > 0.95 and res["mae"] < res["mae_13_91"] + 1e-9
    assert res["r2_ci"].lo <= res["r2"] <= res["r2_ci"].hi


def test_explanatory_signs():
    _, tg = synthetic_league(n_games=200, seed=11)
    out = fit_explanatory(tg, n_boot=200).set_index("feature")
    assert out.loc["efg", "coef"] > 0 and out.loc["efg", "lo"] > 0
    assert set(out.columns) >= {"coef", "lo", "hi", "perm_importance", "perm_lo", "perm_hi"}


def test_run_models_smoke(tmp_path):
    import json
    from src.models import run_models
    proc, rep, mod = tmp_path / "p", tmp_path / "r", tmp_path / "m"
    proc.mkdir()
    games, tg = synthetic_league(n_games=120, seed=2)
    games.rename(columns={"home_key": "home_team_key", "away_key": "away_team_key"}).to_csv(proc / "games.csv", index=False)
    tg.to_csv(proc / "team_games.csv", index=False)
    rng = np.random.default_rng(0)
    n = 60
    ps = pd.DataFrame({f: rng.normal(size=n) for f in ["pts36", "reb36", "ast36", "stl36", "blk36", "tpa_rate", "ftr", "ts_pct"]})
    ps = ps.assign(MIN_total=300, eligible=True, player_id=[f"p{i}" for i in range(n)], season="2025-2026",
                   is_import=rng.random(n) < 0.3, position=rng.choice(["PG", "SG", "SF", "PF", "C"], n))
    ps.to_csv(proc / "players_season.csv", index=False)
    pd.DataFrame({"PF": [2000, 1900, 2100], "PA": [1900, 2000, 1950], "W": [15, 9, 16], "L": [9, 15, 8]}).to_csv(
        proc / "standings_hist.csv", index=False)
    run_models(proc, rep, mod, n_boot=50, stability_boot=10)
    metrics = json.loads((rep / "metrics.json").read_text(encoding="utf-8"))
    assert {"kmeans", "win_cv", "win_bootstrap", "pythagorean", "explanatory"} <= set(metrics)
    assert (rep / "clusters.csv").exists() and (rep / "explanatory.csv").exists()
    assert (mod / "logreg.joblib").exists() and (mod / "kmeans.joblib").exists()
