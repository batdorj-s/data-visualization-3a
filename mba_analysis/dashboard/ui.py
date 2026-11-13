"""Бүх хуудсанд нэгэн хэв маягаар хэрэглэх UI хэсгүүд (лекц 10–11).

- page_header: хуудас юуг хариулах вэ (зорилгыг ойлгох, Norman-ий «зорилго» алхам)
- findings: гол дүгнэлтийг дээд хэсэгт (тайлбарлах, дүгнэх ачааллыг бууруулна)
- chart_note: график бүрийн доор «хэрхэн унших» ба «ямар дата» (ойлголтын зөрүүг арилгана)
- filter_summary: идэвхтэй шүүлтүүрийг харуулж, санах ачааллыг бууруулна (шууд санал хүсэлт)
"""

import html

import streamlit as st

CSS = """
<style>
[data-testid="stMetricValue"], [data-testid="stDataFrame"] { font-variant-numeric: tabular-nums; }
[data-testid="stMarkdownContainer"] p, [data-testid="stMarkdownContainer"] li { line-height: 1.6; }
[data-testid="stCaptionContainer"] { line-height: 1.5; color: #475569; }
.mba-lead { font-size: 1.05rem; color: #334155; max-width: 75ch; margin: -0.4rem 0 0.8rem 0; }
.mba-chip { display: inline-block; padding: 2px 10px; margin: 0 6px 6px 0; border-radius: 999px;
            background: #EEF2FF; color: #1E3A8A; font-size: 0.85rem; }
@media (prefers-reduced-motion: reduce) { * { transition: none !important; animation: none !important; } }
</style>
"""


def inject_css() -> None:
    st.html(CSS)


def page_header(title: str, lead: str) -> None:
    st.title(title)
    st.html(f'<p class="mba-lead">{lead}</p>')


def findings(items: list[str], title: str = "Гол дүгнэлт") -> None:
    with st.container(border=True):
        st.markdown(f"**{title}**")
        st.markdown("\n".join(f"- {t}" for t in items))


def chart_note(how: str, data: str) -> None:
    st.caption(f"**Хэрхэн унших:** {how}  \n**Дата:** {data}")


def filter_summary(f) -> None:
    chips = [f"Улирал: {f.season.replace('-20', '–')}"]
    chips.append("Баг: " + (", ".join(f.teams) if f.teams else "бүгд"))
    chips.append("Байрлал: " + (", ".join(f.positions) if f.positions else "бүгд"))
    chips.append(f"Тоглогч: {f.import_status.lower()}")
    chips.append(f"{f.min_gp}+ тоглолт")
    if f.highlight_team:
        chips.append(f"Онцолсон: {f.highlight_team}")
    st.html("".join(f'<span class="mba-chip">{html.escape(c)}</span>' for c in chips))
