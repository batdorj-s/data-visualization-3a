import re
from datetime import date, datetime

from bs4 import BeautifulSoup

MONTHS = {m: i for i, m in enumerate(["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"], 1)}
STAGES = ("Playoffs", "Finals")
BOX_COLS = ["MIN", "PTS", "REB", "AST", "STL", "BLK", "FG", "TP", "FT", "TOV", "PF"]
MADE_ATT = {"FG", "TP", "FT"}


def _soup(html: str) -> BeautifulSoup:
    return BeautifulSoup(html, "lxml")


def _int(s: str | None) -> int | None:
    if s is None:
        return None
    s = s.strip()
    return int(s) if re.fullmatch(r"-?\d+", s) else None


def _slug(href: str | None, prefix: str) -> str | None:
    if href and href.startswith(prefix):
        return href[len(prefix):].split("?", 1)[0].strip("/")
    return None


def _card_date(li, month: str) -> str:
    section = li.find_parent("section")
    label = next(section.stripped_strings)  # "Sun 4 Jan"
    m = re.fullmatch(r"\w{3} (\d{1,2}) (\w{3})", label.strip())
    if not m:
        raise ValueError(f"Огноо танигдсангүй: {label!r}")
    year = int(month[:4])
    return date(year, MONTHS[m.group(2)], int(m.group(1))).isoformat()


def parse_schedule(html: str, month: str) -> list[dict]:
    main = _soup(html).find("main")
    rows = []
    for li in main.find_all("li"):
        teams = [a for a in li.find_all("a", href=True) if a["href"].startswith("/en/teams/")]
        if len(teams) < 2:
            continue
        strings = list(li.stripped_strings)
        home_name = next(teams[0].stripped_strings)
        away_name = next(teams[1].stripped_strings)
        game_link = li.find("a", href=re.compile(r"^/en/games/\d+$"))
        played = "–" in strings and game_link is not None
        home_pts = away_pts = None
        if played:
            dash = strings.index("–")
            home_pts, away_pts = _int(strings[dash - 1]), _int(strings[dash + 1])
        stage = next((s for s in strings if s in STAGES), "Regular season")
        venue = strings[strings.index(home_name) - 1]
        rows.append({
            "game_id": int(game_link["href"].rsplit("/", 1)[1]) if played else None,
            "date": _card_date(li, month),
            "status": "Final" if played else "Scheduled",
            "stage": stage,
            "venue_raw": venue,
            "home_name": home_name,
            "away_name": away_name,
            "home_team_slug": _slug(teams[0]["href"], "/en/teams/"),
            "away_team_slug": _slug(teams[1]["href"], "/en/teams/"),
            "home_pts": home_pts,
            "away_pts": away_pts,
        })
    return rows


STAT_COLS = ["GP", "MIN", "PPG", "RPG", "APG", "SPG", "BPG", "PF", "FG_pct", "TP_pct", "EFF"]
POSITIONS = {"PG", "SG", "SF", "PF", "C"}


def _float(s: str | None) -> float | None:
    if s is None:
        return None
    s = s.strip()
    return float(s) if re.fullmatch(r"-?\d+(?:\.\d+)?", s) else None


def parse_player_stats(html: str) -> list[dict]:
    table = _soup(html).find("main").find("table")
    rows = []
    for tr in table.find("tbody").find_all("tr"):
        cells = [c.get_text(" ", strip=True) for c in tr.find_all(["td", "th"])]
        link = tr.find("a", href=re.compile(r"^/en/players/"))
        row = {
            "rank": _int(cells[0]),
            "player_name": cells[1],
            "player_slug": _slug(link["href"] if link else None, "/en/players/"),
            "team_name": cells[2],
        }
        for col, raw in zip(STAT_COLS, cells[3:]):
            row[col] = _int(raw) if col == "GP" else _float(raw)
        rows.append(row)
    return rows


def parse_player_profile(html: str, player_slug: str) -> dict:
    main = _soup(html).find("main")
    strings = list(main.stripped_strings)
    meta = next((s for s in strings if re.search(r"\(\s*(PG|SG|SF|PF|C)\s*\)", s) and re.search(r"20\d\d-20\d\d", s)), "")
    parts = [p.strip() for p in meta.split("·")]
    pos = re.search(r"\((PG|SG|SF|PF|C)\)", meta)
    height = re.search(r"(\d{3})\s*cm", meta)
    birth = next((int(p) for p in parts if re.fullmatch(r"(19|20)\d\d", p)), None)
    season = re.search(r"(20\d\d-20\d\d)", meta)
    number = None
    team_name = None
    if "· #" in strings:
        i = strings.index("· #")
        number = _int(strings[i + 1])
        team_name = strings[i - 1]
    ft = None
    table = main.find("table")
    if table is not None:
        header = [th.get_text(strip=True) for th in table.find("tr").find_all("th")]
        ft_idx = header.index("FT%") if "FT%" in header else None
        body = table.find_all("tr")[1:]
        chosen = next((tr for tr in body if season and tr.get_text(" ", strip=True).startswith(season.group(1))), body[0] if body else None)
        if chosen is not None and ft_idx is not None:
            cells = [c.get_text(" ", strip=True) for c in chosen.find_all(["td", "th"])]
            ft = _float(cells[ft_idx]) if ft_idx < len(cells) else None
    return {
        "player_slug": player_slug,
        "team_name": team_name,
        "number": number,
        "position_raw": parts[0] if parts and pos else None,
        "position": pos.group(1) if pos else None,
        "height_cm": int(height.group(1)) if height else None,
        "birth_year": birth,
        "is_import": "Import player" in parts,
        "season": season.group(1) if season else None,
        "FT_pct": ft,
    }


def _quarters(table) -> tuple[list[int], list[int]]:
    trs = table.find_all("tr")
    labels = [c.get_text(strip=True) for c in trs[0].find_all(["th", "td"])][1:]
    if not labels or labels[-1].lower() != "total":
        raise ValueError(f"Quarter хүснэгтийн толгой танигдсангүй: {labels}")
    sides = []
    for tr in trs[1:3]:
        vals = [_int(td.get_text(strip=True)) for td in tr.find_all("td")]
        sides.append(vals[: len(labels) - 1])
    return sides[0], sides[1]


def _player_row(tr, side: str) -> dict:
    cells = tr.find_all(["th", "td"])
    head = cells[0]
    link = head.find("a", href=True)
    name_el = head.select_one("span.truncate")
    name = name_el.get_text(strip=True) if name_el else next(head.stripped_strings)
    head_strings = list(head.stripped_strings)
    number = _int(head_strings[head_strings.index("#") + 1]) if "#" in head_strings else None
    pos = cells[1].get_text(strip=True) or None
    rest = [c.get_text(" ", strip=True) for c in cells[2:]]
    dnp = any("DNP" in r for r in rest)
    row = {"side": side, "name": name, "player_slug": _slug(link["href"] if link else None, "/en/players/"),
           "number": number, "pos": pos, "dnp": dnp}
    for i, col in enumerate(BOX_COLS):
        raw = None if dnp or i >= len(rest) else rest[i]
        row[col] = raw if col in MADE_ATT else _int(raw)
    return row


def _totals_row(tr, side: str) -> dict:
    vals = [c.get_text(strip=True) for c in tr.find_all(["th", "td"])][2:]
    t = {"side": side}
    for i, col in enumerate(BOX_COLS):
        if col == "MIN":
            continue
        t[col] = vals[i] if col in MADE_ATT else _int(vals[i])
    return t


def _comparison(strings: list[str], label: str) -> tuple[int | None, int | None]:
    if label not in strings:
        return None, None
    i = strings.index(label)
    return _int(strings[i - 1]), _int(strings[i + 1])


def parse_game(html: str, game_id: int) -> dict:
    soup = _soup(html)
    title = soup.title.get_text(strip=True)
    m = re.fullmatch(r"(.+?) (\d+):(\d+) (.+?) \| MBA", title)
    if not m:
        raise ValueError(f"Гарчиг танигдсангүй: {title!r}")
    main = soup.find("main")
    strings = list(main.stripped_strings)
    text = " ".join(strings)
    season = re.search(r"\b(20\d\d-20\d\d)\b", text)
    when = re.search(r"(\d{1,2} \w{3} \d{4}) · (\d{1,2}:\d{2}) · ([^·]+?) (?:" + re.escape(m.group(4)) + "|Score by quarter)", text)
    tables = main.find_all("table")
    home_q, away_q = _quarters(tables[0])

    team_totals, players = [], []
    oreb = _comparison(strings, "Offensive rebounds")
    dreb = _comparison(strings, "Defensive rebounds")
    for idx, (side, table) in enumerate(zip(("home", "away"), tables[1:3])):
        for tr in table.find_all("tr")[1:]:
            first = tr.find(["th", "td"])
            if first is None:
                continue
            if first.get_text(strip=True) == "Totals":
                tot = _totals_row(tr, side)
                tot["OREB"], tot["DREB"] = oreb[idx], dreb[idx]
                team_totals.append(tot)
            elif first.find("a", href=True) or "#" in first.get_text():
                players.append(_player_row(tr, side))

    return {
        "game_id": game_id,
        "season": season.group(1) if season else None,
        "date": datetime.strptime(when.group(1), "%d %b %Y").date().isoformat() if when else None,
        "time": when.group(2) if when else None,
        "venue_raw": when.group(3).strip() if when else None,
        "home_name": m.group(1),
        "away_name": m.group(4),
        "home_pts": int(m.group(2)),
        "away_pts": int(m.group(3)),
        "quarters": {"home": home_q, "away": away_q},
        "team_totals": team_totals,
        "players": players,
    }
