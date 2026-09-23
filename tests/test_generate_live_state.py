from __future__ import annotations

from scripts import generate_live_state


def test_config_formatter_distinguishes_explicit_null_from_missing():
    cfg = {"risk": {"max_concurrent": None}}

    assert generate_live_state.dig(cfg, "risk.max_concurrent") is None
    assert generate_live_state.format_config_value(None) == "`null`"
    assert generate_live_state.dig(cfg, "risk.missing") is generate_live_state.MISSING
    assert generate_live_state.format_config_value(generate_live_state.MISSING) == "_missing_"


def test_live_supervision_paths_are_research_relevant():
    paths = set(generate_live_state.RESEARCH_RELEVANT_PATHS)

    assert ".tools/monitor_books.py" in paths
    assert "scripts/run_book_supervisor.ps1" in paths
    assert "src/components/ultimate_book/" in paths
    assert "src/components/ai_companion/" in paths
    assert "src/components/data_ingestion.py" in paths
    assert "src/components/execution.py" in paths
    assert "src/components/slippage_shadow_logger.py" in paths
    assert "src/notifications.py" in paths
    assert "tests/test_runtime_control_atomic_halt.py" in paths
    assert "tests/test_account_pnl_truth_reconciler.py" in paths
    assert "tests/test_notifications.py" in paths


def test_lfs_hydration_report_distinguishes_head_mismatch_from_pointer_only(
    tmp_path,
    monkeypatch,
):
    pointer_path = tmp_path / "shadow_logs" / "slippage.jsonl"
    readable_path = tmp_path / "shadow_logs" / "daily_pnl_history.jsonl"
    pointer_path.parent.mkdir(parents=True)
    pointer_path.write_text(
        "version https://git-lfs.github.com/spec/v1\n"
        "oid sha256:abc\n"
        "size 123\n",
        encoding="utf-8",
    )
    readable_path.write_text('{"readable":true}\n', encoding="utf-8")
    monkeypatch.setattr(generate_live_state, "REPO_ROOT", tmp_path)
    monkeypatch.setattr(generate_live_state, "sparse_checkout_paths", lambda: (False, []))
    monkeypatch.setattr(
        generate_live_state,
        "run",
        lambda *_args, **_kwargs: (
            "abc - shadow_logs/daily_pnl_history.jsonl\n"
            "def - shadow_logs/slippage.jsonl\n"
        ),
    )

    status = generate_live_state.git_lfs_hydration_status()

    assert status["lfs_head_missing_or_mismatch_count"] == 2
    assert status["worktree_pointer_only_count"] == 1
    assert status["lfs_head_missing_or_mismatch_paths"] == [
        "shadow_logs/daily_pnl_history.jsonl",
        "shadow_logs/slippage.jsonl",
    ]
    assert status["worktree_pointer_only_paths"] == ["shadow_logs/slippage.jsonl"]
