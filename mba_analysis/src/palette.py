PALETTE = {
    "orange": "#E69F00", "sky": "#56B4E9", "green": "#009E73", "yellow": "#F0E442",
    "blue": "#0072B2", "vermillion": "#D55E00", "purple": "#CC79A7", "black": "#000000",
}
IMPORT_COLORS = {True: "#D55E00", False: "#0072B2"}
IMPORT_LABELS = {True: "Import", False: "Дотоод"}
POS_COLORS = {"PG": "#E69F00", "SG": "#56B4E9", "SF": "#009E73", "PF": "#CC79A7", "C": "#0072B2"}
NEUTRAL = "#9E9E9E"
LIGHT = "#D9D9D9"
CLUSTER_COLORS = [PALETTE["vermillion"], PALETTE["blue"], PALETTE["green"], PALETTE["orange"], PALETTE["purple"]]


def cluster_colors(names) -> dict:
    """Архетипийн нэр → өнгө; бүх график ба dashboard ижил mapping хэрэглэнэ."""
    return dict(zip(sorted(set(names)), CLUSTER_COLORS))
