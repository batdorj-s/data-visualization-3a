# Өгөгдлийн эх сурвалжийн судалгаа — MBA лиг

- **Судалсан огноо:** 2026-11-12
- **Зорилго:** Бие даалтад ашиглах өгөгдлийн хэмжээ, хувьсагч, авах арга, хязгаарлалтыг баталгаажуулах
- Энэ баримтын бүх тоо тухайн өдрийн байдлаар байна. Сайт цаг тутам шинэчлэгддэг.

---

## 1. MBA статистикийн систем — `mongolia.basketball` (үндсэн эх сурвалж)

**Техникийн онцлог**
- Next.js дээр server-side render хийгддэг тул HTML дотор дата шууд байна. `requests` + `BeautifulSoup` хангалттай, JavaScript ажиллуулах шаардлагагүй.
- `robots.txt`: `Allow: /`, `Disallow: /admin`, `Disallow: /api`. Хуудсуудыг татахыг зөвшөөрдөг.
- Хуудасны дунд хэмжээ ~0.5 MB. Хүсэлтүүдийн хооронд ≥1 секунд хүлээнэ.

**Улирлууд.** Систем зөвхөн 2 улиралтай. 2025-26-аас өмнөх дата байхгүй.

| Улирал | Season ID |
|---|---|
| 2026-2027 (явж байгаа) | `ac48cf7e-0249-4450-a2ee-42fc7b97dc16` |
| 2025-2026 (дууссан) | `c1a0488c-31a5-429d-8254-3b27aa45e702` |

**URL-ийн загвар**

| Хуудас | URL |
|---|---|
| Тоглогчийн улирлын статистик | `/en/stats?competition=league&view=players&season=<id>` (season-гүй үед одоогийн улирал) |
| Багийн статистик | `/en/stats?competition=league&view=teams&season=<id>` |
| Тоглогчийн профайл | `/en/players/<slug>` (slug-ийг статистикийн хүснэгтийн линкээс авна) |
| Сарын хуваарь | `/en/competitions/league/schedule?season=<id>&month=YYYY-MM` |
| Тоглолтын box score | `/en/games/<game_id>` |
| Байрын хүснэгт | `/en/competitions/league/standings` |
| Бусад лиг (хамрахгүй) | `competition=league-w`, `m-league`, `m-league-w`, `mba-cup`, `mba-cup-w` |

**Хувьсагчид**

| Хуудас | Баганууд |
|---|---|
| Тоглогчийн статистик | PLAYER, TEAM, GP, MIN, PPG, RPG, APG, SPG, BPG, PF, FG%, 3P%, EFF |
| Тоглогчийн профайл | Байрлал (жишээ: "Point guard (PG)"), өндөр (см), төрсөн он, "Import player" шошго (дотоодын тоглогчид шошгогүй), FT%, сүүлийн 5 тоглолт |
| Box score | Огноо, цаг, газар, Home/Away, quarter бүрийн оноо. Тоглогчийн мөр: POS, MIN, PTS, REB, AST, STL, BLK, FG (`м-о`), 3P, FT, TO, PF, DNP. Багийн нийлбэр (Totals). Team comparison хэсэгт OREB, DREB, AST, STL, TO, PF байна |

Box score-ийн хоёр багийн хүснэгт хоёулаа HTML-д байна (тоглолт 141 дээр шалгасан: `Totals` 2 удаа, `<table>` 3). Play-by-play, shot chart хэсэг ч байгаа ч төсөлд хамрахгүй.

**Хэмжээ (тоолж шалгасан)**

| Улирал | Тоглогч (статистикийн хүснэгт) | Тоглолт (хуваарийн линк) | Сар бүрээр |
|---|---|---|---|
| 2025-26 | 171 (GP ≥ 5: 147) | 172 | 10: 29, 11: 26, 12: 23, 1: 35, 2: 24, 3: 30, 4: 5 |
| 2026-27 | 147 | 80 (баг бүр 16 тоглолт тоглосон) | 10: 56, 11: 24 |

Таамаглалаар ~4,600 тоглогч-тоглолтын мөр, ~500 баг-тоглолтын мөр гарна.

Game ID нь бүх лигт нийтлэг бөгөөд он цагийн дарааллаар явдаггүй (жишээ: 119 = 2026.10.07, 141 = 2026.01.04). Тиймээс ID-г хуваарийн хуудаснаас цуглуулна.

**Цэвэрлэгээнд анхаарах, бодитоор ажигласан асуудлууд**

| Төрөл | Жишээ |
|---|---|
| Багийн нэрний том/жижиг үсэг | `SELENGE BODONS` ↔ `Selenge Bodons`, `OMNI ERDENET MINERS` ↔ `Omni Erdenet Miners` |
| Багийн нэр солигдсон | `XAC BRONCOS` (slug `khasyn-khuleguud`) = Khasin Khuleguud; `ZAVKHAN BROTHERS` (2025-26) ба `Sono Brothers` (2026-27) хоёр нэг баг эсэхийг шалгах; `BUREN SCORE MONGOLIANS`; `BISHRELT METAL` |
| Тоглогчийн нэр | `SCRUBB Jay` (2025-26) ↔ `SCRUBB Jayden Amari` (2026-27); `SANDAGDORJ Binderyaa` ↔ FIBA `Binderiya Sandagdorj` |
| Нэг багийн олон slug | `selenge-bodons-2`, `selenge-bodons-3`, `darkhan-united`, `darkhan-united-2`, `darkhan-united-3` |
| Хоосон/0 утга | 3P% = 0.0 нь шидээгүй гэсэн утгатай байж болно. DNP мөрүүд |
| Цөөн тоглолт | 2025-26 улиралд GP = 1–4 тоглогч 24 |

**2026-27 улирлын 10 баг:** SG Apes, Omni Erdenet Miners, Darkhan United, South Gobi Broncos, Sono Brothers, Selenge Bodons, Khan Falcons, BCH Knights, Western Warriors, SUA TLG Tushig Bagana.

**2025-26 улирлын 10 баг** (статистикийн хүснэгтэд байгаагаар): Buren Score Mongolians, BCH Knights, Selenge Bodons, Zavkhan Brothers, Khan Falcons, SG Apes, XAC Broncos, Omni Erdenet Miners, Darkhan United, Bishrelt Metal.

---

## 2. Wikipedia (2-р эх сурвалж)

Авах арга: `https://en.wikipedia.org/w/index.php?title=<Title>&action=raw` (wikitext). Лиценз нь CC BY-SA тул эх сурвалжийг заана.

| Нийтлэл | Агуулга | Тэмдэглэл |
|---|---|---|
| *The League (Mongolia)* | 1994–2026 оны аварга ба дэд аварга, одоогийн багууд ба гэр хот, лигийн нэрний түүх | 2023 онд 13 баг болж өргөжсөн, 2024 онд 10 баг руу буцсан |
| *2023–24 The League season* | 13 багийн W/L/PF/PA (`{{Sports table}}`) | Бүрэн |
| *2024–25*, *2025–26 The League season* | Байрын хүснэгтгүй | Ашиглах боломжгүй |

**2023-24 улирлын байр** (Wikipedia):

| Баг | W | L | PF | PA |
|---|---|---|---|---|
| Erdenet Miners | 19 | 4 | 1878 | 1693 |
| Bishrelt Metal | 18 | 5 | 1973 | 1767 |
| IHC Apes | 19 | 5 | 2251 | 2012 |
| BCH Garid | 17 | 6 | 2050 | 1815 |
| Khasin Khuleguud | 14 | 8 | 1739 | 1673 |
| Nalaikh Bison | 11 | 13 | 2099 | 2108 |
| Selenge Bodons | 11 | 13 | 2056 | 2120 |
| Zavkhan Brothers | 10 | 14 | 2039 | 2076 |
| Darkhan United | 8 | 16 | 1927 | 2054 |
| Ulaanbaatar TLG | 7 | 17 | 2060 | 2168 |
| Mongolians | 7 | 17 | 1940 | 2115 |
| Umnugovi Yoluud | 6 | 17 | 1969 | 2216 |
| Shutis Sharks | 5 | 17 | 1862 | 2026 |

Тоглолтын тоо багуудын хооронд жигд биш (22–24) байгааг анхаарна уу.

**Гэр хот** (Wikipedia-гийн "Current teams" хүснэгт): SG Apes, Khasin Khuleguud, BCH Knights, BurenScore Mongolians, Bishrelt Metal — Улаанбаатар; Selenge Bodons — Сүхбаатар; Erdenet Miners — Эрдэнэт; Khovd Falcons — Ховд; Darkhan United — Дархан; Zavkhan Brothers — Улиастай.

2026-27 улирлын шинэ нэртэй багуудын гэр хотыг (South Gobi Broncos, Sono Brothers, Western Warriors, SUA TLG Tushig Bagana, Khan Falcons) MBA-ийн багийн хуудас эсвэл мэдээнээс баталгаажуулах шаардлагатай.

---

## 3. Шигшээ баг (3-р эх сурвалж)

Нийтлэл: Wikipedia, *Mongolia men's national basketball team*. `{{FIBA player}}` загвартай бөгөөд тэмцээний огноо 2026-08-31.

| # | Тоглогч | Байрлал | Төрсөн | Клуб |
|---|---|---|---|---|
| 2 | Gantsolmon Bolor-Erdene | C/F | 2003-11-17 | Erdenet Miners |
| 3 | Amarbayasgalan Enkhbayasgalan | F | 1997-08-14 | Erdenet Miners |
| 4 | Tumenbayar Uuganbayar | G | 1998-02-17 | Bishrelt Metal |
| 5 | Enkhbaatar Saruul-Erdene | G | 1999-01-18 | SG Apes |
| 6 | Delgerchuluun Bayasgalan | G | 1997-10-30 | TSG GhostHawks (Тайвань) |
| 7 | Altangerel Azbayar | C | 2005-03-28 | Fukushima Firebonds (Япон) |
| 8 | Ochirbat Erdenetsogt (ахлагч) | G | 1995-01-14 | BCH Knights |
| 9 | Khishigbaatar Orgil | C | 2003-05-17 | Fukui Blowinds (Япон) |
| 10 | Baatar-Erdene Barsbold | G | 2004-10-19 | Khasin Khuleguud |
| 22 | Erdenetsetseg Sugar-Ochir | G | 1999-07-02 | BCH Knights |
| 25 | Sandagdorj Binderiya | G | 2004-03-08 | Khasin Khuleguud |
| 55 | Sharavjamts Enkhiin-Od | G | 2002-08-27 | South Carolina Gamecocks (АНУ) |

8 тоглогч MBA-ийн клубт тоглодог. MBA-ийн датад нэр нь "ОВОГ Нэр" хэлбэрээр бичигддэг (жишээ: `GANTSOLMON Bolor-Erdene`).

---

## 4. Ашиглахгүй / хязгаарлагдмал эх сурвалж

| Эх сурвалж | Шалтгаан |
|---|---|
| asia-basket.com | `robots.txt` нь ClaudeBot, anthropic-ai, GPTBot зэрэг AI агентуудыг хориглосон (`Content-Signal: ai-train=no, use=reference`). Тоглогчийн бүтэн статистик захиалгын ард байдаг. Үнэгүй хэсэгт зөвхөн шагнал, top-10 тэргүүлэгчид, playoff-ийн хүснэгт байна. 2024-25 улирлын байрыг хэрэглэгч өөрөө хөтчөөр нээж гараар оруулах боломжтой |
| scoutbasketball.com | Бүртгэл шаарддаг |
| 2023-24, 2024-25 улирлын тоглогчийн статистик | Үнэгүй, зөвшөөрөгдсөн эх сурвалжид байхгүй |

**asia-basket-ийн үнэгүй хэсгээс авсан лавлах мэдээлэл (2024-25):** аварга ба улирлын тэргүүлэгч нь Khuleguud Knights, Finals MVP нь Ian Miller, League MVP нь McKenzie Moore, оноогоор тэргүүлэгч нь Justin Moss (30.9 PPG).

---

## 5. ML-д дата хүрэлцэх эсэх

| Загвар | Мөр | Дүгнэлт |
|---|---|---|
| K-Means (тоглогч) | ~265 тоглогч-улирал (GP ≥ 5) | Хангалттай. Хэмжээ биш харьцаа хувьсагч ашиглана |
| Ялалтын тайлбар (Four Factors) | ~250 тоглолт | Хангалттай |
| Ялалтын таамаглал (тоглолтын өмнөх дата) | Эхний тоглолтуудыг хасвал ~210 | Хүрэлцэнэ. 70 тоглолтын тест дээр accuracy-ийн 95% CI ±11 нэгж хувь, walk-forward CV хийвэл ±6 нэгж хувь орчим |

Ихэнх тоглолт М Банк Аренад болдог тул home/away ангиллын утга сул. Тоглолтыг нэг мөр болгож, хоёр багийн зөрүүгээр загварчилна.

---

## 6. Хичээлийн зарчмууд → төсөлд хэрэглэх

Лекцийн агуулгыг өөрийн үгээр хураангуйлсан.

| Лекц | Сэдэв | Төсөлд хэрэглэх нь |
|---|---|---|
| L3–L4 | Мэдрэхүйн зарчим, preattentive шинж (өнгө, хэмжээ, байрлал), өнгөний кодчилол | Онцлох өгөгдөлд тод өнгө, бусдад саармаг. Ангиллын өгөгдөлд категориал палитр, дараалсан өгөгдөлд нэг өнгөний градиент, корреляцид diverging палитр |
| L5 | Нэг ба олон хувьсагчийн дүрслэл | Гистограм, box, violin, scatter, heatmap, pair plot |
| L6 | Цаг хугацааны дүрслэл | Улирлын туршх ялалтын хувь, Elo-ийн явц |
| L7 | Гео-орон зай | Багийн гэр хотыг Монголын газрын зураг дээр |
| L8–L9 | Граф өгөгдөл | Улирал хооронд багуудын хооронд шилжсэн тоглогчдын сүлжээ |
| L10–L11 | Интерактив байдал: 7 зорилго (Yi et al., 2007), Norman-ий үйлдлийн загвар, харилцааны зардал | Dashboard-ийн функц бүрийг 7 зорилготой холбоно. Хариу < 100 мс бол "шууд" мэдрэгддэг тул шүүлтүүрийн шинэчлэлтэд < 300 мс зорилт тавина. Олон давхар цэс хэрэглэхгүй |
| Сурах бичиг: Schwabish, *Better Data Visualizations*, 6-р бүлэг | Pareto chart, статистикийн тодорхой бус байдал (error bar, CI, gradient, fan chart), "датаг өөрийг нь харуулах" (beeswarm, raincloud) | Pareto нь хоёр тэнхлэг зөвшөөрөгддөг цорын ганц тохиолдол. Тодорхой бус байдал 2 төрөлтэй: санамсаргүй байдлаас үүдэлтэй ба өгөгдлийн чанараас үүдэлтэй. Error bar-ын оронд dot + interval (Correll & Gleicher, 2014). Магадлалыг quantile dot plot-оор харуулна (Kay et al., 2016) |

---

## Эх сурвалж

- MBA Statistics Centre — https://mongolia.basketball/en/stats
- The League (Mongolia) — https://en.wikipedia.org/wiki/The_League_(Mongolia)
- 2023–24 The League season — https://en.wikipedia.org/wiki/2023%E2%80%9324_The_League_season
- Mongolia men's national basketball team — https://en.wikipedia.org/wiki/Mongolia_men%27s_national_basketball_team
- Mongolian Basketball League 2024-2025 (asia-basket) — https://www.asia-basket.com/Mongolia/basketball-league-mbl_2024-2025.aspx
