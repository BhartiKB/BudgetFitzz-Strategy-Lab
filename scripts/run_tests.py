"""Run the unittest suite and persist a reviewer-friendly quality-gate log."""

from __future__ import annotations

import io
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def main() -> None:
    suite = unittest.defaultTestLoader.discover(str(ROOT / "tests"))
    stream = io.StringIO()
    result = unittest.TextTestRunner(stream=stream, verbosity=2).run(suite)
    output = stream.getvalue()
    (ROOT / "logs" / "test_report.txt").write_text(output, encoding="utf-8")
    print(output, end="")
    if not result.wasSuccessful():
        raise SystemExit(1)


if __name__ == "__main__":
    main()
