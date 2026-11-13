import numpy as np
import streamlit as st

from data_access import current_filters, latest_elo, load
from plots import px_clusters, px_quantile_dots
from src.build_dashboard_data import win_probability
from ui import chart_note, findings, page_header

f = current_filters()
page_header("Машин сургалт",
            "Компьютер тоглогчдыг хэв маягаар нь бүлэглэж, тоглолтын ялагчийг урьдчилан таамаглах оролдлого.")
mm = load("model_metrics").set_index("model")
acc, elo_acc = mm.loc["logreg", "accuracy_mean"], mm.loc["baseline_elo", "accuracy_mean"]
cl_all = load("clusters")
findings([
    f"Тоглогчид **{cl_all.cluster_name.nunique()}** хэв маягт хуваагдав: "
    + ", ".join(f"«{n}»" for n in sorted(cl_all.cluster_name.unique())) + ".",
    f"Ялагч таамаглах загвар тоглолтын **{acc:.0%}**-ийг зөв таамагласан; «хүчний оноо өндөр нь ялна» гэсэн "
    f"энгийн дүрэм {elo_acc:.0%}. Өөрөөр хэлбэл MBA-д ML загвар энгийн дүрмээс баттай илүү биш.",
    "Таамаглал зөвхөн тухайн тоглолтоос **өмнөх** датаг ашигладаг (ирээдүйн мэдээлэл «хулгайлаагүй»).",
])


@st.fragment
def cluster_explorer():
    st.subheader("Төстэй тоглогч хайх")
    cl = cl_all[cl_all.season == f.season] if (cl_all.season == f.season).any() else cl_all
    names = cl.drop_duplicates("player_id").set_index("player_id").player_name
    pid = st.selectbox("Тоглогч", cl.sort_values("player_name").player_id.drop_duplicates(),
                       format_func=lambda i: names.get(i, i), key="ml_player",
                       help="Нэрийг бичиж хайна. Од тэмдэг = сонгосон тоглогч")
    me = cl[cl.player_id == pid].iloc[0]
    d = np.hypot(cl.pc1 - me.pc1, cl.pc2 - me.pc2)
    near = cl.assign(dist=d)[cl.player_id != pid].nsmallest(5, "dist")
    left, right = st.columns([3, 2], gap="large")
    with left:
        st.plotly_chart(px_clusters(cl, pid), width="stretch")
        chart_note("Олон үзүүлэлтийг (36 минутад ногдох оноо, самбар, дамжуулалт, оновч ...) 2 тэнхлэгт шахаж зурсан: "
                   "ойр цэгүүд төстэй тоглогчид. Цайвар цэг = аль бүлэгт орох нь тодорхой бус.",
                   f"MBA тоглогчийн улирлын статистик, 150+ минут тоглосон {len(cl)} тоглогч.")
    with right:
        with st.container(border=True):
            st.markdown(f"**Хэв маяг:** {me.cluster_name}")
            st.metric("Бүлэгтээ тогтвортой", f"{me.coassign:.0%}",
                      help="100 удаа дахин бүлэглэхэд энэ тоглогч хэдэн хувьд нь ижил бүлэгт орсон")
        st.markdown("**Хамгийн төстэй 5 тоглогч**")
        st.dataframe(near[["player_name", "cluster_name", "dist"]].rename(
            columns={"player_name": "Тоглогч", "cluster_name": "Хэв маяг", "dist": "Ялгаа (бага = төстэй)"}).round(2),
            hide_index=True, width="stretch")


@st.fragment
def win_calculator():
    st.subheader("Ялалтын магадлал тооцоолох")
    elo = latest_elo(f.season)
    teams = sorted(elo.index)
    a, b = st.columns(2)
    t1 = a.selectbox("Баг А", teams, index=0, key="wp_a")
    t2 = b.selectbox("Баг Б", teams, index=min(1, len(teams) - 1), key="wp_b")
    coefs = load("elo_coefs").coef.to_numpy()
    p, lo, hi = win_probability(float(elo[t1]), float(elo[t2]), coefs)
    c1, c2, c3 = st.columns(3)
    c1.metric(f"{t1}: хүчний оноо", f"{elo[t1]:.0f}", border=True)
    c2.metric(f"{t2}: хүчний оноо", f"{elo[t2]:.0f}", border=True)
    c3.metric(f"{t1} ялах магадлал", f"{p:.0%}", border=True,
              help=f"Магадлалтай хүрээ {lo:.0%}–{hi:.0%}" if f.show_ci else None)
    st.plotly_chart(px_quantile_dots(p, 20, t1, t2), width="stretch")
    chart_note(f"20 тойрог = 20 удаа тоглосон гэж төсөөлөхөд цэнхэр нь {t1}, улаан-улбар нь {t2}-ийн ялалт. "
               "Магадлалыг «20-оос хэд» гэж харах нь хувиас илүү ойлгомжтой."
               + (f" Бодит магадлал {lo:.0%}–{hi:.0%} хооронд байх магадлалтай." if f.show_ci else ""),
               "хоёр багийн одоогийн хүчний оноо; томьёог 2025–26, 2026–27 улирлын тоглолтоор тааруулсан.")


cluster_explorer()
win_calculator()
with st.expander("Загваруудын нарийвчилсан үнэлгээ (мэргэжлийн хүнд)"):
    st.dataframe(load("model_metrics").rename(columns={
        "model": "Загвар", "accuracy_mean": "Зөв таамагласан хувь", "accuracy_std": "± хэлбэлзэл",
        "auc_mean": "Ялгах чадвар (AUC)", "auc_std": "± хэлбэлзэл ", "brier_mean": "Магадлалын алдаа (Brier)",
        "brier_std": "± хэлбэлзэл  "}).round(3), hide_index=True, width="stretch")
    st.caption("Загварыг он цагийн дарааллаар 5 хэсэгт хувааж, өмнөх хэсгээр сургаад дараагийнхыг таамаглуулсан.")
