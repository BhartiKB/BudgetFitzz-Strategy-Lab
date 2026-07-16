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


if __name__ == "__main__":
    unittest.main()
