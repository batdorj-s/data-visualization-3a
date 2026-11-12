from pathlib import Path

from src.make_figures import FIGURE_SPECS, render_all

ROOT = Path(__file__).resolve().parents[1]


def test_render_all_fast(tmp_path):
    log = render_all(ROOT / "data" / "processed", ROOT / "reports", tmp_path, n_boot=60)
    assert len(FIGURE_SPECS) >= 26
    assert (log.status == "ok").all(), log[log.status != "ok"].to_string()
    assert len(list(tmp_path.glob("*.png"))) == len(FIGURE_SPECS)
    assert len(list(tmp_path.glob("*.svg"))) == len(FIGURE_SPECS)
    names = [n for n, _ in FIGURE_SPECS]
    for required in ["F01", "F02", "F03", "F04", "F05", "F06", "P1", "P2", "P3", "U01", "U02", "U03", "U04", "U05",
                     "U06a", "U06b", "U09"]:
        assert any(n.startswith(required + "_") for n in names), required
