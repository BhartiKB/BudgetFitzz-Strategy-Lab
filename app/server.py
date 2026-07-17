"""Dependency-free local server for the BudgetFitzz strategy platform."""

from __future__ import annotations

import argparse
import json
import mimetypes
import os
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import unquote, urlparse


ROOT = Path(__file__).resolve().parents[1]


class Handler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(ROOT), **kwargs)

    def do_GET(self):  # noqa: N802
        request_path = unquote(urlparse(self.path).path)
        if request_path in ("/", ""):
            self.send_response(302)
            self.send_header("Location", "/app/index.html")
            self.end_headers()
            return
        if request_path == "/api/status":
            payload = {"status": "ready", "platform": "BudgetFitzz Strategy Lab", "offline": True}
            data = json.dumps(payload).encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(data)))
            self.end_headers()
            self.wfile.write(data)
            return
        if request_path == "/final_report.pdf":
            self._serve_first_existing([
                ROOT / "deploy/final_report.pdf",
                ROOT / "submission/final/final_report.pdf",
                ROOT / "final_report.pdf",
            ])
            return
        if request_path == "/submission-package.zip":
            self._serve_first_existing([
                ROOT / "deploy/insta_strategy_lab_task2_submission.zip",
                ROOT / "submission/insta_strategy_lab_task2_submission.zip",
                ROOT / "insta_strategy_lab_task2_submission.zip",
                ROOT.parent / "insta_strategy_lab_task2_submission.zip",
            ], download_name="insta_strategy_lab_task2_submission.zip")
            return
        if request_path.startswith("/assets/"):
            relative = Path(request_path.removeprefix("/assets/"))
            if ".." in relative.parts:
                self.send_error(400, "Invalid asset path")
                return
            self._serve_first_existing([ROOT / "assets" / relative, ROOT / relative])
            return
        explicit_files = {
            "/submission/final/platform_walkthrough.mp4": ROOT / "deploy/platform_walkthrough.mp4",
            "/submission/final/submission_manifest.json": ROOT / "deploy/submission_manifest.json",
            "/logs/validation_report.json": ROOT / "deploy/validation_report.json",
        }
        if request_path in explicit_files:
            self._serve_first_existing([explicit_files[request_path], ROOT / request_path.lstrip("/")])
            return
        if request_path == "/app":
            self.send_response(302)
            self.send_header("Location", "/app/index.html")
            self.end_headers()
            return
        if request_path.startswith("/app/"):
            self._serve_public_tree(request_path, "/app/", ROOT / "app")
            return
        if request_path.startswith("/analysis/charts/"):
            self._serve_public_tree(request_path, "/analysis/charts/", ROOT / "analysis/charts")
            return
        self.send_error(404, "Public route not found")

    def do_HEAD(self):  # noqa: N802
        self.send_error(405, "HEAD requests are disabled")

    def _serve_public_tree(self, request_path: str, url_prefix: str, directory: Path) -> None:
        relative = Path(request_path.removeprefix(url_prefix))
        if not relative.parts or ".." in relative.parts:
            self.send_error(400, "Invalid public path")
            return
        root = directory.resolve()
        candidate = (root / relative).resolve()
        if not candidate.is_relative_to(root):
            self.send_error(400, "Invalid public path")
            return
        self._serve_first_existing([candidate])

    def _serve_first_existing(self, candidates: list[Path], download_name: str | None = None) -> None:
        for candidate in candidates:
            if candidate.is_file():
                payload = candidate.read_bytes()
                content_type = mimetypes.guess_type(candidate.name)[0] or "application/octet-stream"
                self.send_response(200)
                self.send_header("Content-Type", content_type)
                self.send_header("Content-Length", str(len(payload)))
                if download_name:
                    self.send_header("Content-Disposition", f'attachment; filename="{download_name}"')
                self.end_headers()
                self.wfile.write(payload)
                return
        self.send_error(404, "Requested deliverable was not found")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--host", default=os.environ.get("HOST", "127.0.0.1"))
    parser.add_argument("--port", type=int, default=int(os.environ.get("PORT", "8501")))
    args = parser.parse_args()
    server = ThreadingHTTPServer((args.host, args.port), Handler)
    print(f"BudgetFitzz Strategy Lab ready at http://{args.host}:{args.port}", flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
