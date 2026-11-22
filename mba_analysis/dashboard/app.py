import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
for p in (HERE, HERE.parent):
    if str(p) not in sys.path:
        sys.path.insert(0, str(p))

import streamlit as st  # noqa: E402

from data_access import filters_sidebar  # noqa: E402
from ui import error_state, inject_css  # noqa: E402

st.set_page_config(page_title="MBA Analytics — Монголын сагсан бөмбөгийн лигийн шинжилгээ",
                   page_icon=str(HERE / "assets" / "mba_icon.svg"), layout="wide")
inject_css()
st.logo(str(HERE / "assets" / "mba_wordmark.svg"), size="large", icon_image=str(HERE / "assets" / "mba_icon.svg"))

pages = {
    "Шинжилгээ": [
        st.Page("views/overview.py", title="Тойм", icon=":material/dashboard:", default=True),
        st.Page("views/players.py", title="Тоглогчид", icon=":material/person:"),
        st.Page("views/teams.py", title="Багууд", icon=":material/groups:"),
        st.Page("views/shots.py", title="Шидэлт ба тоглолтын явц", icon=":material/sports_basketball:"),
        st.Page("views/insights.py", title="Олдворууд", icon=":material/lightbulb:"),
        st.Page("views/ml.py", title="Машин сургалт", icon=":material/model_training:"),
    ],
    "Тусламж": [
        st.Page("views/glossary.py", title="Нэр томьёо", icon=":material/menu_book:"),
        st.Page("views/quality.py", title="Өгөгдлийн чанар", icon=":material/fact_check:"),
        st.Page("views/about.py", title="Тухай", icon=":material/info:"),
    ],
}
nav = st.navigation(pages)
st.session_state["_filters"] = filters_sidebar()
try:
    nav.run()
except Exception as exc:  # st.stop / st.rerun нь BaseException тул энд баригдахгүй
    error_state("Энэ хэсгийг харуулах үед алдаа гарлаа",
                "Шүүлтүүрээ өөрчлөх эсвэл хуудсыг дахин ачаалж үзнэ үү. Алдаа давтагдвал доорх дэлгэрэнгүйг хөгжүүлэгчид илгээнэ үү.")
    with st.expander("Техникийн дэлгэрэнгүй"):
        st.exception(exc)
