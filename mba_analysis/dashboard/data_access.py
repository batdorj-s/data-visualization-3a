from dataclasses import dataclass, field
from pathlib import Path

import numpy as np
import pandas as pd
import streamlit as st

DATA = Path(__file__).parent / "data"
SEASONS = ["2025-2026", "2026-2027"]
POSITIONS = ["PG", "SG", "SF", "PF", "C"]
IMPORT_OPTIONS = ["Бүгд", "Import", "Дотоод"]
EMPTY_MSG = "Сонгосон шүүлтүүрт тохирох өгөгдөл алга. Шүүлтүүрээ сулруулна уу."


@st.cache_data(show_spinner=False)
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


def filters_sidebar() -> Filters:
    sb = st.sidebar
    sb.markdown("### Шүүлтүүр")
    season = sb.selectbox("Улирал", SEASONS, key="season",
                          format_func=lambda s: s.replace("-20", "–") + (" (явцын)" if s == "2026-2027" else ""))
    teams = team_names(season)
    for key in ("teams", "highlight_team"):
        cur = st.session_state.get(key)
        if key == "teams" and cur:
            st.session_state[key] = [t for t in cur if t in teams]
        if key == "highlight_team" and cur not in teams:
            st.session_state.pop(key, None)
    sel_teams = sb.multiselect("Баг", teams, key="teams", placeholder="Бүх баг")
    positions = sb.multiselect("Байрлал", POSITIONS, key="positions", placeholder="Бүх байрлал")
    imp = sb.radio("Тоглогчийн төрөл", IMPORT_OPTIONS, key="import_status", horizontal=True)
    min_gp = sb.slider("Хамгийн багадаа тоглосон тоглолт (GP)", 1, 30, key="min_gp",
                       value=st.session_state.get("min_gp", 5))
    show_ci = sb.toggle("Итгэх интервал харуулах", key="show_ci", value=st.session_state.get("show_ci", True))
    sb.markdown("---")
    highlight = sb.selectbox("Онцлох баг (бүх график дээр)", teams, key="highlight_team",
                             index=None, placeholder="Сонгоогүй")
    sb.caption(f"Snapshot: {snapshot()} · Эх сурвалж: MBA статистикийн систем")
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
        out = out[out.is_import.astype(bool) == (f.import_status == "Import")]
    return out[out.GP >= f.min_gp]


def empty_notice(df: pd.DataFrame) -> bool:
    if df is None or len(df) == 0:
        st.info(EMPTY_MSG)
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
