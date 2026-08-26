from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
# Prefer src/agenticloop over tests/agenticloop package name collision.
for path in (str(SRC), str(ROOT)):
    if path in sys.path:
        sys.path.remove(path)
    sys.path.insert(0, path)
