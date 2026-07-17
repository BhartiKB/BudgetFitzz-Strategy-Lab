import json
import sqlite3
import subprocess
import sys
import time
import unittest
import urllib.request
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class WorkflowAppTests(unittest.TestCase):
    def test_retry_and_checkpoint_configuration(self):
        config = json.loads((ROOT / "config/workflow.json").read_text(encoding="utf-8"))
        self.assertGreaterEqual(config["max_retries"], 1)
        self.assertEqual(len(config["human_checkpoints"]), 4)
        self.assertTrue(config["auto_approve_demo"])

    def test_persistent_state_when_present(self):
        path = ROOT / "logs/workflow.db"
        if not path.exists():
            self.skipTest("Workflow has not run yet")
        with sqlite3.connect(path) as conn:
            tables = {row[0] for row in conn.execute("SELECT name FROM sqlite_master WHERE type='table'")}
        self.assertTrue({"runs", "agents", "trace", "checkpoints", "spend"}.issubset(tables))

    def test_application_smoke(self):
        port = 8765
        process = subprocess.Popen([sys.executable, str(ROOT / "app/server.py"), "--port", str(port)], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        try:
            for _ in range(30):
                try:
                    with urllib.request.urlopen(f"http://127.0.0.1:{port}/api/status", timeout=1) as response:
                        payload = json.loads(response.read().decode("utf-8"))
                    self.assertEqual(payload["status"], "ready")
                    break
                except Exception:
                    time.sleep(0.1)
            else:
                self.fail("Application did not start")
        finally:
            process.terminate(); process.wait(timeout=5)
            if process.stdout:
                process.stdout.close()
            if process.stderr:
                process.stderr.close()

    def test_dashboard_metrics_are_pipeline_values_with_lineage(self):
        dashboard = json.loads((ROOT / "app/data/dashboard.json").read_text(encoding="utf-8"))
        self.assertEqual(dashboard["overview_kpis"][0]["value"], str(dashboard["audit"]["rows"]))
        self.assertEqual(
            dashboard["overview_kpis"][3]["value"],
            f"{dashboard['facts']['extreme_video_er_pct']:.2f}%",
        )
        self.assertEqual(dashboard["data_lineage"]["observed_rows"], dashboard["audit"]["rows"])
        self.assertFalse(dashboard["data_lineage"]["after_results_available"])
        self.assertTrue(all(item["source"] for item in dashboard["observed_metrics"]))
        self.assertTrue(all(item["before_kind"] == "observed" for item in dashboard["before_after"]))
        self.assertTrue(all(item["after_kind"] != "observed" for item in dashboard["before_after"]))

    def test_platform_manifest_is_generated_and_keeps_plan_and_video_context(self):
        manifest = json.loads((ROOT / "app/data/platform_manifest.json").read_text(encoding="utf-8"))
        dashboard = json.loads((ROOT / "app/data/dashboard.json").read_text(encoding="utf-8"))
        self.assertEqual(manifest["generated_by"], "insta_strategy_lab.reporting.builder.build_app_data")
        self.assertEqual(len(manifest["content_studio"]["plan"]), 7)
        self.assertEqual(manifest["content_studio"]["plan_counts"], {"post": 5, "video": 2})
        self.assertEqual(len(manifest["content_studio"]["video_briefs"]["briefs"]), 2)
        self.assertFalse(manifest["contract"]["formulas_visible_in_ui"])
        self.assertEqual(manifest["overview"]["kpis"], dashboard["overview_kpis"])

    def test_browser_code_does_not_embed_copied_kpi_values(self):
        script = (ROOT / "app/app.js").read_text(encoding="utf-8")
        self.assertNotIn("['150','historical items'", script)
        self.assertIn("platform_manifest.json", script)
        self.assertIn("overview.kpis", script)

    def test_metric_formulas_are_kept_out_of_the_browser_ui(self):
        markup = (ROOT / "app/index.html").read_text(encoding="utf-8")
        script = (ROOT / "app/app.js").read_text(encoding="utf-8")
        self.assertNotIn("Machine-readable formulas", markup)
        self.assertNotIn('id="metric-grid"', markup)
        self.assertNotIn("data.metric_contract.metrics", script)


if __name__ == "__main__":
    unittest.main()
