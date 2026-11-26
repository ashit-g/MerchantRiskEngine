# Initial Olist results

The first run uses observed late deliveries and one row per eligible seller-month. Reproduce it with `python -m merchant_risk train`. The generated `artifacts/metrics.json` has the full breakdown.

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
| Random forest with known orders | 0.448 | 82 | 170 |
| Random forest with fulfilment context | 0.448 | 85 | 171 |

### Comparison on the original holdout

We retained the original training, validation and test months. The model with fulfilment context had the highest average precision on the fixed validation split and was selected before comparing its test scores. This reuses the two previously reported test months.

| Ranking | Average precision | Positives in 57 reviews | Positives in 140 reviews |
| --- | ---: | ---: | ---: |
| Trailing late-rate rule | 0.084 | 2 | 10 |
| Original random forest | 0.092 | 4 | 14 |
| Random forest with fulfilment context | 0.150 | 7 | 14 |

The gain is concentrated in the smaller review queue. At its own validation-derived cutoff, the updated model captured 12 of 35 positives with 58 reviews. The short historical holdout and shifts in monthly prevalence limit what this establishes about future performance.
