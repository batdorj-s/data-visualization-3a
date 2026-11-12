from typing import NamedTuple

import numpy as np
import pandas as pd
from scipy import stats

from src.uncertainty import fisher_ci, wilson_ci

NUMERIC_COLS = ["PPG", "RPG", "APG", "MIN", "ts_pct", "height_cm", "age"]
CATEGORICAL_COLS = ["position", "pos_group", "team", "is_import", "region", "scorer_tier"]


class HypothesisResult(NamedTuple):
    hid: str
    statement: str
    estimate: float
    ci_lo: float
    ci_hi: float
    null_value: float
    p_value: float
    n: int
    method: str


def _describe(s: pd.Series) -> dict:
    s = pd.to_numeric(s, errors="coerce").dropna().astype(float)
    if s.empty:
        return {"n": 0}
    q1, q2, q3 = s.quantile([0.25, 0.5, 0.75])
    return {"n": int(s.size), "mean": round(s.mean(), 4), "median": s.median(), "mode": s.mode().min(),
            "std": s.std(ddof=1), "min": s.min(), "max": s.max(), "q1": q1, "q2": q2, "q3": q3,
            "iqr": q3 - q1, "skew": s.skew()}


def describe_numeric(df: pd.DataFrame, cols, by: str | None = None) -> pd.DataFrame:
    rows = []
    groups = [("Бүгд", df)] + (list(df.groupby(by, observed=True)) if by else [])
    for name, part in groups:
        for c in cols:
            if c in part.columns:
                rows.append({"variable": c, "group": str(name), **_describe(part[c])})
    out = pd.DataFrame(rows)
    return out if by else out.drop(columns="group")


def describe_categorical(df: pd.DataFrame, cols) -> pd.DataFrame:
    rows = []
    for c in cols:
        if c not in df.columns:
            continue
        counts = df[c].value_counts(dropna=True)
        total = counts.sum()
        top = counts.max() if total else 0
        for value, count in counts.items():
            rows.append({"variable": c, "value": value, "count": int(count),
                         "pct": round(100 * count / total, 2), "is_mode": bool(count == top)})
    return pd.DataFrame(rows)


def describe_games(games: pd.DataFrame) -> pd.DataFrame:
    df = pd.DataFrame({"total_pts": games.home_pts + games.away_pts,
                       "margin": (games.home_pts - games.away_pts).abs()})
    qh = games.quarters_home.str.split("|", expand=True).iloc[:, :4].astype(float)
    qa = games.quarters_away.str.split("|", expand=True).iloc[:, :4].astype(float)
    quarters = pd.DataFrame({f"q{i + 1}_pts": pd.concat([qh[i], qa[i]], ignore_index=True) for i in range(4)})
    rows = [{"variable": c, **_describe(df[c])} for c in df.columns]
    rows += [{"variable": c, **_describe(quarters[c])} for c in quarters.columns]
    return pd.DataFrame(rows)


def eval_h1(players: pd.DataFrame, n_boot: int = 2000, seed: int = 42) -> HypothesisResult:
    imp = players.loc[players.is_import.astype(bool), "PPG"].dropna().to_numpy(float)
    dom = players.loc[~players.is_import.astype(bool), "PPG"].dropna().to_numpy(float)
    est = float(np.median(imp) - np.median(dom))
    rng = np.random.default_rng(seed)
    boots = [np.median(rng.choice(imp, imp.size)) - np.median(rng.choice(dom, dom.size)) for _ in range(n_boot)]
    lo, hi = np.percentile(boots, [2.5, 97.5])
    u = stats.mannwhitneyu(imp, dom, alternative="greater")
    rbc = 2 * u.statistic / (imp.size * dom.size) - 1
    return HypothesisResult("H1", "Import тоглогчид дотоодынхоос илүү оноо авдаг (PPG-ийн медиан зөрүү)",
                            est, float(lo), float(hi), 0.0, float(u.pvalue), int(imp.size + dom.size),
                            f"Mann-Whitney U (нэг талт), rank-biserial r = {rbc:.2f}; CI: тоглогчоор bootstrap {n_boot}")


def eval_h2(games: pd.DataFrame) -> HypothesisResult:
    n = len(games)
    k = int((games.home_pts > games.away_pts).sum())
    ci = wilson_ci(k, n)
    p = stats.binomtest(k, n, 0.5).pvalue
    return HypothesisResult("H2", "Гэрийн баг 50%-аас илүү ялдаг (талбайн давуу тал)", ci.est, ci.lo, ci.hi,
                            0.5, float(p), n, "Binomial тест; CI: Wilson")


def eval_h4(players: pd.DataFrame) -> HypothesisResult:
    d = players[["height_cm", "RPG"]].apply(pd.to_numeric, errors="coerce").dropna()
    r, p = stats.pearsonr(d.height_cm, d.RPG)
    rho = stats.spearmanr(d.height_cm, d.RPG).statistic
    ci = fisher_ci(float(r), len(d))
    return HypothesisResult("H4", "Өндөр тоглогчид илүү их самбар авдаг (Pearson r)", float(r), ci.lo, ci.hi,
                            0.0, float(p), int(len(d)), f"Pearson r; Spearman ρ = {rho:.2f}; CI: Fisher z")
