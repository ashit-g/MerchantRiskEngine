"""Streamlit frontend for the historical Olist seller review workflow."""

import math
from pathlib import Path

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from merchant_risk.data import REQUIRED_FILES, read_olist
from merchant_risk.features import LATE_RATE_PERCENT, previous_window
from merchant_risk.model import score_seller


ROOT = Path(__file__).resolve().parent
DATA_DIR = ROOT / "data" / "olist"
MODEL_PATH = ROOT / "artifacts" / "model.joblib"
QUEUE_PATH = ROOT / "artifacts" / "test_scores.csv"
TIERS = ("Escalate for operations review", "Investigate category", "Monitor")
TIER_LABELS = dict(zip(TIERS, ("Escalate", "Investigate", "Monitor")))
TEAL = "#00796F"
GRID = "#E3EAEE"

FEATURE_LABELS = {
    "mean_order_value_30d": "Average order value · last 30 days",
    "mean_freight_30d": "Average freight cost · last 30 days",
    "mean_delay_30d": "Average delivery delay · last 30 days",
    "previous_late_rate_90d": "Late-delivery rate · prior 90-day baseline",
    "late_rate_change": "Change in late-delivery rate · last 30 days vs baseline",
    "order_volume_change": "Change in orders · last 30 days vs baseline",
    "category_count_30d": "Product categories · last 30 days",
    "top_category_share_30d": "Order share of leading category · last 30 days",
    "previous_low_review_rate_90d": "Low-review rate · prior 90-day baseline",
    "low_review_rate_change": "Change in low-review rate · last 30 days vs baseline",
}
for period in (7, 30, 90):
    for prefix, label in (
        ("orders", "Orders"), ("deliveries", "Completed deliveries"),
        ("late_rate", "Late-delivery rate"), ("reviews", "Reviews"), ("low_review_rate", "Low-review rate"),
    ):
        FEATURE_LABELS[f"{prefix}_{period}d"] = f"{label} · last {period} days"


@st.cache_data(show_spinner=False)
def load_queue(path: Path, modified: int) -> pd.DataFrame:
    return pd.read_csv(path, dtype={"seller_id": str, "target_month": str}, parse_dates=["score_date"])


@st.cache_resource(show_spinner=False)
def load_olist(data_modified: tuple) -> tuple[pd.DataFrame, pd.DataFrame]:
    # The dataframes are shared across sessions and used as read-only inputs.
    return read_olist(DATA_DIR)


@st.cache_data(show_spinner=False, max_entries=128)
def load_seller_detail(
    seller_id: str, cutoff: pd.Timestamp, group_by: str, model_modified: int,
    data_modified: tuple, _orders: pd.DataFrame, _reviews: pd.DataFrame,
) -> dict:
    return score_seller(_orders, _reviews, MODEL_PATH, seller_id, cutoff, group_by)


def month_label(month: str) -> str:
    return pd.Period(month, freq="M").strftime("%B %Y")


def category_label(value: str) -> str:
    return str(value).replace("_", " ").title()


def feature_value(feature: str, value: float) -> str:
    if feature in {"late_rate_change", "low_review_rate_change"}:
        return f"{value * 100:+.1f} pp"
    if "rate" in feature or "share" in feature:
        return f"{value:.1%}"
    if feature in {"mean_order_value_30d", "mean_freight_30d"}:
        return f"R$ {value:,.2f}"
    if feature == "mean_delay_30d":
        return f"{value:.1f} days"
    return f"{value:,.1f}".removesuffix(".0")


def draw_delivery_trend(orders: pd.DataFrame, seller_id: str, cutoff: pd.Timestamp) -> None:
    seller = orders[orders["seller_id"].eq(seller_id) & orders["delay_days"].notna()]
    recent = previous_window(seller, "delivered", cutoff, 84).copy()
    if recent.empty:
        st.info("No completed deliveries with usable dates in the last 12 weeks.")
        return
    recent["week"] = (cutoff - recent["delivered"]).dt.days // 7
    trend = recent.groupby("week")["late"].agg(rate="mean", deliveries="size").reindex(range(11, -1, -1))
    week_ends = cutoff - pd.to_timedelta(trend.index * 7, unit="D")
    chart = go.Figure(go.Scatter(
        x=week_ends, y=trend["rate"], customdata=trend["deliveries"],
        mode="lines+markers", line={"color": TEAL, "width": 3}, marker={"size": 7},
        hovertemplate="Week ending %{x:%d %b}<br>%{y:.1%} late · %{customdata:.0f} deliveries<extra></extra>",
    ))
    chart.update_layout(height=225, margin={"l": 8, "r": 10, "t": 12, "b": 8})
    chart.update_yaxes(tickformat=".0%", rangemode="tozero", gridcolor=GRID)
    chart.update_xaxes(showgrid=False, tickformat="%d %b", nticks=6)
    st.plotly_chart(chart, width="stretch", config={"displayModeBar": False})


def draw_drilldown(detail: dict, group_by: str) -> None:
    history = pd.DataFrame(detail["historical_drilldown"])
    if history.empty:
        st.info("No completed deliveries with usable dates in the last 30 days.")
        return
    label = "Category" if group_by == "category" else "Product ID"
    history = history.rename(columns={group_by: label})
    if group_by == "category":
        history[label] = history[label].map(category_label)
    st.dataframe(
        history,
        hide_index=True,
        width="stretch",
        height="auto",
        column_config={
            "deliveries": st.column_config.NumberColumn("Deliveries"),
            "late_deliveries": st.column_config.NumberColumn("Late"),
            "late_rate": st.column_config.NumberColumn("Late rate", format="percent"),
            "share_of_seller_late_deliveries": st.column_config.NumberColumn("Share of all late", format="percent"),
        },
    )


def draw_drivers(detail: dict) -> None:
    comparisons = detail["feature_comparisons"]
    if not comparisons:
        st.info("No individual feature comparison changed this score.")
        return
    rows = []
    for comparison in comparisons:
        feature = comparison["feature"]
        rows.append({
            "Signal": FEATURE_LABELS.get(feature, feature.replace("_", " ").capitalize()),
            "Seller value": feature_value(feature, comparison["value"]),
            "Training median": feature_value(feature, comparison["training_median"]),
            "Score difference": f"{comparison['score_change_vs_median'] * 100:+.1f} pp",
        })
    st.dataframe(rows, hide_index=True, width="stretch")


def main() -> None:
    st.set_page_config(page_title="MerchantRiskEngine", layout="wide")
    st.html("""
        <style>
        .stMainBlockContainer {max-width: 1360px; padding-top: 2rem; padding-bottom: 3rem;}
        [data-testid="stMetric"] {font-variant-numeric: tabular-nums;}
        [data-testid="stMetricValue"] {letter-spacing: -.03em;}
        @media (max-width: 740px) {
            .st-key-review_workflow [data-testid="stHorizontalBlock"]:has(> [data-testid="stColumn"]:nth-child(2):last-child) {
                flex-wrap: wrap;
            }
            .st-key-review_workflow [data-testid="stHorizontalBlock"] > [data-testid="stColumn"]:nth-last-child(2):first-child,
            .st-key-review_workflow [data-testid="stHorizontalBlock"] > [data-testid="stColumn"]:nth-child(2):last-child {
                flex: 1 1 100%;
                min-width: 0;
            }
        }
        </style>
    """)
    st.caption("MARKETPLACE FULFILMENT  /  HISTORICAL OLIST EVALUATION")
    st.title("MerchantRiskEngine")
    st.write("Prioritise sellers for review and see where recent delivery delays are concentrated.")

    data_paths = [DATA_DIR / name for name in REQUIRED_FILES.values()]
    missing = [path.name for path in [*data_paths, MODEL_PATH, QUEUE_PATH] if not path.is_file()]
    if missing:
        st.warning(f"Missing local inputs: {', '.join(missing)}.")
        st.write("Extract Olist into `data/olist/` and generate the model and review queue from the repository root.")
        st.code("python -m merchant_risk train", language="bash")
        st.stop()

    queue = load_queue(QUEUE_PATH, QUEUE_PATH.stat().st_mtime_ns)
    if queue.empty:
        st.warning("The held-out seller queue is empty. Run training again to regenerate it.")
        st.stop()
    months = sorted(queue["target_month"].unique())
    month_col, tier_col = st.columns(2)
    target_month = month_col.selectbox("Forecast month", months, format_func=month_label)
    month_queue = queue[queue["target_month"].eq(target_month)]
    cutoff = month_queue["score_date"].iloc[0]
    tier_filter = tier_col.selectbox("Review tier", ("All tiers", *TIERS))

    stats = st.columns(4)
    stats[0].metric("Sellers evaluated", f"{len(month_queue):,}", border=True)
    for metric, (tier, name) in zip(stats[1:], TIER_LABELS.items()):
        metric.metric(name, f"{month_queue['review_action'].eq(tier).sum():,}", border=True)
    st.caption(f"Scores use information available by {cutoff:%d %B %Y}. Counts include all review tiers for this month.")

    visible = month_queue if tier_filter == "All tiers" else month_queue[month_queue["review_action"].eq(tier_filter)]
    visible = visible.sort_values(["risk_score", "seller_id"], ascending=[False, True])
    if visible.empty:
        st.info("No sellers match this review tier for the selected month.")
        st.stop()

    workflow = st.container(key="review_workflow")
    queue_col, detail_col = workflow.columns([0.9, 1.3], gap="medium")
    with queue_col:
        with st.container(border=True):
            st.subheader("Seller review queue")
            st.caption(f"{len(visible):,} sellers · highest forecast risk first")
            seller_id = st.selectbox(
                "Inspect seller", visible["seller_id"].tolist(), format_func=lambda value: value[:12],
            )
            queue_table = visible[["seller_id", "risk_score", "review_action"]].copy()
            queue_table["seller_id"] = queue_table["seller_id"].str[:12]
            queue_table["review_action"] = queue_table["review_action"].map(TIER_LABELS)
            st.dataframe(
                queue_table, hide_index=True, height=310, width="stretch",
                column_config={
                    "seller_id": "Seller ID",
                    "risk_score": st.column_config.ProgressColumn(
                        "Forecast risk", min_value=0, max_value=1, format="percent",
                    ),
                    "review_action": "Review tier",
                },
            )

    optional = DATA_DIR / "product_category_name_translation.csv"
    data_modified = tuple((path.name, path.stat().st_mtime_ns) for path in [*data_paths, optional] if path.is_file())
    with detail_col:
        with st.container(border=True):
            st.subheader("Seller profile")
            st.caption(seller_id)
            labels = {"category": "Category", "product_id": "Product"}
            group_by = st.radio(
                "Group recent deliveries by", tuple(labels), format_func=labels.get, horizontal=True,
            )
            try:
                with st.spinner("Loading seller profile…"):
                    orders, reviews = load_olist(data_modified)
                    detail = load_seller_detail(
                        seller_id, cutoff, group_by, MODEL_PATH.stat().st_mtime_ns, data_modified, orders, reviews,
                    )
            except (ValueError, FileNotFoundError) as error:
                st.warning(str(error))
                st.stop()

            selected = visible.loc[visible["seller_id"].eq(seller_id)].iloc[0]
            if not math.isclose(detail["risk_score"], selected["risk_score"], abs_tol=1e-9) \
                    or detail["review_action"] != selected["review_action"]:
                st.error("The saved model and queue disagree. Run `python -m merchant_risk train` to refresh both.")
                st.stop()
            history = detail["historical_drilldown"]
            deliveries = sum(row["deliveries"] for row in history)
            late = sum(row["late_deliveries"] for row in history)
            score_stat, late_stat, count_stat = st.columns(3)
            score_stat.metric("Forecast risk", f"{detail['risk_score']:.1%}")
            late_stat.metric("30-day late rate", f"{late / deliveries:.1%}" if deliveries else "—")
            count_stat.metric("30-day deliveries", deliveries)
            st.markdown(f"**{detail['review_action']}**")
            st.caption(
                f"Forecast for {month_label(target_month)}: chance that at least {LATE_RATE_PERCENT}% "
                "of eligible deliveries will arrive late."
            )

            trend_tab, product_tab, reasons_tab = st.tabs(["Delivery trend", "Product breakdown", "Score drivers"])
            with trend_tab:
                st.caption("Weekly late-delivery rates for the 12 weeks ending on the scoring date.")
                draw_delivery_trend(orders, seller_id, cutoff)
            with product_tab:
                st.caption("Completed deliveries in the 30 days ending on the scoring date.")
                draw_drilldown(detail, group_by)
            with reasons_tab:
                st.caption("Score difference when each seller value is compared with its training median, one feature at a time.")
                draw_drivers(detail)


if __name__ == "__main__":
    main()
