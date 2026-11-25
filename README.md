# MerchantRiskEngine

An ML lab project for forecasting merchant risk from marketplace activity and explaining which signals drive each score.

## Dataset recommendation

Use the [Brazilian E-Commerce Public Dataset by Olist](https://www.kaggle.com/datasets/olistbr/brazilian-ecommerce). It contains about 100,000 anonymised orders from 2016–2018. For the main lab experiment, score **observed delivery risk**. At each month-end, predict whether a seller's share of late deliveries will meet or exceed a fixed threshold in the next calendar month. Use the promised delivery date to assign orders to a target month and compare actual and promised calendar dates to identify late deliveries. Start with single-seller orders and valid delivery timestamps. Report coverage and exclusions, including cancellations, missing timestamps and multi-seller orders. Check the usable row and positive counts before fixing cohort-size and label thresholds. If monthly coverage is too thin, predict late delivery per order and aggregate the predictions for the merchant dashboard.

A preliminary check of the official orders and items files found 81,050 single-seller orders with valid actual and estimated delivery dates for promised months April 2017 through July 2018. With at least five observed deliveries in the target month and a late-rate cutoff of at least 20%, there are 4,103 eligible seller-months across 890 sellers, including 523 positives (12.7%). These counts cover 79.6% of the deliveries in that sample and precede historical-feature eligibility and time-split checks. The five-delivery rule describes which outcomes can be evaluated reliably. At scoring time, use only historical volume to assess whether there is enough data to score a seller.

The project proposal and presenter guide describe a different endpoint: an instalment reaching 30+ days past due within 60 days. Olist has no linked loan repayment or return records. To retain that endpoint, use a documented, reproducible simulation with explicit financing and repayment assumptions. [Home Credit Default Risk](https://www.kaggle.com/competitions/home-credit-default-risk/data) provides optional calibration via `installments_payments.csv` and `POS_CASH_balance.csv`. The competition data requires accepting Kaggle's rules. Its applicant default rate is a different quantity from the prevalence of delinquent merchant-months. For a project centered on observed borrower default, [Home Credit Credit Risk Model Stability](https://www.kaggle.com/c/home-credit-credit-risk-model-stability/data) provides loan-level labels and time indices.

## What to download first

Download the Olist archive and extract it locally. Start with these three CSVs:

| CSV | Fields and role |
| --- | --- |
| `olist_orders_dataset.csv` | `order_id`, purchase date, estimated delivery date and actual delivery date. Supplies the outcome and event timing. |
| `olist_order_items_dataset.csv` | `order_id`, `seller_id`, item ID, price and freight. Supplies the order-to-seller link and transaction features. |
| `olist_order_reviews_dataset.csv` | `order_id`, review score and response timestamp. Supplies historical customer feedback. |

Products and category translation can add category mix. Customers and sellers can add location. Order payments can add checkout payment type and instalment count. Olist's instalment count describes a payment choice. Loan terms, repayment dates and delinquency require separate data.

For real merchant-linked credit training, the minimum additional inputs are pseudonymous order, seller and loan IDs with a verified mapping, origination date and terms, instalment due dates and amounts, payment dates and amounts or dated days-past-due snapshots, and enough follow-up to observe the full 60-day outcome window.

## Training and evaluation

1. Join orders to seller IDs and deduplicate at the seller–order level before aggregation. Keep features available by each scoring cutoff. Use observed delivery and review timestamps to build trailing volume, delays, feedback and changes against a seller's earlier history. For statuses without an event timestamp, leave them out of historical features unless their availability can be established.
2. Profile monthly seller coverage, order counts, missingness and class balance. Require sufficient historical support and report which seller-months are eligible. Freeze target and cohort rules using the development period.
3. Split chronologically into train, validation and test. Require each training or validation label to have fully matured before the next split starts. Compare a trailing late-rate rule, logistic regression and a tree-based model on the same splits. Report average precision, the positive-rate baseline, and precision and recall at a threshold picked on validation.
4. Explain scores and use them to prioritise merchant review. Carry forward SHAP and Apriori for the lab demonstration once the baseline and held-out evaluation are in place.

Keep raw datasets and competition downloads local. Share source links, code and reproducible results through Git.
