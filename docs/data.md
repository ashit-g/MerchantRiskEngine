# Data and target

Download the original [Olist archive](https://www.kaggle.com/datasets/olistbr/brazilian-ecommerce) and extract these files into `data/olist/`. For a different location, pass `--data-dir` to the CLI.

| File | Role |
| --- | --- |
| `olist_orders_dataset.csv` | Purchase, estimated delivery and actual delivery dates, plus order status |
| `olist_order_items_dataset.csv` | Order-to-seller and order-to-product mapping, price and freight |
| `olist_order_reviews_dataset.csv` | Review scores and answer timestamps for historical feedback |
| `olist_products_dataset.csv` | Product categories |
| `product_category_name_translation.csv` | Optional English translations for display |

Only orders with one identifiable seller are used. Order value and freight are summed across items. For the drill-down, each order belongs to the category of its highest-priced item, breaking ties by item sequence. This makes category counts reconcile with the seller totals. Reviews use the earliest valid response per order. Missing categories appear as **Unknown**.

## Label

For each seller and target calendar month:

1. Start with single-seller orders whose estimated delivery date falls in the target month.
2. Include completed deliveries with usable actual dates through 30 calendar days after that month ends. An actual calendar date after the estimated date counts as late.
3. Require at least five eligible deliveries. Mark the seller-month positive when at least 20% of eligible deliveries were late.

Eligibility to **score** a seller uses a separate rule of at least five purchases in the trailing 90 days as of the prior month-end. The outcomes can enter evaluation only when the target month and its 30-day follow-up are covered. The last observed purchase date is used as a conservative bound for dataset coverage.

The label covers completed deliveries with usable dates. Cancellations, undelivered orders and deliveries after the follow-up are outside the definition. Order status is a snapshot, so it is used for outcome eligibility rather than as a historical feature. The data contains no linked consumer loan outcomes or verified returns.

A preliminary profile for April 2017 through July 2018 found 80,887 deliveries with the required dates and follow-up before the five-delivery minimum. The minimum left 4,098 seller-months across 890 sellers and 510 positives (12.4%). Those counts precede the historical activity requirement and chronological split gaps.
