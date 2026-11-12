from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402
import pytest  # noqa: E402

from src.chart_qa import check  # noqa: E402
from src.charts import distribution as D  # noqa: E402
from src.charts import relation as R  # noqa: E402

PROC = Path(__file__).resolve().parents[1] / "data" / "processed"


@pytest.fixture(scope="module")
def players():
    ps = pd.read_csv(PROC / "players_season.csv")
    return ps[ps.eligible.astype(bool)].reset_index(drop=True)


@pytest.fixture(scope="module")
def standings():
    return pd.read_csv(PROC / "standings_hist.csv")


@pytest.fixture(autouse=True)
def _close():
    yield
    plt.close("all")


@pytest.mark.parametrize("fn", [D.fig_ppg_hist, D.fig_ts_box_by_pos, D.fig_corr_heatmap, D.fig_ppg_violin,
                                R.fig_height_reb, R.fig_ts_funnel])
def test_player_charts_pass_qa(fn, players):
    meta = check(fn(players))
    assert meta["n"] > 0


def test_pairplot_with_labels(players):
    labels = pd.Series(np.where(players.PPG > 10, "A", "B"), index=players.index)
    check(D.fig_pairplot(players, labels))
    check(D.fig_pairplot(players, None))


def test_raincloud(players):
    boot = np.random.default_rng(0).normal(10, 1, 500)
    check(D.fig_raincloud(players, boot))


def test_pythagorean(standings):
    check(R.fig_pythagorean(standings))


def test_funnel_ignores_zero_attempts(players):
    extra = players.head(3).copy()
    extra[["FGA", "FTA", "PTS_total"]] = 0
    extra["ts_pct"] = np.nan
    fig = R.fig_ts_funnel(pd.concat([players, extra], ignore_index=True))
    from matplotlib.collections import PathCollection
    scatter = next(c for c in fig.axes[0].collections if isinstance(c, PathCollection))
    offsets = scatter.get_offsets()
    assert len(offsets) == int(((players.FGA + 0.44 * players.FTA) > 0).sum())


def test_hist_direct_labels(players):
    fig = D.fig_ppg_hist(players)
    texts = {t.get_text() for t in fig.axes[0].texts}
    assert any("Import" in t for t in texts) and any("Дотоод" in t for t in texts)
    assert fig.axes[0].get_legend() is None


def test_heatmap_centered(players):
    fig = D.fig_corr_heatmap(players)
    im = fig.axes[0].collections[0] if fig.axes[0].collections else fig.axes[0].images[0]
    assert im.norm.vmin == -1 and im.norm.vmax == 1
