from pathlib import Path
import textwrap

import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages
from matplotlib.lines import Line2D
import numpy as np
import pandas as pd
import seaborn as sns


BASE = Path(__file__).resolve().parent
OUT = BASE / "report_outputs"
OUT.mkdir(exist_ok=True)
sns.set_theme(style="whitegrid", context="notebook")


def add_text_page(pdf: PdfPages, title: str, paragraphs: list[str]) -> None:
    fig = plt.figure(figsize=(8.27, 11.69))
    fig.patch.set_facecolor("white")
    fig.text(0.08, 0.94, title, fontsize=20, weight="bold", color="#17365D")
    y = 0.88
    for paragraph in paragraphs:
        for line in textwrap.wrap(paragraph, width=92):
            fig.text(0.08, y, line, fontsize=11, va="top", color="#222222")
            y -= 0.027
        y -= 0.018
    pdf.savefig(fig, bbox_inches="tight")
    plt.close(fig)


def season(month: int) -> str:
    if month in (12, 1, 2):
        return "Өвөл"
    if month in (3, 4, 5):
        return "Хавар"
    if month in (6, 7, 8):
        return "Зун"
    return "Намар"


def prepare_weather() -> pd.DataFrame:
    weather = pd.read_csv(BASE / "weatherHistory.csv")
    weather["Formatted Date"] = pd.to_datetime(weather["Formatted Date"], utc=True)
    weather["date"] = weather["Formatted Date"].dt.date
    weather["season"] = weather["Formatted Date"].dt.month.map(season)
    daily = (
        weather.groupby(["date", "season"], as_index=False)
        .agg(
            temperature_c=("Temperature (C)", "mean"),
            humidity=("Humidity", "mean"),
            precipitation_mm=("Precip Type", lambda x: (x == "rain").sum()),
            summary=("Summary", lambda x: x.mode().iat[0]),
        )
    )
    daily["date"] = pd.to_datetime(daily["date"])
    return daily


def plot_weather(daily: pd.DataFrame, pdf: PdfPages) -> None:
    colors = {"Өвөл": "#4B9CD3", "Хавар": "#6ABF69", "Зун": "#E87722", "Намар": "#9467BD"}
    fig, axes = plt.subplots(1, 3, figsize=(16, 4.8))

    for name, group in daily.groupby("season"):
        axes[0].scatter(
            group["temperature_c"], group["humidity"], s=18, alpha=0.55,
            color=colors[name], label=name, edgecolors="none",
        )
    axes[0].set(title="Температур ба чийгшил", xlabel="Температур (°C)", ylabel="Чийгшил (0–1)")
    axes[0].legend(title="Улирал", frameon=True)

    axes[1].plot(daily["date"], daily["temperature_c"], color="#C0392B", linewidth=1)
    axes[1].set(title="Өдрийн дундаж температурын хугацааны цуваа",
                xlabel="Огноо", ylabel="Температур (°C)")
    axes[1].tick_params(axis="x", rotation=35)

    axes[2].hist(daily["precipitation_mm"], bins=[-0.5, 0.5, 1.5, 2.5, 3.5, 4.5],
                 color="#2E86AB", edgecolor="white", rwidth=0.9)
    axes[2].set(title="Хур тунадасны өдрийн тархалт",
                xlabel="Бороо орсон цагийн тоо (өдөрт)", ylabel="Өдрийн тоо")

    fig.suptitle("Даалгавар 2 — Weather History (өдрийн агрегат)", fontsize=16, weight="bold")
    fig.tight_layout()
    fig.savefig(OUT / "weather_three_plots.png", dpi=180, bbox_inches="tight")
    pdf.savefig(fig, bbox_inches="tight")
    plt.close(fig)


def prepare_retail() -> pd.DataFrame:
    retail = pd.read_csv(BASE / "retail_sales_dataset.csv", parse_dates=["Date"])
    retail["Quarter"] = retail["Date"].dt.quarter.map(lambda q: f"Q{q}")
    return retail


def plot_retail(retail: pd.DataFrame, pdf: PdfPages) -> None:
    branches = pd.DataFrame(
        {
            "Салбар": list("АБВГД"),
            "Q1": [95, 45, 12, 78, 66],
            "Q2": [98, 67, 34, 82, 72],
            "Q3": [97, 89, 56, 88, 81],
            "Q4": [99, 23, 78, 91, 93],
        }
    )
    long = branches.melt("Салбар", var_name="Улирал", value_name="Борлуулалт")
    fig, axes = plt.subplots(1, 2, figsize=(14, 5))
    axes[0].bar(long["Салбар"] + "-" + long["Улирал"], long["Борлуулалт"], color="#67A86B")
    axes[0].set(title="Муу хувилбар: масштаб ба нэг өнгө буруу",
                xlabel="Салбар-улирал", ylabel="Борлуулалт")
    axes[0].set_ylim(90, 100)
    axes[0].tick_params(axis="x", rotation=70)

    for branch, group in long.groupby("Салбар"):
        axes[1].plot(group["Улирал"], group["Борлуулалт"], marker="o", linewidth=2, label=f"Салбар {branch}")
    axes[1].set(title="Сайн хувилбар: улирлын өөрчлөлтийг шударга харуулсан",
                xlabel="Улирал", ylabel="Борлуулалтын индекс (0-100)")
    axes[1].set_ylim(0, 105)
    axes[1].legend(ncol=2, fontsize=9)
    fig.suptitle("Даалгавар 3 — Дүрслэлийн шалгуурын хэрэглээ", fontsize=16, weight="bold")
    fig.tight_layout()
    fig.savefig(OUT / "retail_bad_good.png", dpi=180, bbox_inches="tight")
    pdf.savefig(fig, bbox_inches="tight")
    plt.close(fig)

    category = retail.groupby("Product Category", as_index=False)["Total Amount"].sum()
    fig, ax = plt.subplots(figsize=(8, 4.8))
    sns.barplot(data=category, x="Product Category", y="Total Amount", hue="Product Category",
                palette="Set2", legend=False, ax=ax)
    ax.set(title="Retail Sales Dataset: ангиллаар нийт борлуулалт",
           xlabel="Бүтээгдэхүүний ангилал", ylabel="Нийт дүн")
    fig.tight_layout()
    fig.savefig(OUT / "retail_category_sales.png", dpi=180, bbox_inches="tight")
    pdf.savefig(fig, bbox_inches="tight")
    plt.close(fig)


def plot_adult(adult: pd.DataFrame, pdf: PdfPages) -> None:
    adult = adult.copy()
    adult["income_label"] = adult["income"].str.replace(".", "", regex=False).str.strip()
    adult["age_group"] = pd.cut(adult["age"], [0, 25, 35, 45, 55, 65, 100],
                                labels=["≤25", "26–35", "36–45", "46–55", "56–65", "66+"])
    income_rate = adult.groupby("age_group", observed=False)["income_label"].apply(
        lambda x: (x == ">50K").mean() * 100
    )
    education_rate = adult.groupby("education", observed=False)["income_label"].apply(
        lambda x: (x == ">50K").mean() * 100
    ).sort_values(ascending=False).head(10)
    fig, axes = plt.subplots(1, 2, figsize=(14, 5))
    income_rate.plot(kind="bar", color="#3B82A0", ax=axes[0])
    axes[0].set(title="Насны бүлгээр >50K орлогын хувь", xlabel="Насны бүлэг", ylabel="Хувь (%)")
    axes[0].tick_params(axis="x", rotation=0)
    education_rate.sort_values().plot(kind="barh", color="#D97A2B", ax=axes[1])
    axes[1].set(title="Боловсролын түвшнээр >50K орлого",
                xlabel="Хувь (%)", ylabel="Боловсрол")
    fig.suptitle("Даалгавар 4 — Adult dataset-ийн хайгуулын жишээ", fontsize=16, weight="bold")
    fig.tight_layout()
    fig.savefig(OUT / "adult_exploration.png", dpi=180, bbox_inches="tight")
    pdf.savefig(fig, bbox_inches="tight")
    plt.close(fig)


def build_report() -> None:
    daily = prepare_weather()
    retail = prepare_retail()
    adult = pd.read_csv(BASE / "adult.csv")
    report_path = BASE / "data_visualization_report.pdf"
    with PdfPages(report_path) as pdf:
        add_text_page(
            pdf,
            "ӨГӨГДЛИЙН ДҮРСЛЭЛ — Даалгавар 2–4",
            [
                "Хичээл: Өгөгдлийн дүрслэл | Нэр: __________________ | Код: __________________",
                "Ашигласан өгөгдөл: weatherHistory.csv, retail_sales_dataset.csv, adult.csv.",
                "Зорилго: өгөгдөл бэлтгэх, зөв график сонгох, аномали/хэв маяг тайлбарлах, хайгуул–баталгаажуулалт–мэдлэг бий болгох 3 гогцоог хэрэглэх.",
            ],
        )
        add_text_page(
            pdf,
            "1. Өгөгдөл бэлтгэл ба Chi (2000) төлөвүүд",
            [
                f"Weather History: {len(daily):,} өдөрт агрегатлав. Температур, чийгшил, бороо орсон цагийн тоо, Summary-ийн мод утгыг ашиглав.",
                "Өгөгдлийн үнэ цэнэ: түүхий CSV. Шинжилгээний ангилал: огноо ба улирлаар бүлэглэсэн өдөр тутмын хүснэгт. Дүрслэлийн ангилал: байрлал, хугацаа, тархалтыг харуулах график. Зурган өгөгдөл: эцсийн PNG/PDF график.",
                "Анхаарах нь: эх өгөгдөлд үүлэрхэг байдлын 0–8 тоон багана байхгүй тул Summary (Clear, Partly Cloudy гэх мэт)-ийг төлөөлөл болгон хадгалсан. Энэ нь хэмжилтийн яг орлуулалт биш.",
            ],
        )
        plot_weather(daily, pdf)
        add_text_page(
            pdf,
            "2. Weather — олдвор, аномали, дараагийн шинжилгээ",
            [
                "Олдвор: зун температур өндөр, чийгшил харьцангуй бага; өвөл температур бага, чийгшил өндөр байх улирлын ялгаа ажиглагдана.",
                "Аномали: температур огцом өөрчлөгдсөн өдөр, мөн бороо орсон цагийн тоо ердийн түвшнээс их өдөр нь шалгах цэг болно. Аномали гэж шууд шүүхгүй; эхлээд цагийн түүхий мөрүүдээр буцааж нягтална.",
                "Магадгүй шалтгаан: фронтын нөлөө, шуурга, хэмжилтийн төхөөрөмж/өгөгдөл тасарсан үе. Нэмэлт арга: улирал тус бүрийн IQR/z-score, rolling mean, корреляци, Summary ангиллын хүснэгт, missing/duplicate шалгалт.",
                "Өнгөний тайлбар: цэнхэр=өвөл, ногоон=хавар, улбар=зун, нил ягаан=намар. Өнгө нь улирлыг шууд ялгуулах pre-attentive кодлолт.",
            ],
        )
        plot_retail(retail, pdf)
        add_text_page(
            pdf,
            "3. Retail — муу дүрслэлийг үнэлж сайжруулсан нь",
            [
                "Шударга: y тэнхлэгийг 90–100-аар тасалсан нь бага утгуудын ялгааг нууж, хэмжээний ойлголтыг гажуудуулна. Сайжруулалт: 0–105 масштаб.",
                "Ойлгомжтой: “График” гэсэн ерөнхий гарчиг, бүгд ногоон өнгө нь ямар үзүүлэлт, аль улирал болохыг хэлэхгүй. Сайжруулалт: тодорхой гарчиг, улирал/салбарыг ялгасан тэмдэглэгээ.",
                "Хялбар: шошго давчуу, нэг графикт олон багана байна. Сайжруулалт: улирлыг x тэнхлэгт байрлуулж, салбар бүрийг нэг шугамаар харуулсан.",
                "Үнэ цэнэтэй: сайжруулсан график нь аль салбар өсөж/буурч байгааг шууд харуулна. Retail dataset өөрөө салбарын баганагүй тул бодит dataset-ийн Product Category борлуулалтыг тусад нь үзүүлэв.",
            ],
        )
        add_text_page(
            pdf,
            "4. Adult — мэдлэг бий болгох 3 гогцоо",
            [
                "Хайгуулын гогцоо: насны бүлэг, хүйс, боловсрол, орлогын тархалтыг bar chart, histogram, boxplot, stacked bar, heatmap-аар харна. Анхны олдвор: нас/боловсролын бүлгүүдэд >50K орлогын хувь ялгаатай мэт харагдана.",
                "Баталгаажуулалтын гогцоо: олдворыг нас, боловсрол, ажилласан цаг, occupation-оор давхар задлан тайлбарлана. Таамаглал: боловсролын түвшин ба долоо хоногийн ажлын цаг өндөр байх нь >50K ангилалтай холбоотой. Chi-square, logistic regression, confidence interval, confounder шалгалтаар тестэлнэ.",
                "Мэдлэг үүсгэх гогцоо: холбоо нь шалтгаан гэдгийг шууд хэлэхгүй; өгөгдлийн түүвэр, missing “?” утга, ангиллын хазайлтыг тодорхой бичнэ. Хөдөлмөрийн зах зээлийн мэргэжилтэнтэй үр дүнг review хийж, сургалт/ажлын байрны бодлогын сегментчилэлд зөвхөн шударга, тайлбарлагдах байдлаар ашиглана.",
            ],
        )
        plot_adult(adult, pdf)
        add_text_page(
            pdf,
            "5. Дүгнэлт ба хавсралт",
            [
                "Гол дүгнэлт: графикийн төрөл, масштаб, өнгө, тайлбар нь өгөгдлийн утгыг дамжуулах чанарт шууд нөлөөлдөг. Weather-ийн хугацаа, улирал, тархалтыг өөр өөр графикаар ялган үзүүлэх нь илүү уншигдахуйц болсон.",
                "Хавсаргасан материал: create_report.py код, weather_three_plots.png, retail_bad_good.png, retail_category_sales.png, adult_exploration.png, мөн эх CSV файлууд.",
                "Дахин ажиллуулах: /opt/anaconda3/bin/python create_report.py. Үүсэх PDF нь 12 pt орчим үндсэн тексттэй, 15 хуудасны хязгаарт багтсан тайлангийн загвар юм.",
            ],
        )
    print(report_path)


if __name__ == "__main__":
    build_report()
