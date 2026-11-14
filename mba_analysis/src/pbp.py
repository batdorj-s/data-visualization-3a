"""Шидэлтийн байршил ба play-by-play-г цэвэрлэж, тоглогч, багтай холбоно (C14–C16).

Талбайн координат нь MBA сайтын ShotChart-ийн хувиргалттай ижил: 28 × 15 м, 22.75 px/м, y-ийн төв 175 px.
Баг бүрийн шидэлтийг довтолж буй сагс нь (1.575 м, 7.5 м)-т байхаар нэг тал руу эргүүлж нэгтгэнэ.
"""
import numpy as np
import pandas as pd

PX_PER_M = 22.75
HOOP = (1.575, 7.5)
PERIOD_SEC = {1: 600, 2: 600, 3: 600, 4: 600}  # FIBA: 4 × 10 мин, нэмэлт цаг 5 мин
OT_SEC = 300
NEAR_M = 3.0
MIN_NEAR_SHARE = 0.10
ZONES = ["Сагсны доор", "Будсан талбай", "Дунд зай", "Булангийн 3", "Гадна 3"]


def shot_geometry(x, y) -> pd.DataFrame:
    """Пикселийг метр болгож, довтолж буй сагс зүүн талд байхаар эргүүлнэ. dist = сагснаас зай (м)."""
    X = np.asarray(x, float) / PX_PER_M
    Y = 7.5 + (np.asarray(y, float) - 175) / PX_PER_M
    flip = X > 14
    X = np.where(flip, 28 - X, X)
    Y = np.where(flip, 15 - Y, Y)
    return pd.DataFrame({"court_x": X, "court_y": Y, "dist": np.hypot(X - HOOP[0], Y - HOOP[1])}).round(2)


def shot_zone(court_x, court_y, dist, three) -> np.ndarray:
    """FIBA-ийн талбайн шугамаар 5 бүс: хязгаарласан хагас тойрог 1.25 м, будсан талбай 5.8 × 4.9 м, булангийн 3 ≤ 3 м."""
    cx, cy, d, t = (np.asarray(v) for v in (court_x, court_y, dist, three))
    paint = (cx <= 5.8) & (np.abs(cy - 7.5) <= 2.45)
    return np.select([~t & (d <= 1.25), ~t & paint, ~t, t & (cx <= 3.0)], ZONES[:4], ZONES[4])


def _player_keys(pg: pd.DataFrame) -> pd.DataFrame:
    return pg[["game_id", "side", "number", "player_id", "player_slug", "team_key", "is_import"]].drop_duplicates(
        ["game_id", "side", "number"])


def clean_shots(shots: pd.DataFrame, pg: pd.DataFrame) -> tuple[pd.DataFrame, dict]:
    """Тоглогч (тоглолт, тал, дугаар)-аар холбож, байршил, бүс, 2/3 онооны зөрчлийг тэмдэглэнэ."""
    s = shots.merge(_player_keys(pg), on=["game_id", "side", "number"], how="left", validate="many_to_one")
    s = pd.concat([s.reset_index(drop=True), shot_geometry(s.x, s.y)], axis=1)
    s["zone"] = shot_zone(s.court_x, s.court_y, s.dist, s.three.astype(bool))
    # 3 онооны шугам 6.75 м (булан 6.6 м): шугамаас эрс зөрсөн шидэлтийг байршлын шинжилгээнээс хасна
    mismatch = (s.three & (s.dist < 6.3)) | (~s.three & (s.dist > 7.0))
    # Зарим тоглолтод байршлыг бүртгээгүй: 2 онооны бүх шидэлт сагснаас хол, цөөн тогтмол цэг дээр байдаг.
    # Хэвийн тоглолтод 2 онооны шидэлтийн 60%+ нь 3 м дотор байдаг тул 10%-иас бага бол бүртгэгдээгүй гэж үзнэ.
    near = (~s.three & (s.dist <= NEAR_M)).groupby(s.game_id).sum() / (~s.three).groupby(s.game_id).sum().clip(lower=1)
    unrecorded = set(near.index[near < MIN_NEAR_SHARE])
    in_unrecorded = s.game_id.isin(unrecorded)
    s["location_ok"] = ~mismatch & ~in_unrecorded
    stats = {"shots": len(s), "unlinked": int(s.player_id.isna().sum()),
             "bad_location": int((mismatch & ~in_unrecorded).sum()), "unrecorded_games": len(unrecorded),
             "unrecorded_shots": int(in_unrecorded.sum())}
    return s.drop(columns=["player", "shot_player_id", "player_slug", "x", "y"]), stats


def _clock_seconds(clock: pd.Series) -> pd.Series:
    mm_ss = clock.fillna("00:00").str.split(":", expand=True).astype(int)
    return mm_ss[0] * 60 + mm_ss[1]


def clean_pbp(pbp: pd.DataFrame, pg: pd.DataFrame, games: pd.DataFrame) -> tuple[pd.DataFrame, dict]:
    """Цагийг секунд болгож, тоглолтын эхнээс өнгөрсөн хугацаа, онооны зөрүү, тоглогч, багийг нэмнэ."""
    e = pbp.sort_values(["game_id", "seq"]).reset_index(drop=True)
    length = e.period.map(PERIOD_SEC).fillna(OT_SEC)
    e["sec_left_period"] = _clock_seconds(e.clock)
    start = (e.period - 1).clip(upper=4) * 600 + (e.period - 5).clip(lower=0) * OT_SEC
    e["elapsed"] = (start + (length - e.sec_left_period)).astype(int)
    for col in ("home", "away"):
        e[col] = e.groupby("game_id")[col].ffill().fillna(0).astype(int)
    e["margin"] = e.home - e.away
    slug_to_id = dict(zip(pg.player_slug, pg.player_id))
    e["player_id"] = e.player_slug.map(slug_to_id)
    sides = games.set_index("game_id")[["home_team_key", "away_team_key"]]
    e = e.join(sides, on="game_id")
    e["team_key"] = np.where(e.side == "home", e.home_team_key, np.where(e.side == "away", e.away_team_key, None))
    needs_player = e.type.isin(["2pt", "3pt", "ft", "ast", "reb", "stl", "blk", "tov", "sub"]) & e.player_slug.notna()
    stats = {"events": len(e), "unlinked_players": int((needs_player & e.player_id.isna()).sum())}
    keep = ["game_id", "seq", "period", "clock", "sec_left_period", "elapsed", "side", "team_key", "player_id", "type",
            "text", "made", "points", "home", "away", "margin"]
    return e[keep], stats


def link_assists(e: pd.DataFrame, window: int = 2) -> tuple[pd.DataFrame, dict]:
    """Оновчтой дамжуулалтыг ±window үйл явдлын доторх, ижил багийн оносон шидэлттэй холбоно (дамжуулагч → оноо авагч)."""
    e = e.sort_values(["game_id", "seq"]).reset_index(drop=True)
    fg = (e.type.isin(["2pt", "3pt"]) & (e.made == True)).to_numpy()  # noqa: E712 — NaN-ийг False гэж үзнэ
    gid, side, pid = e.game_id.to_numpy(), e.side.to_numpy(), e.player_id.to_numpy()
    seq, team, pts, typ = e.seq.to_numpy(), e.team_key.to_numpy(), e.points.to_numpy(), e.type.to_numpy()
    rows, used = [], set()
    for i in np.flatnonzero(typ == "ast"):
        for off in (-1, 1, -2, 2)[: 2 * window]:
            j = i + off
            if (0 <= j < len(e) and j not in used and fg[j] and gid[j] == gid[i] and side[j] == side[i]
                    and pid[j] != pid[i]):
                used.add(j)
                rows.append({"game_id": gid[i], "seq": seq[j], "team_key": team[i], "passer_id": pid[i],
                             "scorer_id": pid[j], "points": int(pts[j]), "three": typ[j] == "3pt"})
                break
    out = pd.DataFrame(rows, columns=["game_id", "seq", "team_key", "passer_id", "scorer_id", "points", "three"])
    n_ast = int((e.type == "ast").sum())
    return out, {"assists": n_ast, "linked": len(out), "share": len(out) / n_ast if n_ast else 0.0}
