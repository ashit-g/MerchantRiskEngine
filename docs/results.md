# Initial Olist results

The first run uses observed late deliveries and one row per eligible seller-month. Reproduce it with `python -m merchant_risk train`. The generated `artifacts/metrics.json` has the full breakdown.

## Coverage and label balance

The table below was regenerated from the Olist archive used for this lab. **History** is the number of sellers with at least five purchases in the 90 days before the scoring date. **Mature label** is the number of seller-months with at least five eligible completed deliveries in the promised-delivery month, after its 30-day follow-up. **Evaluation** is their intersection; only these rows are scored and evaluated.

| Promised month | History | Mature label | Evaluation | Positives | Positive rate |
| --- | ---: | ---: | ---: | ---: | ---: |
| 2017-04 | 246 | 112 | 110 | 5 | 4.5% |
| 2017-05 | 304 | 159 | 152 | 13 | 8.6% |
| 2017-06 | 356 | 193 | 189 | 8 | 4.2% |
| 2017-07 | 354 | 171 | 165 | 7 | 4.2% |
| 2017-08 | 384 | 208 | 200 | 4 | 2.0% |
| 2017-09 | 422 | 225 | 223 | 10 | 4.5% |
| 2017-10 | 450 | 212 | 207 | 13 | 6.3% |
| 2017-11 | 489 | 230 | 220 | 14 | 6.4% |
| 2017-12 | 563 | 327 | 325 | 72 | 22.2% |
| 2018-03 (validation) | 653 | 398 | 385 | 131 | 34.0% |
| 2018-04 (validation) | 694 | 330 | 315 | 107 | 34.0% |
| 2018-06 (test) | 749 | 226 | 222 | 30 | 13.5% |
| 2018-07 (test) | 752 | 351 | 335 | 5 | 1.5% |

The validation positive rate is **238 / 700 = 34.0%**, while the held-out rate is **35 / 557 = 6.3%**. This is a substantial prevalence shift, driven especially by the change from 30 June positives to five July positives. It is why raw alert rates cannot be compared across the periods without also reporting the review capacity and captured positives.

The two eligibility rules answer different questions. A seller can have enough recent purchases to be scored but not five completed, usable deliveries due in the target month; such a seller has no label for this task. Conversely, a seller-month can have a mature delivery label but lack the required purchase history. The label further excludes cancellations, undelivered orders, missing actual delivery dates, and deliveries recorded after the 30-day follow-up. These exclusions keep the observed outcome definition consistent, but reduce coverage and mean the results apply to this completed-delivery cohort rather than every marketplace order.

## Validation comparison

| Candidate | Average precision |
| --- | ---: |
| Trailing late-rate rule | 0.452 |
| Logistic regression, fulfilment features | 0.481 |
| Logistic regression, with product mix and reviews | 0.492 |
| Random forest, fulfilment features | 0.502 |
| Random forest, with product mix and reviews | **0.510** |

The random forest with product mix and reviews was selected on validation average precision. The positive rate was 34.0% over 700 validation seller-months.

## Held-out test

| Candidate | Average precision | Precision | Recall | Review rate |
| --- | ---: | ---: | ---: | ---: |
| Selected random forest | 0.092 | 7.3% | 11.4% | 9.9% |
| Trailing late-rate rule | 0.084 | 9.0% | 48.6% | 33.9% |

There were **35 positives across 557 test seller-months**. The positive rate was 6.3%, down from 34.0% in validation. The model improves ranking slightly over the rule on this holdout. Precision and recall in the table reflect different review volumes because each candidate uses its own validation cutoff. In particular, the selected model caught four of the 35 positives at its review cutoff. These results support a lab demonstration. The matched-budget results below compare both rankings at the same review volume.

## Matched monthly review budgets

Each ranking gets the same number of review slots in each month. The table pools the counts across June and July 2018. Budgets are rounded up separately by month.

| Nominal monthly budget | Reviews per ranking | Model positives captured | Rule positives captured | Model precision | Rule precision | Model recall | Rule recall |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 10% | 57 | 4 | 2 | 7.0% | 3.5% | 11.4% | 5.7% |
| 25% | 140 | 14 | 10 | 10.0% | 7.1% | 40.0% | 28.6% |

At the 25% budget, the model found 13 of June's 30 positives and one of July's five. The rule found ten in June and zero in July. The model captured more positives at both review budgets on this holdout. The gain is based on two months with very different positive rates. More chronological backtests are needed to check whether it persists.

## Model update with fulfilment context

The updated model uses orders already placed by the scoring date and due in the target month. It adds the proportion already delivered, days to the estimated delivery date and the age of orders without a recorded delivery. It also uses smoothed seller late rates, marketplace performance and recently overdue orders.

### Expanding window checks

Five development folds cover December 2017 through April 2018. Each fold trains on earlier outcomes that had fully matured by its scoring date. The table uses average precision averaged across months. Counts pool predictions at the same monthly review budgets.

| Ranking | Mean monthly average precision | Positives in 161 reviews | Positives in 399 reviews |
| --- | ---: | ---: | ---: |
| Trailing late-rate rule | 0.311 | 66 | 134 |
| Original random forest | 0.382 | 73 | 156 |
| Logistic regression with known orders | 0.434 | 81 | 171 |
| Random forest with known orders | 0.449 | 82 | 170 |
| Random forest with fulfilment context | 0.448 | 85 | 171 |

### Comparison on the original holdout

We retained the original training, validation and test months. The model with fulfilment context had the highest average precision on the fixed validation split and was selected before comparing its test scores. This reuses the two previously reported test months.

| Ranking | Average precision | Positives in 57 reviews | Positives in 140 reviews |
| --- | ---: | ---: | ---: |
| Trailing late-rate rule | 0.084 | 2 | 10 |
| Original random forest | 0.092 | 4 | 14 |
| Random forest with fulfilment context | 0.150 | 7 | 14 |

The gain is concentrated in the smaller review queue. At its own validation-derived cutoff, the updated model captured 12 of 35 positives with 58 reviews. The short historical holdout and shifts in monthly prevalence limit what this establishes about future performance.

## Frozen presentation run (2026-11-27)

The presentation artifacts were regenerated together from source commit `466c599da9f92e0820e4e4f1db2b4a90992651a0` with Python 3.10.12. Run `python -m merchant_risk train` followed by `python -m merchant_risk backtest` from the same environment to reproduce them. The selected model is `random_forest/with_fulfilment_context`.

| Split | Seller-months | Positives | Positive rate |
| --- | ---: | ---: | ---: |
| Train (2017-04 to 2017-12) | 1,791 | 146 | 8.2% |
| Validation (2018-03 to 2018-04) | 700 | 238 | 34.0% |
| Test (2018-06 to 2018-07) | 557 | 35 | 6.3% |

On the held-out test, the selected model has average precision **0.150**, Brier score **0.061**, and at its validation-derived action cutoff reviews 10.4% of seller-months with 20.7% precision and 34.3% recall. The following is the fair, matched-capacity comparison used in the presentation.

| Monthly budget | Ranking | Reviews | Positives captured | Precision | Recall |
| --- | --- | ---: | ---: | ---: | ---: |
| 10% | Fulfilment-context random forest | 57 | 7 | 12.3% | 20.0% |
| 10% | Trailing late-rate rule | 57 | 2 | 3.5% | 5.7% |
| 10% | Original random forest | 57 | 4 | 7.0% | 11.4% |
| 25% | Fulfilment-context random forest | 140 | 14 | 10.0% | 40.0% |
| 25% | Trailing late-rate rule | 140 | 10 | 7.1% | 28.6% |
| 25% | Original random forest | 140 | 14 | 10.0% | 40.0% |

The same run produced `artifacts/metrics.json`, `artifacts/backtest_metrics.json`, `artifacts/test_scores.csv`, and `artifacts/model.joblib`. Keep these files together when handing off to the dashboard: the queue and model are deliberately generated in one run.

## What the comparisons say about the features

The development folds show that timing and fulfilment context carry useful signal. The trailing 90-day late-rate rule reaches mean monthly average precision of 0.311; the original random forest, which combines recent order and delivery timing with product mix and reviews, reaches 0.382. Adding orders already known at the scoring date raises that figure to 0.448 for the random forest. The fuller fulfilment-context model ties that average precision but captures the most positives in the smaller matched review queue (85 in 161 reviews, versus 82 for known orders alone).

The fixed validation split selected the fulfilment-context forest before the June--July holdout was compared. On that historical benchmark it improves average precision from 0.092 for the original forest to 0.150, and finds seven rather than four positives in the 57-slot queue. Product mix and review features remain part of the selected feature set, but these aggregate comparisons do not establish that any one category or review feature is independently causal. Any further feature selection must use development folds only; June--July remains a historical benchmark.
