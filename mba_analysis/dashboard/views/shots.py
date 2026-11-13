import numpy as np
import pandas as pd
import streamlit as st

from data_access import current_filters, load
from plots import px_assist_network, px_game_flow, px_inplay_accuracy, px_shot_map, px_zone_bars
from src.inplay import REG_SEC, finalize, win_prob
from src.pbp import ZONES
from ui import chart_note, filter_summary, findings, page_header

f = current_filters()
season_txt = f.season.replace("-20", "–")
page_header("Шидэлт ба тоглолтын явц",
            "Хаанаас шидэх нь хамгийн үр ашигтай вэ, хэн хэнд дамжуулдаг вэ, тоглолт минут тутам хэрхэн өрнөсөн бэ.")
filter_summary(f)

ALL = "Бүгд"
shots_all = load("shots")
shots_season = shots_all[shots_all.season == f.season]
if f.import_status != "Бүгд":
    shots_season = shots_season[shots_season.is_import.astype(bool) == (f.import_status == "Гадаад")]
league_pps = float(shots_season[shots_season.location_ok].pts.mean())


def zone_summary(s: pd.DataFrame) -> pd.DataFrame:
    s = s[s.location_ok]
    z = s.groupby("zone").agg(n=("pts", "size"), pps=("pts", "mean")).reindex(ZONES).dropna().reset_index()
    return z.assign(share=z.n / z.n.sum())


zs = zone_summary(shots_season)
best = zs.loc[zs.pps.idxmax()] if len(zs) else None
worst = zs.loc[zs.pps.idxmin()] if len(zs) else None
minute = load("inplay_minute").set_index("minute")
findings([
    f"Хамгийн үр ашигтай бүс: **{best.zone}** — шидэлт бүрт {best.pps:.2f} оноо (лигийн дундаж {league_pps:.2f})."
    if best is not None else "Шидэлтийн дата алга.",
    (f"Хамгийн бага үр ашигтай: **{worst.zone}** — {worst.pps:.2f} оноо, гэвч нийт шидэлтийн {worst.share:.0%}-ийг эзэлдэг."
     if worst is not None else "Шидэлтийн дата алга."),
    f"Хагас дуусахад ялагчийг **{minute.loc[20, 'acc_model']:.0%}**, 35-р минутад **{minute.loc[35, 'acc_model']:.0%}** "
    "зөв таамаглах боломжтой.",
])


@st.fragment
def shot_section():
    st.subheader("Хаанаас шиддэг вэ")
    teams = sorted(shots_season.team.dropna().unique())
    c1, c2 = st.columns(2)
    default_team = f.highlight_team if f.highlight_team in teams else ALL
    team = c1.selectbox("Баг", [ALL] + teams, index=([ALL] + teams).index(default_team),
                        key=f"shot_team::{f.highlight_team}")
    s = shots_season if team == ALL else shots_season[shots_season.team == team]
    counts = s.player_name.value_counts()
    players = [ALL] + sorted(counts[counts >= 20].index)
    player = c2.selectbox("Тоглогч (20+ шидэлттэй)", players, key=f"shot_player::{team}")
    if player != ALL:
        s = s[s.player_name == player]
    who = player if player != ALL else (team if team != ALL else "Бүх лиг")
    left, right = st.columns([3, 2], gap="large")
    with left:
        st.plotly_chart(px_shot_map(s, league_pps, f"{who}: шидэлтийн газрын зураг"), width="stretch")
    with right:
        st.plotly_chart(px_zone_bars(zone_summary(s), league_pps), width="stretch")
    chart_note("Дөрвөлжин бүр 1 × 1 м талбай: том = олон шидэлт, улаан = шидэлт бүрт лигийн дунджаас их оноо, цэнхэр = бага. "
               "Сагс доод талд. Баруун талд нь 5 бүсээр нэгтгэсэн.",
               f"MBA тоглолтын хуудасны шидэлтийн байршил, {season_txt}, {len(s):,} шидэлт "
               "(байршил нь 2/3 онооны шошготой зөрсөн 4%-ийг хассан).")


@st.fragment
def assist_section():
    st.subheader("Хэн хэнд дамжуулдаг вэ")
    a = load("assists")
    a = a[(a.season == f.season) & a.passer.notna() & a.scorer.notna()]
    teams = sorted(a.team.dropna().unique())
    default = f.highlight_team if f.highlight_team in teams else a.team.value_counts().idxmax()
    c1, c2 = st.columns([2, 1])
    team = c1.selectbox("Баг", teams, index=teams.index(default), key=f"ast_team::{f.highlight_team}")
    min_n = c2.slider("Хамгийн багадаа хэдэн удаа", 1, 10, 4, key="ast_min")
    at = a[a.team == team]
    e = at.groupby(["passer", "scorer"]).size().rename("n").reset_index()
    e = e[e.n >= min_n]
    if e.empty:
        st.info("Энэ хязгаараар холбоос алга. Доод хязгаарыг бууруулна уу.")
        return
    inv = pd.concat([e.groupby("passer").n.sum(), e.groupby("scorer").n.sum()]).groupby(level=0).sum()
    imp = shots_all.drop_duplicates("player_name").set_index("player_name").is_import.to_dict()
    top = e.sort_values("n", ascending=False).iloc[0]
    st.plotly_chart(px_assist_network(e, inv, imp, f"{team}: {top.passer} → {top.scorer} хамгийн олон ({top.n})"),
                    width="stretch")
    chart_note("Цэг = тоглогч (том = олон дамжуулалтад оролцсон; улаан-улбар = гадаад, цэнхэр = дотоод), "
               "шугам = нэг нь нөгөөдөө дамжуулж, тэр нь оносон (зузаан = олон удаа). Шугам дээр хулганаа аваачвал тоог харуулна.",
               f"MBA тоглолтын явцын бичлэг, {season_txt}; дамжуулалтын 87%-ийг шидэлттэй нь холбож чадсан.")


@st.fragment
def flow_section():
    st.subheader("Тоглолт минут тутам")
    gl = load("game_list")
    gl = gl[gl.season == f.season].sort_values("date", ascending=False)
    if f.highlight_team:
        gl = gl[(gl.home_team == f.highlight_team) | (gl.away_team == f.highlight_team)]
    if gl.empty:
        st.info("Энэ шүүлтүүрт тоглолт алга.")
        return
    labels = {r.game_id: f"{r.date}: {r.home_team} {r.home_pts}–{r.away_pts} {r.away_team} ({r.lead_changes} удаа солигдсон)"
              for r in gl.itertuples()}
    default = int(gl.loc[gl.lead_changes.idxmax(), "game_id"])
    gid = st.selectbox("Тоглолт", list(labels), index=list(labels).index(default), format_func=labels.get,
                       key=f"flow_game::{f.season}::{f.highlight_team}",
                       help="Анхдагчаар тэргүүлэгч хамгийн олон солигдсон тоглолт сонгогдоно")
    g = gl.set_index("game_id").loc[gid]
    flow = load("game_flow")
    flow = flow[flow.game_id == gid].sort_values("elapsed")
    p = load("inplay_params").iloc[0]
    params = {"intercept": p.intercept, "coef": {k: p[k] for k in ("margin", "margin_scaled", "elo_diff", "elo_x_time")}}
    wp = finalize(win_prob(params, flow.margin, np.clip(REG_SEC - flow.elapsed, 0, None), g.elo_pre_home - g.elo_pre_away),
                  flow.margin.iloc[-1])
    st.plotly_chart(px_game_flow(flow, wp, g.home_team, g.away_team), width="stretch")
    chart_note("Дээр: онооны зөрүү (улаан-улбар = гэрийн баг тэргүүлсэн, цэнхэр = зочин баг). Доор: тухайн мөчид загварын "
               "тооцсон гэрийн баг ялах магадлал — зөрүү том, хугацаа бага байх тусам 0% эсвэл 100% руу ойртоно.",
               "MBA тоглолтын явцын бичлэг; магадлалын загварыг 252 тоглолтын 10,080 мөчөөр сургасан.")


shot_section()
assist_section()
flow_section()
st.subheader("Ялагчийг хэзээнээс таамаглаж болох вэ")
st.plotly_chart(px_inplay_accuracy(load("inplay_minute").reset_index(drop=True), f.show_ci), width="stretch")
chart_note("Тоглолтын минут бүрд «одоо хэн ялах вэ» гэж таамаглахад хэдэн хувь нь зөв байсан. Загвар энгийн «тэргүүлж буй нь "
           "ялна» дүрмээс зөв хувиар илүү биш ч магадлалаар (жишээ нь 78%) хэр итгэлтэйг хэлж өгдөг.",
           "252 тоглолт; тоглолтоор нь бүлэглэн 5 хэсэгт хувааж шалгасан (нэг тоглолт сургалт, тест хоёрт зэрэг ордоггүй).")
