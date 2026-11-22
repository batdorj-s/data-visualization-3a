"""MBA Analytics — дизайны систем ба дахин ашиглах UI хэсгүүд (лекц 10–11).

Токен (өнгө, зай, фонт) нэг л газар: TOKENS → CSS хувьсагч (--mba-*). .streamlit/config.toml ижил утгатай.
Хэсгүүд:
- page_header: хуудас юуг хариулах вэ (зорилгыг ойлгох)
- findings: гол дүгнэлтийг дээд хэсэгт
- stat_cards: тоон картын эгнээ (дэлгэцийн өргөнд тааран мөр солино)
- section: хэсгийн гарчиг + тайлбар
- team_logo / team_label / team_header / scoreboard: багийн логотой дүрслэл (логогүй бол үсгэн тэмдэг)
- standings_board: лигийн байрын товч жагсаалт
- compare_table: хоёр багийн харьцуулалт
- chart_note: график бүрийн доор төрөл, «хэрхэн унших», ямар дата, ямар файлаас
- empty_state / error_state: хоосон ба алдааны төлөв
- filter_summary: идэвхтэй шүүлтүүр
"""

import html
from collections.abc import Sequence

import streamlit as st

TOKENS = {
    # брэнд
    "primary": "#1B3A6B", "primary-hover": "#142C52", "primary-soft": "#E8EEF7",
    "secondary": "#475569", "accent": "#F08A3C", "accent-ink": "#B9480C", "accent-soft": "#FDEBDD",
    # гадаргуу
    "bg": "#F5F7FA", "surface": "#FFFFFF", "surface-2": "#F1F4F8", "sidebar": "#0F2240",
    # текст
    "text": "#0F172A", "text-2": "#475569", "text-3": "#5B6B7F", "text-inverse": "#E6ECF5",
    # хүрээ
    "border": "#DCE3EC", "border-strong": "#C3CEDC",
    # төлөв
    "success": "#15803D", "success-soft": "#E7F5EC", "warning": "#B45309", "warning-soft": "#FDF3E2",
    "error": "#B91C1C", "error-soft": "#FCECEC", "info": "#1D4ED8", "info-soft": "#E8F0FE",
    # хэмжээ
    "radius": "10px", "radius-sm": "6px", "shadow": "0 1px 2px rgba(15,23,42,.06), 0 1px 3px rgba(15,23,42,.04)",
}
FONT_STACK = "Inter, 'Segoe UI', Arial, sans-serif"

_VARS = "\n".join(f"  --mba-{k}: {v};" for k, v in TOKENS.items())
CSS = f"""
<style>
:root {{
{_VARS}
  --mba-font: {FONT_STACK};
}}
/* ---- суурь ---- */
[data-testid="stDecoration"] {{ display: none; }}
[data-testid="stMainBlockContainer"] {{ padding-top: 2.2rem; padding-bottom: 4rem; max-width: 1440px; }}
[data-testid="stMetricValue"], [data-testid="stDataFrame"], .mba-num {{ font-variant-numeric: tabular-nums; }}
[data-testid="stMarkdownContainer"] p, [data-testid="stMarkdownContainer"] li {{ line-height: 1.6; }}
[data-testid="stCaptionContainer"] {{ line-height: 1.5; color: var(--mba-text-3); }}
h2, h3 {{ letter-spacing: -0.01em; }}
[data-testid="stHeading"] h3 {{ padding-top: .6rem; }}
a:focus-visible, button:focus-visible, [role="tab"]:focus-visible {{
  outline: 2px solid var(--mba-info); outline-offset: 2px; border-radius: 4px; }}

/* ---- карт: хүрээтэй container, график, хүснэгт ---- */
[data-testid="stVerticalBlockBorderWrapper"], div[class*="st-key-mba-card"] {{
  background: var(--mba-surface); border-radius: var(--mba-radius); }}
[data-testid="stPlotlyChart"] {{
  background: var(--mba-surface); border: 1px solid var(--mba-border); border-radius: var(--mba-radius);
  padding: 6px 4px 2px 4px; box-shadow: var(--mba-shadow); }}
[data-testid="stDataFrame"] {{ border-radius: var(--mba-radius-sm); }}

/* ---- табууд ---- */
[data-baseweb="tab-list"] {{ gap: 4px; border-bottom: 1px solid var(--mba-border); }}
[data-baseweb="tab"] {{ padding: 8px 14px; border-radius: 8px 8px 0 0; font-weight: 500; color: var(--mba-text-2); }}
[data-baseweb="tab"]:hover {{ background: var(--mba-surface-2); color: var(--mba-text); }}
[data-baseweb="tab"][aria-selected="true"] {{ color: var(--mba-primary); font-weight: 600; }}
[data-baseweb="tab-highlight"] {{ background-color: var(--mba-primary) !important; height: 3px; }}

/* ---- sidebar ---- */
[data-testid="stSidebar"] {{ border-right: 1px solid #0B1A33; }}
[data-testid="stSidebarNav"] a[aria-current="page"] {{ box-shadow: inset 3px 0 0 var(--mba-accent); }}
[data-testid="stSidebarNavSeparator"] {{ border-color: #2A4675; }}
[data-testid="stSidebar"] [data-testid="stCaptionContainer"], [data-testid="stSidebar"] [data-testid="stCaptionContainer"] p {{ color: #9FB3D1; }}
[data-testid="stSidebar"] hr {{ border-color: #2A4675; }}
.mba-side-title {{ font-size: .72rem; font-weight: 700; letter-spacing: .08em; text-transform: uppercase;
  color: #9FB3D1; margin: .4rem 0 .2rem 0; }}

/* ---- хуудасны толгой ---- */
.mba-head {{ margin: 0 0 1.1rem 0; }}
.mba-head__main {{ min-width: 0; flex: 1 1 420px; }}
.mba-eyebrow {{ font-size: .75rem; font-weight: 700; letter-spacing: .08em; text-transform: uppercase;
  color: var(--mba-accent-ink); margin-bottom: .35rem; }}
.mba-head h1 {{ font-size: 1.9rem; font-weight: 700; color: var(--mba-text); margin: 0; padding: 0; letter-spacing: -0.02em; }}
.mba-lead {{ font-size: 1rem; color: var(--mba-text-2); max-width: 78ch; margin: .45rem 0 0 0; line-height: 1.55; }}
.mba-chips {{ display: flex; flex-wrap: wrap; gap: 6px; margin: .2rem 0 .4rem 0; }}
.mba-chip {{ display: inline-flex; align-items: center; gap: 6px; padding: 3px 10px; border-radius: 999px;
  background: var(--mba-surface); border: 1px solid var(--mba-border); color: var(--mba-text-2); font-size: .8rem; }}
.mba-chip b {{ color: var(--mba-text); font-weight: 600; }}
.mba-chip--active {{ background: var(--mba-primary-soft); border-color: #C9D6EA; color: var(--mba-primary); }}

.mba-head {{ display: flex; gap: 24px; align-items: flex-end; justify-content: space-between; flex-wrap: wrap;
  padding-bottom: 1rem; border-bottom: 1px solid var(--mba-border); }}
.mba-head__meta {{ display: flex; flex-direction: column; align-items: flex-end; gap: 6px; font-size: .8rem; color: var(--mba-text-3); }}
.mba-pill {{ display: inline-flex; align-items: center; gap: 6px; padding: 4px 10px; border-radius: 999px; font-weight: 600;
  background: var(--mba-primary); color: #fff; font-size: .78rem; }}
.mba-pill--live::before {{ content: ""; width: 7px; height: 7px; border-radius: 50%; background: #4ADE80; }}
.mba-fresh {{ display: inline-flex; align-items: center; gap: 6px; }}

/* ---- footer ---- */
.mba-footer {{ margin-top: 3rem; padding: 14px 0 6px 0; border-top: 1px solid var(--mba-border); color: var(--mba-text-3);
  font-size: .8rem; text-align: center; }}

/* ---- expander ---- */
[data-testid="stExpander"] details {{ background: var(--mba-surface); border: 1px solid var(--mba-border); border-radius: var(--mba-radius);
  box-shadow: var(--mba-shadow); }}
[data-testid="stExpander"] summary {{ font-weight: 600; color: var(--mba-text); }}
[data-testid="stExpander"] summary:hover {{ color: var(--mba-primary); }}

/* ---- хэсгийн гарчиг ---- */
.mba-section {{ margin: 1.6rem 0 .6rem 0; }}
.mba-section h2 {{ font-size: 1.2rem; font-weight: 650; color: var(--mba-text); margin: 0; padding: 0; }}
.mba-section p {{ font-size: .9rem; color: var(--mba-text-3); margin: .2rem 0 0 0; max-width: 90ch; }}

/* ---- гол дүгнэлт ---- */
.mba-findings {{ background: var(--mba-surface); border: 1px solid var(--mba-border); border-left: 4px solid var(--mba-primary);
  border-radius: var(--mba-radius); padding: 14px 18px; box-shadow: var(--mba-shadow); margin-bottom: .6rem; }}
.mba-findings h4 {{ margin: 0 0 6px 0; padding: 0; font-size: .78rem; font-weight: 700; letter-spacing: .06em;
  text-transform: uppercase; color: var(--mba-primary); }}
.mba-findings ol {{ margin: 0; padding-left: 1.2rem; }}
.mba-findings li {{ margin: 4px 0; line-height: 1.55; color: var(--mba-text); }}
.mba-findings li::marker {{ color: var(--mba-text-3); font-weight: 600; }}

/* ---- тоон карт ---- */
.mba-stats {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(150px, 1fr)); gap: 12px; margin: .2rem 0 .8rem 0; }}
.mba-stat {{ background: var(--mba-surface); border: 1px solid var(--mba-border); border-radius: var(--mba-radius);
  padding: 14px 16px; box-shadow: var(--mba-shadow); min-width: 0; }}
.mba-stat__label {{ font-size: .78rem; font-weight: 600; color: var(--mba-text-3); text-transform: uppercase; letter-spacing: .04em; }}
.mba-stat__value {{ font-size: 1.7rem; font-weight: 700; color: var(--mba-text); line-height: 1.2; margin-top: 4px;
  font-variant-numeric: tabular-nums; overflow-wrap: anywhere; }}
.mba-stat__sub {{ font-size: .8rem; color: var(--mba-text-3); margin-top: 2px; }}
.mba-stat--accent {{ border-top: 3px solid var(--mba-accent); }}
.mba-stat__row {{ display: flex; align-items: center; gap: 10px; margin-top: 4px; min-width: 0; }}
.mba-stat__row .mba-stat__value {{ margin-top: 0; font-size: 1.25rem; line-height: 1.25; }}

/* ---- багийн лого ---- */
.mba-logo {{ position: relative; display: inline-grid; place-items: center; flex: none; border-radius: 8px;
  background: var(--mba-surface-2); border: 1px solid var(--mba-border); overflow: hidden; color: var(--mba-text-2);
  font-weight: 700; letter-spacing: .02em; vertical-align: middle; }}
.mba-logo img {{ position: absolute; inset: 0; width: 100%; height: 100%; object-fit: contain; padding: 8%;
  background: #fff; }}
.mba-team {{ display: inline-flex; align-items: center; gap: 8px; font-weight: 600; color: var(--mba-text); min-width: 0; }}
.mba-team span.mba-team__name {{ min-width: 0; overflow-wrap: break-word; line-height: 1.25; }}
.mba-teamhead {{ display: flex; align-items: center; gap: 14px; padding: 12px 14px; background: var(--mba-surface);
  border: 1px solid var(--mba-border); border-radius: var(--mba-radius); box-shadow: var(--mba-shadow); }}
.mba-teamhead__name {{ font-size: 1.15rem; font-weight: 700; color: var(--mba-text); line-height: 1.25; }}
.mba-teamhead__meta {{ font-size: .85rem; color: var(--mba-text-3); margin-top: 2px; }}
.mba-teamhead__stats {{ margin-left: auto; display: flex; gap: 18px; flex-wrap: wrap; justify-content: flex-end; }}
.mba-kv {{ text-align: right; }}
.mba-kv b {{ display: block; font-size: 1.15rem; color: var(--mba-text); font-variant-numeric: tabular-nums; }}
.mba-kv span {{ font-size: .72rem; color: var(--mba-text-3); text-transform: uppercase; letter-spacing: .04em; }}

/* ---- онооны самбар ---- */
.mba-score {{ display: grid; grid-template-columns: 1fr auto 1fr; align-items: center; gap: 12px; padding: 14px 18px;
  background: var(--mba-surface); border: 1px solid var(--mba-border); border-radius: var(--mba-radius); box-shadow: var(--mba-shadow); }}
.mba-score__side {{ display: flex; align-items: center; gap: 10px; min-width: 0; }}
.mba-score__side--away {{ justify-content: flex-end; text-align: right; }}
.mba-score__team {{ font-weight: 700; color: var(--mba-text); line-height: 1.2; }}
.mba-score__role {{ font-size: .72rem; color: var(--mba-text-3); text-transform: uppercase; letter-spacing: .05em; }}
.mba-score__pts {{ font-size: 2rem; font-weight: 800; color: var(--mba-text); font-variant-numeric: tabular-nums; white-space: nowrap; }}
.mba-score__pts .lose {{ color: var(--mba-text-3); font-weight: 600; }}
.mba-score__meta {{ grid-column: 1 / -1; text-align: center; font-size: .82rem; color: var(--mba-text-3); }}

/* ---- лигийн байр ---- */
.mba-board {{ background: var(--mba-surface); border: 1px solid var(--mba-border); border-radius: var(--mba-radius);
  box-shadow: var(--mba-shadow); overflow: hidden; container-type: inline-size; }}
.mba-board__head, .mba-board__row {{ display: grid; grid-template-columns: 24px minmax(0, 1fr) auto 104px; align-items: center;
  gap: 10px; padding: 8px 14px; }}
.mba-board__head {{ font-size: .72rem; font-weight: 700; color: var(--mba-text-3); text-transform: uppercase; letter-spacing: .05em;
  background: var(--mba-surface-2); border-bottom: 1px solid var(--mba-border); }}
.mba-board__row {{ border-bottom: 1px solid #EEF2F6; font-size: .92rem; }}
.mba-board__row:last-child {{ border-bottom: 0; }}
.mba-board__row:hover {{ background: #F8FAFC; }}
.mba-board__row--hl {{ background: var(--mba-accent-soft); }}
.mba-board__rank {{ color: var(--mba-text-3); font-weight: 600; text-align: right; font-variant-numeric: tabular-nums; }}
.mba-board__rec {{ text-align: right; font-variant-numeric: tabular-nums; color: var(--mba-text-2); }}
.mba-bar {{ position: relative; height: 8px; border-radius: 999px; background: #E9EEF5; }}
.mba-bar > i {{ position: absolute; left: 0; top: 0; bottom: 0; border-radius: 999px; background: var(--mba-primary); }}
@container (max-width: 380px) {{
  .mba-board__head, .mba-board__row {{ grid-template-columns: 20px minmax(0, 1fr) auto 40px; gap: 8px; padding: 8px 10px; }}
  .mba-board__pct .mba-bar {{ display: none; }}
  .mba-board__pct {{ grid-template-columns: 1fr; }}
}}
.mba-board__pct {{ display: grid; grid-template-columns: 1fr 34px; gap: 6px; align-items: center; font-variant-numeric: tabular-nums;
  font-size: .82rem; color: var(--mba-text-2); text-align: right; }}

/* ---- харьцуулалт ---- */
.mba-cmp {{ width: 100%; border-collapse: separate; border-spacing: 0; background: var(--mba-surface);
  border: 1px solid var(--mba-border); border-radius: var(--mba-radius); overflow: hidden; box-shadow: var(--mba-shadow); }}
.mba-cmp th, .mba-cmp td {{ padding: 9px 14px; border-bottom: 1px solid #EEF2F6; font-size: .92rem; }}
.mba-cmp tr:last-child td {{ border-bottom: 0; }}
.mba-cmp thead th {{ background: var(--mba-surface-2); font-weight: 600; color: var(--mba-text); text-align: center; }}
.mba-cmp thead th:first-child {{ text-align: left; color: var(--mba-text-3); font-size: .75rem; text-transform: uppercase; letter-spacing: .05em; }}
.mba-cmp td {{ text-align: center; font-variant-numeric: tabular-nums; color: var(--mba-text-2); }}
.mba-cmp td:first-child {{ text-align: left; color: var(--mba-text); }}
.mba-cmp td.win {{ color: var(--mba-text); font-weight: 700; background: var(--mba-success-soft); }}
.mba-cmp small {{ display: block; color: var(--mba-text-3); font-size: .75rem; }}

/* ---- графикийн тэмдэглэл ---- */
.mba-note {{ font-size: .82rem; line-height: 1.5; color: var(--mba-text-2); margin: -.35rem 2px .9rem 2px; }}
.mba-note__kind {{ display: inline-block; font-weight: 600; color: var(--mba-primary); background: var(--mba-primary-soft);
  border-radius: 4px; padding: 0 6px; margin-right: 6px; font-size: .75rem; }}
.mba-note__src {{ color: var(--mba-text-3); margin-top: 3px; font-size: .78rem; }}
.mba-note code, .mba-source code {{ color: var(--mba-text-2); background: var(--mba-surface-2); padding: 0 4px; border-radius: 4px;
  font-size: .74rem; }}
.mba-source {{ color: var(--mba-text-3); font-size: .78rem; }}

/* ---- төлөв ---- */
.mba-state {{ display: flex; gap: 14px; align-items: flex-start; padding: 18px 20px; border-radius: var(--mba-radius);
  border: 1px dashed var(--mba-border-strong); background: var(--mba-surface); }}
.mba-state__icon {{ font-size: 1.4rem; line-height: 1; }}
.mba-state__title {{ font-weight: 650; color: var(--mba-text); }}
.mba-state__text {{ color: var(--mba-text-2); font-size: .92rem; margin-top: 2px; }}
.mba-state--error {{ border-style: solid; border-color: #F3C7C7; background: var(--mba-error-soft); }}

/* ---- тоглогчийн карт ---- */
.mba-player {{ display: flex; gap: 12px; align-items: flex-start; }}
.mba-player__name {{ font-size: 1.15rem; font-weight: 700; color: var(--mba-text); line-height: 1.25; }}
.mba-player__meta {{ display: flex; flex-wrap: wrap; gap: 6px; margin-top: 6px; }}
.mba-badge {{ display: inline-block; padding: 1px 8px; border-radius: 999px; font-size: .75rem; font-weight: 600;
  background: var(--mba-surface-2); color: var(--mba-text-2); border: 1px solid var(--mba-border); }}
.mba-badge--import {{ background: #FCEEE6; color: #9A3412; border-color: #F6D3BF; }}
.mba-badge--domestic {{ background: #E6F1F8; color: #075985; border-color: #C5DDEC; }}
.mba-pstats {{ display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 8px; margin-top: 12px; }}
.mba-pstat {{ background: var(--mba-surface-2); border-radius: 8px; padding: 8px 10px; }}
.mba-pstat span {{ display: block; font-size: .72rem; color: var(--mba-text-3); text-transform: uppercase; letter-spacing: .04em; }}
.mba-pstat b {{ font-size: 1.35rem; color: var(--mba-text); font-variant-numeric: tabular-nums; }}
.mba-pstat small {{ display: block; color: var(--mba-text-3); font-size: .74rem; }}

@media (max-width: 640px) {{
  [data-testid="stMainBlockContainer"] {{ padding-left: 1rem; padding-right: 1rem; padding-top: 1.2rem; }}
  .mba-head h1 {{ font-size: 1.5rem; }}
  .mba-head__meta {{ align-items: flex-start; }}
  .mba-stats {{ grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 8px; }}
  .mba-stat {{ padding: 10px 12px; }}
  .mba-stat:last-child:nth-child(odd) {{ grid-column: 1 / -1; }}
  .mba-stat__value {{ font-size: 1.3rem; }}
  .mba-teamhead {{ flex-wrap: wrap; }}
  .mba-teamhead__stats {{ margin-left: 0; width: 100%; justify-content: flex-start; }}
  .mba-kv {{ text-align: left; }}
  .mba-score {{ grid-template-columns: 1fr; text-align: center; }}
  .mba-score__side, .mba-score__side--away {{ justify-content: center; text-align: center; }}
}}
@media (prefers-reduced-motion: reduce) {{ * {{ transition: none !important; animation: none !important; }} }}
</style>
"""

# Датасетийн файлууд (mba_analysis/ хавтаснаас харьцангуй зам). Тайлан, баримт бичгийн D1–D11 хүснэгттэй ижил.
DATASETS = {
    "players": "data/processed/players_season.csv",
    "player_games": "data/processed/player_games.csv",
    "team_games": "data/processed/team_games.csv",
    "games": "data/processed/games.csv",
    "standings": "data/processed/standings_hist.csv",
    "team_meta": "data/processed/team_meta.csv",
    "team_logos": "data/processed/team_logos.csv",
    "geo": "data/raw/geo/mng_adm1.geojson",
    "shots": "data/processed/shots.csv",
    "pbp": "data/processed/pbp.csv.gz",
    "assists": "data/processed/assists.csv",
    "import_bg": "data/raw/import_background_raw.csv",
    "clusters": "reports/clusters.csv",
    "game_matrix": "reports/game_matrix.csv",
    "inplay": "reports/inplay_minute.csv",
    "metrics": "reports/metrics.json",
    "hypotheses": "reports/hypotheses.csv",
    "missing": "reports/missing.csv",
    "name_matches": "reports/name_matches.csv",
    "cleaning_log": "reports/cleaning_log.csv",
}

esc = html.escape


def inject_css() -> None:
    st.html(CSS)


def _md_bold(text: str) -> str:
    """**тод** markdown-ийг <b> болгоно (бусдыг escape)."""
    parts = esc(text).split("**")
    return "".join(f"<b>{p}</b>" if i % 2 else p for i, p in enumerate(parts))


# ---------------------------------------------------------------- толгой, хэсэг
def page_header(title: str, lead: str, eyebrow: str = "MBA Analytics") -> None:
    """Хуудасны толгой: зүүн талд гарчиг ба зорилго, баруун талд идэвхтэй улирал ба дата татсан огноо."""
    from data_access import current_filters, snapshot  # data_access нь ui-г зөвхөн функц дотроос импортолдог

    season = current_filters().season
    live = season == "2026-2027"
    pill = f'<span class="mba-pill{" mba-pill--live" if live else ""}">{esc(season.replace("-20", "–"))}' \
           f'{" · явагдаж буй" if live else ""}</span>'
    st.html(f'<header class="mba-head"><div class="mba-head__main"><div class="mba-eyebrow">{esc(eyebrow)}</div>'
            f'<h1>{esc(title)}</h1><p class="mba-lead">{esc(lead)}</p></div>'
            f'<div class="mba-head__meta">{pill}<span class="mba-fresh">Дата шинэчилсэн: {esc(snapshot())}</span></div>'
            "</header>")


def section(title: str, desc: str | None = None) -> None:
    st.html(f'<div class="mba-section"><h2>{esc(title)}</h2>' + (f"<p>{esc(desc)}</p>" if desc else "") + "</div>")


def findings(items: list[str], title: str = "Гол дүгнэлт") -> None:
    lis = "".join(f"<li>{_md_bold(t)}</li>" for t in items)
    st.html(f'<section class="mba-findings" aria-label="{esc(title)}"><h4>{esc(title)}</h4><ol>{lis}</ol></section>')


def stat_cards(items: Sequence[tuple], accent_first: bool = False) -> None:
    """items: (шошго, утга, тайлбар|None, tooltip|None, (баг, лого)|None) — тайлбар нь утгын доорх жижиг мөр."""
    cards = []
    for i, it in enumerate(items):
        label, value, sub, tip, logo = (list(it) + [None, None, None])[:5]
        cls = "mba-stat mba-stat--accent" if accent_first and i == 0 else "mba-stat"
        title = f' title="{esc(tip)}"' if tip else ""
        val = f'<div class="mba-stat__value">{esc(str(value))}</div>'
        if logo is not None:  # logo = (багийн нэр, URL) → утгын өмнө лого
            val = f'<div class="mba-stat__row">{team_logo(logo[0], logo[1], 34)}{val}</div>'
        cards.append(f'<div class="{cls}"{title}><div class="mba-stat__label">{esc(label)}</div>{val}'
                     + (f'<div class="mba-stat__sub">{esc(sub)}</div>' if sub else "") + "</div>")
    st.html(f'<div class="mba-stats">{"".join(cards)}</div>')


# ---------------------------------------------------------------- багийн дүрслэл
def initials(team: str) -> str:
    words = [w for w in str(team).replace("-", " ").split() if w[:1].isalnum()]
    if not words:
        return "?"
    caps = [w for w in words if w.isupper() and len(w) <= 4]  # BCH, SG, XAC, SUA
    return (caps[0][:3] if caps else "".join(w[0] for w in words[:2])).upper()


def team_logo(team: str, url: str | None, size: int = 24) -> str:
    """Логог тогтмол дөрвөлжинд object-fit: contain-оор. Ард нь үсгэн тэмдэг: URL алга эсвэл ачаалагдахгүй бол тэр харагдана."""
    fs = max(8, int(size * 0.36))
    img = f'<img src="{esc(url)}" alt="" loading="lazy" referrerpolicy="no-referrer">' if url else ""
    return (f'<span class="mba-logo" style="width:{size}px;height:{size}px;font-size:{fs}px" role="img" '
            f'aria-label="{esc(team)} лого">{esc(initials(team))}{img}</span>')


def team_label(team: str, url: str | None, size: int = 22) -> str:
    return f'<span class="mba-team">{team_logo(team, url, size)}<span class="mba-team__name">{esc(team)}</span></span>'


def team_header(team: str, url: str | None, meta: str = "", stats: Sequence[tuple[str, str]] = ()) -> None:
    kv = "".join(f'<div class="mba-kv"><b>{esc(v)}</b><span>{esc(k)}</span></div>' for k, v in stats)
    st.html(f'<div class="mba-teamhead">{team_logo(team, url, 52)}<div style="min-width:0">'
            f'<div class="mba-teamhead__name">{esc(team)}</div><div class="mba-teamhead__meta">{esc(meta)}</div></div>'
            + (f'<div class="mba-teamhead__stats">{kv}</div>' if kv else "") + "</div>")


def scoreboard(home: str, away: str, home_pts: int, away_pts: int, logos: dict, meta: str = "") -> None:
    def side(team, role, cls=""):
        return (f'<div class="mba-score__side {cls}">' + (team_logo(team, logos.get(team), 44) if not cls else "")
                + f'<div><div class="mba-score__team">{esc(team)}</div><div class="mba-score__role">{role}</div></div>'
                + (team_logo(team, logos.get(team), 44) if cls else "") + "</div>")
    hp, ap = (f"{home_pts}", f'<span class="lose">{away_pts}</span>') if home_pts > away_pts else \
        (f'<span class="lose">{home_pts}</span>', f"{away_pts}")
    st.html(f'<div class="mba-score">{side(home, "Гэрийн баг")}<div class="mba-score__pts">{hp} – {ap}</div>'
            f'{side(away, "Зочин баг", "mba-score__side--away")}'
            + (f'<div class="mba-score__meta">{esc(meta)}</div>' if meta else "") + "</div>")


def standings_board(rows, logos: dict, highlight: str | None = None, title: str = "Баг") -> None:
    """rows: (байр, баг, ялалт, хожигдол, ялалтын хувь) дараалал."""
    out = [f'<div class="mba-board__head"><span>#</span><span>{esc(title)}</span>'
           '<span style="text-align:right">Я–Х</span><span style="text-align:right">Ялалт %</span></div>']
    for rank, team, w, l, pct in rows:
        hl = " mba-board__row--hl" if team == highlight else ""
        out.append(f'<div class="mba-board__row{hl}"><span class="mba-board__rank">{rank}</span>{team_label(team, logos.get(team))}'
                   f'<span class="mba-board__rec">{w}–{l}</span><span class="mba-board__pct"><span class="mba-bar">'
                   f'<i style="width:{pct * 100:.0f}%"></i></span><span>{pct:.0%}</span></span></div>')
    st.html(f'<div class="mba-board" role="table" aria-label="Лигийн байр">{"".join(out)}</div>')


def compare_table(t1: str, t2: str, rows, logos: dict) -> None:
    """rows: (үзүүлэлт, тайлбар, утга1, утга2, формат, их нь сайн эсэх)."""
    body = []
    for label, note, v1, v2, fmt, higher_better in rows:
        better1 = (v1 > v2) if higher_better else (v1 < v2)
        better2 = (v2 > v1) if higher_better else (v2 < v1)
        body.append(f'<tr><td>{esc(label)}<small>{esc(note)}</small></td>'
                    f'<td class="{"win" if better1 else ""}">{fmt.format(v1)}</td>'
                    f'<td class="{"win" if better2 else ""}">{fmt.format(v2)}</td></tr>')
    st.html(f'<table class="mba-cmp"><thead><tr><th>Үзүүлэлт</th><th>{team_label(t1, logos.get(t1))}</th>'
            f'<th>{team_label(t2, logos.get(t2))}</th></tr></thead><tbody>{"".join(body)}</tbody></table>')


def player_header(name: str, team: str, logo: str | None, position: str, is_import: bool, style: str) -> None:
    badge = ('<span class="mba-badge mba-badge--import">Гадаад</span>' if is_import
             else '<span class="mba-badge mba-badge--domestic">Дотоод</span>')
    st.html(f'<div class="mba-player">{team_logo(team, logo, 44)}<div style="min-width:0">'
            f'<div class="mba-player__name">{esc(name)}</div><div class="mba-player__meta">'
            f'<span class="mba-badge">{esc(team)}</span><span class="mba-badge">{esc(position)}</span>{badge}'
            f'<span class="mba-badge">Хэв маяг: {esc(style)}</span></div></div></div>')


def player_stats(items: Sequence[tuple[str, str, str | None]]) -> None:
    cells = "".join(f'<div class="mba-pstat"><span>{esc(k)}</span><b>{esc(v)}</b>'
                    + (f"<small>{esc(s)}</small>" if s else "") + "</div>" for k, v, s in items)
    st.html(f'<div class="mba-pstats">{cells}</div>')


# ---------------------------------------------------------------- графикийн тэмдэглэл, төлөв
def chart_note(how: str, data: str, *, kind: str, files: list[str]) -> None:
    """kind = графикийн төрлийн нэр; files = DATASETS-ийн түлхүүрүүд (доор саарлаар файлын нэрийг бичнэ)."""
    paths = ", ".join(f"<code>{esc(DATASETS[k])}</code>" for k in files)
    st.html(f'<div class="mba-note"><span class="mba-note__kind">{esc(kind)}</span>'
            + (f"<b>Хэрхэн унших:</b> {esc(how)}" if how else "")
            + f'<div class="mba-note__src">Дата: {esc(data)} · Файл: {paths}</div></div>')


def empty_state(title: str, text: str = "") -> None:
    st.html(f'<div class="mba-state" role="status"><div class="mba-state__icon" aria-hidden="true">∅</div><div>'
            f'<div class="mba-state__title">{esc(title)}</div><div class="mba-state__text">{esc(text)}</div></div></div>')


def error_state(title: str, text: str = "") -> None:
    st.html(f'<div class="mba-state mba-state--error" role="alert"><div class="mba-state__icon" aria-hidden="true">!</div><div>'
            f'<div class="mba-state__title">{esc(title)}</div><div class="mba-state__text">{esc(text)}</div></div></div>')


def filter_summary(f) -> None:
    chips = [("Улирал", f.season.replace("-20", "–"), True)]
    chips.append(("Баг", ", ".join(f.teams) if f.teams else "бүгд", bool(f.teams)))
    chips.append(("Байрлал", ", ".join(f.positions) if f.positions else "бүгд", bool(f.positions)))
    chips.append(("Тоглогч", f.import_status.lower(), f.import_status != "Бүгд"))
    chips.append(("Доод хязгаар", f"{f.min_gp}+ тоглолт", f.min_gp != 5))
    if f.highlight_team:
        chips.append(("Онцолсон", f.highlight_team, True))
    st.html('<div class="mba-chips" aria-label="Идэвхтэй шүүлтүүр">' + "".join(
        f'<span class="mba-chip{" mba-chip--active" if act else ""}">{esc(k)}: <b>{esc(v)}</b></span>'
        for k, v, act in chips) + "</div>")


def pareto_who(df, teams: dict | None = None, label: str = "лигийн") -> None:
    """Парето графикийн «80%-д хүрсэн тоглогчид хэн бэ» гэсэн задгай хүснэгт (df: rank, player_name, value, cum_share)."""
    d = df.sort_values("rank")
    if d.empty:
        return
    k = int((d.cum_share.to_numpy() < 0.8).sum()) + 1
    with st.expander(f"Онооны 80%-ийг авсан {k} тоглогч хэн бэ?"):
        t = d.head(k).assign(team=d.label.map(teams) if teams else None)
        cols = {"rank": "Байр", "player_name": "Тоглогч", "team": "Баг", "value": "Улирлын нийт оноо",
                "cum_share": f"1-р байраас энэ хүртэлх нийлбэр ({label} онооны %)"}
        if not teams:
            cols.pop("team")
        st.dataframe(t[list(cols)].rename(columns=cols), hide_index=True, width="stretch",
                     column_config={cols["cum_share"]: st.column_config.ProgressColumn(format="percent", min_value=0,
                                                                                         max_value=1)})


# ---------------------------------------------------------------- график ба footer
CHART_CONFIG = {
    "displaylogo": False,
    "modeBarButtonsToRemove": ["lasso2d", "select2d", "autoScale2d", "toggleSpikelines", "hoverCompareCartesian",
                               "hoverClosestCartesian"],
    "toImageButtonOptions": {"format": "png", "filename": "mba_analytics_chart", "scale": 2},
}


def show_chart(fig, select: bool = False, **kw):
    """Бүх графикийг нэг тохиргоогоор: Plotly лого, хэрэггүй товчгүй, PNG-ээр 2× чанартай татна.
    select=True бол хүрээ/lasso сонголтын товчийг үлдээнэ (тоглогч сонгох график)."""
    cfg = dict(CHART_CONFIG)
    if select:
        cfg["modeBarButtonsToRemove"] = [b for b in cfg["modeBarButtonsToRemove"] if b not in ("lasso2d", "select2d")]
    kw.setdefault("width", "stretch")
    return st.plotly_chart(fig, config=cfg, **kw)


def footer() -> None:
    st.html('<footer class="mba-footer" role="contentinfo">© 2026 MBA Analytics</footer>')
