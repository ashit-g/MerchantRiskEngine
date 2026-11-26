"""Compare model variants across development months with matured labels only."""

import json
from pathlib import Path

import pandas as pd
from sklearn.base import clone
from sklearn.metrics import average_precision_score

from .features import KNOWN_NEXT_MONTH_FEATURES, TARGET, maturity_date, month_end
from .model import CONTEXT_FEATURES, HISTORICAL_FEATURES, RULE_FEATURE, build_month, candidate_models
from .review_budget import compare_review_budgets


def run_backtest(orders: pd.DataFrame, reviews: pd.DataFrame, output_dir: Path) -> dict:
    observed_through = orders["purchased"].max()
    months = pd.period_range("2017-04", "2018-04", freq="M")
    frames = {month: build_month(orders, reviews, month, observed_through)[0] for month in months}
    models = candidate_models()
    candidates = {
        "previous_random_forest": (models["random_forest"], HISTORICAL_FEATURES),
        "logistic_regression_with_known_orders": (
            models["logistic_regression"], HISTORICAL_FEATURES + KNOWN_NEXT_MONTH_FEATURES,
        ),
        "random_forest_with_known_orders": (
            models["random_forest"], HISTORICAL_FEATURES + KNOWN_NEXT_MONTH_FEATURES,
        ),
        "random_forest_with_fulfilment_context": (models["random_forest"], CONTEXT_FEATURES),
    }
    rankings = ("trailing_late_rate", *candidates)
    fold_results = {}
    fold_scores = []
    for month in pd.period_range("2017-12", "2018-04", freq="M"):
        cutoff = month_end(month - 1)
        train_months = [earlier for earlier in months if maturity_date(earlier) < cutoff]
        train = pd.concat([frames[earlier] for earlier in train_months], ignore_index=True)
        validation = frames[month]
        evaluated = validation[["seller_id", "target_month", TARGET]].assign(
            trailing_late_rate=validation[RULE_FEATURE].fillna(train[RULE_FEATURE].median()).fillna(0),
        )
        for name, (estimator, columns) in candidates.items():
            fitted = clone(estimator).fit(train[columns], train[TARGET])
            evaluated[name] = fitted.predict_proba(validation[columns])[:, 1]
        fold_results[str(month)] = {
            "scoring_date": cutoff.date().isoformat(),
            "last_training_target_month": str(train_months[-1]),
            "seller_months": len(validation),
            "positives": int(validation[TARGET].sum()),
            "average_precision": {
                name: float(average_precision_score(evaluated[TARGET], evaluated[name])) for name in rankings
            },
        }
        fold_scores.append(evaluated)

    report = {
        "folds": fold_results,
        "mean_monthly_average_precision": {
            name: sum(fold["average_precision"][name] for fold in fold_results.values()) / len(fold_results)
            for name in rankings
        },
        "matched_review_budgets": compare_review_budgets(pd.concat(fold_scores, ignore_index=True), rankings),
    }
    output_dir.mkdir(parents=True, exist_ok=True)
    (output_dir / "backtest_metrics.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    return report
