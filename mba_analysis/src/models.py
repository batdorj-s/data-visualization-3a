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


def fit_archetypes(X: np.ndarray, k_range=range(2, 9), seed: int = SEED, k: int | None = None, min_k: int = 2,
                   scaler: StandardScaler | None = None) -> ArchetypeResult:
    inertia, sil = {}, {}
    for kk in k_range:
        m = _kmeans(kk, seed).fit(X)
        inertia[kk] = float(m.inertia_)
        sil[kk] = float(silhouette_score(X, m.labels_))
    eligible = {kk: v for kk, v in sil.items() if kk >= min_k} or sil
    chosen = k if k is not None else max(eligible, key=eligible.get)
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


WIN_FEATURES = ["elo_diff", "winpct_to_date_diff", "net_rating_last5_diff", "efg_last5_diff", "tov_pct_last5_diff"]
FF_FEATURES = ["efg", "tov_pct", "orb_pct", "ftr"]


def _pregame_team_stats(team_games: pd.DataFrame) -> pd.DataFrame:
    """Баг бүрийн тоглолт бүрийн өмнөх (тухайн өдрөөс ӨМНӨХ) статистик."""
    tg = team_games.assign(dt_=pd.to_datetime(team_games["date"])).sort_values(["dt_", "game_id"], kind="stable")
    rows = []
    for (_, _), grp in tg.groupby(["team_key", "season"], sort=False, observed=True):
        hist = []
        for r in grp.itertuples(index=False):
            prior = [h for h in hist if h[0] < r.dt_]
            last5 = prior[-5:]
            rows.append({
                "game_id": r.game_id, "team_key": r.team_key, "n_prior": len(prior),
                "winpct": np.mean([h[1] for h in prior]) if prior else np.nan,
                "net5": np.mean([h[2] for h in last5]) if last5 else np.nan,
                "efg5": np.nanmean([h[3] for h in last5]) if last5 else np.nan,
                "tov5": np.nanmean([h[4] for h in last5]) if last5 else np.nan,
            })
            hist.append((r.dt_, float(bool(r.win)), r.net, r.efg, r.tov_pct))
    return pd.DataFrame(rows)


def build_game_matrix(games: pd.DataFrame, team_games: pd.DataFrame, seed: int = SEED,
                      min_prior_games: int = 3) -> pd.DataFrame:
    tg = team_games if "date" in team_games.columns else team_games.merge(games[["game_id", "date"]], on="game_id")
    pre = _pregame_team_stats(tg).set_index(["game_id", "team_key"])
    g = games.assign(dt_=pd.to_datetime(games["date"])).sort_values(["dt_", "game_id"], kind="stable").reset_index(drop=True)
    flip = np.random.default_rng(seed).random(len(g)) < 0.5
    rows = []
    for f, r in zip(flip, g.itertuples(index=False)):
        a, b = (r.away_key, r.home_key) if f else (r.home_key, r.away_key)
        ea, eb = (r.elo_pre_away, r.elo_pre_home) if f else (r.elo_pre_home, r.elo_pre_away)
        pa, pb = pre.loc[(r.game_id, a)], pre.loc[(r.game_id, b)]
        if min(pa.n_prior, pb.n_prior) < min_prior_games:
            continue
        a_pts, b_pts = (r.away_pts, r.home_pts) if f else (r.home_pts, r.away_pts)
        rows.append({
            "game_id": r.game_id, "date": r.date, "season": r.season, "team_a": a, "team_b": b,
            "y": int(a_pts > b_pts), "elo_diff": ea - eb, "winpct_to_date_diff": pa.winpct - pb.winpct,
            "net_rating_last5_diff": pa.net5 - pb.net5, "efg_last5_diff": pa.efg5 - pb.efg5,
            "tov_pct_last5_diff": pa.tov5 - pb.tov5,
        })
    return pd.DataFrame(rows, columns=["game_id", "date", "season", "team_a", "team_b", "y", *WIN_FEATURES])


def baseline_predict(df: pd.DataFrame, kind: str) -> np.ndarray:
    col = {"elo": "elo_diff", "winpct": "winpct_to_date_diff"}[kind]
    return np.sign(df[col].fillna(0).to_numpy(float)) * 0.5 + 0.5


def make_models(seed: int = SEED) -> dict:
    from sklearn.ensemble import RandomForestClassifier
    from sklearn.linear_model import LogisticRegression
    from sklearn.pipeline import Pipeline

    return {
        "logreg": Pipeline([("scale", StandardScaler()), ("clf", LogisticRegression(C=1.0))]),
        "rf": RandomForestClassifier(n_estimators=300, max_depth=4, random_state=seed),
    }


def _metrics(y: np.ndarray, p: np.ndarray) -> dict:
    from sklearn.metrics import brier_score_loss, roc_auc_score

    y, p = np.asarray(y), np.asarray(p, float)
    auc = roc_auc_score(y, p) if len(np.unique(y)) == 2 else np.nan
    return {"accuracy": float(((p >= 0.5).astype(int) == y).mean()), "auc": float(auc),
            "brier": float(brier_score_loss(y, p))}


def _predict_all(train: pd.DataFrame, test: pd.DataFrame, models: dict) -> dict[str, np.ndarray]:
    from sklearn.base import clone

    X_tr, X_te = train[WIN_FEATURES].fillna(0).to_numpy(), test[WIN_FEATURES].fillna(0).to_numpy()
    out = {name: clone(m).fit(X_tr, train.y).predict_proba(X_te)[:, 1] for name, m in models.items()}
    out["baseline_elo"] = baseline_predict(test, "elo")
    out["baseline_winpct"] = baseline_predict(test, "winpct")
    return out


def walk_forward_cv(df: pd.DataFrame, models: dict, n_folds: int = 5, return_predictions: bool = False):
    d = df.assign(dt_=pd.to_datetime(df["date"])).sort_values(["dt_", "game_id"]).reset_index(drop=True)
    chunks = np.array_split(np.sort(d.dt_.unique()), n_folds + 1)
    metrics, preds = [], []
    for i in range(n_folds):
        train = d[d.dt_ <= chunks[i][-1]]
        test = d[d.dt_.isin(chunks[i + 1])]
        for name, p in _predict_all(train, test, models).items():
            metrics.append({"fold": i + 1, "model": name, "n_train": len(train), "n_test": len(test),
                            "train_end": train.dt_.max().date().isoformat(),
                            "test_start": test.dt_.min().date().isoformat(), **_metrics(test.y, p)})
            preds.append(pd.DataFrame({"game_id": test.game_id.values, "fold": i + 1, "model": name,
                                       "y": test.y.values, "p": p}))
    res = pd.DataFrame(metrics)
    return (res, pd.concat(preds, ignore_index=True)) if return_predictions else res


def bootstrap_metrics(y, p, n_boot: int = 1000, seed: int = SEED) -> dict:
    from src.uncertainty import CI

    y, p = np.asarray(y), np.asarray(p, float)
    point = _metrics(y, p)
    rng = np.random.default_rng(seed)
    samples = {k: [] for k in point}
    for _ in range(n_boot):
        idx = rng.integers(0, len(y), len(y))
        for k, v in _metrics(y[idx], p[idx]).items():
            samples[k].append(v)
    return {k: CI(point[k], float(np.nanpercentile(samples[k], 2.5)), float(np.nanpercentile(samples[k], 97.5)))
            for k in point}


def season_holdout(df: pd.DataFrame, models: dict, train_season: str = "2025-2026",
                   test_season: str = "2026-2027") -> pd.DataFrame:
    train, test = df[df.season == train_season], df[df.season == test_season]
    if train.empty or test.empty:
        return pd.DataFrame()
    return pd.DataFrame([{"model": name, "n_train": len(train), "n_test": len(test), **_metrics(test.y, p)}
                         for name, p in _predict_all(train, test, models).items()])


def explanatory_matrix(team_games: pd.DataFrame, seed: int = SEED) -> pd.DataFrame:
    home = team_games[team_games.side == "home"].set_index("game_id")
    away = team_games[team_games.side == "away"].set_index("game_id")
    ids = home.index.intersection(away.index).sort_values()
    flip = np.random.default_rng(seed).random(len(ids)) < 0.5
    a = np.where(flip[:, None], away.loc[ids, FF_FEATURES], home.loc[ids, FF_FEATURES]).astype(float)
    b = np.where(flip[:, None], home.loc[ids, FF_FEATURES], away.loc[ids, FF_FEATURES]).astype(float)
    y = np.where(flip, away.loc[ids, "win"], home.loc[ids, "win"]).astype(int)
    out = pd.DataFrame(a - b, columns=FF_FEATURES, index=ids)
    out["y"] = y
    return out.dropna().reset_index()


def fit_explanatory(team_games: pd.DataFrame, n_boot: int = 1000, seed: int = SEED) -> pd.DataFrame:
    from sklearn.inspection import permutation_importance
    from sklearn.linear_model import LogisticRegression

    m = explanatory_matrix(team_games, seed)
    X = StandardScaler().fit_transform(m[FF_FEATURES])
    y = m.y.to_numpy()
    clf = LogisticRegression(C=1.0).fit(X, y)
    rng = np.random.default_rng(seed)
    boots = []
    for _ in range(n_boot):
        idx = rng.integers(0, len(y), len(y))
        if len(np.unique(y[idx])) == 2:
            boots.append(LogisticRegression(C=1.0).fit(X[idx], y[idx]).coef_[0])
    boots = np.array(boots)
    perm = permutation_importance(clf, X, y, n_repeats=30, random_state=seed, scoring="roc_auc").importances
    return pd.DataFrame({
        "feature": FF_FEATURES, "coef": clf.coef_[0],
        "lo": np.percentile(boots, 2.5, axis=0), "hi": np.percentile(boots, 97.5, axis=0),
        "perm_importance": perm.mean(axis=1),
        "perm_lo": np.percentile(perm, 2.5, axis=1), "perm_hi": np.percentile(perm, 97.5, axis=1),
    })


def fit_pythagorean(standings: pd.DataFrame, n_boot: int = 1000, seed: int = SEED) -> dict:
    from src.features import pythag
    from src.uncertainty import CI

    st = standings[(standings.W > 0) & (standings.L > 0)].reset_index(drop=True)
    x = np.log(st.PF.to_numpy(float) / st.PA.to_numpy(float))
    yv = np.log(st.W.to_numpy(float) / st.L.to_numpy(float))
    exp = float((x * yv).sum() / (x * x).sum())
    rng = np.random.default_rng(seed)
    actual = (st.W / (st.W + st.L)).to_numpy(float)
    pf, pa = st.PF.to_numpy(float), st.PA.to_numpy(float)

    def r2_of(e, idx):
        a, p = actual[idx], pythag(pf[idx], pa[idx], e)
        sst = ((a - a.mean()) ** 2).sum()
        return 1 - ((a - p) ** 2).sum() / sst if sst > 0 else np.nan

    boots, r2_boots = [], []
    for _ in range(n_boot):
        i = rng.integers(0, len(x), len(x))
        e = (x[i] * yv[i]).sum() / (x[i] * x[i]).sum()
        boots.append(e)
        r2_boots.append(r2_of(e, i))
    all_idx = np.arange(len(x))
    r2 = r2_of(exp, all_idx)
    pred, pred_ref = pythag(pf, pa, exp), pythag(pf, pa, 13.91)
    return {"exponent": exp, "exponent_ci": CI(exp, float(np.percentile(boots, 2.5)), float(np.percentile(boots, 97.5))),
            "r2": float(r2), "r2_ci": CI(float(r2), float(np.nanpercentile(r2_boots, 2.5)), float(np.nanpercentile(r2_boots, 97.5))),
            "mae": float(np.abs(actual - pred).mean()), "mae_13_91": float(np.abs(actual - pred_ref).mean()),
            "n": int(len(st))}


def cluster_composition(players: pd.DataFrame, labels: np.ndarray, names: dict[int, str]) -> pd.DataFrame:
    df = players.assign(cluster_name=[names[int(l)] for l in labels])
    out = df.groupby("cluster_name").agg(n=("is_import", "size"), pct_import=("is_import", lambda s: 100 * s.mean()))
    pos = pd.crosstab(df.cluster_name, df.position).reindex(columns=POSITIONS, fill_value=0)
    return out.join(pos).fillna(0).astype({p: int for p in POSITIONS}).reset_index()


def _ci_dict(ci) -> dict:
    return {"est": ci.est, "lo": ci.lo, "hi": ci.hi}


def run_models(processed_dir, reports_dir, models_dir, n_boot: int = 1000, stability_boot: int = 100,
               seed: int = SEED) -> dict:
    import json
    from pathlib import Path

    import joblib

    processed_dir, reports_dir, models_dir = Path(processed_dir), Path(reports_dir), Path(models_dir)
    reports_dir.mkdir(parents=True, exist_ok=True)
    models_dir.mkdir(parents=True, exist_ok=True)
    metrics: dict = {}

    # 7.1 K-Means
    ps = pd.read_csv(processed_dir / "players_season.csv")
    ps = ps[ps.eligible.astype(bool)]
    df, X = archetype_matrix(ps, min_minutes=150)
    res = fit_archetypes(X, seed=seed, min_k=3, scaler=df.attrs["scaler"])
    ari, coassign = cluster_stability(X, res.k, n_boot=stability_boot, seed=seed)
    names = name_clusters(res.centroids_z)
    centroids = pd.DataFrame(res.scaler.inverse_transform(res.centroids_z), columns=ARCHETYPE_FEATURES)
    centroids.insert(0, "cluster_name", [names[i] for i in range(res.k)])
    centroids.to_csv(reports_dir / "cluster_centroids.csv", index=False)
    res.centroids_z.assign(cluster_name=[names[i] for i in range(res.k)]).to_csv(
        reports_dir / "cluster_centroids_z.csv", index=False)
    cluster_composition(df, res.labels, names).to_csv(reports_dir / "cluster_composition.csv", index=False)
    pd.DataFrame({"player_id": df.player_id, "season": df.season, "cluster": res.labels,
                  "cluster_name": [names[int(l)] for l in res.labels], "coassign": coassign,
                  "pc1": res.pca_xy[:, 0], "pc2": res.pca_xy[:, 1]}).to_csv(reports_dir / "clusters.csv", index=False)
    metrics["kmeans"] = {"k": res.k, "n": int(len(df)), "silhouette_by_k": res.silhouette_by_k,
                         "inertia_by_k": res.inertia_by_k, "silhouette": res.silhouette_by_k[res.k],
                         "bootstrap_ari": ari, "stable": bool(ari >= 0.6), "names": names}
    joblib.dump(res.model, models_dir / "kmeans.joblib")
    joblib.dump(res.scaler, models_dir / "scaler.joblib")

    # 7.2 Ялалтын таамаглал
    games = pd.read_csv(processed_dir / "games.csv").rename(columns={"home_team_key": "home_key",
                                                                     "away_team_key": "away_key"})
    tg = pd.read_csv(processed_dir / "team_games.csv")
    gm = build_game_matrix(games, tg, seed=seed)
    gm.to_csv(reports_dir / "game_matrix.csv", index=False)
    models = make_models(seed)
    cv, preds = walk_forward_cv(gm, models, n_folds=5, return_predictions=True)
    cv.to_csv(reports_dir / "cv_metrics.csv", index=False)
    preds.to_csv(reports_dir / "cv_predictions.csv", index=False)
    summary = cv.groupby("model")[["accuracy", "auc", "brier"]].agg(["mean", "std"])
    metrics["win_cv"] = {m: {f"{k}_{s}": float(summary.loc[m, (k, s)]) for k in ("accuracy", "auc", "brier")
                             for s in ("mean", "std")} for m in summary.index}
    metrics["win_bootstrap"] = {m: {k: _ci_dict(v) for k, v in bootstrap_metrics(p.y, p.p, n_boot, seed).items()}
                                for m, p in preds.groupby("model")}
    hold = season_holdout(gm, models)
    hold.to_csv(reports_dir / "season_holdout.csv", index=False)
    metrics["win_holdout"] = hold.to_dict(orient="records")
    metrics["win_matrix"] = {"n_games": int(len(gm)), "features": WIN_FEATURES}
    final_X = gm[WIN_FEATURES].fillna(0).to_numpy()
    for name, m in models.items():
        joblib.dump(m.fit(final_X, gm.y), models_dir / f"{name}.joblib")

    # 7.3 Тайлбар загвар
    expl = fit_explanatory(tg, n_boot=n_boot, seed=seed)
    expl.to_csv(reports_dir / "explanatory.csv", index=False)
    metrics["explanatory"] = expl.to_dict(orient="records")

    # 7.4 Pythagorean
    st = pd.read_csv(processed_dir / "standings_hist.csv")
    py = fit_pythagorean(st, n_boot=n_boot, seed=seed)
    metrics["pythagorean"] = {k: (_ci_dict(v) if hasattr(v, "_fields") else v) for k, v in py.items()}

    (reports_dir / "metrics.json").write_text(json.dumps(metrics, ensure_ascii=False, indent=2, default=float),
                                              encoding="utf-8")
    return metrics


if __name__ == "__main__":
    from pathlib import Path

    root = Path(__file__).resolve().parents[1]
    m = run_models(root / "data" / "processed", root / "reports", root / "dashboard" / "models")
    print("k =", m["kmeans"]["k"], "silhouette =", round(m["kmeans"]["silhouette"], 3), "ARI =", round(m["kmeans"]["bootstrap_ari"], 3))
    for name, v in m["win_cv"].items():
        print(name, {k: round(x, 3) for k, x in v.items()})
