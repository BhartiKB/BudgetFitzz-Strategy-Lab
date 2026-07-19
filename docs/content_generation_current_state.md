# Content generation — verified starting state

Before the hybrid update, the workflow used `ContentPlannerAgent` to create the seven-day plan and `CreativeDirectorAgent` to create `analysis/video_generation_briefs.json`. `AssetGenerationAgent` then used `creative/generator.py` for Pillow post composition, `creative/generator.py` scene construction, and `video/generator.py` for FFmpeg/NVENC-first video assembly.

`providers/policy.py` guards paid calls and reads only selected `.env` names. The existing Hugging Face image and video clients remain separate bounded clients behind that policy; their included-credit ledgers record known attempts and HTTP/credit failures. `LocalProvider` selects the deterministic compositor as the guaranteed fallback.

The current Studio reads `app/data/platform_manifest.json`; the manifest links each approved plan item to its asset and links the video briefs to the content-planning and creative-direction decisions. The server already allowlisted `/app/`, `/assets/`, chart files, reports and final deliverables. Existing validators preserve exactly five posts, exactly two videos, approved dimensions/codecs, caption-to-beat alignment, spend checks and package checks.

No pre-existing user-facing file-import endpoint was present. The hybrid change adds one only for revised media candidates and does not alter the currently approved assets unless a human explicitly approves a validated candidate.
