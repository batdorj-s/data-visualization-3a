"""Гадаад тоглогч ба тоглогч солилцооны график: ирэх зам, үлдэлт, байрлал, нас, таамаглалын хураангуй."""
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from src.import_sources import LEVELS
from src.style import IMPORT_COLORS, NEUTRAL, PALETTE, apply_style, finish, source_mba
from src.charts.summary import VERDICT_COLORS

SHAM = "ShamSports-ийн тоглогчийн карьерын хуудас"
VERDICT_KEY = {"Батлагдсан": "Дэмжигдсэн", "Няцаагдсан": "Дэмжигдээгүй", "Баттай биш": "Тодорхойгүй"}
LEVEL_COLORS = dict(zip(LEVELS, ["#08306B", PALETTE["blue"], PALETTE["sky"], "#9ECAE1", "#D9D9D9"]))
LEAGUE_MN = {"Mexico": "Мексик", "G League": "G League (АНУ)", "Greece": "Грек", "China": "Хятад", "Poland": "Польш",
             "Israel": "Израиль", "Spain": "Испани", "Lithuania": "Литва", "Hungary": "Унгар", "South Korea": "Өмнөд Солонгос",
             "Basketball Africa League": "Африкийн лиг", "Europe Cup": "Европын цом", "France": "Франц", "Turkey": "Турк",
             "Italy": "Итали", "Britain": "Их Британи", "Romania": "Румын", "Kosovo": "Косово", "Japan": "Япон",
             "Philippines": "Филиппин", "Australia": "Австрали", "Finland": "Финланд", "Belgium": "Бельги"}


def fig_import_pipeline(background: pd.DataFrame, n_persons: int):
    apply_style()
    f = background[background.status == "олдсон"]
    fig, (a, b) = plt.subplots(1, 2, figsize=(6.3, 3.9), gridspec_kw={"width_ratios": [1, 1.1]})
    lv = f.level.value_counts().reindex(LEVELS, fill_value=0)
    y = np.arange(len(lv))
    a.barh(y, lv.to_numpy(), color=[LEVEL_COLORS[l] for l in lv.index], height=0.65)
    for yy, v in zip(y, lv.to_numpy()):
        a.text(v + 0.3, yy, str(int(v)), va="center", fontsize=8.5)
    a.set_yticks(y, lv.index, fontsize=8.5)
    a.invert_yaxis()
    a.set_xlabel("Тоглогчийн тоо")
    a.set_title("Өмнө тоглосон хамгийн өндөр түвшин", fontsize=9.5, loc="left")
    a._qa_no_ylabel = True
    last = f.last_league.dropna().map(lambda x: LEAGUE_MN.get(x, x)).value_counts()
    top = last.head(8)
    if len(last) > 8:
        top = pd.concat([top, pd.Series({"Бусад": int(last.iloc[8:].sum())})])
    yb = np.arange(len(top))
    b.barh(yb, top.to_numpy(), color=[PALETTE["vermillion"] if i == 0 else NEUTRAL for i in range(len(top))], height=0.65)
    for yy, v in zip(yb, top.to_numpy()):
        b.text(v + 0.15, yy, str(int(v)), va="center", fontsize=8.5)
    b.set_yticks(yb, top.index, fontsize=8.5)
    b.invert_yaxis()
    b.set_xlabel("Тоглогчийн тоо")
    b.set_title("Ирэхийн өмнөх сүүлийн лиг", fontsize=9.5, loc="left")
    b._qa_no_ylabel = True
    usa = int(f.nationality.fillna("").str.contains("USA").sum())
    return finish(fig, f"Олдсон гадаад тоглогчдын {usa}/{len(f)} нь АНУ-ын иргэн; хамгийн олон нь {top.index[0]}-ээс ирсэн",
                  f"Зүүн: ирэхээсээ өмнө тоглож байсан хамгийн өндөр лиг. Баруун: Монголд ирэхийн өмнөх сүүлийн мэргэжлийн лиг. "
                  f"{len(f)} тоглогч ({len(f) / n_persons:.0%})-ийн карьерыг эх сурвалжаар баталгаажуулсан",
                  f"{SHAM}; MBA тоглогчийн профайлтай төрсөн он/өндрөөр тулгасан", n=int(len(f)), unit="гадаад тоглогч",
                  uncertainty_note=f"Үлдсэн {n_persons - len(f)} тоглогч (ихэнх нь Азийн квотын) эх сурвалжид олдоогүй тул "
                                   "дүр зураг АНУ-ын тоглогч руу хазайсан байж болно")


def fig_import_retention(cmp: pd.DataFrame, n_stayed: int, n_total: int):
    apply_style()
    fig, axes = plt.subplots(1, len(cmp), figsize=(6.3, 3.2))
    for ax, r in zip(np.atleast_1d(axes), cmp.itertuples()):
        pct = r.metric in ("usage", "ts_pct")
        for yy, (med, lo, hi, color, lab) in enumerate([(r.med_no, r.lo_no, r.hi_no, NEUTRAL, "Явсан"),
                                                        (r.med_yes, r.lo_yes, r.hi_yes, PALETTE["vermillion"], "Үлдсэн")]):
            ax.hlines(yy, lo, hi, color=color, lw=3, alpha=0.6)
            ax.scatter(med, yy, color=color, s=40, zorder=3)
            ax.text(med, yy + 0.22, f"{med:.0%}" if pct else f"{med:.1f}", ha="center", fontsize=7.5, color=color)
        ax.set_yticks([0, 1], ["Явсан", "Үлдсэн"] if ax is np.atleast_1d(axes)[0] else ["", ""])
        ax.set_ylim(-0.5, 1.6)
        ax.set_title(r.label, fontsize=8.5)
        ax.set_xlabel("✓ баттай ялгаатай" if r.clear else "ялгаа баттай биш", fontsize=7.5,
                      color=PALETTE["green"] if r.clear else "#6B6B6B")
        if pct:
            ax.xaxis.set_major_formatter(plt.FuncFormatter(lambda v, _: f"{v:.0%}"))
        ax.tick_params(axis="x", labelsize=7)
        ax.grid(axis="y", visible=False)
        ax._qa_no_ylabel = True
    ppg = cmp.set_index("metric").loc["PPG"]
    return finish(fig, f"Дараа улиралд үлдсэн {n_stayed} гадаад тоглогч голчоор {ppg.med_yes:.1f} оноо авч байсан "
                       f"(явсан нь {ppg.med_no:.1f}), гэхдээ ялгаа баттай биш",
                  f"2025–26 улирлын {n_total} гадаад тоглогчоос дараа улиралд MBA-д (аль ч багт) үлдсэн ба явсныг харьцуулав. "
                  "Цэг = голч утга, шугам = 95% магадлалтай хүрээ; хүрээ давхцаж байвал ялгааг баттай гэж хэлж чадахгүй",
                  f"{source_mba()} · 2025–26 ба 2026–27 улирал, 5+ тоглолт тоглосон", n=int(n_total), unit="гадаад тоглогч",
                  uncertainty_note="Хүрээг тоглогчдыг 2000 удаа дахин сонгож тооцов; үлдсэн тоглогч цөөн (8) тул хүрээ өргөн. "
                                   "Гэрээний мэдээлэл нийтэд ил биш тул «үлдсэн» = дараа улирлын статистикт гарсан")


def fig_import_position(pm: pd.DataFrame, conc: pd.DataFrame):
    apply_style()
    order = ["PG", "SG", "SF", "PF", "C"]
    seasons = sorted(pm.season.unique())
    fig, ax = plt.subplots(figsize=(6.3, 3.7))
    x = np.arange(len(order))
    w = 0.38
    colors = ["#FDCC8A", IMPORT_COLORS[True]]
    for k, season in enumerate(seasons):
        d = pm[pm.season == season].set_index("position").reindex(order)
        xs = x + (k - 0.5) * w
        ax.bar(xs, d.share, width=w, color=colors[k], label=season.replace("-20", "–"))
        for xx, v in zip(xs, d.share):
            ax.text(xx, v + 0.01, f"{v:.0%}", ha="center", fontsize=7.5)
        ov = conc.set_index("season").loc[season, "overall_share"]
        ax.hlines(ov, -0.5, len(order) - 0.5, color=colors[k], ls="--", lw=1.1)
        ax.text(len(order) - 0.45, ov, f"нийт {ov:.0%}", va="center", fontsize=7.5, color="#4D4D4D")
    ax.set_xticks(x, ["Тоглуулагч\n(PG)", "Шидэгч хамг.\n(SG)", "Жижиг довт.\n(SF)", "Хүчит довт.\n(PF)", "Төвийн\n(C)"])
    ax.set_ylim(0, 0.85)
    ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda v, _: f"{v:.0%}"))
    ax.set_xlabel("Байрлал")
    ax.set_ylabel("Минутын гадаад хувь")
    ax.legend(frameon=False, loc="upper center", ncol=2, title="Улирал", bbox_to_anchor=(0.42, 1.02))
    c = conc.set_index("season")
    last = seasons[-1]
    excess = ", ".join(f"{s.replace('-20', '–')}: {r['diff']:+.0%} ({r.lo:+.0%}…{r.hi:+.0%})" for s, r in c.iterrows())
    return finish(fig, f"{last.replace('-20', '–')}-д төвийн байрлалын минутын {c.loc[last, 'pos_share']:.0%}-ийг гадаад тоглогч "
                       f"тоглосон (нийт минутын {c.loc[last, 'overall_share']:.0%})",
                  "Багана = тухайн байрлалд тоглосон нийт минутын хэдэн хувийг гадаад тоглогч эзэлсэн; тасархай шугам = бүх "
                  "байрлалын дундаж. Шугамаас дээш байвал багууд тэр байрлалд гадаад тоглогчид түлхүү найддаг",
                  f"{source_mba()} · байрлал нь MBA-ийн тоглогчийн профайлаас", n=int(len(pm)), unit="байрлал-улирал",
                  uncertainty_note=f"Төвийн байрлалын илүүдэл (95% хүрээ, тоглогчоор дахин түүвэрлэсэн) — {excess}")


def fig_import_age(imports: pd.DataFrame, age: dict):
    apply_style()
    d = imports.dropna(subset=["age", "PPG"])
    fig, ax = plt.subplots(figsize=(6.3, 3.9))
    for lvl, color in list(LEVEL_COLORS.items()) + [("Тодорхойгүй", "#F0F0F0")]:
        part = d[d.level == lvl]
        if len(part):
            ax.scatter(part.age, part.PPG, s=18 + part.MIN * 1.2, color=color, edgecolor="#4D4D4D", linewidth=0.5,
                       alpha=0.9, label=f"{lvl} ({len(part)})", zorder=3)
    slope, icpt = np.polyfit(d.age, d.PPG, 1)
    xs = np.linspace(d.age.min(), d.age.max(), 20)
    ax.plot(xs, icpt + slope * xs, color="black", lw=1.2)
    ax.set_xlabel("Нас (тухайн улирал эхлэхэд)")
    ax.set_ylabel("Оноо / тоглолт (MBA)")
    ax.legend(frameon=False, fontsize=7, loc="upper left", bbox_to_anchor=(1.01, 1.0), title="Өмнөх хамгийн\nөндөр түвшин",
              title_fontsize=7.5, markerscale=0.7)
    return finish(fig, f"Ахимаг гадаад тоглогч MBA-д илүү оноо авдаг: нас 1 жилээр ахих тусам +{slope:.1f} оноо",
                  "Цэг бүр 1 гадаад тоглогч-улирал, том цэг = олон минут, өнгө = ирэхээсээ өмнө тоглосон хамгийн өндөр лиг. "
                  "Хар шугам = ерөнхий чиг хандлага. Ахимаг тоглогч илүү олон минут тоглодог тул шалтгаан нь туршлага, "
                  "үүрэг хоёр холилдсон байж болно",
                  f"{source_mba()}; нас ба түвшин — {SHAM}", n=int(age["n"]), unit="гадаад тоглогч-улирал",
                  uncertainty_note=f"Хамаарлын хүч {age['r']:.2f} (95% хүрээ {age['lo']:.2f}–{age['hi']:.2f}, Fisher-ийн арга)")


def fig_import_hypotheses(h: pd.DataFrame):
    apply_style()
    fig, axes = plt.subplots(len(h), 1, figsize=(6.3, 0.95 * len(h) + 1.3))
    for ax, r in zip(np.atleast_1d(axes), h.itertuples()):
        color = VERDICT_COLORS[VERDICT_KEY[r.verdict]]
        ax.hlines(0, r.lo, r.hi, color=color, lw=4, alpha=0.5)
        ax.scatter([r.estimate], [0], color=color, s=40, zorder=3)
        ax.axvline(0, color="black", ls="--", lw=0.8)
        span = max(abs(r.lo), abs(r.hi), 1e-6)
        ax.set_xlim(-1.25 * span, 1.25 * span)
        ax.set_yticks([])
        ax.grid(axis="y", visible=False)
        ax.spines["left"].set_visible(False)
        ax.set_title(f"{r.hid}: {r.statement}", fontsize=8.5, loc="left")
        pct = r.hid == "H8"
        ax.set_xlabel(f"{r.measure} ({r.n})", fontsize=7.5)
        if pct:
            ax.xaxis.set_major_formatter(plt.FuncFormatter(lambda v, _: f"{v:+.0%}"))
        ax.text(1.01, 0.5, r.verdict, transform=ax.transAxes, color=color, fontweight="bold", fontsize=8.5, va="center")
        ax._qa_no_ylabel = True
    n_yes = int((h.verdict == "Батлагдсан").sum())
    return finish(fig, f"Гадаад тоглогчийн {len(h)} шалгалтын {n_yes} нь датаар батлагдсан",
                  "Цэг = датаас гарсан утга, өнгөт зурвас = 95% магадлалтай хүрээ, тасархай = «ялгаагүй» үеийн утга (0). "
                  "Зурвас бүхэлдээ 0-ээс баруун тийш байвал таамаглал батлагдана",
                  f"{source_mba()}; гарал үүсэл — {SHAM}", n=int(len(h)), unit="шалгалт",
                  uncertainty_note="Хүрээ: тоглогчоор дахин түүвэрлэх (H6–H8), Fisher-ийн арга (H9); дата цөөн тул хүрээ өргөн")
