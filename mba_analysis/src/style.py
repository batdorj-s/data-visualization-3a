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
        "font.size": 9,
        "axes.titlesize": 10,
        "axes.labelsize": 9,
        "xtick.labelsize": 8,
        "ytick.labelsize": 8,
        "legend.fontsize": 8,
        "axes.spines.top": False,
        "axes.spines.right": False,
        "axes.grid": True,
        "grid.color": "#EBEBEB",
        "grid.linewidth": 0.6,
        "axes.axisbelow": True,
        "savefig.dpi": 300,
        "figure.dpi": 100,
        "svg.fonttype": "none",
    })
    return font


def source_mba() -> str:
    snap = ROOT / "data" / "raw" / "SNAPSHOT.md"
    day = "2026-11-12"
    if snap.exists():
        m = re.search(r"Татсан огноо: (\d{4}-\d{2}-\d{2})", snap.read_text(encoding="utf-8"))
        day = m.group(1) if m else day
    return f"Эх сурвалж: MBA статистикийн систем, {day}"


def finish(fig, title: str, subtitle: str, source: str, n: int, uncertainty_note: str | None = None):
    width_in = fig.get_size_inches()[0]
    sub_lines = textwrap.wrap(f"{subtitle} · n = {n}", width=int(17 * width_in))
    cap_lines = textwrap.wrap(source if not uncertainty_note else f"{source}. {uncertainty_note}",
                              width=int(20 * width_in))
    height_in = fig.get_size_inches()[1]
    line = 0.16 / height_in
    fig.suptitle(title, x=0.01, y=0.985, ha="left", va="top", fontsize=11, fontweight="bold")
    fig.text(0.01, 1 - 0.38 / height_in, "\n".join(sub_lines), ha="left", va="top", fontsize=8.5, color="#4D4D4D")
    fig.text(0.01, 0.01, "\n".join(cap_lines), ha="left", va="bottom", fontsize=7, color="#6B6B6B")
    top = 1 - (0.42 / height_in + len(sub_lines) * line)
    bottom = 0.02 + len(cap_lines) * 0.13 / height_in
    fig.tight_layout(rect=(0, bottom, 1, top))
    fig._mba_meta = {"title": title, "subtitle": subtitle, "source": source, "n": n,
                     "uncertainty_note": uncertainty_note}
    return fig


def save_figure(fig, out_dir: Path, name: str) -> tuple[Path, Path]:
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    w, h = fig.get_size_inches()
    fig.set_size_inches(WIDTH_IN, h * WIDTH_IN / w)
    png, svg = out_dir / f"{name}.png", out_dir / f"{name}.svg"
    fig.savefig(png, dpi=300)
    fig.savefig(svg)
    return png, svg
