# MBA лигийн гүйцэтгэлийн шинжилгээ

Бие даалт — F.ITC341 Өгөгдлийн дүрслэл. Дизайн: [../docs/superpowers/specs/2026-11-12-mba-analysis-design.md](../docs/superpowers/specs/2026-11-12-mba-analysis-design.md)

## Хавтасны бүтэц

| Хавтас | Агуулга |
|---|---|
| `data/raw/` | Эх сурвалжаас татсан CSV, `SNAPSHOT.md` (татсан огноо). `html/` кэш нь git-д орохгүй |
| `data/processed/` | Цэвэрлэсэн, нэгтгэсэн хүснэгтүүд (spec §3) |
| `src/` | Татах, цэвэрлэх, шинэ хувьсагч, загварын код |
| `notebooks/` | 01_collect → 06_ml дарааллаар ажиллуулах notebook-ууд |
| `figures/` | Тайланд орох график (PNG, 300 dpi) |
| `reports/` | Цэвэрлэгээний лог, загварын метрик |
| `dashboard/` | Streamlit интерактив dashboard |
| `report/` | Word тайлан, PowerPoint, шийдлийн зураг төсөл (`blueprint/`) |

## Орчин бэлдэх

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Бүх үр дүнг дахин гаргах

`mba_analysis/` хавтаснаас ажиллуулна. Кэш (`data/raw/html/`) байгаа бол сүлжээгүйгээр ажиллана.
Кэшээс давтан ажиллуулахад дата, тайлан, график яг ижил гарна (шалгасан: `reports/acceptance.md`).

```bash
.venv/bin/python -m src.scrape --offline   # MBA (кэшгүй бол --offline-ийг хасаж татна, ~15 мин)
.venv/bin/python -m src.wiki               # Wikipedia / FIBA
.venv/bin/python -m src.clean              # C1–C12 + шинэ хувьсагч, Elo
.venv/bin/python -m src.models             # K-Means, ялалтын загвар (H3/H5-д хэрэгтэй тул analysis-аас өмнө)
.venv/bin/python -m src.analysis           # статистик, H1–H5
.venv/bin/python -m src.make_figures       # 29 график + chart_qa
.venv/bin/python -m src.blueprint          # шийдлийн зураг төсөл
.venv/bin/python -m src.build_dashboard_data
.venv/bin/python -m src.report_data
(cd tools/report && npm install && node build_docx.js ../../report/report_data.json ../../report/MBA_tailan.docx \
  && node build_pptx.js ../../report/report_data.json ../../report/MBA_taniltsuulga.pptx)
.venv/bin/python -m pytest                 # 184 тест
```

## Dashboard

Локал дээр ажиллуулах (repo-гийн үндсэн хавтаснаас):

```bash
mba_analysis/.venv/bin/streamlit run mba_analysis/dashboard/app.py
```

**Streamlit Community Cloud-д байршуулах** (хэрэглэгч өөрөө хийнэ):
1. https://share.streamlit.io руу GitHub-аараа нэвтэрнэ.
2. "Create app" → Repository: `batdorj-s/data-visualization-3a`, Branch: `main`,
   Main file path: `mba_analysis/dashboard/app.py`.
3. Python 3.13 сонгоод "Deploy" дарна. Санууд нь `mba_analysis/dashboard/requirements.txt`-аас суулгагдана.
4. Гарсан URL-ийг тайлан, слайдад оруулна.

Dashboard нь зөвхөн `dashboard/data/*.parquet`-ийг уншдаг. Датаг шинэчлэх бол
`python -m src.build_dashboard_data` ажиллуулна. Хугацааны хэмжилт: `python tools/time_dashboard.py`
→ `reports/dashboard_timing.csv`.

## Өгөгдлийн эх сурвалж

1. MBA статистикийн систем — https://mongolia.basketball/en/stats
2. Wikipedia — The League (Mongolia), 2023–24 The League season
3. Wikipedia/FIBA — Mongolia men's national basketball team (2026.08-ийн бүрэлдэхүүн)

Дэлгэрэнгүйг [../docs/research/2026-11-12-data-sources.md](../docs/research/2026-11-12-data-sources.md)-аас үзнэ үү.
