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
FONT = dict(family="Inter, 'Segoe UI', Arial, sans-serif", size=13, color="#334155")
INK, MUTED, GRID, AXIS = "#0F172A", "#64748B", "#EDF1F6", "#C3CEDC"
LABELS = {**CHART_LABELS, "EFF": "Үр ашгийн оноо (EFF)"}


def _layout(fig: go.Figure, title: str, height: int = 420, **kw) -> go.Figure:
    """Бүх графикийн нэгдсэн загвар: цагаан суурь, зөөлөн тор, тод гарчиг, нэг фонт, нэг hover загвар."""
    margin = kw.pop("margin", dict(l=10, r=44, t=58, b=10))
    fig.update_layout(title=dict(text=title, x=0.01, xanchor="left", y=0.97, yanchor="top",
                                 font=dict(size=15, color=INK, family=FONT["family"], weight=600)),
                      font=FONT, height=height, margin=margin, plot_bgcolor="white", paper_bgcolor="white",
                      # хэрэгслийн самбарыг баруун ирмэгт босоогоор: гарчиг, графикийн бичиг дээр гарахгүй
                      modebar=dict(orientation="v", bgcolor="rgba(255,255,255,0.85)", color="#94A3B8",
                                   activecolor="#1B3A6B"),
                      hovermode="closest",
                      hoverlabel=dict(bgcolor="white", bordercolor=AXIS, font=dict(family=FONT["family"], size=13, color=INK)),
                      legend=dict(orientation="h", y=-0.22, font=dict(size=12, color="#334155"), bgcolor="rgba(0,0,0,0)"),
                      **kw)
    fig.update_xaxes(showgrid=True, gridcolor=GRID, zeroline=False, showline=True, linecolor=AXIS, ticks="outside",
                     tickcolor=AXIS, ticklen=4, title_font=dict(size=13, color=MUTED), tickfont=dict(size=12, color=MUTED))
    fig.update_yaxes(showgrid=True, gridcolor=GRID, zeroline=False, showline=False,
                     title_font=dict(size=13, color=MUTED), tickfont=dict(size=12, color=MUTED))
    return fig


def add_team_logos(fig: go.Figure, xs, ys, logos: list[str | None], size_frac: float = 0.075, row=None, col=None) -> go.Figure:
    """Цэгийн байрлал дээр багийн логог (албан ёсны URL) зурна. Хэмжээ нь тэнхлэгийн хүрээний хувиар — сунахгүй."""
    xs, ys = np.asarray(xs, float), np.asarray(ys, float)
    if not len(xs):
        return fig
    sx = (np.nanmax(xs) - np.nanmin(xs) or 1) * size_frac
    sy = (np.nanmax(ys) - np.nanmin(ys) or 1) * size_frac * 1.6
    for x, y, url in zip(xs, ys, logos):
        if url:
            fig.add_layout_image(source=url, x=x, y=y, xref="x", yref="y", sizex=sx, sizey=sy, xanchor="center",
                                 yanchor="middle", sizing="contain", layer="above")
    return fig


def px_scatter(df: pd.DataFrame, x: str, y: str, color_by: str, highlight_team: str | None = None,
               selected: str | None = None) -> go.Figure:
    """selected = тоглогчийн картад нээлттэй тоглогчийн id: бусад цэгийн дээр том од тэмдэг, нэрийн шошготой зурна."""
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
    me = df[df.player_id == selected].dropna(subset=[x, y]).head(1)
    if len(me):
        r = me.iloc[0]
        fig.add_trace(go.Scatter(
            x=[r[x]], y=[r[y]], mode="markers", name=f"Картын тоглогч: {r.player_name}",
            customdata=me[["player_id", "player_name", "team"]],
            marker=dict(symbol="star", size=22, color="#FACC15", line=dict(width=2, color="#0F172A")),
            hovertemplate="<b>%{customdata[1]}</b> (картад нээлттэй)<br>%{customdata[2]}<br>" + f"{LABELS.get(x, x)}: "
                          + "%{x:.2f}<br>" + f"{LABELS.get(y, y)}: " + "%{y:.2f}<extra></extra>"))
        fig.add_annotation(x=r[x], y=r[y], text=f"<b>{r.player_name}</b>", showarrow=True, arrowhead=0, ax=0, ay=-30,
                           font=dict(size=13, color="#0F172A"), bgcolor="rgba(255,255,255,0.9)", bordercolor="#0F172A",
                           borderwidth=1, borderpad=3)
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
                             name="Нийлбэр хувь", customdata=df.player_name,
                             hovertemplate="Хамгийн их оноотой %{x} тоглогч нийлээд онооны <b>%{y:.0%}</b>-ийг авсан"
                                           "<br>(%{x}-р байрт: %{customdata})<extra></extra>"),
                  secondary_y=True)
    k = int(np.argmax(df.cum_share.to_numpy() >= 0.8)) + 1
    fig.add_hline(y=0.8, line_dash="dash", line_color=B_COLOR, secondary_y=True)
    fig.add_annotation(x=k, y=0.8, yref="y2", text=f"Хамгийн их оноотой {k} тоглогч<br>({k / len(df):.0%}) = онооны 80%",
                       showarrow=True, font=dict(color=B_COLOR), ax=60, ay=40, bgcolor="rgba(255,255,255,0.9)")
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
    fig = make_subplots(rows=1, cols=4, subplot_titles=[f"{l}<br>({'их' if hb else 'бага'} нь сайн)" for _, l, hb in FACTORS],
                        shared_yaxes=True)
    order = (means["efg"] - league["efg"]).sort_values().index
    for i, (f, lbl, hb) in enumerate(FACTORS, 1):
        dev = (means[f] - league[f]).reindex(order) * 100
        good = dev > 0 if hb else dev < 0
        colors = [("black" if t == highlight else (A_COLOR if g else B_COLOR)) for t, g in zip(dev.index, good)]
        fig.add_trace(go.Bar(x=dev, y=dev.index, orientation="h", marker_color=colors, showlegend=False,
                             hovertemplate="%{y}: дунджаас %{x:+.1f}<extra>" + lbl + "</extra>"), row=1, col=i)
        fig.update_xaxes(title="Дунджаас зөрүү", row=1, col=i)
    fig.update_annotations(font=dict(size=13))
    return _layout(fig, "Ялалтын 4 хүчин зүйл: баг бүр лигийн дунджаас хэр сайн/сул вэ", height=500,
                   margin=dict(l=10, r=44, t=95, b=10))


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
                  annotation_text=f"дундаж {league_pps:.2f}", annotation_position="bottom right",
                  annotation_font=dict(size=11, color="#475569"))
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


def lead_change_index(margin: np.ndarray) -> np.ndarray:
    """Тэргүүлэгч баг солигдсон мөрүүдийн индекс (тэнцүү оноог алгасаж, өмнөх тэргүүлэгчтэй харьцуулна)."""
    nz = np.flatnonzero(margin != 0)
    sign = np.sign(margin[nz])
    return nz[1:][sign[1:] != sign[:-1]]


def _period_name(p: int) -> str:
    return f"{p}-р үе" if p <= 4 else f"нэмэлт цаг {p - 4}"


def px_game_flow(flow: pd.DataFrame, wp: np.ndarray, home: str, away: str, show_ci_line: bool = True) -> go.Figure:
    t = flow.elapsed / 60
    m = flow.margin.to_numpy()
    clock = [f"{int(e // 60)}:{int(e % 60):02d}" for e in flow.elapsed]
    lead = [f"<b>{home}</b> {v} оноогоор тэргүүлж байна" if v > 0 else
            (f"<b>{away}</b> {-v} оноогоор тэргүүлж байна" if v < 0 else "Тэнцүү") for v in m]
    period = [_period_name(int(p)) for p in flow.period]
    fig = make_subplots(rows=2, cols=1, shared_xaxes=True, row_heights=[0.55, 0.45], vertical_spacing=0.1)
    pos, neg = flow.margin.clip(lower=0), flow.margin.clip(upper=0)
    fig.add_trace(go.Scatter(x=t, y=pos, line=dict(shape="hv", width=0), fill="tozeroy", fillcolor="rgba(213,94,0,0.75)",
                             name=f"{home} (гэрийн баг) тэргүүлсэн", hoverinfo="skip"), row=1, col=1)
    fig.add_trace(go.Scatter(x=t, y=neg, line=dict(shape="hv", width=0), fill="tozeroy", fillcolor="rgba(0,114,178,0.75)",
                             name=f"{away} (зочин баг) тэргүүлсэн", hoverinfo="skip"), row=1, col=1)
    fig.add_trace(go.Scatter(x=t, y=flow.margin, mode="lines", line=dict(shape="hv", color="rgba(0,0,0,0)"),
                             showlegend=False, customdata=np.c_[flow.home, flow.away, lead, clock, period],
                             hovertemplate="<b>%{customdata[3]}</b> (%{customdata[4]})<br>"
                                           + f"{home}: " + "%{customdata[0]} оноо · " + f"{away}: " + "%{customdata[1]} оноо"
                                           "<br>%{customdata[2]}<extra></extra>"), row=1, col=1)
    lc = lead_change_index(m)
    if len(lc):
        who = [home if m[i] > 0 else away for i in lc]
        fig.add_trace(go.Scatter(x=t.iloc[lc], y=np.zeros(len(lc)), mode="markers", name="Тэргүүлэгч солигдсон мөч",
                                 marker=dict(symbol="diamond", size=8, color="#0F172A", line=dict(width=1, color="white")),
                                 customdata=np.c_[who, np.array(clock)[lc], flow.home.iloc[lc], flow.away.iloc[lc]],
                                 hovertemplate="<b>%{customdata[1]}</b>: тэргүүлэгч солигдов —<br><b>%{customdata[0]}</b> "
                                               "түрүүллээ (" + home + " %{customdata[2]} – %{customdata[3]} " + away + ")"
                                               "<extra></extra>"), row=1, col=1)
    fig.add_trace(go.Scatter(x=t, y=wp, mode="lines", line=dict(shape="hv", color="black", width=2),
                             name=f"{home} ялах магадлал", customdata=np.c_[1 - np.asarray(wp, float), clock],
                             hovertemplate="<b>%{customdata[1]}</b><br>" + f"{home} ялах магадлал: " + "%{y:.0%}<br>"
                                           + f"{away} ялах магадлал: " + "%{customdata[0]:.0%}<extra></extra>"),
                  row=2, col=1)
    fig.add_hline(y=0.5, line_dash="dot", line_color=NEUTRAL, row=2, col=1)
    end = float(t.max())
    for q in [10, 20, 30] + ([40] if end > 40 else []):
        fig.add_vline(x=q, line_color="#E2E8F0")
    for i, (a, b) in enumerate([(0, 10), (10, 20), (20, 30), (30, 40)] + ([(40, end)] if end > 40 else [])):
        fig.add_annotation(x=(a + b) / 2, y=1.0, xref="x", yref="y domain", yanchor="bottom", showarrow=False,
                           text=_period_name(i + 1) if i < 4 else "нэмэлт цаг", font=dict(size=11, color="#64748B"))
    fig.update_yaxes(title="Онооны зөрүү", row=1, col=1)
    fig.update_yaxes(title="Ялах магадлал", tickformat=".0%", range=[0, 1], row=2, col=1)
    fig.update_xaxes(title="Тоглолтын минут", row=2, col=1)
    final = f"{int(flow.home.iloc[-1])}–{int(flow.away.iloc[-1])}"
    return _layout(fig, f"{home} {final} {away}: оноо минут тутам", height=540)


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


def px_off_def(df: pd.DataFrame, highlight: str | None = None, logos: dict | None = None) -> go.Figure:
    """Тойрог бүр 1 баг: хүрээний өнгө = ялалтын хувь, дотор нь багийн лого (логогүй бол өнгөт тойрог)."""
    mx, my = df.ortg.mean(), df.drtg.mean()
    logos = logos or {}
    urls = [logos.get(t) for t in df.team]
    fig = go.Figure(go.Scatter(
        x=df.ortg, y=df.drtg, mode="markers+text", text=df.team, textposition="bottom center", showlegend=False,
        textfont=dict(size=11, color="#334155"),
        marker=dict(size=44 if any(urls) else 14 + 26 * df.win, color=df.win, colorscale="RdBu", cmin=0.1, cmax=0.9,
                    line=dict(color=["#0F172A" if t == highlight else "white" for t in df.team],
                              width=[4 if t == highlight else 2 for t in df.team]),
                    colorbar=dict(title=dict(text="Ялалт", side="top"), tickformat=".0%", thickness=10, len=0.6, x=1.0)),
        customdata=np.c_[df.win, df.pace, df.ortg - df.drtg],
        hovertemplate="<b>%{text}</b><br>100 довтолгоонд авсан %{x:.1f}, алдсан %{y:.1f} (зөрүү %{customdata[2]:+.1f})<br>"
                      "Ялалт %{customdata[0]:.0%} · тоглолтод %{customdata[1]:.0f} довтолгоо<extra></extra>"))
    add_team_logos(fig, df.ortg, df.drtg, urls, size_frac=0.07)  # өнгөт тойргийн дотор лого: өнгө = ялалтын хувь
    fig.add_vline(x=mx, line_dash="dash", line_color=NEUTRAL)
    fig.add_hline(y=my, line_dash="dash", line_color=NEUTRAL)
    pad_x = (df.ortg.max() - df.ortg.min()) * 0.12 or 1
    pad_y = (df.drtg.max() - df.drtg.min()) * 0.15 or 1
    fig.update_xaxes(title="Довтолгоо: 100 довтолгоонд авсан оноо (баруун тийш = сайн)",
                     range=[df.ortg.min() - pad_x, df.ortg.max() + pad_x])
    fig.update_yaxes(title="Хамгаалалт: алдсан оноо (дээшээ = сайн)", range=[df.drtg.max() + pad_y, df.drtg.min() - pad_y])
    return _layout(fig, "Довтолгоо ба хамгаалалтаар багуудын байрлал", height=520)


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
    fig.update_xaxes(title="Хоёр улирлын хамаарал (0 = холбоогүй, 1 = бүрэн давтагдана)", range=[-0.5, 1.02])
    return _layout(fig, "Аль үзүүлэлт дараа улиралд давтагддаг вэ", height=420, showlegend=False)


PCT_STATS = {"ts_pct", "tp_pct", "tpa_rate"}


def px_stability_pairs(d: pd.DataFrame, stat: str, label: str, r: float, highlight_team: str | None = None) -> go.Figure:
    """Тоглогч бүрийн өмнөх улирлын (x) ба энэ улирлын (y) утга; тасархай шугам = яг ижил үлдсэн."""
    fmt = ".0%" if stat in PCT_STATS else ".1f"
    lo, hi = float(min(d.prev.min(), d.now.min())), float(max(d.prev.max(), d.now.max()))
    pad = (hi - lo) * 0.05
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=[lo - pad, hi + pad], y=[lo - pad, hi + pad], mode="lines", hoverinfo="skip",
                             line=dict(color=NEUTRAL, dash="dash"), name="Хоёр улиралд яг ижил"))
    line = [2 if t == highlight_team else 0 for t in d.team]
    prev_s, now_s = d.prev_season.iloc[0].replace("-20", "–"), d.season.iloc[0].replace("-20", "–")
    fig.add_trace(go.Scatter(x=d.prev, y=d.now, mode="markers", name="Тоглогч",
                             marker=dict(color=B_COLOR if stat in {"ts_pct", "tp_pct"} else A_COLOR, size=10, opacity=0.8,
                                         line=dict(width=line, color="black")),
                             customdata=np.c_[d.player_name, d.team],
                             hovertemplate="<b>%{customdata[0]}</b> (%{customdata[1]})<br>" + f"{prev_s}: " + "%{x:" + fmt
                                           + "}<br>" + f"{now_s}: " + "%{y:" + fmt + "}<extra></extra>"))
    fig.update_xaxes(title=f"{label}, {prev_s}", tickformat=fmt, range=[lo - pad, hi + pad])
    fig.update_yaxes(title=f"{label}, {now_s}", tickformat=fmt, range=[lo - pad, hi + pad])
    return _layout(fig, f"{label}: хамаарал {r:.2f} ({len(d)} тоглогч)", height=420, showlegend=False)


# ---------- Гадаад тоглогч ба солилцоо ----------
VERDICT_HEX = {"Батлагдсан": PALETTE["green"], "Няцаагдсан": PALETTE["vermillion"], "Баттай биш": NEUTRAL}
LEVEL_ORDER = ["NBA", "EuroLeague / EuroCup", "G League", "Бусад мэргэжлийн лиг", "Мэргэжлийн туршлагагүй", "Тодорхойгүй"]
LEVEL_HEX = dict(zip(LEVEL_ORDER, ["#08306B", A_COLOR, "#56B4E9", "#9ECAE1", "#BDBDBD", "#F0F0F0"]))


def px_import_hypotheses(h: pd.DataFrame, show_ci: bool) -> go.Figure:
    fig = make_subplots(rows=len(h), cols=1, vertical_spacing=0.11,
                        subplot_titles=[f"{r.hid}: {r.statement} — <b>{r.verdict}</b>" for r in h.itertuples()])
    for k, r in enumerate(h.itertuples(), 1):
        color = VERDICT_HEX[r.verdict]
        pct = r.hid == "H8"
        if show_ci:
            fig.add_trace(go.Scatter(x=[r.lo, r.hi], y=[0, 0], mode="lines", line=dict(color=color, width=8),
                                     opacity=0.45, hoverinfo="skip", showlegend=False), row=k, col=1)
        fmt = ".0%" if pct else ".2f"
        fig.add_trace(go.Scatter(x=[r.estimate], y=[0], mode="markers", marker=dict(color=color, size=13), showlegend=False,
                                 hovertemplate=f"{r.measure}<br>утга %{{x:{fmt}}}<br>хүрээ {r.lo:{fmt}} … {r.hi:{fmt}}<br>"
                                               f"{r.n}<extra>{r.hid}</extra>"), row=k, col=1)
        span = max(abs(r.lo), abs(r.hi)) * 1.25
        fig.add_vline(x=0, line_dash="dash", line_color="black", row=k, col=1)
        fig.update_xaxes(range=[-span, span], tickformat="+.0%" if pct else None, row=k, col=1)
        fig.update_yaxes(visible=False, row=k, col=1)
    fig.update_annotations(font=dict(size=13), x=0, xanchor="left")
    return _layout(fig, "", height=110 * len(h) + 50, margin=dict(l=10, r=44, t=40, b=10))


def px_import_pipeline(bg: pd.DataFrame) -> go.Figure:
    f = bg[bg.status == "олдсон"]
    lv = f.level.value_counts().reindex(LEVEL_ORDER[:-1], fill_value=0)
    from src.charts.imports import LEAGUE_MN

    last = f.last_league.dropna().map(lambda x: LEAGUE_MN.get(x, x)).value_counts().head(8)
    fig = make_subplots(rows=1, cols=2, horizontal_spacing=0.22,
                        subplot_titles=["Өмнө тоглосон хамгийн өндөр түвшин", "Ирэхийн өмнөх сүүлийн лиг"])
    fig.add_trace(go.Bar(x=lv.to_numpy(), y=lv.index, orientation="h", marker_color=[LEVEL_HEX[l] for l in lv.index],
                         text=lv.to_numpy(), textposition="outside", showlegend=False,
                         hovertemplate="%{y}: %{x} тоглогч<extra></extra>"), row=1, col=1)
    fig.add_trace(go.Bar(x=last.to_numpy(), y=last.index, orientation="h",
                         marker_color=[B_COLOR] + [NEUTRAL] * (len(last) - 1), text=last.to_numpy(), textposition="outside",
                         showlegend=False, hovertemplate="%{y}: %{x} тоглогч<extra></extra>"), row=1, col=2)
    fig.update_yaxes(autorange="reversed")
    fig.update_xaxes(title="Тоглогчийн тоо", range=[0, lv.max() * 1.18], row=1, col=1)
    fig.update_xaxes(title="Тоглогчийн тоо", range=[0, last.max() * 1.18], row=1, col=2)
    fig.update_traces(cliponaxis=False)
    return _layout(fig, "", height=400, margin=dict(l=10, r=44, t=40, b=10))


def px_import_retention(cmp: pd.DataFrame, show_ci: bool) -> go.Figure:
    """Үзүүлэлт бүр нэг мөр (нарийн баганад ч уншигдана); мөр бүрт өөрийн тэнхлэг, дүгнэлт гарчигт нь."""
    titles = [f"{r.label} — {'баттай ялгаатай' if r.clear else 'ялгаа баттай биш'}" for r in cmp.itertuples()]
    fig = make_subplots(rows=len(cmp), cols=1, subplot_titles=titles, vertical_spacing=0.14)
    for k, r in enumerate(cmp.itertuples(), 1):
        pct = r.metric in ("usage", "ts_pct")
        fmt = ".0%" if pct else ".1f"
        for name, med, lo, hi, color in (("Явсан", r.med_no, r.lo_no, r.hi_no, NEUTRAL),
                                         ("Үлдсэн", r.med_yes, r.lo_yes, r.hi_yes, B_COLOR)):
            err = dict(type="data", symmetric=False, array=[hi - med], arrayminus=[med - lo], thickness=3,
                       color=color) if show_ci else None
            fig.add_trace(go.Scatter(x=[med], y=[f"{name}: {format(med, fmt)}"], mode="markers",
                                     marker=dict(color=color, size=12), error_x=err, showlegend=False,
                                     hovertemplate=f"{name}: голч %{{x:{fmt}}} (хүрээ {lo:{fmt}}–{hi:{fmt}})"
                                                   f"<extra>{r.label}</extra>"), row=k, col=1)
        fig.update_xaxes(tickformat=".0%" if pct else None, nticks=6, row=k, col=1)
        fig.update_yaxes(range=[-0.6, 1.6], row=k, col=1)
    fig.update_annotations(font=dict(size=13), x=0, xanchor="left")
    return _layout(fig, "", height=100 * len(cmp) + 40, margin=dict(l=10, r=44, t=30, b=10))


def px_import_position(pm: pd.DataFrame, conc: pd.DataFrame) -> go.Figure:
    order = ["PG", "SG", "SF", "PF", "C"]
    names = {"PG": "Тоглуулагч<br>хамгаалагч (PG)", "SG": "Шидэгч<br>хамгаалагч (SG)", "SF": "Жижиг<br>довтлогч (SF)",
             "PF": "Хүчит<br>довтлогч (PF)", "C": "Төвийн<br>тоглогч (C)"}
    fig = go.Figure()
    colors = ["#FDCC8A", B_COLOR]
    for k, season in enumerate(sorted(pm.season.unique())):
        d = pm[pm.season == season].set_index("position").reindex(order)
        lab = season.replace("-20", "–")
        fig.add_trace(go.Bar(x=[names[p] for p in order], y=d.share, name=lab, marker_color=colors[k],
                             text=[f"{v:.0%}" for v in d.share], textposition="outside",
                             hovertemplate="%{x}: минутын %{y:.0%} нь гадаад<extra>" + lab + "</extra>"))
        ov = conc.set_index("season").loc[season, "overall_share"]
        # дундаж шугамыг тайлбар (legend) дотор нэрлэнэ — графикийн дотор бичиг давхцахгүй
        fig.add_trace(go.Scatter(x=[names[order[0]], names[order[-1]]], y=[ov, ov], mode="lines",
                                 line=dict(color=colors[k], dash="dash", width=2), name=f"{lab}: бүх байрлалын дундаж {ov:.0%}",
                                 hoverinfo="skip"))
    fig.update_yaxes(title="Минутын гадаад хувь", tickformat=".0%", range=[0, 0.8])
    fig.update_xaxes(tickangle=0)
    return _layout(fig, "", height=440, barmode="group", margin=dict(l=10, r=44, t=30, b=10))


def px_import_age(im: pd.DataFrame) -> go.Figure:
    d = im.dropna(subset=["age", "PPG"])
    fig = go.Figure()
    for lvl in LEVEL_ORDER:
        part = d[d.level == lvl]
        if part.empty:
            continue
        fig.add_trace(go.Scatter(x=part.age, y=part.PPG, mode="markers", name=f"{lvl} ({len(part)})",
                                 marker=dict(color=LEVEL_HEX[lvl], size=(8 + part.MIN / 3).tolist(),
                                             line=dict(color="#475569", width=1)),
                                 customdata=np.c_[part.player_name, part.team, part.season, part.last_league.fillna("—")],
                                 hovertemplate="<b>%{customdata[0]}</b> (%{customdata[1]}, %{customdata[2]})<br>нас %{x:.0f} · "
                                               "%{y:.1f} оноо<br>өмнөх лиг: %{customdata[3]}<extra></extra>"))
    slope, icpt = np.polyfit(d.age, d.PPG, 1)
    xs = np.array([d.age.min(), d.age.max()])
    fig.add_trace(go.Scatter(x=xs, y=icpt + slope * xs, mode="lines", line=dict(color="black"), name="Чиг хандлага",
                             hoverinfo="skip"))
    fig.update_xaxes(title="Нас (тухайн улирал эхлэхэд)")
    fig.update_yaxes(title="Оноо / тоглолт (MBA)")
    return _layout(fig, "Нас ба MBA дахь оноо (өнгө = өмнөх хамгийн өндөр түвшин)", height=460)
