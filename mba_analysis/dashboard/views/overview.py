import numpy as np
import streamlit as st

import coach

from data_access import DATA, SEASONS, current_filters, import_share_ci, latest_elo, load, team_key_of, team_logos
from plots import px_fan, px_map, px_pareto
from ui import (chart_note, coach as coach_box, findings, page_header, pareto_who,
                section, show_chart, standings_board, stat_cards)

f = current_filters()
season_txt = f.season.replace("-20", "–") + (" (явагдаж буй)" if f.season == "2026-2027" else "")
page_header("Лигийн тойм",
            f"Монголын сагсан бөмбөгийн дээд лигийн {season_txt} улирлын тойм: хэн оноо авдаг, "
            "аль баг хүчтэй, үр дүн хэр найдвартай вэ?", eyebrow=f"Тойм · {season_txt}")

logos = team_logos()
games = load("games")
g = games[games.season == f.season]
share, lo, hi = import_share_ci(f.season)
pareto_df = load("pareto_league")
pareto_df = pareto_df[pareto_df.season == f.season]
k80 = int(np.argmax(pareto_df.sort_values("rank").cum_share.to_numpy() >= 0.8)) + 1 if len(pareto_df) else 0
elo = latest_elo(f.season)
tg = load("team_games")
tg = tg[tg.season == f.season]
reg = tg[tg.phase == "regular"]
table = (reg.groupby("team").agg(W=("win", "sum"), G=("win", "size"), net=("net", "mean"))
         .assign(L=lambda d: d.G - d.W, pct=lambda d: d.W / d.G).sort_values(["pct", "net"], ascending=False))

ps = load("players")
p = ps[(ps.season == f.season) & (ps.GP >= f.min_gp)]
game_pts = (g.home_pts + g.away_pts).mean()

# Өмнөх улиралтай харьцуулалт: тоглолтын тоо биш, харьцаа/дунджийг л харьцуулна (2026–27 дуусаагүй).
# 2025–26-ийн өмнөх улирлын тоглолт бүрийн дата алга (2023–24 зөвхөн багийн байр) тул тэр үед тэмдэг зурахгүй.
prev = SEASONS[SEASONS.index(f.season) - 1] if SEASONS.index(f.season) > 0 else None
share_d = pts_d = None
if prev:
    prev_txt = prev.replace("-20", "–")
    prev_share = import_share_ci(prev)[0]
    gp = games[games.season == prev]
    prev_pts = (gp.home_pts + gp.away_pts).mean()

    def _dir(d: float, eps: float) -> str:
        return "up" if d > eps else "down" if d < -eps else "flat"
    dp = (share - prev_share) * 100
    share_d = (f"{dp:+.1f} пункт", _dir(dp, 0.5), f"{prev_txt} улиралд {prev_share:.0%} байсан")
    dpts = game_pts - prev_pts
    pts_d = (f"{dpts:+.1f}", _dir(dpts, 0.5), f"{prev_txt} улиралд {prev_pts:.0f} байсан")
stat_cards([
    ("Тоглолт", f"{len(g)}", "үндсэн шат ба плей-офф"),
    (f"Тоглогч ({f.min_gp}+ тоглолт)", f"{len(p)}", f"{int(p.is_import.astype(bool).sum())} гадаад · "
                                                    f"{int((~p.is_import.astype(bool)).sum())} дотоод"),
    ("Гадаадын оноо", f"{share:.0%}", f"95% хүрээ {lo:.0%}–{hi:.0%}" if f.show_ci else "лигийн нийт онооноос",
     "Лигийн нийт онооны хэдэн хувийг гадаад тоглогч авсан", None, share_d),
    ("Тоглолтын оноо", f"{game_pts:.0f}", "хоёр баг нийлээд, дунджаар", None, None, pts_d),
    ("Тэргүүлэгч", table.index[0] if len(table) else "—",
     f"{int(table.W.iloc[0])}–{int(table.L.iloc[0])}, {table.pct.iloc[0]:.0%} ялалт" if len(table) else None, None,
     (table.index[0], logos.get(table.index[0])) if len(table) else None),
], accent_first=False)

findings([
    f"Гадаад тоглогчид лигийн нийт онооны **{share:.0%}**-ийг авдаг"
    + (f" (бодит хувь {lo:.0%}–{hi:.0%} хооронд байх магадлалтай)." if f.show_ci else "."),
    f"Лигийн онооны 80%-ийг хамгийн их оноо авсан **{k80}** тоглогч (нийт тоглогчдын {k80 / max(len(pareto_df), 1):.0%}) "
    "авдаг." if k80 else "Онооны хуваарийг тооцох дата алга.",
    f"Одоогийн хамгийн хүчтэй баг: **{elo.idxmax()}** (хүчний оноо {elo.max():.0f}; 1500 = дундаж)."
    if len(elo) else "Багийн хүчний оноо алга.",
])


@st.fragment
def pareto():
    show_chart(px_pareto(pareto_df, f.show_ci, "Цөөн тоглогч лигийн онооны ихэнхийг авдаг"), width="stretch")
    chart_note("Багана бүр 1 тоглогчийн улирлын нийт оноо, ихээс нь эрэмбэлсэн (улаан-улбар = гадаад, цэнхэр = дотоод). "
               "Хар шугам = 1-р байрын тоглогчоос тухайн байр хүртэлх тоглогчдын оноог нэмээд лигийн нийт онооны хэдэн хувь "
               "болохыг заана. Жишээ нь шугам 10 дээр 30% бол хамгийн их оноотой 10 тоглогч лигийн онооны 30%-ийг авсан. "
               "Хар шугам 80%-ийн тасархай шугамтай огтлолцох цэг = онооны 80%-ийг авсан тоглогчдын тоо.",
               f"тоглолт бүрийн хайрцаг оноо, {season_txt} улирлын үндсэн шат, {len(pareto_df)} тоглогч.",
               kind="Парето график (оноогоор эрэмбэлсэн багана + нийлбэр хувийн шугам)", files=["player_games"])
    coach_box(coach.pareto_league(pareto_df))
    pareto_who(pareto_df, ps[ps.season == f.season].drop_duplicates("player_id", keep="last")
               .set_index("player_id").team.to_dict())


@st.fragment
def fan():
    teams = sorted(tg.team.unique())
    default = f.highlight_team if f.highlight_team in teams else tg.groupby("team").winpct.last().idxmax()
    team = st.selectbox("Ялалтын явцыг харах баг", teams, index=teams.index(default),
                        key=f"overview_fan_team::{f.highlight_team}",
                        help="Дээд самбарын «Онцлох баг»-ийг сонговол энд автоматаар солигдоно")
    show_chart(px_fan(tg, team_key_of(team), f.show_ci), width="stretch")
    chart_note("Улаан-улбар шугам = сонгосон багийн тухайн өдөр хүртэлх ялалтын хувь, саарал = бусад баг. "
               "Сүүдэр нь багийн жинхэнэ хүч байж болох хүрээ: цөөн тоглолтын дараа өргөн, улирлын эцэст нарийсна.",
               f"тоглолтын үр дүн, {season_txt} улирлын үндсэн шат, {tg.team.nunique()} баг.",
               kind="Шугаман график, тодорхой бус байдлын сүүдэртэй (fan chart)", files=["team_games"])
    coach_box(coach.fan(tg[tg.phase == "regular"], team))


left, right = st.columns([5, 7], gap="large")
with left:
    section("Лигийн байр", "Үндсэн шатны ялалт–хожигдол, ялалтын хувиар.")
    standings_board([(i + 1, t, int(r.W), int(r.L), float(r.pct)) for i, (t, r) in enumerate(table.iterrows())],
                    logos, f.highlight_team)
    chart_note("Ялалтын хувиар, тэнцвэл онооны зөрүүгээр эрэмбэлсэн. Шар мөр = онцолсон баг.",
               f"{season_txt} улирлын үндсэн шатны тоглолтын үр дүн; лого — MBA-ийн албан ёсны сайт.",
               kind="Эрэмбэлсэн жагсаалт", files=["team_games", "team_logos"])
    coach_box(coach.standings(table))
with right:
    section("Онооны хуваарь", "Лигийн онооны ихэнхийг хэдэн тоглогч авдаг вэ?")
    pareto()

left, right = st.columns([5, 7], gap="large")
with left:
    section("Багуудын газар зүй", "Багууд хаана төвлөрсөн, аль бүс амжилттай вэ?")
    show_chart(px_map(load("team_meta"), load("standings"), DATA / "mng_adm1.geojson", f.season),
                    width="stretch")
    chart_note("Тойрог бүр 1 баг; том тойрог = өндөр ялалтын хувь. Улаан-улбар = Улаанбаатар, цэнхэр = орон нутаг.",
               "багийн хот — Wikipedia; ялалт — MBA статистик; аймгийн хил — geoBoundaries.",
               kind="Тойргон газрын зураг (bubble map)", files=["team_meta", "standings", "geo"])
    coach_box(coach.region_map(load("team_meta"), load("standings"), f.season))
with right:
    section("Улирлын явц", "Багийн ялалтын хувь тоглолт бүрийн дараа хэрхэн өөрчлөгдсөн бэ?")
    fan()
