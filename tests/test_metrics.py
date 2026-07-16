import unittest

import pandas as pd

from insta_strategy_lab.analytics.core import apply_metric_contract


class MetricTests(unittest.TestCase):
    def test_contract_formulas_and_zero_guard(self):
        frame = pd.DataFrame([{ "id":1,"date":"2026-01-01","format":"video","topic":"x","pillar":"Education","hook":"3 rules","caption":"x","cta":"Save","post_time":"12:00","reach":100,"impressions":150,"likes":5,"comments":2,"shares":1,"saves":2,"video_views":50,"watch_time_sec":200,"video_duration_sec":10 },{ "id":2,"date":"2026-01-02","format":"post","topic":"x","pillar":"Promotion","hook":"x","caption":"x","cta":None,"post_time":"13:00","reach":0,"impressions":0,"likes":0,"comments":0,"shares":0,"saves":0,"video_views":None,"watch_time_sec":None,"video_duration_sec":None }])
        result = apply_metric_contract(frame)
        self.assertEqual(result.loc[0, "engagements"], 10)
        self.assertAlmostEqual(result.loc[0, "engagement_rate_by_reach"], 10.0)
        self.assertAlmostEqual(result.loc[0, "average_watch_time_sec"], 4.0)
        self.assertAlmostEqual(result.loc[0, "retention_proxy"], 40.0)
        self.assertTrue(pd.isna(result.loc[1, "engagement_rate_by_reach"]))
        self.assertTrue(pd.isna(result.loc[1, "video_views"]))


if __name__ == "__main__":
    unittest.main()

