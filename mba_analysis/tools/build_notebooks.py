"""notebooks/01–06-г үүсгэнэ. Notebook бүр зөвхөн src-ийн функц, reports/ ба figures/-ийг ашиглана."""
from pathlib import Path

import nbformat as nbf

ROOT = Path(__file__).resolve().parents[1]
NB = ROOT / "notebooks"
DRAFT = "**[Ноорог — өөрийн үгээр дахин бичих]**"

SETUP = """import sys, json
from pathlib import Path
ROOT = Path.cwd().parent if Path.cwd().name == "notebooks" else Path.cwd()
sys.path.insert(0, str(ROOT))
import pandas as pd
from IPython.display import Image, Markdown, display
pd.set_option("display.max_columns", 50); pd.set_option("display.width", 200)
P, R, F = ROOT / "data" / "processed", ROOT / "reports", ROOT / "figures"
def show(name):
    display(Image(filename=str(F / f"{name}.png"), width=760))"""


def md(text):
    return nbf.v4.new_markdown_cell(text)


def code(text):
    return nbf.v4.new_code_cell(text)


def figs(names, note=""):
    cells = []
    for n in names:
        cells.append(code(f'show("{n}")'))
    if note:
        cells.append(md(f"{DRAFT} {note}"))
    return cells


NOTEBOOKS = {
    "01_collect": [
        md("# 1. Өгөгдөл цуглуулах\n\nЭх сурвалж, татсан арга, хэмжээ (бие даалтын Хэсэг 1). "
           "Татах кодыг дахин ажиллуулах: `python -m src.scrape` (кэштэй бол `--offline`), `python -m src.wiki`."),
        code(SETUP),
        code('display(Markdown((ROOT / "data" / "raw" / "SNAPSHOT.md").read_text(encoding="utf-8")))'),
        md("## Эх сурвалжууд\n\n| # | Эх сурвалж | Юу | Арга |\n|---|---|---|---|\n"
           "| S1 | MBA статистикийн систем (mongolia.basketball) | тоглогчийн улирлын статистик, профайл, тоглолтын box score | `requests` + `BeautifulSoup`, robots.txt-ийг дагаж ≥1 с завсартай |\n"
           "| S2 | Wikipedia — The League (Mongolia), 2023–24 season | 2023-24 байр, гэр хот, аваргууд | wikitext parse |\n"
           "| S3 | Wikipedia/FIBA — шигшээ багийн бүрэлдэхүүн (2026.08) | шигшээ багийн 12 тоглогч | `{{FIBA player}}` parse |"),
        code('raw = ROOT / "data" / "raw"\n'
             'pd.DataFrame([(f.name, len(pd.read_csv(f)), len(pd.read_csv(f).columns)) for f in sorted(raw.glob("*.csv"))],\n'
             '             columns=["файл", "мөр", "багана"])'),
        code('pd.read_csv(raw / "players_season_raw.csv").head()'),
        code('pd.read_csv(raw / "player_games_raw.csv").head()'),
    ],
    "02_clean": [
        md("# 2. Цэвэрлэгээ ба боловсруулалт\n\nАлхам бүрийг `src/clean.py` хийдэг; доорх лог нь `python -m src.clean`-ийн гаралт (бие даалтын Хэсэг 2)."),
        code(SETUP),
        code('pd.read_csv(R / "cleaning_log.csv")'),
        md("## Жишээ: өмнө / дараа"),
        code('raw = pd.read_csv(ROOT / "data" / "raw" / "players_season_raw.csv")\n'
             'print("Багийн түүхий нэрс:", sorted(raw.team_name.unique()))\n'
             'ps = pd.read_csv(P / "players_season.csv")\n'
             'print("Стандарт team_key:", sorted(ps.team_key.unique()))'),
        code('pg_raw = pd.read_csv(ROOT / "data" / "raw" / "player_games_raw.csv")\n'
             'pg = pd.read_csv(P / "player_games.csv")\n'
             'display(pg_raw[["name", "FG", "TP", "FT", "dnp"]].head(3)); display(pg[["player_id", "FGM", "FGA", "TPM", "TPA", "FTM", "FTA"]].head(3))'),
        code('prof = pd.read_csv(ROOT / "data" / "raw" / "players_profile_raw.csv")\n'
             'prof[prof.birth_year.isin([1900, 2025])][["player_slug", "birth_year", "height_cm"]]'),
        md("## Дутуу утга, нэрийн тааруулалт, PPG шалгалт"),
        code('display(pd.read_csv(R / "missing.csv"))\n'
             'm = pd.read_csv(R / "name_matches.csv"); display(m[m.left_id != m.right_id].head(10))\n'
             'v = pd.read_csv(R / "ppg_validation.csv"); v[v.flag]'),
        md("## Шинэ хувьсагчид\n\n`age`, `pos_group`, per-36 (`pts36` …), `ts_pct`, `tpa_rate`, `ftr`, `scorer_tier`, "
           "`is_national`, `region`; багийн тоглолтод Four Factors (`efg`, `tov_pct`, `orb_pct`, `ftr`), `ortg`, `drtg`, `net`; тоглолтод Elo."),
        code('ps[["player_name", "season", "PPG", "pts36", "ts_pct", "tpa_rate", "scorer_tier", "pos_group", "age", "region", "is_national"]].head()'),
        md(f"{DRAFT} MBA-ийн улирлын хүснэгт зөвхөн энгийн улирлыг тооцдог нь C10 шалгалтаар илэрсэн; "
           "1900 гэх мэт placeholder төрсөн оныг C12 алхамд засав; багийн нэрийн 16 хувилбарыг 14 баг болгов."),
    ],
    "03_descriptive": [
        md("# 3. Танилцуулах статистик (Хэсэг 3)"),
        code(SETUP),
        code('num = pd.read_csv(R / "descriptive_numeric.csv")\nnum[num.group == "Бүгд"].round(2)'),
        code('num[num.group != "Бүгд"].round(2)'),
        code('pd.read_csv(R / "descriptive_categorical.csv")'),
        code('pd.read_csv(R / "descriptive_games.csv").round(2)'),
        code('n = num[num.group == "Бүгд"].set_index("variable")\n'
             'print(f"PPG: дундаж {n.loc[\'PPG\',\'mean\']:.1f} > медиан {n.loc[\'PPG\',\'median\']:.1f}, skew {n.loc[\'PPG\',\'skew\']:.2f} → баруун тийш хазгай")\n'
             'print(f"Өндөр: дундаж {n.loc[\'height_cm\',\'mean\']:.1f} см, Q1–Q3 {n.loc[\'height_cm\',\'q1\']:.0f}–{n.loc[\'height_cm\',\'q3\']:.0f} см")'),
        md(f"{DRAFT} Оноо, самбар, дамжуулалтын тархалт баруун тийш хазгай: цөөн од тоглогч дунджийг дээш татдаг тул "
           "медиан илүү төлөөлөлтэй. Import тоглогч тоглогчдын ~25%."),
    ],
    "04_visualization": [
        md("# 4. Өгөгдлийн дүрслэл (Хэсэг 4)\n\nБүх графикийг `python -m src.make_figures` үүсгэж, `src/chart_qa.py`-ээр шалгадаг."),
        code(SETUP),
        code('pd.read_csv(R / "chart_qa.csv")[["name", "status", "title", "n"]]'),
        md("## Үндсэн 6 график"),
        *figs(["F01_ppg_hist", "F02_ts_box_pos", "F03_height_reb", "F04_cum_winpct", "F05_four_factors",
               "F06_import_donut"], "График бүрийн гарчиг гол дүгнэлтийг хэлдэг; тайлбарыг өөрийн үгээр бичнэ."),
        md("## Нэмэлт: heatmap, violin, pair plot, Elo, газрын зураг, сүлжээ, Pythagorean"),
        *figs(["F07_corr_heatmap", "F08_ppg_violin", "F09_pairplot", "F10_elo", "F11_team_map", "F12_transfer_network",
               "F13_pythagorean"]),
        md("## Pareto chart"),
        *figs(["P1_league_pareto", "P2_team_concentration", "P3_importance_pareto"]),
        md("## Тодорхой бус байдлын дүрслэл"),
        *figs(["U01_ts_funnel", "U02_top_ppg_ci", "U03_fan_winpct", "U04_raincloud"]),
    ],
    "05_analysis": [
        md("# 5. Шинжилгээ ба дүгнэлт (Хэсэг 5)"),
        code(SETUP),
        code('hyp = pd.read_csv(R / "hypotheses.csv"); hyp'),
        *figs(["U05_hypotheses", "U09_data_quality"]),
        code('from src.charts.summary import verdict\n'
             'for r in hyp.itertuples():\n'
             '    print(f"{r.hid}: {verdict(pd.Series(r._asdict()))} — тооцоо {r.estimate:.3f} [{r.ci_lo:.3f}, {r.ci_hi:.3f}]")'),
        md("## 1. Үндсэн хандлага"),
        md(f"{DRAFT} Import тоглогчид тоглогчдын 32% боловч онооны 41%-ийг авдаг; топ ~40% тоглогч онооны 80%-ийг авдаг (P1)."),
        md("## 2. Хамаарал"),
        md(f"{DRAFT} Минут ба оноо хамгийн хүчтэй хамааралтай (r ≈ 0.88); өндөр ↔ самбар r ≈ 0.63 (H4); "
           "тоглолтын үр дүнг eFG% хамгийн хүчтэй тайлбарладаг (H3)."),
        md("## 3. Онцгой утга"),
        code('ps = pd.read_csv(P / "players_season.csv"); ps = ps[ps.eligible]\n'
             'g = pd.read_csv(P / "games.csv"); g["margin"] = (g.home_pts - g.away_pts).abs()\n'
             'q1, q3 = g.margin.quantile([.25, .75]); print("Их зөрүүтэй тоглолт (IQR дүрэм):")\n'
             'display(g[g.margin > q3 + 1.5 * (q3 - q1)][["date", "home_team", "away_team", "home_pts", "away_pts", "margin"]])'),
        md(f"{DRAFT} Funnel (U1) дээр хилээс гарсан тоглогчдын ихэнх нь цөөн шидэлттэй — жинхэнэ онцгой ба азын нөлөөг ялгах хэрэгтэй."),
        md("## 4. Шалтгаан, үр дагавар"),
        md(f"{DRAFT} Хамаарал нь шалтгааныг нотлохгүй: Import тоглогч их минут тоглодог (confounder). "
           "Талбайн давуу тал нотлогдоогүй (H2) — ихэнх тоглолт М Банк Аренад болдог."),
        md("## 5. Практик санал"),
        md(f"{DRAFT} (1) Шидэлтийн сонголтыг сайжруулж eFG%-д анхаарах; (2) дотоодын тоглогчийн минутыг нэмэх хөгжлийн хөтөлбөр; "
           "(3) цөөн тоглогчоос хамаарал өндөр багуудад (P2) гүнийг нэмэх; (4) MBA статистикт газар, нэрийн стандарт оруулах."),
    ],
    "06_ml": [
        md("# 6. Машин суралцал (бонус)\n\n`python -m src.models` бүх загварыг сургаж, `reports/metrics.json`-д бичдэг."),
        code(SETUP),
        code('m = json.loads((R / "metrics.json").read_text(encoding="utf-8"))\n'
             'print("K-Means: k =", m["kmeans"]["k"], "silhouette =", round(m["kmeans"]["silhouette"], 3), "bootstrap ARI =", round(m["kmeans"]["bootstrap_ari"], 3))'),
        *figs(["F14a_elbow_silhouette", "F14b_pca_clusters", "F14c_radar"]),
        code('display(pd.read_csv(R / "cluster_composition.csv")); pd.read_csv(R / "cluster_centroids.csv").round(3)'),
        md("## Ялалтын таамаглал (walk-forward CV)"),
        code('pd.DataFrame(m["win_cv"]).T.round(3)'),
        code('pd.DataFrame({k: {kk: f"{vv[\'est\']:.3f} [{vv[\'lo\']:.3f}, {vv[\'hi\']:.3f}]" for kk, vv in v.items()} for k, v in m["win_bootstrap"].items()}).T'),
        code('pd.read_csv(R / "season_holdout.csv").round(3)'),
        *figs(["F14d_confusion", "F14e_roc", "U06a_model_accuracy", "U06b_calibration"],
              "Загвар энгийн Elo baseline-ийг итгэх интервалын хэмжээнд давж чадаагүй — энэ нь өөрөө дүгнэлт: "
              "~200 тоглолтын дата, баг хоорондын тэнцвэр."),
        md("## Тайлбар загвар ба Pythagorean"),
        code('display(pd.read_csv(R / "explanatory.csv").round(3)); m["pythagorean"]'),
        *figs(["P3_importance_pareto", "F13_pythagorean"]),
    ],
}


def main() -> None:
    NB.mkdir(exist_ok=True)
    for name, cells in NOTEBOOKS.items():
        nb = nbf.v4.new_notebook()
        nb.cells = cells
        nb.metadata["kernelspec"] = {"name": "python3", "display_name": "Python 3", "language": "python"}
        nbf.write(nb, NB / f"{name}.ipynb")
        print("ok", name)


if __name__ == "__main__":
    main()
