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

There were **35 positives across 557 test seller-months**. The positive rate was 6.3%, down from 34.0% in validation. The model improves ranking slightly over the rule on this holdout. Precision and recall in the table reflect different review volumes because each candidate uses its own validation cutoff. In particular, the selected model caught four of the 35 positives at its review cutoff. These results support a lab demonstration. Estimating operational value would need more time windows and a comparison at a common review budget.
