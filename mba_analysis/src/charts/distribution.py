import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns

from src.charts import POS_ORDER, POS_SHORT, SEASON_NOTE, label
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
                f"{IMPORT_LABELS[imp]}: голч {medians[imp]:.1f} оноо ({len(s)} тоглогч)",
                color=IMPORT_COLORS[imp], fontsize=8, fontweight="bold")
    ax.set_xlabel(label("PPG"))
    ax.set_ylabel("Тоглогчийн тоо")
    diff = medians[True] - medians[False]
    return finish(fig, f"Гадаад тоглогч дотоод тоглогчоос тоглолт бүрт {diff:.1f} оноогоор илүү авдаг",
                  "Багана = тухайн онооны түвшинд хэдэн тоглогч байгаа; тасархай шугам = голч утга. "
                  "Ихэнх тоглогч цөөн оноо авдаг, цөөхөн нь маш их оноо авдаг",
                  f"{source_mba()} · {SEASON_NOTE}", n=len(players), unit="тоглогч-улирал")


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
    return finish(fig, f"{POS_SHORT[best]} ({best}) байрлалын тоглогчдын шидэлтийн оновч хамгийн өндөр",
                  "Хайрцаг = тоглогчдын дунд хэсгийн 50%, хар зураас = голч утга, цэг = бусдаасаа эрс ялгарах тоглогч",
                  f"{source_mba()} · {SEASON_NOTE}, {MIN_TSA}-аас олон шидэлт хийсэн", n=len(df), unit="тоглогч-улирал")


CORR_COLS = ["PPG", "RPG", "APG", "SPG", "BPG", "MIN", "ts_pct", "tpa_rate", "height_cm", "age"]


CORR_SHORT = {"PPG": "Оноо", "RPG": "Самбар", "APG": "Дамжуулалт", "SPG": "Таслалт", "BPG": "Хаалт", "MIN": "Минут",
              "ts_pct": "Оновч", "tpa_rate": "3 онооны хувь", "height_cm": "Өндөр", "age": "Нас"}


def fig_corr_heatmap(players: pd.DataFrame):
    apply_style()
    corr = players[CORR_COLS].apply(pd.to_numeric, errors="coerce").corr()
    fig, ax = plt.subplots(figsize=(6.3, 5.4))
    im = ax.imshow(corr.values, cmap="RdBu_r", vmin=-1, vmax=1)
    labels = [CORR_SHORT[c] for c in CORR_COLS]
    ax.set_xticks(range(len(CORR_COLS)), labels, rotation=45, ha="right")
    ax.set_yticks(range(len(CORR_COLS)), labels)
    ax.grid(False)
    for i in range(len(CORR_COLS)):
        for j in range(len(CORR_COLS)):
            v = corr.values[i, j]
            ax.text(j, i, f"{v:.2f}", ha="center", va="center", fontsize=7, color="white" if abs(v) > 0.6 else "black")
    cb = fig.colorbar(im, ax=ax, fraction=0.04, pad=0.02)
    cb.set_label("Хамаарлын хүч (−1 … 1)")
    ax.set_xlabel("Хувьсагч")
    ax.set_ylabel("Хувьсагч")
    tri = corr.where(~np.eye(len(corr), dtype=bool)).stack()
    (a, b), r = tri.abs().idxmax(), tri[tri.abs().idxmax()]
    return finish(fig, f"«{CORR_SHORT[a]}» ба «{CORR_SHORT[b]}» хамгийн хүчтэй холбоотой ({r:.2f})",
                  "Нүд бүр 2 үзүүлэлт хэр хамт өөрчлөгддөгийг харуулна (тоглолтын дунджаар): улаан = хамт өсдөг, "
                  "цэнхэр = эсрэг, цагаан = холбоогүй",
                  f"{source_mba()} · {SEASON_NOTE}", n=len(players), unit="тоглогч-улирал")


def fig_ppg_violin(players: pd.DataFrame):
    apply_style()
    df = players.dropna(subset=["pos_group"]).assign(status=lambda d: d.is_import.astype(bool).map(IMPORT_LABELS))
    order = ["Guard", "Forward", "Center"]
    names = {"Guard": "Хамгаалагч", "Forward": "Довтлогч", "Center": "Төв"}
    fig, ax = plt.subplots(figsize=(6.3, 3.8))
    sns.violinplot(data=df, x="pos_group", y="PPG", hue="status", order=order, hue_order=[IMPORT_LABELS[False], IMPORT_LABELS[True]],
                   split=True, inner="quart", cut=0, density_norm="width", linewidth=0.8,
                   palette={IMPORT_LABELS[False]: IMPORT_COLORS[False], IMPORT_LABELS[True]: IMPORT_COLORS[True]}, ax=ax)
    ax.set_xticks(range(3), [names[o] for o in order])
    ax.set_xlabel("Байрлалын бүлэг")
    ax.set_ylabel(label("PPG"))
    ax.legend(title="", frameon=False, loc="upper left")
    gap = df.groupby(["pos_group", "status"]).PPG.median().unstack()
    widest = (gap[IMPORT_LABELS[True]] - gap[IMPORT_LABELS[False]]).idxmax()
    return finish(fig, f"Гадаад ба дотоод тоглогчийн онооны зөрүү {names[widest].lower()} байрлалд хамгийн их",
                  "Өргөн хэсэг = олон тоглогч тэр оноотой. Зүүн тал = дотоод, баруун тал = гадаад; "
                  "тасархай = голч ба дунд хэсгийн хил",
                  f"{source_mba()} · {SEASON_NOTE}", n=len(df), unit="тоглогч-улирал")


PAIR_COLS = ["pts36", "reb36", "ast36", "ts_pct"]


def fig_pairplot(players: pd.DataFrame, labels: pd.Series | None):
    apply_style()
    df = players[players.MIN_total >= 150].copy() if "MIN_total" in players else players.copy()
    df = df.dropna(subset=PAIR_COLS)
    if labels is not None:
        df["Бүлэг"] = labels.reindex(df.index).astype(str)
        from src.charts.ml import cluster_colors
        palette = cluster_colors(df["Бүлэг"].dropna())
        hue, subtitle = "Бүлэг", "Өнгө = компьютерийн олсон тоглолтын хэв маяг"
    else:
        df["Бүлэг"] = df.position
        palette = POS_COLORS
        hue, subtitle = "Бүлэг", "Өнгө = байрлал"
    short = {"pts36": "Оноо /36 мин", "reb36": "Самбар /36 мин", "ast36": "Дамжуулалт /36 мин", "ts_pct": "Оновч"}
    grid = sns.pairplot(df[PAIR_COLS + [hue]].rename(columns=short), hue=hue,
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
    return finish(fig, "Тоглогчдын хэв маяг оноо, самбар, дамжуулалтаар тод ялгардаг",
                  f"Цэг бүр 1 тоглогч; хос үзүүлэлт бүрийг харьцуулсан («/36 мин» = 36 минутад ногдох). {subtitle}",
                  f"{source_mba()} · {SEASON_NOTE}, 150-аас олон минут тоглосон", n=len(df), unit="тоглогч-улирал")


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
    est = float(players.loc[players.is_import.astype(bool), "PPG"].median()
                - players.loc[~players.is_import.astype(bool), "PPG"].median())
    ax2.hist(boot_diff, bins=40, color=NEUTRAL, edgecolor="white", linewidth=0.3)
    for v in (lo, hi):
        ax2.axvline(v, color="black", linestyle="--", linewidth=1)
    ax2.axvline(0, color=PALETTE["vermillion"], linewidth=1)
    ax2.set_xlabel("Голч онооны зөрүү (гадаад − дотоод), 2000 удаа дахин тооцсон")
    ax2.set_ylabel("Хэдэн удаа")
    return finish(fig, f"Гадаад тоглогч {est:.1f}-оор илүү оноо авдаг; бодит зөрүү {lo:.1f}–{hi:.1f} оноо байх магадлалтай",
                  "Дээр: цэг бүр 1 тоглогч. Доор: зөрүүг 2000 удаа дахин тооцоход гарсан утгууд — "
                  "тасархай шугамын хооронд 95% нь багтана, улаан шугам (0) = зөрүүгүй",
                  f"{source_mba()} · {SEASON_NOTE}", n=len(players), unit="тоглогч-улирал",
                  uncertainty_note=f"Тодорхой бус байдлыг тоглогчдыг {len(boot_diff)} удаа дахин сонгож тооцов")
