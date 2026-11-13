"""Тайлан, слайдын агуулгыг (тоо, хүснэгт, зураг, ноорог) датаас үүсгэж report/report_data.json болгоно.

Ноорог блок бүр DRAFT_LABEL-тай: эцсийн тайлбарыг оюутан өөрийн үгээр бичнэ (даалгаврын шаардлага).
"""
import json
import re
from pathlib import Path

import pandas as pd
from PIL import Image

from src.charts.summary import verdict

DRAFT_LABEL = "[Ноорог — өөрийн үгээр дахин бичих]"
VAR_NAMES = {"PPG": "Оноо/тоглолт", "RPG": "Самбар/тоглолт", "APG": "Дамжуулалт/тоглолт", "MIN": "Минут/тоглолт",
             "ts_pct": "TS%", "height_cm": "Өндөр (см)", "age": "Нас"}


def _fig(root: Path, name: str, caption: str, width_cm: float = 12.0) -> dict:
    rel = f"figures/{name}.png" if not name.startswith("report/") else f"{name}.png"
    w, h = Image.open(root / rel).size
    return {"type": "figure", "path": rel, "caption": caption, "width_px": w, "height_px": h, "width_cm": width_cm}


def _table(caption: str, df: pd.DataFrame) -> dict:
    return {"type": "table", "caption": caption, "columns": [str(c) for c in df.columns],
            "rows": [[("" if pd.isna(v) else str(v)) for v in row] for row in df.itertuples(index=False)]}


def _para(text: str) -> dict:
    return {"type": "para", "text": text}


def _draft(text: str) -> dict:
    return {"type": "draft", "text": text}


def _bullets(items: list[str]) -> dict:
    return {"type": "bullets", "items": items}


def _h2(text: str) -> dict:
    return {"type": "h2", "text": text}


def build_report_data(root: Path) -> dict:
    root = Path(root)
    P, R = root / "data" / "processed", root / "reports"
    m = json.loads((R / "metrics.json").read_text(encoding="utf-8"))
    hyp = pd.read_csv(R / "hypotheses.csv")
    hyp["verdict"] = [verdict(r) for _, r in hyp.iterrows()]
    games = pd.read_csv(P / "games.csv")
    ps = pd.read_csv(P / "players_season.csv")
    pg = pd.read_csv(P / "player_games.csv")
    elig = ps[ps.eligible]
    num = pd.read_csv(R / "descriptive_numeric.csv")
    num = num[num.group == "Бүгд"].set_index("variable")
    log = pd.read_csv(R / "cleaning_log.csv")
    chart_titles = pd.read_csv(R / "chart_qa.csv").set_index("name").title
    share = pg.loc[pg.is_import.astype(bool), "PTS"].sum() / pg.PTS.sum()
    h = hyp.set_index("hid")
    cv = m["win_cv"]
    boot = m["win_bootstrap"]
    km = m["kmeans"]
    py = m["pythagorean"]
    kpi = {"games": int(len(games)), "player_seasons": int(len(ps)), "eligible": int(len(elig)),
           "player_games": int(len(pg)), "unique_players": int(ps.player_id.nunique()), "import_share": float(share)}

    snap = re.search(r"Татсан огноо: (\d{4}-\d{2}-\d{2})", (root / "data" / "raw" / "SNAPSHOT.md").read_text(encoding="utf-8"))
    snap_date = snap.group(1) if snap else "тодорхойгүй"
    notes = log.drop_duplicates("step").set_index("step").note.fillna("")
    c1_note = str(notes.get("C1", ""))
    matches = pd.read_csv(R / "name_matches.csv")
    relinks = int((matches.left_id != matches.right_id).sum())
    timing_path = R / "dashboard_timing.csv"
    filter_ms = (pd.read_csv(timing_path).set_index("metric").value.get("filter_update_median_ms")
                 if timing_path.exists() else None)
    player_import_share = float(ps.drop_duplicates("player_id").is_import.mean())
    beats_elo = boot["logreg"]["accuracy"]["lo"] > boot["baseline_elo"]["accuracy"]["hi"]
    model_verdict = ("Загвар Elo baseline-ийг итгэх интервалын хэмжээнд баттай давсан." if beats_elo else
                     "Загвар Elo baseline-ийг итгэх интервалын хэмжээнд баттай давж чадаагүй — энэ нь өөрөө дүгнэлт.")
    h2_contains_null = h.loc["H2", "ci_lo"] <= 0.5 <= h.loc["H2", "ci_hi"]
    h2_text = (f"Талбайн давуу тал нотлогдоогүй (гэрийн багийн ялалт {h.loc['H2', 'estimate']:.1%}, CI 50%-ийг агуулна)."
               if h2_contains_null else f"Гэрийн багийн ялалт {h.loc['H2', 'estimate']:.1%} — 50%-аас баттай ялгаатай.")
    c10_note = str(notes.get("C10", ""))
    from src.charts.comparison import pareto_table
    reg = pg[(pg.phase == "regular") & (pg.season == "2025-2026")]
    pt = pareto_table(reg.groupby("player_id").PTS.sum())
    k80 = int((pt.cum_share.to_numpy() < 0.8).sum()) + 1
    pareto_text = f"Топ {k80 / len(pt):.0%} тоглогч онооны 80%-ийг авдаг"

    def T(name):
        return chart_titles.get(name, name)

    desc = pd.DataFrame([{"Хувьсагч": VAR_NAMES[v], "n": int(r.n), "Дундаж": f"{r['mean']:.2f}",
                          "Медиан": f"{r['median']:.2f}", "Mode": f"{r['mode']:.2f}", "Std": f"{r['std']:.2f}",
                          "Min": f"{r['min']:.2f}", "Q1": f"{r.q1:.2f}", "Q3": f"{r.q3:.2f}", "Max": f"{r['max']:.2f}",
                          "Skew": f"{r['skew']:.2f}"} for v, r in num.iterrows() if v in VAR_NAMES])
    cat = pd.read_csv(R / "descriptive_categorical.csv")
    cat = cat[cat.variable.isin(["position", "is_import", "region"])]
    cat_tbl = pd.DataFrame({"Хувьсагч": cat.variable.map({"position": "Байрлал", "is_import": "Import", "region": "Бүс"}),
                            "Утга": cat.value.astype(str), "Тоо": cat["count"], "Хувь": cat.pct.map(lambda x: f"{x:.1f}%"),
                            "Mode": cat.is_mode.map({True: "✓", False: ""})})
    clog = log.drop_duplicates("step")[["step", "description", "rows_before", "rows_after", "note"]]
    clog = clog.assign(_n=clog.step.str.extract(r"C(\d+)")[0].astype(int), _s=clog.step.str.len()).sort_values(
        ["_n", "_s"]).drop(columns=["_n", "_s"])
    clog.columns = ["Алхам", "Тайлбар", "Өмнө", "Дараа", "Тэмдэглэл"]
    hyp_tbl = pd.DataFrame({"": hyp.hid, "Таамаглал": hyp.statement,
                            "Тооцоо [95% CI]": [f"{r.estimate:.3f} [{r.ci_lo:.3f}, {r.ci_hi:.3f}]" for r in hyp.itertuples()],
                            "Дүгнэлт": hyp.verdict})
    model_names = {"logreg": "Logistic Regression", "rf": "Random Forest", "baseline_elo": "Baseline: Elo",
                   "baseline_winpct": "Baseline: ялалтын хувь"}
    met_tbl = pd.DataFrame([{"Загвар": model_names[k], "Accuracy (CV)": f"{v['accuracy_mean']:.3f} ± {v['accuracy_std']:.3f}",
                             "AUC": f"{v['auc_mean']:.3f}", "Brier": f"{v['brier_mean']:.3f}",
                             "Accuracy 95% CI": f"[{boot[k]['accuracy']['lo']:.3f}, {boot[k]['accuracy']['hi']:.3f}]"}
                            for k, v in cv.items()])
    sources = pd.DataFrame([
        ["MBA статистикийн систем (mongolia.basketball)", "Тоглогчийн статистик, профайл, 252 тоглолтын box score", "Python scraping, robots.txt, ≥1 с"],
        ["Wikipedia: The League (Mongolia), 2023–24 season", "2023-24 байр, гэр хот, аваргууд", "wikitext parse"],
        ["Wikipedia/FIBA: шигшээ багийн бүрэлдэхүүн (2026.08)", "Шигшээ багийн 12 тоглогч", "wikitext parse"],
        ["geoBoundaries (ODbL)", "Монголын аймгийн хил", "GeoJSON"],
    ], columns=["Эх сурвалж", "Агуулга", "Арга"])

    sections = [
        {"title": "1. Оршил, судалгааны асуулт ба таамаглал", "blocks": [
            _para("Энэхүү бие даалт нь Монголын үндэсний дээд лиг (The League)-ийн 2025-26 ба явагдаж буй 2026-27 "
                  "улирлын өгөгдлөөр тоглогч, багийн гүйцэтгэлийг юу тодорхойлдог, тоглолтын үр дүнг урьдчилан "
                  "таамаглаж болох эсэхийг шинжилнэ."),
            _table("Хүснэгт 1. Таамаглалууд ба дүгнэлт", hyp_tbl),
            _draft("Яагаад энэ сэдвийг сонгосон, асуулт хэнд хэрэгтэй вэ гэдгийг өөрийн үгээр бичнэ."),
        ]},
        {"title": "2. Өгөгдөл ба эх сурвалж", "blocks": [
            _table("Хүснэгт 2. Өгөгдлийн эх сурвалж", sources),
            _para(f"Нийт {kpi['games']} тоглолт, {kpi['player_games']:,} тоглогч-тоглолтын мөр, "
                  f"{kpi['player_seasons']} тоглогч-улирал ({kpi['unique_players']} өвөрмөц тоглогч) цуглуулав. "
                  f"Сайт цаг тутам шинэчлэгддэг тул {snap_date}-ны snapshot-ийг ашигласан."),
            _draft("Өгөгдлийг хэрхэн цуглуулсан, ямар ёс зүйн зарчим баримталсныг (robots.txt, хүсэлтийн завсар) тайлбарлана."),
        ]},
        {"title": "3. Өгөгдлийн цэвэрлэгээ ба боловсруулалт", "blocks": [
            _table("Хүснэгт 3. Цэвэрлэгээний алхмууд (reports/cleaning_log.csv-ээс)", clog),
            _fig(root, "U09_data_quality", f"Зураг 1. {T('U09_data_quality')}"),
            _draft(f"Хамгийн сонирхолтой олдвор (C10): {c10_note}. Мөн 1900 гэх мэт placeholder төрсөн оныг засав (C12), "
                   f"оноо зөрчилтэй тоглолтыг илрүүлэв (C13)."),
        ]},
        {"title": "4. Танилцуулах статистик", "blocks": [
            _table("Хүснэгт 4. Тоон хувьсагчдын статистик (GP ≥ 5)", desc),
            _table("Хүснэгт 5. Ангиллын хувьсагчдын давтамж", cat_tbl),
            _draft(f"Оноо баруун тийш хазгай (skew {num.loc['PPG', 'skew']:.2f}): дундаж {num.loc['PPG', 'mean']:.1f} "
                   f"> медиан {num.loc['PPG', 'median']:.1f}, цөөн од тоглогч дунджийг дээш татдаг. "
                   f"Тоглогчийн өндрийн медиан {num.loc['height_cm', 'median']:.0f} см."),
        ]},
        {"title": "5. Өгөгдлийн дүрслэл", "blocks": [
            _para("Бүх график нэг палитр (Okabe-Ito), монгол шошго, эх сурвалжийн тайлбартай; график бүр автомат "
                  "чанарын шалгалтыг (chart_qa) давсан. Гарчиг нь графикийн гол дүгнэлтийг хэлдэг."),
            _fig(root, "F01_ppg_hist", f"Зураг 2. Гистограм — {T('F01_ppg_hist')}"),
            _fig(root, "F02_ts_box_pos", f"Зураг 3. Box plot — {T('F02_ts_box_pos')}"),
            _fig(root, "F03_height_reb", f"Зураг 4. Scatter — {T('F03_height_reb')}"),
            _fig(root, "F04_cum_winpct", f"Зураг 5. Шугаман — {T('F04_cum_winpct')}"),
            _fig(root, "F05_four_factors", f"Зураг 6. Баганат — {T("F05_four_factors")}", 11.5),
            _fig(root, "F06_import_donut", f"Зураг 7. Дугуй — {T("F06_import_donut")}", 10.0),
            _h2("Pareto ба тодорхой бус байдал"),
            _fig(root, "P1_league_pareto", f"Зураг 8. Pareto — {T('P1_league_pareto')}"),
            _fig(root, "U01_ts_funnel", f"Зураг 9. Funnel — {T('U01_ts_funnel')}"),
            _fig(root, "U03_fan_winpct", f"Зураг 10. Fan chart — {T('U03_fan_winpct')}"),
            _draft("График бүрээс юу харагдаж байгааг 1–2 өгүүлбэрээр өөрийн үгээр тайлбарлана. Бусад график "
                   "(heatmap, violin, pair plot, газрын зураг, сүлжээ г.м.) notebooks/04_visualization-д бий."),
        ]},
        {"title": "6. Машин суралцал", "blocks": [
            _para(f"K-Means: k = {km['k']} архетип (silhouette {km['silhouette']:.3f}, bootstrap ARI "
                  f"{km['bootstrap_ari']:.2f}); ялалтын таамаглал: тоглолтын өмнөх 5 хувьсагч, walk-forward CV (5 fold), "
                  f"{m['win_matrix']['n_games']} тоглолт."),
            _fig(root, "F14b_pca_clusters", f"Зураг 11. {T('F14b_pca_clusters')}"),
            _table("Хүснэгт 6. Ялалтын загваруудын үнэлгээ", met_tbl),
            _fig(root, "U06a_model_accuracy", f"Зураг 12. {T('U06a_model_accuracy')}"),
            _draft(f"{model_verdict} "
                   f"Тайлбар загварт eFG%-ийн коэффициент {h.loc['H3', 'estimate']:.2f} хамгийн том."),
        ]},
        {"title": "7. Шинжилгээ ба дүгнэлт", "blocks": [
            _fig(root, "U05_hypotheses", f"Зураг 13. {T('U05_hypotheses')}"),
            _h2("7.1 Үндсэн хандлага"),
            _draft(f"Import тоглогч бүх тоглогчийн {player_import_share:.0%} боловч онооны {share:.0%}-ийг авдаг; медиан онооны зөрүү "
                   f"{h.loc['H1', 'estimate']:.1f} [{h.loc['H1', 'ci_lo']:.1f}–{h.loc['H1', 'ci_hi']:.1f}]."),
            _h2("7.2 Хамаарал"),
            _draft(f"Өндөр ↔ самбар r = {h.loc['H4', 'estimate']:.2f}; Pythagorean R² = {h.loc['H5', 'estimate']:.2f} "
                   f"(лигийн экспонент {py['exponent']:.1f}, NBA 13.91)."),
            _h2("7.3 Онцгой утга"),
            _draft("Funnel дээр 95% хилээс гадуурх тоглогчдын ихэнх нь цөөн шидэлттэй — жинхэнэ онцгой ба азыг ялгах."),
            _h2("7.4 Шалтгаан ба үр дагавар"),
            _draft(f"{h2_text} "
                   "Хамаарал шалтгааныг нотлохгүй: Import тоглогч илүү их минут тоглодог."),
            _h2("7.5 Практик санал"),
            _draft("Шидэлтийн сонголт (eFG%), дотоодын тоглогчийн хөгжил, цөөн тоглогчоос хамаарах эрсдэл."),
        ]},
        {"title": "8. Санал болгож буй шийдэл: MBA Scout", "blocks": [
            _fig(root, "report/blueprint/architecture", "Зураг 14. MBA Scout системийн архитектур", 13.0),
            _bullets(["Скаутын хайлт: архетипээр төстэй тоглогч, статистик бүр итгэх интервалтай",
                      "Тоглолтын өмнөх тайлан: ялах магадлал (20 цэг), Four Factors, Elo явц",
                      f"Интерактив dashboard: 6 хуудас, харилцааны 7 зорилго, шүүлтүүрийн хариу {filter_ms:.0f} мс"]),
            _draft("Санал бүрийг шинжилгээний аль үр дүн дэмжиж байгааг өөрийн үгээр холбож бичнэ."),
        ]},
        {"title": "9. Хязгаарлалт", "blocks": [
            _bullets(["2026-27 улирал дуусаагүй; 2023-24 зөвхөн багийн түвшинд, 2024-25 оны дата байхгүй",
                      f"Улирал хоорондын тоглогчийг нэрээр тааруулсан ({relinks} холбоо); зарим Import шошго, гэр хот батлагдаагүй",
                      "Ялалтын загварын тест жижиг (~210 тоглолт) тул итгэх интервал өргөн",
                      "Ажиглалтын өгөгдөл тул шалтгаан-үр дагаврын дүгнэлт хийх боломжгүй"]),
        ]},
        {"title": "10. Эх сурвалж", "blocks": [
            _bullets([f"Mongolian Basketball Association. Statistics Centre. https://mongolia.basketball/en/stats ({snap_date})",
                      "Wikipedia. The League (Mongolia); 2023–24 The League season; Mongolia men's national basketball team",
                      "geoBoundaries. Mongolia ADM1 (ODbL 1.0)",
                      "Schwabish, J. (2021). Better Data Visualizations. Columbia University Press",
                      "Correll, M., & Gleicher, M. (2014). Error Bars Considered Harmful. IEEE TVCG 20(12)",
                      "Kay, M. et al. (2016). When (ish) is My Bus? Quantile dotplots. CHI",
                      "Yi, J. S. et al. (2007). Toward a Deeper Understanding of the Role of Interaction in InfoVis. IEEE TVCG",
                      "Oliver, D. (2004). Basketball on Paper (Four Factors)"]),
        ]},
    ]

    slides = [
        {"layout": "title", "title": "MBA лигийн гүйцэтгэлийн шинжилгээ",
         "subtitle": "F.ITC341 Өгөгдлийн дүрслэл · Бие даалт · 2026",
         "notes": "Ноорог: судалгааны сэдэв ба зорилгыг өөрийн үгээр танилцуулна."},
        {"layout": "stats", "title": "Асуулт: гүйцэтгэлийг юу тодорхойлдог вэ?",
         "stats": [[str(kpi["games"]), "тоглолт"], [f"{kpi['player_games']:,}", "тоглогч-тоглолт"], ["3", "эх сурвалж"]],
         "bullets": ["5 таамаглал, итгэх интервалтай шалгасан", "2025-26 бүтэн улирал + 2026-27 (явцын)"],
         "notes": "Ноорог: 5 таамаглалыг товч дурдана."},
        {"layout": "image", "title": "Цэвэрлэгээ: датанд бодит алдаа байсан", "image": "figures/U09_data_quality.png",
         "bullets": [f"Багийн нэр: {c1_note}", "MBA-ийн хүснэгт зөвхөн энгийн улирлыг тооцдог (C10)",
                     "1900 гэх мэт placeholder төрсөн он засав (C12)"],
         "notes": "Ноорог: цэвэрлэгээний 12 алхмаас хамгийн чухал 3-ыг тайлбарлана."},
        {"layout": "image", "title": "Онооны тархалт: Import ба дотоод", "image": "figures/F01_ppg_hist.png",
         "bullets": [f"Import тоглогчид онооны {share:.0%}-ийг авдаг", "Тархалт баруун тийш хазгай"],
         "notes": "Ноорог: гистограмаас юу харагдаж байгааг тайлбарлана."},
        {"layout": "image", "title": "Pareto: онооны төвлөрөл", "image": "figures/P1_league_pareto.png",
         "bullets": [pareto_text, "Саарал зурвас = 95% CI"],
         "notes": "Ноорог: Pareto chart-ийг хэрхэн уншихыг тайлбарлана."},
        {"layout": "image", "title": "Funnel: оновч уу, аз уу?", "image": "figures/U01_ts_funnel.png",
         "bullets": ["Цөөн шидэлттэй үед хил өргөн", "Онцгой мэт харагдах нь заримдаа аз"],
         "notes": "Ноорог: funnel plot нь тодорхой бус байдлыг яаж харуулдгийг тайлбарлана."},
        {"layout": "image", "title": "Fan chart: ялалтын хувийн тодорхой бус байдал", "image": "figures/U03_fan_winpct.png",
         "bullets": ["Улирлын эхэнд итгэх интервал өргөн", "Fan = 50/80/95% Wilson интервал"],
         "notes": "Ноорог: улирлын явцад тодорхой бус байдал хэрхэн буурдгийг тайлбарлана."},
        {"layout": "image", "title": "Таамаглалын дүн", "image": "figures/U05_hypotheses.png",
         "bullets": [f"{r.hid}: {r.verdict}" for r in hyp.itertuples()][:3],
         "notes": "Ноорог: таамаглал бүрийн дүгнэлтийг өөрийн үгээр."},
        {"layout": "image", "title": "ML 1: тоглогчийн архетип (K-Means)", "image": "figures/F14b_pca_clusters.png",
         "bullets": [f"k = {km['k']}: " + ", ".join(sorted(set(km['names'].values()))), f"Bootstrap ARI {km['bootstrap_ari']:.2f}"],
         "notes": "Ноорог: архетипүүдийг тайлбарлана."},
        {"layout": "image", "title": "ML 2: ялалтын таамаглал", "image": "figures/U06a_model_accuracy.png",
         "bullets": [f"Logistic Regression acc {cv['logreg']['accuracy_mean']:.2f}, Elo baseline {cv['baseline_elo']['accuracy_mean']:.2f}",
                     "Walk-forward CV, leakage-гүй"],
         "notes": "Ноорог: яагаад ML загвар baseline-ийг давж чадаагүйг тайлбарлана."},
        {"layout": "image", "title": "Шийдэл: MBA Scout ба интерактив dashboard", "image": "report/blueprint/architecture.png",
         "bullets": ["Dashboard: 6 хуудас, харилцааны 7 зорилго", "Локал: streamlit run mba_analysis/dashboard/app.py"],
         "notes": "Ноорог: dashboard-ийг шууд үзүүлж тайлбарлана."},
        {"layout": "closing", "title": "Дүгнэлт ба санал",
         "bullets": ["Import тоглогч оноонд давамгай; дотоодын тоглогчийн хөгжилд анхаарах",
                     "Ялалтыг eFG% хамгийн их тайлбарладаг",
                     "Тодорхой бус байдлыг харуулах нь буруу дүгнэлтээс сэргийлнэ"],
         "notes": "Ноорог: гол 3 дүгнэлт, асуултад бэлтгэнэ."},
    ]
    hyp_records = hyp.astype(object).where(hyp.notna(), None).to_dict(orient="records")
    return {"kpi": kpi, "hypotheses": hyp_records, "sections": sections, "slides": slides,
            "draft_label": DRAFT_LABEL}


if __name__ == "__main__":
    root = Path(__file__).resolve().parents[1]
    (root / "report").mkdir(exist_ok=True)
    data = build_report_data(root)
    (root / "report" / "report_data.json").write_text(json.dumps(data, ensure_ascii=False, indent=1), encoding="utf-8")
    print("ok", len(data["sections"]), "sections,", len(data["slides"]), "slides")
