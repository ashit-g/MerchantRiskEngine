"""Compare rankings under the same monthly review capacity."""

from math import ceil

import pandas as pd

from .features import TARGET


REVIEW_BUDGET_PERCENTS = (10, 25)
RANKINGS = ("selected_model", "trailing_late_rate")


def queue_metrics(reviewed: int, captured: int, rows: int, positives: int) -> dict:
    return {
        "reviewed": reviewed,
        "positives_captured": captured,
        "precision": captured / reviewed if reviewed else None,
        "recall": captured / positives if positives else None,
        "review_rate": reviewed / rows if rows else None,
    }


def compare_review_budgets(scores: pd.DataFrame, rankings: tuple[str, ...] = RANKINGS) -> dict:
    """Allocate the same number of review slots to each ranking each month."""
    report = {}
    for percent in REVIEW_BUDGET_PERCENTS:
        by_month = {}
        for month, frame in scores.groupby("target_month", sort=True):
            rows = len(frame)
            positives = int(frame[TARGET].sum())
            slots = ceil(rows * percent / 100)
            by_month[month] = {"seller_months": rows, "positives": positives}
            for ranking in rankings:
                # A stable, outcome-independent tie-break keeps slot counts exact.
                ranked = frame.sort_values([ranking, "seller_id"], ascending=[False, True])
                captured = int(ranked.head(slots)[TARGET].sum())
                by_month[month][ranking] = queue_metrics(slots, captured, rows, positives)

        rows = len(scores)
        positives = int(scores[TARGET].sum())
        pooled = {"seller_months": rows, "positives": positives}
        for ranking in rankings:
            reviewed = sum(month[ranking]["reviewed"] for month in by_month.values())
            captured = sum(month[ranking]["positives_captured"] for month in by_month.values())
            pooled[ranking] = queue_metrics(reviewed, captured, rows, positives)

        report[f"{percent}%"] = {"pooled": pooled, "by_month": by_month}
    return report
