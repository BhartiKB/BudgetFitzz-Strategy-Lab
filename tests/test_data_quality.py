import unittest
from pathlib import Path

import pandas as pd

from insta_strategy_lab.analytics.core import audit_dataset


ROOT = Path(__file__).resolve().parents[1]


class DataQualityTests(unittest.TestCase):
    def test_verified_source_contract(self):
        frame = pd.read_csv(ROOT / "data/raw/budgetfitzz_dataset_fixed.csv")
        audit = audit_dataset(frame)
        self.assertEqual(audit["rows"], 150)
        self.assertEqual(audit["format_counts"], {"post": 137, "video": 13})
        self.assertEqual(audit["missing_by_column"]["cta"], 14)
        self.assertGreaterEqual(audit["span_days"], 14)


if __name__ == "__main__":
    unittest.main()

