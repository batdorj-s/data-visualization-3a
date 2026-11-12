import json
from pathlib import Path

from src.wiki import clean_wikilink, parse_champions, parse_current_teams, parse_fiba_roster, parse_sports_table

GEO = Path(__file__).resolve().parents[1] / "data" / "raw" / "geo" / "mng_adm1.geojson"


def test_clean_wikilink():
    assert clean_wikilink("[[Bishrelt Metal]]") == "Bishrelt Metal"
    assert clean_wikilink("[[Darkhan (city)|Darkhan]]") == "Darkhan"
    assert clean_wikilink(" BCH Garid <ref>x</ref>") == "BCH Garid"


def test_standings_2023_24(wiki):
    df = parse_sports_table(wiki("season_2023_24"))
    assert len(df) == 13
    em = df.set_index("team_raw").loc["Erdenet Miners"]
    assert (em.W, em.L, em.PF, em.PA) == (19, 4, 1878, 1693)
    sh = df.set_index("team_raw").loc["Shutis Sharks"]
    assert (sh.W, sh.L) == (5, 17)
    assert "Bishrelt Metal" in set(df.team_raw)


def test_fiba_roster(wiki):
    df = parse_fiba_roster(wiki("national_team"))
    assert len(df) == 12
    r8 = df.set_index("num").loc[8]
    assert (r8.first, r8["last"], r8.pos) == ("Erdenetsogt", "Ochirbat", "G")
    assert r8.birth_date == "1995-01-14" and r8.club == "BCH Knights"
    assert bool(r8.captain) is True
    assert df.set_index("num").loc[7].club_country == "Japan"
    assert df.captain.sum() == 1


def test_current_teams(wiki):
    df = parse_current_teams(wiki("league")).set_index("team_raw")
    assert df.loc["Darkhan United", "home_city"] == "Darkhan"
    assert df.loc["Khovd Falcons", "home_city"] == "Khovd"
    assert len(df) == 10


def test_champions_has_1994(wiki):
    df = parse_champions(wiki("league"))
    first = df.iloc[0]
    assert (first.season, first.champion, first.runner_up) == ("1994–95", "1+11", "Asian Wolf")
    assert df.season.is_unique


def test_geojson_has_22_units():
    if not GEO.exists():
        import pytest
        pytest.skip("geojson татагдаагүй")
    assert len(json.loads(GEO.read_text(encoding="utf-8"))["features"]) == 22
