from src.parse_mba import parse_game, parse_schedule


def test_parse_schedule_jan(html):
    rows = parse_schedule(html("schedule_2025_26_2026_01"), "2026-01")
    played = [r for r in rows if r["game_id"] is not None]
    assert len(played) == 35
    g = next(r for r in rows if r["game_id"] == 141)
    assert g["date"] == "2026-01-04"
    assert g["stage"] == "Regular season"
    assert g["status"] == "Final"
    assert g["home_name"] == "XAC BRONCOS"
    assert g["away_name"] == "SELENGE BODONS"
    assert g["home_pts"] == 77 and g["away_pts"] == 69
    assert g["venue_raw"] == "М Банк арена"
    assert g["home_team_slug"] == "khasyn-khuleguud"


def test_parse_schedule_playoff_stage(html):
    rows = parse_schedule(html("schedule_2025_26_2026_03"), "2026-03")
    stages = {r["stage"] for r in rows}
    assert "Playoffs" in stages
    assert stages <= {"Regular season", "Playoffs", "Finals"}


def test_parse_schedule_skips_unplayed(html):
    rows = parse_schedule(html("schedule_2026_27_2026_11"), "2026-11")
    unplayed = [r for r in rows if r["status"] != "Final"]
    assert unplayed, "11-р сард тоглогдоогүй тоглолт байх ёстой"
    for r in unplayed:
        assert r["status"] == "Scheduled"
        assert r["game_id"] is None
        assert r["home_pts"] is None and r["away_pts"] is None
    assert all(r["game_id"] is not None for r in rows if r["status"] == "Final")


def test_parse_game_141_header(html):
    g = parse_game(html("game_141"), 141)
    assert g["game_id"] == 141
    assert g["season"] == "2025-2026"
    assert g["date"] == "2026-01-04"
    assert g["time"] == "16:10"
    assert g["home_name"] == "XAC BRONCOS"
    assert g["away_name"] == "SELENGE BODONS"
    assert g["home_pts"] == 77 and g["away_pts"] == 69
    assert g["quarters"] == {"home": [18, 20, 20, 19], "away": [17, 23, 16, 13]}


def test_parse_game_141_totals(html):
    g = parse_game(html("game_141"), 141)
    home, away = (next(t for t in g["team_totals"] if t["side"] == s) for s in ("home", "away"))
    assert home == {
        "side": "home", "PTS": 77, "REB": 50, "AST": 19, "STL": 6, "BLK": 3,
        "FG": "24-70", "TP": "8-28", "FT": "21-24", "TOV": 11, "PF": 19, "OREB": 17, "DREB": 33,
    }
    assert (away["PTS"], away["REB"], away["OREB"], away["DREB"]) == (69, 38, 13, 25)
    assert (away["FG"], away["TP"], away["FT"], away["TOV"]) == ("21-68", "8-33", "19-25", 13)


def test_parse_game_141_players(html):
    g = parse_game(html("game_141"), 141)
    p = next(x for x in g["players"] if x["name"] == "ALTANGEREL Azbayar")
    assert p["side"] == "home" and p["number"] == 7 and p["pos"] == "C"
    assert (p["MIN"], p["PTS"], p["REB"]) == (32, 12, 13)
    assert (p["FG"], p["TP"], p["FT"]) == ("5-12", "0-1", "2-2")
    assert p["dnp"] is False
    assert p["player_slug"]
    dnp = [x for x in g["players"] if x["dnp"]]
    assert dnp
    assert all(x["MIN"] is None and x["PTS"] is None and x["FG"] is None for x in dnp)
    assert {x["side"] for x in g["players"]} == {"home", "away"}


OT_HTML = """
<html><head><title>AAA 95:90 BBB | MBA</title></head><body><main>
<nav>Home / National Basketball League / 2025-2026 / Schedule / AAA — BBB</nav>
<div>AAA</div><div>Home</div><div>Final</div><div>95</div><div>–</div><div>90</div>
<div>4 Jan 2026</div><div>·</div><div>16:10</div><div>·</div><div>М Банк арена</div>
<div>BBB</div><div>Away</div><div>Score by quarter</div>
<table>
<tr><th></th><th>Q1</th><th>Q2</th><th>Q3</th><th>Q4</th><th>OT</th><th>Total</th></tr>
<tr><th>AAA</th><td>20</td><td>20</td><td>20</td><td>20</td><td>15</td><td>95</td></tr>
<tr><th>BBB</th><td>25</td><td>15</td><td>20</td><td>20</td><td>10</td><td>90</td></tr>
</table>
</main></body></html>
"""


def test_parse_game_overtime_columns():
    g = parse_game(OT_HTML, 999)
    assert len(g["quarters"]["home"]) == 5
    assert sum(g["quarters"]["home"]) == g["home_pts"] == 95
    assert sum(g["quarters"]["away"]) == g["away_pts"] == 90


LIVE_CARD = """
<html><body><main><section><h3>Sat 14 Nov</h3><ul>
<li><span>Q3</span><span>LIVE</span><span>M BANK ARENA</span>
<a href="/en/teams/a"><span>Team A</span><span>AAA</span></a><span>45</span><span>–</span><span>40</span>
<a href="/en/teams/b"><span>Team B</span><span>BBB</span></a><a href="/en/games/900">Box score</a></li>
<li><span>Final</span><span>M BANK ARENA</span>
<a href="/en/teams/a"><span>Team A</span><span>AAA</span></a><span>80</span><span>–</span><span>70</span>
<a href="/en/teams/b"><span>Team B</span><span>BBB</span></a><a href="/en/games/901">Box score</a></li>
</ul></section></main></body></html>
"""


def test_parse_schedule_live_game_is_not_final():
    rows = {r["game_id"] or "live": r for r in parse_schedule(LIVE_CARD, "2026-11")}
    assert rows[901]["status"] == "Final"
    live = [r for r in parse_schedule(LIVE_CARD, "2026-11") if r["status"] != "Final"]
    assert len(live) == 1 and live[0]["game_id"] is None and live[0]["home_pts"] is None


def test_parse_game_events_141(html):
    from src.parse_mba import parse_game_events
    ev = parse_game_events(html("game_141"), 141)
    shots, pbp = ev["shots"], ev["events"]
    assert len(shots) == 138
    s = shots[0]
    assert set(s) >= {"game_id", "seq", "side", "player", "number", "period", "made", "three", "x", "y"}
    assert s["game_id"] == 141 and s["side"] in ("home", "away") and 0 <= s["x"] <= 637 and 0 <= s["y"] <= 350
    assert len(pbp) > 300
    last_score = [e for e in pbp if e["home"] is not None][-1]
    assert (last_score["home"], last_score["away"]) == (77, 69)  # гарчгийн эцсийн оноо
    made = [e for e in pbp if e["type"] in ("2pt", "3pt", "ft") and e["made"] is True]
    assert sum(e["points"] for e in made if e["side"] == "home") == 77
    sub = next(e for e in pbp if e["type"] == "sub")
    assert sub["player_slug"] and sub["clock"] == "10:00"


def test_parse_game_events_missing_block_returns_empty():
    from src.parse_mba import parse_game_events
    assert parse_game_events("<html><head><title>x</title></head><body></body></html>", 1) == {"shots": [], "events": []}
