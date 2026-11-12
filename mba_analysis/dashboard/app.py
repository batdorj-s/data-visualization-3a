import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
for p in (HERE, HERE.parent):
    if str(p) not in sys.path:
        sys.path.insert(0, str(p))

import streamlit as st  # noqa: E402

from data_access import filters_sidebar  # noqa: E402

st.set_page_config(page_title="MBA лигийн анализ", page_icon=":material/sports_basketball:", layout="wide")

pages = [
    st.Page("views/overview.py", title="Тойм", default=True),
    st.Page("views/players.py", title="Тоглогчид"),
    st.Page("views/teams.py", title="Багууд"),
    st.Page("views/ml.py", title="Машин суралцал"),
    st.Page("views/quality.py", title="Өгөгдлийн чанар"),
    st.Page("views/about.py", title="Тухай"),
]
nav = st.navigation(pages)
st.session_state["_filters"] = filters_sidebar()
nav.run()
