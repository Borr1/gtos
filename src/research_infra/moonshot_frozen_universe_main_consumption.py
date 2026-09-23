from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any, Iterable


SCHEMA_VERSION = "moonshot_frozen_universe_main_consumption_v1"
DATE = "2026-05-18"
MOONSHOT_ROUTE_RELATIVE = Path(
    "research/science_program_2026_05/06_outcome_testing/"
    "weekend_mechanical_edge_factory_moonshot_2026_05_15"
)

CP280_PREFIX = "HISTORICAL_OHLC_GTOS_REPLAY_FROZEN_UNIVERSE_IMPLEMENTATION_CLOSURE"
CP281_PREFIX = "HISTORICAL_OHLC_GTOS_REPLAY_FROZEN_UNIVERSE_READY_ACTION_RUNTIME"
CP282_PREFIX = "HISTORICAL_OHLC_GTOS_REPLAY_FROZEN_UNIVERSE_MAIN_HANDOFF"

CP280_RESULT = f"{CP280_PREFIX}_RESULT_2026-05-17.json"
CP281_RESULT = f"{CP281_PREFIX}_RESULT_2026-05-17.json"
CP282_RESULT = f"{CP282_PREFIX}_RESULT_2026-05-17.json"
CP282_VERIFIER = f"{CP282_PREFIX}_VERIFIER_RESULT_2026-05-17.json"
CP282_ARTIFACT_LEDGER = f"{CP282_PREFIX}_ARTIFACT_LEDGER_2026-05-17.jsonl"
CP282_CONSUMPTION_ORDER_LEDGER = f"{CP282_PREFIX}_CONSUMPTION_ORDER_LEDGER_2026-05-17.jsonl"
CP282_COUNT_CHECK_LEDGER = f"{CP282_PREFIX}_COUNT_CHECK_LEDGER_2026-05-17.jsonl"


def sha256_path(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def stable_json(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), default=str)


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            if line.strip():
                rows.append(json.loads(line))
    return rows


def count_lines(path: Path) -> int:
    with path.open("rb") as handle:
        return sum(1 for _ in handle)


def moonshot_route_dir(moonshot_root: Path) -> Path:
    return moonshot_root / MOONSHOT_ROUTE_RELATIVE


def source_file_inventory(route_dir: Path) -> dict[str, dict[str, Any]]:
    filenames = {
        "cp280_result": CP280_RESULT,
        "cp281_result": CP281_RESULT,
        "cp282_result": CP282_RESULT,
        "cp282_verifier": CP282_VERIFIER,
        "cp282_artifact_ledger": CP282_ARTIFACT_LEDGER,
        "cp282_consumption_order_ledger": CP282_CONSUMPTION_ORDER_LEDGER,
        "cp282_count_check_ledger": CP282_COUNT_CHECK_LEDGER,
    }
    inventory: dict[str, dict[str, Any]] = {}
    for key, filename in filenames.items():
        path = route_dir / filename
        inventory[key] = {
            "path": str(MOONSHOT_ROUTE_RELATIVE / filename).replace("\\", "/"),
            "exists": path.exists(),
            "bytes": path.stat().st_size if path.exists() else 0,
            "lines": count_lines(path) if path.exists() else 0,
            "sha256": sha256_path(path) if path.exists() else None,
        }
    return inventory


def load_packet(route_dir: Path) -> dict[str, Any]:
    return {
        "cp280_result": read_json(route_dir / CP280_RESULT),
        "cp281_result": read_json(route_dir / CP281_RESULT),
        "cp282_result": read_json(route_dir / CP282_RESULT),
        "cp282_verifier": read_json(route_dir / CP282_VERIFIER),
        "artifact_rows": read_jsonl(route_dir / CP282_ARTIFACT_LEDGER),
        "consumption_order_rows": read_jsonl(route_dir / CP282_CONSUMPTION_ORDER_LEDGER),
        "count_check_rows": read_jsonl(route_dir / CP282_COUNT_CHECK_LEDGER),
        "source_inventory": source_file_inventory(route_dir),
    }


def build_artifact_consumption_rows(
    artifact_rows: Iterable[dict[str, Any]],
    consumption_order_rows: Iterable[dict[str, Any]],
    *,
    moonshot_head: str,
    moonshot_status_clean: bool,
) -> list[dict[str, Any]]:
    order_by_path: dict[str, dict[str, Any]] = {}
    for order_row in consumption_order_rows:
        for artifact_path in order_row.get("artifact_paths") or []:
            order_by_path[artifact_path] = order_row

    rows: list[dict[str, Any]] = []
    for row in artifact_rows:
        artifact_path = row.get("artifact_path")
        order_row = order_by_path.get(artifact_path, {})
        checkpoint = row.get("checkpoint")
        artifact_role = row.get("artifact_role")
        rows.append(
            {
                "schema_version": SCHEMA_VERSION,
                "row_type": "moonshot_frozen_universe_artifact_consumption",
                "row_key": hashlib.sha256(
                    stable_json(["artifact", checkpoint, artifact_role, artifact_path]).encode("utf-8")
                ).hexdigest(),
                "source_checkpoint": checkpoint,
                "source_artifact_role": artifact_role,
                "source_artifact_path": artifact_path,
                "source_artifact_sha256": row.get("artifact_sha256"),
                "source_artifact_bytes": row.get("artifact_byte_count"),
                "source_row_count": row.get("row_count"),
                "source_row_count_basis": row.get("row_count_basis"),
                "source_handoff_row_id": row.get("frozen_main_handoff_artifact_row_id"),
                "consumption_priority_order": order_row.get("priority_order"),
                "consumption_role": order_row.get("main_consumption_role"),
                "handoff_class": order_row.get("handoff_class"),
                "row_ownership": {
                    "owner_checkpoint": f"CP{checkpoint}",
                    "owner_artifact_role": artifact_role,
                    "owner_artifact_path": artifact_path,
                    "owner_row_count": row.get("row_count"),
                    "owner_row_count_basis": row.get("row_count_basis"),
                },
                "moonshot_snapshot": {
                    "worktree_head": moonshot_head,
                    "status_clean": moonshot_status_clean,
                },
                "main_consumption_action": classify_consumption_action(row, order_row),
                "research_boundary": research_boundary(),
            }
        )
    return rows


def build_consumption_order_rows(
    consumption_order_rows: Iterable[dict[str, Any]],
    *,
    moonshot_head: str,
    moonshot_status_clean: bool,
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for row in consumption_order_rows:
        rows.append(
            {
                "schema_version": SCHEMA_VERSION,
                "row_type": "moonshot_frozen_universe_consumption_order",
                "row_key": hashlib.sha256(
                    stable_json(["order", row.get("priority_order"), row.get("main_consumption_role")]).encode("utf-8")
                ).hexdigest(),
                "priority_order": row.get("priority_order"),
                "handoff_class": row.get("handoff_class"),
                "main_consumption_role": row.get("main_consumption_role"),
                "artifact_count": row.get("artifact_count"),
                "artifact_paths": row.get("artifact_paths") or [],
                "artifact_paths_sha256": row.get("artifact_paths_sha256"),
                "source_handoff_row_id": row.get("frozen_main_consumption_order_row_id"),
                "moonshot_snapshot": {
                    "worktree_head": moonshot_head,
                    "status_clean": moonshot_status_clean,
                },
                "main_consumption_action": "CONSUME_IN_CP282_PRIORITY_ORDER",
                "research_boundary": research_boundary(),
            }
        )
    return rows


def build_count_check_rows(
    count_check_rows: Iterable[dict[str, Any]],
    *,
    moonshot_head: str,
    moonshot_status_clean: bool,
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for row in count_check_rows:
        rows.append(
            {
                "schema_version": SCHEMA_VERSION,
                "row_type": "moonshot_frozen_universe_count_check",
                "row_key": hashlib.sha256(stable_json(["check", row.get("check_name")]).encode("utf-8")).hexdigest(),
                "check_name": row.get("check_name"),
                "check_pass": row.get("check_pass"),
                "expected": row.get("expected"),
                "observed": row.get("observed"),
                "evidence_path": row.get("evidence_path"),
                "source_handoff_row_id": row.get("frozen_main_handoff_count_check_row_id"),
                "moonshot_snapshot": {
                    "worktree_head": moonshot_head,
                    "status_clean": moonshot_status_clean,
                },
                "main_consumption_action": "COUNT_CHECK_CONFIRMS_SOURCE_PACKET_BOUNDARY",
                "research_boundary": research_boundary(),
            }
        )
    return rows


def classify_consumption_action(artifact_row: dict[str, Any], order_row: dict[str, Any]) -> str:
    checkpoint = artifact_row.get("checkpoint")
    role = str(artifact_row.get("artifact_role") or "")
    if checkpoint == 281 or "ready_action_runtime" in role:
        return "CONSUME_CP281_READY_RUNTIME_RULES_FIRST"
    if role == "implementation_ready_bundle":
        return "CONSUME_CP280_IMPLEMENTATION_READY_BUNDLE"
    if role == "repair_needed_bundle":
        return "PRESERVE_CP280_REPAIR_NEEDED_ROW_OWNERSHIP_FOR_SOURCE_REPAIR"
    if role == "kill_preserve_ledger":
        return "PRESERVE_CP280_KILL_PRESERVE_INTELLIGENCE"
    if role == "frozen_market_timeframe_source_coverage":
        return "CONSUME_CP280_MARKET_TIMEFRAME_SOURCE_COVERAGE"
    if order_row.get("priority_order") is not None:
        return "CONSUME_IN_CP282_PRIORITY_ORDER"
    return "PRESERVE_SOURCE_ARTIFACT_FOR_MAIN_CONSUMPTION"


def research_boundary() -> dict[str, bool | str]:
    return {
        "artifact_scope": "main_side_research_consumption_index",
        "runtime_trading_or_live_broker_effect": False,
        "broker_operation": False,
        "paid_api_or_vendor_call": False,
        "runtime_candidate_use_permitted": False,
        "production_import_path": False,
        "mutates_order_risk_prompt_safety_or_mt5": False,
    }


def summarize_consumption(
    *,
    packet: dict[str, Any],
    artifact_rows: list[dict[str, Any]],
    order_rows: list[dict[str, Any]],
    count_rows: list[dict[str, Any]],
    moonshot_root: Path,
    moonshot_head: str,
    moonshot_status_clean: bool,
) -> dict[str, Any]:
    cp280_counts = packet["cp280_result"].get("counts") or {}
    cp281_counts = packet["cp281_result"].get("counts") or {}
    cp282_counts = packet["cp282_result"].get("counts") or {}
    artifact_counts_by_checkpoint = _counts(row.get("source_checkpoint") for row in artifact_rows)
    return {
        "schema_version": SCHEMA_VERSION,
        "moonshot_root": str(moonshot_root),
        "moonshot_route_relative": str(MOONSHOT_ROUTE_RELATIVE).replace("\\", "/"),
        "moonshot_head": moonshot_head,
        "moonshot_status_clean": moonshot_status_clean,
        "cp280_result_ok": packet["cp280_result"].get("ok") is True,
        "cp281_result_ok": packet["cp281_result"].get("ok") is True,
        "cp282_result_ok": packet["cp282_result"].get("ok") is True,
        "cp282_verifier_ok": packet["cp282_verifier"].get("ok") is True,
        "artifact_rows": len(artifact_rows),
        "artifact_counts_by_checkpoint": artifact_counts_by_checkpoint,
        "cp280_artifact_rows": artifact_counts_by_checkpoint.get("280", 0),
        "cp281_artifact_rows": artifact_counts_by_checkpoint.get("281", 0),
        "consumption_order_rows": len(order_rows),
        "count_check_rows": len(count_rows),
        "count_check_pass_rows": sum(row.get("check_pass") is True for row in count_rows),
        "source_inventory": packet["source_inventory"],
        "cp280_counts": cp280_counts,
        "cp281_counts": cp281_counts,
        "cp282_counts": cp282_counts,
        "key_counts": {
            "cp281_ready_runtime_rule_rows": cp281_counts.get("rule_rows"),
            "cp281_follow_rule_inputs": (cp281_counts.get("action_class_counts") or {}).get("follow_rule"),
            "cp281_avoid_filter_inputs": (cp281_counts.get("action_class_counts") or {}).get("avoid_filter"),
            "cp281_self_test_pass_rows": cp281_counts.get("self_test_pass_rows"),
            "cp280_implementation_ready_rows": cp280_counts.get("implementation_ready_rows"),
            "cp280_repair_needed_rows": cp280_counts.get("repair_needed_rows"),
            "cp280_kill_preserve_rows": cp280_counts.get("kill_preserve_rows"),
            "cp280_coverage_rows": cp280_counts.get("coverage_rows"),
            "cp282_repair_needed_rows_preserved": cp282_counts.get("repair_needed_rows_preserved"),
            "cp282_kill_preserve_rows_preserved": cp282_counts.get("kill_preserve_rows_preserved"),
            "cp282_coverage_rows_preserved": cp282_counts.get("coverage_rows_preserved"),
        },
        "implementation_effect": {
            "main_side_cp280_cp281_cp282_consumption_index_materialized": True,
            "runtime_trading_or_live_broker_effect": False,
            "broker_operation": False,
            "paid_api_or_vendor_call": False,
            "runtime_candidate_use_permitted": False,
            "production_import_path": False,
            "mutates_order_risk_prompt_safety_or_mt5": False,
        },
        "next_required_action": (
            "Consume CP281 461 ready runtime rows into main code/config/test surfaces "
            "or exact parked reasons without sampling."
        ),
    }


def _counts(values: Iterable[Any]) -> dict[str, int]:
    counts: dict[str, int] = {}
    for value in values:
        key = str(value)
        counts[key] = counts.get(key, 0) + 1
    return dict(sorted(counts.items()))
