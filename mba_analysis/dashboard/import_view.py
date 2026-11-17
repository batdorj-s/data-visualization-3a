"""Тоглогчийн хуудасны «Гадаад тоглогч ба солилцоо» таб: гарал үүсэл, 4 таамаглал, орлуулах тоглогч хайгч."""
import pandas as pd
import streamlit as st

from data_access import load
from plots import (px_import_age, px_import_hypotheses, px_import_pipeline, px_import_position, px_import_retention)
from src.imports import SIM_FEATURES, similar_players
from ui import chart_note, findings

SHAM = "ShamSports-ийн тоглогчийн карьерын хуудас (тоглогч бүрийг MBA-ийн профайлтай төрсөн он эсвэл өндрөөр тулгасан)"


def import_section(f) -> None:
    bg = load("imp_background")
    im = load("imp_players")
    hyp = load("imp_hypotheses")
    found = bg[bg.status == "олдсон"]
    ret = load("imp_retention")
    findings([
        f"72 гадаад тоглогчийн **{len(found)}**-ийн гарал үүслийг эх сурвалжаар баталгаажуулсан; тэдний "
        f"{int(found.nationality.fillna('').str.contains('USA').sum())} нь АНУ-ын иргэн.",
        f"2025–26 улирлын {len(ret)} гадаад тоглогчоос дараа улиралд MBA-д **{int(ret.stayed.sum())}** нь л үлдсэн "
        f"(тэдний {int(ret.same_team.sum())} нь ижил багтаа) — бараг бүх гадаад тоглогч жил бүр солигддог.",
        "Датаар батлагдсан: **" + "; ".join(r.statement for r in hyp[hyp.verdict == "Батлагдсан"].itertuples())
        + "**. Бусад нь баттай биш (дата цөөн).",
    ])
    st.caption("Гэрээний хугацаа, цалин, төлөөлөгчийн мэдээлэл нийтэд ил биш (MBA-ийн мэдээ, баримт бичгийн хуудас хоосон) тул "
               "«яагаад сонгосон» гэдгийг шууд мэдэх боломжгүй. Доор датанд ажиглагдсан хэв маягийг таамаглал болгон шалгав.")

    st.subheader("Таамаглалын дүн")
    st.plotly_chart(px_import_hypotheses(hyp, f.show_ci), width="stretch")
    chart_note("Цэг = датаас гарсан утга, өнгөт зурвас = 95% магадлалтай хүрээ, тасархай = «ялгаагүй» (0). Зурвас бүхэлдээ 0-ээс "
               "баруун тийш байвал таамаглал батлагдана; 0-ийг дайрвал баттай хэлж чадахгүй.",
               "MBA статистик (2025–26, 2026–27) + " + SHAM + ".",
               kind="Цэгэн график, 95% хүрээтэй (forest plot)", files=["players", "import_bg"])

    st.subheader("Хаанаас ирж байна вэ?")
    st.plotly_chart(px_import_pipeline(bg), width="stretch")
    chart_note("Зүүн: ирэхээсээ өмнө тоглож байсан хамгийн өндөр лиг. Баруун: Монголд ирэхийн өмнөх сүүлийн мэргэжлийн лиг.",
               f"{SHAM}; {len(found)}/72 тоглогч. Олдоогүй нь ихэвчлэн Азийн квотын тоглогчид тул дүр зураг АНУ руу хазайсан байж болно.",
               kind="Хэвтээ багана график (2 хэсэгтэй)", files=["import_bg"])

    st.subheader("Хэн дараа улиралд үлддэг вэ?")
    st.plotly_chart(px_import_retention(load("imp_ret_cmp"), f.show_ci), width="stretch")
    chart_note("Мөр бүр 1 үзүүлэлт: улбар шар = дараа улиралд үлдсэн, саарал = явсан тоглогчдын голч утга, зураас = 95% хүрээ. "
               "Үлдсэн тоглогч илүү их оноо авч, илүү олон минут тоглож байсан ч үлдсэн нь ердөө 8 тул ялгаа баттай биш.",
               "MBA статистик; «үлдсэн» = дараа улирлын статистикт аль нэг багийн нэрээр гарсан.",
               kind="Цэгэн график, 95% хүрээтэй (dot plot)", files=["players", "player_games", "import_bg"])

    st.subheader("Аль байрлалд гадаад тоглогч түлхүү тоглодог вэ?")
    st.plotly_chart(px_import_position(load("imp_position"), load("imp_conc")), width="stretch")
    chart_note("Багана = тухайн байрлалын нийт минутын хэдэн хувийг гадаад тоглогч тоглосон; тасархай шугам = бүх байрлалын "
               "дундаж. 2026–27-д төвийн байрлалын минутын гуравны хоёрыг гадаад тоглогч тоглож байна.",
               "MBA статистик; байрлал MBA-ийн профайлаас.",
               kind="Бүлэглэсэн багана график + дундаж шугам", files=["players"])

    st.subheader("Нас, туршлага, гүйцэтгэл")
    st.plotly_chart(px_import_age(im), width="stretch")
    chart_note("Цэг бүр 1 гадаад тоглогч-улирал, том цэг = олон минут, өнгө = өмнө тоглосон хамгийн өндөр лиг. Ахимаг тоглогч илүү оноо "
               "авдаг ч илүү олон минут тоглодог тул шалтгаан нь туршлага, багийн өгсөн үүрэг хоёр холилдсон байж болно.",
               "MBA статистик; нас ба лигийн түвшин — " + SHAM + ".",
               kind="Тойргон цэгэн график (bubble chart)", files=["players", "player_games", "import_bg"])

    st.subheader("Явсан тоглогчийг орлох төстэй тоглогч")
    gone = ret[~ret.stayed].sort_values("PPG", ascending=False)
    pool = im.dropna(subset=list(SIM_FEATURES))
    gone = gone[gone.player_id.isin(pool.player_id)]
    if gone.empty:
        st.info("Харьцуулах дата хүрэлцэхгүй байна.")
        return
    labels = {r.player_id: f"{r.player_name} ({r.team}, {r.PPG:.1f} оноо)" for r in gone.itertuples()}
    pid = st.selectbox("2025–26 улирлын дараа явсан гадаад тоглогч", list(labels), format_func=labels.get, key="repl_player",
                       help="Хэв маяг ба гүйцэтгэлээр хамгийн төстэй MBA-ийн бусад гадаад тоглогчдыг хайна")
    idx = pool[(pool.player_id == pid) & (pool.season == "2025-2026")].index[0]
    sim = similar_players(pool, idx, k=5)
    me = pool.loc[[idx]].assign(distance=0.0)
    show = pd.concat([me, sim])
    cols = {"player_name": "Тоглогч", "season": "Улирал", "team": "Баг", "distance": "Ялгаа (бага = төстэй)",
            **{k: v for k, v in SIM_FEATURES.items()}, "level": "Өмнөх түвшин", "last_league": "Өмнөх лиг"}
    st.dataframe(show[list(cols)].rename(columns=cols).round(2), hide_index=True, width="stretch",
                 column_config={"Шидэлтийн оновч": st.column_config.NumberColumn(format="percent"),
                                "Довтолгооны ачаалал": st.column_config.NumberColumn(format="percent"),
                                "3 оноогоор шидсэн хувь": st.column_config.NumberColumn(format="percent")})
    chart_note("Эхний мөр = сонгосон тоглогч. Доорх 5 нь MBA-д тоглосон бусад гадаад тоглогчдоос оноо, самбар, дамжуулалт (36 минутад), "
               "3 оноогоор шидэх хувь, оновч, довтолгооны ачаалал, өндрөөр хамгийн ойр нь. Ижил хэв маягийн тоглогч хайхад тусална; "
               "гэрээний боломж, цалинг тусгаагүй.",
               "MBA статистик (2025–26, 2026–27), 5+ тоглолт тоглосон гадаад тоглогчид; үзүүлэлт бүрийг стандартчилсан.",
               kind="Хүснэгт (төстэй тоглогчид)", files=["players", "player_games", "import_bg"])
