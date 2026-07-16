import csv
import json
import unittest
from pathlib import Path

from PIL import Image


ROOT = Path(__file__).resolve().parents[1]


class AssetSpendTests(unittest.TestCase):
    def setUp(self):
        plan_path = ROOT / "analysis/seven_day_plan.json"
        if not plan_path.exists():
            self.skipTest("Generated outputs not present yet")
        self.plan = json.loads(plan_path.read_text(encoding="utf-8"))

    def test_post_dimensions_and_mapping(self):
        posts = [item for item in self.plan if item["format"] == "post"]
        self.assertEqual(len(posts), 5)
        for item in posts:
            path = ROOT / "assets/posts" / item["asset_filename"]
            self.assertTrue(path.exists())
            with Image.open(path) as image:
                self.assertEqual(image.size, (1080, 1350))
                self.assertEqual(image.format, "PNG")
                self.assertTrue(image.info.get("Description"))

    def test_paid_spend_cap(self):
        with (ROOT / "logs/spend_log.csv").open(encoding="utf-8-sig", newline="") as handle:
            rows = list(csv.DictReader(handle))
        total = sum(float(row["total_cost_inr"]) for row in rows if row["paid_or_free"] == "paid")
        self.assertLessEqual(total, 100)
        self.assertEqual(total, 0)


if __name__ == "__main__":
    unittest.main()

