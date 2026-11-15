from pathlib import Path

import numpy as np
import pandas as pd

from src import imports as IM

ROOT = Path(__file__).resolve().parents[1]
P = ROOT / "data" / "processed"


def _real():
    ps = pd.read_csv(P / "players_season.csv")
    pg = pd.read_csv(P / "player_games.csv")
    bg = pd.read_csv(ROOT / "data" / "raw" / "import_background_raw.csv")
    return ps, IM.import_table(ps, pg, bg)


def test_compare_groups_detects_clear_difference():
    rng = np.random.default_rng(0)
    df = pd.DataFrame({"x": np.r_[rng.normal(20, 1, 30), rng.normal(10, 1, 30)]})
    g = pd.Series([True] * 30 + [False] * 30)
    r = IM.compare_groups(df, g, {"x": "x"}, n_boot=300).iloc[0]
    assert r.clear and 8 < r["diff"] < 12 and r.diff_lo < r["diff"] < r.diff_hi


def test_position_concentration_synthetic():
    ps = pd.DataFrame({"season": ["s"] * 4, "position": ["C", "C", "PG", "PG"], "is_import": [True, False, False, False],
                       "MIN_total": [100, 0, 100, 100]})
    r = IM.position_concentration(ps, n_boot=100).iloc[0]
    assert r.pos_share == 1.0 and abs(r.overall_share - 1 / 3) < 1e-9 and abs(r["diff"] - 2 / 3) < 1e-9


def test_retention_counts_name_order_fix():
    ps, im = _real()
    ret = IM.retention(ps, im)
    assert ret.stayed.sum() == 8  # C2c засварын дараа: Ian Miller, McKenzie Moore, Emmanuel Ejesu орно
    assert {"MILLER Ian", "MCKENZIE Moore", "EMMANUEL Ejesu"} <= set(ret.loc[ret.stayed, "player_name"])


def test_background_identity_checked_and_ages_plausible():
    _, im = _real()
    assert im.age.dropna().between(18, 45).all()
    moore = im[im.player_name.str.contains("Moore", case=False)]
    assert (moore.age.dropna() >= 32).all()  # MBA-ийн 2002 гэсэн алдааг ShamSports-ийн 1992 засна


def test_hypotheses_table_is_consistent():
    ps, im = _real()
    h = IM.hypotheses(ps, im)
    assert set(h.hid) == {"H6", "H7", "H8", "H9"}
    assert ((h.lo <= h.estimate) & (h.estimate <= h.hi)).all()
    ok = h.verdict.map({"Батлагдсан": lambda r: r.lo > 0, "Няцаагдсан": lambda r: r.hi < 0,
                        "Баттай биш": lambda r: r.lo <= 0 <= r.hi})
    assert all(f(r) for f, (_, r) in zip(ok, h.iterrows()))


def test_similar_players_excludes_self_and_is_sorted():
    _, im = _real()
    idx = im.dropna(subset=list(IM.SIM_FEATURES)).index[0]
    sim = IM.similar_players(im, idx, k=5)
    assert len(sim) == 5 and im.loc[idx, "player_id"] not in set(sim.player_id)
    assert sim.distance.is_monotonic_increasing and sim.player_id.is_unique
