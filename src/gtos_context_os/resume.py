"""Resume bundle generation for GTOS Context OS."""

from __future__ import annotations

import subprocess
from pathlib import Path
from typing import Any

from src.gtos_context_os.catalog import DEFAULT_DB_PATH, build_catalog, utc_now
from src.gtos_context_os.health import context_intelligence_health
from src.gtos_context_os.pack import build_context_pack, render_markdown_pack
from src.gtos_context_os.second_brain import DEFAULT_SECOND_BRAIN_ROOT
from src.gtos_context_os.session import create_session_capsule, list_session_capsules


CONTEXT_OS_SCOPE = (
    ".context/00_core/gtos_context_os.md",
    ".context/00_core/gtos_second_brain.md",
    ".context/LIVE_STATE.md",
    "src/gtos_context_os",
    "tests/test_gtos_context_os.py",
)


def build_resume_bundle(
    task: str,
    *,
    repo: Path | str = ".",
    db_path: Path | str = DEFAULT_DB_PATH,
    profile: str = "ultimate",
    route: str | None = None,
    limit: int = 10,
    include_memory: bool = True,
    include_second_brain: bool = True,
    second_brain_root: Path | str | None = DEFAULT_SECOND_BRAIN_ROOT,
    write_capsule: bool = True,
    markdown_pack: bool = False,
) -> dict[str, Any]:
    """Build the one-stop resume object for interrupted Context OS sessions."""

    repo_path = Path(repo).resolve()
    build_result = build_catalog(repo=repo_path, db_path=db_path)
    capsule_path: str | None = None
    if write_capsule:
        capsule = create_session_capsule(
            "Context OS Resume Checkpoint",
            "Generated a resume bundle with fresh catalog, health, pack, git state, and continuity context.",
            task=task,
            sources=[
                "src/gtos_context_os/resume.py",
                "src/gtos_context_os/health.py",
                "src/gtos_context_os/pack.py",
            ],
            commands=[f"python3 scripts/gtos_context.py resume --task {task!r}"],
            decisions=[
                "Resume bundles are local continuity hints and must be verified against current disk before action."
            ],
            repo=repo_path,
        )
        capsule_path = capsule.as_posix()

    health = context_intelligence_health(
        repo=repo_path,
        db_path=db_path,
        second_brain_root=second_brain_root,
    )
    pack = build_context_pack(
        task,
        repo=repo_path,
        db_path=db_path,
        limit=limit,
        profile=profile,
        route=route,
        include_memory=include_memory,
        include_second_brain=include_second_brain,
        second_brain_root=second_brain_root,
        auto_build=True,
        auto_rebuild_stale=True,
    )
    return {
        "schema_version": "gtos_context_resume_bundle_v1",
        "generated_at_utc": utc_now(),
        "repo": repo_path.as_posix(),
        "task": task,
        "profile": profile,
        "route": route,
        "catalog_build": {
            "db_path": build_result.db_path.as_posix(),
            "indexed_documents": build_result.indexed_documents,
            "metadata_only_documents": build_result.metadata_only_documents,
            "skipped_paths": build_result.skipped_paths,
            "reused_existing": build_result.reused_existing,
            "generated_at_utc": build_result.generated_at_utc,
        },
        "health": health,
        "git_state": _git_state(repo_path),
        "recent_session_capsules": list_session_capsules(repo=repo_path, limit=5),
        "created_resume_capsule": capsule_path,
        "pack": pack,
        "pack_markdown": render_markdown_pack(pack) if markdown_pack else None,
        "use_boundary": "resume_bundle_is_context_intelligence_verify_against_current_disk",
    }


def _git_state(repo_path: Path) -> dict[str, Any]:
    return {
        "head": _git(["rev-parse", "HEAD"], repo_path),
        "branch": _git(["rev-parse", "--abbrev-ref", "HEAD"], repo_path),
        "context_os_dirty": _git_status(repo_path, CONTEXT_OS_SCOPE),
        "scope": "context_os_bounded_status_not_full_repo_porcelain",
    }


def _git(args: list[str], repo_path: Path) -> str:
    try:
        return subprocess.check_output(
            ["git", *args],
            cwd=repo_path,
            text=True,
            stderr=subprocess.DEVNULL,
            timeout=5,
        ).strip()
    except (OSError, subprocess.CalledProcessError, subprocess.TimeoutExpired):
        return "unknown"


def _git_status(repo_path: Path, paths: tuple[str, ...]) -> dict[str, Any]:
    try:
        output = subprocess.check_output(
            ["git", "status", "--short", "--untracked-files=all", "--", *paths],
            cwd=repo_path,
            text=True,
            stderr=subprocess.DEVNULL,
            timeout=10,
        )
    except (OSError, subprocess.CalledProcessError, subprocess.TimeoutExpired) as exc:
        return {"status": "unavailable", "error": type(exc).__name__, "entries": []}
    entries = [line for line in output.splitlines() if line.strip()]
    return {
        "status": "ok",
        "count": len(entries),
        "entries": entries[:80],
        "truncated": len(entries) > 80,
    }
