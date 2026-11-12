import json
import subprocess
from pathlib import Path

import pytest

from src.report_data import DRAFT_LABEL, build_report_data

ROOT = Path(__file__).resolve().parents[1]
TOOLS = ROOT / "tools" / "report"


@pytest.fixture(scope="module")
def data():
    return build_report_data(ROOT)


def test_report_data_sections(data):
    assert len(data["sections"]) == 10
    assert data["sections"][0]["title"].startswith("1.")
    figs = [f for s in data["sections"] for b in s["blocks"] if b["type"] == "figure" for f in [b]]
    assert len(figs) >= 12
    assert all(Path(ROOT / f["path"]).exists() and f["width_px"] > 0 for f in figs)
    tables = [b for s in data["sections"] for b in s["blocks"] if b["type"] == "table"]
    assert len(tables) >= 5
    drafts = [b for s in data["sections"] for b in s["blocks"] if b["type"] == "draft"]
    assert len(drafts) >= 5


def test_report_numbers_match_reports(data):
    hyp = {h["hid"]: h for h in data["hypotheses"]}
    assert set(hyp) == {"H1", "H2", "H3", "H4", "H5"}
    assert hyp["H2"]["verdict"] == "Тодорхойгүй"
    assert data["kpi"]["games"] == 252
    assert data["slides"] and 11 <= len(data["slides"]) <= 13
    assert all(len(s.get("bullets", [])) <= 3 for s in data["slides"])


def _node(script, out):
    subprocess.run(["node", str(TOOLS / script), str(ROOT / "report" / "report_data.json"), str(out)],
                   check=True, cwd=TOOLS, capture_output=True)


def test_docx_structure(tmp_path, data):
    from docx import Document
    (ROOT / "report").mkdir(exist_ok=True)
    (ROOT / "report" / "report_data.json").write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")
    out = tmp_path / "t.docx"
    _node("build_docx.js", out)
    doc = Document(out)
    h1 = [p for p in doc.paragraphs if p.style.name == "Heading 1"]
    assert len(h1) == 10
    assert len(doc.inline_shapes) >= 12
    assert len(doc.tables) >= 5
    assert sum(DRAFT_LABEL in p.text for p in doc.paragraphs) >= 5


def test_pptx_structure(tmp_path, data):
    from pptx import Presentation
    from pptx.enum.shapes import MSO_SHAPE_TYPE
    (ROOT / "report" / "report_data.json").write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")
    out = tmp_path / "t.pptx"
    _node("build_pptx.js", out)
    prs = Presentation(out)
    assert 11 <= len(prs.slides) <= 13
    for slide in prs.slides:
        pics = [s for s in slide.shapes if s.shape_type == MSO_SHAPE_TYPE.PICTURE]
        assert len(pics) <= 1
        assert slide.has_notes_slide and slide.notes_slide.notes_text_frame.text.strip()
