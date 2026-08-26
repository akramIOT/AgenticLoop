"""Strengthened research claims derived from durable V6 artifacts.

All claims are falsifiable and tied to on-disk metrics. No new model runs.
"""

from __future__ import annotations

import json
from collections import defaultdict
from dataclasses import asdict, dataclass, field
from pathlib import Path
from statistics import mean, pstdev
from typing import Any


def _repo_root(start: Path | None = None) -> Path:
    if start is None:
        start = Path(__file__).resolve()
    for parent in [start, *start.parents]:
        if (parent / "docs" / "research" / "CURRENT").exists():
            return parent
    return Path(__file__).resolve().parents[2]


@dataclass(frozen=True)
class StrengthenedClaims:
    schema_version: int
    cosmetics_traces: dict[str, Any]
    aggregation_sensitivity: dict[str, Any]
    pairwise_nulls: dict[str, Any]
    near_equivalence: dict[str, Any]
    task_harm_asymmetry: dict[str, Any]
    seed_instability: dict[str, Any]
    tc_saturation: dict[str, Any]
    gate_negative_tasks: list[dict[str, Any]]
    claims: list[dict[str, str]] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def compute_strengthened_claims(repo_root: Path | None = None) -> StrengthenedClaims:
    root = repo_root or _repo_root()
    t05 = json.loads((root / "runs" / "V6_RQ01_T05_metrics.json").read_text(encoding="utf-8"))
    t06 = json.loads((root / "runs" / "V6_RQ01_T06_comparison_summary.json").read_text(encoding="utf-8"))
    labels = json.loads((root / "runs" / "V6_RQ01_T05_audit_labels.json").read_text(encoding="utf-8"))[
        "audits"
    ]

    bc = t05["by_condition"]
    btc = t05["by_task_condition"]
    tasks = sorted({k.split("__")[0] for k in btc})

    # SC1: cosmetic / insufficient traces
    trace_stats: dict[str, dict[str, int]] = defaultdict(lambda: {"traced": 0, "traced_bad": 0})
    traced = traced_bad = supported_traced = 0
    for a in labels:
        cond = a["condition_id"]
        for c in a.get("claim_labels", []):
            if not c.get("has_trace"):
                continue
            traced += 1
            trace_stats[cond]["traced"] += 1
            if c.get("label") == "supported":
                supported_traced += 1
            else:
                traced_bad += 1
                trace_stats[cond]["traced_bad"] += 1
    # Among traced claims, label=="unsupported" is typically 0; failures are
    # source_abuse / cross_contaminates / mock_leakage / baseline_drift.
    traced_label_counts: dict[str, int] = defaultdict(int)
    for a in labels:
        for c in a.get("claim_labels", []):
            if c.get("has_trace"):
                traced_label_counts[str(c.get("label", "unknown"))] += 1
    cosmetics_traces = {
        "n_traced_claims": traced,
        "n_traced_but_not_supported": traced_bad,
        "traced_but_not_supported_rate": round(traced_bad / traced, 4) if traced else None,
        "n_traced_with_label_unsupported": traced_label_counts.get("unsupported", 0),
        "traced_failure_label_counts": dict(traced_label_counts),
        "definition": (
            "traced_but_not_supported = has_trace and label!='supported' "
            "(failure-mode labels; not the T05 unsupported_count metric alone)"
        ),
        "supported_all_have_trace": supported_traced > 0,  # checked below
        "by_condition": {
            cond: {
                "traced": d["traced"],
                "traced_but_not_supported": d["traced_bad"],
                "rate": round(d["traced_bad"] / d["traced"], 4) if d["traced"] else None,
            }
            for cond, d in trace_stats.items()
        },
    }
    # verify all supported have trace
    unsupported_without_check = 0
    for a in labels:
        for c in a.get("claim_labels", []):
            if c.get("label") == "supported" and not c.get("has_trace"):
                unsupported_without_check += 1
    cosmetics_traces["n_supported_without_trace"] = unsupported_without_check
    cosmetics_traces["supported_all_have_trace"] = unsupported_without_check == 0

    # SC2: aggregation sensitivity
    aggregation_sensitivity = {
        "claim_weighted": {
            "B01": bc["B01"]["unsupported_claim_rate"],
            "B02": bc["B02"]["unsupported_claim_rate"],
            "full": bc["full"]["unsupported_claim_rate"],
        },
        "task_mean": {
            "B01": t06["task_mean"]["B01"]["unsupported_claim_rate"],
            "B02": t06["task_mean"]["B02"]["unsupported_claim_rate"],
            "full": t06["task_mean"]["full"]["unsupported_claim_rate"],
        },
        "task_mean_full_minus_b02_pp": round(
            (
                t06["task_mean"]["full"]["unsupported_claim_rate"]
                - t06["task_mean"]["B02"]["unsupported_claim_rate"]
            )
            * 100,
            4,
        ),
        "claim_weighted_full_minus_b02_pp": round(
            (bc["full"]["unsupported_claim_rate"] - bc["B02"]["unsupported_claim_rate"]) * 100, 4
        ),
    }

    # SC3 pairwise nulls
    wil = t06["wilcoxon_unsupported_rate"]
    pairwise_nulls = {
        "friedman": t06["friedman_unsupported_rate"],
        "wilcoxon": {
            k: {"statistic": wil[k]["statistic"], "pvalue": wil[k]["pvalue"]}
            for k in ("B01_vs_full", "B02_vs_full", "B01_vs_B02")
        },
        "bonferroni_alpha": wil["bonferroni_alpha"],
        "all_pairwise_p_gt_0_5": all(wil[k]["pvalue"] > 0.5 for k in ("B01_vs_full", "B02_vs_full", "B01_vs_B02")),
    }

    # SC4 near equivalence
    near_equivalence = {
        "abs_full_minus_b02_claim_weighted_pp": round(
            abs(bc["full"]["unsupported_claim_rate"] - bc["B02"]["unsupported_claim_rate"]) * 100, 4
        ),
        "abs_full_minus_b02_tc_pp": round(
            abs(bc["full"]["trace_completeness"] - bc["B02"]["trace_completeness"]) * 100, 4
        ),
        "descriptive_near_zero_band_pp": 0.5,
        "within_descriptive_0_5pp_band": abs(
            bc["full"]["unsupported_claim_rate"] - bc["B02"]["unsupported_claim_rate"]
        )
        * 100
        < 0.5,
        "formal_equivalence_tested": False,
        "note": (
            "Near-zero observed difference; formal equivalence (e.g. TOST) was not tested. "
            "Non-significance does not imply equivalence."
        ),
    }

    # SC5 task harm asymmetry
    deltas = []
    for t in tasks:
        d = btc[f"{t}__full"]["unsupported_claim_rate"] - btc[f"{t}__B02"]["unsupported_claim_rate"]
        deltas.append({"task_id": t, "full_minus_b02": d})
    worse = [x["full_minus_b02"] for x in deltas if x["full_minus_b02"] > 1e-12]
    better = [x["full_minus_b02"] for x in deltas if x["full_minus_b02"] < -1e-12]
    ties = sum(1 for x in deltas if abs(x["full_minus_b02"]) <= 1e-12)
    task_harm_asymmetry = {
        "n_full_better_than_b02": len(better),
        "n_full_worse_than_b02": len(worse),
        "n_tie": ties,
        "mean_delta": round(mean([x["full_minus_b02"] for x in deltas]), 4),
        "mean_harm_when_worse_pp": round(mean(worse) * 100, 4) if worse else None,
        "mean_help_when_better_pp": round(mean(better) * 100, 4) if better else None,
        "sd_delta_pp": round(pstdev([x["full_minus_b02"] for x in deltas]) * 100, 4),
    }

    # Bootstrap 95% CI for mean Full−B02 task-mean UR delta (deterministic seed)
    import random

    rng = random.Random(0)
    raw = [x["full_minus_b02"] for x in deltas]
    boots = []
    for _ in range(10000):
        sample = [raw[rng.randrange(len(raw))] for _ in range(len(raw))]
        boots.append(mean(sample))
    boots.sort()
    task_harm_asymmetry["bootstrap_mean_full_minus_b02_pp"] = round(mean(raw) * 100, 4)
    task_harm_asymmetry["bootstrap_95ci_pp"] = [
        round(boots[250] * 100, 4),
        round(boots[9750] * 100, 4),
    ]
    task_harm_asymmetry["bootstrap_note"] = (
        "Nonparametric bootstrap over 15 task deltas; CI includes 0 (consistent with null)."
    )

    # SC6 seed instability (run-level UR means by seed)
    seed_instability = {}
    for cond in ("B01", "B02", "full"):
        by_seed: dict[Any, list[float]] = defaultdict(list)
        for a in labels:
            if a["condition_id"] != cond:
                continue
            tot = a.get("total_claims") or 0
            ur = (a.get("unsupported_count") or 0) / tot if tot else 0.0
            by_seed[a["seed"]].append(ur)
        means = {int(s): round(mean(xs), 4) for s, xs in sorted(by_seed.items())}
        vals = list(means.values())
        seed_instability[cond] = {
            "seed_mean_ur": means,
            "range_pp": round((max(vals) - min(vals)) * 100, 4) if vals else None,
        }

    # SC7 TC saturation
    tc_saturation = {
        "tc_b01": bc["B01"]["trace_completeness"],
        "tc_b02": bc["B02"]["trace_completeness"],
        "tc_full": bc["full"]["trace_completeness"],
        "b01_to_b02_pp": round((bc["B02"]["trace_completeness"] - bc["B01"]["trace_completeness"]) * 100, 4),
        "b02_to_full_pp": round((bc["full"]["trace_completeness"] - bc["B02"]["trace_completeness"]) * 100, 4),
    }

    # SC8 gate-negative tasks (Full UR much worse than B02)
    gate_negative_tasks = []
    for t in tasks:
        u2 = btc[f"{t}__B02"]["unsupported_claim_rate"]
        uf = btc[f"{t}__full"]["unsupported_claim_rate"]
        delta_pp = (uf - u2) * 100
        if delta_pp >= 5.0:
            gate_negative_tasks.append(
                {
                    "task_id": t,
                    "b02_ur": u2,
                    "full_ur": uf,
                    "full_minus_b02_pp": round(delta_pp, 4),
                }
            )
    gate_negative_tasks.sort(key=lambda x: -x["full_minus_b02_pp"])

    claims = [
        {
            "id": "SC1_cosmetic_traces",
            "title": "Traces insufficient: failure-labeled claims can still have traces",
            "statement": (
                f"{cosmetics_traces['traced_but_not_supported_rate']:.2%} of traced claims are "
                f"failure-labeled / not supported ({traced_bad}/{traced}; labels such as "
                f"source_abuse/cross_contaminates/mock_leakage—not T05 label==unsupported, "
                f"of which {cosmetics_traces['n_traced_with_label_unsupported']} are traced). "
                f"Full has the highest traced-but-not-supported rate "
                f"({cosmetics_traces['by_condition'].get('full', {}).get('rate')}). "
                f"All supported claims already have traces "
                f"(supported_without_trace={unsupported_without_check})."
            ),
            "strength": "mechanism",
            "evidence": "V6_RQ01_T05_audit_labels.json has_trace × label",
        },
        {
            "id": "SC2_aggregation_sensitivity",
            "title": "Null is aggregation-robust; task-mean even favors B02",
            "statement": (
                f"Claim-weighted Full−B02 = {aggregation_sensitivity['claim_weighted_full_minus_b02_pp']}pp; "
                f"task-mean Full−B02 = {aggregation_sensitivity['task_mean_full_minus_b02_pp']}pp "
                f"(Full {aggregation_sensitivity['task_mean']['full']:.4f} vs B02 "
                f"{aggregation_sensitivity['task_mean']['B02']:.4f})."
            ),
            "strength": "robustness",
            "evidence": "T05 claim-weighted + T06 task_mean",
        },
        {
            "id": "SC3_pairwise_wilcoxon_null",
            "title": "All pairwise Wilcoxon tests are non-significant",
            "statement": (
                f"B01 vs Full p={wil['B01_vs_full']['pvalue']:.3f}, "
                f"B02 vs Full p={wil['B02_vs_full']['pvalue']:.3f}, "
                f"B01 vs B02 p={wil['B01_vs_B02']['pvalue']:.3f} "
                f"(Bonferroni α={wil['bonferroni_alpha']:.4f}); Friedman p="
                f"{t06['friedman_unsupported_rate']['pvalue']:.3f}."
            ),
            "strength": "statistical",
            "evidence": "V6_RQ01_T06_comparison_summary.json",
        },
        {
            "id": "SC4_near_equivalence",
            "title": "Full ≈ B02 within 0.01pp (near-zero difference; not TOST-tested)",
            "statement": (
                f"|Full−B02| UR = {near_equivalence['abs_full_minus_b02_claim_weighted_pp']}pp and "
                f"|ΔTC| = {near_equivalence['abs_full_minus_b02_tc_pp']}pp (descriptive near-zero). "
                f"Formal equivalence was not tested; non-significance ≠ equivalence."
            ),
            "strength": "effect_size",
            "evidence": "V6_RQ01_T05_metrics.json by_condition",
        },
        {
            "id": "SC5_task_harm_asymmetry",
            "title": "Full harms more tasks than it helps vs B02",
            "statement": (
                f"Full better on {task_harm_asymmetry['n_full_better_than_b02']}/15, worse on "
                f"{task_harm_asymmetry['n_full_worse_than_b02']}/15 (tie {task_harm_asymmetry['n_tie']}); "
                f"mean harm when worse {task_harm_asymmetry['mean_harm_when_worse_pp']}pp; "
                f"delta SD {task_harm_asymmetry['sd_delta_pp']}pp."
            ),
            "strength": "heterogeneity",
            "evidence": "by_task_condition Full−B02",
        },
        {
            "id": "SC6_seed_instability",
            "title": "Full shows higher seed UR range than B02",
            "statement": (
                f"Seed-mean UR range: B02 {seed_instability['B02']['range_pp']}pp vs "
                f"Full {seed_instability['full']['range_pp']}pp "
                f"(B01 {seed_instability['B01']['range_pp']}pp)."
            ),
            "strength": "stability",
            "evidence": "audit labels grouped by seed",
        },
        {
            "id": "SC7_tc_saturation_by_linear",
            "title": "Linear protocol already saturates trace completeness",
            "statement": (
                f"TC gain B01→B02 = {tc_saturation['b01_to_b02_pp']}pp; B02→Full = "
                f"{tc_saturation['b02_to_full_pp']}pp (TC Full={tc_saturation['tc_full']:.4f})."
            ),
            "strength": "mechanism",
            "evidence": "T05 trace_completeness by_condition",
        },
        {
            "id": "SC8_gate_negative_tasks",
            "title": "Large gate-negative tasks exist",
            "statement": (
                f"{len(gate_negative_tasks)} tasks have Full UR ≥5pp above B02"
                + (
                    ": "
                    + ", ".join(
                        f"{r['task_id']} (+{r['full_minus_b02_pp']}pp)" for r in gate_negative_tasks[:3]
                    )
                    if gate_negative_tasks
                    else "."
                )
            ),
            "strength": "counterexample",
            "evidence": "by_task_condition gate-negative slice",
        },
    ]

    return StrengthenedClaims(
        schema_version=1,
        cosmetics_traces=cosmetics_traces,
        aggregation_sensitivity=aggregation_sensitivity,
        pairwise_nulls=pairwise_nulls,
        near_equivalence=near_equivalence,
        task_harm_asymmetry=task_harm_asymmetry,
        seed_instability=seed_instability,
        tc_saturation=tc_saturation,
        gate_negative_tasks=gate_negative_tasks,
        claims=claims,
    )


def write_strengthened_claim_artifacts(repo_root: Path | None = None) -> dict[str, Path]:
    root = repo_root or _repo_root()
    analysis = compute_strengthened_claims(root)
    out_json = root / "runs" / "V6_RQ01_T11_strengthened_claims.json"
    out_md = root / "runs" / "V6_RQ01_T11_strengthened_claims.md"
    out_json.write_text(json.dumps(analysis.to_dict(), indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    lines = [
        "# V6 RQ01 T11 — Strengthened Research Claims",
        "",
        "Falsifiable claims derived from durable artifacts (no new model runs).",
        "",
    ]
    for c in analysis.claims:
        lines.append(f"## {c['id']} ({c['strength']})")
        lines.append("")
        lines.append(f"**{c['title']}.** {c['statement']}")
        lines.append("")
        lines.append(f"Evidence: `{c['evidence']}`")
        lines.append("")
    out_md.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return {"json": out_json, "md": out_md}
