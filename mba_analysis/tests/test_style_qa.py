import warnings

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import pytest  # noqa: E402
from PIL import Image  # noqa: E402

from src.chart_qa import ChartQAError, check  # noqa: E402
from src.style import IMPORT_COLORS, NEUTRAL, PALETTE, apply_style, finish, save_figure, source_mba  # noqa: E402


def good_fig():
    apply_style()
    fig, ax = plt.subplots(figsize=(6.3, 4))
    ax.scatter([1, 2, 3], [3, 1, 2], color=PALETTE["blue"])
    ax.set_xlabel("Минут")
    ax.set_ylabel("Оноо")
    return finish(fig, "Минут ихсэх тусам оноо өсдөг", "2025-26, GP ≥ 5", source_mba(), n=3)


def test_apply_style_font_and_cyrillic():
    font = apply_style()
    assert font in {"Arial", "DejaVu Sans"}
    with warnings.catch_warnings():
        warnings.simplefilter("error")
        fig, ax = plt.subplots()
        ax.set_title("Өөрийн үгээр — Үзүүлэлт")
        fig.canvas.draw()
    plt.close(fig)


def test_palette_constants():
    assert IMPORT_COLORS == {True: "#D55E00", False: "#0072B2"}
    assert NEUTRAL == "#9E9E9E"


def test_check_passes_on_complete_figure():
    meta = check(good_fig())
    assert meta["n"] == 3 and meta["title"].startswith("Минут")


def test_check_missing_source():
    fig = good_fig()
    fig._mba_meta["source"] = ""
    with pytest.raises(ChartQAError, match="source"):
        check(fig)


def test_check_missing_ylabel():
    fig = good_fig()
    fig.axes[0].set_ylabel("")
    with pytest.raises(ChartQAError, match="ylabel"):
        check(fig)


def test_check_too_many_colors():
    apply_style()
    fig, ax = plt.subplots()
    colors = ["#E69F00", "#56B4E9", "#009E73", "#F0E442", "#0072B2", "#D55E00", "#CC79A7"]
    ax.bar(range(7), range(1, 8), color=colors)
    ax.set_xlabel("x")
    ax.set_ylabel("y")
    finish(fig, "Гарчиг", "Дэд", source_mba(), n=7)
    with pytest.raises(ChartQAError, match="colors"):
        check(fig)


def test_check_unfinished_figure():
    fig, ax = plt.subplots()
    with pytest.raises(ChartQAError, match="finish"):
        check(fig)


def test_save_figure_png_svg(tmp_path):
    png, svg = save_figure(good_fig(), tmp_path, "F00_test")
    assert png.exists() and svg.exists()
    width = Image.open(png).size[0]
    assert abs(width - 1890) <= 5


def test_long_subtitle_wraps():
    apply_style()
    fig, ax = plt.subplots(figsize=(6.3, 4))
    ax.set_xlabel("x")
    ax.set_ylabel("y")
    finish(fig, "Гарчиг", "маш урт дэд гарчиг " * 15, source_mba(), n=1)
    subtitle = next(t for t in fig.texts if "маш урт" in t.get_text())
    assert "\n" in subtitle.get_text()
    assert all(len(line) <= 120 for line in subtitle.get_text().split("\n"))


def test_svg_output_is_deterministic(tmp_path):
    a = save_figure(good_fig(), tmp_path / "a", "F00")[1].read_bytes()
    b = save_figure(good_fig(), tmp_path / "b", "F00")[1].read_bytes()
    assert a == b
