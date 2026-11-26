import json
from pathlib import Path

import joblib
import pandas as pd
from sklearn.base import clone
from sklearn.ensemble import RandomForestClassifier
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import average_precision_score, brier_score_loss, precision_score, recall_score
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler

from .features import (
    BASE_FEATURES, EXTRA_FEATURES, FULFILMENT_CONTEXT_FEATURES, KNOWN_NEXT_MONTH_FEATURES,
    TARGET, maturity_date, month_end, monthly_outcomes,
    product_drilldown, seller_features,
)
from .review_budget import compare_review_budgets


# Periods are target (promised-delivery) months. The gaps allow labels to mature.
SPLITS = {
    "train": ("2017-04", "2017-12"),
    "validation": ("2018-03", "2018-04"),
    "test": ("2018-06", "2018-07"),
}
RULE_FEATURE = "late_rate_90d"
HISTORICAL_FEATURES = BASE_FEATURES + EXTRA_FEATURES
CONTEXT_FEATURES = HISTORICAL_FEATURES + FULFILMENT_CONTEXT_FEATURES + KNOWN_NEXT_MONTH_FEATURES
PREVIOUS_MODEL = "random_forest/with_product_mix_and_reviews"


def build_month(
    orders: pd.DataFrame, reviews: pd.DataFrame, month: pd.Period, observed_through: pd.Timestamp,
) -> tuple[pd.DataFrame, dict]:
    features = seller_features(orders, reviews, month_end(month - 1))
    outcomes = monthly_outcomes(orders, month, observed_through)
    eligible = outcomes[outcomes[TARGET].notna()]
    joined = features.merge(eligible, on="seller_id", how="inner", validate="one_to_one")
    joined["target_month"] = str(month)
    joined[TARGET] = joined[TARGET].astype(int)
    coverage = {
        "historically_eligible_sellers": len(features),
        "seller_months_with_label": len(eligible),
        "seller_months_in_evaluation": len(joined),
        "positives_in_evaluation": int(joined[TARGET].sum()),
    }
    return joined, coverage


def build_splits(orders: pd.DataFrame, reviews: pd.DataFrame) -> tuple[dict, dict]:
    splits, coverage = {}, {}
    observed_through = orders["purchased"].max()
    prior_maturity = None
    for name, (start, end) in SPLITS.items():
        months = pd.period_range(start, end, freq="M")
        first_score = month_end(months[0] - 1)
        if prior_maturity is not None and prior_maturity >= first_score:
            raise ValueError(f"Labels from the preceding split have not matured before {name} scoring.")
        rows = []
        for month in months:
            joined, coverage[str(month)] = build_month(orders, reviews, month, observed_through)
            rows.append(joined)
        frame = pd.concat(rows, ignore_index=True)
        if frame[TARGET].nunique() != 2:
            raise ValueError(f"The {name} split needs both outcome classes.")
        splits[name] = frame
        prior_maturity = maturity_date(months[-1])
    return splits, coverage


def candidate_models() -> dict:
    return {
        "logistic_regression": make_pipeline(
            SimpleImputer(strategy="median", add_indicator=True, keep_empty_features=True),
            StandardScaler(),
            LogisticRegression(max_iter=1000),
        ),
        "random_forest": make_pipeline(
            SimpleImputer(strategy="median", add_indicator=True, keep_empty_features=True),
            RandomForestClassifier(n_estimators=250, min_samples_leaf=10, random_state=42),
        ),
    }


def review_thresholds(scores) -> tuple[float, float]:
    """Use validation score percentiles as illustrative review capacity cutoffs."""
    return tuple(float(value) for value in pd.Series(scores).quantile([0.75, 0.90]))


def review_action(score: float, thresholds: tuple[float, float]) -> str:
    investigate, escalate = thresholds
    if score > escalate:
        return "Escalate for operations review"
    if score > investigate:
        return "Investigate category"
    return "Monitor"


def metrics(labels, scores, threshold: float) -> dict:
    flagged = scores > threshold
    return {
        "average_precision": float(average_precision_score(labels, scores)),
        "precision": float(precision_score(labels, flagged, zero_division=0)),
        "recall": float(recall_score(labels, flagged, zero_division=0)),
        "review_rate": float(flagged.mean()),
    }


def train_and_evaluate(orders: pd.DataFrame, reviews: pd.DataFrame, output_dir: Path) -> dict:
    splits, coverage = build_splits(orders, reviews)
    train, validation, test = (splits[key] for key in SPLITS)
    validation_labels = validation[TARGET]
    rule_median = train[RULE_FEATURE].median()
    rule_validation = validation[RULE_FEATURE].fillna(rule_median).fillna(0)
    rule_threshold, _ = review_thresholds(rule_validation)
    validation_metrics = {
        "trailing_late_rate": metrics(validation_labels, rule_validation, rule_threshold),
    }
    models = candidate_models()
    candidates = [
        (f"{name}/{feature_set}", estimator, columns)
        for name, estimator in models.items()
        for feature_set, columns in (
            ("fulfilment", BASE_FEATURES), ("with_product_mix_and_reviews", HISTORICAL_FEATURES),
        )
    ]
    candidates.append(("random_forest/with_fulfilment_context", models["random_forest"], CONTEXT_FEATURES))
    fitted = {}
    for key, estimator, columns in candidates:
        model = clone(estimator).fit(train[columns], train[TARGET])
        validation_scores = model.predict_proba(validation[columns])[:, 1]
        thresholds = review_thresholds(validation_scores)
        result = metrics(validation_labels, validation_scores, thresholds[0])
        result["brier_score"] = float(brier_score_loss(validation_labels, validation_scores))
        validation_metrics[key] = result
        fitted[key] = (model, columns, thresholds)

    best_name = max(fitted, key=lambda name: validation_metrics[name]["average_precision"])
    best_model, best_columns, best_thresholds = fitted[best_name]
    previous_model, previous_columns, previous_thresholds = fitted[PREVIOUS_MODEL]
    previous_scores = previous_model.predict_proba(test[previous_columns])[:, 1]
    test_scores = best_model.predict_proba(test[best_columns])[:, 1]
    test_rule = test[RULE_FEATURE].fillna(rule_median).fillna(0)
    model_metrics = metrics(test[TARGET], test_scores, best_thresholds[0])
    model_metrics["brier_score"] = float(brier_score_loss(test[TARGET], test_scores))
    budget_scores = test[["seller_id", "target_month", TARGET]].assign(
        selected_model=test_scores, trailing_late_rate=test_rule, previous_random_forest=previous_scores,
    )
    report = {
        "matched_review_budgets": compare_review_budgets(
            budget_scores, ("selected_model", "trailing_late_rate", "previous_random_forest"),
        ),
        "selected_model": best_name,
        "thresholds": {"investigate": best_thresholds[0], "escalate": best_thresholds[1]},
        "splits": {
            name: {
                "target_months": SPLITS[name],
                "rows": len(frame),
                "positives": int(frame[TARGET].sum()),
                "positive_rate": float(frame[TARGET].mean()),
            }
            for name, frame in splits.items()
        },
        "monthly_coverage": coverage,
        "validation": validation_metrics,
        "held_out_test": {
            "selected_model": model_metrics,
            "trailing_late_rate": metrics(test[TARGET], test_rule, rule_threshold),
            "previous_random_forest": metrics(test[TARGET], previous_scores, previous_thresholds[0]),
        },
    }
    output_dir.mkdir(parents=True, exist_ok=True)
    (output_dir / "metrics.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    test[["seller_id", "score_date", "target_month", TARGET, "target_deliveries", "target_late_deliveries"]].assign(
        risk_score=test_scores,
        baseline_score=test_rule,
        review_action=[review_action(score, best_thresholds) for score in test_scores],
    ).to_csv(output_dir / "test_scores.csv", index=False)
    joblib.dump({
        "model": best_model,
        "name": best_name,
        "features": best_columns,
        "thresholds": best_thresholds,
        "training_medians": train[best_columns].median().dropna().to_dict(),
        "ready_after": maturity_date(pd.Period(SPLITS["validation"][1], freq="M")),
    }, output_dir / "model.joblib")
    return report


def score_seller(
    orders: pd.DataFrame, reviews: pd.DataFrame, model_path: Path, seller_id: str,
    cutoff: pd.Timestamp, group_by: str,
) -> dict:
    artifact = joblib.load(model_path)
    if cutoff <= artifact["ready_after"]:
        raise ValueError("Pick a scoring date after the model's validation outcomes matured.")
    if cutoff > orders["purchased"].max():
        raise ValueError("The scoring date is beyond the available Olist order history.")
    features = seller_features(orders, reviews, cutoff).set_index("seller_id")
    if seller_id not in features.index:
        raise ValueError(f"Seller {seller_id} has insufficient recent order history or is absent.")

    model = artifact["model"]
    row = features.loc[[seller_id], artifact["features"]]
    score = float(model.predict_proba(row)[0, 1])
    changes = []
    for feature, median in artifact["training_medians"].items():
        value = row.iloc[0][feature]
        if pd.isna(value) or value == median:
            continue
        comparison = row.assign(**{feature: median})
        difference = score - float(model.predict_proba(comparison)[0, 1])
        if difference:
            changes.append({
                "feature": feature,
                "value": float(value),
                "training_median": median,
                "score_change_vs_median": difference,
            })
    drivers = sorted(changes, key=lambda change: abs(change["score_change_vs_median"]), reverse=True)
    return {
        "seller_id": seller_id,
        "score_date": cutoff.date().isoformat(),
        "target_month": str(cutoff.to_period("M") + 1),
        "model": artifact["name"],
        "risk_score": score,
        "review_action": review_action(score, artifact["thresholds"]),
        "feature_comparisons": drivers[:3],
        "historical_drilldown": product_drilldown(orders, seller_id, cutoff, group_by).to_dict("records"),
    }
