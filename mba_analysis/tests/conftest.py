from pathlib import Path

import pytest

FIXTURES = Path(__file__).parent / "fixtures"


def load_fixture(kind: str, name: str) -> str:
    ext = "html" if kind == "html" else "txt"
    path = FIXTURES / kind / f"{name}.{ext}"
    if not path.exists():
        pytest.skip(f"fixture алга: {path} — `python tools/fetch_fixtures.py` ажиллуулна уу")
    return path.read_text(encoding="utf-8")


@pytest.fixture
def html():
    return lambda name: load_fixture("html", name)


@pytest.fixture
def wiki():
    return lambda name: load_fixture("wiki", name)
