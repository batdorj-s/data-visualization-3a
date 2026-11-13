import json
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402
import pytest  # noqa: E402
from matplotlib.collections import PathCollection  # noqa: E402

from src.chart_qa import check  # noqa: E402
from src.charts import ml as M  # noqa: E402

REP = Path(__file__).resolve().parents[1] / "reports"


@pytest.fixture(scope="module")
def metrics():
    return json.loads((REP / "metrics.json").read_text(encoding="utf-8"))


@pytest.fixture(scope="module")
def preds():
    return pd.read_csv(REP / "cv_predictions.csv")


@pytest.fixture(autouse=True)
def _close():
    yield
    plt.close("all")


def test_elbow_silhouette(metrics):
    km = metrics["kmeans"]
    check(M.fig_elbow_silhouette(km["inertia_by_k"], km["silhouette_by_k"], km["k"]))


def test_pca_clusters_alpha_range():
    cl = pd.read_csv(REP / "clusters.csv")
    fig = M.fig_pca_clusters(cl)
    sc = [c for c in fig.axes[0].collections if isinstance(c, PathCollection)]
    alphas = np.concatenate([c.get_facecolors()[:, 3] for c in sc])
    assert alphas.min() >= 0.15 - 1e-9 and alphas.max() <= 1 + 1e-9
    check(fig)


def test_radar():
    check(M.fig_radar_centroids(pd.read_csv(REP / "cluster_centroids_z.csv")))


def test_confusion_and_roc(preds):
    lr = preds[preds.model == "logreg"]
    check(M.fig_confusion(lr.y.to_numpy(), lr.p.to_numpy()))
    check(M.fig_roc(preds))


def test_metric_distributions(preds):
    check(M.fig_metric_distributions(preds, n_boot=200))


def test_calibration_bins(preds):
    lr = preds[preds.model == "logreg"]
    fig = M.fig_calibration(lr.y.to_numpy(), lr.p.to_numpy(), n_bins=5)
    sc = [c for c in fig.axes[0].collections if isinstance(c, PathCollection)]
    assert sum(len(c.get_offsets()) for c in sc) <= 5
    check(fig)


def test_importance_pareto():
    check(M.fig_importance_pareto(pd.read_csv(REP / "explanatory.csv")))


def test_cluster_colors_consistent_across_charts():
    cl = pd.read_csv(REP / "clusters.csv")
    cz = pd.read_csv(REP / "cluster_centroids_z.csv")
    colors = M.cluster_colors(cl.cluster_name)
    radar = M.fig_radar_centroids(cz)
    for line in radar.axes[0].get_lines():
        if line.get_label() in colors:
            assert matplotlib.colors.to_hex(line.get_color()) == matplotlib.colors.to_hex(colors[line.get_label()])


def test_calibration_title_detects_miscalibration():
    import numpy as np
    y = np.zeros(200, dtype=int)
    p = np.linspace(0.6, 0.95, 200)
    assert "зөрсөн" in M.fig_calibration(y, p)._mba_meta["title"]
