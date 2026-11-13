import streamlit as st

from data_access import current_filters, latest_elo, load, team_key_of
from plots import px_elo, px_four_factors, px_pareto
from ui import chart_note, filter_summary, findings, page_header

f = current_filters()
season_txt = f.season.replace("-20", "–")
page_header("Багууд", "Аль баг яагаад ялж байна вэ: байр, ялалтын 4 хүчин зүйл, хүчний онооны явц, хоёр багийн харьцуулалт.")
filter_summary(f)
tg_all = load("team_games")
tg = tg_all[tg_all.season == f.season]
reg = tg[tg.phase == "regular"]

table = reg.groupby("team").agg(Тоглолт=("win", "size"), Ялалт=("win", "sum"), Оноо=("PTS", "mean"),
                                Алдсан=("opp_pts", "mean"), Зөрүү=("net", "mean"), Оновч=("efg", "mean"))
table["Ялалтын хувь"] = table.Ялалт / table.Тоглолт
table = table.sort_values("Ялалтын хувь", ascending=False)
elo = latest_elo(f.season)
if len(table):
    best_efg = table.Оновч.idxmax()
    findings([
        f"Тэргүүлэгч: **{table.index[0]}** ({table['Ялалтын хувь'].iloc[0]:.0%} ялалт).",
        f"Шидэлтийн оновчоор лигт тэргүүлэх баг: **{best_efg}** ({table.Оновч.max():.0%}).",
        f"Одоогийн хүчний оноогоор хамгийн хүчтэй: **{elo.idxmax()}** ({elo.max():.0f})." if len(elo) else
        "Хүчний оноо алга.",
    ])


@st.fragment
def standings():
    st.subheader("Байр")
    st.dataframe(table.round(2), width="stretch",
                 column_config={"Ялалтын хувь": st.column_config.ProgressColumn(format="percent", min_value=0, max_value=1),
                                "Оновч": st.column_config.NumberColumn(format="percent"),
                                "Зөрүү": st.column_config.NumberColumn(help="Дунджаар хэдэн оноогоор ялсан (+) эсвэл ялагдсан (−)")})
    chart_note("Ялалтын хувиар эрэмбэлсэн. Оноо/Алдсан = тоглолтын дундаж; Зөрүү эерэг бол баг ихэвчлэн давуу тоглодог.",
               f"тоглолтын хайрцаг оноо, {season_txt} улирлын үндсэн шат, {reg.team.nunique()} баг.")


@st.fragment
def team_pareto():
    teams = sorted(tg.team.unique())
    default = f.highlight_team if f.highlight_team in teams else teams[0]
    team = st.selectbox("Онооны хуваарийг харах баг", teams, index=teams.index(default),
                        key=f"team_pareto_team::{f.highlight_team}")
    pt = load("pareto_team")
    pt = pt[(pt.season == f.season) & (pt.team_key == team_key_of(team))]
    st.plotly_chart(px_pareto(pt, False, f"{team}: оноо цөөн тоглогчоос хэр хамаардаг вэ"), width="stretch")
    chart_note("Багана = тоглогчийн улирлын нийт оноо. Хар шугам 80%-д цөөн тоглогчоор хүрвэл баг цөөн од тоглогчоос "
               "хамааралтай — тэр тоглогч гэмтвэл эрсдэлтэй.", f"тоглолт бүрийн оноо, {season_txt}, {len(pt)} тоглогч.")


@st.fragment
def compare():
    teams = sorted(tg.team.unique())
    a, b = st.columns(2)
    t1 = a.selectbox("Баг 1", teams, index=0, key="cmp1")
    t2 = b.selectbox("Баг 2", teams, index=min(1, len(teams) - 1), key="cmp2")
    names = {"PTS": "Авсан оноо", "opp_pts": "Алдсан оноо", "efg": "Оновч (3 оноог тооцсон)", "tov_pct": "Бөмбөг алдалт",
             "orb_pct": "Довтолгооны самбар", "ftr": "Торгууль авалт", "ortg": "100 довтолгоонд авсан оноо",
             "drtg": "100 довтолгоонд алдсан оноо", "net": "Онооны зөрүү"}
    st.dataframe(tg[tg.team.isin([t1, t2])].groupby("team")[list(names)].mean().round(3).rename(columns=names).T,
                 width="stretch")
    chart_note("Мөр бүр 1 үзүүлэлтийн тоглолтын дундаж. Бөмбөг алдалт ба алдсан оноо бага байх нь сайн, бусад нь их байх нь сайн.",
               f"тоглолтын хайрцаг оноо, {season_txt}.")


standings()
st.plotly_chart(px_four_factors(tg, f.highlight_team), width="stretch")
chart_note("Баг бүрийг лигийн дундажтай (0) харьцуулав: цэнхэр = дунджаас сайн, улаан-улбар = сул, хар = онцолсон баг. "
           "Эдгээр 4 үзүүлэлт ялалтыг хамгийн их тайлбарладаг; оновч нь хамгийн чухал нь.",
           f"тоглолтын хайрцаг оноо, {season_txt} улирлын үндсэн шат.")
left, right = st.columns(2, gap="large")
with left:
    team_pareto()
with right:
    st.plotly_chart(px_elo(load("games"), f.highlight_team), width="stretch")
    chart_note("Хүчний оноо тоглолт бүрийн дараа шинэчлэгдэнэ: хүчтэй багийг ялвал их нэмэгдэнэ. 1500 = дундаж. "
               "Зүүн талд «Онцлох баг» сонговол тэр багийн шугам тодорно.",
               "2025–26 ба 2026–27 улирлын бүх тоглолтын үр дүн.")
st.subheader("Хоёр багийг харьцуулах")
compare()
