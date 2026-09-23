"""Namespace isolation guard: the shadow refuses to start on a collision.

The live book owns ``pipeline_state/ultimate_book/...`` and
``shadow_logs/gtos_vnext_*``.  The forward-shadow lane owns exactly one
directory of its own (default ``shadow_logs/funnel_shadow``) and stamps it
with an ownership marker.  Refusal conditions:

  * the namespace resolves inside (or equal to) a live-book-owned tree;
  * the namespace exists WITHOUT the shadow's ownership marker (someone else's
    directory — never adopt it);
  * the marker exists but names a different owner lane.

This is a startup guard, not a lock: two shadow processes on the same
namespace are additionally excluded by an exclusive pid lockfile.
"""

from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from pathlib import Path

MARKER_NAME = "FORWARD_SHADOW_NAMESPACE.json"
LANE_ID = "wave21_forward_shadow_funnel_v1"

# Path fragments the live book owns; the shadow namespace must not resolve
# into any of them.
_LIVE_OWNED_FRAGMENTS = (
    ("pipeline_state",),
    ("shadow_logs", "gtos_vnext_runtime_decisions.jsonl"),
    ("shadow_logs", "gtos_vnext_replacement_monitoring.jsonl"),
)
_LIVE_OWNED_DIR_PREFIXES = (
    ("pipeline_state",),
    ("shadow_logs", "gtos_vnext"),
)


class NamespaceCollisionError(RuntimeError):
    pass


def _resolved_parts(path: Path, repo_root: Path) -> tuple[str, ...]:
    resolved = path.resolve()
    try:
        return resolved.relative_to(repo_root.resolve()).parts
    except ValueError:
        return resolved.parts


def assert_namespace_safe(namespace_dir: Path, *, repo_root: Path) -> None:
    parts = _resolved_parts(namespace_dir, repo_root)
    for prefix in _LIVE_OWNED_DIR_PREFIXES:
        if len(parts) >= len(prefix):
            head = parts[: len(prefix)]
            if head[:-1] == prefix[:-1] and str(head[-1]).startswith(prefix[-1]):
                raise NamespaceCollisionError(
                    "shadow namespace resolves into a live-book-owned tree: "
                    f"{namespace_dir} (matches {'/'.join(prefix)}*)"
                )
    for fragment in _LIVE_OWNED_FRAGMENTS:
        if parts[: len(fragment)] == fragment:
            raise NamespaceCollisionError(
                f"shadow namespace collides with live artifact: {namespace_dir}"
            )


def claim_namespace(namespace_dir: Path, *, repo_root: Path) -> Path:
    """Validate, create-or-adopt, and pid-lock the namespace. Returns lock path."""

    assert_namespace_safe(namespace_dir, repo_root=repo_root)
    marker_path = namespace_dir / MARKER_NAME
    if namespace_dir.exists():
        if not namespace_dir.is_dir():
            raise NamespaceCollisionError(f"namespace is not a directory: {namespace_dir}")
        if not marker_path.is_file():
            if any(namespace_dir.iterdir()):
                raise NamespaceCollisionError(
                    "namespace directory exists without the shadow ownership "
                    f"marker — refusing to adopt: {namespace_dir}"
                )
        else:
            marker = json.loads(marker_path.read_text(encoding="utf-8"))
            if marker.get("lane_id") != LANE_ID:
                raise NamespaceCollisionError(
                    f"namespace owned by another lane: {marker.get('lane_id')!r}"
                )
    namespace_dir.mkdir(parents=True, exist_ok=True)
    if not marker_path.is_file():
        marker_path.write_text(
            json.dumps(
                {
                    "lane_id": LANE_ID,
                    "created_utc": datetime.now(timezone.utc).isoformat(),
                    "broker_mutation_enabled": False,
                },
                indent=2,
                sort_keys=True,
            )
            + "\n",
            encoding="utf-8",
        )

    lock_path = namespace_dir / "runner.pid.lock"
    if lock_path.exists():
        stale_pid = None
        try:
            stale_pid = int(lock_path.read_text(encoding="utf-8").strip() or 0)
        except ValueError:
            pass
        if stale_pid and _pid_alive(stale_pid):
            raise NamespaceCollisionError(
                f"another shadow runner (pid {stale_pid}) holds {lock_path}"
            )
        lock_path.unlink()
    fd = os.open(str(lock_path), os.O_CREAT | os.O_EXCL | os.O_WRONLY)
    try:
        os.write(fd, str(os.getpid()).encode())
    finally:
        os.close(fd)
    return lock_path


def _pid_alive(pid: int) -> bool:
    try:
        os.kill(pid, 0)
    except OSError:
        return False
    return True


def release_namespace(lock_path: Path) -> None:
    try:
        lock_path.unlink()
    except FileNotFoundError:
        pass
