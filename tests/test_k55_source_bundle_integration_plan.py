from __future__ import annotations

import json
from pathlib import Path

from scripts import build_k55_source_bundle_integration_plan as script
from src.research_infra import k55_source_bundle_integration_plan as mod


def _write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, sort_keys=True) + "\n", encoding="utf-8")


def _seed_artifacts(root: Path) -> None:
    _write_json(
        root / "research/program_control/LTO031_LTO032_SOURCE_CONTRACT_REGISTRY_2026-05-06.json",
        {
            "schema_version": "registry_v1",
            "status": "SOURCE_CONTRACT_REGISTRY_READY_RESEARCH_ONLY",
            "promotion_verdict": "NO_PROMOTION_VERDICT",
            "source_contract_count": 11,
            "validation_safe_counts": {"false": 11},
            "validation_issues": [],
        },
    )
    _write_json(
        root / "research/program_control/LTO031_LTO032_FREE_PUBLIC_SOURCE_MANIFESTS_2026-05-06.json",
        {
            "schema_version": "free_public_v1",
            "status": "FREE_PUBLIC_SOURCE_MANIFESTS_READY_NO_FETCH",
            "promotion_verdict": "NO_PROMOTION_VERDICT",
            "manifest_count": 5,
            "validation_safe_counts": {"false": 5, "true": 0},
            "validation_issues": [],
        },
    )
    _write_json(
        root / "research/program_control/LTO031_LTO032_DATABENTO_CREDIT_REPLAY_MANIFESTS_2026-05-06.json",
        {
            "schema_version": "databento_v1",
            "status": "DATABENTO_CREDIT_REPLAY_MANIFESTS_READY_ESTIMATE_REQUIRED",
            "promotion_verdict": "NO_PROMOTION_VERDICT",
            "request_count": 8,
            "validation_issues": [],
        },
    )
    _write_json(
        root / "research/program_control/LTO031_LTO032_SIERRA_SCID_FOOTPRINT_PROFILE_PLAN_2026-05-06.json",
        {
            "schema_version": "sierra_v1",
            "status": "SIERRA_SCID_FOOTPRINT_PROFILE_PLAN_READY_SHADOW_ONLY",
            "promotion_verdict": "NO_PROMOTION_VERDICT",
            "sierra_inventory": {"csv_file_count": 125},
            "validation_issues": [],
        },
    )
    _write_json(
        root / "research/program_control/LTO032_OPTIONS_GAMMA_VRP_SOURCE_MANIFESTS_2026-05-06.json",
        {
            "schema_version": "options_v1",
            "status": "OPTIONS_GAMMA_VRP_SOURCE_MANIFESTS_READY_NO_FETCH",
            "promotion_verdict": "NO_PROMOTION_VERDICT",
            "source_row_count": 4,
            "validation_safe_counts": {"false": 4, "true": 0},
            "validation_issues": [],
        },
    )


def test_source_bundle_rows_summarize_all_p0_to_p4_artifacts(tmp_path: Path):
    _seed_artifacts(tmp_path)

    rows = mod.build_source_bundle_rows(tmp_path)
    by_key = {row["bundle_key"]: row for row in rows}

    assert len(rows) == 5
    assert by_key["p0_source_contract_registry"]["count_summary"]["source_contract_count"] == 11
    assert by_key["p1_free_public_existing_feeds"]["count_summary"]["manifest_count"] == 5
    assert by_key["p2_databento_credit_replay"]["count_summary"]["request_count"] == 8
    assert by_key["p3_sierra_scid_footprint_profile"]["count_summary"]["csv_file_count"] == 125
    assert by_key["p4_options_gamma_vrp"]["count_summary"]["source_row_count"] == 4
    assert all(row["k55_provenance_flags_allowed"] is True for row in rows)
    assert all(row["k55_numeric_feature_allowed"] is False for row in rows)


def test_k55_source_bundle_payload_enforces_whitelist_and_stale_k54_rejection(tmp_path: Path):
    _seed_artifacts(tmp_path)

    payload = mod.build_payload(
        repo_root=tmp_path,
        generated_at_utc="2026-05-06T00:00:00+00:00",
    )

    assert payload["status"] == mod.STATUS_READY
    assert payload["promotion_verdict"] == mod.PROMOTION_VERDICT
    assert payload["validation_issues"] == []
    assert payload["source_bundle_ready_for_numeric_features"] == 0
    assert all(
        row["reuse_allowed"] is False
        for row in payload["stale_artifact_policy"]
        if row["artifact_family"].startswith("k54")
    )
    assert mod.feature_key_forbidden_by_external_bundle_policy("broker_actual_r__p1_free_public_existing_feeds")
    assert mod.feature_key_forbidden_by_external_bundle_policy("source_available_unprefixed")
    assert not mod.feature_key_forbidden_by_external_bundle_policy("source_available__p1_free_public_existing_feeds")
    assert not mod.feature_key_forbidden_by_external_bundle_policy("context_flag__vix1d_vix9d_missing_required_terms")


def test_k55_source_bundle_missing_artifacts_are_action_required(tmp_path: Path):
    payload = mod.build_payload(
        repo_root=tmp_path,
        generated_at_utc="2026-05-06T00:00:00+00:00",
    )

    assert payload["status"] == "K55_SOURCE_BUNDLE_INTEGRATION_PLAN_ACTION_REQUIRED"
    assert any("ARTIFACT_MISSING_OR_UNREADABLE" in row["validation_issues"] for row in payload["source_bundle_rows"])


def test_k55_source_bundle_payload_has_no_action_counters(tmp_path: Path):
    _seed_artifacts(tmp_path)

    payload = mod.build_payload(
        repo_root=tmp_path,
        generated_at_utc="2026-05-06T00:00:00+00:00",
    )

    assert payload["ai_calls"] == 0
    assert payload["canary_calls"] == 0
    assert payload["order_calls"] == 0
    assert payload["paid_data_calls"] == 0
    assert payload["paid_fetch_attempted"] is False
    assert payload["no_execution"] is True


def test_validation_rejects_numeric_feature_and_stale_k54_reuse(tmp_path: Path):
    _seed_artifacts(tmp_path)
    payload = mod.build_payload(
        repo_root=tmp_path,
        generated_at_utc="2026-05-06T00:00:00+00:00",
    )
    payload["source_bundle_rows"][0]["k55_numeric_feature_allowed"] = True
    payload["stale_artifact_policy"][0]["reuse_allowed"] = True

    issues = mod.validate_payload(payload)

    assert "p0_source_contract_registry:NUMERIC_FEATURE_ALLOWED_BEFORE_ASOF_ROWS" in issues
    assert "k54_v2:STALE_K54_REUSE_ALLOWED" in issues


def test_script_writes_k55_source_bundle_artifacts(tmp_path: Path):
    _seed_artifacts(tmp_path)
    out_json = tmp_path / "k55_source_bundle.json"
    out_md = tmp_path / "k55_source_bundle.md"
    ops_md = tmp_path / "ops.md"

    assert script.main(
        [
            "--repo-root",
            str(tmp_path),
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
    assert "Stale K54 v2/v3/v4 artifacts are rejected" in ops_md.read_text(encoding="utf-8")
