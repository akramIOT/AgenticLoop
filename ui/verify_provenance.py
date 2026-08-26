#!/usr/bin/env python3
"""Verify paper-canonical numbers against durable T05 artifacts."""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from agenticloop.analysis_ext import compute_extended_analysis, verify_paper_numbers, write_extended_artifacts


def main() -> int:
    verify = verify_paper_numbers(ROOT)
    analysis = compute_extended_analysis(ROOT)
    if "--write" in sys.argv:
        paths = write_extended_artifacts(ROOT)
        print(f"wrote {paths['json']}")
    print(json.dumps({"provenance_verify": verify, "gate_redundancy": analysis.gate_redundancy}, indent=2))
    return 0 if verify["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
