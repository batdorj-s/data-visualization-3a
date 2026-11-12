import pandas as pd

K = 20
INIT = 1500.0
CARRY = 0.75


def expected(ra: float, rb: float) -> float:
    return 1.0 / (1.0 + 10 ** ((rb - ra) / 400))


def update(ra: float, rb: float, a_won: bool, k: float = K) -> tuple[float, float]:
    ea = expected(ra, rb)
    delta = k * ((1.0 if a_won else 0.0) - ea)
    return ra + delta, rb - delta


def run_elo(games: pd.DataFrame, k: float = K, init: float = INIT, carry: float = CARRY,
            successors: dict[str, str] | None = None) -> pd.DataFrame:
    """Тоглолт бүрийн өмнөх ба дараах Elo. Талбайн давуу тал = 0."""
    successors = successors or {}
    ratings: dict[str, tuple[float, str]] = {}

    def pre(team: str, season: str) -> float:
        if team not in ratings and successors.get(team) in ratings:
            ratings[team] = ratings[successors[team]]
        rating, last = ratings.get(team, (init, season))
        if last != season:
            rating = carry * rating + (1 - carry) * init
        return rating

    rows = []
    ordered = games.assign(_d=pd.to_datetime(games["date"])).sort_values(["_d", "game_id"], kind="stable")
    for g in ordered.itertuples(index=False):
        rh, ra = pre(g.home_key, g.season), pre(g.away_key, g.season)
        nh, na = update(rh, ra, g.home_pts > g.away_pts, k)
        ratings[g.home_key] = (nh, g.season)
        ratings[g.away_key] = (na, g.season)
        rows.append({"game_id": g.game_id, "home_key": g.home_key, "away_key": g.away_key,
                     "elo_pre_home": rh, "elo_pre_away": ra, "elo_post_home": nh, "elo_post_away": na})
    return pd.DataFrame(rows)
