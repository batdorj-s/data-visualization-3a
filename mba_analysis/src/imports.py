"""Гадаад тоглогч ба тоглогч солилцооны таамаглалууд (график, dashboard хоёулаа эндээс авна).

Таамаглал бүрийг датаар шалгаж, тодорхой бус байдлыг тоглогчоор дахин түүвэрлэх (bootstrap) эсвэл Fisher-ийн аргаар
тооцно. Тоглогчийн тоо цөөн (нэг улиралд ~40 гадаад тоглогч) тул хүрээ өргөн гарна — үүнийг нуухгүй.
"""
import numpy as np
import pandas as pd

from src.import_sources import LEVELS
from src.insights import usage_table
from src.uncertainty import fisher_ci

SEED = 42
SIM_FEATURES = {"pts36": "Оноо (36 мин)", "reb36": "Самбар (36 мин)", "ast36": "Дамжуулалт (36 мин)",
                "tpa_rate": "3 оноогоор шидсэн хувь", "ts_pct": "Шидэлтийн оновч", "usage": "Довтолгооны ачаалал",
                "height_cm": "Өндөр (см)"}
HIGH_LEVELS = LEVELS[:3]  # NBA, EuroLeague/EuroCup, G League


def import_table(players_season: pd.DataFrame, player_games: pd.DataFrame, background: pd.DataFrame) -> pd.DataFrame:
    """Гадаад тоглогч-улирал бүрийн MBA гүйцэтгэл + гарал үүсэл (5+ тоглолт тоглосон)."""
    ps = players_season[players_season.is_import.astype(bool) & players_season.eligible.astype(bool)]
    use = usage_table(player_games, min_minutes=0)[["player_id", "season", "usage"]]
    df = ps.merge(use, on=["player_id", "season"], how="left")
    bg = background[background.status == "олдсон"][["player_id", "birth_year", "nationality", "level", "last_league",
                                                     "nba_games", "pro_seasons", "source_url"]]
    df = df.merge(bg.rename(columns={"birth_year": "bg_birth_year"}), on="player_id", how="left")
    # Нас: ShamSports-ийн төрсөн он илүү найдвартай (MBA-ийн профайлд алдаа олдсон, жишээ нь McKenzie Moore 2002 ↔ 1992)
    birth = df.bg_birth_year.fillna(df.birth_year)
    df["age"] = df.season.str[:4].astype(int) - birth
    df["level"] = df.level.fillna("Тодорхойгүй")
    return df


def retention(players_season: pd.DataFrame, imports: pd.DataFrame, season: str = "2025-2026",
              next_season: str = "2026-2027") -> pd.DataFrame:
    """Тухайн улирлын гадаад тоглогч дараа улиралд MBA-д (аль ч багт) үлдсэн эсэх."""
    nxt = players_season[players_season.season == next_season]
    cur = imports[imports.season == season].copy()
    cur["stayed"] = cur.player_id.isin(nxt.player_id)
    team_next = nxt.drop_duplicates("player_id", keep="last").set_index("player_id").team
    cur["next_team"] = cur.player_id.map(team_next)
    cur["same_team"] = cur.stayed & (cur.next_team == cur.team)
    return cur


def _boot_median(v: np.ndarray, rng, n_boot: int) -> tuple[float, float, float]:
    v = v[~np.isnan(v)]
    if len(v) == 0:
        return np.nan, np.nan, np.nan
    b = np.median(v[rng.integers(0, len(v), (n_boot, len(v)))], axis=1)
    return float(np.median(v)), float(np.percentile(b, 2.5)), float(np.percentile(b, 97.5))


def compare_groups(df: pd.DataFrame, group: pd.Series, metrics: dict, n_boot: int = 2000, seed: int = SEED) -> pd.DataFrame:
    """Хоёр бүлгийн голч утга ба зөрүүний 95% хүрээ (тоглогчоор дахин түүвэрлэнэ). group: True/False."""
    rng = np.random.default_rng(seed)
    rows = []
    for col, label in metrics.items():
        a = df.loc[group, col].to_numpy(float)
        b = df.loc[~group, col].to_numpy(float)
        a, b = a[~np.isnan(a)], b[~np.isnan(b)]
        ma, la, ha = _boot_median(a, rng, n_boot)
        mb, lb, hb = _boot_median(b, rng, n_boot)
        da = np.median(a[rng.integers(0, len(a), (n_boot, len(a)))], axis=1)
        db = np.median(b[rng.integers(0, len(b), (n_boot, len(b)))], axis=1)
        lo, hi = np.percentile(da - db, [2.5, 97.5])
        rows.append({"metric": col, "label": label, "n_yes": len(a), "n_no": len(b), "med_yes": ma, "lo_yes": la,
                     "hi_yes": ha, "med_no": mb, "lo_no": lb, "hi_no": hb, "diff": ma - mb, "diff_lo": float(lo),
                     "diff_hi": float(hi), "clear": bool(lo > 0 or hi < 0)})
    return pd.DataFrame(rows)


RET_METRICS = {"PPG": "Оноо / тоглолт", "MIN": "Минут / тоглолт", "usage": "Довтолгооны ачаалал",
               "ts_pct": "Шидэлтийн оновч", "age": "Нас"}


def level_performance(imports: pd.DataFrame, n_boot: int = 2000, seed: int = SEED) -> pd.DataFrame:
    """Өмнөх хамгийн өндөр түвшин бүрийн MBA дахь голч оноо, оновч (95% хүрээ)."""
    rng = np.random.default_rng(seed)
    rows = []
    for lvl in LEVELS + ["Тодорхойгүй"]:
        part = imports[imports.level == lvl]
        if len(part) == 0:
            continue
        p, pl, ph = _boot_median(part.PPG.to_numpy(float), rng, n_boot)
        t, tl, th = _boot_median(part.ts_pct.to_numpy(float), rng, n_boot)
        rows.append({"level": lvl, "n": len(part), "ppg": p, "ppg_lo": pl, "ppg_hi": ph, "ts": t, "ts_lo": tl, "ts_hi": th})
    return pd.DataFrame(rows)


def position_minutes(players_season: pd.DataFrame) -> pd.DataFrame:
    """Байрлал бүрийн тоглосон минутын хэдэн хувийг гадаад тоглогч эзэлсэн бэ (улирал бүрээр)."""
    ps = players_season[players_season.position.notna()]
    g = ps.groupby(["season", "position", ps.is_import.astype(bool)]).MIN_total.sum().unstack(fill_value=0)
    g.columns = ["domestic", "imp"]
    g["share"] = g.imp / (g.imp + g.domestic)
    return g.reset_index()


def age_performance(imports: pd.DataFrame) -> dict:
    d = imports.dropna(subset=["age", "PPG"])
    r = float(np.corrcoef(d.age, d.PPG)[0, 1])
    ci = fisher_ci(r, len(d))
    return {"r": r, "lo": ci.lo, "hi": ci.hi, "n": len(d)}


def similar_players(imports: pd.DataFrame, target_index, k: int = 5) -> pd.DataFrame:
    """Хэв маягийн 7 үзүүлэлтийг стандартчилж, хамгийн ойр k гадаад тоглогч-улирлыг буцаана (тухайн хүнийг өөрийг нь хасна)."""
    feats = list(SIM_FEATURES)
    d = imports.dropna(subset=feats).copy()
    z = (d[feats] - d[feats].mean()) / d[feats].std(ddof=0)
    target = z.loc[target_index]
    dist = np.sqrt(((z - target) ** 2).sum(axis=1))
    me = d.loc[target_index, "player_id"]
    # нэг хүнийг (хоёр улиралд тоглосон бол) хамгийн ойр улирлаар нь нэг л удаа харуулна
    out = (d.assign(distance=dist)[d.player_id != me].sort_values("distance").drop_duplicates("player_id").head(k))
    return out


def position_concentration(players_season: pd.DataFrame, position: str = "C", n_boot: int = 2000,
                           seed: int = SEED) -> pd.DataFrame:
    """Тухайн байрлалын минутын гадаад тоглогчийн хувь − бүх минутын гадаад тоглогчийн хувь (улирал бүр, 95% хүрээ).
    Хүрээг тоглогч-улирлаар дахин түүвэрлэж тооцно."""
    rng = np.random.default_rng(seed)
    rows = []
    for season, d in players_season[players_season.position.notna()].groupby("season"):
        imp = d.is_import.astype(bool).to_numpy()
        mins = d.MIN_total.fillna(0).to_numpy(float)
        pos = (d.position == position).to_numpy()

        def stat(idx):
            m, i, p = mins[idx], imp[idx], pos[idx]
            return (m * i * p).sum() / max((m * p).sum(), 1e-9) - (m * i).sum() / max(m.sum(), 1e-9)
        est = stat(np.arange(len(d)))
        boots = np.array([stat(rng.integers(0, len(d), len(d))) for _ in range(n_boot)])
        lo, hi = np.percentile(boots, [2.5, 97.5])
        overall = (mins * imp).sum() / mins.sum()
        rows.append({"season": season, "position": position, "overall_share": overall, "pos_share": overall + est,
                     "diff": est, "lo": lo, "hi": hi})
    return pd.DataFrame(rows)


def hypotheses(players_season: pd.DataFrame, imports: pd.DataFrame) -> pd.DataFrame:
    """Гадаад тоглогч, солилцооны 4 таамаглал: дүгнэлтийг 95% хүрээ 0-ийг (эсвэл 0 хамаарлыг) агуулах эсэхээр гаргана."""
    ret = retention(players_season, imports)
    rc = compare_groups(ret, ret.stayed, {"PPG": "Оноо / тоглолт"}).iloc[0]
    known = imports[imports.level.isin(LEVELS)]
    lc = compare_groups(known, known.level.isin(HIGH_LEVELS), {"PPG": "Оноо / тоглолт"}).iloc[0]
    pc = position_concentration(players_season)
    age = age_performance(imports)

    def verdict(lo, hi):
        return "Батлагдсан" if lo > 0 else ("Няцаагдсан" if hi < 0 else "Баттай биш")
    rows = [
        {"hid": "H6", "statement": "MBA-д олон оноо авсан гадаад тоглогч дараа улиралд лигт үлддэг",
         "measure": "Үлдсэн ба явсан тоглогчийн голч онооны зөрүү", "estimate": rc["diff"], "lo": rc.diff_lo,
         "hi": rc.diff_hi, "n": f"{int(rc.n_yes)} үлдсэн, {int(rc.n_no)} явсан", "verdict": verdict(rc.diff_lo, rc.diff_hi)},
        {"hid": "H7", "statement": "Өндөр түвшний лигээс ирсэн гадаад тоглогч MBA-д илүү оноо авдаг",
         "measure": "NBA / EuroLeague / G League ба бусад лигээс ирсэн тоглогчийн голч онооны зөрүү", "estimate": lc["diff"], "lo": lc.diff_lo, "hi": lc.diff_hi,
         "n": f"{int(lc.n_yes)} өндөр, {int(lc.n_no)} бусад", "verdict": verdict(lc.diff_lo, lc.diff_hi)},
    ]
    for r in pc.itertuples():
        rows.append({"hid": "H8", "statement": f"Багууд гадаад тоглогчийг төвийн (C) байрлалд түлхүү тоглуулдаг ({r.season.replace('-20', '–')})",
                     "measure": "Төвийн минутын гадаад хувь − нийт минутын гадаад хувь", "estimate": r.diff, "lo": r.lo,
                     "hi": r.hi, "n": r.season, "verdict": verdict(r.lo, r.hi)})
    rows.append({"hid": "H9", "statement": "Ахимаг гадаад тоглогч MBA-д илүү оноо авдаг",
                 "measure": "Нас ба тоглолтын онооны хамаарлын хүч", "estimate": age["r"], "lo": age["lo"], "hi": age["hi"],
                 "n": f"{age['n']} тоглогч-улирал", "verdict": verdict(age["lo"], age["hi"])})
    return pd.DataFrame(rows)
