import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from src.style import NEUTRAL, PALETTE, apply_style, finish, source_mba

VERDICT_COLORS = {"Дэмжигдсэн": PALETTE["green"], "Дэмжигдээгүй": PALETTE["vermillion"], "Тодорхойгүй": NEUTRAL}
VERDICT_PLAIN = {"Дэмжигдсэн": "Батлагдсан", "Дэмжигдээгүй": "Няцаагдсан", "Тодорхойгүй": "Баттай биш"}
UNITS = {"H1": "Голч онооны зөрүү (гадаад − дотоод), оноо", "H2": "Гэрийн багийн ялалтын хувь",
         "H3": "Оновчийн нөлөө бусад хүчин зүйлээс хэр илүү", "H4": "Хамаарлын хүч (өндөр ба самбар)",
         "H5": "Онооны тайлбарлах хувь (0.5 = тал)"}
COL_LABELS = {"position": "Байрлал", "height_cm": "Өндөр", "birth_year": "Төрсөн он", "FT_pct": "Торгуулийн оновч",
              "TP_pct": "3 онооны оновч", "FGA": "Шидэлтийн тоо"}


def verdict(row: pd.Series) -> str:
    if row.ci_lo > row.null_value and row.estimate > row.null_value:
        return "Дэмжигдсэн"
    if row.ci_hi < row.null_value:
        return "Дэмжигдээгүй"
    return "Тодорхойгүй"


def fig_hypothesis_summary(hyp: pd.DataFrame):
    apply_style()
    hyp = hyp.sort_values("hid").reset_index(drop=True)
    fig, axes = plt.subplots(len(hyp), 1, figsize=(6.3, 1.05 * len(hyp) + 1.4))
    axes = np.atleast_1d(axes)
    verdicts = []
    for ax, r in zip(axes, hyp.itertuples()):
        v = verdict(pd.Series(r._asdict()))
        verdicts.append(v)
        color = VERDICT_COLORS[v]
        ax.hlines(0, r.ci_lo, r.ci_hi, color=color, linewidth=4, alpha=0.5)
        ax.scatter([r.estimate], [0], color=color, s=40, zorder=3)
        ax.axvline(r.null_value, color="black", linestyle="--", linewidth=0.8)
        span = max(r.ci_hi, r.null_value) - min(r.ci_lo, r.null_value)
        ax.set_xlim(min(r.ci_lo, r.null_value) - 0.15 * span, max(r.ci_hi, r.null_value) + 0.15 * span)
        ax.set_yticks([])
        ax.grid(axis="y", visible=False)
        ax.spines["left"].set_visible(False)
        ax.set_title(f"{r.hid}: {r.statement}", fontsize=9, loc="left")
        ax.set_xlabel(UNITS.get(r.hid, "Утга"), fontsize=8)
        ax.text(1.01, 0.5, VERDICT_PLAIN[v], transform=ax.transAxes, color=color, fontweight="bold", fontsize=9, va="center")
        ax._qa_no_ylabel = True
    n_yes = verdicts.count("Дэмжигдсэн")
    others = [h for h, v in zip(hyp.hid, verdicts) if v != "Дэмжигдсэн"]
    title = f"{len(hyp)} таамаглалын {n_yes} нь датагаар батлагдсан" + (f"; {', '.join(others)} батлагдаагүй" if others else "")
    return finish(fig, title,
                  "Цэг = датаас гарсан утга, өнгөт зурвас = бодит утга байж болох 95% хүрээ, тасархай = «нөлөөгүй» "
                  "үеийн утга. Зурвас бүхэлдээ тасархайн баруун талд байвал таамаглал батлагдана",
                  "MBA статистик (2025–27), Wikipedia (2023–24)", n=int(len(hyp)), unit="таамаглал",
                  uncertainty_note="Хүрээг таамаглал бүрт тохирох статистик аргаар тооцов (арга зүйг тайлангаас үзнэ үү)")


def fig_data_quality(missing: pd.DataFrame, matches: pd.DataFrame, ppg_val: pd.DataFrame):
    apply_style()
    fig, (a, b, c) = plt.subplots(1, 3, figsize=(6.3, 3.4), gridspec_kw={"width_ratios": [1.25, 1, 1]})
    m = missing.sort_values("pct_missing")
    a.barh([COL_LABELS.get(x, x) for x in m.column], m.pct_missing, color=PALETTE["blue"])
    a.set_xlabel("Дутуу, %")
    a.set_title("Дутуу утга", fontsize=9.5)
    a._qa_no_ylabel = True
    relinked = matches[matches.left_id != matches.right_id]
    b.hist(relinked.score, bins=np.linspace(0.85, 1.0, 7), color=PALETTE["blue"], edgecolor="white")
    b.set_xlabel("Нэрийн төстэй байдал")
    b.set_ylabel("Тоглогчийн тоо")
    b.set_title(f"Нэр холбосон: {len(relinked)}", fontsize=9.5)
    diff = ppg_val["diff"].dropna()
    c.hist(np.clip(diff, 0, 1.0), bins=np.arange(0, 1.051, 0.05), color=NEUTRAL, edgecolor="white")
    c.set_yscale("symlog", linthresh=10)
    c.axvline(0.2, color=PALETTE["vermillion"], linestyle="--", linewidth=1)
    if (diff > 1).any():
        c.text(0.98, 0.9, f"> 1: {int((diff > 1).sum())}", transform=c.transAxes, ha="right", fontsize=8)
    c.set_xlabel("Зөрүү (оноо)")
    c.set_ylabel("Тоглогч")
    c.set_title(f"Оноо тулгалт: {int(ppg_val.flag.sum())} зөрүү", fontsize=9.5)
    worst = missing.loc[missing.pct_missing.idxmax()]
    return finish(fig, f"Өгөгдөл бараг бүрэн: хамгийн их дутуу нь {COL_LABELS.get(worst.column, worst.column)} "
                  f"({worst.pct_missing:.0f}%)", "Зүүн: үзүүлэлт бүрийн дутуу хувь. Дунд: өөр улиралд нэр нь бага зэрэг "
                  "өөр бичигдсэн тоглогчийг холбосон (1 = нэр яг ижил). Баруун: сайтын нэгтгэсэн оноо ба тоглолт бүрийн "
                  "онооны нийлбэрийн зөрүү",
                  source_mba(), n=int(len(ppg_val)), unit="тоглогч-улирал",
                  uncertainty_note="Улаан тасархай = зөвшөөрөх хязгаар 0.2 оноо")
