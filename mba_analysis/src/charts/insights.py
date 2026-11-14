"""Нэмэлт олдворуудын график: талбай дээрх гадаад тоглогч, тэргүүллийн найдвартай байдал, эргэлт, зайны муруй,
дамжуулалттай оноо, довтолгоо–хамгаалалт, ачаалал–оновч, улирал хоорондын тогтвортой байдал."""
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from src.insights import CHECKPOINTS, LEAD_LABELS
from src.pbp import ZONES
from src.style import IMPORT_COLORS, IMPORT_LABELS, NEUTRAL, PALETTE, apply_style, finish, source_mba
from src.uncertainty import wilson_ci

PBP = "MBA тоглолтын явцын бичлэг"
SHOTS = "MBA тоглолтын хуудасны шидэлтийн байршил"
COUNT_COLORS = {0: "#D9D9D9", 1: "#FDCC8A", 2: "#E66101", 3: "#7F2704"}
PCT = plt.FuncFormatter(lambda v, _: f"{v:.0%}")


def _season(s: str) -> str:
    return s.replace("-20", "–")


def fig_imports_on_court(ioc: pd.DataFrame, pts_share: pd.DataFrame, coverage: float):
    apply_style()
    seasons = sorted(ioc.season.unique())
    fig, axes = plt.subplots(1, len(seasons), figsize=(6.3, 4.7), sharey=True)
    mean = ioc.drop_duplicates(["season", "period"]).set_index(["season", "period"]).mean_k
    pts = pts_share.set_index(["season", "period"]).import_pts_share
    for ax, season in zip(np.atleast_1d(axes), seasons):
        d = ioc[ioc.season == season].pivot_table(index="period", columns="k", values="share", fill_value=0)
        bottom = np.zeros(len(d))
        for k in sorted(d.columns):
            ax.bar(d.index, d[k], bottom=bottom, color=COUNT_COLORS[int(k)], width=0.7,
                   label=f"{int(k)} гадаад" if ax is np.atleast_1d(axes)[0] else None)
            bottom += d[k].to_numpy()
        for q in d.index:
            ax.text(q, 1.02, f"дундаж {mean[season, q]:.1f}\nоноо {pts[season, q]:.0%}", ha="center", va="bottom",
                    fontsize=7.5)
        ax.set_title(f"{_season(season)} улирал", fontsize=9.5, pad=24)
        ax.set_xticks([1, 2, 3, 4], [f"{q}-р үе" for q in (1, 2, 3, 4)])
        ax.set_ylim(0, 1)
        ax.yaxis.set_major_formatter(PCT)
        ax.set_xlabel("Тоглолтын үе")
        ax.grid(axis="x", visible=False)
    np.atleast_1d(axes)[0].set_ylabel("Тоглох хугацааны хувь")
    for ax in np.atleast_1d(axes)[1:]:
        ax._qa_no_ylabel = True
    fig.legend(loc="lower center", ncol=4, frameon=False, fontsize=8, bbox_to_anchor=(0.5, 0.10),
               title="Нэг багийн талбай дээрх гадаад тоглогчийн тоо", title_fontsize=8)
    a, b = seasons[0], seasons[-1]
    mid, edge = (mean[a, 2] + mean[a, 3]) / 2, (mean[a, 1] + mean[a, 4]) / 2
    fig = finish(fig, f"{_season(a)}-д гадаад тоглогч 2, 3-р үед илүү олон тоглосон ({mid:.1f} vs {edge:.1f}); "
                      f"{_season(b)}-д бүх үед ~{np.mean([mean[b, q] for q in (1, 2, 3, 4)]):.1f}",
                 "Багана = тухайн үеийн хугацааны хэдэн хувьд нэг баг 0, 1, 2, 3 гадаад тоглогчтой тоглосон. Баганын дээр: "
                 "дундаж тоо ба тэр үеийн онооны хэдэн хувийг гадаад тоглогч авсан",
                 f"{PBP} · талбай дээрх 5 тоглогчийг солилтоос сэргээсэн (хугацааны {coverage:.1%}-д амжилттай)",
                 n=int(ioc.seconds.sum() // 60), unit="баг-минут",
                 uncertainty_note="Гадаад эсэхийг MBA-ийн тоглогчийн профайлын шошгоор тодорхойлсон; лигийн дүрмийн "
                                  "албан бичвэрээр баталгаажуулаагүй — зөвхөн датанд ажиглагдсан хэв маяг")
    fig.subplots_adjust(bottom=fig.subplotpars.bottom + 0.10)
    return fig


def fig_lead_safety(ls: pd.DataFrame):
    apply_style()
    fig, ax = plt.subplots(figsize=(6.3, 3.9))
    colors = dict(zip(CHECKPOINTS, [PALETTE["sky"], PALETTE["blue"], "#08306B"]))
    x = np.arange(len(LEAD_LABELS))
    for i, name in enumerate(CHECKPOINTS):
        d = ls[ls.checkpoint == name].set_index("bin").reindex(LEAD_LABELS)
        xs = x + (i - 1) * 0.16
        ax.errorbar(xs, d.est, yerr=[d.est - d.lo, d.hi - d.est], fmt="none", ecolor=colors[name], elinewidth=1.4,
                    capsize=2.5, alpha=0.8)
        ax.plot(xs, d.est, marker="o", color=colors[name], lw=1.6, ms=5, label=name)
    ax.axhline(0.5, color="black", lw=0.6, ls=":")
    ax.set_xticks(x, LEAD_LABELS)
    ax.set_ylim(0.18, 1.02)
    ax.yaxis.set_major_formatter(PCT)
    ax.set_xlabel("Тухайн мөчид хэдэн оноогоор тэргүүлж байсан")
    ax.set_ylabel("Тэргүүлж байсан баг ялсан хувь")
    ax.legend(frameon=False, loc="lower right", title="Аль мөчид тэргүүлж байсан")
    half = ls[ls.checkpoint == "Хагас"].set_index("bin")
    return finish(fig, f"Хагаст 7–10 оноогоор тэргүүлсэн баг {half.loc['7–10', 'est']:.0%} ялдаг; "
                       f"1–3 оноо бол зоос шидэхтэй адил ({half.loc['1–3', 'est']:.0%})",
                  "Цэг = тэр хэмжээгээр тэргүүлсэн багуудын ялсан хувь, босоо зураас = 95% магадлалтай хүрээ. "
                  "Бараан шугам = тоглолтын хожуу үе: ижил зөрүү хожуу байх тусам найдвартай",
                  f"{PBP} · 2025–26 ба 2026–27 улирал", n=int(ls[ls.checkpoint == 'Хагас'].n.sum()),
                  unit="тоглолт (хагаст тэнцээгүй)", uncertainty_note="Хүрээ: Wilson-ийн арга; цөөн тоглолттой бүлгийн хүрээ өргөн")


def fig_comebacks(cb: pd.DataFrame):
    apply_style()
    fig, ax = plt.subplots(figsize=(6.3, 3.7))
    counts = cb.deficit.value_counts().sort_index()
    xs = np.arange(0, counts.index.max() + 1)
    ys = counts.reindex(xs, fill_value=0).to_numpy()
    ax.bar(xs, ys, color=np.where(xs >= 10, PALETTE["vermillion"], NEUTRAL), width=0.85)
    n10 = int((cb.deficit >= 10).sum())
    ci = wilson_ci(n10, len(cb))
    ax.text(10, ys.max() * 0.72, f"10+ оноогоор хоцорч\nбайгаад ялсан:\n{n10} тоглолт ({ci.est:.0%})",
            color=PALETTE["vermillion"], fontsize=8.5, fontweight="bold", va="top")
    ax.set_xlabel("Ялсан баг тоглолтын дундуур хамгийн ихдээ хэдэн оноогоор хоцорч байсан")
    ax.set_ylabel("Тоглолтын тоо")
    big = cb.deficit.max()
    return finish(fig, f"Ялсан багийн {ci.est:.0%} нь 10 ба түүнээс олон оноогоор хоцорч байгаад эргүүлсэн",
                  f"Багана = тийм хэмжээний хоцрогдлыг давж ялсан тоглолтын тоо; 0 = хэзээ ч хоцроогүй. Хамгийн том эргэлт "
                  f"{big} оноо. Ялсан багийн {cb.trailed_at_half.mean():.0%} нь хагаст хоцорч байсан",
                  f"{PBP} · 2025–26 ба 2026–27 улирал", n=int(len(cb)), unit="тоглолт",
                  uncertainty_note=f"10+ онооны эргэлтийн хувийн 95% магадлалтай хүрээ {ci.lo:.0%}–{ci.hi:.0%}")


def fig_distance_curve(dc: pd.DataFrame, league_pps: float):
    apply_style()
    fig, (ax, bx) = plt.subplots(2, 1, figsize=(6.3, 4.6), sharex=True, gridspec_kw={"height_ratios": [2.2, 1]})
    colors = np.where(dc.three_share > 0.5, PALETTE["vermillion"], PALETTE["blue"])
    ax.vlines(dc.mid, dc.lo, dc.hi, color=colors, lw=2.2, alpha=0.55)
    ax.plot(dc.mid, dc.pps, color=NEUTRAL, lw=1, zorder=1)
    ax.scatter(dc.mid, dc.pps, c=colors, s=34, zorder=3)
    ax.axhline(league_pps, color="black", lw=0.7, ls=":")
    ax.text(3.5, league_pps, f"бүх шидэлтийн дундаж {league_pps:.2f}", ha="center", va="bottom", fontsize=8)
    for a in (ax, bx):
        a.axvline(6.75, color=NEUTRAL, ls="--", lw=1)
    ax.text(6.8, ax.get_ylim()[1], " 3 онооны шугам", va="top", fontsize=8, color="#4D4D4D")
    ax.set_ylabel("Оноо / шидэлт")
    ax._qa_no_xlabel = True
    bx.bar(dc.mid, dc.n, width=(dc.hi_m.clip(upper=10) - dc.lo_m) * 0.9, color=colors, alpha=0.8)
    bx.set_ylabel("Шидэлтийн тоо")
    bx.set_xlabel("Сагснаас зай (м)")
    mid = dc[(dc.lo_m >= 2) & (dc.hi_m <= 6)]
    mid_pps = (mid.pps * mid.n).sum() / mid.n.sum()
    line3 = dc[dc.lo_m == 6.75].iloc[0]
    return finish(fig, f"Сагснаас 2–6 м-ийн шидэлт хамгийн үр ашиг муутай ({mid_pps:.2f} оноо); 3 онооны шугамын "
                       f"яг ард {line3.pps:.2f}",
                  "Дээр: зайн интервал бүрээс шидэхэд дунджаар хэдэн оноо авсан (цэнхэр = 2 оноо, улаан-улбар = 3 оноо; "
                  "босоо зураас = 95% магадлалтай хүрээ). Доор: тэр зайнаас хэдэн удаа шидсэн",
                  f"{SHOTS} · байршил бүртгэгдсэн тоглолтууд", n=int(dc.n.sum()), unit="шидэлт",
                  uncertainty_note="Хүрээг тоглолтуудыг 1000 удаа дахин сонгож тооцов; сүүлийн цэг = 8.5 м-ээс цааш бүх шидэлт")


def fig_assisted_share(a: pd.DataFrame):
    apply_style()
    fig, ax = plt.subplots(figsize=(6.3, 3.6))
    y = np.arange(len(ZONES))
    for imp in (False, True):
        d = a[a.is_import == imp].set_index("zone").reindex(ZONES)
        yy = y + (0.14 if imp else -0.14)
        ax.hlines(yy, d.lo, d.hi, color=IMPORT_COLORS[imp], lw=2.4, alpha=0.5)
        ax.scatter(d.est, yy, color=IMPORT_COLORS[imp], s=36, zorder=3, label=f"{IMPORT_LABELS[imp]} тоглогч")
        for xx, yv in zip(d.est, yy):
            ax.text(xx + 0.025, yv, f"{xx:.0%}", va="center", fontsize=8, color=IMPORT_COLORS[imp])
    ax.set_yticks(y, ZONES)
    ax.invert_yaxis()
    ax.set_xlim(0, 1.1)
    ax.xaxis.set_major_formatter(PCT)
    ax.set_xlabel("Оносон шидэлтийн хэдэн хувь нь дамжуулалтаас гарсан")
    ax.set_ylabel("Шидсэн бүс")
    ax.legend(frameon=False, loc="lower left")
    tot = a.groupby("is_import").apply(lambda g: (g.est * g.n).sum() / g.n.sum(), include_groups=False)
    corner = a[a.zone == "Булангийн 3"]
    c = (corner.est * corner.n).sum() / corner.n.sum()
    return finish(fig, f"Булангийн 3 онооны {c:.0%} нь дамжуулалтаас гардаг; гадаад тоглогч оноогоо илүү бие даан "
                       f"бүтээдэг ({tot[True]:.0%} vs {tot[False]:.0%})",
                  "Цэг = тухайн бүсээс оносон шидэлтийн дамжуулалттай хувь, шугам = 95% магадлалтай хүрээ. Баруун тийш = "
                  "хамтын тоглолтоос гарсан оноо, зүүн тийш = тоглогч өөрөө бүтээсэн",
                  f"{SHOTS} ба тоглолтын явцын бичлэг · байршил бүртгэгдсэн тоглолтууд", n=int(a.n.sum()), unit="оносон шидэлт",
                  uncertainty_note="Дамжуулалтын 87%-ийг л шидэлттэй нь холбож чадсан тул бодит хувь арай өндөр байж болно")


def _label_points(ax, xs, ys, labels, fontsize: float = 7) -> None:
    """Цэгийн шошгыг баруун/зүүн/дээр/доор 4 байрлалаас бусад шошго, цэгтэй давхцахгүйг нь сонгож тавина."""
    ax.figure.canvas.draw()
    pts = ax.transData.transform(np.c_[xs, ys]) * 72 / ax.figure.dpi  # дэлгэцийн цэг (pt)
    boxes = [(px - 7, py - 7, px + 7, py + 7) for px, py in pts]
    left, right = (v * 72 / ax.figure.dpi for v in (ax.bbox.x0, ax.bbox.x1))
    for (px, py), text in zip(pts, labels):
        w, h = 0.56 * fontsize * len(text), fontsize + 2
        options = [((10, 0), "left", (px + 10, py - h / 2, px + 10 + w, py + h / 2)),
                   ((-10, 0), "right", (px - 10 - w, py - h / 2, px - 10, py + h / 2)),
                   ((0, 12), "center", (px - w / 2, py + 12 - h / 2, px + w / 2, py + 12 + h / 2)),
                   ((0, -12), "center", (px - w / 2, py - 12 - h / 2, px + w / 2, py - 12 + h / 2))]

        def overlap(b):
            outside = b[0] < left or b[2] > right  # тэнхлэгээс гарсан шошгыг хамгийн муу сонголт гэж үзнэ
            return 10 * outside + sum(not (b[2] < o[0] or o[2] < b[0] or b[3] < o[1] or o[3] < b[1]) for o in boxes)

        off, ha, box = min(options, key=lambda o: overlap(o[2]))
        boxes.append(box)
        ax.annotate(text, xy=ax.transData.inverted().transform((px * ax.figure.dpi / 72, py * ax.figure.dpi / 72)),
                    xytext=off, textcoords="offset points", ha=ha, va="center", fontsize=fontsize)


def fig_off_def(tr: pd.DataFrame):
    apply_style()
    seasons = sorted(tr.season.unique())
    fig, axes = plt.subplots(len(seasons), 1, figsize=(6.3, 3.3 * len(seasons) + 0.6))
    for ax, season in zip(np.atleast_1d(axes), seasons):
        d = tr[tr.season == season].sort_values("drtg")
        mx, my = d.ortg.mean(), d.drtg.mean()
        ax.axvline(mx, color=NEUTRAL, lw=0.8, ls="--")
        ax.axhline(my, color=NEUTRAL, lw=0.8, ls="--")
        ax.scatter(d.ortg, d.drtg, s=40 + 160 * d.win, c=d.win, cmap="RdBu", vmin=0.1, vmax=0.9, edgecolor="black",
                   linewidth=0.5, zorder=3)
        ax.set_xlim(d.ortg.min() - 3.5, d.ortg.max() + 3.5)
        ax.set_ylim(d.drtg.max() + 1.8, d.drtg.min() - 1.8)  # дээшээ = сайн хамгаалалт (бага оноо алдсан)
        _label_points(ax, d.ortg.to_numpy(), d.drtg.to_numpy(), [f"{t} {w:.0%}" for t, w in zip(d.team, d.win)])
        ax.set_title(f"{_season(season)} улирал", fontsize=9.5, loc="left")
        ax.set_xlabel("Довтолгоо: 100 довтолгоонд авсан оноо (баруун тийш = сайн)")
        ax.set_ylabel("Хамгаалалт: алдсан оноо\n(дээшээ = сайн)")
    r = float(np.corrcoef(tr.ortg - tr.drtg, tr.win)[0, 1])
    best = tr.assign(net=tr.ortg - tr.drtg).sort_values("net").iloc[-1]
    return finish(fig, f"{best.team} ({_season(best.season)}) 100 довтолгоонд {best.net:+.1f} оноогоор хамгийн давуу; "
                       f"энэ зөрүү ялалттай {r:.2f} хамааралтай",
                  "Тойрог бүр 1 баг: баруун тийш = сайн довтолгоо, дээшээ = сайн хамгаалалт. Тойрог том, цэнхэр = өндөр "
                  "ялалтын хувь (нэрийн ард бичсэн); тасархай шугам = тухайн улирлын дундаж",
                  f"{source_mba()} · үндсэн шатны тоглолтын хайрцаг оноо", n=int(len(tr)), unit="баг-улирал",
                  uncertainty_note="Довтолгооны тоог хайрцаг онооноос тооцоолсон (шидэлт − довт. самбар + бөмбөг алдалт "
                                   "+ 0.44 × торгууль); 2026–27 улирал дуусаагүй")


def fig_usage_efficiency(u: pd.DataFrame):
    apply_style()
    fig, ax = plt.subplots(figsize=(6.3, 4.2))
    for imp in (False, True):
        d = u[u.is_import.astype(bool) == imp]
        ax.scatter(d.usage, d.ts, s=10 + d.minutes / 25, color=IMPORT_COLORS[imp], alpha=0.65, linewidths=0,
                   label=f"{IMPORT_LABELS[imp]} тоглогч")
    mu, mt = u.usage.median(), u.ts.median()
    ax.axvline(mu, color=NEUTRAL, lw=0.8, ls="--")
    ax.axhline(mt, color=NEUTRAL, lw=0.8, ls="--")
    stars = u[(u.usage > mu) & (u.ts > mt)].assign(score=lambda d: d.usage * d.ts).nlargest(6, "score")
    for r in stars.itertuples():
        ax.annotate(r.name, (r.usage, r.ts), xytext=(0, 6), textcoords="offset points", fontsize=7, ha="center")
    ax.xaxis.set_major_formatter(PCT)
    ax.yaxis.set_major_formatter(PCT)
    ax.set_xlabel("Довтолгооны ачаалал (талбай дээр байхдаа багийн довтолгооны хэдийг дуусгадаг)")
    ax.set_ylabel("Шидэлтийн оновч")
    ax.legend(frameon=False, loc="lower right")
    med = u.groupby(u.is_import.astype(bool))[["usage", "ts"]].median()
    return finish(fig, f"Гадаад тоглогч довтолгооны {med.loc[True, 'usage']:.0%}-ийг дуусгадаг (дотоод {med.loc[False, 'usage']:.0%}) "
                       f"атлаа оновч нь өндөр ({med.loc[True, 'ts']:.0%} vs {med.loc[False, 'ts']:.0%})",
                  "Цэг бүр 1 тоглогч-улирал, том цэг = олон минут. Баруун дээд булан = ачаалал ихтэй мөртлөө оновчтой "
                  "(хамгийн үнэ цэнтэй); тасархай шугам = голч утга",
                  f"{source_mba()} · үндсэн шат, 200-аас олон минут тоглосон", n=int(len(u)), unit="тоглогч-улирал",
                  uncertainty_note="Ачаалал = (шидэлт + 0.44 × торгууль + бөмбөг алдалт)-ыг багийн нийлбэрт харьцуулж, "
                                   "тоглосон минутаар жинлэсэн")


def fig_stability(st: pd.DataFrame):
    apply_style()
    d = st.sort_values("r").reset_index(drop=True)
    fig, ax = plt.subplots(figsize=(6.3, 3.6))
    eff = d.stat.isin(["ts_pct", "tp_pct"])
    colors = np.where(eff, PALETTE["vermillion"], PALETTE["blue"])
    y = np.arange(len(d))
    ax.hlines(y, d.lo, d.hi, color=colors, lw=2.6, alpha=0.5)
    ax.scatter(d.r, y, c=colors, s=38, zorder=3)
    ax.axvline(0, color="black", lw=0.7)
    ax.set_yticks(y, [f"{lab} ({n})" for lab, n in zip(d.label, d.n)], fontsize=8.5)
    ax.set_xlim(-0.5, 1)
    ax.set_xlabel("Хоёр улирлын хамаарлын хүч (0 = холбоогүй, 1 = ижил)")
    ax.set_ylabel("Үзүүлэлт (тоглогчийн тоо)")
    style, effi = d[~eff], d[eff]
    return finish(fig, f"Тоглогчийн хэв маяг улирлаас улиралд хадгалагддаг ({style.r.min():.2f}–{style.r.max():.2f}), "
                       f"оновч хадгалагддаггүй ({effi.r.mean():.2f})",
                  "Цэг = нэг тоглогчийн өмнөх ба энэ улирлын үзүүлэлт хэр төстэй вэ, шугам = 95% магадлалтай хүрээ. "
                  "Цэнхэр = хэв маяг, тоглох хэмжээ; улаан-улбар = оновч. Хүрээ 0-ийг дайрвал холбоо батлагдаагүй",
                  f"{source_mba()} · 2025–26 ба 2026–27 улиралд хоёуланд нь тоглосон", n=int(d.n.max()), unit="тоглогч",
                  uncertainty_note="Улирал бүрт 50-аас олон шидэлт (3 онооны оновчид 30-аас олон 3 онооны шидэлт) хийсэн "
                                   "тоглогчид; хүрээ: Fisher-ийн арга; 2026–27 улирал дуусаагүй")
