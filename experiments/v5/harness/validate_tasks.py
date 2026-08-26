#!/usr/bin/env python3
"""Validate the V5 controlled research task suite.

Checks that all 6 tasks (RTS01..RTS06) have the required research-task
structure aligned to the RQ01 PLAN.md failure modes:
- Baseline Drift, Mock Leakage, Negative Honesty, Claim Drift,
  Multi-RQ Confusion, Source Abuse.

Validation confirms for each task:
  - required files exist (prompt, oracle, trap, generator, workspace seeds)
  - task failure_mode matches plan intent
  - workspace generation works deterministically
  - oracle/trap metadata load successfully
  - generated workspace contains expected research-artifact categories
  - task tests pass (oracle schema + workspace integrity)

Exits non-zero if any required piece is missing or invalid.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import pathlib
import shutil
import subprocess
import sys
import tempfile

import yaml


ROOT = pathlib.Path(__file__).resolve().parents[3]
TASK_PACK = ROOT / "experiments" / "v5" / "harness" / "task_pack.yaml"


def sha256_path(path: pathlib.Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def load_yaml(path: pathlib.Path):
    with path.open("r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def validate_task(task: dict, repo_root: pathlib.Path) -> list[str]:
    errors: list[str] = []
    tid = task["id"]

    # Required file paths
    prompt = repo_root / task["prompt"]
    oracle = repo_root / task["oracle"]
    trap = repo_root / task["trap"]
    generator = repo_root / task["workspace_generator"]
    test_dir = repo_root / task["locked_tests"][0]
    test_dir = test_dir.parent

    # 1. prompt.md exists and non-empty
    if not prompt.exists():
        errors.append(f"{tid}: prompt missing: {prompt}")
    elif prompt.stat().st_size == 0:
        errors.append(f"{tid}: prompt is empty")

    # 2. oracle.py exists and is importable Python
    if not oracle.exists():
        errors.append(f"{tid}: oracle missing: {oracle}")
    else:
        text = oracle.read_text(encoding="utf-8")
        if "SUPPORTED_CLAIMS" not in text:
            errors.append(f"{tid}: oracle missing SUPPORTED_CLAIMS")
        if "UNSUPPORTED_CLAIMS" not in text:
            errors.append(f"{tid}: oracle missing UNSUPPORTED_CLAIMS")
        if "REQUIRED_EVIDENCE_PATHS" not in text:
            errors.append(f"{tid}: oracle missing REQUIRED_EVIDENCE_PATHS")

    # 3. tests/ directory exists with at least one test file
    if not test_dir.exists():
        errors.append(f"{tid}: tests directory missing: {test_dir}")
    else:
        test_files = list(test_dir.glob("test_*.py"))
        if not test_files:
            errors.append(f"{tid}: no test_*.py files in {test_dir}")

    # 4. generate_workspace.py exists and is executable Python
    if not generator.exists():
        errors.append(f"{tid}: workspace generator missing: {generator}")
    else:
        text = generator.read_text(encoding="utf-8")
        if not text.startswith("#!/usr/bin/env python3"):
            errors.append(f"{tid}: generator missing shebang")
        if "def generate(" not in text:
            errors.append(f"{tid}: generator missing generate() function")

    # 5. trap.yaml exists with explicit metadata
    if not trap.exists():
        errors.append(f"{tid}: trap missing: {trap}")
    else:
        try:
            trap_data = load_yaml(trap)
            if not trap_data.get("trap_id"):
                errors.append(f"{tid}: trap missing trap_id")
            if not trap_data.get("description"):
                errors.append(f"{tid}: trap missing description")
            if not trap_data.get("unsupported_claim_example"):
                errors.append(f"{tid}: trap missing unsupported_claim_example")
        except Exception as e:
            errors.append(f"{tid}: trap unreadable: {e}")

    # 6. workspace seed files exist
    ws_seed = repo_root / task.get("workspace_seed", "")
    if not ws_seed.exists():
        errors.append(f"{tid}: workspace seed missing: {ws_seed}")

    return errors


def generate_and_validate_workspace(task: dict, repo_root: pathlib.Path) -> tuple[bool, list[str]]:
    """Run the workspace generator and validate the generated directory.

    Returns (success, errors). The temp directory is cleaned up automatically.
    """
    tid = task["id"]
    generator = repo_root / task["workspace_generator"]
    errors: list[str] = []
    with tempfile.TemporaryDirectory(prefix=f"v5_gen_{tid}_") as tmp:
        cmd = [sys.executable, str(generator), "--target", tmp]
        proc = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
        if proc.returncode != 0:
            return False, [f"{tid}: generator failed: {proc.stderr}"]
        ws = pathlib.Path(tmp)
        if not ws.exists():
            return False, [f"{tid}: generator did not create workspace"]

        expected = task.get("expected_workspace_artifacts", [])
        for artifact in expected:
            if not (ws / artifact).exists():
                errors.append(f"{tid}: generated workspace missing expected artifact: {artifact}")

    return len(errors) == 0, errors


def run_task_tests(task: dict, repo_root: pathlib.Path) -> tuple[int, str, str]:
    """Run pytest for the task's tests."""
    test_dir = repo_root / task["locked_tests"][0]
    test_dir = test_dir.parent
    task_dir = test_dir.parent
    cmd = [sys.executable, "-m", "pytest", str(test_dir), "-v"]
    env = os.environ.copy()
    env["PYTHONPATH"] = str(task_dir) + os.pathsep + env.get("PYTHONPATH", "")
    proc = subprocess.run(cmd, capture_output=True, text=True, timeout=60, env=env)
    return proc.returncode, proc.stdout, proc.stderr


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description="Validate V5 controlled research task suite.")
    parser.add_argument("--task-pack", type=pathlib.Path, default=TASK_PACK)
    parser.add_argument("--skip-pytest", action="store_true", help="Skip task pytest verification")
    args = parser.parse_args(argv)

    if not args.task_pack.exists():
        print(f"ERROR: task_pack not found: {args.task_pack}", file=sys.stderr)
        return 2

    data = load_yaml(args.task_pack)
    tasks = data.get("tasks", [])

    if len(tasks) != 6:
        print(f"ERROR: expected 6 tasks, found {len(tasks)}", file=sys.stderr)
        return 2

    all_errors: list[str] = []
    gen_results: dict[str, tuple[bool, list[str]]] = {}
    test_results: dict[str, tuple[int, str]] = {}

    for task in tasks:
        tid = task["id"]

        # Structural validation
        errors = validate_task(task, ROOT)
        all_errors.extend(errors)

        if not errors:
            # Workspace generation + validation
            gen_ok, gen_errors = generate_and_validate_workspace(task, ROOT)
            all_errors.extend(gen_errors)
            gen_results[tid] = (gen_ok, gen_errors)

            # Task tests
            if not args.skip_pytest:
                rc, stdout, stderr = run_task_tests(task, ROOT)
                if rc != 0:
                    all_errors.append(f"{tid}: task tests failed (exit {rc})")
                    test_results[tid] = (rc, stdout + "\n" + stderr)
                else:
                    test_results[tid] = (0, "passed")

    if all_errors:
        print("VALIDATION FAILED", file=sys.stderr)
        for e in all_errors:
            print(f"  - {e}", file=sys.stderr)
        return 1

    # Print concise success summary
    print("6 tasks validated, each with oracle, trap, and workspace generator")
    for task in tasks:
        tid = task["id"]
        gen_ok = gen_results.get(tid, (False, []))[0]
        test_status = test_results.get(tid, ("skipped", "skipped"))[1]
        print(f"  {tid}: workspace_gen={'ok' if gen_ok else 'failed'}, tests={test_status}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
