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

import base64
import html
from collections.abc import Sequence

import streamlit as st

TOKENS = {
    # брэнд
    "primary": "#1B3A6B", "primary-hover": "#142C52", "primary-soft": "#E8EEF7",
    "secondary": "#475569", "accent": "#F08A3C", "accent-ink": "#B9480C", "accent-soft": "#FDEBDD",
    # гадаргуу
    "bg": "#F5F7FA", "surface": "#FFFFFF", "surface-2": "#F1F4F8", "sidebar": "#F8FAFC",
    # текст
    "text": "#0F172A", "text-2": "#475569", "text-3": "#5B6B7F", "text-inverse": "#E6ECF5",
    # хүрээ
    "border": "#DCE3EC", "border-strong": "#C3CEDC",
    # төлөв
    "success": "#15803D", "success-soft": "#E7F5EC", "warning": "#B45309", "warning-soft": "#FDF3E2",
    "error": "#B91C1C", "error-soft": "#FCECEC", "info": "#1D4ED8", "info-soft": "#E8F0FE",
    # хэмжээ
    "muted": "#F1F4F8", "ring": "rgba(27,58,107,.30)",
    # хэмжээ (shadcn: --radius 0.625rem → xl ×1.4, md ×0.8, sm ×0.6; shadow-sm, shadow-xs)
    "radius-xl": "14px", "radius": "10px", "radius-md": "8px", "radius-sm": "6px",
    "shadow": "0 1px 3px 0 rgba(15,23,42,.08), 0 1px 2px -1px rgba(15,23,42,.08)", "shadow-xs": "0 1px 2px 0 rgba(15,23,42,.05)",
}
FONT_STACK = "Inter, 'Segoe UI', Arial, sans-serif"

_VARS = "\n".join(f"  --mba-{k}: {v};" for k, v in TOKENS.items())
CSS = f"""
<style>
/* Бүрэлдэхүүний хэмжээ shadcn/ui (new-york-v4)-ийн Tailwind классаас: Card rounded-xl border shadow-sm, Badge rounded-full
   px-2 py-0.5 text-xs, Table text-sm h-10/p-2, TabsList bg-muted rounded-lg p-[3px] h-9, Button/Input h-9 rounded-md shadow-xs,
   focus ring 3px. Өнгө нь MBA Analytics-ийн брэнд токен. */
:root {{
{_VARS}
  --mba-font: {FONT_STACK};
}}
/* ---- суурь ---- */
[data-testid="stDecoration"] {{ display: none; }}
/* Streamlit-ийн дээд header (лого, sidebar нээх товч) 3.5rem өндөр бөгөөд контентын дээр давхарладаг тул түүний доороос эхэлнэ */
[data-testid="stMainBlockContainer"] {{ padding-top: 4rem; padding-bottom: 3rem; max-width: 1440px; }}
[data-testid="stMetricValue"], [data-testid="stDataFrame"], .mba-num {{ font-variant-numeric: tabular-nums; }}
[data-testid="stMarkdownContainer"] p, [data-testid="stMarkdownContainer"] li {{ line-height: 1.6; }}
[data-testid="stCaptionContainer"] {{ line-height: 1.5; color: var(--mba-text-3); }}
h2, h3 {{ letter-spacing: -0.01em; }}
[data-testid="stHeading"] h3 {{ padding-top: .6rem; }}
a:focus-visible, button:focus-visible, [role="tab"]:focus-visible {{
  outline: 2px solid var(--mba-info); outline-offset: 2px; border-radius: 4px; }}

/* ---- карт (shadcn Card) ---- */
.mba-card {{ background: var(--mba-surface); border: 1px solid var(--mba-border); border-radius: var(--mba-radius-xl);
  box-shadow: var(--mba-shadow); }}
[data-testid="stPlotlyChart"] {{ background: var(--mba-surface); border: 1px solid var(--mba-border); border-radius: var(--mba-radius-xl);
  box-shadow: var(--mba-shadow); padding: 8px 6px 4px 6px; overflow: hidden; }}
[data-testid="stDataFrame"] {{ border-radius: var(--mba-radius-md); }}
[data-testid="stVerticalBlockBorderWrapper"] {{ background: var(--mba-surface); border-radius: var(--mba-radius-xl); }}

/* ---- товч (shadcn Button: outline / default) ---- */
[data-testid="stBaseButton-secondary"], [data-testid="stBaseButton-primary"] {{
  min-height: 36px; border-radius: var(--mba-radius-md); font-size: .875rem; font-weight: 500; box-shadow: var(--mba-shadow-xs);
  transition: background-color .15s, box-shadow .15s; }}
[data-testid="stMain"] [data-testid="stBaseButton-secondary"]:hover {{ background: var(--mba-muted); border-color: var(--mba-border); color: var(--mba-text); }}
[data-testid="stBaseButton-secondary"]:focus-visible, [data-testid="stBaseButton-primary"]:focus-visible {{
  box-shadow: 0 0 0 3px var(--mba-ring); outline: none; }}

/* ---- оролт, сонгогч (shadcn Input / SelectTrigger) ---- */
[data-testid="stMain"] [data-baseweb="select"] > div, [data-testid="stMain"] [data-baseweb="input"] {{
  border-radius: var(--mba-radius-md); box-shadow: var(--mba-shadow-xs); min-height: 36px; }}
[data-testid="stMain"] [data-baseweb="select"] > div:focus-within, [data-testid="stMain"] [data-baseweb="input"]:focus-within {{
  box-shadow: 0 0 0 3px var(--mba-ring); }}
[data-testid="stWidgetLabel"] p {{ font-size: .875rem; font-weight: 500; }}

/* ---- табууд (shadcn TabsList / TabsTrigger; Streamlit 1.67 = react-aria: role=tablist, data-testid=stTab) ---- */
[data-testid="stTabs"] [role="tablist"] {{ display: inline-flex; width: fit-content; max-width: 100%; gap: 0; padding: 3px;
  border-radius: var(--mba-radius); background: var(--mba-muted); border: 0; overflow-x: auto; }}
[data-testid="stTab"] {{ height: 30px; padding: 4px 12px; margin: 0; border-radius: var(--mba-radius-md);
  border: 1px solid transparent !important; color: var(--mba-text-2); background: transparent; transition: all .15s; white-space: nowrap; }}
[data-testid="stTab"]::after, [data-testid="stTab"]::before {{ display: none !important; }}
[data-testid="stTab"] .react-aria-SelectionIndicator {{ display: none !important; }}
[data-testid="stTab"] p {{ font-size: .875rem; font-weight: 500; }}
[data-testid="stTab"]:hover {{ color: var(--mba-text); }}
[data-testid="stTab"][aria-selected="true"] {{ background: var(--mba-surface); color: var(--mba-text); box-shadow: var(--mba-shadow); }}
[data-testid="stTab"]:focus-visible {{ box-shadow: 0 0 0 3px var(--mba-ring); outline: none; }}
[data-testid="stTabPanel"] {{ padding-top: 1rem; }}

/* ---- segmented control ---- */
[data-testid="stButtonGroup"] button {{ font-size: .875rem; }}

/* ---- sidebar (shadcn: цайвар, зөвхөн навигаци) ---- */
[data-testid="stSidebar"] {{ border-right: 1px solid var(--mba-border); }}
[data-testid="stSidebarNav"] a {{ border-radius: var(--mba-radius-md); }}
[data-testid="stSidebarNav"] a:hover {{ background: var(--mba-surface-2); }}
[data-testid="stSidebarNav"] a[aria-current="page"] {{ background: var(--mba-primary-soft); }}
[data-testid="stSidebarNav"] a[aria-current="page"] span {{ color: var(--mba-primary); font-weight: 600; }}
[data-testid="stSidebarNavSeparator"] {{ border-color: var(--mba-border); }}
[data-testid="stSidebar"] [data-testid="stCaptionContainer"], [data-testid="stSidebar"] [data-testid="stCaptionContainer"] p {{ color: var(--mba-text-3); }}

/* ---- дээд самбар: байршил + шүүлтүүр ---- */
/* sticky-г Streamlit-ийн wrapper дээр тавина (дотор талын блок дээр тавибал wrapper-ээсээ гарч наалдахгүй) */
[data-testid="stLayoutWrapper"]:has(> .st-key-mba_toolbar) {{ position: sticky; top: 3.5rem; z-index: 50;
  background: color-mix(in srgb, var(--mba-bg) 88%, transparent); backdrop-filter: blur(8px); }}
.st-key-mba_toolbar {{ padding: 10px 0; margin: 0 0 .6rem 0; border-bottom: 1px solid var(--mba-border); }}
.st-key-mba_toolbar > div:first-child {{ margin-right: auto; }}
.mba-crumb {{ display: flex; gap: 8px; align-items: center; font-size: .875rem; color: var(--mba-text-3); white-space: nowrap; }}
.mba-crumb b {{ color: var(--mba-text); font-weight: 600; }}
.mba-crumb--solo {{ padding: 10px 0; margin-bottom: .6rem; border-bottom: 1px solid var(--mba-border); }}
.mba-chips__label {{ font-size: .8rem; color: var(--mba-text-3); align-self: center; margin-right: 2px; }}

/* ---- хуудасны толгой ---- */
.mba-head {{ display: flex; gap: 24px; align-items: flex-end; justify-content: space-between; flex-wrap: wrap;
  margin: 0 0 1rem 0; padding-bottom: 1rem; border-bottom: 1px solid var(--mba-border); }}
.mba-head__main {{ min-width: 0; flex: 1 1 420px; }}
.mba-head__meta {{ display: flex; flex-direction: column; align-items: flex-end; gap: 6px; font-size: .8rem; color: var(--mba-text-3); }}
.mba-eyebrow {{ font-size: .75rem; font-weight: 700; letter-spacing: .08em; text-transform: uppercase;
  color: var(--mba-accent-ink); margin-bottom: .35rem; }}
.mba-head h1 {{ font-size: 1.9rem; font-weight: 700; color: var(--mba-text); margin: 0; padding: 0; letter-spacing: -0.02em; }}
.mba-lead {{ font-size: 1rem; color: var(--mba-text-2); max-width: 78ch; margin: .45rem 0 0 0; line-height: 1.55; }}
.mba-fresh {{ display: inline-flex; align-items: center; gap: 6px; }}

/* ---- тэмдэг (shadcn Badge: default / secondary / outline) ---- */
.mba-badge {{ display: inline-flex; align-items: center; gap: 4px; width: fit-content; white-space: nowrap; padding: 2px 8px;
  border-radius: 999px; border: 1px solid transparent; font-size: .75rem; line-height: 1rem; font-weight: 500;
  background: var(--mba-muted); color: var(--mba-text); }}
.mba-badge--default {{ background: var(--mba-primary); color: #fff; }}
.mba-badge--outline {{ background: var(--mba-surface); border-color: var(--mba-border); color: var(--mba-text); }}
.mba-badge--soft {{ background: var(--mba-primary-soft); color: var(--mba-primary); }}
.mba-badge--import {{ background: #FCEEE6; color: #9A3412; }}
.mba-badge--domestic {{ background: #E6F1F8; color: #075985; }}
.mba-badge--live::before {{ content: ""; width: 6px; height: 6px; border-radius: 50%; background: #4ADE80; }}
.mba-badge b {{ font-weight: 600; }}
.mba-chips {{ display: flex; flex-wrap: wrap; gap: 6px; margin: 0; }}
.st-key-mba_chips {{ margin: -.2rem 0 .6rem 0; }}

/* ---- хэсгийн гарчиг ---- */
.mba-section {{ margin: 1.8rem 0 .7rem 0; }}
.mba-section h2 {{ font-size: 1.15rem; font-weight: 600; color: var(--mba-text); margin: 0; padding: 0; line-height: 1.3; }}
.mba-section p {{ font-size: .875rem; color: var(--mba-text-3); margin: .25rem 0 0 0; max-width: 90ch; }}

/* ---- гол дүгнэлт (shadcn Alert) ---- */
.mba-alert {{ display: grid; grid-template-columns: 16px 1fr; column-gap: 12px; align-items: start; padding: 12px 16px;
  border: 1px solid var(--mba-border); border-radius: var(--mba-radius); background: var(--mba-surface); margin-bottom: .6rem; }}
.mba-alert__icon {{ width: 16px; height: 16px; margin-top: 2px; }}
.mba-alert__title {{ font-size: .875rem; font-weight: 600; color: var(--mba-text); line-height: 1.25; letter-spacing: -0.01em; }}
.mba-alert__desc {{ margin: 6px 0 0 0; padding-left: 1.1rem; font-size: .875rem; line-height: 1.6; color: var(--mba-text-2); }}
.mba-alert__desc li {{ margin: 2px 0; }}
.mba-alert__desc b {{ color: var(--mba-text); }}

/* ---- тоон карт (shadcn dashboard «SectionCards») ---- */
.mba-stats {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(170px, 1fr)); gap: 12px; margin: .2rem 0 .9rem 0; }}
.mba-kpi {{ display: flex; flex-direction: column; gap: 6px; padding: 16px 18px; min-width: 0; container-type: inline-size; }}
.mba-kpi__desc {{ font-size: .875rem; color: var(--mba-text-3); line-height: 1.25; }}
.mba-kpi__value {{ font-size: 1.5rem; font-weight: 600; color: var(--mba-text); line-height: 1.15; letter-spacing: -0.01em;
  font-variant-numeric: tabular-nums; overflow-wrap: anywhere; }}
@container (min-width: 220px) {{ .mba-kpi__value {{ font-size: 1.875rem; }} }}
.mba-kpi__foot {{ font-size: .8rem; color: var(--mba-text-3); line-height: 1.4; }}
.mba-kpi__row {{ display: flex; align-items: center; gap: 10px; min-width: 0; }}
.mba-kpi__row--trend {{ flex-wrap: wrap; row-gap: 4px; }}
.mba-kpi__row--trend .mba-kpi__value {{ font-size: inherit; }}
.mba-kpi__trend {{ flex: none; font-variant-numeric: tabular-nums; white-space: nowrap; }}
.mba-kpi__foot--note {{ color: var(--mba-text-2); font-weight: 500; }}
.mba-kpi__row .mba-kpi__value {{ font-size: 1.25rem; }}

/* ---- багийн лого ---- */
.mba-logo {{ position: relative; display: inline-grid; place-items: center; flex: none; border-radius: var(--mba-radius-md);
  background: var(--mba-muted); border: 1px solid var(--mba-border); overflow: hidden; color: var(--mba-text-2);
  font-weight: 700; letter-spacing: .02em; vertical-align: middle; }}
.mba-logo img {{ position: absolute; inset: 0; width: 100%; height: 100%; object-fit: contain; padding: 8%; background: #fff; }}
.mba-team {{ display: inline-flex; align-items: center; gap: 8px; font-weight: 500; color: var(--mba-text); min-width: 0; }}
.mba-team span.mba-team__name {{ min-width: 0; overflow-wrap: break-word; line-height: 1.25; }}
.mba-teamhead {{ display: flex; align-items: center; gap: 14px; padding: 16px 18px; }}
.mba-teamhead__name {{ font-size: 1.125rem; font-weight: 600; color: var(--mba-text); line-height: 1.25; }}
.mba-teamhead__meta {{ font-size: .875rem; color: var(--mba-text-3); margin-top: 2px; }}
.mba-teamhead__stats {{ margin-left: auto; display: flex; gap: 20px; flex-wrap: wrap; justify-content: flex-end; }}
.mba-kv {{ text-align: right; }}
.mba-kv b {{ display: block; font-size: 1.125rem; font-weight: 600; color: var(--mba-text); font-variant-numeric: tabular-nums; }}
.mba-kv span {{ font-size: .75rem; color: var(--mba-text-3); }}

/* ---- онооны самбар ---- */
.mba-score {{ display: grid; grid-template-columns: 1fr auto 1fr; align-items: center; gap: 12px; padding: 16px 20px; }}
.mba-score__side {{ display: flex; align-items: center; gap: 10px; min-width: 0; }}
.mba-score__side--away {{ justify-content: flex-end; text-align: right; }}
.mba-score__team {{ font-weight: 600; color: var(--mba-text); line-height: 1.2; }}
.mba-score__role {{ font-size: .75rem; color: var(--mba-text-3); }}
.mba-score__pts {{ font-size: 2rem; font-weight: 700; color: var(--mba-text); font-variant-numeric: tabular-nums; white-space: nowrap;
  letter-spacing: -0.02em; }}
.mba-score__pts .lose {{ color: var(--mba-text-3); font-weight: 500; }}
.mba-score__meta {{ grid-column: 1 / -1; text-align: center; font-size: .8rem; color: var(--mba-text-3); padding-top: 10px;
  border-top: 1px solid var(--mba-border); }}

/* ---- хүснэгт (shadcn Table) ---- */
.mba-table {{ width: 100%; border-collapse: collapse; font-size: .875rem; }}
.mba-table th {{ height: 40px; padding: 0 10px; text-align: left; vertical-align: middle; font-weight: 500; color: var(--mba-text);
  white-space: nowrap; border-bottom: 1px solid var(--mba-border); }}
.mba-table td {{ padding: 8px 10px; vertical-align: middle; border-bottom: 1px solid var(--mba-border); color: var(--mba-text);
  font-variant-numeric: tabular-nums; }}
.mba-table tbody tr {{ transition: background-color .15s; }}
.mba-table tbody tr:hover {{ background: rgba(241,244,248,.6); }}
.mba-table tbody tr:last-child td {{ border-bottom: 0; }}
.mba-table .num {{ text-align: right; }}
.mba-table .muted {{ color: var(--mba-text-3); }}
.mba-table-wrap {{ overflow-x: auto; padding: 4px 8px; }}

/* ---- лигийн байр ---- */
.mba-board {{ container-type: inline-size; }}
.mba-board tr.hl {{ background: var(--mba-accent-soft); }}
.mba-board tr.hl:hover {{ background: var(--mba-accent-soft); }}
.mba-board td.rank {{ width: 28px; color: var(--mba-text-3); text-align: right; font-weight: 500; }}
.mba-progress {{ display: flex; align-items: center; gap: 8px; justify-content: flex-end; }}
.mba-bar {{ position: relative; width: 64px; height: 8px; border-radius: 999px; background: rgba(27,58,107,.2); overflow: hidden; flex: none; }}
.mba-bar > i {{ position: absolute; left: 0; top: 0; bottom: 0; border-radius: 999px; background: var(--mba-primary); }}
@container (max-width: 380px) {{ .mba-board .mba-bar {{ display: none; }} .mba-board th, .mba-board td {{ padding-left: 6px; padding-right: 6px; }} }}

/* ---- харьцуулалт ---- */
.mba-cmp th {{ text-align: center; }}
.mba-cmp th:first-child {{ text-align: left; color: var(--mba-text-3); }}
.mba-cmp td {{ text-align: center; color: var(--mba-text-2); }}
.mba-cmp td:first-child {{ text-align: left; color: var(--mba-text); }}
.mba-cmp td.win {{ color: var(--mba-text); font-weight: 600; background: var(--mba-success-soft); }}
.mba-cmp small {{ display: block; color: var(--mba-text-3); font-size: .75rem; }}

/* ---- графикийн тэмдэглэл ---- */
.mba-note {{ font-size: .82rem; line-height: 1.55; color: var(--mba-text-2); margin: -.2rem 2px 1rem 2px; }}
.mba-note .mba-badge {{ margin-right: 6px; vertical-align: 1px; }}
.mba-note__src {{ color: var(--mba-text-3); margin-top: 3px; font-size: .78rem; }}
.mba-note code, .mba-source code {{ color: var(--mba-text-2); background: var(--mba-muted); padding: 0 4px; border-radius: 4px; font-size: .74rem; }}
.mba-source {{ color: var(--mba-text-3); font-size: .78rem; }}

/* ---- дасгалжуулагчийн дүгнэлт (график бүрийн доор) ---- */
.mba-coach {{ display: grid; grid-template-columns: 16px 1fr; column-gap: 10px; align-items: start; padding: 10px 14px;
  margin: -.4rem 2px 1.1rem 2px; background: var(--mba-muted); border: 1px solid var(--mba-border); border-radius: var(--mba-radius-md); }}
.mba-coach__icon {{ width: 16px; height: 16px; margin-top: 2px; }}
.mba-coach__title {{ font-size: .8rem; font-weight: 600; color: var(--mba-accent-ink); letter-spacing: .01em; }}
.mba-coach ul {{ margin: 4px 0 0 0; padding-left: 1.05rem; font-size: .84rem; line-height: 1.55; color: var(--mba-text-2); }}
.mba-coach li {{ margin: 2px 0; }}
.mba-coach b {{ color: var(--mba-text); }}

/* ---- төлөв (shadcn Alert / Empty) ---- */
.mba-state {{ display: flex; gap: 12px; align-items: flex-start; padding: 16px 18px; border-radius: var(--mba-radius);
  border: 1px dashed var(--mba-border-strong); background: var(--mba-surface); }}
.mba-state__icon {{ font-size: 1.2rem; line-height: 1.2; color: var(--mba-text-3); }}
.mba-state__title {{ font-weight: 600; font-size: .925rem; color: var(--mba-text); }}
.mba-state__text {{ color: var(--mba-text-2); font-size: .875rem; margin-top: 2px; }}
.mba-state--error {{ border-style: solid; border-color: #F3C7C7; background: var(--mba-error-soft); }}
.mba-state--error .mba-state__title, .mba-state--error .mba-state__icon {{ color: var(--mba-error); }}

/* ---- тоглогчийн карт ---- */
.mba-player {{ display: flex; gap: 12px; align-items: flex-start; }}
.mba-player__name {{ font-size: 1.125rem; font-weight: 600; color: var(--mba-text); line-height: 1.25; }}
.mba-player__meta {{ display: flex; flex-wrap: wrap; gap: 6px; margin-top: 6px; }}
.mba-pstats {{ display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 8px; margin-top: 12px; }}
.mba-pstat {{ border: 1px solid var(--mba-border); border-radius: var(--mba-radius-md); padding: 8px 10px; }}
.mba-pstat span {{ display: block; font-size: .78rem; color: var(--mba-text-3); }}
.mba-pstat b {{ font-size: 1.35rem; font-weight: 600; color: var(--mba-text); font-variant-numeric: tabular-nums; }}
.mba-pstat small {{ display: block; color: var(--mba-text-3); font-size: .74rem; }}

/* ---- expander (shadcn Accordion/Card) ---- */
[data-testid="stExpander"] details {{ background: var(--mba-surface); border: 1px solid var(--mba-border); border-radius: var(--mba-radius);
  box-shadow: var(--mba-shadow-xs); }}
[data-testid="stExpander"] summary {{ font-size: .875rem; font-weight: 500; color: var(--mba-text); }}
[data-testid="stExpander"] summary:hover {{ color: var(--mba-primary); }}

/* ---- footer ---- */
.mba-footer {{ margin-top: 3rem; padding: 14px 0 6px 0; border-top: 1px solid var(--mba-border); color: var(--mba-text-3);
  font-size: .8rem; text-align: center; }}

@media (max-width: 640px) {{
  [data-testid="stMainBlockContainer"] {{ padding-left: 1rem; padding-right: 1rem; padding-top: 4rem; }}
  .mba-head h1 {{ font-size: 1.5rem; }}
  .mba-head__meta {{ align-items: flex-start; }}
  .mba-stats {{ grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 8px; }}
  .mba-kpi {{ padding: 12px 14px; }}
  .mba-stats > :last-child:nth-child(odd) {{ grid-column: 1 / -1; }}
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
    """Хуудасны толгой: гарчиг ба зорилго, баруун талд дата шинэчилсэн огноо.
    Байршил ба улирал дээд самбарт (breadcrumb, улирлын сонголт) харагддаг тул eyebrow-г давхардуулж зурахгүй."""
    from data_access import snapshot  # data_access нь ui-г зөвхөн функц дотроос импортолдог

    st.html(f'<header class="mba-head"><div class="mba-head__main">'
            f'<h1>{esc(title)}</h1><p class="mba-lead">{esc(lead)}</p></div>'
            f'<div class="mba-head__meta"><span class="mba-fresh">Дата шинэчилсэн: {esc(snapshot())}</span></div>'
            "</header>")


def section(title: str, desc: str | None = None) -> None:
    st.html(f'<div class="mba-section"><h2>{esc(title)}</h2>' + (f"<p>{esc(desc)}</p>" if desc else "") + "</div>")


_INFO_ICON = "data:image/svg+xml;base64,PHN2ZyB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciIHdpZHRoPSIxNiIgaGVpZ2h0PSIxNiIgdmlld0JveD0iMCAwIDI0IDI0IiBmaWxsPSJub25lIiBzdHJva2U9IiMxQjNBNkIiIHN0cm9rZS13aWR0aD0iMiIgc3Ryb2tlLWxpbmVjYXA9InJvdW5kIiBzdHJva2UtbGluZWpvaW49InJvdW5kIj48Y2lyY2xlIGN4PSIxMiIgY3k9IjEyIiByPSIxMCIvPjxwYXRoIGQ9Ik0xMiAxNnYtNCIvPjxwYXRoIGQ9Ik0xMiA4aC4wMSIvPjwvc3ZnPg=="  # lucide «info» (ISC), брэндийн цэнхэр


def findings(items: list[str], title: str = "Гол дүгнэлт") -> None:
    """shadcn Alert хэлбэрийн дүгнэлт: дүрс, гарчиг, дугаарласан жагсаалт."""
    lis = "".join(f"<li>{_md_bold(t)}</li>" for t in items)
    st.html(f'<section class="mba-alert" role="note" aria-label="{esc(title)}"><img class="mba-alert__icon" src="{_INFO_ICON}" alt="">'
            f'<div><div class="mba-alert__title">{esc(title)}</div><ol class="mba-alert__desc">{lis}</ol></div></section>')


def stat_cards(items: Sequence[tuple], accent_first: bool = False) -> None:
    """shadcn dashboard-ийн KPI карт (SectionCards): тайлбар + чиг хандлагын тэмдэг, том утга, доод мөр.
    items: (шошго, утга, тайлбар|None, tooltip|None, (баг, лого)|None, (өөрчлөлт, чиглэл, тайлбар)|None).
    чиглэл: "up" | "down" | "flat". Өнгөөр сайн/муу гэж дүгнэхгүй (гадаадын онооны өсөлт сайн ч биш, муу ч биш),
    зөвхөн сум ба тоогоор харуулна. accent_first: хуучин API (одоо ашиглахгүй)."""
    arrows = {"up": "↑", "down": "↓", "flat": "→"}
    cards = []
    for it in items:
        label, value, sub, tip, logo, delta = (list(it) + [None] * 4)[:6]
        title = f' title="{esc(tip)}"' if tip else ""
        val = f'<div class="mba-kpi__value">{esc(str(value))}</div>'
        if logo is not None:  # logo = (багийн нэр, URL) → утгын өмнө лого
            val = f'<div class="mba-kpi__row">{team_logo(logo[0], logo[1], 34)}{val}</div>'
        trend = ""
        if delta is not None:
            text, direction, note = (list(delta) + [None])[:3]
            trend = (f'<span class="mba-badge mba-badge--outline mba-kpi__trend" title="{esc(note or "")}">'
                     f'<span aria-hidden="true">{arrows.get(direction, "")}</span> {esc(text)}</span>')
        if trend:  # утгын баруун талд — карт нарийн үед шошгыг шахахгүй
            val = f'<div class="mba-kpi__row mba-kpi__row--trend">{val}{trend}</div>'
        head = f'<div class="mba-kpi__desc">{esc(label)}</div>'
        cards.append(f'<div class="mba-card mba-kpi"{title}>{head}{val}'
                     + (f'<div class="mba-kpi__foot">{esc(sub)}</div>' if sub else "")
                     + (f'<div class="mba-kpi__foot mba-kpi__foot--note">{esc(delta[2])}</div>'
                        if delta is not None and len(delta) > 2 and delta[2] else "")
                     + "</div>")
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
    st.html(f'<div class="mba-card mba-teamhead">{team_logo(team, url, 52)}<div style="min-width:0">'
            f'<div class="mba-teamhead__name">{esc(team)}</div><div class="mba-teamhead__meta">{esc(meta)}</div></div>'
            + (f'<div class="mba-teamhead__stats">{kv}</div>' if kv else "") + "</div>")


def scoreboard(home: str, away: str, home_pts: int, away_pts: int, logos: dict, meta: str = "") -> None:
    def side(team, role, cls=""):
        return (f'<div class="mba-score__side {cls}">' + (team_logo(team, logos.get(team), 44) if not cls else "")
                + f'<div><div class="mba-score__team">{esc(team)}</div><div class="mba-score__role">{role}</div></div>'
                + (team_logo(team, logos.get(team), 44) if cls else "") + "</div>")
    hp, ap = (f"{home_pts}", f'<span class="lose">{away_pts}</span>') if home_pts > away_pts else \
        (f'<span class="lose">{home_pts}</span>', f"{away_pts}")
    st.html(f'<div class="mba-card mba-score">{side(home, "Гэрийн баг")}<div class="mba-score__pts">{hp} – {ap}</div>'
            f'{side(away, "Зочин баг", "mba-score__side--away")}'
            + (f'<div class="mba-score__meta">{esc(meta)}</div>' if meta else "") + "</div>")


def standings_board(rows, logos: dict, highlight: str | None = None, title: str = "Баг") -> None:
    """rows: (байр, баг, ялалт, хожигдол, ялалтын хувь) дараалал. shadcn Table + Progress."""
    body = []
    for rank, team, w, l, pct in rows:
        body.append(f'<tr class="{"hl" if team == highlight else ""}"><td class="rank">{rank}</td><td>{team_label(team, logos.get(team))}</td>'
                    f'<td class="num muted">{w}–{l}</td><td class="num"><span class="mba-progress"><span class="mba-bar">'
                    f'<i style="width:{pct * 100:.0f}%"></i></span><span>{pct:.0%}</span></span></td></tr>')
    st.html(f'<div class="mba-card mba-board mba-table-wrap"><table class="mba-table" aria-label="Лигийн байр"><thead><tr>'
            f'<th class="num">#</th><th>{esc(title)}</th><th class="num">Я–Х</th><th class="num">Ялалт</th></tr></thead>'
            f'<tbody>{"".join(body)}</tbody></table></div>')


def compare_table(t1: str, t2: str, rows, logos: dict) -> None:
    """rows: (үзүүлэлт, тайлбар, утга1, утга2, формат, их нь сайн эсэх)."""
    body = []
    for label, note, v1, v2, fmt, higher_better in rows:
        better1 = (v1 > v2) if higher_better else (v1 < v2)
        better2 = (v2 > v1) if higher_better else (v2 < v1)
        body.append(f'<tr><td>{esc(label)}<small>{esc(note)}</small></td>'
                    f'<td class="{"win" if better1 else ""}">{fmt.format(v1)}</td>'
                    f'<td class="{"win" if better2 else ""}">{fmt.format(v2)}</td></tr>')
    st.html(f'<div class="mba-card mba-table-wrap"><table class="mba-table mba-cmp"><thead><tr><th>Үзүүлэлт</th>'
            f'<th>{team_label(t1, logos.get(t1))}</th><th>{team_label(t2, logos.get(t2))}</th></tr></thead>'
            f'<tbody>{"".join(body)}</tbody></table></div>')


def player_header(name: str, team: str, logo: str | None, position: str, is_import: bool, style: str) -> None:
    badge = ('<span class="mba-badge mba-badge--import">Гадаад</span>' if is_import
             else '<span class="mba-badge mba-badge--domestic">Дотоод</span>')
    st.html(f'<div class="mba-player">{team_logo(team, logo, 44)}<div style="min-width:0">'
            f'<div class="mba-player__name">{esc(name)}</div><div class="mba-player__meta">'
            f'<span class="mba-badge mba-badge--outline">{esc(team)}</span><span class="mba-badge mba-badge--outline">{esc(position)}</span>'
            f'{badge}<span class="mba-badge">Хэв маяг: {esc(style)}</span></div></div></div>')


def player_stats(items: Sequence[tuple[str, str, str | None]]) -> None:
    cells = "".join(f'<div class="mba-pstat"><span>{esc(k)}</span><b>{esc(v)}</b>'
                    + (f"<small>{esc(s)}</small>" if s else "") + "</div>" for k, v, s in items)
    st.html(f'<div class="mba-pstats">{cells}</div>')


# ---------------------------------------------------------------- графикийн тэмдэглэл, төлөв
def chart_note(how: str, data: str, *, kind: str, files: list[str]) -> None:
    """kind = графикийн төрлийн нэр; files = DATASETS-ийн түлхүүрүүд (доор саарлаар файлын нэрийг бичнэ)."""
    paths = ", ".join(f"<code>{esc(DATASETS[k])}</code>" for k in files)
    st.html(f'<div class="mba-note"><span class="mba-badge">{esc(kind)}</span>'
            + (f"<b>Хэрхэн унших:</b> {esc(how)}" if how else "")
            + f'<div class="mba-note__src">Дата: {esc(data)} · Файл: {paths}</div></div>')


_COACH_ICON = "data:image/svg+xml;base64," + base64.b64encode(  # lucide «clipboard-list» (ISC), accent-ink
    b'<svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="#B9480C" '
    b'stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect width="8" height="4" x="8" y="2" rx="1" ry="1"/>'
    b'<path d="M16 4h2a2 2 0 0 1 2 2v14a2 2 0 0 1-2 2H6a2 2 0 0 1-2-2V6a2 2 0 0 1 2-2h2"/><path d="M12 11h4"/>'
    b'<path d="M12 16h4"/><path d="M8 11h.01"/><path d="M8 16h.01"/></svg>').decode()


def coach(items: list[str], title: str = "Дасгалжуулагчийн дүгнэлт") -> None:
    """График бүрийн доорх практик дүгнэлт (dashboard/coach.py-аас датаар тооцоолсон). Хоосон бол юу ч зурахгүй."""
    items = [t for t in items if t]
    if not items:
        return
    lis = "".join(f"<li>{_md_bold(t)}</li>" for t in items)
    st.html(f'<aside class="mba-coach" aria-label="{esc(title)}"><img class="mba-coach__icon" src="{_COACH_ICON}" alt="">'
            f'<div><div class="mba-coach__title">{esc(title)}</div><ul>{lis}</ul></div></aside>')


def empty_state(title: str, text: str = "") -> None:
    st.html(f'<div class="mba-state" role="status"><div class="mba-state__icon" aria-hidden="true">∅</div><div>'
            f'<div class="mba-state__title">{esc(title)}</div><div class="mba-state__text">{esc(text)}</div></div></div>')


def error_state(title: str, text: str = "") -> None:
    st.html(f'<div class="mba-state mba-state--error" role="alert"><div class="mba-state__icon" aria-hidden="true">!</div><div>'
            f'<div class="mba-state__title">{esc(title)}</div><div class="mba-state__text">{esc(text)}</div></div></div>')


def filter_summary(f) -> None:
    """Идэвхтэй (анхдагчаас өөр) шүүлтүүрийг чипээр харуулна; анхдагч төлөвт юу ч зурахгүй."""
    chips = []
    if f.teams:
        chips.append(("Баг", ", ".join(f.teams)))
    if f.positions:
        chips.append(("Байрлал", ", ".join(f.positions)))
    if f.import_status != "Бүгд":
        chips.append(("Тоглогч", f.import_status.lower()))
    if f.min_gp != 5:
        chips.append(("Доод хязгаар", f"{f.min_gp}+ тоглолт"))
    if not f.show_ci:
        chips.append(("Магадлалтай хүрээ", "нуусан"))
    if f.highlight_team:
        chips.append(("Онцолсон", f.highlight_team))
    if chips:
        from data_access import reset_filters  # data_access нь ui-г зөвхөн функц дотроос импортолдог
        with st.container(horizontal=True, vertical_alignment="center", gap="small", key="mba_chips"):
            st.html('<div class="mba-chips" aria-label="Идэвхтэй шүүлтүүр"><span class="mba-chips__label">Идэвхтэй шүүлтүүр:</span>'
                    + "".join(f'<span class="mba-badge mba-badge--soft">{esc(k)}: <b>{esc(v)}</b></span>' for k, v in chips)
                    + "</div>", width="content")
            st.button("Бүгдийг цэвэрлэх", on_click=reset_filters, type="tertiary", key="reset_filters",
                      icon=":material/close:", help="Бүх шүүлтүүрийг анхдагч төлөвт буцаана")


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
