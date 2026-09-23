from __future__ import annotations

import json
from pathlib import Path

from scripts.audit_v4u_exit_policy_close_marks import build_audit


def _write_jsonl(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row) + "\n")


def test_close_mark_audit_preserves_exact_source_requirement(tmp_path: Path) -> None:
    route = tmp_path / "route"
    replay = route / "repaired_full_replay_wave4r_named"
    shard = tmp_path / "dynamic.jsonl"
    _write_jsonl(
        shard,
        [
            {
                "candidate_id": "cand-1",
                "dynamic_policy_replay": {
                    "policy_results": {
                        "time_stop_only": {
                            "exit_reason": "time_stop",
                            "exit_time_utc": "2026-01-01 03:00:00",
                            "final_r": 0.25,
                        }
                    }
                },
            }
        ],
    )
    _write_jsonl(
        replay / "WAVE4R_CANDIDATE_TRADE_MICROSCOPE_LEDGER.jsonl",
        [
            {
                "candidate_id": "cand-bound",
                "exit_policy_action": "CLOSE_TIME_STOP",
                "exit_policy_result_source_status": "exit_policy_close_mark_replay_bound",
                "exit_policy_close_mark": {
                    "source_status": (
                        "m15_local_close_mark_replay_bound_source_sha_mismatch"
                    ),
                    "source_hash_match_status": "source_sha256_mismatch",
                },
            },
            {
                "candidate_id": "cand-1",
                "asof_utc": "2026-01-01T00:00:00+00:00",
                "symbol": "XAUUSD",
                "side": "LONG",
                "exit_policy_action": "CLOSE_TIME_STOP",
                "exit_policy_close_reason": "v4_time_stop",
                "exit_policy_result_source_status": (
                    "exit_policy_close_mark_source_gap_result_unadjusted"
                ),
                "source_path": "missing_XAUUSD_M15.csv",
                "source_sha256": "a" * 64,
                "dynamic_shard_path": str(shard),
                "current_v4_policy_result_source": "fallback_momentum_proxy",
            }
        ],
    )
    source_root = tmp_path / "sources"
    source_root.mkdir()
    (source_root / "XAUUSD_M15.csv").write_text(
        "time,open,high,low,close\n2026-01-01T00:00:00Z,1,1,1,1\n",
        encoding="utf-8",
    )

    report, requirement_rows = build_audit(route, [source_root])

    assert report["close_mark_gap_rows"] == 1
    assert report["close_mark_action_rows"] == 2
    assert report["materialized_close_mark_rows"] == 1
    assert report["materialized_source_status_counts"] == {
        "m15_local_close_mark_replay_bound_source_sha_mismatch": 1
    }
    assert report["materialized_source_hash_match_status_counts"] == {
        "source_sha256_mismatch": 1
    }
    assert report["source_hashes_with_exact_local_match"] == 0
    assert report["dynamic_reuse_status_counts"] == {
        "not_reusable_as_v4_close_mark_without_v4_policy_id_action_reason_and_bar_clock": 1
    }
    assert requirement_rows[0]["source_hash_exact_local_matches"] == []
    assert requirement_rows[0]["required_policy_id"] == "v4_exit_policy_close_mark_v1"
    assert "bars_elapsed" in requirement_rows[0]["required_close_mark_fields"]


def test_close_mark_audit_does_not_hash_default_roots_without_explicit_source_root(
    tmp_path: Path,
) -> None:
    route = tmp_path / "route"
    replay = route / "repaired_full_replay_wave4r_named"
    shard = tmp_path / "dynamic.jsonl"
    _write_jsonl(shard, [{"candidate_id": "cand-1"}])
    _write_jsonl(
        replay / "WAVE4R_CANDIDATE_TRADE_MICROSCOPE_LEDGER.jsonl",
        [
            {
                "candidate_id": "cand-1",
                "exit_policy_action": "CLOSE_TIME_STOP",
                "exit_policy_result_source_status": (
                    "exit_policy_close_mark_source_gap_result_unadjusted"
                ),
                "source_sha256": "a" * 64,
                "dynamic_shard_path": str(shard),
            }
        ],
    )

    report, requirement_rows = build_audit(route, [])

    assert report["close_mark_gap_rows"] == 1
    assert report["materialized_close_mark_rows"] == 0
    assert report["source_roots_checked"] == []
    assert report["source_hash_match_status"] == "not_checked_no_source_roots_supplied"
    assert report["source_hashes_with_exact_local_match"] == 0
    assert requirement_rows[0]["dynamic_policy_status"]["dynamic_row_status"] == "found"
