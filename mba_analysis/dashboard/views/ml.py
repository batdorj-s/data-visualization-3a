import numpy as np
import streamlit as st

from data_access import current_filters, latest_elo, load, team_logos
from plots import px_clusters, px_quantile_dots
from src.build_dashboard_data import win_probability
from ui import chart_note, findings, page_header, section, show_chart, team_header

f = current_filters()
page_header("Машин сургалт",
            "Компьютер тоглогчдыг хэв маягаар нь бүлэглэж, тоглолтын ялагчийг урьдчилан таамаглах оролдлого.",
            eyebrow="Машин сургалт")
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
    section("Төстэй тоглогч хайх")
    cl = cl_all[cl_all.season == f.season] if (cl_all.season == f.season).any() else cl_all
    names = cl.drop_duplicates("player_id").set_index("player_id").player_name
    pid = st.selectbox("Тоглогч", cl.sort_values("player_name").player_id.drop_duplicates(),
                       format_func=lambda i: str(names.get(i, i)), key="ml_player",
                       help="Нэрийг бичиж хайна. Од тэмдэг = сонгосон тоглогч")
    me = cl[cl.player_id == pid].iloc[0]
    d = np.hypot(cl.pc1 - me.pc1, cl.pc2 - me.pc2)
    near = cl.assign(dist=d)[cl.player_id != pid].sort_values("dist").drop_duplicates("player_id").head(5)
    near.insert(0, "rank", range(1, len(near) + 1))
    left, right = st.columns([3, 2], gap="large")
    with left:
        show_chart(px_clusters(cl, pid), width="stretch")
        chart_note("Олон үзүүлэлтийг (36 минутад ногдох оноо, самбар, дамжуулалт, оновч ...) 2 тэнхлэгт шахаж зурсан: "
                   "ойр цэгүүд төстэй тоглогчид. Цайвар цэг = аль бүлэгт орох нь тодорхой бус.",
                   f"MBA тоглогчийн улирлын статистик, 150+ минут тоглосон {len(cl)} тоглогч.",
                   kind="Цэгэн график (scatter plot), хэв маягийн бүлгээр өнгөлсөн", files=["clusters", "players"])
    with right:
        with st.container(border=True):
            st.markdown(f"**Хэв маяг:** {me.cluster_name}")
            st.metric("Бүлэгтээ тогтвортой", f"{me.coassign:.0%}",
                      help="100 удаа дахин бүлэглэхэд энэ тоглогч хэдэн хувьд нь ижил бүлэгт орсон")
        st.markdown(f"**{me.player_name}-тэй хамгийн төстэй 5 тоглогч**")
        st.dataframe(near[["rank", "player_name", "cluster_name", "dist"]].rename(
            columns={"rank": "Эрэмбэ", "player_name": "Тоглогч", "cluster_name": "Хэв маяг",
                     "dist": "Ялгаа (бага = төстэй)"}).round(2),
            hide_index=True, width="stretch",
            column_config={"Эрэмбэ": st.column_config.NumberColumn(format="%d", width="small",
                                                                    help="1 = хамгийн төстэй")})
        chart_note("1 = хамгийн төстэй, 5 = тавдугаарт төстэй. «Ялгаа» = зүүн талын график дээрх хоёр цэгийн хоорондох "
                   "зай: бага байх тусам хэв маяг нь ойр.", f"{len(cl)} тоглогчийн хэв маягийн бүлэглэл.",
                   kind="Хүснэгт (эрэмбэлсэн)", files=["clusters"])


@st.fragment
def win_calculator():
    section("Ялалтын магадлал тооцоолох")
    elo = latest_elo(f.season)
    teams = sorted(elo.index)
    a, b = st.columns(2)
    t1 = a.selectbox("Баг А", teams, index=0, key="wp_a")
    t2 = b.selectbox("Баг Б", teams, index=min(1, len(teams) - 1), key="wp_b")
    coefs = load("elo_coefs").coef.to_numpy()
    p, lo, hi = win_probability(float(elo[t1]), float(elo[t2]), coefs)
    logos = team_logos()
    c1, c2 = st.columns(2)
    with c1:
        team_header(t1, logos.get(t1), "Баг А", [("Хүчний оноо", f"{elo[t1]:.0f}"), ("Ялах магадлал", f"{p:.0%}")])
    with c2:
        team_header(t2, logos.get(t2), "Баг Б", [("Хүчний оноо", f"{elo[t2]:.0f}"), ("Ялах магадлал", f"{1 - p:.0%}")])
    if f.show_ci:
        st.caption(f"{t1} ялах магадлалын 95% хүрээ: {lo:.0%}–{hi:.0%} (1500 = лигийн дундаж хүчний оноо).")
    show_chart(px_quantile_dots(p, 20, t1, t2), width="stretch")
    chart_note(f"20 тойрог = 20 удаа тоглосон гэж төсөөлөхөд цэнхэр нь {t1}, улаан-улбар нь {t2}-ийн ялалт. "
               "Магадлалыг «20-оос хэд» гэж харах нь хувиас илүү ойлгомжтой."
               + (f" Бодит магадлал {lo:.0%}–{hi:.0%} хооронд байх магадлалтай." if f.show_ci else ""),
               "хоёр багийн одоогийн хүчний оноо; томьёог 2025–26, 2026–27 улирлын тоглолтоор тааруулсан.",
               kind="Тоон цэгэн зураг (quantile dot plot)", files=["games", "game_matrix"])


cluster_explorer()
win_calculator()
with st.expander("Загваруудын нарийвчилсан үнэлгээ (мэргэжлийн хүнд)"):
    st.dataframe(load("model_metrics").rename(columns={
        "model": "Загвар", "accuracy_mean": "Зөв таамагласан хувь", "accuracy_std": "± хэлбэлзэл",
        "auc_mean": "Ялгах чадвар (AUC)", "auc_std": "± хэлбэлзэл ", "brier_mean": "Магадлалын алдаа (Brier)",
        "brier_std": "± хэлбэлзэл  "}).round(3), hide_index=True, width="stretch")
    chart_note("Загварыг он цагийн дарааллаар 5 хэсэгт хувааж, өмнөх хэсгээр сургаад дараагийнхыг таамаглуулсан.",
               "2025–26, 2026–27 улирлын тоглолт бүрийн өмнөх үзүүлэлт.", kind="Хүснэгт",
               files=["game_matrix", "metrics"])
