"""Тоглолтын дундах ялах магадлал: онооны зөрүү + үлдсэн хугацаа + тоглолтын өмнөх хүч → гэрийн баг ялах магадлал.

Тоглолт бүрийг минут тутам (0–39 дэх минут) «зогсоож» төлөв болгоно → ~10,000 мөр (252 тоглолт биш).
Нэг тоглолтын төлөвүүд хоорондоо хамааралтай тул шалгалтыг тоглолтоор бүлэглэж (GroupKFold) хийнэ: нэг тоглолтын
мөрүүд сургалт, тест хоёрт зэрэг орохгүй. Тоглолтын өмнөх Elo нь зөвхөн өмнөх тоглолтуудаас тооцогдсон тул ирээдүйн
мэдээлэл ордоггүй.
"""
import numpy as np
import pandas as pd
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import GroupKFold

SEED = 42
REG_SEC = 2400
FEATURES = ["margin", "margin_scaled", "elo_diff", "elo_x_time"]


def features(margin, t_left, elo_diff) -> pd.DataFrame:
    """margin_scaled: үлдсэн хугацаа багасах тусам ижил зөрүү илүү шийдвэрлэх болно (√ минут-аар хуваана)."""
    margin, t_left, elo_diff = (np.asarray(v, float) for v in (margin, t_left, elo_diff))
    return pd.DataFrame({"margin": margin, "margin_scaled": margin / np.sqrt(t_left / 60 + 1),
                         "elo_diff": elo_diff / 100, "elo_x_time": elo_diff / 100 * t_left / REG_SEC})


def build_states(pbp: pd.DataFrame, games: pd.DataFrame, minutes=range(0, 40)) -> pd.DataFrame:
    """Тоглолт бүрийг минут бүрийн эхэнд онооны зөрүүтэй нь авна (эхний 40 минут, нэмэлт цаг ороогүй)."""
    g = games.set_index("game_id")
    rows = []
    for gid, e in pbp.sort_values(["game_id", "seq"]).groupby("game_id"):
        if gid not in g.index:
            continue
        el, mg = e.elapsed.to_numpy(), e.margin.to_numpy()
        for m in minutes:
            idx = np.searchsorted(el, 60 * m, side="right") - 1
            rows.append({"game_id": gid, "season": g.at[gid, "season"], "minute": m, "t_left": REG_SEC - 60 * m,
                         "margin": int(mg[idx]) if idx >= 0 else 0,
                         "elo_diff": float(g.at[gid, "elo_pre_home"] - g.at[gid, "elo_pre_away"]),
                         "y": int(g.at[gid, "home_pts"] > g.at[gid, "away_pts"])})
    return pd.DataFrame(rows)


def _model() -> LogisticRegression:
    return LogisticRegression(C=1.0, max_iter=1000)


def leader_rule(df: pd.DataFrame) -> np.ndarray:
    """Энгийн дүрэм: одоо тэргүүлж буй баг ялна; тэнцүү бол тоглолтын өмнөх Elo өндөр нь."""
    return np.where(df.margin != 0, df.margin > 0, df.elo_diff >= 0).astype(int)


def grouped_cv(states: pd.DataFrame, n_folds: int = 5) -> pd.DataFrame:
    X, y, groups = features(states.margin, states.t_left, states.elo_diff), states.y.to_numpy(), states.game_id
    p = np.empty(len(states))
    for tr, te in GroupKFold(n_splits=n_folds).split(X, y, groups):
        p[te] = _model().fit(X.iloc[tr], y[tr]).predict_proba(X.iloc[te])[:, 1]
    return states.assign(p=p, leader=leader_rule(states))


def by_minute(cv: pd.DataFrame, n_boot: int = 1000, seed: int = SEED) -> pd.DataFrame:
    """Минут бүрийн зөв таамагласан хувь; хүрээг тоглолтоор дахин түүвэрлэж тооцно."""
    rng = np.random.default_rng(seed)
    cv = cv.assign(ok_model=((cv.p >= 0.5).astype(int) == cv.y).astype(float), ok_leader=(cv.leader == cv.y).astype(float),
                   sq=(cv.p - cv.y) ** 2)
    piv = {c: cv.pivot(index="game_id", columns="minute", values=c) for c in ("ok_model", "ok_leader")}
    idx = rng.integers(0, len(piv["ok_model"]), (n_boot, len(piv["ok_model"])))
    out = []
    for m in sorted(cv.minute.unique()):
        row = {"minute": int(m), "n": int((cv.minute == m).sum()), "brier": float(cv.loc[cv.minute == m, "sq"].mean())}
        for c, name in (("ok_model", "model"), ("ok_leader", "leader")):
            v = piv[c][m].to_numpy()
            boots = v[idx].mean(axis=1)
            row[f"acc_{name}"] = float(v.mean())
            row[f"lo_{name}"], row[f"hi_{name}"] = (float(x) for x in np.percentile(boots, [2.5, 97.5]))
        out.append(row)
    return pd.DataFrame(out)


def fit_final(states: pd.DataFrame) -> dict:
    m = _model().fit(features(states.margin, states.t_left, states.elo_diff), states.y)
    return {"intercept": float(m.intercept_[0]), "coef": dict(zip(FEATURES, map(float, m.coef_[0])))}


def win_prob(params: dict, margin, t_left, elo_diff) -> np.ndarray:
    X = features(margin, t_left, elo_diff)
    z = params["intercept"] + sum(params["coef"][f] * X[f].to_numpy() for f in FEATURES)
    return 1 / (1 + np.exp(-z))


def run_inplay(pbp: pd.DataFrame, games: pd.DataFrame, n_boot: int = 1000) -> tuple[pd.DataFrame, pd.DataFrame, dict]:
    states = build_states(pbp, games)
    cv = grouped_cv(states)
    minute = by_minute(cv, n_boot=n_boot)
    eps = 1e-6
    logloss = float(-np.mean(cv.y * np.log(cv.p + eps) + (1 - cv.y) * np.log(1 - cv.p + eps)))
    at = minute.set_index("minute")
    metrics = {"n_states": int(len(states)), "n_games": int(states.game_id.nunique()),
               "brier": float(((cv.p - cv.y) ** 2).mean()), "logloss": logloss,
               "acc": float(((cv.p >= 0.5).astype(int) == cv.y).mean()), "acc_leader": float((cv.leader == cv.y).mean()),
               "acc_minute": {str(m): float(at.loc[m, "acc_model"]) for m in (0, 10, 20, 30, 35)},
               "params": fit_final(states)}
    return cv, minute, metrics


def finalize(wp: np.ndarray, final_margin: float) -> np.ndarray:
    """Шүгэл дуугарсны дараа магадлал нь бодит үр дүн (1 эсвэл 0) болно."""
    wp = np.asarray(wp, float).copy()
    if len(wp) and final_margin != 0:
        wp[-1] = float(final_margin > 0)
    return wp
