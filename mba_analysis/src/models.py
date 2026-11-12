from dataclasses import dataclass

import numpy as np
import pandas as pd
from scipy.optimize import linear_sum_assignment
from sklearn.cluster import KMeans
from sklearn.decomposition import PCA
from sklearn.metrics import adjusted_rand_score, silhouette_score
from sklearn.preprocessing import StandardScaler

SEED = 42
ARCHETYPE_FEATURES = ["pts36", "reb36", "ast36", "stl36", "blk36", "tpa_rate", "ftr", "ts_pct"]
ARCHETYPE_NAMES = {
    "pts36": "Оноо авагч", "ts_pct": "Оноо авагч", "ast36": "Тоглолт зохион байгуулагч",
    "reb36": "Хамгаалалтын төв", "blk36": "Хамгаалалтын төв", "tpa_rate": "Гурвын мэргэн",
    "stl36": "Идэвхтэй хамгаалагч", "ftr": "Сагс руу дайрагч",
}
BALANCED = "Тэнцвэртэй"
BALANCED_Z = 0.5
POSITIONS = ["PG", "SG", "SF", "PF", "C"]


@dataclass
class ArchetypeResult:
    k: int
    labels: np.ndarray
    inertia_by_k: dict
    silhouette_by_k: dict
    centroids_z: pd.DataFrame
    pca_xy: np.ndarray
    model: KMeans
    scaler: StandardScaler | None = None


def archetype_matrix(players: pd.DataFrame, min_minutes: float = 150) -> tuple[pd.DataFrame, np.ndarray]:
    df = players[players["MIN_total"] >= min_minutes].dropna(subset=ARCHETYPE_FEATURES).reset_index(drop=True)
    scaler = StandardScaler()
    X = scaler.fit_transform(df[ARCHETYPE_FEATURES].to_numpy(float))
    df.attrs["scaler"] = scaler
    return df, X


def _kmeans(k: int, seed: int) -> KMeans:
    return KMeans(n_clusters=k, n_init=10, random_state=seed)


def fit_archetypes(X: np.ndarray, k_range=range(2, 9), seed: int = SEED, k: int | None = None,
                   scaler: StandardScaler | None = None) -> ArchetypeResult:
    inertia, sil = {}, {}
    for kk in k_range:
        m = _kmeans(kk, seed).fit(X)
        inertia[kk] = float(m.inertia_)
        sil[kk] = float(silhouette_score(X, m.labels_))
    chosen = k if k is not None else max(sil, key=sil.get)
    model = _kmeans(chosen, seed).fit(X)
    cols = ARCHETYPE_FEATURES if X.shape[1] == len(ARCHETYPE_FEATURES) else [f"f{i}" for i in range(X.shape[1])]
    return ArchetypeResult(chosen, model.labels_, inertia, sil, pd.DataFrame(model.cluster_centers_, columns=cols),
                           PCA(n_components=2, random_state=seed).fit_transform(X), model, scaler)


def _align(base: np.ndarray, pred: np.ndarray, k: int) -> np.ndarray:
    cont = np.zeros((k, k))
    for b, p in zip(base, pred):
        cont[p, b] += 1
    rows, cols = linear_sum_assignment(-cont)
    mapping = dict(zip(rows, cols))
    return np.array([mapping.get(p, -1) for p in pred])


def cluster_stability(X: np.ndarray, k: int, n_boot: int = 100, seed: int = SEED) -> tuple[float, np.ndarray]:
    base = _kmeans(k, seed).fit(X).labels_
    rng = np.random.default_rng(seed)
    aris, agree = [], np.zeros(len(X))
    for b in range(n_boot):
        idx = rng.integers(0, len(X), len(X))
        pred = _kmeans(k, seed + b + 1).fit(X[idx]).predict(X)
        aris.append(adjusted_rand_score(base, pred))
        agree += _align(base, pred, k) == base
    return float(np.mean(aris)), agree / n_boot


def name_clusters(centroids_z: pd.DataFrame) -> dict[int, str]:
    names: dict[int, str] = {}
    used: set[str] = set()
    for i, row in centroids_z.iterrows():
        ranked = row.sort_values(ascending=False)
        name = BALANCED
        if ranked.iloc[0] >= BALANCED_Z:
            candidates = [ARCHETYPE_NAMES.get(f, f) for f, z in ranked.items() if z >= BALANCED_Z]
            name = next((c for c in candidates if c not in used), candidates[0])
        base, n = name, 2
        while name in used:
            name, n = f"{base} {n}", n + 1
        names[int(i)] = name
        used.add(name)
    return names


def cluster_composition(players: pd.DataFrame, labels: np.ndarray, names: dict[int, str]) -> pd.DataFrame:
    df = players.assign(cluster_name=[names[int(l)] for l in labels])
    out = df.groupby("cluster_name").agg(n=("is_import", "size"), pct_import=("is_import", lambda s: 100 * s.mean()))
    pos = pd.crosstab(df.cluster_name, df.position).reindex(columns=POSITIONS, fill_value=0)
    return out.join(pos).fillna(0).astype({p: int for p in POSITIONS}).reset_index()
