import numpy as np
import pandas as pd
import pytest

from src.clean import (
    CleaningLog,
    UnmappedTeamError,
    dedupe,
    drop_dnp,
    fix_zero_attempt_pct,
    flag_eligible,
    map_teams,
    normalize_venue,
    split_made_att,
    stage_to_phase,
    validate_ppg,
)

ALIASES = pd.DataFrame({
    "raw_name": ["SELENGE BODONS", "Selenge Bodons", "XAC BRONCOS"],
    "season": ["*", "*", "*"],
    "team_key": ["selenge_bodons", "selenge_bodons", "khasin_khuleguud"],
    "canonical_name": ["Selenge Bodons", "Selenge Bodons", "Khasin Khuleguud"],
    "successor_of": ["", "", ""],
    "source": ["", "", ""],
})


def test_map_teams_case_variants():
    df = pd.DataFrame({"team_name": ["SELENGE BODONS", "Selenge Bodons"], "season": ["2025-2026", "2026-2027"]})
    out = map_teams(df, "team_name", ALIASES)
    assert out.team_key.tolist() == ["selenge_bodons", "selenge_bodons"]


def test_map_teams_unmapped_raises():
    df = pd.DataFrame({"team_name": ["Unknown FC"], "season": ["2025-2026"]})
    with pytest.raises(UnmappedTeamError, match="Unknown FC"):
        map_teams(df, "team_name", ALIASES)


def test_zero_attempts_pct_nan():
    df = pd.DataFrame({"TPA": [0, 3], "TP_pct": [0.0, 0.0], "FGA": [5, 0], "FG_pct": [40.0, 0.0]})
    out = fix_zero_attempt_pct(df)
    assert np.isnan(out.TP_pct[0]) and out.TP_pct[1] == 0.0
    assert out.FG_pct[0] == 40.0 and np.isnan(out.FG_pct[1])


def test_split_made_att():
    df = pd.DataFrame({"FG": ["24-70", None], "TP": ["8-28", None], "FT": ["21-24", None]})
    out = split_made_att(df)
    assert (out.FGM[0], out.FGA[0], out.TPM[0], out.TPA[0], out.FTM[0], out.FTA[0]) == (24, 70, 8, 28, 21, 24)
    assert pd.isna(out.FGM[1]) and pd.isna(out.FGA[1])
    assert "FG" not in out.columns


def test_drop_dnp_logs_count():
    log = CleaningLog()
    df = pd.DataFrame({"dnp": [False, True, False], "PTS": [10, None, 3]})
    out = drop_dnp(df, log)
    assert len(out) == 2
    row = log.to_frame().iloc[-1]
    assert (row.step, row.rows_before, row.rows_after) == ("C4", 3, 2)


def test_dedupe_keeps_traded_player_rows():
    df = pd.DataFrame({
        "player_id": ["p1", "p1", "p2", "p2"],
        "season": ["2025-2026"] * 4,
        "team_key": ["a", "b", "c", "c"],
        "PPG": [10.0, 12.0, 5.0, 5.0],
    })
    out = dedupe(df, ["player_id", "season", "team_key"])
    assert len(out) == 3
    assert set(out[out.player_id == "p1"].team_key) == {"a", "b"}


def test_stage_to_phase():
    assert stage_to_phase("Regular season") == "regular"
    assert stage_to_phase("Playoffs") == "playoff"
    assert stage_to_phase("Finals") == "playoff"
    with pytest.raises(ValueError):
        stage_to_phase("Exhibition")


def test_normalize_venue_variants():
    assert normalize_venue("М Банк арена") == normalize_venue("M BANK ARENA") == "М Банк Арена"
    assert normalize_venue("M Банк Арена") == normalize_venue("М Банк Арена") == "М Банк Арена"
    assert normalize_venue("DARKHAN UNITED ARENA") == normalize_venue("Darkhan united arena") == "Дархан Юнайтед Арена"
    assert normalize_venue("МҮЭСТО") == "МҮЭСТО"


def test_flag_eligible():
    out = flag_eligible(pd.DataFrame({"GP": [4, 5, 20]}), min_gp=5)
    assert out.eligible.tolist() == [False, True, True]


def test_validate_ppg_flags_gap():
    season = pd.DataFrame({"player_id": ["p1", "p2"], "season": ["s", "s"], "team_key": ["a", "a"],
                           "PPG": [20.0, 10.0], "GP": [2, 2]})
    games = pd.DataFrame({"player_id": ["p1", "p1", "p2", "p2"], "season": ["s"] * 4, "team_key": ["a"] * 4,
                          "PTS": [19, 20, 10, 10]})
    out = validate_ppg(season, games, tol=0.2).set_index("player_id")
    assert bool(out.loc["p1", "flag"]) is True
    assert bool(out.loc["p2", "flag"]) is False
    assert out.loc["p1", "ppg_games"] == 19.5


def test_assign_player_ids_links_across_seasons():
    from src.clean import assign_player_ids
    ps = pd.DataFrame({
        "season": ["2025-2026", "2026-2027", "2025-2026", "2026-2027"],
        "player_slug": ["scrubb-jay", "scrubb-jayden-amari", "smith-kendall-2", "smith-donovan"],
        "player_name": ["SCRUBB Jay", "SCRUBB Jayden Amari", "SMITH Kendall", "SMITH Donovan"],
        "team_key": ["selenge_bodons", "selenge_bodons", "bch_knights", "bch_knights"],
    })
    out, matches = assign_player_ids(ps)
    ids = dict(zip(out.player_slug, out.player_id))
    assert ids["scrubb-jay"] == ids["scrubb-jayden-amari"] == "scrubb-jayden-amari"
    assert ids["smith-kendall-2"] == "smith-kendall-2"
    assert matches.left_id.tolist() == ["scrubb-jay"]


def test_assign_player_ids_respects_reject_override():
    from src.clean import assign_player_ids
    ps = pd.DataFrame({"season": ["2025-2026", "2026-2027"], "player_slug": ["a-x", "a-xy"],
                       "player_name": ["AAA X", "AAA Xy"], "team_key": ["t", "t"]})
    over = pd.DataFrame({"left_id": ["a-x"], "right_id": ["a-xy"], "decision": ["reject"]})
    out, _ = assign_player_ids(ps, over)
    assert out.player_id.tolist() == ["a-x", "a-xy"]


def test_link_national_team():
    from src.clean import link_national_team
    nat = pd.DataFrame({"first": ["Binderiya", "Orgil"], "last": ["Sandagdorj", "Khishigbaatar"]})
    ps = pd.DataFrame({"season": ["2025-2026"], "player_id": ["sandagdorj-binderyaa"],
                       "player_name": ["SANDAGDORJ Binderyaa"]})
    out = link_national_team(nat, ps)
    assert out.matched_player_id.tolist()[0] == "sandagdorj-binderyaa"
    assert pd.isna(out.matched_player_id.tolist()[1])


def test_fix_implausible_values():
    from src.clean import fix_implausible_values
    log = CleaningLog()
    df = pd.DataFrame({"season": ["2026-2027"] * 4, "birth_year": [1900, 2025, 1995, None],
                       "height_cm": [202, 150, 195, 190]})
    out = fix_implausible_values(df, log)
    assert pd.isna(out.birth_year[0]) and pd.isna(out.birth_year[1]) and out.birth_year[2] == 1995
    assert pd.isna(out.height_cm[1]) and out.height_cm[0] == 202
    assert log.to_frame().iloc[-1].step == "C12"
    assert "3" in log.to_frame().iloc[-1].note


def _pg(rows):
    return pd.DataFrame(rows, columns=["player_id", "season", "team_key", "game_id", "PTS", "FGM", "FGA", "TPM", "TPA",
                                       "FTM", "FTA"])


def test_attach_totals_traded_player_uses_all_teams():
    from src.clean import attach_totals
    ps = pd.DataFrame({"player_id": ["p1"], "season": ["s"], "team_key": ["b"], "GP": [5], "PPG": [12.0]})
    pg = _pg([("p1", "s", "a", 1, 10, 4, 8, 0, 1, 2, 2), ("p1", "s", "a", 2, 10, 4, 8, 0, 1, 2, 2),
              ("p1", "s", "b", 3, 20, 8, 15, 1, 3, 3, 4), ("p1", "s", "b", 4, 10, 4, 9, 0, 1, 2, 2),
              ("p1", "s", "b", 5, 10, 4, 9, 0, 1, 2, 2)])
    out = attach_totals(ps, pg).iloc[0]
    assert (out.PTS_total, out.GP_games, out.FGA) == (60, 5, 49)
    assert bool(out.traded) is True


def test_attach_totals_two_season_rows_stay_per_team():
    from src.clean import attach_totals
    ps = pd.DataFrame({"player_id": ["p2", "p2"], "season": ["s", "s"], "team_key": ["a", "b"], "GP": [1, 1],
                       "PPG": [10.0, 20.0]})
    pg = _pg([("p2", "s", "a", 1, 10, 4, 8, 0, 1, 2, 2), ("p2", "s", "b", 2, 20, 8, 15, 1, 3, 3, 4)])
    out = attach_totals(ps, pg).set_index("team_key")
    assert out.loc["a", "PTS_total"] == 10 and out.loc["b", "PTS_total"] == 20
    assert out.GP_games.tolist() == [1, 1]


def test_check_score_consistency_flags_mismatches():
    from src.clean import check_score_consistency
    games = pd.DataFrame({"game_id": [1, 2, 3], "home_pts": [80, 90, 70], "away_pts": [70, 85, 60],
                          "quarters_home": ["20|20|20|20", "20|20|20|20", "20|20|20|10"],
                          "quarters_away": ["20|20|20|10", "20|20|20|25", "15|15|15|15"]})
    tg = pd.DataFrame({"game_id": [1, 1, 2, 2, 3, 3], "side": ["home", "away"] * 3,
                       "PTS": [80, 70, 88, 85, 70, 60]})
    out = check_score_consistency(games, tg).set_index("game_id")
    assert list(out.index) == [2]
    assert out.loc[2, "title_vs_box"] and out.loc[2, "title_vs_quarters"]
    assert out.loc[2, "box_home"] == 88
