import json
from pathlib import Path

import numpy as np
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots

from src.charts import LABELS as CHART_LABELS
from src.palette import IMPORT_COLORS, IMPORT_LABELS, NEUTRAL, PALETTE, POS_COLORS, cluster_colors
from src.uncertainty import funnel_limits

A_COLOR, B_COLOR = PALETTE["blue"], PALETTE["vermillion"]
LIGHTEST = "#D0D0D0"
FONT = dict(family="Fira Sans, Arial, sans-serif", size=14, color="#0F172A")
LABELS = {**CHART_LABELS, "EFF": "Үр ашгийн оноо (EFF)"}


def _layout(fig: go.Figure, title: str, height: int = 420, **kw) -> go.Figure:
    fig.update_layout(title=dict(text=title, x=0, font=dict(size=17, color="#0F172A")), font=FONT, height=height,
                      margin=dict(l=10, r=10, t=60, b=10), plot_bgcolor="white", paper_bgcolor="white",
                      hovermode="closest", hoverlabel=dict(font=dict(family=FONT["family"], size=14)),
                      legend=dict(orientation="h", y=-0.22), **kw)
    fig.update_xaxes(showgrid=True, gridcolor="#E2E8F0", zeroline=False, title_font=dict(size=14))
    fig.update_yaxes(showgrid=True, gridcolor="#E2E8F0", zeroline=False, title_font=dict(size=14))
    return fig


def px_scatter(df: pd.DataFrame, x: str, y: str, color_by: str, highlight_team: str | None = None) -> go.Figure:
    fig = go.Figure()
    if color_by == "position":
        groups = [(p, POS_COLORS[p], df.position == p) for p in POS_COLORS]
    elif color_by == "is_import":
        groups = [(IMPORT_LABELS[v], IMPORT_COLORS[v], df.is_import.astype(bool) == v) for v in (False, True)]
    else:
        cmap = cluster_colors(df.cluster_name.dropna())
        groups = [(n, c, df.cluster_name == n) for n, c in cmap.items()] + [("Бүлэггүй", NEUTRAL, df.cluster_name.isna())]
    for name, color, mask in groups:
        part = df[mask]
        if part.empty:
            continue
        line = [2 if t == highlight_team else 0 for t in part.team]
        fig.add_trace(go.Scattergl(
            x=part[x], y=part[y], mode="markers", name=name, customdata=part[["player_id", "player_name", "team"]],
            marker=dict(color=color, size=9, opacity=0.8, line=dict(width=line, color="black")),
            hovertemplate="<b>%{customdata[1]}</b><br>%{customdata[2]}<br>" + f"{LABELS.get(x, x)}: " + "%{x:.2f}<br>"
                          + f"{LABELS.get(y, y)}: " + "%{y:.2f}<extra></extra>"))
    fig.update_xaxes(title=LABELS.get(x, x))
    fig.update_yaxes(title=LABELS.get(y, y))
    return _layout(fig, f"{LABELS.get(y, y)} ба {LABELS.get(x, x)} — цэг бүр 1 тоглогч", dragmode="select")


def px_funnel(players: pd.DataFrame, show_ci: bool) -> go.Figure:
    df = players.assign(tsa=players.FGA.fillna(0) + 0.44 * players.FTA.fillna(0))
    df = df[(df.tsa > 0) & df.ts_pct.notna()]
    p0 = df.PTS_total.sum() / (2 * df.tsa.sum())
    fig = go.Figure()
    grid = np.linspace(max(df.tsa.min(), 1), df.tsa.max(), 150)
    if show_ci:
        for z, name, alpha in ((3.09, "99.8% хүрээ", 0.12), (1.96, "95% хүрээ", 0.22)):
            lo, hi = funnel_limits(p0, grid, z)
            fig.add_trace(go.Scatter(x=np.r_[grid, grid[::-1]], y=np.r_[hi, lo[::-1]], fill="toself", name=name,
                                     fillcolor=f"rgba(86,180,233,{alpha})", line=dict(width=0), hoverinfo="skip"))
    lo95, hi95 = funnel_limits(p0, df.tsa.to_numpy(), 1.96)
    colors = np.where(df.ts_pct > hi95, PALETTE["green"], np.where(df.ts_pct < lo95, PALETTE["vermillion"], NEUTRAL))
    fig.add_trace(go.Scattergl(x=df.tsa, y=df.ts_pct, mode="markers", name="Тоглогч", marker=dict(color=colors, size=8),
                               customdata=df[["player_name", "team"]],
                               hovertemplate="<b>%{customdata[0]}</b> (%{customdata[1]})<br>Оновч %{y:.1%}<br>"
                                             "Шидэлт %{x:.0f}<extra></extra>"))
    fig.add_hline(y=p0, line_color="black", annotation_text=f"Лигийн дундаж {p0:.0%}")
    fig.update_xaxes(title="Шидэлтийн тоо (торгуулийг оролцуулан)")
    fig.update_yaxes(title="Шидэлтийн оновч", tickformat=".0%")
    above = int((df.ts_pct > hi95).sum())
    return _layout(fig, f"{above} тоглогчийн оновч лигийн дунджаас үнэхээр өндөр")


def px_dot_ci(ci: pd.DataFrame, show_ci: bool, metric_label: str) -> go.Figure:
    df = ci.sort_values("est")
    colors = df.is_import.astype(bool).map(IMPORT_COLORS) if "is_import" in df else A_COLOR
    err = dict(type="data", symmetric=False, array=df.hi - df.est, arrayminus=df.est - df.lo, color=NEUTRAL,
               thickness=2) if show_ci else None
    fig = go.Figure(go.Scatter(x=df.est, y=df.player_name, mode="markers", error_x=err,
                               name="95% хүрээ" if show_ci else "Тооцоолсон утга", marker=dict(color=colors, size=10),
                               hovertemplate="<b>%{y}</b><br>%{x:.2f}<extra></extra>"))
    fig.update_xaxes(title=metric_label)
    return _layout(fig, f"Шилдэг {len(df)}: {metric_label}" + (" (шугам = 95% хүрээ)" if show_ci else ""),
                   height=max(320, 26 * len(df) + 120), showlegend=False)


def px_pareto(df: pd.DataFrame, show_ci: bool, title: str) -> go.Figure:
    fig = make_subplots(specs=[[{"secondary_y": True}]])
    fig.add_trace(go.Bar(x=df["rank"], y=df.value, marker_color=df.is_import.astype(bool).map(IMPORT_COLORS)
                         if "is_import" in df else A_COLOR, name="Оноо", customdata=df.player_name,
                         hovertemplate="#%{x} %{customdata}: %{y:.0f} оноо<extra></extra>"), secondary_y=False)
    if show_ci and "lo" in df:
        fig.add_trace(go.Scatter(x=np.r_[df["rank"], df["rank"][::-1]], y=np.r_[df.hi, df.lo[::-1]], fill="toself",
                                 fillcolor="rgba(0,0,0,0.15)", line=dict(width=0), name="Нийлбэр хувийн 95% хүрээ",
                                 hoverinfo="skip"), secondary_y=True)
    fig.add_trace(go.Scatter(x=df["rank"], y=df.cum_share, mode="lines", line=dict(color="black"),
                             name="Нийлбэр хувь", hovertemplate="Эхний %{x} тоглогч: %{y:.0%}<extra></extra>"),
                  secondary_y=True)
    k = int(np.argmax(df.cum_share.to_numpy() >= 0.8)) + 1
    fig.add_hline(y=0.8, line_dash="dash", line_color=B_COLOR, secondary_y=True)
    fig.add_annotation(x=k, y=0.8, yref="y2", text=f"Эхний {k} ({k / len(df):.0%}) = 80%", showarrow=True,
                       font=dict(color=B_COLOR))
    fig.update_yaxes(title="Оноо", rangemode="tozero", secondary_y=False)
    fig.update_yaxes(title="Нийлбэр хувь", tickformat=".0%", range=[0, 1.02], dtick=0.2, secondary_y=True, showgrid=False)
    fig.update_xaxes(title="Тоглогч (оноогоор эрэмбэлсэн)")
    return _layout(fig, title)


def px_fan(tg: pd.DataFrame, team_key: str, show_ci: bool, others: bool = True) -> go.Figure:
    fig = go.Figure()
    if others:
        for key, part in tg.groupby("team_key"):
            if key != team_key:
                fig.add_trace(go.Scatter(x=part.date, y=part.winpct, mode="lines", line=dict(color=LIGHTEST, width=1),
                                         name=part.team.iloc[0], showlegend=False,
                                         hovertemplate=f"{part.team.iloc[0]}: " + "%{y:.0%}<extra></extra>"))
    t = tg[tg.team_key == team_key]
    if t.empty:
        return _layout(fig, "Баг сонгоно уу")
    if show_ci:
        for lvl, alpha in (("95", 0.12), ("80", 0.2), ("50", 0.3)):
            fig.add_trace(go.Scatter(x=np.r_[t.date, t.date[::-1]], y=np.r_[t[f"hi{lvl}"], t[f"lo{lvl}"][::-1]],
                                     fill="toself", fillcolor=f"rgba(213,94,0,{alpha})", line=dict(width=0),
                                     name=f"{lvl}% хүрээ", hoverinfo="skip"))
    fig.add_trace(go.Scatter(x=t.date, y=t.winpct, mode="lines+markers", line=dict(color=B_COLOR, width=3),
                             name=t.team.iloc[0], customdata=np.c_[t.wins, t.games],
                             hovertemplate="%{y:.0%} (%{customdata[0]}/%{customdata[1]})<extra></extra>"))
    fig.add_hline(y=0.5, line_dash="dot", line_color="black")
    fig.update_yaxes(title="Тухайн өдөр хүртэлх ялалтын хувь", tickformat=".0%", range=[0, 1])
    fig.update_xaxes(title="Огноо")
    return _layout(fig, f"{t.team.iloc[0]}: ялалтын хувь улирлын турш" + (" (сүүдэр = магадлалтай хүрээ)" if show_ci else ""))



def px_quantile_dots(p: float, n: int = 20, team_a: str = "А", team_b: str = "Б") -> go.Figure:
    k = int(round(p * n))
    cols, rows = 10, int(np.ceil(n / 10))
    xs = [i % cols for i in range(n)]
    ys = [rows - 1 - i // cols for i in range(n)]
    colors = [A_COLOR] * k + [B_COLOR] * (n - k)
    fig = go.Figure(go.Scatter(x=xs, y=ys, mode="markers", marker=dict(color=colors, size=26),
                               hoverinfo="skip", showlegend=False))
    fig.update_xaxes(visible=False, range=[-0.7, cols - 0.3])
    fig.update_yaxes(visible=False, range=[-0.7, rows - 0.3])
    return _layout(fig, f"{n} тоглолт тоглогдвол: {team_a} ≈ {k}, {team_b} ≈ {n - k} ялна", height=200)


def px_clusters(clusters: pd.DataFrame, selected: str | None = None) -> go.Figure:
    fig = go.Figure()
    cmap = cluster_colors(clusters.cluster_name)
    for name, color in cmap.items():
        part = clusters[clusters.cluster_name == name]
        fig.add_trace(go.Scattergl(x=part.pc1, y=part.pc2, mode="markers", name=name,
                                   marker=dict(color=color, size=9, opacity=(0.15 + 0.85 * part.coassign).tolist()),
                                   customdata=np.c_[part.player_name, part.coassign],
                                   hovertemplate="<b>%{customdata[0]}</b><br>Бүлэгтээ тогтвортой %{customdata[1]:.0%}"
                                                 "<extra>" + name + "</extra>"))
    if selected is not None:
        s = clusters[clusters.player_id == selected]
        fig.add_trace(go.Scatter(x=s.pc1, y=s.pc2, mode="markers", name="Сонгосон",
                                 marker=dict(symbol="star", size=20, color="black")))
    fig.update_xaxes(title="Хэв маягийн 1-р тэнхлэг")
    fig.update_yaxes(title="Хэв маягийн 2-р тэнхлэг")
    return _layout(fig, "Тоглолтын хэв маяг: ойр цэг = төстэй тоглогч")


FACTORS = [("efg", "Оновч", True), ("tov_pct", "Бөмбөг алдалт", False), ("orb_pct", "Довт. самбар", True),
           ("ftr", "Торгууль авалт", True)]


def px_four_factors(tg: pd.DataFrame, highlight: str | None = None) -> go.Figure:
    reg = tg[tg.phase == "regular"]
    means = reg.groupby("team")[[f for f, _, _ in FACTORS]].mean()
    league = reg[[f for f, _, _ in FACTORS]].mean()
    fig = make_subplots(rows=1, cols=4, subplot_titles=[f"{l} ({'их' if hb else 'бага'} нь сайн)" for _, l, hb in FACTORS],
                        shared_yaxes=True)
    order = (means["efg"] - league["efg"]).sort_values().index
    for i, (f, lbl, hb) in enumerate(FACTORS, 1):
        dev = (means[f] - league[f]).reindex(order) * 100
        good = dev > 0 if hb else dev < 0
        colors = [("black" if t == highlight else (A_COLOR if g else B_COLOR)) for t, g in zip(dev.index, good)]
        fig.add_trace(go.Bar(x=dev, y=dev.index, orientation="h", marker_color=colors, showlegend=False,
                             hovertemplate="%{y}: дунджаас %{x:+.1f}<extra>" + lbl + "</extra>"), row=1, col=i)
        fig.update_xaxes(title="Дунджаас зөрүү", row=1, col=i)
    return _layout(fig, "Ялалтын 4 хүчин зүйл: баг бүр лигийн дунджаас хэр сайн/сул вэ", height=470)


def px_elo(games: pd.DataFrame, highlight: str | None = None) -> go.Figure:
    rows = pd.concat([games[["date", "season", "home_team", "elo_post_home"]].set_axis(["date", "season", "team", "elo"], axis=1),
                      games[["date", "season", "away_team", "elo_post_away"]].set_axis(["date", "season", "team", "elo"], axis=1)])
    rows = rows.sort_values("date")
    fig = go.Figure()
    for (team, season), part in rows.groupby(["team", "season"]):
        hl = team == highlight
        fig.add_trace(go.Scatter(x=part.date, y=part.elo, mode="lines", name=team, showlegend=False,
                                 line=dict(color=B_COLOR if hl else LIGHTEST, width=3 if hl else 1),
                                 hovertemplate=f"{team}: " + "%{y:.0f}<extra></extra>"))
    fig.add_hline(y=1500, line_dash="dot")
    fig.update_yaxes(title="Багийн хүчний оноо (Elo)")
    fig.update_xaxes(title="Огноо")
    return _layout(fig, "Багийн хүчний онооны явц" + (f" — {highlight}" if highlight else ""))


def px_map(meta: pd.DataFrame, standings: pd.DataFrame, geojson_path: Path, season: str) -> go.Figure:
    geo = json.loads(Path(geojson_path).read_text(encoding="utf-8"))
    st = standings[standings.season == season].assign(winpct=lambda d: d.W / (d.W + d.L)).merge(meta, on="team_key")
    known = st[st.lat.notna()]
    # Аймгийн хилийг шугамаар зурна: geojson-ий эргэлтийн чиглэл plotly-ийн шаардлагаас өөр тул Choropleth дүүргэлт
    # бүх дэлхийг саарал болгодог.
    lons, lats = [], []
    for feat in geo["features"]:
        g = feat["geometry"]
        polys = g["coordinates"] if g["type"] == "MultiPolygon" else [g["coordinates"]]
        for poly in polys:
            ring = np.asarray(poly[0])[:, :2]
            lons += ring[:, 0].tolist() + [None]
            lats += ring[:, 1].tolist() + [None]
    fig = go.Figure(go.Scattergeo(lon=lons, lat=lats, mode="lines", line=dict(color="#94A3B8", width=0.8),
                                  hoverinfo="skip", showlegend=False, fill="none"))
    for region, color in (("Улаанбаатар", B_COLOR), ("Орон нутаг", A_COLOR)):
        part = known[known.region == region]
        fig.add_trace(go.Scattergeo(lon=part.lon, lat=part.lat, mode="markers", name=region,
                                    marker=dict(size=10 + 40 * part.winpct, color=color, opacity=0.75),
                                    text=part.canonical_name + " — " + (part.winpct * 100).round(0).astype(str) + "%",
                                    hovertemplate="%{text}<extra></extra>"))
    fig.update_geos(visible=False, projection_type="mercator", lonaxis_range=[87, 120.5], lataxis_range=[41.3, 52.3],
                    bgcolor="white")
    unknown = len(st) - len(known)
    title = "Багийн хот ба ялалтын хувь" + (f" ({unknown} багийн хот тодорхойгүй)" if unknown else "")
    return _layout(fig, title, height=400)


# ---------- Шидэлт ба тоглолтын явц ----------
def _arc(cx, cy, r, a0, a1, n=60):
    t = np.radians(np.linspace(a0, a1, n))
    return cx + r * np.cos(t), cy + r * np.sin(t)


def court_traces(color: str = "#94A3B8") -> list[go.Scatter]:
    """FIBA-ийн хагас талбай: хэвтээ = өргөн 0–15 м, босоо = суурь шугамаас зай, сагс (7.5; 1.575)."""
    ang = np.degrees(np.arcsin(6.6 / 6.75))
    yc = 1.575 + 6.75 * np.cos(np.radians(ang))
    parts = [
        ([0, 15, 15, 0, 0], [0, 0, 10.5, 10.5, 0]),
        ([5.05, 5.05, 9.95, 9.95], [0, 5.8, 5.8, 0]),
        _arc(7.5, 1.575, 0.225, 0, 360), _arc(7.5, 1.575, 1.25, 0, 180), _arc(7.5, 5.8, 1.8, 0, 180),
        ([0.9, 0.9], [0, yc]), ([14.1, 14.1], [0, yc]), _arc(7.5, 1.575, 6.75, 90 - ang, 90 + ang),
        ([6.6, 8.4], [1.2, 1.2]),
    ]
    return [go.Scatter(x=list(x), y=list(y), mode="lines", line=dict(color=color, width=1.2), hoverinfo="skip",
                       showlegend=False) for x, y in parts]


def shot_cells(shots: pd.DataFrame, size: float = 1.0, min_n: int = 5) -> pd.DataFrame:
    s = shots[shots.location_ok]
    cx = (s.court_y // size) * size + size / 2
    cy = (s.court_x // size) * size + size / 2
    c = s.assign(cx=cx, cy=cy).groupby(["cx", "cy"]).agg(n=("pts", "size"), pps=("pts", "mean"),
                                                        fg=("made", "mean")).reset_index()
    return c[(c.n >= min_n) & (c.cy <= 10.5)]


def px_shot_map(shots: pd.DataFrame, league_pps: float, title: str) -> go.Figure:
    c = shot_cells(shots, min_n=max(3, len(shots) // 800))
    fig = go.Figure(court_traces())
    if len(c):
        fig.add_trace(go.Scatter(
            x=c.cx, y=c.cy, mode="markers", showlegend=False,
            marker=dict(symbol="square", size=(8 + 30 * np.sqrt(c.n / c.n.max())).tolist(), color=c.pps,
                        colorscale="RdBu_r", cmid=league_pps, cmin=0.4, cmax=1.8, line=dict(width=0),
                        colorbar=dict(title=dict(text="Оноо /<br>шидэлт", side="top"), thickness=12, len=0.7)),
            customdata=np.c_[c.n, c.fg],
            hovertemplate="%{customdata[0]} шидэлт<br>Оносон %{customdata[1]:.0%}<br>Шидэлт бүрт %{marker.color:.2f} "
                          "оноо<extra></extra>"))
    fig.update_xaxes(visible=False, range=[-0.3, 15.3])
    fig.update_yaxes(visible=False, range=[-0.3, 10.8], scaleanchor="x", scaleratio=1)
    return _layout(fig, title, height=470)


def px_zone_bars(zones: pd.DataFrame, league_pps: float) -> go.Figure:
    z = zones.sort_values("pps")
    fig = go.Figure(go.Bar(x=z.pps, y=z.zone, orientation="h",
                           marker_color=[B_COLOR if v >= league_pps else A_COLOR for v in z.pps],
                           customdata=np.c_[z.n, z.share], text=[f"{v:.2f}" for v in z.pps], textposition="outside",
                           hovertemplate="%{y}: шидэлт бүрт %{x:.2f} оноо<br>%{customdata[0]} шидэлт "
                                         "(%{customdata[1]:.0%})<extra></extra>"))
    fig.add_vline(x=league_pps, line_dash="dash", line_color=NEUTRAL,
                  annotation_text=f"Лигийн дундаж {league_pps:.2f}", annotation_position="top")
    fig.update_xaxes(title="Шидэлт бүрт ногдох оноо", range=[0, max(1.6, z.pps.max() + 0.25)])
    return _layout(fig, "Бүс бүрийн үр ашиг", height=330, showlegend=False)


def px_assist_network(edges: pd.DataFrame, involvement: pd.Series, is_import: dict, title: str) -> go.Figure:
    nodes = list(involvement.sort_values(ascending=False).index)
    ang = np.linspace(0, 2 * np.pi, len(nodes), endpoint=False)
    pos = {n: (np.cos(a), np.sin(a)) for n, a in zip(nodes, ang)}
    fig = go.Figure()
    mx = max(edges.n.max(), 1) if len(edges) else 1
    for r in edges.itertuples():
        (x0, y0), (x1, y1) = pos[r.passer], pos[r.scorer]
        fig.add_trace(go.Scatter(x=[x0, x1], y=[y0, y1], mode="lines", showlegend=False, hoverinfo="text",
                                 text=f"{r.passer} → {r.scorer}: {r.n} удаа",
                                 line=dict(color=f"rgba(100,116,139,{0.25 + 0.6 * r.n / mx})", width=1 + 7 * r.n / mx)))
        fig.add_annotation(x=x1, y=y1, ax=x0, ay=y0, xref="x", yref="y", axref="x", ayref="y", showarrow=True,
                           arrowhead=2, arrowsize=1, arrowwidth=1, arrowcolor="rgba(100,116,139,0.6)", text="",
                           standoff=12)
    fig.add_trace(go.Scatter(
        x=[pos[n][0] for n in nodes], y=[pos[n][1] for n in nodes], mode="markers+text", showlegend=False,
        text=nodes, textposition=["top center" if pos[n][1] >= 0 else "bottom center" for n in nodes],
        marker=dict(size=(12 + 30 * np.sqrt(involvement[nodes] / involvement.max())).tolist(),
                    color=[IMPORT_COLORS[bool(is_import.get(n, False))] for n in nodes], line=dict(color="white", width=1)),
        customdata=involvement[nodes].to_numpy(), hovertemplate="%{text}: %{customdata} дамжуулалтад оролцсон<extra></extra>"))
    fig.update_xaxes(visible=False, range=[-1.45, 1.45])
    fig.update_yaxes(visible=False, range=[-1.35, 1.35], scaleanchor="x")
    return _layout(fig, title, height=520)


def px_game_flow(flow: pd.DataFrame, wp: np.ndarray, home: str, away: str, show_ci_line: bool = True) -> go.Figure:
    t = flow.elapsed / 60
    fig = make_subplots(rows=2, cols=1, shared_xaxes=True, row_heights=[0.55, 0.45], vertical_spacing=0.08)
    pos, neg = flow.margin.clip(lower=0), flow.margin.clip(upper=0)
    fig.add_trace(go.Scatter(x=t, y=pos, line=dict(shape="hv", width=0), fill="tozeroy", fillcolor="rgba(213,94,0,0.75)",
                             name=f"{home} тэргүүлсэн", hoverinfo="skip"), row=1, col=1)
    fig.add_trace(go.Scatter(x=t, y=neg, line=dict(shape="hv", width=0), fill="tozeroy", fillcolor="rgba(0,114,178,0.75)",
                             name=f"{away} тэргүүлсэн", hoverinfo="skip"), row=1, col=1)
    fig.add_trace(go.Scatter(x=t, y=flow.margin, mode="lines", line=dict(shape="hv", color="rgba(0,0,0,0)"),
                             showlegend=False, customdata=np.c_[flow.home, flow.away],
                             hovertemplate="%{x:.1f} мин: %{customdata[0]}–%{customdata[1]}<extra></extra>"), row=1, col=1)
    fig.add_trace(go.Scatter(x=t, y=wp, mode="lines", line=dict(shape="hv", color="black", width=2),
                             name=f"{home} ялах магадлал", hovertemplate="%{x:.1f} мин: %{y:.0%}<extra></extra>"),
                  row=2, col=1)
    fig.add_hline(y=0.5, line_dash="dot", line_color=NEUTRAL, row=2, col=1)
    for q in (10, 20, 30):
        fig.add_vline(x=q, line_color="#E2E8F0")
    fig.update_yaxes(title="Онооны зөрүү", row=1, col=1)
    fig.update_yaxes(title="Ялах магадлал", tickformat=".0%", range=[0, 1], row=2, col=1)
    fig.update_xaxes(title="Тоглолтын минут", row=2, col=1)
    return _layout(fig, f"{home} – {away}: тоглолтын явц", height=520)


def px_inplay_accuracy(minute: pd.DataFrame, show_ci: bool) -> go.Figure:
    fig = go.Figure()
    for key, color, name, dash in (("model", A_COLOR, "Загвар", "solid"), ("leader", NEUTRAL, "Одоо тэргүүлж буй нь ялна", "dash")):
        if show_ci:
            fig.add_trace(go.Scatter(x=np.r_[minute.minute, minute.minute[::-1]],
                                     y=np.r_[minute[f"hi_{key}"], minute[f"lo_{key}"][::-1]], fill="toself",
                                     fillcolor="rgba(0,114,178,0.15)" if key == "model" else "rgba(158,158,158,0.18)",
                                     line=dict(width=0), name=f"{name}: 95% хүрээ", hoverinfo="skip"))
        fig.add_trace(go.Scatter(x=minute.minute, y=minute[f"acc_{key}"], mode="lines", name=name,
                                 line=dict(color=color, width=3 if key == "model" else 2, dash=dash),
                                 hovertemplate="%{x}-р минут: %{y:.0%}<extra>" + name + "</extra>"))
    fig.update_yaxes(title="Ялагчийг зөв таамагласан хувь", tickformat=".0%", range=[0.4, 1])
    fig.update_xaxes(title="Тоглолтын минут")
    return _layout(fig, "Тоглолт урагшлах тусам ялагчийг хэр зөв таамаглах вэ", height=400)


# ---------- Олдворууд ----------
COUNT_COLORS = {0: "#D9D9D9", 1: "#FDCC8A", 2: "#E66101", 3: "#7F2704"}


def px_imports_on_court(df: pd.DataFrame) -> go.Figure:
    seasons = sorted(df.season.unique())
    fig = make_subplots(rows=1, cols=len(seasons), shared_yaxes=True,
                        subplot_titles=[s.replace("-20", "–") + " улирал" for s in seasons])
    for c, season in enumerate(seasons, 1):
        d = df[df.season == season]
        for k in sorted(df.k.unique()):
            part = d[d.k == k]
            fig.add_trace(go.Bar(x=[f"{q}-р үе" for q in part.period], y=part.share, name=f"{int(k)} гадаад тоглогч",
                                 marker_color=COUNT_COLORS[int(k)], legendgroup=str(k), showlegend=c == 1,
                                 hovertemplate="%{x}: хугацааны %{y:.0%}<extra>" + f"{int(k)} гадаад</extra>"), row=1, col=c)
        m = d.drop_duplicates("period")
        for r in m.itertuples():
            fig.add_annotation(x=f"{r.period}-р үе", y=1.02, yanchor="bottom", showarrow=False, row=1, col=c,
                               text=f"дундаж {r.mean_k:.1f}<br>оноо {r.import_pts_share:.0%}", font=dict(size=12))
    fig.update_yaxes(tickformat=".0%", range=[0, 1.2], title="Тоглох хугацааны хувь", row=1, col=1)
    fig.update_yaxes(tickformat=".0%", range=[0, 1.2], tickvals=[0, 0.25, 0.5, 0.75, 1])
    return _layout(fig, "Нэг баг талбай дээр хэдэн гадаад тоглогчтой тоглодог вэ", height=440, barmode="stack")


def px_lead_safety(df: pd.DataFrame, show_ci: bool) -> go.Figure:
    fig = go.Figure()
    colors = ["#56B4E9", A_COLOR, "#08306B"]
    for color, (name, d) in zip(colors, df.groupby("checkpoint", sort=False)):
        err = dict(type="data", symmetric=False, array=d.hi - d.est, arrayminus=d.est - d.lo, thickness=1.5) if show_ci else None
        fig.add_trace(go.Scatter(x=d.bin, y=d.est, mode="lines+markers", name=name, line=dict(color=color, width=2.5),
                                 marker=dict(size=9), error_y=err, customdata=np.c_[d.n, d.lo, d.hi],
                                 hovertemplate="%{x} оноогоор тэргүүлсэн: %{y:.0%} ялсан<br>%{customdata[0]} тоглолт, хүрээ "
                                               "%{customdata[1]:.0%}–%{customdata[2]:.0%}<extra>" + name + "</extra>"))
    fig.add_hline(y=0.5, line_dash="dot", line_color="black")
    fig.update_yaxes(title="Тэргүүлж байсан баг ялсан хувь", tickformat=".0%", range=[0.2, 1.03])
    fig.update_xaxes(title="Тухайн мөчид хэдэн оноогоор тэргүүлж байсан", type="category")
    return _layout(fig, "Тэргүүлэл хэр найдвартай вэ", height=430)


def px_comebacks(df: pd.DataFrame) -> go.Figure:
    c = df.deficit.value_counts().sort_index()
    xs = np.arange(0, c.index.max() + 1)
    ys = c.reindex(xs, fill_value=0)
    fig = go.Figure(go.Bar(x=xs, y=ys, marker_color=[B_COLOR if x >= 10 else NEUTRAL for x in xs],
                           hovertemplate="%{x} оноогоор хоцорч байгаад ялсан: %{y} тоглолт<extra></extra>"))
    share = (df.deficit >= 10).mean()
    fig.add_annotation(x=12, y=ys.max() * 0.8, showarrow=False, font=dict(color=B_COLOR, size=14),
                       text=f"10+ оноогоор хоцорч<br>байгаад ялсан: {share:.0%}")
    fig.update_xaxes(title="Ялсан баг хамгийн ихдээ хэдэн оноогоор хоцорч байсан")
    fig.update_yaxes(title="Тоглолтын тоо")
    return _layout(fig, "Эргэлт хэр их тохиолддог вэ", height=400, showlegend=False)


def px_distance(df: pd.DataFrame, league_pps: float, show_ci: bool) -> go.Figure:
    colors = [B_COLOR if t > 0.5 else A_COLOR for t in df.three_share]
    labels = [f"{a:g}–{b:g} м" if b < 20 else f"{a:g} м+" for a, b in zip(df.lo_m, df.hi_m)]
    fig = make_subplots(rows=2, cols=1, shared_xaxes=True, row_heights=[0.68, 0.32], vertical_spacing=0.06)
    err = dict(type="data", symmetric=False, array=df.hi - df.pps, arrayminus=df.pps - df.lo, thickness=1.5) if show_ci else None
    fig.add_trace(go.Scatter(x=df.mid, y=df.pps, mode="lines+markers", line=dict(color=NEUTRAL, width=1),
                             marker=dict(color=colors, size=11), error_y=err, customdata=np.c_[labels, df.fg, df.n],
                             hovertemplate="%{customdata[0]}: шидэлт бүрт %{y:.2f} оноо<br>оносон %{customdata[1]:.0%}, "
                                           "%{customdata[2]} шидэлт<extra></extra>", showlegend=False), row=1, col=1)
    fig.add_trace(go.Bar(x=df.mid, y=df.n, width=(df.hi_m.clip(upper=10) - df.lo_m) * 0.9, marker_color=colors,
                         customdata=labels, hovertemplate="%{customdata}: %{y} шидэлт<extra></extra>", showlegend=False),
                  row=2, col=1)
    fig.add_hline(y=league_pps, line_dash="dot", line_color="black", row=1, col=1,
                  annotation_text=f"бүх шидэлтийн дундаж {league_pps:.2f}", annotation_position="top left")
    fig.add_vline(x=6.75, line_dash="dash", line_color=NEUTRAL, annotation_text="3 онооны шугам", annotation_position="top right")
    fig.update_yaxes(title="Оноо / шидэлт", row=1, col=1)
    fig.update_yaxes(title="Шидэлтийн тоо", row=2, col=1)
    fig.update_xaxes(title="Сагснаас зай (м)", row=2, col=1)
    return _layout(fig, "Сагснаас холдох тусам шидэлтийн үр ашиг", height=500)


def px_assisted(df: pd.DataFrame, show_ci: bool) -> go.Figure:
    fig = go.Figure()
    for imp in (False, True):
        d = df[df.is_import == imp]
        err = dict(type="data", symmetric=False, array=d.hi - d.est, arrayminus=d.est - d.lo, thickness=2,
                   color=IMPORT_COLORS[imp]) if show_ci else None
        fig.add_trace(go.Scatter(x=d.est, y=d.zone, mode="markers", name=f"{IMPORT_LABELS[imp]} тоглогч", error_x=err,
                                 marker=dict(color=IMPORT_COLORS[imp], size=12), customdata=d.n,
                                 hovertemplate="%{y}: оносон шидэлтийн %{x:.0%} нь дамжуулалтаас<br>%{customdata} оносон "
                                               "шидэлт<extra>" + IMPORT_LABELS[imp] + "</extra>"))
    fig.update_xaxes(title="Оносон шидэлтийн хэдэн хувь нь дамжуулалтаас гарсан", tickformat=".0%", range=[0, 1.05])
    fig.update_yaxes(autorange="reversed")
    return _layout(fig, "Оноо хэрхэн бүтдэг вэ: дамжуулалтаас уу, бие даан уу", height=400)


def px_off_def(df: pd.DataFrame, highlight: str | None = None) -> go.Figure:
    mx, my = df.ortg.mean(), df.drtg.mean()
    fig = go.Figure(go.Scatter(
        x=df.ortg, y=df.drtg, mode="markers+text", text=df.team, textposition="top center", showlegend=False,
        marker=dict(size=14 + 26 * df.win, color=df.win, colorscale="RdBu", cmin=0.1, cmax=0.9,
                    line=dict(color=["black" if t == highlight else "#475569" for t in df.team],
                              width=[3 if t == highlight else 1 for t in df.team]),
                    colorbar=dict(title=dict(text="Ялалтын<br>хувь", side="top"), tickformat=".0%", thickness=12, len=0.7)),
        customdata=np.c_[df.win, df.pace, df.ortg - df.drtg],
        hovertemplate="<b>%{text}</b><br>100 довтолгоонд авсан %{x:.1f}, алдсан %{y:.1f} (зөрүү %{customdata[2]:+.1f})<br>"
                      "Ялалт %{customdata[0]:.0%} · тоглолтод %{customdata[1]:.0f} довтолгоо<extra></extra>"))
    fig.add_vline(x=mx, line_dash="dash", line_color=NEUTRAL)
    fig.add_hline(y=my, line_dash="dash", line_color=NEUTRAL)
    fig.update_xaxes(title="Довтолгоо: 100 довтолгоонд авсан оноо (баруун тийш = сайн)")
    fig.update_yaxes(title="Хамгаалалт: алдсан оноо (дээшээ = сайн)", autorange="reversed")
    return _layout(fig, "Довтолгоо ба хамгаалалтаар багуудын байрлал", height=500)


def px_usage(df: pd.DataFrame, highlight_team: str | None = None) -> go.Figure:
    fig = go.Figure()
    for imp in (False, True):
        d = df[df.is_import.astype(bool) == imp]
        fig.add_trace(go.Scatter(
            x=d.usage, y=d.ts, mode="markers", name=f"{IMPORT_LABELS[imp]} тоглогч",
            marker=dict(color=IMPORT_COLORS[imp], size=(6 + d.minutes / 60).tolist(), opacity=0.75,
                        line=dict(color="black", width=[2 if t == highlight_team else 0 for t in d.team])),
            customdata=np.c_[d.name, d.team, d.ppg, d.minutes],
            hovertemplate="<b>%{customdata[0]}</b> (%{customdata[1]})<br>Ачаалал %{x:.0%} · оновч %{y:.0%}<br>"
                          "%{customdata[2]:.1f} оноо/тоглолт · %{customdata[3]:.0f} минут<extra></extra>"))
    if len(df):
        fig.add_vline(x=df.usage.median(), line_dash="dash", line_color=NEUTRAL)
        fig.add_hline(y=df.ts.median(), line_dash="dash", line_color=NEUTRAL)
    fig.update_xaxes(title="Довтолгооны ачаалал (талбай дээр байхдаа багийн довтолгооны хэдийг дуусгадаг)", tickformat=".0%")
    fig.update_yaxes(title="Шидэлтийн оновч", tickformat=".0%")
    return _layout(fig, "Их ачаалалтай тоглогч оновчтой байж чаддаг уу", height=480)


def px_stability(df: pd.DataFrame, show_ci: bool) -> go.Figure:
    d = df.sort_values("r")
    eff = d.stat.isin(["ts_pct", "tp_pct"])
    colors = [B_COLOR if e else A_COLOR for e in eff]
    err = dict(type="data", symmetric=False, array=d.hi - d.r, arrayminus=d.r - d.lo, thickness=2, color=NEUTRAL) if show_ci else None
    fig = go.Figure(go.Scatter(x=d.r, y=[f"{lab} ({n})" for lab, n in zip(d.label, d.n)], mode="markers", error_x=err,
                               marker=dict(color=colors, size=12), customdata=np.c_[d.lo, d.hi, d.n],
                               hovertemplate="%{y}<br>хамаарлын хүч %{x:.2f} (хүрээ %{customdata[0]:.2f}–%{customdata[1]:.2f})"
                                             "<extra></extra>"))
    fig.add_vline(x=0, line_color="black")
    fig.update_xaxes(title="Өмнөх ба энэ улирлын хамаарлын хүч (0 = холбоогүй, 1 = ижил)", range=[-0.5, 1.02])
    return _layout(fig, "Юу улирлаас улиралд хадгалагддаг вэ", height=400, showlegend=False)
