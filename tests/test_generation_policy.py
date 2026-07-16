import json
import tempfile
import unittest
from pathlib import Path

from insta_strategy_lab.providers import (
    GenerationPolicy,
    GenerationPolicyError,
    HuggingFaceImageClient,
    HuggingFaceVideoClient,
)


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
                "promotional_credit": {
                    "confirmed_by_user": True,
                    "maximum_test_list_cost_usd": 0.025,
                    "image_batch": {
                        "routing_provider": "replicate",
                        "confirmed_by_user": True,
                        "maximum_outputs": 5,
                        "list_cost_per_output_usd": 0.003,
                        "maximum_batch_list_cost_usd": 0.015,
                    },
                },
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

    def test_confirmed_hf_credit_call_is_bounded(self):
        policy = GenerationPolicy(self.make_root())
        policy.assert_promotional_credit_call_allowed("huggingface", 0.025, 0)
        with self.assertRaises(GenerationPolicyError):
            policy.assert_promotional_credit_call_allowed("huggingface", 0.026, 0)
        with self.assertRaises(GenerationPolicyError):
            policy.assert_promotional_credit_call_allowed("huggingface", 0.025, 1)

    def test_fal_credential_cannot_be_retrieved(self):
        policy = GenerationPolicy(self.make_root())
        with self.assertRaises(GenerationPolicyError):
            policy.credential("FAL_KEY")

    def test_existing_hf_reservation_blocks_a_repeat_before_network_access(self):
        root = self.make_root()
        (root / "logs").mkdir()
        (root / "logs/hf_promotional_credit_test.json").write_text(
            json.dumps({"status": "reserved"}), encoding="utf-8"
        )
        with self.assertRaises(GenerationPolicyError):
            HuggingFaceVideoClient(root).generate_test("prompt", root / "tmp/test.mp4")

    def test_confirmed_hf_image_batch_is_bounded_and_never_routes_to_fal(self):
        policy = GenerationPolicy(self.make_root())
        policy.assert_promotional_image_batch_allowed("huggingface", "replicate", 5, 0.003, 0)
        with self.assertRaises(GenerationPolicyError):
            policy.assert_promotional_image_batch_allowed("huggingface", "fal-ai", 5, 0.003, 0)
        with self.assertRaises(GenerationPolicyError):
            policy.assert_promotional_image_batch_allowed("huggingface", "replicate", 6, 0.003, 0)

    def test_existing_hf_image_ledger_blocks_the_entire_batch(self):
        root = self.make_root()
        (root / "logs").mkdir()
        (root / "logs/hf_promotional_image_batch.json").write_text(
            json.dumps({"status": "reserved"}), encoding="utf-8"
        )
        with self.assertRaises(GenerationPolicyError):
            HuggingFaceImageClient(root).generate_batch({}, root / "assets/source_media/posts")

    def test_partial_hf_image_batch_is_reported_without_claiming_completion(self):
        root = self.make_root()
        (root / "logs").mkdir()
        (root / "logs/hf_promotional_image_batch.json").write_text(
            json.dumps({
                "status": "resume_rejected_no_credit",
                "outputs": [
                    {"filename": "day01.jpg", "status": "succeeded"},
                    {"filename": "day03.jpg", "status": "succeeded"},
                ],
                "credit_restored_resume": {
                    "outputs": [
                        {"filename": "day03.jpg", "status": "succeeded"},
                        {"filename": "day04.jpg", "status": "succeeded"},
                        {"filename": "day06.jpg", "status": "succeeded"},
                    ]
                },
            }),
            encoding="utf-8",
        )
        summary = GenerationPolicy(root).public_summary()
        self.assertEqual(summary["hf_promotional_post_images_completed"], 4)
        self.assertEqual(summary["hf_promotional_post_images_status"], "partial")
        self.assertFalse(summary["hf_promotional_post_images_succeeded"])


if __name__ == "__main__":
    unittest.main()
