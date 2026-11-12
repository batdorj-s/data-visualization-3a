"""Тестийн fixture-уудыг татаж tests/fixtures/ дотор хадгална (git-д орохгүй)."""

from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.fetch import Fetcher  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
BASE = "https://mongolia.basketball"
S25 = "c1a0488c-31a5-429d-8254-3b27aa45e702"
S26 = "ac48cf7e-0249-4450-a2ee-42fc7b97dc16"

HTML_FIXTURES = {
    "game_141": f"{BASE}/en/games/141",
    "schedule_2025_26_2026_01": f"{BASE}/en/competitions/league/schedule?season={S25}&month=2026-01",
    "schedule_2025_26_2026_03": f"{BASE}/en/competitions/league/schedule?season={S25}&month=2026-03",
    "schedule_2026_27_2026_11": f"{BASE}/en/competitions/league/schedule?season={S26}&month=2026-11",
    "stats_2025_26": f"{BASE}/en/stats?competition=league&view=players&season={S25}",
    "profile_byron_wesley": f"{BASE}/en/players/byron-wesley",
    "profile_narangerel_batbayar": f"{BASE}/en/players/narangerel-batbayar",
}

WIKI = "https://en.wikipedia.org/w/index.php?action=raw&title="
WIKI_FIXTURES = {
    "league": WIKI + "The_League_(Mongolia)",
    "season_2023_24": WIKI + "2023%E2%80%9324_The_League_season",
    "national_team": WIKI + "Mongolia_men%27s_national_basketball_team",
}


def main() -> None:
    fetcher = Fetcher(ROOT / "data" / "raw" / "html")
    html_dir = ROOT / "tests" / "fixtures" / "html"
    html_dir.mkdir(parents=True, exist_ok=True)
    for name, url in HTML_FIXTURES.items():
        (html_dir / f"{name}.html").write_text(fetcher.get(url), encoding="utf-8")
        print("ok", name)
    wiki_dir = ROOT / "tests" / "fixtures" / "wiki"
    wiki_dir.mkdir(parents=True, exist_ok=True)
    for name, url in WIKI_FIXTURES.items():
        (wiki_dir / f"{name}.txt").write_text(fetcher.get(url), encoding="utf-8")
        print("ok", name)


if __name__ == "__main__":
    main()
