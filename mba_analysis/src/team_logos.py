"""Багийн албан ёсны логоны URL → data/processed/team_logos.csv.

Эх сурвалж: MBA-ийн тоглолтын хуудас бүрт байгаа schema.org «SportsTeam» бичлэг (нэр, багийн хуудас, логоны URL).
Хадгалсан HTML-ээс (data/raw/html) offline уншина; логоны зургийг repo-д хуулахгүй, зөвхөн албан ёсны URL-ийг хадгална.
Багийн нэрийг team_aliases.csv-ээр team_key руу буулгана (clean-тэй ижил дүрэм).

Ажиллуулах: python -m src.team_logos   (clean-ийн дараа)
"""
import re
from collections import Counter
from pathlib import Path

import pandas as pd

from src.clean import map_teams

ROOT = Path(__file__).resolve().parents[1]
PATTERN = re.compile(r'"@type":"SportsTeam","name":"([^"]+)","url":"([^"]+)","logo":"(https://mongolia\.basketball/[^"]+)"')


def extract(html_dir: Path, aliases: pd.DataFrame) -> pd.DataFrame:
    seen: Counter = Counter()
    for f in sorted(Path(html_dir).glob("*.html")):
        for m in PATTERN.finditer(f.read_text(encoding="utf-8", errors="ignore")):
            seen[m.groups()] += 1
    if not seen:
        return pd.DataFrame(columns=["team_key", "logo_url", "team_url", "n_pages"])
    raw = pd.DataFrame([(n, u, lg, c) for (n, u, lg), c in seen.items()],
                       columns=["team_name", "team_url", "logo_url", "n_pages"])
    raw = map_teams(raw, "team_name", aliases)
    # Нэг багт хэд хэдэн нэр/хуудас байж болно: хамгийн олон хуудсанд гарсан логог авна
    best = raw.sort_values(["team_key", "n_pages"], ascending=[True, False]).drop_duplicates("team_key")
    return best[["team_key", "logo_url", "team_url", "n_pages"]].reset_index(drop=True)


def main() -> None:
    aliases = pd.read_csv(ROOT / "data" / "raw" / "manual" / "team_aliases.csv", dtype=str).fillna("")
    out = extract(ROOT / "data" / "raw" / "html", aliases)
    dest = ROOT / "data" / "processed" / "team_logos.csv"
    if out.empty and dest.exists():  # HTML кэш алга (жишээ нь шинэ clone) — өмнөх баталгаажсан файлыг дарж устгахгүй
        print("HTML кэш алга: team_logos.csv-ийг хэвээр үлдээв")
        return
    out.to_csv(dest, index=False)
    print(f"{len(out)} багийн логоны URL")


if __name__ == "__main__":
    main()
