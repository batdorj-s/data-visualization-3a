import re
from pathlib import Path

import pandas as pd

from src.fetch import Fetcher

ROOT = Path(__file__).resolve().parents[1]
WIKI_RAW = "https://en.wikipedia.org/w/index.php?action=raw&title="
TITLES = {
    "league": "The_League_(Mongolia)",
    "season_2023_24": "2023%E2%80%9324_The_League_season",
    "national_team": "Mongolia_men%27s_national_basketball_team",
}


def fetch_wikitext(title: str, fetcher: Fetcher) -> str:
    return fetcher.get(WIKI_RAW + title)


def clean_wikilink(s: str) -> str:
    s = re.sub(r"<ref[^>]*>.*?</ref>|<ref[^>]*/>", "", s, flags=re.S)
    s = re.sub(r"\[\[(?:[^\]|]*\|)?([^\]]*)\]\]", r"\1", s)
    s = re.sub(r"'{2,}", "", s)
    return s.strip()


def _section_table(wt: str, heading: str) -> list[list[str]]:
    m = re.search(r"^==\s*" + re.escape(heading) + r"\s*==\s*$", wt, flags=re.M)
    if not m:
        raise ValueError(f"Хэсэг олдсонгүй: {heading}")
    start = wt.index("{|", m.end())
    end = wt.index("|}", start)
    rows, current = [], []
    for line in wt[start:end].splitlines()[1:]:
        line = line.strip()
        if line.startswith("|-"):
            if current:
                rows.append(current)
            current = []
        elif line.startswith("|+") or line.startswith("!"):
            continue
        elif line.startswith("|"):
            current.extend(clean_wikilink(c) for c in line[1:].split("||"))
    if current:
        rows.append(current)
    return rows


def parse_sports_table(wt: str) -> pd.DataFrame:
    names = {k: clean_wikilink(v) for k, v in re.findall(r"\|\s*name_(\w+)\s*=\s*([^|\n]+)", wt)}
    rows = []
    for code, name in names.items():
        def val(field):
            m = re.search(rf"{field}_{code}\s*=\s*(\d+)", wt)
            return int(m.group(1)) if m else None
        rows.append({"code": code, "team_raw": name, "W": val("win"), "L": val("loss"),
                     "PF": val("pf"), "PA": val("pa")})
    return pd.DataFrame(rows)


def parse_champions(wt: str) -> pd.DataFrame:
    rows = [r for r in _section_table(wt, "Champions") if len(r) >= 3]
    return pd.DataFrame([{"season": r[0], "champion": r[1], "runner_up": r[2]} for r in rows])


def parse_current_teams(wt: str) -> pd.DataFrame:
    rows = [r for r in _section_table(wt, "Current teams") if len(r) >= 2]
    return pd.DataFrame([{"team_raw": r[0], "home_city": r[1]} for r in rows])


def parse_fiba_roster(wt: str) -> pd.DataFrame:
    rows = []
    for body in re.findall(r"\{\{FIBA player\|(.*?)\}\}", wt, flags=re.S):
        kv = {}
        for part in body.split("|"):
            if "=" in part:
                k, v = part.split("=", 1)
                kv[k.strip()] = v.strip()
        rows.append({
            "num": int(kv["num"]),
            "first": kv.get("first"),
            "last": kv.get("last"),
            "pos": kv.get("pos"),
            "birth_date": f"{int(kv['year']):04d}-{int(kv['month']):02d}-{int(kv['date']):02d}",
            "club": kv.get("club"),
            "club_country": kv.get("nat"),
            "captain": kv.get("note", "").upper() == "C",
        })
    return pd.DataFrame(rows)


def build_wiki_raw(raw_dir: Path, fetcher: Fetcher) -> None:
    raw_dir = Path(raw_dir)
    league = fetch_wikitext(TITLES["league"], fetcher)
    parse_sports_table(fetch_wikitext(TITLES["season_2023_24"], fetcher)).assign(season="2023-2024").to_csv(
        raw_dir / "standings_2023_24_raw.csv", index=False)
    parse_champions(league).to_csv(raw_dir / "champions_raw.csv", index=False)
    parse_current_teams(league).to_csv(raw_dir / "team_cities_raw.csv", index=False)
    parse_fiba_roster(fetch_wikitext(TITLES["national_team"], fetcher)).to_csv(
        raw_dir / "national_team_raw.csv", index=False)


if __name__ == "__main__":
    build_wiki_raw(ROOT / "data" / "raw", Fetcher(ROOT / "data" / "raw" / "html"))
    print("ok")
