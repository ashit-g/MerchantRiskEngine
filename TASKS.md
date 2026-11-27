# MerchantRiskEngine lab task plan

**Member 1 owns the data, model and evaluation evidence. Member 2 owns the dashboard, presentation and live demo.** Both members verify the final run and rehearse their handoff.

The lab predicts whether at least 20% of a seller's eligible Olist deliveries will arrive late in the next expected-delivery month. The assessment uses observed delivery outcomes.

## Completed

- [x] **Member 1** — Joined the Olist files, built features using information available by each scoring date, and trained and compared the candidate models.
- [x] **Member 1** — Ran five chronological development backtests and evaluated the updated random forest, original random forest and trailing late-rate rule at matched review budgets.
- [x] **Member 2** — Built the Streamlit lab overview and seller explorer, including review-budget controls, seller history, product drill-down and score drivers.
- [x] **Member 2** — Documented a confirmed alert and a false alarm for the June 2018 demo.

## Member 1 — Data and model evaluation

- [x] **Audit coverage and class balance**. `docs/results.md` explains the monthly counts of sellers with enough history, sellers with a mature label, and their overlap. Quantify the change in positive rates from validation to test and explain the delivery and follow-up exclusions.
- [x] **Summarise which features helped**. Document what the existing comparisons show about order timing, fulfilment context, product mix and reviews. Use development folds for any additional feature selection. Keep the June–July 2018 results as the existing historical benchmark.
- [x] **Freeze the presentation results**. Run `python -m merchant_risk train` and `python -m merchant_risk backtest`. Record the commit, selected model, split sizes and exact 10% and 25% results. Share `metrics.json`, `test_scores.csv` and `model.joblib` from the same run locally, or give Member 2 the commands to regenerate them.
- [x] **Prepare the technical explanation**. Be ready to explain the seller-month label, how historical features avoid future delivery information, chronological splits and why matched review budgets matter. Cover the short test period and the assumption that Olist's estimated delivery date was available when the order was placed.

## Member 2 — Dashboard and presentation

- [x] **Check the dashboard against the final run**. Verified the README installation and local launch, both budget selections, and both demo sellers' score and action against the CLI. The [dashboard verifier](scripts/verify_dashboard.py) reproduces these checks using `python -m scripts.verify_dashboard`. See the [verification record](docs/member2-validation.md).
- [x] **Prepare and verify the two seller walkthroughs**. Checked the June confirmed alert `de23c3b98a88888289c6f5cc1209054a` and false alarm `2c9e548be18521d1c43cde1c582c6de8` against the saved queue, CLI and live dashboard. The [demo guide](docs/demo-guide.md) explains the forecast, historical evidence and later outcome, with exact navigation and commands. The two-person rehearsal remains in joint sign-off below.
- [x] **Prepare the lab presentation and fallback**. Created an [11-slide deck](docs/presentation/MerchantRiskEngine_ML_Lab.pptx), [Markdown outline with speaker notes and viva preparation](docs/presentation.md), and [screenshots](docs/presentation/screenshots/) covering both overview budgets and both seller cases. The deck covers the problem, data, target, model, evaluation, demo and limitations. Member 1's peer review remains in joint sign-off below.
- [x] **Check local presentation setup**. Started the dashboard on this machine, inspected 1440×1000 and 1366×768 layouts, exercised filters, tabs and drill-down modes, and verified missing-input recovery in isolated app copies. See the [verification record](docs/member2-validation.md) for scope. Actual classroom projection remains in joint sign-off below.

## Handoff and joint sign-off

- [x] **Member 1 → Member 2** — Frozen evaluation source, commands, split counts and exact results are documented in [results](docs/results.md#frozen-presentation-run-2026-11-27). Local artifacts used by the dashboard are identified in the [verification record](docs/member2-validation.md#artifact-identity).
- [x] **Member 2 → Member 1** — Prepared the [presentation](docs/presentation.md) and [checked demo sequence](docs/demo-guide.md). Dashboard, CLI and queue values agree for both cases. Refreshed the README's confirmed-alert score to the current local 36.5%.
- [ ] **Member 1 peer review** — Review the presentation's model explanation, limitations and numbers against the frozen run.
- [ ] **Both, rehearsal** — Verify the project from a clean checkout, run the tests and rehearse once. Member 1 presents data, modelling and evaluation. Member 2 presents the dashboard, seller examples and review workflow.
- [ ] **Both, classroom check** — Confirm projector readability and the slide deck in the chosen presentation software on the evaluation setup.

Use separate branches for concurrent work. Commit source code, Markdown and the presentation deck/screenshots to GitHub so both members can use the demo fallback. Keep raw Olist files, model artifacts and temporary build outputs local.

## Optional after the demo is ready

- **Member 1** can evaluate SHAP explanations or mine Apriori warning patterns on the development data. Document support, confidence and lift for any rules presented.
- **Member 2** can add a dashboard view for an explanation or warning pattern after Member 1 verifies it. Keep the existing score drivers and seller walkthrough as the demo baseline.
