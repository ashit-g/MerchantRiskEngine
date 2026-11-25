from pathlib import Path

import pandas as pd


REQUIRED_FILES = {
    "orders": "olist_orders_dataset.csv",
    "items": "olist_order_items_dataset.csv",
    "reviews": "olist_order_reviews_dataset.csv",
    "products": "olist_products_dataset.csv",
}


def read_olist(data_dir: Path) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Return one row per eligible seller order and one dated review per order."""
    paths = {key: data_dir / name for key, name in REQUIRED_FILES.items()}
    missing = [path.name for path in paths.values() if not path.is_file()]
    if missing:
        raise FileNotFoundError(f"Missing Olist files in {data_dir}: {', '.join(missing)}")

    orders = pd.read_csv(paths["orders"], usecols=[
        "order_id", "order_status", "order_purchase_timestamp",
        "order_estimated_delivery_date", "order_delivered_customer_date",
    ]).rename(columns={
        "order_purchase_timestamp": "purchased",
        "order_estimated_delivery_date": "promised",
        "order_delivered_customer_date": "delivered",
    })
    for column in ("purchased", "promised", "delivered"):
        orders[column] = pd.to_datetime(orders[column], errors="raise").dt.normalize()
    orders = orders.dropna(subset=["purchased"]).copy()

    items = pd.read_csv(paths["items"], usecols=[
        "order_id", "order_item_id", "seller_id", "product_id", "price", "freight_value",
    ])
    items = items.dropna(subset=["seller_id"])
    seller_counts = items.groupby("order_id")["seller_id"].nunique()
    items = items[items["order_id"].isin(seller_counts.index[seller_counts.eq(1)])]
    # One representative product per order keeps the drill-down totals additive.
    representative = (
        items.sort_values(["price", "order_item_id"], ascending=[False, True])
        .drop_duplicates("order_id")[["order_id", "seller_id", "product_id"]]
    )
    amounts = items.groupby("order_id", as_index=False).agg(
        order_value=("price", "sum"), freight_value=("freight_value", "sum"),
    )
    products = pd.read_csv(paths["products"], usecols=["product_id", "product_category_name"])
    products = products.rename(columns={"product_category_name": "category"})
    translation_path = data_dir / "product_category_name_translation.csv"
    if translation_path.is_file():
        translations = pd.read_csv(translation_path).set_index("product_category_name")
        products["category"] = (
            products["category"].map(translations["product_category_name_english"])
            .fillna(products["category"])
        )
    orders = (
        orders.merge(representative, on="order_id", validate="one_to_one")
        .merge(amounts, on="order_id", validate="one_to_one")
        .merge(products, on="product_id", how="left", validate="many_to_one")
    )
    orders["category"] = orders["category"].fillna("Unknown")
    orders["delay_days"] = (orders["delivered"] - orders["promised"]).dt.days
    # Invalid event sequences cannot establish a delivery that was known at a cutoff.
    invalid_delivery = orders["delivered"].lt(orders["purchased"])
    orders.loc[invalid_delivery, ["delivered", "delay_days"]] = [pd.NaT, float("nan")]
    orders["late"] = orders["delay_days"].gt(0)

    reviews = pd.read_csv(paths["reviews"], usecols=[
        "order_id", "review_id", "review_score", "review_answer_timestamp",
    ]).rename(columns={"review_answer_timestamp": "reviewed"})
    reviews["reviewed"] = pd.to_datetime(reviews["reviewed"], errors="raise")
    reviews = reviews.merge(
        orders[["order_id", "purchased", "seller_id"]], on="order_id", validate="many_to_one",
    )
    reviews = reviews[reviews["review_score"].between(1, 5) & reviews["reviewed"].ge(reviews["purchased"])]
    reviews = reviews.sort_values(["reviewed", "review_id", "review_score"]).drop_duplicates("order_id").copy()
    reviews["reviewed"] = reviews["reviewed"].dt.normalize()
    reviews["low_review"] = reviews["review_score"].le(2)
    return orders, reviews
