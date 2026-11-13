"""Шидэлтийн байршил, дамжуулалтын сүлжээ, тоглолтын явц, тоглолтын дундах ялах магадлал (play-by-play дата)."""
import matplotlib.pyplot as plt
import networkx as nx
import numpy as np
import pandas as pd
from matplotlib.colors import TwoSlopeNorm
from matplotlib.patches import Arc, Circle, Rectangle

from src.pbp import ZONES
from src.style import IMPORT_COLORS, IMPORT_LABELS, NEUTRAL, PALETTE, apply_style, finish, source_mba

PBP_SOURCE = "MBA тоглолтын хуудасны шидэлтийн байршил ба тоглолтын явц"


def _pts(shots: pd.DataFrame) -> pd.Series:
    return shots.made.astype(int) * (2 + shots.three.astype(int))


def draw_half_court(ax, color: str = "#8C8C8C", lw: float = 1.0) -> None:
    """FIBA-ийн хагас талбай (м): хэвтээ = талбайн өргөн 0–15, босоо = суурь шугамаас зай; сагс доод талд."""
    kw = {"color": color, "lw": lw, "fill": False}
    ax.add_patch(Rectangle((0, 0), 15, 14, **kw))
    ax.add_patch(Rectangle((7.5 - 2.45, 0), 4.9, 5.8, **kw))
    ax.add_patch(Circle((7.5, 1.575), 0.225, **kw))
    ax.plot([6.6, 8.4], [1.2, 1.2], color=color, lw=lw)
    ax.add_patch(Arc((7.5, 1.575), 2.5, 2.5, theta1=0, theta2=180, color=color, lw=lw))
    ax.add_patch(Arc((7.5, 5.8), 3.6, 3.6, theta1=0, theta2=180, color=color, lw=lw))
    ang = np.degrees(np.arcsin((7.5 - 0.9) / 6.75))
    ax.add_patch(Arc((7.5, 1.575), 13.5, 13.5, theta1=90 - ang, theta2=90 + ang, color=color, lw=lw))
    y_corner = 1.575 + 6.75 * np.cos(np.radians(ang))
    for x in (0.9, 14.1):
        ax.plot([x, x], [0, y_corner], color=color, lw=lw)
    ax.set_xlim(-0.3, 15.3)
    ax.set_ylim(-0.3, 10.5)
    ax.set_aspect("equal")
    ax.grid(False)
    ax.set_xticks([])
    ax.set_yticks([])
    for side in ("top", "right", "left", "bottom"):
        ax.spines[side].set_visible(False)


def zone_table(shots: pd.DataFrame, n_boot: int = 1000, seed: int = 42) -> pd.DataFrame:
    """Бүс бүрийн шидэлт бүрт ногдох оноо; хүрээг тоглолтоор дахин түүвэрлэж тооцно."""
    s = shots[shots.location_ok].assign(pts=_pts)
    rng = np.random.default_rng(seed)
    games = s.game_id.unique()
    per = s.groupby(["game_id", "zone"]).pts.agg(["sum", "size"]).unstack(fill_value=0)
    idx = rng.integers(0, len(games), (n_boot, len(games)))
    rows = []
    for z in ZONES:
        tot, n = per["sum"][z].reindex(games, fill_value=0).to_numpy(), per["size"][z].reindex(games, fill_value=0).to_numpy()
        boots = tot[idx].sum(1) / np.maximum(n[idx].sum(1), 1)
        rows.append({"zone": z, "n": int(n.sum()), "share": n.sum() / len(s), "pps": tot.sum() / max(n.sum(), 1),
                     "lo": float(np.percentile(boots, 2.5)), "hi": float(np.percentile(boots, 97.5))})
    return pd.DataFrame(rows)


def fig_shot_map(shots: pd.DataFrame, n_boot: int = 1000):
    apply_style()
    s = shots[shots.location_ok].assign(pts=_pts)
    league = s.pts.mean()
    fig, (ax, bx) = plt.subplots(1, 2, figsize=(6.3, 3.9), gridspec_kw={"width_ratios": [1.25, 1]})
    hb = ax.hexbin(s.court_y, s.court_x, C=s.pts, reduce_C_function=np.mean, gridsize=(12, 8),
                   extent=(0, 15, 0, 10.5), mincnt=40, cmap="RdBu_r", norm=TwoSlopeNorm(league, 0.5, 1.6),
                   linewidths=0.2, edgecolors="white")
    draw_half_court(ax)
    cb = fig.colorbar(hb, ax=ax, fraction=0.045, pad=0.02, orientation="horizontal")
    cb.set_label(f"Шидэлт бүрт ногдох оноо (лигийн дундаж {league:.2f})")
    ax._qa_skip = True
    z = zone_table(shots, n_boot=n_boot).sort_values("pps")
    y = np.arange(len(z))
    colors = np.where(z.pps >= league, PALETTE["vermillion"], PALETTE["blue"])
    bx.barh(y, z.pps, color=colors, height=0.6, alpha=0.85)
    bx.hlines(y, z.lo, z.hi, color="black", lw=1.2)
    bx.axvline(league, color=NEUTRAL, ls="--", lw=1)
    bx.set_yticks(y, [f"{n}\n({sh:.0%} шидэлт)" for n, sh in zip(z.zone, z.share)], fontsize=8)
    bx.set_xlabel("Шидэлт бүрт ногдох оноо")
    bx.set_xlim(0.6, max(z.hi) + 0.1)
    bx._qa_no_ylabel = True
    best, worst = z.iloc[-1], z.iloc[0]
    return finish(fig, f"Сагсны доорх шидэлт хамгийн үр ашигтай ({best.pps:.2f} оноо), "
                       f"{worst.zone.lower()} хамгийн бага ({worst.pps:.2f})",
                  "Зүүн: талбайн хэсэг бүрээс шидэхэд дунджаар хэдэн оноо авсан (улаан = дунджаас их, цэнхэр = бага; "
                  "40-өөс цөөн шидэлттэй хэсэг хоосон). Баруун: 5 бүсээр, хар зураас = 95% магадлалтай хүрээ",
                  f"{PBP_SOURCE} · 2025–26 ба 2026–27 улирал", n=int(len(s)), unit="шидэлт",
                  uncertainty_note=f"Хүрээг тоглолтуудыг {n_boot} удаа дахин сонгож тооцов; байршил нь 2/3 онооны "
                                   "шошготой зөрсөн 4%-ийг хассан")


def fig_shot_profile(shots: pd.DataFrame):
    apply_style()
    s = shots[shots.location_ok & shots.is_import.notna()]
    share = s.groupby([s.is_import.astype(bool), "zone"]).size().unstack(fill_value=0)
    share = share.div(share.sum(axis=1), axis=0)[ZONES]
    fig, ax = plt.subplots(figsize=(6.3, 3.6))
    y = np.arange(len(ZONES))
    for k, imp in enumerate((False, True)):
        vals = share.loc[imp].to_numpy()
        ax.barh(y + (k - 0.5) * 0.38, vals, height=0.36, color=IMPORT_COLORS[imp], label=IMPORT_LABELS[imp])
        for yy, v in zip(y + (k - 0.5) * 0.38, vals):
            ax.text(v + 0.005, yy, f"{v:.0%}", va="center", fontsize=8, color=IMPORT_COLORS[imp])
    ax.set_yticks(y, ZONES)
    ax.invert_yaxis()
    ax.xaxis.set_major_formatter(plt.FuncFormatter(lambda v, _: f"{v:.0%}"))
    ax.set_xlabel("Бүх шидэлтийн доторх хувь")
    ax.set_ylabel("Шидсэн бүс")
    ax.legend(frameon=False, loc="center right")
    three = {imp: share.loc[imp, ["Булангийн 3", "Гадна 3"]].sum() for imp in (False, True)}
    return finish(fig, f"Дотоод тоглогч шидэлтийнхээ {three[False]:.0%}-ийг 3 онооноос шиддэг, гадаад тоглогч "
                       f"{three[True]:.0%}",
                  "Тоглогчийн төрөл бүрийн шидэлт аль бүсээс хийгдсэнийг харьцуулав; багана бүр тухайн төрлийн нийт "
                  "шидэлтийн хувь (нийлбэр нь 100%)", f"{PBP_SOURCE} · 2025–26 ба 2026–27 улирал", n=int(len(s)),
                  unit="шидэлт")


def assist_edges(assists: pd.DataFrame, team_key: str) -> pd.DataFrame:
    a = assists[(assists.team_key == team_key) & assists.passer_id.notna() & assists.scorer_id.notna()]
    return a.groupby(["passer_id", "scorer_id"]).agg(n=("points", "size"), pts=("points", "sum")).reset_index()


def fig_assist_network(assists: pd.DataFrame, team_key: str, team_name: str, names: dict, is_import: dict,
                       min_count: int = 4):
    apply_style()
    e = assist_edges(assists, team_key)
    strong = e[e.n >= min_count]
    G = nx.DiGraph()
    for r in strong.itertuples():
        G.add_edge(r.passer_id, r.scorer_id, n=r.n)
    involvement = pd.concat([e.groupby("passer_id").n.sum(), e.groupby("scorer_id").n.sum()]).groupby(level=0).sum()
    nodes = sorted(G.nodes(), key=lambda n: -involvement.get(n, 0))
    pos = nx.circular_layout(nodes)
    fig, ax = plt.subplots(figsize=(6.3, 5.0))
    widths = [0.6 + 0.35 * G[u][v]["n"] for u, v in G.edges()]
    nx.draw_networkx_edges(G, pos, ax=ax, width=widths, edge_color="#9E9E9E", alpha=0.7, arrows=True, arrowsize=10,
                           connectionstyle="arc3,rad=0.15", node_size=[80 + 3 * involvement.get(n, 0) for n in G.nodes()])
    nx.draw_networkx_nodes(G, pos, ax=ax, node_size=[80 + 3 * involvement.get(n, 0) for n in G.nodes()],
                           node_color=[IMPORT_COLORS[bool(is_import.get(n, False))] for n in G.nodes()], alpha=0.9)
    for n, (x, y) in pos.items():
        ax.text(x * 1.27, y * 1.19, names.get(n, n), ha="center", va="center", fontsize=7.5)
    ax.set_xlim(-1.65, 1.65)
    ax.set_ylim(-1.38, 1.38)
    ax.axis("off")
    top = e.sort_values("n", ascending=False).iloc[0]
    return finish(fig, f"{team_name}: {names.get(top.passer_id, top.passer_id)} → {names.get(top.scorer_id, top.scorer_id)} "
                       f"хамгийн олон ({int(top.n)}) оновчтой дамжуулалт",
                  f"Сум = нэг тоглогч нөгөөдөө дамжуулж, тэр нь оносон (≥ {min_count} удаа). Сум зузаан = олон удаа, "
                  "тойрог том = олон дамжуулалтад оролцсон. Улаан-улбар = гадаад, цэнхэр = дотоод тоглогч",
                  f"{PBP_SOURCE} · 2025–26 улирлын үндсэн шат", n=int(e.n.sum()), unit="холбогдсон дамжуулалт",
                  uncertainty_note="Дамжуулалтын 87%-ийг шидэлттэй нь холбож чадсан; үлдсэн нь тоглолтын бичлэгт "
                                   "шидэлтээс хол бичигдсэн")


def lead_changes(e: pd.DataFrame) -> int:
    sign = np.sign(e.margin.to_numpy())
    sign = sign[sign != 0]
    return int((sign[1:] != sign[:-1]).sum())


def pick_dramatic_game(pbp: pd.DataFrame, games: pd.DataFrame, season: str = "2025-2026") -> int:
    ids = games[(games.season == season) & (games.phase == "regular")].game_id
    lc = {gid: lead_changes(e) for gid, e in pbp[pbp.game_id.isin(ids)].sort_values(["game_id", "seq"]).groupby("game_id")}
    return max(lc, key=lambda g: (lc[g], -g))


def fig_game_flow(pbp: pd.DataFrame, games: pd.DataFrame, params: dict, game_id: int | None = None):
    from src.inplay import REG_SEC, finalize, win_prob

    apply_style()
    game_id = game_id or pick_dramatic_game(pbp, games)
    g = games.set_index("game_id").loc[game_id]
    e = pbp[pbp.game_id == game_id].sort_values("seq")
    t = e.elapsed.to_numpy() / 60
    m = e.margin.to_numpy()
    wp = finalize(win_prob(params, m, np.clip(REG_SEC - e.elapsed.to_numpy(), 0, None), g.elo_pre_home - g.elo_pre_away),
                  m[-1])
    fig, (a1, a2) = plt.subplots(2, 1, figsize=(6.3, 4.6), sharex=True, gridspec_kw={"height_ratios": [1.2, 1]})
    a1.fill_between(t, m, 0, where=m >= 0, step="post", color=PALETTE["vermillion"], alpha=0.75, lw=0)
    a1.fill_between(t, m, 0, where=m < 0, step="post", color=PALETTE["blue"], alpha=0.75, lw=0)
    a1.axhline(0, color="black", lw=0.6)
    a1.set_ylabel("Онооны зөрүү")
    a1._qa_no_xlabel = True  # доод графиктай хэвтээ тэнхлэгээ хуваалцана
    a1.text(0.3, max(m.max(), 1) * 0.85, f"{g.home_team} тэргүүлж байна", color=PALETTE["vermillion"], fontsize=8)
    a1.text(0.3, min(m.min(), -1) * 0.85, f"{g.away_team} тэргүүлж байна", color=PALETTE["blue"], fontsize=8)
    a2.plot(t, wp, color="black", lw=1.4, drawstyle="steps-post")
    a2.axhline(0.5, color=NEUTRAL, ls=":", lw=1)
    a2.set_ylim(0, 1)
    a2.yaxis.set_major_formatter(plt.FuncFormatter(lambda v, _: f"{v:.0%}"))
    a2.set_ylabel(f"{g.home_team}\nялах магадлал", fontsize=8.5)
    a2.set_xlabel("Тоглолтын минут")
    for ax in (a1, a2):
        for q in (10, 20, 30):
            ax.axvline(q, color="#D9D9D9", lw=0.8)
    n_lc = lead_changes(e)
    return finish(fig, f"{g.home_team} {int(g.home_pts)}–{int(g.away_pts)} {g.away_team}: тэргүүлэгч {n_lc} удаа солигдсон",
                  "Дээр: онооны зөрүү минут бүрээр (улаан-улбар = гэрийн баг, цэнхэр = зочин баг тэргүүлсэн). "
                  "Доор: загварын тооцсон гэрийн баг ялах магадлал — зөрүү ба үлдсэн хугацаанаас хамаарна",
                  f"{PBP_SOURCE} · {g.date}", n=int(len(e)), unit="үйл явдал")


def fig_inplay_accuracy(minute: pd.DataFrame):
    apply_style()
    fig, ax = plt.subplots(figsize=(6.3, 3.8))
    for key, color, label in (("model", PALETTE["blue"], "Загвар (зөрүү + хугацаа + хүч)"),
                              ("leader", NEUTRAL, "Энгийн дүрэм: одоо тэргүүлж буй нь ялна")):
        ax.fill_between(minute.minute, minute[f"lo_{key}"], minute[f"hi_{key}"], color=color, alpha=0.18, lw=0)
        ax.plot(minute.minute, minute[f"acc_{key}"], color=color, lw=2 if key == "model" else 1.4,
                ls="-" if key == "model" else "--", label=label)
    ax.axhline(0.5, color="black", lw=0.6, ls=":")
    ax.set_ylim(0.4, 1)
    ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda v, _: f"{v:.0%}"))
    ax.set_xlabel("Тоглолтын минут (таамаглал хийсэн мөч)")
    ax.set_ylabel("Ялагчийг зөв таамагласан хувь")
    ax.legend(frameon=False, loc="upper left")
    at = minute.set_index("minute")
    m20, m35 = at.loc[20, "acc_model"], at.loc[35, "acc_model"]
    return finish(fig, f"Хагас дуусахад ялагчийг {m20:.0%}, 35-р минутад {m35:.0%} зөв таамаглана",
                  "Шугам = тухайн минутад хийсэн таамаглалын зөв хувь, сүүдэр = 95% магадлалтай хүрээ. Загвар энгийн "
                  "дүрмээс зөв хувиар илүү биш ч «хэр итгэлтэй» гэдгийг магадлалаар өгдөг",
                  f"{PBP_SOURCE} · 2025–26 ба 2026–27 улирал", n=int(minute.n.iloc[0]), unit="тоглолт",
                  uncertainty_note="Тоглолтоор нь бүлэглэн 5 хэсэгт хувааж шалгав (нэг тоглолт сургалт, тест хоёрт "
                                   "зэрэг ордоггүй); хүрээг тоглолтоор дахин түүвэрлэж тооцов")
