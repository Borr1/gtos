"""Doctrine checklist generation for Context OS packs."""

from __future__ import annotations

from typing import Any


PROFILE_QUERY_TERMS = {
    "standard": "",
    "implementation": "src tests config scripts verifier",
    "research": "research operations summary manifest verifier source evidence",
    "ultimate": (
        "current disk authority route summary manifest verifier source evidence "
        "selector scheduler risk lifecycle execution replay context hygiene"
    ),
    "replay-repair": (
        "replay behavior ledger source-bound executable parity selector scheduler "
        "risk order lifecycle exit verifier holdout stress"
    ),
    "selector-scheduler": (
        "selector scheduler admission ranking reallocation candidate packet "
        "source completeness probability expected net r"
    ),
    "cost-order": (
        "broker calibrated cost spread slippage commission swap order policy "
        "limit fillability fallback refused source gap"
    ),
    "lifecycle-exit": (
        "pending lifecycle delay skip reduce cancel replace expire same-symbol "
        "exit profit harvest stop target geometry"
    ),
    "verifier-audit": (
        "verifier audit artifact manifest prompt hardening diff check fatal "
        "authority leakage row count"
    ),
    "context-cleanup": (
        "context cleanup stale authority raw evidence manifest archive cold pointer "
        "current head source gap"
    ),
}


def profile_query_terms(profile: str) -> str:
    return PROFILE_QUERY_TERMS.get(profile, "")


def doctrine_checklist(*, task: str, profile: str, route: str | None = None) -> dict[str, Any]:
    lane = profile if profile in PROFILE_QUERY_TERMS else "standard"
    return {
        "schema_version": "gtos_context_doctrine_checklist_v1",
        "task": task,
        "route": route,
        "profile": profile,
        "lane_posture": lane_posture(lane),
        "operating_posture": (
            "Act decisively from current disk evidence. Use the pack as a source map, "
            "open exact files, patch/build/verify when evidence supports it, and keep "
            "claim quality explicit without treating context boundaries as brakes."
        ),
        "mandatory_rules": [
            "use current disk authority as the launch point; verify chat, memory, handoffs, and raw summaries against it",
            "use Context OS packs as retrieval maps and source pointers, then open exact files and act",
            "preserve evidence classes while moving work forward: broker-real, replay, proxy, source-bound, diagnostic, live/final",
            "keep the full underlying surface visible when narrowing is useful for execution",
            "turn raw-data gaps into exact approved-root, route-pointer, or capture requirements",
            "repair same-evidence-class blockers when source evidence supports a repair",
            "write sourced continuity capsules or writeback proposals for durable findings",
        ],
        "anti_staleness": [
            "refresh LIVE_STATE before substantial work",
            "reuse or rebuild a fresh Context OS catalog before pack generation",
            "when freshness reports stale HEAD or authority anchors, refresh context before relying on the pack",
            "treat Codex/Claude memory hits as bronze recall until verified from current disk",
        ],
        "completion_questions": [
            "What source files/artifacts did the pack point to, and which were actually opened?",
            "Which evidence class is each claim using?",
            "What exact raw/cold evidence was not hydrated, and why?",
            "What changed in code, data, route artifacts, or decisions?",
            "What is the next executable repair or exact non-executable/source-gap classification?",
        ],
    }


def lane_posture(profile: str) -> str:
    if profile in {"implementation", "selector-scheduler", "cost-order", "lifecycle-exit"}:
        return "production-code-or-replay-implementation: patch code/config/tests when disk evidence supports it"
    if profile in {"research", "replay-repair"}:
        return "research-repair: compute strongest source-safe result, repair source gaps, preserve splits and evidence class"
    if profile == "verifier-audit":
        return "adversarial-audit: prioritize verifier truth, artifact consistency, row-counts, and authority leakage"
    if profile == "context-cleanup":
        return "context-hygiene: demote stale/raw evidence safely while preserving current authority and pointers"
    if profile == "ultimate":
        return "ultimate-system: broad, source-bound, repair-oriented, convert context into action, keep the full surface visible"
    return "standard: current-disk-first retrieval and exact source verification"
