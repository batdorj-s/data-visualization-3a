import numpy as np
import pandas as pd

from src.inplay import build_states, by_minute, grouped_cv, leader_rule, win_prob


def _toy(n_games=40, seed=0):
    rng = np.random.default_rng(seed)
    ev, games = [], []
    for gid in range(n_games):
        strength = rng.normal(0, 1)
        margin, seq = 0, 0
        for t in range(0, 2400, 30):
            margin += int(rng.normal(strength * 0.6, 2))
            seq += 1
            ev.append({"game_id": gid, "seq": seq, "elapsed": t, "margin": margin})
        games.append({"game_id": gid, "season": "s", "elo_pre_home": 1500 + 50 * strength, "elo_pre_away": 1500,
                      "home_pts": 80 + max(margin, 0), "away_pts": 80 + max(-margin, 0) + (margin == 0)})
    return pd.DataFrame(ev), pd.DataFrame(games)


def test_states_one_row_per_game_minute():
    e, g = _toy()
    s = build_states(e, g)
    assert len(s) == 40 * 40 and s.groupby("game_id").minute.nunique().eq(40).all()


def test_grouped_cv_improves_late_in_game():
    e, g = _toy()
    m = by_minute(grouped_cv(build_states(e, g)), n_boot=50).set_index("minute")
    assert m.loc[39, "acc_model"] >= m.loc[0, "acc_model"]
    assert (m.lo_model <= m.acc_model).all() and (m.acc_model <= m.hi_model).all()


def test_leader_rule_breaks_ties_with_elo():
    df = pd.DataFrame({"margin": [3, -2, 0, 0], "elo_diff": [0, 0, 10, -10]})
    assert list(leader_rule(df)) == [1, 0, 1, 0]


def test_win_prob_monotone_in_margin():
    params = {"intercept": 0.0, "coef": {"margin": 0.05, "margin_scaled": 0.8, "elo_diff": 0.4, "elo_x_time": 0.3}}
    p = win_prob(params, [-10, 0, 10], [300, 300, 300], [0, 0, 0])
    assert p[0] < p[1] < p[2] and abs(p[1] - 0.5) < 1e-9


def test_finalize_sets_result_at_buzzer():
    from src.inplay import finalize
    assert list(finalize([0.5, 0.6], 1)) == [0.5, 1.0]
    assert list(finalize([0.5, 0.6], -3)) == [0.5, 0.0]
    assert list(finalize([0.5, 0.6], 0)) == [0.5, 0.6]
