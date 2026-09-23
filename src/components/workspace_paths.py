"""Portable local workspace path resolution for GTOS research tooling."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Mapping


def _configured_path(
    environ: Mapping[str, str],
    *keys: str,
) -> Path | None:
    for key in keys:
        value = str(environ.get(key) or "").strip()
        if value:
            return Path(value).expanduser()
    return None


def _active_workspace_root(active_repo_root: Path) -> Path | None:
    """Return the enclosing GTOSActive workspace for a repo or worktree."""

    active_root = Path(active_repo_root).expanduser()
    for candidate in (active_root, *active_root.parents):
        if candidate.name == "GTOSActive":
            return candidate
    return None


def resolve_gtos_integration_repo(
    active_repo_root: Path,
    *,
    environ: Mapping[str, str] | None = None,
    home: Path | None = None,
) -> Path:
    """Resolve the separate integration/evidence repo across normal and hot layouts."""

    env = os.environ if environ is None else environ
    active_root = Path(active_repo_root).expanduser()
    home_root = Path.home() if home is None else Path(home).expanduser()
    configured_repo = _configured_path(
        env,
        "GTOS_MAIN_REPO_ROOT",
        "GTOS_REPO_ROOT",
    )
    configured_workspace = _configured_path(env, "GTOS_WORKSPACE_ROOT")
    active_workspace = _active_workspace_root(active_root)
    candidates = [
        configured_repo,
        active_workspace / "repo" if active_workspace is not None else None,
        active_root.parent / "ai-trading-agent",
        (
            configured_workspace / "repo/ai-trading-agent"
            if configured_workspace is not None
            else None
        ),
        home_root / "Documents/gtos/repo/ai-trading-agent",
    ]
    for candidate in candidates:
        if candidate is not None and candidate.is_dir():
            return candidate
    return configured_repo or active_root.parent / "ai-trading-agent"


def resolve_gtos_workspace_root(
    active_repo_root: Path,
    *,
    integration_repo: Path | None = None,
    environ: Mapping[str, str] | None = None,
    home: Path | None = None,
) -> Path:
    """Resolve the Mac research workspace without assuming the repo parent layout."""

    env = os.environ if environ is None else environ
    active_root = Path(active_repo_root).expanduser()
    home_root = Path.home() if home is None else Path(home).expanduser()
    configured_workspace = _configured_path(env, "GTOS_WORKSPACE_ROOT")
    active_workspace = _active_workspace_root(active_root)
    resolved_integration = integration_repo or resolve_gtos_integration_repo(
        active_root,
        environ=env,
        home=home_root,
    )
    candidates = [
        configured_workspace,
        active_workspace,
        (
            resolved_integration.parent.parent
            if resolved_integration.parent.name == "repo"
            else None
        ),
        active_root.parent.parent if active_root.parent.name == "repo" else None,
        home_root / "Documents/gtos",
    ]
    for candidate in candidates:
        if candidate is not None and candidate.is_dir():
            return candidate
    return configured_workspace or home_root / "Documents/gtos"
