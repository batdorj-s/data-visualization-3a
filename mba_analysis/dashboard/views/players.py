import streamlit as st

from data_access import apply, apply_selection, current_filters, empty_notice, load
from plots import LABELS, px_dot_ci, px_funnel, px_scatter
from src.palette import IMPORT_LABELS
from ui import chart_note, filter_summary, findings, page_header

f = current_filters()
season_txt = f.season.replace("-20", "–")
page_header("Тоглогчид",
            "Тоглогчдыг хоёр үзүүлэлтээр харьцуулж, цэг дээр дарж тухайн тоглогчийн картыг баруун талд нь нээнэ.")
filter_summary(f)
players = apply(load("players"), f)
if empty_notice(players):
    st.stop()

AXES = ["PPG", "RPG", "APG", "SPG", "BPG", "MIN", "ts_pct", "pts36", "reb36", "ast36", "tpa_rate", "height_cm", "age", "EFF"]
COLOR_BY = {"Байрлал": "position", "Гадаад / дотоод": "is_import", "Тоглолтын хэв маяг": "cluster_name"}

top = players.sort_values("PPG", ascending=False).iloc[0]
imp = players[players.is_import.astype(bool)]
dom = players[~players.is_import.astype(bool)]
facts = [f"Хамгийн их оноо авагч: **{top.player_name}** ({top.team}), тоглолтод {top.PPG:.1f} оноо."]
if len(imp) and len(dom):
    facts.append(f"Гадаад тоглогчийн голч оноо **{imp.PPG.median():.1f}**, дотоодынх **{dom.PPG.median():.1f}** "
                 f"({len(imp)} гадаад, {len(dom)} дотоод тоглогч).")
facts.append("Цөөн шидэлттэй тоглогчийн оновч санамсаргүй их хэлбэлздэг тул доорх «Хэр найдвартай вэ» хэсгийг хамт хараарай.")
findings(facts)


@st.fragment
def explorer():
    c1, c2 = st.columns(2)
    x = c1.selectbox("Хэвтээ тэнхлэг", AXES, index=AXES.index("MIN"), format_func=lambda c: LABELS.get(c, c), key="px")
    y = c2.selectbox("Босоо тэнхлэг", AXES, index=AXES.index("PPG"), format_func=lambda c: LABELS.get(c, c), key="py")
    color = st.radio("Өнгөөр ялгах", list(COLOR_BY), horizontal=True, key="pcolor")
    event = st.plotly_chart(px_scatter(players, x, y, COLOR_BY[color], f.highlight_team), width="stretch",
                            on_select="rerun", selection_mode=("points", "box", "lasso"), key="scatter")
    chart_note("Цэг бүр 1 тоглогч. Цэг дээр дарвал баруун талын карт тэр тоглогч руу шилжинэ; хулганаар хүрээ татаж "
               "олон тоглогч сонговол доор нь жагсаалт гарна. Хар хүрээтэй цэг = онцолсон багийн тоглогч.",
               f"MBA тоглогчийн улирлын статистик, {season_txt}, шүүлтүүрт тохирох {len(players)} тоглогч.")
    selected = [p["customdata"][0] for p in (event.selection.points if event and event.selection else [])
                if p.get("customdata")]
    if apply_selection(st.session_state, selected):
        st.rerun(scope="app")
    if len(selected) > 1:
        st.dataframe(players[players.player_id.isin(selected)][["player_name", "team", "position", "GP", "PPG",
                                                                "RPG", "APG", "ts_pct"]].rename(columns=COLS),
                     hide_index=True, width="stretch")


COLS = {"player_name": "Тоглогч", "team": "Баг", "position": "Байрлал", "GP": "Тоглолт", "MIN": "Минут",
        "PPG": "Оноо", "RPG": "Самбар", "APG": "Дамжуулалт", "SPG": "Таслалт", "BPG": "Хаалт",
        "FG_pct": "Шидэлтийн %", "TP_pct": "3 онооны %", "FT_pct": "Торгуулийн %", "EFF": "Үр ашиг",
        "height_cm": "Өндөр", "age": "Нас", "ts_pct": "Оновч", "date": "Огноо", "home_team": "Гэрийн баг",
        "away_team": "Зочин баг", "PTS": "Оноо", "REB": "Самбар", "AST": "Дамжуулалт", "FGM": "Оносон",
        "FGA": "Шидсэн", "TPM": "3 оноо оносон", "TPA": "3 оноо шидсэн", "FTM": "Торгууль оносон",
        "FTA": "Торгууль шидсэн", "TOV": "Бөмбөг алдсан"}


@st.fragment
def player_card():
    options = players.sort_values("PPG", ascending=False)
    ids = list(dict.fromkeys(options.player_id))
    if st.session_state.get("card_player") not in ids:
        st.session_state.pop("card_player", None)
    names = options.drop_duplicates("player_id").set_index("player_id").player_name
    with st.container(border=True):
        pid = st.selectbox("Тоглогчийн карт", ids, key="card_player", format_func=lambda i: names.get(i, i),
                           help="Зүүн талын графикаас цэг дарж эсвэл энд нэрээр нь хайж сонгоно")
        row = options[options.player_id == pid].iloc[0]
        ci = load("player_ci")
        ci = ci[(ci.player_id == pid) & (ci.season == f.season)].set_index("metric")
        style = row.cluster_name if isinstance(row.cluster_name, str) else "тодорхойгүй"
        st.markdown(f"**{row.player_name}** · {row.team} · {row.position} · "
                    f"{IMPORT_LABELS[bool(row.is_import)].lower()} тоглогч · хэв маяг: {style}")
        c = st.columns(2)
        for col, (m, label, fmt) in zip(c, [("ppg", "Оноо / тоглолт", "{:.1f}"), ("ts_pct", "Шидэлтийн оновч", "{:.0%}")]):
            if m in ci.index:
                r = ci.loc[m]
                col.metric(label, fmt.format(r.est))
                if f.show_ci:
                    col.caption(f"Хүрээ: {fmt.format(r.lo)}–{fmt.format(r.hi)}")
        c = st.columns(2)
        c[0].metric("Самбар / тоглолт", f"{row.RPG:.1f}")
        c[1].metric("Дамжуулалт / тоглолт", f"{row.APG:.1f}")
        level = st.segmented_control("Харах түвшин", ["Улирлын дундаж", "Тоглолт бүр"], default="Улирлын дундаж",
                                     key="card_level")
        if level == "Тоглолт бүр":
            pg = load("player_games")
            log = pg[(pg.player_id == pid) & (pg.season == f.season)].sort_values("date")
            st.dataframe(log[["date", "home_team", "away_team", "MIN", "PTS", "REB", "AST", "FGM", "FGA", "TPM", "TPA",
                              "FTM", "FTA", "TOV"]].rename(columns=COLS), hide_index=True, width="stretch", height=260)
        else:
            st.dataframe(row[["GP", "MIN", "PPG", "RPG", "APG", "SPG", "BPG", "FG_pct", "TP_pct", "FT_pct", "EFF",
                              "height_cm", "age"]].rename(COLS).to_frame("Утга"), width="stretch", height=260)


@st.fragment
def uncertainty():
    st.subheader("Хэр найдвартай вэ?")
    st.markdown("Цөөн тоглолт, цөөн шидэлттэй тоглогчийн үзүүлэлт санамсаргүйгээр өндөр эсвэл бага гарч болно. "
                "Доорх хоёр график «үнэхээр сайн» ба «азаар сайн харагдаж байгаа»-г ялгахад тусална.")
    left, right = st.columns(2, gap="large")
    with left:
        st.plotly_chart(px_funnel(players, f.show_ci), width="stretch")
        chart_note("Цэг бүр 1 тоглогч. Цэнхэр юүлүүр = санамсаргүй хэлбэлзлийн хүрээ; ногоон цэг юүлүүрээс дээш "
                   "(онцгой сайн), улаан доош. Баруун тийш (олон шидэлт) явах тусам юүлүүр нарийсна.",
                   f"MBA тоглогчийн шидэлтийн статистик, {season_txt}, {len(players)} тоглогч.")
    with right:
        n = st.slider("Хэдэн тоглогч харуулах", 5, 25, 15, key="topn")
        ci = load("player_ci")
        ci = ci[(ci.season == f.season) & (ci.metric == "ppg") & ci.player_id.isin(players.player_id)]
        names = players.drop_duplicates(["player_id", "season"])[["player_id", "player_name", "is_import"]]
        top_n = ci.merge(names, on="player_id", validate="many_to_one").nlargest(n, "est")
        st.plotly_chart(px_dot_ci(top_n, f.show_ci, "Тоглолтын дундаж оноо"), width="stretch")
        chart_note("Цэг = тоглолтын дундаж оноо, шугам = бодит түвшин байж болох хүрээ. Хоёр тоглогчийн шугам давхцаж "
                   "байвал хэн нь илүү гэдгийг дата баттай хэлж чадахгүй.",
                   f"тоглолт бүрийн оноо, {season_txt}; хүрээг тоглолтуудыг 2000 удаа дахин сонгож тооцсон.")


left, right = st.columns([3, 2], gap="large")
with left:
    explorer()
with right:
    player_card()
uncertainty()
