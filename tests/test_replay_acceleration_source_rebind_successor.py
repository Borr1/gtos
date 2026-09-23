from __future__ import annotations

import copy
import json
from pathlib import Path

import pytest

from src.research_infra import replay_acceleration_source_rebind_successor as rebind


R6 = Path(".hermes/receipts/task2/source-bundle-consumer-rebind-20260722-r6")
R6_EVIDENCE = Path(
    ".hermes/evidence/task2/source-bundle-consumer-rebind-20260722-r6"
)


def test_bundle_projection_rejects_nonmapping_partition() -> None:
    payload = {
        "physical_partitions": [
            {
                "index": 0,
                "partition_id": "XAUUSD:M15",
                "symbol": "XAUUSD",
                "physical_timeframe": "M15",
                "logical_timeframes": ["M15"],
            },
            "malformed",
        ],
        "logical_partitions": [],
    }
    with pytest.raises(
        rebind.SourceRebindRejected,
        match="source_rebind_bundle_inventory_invalid",
    ):
        rebind._bundle_source_projection(payload)


def test_successor_run_and_verifier_envelope_are_self_authenticated() -> None:
    run_path = (
        R6_EVIDENCE
        / "materialization-current/runs/task2-state-preimage-consumer-cold.json"
    )
    envelope_path = R6 / "VERIFY_CURRENT_STATE_PREIMAGE_COLD.json"
    run = json.loads(run_path.read_text(encoding="utf-8"))
    envelope = json.loads(envelope_path.read_text(encoding="utf-8"))

    rebind.validate_successor_run(run)
    rebind.validate_independent_verifier_envelope(
        envelope,
        envelope_path=envelope_path,
    )

    tampered_run = copy.deepcopy(run)
    tampered_run["source_stage_only"] = False
    with pytest.raises(rebind.SourceRebindRejected):
        rebind.validate_successor_run(tampered_run)

    tampered_envelope = copy.deepcopy(envelope)
    tampered_envelope["receipt"]["writer_imported"] = True
    with pytest.raises(rebind.SourceRebindRejected):
        rebind.validate_independent_verifier_envelope(
            tampered_envelope,
            envelope_path=envelope_path,
        )


@pytest.mark.parametrize("reason", ("", "Task 3 spaces", "task3/cache"))
def test_successor_reason_is_machine_stable(reason: str, tmp_path: Path) -> None:
    with pytest.raises(
        rebind.SourceRebindRejected,
        match="source_rebind_reason_invalid",
    ):
        rebind.seal_successor(
            predecessor_bundle_path=tmp_path / "not-read",
            predecessor_selection_path=tmp_path / "not-read",
            successor_bundle_path=tmp_path / "not-read",
            successor_selection_path=tmp_path / "not-read",
            successor_run_path=tmp_path / "not-read",
            independent_verifier_path=tmp_path / "not-read",
            transformation_output=tmp_path / "not-written",
            authority_output=tmp_path / "not-written",
            reason=reason,
        )
