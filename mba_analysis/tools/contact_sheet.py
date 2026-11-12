"""figures/ доторх PNG-үүдийг нэг зураг болгож нийлүүлнэ (нүдээр шалгахад)."""
import sys
from pathlib import Path

from PIL import Image


def sheet(paths, out, cols=3, width=700):
    ims = []
    for p in paths:
        im = Image.open(p).convert("RGB")
        ims.append(im.resize((width, int(im.height * width / im.width))))
    rows = [ims[i:i + cols] for i in range(0, len(ims), cols)]
    H = sum(max(i.height for i in r) for r in rows)
    canvas = Image.new("RGB", (cols * width, H), "white")
    y = 0
    for r in rows:
        for j, im in enumerate(r):
            canvas.paste(im, (j * width, y))
        y += max(i.height for i in r)
    canvas.save(out)


if __name__ == "__main__":
    sheet(sorted(Path(sys.argv[1]).glob(sys.argv[2])), sys.argv[3], cols=int(sys.argv[4]) if len(sys.argv) > 4 else 3)
