from PIL import Image

from src.blueprint import draw_architecture, draw_wireframe_pregame, draw_wireframe_scout, write_user_stories


def test_blueprint_images(tmp_path):
    for fn in (draw_architecture, draw_wireframe_scout, draw_wireframe_pregame):
        png = fn(tmp_path)
        assert png.exists() and png.with_suffix(".svg").exists()
        assert Image.open(png).size[0] >= 1800


def test_user_stories(tmp_path):
    path = write_user_stories(tmp_path)
    text = path.read_text(encoding="utf-8")
    assert text.count("- **") >= 4
    assert "Хязгаарлалт" in text and "Дараагийн алхам" in text
