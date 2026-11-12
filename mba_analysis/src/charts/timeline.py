import matplotlib.dates as mdates
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from src.style import NEUTRAL, PALETTE, apply_style, finish, source_mba
from src.uncertainty import wilson_ci

HIGHLIGHT_COLORS = [PALETTE["vermillion"], PALETTE["blue"], PALETTE["green"]]
BANDS = ((0.95, 0.12), (0.80, 0.22), (0.50, 0.35))


def _team_names(df: pd.DataFrame) -> dict:
    return dict(zip(df.team_key, df.team)) if "team" in df.columns else {}


def _spread_labels(ends: dict, gap: float = 0.05) -> dict:
    """Шугамын төгсгөлийн шошгыг босоо тэнхлэгийн дагуу давхцахгүй зайтай байрлуулна."""
    ordered = sorted(ends.items(), key=lambda kv: kv[1][1])
    out, last = {}, -np.inf
    for key, (x, y, color) in ordered:
        y = max(y, last + gap)
        out[key] = (x, y, color)
        last = y
    return out


def cumulative_winpct(team_games: pd.DataFrame, season: str) -> pd.DataFrame:
    tg = team_games[(team_games.season == season) & (team_games.phase == "regular")].copy()
    tg["date"] = pd.to_datetime(tg.date)
    tg = tg.sort_values(["team_key", "date", "game_id"])
    tg["wins"] = tg.groupby("team_key").win.cumsum()
    tg["games"] = tg.groupby("team_key").cumcount() + 1
    tg["winpct"] = tg.wins / tg.games
    return tg


def fig_cum_winpct(team_games: pd.DataFrame, highlight: list[str], bands: bool = True, season: str = "2025-2026"):
    apply_style()
    tg = cumulative_winpct(team_games, season)
    names = _team_names(team_games)
    fig, ax = plt.subplots(figsize=(6.3, 4))
    for key, part in tg.groupby("team_key"):
        if key not in highlight:
            ax.plot(part.date, part.winpct, color=NEUTRAL, linewidth=0.8, alpha=0.6)
    ends = {}
    for i, (color, key) in enumerate(zip(HIGHLIGHT_COLORS, highlight)):
        part = tg[tg.team_key == key]
        if bands and i == 0:
            for level, alpha in BANDS:
                cis = [wilson_ci(int(w), int(n), alpha=1 - level) for w, n in zip(part.wins, part.games)]
                ax.fill_between(part.date, [c.lo for c in cis], [c.hi for c in cis], color=color, alpha=alpha,
                                linewidth=0)
        ax.plot(part.date, part.winpct, color=color, linewidth=2)
        ends[key] = (part.date.iloc[-1], part.winpct.iloc[-1], color)
    for key, (x, y, color) in _spread_labels(ends).items():
        ax.text(x, y, f" {names.get(key, key)}", color=color, fontsize=8, fontweight="bold", va="center")
    ax.axhline(0.5, color="black", linewidth=0.6, linestyle=":")
    ax.set_ylim(0, 1)
    ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda v, _: f"{v:.0%}"))
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%Y-%m"))
    ax.set_xlabel("Огноо")
    ax.set_ylabel("Хуримтлагдсан ялалтын хувь")
    final = tg.groupby("team_key").last()
    leader = final.winpct.idxmax()
    return finish(fig, f"{names.get(leader, leader)} улирлыг {final.loc[leader, 'winpct']:.0%} ялалтаар тэргүүлж дуусгасан",
                  f"{season.replace('-20', '–')} энгийн улирал; саарал = бусад баг"
                  + (f"; зурвас = {names.get(highlight[0], highlight[0])}-ийн 50/80/95% итгэх интервал" if bands else ""),
                  source_mba(), n=int(tg.team_key.nunique()),
                  uncertainty_note="Итгэх интервал: Wilson, хуримтлагдсан ялалт/тоглолтоор" if bands else None)


def elo_series(games: pd.DataFrame) -> pd.DataFrame:
    g = games.copy()
    g["date"] = pd.to_datetime(g.date)
    rows = pd.concat([
        g[["date", "game_id", "season", "home_team_key", "elo_post_home"]].set_axis(["date", "game_id", "season", "team_key", "elo"], axis=1),
        g[["date", "game_id", "season", "away_team_key", "elo_post_away"]].set_axis(["date", "game_id", "season", "team_key", "elo"], axis=1),
    ])
    return rows.sort_values(["team_key", "date", "game_id"])


def fig_elo(games: pd.DataFrame, highlight: list[str]):
    apply_style()
    s = elo_series(games)
    names = dict(zip(games.home_team_key, games.home_team)) if "home_team" in games.columns else {}
    fig, ax = plt.subplots(figsize=(6.3, 4))
    for (key, season), part in s.groupby(["team_key", "season"]):
        if key not in highlight:
            ax.plot(part.date, part.elo, color=NEUTRAL, linewidth=0.7, alpha=0.5)
    for color, key in zip(HIGHLIGHT_COLORS, highlight):
        for season, part in s[s.team_key == key].groupby("season"):
            ax.plot(part.date, part.elo, color=color, linewidth=1.8)
        last = s[s.team_key == key].iloc[-1]
        ax.text(last.date, last.elo, f" {names.get(key, key)}", color=color, fontsize=8, fontweight="bold", va="center")
    boundary = s[s.season == "2026-2027"].date.min()
    if pd.notna(boundary):
        ax.axvline(boundary, color="black", linestyle="--", linewidth=0.8)
        ax.text(boundary, ax.get_ylim()[1], " 2026–27 (явцын)", va="top", fontsize=7.5)
    ax.axhline(1500, color="black", linewidth=0.6, linestyle=":")
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%Y-%m"))
    ax.set_xlabel("Огноо")
    ax.set_ylabel("Elo үнэлгээ")
    latest = s.groupby("team_key").last()
    top = latest.elo.idxmax()
    return finish(fig, f"{names.get(top, top)}-ийн Elo үнэлгээ одоогоор хамгийн өндөр ({latest.loc[top, 'elo']:.0f})",
                  "Elo: K = 20, эхлэл 1500, улирлын шилжилтэд 75% хадгална; тасархай = улирлын заг",
                  source_mba(), n=int(s.team_key.nunique()))
