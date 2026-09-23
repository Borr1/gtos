"""Authority and evidence classification for GTOS context retrieval."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


PLATINUM_CURRENT_AUTHORITY = "platinum_current_disk_authority"
GOLD_CODE_CONFIG_TEST = "gold_active_code_config_test"
GOLD_ROUTE_SUMMARY = "gold_route_summary_manifest"
SILVER_ROUTE_ARTIFACT = "silver_route_artifact"
BRONZE_CHAT_MEMORY = "bronze_chat_or_memory"
COLD_RAW_EVIDENCE = "cold_raw_evidence"
UNKNOWN = "unknown"


CURRENT_AUTHORITY_PATHS = {
    ".context/LIVE_STATE.md",
    ".context/00_core/current_vnext_system_map.md",
    ".context/00_core/current_vnext_system_map.json",
    ".context/00_core/current_repo_reading_order.md",
    ".context/00_core/quick_reference_card.md",
    ".context/00_core/repo_cleanup_and_staleness_policy.md",
    ".context/00_core/research_operating_doctrine.md",
    ".context/00_core/goal_session_research_discipline.md",
    ".context/00_core/gtos_context_os.md",
    ".context/00_core/gtos_second_brain.md",
    ".context/00_core/final_moonshot_central_orchestrator_successor_brief.md",
    ".context/00_core/final_moonshot_post_hard_halt_research_plan.md",
    ".context/00_core/final_moonshot_goal_session_execution_architecture.md",
    "AGENTS.md",
    "CLAUDE.md",
    "pyproject.toml",
}

ROUTE_SUMMARY_TOKENS = (
    "SUMMARY",
    "MANIFEST",
    "VERIFICATION",
    "VERIFY",
    "AUDIT",
    "DOSSIER",
    "REPORT",
    "RESULT",
    "PLAN",
    "README",
)

RAW_EVIDENCE_SUFFIXES = {".jsonl", ".parquet", ".feather", ".pkl", ".sqlite", ".db"}
RAW_EVIDENCE_PARTS = {
    "shadow_logs",
    "data",
    "pipeline_state",
    "logs",
    "scratch",
}

CHAT_MEMORY_PARTS = {
    ".codex",
    ".claude",
    "rollout_summaries",
    "sessions",
    "attachments",
}


@dataclass(frozen=True)
class ContextClassification:
    """Classification attached to one indexed context item."""

    authority_tier: str
    evidence_class: str
    freshness: str
    doc_type: str
    route: str | None = None


def normalize_relative_path(path: str | Path) -> str:
    normalized = Path(path).as_posix()
    while normalized.startswith("./"):
        normalized = normalized[2:]
    return normalized


def route_name(relative_path: str) -> str | None:
    parts = Path(relative_path).parts
    if len(parts) >= 3 and parts[0] == "research" and parts[1] == "operations":
        return parts[2]
    return None


def _contains_any(parts: tuple[str, ...], values: set[str]) -> bool:
    return any(part in values for part in parts)


def classify_path(path: str | Path, text_sample: str = "") -> ContextClassification:
    """Classify a repo-relative path for retrieval ranking.

    The classifier is intentionally simple and deterministic.  It ranks current
    disk authority and active code above summaries, summaries above generic
    route artifacts, and cold raw evidence below all of them.
    """

    rel = normalize_relative_path(path)
    rel_path = Path(rel)
    parts = rel_path.parts
    suffix = rel_path.suffix.lower()
    upper_name = rel_path.name.upper()
    lowered = f"{rel}\n{text_sample[:4000]}".lower()
    route = route_name(rel)

    if rel in CURRENT_AUTHORITY_PATHS:
        return ContextClassification(
            authority_tier=PLATINUM_CURRENT_AUTHORITY,
            evidence_class="current_context_authority",
            freshness="current_or_regenerated",
            doc_type="current_authority",
            route=route,
        )

    if suffix in RAW_EVIDENCE_SUFFIXES or _contains_any(parts, RAW_EVIDENCE_PARTS):
        return ContextClassification(
            authority_tier=COLD_RAW_EVIDENCE,
            evidence_class="raw_or_large_evidence_pointer",
            freshness="cold_unless_route_manifest_requires",
            doc_type="raw_evidence",
            route=route,
        )

    if _contains_any(parts, CHAT_MEMORY_PARTS):
        return ContextClassification(
            authority_tier=BRONZE_CHAT_MEMORY,
            evidence_class="chat_memory_or_transcript",
            freshness="historical_until_verified_from_disk",
            doc_type="chat_memory",
            route=route,
        )

    if parts and parts[0] in {"src", "scripts", "tests", "config"}:
        return ContextClassification(
            authority_tier=GOLD_CODE_CONFIG_TEST,
            evidence_class="active_code_config_or_test",
            freshness="current_head_working_surface",
            doc_type=parts[0],
            route=route,
        )

    if route is not None:
        if any(token in upper_name for token in ROUTE_SUMMARY_TOKENS):
            tier = GOLD_ROUTE_SUMMARY
            doc_type = "route_summary_or_manifest"
            freshness = "route_current_if_referenced_by_live_state_or_manifest"
        else:
            tier = SILVER_ROUTE_ARTIFACT
            doc_type = "route_artifact"
            freshness = "route_artifact_verify_against_current_manifest"
        evidence_class = "route_evidence"
        if "broker-real" in lowered or "broker_real" in lowered or "broker truth" in lowered:
            evidence_class = "broker_real_route_evidence"
        elif "source-bound" in lowered or "source_bound" in lowered:
            evidence_class = "source_bound_route_evidence"
        elif "proxy" in lowered or "reconstructed" in lowered:
            evidence_class = "proxy_or_reconstructed_route_evidence"
        elif "replay" in lowered:
            evidence_class = "replay_route_evidence"
        return ContextClassification(
            authority_tier=tier,
            evidence_class=evidence_class,
            freshness=freshness,
            doc_type=doc_type,
            route=route,
        )

    if parts and parts[0] == ".context":
        return ContextClassification(
            authority_tier=GOLD_ROUTE_SUMMARY,
            evidence_class="context_document",
            freshness="verify_against_live_state",
            doc_type="context_doc",
            route=route,
        )

    return ContextClassification(
        authority_tier=UNKNOWN,
        evidence_class="unclassified",
        freshness="verify_before_use",
        doc_type="other",
        route=route,
    )


AUTHORITY_WEIGHT = {
    PLATINUM_CURRENT_AUTHORITY: 100,
    GOLD_CODE_CONFIG_TEST: 80,
    GOLD_ROUTE_SUMMARY: 75,
    SILVER_ROUTE_ARTIFACT: 55,
    BRONZE_CHAT_MEMORY: 25,
    COLD_RAW_EVIDENCE: 10,
    UNKNOWN: 1,
}
