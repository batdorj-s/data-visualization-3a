import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from scipy import stats

from src.charts import POS_ORDER, SEASON_NOTE, label
from src.features import pythag
from src.style import NEUTRAL, PALETTE, POS_COLORS, apply_style, finish, source_mba
from src.uncertainty import fisher_ci, funnel_limits


def fig_height_reb(players: pd.DataFrame):
    apply_style()
    df = players.dropna(subset=["height_cm", "RPG", "position"])
    fig, ax = plt.subplots(figsize=(6.3, 4))
    for p in POS_ORDER:
        part = df[df.position == p]
        ax.scatter(part.height_cm, part.RPG, s=14, color=POS_COLORS[p], alpha=0.75, linewidths=0, label=p)
    slope, intercept, r, _, _ = stats.linregress(df.height_cm, df.RPG)
    xs = np.linspace(df.height_cm.min(), df.height_cm.max(), 50)
    ax.plot(xs, intercept + slope * xs, color="black", linewidth=1.2)
    ci = fisher_ci(r, len(df))
    ax.text(0.02, 0.95, f"10 см өндөр = тоглолтод +{10 * slope:.1f} самбар\nХамаарлын хүч {r:.2f} ({ci.lo:.2f}–{ci.hi:.2f})",
            transform=ax.transAxes, va="top", fontsize=8)
    ax.legend(title="Байрлал", frameon=False, ncol=5, loc="upper center", bbox_to_anchor=(0.6, 1.02), fontsize=7)
    ax.set_xlabel(label("height_cm"))
    ax.set_ylabel(label("RPG"))
    return finish(fig, f"Өндөр тоглогч илүү олон самбар авдаг: 10 см тутамд +{10 * slope:.1f} самбар",
                  "Цэг бүр 1 тоглогч, өнгө = байрлал; хар шугам = ерөнхий чиг хандлага",
                  f"{source_mba()} · {SEASON_NOTE}", n=len(df), unit="тоглогч-улирал",
                  uncertainty_note="Хаалтанд = хамаарлын хүчний 95% магадлалтай хүрээ")


MARKERS = {"2023-2024": "o", "2024-2025": "D", "2025-2026": "s", "2026-2027": "^"}


def fig_pythagorean(standings: pd.DataFrame):
    from src.models import fit_pythagorean

    apply_style()
    st = standings[(standings.W + standings.L) > 0].copy()
    fit = fit_pythagorean(st, n_boot=500)
    st["actual"] = st.W / (st.W + st.L)
    st["pred"] = pythag(st.PF, st.PA, fit["exponent"])
    fig, ax = plt.subplots(figsize=(6.3, 4.2))
    ax.plot([0, 1], [0, 1], color=NEUTRAL, linestyle="--", linewidth=1)
    for season, part in st.groupby("season"):
        ax.scatter(part.pred, part.actual, marker=MARKERS.get(season, "o"), s=26, color=PALETTE["blue"],
                   alpha=0.8, label=season.replace("-20", "–"))
    ax.legend(title="Улирал", frameon=False, fontsize=8)
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.set_xlabel("Авсан, алдсан онооноос тооцсон ялалтын хувь")
    ax.set_ylabel("Бодит ялалтын хувь")
    e_ci = fit["exponent_ci"]
    return finish(fig, f"Багийн авсан, алдсан оноо ялалтын хувийг {fit['r2']:.0%} тайлбарладаг",
                  "Цэг бүр 1 баг-улирал. Тасархай шугам дээр байвал оноо нь ялалттайгаа яг таарсан; "
                  "шугамаас дээш = онооноосоо илүү ялсан (азтай эсвэл ойр тоглолтуудад сайн)",
                  "MBA статистик (2025–27) ба Wikipedia (2023–24 улирлын хүснэгт)", n=int(len(st)), unit="баг-улирал",
                  uncertainty_note=f"Томьёоны илтгэгч {fit['exponent']:.1f} (95% магадлалтай хүрээ "
                                   f"{e_ci.lo:.1f}–{e_ci.hi:.1f}), MBA-д тааруулсан")


def fig_ts_funnel(players: pd.DataFrame):
    apply_style()
    tsa = players.FGA.fillna(0) + 0.44 * players.FTA.fillna(0)
    df = players.assign(tsa=tsa)
    df = df[(df.tsa > 0) & df.ts_pct.notna()]
    p0 = df.PTS_total.sum() / (2 * df.tsa.sum())
    n_grid = np.linspace(df.tsa.min(), df.tsa.max(), 200)
    fig, ax = plt.subplots(figsize=(6.3, 4.2))
    for z, alpha, name in ((3.09, 0.10, "99.8%"), (1.96, 0.18, "95%")):
        lo, hi = funnel_limits(p0, n_grid, z)
        ax.fill_between(n_grid, lo, hi, color=PALETTE["sky"], alpha=alpha, linewidth=0)
        ax.text(n_grid[-1], hi[-1], f" {name}", fontsize=8, va="bottom" if z > 3 else "top", color="#4D4D4D")
    lo95, hi95 = funnel_limits(p0, df.tsa.to_numpy(), 1.96)
    lo998, hi998 = funnel_limits(p0, df.tsa.to_numpy(), 3.09)
    above, below = df.ts_pct.to_numpy() > hi95, df.ts_pct.to_numpy() < lo95
    colors = np.where(above, PALETTE["green"], np.where(below, PALETTE["vermillion"], NEUTRAL))
    ax.scatter(df.tsa, df.ts_pct, s=12, c=colors, linewidths=0, alpha=0.85)
    ax.axhline(p0, color="black", linewidth=1)
    extreme = df[(df.ts_pct.to_numpy() > hi998) | (df.ts_pct.to_numpy() < lo998)]
    for r in extreme.sort_values("tsa", ascending=False).head(8).itertuples():
        ax.annotate(r.player_name.split()[0].title(), (r.tsa, r.ts_pct), xytext=(4, 2), textcoords="offset points",
                    fontsize=6.5)
    ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda v, _: f"{v:.0%}"))
    ax.set_ylim(max(0, df.ts_pct.min() - 0.05), min(1, df.ts_pct.max() + 0.05))
    ax.set_xlabel("Шидэлтийн тоо (торгуулийн шидэлтийг оролцуулан)")
    ax.set_ylabel(label("ts_pct"))
    return finish(fig, f"Зөвхөн {int(above.sum())} тоглогчийн оновч лигийн дунджаас үнэхээр өндөр",
                  f"Хар шугам = лигийн дундаж оновч {p0:.0%}. Цэнхэр юүлүүр = санамсаргүй хэлбэлзлийн хүрээ: "
                  "цөөн шидэлттэй тоглогчийнх өргөн. Ногоон = юүлүүрээс дээш (онцгой сайн), улаан = доош",
                  f"{source_mba()} · {SEASON_NOTE}", n=int(len(df)), unit="тоглогч-улирал",
                  uncertainty_note="Юүлүүрийн хил: 95% ба 99.8% магадлалтай хүрээ")
