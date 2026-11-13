import numpy as np
import streamlit as st

from data_access import DATA, current_filters, import_share_ci, latest_elo, load, snapshot, team_key_of
from plots import px_fan, px_map, px_pareto
from ui import chart_note, filter_summary, findings, page_header

f = current_filters()
season_txt = f.season.replace("-20", "–") + (" (явагдаж буй)" if f.season == "2026-2027" else "")
page_header("MBA лигийн тойм",
            f"Монголын сагсан бөмбөгийн дээд лигийн {season_txt} улирлыг нэг дороос: хэн оноо авдаг, "
            "аль баг хүчтэй, үр дүн хэр найдвартай вэ.")
filter_summary(f)

games = load("games")
g = games[games.season == f.season]
share, lo, hi = import_share_ci(f.season)
pareto_df = load("pareto_league")
pareto_df = pareto_df[pareto_df.season == f.season]
k80 = int(np.argmax(pareto_df.sort_values("rank").cum_share.to_numpy() >= 0.8)) + 1 if len(pareto_df) else 0
elo = latest_elo(f.season)
findings([
    f"Гадаад тоглогчид лигийн нийт онооны **{share:.0%}**-ийг авдаг"
    + (f" (бодит хувь {lo:.0%}–{hi:.0%} хооронд байх магадлалтай)." if f.show_ci else "."),
    f"Тоглогчдын **{k80 / max(len(pareto_df), 1):.0%}** буюу {k80} тоглогч л лигийн онооны 80%-ийг авдаг."
    if k80 else "Онооны хуваарийг тооцох дата алга.",
    f"Одоогийн хамгийн хүчтэй баг: **{elo.idxmax()}** (хүчний оноо {elo.max():.0f}; 1500 = дундаж)."
    if len(elo) else "Багийн хүчний оноо алга.",
])


@st.fragment
def kpis():
    ps = load("players")
    p = ps[(ps.season == f.season) & (ps.GP >= f.min_gp)]
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Тоглолт", f"{len(g)}", help="Үндсэн шат ба плей-офф", border=True)
    c2.metric(f"Тоглогч ({f.min_gp}+ тоглолт)", f"{len(p)}", border=True)
    c3.metric("Гадаадын онооны хувь", f"{share:.0%}", border=True,
              help=f"95% магадлалтай хүрээ {lo:.0%}–{hi:.0%}" if f.show_ci else None)
    c4.metric("Тоглолтын нийт оноо", f"{(g.home_pts + g.away_pts).mean():.0f}", border=True,
              help="Нэг тоглолтод хоёр баг нийлээд дунджаар авсан оноо")


@st.fragment
def pareto():
    st.plotly_chart(px_pareto(pareto_df, f.show_ci, "Цөөн тоглогч лигийн онооны ихэнхийг авдаг"), width="stretch")
    chart_note("Багана бүр 1 тоглогчийн улирлын нийт оноо, ихээс нь эрэмбэлсэн (улаан-улбар = гадаад, цэнхэр = дотоод). "
               "Хар шугам эхний N тоглогчийн нийлбэр хувийг заана; тасархай 80%-ийн шугамтай огтлолцох цэгийг хараарай.",
               f"тоглолт бүрийн хайрцаг оноо, {season_txt} улирлын үндсэн шат, {len(pareto_df)} тоглогч.")


@st.fragment
def fan():
    tg = load("team_games")
    tg = tg[tg.season == f.season]
    teams = sorted(tg.team.unique())
    default = f.highlight_team if f.highlight_team in teams else tg.groupby("team").winpct.last().idxmax()
    team = st.selectbox("Ялалтын явцыг харах баг", teams, index=teams.index(default),
                        key=f"overview_fan_team::{f.highlight_team}",
                        help="Зүүн талын «Онцлох баг»-ийг сонговол энд автоматаар солигдоно")
    st.plotly_chart(px_fan(tg, team_key_of(team), f.show_ci), width="stretch")
    chart_note("Улаан-улбар шугам = сонгосон багийн тухайн өдөр хүртэлх ялалтын хувь, саарал = бусад баг. "
               "Сүүдэр нь багийн жинхэнэ хүч байж болох хүрээ: цөөн тоглолтын дараа өргөн, улирлын эцэст нарийсна.",
               f"тоглолтын үр дүн, {season_txt} улирлын үндсэн шат, {tg.team.nunique()} баг.")


kpis()
left, right = st.columns([3, 2], gap="large")
with left:
    pareto()
with right:
    st.plotly_chart(px_map(load("team_meta"), load("standings"), DATA / "mng_adm1.geojson", f.season),
                    width="stretch")
    chart_note("Тойрог бүр 1 баг; том тойрог = өндөр ялалтын хувь. Улаан-улбар = Улаанбаатар, цэнхэр = орон нутаг.",
               "багийн хот — Wikipedia; ялалт — MBA статистик; аймгийн хил — geoBoundaries.")
fan()
st.caption(f"Дата татсан огноо: {snapshot()}. Нэр томьёоны тайлбарыг «Нэр томьёо» хуудаснаас үзнэ үү.")
