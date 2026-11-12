import plotly.graph_objects as go
import streamlit as st

from data_access import load
from plots import A_COLOR, _layout

st.title("Өгөгдлийн чанар")
missing = load("quality_missing")
fig = go.Figure(go.Bar(x=missing.pct_missing, y=missing.column, orientation="h", marker_color=A_COLOR,
                       hovertemplate="%{y}: %{x:.1f}%<extra></extra>"))
fig.update_xaxes(title="Дутуу утга, %")
st.plotly_chart(_layout(fig, "Хувьсагч бүрийн дутуу утга (импутаци хийгээгүй)", height=300), width="stretch")
m = load("quality_matches")
st.subheader(f"Улирал хоорондын нэрийн тааруулалт ({int((m.left_id != m.right_id).sum())} хос)")
st.dataframe(m[m.left_id != m.right_id], hide_index=True, width="stretch")
st.subheader("Цэвэрлэгээний лог")
st.dataframe(load("cleaning_log"), hide_index=True, width="stretch")
