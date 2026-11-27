# MerchantRiskEngine lab presentation

The [slide deck](presentation/MerchantRiskEngine_ML_Lab.pptx) follows this outline. Allow approximately eight minutes, including the two-minute demo. The [demo guide](demo-guide.md) provides exact clicks, CLI commands, screenshots and recovery steps. Member 1 should review the technical wording and frozen results before the joint rehearsal.

## 1. MerchantRiskEngine

**Member 2 · 20 seconds**

Seller fulfilment risk forecasting using Olist marketplace data. Team Casevocate, Machine Learning Lab.

Explain the operations user who needs to decide which sellers to review next month. The project combines a predictive model with historical delivery evidence and a product/category investigation view.

## 2. Operations review problem

**Member 2 · 30 seconds**

Recent delays, changes in order volume, customer feedback and the status of already-placed orders can help prioritise seller reviews. The dashboard ranks sellers, exposes historical evidence and suggests a review tier.

The product flow is historical transactions and feedback → monthly features → seller risk forecast → product investigation → human operations review. Product and category views describe each seller's observed delivery history.

## 3. Prediction target

**Member 1 · 40 seconds**

- One observation is a seller-month.
- Score at the end of the preceding month.
- Assign deliveries to the month of their promised delivery date.
- Require at least five eligible completed deliveries for an outcome.
- Label positive when at least 20% arrive after their promised calendar date.
- Observe outcomes through the target month-end plus 30 days.

Use June as the worked example. Features stop on 31 May. Outcomes belong to June and receive follow-up through 30 July. Two late deliveries among six give a 33.3% late rate and a positive label. A forecast score estimates the chance of that seller-month event.

## 4. Data and eligibility

**Member 1 · 35 seconds**

Olist orders provide purchase, promised and actual delivery dates. Items link orders to sellers and products. Products provide category information. Reviews provide feedback and response timestamps. Optional category translations support English labels.

Use single-seller orders. Scoring requires at least five purchases in the trailing 90 days. Evaluation also requires a mature outcome label. Cancellations, undelivered orders and deliveries after the follow-up are outside the completed-delivery outcome. The [data guide](data.md) documents the exclusions and category assignment.

## 5. Chronological evaluation

**Member 1 · 40 seconds**

| Split | Promised-delivery months | Seller-months | Positives |
| --- | --- | ---: | ---: |
| Training | Apr–Dec 2017 | 1,791 | 146 |
| Validation | Mar–Apr 2018 | 700 | 238 |
| Historical test | Jun–Jul 2018 | 557 | 35 |

Gaps allow preceding labels to mature. Fit preprocessing and estimators on training data. Select the configuration using validation average precision. Five expanding development folds cover December 2017 through April 2018. The June–July test period has already been reused during model development and remains a historical benchmark.

## 6. Features and learning algorithm

**Member 1 · 40 seconds**

Use rolling 7-, 30- and 90-day activity and delivery rates, product mix, customer feedback, smoothed seller rates, marketplace context and already-placed orders due next month. Features use event timestamps available by scoring time. A delivery or review recorded later stays outside those historical features.

Compare logistic regression and random forest variants with a trailing 90-day late-rate rule. The selected fulfilment-context random forest uses 250 trees, a minimum leaf size of ten and random seed 42. Training-fitted median imputation handles missing values. The [methodology](methodology.md) gives the full modelling protocol.

## 7. Results at equal review capacity

**Member 1 · 45 seconds**

| Monthly budget | Total reviews | Updated forest caught | Original forest caught | Late-rate rule caught |
| --- | ---: | ---: | ---: | ---: |
| 10% | 57 | 7 | 4 | 2 |
| 25% | 140 | 14 | 14 | 10 |

**Slide takeaway.** The fulfilment-context random forest captured **7 of 35 positives in 57 reviews**, compared with **4** for the original forest and **2** for the trailing late-rate rule. At 140 reviews, both forests captured 14.

| Ranking | Average precision | Precision at 10% | Recall at 10% | Precision at 25% | Recall at 25% |
| --- | ---: | ---: | ---: | ---: | ---: |
| Fulfilment-context random forest | 0.150 | 12.3% | 20.0% | 10.0% | 40.0% |
| Original random forest | 0.092 | 7.0% | 11.4% | 10.0% | 40.0% |
| Trailing 90-day late-rate rule | 0.084 | 3.5% | 5.7% | 7.1% | 28.6% |

**Speaker notes.** The June–July 2018 historical test contains 557 seller-months and 35 positives (6.3%). Average precision summarises precision across the ranking as recall increases. At the separate validation-derived action cutoff, the updated forest flagged 58 cases and captured 12 positives, yielding 20.7% precision and 34.3% recall. Brier score was 0.061. Report these cutoff results separately from the matched-capacity comparison.

Review slots are rounded up separately each month. Fixed action tiers use validation-derived thresholds and have different review volumes. The [results](results.md) include development-fold results and the full frozen evaluation.

## 8. Confirmed alert

**Member 2 · included in live demo**

Seller `de23c3b98a88888289c6f5cc1209054a`, scored 31 May for June. Forecast 36.5%, suggested action Investigate category. Recent completed-delivery history is zero late among seven. Later, two of six eligible June deliveries are late. Already-placed orders contribute information beyond completed-delivery history. The [demo guide](demo-guide.md#confirmed-alert) gives the score-driver explanation.

## 9. False alarm

**Member 2 · included in live demo**

Seller `2c9e548be18521d1c43cde1c582c6de8`, same scoring date and target month. Forecast 44.8%, suggested action Escalate for operations review. Recent history has five late among 17. Stationery contributes three late deliveries and toys two. Later, all eight eligible June deliveries arrive on time. Discuss review cost and forecast uncertainty.

## 10. Dashboard walkthrough

**Member 2 · two minutes including the seller examples**

Present the matched-budget comparison on slide 7. Open the merchant review dashboard for June, inspect the confirmed alert and false alarm, switch category/product grouping, and visit all three tabs. Clearly identify the scoring date, target month, historical window and later-observed outcome.

The score drivers replace individual inputs with their training medians. Interpret them as model sensitivity. Product drill-down attributes observed late deliveries to categories or representative products. A human reviewer can use these signals to choose a follow-up investigation.

## 11. Limitations and conclusion

**Both · 45 seconds**

- Only two historical test months, with 30 positives in June and five in July.
- Validation prevalence is 34.0%, compared with 6.3% in the test period.
- Completed-delivery eligibility and history requirements limit coverage.
- Estimated delivery dates are assumed known at purchase. Revision history is unavailable.
- Score sensitivity and category breakdowns support interpretation. Causal interpretation requires additional evidence.
- Consumer repayment outcomes, verified returns and financing losses are unavailable in these data.

Conclude that the lab demonstrates monthly seller risk ranking and an inspectable operations workflow on observed marketplace delivery outcomes. Further generalisation requires additional chronological evidence.

## Viva preparation

| Question | Answer |
| --- | --- |
| Why score the merchant? | The target aggregates a seller's delivery reliability. Operations teams can prioritise seller and product investigations. |
| What does a 36.5% score mean? | The estimated chance that the seller-month meets the high-late-rate outcome definition. |
| Why use average precision? | Positive seller-months are uncommon in the historical test period. Ranking quality and captured positives at a fixed review capacity directly describe the review workflow. |
| Why chronological splits? | They reflect forecasting later months and allow training labels to mature before subsequent scoring. |
| What prevents future information entering features? | Each historical event is restricted by its observable timestamp, and regression tests cover events after the scoring cutoff. |
| Can the same seller appear in different splits? | Yes. The task evaluates future months for marketplace sellers with sufficient history. Unseen-seller generalisation needs a separate evaluation. |
| Is the product view a separate product model? | It aggregates observed historical delivery outcomes using a representative product/category per order. The learned forecast is at seller-month level. |
| Does 30-day follow-up mean 30 days overdue? | It is the observation window after month-end. A completed delivery counts as late when its calendar delivery date exceeds its promised date. |
| Does a high score guarantee a bad month? | The false-alarm example shows the uncertainty. Review tiers prioritise follow-up using validation-derived score thresholds. |
