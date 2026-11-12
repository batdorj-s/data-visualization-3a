from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import pandas as pd  # noqa: E402
import pytest  # noqa: E402

from src.chart_qa import check  # noqa: E402
from src.charts.summary import fig_data_quality, fig_hypothesis_summary, verdict  # noqa: E402

REP = Path(__file__).resolve().parents[1] / "reports"


@pytest.fixture(autouse=True)
def _close():
    yield
    plt.close("all")


def row(**kw):
    return pd.Series({"estimate": 0.3, "ci_lo": 0.1, "ci_hi": 0.5, "null_value": 0.0, **kw})


def test_verdict():
    assert verdict(row()) == "Дэмжигдсэн"
    assert verdict(row(ci_lo=-0.1)) == "Тодорхойгүй"
    assert verdict(row(estimate=0.4, ci_lo=0.35, ci_hi=0.45, null_value=0.5)) == "Дэмжигдээгүй"


def test_hypothesis_summary_one_axis_per_hypothesis():
    hyp = pd.read_csv(REP / "hypotheses.csv")
    fig = fig_hypothesis_summary(hyp)
    assert len(fig.axes) == len(hyp) == 5
    check(fig)


def test_data_quality_qa():
    fig = fig_data_quality(pd.read_csv(REP / "missing.csv"), pd.read_csv(REP / "name_matches.csv"),
                           pd.read_csv(REP / "ppg_validation.csv"))
    assert len(fig.axes) == 3
    check(fig)
