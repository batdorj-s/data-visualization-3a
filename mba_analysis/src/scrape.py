import argparse
import re
from datetime import datetime
from pathlib import Path

import pandas as pd

from src.fetch import CacheMiss, Fetcher
from src.parse_mba import parse_game, parse_game_events, parse_player_profile, parse_player_stats, parse_schedule

BASE = "https://mongolia.basketball"
ROOT = Path(__file__).resolve().parents[1]

SEASONS: dict[str, tuple[str, list[str]]] = {
    "2025-2026": ("c1a0488c-31a5-429d-8254-3b27aa45e702",
                  ["2025-10", "2025-11", "2025-12", "2026-01", "2026-02", "2026-03", "2026-04"]),
    "2026-2027": ("ac48cf7e-0249-4450-a2ee-42fc7b97dc16", ["2026-10", "2026-11"]),
}


def schedule_url(season_id: str, month: str) -> str:
    return f"{BASE}/en/competitions/league/schedule?season={season_id}&month={month}"


def game_url(game_id: int) -> str:
    return f"{BASE}/en/games/{game_id}"


def stats_url(season_id: str) -> str:
    return f"{BASE}/en/stats?competition=league&view=players&season={season_id}"


def profile_url(slug: str) -> str:
    return f"{BASE}/en/players/{slug}"


GZIP = {"method": "gzip", "mtime": 0}  # mtime=0: дахин ажиллуулахад файл байт бүрээрээ ижил


def _write(df: pd.DataFrame, path: Path) -> int:
    df.to_csv(path, index=False, encoding="utf-8", compression=GZIP if str(path).endswith(".gz") else None)
    return len(df)


def scrape_all(raw_dir: Path, fetcher: Fetcher) -> dict[str, int]:
    raw_dir = Path(raw_dir)
    raw_dir.mkdir(parents=True, exist_ok=True)
    counts: dict[str, int] = {"missing_games": 0, "missing_profiles": 0}

    current = max(SEASONS)  # явагдаж буй улирлын хуудсуудыг шинэчилнэ; дууссан тоглолтын хуудас өөрчлөгдөхгүй
    schedule = []
    for season, (sid, months) in SEASONS.items():
        for month in months:
            page = fetcher.get(schedule_url(sid, month), refresh=season == current)
            for row in parse_schedule(page, month):
                schedule.append({"season": season, **row})
    sched_df = pd.DataFrame(schedule)
    counts["schedule"] = _write(sched_df, raw_dir / "schedule.csv")

    finals = (sched_df[sched_df["status"] == "Final"].drop_duplicates("game_id")
              if len(sched_df) else sched_df)
    games, team_games, player_games, shots, events = [], [], [], [], []
    for i, card in enumerate(finals.to_dict("records"), 1):
        gid = int(card["game_id"])
        try:
            page = fetcher.get(game_url(gid))
            g = parse_game(page, gid)
        except CacheMiss:
            counts["missing_games"] += 1
            continue
        names = {"home": g["home_name"], "away": g["away_name"]}
        games.append({
            "game_id": gid, "season": g["season"] or card["season"], "date": g["date"], "time": g["time"],
            "venue_raw": g["venue_raw"], "stage": card["stage"],
            "home_name": g["home_name"], "away_name": g["away_name"],
            "home_team_slug": card["home_team_slug"], "away_team_slug": card["away_team_slug"],
            "home_pts": g["home_pts"], "away_pts": g["away_pts"],
            "quarters_home": "|".join(map(str, g["quarters"]["home"])),
            "quarters_away": "|".join(map(str, g["quarters"]["away"])),
        })
        for t in g["team_totals"]:
            team_games.append({"game_id": gid, "season": card["season"], "team_name": names[t["side"]], **t})
        for p in g["players"]:
            player_games.append({"game_id": gid, "season": card["season"], "team_name": names[p["side"]], **p})
        ev = parse_game_events(page, gid)
        shots += ev["shots"]
        events += ev["events"]
        if i % 25 == 0:
            print(f"  тоглолт {i}/{len(finals)}", flush=True)
    counts["games_raw"] = _write(pd.DataFrame(games), raw_dir / "games_raw.csv")
    counts["team_games_raw"] = _write(pd.DataFrame(team_games), raw_dir / "team_games_raw.csv")
    counts["player_games_raw"] = _write(pd.DataFrame(player_games), raw_dir / "player_games_raw.csv")
    counts["shots_raw"] = _write(pd.DataFrame(shots), raw_dir / "shots_raw.csv")
    counts["pbp_raw"] = _write(pd.DataFrame(events), raw_dir / "pbp_raw.csv.gz")

    stats = []
    counts["missing_stats"] = 0
    for season, (sid, _) in SEASONS.items():
        try:
            page = fetcher.get(stats_url(sid), refresh=season == current)
        except CacheMiss:
            counts["missing_stats"] += 1
            continue
        for row in parse_player_stats(page):
            stats.append({"season": season, **row})
    stats_df = pd.DataFrame(stats)
    counts["players_season_raw"] = _write(stats_df, raw_dir / "players_season_raw.csv")

    slugs = list(dict.fromkeys(stats_df["player_slug"].dropna())) if len(stats_df) else []
    profiles = []
    for i, slug in enumerate(slugs, 1):
        try:
            profiles.append(parse_player_profile(fetcher.get(profile_url(slug)), slug))
        except CacheMiss:
            counts["missing_profiles"] += 1
        if i % 50 == 0:
            print(f"  профайл {i}/{len(slugs)}", flush=True)
    counts["players_profile_raw"] = _write(pd.DataFrame(profiles), raw_dir / "players_profile_raw.csv")

    fetched_at = datetime.now().isoformat(timespec="minutes")
    snap = raw_dir / "SNAPSHOT.md"
    if fetcher.offline and snap.exists():
        prev = re.search(r"Татсан огноо: (\S+)", snap.read_text(encoding="utf-8"))
        fetched_at = prev.group(1) if prev else fetched_at
    lines = [
        "# Өгөгдлийн snapshot",
        "",
        f"- Татсан огноо: {fetched_at}",
        f"- Эх сурвалж: {BASE} (MBA статистикийн систем)",
        "- 2026-2027 улирал энэ огнооны байдлаар дуусаагүй (явцын).",
        "",
        "| Улирал | Season ID | Сарууд |",
        "|---|---|---|",
        *[f"| {s} | {sid} | {', '.join(m)} |" for s, (sid, m) in SEASONS.items()],
        "",
        "| Файл | Мөр |",
        "|---|---|",
        *[f"| {k} | {v} |" for k, v in counts.items()],
    ]
    (raw_dir / "SNAPSHOT.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    return counts


def main() -> None:
    ap = argparse.ArgumentParser(description="MBA-ийн түүхий датаг data/raw/*.csv болгоно")
    ap.add_argument("--offline", action="store_true", help="зөвхөн кэшээс уншина")
    args = ap.parse_args()
    fetcher = Fetcher(ROOT / "data" / "raw" / "html", offline=args.offline)
    counts = scrape_all(ROOT / "data" / "raw", fetcher)
    for k, v in counts.items():
        print(f"{k}: {v}")


if __name__ == "__main__":
    main()
