import unittest

from insta_strategy_lab.agents.content_strategy import build_plan


class PlanTests(unittest.TestCase):
    def test_exact_format_contract(self):
        plan = build_plan()
        self.assertEqual(len(plan), 7)
        self.assertEqual(sum(item.format == "post" for item in plan), 5)
        self.assertEqual(sum(item.format == "video" for item in plan), 2)
        self.assertEqual([item.day for item in plan], list(range(1, 8)))
        self.assertTrue(all("target" in item.reasoned_target_range.lower() for item in plan))


if __name__ == "__main__":
    unittest.main()

