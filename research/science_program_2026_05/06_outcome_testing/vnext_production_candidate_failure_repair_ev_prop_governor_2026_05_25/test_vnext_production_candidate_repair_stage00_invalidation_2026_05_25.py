from __future__ import annotations

import json
from pathlib import Path


ROUTE_DIR = Path(__file__).resolve().parent
MANIFEST_PATH = ROUTE_DIR / "VNEXT_PRODUCTION_CANDIDATE_REPAIR_INPUT_MANIFEST_2026-05-25.json"
LEDGER_PATH = ROUTE_DIR / "VNEXT_PRODUCTION_CANDIDATE_REPAIR_FAILED_ROUTE_INVALIDATION_LEDGER_2026-05-25.jsonl"
STATE_PATH = ROUTE_DIR / "VNEXT_PRODUCTION_CANDIDATE_REPAIR_SESSION_STATE_2026-05-25.json"


def load_json(path: Path) -> dict:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def test_stage00_preserves_and_invalidates_failed_completion_claim() -> None:
    manifest = load_json(MANIFEST_PATH)
    facts = manifest["recomputed_failure_facts"]

    assert manifest["branch_decision"] == "failed_route_completion_claim_invalidated"
    assert facts["completion_audit_claimed_complete"] is True
    assert facts["completion_audit_embedded_stage10_status"] == "in_progress"
    assert facts["activation_safe"] is False
    assert facts["candidate_rows"] == 253234
    assert facts["baseline_selected_count"] == 35983
    assert facts["new_mechanical_selected_count"] == 10
    assert facts["new_mechanical_total_r"] == -4.999959196997


def test_stage00_hashes_shards_and_leaves_stage01_as_next_invariant() -> None:
    manifest = load_json(MANIFEST_PATH)
    state = load_json(STATE_PATH)
    with LEDGER_PATH.open("r", encoding="utf-8") as handle:
        ledger_records = [json.loads(line) for line in handle]

    assert manifest["stage09_replay_shards"]["shard_count"] == 11
    assert manifest["stage09_replay_shards"]["total_rows"] == 253234
    assert manifest["stage09_replay_shards"]["matches_stage09_written_replay_rows"] is True
    assert manifest["runtime_activation_flags"]["broker_facing_vnext_activation_flags_off"] is True
    assert state["stage_status_table"]["STAGE_00_INPUT_FREEZE_AND_FAILED_ROUTE_INVALIDATION"] == "complete"
    assert state["first_incomplete_invariant"] == "STAGE_01_FULL_FAILURE_ANATOMY_LEDGER"
    assert {record["record_type"] for record in ledger_records} >= {
        "stage00_artifact_freeze",
        "failed_completion_claim_invalidated",
        "runtime_activation_boundary_preserved",
        "stage00_completion_and_next_invariant",
    }
