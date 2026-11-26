# Modelling and evaluation

The TVS Credit case study informs the product flow. The lab implementation uses marketplace fulfilment outcomes to demonstrate detection, explanation and review prioritisation.

## Features and model comparison

| Feature group | Examples |
| --- | --- |
| Order activity | Trailing 7-, 30- and 90-day counts, order value and freight, and recent volume versus prior history |
| Fulfilment | Trailing delivery counts and late rates, recent mean delivery delay, and the 30-day late rate versus the preceding 90 days |
| Product mix and feedback | Category count and concentration, review volume, low-review rates, and change relative to prior history |

Each feature uses the date of the event it describes. A late delivery enters the history when it is delivered. A review enters on its answer date. A missing rate remains missing until a training-fitted imputer handles it. Counts give context for rates from small samples. Seller and product IDs are used for grouping and reporting.

Compare logistic regression and a random forest with and without product-mix and feedback features. Use the trailing 90-day late rate as the simple ranking baseline. Fit and preprocess on training data, then select the learned configuration with the highest validation average precision. Compare the selected configuration with the rule on the held-out data. The positive rate gives context for average precision under class imbalance.

## Evaluation windows

| Split | Promised-delivery months |
| --- | --- |
| Train | April–December 2017 |
| Validation | March–April 2018 |
| Test | June–July 2018 |

The gaps let outcome labels finish maturing before the next split's scoring dates. The report records coverage by month, including historically eligible sellers, seller-months with labels, their intersection, and positives. It includes average precision, precision, recall and the review rate. Brier score is reported for the learned probabilities.

## Matched review budgets

For the held-out comparison, rank the same evaluable sellers separately for each target month using the selected model and the trailing late-rate rule. Allocate 10% and 25% of that month's seller-months as review slots, rounded up to whole sellers. Break score ties by seller ID in ascending order without using outcomes. Report the number reviewed, positives captured, precision and recall by month and from pooled counts.

This retrospective comparison is limited to historically eligible sellers with mature outcome labels. It compares rankings at a common review capacity. The CLI action tiers use validation thresholds for individual scores, so their review volume can vary. See `matched_review_budgets` in `artifacts/metrics.json` and `baseline_score` in `artifacts/test_scores.csv`.

## Decision output

Validation score percentiles give illustrative review thresholds. Scores above the 75th percentile trigger **Investigate category**, and scores above the 90th percentile trigger **Escalate for operations review**. Remaining scores map to **Monitor**. Review volumes may differ on later data and when scores tie.

For each score, replace one feature at a time with its training median and report the largest changes. This gives a simple model sensitivity check. The product drill-down ranks categories or product IDs by their contribution to observed late deliveries in the past 30 days, with counts and rates for context.

The implementation provides a training and scoring CLI, evaluation outputs, and a Streamlit dashboard for the historical seller review workflow. SHAP and Apriori are follow-on work.
