from src.parse_mba import parse_player_profile, parse_player_stats


def test_stats_2025_26_rows(html):
    rows = parse_player_stats(html("stats_2025_26"))
    assert len(rows) == 171
    r = rows[0]
    assert r["rank"] == 1
    assert r["player_name"] == "BYRON Wesley"
    assert r["player_slug"] == "byron-wesley-2"
    assert r["team_name"] == "BUREN SCORE MONGOLIANS"
    assert r["GP"] == 24
    assert (r["MIN"], r["PPG"], r["RPG"], r["APG"]) == (32.5, 27.9, 5.4, 3.8)
    assert (r["SPG"], r["BPG"], r["PF"]) == (1.9, 0.9, 1.5)
    assert (r["FG_pct"], r["TP_pct"], r["EFF"]) == (50.3, 31.4, 25.5)


def test_stats_distinct_teams(html):
    rows = parse_player_stats(html("stats_2025_26"))
    assert len({r["team_name"] for r in rows}) == 10


def test_stats_negative_eff_parsed(html):
    rows = parse_player_stats(html("stats_2025_26"))
    assert min(r["EFF"] for r in rows) < 0


def test_profile_import(html):
    p = parse_player_profile(html("profile_byron_wesley"), "byron-wesley")
    assert p["player_slug"] == "byron-wesley"
    assert p["position"] == "PG" and p["position_raw"] == "Point guard (PG)"
    assert p["height_cm"] == 196 and p["birth_year"] == 1992
    assert p["is_import"] is True
    assert p["season"] == "2026-2027"
    assert p["FT_pct"] == 85.1
    assert p["team_name"] == "Khan Falcons" and p["number"] == 22


def test_profile_domestic(html):
    p = parse_player_profile(html("profile_narangerel_batbayar"), "narangerel-batbayar")
    assert p["position"] == "SG"
    assert p["height_cm"] == 193 and p["birth_year"] == 1995
    assert p["is_import"] is False
    assert p["team_name"] == "Selenge Bodons" and p["number"] == 9
    assert p["FT_pct"] == 81.8


MISSING_HTML = """
<html><body><main>
<a>Home</a><span>/</span><a>Some Team</a><span>/</span><span>DOE John</span>
<span>Some Team</span><span>· #</span><span>5</span><h1>DOE John</h1>
<p>Center (C) · 2026-2027</p>
</main></body></html>
"""


def test_profile_missing_fields():
    p = parse_player_profile(MISSING_HTML, "doe-john")
    assert p["position"] == "C"
    assert p["height_cm"] is None and p["birth_year"] is None
    assert p["is_import"] is False
    assert p["FT_pct"] is None
