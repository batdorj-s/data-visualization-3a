"""Dashboard-д хэрэгтэй бүх тооцоог урьдчилан хийж dashboard/data/*.parquet болгоно (spec §9.1)."""
import json
import shutil
from pathlib import Path

import numpy as np
import pandas as pd

from src.uncertainty import CI

ROOT = Path(__file__).resolve().parents[1]
EXPECTED = ["players", "player_ci", "player_games", "team_games", "games", "standings", "pareto_league",
            "pareto_team", "clusters", "team_meta", "elo_coefs", "hypotheses", "quality_missing",
            "quality_matches", "cleaning_log", "model_metrics"]
LEVELS = {"95": 0.05, "80": 0.20, "50": 0.50}


def player_ci_fast(pts: np.ndarray, fga: np.ndarray, fta: np.ndarray, n_boot: int = 2000,
                   seed: int = 42) -> dict[str, CI]:
    """Нэг тоглогчийн тоглолт бүр нэг мөр тул мөрөөр bootstrap = тоглолтоор cluster bootstrap."""
    n = len(pts)
    idx = np.random.default_rng(seed).integers(0, n, (n_boot, n))
    ppg = pts[idx].mean(axis=1)
    denom = 2 * (fga[idx].sum(axis=1) + 0.44 * fta[idx].sum(axis=1))
    with np.errstate(divide="ignore", invalid="ignore"):
        ts = np.where(denom > 0, pts[idx].sum(axis=1) / denom, np.nan)
    tsa = 2 * (fga.sum() + 0.44 * fta.sum())
    ts_est = pts.sum() / tsa if tsa > 0 else np.nan
    out = {"ppg": CI(float(pts.mean()), *map(float, np.percentile(ppg, [2.5, 97.5])))}
    if np.isfinite(ts_est):
        lo, hi = np.nanpercentile(ts, [2.5, 97.5])
        out["ts_pct"] = CI(float(ts_est), float(min(lo, ts_est)), float(max(hi, ts_est)))
    return out


def win_probability(elo_a: float, elo_b: float, coefs: np.ndarray) -> tuple[float, float, float]:
    """P(A ялна) = sigmoid(β·(Elo_A − Elo_B)); β-ийн bootstrap дээжээс 95% интервал."""
    diff = elo_a - elo_b
    point = 1 / (1 + np.exp(-np.median(coefs) * diff))
    samples = 1 / (1 + np.exp(-coefs * diff))
    lo, hi = np.percentile(samples, [2.5, 97.5])
    return float(point), float(lo), float(hi)


def elo_coefficients(game_matrix: pd.DataFrame, n_boot: int = 500, seed: int = 42) -> np.ndarray:
    from sklearn.linear_model import LogisticRegression

    x = game_matrix[["elo_diff"]].to_numpy(float)
    y = game_matrix.y.to_numpy()
    rng = np.random.default_rng(seed)
    coefs = []
    for _ in range(n_boot):
        i = rng.integers(0, len(y), len(y))
        if len(np.unique(y[i])) == 2:
            coefs.append(LogisticRegression(fit_intercept=False, C=1e6).fit(x[i], y[i]).coef_[0, 0])
    return np.array(coefs)


def _team_games(tg: pd.DataFrame) -> pd.DataFrame:
    from src.charts.timeline import cumulative_winpct
    from src.uncertainty import wilson_ci

    parts = []
    for season in sorted(tg.season.unique()):
        c = cumulative_winpct(tg, season)
        for lvl, alpha in LEVELS.items():
            cis = [wilson_ci(int(w), int(n), alpha=alpha) for w, n in zip(c.wins, c.games)]
            c[f"lo{lvl}"], c[f"hi{lvl}"] = [x.lo for x in cis], [x.hi for x in cis]
        parts.append(c)
    return pd.concat(parts, ignore_index=True)


def build(processed_dir: Path, reports_dir: Path, out_dir: Path, n_boot: int = 2000) -> dict[str, int]:
    from src.charts.comparison import pareto_ci, pareto_table

    p, r, out = Path(processed_dir), Path(reports_dir), Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    ps = pd.read_csv(p / "players_season.csv")
    clusters = pd.read_csv(r / "clusters.csv")
    ps = ps.merge(clusters[["player_id", "season", "team_key", "cluster_name", "coassign", "pc1", "pc2"]],
                  on=["player_id", "season", "team_key"], how="left", validate="one_to_one")
    games = pd.read_csv(p / "games.csv")
    pg = pd.read_csv(p / "player_games.csv")
    pg["is_import"] = pg.is_import.astype(bool)
    pg_reg = pg[pg.phase == "regular"]

    ci_rows = []
    for (pid, season), d in pg_reg.groupby(["player_id", "season"]):
        for metric, ci in player_ci_fast(d.PTS.to_numpy(float), d.FGA.to_numpy(float), d.FTA.to_numpy(float),
                                         n_boot=n_boot).items():
            ci_rows.append({"player_id": pid, "season": season, "metric": metric, "gp": len(d),
                            "est": ci.est, "lo": ci.lo, "hi": ci.hi})

    pareto_rows, team_rows = [], []
    for season, d in pg_reg.groupby("season"):
        t = pareto_table(d.groupby("player_id").PTS.sum())
        lo, hi = pareto_ci(d, n_boot=max(100, n_boot // 4))
        imp = d.drop_duplicates("player_id").set_index("player_id").is_import
        pareto_rows.append(t.assign(season=season, lo=lo, hi=hi, is_import=imp.reindex(t.label).to_numpy(),
                                    rank=np.arange(1, len(t) + 1)))
        for team, dt in d.groupby("team_key"):
            tt = pareto_table(dt.groupby("player_id").PTS.sum())
            team_rows.append(tt.assign(season=season, team_key=team, rank=np.arange(1, len(tt) + 1)))

    names = ps.drop_duplicates("player_id", keep="last").set_index("player_id").player_name
    metrics = json.loads((r / "metrics.json").read_text(encoding="utf-8"))
    gm = pd.read_csv(r / "game_matrix.csv")
    tables = {
        "players": ps,
        "player_ci": pd.DataFrame(ci_rows),
        "player_games": pg.merge(games[["game_id", "home_team", "away_team"]], on="game_id", how="left"),
        "team_games": _team_games(pd.read_csv(p / "team_games.csv")),
        "games": games,
        "standings": pd.read_csv(p / "standings_hist.csv"),
        "pareto_league": pd.concat(pareto_rows, ignore_index=True).assign(player_name=lambda d: d.label.map(names)),
        "pareto_team": pd.concat(team_rows, ignore_index=True).assign(player_name=lambda d: d.label.map(names)),
        "clusters": clusters.assign(player_name=clusters.player_id.map(names)),
        "team_meta": pd.read_csv(p / "team_meta.csv"),
        "elo_coefs": pd.DataFrame({"coef": elo_coefficients(gm, n_boot=max(100, n_boot // 4))}),
        "hypotheses": pd.read_csv(r / "hypotheses.csv"),
        "quality_missing": pd.read_csv(r / "missing.csv"),
        "quality_matches": pd.read_csv(r / "name_matches.csv"),
        "cleaning_log": pd.read_csv(r / "cleaning_log.csv"),
        "model_metrics": pd.DataFrame(metrics["win_cv"]).T.reset_index(names="model"),
    }
    counts = {}
    for name, df in tables.items():
        df.to_parquet(out / f"{name}.parquet", index=False)
        counts[name] = len(df)
    geo = ROOT / "data" / "raw" / "geo" / "mng_adm1.geojson"
    if geo.exists():
        shutil.copy(geo, out / "mng_adm1.geojson")
    (out / "snapshot.txt").write_text(
        next((l.split(": ", 1)[1] for l in (ROOT / "data" / "raw" / "SNAPSHOT.md").read_text(encoding="utf-8").splitlines()
              if l.startswith("- Татсан огноо")), "2026-11-12")[:10], encoding="utf-8")
    return counts


if __name__ == "__main__":
    c = build(ROOT / "data" / "processed", ROOT / "reports", ROOT / "dashboard" / "data")
    print(c)
