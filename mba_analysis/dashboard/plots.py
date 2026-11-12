import json
from pathlib import Path

import numpy as np
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots

from src.palette import IMPORT_COLORS, IMPORT_LABELS, NEUTRAL, PALETTE, POS_COLORS, cluster_colors
from src.uncertainty import funnel_limits

A_COLOR, B_COLOR = PALETTE["blue"], PALETTE["vermillion"]
LIGHTEST = "#D0D0D0"
FONT = dict(family="Arial, DejaVu Sans, sans-serif", size=12)
LABELS = {"PPG": "Оноо / тоглолт", "RPG": "Самбар / тоглолт", "APG": "Дамжуулалт / тоглолт",
          "SPG": "Таслалт / тоглолт", "BPG": "Хаалт / тоглолт", "MIN": "Минут / тоглолт", "ts_pct": "TS%",
          "height_cm": "Өндөр (см)", "age": "Нас", "pts36": "Оноо / 36 мин", "reb36": "Самбар / 36 мин",
          "ast36": "Дамжуулалт / 36 мин", "tpa_rate": "3 онооны шидэлтийн хувь", "EFF": "EFF"}


def _layout(fig: go.Figure, title: str, height: int = 420, **kw) -> go.Figure:
    fig.update_layout(title=dict(text=title, x=0, font=dict(size=15)), font=FONT, height=height,
                      margin=dict(l=10, r=10, t=55, b=10), plot_bgcolor="white", hovermode="closest",
                      legend=dict(orientation="h", y=-0.2), **kw)
    fig.update_xaxes(showgrid=True, gridcolor="#EBEBEB", zeroline=False)
    fig.update_yaxes(showgrid=True, gridcolor="#EBEBEB", zeroline=False)
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
    return _layout(fig, f"{LABELS.get(y, y)} ба {LABELS.get(x, x)}", dragmode="select")


def px_funnel(players: pd.DataFrame, show_ci: bool) -> go.Figure:
    df = players.assign(tsa=players.FGA.fillna(0) + 0.44 * players.FTA.fillna(0))
    df = df[(df.tsa > 0) & df.ts_pct.notna()]
    p0 = df.PTS_total.sum() / (2 * df.tsa.sum())
    fig = go.Figure()
    grid = np.linspace(max(df.tsa.min(), 1), df.tsa.max(), 150)
    if show_ci:
        for z, name, alpha in ((3.09, "99.8% CI хил", 0.12), (1.96, "95% CI хил", 0.22)):
            lo, hi = funnel_limits(p0, grid, z)
            fig.add_trace(go.Scatter(x=np.r_[grid, grid[::-1]], y=np.r_[hi, lo[::-1]], fill="toself", name=name,
                                     fillcolor=f"rgba(86,180,233,{alpha})", line=dict(width=0), hoverinfo="skip"))
    lo95, hi95 = funnel_limits(p0, df.tsa.to_numpy(), 1.96)
    colors = np.where(df.ts_pct > hi95, PALETTE["green"], np.where(df.ts_pct < lo95, PALETTE["vermillion"], NEUTRAL))
    fig.add_trace(go.Scattergl(x=df.tsa, y=df.ts_pct, mode="markers", name="Тоглогч", marker=dict(color=colors, size=8),
                               customdata=df[["player_name", "team"]],
                               hovertemplate="<b>%{customdata[0]}</b> (%{customdata[1]})<br>TS% %{y:.1%}<br>"
                                             "Оролдлого %{x:.0f}<extra></extra>"))
    fig.add_hline(y=p0, line_color="black", annotation_text=f"Лигийн TS% {p0:.1%}")
    fig.update_xaxes(title="Шидэлтийн оролдлого (FGA + 0.44·FTA)")
    fig.update_yaxes(title="TS%", tickformat=".0%")
    above = int((df.ts_pct > hi95).sum())
    return _layout(fig, f"Funnel: {above} тоглогчийн оновч лигийн дунджаас баттай өндөр")


def px_dot_ci(ci: pd.DataFrame, show_ci: bool, metric_label: str) -> go.Figure:
    df = ci.sort_values("est")
    colors = df.is_import.astype(bool).map(IMPORT_COLORS) if "is_import" in df else A_COLOR
    err = dict(type="data", symmetric=False, array=df.hi - df.est, arrayminus=df.est - df.lo, color=NEUTRAL,
               thickness=2) if show_ci else None
    fig = go.Figure(go.Scatter(x=df.est, y=df.player_name, mode="markers", error_x=err,
                               name="95% CI" if show_ci else "Тооцоолсон утга", marker=dict(color=colors, size=10),
                               hovertemplate="<b>%{y}</b><br>%{x:.2f}<extra></extra>"))
    fig.update_xaxes(title=metric_label)
    return _layout(fig, f"Топ {len(df)}: {metric_label}" + (" (цэг + 95% CI)" if show_ci else ""),
                   height=max(320, 26 * len(df) + 120), showlegend=False)


def px_pareto(df: pd.DataFrame, show_ci: bool, title: str) -> go.Figure:
    fig = make_subplots(specs=[[{"secondary_y": True}]])
    fig.add_trace(go.Bar(x=df["rank"], y=df.value, marker_color=df.is_import.astype(bool).map(IMPORT_COLORS)
                         if "is_import" in df else A_COLOR, name="Оноо", customdata=df.player_name,
                         hovertemplate="#%{x} %{customdata}: %{y:.0f} оноо<extra></extra>"), secondary_y=False)
    if show_ci and "lo" in df:
        fig.add_trace(go.Scatter(x=np.r_[df["rank"], df["rank"][::-1]], y=np.r_[df.hi, df.lo[::-1]], fill="toself",
                                 fillcolor="rgba(0,0,0,0.15)", line=dict(width=0), name="95% CI (хуримтлагдсан)",
                                 hoverinfo="skip"), secondary_y=True)
    fig.add_trace(go.Scatter(x=df["rank"], y=df.cum_share, mode="lines", line=dict(color="black"),
                             name="Хуримтлагдсан хувь", hovertemplate="Топ %{x}: %{y:.0%}<extra></extra>"),
                  secondary_y=True)
    k = int(np.argmax(df.cum_share.to_numpy() >= 0.8)) + 1
    fig.add_hline(y=0.8, line_dash="dash", line_color=B_COLOR, secondary_y=True)
    fig.add_annotation(x=k, y=0.8, yref="y2", text=f"Топ {k} ({k / len(df):.0%}) = 80%", showarrow=True,
                       font=dict(color=B_COLOR))
    fig.update_yaxes(title="Оноо", rangemode="tozero", secondary_y=False)
    fig.update_yaxes(title="Хуримтлагдсан хувь", tickformat=".0%", range=[0, 1.02], secondary_y=True, showgrid=False)
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
                                     name=f"{lvl}% CI", hoverinfo="skip"))
    fig.add_trace(go.Scatter(x=t.date, y=t.winpct, mode="lines+markers", line=dict(color=B_COLOR, width=3),
                             name=t.team.iloc[0], customdata=np.c_[t.wins, t.games],
                             hovertemplate="%{y:.0%} (%{customdata[0]}/%{customdata[1]})<extra></extra>"))
    fig.add_hline(y=0.5, line_dash="dot", line_color="black")
    fig.update_yaxes(title="Хуримтлагдсан ялалтын хувь", tickformat=".0%", range=[0, 1])
    fig.update_xaxes(title="Огноо")
    return _layout(fig, f"{t.team.iloc[0]}: ялалтын хувь улирлын турш" + (" (Wilson CI)" if show_ci else ""))



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
                                   hovertemplate="<b>%{customdata[0]}</b><br>Тогтвортой байдал %{customdata[1]:.0%}"
                                                 "<extra>" + name + "</extra>"))
    if selected is not None:
        s = clusters[clusters.player_id == selected]
        fig.add_trace(go.Scatter(x=s.pc1, y=s.pc2, mode="markers", name="Сонгосон",
                                 marker=dict(symbol="star", size=20, color="black")))
    fig.update_xaxes(title="Гол бүрэлдэхүүн 1")
    fig.update_yaxes(title="Гол бүрэлдэхүүн 2")
    return _layout(fig, "Тоглогчийн архетип (тод = тогтвортой, цайвар = бүлгийн заагт)")


FACTORS = [("efg", "eFG%", True), ("tov_pct", "TOV%", False), ("orb_pct", "ORB%", True), ("ftr", "FTr", True)]


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
                             hovertemplate="%{y}: %{x:+.1f} нэгж %<extra>" + lbl + "</extra>"), row=1, col=i)
        fig.update_xaxes(title="Дунджаас, нэгж %", row=1, col=i)
    return _layout(fig, "Four Factors: лигийн дунджаас хазайлт (цэнхэр = давуу, улаан = сул)", height=460)


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
    fig.update_yaxes(title="Elo үнэлгээ")
    fig.update_xaxes(title="Огноо")
    return _layout(fig, "Elo үнэлгээний явц" + (f" — {highlight}" if highlight else ""))


def px_map(meta: pd.DataFrame, standings: pd.DataFrame, geojson_path: Path, season: str) -> go.Figure:
    geo = json.loads(Path(geojson_path).read_text(encoding="utf-8"))
    names = [f["properties"]["shapeName"] for f in geo["features"]]
    st = standings[standings.season == season].assign(winpct=lambda d: d.W / (d.W + d.L)).merge(meta, on="team_key")
    known = st[st.lat.notna()]
    fig = go.Figure(go.Choropleth(geojson=geo, locations=names, z=[0] * len(names), featureidkey="properties.shapeName",
                                  colorscale=[[0, "#E3E3E3"], [1, "#E3E3E3"]], showscale=False,
                                  marker_line_color="#A6A6A6", hoverinfo="skip"))
    for region, color in (("Улаанбаатар", B_COLOR), ("Орон нутаг", A_COLOR)):
        part = known[known.region == region]
        fig.add_trace(go.Scattergeo(lon=part.lon, lat=part.lat, mode="markers", name=region,
                                    marker=dict(size=10 + 40 * part.winpct, color=color, opacity=0.75),
                                    text=part.canonical_name + " — " + (part.winpct * 100).round(0).astype(str) + "%",
                                    hovertemplate="%{text}<extra></extra>"))
    fig.update_geos(fitbounds="locations", visible=False)
    unknown = len(st) - len(known)
    return _layout(fig, f"Багийн гэр хот ба ялалтын хувь ({unknown} багийн хот тодорхойгүй)", height=380)
