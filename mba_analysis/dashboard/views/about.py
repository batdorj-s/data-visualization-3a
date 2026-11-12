import streamlit as st

from data_access import load, snapshot

st.title("Тухай")
st.markdown(f"""
**Snapshot:** {snapshot()} — 2026-27 улирал явагдаж байгаа.

### Эх сурвалж
1. **MBA статистикийн систем** — mongolia.basketball (тоглогч, тоглолтын box score, профайл)
2. **Wikipedia** — The League (Mongolia), 2023–24 улирал (байр, гэр хот, аваргууд)
3. **Wikipedia/FIBA** — шигшээ багийн бүрэлдэхүүн (2026.08)
4. **geoBoundaries** — Монголын аймгийн хил (ODbL)

### Тодорхой бус байдлыг хэрхэн тооцсон
- Тоглогч, багийн дундаж, онооны хувь: **тоглолтоор cluster bootstrap**, 2,000 давталт, 95% percentile CI
- Ялалтын хувь: **Wilson** интервал; корреляц: **Fisher z**
- Ялалтын магадлал: `sigmoid(β·ΔElo)`, β-ийн 500 bootstrap дээжээс интервал
- "Итгэх интервал харуулах" сонголтыг унтраавал бүх CI нуугдана

### Харилцааны 7 зорилго (Yi et al., 2007)
| Зорилго | Хэрэгжүүлэлт |
|---|---|
| Тэмдэглэх (Select) | Тоглогчид → scatter дээр цэг/хүрээгээр сонгох → тоглогчийн карт |
| Судлах (Explore) | Plotly zoom / pan |
| Зохион байгуулах (Reconfigure) | X / Y тэнхлэгийн хувьсагч сонгох |
| Өөр дүрслэл (Encode) | Өнгө: байрлал / Import / архетип |
| Дэлгэрэнгүй (Abstract/Elaborate) | Тоглогчийн карт: улирлын дундаж ↔ тоглолт бүр |
| Шүүх (Filter) | Хажуугийн самбар: улирал, баг, байрлал, төрөл, GP |
| Холбох (Connect) | "Онцлох баг" бүх хуудасны график дээр онцлогдоно |
""")
st.subheader("Таамаглалын үр дүн")
st.dataframe(load("hypotheses")[["hid", "statement", "estimate", "ci_lo", "ci_hi", "method"]].round(3),
             hide_index=True, width="stretch")
