"""MBA Analytics dashboard-ийн кодоос (ui.py, palette.py) Design System-ийн файлуудыг (tokens, бүрэлдэхүүний жишээ) үүсгэнэ.

Ажиллуулах (mba_analysis/dashboard хавтаснаас):  ../.venv/bin/python ../tools/design_system/build.py <гаралтын хавтас>
Бүрэлдэхүүний HTML нь ui.py-ийн функцуудыг ажиллуулж барьсан markup тул dashboard-тай яг ижил. README.md, charts.md, cover-ийг
design system дээр гараар бичсэн."""
import json, re, sys, types
from pathlib import Path

DASH = Path.cwd()
OUT = Path(sys.argv[1]) / "project"
sys.path[:0] = [str(DASH), str(DASH.parent)]

# --- markup-ийг яг ui.py-аас: st.html-ийг барьж авна
import streamlit as st
captured = []
st.html = lambda body, *a, **k: captured.append(body)
fake = types.ModuleType("data_access")
fake.current_filters = lambda: types.SimpleNamespace(season="2025-2026")
fake.snapshot = lambda: "2026-11-12"
sys.modules["data_access"] = fake
import ui
from src.palette import PALETTE, NEUTRAL, POS_COLORS

def grab(fn, *a, **k):
    captured.clear(); fn(*a, **k); return "\n".join(captured)

T = ui.TOKENS
def w(path, text):
    p = OUT / path; p.parent.mkdir(parents=True, exist_ok=True); p.write_text(text, encoding="utf-8")

# ---------------- tokens.json
color_usage = {
 "primary": "Брэндийн гол өнгө: идэвхтэй улирлын шошго, табын тэмдэглэгээ, байрын баар, Streamlit-ийн primaryColor. Цагаан бичиг дээр нь 11.3:1.",
 "primary-hover": "primary товчийн hover төлөв.",
 "primary-soft": "Идэвхтэй шүүлтүүрийн chip, графикийн төрлийн шошгоны суурь; дээр нь primary бичиг 9.7:1.",
 "secondary": "Хоёрдогч, саармаг үйлдэл.",
 "accent": "Сагсны талбайн улбар шар: зөвхөн брэнд тэмдэг, sidebar-ийн идэвхтэй цэсний зураас, онцлох тоон картын дээд хүрээ. Цайвар суурь дээр бичиг болгохгүй (2.3:1) — бичигт accent-ink.",
 "accent-ink": "Улбар шар БИЧИГ (хуудасны eyebrow): bg дээр 4.9:1, surface дээр 5.3:1.",
 "accent-soft": "Онцолсон багийн мөрийн суурь (байрын жагсаалт).",
 "bg": "Хуудасны суурь (Streamlit backgroundColor). Карт, график цагаан surface-ээр дээр нь тодорно.",
 "surface": "Карт, график, хүснэгт, онооны самбарын суурь.",
 "surface-2": "Карт доторх давхар суурь: тоглогчийн үзүүлэлтийн нүд, хүснэгтийн толгой, логоны үсгэн тэмдэг.",
 "sidebar": "Sidebar ба footer-ийн гүн цэнхэр суурь; дээр нь text-inverse 13.4:1.",
 "text": "Үндсэн бичиг bg, surface, surface-2, success-soft дээр (15.9–16.6:1).",
 "text-2": "Тайлбар, lead бичиг surface, bg, surface-2 дээр (6.9–7.6:1).",
 "text-3": "Шошго, эх сурвалжийн мөр, тэнхлэгийн бичиг surface, bg, surface-2 дээр (4.9–5.5:1).",
 "text-inverse": "sidebar суурин дээрх бичиг.",
 "border": "Карт, хүснэгт, chip-ийн хүрээ (чимэглэлийн; 1.3:1 — утга агуулсан хүрээнд border-strong).",
 "border-strong": "Хоосон төлөвийн тасархай хүрээ, графикийн тэнхлэгийн шугам.",
 "success": "Амжилт, «Батлагдсан» дүгнэлт.", "success-soft": "Харьцуулах хүснэгтэд давуу талын нүд; дээр нь text (bold).",
 "warning": "Анхааруулга.", "warning-soft": "Анхааруулгын суурь; дээр нь warning 4.6:1.",
 "error": "Алдааны бичиг, тэмдэг.", "error-soft": "Алдааны төлөвийн суурь; дээр нь error 5.7:1.",
 "info": "Focus ring (2px, surface дээр 6.7:1), холбоос.", "info-soft": "Мэдээллийн суурь.",
}
order = ["primary","primary-hover","primary-soft","secondary","accent","accent-ink","accent-soft","bg","surface","surface-2","sidebar",
         "text","text-2","text-3","text-inverse","border","border-strong","success","success-soft","warning","warning-soft","error","error-soft","info","info-soft"]
assert set(order) <= set(T)
ctok = [{"name": f"mba-{k}", "value": {"light": T[k]}, "usage": color_usage[k]} for k in order]
extra = [
 ("mba-sidebar-2", "#17305A", "Sidebar доторх оролтын талбарын суурь (theme.sidebar.secondaryBackgroundColor)."),
 ("mba-sidebar-border", "#2A4675", "Sidebar ба footer доторх тусгаарлах шугам."),
 ("mba-sidebar-muted", "#9FB3D1", "Sidebar, footer дээрх хоёрдогч бичиг (7.4:1)."),
 ("mba-row-divider", "#EEF2F6", "Хүснэгт, жагсаалтын мөр хоорондын шугам."),
 ("mba-bar-track", "#E9EEF5", "Ялалтын хувийн баарын хоосон зам."),
 ("mba-badge-import-bg", "#FCEEE6", "«Гадаад» тэмдгийн суурь."), ("mba-badge-import-ink", "#9A3412", "«Гадаад» тэмдгийн бичиг (6.4:1)."),
 ("mba-badge-domestic-bg", "#E6F1F8", "«Дотоод» тэмдгийн суурь."), ("mba-badge-domestic-ink", "#075985", "«Дотоод» тэмдгийн бичиг (6.6:1)."),
 ("chart-blue", PALETTE["blue"], "Графикт ДОТООД тоглогч, «А» баг, сайн тал. Okabe–Ito."),
 ("chart-vermillion", PALETTE["vermillion"], "Графикт ГАДААД тоглогч, «Б» баг, онцолсон шугам. surface дээр 3.9:1 (тэмдэгт хангалттай)."),
 ("chart-green", PALETTE["green"], "SF байрлал, бүлгийн 3-р өнгө."), ("chart-orange", PALETTE["orange"], "PG байрлал, бүлгийн 4-р өнгө."),
 ("chart-sky", PALETTE["sky"], "SG байрлал."), ("chart-purple", PALETTE["purple"], "PF байрлал, бүлгийн 5-р өнгө."),
 ("chart-neutral", NEUTRAL, "Лавлах шугам (дундаж, 0, 50%)."), ("chart-lightest", "#D0D0D0", "Онцлоогүй багийн шугам (Elo)."),
 ("chart-grid", "#EDF1F6", "Графикийн тор."), ("chart-axis", "#C3CEDC", "Тэнхлэгийн шугам, hover хүрээ."),
]
ctok += [{"name": n, "value": {"light": v}, "usage": u} for n, v, u in extra]
tokens = {
 "name": "MBA Analytics", "version": 1,
 "meta": {"source": "local", "repo": "batdorj-s/data-visualization-3a", "paths": {"tokens": ["mba_analysis/dashboard/ui.py (TOKENS)", "mba_analysis/.streamlit/config.toml", "mba_analysis/src/palette.py", "mba_analysis/dashboard/plots.py"]}, "synced": "2026-11-22"},
 "color": {"themes": [{"id": "light", "name": "Light"}], "tokens": ctok},
 "type": {"fonts": [],
  "families": {"sans": "Inter, \"Segoe UI\", Arial, sans-serif", "mono": "\"JetBrains Mono\", ui-monospace, monospace"},
  "groups": [
   {"name": "Гарчиг", "family": "sans", "styles": [
     {"name": "page-title", "fontSize": "1.9rem", "lineHeight": 1.2, "fontWeight": 700, "letterSpacing": "-0.02em", "sample": "Лигийн тойм", "usage": "Хуудасны h1 (.mba-head h1). Утсан дээр 1.5rem."},
     {"name": "section-title", "fontSize": "1.2rem", "lineHeight": 1.3, "fontWeight": 650, "sample": "Лигийн байр", "usage": "Хэсгийн гарчиг (.mba-section h2)."},
     {"name": "chart-title", "fontSize": "15px", "lineHeight": 1.3, "fontWeight": 600, "sample": "Цөөн тоглогч лигийн онооны ихэнхийг авдаг", "usage": "Plotly графикийн гарчиг: зүүн тийш, дүгнэлт хэлбэрээр."},
     {"name": "eyebrow", "fontSize": "0.75rem", "lineHeight": 1.3, "fontWeight": 700, "letterSpacing": "0.08em", "sample": "ТОЙМ · 2025–26", "usage": "Гарчгийн дээрх хэсэг · улирал; ТОМ үсгээр, accent-ink."}]},
   {"name": "Бичвэр", "family": "sans", "styles": [
     {"name": "body", "fontSize": "15px", "lineHeight": 1.6, "fontWeight": 400, "sample": "Гадаад тоглогчид лигийн нийт онооны 38%-ийг авдаг.", "usage": "Үндсэн бичиг (Streamlit baseFontSize = 15)."},
     {"name": "lead", "fontSize": "1rem", "lineHeight": 1.55, "fontWeight": 400, "sample": "Аль баг яагаад ялж байна вэ.", "usage": "Хуудасны зорилгын өгүүлбэр, text-2, 78ch хүртэл."},
     {"name": "note", "fontSize": "0.82rem", "lineHeight": 1.5, "fontWeight": 400, "sample": "Хэрхэн унших: Багана бүр 1 тоглогч…", "usage": "Графикийн доорх тэмдэглэл."},
     {"name": "label", "fontSize": "0.78rem", "lineHeight": 1.3, "fontWeight": 600, "letterSpacing": "0.04em", "sample": "ГАДААДЫН ОНОО", "usage": "Тоон картын шошго, ТОМ үсгээр, text-3."}]},
   {"name": "Тоо", "family": "sans", "styles": [
     {"name": "stat-value", "fontSize": "1.7rem", "lineHeight": 1.2, "fontWeight": 700, "sample": "38%", "usage": "Тоон картын утга; tabular-nums."},
     {"name": "score", "fontSize": "2rem", "lineHeight": 1.1, "fontWeight": 800, "sample": "73 – 72", "usage": "Онооны самбар; ялагдсан тал text-3, 600."},
     {"name": "tick", "fontSize": "12px", "lineHeight": 1.2, "fontWeight": 400, "sample": "2025.11", "usage": "Графикийн тэнхлэгийн тоо, text-3."}]},
   {"name": "Код", "family": "mono", "styles": [
     {"name": "file-path", "fontSize": "0.74rem", "lineHeight": 1.5, "fontWeight": 400, "sample": "data/processed/players_season.csv", "usage": "Графикийн доорх датасетийн файлын зам."}]}]},
 "spacing": {"tokens": [
   {"name": "space-chip", "value": "6px", "usage": "Chip, тэмдэг хоорондын зай."},
   {"name": "space-2", "value": "8px", "usage": "Багийн лого ба нэрийн зай; утсан дээр тоон картын зай."},
   {"name": "space-3", "value": "12px", "usage": "Тоон картын эгнээний зай, онооны самбарын зай."},
   {"name": "space-4", "value": "14px", "usage": "Карт, мөрийн хэвтээ дотор зай."},
   {"name": "space-5", "value": "18px", "usage": "Гол дүгнэлт, онооны самбарын дотор зай."},
   {"name": "space-6", "value": "24px", "usage": "Footer-ийн баганы зай, толгойн хэсгийн зай."}]},
 "radius": {"tokens": [
   {"name": "mba-radius", "value": "10px", "usage": "Карт, график, хүснэгт, footer (Streamlit baseRadius medium)."},
   {"name": "mba-radius-sm", "value": "6px", "usage": "Dataframe."},
   {"name": "radius-logo", "value": "8px", "usage": "Багийн логоны дөрвөлжин."},
   {"name": "radius-tag", "value": "4px", "usage": "Графикийн төрлийн шошго, файлын зам."},
   {"name": "radius-pill", "value": "999px", "usage": "Chip, тэмдэг, улирлын шошго, баар."}]},
 "shadow": {"tokens": [{"name": "mba-shadow", "value": T["shadow"], "usage": "Бүх карт, график, хүснэгтэнд нэг л сүүдэр."}]},
}
w("tokens.json", json.dumps(tokens, ensure_ascii=False, indent=1))

# tokens.css (анхны хувилбар; page-д хадгалахад дахин үүснэ)
css = ["/* MBA Analytics — generated from tokens.json */", ':root, [data-theme="light"] {']
css += [f"  --{t['name']}: {t['value']['light']};" for t in ctok] + [f"  --mba-shadow: {T['shadow']};", "}", ":root {"]
css += [f"  --{t['name']}: {t['value']};" for fam in ("spacing", "radius") for t in tokens[fam]["tokens"]]
css += [f"  --font-{k}: {v};" for k, v in tokens["type"]["families"].items()] + ["}"]
for g in tokens["type"]["groups"]:
    for s_ in g["styles"]:
        css.append(f".{s_['name']} {{ font-family: var(--font-{g['family']}); font-size: {s_['fontSize']}; line-height: {s_['lineHeight']}; "
                   f"font-weight: {s_['fontWeight']};" + (f" letter-spacing: {s_['letterSpacing']};" if 'letterSpacing' in s_ else "") + " }")
w("tokens.css", "\n".join(css) + "\n")

# ---------------- bundle.css: ui.CSS-ээс Streamlit-ийн сонгогчгүй дүрмүүд
raw = re.sub(r"</?style>", "", ui.CSS)
def rules(text):
    out, i, depth, start = [], 0, 0, 0
    while i < len(text):
        c = text[i]
        if c == "{": depth += 1
        elif c == "}":
            depth -= 1
            if depth == 0: out.append(text[start:i + 1].strip()); start = i + 1
        i += 1
    return out
keep = []
for r in rules(raw):
    head = r.split("{", 1)[0]
    if head.strip() == ":root" or "data-testid" in head or "data-baseweb" in head:
        continue
    if head.strip().startswith("@media") and "max-width" in head:
        body = r[r.index("{") + 1:r.rindex("}")]
        inner = [x for x in rules(body) if "data-testid" not in x.split("{", 1)[0]]
        r = head.strip() + " {\n  " + "\n  ".join(inner) + "\n}"
    keep.append(r)
bundle = ("@import url(\"https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&family=JetBrains+Mono:wght@400;500&display=swap\");\n"
          "/* MBA Analytics — бүрэлдэхүүний загвар, dashboard/ui.py-ийн CSS-ээс (Streamlit-ийн сонгогчгүй) */\n"
          ":root { --mba-font: var(--font-sans); }\n"
          "body { margin: 0; font-family: var(--font-sans); font-size: 15px; line-height: 1.6; color: var(--mba-text); background: var(--mba-bg); }\n"
          ".ds-frame { padding: 16px; background: var(--mba-bg); }\n"
          "h1, h2, h4 { font-family: var(--font-sans); }\n" + "\n".join(keep) + "\n")
w("components/bundle.css", bundle)

# ---------------- бүрэлдэхүүнүүд
def card(name, group, height, markup, readme, subtitle=None):
    marker = f'<!-- @dsCard group="{group}" height={height}' + (f' subtitle="{subtitle}"' if subtitle else "") + " -->"
    w(f"components/{name}/preview.html", marker + '\n<div class="ds-frame">\n' + markup + "\n</div>\n")
    w(f"components/{name}/README.md", readme.strip() + "\n")

N = None
card("PageHeader", "Бүтэц", 190, grab(ui.page_header, "Лигийн тойм", "Монголын сагсан бөмбөгийн дээд лигийн 2025–26 улирлыг нэг дороос: хэн оноо авдаг, аль баг хүчтэй, үр дүн хэр найдвартай вэ.", eyebrow="Тойм · 2025–26"), """
Хуудас бүрийн толгой: зүүн талд eyebrow, гарчиг, нэг өгүүлбэр зорилго; баруун талд идэвхтэй улирал ба дата шинэчилсэн огноо.

- `page_header(title, lead, eyebrow)` — хуудасны эхний мөр болгон НЭГ удаа дуудна.
- Eyebrow = «Хэсэг · улирал», `accent-ink`, ТОМ үсгээр. Гарчиг `page-title`, зорилго `lead` (`mba-text-2`).
- Улирлын шошго `mba-primary` дээр цагаан; 2026–27 (явагдаж буй) бол ногоон цэгтэй «явагдаж буй».
- Зорилгын өгүүлбэр хуудас юуг хариулахыг хэлнэ; товчлол (TS%, CI) бичихгүй.
""")
card("Section", "Бүтэц", 110, grab(ui.section, "Лигийн байр", "Үндсэн шатны ялалт–хожигдол, ялалтын хувиар."), """
Хэсгийн гарчиг ба нэг мөр тайлбар; `st.subheader`-ийн оронд бүх хуудсанд.

- `section(title, desc=None)` — гарчиг `section-title`, тайлбар `mba-text-3`.
- Тайлбар нь асуулт эсвэл юу харуулахыг хэлнэ («Лигийн онооны ихэнхийг хэдэн тоглогч авдаг вэ?»).
""")
card("FilterChips", "Өгөгдөл", 110, grab(ui.filter_summary, types.SimpleNamespace(season="2025-2026", teams=["XAC Broncos"], positions=[], import_status="Бүгд", min_gp=5, highlight_team="SG Apes")), """
Идэвхтэй шүүлтүүрийн chip-үүд: хэрэглэгч юуг шүүснээ санах шаардлагагүй.

- `filter_summary(f)` — page_header-ийн дараа.
- Анхдагчаас өөрчилсөн шүүлтүүр `mba-chip--active` (`mba-primary-soft` суурь, `mba-primary` бичиг); бусад нь цагаан.
""")
card("Findings", "Өгөгдөл", 170, grab(ui.findings, ["Гадаад тоглогчид лигийн нийт онооны **38%**-ийг авдаг (бодит хувь 37%–40% хооронд байх магадлалтай).",
     "Хамгийн их оноо авсан **69** тоглогч (нийт тоглогчдын 41%) л лигийн онооны 80%-ийг авдаг.",
     "Одоогийн хамгийн хүчтэй баг: **XAC Broncos** (хүчний оноо 1623; 1500 = дундаж)."]), """
«Гол дүгнэлт» — хуудасны 2–3 гол олдвор, датагаас тооцсон тоогоор.

- `findings(items)` — `**тод**` markdown-ийг дэмжинэ; бусдыг escape хийнэ.
- 3 мөрөөс илүүгүй; мөр бүр нэг тоо, нэг дүгнэлт. Тодорхой бус байдал байвал хүрээг нь бичнэ.
- Зүүн талын `mba-primary` зураас нь хуудсан дээрх ганц ийм тэмдэг; өөр картад давтахгүй.
""")
card("StatCards", "Өгөгдөл", 150, grab(ui.stat_cards, [("Тоглолт", "172", "үндсэн шат ба плей-офф"), ("Тоглогч (5+ тоглолт)", "147", "34 гадаад · 113 дотоод"),
     ("Гадаадын оноо", "38%", "95% хүрээ 37%–40%"), ("Тоглолтын оноо", "164", "хоёр баг нийлээд, дунджаар"),
     ("Тэргүүлэгч", "XAC Broncos", "18–9, 67% ялалт", None, ("XAC Broncos", None))]), """
Тоон картын эгнээ: шошго, утга, нэг мөр тайлбар; хүсвэл багийн логотой.

- `stat_cards([(шошго, утга, тайлбар, tooltip, (баг, лого_url))])` — сүүлийн гурав заавал биш.
- Шошго `label`, утга `stat-value` (tabular-nums), тайлбар `mba-text-3`.
- Сүлжээ `minmax(150px, 1fr)`: компьютер дээр 5 нэг мөрөнд, утсан дээр 2 багана, ганц үлдсэн карт бүтэн өргөнөөр.
- Хуудсын эхэнд НЭГ эгнээ; утга нь хуудасны гол асуултад хамаатай тоо байх ёстой.
""")
card("TeamLogo", "Багийн дүрслэл", 120, '<div style="display:flex;gap:16px;align-items:center;flex-wrap:wrap">'
     + "".join(ui.team_logo(t, None, s) for t, s in [("BCH Knights", 52), ("Khan Falcons", 44), ("XAC Broncos", 34), ("SG Apes", 24)])
     + '<span style="width:1px;height:40px;background:var(--mba-border)"></span>'
     + "".join(ui.team_label(t, None) for t in ["Selenge Bodons", "Erdenet Miners"]) + "</div>", """
Багийн лого: тогтмол дөрвөлжин, `object-fit: contain`, сунахгүй; лого алга эсвэл ачаалагдахгүй бол багийн нэрийн эхний үсэг.

- `team_logo(team, url, size)` — 24 (жагсаалт), 34 (тоон карт), 44 (онооны самбар, тоглогчийн карт), 52 (багийн профайл) px.
- `team_label(team, url)` — лого + нэр, хүснэгт ба жагсаалтад.
- URL нь MBA-ийн албан ёсны сайтын тоглолтын хуудсан дахь `schema.org SportsTeam` бичлэгээс (`src/team_logos.py`); dashboard серверт 128 px болгож кэшилнэ. Зургийг repo, design system-д хуулахгүй — энэ жишээ зөвхөн үсгэн тэмдгийг харуулна.
- Үсгэн тэмдэг: товчилсон нэр (BCH, XAC, SG) байвал тэр, үгүй бол эхний хоёр үгийн эхний үсэг (KF). Лого шинээр зурж, «загварчилж» хэзээ ч болохгүй.
""")
card("TeamHeader", "Багийн дүрслэл", 120, grab(ui.team_header, "XAC Broncos", None, "Улаанбаатар · 2025–26 улирал, үндсэн шат",
     [("Байр", "1/10"), ("Я–Х", "18–9"), ("Ялалт", "67%"), ("Онооны зөрүү", "+6.7"), ("Хүчний оноо", "1623")]), """
Багийн профайлын толгой: 52 px лого, нэр, хот, баруун талд гол тоонууд.

- `team_header(team, url, meta, stats=[(шошго, утга)])` — Багууд хуудасны профайл, ML-ийн ялалтын тооцоолуурт хоёуланг нь зэрэгцүүлж.
- Тоо 5-аас ихгүй; утсан дээр тоонууд нэрийн доор шилжинэ.
""")
card("Scoreboard", "Багийн дүрслэл", 150, grab(ui.scoreboard, "Selenge Bodons", "Erdenet Miners", 73, 72, {},
     "2026-03-09 · тэргүүлэгч 24 удаа солигдсон · Selenge Bodons хамгийн ихдээ 6, Erdenet Miners 5 оноогоор тэргүүлсэн"), """
Нэг тоглолтын онооны самбар: гэрийн баг зүүн, зочин баруун, ялагдсан талын оноо бүдэг.

- `scoreboard(home, away, home_pts, away_pts, logos, meta)` — «Тоглолт минут тутам» графикийн дээр.
- Оноо `score` (tabular-nums). Доорх мөрөнд огноо ба тоглолтын товч тайлбар.
""")
card("StandingsBoard", "Өгөгдөл", 300, grab(ui.standings_board, [(1, "XAC Broncos", 18, 9, 0.667), (2, "SG Apes", 18, 9, 0.667), (3, "BCH Knights", 17, 10, 0.63),
     (4, "Erdenet Miners", 16, 11, 0.593), (5, "Selenge Bodons", 15, 12, 0.556)], {}, "SG Apes"), """
Лигийн байрын товч жагсаалт: байр, логотой нэр, ялалт–хожигдол, ялалтын хувийн баар.

- `standings_board(rows, logos, highlight)` — rows = (байр, баг, ялалт, хожигдол, хувь).
- Онцолсон баг `mba-accent-soft` мөр. Баар `mba-primary` дээр `mba-bar-track`.
- Container query: 380 px-ээс нарийн бол баар нуугдаж зөвхөн хувь үлдэнэ.
""")
card("CompareTable", "Өгөгдөл", 260, grab(ui.compare_table, "XAC Broncos", "SG Apes", [
     ("Авсан оноо", "тоглолтын дундаж", 82.7, 81.7, "{:.1f}", True), ("Алдсан оноо", "бага нь сайн", 78.6, 82.1, "{:.1f}", False),
     ("Оновч", "3 оноог 1.5 дахин тооцсон", 0.524, 0.515, "{:.1%}", True), ("Бөмбөг алдалт", "довтолгооны хэдэн хувьд, бага нь сайн", 0.193, 0.199, "{:.1%}", False)], {}), """
Хоёр багийн харьцуулалт: үзүүлэлт бүрт давуу талыг `mba-success-soft` нүд, тод бичгээр.

- `compare_table(t1, t2, rows, logos)` — rows = (үзүүлэлт, тайлбар, утга1, утга2, формат, их_нь_сайн).
- «Бага нь сайн» үзүүлэлтэд (алдсан оноо, бөмбөг алдалт) `их_нь_сайн=False`; тайлбарт заавал бичнэ.
- Өнгө дангаараа утга илэрхийлэхгүй: давуу нүд тод бичигтэй.
""")
card("PlayerCard", "Тоглогч", 230, grab(ui.player_header, "BYRON Wesley", "BurenScore Mongolians", None, "SF", True, "Тоглолт зохион байгуулагч")
     + grab(ui.player_stats, [("Оноо / тоглолт", "27.9", "Хүрээ 23.7–31.6"), ("Шидэлтийн оновч", "59%", "Хүрээ 56%–63%"), ("Самбар / тоглолт", "5.4", None), ("Дамжуулалт / тоглолт", "3.8", None)]), """
Тоглогчийн карт: багийн лого, нэр, баг · байрлал · гадаад/дотоод · хэв маяг тэмдэг, 4 гол үзүүлэлт.

- `player_header(name, team, logo, position, is_import, style)` + `player_stats([(шошго, утга, хүрээ)])`.
- Гадаад/дотоод тэмдгийн өнгө графиктай нийцнэ: гадаад улбар (`mba-badge-import-*`), дотоод цэнхэр (`mba-badge-domestic-*`), бичигтэй.
- Хүрээ (95%) нь «Магадлалтай хүрээ» асаалттай үед л.
""")
card("ChartNote", "Өгөгдөл", 130, '<div style="height:28px;border:1px dashed var(--mba-border-strong);border-radius:var(--mba-radius);margin-bottom:12px;display:grid;place-items:center;color:var(--mba-text-3);font-size:.78rem">график</div>'
     + grab(ui.chart_note, "Багана бүр 1 тоглогчийн улирлын нийт оноо, ихээс нь эрэмбэлсэн (улаан-улбар = гадаад, цэнхэр = дотоод).",
            "тоглолт бүрийн хайрцаг оноо, 2025–26 улирлын үндсэн шат, 170 тоглогч.", kind="Парето график (оноогоор эрэмбэлсэн багана + нийлбэр хувийн шугам)", files=["player_games"]), """
График, хүснэгт БҮРИЙН доор: төрлийн шошго, «Хэрхэн унших», саарлаар дата ба файлын зам.

- `chart_note(how, data, kind=..., files=[DATASETS-ийн түлхүүр])` — `show_chart`-ийн дараа шууд. Тест шалгадаг.
- `kind` = графикийн төрлийг монголоор + хаалтанд англиар («Цэгэн график (scatter plot)»).
- `how` = хэрхэн унших 1–3 өгүүлбэр; өнгө бүр юу гэсэн үг болохыг бичнэ.
- `data` = юуны дата, хэдэн ажиглалт; `files` = `data/processed/...` эсвэл `reports/...` файл.
""")
card("States", "Хариу", 170, grab(ui.empty_state, "Сонгосон шүүлтүүрт тохирох өгөгдөл алга", "Зүүн талын «Шүүлтүүрийг цэвэрлэх» товчийг дарж эсвэл тоглолтын доод хязгаарыг бууруулна уу.")
     + '<div style="height:12px"></div>' + grab(ui.error_state, "Энэ хэсгийг харуулах үед алдаа гарлаа", "Шүүлтүүрээ өөрчлөх эсвэл хуудсыг дахин ачаалж үзнэ үү."), """
Хоосон ба алдааны төлөв.

- `empty_state(title, text)` — шүүлтүүрт дата алга үед; text нь яаж засахыг хэлнэ. `role="status"`.
- `error_state(title, text)` — хуудас алдаа өгвөл app.py барьж харуулна, техникийн дэлгэрэнгүй нээгддэг хэсэгт. `role="alert"`.
- Ачаалж буй төлөв: `@st.cache_data(show_spinner="Өгөгдөл ачаалж байна…")`.
""")
card("Footer", "Бүтэц", 96, grab(ui.footer), """
Бүх хуудасны доорх нэг мөр footer: «© 2026 MBA Analytics».

- `footer()` — app.py-д `nav.run()`-ийн дараа нэг удаа; хуудас бүрт дуудахгүй.
- Зөвхөн энэ мөр: эх сурвалж, төслийн мэдээлэл, холбоос нэмэхгүй (эх сурвалж график бүрийн доорх `ChartNote` ба «Тухай» хуудсанд).
- Дээрээ `mba-border` зураас, `mba-text-3` бичиг, голлуулсан.
""")

print("ok", sorted(p.name for p in (OUT / "components").iterdir()))
