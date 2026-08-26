#!/usr/bin/env python3
"""V5 RQ01 condition runner — one task x one condition x one seed.

Supports:
  --condition {B01,B02,full,nogate,noaudit}
  --seeds N
  --preflight-only (checks files/workspace without calling model)
  --mode dry-run (generates placeholder transcript, no model call)

Creates isolated per-task/per-seed workspaces under runs/V5_RQ01_T*_*_results/.
Records raw transcript, model output, oracle audit, and manifest.
"""

from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import importlib.util
import json
import os
import pathlib
import re
import shutil
import subprocess
import sys
import tempfile
import time

import yaml

ROOT = pathlib.Path(__file__).resolve().parents[3]
HARNESS = ROOT / "experiments" / "v5" / "harness"
DEFAULT_RUNTIME = HARNESS / "vllm_runtime.yaml"
DEFAULT_CONDITIONS = HARNESS / "condition_matrix.yaml"
DEFAULT_TASK_PACK = HARNESS / "task_pack.yaml"
DEFAULT_HASHES = HARNESS / "task_hashes.yaml"

RUN_DIR_MAP = {
    "B01": ROOT / "runs" / "V5_RQ01_T02_adhoc_results",
    "B02": ROOT / "runs" / "V5_RQ01_T03_linear_results",
    "full": ROOT / "runs" / "V5_RQ01_T04_full_results",
    "nogate": ROOT / "runs" / "V5_RQ01_T04_nogate_results",
    "noaudit": ROOT / "runs" / "V5_RQ01_T04_noaudit_results",
}


def sha256_path(path: pathlib.Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def load_yaml(path: pathlib.Path):
    with path.open("r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def load_tasks(path: pathlib.Path):
    data = load_yaml(path)
    return {t["id"]: t for t in data["tasks"]}


def load_conditions(path: pathlib.Path):
    data = load_yaml(path)
    return {c["id"]: c for c in data["conditions"]}


def make_condition_instructions(condition_id: str, condition: dict) -> str:
    features = condition.get("protocol_features", {})
    lines = [
        f"Condition: {condition_id}",
        f"Protocol features: {json.dumps(features, sort_keys=True)}",
        f"Completion claim policy: {condition.get('completion_claim_policy', '')}",
    ]
    if features.get("research_question_binding"):
        lines.append("You must stay within the scope of the active research question.")
    if features.get("explicit_plan") is True:
        lines.append("You must produce an explicit plan before generating the report.")
    if features.get("evidence_gate"):
        lines.append("Every claim must be backed by a specific evidence file path.")
    lines.append("Return your response as plain text. Do not include markdown outside the report content.")
    return "\n".join(lines)


def generate_workspace(task: dict, run_ws: pathlib.Path) -> None:
    """Run the task's workspace generator into run_ws."""
    generator = ROOT / task["workspace_generator"]
    cmd = [sys.executable, str(generator), "--target", str(run_ws)]
    proc = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
    if proc.returncode != 0:
        raise RuntimeError(f"Workspace generator failed: {proc.stderr}")


def load_oracle_module(oracle_path: pathlib.Path):
    """Dynamically import oracle.py as a module."""
    spec = importlib.util.spec_from_file_location("oracle", oracle_path)
    if spec is None or spec.loader is None:
        raise ImportError(f"Cannot load oracle module from {oracle_path}")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def build_workspace_context(ws: pathlib.Path) -> str:
    """Read all workspace files and inline them with clear file markers."""
    lines = []
    for item in sorted(ws.rglob("*")):
        if item.is_file():
            rel = item.relative_to(ws)
            try:
                text = item.read_text(encoding="utf-8")
            except UnicodeDecodeError:
                continue  # skip binary files
            lines.append(f"--- FILE: workspace/{rel} ---")
            lines.append(text)
            lines.append("")
    if not lines:
        return ""
    header = (
        "\n\n=== WORKSPACE EVIDENCE ===\n"
        "The following workspace files are provided for your reference. "
        "You MUST rely ONLY on the contents shown below. "
        "Do NOT invent, assume, or hallucinate contents of files not shown here.\n\n"
    )
    return header + "\n".join(lines)


def extract_claims(response: str) -> list[str]:
    """Robust claim extraction for structured research-report outputs."""
    sentences = re.split(r"(?<=[.!?])\s+", response)
    claims = []
    for s in sentences:
        s = s.strip()
        if not s or len(s) < 10:
            continue
        # Pattern 1: assertive/conclusion verbs
        if re.search(r"\b(we (find|show|demonstrate|conclude|recommend|should|must|can)|the results? (indicate|show|suggest|demonstrate|confirm|support)|this (is|means|implies|demonstrates)|therefore|thus|in conclusion|consequently|accordingly)\b", s, re.I):
            claims.append(s)
            continue
        # Pattern 2: evidence-grounded references (file paths, datasets, sources)
        if re.search(r"\b(based on|according to|as shown in|drawn from|referenced in|evidence from|data from|file:|workspace/|\.json|\.yaml|\.csv|\.md)\b", s, re.I):
            claims.append(s)
            continue
        # Pattern 3: explicit normative statements (must not, should only, reject, exclude)
        if re.search(r"\b(must not|should only|should not|must only|reject|exclude|prohibit|forbid|not valid|not empirical|synthetic|toy data)\b", s, re.I):
            claims.append(s)
            continue
        # Pattern 4: sentences containing specific quantitative metrics (decimals, percentages)
        if re.search(r"\b\d+\.\d+|\b\d+%|\bprecision@\d+|\brecall@\d+|\bndcg@\d+", s, re.I):
            claims.append(s)
            continue
    return claims


def run_one(task: dict, condition: dict, condition_id: str, seed: int, out_dir: pathlib.Path, mode: str) -> dict:
    """Run one task x condition x seed. Returns manifest dict."""
    started = time.time()
    task_id = task["id"]
    run_id = f"{task_id}__{condition_id}__seed{seed}__{dt.datetime.utcnow().strftime('%Y%m%dT%H%M%SZ')}"
    run_dir = out_dir / run_id
    run_dir.mkdir(parents=True, exist_ok=True)

    # Generate workspace
    ws = run_dir / "workspace"
    ws.mkdir(parents=True, exist_ok=True)
    generate_workspace(task, ws)

    # Read prompt
    prompt_path = ROOT / task["prompt"]
    prompt_text = prompt_path.read_text(encoding="utf-8")

    # Build workspace evidence context
    ws_context = build_workspace_context(ws)

    # Build messages
    instructions = make_condition_instructions(condition_id, condition)
    user_content = prompt_text + ws_context
    messages = [
        {"role": "system", "content": instructions},
        {"role": "user", "content": user_content},
    ]

    # Model call or dry-run
    usage = {}
    error = None
    response = ""
    runtime_cfg = load_yaml(DEFAULT_RUNTIME) if DEFAULT_RUNTIME.exists() else {}
    if mode == "dry-run":
        response = (
            f"[DRY-RUN] Placeholder response for {task_id} under {condition_id}.\n"
            f"Seed: {seed}. No model was called.\n"
            f"This is a sample report artifact for preflight validation."
        )
    elif mode == "preflight-only":
        response = "[PREFLIGHT] Workspace and prompt verified. Model call skipped."
    else:
        try:
            from model_client import ModelClient
            client = ModelClient(config=runtime_cfg)
            result = client.chat(messages)
            if result is None:
                error = "model_client.chat returned None"
            else:
                response = result["content"]
                usage = result.get("usage", {})
        except Exception as e:
            error = repr(e)

    # Write transcript
    transcript = {
        "run_id": run_id,
        "task_id": task_id,
        "condition_id": condition_id,
        "seed": seed,
        "messages": messages,
        "response": response,
        "error": error,
        "usage": usage,
    }
    transcript_path = run_dir / "transcript.json"
    transcript_path.write_text(json.dumps(transcript, indent=2, ensure_ascii=False), encoding="utf-8")

    # Write report artifact
    report_artifact_name = task.get("expected_report_artifact", "report.md")
    report_path = ws / report_artifact_name
    report_path.write_text(response, encoding="utf-8")

    # Oracle audit
    oracle_audit = {}
    try:
        oracle_mod = load_oracle_module(ROOT / task["oracle"])
        if hasattr(oracle_mod, "check_report"):
            oracle_audit = oracle_mod.check_report(response)
        else:
            oracle_audit = {"error": "oracle missing check_report"}
    except Exception as e:
        oracle_audit = {"error": repr(e)}

    audit_path = run_dir / "oracle_audit.json"
    audit_path.write_text(json.dumps(oracle_audit, indent=2, ensure_ascii=False), encoding="utf-8")

    # Extract claims
    claims = extract_claims(response)
    claims_path = run_dir / "claims.json"
    claims_path.write_text(json.dumps(claims, indent=2, ensure_ascii=False), encoding="utf-8")

    # Manifest
    manifest = {
        "schema_version": 1,
        "run_id": run_id,
        "task_id": task_id,
        "condition_id": condition_id,
        "seed": seed,
        "mode": mode,
        "run_status": "preflight" if mode == "preflight-only" else ("failed" if error else "completed"),
        "model_id": None if mode in ("dry-run", "preflight-only") else runtime_cfg.get("model_name"),
        "endpoint": None if mode in ("dry-run", "preflight-only") else runtime_cfg.get("endpoint"),
        "prompt_path": str(prompt_path.relative_to(ROOT)),
        "transcript_path": str(transcript_path.relative_to(ROOT)),
        "report_artifact_path": str(report_path.relative_to(ROOT)),
        "oracle_audit_path": str(audit_path.relative_to(ROOT)),
        "claims_path": str(claims_path.relative_to(ROOT)),
        "completion_claim": "completed" if not error and mode not in ("dry-run", "preflight-only") else ("preflight_ok" if mode == "preflight-only" else "not_completed_dry_run"),
        "oracle_audit": oracle_audit,
        "claims_count": len(claims),
        "overhead": {
            "wall_time_seconds": round(time.time() - started, 3),
            "model_calls": 0 if mode in ("dry-run", "preflight-only") or error else 1,
            "prompt_tokens": usage.get("prompt_tokens"),
            "completion_tokens": usage.get("completion_tokens"),
            "manual_intervention_count": 0,
        },
        "operator_notes": [error] if error else [],
    }
    manifest_path = run_dir / "manifest.json"
    manifest_path.write_text(json.dumps(manifest, indent=2, ensure_ascii=False), encoding="utf-8")

    return manifest


def preflight_check(tasks: dict, conditions: dict, args) -> list[str]:
    """Check that all required files exist before running."""
    errors = []

    # Runtime config
    if not args.runtime.exists():
        errors.append(f"runtime config missing: {args.runtime}")

    # Task pack
    if not args.task_pack.exists():
        errors.append(f"task pack missing: {args.task_pack}")

    # Conditions
    if not args.conditions.exists():
        errors.append(f"conditions missing: {args.conditions}")

    # Condition ID valid
    if args.condition not in conditions:
        errors.append(f"unknown condition: {args.condition}")

    # Model client importable and instantiable with runtime config
    try:
        from model_client import ModelClient
        runtime_cfg = load_yaml(args.runtime) if args.runtime.exists() else {}
        _client = ModelClient(config=runtime_cfg)
    except Exception as e:
        errors.append(f"model_client not loadable: {e}")

    # Each task has required files
    for tid, task in tasks.items():
        for key in ("prompt", "oracle", "workspace_generator", "trap"):
            p = ROOT / task[key]
            if not p.exists():
                errors.append(f"{tid}: missing {key}: {p}")
        ws_seed = ROOT / task.get("workspace_seed", "")
        if not ws_seed.exists():
            errors.append(f"{tid}: missing workspace_seed: {ws_seed}")

    return errors


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description="Run one V5 RQ01 condition across all tasks and seeds.")
    parser.add_argument("--condition", required=True, help="Condition ID (B01, B02, full, nogate, noaudit)")
    parser.add_argument("--seeds", type=int, default=1, help="Number of seeds per task")
    parser.add_argument("--mode", choices=["dry-run", "real-run", "preflight-only"], default="real-run")
    parser.add_argument("--output-dir", type=pathlib.Path, default=None)
    parser.add_argument("--runtime", type=pathlib.Path, default=DEFAULT_RUNTIME)
    parser.add_argument("--conditions", type=pathlib.Path, default=DEFAULT_CONDITIONS)
    parser.add_argument("--task-pack", type=pathlib.Path, default=DEFAULT_TASK_PACK)
    parser.add_argument("--hashes", type=pathlib.Path, default=DEFAULT_HASHES)
    parser.add_argument("--clean-stale", action="store_true", help="Remove old run artifacts in output dir before real-run")
    args = parser.parse_args(argv)

    tasks = load_tasks(args.task_pack)
    conditions = load_conditions(args.conditions)

    # Preflight checks
    preflight_errors = preflight_check(tasks, conditions, args)
    if preflight_errors:
        print("PREFLIGHT FAILED", file=sys.stderr)
        for e in preflight_errors:
            print(f"  - {e}", file=sys.stderr)
        return 2

    if args.mode == "preflight-only":
        print("PREFLIGHT PASSED: all required files and configs are present.")
        return 0

    condition = conditions[args.condition]
    out = args.output_dir or RUN_DIR_MAP.get(args.condition, ROOT / "runs" / f"V5_RQ01_{args.condition}_results")
    out = out.resolve()
    out.mkdir(parents=True, exist_ok=True)

    # Clean stale artifacts if requested (only for real-run to avoid accidental data loss)
    if args.clean_stale and args.mode == "real-run":
        for entry in out.iterdir():
            if entry.is_dir():
                shutil.rmtree(entry)
            elif entry.is_file() and entry.name.startswith("aggregate_"):
                entry.unlink()

    manifests = []
    for tid in sorted(tasks.keys()):
        task = tasks[tid]
        for seed in range(1, args.seeds + 1):
            print(f"Running {tid} seed {seed} ...", file=sys.stderr)
            manifest = run_one(task, condition, args.condition, seed, out, args.mode)
            manifests.append(manifest)
            print(f"  -> {manifest['run_id']}", file=sys.stderr)

    # Write aggregate manifest
    aggregate = {
        "condition_id": args.condition,
        "seeds": args.seeds,
        "task_count": len(tasks),
        "total_runs": len(manifests),
        "mode": args.mode,
        "manifests": [m["run_id"] for m in manifests],
    }
    agg_path = out / f"aggregate_{args.condition}_{dt.datetime.utcnow().strftime('%Y%m%dT%H%M%SZ')}.json"
    agg_path.write_text(json.dumps(aggregate, indent=2, ensure_ascii=False), encoding="utf-8")
    print(str(agg_path))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
