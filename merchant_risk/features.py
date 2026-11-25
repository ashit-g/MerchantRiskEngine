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
