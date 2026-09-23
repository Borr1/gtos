"""Context intelligence health checks for GTOS Context OS."""

from __future__ import annotations

import sqlite3
import subprocess
from pathlib import Path
from typing import Any

from src.gtos_context_os.catalog import DEFAULT_DB_PATH, catalog_freshness, catalog_stats, utc_now
from src.gtos_context_os.second_brain import second_brain_status
from src.gtos_context_os.session import session_capsule_status


REQUIRED_ANCHORS = (
    ".context/LIVE_STATE.md",
    ".context/00_core/current_vnext_system_map.md",
    ".context/00_core/current_repo_reading_order.md",
    ".context/00_core/gtos_context_os.md",
    ".context/00_core/gtos_second_brain.md",
)
PROCESS_KINDS = {
    "context_build": ("scripts/gtos_context.py build", "gtos_context.py build"),
    "context_mcp_stdio": ("gtos_context.py --repo", "gtos_context.py mcp-stdio"),
    "context_test": ("pytest tests/test_gtos_context_os", "tests/test_gtos_context_os.py"),
    "broad_replay": ("run_broad_live_as_if_replay", "BROAD_LIVE_AS_IF_REPLAY"),
    "route_verifier": ("verify_denominator_to_deployment", "audit_goal_route_artifacts"),
}


def context_intelligence_health(
    *,
    repo: Path | str = ".",
    db_path: Path | str = DEFAULT_DB_PATH,
    second_brain_root: Path | str | None = None,
    session_capsule_limit: int = 5,
) -> dict[str, Any]:
    """Return a compact health/continuity view for context consumers."""

    repo_path = Path(repo).resolve()
    db = repo_path / db_path if not Path(db_path).is_absolute() else Path(db_path)
    warnings: list[str] = []
    actions: list[str] = []
    freshness = catalog_freshness(db_path=db_path, repo=repo_path)
    stats: dict[str, Any] | None = None
    if not freshness.get("fresh"):
        warnings.append("catalog_not_fresh")
        actions.append("run python3 scripts/gtos_context.py build before relying on packs")
    if db.exists():
        try:
            stats = catalog_stats(db_path=db_path, repo=repo_path)
        except (OSError, sqlite3.DatabaseError) as exc:
            warnings.append(f"catalog_stats_unavailable:{type(exc).__name__}")
            actions.append("rebuild the Context OS catalog")
    else:
        warnings.append("catalog_missing")
        actions.append("run python3 scripts/gtos_context.py build")

    anchors = _anchor_status(repo_path)
    missing_anchors = [anchor["path"] for anchor in anchors if not anchor["exists"]]
    if missing_anchors:
        warnings.append("required_anchor_missing")
        actions.append("restore or regenerate missing current-context anchors")

    brain = second_brain_status(root=second_brain_root)
    raw_count = int(brain.get("counts_by_status", {}).get("raw_inbox_not_agent_authority", 0))
    reviewed_count = int(brain.get("counts_by_status", {}).get("reviewed_retrieval_intelligence", 0))
    distilled_count = int(brain.get("counts_by_status", {}).get("candidate_distillation_needs_review", 0))
    if raw_count > reviewed_count + distilled_count:
        warnings.append("raw_second_brain_outpaces_distilled_cards")
        actions.append("distill raw second-brain inbox notes before expecting agents to use them")

    sessions = session_capsule_status(repo=repo_path, limit=session_capsule_limit)
    if sessions.get("count", 0) == 0:
        warnings.append("no_session_capsules")
        actions.append("create a session capsule at meaningful interruption or checkpoint boundaries")

    processes = _process_snapshot()
    if processes["counts_by_kind"].get("context_build", 0) > 1:
        warnings.append("multiple_context_build_processes")
        actions.append("let the first Context OS builder finish; later same-options builders should reuse it")
    if processes["counts_by_kind"].get("context_mcp_stdio", 0) > 3:
        warnings.append("many_context_mcp_stdio_processes")
        actions.append("prefer gtos_context_fast_pack or restart stale MCP clients if pack calls timeout")

    status = "ready" if not warnings else "attention_required"
    return {
        "schema_version": "gtos_context_intelligence_health_v1",
        "generated_at_utc": utc_now(),
        "repo": repo_path.as_posix(),
        "status": status,
        "warnings": warnings,
        "recommended_actions": actions,
        "catalog_freshness": freshness,
        "catalog_total_documents": stats.get("total_documents") if stats else None,
        "catalog_content_statuses": stats.get("content_statuses") if stats else {},
        "catalog_authority_tiers": stats.get("authority_tiers") if stats else {},
        "anchors": anchors,
        "second_brain": brain,
        "session_capsules": sessions,
        "processes": processes,
        "workspace_hygiene": _workspace_hygiene_contract(),
        "operating_posture": {
            "mode": "strongest_evidence_bound_action",
            "agent_instruction": (
                "Use current health, packs, capsules, and exact source files to act decisively. "
                "Warnings identify specific repairs or refresh steps; they are triage signals, not broad brakes."
            ),
            "momentum_rule": "continue unrelated valid work while refreshing or repairing the exact stale/missing context surface",
        },
        "stale_nudge_filter": {
            "durable_intent_allowed": True,
            "literal_old_chat_replay_disallowed": True,
            "active_task_source": "newest_user_instruction_plus_current_disk_process_state",
        },
        "continuity_contract": {
            "current_disk_first": True,
            "raw_memory_is_not_authority": True,
            "packs_are_retrieval_maps": True,
            "session_capsules_are_resume_hints": True,
            "verify_capsules_against_current_disk": True,
        },
    }


def _anchor_status(repo_path: Path) -> list[dict[str, Any]]:
    anchors: list[dict[str, Any]] = []
    for rel in REQUIRED_ANCHORS:
        path = repo_path / rel
        exists = path.exists() and path.is_file()
        item: dict[str, Any] = {"path": rel, "exists": exists}
        if exists:
            stat = path.stat()
            item["size_bytes"] = stat.st_size
            item["mtime_ns"] = stat.st_mtime_ns
        anchors.append(item)
    return anchors


def _workspace_hygiene_contract() -> dict[str, Any]:
    return {
        "clean_code_roots": [
            "src/gtos_context_os",
            "tests/test_gtos_context_os.py",
            "scripts/gtos_context.py",
            ".context/00_core",
            "config",
            "AGENTS.md",
            "CLAUDE.md",
            "pyproject.toml",
            "requirements.txt",
        ],
        "cold_by_default": [
            "research/operations/**/*.jsonl",
            "research/science_program_2026_05/**/*.jsonl",
            "shadow_logs/**/*.jsonl",
            "data/ticks",
            "data/m1",
            ".context/context_os/catalog.sqlite",
            ".context/context_os/session_capsules",
        ],
        "search_default": "rg over src tests config scripts .context/00_core with --glob !*.jsonl unless exact evidence path is required",
        "raw_evidence_policy": "hydrate exact raw ledgers only from a route pointer, manifest, verifier, or explicit source requirement",
    }


def _process_snapshot() -> dict[str, Any]:
    try:
        output = subprocess.check_output(
            ["ps", "-axo", "pid,ppid,stat,etime,%cpu,%mem,rss,command"],
            text=True,
            stderr=subprocess.DEVNULL,
            timeout=3,
        )
    except (OSError, subprocess.CalledProcessError, subprocess.TimeoutExpired) as exc:
        return {
            "status": "unavailable",
            "error": type(exc).__name__,
            "matches": [],
            "counts_by_kind": {},
        }

    matches: list[dict[str, Any]] = []
    counts: dict[str, int] = {}
    for line in output.splitlines()[1:]:
        if "ps -axo pid,ppid,stat,etime" in line:
            continue
        if " -lc " in line and "gtos_context.py" in line:
            continue
        if "rg " in line and "gtos_context.py" in line:
            continue
        kind = _process_kind(line)
        if kind is None:
            continue
        parts = line.split(None, 7)
        if len(parts) < 8:
            continue
        pid, ppid, stat, elapsed, cpu, mem, rss, command = parts
        counts[kind] = counts.get(kind, 0) + 1
        matches.append(
            {
                "kind": kind,
                "pid": int(pid),
                "ppid": int(ppid),
                "stat": stat,
                "elapsed": elapsed,
                "cpu_pct": cpu,
                "mem_pct": mem,
                "rss_kb": int(rss),
                "command": command[:500],
            }
        )
    return {
        "status": "ok",
        "matches": matches,
        "counts_by_kind": counts,
    }


def _process_kind(line: str) -> str | None:
    for kind, needles in PROCESS_KINDS.items():
        if any(needle in line for needle in needles):
            return kind
    return None
