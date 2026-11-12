from matplotlib.collections import Collection
from matplotlib.colors import to_rgba
from matplotlib.lines import Line2D
from matplotlib.patches import Patch

MAX_COLORS = 6


class ChartQAError(AssertionError):
    pass


def _is_neutral(rgba) -> bool:
    r, g, b, a = rgba
    return a < 0.05 or (max(r, g, b) - min(r, g, b) < 0.06)


def _categorical_colors(fig) -> set:
    colors = set()

    def add(c):
        try:
            rgba = to_rgba(c)
        except (ValueError, TypeError):
            return
        if not _is_neutral(rgba):
            colors.add(tuple(round(x, 2) for x in rgba[:3]))

    for ax in fig.axes:
        if ax.get_label() == "<colorbar>":
            continue
        for p in ax.patches:
            if isinstance(p, Patch):
                add(p.get_facecolor())
        for line in ax.get_lines():
            if isinstance(line, Line2D):
                add(line.get_color())
        for coll in ax.collections:
            if isinstance(coll, Collection) and coll.get_array() is None:
                for fc in coll.get_facecolors()[:200]:
                    add(fc)
    return colors


def check(fig) -> dict:
    meta = getattr(fig, "_mba_meta", None)
    if meta is None:
        raise ChartQAError("style.finish() дуудагдаагүй (гарчиг, эх сурвалж, n алга)")
    problems = []
    for key in ("title", "subtitle", "source"):
        if not str(meta.get(key) or "").strip():
            problems.append(key)
    if not isinstance(meta.get("n"), int) or meta["n"] <= 0:
        problems.append("n")
    sup_x = fig.get_supxlabel() if hasattr(fig, "get_supxlabel") else ""
    sup_y = fig.get_supylabel() if hasattr(fig, "get_supylabel") else ""
    for i, ax in enumerate(fig.axes):
        if not ax.axison or ax.get_label() == "<colorbar>" or getattr(ax, "_qa_skip", False):
            continue
        if not ax.get_xlabel().strip() and not sup_x and not getattr(ax, "_qa_no_xlabel", False):
            problems.append(f"xlabel[ax{i}]")
        if not ax.get_ylabel().strip() and not sup_y and not getattr(ax, "_qa_no_ylabel", False):
            problems.append(f"ylabel[ax{i}]")
    n_colors = len(_categorical_colors(fig))
    if n_colors > MAX_COLORS:
        problems.append(f"colors ({n_colors} > {MAX_COLORS})")
    if problems:
        raise ChartQAError("Графикийн чанарын шалгалт: дутуу/буруу — " + ", ".join(problems))
    return meta
