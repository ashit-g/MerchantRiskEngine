import unittest

import pandas as pd

from merchant_risk.features import TARGET
from merchant_risk.review_budget import compare_review_budgets


class ReviewBudgetTest(unittest.TestCase):
    def setUp(self):
        self.scores = pd.DataFrame({
            "target_month": ["2018-06"] * 5 + ["2018-07"] * 2,
            "seller_id": ["e", "c", "a", "b", "d", "a", "b"],
            TARGET: [0, 0, 1, 1, 0, 0, 0],
            "selected_model": [0.1, 0.4, 0.9, 0.8, 0.3, 0.2, 0.1],
            "trailing_late_rate": [0.5] * 7,
        })

    def test_budget_is_allocated_per_month_and_metrics_are_pooled_from_counts(self):
        result = compare_review_budgets(self.scores)["25%"]
        self.assertEqual(result["by_month"]["2018-06"]["selected_model"]["reviewed"], 2)
        self.assertEqual(result["by_month"]["2018-07"]["selected_model"]["reviewed"], 1)
        for ranking in ("selected_model", "trailing_late_rate"):
            pooled = result["pooled"][ranking]
            self.assertEqual(pooled["reviewed"], 3)
            self.assertEqual(pooled["positives_captured"], 2)
            self.assertAlmostEqual(pooled["precision"], 2 / 3)
            self.assertEqual(pooled["recall"], 1)
            self.assertIsNone(result["by_month"]["2018-07"][ranking]["recall"])

    def test_score_ties_use_seller_id_regardless_of_input_order(self):
        forward = compare_review_budgets(self.scores)["10%"]
        reverse = compare_review_budgets(self.scores.iloc[::-1])["10%"]
        self.assertEqual(forward, reverse)
        self.assertEqual(forward["by_month"]["2018-06"]["trailing_late_rate"]["positives_captured"], 1)


if __name__ == "__main__":
    unittest.main()
