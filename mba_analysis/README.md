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
