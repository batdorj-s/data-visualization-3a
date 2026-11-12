import numpy as np
import pandas as pd
import pytest

from src.features import add_player_categories, efg_pct, four_factors, per36, possessions, pythag, ts_pct


def game141() -> pd.DataFrame:
    base = {"game_id": 141, "season": "2025-2026"}
    home = dict(team_key="khasin_khuleguud", side="home", PTS=77, FGM=24, FGA=70, TPM=8, TPA=28, FTM=21, FTA=24,
                OREB=17, DREB=33, TOV=11)
    away = dict(team_key="selenge_bodons", side="away", PTS=69, FGM=21, FGA=68, TPM=8, TPA=33, FTM=19, FTA=25,
                OREB=13, DREB=25, TOV=13)
    return pd.DataFrame([{**base, **home}, {**base, **away}])


def test_four_factors_game_141_home():
    ff = four_factors(game141()).set_index("side")
    h = ff.loc["home"]
    assert h.efg == pytest.approx(0.4000, abs=1e-4)
    assert h.poss == pytest.approx(74.56, abs=1e-2)
    assert h.tov_pct == pytest.approx(0.1475, abs=1e-4)
    assert h.orb_pct == pytest.approx(0.4048, abs=1e-4)
    assert h.ftr == pytest.approx(0.3000, abs=1e-4)
    assert h.ortg == pytest.approx(103.27, abs=1e-2)
    assert h.drtg == pytest.approx(87.34, abs=1e-2)
    assert h.net == pytest.approx(103.27 - 87.34, abs=2e-2)
    assert (h.opp_key, h.win) == ("selenge_bodons", True)


def test_four_factors_game_141_away():
    a = four_factors(game141()).set_index("side").loc["away"]
    assert a.efg == pytest.approx(0.3676, abs=1e-4)
    assert a.poss == pytest.approx(79.0, abs=1e-2)
    assert a.tov_pct == pytest.approx(0.1646, abs=1e-4)
    assert a.orb_pct == pytest.approx(0.2826, abs=1e-4)
    assert a.ftr == pytest.approx(0.2794, abs=1e-4)


def test_ts_pct_value():
    assert ts_pct(77, 70, 24) == pytest.approx(0.4779, abs=1e-4)


def test_rates_zero_attempts_are_nan():
    assert np.isnan(ts_pct(0, 0, 0))
    assert np.isnan(efg_pct(0, 0, 0))
    assert np.isnan(per36(5, 0))
    assert np.isnan(possessions(0, 0, 0, 0))
    g = game141()
    g.loc[0, ["FGA", "FGM", "TPM", "FTA", "FTM", "OREB", "TOV", "PTS"]] = 0
    ff = four_factors(g)
    num = ff.select_dtypes("number").to_numpy(dtype=float)
    assert np.isinf(num).sum() == 0
    assert np.isnan(ff.set_index("side").loc["home", "efg"])


def test_vectorized_rates():
    out = ts_pct(pd.Series([77, 0]), pd.Series([70, 0]), pd.Series([24, 0]))
    assert out.iloc[0] == pytest.approx(0.4779, abs=1e-4) and np.isnan(out.iloc[1])


def test_categories():
    df = pd.DataFrame({"PPG": [4.9, 12.0, 20.0, 7.0], "position": ["PG", "PF", "C", None], "birth_year": [1995, 2000, 1990, None]})
    out = add_player_categories(df, season_start_year=2025)
    assert out.scorer_tier.tolist() == ["Бага", "Өндөр", "Од", "Дунд"]
    assert out.pos_group.tolist()[:3] == ["Guard", "Forward", "Center"]
    assert pd.isna(out.pos_group.iloc[3])
    assert out.age.iloc[0] == 30 and pd.isna(out.age.iloc[3])


def test_pythag_erdenet_2023_24():
    assert pythag(1878, 1693) == pytest.approx(0.8088, abs=1e-4)
