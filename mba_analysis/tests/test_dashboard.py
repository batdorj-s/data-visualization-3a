import json
import sys
from pathlib import Path

import pytest
from streamlit.testing.v1 import AppTest

DASH = Path(__file__).resolve().parents[1] / "dashboard"
APP = str(DASH / "app.py")
PAGES = ["views/overview.py", "views/players.py", "views/teams.py", "views/ml.py", "views/quality.py",
         "views/about.py"]
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
        return sum(1 for s in specs for t in s["data"] if "CI" in str(t.get("name", "")))
    assert ci_traces(with_ci) > 0
    assert ci_traces(without) == 0


def test_quantile_dots():
    sys.path.insert(0, str(DASH))
    from plots import A_COLOR, px_quantile_dots
    fig = px_quantile_dots(0.62, n=20)
    colors = list(fig.data[0].marker.color)
    assert len(colors) == 20
    assert colors.count(A_COLOR) == 12
