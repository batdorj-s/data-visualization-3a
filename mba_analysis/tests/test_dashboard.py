import json
import sys
from pathlib import Path

import pytest
from streamlit.testing.v1 import AppTest

DASH = Path(__file__).resolve().parents[1] / "dashboard"
APP = str(DASH / "app.py")
PAGES = ["views/overview.py", "views/players.py", "views/teams.py", "views/ml.py", "views/quality.py",
         "views/about.py", "views/glossary.py", "views/shots.py", "views/insights.py"]
EMPTY_MSG = "Сонгосон шүүлтүүрт тохирох өгөгдөл алга"


def run(page=None, **state):
    at = AppTest.from_file(APP, default_timeout=60)
    for k, v in state.items():
        at.session_state[k] = v
    at.run()
    if page:
        at.switch_page(page)
        at.run()
    return at


@pytest.mark.parametrize("page", PAGES)
def test_app_runs_all_pages(page):
    at = run(page)
    assert not at.exception, [e.value for e in at.exception]


def test_empty_filter_shows_message():
    at = run("views/players.py", min_gp=28, teams=["Erdenet Miners"], positions=["C"], season="2026-2027")
    assert not at.exception
    assert any(EMPTY_MSG in i.value for i in at.info)


def _plot_specs(at):
    return [json.loads(el.proto.spec) for el in at.get("plotly_chart")]


def test_ci_toggle_removes_ci_traces():
    with_ci = _plot_specs(run("views/players.py", show_ci=True))
    without = _plot_specs(run("views/players.py", show_ci=False))

    def ci_traces(specs):
        return sum(1 for s in specs for t in s["data"] if "хүрээ" in str(t.get("name", "")))
    assert ci_traces(with_ci) > 0
    assert ci_traces(without) == 0


def test_quantile_dots():
    sys.path.insert(0, str(DASH))
    from plots import A_COLOR, px_quantile_dots
    fig = px_quantile_dots(0.62, n=20)
    colors = list(fig.data[0].marker.color)
    assert len(colors) == 20
    assert colors.count(A_COLOR) == 12


def test_highlight_team_drives_overview_fan():
    at = run(None, highlight_team="SG Apes")
    at.session_state["highlight_team"] = "BCH Knights"
    at.run()
    fan = next(s for s in at.selectbox if s.label == "Ялалтын явцыг харах баг")
    assert fan.value == "BCH Knights"


def test_scatter_selection_updates_card():
    sys.path.insert(0, str(DASH))
    from data_access import apply_selection
    state = {"card_player": "a"}
    assert apply_selection(state, ["b", "c"]) is True
    assert state["card_player"] == "b"
    state["card_player"] = "z"  # хэрэглэгч картаа гараар сольсон
    assert apply_selection(state, ["b", "c"]) is False  # ижил сонголт картыг буцааж дарахгүй
    assert state["card_player"] == "z"
    assert apply_selection(state, []) is False
    assert apply_selection(state, ["d"]) is True and state["card_player"] == "d"


def test_reset_filters_restores_defaults():
    at = run("views/players.py", min_gp=20, positions=["C"], import_status="Гадаад")
    next(b for b in at.button if b.label == "Шүүлтүүрийг цэвэрлэх").click()
    at.run()
    assert at.session_state["min_gp"] == 5 and at.session_state["positions"] == []
    assert at.session_state["import_status"] == "Бүгд"


def test_glossary_search_filters_terms():
    at = run("views/glossary.py")
    at.text_input(key="glossary_q").input("оновч").run()
    assert not at.exception
    text = " ".join(m.value for m in at.markdown)
    assert "Шидэлтийн оновч" in text and "Багийн хүчний оноо" not in text


def test_theme_config_copies_match():
    root = DASH.parents[1]
    assert (root / ".streamlit" / "config.toml").read_text() == (DASH.parent / ".streamlit" / "config.toml").read_text()


def test_shots_page_follows_highlight_team():
    at = run("views/shots.py", highlight_team="BCH Knights")
    assert not at.exception, [e.value for e in at.exception]
    team = next(s for s in at.selectbox if s.label == "Баг")
    assert team.value == "BCH Knights"


def test_insights_page_ci_toggle_and_empty_usage():
    def error_bars(at):
        return sum(1 for s in _plot_specs(at) for t in s["data"] if t.get("error_y") or t.get("error_x"))
    assert error_bars(run("views/insights.py", show_ci=True)) > error_bars(run("views/insights.py", show_ci=False)) == 0
    at = run("views/insights.py", teams=["Erdenet Miners"], import_status="Гадаад", season="2026-2027")
    assert not at.exception, [e.value for e in at.exception]


def test_players_import_tab_runs_and_finds_replacements():
    at = run("views/players.py")
    assert not at.exception, [e.value for e in at.exception]
    assert any(s.label.startswith("2025–26 улирлын дараа явсан") for s in at.selectbox)
    assert any("Батлагдсан" in str(spec) for spec in _plot_specs(at))


def test_dashboard_requirements_cover_imported_libraries():
    """Streamlit Cloud зөвхөн dashboard/requirements.txt-г суулгана: dashboard-ийн ачаалдаг бүх гуравдагч сан тэнд байх ёстой."""
    import sysconfig
    for p in PAGES:
        run(p)
    site = sysconfig.get_paths()["purelib"]
    loaded = {n.split(".")[0] for n, m in list(sys.modules.items()) if (getattr(m, "__file__", None) or "").startswith(site)}
    needed = {"sklearn": "scikit-learn", "bs4": "beautifulsoup4", "lxml": "lxml", "requests": "requests",
              "matplotlib": "matplotlib", "joblib": "joblib", "scipy": "scipy", "plotly": "plotly", "pyarrow": "pyarrow",
              "pandas": "pandas", "numpy": "numpy", "streamlit": "streamlit"}
    req = {l.split("==")[0].strip().lower() for l in (DASH / "requirements.txt").read_text().splitlines() if "==" in l}
    missing = [pkg for mod, pkg in needed.items() if mod in loaded and pkg not in req]
    assert missing == [], missing
    assert all("==" in l for l in (DASH / "requirements.txt").read_text().splitlines() if l and not l.startswith("#"))


def test_every_chart_note_names_chart_type_and_existing_files():
    import ast
    sys.path.insert(0, str(DASH))
    from ui import DATASETS
    root = DASH.parent
    assert all((root / path).exists() for path in DATASETS.values()), [p for p in DATASETS.values() if not (root / p).exists()]
    calls = 0
    for fn in [*PAGES, "import_view.py"]:
        for n in ast.walk(ast.parse((DASH / fn).read_text(encoding="utf-8"))):
            if isinstance(n, ast.Call) and getattr(n.func, "id", None) == "chart_note":
                kw = {k.arg: k.value for k in n.keywords}
                assert {"kind", "files"} <= set(kw), f"{fn}:{n.lineno}"
                assert all(e.value in DATASETS for e in kw["files"].elts), f"{fn}:{n.lineno}"
                calls += 1
    assert calls >= 39


def test_every_plotly_chart_is_followed_by_chart_note():
    """График бүрийн доор төрөл, дата, файлын тэмдэглэл байх ёстой (дараагийн 6 мөрт chart_note)."""
    for fn in [*PAGES, "import_view.py"]:
        lines = (DASH / fn).read_text(encoding="utf-8").splitlines()
        for i, line in enumerate(lines):
            if "st.plotly_chart(" in line:
                assert any("chart_note(" in x for x in lines[i + 1:i + 8]), f"{fn}:{i + 1}"


def test_scatter_marks_carded_player_with_star():
    sys.path.insert(0, str(DASH))
    import pandas as pd
    from plots import px_scatter
    df = pd.DataFrame({"player_id": ["a", "b"], "player_name": ["A", "B"], "team": ["T", "U"], "position": ["G", "F"],
                       "is_import": [False, True], "MIN": [10.0, 20.0], "PPG": [5.0, 9.0]})
    fig = px_scatter(df, "MIN", "PPG", "position", None, "b")
    star = [t for t in fig.data if getattr(t.marker, "symbol", None) == "star"]
    assert len(star) == 1 and list(star[0].x) == [20.0] and "B" in star[0].name
    assert not [t for t in px_scatter(df, "MIN", "PPG", "position").data if getattr(t.marker, "symbol", None) == "star"]


def test_game_flow_lead_changes_match_game_list_and_hover_names_teams():
    sys.path.insert(0, str(DASH))
    import numpy as np
    import pandas as pd
    from plots import lead_change_index, px_game_flow
    flow, gl = pd.read_parquet(DASH / "data" / "game_flow.parquet"), pd.read_parquet(DASH / "data" / "game_list.parquet")
    for g in gl.sample(20, random_state=1).itertuples():
        m = flow[flow.game_id == g.game_id].sort_values("elapsed").margin.to_numpy()
        assert len(lead_change_index(m)) == g.lead_changes
    g = gl.loc[gl.lead_changes.idxmax()]
    f = flow[flow.game_id == g.game_id].sort_values("elapsed")
    fig = px_game_flow(f, np.full(len(f), 0.5), g.home_team, g.away_team)
    hover = " ".join(str(t.hovertemplate) for t in fig.data)
    assert g.home_team in hover and g.away_team in hover
    assert sum(len(t.x) for t in fig.data if t.name == "Тэргүүлэгч солигдсон мөч") == g.lead_changes


def test_ml_similar_players_ranked_one_to_five():
    at = run("views/ml.py")
    assert not at.exception
    t = next(d.value for d in at.dataframe if "Эрэмбэ" in d.value.columns)
    assert list(t["Эрэмбэ"]) == [1, 2, 3, 4, 5]
    assert t["Ялгаа (бага = төстэй)"].is_monotonic_increasing
