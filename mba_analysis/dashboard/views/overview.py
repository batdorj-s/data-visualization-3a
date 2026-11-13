import streamlit as st

from data_access import DATA, current_filters, import_share_ci, load, snapshot, team_key_of
from plots import px_fan, px_map, px_pareto

f = current_filters()
st.title("MBA лигийн гүйцэтгэлийн шинжилгээ")
st.caption(f"Snapshot: {snapshot()} · Улирал: {f.season.replace('-20', '–')}"
           + (" (явцын)" if f.season == "2026-2027" else ""))


@st.fragment
def kpis():
    games = load("games")
    g = games[games.season == f.season]
    ps = load("players")
    p = ps[(ps.season == f.season) & (ps.GP >= f.min_gp)]
    share, lo, hi = import_share_ci(f.season)
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Тоглолт", f"{len(g)}", help="Энгийн улирал + playoff")
    c2.metric("Тоглогч (GP шүүлтүүрээр)", f"{len(p)}")
    c3.metric("Import тоглогчийн онооны хувь", f"{share:.0%}",
              help=f"95% CI {lo:.0%}–{hi:.0%} (тоглолтоор bootstrap)" if f.show_ci else None)
    c4.metric("Нэг тоглолтын дундаж нийт оноо", f"{(g.home_pts + g.away_pts).mean():.1f}")
    if f.show_ci:
        st.caption(f"Import онооны хувийн 95% итгэх интервал: {lo:.0%}–{hi:.0%}")


@st.fragment
def pareto():
    df = load("pareto_league")
    df = df[df.season == f.season]
    st.plotly_chart(px_pareto(df, f.show_ci, "Pareto: цөөн тоглогч лигийн онооны ихэнхийг авдаг"),
                    width="stretch")


@st.fragment
def fan():
    tg = load("team_games")
    tg = tg[tg.season == f.season]
    teams = sorted(tg.team.unique())
    default = f.highlight_team if f.highlight_team in teams else tg.groupby("team").winpct.last().idxmax()
    team = st.selectbox("Баг (fan chart)", teams, index=teams.index(default), key=f"overview_fan_team::{f.highlight_team}")
    st.plotly_chart(px_fan(tg, team_key_of(team), f.show_ci), width="stretch")


kpis()
left, right = st.columns([3, 2])
with left:
    pareto()
with right:
    st.plotly_chart(px_map(load("team_meta"), load("standings"), DATA / "mng_adm1.geojson", f.season),
                    width="stretch")
fan()
