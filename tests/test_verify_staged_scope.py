from scripts.verify_staged_scope import (
    is_live_runtime_dirt,
    normalize_repo_path,
    verify_paths,
)


def test_normalize_repo_path_uses_posix_style():
    assert normalize_repo_path(r".\shadow_logs\decisions.jsonl") == "shadow_logs/decisions.jsonl"


def test_verify_staged_scope_blocks_live_runtime_dirt():
    result = verify_paths(
        [
            "src/components/gtos_vnext_runtime.py",
            "shadow_logs/gtos_vnext_runtime_decisions.jsonl",
            ".context/LIVE_STATE.md",
            "pipeline_state/heartbeat_XAUUSD.json",
        ]
    )

    assert result.ok is False
    assert result.blocked_paths == (
        "shadow_logs/gtos_vnext_runtime_decisions.jsonl",
        ".context/LIVE_STATE.md",
        "pipeline_state/heartbeat_XAUUSD.json",
    )


def test_verify_staged_scope_allows_explicit_override_for_separate_context_commit():
    result = verify_paths(
        [".context/LIVE_STATE.md", "tests/test_verify_staged_scope.py"],
        allow=[".context/LIVE_STATE.md"],
    )

    assert result.ok is True
    assert result.allowed_overrides == (".context/LIVE_STATE.md",)


def test_is_live_runtime_dirt_does_not_block_research_or_source_files():
    assert is_live_runtime_dirt("research/output.jsonl") is False
    assert is_live_runtime_dirt("src/components/orchestrator.py") is False
