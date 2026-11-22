"""Сагсан бөмбөгийн нэмэлт олдворуудын тооцоо (график, dashboard хоёулаа эндээс авна).

Функц бүр цэвэр хүснэгт буцаана; тодорхой бус байдлыг Wilson (хувь), Fisher (хамаарал) эсвэл тоглолтоор
дахин түүвэрлэх аргаар тооцно. Дата хангалтгүй бүлгийг хасахын оронд n-ийг нь хамт буцаана.
"""
import numpy as np
import pandas as pd

from src.pbp import ZONES
from src.uncertainty import fisher_ci, wilson_ci

SEED = 42
LEAD_BINS = [0, 3, 6, 10, 15, 100]
LEAD_LABELS = ["1–3", "4–6", "7–10", "11–15", "16+"]
CHECKPOINTS = {"1-р үеийн төгсгөл": 600, "Хагас": 1200, "3-р үеийн төгсгөл": 1800}
DIST_EDGES = [0, 1, 2, 3, 4, 5, 6, 6.75, 7.5, 8.5, 30]  # сүүлийн интервал: 8.5 м-ээс цааш бүгд


# ---------- Талбай дээрх тоглогчид (солилтоос сэргээнэ) ----------
def lineup_stints(pbp: pd.DataFrame) -> pd.DataFrame:
    """Солилтын бичлэгээс тал бүрийн талбай дээрх тоглогчдыг сэргээж, өөрчлөгдөөгүй хугацааны хэсэг (stint) болгоно.

    Мөр: game_id, period, side, players (эрэмбэлсэн tuple), seconds. Зөвхөн үндсэн 4 үе.
    """
    rows = []
    for gid, d in pbp.sort_values(["game_id", "seq"]).groupby("game_id", sort=False):
        on = {"home": set(), "away": set()}
        prev_t, prev_p = None, None
        for typ, text, side, pid, period, t in zip(d.type, d.text, d.side, d.player_id, d.period, d.elapsed):
            if prev_t is not None and period == prev_p and period <= 4 and t > prev_t:
                for s in ("home", "away"):
                    rows.append((gid, period, s, tuple(sorted(on[s])), t - prev_t))
            if typ == "sub" and isinstance(pid, str) and side in on:
                (on[side].add if "in" in str(text) else on[side].discard)(pid)
            prev_t, prev_p = t, period
    return pd.DataFrame(rows, columns=["game_id", "period", "side", "players", "seconds"])


def imports_on_court(stints: pd.DataFrame, is_import: dict, games: pd.DataFrame) -> pd.DataFrame:
    """Улирал × үе бүрт талбай дээр хэдэн гадаад тоглогч байсан хугацааны хуваарь (зөвхөн яг 5 тоглогчтой хэсэг)."""
    s = stints[stints.players.map(len) == 5].copy()
    s["k"] = s.players.map(lambda ps: sum(bool(is_import.get(p, False)) for p in ps))
    s = s.merge(games[["game_id", "season"]], on="game_id")
    sec = s.groupby(["season", "period", "k"]).seconds.sum().rename("seconds").reset_index()
    tot = sec.groupby(["season", "period"]).seconds.transform("sum")
    sec["share"] = sec.seconds / tot
    mean = (sec.k * sec.seconds).groupby([sec.season, sec.period]).sum() / sec.groupby(["season", "period"]).seconds.sum()
    return sec.merge(mean.rename("mean_k").reset_index(), on=["season", "period"])


def lineup_coverage(stints: pd.DataFrame) -> float:
    """Нийт хугацааны хэдэн хувьд талбай дээр яг 5 тоглогч сэргээгдсэн бэ (сэргээлтийн чанар)."""
    return float(stints.loc[stints.players.map(len) == 5, "seconds"].sum() / stints.seconds.sum())


def import_points_by_period(pbp: pd.DataFrame, is_import: dict, games: pd.DataFrame) -> pd.DataFrame:
    e = pbp[pbp.type.isin(["2pt", "3pt", "ft"]) & (pbp.made == True) & (pbp.period <= 4)]  # noqa: E712
    e = e.assign(imp=e.player_id.map(is_import).fillna(False).astype(bool)).merge(games[["game_id", "season"]], on="game_id")
    g = e.groupby(["season", "period"]).apply(lambda d: d.loc[d.imp, "points"].sum() / d.points.sum(), include_groups=False)
    return g.rename("import_pts_share").reset_index()


# ---------- Тэргүүлэл ба эргэлт ----------
def _margin_at(pbp: pd.DataFrame, t: int) -> pd.Series:
    return pbp[pbp.elapsed <= t].sort_values(["game_id", "seq"]).groupby("game_id").margin.last()


def lead_safety(pbp: pd.DataFrame, games: pd.DataFrame) -> pd.DataFrame:
    """Үеийн төгсгөлд N оноогоор тэргүүлсэн баг хэдэн хувьд нь ялсан бэ (Wilson 95%)."""
    g = games.set_index("game_id")
    home_won = g.home_pts > g.away_pts
    rows = []
    for name, t in CHECKPOINTS.items():
        m = _margin_at(pbp, t)
        m = m[m != 0]
        won = np.where(m > 0, home_won.reindex(m.index), ~home_won.reindex(m.index))
        df = pd.DataFrame({"lead": m.abs().to_numpy(), "won": won})
        df["bin"] = pd.cut(df.lead, LEAD_BINS, labels=LEAD_LABELS)
        for b, part in df.groupby("bin", observed=True):
            ci = wilson_ci(int(part.won.sum()), len(part))
            rows.append({"checkpoint": name, "bin": str(b), "n": len(part), "est": ci.est, "lo": ci.lo, "hi": ci.hi})
    return pd.DataFrame(rows)


def comebacks(pbp: pd.DataFrame) -> pd.DataFrame:
    """Тоглолт бүрт ялсан баг хамгийн ихдээ хэдэн оноогоор хоцорч байсан бэ."""
    rows = []
    for gid, d in pbp.sort_values(["game_id", "seq"]).groupby("game_id", sort=False):
        final = d.margin.iloc[-1]
        if final == 0:
            continue
        m = d.margin.to_numpy() * (1 if final > 0 else -1)
        half = m[np.searchsorted(d.elapsed.to_numpy(), 1200, side="right") - 1]
        rows.append({"game_id": gid, "deficit": int(max(0, -m.min())), "final_margin": int(abs(final)),
                     "trailed_at_half": bool(half < 0)})
    return pd.DataFrame(rows)


# ---------- Шидэлт ----------
def _pts(shots: pd.DataFrame) -> pd.Series:
    return shots.made.astype(int) * (2 + shots.three.astype(int))


def distance_curve(shots: pd.DataFrame, n_boot: int = 1000, seed: int = SEED) -> pd.DataFrame:
    """Сагснаас зайн интервал бүрт шидэлт бүрт ногдох оноо; хүрээг тоглолтоор дахин түүвэрлэнэ."""
    s = shots[shots.location_ok].assign(pts=_pts)
    s["bin"] = pd.cut(s.dist, DIST_EDGES, include_lowest=True)
    games = s.game_id.unique()
    idx = np.random.default_rng(seed).integers(0, len(games), (n_boot, len(games)))
    per = s.groupby(["game_id", "bin"], observed=False).pts.agg(["sum", "size"])
    rows = []
    for b in s.bin.cat.categories:
        tot = per["sum"].xs(b, level="bin").reindex(games, fill_value=0).to_numpy()
        n = per["size"].xs(b, level="bin").reindex(games, fill_value=0).to_numpy()
        boots = tot[idx].sum(1) / np.maximum(n[idx].sum(1), 1)
        part = s[s.bin == b]
        rows.append({"lo_m": b.left if b.left > 0 else 0.0, "hi_m": b.right, "mid": (max(b.left, 0) + min(b.right, 10.0)) / 2,
                     "n": int(n.sum()), "fg": float(part.made.mean()), "three_share": float(part.three.mean()),
                     "pps": float(tot.sum() / max(n.sum(), 1)), "lo": float(np.percentile(boots, 2.5)),
                     "hi": float(np.percentile(boots, 97.5))})
    return pd.DataFrame(rows)


def assisted_share(shots: pd.DataFrame, assists: pd.DataFrame) -> pd.DataFrame:
    """Оносон шидэлтийн хэд нь дамжуулалтаас гарсан бэ: бүс × тоглогчийн төрөл (Wilson 95%).

    Дамжуулалтын зөвхөн шидэлттэй холбогдсон хэсэг тоологдох тул хувь нь доод тооцоо.
    """
    made = shots[shots.location_ok & shots.made & shots.is_import.notna()].merge(
        assists[["game_id", "seq"]].assign(assisted=True), on=["game_id", "seq"], how="left")
    made["assisted"] = made.assisted.fillna(False).astype(bool)
    rows = []
    for (zone, imp), part in made.groupby(["zone", made.is_import.astype(bool)]):
        ci = wilson_ci(int(part.assisted.sum()), len(part))
        rows.append({"zone": zone, "is_import": bool(imp), "n": len(part), "est": ci.est, "lo": ci.lo, "hi": ci.hi})
    out = pd.DataFrame(rows)
    out["zone"] = pd.Categorical(out.zone, ZONES)
    return out.sort_values(["zone", "is_import"]).reset_index(drop=True)


# ---------- Баг ----------
def team_ratings(team_games: pd.DataFrame) -> pd.DataFrame:
    """Баг-улирал бүрийн 100 довтолгоонд авсан/алдсан оноо, хурд (довтолгоо/тоглолт), ялалтын хувь (үндсэн шат)."""
    reg = team_games[team_games.phase == "regular"]
    return reg.groupby(["season", "team_key", "team"]).agg(
        ortg=("ortg", "mean"), drtg=("drtg", "mean"), pace=("poss", "mean"), win=("win", "mean"),
        games=("win", "size")).reset_index()


# ---------- Тоглогч ----------
def usage_table(player_games: pd.DataFrame, min_minutes: float = 200) -> pd.DataFrame:
    """Довтолгооны ачаалал (талбай дээр байх үедээ багийн довтолгооны хэдийг дуусгадаг) ба шидэлтийн оновч.

    Ачаалал = (шидэлт + 0.44·торгууль + бөмбөг алдалт) × (багийн минут / 5) / (тоглогчийн минут × багийн нийлбэр).
    """
    p = player_games[player_games.phase == "regular"].copy()
    p["use"] = p.FGA + 0.44 * p.FTA + p.TOV
    team = p.groupby(["game_id", "team_key"]).agg(t_use=("use", "sum"), t_min=("MIN", "sum")).reset_index()
    p = p.merge(team, on=["game_id", "team_key"])
    a = p.groupby(["player_id", "season"]).agg(
        name=("name", "first"), team=("team", "last"), is_import=("is_import", "max"), gp=("MIN", "size"),
        minutes=("MIN", "sum"), use=("use", "sum"), t_use=("t_use", "sum"), t_min=("t_min", "sum"), pts=("PTS", "sum"),
        fga=("FGA", "sum"), fta=("FTA", "sum")).reset_index()
    a = a[a.minutes >= min_minutes].copy()
    a["usage"] = a.use * (a.t_min / 5) / (a.minutes * a.t_use)
    a["ts"] = a.pts / (2 * (a.fga + 0.44 * a.fta))
    a["ppg"] = a.pts / a.gp
    a["name"] = a.name.str.title()
    return a[["player_id", "season", "name", "team", "is_import", "gp", "minutes", "usage", "ts", "ppg"]]


STABILITY_STATS = {"reb36": "Самбар (36 минутад)", "ast36": "Дамжуулалт (36 минутад)", "tpa_rate": "3 оноогоор шидсэн хувь",
                   "PPG": "Оноо / тоглолт", "MIN": "Минут / тоглолт", "pts36": "Оноо (36 минутад)",
                   "ts_pct": "Шидэлтийн оновч", "tp_pct": "3 онооны оновч"}


def stability_pairs(players_season: pd.DataFrame, col: str, min_tsa: float = 50, min_tpa: float = 30) -> pd.DataFrame:
    """Хоёр улиралд хоёуланд нь тоглосон тоглогч бүрийн тухайн үзүүлэлтийн өмнөх (prev) ба сүүлийн (now) улирлын утга.
    Цөөн шидэлттэй тоглогчийг хасна (3 онооны оновчид 30+ гурвын шидэлт, бусдад 50+ шидэлтийн оролдлого)."""
    ps = players_season[players_season.eligible.astype(bool)].copy()
    ps["tsa"] = ps.FGA + 0.44 * ps.FTA
    ps["tp_pct"] = ps.TPM / ps.TPA.where(ps.TPA > 0)
    seasons = sorted(ps.season.unique())[-2:]
    d = ps[(ps.TPA >= min_tpa) if col == "tp_pct" else (ps.tsa >= min_tsa)]
    w = d.pivot_table(index="player_id", columns="season", values=col, aggfunc="first").reindex(columns=seasons).dropna()
    info = ps.sort_values("season").drop_duplicates("player_id", keep="last").set_index("player_id")
    return pd.DataFrame({"player_id": w.index, "player_name": info.player_name.reindex(w.index).to_numpy(),
                         "team": info.team.reindex(w.index).to_numpy(), "prev": w[seasons[0]].to_numpy(),
                         "now": w[seasons[1]].to_numpy(), "prev_season": seasons[0], "season": seasons[1]})


def season_stability(players_season: pd.DataFrame, min_tsa: float = 50, min_tpa: float = 30) -> pd.DataFrame:
    """Хоёр улиралд хоёуланд нь тоглосон тоглогчийн үзүүлэлт улирал хооронд хэр хадгалагддаг вэ (хамаарал, Fisher 95%)."""
    rows = []
    for col, label in STABILITY_STATS.items():
        w = stability_pairs(players_season, col, min_tsa, min_tpa)
        if len(w) < 5:
            continue
        r = float(w.prev.corr(w.now))
        ci = fisher_ci(r, len(w))
        rows.append({"stat": col, "label": label, "n": len(w), "r": r, "lo": ci.lo, "hi": ci.hi})
    return pd.DataFrame(rows).sort_values("r", ascending=False).reset_index(drop=True)


# ---------------------------------------------------------------- +/- (Plus/Minus) ба on/off
GAME_SEC = 2400  # FIBA: 4 × 10 минут


def plus_minus_games(pbp: pd.DataFrame) -> pd.DataFrame:
    """Тоглогч-тоглолт бүрийн талбай дээр байсан хугацаа (sec) ба тэр хугацаанд багийн онооны зөрүү (pm, +/-).

    MBA-ийн хайрцаг оноонд +/- байхгүй тул тоглолтын явцын бичлэгээс тооцно: солилтын бичлэгээр талбай дээрх тоглогчдыг
    сэргээж, хоёр бичлэгийн хоорондох онооны өөрчлөлтийг тэр үед талбай дээр байсан тоглогч бүрт өгнө (нэмэлт цаг орно).
    valid = тухайн тал дээр 5 тоглогчийн +/--ийн нийлбэр 5 × эцсийн онооны зөрүүтэй яг тэнцүү (солилтын бичлэг бүрэн).
    """
    rows = []
    for gid, d in pbp.sort_values(["game_id", "seq"]).groupby("game_id", sort=False):
        on = {"home": set(), "away": set()}
        pt = pp = ph = pa = None
        for typ, text, side, pid, per, t, h, a in zip(d.type, d.text, d.side, d.player_id, d.period, d.elapsed, d.home, d.away):
            if pt is not None and per == pp and t >= pt:
                diff = (h - ph) - (a - pa)
                for s, sign in (("home", 1), ("away", -1)):
                    for p in on[s]:
                        rows.append((gid, s, p, t - pt, sign * diff))
            if typ == "sub" and isinstance(pid, str) and side in on:
                (on[side].add if "in" in str(text) else on[side].discard)(pid)
            pt, pp, ph, pa = t, per, h, a
    out = (pd.DataFrame(rows, columns=["game_id", "side", "player_id", "sec", "pm"])
           .groupby(["game_id", "side", "player_id"], as_index=False).sum())
    final = pbp.groupby("game_id").agg(h=("home", "last"), a=("away", "last"), game_sec=("elapsed", "max"))
    out = out.merge(final, left_on="game_id", right_index=True)
    out["team_margin"] = np.where(out.side == "home", out.h - out.a, out.a - out.h)
    team_sum = out.groupby(["game_id", "side"]).pm.transform("sum")
    out["valid"] = team_sum == 5 * out.team_margin
    return out.drop(columns=["h", "a"])


def plus_minus_season(pmg: pd.DataFrame, player_games: pd.DataFrame, n_boot: int = 1000, seed: int = SEED) -> pd.DataFrame:
    """Тоглогч-улирал бүрийн +/- (зөвхөн солилтын бичлэг бүрэн тоглолтоор).

    pm40     = талбай дээр байхад 40 минутад ногдох багийн онооны зөрүү (95% хүрээ: тоглолтоор дахин түүвэрлэж)
    on_off40 = тоглогч талбай дээр байх үеийн pm40 − сэлгээнд байх үеийн багийн онооны зөрүү (40 минутад)
    """
    info = player_games[["game_id", "player_id", "season", "team", "is_import"]].drop_duplicates(["game_id", "player_id"])
    d = pmg[pmg.valid & (pmg.sec > 0)].merge(info, on=["game_id", "player_id"], how="inner")
    d = d.assign(off_sec=(d.game_sec - d.sec).clip(lower=0), off_pm=d.team_margin - d.pm)
    rng = np.random.default_rng(seed)
    rows = []
    for (pid, season), g in d.groupby(["player_id", "season"]):
        pm, sec = g.pm.to_numpy(float), g.sec.to_numpy(float)
        idx = rng.integers(0, len(g), (n_boot, len(g)))
        boot = pm[idx].sum(1) / np.maximum(sec[idx].sum(1), 1) * GAME_SEC
        pm40 = pm.sum() / sec.sum() * GAME_SEC
        off_sec = g.off_sec.sum()
        off40 = g.off_pm.sum() / off_sec * GAME_SEC if off_sec >= 600 else np.nan  # 10-аас цөөн минут сэлгээнд бол тооцохгүй
        rows.append({"player_id": pid, "season": season, "team": g.team.iloc[-1], "is_import": bool(g.is_import.iloc[0]),
                     "games": len(g), "minutes": sec.sum() / 60, "pm": int(pm.sum()), "pm_per_game": pm.sum() / len(g),
                     "pm40": pm40, "pm40_lo": float(np.percentile(boot, 2.5)), "pm40_hi": float(np.percentile(boot, 97.5)),
                     "off40": off40, "on_off40": pm40 - off40})
    return pd.DataFrame(rows)
