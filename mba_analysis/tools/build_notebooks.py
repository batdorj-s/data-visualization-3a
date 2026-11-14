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
           "Дахин татах: `python -m src.scrape` (кэштэй бол `--offline`), `python -m src.wiki`."),
        code(SETUP),
        code('display(Markdown((ROOT / "data" / "raw" / "SNAPSHOT.md").read_text(encoding="utf-8")))'),
        md("## Эх сурвалжууд\n\n| # | Эх сурвалж | Юу | Хэрхэн авсан |\n|---|---|---|---|\n"
           "| S1 | MBA лигийн албан ёсны статистик (mongolia.basketball) | тоглогчийн улирлын статистик, профайл, тоглолтын хайрцаг оноо | Python (`requests` + `BeautifulSoup`), сайтын дүрмийг (robots.txt) дагаж хүсэлт хооронд ≥1 с |\n"
           "| S1b | Мөн адил тоглолтын хуудас | шидэлтийн байршил, тоглолтын явцын бичлэг (play-by-play) | хуудсанд нуугдсан JSON-оос; шинэ хүсэлтгүй |\n"
           "| S2 | Wikipedia — The League (Mongolia), 2023–24 улирал | 2023–24 байр, багийн хот, аваргууд | хуудасны текстээс |\n"
           "| S3 | Wikipedia/FIBA — шигшээ багийн бүрэлдэхүүн (2026.08) | шигшээ багийн 12 тоглогч | хуудасны текстээс |\n"
           "| S4 | geoBoundaries | Монголын аймгийн хил | GeoJSON файл |"),
        code('raw = ROOT / "data" / "raw"\n'
             'files = sorted(list(raw.glob("*.csv")) + list(raw.glob("*.csv.gz")))\n'
             'pd.DataFrame([(f.name, len(df := pd.read_csv(f)), len(df.columns)) for f in files], columns=["файл", "мөр", "багана"])'),
        code('pd.read_csv(raw / "players_season_raw.csv").head()'),
        code('pd.read_csv(raw / "player_games_raw.csv").head()'),
        md("## Шидэлт ба тоглолтын явц\n\nТоглолтын хуудас бүр шидэлт бүрийн талбай дээрх байршил (x, y пиксел), "
           "оносон эсэх, 2/3 оноо, мөн тоглолтын бүх үйл явдлыг (солилт, дамжуулалт, алдаа ...) цаг, онооны хамт агуулдаг."),
        code('display(pd.read_csv(raw / "shots_raw.csv").head(3)); pd.read_csv(raw / "pbp_raw.csv.gz").head(5)'),
    ],
    "02_clean": [
        md("# 2. Цэвэрлэгээ ба боловсруулалт\n\nАлхам бүрийг `src/clean.py` (шидэлт, тоглолтын явцыг `src/pbp.py`) хийдэг; "
           "доорх лог нь `python -m src.clean`-ийн гаралт (бие даалтын Хэсэг 2)."),
        code(SETUP),
        code('log = pd.read_csv(R / "cleaning_log.csv"); log'),
        md("## Жишээ: өмнө / дараа"),
        code('raw = pd.read_csv(ROOT / "data" / "raw" / "players_season_raw.csv")\n'
             'print("Багийн түүхий нэрс:", sorted(raw.team_name.unique()))\n'
             'ps = pd.read_csv(P / "players_season.csv")\n'
             'print("Стандарт баг:", sorted(ps.team_key.unique()))'),
        code('pg_raw = pd.read_csv(ROOT / "data" / "raw" / "player_games_raw.csv")\n'
             'pg = pd.read_csv(P / "player_games.csv")\n'
             'display(pg_raw[["name", "FG", "TP", "FT", "dnp"]].head(3)); display(pg[["player_id", "FGM", "FGA", "TPM", "TPA", "FTM", "FTA"]].head(3))'),
        code('prof = pd.read_csv(ROOT / "data" / "raw" / "players_profile_raw.csv")\n'
             'prof[prof.birth_year.isin([1900, 2025])][["player_slug", "birth_year", "height_cm"]]'),
        md("## Дутуу утга, нэрийн тааруулалт, онооны тулгалт"),
        code('display(pd.read_csv(R / "missing.csv"))\n'
             'm = pd.read_csv(R / "name_matches.csv"); display(m[m.left_id != m.right_id].head(10))\n'
             'v = pd.read_csv(R / "ppg_validation.csv"); v[v.flag]'),
        md("## Шидэлт ба тоглолтын явц (C14–C16)\n\n"
           "- **C14:** шидэлтийг (тоглолт, тал, өмсгөлийн дугаар)-аар тоглогчтой холбож, пикселийг метр болгов. Хувиргалтыг "
           "MBA сайтын өөрийнх нь шидэлтийн зургийн кодоос авсан: талбай 28 × 15 м, 1 м = 22.75 пиксел. Баг бүрийн шидэлтийг "
           "нэг сагс руу эргүүлж нэгтгээд 5 бүсэд хуваав.\n"
           "- **C15:** тоглолтын явцын цагийг секунд, онооны зөрүү болгов.\n"
           "- **C16:** оновчтой дамжуулалтыг ойролцоох оносон шидэлттэй холбов."),
        code('shots = pd.read_csv(P / "shots.csv")\n'
             'print(f"Шидэлт: {len(shots):,}; хайрцаг онооны нийт шидэлт: {int(pg.FGA.sum()):,} (тэнцүү байх ёстой)")\n'
             'print(f"Байршил нь 2/3 онооны шошготой зөрсөн: {(~shots.location_ok).mean():.1%} (байршлын шинжилгээнээс хассан)")\n'
             'shots.head()'),
        code('e = pd.read_csv(P / "pbp.csv.gz"); g = pd.read_csv(P / "games.csv").set_index("game_id")\n'
             'last = e.sort_values(["game_id", "seq"]).groupby("game_id")[["home", "away"]].last()\n'
             'ok = (last.home == g.home_pts.reindex(last.index)) & (last.away == g.away_pts.reindex(last.index))\n'
             'print(f"Тоглолтын явцын эцсийн оноо гарчигтай таарсан: {ok.sum()}/{len(ok)}; зөрсөн:", sorted(ok.index[~ok]))'),
        md("## Шинэ үзүүлэлтүүд\n\n`age`, `pos_group`, 36 минутад ногдох (`pts36` …), шидэлтийн оновч (`ts_pct`), 3 оноогоор "
           "шидсэн хувь (`tpa_rate`), торгууль авалт (`ftr`), `scorer_tier`, `is_national`, `region`; багийн тоглолтод ялалтын "
           "4 хүчин зүйл (`efg`, `tov_pct`, `orb_pct`, `ftr`), 100 довтолгоонд ногдох оноо (`ortg`, `drtg`, `net`); тоглолтод "
           "багийн хүчний оноо (Elo); шидэлтэд зай (м) ба бүс."),
        code('ps[["player_name", "season", "PPG", "pts36", "ts_pct", "tpa_rate", "scorer_tier", "pos_group", "age", "region", "is_national"]].head()'),
        code('notes = log.drop_duplicates("step").set_index("step").note.fillna("")\n'
             'for step in ["C1", "C10", "C12", "C13"]:\n'
             '    print(step, "—", notes.get(step, ""))'),
        md(f"{DRAFT} Дээрх 4 алхмаас хамгийн чухал олдворыг (жишээ нь C10: сайтын нэгтгэл зөвхөн үндсэн шатыг тооцдог) "
           "өөрийн үгээр тайлбарлана."),
    ],
    "03_descriptive": [
        md("# 3. Танилцуулах статистик (Хэсэг 3)"),
        code(SETUP),
        code('num = pd.read_csv(R / "descriptive_numeric.csv")\nnum[num.group == "Бүгд"].round(2)'),
        code('num[num.group != "Бүгд"].round(2)'),
        code('pd.read_csv(R / "descriptive_categorical.csv")'),
        code('pd.read_csv(R / "descriptive_games.csv").round(2)'),
        code('n = num[num.group == "Бүгд"].set_index("variable")\n'
             'print(f"Оноо/тоглолт: дундаж {n.loc[\'PPG\',\'mean\']:.1f} > голч {n.loc[\'PPG\',\'median\']:.1f}, хазгай {n.loc[\'PPG\',\'skew\']:.2f} → цөөн өндөр оноотой тоглогч дунджийг татдаг")\n'
             'print(f"Өндөр: дундаж {n.loc[\'height_cm\',\'mean\']:.1f} см, Q1–Q3 {n.loc[\'height_cm\',\'q1\']:.0f}–{n.loc[\'height_cm\',\'q3\']:.0f} см")\n'
             'ps = pd.read_csv(P / "players_season.csv")\n'
             'print(f"Гадаад тоглогч: тоглогчдын {ps.drop_duplicates(\'player_id\').is_import.mean():.0%}")'),
        md("## Шидэлтийн бүсээр"),
        code('s = pd.read_csv(P / "shots.csv"); s = s[s.location_ok].assign(pts=lambda d: d.made * (2 + d.three))\n'
             's.groupby("zone").agg(шидэлт=("pts", "size"), оносон_хувь=("made", "mean"), шидэлт_бүрт_оноо=("pts", "mean")).round(3)'),
        md(f"{DRAFT} Оноо, самбар, дамжуулалтын тархалт баруун тийш хазгай тул голч утга илүү төлөөлөлтэй гэдгийг, мөн аль "
           "бүсээс шидэх нь хамгийн үр ашигтайг өөрийн үгээр тайлбарлана."),
    ],
    "04_visualization": [
        md("# 4. Өгөгдлийн дүрслэл (Хэсэг 4)\n\nБүх графикийг `python -m src.make_figures` үүсгэж, `src/chart_qa.py`-ээр "
           "шалгадаг. График бүрийн гарчиг нь гол дүгнэлт, доод мөр нь ашигласан дата ба тоог хэлнэ."),
        code(SETUP),
        code('pd.read_csv(R / "chart_qa.csv")[["name", "status", "title", "n"]]'),
        md("## Үндсэн 6 график"),
        *figs(["F01_ppg_hist", "F02_ts_box_pos", "F03_height_reb", "F04_cum_winpct", "F05_four_factors",
               "F06_import_donut"], "График бүрээс юу харагдаж байгааг өөрийн үгээр 1–2 өгүүлбэрээр тайлбарлана."),
        md("## Нэмэлт: дулааны зураг, violin, хос харьцуулалт, хүчний оноо, газрын зураг, шилжилтийн сүлжээ"),
        *figs(["F07_corr_heatmap", "F08_ppg_violin", "F09_pairplot", "F10_elo", "F11_team_map", "F12_transfer_network",
               "F13_pythagorean"]),
        md("## Шидэлтийн байршил, дамжуулалт, тоглолтын явц"),
        *figs(["F15_shot_map", "F16_shot_profile", "F17_assist_network", "F18_game_flow"]),
        md("## Парето (Pareto) график"),
        *figs(["P1_league_pareto", "P2_team_concentration", "P3_importance_pareto"]),
        md("## Тодорхой бус байдлын дүрслэл"),
        *figs(["U01_ts_funnel", "U02_top_ppg_ci", "U03_fan_winpct", "U04_raincloud"]),
    ],
    "05_analysis": [
        md("# 5. Шинжилгээ ба дүгнэлт (Хэсэг 5)"),
        code(SETUP),
        code('from src.charts.summary import VERDICT_PLAIN, verdict\n'
             'hyp = pd.read_csv(R / "hypotheses.csv")\n'
             'hyp.assign(дүгнэлт=[VERDICT_PLAIN[verdict(r)] for _, r in hyp.iterrows()])[["hid", "statement", "estimate", "ci_lo", "ci_hi", "дүгнэлт"]].round(3)'),
        *figs(["U05_hypotheses", "U09_data_quality"]),
        md("## 1. Үндсэн хандлага"),
        code('pg = pd.read_csv(P / "player_games.csv"); ps = pd.read_csv(P / "players_season.csv")\n'
             'share = pg.loc[pg.is_import, "PTS"].sum() / pg.PTS.sum()\n'
             'print(f"Гадаад тоглогч: тоглогчдын {ps.drop_duplicates(\'player_id\').is_import.mean():.0%}, онооны {share:.0%}")\n'
             'from src.charts.comparison import pareto_table\n'
             'reg = pg[(pg.phase == "regular") & (pg.season == "2025-2026")]\n'
             't = pareto_table(reg.groupby("player_id").PTS.sum()); k = int((t.cum_share < 0.8).sum()) + 1\n'
             'print(f"2025–26: эхний {k} тоглогч ({k / len(t):.0%}) онооны 80%-ийг авдаг")'),
        md(f"{DRAFT} Дээрх тоогоор лигийн оноо цөөн тоглогчид, ялангуяа гадаад тоглогчид төвлөрдөг эсэхийг өөрийн үгээр бичнэ."),
        md("## 2. Хамаарал"),
        code('h = hyp.set_index("hid")\n'
             'print(f"Өндөр ба самбарын хамаарлын хүч: {h.loc[\'H4\', \'estimate\']:.2f}")\n'
             'print(f"Оновч бусад хүчин зүйлээс хэр илүү нөлөөтэй (H3): {h.loc[\'H3\', \'estimate\']:.2f}")'),
        md(f"{DRAFT} Хүчтэй хамааралтай хосууд, ялалтад хамгийн их нөлөөлдөг хүчин зүйлийг тайлбарлана."),
        md("## 3. Онцгой утга"),
        code('g = pd.read_csv(P / "games.csv"); g["margin"] = (g.home_pts - g.away_pts).abs()\n'
             'q1, q3 = g.margin.quantile([.25, .75]); print("Их зөрүүтэй тоглолт (хайрцган графикийн дүрмээр):")\n'
             'display(g[g.margin > q3 + 1.5 * (q3 - q1)][["date", "home_team", "away_team", "home_pts", "away_pts", "margin"]])'),
        md(f"{DRAFT} Юүлүүр график (U01) дээр гадуурх тоглогчдын ихэнх нь цөөн шидэлттэй — жинхэнэ онцгой ба азыг ялгах."),
        md("## 4. Шалтгаан, үр дагавар"),
        md(f"{DRAFT} Хамт өөрчлөгдөх нь шалтгаан гэсэн үг биш (гадаад тоглогч илүү олон минут тоглодог). Гэрийн талбайн "
           "давуу тал батлагдаагүй (H2) — ихэнх тоглолт нэг заалд болдог."),
        md("## 5. Практик санал"),
        md(f"{DRAFT} Жишээ: (1) дунд зайн шидэлтийг багасгаж сагсны доор ба булангийн 3 оноо руу шилжүүлэх (F15); "
           "(2) дотоод тоглогчийн минутыг нэмэх; (3) цөөн тоглогчоос хамаарал өндөр багуудад (P2) гүнийг нэмэх."),
    ],
    "06_ml": [
        md("# 6. Машин сургалт (бонус)\n\n`python -m src.models` бүх загварыг сургаж, `reports/metrics.json`-д бичдэг."),
        code(SETUP),
        code('m = json.loads((R / "metrics.json").read_text(encoding="utf-8"))\n'
             'print("Тоглогчийн хэв маяг (K-Means): бүлэг", m["kmeans"]["k"], "· ялгарал", round(m["kmeans"]["silhouette"], 3), "· дахин тооцоход давхцал", round(m["kmeans"]["bootstrap_ari"], 3))'),
        *figs(["F14a_elbow_silhouette", "F14b_pca_clusters", "F14c_radar"]),
        code('display(pd.read_csv(R / "cluster_composition.csv")); pd.read_csv(R / "cluster_centroids.csv").round(3)'),
        md("## Тоглолтын өмнө ялагчийг таамаглах\n\nЗагварыг он цагийн дарааллаар өмнөх тоглолтоор сургаж, дараагийнхыг "
           "таамаглуулсан (walk-forward)."),
        code('pd.DataFrame(m["win_cv"]).T.round(3)'),
        code('pd.DataFrame({k: {kk: f"{vv[\'est\']:.3f} [{vv[\'lo\']:.3f}, {vv[\'hi\']:.3f}]" for kk, vv in v.items()} for k, v in m["win_bootstrap"].items()}).T'),
        code('pd.read_csv(R / "season_holdout.csv").round(3)'),
        *figs(["F14d_confusion", "F14e_roc", "U06a_model_accuracy", "U06b_calibration"],
              "Загвар «хүчний оноо өндөр нь ялна» гэсэн энгийн дүрмийг баттай давж чадаагүйг, яагаад гэдгийг (дата цөөн, "
              "багууд тэнцүү) өөрийн үгээр тайлбарлана."),
        md("## Тоглолтын дундах ялах магадлал\n\nТоглолт бүрийг минут тутам зогсоож (онооны зөрүү, үлдсэн хугацаа, "
           "тоглолтын өмнөх хүч) гэрийн баг ялах магадлалыг тооцсон. Нэг тоглолтын мөчүүд сургалт, тест хоёрт зэрэг орохгүй."),
        code('ip = m["inplay"]\n'
             'print(f"{ip[\'n_states\']:,} мөч, {ip[\'n_games\']} тоглолт · зөв таамагласан {ip[\'acc\']:.1%} (энгийн дүрэм {ip[\'acc_leader\']:.1%}) · Brier {ip[\'brier\']:.3f}")\n'
             'pd.read_csv(R / "inplay_minute.csv").iloc[::5].round(3)'),
        *figs(["U10_inplay_accuracy", "F18_game_flow"]),
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
