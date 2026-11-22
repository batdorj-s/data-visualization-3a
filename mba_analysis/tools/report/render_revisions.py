"""Графикийн өөрчлөлтийн бүртгэлийн «өмнө / дараа» зургийг git түүхээс бодитоор гаргана → figures/revisions/<key>.png.

Өөрчлөлт бүрийн өмнөх ба дараах commit-ийг түр git worktree болгон гаргаж, ТУХАЙН ҮЕИЙН dashboard/plots.py ба
dashboard/data/*.parquet-аар графикийг зурна (тухайн үеийн хэрэглэгчийн харсантай ижил). Plotly-г HTML болгоод headless
Chrome-оор 2× PNG болгож, хоёрыг «Өмнө» / «Дараа» гэж зэрэгцүүлнэ. Аль өөрчлөлтийг юугаар зурахыг src/revision_log.py.

Ажиллуулах (mba_analysis/-аас):  .venv/bin/python tools/report/render_revisions.py
Шаардлага: git, Google Chrome (CHROME орчны хувьсагчаар зам өөрчилж болно), сүлжээ (зөвхөн багийн логоны зурагт).
"""
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[2]  # mba_analysis/
REPO = ROOT.parent
sys.path.insert(0, str(ROOT))
from src.revision_log import REVISIONS  # noqa: E402

CHROME = os.environ.get("CHROME", "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome")
OUT = ROOT / "figures" / "revisions"
WIDTH = 900

RUNNER = r'''
import base64, io, sys
import numpy as np, pandas as pd
DATA = sys.argv[1]
def load(name): return pd.read_parquet(f"{DATA}/{name}.parquet")
def thumbs(meta):
    import requests
    from PIL import Image
    out = {}
    for name, url in zip(meta.canonical_name, meta.get("logo_url", pd.Series(dtype=str))):
        if not isinstance(url, str): continue
        r = requests.get(url, timeout=15, headers={"User-Agent": "Mozilla/5.0 (MBA Analytics student report)"}); r.raise_for_status()
        im = Image.open(io.BytesIO(r.content)).convert("RGBA"); im.thumbnail((128, 128)); b = io.BytesIO(); im.save(b, "PNG")
        out[name] = "data:image/png;base64," + base64.b64encode(b.getvalue()).decode()
    return out
from plots import *
SEASON = "2025-2026"
players = load("players"); P = players[(players.season == SEASON) & (players.GP >= 5)]
fig = None
exec(sys.argv[3])
fig.update_layout(width=%(width)d)
html = fig.to_html(include_plotlyjs=True, full_html=True, config={"staticPlot": True})
open(sys.argv[2], "w", encoding="utf-8").write(html.replace("<head>", "<head><style>html,body{margin:0;background:#fff}</style>", 1))
print(int(fig.layout.height or 450))
''' % {"width": WIDTH}


def worktree(commit: str, base: Path) -> Path:
    path = base / commit
    if not path.exists():
        subprocess.run(["git", "-C", str(REPO), "worktree", "add", "--detach", "--quiet", str(path), commit], check=True)
    return path


def render(commit: str, code: str, out_png: Path, base: Path) -> None:
    wt = worktree(commit, base) / "mba_analysis"
    html = out_png.with_suffix(".html")
    env = {**os.environ, "PYTHONPATH": f"{wt / 'dashboard'}{os.pathsep}{wt}", "MBA_LOGO_FETCH": "0"}
    res = subprocess.run([sys.executable, "-c", RUNNER, str(wt / "dashboard" / "data"), str(html), code],
                         env=env, cwd=wt / "dashboard", capture_output=True, text=True)
    if res.returncode:
        raise RuntimeError(f"{commit}: {res.stderr[-1500:]}")
    height = int(res.stdout.strip().splitlines()[-1])
    subprocess.run([CHROME, "--headless=new", "--disable-gpu", "--hide-scrollbars", "--force-device-scale-factor=2",
                    f"--window-size={WIDTH},{height}", "--virtual-time-budget=8000", f"--screenshot={out_png}",
                    html.as_uri()], check=True, capture_output=True)
    html.unlink()


def _font(size: int):
    for f in ("/System/Library/Fonts/Supplemental/Arial Bold.ttf", "/Library/Fonts/Arial Bold.ttf",
              "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"):
        if Path(f).exists():
            return ImageFont.truetype(f, size)
    return ImageFont.load_default()


def side_by_side(before: Path, after: Path, out: Path) -> None:
    """«Өмнө» ба «Дараа»-г дээш доош нь (тайлангийн өргөнд уншигдахуйц) шошготой нэгтгэнэ."""
    a, b = Image.open(before).convert("RGB"), Image.open(after).convert("RGB")
    w = max(a.width, b.width)
    label_h, gap = 70, 30
    canvas = Image.new("RGB", (w, a.height + b.height + 2 * label_h + gap), "white")
    draw = ImageDraw.Draw(canvas)
    font = _font(40)
    y = 0
    for img, text, color in ((a, "Өмнө", (110, 110, 110)), (b, "Дараа", (27, 58, 107))):
        draw.text((16, y + 14), text, fill=color, font=font)
        canvas.paste(img, (0, y + label_h))
        y += label_h + img.height + gap
        draw.line([(0, y - gap // 2), (w, y - gap // 2)], fill=(210, 215, 222), width=2)
    canvas.save(out, optimize=True)


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    base = Path(tempfile.mkdtemp(prefix="mba_rev_"))
    try:
        for r in REVISIONS:
            if not r.get("before"):
                continue
            tmp_b, tmp_a = OUT / f"{r['key']}_before.png", OUT / f"{r['key']}_after.png"
            render(r["before"]["commit"], r["before"]["code"], tmp_b, base)
            render(r["after"]["commit"], r["after"]["code"], tmp_a, base)
            side_by_side(tmp_b, tmp_a, OUT / f"{r['key']}.png")
            tmp_b.unlink(); tmp_a.unlink()
            print("ok", r["key"])
    finally:
        for wt in base.iterdir():
            subprocess.run(["git", "-C", str(REPO), "worktree", "remove", "--force", str(wt)], check=False)
        shutil.rmtree(base, ignore_errors=True)


if __name__ == "__main__":
    main()
