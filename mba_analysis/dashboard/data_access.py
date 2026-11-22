from dataclasses import dataclass, field
from pathlib import Path

import numpy as np
import pandas as pd
import streamlit as st

DATA = Path(__file__).parent / "data"
SEASONS = ["2025-2026", "2026-2027"]
POSITIONS = ["PG", "SG", "SF", "PF", "C"]
IMPORT_OPTIONS = ["Бүгд", "Гадаад", "Дотоод"]
EMPTY_MSG = ("Сонгосон шүүлтүүрт тохирох өгөгдөл алга. Зүүн талын «Шүүлтүүрийг цэвэрлэх» товчийг дарж "
             "эсвэл тоглолтын доод хязгаарыг бууруулна уу.")
DEFAULTS = {"season": "2025-2026", "teams": [], "positions": [], "import_status": "Бүгд", "min_gp": 5,
            "show_ci": True}


@st.cache_data(show_spinner="Өгөгдөл ачаалж байна…")
def load(name: str) -> pd.DataFrame:
    return pd.read_parquet(DATA / f"{name}.parquet")


@st.cache_data(show_spinner=False)
def snapshot() -> str:
    return (DATA / "snapshot.txt").read_text(encoding="utf-8").strip()


@dataclass
class Filters:
    season: str = "2025-2026"
    teams: list[str] = field(default_factory=list)
    positions: list[str] = field(default_factory=list)
    import_status: str = "Бүгд"
    min_gp: int = 5
    show_ci: bool = True
    highlight_team: str | None = None


def team_names(season: str) -> list[str]:
    ps = load("players")
    return sorted(ps.loc[ps.season == season, "team"].dropna().unique())


def reset_filters() -> None:
    for k, v in DEFAULTS.items():
        st.session_state[k] = list(v) if isinstance(v, list) else v
    st.session_state.pop("highlight_team", None)


LOGO_PX = 128  # дэлгэцэнд 52 px хүртэл харагдана → 128 px нь retina-д хангалттай


def _thumb(url: str) -> str:
    """Албан ёсны логог (0.1–3 MB) серверийн талд нэг удаа татаж, 128 px PNG data URI болгоно.
    Зургийг repo-д хадгалахгүй. Татаж чадахгүй бол эх URL-ийг буцаана (хөтөч өөрөө ачаална)."""
    import base64
    import io

    import requests
    from PIL import Image

    try:
        r = requests.get(url, timeout=10, headers={"User-Agent": "Mozilla/5.0 (MBA Analytics student dashboard)"})
        r.raise_for_status()
        im = Image.open(io.BytesIO(r.content)).convert("RGBA")
        im.thumbnail((LOGO_PX, LOGO_PX), Image.LANCZOS)
        buf = io.BytesIO()
        im.save(buf, format="PNG", optimize=True)
        return "data:image/png;base64," + base64.b64encode(buf.getvalue()).decode()
    except Exception:
        return url


@st.cache_data(show_spinner="Багийн лого ачаалж байна…", ttl=7 * 24 * 3600)
def team_logos() -> dict[str, str]:
    """Багийн нэр → лого (жижигрүүлсэн data URI, эсвэл албан ёсны URL). Эх сурвалж: MBA сайтын schema.org SportsTeam.
    Логогүй баг орохгүй (тэр үед UI үсгэн тэмдэг харуулна). MBA_LOGO_FETCH=0 бол татахгүй, URL-ийг шууд өгнө (тест)."""
    import os
    from concurrent.futures import ThreadPoolExecutor

    meta = load("team_meta")
    if "logo_url" not in meta:
        return {}
    m = meta.dropna(subset=["logo_url"])
    urls = dict(zip(m.canonical_name, m.logo_url))
    if os.environ.get("MBA_LOGO_FETCH", "1") == "0":
        return urls
    with ThreadPoolExecutor(max_workers=6) as ex:
        thumbs = dict(zip(urls, ex.map(_thumb, urls.values())))
    return thumbs


@st.cache_data(show_spinner=False)
def team_info() -> pd.DataFrame:
    return load("team_meta").set_index("canonical_name")


def filters_sidebar() -> Filters:
    sb = st.sidebar
    sb.html('<div class="mba-side-title">Шүүлтүүр</div>')
    sb.caption("Бүх хуудсанд нэг дор үйлчилнэ.")
    season = sb.selectbox("Улирал", SEASONS, key="season",
                          format_func=lambda s: s.replace("-20", "–") + (" (явагдаж буй)" if s == "2026-2027" else ""))
    teams = team_names(season)
    for key in ("teams", "highlight_team"):
        cur = st.session_state.get(key)
        if key == "teams" and cur:
            st.session_state[key] = [t for t in cur if t in teams]
        if key == "highlight_team" and cur not in teams:
            st.session_state.pop(key, None)
    sel_teams = sb.multiselect("Баг", teams, key="teams", placeholder="Бүх баг")
    positions = sb.multiselect("Байрлал", POSITIONS, key="positions", placeholder="Бүх байрлал")
    imp = sb.radio("Тоглогчийн төрөл", IMPORT_OPTIONS, key="import_status", horizontal=True,
                   help="Гадаад = лигийн гадаад тоглогчийн квотоор тоглож буй тоглогч")
    min_gp = sb.slider("Хамгийн багадаа хэдэн тоглолт тоглосон", 1, 30, key="min_gp",
                       value=st.session_state.get("min_gp", 5),
                       help="Цөөн тоглолттой тоглогчийн дундаж санамсаргүй их хэлбэлздэг тул анхдагчаар 5+")
    show_ci = sb.toggle("Магадлалтай хүрээг харуулах", key="show_ci", value=st.session_state.get("show_ci", True),
                        help="Дата цөөн үед бодит утга хаана байж болохыг сүүдэр/шугамаар харуулна (95% магадлал)")
    sb.button("Шүүлтүүрийг цэвэрлэх", on_click=reset_filters, icon=":material/restart_alt:", width="stretch")
    sb.divider()
    highlight = sb.selectbox("Онцлох баг", teams, key="highlight_team", index=None, placeholder="Сонгоогүй",
                             help="Сонгосон баг бүх хуудасны график дээр тодорч харагдана")
    sb.caption(f"Дата: MBA лигийн албан ёсны статистик, {snapshot()}-нд татсан")
    return Filters(season, sel_teams, positions, imp, min_gp, show_ci, highlight)


def current_filters() -> Filters:
    return st.session_state.get("_filters") or Filters()


def apply(df: pd.DataFrame, f: Filters) -> pd.DataFrame:
    out = df[df.season == f.season]
    if f.teams:
        out = out[out.team.isin(f.teams)]
    if f.positions:
        out = out[out.position.isin(f.positions)]
    if f.import_status != "Бүгд":
        out = out[out.is_import.astype(bool) == (f.import_status == "Гадаад")]
    return out[out.GP >= f.min_gp]


def apply_selection(state, selected_ids: list) -> bool:
    """Scatter-ийн ШИНЭ сонголтыг тоглогчийн карт руу дамжуулна. Шинэчилсэн бол True (апп-ыг дахин ажиллуулна)."""
    if not selected_ids or list(selected_ids) == state.get("_last_selection"):
        return False
    state["_last_selection"] = list(selected_ids)
    state["card_player"] = selected_ids[0]
    return True


def empty_notice(df: pd.DataFrame) -> bool:
    if df is None or len(df) == 0:
        from ui import empty_state
        empty_state("Сонгосон шүүлтүүрт тохирох өгөгдөл алга", EMPTY_MSG.split(". ", 1)[1])
        return True
    return False


def team_key_of(name: str | None) -> str | None:
    if not name:
        return None
    ps = load("players")
    hit = ps.loc[ps.team == name, "team_key"]
    return hit.iloc[0] if len(hit) else None


@st.cache_data(show_spinner=False)
def import_share_ci(season: str | None = None, n_boot: int = 2000) -> tuple[float, float, float]:
    pg = load("player_games")
    if season:
        pg = pg[pg.season == season]
    per_game = pg.assign(imp_pts=pg.PTS.where(pg.is_import, 0)).groupby("game_id")[["imp_pts", "PTS"]].sum()
    imp, tot = per_game.imp_pts.to_numpy(float), per_game.PTS.to_numpy(float)
    idx = np.random.default_rng(42).integers(0, len(imp), (n_boot, len(imp)))
    boots = imp[idx].sum(axis=1) / tot[idx].sum(axis=1)
    return float(imp.sum() / tot.sum()), *map(float, np.percentile(boots, [2.5, 97.5]))


def latest_elo(season: str) -> pd.Series:
    g = load("games")
    g = g[g.season == season].sort_values(["date", "game_id"])
    rows = pd.concat([g[["date", "home_team", "elo_post_home"]].set_axis(["date", "team", "elo"], axis=1),
                      g[["date", "away_team", "elo_post_away"]].set_axis(["date", "team", "elo"], axis=1)])
    return rows.sort_values("date").groupby("team").elo.last()
