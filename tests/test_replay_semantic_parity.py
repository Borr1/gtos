from __future__ import annotations

import copy
import hashlib
import inspect
import json
from pathlib import Path

import pytest


class _OneShotRows:
    def __init__(self, rows: list[dict[str, object]]) -> None:
        self._rows = rows
        self.iteration_count = 0

    def __len__(self) -> int:
        return len(self._rows)

    def __iter__(self):
        self.iteration_count += 1
        if self.iteration_count == 1:
            return iter(self._rows)
        return iter(())


class _ForbiddenRows:
    def __init__(self) -> None:
        self.iteration_count = 0

    def __iter__(self):
        self.iteration_count += 1
        raise AssertionError("semantic role stream opened before proof validation")


def _canonical_sha256(value: object) -> str:
    raw = json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
        allow_nan=False,
    ).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


def _default_execution_sidecar_id() -> str:
    return _canonical_sha256(
        {
            "campaign": "campaign-1",
            "candidate_id": "candidate-1",
            "simulated_order_id": "simulated-order-1",
            "type": "execution_manager_v4",
        }
    )


def _packet_hash(value: dict[str, object]) -> str:
    return _canonical_sha256(
        {
            key: item
            for key, item in value.items()
            if key not in {"generated_at_utc", "packet_hash_sha256"}
        }
    )


def _order_fixture(
    *,
    generated_at_utc: str,
) -> tuple[dict[str, object], dict[str, dict[str, object]]]:
    nested_lifecycle_packet: dict[str, object] = {
        "schema_version": "broker_order_lifecycle_capture_v4_packet_v1",
        "component": "broker_order_lifecycle_capture_v4",
        "generated_at_utc": generated_at_utc,
        "stage": "pre_order_contract",
        "status": "pre_order_capture_contract_ready",
    }
    nested_lifecycle_packet["packet_hash_sha256"] = _packet_hash(
        nested_lifecycle_packet
    )
    execution_manager_packet: dict[str, object] = {
        "schema_version": "execution_manager_v4_packet_v1",
        "component": "execution_manager_v4",
        "generated_at_utc": generated_at_utc,
        "action": "observe_only",
        "identity": {
            "candidate_id": "candidate-1",
            "symbol": "EURUSD",
        },
        "entry_timing": {
            "decision_time_utc": "2026-01-02T08:00:00+00:00",
        },
        "broker_order_lifecycle_capture_v4": nested_lifecycle_packet,
    }
    nested_execution_hash = _packet_hash(execution_manager_packet)
    lifecycle_packet = {
        "schema_version": "broker_order_lifecycle_capture_v4_packet_v1",
        "component": "broker_order_lifecycle_capture_v4",
        "generated_at_utc": generated_at_utc,
        "stage": "pre_order_contract",
        "status": "pre_order_capture_contract_ready",
        "identity": {
            "candidate_id": "candidate-1",
            "decision_time_utc": "2026-01-02T08:00:00+00:00",
        },
        "pre_order_capture_contract": {
            "execution_manager_packet_hash": nested_execution_hash,
        },
    }
    lifecycle_packet["packet_hash_sha256"] = _canonical_sha256(
        {
            key: value
            for key, value in lifecycle_packet.items()
            if key != "generated_at_utc"
        }
    )
    sidecar_id = _default_execution_sidecar_id()
    row = {
        "row_type": "simulated_order",
        "row_provenance_schema": "broad_live_as_if_replay_row_provenance_v1",
        "campaign": "campaign-1",
        "profile": "S0R0",
        "broad_replay_profile": "S0R0",
        "decision_window_id": "window-1",
        "canonical_replay_candidate_instance_key": "candidate-instance-1",
        "candidate_id": "candidate-1",
        "simulated_order_id": "simulated-order-1",
        "decision_time_utc": "2026-01-02T08:00:00+00:00",
        "decision_time": "2026-01-02T08:00:00+00:00",
        "selected_order_attempt_primary": True,
        "selected_order_sequence": 1,
        "order_status": "simulated_pending",
        "broker_order_lifecycle_capture_v4_packet": lifecycle_packet,
        "execution_manager_packet_hash_sha256": "b" * 64,
        "execution_packet_sidecar_hash_sha256": "d" * 64,
        "execution_packet_sidecar_id": sidecar_id,
    }
    preimages = {
        sidecar_id: {
            "execution_manager_packet": execution_manager_packet,
            "broker_order_lifecycle_capture_v4_packet": lifecycle_packet,
        }
    }
    row["execution_manager_packet_hash_sha256"] = _canonical_sha256(
        execution_manager_packet
    )
    row["execution_packet_sidecar_hash_sha256"] = _canonical_sha256(
        preimages[sidecar_id]
    )
    return row, preimages


def _order_row(*, generated_at_utc: str) -> dict[str, object]:
    return _order_fixture(generated_at_utc=generated_at_utc)[0]


def test_order_projection_normalizes_only_allowlisted_runtime_envelope_and_hash() -> None:
    from src.research_infra.replay_semantic_parity import project_role_rows

    reference, reference_preimages = _order_fixture(
        generated_at_utc="2026-01-02T08:00:01+00:00"
    )
    accelerated, accelerated_preimages = _order_fixture(
        generated_at_utc="2026-01-02T08:00:02+00:00"
    )

    reference_projection = project_role_rows(
        "order", [reference], provenance_preimages=reference_preimages
    )
    accelerated_projection = project_role_rows(
        "order", [accelerated], provenance_preimages=accelerated_preimages
    )

    assert reference_projection == accelerated_projection
    assert reference_projection["row_count"] == 1
    assert reference_projection["normalized_paths"] == [
        [
            "0",
            "broker_order_lifecycle_capture_v4_packet",
            "generated_at_utc",
        ],
        [
            "0",
            "broker_order_lifecycle_capture_v4_packet",
            "pre_order_capture_contract",
            "execution_manager_packet_hash",
        ],
        [
            "0",
            "broker_order_lifecycle_capture_v4_packet",
            "packet_hash_sha256",
        ],
        ["0", "execution_manager_packet_hash_sha256"],
        ["0", "execution_packet_sidecar_hash_sha256"],
    ]
    assert reference_projection["economic_values_exposed"] is False


def test_order_projection_keeps_causal_time_exact() -> None:
    from src.research_infra.replay_semantic_parity import project_role_rows

    reference = _order_row(generated_at_utc="2026-01-02T08:00:01+00:00")
    accelerated = copy.deepcopy(reference)
    accelerated["decision_time_utc"] = "2026-01-02T08:15:00+00:00"

    assert project_role_rows("order", [reference]) != project_role_rows(
        "order", [accelerated]
    )


def _role_row(role: str, candidate_key: str) -> dict[str, object]:
    row_types = {
        "scorecard": "scheduler_scorecard",
        "trade": "simulated_trade",
        "oracle": "ordered_path_oracle",
        "missed": "missed_opportunity",
    }
    row: dict[str, object] = {
        "row_type": row_types[role],
        "row_provenance_schema": "broad_live_as_if_replay_row_provenance_v1",
        "campaign": "campaign-1",
        "profile": "S0R0",
        "broad_replay_profile": "S0R0",
        "decision_window_id": (
            "window-2" if candidate_key.endswith("-2") else "window-1"
        ),
        "canonical_replay_candidate_instance_key": candidate_key,
        "candidate_id": candidate_key.replace("-instance", ""),
        "decision_time_utc": "2026-01-02T08:00:00+00:00",
        "decision_time": "2026-01-02T08:00:00+00:00",
        "selector_action": "selected" if role != "missed" else "not_selected",
        "source_sha256": "c" * 64,
    }
    if role == "scorecard":
        trace = [{"option": row["candidate_id"]}]
        row["compact_scorecard_projection_schema"] = (
            "gtos.final_moonshot.broad_replay.compact_scorecard_projection.v1"
        )
        row["scheduler_option_trace"] = trace
        row["scheduler_option_trace_projection_status"] = (
            "canonical_trace_preserved_no_aliases_present"
        )
        row["scheduler_option_trace_omitted_duplicate_aliases"] = []
        row["scheduler_option_trace_projection_sha256"] = _canonical_sha256(trace)
    if role == "missed":
        row["missed_opportunity_compact_schema"] = (
            "compact_broad_replay_missed_opportunity_v1"
        )
    if role in {"trade", "oracle"}:
        row["simulated_order_id"] = "simulated-order-1"
    return row


def _semantic_ledgers(*, generated_at_utc: str) -> dict[str, list[dict[str, object]]]:
    selected_key = "candidate-instance-1"
    missed_key = "candidate-instance-2"
    order = _order_row(generated_at_utc=generated_at_utc)
    order["source_sha256"] = "c" * 64
    return {
        "scorecard": [
            _role_row("scorecard", selected_key),
            _role_row("scorecard", missed_key),
        ],
        "order": [order],
        "trade": [_role_row("trade", selected_key)],
        "oracle": [_role_row("oracle", selected_key)],
        "missed": [_role_row("missed", missed_key)],
    }


def _self_rooted_proof_row(**values: object) -> dict[str, object]:
    row = {
        "schema": "gtos.replay_acceleration.semantic_proof_row.v1",
        **values,
    }
    row["proof_root_sha256"] = _canonical_sha256(row)
    return row


def _reroot_proof_row(row: dict[str, object]) -> None:
    row.pop("proof_root_sha256", None)
    row["proof_root_sha256"] = _canonical_sha256(row)


def _strict_stream_fixture(
    *,
    generated_at_utc: str = "2026-01-02T08:00:01+00:00",
) -> tuple[
    dict[str, list[dict[str, object]]],
    list[dict[str, object]],
]:
    ledgers = _semantic_ledgers(generated_at_utc=generated_at_utc)
    preimage = _order_fixture(generated_at_utc=generated_at_utc)[1][
        _default_execution_sidecar_id()
    ]
    sidecar_payload = json.dumps(
        preimage,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
        allow_nan=False,
    )
    sidecar_hash = hashlib.sha256(sidecar_payload.encode("ascii")).hexdigest()
    ledgers["order"][0]["execution_packet_sidecar_hash_sha256"] = sidecar_hash

    pre_day_state = {
        "schema": "gtos.replay_acceleration.pre_day_state.v1",
        "account_root_sha256": "1" * 64,
        "broker_root_sha256": "2" * 64,
        "event_queue_root_sha256": "3" * 64,
        "reservation_root_sha256": "4" * 64,
        "selected_order_sequence": 0,
    }
    post_day_state = {
        **pre_day_state,
        "account_root_sha256": "5" * 64,
        "broker_root_sha256": "6" * 64,
        "selected_order_sequence": 1,
    }
    partitions = {
        "candidate": {
            "row_count": len(ledgers["scorecard"]),
            "ordered_rows_root_sha256": _canonical_sha256(ledgers["scorecard"]),
        },
        "missed": {
            "row_count": len(ledgers["missed"]),
            "ordered_rows_root_sha256": _canonical_sha256(ledgers["missed"]),
        },
        "order": {
            "row_count": len(ledgers["order"]),
            "ordered_rows_root_sha256": _canonical_sha256(ledgers["order"]),
        },
        "trade": {
            "row_count": len(ledgers["trade"]),
            "ordered_rows_root_sha256": _canonical_sha256(ledgers["trade"]),
        },
    }
    proof_rows = [
        _self_rooted_proof_row(
            proof_sequence=0,
            proof_type="state_checkpoint",
            trading_day="2026-01-02",
            boundary="pre_day",
            state_projection=pre_day_state,
            state_root_sha256=_canonical_sha256(pre_day_state),
        ),
        _self_rooted_proof_row(
            proof_sequence=1,
            proof_type="state_checkpoint",
            trading_day="2026-01-02",
            boundary="post_day",
            state_projection=post_day_state,
            state_root_sha256=_canonical_sha256(post_day_state),
        ),
        _self_rooted_proof_row(
            proof_sequence=2,
            proof_type="terminal_partition",
            trading_day="2026-01-02",
            partitions=partitions,
        ),
        _self_rooted_proof_row(
            proof_sequence=3,
            proof_type="order_sidecar_preimage",
            trading_day="2026-01-02",
            execution_packet_sidecar_id=_default_execution_sidecar_id(),
            sidecar_payload_canonical_json=sidecar_payload,
            sidecar_payload_sha256=sidecar_hash,
            owner={
                "campaign": "campaign-1",
                "profile": "S0R0",
                "decision_window_id": "window-1",
                "candidate_id": "candidate-1",
                "canonical_replay_candidate_instance_key": (
                    "candidate-instance-1"
                ),
                "decision_time_utc": "2026-01-02T08:00:00+00:00",
                "simulated_order_id": "simulated-order-1",
                "payload_root_sha256": sidecar_hash,
            },
        ),
    ]
    return ledgers, proof_rows


def test_compare_semantic_ledgers_accepts_only_paired_envelope_differences() -> None:
    from src.research_infra.replay_semantic_parity import compare_semantic_ledgers

    reference = _semantic_ledgers(generated_at_utc="2026-01-02T08:00:01+00:00")
    accelerated = _semantic_ledgers(generated_at_utc="2026-01-02T08:00:02+00:00")
    reference_preimages = _order_fixture(
        generated_at_utc="2026-01-02T08:00:01+00:00"
    )[1]
    accelerated_preimages = _order_fixture(
        generated_at_utc="2026-01-02T08:00:02+00:00"
    )[1]

    receipt = compare_semantic_ledgers(
        reference,
        accelerated,
        reference_provenance_preimages=reference_preimages,
        accelerated_provenance_preimages=accelerated_preimages,
    )

    assert receipt["parity_status"] == "INCOMPLETE_DIAGNOSTIC_ONLY"
    assert receipt["acceptance_authorized"] is False
    assert receipt["diagnostic_complete"] is False
    assert receipt["economic_values_exposed"] is False
    assert [item["role"] for item in receipt["roles"]] == [
        "scorecard",
        "order",
        "trade",
        "oracle",
        "missed",
    ]
    assert all("rows" not in item for item in receipt["roles"])


def test_one_shot_role_stream_detects_mismatch_and_is_consumed_once() -> None:
    from src.research_infra.replay_semantic_parity import (
        SemanticParityError,
        compare_semantic_ledgers,
    )

    reference_rows = _semantic_ledgers(generated_at_utc="2026-01-02T08:00:01+00:00")
    accelerated_rows = copy.deepcopy(reference_rows)
    accelerated_rows["scorecard"][0]["selector_action"] = "blocked"
    reference = {
        role: _OneShotRows(rows) for role, rows in reference_rows.items()
    }
    accelerated = {
        role: _OneShotRows(rows) for role, rows in accelerated_rows.items()
    }

    caught: SemanticParityError | None = None
    try:
        compare_semantic_ledgers(reference, accelerated)  # type: ignore[arg-type]
    except SemanticParityError as exc:
        caught = exc

    assert caught is not None
    assert str(caught).startswith("semantic_row_mismatch:scorecard:0")
    assert all(rows.iteration_count == 1 for rows in reference.values())
    assert all(rows.iteration_count == 1 for rows in accelerated.values())


def test_rejects_forged_sidecar_hash_even_when_both_rows_match() -> None:
    from src.research_infra.replay_semantic_parity import (
        SemanticParityError,
        compare_semantic_ledgers,
    )

    reference = _semantic_ledgers(generated_at_utc="2026-01-02T08:00:01+00:00")
    accelerated = _semantic_ledgers(generated_at_utc="2026-01-02T08:00:02+00:00")
    reference_preimages = _order_fixture(
        generated_at_utc="2026-01-02T08:00:01+00:00"
    )[1]
    accelerated_preimages = _order_fixture(
        generated_at_utc="2026-01-02T08:00:02+00:00"
    )[1]
    forged_hash = "d" * 64
    assert forged_hash != _canonical_sha256(
        reference_preimages[_default_execution_sidecar_id()]
    )
    assert forged_hash != _canonical_sha256(
        accelerated_preimages[_default_execution_sidecar_id()]
    )
    reference["order"][0]["execution_packet_sidecar_hash_sha256"] = forged_hash
    accelerated["order"][0]["execution_packet_sidecar_hash_sha256"] = forged_hash

    with pytest.raises(SemanticParityError, match="semantic_sidecar_hash_mismatch"):
        compare_semantic_ledgers(
            reference,
            accelerated,
            reference_provenance_preimages=reference_preimages,
            accelerated_provenance_preimages=accelerated_preimages,
        )


def test_rejects_rehashed_truncated_execution_preimage() -> None:
    from src.research_infra.replay_semantic_parity import (
        SemanticParityError,
        compare_semantic_ledgers,
    )

    reference = _semantic_ledgers(generated_at_utc="2026-01-02T08:00:01+00:00")
    accelerated = copy.deepcopy(reference)
    reference_preimages = _order_fixture(
        generated_at_utc="2026-01-02T08:00:01+00:00"
    )[1]
    accelerated_preimages = copy.deepcopy(reference_preimages)

    for ledgers, preimages in (
        (reference, reference_preimages),
        (accelerated, accelerated_preimages),
    ):
        preimage = preimages[_default_execution_sidecar_id()]
        execution_packet = preimage["execution_manager_packet"]
        assert isinstance(execution_packet, dict)
        execution_packet.pop("action")
        broker_packet = preimage["broker_order_lifecycle_capture_v4_packet"]
        assert isinstance(broker_packet, dict)
        pre_order = broker_packet["pre_order_capture_contract"]
        assert isinstance(pre_order, dict)
        pre_order["execution_manager_packet_hash"] = _packet_hash(
            execution_packet
        )
        broker_packet["packet_hash_sha256"] = _packet_hash(broker_packet)
        ledgers["order"][0][
            "broker_order_lifecycle_capture_v4_packet"
        ] = copy.deepcopy(broker_packet)
        ledgers["order"][0][
            "execution_packet_sidecar_hash_sha256"
        ] = _canonical_sha256(preimage)

    with pytest.raises(SemanticParityError, match="semantic_preimage_incomplete"):
        compare_semantic_ledgers(
            reference,
            accelerated,
            reference_provenance_preimages=reference_preimages,
            accelerated_provenance_preimages=accelerated_preimages,
        )


def test_compare_semantic_streams_returns_non_accepting_value_free_receipt() -> None:
    from src.research_infra.replay_semantic_parity import compare_semantic_streams

    reference_rows, reference_proof_rows = _strict_stream_fixture()
    accelerated_rows = copy.deepcopy(reference_rows)
    accelerated_proof_rows = copy.deepcopy(reference_proof_rows)
    reference = {
        role: _OneShotRows(rows) for role, rows in reference_rows.items()
    }
    accelerated = {
        role: _OneShotRows(rows) for role, rows in accelerated_rows.items()
    }
    reference_proofs = _OneShotRows(reference_proof_rows)
    accelerated_proofs = _OneShotRows(accelerated_proof_rows)

    receipt = compare_semantic_streams(
        reference,
        accelerated,
        reference_proof_rows=reference_proofs,
        accelerated_proof_rows=accelerated_proofs,
    )

    assert receipt["status"] == (
        "UNBOUND_RUNTIME_ENVELOPE_SEMANTIC_DIAGNOSTIC_INCOMPLETE"
    )
    assert receipt["parity_status"] == "INCOMPLETE_DIAGNOSTIC_ONLY"
    assert receipt["acceptance_authorized"] is False
    assert receipt["diagnostic_complete"] is False
    assert receipt["campaign_calendar_bound"] is False
    assert receipt["candidate_partition_recomputed"] is False
    assert receipt["persisted_terminal_partitions_recomputed"] is True
    assert receipt["economic_values_exposed"] is False
    assert all("rows" not in role for role in receipt["roles"])
    assert all(rows.iteration_count == 1 for rows in reference.values())
    assert all(rows.iteration_count == 1 for rows in accelerated.values())
    assert reference_proofs.iteration_count == 1
    assert accelerated_proofs.iteration_count == 1


def test_compare_semantic_streams_accepts_paired_runtime_hash_closure() -> None:
    from src.research_infra.replay_semantic_parity import compare_semantic_streams

    reference, reference_proofs = _strict_stream_fixture(
        generated_at_utc="2026-01-02T08:00:01+00:00"
    )
    accelerated, accelerated_proofs = _strict_stream_fixture(
        generated_at_utc="2026-01-02T08:00:02+00:00"
    )

    receipt = compare_semantic_streams(
        reference,
        accelerated,
        reference_proof_rows=reference_proofs,
        accelerated_proof_rows=accelerated_proofs,
    )

    order_receipt = next(
        role for role in receipt["roles"] if role["role"] == "order"
    )
    assert receipt["parity_status"] == "INCOMPLETE_DIAGNOSTIC_ONLY"
    assert receipt["acceptance_authorized"] is False
    assert order_receipt["normalized_path_count"] == 5


def test_pre_day_state_mismatch_fails_before_stream_consumption() -> None:
    from src.research_infra.replay_semantic_parity import (
        SemanticParityError,
        compare_semantic_streams,
    )

    _ledgers, reference_proofs = _strict_stream_fixture()
    accelerated_proofs = copy.deepcopy(reference_proofs)
    accelerated_pre_day = accelerated_proofs[0]
    state_projection = accelerated_pre_day["state_projection"]
    assert isinstance(state_projection, dict)
    state_projection["account_root_sha256"] = "9" * 64
    accelerated_pre_day["state_root_sha256"] = _canonical_sha256(
        state_projection
    )
    accelerated_pre_day.pop("proof_root_sha256")
    accelerated_pre_day["proof_root_sha256"] = _canonical_sha256(
        accelerated_pre_day
    )
    reference = {role: _ForbiddenRows() for role in _semantic_ledgers(
        generated_at_utc="2026-01-02T08:00:01+00:00"
    )}
    accelerated = {role: _ForbiddenRows() for role in reference}

    with pytest.raises(
        SemanticParityError,
        match="semantic_pre_day_state_mismatch",
    ):
        compare_semantic_streams(
            reference,
            accelerated,
            reference_proof_rows=reference_proofs,
            accelerated_proof_rows=accelerated_proofs,
        )

    assert all(rows.iteration_count == 0 for rows in reference.values())
    assert all(rows.iteration_count == 0 for rows in accelerated.values())


def test_rejects_invalid_semantic_proof_inventory() -> None:
    from src.research_infra.replay_semantic_parity import (
        SemanticParityError,
        compare_semantic_streams,
    )

    _ledgers, reference_proofs = _strict_stream_fixture()
    accelerated_proofs = copy.deepcopy(reference_proofs)
    reference_proofs.pop(2)
    reference = {role: _ForbiddenRows() for role in _semantic_ledgers(
        generated_at_utc="2026-01-02T08:00:01+00:00"
    )}
    accelerated = {role: _ForbiddenRows() for role in reference}

    with pytest.raises(
        SemanticParityError,
        match="semantic_proof_inventory_invalid:reference",
    ):
        compare_semantic_streams(
            reference,
            accelerated,
            reference_proof_rows=reference_proofs,
            accelerated_proof_rows=accelerated_proofs,
        )

    assert all(rows.iteration_count == 0 for rows in reference.values())
    assert all(rows.iteration_count == 0 for rows in accelerated.values())


def test_rejects_semantic_proof_day_metadata_drift_before_streams() -> None:
    from src.research_infra.replay_semantic_parity import (
        SemanticParityError,
        compare_semantic_streams,
    )

    _ledgers, reference_proofs = _strict_stream_fixture()
    accelerated_proofs = copy.deepcopy(reference_proofs)
    accelerated_partition = accelerated_proofs[2]
    accelerated_partition["trading_day"] = "2026-01-03"
    accelerated_partition.pop("proof_root_sha256")
    accelerated_partition["proof_root_sha256"] = _canonical_sha256(
        accelerated_partition
    )
    reference = {
        role: _ForbiddenRows()
        for role in _semantic_ledgers(generated_at_utc="2026-01-02T08:00:01+00:00")
    }
    accelerated = {role: _ForbiddenRows() for role in reference}

    with pytest.raises(
        SemanticParityError,
        match="semantic_proof_inventory_invalid:accelerated",
    ):
        compare_semantic_streams(
            reference,
            accelerated,
            reference_proof_rows=reference_proofs,
            accelerated_proof_rows=accelerated_proofs,
        )

    assert all(rows.iteration_count == 0 for rows in reference.values())
    assert all(rows.iteration_count == 0 for rows in accelerated.values())


def test_rejects_unproven_compact_scorecard_topology_even_when_rows_equal() -> None:
    from src.research_infra.replay_semantic_parity import (
        SemanticParityError,
        compare_semantic_ledgers,
    )

    reference = _semantic_ledgers(generated_at_utc="2026-01-02T08:00:01+00:00")
    reference["scorecard"][0][
        "scheduler_option_trace_omitted_duplicate_aliases"
    ] = ["pre_scheduler_trace", "post_risk_finalizer_trace"]
    accelerated = copy.deepcopy(reference)

    with pytest.raises(
        SemanticParityError,
        match="semantic_scorecard_topology_unproven:0",
    ):
        compare_semantic_ledgers(reference, accelerated)


@pytest.mark.parametrize("mode", ["omitted", "distinct"])
def test_accepts_complete_compact_scorecard_topology_contract(
    mode: str,
) -> None:
    from src.research_infra.replay_semantic_parity import compare_semantic_ledgers

    reference = _semantic_ledgers(generated_at_utc="2026-01-02T08:00:01+00:00")
    for row in reference["scorecard"]:
        trace = row["scheduler_option_trace"]
        if mode == "omitted":
            row["scheduler_option_trace_projection_status"] = (
                "canonical_trace_preserved_exact_duplicate_aliases_omitted"
            )
            row["scheduler_option_trace_omitted_duplicate_aliases"] = [
                "pre_risk_finalizer_scheduler_option_trace"
            ]
        else:
            row["scheduler_option_trace_projection_status"] = (
                "canonical_trace_preserved_distinct_aliases_not_compacted"
            )
            row["scheduler_option_trace_omitted_duplicate_aliases"] = []
            row["pre_risk_finalizer_scheduler_option_trace"] = [
                {"option": "distinct"}
            ]
        row["scheduler_option_trace_projection_sha256"] = _canonical_sha256(
            trace
        )
    accelerated = copy.deepcopy(reference)

    assert compare_semantic_ledgers(reference, accelerated)["parity_status"] == "INCOMPLETE_DIAGNOSTIC_ONLY"


def test_rejects_dangling_missed_candidate_reference() -> None:
    from src.research_infra.replay_semantic_parity import (
        SemanticParityError,
        compare_semantic_ledgers,
    )

    reference = _semantic_ledgers(generated_at_utc="2026-01-02T08:00:01+00:00")
    for ledgers in (reference,):
        ledgers["missed"][0][
            "canonical_replay_candidate_instance_key"
        ] = "candidate-instance-missing"
        ledgers["missed"][0]["candidate_id"] = "candidate-missing"
    accelerated = copy.deepcopy(reference)

    with pytest.raises(
        SemanticParityError,
        match="dangling_candidate_reference:missed",
    ):
        compare_semantic_ledgers(reference, accelerated)


def test_rejects_one_sidecar_reused_by_distinct_orders() -> None:
    from src.research_infra.replay_semantic_parity import (
        SemanticParityError,
        compare_semantic_streams,
    )

    reference, reference_proofs = _strict_stream_fixture()
    accelerated = copy.deepcopy(reference)
    accelerated_proofs = copy.deepcopy(reference_proofs)
    for ledgers, proofs in (
        (reference, reference_proofs),
        (accelerated, accelerated_proofs),
    ):
        duplicate = copy.deepcopy(ledgers["order"][0])
        duplicate["simulated_order_id"] = "simulated-order-2"
        duplicate["selected_order_sequence"] = 2
        ledgers["order"].append(duplicate)
        partition = proofs[2]["partitions"]
        assert isinstance(partition, dict)
        partition["order"] = {
            "row_count": len(ledgers["order"]),
            "ordered_rows_root_sha256": _canonical_sha256(ledgers["order"]),
        }
        _reroot_proof_row(proofs[2])

    with pytest.raises(
        SemanticParityError,
        match="semantic_sidecar_owner_mismatch|sidecar_reused_by_distinct_order",
    ):
        compare_semantic_streams(
            reference,
            accelerated,
            reference_proof_rows=reference_proofs,
            accelerated_proof_rows=accelerated_proofs,
        )


def test_rejects_sidecar_proof_bound_to_wrong_in_scope_day() -> None:
    from src.research_infra.replay_semantic_parity import (
        SemanticParityError,
        compare_semantic_streams,
    )

    reference, one_day_proofs = _strict_stream_fixture()
    accelerated = copy.deepcopy(reference)

    def two_day_proofs() -> list[dict[str, object]]:
        jan2_pre = copy.deepcopy(one_day_proofs[0]["state_projection"])
        jan2_post = copy.deepcopy(one_day_proofs[1]["state_projection"])
        assert isinstance(jan2_pre, dict)
        assert isinstance(jan2_post, dict)
        jan3_pre = copy.deepcopy(jan2_post)
        jan3_post = copy.deepcopy(jan3_pre)
        jan3_post["account_root_sha256"] = "7" * 64
        terminal = copy.deepcopy(one_day_proofs[2]["partitions"])
        sidecar = one_day_proofs[3]
        rows = [
            _self_rooted_proof_row(
                proof_sequence=0,
                proof_type="state_checkpoint",
                trading_day="2026-01-02",
                boundary="pre_day",
                state_projection=jan2_pre,
                state_root_sha256=_canonical_sha256(jan2_pre),
            ),
            _self_rooted_proof_row(
                proof_sequence=1,
                proof_type="state_checkpoint",
                trading_day="2026-01-02",
                boundary="post_day",
                state_projection=jan2_post,
                state_root_sha256=_canonical_sha256(jan2_post),
            ),
            _self_rooted_proof_row(
                proof_sequence=2,
                proof_type="state_checkpoint",
                trading_day="2026-01-03",
                boundary="pre_day",
                state_projection=jan3_pre,
                state_root_sha256=_canonical_sha256(jan3_pre),
            ),
            _self_rooted_proof_row(
                proof_sequence=3,
                proof_type="state_checkpoint",
                trading_day="2026-01-03",
                boundary="post_day",
                state_projection=jan3_post,
                state_root_sha256=_canonical_sha256(jan3_post),
            ),
            _self_rooted_proof_row(
                proof_sequence=4,
                proof_type="terminal_partition",
                trading_day="2026-01-03",
                partitions=terminal,
            ),
            _self_rooted_proof_row(
                proof_sequence=5,
                proof_type="order_sidecar_preimage",
                trading_day="2026-01-03",
                execution_packet_sidecar_id=sidecar[
                    "execution_packet_sidecar_id"
                ],
                sidecar_payload_canonical_json=sidecar[
                    "sidecar_payload_canonical_json"
                ],
                sidecar_payload_sha256=sidecar["sidecar_payload_sha256"],
                owner=copy.deepcopy(sidecar["owner"]),
            ),
        ]
        return rows

    with pytest.raises(
        SemanticParityError,
        match="semantic_sidecar_day_mismatch",
    ):
        compare_semantic_streams(
            reference,
            accelerated,
            reference_proof_rows=two_day_proofs(),
            accelerated_proof_rows=two_day_proofs(),
        )


def test_rejects_compact_scorecard_omission_status_without_marker() -> None:
    from src.research_infra.replay_semantic_parity import (
        SemanticParityError,
        compare_semantic_ledgers,
    )

    reference = _semantic_ledgers(generated_at_utc="2026-01-02T08:00:01+00:00")
    for row in reference["scorecard"]:
        trace = [{"option": row["candidate_id"]}]
        row["scheduler_option_trace"] = trace
        row["scheduler_option_trace_projection_status"] = (
            "canonical_trace_preserved_exact_duplicate_aliases_omitted"
        )
        row["scheduler_option_trace_projection_sha256"] = _canonical_sha256(
            trace
        )
        row.pop("scheduler_option_trace_omitted_duplicate_aliases", None)
    accelerated = copy.deepcopy(reference)

    with pytest.raises(
        SemanticParityError,
        match="semantic_scorecard_topology_unproven",
    ):
        compare_semantic_ledgers(reference, accelerated)


@pytest.mark.parametrize("malformation", ["proof_sequence", "row_count"])
def test_rejects_boolean_integral_semantic_proof_fields(
    malformation: str,
) -> None:
    from src.research_infra.replay_semantic_parity import (
        SemanticParityError,
        compare_semantic_streams,
    )

    reference, reference_proofs = _strict_stream_fixture()
    accelerated = copy.deepcopy(reference)
    accelerated_proofs = copy.deepcopy(reference_proofs)
    for proofs in (reference_proofs, accelerated_proofs):
        if malformation == "proof_sequence":
            proofs[1]["proof_sequence"] = True
            _reroot_proof_row(proofs[1])
        else:
            partitions = proofs[2]["partitions"]
            assert isinstance(partitions, dict)
            missed = partitions["missed"]
            assert isinstance(missed, dict)
            missed["row_count"] = True
            _reroot_proof_row(proofs[2])

    with pytest.raises(
        SemanticParityError,
        match="semantic_proof_inventory_invalid",
    ):
        compare_semantic_streams(
            reference,
            accelerated,
            reference_proof_rows=reference_proofs,
            accelerated_proof_rows=accelerated_proofs,
        )


def test_accepts_valid_nested_only_runtime_hash_closure() -> None:
    from src.research_infra.replay_semantic_parity import compare_semantic_streams

    reference, reference_proofs = _strict_stream_fixture(
        generated_at_utc="2026-01-02T08:00:01+00:00"
    )
    accelerated, accelerated_proofs = _strict_stream_fixture(
        generated_at_utc="2026-01-02T08:00:01+00:00"
    )
    sidecar_proof = accelerated_proofs[3]
    payload = json.loads(sidecar_proof["sidecar_payload_canonical_json"])
    execution = payload["execution_manager_packet"]
    nested = execution["broker_order_lifecycle_capture_v4"]
    broker = payload["broker_order_lifecycle_capture_v4_packet"]
    execution["generated_at_utc"] = "2026-01-02T08:00:03+00:00"
    nested["generated_at_utc"] = "2026-01-02T08:00:04+00:00"
    nested["packet_hash_sha256"] = _packet_hash(nested)
    execution["broker_order_lifecycle_capture_v4"] = nested
    broker["pre_order_capture_contract"][
        "execution_manager_packet_hash"
    ] = _packet_hash(execution)
    broker["packet_hash_sha256"] = _packet_hash(broker)
    payload["broker_order_lifecycle_capture_v4_packet"] = broker
    accelerated["order"][0][
        "broker_order_lifecycle_capture_v4_packet"
    ] = copy.deepcopy(broker)
    accelerated["order"][0][
        "execution_manager_packet_hash_sha256"
    ] = _canonical_sha256(execution)
    accelerated["order"][0][
        "execution_packet_sidecar_hash_sha256"
    ] = _canonical_sha256(payload)
    payload_text = json.dumps(
        payload,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
        allow_nan=False,
    )
    sidecar_proof["sidecar_payload_canonical_json"] = payload_text
    sidecar_proof["sidecar_payload_sha256"] = hashlib.sha256(
        payload_text.encode("ascii")
    ).hexdigest()
    owner = sidecar_proof["owner"]
    assert isinstance(owner, dict)
    owner["payload_root_sha256"] = sidecar_proof["sidecar_payload_sha256"]
    _reroot_proof_row(sidecar_proof)
    partitions = accelerated_proofs[2]["partitions"]
    assert isinstance(partitions, dict)
    partitions["order"] = {
        "row_count": 1,
        "ordered_rows_root_sha256": _canonical_sha256(accelerated["order"]),
    }
    _reroot_proof_row(accelerated_proofs[2])

    receipt = compare_semantic_streams(
        reference,
        accelerated,
        reference_proof_rows=reference_proofs,
        accelerated_proof_rows=accelerated_proofs,
    )
    assert receipt["parity_status"] == "INCOMPLETE_DIAGNOSTIC_ONLY"
    assert receipt["acceptance_authorized"] is False


@pytest.mark.parametrize("role", ["order", "trade"])
def test_compare_semantic_ledgers_accepts_outer_runtime_timestamp_only(
    role: str,
) -> None:
    from src.research_infra.replay_semantic_parity import compare_semantic_ledgers

    reference = _semantic_ledgers(generated_at_utc="2026-01-02T08:00:01+00:00")
    if role == "trade":
        reference["trade"][0][
            "broker_order_lifecycle_capture_v4_packet"
        ] = copy.deepcopy(
            reference["order"][0]["broker_order_lifecycle_capture_v4_packet"]
        )
    accelerated = copy.deepcopy(reference)
    accelerated[role][0]["broker_order_lifecycle_capture_v4_packet"][
        "generated_at_utc"
    ] = "2026-01-02T08:00:02+00:00"

    receipt = compare_semantic_ledgers(reference, accelerated)

    assert receipt["parity_status"] == "INCOMPLETE_DIAGNOSTIC_ONLY"
    role_receipt = next(item for item in receipt["roles"] if item["role"] == role)
    assert role_receipt["normalized_path_count"] == 1


@pytest.mark.parametrize("role", ["order", "trade"])
def test_rejects_whitespace_only_outer_runtime_timestamp(role: str) -> None:
    from src.research_infra.replay_semantic_parity import (
        SemanticParityError,
        compare_semantic_ledgers,
    )

    reference = _semantic_ledgers(generated_at_utc="2026-01-02T08:00:01+00:00")
    if role == "trade":
        reference["trade"][0][
            "broker_order_lifecycle_capture_v4_packet"
        ] = copy.deepcopy(
            reference["order"][0]["broker_order_lifecycle_capture_v4_packet"]
        )
    reference[role][0]["broker_order_lifecycle_capture_v4_packet"][
        "generated_at_utc"
    ] = "   "
    accelerated = copy.deepcopy(reference)

    with pytest.raises(
        SemanticParityError,
        match=f"{role}_runtime_envelope_timestamp_invalid",
    ):
        compare_semantic_ledgers(reference, accelerated)


def test_auxiliary_order_sequence_is_not_counted_as_primary_attempt() -> None:
    from src.research_infra.replay_semantic_parity import compare_semantic_streams

    reference, reference_proofs = _strict_stream_fixture()
    accelerated = copy.deepcopy(reference)
    accelerated_proofs = copy.deepcopy(reference_proofs)
    for ledgers, proofs in (
        (reference, reference_proofs),
        (accelerated, accelerated_proofs),
    ):
        auxiliary = copy.deepcopy(ledgers["order"][0])
        auxiliary.update(
            {
                "selected_order_attempt_primary": False,
                "selected_order_sequence": 999,
                "order_status": "simulated_expired",
                "order_event_stage": "terminal_expired",
                "event_time_utc": "2026-01-02T09:00:00+00:00",
            }
        )
        ledgers["order"].append(auxiliary)
        _update_order_partition(ledgers, proofs)
    candidates = _semantic_candidate_rows()
    for proofs in (reference_proofs, accelerated_proofs):
        _bind_candidate_partition(proofs, candidates)

    receipt = compare_semantic_streams(
        reference,
        accelerated,
        reference_candidate_rows=candidates,
        accelerated_candidate_rows=copy.deepcopy(candidates),
        reference_proof_rows=reference_proofs,
        accelerated_proof_rows=accelerated_proofs,
        expected_campaign_days=("2026-01-02",),
    )

    assert receipt["parity_status"] == "PASS_DIAGNOSTIC_ONLY"
    assert receipt["selected_order_sequence_reconciled"] is True


@pytest.mark.parametrize(
    ("role", "path", "replacement"),
    [
        ("order", ("decision_time_utc",), "2026-01-02T08:15:00+00:00"),
        ("scorecard", ("selector_action",), "blocked"),
        ("trade", ("source_sha256",), "d" * 64),
        ("oracle", ("unregistered_runtime_field",), "different"),
    ],
)
def test_compare_semantic_ledgers_rejects_nonvolatile_differences(
    role: str,
    path: tuple[str, ...],
    replacement: str,
) -> None:
    from src.research_infra.replay_semantic_parity import (
        SemanticParityError,
        compare_semantic_ledgers,
    )

    reference = _semantic_ledgers(generated_at_utc="2026-01-02T08:00:01+00:00")
    accelerated = copy.deepcopy(reference)
    accelerated[role][0][path[0]] = replacement

    with pytest.raises(SemanticParityError, match=f"semantic_row_mismatch:{role}"):
        compare_semantic_ledgers(reference, accelerated)


def test_compare_semantic_ledgers_rejects_hash_only_difference() -> None:
    from src.research_infra.replay_semantic_parity import (
        SemanticParityError,
        compare_semantic_ledgers,
    )

    reference = _semantic_ledgers(generated_at_utc="2026-01-02T08:00:01+00:00")
    accelerated = copy.deepcopy(reference)
    accelerated["order"][0]["execution_packet_sidecar_hash_sha256"] = "e" * 64

    with pytest.raises(SemanticParityError, match="semantic_preimage_missing:order:0"):
        compare_semantic_ledgers(reference, accelerated)


def test_compare_semantic_ledgers_rejects_missing_or_forged_preimage() -> None:
    from src.research_infra.replay_semantic_parity import (
        SemanticParityError,
        compare_semantic_ledgers,
    )

    reference = _semantic_ledgers(generated_at_utc="2026-01-02T08:00:01+00:00")
    accelerated = _semantic_ledgers(generated_at_utc="2026-01-02T08:00:02+00:00")
    with pytest.raises(SemanticParityError, match="semantic_preimage_missing:order:0"):
        compare_semantic_ledgers(reference, accelerated)

    reference_preimages = _order_fixture(
        generated_at_utc="2026-01-02T08:00:01+00:00"
    )[1]
    accelerated_preimages = _order_fixture(
        generated_at_utc="2026-01-02T08:00:02+00:00"
    )[1]
    accelerated["order"][0]["broker_order_lifecycle_capture_v4_packet"][
        "pre_order_capture_contract"
    ]["execution_manager_packet_hash"] = "e" * 64
    packet = accelerated["order"][0][
        "broker_order_lifecycle_capture_v4_packet"
    ]
    packet["packet_hash_sha256"] = _packet_hash(packet)
    accelerated_preimages[_default_execution_sidecar_id()][
        "broker_order_lifecycle_capture_v4_packet"
    ] = copy.deepcopy(packet)
    with pytest.raises(
        SemanticParityError,
        match="semantic_preimage_execution_hash_mismatch:order:0",
    ):
        compare_semantic_ledgers(
            reference,
            accelerated,
            reference_provenance_preimages=reference_preimages,
            accelerated_provenance_preimages=accelerated_preimages,
        )


def test_compare_semantic_ledgers_rejects_cardinality_duplicates_and_order() -> None:
    from src.research_infra.replay_semantic_parity import (
        SemanticParityError,
        compare_semantic_ledgers,
    )

    reference = _semantic_ledgers(generated_at_utc="2026-01-02T08:00:01+00:00")
    extra = copy.deepcopy(reference)
    extra["scorecard"].append(copy.deepcopy(extra["scorecard"][0]))
    with pytest.raises(SemanticParityError, match="semantic_row_count_mismatch"):
        compare_semantic_ledgers(reference, extra)

    reordered = copy.deepcopy(reference)
    reordered["scorecard"].reverse()
    with pytest.raises(SemanticParityError, match="semantic_row_mismatch:scorecard"):
        compare_semantic_ledgers(reference, reordered)


def test_compare_semantic_ledgers_rejects_dangling_candidate_reference() -> None:
    from src.research_infra.replay_semantic_parity import (
        SemanticParityError,
        compare_semantic_ledgers,
    )

    reference = _semantic_ledgers(generated_at_utc="2026-01-02T08:00:01+00:00")
    accelerated = copy.deepcopy(reference)
    for ledgers in (reference, accelerated):
        ledgers["trade"][0][
            "canonical_replay_candidate_instance_key"
        ] = "candidate-instance-missing"

    with pytest.raises(SemanticParityError, match="dangling_candidate_reference:trade"):
        compare_semantic_ledgers(reference, accelerated)


def test_compare_semantic_ledgers_rejects_candidate_from_wrong_window() -> None:
    from src.research_infra.replay_semantic_parity import (
        SemanticParityError,
        compare_semantic_ledgers,
    )

    reference = _semantic_ledgers(generated_at_utc="2026-01-02T08:00:01+00:00")
    accelerated = copy.deepcopy(reference)
    for ledgers in (reference, accelerated):
        ledgers["trade"][0]["decision_window_id"] = "window-2"

    with pytest.raises(SemanticParityError, match="dangling_candidate_reference:trade"):
        compare_semantic_ledgers(reference, accelerated)


def test_compare_semantic_ledgers_rejects_wrong_schema_and_order_reference() -> None:
    from src.research_infra.replay_semantic_parity import (
        SemanticParityError,
        compare_semantic_ledgers,
    )

    reference = _semantic_ledgers(generated_at_utc="2026-01-02T08:00:01+00:00")
    accelerated = copy.deepcopy(reference)
    for ledgers in (reference, accelerated):
        ledgers["trade"][0]["row_type"] = "trade"
    with pytest.raises(SemanticParityError, match="semantic_row_schema_invalid:trade"):
        compare_semantic_ledgers(reference, accelerated)

    reference = _semantic_ledgers(generated_at_utc="2026-01-02T08:00:01+00:00")
    accelerated = copy.deepcopy(reference)
    for ledgers in (reference, accelerated):
        ledgers["oracle"][0]["simulated_order_id"] = "missing-order"
    with pytest.raises(SemanticParityError, match="dangling_order_reference:oracle"):
        compare_semantic_ledgers(reference, accelerated)


def test_compare_semantic_ledgers_rejects_equal_invalid_lifecycle_hash() -> None:
    from src.research_infra.replay_semantic_parity import (
        SemanticParityError,
        compare_semantic_ledgers,
    )

    reference = _semantic_ledgers(generated_at_utc="2026-01-02T08:00:01+00:00")
    reference["order"][0]["broker_order_lifecycle_capture_v4_packet"][
        "packet_hash_sha256"
    ] = "e" * 64
    accelerated = copy.deepcopy(reference)

    with pytest.raises(
        SemanticParityError,
        match="order_runtime_envelope_packet_hash_invalid:0",
    ):
        compare_semantic_ledgers(reference, accelerated)


@pytest.mark.parametrize(
    ("reference_value", "accelerated_value"),
    [
        (True, 1),
        (1, 1.0),
        (0.0, -0.0),
    ],
)
def test_compare_semantic_ledgers_uses_canonical_json_identity(
    reference_value: object,
    accelerated_value: object,
) -> None:
    from src.research_infra.replay_semantic_parity import (
        SemanticParityError,
        compare_semantic_ledgers,
    )

    reference = _semantic_ledgers(generated_at_utc="2026-01-02T08:00:01+00:00")
    accelerated = copy.deepcopy(reference)
    reference["scorecard"][0]["semantic_probe"] = reference_value
    accelerated["scorecard"][0]["semantic_probe"] = accelerated_value

    with pytest.raises(SemanticParityError, match="semantic_row_mismatch:scorecard"):
        compare_semantic_ledgers(reference, accelerated)


def test_compare_semantic_ledgers_rejects_nonfinite_numeric_values() -> None:
    """Any non-finite leaf is a hard parity failure.

    Superseded `test_compare_semantic_ledgers_preserves_nonfinite_numeric_identity`
    (Opus-5 architecture audit, finding R-P1).

    Invariant the old test protected: non-finite values are compared by exact
    class and sign, so `+inf` vs `-inf` is a mismatch.

    Was that protection real? Only half of it. `canonical_bytes` used
    `allow_nan=True`, so `NaN` serialised to the bare token `NaN` and — because
    parity is byte equality — two runs that BOTH produced `NaN` in an economic
    field compared EQUAL and the comparator reported zero differences. That is
    precisely the case a broken computation produces. Meanwhile all 28 sealing
    encoders in this package use `allow_nan=False` and raise on the same input,
    so the parity gate was strictly weaker than the sealing gate.

    Replacement: treat any non-finite leaf as a hard parity failure. This is
    strictly stronger — it still catches the `+inf`/`-inf` sign flip below, and
    additionally catches `NaN`/`NaN`. No accepted artifact is affected: a scan of
    the materialised Phase-D January S1R1 ledgers found zero non-finite tokens.
    """
    from src.research_infra.replay_semantic_parity import (
        SemanticParityError,
        compare_semantic_ledgers,
    )

    reference = _semantic_ledgers(generated_at_utc="2026-01-02T08:00:01+00:00")
    accelerated = copy.deepcopy(reference)

    # Identical non-finite values used to PASS. They must now fail closed.
    reference["scorecard"][0]["nonfinite_probe"] = float("inf")
    accelerated["scorecard"][0]["nonfinite_probe"] = float("inf")
    with pytest.raises(SemanticParityError, match="semantic_row_non_finite:scorecard"):
        compare_semantic_ledgers(reference, accelerated)

    # The sign flip the old test protected still fails.
    accelerated["scorecard"][0]["nonfinite_probe"] = float("-inf")
    with pytest.raises(SemanticParityError, match="semantic_row_non_finite:scorecard"):
        compare_semantic_ledgers(reference, accelerated)

    # The case the old behaviour could not catch at all.
    reference["scorecard"][0]["nonfinite_probe"] = float("nan")
    accelerated["scorecard"][0]["nonfinite_probe"] = float("nan")
    with pytest.raises(SemanticParityError, match="semantic_row_non_finite:scorecard"):
        compare_semantic_ledgers(reference, accelerated)

    # Finite values are unaffected.
    reference["scorecard"][0]["nonfinite_probe"] = 1.5
    accelerated["scorecard"][0]["nonfinite_probe"] = 1.5
    assert (
        compare_semantic_ledgers(reference, accelerated)["parity_status"]
        == "INCOMPLETE_DIAGNOSTIC_ONLY"
    )


def _semantic_candidate_rows() -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for candidate_key in ("candidate-instance-1", "candidate-instance-2"):
        rows.append(
            {
                "row_type": "candidate_index",
                "row_provenance_schema": (
                    "broad_live_as_if_replay_row_provenance_v1"
                ),
                "candidate_index_schema": (
                    "compact_broad_replay_candidate_index_v1"
                ),
                "campaign": "campaign-1",
                "profile": "S0R0",
                "decision_window_id": (
                    "window-2" if candidate_key.endswith("-2") else "window-1"
                ),
                "candidate_id": candidate_key.replace("-instance", ""),
                "canonical_replay_candidate_instance_key": candidate_key,
                "decision_time_utc": "2026-01-02T08:00:00+00:00",
                "trading_day": "2026-01-02",
            }
        )
    return rows


def _sidecar_owner(
    order: dict[str, object],
    *,
    payload_root_sha256: str,
) -> dict[str, object]:
    return {
        "campaign": order["campaign"],
        "profile": order["profile"],
        "decision_window_id": order["decision_window_id"],
        "canonical_replay_candidate_instance_key": order[
            "canonical_replay_candidate_instance_key"
        ],
        "candidate_id": order["candidate_id"],
        "simulated_order_id": order["simulated_order_id"],
        "decision_time_utc": order["decision_time_utc"],
        "payload_root_sha256": payload_root_sha256,
    }


def _bind_candidate_partition(
    proofs: list[dict[str, object]],
    candidate_rows: list[dict[str, object]],
) -> None:
    partitions = proofs[2]["partitions"]
    assert isinstance(partitions, dict)
    partitions["candidate"] = {
        "row_count": len(candidate_rows),
        "ordered_rows_root_sha256": _canonical_sha256(candidate_rows),
    }
    _reroot_proof_row(proofs[2])


def _bind_sidecar_owner(
    ledgers: dict[str, list[dict[str, object]]],
    proofs: list[dict[str, object]],
) -> None:
    sidecar = proofs[-1]
    payload_root = sidecar["sidecar_payload_sha256"]
    assert isinstance(payload_root, str)
    sidecar["owner"] = _sidecar_owner(
        ledgers["order"][0],
        payload_root_sha256=payload_root,
    )
    _reroot_proof_row(sidecar)


def _update_order_partition(
    ledgers: dict[str, list[dict[str, object]]],
    proofs: list[dict[str, object]],
) -> None:
    partitions = proofs[2]["partitions"]
    assert isinstance(partitions, dict)
    partitions["order"] = {
        "row_count": len(ledgers["order"]),
        "ordered_rows_root_sha256": _canonical_sha256(ledgers["order"]),
    }
    _reroot_proof_row(proofs[2])


def _gapped_campaign_proofs(
    one_day_proofs: list[dict[str, object]],
) -> list[dict[str, object]]:
    jan2_pre = copy.deepcopy(one_day_proofs[0]["state_projection"])
    jan2_post = copy.deepcopy(one_day_proofs[1]["state_projection"])
    assert isinstance(jan2_pre, dict)
    assert isinstance(jan2_post, dict)
    jan5_pre = copy.deepcopy(jan2_post)
    jan5_post = copy.deepcopy(jan5_pre)
    jan5_post["account_root_sha256"] = "7" * 64
    terminal = copy.deepcopy(one_day_proofs[2]["partitions"])
    sidecar = one_day_proofs[3]
    return [
        _self_rooted_proof_row(
            proof_sequence=0,
            proof_type="state_checkpoint",
            trading_day="2026-01-02",
            boundary="pre_day",
            state_projection=jan2_pre,
            state_root_sha256=_canonical_sha256(jan2_pre),
        ),
        _self_rooted_proof_row(
            proof_sequence=1,
            proof_type="state_checkpoint",
            trading_day="2026-01-02",
            boundary="post_day",
            state_projection=jan2_post,
            state_root_sha256=_canonical_sha256(jan2_post),
        ),
        _self_rooted_proof_row(
            proof_sequence=2,
            proof_type="state_checkpoint",
            trading_day="2026-01-05",
            boundary="pre_day",
            state_projection=jan5_pre,
            state_root_sha256=_canonical_sha256(jan5_pre),
        ),
        _self_rooted_proof_row(
            proof_sequence=3,
            proof_type="state_checkpoint",
            trading_day="2026-01-05",
            boundary="post_day",
            state_projection=jan5_post,
            state_root_sha256=_canonical_sha256(jan5_post),
        ),
        _self_rooted_proof_row(
            proof_sequence=4,
            proof_type="terminal_partition",
            trading_day="2026-01-05",
            partitions=terminal,
        ),
        _self_rooted_proof_row(
            proof_sequence=5,
            proof_type="order_sidecar_preimage",
            trading_day="2026-01-02",
            execution_packet_sidecar_id=sidecar[
                "execution_packet_sidecar_id"
            ],
            sidecar_payload_canonical_json=sidecar[
                "sidecar_payload_canonical_json"
            ],
            sidecar_payload_sha256=sidecar["sidecar_payload_sha256"],
            owner=copy.deepcopy(sidecar["owner"]),
        ),
    ]


def test_production_semantic_diagnostic_entrypoint_is_source_manifest_only() -> None:
    import src.research_infra.replay_semantic_diagnostic as diagnostic

    signature = inspect.signature(diagnostic.run_production_semantic_diagnostic)

    assert tuple(signature.parameters) == (
        "reference_source_manifest_path",
        "accelerated_source_manifest_path",
    )
    assert not hasattr(diagnostic, "produce_semantic_proof_rows")
    assert "run_production_semantic_diagnostic" in diagnostic.__all__


def test_producer_derives_strict_proof_rows_from_authenticated_surfaces() -> None:
    from src.research_infra.replay_semantic_diagnostic import (
        _produce_semantic_proof_rows,
    )
    from src.research_infra.replay_semantic_parity import compare_semantic_streams

    ledgers, fixture_proofs = _strict_stream_fixture()
    candidates = _semantic_candidate_rows()
    state_rows = [
        {
            "schema": "gtos.replay_acceleration.semantic_state_checkpoint.v1",
            "campaign": "campaign-1",
            "profile": "S0R0",
            "trading_day": proof["trading_day"],
            "boundary": proof["boundary"],
            "state_projection": copy.deepcopy(proof["state_projection"]),
            "state_root_sha256": proof["state_root_sha256"],
        }
        for proof in fixture_proofs[:2]
    ]
    preimage = fixture_proofs[3]
    preimage_rows = [
        {
            "schema": "gtos.replay_acceleration.semantic_order_preimage.v1",
            "profile": "S0R0",
            "trading_day": preimage["trading_day"],
            "execution_packet_sidecar_id": preimage[
                "execution_packet_sidecar_id"
            ],
            "sidecar_payload_canonical_json": preimage[
                "sidecar_payload_canonical_json"
            ],
            "sidecar_payload_sha256": preimage["sidecar_payload_sha256"],
            "owner": copy.deepcopy(preimage["owner"]),
        }
    ]

    produced = _produce_semantic_proof_rows(
        campaign_days=("2026-01-02",),
        state_checkpoint_rows=state_rows,
        candidate_rows=candidates,
        missed_rows=ledgers["missed"],
        order_rows=ledgers["order"],
        trade_rows=ledgers["trade"],
        order_preimage_rows=preimage_rows,
    )
    receipt = compare_semantic_streams(
        ledgers,
        copy.deepcopy(ledgers),
        reference_candidate_rows=candidates,
        accelerated_candidate_rows=copy.deepcopy(candidates),
        reference_proof_rows=produced,
        accelerated_proof_rows=copy.deepcopy(produced),
        expected_campaign_days=("2026-01-02",),
    )

    assert receipt["parity_status"] == "PASS_DIAGNOSTIC_ONLY"
    assert receipt["diagnostic_complete"] is True
    assert receipt["acceptance_authorized"] is False


def test_production_semantic_adapter_verifies_both_archives_before_direct_files(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from pathlib import Path

    import src.research_infra.replay_semantic_diagnostic as diagnostic

    events: list[str] = []

    def fake_prepare(path: Path) -> dict[str, object]:
        return {
            "path": path,
            "raw_sha256": "d" * 64,
            "manifest": {
                "source_identity": {"profile": "S0R0"},
                "calendar": {"days": ["2026-01-02"]},
                "archive": {
                    "campaign_manifest": {
                        "path": str(path.with_name(f"{path.stem}-archive.json")),
                    },
                },
                "comparison_scope": {
                    "comparison_scope_root_sha256": "c" * 64,
                },
                "source_manifest_root_sha256": "b" * 64,
                "evidence_set_root_sha256": "e" * 64,
            },
        }

    def fake_verify(
        path: Path,
    ) -> tuple[dict[str, list[dict[str, object]]], dict[str, object]]:
        events.append(f"archive:{path.name}")
        return (
            {"scorecard": [], "missed": []},
            {"verification_root_sha256": "a" * 64},
        )

    def fake_load(
        prepared: dict[str, object],
        archive_rows: dict[str, list[dict[str, object]]],
        archive_report: dict[str, object],
    ) -> dict[str, list[dict[str, object]]]:
        assert events[:2] == [
            "archive:reference-source-archive.json",
            "archive:accelerated-source-archive.json",
        ]
        assert archive_rows == {"scorecard": [], "missed": []}
        assert archive_report == {"verification_root_sha256": "a" * 64}
        path = prepared["path"]
        assert isinstance(path, Path)
        events.append(f"direct:{path.name}")
        return {
            "candidate": [],
            "scorecard": [],
            "order": [],
            "trade": [],
            "oracle": [],
            "missed": [],
            "state_checkpoint": [],
            "order_preimage": [],
        }

    monkeypatch.setattr(diagnostic, "_prepare_source_manifest", fake_prepare)
    monkeypatch.setattr(diagnostic, "_verified_archive_rows", fake_verify)
    monkeypatch.setattr(diagnostic, "_load_authenticated_source", fake_load)
    monkeypatch.setattr(
        diagnostic,
        "_produce_semantic_proof_rows",
        lambda **_kwargs: [],
    )
    monkeypatch.setattr(
        diagnostic,
        "compare_semantic_streams",
        lambda *_args, **_kwargs: {
            "status": "DECLARED_RUNTIME_ENVELOPE_SEMANTIC_DIAGNOSTIC_PASS",
            "parity_status": "PASS_DIAGNOSTIC_ONLY",
            "acceptance_authorized": False,
            "diagnostic_complete": True,
        },
    )

    receipt = diagnostic.run_production_semantic_diagnostic(
        reference_source_manifest_path=Path("reference-source.json"),
        accelerated_source_manifest_path=Path("accelerated-source.json"),
    )

    assert events == [
        "archive:reference-source-archive.json",
        "archive:accelerated-source-archive.json",
        "direct:reference-source.json",
        "direct:accelerated-source.json",
    ]
    assert receipt["parity_status"] == "PASS_DIAGNOSTIC_ONLY"
    assert receipt["acceptance_authorized"] is False
    assert receipt["exact_persisted_byte_acceptance_delegated"] is True


def test_window_scorecard_uses_authenticated_candidate_stream() -> None:
    from src.research_infra.replay_semantic_parity import compare_semantic_streams

    reference, reference_proofs = _strict_stream_fixture()
    accelerated = copy.deepcopy(reference)
    accelerated_proofs = copy.deepcopy(reference_proofs)
    reference["scorecard"] = [reference["scorecard"][0]]
    accelerated["scorecard"] = [accelerated["scorecard"][0]]
    reference_candidates = _semantic_candidate_rows()
    accelerated_candidates = copy.deepcopy(reference_candidates)
    _bind_candidate_partition(reference_proofs, reference_candidates)
    _bind_candidate_partition(accelerated_proofs, accelerated_candidates)

    receipt = compare_semantic_streams(
        reference,
        accelerated,
        reference_candidate_rows=reference_candidates,
        accelerated_candidate_rows=accelerated_candidates,
        reference_proof_rows=reference_proofs,
        accelerated_proof_rows=accelerated_proofs,
        expected_campaign_days=("2026-01-02",),
    )

    assert receipt["parity_status"] == "PASS_DIAGNOSTIC_ONLY"
    assert receipt["candidate_partition_recomputed"] is True


def test_rejects_duplicate_candidate_identity() -> None:
    from src.research_infra.replay_semantic_parity import (
        SemanticParityError,
        compare_semantic_streams,
    )

    reference, reference_proofs = _strict_stream_fixture()
    accelerated = copy.deepcopy(reference)
    accelerated_proofs = copy.deepcopy(reference_proofs)
    reference_candidates = _semantic_candidate_rows()
    reference_candidates.append(copy.deepcopy(reference_candidates[0]))
    accelerated_candidates = copy.deepcopy(reference_candidates)
    _bind_candidate_partition(reference_proofs, reference_candidates)
    _bind_candidate_partition(accelerated_proofs, accelerated_candidates)

    with pytest.raises(SemanticParityError, match="duplicate_candidate_identity"):
        compare_semantic_streams(
            reference,
            accelerated,
            reference_candidate_rows=reference_candidates,
            accelerated_candidate_rows=accelerated_candidates,
            reference_proof_rows=reference_proofs,
            accelerated_proof_rows=accelerated_proofs,
            expected_campaign_days=("2026-01-02",),
        )


def test_v4_producer_sidecar_round_trips_losslessly() -> None:
    from src.research_infra.replay_semantic_parity import compare_semantic_streams
    from src.research_infra.v4_timewarp_simulated_live_research_loop import (
        build_lossless_semantic_order_preimage,
    )

    reference, reference_proofs = _strict_stream_fixture()
    accelerated = copy.deepcopy(reference)
    accelerated_proofs = copy.deepcopy(reference_proofs)
    order = reference["order"][0]
    _row, preimages = _order_fixture(generated_at_utc="2026-01-02T08:00:01+00:00")
    preimage = preimages[_default_execution_sidecar_id()]
    produced = build_lossless_semantic_order_preimage(
        campaign=str(order["campaign"]),
        profile=str(order["profile"]),
        decision_window_id=str(order["decision_window_id"]),
        canonical_replay_candidate_instance_key=str(
            order["canonical_replay_candidate_instance_key"]
        ),
        candidate_id=str(order["candidate_id"]),
        simulated_order_id=str(order["simulated_order_id"]),
        decision_time_utc=str(order["decision_time_utc"]),
        trading_day="2026-01-02",
        execution_manager_packet=preimage["execution_manager_packet"],
        broker_order_lifecycle_capture_v4_packet=preimage[
            "broker_order_lifecycle_capture_v4_packet"
        ],
    )
    payload_text = produced["sidecar_payload_canonical_json"]
    assert isinstance(payload_text, str)
    assert json.loads(payload_text) == preimage

    for ledgers, proofs in (
        (reference, reference_proofs),
        (accelerated, accelerated_proofs),
    ):
        ledgers["order"][0]["execution_packet_sidecar_hash_sha256"] = produced[
            "sidecar_payload_sha256"
        ]
        proofs[-1] = _self_rooted_proof_row(
            proof_sequence=3,
            proof_type="order_sidecar_preimage",
            trading_day=produced["trading_day"],
            execution_packet_sidecar_id=produced[
                "execution_packet_sidecar_id"
            ],
            sidecar_payload_canonical_json=payload_text,
            sidecar_payload_sha256=produced["sidecar_payload_sha256"],
            owner=copy.deepcopy(produced["owner"]),
        )
        _update_order_partition(ledgers, proofs)
    candidates = _semantic_candidate_rows()
    for proofs in (reference_proofs, accelerated_proofs):
        _bind_candidate_partition(proofs, candidates)

    receipt = compare_semantic_streams(
        reference,
        accelerated,
        reference_candidate_rows=candidates,
        accelerated_candidate_rows=copy.deepcopy(candidates),
        reference_proof_rows=reference_proofs,
        accelerated_proof_rows=accelerated_proofs,
        expected_campaign_days=("2026-01-02",),
    )
    assert receipt["parity_status"] == "PASS_DIAGNOSTIC_ONLY"


def test_rejects_blank_normalized_preimage_timestamps() -> None:
    from src.research_infra.replay_semantic_parity import (
        SemanticParityError,
        compare_semantic_streams,
    )

    reference, reference_proofs = _strict_stream_fixture()
    accelerated = copy.deepcopy(reference)
    accelerated_proofs = copy.deepcopy(reference_proofs)
    for ledgers, proofs in (
        (reference, reference_proofs),
        (accelerated, accelerated_proofs),
    ):
        sidecar = proofs[-1]
        payload = json.loads(sidecar["sidecar_payload_canonical_json"])
        execution = payload["execution_manager_packet"]
        nested = execution["broker_order_lifecycle_capture_v4"]
        broker = payload["broker_order_lifecycle_capture_v4_packet"]
        execution["generated_at_utc"] = ""
        nested["generated_at_utc"] = ""
        nested["packet_hash_sha256"] = _packet_hash(nested)
        execution["broker_order_lifecycle_capture_v4"] = nested
        broker["pre_order_capture_contract"][
            "execution_manager_packet_hash"
        ] = _packet_hash(execution)
        broker["packet_hash_sha256"] = _packet_hash(broker)
        payload["broker_order_lifecycle_capture_v4_packet"] = broker
        ledgers["order"][0][
            "broker_order_lifecycle_capture_v4_packet"
        ] = copy.deepcopy(broker)
        ledgers["order"][0][
            "execution_manager_packet_hash_sha256"
        ] = _canonical_sha256(execution)
        ledgers["order"][0][
            "execution_packet_sidecar_hash_sha256"
        ] = _canonical_sha256(payload)
        payload_text = json.dumps(
            payload,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=True,
            allow_nan=False,
        )
        sidecar["sidecar_payload_canonical_json"] = payload_text
        sidecar["sidecar_payload_sha256"] = hashlib.sha256(
            payload_text.encode("ascii")
        ).hexdigest()
        owner = sidecar["owner"]
        assert isinstance(owner, dict)
        owner["payload_root_sha256"] = sidecar["sidecar_payload_sha256"]
        _reroot_proof_row(sidecar)
        _update_order_partition(ledgers, proofs)

    with pytest.raises(
        SemanticParityError,
        match="semantic_preimage_timestamp_invalid",
    ):
        compare_semantic_streams(
            reference,
            accelerated,
            reference_proof_rows=reference_proofs,
            accelerated_proof_rows=accelerated_proofs,
        )


@pytest.mark.parametrize("malformation", ["owner", "duplicate"])
def test_rejects_sidecar_payload_owner_mismatch_and_exact_duplicate_order_event(
    malformation: str,
) -> None:
    from src.research_infra.replay_semantic_parity import (
        SemanticParityError,
        compare_semantic_streams,
    )

    reference, reference_proofs = _strict_stream_fixture()
    accelerated = copy.deepcopy(reference)
    accelerated_proofs = copy.deepcopy(reference_proofs)
    for ledgers, proofs in (
        (reference, reference_proofs),
        (accelerated, accelerated_proofs),
    ):
        _bind_sidecar_owner(ledgers, proofs)
        if malformation == "owner":
            sidecar = proofs[-1]
            payload = json.loads(sidecar["sidecar_payload_canonical_json"])
            execution = payload["execution_manager_packet"]
            broker = payload["broker_order_lifecycle_capture_v4_packet"]
            execution.setdefault("identity", {})["candidate_id"] = "candidate-other"
            broker["identity"]["candidate_id"] = "candidate-other"
            broker["pre_order_capture_contract"][
                "execution_manager_packet_hash"
            ] = _packet_hash(execution)
            broker["packet_hash_sha256"] = _packet_hash(broker)
            payload["broker_order_lifecycle_capture_v4_packet"] = broker
            ledgers["order"][0][
                "broker_order_lifecycle_capture_v4_packet"
            ] = copy.deepcopy(broker)
            ledgers["order"][0][
                "execution_manager_packet_hash_sha256"
            ] = _canonical_sha256(execution)
            ledgers["order"][0][
                "execution_packet_sidecar_hash_sha256"
            ] = _canonical_sha256(payload)
            payload_text = json.dumps(
                payload,
                sort_keys=True,
                separators=(",", ":"),
                ensure_ascii=True,
                allow_nan=False,
            )
            sidecar["sidecar_payload_canonical_json"] = payload_text
            sidecar["sidecar_payload_sha256"] = hashlib.sha256(
                payload_text.encode("ascii")
            ).hexdigest()
            owner = sidecar["owner"]
            assert isinstance(owner, dict)
            owner["payload_root_sha256"] = sidecar["sidecar_payload_sha256"]
            _reroot_proof_row(sidecar)
        else:
            duplicate = copy.deepcopy(ledgers["order"][0])
            duplicate["irrelevant_diagnostic_note"] = "mutated-copy"
            ledgers["order"].append(duplicate)
        _update_order_partition(ledgers, proofs)

    expected = (
        "semantic_sidecar_owner_mismatch"
        if malformation == "owner"
        else "duplicate_order_lifecycle_event"
    )
    with pytest.raises(SemanticParityError, match=expected):
        compare_semantic_streams(
            reference,
            accelerated,
            reference_proof_rows=reference_proofs,
            accelerated_proof_rows=accelerated_proofs,
        )


def _write_semantic_source_rows(
    path: "Path",
    rows: list[dict[str, object]],
) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        "".join(
            json.dumps(
                row,
                sort_keys=True,
                separators=(",", ":"),
                ensure_ascii=True,
                allow_nan=True,
            )
            + "\n"
            for row in rows
        ),
        encoding="ascii",
    )


def _semantic_source_fixture_rows() -> dict[str, list[dict[str, object]]]:
    campaign_id = "unit_S0R0"
    day = "2026-01-02"
    ledgers, proofs = _strict_stream_fixture()
    direct = copy.deepcopy(ledgers)
    for rows in direct.values():
        for row in rows:
            row["campaign"] = campaign_id
            row["profile"] = "S0R0"
            row["broad_replay_profile"] = "S0R0"
            row["trading_day"] = day
    exact_order = direct["order"][0]
    exact_order.pop("selected_order_attempt_primary", None)
    exact_order.pop("selected_order_sequence", None)

    proof_preimage = proofs[3]
    payload_text = str(proof_preimage["sidecar_payload_canonical_json"])
    payload = json.loads(payload_text)
    payload_sha256 = hashlib.sha256(payload_text.encode("ascii")).hexdigest()
    sidecar_id = _canonical_sha256(
        {
            "campaign": campaign_id,
            "candidate_id": exact_order["candidate_id"],
            "simulated_order_id": exact_order["simulated_order_id"],
            "type": "execution_manager_v4",
        }
    )
    execution_manager_sha256 = _canonical_sha256(
        payload["execution_manager_packet"]
    )
    exact_order["execution_packet_sidecar_id"] = sidecar_id
    exact_order["execution_packet_sidecar_hash_sha256"] = payload_sha256
    exact_order["execution_manager_packet_hash_sha256"] = (
        execution_manager_sha256
    )

    candidates: list[dict[str, object]] = []
    for original in _semantic_candidate_rows():
        candidate = {
            key: copy.deepcopy(value)
            for key, value in original.items()
            if key not in {"candidate_index_schema", "row_provenance_schema"}
        }
        candidate.update(
            {
                "schema": "gtos.replay_acceleration.semantic_candidate.v1",
                "row_type": "semantic_candidate",
                "row_provenance_schema": (
                    "gtos.replay_acceleration.semantic_candidate_provenance.v1"
                ),
                "campaign": campaign_id,
                "profile": "S0R0",
                "trading_day": day,
            }
        )
        candidates.append(candidate)

    state_rows = [
        {
            "schema": "gtos.replay_acceleration.semantic_state_checkpoint.v1",
            "campaign": campaign_id,
            "profile": "S0R0",
            "trading_day": proof["trading_day"],
            "boundary": proof["boundary"],
            "state_projection": copy.deepcopy(proof["state_projection"]),
            "state_root_sha256": proof["state_root_sha256"],
        }
        for proof in proofs[:2]
    ]
    owner = {
        "campaign": campaign_id,
        "profile": "S0R0",
        "decision_window_id": exact_order["decision_window_id"],
        "canonical_replay_candidate_instance_key": exact_order[
            "canonical_replay_candidate_instance_key"
        ],
        "candidate_id": exact_order["candidate_id"],
        "simulated_order_id": exact_order["simulated_order_id"],
        "decision_time_utc": exact_order["decision_time_utc"],
        "payload_root_sha256": payload_sha256,
    }
    preimage_rows = [
        {
            "schema": "gtos.replay_acceleration.semantic_order_preimage.v1",
            "trading_day": day,
            "execution_packet_sidecar_id": sidecar_id,
            "sidecar_payload_canonical_json": payload_text,
            "sidecar_payload_sha256": payload_sha256,
            "semantic_execution_manager_packet_sha256": (
                execution_manager_sha256
            ),
            "owner": owner,
            "selected_order_attempt_primary": True,
            "selected_order_sequence": 1,
            "producer_order_stream_index": 0,
            "producer_order_row_sha256": _canonical_sha256(exact_order),
            "persisted_order_stream_index": 0,
            "persisted_order_row_sha256": _canonical_sha256(exact_order),
        }
    ]
    return {
        "candidate": candidates,
        "order": direct["order"],
        "trade": direct["trade"],
        "oracle": direct["oracle"],
        "state_checkpoint": state_rows,
        "order_preimage": preimage_rows,
        "scorecard": direct["scorecard"],
        "missed": direct["missed"],
    }


def _archive_partition_rows(
    rows: list[dict[str, object]],
) -> list[dict[str, object]]:
    day = "2026-01-02"
    partitioned = copy.deepcopy(rows)
    for row in partitioned:
        row.update(
            {
                "trading_day": day,
                "profile": "S0R0",
                "broad_replay_profile": "S0R0",
                "split": "development",
                "chunk_id": f"S0R0:development:{day}:{day}",
                "chunk_start_day": day,
                "chunk_end_day": day,
                "chunk_day_count": 1,
                "row_provenance_schema": (
                    "broad_live_as_if_replay_row_provenance_v1"
                ),
            }
        )
    return partitioned


def _seal_semantic_source_archive(
    exact_root: "Path",
    *,
    scorecard_rows: list[dict[str, object]],
    missed_rows: list[dict[str, object]],
):
    from src.research_infra.replay_acceleration_streaming_archive import (
        StreamingProofArchive,
    )

    day = "2026-01-02"
    decision_rows = _archive_partition_rows(
        [
            {
                "row_type": "asof_decision",
                "campaign": "unit_S0R0",
                "canonical_replay_candidate_instance_key": (
                    "candidate-instance-1"
                ),
            }
        ]
    )
    hot_outputs = {
        "decision": exact_root / "UNIT_DECISION_LEDGER.jsonl",
        "scorecard": exact_root / "UNIT_SCORECARD_LEDGER.jsonl",
        "missed": exact_root / "UNIT_MISSED_OPPORTUNITY_LEDGER.jsonl",
    }
    _write_semantic_source_rows(hot_outputs["decision"], decision_rows)
    _write_semantic_source_rows(
        hot_outputs["scorecard"],
        _archive_partition_rows(scorecard_rows),
    )
    _write_semantic_source_rows(
        hot_outputs["missed"],
        _archive_partition_rows(missed_rows),
    )
    archive = StreamingProofArchive(
        root=exact_root / "proof-archive",
        output_prefix="UNIT",
        hot_outputs=hot_outputs,
        max_archive_bytes=64 * 1024 * 1024,
        hard_floor_free_bytes=1,
    )
    identity_core = {
        "schema": "synthetic.attempt5_execution_identity.v1",
        "output_prefix": "UNIT",
    }
    identity = {
        **identity_core,
        "identity_root_sha256": _canonical_sha256(identity_core),
    }
    shared_payload = {
        "schema": "gtos.final_moonshot.broad_replay.shared_execution_contract.v1",
        "code_authority": [
            {"path": "synthetic_runner.py", "sha256": "6" * 64}
        ],
        "config_file_hashes": {"synthetic.yaml": "7" * 64},
    }
    shared_digest = _canonical_sha256(shared_payload)
    shared = {
        **shared_payload,
        "valid": True,
        "status": "shared_execution_contract_bound",
        "shared_execution_contract_digest_sha256": shared_digest,
    }
    arm = {"arm_id": "S0R0", "arm_fingerprint_sha256": "3" * 64}
    partial_path = exact_root / "UNIT_PRE_ARCHIVE_PARTIAL.json"
    partial_path.write_text(
        json.dumps(
            {
                "schema": "synthetic.pre_archive_partial.v1",
                "output_prefix": "UNIT",
                "last_completed_end_day": day,
                "attempt5_execution_identity": identity,
                "shared_execution_contract": shared,
                "b7_5_selection_sizing_factorial_arm_binding": arm,
                "b7_5_contract_binding": {
                    "actual_source_plan_digests_sha256": ["2" * 64],
                    "actual_shared_execution_contract_digest_sha256": (
                        shared_digest
                    ),
                    "selection_sizing_factorial_arm_binding": arm,
                },
            },
            sort_keys=True,
            separators=(",", ":"),
        )
        + "\n",
        encoding="ascii",
    )
    code_config_root = _canonical_sha256(
        {
            "code_authority": shared["code_authority"],
            "config_file_hashes": shared["config_file_hashes"],
        }
    )
    archive.seal_and_reclaim(
        start_day=day,
        end_day=day,
        pre_archive_partial_summary_path=partial_path,
        checkpoint_authority={
            "schema": (
                "gtos.replay_acceleration.streaming_checkpoint_authority.v1"
            ),
            "output_prefix": "UNIT",
            "run_identity_root_sha256": identity["identity_root_sha256"],
            "source_plan_digest_sha256": "2" * 64,
            "arm_fingerprint_sha256": "3" * 64,
            "shared_execution_contract_sha256": shared_digest,
            "accelerated_code_config_authority_root_sha256": code_config_root,
        },
    )
    receipt_path = archive.root / "VERIFY_RECEIPT.json"
    archive.independent_verify_campaign(receipt_path)
    return archive, receipt_path


def _build_archive_bound_semantic_source(
    root: "Path",
) -> dict[str, object]:
    from src.research_infra.replay_semantic_diagnostic import (
        write_semantic_source_manifest,
    )

    rows = _semantic_source_fixture_rows()
    exact_root = root
    semantic_root = root.parent / f"{root.name}.semantic-diagnostic"
    exact_root.mkdir(parents=True)
    semantic_root.mkdir(parents=True)
    direct_paths = {
        "candidate": semantic_root / "UNIT_SEMANTIC_CANDIDATE_LEDGER.jsonl",
        "order": exact_root / "UNIT_ORDER_LEDGER.jsonl",
        "trade": exact_root / "UNIT_TRADE_LEDGER.jsonl",
        "oracle": exact_root / "UNIT_ORDERED_PATH_ORACLE_LEDGER.jsonl",
        "state_checkpoint": (
            semantic_root / "UNIT_SEMANTIC_STATE_CHECKPOINT_LEDGER.jsonl"
        ),
        "order_preimage": (
            semantic_root / "UNIT_SEMANTIC_ORDER_PREIMAGE_LEDGER.jsonl"
        ),
    }
    for role, path in direct_paths.items():
        _write_semantic_source_rows(path, rows[role])
    archive, archive_receipt = _seal_semantic_source_archive(
        exact_root,
        scorecard_rows=rows["scorecard"],
        missed_rows=rows["missed"],
    )
    source_manifest_path = semantic_root / "UNIT_SEMANTIC_SOURCE_MANIFEST.json"
    manifest = write_semantic_source_manifest(
        source_manifest_path=source_manifest_path,
        evidence_paths=direct_paths,
        archive_manifest_path=archive.campaign_manifest_path,
        archive_verification_receipt_path=archive_receipt,
        campaign_id="unit_S0R0",
        profile="S0R0",
        arm_id="S0R0",
        campaign_days=("2026-01-02",),
    )
    return {
        "manifest": manifest,
        "manifest_path": source_manifest_path,
        "direct_paths": direct_paths,
        "archive_manifest_path": archive.campaign_manifest_path,
        "archive_receipt_path": archive_receipt,
    }


def test_archive_bound_source_manifests_run_complete_diagnostic(
    tmp_path: "Path",
) -> None:
    from pathlib import Path

    from src.research_infra.replay_semantic_diagnostic import (
        run_production_semantic_diagnostic,
    )

    assert isinstance(tmp_path, Path)
    reference = _build_archive_bound_semantic_source(tmp_path / "reference")
    accelerated = _build_archive_bound_semantic_source(tmp_path / "accelerated")

    receipt = run_production_semantic_diagnostic(
        reference_source_manifest_path=reference["manifest_path"],
        accelerated_source_manifest_path=accelerated["manifest_path"],
    )

    assert receipt["parity_status"] == "PASS_DIAGNOSTIC_ONLY"
    assert receipt["diagnostic_complete"] is True
    assert receipt["acceptance_authorized"] is False
    assert receipt["exact_persisted_byte_acceptance_delegated"] is True


def test_source_manifest_rejects_mixed_run_archive_topology(
    tmp_path: "Path",
) -> None:
    from src.research_infra.replay_semantic_diagnostic import (
        write_semantic_source_manifest,
    )

    reference = _build_archive_bound_semantic_source(tmp_path / "reference")
    accelerated = _build_archive_bound_semantic_source(tmp_path / "accelerated")

    with pytest.raises(ValueError, match="semantic_source_file_topology_invalid"):
        write_semantic_source_manifest(
            source_manifest_path=(
                reference["manifest_path"].with_name("MIXED_SOURCE.json")
            ),
            evidence_paths=reference["direct_paths"],
            archive_manifest_path=accelerated["archive_manifest_path"],
            archive_verification_receipt_path=accelerated[
                "archive_receipt_path"
            ],
            campaign_id="unit_S0R0",
            profile="S0R0",
            arm_id="S0R0",
            campaign_days=("2026-01-02",),
        )


def test_source_diagnostic_rejects_direct_file_replacement(
    tmp_path: "Path",
) -> None:
    from pathlib import Path

    from src.research_infra.replay_semantic_diagnostic import (
        run_production_semantic_diagnostic,
    )

    reference = _build_archive_bound_semantic_source(tmp_path / "reference")
    accelerated = _build_archive_bound_semantic_source(tmp_path / "accelerated")
    direct_paths = reference["direct_paths"]
    assert isinstance(direct_paths, dict)
    order_path = direct_paths["order"]
    assert isinstance(order_path, Path)
    order_path.write_bytes(order_path.read_bytes() + b"\n")

    with pytest.raises(ValueError, match="semantic_source_jsonl_invalid"):
        run_production_semantic_diagnostic(
            reference_source_manifest_path=reference["manifest_path"],
            accelerated_source_manifest_path=accelerated["manifest_path"],
        )


def test_source_diagnostic_revalidates_manifest_after_archive_verification(
    tmp_path: "Path",
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from pathlib import Path

    import src.research_infra.replay_semantic_diagnostic as diagnostic

    reference = _build_archive_bound_semantic_source(tmp_path / "reference")
    accelerated = _build_archive_bound_semantic_source(tmp_path / "accelerated")
    original_verify = diagnostic._verified_archive_rows
    calls = 0

    def replacing_verify(path: Path):
        nonlocal calls
        result = original_verify(path)
        calls += 1
        if calls == 2:
            manifest_path = reference["manifest_path"]
            assert isinstance(manifest_path, Path)
            manifest_path.write_bytes(manifest_path.read_bytes() + b" ")
        return result

    monkeypatch.setattr(diagnostic, "_verified_archive_rows", replacing_verify)

    with pytest.raises(
        ValueError,
        match="semantic_source_manifest_changed_after_archive_verify",
    ):
        diagnostic.run_production_semantic_diagnostic(
            reference_source_manifest_path=reference["manifest_path"],
            accelerated_source_manifest_path=accelerated["manifest_path"],
        )


def test_source_diagnostic_revalidates_campaign_after_archive_verification(
    tmp_path: "Path",
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from pathlib import Path

    import src.research_infra.replay_semantic_diagnostic as diagnostic

    reference = _build_archive_bound_semantic_source(tmp_path / "reference")
    accelerated = _build_archive_bound_semantic_source(tmp_path / "accelerated")
    original_verify = diagnostic._verified_archive_rows
    calls = 0

    def replacing_verify(path: Path):
        nonlocal calls
        result = original_verify(path)
        calls += 1
        if calls == 2:
            campaign_path = reference["archive_manifest_path"]
            assert isinstance(campaign_path, Path)
            campaign_path.write_bytes(campaign_path.read_bytes() + b" ")
        return result

    monkeypatch.setattr(diagnostic, "_verified_archive_rows", replacing_verify)

    with pytest.raises(
        ValueError,
        match="semantic_archive_campaign_identity_mismatch",
    ):
        diagnostic.run_production_semantic_diagnostic(
            reference_source_manifest_path=reference["manifest_path"],
            accelerated_source_manifest_path=accelerated["manifest_path"],
        )


def test_source_diagnostic_revalidates_terminal_snapshot_after_archive_verification(
    tmp_path: "Path",
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from pathlib import Path

    import src.research_infra.replay_semantic_diagnostic as diagnostic

    reference = _build_archive_bound_semantic_source(tmp_path / "reference")
    accelerated = _build_archive_bound_semantic_source(tmp_path / "accelerated")
    original_verify = diagnostic._verified_archive_rows
    calls = 0

    def replacing_verify(path: Path):
        nonlocal calls
        result = original_verify(path)
        calls += 1
        if calls == 2:
            manifest = reference["manifest"]
            assert isinstance(manifest, dict)
            snapshot_contract = manifest["archive"]["terminal_checkpoint_snapshot"]
            snapshot_path = Path(snapshot_contract["path"])
            snapshot_path.write_bytes(snapshot_path.read_bytes() + b" ")
        return result

    monkeypatch.setattr(diagnostic, "_verified_archive_rows", replacing_verify)

    reference_manifest_path = reference["manifest_path"]
    accelerated_manifest_path = accelerated["manifest_path"]
    assert isinstance(reference_manifest_path, Path)
    assert isinstance(accelerated_manifest_path, Path)

    with pytest.raises(
        ValueError,
        match="semantic_archive_checkpoint_snapshot_invalid",
    ):
        diagnostic.run_production_semantic_diagnostic(
            reference_source_manifest_path=reference_manifest_path,
            accelerated_source_manifest_path=accelerated_manifest_path,
        )


def test_rejects_non_string_semantic_proof_day() -> None:
    from src.research_infra.replay_semantic_parity import (
        SemanticParityError,
        compare_semantic_streams,
    )

    reference, reference_proofs = _strict_stream_fixture()
    accelerated = copy.deepcopy(reference)
    accelerated_proofs = copy.deepcopy(reference_proofs)
    for proofs in (reference_proofs, accelerated_proofs):
        for proof in proofs:
            proof["trading_day"] = 20260102
            _reroot_proof_row(proof)

    with pytest.raises(
        SemanticParityError,
        match="semantic_proof_inventory_invalid",
    ):
        compare_semantic_streams(
            reference,
            accelerated,
            reference_proof_rows=reference_proofs,
            accelerated_proof_rows=accelerated_proofs,
        )


def test_accepts_explicit_gapped_campaign_calendar() -> None:
    from src.research_infra.replay_semantic_parity import compare_semantic_streams

    reference, one_day_proofs = _strict_stream_fixture()
    accelerated = copy.deepcopy(reference)
    reference_proofs = _gapped_campaign_proofs(one_day_proofs)
    accelerated_proofs = copy.deepcopy(reference_proofs)

    receipt = compare_semantic_streams(
        reference,
        accelerated,
        reference_proof_rows=reference_proofs,
        accelerated_proof_rows=accelerated_proofs,
        expected_campaign_days=("2026-01-02", "2026-01-05"),
    )

    assert receipt["parity_status"] == "INCOMPLETE_DIAGNOSTIC_ONLY"
    assert receipt["campaign_calendar_bound"] is True
    assert receipt["candidate_partition_recomputed"] is False


def test_rejects_unreconciled_selected_order_sequence() -> None:
    from src.research_infra.replay_semantic_parity import (
        SemanticParityError,
        compare_semantic_streams,
    )

    reference, reference_proofs = _strict_stream_fixture()
    accelerated = copy.deepcopy(reference)
    accelerated_proofs = copy.deepcopy(reference_proofs)
    for ledgers, proofs in (
        (reference, reference_proofs),
        (accelerated, accelerated_proofs),
    ):
        post = proofs[1]
        state = post["state_projection"]
        assert isinstance(state, dict)
        state["selected_order_sequence"] = 99
        post["state_root_sha256"] = _canonical_sha256(state)
        _reroot_proof_row(post)
        ledgers["order"][0].pop("selected_order_sequence", None)
        _update_order_partition(ledgers, proofs)

    with pytest.raises(
        SemanticParityError,
        match="semantic_order_sequence_mismatch",
    ):
        compare_semantic_streams(
            reference,
            accelerated,
            reference_proof_rows=reference_proofs,
            accelerated_proof_rows=accelerated_proofs,
        )
