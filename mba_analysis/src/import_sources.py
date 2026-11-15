"""Гадаад тоглогчдын гарал үүсэл, өмнөх карьер (ShamSports) → data/raw/import_background_raw.csv, import_career_raw.csv.

Эх сурвалж: shamsports.com/players/<нэр-овог> (robots.txt зөвшөөрнө). MBA нэрийн дарааллыг холимог бичдэг тул хэд хэдэн
дарааллаар хайна. Буруу хүнтэй андуурахаас сэргийлж төрсөн он (±1) эсвэл MBA-д төрсөн он байхгүй бол өндөр (±5 см)-өөр
баталгаажуулна. Хуудасны «Transactions», «Career» хэсэг 2017–2019 оноос хойш шинэчлэгдээгүй тул ашиглахгүй; зөвхөн
улирал бүрийн статистикийн хүснэгтийг уншина.

Ажиллуулах: python -m src.import_sources [--offline]   (clean-ийн дараа)
"""
import argparse
import re
import unicodedata
from pathlib import Path

import pandas as pd
import requests
from bs4 import BeautifulSoup

from src.fetch import CacheMiss, Fetcher

ROOT = Path(__file__).resolve().parents[1]
BASE = "https://www.shamsports.com/players/"
MBA_SEASON_START = {"2025-2026": 2025, "2026-2027": 2026}


def _slug(text: str) -> str:
    s = unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode().lower()
    return re.sub(r"[^a-z0-9]+", "-", s).strip("-")


def slug_candidates(mba_name: str) -> list[str]:
    """«MILLER Ian», «IAN Miller», «MOORE Mckenzie Zachary» → боломжит URL slug-ууд (давхардалгүй, дараалалтай)."""
    p = mba_name.split()
    cands = [" ".join(p[1:] + p[:1]), mba_name]
    if len(p) > 2:
        cands += [f"{p[1]} {p[0]}", f"{p[0]} {p[-1]}", f"{p[-1]} {p[0]}"]
    return list(dict.fromkeys(_slug(c) for c in cands if c.strip()))


def _field(soup: BeautifulSoup, label: str) -> str | None:
    el = soup.find("strong", string=lambda x: x and x.strip() == label)
    if el is None:
        return None
    text = el.parent.get_text(" | ", strip=True)
    return text.split("|", 1)[1].strip(" |") if "|" in text else None


def parse_profile(html: str) -> dict:
    soup = BeautifulSoup(html, "lxml")
    born = _field(soup, "Born") or ""
    m = re.search(r"(\d{4})", born)
    nat = _field(soup, "Nationality") or ""
    nat = ", ".join(p.strip() for p in re.split(r"\s{2,}|\|", re.sub(r"[^\w\s.'|&-]", "", nat)) if p.strip()) or None
    hm_el = soup.find(attrs={"data-unit-metric": re.compile(r"^\d+cm$")})
    rows = []
    for t in soup.find_all("table"):
        head = [th.get_text(strip=True) for th in t.find_all("th")]
        if head[:3] != ["Year", "League", "Team"]:
            continue
        idx = {h: i for i, h in enumerate(head)}
        for tr in t.find_all("tr")[1:]:
            td = [c.get_text(" ", strip=True) for c in tr.find_all("td")]
            if len(td) < len(head) or not re.fullmatch(r"\d{4}-\d{2}", td[0]):
                continue

            def num(col):
                v = td[idx[col]].rstrip("%") if col in idx else ""
                try:
                    return float(v)
                except ValueError:
                    return None
            rows.append({"year": td[0], "league": td[1], "team": td[2], "g": num("G"), "mpg": num("MPG"),
                         "ppg": num("PTS/G"), "fg_pct": num("FG%"), "tp_pct": num("3P%")})
        break
    return {"birth_year": int(m.group(1)) if m else None, "nationality": nat,
            "height_cm": int(hm_el["data-unit-metric"][:-2]) if hm_el else None,
            "draft": _field(soup, "NBA Draft"), "pre_draft": _field(soup, "Pre-draft team"),
            "career": rows}  # төлөөлөгчийн нэрийг хадгалахгүй: шинжилгээнд хэрэггүй хувийн мэдээлэл (нийтийн repo)


def identity_ok(prof: dict, mba_birth, mba_height: float | None) -> bool:
    """mba_birth: нэг тоо эсвэл олонлог (нэг хүний өөр улирлын профайлууд өөр он өгөх нь бий)."""
    births = [b for b in (mba_birth if isinstance(mba_birth, (set, list, tuple)) else [mba_birth]) if pd.notna(b)]
    if births and prof["birth_year"]:
        return any(abs(prof["birth_year"] - b) <= 1 for b in births)
    if pd.notna(mba_height) and prof["height_cm"]:
        return abs(prof["height_cm"] - mba_height) <= 5
    return False


LEVELS = ["NBA", "EuroLeague / EuroCup", "G League", "Бусад мэргэжлийн лиг", "Мэргэжлийн туршлагагүй"]


def level_of(career: pd.DataFrame) -> str:
    pro = career[~career.league.isin(["NCAA", "NCAA D2", "NAIA", "JUCO"])]
    leagues = set(pro.league)
    if "NBA" in leagues:
        return LEVELS[0]
    if leagues & {"EuroLeague", "EuroCup"}:
        return LEVELS[1]
    if leagues & {"G League", "D League"}:
        return LEVELS[2]
    return LEVELS[3] if len(pro) else LEVELS[4]


def collect(players_season: pd.DataFrame, fetcher: Fetcher) -> tuple[pd.DataFrame, pd.DataFrame]:
    imp = players_season[players_season.is_import.astype(bool)].sort_values("season")
    people = imp.groupby("player_id").agg(name=("player_name", "last"), first_season=("season", "first"),
                                          mba_birth=("birth_year", lambda s: set(s.dropna())),
                                          mba_height=("height_cm", "max")).reset_index()
    ov_path = ROOT / "data" / "raw" / "manual" / "import_identity_overrides.csv"
    overrides = (pd.read_csv(ov_path).query("decision == 'accept'").set_index("player_id").shamsports_slug.to_dict()
                 if ov_path.exists() else {})
    bg, career_rows = [], []
    for r in people.itertuples():
        rec = {"player_id": r.player_id, "mba_name": r.name, "source_url": None, "status": "олдсонгүй"}
        names = imp.loc[imp.player_id == r.player_id, "player_name"].unique()
        for slug in dict.fromkeys(s for n in names for s in slug_candidates(n)):
            url = BASE + slug
            try:
                html = fetcher.get(url)
            except (CacheMiss, requests.HTTPError):
                continue
            prof = parse_profile(html)
            if overrides.get(r.player_id) != slug and not identity_ok(prof, r.mba_birth, r.mba_height):
                rec["status"] = "өөр хүн (төрсөн он/өндөр таараагүй)"
                continue
            car = pd.DataFrame(prof.pop("career"), columns=["year", "league", "team", "g", "mpg", "ppg", "fg_pct", "tp_pct"])
            start = MBA_SEASON_START[r.first_season]
            before = car[car.year.str[:4].astype(int) < start] if len(car) else car
            pro_before = before[~before.league.isin(["NCAA"])]
            last = pro_before.iloc[-1] if len(pro_before) else None
            rec.update(prof, source_url=url, status="олдсон", level=level_of(before),
                       nba_games=float(before.loc[before.league == "NBA", "g"].sum()),
                       pro_seasons=int(pro_before.year.nunique()), last_league=last.league if last is not None else None,
                       last_year=last.year if last is not None else None, college=bool((before.league == "NCAA").any()))
            career_rows.append(car.assign(player_id=r.player_id))
            break
        bg.append(rec)
    career = pd.concat(career_rows, ignore_index=True) if career_rows else pd.DataFrame()
    return pd.DataFrame(bg), career


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--offline", action="store_true")
    args = ap.parse_args()
    fetcher = Fetcher(ROOT / "data" / "raw" / "html", delay_s=2.0, offline=args.offline)
    bg, career = collect(pd.read_csv(ROOT / "data" / "processed" / "players_season.csv"), fetcher)
    bg.to_csv(ROOT / "data" / "raw" / "import_background_raw.csv", index=False)
    career.to_csv(ROOT / "data" / "raw" / "import_career_raw.csv", index=False)
    print(bg.status.value_counts().to_string())


if __name__ == "__main__":
    main()
