"""Хэрэглэгчийн санал хүсэлтийн дараах графикийн өөрчлөлтийн бүртгэл (тайлангийн хавсралт).

feedback = хэрэглэгчийн бичсэн үг яг хэвээр (харилцааны түүхээс); change = юу өөрчлөгдсөн; reason = яагаад;
commit = өөрчлөлтийг оруулсан commit. before = өөрчлөлтийн өмнөх БОДИТ хувилбар (тухайн commit-ийн plots.py ба дата);
after = одоогийн эцсийн хувилбар (NOW). Зурах кодын хувьсагч: P = 2025–26 улирлын 5+ тоглолттой тоглогчид, load(нэр) = parquet.
Зураг: figures/revisions/<key>.png.

GALLERY = dashboard-ийн хуудас бүрийн «муу жишээ ба сонгосон хувилбар»: муу хувилбарыг ЗОРИУД зурсан (dashboard-д хэзээ ч
байгаагүй) бөгөөд тайланд тийм гэж тэмдэглэнэ; дизайны сонголтыг тайлбарлах зорилготой.
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


NOW = "WORKTREE"  # одоогийн (эцсийн) хувилбар: repo-ийн ажлын хавтас


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
     "before": _spec("201fdb6", "fig = px_funnel(P, True)"), "after": _spec(NOW, "fig = px_funnel(P, True)")},
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
     "after": _spec(NOW, 'fig = px_import_retention(load("imp_ret_cmp"), True)')},
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
     "after": _spec(NOW, 'fig = px_scatter(P, "MIN", "PPG", "position", None, "byron-wesley")')},
    {"key": "R06_pareto_wording", "date": "2026-11-17",
     "feedback": "ehnii 2 toglogch , ehnii … toglogch gej yu ve hen be eda alda yu?",
     "chart": "Парето график",
     "change": "«Эхний N» шошгыг «Хамгийн их оноотой N тоглогч» болгож, hover-т тухайн байрын тоглогчийн нэрийг, доор нь "
               "онооны 80%-ийг авсан тоглогчдын жагсаалтыг нэмсэн.",
     "reason": "«Эхний» гэдэг нь юугаар эрэмбэлсэн, хэн болох нь ойлгогдохгүй байсан.",
     "commit": "de2d586",
     "before": _spec("01932de", _PARETO), "after": _spec(NOW, _PARETO)},
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
     "before": _spec("01932de", _FLOW), "after": _spec(NOW, _FLOW)},
    {"key": "R09_stability", "date": "2026-11-17",
     "feedback": "toglogchiin yu in uliralaas ulirald hadgalagddag ve ene hesgiig iluu bolovsrongui bolgoh tailbar onovchgui bn",
     "chart": "Улирлаас улиралд хадгалагддаг үзүүлэлт",
     "change": "«Цэг = нэг тоглогч» гэсэн буруу тайлбарыг «мөр бүр = 1 үзүүлэлт» болгож засаж, гарчиг, тэнхлэгийг асуулт "
               "хэлбэрээр бичиж, тоглогч бүрийн хоёр улирлыг харьцуулах цэгэн графикийг нэмсэн.",
     "reason": "Тайлбар графикийн бодит утгатай зөрж байсан; хураангуй тоо (хамаарал) юуг хэлж байгааг жишээгээр харуулах.",
     "commit": "de2d586",
     "before": _spec("01932de", 'fig = px_stability(load("ins_stability"), True)'),
     "after": _spec(NOW, 'fig = px_stability(load("ins_stability"), True)')},
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
     "before": _spec("de2d586", _OFFDEF), "after": _spec(NOW, _OFFDEF_LOGO)},
    {"key": "R12_elo_axis", "date": "2026-11-22",
     "feedback": "design bolo chart graphic header footer geh met",
     "chart": "Багийн хүчний онооны явц (Elo)",
     "change": "Онцолсон багийн шугамыг бусдын дээр зурж, төгсгөлд сүүлийн оноог бичсэн; огноог давхцахгүй, хэвтээ болгож, "
               "«1500 = дундаж» шошго нэмсэн.",
     "reason": "Онцолсон баг саарал шугамуудын доор далдарч, огноо давхцаж байсан.",
     "commit": "67b3281",
     "before": _spec("8423be8", 'fig = px_elo(load("games"), "XAC Broncos")'),
     "after": _spec(NOW, 'fig = px_elo(load("games"), "XAC Broncos")')},
    {"key": "R13_pareto_label", "date": "2026-11-22",
     "feedback": "design bolo chart graphic header footer geh met",
     "chart": "Парето график — 80%-ийн шошго",
     "change": "80%-д хүрэх цэгийг тод цэгээр тэмдэглэж, шошгыг баганатай давхцахгүй хоосон хэсэгт шилжүүлсэн.",
     "reason": "Шошго баганын дээр давхцаж, утсан дээр уншигдахгүй байсан.",
     "commit": "67b3281"},
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


_LATEST_ELO = """
g = load("games"); g = g[g.season == SEASON].sort_values(["date", "game_id"])
rows = pd.concat([g[["date", "home_team", "elo_post_home"]].set_axis(["date", "team", "elo"], axis=1),
                  g[["date", "away_team", "elo_post_away"]].set_axis(["date", "team", "elo"], axis=1)])
elo = rows.sort_values("date").groupby("team").elo.last()
from src.build_dashboard_data import win_probability
coefs = load("elo_coefs").coef.to_numpy()
p_win = win_probability(float(elo["BCH Knights"]), float(elo["Bishrelt Metal"]), coefs)[0]
"""
_SHOTS = 'sh = load("shots"); sh = sh[sh.season == SEASON]; league_pps = float(sh[sh.location_ok].pts.mean())'
_TG = 'tg = load("team_games"); tg = tg[tg.season == SEASON]'
_PM = 'pm = load("plus_minus"); pm = pm[(pm.season == SEASON) & (pm.minutes >= 200)]'
_BAD = "fig.update_layout(template='plotly', font=dict(family='Arial', size=12))"  # Plotly-ийн анхдагч загвар

GALLERY = [
    {"key": "G01_overview_pareto", "page": "Тойм", "chart": "Онооны хуваарь",
     "bad": "170 хэсэгтэй дугуй диаграм: өнцгөөр 170 хэсгийг харьцуулах боломжгүй, өнгө нь солонгын дараалал тул утгагүй, "
            "тайлбар (legend) нь 170 нэртэй; «цөөн тоглогч онооны ихэнхийг авдаг» гэсэн олдвор харагдахгүй.",
     "good": "Оноогоор эрэмбэлсэн багана + нийлбэр хувийн шугам (Парето): 80%-д хүрэх цэг шууд уншигдана; өнгө нь гадаад/дотоодыг "
             "ялгана; сүүдэр = 95% хүрээ.",
     "bad_code": 'pl = load("pareto_league"); pl = pl[pl.season == SEASON]\n'
                 'fig = go.Figure(go.Pie(labels=pl.player_name, values=pl.value, textinfo="none", sort=False))\n'
                 'fig.update_layout(title="PTS by player", height=460)\n' + _BAD,
     "good_code": _PARETO},
    {"key": "G02_players_scatter", "page": "Тоглогчид", "chart": "Тоглогчийн харьцуулалт",
     "bad": "Бүх цэг дээр нэр бичсэн тул бичиг давхцаж уншигдахгүй; өнгө (өндөр) нь асуулттай холбоогүй, солонгын (Jet) шкал "
            "өнгөт харалгүй хүнд ялгарахгүй; тэнхлэгийн нэр «TS%», «PPG» гэх товчлол.",
     "good": "Ойлгомжтой тэнхлэг (минут ба оноо), өнгө = байрлал, картад сонгосон тоглогч шар одоор; нэрийг зөвхөн hover-т.",
     "bad_code": 'fig = go.Figure(go.Scatter(x=P.ts_pct, y=P.PPG, mode="markers+text", text=P.player_name, '
                 'textfont=dict(size=9), marker=dict(color=P.height_cm, colorscale="Jet", size=9, showscale=True)))\n'
                 'fig.update_layout(title="TS% vs PPG", xaxis_title="TS%", yaxis_title="PPG", height=460)\n' + _BAD,
     "good_code": 'fig = px_scatter(P, "MIN", "PPG", "position", None, "byron-wesley")'},
    {"key": "G03_teams_factors", "page": "Багууд", "chart": "Ялалтын 4 хүчин зүйл",
     "bad": "4 өөр хэмжүүрийг (оновч ~0.5, торгууль ~0.2) нэг тэнхлэгт 40 баганаар: багуудыг харьцуулахад нүд тэнхлэг, тайлбар, "
            "өнгө хооронд гүйнэ; «бага нь сайн» (бөмбөг алдалт) үзүүлэлт бусадтайгаа адил өнгөтэй тул чиглэл андуурагдана.",
     "good": "Үзүүлэлт бүр тусдаа самбарт, лигийн дунджаас хазайлтаар: цэнхэр = дунджаас сайн, улаан-улбар = сул (бага нь сайн "
             "үзүүлэлтэд чиглэлийг эргүүлсэн).",
     "bad_code": _TG + '\nm = tg[tg.phase == "regular"].groupby("team")[["efg", "tov_pct", "orb_pct", "ftr"]].mean()\n'
                 'fig = go.Figure([go.Bar(name=c, x=m.index, y=m[c]) for c in m.columns])\n'
                 'fig.update_layout(barmode="group", title="eFG% TOV% ORB% FTr by team", height=440)\n' + _BAD,
     "good_code": _TG + "\nfig = px_four_factors(tg, None)"},
    {"key": "G04_shots_map", "page": "Шидэлт ба тоглолтын явц", "chart": "Шидэлтийн газрын зураг",
     "bad": "15 мянга орчим цэг давхцаж (overplotting) нягт газар нэг өнгийн толбо болно; ногоон/улаан нь өнгөт харалгүй хүнд "
            "ялгарахгүй; талбайн шугамгүй тул байрлал уншигдахгүй; «хаанаас шидэх нь ашигтай вэ» гэсэн асуултад хариулахгүй.",
     "good": "1 × 1 м нүдээр нэгтгэсэн: хэмжээ = шидэлтийн тоо, өнгө = шидэлт бүрт ногдох оноо лигийн дунджаас дээш/доош; "
             "талбайн шугамтай.",
     "bad_code": _SHOTS + '\ns = sh[sh.location_ok]\nfig = go.Figure(go.Scattergl(x=s.court_x, y=s.court_y, mode="markers", '
                 'marker=dict(size=4, color=np.where(s.made, "green", "red"))))\n'
                 'fig.update_layout(title="Shots", height=440)\n' + _BAD,
     "good_code": _SHOTS + '\nfig = px_shot_map(sh, league_pps, "Бүх лиг: шидэлтийн газрын зураг")'},
    {"key": "G05_game_flow", "page": "Шидэлт ба тоглолтын явц", "chart": "Тоглолт минут тутам",
     "bad": "Хоёр багийн хуримтлагдсан онооны шугам бараг давхцаж, хэн хэдэн оноогоор тэргүүлж байгааг нүдээр хасаж тооцох "
            "шаардлагатай; тэргүүлэгч солигдсон мөч харагдахгүй.",
     "good": "Онооны ЗӨРҮҮг шууд зурсан (дээш = гэрийн баг, доош = зочин баг тэргүүлсэн), тэргүүлэгч солигдсон мөч ромбоор, "
             "доор нь ялах магадлал.",
     "bad_code": 'gl = load("game_list"); gl = gl[gl.season == SEASON]; g = gl.loc[gl.lead_changes.idxmax()]\n'
                 'f = load("game_flow"); f = f[f.game_id == g.game_id].sort_values("elapsed")\n'
                 'fig = go.Figure([go.Scatter(x=f.elapsed, y=f.home, name="home"), go.Scatter(x=f.elapsed, y=f.away, name="away")])\n'
                 'fig.update_layout(title="Score", height=440)\n' + _BAD,
     "good_code": _FLOW},
    {"key": "G06_insights_lead", "page": "Олдворууд", "chart": "Тэргүүлэл хэр найдвартай вэ",
     "bad": "Босоо тэнхлэг 50%-аас эхэлсэн тул ялгаа хэт томорч харагдана; 95% хүрээгүй тул цөөн тоглолттой бүлгийн (16+) тоо "
            "ямар найдвартай нь мэдэгдэхгүй; ганц мөчийг л харуулна.",
     "good": "Тэнхлэг 20%-аас бодит хэмжээгээр, гурван мөчийг (1-р үе, хагас, 3-р үе) нэг дор, 95% хүрээтэй.",
     "bad_code": 'd = load("ins_lead"); d = d[d.checkpoint == "Хагас"]\n'
                 'fig = go.Figure(go.Bar(x=d.bin, y=d.est, marker_color=["#ff0000", "#ff9900", "#ffff00", "#00ff00", "#0000ff"]))\n'
                 'fig.update_yaxes(range=[0.5, 1]); fig.update_layout(title="Win% by lead", height=420)\n' + _BAD,
     "good_code": 'fig = px_lead_safety(load("ins_lead"), True)'},
    {"key": "G07_ml_quantile", "page": "Машин сургалт", "chart": "Ялалтын магадлал",
     "bad": "Хоёр хэсэгтэй дугуй диаграм хувийг өнгөөр л давтана; магадлалыг «20-оос хэд» гэж ойлгоход хэцүү, "
            "тодорхой бус байдал харагдахгүй.",
     "good": "20 тойрог = 20 удаа тоглосон гэж төсөөлөхөд хэдийг нь аль баг ялах вэ (quantile dot plot); тоолж болох тул "
             "магадлалыг ойлгоход хялбар (Kay et al., 2016).",
     "bad_code": _LATEST_ELO + 'fig = go.Figure(go.Pie(labels=["BCH Knights", "Bishrelt Metal"], values=[p_win, 1 - p_win], '
                 'pull=[0.1, 0]))\nfig.update_layout(title="Win probability", height=420)\n' + _BAD,
     "good_code": _LATEST_ELO + 'fig = px_quantile_dots(p_win, 20, "BCH Knights", "Bishrelt Metal")'},
    {"key": "G08_players_plus_minus", "page": "Тоглогчид", "chart": "+/- (талбай дээрх онооны зөрүү)",
     "bad": "Нийт +/- (40 минутад шилжүүлээгүй) тул олон минут тоглосон тоглогч давуу; 100 гаруй тоглогчийг цагаан толгойн "
            "дарааллаар, нэргүй, хүрээгүй харуулсан тул хэн өндөр, хэн найдвартай нь харагдахгүй.",
     "good": "40 минутад шилжүүлж, хамгийн өндөр ба бага 8 тоглогчийг эрэмбэлэн 95% хүрээтэй; 0-ийн шугам, өнгө = гадаад/дотоод.",
     "bad_code": _PM + '\nd = pm.sort_values("player_id")\nfig = go.Figure(go.Bar(x=d.player_id, y=d.pm, '
                 'marker=dict(color=d.pm, colorscale="Rainbow")))\n'
                 'fig.update_xaxes(showticklabels=False); fig.update_layout(title="+/-", height=420)\n' + _BAD,
     "good_code": _PM + '\nsel = pd.concat([pm.nlargest(8, "pm40"), pm.nsmallest(8, "pm40")]).drop_duplicates("player_id")\n'
                  'fig = px_plus_minus(sel, True, None)'},
]
