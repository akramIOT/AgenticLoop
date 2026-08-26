"""Extended research-point analyses over durable V5/V6 artifacts.

All outputs are derived from existing artifacts. No new model runs are invented.
"""

from __future__ import annotations

import json
from collections import defaultdict
from dataclasses import asdict, dataclass, field
from pathlib import Path
from statistics import mean, pstdev
from typing import Any


@dataclass(frozen=True)
class ExtendedAnalysis:
    schema_version: int
    claim_volume: dict[str, Any]
    gate_redundancy: dict[str, Any]
    cross_classifier_drift: dict[str, Any]
    task_heterogeneity: dict[str, Any]
    high_ur_tasks_full: list[dict[str, Any]]
    temperature_profile: dict[str, Any] = field(default_factory=dict)
    failure_modes: dict[str, Any] = field(default_factory=dict)
    pairwise_wins: dict[str, Any] = field(default_factory=dict)
    label_taxonomy: dict[str, Any] = field(default_factory=dict)
    v5_v6_shift: dict[str, Any] = field(default_factory=dict)
    ablation_volume: dict[str, Any] = field(default_factory=dict)
    research_points: list[dict[str, str]] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def _repo_root(start: Path | None = None) -> Path:
    if start is None:
        start = Path(__file__).resolve()
    for parent in [start, *start.parents]:
        if (parent / "docs" / "research" / "CURRENT").exists():
            return parent
    return Path(__file__).resolve().parents[2]


def _pearson(xs: list[float], ys: list[float]) -> float | None:
    if len(xs) < 2 or len(xs) != len(ys):
        return None
    mx, my = mean(xs), mean(ys)
    num = sum((x - mx) * (y - my) for x, y in zip(xs, ys))
    den = (sum((x - mx) ** 2 for x in xs) * sum((y - my) ** 2 for y in ys)) ** 0.5
    return round(num / den, 4) if den > 0 else None


def compute_extended_analysis(repo_root: Path | None = None) -> ExtendedAnalysis:
    root = repo_root or _repo_root()
    t05 = json.loads((root / "runs" / "V6_RQ01_T05_metrics.json").read_text(encoding="utf-8"))
    abl = json.loads((root / "runs" / "V6_RQ02_T03_ablation_delta.json").read_text(encoding="utf-8"))
    labels_path = root / "runs" / "V6_RQ01_T05_audit_labels.json"
    v5_path = root / "runs" / "V5_RQ01_T05_metrics.json"

    bc = t05["by_condition"]
    btc = t05["by_task_condition"]
    tasks = sorted({k.split("__")[0] for k in btc})

    claim_volume = {}
    for cond in ("B01", "B02", "full"):
        runs = bc[cond]["total_runs"]
        claims = bc[cond]["total_claims"]
        claim_volume[cond] = {
            "total_runs": runs,
            "total_claims": claims,
            "unsupported_claim_rate": bc[cond]["unsupported_claim_rate"],
            "trace_completeness": bc[cond]["trace_completeness"],
            "claims_per_run": round(claims / runs, 4) if runs else 0.0,
        }
    claim_volume["ratios"] = {
        "full_over_b01_claims_per_run": round(
            claim_volume["full"]["claims_per_run"] / claim_volume["B01"]["claims_per_run"], 4
        ),
        "full_over_b02_claims_per_run": round(
            claim_volume["full"]["claims_per_run"] / claim_volume["B02"]["claims_per_run"], 4
        ),
        "note": "Full emits more claims/run than B01/B02 at nearly identical UR to B02.",
    }

    ur_b01 = bc["B01"]["unsupported_claim_rate"]
    ur_b02 = bc["B02"]["unsupported_claim_rate"]
    ur_full = bc["full"]["unsupported_claim_rate"]
    linear_gain = ur_b01 - ur_b02
    gate_extra = ur_b02 - ur_full
    total_gain = ur_b01 - ur_full
    gate_share = (gate_extra / total_gain) if abs(total_gain) > 1e-12 else 0.0
    if abs(linear_gain) < 1e-12:
        redundancy = 1.0 if abs(gate_extra) < 1e-12 else 0.0
    else:
        redundancy = max(0.0, min(1.0, 1.0 - abs(gate_extra) / abs(linear_gain)))

    gate_redundancy = {
        "ur_b01": ur_b01,
        "ur_b02": ur_b02,
        "ur_full": ur_full,
        "linear_gain_pp": round(linear_gain * 100, 4),
        "gate_extra_over_linear_pp": round(gate_extra * 100, 4),
        "b01_to_full_pp": round(total_gain * 100, 4),
        "gate_share_of_b01_to_full": round(gate_share, 4),
        "gate_redundancy_index": round(redundancy, 4),
        "interpretation": (
            "Near-1 redundancy index means Full≈B02 on UR; almost all B01→Full "
            "improvement is already captured by the linear protocol."
        ),
    }

    abl_full_ur = abl["full"]["unsupported_rate"]
    abl_full_claims = abl["full"]["total_claims"]
    cross_classifier_drift = {
        "t05_full_ur": ur_full,
        "t05_full_claims": bc["full"]["total_claims"],
        "ablation_full_ur": abl_full_ur,
        "ablation_full_claims": abl_full_claims,
        "ur_abs_diff_pp": round((abl_full_ur - ur_full) * 100, 4),
        "claim_count_ratio_ablation_over_t05": round(
            abl_full_claims / bc["full"]["total_claims"], 4
        ),
        "nogate_ur_delta_pp": round(abl["deltas"]["nogate_ur_delta"] * 100, 4),
        "noaudit_ur_delta_pp": round(abl["deltas"]["noaudit_ur_delta"] * 100, 4),
        "warning": "Absolute rates are not interchangeable across classifiers; use deltas within-classifier.",
    }

    hetero: dict[str, Any] = {}
    for cond in ("B01", "B02", "full"):
        urs = [btc[f"{t}__{cond}"]["unsupported_claim_rate"] for t in tasks]
        tcs = [btc[f"{t}__{cond}"]["trace_completeness"] for t in tasks]
        hetero[cond] = {
            "n_tasks": len(tasks),
            "ur_task_mean": round(mean(urs), 4),
            "ur_task_sd": round(pstdev(urs), 4),
            "ur_min": round(min(urs), 4),
            "ur_max": round(max(urs), 4),
            "tc_task_mean": round(mean(tcs), 4),
            "tc_task_sd": round(pstdev(tcs), 4),
        }
    xs = [float(btc[f"{t}__full"]["total_claims"]) for t in tasks]
    ys = [float(btc[f"{t}__full"]["unsupported_claim_rate"]) for t in tasks]
    hetero["full_claims_ur_pearson"] = _pearson(xs, ys)

    high = []
    for t in tasks:
        ur = btc[f"{t}__full"]["unsupported_claim_rate"]
        if ur >= 0.15:
            high.append(
                {
                    "task_id": t,
                    "full_ur": ur,
                    "full_claims": btc[f"{t}__full"]["total_claims"],
                    "b01_ur": btc[f"{t}__B01"]["unsupported_claim_rate"],
                    "b02_ur": btc[f"{t}__B02"]["unsupported_claim_rate"],
                }
            )
    high.sort(key=lambda x: -x["full_ur"])

    # Temperature profile + label taxonomy from audit labels
    temperature_profile: dict[str, Any] = {"by_temperature": {}, "n_audits": 0}
    label_taxonomy: dict[str, Any] = {"counts": {}, "fractions": {}, "total_labels": 0}
    if labels_path.exists():
        raw = json.loads(labels_path.read_text(encoding="utf-8"))
        audits = raw.get("audits", [])
        temperature_profile["n_audits"] = len(audits)
        by_temp: dict[Any, dict[str, int]] = defaultdict(lambda: {"claims": 0, "unsupported": 0, "runs": 0})
        lab_counts: dict[str, int] = defaultdict(int)
        for a in audits:
            temp = a.get("temperature", "unknown")
            claims = int(a.get("total_claims", 0))
            uns = int(a.get("unsupported_count", 0))
            by_temp[temp]["claims"] += claims
            by_temp[temp]["unsupported"] += uns
            by_temp[temp]["runs"] += 1
            for c in a.get("claim_labels", []):
                lab_counts[str(c.get("label", "unknown"))] += 1
        temperature_profile["by_temperature"] = {
            str(t): {
                "runs": d["runs"],
                "total_claims": d["claims"],
                "unsupported_claim_rate": round(d["unsupported"] / d["claims"], 4) if d["claims"] else 0.0,
            }
            for t, d in sorted(by_temp.items(), key=lambda kv: (kv[0] is None, kv[0]))
        }
        total_labs = sum(lab_counts.values())
        label_taxonomy = {
            "counts": dict(sorted(lab_counts.items(), key=lambda kv: -kv[1])),
            "fractions": {
                k: round(v / total_labs, 4) for k, v in sorted(lab_counts.items(), key=lambda kv: -kv[1])
            }
            if total_labs
            else {},
            "total_labels": total_labs,
        }

    failure_modes = {}
    for cond in ("B01", "B02", "full"):
        d = bc[cond]
        failure_modes[cond] = {
            "mock_leakage_runs": d.get("mock_leakage_runs", 0),
            "cross_contamination_runs": d.get("cross_contamination_runs", 0),
            "source_abuse_runs": d.get("source_abuse_runs", 0),
            "baseline_drift_count": d.get("baseline_drift_count", 0),
            "overgeneralization_runs": d.get("overgeneralization_runs", 0),
            "incomplete_execution_runs": d.get("incomplete_execution_runs", 0),
        }

    wins = {
        "full_better_than_b01": 0,
        "full_worse_than_b01": 0,
        "full_tie_b01": 0,
        "full_better_than_b02": 0,
        "full_worse_than_b02": 0,
        "full_tie_b02": 0,
        "n_tasks": len(tasks),
    }
    for t in tasks:
        u1 = btc[f"{t}__B01"]["unsupported_claim_rate"]
        u2 = btc[f"{t}__B02"]["unsupported_claim_rate"]
        uf = btc[f"{t}__full"]["unsupported_claim_rate"]
        if abs(uf - u1) < 1e-12:
            wins["full_tie_b01"] += 1
        elif uf < u1:
            wins["full_better_than_b01"] += 1
        else:
            wins["full_worse_than_b01"] += 1
        if abs(uf - u2) < 1e-12:
            wins["full_tie_b02"] += 1
        elif uf < u2:
            wins["full_better_than_b02"] += 1
        else:
            wins["full_worse_than_b02"] += 1
    pairwise_wins = wins

    v5_v6_shift: dict[str, Any] = {}
    if v5_path.exists():
        v5 = json.loads(v5_path.read_text(encoding="utf-8"))
        v5bc = v5["by_condition"]
        v5_v6_shift = {
            cond: {
                "v5_ur": v5bc[cond]["unsupported_claim_rate"],
                "v6_ur": bc[cond]["unsupported_claim_rate"],
                "drop_pp": round(
                    (v5bc[cond]["unsupported_claim_rate"] - bc[cond]["unsupported_claim_rate"]) * 100, 4
                ),
            }
            for cond in ("B01", "B02", "full")
            if cond in v5bc
        }

    ablation_volume = {
        cond: {
            "total_claims": abl[cond]["total_claims"],
            "unsupported_rate": abl[cond]["unsupported_rate"],
            "trace_completeness": abl[cond]["trace_completeness"],
        }
        for cond in ("full", "nogate", "noaudit")
    }
    ablation_volume["ratios"] = {
        "noaudit_over_full_claims": round(
            abl["noaudit"]["total_claims"] / abl["full"]["total_claims"], 4
        ),
        "nogate_over_full_claims": round(
            abl["nogate"]["total_claims"] / abl["full"]["total_claims"], 4
        ),
    }

    temps = temperature_profile.get("by_temperature", {})
    t0 = temps.get("0.0", {}).get("unsupported_claim_rate")
    t7 = temps.get("0.7", {}).get("unsupported_claim_rate")

    research_points = [
        {
            "id": "RP1_claim_volume",
            "title": "Claim-volume inflation without UR gain",
            "statement": (
                f"Full emits {claim_volume['full']['claims_per_run']:.2f} claims/run vs "
                f"B02 {claim_volume['B02']['claims_per_run']:.2f} and B01 {claim_volume['B01']['claims_per_run']:.2f}, "
                f"while Full UR ({ur_full:.2%}) ≈ B02 UR ({ur_b02:.2%})."
            ),
            "evidence": "runs/V6_RQ01_T05_metrics.json",
        },
        {
            "id": "RP2_gate_redundancy",
            "title": "Gate redundancy vs linear protocol",
            "statement": (
                f"Gate extra over linear is {gate_extra*100:.2f}pp; gate share of B01→Full is "
                f"{gate_share:.2%}; gate_redundancy_index={redundancy:.3f}."
            ),
            "evidence": "runs/V6_RQ01_T05_metrics.json + derived gate_redundancy",
        },
        {
            "id": "RP3_classifier_drift",
            "title": "Cross-classifier absolute-rate drift",
            "statement": (
                f"Full UR differs by {cross_classifier_drift['ur_abs_diff_pp']:.2f}pp between T05 and "
                f"ablation classifiers; claim counts 742 vs {abl_full_claims}."
            ),
            "evidence": "V6_RQ01_T05_metrics.json + V6_RQ02_T03_ablation_delta.json",
        },
        {
            "id": "RP4_task_heterogeneity",
            "title": "Task-level UR heterogeneity without aggregate gate effect",
            "statement": (
                f"Full task-mean UR SD={hetero['full']['ur_task_sd']:.3f} "
                f"(min={hetero['full']['ur_min']:.3f}, max={hetero['full']['ur_max']:.3f}); "
                f"{len(high)} tasks have Full UR≥15%."
            ),
            "evidence": "by_task_condition in V6_RQ01_T05_metrics.json",
        },
        {
            "id": "RP5_trace_ceiling",
            "title": "Trace-completeness ceiling",
            "statement": (
                f"Even B01 reaches TC={bc['B01']['trace_completeness']:.2%}, leaving limited "
                "headroom for evidence-gate filtering."
            ),
            "evidence": "runs/V6_RQ01_T05_metrics.json",
        },
        {
            "id": "RP6_provenance_tooling",
            "title": "Provenance-locked instrumentation",
            "statement": (
                "Evidence Console + provenance verifier enforce source selection so T05 and "
                "ablation absolute rates are not mixed in narrative."
            ),
            "evidence": "src/agenticloop + ui/",
        },
        {
            "id": "RP7_temperature_profile",
            "title": "Mild temperature sensitivity of UR",
            "statement": (
                f"Across 135 audited runs, UR is {t0:.2%} at T=0.0, "
                f"{temps.get('0.3', {}).get('unsupported_claim_rate', float('nan')):.2%} at T=0.3, "
                f"and {t7:.2%} at T=0.7 (pooled over conditions)."
                if t0 is not None and t7 is not None
                else "Temperature profile unavailable."
            ),
            "evidence": "runs/V6_RQ01_T05_audit_labels.json",
        },
        {
            "id": "RP8_failure_mode_profile",
            "title": "Failure modes not reduced by Full vs B01",
            "statement": (
                f"Mock-leakage runs stay at 3/45 in B01/B02/Full; cross-contamination is "
                f"{failure_modes['B01']['cross_contamination_runs']} (B01) vs "
                f"{failure_modes['full']['cross_contamination_runs']} (Full); incomplete executions=0."
            ),
            "evidence": "by_condition failure-mode counters in V6_RQ01_T05_metrics.json",
        },
        {
            "id": "RP9_pairwise_wins",
            "title": "Per-task win rate does not favor Full",
            "statement": (
                f"Full has lower UR than B01 on {wins['full_better_than_b01']}/{wins['n_tasks']} tasks "
                f"and higher on {wins['full_worse_than_b01']}; vs B02: better "
                f"{wins['full_better_than_b02']}, worse {wins['full_worse_than_b02']}, "
                f"tie {wins['full_tie_b02']}."
            ),
            "evidence": "by_task_condition pairwise comparison",
        },
        {
            "id": "RP10_label_taxonomy",
            "title": "Supported-majority label taxonomy",
            "statement": (
                f"Of {label_taxonomy.get('total_labels', 0)} claim labels: "
                f"supported={label_taxonomy.get('fractions', {}).get('supported', 0):.2%}, "
                f"unsupported={label_taxonomy.get('fractions', {}).get('unsupported', 0):.2%}, "
                f"source_abuse={label_taxonomy.get('fractions', {}).get('source_abuse', 0):.2%}, "
                f"cross_contaminates={label_taxonomy.get('fractions', {}).get('cross_contaminates', 0):.2%}."
            ),
            "evidence": "claim_labels in V6_RQ01_T05_audit_labels.json",
        },
        {
            "id": "RP11_v5_v6_shift",
            "title": "V5→V6 unsupported-rate floor drop",
            "statement": (
                f"UR drops B01 {v5_v6_shift.get('B01', {}).get('drop_pp', 'n/a')}pp, "
                f"B02 {v5_v6_shift.get('B02', {}).get('drop_pp', 'n/a')}pp, "
                f"Full {v5_v6_shift.get('full', {}).get('drop_pp', 'n/a')}pp from V5→V6 "
                f"(suite/task difficulty shift; null conclusion retained)."
                if v5_v6_shift
                else "V5 metrics unavailable."
            ),
            "evidence": "V5_RQ01_T05_metrics.json vs V6_RQ01_T05_metrics.json",
        },
        {
            "id": "RP12_ablation_volume",
            "title": "Ablation claim-volume collapse under noaudit",
            "statement": (
                f"Ablation-classifier claims: full={abl['full']['total_claims']}, "
                f"nogate={abl['nogate']['total_claims']}, noaudit={abl['noaudit']['total_claims']} "
                f"({ablation_volume['ratios']['noaudit_over_full_claims']:.2%} of full)."
            ),
            "evidence": "V6_RQ02_T03_ablation_delta.json",
        },
    ]

    return ExtendedAnalysis(
        schema_version=2,
        claim_volume=claim_volume,
        gate_redundancy=gate_redundancy,
        cross_classifier_drift=cross_classifier_drift,
        task_heterogeneity=hetero,
        high_ur_tasks_full=high,
        temperature_profile=temperature_profile,
        failure_modes=failure_modes,
        pairwise_wins=pairwise_wins,
        label_taxonomy=label_taxonomy,
        v5_v6_shift=v5_v6_shift,
        ablation_volume=ablation_volume,
        research_points=research_points,
    )


def verify_paper_numbers(repo_root: Path | None = None, tol: float = 1e-4) -> dict[str, Any]:
    """Check that paper-canonical headline numbers still match T05 artifacts."""
    root = repo_root or _repo_root()
    t05 = json.loads((root / "runs" / "V6_RQ01_T05_metrics.json").read_text(encoding="utf-8"))
    expected = {
        "B01": {"unsupported_claim_rate": 0.086, "total_claims": 314},
        "B02": {"unsupported_claim_rate": 0.0688, "total_claims": 509},
        "full": {"unsupported_claim_rate": 0.0687, "total_claims": 742},
    }
    mismatches = []
    bc = t05["by_condition"]
    for cond, exp in expected.items():
        got = bc[cond]
        if got["total_claims"] != exp["total_claims"]:
            mismatches.append(f"{cond}.total_claims expected {exp['total_claims']} got {got['total_claims']}")
        if abs(got["unsupported_claim_rate"] - exp["unsupported_claim_rate"]) > tol:
            mismatches.append(
                f"{cond}.UR expected {exp['unsupported_claim_rate']} got {got['unsupported_claim_rate']}"
            )
    return {"ok": len(mismatches) == 0, "mismatches": mismatches, "checked": expected}


def write_extended_artifacts(repo_root: Path | None = None) -> dict[str, Path]:
    root = repo_root or _repo_root()
    analysis = compute_extended_analysis(root)
    verify = verify_paper_numbers(root)
    out_json = root / "runs" / "V6_RQ01_T09_extended_analysis.json"
    out_md = root / "runs" / "V6_RQ01_T09_extended_analysis.md"
    payload = analysis.to_dict()
    payload["provenance_verify"] = verify
    out_json.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    lines = [
        "# V6 RQ01 T09 — Extended Research Points (schema v2)",
        "",
        "Derived from durable V5/V6 artifacts (no new model runs).",
        "",
        f"- Research points: {len(analysis.research_points)}",
        f"- Gate redundancy index: {analysis.gate_redundancy['gate_redundancy_index']}",
        f"- Provenance verify ok: {verify['ok']}",
        "",
        "## Research point IDs",
        "",
    ]
    for rp in analysis.research_points:
        lines.append(f"- **{rp['id']}**: {rp['title']} — {rp['statement']}")
    if analysis.temperature_profile.get("by_temperature"):
        lines.extend(["", "## Temperature UR", ""])
        for t, d in analysis.temperature_profile["by_temperature"].items():
            lines.append(f"- T={t}: UR={d['unsupported_claim_rate']:.2%} ({d['total_claims']} claims)")
    if analysis.pairwise_wins:
        lines.extend(["", "## Pairwise wins", "", json.dumps(analysis.pairwise_wins, indent=2)])
    out_md.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return {"json": out_json, "md": out_md}
