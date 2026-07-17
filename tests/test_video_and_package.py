import json
import subprocess
import unittest
import zipfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class VideoPackageTests(unittest.TestCase):
    def setUp(self):
        if not (ROOT / "analysis/seven_day_plan.json").exists():
            self.skipTest("Generated outputs not present yet")

    def test_video_validity(self):
        probe_matches = list((ROOT / "tools/ffmpeg").glob("**/bin/ffprobe.exe"))
        self.assertTrue(probe_matches)
        plan = json.loads((ROOT / "analysis/seven_day_plan.json").read_text(encoding="utf-8"))
        videos = [x for x in plan if x["format"] == "video"]
        self.assertEqual(len(videos), 2)
        for item in videos:
            path = ROOT / "assets/videos" / item["asset_filename"]
            completed = subprocess.run([str(probe_matches[0]), "-v", "error", "-show_entries", "stream=codec_name,width,height:format=duration", "-of", "json", str(path)], capture_output=True, text=True, check=True)
            data = json.loads(completed.stdout)
            self.assertEqual(data["streams"][0]["codec_name"], "h264")
            self.assertEqual((data["streams"][0]["width"], data["streams"][0]["height"]), (1080, 1920))
            self.assertTrue(8 <= float(data["format"]["duration"]) <= 15)

    def test_day_two_caption_describes_the_photographic_video(self):
        plan = json.loads((ROOT / "analysis/seven_day_plan.json").read_text(encoding="utf-8"))
        day_two = next(item for item in plan if item["day"] == 2)
        caption = day_two["full_proposed_caption"].lower()
        self.assertIn("one overshirt", caption)
        self.assertIn("cream tee", caption)
        self.assertIn("one setting", caption)
        self.assertIn("collar, cuff and hem", caption)
        self.assertNotIn("commute", caption)
        self.assertNotIn("evening", caption)
        self.assertIn("photographic", day_two["visual_direction"].lower())

    def test_day_five_caption_lists_all_photographic_fit_checks(self):
        plan = json.loads((ROOT / "analysis/seven_day_plan.json").read_text(encoding="utf-8"))
        day_five = next(item for item in plan if item["day"] == 5)
        caption = day_five["full_proposed_caption"].lower()
        self.assertIn("not a before-and-after", caption)
        self.assertIn("tee hem", caption)
        self.assertIn("trouser line", caption)
        self.assertNotIn("heavy stacking", caption)
        self.assertNotIn("oversized top", caption)
        self.assertIn("photographic", day_five["visual_direction"].lower())
        self.assertTrue((ROOT / "assets/source_media/day05_hf_wan.mp4").exists())

    def test_agent_storyboards_are_caption_backed(self):
        plan = json.loads((ROOT / "analysis/seven_day_plan.json").read_text(encoding="utf-8"))
        payload = json.loads((ROOT / "analysis/video_generation_briefs.json").read_text(encoding="utf-8"))
        self.assertEqual(payload["generated_by"], ["ContentPlannerAgent", "CreativeDirectorAgent"])
        self.assertEqual(len(payload["briefs"]), 2)
        plan_by_asset = {item["asset_filename"]: item for item in plan if item["format"] == "video"}
        self.assertEqual({item["asset_filename"] for item in payload["briefs"]}, set(plan_by_asset))
        for brief in payload["briefs"]:
            caption = plan_by_asset[brief["asset_filename"]]["full_proposed_caption"].lower()
            self.assertTrue(brief["creative_director_decision"]["why"])
            self.assertTrue(brief["beats"])
            for beat in brief["beats"]:
                self.assertIn(beat["caption_evidence"].lower(), caption)
                self.assertGreater(beat["source_window_sec"][1], beat["source_window_sec"][0])
                self.assertTrue(beat["focus_graphic"])

    def test_package_is_valid_zip_when_present(self):
        path = ROOT / "submission/insta_strategy_lab_task2_submission.zip"
        if not path.exists():
            self.skipTest("Package not built yet")
        self.assertTrue(zipfile.is_zipfile(path))


if __name__ == "__main__":
    unittest.main()
