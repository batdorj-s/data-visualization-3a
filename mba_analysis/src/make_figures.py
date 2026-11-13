import json
import sys
import traceback
from pathlib import Path
from typing import Any, Callable

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

from src.chart_qa import check  # noqa: E402
from src.charts import comparison as C  # noqa: E402
from src.charts import distribution as D  # noqa: E402
from src.charts import geo_network as G  # noqa: E402
from src.charts import ml as M  # noqa: E402
from src.charts import relation as R  # noqa: E402
from src.charts import summary as S  # noqa: E402
from src.charts import timeline as T  # noqa: E402
from src.style import IMPORT_COLORS, IMPORT_LABELS, save_figure, source_mba  # noqa: E402
from src.uncertainty import cluster_bootstrap  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
MAIN_SEASON = "2025-2026"


def player_ppg_ci(pg: pd.DataFrame, ps: pd.DataFrame, season: str, top: int = 15, n_boot: int = 2000) -> pd.DataFrame:
    cand = ps[(ps.season == season) & ps.eligible.astype(bool)].nlargest(top, "PPG")
    sub = pg[(pg.season == season) & (pg.phase == "regular")]
    rows = []
    for r in cand.itertuples():
        d = sub[sub.player_id == r.player_id]
        ci = cluster_bootstrap(d, "game_id", lambda x: x.PTS.mean(), n_boot=n_boot)
        rows.append({"player": r.player_name.title(), "est": ci.est, "lo": ci.lo, "hi": ci.hi, "is_import": r.is_import})
    return pd.DataFrame(rows)


def load_inputs(processed_dir: Path, reports_dir: Path, n_boot: int = 2000) -> dict[str, Any]:
    p, r = Path(processed_dir), Path(reports_dir)
    ps_all = pd.read_csv(p / "players_season.csv")
    ps = ps_all[ps_all.eligible.astype(bool)].reset_index(drop=True)
    pg = pd.read_csv(p / "player_games.csv")
    pg["is_import"] = pg.is_import.astype(bool)
    tg = pd.read_csv(p / "team_games.csv")
    clusters = pd.read_csv(r / "clusters.csv")
    labels = ps.merge(clusters[["player_id", "season", "team_key", "cluster_name"]],
                      on=["player_id", "season", "team_key"], how="left", validate="one_to_one").cluster_name
    labels.index = ps.index
    rng = np.random.default_rng(42)
    imp, dom = ps[ps.is_import.astype(bool)].PPG.to_numpy(), ps[~ps.is_import.astype(bool)].PPG.to_numpy()
    boot_diff = np.array([np.median(rng.choice(imp, imp.size)) - np.median(rng.choice(dom, dom.size))
                          for _ in range(n_boot)])
    final = T.cumulative_winpct(tg, MAIN_SEASON).groupby("team_key").winpct.last().sort_values(ascending=False)
    return {
        "ps": ps, "ps_all": ps_all, "pg": pg, "tg": tg, "games": pd.read_csv(p / "games.csv"),
        "standings": pd.read_csv(p / "standings_hist.csv"), "meta": pd.read_csv(p / "team_meta.csv"),
        "hyp": pd.read_csv(r / "hypotheses.csv"), "missing": pd.read_csv(r / "missing.csv"),
        "matches": pd.read_csv(r / "name_matches.csv"), "ppg_val": pd.read_csv(r / "ppg_validation.csv"),
        "metrics": json.loads((r / "metrics.json").read_text(encoding="utf-8")), "clusters": clusters,
        "centroids_z": pd.read_csv(r / "cluster_centroids_z.csv"), "preds": pd.read_csv(r / "cv_predictions.csv"),
        "expl": pd.read_csv(r / "explanatory.csv"), "labels": labels, "boot_diff": boot_diff,
        "highlight": [final.index[0], final.index[1], final.index[-1]],
        "geo": ROOT / "data" / "raw" / "geo" / "mng_adm1.geojson", "n_boot": n_boot,
    }


def _league_pareto(i: dict):
    pg = i["pg"][(i["pg"].season == MAIN_SEASON) & (i["pg"].phase == "regular")]
    vals = pg.groupby("player_id").PTS.sum()
    imp = pg.drop_duplicates("player_id").set_index("player_id").is_import
    t = C.pareto_table(vals)
    k = int(np.argmax(t.cum_share.to_numpy() >= 0.8)) + 1
    return C.fig_pareto(
        vals, imp.reindex(vals.index).map(IMPORT_COLORS),
        title=f"Тоглогчдын {k / len(vals):.0%} буюу {k} тоглогч лигийн нийт онооны 80%-ийг авдаг",
        subtitle="Багана бүр 1 тоглогчийн улирлын нийт оноо, ихээс нь эрэмбэлсэн. Хар шугам = эхний N тоглогчийн "
                 "нийлбэр хувь, саарал сүүдэр = түүний 95% магадлалтай хүрээ",
        xlabel="Тоглогч (оноогоор эрэмбэлсэн)", ylabel="Улирлын нийт оноо", n=len(vals), unit="тоглогч",
        source=f"{source_mba()} · 2025–26 улирлын үндсэн шат",
        cum_ci=C.pareto_ci(pg, n_boot=i["n_boot"]),
        uncertainty_note=f"Хүрээг тоглолтуудыг {i['n_boot']} удаа дахин сонгож тооцов",
        legend={IMPORT_LABELS[True]: IMPORT_COLORS[True], IMPORT_LABELS[False]: IMPORT_COLORS[False]})


def _metric_dist(i):
    return M.fig_metric_distributions(i["preds"], n_boot=i["n_boot"])


def _logreg(i, fn):
    lr = i["preds"][i["preds"].model == "logreg"]
    return fn(lr.y.to_numpy(), lr.p.to_numpy())


FIGURE_SPECS: list[tuple[str, Callable[[dict], Any]]] = [
    ("F01_ppg_hist", lambda i: D.fig_ppg_hist(i["ps"])),
    ("F02_ts_box_pos", lambda i: D.fig_ts_box_by_pos(i["ps"])),
    ("F03_height_reb", lambda i: R.fig_height_reb(i["ps"])),
    ("F04_cum_winpct", lambda i: T.fig_cum_winpct(i["tg"], i["highlight"], bands=False)),
    ("F05_four_factors", lambda i: C.fig_four_factors(i["tg"])),
    ("F06_import_donut", lambda i: C.fig_import_share_donut(i["pg"], n_boot=i["n_boot"])),
    ("F07_corr_heatmap", lambda i: D.fig_corr_heatmap(i["ps"])),
    ("F08_ppg_violin", lambda i: D.fig_ppg_violin(i["ps"])),
    ("F09_pairplot", lambda i: D.fig_pairplot(i["ps"], i["labels"])),
    ("F10_elo", lambda i: T.fig_elo(i["games"], i["highlight"][:2])),
    ("F11_team_map", lambda i: G.fig_team_map(i["meta"], i["standings"], i["geo"])),
    ("F12_transfer_network", lambda i: G.fig_transfer_network(G.transfer_edges(i["ps_all"]),
                                                              dict(zip(i["ps_all"].team_key, i["ps_all"].team)))),
    ("F13_pythagorean", lambda i: R.fig_pythagorean(i["standings"])),
    ("F14a_elbow_silhouette", lambda i: M.fig_elbow_silhouette(i["metrics"]["kmeans"]["inertia_by_k"],
                                                              i["metrics"]["kmeans"]["silhouette_by_k"],
                                                              i["metrics"]["kmeans"]["k"])),
    ("F14b_pca_clusters", lambda i: M.fig_pca_clusters(i["clusters"])),
    ("F14c_radar", lambda i: M.fig_radar_centroids(i["centroids_z"])),
    ("F14d_confusion", lambda i: _logreg(i, M.fig_confusion)),
    ("F14e_roc", lambda i: M.fig_roc(i["preds"])),
    ("P1_league_pareto", _league_pareto),
    ("P2_team_concentration", lambda i: C.fig_team_concentration(i["pg"][i["pg"].phase == "regular"], n_boot=i["n_boot"])),
    ("P3_importance_pareto", lambda i: M.fig_importance_pareto(i["expl"])),
    ("U01_ts_funnel", lambda i: R.fig_ts_funnel(i["ps"])),
    ("U02_top_ppg_ci", lambda i: C.fig_top_dot_ci(player_ppg_ci(i["pg"], i["ps"], MAIN_SEASON, n_boot=i["n_boot"]),
                                                  "Тоглолтын дундаж оноо (2025–26)", highlight_col="is_import")),
    ("U03_fan_winpct", lambda i: T.fig_cum_winpct(i["tg"], i["highlight"], bands=True)),
    ("U04_raincloud", lambda i: D.fig_raincloud(i["ps"], i["boot_diff"])),
    ("U05_hypotheses", lambda i: S.fig_hypothesis_summary(i["hyp"])),
    ("U06a_model_accuracy", _metric_dist),
    ("U06b_calibration", lambda i: _logreg(i, M.fig_calibration)),
    ("U09_data_quality", lambda i: S.fig_data_quality(i["missing"], i["matches"], i["ppg_val"])),
]


def render_all(processed_dir: Path, reports_dir: Path, out_dir: Path, n_boot: int = 2000) -> pd.DataFrame:
    inputs = load_inputs(processed_dir, reports_dir, n_boot=n_boot)
    rows = []
    for name, build in FIGURE_SPECS:
        try:
            fig = build(inputs)
            meta = check(fig)
            save_figure(fig, out_dir, name)
            rows.append({"name": name, "status": "ok", "title": meta["title"], "n": meta["n"], "error": ""})
        except Exception as exc:  # noqa: BLE001 — нэг график унасан ч бусдыг үргэлжлүүлнэ
            rows.append({"name": name, "status": "error", "title": "", "n": None,
                         "error": f"{type(exc).__name__}: {exc}"})
            traceback.print_exc()
        finally:
            plt.close("all")
    return pd.DataFrame(rows)


if __name__ == "__main__":
    log = render_all(ROOT / "data" / "processed", ROOT / "reports", ROOT / "figures")
    log.to_csv(ROOT / "reports" / "chart_qa.csv", index=False)
    print(log[["name", "status", "title"]].to_string(index=False))
    sys.exit(0 if (log.status == "ok").all() else 1)
