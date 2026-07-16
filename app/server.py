"""Dependency-free local server for the BudgetFitzz strategy platform."""

from __future__ import annotations

import argparse
import json
import mimetypes
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import unquote, urlparse


ROOT = Path(__file__).resolve().parents[1]


class Handler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(ROOT), **kwargs)

    def do_GET(self):  # noqa: N802
        request_path = unquote(urlparse(self.path).path)
        if self.path in ("/", ""):
            self.send_response(302)
            self.send_header("Location", "/app/index.html")
            self.end_headers()
            return
        if self.path == "/api/status":
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
                ROOT / "submission/final/final_report.pdf",
                ROOT / "final_report.pdf",
            ])
            return
        if request_path == "/submission-package.zip":
            self._serve_first_existing([
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
        super().do_GET()

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
    parser.add_argument("--port", type=int, default=8501)
    args = parser.parse_args()
    server = ThreadingHTTPServer(("127.0.0.1", args.port), Handler)
    print(f"BudgetFitzz Strategy Lab ready at http://127.0.0.1:{args.port}", flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
