from __future__ import annotations

from pathlib import Path

from src.components.workspace_paths import (
    resolve_gtos_integration_repo,
    resolve_gtos_workspace_root,
)


def test_mac_local_cutover_prefers_active_workspace_repo(tmp_path: Path) -> None:
    active_repo = tmp_path / "GTOSActive/repo"
    integration_repo = tmp_path / "home/Documents/gtos/repo/ai-trading-agent"
    active_repo.mkdir(parents=True)
    integration_repo.mkdir(parents=True)

    resolved_repo = resolve_gtos_integration_repo(
        active_repo,
        environ={},
        home=tmp_path / "home",
    )
    resolved_workspace = resolve_gtos_workspace_root(
        active_repo,
        integration_repo=resolved_repo,
        environ={},
        home=tmp_path / "home",
    )

    assert resolved_repo == active_repo
    assert resolved_workspace == tmp_path / "GTOSActive"


def test_mac_local_worktree_resolves_active_workspace_repo(tmp_path: Path) -> None:
    active_repo = tmp_path / "GTOSActive/repo"
    worktree = tmp_path / "GTOSActive/worktrees/attempt5"
    retired_repo = tmp_path / "home/Documents/gtos/repo/ai-trading-agent"
    active_repo.mkdir(parents=True)
    worktree.mkdir(parents=True)
    retired_repo.mkdir(parents=True)

    assert (
        resolve_gtos_integration_repo(
            worktree,
            environ={},
            home=tmp_path / "home",
        )
        == active_repo
    )
    assert (
        resolve_gtos_workspace_root(
            worktree,
            environ={},
            home=tmp_path / "home",
        )
        == tmp_path / "GTOSActive"
    )


def test_explicit_repo_and_workspace_overrides_take_precedence(tmp_path: Path) -> None:
    active_repo = tmp_path / "GTOSActive/repo"
    integration_repo = tmp_path / "evidence/integration"
    workspace = tmp_path / "evidence"
    active_repo.mkdir(parents=True)
    integration_repo.mkdir(parents=True)

    env = {
        "GTOS_MAIN_REPO_ROOT": str(integration_repo),
        "GTOS_WORKSPACE_ROOT": str(workspace),
    }
    assert resolve_gtos_integration_repo(active_repo, environ=env) == integration_repo
    assert (
        resolve_gtos_workspace_root(
            active_repo,
            integration_repo=integration_repo,
            environ=env,
        )
        == workspace
    )
