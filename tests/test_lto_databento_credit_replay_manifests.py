from __future__ import annotations

from pathlib import Path

from scripts import build_lto031_lto032_databento_credit_replay_manifests as script
from src.research_infra import lto_databento_credit_replay_manifests as mod


def _write(path: Path, text: str = "x") -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def _seed_databento(root: Path) -> None:
    _write(
        root
        / "GLBX.MDP3/mbp-10/GLBX.MDP3.mbp-10.NQ.v.0.2026-04-28T12_15_00_00_00_2026-04-28T18_00_00_00_00.full.dbn.zst"
    )
    _write(
        root
        / "GLBX.MDP3/mbp-10/GLBX.MDP3.mbp-10.NQ.v.0.2026-04-28T12_15_00_00_00_2026-04-28T18_00_00_00_00.full.dbn.zst.meta.json",
        "{}",
    )
    _write(
        root
        / "GLBX.MDP3/trades/GLBX.MDP3.trades.6B.v.0.2026-04-17T07_00_00_00_00_2026-04-17T09_00_00_00_00.full.dbn.zst"
    )


def test_databento_inventory_counts_schema_symbol_and_metadata(tmp_path: Path):
    raw_root = tmp_path / "data/external/raw/databento"
    _seed_databento(raw_root)

    inventory = mod.inventory_databento_raw(raw_root, repo_root=tmp_path)

    assert inventory["raw_file_count"] == 2
    assert inventory["metadata_file_count"] == 1
    assert inventory["files_by_schema"] == {"mbp-10": 1, "trades": 1}
    assert inventory["files_by_symbol"]["NQ.v.0"] == 1
    assert inventory["files_by_symbol"]["6B.v.0"] == 1


def test_replay_manifest_requires_estimate_before_fetch_and_no_live_collector(tmp_path: Path):
    payload = mod.build_payload(
        repo_root=tmp_path,
        raw_root=tmp_path / "missing",
        generated_at_utc="2026-05-06T00:00:00+00:00",
    )

    assert payload["status"] == mod.STATUS_READY
    assert payload["promotion_verdict"] == mod.PROMOTION_VERDICT
    assert payload["credit_policy"]["use_existing_credits_only"] is True
    assert payload["credit_policy"]["estimate_before_fetch"] is True
    assert payload["live_collector_enabled"] is False
    assert payload["fetch_ready_count"] == 0
    assert payload["paid_data_calls"] == 0
    assert payload["paid_fetch_attempted"] is False
    assert all(row["estimate_ready"] is False for row in payload["requests"])
    assert all(row["fetch_allowed"] is False for row in payload["requests"])


def test_replay_manifest_separates_decision_features_from_post_event_labels(tmp_path: Path):
    payload = mod.build_payload(
        repo_root=tmp_path,
        raw_root=tmp_path / "missing",
        generated_at_utc="2026-05-06T00:00:00+00:00",
    )

    assert payload["validation_issues"] == []
    for row in payload["requests"]:
        assert row["window_template"]["decision_cutoff_utc"] == "DYNAMIC_CANDIDATE_DECISION_TIME_UTC"
        assert "ts_event <= decision_cutoff_utc" in row["decision_time_feature_policy"]
        assert "Post-decision rows" in row["post_event_label_policy"]


def test_replay_manifest_preserves_proxy_and_source_definition_blockers(tmp_path: Path):
    payload = mod.build_payload(
        repo_root=tmp_path,
        raw_root=tmp_path / "missing",
        generated_at_utc="2026-05-06T00:00:00+00:00",
    )
    rows = {row["request_id"]: row for row in payload["requests"]}

    assert rows["P2_XAGUSD_SI_MBP10_DECISION_WINDOW_V1"]["status"] == "BLOCKED_SOURCE_DEFINITION_BEFORE_ESTIMATE"
    assert "SI_SOURCE_DEPTH_DEFINITION_BLOCKED" in rows["P2_XAGUSD_SI_MBP10_DECISION_WINDOW_V1"]["fetch_blockers"]
    assert rows["P2_USDJPY_6J_TRADES_DECISION_WINDOW_V1"]["status"] == "BLOCKED_PROXY_TRANSFER_REVIEW_BEFORE_ESTIMATE"
    assert "USDJPY_6J_INVERSE_TRANSFER_POLICY_OPEN" in rows["P2_USDJPY_6J_TRADES_DECISION_WINDOW_V1"]["fetch_blockers"]
    assert rows["P2_GBPUSD_6B_TRADES_DECISION_WINDOW_V1"]["status"] == "BLOCKED_ALIGNMENT_POLICY_BEFORE_ESTIMATE"
    assert "GBPUSD_6B_COMMON_SECOND_ALIGNMENT_REQUIRED" in rows["P2_GBPUSD_6B_TRADES_DECISION_WINDOW_V1"]["fetch_blockers"]


def test_validation_rejects_fetch_allowed_without_estimate():
    rows = mod.build_request_templates()
    rows[0]["fetch_allowed"] = True

    issues = mod.validate_requests(rows)

    assert "P2_NAS100_NQ_TRADES_DECISION_WINDOW_V1:FETCH_ALLOWED_WITHOUT_ESTIMATE" in issues
    assert "P2_NAS100_NQ_TRADES_DECISION_WINDOW_V1:FETCH_ALLOWED_WITHOUT_COST" in issues


def test_script_writes_replay_manifest_artifacts(tmp_path: Path):
    raw_root = tmp_path / "data/external/raw/databento"
    _seed_databento(raw_root)
    out_json = tmp_path / "databento.json"
    out_md = tmp_path / "databento.md"
    ops_md = tmp_path / "ops.md"

    assert script.main(
        [
            "--repo-root",
            str(tmp_path),
            "--raw-root",
            str(raw_root),
            "--output-json",
            str(out_json),
            "--output-md",
            str(out_md),
            "--operations-md",
            str(ops_md),
            "--generated-at-utc",
            "2026-05-06T00:00:00+00:00",
        ]
    ) == 0

    assert out_json.exists()
    assert out_md.exists()
    assert ops_md.exists()
    assert "NO_PROMOTION_VERDICT" in out_md.read_text(encoding="utf-8")
    assert "No request is fetch-ready yet" in ops_md.read_text(encoding="utf-8")
