# GPU and local generation

- GPU: NVIDIA GeForce RTX 4050 Laptop GPU
- VRAM: 6141 MiB
- Driver: 581.86
- FFmpeg NVENC available: True
- Selected encoder: h264_nvenc
- Meaningful GPU use confirmed: True
- PyTorch CUDA: False (PyTorch is optional and not installed in the executed environment)
- Local language provider: deterministic-template / budgetfitzz-editorial-v1

The project did not download or invoke a paid model. Structured content used a deterministic validated fallback. Video scenes were rendered locally and encoded through NVENC when available, with libx264 as a documented recovery path.
