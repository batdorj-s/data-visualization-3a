import pandas as pd

from src.import_sources import LEVELS, identity_ok, level_of, parse_profile, slug_candidates


def test_slug_candidates_cover_both_name_orders():
    assert slug_candidates("MILLER Ian")[:2] == ["ian-miller", "miller-ian"]
    assert "mckenzie-moore" in slug_candidates("MOORE Mckenzie Zachary")


def test_identity_check_uses_birth_year_then_height():
    assert identity_ok({"birth_year": 1991, "height_cm": 191}, 1992, None)
    assert not identity_ok({"birth_year": 1985, "height_cm": 191}, 1992, 191)  # төрсөн он тэргүүлнэ
    assert identity_ok({"birth_year": None, "height_cm": 200}, None, 203)
    assert not identity_ok({"birth_year": 1990, "height_cm": None}, None, None)  # баталгаажуулах юм алга


def test_level_tiers():
    df = lambda leagues: pd.DataFrame({"league": leagues})  # noqa: E731
    assert level_of(df(["NCAA", "G League", "NBA"])) == LEVELS[0]
    assert level_of(df(["NCAA", "EuroCup", "Spain"])) == LEVELS[1]
    assert level_of(df(["NCAA", "D League", "Poland"])) == LEVELS[2]
    assert level_of(df(["NCAA", "Mexico"])) == LEVELS[3]
    assert level_of(df(["NCAA"])) == LEVELS[4]


def test_parse_profile_minimal_html():
    html = """<html><body>
    <div><strong>Born</strong><span>28th September 1991 (age 35)</span></div>
    <div><strong>Nationality</strong><span><span>🇺🇸</span><a>USA</a></span></div>
    <div><strong id="h">Height</strong><span><a data-unit-metric="191cm">6'3</a></span></div>
    <table><tr><th>Year</th><th>League</th><th>Team</th><th>G</th><th>MPG</th><th>PTS/G</th><th>FG%</th><th>3P%</th></tr>
    <tr><td>2013-14</td><td>NCAA</td><td>Florida State</td><td>33</td><td>28.4</td><td>13.7</td><td>44.9%</td><td>37.0%</td></tr>
    <tr><td>2024-25</td><td>Lithuania</td><td>Juventus</td><td>6</td><td>17.0</td><td>11.0</td><td>45.2%</td><td>36.4%</td></tr>
    </table></body></html>"""
    p = parse_profile(html)
    assert p["birth_year"] == 1991 and p["nationality"] == "USA" and p["height_cm"] == 191
    assert [r["league"] for r in p["career"]] == ["NCAA", "Lithuania"] and p["career"][1]["ppg"] == 11.0
