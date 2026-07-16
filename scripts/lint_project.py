"""Dependency-free project lint: UTF-8, Python syntax, indentation tabs, and trailing space."""

from __future__ import annotations

import ast
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
EXCLUDED = {".git", ".venv", "submission", "tmp", "tools", "__pycache__"}


def main() -> None:
    issues: list[dict[str, object]] = []
    files = [
        path
        for path in ROOT.rglob("*.py")
        if not any(part in EXCLUDED for part in path.relative_to(ROOT).parts)
    ]
    for path in sorted(files):
        relative = path.relative_to(ROOT).as_posix()
        try:
            source = path.read_text(encoding="utf-8")
        except UnicodeDecodeError as exc:
            issues.append({"file": relative, "line": exc.start, "rule": "utf8", "message": str(exc)})
            continue
        try:
            ast.parse(source, filename=relative)
        except SyntaxError as exc:
            issues.append({"file": relative, "line": exc.lineno or 0, "rule": "syntax", "message": exc.msg})
        for number, line in enumerate(source.splitlines(), start=1):
            if line.rstrip() != line:
                issues.append({"file": relative, "line": number, "rule": "trailing-whitespace", "message": "Remove trailing whitespace."})
            indentation = line[: len(line) - len(line.lstrip())]
            if "\t" in indentation:
                issues.append({"file": relative, "line": number, "rule": "indent-tabs", "message": "Use spaces for indentation."})
    report = {"status": "PASS" if not issues else "FAIL", "files_checked": len(files), "issues": issues}
    output = ROOT / "logs" / "lint_report.json"
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2))
    if issues:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
