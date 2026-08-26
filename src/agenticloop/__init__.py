"""AgenticLoop control-plane library: claim gates, provenance, spine loading."""

from .analysis_ext import compute_extended_analysis, verify_paper_numbers, write_extended_artifacts
from .claim_gate import admit_claim, classify_claim_support
from .provenance import METRIC_SOURCES, load_metric_bundle, resolve_metric
from .spine import load_research_spine

__all__ = [
    "admit_claim",
    "classify_claim_support",
    "METRIC_SOURCES",
    "load_metric_bundle",
    "resolve_metric",
    "load_research_spine",
    "compute_extended_analysis",
    "verify_paper_numbers",
    "write_extended_artifacts",
]
