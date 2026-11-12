# MBA лигийн гүйцэтгэлийн шинжилгээ — Хэрэгжүүлэх төлөвлөгөө

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** MBA лигийн 2025-26 ба 2026-27 улирлын өгөгдлийг татаж, цэвэрлэх, статистик, Pareto ба тодорхой бус байдлын дүрслэл, ML, интерактив dashboard, Word/PowerPoint тайланг spec-ийн дагуу бүтээх.

**Architecture:** `mba_analysis/src/` дотор цэвэр (pure) функцүүдтэй модулиуд байна. Дараалал: fetch → parse → clean → features → analysis/models → charts. Notebook-ууд зөвхөн эдгээр функцийг дуудна. Dashboard нь урьдчилан тооцоолсон parquet-ийг уншина. Тест бүр бодит HTML fixture эсвэл гараар тооцсон жижиг DataFrame дээр ажиллана.

**Tech Stack:** Python 3.13, pandas, numpy, requests, beautifulsoup4 + lxml, scipy, scikit-learn, matplotlib, seaborn, plotly, networkx, streamlit 1.57 (`st.fragment`, `AppTest`), pyarrow, joblib, python-docx, python-pptx, docx2pdf, pytest.

**Spec:** [`docs/superpowers/specs/2026-11-12-mba-analysis-design.md`](../specs/2026-11-12-mba-analysis-design.md). Судалгаа: [`docs/research/2026-11-12-data-sources.md`](../../research/2026-11-12-data-sources.md).

## Global Constraints

- Бүх команд `mba_analysis/` хавтаснаас ажиллана. Тест: `.venv/bin/python -m pytest`.
- Санамсаргүй тоонуудын seed = **42** (bootstrap, K-Means, тоглолтын чиглэл, RF).
- HTTP: User-Agent `"Mozilla/5.0 (student project)"`, хүсэлт хоорондын хүлээлт ≥ **1.0 с**. `/api`, `/admin` руу хандахгүй. **asia-basket.com-оос хэзээ ч автоматаар татахгүй.**
- Түүхий HTML кэш `data/raw/html/`, тестийн fixture `tests/fixtures/html/` хоёулаа git-д орохгүй.
- Шинжилгээний шүүлтүүр: GP ≥ **5**. K-Means-д нийт MIN ≥ **150**.
- Bootstrap: тоглолтоор cluster bootstrap, **2,000** давталт, percentile 95% CI. Загварын метрик: 1,000 давталт.
- Elo: K = **20**, эхлэл **1500**, талбайн давуу тал **0**, улирлын шилжилт `0.75·Elo + 0.25·1500`. Залгамжлагч баг эх сурвалжгүй бол **1500**-аас эхэлнэ.
- Pythagorean экспонент: суурь **13.91**, мөн лигийн датад тааруулсан утгыг тооцно.
- Графикийн бүх бичвэр монгол хэлээр. Палитр Okabe-Ito: Import `#D55E00`, Дотоод `#0072B2`, саармаг `#9E9E9E`. Байрлал: PG `#E69F00`, SG `#56B4E9`, SF `#009E73`, PF `#CC79A7`, C `#0072B2`. Ялгах өнгө ≤ 6.
- Фонт: Arial, олдохгүй бол DejaVu Sans. Экспорт: PNG 300 dpi + SVG, 16 см өргөн. Нэрлэх загвар: `F01_ppg_hist.png`.
- Caption-ий загвар: `"Эх сурвалж: MBA статистикийн систем, 2026-11-12"` + тодорхой бус байдлыг хэрхэн тооцсон нэг өгүүлбэр.
- Dashboard-ийн хугацааны зорилт: анх ачаалах < 3 с, шүүлтүүрийн шинэчлэлт median < 300 мс, ялалтын магадлалын тооцоолуур < 100 мс.
- Тайлан, слайдын тайлбар бичвэр нь **ноорог** байна. Шар өнгөөр тодруулж, "Өөрийн үгээр дахин бичих" гэсэн шошготой. Эцсийн бичвэрийг хэрэглэгч бичнэ.
- Commit бүр `Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>` мөрөөр төгсөнө. Файлыг нэрээр нь stage хийнэ.

## Review Focus

1. **Тоглогдоогүй тоглолт** (2026-27 улирлын "Scheduled"/"Tomorrow" картууд) нь датад орох ёсгүй. `scrape` зөвхөн `status == "Final"` тоглолтыг татна. Тест: Task 2 `test_parse_schedule_skips_unplayed`.
2. **Тэгд хуваах:** FGA = 0, TPA = 0, POSS = 0, шидэлт 0. Хариу нь `inf` биш `NaN` байх ёстой бөгөөд funnel plot-оос хасагдана. Тест: Task 7 `test_rates_zero_attempts_are_nan`.
3. **Сунгалт (OT):** quarter-ийн хүснэгтэд 5+ багана байж болно. Нийт оноо OT-оо оруулсан байх ёстой. Тест: Task 2 `test_parse_game_overtime_columns`.
4. **Улирлын дундуур баг сольсон тоглогч:** (player, season)-д 2 мөр байж болно. Нэгтгэхдээ нэг мөр болгохгүй, `team_key`-ээр ялгана. Тест: Task 6 `test_dedupe_keeps_traded_player_rows`.
5. **Dashboard-ийн шүүлтүүр хоосон үр дүн өгөх.** Жишээ нь баг + байрлал + GP ≥ 25 хослол. Алдаа гаргахгүй, "Сонгосон шүүлтүүрт тохирох өгөгдөл алга" гэсэн мэдэгдэл харуулна. Тест: Task 20 `test_empty_filter_shows_message`.

---

## Файлын бүтэц

```
mba_analysis/
├── pyproject.toml                 pytest тохиргоо (pythonpath=".", testpaths=["tests"])
├── requirements.txt               (байгаа) + pytest, docx2pdf
├── tools/fetch_fixtures.py        тестийн HTML/wikitext fixture-уудыг татах
├── src/
│   ├── fetch.py                   Fetcher: кэш + throttle + offline горим
│   ├── parse_mba.py               schedule/game/stats/profile HTML parser
│   ├── scrape.py                  MBA-ийн бүх датаг data/raw/*.csv болгох CLI
│   ├── wiki.py                    Wikipedia wikitext parser + geojson татах
│   ├── names.py                   нэр normalize, тааруулах
│   ├── clean.py                   C1–C11, CleaningLog, run_cleaning CLI
│   ├── features.py                rate/four factors/ratings/ангилал/pythag
│   ├── elo.py                     Elo
│   ├── uncertainty.py             cluster bootstrap, Wilson, Fisher
│   ├── analysis.py                танилцуулах статистик, H1–H5
│   ├── models.py                  K-Means, win model, тайлбар загвар, pythag fit
│   ├── style.py                   палитр, фонт, caption, save_figure
│   ├── chart_qa.py                графикийн чанарын шалгалт
│   ├── charts/
│   │   ├── distribution.py        F1 F2 F7 F8 F9 U4
│   │   ├── relation.py            F3 F13 U1
│   │   ├── timeline.py            F4(+U3) F10
│   │   ├── comparison.py          F5 F6 P1 P2 U2
│   │   ├── geo_network.py         F11 F12
│   │   ├── summary.py             U5 U9
│   │   └── ml.py                  F14 U6 U8 P3
│   ├── make_figures.py            бүх графикийг figures/-д гаргах CLI + chart_qa лог
│   ├── build_dashboard_data.py    dashboard/data/*.parquet, models/*.joblib
│   ├── blueprint.py               архитектур + 2 wireframe
│   ├── report_docx.py             Word тайлан
│   └── report_pptx.py             PowerPoint
├── data/raw/manual/               гараар бэлтгэсэн: team_aliases.csv, team_meta.csv, (сонголт) standings_2024_25.csv
├── data/raw/geo/mng_adm1.geojson  geoBoundaries (ODbL)
├── notebooks/01_collect … 06_ml.ipynb
├── dashboard/
│   ├── app.py  plots.py  data_access.py  requirements.txt
│   └── views/ overview.py players.py teams.py ml.py quality.py about.py
├── tools/time_dashboard.py
└── tests/  test_*.py, fixtures/ (html/ ба wiki/ нь gitignore)
```

---

## Үе шат A — Өгөгдөл цуглуулах

### Task 1: Төслийн орчин ба `Fetcher`

**Files:**
- Create: `mba_analysis/pyproject.toml`, `mba_analysis/src/__init__.py`, `mba_analysis/src/fetch.py`, `mba_analysis/tests/test_fetch.py`
- Modify: `mba_analysis/requirements.txt` (`pytest>=8.4`, `docx2pdf>=0.1.8` нэмнэ), `.gitignore` (`mba_analysis/tests/fixtures/html/`, `mba_analysis/tests/fixtures/wiki/`, `mba_analysis/.venv/` нэмнэ)

**Interfaces:**
- Produces:
  - `UA: str`
  - `class CacheMiss(Exception)`
  - `class Fetcher(cache_dir: Path, delay_s: float = 1.0, user_agent: str = UA, offline: bool = False)` ба түүний арга `get(url: str) -> str`. Кэшийн файл: `cache_dir / f"{sha1(url)}.html"`. Offline горимд кэш байхгүй бол `CacheMiss` өгнө.

- [ ] **Step 1: Орчин бэлдэх**

```bash
cd mba_analysis && python3 -m venv .venv && .venv/bin/pip install -r requirements.txt
```
Expected: алдаагүй дуусна, `.venv/bin/python -c "import streamlit, docx, pptx"` ажиллана.

- [ ] **Step 2: Унах тест бичих** (`tests/test_fetch.py`). `requests.get`-ийг monkeypatch хийж дуудлагыг тоолно, `time.sleep`-ийг монкипатчаар бүртгэнэ.
  - `test_get_uses_cache_on_second_call`: нэг URL-ийг 2 удаа дуудахад сүлжээний дуудлага = 1, хоёр дахь удаад ижил текст буцна.
  - `test_offline_cache_miss_raises`: `offline=True`, кэш хоосон үед `CacheMiss` өгнө.
  - `test_throttle_between_network_calls`: 2 өөр URL дуудахад `sleep`-д нийт ≥ 1.0 с бүртгэгдэнэ.
  - `test_sends_user_agent`: header `User-Agent == "Mozilla/5.0 (student project)"`.
  - `test_refuses_disallowed_hosts`: `https://www.asia-basket.com/...` эсвэл `https://mongolia.basketball/api/...` руу хандахад `ValueError` өгнө.
- [ ] **Step 3:** `.venv/bin/python -m pytest tests/test_fetch.py -v` → FAIL (`ModuleNotFoundError: src.fetch`)
- [ ] **Step 4: `src/fetch.py`-г хэрэгжүүлэх.** `requests.get(url, headers=..., timeout=30)` ашиглана. `raise_for_status()` дуудна. Кэшийг UTF-8-аар бичнэ. Хориотой host/path-ийг `urllib.parse`-ээр шалгана.
- [ ] **Step 5:** `.venv/bin/python -m pytest tests/test_fetch.py -v` → 5 PASS
- [ ] **Step 6: Commit**

```bash
git add .gitignore mba_analysis/pyproject.toml mba_analysis/requirements.txt mba_analysis/src/__init__.py mba_analysis/src/fetch.py mba_analysis/tests/test_fetch.py
git commit -m "feat(mba): кэштэй, хурд хязгаарласан Fetcher"
```

### Task 2: Хуваарь ба box score-ийн parser

**Files:**
- Create: `mba_analysis/tools/fetch_fixtures.py`, `mba_analysis/src/parse_mba.py`, `mba_analysis/tests/test_parse_games.py`

**Interfaces:**
- Consumes: `Fetcher` (Task 1)
- Produces:
  - `parse_schedule(html: str, month: str) -> list[dict]`. Түлхүүрүүд: `game_id:int, date:str(YYYY-MM-DD), status:str, stage:str ∈ {"Regular season","Playoffs","Finals"}, venue_raw:str, home_name:str, away_name:str, home_pts:int|None, away_pts:int|None`.
  - `parse_game(html: str, game_id: int) -> dict`. Түлхүүрүүд:
    - `game_id, season:str("2025-2026"), date, time, venue_raw, home_name, away_name, home_pts, away_pts`
    - `quarters: {"home": list[int], "away": list[int]}`
    - `team_totals: list[dict]` (side, PTS, REB, AST, STL, BLK, FG, TP, FT, TOV, PF, OREB, DREB)
    - `players: list[dict]` (side, name, number, pos, MIN, PTS, REB, AST, STL, BLK, FG, TP, FT, TOV, PF, dnp:bool)
    - FG/TP/FT нь `"24-70"` хэлбэрийн мөр хэвээрээ үлдэнэ. Задлахыг C5 хийнэ.

- [ ] **Step 1: Fixture татах скрипт** `tools/fetch_fixtures.py`. `Fetcher`-ээр дараах хуудсуудыг `tests/fixtures/html/<name>.html` болгон хадгална:
  - `game_141` = `/en/games/141`
  - `schedule_2025_26_2026_01` = `/en/competitions/league/schedule?season=c1a0488c-31a5-429d-8254-3b27aa45e702&month=2026-01`
  - `schedule_2025_26_2026_03` (month=2026-03)
  - `schedule_2026_27_2026_11` = `?season=ac48cf7e-0249-4450-a2ee-42fc7b97dc16&month=2026-11`
  - Task 3-т хэрэгтэй хуудсууд: `stats_2025_26` = `/en/stats?competition=league&view=players&season=c1a0488c-…`, `profile_byron_wesley` = `/en/players/byron-wesley`, `profile_narangerel_batbayar` = `/en/players/narangerel-batbayar`
  - Ажиллуулах: `.venv/bin/python tools/fetch_fixtures.py` → 7 файл үүснэ.
- [ ] **Step 2: Унах тест бичих.** Fixture байхгүй бол `pytest.skip` хийнэ.
  - `test_parse_schedule_jan`: `len == 35`. `game_id == 141` мөрийн утгууд:
    - `date == "2026-01-04"`, `stage == "Regular season"`, `status == "Final"`
    - `home_name == "XAC BRONCOS"`, `away_name == "SELENGE BODONS"`, `home_pts == 77`, `away_pts == 69`, `venue_raw == "М Банк арена"`
  - `test_parse_schedule_playoff_stage`: 2026-03 fixture-т `stage == "Playoffs"` бүхий мөр ≥ 1. 2026-04-ийн "Finals" карт ч ижил логикоор танигдана.
  - `test_parse_schedule_skips_unplayed` (Review Focus #1): 2026-11 fixture-т `status != "Final"` мөрүүдийн `home_pts is None`.
  - `test_parse_game_141_header`:
    - `season == "2025-2026"`, `date == "2026-01-04"`, `home_name == "XAC BRONCOS"`, `away_pts == 69`
    - `quarters == {"home": [18, 20, 20, 19], "away": [17, 23, 16, 13]}`
  - `test_parse_game_141_totals`:
    - home: `PTS 77, REB 50, AST 19, STL 6, BLK 3, FG "24-70", TP "8-28", FT "21-24", TOV 11, PF 19, OREB 17, DREB 33`
    - away: `PTS 69, REB 38, OREB 13, DREB 25, FG "21-68", TP "8-33", FT "19-25", TOV 13`
  - `test_parse_game_141_players`: `ALTANGEREL Azbayar` мөр нь `pos "C", MIN 32, PTS 12, REB 13, FG "5-12", TP "0-1", FT "2-2"`. DNP тоглогчид `dnp is True`, статистик нь `None`.
  - `test_parse_game_overtime_columns` (Review Focus #3): жижиг синтетик HTML-ийн quarter хүснэгт `Q1 Q2 Q3 Q4 OT TOTAL` гэсэн толгойтой. Үр дүнд `len(quarters["home"]) == 5` бөгөөд `sum(quarters["home"]) == home_pts`.
- [ ] **Step 3:** `.venv/bin/python -m pytest tests/test_parse_games.py -v` → FAIL
- [ ] **Step 4: `src/parse_mba.py`-ийн `parse_schedule`, `parse_game`-ийг хэрэгжүүлэх.**
  - Хуваарь: `a[href^="/en/games/"]`-ийн хамгийн ойрын `li` нь карт, `li.find_parent("section")`-ийн эхний мөр нь огноо ("Sun 4 Jan"). Он нь `month`-оос авна.
  - Картын мөрүүдийн дараалал: `status, [stage], venue, home, abbr, pts, "–", pts, away, abbr…`.
  - Game хуудас: `<title>` нь "HOME 77:69 AWAY | MBA". Огноо "4 Jan 2026 · 16:10 · venue". Season-ийг breadcrumb-аас авна.
  - Box score хүснэгт 2, quarter хүснэгт 1. OREB/DREB-ийг "Offensive rebounds"/"Defensive rebounds" шошгын хоёр талын тооноос (home, away) авна.
- [ ] **Step 5:** `.venv/bin/python -m pytest tests/test_parse_games.py -v` → 7 PASS
- [ ] **Step 6: Commit** — `tools/fetch_fixtures.py src/parse_mba.py tests/test_parse_games.py`, мессеж `"feat(mba): хуваарь ба box score parser"`.

### Task 3: Тоглогчийн статистик ба профайлын parser

**Files:**
- Modify: `mba_analysis/src/parse_mba.py`
- Create: `mba_analysis/tests/test_parse_players.py`

**Interfaces:**
- Produces:
  - `parse_player_stats(html: str) -> list[dict]`. Түлхүүрүүд: `rank, player_name, player_slug, team_name, GP:int, MIN, PPG, RPG, APG, SPG, BPG, PF, FG_pct, TP_pct, EFF` (float).
  - `parse_player_profile(html: str, player_slug: str) -> dict`. Түлхүүрүүд: `player_slug, team_name, number:int|None, position_raw, position ∈ {"PG","SG","SF","PF","C"}|None, height_cm:int|None, birth_year:int|None, is_import:bool, FT_pct:float|None`.

- [ ] **Step 1: Унах тест бичих**
  - `test_stats_2025_26_rows`: `len == 171`. Эхний мөр нь `player_name "BYRON Wesley", player_slug "byron-wesley", team_name "BUREN SCORE MONGOLIANS", GP 24, MIN 32.5, PPG 27.9, RPG 5.4, APG 3.8, FG_pct 50.3, TP_pct 31.4, EFF 25.5`.
  - `test_stats_distinct_teams`: `team_name`-ийн давтагдашгүй утга 10.
  - `test_profile_import`: `byron-wesley` нь `position "PG", height_cm 196, birth_year 1992, is_import True`. FT_pct нь float (fixture-т 85.1).
  - `test_profile_domestic`: `narangerel-batbayar` нь `position "SG", height_cm 193, birth_year 1995, is_import False, team_name "Selenge Bodons", number 9`.
  - `test_profile_missing_fields`: "cm" болон он байхгүй синтетик HTML дээр `height_cm is None`, `birth_year is None` (алдаа өгөхгүй).
- [ ] **Step 2:** `.venv/bin/python -m pytest tests/test_parse_players.py -v` → FAIL
- [ ] **Step 3: Хэрэгжүүлэх.**
  - Статистик: `table tbody tr`-ийн нүд бүрийг уншина. Slug нь мөр доторх `a[href^="/en/players/"]`.
  - Профайл: "Байрлал (XX) · NNN cm · YYYY · [Import player] · season" мөрийг regex-ээр задална. FT%-ийг "SEASON AVERAGES" хүснэгтийн сүүлийн баганаас авна.
- [ ] **Step 4:** `.venv/bin/python -m pytest tests/test_parse_players.py -v` → 5 PASS
- [ ] **Step 5: Commit** — `"feat(mba): тоглогчийн статистик ба профайлын parser"`

### Task 4: `scrape` — MBA-ийн бүх түүхий датаг CSV болгох

**Files:**
- Create: `mba_analysis/src/scrape.py`, `mba_analysis/tests/test_scrape.py`
- Output (commit хийнэ): `data/raw/schedule.csv`, `games_raw.csv`, `team_games_raw.csv`, `player_games_raw.csv`, `players_season_raw.csv`, `players_profile_raw.csv`, `SNAPSHOT.md`

**Interfaces:**
- Consumes: `Fetcher`, `parse_*` (Tasks 1–3)
- Produces:
  - `SEASONS: dict[str, tuple[str, list[str]]]`:
    - `"2025-2026"` → (`c1a0488c-31a5-429d-8254-3b27aa45e702`, `["2025-10" … "2026-04"]`)
    - `"2026-2027"` → (`ac48cf7e-0249-4450-a2ee-42fc7b97dc16`, `["2026-10", "2026-11"]`)
  - `scrape_all(raw_dir: Path, fetcher: Fetcher) -> dict[str, int]`: файл тус бүрийн мөрийн тоог буцаана.
  - CLI: `python -m src.scrape [--offline]`
  - CSV-ийн баганууд нь parser-ийн түлхүүрүүд + `season`, `game_id`, `side`.

- [ ] **Step 1: Унах тест бичих.** `tmp_path` кэш дотор fixture-уудыг URL-ийн sha1 нэрээр байрлуулж, offline Fetcher ашиглана. `SEASONS`-ийг monkeypatch хийж зөвхөн `"2025-2026": (id, ["2026-01"])` болгоно. Fixture-д байхгүй game хуудсуудын хувьд `CacheMiss`-ийг барьж алгасна, тоог лог-д бичнэ.
  - `test_scrape_offline_writes_csvs`: 7 файл бүгд үүснэ. `games_raw.csv`-д `game_id == 141` мөр байна. `team_games_raw.csv`-д game 141-ийн мөр 2 (home, away). `SNAPSHOT.md` нь "2026-" гэсэн огноо болон season ID-уудыг агуулна.
  - `test_scrape_only_final_games`: status ≠ Final картуудын game хуудсыг Fetcher рүү дуудаагүй.
- [ ] **Step 2:** `.venv/bin/python -m pytest tests/test_scrape.py -v` → FAIL
- [ ] **Step 3: Хэрэгжүүлэх.**
  - Дараалал: хуваарь → Final game ID-уудаас давхардлыг хасах → game хуудас → статистикийн хуудас (2 улирал) → статистикт гарсан бүх slug-ийн профайл.
  - Явцыг `print` хийнэ. Нийт хүсэлт ~550 тул ~10 минут болно.
  - `SNAPSHOT.md`-д огноо (ISO), season ID-ууд, файл бүрийн мөрийн тоог бичнэ.
- [ ] **Step 4:** `.venv/bin/python -m pytest tests/test_scrape.py -v` → PASS
- [ ] **Step 5: Бодит татах үйлдлийг background-д ажиллуулах:** `.venv/bin/python -m src.scrape`
  - Expected: games_raw ≥ 240, players_season_raw ≈ 318, players_profile_raw ≈ 290–318 (давхардсан тоглогч цөөрүүлнэ).
  - Дахин `--offline` ажиллуулахад ижил тоо гарна.
- [ ] **Step 6: Commit** — `src/scrape.py tests/test_scrape.py data/raw/*.csv data/raw/SNAPSHOT.md`, `"feat(mba): MBA түүхий дата татав (snapshot 2026-11-xx)"`

### Task 5: Wikipedia, FIBA, газрын зураг, гараар бэлтгэх файлууд

**Files:**
- Create: `mba_analysis/src/wiki.py`, `mba_analysis/tests/test_wiki.py`, `data/raw/manual/team_aliases.csv`, `data/raw/manual/team_meta.csv`, `data/raw/geo/mng_adm1.geojson`
- Output: `data/raw/standings_2023_24_raw.csv`, `champions_raw.csv`, `team_cities_raw.csv`, `national_team_raw.csv`

**Interfaces:**
- Produces:
  - `fetch_wikitext(title: str, fetcher: Fetcher) -> str`. URL: `https://en.wikipedia.org/w/index.php?title=<title>&action=raw`.
  - `parse_sports_table(wt: str) -> DataFrame[code, team_raw, W, L, PF, PA]`
  - `parse_champions(wt: str) -> DataFrame[season, champion, runner_up]`
  - `parse_current_teams(wt: str) -> DataFrame[team_raw, home_city]`
  - `parse_fiba_roster(wt: str) -> DataFrame[num, first, last, pos, birth_date, club, club_country, captain:bool]`
  - `build_wiki_raw(raw_dir: Path, fetcher: Fetcher) -> None`. CLI: `python -m src.wiki`.
  - `team_aliases.csv`-ийн баганууд: `raw_name, season, team_key, canonical_name, successor_of, source`
  - `team_meta.csv`-ийн баганууд: `team_key, canonical_name, home_city, aimag, region ∈ {"Улаанбаатар","Орон нутаг","Тодорхойгүй"}, lat, lon, source`

- [ ] **Step 1: Fixture нэмэх.** `tools/fetch_fixtures.py`-д 3 wikitext (`The_League_(Mongolia)`, `2023–24_The_League_season`, `Mongolia_men's_national_basketball_team`)-ийг `tests/fixtures/wiki/*.txt` болгон хадгалах кодыг нэмж ажиллуулна.
- [ ] **Step 2: Унах тест бичих**
  - `test_standings_2023_24`: 13 мөр. `team_raw == "Erdenet Miners"` → `W 19, L 4, PF 1878, PA 1693`. `"Shutis Sharks"` → `W 5, L 17`. `[[...]]` холбоосыг цэвэрлэнэ (`"[[Bishrelt Metal]]"` → `"Bishrelt Metal"`).
  - `test_fiba_roster`: 12 мөр. `num 8` → `first "Erdenetsogt", last "Ochirbat", pos "G", birth_date "1995-01-14", club "BCH Knights", captain True`. `num 7`-ийн `club_country == "Japan"`.
  - `test_current_teams`: `"Darkhan United" → "Darkhan"`, `"Khovd Falcons" → "Khovd"` (`[[Darkhan (city)|Darkhan]]` загварыг цэвэрлэнэ).
  - `test_champions_has_1994`: `season "1994–95"`-ийн champion нь `"1+11"`.
- [ ] **Step 3:** FAIL → `src/wiki.py`-г regex-ээр хэрэгжүүлнэ. `{{Sports table}}`-ийн `name_XXX`, `win_XXX`, `loss_XXX`, `pf_XXX`, `pa_XXX` талбаруудыг уншина. `{{FIBA player|...}}`-ийн `key = value` хосуудыг задална. → PASS.
- [ ] **Step 4: Бодит татах:** `.venv/bin/python -m src.wiki` → 4 CSV. Газрын зургийг татах:

```bash
curl -sL -o data/raw/geo/mng_adm1.geojson "https://github.com/wmgeolab/geoBoundaries/raw/9469f09/releaseData/gbOpen/MNG/ADM1/geoBoundaries-MNG-ADM1_simplified.geojson"
```
  Expected: 22 feature (21 аймаг + Улаанбаатар), файл ≤ 1 MB. Лиценз ODbL тул эх сурвалжийг README болон caption-д заана.
- [ ] **Step 5: Гараар бэлтгэх файлууд**
  - `team_aliases.csv`: `schedule.csv`, `players_season_raw.csv`, `standings_2023_24_raw.csv`-д гарсан бүх багийн нэрийг багтаана.
    - Тодорхой mapping: `XAC BRONCOS`/`Khasin Khuleguud` → `khasin_khuleguud`, `IHC Apes` → `sg_apes`, `BCH Garid` → `bch_knights`, `Erdenet Miners`/`OMNI ERDENET MINERS` → `erdenet_miners`. Том/жижиг үсгийн хувилбаруудыг нэг key-д оруулна.
    - `successor_of`-ийг зөвхөн эх сурвалжтай үед бөглөнө (жишээ нь баг нэрээ сольсон тухай MBA-ийн мэдээ). Эх сурвалжгүй бол хоосон үлдээнэ.
  - `team_meta.csv`: гэр хотыг Wikipedia "Current teams" хүснэгт эсвэл MBA-ийн мэдээнээс авч, `source`-д URL-ийг бичнэ. Олдоогүй бол `region = "Тодорхойгүй"`, lat/lon хоосон.
- [ ] **Step 6: Commit** — `"feat(mba): Wikipedia/FIBA дата, газрын зураг, багийн нэрийн хүснэгт"`

---

## Үе шат B — Цэвэрлэгээ ба шинэ хувьсагч

### Task 6: Нэр тааруулах ба цэвэрлэгээ (C1–C11)

**Files:**
- Create: `mba_analysis/src/names.py`, `mba_analysis/src/clean.py`, `mba_analysis/tests/test_names.py`, `mba_analysis/tests/test_clean.py`
- Output: `data/processed/{players_season,players_profile,games,team_games,player_games,standings_hist,national_team,champions,team_meta}.csv`, `reports/{cleaning_log,missing,name_matches,ppg_validation}.csv`

**Interfaces:**
- Produces (`names.py`):
  - `normalize(s: str) -> str`: NFKC, жижиг үсэг, цэг/таслалыг хасна, зураасыг үлдээнэ, олон зайг нэг болгоно.
  - `split_mba_name(name: str) -> tuple[str, str]`: эхний ТОМ ҮСГЭН token-ууд нь овог. `"DAVIS MCMURRIN Gage Andrew"` → `("davis mcmurrin", "gage andrew")`.
  - `same_person(a: tuple[str,str], b: tuple[str,str]) -> bool`: овог ижил (normalize-ийн дараа) **бөгөөд** нэр нь нэг нь нөгөөгийнхөө эхлэл (prefix) эсвэл `difflib` ratio ≥ 0.85.
  - `match_names(left: pd.DataFrame, right: pd.DataFrame) -> pd.DataFrame[left_id, right_id, score]`
- Produces (`clean.py`):
  - `class CleaningLog` нь `add(step: str, description: str, rows_before: int, rows_after: int, note: str = "")` ба `to_frame() -> DataFrame` аргатай.
  - `class UnmappedTeamError(ValueError)`
  - `map_teams(df, col, aliases, season_col="season") -> df`: `team_key` баганыг нэмнэ (C1).
  - `normalize_venue(s) -> str`: "М Банк арена" / "M BANK ARENA" → "М Банк Арена".
  - `assign_player_ids(players_season, profiles) -> df`: `player_id` нэмнэ. Улирал хоорондын нэр зөрүүг `same_person` + ижил багаар нэгтгэнэ (C2).
  - `fix_zero_attempt_pct(df) -> df` (C3)
  - `drop_dnp(df) -> df` (C4)
  - `split_made_att(df, cols=("FG","TP","FT")) -> df`: `FGM/FGA/TPM/TPA/FTM/FTA` (Int64) үүсгэнэ (C5).
  - `report_missing(df, cols) -> DataFrame[column, n_missing, pct_missing]` (C6)
  - `dedupe(df, keys) -> df` (C7)
  - `flag_eligible(df, min_gp=5) -> df`: `eligible: bool` (C8)
  - `set_dtypes(df, table: str) -> df` (C9)
  - `validate_ppg(players_season, player_games, tol=0.2) -> DataFrame` (C10)
  - `stage_to_phase(stage) -> str`: "Regular season" → "regular", "Playoffs"/"Finals" → "playoff" (C11)
  - `run_cleaning(raw_dir, out_dir, reports_dir) -> CleaningLog`. CLI: `python -m src.clean`.

- [ ] **Step 1: Унах тест бичих** (`test_names.py`)
  - `same_person(split_mba_name("SCRUBB Jay"), split_mba_name("SCRUBB Jayden Amari")) is True`
  - `same_person(("sandagdorj","binderyaa"), ("sandagdorj","binderiya")) is True` (ratio 0.889)
  - `same_person(split_mba_name("SMITH Kendall"), split_mba_name("SMITH Donovan")) is False`
  - `split_mba_name("HUGLEY IV John Ike") == ("hugley iv", "john ike")`
- [ ] **Step 2: Унах тест бичих** (`test_clean.py`, жижиг синтетик DataFrame-ууд)
  - `test_map_teams_case_variants`: `"SELENGE BODONS"` болон `"Selenge Bodons"` хоёулаа ижил `team_key` авна.
  - `test_map_teams_unmapped_raises`: `"Unknown FC"` → `UnmappedTeamError`, алдааны мессежид нэр нь орсон.
  - `test_zero_attempts_pct_nan`: TPA = 0, TP_pct = 0.0 → NaN. TPA = 3, TP_pct = 0.0 → 0.0 хэвээр.
  - `test_split_made_att`: `"24-70"` → FGM 24, FGA 70. `None` → `<NA>`.
  - `test_drop_dnp_logs_count`: 3 мөрийн 1 нь DNP → 2 мөр үлдэж, log-д `rows_before 3, rows_after 2`.
  - `test_dedupe_keeps_traded_player_rows` (Review Focus #4): ижил (player_id, season), өөр `team_key`-тэй 2 мөр хоёулаа үлдэнэ. Яг давхар мөр 1 болно.
  - `test_stage_to_phase`: дээрх 3 утгыг шалгана. Мэдэгдээгүй утга → `ValueError`.
  - `test_normalize_venue_variants`: 2 хувилбар ижил гаралт өгнө.
  - `test_validate_ppg_flags_gap`: season PPG 20.0, тоглолтын дундаж 19.5 → `flag True` (tol 0.2).
- [ ] **Step 3:** `.venv/bin/python -m pytest tests/test_names.py tests/test_clean.py -v` → FAIL
- [ ] **Step 4:** `src/names.py`, `src/clean.py`-г хэрэгжүүлнэ. `run_cleaning` нь §3-ийн бүх хүснэгтийг бичнэ. `standings_hist`-д 2023-24 (Wikipedia), байвал 2024-25 (manual), 2025-26 ба 2026-27 (`games`-ээс regular season-ий W/L/PF/PA тооцож) оруулна. `national_team`-ийг `same_person`-оор MBA-ийн `player_id`-тай холбоно.
- [ ] **Step 5:** Тестүүд → PASS. Дараа нь `.venv/bin/python -m src.clean` ажиллуулна.
  - Expected: `UnmappedTeamError` гарахгүй (гарвал `team_aliases.csv`-д нэмнэ).
  - `reports/cleaning_log.csv` нь ≥ 11 мөртэй.
  - `name_matches.csv`-ийн бүх хосыг гараар шалгаж, буруу хосыг `data/raw/manual/name_overrides.csv` (`left_id, right_id, decision`)-д тэмдэглэнэ. `assign_player_ids` нь энэ файлыг дагана.
- [ ] **Step 6: Commit** — `"feat(mba): нэр тааруулалт ба C1–C11 цэвэрлэгээ"` (processed CSV, reports, manual файлуудыг оруулна)

### Task 7: Шинэ хувьсагчид ба Elo

**Files:**
- Create: `mba_analysis/src/features.py`, `mba_analysis/src/elo.py`, `mba_analysis/tests/test_features.py`, `mba_analysis/tests/test_elo.py`
- Modify: `src/clean.py` (`run_cleaning`-ийн төгсгөлд `add_all_features`-ийг дуудна)

**Interfaces:**
- Produces (`features.py`). Бүх rate функц тэгд хуваахад `NaN` буцаана, `inf` хэзээ ч буцаахгүй.
  - `per36(stat, minutes)`
  - `ts_pct(pts, fga, fta)`
  - `efg_pct(fgm, tpm, fga)`
  - `possessions(fga, oreb, tov, fta)`
  - `four_factors(team_games: DataFrame) -> DataFrame`: `efg, tov_pct, orb_pct, ftr, poss, ortg, drtg, net` баганыг нэмнэ. Өрсөлдөгчийн мөрийг `game_id`-аар холбоно.
  - `player_season_from_games(player_games) -> DataFrame`: тоглогч-улирлын нийлбэр FGA/FTA/TPA, TS%, per-36.
  - `add_player_categories(df, season_start_year) -> df`: `age, pos_group ∈ {"Guard","Forward","Center"}`, `scorer_tier ∈ {"Бага","Дунд","Өндөр","Од"}` (<5, 5–12, 12–20, ≥20).
  - `pythag(pf, pa, exponent=13.91)`
  - `add_all_features(processed_dir) -> None`: `players_season`-д per-36, TS%, `tpa_rate`, `ftr`, ангиллууд, `is_national` (`national_team.matched_player_id`-оос), `region` (`team_meta`-аас) баганыг нэмнэ. `team_games`-д Four Factors, `games`-д `elo_pre_*` ба `phase` нэмнэ.
- Produces (`elo.py`):
  - `run_elo(games: DataFrame, k=20, init=1500, carry=0.75, successors: dict[str,str] | None = None) -> DataFrame[game_id, home_key, away_key, elo_pre_home, elo_pre_away, elo_post_home, elo_post_away]`. Огноо болон game_id-аар эрэмбэлнэ. `successors`-ийг `team_aliases.csv`-ийн `successor_of`-оос үүсгэнэ.
  - `expected(ra, rb) -> float`

- [ ] **Step 1: Унах тест бичих** (game 141-ийн totals-аар, гараар тооцсон утгууд):
  - home: `efg 0.4000, poss 74.56, tov_pct 0.1475, orb_pct 0.4048, ftr 0.3000, ortg 103.27, drtg 87.34`; `ts_pct(77,70,24) == 0.4779` (abs 1e-4)
  - away: `efg 0.3676, poss 79.0, tov_pct 0.1646, orb_pct 0.2826, ftr 0.2794`
  - `test_rates_zero_attempts_are_nan` (Review Focus #2): `ts_pct(0,0,0)`, `efg_pct(0,0,0)`, `four_factors` нь FGA = 0 мөрөнд NaN; `np.isinf`-ийн нийлбэр 0.
  - `test_categories`: PPG 4.9 → "Бага", 12.0 → "Өндөр", 20.0 → "Од". "PF" → "Forward". birth_year 1995, season 2025 → age 30.
  - `test_pythag_erdenet_2023_24`: `pythag(1878, 1693) == 0.8088` (abs 1e-4)
- [ ] **Step 2: Унах тест бичих** (`test_elo.py`):
  - Тэнцүү 1500 vs 1500, home ялбал → `elo_post_home == 1510.0`
  - 1600 vs 1400, сул баг ялбал хүчтэй баг → `1584.805` (abs 1e-3)
  - Улирлын шилжилт: 1600 → 1575.0. Залгамжлагчгүй шинэ баг → 1500.
  - `elo_pre_*` нь тухайн тоглолтын үр дүнгээс хамаарахгүй: сүүлийн тоглолтын оноог солиход тухайн мөрийн `elo_pre` өөрчлөгдөхгүй.
- [ ] **Step 3:** FAIL → хэрэгжүүлнэ → `.venv/bin/python -m pytest tests/test_features.py tests/test_elo.py -v` PASS
- [ ] **Step 4:** `.venv/bin/python -m src.clean` дахин ажиллуулна. `team_games.csv`-д Four Factors, `games.csv`-д `elo_pre_*` баганууд нэмэгдэнэ. `team_games`-д `inf` 0 байна.
- [ ] **Step 5: Commit** — `"feat(mba): Four Factors, TS%, ангилал, Pythagorean, Elo"`

### Task 8: Тодорхой бус байдлын тооцоолол

**Files:**
- Create: `mba_analysis/src/uncertainty.py`, `mba_analysis/tests/test_uncertainty.py`

**Interfaces:**
- Produces:
  - `class CI(NamedTuple): est: float; lo: float; hi: float`
  - `cluster_bootstrap(df, group_col: str, stat: Callable[[DataFrame], float], n_boot=2000, seed=42, alpha=0.05) -> CI`: `group_col`-ийн утгуудыг (жишээ нь `game_id`) буцаалттайгаар дахин түүвэрлэнэ.
  - `bootstrap_distribution(...) -> np.ndarray`: дээрхтэй ижил, түүврүүдийг буцаана (U4/U6 графикт).
  - `wilson_ci(k: int, n: int, alpha=0.05) -> CI`
  - `fisher_ci(r: float, n: int, alpha=0.05) -> CI`
  - `funnel_limits(p0: float, n: np.ndarray, z: float) -> tuple[np.ndarray, np.ndarray]`: `p0 ± z·sqrt(p0(1−p0)/n)`, [0, 1] хязгаарт тайрна.

- [ ] **Step 1: Унах тест бичих**
  - `wilson_ci(8, 10)` → `lo 0.4902, hi 0.9433`. `wilson_ci(0, 5)` → `lo 0.0, hi 0.4345` (abs 1e-4).
  - `fisher_ci(0.5, 30)` → `lo 0.1704, hi 0.7290` (abs 1e-3).
  - `test_cluster_bootstrap_resamples_groups`: 10 тоглолт, тоглолт бүрт ижил утгатай 5 мөр. Үр дүн нь тоглолтын түвшний bootstrap-тай яг тэнцүү (seed 42). Бүх бүлэг ижил утгатай бол `lo == hi == est`.
  - `test_cluster_bootstrap_deterministic`: ижил seed ижил үр дүн өгнө. `est` нь бүтэн дата дээрх `stat`.
  - `funnel_limits(0.5, np.array([100]), 1.96)` → `(0.402, 0.598)` (abs 1e-3).
- [ ] **Step 2:** FAIL → хэрэгжүүлнэ (numpy vectorized; z-ийг `scipy.stats.norm.ppf`-ээр) → PASS
- [ ] **Step 3: Commit** — `"feat(mba): cluster bootstrap, Wilson, Fisher, funnel хил"`

---

## Үе шат C — Статистик ба дүрслэл

### Task 9: Танилцуулах статистик ба H1, H2, H4, H5

**Files:**
- Create: `mba_analysis/src/analysis.py`, `mba_analysis/tests/test_analysis.py`
- Output: `reports/descriptive_numeric.csv`, `reports/descriptive_categorical.csv`, `reports/descriptive_games.csv`, `reports/hypotheses.csv`

**Interfaces:**
- Consumes: `CI`, `cluster_bootstrap`, `wilson_ci`, `fisher_ci` (Task 8)
- Produces:
  - `describe_numeric(df, cols, by: str | None = None) -> DataFrame`. Баганууд: `variable, group, n, mean, median, mode, std, min, max, q1, q2, q3, iqr, skew`. Олон mode байвал хамгийн бага утгыг авна.
  - `describe_categorical(df, cols) -> DataFrame[variable, value, count, pct, is_mode]`
  - `describe_games(games) -> DataFrame`: нэг тоглолтын нийт оноо, ялалтын онооны зөрүү, quarter бүрийн дундаж оноог `describe_numeric`-ийн баганаар гаргана.
  - `class HypothesisResult(NamedTuple)`: `hid, statement, estimate, ci_lo, ci_hi, null_value, p_value, n, method`
  - `eval_h1(players)`: median(Import PPG) − median(Дотоод PPG). Mann-Whitney U-гийн p утга, rank-biserial r-ийг `method` мөрөнд бичнэ. CI-г тоглогчоор bootstrap хийнэ.
  - `eval_h2(games)`: home-ийн ялалтын хувь, Wilson CI, binomial p (null 0.5).
  - `eval_h4(players)`: Pearson r, Fisher CI. Spearman-ийг `method`-д бичнэ.
  - `eval_h3`, `eval_h5`-ийг Task 16 нэмнэ. Тэр болтол `run_analysis` нь байгаа таамаглалуудыг л бичнэ.
  - `run_analysis(processed_dir, reports_dir) -> None`. CLI: `python -m src.analysis`. Гаралтад `reports/descriptive_games.csv` нэмэгдэнэ.

- [ ] **Step 1: Унах тест бичих**
  - `describe_numeric` нь `[1,2,2,3,10]` дээр `mean 3.6, median 2, mode 2, min 1, max 10, q1 2, q3 3, iqr 1`, skew > 0.
  - `describe_categorical` нь `["PG","PG","C"]` дээр PG `count 2, pct 66.67, is_mode True`.
  - `test_h1_direction`: `eval_h1` нь Import [20,22,25], Дотоод [5,6,8] дээр `estimate == 16`, `ci_lo > 0`, `p_value < 0.1`.
  - `test_h2_fair_coin`: `eval_h2` нь 50 ялалт / 100 дээр `estimate 0.5`, `p_value == 1.0` (abs 1e-9).
  - `test_h4_perfect`: `eval_h4` нь y = 2x (n = 30) дээр `estimate == 1.0`.
  - `test_describe_games`: 2 тоглолт (77–69, 80–70) → нийт онооны mean 148, зөрүүний mean 9.
- [ ] **Step 2:** FAIL → хэрэгжүүлнэ → PASS
- [ ] **Step 3:** `.venv/bin/python -m src.analysis` → 3 CSV. Тоон хувьсагчид: PPG, RPG, APG, MIN, ts_pct, height_cm, age (eligible мөрүүд). Import/дотоодоор салгасан хувилбар ч орно.
- [ ] **Step 4: Commit** — `"feat(mba): танилцуулах статистик, H1/H2/H4"`

### Task 10: Хэв маяг ба графикийн чанарын шалгалт

**Files:**
- Create: `mba_analysis/src/style.py`, `mba_analysis/src/chart_qa.py`, `mba_analysis/tests/test_style_qa.py`

**Interfaces:**
- Produces (`style.py`):
  - `PALETTE: dict[str,str]` (Global Constraints-ийн hex утгууд), `IMPORT_COLORS = {True: "#D55E00", False: "#0072B2"}`, `POS_COLORS`, `NEUTRAL = "#9E9E9E"`
  - `apply_style() -> str`: matplotlib rcParams тохируулж, ашигласан фонтын нэрийг буцаана ("Arial" эсвэл "DejaVu Sans").
  - `finish(fig, title: str, subtitle: str, source: str, n: int, uncertainty_note: str | None = None) -> Figure`: action title, дэд гарчиг (n-ийг оруулна), доод caption-ийг нэмж, `fig._mba_meta` dict-д хадгална.
  - `save_figure(fig, out_dir: Path, name: str) -> tuple[Path, Path]`: PNG 300 dpi + SVG, өргөн 16 см (6.3 инч).
  - `SOURCE_MBA = "Эх сурвалж: MBA статистикийн систем, 2026-11-12"` (snapshot огноог `SNAPSHOT.md`-оос уншина)
- Produces (`chart_qa.py`):
  - `class ChartQAError(AssertionError)`
  - `check(fig) -> dict`: `title, subtitle, source, n`-ийг `fig._mba_meta`-оос шалгана. Бүх `Axes`-ийн x/y label хоосон биш эсэхийг шалгана (`axis("off")` бүхий axes, жишээ нь donut, газрын зургийг алгасна). Ялгаатай өнгөний тоо ≤ 6 (зөвхөн categorical artist, colormap-ийг тооцохгүй). Дутуу зүйл бүрийг жагсаасан `ChartQAError` өгнө.

- [ ] **Step 1: Унах тест бичих**
  - `apply_style()` нь `{"Arial","DejaVu Sans"}`-ийн аль нэгийг буцаана. `"Өөрийн"` гэсэн текст бүхий figure-ийг рендерлэхэд "missing glyph" анхааруулга гарахгүй (`warnings` барина).
  - Бүрэн `finish` хийсэн scatter → `check` OK.
  - `source` дутуу → `ChartQAError`, мессежид `"source"` орсон. `ylabel` хоосон → мессежид `"ylabel"` орсон.
  - 7 өөр өнгөтэй bar → `ChartQAError("colors")`.
  - `save_figure` нь `.png`, `.svg` үүсгэнэ. PNG-ийн өргөн 16 см @ 300 dpi ≈ 1890 px (±5).
- [ ] **Step 2:** FAIL → хэрэгжүүлнэ → PASS
- [ ] **Step 3: Commit** — `"feat(mba): графикийн хэв маяг ба автомат чанарын шалгалт"`

### Task 11: Тархалт ба хамаарлын график (F1 F2 F3 F7 F8 F9 F13 U1 U4)

**Files:**
- Create: `mba_analysis/src/charts/__init__.py`, `src/charts/distribution.py`, `src/charts/relation.py`, `mba_analysis/tests/conftest.py`, `mba_analysis/tests/test_charts_dist_rel.py`

**Interfaces:**
- Consumes: `style.finish`, `chart_qa.check`, `uncertainty.*`, `features.*`
- Produces. Бүгд `Figure` буцаана, оролт нь `data/processed`-ийн DataFrame:
  - `fig_ppg_hist(players)` — F1
  - `fig_ts_box_by_pos(players)` — F2. 1.5·IQR-аас гадуурх цэгт нэр бичнэ.
  - `fig_height_reb(players)` — F3. OLS шугам, r ба Fisher CI-г тэмдэглэнэ.
  - `fig_corr_heatmap(players)` — F7. `RdBu_r`, `vmin=-1, vmax=1`, төв 0.
  - `fig_ppg_violin(players)` — F8. Import/дотоодоор split violin.
  - `fig_pairplot(players, labels)` — F9. `labels` нь cluster label (Task 15). `None` бол байрлалаар будна.
  - `fig_pythagorean(standings)` — F13. y = x шугам, улирлыг өнгө биш хэлбэрээр (marker) ялгана.
  - `fig_ts_funnel(players)` — U1. X = `fga + 0.44·fta` (тэгтэйг хасна), Y = TS%, лигийн жигнэсэн TS% шугам, 95% ба 99.8% хил. Хилээс гадуурх тоглогчдын нэр бичнэ.
  - `fig_raincloud(players, boot_diff: np.ndarray)` — U4. Дээд талд нь raincloud, доор нь median зөрүүний bootstrap тархалт + 95% CI.
- `tests/conftest.py`: `players_small` fixture. Seed 42-оор 120 тоглогч үүсгэнэ, `players_season.csv`-ийн бүх багана, 5 байрлал, Import 30%. Мөн `standings_small` fixture.

- [ ] **Step 1: Унах тест бичих.** Parametrize хийнэ: функц бүр `players_small` дээр `chart_qa.check`-ийг давна. Нэмэлтээр:
  - `fig_ts_funnel`: тэг шидэлттэй 3 тоглогч нэмэхэд алдаа гарахгүй, цэгийн тоо 120 хэвээр.
  - `fig_ppg_hist`: legend-ийн оронд шууд шошго ашиглана, "Import", "Дотоод" текстүүд axes дотор байна.
  - `fig_corr_heatmap`: colormap-ийн `vmin == -1`, `vmax == 1`.
- [ ] **Step 2:** FAIL → хэрэгжүүлнэ → `.venv/bin/python -m pytest tests/test_charts_dist_rel.py -v` PASS
- [ ] **Step 3: Нүдээр шалгах.** `.venv/bin/python -c "..."`-аар бодит `players_season.csv` дээр 9 графикийг `figures/_preview/`-д гаргаж, PNG бүрийг нээж харна. Шалгах зүйлс: давхцсан шошго, хайрцагт багтаагүй текст, кирилл үсэг.
- [ ] **Step 4: Commit** — `"feat(mba): тархалт, хамаарал, funnel, raincloud график"`

### Task 12: Цаг хугацаа ба харьцуулалтын график (F4+U3 F10 F5 F6 P1 P2 U2)

**Files:**
- Create: `src/charts/timeline.py`, `src/charts/comparison.py`, `tests/test_charts_time_cmp.py`
- Modify: `tests/conftest.py` (`games_small`, `team_games_small`, `player_games_small` fixture нэмнэ: 10 баг, 60 тоглолт)

**Interfaces:**
- Produces:
  - `fig_cum_winpct(team_games, highlight: list[str], bands: bool = True)` — F4/U3. Сонгосон багуудыг тод өнгөөр, бусдыг саармагаар зурна. `bands` бол Wilson 50/80/95% зурвасыг alpha 0.35/0.22/0.12-оор зурна.
  - `fig_elo(games, highlight)` — F10. Улирлын заагт босоо тасархай шугам, 2026-27 улиралд "явцын" гэсэн тэмдэглэгээ.
  - `fig_four_factors(team_games)` — F5. Лигийн дунджаас хазайлтыг 4 panel-д small multiples-аар, баг эрэмбэлэгдсэн байна.
  - `fig_import_share_donut(player_games)` — F6. 2 хэсэг, хувийг хэсэг дээр нь бичнэ. CI-г тайлбарт бичнэ (тоглолтоор bootstrap).
  - `pareto_table(values: pd.Series) -> DataFrame[label, value, cum_share]`
  - `fig_pareto(values: pd.Series, colors: pd.Series, title, cum_ci: tuple[np.ndarray, np.ndarray] | None, threshold=0.8)` — P1/P2. Буурах дарааллаар эрэмбэлнэ. Хоёр тэнхлэг хоёулаа 0-ээс эхэлнэ, баруун тэнхлэг 0–100%. 80% шугам болон огтлолцох цэгт "Топ k (x%) = 80%" annotate.
  - `pareto_ci(player_games, n_boot=2000, seed=42) -> tuple[np.ndarray, np.ndarray]`: тоглолтоор bootstrap хийж эрэмбэ бүрийн cum_share-ийн 2.5/97.5 percentile.
  - `fig_team_concentration(player_games)` — P2. 10 багийн "80%-д хүрэх тоглогчийн тоо"-г dot + CI-аар.
  - `fig_top_dot_ci(players_ci: DataFrame[player, est, lo, hi], metric_label)` — U2. Хэвтээ интервал, цэг. Bar болон error bar хэрэглэхгүй.

- [ ] **Step 1: Унах тест бичих**
  - `pareto_table(pd.Series({"a":50,"b":30,"c":20}))` → `cum_share == [0.5, 0.8, 1.0]`, дараалал `a, b, c`.
  - `fig_pareto`-ийн хоёр тэнхлэгийн `get_ylim()[0] == 0`, баруун тэнхлэгийн дээд хязгаар ≤ 1.05 (эсвэл 105%). 80%-ийн `axhline` байна.
  - `pareto_ci`: `lo ≤ cum_share ≤ hi` бүх эрэмбэд.
  - `fig_cum_winpct(bands=True)` нь ≥ 3 `PolyCollection` агуулна. `bands=False` бол 0.
  - `fig_top_dot_ci`: axes-д `BarContainer` байхгүй.
  - Функц бүр `chart_qa.check`-ийг давна.
- [ ] **Step 2:** FAIL → хэрэгжүүлнэ → PASS
- [ ] **Step 3:** Бодит дата дээр `figures/_preview/`-д гаргаж нүдээр шалгана.
- [ ] **Step 4: Commit** — `"feat(mba): Pareto, fan chart, dot+CI, Four Factors график"`

### Task 13: Газрын зураг ба сүлжээ (F11 F12)

**Files:**
- Create: `src/charts/geo_network.py`, `tests/test_charts_geo_net.py`

**Interfaces:**
- Produces:
  - `load_aimags(path: Path) -> list[dict]`: geojson-ийг уншина. `geopandas` хэрэглэхгүй, matplotlib `PathPatch`-аар зурна.
  - `fig_team_map(team_meta, standings, geo_path)` — F11. Bubble хэмжээ = ялалтын хувь, өнгө = бүс. `region == "Тодорхойгүй"` багуудыг зурахгүй бөгөөд тэдний тоог caption-д бичнэ.
  - `transfer_edges(players_season) -> DataFrame[src_team, dst_team, n]`: `player_id` нь 2025-26-д `src`, 2026-27-д `dst` бөгөөд `src != dst`.
  - `fig_transfer_network(edges)` — F12. `networkx` circular layout. Ирмэгийн өргөн ∝ n. Зангилааны хэмжээ ∝ орж ирсэн тоглогчийн тоо.

- [ ] **Step 1: Унах тест бичих**
  - `load_aimags(data/raw/geo/mng_adm1.geojson)`-ийн урт 22.
  - `transfer_edges`: A нь X→Y, B нь X→X, C нь X→Y → `[(X, Y, 2)]`.
  - Хоёр функц `check`-ийг давна. Тодорхойгүй бүстэй 1 баг байхад caption-д "1 баг" гэж бичигдсэн.
- [ ] **Step 2:** FAIL → хэрэгжүүлнэ → PASS
- [ ] **Step 3: Commit** — `"feat(mba): багийн газрын зураг ба шилжилтийн сүлжээ"`

### Task 14: Хураангуй самбарууд (U5 U9)

**Files:**
- Create: `src/charts/summary.py`, `tests/test_charts_summary.py`

**Interfaces:**
- Consumes: `reports/hypotheses.csv` (`HypothesisResult`-ийн баганууд), `reports/missing.csv`, `reports/name_matches.csv`, `reports/ppg_validation.csv`
- Produces:
  - `fig_hypothesis_summary(hyp: DataFrame)` — U5. Таамаглал бүр өөрийн хэмжээстэй нэг мөр panel (small multiples). Цэг + 95% CI, `null_value` дээр босоо шугам. Баруун талд "Дэмжигдсэн / Дэмжигдээгүй / Тодорхойгүй" гэсэн шошго: CI нь null-ийг агуулахгүй бол дэмжигдсэн, агуулбал тодорхойгүй.
  - `fig_data_quality(missing, matches, ppg_val)` — U9. 3 panel: дутуугийн хувь (bar), fuzzy match-ийн онооны гистограм, PPG-ийн зөрүүний тархалт.
  - `verdict(row: pd.Series) -> str`: `row`-ийн `estimate, ci_lo, ci_hi, null_value`-г ашиглана.

- [ ] **Step 1: Унах тест бичих**
  - `verdict(pd.Series(dict(estimate=0.3, ci_lo=0.1, ci_hi=0.5, null_value=0)))` → "Дэмжигдсэн". `ci_lo=-0.1` → "Тодорхойгүй". `ci_hi < null_value` (жишээ нь H2-д 0.40 < 0.5) → "Дэмжигдээгүй".
  - 5 мөртэй `hyp` → 5 axes. `check`-ийг давна.
- [ ] **Step 2:** FAIL → хэрэгжүүлнэ → PASS
- [ ] **Step 3: Commit** — `"feat(mba): таамаглалын хураангуй ба өгөгдлийн чанарын самбар"`

---

## Үе шат D — Машин суралцал

### Task 15: K-Means архетип ба тогтвортой байдал

**Files:**
- Create: `mba_analysis/src/models.py`, `mba_analysis/tests/test_models_kmeans.py`

**Interfaces:**
- Produces:
  - `ARCHETYPE_FEATURES = ["pts36","reb36","ast36","stl36","blk36","tpa_rate","ftr","ts_pct"]`
  - `archetype_matrix(players, min_minutes=150) -> tuple[DataFrame, np.ndarray]`: шүүсэн мөрүүд ба `StandardScaler`-ийн дараах X. NaN-тай мөрийг хасна.
  - `class ArchetypeResult`: `k, labels, inertia_by_k: dict, silhouette_by_k: dict, centroids: DataFrame (анхны нэгжээр), pca_xy: ndarray, model, scaler`
  - `fit_archetypes(X, k_range=range(2, 9), seed=42, k: int | None = None) -> ArchetypeResult`. `k is None` бол silhouette хамгийн өндөр k-г сонгоно.
  - `cluster_stability(X, k, n_boot=100, seed=42) -> tuple[float, np.ndarray]`: ARI-ийн дундаж ба мөр бүрийн co-assignment давтамж (0–1). Bootstrap түүвэр бүрийг анхны загвартай харьцуулна.
  - `name_clusters(res) -> dict[int, str]`: центроидын стандартчилсан утгын хамгийн өндөр хувьсагчаар нэр өгнө.
    - `pts36` эсвэл `ts_pct` → "Оноо авагч"
    - `ast36` → "Тоглолт зохион байгуулагч"
    - `reb36` эсвэл `blk36` → "Хамгаалалтын төв"
    - `tpa_rate` → "Гурвын мэргэн"
    - `stl36` → "Идэвхтэй хамгаалагч"
    - хамгийн өндөр z < 0.5 → "Тэнцвэртэй"
    - Ижил нэр давхцвал 2 дахь хамгийн өндөр хувьсагчаар ялгана.
  - `cluster_composition(players, labels, names) -> DataFrame[cluster_name, n, pct_import, PG, SG, SF, PF, C]`

- [ ] **Step 1: Унах тест бичих**
  - `make_blobs(n_samples=150, centers=3, random_state=42)` дээр `fit_archetypes(...).k == 3`. `cluster_stability`-ийн ARI > 0.9, co-assignment-ийн median > 0.9.
  - `archetype_matrix`: MIN 100 ба 200 тоглогчоос зөвхөн 200 үлдэнэ.
  - Ижил seed → ижил labels.
  - `name_clusters`: `ast36`-ийн z = 2.0 бусад < 0.5 центроид → "Тоглолт зохион байгуулагч". Бүх z < 0.5 → "Тэнцвэртэй". Үр дүнгийн нэрс бүгд ялгаатай.
  - `cluster_composition`-ий `pct_import` нь 0–100 хооронд, байрлалын баганын нийлбэр = `n`.
- [ ] **Step 2:** FAIL → хэрэгжүүлнэ → PASS
- [ ] **Step 3: Commit** — `"feat(mba): K-Means архетип, нэрлэлт, bootstrap тогтвортой байдал"`

### Task 16: Ялалтын таамаглал, тайлбар загвар, Pythagorean fit

**Files:**
- Modify: `mba_analysis/src/models.py`, `src/analysis.py` (`eval_h3(expl)` нь `fit_explanatory`-ийн `efg` мөрийг HypothesisResult болгоно; `eval_h5(standings)` нь `fit_pythagorean`-ийн R²-ийг bootstrap CI-тай буцаана; хоёуланг `run_analysis`-д нэмнэ)
- Create: `mba_analysis/tests/test_models_win.py`
- Output: `reports/metrics.json`

**Interfaces:**
- Consumes: `elo.run_elo`, `features.four_factors`, `uncertainty.CI`
- Produces:
  - `WIN_FEATURES = ["elo_diff","winpct_to_date_diff","net_rating_last5_diff","efg_last5_diff","tov_pct_last5_diff"]`
  - `build_game_matrix(games, team_games, seed=42, min_prior_games=3) -> DataFrame`. Баганууд: `game_id, date, season, team_a, team_b, y` + `WIN_FEATURES`.
    - Тоглолт бүр 1 мөр, A/B-г seed-тэй санамсаргүйгээр сонгоно.
    - Бүх хувьсагч зөвхөн **тухайн огнооноос өмнөх** тоглолтуудаас тооцогдоно. Ижил өдрийн тоглолтуудыг ч оруулахгүй.
    - Улирал бүрт дахин эхэлнэ. Elo нь `elo_pre`-ээс.
  - `baseline_predict(df, kind: Literal["elo","winpct"]) -> np.ndarray` (магадлал 0/0.5/1)
  - `make_models(seed=42) -> dict[str, estimator]`:
    - `"logreg"`: `Pipeline(StandardScaler, LogisticRegression(C=1.0))`
    - `"rf"`: `RandomForestClassifier(n_estimators=300, max_depth=4, random_state=42)`
  - `walk_forward_cv(df, models, n_folds=5) -> DataFrame[fold, model, n_train, n_test, accuracy, auc, brier]`. Огноогоор эрэмбэлсэн expanding window. Fold бүрийн test нь train-аас хойшхи огноотой.
  - `bootstrap_metrics(y, p, n_boot=1000, seed=42) -> dict[str, CI]`
  - `season_holdout(df, models) -> DataFrame`: 2025-2026 дээр сургаж, 2026-2027 дээр шалгана.
  - `fit_explanatory(team_games, n_boot=1000, seed=42) -> DataFrame[feature, coef, lo, hi, perm_importance, perm_lo, perm_hi]`: тухайн тоглолтын Four Factors-ийн A − B зөрүү, стандартчилсан.
  - `fit_pythagorean(standings) -> dict(exponent, exponent_ci: CI, r2, mae, mae_13_91)`: `log(W/L) = e·log(PF/PA)`-ийг тэг цэгээр дамжих OLS-аар тааруулна. CI-г баг-улирлын мөрөөр bootstrap.
  - `run_models(processed_dir, reports_dir, models_dir) -> None`. CLI: `python -m src.models`. `metrics.json`-д CV-ийн mean ± std, bootstrap CI, holdout, baseline-ууд, k, silhouette, ARI-г бичнэ.

- [ ] **Step 1: Унах тест бичих**
  - `test_no_leakage`: синтетик 6 баг, 40 тоглолт. Сүүлийн тоглолтын оноог эсрэгээр нь солиход тухайн мөрийн бүх `WIN_FEATURES` өөрчлөгдөхгүй.
  - `test_same_day_excluded`: нэг өдөр 2 тоглолт тоглосон баг эхнийх нь үр дүнг хоёр дахийн хувьсагчдад ашиглахгүй.
  - `test_orientation_balanced`: 200 тоглолтын `y`-ийн дундаж 0.4–0.6. Нэг тоглолт яг 1 мөртэй.
  - `test_min_prior_games`: аль нэг баг < 3 өмнөх тоглолттой мөрүүд хасагдсан.
  - `test_walk_forward_chronological`: fold бүрийн `max(train.date) < min(test.date)`.
  - `test_pythag_recovers_exponent`: PF/PA-аас e = 14-өөр W/L үүсгэхэд `exponent ≈ 14 ± 0.5`.
  - `test_explanatory_signs`: eFG зөрүү өндөр байх тусам ялдаг синтетик дата дээр `efg` коэффициент > 0 бөгөөд `lo > 0`.
- [ ] **Step 2:** FAIL → хэрэгжүүлнэ → `.venv/bin/python -m pytest tests/test_models_kmeans.py tests/test_models_win.py -v` PASS
- [ ] **Step 3:** `.venv/bin/python -m src.models` → `reports/metrics.json`, `dashboard/models/{logreg,rf,kmeans,scaler}.joblib`. Дараа нь `.venv/bin/python -m src.analysis` → `hypotheses.csv` 5 мөр (H3 нь `fit_explanatory`-ийн efg коэффициент).
- [ ] **Step 4: Commit** — `"feat(mba): ялалтын таамаглал (walk-forward), тайлбар загвар, Pythagorean"`

### Task 17: ML-ийн графикууд (F14 U6 U8 P3)

**Files:**
- Create: `src/charts/ml.py`, `tests/test_charts_ml.py`

**Interfaces:**
- Consumes: `ArchetypeResult`, `cluster_stability`, `metrics.json`, `fit_explanatory`-ийн гаралт, `fig_pareto`
- Produces:
  - `fig_elbow_silhouette(res)`
  - `fig_pca_clusters(res, coassign: np.ndarray, names: dict[int,str])` — F14 + U8. Цэгийн alpha = `0.15 + 0.85·coassign`.
  - `fig_radar_centroids(res, names)`
  - `fig_confusion(y, p, threshold=0.5)`
  - `fig_roc(curves: dict[str, tuple])`
  - `fig_metric_distributions(boot: dict[str, np.ndarray], baselines: dict[str, CI])` — U6a. Half-eye: density + median + 66/95% интервал.
  - `fig_calibration(y, p, n_bins=5)` — U6b. Bin бүрт Wilson CI.
  - `fig_importance_pareto(expl)` — P3. `fig_pareto`-ийг дахин ашиглана, CI-г whisker-ээр.

- [ ] **Step 1: Унах тест бичих:** синтетик оролтоор функц бүр `check`-ийг давна. `fig_pca_clusters`-ийн scatter alpha-ууд [0.15, 1.0] хооронд. `fig_calibration` нь ≤ 5 цэгтэй.
- [ ] **Step 2:** FAIL → хэрэгжүүлнэ → PASS
- [ ] **Step 3: Commit** — `"feat(mba): ML-ийн график ба загварын тодорхой бус байдал"`

---

## Үе шат E — Бүх графикийг гаргах ба notebook

### Task 18: `make_figures` ба 6 notebook

**Files:**
- Create: `mba_analysis/src/make_figures.py`, `tests/test_make_figures.py`, `notebooks/01_collect.ipynb` … `06_ml.ipynb`
- Output: `figures/F01…F14, P1…P3, U1…U9 *.png|*.svg`, `reports/chart_qa.csv`

**Interfaces:**
- Consumes: Tasks 9–17-ийн бүх функц
- Produces:
  - `FIGURE_SPECS: list[tuple[str, Callable[[dict], Figure]]]`. Нэр ба барих функц. Жишээ: `("F01_ppg_hist", ...)`, `("P1_league_pareto", ...)`, `("U1_ts_funnel", ...)`.
  - `load_inputs(processed_dir, reports_dir) -> dict[str, Any]`
  - `render_all(processed_dir, reports_dir, out_dir) -> DataFrame[name, status, error]`. Нэг график алдаа гарсан ч бусдыгаа үргэлжлүүлнэ. Дуусахад алдаа байвал exit code 1. CLI: `python -m src.make_figures`.
  - Action title-ийн гол тоо (жишээ нь "Топ 23 тоглогч онооны 80%-ийг авдаг") бодит датаас тооцогдоно. Бичвэрт тоог хатуу бичихгүй.

- [ ] **Step 1: Унах тест бичих:** `conftest`-ийн жижиг дата-аар `render_all` ажиллуулахад бүх мөрийн `status == "ok"`, PNG ба SVG тоо = `len(FIGURE_SPECS)` (≥ 26).
- [ ] **Step 2:** FAIL → хэрэгжүүлнэ → PASS
- [ ] **Step 3:** `.venv/bin/python -m src.make_figures` → `reports/chart_qa.csv` бүх мөр ok. Хувь бүр нь нүдээр шалгагдана (Task 11 Step 3-ийн жагсаалтаар).
- [ ] **Step 4: Notebook бичих.** Бүгд зөвхөн `src`-ийн функцийг дуудаж, үр дүнг харуулна. Тайлбарын markdown нүдүүд товч, ноорог хэлбэртэй ("📝 Өөрийн үгээр дахин бичих").
  - `01_collect`: SNAPSHOT, мөрийн тоо, эх сурвалжийн хүснэгт
  - `02_clean`: cleaning_log, жишээ өмнө/дараа, missing, name_matches
  - `03_descriptive`: 2 хүснэгт + тайлбар
  - `04_visualization`: F1–F14, P1–P3, U1–U4
  - `05_analysis`: H1–H5, U5, U9, 5 асуулт
  - `06_ml`: K-Means, win model, тайлбар загвар, Pythagorean, U6, U8, P3
- [ ] **Step 5:** `for nb in notebooks/0*.ipynb; do .venv/bin/jupyter nbconvert --to notebook --execute --inplace "$nb"; done` → 6 notebook алдаагүй ажиллана.
- [ ] **Step 6: Commit** — `"feat(mba): бүх график (chart_qa давсан) ба 6 notebook"`

---

## Үе шат F — Dashboard

### Task 19: Dashboard-ийн урьдчилан тооцоолсон дата

**Files:**
- Create: `mba_analysis/src/build_dashboard_data.py`, `tests/test_build_dashboard_data.py`
- Output: `dashboard/data/{players,player_ci,team_games,games,standings,pareto_league,pareto_team,clusters,team_meta}.parquet`, `dashboard/models/*.joblib` (Task 16)

**Interfaces:**
- Produces:
  - `build(processed_dir, reports_dir, out_dir) -> dict[str, int]`. CLI: `python -m src.build_dashboard_data`.
  - `player_ci.parquet`: `player_id, season, metric ∈ {ppg, ts_pct}, est, lo, hi` (тоглолтоор bootstrap 2,000)
  - `clusters.parquet`: `player_id, season, cluster, cluster_name, coassign, pc1, pc2`
  - `team_games.parquet`: Wilson CI-тай cum_winpct, `elo_pre`
  - `win_probability(elo_a: float, elo_b: float) -> tuple[float, float, float]`: Elo-ийн магадлал ба загварын bootstrap-аас авсан интервал. Цэвэр функц тул < 1 мс.

- [ ] **Step 1: Унах тест бичих**
  - `build` нь 9 parquet үүсгэнэ, `player_ci`-ийн бүх мөрөнд `lo ≤ est ≤ hi`.
  - `win_probability(1500, 1500)[0] == 0.5`. 1,000 удаагийн дуудлага < 0.1 с.
  - Нийт parquet ≤ 20 MB.
- [ ] **Step 2:** FAIL → хэрэгжүүлнэ → PASS → `.venv/bin/python -m src.build_dashboard_data`
- [ ] **Step 3: Commit** — `"feat(mba): dashboard-ийн урьдчилан тооцоолсон parquet"`

### Task 20: Streamlit dashboard

**Files:**
- Create: `dashboard/app.py`, `dashboard/data_access.py`, `dashboard/plots.py`, `dashboard/views/{overview,players,teams,ml,quality,about}.py`, `dashboard/requirements.txt`, `.streamlit/config.toml` (repo root), `tests/test_dashboard.py`, `tools/time_dashboard.py`
- Output: `reports/dashboard_timing.csv`

**Interfaces:**
- Consumes: `dashboard/data/*.parquet`, `win_probability`, `style.PALETTE`
- Produces:
  - `data_access.load(name: str) -> pd.DataFrame` (`@st.cache_data`)
  - `data_access.filters_sidebar() -> Filters`. `Filters` нь dataclass: `season, teams, positions, import_status, min_gp:int=5, show_ci: bool=True`.
  - `data_access.apply(df, f: Filters) -> pd.DataFrame`
  - `data_access.empty_notice(df) -> bool`: хоосон бол `st.info("Сонгосон шүүлтүүрт тохирох өгөгдөл алга")` харуулаад `True` буцаана.
  - `plots.py`-ийн Plotly функцүүд нь `style.PALETTE`-ийг ашиглаж, `go.Figure` буцаана:
    - `px_pareto` (P1/P2), `px_funnel` (U1, `Scattergl`), `px_dot_ci` (U2), `px_fan` (U3), `px_quantile_dots(p: float, n=20)` (U7), `px_clusters` (U8, `Scattergl`, alpha = coassign), `px_four_factors`, `px_elo`, `px_map`, `px_scatter(x, y, color)`
    - Hover бүрт тоо болон CI гарна.
  - `views/*.py` бүр `render(f: Filters) -> None` функцтэй. Бие даасан хэсэг бүр `@st.fragment`-д ороно. Хуудас бүрийн агуулга нь spec §9-ийн хуудасны хүснэгтийг яг дагана, үүнд Тойм хуудасны CI-тай KPI картууд ба Өгөгдлийн чанар хуудасны U9 орно.
  - `app.py`: `st.set_page_config(layout="wide")`, `st.navigation` 6 хуудастай. Хуудас бүрийн дээд хэсэгт "Snapshot: 2026-11-12" байна.
  - **7 харилцааны зорилгын хэрэгжүүлэлт** (spec §9-ийн хүснэгтээр):
    - Select: Plotly `on_select="rerun"` → тоглогчийн карт
    - Explore: zoom/pan
    - Reconfigure: X/Y `selectbox`
    - Encode: өнгө = {байрлал, Import, cluster} `radio`
    - Abstract/Elaborate: "Улирлын дундаж / Тоглолт бүр" `segmented_control`
    - Filter: sidebar
    - Connect: `st.session_state["highlight_team"]` бүх graph дээр онцлогдоно

- [ ] **Step 1: Унах тест бичих** (`streamlit.testing.v1.AppTest`, timeout 30)
  - `test_app_runs_all_pages`: `AppTest.from_file("dashboard/app.py").run()` дээр `exception` хоосон. `at.switch_page` ашиглан 6 хуудас бүгд exception-гүй ажиллана.
  - `test_empty_filter_shows_message` (Review Focus #5): players хуудсанд `min_gp` slider-ийг 28, баг = 1, байрлал = "C" болгоход `at.info`-д "Сонгосон шүүлтүүрт тохирох өгөгдөл алга" гарч, exception гарахгүй.
  - `test_ci_toggle`: `show_ci = False` болгоход players хуудасны U2 graph-д CI trace байхгүй болно (plotly chart-ийн JSON-оос шалгана).
  - `test_quantile_dots`: `px_quantile_dots(0.62)` нь 20 цэгтэй, 12 нь А багийн өнгөтэй (`round(0.62·20) = 12`).
- [ ] **Step 2:** FAIL → хэрэгжүүлнэ → PASS
- [ ] **Step 3: Хугацааг хэмжих.** `tools/time_dashboard.py`: `AppTest` ашиглан анх ажиллуулах хугацааг 1 удаа, шүүлтүүр солих хугацааг 20 удаа хэмжинэ. Үр дүнг `reports/dashboard_timing.csv`-д бичнэ. Expected: анх < 3 с, шүүлтүүрийн median < 300 мс. Хэтэрвэл хамгийн удаан хэсгийг (`st.fragment`, тооцоог parquet руу шилжүүлэх) засна.
- [ ] **Step 4: Хөтөч дээр шалгах.** `.claude/launch.json`-д `streamlit run mba_analysis/dashboard/app.py --server.port 8501` тохиргоог нэмж, preview дээр нээнэ. Шалгах зүйлс:
  - 6 хуудас бүгд ажиллана
  - 7 харилцааны зорилго бүгд хэрэгждэг
  - Hover дээр CI гарна
  - Гар утасны өргөнд (375px) layout эвдрэхгүй
  - Console-д алдаа гарахгүй
- [ ] **Step 5: Байршуулахад бэлдэх.**
  - `dashboard/requirements.txt`: `streamlit>=1.57, pandas>=2.3, numpy>=2.3, plotly>=6.3, pyarrow>=21.0, scikit-learn>=1.8, joblib>=1.5`
  - `mba_analysis/README.md`-д Streamlit Community Cloud-д байршуулах алхмуудыг нэмнэ: repo `batdorj-s/data-visualization-3a`, branch `main`, main file `mba_analysis/dashboard/app.py`.
  - **Deploy хийх алхмыг хэрэглэгч өөрөө хийнэ.**
- [ ] **Step 6: Commit** — `"feat(mba): Streamlit dashboard (7 зорилго, CI, fragment), хугацааны хэмжилт"`

---

## Үе шат G — Тайлан ба танилцуулга

### Task 21: Шийдлийн зураг төсөл (blueprint)

**Files:**
- Create: `mba_analysis/src/blueprint.py`, `tests/test_blueprint.py`
- Output: `report/blueprint/{architecture,wireframe_scout,wireframe_pregame}.png|.svg`, `report/blueprint/user_stories.md`

**Interfaces:**
- Produces:
  - `draw_architecture(out: Path) -> Path`: scraper → цэвэрлэгээ/feature → загварууд → dashboard/API. Мөн өдөр бүр ажиллах cron.
  - `draw_wireframe_scout(out: Path) -> Path`: архетипээр хайх, төстэй тоглогч, CI-тай карт.
  - `draw_wireframe_pregame(out: Path) -> Path`: 2 багийн Four Factors, магадлал + quantile dots, сүүлийн 5 тоглолт.
  - Бүгд matplotlib-ийн `FancyBboxPatch` + сумаар зурагдана. Палитр `style.py`-аас, бичвэр монгол хэлээр.
  - `user_stories.md`: 4 хэрэглэгчийн хэрэгцээ (дасгалжуулагч, скаут, MBA, хөгжөөн дэмжигч), хязгаарлалт, дараагийн алхам.

- [ ] **Step 1: Унах тест бичих:** 3 функц бүр PNG үүсгэнэ, өргөн ≥ 1800 px.
- [ ] **Step 2:** FAIL → хэрэгжүүлнэ → PASS → 3 зургийг нээж нүдээр шалгана (давхцал, сумны чиглэл).
- [ ] **Step 3: Commit** — `"feat(mba): MBA Scout шийдлийн зураг төсөл"`

### Task 22: Word тайлан ба PowerPoint

**Files:**
- Create: `mba_analysis/src/report_docx.py`, `mba_analysis/src/report_pptx.py`, `tests/test_reports.py`
- Output: `report/MBA_tailan.docx`, `report/MBA_taniltsuulga.pptx`

**Interfaces:**
- Consumes: `figures/*.png`, `reports/*.csv`, `reports/metrics.json`, `report/blueprint/*`
- Produces:
  - `build_report(root: Path, out: Path) -> Path`
    - Бүтэц (spec §11): 1 Оршил, асуулт, таамаглал / 2 Өгөгдөл ба эх сурвалж / 3 Цэвэрлэгээ / 4 Танилцуулах статистик / 5 Дүрслэл / 6 ML / 7 Шинжилгээ ба 5 асуулт / 8 Санал ба зураг төсөл / 9 Хязгаарлалт / 10 Эх сурвалж
    - Хүснэгтүүд: эх сурвалж, cleaning_log, descriptive (хураангуйлсан), hypotheses, metrics
    - Зураг: F01–F06, P1, U1–U5, F14, blueprint/architecture (бусдыг нь хавсралт болгож notebook руу лавлана)
    - `DRAFT_STYLE`: шар тодруулгатай "📝 Ноорог — өөрийн үгээр дахин бичих" догол мөр. Тоон дүгнэлтүүдийг жагсаалт хэлбэрээр бичнэ.
    - A4, Arial 11pt, гарчиг Heading 1/2, хуудасны дугаартай.
  - `build_deck(root: Path, out: Path) -> Path`: 16:9, ~12 слайд. Нүүр, асуулт/таамаглал, өгөгдөл, цэвэрлэгээ, P1, U1, F4+U3, U5, ML (2), dashboard (QR эсвэл URL-ийн байршил), санал + blueprint, дүгнэлт. Слайд бүр ≤ 1 график, ≤ 3 мөр текст, илтгэгчийн тэмдэглэл ноорог хэлбэрээр.
  - CLI: `python -m src.report_docx`, `python -m src.report_pptx`

- [ ] **Step 1: Унах тест бичих**
  - docx-ийн Heading 1 гарчиг 10, зураг ≥ 12, хүснэгт ≥ 5. `"Ноорог"` гэсэн догол мөр ≥ 5.
  - pptx-ийн слайд 11–13, слайд бүрт ≤ 1 зураг.
- [ ] **Step 2:** FAIL → хэрэгжүүлнэ → PASS
- [ ] **Step 3: Хуудасны тоог шалгах** (Word суусан тул `docx2pdf` ажиллана):

```bash
.venv/bin/python -c "from docx2pdf import convert; convert('report/MBA_tailan.docx','report/_check.pdf')" && .venv/bin/python -c "import pypdf; print(len(pypdf.PdfReader('report/_check.pdf').pages))"
```
  Expected: 8–10. Хэтэрвэл хавсралт руу зураг шилжүүлнэ. PDF-ийн хуудсуудыг зураг болгож нүдээр шалгана. `_check.pdf`-ийг commit хийхгүй.
- [ ] **Step 4: Commit** — `"feat(mba): Word тайлан ба PowerPoint (ноорог тайлбартай)"`

### Task 23: Эцсийн шалгалт

**Files:**
- Modify: `mba_analysis/README.md` (ажиллуулах дараалал, эх сурвалж, лиценз), `docs/assignment/requirements.md` (✓ тэмдэглэгээ)

- [ ] **Step 1:** `.venv/bin/python -m pytest` → бүгд PASS.
- [ ] **Step 2: Цэвэр давталт.** `python -m src.scrape --offline && python -m src.wiki && python -m src.clean && python -m src.analysis && python -m src.models && python -m src.make_figures && python -m src.build_dashboard_data` → алдаагүй ажиллаж, ижил мөрийн тоо гарна.
- [ ] **Step 3: Spec §15-ийн хүлээн авах шалгуурын жагсаалтыг нэг бүрчлэн шалгах.** Үр дүнг `reports/acceptance.md`-д бичнэ: шалгуур бүрийн тоо ба хаанаас харсан.
- [ ] **Step 4:** `docs/assignment/requirements.md`-ийн шалгах хуудсанд ✓ тэмдэглэнэ. Хэрэглэгч өөрийн үгээр бичих ёстой хэсгүүдийг (тайлангийн ноорог догол мөрүүд, слайдын тэмдэглэл) жагсааж хэрэглэгчид мэдэгдэнэ.
- [ ] **Step 5: Commit ба push**

```bash
git add mba_analysis docs
git commit -m "docs(mba): эцсийн шалгалт ба ажиллуулах заавар"
git push origin main
```
