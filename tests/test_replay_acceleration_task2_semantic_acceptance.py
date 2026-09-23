from __future__ import annotations

import copy
import hashlib
import json
from pathlib import Path

import pytest


def test_semantic_equivalence_report_cannot_authorize_continuation() -> None:
    from src.research_infra.replay_acceleration_task2_semantic_acceptance import (
        SEMANTIC_REPORT_ACCEPTANCE_AUTHORIZED,
    )

    assert SEMANTIC_REPORT_ACCEPTANCE_AUTHORIZED is False


def _accepted_summary_pair() -> tuple[dict[str, object], dict[str, object]]:
    from src.research_infra.replay_acceleration_task2_semantic_acceptance import (
        ACCELERATED_JAN1_7_ROOT,
        LEGACY_ROOT,
        PREFIX,
    )

    name = f"{PREFIX}_PARTIAL_SUMMARY.json"
    legacy = json.loads((LEGACY_ROOT / name).read_text(encoding="utf-8"))
    accelerated = json.loads(
        (ACCELERATED_JAN1_7_ROOT / name).read_text(encoding="utf-8")
    )
    return legacy, accelerated


def test_summary_authority_rejects_nested_execution_option_change() -> None:
    from src.research_infra.replay_acceleration_task2_semantic_acceptance import (
        SemanticAcceptanceError,
        compare_summary_semantics,
    )

    legacy, accelerated = _accepted_summary_pair()
    accelerated["shared_execution_contract"]["execution_options"]["chunk_size"] = 2

    with pytest.raises(
        SemanticAcceptanceError,
        match="summary_authority_semantic_mismatch",
    ):
        compare_summary_semantics(legacy, accelerated)


def test_summary_authority_rejects_unknown_nested_field() -> None:
    from src.research_infra.replay_acceleration_task2_semantic_acceptance import (
        SemanticAcceptanceError,
        compare_summary_semantics,
    )

    legacy, accelerated = _accepted_summary_pair()
    accelerated["shared_execution_contract"]["unknown_nested_authority"] = {
        "enabled": False
    }

    with pytest.raises(
        SemanticAcceptanceError,
        match="summary_shared_contract_schema_invalid",
    ):
        compare_summary_semantics(legacy, accelerated)


def test_selected_preimage_partition_requires_every_selected_identity() -> None:
    from src.research_infra.replay_acceleration_task2_semantic_acceptance import (
        SemanticAcceptanceError,
        _require_exact_selected_preimage_identities,
    )

    _require_exact_selected_preimage_identities(
        {"candidate-a", "candidate-b"},
        {"candidate-a", "candidate-b"},
    )
    with pytest.raises(
        SemanticAcceptanceError,
        match="semantic_order_preimage_identity_partition_invalid",
    ):
        _require_exact_selected_preimage_identities(
            {"candidate-a"},
            {"candidate-a", "candidate-b"},
        )


def test_historical_side_may_lack_selected_preimages_but_accelerated_may_not(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    from src.research_infra import (
        replay_acceleration_task2_semantic_acceptance as acceptance,
    )

    missing = Path(str(tmp_path)) / "missing-order-preimages.jsonl"
    monkeypatch.setattr(
        acceptance,
        "_semantic_paths",
        lambda _root: {"order_preimage": missing},
    )
    historical = acceptance._validate_selected_order_preimages(
        Path(str(tmp_path)),
        end_day="2026-01-02",
        exact_scope=False,
        required=False,
        required_candidate_keys={"candidate-a"},
    )
    assert historical["status"] == "HISTORICAL_PREIMAGE_UNAVAILABLE"
    assert historical["historical_selected_identity_count"] == 1

    with pytest.raises(
        acceptance.SemanticAcceptanceError,
        match="semantic_order_preimage_missing",
    ):
        acceptance._validate_selected_order_preimages(
            Path(str(tmp_path)),
            end_day="2026-01-02",
            exact_scope=True,
            required=True,
            required_candidate_keys={"candidate-a"},
        )


def test_existing_semantic_manifest_authenticates_complete_inventory() -> None:
    from src.research_infra.replay_acceleration_task2_semantic_acceptance import (
        ACCELERATED_JAN1_7_ROOT,
        validate_semantic_source_manifest,
    )

    receipt = validate_semantic_source_manifest(ACCELERATED_JAN1_7_ROOT)
    assert receipt["authenticated_file_roles"] == [
        "candidate",
        "oracle",
        "order",
        "order_preimage",
        "state_checkpoint",
        "trade",
    ]


def _root(value: object) -> str:
    return hashlib.sha256(
        json.dumps(
            value,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=True,
            allow_nan=False,
        ).encode("utf-8")
    ).hexdigest()


def _risk_row(*, captured_at_utc: str) -> dict[str, object]:
    snapshot: dict[str, object] = {
        "schema_version": "prop_firm_headroom_snapshot_v4",
        "captured_at_utc": captured_at_utc,
        "current_equity": 100_000.0,
        "max_allowed_new_trade_risk_pct": 4.0,
    }
    snapshot["snapshot_hash_sha256"] = _root(snapshot)
    risk_authority: dict[str, object] = {
        "schema_version": "timewarp_v4_runtime_risk_authority_v1",
        "prop_firm_headroom": {
            "simulated_headroom": copy.deepcopy(snapshot),
            "prop_firm_headroom_v4_evaluation": {
                "schema_version": "prop_firm_headroom_evaluation_v4",
                "component": "prop_firm_headroom_v4",
                "captured_at_utc": captured_at_utc,
                "snapshot": copy.deepcopy(snapshot),
            },
        },
        "final_approved_risk_pct": 0.1,
        "risk_cash": 100.0,
        "packet_hash_sha256": "",
    }
    risk_authority["packet_hash_sha256"] = _root(risk_authority)
    return {
        "row_type": "simulated_trade",
        "row_provenance_schema": "broad_live_as_if_replay_row_provenance_v1",
        "trading_day": "2026-01-02",
        "campaign": "campaign",
        "profile": "repaired_package_conversion_v3",
        "decision_window_id": "timewarp:2026-01-02T08:00:00+00:00",
        "canonical_replay_candidate_instance_key": "candidate@@2026-01-02T08:00:00+00:00",
        "candidate_id": "candidate",
        "decision_time_utc": "2026-01-02T08:00:00+00:00",
        "simulated_order_id": "order-1",
        "simulated_trade_id": "trade-1",
        "entry_price": 1.25,
        "risk_authority": risk_authority,
        "risk_authority_packet_hash_sha256": risk_authority[
            "packet_hash_sha256"
        ],
    }


def test_semantic_projection_accepts_only_validated_runtime_clock_closure() -> None:
    from src.research_infra.replay_acceleration_task2_semantic_acceptance import (
        compare_role_rows,
    )

    legacy = _risk_row(captured_at_utc="2026-07-17T18:06:56+00:00")
    accelerated = _risk_row(captured_at_utc="2026-01-02T08:00:00+00:00")

    receipt = compare_role_rows("trade", [legacy], [accelerated])

    assert receipt["status"] == "SEMANTICALLY_EQUIVALENT"
    assert receipt["row_count"] == 1
    assert receipt["meaningful_difference_count"] == 0
    assert receipt["excluded_volatile_difference_count"] == 7
    assert set(receipt["observed_allowlisted_paths"]) == {
        "risk_authority/packet_hash_sha256",
        "risk_authority/prop_firm_headroom/prop_firm_headroom_v4_evaluation/captured_at_utc",
        "risk_authority/prop_firm_headroom/prop_firm_headroom_v4_evaluation/snapshot/captured_at_utc",
        "risk_authority/prop_firm_headroom/prop_firm_headroom_v4_evaluation/snapshot/snapshot_hash_sha256",
        "risk_authority/prop_firm_headroom/simulated_headroom/captured_at_utc",
        "risk_authority/prop_firm_headroom/simulated_headroom/snapshot_hash_sha256",
        "risk_authority_packet_hash_sha256",
    }
    assert receipt["economic_values_exposed"] is False


def test_semantic_projection_rejects_unproven_hash_only_difference() -> None:
    from src.research_infra.replay_acceleration_task2_semantic_acceptance import (
        SemanticAcceptanceError,
        compare_role_rows,
    )

    reference = {
        "trading_day": "2026-01-02",
        "candidate_id": "candidate",
        "decision_time_utc": "2026-01-02T08:00:00+00:00",
        "canonical_replay_candidate_instance_key": (
            "candidate@@2026-01-02T08:00:00+00:00"
        ),
        "packet_sidecar_hash_sha256": "1" * 64,
    }
    accelerated = {**reference, "packet_sidecar_hash_sha256": "2" * 64}

    with pytest.raises(
        SemanticAcceptanceError,
        match="derived_hash_closure_unproven",
    ):
        compare_role_rows("missed", [reference], [accelerated])


@pytest.mark.parametrize(
    ("path", "value"),
    [
        (("entry_price",), 1.26),
        (("decision_time_utc",), "2026-01-02T08:15:00+00:00"),
        (("candidate_id",), "different-candidate"),
        (("risk_authority", "risk_cash"), 101.0),
    ],
)
def test_semantic_projection_rejects_meaningful_differences(
    path: tuple[str, ...],
    value: object,
) -> None:
    from src.research_infra.replay_acceleration_task2_semantic_acceptance import (
        SemanticAcceptanceError,
        compare_role_rows,
    )

    legacy = _risk_row(captured_at_utc="2026-07-17T18:06:56+00:00")
    accelerated = copy.deepcopy(legacy)
    target = accelerated
    for key in path[:-1]:
        target = target[key]  # type: ignore[index,assignment]
    target[path[-1]] = value

    with pytest.raises(
        SemanticAcceptanceError,
        match="semantic_row_mismatch|risk_packet_hash_invalid",
    ):
        compare_role_rows("trade", [legacy], [accelerated])


def test_semantic_projection_rejects_equal_forged_snapshot_hash() -> None:
    from src.research_infra.replay_acceleration_task2_semantic_acceptance import (
        SemanticAcceptanceError,
        compare_role_rows,
    )

    legacy = _risk_row(captured_at_utc="2026-07-17T18:06:56+00:00")
    accelerated = copy.deepcopy(legacy)
    for row in (legacy, accelerated):
        row["risk_authority"]["prop_firm_headroom"]["simulated_headroom"][  # type: ignore[index]
            "snapshot_hash_sha256"
        ] = "0" * 64

    with pytest.raises(SemanticAcceptanceError, match="snapshot_hash_invalid"):
        compare_role_rows("trade", [legacy], [accelerated])


def test_semantic_projection_rejects_cardinality_and_order_drift() -> None:
    from src.research_infra.replay_acceleration_task2_semantic_acceptance import (
        SemanticAcceptanceError,
        compare_role_rows,
    )

    first = _risk_row(captured_at_utc="2026-01-02T08:00:00+00:00")
    second = copy.deepcopy(first)
    second["candidate_id"] = "candidate-2"
    second["canonical_replay_candidate_instance_key"] = (
        "candidate-2@@2026-01-02T08:00:00+00:00"
    )

    with pytest.raises(SemanticAcceptanceError, match="semantic_row_count_mismatch"):
        compare_role_rows("trade", [first], [first, second])
    with pytest.raises(SemanticAcceptanceError, match="semantic_row_mismatch"):
        compare_role_rows("trade", [first, second], [second, first])


def test_exact_role_never_normalizes_even_hash_like_fields() -> None:
    from src.research_infra.replay_acceleration_task2_semantic_acceptance import (
        SemanticAcceptanceError,
        compare_role_rows,
    )

    reference = [{"row_type": "asof_decision", "price": 1.0, "hash": "a" * 64}]
    accelerated = copy.deepcopy(reference)
    accelerated[0]["hash"] = "b" * 64

    with pytest.raises(SemanticAcceptanceError, match="semantic_row_mismatch"):
        compare_role_rows("decision", reference, accelerated)


def test_summary_projection_binds_semantic_state_and_slices_progress() -> None:
    from src.research_infra.replay_acceleration_task2_semantic_acceptance import (
        compare_summary_semantics,
    )

    progress = [
        {"start_day": "2026-01-01", "end_day": "2026-01-01", "orders": 0},
        {"start_day": "2026-01-02", "end_day": "2026-01-02", "orders": 5},
        {"start_day": "2026-01-03", "end_day": "2026-01-03", "orders": 2},
    ]
    reference = {
        "b7_5_selection_sizing_factorial_arm_binding": {
            "arm_id": "S0R0",
            "arm_fingerprint_sha256": (
                "2ece240b5fc9434a7ec20919e95cdf549bcd46f1c0311f130458fd4804c6d447"
            ),
            "broker_mutation_enabled": False,
            "live_broker_authority": False,
            "uses_outcome_fields": False,
            "valid": True,
        },
        "candidate_relational_materialization": {"valid": True, "rows": 10},
        "compact_projection_counts_so_far": {"decision": 10},
        "ledger_write_row_counts_so_far": {"order": 5},
        "progress_rows": progress,
        "source_authority_chunk_invariance_contract": {"valid": True},
        "source_authority_preflight_checkpoints": [{"valid": True}],
        "ultimate_package_runtime_input_contract": {"valid": True},
        "generated_at_utc": "volatile",
    }
    accelerated = copy.deepcopy(reference)
    accelerated["progress_rows"] = progress[:2]
    accelerated["generated_at_utc"] = "different"

    receipt = compare_summary_semantics(
        reference,
        accelerated,
        end_day="2026-01-02",
    )

    assert receipt["status"] == "SEMANTICALLY_EQUIVALENT"
    assert receipt["progress_row_count"] == 2


def test_summary_projection_rejects_every_unknown_field() -> None:
    from src.research_infra.replay_acceleration_task2_semantic_acceptance import (
        SemanticAcceptanceError,
        compare_summary_semantics,
    )

    reference = {
        "schema": "summary-v1",
        "status": "partial",
        "progress_rows": [],
        "unexpected_authority": {"enabled": False},
    }
    accelerated = copy.deepcopy(reference)

    with pytest.raises(SemanticAcceptanceError, match="summary_field_unknown"):
        compare_summary_semantics(reference, accelerated)


def test_semantic_row_day_accepts_only_single_day_chunk_aggregate() -> None:
    from src.research_infra.replay_acceleration_task2_semantic_acceptance import (
        SemanticAcceptanceError,
        _row_day,
    )

    assert _row_day(
        {
            "row_type": "bucket",
            "chunk_start_day": "2026-01-02",
            "chunk_end_day": "2026-01-02",
        }
    ) == "2026-01-02"
    with pytest.raises(SemanticAcceptanceError, match="semantic_row_day_invalid"):
        _row_day(
            {
                "row_type": "bucket",
                "chunk_start_day": "2026-01-01",
                "chunk_end_day": "2026-01-02",
            }
        )


def test_exact_scope_rows_rejects_unconsumed_future_rows() -> None:
    from src.research_infra.replay_acceleration_task2_semantic_acceptance import (
        SemanticAcceptanceError,
        exact_scope_rows,
    )

    rows = [
        {"trading_day": "2026-01-01", "candidate_id": "a"},
        {"trading_day": "2026-01-02", "candidate_id": "b"},
        {"trading_day": "2026-01-03", "candidate_id": "c"},
    ]

    with pytest.raises(
        SemanticAcceptanceError,
        match="semantic_row_outside_exact_scope:missed:2:2026-01-03",
    ):
        list(
            exact_scope_rows(
                rows,
                role="missed",
                start_day="2026-01-01",
                end_day="2026-01-02",
            )
        )


def test_state_checkpoint_requires_recomputed_complete_account_preimage() -> None:
    from src.research_infra.replay_acceleration_task2_semantic_acceptance import (
        SemanticAcceptanceError,
        canonical_sha256,
        compare_state_checkpoint_semantics,
    )

    account_field_names = (
        "balance",
        "equity",
        "peak_equity",
        "max_drawdown_pct",
        "daily_start_balance",
        "accepted_risk_orders_by_day",
        "accepted_risk_pct_by_day",
        "accepted_risk_orders_by_day_session",
        "accepted_risk_pct_by_day_session",
        "accepted_risk_orders_by_day_decision_time",
        "accepted_risk_pct_by_day_decision_time",
        "accepted_risk_orders_by_day_decision_cluster_side",
        "accepted_risk_pct_by_day_decision_cluster_side",
        "pending_orders",
        "open_positions",
        "closed_trades",
        "event_queue",
        "event_sequence",
    )

    def account_payload(
        closed_trades: list[dict[str, object]] | None = None,
    ) -> dict[str, object]:
        payload: dict[str, object] = {
            "balance": 100_000.0,
            "equity": 100_000.0,
            "peak_equity": 100_000.0,
            "max_drawdown_pct": 0.0,
            "daily_start_balance": {},
            "accepted_risk_orders_by_day": {},
            "accepted_risk_pct_by_day": {},
            "accepted_risk_orders_by_day_session": {},
            "accepted_risk_pct_by_day_session": {},
            "accepted_risk_orders_by_day_decision_time": {},
            "accepted_risk_pct_by_day_decision_time": {},
            "accepted_risk_orders_by_day_decision_cluster_side": {},
            "accepted_risk_pct_by_day_decision_cluster_side": {},
            "pending_orders": {},
            "open_positions": {},
            "closed_trades": list(closed_trades or []),
            "event_queue": [],
            "event_sequence": 0,
        }
        assert tuple(payload) == account_field_names
        return payload

    def checkpoint(
        day: str,
        boundary: str,
        account: dict[str, object],
        *,
        include_preimage: bool,
    ) -> dict[str, object]:
        reservation = {
            key: account[key]
            for key in (
                "accepted_risk_orders_by_day",
                "accepted_risk_pct_by_day",
                "accepted_risk_orders_by_day_session",
                "accepted_risk_pct_by_day_session",
                "accepted_risk_orders_by_day_decision_time",
                "accepted_risk_pct_by_day_decision_time",
                "accepted_risk_orders_by_day_decision_cluster_side",
                "accepted_risk_pct_by_day_decision_cluster_side",
                "pending_orders",
                "open_positions",
            )
        }
        projection = {
            "schema": "gtos.replay_acceleration.pre_day_state.v1",
            "account_root_sha256": canonical_sha256(account),
            "broker_root_sha256": "b" * 64,
            "event_queue_root_sha256": canonical_sha256(account["event_queue"]),
            "reservation_root_sha256": canonical_sha256(reservation),
            "selected_order_sequence": 5 if day == "2026-01-02" else 0,
        }
        result = {
            "schema": "gtos.replay_acceleration.semantic_state_checkpoint.v1",
            "campaign": "campaign",
            "profile": "profile",
            "trading_day": day,
            "boundary": boundary,
            "state_projection": projection,
            "state_root_sha256": canonical_sha256(projection),
        }
        if include_preimage:
            result["account_preimage"] = copy.deepcopy(account)
        return result

    empty = account_payload()
    jan1 = checkpoint(
        "2026-01-01", "pre_day", empty, include_preimage=False
    )
    jan1_post = checkpoint(
        "2026-01-01", "post_day", empty, include_preimage=False
    )
    jan2_pre = copy.deepcopy(jan1_post)
    jan2_pre["trading_day"] = "2026-01-02"
    jan2_pre["boundary"] = "pre_day"
    reference_closed_trade = {
        "simulated_trade_id": "trade-1",
        "packet_sidecar_hash_sha256": "2" * 64,
        "pnl_cash": 1.0,
    }
    accelerated_closed_trade = {
        **reference_closed_trade,
        "packet_sidecar_hash_sha256": "3" * 64,
    }
    reference = [
        jan1,
        jan1_post,
        jan2_pre,
        checkpoint(
            "2026-01-02",
            "post_day",
            account_payload([reference_closed_trade]),
            include_preimage=False,
        ),
    ]
    accelerated_jan1_post = checkpoint(
        "2026-01-01", "post_day", empty, include_preimage=True
    )
    accelerated_jan2_pre = copy.deepcopy(accelerated_jan1_post)
    accelerated_jan2_pre["trading_day"] = "2026-01-02"
    accelerated_jan2_pre["boundary"] = "pre_day"
    accelerated = [
        checkpoint(
            "2026-01-01", "pre_day", empty, include_preimage=True
        ),
        accelerated_jan1_post,
        accelerated_jan2_pre,
        checkpoint(
            "2026-01-02",
            "post_day",
            account_payload([accelerated_closed_trade]),
            include_preimage=True,
        ),
    ]
    progress = [
        {"start_day": "2026-01-01", "end_day": "2026-01-01", "cash": 0.0},
        {"start_day": "2026-01-02", "end_day": "2026-01-02", "cash": 1.0},
    ]
    reference_trade = [copy.deepcopy(reference_closed_trade)]
    accelerated_trade = [copy.deepcopy(accelerated_closed_trade)]

    receipt = compare_state_checkpoint_semantics(
        reference,
        accelerated,
        reference_progress_rows=progress,
        accelerated_progress_rows=copy.deepcopy(progress),
        reference_order_rows=[],
        accelerated_order_rows=[],
        reference_trade_rows=reference_trade,
        accelerated_trade_rows=accelerated_trade,
        derived_hash_proofs={
            "packet_sidecar_hash_sha256": "HISTORICAL_HASH_ONLY_NONCAUSAL"
        },
    )
    assert receipt["status"] == "SEMANTIC_ACCOUNT_STATE_EQUIVALENT"
    assert receipt["excluded_derived_hash_difference_count"] == 2
    assert receipt["account_state_field_count"] == len(account_field_names)

    accelerated[-1]["state_projection"]["account_root_sha256"] = "0" * 64
    accelerated[-1]["state_root_sha256"] = canonical_sha256(
        accelerated[-1]["state_projection"]
    )
    with pytest.raises(
        SemanticAcceptanceError,
        match="account_preimage_accelerated_root_mismatch",
    ):
        compare_state_checkpoint_semantics(
            reference,
            accelerated,
            reference_progress_rows=progress,
            accelerated_progress_rows=progress,
            reference_order_rows=[],
            accelerated_order_rows=[],
            reference_trade_rows=reference_trade,
            accelerated_trade_rows=accelerated_trade,
            derived_hash_proofs={
                "packet_sidecar_hash_sha256": "HISTORICAL_HASH_ONLY_NONCAUSAL"
            },
        )
