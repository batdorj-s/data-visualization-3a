import pandas as pd
import pytest

from src import scrape
from src.fetch import Fetcher
from src.parse_mba import parse_schedule
from tests.conftest import load_fixture

S25 = "c1a0488c-31a5-429d-8254-3b27aa45e702"
S26 = "ac48cf7e-0249-4450-a2ee-42fc7b97dc16"


def seed(fetcher: Fetcher, mapping: dict[str, str]) -> None:
    for url, name in mapping.items():
        fetcher.cache_path(url).write_text(load_fixture("html", name), encoding="utf-8")


class SpyFetcher(Fetcher):
    def __init__(self, *a, **k):
        super().__init__(*a, **k)
        self.urls = []

    def get(self, url):
        self.urls.append(url)
        return super().get(url)


@pytest.fixture
def offline_jan(tmp_path, monkeypatch):
    monkeypatch.setattr(scrape, "SEASONS", {"2025-2026": (S25, ["2026-01"])})
    f = SpyFetcher(tmp_path / "cache", offline=True)
    seed(f, {
        scrape.schedule_url(S25, "2026-01"): "schedule_2025_26_2026_01",
        scrape.game_url(141): "game_141",
        scrape.stats_url(S25): "stats_2025_26",
        scrape.profile_url("byron-wesley-2"): "profile_byron_wesley",
    })
    return f


def test_scrape_offline_writes_csvs(tmp_path, offline_jan):
    raw = tmp_path / "raw"
    counts = scrape.scrape_all(raw, offline_jan)
    for name in ["schedule", "games_raw", "team_games_raw", "player_games_raw",
                 "players_season_raw", "players_profile_raw"]:
        assert (raw / f"{name}.csv").exists(), name
    games = pd.read_csv(raw / "games_raw.csv")
    assert list(games["game_id"]) == [141]
    assert games.loc[0, "stage"] == "Regular season"
    assert games.loc[0, "quarters_home"] == "18|20|20|19"
    tg = pd.read_csv(raw / "team_games_raw.csv")
    assert sorted(tg.loc[tg.game_id == 141, "side"]) == ["away", "home"]
    assert len(pd.read_csv(raw / "players_season_raw.csv")) == 171
    assert len(pd.read_csv(raw / "players_profile_raw.csv")) == 1
    snap = (raw / "SNAPSHOT.md").read_text(encoding="utf-8")
    assert "2026-" in snap and S25 in snap
    assert counts["games_raw"] == 1
    assert counts["missing_games"] == 34


def test_scrape_only_final_games(tmp_path, monkeypatch):
    monkeypatch.setattr(scrape, "SEASONS", {"2026-2027": (S26, ["2026-11"])})
    f = SpyFetcher(tmp_path / "cache", offline=True)
    seed(f, {scrape.schedule_url(S26, "2026-11"): "schedule_2026_27_2026_11"})
    scrape.scrape_all(tmp_path / "raw", f)
    sched = parse_schedule(load_fixture("html", "schedule_2026_27_2026_11"), "2026-11")
    expected = {scrape.game_url(r["game_id"]) for r in sched if r["status"] == "Final"}
    requested = {u for u in f.urls if "/en/games/" in u}
    assert requested == expected
    assert any(r["status"] == "Scheduled" for r in sched)


def test_offline_rerun_keeps_snapshot_date(tmp_path, offline_jan):
    raw = tmp_path / "raw"
    raw.mkdir()
    (raw / "SNAPSHOT.md").write_text("# Өгөгдлийн snapshot\n\n- Татсан огноо: 2026-11-12T23:58\n", encoding="utf-8")
    scrape.scrape_all(raw, offline_jan)
    assert "Татсан огноо: 2026-11-12T23:58" in (raw / "SNAPSHOT.md").read_text(encoding="utf-8")
