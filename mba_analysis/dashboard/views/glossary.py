import streamlit as st

from src.glossary import TERMS
from ui import page_header

page_header("Нэр томьёо", "Dashboard ба тайланд гарах үг бүрийн энгийн тайлбар. Хайх талбарт үгээ бичнэ үү.")
q = st.text_input("Хайх", placeholder="жишээ нь: оновч, хүрээ, Elo", key="glossary_q").strip().lower()
rows = [t for t in TERMS if not q or any(q in x.lower() for x in t)]
if not rows:
    st.info("Тохирох нэр томьёо олдсонгүй. Өөр үгээр хайгаад үзээрэй.")
for plain, tech, text in rows:
    with st.container(border=True):
        st.markdown(f"**{plain}** · <span style='color:#64748B'>{tech}</span>", unsafe_allow_html=True)
        st.markdown(text)
