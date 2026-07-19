import json
import socket
import subprocess
import sys
import tempfile
import time
import unittest
import urllib.error
import urllib.request
from pathlib import Path

from PIL import Image

from insta_strategy_lab.generation.import_service import ImportService, ImportValidationError
from insta_strategy_lab.generation.prompts import create_prompt_artifacts
from insta_strategy_lab.providers import GenerationRequest, ProviderRegistry, ProviderRouter, VeoProvider
from insta_strategy_lab.schemas import PlanItem


ROOT = Path(__file__).resolve().parents[1]


class HybridContentGenerationTests(unittest.TestCase):
    def test_provider_registry_is_truthful_and_manual_demo_is_enabled(self):
        status = ProviderRegistry(ROOT).public_status()
        states = {provider["id"]: provider for provider in status["providers"]}
        self.assertEqual(status["default_mode"], "MANUAL_PROVIDER")
        self.assertEqual(states["veo"]["api_state"], "DISABLED")
        self.assertEqual(states["veo"]["manual_state"], "READY")
        self.assertFalse(states["veo"]["api_tested"])
        self.assertEqual(states["local"]["api_state"], "READY")

    def test_router_respects_explicit_manual_mode_and_veo_needs_approval(self):
        router = ProviderRouter(ROOT)
        self.assertEqual(router.select_mode("MANUAL_PROVIDER"), "MANUAL_PROVIDER")
        request = GenerationRequest(job_id="test", asset_id="day02_one_shirt_three_ways", plan_day=2, asset_type="video", provider_mode="VEO_API", provider_name="Veo", model_name="Veo", prompt="test", width=1080, height=1920, aspect_ratio="9:16")
        result = VeoProvider(ROOT).prepare(request, approved=False)
        self.assertEqual(result.status, "DISABLED")
        self.assertIn("No Veo API request", result.error)

    def test_prompt_artifacts_are_exactly_exportable(self):
        payload = json.loads((ROOT / "analysis/content_generation_prompts.json").read_text(encoding="utf-8"))
        self.assertEqual(len(payload["assets"]), 7)
        for entry in payload["assets"]:
            package = json.loads((ROOT / "analysis/generation_packages" / f"{entry['asset_id']}.json").read_text(encoding="utf-8"))
            self.assertEqual(package["prompt"], entry["prompt"])
            self.assertEqual(package["negative_prompt"], entry["negative_prompt"])
            self.assertEqual(package["prompt_hash"], entry["prompt_hash"])
        self.assertIn("visible and exportable prompts", (ROOT / "analysis/content_generation_prompts.md").read_text(encoding="utf-8"))

    def test_image_import_uses_quarantine_versions_and_duplicate_guard(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "config").mkdir(); (root / "analysis").mkdir(); (root / "tools/ffmpeg/bin").mkdir(parents=True)
            (root / "config/content_generation.yaml").write_text((ROOT / "config/content_generation.yaml").read_text(encoding="utf-8"), encoding="utf-8")
            (root / "tools/ffmpeg/bin/ffmpeg.exe").write_bytes(b""); (root / "tools/ffmpeg/bin/ffprobe.exe").write_bytes(b"")
            prompt = {"assets": [{"asset_id": "sample", "plan_day": 1, "asset_type": "image", "prompt_version": 1, "prompt_hash": "hash"}]}
            (root / "analysis/content_generation_prompts.json").write_text(json.dumps(prompt), encoding="utf-8")
            image = Image.new("RGB", (800, 1000), "#336699")
            for x in range(0, 800, 40):
                for y in range(0, 1000, 40):
                    if (x + y) % 80 == 0:
                        image.paste("#99CC55", (x, y, x + 40, y + 40))
            image_path = root / "source.png"; image.save(image_path)
            fields = {"asset_id": "sample", "provider": "Google Flow / Veo", "access_method": "Manual web interface", "permission_confirmed": "true", "prompt_version": "1", "actual_cost_inr": "0", "attempts": "1"}
            service = ImportService(root)
            result = service.import_media(fields, "manual.png", image_path.read_bytes())
            self.assertEqual(result["status"], "AWAITING_REVIEW")
            versions = json.loads((root / "analysis/media_versions.json").read_text(encoding="utf-8"))
            version = versions["assets"]["sample"]["versions"][0]
            self.assertTrue((root / version["raw_import"]).is_file())
            self.assertTrue((root / version["candidate_output"]).is_file())
            with self.assertRaises(ImportValidationError):
                service.import_media(fields, "manual.png", image_path.read_bytes())

    def test_video_validation_preserves_existing_video_contract(self):
        service = ImportService(ROOT)
        payload = service._validate_video(ROOT / "assets/videos/day02_one_shirt_three_ways.mp4")
        self.assertEqual(payload["codec"], "h264")
        self.assertEqual((payload["width"], payload["height"]), (1080, 1920))

    def test_approval_archives_previous_active_media(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "config").mkdir(); (root / "analysis").mkdir(); (root / "assets/videos").mkdir(parents=True); (root / "tools/ffmpeg/bin").mkdir(parents=True)
            (root / "config/content_generation.yaml").write_text((ROOT / "config/content_generation.yaml").read_text(encoding="utf-8"), encoding="utf-8")
            (root / "tools/ffmpeg/bin/ffmpeg.exe").write_bytes(b""); (root / "tools/ffmpeg/bin/ffprobe.exe").write_bytes(b"")
            prompt = {"assets": [{"asset_id": "sample_video", "plan_day": 2, "asset_type": "video", "prompt_version": 1, "prompt_hash": "hash"}]}
            (root / "analysis/content_generation_prompts.json").write_text(json.dumps(prompt), encoding="utf-8")
            old = root / "assets/videos/sample_video.mp4"; old.write_bytes(b"old-approved-media")
            candidate = root / "artifacts/processed_candidates/sample_video/v002.mp4"; candidate.parent.mkdir(parents=True); candidate.write_bytes(b"new-candidate-media")
            (root / "analysis/media_versions.json").write_text(json.dumps({"assets": {"sample_video": {"active_version": "v001", "versions": [{"version": "v001", "status": "APPROVED", "candidate_output": "assets/videos/sample_video.mp4", "approval_history": []}, {"version": "v002", "status": "AWAITING_REVIEW", "candidate_output": "artifacts/processed_candidates/sample_video/v002.mp4", "approval_history": []}]}}}), encoding="utf-8")
            (root / "analysis/generation_jobs.json").write_text(json.dumps({"jobs": [{"job_id": "job-2", "asset_id": "sample_video", "final_output": "artifacts/processed_candidates/sample_video/v002.mp4", "status": "AWAITING_REVIEW"}]}), encoding="utf-8")
            result = ImportService(root).approve("job-2")
            self.assertEqual(result["status"], "APPROVED")
            self.assertEqual(old.read_bytes(), b"new-candidate-media")
            self.assertEqual((root / "assets/versions/sample_video/v001.mp4").read_bytes(), b"old-approved-media")
            versions = json.loads((root / "analysis/media_versions.json").read_text(encoding="utf-8"))
            self.assertEqual(versions["assets"]["sample_video"]["active_version"], "v002")
            self.assertEqual(versions["assets"]["sample_video"]["versions"][0]["status"], "SUPERSEDED")

    def test_import_security_rejects_wrong_signature_and_missing_permission(self):
        service = ImportService(ROOT)
        with self.assertRaises(ImportValidationError):
            service.import_media({"asset_id": "day01_capsule_formula", "provider": "Google Flow / Veo", "access_method": "Manual web interface", "permission_confirmed": "false", "prompt_version": "1"}, "not-media.txt", b"not an image")

    def test_existing_asset_versions_are_preserved_as_v001(self):
        versions = json.loads((ROOT / "analysis/media_versions.json").read_text(encoding="utf-8"))
        self.assertSetEqual(set(versions["assets"]), {"day01_capsule_formula", "day02_one_shirt_three_ways", "day03_colour_vote", "day04_budget_priority", "day05_fit_mistakes", "day06_sneaker_scorecard", "day07_wardrobe_audit"})
        self.assertTrue(all(item["active_version"].startswith("v") for item in versions["assets"].values()))

    def test_frontend_exposes_prompt_export_and_import_controls(self):
        script = (ROOT / "app/app.js").read_text(encoding="utf-8")
        self.assertIn("Generation Prompt", script)
        self.assertIn("Copy prompt", script)
        self.assertIn("Export JSON", script)
        self.assertIn("Import Generated Media", script)
        self.assertIn("/api/generation/import", script)

    def test_import_endpoint_rejects_malformed_or_unsafe_upload(self):
        with socket.socket() as sock:
            sock.bind(("127.0.0.1", 0)); port = sock.getsockname()[1]
        process = subprocess.Popen([sys.executable, str(ROOT / "app/server.py"), "--port", str(port)], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        try:
            for _ in range(30):
                try:
                    urllib.request.urlopen(f"http://127.0.0.1:{port}/api/status", timeout=1); break
                except Exception:
                    time.sleep(0.1)
            request = urllib.request.Request(f"http://127.0.0.1:{port}/api/generation/import", data=b"not-a-multipart-upload", method="POST", headers={"Content-Type": "text/plain"})
            with self.assertRaises(urllib.error.HTTPError) as response:
                urllib.request.urlopen(request, timeout=2)
            self.assertEqual(response.exception.code, 400)
        finally:
            process.terminate(); process.wait(timeout=5)
            if process.stdout: process.stdout.close()
            if process.stderr: process.stderr.close()


if __name__ == "__main__":
    unittest.main()
