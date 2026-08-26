#!/usr/bin/env python3
"""CLI: admit a draft claim through the AgenticLoop evidence gate."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from agenticloop.claim_gate import admit_claim


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="AgenticLoop claim admission CLI")
    parser.add_argument("claim", nargs="?", help="Draft claim text")
    parser.add_argument("--file", type=Path, help="Read claim text from file")
    parser.add_argument("--require-artifact-path", action="store_true")
    parser.add_argument("--allow-mock", action="store_true")
    parser.add_argument("--json", action="store_true", help="Emit JSON")
    args = parser.parse_args(argv)

    if args.file:
        claim = args.file.read_text(encoding="utf-8")
    elif args.claim:
        claim = args.claim
    else:
        claim = sys.stdin.read()

    result = admit_claim(
        claim,
        require_artifact_path=args.require_artifact_path,
        allow_mock=args.allow_mock,
    )
    if args.json:
        print(json.dumps(result.to_dict(), indent=2, ensure_ascii=False))
    else:
        print(f"decision: {result.decision}")
        print(f"paper_allowed: {result.paper_allowed}")
        for reason in result.reasons:
            print(f"- {reason}")
    return 0 if result.decision != "rejected" else 2


if __name__ == "__main__":
    raise SystemExit(main())
