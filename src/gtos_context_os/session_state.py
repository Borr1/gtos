"""Active Context OS session-state readers.

These files are compact continuity surfaces, not proof.  They let a resumed
agent start from the latest root-cause/checkpoint map before falling back to
older chat, memory, or second-brain retrieval.
"""

from __future__ import annotations

from datetime import datetime, timezone
import json
from pathlib import Path
from typing import Any, Sequence


DEFAULT_ACTIVE_SESSION_STATE_PATH = ".context/context_os/ACTIVE_SESSION_STATE.json"
DEFAULT_ROOT_CAUSE_MAP_PATH = ".context/context_os/CURRENT_ROOT_CAUSE_MAP.json"
DEFAULT_CONTINUATION_CURSOR_PATH = ".context/context_os/CONTINUATION_CURSOR.json"
DEFAULT_ACTIVE_STATE_PATHS = (
    DEFAULT_ACTIVE_SESSION_STATE_PATH,
    DEFAULT_ROOT_CAUSE_MAP_PATH,
)
ACTIVE_STATE_KINDS = {
    "session": DEFAULT_ACTIVE_SESSION_STATE_PATH,
    "root-cause": DEFAULT_ROOT_CAUSE_MAP_PATH,
}


def load_active_session_state(
    *,
    repo: Path | str = ".",
    paths: Sequence[str] = DEFAULT_ACTIVE_STATE_PATHS,
    max_text_chars: int = 20_000,
) -> dict[str, Any]:
    """Return current compact state files if present.

    The latest existing state is surfaced first.  JSON is parsed when possible;
    non-JSON files are still returned as bounded text so a corrupted checkpoint
    is visible instead of silently disappearing.
    """

    repo_path = Path(repo).resolve()
    states: list[dict[str, Any]] = []
    for rel in paths:
        path = repo_path / rel
        if not path.exists() or not path.is_file():
            continue
        stat = path.stat()
        text = path.read_text(encoding="utf-8", errors="replace")
        payload: Any | None = None
        parse_status = "not_json"
        try:
            payload = json.loads(text)
            parse_status = "json"
        except json.JSONDecodeError as exc:
            payload = {
                "error": "json_parse_error",
                "error_type": type(exc).__name__,
                "message": str(exc),
                "text_preview": text[:max_text_chars],
            }
            parse_status = "json_parse_error"
        states.append(
            {
                "path": rel,
                "abs_path": path.as_posix(),
                "size_bytes": stat.st_size,
                "mtime_ns": stat.st_mtime_ns,
                "status": "active_session_state_verify_against_current_disk",
                "parse_status": parse_status,
                "payload": payload,
            }
        )
    states.sort(key=lambda item: int(item.get("mtime_ns") or 0), reverse=True)
    latest = states[0] if states else None
    return {
        "schema_version": "gtos_context_active_session_state_v1",
        "status": "present" if latest else "missing",
        "count": len(states),
        "latest": latest,
        "states": states,
        "expected_paths": list(paths),
        "use_boundary": "active_session_state_is_continuity_intelligence_verify_against_current_disk",
    }


def write_active_session_state(
    *,
    repo: Path | str = ".",
    kind: str = "session",
    title: str,
    task: str = "",
    latest_replay_prefix: str = "",
    current_checkpoint: str = "",
    next_patch_batch: str = "",
    fixed: Sequence[str] = (),
    partially_fixed: Sequence[str] = (),
    remaining: Sequence[str] = (),
    blockers: Sequence[str] = (),
    sources: Sequence[str] = (),
    decisions: Sequence[str] = (),
    notes: Sequence[str] = (),
    extra: dict[str, Any] | None = None,
    path: str | None = None,
) -> dict[str, Any]:
    """Write one compact continuity checkpoint atomically.

    This is a local Context OS surface, not a proof ledger.  It exists so long
    sessions can publish the current root-cause/checkpoint map in one small
    current-scope file instead of relying on stale chat history.
    """

    repo_path = Path(repo).resolve()
    rel_path = path or ACTIVE_STATE_KINDS.get(kind)
    if rel_path is None:
        raise ValueError(f"unknown active-state kind: {kind}")
    if not title.strip():
        raise ValueError("active-state title is required")
    if Path(rel_path).is_absolute() or ".." in Path(rel_path).parts:
        raise ValueError("active-state path must be repo-relative and cannot contain '..'")

    payload: dict[str, Any] = {
        "schema_version": "gtos_context_active_session_state_checkpoint_v1",
        "generated_at_utc": _utc_now(),
        "kind": kind,
        "title": title.strip(),
        "task": task.strip(),
        "latest_replay_prefix": latest_replay_prefix.strip(),
        "current_checkpoint": current_checkpoint.strip(),
        "next_patch_batch": next_patch_batch.strip(),
        "fixed": [item for item in fixed if item],
        "partially_fixed": [item for item in partially_fixed if item],
        "remaining": [item for item in remaining if item],
        "blockers": [item for item in blockers if item],
        "sources": [item for item in sources if item],
        "decisions": [item for item in decisions if item],
        "notes": [item for item in notes if item],
        "use_boundary": "continuity_intelligence_verify_against_current_disk",
    }
    if extra:
        payload["extra"] = extra

    out_path = repo_path / rel_path
    out_path.parent.mkdir(parents=True, exist_ok=True)
    tmp_path = out_path.with_name(f"{out_path.name}.tmp")
    tmp_path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    tmp_path.replace(out_path)
    stat = out_path.stat()
    return {
        "schema_version": "gtos_context_active_session_state_write_v1",
        "status": "written",
        "path": rel_path,
        "abs_path": out_path.as_posix(),
        "size_bytes": stat.st_size,
        "mtime_ns": stat.st_mtime_ns,
        "payload": payload,
    }


def load_continuation_cursor(
    *,
    repo: Path | str = ".",
    path: str = DEFAULT_CONTINUATION_CURSOR_PATH,
    max_text_chars: int = 20_000,
) -> dict[str, Any]:
    """Read the compact "resume exactly here" cursor if present."""

    repo_path = Path(repo).resolve()
    cursor_path = repo_path / path
    if not cursor_path.exists() or not cursor_path.is_file():
        return {
            "schema_version": "gtos_context_continuation_cursor_read_v1",
            "status": "missing",
            "path": path,
            "latest": None,
            "use_boundary": "continuation_cursor_is_working_memory_verify_against_current_disk",
        }
    stat = cursor_path.stat()
    text = cursor_path.read_text(encoding="utf-8", errors="replace")
    try:
        payload: Any = json.loads(text)
        parse_status = "json"
    except json.JSONDecodeError as exc:
        payload = {
            "error": "json_parse_error",
            "error_type": type(exc).__name__,
            "message": str(exc),
            "text_preview": text[:max_text_chars],
        }
        parse_status = "json_parse_error"
    return {
        "schema_version": "gtos_context_continuation_cursor_read_v1",
        "status": "present",
        "path": path,
        "latest": {
            "path": path,
            "abs_path": cursor_path.as_posix(),
            "size_bytes": stat.st_size,
            "mtime_ns": stat.st_mtime_ns,
            "parse_status": parse_status,
            "payload": payload,
        },
        "use_boundary": "continuation_cursor_is_working_memory_verify_against_current_disk",
    }


def write_continuation_cursor(
    *,
    repo: Path | str = ".",
    task: str = "",
    mode: str = "checkpoint",
    last_observation: str,
    current_hypothesis: str = "",
    next_atomic_step: str = "",
    files_recently_read: Sequence[str] = (),
    symbols_recently_checked: Sequence[str] = (),
    commands_recently_run: Sequence[str] = (),
    recent_actions: Sequence[str] = (),
    do_not_repeat: Sequence[str] = (),
    verify_next: Sequence[str] = (),
    sources: Sequence[str] = (),
    notes: Sequence[str] = (),
    path: str = DEFAULT_CONTINUATION_CURSOR_PATH,
) -> dict[str, Any]:
    """Write the short-lived continuation cursor atomically."""

    if not last_observation.strip():
        raise ValueError("continuation cursor last_observation is required")
    rel = Path(path)
    if rel.is_absolute() or ".." in rel.parts:
        raise ValueError("continuation cursor path must be repo-relative and cannot contain '..'")
    repo_path = Path(repo).resolve()
    payload = {
        "schema_version": "gtos_context_continuation_cursor_v1",
        "generated_at_utc": _utc_now(),
        "task": task.strip(),
        "mode": mode.strip() or "checkpoint",
        "last_observation": last_observation.strip(),
        "current_hypothesis": current_hypothesis.strip(),
        "next_atomic_step": next_atomic_step.strip(),
        "files_recently_read": [item for item in files_recently_read if item],
        "symbols_recently_checked": [item for item in symbols_recently_checked if item],
        "commands_recently_run": [item for item in commands_recently_run if item],
        "recent_actions": [item for item in recent_actions if item],
        "do_not_repeat": [item for item in do_not_repeat if item],
        "verify_next": [item for item in verify_next if item],
        "sources": [item for item in sources if item],
        "notes": [item for item in notes if item],
        "use_boundary": "working_memory_cursor_verify_against_current_disk_before_action",
    }
    out_path = repo_path / rel
    out_path.parent.mkdir(parents=True, exist_ok=True)
    tmp_path = out_path.with_name(f"{out_path.name}.tmp")
    tmp_path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    tmp_path.replace(out_path)
    stat = out_path.stat()
    return {
        "schema_version": "gtos_context_continuation_cursor_write_v1",
        "status": "written",
        "path": rel.as_posix(),
        "abs_path": out_path.as_posix(),
        "size_bytes": stat.st_size,
        "mtime_ns": stat.st_mtime_ns,
        "payload": payload,
    }


def write_context_checkpoint(
    *,
    repo: Path | str = ".",
    title: str,
    task: str,
    current_checkpoint: str,
    next_patch_batch: str = "",
    last_observation: str,
    current_hypothesis: str = "",
    next_atomic_step: str = "",
    fixed: Sequence[str] = (),
    partially_fixed: Sequence[str] = (),
    remaining: Sequence[str] = (),
    blockers: Sequence[str] = (),
    files_recently_read: Sequence[str] = (),
    symbols_recently_checked: Sequence[str] = (),
    commands_recently_run: Sequence[str] = (),
    recent_actions: Sequence[str] = (),
    do_not_repeat: Sequence[str] = (),
    verify_next: Sequence[str] = (),
    sources: Sequence[str] = (),
    decisions: Sequence[str] = (),
    notes: Sequence[str] = (),
) -> dict[str, Any]:
    """Write durable active state plus short-lived continuation cursor."""

    state = write_active_session_state(
        repo=repo,
        kind="session",
        title=title,
        task=task,
        current_checkpoint=current_checkpoint,
        next_patch_batch=next_patch_batch,
        fixed=fixed,
        partially_fixed=partially_fixed,
        remaining=remaining,
        blockers=blockers,
        sources=sources,
        decisions=decisions,
        notes=notes,
    )
    cursor = write_continuation_cursor(
        repo=repo,
        task=task,
        mode="checkpoint",
        last_observation=last_observation,
        current_hypothesis=current_hypothesis,
        next_atomic_step=next_atomic_step,
        files_recently_read=files_recently_read,
        symbols_recently_checked=symbols_recently_checked,
        commands_recently_run=commands_recently_run,
        recent_actions=recent_actions,
        do_not_repeat=do_not_repeat,
        verify_next=verify_next,
        sources=sources,
        notes=notes,
    )
    return {
        "schema_version": "gtos_context_checkpoint_write_v1",
        "status": "written",
        "active_state": state,
        "continuation_cursor": cursor,
        "use_boundary": "checkpoint_is_continuity_intelligence_verify_against_current_disk",
    }


def _utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def summarize_active_state_payload(payload: dict[str, Any]) -> dict[str, Any]:
    """Return display-safe continuity fields across active-state schemas."""

    summary: dict[str, Any] = {
        "schema_version": payload.get("schema_version"),
        "title": payload.get("title"),
        "task": payload.get("task"),
        "latest_replay_prefix": payload.get("latest_replay_prefix"),
        "current_checkpoint": payload.get("current_checkpoint"),
        "next_patch_batch": payload.get("next_patch_batch"),
    }
    if payload.get("schema_version") == "gtos_current_root_cause_map_v1":
        latest_replay = payload.get("latest_replay")
        if isinstance(latest_replay, dict):
            summary["latest_replay_prefix"] = latest_replay.get("prefix")
            headline = latest_replay.get("headline_net_r")
            if headline is not None:
                summary["latest_headline_net_r"] = headline
        next_batch = payload.get("next_same_root_patch_batch")
        if isinstance(next_batch, dict):
            summary["next_patch_batch"] = next_batch.get("name") or next_batch.get("repair_intent")
        if not summary.get("title"):
            summary["title"] = "Current root-cause map"
        if not summary.get("current_checkpoint"):
            summary["current_checkpoint"] = payload.get("generated_at_utc")
        if isinstance(payload.get("fixed"), list):
            summary["fixed_count"] = len(payload["fixed"])
        if isinstance(payload.get("partially_fixed"), list):
            summary["partially_fixed_count"] = len(payload["partially_fixed"])
        if isinstance(payload.get("remaining"), list):
            summary["remaining_count"] = len(payload["remaining"])
        if isinstance(payload.get("subagent_findings"), list):
            summary["subagent_findings_count"] = len(payload["subagent_findings"])
    return {key: value for key, value in summary.items() if value not in (None, "", [], {})}


def summarize_continuation_cursor_payload(payload: dict[str, Any]) -> dict[str, Any]:
    """Return display-safe fields for the continuation cursor."""

    fields = (
        "schema_version",
        "task",
        "mode",
        "last_observation",
        "current_hypothesis",
        "next_atomic_step",
        "files_recently_read",
        "symbols_recently_checked",
        "recent_actions",
        "do_not_repeat",
        "verify_next",
    )
    return {
        key: payload.get(key)
        for key in fields
        if payload.get(key) not in (None, "", [], {})
    }
