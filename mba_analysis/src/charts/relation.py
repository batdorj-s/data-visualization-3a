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
    ax.text(0.02, 0.95, f"r = {r:.2f} (95% CI {ci.lo:.2f}–{ci.hi:.2f})\n+10 см ≈ +{10 * slope:.1f} самбар",
            transform=ax.transAxes, va="top", fontsize=8)
    ax.legend(title="Байрлал", frameon=False, ncol=5, loc="upper center", bbox_to_anchor=(0.6, 1.02), fontsize=7)
    ax.set_xlabel(label("height_cm"))
    ax.set_ylabel(label("RPG"))
    return finish(fig, f"Өндөр нэмэгдэх тусам самбар өсдөг (r = {r:.2f})",
                  f"Шугам = OLS регресс · {SEASON_NOTE}", source_mba(), n=len(df),
                  uncertainty_note="r-ийн 95% CI: Fisher z хувиргалт")


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
    ax.legend(title="Улирал", frameon=False, fontsize=7)
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.set_xlabel(f"Таамагласан ялалтын хувь (PF^e / (PF^e + PA^e), e = {fit['exponent']:.1f})")
    ax.set_ylabel("Бодит ялалтын хувь")
    e_ci = fit["exponent_ci"]
    return finish(fig, f"Авсан/алдсан онооноос ялалтын хувийг сайн таамаглана (R² = {fit['r2']:.2f})",
                  f"Pythagorean expectation; NBA-ийн 13.91-ийн оронд лигт тааруулсан e = {fit['exponent']:.1f} "
                  f"(95% CI {e_ci.lo:.1f}–{e_ci.hi:.1f})", "Эх сурвалж: MBA (2025–27), Wikipedia (2023–24)",
                  n=int(len(st)), uncertainty_note="e-ийн CI: баг-улирлаар 500 bootstrap")


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
        ax.text(n_grid[-1], hi[-1], f" {name}", fontsize=7, va="center", color="#4D4D4D")
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
    ax.set_xlabel("Шидэлтийн оролдлого (FGA + 0.44·FTA)")
    ax.set_ylabel(label("ts_pct"))
    return finish(fig, f"Зөвхөн {int(above.sum())} тоглогчийн оновч лигийн дунджаас баттай өндөр",
                  f"Хар шугам = лигийн TS% {p0:.1%}; ногоон = 95% хилээс дээш, улаан = доош · {SEASON_NOTE}",
                  source_mba(), n=int(len(df)),
                  uncertainty_note="Хил: TS%-ийг пропорц гэж үзсэн биномын ойролцоолол; цөөн шидэлттэй үед хил өргөн")
