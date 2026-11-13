import plotly.graph_objects as go
import streamlit as st

from data_access import load
from plots import A_COLOR, _layout
from ui import chart_note, findings, page_header

page_header("Өгөгдлийн чанар", "Дата хэр бүрэн, хэр цэвэр вэ — дүгнэлтэд итгэж болох эсэхийг шалгах хуудас.")
missing = load("quality_missing")
m = load("quality_matches")
relinked = m[m.left_id != m.right_id]
log = load("cleaning_log")
NAMES = {"position": "Байрлал", "height_cm": "Өндөр", "birth_year": "Төрсөн он", "FT_pct": "Торгуулийн оновч",
         "TP_pct": "3 онооны оновч", "FGA": "Шидэлтийн тоо"}
worst = missing.loc[missing.pct_missing.idxmax()]
findings([
    f"Хамгийн их дутуу үзүүлэлт: **{NAMES.get(worst.column, worst.column)}** ({worst.pct_missing:.0f}%). "
    "Дутуу утгыг зохиомлоор нөхөөгүй, тухайн тооцооноос хассан.",
    f"Өөр улиралд нэр нь бага зэрэг өөр бичигдсэн **{len(relinked)}** тоглогчийг нэг хүн гэж холбосон.",
    f"Цэвэрлэгээний **{log.step.nunique()}** төрлийн алхам хийсэн (доорх бүртгэлээс харна).",
])
fig = go.Figure(go.Bar(x=missing.pct_missing, y=missing.column.map(lambda c: NAMES.get(c, c)), orientation="h",
                       marker_color=A_COLOR, hovertemplate="%{y}: %{x:.1f}%<extra></extra>"))
fig.update_xaxes(title="Дутуу утга, %")
st.plotly_chart(_layout(fig, "Үзүүлэлт бүрийн дутуу утгын хувь", height=320), width="stretch")
chart_note("Багана урт байх тусам тухайн үзүүлэлт олон тоглогчид дутуу.", "MBA тоглогчийн профайл ба улирлын статистик.")
st.subheader(f"Нэрээр холбосон тоглогчид ({len(relinked)})")
st.dataframe(relinked.rename(columns={"left_name": "Нэр (нэг улирал)", "right_name": "Нэр (нөгөө улирал)",
                                      "score": "Төстэй байдал (1 = ижил)", "same_team": "Ижил баг",
                                      "n_candidates": "Сонголтын тоо"})
             [["Нэр (нэг улирал)", "Нэр (нөгөө улирал)", "Төстэй байдал (1 = ижил)", "Ижил баг", "Сонголтын тоо"]],
             hide_index=True, width="stretch")
with st.expander("Цэвэрлэгээний бүрэн бүртгэл"):
    st.dataframe(log.rename(columns={"step": "Алхам", "description": "Юу хийсэн", "rows_before": "Өмнө (мөр)",
                                     "rows_after": "Дараа (мөр)", "note": "Тэмдэглэл"}),
                 hide_index=True, width="stretch")
