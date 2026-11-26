# MerchantRiskEngine lab task plan

**Member 1 owns the data, model and evaluation evidence. Member 2 owns the dashboard, presentation and live demo.** Both members verify the final run and rehearse their handoff.

The lab predicts whether at least 20% of a seller's eligible Olist deliveries will arrive late in the next expected-delivery month. The assessment uses observed delivery outcomes.

## Completed

- [x] **Member 1** — Joined the Olist files, built features using information available by each scoring date, and trained and compared the candidate models.
- [x] **Member 1** — Ran five chronological development backtests and evaluated the updated random forest, original random forest and trailing late-rate rule at matched review budgets.
- [x] **Member 2** — Built the Streamlit lab overview and seller explorer, including review-budget controls, seller history, product drill-down and score drivers.
- [x] **Member 2** — Documented a confirmed alert and a false alarm for the June 2018 demo.

## Member 1 — Data and model evaluation

- [ ] **Audit coverage and class balance**. `docs/results.md` explains the monthly counts of sellers with enough history, sellers with a mature label, and their overlap. Quantify the change in positive rates from validation to test and explain the delivery and follow-up exclusions.
- [ ] **Summarise which features helped**. Document what the existing comparisons show about order timing, fulfilment context, product mix and reviews. Use development folds for any additional feature selection. Keep the June–July 2018 results as the existing historical benchmark.
- [ ] **Freeze the presentation results**. Run `python -m merchant_risk train` and `python -m merchant_risk backtest`. Record the commit, selected model, split sizes and exact 10% and 25% results. Share `metrics.json`, `test_scores.csv` and `model.joblib` from the same run locally, or give Member 2 the commands to regenerate them.
- [ ] **Prepare the technical explanation**. Be ready to explain the seller-month label, how historical features avoid future delivery information, chronological splits and why matched review budgets matter. Cover the short test period and the assumption that Olist's estimated delivery date was available when the order was placed.

## Member 2 — Dashboard and presentation

- [ ] **Check the dashboard against the final run**. Install and launch from the [README](README.md#run-the-streamlit-dashboard). Verify both budget selections against Member 1's metrics and match at least one dashboard seller score and review tier to the CLI output for the same date.
- [ ] **Rehearse the two seller examples**. In June 2018, use `de23c3b98a88` for a confirmed alert and `2c9e548be185` for a false alarm from the current run. Verify both against the final export. Explain the forecast, the seller's history at scoring time, and the outcome observed later.
- [ ] **Prepare the lab presentation**. Arrange the story around the problem, data, model, results, live seller demo and limitations. Have Member 1 review the numbers and wording. Save screenshots of the lab overview and both seller examples as a fallback for the live demo.
- [ ] **Check the classroom setup**. Start the dashboard on the presentation machine. Check text and chart legibility at the planned display size, try the filters and tabs, and confirm that the missing-artifact message gives a usable recovery step.

## Handoff and joint sign-off

1. **Member 1 → Member 2** — Share the evaluation commit, run commands, exact results and the model and queue from a single run.
2. **Member 2 → Member 1** — Share the presentation outline and checked demo sequence. Flag any differences between the dashboard, CLI and reported numbers.
3. **Both** — Verify the project from a clean checkout, run the tests and rehearse once. Member 1 presents the data, model and evaluation. Member 2 presents the dashboard, seller examples and review workflow.

Use separate branches for concurrent work. Commit source code and Markdown to GitHub. Keep raw Olist files and generated artifacts local.

## Optional after the demo is ready

- **Member 1** can evaluate SHAP explanations or mine Apriori warning patterns on the development data. Document support, confidence and lift for any rules presented.
- **Member 2** can add a dashboard view for an explanation or warning pattern after Member 1 verifies it. Keep the existing score drivers and seller walkthrough as the demo baseline.
