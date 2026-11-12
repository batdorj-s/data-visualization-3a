import math
from typing import Callable, NamedTuple

import numpy as np
import pandas as pd
from scipy.stats import norm


class CI(NamedTuple):
    est: float
    lo: float
    hi: float


def _z(alpha: float) -> float:
    return float(norm.ppf(1 - alpha / 2))


def bootstrap_distribution(df: pd.DataFrame, group_col: str, stat: Callable[[pd.DataFrame], float],
                           n_boot: int = 2000, seed: int = 42) -> np.ndarray:
    """Бүлгийг (жишээ нь game_id) буцаалттайгаар дахин түүвэрлэж stat-ийн тархалтыг буцаана."""
    groups = np.unique(df[group_col].to_numpy())
    positions = df.groupby(group_col, sort=True).indices
    idx_by_group = [positions[g] for g in groups]
    rng = np.random.default_rng(seed)
    out = np.empty(n_boot)
    for b in range(n_boot):
        pick = rng.integers(0, len(groups), len(groups))
        out[b] = stat(df.iloc[np.concatenate([idx_by_group[i] for i in pick])])
    return out


def cluster_bootstrap(df: pd.DataFrame, group_col: str, stat: Callable[[pd.DataFrame], float],
                      n_boot: int = 2000, seed: int = 42, alpha: float = 0.05) -> CI:
    dist = bootstrap_distribution(df, group_col, stat, n_boot=n_boot, seed=seed)
    lo, hi = np.percentile(dist, [100 * alpha / 2, 100 * (1 - alpha / 2)])
    return CI(float(stat(df)), float(lo), float(hi))


def wilson_ci(k: int, n: int, alpha: float = 0.05) -> CI:
    if n == 0:
        return CI(float("nan"), float("nan"), float("nan"))
    z = _z(alpha)
    p = k / n
    denom = 1 + z * z / n
    center = (p + z * z / (2 * n)) / denom
    half = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / denom
    return CI(p, max(0.0, center - half), min(1.0, center + half))


def fisher_ci(r: float, n: int, alpha: float = 0.05) -> CI:
    if n <= 3 or abs(r) >= 1:
        return CI(float(r), float(r), float(r))
    zr, se = math.atanh(r), 1 / math.sqrt(n - 3)
    z = _z(alpha)
    return CI(float(r), math.tanh(zr - z * se), math.tanh(zr + z * se))


def funnel_limits(p0: float, n: np.ndarray, z: float) -> tuple[np.ndarray, np.ndarray]:
    n = np.asarray(n, dtype=float)
    se = np.sqrt(p0 * (1 - p0) / n)
    return np.clip(p0 - z * se, 0.0, 1.0), np.clip(p0 + z * se, 0.0, 1.0)
