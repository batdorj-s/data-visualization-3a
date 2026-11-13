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

from src.palette import CLUSTER_COLORS, cluster_colors  # noqa: E402,F401
MODEL_NAMES = {"logreg": "ML загвар (логистик регресс)", "rf": "ML загвар (санамсаргүй ой)",
               "baseline_elo": "Энгийн дүрэм: хүчний оноо өндөр нь ялна",
               "baseline_winpct": "Энгийн дүрэм: ялалтын хувь өндөр нь ялна"}
MODEL_COLORS = {"logreg": PALETTE["blue"], "rf": PALETTE["green"], "baseline_elo": NEUTRAL, "baseline_winpct": "#6B6B6B"}
ML_SOURCE = "MBA лигийн албан ёсны статистик (mongolia.basketball), 2025–26 ба 2026–27 улирал"



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
    a.set_ylabel("Бүлэг доторх зөрүү (бага нь сайн)")
    b.set_ylabel("Бүлгүүдийн тодорхой ялгарал (их нь сайн)")
    return finish(fig, f"Тоглогчдыг {k} хэв маягт хуваах нь хамгийн тохиромжтой",
                  "Зүүн: бүлэг нэмэх тусам бүлэг доторх зөрүү буурна. Баруун: бүлгүүд хэр тод ялгарч байгаа. "
                  "2 бүлэг нь зөвхөн «намхан/өндөр» гэсэн хуваалт өгдөг тул 3-аас эхлэн сонгосон",
                  ML_SOURCE, n=len(ks), unit="хувилбар (бүлгийн тоо)")


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
    ax.set_xlabel("Хэв маягийн 1-р тэнхлэг")
    ax.set_ylabel("Хэв маягийн 2-р тэнхлэг")
    unstable = int((clusters.coassign < 0.7).sum())
    return finish(fig, f"{len(names)} хэв маяг; {unstable} тоглогч аль бүлэгт орох нь тодорхой бус",
                  "Цэг бүр 1 тоглогч; олон үзүүлэлтийг 2 тэнхлэгт шахаж зурсан тул ойр цэгүүд төстэй. "
                  "Цайвар цэг = дахин тооцоход өөр бүлэгт орж байсан (заагийн) тоглогч",
                  ML_SOURCE, n=int(len(clusters)), unit="тоглогч-улирал",
                  uncertainty_note="Тогтвортой байдлыг 100 удаа дахин бүлэглэж шалгав")


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
    ax.set_xticks(angles[:-1], [label(f) for f in feats], fontsize=8)
    ax.set_yticks([-1, 0, 1])
    ax.set_yticklabels(["", "дундаж", ""], fontsize=7, color="#6B6B6B")
    ax.legend(frameon=False, loc="lower left", bbox_to_anchor=(1.08, 0.0), fontsize=8)
    ax._qa_skip = True
    return finish(fig, "Хэв маяг бүр өөр хүчтэй талтай",
                  "Хэв маяг бүрийн дундаж тоглогчийг лигийн дундажтай (дунд цагираг) харьцуулав: "
                  "гадагш тодорсон тал = тэр бүлгийн хүчтэй тал",
                  ML_SOURCE, n=int(len(centroids_z)), unit="хэв маяг")


def fig_confusion(y: np.ndarray, p: np.ndarray, threshold: float = 0.5):
    apply_style()
    cm = confusion_matrix(y, (p >= threshold).astype(int), labels=[0, 1])
    fig, ax = plt.subplots(figsize=(4.6, 3.8))
    ax.imshow(cm, cmap="Blues")
    for i in range(2):
        for j in range(2):
            ax.text(j, i, str(cm[i, j]), ha="center", va="center", fontsize=12,
                    color="white" if cm[i, j] > (cm.min() + cm.max()) / 2 else "black")
    ax.set_xticks([0, 1], ["Хожигдоно гэсэн", "Ялна гэсэн"])
    ax.set_yticks([0, 1], ["Хожигдсон", "Ялсан"])
    ax.set_xlabel("Загварын таамаглал")
    ax.set_ylabel("Бодит үр дүн")
    ax.grid(False)
    acc = np.trace(cm) / cm.sum()
    return finish(fig, f"Загвар тоглолтын {acc:.0%}-ийн ялагчийг зөв таамагласан",
                  "Диагональ (зүүн дээд, баруун доод) = зөв таамаглал. Загварт зөвхөн тухайн тоглолтоос өмнөх "
                  "датаг өгсөн", ML_SOURCE, n=int(cm.sum()), unit="таамагласан тоглолт")


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
    ax.legend(frameon=False, fontsize=7.5, loc="lower right")
    ax.set_xlabel("Хожигдох тоглолтыг «ялна» гэж андуурсан хувь")
    ax.set_ylabel("Ялах тоглолтыг зөв олсон хувь")
    best = max(aucs, key=aucs.get)
    return finish(fig, f"«{MODEL_NAMES.get(best, best)}» ялагчийг хамгийн сайн ялгадаг ({aucs[best]:.2f})",
                  "Муруй зүүн дээд булан руу ойртох тусам сайн; тасархай = санамсаргүй таавар. "
                  "Хаалтанд = ялгах чадвар (0.5 санамсаргүй, 1 төгс)", ML_SOURCE, n=int(preds.game_id.nunique()),
                  unit="таамагласан тоглолт")


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
    ax.set_yticks(range(len(models)), [MODEL_NAMES[m] for m in models], fontsize=8)
    ax.axvline(0.5, color=NEUTRAL, linestyle=":", linewidth=1)
    ax.set_xlabel("Зөв таамагласан хувь")
    ax.set_ylabel("Арга")
    lr, elo = summary.get("logreg"), summary.get("baseline_elo")
    beats = lr and elo and lr[1] > elo[2]
    title = ("ML загвар «хүчний оноо өндөр нь ялна» гэсэн энгийн дүрмийг баттай давсан" if beats
             else "ML загвар «хүчний оноо өндөр нь ялна» гэсэн энгийн дүрмээс баттай илүү биш")
    return finish(fig, title, "Цагаан цэг = зөв таамагласан хувь, бүдүүн шугам = 66%, нарийн шугам = 95% магадлалтай "
                  "хүрээ. Хүрээнүүд давхцаж байвал аргуудыг ялгах боломжгүй", ML_SOURCE,
                  n=int(preds.game_id.nunique()), unit="таамагласан тоглолт",
                  uncertainty_note=f"Хүрээг тоглолтуудыг {n_boot} удаа дахин сонгож тооцов")


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
    off = sum(not (y_ - lo_ <= x_ <= y_ + hi_) for x_, y_, lo_, hi_ in zip(xs, ys, los, his))
    title = ("Загварын хэлсэн магадлал бодит ялалтын хувьтай таарч байна" if off == 0
             else f"{len(xs)} бүлгийн {off}-д загварын хэлсэн магадлал бодит ялалтын хувиас зөрсөн")
    return finish(fig, title,
                  f"Тоглолтуудыг загварын таамагласан магадлалаар {n_bins} бүлэгт хуваав. Цэг тасархай шугам дээр "
                  "байвал «70% ялна» гэсэн тоглолтуудын бараг 70% нь үнэхээр ялсан гэсэн үг", ML_SOURCE,
                  n=int(len(df)), unit="таамагласан тоглолт",
                  uncertainty_note="Босоо шугам = бүлэг бүрийн 95% магадлалтай хүрээ")


def fig_importance_pareto(expl: pd.DataFrame):
    vals = expl.set_index("feature").perm_importance.clip(lower=0)
    names = {"efg": "Оновч", "tov_pct": "Бөмбөг алдалт", "orb_pct": "Довт. самбар", "ftr": "Торгууль авалт"}
    vals.index = [names.get(i, i) for i in vals.index]
    fig = fig_pareto(vals, pd.Series(PALETTE["blue"], index=vals.index),
                     title=f"Ялалтын 4 хүчин зүйлээс «{vals.idxmax()}» хамгийн чухал",
                     subtitle="Багана = тухайн хүчин зүйлийг загвараас «нуувал» таамаглал хэр муудах вэ "
                              "(өндөр = чухал). Хар шугам = нийлбэр хувь",
                     xlabel="Хүчин зүйл (чухлаас нь эрэмбэлсэн)", ylabel="Таамаглал муудах хэмжээ", n=len(vals),
                     threshold=0.8, unit="хүчин зүйл", source=ML_SOURCE,
                     uncertainty_note="Багана дээрх зураас = 30 удаагийн туршилтын 95% хүрээ")
    ax = fig.axes[0]
    t = expl.assign(name=[names.get(f, f) for f in expl.feature]).set_index("name").loc[
        vals.sort_values(ascending=False).index]
    ax.errorbar(np.arange(1, len(t) + 1), t.perm_importance, yerr=[t.perm_importance - t.perm_lo, t.perm_hi - t.perm_importance],
                fmt="none", ecolor="black", capsize=3, linewidth=1)
    ax.set_xticks(np.arange(1, len(t) + 1), t.index)
    ax.set_ylim(0, float(t.perm_hi.max()) * 1.1)
    return fig
