import streamlit as st

from data_access import current_filters, load, team_key_of
from plots import px_elo, px_four_factors, px_pareto

f = current_filters()
st.title("Багууд")
tg_all = load("team_games")
tg = tg_all[tg_all.season == f.season]


@st.fragment
def standings():
    reg = tg[tg.phase == "regular"]
    table = reg.groupby("team").agg(Тоглолт=("win", "size"), Ялалт=("win", "sum"), Оноо=("PTS", "mean"),
                                    Алдсан=("opp_pts", "mean"), Net=("net", "mean"), eFG=("efg", "mean"))
    table["Ялалтын %"] = table.Ялалт / table.Тоглолт
    table = table.sort_values("Ялалтын %", ascending=False).round(3)
    st.dataframe(table, width="stretch",
                 column_config={"Ялалтын %": st.column_config.ProgressColumn(format="percent", min_value=0, max_value=1)})


@st.fragment
def team_pareto():
    teams = sorted(tg.team.unique())
    default = f.highlight_team if f.highlight_team in teams else teams[0]
    team = st.selectbox("Багийн Pareto", teams, index=teams.index(default), key="team_pareto_team")
    pt = load("pareto_team")
    pt = pt[(pt.season == f.season) & (pt.team_key == team_key_of(team))]
    st.plotly_chart(px_pareto(pt, False, f"{team}: багийн оноо цөөн тоглогчоос хэр хамаардаг вэ"),
                    width="stretch")


@st.fragment
def compare():
    teams = sorted(tg.team.unique())
    a, b = st.columns(2)
    t1 = a.selectbox("Баг 1", teams, index=0, key="cmp1")
    t2 = b.selectbox("Баг 2", teams, index=min(1, len(teams) - 1), key="cmp2")
    cols = ["PTS", "opp_pts", "efg", "tov_pct", "orb_pct", "ftr", "ortg", "drtg", "net"]
    st.dataframe(tg[tg.team.isin([t1, t2])].groupby("team")[cols].mean().round(3).T, width="stretch")


standings()
st.plotly_chart(px_four_factors(tg, f.highlight_team), width="stretch")
left, right = st.columns(2)
with left:
    team_pareto()
with right:
    st.plotly_chart(px_elo(load("games"), f.highlight_team), width="stretch")
st.subheader("Хоёр багийг харьцуулах")
compare()
