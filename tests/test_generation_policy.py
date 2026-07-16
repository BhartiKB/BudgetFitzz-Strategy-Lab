import json
import tempfile
import unittest
from pathlib import Path

from insta_strategy_lab.providers import GenerationPolicy, GenerationPolicyError


class GenerationPolicyTests(unittest.TestCase):
    def make_root(self) -> Path:
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        root = Path(temporary.name)
        (root / "config").mkdir()
        (root / "config/workflow.json").write_text(json.dumps({
            "generation_policy": {
                "mode": "free_only",
                "allow_paid_generation": False,
                "maximum_paid_generation_inr": 0,
                "disabled_providers": ["fal"],
            }
        }), encoding="utf-8")
        (root / ".env").write_text(
            "FAL_KEY=must-never-be-loaded\n"
            "gemini_token=dummy-gemini\n"
            "HF_TOKEN=dummy-hf\n",
            encoding="utf-8",
        )
        return root

    def test_credentials_are_reported_without_values(self):
        summary = GenerationPolicy(self.make_root()).public_summary()
        self.assertTrue(summary["gemini_configured"])
        self.assertTrue(summary["huggingface_configured"])
        self.assertTrue(summary["fal_ignored"])
        self.assertNotIn("dummy", json.dumps(summary))

    def test_fal_is_blocked_even_at_zero_estimated_cost(self):
        policy = GenerationPolicy(self.make_root())
        with self.assertRaises(GenerationPolicyError):
            policy.assert_media_call_allowed("fal", 0)

    def test_unknown_cost_and_paid_calls_are_blocked(self):
        policy = GenerationPolicy(self.make_root())
        with self.assertRaises(GenerationPolicyError):
            policy.assert_media_call_allowed("huggingface-video", None)
        with self.assertRaises(GenerationPolicyError):
            policy.assert_media_call_allowed("gemini-image", 0.01)

    def test_local_zero_cost_generation_is_allowed(self):
        GenerationPolicy(self.make_root()).assert_media_call_allowed("local", 0)


if __name__ == "__main__":
    unittest.main()
