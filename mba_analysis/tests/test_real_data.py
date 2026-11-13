"""Commit хийгдсэн бодит snapshot дээрх бүрэн бүтэн байдлын шалгалт."""
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
P, R, D = ROOT / "data" / "processed", ROOT / "reports", ROOT / "dashboard" / "data"


def test_every_regular_season_player_game_maps_to_a_season_row():
    ps = pd.read_csv(P / "players_season.csv")
    pg = pd.read_csv(P / "player_games.csv")
    pg = pg[pg.phase == "regular"]
    keys = set(zip(ps.player_id, ps.season))
    missing = [k for k in zip(pg.player_id, pg.season) if k not in keys]
    assert missing == []


def test_import_flag_is_a_person_attribute():
    ps = pd.read_csv(P / "players_season.csv")
    pg = pd.read_csv(P / "player_games.csv")
    person = ps.groupby("player_id").is_import.max()
    assert "is_import" in pg.columns
    assert (pg.is_import.astype(bool) == pg.player_id.map(person).fillna(False).astype(bool)).all()


def test_season_totals_match_mba_ppg_for_traded_players():
    ps = pd.read_csv(P / "players_season.csv")
    traded = ps[ps.traded.astype(bool) & ps.eligible.astype(bool)]
    assert len(traded) > 0
    assert ((traded.PTS_total / traded.GP_games - traded.PPG).abs() < 0.2).all()


def test_dashboard_player_ci_is_unique_per_player_season():
    ci = pd.read_parquet(D / "player_ci.parquet")
    assert not ci.duplicated(["player_id", "season", "metric"]).any()


def test_clusters_carry_team_key():
    cl = pd.read_csv(R / "clusters.csv")
    assert "team_key" in cl.columns
    assert not cl.duplicated(["player_id", "season", "team_key"]).any()
