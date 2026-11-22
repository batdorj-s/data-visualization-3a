"""Багийн лого (эх сурвалж, тааруулалт) ба дизайны системийн UI хэсгүүд."""
import sys
from pathlib import Path

import pandas as pd

from src.team_logos import extract

ROOT = Path(__file__).resolve().parents[1]
DASH = ROOT / "dashboard"
sys.path.insert(0, str(DASH))


def test_extract_maps_schema_org_teams_through_aliases(tmp_path):
    page = ('{"@type":"SportsTeam","name":"OMNI ERDENET MINERS","url":"https://mongolia.basketball/en/teams/a",'
            '"logo":"https://mongolia.basketball/media/8f/x.png"} '
            '{"@type":"SportsTeam","name":"XAC BRONCOS","url":"https://mongolia.basketball/en/teams/b",'
            '"logo":"https://mongolia.basketball/media/06/y.png"}')
    (tmp_path / "g1.html").write_text(page, encoding="utf-8")
    (tmp_path / "g2.html").write_text(page.split("} ")[0] + "}", encoding="utf-8")
    aliases = pd.read_csv(ROOT / "data" / "raw" / "manual" / "team_aliases.csv", dtype=str).fillna("")
    out = extract(tmp_path, aliases).set_index("team_key")
    assert set(out.index) == {"erdenet_miners", "khasin_khuleguud"}
    assert out.loc["erdenet_miners", "logo_url"].endswith("/x.png") and out.loc["erdenet_miners", "n_pages"] == 2


def test_every_current_team_has_an_official_logo():
    logos = pd.read_csv(ROOT / "data" / "processed" / "team_logos.csv")
    teams = set(pd.read_csv(ROOT / "data" / "processed" / "team_games.csv").team_key)
    assert teams <= set(logos.team_key), teams - set(logos.team_key)
    assert logos.logo_url.str.startswith("https://mongolia.basketball/media/").all()
    assert logos.team_key.is_unique


def test_team_logo_has_fixed_box_contain_fit_and_initials_fallback():
    from ui import CSS, initials, team_logo
    assert initials("BCH Knights") == "BCH" and initials("XAC Broncos") == "XAC" and initials("Khan Falcons") == "KF"
    with_img = team_logo("Khan Falcons", "https://example.org/l.png", 40)
    assert "width:40px;height:40px" in with_img and "<img" in with_img and ">KF<" in with_img
    without = team_logo("Khan Falcons", None, 40)
    assert "<img" not in without and ">KF<" in without  # лого алга → үсгэн тэмдэг
    assert "object-fit: contain" in CSS  # лого сунахгүй


def test_design_tokens_match_streamlit_theme():
    import tomllib
    from ui import TOKENS
    theme = tomllib.loads((ROOT / ".streamlit" / "config.toml").read_text())["theme"]
    assert theme["primaryColor"].lower() == TOKENS["primary"].lower()
    assert theme["backgroundColor"].lower() == TOKENS["bg"].lower()
    assert theme["textColor"].lower() == TOKENS["text"].lower()


def test_off_def_chart_places_one_logo_per_team():
    from plots import px_off_def
    df = pd.DataFrame({"team": ["A", "B", "C"], "ortg": [100.0, 105, 110], "drtg": [104.0, 100, 106],
                       "win": [0.4, 0.7, 0.5], "pace": [70.0, 72, 71]})
    fig = px_off_def(df, "B", {"A": "data:image/png;base64,AA", "B": "data:image/png;base64,BB"})
    assert len(fig.layout.images) == 2 and {im.sizing for im in fig.layout.images} == {"contain"}
    assert len(px_off_def(df, None).layout.images) == 0  # логогүй бол хуучин тойрог
