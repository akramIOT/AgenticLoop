#!/usr/bin/env python3
"""Workspace generator for RTS03 Negative Honesty.

Copies seed workspace artifacts into the target directory deterministically.
"""

import argparse
import shutil
from pathlib import Path


def generate(target_dir: Path) -> Path:
    target_dir = Path(target_dir)
    target_dir.mkdir(parents=True, exist_ok=True)
    src = Path(__file__).resolve().parent / "workspace"
    for item in src.iterdir():
        if item.is_file():
            shutil.copy2(item, target_dir / item.name)
    return target_dir


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--target", required=True, help="Workspace directory to populate")
    args = parser.parse_args()
    out = generate(args.target)
    print(out)
