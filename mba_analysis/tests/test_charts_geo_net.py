from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import pandas as pd  # noqa: E402
import pytest  # noqa: E402

from src.chart_qa import check  # noqa: E402
from src.charts.geo_network import fig_team_map, fig_transfer_network, load_aimags, transfer_edges  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
GEO = ROOT / "data" / "raw" / "geo" / "mng_adm1.geojson"


@pytest.fixture(autouse=True)
def _close():
    yield
    plt.close("all")


def test_load_aimags():
    shapes = load_aimags(GEO)
    assert len(shapes) == 22
    assert all(s["paths"] for s in shapes)


def test_transfer_edges():
    ps = pd.DataFrame({
        "player_id": ["a", "a", "b", "b", "c", "c", "d"],
        "season": ["2025-2026", "2026-2027"] * 3 + ["2026-2027"],
        "team_key": ["X", "Y", "X", "X", "X", "Y", "Z"],
    })
    edges = transfer_edges(ps)
    assert edges.values.tolist() == [["X", "Y", 2]]


def test_team_map_caption_counts_unknown():
    meta = pd.read_csv(ROOT / "data" / "processed" / "team_meta.csv")
    st = pd.read_csv(ROOT / "data" / "processed" / "standings_hist.csv")
    fig = fig_team_map(meta, st, GEO, season="2026-2027")
    meta_check = check(fig)
    unknown = meta[meta.team_key.isin(st[st.season == "2026-2027"].team_key) & meta.lat.isna()]
    assert f"{len(unknown)} баг" in meta_check["uncertainty_note"]


def test_transfer_network_qa():
    ps = pd.read_csv(ROOT / "data" / "processed" / "players_season.csv")
    names = dict(zip(ps.team_key, ps.team))
    check(fig_transfer_network(transfer_edges(ps), names))
