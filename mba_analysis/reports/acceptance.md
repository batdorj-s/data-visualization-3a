# Хүлээн авах шалгуур (spec §15) — шалгалтын үр дүн

Шалгасан огноо: 2026-11-13 · Branch: `feat/mba-analysis` · Тест: `.venv/bin/python -m pytest` → **162 passed**

| # | Шалгуур | Дүн | Нотолгоо |
|---|---|---|---|
| 1 | `python -m src.scrape` кэштэй үед сүлжээгүйгээр давтан ажиллаж §3-ийн бүх CSV-г үүсгэнэ | ✅ | `--offline` горимоор бүтэн pipeline-ийг 2 удаа ажиллуулахад git зөрүү 0 (дата, тайлан, график бүгд ижил) |
| 2 | Mapping-гүй багийн нэр 0, C10 зөрүү тайлбартай | ✅ | `UnmappedTeamError` гараагүй; C10: бүх тоглолтоор 79 → энгийн улирлаар 8 зөрүү (MBA-ийн хүснэгт зөвхөн энгийн улирлыг тооцдог), `reports/ppg_validation.csv` |
| 3 | players_season (GP ≥ 5) ≥ 230, games ≥ 240 | ✅ | 273 тоглогч-улирал, 252 тоглолт |
| 4 | F1–F6 монгол гарчиг, тэнхлэг, legend, эх сурвалжийн caption | ✅ | `reports/chart_qa.csv`: 29/29 `ok` |
| 5 | K-Means: silhouette ба bootstrap ARI тайлагнагдсан | ✅ | k = 3, silhouette 0.215, ARI 0.779 (`reports/metrics.json`) |
| 6 | Win model: walk-forward CV, 95% CI, 2 baseline | ✅ | Logistic Regression acc 0.592 ± 0.091, AUC 0.655; bootstrap acc 0.585 [0.519, 0.656]; Elo baseline 0.603 → baseline-ийг баттай давахгүй (шударга дүгнэлт) |
| 7 | P1–P3 Pareto: эрэмбэлсэн, тэнхлэг 0-ээс, 80% шугам, P1 CI зурвас | ✅ | `tests/test_charts_time_cmp.py`, `tests/test_charts_ml.py` |
| 8 | U1–U9: CI-г cluster bootstrap / Wilson / Fisher-ээр, caption-д аргачлал | ✅ | caption бүрт аргачлал; `src/uncertainty.py` тестүүд |
| 9 | Бүх `figures/*.png` `chart_qa`-г давсан | ✅ | 29/29 |
| 10 | Dashboard ажиллаж, 7 харилцааны зорилго хэрэгжсэн | ✅ | `tests/test_dashboard.py` 9/9; хөтөч дээр шалгасан (console алдаа 0, 375 px layout) |
| 11 | Dashboard хугацаа: анх < 3 с, шүүлтүүр median < 300 мс | ✅ | 664 мс / 31 мс (серверийн тал, AppTest) `reports/dashboard_timing.csv` |
| 12 | Тайлан 8–10 хуудас, слайд ~12, зураг төсөл 2+ | ⚠️ хэсэгчлэн | Слайд 12 ✅, зураг төсөл 3 ✅; Word-ийн хуудасны тоог хэмжих боломжгүй байсан (LibreOffice байхгүй, Word-ийн автоматжуулалт файлын зөвшөөрөл шаардсан) — тооцоогоор ≈ 9–10 хуудас. **Word дээр нээж шалгах** |

## Илгээхээс өмнө оюутны хийх зүйлс
1. `report/MBA_tailan.docx`, `report/MBA_taniltsuulga.pptx` дахь шар "[Ноорог — өөрийн үгээр дахин бичих]" хэсгүүдийг өөрийн үгээр бичих (даалгаврын шаардлага).
2. Word дээр хуудасны тоо 8–10 эсэхийг шалгах.
3. Dashboard-ийг Streamlit Community Cloud-д байршуулж URL-ийг тайлан, слайдад нэмэх (`README.md`).
