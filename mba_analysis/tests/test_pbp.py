import numpy as np
import pandas as pd
import pytest

from src.pbp import ZONES, clean_pbp, link_assists, shot_geometry, shot_zone


def test_geometry_folds_both_halves_to_left_hoop():
    # Хоёр сагсны төв: зүүн (1.575 м, 7.5 м), баруун нь толин тусгал
    g = shot_geometry([1.575 * 22.75, 637 - 1.575 * 22.75], [175, 175])
    assert np.allclose(g.dist, 0, atol=0.05)
    assert (g.court_x <= 14).all()


def test_zones():
    z = shot_zone([1.6, 4.0, 8.0, 1.0, 8.5], [7.5, 8.0, 7.5, 0.6, 7.5], [0.1, 2.5, 6.4, 6.9, 6.9],
                  [False, False, False, True, True])
    assert list(z) == ZONES


def _games():
    return pd.DataFrame({"game_id": [1], "home_team_key": ["a"], "away_team_key": ["b"]})


def _pg():
    return pd.DataFrame({"player_slug": ["p1", "p2", "q1"], "player_id": ["P1", "P2", "Q1"]})


def test_clean_pbp_elapsed_and_margin():
    pbp = pd.DataFrame({"game_id": [1, 1, 1], "seq": [1, 2, 3], "period": [1, 2, 5],
                        "clock": ["10:00", "05:30", "04:00"], "side": [None, "home", "away"],
                        "player_slug": [None, "p1", "q1"], "type": ["start", "2pt", "3pt"], "text": ["", "", ""],
                        "made": [None, True, True], "points": [0, 2, 3], "home": [0, 2, None], "away": [0, 0, 3]})
    e, stats = clean_pbp(pbp, _pg(), _games())
    assert list(e.elapsed) == [0, 600 + 270, 2400 + 60]
    assert list(e.margin) == [0, 2, -1]  # хоосон home оноог өмнөхөөр нөхнө
    assert list(e.team_key.fillna("-")) == ["-", "a", "b"] and stats["unlinked_players"] == 0


def test_link_assists_before_or_after_shot():
    e = pd.DataFrame({"game_id": [1] * 5, "seq": [1, 2, 3, 4, 5], "side": ["home", "home", "away", "away", "home"],
                      "team_key": ["a", "a", "b", "b", "a"], "player_id": ["P1", "P2", "Q1", "Q2", "P1"],
                      "type": ["2pt", "ast", "ast", "3pt", "2pt"], "made": [True, None, None, True, False],
                      "points": [2, 0, 0, 3, 0]})
    out, stats = link_assists(e)
    assert list(zip(out.passer_id, out.scorer_id, out.three)) == [("P2", "P1", False), ("Q1", "Q2", True)]
    assert stats["share"] == pytest.approx(1.0)
