"""Дасгалжуулагчийн дүгнэлт: хуудас бүрт гарч, тоо нь датаас ирж, «nan»/«inf» шиг эвдэрсэн утга агуулахгүй."""
import re
import sys
from pathlib import Path

import pandas as pd
import pytest
from streamlit.testing.v1 import AppTest

DASH = Path(__file__).resolve().parents[1] / "dashboard"
sys.path.insert(0, str(DASH))
import coach  # noqa: E402

APP = str(DASH / "app.py")
# хуудас → хамгийн багадаа хэдэн дүгнэлтийн хайрцаг (таб, fragment-ийн анхдагч төлөвт)
PAGES = {"views/overview.py": 4, "views/teams.py": 5, "views/players.py": 5, "views/shots.py": 4,
         "views/insights.py": 9, "views/ml.py": 2, "views/quality.py": 1}
BAD = re.compile(r"\bnan\b|\binf\b|None|%-ийг -", re.I)


def _coach_html(at) -> list[str]:
    return [h.proto.body for h in at.get("html") if 'class="mba-coach"' in h.proto.body]


@pytest.mark.parametrize("page,expected", PAGES.items())
def test_every_chart_page_has_coach_notes(page, expected):
    at = AppTest.from_file(APP, default_timeout=90)
    at.run()
    at.switch_page(page)
    at.run()
    assert not at.exception, [e.value for e in at.exception]
    boxes = _coach_html(at)
    assert len(boxes) >= expected, (page, len(boxes))
    for b in boxes:
        assert "Дасгалжуулагчийн дүгнэлт" in b and "<li>" in b
        assert not BAD.search(re.sub(r"<[^>]+>", " ", b)), b


@pytest.mark.parametrize("season", ["2025-2026", "2026-2027"])
def test_coach_text_tracks_the_data(season):
    data = DASH / "data"
    tg = pd.read_parquet(data / "team_games.parquet")
    reg = tg[(tg.season == season) & (tg.phase == "regular")]
    table = (reg.groupby("team").agg(W=("win", "sum"), G=("win", "size"), net=("net", "mean"))
             .assign(L=lambda d: d.G - d.W, pct=lambda d: d.W / d.G).sort_values(["pct", "net"], ascending=False))
    text = " ".join(coach.standings(table))
    assert table.index[0] in text and f"{int(table.W.iloc[0])}–{int(table.L.iloc[0])}" in text
    lead = pd.read_parquet(data / "ins_lead.parquet")
    safe = lead[(lead.checkpoint == "Хагас") & (lead.est >= 0.9)].iloc[0]
    assert f"**{safe.bin}**" in coach.lead_safety(lead)[0]


def test_coach_rules_of_thumb():
    assert "ойролцоо" in coach.win_calc("A", "B", 0.5)[1]
    assert "20-оос ердөө 4" in coach.win_calc("A", "B", 0.8)[1]
    rows = [("Оноо", "", 80.0, 70.0, "", True), ("Алдсан оноо", "", 75.0, 70.0, "", False)]
    out = coach.compare("A", "B", rows)
    assert "1-д" in out[0] and "«Алдсан оноо» үзүүлэлтийг" in out[1]
