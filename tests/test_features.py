import unittest

import pandas as pd

from merchant_risk.features import TARGET, monthly_outcomes, product_drilldown, seller_features


class HistoricalCutoffTest(unittest.TestCase):
    def setUp(self):
        self.cutoff = pd.Timestamp("2018-05-31")
        self.orders = pd.DataFrame({
            "seller_id": ["seller"] * 7,
            "purchased": pd.to_datetime(["2018-05-20"] * 6 + ["2018-06-01"]),
            "promised": pd.to_datetime(["2018-05-25"] * 4 + ["2018-05-30"] * 2 + ["2018-06-05"]),
            "delivered": pd.to_datetime([
                "2018-05-25", "2018-05-26", "2018-05-26", "2018-05-27",
                "2018-05-31", "2018-06-01", "2018-06-07",
            ]),
            "category": ["a", "a", "b", "b", "b", "c", "c"],
            "order_value": [10] * 6 + [100],
            "freight_value": [2] * 7,
        })
        self.orders["delay_days"] = (self.orders["delivered"] - self.orders["promised"]).dt.days
        self.orders["late"] = self.orders["delay_days"].gt(0)
        self.reviews = pd.DataFrame({
            "seller_id": ["seller", "seller"],
            "reviewed": pd.to_datetime(["2018-05-31", "2018-06-01"]),
            "low_review": [False, True],
        })

    def test_future_events_do_not_enter_historical_features(self):
        features = seller_features(self.orders, self.reviews, self.cutoff).iloc[0]
        self.assertEqual(features["orders_30d"], 6)
        self.assertEqual(features["deliveries_30d"], 5)
        self.assertAlmostEqual(features["late_rate_30d"], 0.8)
        self.assertEqual(features["reviews_30d"], 1)
        self.assertEqual(features["low_review_rate_30d"], 0)

    def test_known_next_month_orders_use_only_information_available_at_cutoff(self):
        orders = self.orders.copy()
        orders.loc[4:5, "promised"] = pd.Timestamp("2018-06-05")
        orders["delay_days"] = (orders["delivered"] - orders["promised"]).dt.days
        orders["late"] = orders["delay_days"].gt(0)
        features = seller_features(orders, self.reviews, self.cutoff).iloc[0]
        self.assertEqual(features["known_next_month_orders"], 2)
        self.assertEqual(features["known_next_month_delivered_share"], 0.5)
        self.assertEqual(features["known_next_month_days_to_promise"], 5)
        self.assertEqual(features["known_next_month_open_days"], 11)

        orders.loc[5, "delivered"] = pd.NaT
        orders["delay_days"] = (orders["delivered"] - orders["promised"]).dt.days
        orders["late"] = orders["delay_days"].gt(0)
        pd.testing.assert_series_equal(features, seller_features(orders, self.reviews, self.cutoff).iloc[0])

    def test_drilldown_reconciles_to_seller_totals(self):
        drilldown = product_drilldown(self.orders, "seller", self.cutoff)
        self.assertEqual(drilldown["category"].tolist(), ["b", "a"])
        self.assertEqual(drilldown["deliveries"].sum(), 5)
        self.assertEqual(drilldown["late_deliveries"].sum(), 4)
        self.assertAlmostEqual(drilldown["share_of_seller_late_deliveries"].sum(), 1.0)


class OutcomeTest(unittest.TestCase):
    def setUp(self):
        self.month = pd.Period("2018-06", freq="M")
        self.observed_through = pd.Timestamp("2018-07-30")
        self.orders = pd.DataFrame({
            "seller_id": ["exact_threshold"] * 6 + ["insufficient"] * 4,
            "order_status": ["delivered"] * 10,
            "promised": pd.to_datetime(["2018-06-24"] * 10),
            "delivered": pd.to_datetime(["2018-06-24"] * 4 + ["2018-07-30", "2018-07-31"]
                                        + ["2018-06-25"] * 4),
        })
        self.orders["delay_days"] = (self.orders["delivered"] - self.orders["promised"]).dt.days
        self.orders["late"] = self.orders["delay_days"].gt(0)

    def test_label_includes_exact_threshold_and_excludes_post_maturity_delivery(self):
        outcomes = monthly_outcomes(self.orders, self.month, self.observed_through).set_index("seller_id")
        self.assertEqual(outcomes.loc["exact_threshold", "target_deliveries"], 5)
        self.assertEqual(outcomes.loc["exact_threshold", "target_late_deliveries"], 1)
        self.assertEqual(outcomes.loc["exact_threshold", TARGET], 1)
        self.assertTrue(pd.isna(outcomes.loc["insufficient", TARGET]))

    def test_requires_full_label_followup(self):
        with self.assertRaisesRegex(ValueError, "needs observations"):
            monthly_outcomes(self.orders, self.month, self.observed_through - pd.Timedelta(days=1))


if __name__ == "__main__":
    unittest.main()
