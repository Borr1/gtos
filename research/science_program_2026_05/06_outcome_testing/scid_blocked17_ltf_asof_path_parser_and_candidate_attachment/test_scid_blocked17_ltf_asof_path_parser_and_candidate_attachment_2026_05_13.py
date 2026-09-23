"""Focused tests for Blocked17 LTF as-of parser/source attachment."""

from __future__ import annotations

import json

import build_scid_blocked17_ltf_asof_path_parser_and_candidate_attachment_2026_05_13 as builder


def load_json(name: str) -> dict:
    return json.loads((builder.ROUTE_DIR / name).read_text(encoding="utf-8"))


def test_source_exists_rows_are_parser_bound_and_hash_asof_attached() -> None:
    matrix = load_json(f"{builder.PREFIX}_PARSER_SOURCE_HASH_ATTACHMENT_MATRIX_{builder.DATE}.json")

    assert matrix["source_exists_card_count"] == 13
    assert matrix["source_exists_input_field_row_count"] == 78
    assert matrix["attachment_row_count"] == 78
    assert matrix["all_source_exists_rows_closed_or_exact_requirement_attached"] is True

    required_families = {
        "accepted_scid_m15_source_control_bars",
        "sierra_converted_m1_m5_m15_ohlcv_roots",
        "prior_production_mt5_tick_parquet_market_context",
        "forward_capture_ltf_availability_schema",
    }
    for row in matrix["attachment_rows"]:
        assert row["input_status"] == "SOURCE_EXISTS_NEEDS_PARSER"
        assert row["parser_bound"] is True
        assert row["source_hash_or_exact_hash_requirement_attached"] is True
        assert row["decision_window_asof_requirement_attached"] is True
        assert row["may_score_results_now"] is False
        assert row["result_scoring_opened"] is False
        assert required_families <= {binding["source_family"] for binding in row["parser_bindings"]}


def test_denominator_preserves_blocked17_and_excludes_other_denominators() -> None:
    noleak = load_json(f"{builder.PREFIX}_DENOMINATOR_NOLEAK_AUDIT_{builder.DATE}.json")

    assert noleak["ok"] is True
    assert noleak["included_blocked17_count"] == 17
    assert noleak["source_exists_card_count"] == 13
    assert noleak["source_exists_field_row_count"] == 78
    assert noleak["excluded_blocked15_count"] == 15
    assert noleak["ready8_excluded_count"] == 8
    assert noleak["expansion_candidate_count_outside_denominator"] == 8
    assert set(noleak["included_blocked17_card_ids"]).isdisjoint(noleak["ready8_excluded_card_ids"])
    assert set(noleak["included_blocked17_card_ids"]).isdisjoint(
        noleak["expansion_candidate_ids_outside_denominator"]
    )
    assert noleak["raw_market_blob_commits_added"] == 0
    assert noleak["broker_native_cfd_truth_claims"] == 0


def test_candidate_decision_window_manifest_is_input_only_and_fail_closed() -> None:
    manifest = load_json(f"{builder.PREFIX}_CANDIDATE_DECISION_WINDOW_ASOF_MANIFEST_{builder.DATE}.json")
    rowset = manifest["candidate_rowset"]

    assert rowset["candidate_input_row_count"] == 3014
    assert rowset["manifest_candidate_input_row_count"] == 3014
    assert rowset["forbidden_field_scan_fail_count"] == 0
    assert rowset["duplicate_key_collision_count"] == 0
    assert rowset["all_rows_input_only"] is True
    assert manifest["result_scoring_opened"] is False
    assert manifest["validation_execution_allowed"] is False
    assert "decision_asof_utc" in " ".join(manifest["decision_window_asof_rules"])
    assert "decision_minus_window_start_utc" in " ".join(manifest["decision_window_asof_rules"])
    assert manifest["source_family_coverage"]["sierra_converted_m1_m5_m15_ohlcv_roots"][
        "source_file_count"
    ] == 150
    assert manifest["source_family_coverage"]["prior_production_mt5_tick_parquet_market_context"][
        "source_file_count"
    ] == 93


def test_missing_parser_access_ledger_has_exact_requirements_not_vague_blockers() -> None:
    ledger = load_json(f"{builder.PREFIX}_MISSING_PARSER_ACCESS_LEDGER_{builder.DATE}.json")

    assert ledger["vague_blocker_count"] == 0
    assert ledger["source_exists_rows_left_as_unreduced_blocker"] == 0
    assert ledger["exact_requirement_count"] >= 4
    for requirement in ledger["exact_requirements"]:
        assert requirement["exact_action"]
        assert requirement["status"].startswith("EXACT_")
        lowered = json.dumps(requirement, sort_keys=True).lower()
        assert "future work" not in lowered
        assert "needs more data" not in lowered
        assert "unknown" not in lowered
        assert "maybe" not in lowered


def test_next_g12_prompt_and_starter_preserve_safe_flags() -> None:
    prompt = builder.NEXT_G12_PROMPT.read_text(encoding="utf-8")
    starter = builder.NEXT_G12_STARTER.read_text(encoding="utf-8")
    output_manifest = load_json(f"{builder.PREFIX}_OUTPUT_MANIFEST_{builder.DATE}.json")

    for token in ("NO_PROMOTION_VERDICT", "validation_safe=false", "outcome_review_opened=false", "live_effect=false"):
        assert token in prompt
        assert token in starter
    assert output_manifest["required_outputs_present"]["LTF parser/source hash attachment matrix"] is True
    assert output_manifest["required_outputs_present"]["candidate decision-window as-of manifest"] is True
    assert output_manifest["required_outputs_present"]["missing parser/access ledger"] is True
    assert output_manifest["required_outputs_present"]["G12 source-status repair audit prompt/starter"] is True

