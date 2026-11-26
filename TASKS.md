# MerchantRiskEngine task plan

This plan divides the remaining lab work between two teammates. Use the role labels below until the team assigns names. The current target is a seller-month with at least 20% late deliveries among eligible Olist orders due the following month.

## Completed foundation

- [x] Join Olist orders, items, reviews and products and build historical seller features.
- [x] Train and compare logistic regression, random forest and a trailing late-rate rule.
- [x] Score an individual seller and provide category and product drill-downs through the CLI.
- [x] Compare the model and rule at equal monthly review budgets and document the June–July 2018 results.

## Teammate 1 — Data and model evaluation

- [ ] **Audit evaluation coverage and drift.** Use monthly counts to show how seller coverage, positive rates and order volumes change over time. Describe how many sellers are excluded by the historical volume and target follow-up rules. Deliver a short table in `docs/results.md`.
- [x] **Run chronological backtests.** Compared model variants across five development months with matured labels and matched monthly review budgets. The results are in `docs/results.md`.
- [ ] **Evaluate feature groups.** Quantify what product mix and review signals add beyond historical fulfilment and order volume. If they help only in some months, record those differences.
- [ ] **Provide model outputs for the demo.** Share a runnable model and documented output schema, plus two historical seller IDs and scoring dates for the demo. Include at least one alert with a clear category drill-down and one low-risk example. Keep raw data and model artifacts local.

## Teammate 2 — Product experience and explanation

- [x] **Build the dashboard.** Added month, tier and seller filters, the forecast, historical delivery trends, and product or category drill-down.
- [x] **Make the alert explainable.** Displayed plain-language feature comparisons and periods, plus the category contribution to recent delays.
- [ ] **Evaluate SHAP and a warning-pattern view if time permits.** Use Apriori on historical signals in the development period. Show support, confidence and lift if the rules have enough examples to be worth presenting.
- [ ] **Prepare and run the demo.** Document setup, expected outputs, and empty states for sellers with insufficient history. Rehearse the two examples and explain the difference between a forward seller score and a historical product drill-down.

## Handoffs and submission

1. Teammate 2 can refine the dashboard against the current outputs. Coordinate any model-output schema changes before updating the dashboard.
2. Teammate 1 shares backtest results, the chosen model and demo inputs. Teammate 2 verifies that the dashboard matches the same seller/date outputs from the CLI.
3. Both teammates run the project from a clean checkout, review each other's changes, and agree on the results and limitations to present. Use separate Git branches for the evaluation and dashboard work.
