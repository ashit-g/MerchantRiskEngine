import pandas as pd


MIN_TARGET_DELIVERIES = 5
LATE_RATE_PERCENT = 20
LABEL_GRACE_DAYS = 30
MIN_HISTORICAL_ORDERS = 5
TARGET = "high_late_rate"

BASE_FEATURES = [
    "orders_7d", "orders_30d", "orders_90d", "mean_order_value_30d", "mean_freight_30d",
    "deliveries_7d", "deliveries_30d", "deliveries_90d",
    "late_rate_7d", "late_rate_30d", "late_rate_90d", "mean_delay_30d",
    "previous_late_rate_90d", "late_rate_change", "order_volume_change",
]
EXTRA_FEATURES = [
    "category_count_30d", "top_category_share_30d",
    "reviews_30d", "reviews_90d", "low_review_rate_30d", "low_review_rate_90d",
    "previous_low_review_rate_90d", "low_review_rate_change",
]


FULFILMENT_CONTEXT_FEATURES = [
    "late_rate_30d_smoothed", "late_rate_90d_smoothed", "market_late_rate_30d",
    "recent_due_orders_undelivered_share", "overdue_open_orders_90d",
    "mean_promised_lead_days_30d", "late_rate_recent_vs_market",
]
KNOWN_NEXT_MONTH_FEATURES = [
    "known_next_month_orders", "known_next_month_delivered_share",
    "known_next_month_days_to_promise", "known_next_month_open_days",
]


def month_end(month: pd.Period) -> pd.Timestamp:
    return month.end_time.normalize()


def maturity_date(target_month: pd.Period) -> pd.Timestamp:
    return month_end(target_month) + pd.Timedelta(days=LABEL_GRACE_DAYS)


def previous_window(frame: pd.DataFrame, date_col: str, cutoff: pd.Timestamp, days: int) -> pd.DataFrame:
    start = cutoff - pd.Timedelta(days=days)
    return frame[frame[date_col].gt(start) & frame[date_col].le(cutoff)]


def seller_features(orders: pd.DataFrame, reviews: pd.DataFrame, cutoff: pd.Timestamp) -> pd.DataFrame:
    """Build features from events observed on or before the scoring date."""
    recent_orders = previous_window(orders, "purchased", cutoff, 90)
    seller_counts = recent_orders.groupby("seller_id").size()
    sellers = seller_counts.index[seller_counts.ge(MIN_HISTORICAL_ORDERS)]
    features = pd.DataFrame(index=sellers)

    deliveries = orders[orders["delay_days"].notna()]
    for days in (7, 30, 90):
        purchased = previous_window(recent_orders, "purchased", cutoff, days)
        delivered = previous_window(deliveries, "delivered", cutoff, days)
        purchase_group = purchased.groupby("seller_id")
        delivery_group = delivered.groupby("seller_id")
        features[f"orders_{days}d"] = purchase_group.size().reindex(sellers, fill_value=0)
        features[f"deliveries_{days}d"] = delivery_group.size().reindex(sellers, fill_value=0)
        features[f"late_rate_{days}d"] = delivery_group["late"].mean()
        if days == 30:
            features["mean_order_value_30d"] = purchase_group["order_value"].mean()
            features["mean_freight_30d"] = purchase_group["freight_value"].mean()
            features["mean_delay_30d"] = delivery_group["delay_days"].mean()
            categories = purchased.groupby(["seller_id", "category"]).size().groupby(level=0)
            features["category_count_30d"] = categories.size().reindex(sellers, fill_value=0)
            features["top_category_share_30d"] = categories.max() / purchase_group.size()

    for days in (30, 90):
        review_group = previous_window(reviews, "reviewed", cutoff, days).groupby("seller_id")
        features[f"reviews_{days}d"] = review_group.size().reindex(sellers, fill_value=0)
        features[f"low_review_rate_{days}d"] = review_group["low_review"].mean()

    prior_cutoff = cutoff - pd.Timedelta(days=30)
    prior_deliveries = previous_window(deliveries, "delivered", prior_cutoff, 90)
    prior_reviews = previous_window(reviews, "reviewed", prior_cutoff, 90)
    prior_orders = previous_window(orders, "purchased", prior_cutoff, 90)
    features["previous_late_rate_90d"] = prior_deliveries.groupby("seller_id")["late"].mean()
    features["previous_low_review_rate_90d"] = prior_reviews.groupby("seller_id")["low_review"].mean()
    features["late_rate_change"] = features["late_rate_30d"] - features["previous_late_rate_90d"]
    features["low_review_rate_change"] = (
        features["low_review_rate_30d"] - features["previous_low_review_rate_90d"]
    )
    features["order_volume_change"] = (
        features["orders_30d"] - prior_orders.groupby("seller_id").size().reindex(sellers, fill_value=0) / 3
    )
    recent_deliveries = previous_window(deliveries, "delivered", cutoff, 30)
    market_late_rate = recent_deliveries["late"].mean()
    features["market_late_rate_30d"] = market_late_rate
    for days in (30, 90):
        window = previous_window(deliveries, "delivered", cutoff, days)
        late_counts = window.groupby("seller_id")["late"].sum().reindex(sellers, fill_value=0)
        # Stabilise rates of sellers with only a few completed deliveries.
        features[f"late_rate_{days}d_smoothed"] = (
            (late_counts + 10 * market_late_rate) / (features[f"deliveries_{days}d"] + 10)
        )
    features["late_rate_recent_vs_market"] = features["late_rate_30d_smoothed"] - market_late_rate

    due = recent_orders[recent_orders["promised"].lt(cutoff)]
    awaiting_delivery = due[due["delivered"].isna() | due["delivered"].gt(cutoff)]
    features["overdue_open_orders_90d"] = (
        awaiting_delivery.groupby("seller_id").size().reindex(sellers, fill_value=0)
    )
    due_last_week = due[due["promised"].ge(cutoff - pd.Timedelta(days=7))]
    awaiting_last_week = awaiting_delivery[awaiting_delivery["promised"].ge(cutoff - pd.Timedelta(days=7))]
    features["recent_due_orders_undelivered_share"] = (
        awaiting_last_week.groupby("seller_id").size().reindex(sellers, fill_value=0)
        / due_last_week.groupby("seller_id").size().reindex(sellers)
    )
    orders_30d = previous_window(recent_orders, "purchased", cutoff, 30)
    lead_time = (orders_30d["promised"] - orders_30d["purchased"]).dt.days
    features["mean_promised_lead_days_30d"] = lead_time.where(lead_time.ge(0)).groupby(
        orders_30d["seller_id"]
    ).mean()

    target_month = cutoff.to_period("M") + 1
    known_orders = recent_orders[recent_orders["promised"].between(target_month.start_time, month_end(target_month))]
    known_counts = known_orders.groupby("seller_id").size()
    known_delivered = known_orders["delivered"].le(cutoff)
    known_completed = known_delivered.groupby(known_orders["seller_id"]).sum()
    features["known_next_month_orders"] = known_counts.reindex(sellers, fill_value=0)
    features["known_next_month_delivered_share"] = known_completed / known_counts
    days_to_promise = (known_orders["promised"] - cutoff).dt.days
    features["known_next_month_days_to_promise"] = days_to_promise.groupby(known_orders["seller_id"]).mean()
    open_age = (cutoff - known_orders["purchased"]).dt.days
    features["known_next_month_open_days"] = open_age.where(~known_delivered).groupby(known_orders["seller_id"]).mean()
    features["score_date"] = cutoff
    return features.reset_index()


def monthly_outcomes(
    orders: pd.DataFrame, target_month: pd.Period, observed_through: pd.Timestamp,
) -> pd.DataFrame:
    mature = maturity_date(target_month)
    if mature > observed_through:
        raise ValueError(f"The {target_month} target needs observations through {mature.date()}.")
    cohort = orders[orders["promised"].between(target_month.start_time, month_end(target_month))]
    delivered = cohort[
        cohort["order_status"].eq("delivered") & cohort["delay_days"].notna() & cohort["delivered"].le(mature)
    ]
    counts = delivered.groupby("seller_id", as_index=False).agg(
        target_deliveries=("late", "size"), target_late_deliveries=("late", "sum"),
    )
    counts[TARGET] = pd.Series(pd.NA, index=counts.index, dtype="Int64")
    eligible = counts["target_deliveries"].ge(MIN_TARGET_DELIVERIES)
    counts.loc[eligible, TARGET] = (
        counts.loc[eligible, "target_late_deliveries"] * 100
        >= counts.loc[eligible, "target_deliveries"] * LATE_RATE_PERCENT
    ).astype(int)
    return counts


def product_drilldown(
    orders: pd.DataFrame, seller_id: str, cutoff: pd.Timestamp, group_by: str = "category",
) -> pd.DataFrame:
    seller = orders[orders["seller_id"].eq(seller_id) & orders["delay_days"].notna()]
    recent = previous_window(seller, "delivered", cutoff, 30)
    result = recent.groupby(group_by, as_index=False, dropna=False).agg(
        deliveries=("late", "size"), late_deliveries=("late", "sum"),
    )
    result["late_rate"] = result["late_deliveries"] / result["deliveries"]
    total_late = result["late_deliveries"].sum()
    result["share_of_seller_late_deliveries"] = result["late_deliveries"] / total_late if total_late else 0.0
    return result.sort_values(["late_deliveries", "deliveries", group_by], ascending=[False, False, True])
