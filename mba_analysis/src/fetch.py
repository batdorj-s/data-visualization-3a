import hashlib
import time
from pathlib import Path
from urllib.parse import urlparse

import requests

UA = "Mozilla/5.0 (student project)"

BLOCKED_HOSTS = {"asia-basket.com"}
BLOCKED_PATH_PREFIXES = {"mongolia.basketball": ("/api", "/admin")}


class CacheMiss(Exception):
    pass


def _check_allowed(url: str) -> None:
    parts = urlparse(url)
    host = parts.hostname or ""
    if any(host == h or host.endswith("." + h) for h in BLOCKED_HOSTS):
        raise ValueError(f"Хориглосон эх сурвалж (robots.txt): {host}")
    for blocked_host, prefixes in BLOCKED_PATH_PREFIXES.items():
        if host == blocked_host and parts.path.startswith(prefixes):
            raise ValueError(f"robots.txt-ээр хориглосон зам: {parts.path}")


class Fetcher:
    def __init__(self, cache_dir: Path, delay_s: float = 1.0, user_agent: str = UA, offline: bool = False):
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.delay_s = delay_s
        self.user_agent = user_agent
        self.offline = offline
        self._made_request = False

    def cache_path(self, url: str) -> Path:
        return self.cache_dir / f"{hashlib.sha1(url.encode('utf-8')).hexdigest()}.html"

    def get(self, url: str, refresh: bool = False) -> str:
        """refresh=True: кэштэй ч дахин татна (явагдаж буй улирлын хуудсанд). Offline үед кэшийг л уншина."""
        _check_allowed(url)
        path = self.cache_path(url)
        if path.exists() and (self.offline or not refresh):
            return path.read_text(encoding="utf-8")
        if self.offline:
            raise CacheMiss(url)
        if self._made_request:
            time.sleep(self.delay_s)
        resp = requests.get(url, headers={"User-Agent": self.user_agent}, timeout=30)
        self._made_request = True
        resp.raise_for_status()
        resp.encoding = "utf-8"
        path.write_text(resp.text, encoding="utf-8")
        return resp.text
