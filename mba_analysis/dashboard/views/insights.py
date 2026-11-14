import streamlit as st

from data_access import current_filters, load
from plots import (px_assisted, px_comebacks, px_distance, px_imports_on_court, px_lead_safety, px_off_def, px_stability,
                   px_usage)
from ui import chart_note, filter_summary, findings, page_header

f = current_filters()
season_txt = f.season.replace("-20", "–")
page_header("Олдворууд",
            "Датаас гарсан сагсан бөмбөгийн 8 олдвор. Таб бүр нэг сэдэв; график бүрийн дээр асуулт, доор нь хэрхэн уншихыг бичсэн.")
filter_summary(f)

imports = load("ins_imports")
lead = load("ins_lead")
cb = load("ins_comebacks")
dist = load("ins_distance")
assisted = load("ins_assisted")
ratings = load("ins_ratings")
usage = load("ins_usage")
stab = load("ins_stability")

half = lead[lead.checkpoint == "Хагас"].set_index("bin").est
mid = dist[(dist.lo_m >= 2) & (dist.hi_m <= 6)]
mid_pps = (mid.pps * mid.n).sum() / mid.n.sum()
style = stab[~stab.stat.isin(["ts_pct", "tp_pct"])]
eff = stab[stab.stat.isin(["ts_pct", "tp_pct"])]
findings([
    f"Хагаст 7–10 оноогоор тэргүүлсэн баг **{half['7–10']:.0%}** ялдаг, харин ялсан багийн **{(cb.deficit >= 10).mean():.0%}** нь "
    "тоглолтын дундуур 10+ оноогоор хоцорч байсан.",
    f"Сагснаас 2–6 м-ийн шидэлт хамгийн үр ашиг муутай (**{mid_pps:.2f}** оноо); сагсны доор ба 3 онооны шугамын ард илүү.",
    f"Тоглогчийн хэв маяг улирлаас улиралд хадгалагддаг (хамаарал {style.r.min():.2f}–{style.r.max():.2f}), "
    f"харин оновч хадгалагддаггүй ({eff.r.mean():.2f}).",
])

tab_game, tab_shot, tab_team, tab_import = st.tabs(["Тоглолтын явц", "Шидэлт ба дамжуулалт", "Баг ба тоглогч",
                                                    "Гадаад тоглогч"])

with tab_game:
    st.subheader("Тэргүүлж байгаа баг хэр найдвартай ялдаг вэ?")
    st.plotly_chart(px_lead_safety(lead, f.show_ci), width="stretch")
    chart_note("Хэвтээ тэнхлэг = тухайн мөчид хэдэн оноогоор тэргүүлж байсан, босоо = тэр баг эцэст нь ялсан хувь. Бараан "
               "шугам = тоглолтын хожуу үе. Босоо зураас = 95% магадлалтай хүрээ: цөөн тоглолттой бүлэгт өргөн.",
               "MBA тоглолтын явцын бичлэг, 2025–26 ба 2026–27 улирлын 252 тоглолт.")
    st.subheader("Хоцорч байгаад ялах нь хэр их тохиолддог вэ?")
    left, right = st.columns([3, 2], gap="large")
    with left:
        st.plotly_chart(px_comebacks(cb), width="stretch")
    with right:
        st.markdown("**Хамгийн том 5 эргэлт**")
        top = cb.sort_values("deficit", ascending=False).head(5)
        st.dataframe(top.assign(Тоглолт=top.home_team + " " + top.home_pts.astype(str) + "–" + top.away_pts.astype(str)
                                + " " + top.away_team)[["date", "Тоглолт", "deficit"]]
                     .rename(columns={"date": "Огноо", "deficit": "Хоцорсон оноо"}), hide_index=True, width="stretch")
    chart_note("Багана = ялсан баг тоглолтын дундуур хамгийн ихдээ тэр хэмжээгээр хоцорч байсан тоглолтын тоо. "
               "0 = хэзээ ч хоцроогүй. Улаан-улбар = 10 ба түүнээс олон оноо.",
               f"MBA тоглолтын явцын бичлэг, {len(cb)} тоглолт; ялсан багийн {cb.trailed_at_half.mean():.0%} нь хагаст хоцорч байсан.")

with tab_shot:
    st.subheader("Хэр холоос шидэх нь ашигтай вэ?")
    league_pps = float((dist.pps * dist.n).sum() / dist.n.sum())
    st.plotly_chart(px_distance(dist, league_pps, f.show_ci), width="stretch")
    chart_note("Дээр: тэр зайнаас шидэхэд дунджаар хэдэн оноо авсан (цэнхэр = 2 оноо, улаан-улбар = 3 оноо). Доор: хэдэн удаа "
               "шидсэн. 3 оноо нь 2 онооноос бага онодог ч 1.5 дахин үнэтэй тул дунд зайн шидэлтээс ашигтай.",
               f"MBA тоглолтын хуудасны шидэлтийн байршил, байршил бүртгэгдсэн тоглолтуудын {int(dist.n.sum()):,} шидэлт "
               "(2025 оны 10-р сарын 29 тоглолтод байршил бүртгэгдээгүй тул хассан).")
    st.subheader("Оноо хамтын тоглолтоос гардаг уу, бие даасан тоглолтоос уу?")
    st.plotly_chart(px_assisted(assisted, f.show_ci), width="stretch")
    chart_note("Цэг = тухайн бүсээс оносон шидэлтийн хэдэн хувь нь багийн андын дамжуулалтаас гарсан. Баруун тийш = хамтын "
               "тоглолт, зүүн тийш = тоглогч өөрөө бүтээсэн.",
               f"шидэлтийн байршил ба тоглолтын явцын бичлэг, {int(assisted.n.sum()):,} оносон шидэлт; дамжуулалтын 87%-ийг "
               "шидэлттэй нь холбож чадсан тул бодит хувь арай өндөр байж болно.")

with tab_team:
    st.subheader("Аль баг довтолгоогоор, аль нь хамгаалалтаар хүчтэй вэ?")
    r = ratings[ratings.season == f.season]
    st.plotly_chart(px_off_def(r, f.highlight_team), width="stretch")
    chart_note("Тойрог бүр 1 баг: баруун тийш = сайн довтолгоо, дээшээ = сайн хамгаалалт; том, цэнхэр = өндөр ялалтын хувь. "
               "Тасархай шугам = лигийн дундаж. «Онцлох баг» сонговол зузаан хүрээтэй харагдана.",
               f"тоглолтын хайрцаг оноо, {season_txt} улирлын үндсэн шат, {len(r)} баг; довтолгооны тоог хайрцаг онооноос тооцоолсон.")
    st.subheader("Их ачаалалтай тоглогч оновчтой байж чаддаг уу?")
    u = usage[usage.season == f.season]
    if f.teams:
        u = u[u.team.isin(f.teams)]
    if f.import_status != "Бүгд":
        u = u[u.is_import.astype(bool) == (f.import_status == "Гадаад")]
    if u.empty:
        st.info("Энэ шүүлтүүрт 200-аас олон минут тоглосон тоглогч алга.")
    else:
        st.plotly_chart(px_usage(u, f.highlight_team), width="stretch")
        med = u.groupby(u.is_import.astype(bool))[["usage", "ts"]].median()
        extra = (f" Голч ачаалал: гадаад {med.loc[True, 'usage']:.0%}, дотоод {med.loc[False, 'usage']:.0%}."
                 if {True, False} <= set(med.index) else "")
        chart_note("Цэг бүр 1 тоглогч, том цэг = олон минут. Баруун дээд булан = олон довтолгоо дуусгадаг мөртлөө оновчтой "
                   "(хамгийн үнэ цэнтэй тоглогчид). Цэг дээр хулганаа аваачвал нэрийг харуулна." + extra,
                   f"тоглолтын хайрцаг оноо, {season_txt} улирлын үндсэн шат, 200-аас олон минут тоглосон {len(u)} тоглогч.")
    st.subheader("Тоглогчийн юу нь улирлаас улиралд хадгалагддаг вэ?")
    st.plotly_chart(px_stability(stab, f.show_ci), width="stretch")
    chart_note("Цэг = нэг тоглогчийн өмнөх ба энэ улирлын үзүүлэлт хэр төстэй вэ (1 = яг ижил, 0 = холбоогүй). Цэнхэр = хэв маяг "
               "ба тоглох хэмжээ, улаан-улбар = оновч. Шугам 0-ийг дайрч байвал холбоо батлагдаагүй. Дүгнэлт: шинэ тоглогч "
               "сонгохдоо нэг улирлын оновчид бус, тоглолтын хэв маягт нь найдах нь зөв.",
               f"хоёр улиралд хоёуланд нь тоглосон {int(stab.n.max())} тоглогч (улирал бүрт 50-аас олон шидэлттэй); "
               "2026–27 улирал дуусаагүй.")

with tab_import:
    st.subheader("Гадаад тоглогч тоглолтын аль үед талбай дээр байдаг вэ?")
    st.plotly_chart(px_imports_on_court(imports), width="stretch")
    m = imports.drop_duplicates(["season", "period"]).set_index(["season", "period"]).mean_k
    seasons = sorted(imports.season.unique())
    chart_note("Багана = тухайн үеийн хугацааны хэдэн хувьд нэг баг 0, 1, 2, 3 гадаад тоглогчтой тоглосон. Баганын дээр: "
               "дундаж тоо ба тэр үеийн онооны хэдэн хувийг гадаад тоглогч авсан. "
               f"{seasons[0].replace('-20', '–')}-д 2, 3-р үед дунджаар {(m[seasons[0], 2] + m[seasons[0], 3]) / 2:.1f}, "
               f"1, 4-р үед {(m[seasons[0], 1] + m[seasons[0], 4]) / 2:.1f} байсан бол {seasons[-1].replace('-20', '–')}-д бүх үед "
               "ойролцоо болсон.",
               f"тоглолтын явцын бичлэг; талбай дээрх 5 тоглогчийг солилтоос сэргээсэн (хугацааны {imports.coverage.iloc[0]:.1%}-д "
               "амжилттай). Гадаад эсэхийг MBA-ийн профайлын шошгоор тодорхойлсон; лигийн дүрмийн албан бичвэрээр "
               "баталгаажуулаагүй, зөвхөн датанд ажиглагдсан хэв маяг.")
