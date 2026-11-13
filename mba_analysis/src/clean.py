from dataclasses import dataclass, field
from pathlib import Path

import numpy as np
import pandas as pd

from src.names import given_score, normalize, same_person, split_mba_name

ROOT = Path(__file__).resolve().parents[1]
LATEST_SEASON = "2026-2027"
HOME_ARENAS = {"Дархан Юнайтед Арена": "darkhan_united"}
PCT_PAIRS = [("FGA", "FG_pct"), ("TPA", "TP_pct"), ("FTA", "FT_pct")]
VENUES = {"м банк арена": "М Банк Арена", "m bank arena": "М Банк Арена", "m банк арена": "М Банк Арена",
          "darkhan united arena": "Дархан Юнайтед Арена"}
PHASES = {"Regular season": "regular", "Playoffs": "playoff", "Finals": "playoff"}


class UnmappedTeamError(ValueError):
    pass


@dataclass
class CleaningLog:
    rows: list[dict] = field(default_factory=list)

    def add(self, step: str, description: str, rows_before: int, rows_after: int, note: str = "") -> None:
        self.rows.append({"step": step, "description": description, "rows_before": rows_before,
                          "rows_after": rows_after, "note": note})

    def to_frame(self) -> pd.DataFrame:
        return pd.DataFrame(self.rows, columns=["step", "description", "rows_before", "rows_after", "note"])


def _log(log: CleaningLog | None, *args, **kwargs) -> None:
    if log is not None:
        log.add(*args, **kwargs)


def map_teams(df: pd.DataFrame, col: str, aliases: pd.DataFrame, season_col: str = "season",
              log: CleaningLog | None = None) -> pd.DataFrame:
    a = aliases.assign(norm_key=aliases["raw_name"].map(normalize), season=aliases["season"].fillna("*"))
    specific = {(r.norm_key, r.season): (r.team_key, r.canonical_name) for r in a.itertuples() if r.season != "*"}
    generic = {r.norm_key: (r.team_key, r.canonical_name) for r in a.itertuples() if r.season == "*"}

    def lookup(name, season):
        k = normalize(name)
        return specific.get((k, season)) or generic.get(k)

    seasons = df[season_col] if season_col in df.columns else pd.Series(["*"] * len(df), index=df.index)
    found = [lookup(n, s) for n, s in zip(df[col], seasons)]
    missing = sorted({str(n) for n, f in zip(df[col], found) if f is None})
    if missing:
        raise UnmappedTeamError(f"team_aliases.csv-д байхгүй багийн нэр: {missing}")
    out = df.copy()
    prefix = "" if col in ("team_name", "team_raw") else col.removesuffix("_name") + "_"
    out[f"{prefix}team_key" if prefix else "team_key"] = [f[0] for f in found]
    out[f"{prefix}team" if prefix else "team"] = [f[1] for f in found]
    _log(log, "C1", f"{col}: багийн нэрийг стандарт team_key руу буулгав", len(df), len(out),
         f"{df[col].nunique()} түүхий нэр → {len({f[0] for f in found})} баг")
    return out


def normalize_venue(s: str) -> str:
    s = str(s).strip()
    return VENUES.get(normalize(s), s)


def fix_zero_attempt_pct(df: pd.DataFrame, log: CleaningLog | None = None) -> pd.DataFrame:
    out = df.copy()
    changed = 0
    for att, pct in PCT_PAIRS:
        if att in out.columns and pct in out.columns:
            mask = out[att].fillna(0).eq(0)
            changed += int(mask.sum())
            out.loc[mask, pct] = np.nan
    _log(log, "C3", "Оролдлого 0 үеийн хувь (0.0)-ийг NaN болгов", len(df), len(out), f"{changed} утга")
    return out


AGE_RANGE = (15, 45)
HEIGHT_RANGE = (160, 230)


def fix_implausible_values(df: pd.DataFrame, log: CleaningLog | None = None) -> pd.DataFrame:
    """Боломжгүй утгыг (1900 гэх мэт placeholder төрсөн он, 150 см) NaN болгоно (C12)."""
    out = df.copy()
    start = out["season"].astype(str).str[:4].astype(int)
    age = start - pd.to_numeric(out["birth_year"], errors="coerce")
    bad_birth = age.notna() & ~age.between(*AGE_RANGE)
    h = pd.to_numeric(out["height_cm"], errors="coerce")
    bad_height = h.notna() & ~h.between(*HEIGHT_RANGE)
    out.loc[bad_birth, "birth_year"] = np.nan
    out.loc[bad_height, "height_cm"] = np.nan
    _log(log, "C12", f"Алдаатай утгыг засав: нас {AGE_RANGE}-аас гадуур → төрсөн он NaN, өндөр {HEIGHT_RANGE} см-ээс гадуур → NaN",
         len(df), len(out), f"төрсөн он: {int(bad_birth.sum())}, өндөр: {int(bad_height.sum())}; нийт {int(bad_birth.sum() + bad_height.sum())}")
    return out


def drop_dnp(df: pd.DataFrame, log: CleaningLog | None = None) -> pd.DataFrame:
    out = df[~df["dnp"].astype(bool)].copy()
    _log(log, "C4", "Тоглоогүй (DNP) мөрийг хасав", len(df), len(out))
    return out


def split_made_att(df: pd.DataFrame, cols=("FG", "TP", "FT"), log: CleaningLog | None = None) -> pd.DataFrame:
    out = df.copy()
    for c in cols:
        parts = out[c].astype("string").str.extract(r"^\s*(\d+)\s*-\s*(\d+)\s*$")
        out[f"{c}M"] = pd.to_numeric(parts[0]).astype("Int64")
        out[f"{c}A"] = pd.to_numeric(parts[1]).astype("Int64")
        out = out.drop(columns=c)
    _log(log, "C5", f"'м-о' хэлбэрийн {', '.join(cols)} баганыг made/attempt болгож задлав", len(df), len(out))
    return out


def report_missing(df: pd.DataFrame, cols) -> pd.DataFrame:
    n = len(df)
    return pd.DataFrame([{"column": c, "n_missing": int(df[c].isna().sum()),
                          "pct_missing": round(100 * df[c].isna().mean(), 2) if n else 0.0} for c in cols])


def dedupe(df: pd.DataFrame, keys, log: CleaningLog | None = None, step: str = "C7") -> pd.DataFrame:
    out = df.drop_duplicates().drop_duplicates(subset=list(keys), keep="first")
    _log(log, step, f"Давхардлыг хасав ({', '.join(keys)})", len(df), len(out))
    return out.reset_index(drop=True)


def flag_eligible(df: pd.DataFrame, min_gp: int = 5, log: CleaningLog | None = None) -> pd.DataFrame:
    out = df.assign(eligible=df["GP"] >= min_gp)
    _log(log, "C8", f"GP ≥ {min_gp} шүүлтүүрийн тэмдэглэгээ (eligible) нэмэв", len(df), len(out),
         f"eligible: {int(out.eligible.sum())}")
    return out


DTYPES = {
    "games": {"date": "datetime64[ns]", "season": "category", "phase": "category"},
    "players_season": {"season": "category", "eligible": "bool"},
    "players_profile": {"is_import": "bool", "position": "category"},
}


def set_dtypes(df: pd.DataFrame, table: str, log: CleaningLog | None = None) -> pd.DataFrame:
    out = df.copy()
    for col, dtype in DTYPES.get(table, {}).items():
        if col in out.columns:
            out[col] = pd.to_datetime(out[col]) if dtype.startswith("datetime") else out[col].astype(dtype)
    _log(log, "C9", f"{table}: өгөгдлийн төрлийг тохируулав", len(df), len(out))
    return out


TOTAL_COLS = {"PTS_total": "PTS", "FGM": "FGM", "FGA": "FGA", "TPM": "TPM", "TPA": "TPA", "FTM": "FTM", "FTA": "FTA"}


def attach_totals(players_season: pd.DataFrame, player_games: pd.DataFrame) -> pd.DataFrame:
    """Тоглолтын мөрөөс улирлын нийлбэрийг нэмнэ.

    MBA улирлын дундуур баг сольсон тоглогчид улирлын хүснэгтэд ихэвчлэн НЭГ мөр (бүх багийн нийлбэр) өгдөг тул
    ийм тоглогчийн нийлбэрийг бүх багаар авна. Хүснэгтэд баг тус бүрээр мөр байвал багаар нь авна.
    """
    ps = players_season.drop(columns=[c for c in [*TOTAL_COLS, "GP_games", "traded"] if c in players_season.columns])
    agg = {k: (v, "sum") for k, v in TOTAL_COLS.items() if v in player_games.columns}
    gp = ("game_id", "nunique") if "game_id" in player_games.columns else ("PTS", "size")
    by_team = player_games.groupby(["player_id", "season", "team_key"], as_index=False).agg(**agg, GP_games=gp)
    by_season = player_games.groupby(["player_id", "season"], as_index=False).agg(
        **agg, GP_games=gp, traded=("team_key", "nunique"))
    by_season["traded"] = by_season.traded > 1
    rows = ps.groupby(["player_id", "season"]).player_id.transform("size")
    single = ps[rows == 1].merge(by_season, on=["player_id", "season"], how="left")
    multi = ps[rows > 1].merge(by_team, on=["player_id", "season", "team_key"], how="left").assign(traded=True)
    out = pd.concat([single, multi]).sort_index(kind="stable").reset_index(drop=True)
    out["traded"] = out.traded.fillna(False).astype(bool)
    return out


def validate_ppg(players_season: pd.DataFrame, player_games: pd.DataFrame, tol: float = 0.2) -> pd.DataFrame:
    keys = ["player_id", "season", "team_key"]
    out = attach_totals(players_season[keys + ["PPG", "GP"]], player_games)
    out["gp_games"] = out.GP_games
    out["ppg_games"] = (out.PTS_total / out.GP_games).round(2)
    out["diff"] = (out["PPG"] - out["ppg_games"]).abs().round(2)
    out["flag"] = out["diff"] > tol
    return out


def stage_to_phase(stage: str) -> str:
    if stage not in PHASES:
        raise ValueError(f"Мэдэгдэхгүй үе шат: {stage!r}")
    return PHASES[stage]


def assign_player_ids(players_season: pd.DataFrame, overrides: pd.DataFrame | None = None) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Улирал бүрт slug өөр байдаг тул улирал хоорондын нэг хүнийг нэрээр холбож player_id өгнө (C2)."""
    blocked = set()
    if overrides is not None and len(overrides):
        blocked = {(r.left_id, r.right_id) for r in overrides.itertuples() if str(r.decision).lower() == "reject"}
    ps = players_season.copy()
    ps["player_id"] = ps["player_slug"]
    latest = ps[ps.season == LATEST_SEASON]
    matches = []
    for idx, row in ps[ps.season != LATEST_SEASON].iterrows():
        a = split_mba_name(row.player_name)
        cands = [(r.player_slug, r.team_key, given_score(a[1], split_mba_name(r.player_name)[1]))
                 for r in latest.itertuples() if same_person(a, split_mba_name(r.player_name))
                 and (row.player_slug, r.player_slug) not in blocked]
        if not cands:
            continue
        cands.sort(key=lambda c: (c[1] != row.team_key, -c[2]))
        slug, team, score = cands[0]
        ps.at[idx, "player_id"] = slug
        matches.append({"left_id": row.player_slug, "left_name": row.player_name, "right_id": slug,
                        "right_name": latest.loc[latest.player_slug == slug, "player_name"].iloc[0],
                        "score": round(score, 3), "same_team": team == row.team_key, "n_candidates": len(cands)})
    return ps, pd.DataFrame(matches, columns=["left_id", "left_name", "right_id", "right_name", "score",
                                              "same_team", "n_candidates"])


def link_national_team(national: pd.DataFrame, players_season: pd.DataFrame) -> pd.DataFrame:
    pool = players_season.sort_values("season", ascending=False).drop_duplicates("player_id")
    out = national.copy()
    found = []
    for r in out.itertuples():
        hit = next((p.player_id for p in pool.itertuples()
                    if same_person((r.last, r.first), split_mba_name(p.player_name))), None)
        found.append(hit)
    out["matched_player_id"] = found
    return out


def _split_quarters(games: pd.DataFrame) -> pd.DataFrame:
    out = games.copy()
    for side in ("home", "away"):
        q = out[f"quarters_{side}"].astype(str).str.split("|", expand=True).apply(pd.to_numeric, errors="coerce")
        for i in range(4):
            out[f"q{i + 1}_{side}"] = q[i].astype("Int64")
        out[f"ot_{side}"] = (q.iloc[:, 4:].sum(axis=1) if q.shape[1] > 4 else 0)
        out[f"ot_{side}"] = out[f"ot_{side}"].astype("Int64")
    return out


def _standings_from_games(games: pd.DataFrame) -> pd.DataFrame:
    reg = games[games.phase == "regular"]
    rows = []
    for side, opp in (("home", "away"), ("away", "home")):
        rows.append(pd.DataFrame({"season": reg.season, "team_key": reg[f"{side}_team_key"],
                                  "W": (reg[f"{side}_pts"] > reg[f"{opp}_pts"]).astype(int),
                                  "L": (reg[f"{side}_pts"] < reg[f"{opp}_pts"]).astype(int),
                                  "PF": reg[f"{side}_pts"], "PA": reg[f"{opp}_pts"]}))
    st = pd.concat(rows).groupby(["season", "team_key"], as_index=False).sum()
    return st.assign(source="MBA (тоглолтоос тооцсон, regular season)")


def run_cleaning(raw_dir: Path = ROOT / "data" / "raw", out_dir: Path = ROOT / "data" / "processed",
                 reports_dir: Path = ROOT / "reports") -> CleaningLog:
    raw_dir, out_dir, reports_dir = Path(raw_dir), Path(out_dir), Path(reports_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    reports_dir.mkdir(parents=True, exist_ok=True)
    manual = raw_dir / "manual"
    log = CleaningLog()
    aliases = pd.read_csv(manual / "team_aliases.csv", dtype=str).fillna("")

    # games
    g = pd.read_csv(raw_dir / "games_raw.csv")
    g = dedupe(g, ["game_id"], log)
    g = map_teams(g.rename(columns={"home_name": "home_name", "away_name": "away_name"}), "home_name", aliases, log=log)
    g = map_teams(g, "away_name", aliases, log=log)
    n_venues = g.venue_raw.nunique()
    g["venue"] = g.venue_raw.map(normalize_venue)
    log.add("C1b", "Газрын нэрийг стандартчлав", len(g), len(g), f"{n_venues} хувилбар → {g.venue.nunique()}")
    g["phase"] = g.stage.map(stage_to_phase)
    log.add("C11", "Тоглолтын үе шатыг (regular/playoff) хуваарийн шошгоос авав", len(g), len(g),
            f"playoff: {int((g.phase == 'playoff').sum())}")
    g["home_court"] = g.apply(lambda r: HOME_ARENAS.get(r.venue) in (r.home_team_key, r.away_team_key), axis=1)
    g["home_court_team"] = g.venue.map(HOME_ARENAS)
    g = _split_quarters(g)
    g = set_dtypes(g, "games", log)

    # team_games
    tg = pd.read_csv(raw_dir / "team_games_raw.csv")
    tg = map_teams(tg, "team_name", aliases, log=log)
    tg = split_made_att(tg, log=log)
    tg = tg.merge(g[["game_id", "date", "phase"]], on="game_id", how="left")
    tg = dedupe(tg, ["game_id", "team_key"], log)

    # players_season + ids
    ps = pd.read_csv(raw_dir / "players_season_raw.csv")
    ps = map_teams(ps, "team_name", aliases, log=log)
    overrides_path = manual / "name_overrides.csv"
    overrides = pd.read_csv(overrides_path) if overrides_path.exists() else None
    ps, matches = assign_player_ids(ps, overrides)
    relinked = int((matches.left_id != matches.right_id).sum())
    log.add("C2", "Улирал хоорондын тоглогчийг нэрээр холбож player_id өгөв", len(ps), len(ps),
            f"slug өөрчлөгдсөн {relinked} тоглогчийг холбов; {ps.player_id.nunique()} өвөрмөц тоглогч")
    ps = dedupe(ps, ["player_id", "season", "team_key"], log)

    # player_games
    pg = pd.read_csv(raw_dir / "player_games_raw.csv")
    pg = drop_dnp(pg, log)
    pg = split_made_att(pg, log=log)
    pg = map_teams(pg, "team_name", aliases, log=log)
    slug_to_id = dict(zip(ps.player_slug, ps.player_id))
    pg["player_id"] = pg.player_slug.map(slug_to_id).fillna(pg.player_slug)
    pg = dedupe(pg, ["game_id", "player_id"], log)
    pg = pg.merge(g[["game_id", "date", "phase"]], on="game_id", how="left")
    pg_regular = pg[pg.phase == "regular"]

    # MBA-ийн улирлын хүснэгт зөвхөн regular season-ийг тооцдог тул нийлбэрийг мөн regular-аас авна
    ps = attach_totals(ps, pg_regular)
    playoff_only = sorted(set(pg.player_id) - set(ps.player_id))
    log.add("C10b", "Улирлын дундуур баг сольсон тоглогчийн нийлбэрийг бүх багаар нь тооцов", len(ps), len(ps),
            f"баг сольсон тоглогч-улирал: {int(ps.traded.sum())} (MBA-ийн хүснэгт тэдэнд нэг мөр өгдөг); "
            f"зөвхөн playoff-д тоглосон, улирлын хүснэгтэд байхгүй: {', '.join(playoff_only) or 'алга'}")

    # profiles
    prof = pd.read_csv(raw_dir / "players_profile_raw.csv")
    prof = dedupe(prof, ["player_slug"], log)
    ps = ps.merge(prof[["player_slug", "position", "height_cm", "birth_year", "is_import", "FT_pct"]],
                  on="player_slug", how="left")
    ps["is_import"] = ps.is_import.fillna(False).astype(bool)
    pg["is_import"] = pg.player_id.map(ps.groupby("player_id").is_import.max()).fillna(False).astype(bool)
    ps = fix_implausible_values(ps, log)
    ps = fix_zero_attempt_pct(ps, log)
    ps = flag_eligible(ps, 5, log)
    missing = report_missing(ps, ["position", "height_cm", "birth_year", "FT_pct", "TP_pct", "FGA"])
    log.add("C6", "Дутуу утгыг тайлагнав (импутаци хийгээгүй)", len(ps), len(ps),
            "; ".join(f"{r.column}: {r.pct_missing}%" for r in missing.itertuples()))
    ps = set_dtypes(ps, "players_season", log)
    validation_all = validate_ppg(ps, pg)
    validation = validate_ppg(ps, pg_regular)
    log.add("C10", "Улирлын PPG-ийг тоглолтын мөрөөс тооцсонтой харьцуулав (tol 0.2)", len(ps), len(ps),
            f"бүх тоглолтоор {int(validation_all.flag.sum())} зөрүүтэй → MBA-ийн хүснэгт зөвхөн regular season-ийг "
            f"тооцдог нь тогтоогдов; regular-аар, баг сольсон тоглогчийг бүх багаар нэгтгэхэд "
            f"{int(validation.flag.sum())} зөрүүтэй")

    # standings
    st23 = pd.read_csv(raw_dir / "standings_2023_24_raw.csv")
    st23 = map_teams(st23, "team_raw", aliases, log=log)[["season", "team_key", "W", "L", "PF", "PA"]].assign(
        source="Wikipedia 2023–24 The League season")
    parts = [st23]
    manual_2425 = manual / "standings_2024_25.csv"
    if manual_2425.exists():
        m = map_teams(pd.read_csv(manual_2425), "team_raw", aliases, log=log)
        parts.append(m[["season", "team_key", "W", "L", "PF", "PA", "source"]])
    parts.append(_standings_from_games(g))
    standings = pd.concat(parts, ignore_index=True)

    nat = link_national_team(pd.read_csv(raw_dir / "national_team_raw.csv"), ps)
    log.add("C2b", "Шигшээ багийн тоглогчдыг MBA-ийн player_id-тай холбов", len(nat), len(nat),
            f"{int(nat.matched_player_id.notna().sum())}/{len(nat)} холбогдов")

    meta = pd.read_csv(manual / "team_meta.csv")
    unknown_keys = set(g.home_team_key) | set(ps.team_key) - set(meta.team_key)
    missing_meta = sorted(k for k in unknown_keys if k not in set(meta.team_key))
    if missing_meta:
        raise UnmappedTeamError(f"team_meta.csv-д байхгүй team_key: {missing_meta}")

    g.to_csv(out_dir / "games.csv", index=False)
    tg.to_csv(out_dir / "team_games.csv", index=False)
    pg.to_csv(out_dir / "player_games.csv", index=False)
    ps.to_csv(out_dir / "players_season.csv", index=False)
    prof.to_csv(out_dir / "players_profile.csv", index=False)
    standings.to_csv(out_dir / "standings_hist.csv", index=False)
    nat.to_csv(out_dir / "national_team.csv", index=False)
    pd.read_csv(raw_dir / "champions_raw.csv").to_csv(out_dir / "champions.csv", index=False)
    meta.to_csv(out_dir / "team_meta.csv", index=False)
    log.to_frame().to_csv(reports_dir / "cleaning_log.csv", index=False)
    missing.to_csv(reports_dir / "missing.csv", index=False)
    matches.to_csv(reports_dir / "name_matches.csv", index=False)
    validation.to_csv(reports_dir / "ppg_validation.csv", index=False)

    from src.features import add_all_features

    add_all_features(out_dir)
    return log


if __name__ == "__main__":
    result = run_cleaning()
    print(result.to_frame().to_string(index=False))
