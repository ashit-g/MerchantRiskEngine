# Lab demo guide

## Setup

Run these commands from the repository root using Python 3.10–3.12. The [data guide](data.md) lists the required Olist files. Keep the model, metrics and score export from one training run together.

```sh
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python -m merchant_risk train
python -m unittest discover -s tests -v
python -m scripts.verify_dashboard
python -m streamlit run dashboard.py --server.address 127.0.0.1
```

Open [the dashboard](http://localhost:8501). Existing matching artifacts can be reused. The verification command uses the saved run and writes its evidence to `artifacts/member2-verification.json`.

## Two-minute walkthrough

1. Present the evaluation using the [slide notes](presentation.md#7-results-at-equal-review-capacity). Explain the seller-month target and compare the models at the same review capacity.
2. Open the dashboard, select **June 2018** and keep **All actions**. Search **Find merchant by ID** for `de23c3b98a88`. Explain the confirmed alert, then show **Delivery trend**, **Product breakdown** and **Score drivers**. The **Category / Product** control is inside **Product breakdown**.
3. Select `2c9e548be185` and explain the false alarm below. Show how category counts inform an operations review, then demonstrate recording a decision.
4. Close with the short evaluation period, prevalence shift and completed-delivery coverage.

The slides compare rankings at a fixed monthly review capacity. The dashboard assigns suggested actions using fixed validation-derived score thresholds, so its tier counts can differ from the slide budgets.

## Confirmed alert

Seller `de23c3b98a88888289c6f5cc1209054a` is scored on **31 May 2018** for **June 2018**.

| Item | Verified local value |
| --- | --- |
| Forecast | 36.5% chance of the high-late-rate seller-month outcome |
| Suggested action | Investigate category |
| Past 30-day completed deliveries | Seven, with zero late |
| Historical category mix | Stationery four deliveries, toys three |
| Outcome observed later | Two late among six eligible June deliveries, or 33.3% |
| June outcome label | Positive |

Say, “At the end of May, this seller had no late deliveries in its recent completed-delivery history. The model also uses orders already placed and due next month. None of those known next-month orders had been delivered by scoring time. Replacing that input with its training median reduces this forecast by 18.4 percentage points. We later observe two late deliveries out of six.”

The 36.5% forecast concerns the seller-month event. The 33.3% observed rate is the fraction of eligible deliveries that arrived late. The score-driver comparison describes sensitivity to one input replacement. Causal interpretation requires additional evidence.

```sh
python -m merchant_risk score --seller-id de23c3b98a88888289c6f5cc1209054a --as-of 2018-05-31
```

## False alarm

Seller `2c9e548be18521d1c43cde1c582c6de8` has the same scoring date and target month.

| Item | Verified local value |
| --- | --- |
| Forecast | 44.8% |
| Suggested action | Escalate for operations review |
| Past 30-day completed deliveries | 17, with five late, or 29.4% |
| Stationery | Three late among 13 deliveries, contributing 60% of recent late deliveries |
| Toys | Two late among four deliveries, contributing 40% of recent late deliveries |
| Outcome observed later | Zero late among eight eligible June deliveries |
| June outcome label | Negative |

Say, “This seller has the highest June score. Recent history contains five late deliveries, so the queue prioritises an operations review. Stationery contributes more late deliveries, while toys has a higher late rate on fewer deliveries. All eight eligible June deliveries subsequently arrive on time. This is a false alarm under the action threshold and illustrates the cost of reviewing uncertain forecasts.”

```sh
python -m merchant_risk score --seller-id 2c9e548be18521d1c43cde1c582c6de8 --as-of 2018-05-31 --group-by product_id
```

## Offline fallback

Use the [local slide deck](presentation/MerchantRiskEngine_ML_Lab.pptx) and the following screenshots when the dashboard is unavailable. The slides include speaker notes. The [Markdown presentation](presentation.md) is editable in the repository.

- [Confirmed alert](presentation/screenshots/seller-confirmed-alert.png)
- [False alarm](presentation/screenshots/seller-false-alarm.png)
- [Score drivers](presentation/screenshots/seller-score-drivers.png)

The screenshots record the verified local run on 27 November 2026. Regenerated models can produce slightly different scores across supported Python and numerical-library versions. Rerun verification and refresh the examples whenever the saved model changes.

## Recovery during setup

| Symptom | Recovery |
| --- | --- |
| Missing Olist inputs | Extract the required CSVs into `data/olist/`, following the [data guide](data.md) |
| Missing metrics, model or queue | Run `python -m merchant_risk train` from the repository root |
| Model and queue disagree | Regenerate them together with the training command, then restart Streamlit |
| Port already in use | Reuse the existing dashboard or launch with `--server.port 8502` and open that port |
| A stale process still uses earlier source | Stop the server with Ctrl+C and start it again |
| Live demo unavailable | Open the saved deck and screenshots |

## Joint rehearsal

- Member 1 reviews the target, evaluation numbers and model wording against the [results](results.md).
- Member 2 follows the sequence above with the final model and screenshots.
- Both members check a clean checkout with the locally supplied dataset and regenerated artifacts.
- Check the actual classroom projector, browser zoom and back-row readability together. The local browser checks cover 1440×1000 and 1366×768 viewports.
