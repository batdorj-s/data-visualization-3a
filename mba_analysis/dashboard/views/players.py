import streamlit as st

from data_access import apply, current_filters, empty_notice, load
from plots import LABELS, px_dot_ci, px_funnel, px_scatter

f = current_filters()
st.title("Тоглогчид")
players = apply(load("players"), f)
if empty_notice(players):
    st.stop()

AXES = ["PPG", "RPG", "APG", "SPG", "BPG", "MIN", "ts_pct", "pts36", "reb36", "ast36", "tpa_rate", "height_cm", "age", "EFF"]
COLOR_BY = {"Байрлал": "position", "Import / дотоод": "is_import", "K-Means архетип": "cluster_name"}


@st.fragment
def explorer():
    c1, c2, c3 = st.columns([1, 1, 2])
    x = c1.selectbox("X тэнхлэг", AXES, index=AXES.index("MIN"), format_func=lambda c: LABELS.get(c, c), key="px")
    y = c2.selectbox("Y тэнхлэг", AXES, index=AXES.index("PPG"), format_func=lambda c: LABELS.get(c, c), key="py")
    color = c3.radio("Өнгө", list(COLOR_BY), horizontal=True, key="pcolor")
    event = st.plotly_chart(px_scatter(players, x, y, COLOR_BY[color], f.highlight_team), width="stretch",
                            on_select="rerun", selection_mode=("points", "box", "lasso"), key="scatter")
    selected = [p["customdata"][0] for p in (event.selection.points if event and event.selection else [])
                if p.get("customdata")]
    if selected:
        st.session_state["selected_player"] = selected[0]
        if len(selected) > 1:
            st.dataframe(players[players.player_id.isin(selected)][["player_name", "team", "position", "GP", "PPG",
                                                                    "RPG", "APG", "ts_pct"]],
                         hide_index=True, width="stretch")


@st.fragment
def player_card():
    pid = st.session_state.get("selected_player")
    options = players.sort_values("PPG", ascending=False)
    ids = options.player_id.tolist()
    idx = ids.index(pid) if pid in ids else 0
    names = options.drop_duplicates("player_id").set_index("player_id").player_name
    pid = st.selectbox("Тоглогчийн карт", list(dict.fromkeys(ids)), index=list(dict.fromkeys(ids)).index(ids[idx]),
                       key="card_player", format_func=lambda i: names.get(i, i))
    row = options[options.player_id == pid].iloc[0]
    ci = load("player_ci")
    ci = ci[(ci.player_id == pid) & (ci.season == f.season) & (ci.team_key == row.team_key)].set_index("metric")
    archetype = row.cluster_name if isinstance(row.cluster_name, str) else "—"
    st.markdown(f"**{row.player_name}** · {row.team} · {row.position} · "
                f"{'Import' if row.is_import else 'Дотоод'} · архетип: {archetype}")
    c = st.columns(3)
    for col, (m, label, fmt) in zip(c[:2], [("ppg", "PPG", "{:.1f}"), ("ts_pct", "TS%", "{:.1%}")]):
        if m in ci.index:
            r = ci.loc[m]
            col.metric(label, fmt.format(r.est), help=f"95% CI {fmt.format(r.lo)}–{fmt.format(r.hi)}" if f.show_ci else None)
            if f.show_ci:
                col.caption(f"95% CI {fmt.format(r.lo)}–{fmt.format(r.hi)}")
    c[2].metric("RPG / APG", f"{row.RPG:.1f} / {row.APG:.1f}")
    level = st.segmented_control("Дэлгэрэнгүй", ["Улирлын дундаж", "Тоглолт бүр"], default="Улирлын дундаж",
                                 key="card_level")
    if level == "Тоглолт бүр":
        pg = load("player_games")
        log = pg[(pg.player_id == pid) & (pg.season == f.season)].sort_values("date")
        st.dataframe(log[["date", "home_team", "away_team", "MIN", "PTS", "REB", "AST", "FGM", "FGA", "TPM", "TPA",
                          "FTM", "FTA", "TOV"]], hide_index=True, width="stretch")
    else:
        st.dataframe(row[["GP", "MIN", "PPG", "RPG", "APG", "SPG", "BPG", "FG_pct", "TP_pct", "FT_pct", "EFF",
                          "height_cm", "age"]].to_frame("Утга").T, width="stretch")


@st.fragment
def uncertainty():
    left, right = st.columns(2)
    with left:
        st.plotly_chart(px_funnel(players, f.show_ci), width="stretch")
    with right:
        n = st.slider("Топ N", 5, 25, 15, key="topn")
        ci = load("player_ci")
        ci = ci[(ci.season == f.season) & (ci.metric == "ppg") & ci.player_id.isin(players.player_id)]
        top = ci.merge(players[["player_id", "player_name", "is_import"]], on="player_id").nlargest(n, "est")
        st.plotly_chart(px_dot_ci(top, f.show_ci, "Оноо / тоглолт"), width="stretch")


explorer()
player_card()
uncertainty()
