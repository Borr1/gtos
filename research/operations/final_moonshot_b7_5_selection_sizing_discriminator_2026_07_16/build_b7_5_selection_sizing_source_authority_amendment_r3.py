#!/usr/bin/env python3
"""Build/audit the replay-free January-only B7.5 R3 source correction.

This builder reads one sealed control artifact, the B7.5 source-window
contract, and invokes the current source resolver twice for January.  It does
not read the experiment protocol, R1/R2, any replay result, or any March
window/outcome artifact.  January-selected multi-month raw source containers
may still be traversed for file-integrity hashing.  The closed decision-
contract builder validates the embedded hash chain separately before applying
R3 to ``development_january`` only.
"""

from __future__ import annotations

import argparse
import copy
import hashlib
import json
import os
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable, Mapping


ROUTE = Path(__file__).resolve().parent
ROOT = Path(__file__).resolve().parents[3]
EXECUTION_ROUTE_RELATIVE_PATH = (
    "research/operations/"
    "final_moonshot_ultimate_system_denominator_to_deployment_execution_2026_06_20"
)
EXECUTION_ROUTE = ROOT / EXECUTION_ROUTE_RELATIVE_PATH

SCHEMA = (
    "gtos.b7_5.selection_sizing_january_source_authority_correction_r3.v1"
)
STATUS = "SEALED_JANUARY_ONLY_SOURCE_AUTHORITY_CORRECTION_BEFORE_REPLAY"
CANONICALIZATION = "utf8_json_sort_keys_compact_separators_ensure_ascii"
OUTPUT_PATH = ROUTE / (
    "B7_5_SELECTION_SIZING_SOURCE_AUTHORITY_REPAIR_AMENDMENT_R3.json"
)

PROTOCOL_RELATIVE_PATH = (
    "research/operations/"
    "final_moonshot_b7_5_selection_sizing_discriminator_2026_07_16/"
    "B7_5_SELECTION_SIZING_EXPERIMENT_PROTOCOL.json"
)
AMENDMENT_R1_RELATIVE_PATH = (
    "research/operations/"
    "final_moonshot_b7_5_selection_sizing_discriminator_2026_07_16/"
    "B7_5_SELECTION_SIZING_SOURCE_AUTHORITY_REPAIR_AMENDMENT_R1.json"
)
AMENDMENT_R2_RELATIVE_PATH = (
    "research/operations/"
    "final_moonshot_b7_5_selection_sizing_discriminator_2026_07_16/"
    "B7_5_SELECTION_SIZING_SOURCE_AUTHORITY_REPAIR_AMENDMENT_R2.json"
)
SOURCE_WINDOW_CONTRACT_RELATIVE_PATH = (
    f"{EXECUTION_ROUTE_RELATIVE_PATH}/"
    "B7_5_EXTENDED_HISTORY_SOURCE_WINDOW_CONTRACT.json"
)
SOURCE_PLAN_BUILDER_RELATIVE_PATH = (
    f"{EXECUTION_ROUTE_RELATIVE_PATH}/"
    "build_b7_5_extended_history_source_window_contract.py"
)
RESOLVER_RELATIVE_PATH = (
    f"{EXECUTION_ROUTE_RELATIVE_PATH}/run_broad_live_as_if_replay_harness.py"
)

EXPECTED_PROTOCOL_FILE_SHA256 = (
    "55ccc9a95647179fcf3e43acb2445b9b8ab4f2b146752cacc05b84bb8444be1a"
)
EXPECTED_AMENDMENT_R1_FILE_SHA256 = (
    "cd019fd2cb5db43838935c571d73b24b28e8c91fbbb1bd2d8f55a9416d4103e0"
)
EXPECTED_AMENDMENT_R1_SELF_HASH_SHA256 = (
    "880061b1154894599075994b723aba23aa3b5753dc341f3afedf47784e8fb713"
)
EXPECTED_AMENDMENT_R2_FILE_SHA256 = (
    "087811cb68736ed8f3daa924444a7bd09940f57b6dc3916efcc7c87232dbef66"
)
EXPECTED_AMENDMENT_R2_SELF_HASH_SHA256 = (
    "c6649eea6fbe83396aa25e6d978776567891f3f237e8d7a33a517b8e0cbb6a35"
)

EXPECTED_SOURCE_WINDOW_CONTRACT_FILE_SHA256 = (
    "13c19851a576ce1686de6857d953c2669eeae7a3e15cfea66ef702822b86c70d"
)
EXPECTED_SOURCE_WINDOW_CONTRACT_SCHEMA = (
    "gtos.final_moonshot.b7_5.extended_history_source_window_contract.v1"
)
EXPECTED_SOURCE_WINDOW_CONTRACT_STATUS = (
    "b7_5_extended_history_source_window_contract_valid_replay_closed"
)
EXPECTED_SOURCE_PLAN_BUILDER_FILE_SHA256 = (
    "b82c0f8c27ac69e368845150007ee49b1e45586860e95f5b667316483a738e17"
)
EXPECTED_RESOLVER_FILE_SHA256 = (
    "c8efd882c0f2af45ceeed0f4dbd9e917a3baae1083d447fb9b5ea40ea90cb5b4"
)

JANUARY_SOURCE_WINDOW_ID = "b7_5_2026_01"
JANUARY_DECISION_WINDOW_ID = "development_january"
JANUARY_WINDOW = {
    "window_id": JANUARY_SOURCE_WINDOW_ID,
    "start_day": "2026-01-01",
    "end_day": "2026-01-31",
}

EXPECTED_OLD_PLAN_DIGEST_SHA256 = (
    "b41714da59188be2ca1c4d72797521589a594ceb000a5e7f58eb3ac2ea5147d2"
)
EXPECTED_CURRENT_PLAN_DIGEST_SHA256 = (
    "85663876fababc9b69c1bd7041c2bd043b286b456c2e635b2a6fc2289192d4e5"
)
EXPECTED_OLD_SOURCE_ROW_COUNT = 144
EXPECTED_CURRENT_SOURCE_ROW_COUNT = 124
EXPECTED_OLD_RESOLUTION_ROW_COUNT = 931
EXPECTED_CURRENT_RESOLUTION_ROW_COUNT = 864
EXPECTED_OLD_RESOLUTION_DIGEST_SHA256 = (
    "3ac9efe43b353c9ca3bc95879a99bdd276b496800b0ba046009b671d480ffbdd"
)
EXPECTED_CURRENT_RESOLUTION_DIGEST_SHA256 = (
    "796078e9fef9019e20d28c4f094cd186a41839c03b915d1751262882d0e66868"
)
EXPECTED_STATIC_ROW_COUNT = 96
EXPECTED_STATIC_DIGEST_SHA256 = (
    "ba2da8b7f85dc6bcf64254baf56901f67bf13f0a8506878e82e9b828447a6fde"
)
EXPECTED_M1_ROW_COUNT = 744
EXPECTED_M1_DIGEST_SHA256 = (
    "7f02e7ecc24e30195cac67f15320e5249a732082b6a42c4ecf140067266c7ee4"
)
EXPECTED_TICK_AUTHORITY_ROW_COUNT = 24
EXPECTED_OLD_TICK_COMPONENT_DIGEST_SHA256 = (
    "d2255d05d0b0f951e003966a480959ab2aa0004f69310cb91da982f0094e7dc3"
)
EXPECTED_CURRENT_TICK_COMPONENT_DIGEST_SHA256 = (
    "391be51457ba42909db58724e13284aa2e490d7758666238e2f2ee2a056614d4"
)
EXPECTED_OLD_TICK_WINDOW_PLAN_DIGEST_SHA256 = (
    "ab8bf9fc9c7705ff1941a70daf22989b538bb55034b022944eaaaee15f0c76fa"
)
EXPECTED_CURRENT_TICK_WINDOW_PLAN_DIGEST_SHA256 = (
    "75b78c4eb240b3a2223ceeb544814fb3e9e2de8db2d8249f1c2a6ef26d47b38a"
)
EXPECTED_OLD_COVERED_TICK_SYMBOLS = ("USDJPY",)
EXPECTED_CURRENT_COVERED_TICK_SYMBOLS = (
    "EURUSD",
    "USDJPY",
    "XAGUSD",
    "XAUUSD",
)
EXPECTED_CHANGED_TICK_AUTHORITY_ROW_COUNT = 24

RESOLVER_CAUSE_COMMIT = {
    "commit_sha": "b136995969d8947b238731475eca4585828b41d3",
    "subject": "fix(research): repair window-scoped tick authority",
    "committed_at": "2026-07-17T03:20:18+08:00",
}


class AmendmentValidationError(ValueError):
    """Raised when the sealed source or current resolver fails closed."""


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise AmendmentValidationError(message)


def canonical_sha256(payload: Any) -> str:
    material = json.dumps(
        payload,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
        default=str,
    )
    return hashlib.sha256(material.encode("utf-8")).hexdigest()


def file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def canonical_self_hash(payload: Mapping[str, Any]) -> str:
    projection = copy.deepcopy(dict(payload))
    self_hash = projection.get("self_hash")
    _require(isinstance(self_hash, dict), "self_hash_metadata_missing")
    self_hash.pop("sha256", None)
    return canonical_sha256(projection)


def verify_self_hash(payload: Mapping[str, Any]) -> bool:
    self_hash = payload.get("self_hash")
    return bool(
        isinstance(self_hash, Mapping)
        and isinstance(self_hash.get("sha256"), str)
        and len(str(self_hash["sha256"])) == 64
        and self_hash["sha256"] == canonical_self_hash(payload)
    )


def _load_sealed_january(
    path: Path = ROOT / SOURCE_WINDOW_CONTRACT_RELATIVE_PATH,
) -> tuple[dict[str, Any], dict[str, Any], str]:
    raw = path.read_bytes()
    digest = hashlib.sha256(raw).hexdigest()
    _require(
        digest == EXPECTED_SOURCE_WINDOW_CONTRACT_FILE_SHA256,
        "sealed_source_window_contract_file_sha256_mismatch",
    )
    try:
        contract = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise AmendmentValidationError(
            f"sealed_source_window_contract_invalid_json:{exc.msg}"
        ) from exc
    _require(isinstance(contract, dict), "sealed_source_window_contract_not_mapping")
    _require(
        contract.get("schema") == EXPECTED_SOURCE_WINDOW_CONTRACT_SCHEMA,
        "sealed_source_window_contract_schema_mismatch",
    )
    _require(
        contract.get("status") == EXPECTED_SOURCE_WINDOW_CONTRACT_STATUS,
        "sealed_source_window_contract_status_mismatch",
    )
    _require(contract.get("valid") is True, "sealed_source_window_contract_invalid")
    _require(
        contract.get("replay_free_builder") is True
        and contract.get("run_campaign_call_count") == 0,
        "sealed_source_window_contract_not_replay_free",
    )
    january = next(
        (
            row
            for row in contract.get("windows") or ()
            if isinstance(row, Mapping)
            and row.get("window_id") == JANUARY_SOURCE_WINDOW_ID
        ),
        None,
    )
    _require(isinstance(january, Mapping), "sealed_january_window_missing")
    january = copy.deepcopy(dict(january))
    _require(
        january.get("start_day") == JANUARY_WINDOW["start_day"]
        and january.get("end_day") == JANUARY_WINDOW["end_day"],
        "sealed_january_window_bounds_mismatch",
    )
    _require(
        january.get("source_plan_valid") is True
        and january.get("source_cache_cleanup_valid") is True,
        "sealed_january_source_plan_invalid",
    )
    return contract, january, digest


def resolve_current_january_source_plan() -> dict[str, Any]:
    """Resolve only January through the current production replay resolver."""

    if str(EXECUTION_ROUTE) not in sys.path:
        sys.path.insert(0, str(EXECUTION_ROUTE))
    from build_b7_5_extended_history_source_window_contract import (  # noqa: PLC0415
        source_authority_plans,
    )

    plans = source_authority_plans(windows=(JANUARY_WINDOW,))
    row = plans.get(JANUARY_SOURCE_WINDOW_ID)
    _require(isinstance(row, Mapping), "current_january_source_plan_missing")
    return copy.deepcopy(dict(row))


def _tick_rows(plan: Mapping[str, Any]) -> dict[str, Mapping[str, Any]]:
    rows = plan.get("tick_window_authority_rows") or ()
    result = {
        str(row.get("symbol") or ""): row
        for row in rows
        if isinstance(row, Mapping) and row.get("symbol")
    }
    _require(
        len(result) == EXPECTED_TICK_AUTHORITY_ROW_COUNT,
        "tick_authority_symbol_cardinality_mismatch",
    )
    return result


def _covered_symbols(rows: Mapping[str, Mapping[str, Any]]) -> tuple[str, ...]:
    return tuple(
        sorted(
            symbol
            for symbol, row in rows.items()
            if int(row.get("covered_day_count") or 0) > 0
        )
    )


def _snapshot(wrapper: Mapping[str, Any]) -> dict[str, Any]:
    plan = wrapper.get("source_authority_plan")
    _require(isinstance(plan, Mapping), "source_authority_plan_missing")
    tick_rows = _tick_rows(plan)
    tick_projection = [
        {
            "symbol": symbol,
            "tick_window_authority_digest_sha256": row.get(
                "tick_window_authority_digest_sha256"
            ),
            "component_count": int(row.get("component_count") or 0),
            "covered_day_count": int(row.get("covered_day_count") or 0),
            "status": row.get("status"),
            "integrity_valid": row.get("integrity_valid"),
            "integrity_failure_count": len(row.get("integrity_failures") or ()),
        }
        for symbol, row in sorted(tick_rows.items())
    ]
    snapshot = {
        "window_id": wrapper.get("window_id"),
        "start_day": wrapper.get("start_day"),
        "end_day": wrapper.get("end_day"),
        "source_cache_cleanup_valid": wrapper.get("source_cache_cleanup_valid"),
        "source_resolution_row_count": wrapper.get("source_resolution_row_count"),
        "source_resolution_rows_digest_sha256": wrapper.get(
            "source_resolution_rows_digest_sha256"
        ),
        "plan_valid": plan.get("valid"),
        "plan_status": plan.get("status"),
        "source_row_count": plan.get("source_row_count"),
        "plan_digest_sha256": plan.get("plan_digest_sha256"),
        "static_source_row_count": plan.get("static_source_row_count"),
        "static_source_digest_sha256": plan.get(
            "static_source_digest_sha256"
        ),
        "m1_symbol_day_authority_row_count": plan.get(
            "m1_symbol_day_authority_row_count"
        ),
        "m1_day_plan_digest_sha256": plan.get("m1_day_plan_digest_sha256"),
        "tick_window_authority_row_count": plan.get(
            "tick_window_authority_row_count"
        ),
        "tick_component_source_digest_sha256": plan.get(
            "tick_component_source_digest_sha256"
        ),
        "tick_window_plan_digest_sha256": plan.get(
            "tick_window_plan_digest_sha256"
        ),
        "tick_window_integrity_failure_symbols": sorted(
            plan.get("tick_window_integrity_failure_symbols") or ()
        ),
        "incomplete_sources": copy.deepcopy(plan.get("incomplete_sources") or []),
        "covered_tick_symbols": list(_covered_symbols(tick_rows)),
        "tick_authority_rows": tick_projection,
    }
    snapshot["reproduction_projection_sha256"] = canonical_sha256(snapshot)
    return snapshot


def _validate_old_snapshot(snapshot: Mapping[str, Any]) -> None:
    expected = {
        "window_id": JANUARY_SOURCE_WINDOW_ID,
        "start_day": JANUARY_WINDOW["start_day"],
        "end_day": JANUARY_WINDOW["end_day"],
        "source_cache_cleanup_valid": True,
        "source_resolution_row_count": EXPECTED_OLD_RESOLUTION_ROW_COUNT,
        "source_resolution_rows_digest_sha256": (
            EXPECTED_OLD_RESOLUTION_DIGEST_SHA256
        ),
        "plan_valid": True,
        "source_row_count": EXPECTED_OLD_SOURCE_ROW_COUNT,
        "plan_digest_sha256": EXPECTED_OLD_PLAN_DIGEST_SHA256,
        "static_source_row_count": EXPECTED_STATIC_ROW_COUNT,
        "static_source_digest_sha256": EXPECTED_STATIC_DIGEST_SHA256,
        "m1_symbol_day_authority_row_count": EXPECTED_M1_ROW_COUNT,
        "m1_day_plan_digest_sha256": EXPECTED_M1_DIGEST_SHA256,
        "tick_window_authority_row_count": EXPECTED_TICK_AUTHORITY_ROW_COUNT,
        "tick_component_source_digest_sha256": (
            EXPECTED_OLD_TICK_COMPONENT_DIGEST_SHA256
        ),
        "tick_window_plan_digest_sha256": (
            EXPECTED_OLD_TICK_WINDOW_PLAN_DIGEST_SHA256
        ),
        "tick_window_integrity_failure_symbols": [],
        "incomplete_sources": [],
        "covered_tick_symbols": list(EXPECTED_OLD_COVERED_TICK_SYMBOLS),
    }
    for field, value in expected.items():
        _require(snapshot.get(field) == value, f"sealed_old_snapshot_mismatch:{field}")


def _validate_current_snapshot(snapshot: Mapping[str, Any]) -> None:
    expected = {
        "window_id": JANUARY_SOURCE_WINDOW_ID,
        "start_day": JANUARY_WINDOW["start_day"],
        "end_day": JANUARY_WINDOW["end_day"],
        "source_cache_cleanup_valid": True,
        "source_resolution_row_count": EXPECTED_CURRENT_RESOLUTION_ROW_COUNT,
        "source_resolution_rows_digest_sha256": (
            EXPECTED_CURRENT_RESOLUTION_DIGEST_SHA256
        ),
        "plan_valid": True,
        "source_row_count": EXPECTED_CURRENT_SOURCE_ROW_COUNT,
        "plan_digest_sha256": EXPECTED_CURRENT_PLAN_DIGEST_SHA256,
        "static_source_row_count": EXPECTED_STATIC_ROW_COUNT,
        "static_source_digest_sha256": EXPECTED_STATIC_DIGEST_SHA256,
        "m1_symbol_day_authority_row_count": EXPECTED_M1_ROW_COUNT,
        "m1_day_plan_digest_sha256": EXPECTED_M1_DIGEST_SHA256,
        "tick_window_authority_row_count": EXPECTED_TICK_AUTHORITY_ROW_COUNT,
        "tick_component_source_digest_sha256": (
            EXPECTED_CURRENT_TICK_COMPONENT_DIGEST_SHA256
        ),
        "tick_window_plan_digest_sha256": (
            EXPECTED_CURRENT_TICK_WINDOW_PLAN_DIGEST_SHA256
        ),
        "tick_window_integrity_failure_symbols": [],
        "incomplete_sources": [],
        "covered_tick_symbols": list(EXPECTED_CURRENT_COVERED_TICK_SYMBOLS),
    }
    for field, value in expected.items():
        _require(snapshot.get(field) == value, f"current_snapshot_mismatch:{field}")
    _require(
        all(row.get("integrity_valid") is True for row in snapshot["tick_authority_rows"]),
        "current_tick_integrity_invalid",
    )


def _tick_transition(
    old_snapshot: Mapping[str, Any],
    current_snapshot: Mapping[str, Any],
) -> list[dict[str, Any]]:
    old_rows = {row["symbol"]: row for row in old_snapshot["tick_authority_rows"]}
    current_rows = {
        row["symbol"]: row for row in current_snapshot["tick_authority_rows"]
    }
    _require(old_rows.keys() == current_rows.keys(), "tick_symbol_set_changed")
    rows = []
    for symbol in sorted(old_rows):
        old = old_rows[symbol]
        current = current_rows[symbol]
        rows.append(
            {
                "symbol": symbol,
                "old_tick_window_authority_digest_sha256": old[
                    "tick_window_authority_digest_sha256"
                ],
                "current_tick_window_authority_digest_sha256": current[
                    "tick_window_authority_digest_sha256"
                ],
                "digest_changed": old["tick_window_authority_digest_sha256"]
                != current["tick_window_authority_digest_sha256"],
                "old_component_count": old["component_count"],
                "current_component_count": current["component_count"],
                "old_covered_day_count": old["covered_day_count"],
                "current_covered_day_count": current["covered_day_count"],
                "old_status": old["status"],
                "current_status": current["status"],
                "current_integrity_valid": current["integrity_valid"],
                "current_integrity_failure_count": current[
                    "integrity_failure_count"
                ],
            }
        )
    _require(
        sum(row["digest_changed"] for row in rows)
        == EXPECTED_CHANGED_TICK_AUTHORITY_ROW_COUNT,
        "changed_tick_authority_row_count_mismatch",
    )
    return rows


def _validate_code_inputs() -> dict[str, Any]:
    source_builder_path = ROOT / SOURCE_PLAN_BUILDER_RELATIVE_PATH
    resolver_path = ROOT / RESOLVER_RELATIVE_PATH
    source_builder_sha256 = file_sha256(source_builder_path)
    resolver_sha256 = file_sha256(resolver_path)
    _require(
        source_builder_sha256 == EXPECTED_SOURCE_PLAN_BUILDER_FILE_SHA256,
        "source_plan_builder_file_sha256_mismatch",
    )
    _require(
        resolver_sha256 == EXPECTED_RESOLVER_FILE_SHA256,
        "resolver_file_sha256_mismatch",
    )
    return {
        "source_plan_builder_path": SOURCE_PLAN_BUILDER_RELATIVE_PATH,
        "source_plan_builder_file_sha256": source_builder_sha256,
        "resolver_path": RESOLVER_RELATIVE_PATH,
        "resolver_file_sha256": resolver_sha256,
        "causal_change": copy.deepcopy(RESOLVER_CAUSE_COMMIT),
        "causal_semantics": (
            "resolve_tick_is_authority_window_scoped_filters_nonoverlapping_"
            "components_and_deduplicates_selected_components_by_sha256"
        ),
        "source_hydration_explanation_rejected": True,
        "source_hydration_rejection_evidence": (
            "sealed_old_january_plan_already_contains_the_usdjpy_"
            "bridge_ftmo_ticks_micro_2025_2026_component"
        ),
        "cause_class": "resolver_code_semantics_change_after_source_contract_seal",
    }


def build_amendment_payload(
    *,
    sealed_at_utc: str,
    resolver: Callable[[], Mapping[str, Any]] = resolve_current_january_source_plan,
    source_window_contract_path: Path = ROOT / SOURCE_WINDOW_CONTRACT_RELATIVE_PATH,
) -> dict[str, Any]:
    """Build R3 after two identical current-resolver January reproductions."""

    _contract, old_wrapper, contract_file_sha256 = _load_sealed_january(
        source_window_contract_path
    )
    code_binding = _validate_code_inputs()
    old_snapshot = _snapshot(old_wrapper)
    _validate_old_snapshot(old_snapshot)

    current_snapshots = [_snapshot(resolver()), _snapshot(resolver())]
    for snapshot in current_snapshots:
        _validate_current_snapshot(snapshot)
    _require(
        current_snapshots[0] == current_snapshots[1],
        "current_january_reproduction_runs_differ",
    )
    current_snapshot = current_snapshots[0]
    transitions = _tick_transition(old_snapshot, current_snapshot)

    _require(
        old_snapshot["static_source_digest_sha256"]
        == current_snapshot["static_source_digest_sha256"]
        and old_snapshot["static_source_row_count"]
        == current_snapshot["static_source_row_count"],
        "static_component_changed",
    )
    _require(
        old_snapshot["m1_day_plan_digest_sha256"]
        == current_snapshot["m1_day_plan_digest_sha256"]
        and old_snapshot["m1_symbol_day_authority_row_count"]
        == current_snapshot["m1_symbol_day_authority_row_count"],
        "m1_component_changed",
    )

    payload: dict[str, Any] = {
        "schema": SCHEMA,
        "status": STATUS,
        "sealed_at_utc": sealed_at_utc,
        "scope": {
            "decision_window_id": JANUARY_DECISION_WINDOW_ID,
            "source_window_contract_window_id": JANUARY_SOURCE_WINDOW_ID,
            "start": JANUARY_WINDOW["start_day"],
            "end": JANUARY_WINDOW["end_day"],
            "repair_class": "source_authority_only",
            "factorial_treatment_change": False,
            "all_other_decision_windows_unchanged": True,
        },
        "prior_chain_binding": {
            "protocol": {
                "path": PROTOCOL_RELATIVE_PATH,
                "file_sha256": EXPECTED_PROTOCOL_FILE_SHA256,
                "preserved_immutable": True,
            },
            "r1": {
                "path": AMENDMENT_R1_RELATIVE_PATH,
                "file_sha256": EXPECTED_AMENDMENT_R1_FILE_SHA256,
                "self_hash_sha256": EXPECTED_AMENDMENT_R1_SELF_HASH_SHA256,
                "preserved_immutable": True,
            },
            "r2": {
                "path": AMENDMENT_R2_RELATIVE_PATH,
                "file_sha256": EXPECTED_AMENDMENT_R2_FILE_SHA256,
                "self_hash_sha256": EXPECTED_AMENDMENT_R2_SELF_HASH_SHA256,
                "preserved_immutable": True,
                "remains_active_for_window_id": "engineering_june_04",
            },
        },
        "sealed_source_window_contract_binding": {
            "path": SOURCE_WINDOW_CONTRACT_RELATIVE_PATH,
            "file_sha256": contract_file_sha256,
            "schema": EXPECTED_SOURCE_WINDOW_CONTRACT_SCHEMA,
            "status": EXPECTED_SOURCE_WINDOW_CONTRACT_STATUS,
            "valid": True,
            "replay_free_builder": True,
            "run_campaign_call_count": 0,
            "window_id": JANUARY_SOURCE_WINDOW_ID,
        },
        "reproduction_audit": {
            "evidence_class": (
                "replay_free_current_resolver_two_pass_exact_january_reproduction"
            ),
            "resolver_run_count": 2,
            "resolver_runs_identical": True,
            "resolver_run_projection_sha256": current_snapshot[
                "reproduction_projection_sha256"
            ],
            "reproduced_source_plan_digest_sha256": (
                EXPECTED_CURRENT_PLAN_DIGEST_SHA256
            ),
            "run_campaign_call_count": 0,
            "replay_launched": False,
            "protocol_file_read_count": 0,
            "amendment_r1_file_read_count": 0,
            "amendment_r2_file_read_count": 0,
            "outcome_ledger_read_count": 0,
            "outcome_artifact_read_count": 0,
            "march_window_evaluation_count": 0,
            "march_window_replay_count": 0,
            "march_outcome_artifact_read_count": 0,
            "march_outcome_read": False,
            "selected_january_authority_file_integrity_hashes_may_traverse_"
            "multi_month_raw_source_containers": True,
            "raw_source_container_byte_reads_are_not_march_outcome_"
            "evaluation": True,
        },
        "active_source_plan_transition": {
            "window_id": JANUARY_DECISION_WINDOW_ID,
            "source_window_contract_window_id": JANUARY_SOURCE_WINDOW_ID,
            "protocol_and_sealed_contract_source_plan_digest_sha256": (
                EXPECTED_OLD_PLAN_DIGEST_SHA256
            ),
            "current_reproduced_source_plan_digest_sha256": (
                EXPECTED_CURRENT_PLAN_DIGEST_SHA256
            ),
            "binding_action": (
                "override_development_january_source_plan_binding_with_r3_"
                "current_reproduced_digest_only"
            ),
            "old_and_r3_source_plan_arms_may_not_mix": True,
        },
        "component_transition": {
            "old_source_row_count": EXPECTED_OLD_SOURCE_ROW_COUNT,
            "current_source_row_count": EXPECTED_CURRENT_SOURCE_ROW_COUNT,
            "old_source_resolution_row_count": EXPECTED_OLD_RESOLUTION_ROW_COUNT,
            "current_source_resolution_row_count": (
                EXPECTED_CURRENT_RESOLUTION_ROW_COUNT
            ),
            "old_source_resolution_rows_digest_sha256": (
                EXPECTED_OLD_RESOLUTION_DIGEST_SHA256
            ),
            "current_source_resolution_rows_digest_sha256": (
                EXPECTED_CURRENT_RESOLUTION_DIGEST_SHA256
            ),
            "static_source_row_count": EXPECTED_STATIC_ROW_COUNT,
            "static_source_digest_sha256": EXPECTED_STATIC_DIGEST_SHA256,
            "static_component_unchanged": True,
            "m1_symbol_day_authority_row_count": EXPECTED_M1_ROW_COUNT,
            "m1_day_plan_digest_sha256": EXPECTED_M1_DIGEST_SHA256,
            "m1_component_unchanged": True,
            "tick_window_authority_row_count": (
                EXPECTED_TICK_AUTHORITY_ROW_COUNT
            ),
            "old_tick_component_source_digest_sha256": (
                EXPECTED_OLD_TICK_COMPONENT_DIGEST_SHA256
            ),
            "current_tick_component_source_digest_sha256": (
                EXPECTED_CURRENT_TICK_COMPONENT_DIGEST_SHA256
            ),
            "old_tick_window_plan_digest_sha256": (
                EXPECTED_OLD_TICK_WINDOW_PLAN_DIGEST_SHA256
            ),
            "current_tick_window_plan_digest_sha256": (
                EXPECTED_CURRENT_TICK_WINDOW_PLAN_DIGEST_SHA256
            ),
            "changed_tick_authority_row_count": (
                EXPECTED_CHANGED_TICK_AUTHORITY_ROW_COUNT
            ),
            "old_covered_tick_symbols": list(EXPECTED_OLD_COVERED_TICK_SYMBOLS),
            "current_covered_tick_symbols": list(
                EXPECTED_CURRENT_COVERED_TICK_SYMBOLS
            ),
            "incomplete_sources": [],
            "tick_integrity_failure_symbols": [],
            "only_tick_component_tick_window_and_composite_plan_changed": True,
        },
        "tick_authority_row_transition": transitions,
        "resolver_code_cause": code_binding,
        "immutable_factorial_closure": {
            "protocol_preserved_byte_for_byte": True,
            "r1_preserved_byte_for_byte": True,
            "r2_preserved_byte_for_byte": True,
            "engineering_june_04_r2_binding_unchanged": True,
            "selection_factor_changed": False,
            "sizing_factor_changed": False,
            "neutral_selection_seed_changed": False,
            "thresholds_changed": False,
            "amendment_is_arm_varying_treatment": False,
        },
        "outcome_boundary": {
            "repaired_source_replay_outcomes_read_at_seal": False,
            "replay_launched_at_seal": False,
            "january_outcome_artifact_read": False,
            "june_outcome_artifact_read": False,
            "march_outcome_read": False,
            "march_outcome_gate_unchanged": (
                "development_disposition_and_treatment_frozen"
            ),
        },
        "authority_boundary": {
            "january_source_authority_correction_only": True,
            "production_config_changed": False,
            "broker_mutation_enabled": False,
            "broker_authority": False,
            "live_authority": False,
            "canary_authority": False,
            "final_authority": False,
        },
        "self_hash": {
            "algorithm": "sha256",
            "canonicalization": CANONICALIZATION,
            "excluded_path": "self_hash.sha256",
        },
    }
    payload["self_hash"]["sha256"] = canonical_self_hash(payload)
    return payload


def atomic_write_json(path: Path, payload: Mapping[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(
        mode="w",
        encoding="utf-8",
        prefix=f".{path.name}.",
        suffix=".tmp",
        dir=path.parent,
        delete=False,
    ) as handle:
        json.dump(payload, handle, indent=2, sort_keys=True)
        handle.write("\n")
        temporary = Path(handle.name)
    os.replace(temporary, path)


def _utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace(
        "+00:00", "Z"
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=OUTPUT_PATH)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args(argv)

    existing: dict[str, Any] | None = None
    if args.check:
        try:
            existing = json.loads(args.output.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            print(f"R3_CHECK_FAILED:cannot_read_existing:{exc}", file=sys.stderr)
            return 1
        sealed_at_utc = str(existing.get("sealed_at_utc") or "")
        if not sealed_at_utc:
            print("R3_CHECK_FAILED:sealed_at_utc_missing", file=sys.stderr)
            return 1
    else:
        sealed_at_utc = _utc_now()

    try:
        payload = build_amendment_payload(sealed_at_utc=sealed_at_utc)
    except AmendmentValidationError as exc:
        print(f"R3_BUILD_FAILED:{exc}", file=sys.stderr)
        return 1

    if args.check:
        if existing != payload or not verify_self_hash(existing or {}):
            print("R3_CHECK_FAILED:stored_artifact_drift", file=sys.stderr)
            return 1
        print(
            json.dumps(
                {
                    "status": "R3_CHECK_OK",
                    "path": str(args.output),
                    "self_hash_sha256": payload["self_hash"]["sha256"],
                    "source_plan_digest_sha256": (
                        EXPECTED_CURRENT_PLAN_DIGEST_SHA256
                    ),
                    "resolver_run_count": 2,
                    "replay_launched": False,
                    "outcome_artifact_read_count": 0,
                    "march_outcome_read": False,
                },
                sort_keys=True,
            )
        )
        return 0

    atomic_write_json(args.output, payload)
    print(
        json.dumps(
            {
                "status": "R3_WRITTEN",
                "path": str(args.output),
                "file_sha256": file_sha256(args.output),
                "self_hash_sha256": payload["self_hash"]["sha256"],
                "source_plan_digest_sha256": EXPECTED_CURRENT_PLAN_DIGEST_SHA256,
                "resolver_run_count": 2,
                "replay_launched": False,
                "outcome_artifact_read_count": 0,
                "march_outcome_read": False,
            },
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
