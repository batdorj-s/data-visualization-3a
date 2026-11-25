"""SaaS загварын дээд самбар (шүүлтүүр), цайвар sidebar, KPI-ийн чиг хандлагын тэмдэг."""
from pathlib import Path

from streamlit.testing.v1 import AppTest

DASH = Path(__file__).resolve().parents[1] / "dashboard"
APP = str(DASH / "app.py")


def run(page=None, **state):
    at = AppTest.from_file(APP, default_timeout=90)
    for k, v in state.items():
        at.session_state[k] = v
    at.run()
    if page:
        at.switch_page(page)
        at.run()
    assert not at.exception, [e.value for e in at.exception]
    return at


def _html(at) -> str:
    return " ".join(h.proto.body for h in at.get("html"))


def test_filters_live_in_main_toolbar_not_sidebar():
    at = run()
    assert not at.sidebar.selectbox and not at.sidebar.multiselect and not at.sidebar.slider
    labels = {w.label for w in at.multiselect} | {w.label for w in at.selectbox} | {w.label for w in at.slider}
    assert {"Баг", "Онцлох баг", "Хамгийн багадаа хэдэн тоглолт тоглосон"} <= labels
    assert 'class="mba-crumb"' in _html(at) and "Шинжилгээ" in _html(at)


def test_active_filters_show_as_chips_only_when_set():
    assert "Идэвхтэй шүүлтүүр" not in _html(run())
    html = _html(run(None, positions=["C"], min_gp=10))
    assert "Идэвхтэй шүүлтүүр" in html and "Байрлал" in html and "10+ тоглолт" in html


def test_filter_state_survives_help_page():
    at = run(None, positions=["PG"], season="2026-2027")
    at.switch_page("views/glossary.py")
    at.run()
    assert 'mba-crumb--solo' in _html(at) and not at.multiselect
    at.switch_page("views/overview.py")
    at.run()
    assert at.session_state["positions"] == ["PG"] and at.session_state["season"] == "2026-2027"


def test_kpi_trend_only_when_previous_season_exists():
    assert "mba-kpi__trend\" title" not in _html(run(None, season="2025-2026"))
    html = _html(run(None, season="2026-2027"))
    assert html.count("mba-kpi__trend\" title") == 2 and "2025–26 улиралд" in html


def test_sidebar_theme_is_light():
    cfg = (DASH.parent / ".streamlit" / "config.toml").read_text()
    side = cfg.split("[theme.sidebar]")[1].split("[")[0]
    assert 'backgroundColor = "#F8FAFC"' in side and 'textColor = "#0F172A"' in side
    assert 'fill="#FFFFFF"' not in (DASH / "assets" / "mba_wordmark.svg").read_text()
