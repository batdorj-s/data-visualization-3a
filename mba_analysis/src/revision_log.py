"""Хэрэглэгчийн санал хүсэлтийн дараах графикийн өөрчлөлтийн бүртгэл (тайлангийн хавсралт).

feedback = хэрэглэгчийн бичсэн үг яг хэвээр (харилцааны түүхээс); change = юу өөрчлөгдсөн; reason = яагаад;
commit = өөрчлөлтийг оруулсан commit. before/after = tools/report/render_revisions.py-ийн зурах код: тухайн commit-ийн
dashboard/plots.py-ийн функцийг тухайн үеийн датагаар дуудна (P = 2025–26 улирлын 5+ тоглолттой тоглогчид, load(нэр) = parquet).
Зурагтай бүртгэлийн зураг: figures/revisions/<key>.png.
"""

_FLOW = """
from src.inplay import REG_SEC, finalize, win_prob
gl = load("game_list"); gl = gl[gl.season == SEASON]; g = gl.loc[gl.lead_changes.idxmax()]
flow = load("game_flow"); flow = flow[flow.game_id == g.game_id].sort_values("elapsed")
p = load("inplay_params").iloc[0]
params = {"intercept": p.intercept, "coef": {k: p[k] for k in ("margin", "margin_scaled", "elo_diff", "elo_x_time")}}
wp = finalize(win_prob(params, flow.margin, np.clip(REG_SEC - flow.elapsed, 0, None), g.elo_pre_home - g.elo_pre_away),
              flow.margin.iloc[-1])
fig = px_game_flow(flow, wp, g.home_team, g.away_team)
"""
_PARETO = 'pl = load("pareto_league"); fig = px_pareto(pl[pl.season == SEASON], True, "Цөөн тоглогч лигийн онооны ихэнхийг авдаг")'
_OFFDEF = 'r = load("ins_ratings"); r = r[r.season == SEASON]; fig = px_off_def(r, None)'
_OFFDEF_LOGO = 'r = load("ins_ratings"); r = r[r.season == SEASON]; fig = px_off_def(r, None, thumbs(load("team_meta")))'


def _spec(commit: str, code: str) -> dict:
    return {"commit": commit, "code": code}


REVISIONS = [
    {"key": "R01_plain_language", "date": "2026-11-13",
     "feedback": "text-uud heterhii nariin helleg ashiglsan bn hereglegch uuniig unshaad oilgohgui",
     "chart": "Юүлүүр график (бүх график, dashboard-ийн бүх текст)",
     "change": "«TS%», «FGA + 0.44·FTA», «Four Factors», «Elo үнэлгээ» зэрэг товчлолыг «Шидэлтийн оновч», «Шидэлтийн "
               "оролдлого», «Ялалтын 4 хүчин зүйл», «Багийн хүчний оноо» болгож, нэр томьёоны толь нэмсэн.",
     "reason": "Dashboard-ийн хэрэглэгч сагсан бөмбөгийн статистикийн мэргэжилтэн биш; товчлол уншигчийг зогсоодог.",
     "commit": "26b20a5",
     "before": _spec("201fdb6", "fig = px_funnel(P, True)"), "after": _spec("26b20a5", "fig = px_funnel(P, True)")},
    {"key": "R02_data_accuracy", "date": "2026-11-15",
     "feedback": "chart bolon graph unen zuv data unen zuv baih ystoi buguud zuv durslej hiih",
     "chart": "Гадаад тоглогчийн бүх график (F26–F29, H6–H9)",
     "change": "Нэрийн дараалал холимог бичигдсэн («MILLER Ian» / «IAN Miller») нэг хүнийг хоёр болгож байсныг нэгтгэсэн "
               "(8 гадаад тоглогч буцаж нэгдсэн); MBA-ийн профайлд төрсөн он алдаатай тоглогчийг эх сурвалжаар засав.",
     "reason": "Нэг хүн хоёр тоолоход «дараа улиралд үлдсэн» хувь, насны дүн буруу гарч байсан.",
     "commit": "627ff35"},
    {"key": "R03_layout_overlap", "date": "2026-11-15",
     "feedback": "text davhardalt , layout grid geh met aldaa bn , mun ter tool chart-ruu orj ireed bn",
     "chart": "«Хэн дараа улиралд үлддэг вэ?» (бүх графикийн хэрэгслийн самбар)",
     "change": "Хэрэгслийн самбарыг баруун ирмэгт босоо болгож гарчиг дээрээс гаргасан; үлдэлтийн графикийг баганаас мөр "
               "болгож бүтэн өргөнөөр байрлуулсан; тасарсан тоо, хазайсан нэрийг засав.",
     "reason": "Бичиг давхцаж, хэрэгслийн самбар графикийн гарчгийг дарж байсан тул уншигдахгүй байсан.",
     "commit": "93cb400",
     "before": _spec("627ff35", 'fig = px_import_retention(load("imp_ret_cmp"), True)'),
     "after": _spec("93cb400", 'fig = px_import_retention(load("imp_ret_cmp"), True)')},
    {"key": "R04_chart_notes", "date": "2026-11-17",
     "feedback": "chart graph buriin door ymr nertei chart graph gedgiig bichih … niit buh chart-nii door saaralaar ymr data "
                 "set ashiglsniig bich data set file ner baih",
     "chart": "Бүх график ба хүснэгт",
     "change": "График бүрийн доор төрлийн нэр, «Хэрхэн унших», саарлаар дата ба файлын замыг нэмсэн; ийм тэмдэглэлгүй график "
               "үлдвэл тест унана.",
     "reason": "Уншигч ямар график, ямар датаас гэдгийг мэдэхгүй байсан; эх сурвалж ил тод байх ёстой.",
     "commit": "de2d586"},
    {"key": "R05_selected_player", "date": "2026-11-17",
     "feedback": "toglogchid hesgiin ehnii chart der «toglogchiin kart» hesgees songson toglogchiig chart der busad tsegees "
                 "uur uur durslej ontsloh",
     "chart": "Тоглогчдын цэгэн график (scatter)",
     "change": "Картад нээлттэй тоглогчийг шар од, нэрийн шошготой тодруулж, карт солигдоход од шилждэг болгосон.",
     "reason": "Карт ба график хоорондоо холбоогүй байсан тул тоглогч бусдын дунд хаана байгаа нь харагдахгүй байв.",
     "commit": "de2d586",
     "before": _spec("01932de", 'fig = px_scatter(P, "MIN", "PPG", "position", None)'),
     "after": _spec("de2d586", 'fig = px_scatter(P, "MIN", "PPG", "position", None, "byron-wesley")')},
    {"key": "R06_pareto_wording", "date": "2026-11-17",
     "feedback": "ehnii 2 toglogch , ehnii … toglogch gej yu ve hen be eda alda yu?",
     "chart": "Парето график",
     "change": "«Эхний N» шошгыг «Хамгийн их оноотой N тоглогч» болгож, hover-т тухайн байрын тоглогчийн нэрийг, доор нь "
               "онооны 80%-ийг авсан тоглогчдын жагсаалтыг нэмсэн.",
     "reason": "«Эхний» гэдэг нь юугаар эрэмбэлсэн, хэн болох нь ойлгогдохгүй байсан.",
     "commit": "de2d586",
     "before": _spec("01932de", _PARETO), "after": _spec("de2d586", _PARETO)},
    {"key": "R07_shots_filter", "date": "2026-11-17",
     "feedback": "toglogch +20 shidelttei gej yu gesen ug ve ?",
     "chart": "Шидэлтийн газрын зураг — тоглогчийн шүүлтүүр",
     "change": "«Тоглогч (энэ улиралд 20 ба түүнээс олон шидэлт хийсэн)» гэж бүтэн бичиж, тайлбар (help) ба нэр бүрийн хажууд "
               "шидэлтийн тоог нэмсэн; зөвхөн байршил нь бүртгэгдсэн шидэлтийг тоолдог болгосон.",
     "reason": "«20+» гэдэг товчлол ойлгогдоогүй; цөөн шидэлттэй тоглогчийн зураг санамсаргүй хэлбэлздэг тул хассан шалтгааныг хэлэх.",
     "commit": "de2d586"},
    {"key": "R08_game_flow", "date": "2026-11-17",
     "feedback": "toglogch minute tutam iluu oilgomjtoi bolovsrongui bolgoh «.... udaa soligdson» gej yu gej baiga ve chart der "
                 "cursor ochkhod jisheen : 4,5 min : 7 . 5 yg ali bag gedeg in medegdehgui bn",
     "chart": "Тоглолт минут тутам",
     "change": "Hover-т цаг, үе, баг бүрийн нэр ба оноо, хэн хэдэн оноогоор тэргүүлж байгааг бичдэг; тэргүүлэгч солигдсон мөчийг "
               "ромбоор, үеийн шошгыг дээр нь; «тэргүүлэгч N удаа солигдсон»-ыг тайлбарлаж, онооны самбар нэмсэн.",
     "reason": "«7–5» гэдэг тоо аль багийнх нь тодорхойгүй, «солигдсон» гэдэг юу солигдсон нь ойлгогдохгүй байсан.",
     "commit": "de2d586",
     "before": _spec("01932de", _FLOW), "after": _spec("de2d586", _FLOW)},
    {"key": "R09_stability", "date": "2026-11-17",
     "feedback": "toglogchiin yu in uliralaas ulirald hadgalagddag ve ene hesgiig iluu bolovsrongui bolgoh tailbar onovchgui bn",
     "chart": "Улирлаас улиралд хадгалагддаг үзүүлэлт",
     "change": "«Цэг = нэг тоглогч» гэсэн буруу тайлбарыг «мөр бүр = 1 үзүүлэлт» болгож засаж, гарчиг, тэнхлэгийг асуулт "
               "хэлбэрээр бичиж, тоглогч бүрийн хоёр улирлыг харьцуулах цэгэн графикийг нэмсэн.",
     "reason": "Тайлбар графикийн бодит утгатай зөрж байсан; хураангуй тоо (хамаарал) юуг хэлж байгааг жишээгээр харуулах.",
     "commit": "de2d586",
     "before": _spec("01932de", 'fig = px_stability(load("ins_stability"), True)'),
     "after": _spec("de2d586", 'fig = px_stability(load("ins_stability"), True)')},
    {"key": "R10_similar_rank", "date": "2026-11-17",
     "feedback": "mashin sergalt hesgiin «Hamgiin tustei 5 toglogch» husnegt baina uuniig toogoor erembleh hamgiin adilhan "
                 "medeej 1 dooshoo 2,3,4,5",
     "chart": "ML — хамгийн төстэй 5 тоглогчийн хүснэгт",
     "change": "«Эрэмбэ» багана (1 = хамгийн төстэй) нэмж, ялгаагаар өсөхөөр эрэмбэлсэн.",
     "reason": "Хүснэгтийн дараалал юугаар болохыг уншигч мэдэхгүй байсан.",
     "commit": "de2d586"},
    {"key": "R11_team_logos", "date": "2026-11-22",
     "feedback": "Every basketball team must have its own visual identity … Display each team's logo next to its name.",
     "chart": "Довтолгоо ба хамгаалалтын график (мөн байр, профайл, харьцуулалт, онооны самбар)",
     "change": "Багийн албан ёсны логог (MBA сайтын schema.org SportsTeam бичлэгээс) тойрог дотор нь, бусад газарт нэрийн "
               "хажууд харуулсан; лого алга бол үсгэн тэмдэг.",
     "reason": "Багийг нэрээс илүү хурдан таних; мэргэжлийн спортын платформын дүр төрх.",
     "commit": "8423be8",
     "before": _spec("de2d586", _OFFDEF), "after": _spec("8423be8", _OFFDEF_LOGO)},
    {"key": "R12_elo_axis", "date": "2026-11-22",
     "feedback": "design bolo chart graphic header footer geh met",
     "chart": "Багийн хүчний онооны явц (Elo)",
     "change": "Онцолсон багийн шугамыг бусдын дээр зурж, төгсгөлд сүүлийн оноог бичсэн; огноог давхцахгүй, хэвтээ болгож, "
               "«1500 = дундаж» шошго нэмсэн.",
     "reason": "Онцолсон баг саарал шугамуудын доор далдарч, огноо давхцаж байсан.",
     "commit": "67b3281",
     "before": _spec("8423be8", 'fig = px_elo(load("games"), "XAC Broncos")'),
     "after": _spec("67b3281", 'fig = px_elo(load("games"), "XAC Broncos")')},
    {"key": "R13_pareto_label", "date": "2026-11-22",
     "feedback": "design bolo chart graphic header footer geh met",
     "chart": "Парето график — 80%-ийн шошго",
     "change": "80%-д хүрэх цэгийг тод цэгээр тэмдэглэж, шошгыг баганатай давхцахгүй хоосон хэсэгт шилжүүлсэн.",
     "reason": "Шошго баганын дээр давхцаж, утсан дээр уншигдахгүй байсан.",
     "commit": "67b3281",
     "before": _spec("8423be8", _PARETO), "after": _spec("67b3281", _PARETO)},
    {"key": "R14_footer", "date": "2026-11-22",
     "feedback": "footer der zuer tovch text baih 2026 on mba analytics gedeg ch ymu eldev yanziin data edr source, hicheeliin "
                 "ner biy daalt geh hereggu",
     "chart": "Footer",
     "change": "Эх сурвалж, хичээлийн нэр, холбоостой том footer-ийг «© 2026 MBA Analytics» гэсэн нэг мөр болгосон.",
     "reason": "Эх сурвалж график бүрийн доор аль хэдийн бий; footer нь давхардсан, хэт их мэдээлэлтэй байсан.",
     "commit": "07c6528"},
    {"key": "R15_shadcn", "date": "2026-11-22",
     "feedback": "https://ui.shadcn.com/ эндээс comp awaj design-iig saijruulah",
     "chart": "Бүх карт, хүснэгт, таб, товч",
     "change": "shadcn/ui-ийн Card, Alert, Table, Badge, Tabs, Button, Input-ийн хэмжээ, хүрээ, сүүдрийг брэндийн өнгөтэй "
               "хослуулан шилжүүлсэн; «Гол дүгнэлт»-ийг Alert, байрын жагсаалтыг Table болгосон.",
     "reason": "Бүрэлдэхүүн бүр нэг дүрэмтэй, мэргэжлийн харагдацтай болох.",
     "commit": "4c2ca14"},
    {"key": "R16_plus_minus", "date": "2026-11-22",
     "feedback": "mnai data-nd NBA-ийн +/- (Plus/Minus) uzuulelt bnu data sudalgaa ba unen zuv baidal hangah",
     "chart": "Тоглогчийн карт ба «Талбай дээр байхад баг хэр сайн байсан бэ? (+/-)» график (шинэ)",
     "change": "MBA-д байхгүй +/- ба on/off-ийг тоглолтын явцын бичлэгээс тооцож нэмсэн; солилтын бичлэг бүрэн тоглолтоор л, "
               "95% хүрээтэй.",
     "reason": "Шалгалтаар найдвартай нь батлагдсан: минут 96% нь 1 минутын дотор таарч, багийн нийлбэр 90.1% нь яг таарсан.",
     "commit": "f40dff9"},
]
