"""Санал болгож буй шийдэл "MBA Scout"-ийн зураг төсөл: архитектур ба 2 wireframe (spec §10)."""
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch  # noqa: E402

from src.palette import IMPORT_COLORS, LIGHT, NEUTRAL, PALETTE  # noqa: E402
from src.style import apply_style  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "report" / "blueprint"


def _box(ax, x, y, w, h, text, color, fontsize=8, text_color="black", alpha=0.18, bold=False):
    ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.01,rounding_size=0.015",
                                facecolor=color, alpha=alpha, edgecolor=color, linewidth=1.2))
    ax.text(x + w / 2, y + h / 2, text, ha="center", va="center", fontsize=fontsize, color=text_color,
            fontweight="bold" if bold else "normal", wrap=True)


def _arrow(ax, a, b, color="#4D4D4D"):
    ax.add_patch(FancyArrowPatch(a, b, arrowstyle="-|>", mutation_scale=12, color=color, linewidth=1.2))


def _canvas(title: str, subtitle: str, size=(6.3, 4.2)):
    apply_style()
    fig, ax = plt.subplots(figsize=size)
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.axis("off")
    fig.suptitle(title, x=0.02, ha="left", fontsize=11, fontweight="bold")
    fig.text(0.02, 0.905, subtitle, fontsize=8, color="#4D4D4D")
    return fig, ax


def _save(fig, out_dir: Path, name: str) -> Path:
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    png = out_dir / f"{name}.png"
    fig.savefig(png, dpi=300, metadata={"Software": None})
    fig.savefig(out_dir / f"{name}.svg", metadata={"Date": None})
    plt.close(fig)
    return png


def draw_architecture(out_dir: Path = OUT) -> Path:
    fig, ax = _canvas("MBA Scout: санал болгож буй системийн архитектур",
                      "Энэ төслийн pipeline-ийг клубуудад зориулсан өдөр бүр шинэчлэгддэг үйлчилгээ болгох")
    blue, green, orange, verm = PALETTE["blue"], PALETTE["green"], PALETTE["orange"], PALETTE["vermillion"]
    _box(ax, 0.02, 0.62, 0.17, 0.18, "MBA\nстатистикийн\nсистем", NEUTRAL, bold=True)
    _box(ax, 0.02, 0.36, 0.17, 0.18, "Wikipedia /\nFIBA", NEUTRAL, bold=True)
    _box(ax, 0.02, 0.12, 0.17, 0.18, "Клубын\nбичлэг\n(ирээдүйд)", NEUTRAL)
    _box(ax, 0.26, 0.44, 0.17, 0.30, "Scraper\n(кэш, 1 с\nзавсар,\nrobots.txt)", blue)
    _box(ax, 0.48, 0.44, 0.17, 0.30, "Цэвэрлэгээ +\nfeature\n(C1–C12,\nFour Factors,\nElo)", blue)
    _box(ax, 0.70, 0.62, 0.13, 0.18, "Архетип\n(K-Means)", green)
    _box(ax, 0.70, 0.40, 0.13, 0.18, "Ялалтын\nмагадлал", green)
    _box(ax, 0.70, 0.18, 0.13, 0.18, "Тодорхой бус\nбайдал\n(bootstrap)", green)
    _box(ax, 0.87, 0.52, 0.12, 0.28, "Dashboard\n(Streamlit)", orange, bold=True)
    _box(ax, 0.87, 0.18, 0.12, 0.28, "Тоглолтын\nөмнөх PDF\nтайлан", orange)
    _box(ax, 0.26, 0.12, 0.39, 0.16, "Өдөр бүр 06:00 cron →\nsnapshot + өгөгдлийн чанарын шалгалт (C10)", verm, fontsize=7)
    for y in (0.71, 0.45):
        _arrow(ax, (0.19, y), (0.26, 0.59))
    _arrow(ax, (0.19, 0.30), (0.26, 0.47))
    _arrow(ax, (0.43, 0.59), (0.48, 0.59))
    for y in (0.71, 0.49, 0.27):
        _arrow(ax, (0.65, 0.59), (0.70, y))
        _arrow(ax, (0.83, y), (0.87, 0.66 if y > 0.4 else 0.32))
    _arrow(ax, (0.45, 0.26), (0.45, 0.44))
    return _save(fig, out_dir, "architecture")


def _frame(ax, x, y, w, h, title):
    ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.005", facecolor="white", edgecolor=LIGHT, linewidth=1))
    ax.text(x + 0.01, y + h - 0.03, title, fontsize=7.5, fontweight="bold", va="top")


def draw_wireframe_scout(out_dir: Path = OUT) -> Path:
    fig, ax = _canvas("Wireframe 1: Скаутын хайлт", "Дасгалжуулагч багтаа дутагдаж буй архетипийн тоглогчийг олох")
    _frame(ax, 0.02, 0.05, 0.25, 0.80, "Шүүлтүүр")
    for i, label in enumerate(["Архетип: зохион байгуулагч", "Байрлал: PG, SG", "Нас ≤ 25", "Дотоод тоглогч",
                               "GP ≥ 10", "[Хайх]"]):
        _box(ax, 0.04, 0.70 - i * 0.11, 0.21, 0.07, label, PALETTE["blue"] if i == 5 else NEUTRAL, fontsize=6)
    _frame(ax, 0.30, 0.45, 0.68, 0.40, "Архетипийн газрын зураг (PCA) — цайвар цэг = бүлгийн заагт")
    import numpy as np
    rng = np.random.default_rng(1)
    for c, (cx, cy) in zip([PALETTE["vermillion"], PALETTE["blue"], PALETTE["green"]], [(0.45, 0.6), (0.65, 0.7), (0.85, 0.58)]):
        ax.scatter(cx + rng.normal(0, 0.04, 25), cy + rng.normal(0, 0.035, 25), s=8, color=c, alpha=0.7)
    ax.scatter([0.66], [0.69], marker="*", s=120, color="black")
    _frame(ax, 0.30, 0.05, 0.68, 0.36, "Төстэй 5 тоглогч — карт бүр CI-тай")
    for i in range(5):
        _box(ax, 0.32 + i * 0.132, 0.09, 0.12, 0.24, f"Тоглогч {i + 1}\nPPG 12.4\n[10.1–14.6]\nTS% 56%",
             IMPORT_COLORS[False], fontsize=6)
    return _save(fig, out_dir, "wireframe_scout")


def draw_wireframe_pregame(out_dir: Path = OUT) -> Path:
    fig, ax = _canvas("Wireframe 2: Тоглолтын өмнөх тайлан", "Хоёр багийн хүчин зүйл, магадлал ба сүүлийн хэлбэр")
    _frame(ax, 0.02, 0.55, 0.46, 0.30, "Ялах магадлал")
    for i in range(20):
        ax.scatter(0.06 + (i % 10) * 0.04, 0.70 - (i // 10) * 0.07, s=60,
                   color=PALETTE["blue"] if i < 13 else PALETTE["vermillion"])
    ax.text(0.06, 0.585, "А баг 65% (95% CI 55–74%)", fontsize=7)
    _frame(ax, 0.52, 0.55, 0.46, 0.30, "Four Factors: А vs Б")
    for i, (lab, a, b) in enumerate([("eFG%", 0.8, 0.6), ("TOV%", 0.5, 0.7), ("ORB%", 0.6, 0.5), ("FTr", 0.4, 0.55)]):
        y = 0.76 - i * 0.05
        ax.text(0.54, y, lab, fontsize=6.5, va="center")
        ax.barh(y + 0.01, a * 0.3, height=0.018, left=0.62, color=PALETTE["blue"])
        ax.barh(y - 0.01, b * 0.3, height=0.018, left=0.62, color=PALETTE["vermillion"])
    _frame(ax, 0.02, 0.05, 0.46, 0.45, "Сүүлийн 5 тоглолт (Elo явц)")
    ax.plot([0.06, 0.14, 0.22, 0.30, 0.38, 0.44], [0.20, 0.25, 0.22, 0.30, 0.34, 0.33], color=PALETTE["blue"])
    ax.plot([0.06, 0.14, 0.22, 0.30, 0.38, 0.44], [0.30, 0.27, 0.25, 0.22, 0.24, 0.21], color=PALETTE["vermillion"])
    _frame(ax, 0.52, 0.05, 0.46, 0.45, "Гол тоглогчид ба онооны төвлөрөл (Pareto)")
    for i, h in enumerate([0.25, 0.18, 0.12, 0.09, 0.06, 0.04]):
        ax.bar(0.58 + i * 0.06, h, width=0.045, bottom=0.10, color=NEUTRAL)
    return _save(fig, out_dir, "wireframe_pregame")


USER_STORIES = """# MBA Scout — хэрэглэгчийн хэрэгцээ ба зураг төсөл

## Хэрэглэгчийн хэрэгцээ (user stories)
- **Дасгалжуулагч:** Багтаа дутагдаж буй архетипийн (жишээ нь тоглолт зохион байгуулагч) дотоодын тоглогчийг олж, тэдний статистикийг итгэх интервалтай нь харьцуулмаар байна.
- **Скаут:** Цөөн тоглолттой тоглогчийн өндөр оновч жинхэнэ ур чадвар уу, эсвэл аз уу гэдгийг funnel графикаар ялгамаар байна.
- **MBA (холбоо):** Import тоглогчийн онооны хувь, багуудын тэнцвэрийг улирал бүр хянаж, квотын бодлогод ашигламаар байна.
- **Хөгжөөн дэмжигч / сэтгүүлч:** Тоглолтын өмнө хоёр багийн хүчин зүйл, ялах магадлалыг ойлгомжтой (20 цэгийн) хэлбэрээр харах.

## Архитектур
`architecture.png`: эх сурвалж → scraper (кэш, robots.txt) → цэвэрлэгээ/feature → загварууд → dashboard ба PDF тайлан; өдөр бүр cron.

## Wireframe
- `wireframe_scout.png` — скаутын хайлт: шүүлтүүр, архетипийн газрын зураг, төстэй 5 тоглогч.
- `wireframe_pregame.png` — тоглолтын өмнөх тайлан: магадлал (quantile dots), Four Factors, Elo явц, Pareto.

## Хязгаарлалт
- MBA-ийн систем 2025-26 улирлаас өмнөх тоглогчийн датагүй; 2023-24 улирал зөвхөн багийн түвшинд.
- Ялалтын загвар (~210 тоглолт) энгийн Elo baseline-аас баттай илүү биш.
- Зарим тоглогчийн Import шошго, багийн гэр хот эх сурвалжаар батлагдаагүй.

## Дараагийн алхам
- Play-by-play датагаар тоглогчийн хослол (lineup) ба +/- шинжилгээ.
- Улирал бүр шинэчлэгдэх загвар, багийн нэр солигдсон тохиолдлыг MBA-тай тулгах.
- Эмэгтэйчүүдийн лиг ба M хөгжлийн лигийг нэмэх.
"""


def write_user_stories(out_dir: Path = OUT) -> Path:
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    path = out_dir / "user_stories.md"
    path.write_text(USER_STORIES, encoding="utf-8")
    return path


if __name__ == "__main__":
    for fn in (draw_architecture, draw_wireframe_scout, draw_wireframe_pregame, write_user_stories):
        print(fn())
