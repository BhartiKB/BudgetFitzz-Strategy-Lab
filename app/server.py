"""Dependency-free local server for the BudgetFitzz strategy platform."""

from __future__ import annotations

import argparse
import json
import mimetypes
import os
import re
import sys
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import unquote, urlparse


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))


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
        if request_path.startswith("/analysis/generation_packages/"):
            self._serve_public_tree(request_path, "/analysis/generation_packages/", ROOT / "analysis/generation_packages")
            return
        if request_path in {"/analysis/content_generation_prompts.json", "/analysis/content_generation_prompts.md"}:
            self._serve_first_existing([ROOT / request_path.lstrip("/")])
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

    def do_POST(self):  # noqa: N802
        request_path = unquote(urlparse(self.path).path)
        if request_path == "/api/generation/import":
            self._import_generated_media()
            return
        if request_path == "/api/generation/approve":
            self._approve_generated_media()
            return
        self.send_error(404, "Public route not found")

    def do_HEAD(self):  # noqa: N802
        self.send_error(405, "HEAD requests are disabled")

    def _send_json(self, status: int, payload: dict) -> None:
        data = json.dumps(payload).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def _multipart_fields(self) -> tuple[dict[str, str], str, bytes]:
        content_type = self.headers.get("Content-Type", "")
        match = re.search(r"boundary=([^;]+)", content_type)
        length = int(self.headers.get("Content-Length", "0"))
        if not match or length <= 0 or length > 85 * 1024 * 1024:
            raise ValueError("Invalid or oversized multipart upload")
        boundary = match.group(1).strip().strip('"').encode("utf-8")
        fields: dict[str, str] = {}
        media_name = ""
        media_bytes = b""
        for part in self.rfile.read(length).split(b"--" + boundary):
            if b"\r\n\r\n" not in part:
                continue
            header, value = part.split(b"\r\n\r\n", 1)
            value = value.rstrip(b"\r\n")
            headers = header.decode("utf-8", errors="replace")
            name_match = re.search(r'name="([^\"]+)"', headers)
            if not name_match:
                continue
            name = name_match.group(1)
            filename_match = re.search(r'filename="([^\"]*)"', headers)
            if filename_match and filename_match.group(1):
                if name == "media_file":
                    media_name, media_bytes = filename_match.group(1), value
            else:
                fields[name] = value.decode("utf-8", errors="replace")
        if not media_name:
            raise ValueError("A media_file field is required")
        return fields, media_name, media_bytes

    def _import_generated_media(self) -> None:
        try:
            from insta_strategy_lab.generation.import_service import ImportService
            fields, filename, content = self._multipart_fields()
            result = ImportService(ROOT).import_media(fields, filename, content)
            self._send_json(201, {"status": "ok", "result": result})
        except (ValueError, OSError) as exc:
            self._send_json(400, {"status": "error", "message": str(exc)})

    def _approve_generated_media(self) -> None:
        try:
            from insta_strategy_lab.generation.import_service import ImportService
            length = int(self.headers.get("Content-Length", "0"))
            if length <= 0 or length > 4096:
                raise ValueError("Invalid approval request")
            job_id = str(json.loads(self.rfile.read(length).decode("utf-8")).get("job_id", ""))
            result = ImportService(ROOT).approve(job_id)
            self._send_json(200, {"status": "ok", "result": result})
        except (ValueError, OSError, json.JSONDecodeError) as exc:
            self._send_json(400, {"status": "error", "message": str(exc)})

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
