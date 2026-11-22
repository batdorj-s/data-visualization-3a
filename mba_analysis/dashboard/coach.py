"""Дасгалжуулагчийн дүгнэлт: график бүрийн доор датаас ТООЦООЛЖ гаргасан 1–3 практик зөвлөмж.

Бүх тоо тухайн мөчийн шүүлтүүрийн датаас ирдэг тул шүүлтүүр солигдоход өгүүлбэр ч өөрчлөгдөнө. Зөвлөмж нь ажиглалтад
тулгуурласан санал бөгөөд шалтгаан-үр дагаврыг баталсан дүгнэлт биш. Латин үсгээр бичсэн баг, тоглогчийн нэрэнд монгол
нөхцөл залгахгүйн тулд «… баг», «… тоглогч» гэж ард нь үг нэмнэ.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from src.uncertainty import funnel_limits

POSITIONS = {"PG": "тоглуулагч", "SG": "хамгаалагч-шидэгч", "SF": "жижиг довтлогч", "PF": "хүчтэй довтлогч", "C": "төв"}
FACTOR_ADVICE = {  # (нэр, ялалтын хувьтай эерэг холбоотой эсэх, бэлтгэлийн зөвлөмж)
    "efg": ("шидэлтийн оновч", True, "шидэлтийн сонголт ба оновчийн дасгалд"),
    "tov_pct": ("бөмбөг алдалт", False, "бөмбөг хамгаалах, дамжуулалтын нарийвчлалд"),
    "orb_pct": ("довтолгооны самбар", True, "довтолгооны самбарт тэмцэхэд"),
    "ftr": ("торгууль авалт", True, "сагс руу дайрч торгууль авахад"),
}


def _names(s: pd.Series, k: int = 3) -> str:
    return ", ".join(str(x) for x in s.head(k))


def _strength(r: float) -> str:
    a = abs(r)
    return "хүчтэй" if a >= 0.6 else "дунд зэрэг" if a >= 0.3 else "сул"


# ---------------------------------------------------------------- Тойм
def standings(table: pd.DataFrame) -> list[str]:
    """table: index = баг, багана W, L, pct, net (үндсэн шат)."""
    if len(table) < 2:
        return []
    a, b = table.iloc[0], table.iloc[1]
    gap = int(a.W - b.W)
    head = f"Тэргүүлэгч **{table.index[0]}** баг ({int(a.W)}–{int(a.L)}) 2-р байрын {table.index[1]} баг"
    out = [f"{head}аас {gap} ялалтаар илүү." if gap > 2 else
           f"{head}аас ердөө {gap} ялалтаар илүү — тэргүүллийн төлөөх өрсөлдөөн ширүүн." if gap > 0 else
           f"{head}тай ижил тооны ялалттай бөгөөд ялалтын хувиар л түрүүлж байна — өрсөлдөөн ширүүн."]
    best_net = table.net.idxmax()
    if best_net != table.index[0]:
        out.append(f"Онооны зөрүүгээр хамгийн давуу нь **{best_net}** баг ({table.net.max():+.1f}). Байраасаа илүү хүчтэй "
                   "байж болзошгүй — ойролцоо оноотой тоглолтуудад азгүйтсэн байх магадлалтай.")
    else:
        out.append(f"Тэргүүлэгч баг онооны зөрүүгээр ч тэргүүлж байна ({a.net:+.1f}), өөрөөр хэлбэл ялалт нь азаас бус "
                   "тогтмол давуу тоглолтоос ирж байна.")
    return out


def pareto_league(pareto_df: pd.DataFrame) -> list[str]:
    d = pareto_df.sort_values("rank")
    if len(d) < 10:
        return []
    top = d.head(10)
    n_imp = int(top.is_import.astype(bool).sum())
    share = top.cum_share.iloc[-1]
    return [f"Шилдэг 10 оноо авагч лигийн нийт онооны **{share:.0%}**-ийг авдаг; тэдний **{n_imp}** нь гадаад тоглогч.",
            "Хамгаалалтын төлөвлөгөө: оноо цөөн тоглогчид төвлөрсөн тул өрсөлдөгчийн шилдэг оноо авагчийг давхар "
            "хамгаалалтаар хязгаарлах нь үр дүнтэй." if share >= 0.4 else
            "Лигийн хэмжээнд оноо олон тоглогчид тархсан тул нэг од тоглогчийг хаах бус, багаараа хамгаалах сахилга бат "
            "илүү чухал. Багийн түвшний хуваарийг «Багууд» хуудаснаас харна уу."]


def region_map(meta: pd.DataFrame, standings_df: pd.DataFrame, season: str) -> list[str]:
    s = standings_df[standings_df.season == season].merge(meta[["team_key", "region"]], on="team_key")
    s = s[s.region.isin(["Улаанбаатар", "Орон нутаг"])].assign(pct=lambda d: d.W / (d.W + d.L))
    if s.region.nunique() < 2:
        return []
    g = s.groupby("region").agg(n=("pct", "size"), pct=("pct", "mean"))
    ub, rural = g.loc["Улаанбаатар"], g.loc["Орон нутаг"]
    return [f"Улаанбаатарын {int(ub.n)} баг дунджаар **{ub.pct:.0%}**, орон нутгийн {int(rural.n)} баг **{rural.pct:.0%}** "
            "ялалттай.",
            "Баг цөөн тул бүсийн ялгааг баттай дүгнэхгүй: багийн хүчийг байршлаас илүү бүрэлдэхүүнээр нь харах нь зөв."]


def fan(tg: pd.DataFrame, team: str) -> list[str]:
    t = tg[tg.team == team].sort_values("date")
    if len(t) < 12:
        return []
    first, last = t.win.head(10).mean(), t.win.tail(10).mean()
    diff = round(last - first, 2)
    trend = ("хэлбэр нь сайжирсан" if diff >= 0.2 else "хэлбэр нь суларсан" if diff <= -0.2
             else "тогтвортой тоглож байна")
    end = t.iloc[-1]
    return [f"**{team}** баг эхний 10 тоглолтдоо {first:.0%}, сүүлийн 10 тоглолтдоо **{last:.0%}** ялалттай — {trend}.",
            f"Одоогийн ялалтын хувь {end.winpct:.0%}; жинхэнэ түвшин нь {end.lo95:.0%}–{end.hi95:.0%} хооронд байх "
            "магадлалтай. Сүүдэр өргөн бол цөөн тоглолтоор хэт яаран дүгнэхгүй."]


# ---------------------------------------------------------------- Багууд
def team_pareto(pt: pd.DataFrame, team: str) -> list[str]:
    d = pt.sort_values("rank")
    if len(d) < 3:
        return []
    top2 = d.cum_share.iloc[1]
    n80 = int(np.argmax(d.cum_share.to_numpy() >= 0.8)) + 1
    out = [f"**{team}** багийн онооны **{top2:.0%}** нь хоёр тоглогчоос ({_names(d.player_name, 2)}) ирдэг; онооны 80%-д "
           f"{n80} тоглогч хүрэлцэнэ."]
    out.append("Цөөн тоглогчоос хамааралтай: тэднийг гэмтэл, хурц хамгаалалтаас хамгаалж, сэлгээний тоглогчдын оноо авах "
               "чадварыг нэмэх шаардлагатай." if n80 <= 5 else
               "Оноо олон тоглогчид тархсан тул өрсөлдөгч нэг тоглогчийг хааж зогсоох боломж бага — энэ нь багийн давуу тал.")
    return out


def elo(games: pd.DataFrame, team: str, season: str) -> list[str]:
    g = games[games.season == season].sort_values(["date", "game_id"])
    rows = pd.concat([g[["date", "home_team", "elo_post_home"]].set_axis(["date", "team", "elo"], axis=1),
                      g[["date", "away_team", "elo_post_away"]].set_axis(["date", "team", "elo"], axis=1)])
    t = rows[rows.team == team].sort_values("date")
    if len(t) < 6:
        return []
    now, peak = t.elo.iloc[-1], t.elo.max()
    k = min(10, len(t) - 1)
    delta = now - t.elo.iloc[-1 - k]
    return [f"**{team}** багийн хүчний оноо одоо {now:.0f} (улирлын дээд цэг {peak:.0f}); сүүлийн {k} тоглолтод "
            f"**{delta:+.0f}**.",
            "Хүчний оноо өсөж байгаа нь хүчтэй багуудыг ялж эхэлснийг илтгэнэ." if delta > 0 else
            "Хүчний оноо буурч байна: сүүлийн тоглолтуудын бичлэгийг үзэж, хаана оноо алдаж байгааг шалгах цаг."]


def standings_table(table: pd.DataFrame) -> list[str]:
    """table: index = баг, багана Оноо, Алдсан, Зөрүү."""
    if table.empty:
        return []
    return [f"Довтолгоогоор **{table.Оноо.idxmax()}** баг (тоглолтод {table.Оноо.max():.1f} оноо), хамгаалалтаар "
            f"**{table.Алдсан.idxmin()}** баг ({table.Алдсан.min():.1f} оноо алддаг) тэргүүлж байна.",
            "Байрын хүснэгтийг ялалт–хожигдлоор бус «Зөрүү» баганаар эрэмбэлж үзээрэй: багийн жинхэнэ хүчийг ялалтын "
            "хувиас илүү тогтвортой харуулдаг."]


def four_factors(tg: pd.DataFrame, highlight: str | None) -> list[str]:
    reg = tg[tg.phase == "regular"]
    m = reg.groupby("team")[[*FACTOR_ADVICE, "win"]].mean()
    if len(m) < 4:
        return []
    r = m[list(FACTOR_ADVICE)].corrwith(m.win)
    signed = pd.Series({k: r[k] if FACTOR_ADVICE[k][1] else -r[k] for k in r.index})
    key = signed.idxmax()
    name, _, advice = FACTOR_ADVICE[key]
    out = [f"Энэ улиралд багийн ялалтын хувьтай хамгийн нягт холбоотой нь **{name}** (хамаарал {r[key]:+.2f}, {len(m)} баг). "
           f"Бэлтгэлийн цагийн ихэнхийг {advice} зориулах нь хамгийн их үр өгөх магадлалтай."]
    if highlight in m.index:
        z = (m[list(FACTOR_ADVICE)] - m[list(FACTOR_ADVICE)].mean()) / m[list(FACTOR_ADVICE)].std()
        z = z.loc[highlight] * pd.Series({k: 1 if FACTOR_ADVICE[k][1] else -1 for k in FACTOR_ADVICE})
        out.append(f"**{highlight}** багийн хамгийн сул тал — {FACTOR_ADVICE[z.idxmin()][0]}, хамгийн хүчтэй тал — "
                   f"{FACTOR_ADVICE[z.idxmax()][0]}.")
    return out


def compare(t1: str, t2: str, rows: list[tuple]) -> list[str]:
    """rows: (шошго, тайлбар, утга1, утга2, формат, их нь сайн)."""
    adv = []
    for lab, _, v1, v2, _, hb in rows:
        base = max(abs(v1), abs(v2), 1e-9)
        adv.append((lab, (v1 - v2) / base * (1 if hb else -1)))
    wins1 = sum(d > 0 for _, d in adv)
    best1 = max(adv, key=lambda x: x[1])
    best2 = min(adv, key=lambda x: x[1])
    out = [f"**{t1}** баг {len(adv)} үзүүлэлтийн {wins1}-д, **{t2}** баг {len(adv) - wins1}-д давуу."]
    if best2[1] < 0:
        out.append(f"{t1} багийн тоглолтын төлөвлөгөө: өрсөлдөгчийн хамгийн том давуу тал болох «{best2[0]}» "
                   f"үзүүлэлтийг хязгаарлаж, өөрийн давуу тал болох «{best1[0]}» үзүүлэлтээр тоглолтыг удирдах.")
    return out


# ---------------------------------------------------------------- Тоглогчид
def scatter(players: pd.DataFrame, x: str, y: str, labels: dict) -> list[str]:
    d = players[["player_name", x, y]].dropna()
    if len(d) < 5 or d[x].std() == 0 or d[y].std() == 0:
        return []
    r = d[x].corr(d[y])
    slope, icpt = np.polyfit(d[x], d[y], 1)
    over = d.assign(res=d[y] - (slope * d[x] + icpt)).sort_values("res", ascending=False)
    lx, ly = labels.get(x, x), labels.get(y, y)
    return [f"«{lx}» ба «{ly}» хоёрын хамаарал {_strength(r)} (r = {r:.2f}). «{ly}» үзүүлэлтээр тэргүүлэгчид: "
            f"**{_names(d.sort_values(y, ascending=False).player_name)}**.",
            f"«{lx}» үзүүлэлтийнхээ түвшинд хүлээгдэхээс хамгийн их давсан тоглогч: **{over.player_name.iloc[0]}**. Ийм тоглогч "
            "илүү үүрэг, минут өгөхөд бэлэн нөөц байж болно."]


def player_card(row: pd.Series, players: pd.DataFrame, pm: pd.DataFrame) -> list[str]:
    pct = {lab: (players[c] < row[c]).mean() for c, lab in (("PPG", "оноо"), ("RPG", "самбар"), ("APG", "дамжуулалт"))
           if c in players and pd.notna(row.get(c))}
    if not pct:
        return []
    best = max(pct, key=pct.get)
    worst = min(pct, key=pct.get)
    out = [f"Шүүлтүүрт тохирох {len(players)} тоглогчтой харьцуулахад **{best}** үзүүлэлтээр дээд "
           f"{max(1 - pct[best], 0.01):.0%}-д, {worst} үзүүлэлтээр дээд {max(1 - pct[worst], 0.01):.0%}-д багтана."]
    if len(pm):
        r = pm.iloc[0]
        out.append("Талбай дээр байхад баг нь баттай давуу (+/- хүрээ бүхэлдээ 0-ээс дээш) — эхний бүрэлдэхүүний тоглогч."
                   if r.pm40_lo > 0 else
                   "Талбай дээр байхад баг нь баттай сул (+/- хүрээ бүхэлдээ 0-ээс доош): хамт тоглож буй бүрэлдэхүүнийг "
                   "нь эргэн харах хэрэгтэй." if r.pm40_hi < 0 else
                   "+/- хүрээ 0-ийг дайрсан тул багийн үзүүлэлтэд үзүүлэх нөлөөг нь одоогоор баттай хэлэх боломжгүй.")
    return out


def funnel(players: pd.DataFrame) -> list[str]:
    df = players.assign(tsa=players.FGA.fillna(0) + 0.44 * players.FTA.fillna(0))
    df = df[(df.tsa > 0) & df.ts_pct.notna()]
    if df.empty:
        return []
    p0 = df.PTS_total.sum() / (2 * df.tsa.sum())
    lo, hi = funnel_limits(p0, df.tsa.to_numpy(), 1.96)
    above = df[df.ts_pct > hi].sort_values("tsa", ascending=False)
    below = df[df.ts_pct < lo].sort_values("tsa", ascending=False)
    out = [f"Оновч нь лигийн дунджаас баттай өндөр **{len(above)}** тоглогч бий"
           + (f" (хамгийн олон шидсэн нь: **{_names(above.player_name)}**). Тэдэнд илүү олон шидэлт олгох нь ашигтай."
              if len(above) else ".")]
    if len(below):
        out.append(f"Баттай доогуур {len(below)} тоглогч (олон шидэлттэй нь: {_names(below.player_name, 2)}) — шидэлтийн "
                   "сонголтыг нь видео бичлэгээр хамт шинжлэх хэрэгтэй.")
    return out


def dot_ci(top_n: pd.DataFrame) -> list[str]:
    d = top_n.sort_values("est", ascending=False)
    if len(d) < 2:
        return []
    a = d.iloc[0]
    overlap = int((d.iloc[1:].hi >= a.lo).sum())
    return [f"Эхний {len(d)} тоглогчийн {overlap} нь 1-р байрын **{a.player_name}** тоглогчтой хүрээгээрээ давхцаж байна."
            + (" Өөрөөр хэлбэл тэргүүлэгч нь баттай тэргүүлж байна." if overlap == 0 else
               " Тиймээс «лигийн шилдэг оноо авагч» гэж баттай нэрлэхэд дата хангалтгүй.")]


def plus_minus(pm: pd.DataFrame) -> list[str]:
    if pm.empty:
        return []
    pos = pm[pm.pm40_lo > 0].sort_values("pm40", ascending=False)
    out = [f"+/- хүрээ нь бүхэлдээ 0-ээс дээш **{len(pos)}** тоглогч"
           + (f": **{_names(pos.player_name)}**. Тэд талбай дээр байхад баг нь тогтмол давуу тоглосон." if len(pos) else
              " алга — энэ шүүлтүүрт нэг ч тоглогчийн нөлөө баттай биш.")]
    oo = pm.dropna(subset=["on_off40"])
    if len(oo):
        top = oo.loc[oo.on_off40.idxmax()]
        out.append(f"Талбай дээр байх, сэлгээнд суух хоёрын ялгаа хамгийн их нь **{top.player_name}** тоглогч "
                   f"({top.on_off40:+.1f} оноо / 40 минут): түүнийг сэлгэх мөчийг хамгийн сайн тооцох хэрэгтэй. Сэлгээнд "
                   "цөөн минут суусан тоглогчийн энэ тоо их хэлбэлздэг тул чиг хандлага гэж л ойлгоно.")
    return out


# ---------------------------------------------------------------- Гадаад тоглогч
def import_hypotheses(hyp: pd.DataFrame) -> list[str]:
    ok = int((hyp.verdict == "Батлагдсан").sum())
    return [f"{len(hyp)} таамаглалаас **{ok}** нь батлагдсан. Гадаад тоглогч сонгохдоо зөвхөн батлагдсан хэв маягт "
            "тулгуурлаж, бусдыг дата нэмэгдтэл шийдвэрийн үндэс болгохгүй байх нь зөв."]


def import_pipeline(bg: pd.DataFrame) -> list[str]:
    found = bg[bg.status == "олдсон"]
    if found.empty:
        return []
    lv = found.level.value_counts()
    return [f"Баталгаажсан {len(found)} тоглогчийн хамгийн олон нь **{lv.index[0]}** ({lv.iloc[0]}), дараа нь "
            f"{lv.index[1]} ({lv.iloc[1]}) түвшнээс ирсэн." if len(lv) > 1 else
            f"Баталгаажсан тоглогчдын ихэнх нь **{lv.index[0]}** түвшнээс ирсэн.",
            "Сонгон шалгаруулалтын гол зах зээл эдгээр лиг: тоглогч хайхдаа эндээс эхлэх нь цаг хэмнэнэ."]


def import_retention(cmp: pd.DataFrame, ret: pd.DataFrame) -> list[str]:
    big = cmp.loc[(cmp["diff"] / cmp.med_no.abs()).idxmax()]
    fmt = "{:.0%}" if abs(big.med_no) < 1.5 else "{:.1f}"
    return [f"{len(ret)} гадаад тоглогчоос дараа улиралд **{int(ret.stayed.sum())}** нь л үлдсэн. Үлдсэн ба явсан тоглогчдын "
            f"хамгийн том ялгаа «{big.label}» үзүүлэлтэд байна (голч {fmt.format(big.med_yes)} ба {fmt.format(big.med_no)})"
            + (", ялгаа баттай." if big.clear else ", гэвч цөөн тоглогч тул баттай биш."),
            "Шинэ улирлын бэлтгэлийг гадаад тоглогчгүйгээр эхлүүлэх нь элбэг тул багийн тоглолтын системийг дотоодын "
            "тоглогчид дээр тогтвортой барих нь чухал."]


def import_position(pos: pd.DataFrame, season: str) -> list[str]:
    s = pos[pos.season == season]
    if s.empty:
        return []
    top = s.loc[s.share.idxmax()]
    return [f"{season.replace('-20', '–')} улиралд **{POSITIONS.get(top.position, top.position)}** байрлалын минутын "
            f"**{top.share:.0%}**-ийг гадаад тоглогч тоглосон — бусад байрлалаас хамгийн өндөр.",
            "Энэ байрлалд дотоодын тоглогч бага минут авч байгаа нь залуу дотоод тоглогч бэлтгэх хэрэгцээг харуулж "
            "магадгүй."]


def import_age(im: pd.DataFrame) -> list[str]:
    d = im.dropna(subset=["age", "PPG", "pts36"])
    if len(d) < 5:
        return []
    r1, r2 = d.age.corr(d.PPG), d.age.corr(d.pts36)
    return [f"Нас ба тоглолтын онооны хамаарал r = {r1:.2f}, харин нас ба 36 минутад ногдох онооных r = **{r2:.2f}**.",
            "Минутын нөлөөг хасахад хамаарал суларч байгаа тул ахимаг тоглогчийн илүү оноо нь хэсэгчлэн илүү минут "
            "авснаас үүдэлтэй: туршлагыг дангаар нь сонгох шалгуур болгоход хангалтгүй." if abs(r2) < abs(r1) else
            "Минутын нөлөөг хассан ч хамаарал хадгалагдаж байгаа тул туршлагатай гадаад тоглогч бодитоор илүү бүтээмжтэй."]


def replacement(sim: pd.DataFrame, name: str) -> list[str]:
    if sim.empty:
        return []
    r = sim.iloc[0]
    return [f"**{name}** тоглогчийг орлох хамгийн төстэй хувилбар: **{r.player_name}** ({r.season.replace('-20', '–')}, "
            f"{r.team} баг). Гэрээ, цалингийн боломжийг тусад нь шалгах хэрэгтэй."]


# ---------------------------------------------------------------- Шидэлт ба тоглолтын явц
def shot_zones(z: pd.DataFrame, s: pd.DataFrame, league_pps: float, who: str) -> list[str]:
    if z.empty:
        return []
    best = z.loc[z.pps.idxmax()]
    out = [f"**{who}**: хамгийн ашигтай бүс «{best.zone}» (шидэлт бүрт {best.pps:.2f} оноо; лигийн дундаж {league_pps:.2f})."]
    mid = z[z.zone == "Дунд зай"]
    games = s[s.location_ok].game_id.nunique()
    if len(mid) and games:
        m = mid.iloc[0]
        gain = 0.2 * m.n / games * (best.pps - m.pps)
        if gain > 0:
            out.append(f"Шидэлтийн {m.share:.0%} нь дунд зайнаас ({m.pps:.2f} оноо). Тэдгээрийн 5 тутмын 1-ийг «{best.zone}» "
                       f"бүс рүү шилжүүлбэл оновч хэвээр гэж үзэхэд тоглолтод ойролцоогоор **+{gain:.1f}** оноо нэмэгдэнэ.")
    return out


def assists(at: pd.DataFrame, team: str) -> list[str]:
    if at.empty:
        return []
    vc = at.passer.value_counts()
    share = vc.iloc[0] / len(at)
    out = [f"**{team}** багийн оноо болсон дамжуулалтын **{share:.0%}**-ийг {vc.index[0]} тоглогч хийсэн."]
    out.append("Довтолгоо нэг тоглогчоос их хамааралтай: өрсөлдөгч түүнийг хавчвал багийн хамтын тоглолт тасарна, "
               "тиймээс хоёр дахь тоглолт зохион байгуулагч бэлтгэх хэрэгтэй." if share >= 0.3 else
               "Дамжуулалт олон тоглогчид тархсан тул нэг тоглогчийг хааж довтолгоог зогсооход хэцүү.")
    return out


def game_flow(flow: pd.DataFrame, home: str, away: str) -> list[str]:
    f = flow.sort_values("elapsed")
    if f.empty:
        return []
    final = f.margin.iloc[-1]
    winner, loser_sign = (home, -1) if final > 0 else (away, 1)
    trail = max(int((loser_sign * f.margin).max()), 0)
    sign = np.sign(f.margin.to_numpy())
    nz = np.flatnonzero(sign != 0)
    last_change = 0.0
    for i, j in zip(nz[:-1], nz[1:]):
        if sign[i] != sign[j]:
            last_change = f.elapsed.iloc[j]
    minute = int(last_change // 60) + 1
    out = [f"Ялагч **{winner}** баг тоглолтын явцад хамгийн ихдээ {trail} оноогоор хоцорч байсан"
           + ("; эхнээс нь дуустал бараг тэргүүлсэн." if trail <= 2 else ".")]
    if last_change:
        out.append(f"Тэргүүлэгч сүүлчийн удаа {minute}-р минутад солигдсон"
                   + (" — тоглолт төгсгөлийн минутуудад шийдэгдсэн тул төгсгөлийн довтолгооны схем, торгуулийн оновч "
                      "шийдвэрлэх үүрэгтэй байжээ." if minute >= 36 else "; түүнээс хойш ялагч баг тэргүүллээ алдаагүй."))
    return out


def inplay_accuracy(minute: pd.DataFrame) -> list[str]:
    m = minute.set_index("minute")
    hit = m.index[m.acc_model >= 0.8]
    acc = m.loc[20, "acc_leader"]
    out = [f"Хагас дуусахад (20-р минут) тэргүүлж буй баг **{acc:.0%}** тохиолдолд ялдаг, үлдсэн {1 - acc:.0%}-д нь "
           "хоцорч байсан баг эргэж ялдаг. Хагаст хоцорсон ч тоглолт дуусаагүй."]
    if len(hit):
        out.append(f"Загварын таамаглал {int(hit[0])}-р минутаас 80%-иас дээш зөв болдог — тэр мөчөөс хоцорсон баг "
                   "эрсдэл өндөр тоглолтын хэв маяг руу шилжих шаардлагатай.")
    return out


# ---------------------------------------------------------------- Олдворууд
def lead_safety(lead: pd.DataFrame) -> list[str]:
    safe = []
    for cp, when in (("Хагас", "хагаст"), ("3-р үеийн төгсгөл", "3-р үеийн төгсгөлд")):
        d = lead[(lead.checkpoint == cp) & (lead.est >= 0.9)]
        if len(d):
            safe.append(f"{when} **{d.bin.iloc[0]}** оноогоор тэргүүлбэл {d.est.iloc[0]:.0%}")
    out = ["Ялалтын 90%-ийн баталгаа: " + ", ".join(safe) + " ялдаг."] if safe else []
    mid = lead[(lead.checkpoint == "Хагас") & (lead.bin == "7–10")]
    if len(mid) and mid.est.iloc[0] < 1:
        out.append(f"Хагаст 7–10 оноогоор тэргүүлсэн баг ч {1 - mid.est.iloc[0]:.0%} тохиолдолд ялагддаг тул завсарлагааны "
                   "дараа хурдаа сулруулж болохгүй.")
    return out


def comebacks(cb: pd.DataFrame) -> list[str]:
    if cb.empty:
        return []
    return [f"Ялалтын **{(cb.deficit >= 10).mean():.0%}** нь 10 ба түүнээс олон оноогоор хоцорсноос эргэж гарсан; хамгийн том "
            f"эргэлт {int(cb.deficit.max())} оноо.",
            "10 оноогоор хоцорсон ч тоглолт дуусаагүй: тоглогчдод эргэж ирэх боломжийг тоогоор харуулж, сэтгэл зүйн хувьд "
            "бэлтгэх нь ашигтай."]


def distance(dist: pd.DataFrame) -> list[str]:
    d = dist.assign(w=dist.n)
    mid = d[(d.lo_m >= 2) & (d.hi_m <= 6)]
    mid_pps = (mid.pps * mid.n).sum() / mid.n.sum()
    three = d[d.three_share > 0.5]
    best3 = three.loc[three.pps.idxmax()]
    deep = three.loc[three.lo_m.idxmax()]
    return [f"3 онооны шугамын ойр ({best3.lo_m:.2f}–{best3.hi_m:.2f} м) шидэлт бүрт **{best3.pps:.2f}** оноо, 2–6 м-ийн "
            f"шидэлт {mid_pps:.2f}: 100 шидэлт тутамд {100 * (best3.pps - mid_pps):.0f} онооны зөрүү.",
            f"Харин шугамаас хэт хол ({deep.lo_m:.1f} м+) шидэх нь {deep.pps:.2f} оноо — сул. Тоглогчдыг шугамын яг ард "
            "байрлуулах дасгал хамгийн их ашиг өгнө."]


def assisted(a: pd.DataFrame) -> list[str]:
    w = a.groupby("zone").apply(lambda g: (g.est * g.n).sum() / g.n.sum(), include_groups=False)
    out = [f"«{w.idxmax()}» бүсийн оносон шидэлтийн **{w.max():.0%}** нь дамжуулалтаас гардаг бол «{w.idxmin()}» бүсийнх "
           f"{w.min():.0%}."]
    p = a.pivot(index="zone", columns="is_import", values="est")
    if {True, False} <= set(p.columns):
        gap = (p[False] - p[True]).sort_values(ascending=False)
        out.append(f"«{gap.index[0]}» бүсэд гадаад тоглогч {p.loc[gap.index[0], True]:.0%}, дотоодынх "
                   f"{p.loc[gap.index[0], False]:.0%} дамжуулалтаас онодог: гадаад тоглогч шидэлтээ өөрөө бүтээдэг бол дотоод "
                   "шидэгчид бөмбөг эргүүлэх схем хэрэгтэй.")
    return out


def off_def(r: pd.DataFrame) -> list[str]:
    if len(r) < 3:
        return []
    o, dd = r.loc[r.ortg.idxmax()], r.loc[r.drtg.idxmin()]
    both = r[(r.ortg > r.ortg.mean()) & (r.drtg < r.drtg.mean())]
    return [f"Довтолгоогоор **{o.team}** баг (100 довтолгоонд {o.ortg:.0f} оноо), хамгаалалтаар **{dd.team}** баг "
            f"(100 довтолгоонд {dd.drtg:.0f} оноо алддаг) тэргүүлнэ.",
            f"Хоёуланд нь дунджаас сайн {len(both)} баг ({_names(both.team, 4)}) — аварга болох гол өрсөлдөгчид."
            if len(both) else "Довтолгоо, хамгаалалт хоёуланд нь дунджаас сайн баг алга."]


def usage(u: pd.DataFrame) -> list[str]:
    if len(u) < 5:
        return []
    q = u[(u.usage > u.usage.median()) & (u.ts > u.ts.median())].sort_values("usage", ascending=False)
    return [f"Олон довтолгоо дуусгадаг мөртлөө оновчтой (баруун дээд булан) **{len(q)}** тоглогч"
            + (f": {_names(q.name)}. Баг нь довтолгоогоо эдгээр тоглогчийн эргэн тойронд зохион байгуулах нь зүйтэй."
               if len(q) else " алга.")]


def stability(stab: pd.DataFrame) -> list[str]:
    s = stab.sort_values("r", ascending=False)
    lo = s.iloc[-1]
    return [f"Хамгийн тогтвортой нь «{s.label.iloc[0]}» (r = {s.r.iloc[0]:.2f}), хамгийн тогтворгүй нь «{lo.label}» "
            f"(r = {lo.r:.2f}).",
            "Тоглогч сонгохдоо дээд мөрүүдийн үзүүлэлтэд найдаж, нэг улирлын шидэлтийн оновчийг хэт үнэлэхгүй байх."]


def stability_pairs(pairs: pd.DataFrame, label: str) -> list[str]:
    d = pairs.dropna(subset=["prev", "now"])
    if len(d) < 3:
        return []
    ch = d.assign(delta=d.now - d.prev).sort_values("delta")
    up, down = ch.iloc[-1], ch.iloc[0]
    return [f"«{label}» үзүүлэлтээр хамгийн их ахисан нь **{up.player_name}** тоглогч ({up.prev:.2f} → {up.now:.2f}), "
            f"хамгийн их унасан нь {down.player_name} тоглогч ({down.prev:.2f} → {down.now:.2f}). Ийм огцом өөрчлөлтийн "
            "шалтгааныг (үүрэг, гэмтэл, баг сольсон) тоглогчтой ярилцаж тодруулах хэрэгтэй."]


def imports_on_court(imports: pd.DataFrame) -> list[str]:
    m = imports.drop_duplicates(["season", "period"])
    out = []
    for season, g in m.groupby("season"):
        top = g.loc[g.mean_k.idxmax()]
        out.append(f"{season.replace('-20', '–')}: гадаад тоглогч {int(top.period)}-р үед хамгийн олон "
                   f"(дунджаар {top.mean_k:.1f}) талбайд байсан.")
    return [" ".join(out), "Өрсөлдөгчийн гадаад тоглогчид хамгийн олон талбай дээр байх үед хамгаалалтын хамгийн сайн "
            "бүрэлдэхүүнээ гаргах нь зүйтэй."] if out else []


# ---------------------------------------------------------------- Машин сургалт
def clusters(cl: pd.DataFrame, me: pd.Series, near: pd.DataFrame) -> list[str]:
    if near.empty:
        return []
    share = (cl.drop_duplicates("player_id").cluster_name == me.cluster_name).mean()
    return [f"**{me.player_name}** тоглогч «{me.cluster_name}» хэв маягтай (тоглогчдын {share:.0%} энэ бүлэгт).",
            f"Гэмтэл, шилжилтийн үед хэв маягаараа хамгийн ойр орлуулагч: **{near.player_name.iloc[0]}** тоглогч."]


def win_calc(t1: str, t2: str, p: float) -> list[str]:
    k = int(round(20 * p))
    return [f"20 удаа тоглосон гэж үзвэл **{t1}** баг ойролцоогоор **{k}** удаа, {t2} баг {20 - k} удаа ялна.",
            "Хүч ойролцоо — тоглолтыг тухайн өдрийн бүрэлдэхүүн, гэрийн талбай, шидэлтийн оновч шийднэ." if 0.4 <= p <= 0.6
            else f"Сул баг ялахын тулд онцгой сайн өдөр хэрэгтэй: 20-оос ердөө {min(k, 20 - k)} удаа."]


def quality(missing: pd.DataFrame, names: dict) -> list[str]:
    w = missing.loc[missing.pct_missing.idxmax()]
    return [f"«{names.get(w.column, w.column)}» {w.pct_missing:.0f}% дутуу тул энэ үзүүлэлтээр тоглогч сонгохдоо MBA-ийн "
            "профайл эсвэл багийн бүртгэлээс нэмж шалгах хэрэгтэй."]
