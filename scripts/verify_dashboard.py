"""Verify the lab dashboard against existing local evaluation artifacts.

Run ``python -m scripts.verify_dashboard`` from the repository root after
installing requirements-dashboard.txt and training once. This checks the saved
run without retraining or changing it.
"""

import hashlib
import json
import math
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile

import pandas as pd
from streamlit.testing.v1 import AppTest


ROOT = Path(__file__).resolve().parents[1]
DEMO_SELLERS = {
    "confirmed_alert": "de23c3b98a88888289c6f5cc1209054a",
    "false_alarm": "2c9e548be18521d1c43cde1c582c6de8",
}


def check_app(app: AppTest) -> None:
    if app.exception or app.error:
        raise AssertionError([item.message for item in app.exception] + [item.value for item in app.error])


def main() -> None:
    report = json.loads((ROOT / "artifacts/metrics.json").read_text())
    queue = pd.read_csv(ROOT / "artifacts/test_scores.csv", dtype={"seller_id": str})
    assert len(queue) == report["splits"]["test"]["rows"]
    assert int(queue["high_late_rate"].sum()) == report["splits"]["test"]["positives"]
    app = AppTest.from_file(str(ROOT / "dashboard.py"), default_timeout=45).run()
    check_app(app)
    assert app.radio[0].value == "Merchant review"
    app.radio[0].set_value("Model evaluation").run()
    assert [metric.value for metric in app.metric] == [
        f"{len(queue):,}", str(int(queue["high_late_rate"].sum())),
        f"{report['held_out_test']['selected_model']['average_precision']:.3f}",
    ]

    budget_checks = {}
    for budget, values in report["matched_review_budgets"].items():
        pooled = values["pooled"]
        for column, ranking in (("risk_score", "selected_model"), ("baseline_score", "trailing_late_rate")):
            reviews, caught = 0, 0
            for _, month in queue.groupby("target_month"):
                slots = math.ceil(len(month) * int(budget.removesuffix("%")) / 100)
                selected = month.sort_values([column, "seller_id"], ascending=[False, True]).head(slots)
                reviews += len(selected)
                caught += int(selected["high_late_rate"].sum())
            assert (reviews, caught) == (pooled[ranking]["reviewed"], pooled[ranking]["positives_captured"])
        app.radio[1].set_value(budget).run()
        check_app(app)
        selected = pooled["selected_model"]
        sentence = (
            f"With **{selected['reviewed']} reviews**, the model found **{selected['positives_captured']} of "
            f"{pooled['positives']}** high-risk cases. The late-rate rule found "
            f"**{pooled['trailing_late_rate']['positives_captured']}**."
        )
        assert sentence in [item.value for item in app.markdown]
        table = app.dataframe[0].value
        assert table.iloc[0]["Caught"] == selected["positives_captured"]
        budget_checks[budget] = pooled

    app.radio[0].set_value("Merchant review").run()
    check_app(app)
    demo_details = {}
    for name, seller_id in DEMO_SELLERS.items():
        app.selectbox[0].set_value("2018-06").run()
        app.selectbox[1].set_value("All tiers").run()
        app.selectbox[2].set_value(seller_id).run()
        check_app(app)
        row = queue[queue["target_month"].eq("2018-06") & queue["seller_id"].eq(seller_id)].iloc[0]
        result = subprocess.run([
            sys.executable, "-m", "merchant_risk", "score", "--seller-id", seller_id,
            "--as-of", row["score_date"],
        ], cwd=ROOT, check=True, capture_output=True, text=True)
        detail = json.loads(result.stdout)
        assert math.isclose(detail["risk_score"], row["risk_score"], abs_tol=1e-9)
        assert detail["review_action"] == row["review_action"]
        metrics = {metric.label: metric.value for metric in app.metric}
        assert metrics["Next-month risk"] == f"{detail['risk_score']:.1%}"
        assert f"**Suggested action · {detail['review_action']}**" in [item.value for item in app.markdown]
        assert [tab.label for tab in app.tabs] == ["Delivery trend", "Product breakdown", "Score drivers"]
        history = detail["historical_drilldown"]
        assert int(metrics["30-day deliveries"]) == sum(item["deliveries"] for item in history)
        app.radio[1].set_value("product_id").run()
        check_app(app)
        assert "Product ID" in app.dataframe[1].value.columns
        app.radio[1].set_value("category").run()
        demo_details[name] = {
            **detail,
            "observed_deliveries": int(row["target_deliveries"]),
            "observed_late_deliveries": int(row["target_late_deliveries"]),
            "observed_label": int(row["high_late_rate"]),
        }

    app.text_area[0].set_value("Verify carrier handoff")
    app.selectbox[3].set_value("Monitor")
    app.button[0].click().run()
    saved_case = (DEMO_SELLERS["false_alarm"], "2018-06")
    assert app.session_state["merchant_decisions"][saved_case] == {
        "decision": "Monitor", "notes": "Verify carrier handoff",
    }
    app.selectbox[2].set_value(DEMO_SELLERS["confirmed_alert"]).run()
    assert app.text_area[0].value == ""
    app.selectbox[2].set_value(DEMO_SELLERS["false_alarm"]).run()
    assert app.text_area[0].value == "Verify carrier handoff"

    filter_checks = []
    for month in sorted(queue["target_month"].unique()):
        app.selectbox[0].set_value(month).run()
        for tier in ("All tiers", "Escalate for operations review", "Investigate category", "Monitor"):
            app.selectbox[1].set_value(tier).run()
            check_app(app)
            expected = queue[queue["target_month"].eq(month)]
            if tier != "All tiers":
                expected = expected[expected["review_action"].eq(tier)]
            assert len(app.selectbox[2].options) == len(expected)
            filter_checks.append({"month": month, "tier": tier, "sellers": len(expected)})

    # Isolated app copies exercise recovery while preserving the real run.
    with tempfile.TemporaryDirectory() as directory:
        isolated = Path(directory)
        for name in ("dashboard.py", "dashboard.css"):
            shutil.copy2(ROOT / name, isolated / name)
        missing = AppTest.from_file(str(isolated / "dashboard.py")).run()
        check_app(missing)
        missing.radio[0].set_value("Model evaluation").run()
        assert "python -m merchant_risk train" in missing.warning[0].value
        missing.radio[0].set_value("Merchant review").run()
        check_app(missing)
        assert "Missing local inputs" in missing.warning[0].value
        assert missing.code[0].value == "python -m merchant_risk train"

    artifact_names = ["metrics.json", "test_scores.csv", "model.joblib"]
    if (ROOT / "artifacts/backtest_metrics.json").is_file():
        artifact_names.append("backtest_metrics.json")
    output = ROOT / "artifacts/member2-verification.json"
    output.write_text(json.dumps({
        "selected_model": report["selected_model"],
        "artifact_sha256": {
            name: hashlib.sha256((ROOT / "artifacts" / name).read_bytes()).hexdigest()
            for name in artifact_names
        },
        "budgets": budget_checks, "demo_sellers": demo_details,
        "filters": filter_checks, "missing_input_recovery": "passed",
    }, indent=2) + "\n")
    print(f"Passed both budgets, two CLI/dashboard seller matches, {len(filter_checks)} month/tier combinations,")
    print("both drill-down modes, all tab contents, and missing-input recovery.")
    print(f"Evidence saved to {output}")


if __name__ == "__main__":
    main()
