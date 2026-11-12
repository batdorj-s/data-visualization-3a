import numpy as np
import pandas as pd
from sklearn.datasets import make_blobs

from src.models import (
    ARCHETYPE_FEATURES,
    archetype_matrix,
    cluster_composition,
    cluster_stability,
    fit_archetypes,
    name_clusters,
)


def blobs():
    X, _ = make_blobs(n_samples=150, centers=3, n_features=4, cluster_std=0.6, random_state=42)
    return X


def test_fit_archetypes_picks_three():
    res = fit_archetypes(blobs(), seed=42)
    assert res.k == 3
    assert set(res.silhouette_by_k) == set(range(2, 9))
    assert res.pca_xy.shape == (150, 2)


def test_stability_high_on_clean_blobs():
    ari, coassign = cluster_stability(blobs(), 3, n_boot=30, seed=42)
    assert ari > 0.9
    assert np.median(coassign) > 0.9
    assert coassign.min() >= 0 and coassign.max() <= 1


def test_same_seed_same_labels():
    a = fit_archetypes(blobs(), seed=42).labels
    b = fit_archetypes(blobs(), seed=42).labels
    assert (a == b).all()


def _players(n=4, minutes=(100, 200, 300, 400)):
    df = pd.DataFrame({f: np.linspace(1, 4, n) for f in ARCHETYPE_FEATURES})
    df["MIN_total"] = list(minutes)
    df["player_id"] = [f"p{i}" for i in range(n)]
    return df


def test_archetype_matrix_filters_minutes():
    df, X = archetype_matrix(_players(), min_minutes=150)
    assert df.player_id.tolist() == ["p1", "p2", "p3"]
    assert X.shape == (3, len(ARCHETYPE_FEATURES))
    assert np.allclose(X.mean(axis=0), 0, atol=1e-9)


def test_archetype_matrix_drops_nan_rows():
    p = _players()
    p.loc[3, "ts_pct"] = np.nan
    df, _ = archetype_matrix(p, min_minutes=150)
    assert df.player_id.tolist() == ["p1", "p2"]


def _centroid_z(**z):
    row = {f: 0.0 for f in ARCHETYPE_FEATURES}
    row.update(z)
    return row


def test_name_clusters_rules():
    centroids_z = pd.DataFrame([
        _centroid_z(ast36=2.0),
        _centroid_z(pts36=1.5, ts_pct=0.8),
        _centroid_z(reb36=1.2, blk36=1.0),
        _centroid_z(tpa_rate=0.3),
    ])
    names = name_clusters(centroids_z)
    assert names[0] == "Тоглолт зохион байгуулагч"
    assert names[1] == "Оноо авагч"
    assert names[2] == "Хамгаалалтын төв"
    assert names[3] == "Тэнцвэртэй"
    assert len(set(names.values())) == 4


def test_name_clusters_unique_when_same_top_feature():
    names = name_clusters(pd.DataFrame([_centroid_z(pts36=2.0, ast36=1.0), _centroid_z(pts36=1.8, tpa_rate=1.2)]))
    assert len(set(names.values())) == 2


def test_cluster_composition():
    players = pd.DataFrame({"is_import": [True, False, False, True], "position": ["PG", "C", "C", "SF"]})
    out = cluster_composition(players, np.array([0, 1, 1, 0]), {0: "A", 1: "B"}).set_index("cluster_name")
    assert out.loc["A", "n"] == 2 and out.loc["A", "pct_import"] == 100.0
    assert out.loc["B", "C"] == 2
    pos_cols = ["PG", "SG", "SF", "PF", "C"]
    assert (out[pos_cols].sum(axis=1) == out["n"]).all()


def test_min_k_respected_but_all_k_scored():
    X, _ = make_blobs(n_samples=120, centers=2, n_features=4, cluster_std=0.5, random_state=1)
    res = fit_archetypes(X, seed=42, min_k=3)
    assert res.k >= 3
    assert 2 in res.silhouette_by_k
