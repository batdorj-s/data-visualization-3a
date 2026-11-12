import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from src.charts import label
from src.style import IMPORT_COLORS, IMPORT_LABELS, NEUTRAL, PALETTE, apply_style, finish, source_mba
from src.uncertainty import bootstrap_distribution

GOOD, BAD = PALETTE["blue"], PALETTE["vermillion"]
FACTORS = [("efg", True), ("tov_pct", False), ("orb_pct", True), ("ftr", True)]


SHORT = {"efg": "eFG%", "tov_pct": "TOV%", "orb_pct": "ORB%", "ftr": "FTr (FTM/FGA)"}


def fig_four_factors(team_games: pd.DataFrame, season: str = "2025-2026"):
    apply_style()
    tg = team_games[(team_games.season == season) & (team_games.phase == "regular")]
    means = tg.groupby("team")[[f for f, _ in FACTORS]].mean()
    league = tg[[f for f, _ in FACTORS]].mean()
    fig, axes = plt.subplots(2, 2, figsize=(6.3, 5.6))
    for ax, (f, higher_better) in zip(axes.flat, FACTORS):
        dev = (means[f] - league[f]).sort_values(ascending=not higher_better)
        good = dev > 0 if higher_better else dev < 0
        ax.barh(range(len(dev)), dev * 100, color=np.where(good, GOOD, BAD), height=0.7)
        ax.set_yticks(range(len(dev)), dev.index, fontsize=7)
        ax.axvline(0, color="black", linewidth=0.6)
        ax.xaxis.set_major_locator(plt.MaxNLocator(4))
        ax.set_title(f"{SHORT[f]} ({'их' if higher_better else 'бага'} нь сайн)", fontsize=8.5)
        ax.set_xlabel("Лигийн дунджаас зөрүү, нэгж %", fontsize=7)
        ax._qa_no_ylabel = True
    best = (means["efg"] - league["efg"]).idxmax()
    return finish(fig, f"{best} шидэлтийн оновчоороо (eFG%) лигт тэргүүлдэг",
                  f"Dean Oliver-ийн 4 хүчин зүйл, лигийн дунджаас хазайлт · {season.replace('-20', '–')} энгийн улирал; "
                  "цэнхэр = давуу, улаан = сул", source_mba(), n=int(len(means)))


def _import_share(df: pd.DataFrame) -> float:
    return df.loc[df.is_import, "PTS"].sum() / df.PTS.sum()


def fig_import_share_donut(player_games: pd.DataFrame, n_boot: int = 2000):
    apply_style()
    share = _import_share(player_games)
    dist = bootstrap_distribution(player_games, "game_id", _import_share, n_boot=n_boot)
    lo, hi = np.percentile(dist, [2.5, 97.5])
    fig, ax = plt.subplots(figsize=(6.3, 3.8))
    wedges, _ = ax.pie([share, 1 - share], colors=[IMPORT_COLORS[True], IMPORT_COLORS[False]], startangle=90,
                       counterclock=False, wedgeprops={"width": 0.38, "edgecolor": "white"})
    for w, txt, color in zip(wedges, [f"Import\n{share:.0%}", f"Дотоод\n{1 - share:.0%}"],
                             [IMPORT_COLORS[True], IMPORT_COLORS[False]]):
        ang = np.deg2rad((w.theta2 + w.theta1) / 2)
        ax.text(1.28 * np.cos(ang), 1.18 * np.sin(ang), txt, ha="center", va="center", color=color,
                fontsize=10, fontweight="bold")
    imp_players = player_games.loc[player_games.is_import, "player_id"].nunique()
    all_players = player_games.player_id.nunique()
    ax.text(0, 0, f"{imp_players / all_players:.0%}\nтоглогч\nImport", ha="center", va="center", fontsize=9)
    ax.set_aspect("equal")
    ax.axis("off")
    return finish(fig, f"Тоглогчдын {imp_players / all_players:.0%} нь Import ч лигийн онооны {share:.0%}-ийг авдаг",
                  f"Бүх тоглолтын онооны хуваарь (95% CI {lo:.0%}–{hi:.0%}) · 2025-26 ба 2026-27",
                  source_mba(), n=int(player_games.game_id.nunique()),
                  uncertainty_note=f"CI: тоглолтоор {n_boot} bootstrap; n = тоглолтын тоо")


def pareto_table(values: pd.Series) -> pd.DataFrame:
    v = values.sort_values(ascending=False)
    return pd.DataFrame({"label": v.index, "value": v.to_numpy(), "cum_share": (v.cumsum() / v.sum()).to_numpy()})


def pareto_ci(player_games: pd.DataFrame, n_boot: int = 2000, seed: int = 42) -> tuple[np.ndarray, np.ndarray]:
    n_players = player_games.player_id.nunique()
    games = np.unique(player_games.game_id)
    idx = player_games.groupby("game_id").indices
    rng = np.random.default_rng(seed)
    curves = np.empty((n_boot, n_players))
    for b in range(n_boot):
        pick = games[rng.integers(0, len(games), len(games))]
        sample = player_games.iloc[np.concatenate([idx[g] for g in pick])]
        v = np.sort(sample.groupby("player_id").PTS.sum().to_numpy())[::-1]
        cum = np.cumsum(v) / v.sum()
        curves[b] = np.concatenate([cum, np.ones(n_players - len(cum))])[:n_players]
    point = pareto_table(player_games.groupby("player_id").PTS.sum()).cum_share.to_numpy()
    lo, hi = np.percentile(curves, [2.5, 97.5], axis=0)
    return np.minimum(lo, point), np.maximum(hi, point)


def fig_pareto(values: pd.Series, colors: pd.Series, title: str, subtitle: str, xlabel: str, ylabel: str, n: int,
               cum_ci: tuple[np.ndarray, np.ndarray] | None = None, threshold: float = 0.8,
               uncertainty_note: str | None = None, legend: dict | None = None):
    apply_style()
    t = pareto_table(values)
    x = np.arange(1, len(t) + 1)
    fig, ax = plt.subplots(figsize=(6.3, 3.9))
    ax.bar(x, t.value, color=colors.reindex(t.label).fillna(NEUTRAL).to_numpy(), width=1.0 if len(t) > 40 else 0.8,
           linewidth=0)
    ax2 = ax.twinx()
    ax2._qa_no_xlabel = True
    ax2.spines["right"].set_visible(True)
    if cum_ci is not None:
        ax2.fill_between(x, cum_ci[0], cum_ci[1], color="black", alpha=0.15, linewidth=0)
    ax2.plot(x, t.cum_share, color="black", linewidth=1.4)
    ax2.plot([x[0], x[-1]], [threshold, threshold], color=PALETTE["vermillion"], linestyle="--", linewidth=1)
    k = int(np.argmax(t.cum_share.to_numpy() >= threshold)) + 1
    ax2.plot([k, k], [0, threshold], color=PALETTE["vermillion"], linestyle=":", linewidth=1)
    ax2.annotate(f"Топ {k} ({k / len(t):.0%}) = {threshold:.0%}", (k, threshold), xytext=(8, -14),
                 textcoords="offset points", fontsize=8, color=PALETTE["vermillion"], fontweight="bold")
    ax.set_ylim(0, t.value.max() * 1.05)
    ax2.set_ylim(0, 1.0)
    ax2.yaxis.set_major_formatter(plt.FuncFormatter(lambda v, _: f"{v:.0%}"))
    ax2.grid(False)
    ax.set_xlabel(xlabel)
    ax.set_ylabel(ylabel)
    ax2.set_ylabel("Хуримтлагдсан хувь")
    if legend:
        from matplotlib.patches import Patch
        ax.legend(handles=[Patch(color=c, label=l) for l, c in legend.items()], frameon=False, loc="center right")
    fig._pareto_k = k
    return finish(fig, title, subtitle, source_mba(), n=n, uncertainty_note=uncertainty_note)


def players_to_threshold(points: pd.Series, threshold: float = 0.8) -> int:
    cum = np.cumsum(np.sort(points.to_numpy())[::-1]) / points.sum()
    return int(np.argmax(cum >= threshold)) + 1


def fig_team_concentration(player_games: pd.DataFrame, season: str = "2025-2026", n_boot: int = 2000):
    apply_style()
    pg = player_games[player_games.season == season]
    names = dict(zip(pg.team_key, pg.team)) if "team" in pg.columns else {}
    rows = []
    for key, part in pg.groupby("team_key"):
        est = players_to_threshold(part.groupby("player_id").PTS.sum())
        dist = bootstrap_distribution(part, "game_id", lambda d: players_to_threshold(d.groupby("player_id").PTS.sum()),
                                      n_boot=n_boot)
        lo, hi = np.percentile(dist, [2.5, 97.5])
        rows.append((names.get(key, key), est, lo, hi))
    df = pd.DataFrame(rows, columns=["team", "est", "lo", "hi"]).sort_values("est")
    fig, ax = plt.subplots(figsize=(6.3, 3.8))
    y = np.arange(len(df))
    ax.hlines(y, df.lo, df.hi, color=NEUTRAL, linewidth=3, alpha=0.7)
    ax.scatter(df.est, y, color=PALETTE["blue"], s=36, zorder=3)
    ax.set_yticks(y, df.team)
    ax.set_xlabel("Багийн онооны 80%-д хүрэх тоглогчийн тоо")
    ax.set_ylabel("Баг")
    top = df.iloc[0]
    return finish(fig, f"{top.team} хамгийн цөөн ({top.est:.0f}) тоглогчоосоо хамааралтай",
                  f"Цэг = тооцоолсон утга, зурвас = 95% CI · {season.replace('-20', '–')}", source_mba(), n=int(len(df)),
                  uncertainty_note=f"CI: тоглолтоор {n_boot} bootstrap")


def fig_top_dot_ci(players_ci: pd.DataFrame, metric_label: str, highlight_col: str | None = None):
    apply_style()
    df = players_ci.sort_values("est").reset_index(drop=True)
    fig, ax = plt.subplots(figsize=(6.3, 0.28 * len(df) + 1.6))
    y = np.arange(len(df))
    colors = (df[highlight_col].map(IMPORT_COLORS).fillna(PALETTE["blue"]) if highlight_col else
              pd.Series([PALETTE["blue"]] * len(df)))
    ax.hlines(y, df.lo, df.hi, color=colors, linewidth=2.5, alpha=0.45)
    ax.scatter(df.est, y, color=colors, s=30, zorder=3)
    ax.set_yticks(y, df.player)
    ax.set_xlabel(metric_label)
    ax.set_ylabel("Тоглогч")
    overlap = df.iloc[-1].lo <= df.iloc[-2].hi if len(df) > 1 else False
    title = (f"Тэргүүлэгч {df.iloc[-1].player}-ийн давуу байдал статистикийн хувьд баттай биш" if overlap
             else f"{df.iloc[-1].player} бусдаас баттай тэргүүлж байна")
    return finish(fig, title, f"Цэг = тооцоолсон утга, шугам = 95% итгэх интервал · топ {len(df)}",
                  source_mba(), n=int(len(df)), uncertainty_note="CI: тоглолтоор 2000 bootstrap")
