import json
from pathlib import Path

import matplotlib.pyplot as plt
import networkx as nx
import numpy as np
import pandas as pd
from matplotlib.patches import PathPatch
from matplotlib.path import Path as MplPath

from src.style import LIGHT, PALETTE, apply_style, finish, source_mba

REGION_COLORS = {"Улаанбаатар": PALETTE["vermillion"], "Орон нутаг": PALETTE["blue"]}


def load_aimags(path: Path) -> list[dict]:
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    shapes = []
    for f in data["features"]:
        geom = f["geometry"]
        polys = geom["coordinates"] if geom["type"] == "MultiPolygon" else [geom["coordinates"]]
        paths = [MplPath(np.asarray(ring)[:, :2]) for poly in polys for ring in poly]
        shapes.append({"name": f["properties"].get("shapeName"), "paths": paths})
    return shapes


def _spread(points: pd.DataFrame, radius: float = 0.9) -> pd.DataFrame:
    """Ижил координаттай багуудыг тойргийн дагуу бага зэрэг тараана."""
    out = points.copy()
    for (_, _), idx in points.groupby(["lat", "lon"]).groups.items():
        if len(idx) > 1:
            angles = np.linspace(0, 2 * np.pi, len(idx), endpoint=False)
            out.loc[idx, "lon"] += radius * np.cos(angles)
            out.loc[idx, "lat"] += radius * 0.6 * np.sin(angles)
    return out


def fig_team_map(team_meta: pd.DataFrame, standings: pd.DataFrame, geo_path: Path, season: str = "2025-2026"):
    apply_style()
    st = standings[standings.season == season].assign(winpct=lambda d: d.W / (d.W + d.L))
    df = st.merge(team_meta, on="team_key", how="left")
    unknown = df[df.lat.isna()]
    known = _spread(df[df.lat.notna()])
    fig, ax = plt.subplots(figsize=(6.3, 3.9))
    for shape in load_aimags(geo_path):
        for p in shape["paths"]:
            ax.add_patch(PathPatch(p, facecolor="#F4F4F4", edgecolor=LIGHT, linewidth=0.5))
    for region, part in known.groupby("region"):
        ax.scatter(part.lon, part.lat, s=60 + 900 * part.winpct, color=REGION_COLORS.get(region, "#9E9E9E"),
                   alpha=0.75, edgecolor="white", linewidth=0.8, label=region)
    ub = known[known.region == "Улаанбаатар"]
    offsets = {}
    for r in known[known.region != "Улаанбаатар"].sort_values("lat").itertuples():
        dy = -10 if any(abs(r.lat - lat) < 1.0 and abs(r.lon - lon) < 3 for lat, lon in offsets.values()) else 0
        offsets[r.Index] = (r.lat, r.lon)
        ax.annotate(f"{r.canonical_name} {r.winpct:.0%}", (r.lon, r.lat), xytext=(9, dy), textcoords="offset points",
                    fontsize=6.5, va="center")
    if len(ub):
        cx, cy = ub.lon.mean(), ub.lat.mean()
        lines = "\n".join(f"{r.canonical_name} {r.winpct:.0%}" for r in ub.sort_values("winpct", ascending=False).itertuples())
        ax.annotate(f"Улаанбаатар:\n{lines}", (cx, cy), xytext=(113.5, 51.6), textcoords="data", fontsize=6.5, va="top",
                    arrowprops={"arrowstyle": "-", "color": "#6B6B6B", "linewidth": 0.6},
                    bbox={"boxstyle": "round,pad=0.3", "facecolor": "white", "edgecolor": LIGHT})
    ax.set_xlim(87, 122)
    ax.set_ylim(41, 52.5)
    ax.set_aspect(1.3)
    ax.axis("off")
    ax.legend(frameon=False, loc="lower right", fontsize=7, markerscale=0.45,
              title="Бөмбөгийн хэмжээ = ялалтын хувь", title_fontsize=7)
    title = (f"{len(ub)} баг Улаанбаатарт төвлөрсөн; орон нутгийн {len(known) - len(ub)} баг"
             if len(known) else "Багуудын байршил")
    note = (f"Гэр хот нь эх сурвалжаар батлагдаагүй {len(unknown)} баг зурагдаагүй: "
            f"{', '.join(unknown.canonical_name.fillna(unknown.team_key))}" if len(unknown)
            else "Бүх багийн гэр хот эх сурвалжтай (0 баг дутуу)")
    return finish(fig, title, f"Багийн гэр хот ба {season.replace('-20', '–')} энгийн улирлын ялалтын хувь",
                  f"{source_mba()}; Wikipedia; хил: geoBoundaries (ODbL)", n=int(len(df)), uncertainty_note=note)


def transfer_edges(players_season: pd.DataFrame, src: str = "2025-2026", dst: str = "2026-2027") -> pd.DataFrame:
    a = players_season[players_season.season == src].drop_duplicates("player_id", keep="last")[["player_id", "team_key"]]
    b = players_season[players_season.season == dst].drop_duplicates("player_id", keep="last")[["player_id", "team_key"]]
    m = a.merge(b, on="player_id", suffixes=("_src", "_dst"))
    m = m[m.team_key_src != m.team_key_dst]
    return (m.groupby(["team_key_src", "team_key_dst"]).size().reset_index(name="n")
            .rename(columns={"team_key_src": "src_team", "team_key_dst": "dst_team"})
            .sort_values(["n", "src_team"], ascending=[False, True]).reset_index(drop=True))


def fig_transfer_network(edges: pd.DataFrame, names: dict):
    apply_style()
    G = nx.DiGraph()
    for r in edges.itertuples():
        G.add_edge(r.src_team, r.dst_team, weight=r.n)
    pos = nx.circular_layout(sorted(G.nodes()))
    incoming = {n: sum(d["weight"] for _, _, d in G.in_edges(n, data=True)) for n in G.nodes()}
    fig, ax = plt.subplots(figsize=(6.3, 5.2))
    nx.draw_networkx_edges(G, pos, ax=ax, width=[0.8 + 1.4 * d["weight"] for _, _, d in G.edges(data=True)],
                           edge_color="#9E9E9E", alpha=0.75, arrows=True, arrowsize=12,
                           connectionstyle="arc3,rad=0.12", node_size=[150 + 120 * incoming[n] for n in G.nodes()])
    nx.draw_networkx_nodes(G, pos, ax=ax, node_size=[150 + 120 * incoming[n] for n in G.nodes()],
                           node_color=PALETTE["blue"], alpha=0.9)
    for n, (x, y) in pos.items():
        ax.text(x * 1.18, y * 1.18, f"{names.get(n, n)}\n(+{incoming[n]})", ha="center", va="center", fontsize=7)
    ax.set_xlim(-1.5, 1.5)
    ax.set_ylim(-1.4, 1.4)
    ax.axis("off")
    top = max(incoming, key=incoming.get) if incoming else None
    title = (f"{names.get(top, top)} хамгийн олон ({incoming[top]}) тоглогч өөр багаас авсан" if top
             else "Улирал хооронд баг сольсон тоглогч алга")
    return finish(fig, title, "2025–26 → 2026–27 улиралд баг сольсон тоглогчид; сумны зузаан = тоглогчийн тоо, "
                  "зангилааны хэмжээ = орж ирсэн тоглогч", source_mba(), n=int(edges.n.sum()) or 1,
                  uncertainty_note="Улирал хоорондын тоглогчийг нэрээр тааруулсан (C2)")
