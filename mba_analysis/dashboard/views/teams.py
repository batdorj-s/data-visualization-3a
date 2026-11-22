import streamlit as st

import coach

from data_access import current_filters, latest_elo, load, team_info, team_key_of, team_logos
from plots import px_elo, px_four_factors, px_pareto
from ui import (chart_note, coach as coach_box, compare_table, filter_summary, findings, page_header,
                pareto_who, section, show_chart, team_header)

f = current_filters()
season_txt = f.season.replace("-20", "–")
page_header("Багууд", "Аль баг, яагаад ялж байна вэ? Багийн профайл, байр, ялалтын 4 хүчин зүйл, хүчний онооны явц ба "
            "хоёр багийн харьцуулалт.", eyebrow=f"Багууд · {season_txt}")
filter_summary(f)
logos = team_logos()
info = team_info()
tg_all = load("team_games")
tg = tg_all[tg_all.season == f.season]
reg = tg[tg.phase == "regular"]

table = reg.groupby("team").agg(Тоглолт=("win", "size"), Ялалт=("win", "sum"), Оноо=("PTS", "mean"),
                                Алдсан=("opp_pts", "mean"), Зөрүү=("net", "mean"), Оновч=("efg", "mean"))
table["Хожигдол"] = table.Тоглолт - table.Ялалт
table["Ялалтын хувь"] = table.Ялалт / table.Тоглолт
table = table.sort_values(["Ялалтын хувь", "Зөрүү"], ascending=False)
table.insert(0, "Байр", range(1, len(table) + 1))
elo = latest_elo(f.season)
if len(table):
    best_efg = table.Оновч.idxmax()
    findings([
        f"Тэргүүлэгч: **{table.index[0]}** ({table['Ялалтын хувь'].iloc[0]:.0%} ялалт).",
        f"Шидэлтийн оновчоор лигт тэргүүлэх баг: **{best_efg}** ({table.Оновч.max():.0%}).",
        f"Одоогийн хүчний оноогоор хамгийн хүчтэй: **{elo.idxmax()}** ({elo.max():.0f})." if len(elo) else
        "Хүчний оноо алга.",
    ])

teams = list(table.index) or sorted(tg.team.unique())
default = f.highlight_team if f.highlight_team in teams else teams[0]


@st.fragment
def profile():
    section("Багийн профайл", "Баг сонгоход доорх онооны хуваарь ба хүчний онооны явц тухайн багийнх болж солигдоно.")
    team = st.selectbox("Баг сонгох", teams, index=teams.index(default), key=f"team_profile::{f.highlight_team}",
                        help="Зүүн талын «Онцлох баг»-ийг сонговол энд автоматаар солигдоно")
    r = table.loc[team] if team in table.index else None
    city = info.home_city.get(team, "") if "home_city" in info else ""
    stats = []
    if r is not None:
        stats = [("Байр", f"{int(r.Байр)}/{len(table)}"), ("Я–Х", f"{int(r.Ялалт)}–{int(r.Хожигдол)}"),
                 ("Ялалт", f"{r['Ялалтын хувь']:.0%}"), ("Онооны зөрүү", f"{r.Зөрүү:+.1f}")]
    if team in elo.index:
        stats.append(("Хүчний оноо", f"{elo[team]:.0f}"))
    team_header(team, logos.get(team), f"{city} · {season_txt} улирал, үндсэн шат" if city else f"{season_txt} улирал",
                stats)
    left, right = st.columns(2, gap="large")
    with left:
        pt = load("pareto_team")
        pt = pt[(pt.season == f.season) & (pt.team_key == team_key_of(team))]
        show_chart(px_pareto(pt, False, f"{team}: онооны хуваарь"), width="stretch")
        chart_note("Багана = тоглогчийн улирлын нийт оноо. Хар шугам = 1-р байрын тоглогчоос тухайн байр хүртэлх тоглогчдын "
                   "оноо багийн нийт онооны хэдэн хувь вэ. Хар шугам 80%-д цөөн тоглогчоор хүрвэл баг цөөн од тоглогчоос "
                   "хамааралтай — тэр тоглогч гэмтвэл эрсдэлтэй.", f"тоглолт бүрийн оноо, {season_txt}, {len(pt)} тоглогч.",
                   kind="Парето график (оноогоор эрэмбэлсэн багана + нийлбэр хувийн шугам)", files=["player_games"])
        coach_box(coach.team_pareto(pt, team))
        pareto_who(pt, label="багийн")
    with right:
        show_chart(px_elo(load("games"), team), width="stretch")
        chart_note("Хүчний оноо тоглолт бүрийн дараа шинэчлэгддэг: хүчтэй багийг ялбал их нэмэгдэнэ. 1500 = дундаж. "
                   "Сонгосон багийн шугам тод, бусад нь саарал.",
                   "2025–26 ба 2026–27 улирлын бүх тоглолтын үр дүн.", kind="Шугаман график (line chart)", files=["games"])
        coach_box(coach.elo(load("games"), team, f.season))


def standings():
    section("Байрын хүснэгт", "Үндсэн шат. Баганын нэр дээр дарж эрэмбийг өөрчилнө.")
    show = table.reset_index().rename(columns={"team": "Баг"})
    show.insert(1, "Лого", show["Баг"].map(logos))
    cols = ["Байр", "Лого", "Баг", "Тоглолт", "Ялалт", "Хожигдол", "Ялалтын хувь", "Оноо", "Алдсан", "Зөрүү", "Оновч"]
    st.dataframe(show[cols].round(2), width="stretch", hide_index=True,
                 column_config={"Байр": st.column_config.NumberColumn(width="small", format="%d"),
                                "Лого": st.column_config.ImageColumn("", width="small"),
                                "Баг": st.column_config.TextColumn(width="medium"),
                                "Ялалтын хувь": st.column_config.ProgressColumn(format="percent", min_value=0, max_value=1),
                                "Оноо": st.column_config.NumberColumn(help="Тоглолтод дунджаар авсан оноо", format="%.1f"),
                                "Алдсан": st.column_config.NumberColumn(help="Тоглолтод дунджаар алдсан оноо", format="%.1f"),
                                "Оновч": st.column_config.NumberColumn(format="percent",
                                                                        help="3 онооны шидэлтийг 1.5 дахин тооцсон оновч"),
                                "Зөрүү": st.column_config.NumberColumn(format="%+.1f",
                                                                        help="Дунджаар хэдэн оноогоор ялсан (+) эсвэл ялагдсан (−)")})
    chart_note("Ялалтын хувиар, тэнцвэл онооны зөрүүгээр эрэмбэлсэн. Оноо/Алдсан = тоглолтын дундаж; Зөрүү эерэг бол баг "
               "ихэвчлэн давуу тоглодог.", f"тоглолтын хайрцаг оноо, {season_txt} улирлын үндсэн шат, {len(table)} баг; "
               "лого — MBA-ийн албан ёсны сайт.", kind="Хүснэгт (байрын хүснэгт)", files=["team_games", "team_logos"])
    coach_box(coach.standings_table(table))


@st.fragment
def compare():
    section("Хоёр багийг харьцуулах", "Ногоон нүд = тухайн үзүүлэлтээр давуу баг.")
    a, b = st.columns(2)
    t1 = a.selectbox("Баг 1", teams, index=0, key="cmp1")
    t2 = b.selectbox("Баг 2", teams, index=min(1, len(teams) - 1), key="cmp2")
    m = tg[tg.team.isin([t1, t2])].groupby("team").mean(numeric_only=True)
    if t1 == t2 or t1 not in m.index or t2 not in m.index:
        st.info("Харьцуулахын тулд хоёр өөр баг сонгоно уу.")
        return
    spec = [("Авсан оноо", "тоглолтын дундаж", "PTS", "{:.1f}", True), ("Алдсан оноо", "бага нь сайн", "opp_pts", "{:.1f}", False),
            ("Онооны зөрүү", "тоглолтын дундаж", "net", "{:+.1f}", True),
            ("Оновч", "3 оноог 1.5 дахин тооцсон", "efg", "{:.1%}", True),
            ("Бөмбөг алдалт", "довтолгооны хэдэн хувьд, бага нь сайн", "tov_pct", "{:.1%}", False),
            ("Довтолгооны самбар", "боломжит самбарын хувь", "orb_pct", "{:.1%}", True),
            ("Торгууль авалт", "шидэлт тутамд торгууль", "ftr", "{:.2f}", True),
            ("Довтолгооны үр ашиг", "100 довтолгоонд авсан оноо", "ortg", "{:.1f}", True),
            ("Хамгаалалтын үр ашиг", "100 довтолгоонд алдсан оноо, бага нь сайн", "drtg", "{:.1f}", False)]
    rows = [(lab, note, float(m.loc[t1, c]), float(m.loc[t2, c]), fmt, hb) for lab, note, c, fmt, hb in spec]
    compare_table(t1, t2, rows, logos)
    chart_note("Мөр бүр 1 үзүүлэлтийн тоглолтын дундаж (үндсэн шат ба плей-офф). Бөмбөг алдалт, алдсан оноо, хамгаалалтын "
               "үр ашиг бага байх нь сайн, бусад нь их байх нь сайн.", f"тоглолтын хайрцаг оноо, {season_txt}.",
               kind="Харьцуулах хүснэгт", files=["team_games", "team_logos"])
    coach_box(coach.compare(t1, t2, rows))


profile()
standings()
section("Ялалтын 4 хүчин зүйл", "Ялалтыг хамгийн их тайлбарладаг 4 үзүүлэлтээр баг бүрийг лигийн дундажтай харьцуулав.")
show_chart(px_four_factors(tg, f.highlight_team), width="stretch")
chart_note("Баг бүрийг лигийн дундажтай (0) харьцуулав: цэнхэр = дунджаас сайн, улаан-улбар = сул, хар = онцолсон баг. "
           "Эдгээр 4 үзүүлэлт ялалтыг хамгийн их тайлбарладаг бөгөөд ерөнхийдөө оновч хамгийн чухал нь.",
           f"тоглолтын хайрцаг оноо, {season_txt} улирлын үндсэн шат.",
           kind="Хэвтээ багана график, дунджаас хазайлт (diverging bar chart)", files=["team_games"])
coach_box(coach.four_factors(tg, f.highlight_team))
compare()
