"""Тайлан, слайдын агуулгыг (тоо, хүснэгт, зураг, ноорог) датаас үүсгэж report/report_data.json болгоно.

Ноорог блок бүр DRAFT_LABEL-тай: эцсийн тайлбарыг оюутан өөрийн үгээр бичнэ (даалгаврын шаардлага).
"""
import json
import re
from pathlib import Path

import pandas as pd
from PIL import Image

from src.charts.summary import VERDICT_PLAIN, verdict
from src.glossary import TERMS

DRAFT_LABEL = "[Ноорог — өөрийн үгээр дахин бичих]"
VAR_NAMES = {"PPG": "Оноо/тоглолт", "RPG": "Самбар/тоглолт", "APG": "Дамжуулалт/тоглолт", "MIN": "Минут/тоглолт",
             "ts_pct": "Шидэлтийн оновч", "height_cm": "Өндөр (см)", "age": "Нас"}


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
    model_verdict = ("ML загвар «хүчний оноо өндөр нь ялна» гэсэн энгийн дүрмийг баттай давсан." if beats_elo else
                     "ML загвар «хүчний оноо өндөр нь ялна» гэсэн энгийн дүрмийг баттай давж чадаагүй — "
                     "энэ нь өөрөө чухал дүгнэлт: MBA-д багийн хүч ялалтыг хамгийн сайн тайлбарладаг.")
    h2_contains_null = h.loc["H2", "ci_lo"] <= 0.5 <= h.loc["H2", "ci_hi"]
    h2_text = (f"Гэрийн талбайн давуу тал батлагдаагүй: гэрийн баг {h.loc['H2', 'estimate']:.0%} ялсан ч бодит хувь "
               f"{h.loc['H2', 'ci_lo']:.0%}–{h.loc['H2', 'ci_hi']:.0%} хооронд байж болох тул 50%-аас ялгаатай гэж хэлж чадахгүй."
               if h2_contains_null else f"Гэрийн баг {h.loc['H2', 'estimate']:.0%} ялсан нь 50%-аас баттай ялгаатай.")
    c10_note = str(notes.get("C10", ""))
    from src.charts.comparison import pareto_table
    reg = pg[(pg.phase == "regular") & (pg.season == "2025-2026")]
    pt = pareto_table(reg.groupby("player_id").PTS.sum())
    k80 = int((pt.cum_share.to_numpy() < 0.8).sum()) + 1
    pareto_text = f"Тоглогчдын {k80 / len(pt):.0%} нь онооны 80%-ийг авдаг"

    def T(name):
        return chart_titles.get(name, name)

    desc = pd.DataFrame([{"Үзүүлэлт": VAR_NAMES[v], "Тоо": int(r.n), "Дундаж": f"{r['mean']:.2f}",
                          "Голч": f"{r['median']:.2f}", "Моод": f"{r['mode']:.2f}", "Ст. хазайлт": f"{r['std']:.2f}",
                          "Бага": f"{r['min']:.2f}", "Q1": f"{r.q1:.2f}", "Q3": f"{r.q3:.2f}", "Их": f"{r['max']:.2f}",
                          "Хазгай": f"{r['skew']:.2f}"} for v, r in num.iterrows() if v in VAR_NAMES])
    cat = pd.read_csv(R / "descriptive_categorical.csv")
    cat = cat[cat.variable.isin(["position", "is_import", "region"])]
    cat_val = cat.value.astype(str).where(cat.variable != "is_import",
                                          cat.value.astype(str).map({"True": "Гадаад", "False": "Дотоод"}))
    cat_tbl = pd.DataFrame({"Үзүүлэлт": cat.variable.map({"position": "Байрлал", "is_import": "Гадаад/дотоод",
                                                          "region": "Бүс"}),
                            "Утга": cat_val, "Тоо": cat["count"], "Хувь": cat.pct.map(lambda x: f"{x:.1f}%"),
                            "Хамгийн олон": cat.is_mode.map({True: "✓", False: ""})})
    clog = log.drop_duplicates("step")[["step", "description", "rows_before", "rows_after", "note"]]
    clog = clog.assign(_n=clog.step.str.extract(r"C(\d+)")[0].astype(int), _s=clog.step.str.len()).sort_values(
        ["_n", "_s"]).drop(columns=["_n", "_s"])
    clog.columns = ["Алхам", "Тайлбар", "Өмнө", "Дараа", "Тэмдэглэл"]
    hyp_tbl = pd.DataFrame({"": hyp.hid, "Таамаглал": hyp.statement,
                            "Датаас гарсан утга [95% хүрээ]": [f"{r.estimate:.2f} [{r.ci_lo:.2f} – {r.ci_hi:.2f}]"
                                                               for r in hyp.itertuples()],
                            "Дүгнэлт": hyp.verdict.map(VERDICT_PLAIN)})
    model_names = {"logreg": "ML: логистик регресс", "rf": "ML: санамсаргүй ой", "baseline_elo": "Дүрэм: хүчний оноо",
                   "baseline_winpct": "Дүрэм: ялалтын хувь"}
    met_tbl = pd.DataFrame([{"Арга": model_names[k],
                             "Зөв таамагласан": f"{v['accuracy_mean']:.0%} ± {v['accuracy_std']:.0%}",
                             "95% хүрээ": f"{boot[k]['accuracy']['lo']:.0%} – {boot[k]['accuracy']['hi']:.0%}",
                             "Ялгах чадвар (AUC)": f"{v['auc_mean']:.2f}", "Магадлалын алдаа (Brier)": f"{v['brier_mean']:.3f}"}
                            for k, v in cv.items()])
    gloss_tbl = pd.DataFrame([(plain, tech, text) for plain, tech, text in TERMS],
                             columns=["Энгийн нэр", "Мэргэжлийн нэр", "Тайлбар"])
    sources = pd.DataFrame([
        ["MBA лигийн албан ёсны статистик (mongolia.basketball)", "Тоглогчийн статистик, профайл, 252 тоглолтын хайрцаг оноо",
         "Python-оор вэб хуудаснаас татсан; сайтын дүрмийг (robots.txt) дагаж, хүсэлт хооронд ≥1 с хүлээсэн"],
        ["Wikipedia: The League (Mongolia), 2023–24 улирал", "2023–24 улирлын байр, багийн хот, аваргууд", "Хуудасны текстээс уншсан"],
        ["Wikipedia/FIBA: шигшээ багийн бүрэлдэхүүн (2026.08)", "Шигшээ багийн 12 тоглогч", "Хуудасны текстээс уншсан"],
        ["geoBoundaries (ODbL лиценз)", "Монголын аймгийн хил", "Газрын зургийн файл (GeoJSON)"],
    ], columns=["Эх сурвалж", "Агуулга", "Хэрхэн авсан"])

    sections = [
        {"title": "1. Оршил, судалгааны асуулт ба таамаглал", "blocks": [
            _para("Энэхүү бие даалт нь Монголын сагсан бөмбөгийн дээд лиг (The League)-ийн 2025–26 ба одоо явагдаж буй "
                  "2026–27 улирлын датагаар хоёр асуултад хариулна: тоглогч, багийн амжилтыг юу тодорхойлдог вэ, "
                  "тоглолтын ялагчийг урьдчилан таамаглаж болох уу?"),
            _para("Тоо бүрийг «бодит утга байх магадлалтай хүрээ»-тэй (95%) хамт өгсөн: нэг улиралд баг 20–30 л тоглолт "
                  "тоглодог тул санамсаргүй хэлбэлзэл их. Нэр томьёоны тайлбарыг 10-р бүлгийн төгсгөлөөс үзнэ үү."),
            _table("Хүснэгт 1. Таамаглалууд ба дүгнэлт", hyp_tbl),
            _draft("Яагаад энэ сэдвийг сонгосон, асуулт хэнд хэрэгтэй вэ гэдгийг өөрийн үгээр бичнэ."),
        ]},
        {"title": "2. Өгөгдөл ба эх сурвалж", "blocks": [
            _table("Хүснэгт 2. Өгөгдлийн эх сурвалж", sources),
            _para(f"Нийт {kpi['games']} тоглолт, тоглогч бүрийн {kpi['player_games']:,} тоглолтын бичлэг, "
                  f"{kpi['player_seasons']} тоглогч-улирал ({kpi['unique_players']} өөр тоглогч) цуглуулав. "
                  f"Сайт байнга шинэчлэгддэг тул бүх тооцоо {snap_date}-нд татсан хувилбар дээр хийгдсэн."),
            _draft("Өгөгдлийг хэрхэн цуглуулсан, ямар ёс зүйн зарчим баримталсныг (robots.txt, хүсэлтийн завсар) тайлбарлана."),
        ]},
        {"title": "3. Өгөгдлийн цэвэрлэгээ ба боловсруулалт", "blocks": [
            _table("Хүснэгт 3. Цэвэрлэгээний алхмууд", clog),
            _fig(root, "U09_data_quality", f"Зураг 1. {T('U09_data_quality')}"),
            _draft(f"Хамгийн сонирхолтой олдвор (C10): {c10_note}. Мөн «1900» гэх мэт бодит бус төрсөн оныг засав (C12), "
                   f"гарчиг дээрх оноо ба тоглогчдын онооны нийлбэр зөрсөн тоглолтуудыг илрүүлэв (C13)."),
        ]},
        {"title": "4. Танилцуулах статистик", "blocks": [
            _table("Хүснэгт 4. Тоон үзүүлэлтүүдийн статистик (5+ тоглолт тоглосон тоглогчид)", desc),
            _table("Хүснэгт 5. Ангиллын үзүүлэлтүүдийн давтамж", cat_tbl),
            _draft(f"Онооны тархалт тэгш биш: дундаж {num.loc['PPG', 'mean']:.1f} нь голч утга "
                   f"{num.loc['PPG', 'median']:.1f}-ээс их, учир нь цөөн од тоглогч дунджийг дээш татдаг "
                   f"(хазгайн коэффициент {num.loc['PPG', 'skew']:.2f}). Тоглогчийн өндрийн голч утга "
                   f"{num.loc['height_cm', 'median']:.0f} см."),
        ]},
        {"title": "5. Өгөгдлийн дүрслэл", "blocks": [
            _para("Бүх график өнгөний сохролттой хүнд ч ялгарах нэг өнгөний багц (Okabe-Ito), монгол шошготой. Гарчиг нь "
                  "графикийн гол дүгнэлтийг шууд хэлж, дэд гарчиг нь хэрхэн уншихыг, доод мөр нь ямар дата, хэдэн "
                  "ширхэгийг ашигласныг заана. График бүр автомат чанарын шалгалтыг давсан."),
            _fig(root, "F01_ppg_hist", f"Зураг 2. Гистограм — {T('F01_ppg_hist')}"),
            _fig(root, "F02_ts_box_pos", f"Зураг 3. Хайрцган график (box plot) — {T('F02_ts_box_pos')}"),
            _fig(root, "F03_height_reb", f"Зураг 4. Цэгэн график (scatter) — {T('F03_height_reb')}"),
            _fig(root, "F04_cum_winpct", f"Зураг 5. Шугаман график — {T('F04_cum_winpct')}"),
            _fig(root, "F05_four_factors", f"Зураг 6. Баганан график — {T("F05_four_factors")}", 11.5),
            _fig(root, "F06_import_donut", f"Зураг 7. Цагираган график — {T("F06_import_donut")}", 10.0),
            _h2("Парето (Pareto) ба тодорхой бус байдлын график"),
            _fig(root, "P1_league_pareto", f"Зураг 8. Парето (Pareto) график — {T('P1_league_pareto')}"),
            _fig(root, "U01_ts_funnel", f"Зураг 9. Юүлүүр (funnel) график — {T('U01_ts_funnel')}"),
            _fig(root, "U03_fan_winpct", f"Зураг 10. Сэнсэн (fan) график — {T('U03_fan_winpct')}"),
            _draft("График бүрээс юу харагдаж байгааг 1–2 өгүүлбэрээр өөрийн үгээр тайлбарлана. Бусад график "
                   "(дулааны зураг, violin, хос харьцуулалт, газрын зураг, шилжилтийн сүлжээ г.м.) "
                   "notebooks/04_visualization-д бий."),
        ]},
        {"title": "6. Машин суралцал", "blocks": [
            _para(f"Хоёр зүйл хийсэн. (1) Тоглогчдыг статистикаар нь {km['k']} тоглолтын хэв маягт автоматаар бүлэглэсэн "
                  f"(K-Means арга; бүлгүүдийн ялгарал {km['silhouette']:.2f}, дахин тооцоход бүлэглэлт "
                  f"{km['bootstrap_ari']:.0%} давхцсан). (2) Тоглолтын ялагчийг зөвхөн тоглолтоос өмнөх 5 үзүүлэлтээр "
                  f"таамагласан: загварыг он цагийн дарааллаар өмнөх тоглолтоор сургаж, дараагийнхыг таамаглуулсан "
                  f"({m['win_matrix']['n_games']} тоглолт)."),
            _fig(root, "F14b_pca_clusters", f"Зураг 11. {T('F14b_pca_clusters')}"),
            _table("Хүснэгт 6. Ялагч таамаглах аргуудын үнэлгээ", met_tbl),
            _fig(root, "U06a_model_accuracy", f"Зураг 12. {T('U06a_model_accuracy')}"),
            _draft(f"{model_verdict} "
                   f"Ялалтыг тайлбарлах загварт шидэлтийн оновч бусад хүчин зүйлээс {h.loc['H3', 'estimate']:.1f} "
                   f"нэгжээр илүү нөлөөтэй гарсан."),
        ]},
        {"title": "7. Шинжилгээ ба дүгнэлт", "blocks": [
            _fig(root, "U05_hypotheses", f"Зураг 13. {T('U05_hypotheses')}"),
            _h2("7.1 Үндсэн хандлага"),
            _draft(f"Гадаад тоглогч бүх тоглогчийн {player_import_share:.0%} боловч онооны {share:.0%}-ийг авдаг; голч "
                   f"утгаараа тоглолт бүрт {h.loc['H1', 'estimate']:.1f} оноогоор илүү (бодит зөрүү "
                   f"{h.loc['H1', 'ci_lo']:.1f}–{h.loc['H1', 'ci_hi']:.1f} оноо байх магадлалтай)."),
            _h2("7.2 Хамаарал"),
            _draft(f"Өндөр ба самбарын хамаарлын хүч {h.loc['H4', 'estimate']:.2f} (хүчтэй). Багийн авсан, алдсан оноо "
                   f"ялалтын хувийн {h.loc['H5', 'estimate']:.0%}-ийг тайлбарладаг (томьёоны илтгэгч MBA-д "
                   f"{py['exponent']:.1f}, NBA-д 13.91)."),
            _h2("7.3 Онцгой утга"),
            _draft("Юүлүүр график дээр юүлүүрээс гадуурх тоглогчдын ихэнх нь цөөн шидэлттэй — жинхэнэ онцгой "
                   "тоглогч ба азаар өндөр харагдаж буйг ялгах хэрэгтэй."),
            _h2("7.4 Шалтгаан ба үр дагавар"),
            _draft(f"{h2_text} "
                   "Хоёр зүйл хамт өөрчлөгддөг нь нэг нь нөгөөгийн шалтгаан гэсэн үг биш: гадаад тоглогч илүү "
                   "олон минут тоглодог тул оноо ч их."),
            _h2("7.5 Практик санал"),
            _draft("Шидэлтийн оновчийг сайжруулах, дотоодын тоглогчийн хөгжил, цөөн од тоглогчоос хамаарах эрсдэл."),
        ]},
        {"title": "8. Санал болгож буй шийдэл: MBA Scout", "blocks": [
            _fig(root, "report/blueprint/architecture", "Зураг 14. MBA Scout системийн архитектур", 13.0),
            _bullets(["Скаутын хайлт: хэв маягаар төстэй тоглогч олох, тоо бүр магадлалтай хүрээтэй",
                      "Тоглолтын өмнөх тайлан: ялах магадлал («20 тоглолтоос хэд»), ялалтын 4 хүчин зүйл, хүчний онооны явц",
                      f"Интерактив dashboard: 7 хуудас (нэр томьёоны толь орсон), харилцааны 7 зорилго, шүүлтүүрийн хариу "
                      f"{filter_ms:.0f} мс"]),
            _draft("Санал бүрийг шинжилгээний аль үр дүн дэмжиж байгааг өөрийн үгээр холбож бичнэ."),
        ]},
        {"title": "9. Хязгаарлалт", "blocks": [
            _bullets(["2026–27 улирал дуусаагүй; 2023–24 зөвхөн багийн түвшинд, 2024–25 оны дата байхгүй",
                      f"Улирал хоорондын тоглогчийг нэрээр нь тааруулсан ({relinks} холбоо); зарим тоглогчийн гадаад "
                      "эсэх, багийн хот эх сурвалжаар батлагдаагүй",
                      "Ялагч таамаглах загварыг шалгах тоглолт цөөн (~210) тул магадлалтай хүрээ өргөн",
                      "Туршилт бус, ажигласан дата тул «шалтгаан нь юу вэ» гэдгийг баталж чадахгүй"]),
        ]},
        {"title": "10. Эх сурвалж ба нэр томьёо", "blocks": [
            _bullets([f"Mongolian Basketball Association. Statistics Centre. https://mongolia.basketball/en/stats ({snap_date})",
                      "Wikipedia. The League (Mongolia); 2023–24 The League season; Mongolia men's national basketball team",
                      "geoBoundaries. Mongolia ADM1 (ODbL 1.0)",
                      "Schwabish, J. (2021). Better Data Visualizations. Columbia University Press",
                      "Correll, M., & Gleicher, M. (2014). Error Bars Considered Harmful. IEEE TVCG 20(12)",
                      "Kay, M. et al. (2016). When (ish) is My Bus? Quantile dotplots. CHI",
                      "Yi, J. S. et al. (2007). Toward a Deeper Understanding of the Role of Interaction in InfoVis. IEEE TVCG",
                      "Oliver, D. (2004). Basketball on Paper (Four Factors)"]),
            _h2("Нэр томьёоны тайлбар"),
            _table("Хүснэгт 7. Тайланд хэрэглэсэн нэр томьёо", gloss_tbl),
        ]},
    ]

    slides = [
        {"layout": "title", "title": "MBA лигийн гүйцэтгэлийн шинжилгээ",
         "subtitle": "F.ITC341 Өгөгдлийн дүрслэл · Бие даалт · 2026",
         "notes": "Ноорог: судалгааны сэдэв ба зорилгыг өөрийн үгээр танилцуулна."},
        {"layout": "stats", "title": "Асуулт: гүйцэтгэлийг юу тодорхойлдог вэ?",
         "stats": [[str(kpi["games"]), "тоглолт"], [f"{kpi['player_games']:,}", "тоглогчийн тоглолт"], ["3", "эх сурвалж"]],
         "bullets": ["5 таамаглалыг магадлалтай хүрээгээр шалгасан", "2025–26 бүтэн улирал + 2026–27 (явагдаж буй)"],
         "notes": "Ноорог: 5 таамаглалыг товч дурдана."},
        {"layout": "image", "title": "Цэвэрлэгээ: датанд бодит алдаа байсан", "image": "figures/U09_data_quality.png",
         "bullets": [f"Багийн нэр: {c1_note}", "Сайтын нэгтгэл зөвхөн үндсэн шатыг тооцдог (C10)",
                     "«1900» гэх мэт бодит бус төрсөн оныг засав (C12)"],
         "notes": "Ноорог: цэвэрлэгээний 12 алхмаас хамгийн чухал 3-ыг тайлбарлана."},
        {"layout": "image", "title": "Онооны тархалт: гадаад ба дотоод", "image": "figures/F01_ppg_hist.png",
         "bullets": [f"Гадаад тоглогчид онооны {share:.0%}-ийг авдаг", "Ихэнх нь цөөн, цөөхөн нь маш их оноо авдаг"],
         "notes": "Ноорог: гистограмаас юу харагдаж байгааг тайлбарлана."},
        {"layout": "image", "title": "Парето: цөөн тоглогч ихэнх оноог авдаг", "image": "figures/P1_league_pareto.png",
         "bullets": [pareto_text, "Саарал сүүдэр = 95% магадлалтай хүрээ"],
         "notes": "Ноорог: Парето (Pareto) графикийг хэрхэн уншихыг тайлбарлана."},
        {"layout": "image", "title": "Юүлүүр: оновч уу, аз уу?", "image": "figures/U01_ts_funnel.png",
         "bullets": ["Цөөн шидэлттэй тоглогчийн хүрээ өргөн", "Онцгой мэт харагдах нь заримдаа аз"],
         "notes": "Ноорог: юүлүүр график тодорхой бус байдлыг яаж харуулдгийг тайлбарлана."},
        {"layout": "image", "title": "Ялалтын хувь: хэр итгэлтэй вэ?", "image": "figures/U03_fan_winpct.png",
         "bullets": ["Улирлын эхэнд хүрээ өргөн, сүүлд нарийн", "Сүүдэр = 50 / 80 / 95% магадлалтай хүрээ"],
         "notes": "Ноорог: улирлын явцад тодорхой бус байдал хэрхэн буурдгийг тайлбарлана."},
        {"layout": "image", "title": "Таамаглалын дүн", "image": "figures/U05_hypotheses.png",
         "bullets": [f"{r.hid}: {VERDICT_PLAIN[r.verdict]}" for r in hyp.itertuples()][:3],
         "notes": "Ноорог: таамаглал бүрийн дүгнэлтийг өөрийн үгээр."},
        {"layout": "image", "title": "ML 1: тоглогчийн хэв маяг", "image": "figures/F14b_pca_clusters.png",
         "bullets": [f"{km['k']} хэв маяг: " + ", ".join(sorted(set(km['names'].values()))),
                     f"Дахин тооцоход {km['bootstrap_ari']:.0%} давхцсан (тогтвортой)"],
         "notes": "Ноорог: хэв маяг бүрийг тайлбарлана."},
        {"layout": "image", "title": "ML 2: ялагчийг таамаглах", "image": "figures/U06a_model_accuracy.png",
         "bullets": [f"ML загвар {cv['logreg']['accuracy_mean']:.0%}, энгийн дүрэм {cv['baseline_elo']['accuracy_mean']:.0%} зөв",
                     "Зөвхөн тоглолтын өмнөх датаг ашигласан"],
         "notes": "Ноорог: яагаад ML загвар энгийн дүрмийг давж чадаагүйг тайлбарлана."},
        {"layout": "image", "title": "Шийдэл: MBA Scout ба интерактив dashboard", "image": "report/blueprint/architecture.png",
         "bullets": ["Dashboard: 7 хуудас, энгийн хэлтэй, нэр томьёоны тольтой", "Харилцааны 7 зорилгыг бүгдийг хэрэгжүүлсэн"],
         "notes": "Ноорог: dashboard-ийг шууд үзүүлж тайлбарлана."},
        {"layout": "closing", "title": "Дүгнэлт ба санал",
         "bullets": ["Гадаад тоглогч оноонд давамгай; дотоодын тоглогчийн хөгжилд анхаарах",
                     "Ялалтыг шидэлтийн оновч хамгийн их тайлбарладаг",
                     "Магадлалтай хүрээг харуулах нь буруу дүгнэлтээс сэргийлнэ"],
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
