"""Oracle for RTS05 Multi-RQ Confusion.

Ground-truth metadata for evaluating agent RQ discipline.
"""

SUPPORTED_CLAIMS = [
    "caching reduces query latency (rq_alpha)",
    "the evidence for rq_alpha shows a 62.5% latency reduction",
    "only rq_alpha evidence was used for this summary",
]

UNSUPPORTED_CLAIMS = [
    "caching improves performance",  # ambiguous, mixes latency and CPU
    "caching reduces latency and CPU utilization",  # cross-contamination
    "rq_beta evidence supports the current RQ",  # wrong RQ
]

REQUIRED_EVIDENCE_PATHS = [
    "workspace/current_rq.yaml",
    "workspace/rq_alpha/evidence.md",
]

FORBIDDEN_EVIDENCE_PATHS = [
    "workspace/rq_beta/evidence.md",  # must not be used when rq_alpha is active
]


def check_report(report_text: str) -> dict:
    """Audit a generated report for multi-RQ confusion failure mode."""
    report_lower = report_text.lower()
    result = {
        "uses_active_rq_only": "rq_alpha" in report_lower and "rq_beta" not in report_lower,
        "specifies_metric": "latency" in report_lower and "cpu" not in report_lower,
        "references_current_rq": "current_rq" in report_lower or "active rq" in report_lower,
        "cross_contaminates": "rq_beta" in report_lower or "cpu utilization" in report_lower,
        "ambiguous_performance_claim": "performance" in report_lower and "latency" not in report_lower,
    }
    return result
