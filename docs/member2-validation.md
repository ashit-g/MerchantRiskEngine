# Member 2 verification record

Verified locally on **27 November 2026** against source baseline `cbdc275daf2454bba3af179dfccf38e4945c9cd1` and the existing evaluation artifacts. The [frozen results](results.md#frozen-presentation-run-2026-11-27) identify Member 1's evaluation source. This dashboard verification used Python 3.12.14, scikit-learn 1.7.2, pandas 2.3.3, Streamlit 1.52.2 and Plotly 6.5.0.

## Delivered

- [Eleven-slide PowerPoint deck](presentation/MerchantRiskEngine_ML_Lab.pptx) with speaker notes and six editable tables.
- [Markdown presentation](presentation.md) with roles, timing and viva answers.
- [Checked demo guide](demo-guide.md) with two seller examples and setup recovery.
- [Dashboard screenshots](presentation/screenshots/) for offline use.
- [Repeatable dashboard verifier](../scripts/verify_dashboard.py), invoked as `python -m scripts.verify_dashboard`.

The presentation service failed before authoring the deck, so the delivered deck is a local PowerPoint file. Every slide was rendered and visually inspected. Package integrity, slide geometry, font policy and reimport checks passed with zero findings. Native PowerPoint execution remains part of the presentation-machine rehearsal.

## Checks performed

| Check | Result |
| --- | --- |
| README dashboard installation | `python -m pip install -r requirements-dashboard.txt` succeeded with the existing pinned dependencies |
| Dependency consistency | `python -m pip check` passed |
| Existing unit tests | Seven passed |
| Local server | Launched at `http://127.0.0.1:8501` |
| Overview summary | 557 seller-months, 35 positives, average precision 0.150 |
| 10% budget | 57 reviews, updated forest seven positives, original forest four, rule two |
| 25% budget | 140 reviews, updated forest 14 positives, original forest 14, rule ten |
| Budget arithmetic | Recomputed selected-model and rule counts from the score export, allocating capacity separately by month |
| Exact-results table | Selected-model counts match the saved report at both budgets |
| Seller forecast and action | Both demo sellers match CLI output and the saved queue, score tolerance 1e-9 |
| Seller history | Dashboard completed-delivery counts reconcile with CLI category totals |
| Filters | All eight combinations of two forecast months and four tier choices passed |
| Product views | Category and individual-product modes passed for both demo sellers |
| Tabs | All three tab contents executed without exceptions, and browser switching passed |
| Missing inputs | Isolated app copies displayed the missing report/data/model recovery messages and training command |
| Browser layout | Inspected at 1440×1000 and 1366×768, with no page-level horizontal overflow or Streamlit exceptions at 1366×768 |
| Screenshot fallback | Saved and visually inspected both review budgets, both sellers and score drivers |

The browser checks used the installed Chrome browser in headless mode. At 1366×768, the page requires vertical scrolling to inspect the full seller profile and its evidence. Table text and long product IDs may require the table's horizontal scrollbar. The projector's physical readability still needs an in-room check.

## Verified seller cases

Both forecasts use 31 May 2018 as the cutoff and June 2018 as the target month.

| Case | Seller prefix | Forecast | Action | Past 30 days | Later eligible June outcome |
| --- | --- | ---: | --- | --- | --- |
| Confirmed alert | `de23c3b98a88` | 36.5% | Investigate category | Zero late among seven | Two late among six, positive |
| False alarm | `2c9e548be185` | 44.8% | Escalate for operations review | Five late among 17 | Zero late among eight, negative |

The README's earlier 36.3% example was refreshed to the locally verified 36.5%. The [demo guide](demo-guide.md) records full IDs, exact commands, category counts and the explanation of forecast versus observed late-delivery rate.

## Artifact identity

The verification script writes its detailed output and SHA-256 hashes to `artifacts/member2-verification.json`. These identify the local run used for the deck and screenshots.

| Artifact | SHA-256 |
| --- | --- |
| `metrics.json` | `079073b7766a21389a0bacd6e0bc0ffe8f2e69c5e7d0248a45eb427fe80ad66f` |
| `test_scores.csv` | `d05d1ea82a4cdaf23a09f332e156c96c8413c9aac5e9a2fccba7c764e66266cf` |
| `model.joblib` | `54071e0852591b53077454e8d9156b4f7e2f68bf2444805c9837cb53698eb592` |
| `backtest_metrics.json` | `6787add061a8305166a1f42ac6e8a0a72a5fdb54cebf1557f23a22769fba491b` |

## Joint sign-off still required

- Member 1 reviews the presentation wording and numbers.
- Both members rehearse the speaker handoff and live walkthrough once.
- Check the actual classroom projector and open the deck in the presentation software used for evaluation.

The [task plan](../TASKS.md) keeps these human sign-off items separate from the completed implementation and local checks.
