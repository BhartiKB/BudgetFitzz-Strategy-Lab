# Media import and validation

The import endpoint accepts only an allowlisted image signature or MP4-style video signature, applies an upload-size limit, creates safe filenames, rejects traversal, writes to quarantine first, hashes the source, detects duplicates, validates content, atomically promotes the raw source and creates a processed candidate.

Images are decoded with Pillow, checked for size and blank output, then fitted to 1080×1350 PNG. Videos are inspected with FFprobe for streams, duration, dimensions and pixel format, then crop/padded and encoded as 1080×1920 H.264 using NVENC when available or libx264 otherwise. Raw imports are preserved separately; candidates never replace approved media until human approval.
