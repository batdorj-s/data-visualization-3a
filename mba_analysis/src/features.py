import numpy as np
import pandas as pd

POS_GROUP = {"PG": "Guard", "SG": "Guard", "SF": "Forward", "PF": "Forward", "C": "Center"}
TIER_BINS = [-np.inf, 5, 12, 20, np.inf]
TIER_LABELS = ["Бага", "Дунд", "Өндөр", "Од"]
PYTHAG_EXP = 13.91


def _div(num, den):
    """Хуваалт; хуваагч 0 эсвэл NaN бол NaN (inf хэзээ ч биш)."""
    if isinstance(num, (pd.Series, np.ndarray)) or isinstance(den, (pd.Series, np.ndarray)):
        num_a = np.asarray(num, dtype=float)
        den_a = np.asarray(den, dtype=float)
        with np.errstate(divide="ignore", invalid="ignore"):
            out = np.where(den_a == 0, np.nan, num_a / np.where(den_a == 0, 1, den_a))
        index = num.index if isinstance(num, pd.Series) else den.index if isinstance(den, pd.Series) else None
        return pd.Series(out, index=index) if index is not None else out
    if den is None or den == 0 or (isinstance(den, float) and np.isnan(den)):
        return float("nan")
    return float(num) / float(den)


def per36(stat, minutes):
    return _div(stat, minutes) * 36


def ts_pct(pts, fga, fta):
    return _div(pts, 2 * (fga + 0.44 * fta))


def efg_pct(fgm, tpm, fga):
    return _div(fgm + 0.5 * tpm, fga)


def possessions(fga, oreb, tov, fta):
    poss = fga - oreb + tov + 0.44 * fta
    if np.isscalar(poss):
        return float(poss) if poss > 0 else float("nan")
    return poss.where(poss > 0)


def four_factors(team_games: pd.DataFrame) -> pd.DataFrame:
    tg = team_games.copy()
    for c in ["PTS", "FGM", "FGA", "TPM", "FTM", "FTA", "OREB", "DREB", "TOV"]:
        tg[c] = pd.to_numeric(tg[c], errors="coerce").astype(float)
    tg["poss"] = possessions(tg.FGA, tg.OREB, tg.TOV, tg.FTA)
    opp = tg[["game_id", "side", "team_key", "PTS", "DREB", "poss"]].rename(columns={
        "side": "opp_side", "team_key": "opp_key", "PTS": "opp_pts", "DREB": "opp_dreb", "poss": "opp_poss"})
    out = tg.merge(opp, on="game_id")
    out = out[out.side != out.opp_side].drop(columns="opp_side").reset_index(drop=True)
    out["efg"] = efg_pct(out.FGM, out.TPM, out.FGA)
    out["tov_pct"] = _div(out.TOV, out.poss)
    out["orb_pct"] = _div(out.OREB, out.OREB + out.opp_dreb)
    out["ftr"] = _div(out.FTM, out.FGA)
    out["ortg"] = 100 * _div(out.PTS, out.poss)
    out["drtg"] = 100 * _div(out.opp_pts, out.opp_poss)
    out["net"] = out.ortg - out.drtg
    out["win"] = out.PTS > out.opp_pts
    return out


def add_player_categories(df: pd.DataFrame, season_start_year: int | pd.Series) -> pd.DataFrame:
    out = df.copy()
    out["age"] = (season_start_year - pd.to_numeric(out["birth_year"], errors="coerce")).astype("Int64")
    out["pos_group"] = out["position"].map(POS_GROUP)
    out["scorer_tier"] = pd.cut(out["PPG"], TIER_BINS, labels=TIER_LABELS, right=False).astype(object)
    return out


def pythag(pf, pa, exponent: float = PYTHAG_EXP):
    pf_e, pa_e = np.power(pf, exponent, dtype=float), np.power(pa, exponent, dtype=float)
    return _div(pf_e, pf_e + pa_e)
