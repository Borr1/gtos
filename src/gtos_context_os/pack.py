"""Context-pack assembly for GTOS agents."""

from __future__ import annotations

import json
import signal
import threading
import time
from contextlib import contextmanager
from pathlib import Path
from typing import Any, Callable, TypeVar

from src.gtos_context_os.catalog import (
    DEFAULT_DB_PATH,
    build_catalog,
    catalog_stats,
    ensure_catalog_fresh,
    get_documents,
    search_catalog,
    StaleCatalogError,
    utc_now,
)
from src.gtos_context_os.doctrine import doctrine_checklist, profile_query_terms
from src.gtos_context_os.health import context_intelligence_health
from src.gtos_context_os.memory import search_memory
from src.gtos_context_os.route import route_overview
from src.gtos_context_os.second_brain import second_brain_pack
from src.gtos_context_os.session import list_session_capsules
from src.gtos_context_os.session_state import (
    load_active_session_state,
    load_continuation_cursor,
    summarize_active_state_payload,
    summarize_continuation_cursor_payload,
)
from src.gtos_context_os.symbols import search_symbols


T = TypeVar("T")
DEFAULT_PACK_SECTION_TIMEOUT_SECONDS = 8.0


ANCHOR_PATHS = (
    ".context/LIVE_STATE.md",
    ".context/00_core/current_vnext_system_map.md",
    ".context/00_core/current_repo_reading_order.md",
    ".context/00_core/quick_reference_card.md",
    ".context/00_core/gtos_context_os.md",
    ".context/00_core/gtos_second_brain.md",
    ".context/00_core/repo_cleanup_and_staleness_policy.md",
    ".context/00_core/research_operating_doctrine.md",
    ".context/00_core/goal_session_research_discipline.md",
)


def _db_exists(repo: Path, db_path: Path | str) -> bool:
    db = repo / db_path if not Path(db_path).is_absolute() else Path(db_path)
    return db.exists()


def build_context_pack(
    task: str,
    *,
    repo: Path | str = ".",
    db_path: Path | str = DEFAULT_DB_PATH,
    limit: int = 10,
    profile: str = "standard",
    route: str | None = None,
    include_memory: bool = False,
    memory_root: Path | str | None = None,
    include_second_brain: bool = False,
    second_brain_root: Path | str | None = None,
    second_brain_query: str | None = None,
    include_health: bool = True,
    include_recent_capsules: bool = True,
    section_timeout_seconds: float = DEFAULT_PACK_SECTION_TIMEOUT_SECONDS,
    auto_build: bool = True,
    allow_stale: bool = False,
    auto_rebuild_stale: bool = False,
) -> dict[str, Any]:
    """Return a compact, authority-ranked context pack for one task."""

    repo_path = Path(repo).resolve()
    section_status: dict[str, dict[str, Any]] = {}
    if auto_build and not _db_exists(repo_path, db_path):
        build_catalog(repo=repo_path, db_path=db_path)
    try:
        freshness = ensure_catalog_fresh(db_path=db_path, repo=repo_path, allow_stale=allow_stale)
    except StaleCatalogError:
        if not auto_rebuild_stale:
            raise
        build_catalog(repo=repo_path, db_path=db_path)
        freshness = ensure_catalog_fresh(db_path=db_path, repo=repo_path, allow_stale=False)

    anchors = _pack_section(
        "anchors",
        section_status,
        lambda: get_documents(ANCHOR_PATHS, db_path=db_path, repo=repo_path),
        default=[],
        timeout_seconds=section_timeout_seconds,
    )
    query = _profile_query(task, profile)
    hits = _pack_section(
        "catalog_search",
        section_status,
        lambda: search_catalog(
            query,
            db_path=db_path,
            repo=repo_path,
            limit=limit,
            require_all_terms=profile == "standard",
        ),
        default=[],
        timeout_seconds=section_timeout_seconds,
    )
    stats = _pack_section(
        "catalog_stats",
        section_status,
        lambda: catalog_stats(db_path=db_path, repo=repo_path),
        default={"total_documents": None, "authority_tiers": {}, "content_statuses": {}},
        timeout_seconds=section_timeout_seconds,
    )

    seen = {str(doc["path"]) for doc in anchors}
    relevant = [hit for hit in hits if str(hit["path"]) not in seen]
    active_state = _pack_section(
        "active_session_state",
        section_status,
        lambda: load_active_session_state(repo=repo_path),
        default={
            "schema_version": "gtos_context_active_session_state_v1",
            "status": "unavailable",
            "count": 0,
            "latest": None,
            "states": [],
        },
        timeout_seconds=section_timeout_seconds,
    )
    continuation_cursor = _pack_section(
        "continuation_cursor",
        section_status,
        lambda: load_continuation_cursor(repo=repo_path),
        default={
            "schema_version": "gtos_context_continuation_cursor_read_v1",
            "status": "unavailable",
            "latest": None,
        },
        timeout_seconds=section_timeout_seconds,
    )
    symbol_hits = _pack_section(
        "symbol_search",
        section_status,
        lambda: search_symbols(
            task,
            repo=repo_path,
            limit=max(8, min(20, limit)),
            max_files=120 if section_timeout_seconds <= 3.5 else 500,
            max_file_bytes=750_000,
            max_elapsed_seconds=max(0.5, section_timeout_seconds * 0.65),
        ),
        default={
            "schema_version": "gtos_context_symbol_search_v1",
            "status": "unavailable",
            "query": task,
            "parsed_files": 0,
            "symbol_count": 0,
            "hit_count": 0,
            "hits": [],
            "errors": [],
        },
        timeout_seconds=section_timeout_seconds,
    )
    route_state = (
        _pack_section(
            "route_overview",
            section_status,
            lambda: route_overview(route, repo=repo_path, db_path=db_path),
            default=None,
            timeout_seconds=section_timeout_seconds,
        )
        if route
        else None
    )
    memory_hits = (
        _pack_section(
            "memory",
            section_status,
            lambda: search_memory(query, memory_root=memory_root, limit=max(4, limit // 2)),
            default=[],
            timeout_seconds=section_timeout_seconds,
        )
        if include_memory
        else []
    )
    brain = (
        _pack_section(
            "second_brain",
            section_status,
            lambda: second_brain_pack(
                second_brain_query or query,
                root=second_brain_root,
                limit=max(4, limit // 2),
            ),
            default={
                "status": {"status": "unavailable"},
                "hits": [],
                "rules": {
                    "fallback": "second_brain_section_unavailable_verify_current_disk",
                },
            },
            timeout_seconds=section_timeout_seconds,
        )
        if include_second_brain
        else None
    )
    health = (
        _pack_section(
            "context_health",
            section_status,
            lambda: context_intelligence_health(
                repo=repo_path,
                db_path=db_path,
                second_brain_root=second_brain_root,
                session_capsule_limit=5,
            ),
            default={
                "status": "unavailable",
                "warnings": ["context_health_section_unavailable"],
                "recommended_actions": ["run python3 scripts/gtos_context.py health separately"],
            },
            timeout_seconds=section_timeout_seconds,
        )
        if include_health
        else {
            "status": "skipped",
            "warnings": ["context_health_skipped_for_fast_pack"],
            "recommended_actions": ["run gtos_context_health or CLI health when diagnostics are needed"],
        }
    )
    recent_capsules = (
        _pack_section(
            "recent_session_capsules",
            section_status,
            lambda: list_session_capsules(repo=repo_path, limit=5),
            default=[],
            timeout_seconds=section_timeout_seconds,
        )
        if include_recent_capsules
        else []
    )

    return {
        "schema_version": "gtos_context_pack_v1",
        "generated_at_utc": utc_now(),
        "repo": repo_path.as_posix(),
        "task": task,
        "profile": profile,
        "route": route,
        "catalog": stats,
        "catalog_freshness": freshness,
        "context_health": health,
        "pack_diagnostics": {
            "schema_version": "gtos_context_pack_diagnostics_v1",
            "section_timeout_seconds": section_timeout_seconds,
            "section_status": section_status,
            "partial_result": any(
                status.get("status") != "ok" for status in section_status.values()
            ),
        },
        "doctrine_checklist": doctrine_checklist(task=task, profile=profile, route=route),
        "rules": {
            "execution_posture": "act decisively from current disk evidence; patch/build/verify when source evidence supports it",
            "source_of_truth": "current disk artifacts are the launch point; chat, memory, and stale summaries are recall to verify",
            "raw_evidence": "large JSONL/LFS/raw evidence is cold by default; hydrate exact files from route/source pointers",
            "broker_boundary": "Context OS supplies intelligence only; broker/live authority stays with active task doctrine and runtime controls",
            "writeback": "agents should propose canonical writebacks with sources instead of silently rewriting memory",
            "second_brain": "raw owner ideas are not authority; use distilled cards as retrieval intelligence only",
        },
        "anchors": anchors,
        "active_session_state": active_state,
        "continuation_cursor": continuation_cursor,
        "symbol_hits": symbol_hits,
        "route_overview": route_state,
        "relevant_hits": relevant,
        "memory_hits": memory_hits,
        "second_brain": brain,
        "recent_session_capsules": recent_capsules,
    }


class ContextPackSectionTimeout(TimeoutError):
    """Raised when an optional pack section exceeds its local budget."""


@contextmanager
def _section_time_limit(seconds: float) -> Any:
    if seconds <= 0 or threading.current_thread() is not threading.main_thread():
        yield
        return
    previous_handler = signal.getsignal(signal.SIGALRM)
    previous_timer = signal.setitimer(signal.ITIMER_REAL, 0.0)

    def _raise_timeout(_signum: int, _frame: object) -> None:
        raise ContextPackSectionTimeout(f"context pack section timed out after {seconds:g}s")

    signal.signal(signal.SIGALRM, _raise_timeout)
    signal.setitimer(signal.ITIMER_REAL, seconds)
    try:
        yield
    finally:
        signal.setitimer(signal.ITIMER_REAL, 0.0)
        signal.signal(signal.SIGALRM, previous_handler)
        if previous_timer[0] > 0:
            signal.setitimer(signal.ITIMER_REAL, *previous_timer)


def _pack_section(
    name: str,
    section_status: dict[str, dict[str, Any]],
    callback: Callable[[], T],
    *,
    default: T,
    timeout_seconds: float,
) -> T:
    started = time.perf_counter()
    try:
        with _section_time_limit(timeout_seconds):
            value = callback()
    except Exception as exc:
        section_status[name] = {
            "status": "error",
            "elapsed_seconds": round(time.perf_counter() - started, 6),
            "error_type": type(exc).__name__,
            "error": str(exc)[:500],
        }
        return default
    section_status[name] = {
        "status": "ok",
        "elapsed_seconds": round(time.perf_counter() - started, 6),
    }
    return value


def _profile_query(task: str, profile: str) -> str:
    terms = profile_query_terms(profile)
    return f"{task} {terms}".strip()


def render_markdown_pack(pack: dict[str, Any], *, snippet_chars: int = 1400) -> str:
    lines: list[str] = []
    lines.append("# GTOS Context Pack")
    lines.append("")
    lines.append(f"- generated_at_utc: `{pack['generated_at_utc']}`")
    lines.append(f"- repo: `{pack['repo']}`")
    lines.append(f"- task: `{pack['task']}`")
    lines.append(f"- profile: `{pack.get('profile', 'standard')}`")
    if pack.get("route"):
        lines.append(f"- route: `{pack['route']}`")
    lines.append("")
    _render_operating_posture(lines, pack)
    lines.append("")
    lines.append("## Retrieval Rules")
    for key, value in pack["rules"].items():
        lines.append(f"- `{key}`: {value}")
    lines.append("")
    lines.append("## Catalog State")
    catalog = pack["catalog"]
    lines.append(f"- total_documents: `{catalog['total_documents']}`")
    meta = catalog.get("meta", {})
    if meta.get("generated_at_utc"):
        lines.append(f"- catalog_generated_at_utc: `{meta['generated_at_utc']}`")
    lines.append(f"- authority_tiers: `{json.dumps(catalog.get('authority_tiers', {}), sort_keys=True)}`")
    if pack.get("catalog_freshness"):
        freshness = pack["catalog_freshness"]
        lines.append(f"- freshness_status: `{freshness.get('status')}`")
        if freshness.get("reasons"):
            lines.append(f"- freshness_reasons: `{json.dumps(freshness.get('reasons'), sort_keys=True)}`")
    lines.append("")
    _render_context_health(lines, pack.get("context_health") or {})
    lines.append("")
    _render_pack_diagnostics(lines, pack.get("pack_diagnostics") or {})
    lines.append("")
    _render_active_session_state(lines, pack.get("active_session_state") or {})
    lines.append("")
    _render_continuation_cursor(lines, pack.get("continuation_cursor") or {})
    lines.append("")
    _render_symbol_hits(lines, pack.get("symbol_hits") or {})
    lines.append("")
    _render_doctrine(lines, pack.get("doctrine_checklist") or {})
    lines.append("")
    lines.append("## Current Authority Anchors")
    _render_docs(lines, pack["anchors"], snippet_chars=snippet_chars)
    lines.append("")
    if pack.get("route_overview"):
        _render_route_overview(lines, pack["route_overview"])
        lines.append("")
    lines.append("## Task-Relevant Hits")
    _render_docs(lines, pack["relevant_hits"], snippet_chars=snippet_chars)
    if pack.get("memory_hits"):
        lines.append("")
        lines.append("## Codex Memory Hits")
        _render_docs(lines, pack["memory_hits"], snippet_chars=snippet_chars)
    if pack.get("second_brain"):
        lines.append("")
        _render_second_brain(lines, pack["second_brain"], snippet_chars=snippet_chars)
    if pack.get("recent_session_capsules"):
        lines.append("")
        _render_session_capsules(lines, pack["recent_session_capsules"])
    return "\n".join(lines).rstrip() + "\n"


def _render_operating_posture(lines: list[str], pack: dict[str, Any]) -> None:
    lines.append("## Operating Posture")
    checklist = pack.get("doctrine_checklist") or {}
    health = pack.get("context_health") or {}
    lines.append(f"- lane_posture: `{checklist.get('lane_posture')}`")
    if checklist.get("operating_posture"):
        lines.append(f"- action_rule: {checklist['operating_posture']}")
    posture = health.get("operating_posture") or {}
    if posture.get("agent_instruction"):
        lines.append(f"- health_rule: {posture['agent_instruction']}")
    lines.append("- quality_rule: preserve evidence class labels while still moving implementation/research forward")


def _render_context_health(lines: list[str], health: dict[str, Any]) -> None:
    lines.append("## Context Intelligence Health")
    if not health:
        lines.append("- unavailable")
        return
    lines.append(f"- status: `{health.get('status')}`")
    if health.get("warnings"):
        lines.append(f"- warnings: `{json.dumps(health.get('warnings'), sort_keys=True)}`")
    if health.get("recommended_actions"):
        lines.append(
            f"- recommended_actions: `{json.dumps(health.get('recommended_actions'), sort_keys=True)}`"
        )
    posture = health.get("operating_posture") or {}
    if posture.get("momentum_rule"):
        lines.append(f"- warning_policy: {posture['momentum_rule']}")
    sessions = health.get("session_capsules") or {}
    lines.append(f"- session_capsules: `{sessions.get('count', 0)}`")
    latest = sessions.get("latest")
    if latest:
        lines.append(f"- latest_session_capsule: `{latest.get('path')}`")
    brain = health.get("second_brain") or {}
    lines.append(f"- second_brain_active_markdown: `{brain.get('active_markdown', 0)}`")
    lines.append(f"- second_brain_infrastructure_markdown: `{brain.get('infrastructure_markdown', 0)}`")
    hygiene = health.get("workspace_hygiene") or {}
    if hygiene.get("search_default"):
        lines.append(f"- workspace_search_default: {hygiene['search_default']}")


def _render_pack_diagnostics(lines: list[str], diagnostics: dict[str, Any]) -> None:
    lines.append("## Pack Diagnostics")
    if not diagnostics:
        lines.append("- unavailable")
        return
    lines.append(f"- partial_result: `{diagnostics.get('partial_result')}`")
    lines.append(f"- section_timeout_seconds: `{diagnostics.get('section_timeout_seconds')}`")
    statuses = diagnostics.get("section_status") or {}
    for name, status in sorted(statuses.items()):
        lines.append(
            f"- `{name}`: `{status.get('status')}` "
            f"elapsed=`{status.get('elapsed_seconds')}`"
        )
        if status.get("error_type"):
            lines.append(
                f"  error=`{status.get('error_type')}: {status.get('error')}`"
            )


def _render_active_session_state(lines: list[str], state: dict[str, Any]) -> None:
    lines.append("## Active Session State")
    if not state:
        lines.append("- unavailable")
        return
    lines.append(f"- status: `{state.get('status')}`")
    lines.append(f"- count: `{state.get('count', 0)}`")
    latest = state.get("latest") or {}
    if not latest:
        lines.append("- latest: none")
        return
    lines.append(f"- latest: `{latest.get('path')}`")
    lines.append(f"- parse_status: `{latest.get('parse_status')}`")
    payload = latest.get("payload")
    if isinstance(payload, dict):
        for key, value in summarize_active_state_payload(payload).items():
            if value not in (None, "", [], {}):
                lines.append(f"- {key}: {str(value)[:500]}")
    lines.append("- boundary: verify this compact state against current disk before acting")


def _render_continuation_cursor(lines: list[str], cursor: dict[str, Any]) -> None:
    lines.append("## Continuation Cursor")
    if not cursor:
        lines.append("- unavailable")
        return
    lines.append(f"- status: `{cursor.get('status')}`")
    latest = cursor.get("latest") or {}
    if not latest:
        lines.append("- latest: none")
        return
    lines.append(f"- latest: `{latest.get('path')}`")
    lines.append(f"- parse_status: `{latest.get('parse_status')}`")
    payload = latest.get("payload")
    if isinstance(payload, dict):
        for key, value in summarize_continuation_cursor_payload(payload).items():
            if value not in (None, "", [], {}):
                lines.append(f"- {key}: {str(value)[:500]}")
    lines.append("- boundary: use as short-lived working memory; verify exact files before acting")


def _render_symbol_hits(lines: list[str], symbols: dict[str, Any]) -> None:
    lines.append("## Live Symbol Hits")
    if not symbols:
        lines.append("- unavailable")
        return
    lines.append(f"- query: `{symbols.get('query')}`")
    lines.append(f"- parsed_files: `{symbols.get('parsed_files', 0)}`")
    lines.append(f"- symbol_count: `{symbols.get('symbol_count', 0)}`")
    lines.append(f"- hit_count: `{symbols.get('hit_count', 0)}`")
    hits = symbols.get("hits") or []
    if not hits:
        lines.append("- hits: none")
        return
    lines.append("- boundary: navigation intelligence; open exact source before code claims")
    for hit in hits[:12]:
        lines.append(
            f"- `{hit.get('qualname')}` `{hit.get('kind')}` "
            f"{hit.get('path')}:{hit.get('line')} score=`{hit.get('score')}`"
        )


def _render_doctrine(lines: list[str], checklist: dict[str, Any]) -> None:
    lines.append("## Doctrine Checklist")
    if not checklist:
        lines.append("- none")
        return
    lines.append(f"- lane_posture: `{checklist.get('lane_posture')}`")
    for rule in checklist.get("mandatory_rules", [])[:10]:
        lines.append(f"- {rule}")
    lines.append("")
    lines.append("### Anti-Staleness")
    for rule in checklist.get("anti_staleness", [])[:8]:
        lines.append(f"- {rule}")


def _render_route_overview(lines: list[str], overview: dict[str, Any]) -> None:
    lines.append("## Route Overview")
    lines.append(f"- route: `{overview['route']}`")
    lines.append(f"- total_documents: `{overview['total_documents']}`")
    lines.append(f"- compact_documents: `{overview['compact_documents']}`")
    lines.append(f"- cold_raw_pointers: `{overview['cold_raw_pointers']}`")
    lines.append(f"- authority_tiers: `{json.dumps(overview.get('authority_tiers', {}), sort_keys=True)}`")
    lines.append(f"- evidence_classes: `{json.dumps(overview.get('evidence_classes', {}), sort_keys=True)}`")
    read_first = overview.get("read_first") or []
    lines.append("")
    lines.append("### Route Read First")
    if not read_first:
        lines.append("- none")
        return
    for doc in read_first[:12]:
        lines.append(
            f"- `{doc['path']}` "
            f"({doc['authority_tier']}; {doc['evidence_class']}; {doc['content_status']})"
        )


def _render_docs(lines: list[str], docs: list[dict[str, Any]], *, snippet_chars: int) -> None:
    if not docs:
        lines.append("- none")
        return
    for doc in docs:
        lines.append(f"### {doc['path']}")
        lines.append(f"- title: {doc['title']}")
        lines.append(f"- authority_tier: `{doc['authority_tier']}`")
        lines.append(f"- evidence_class: `{doc['evidence_class']}`")
        lines.append(f"- freshness: `{doc['freshness']}`")
        if doc.get("route"):
            lines.append(f"- route: `{doc['route']}`")
        if doc.get("sha256"):
            lines.append(f"- sha256: `{str(doc['sha256'])[:16]}`")
        snippet = str(doc.get("snippet") or "").strip()
        if snippet:
            lines.append("")
            lines.append("```text")
            lines.append(snippet[:snippet_chars])
            lines.append("```")
        lines.append("")


def _render_second_brain(lines: list[str], brain: dict[str, Any], *, snippet_chars: int) -> None:
    lines.append("## GTOS Second Brain")
    status = brain.get("status") or {}
    lines.append(f"- root: `{status.get('root')}`")
    lines.append(f"- pour_ideas_here: `{status.get('pour_ideas_here')}`")
    lines.append("- boundary: raw inbox notes are preserved, not direct agent authority")
    lines.append("- agent_use: distilled cards are retrieval intelligence; verify against current disk/source evidence")
    hits = brain.get("hits") or []
    if not hits:
        lines.append("- hits: none")
        return
    lines.append("")
    lines.append("### Brain Hits")
    for hit in hits:
        lines.append(f"#### {hit['path']}")
        lines.append(f"- title: {hit['title']}")
        lines.append(f"- status: `{hit['status']}`")
        lines.append(f"- authority_tier: `{hit['authority_tier']}`")
        lines.append(f"- freshness: `{hit['freshness']}`")
        if hit.get("tags"):
            lines.append(f"- tags: `{json.dumps(hit['tags'], sort_keys=True)}`")
        snippet = str(hit.get("snippet") or "").strip()
        if snippet:
            lines.append("")
            lines.append("```text")
            lines.append(snippet[:snippet_chars])
            lines.append("```")
        lines.append("")


def _render_session_capsules(lines: list[str], capsules: list[dict[str, Any]]) -> None:
    lines.append("## Recent Session Capsules")
    if not capsules:
        lines.append("- none")
        return
    lines.append("- boundary: local continuity hints; verify against current disk before acting")
    for capsule in capsules:
        lines.append(f"### {capsule['path']}")
        lines.append(f"- title: {capsule.get('title')}")
        if capsule.get("task"):
            lines.append(f"- task: {capsule.get('task')}")
        lines.append(f"- generated_at_utc: `{capsule.get('generated_at_utc')}`")
        lines.append(f"- status: `{capsule.get('status')}`")
        summary = str(capsule.get("summary") or "").strip()
        if summary:
            lines.append(f"- summary: {summary[:700]}")
        sources = capsule.get("sources") or []
        if sources:
            lines.append(f"- sources: `{json.dumps(sources[:12])}`")
        decisions = capsule.get("decisions") or []
        if decisions:
            lines.append(f"- decisions: `{json.dumps(decisions[:8])}`")
        lines.append("")
