import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.colors import to_rgba
from scipy.stats import gaussian_kde
from sklearn.metrics import confusion_matrix, roc_curve

from src.charts import label
from src.charts.comparison import fig_pareto
from src.models import ARCHETYPE_FEATURES, _metrics
from src.style import NEUTRAL, PALETTE, apply_style, finish, source_mba
from src.uncertainty import wilson_ci

CLUSTER_COLORS = [PALETTE["vermillion"], PALETTE["blue"], PALETTE["green"], PALETTE["orange"], PALETTE["purple"]]
MODEL_NAMES = {"logreg": "Logistic Regression", "rf": "Random Forest", "baseline_elo": "Baseline: Elo өндөр нь ялна",
               "baseline_winpct": "Baseline: ялалтын хувь өндөр нь ялна"}
MODEL_COLORS = {"logreg": PALETTE["blue"], "rf": PALETTE["green"], "baseline_elo": NEUTRAL, "baseline_winpct": "#6B6B6B"}
ML_SOURCE = "Эх сурвалж: MBA статистикийн систем; загвар: reports/metrics.json"


def cluster_colors(names) -> dict:
    """Архетипийн нэр → өнгө; бүх график (PCA, radar, pair plot, dashboard) ижил mapping хэрэглэнэ."""
    return dict(zip(sorted(set(names)), CLUSTER_COLORS))


def fig_elbow_silhouette(inertia_by_k: dict, silhouette_by_k: dict, k: int):
    apply_style()
    ks = sorted(int(x) for x in silhouette_by_k)
    fig, (a, b) = plt.subplots(1, 2, figsize=(6.3, 3.0))
    a.plot(ks, [inertia_by_k[str(x)] if str(x) in inertia_by_k else inertia_by_k[x] for x in ks], marker="o",
           color=PALETTE["blue"])
    b.plot(ks, [silhouette_by_k[str(x)] if str(x) in silhouette_by_k else silhouette_by_k[x] for x in ks], marker="o",
           color=PALETTE["blue"])
    for ax in (a, b):
        ax.axvline(k, color=PALETTE["vermillion"], linestyle="--", linewidth=1)
        ax.set_xlabel("Бүлгийн тоо (k)")
    a.set_ylabel("Inertia (бага нь сайн)")
    b.set_ylabel("Silhouette (их нь сайн)")
    return finish(fig, f"k = {k} архетипийг сонгосон: k ≥ 3 дотор silhouette хамгийн өндөр",
                  "Elbow (зүүн) ба silhouette (баруун); k = 2 нь зөвхөн жижиг/том тоглогч гэсэн хуваалт",
                  ML_SOURCE, n=len(ks))


def fig_pca_clusters(clusters: pd.DataFrame):
    apply_style()
    fig, ax = plt.subplots(figsize=(6.3, 4.2))
    colors = cluster_colors(clusters.cluster_name)
    names = sorted(colors)
    for name in names:
        color = colors[name]
        part = clusters[clusters.cluster_name == name]
        rgba = np.array([to_rgba(color, 0.15 + 0.85 * c) for c in part.coassign.clip(0, 1)])
        ax.scatter(part.pc1, part.pc2, s=18, c=rgba, linewidths=0, label=name)
        cx, cy = part.pc1.mean(), part.pc2.mean()
        ax.text(cx, cy, name, fontsize=8, fontweight="bold", color=color, ha="center",
                bbox={"facecolor": "white", "edgecolor": "none", "alpha": 0.7, "pad": 1})
    ax.set_xlabel("Гол бүрэлдэхүүн 1 (PCA)")
    ax.set_ylabel("Гол бүрэлдэхүүн 2 (PCA)")
    unstable = int((clusters.coassign < 0.7).sum())
    return finish(fig, f"{len(names)} архетип; {unstable} тоглогч бүлгийн заагт (тогтворгүй) байна",
                  "Цэгийн тод байдал = bootstrap-д ижил бүлэгт орсон давтамж (цайвар = тодорхой бус)",
                  ML_SOURCE, n=int(len(clusters)), uncertainty_note="Тогтвортой байдал: 100 bootstrap, Hungarian тааруулалт")


def fig_radar_centroids(centroids_z: pd.DataFrame):
    apply_style()
    feats = [f for f in ARCHETYPE_FEATURES if f in centroids_z.columns]
    angles = np.linspace(0, 2 * np.pi, len(feats), endpoint=False).tolist()
    angles += angles[:1]
    fig = plt.figure(figsize=(6.3, 4.6))
    ax = fig.add_subplot(111, polar=True)
    colors = cluster_colors(centroids_z.cluster_name)
    for r in centroids_z.sort_values("cluster_name").itertuples():
        color = colors[r.cluster_name]
        vals = [getattr(r, f) for f in feats]
        vals += vals[:1]
        ax.plot(angles, vals, color=color, linewidth=1.8, label=r.cluster_name)
        ax.fill(angles, vals, color=color, alpha=0.12)
    ax.set_xticks(angles[:-1], [label(f) for f in feats], fontsize=7)
    ax.set_yticks([-1, 0, 1])
    ax.set_yticklabels(["−1σ", "0", "+1σ"], fontsize=6)
    ax.legend(frameon=False, loc="upper right", bbox_to_anchor=(1.35, 1.1), fontsize=7)
    ax._qa_skip = True
    return finish(fig, "Архетип бүр өөр хүчтэй талтай", "Бүлгийн төвийн стандартчилсан утга (0 = лигийн дундаж)",
                  ML_SOURCE, n=int(len(centroids_z)))


def fig_confusion(y: np.ndarray, p: np.ndarray, threshold: float = 0.5):
    apply_style()
    cm = confusion_matrix(y, (p >= threshold).astype(int), labels=[0, 1])
    fig, ax = plt.subplots(figsize=(4.6, 3.8))
    ax.imshow(cm, cmap="Blues")
    for i in range(2):
        for j in range(2):
            ax.text(j, i, str(cm[i, j]), ha="center", va="center", fontsize=12,
                    color="white" if cm[i, j] > (cm.min() + cm.max()) / 2 else "black")
    ax.set_xticks([0, 1], ["Хожигдоно", "Ялна"])
    ax.set_yticks([0, 1], ["Хожигдсон", "Ялсан"])
    ax.set_xlabel("Таамаглал")
    ax.set_ylabel("Бодит")
    ax.grid(False)
    acc = np.trace(cm) / cm.sum()
    return finish(fig, f"Logistic Regression тоглолтын {acc:.0%}-ийг зөв таамагласан",
                  "Walk-forward CV-ийн бүх fold-ын таамаглал, босго 0.5", ML_SOURCE, n=int(cm.sum()))


def fig_roc(preds: pd.DataFrame):
    apply_style()
    fig, ax = plt.subplots(figsize=(5.2, 4.2))
    ax.plot([0, 1], [0, 1], color=NEUTRAL, linestyle="--", linewidth=1)
    aucs = {}
    for model, part in preds.groupby("model"):
        fpr, tpr, _ = roc_curve(part.y, part.p)
        aucs[model] = _metrics(part.y, part.p)["auc"]
        style = {"marker": "o"} if model.startswith("baseline") else {}
        ax.plot(fpr, tpr, color=MODEL_COLORS.get(model, NEUTRAL), linewidth=1.6,
                label=f"{MODEL_NAMES.get(model, model)} (AUC {aucs[model]:.2f})", **style)
    ax.legend(frameon=False, fontsize=7, loc="lower right")
    ax.set_xlabel("Худал эерэг хувь (FPR)")
    ax.set_ylabel("Үнэн эерэг хувь (TPR)")
    best = max(aucs, key=aucs.get)
    return finish(fig, f"{MODEL_NAMES.get(best, best)}-ийн AUC хамгийн өндөр ({aucs[best]:.2f})",
                  "ROC муруй, walk-forward CV-ийн таамаглал", ML_SOURCE, n=int(preds.game_id.nunique()))


def fig_metric_distributions(preds: pd.DataFrame, n_boot: int = 1000, seed: int = 42):
    apply_style()
    rng = np.random.default_rng(seed)
    order = ["logreg", "rf", "baseline_elo", "baseline_winpct"]
    models = [m for m in order if m in set(preds.model)]
    fig, ax = plt.subplots(figsize=(6.3, 3.6))
    summary = {}
    for i, m in enumerate(models):
        part = preds[preds.model == m]
        y, p = part.y.to_numpy(), part.p.to_numpy()
        dist = np.array([((p[idx] >= 0.5).astype(int) == y[idx]).mean()
                         for idx in (rng.integers(0, len(y), len(y)) for _ in range(n_boot))])
        xs = np.linspace(dist.min(), dist.max(), 200)
        dens = gaussian_kde(dist)(xs)
        ax.fill_between(xs, i, i + 0.4 * dens / dens.max(), color=MODEL_COLORS[m], alpha=0.5, linewidth=0)
        lo95, lo66, med, hi66, hi95 = np.percentile(dist, [2.5, 17, 50, 83, 97.5])
        ax.hlines(i, lo95, hi95, color="black", linewidth=1)
        ax.hlines(i, lo66, hi66, color="black", linewidth=3)
        ax.scatter([med], [i], color="white", edgecolor="black", s=30, zorder=3)
        summary[m] = (med, lo95, hi95)
    ax.set_yticks(range(len(models)), [MODEL_NAMES[m] for m in models], fontsize=7.5)
    ax.axvline(0.5, color=NEUTRAL, linestyle=":", linewidth=1)
    ax.set_xlabel("Accuracy (зөв таамагласан хувь)")
    ax.set_ylabel("Загвар")
    lr, elo = summary.get("logreg"), summary.get("baseline_elo")
    beats = lr and elo and lr[1] > elo[2]
    title = ("Загвар Elo baseline-ийг баттай давсан" if beats
             else "ML загвар энгийн Elo baseline-аас баттай илүү биш")
    return finish(fig, title, "Half-eye: тархалт + медиан + 66%/95% интервал", ML_SOURCE,
                  n=int(preds.game_id.nunique()), uncertainty_note=f"Тоглолтоор {n_boot} bootstrap; walk-forward CV")


def fig_calibration(y: np.ndarray, p: np.ndarray, n_bins: int = 5):
    apply_style()
    df = pd.DataFrame({"y": y, "p": p})
    df["bin"] = pd.qcut(df.p.rank(method="first"), n_bins, labels=False)
    fig, ax = plt.subplots(figsize=(5.2, 4.2))
    ax.plot([0, 1], [0, 1], color=NEUTRAL, linestyle="--", linewidth=1)
    xs, ys, los, his = [], [], [], []
    for _, part in df.groupby("bin"):
        ci = wilson_ci(int(part.y.sum()), len(part))
        xs.append(part.p.mean())
        ys.append(ci.est)
        los.append(ci.est - ci.lo)
        his.append(ci.hi - ci.est)
    ax.errorbar(xs, ys, yerr=[los, his], fmt="none", ecolor=PALETTE["blue"], elinewidth=1.2, capsize=3)
    ax.scatter(xs, ys, color=PALETTE["blue"], s=30, zorder=3)
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.set_xlabel("Таамагласан ялах магадлал")
    ax.set_ylabel("Бодит ялалтын хувь")
    return finish(fig, "Магадлалын тохируулга: таамаглал бодит хувьтай ойролцоо",
                  f"Logistic Regression, {n_bins} квантил бүлэг", ML_SOURCE, n=int(len(df)),
                  uncertainty_note="Шугам: бүлэг бүрийн Wilson 95% CI")


def fig_importance_pareto(expl: pd.DataFrame):
    vals = expl.set_index("feature").perm_importance.clip(lower=0)
    names = {"efg": "eFG%", "tov_pct": "TOV%", "orb_pct": "ORB%", "ftr": "FTr"}
    vals.index = [names.get(i, i) for i in vals.index]
    fig = fig_pareto(vals, pd.Series(PALETTE["blue"], index=vals.index),
                     title=f"{vals.idxmax()} ялалтыг хамгийн ихээр тайлбарладаг",
                     subtitle="Permutation importance (AUC-ийн бууралт), тухайн тоглолтын Four Factors-ийн зөрүү",
                     xlabel="Хүчин зүйл (эрэмбэлсэн)", ylabel="AUC-ийн бууралт", n=len(vals), threshold=0.8,
                     uncertainty_note="Шугам: 30 permutation-ийн 95% интервал")
    ax = fig.axes[0]
    t = expl.assign(name=[names.get(f, f) for f in expl.feature]).set_index("name").loc[
        vals.sort_values(ascending=False).index]
    ax.errorbar(np.arange(1, len(t) + 1), t.perm_importance, yerr=[t.perm_importance - t.perm_lo, t.perm_hi - t.perm_importance],
                fmt="none", ecolor="black", capsize=3, linewidth=1)
    ax.set_xticks(np.arange(1, len(t) + 1), t.index)
    ax.set_ylim(0, float(t.perm_hi.max()) * 1.1)
    return fig
