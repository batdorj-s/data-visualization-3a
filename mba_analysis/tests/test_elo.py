import pandas as pd
import pytest

from src.elo import expected, run_elo


def games(rows):
    return pd.DataFrame(rows, columns=["game_id", "season", "date", "home_key", "away_key", "home_pts", "away_pts"])


def test_equal_ratings_home_win():
    out = run_elo(games([(1, "2025-2026", "2025-10-01", "a", "b", 80, 70)])).iloc[0]
    assert (out.elo_pre_home, out.elo_pre_away) == (1500, 1500)
    assert out.elo_post_home == pytest.approx(1510.0)
    assert out.elo_post_away == pytest.approx(1490.0)


def test_upset_loss_from_1600():
    assert expected(1600, 1400) == pytest.approx(1 / (1 + 10 ** (-0.5)))
    g = games([(i, "2025-2026", f"2025-10-{i:02d}", "a", "x", 90, 70) for i in range(1, 30)])
    out = run_elo(g)
    ra = out.iloc[-1].elo_post_home
    rb = out.iloc[-1].elo_post_away
    upset = games([(99, "2025-2026", "2025-11-30", "a", "x", 60, 70)])
    after = run_elo(pd.concat([g, upset], ignore_index=True)).iloc[-1]
    assert after.elo_pre_home == pytest.approx(ra)
    assert after.elo_post_home == pytest.approx(ra + 20 * (0 - expected(ra, rb)))


def test_1600_vs_1400_exact():
    from src.elo import update
    new_a, new_b = update(1600, 1400, a_won=False, k=20)
    assert new_a == pytest.approx(1584.805, abs=1e-3)
    assert new_b == pytest.approx(1400 + (1600 - new_a))


def test_season_carryover_and_new_team():
    g = games([
        (1, "2025-2026", "2025-10-01", "a", "b", 80, 70),
        (2, "2026-2027", "2026-10-01", "a", "c", 80, 70),
    ])
    out = run_elo(g).set_index("game_id")
    post_a = out.loc[1, "elo_post_home"]
    assert out.loc[2, "elo_pre_home"] == pytest.approx(0.75 * post_a + 0.25 * 1500)
    assert out.loc[2, "elo_pre_away"] == 1500


def test_successor_inherits_rating():
    g = games([
        (1, "2025-2026", "2025-10-01", "old", "b", 80, 70),
        (2, "2026-2027", "2026-10-01", "new", "b", 80, 70),
    ])
    out = run_elo(g, successors={"new": "old"}).set_index("game_id")
    assert out.loc[2, "elo_pre_home"] == pytest.approx(0.75 * out.loc[1, "elo_post_home"] + 0.25 * 1500)


def test_pre_rating_independent_of_own_result():
    base = [(1, "2025-2026", "2025-10-01", "a", "b", 80, 70), (2, "2025-2026", "2025-10-05", "a", "b", 70, 80)]
    flipped = [base[0], (2, "2025-2026", "2025-10-05", "a", "b", 90, 60)]
    p1 = run_elo(games(base)).set_index("game_id").loc[2, ["elo_pre_home", "elo_pre_away"]]
    p2 = run_elo(games(flipped)).set_index("game_id").loc[2, ["elo_pre_home", "elo_pre_away"]]
    assert p1.tolist() == p2.tolist()
