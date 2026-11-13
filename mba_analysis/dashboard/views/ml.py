import numpy as np
import streamlit as st

from data_access import current_filters, latest_elo, load
from plots import px_clusters, px_quantile_dots
from src.build_dashboard_data import win_probability

f = current_filters()
st.title("Машин суралцал")


@st.fragment
def cluster_explorer():
    st.subheader("Төстэй тоглогч хайх (K-Means архетип)")
    cl = load("clusters")
    cl = cl[cl.season == f.season] if (cl.season == f.season).any() else cl
    names = cl.drop_duplicates("player_id").set_index("player_id").player_name
    pid = st.selectbox("Тоглогч", cl.sort_values("player_name").player_id.drop_duplicates(), format_func=lambda i: names.get(i, i),
                       key="ml_player")
    me = cl[cl.player_id == pid].iloc[0]
    d = np.hypot(cl.pc1 - me.pc1, cl.pc2 - me.pc2)
    near = cl.assign(dist=d)[cl.player_id != pid].nsmallest(5, "dist")
    left, right = st.columns([3, 2])
    with left:
        st.plotly_chart(px_clusters(cl, pid), width="stretch")
    with right:
        st.metric("Архетип", me.cluster_name)
        st.metric("Бүлэгт харьяалагдах тогтвортой байдал", f"{me.coassign:.0%}",
                  help="100 bootstrap-д энэ тоглогч ижил бүлэгт орсон давтамж")
        st.markdown("**Хамгийн төстэй 5 тоглогч**")
        st.dataframe(near[["player_name", "cluster_name", "dist"]].rename(
            columns={"player_name": "Тоглогч", "cluster_name": "Архетип", "dist": "Зай"}).round(2),
            hide_index=True, width="stretch")


@st.fragment
def win_calculator():
    st.subheader("Ялалтын магадлалын тооцоолуур")
    elo = latest_elo(f.season)
    teams = sorted(elo.index)
    a, b = st.columns(2)
    t1 = a.selectbox("Баг А", teams, index=0, key="wp_a")
    t2 = b.selectbox("Баг Б", teams, index=min(1, len(teams) - 1), key="wp_b")
    coefs = load("elo_coefs").coef.to_numpy()
    p, lo, hi = win_probability(float(elo[t1]), float(elo[t2]), coefs)
    c1, c2, c3 = st.columns(3)
    c1.metric(f"{t1} Elo", f"{elo[t1]:.0f}")
    c2.metric(f"{t2} Elo", f"{elo[t2]:.0f}")
    c3.metric(f"{t1} ялах магадлал", f"{p:.0%}", help=f"95% интервал {lo:.0%}–{hi:.0%}" if f.show_ci else None)
    if f.show_ci:
        mm = load("model_metrics").set_index("model")
        acc, elo_acc = mm.loc["logreg", "accuracy_mean"], mm.loc["baseline_elo", "accuracy_mean"]
        st.caption(f"95% интервал {lo:.0%}–{hi:.0%} (β-ийн 500 bootstrap). Walk-forward CV: Logistic Regression "
                   f"accuracy {acc:.0%}, энгийн Elo baseline {elo_acc:.0%}.")
    st.plotly_chart(px_quantile_dots(p, 20, t1, t2), width="stretch")


cluster_explorer()
win_calculator()
st.subheader("Загварын үнэлгээ (walk-forward CV, 5 fold)")
st.dataframe(load("model_metrics").round(3), hide_index=True, width="stretch")
