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

## Өгөгдлийн эх сурвалж

1. MBA статистикийн систем — https://mongolia.basketball/en/stats
2. Wikipedia — The League (Mongolia), 2023–24 The League season
3. Wikipedia/FIBA — Mongolia men's national basketball team (2026.08-ийн бүрэлдэхүүн)

Дэлгэрэнгүйг [../docs/research/2026-11-12-data-sources.md](../docs/research/2026-11-12-data-sources.md)-аас үзнэ үү.
