from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from src import insights as I

P = Path(__file__).resolve().parents[1] / "data" / "processed"


def _ev(gid, seq, period, elapsed, typ, side=None, pid=None, text="", made=None, points=0, margin=0):
    return {"game_id": gid, "seq": seq, "period": period, "elapsed": elapsed, "type": typ, "side": side,
            "player_id": pid, "text": text, "made": made, "points": points, "margin": margin}


def test_lineup_stints_tracks_substitutions():
    ev = [_ev(1, i, 1, 0, "sub", "home", f"h{i}", "substitution in") for i in range(5)]
    ev += [_ev(1, 10, 1, 100, "2pt", "home", "h0", made=True, points=2),
           _ev(1, 11, 1, 100, "sub", "home", "h0", "substitution out"),
           _ev(1, 12, 1, 100, "sub", "home", "x", "substitution in"),
           _ev(1, 13, 1, 300, "end")]
    st = I.lineup_stints(pd.DataFrame(ev))
    home = st[st.side == "home"]
    assert list(home.seconds) == [100, 200]
    assert home.players.iloc[0] == ("h0", "h1", "h2", "h3", "h4") and "x" in home.players.iloc[1]
    assert I.lineup_coverage(home) == 1.0


def test_imports_on_court_counts_time_shares():
    st = pd.DataFrame({"game_id": [1, 1, 1], "period": [1, 1, 1], "side": ["home"] * 3,
                       "players": [("a", "b", "c", "d", "e"), ("a", "b", "c", "d", "f"), ("a", "b")],
                       "seconds": [300, 100, 999]})
    out = I.imports_on_court(st, {"a": True, "f": True}, pd.DataFrame({"game_id": [1], "season": ["s"]}))
    assert dict(zip(out.k, out.share)) == {1: 0.75, 2: 0.25}  # 5-аас өөр тоглогчтой хэсэг тооцогдохгүй
    assert out.mean_k.iloc[0] == pytest.approx(1.25)


def test_lead_safety_and_comebacks():
    ev = []
    for gid, half, final in ((1, 8, 5), (2, 8, -2), (3, -12, -20)):
        ev += [_ev(gid, 1, 1, 0, "start"), _ev(gid, 2, 2, 1190, "2pt", margin=half),
               _ev(gid, 3, 4, 2400, "end", margin=final)]
    pbp = pd.DataFrame(ev)
    games = pd.DataFrame({"game_id": [1, 2, 3], "home_pts": [85, 78, 60], "away_pts": [80, 80, 80]})
    ls = I.lead_safety(pbp, games)
    half = ls[ls.checkpoint == "Хагас"].set_index("bin")
    assert half.loc["7–10", "n"] == 2 and half.loc["7–10", "est"] == 0.5
    assert half.loc["11–15", "est"] == 1.0
    cb = I.comebacks(pbp).set_index("game_id")
    assert cb.loc[2, "deficit"] == 8 and cb.loc[2, "trailed_at_half"] and cb.loc[1, "deficit"] == 0


def test_usage_sums_to_one_per_team():
    pg = pd.DataFrame({"game_id": [1] * 5, "team_key": ["t"] * 5, "team": ["T"] * 5, "phase": ["regular"] * 5,
                       "season": ["s"] * 5, "player_id": list("abcde"), "name": list("ABCDE"),
                       "is_import": [True, False, False, False, False], "MIN": [40] * 5, "PTS": [30, 10, 10, 10, 10],
                       "FGA": [20, 5, 5, 5, 5], "FTA": [0] * 5, "TOV": [0] * 5})
    u = I.usage_table(pg, min_minutes=0)
    assert u.usage.sum() == pytest.approx(1.0)  # 5 тоглогч бүтэн тоглосон бол ачааллын нийлбэр 100%
    assert u.set_index("player_id").loc["a", "usage"] == pytest.approx(0.5)
    assert u.set_index("player_id").loc["a", "ts"] == pytest.approx(0.75)


def test_real_data_findings_hold():
    games = pd.read_csv(P / "games.csv")
    pbp = pd.read_csv(P / "pbp.csv.gz")
    pg = pd.read_csv(P / "player_games.csv")
    stints = I.lineup_stints(pbp)
    assert I.lineup_coverage(stints) > 0.97
    ioc = I.imports_on_court(stints, pg.groupby("player_id").is_import.max().to_dict(), games)
    m = ioc.drop_duplicates(["season", "period"]).set_index(["season", "period"]).mean_k
    # 2025–26: 2, 3-р үед 1, 4-р үеэс илүү гадаад тоглогч талбай дээр байсан
    assert m["2025-2026", 2] > m["2025-2026", 1] + 0.3 and m["2025-2026", 3] > m["2025-2026", 4] + 0.3
    ls = I.lead_safety(pbp, games)
    half = ls[ls.checkpoint == "Хагас"].set_index("bin").est
    assert half["16+"] > half["1–3"]
    cb = I.comebacks(pbp)
    assert 0.1 < (cb.deficit >= 10).mean() < 0.35


def test_distance_curve_and_assisted_share_real():
    shots = pd.read_csv(P / "shots.csv")
    assists = pd.read_csv(P / "assists.csv")
    d = I.distance_curve(shots, n_boot=100)
    assert d.n.sum() == int(shots.location_ok.sum()) and (d.lo <= d.pps).all() and (d.pps <= d.hi).all()
    assert d.iloc[0].pps == d.pps.max()  # сагсны доор хамгийн үр ашигтай
    a = I.assisted_share(shots, assists)
    by_zone = a.groupby("zone", observed=True).apply(lambda g: (g.est * g.n).sum() / g.n.sum(), include_groups=False)
    assert by_zone["Булангийн 3"] > by_zone["Дунд зай"]


def test_season_stability_style_beats_efficiency():
    st = I.season_stability(pd.read_csv(P / "players_season.csv")).set_index("stat")
    assert st.loc["reb36", "r"] > 0.6 and st.loc["tpa_rate", "r"] > 0.6
    assert st.loc["ts_pct", "hi"] < st.loc["reb36", "lo"]  # оновчийн хүрээ хэв маягийнхаас бүхэлдээ доогуур
    assert (st.n >= 5).all() and np.isfinite(st.r).all()
