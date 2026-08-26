#!/usr/bin/env python3
"""AgenticLoop Evidence Console — local UI for the research control plane.

Serves a branded console that:
  - visualizes the Direction → Epoch → Gate → Binding pipeline
  - admits/holds draft claims via the evidence-gate heuristic
  - inspects metric provenance (T05 vs ablation) without mixing sources
  - compares protocol conditions from durable run artifacts

Run from repo root:
  python ui/server.py
  # open http://127.0.0.1:8765
"""

from __future__ import annotations

import sys
from pathlib import Path

from flask import Flask, jsonify, request, send_from_directory

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from agenticloop.analysis_ext import compute_extended_analysis, verify_paper_numbers  # noqa: E402
from agenticloop.claim_gate import admit_claim  # noqa: E402
from agenticloop.core_directions import compute_core_directions  # noqa: E402
from agenticloop.provenance import load_metric_bundle, resolve_metric  # noqa: E402
from agenticloop.spine import load_research_spine  # noqa: E402
from agenticloop.strengthened_claims import compute_strengthened_claims  # noqa: E402

STATIC = Path(__file__).resolve().parent / "static"
app = Flask(__name__, static_folder=str(STATIC), static_url_path="/static")


@app.get("/")
def index():
    return send_from_directory(STATIC, "index.html")


@app.get("/api/health")
def health():
    return jsonify({"ok": True, "service": "agenticloop-evidence-console"})


@app.get("/api/spine")
def spine():
    return jsonify(load_research_spine(ROOT))


@app.get("/api/metrics")
def metrics():
    return jsonify(load_metric_bundle(ROOT))


@app.get("/api/metrics/<metric_id>")
def metric_one(metric_id: str):
    try:
        return jsonify(resolve_metric(metric_id, ROOT))
    except KeyError as e:
        return jsonify({"error": str(e)}), 404


@app.post("/api/admit")
def admit():
    payload = request.get_json(silent=True) or {}
    claim = payload.get("claim", "")
    require_path = bool(payload.get("require_artifact_path", False))
    allow_mock = bool(payload.get("allow_mock", False))
    result = admit_claim(claim, require_artifact_path=require_path, allow_mock=allow_mock)
    return jsonify(result.to_dict())


@app.get("/api/research-points")
def research_points():
    analysis = compute_extended_analysis(ROOT)
    verify = verify_paper_numbers(ROOT)
    payload = analysis.to_dict()
    payload["provenance_verify"] = verify
    return jsonify(payload)


@app.get("/api/core-directions")
def core_directions():
    return jsonify(compute_core_directions(ROOT).to_dict())


@app.get("/api/strengthened-claims")
def strengthened_claims():
    return jsonify(compute_strengthened_claims(ROOT).to_dict())


def main() -> int:
    print("AgenticLoop Evidence Console")
    print(f"  repo: {ROOT}")
    print("  open: http://127.0.0.1:8765")
    app.run(host="127.0.0.1", port=8765, debug=False)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
