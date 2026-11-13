import pytest

from src import fetch
from src.fetch import UA, CacheMiss, Fetcher


class FakeResponse:
    def __init__(self, text):
        self.text = text
        self.encoding = "utf-8"

    def raise_for_status(self):
        pass


@pytest.fixture
def calls(monkeypatch):
    log = {"get": [], "sleep": []}

    def fake_get(url, headers=None, timeout=None):
        log["get"].append((url, headers))
        return FakeResponse(f"<html>{url}</html>")

    monkeypatch.setattr(fetch.requests, "get", fake_get)
    monkeypatch.setattr(fetch.time, "sleep", lambda s: log["sleep"].append(s))
    return log


def test_get_uses_cache_on_second_call(tmp_path, calls):
    f = Fetcher(tmp_path)
    url = "https://mongolia.basketball/en/games/141"
    first = f.get(url)
    second = f.get(url)
    assert first == second == f"<html>{url}</html>"
    assert len(calls["get"]) == 1


def test_offline_cache_miss_raises(tmp_path, calls):
    f = Fetcher(tmp_path, offline=True)
    with pytest.raises(CacheMiss):
        f.get("https://mongolia.basketball/en/games/1")
    assert calls["get"] == []


def test_throttle_between_network_calls(tmp_path, calls):
    f = Fetcher(tmp_path, delay_s=1.0)
    f.get("https://mongolia.basketball/en/games/1")
    f.get("https://mongolia.basketball/en/games/2")
    assert sum(calls["sleep"]) >= 1.0


def test_sends_user_agent(tmp_path, calls):
    Fetcher(tmp_path).get("https://mongolia.basketball/en/stats")
    _, headers = calls["get"][0]
    assert headers["User-Agent"] == "Mozilla/5.0 (student project)" == UA


@pytest.mark.parametrize(
    "url",
    [
        "https://www.asia-basket.com/Mongolia/basketball-League-MBL-Leaders.aspx",
        "https://mongolia.basketball/api/players",
        "https://mongolia.basketball/admin",
    ],
)
def test_refuses_disallowed_hosts(tmp_path, calls, url):
    with pytest.raises(ValueError):
        Fetcher(tmp_path).get(url)
    assert calls["get"] == []


def test_refresh_refetches_cached_page(tmp_path, calls):
    f = Fetcher(tmp_path)
    url = "https://mongolia.basketball/en/competitions/league/schedule?month=2026-11"
    f.get(url)
    f.get(url, refresh=True)
    assert len(calls["get"]) == 2


def test_refresh_offline_uses_cache(tmp_path, calls):
    url = "https://mongolia.basketball/en/stats"
    Fetcher(tmp_path).get(url)
    assert Fetcher(tmp_path, offline=True).get(url, refresh=True).startswith("<html>")
    assert len(calls["get"]) == 1
