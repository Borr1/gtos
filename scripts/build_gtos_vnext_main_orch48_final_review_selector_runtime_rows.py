#!/usr/bin/env python3
"""Build MAIN_ORCH48 final-review selector runtime rows."""

from __future__ import annotations

import os
import argparse
import hashlib
import json
import sys
from collections import Counter
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from src.components.gtos_vnext_runtime import resolve_vnext_symbol_family


SOURCE_DIR = (
    REPO_ROOT
    / "research"
    / "science_program_2026_05"
    / "06_outcome_testing"
    / "main_orchestrator_24h_full_stack_research_integration_materialization"
)
OUTPUT_DIR = (
    REPO_ROOT
    / "research"
    / "science_program_2026_05"
    / "06_outcome_testing"
    / "gtos_vnext_research_to_runtime_builder"
)

DATE = "2026-05-18"
WAVE_ID = "WAVE_MAIN_ORCH48_FINAL_REVIEW_SELECTOR_RUNTIME"
EVIDENCE_FAMILY = "gtos_vnext_main_orch48_final_review_selector_runtime"
SOURCE_NAME = "gtos_vnext_main_orch48_final_review_selector_runtime_wave"
RUNTIME_SURFACE = "main_orch48_final_review_selector_runtime"

OUTPUT_ROWS = (
    OUTPUT_DIR
    / f"GTOS_VNEXT_MAIN_ORCH48_FINAL_REVIEW_SELECTOR_RUNTIME_ROWS_{DATE}.jsonl"
)
OUTPUT_SUMMARY = (
    OUTPUT_DIR
    / f"GTOS_VNEXT_MAIN_ORCH48_FINAL_REVIEW_SELECTOR_RUNTIME_SUMMARY_{DATE}.json"
)

LEDGER_SOURCES = (
    (
        "final_review_adj_emitter_contract",
        "MAIN_ORCH48_FINAL_REVIEW_ADJ_EMITTER_CONTRACT_LEDGER_2026-05-18.jsonl",
    ),
    (
        "final_review_adj_registry_score",
        "MAIN_ORCH48_FINAL_REVIEW_ADJ_REGISTRY_SCORE_LEDGER_2026-05-18.jsonl",
    ),
    (
        "final_review_adj_source_priority",
        "MAIN_ORCH48_FINAL_REVIEW_ADJ_SOURCE_PRIORITY_LEDGER_2026-05-18.jsonl",
    ),
)

SELECTED_SOURCE_ARTIFACTS = (
    "MAIN_ORCH48_FINAL_REVIEW_ADJ_EMITTER_CONTRACT_LEDGER_2026-05-18.jsonl",
    "MAIN_ORCH48_FINAL_REVIEW_ADJ_EMITTER_CONTRACT_OUTPUT_MANIFEST_2026-05-18.json",
    "MAIN_ORCH48_FINAL_REVIEW_ADJ_EMITTER_CONTRACT_SUMMARY_2026-05-18.json",
    "MAIN_ORCH48_FINAL_REVIEW_ADJ_EMITTER_CONTRACT_VERIFY_RESULT_2026-05-18.json",
    "MAIN_ORCH48_FINAL_REVIEW_ADJ_REGISTRY_SCORE_LEDGER_2026-05-18.jsonl",
    "MAIN_ORCH48_FINAL_REVIEW_ADJ_REGISTRY_SCORE_OUTPUT_MANIFEST_2026-05-18.json",
    "MAIN_ORCH48_FINAL_REVIEW_ADJ_REGISTRY_SCORE_SUMMARY_2026-05-18.json",
    "MAIN_ORCH48_FINAL_REVIEW_ADJ_REGISTRY_SCORE_VERIFY_RESULT_2026-05-18.json",
    "MAIN_ORCH48_FINAL_REVIEW_ADJ_SOURCE_PRIORITY_LEDGER_2026-05-18.jsonl",
    "MAIN_ORCH48_FINAL_REVIEW_ADJ_SOURCE_PRIORITY_OUTPUT_MANIFEST_2026-05-18.json",
    "MAIN_ORCH48_FINAL_REVIEW_ADJ_SOURCE_PRIORITY_SUMMARY_2026-05-18.json",
    "MAIN_ORCH48_FINAL_REVIEW_ADJ_SOURCE_PRIORITY_VERIFY_RESULT_2026-05-18.json",
)

ANCHOR_FIELDS = (
    "symbol",
    "source_symbol",
    "market",
    "symbol_family",
    "market_timeframe",
    "timeframe",
    "horizon_id",
    "route_session",
    "route_family",
    "side",
    "source_component",
    "source_role",
    "entry_variant",
    "target_stop_order_class",
    "r_evidence_class",
)


def _norm(value: Any) -> str:
    if value is None:
        return ""
    text = str(value).strip()
    return "" if text.casefold() in {"none", "null", "nan"} else text


def _float(value: Any) -> float | None:
    if value in (None, ""):
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _long_path(path: Path) -> str:
    text = str(path.resolve())
    if os.name == "nt" and len(text) >= 240 and not text.startswith("\\\\?\\"):
        return "\\\\?\\" + text
    return text


def _path_text(path: Path) -> str:
    try:
        return path.resolve().relative_to(REPO_ROOT).as_posix()
    except ValueError:
        return str(path).replace("\\", "/")


def _source_path(name: str) -> Path:
    return SOURCE_DIR / name


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with open(_long_path(path), "rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _git_blob_sha1(path: Path) -> str:
    data = path.read_bytes()
    return hashlib.sha1(
        b"blob " + str(len(data)).encode("ascii") + b"\0" + data
    ).hexdigest()


def _sha256_payload(payload: Any) -> str:
    return hashlib.sha256(
        json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()


def _read_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    with open(_long_path(path), "r", encoding="utf-8-sig", newline="") as handle:
        for line in handle:
            if not line.strip():
                continue
            payload = json.loads(line)
            if isinstance(payload, dict):
                rows.append(payload)
    return rows


def _source_row_count(path: Path) -> int:
    if path.suffix.casefold() == ".jsonl":
        return len(_read_jsonl(path))
    if path.suffix.casefold() == ".json":
        return 1
    with open(_long_path(path), "r", encoding="utf-8", errors="ignore") as handle:
        return sum(1 for line in handle if line.strip())


def _metric(value: float | int | None, *, source_field: str) -> dict[str, Any] | None:
    if value is None:
        return None
    value = float(value)
    return {
        "sum": round(value, 12),
        "count": 1,
        "mean": round(value, 12),
        "positive_rows": 1 if value > 0 else 0,
        "negative_rows": 1 if value < 0 else 0,
        "zero_rows": 1 if value == 0 else 0,
        "match_rows_with_metric": 1,
        "source_field": source_field,
        "source_shape": "scalar",
    }


def _status_values(row: dict[str, Any]) -> list[str]:
    values: list[str] = []
    for field in (
        "final_review_registry_score_status",
        "final_review_source_capture_class",
        "emitter_contract_status",
        "expected_candidate_final_review_status",
        "source_capture_priority_status",
    ):
        value = _norm(row.get(field)).upper()
        if value:
            values.append(value)
    return values


def _behavior(row: dict[str, Any]) -> dict[str, Any]:
    statuses = _status_values(row)
    joined = " ".join(statuses)
    capacity_blocked = bool(row.get("expected_candidate_capacity_blocked"))
    redesign_only = (
        capacity_blocked
        or "REDESIGN_BLOCKED" in joined
        or "REDESIGN_ONLY" in joined
        or "CAPACITY_BLOCKED_REDESIGN" in joined
    )
    mixed_redesign = (
        not redesign_only
        and ("WITH_REDESIGN" in joined or "REDESIGN_SUBSET" in joined)
    )
    if redesign_only:
        return {
            "decision": "AVOID",
            "review_action": "AVOID_FINAL_REVIEW_CAPACITY_BLOCK",
            "source_group": "main_orch48_final_review_capacity_blocked_redesign_avoid",
            "source_role": "main_orch48_final_review_capacity_redesign_guard",
            "system_surface": "main_orch48_final_review_selector_redesign_guard",
            "action_class": "main_orch48_final_review_capacity_blocked_avoid_filter",
            "r_evidence_class": (
                "MAIN_ORCH48_FINAL_REVIEW_CAPACITY_BLOCKED_REDESIGN_AVOID_FILTER"
            ),
            "proxy_r_class": "NEGATIVE_PROXY_R",
        }
    if mixed_redesign:
        return {
            "decision": "MIXED",
            "review_action": "MIXED_FINAL_REVIEW_REDESIGN_CONTEXT",
            "source_group": "main_orch48_final_review_implement_ready_with_redesign_context",
            "source_role": "main_orch48_final_review_implement_ready_redesign_context",
            "system_surface": "main_orch48_final_review_selector_redesign_context",
            "action_class": "main_orch48_final_review_mixed_redesign_context",
            "r_evidence_class": (
                "MAIN_ORCH48_FINAL_REVIEW_IMPLEMENT_READY_WITH_REDESIGN_CONTEXT"
            ),
            "proxy_r_class": "MIXED_PROXY_R",
        }
    return {
        "decision": "FOLLOW",
        "review_action": "FOLLOW_DEFAULT_OFF_FINAL_REVIEW_SELECTOR_PRESSURE",
        "source_group": "main_orch48_final_review_default_off_selector_follow",
        "source_role": "main_orch48_final_review_default_off_selector_follow",
        "system_surface": "main_orch48_final_review_selector_default_off_follow",
        "action_class": "main_orch48_final_review_default_off_follow_pressure",
        "r_evidence_class": (
            "MAIN_ORCH48_FINAL_REVIEW_DEFAULT_OFF_IMPLEMENT_READY_FOLLOW_PRESSURE"
        ),
        "proxy_r_class": "POSITIVE_PROXY_R",
    }


def _scope(row: dict[str, Any], behavior: dict[str, Any]) -> dict[str, str]:
    symbol = _norm(row.get("symbol")) or _norm(row.get("source_symbol"))
    source_symbol = _norm(row.get("source_symbol")) or symbol
    timeframe = _norm(row.get("market_timeframe")) or _norm(row.get("timeframe"))
    side = _norm(row.get("selected_side")) or _norm(row.get("side")) or "ALL_SIDES"
    source_component = _norm(row.get("source_component")) or "default_off_application"
    source_role = behavior["source_role"]
    symbol_family = resolve_vnext_symbol_family(symbol) if symbol else ""
    scope = {
        "symbol": symbol,
        "source_symbol": source_symbol,
        "market": symbol,
        "symbol_family": symbol_family or symbol,
        "market_timeframe": timeframe,
        "timeframe": timeframe,
        "horizon_id": _norm(row.get("horizon_id")),
        "route_session": _norm(row.get("route_session")) or "ALL_SESSIONS",
        "route_family": "main_orch48_final_review_selector",
        "side": side,
        "source_component": source_component,
        "source_role": source_role,
        "entry_variant": _norm(row.get("event_emitter_surface"))
        or _norm(row.get("event_adapter_surface"))
        or "main_orch48_final_review_selector",
        "target_stop_order_class": behavior["r_evidence_class"],
        "r_evidence_class": behavior["r_evidence_class"],
    }
    return {key: value for key, value in scope.items() if value}


def _source_rows_represented(row: dict[str, Any]) -> int:
    _ = row
    return 1


def _r_metrics(row: dict[str, Any]) -> dict[str, dict[str, Any]]:
    metrics = {
        key: value
        for key, value in {
            "proxy_score": _metric(
                _float(row.get("average_selected_intrabar_cost_adjusted_simulated_r_mean_reference")),
                source_field="average_selected_intrabar_cost_adjusted_simulated_r_mean_reference",
            ),
            "cost_adjusted_simulated_r": _metric(
                _float(row.get("average_selected_intrabar_cost_adjusted_simulated_r_mean_reference")),
                source_field="average_selected_intrabar_cost_adjusted_simulated_r_mean_reference",
            ),
            "effective_n": _metric(
                _float(row.get("implementation_ready_candidate_rows"))
                or _float(row.get("registry_match_rows"))
                or _float(row.get("candidate_rows")),
                source_field="implementation_ready_or_registry_match_rows",
            ),
        }.items()
        if value is not None
    }
    return metrics


def _source_row_id(row: dict[str, Any], source_label: str, line_no: int) -> str:
    for field in (
        "emitter_contract_row_id",
        "event_row_id",
        "source_capture_priority_row_id",
        "expected_candidate_row_id",
    ):
        value = _norm(row.get(field))
        if value:
            return value
    return f"{source_label}:{line_no}"


def _runtime_row(
    *,
    source_label: str,
    source_path: Path,
    source_sha: str,
    line_no: int,
    row: dict[str, Any],
) -> dict[str, Any]:
    behavior = _behavior(row)
    scope = _scope(row, behavior)
    row_hash = _sha256_payload(row)
    source_rows_represented = _source_rows_represented(row)
    runtime = {
        "schema_version": "gtos_vnext_main_orch48_final_review_selector_runtime_row_v1",
        "row_type": "gtos_vnext_main_orch48_final_review_selector_runtime_row",
        "main_orch48_final_review_selector_runtime_row_id": (
            f"main_orch48_final_review_selector:{source_label}:{line_no}:{row_hash[:16]}"
        ),
        "row_key": f"main_orch48_final_review_selector:{source_label}:{line_no}:{row_hash[:16]}",
        "source_name": SOURCE_NAME,
        "evidence_family": EVIDENCE_FAMILY,
        "batch_wave_id": WAVE_ID,
        "source_artifact": _path_text(source_path),
        "source_file_sha256": source_sha,
        "source_line_no": line_no,
        "source_payload_hash": row_hash,
        "source_label": source_label,
        "source_row_id": _source_row_id(row, source_label, line_no),
        "source_group": behavior["source_group"],
        "source_role": behavior["source_role"],
        "source_component": scope["source_component"],
        "system_surface": behavior["system_surface"],
        "action_class": behavior["action_class"],
        "review_action": behavior["review_action"],
        "decision": behavior["decision"],
        "r_evidence_class": behavior["r_evidence_class"],
        "proxy_r_class": behavior["proxy_r_class"],
        "event_scope": scope,
        "source_rows_represented": source_rows_represented,
        "source_bound": bool(scope.get("source_component")),
        "candidate_use_allowed_now": False,
        "runtime_candidate_use_permitted": False,
        "fresh_moonshot_cp_evidence_override_allowed": True,
        "legacy_cannot_override_fresher_cp280_cp281_cp282": True,
        "live_effect": False,
        "broker_operation": False,
        "paid_api_or_vendor_call": False,
        "runtime_trading_or_live_broker_effect": False,
        "runtime_effect_now": "main_orch48_final_review_selector_shadow_runtime",
        "source_acquisition_required": False,
        "replay_shadow_activation_path": (
            "vnext_artifact_loader_pre_ai_post_l2_route_risk_shadow_logs"
        ),
        "original_final_review_registry_score_status": row.get(
            "final_review_registry_score_status"
        ),
        "expected_candidate_final_review_status": row.get(
            "expected_candidate_final_review_status"
        ),
        "final_review_source_capture_class": row.get("final_review_source_capture_class"),
        "emitter_contract_status": row.get("emitter_contract_status"),
        "source_capture_priority_status": row.get("source_capture_priority_status"),
        "candidate_rows": row.get("candidate_rows"),
        "registry_match_rows": row.get("registry_match_rows"),
        "event_registry_match_rows": row.get("event_registry_match_rows"),
        "implementation_ready_candidate_rows": row.get(
            "implementation_ready_candidate_rows"
        ),
        "capacity_blocked_candidate_rows": row.get("capacity_blocked_candidate_rows"),
        "expected_candidate_capacity_blocked": row.get(
            "expected_candidate_capacity_blocked"
        ),
        "required_event_field_count": row.get("required_event_field_count"),
        "r_metrics": _r_metrics(row),
    }
    runtime.update(scope)
    return {key: value for key, value in runtime.items() if value not in (None, "", {}, [])}


def build_rows() -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for source_label, filename in LEDGER_SOURCES:
        path = _source_path(filename)
        source_sha = _sha256_file(path)
        for line_no, row in enumerate(_read_jsonl(path), start=1):
            rows.append(
                _runtime_row(
                    source_label=source_label,
                    source_path=path,
                    source_sha=source_sha,
                    line_no=line_no,
                    row=row,
                )
            )
    return rows


def _coverage_counts(rows: list[dict[str, Any]]) -> dict[str, dict[str, int]]:
    return {
        "symbols": dict(Counter(row.get("symbol") for row in rows if row.get("symbol"))),
        "source_symbols": dict(Counter(row.get("source_symbol") for row in rows if row.get("source_symbol"))),
        "markets": dict(Counter(row.get("market") for row in rows if row.get("market"))),
        "symbol_families": dict(Counter(row.get("symbol_family") for row in rows if row.get("symbol_family"))),
        "timeframes": dict(Counter(row.get("timeframe") for row in rows if row.get("timeframe"))),
        "sessions": dict(Counter(row.get("route_session") for row in rows if row.get("route_session"))),
        "sides": dict(Counter(row.get("side") for row in rows if row.get("side"))),
        "horizon_ids": dict(Counter(row.get("horizon_id") for row in rows if row.get("horizon_id"))),
        "entry_variants": dict(Counter(row.get("entry_variant") for row in rows if row.get("entry_variant"))),
        "target_stop_order_classes": dict(
            Counter(row.get("target_stop_order_class") for row in rows if row.get("target_stop_order_class"))
        ),
    }


def _blank_anchor_counts(rows: list[dict[str, Any]]) -> dict[str, int]:
    return {
        field: sum(1 for row in rows if not _norm(row.get(field)))
        for field in ANCHOR_FIELDS
    }


def build_summary(rows: list[dict[str, Any]]) -> dict[str, Any]:
    selected_paths = [_source_path(name) for name in SELECTED_SOURCE_ARTIFACTS]
    source_artifacts = [
        {
            "path": _path_text(path),
            "name": path.name,
            "hash": _git_blob_sha1(path),
            "hash_algorithm": "git_blob",
            "row_count": _source_row_count(path),
            "source_batch_wave_id": WAVE_ID,
        }
        for path in selected_paths
    ]
    decisions = Counter(row["decision"] for row in rows)
    return {
        "schema_version": "gtos_vnext_main_orch48_final_review_selector_runtime_summary_v1",
        "wave_id": WAVE_ID,
        "evidence_family": EVIDENCE_FAMILY,
        "runtime_surface": RUNTIME_SURFACE,
        "runtime_row_count": len(rows),
        "runtime_source_rows_represented": sum(
            int(row.get("source_rows_represented") or 1) for row in rows
        ),
        "wave_source_rows_counted": sum(item["row_count"] for item in source_artifacts),
        "selected_open_unit_count": len(source_artifacts),
        "row_count_unknown_unit_count": 0,
        "source_artifacts": source_artifacts,
        "source_rows_by_label": dict(Counter(row["source_label"] for row in rows)),
        "decision_counts": dict(decisions),
        "r_evidence_class_counts": dict(Counter(row["r_evidence_class"] for row in rows)),
        "proxy_r_class_counts": dict(Counter(row["proxy_r_class"] for row in rows)),
        "source_component_counts": dict(Counter(row["source_component"] for row in rows)),
        "source_role_counts": dict(Counter(row["source_role"] for row in rows)),
        "source_group_counts": dict(Counter(row["source_group"] for row in rows)),
        "final_review_registry_score_status_counts": dict(
            Counter(
                row.get("original_final_review_registry_score_status", "MISSING")
                for row in rows
            )
        ),
        "expected_candidate_final_review_status_counts": dict(
            Counter(
                row.get("expected_candidate_final_review_status", "MISSING")
                for row in rows
            )
        ),
        "final_review_source_capture_class_counts": dict(
            Counter(row.get("final_review_source_capture_class", "MISSING") for row in rows)
        ),
        "emitter_contract_status_counts": dict(
            Counter(row.get("emitter_contract_status", "MISSING") for row in rows)
        ),
        "source_capture_priority_status_counts": dict(
            Counter(row.get("source_capture_priority_status", "MISSING") for row in rows)
        ),
        "implementation_ready_rows": decisions["FOLLOW"],
        "capacity_blocked_or_redesign_rows": decisions["AVOID"],
        "mixed_redesign_context_rows": decisions["MIXED"],
        "runtime_candidate_use_permitted_rows": sum(
            1 for row in rows if row.get("runtime_candidate_use_permitted")
        ),
        "candidate_use_allowed_now_rows": sum(
            1 for row in rows if row.get("candidate_use_allowed_now")
        ),
        "source_acquisition_required_rows": sum(
            1 for row in rows if row.get("source_acquisition_required")
        ),
        "runtime_trading_or_live_broker_effect_rows": 0,
        "broker_operation_rows": 0,
        "paid_api_or_vendor_call_rows": 0,
        "coverage_counts": _coverage_counts(rows),
        "blank_anchor_counts": _blank_anchor_counts(rows),
    }


def write_outputs() -> tuple[list[dict[str, Any]], dict[str, Any]]:
    rows = build_rows()
    summary = build_summary(rows)
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    with OUTPUT_ROWS.open("w", encoding="utf-8", newline="\n") as handle:
        for row in rows:
            handle.write(json.dumps(row, sort_keys=True, separators=(",", ":")) + "\n")
    OUTPUT_SUMMARY.write_text(
        json.dumps(summary, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return rows, summary


def _current_text(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except OSError:
        return ""


def check_outputs() -> tuple[bool, str]:
    rows = build_rows()
    summary = build_summary(rows)
    expected_rows = "".join(
        json.dumps(row, sort_keys=True, separators=(",", ":")) + "\n"
        for row in rows
    )
    expected_summary = json.dumps(summary, indent=2, sort_keys=True) + "\n"
    if _current_text(OUTPUT_ROWS) != expected_rows:
        return False, f"{OUTPUT_ROWS} is stale or missing"
    if _current_text(OUTPUT_SUMMARY) != expected_summary:
        return False, f"{OUTPUT_SUMMARY} is stale or missing"
    return True, f"MAIN_ORCH48 final-review selector runtime outputs are current: {len(rows)} rows"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="Verify generated outputs are current")
    args = parser.parse_args()
    if args.check:
        ok, message = check_outputs()
        print(message)
        return 0 if ok else 1
    rows, summary = write_outputs()
    print(
        json.dumps(
            {
                "blank_anchor_counts": summary["blank_anchor_counts"],
                "decision_counts": summary["decision_counts"],
                "runtime_rows": str(OUTPUT_ROWS),
                "rows": len(rows),
                "summary": str(OUTPUT_SUMMARY),
            },
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
