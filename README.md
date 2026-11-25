# MerchantRiskEngine

MerchantRiskEngine is an ML lab project for marketplace fulfilment monitoring. It helps an operations team identify which sellers are likely to have a high late-delivery rate next month, see which products or categories are contributing to recent delays, and decide where to investigate first.

## Prediction target

At the end of each calendar month, score each seller with sufficient historical activity. The model estimates the probability that **at least 20% of the seller's eligible deliveries in the next promised-delivery month will arrive late**.

- Assign each order to a target month using its estimated delivery date. An order is late when its actual delivery date falls after its estimated delivery date.
- Evaluate single-seller orders with a valid estimated delivery date and a completed delivery observed within 30 calendar days after the target month ends. A seller-month needs at least five eligible deliveries to get a label. Report excluded orders and seller-months alongside the metrics.
- Determine scoring eligibility from historical activity available at month-end. The five-delivery requirement applies to evaluation outcomes once they mature.
- Build the score from historical orders, completed deliveries and reviews available on the scoring date. The target measures late delivery among observed completed deliveries. Future cancellations, undelivered orders and credit delinquency are outside this target.

An initial profile of the official Olist files for promised months April 2017 through July 2018 found 80,887 eligible deliveries before the five-delivery minimum. After applying the minimum, 4,098 seller-months across 890 sellers remain, with 510 positive labels (12.4%). They represent 79.6% of the eligible deliveries in that period. These are dataset counts before historical feature and time-split checks.

## Inputs and merchant profile

Download the [Brazilian E-Commerce Public Dataset by Olist](https://www.kaggle.com/datasets/olistbr/brazilian-ecommerce) and extract it locally.

| File | What it provides |
| --- | --- |
| `olist_orders_dataset.csv` | Order, purchase, estimated delivery and actual delivery dates |
| `olist_order_items_dataset.csv` | Order-to-seller and order-to-product mapping, price and freight |
| `olist_order_reviews_dataset.csv` | Review scores and timestamps for historical customer feedback |
| `olist_products_dataset.csv` | Product categories for the drill-down |
| `product_category_name_translation.csv` | Optional English category names for display |

Use trailing 7-, 30- and 90-day summaries where there is enough activity. Start with order volume and category mix, delivery delays and late-delivery rates, and review counts and low-score rates. Include the counts behind rates and compare recent values with the seller's prior history. Use timestamps to establish when each feature became available. Keep cancellation snapshots out of historical features where the event date is unavailable.

## Merchant score and product drill-down

- **Merchant score.** Show the forecast, the largest model drivers, and recent rates with their order counts and historical baselines.
- **Product drill-down.** Show which categories contribute the most to the seller's recently observed late deliveries, alongside their order counts and late-delivery rates. Show individual products when there is enough history. For orders spanning several categories, use a consistent assignment rule so counts reconcile to the merchant total.
- **Review actions.** Start with Monitor, Investigate category, and Escalate for operations review. Choose score thresholds on validation data and show which categories merit review.

The product drill-down describes observed outcomes. Its scope is to localise a merchant alert, while the forecast is evaluated at seller-month level.

## Lab evaluation

1. Check join uniqueness, timestamp availability, missingness, seller coverage and positive counts by month. Confirm that the completed-delivery and historical-volume requirements leave usable validation and test periods.
2. Split chronologically into train, validation and test. Require each development label to mature before the next split starts.
3. Compare a rule based on the seller's trailing late-delivery rate with logistic regression and a tree-based model. Use average precision as the primary metric and show the positive-rate baseline. Report precision, recall and review volume at a threshold fixed on validation.
4. Compare models with and without product-mix and feedback features to test whether they improve on historical fulfilment rates and order volume. Use SHAP for model explanations and Apriori to explore combinations of historical warning signs after the baseline is established.

The TVS Credit case study motivates the merchant and product views. This lab version uses observed fulfilment outcomes from Olist and requires no synthetic repayments or Home Credit download. A future credit-risk extension would require linked merchant orders, loan IDs and repayment events.

Keep source datasets local. Share source links, code and reproducible results through Git.
