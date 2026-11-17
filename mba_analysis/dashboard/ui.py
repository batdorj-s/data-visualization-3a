"""Бүх хуудсанд нэгэн хэв маягаар хэрэглэх UI хэсгүүд (лекц 10–11).

- page_header: хуудас юуг хариулах вэ (зорилгыг ойлгох, Norman-ий «зорилго» алхам)
- findings: гол дүгнэлтийг дээд хэсэгт (тайлбарлах, дүгнэх ачааллыг бууруулна)
- chart_note: график бүрийн доор төрөл, «хэрхэн унших», ямар дата, ямар файлаас (ойлголтын зөрүүг арилгана)
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
.mba-source { color: #64748B; font-size: 0.8rem; line-height: 1.5; margin: -0.6rem 0 1rem 0; }
.mba-source code { color: #475569; background: #F1F5F9; padding: 0 4px; border-radius: 4px; font-size: 0.78rem; }
.mba-chip { display: inline-block; padding: 2px 10px; margin: 0 6px 6px 0; border-radius: 999px;
            background: #EEF2FF; color: #1E3A8A; font-size: 0.85rem; }
@media (prefers-reduced-motion: reduce) { * { transition: none !important; animation: none !important; } }
</style>
"""


def inject_css() -> None:
    st.html(CSS)


def page_header(title: str, lead: str) -> None:
    st.title(title)
    st.html(f'<p class="mba-lead">{html.escape(lead)}</p>')


def findings(items: list[str], title: str = "Гол дүгнэлт") -> None:
    with st.container(border=True):
        st.markdown(f"**{title}**")
        st.markdown("\n".join(f"- {t}" for t in items))


# Датасетийн файлууд (mba_analysis/ хавтаснаас харьцангуй зам). Тайлан, баримт бичгийн D1–D11 хүснэгттэй ижил.
DATASETS = {
    "players": "data/processed/players_season.csv",
    "player_games": "data/processed/player_games.csv",
    "team_games": "data/processed/team_games.csv",
    "games": "data/processed/games.csv",
    "standings": "data/processed/standings_hist.csv",
    "team_meta": "data/processed/team_meta.csv",
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


def chart_note(how: str, data: str, *, kind: str, files: list[str]) -> None:
    """kind = графикийн төрлийн нэр; files = DATASETS-ийн түлхүүрүүд (доор саарлаар файлын нэрийг бичнэ)."""
    lines = [f"**График:** {kind}"] + ([f"**Хэрхэн унших:** {how}"] if how else [])
    st.caption("  \n".join(lines))
    paths = ", ".join(f"<code>{html.escape(DATASETS[k])}</code>" for k in files)
    st.html(f'<p class="mba-source">Дата: {html.escape(data)}<br>Файл: {paths}</p>')


def filter_summary(f) -> None:
    chips = [f"Улирал: {f.season.replace('-20', '–')}"]
    chips.append("Баг: " + (", ".join(f.teams) if f.teams else "бүгд"))
    chips.append("Байрлал: " + (", ".join(f.positions) if f.positions else "бүгд"))
    chips.append(f"Тоглогч: {f.import_status.lower()}")
    chips.append(f"{f.min_gp}+ тоглолт")
    if f.highlight_team:
        chips.append(f"Онцолсон: {f.highlight_team}")
    st.html("".join(f'<span class="mba-chip">{html.escape(c)}</span>' for c in chips))


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
