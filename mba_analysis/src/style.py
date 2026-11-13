import re
import textwrap
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
from matplotlib import font_manager  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
WIDTH_IN = 16 / 2.54

from src.palette import IMPORT_COLORS, IMPORT_LABELS, LIGHT, NEUTRAL, PALETTE, POS_COLORS  # noqa: E402,F401


def apply_style() -> str:
    available = {f.name for f in font_manager.fontManager.ttflist}
    font = "Arial" if "Arial" in available else "DejaVu Sans"
    plt.rcParams.update({
        "font.family": font,
        "font.size": 9.5,
        "axes.titlesize": 10.5,
        "axes.labelsize": 9.5,
        "xtick.labelsize": 8.5,
        "ytick.labelsize": 8.5,
        "legend.fontsize": 8.5,
        "axes.labelcolor": "#333333",
        "xtick.color": "#4D4D4D",
        "ytick.color": "#4D4D4D",
        "axes.spines.top": False,
        "axes.spines.right": False,
        "axes.grid": True,
        "grid.color": "#EBEBEB",
        "grid.linewidth": 0.6,
        "axes.axisbelow": True,
        "savefig.dpi": 300,
        "figure.dpi": 100,
        "svg.fonttype": "none",
        "svg.hashsalt": "mba-analysis",
    })
    return font


def source_mba() -> str:
    snap = ROOT / "data" / "raw" / "SNAPSHOT.md"
    day = "2026-11-12"
    if snap.exists():
        m = re.search(r"Татсан огноо: (\d{4}-\d{2}-\d{2})", snap.read_text(encoding="utf-8"))
        day = m.group(1) if m else day
    return f"MBA лигийн албан ёсны статистик (mongolia.basketball), {day}-нд татсан"


def finish(fig, title: str, subtitle: str, source: str, n: int, uncertainty_note: str | None = None,
           unit: str | None = None):
    """Гарчиг (гол дүгнэлт), дэд гарчиг (хэрхэн унших), доод тайлбар (ямар дата, хэдэн ширхэг) нэмнэ."""
    width_in = fig.get_size_inches()[0]
    title_lines = textwrap.wrap(title, width=int(10.5 * width_in))
    sub_lines = textwrap.wrap(subtitle, width=int(14 * width_in))
    count = f"{n} {unit}" if unit else f"n = {n}"
    caption = f"Дата: {source} · {count}"
    if uncertainty_note:
        caption += f". {uncertainty_note}"
    cap_lines = textwrap.wrap(caption, width=int(17.5 * width_in))
    height_in = fig.get_size_inches()[1]
    line = 0.175 / height_in
    # suptitle биш fig.text: tight_layout нь suptitle-ийн зайг rect дээр давхар хасдаг
    fig.text(0.01, 1 - 0.06 / fig.get_size_inches()[1], "\n".join(title_lines), ha="left", va="top", fontsize=12,
             fontweight="bold", color="#1A1A1A")
    title_h = 0.22 * len(title_lines) / height_in
    fig.text(0.01, 1 - 0.18 / height_in - title_h, "\n".join(sub_lines), ha="left", va="top", fontsize=9.5, color="#404040")
    fig.text(0.01, 0.01, "\n".join(cap_lines), ha="left", va="bottom", fontsize=8, color="#5C5C5C")
    top = 1 - (0.24 / height_in + title_h + len(sub_lines) * line)
    bottom = 0.02 + len(cap_lines) * 0.15 / height_in
    fig.tight_layout(rect=(0, bottom, 1, top))
    fig._mba_meta = {"title": title, "subtitle": subtitle, "source": source, "n": n,
                     "uncertainty_note": uncertainty_note, "unit": unit}
    return fig


def save_figure(fig, out_dir: Path, name: str) -> tuple[Path, Path]:
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    w, h = fig.get_size_inches()
    fig.set_size_inches(WIDTH_IN, h * WIDTH_IN / w)
    png, svg = out_dir / f"{name}.png", out_dir / f"{name}.svg"
    fig.savefig(png, dpi=300, metadata={"Software": None})
    fig.savefig(svg, metadata={"Date": None})
    return png, svg
