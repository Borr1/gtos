from __future__ import annotations

from src.research_infra.ai_decision_architecture_audit import (
    ai_architecture_config_audit_row,
    ai_architecture_confidence_filter_quarantine_row,
    ai_architecture_malformed_response_audit_row,
    ai_architecture_selector_dossier_audit_row,
    classify_malformed_ai_response,
    summarize_b12_confidence_autopsy,
    summarize_ai_architecture_audit_rows,
)


def test_classify_malformed_ai_response_separates_flat_refusal_and_fenced_json():
    assert (
        classify_malformed_ai_response(
            {
                "error": "Expecting value: line 1 column 1 (char 0)",
                "raw_response_length": 38,
                "raw_response": "Sorry, I can't produce JSON right now.",
            }
        )
        == "FLAT_REFUSAL_OR_SHORT_NON_JSON"
    )
    assert (
        classify_malformed_ai_response(
            {
                "error": "Extra data: line 70 column 1 (char 3378)",
                "raw_response_length": 4378,
                "raw_response": "```json\n{\"decision\":\"CANDIDATE\"}\n```",
            }
        )
        == "JSON_FENCE_OR_TRAILING_TEXT_PARSE_FAILURE"
    )


def test_ai_architecture_config_audit_extracts_cost_controls_without_runtime_enablement():
    row = ai_architecture_config_audit_row(
        """
ai:
  billing_mode: "api"
  primary_model: "claude-sonnet-4-6"
  primary_effort: "max"
  timeout_retry_enabled: false
session_memory_enabled: false
confidence_filter_mode: "shadow"
""",
        audit_row_id="AI-AUDIT-1",
        source_artifact="config.yaml",
        source_sha256="cfg-sha",
    )

    assert row["ai_billing_mode"] == "api"
    assert row["ai_primary_model"] == "claude-sonnet-4-6"
    assert row["ai_timeout_retry_enabled"] is False
    assert row["session_memory_enabled"] is False
    assert row["runtime_candidate_use_permitted"] is False
    assert row["production_change_opened_now"] is False


def test_ai_architecture_audit_summary_preserves_no_api_no_runtime_boundary():
    malformed = ai_architecture_malformed_response_audit_row(
        [
            {
                "timestamp": "2026-05-18T00:00:00+00:00",
                "attempt": 1,
                "error": "Expecting value: line 1 column 1 (char 0)",
                "raw_response_length": 8,
                "raw_response": "not json",
            }
        ],
        audit_row_id="AI-AUDIT-1",
        source_artifact="malformed.jsonl",
        source_sha256="malformed-sha",
    )
    selector = ai_architecture_selector_dossier_audit_row(
        {
            "rows": 231,
            "mechanical_selector_scope_draft_ready_for_separate_review_rows": 221,
            "capacity_blocked_selector_blocklist_required_rows": 32,
            "implementation_ready_candidate_rows": 1597,
            "capacity_blocked_candidate_rows": 151,
            "production_change_opened_now_rows": 0,
            "runtime_candidate_use_permitted_rows": 0,
        },
        audit_row_id="AI-AUDIT-2",
        source_artifact="selector_summary.json",
        source_sha256="selector-sha",
    )
    summary = summarize_ai_architecture_audit_rows([malformed, selector])

    assert summary["rows"] == 2
    assert summary["malformed_response_rows"] == 1
    assert summary["selector_dossier_rows"] == 231
    assert summary["mechanical_selector_scope_draft_ready_for_separate_review_rows"] == 221
    assert summary["paid_api_or_vendor_call_rows"] == 0
    assert summary["runtime_candidate_use_permitted_rows"] == 0
    assert summary["production_change_opened_now_rows"] == 0


def test_summarize_b12_confidence_autopsy_counts_predictive_and_tested_strata():
    summary = summarize_b12_confidence_autopsy(
        {
            "distribution": {"n": 25, "mean": 78.0, "mode": 80, "mode_fraction": 0.8, "fraction_at_80": 0.8},
            "family_size": 1,
            "min_n": 20,
            "alpha": 0.05,
            "rho_threshold": 0.2,
            "n_perms": 1000,
            "seed": 1,
            "strata_axes": ["symbol", "regime"],
            "all_results": [
                {"flag": "NOT_PREDICTIVE", "n": 25},
                {"flag": "INSUFFICIENT_N", "n": 4},
                {"flag": "DEGENERATE", "n": 20},
            ],
            "predictive": [],
        }
    )

    assert summary["b12_confidence_trades_evaluated"] == 25
    assert summary["b12_confidence_family_size"] == 1
    assert summary["b12_confidence_total_strata_observed"] == 3
    assert summary["b12_confidence_tested_strata"] == 1
    assert summary["b12_confidence_predictive_strata"] == 0


def test_confidence_filter_quarantine_row_blocks_active_promotion_without_runtime_use():
    row = ai_architecture_confidence_filter_quarantine_row(
        """
confidence_filter_mode: "shadow"
confidence:
  price_range: [1500.0, 6000.0]
""",
        {
            "distribution": {"n": 312, "mean": 76.2, "mode": 72, "mode_fraction": 0.36, "fraction_at_80": 0.21},
            "family_size": 8,
            "min_n": 20,
            "alpha": 0.05,
            "rho_threshold": 0.2,
            "n_perms": 1000,
            "seed": 1,
            "strata_axes": ["symbol"],
            "all_results": [{"flag": "NOT_PREDICTIVE", "n": 58}],
            "predictive": [],
        },
        orchestrator_text='if conf_mode == "active":\n    return "SKIPPED_LOW_CONFIDENCE"',
        confidence_scorer_text="_PRICE_RANGE = (1500.0, 6000.0)",
        audit_row_id="AI-AUDIT-CONFIDENCE-1",
        source_artifact="config/agent_config.yaml",
        source_sha256="cfg-sha",
        b12_source_artifact="research/ai_behavior/B12_confidence/autopsy.json",
        b12_source_sha256="b12-sha",
    )

    assert row["audit_surface"] == "confidence_filter_quarantine"
    assert row["confidence_filter_shadow_mode_configured"] is True
    assert row["confidence_filter_active_branch_present"] is True
    assert row["b12_confidence_predictive_strata"] == 0
    assert row["ai_architecture_action"] == (
        "KEEP_CONFIDENCE_FILTER_SHADOW_AND_BLOCK_ACTIVE_PROMOTION_WITHOUT_FRESH_VALIDATION"
    )
    assert row["runtime_candidate_use_permitted"] is False
    assert row["production_change_opened_now"] is False
