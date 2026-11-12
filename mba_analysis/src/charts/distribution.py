import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns

from src.charts import POS_ORDER, SEASON_NOTE, label
from src.style import IMPORT_COLORS, IMPORT_LABELS, NEUTRAL, PALETTE, POS_COLORS, apply_style, finish, source_mba

MIN_TSA = 30


def fig_ppg_hist(players: pd.DataFrame):
    apply_style()
    fig, ax = plt.subplots(figsize=(6.3, 3.8))
    bins = np.arange(0, players.PPG.max() + 1.5, 1.5)
    medians = {}
    for imp in (False, True):
        s = players.loc[players.is_import.astype(bool) == imp, "PPG"]
        medians[imp] = s.median()
        ax.hist(s, bins=bins, color=IMPORT_COLORS[imp], alpha=0.55, edgecolor="white", linewidth=0.5)
        ax.axvline(medians[imp], color=IMPORT_COLORS[imp], linestyle="--", linewidth=1.2)
        top = ax.get_ylim()[1]
        ax.text(medians[imp] + 0.4, top * (0.92 if imp else 0.80),
                f"{IMPORT_LABELS[imp]} (медиан {medians[imp]:.1f}, n={len(s)})",
                color=IMPORT_COLORS[imp], fontsize=8, fontweight="bold")
    ax.set_xlabel(label("PPG"))
    ax.set_ylabel("Тоглогчийн тоо")
    diff = medians[True] - medians[False]
    return finish(fig, f"Import тоглогчийн медиан оноо дотоодынхоос {diff:.1f}-оор их",
                  f"Нэг тоглолтын онооны тархалт баруун тийш хазгай · {SEASON_NOTE}", source_mba(), n=len(players))


def _tsa(players: pd.DataFrame) -> pd.Series:
    return players.FGA.fillna(0) + 0.44 * players.FTA.fillna(0)


def fig_ts_box_by_pos(players: pd.DataFrame):
    apply_style()
    df = players[(_tsa(players) >= MIN_TSA) & players.position.isin(POS_ORDER)]
    fig, ax = plt.subplots(figsize=(6.3, 3.8))
    data = [df.loc[df.position == p, "ts_pct"].dropna() for p in POS_ORDER]
    bp = ax.boxplot(data, patch_artist=True, widths=0.55, showfliers=True,
                    medianprops={"color": "black"}, flierprops={"marker": "o", "markersize": 3,
                                                                "markerfacecolor": NEUTRAL, "markeredgecolor": NEUTRAL})
    for patch, p in zip(bp["boxes"], POS_ORDER):
        patch.set_facecolor(POS_COLORS[p])
        patch.set_alpha(0.75)
    ax.set_xticks(range(1, 6), POS_ORDER)
    outliers = []
    for i, p in enumerate(POS_ORDER, 1):
        part = df[df.position == p]
        q1, q3 = part.ts_pct.quantile([0.25, 0.75])
        lim = 1.5 * (q3 - q1)
        out = part[(part.ts_pct < q1 - lim) | (part.ts_pct > q3 + lim)]
        outliers += [(i, r.ts_pct, r.player_name) for r in out.itertuples()]
    for i, y, name in sorted(outliers, key=lambda t: -abs(t[1] - df.ts_pct.median()))[:6]:
        ax.annotate(name.split()[0].title(), (i, y), xytext=(6, 0), textcoords="offset points", fontsize=7)
    ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda v, _: f"{v:.0%}"))
    ax.set_xlabel("Байрлал")
    ax.set_ylabel(label("ts_pct"))
    best = max(POS_ORDER, key=lambda p: df.loc[df.position == p, "ts_pct"].median())
    return finish(fig, f"{best} байрлалын тоглогчдын шидэлтийн оновч (TS%) хамгийн өндөр",
                  f"Шидэлтийн оролдлого ≥ {MIN_TSA}; цэг = 1.5·IQR-аас гадуурх тоглогч · {SEASON_NOTE}",
                  source_mba(), n=len(df))


CORR_COLS = ["PPG", "RPG", "APG", "SPG", "BPG", "MIN", "ts_pct", "tpa_rate", "height_cm", "age"]


def fig_corr_heatmap(players: pd.DataFrame):
    apply_style()
    corr = players[CORR_COLS].apply(pd.to_numeric, errors="coerce").corr()
    fig, ax = plt.subplots(figsize=(6.3, 5.4))
    im = ax.imshow(corr.values, cmap="RdBu_r", vmin=-1, vmax=1)
    labels = [label(c) for c in CORR_COLS]
    ax.set_xticks(range(len(CORR_COLS)), labels, rotation=45, ha="right")
    ax.set_yticks(range(len(CORR_COLS)), labels)
    ax.grid(False)
    for i in range(len(CORR_COLS)):
        for j in range(len(CORR_COLS)):
            v = corr.values[i, j]
            ax.text(j, i, f"{v:.2f}", ha="center", va="center", fontsize=6.5, color="white" if abs(v) > 0.6 else "black")
    cb = fig.colorbar(im, ax=ax, fraction=0.04, pad=0.02)
    cb.set_label("Pearson r")
    ax.set_xlabel("Хувьсагч")
    ax.set_ylabel("Хувьсагч")
    tri = corr.where(~np.eye(len(corr), dtype=bool)).stack()
    (a, b), r = tri.abs().idxmax(), tri[tri.abs().idxmax()]
    return finish(fig, f"{label(a)} ба {label(b)} хамгийн хүчтэй хамааралтай (r = {r:.2f})",
                  f"Тоглогчийн статистикийн корреляцийн матриц · {SEASON_NOTE}", source_mba(), n=len(players))


def fig_ppg_violin(players: pd.DataFrame):
    apply_style()
    df = players.dropna(subset=["pos_group"]).assign(status=lambda d: d.is_import.astype(bool).map(IMPORT_LABELS))
    order = ["Guard", "Forward", "Center"]
    names = {"Guard": "Хамгаалагч", "Forward": "Довтлогч", "Center": "Төв"}
    fig, ax = plt.subplots(figsize=(6.3, 3.8))
    sns.violinplot(data=df, x="pos_group", y="PPG", hue="status", order=order, hue_order=["Дотоод", "Import"],
                   split=True, inner="quart", cut=0, density_norm="width", linewidth=0.8,
                   palette={"Дотоод": IMPORT_COLORS[False], "Import": IMPORT_COLORS[True]}, ax=ax)
    ax.set_xticks(range(3), [names[o] for o in order])
    ax.set_xlabel("Байрлалын бүлэг")
    ax.set_ylabel(label("PPG"))
    ax.legend(title="", frameon=False, loc="upper left")
    gap = df.groupby(["pos_group", "status"]).PPG.median().unstack()
    widest = (gap["Import"] - gap["Дотоод"]).idxmax()
    return finish(fig, f"Import ба дотоодын онооны ялгаа {names[widest].lower()} байрлалд хамгийн их",
                  f"Хагас violin: зүүн = дотоод, баруун = Import; тасархай = квартил · {SEASON_NOTE}",
                  source_mba(), n=len(df))


PAIR_COLS = ["pts36", "reb36", "ast36", "ts_pct"]


def fig_pairplot(players: pd.DataFrame, labels: pd.Series | None):
    apply_style()
    df = players[players.MIN_total >= 150].copy() if "MIN_total" in players else players.copy()
    df = df.dropna(subset=PAIR_COLS)
    if labels is not None:
        df["Бүлэг"] = labels.reindex(df.index).astype(str)
        from src.charts.ml import cluster_colors
        palette = cluster_colors(df["Бүлэг"].dropna())
        hue, subtitle = "Бүлэг", "Өнгө = K-Means архетип"
    else:
        df["Бүлэг"] = df.position
        palette = POS_COLORS
        hue, subtitle = "Бүлэг", "Өнгө = байрлал"
    grid = sns.pairplot(df[PAIR_COLS + [hue]].rename(columns={c: label(c) for c in PAIR_COLS}), hue=hue,
                        palette=palette, corner=True, plot_kws={"s": 10, "alpha": 0.7, "linewidth": 0},
                        diag_kws={"common_norm": False})
    fig = grid.figure
    fig.set_size_inches(6.3, 6.3)
    for ax in fig.axes:
        if not ax.get_xlabel():
            ax._qa_no_xlabel = True
        if not ax.get_ylabel():
            ax._qa_no_ylabel = True
    if grid.legend is not None:
        grid.legend.set_title("")
    return finish(fig, "Тоглогчдын хэв маяг олон хувьсагчаар ялгардаг",
                  f"{subtitle} · нийт минут ≥ 150 · {SEASON_NOTE}", source_mba(), n=len(df))


def _half_violin(ax, data, pos, color):
    parts = ax.violinplot([data], positions=[pos], orientation="horizontal", widths=0.8, showextrema=False)
    for body in parts["bodies"]:
        verts = body.get_paths()[0].vertices
        verts[:, 1] = np.clip(verts[:, 1], pos, np.inf)
        body.set_facecolor(color)
        body.set_alpha(0.6)
        body.set_edgecolor("none")


def fig_raincloud(players: pd.DataFrame, boot_diff: np.ndarray):
    apply_style()
    fig, (ax, ax2) = plt.subplots(2, 1, figsize=(6.3, 4.8), gridspec_kw={"height_ratios": [3, 1.3]})
    rng = np.random.default_rng(42)
    for pos, imp in ((0, False), (1, True)):
        s = players.loc[players.is_import.astype(bool) == imp, "PPG"].dropna().to_numpy()
        color = IMPORT_COLORS[imp]
        _half_violin(ax, s, pos, color)
        ax.boxplot([s], positions=[pos - 0.1], orientation="horizontal", widths=0.08, showfliers=False,
                   medianprops={"color": "black"}, boxprops={"color": color}, whiskerprops={"color": color},
                   capprops={"color": color})
        ax.scatter(s, pos - 0.28 + rng.uniform(-0.07, 0.07, s.size), s=6, color=color, alpha=0.6, linewidths=0)
    ax.set_yticks([0, 1], [IMPORT_LABELS[False], IMPORT_LABELS[True]])
    ax.set_xlabel(label("PPG"))
    ax.set_ylabel("Тоглогчийн төрөл")
    lo, hi = np.percentile(boot_diff, [2.5, 97.5])
    est = float(np.median(boot_diff))
    ax2.hist(boot_diff, bins=40, color=NEUTRAL, edgecolor="white", linewidth=0.3)
    for v in (lo, hi):
        ax2.axvline(v, color="black", linestyle="--", linewidth=1)
    ax2.axvline(0, color=PALETTE["vermillion"], linewidth=1)
    ax2.set_xlabel("Медиан PPG-ийн зөрүү (Import − дотоод), bootstrap")
    ax2.set_ylabel("Давтамж")
    return finish(fig, f"Import тоглогчийн медиан оноо {est:.1f}-оор их (95% CI {lo:.1f}–{hi:.1f})",
                  f"Дээр: тархалт + хайрцаг + тоглогч бүр; доор: зөрүүний тодорхой бус байдал · {SEASON_NOTE}",
                  source_mba(), n=len(players),
                  uncertainty_note=f"95% CI: тоглогчоор {len(boot_diff)} удаагийн bootstrap; улаан шугам = зөрүүгүй")
