from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402
import pytest  # noqa: E402
from matplotlib.collections import PolyCollection  # noqa: E402
from matplotlib.container import BarContainer  # noqa: E402

from src.chart_qa import check  # noqa: E402
from src.charts import comparison as C  # noqa: E402
from src.charts import timeline as T  # noqa: E402

PROC = Path(__file__).resolve().parents[1] / "data" / "processed"


@pytest.fixture(scope="module")
def tg():
    return pd.read_csv(PROC / "team_games.csv")


@pytest.fixture(scope="module")
def games():
    return pd.read_csv(PROC / "games.csv")


@pytest.fixture(scope="module")
def pg():
    return pd.read_csv(PROC / "player_games.csv").assign(is_import=lambda d: d.is_import.astype(bool))


@pytest.fixture(autouse=True)
def _close():
    yield
    plt.close("all")


def test_pareto_table():
    t = C.pareto_table(pd.Series({"a": 50, "b": 30, "c": 20}))
    assert t.label.tolist() == ["a", "b", "c"]
    assert t.cum_share.tolist() == pytest.approx([0.5, 0.8, 1.0])


def test_fig_pareto_axes_and_threshold():
    values = pd.Series({"a": 50, "b": 30, "c": 20})
    fig = C.fig_pareto(values, pd.Series({"a": "#0072B2", "b": "#0072B2", "c": "#D55E00"}),
                       title="Т", subtitle="Д", xlabel="x", ylabel="y", n=3)
    ax, ax2 = fig.axes[0], fig.axes[1]
    assert ax.get_ylim()[0] == 0 and ax2.get_ylim()[0] == 0
    assert ax2.get_ylim()[1] <= 1.05
    assert any(abs(line.get_ydata()[0] - 0.8) < 1e-9 for line in ax2.get_lines() if len(line.get_ydata()) == 2)
    check(fig)


def test_pareto_ci_brackets_point(pg):
    sub = pg[pg.season == "2025-2026"]
    values = sub.groupby("player_id").PTS.sum()
    lo, hi = C.pareto_ci(sub, n_boot=100)
    cum = C.pareto_table(values).cum_share.to_numpy()
    assert len(lo) == len(cum)
    assert np.all(lo <= cum + 1e-9) and np.all(cum <= hi + 1e-9)


def test_cum_winpct_bands(tg):
    with_bands = T.fig_cum_winpct(tg, highlight=["sg_apes"], bands=True)
    assert sum(isinstance(c, PolyCollection) for c in with_bands.axes[0].collections) >= 3
    no_bands = T.fig_cum_winpct(tg, highlight=["sg_apes"], bands=False)
    assert sum(isinstance(c, PolyCollection) for c in no_bands.axes[0].collections) == 0
    check(with_bands)


def test_top_dot_ci_has_no_bars():
    df = pd.DataFrame({"player": ["A", "B"], "est": [20.0, 18.0], "lo": [18.0, 15.0], "hi": [22.0, 21.0]})
    fig = C.fig_top_dot_ci(df, "Оноо / тоглолт")
    assert not any(isinstance(c, BarContainer) for c in fig.axes[0].containers)
    check(fig)


def test_other_charts_pass_qa(tg, games, pg):
    check(T.fig_elo(games, highlight=["sg_apes", "erdenet_miners"]))
    check(C.fig_four_factors(tg))
    check(C.fig_import_share_donut(pg, n_boot=100))
    check(C.fig_team_concentration(pg, n_boot=50))
    vals = pg[pg.season == "2025-2026"].groupby("player_id").PTS.sum()
    imp = pg.drop_duplicates("player_id").set_index("player_id").is_import
    check(C.fig_pareto(vals, imp.reindex(vals.index).map({True: "#D55E00", False: "#0072B2"}),
                       title="Т", subtitle="Д", xlabel="x", ylabel="y", n=len(vals), cum_ci=C.pareto_ci(
                           pg[pg.season == "2025-2026"], n_boot=50)))


def test_fan_title_differs_from_plain(tg):
    a = T.fig_cum_winpct(tg, ["sg_apes"], bands=False)._mba_meta["title"]
    b = T.fig_cum_winpct(tg, ["sg_apes"], bands=True)._mba_meta["title"]
    assert a != b and "±" in b
