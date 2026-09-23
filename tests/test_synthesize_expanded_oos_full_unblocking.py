from __future__ import annotations

from scripts import synthesize_expanded_oos_full_unblocking as synth


def _matrix():
    return {
        "summary": {"families_with_ohlcv_adapter_status": 2},
        "families": [
            {
                "family": "NAS100/NDX100 with NQ/MNQ",
                "evidence_class": "FUTURES_PROXY_TRANSFER",
                "replay_or_label_status": "PATH_WORKS_NO_FROZEN_COHORT_MATCH",
                "depth_status": "EXACT_CACHED_MBP10_MATCH_NQ",
                "converted_sources": ["NQM26-CME"],
            },
            {
                "family": "EURUSD with EURUSD/6E",
                "evidence_class": "SAME_MARKET_SOURCE_TRANSFER_AND_FUTURES_PROXY_TRANSFER",
                "replay_or_label_status": "NOT_OPENED",
                "depth_status": "NOT_AUDITED_IN_DEPTH_BATCH",
                "converted_sources": ["EURUSD"],
            },
        ],
    }


def _label_audit():
    return {
        "families": [
            {
                "family": "EURUSD with EURUSD/6E",
                "label_status": "LABEL_STATUS_ONLY_NO_REGISTERED_FROZEN_COHORT",
                "outcome_slice_status": "NOT_OPENED_BY_LABEL_STATUS_AUDIT",
            }
        ]
    }


def _checkpoint():
    return {
        "opened_replay_ledger": [
            {
                "batch_id": "sierra_nq_to_nas100_pilot_20260504",
                "slice": "2026-04-15/2026-04-17",
                "rows_replayed": 10,
                "actions_taken": 0,
                "resolved_r_n": 0,
                "status": "PATH_WORKS_NO_FROZEN_COHORT_MATCH",
            },
            {
                "batch_id": "sierra_xauusd_scid_v2_mtf_pilot_20260504",
                "slice": "2026-04-15/2026-04-17",
                "rows_replayed": 10,
                "take_rows_seen": 2,
                "resolved_r_n_reference": 1,
                "status": "DIAGNOSTIC_POSITIVE_SMALL_N_SOURCE_TRANSFER_ONLY",
            },
        ]
    }


def _registry():
    return {
        "candidates": [
            {
                "candidate_id": "CAND-001-J46-J49-LIVE-BASELINE",
                "rule_name": "baseline",
                "status": "FROZEN_FOR_COMPARISON",
            },
            {
                "candidate_id": "CAND-002-V2-OB-BOUNDARY",
                "rule_name": "v2",
                "status": "FROZEN_DISCOVERY_CANDIDATE",
            },
            {
                "candidate_id": "CAND-005-NAS100-DEPTH-THINNESS",
                "rule_name": "depth",
                "status": "REGISTERED_DIAGNOSTIC_NOT_PROMOTABLE",
            },
        ]
    }


def test_completion_standard_audit_marks_replay_or_label_status_met() -> None:
    rows = synth.completion_standard_audit(
        matrix=_matrix(),
        label_audit=_label_audit(),
        checkpoint=_checkpoint(),
    )

    by_requirement = {row["requirement"]: row for row in rows}
    replay_label = by_requirement["Replay or label-status artifacts for every first-wave family"]

    assert replay_label["status"] == "MET_AS_STATUS_ARTIFACTS_NOT_OUTCOME_REPLAYS"
    assert replay_label["numbers"]["combined_replay_or_label_status_count"] == 2


def test_candidate_survival_table_keeps_no_promotion_statuses() -> None:
    rows = synth.candidate_survival_table(
        registry=_registry(),
        checkpoint=_checkpoint(),
        depth_batch={"summary": {"exact_cached_mbp10_matches": 2}},
        sampling_audit={"updated_batch_interpretation": {"exact_clean_families": ["YM", "NQ"]}},
    )

    by_id = {row["candidate_id"]: row for row in rows}

    assert by_id["CAND-001-J46-J49-LIVE-BASELINE"]["result_status"] == "COMPARATOR_ONLY_NO_NEW_BROKER_R"
    assert by_id["CAND-002-V2-OB-BOUNDARY"]["dsr_status"] == "not_computable"
    assert by_id["CAND-005-NAS100-DEPTH-THINNESS"]["result_status"] == "DEPTH_PARITY_SOURCE_STATUS_ONLY_LABEL_LIMITED"


def test_expansion_scorecard_uses_label_audit_for_unopened_family() -> None:
    rows = synth.instrument_source_scorecard(matrix=_matrix(), label_audit=_label_audit())
    by_family = {row["family"]: row for row in rows}

    assert by_family["NAS100/NDX100 with NQ/MNQ"]["scorecard_status"] == "PROMISING_DIAGNOSTIC"
    assert by_family["EURUSD with EURUSD/6E"]["scorecard_status"] == "BLOCKED_NO_REGISTERED_COHORT"


def test_opened_ledger_preserves_zero_action_counts() -> None:
    rows = synth.opened_burned_reserved_ledger(
        checkpoint=_checkpoint(),
        label_audit=_label_audit(),
        batch_registry={"registered_batches": []},
    )

    by_id = {row["slice_id"]: row for row in rows}

    assert by_id["sierra_nq_to_nas100_pilot_20260504"]["actions_taken"] == 0


def test_payload_and_markdown_preserve_no_promotion(tmp_path) -> None:
    payload = synth.build_payload(
        matrix=_matrix(),
        label_audit=_label_audit(),
        conversion_status={
            "m15_inventory": [
                {
                    "file_symbol": "EURUSD_SCID",
                    "source_symbol": "EURUSD",
                    "evidence_class": "SAME_MARKET_SOURCE_TRANSFER",
                    "rows": 10,
                    "first": "2026-04-15 00:00:00",
                    "last": "2026-04-15 02:15:00",
                    "gap_count": 0,
                }
            ]
        },
        checkpoint=_checkpoint(),
        batch_registry={"registered_batches": []},
        candidate_registry=_registry(),
        depth_batch={"summary": {"exact_cached_mbp10_matches": 2}},
        sampling_audit={"audits": [], "updated_batch_interpretation": {}},
    )
    path = tmp_path / "synthesis.md"

    synth.write_markdown(path, payload)

    text = path.read_text(encoding="utf-8")
    assert payload["promotion_verdict"] == "NO_PROMOTION_VERDICT"
    assert payload["promotion_readiness"]["status"] == "NOT_READY"
    assert "Candidate Survival" in text
    assert "NO_PROMOTION_VERDICT" in text
