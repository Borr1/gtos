"""Subagent/goal starter generation from Context OS packs."""

from __future__ import annotations

from typing import Any

from src.gtos_context_os.session_state import (
    summarize_active_state_payload,
    summarize_continuation_cursor_payload,
)


def build_starter_prompt(pack: dict[str, Any], *, lane: str = "general") -> str:
    route = pack.get("route")
    lines = [
        f"Context OS starter for lane: {lane}",
        "",
        f"Task: {pack['task']}",
        f"Profile: {pack.get('profile', 'standard')}",
    ]
    if route:
        lines.append(f"Route: {route}")
    checklist = pack.get("doctrine_checklist") or {}
    health = pack.get("context_health") or {}
    posture = health.get("operating_posture") or {}
    lines.extend(
        [
            "",
            "Execution posture:",
            f"- lane_posture: {checklist.get('lane_posture')}",
            f"- action_rule: {checklist.get('operating_posture')}",
            f"- health_rule: {posture.get('agent_instruction')}",
            "- Use this pack to move the work forward: open exact sources, patch/build/verify when evidence supports it.",
            "- Preserve evidence class labels and source-gap dispositions while still producing concrete repairs or exact next blockers.",
            "- Hydrate raw JSONL by exact route/source pointer when needed; keep broad search focused on clean code/context roots.",
            "- Return exact files, rows/counts when applicable, and concrete repair recommendations.",
            "",
            "Doctrine checklist:",
        ]
    )
    lines.extend(
        [
            "",
            "Context intelligence state:",
            f"- health_status: {health.get('status')}",
        ]
    )
    if health.get("warnings"):
        for warning in health.get("warnings", [])[:8]:
            lines.append(f"- warning: {warning}")
    sessions = health.get("session_capsules") or {}
    if sessions.get("latest"):
        latest = sessions["latest"]
        lines.append(f"- latest_session_capsule: {latest.get('path')}")
        if latest.get("summary"):
            lines.append(f"- latest_session_summary: {str(latest.get('summary'))[:500]}")
    else:
        lines.append("- latest_session_capsule: none")
    if pack.get("recent_session_capsules"):
        lines.extend(["", "Recent continuity capsules, verify before use:"])
        for capsule in pack["recent_session_capsules"][:5]:
            lines.append(f"- {capsule['path']} ({capsule.get('generated_at_utc')}; {capsule.get('status')})")
    active_state = pack.get("active_session_state") or {}
    latest_state = active_state.get("latest") or {}
    if latest_state:
        lines.extend(["", "Active session state, verify before use:"])
        lines.append(f"- {latest_state.get('path')} ({latest_state.get('parse_status')})")
        payload = latest_state.get("payload")
        if isinstance(payload, dict):
            for key, value in summarize_active_state_payload(payload).items():
                if value not in (None, "", [], {}):
                    lines.append(f"- {key}: {str(value)[:500]}")
    cursor = pack.get("continuation_cursor") or {}
    latest_cursor = cursor.get("latest") or {}
    if latest_cursor:
        lines.extend(["", "Continuation cursor, verify before use:"])
        lines.append(f"- {latest_cursor.get('path')} ({latest_cursor.get('parse_status')})")
        payload = latest_cursor.get("payload")
        if isinstance(payload, dict):
            for key, value in summarize_continuation_cursor_payload(payload).items():
                if value not in (None, "", [], {}):
                    lines.append(f"- {key}: {str(value)[:500]}")
    for rule in checklist.get("mandatory_rules", [])[:10]:
        lines.append(f"- {rule}")
    lines.extend(["", "Read-first anchors:"])
    for doc in (pack.get("anchors") or [])[:8]:
        lines.append(f"- {doc['path']} ({doc['authority_tier']}; {doc['evidence_class']})")
    if pack.get("route_overview"):
        lines.extend(["", "Route read-first artifacts:"])
        for doc in (pack["route_overview"].get("read_first") or [])[:10]:
            lines.append(f"- {doc['path']} ({doc['authority_tier']}; {doc['evidence_class']})")
    lines.extend(["", "Task-relevant hits:"])
    for doc in (pack.get("relevant_hits") or [])[:12]:
        lines.append(f"- {doc['path']} ({doc['authority_tier']}; {doc['evidence_class']})")
    symbol_hits = (pack.get("symbol_hits") or {}).get("hits") or []
    if symbol_hits:
        lines.extend(["", "Live symbol hits, open exact source before claims:"])
        for hit in symbol_hits[:8]:
            lines.append(
                f"- {hit.get('path')}:{hit.get('line')} {hit.get('qualname')} "
                f"({hit.get('kind')}; score={hit.get('score')})"
            )
    if pack.get("memory_hits"):
        lines.extend(["", "Memory recall hits, verify before use:"])
        for doc in pack["memory_hits"][:5]:
            lines.append(f"- {doc['path']} ({doc['freshness']})")
    brain = pack.get("second_brain") or {}
    if brain.get("hits"):
        lines.extend(["", "Second-brain hits, retrieval intelligence only:"])
        for hit in brain["hits"][:5]:
            lines.append(f"- {hit['path']} ({hit['status']}; {hit['freshness']})")
    return "\n".join(lines).rstrip() + "\n"
