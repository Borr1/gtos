#!/usr/bin/env python3
"""Build runtime rows for Main Orch24 source-accepted action repair evidence."""

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


ROUTE_DIR = (
    REPO_ROOT
    / "research"
    / "science_program_2026_05"
    / "06_outcome_testing"
    / "gtos_vnext_research_to_runtime_builder"
)
SOURCE_DIR = (
    REPO_ROOT
    / "research"
    / "science_program_2026_05"
    / "06_outcome_testing"
    / "main_orchestrator_24h_full_stack_research_integration_materialization"
)
DATE = "2026-05-18"
WAVE_ID = "WAVE_MAIN_ORCH24_SOURCE_ACCEPTED_ACTION_REPAIR_RUNTIME"
EVIDENCE_FAMILY = "gtos_vnext_main_orch24_source_accepted_action_repair_runtime"
SOURCE_NAME = "gtos_vnext_main_orch24_source_accepted_action_repair_runtime_wave"
OUTPUT_ROWS = (
    ROUTE_DIR
    / f"GTOS_VNEXT_MAIN_ORCH24_SOURCE_ACCEPTED_RUNTIME_ROWS_{DATE}.jsonl"
)
OUTPUT_SUMMARY = (
    ROUTE_DIR
    / f"GTOS_VNEXT_MAIN_ORCH24_SOURCE_ACCEPTED_RUNTIME_SUMMARY_{DATE}.json"
)

ACTION_RECLASS_SOURCE = (
    "MAIN_ORCH24_ACTION_AFTER_SOURCE_ACCEPTED_ACTION_RECLASS_LEDGER_2026-05-17.jsonl"
)
BRANCH_LABEL_SOURCE = (
    "MAIN_ORCH24_ACTION_AFTER_SOURCE_ACCEPTED_BRANCH_LABEL_REPAIR_LEDGER_2026-05-17.jsonl"
)
DEGRADED_REDESIGN_SOURCE = (
    "MAIN_ORCH24_ACTION_AFTER_SOURCE_ACCEPTED_DEGRADED_REDESIGN_LEDGER_2026-05-17.jsonl"
)

SOURCE_ARTIFACTS = (
    (
        "UNIT_009355",
        "build_main_orchestrator_action_after_source_accepted_degraded_redesign_2026_05_17.py",
        "1d8ad2a6059f904b179ac3e9563d8302ab087bbb",
    ),
    (
        "UNIT_009469",
        "build_main_orchestrator_source_accepted_action_reclass_2026_05_17.py",
        "2ff569693f62e3735f3f3e0266356cf037a59e15",
    ),
    (
        "UNIT_009470",
        "build_main_orchestrator_source_accepted_branch_label_repair_2026_05_17.py",
        "41886d14f837c05f54535d8a9df1c2a6840025bf",
    ),
    (
        "UNIT_009566",
        ACTION_RECLASS_SOURCE,
        "4103073a975c5e22e2fac10473f95d3f904404f5",
    ),
    (
        "UNIT_009567",
        "MAIN_ORCH24_ACTION_AFTER_SOURCE_ACCEPTED_ACTION_RECLASS_OUTPUT_MANIFEST_2026-05-17.json",
        "dc01a1f51fb8183f00b376b77cc44e42b855cdf7",
    ),
    (
        "UNIT_009568",
        "MAIN_ORCH24_ACTION_AFTER_SOURCE_ACCEPTED_ACTION_RECLASS_SUMMARY_2026-05-17.json",
        "44a0d4fd8c2660732725b30d1eda895a9d3b6df7",
    ),
    (
        "UNIT_009569",
        "MAIN_ORCH24_ACTION_AFTER_SOURCE_ACCEPTED_ACTION_RECLASS_VERIFICATION_RESULT_2026-05-17.json",
        "6e696c118c6ede334a2f11b3f0ef97113e4c625c",
    ),
    (
        "UNIT_009570",
        BRANCH_LABEL_SOURCE,
        "beb6fd8c825f89daed375d8a28e199d2c34b64e2",
    ),
    (
        "UNIT_009571",
        "MAIN_ORCH24_ACTION_AFTER_SOURCE_ACCEPTED_BRANCH_LABEL_REPAIR_OUTPUT_MANIFEST_2026-05-17.json",
        "0fb6b16729b378a1c96e3ebebfa4d02037f3d090",
    ),
    (
        "UNIT_009572",
        "MAIN_ORCH24_ACTION_AFTER_SOURCE_ACCEPTED_BRANCH_LABEL_REPAIR_SUMMARY_2026-05-17.json",
        "83732257fec035232791c9bb661905aebee0d0f8",
    ),
    (
        "UNIT_009573",
        "MAIN_ORCH24_ACTION_AFTER_SOURCE_ACCEPTED_BRANCH_LABEL_REPAIR_VERIFICATION_RESULT_2026-05-17.json",
        "436b6a5a3f2cf6bc36b9ab217ff5ce84f4ae89f1",
    ),
    (
        "UNIT_009574",
        DEGRADED_REDESIGN_SOURCE,
        "fa685bafa654401a9af834ae3ec34854bc8a989c",
    ),
    (
        "UNIT_009575",
        "MAIN_ORCH24_ACTION_AFTER_SOURCE_ACCEPTED_DEGRADED_REDESIGN_OUTPUT_MANIFEST_2026-05-17.json",
        "ae127139ea225e93ff31cee5e8fc0478d4ab7259",
    ),
    (
        "UNIT_009576",
        "MAIN_ORCH24_ACTION_AFTER_SOURCE_ACCEPTED_DEGRADED_REDESIGN_SUMMARY_2026-05-17.json",
        "e485ca0563ef748dd811676b440e934d0d955ffb",
    ),
    (
        "UNIT_009577",
        "MAIN_ORCH24_ACTION_AFTER_SOURCE_ACCEPTED_DEGRADED_REDESIGN_VERIFICATION_RESULT_2026-05-17.json",
        "f0e252bf3f46756babf367a7e026f7dbcf240ab9",
    ),
    (
        "UNIT_010281",
        "verify_main_orchestrator_action_after_source_accepted_degraded_redesign_2026_05_17.py",
        "801f41022b4a1242b1a71b365a51861b1b157afd",
    ),
    (
        "UNIT_010395",
        "verify_main_orchestrator_source_accepted_action_reclass_2026_05_17.py",
        "9bb0c3b2b775764c8cf459787dc3db4cad85c1ff",
    ),
    (
        "UNIT_010396",
        "verify_main_orchestrator_source_accepted_branch_label_repair_2026_05_17.py",
        "96a4473c8d5062dcbe3412797ba455779ae3ccb1",
    ),
)

ANCHOR_FIELDS = (
    "symbol",
    "source_symbol",
    "market",
    "timeframe",
    "market_timeframe",
    "route_session",
    "route_family",
    "primitive",
    "side",
    "source_component",
    "entry_variant",
    "target_stop_order_class",
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
        if path.is_relative_to(REPO_ROOT):
            return path.relative_to(REPO_ROOT).as_posix()
    except ValueError:
        pass
    return str(path).replace("\\", "/")


def _source_path(name: str) -> Path:
    return SOURCE_DIR / name


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with open(_long_path(path), "rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _sha256_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


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
    return 1


def _metric(
    value: float | int | None,
    *,
    source_field: str,
    count: int = 1,
) -> dict[str, Any] | None:
    if value is None:
        return None
    value = float(value)
    return {
        "sum": round(value, 12),
        "count": count,
        "mean": round(value / count, 12) if count else round(value, 12),
        "positive_rows": 1 if value > 0 else 0,
        "negative_rows": 1 if value < 0 else 0,
        "zero_rows": 1 if value == 0 else 0,
        "match_rows_with_metric": count,
        "source_field": source_field,
        "source_shape": "scalar",
    }


def _candidate_parts(candidate_id: Any) -> tuple[str, str, str]:
    parts = _norm(candidate_id).split("|")
    session = parts[1] if len(parts) >= 2 and parts[1] else "ALL_SESSIONS"
    primitive = parts[2] if len(parts) >= 3 and parts[2] else ""
    horizon = parts[-1] if len(parts) >= 4 and parts[-1].startswith("h") else ""
    return session, primitive, horizon


def _base_scope(
    *,
    symbol: str,
    side: str,
    route_session: str,
    primitive: str,
    source_component: str,
    horizon: str,
) -> dict[str, str]:
    scope = {
        "symbol": symbol,
        "source_symbol": symbol,
        "market": symbol,
        "symbol_family": resolve_vnext_symbol_family(symbol),
        "timeframe": "M15",
        "market_timeframe": "M15",
        "route_session": route_session or "ALL_SESSIONS",
        "route_family": "main_orch24_source_accepted_runtime",
        "primitive": primitive,
        "source_component": source_component,
        "side": side,
        "horizon_id": horizon,
    }
    return {key: value for key, value in scope.items() if value}


def _is_target_row(row: dict[str, Any]) -> bool:
    return any(
        _norm(row.get(key)).upper() not in {"", "NOT_TARGET_ROW"}
        for key in (
            "source_accepted_action_reclass_status",
            "source_accepted_branch_label_repair_status",
            "source_accepted_degraded_redesign_status",
        )
    )


def _behavior(row: dict[str, Any]) -> dict[str, str]:
    branch = _norm(row.get("branch_decision")).upper()
    if _norm(row.get("source_accepted_degraded_redesign_status")).upper() != "NOT_TARGET_ROW":
        return {
            "review_action": "MIXED",
            "source_component": (
                "main_orch24_source_accepted_degraded_redesign_source_acquisition"
            ),
            "source_role": "main_orch24_source_accepted_exact_repair_required",
            "source_group": "main_orch24_source_accepted_exact_repair",
            "system_surface": "execution_adjacent_source_accepted_source_acquisition",
            "action_class": "main_orch24_source_accepted_degraded_redesign_context",
            "r_evidence_class": (
                "MAIN_ORCH24_SOURCE_ACCEPTED_DEGRADED_REDESIGN_EXACT_REPAIR_REQUIRED"
            ),
            "proxy_r_class": "MIXED_PROXY_R",
        }
    if "AFTER_M15_ORDERING_POSITIVE_PROXY" in branch:
        return {
            "review_action": "FOLLOW",
            "source_component": "main_orch24_source_accepted_m15_ordering_follow",
            "source_role": "main_orch24_source_accepted_m15_ordering_follow",
            "source_group": "main_orch24_source_accepted_positive_proxy",
            "system_surface": "execution_adjacent_source_accepted_positive_proxy",
            "action_class": "main_orch24_source_accepted_m15_ordering_follow",
            "r_evidence_class": (
                "MAIN_ORCH24_SOURCE_ACCEPTED_M15_ORDERING_POSITIVE_PROXY"
            ),
            "proxy_r_class": "POSITIVE_PROXY_R",
        }
    return {
        "review_action": "FOLLOW",
        "source_component": "main_orch24_source_accepted_source_cost_proxy_follow",
        "source_role": "main_orch24_source_accepted_source_cost_proxy_follow",
        "source_group": "main_orch24_source_accepted_positive_proxy",
        "system_surface": "execution_adjacent_source_accepted_positive_proxy",
        "action_class": "main_orch24_source_accepted_source_cost_proxy_follow",
        "r_evidence_class": "MAIN_ORCH24_SOURCE_ACCEPTED_SOURCE_COST_POSITIVE_PROXY",
        "proxy_r_class": "POSITIVE_PROXY_R",
    }


def _runtime_row(
    *,
    line_no: int,
    source_path: Path,
    source_sha: str,
    source_row: dict[str, Any],
    behavior: dict[str, str],
    event_scope: dict[str, str],
    metrics: dict[str, dict[str, Any]],
) -> dict[str, Any]:
    row_id = (
        f"main_orch24:source_accepted:{line_no}:"
        f"{_sha256_text(json.dumps(source_row, sort_keys=True))[:16]}"
    )
    runtime = {
        "schema_version": "gtos_vnext_main_orch24_source_accepted_runtime_row_v1",
        "row_type": "gtos_vnext_main_orch24_source_accepted_runtime_row",
        "main_orch24_source_accepted_runtime_row_id": row_id,
        "row_key": row_id,
        "source_name": SOURCE_NAME,
        "evidence_family": EVIDENCE_FAMILY,
        "source_kind": "main_orch24_action_after_source_accepted_repair_row",
        "source_group": behavior["source_group"],
        "source_role": behavior["source_role"],
        "source_component": behavior["source_component"],
        "system_surface": behavior["system_surface"],
        "action_class": behavior["action_class"],
        "review_action": behavior["review_action"],
        "r_evidence_class": behavior["r_evidence_class"],
        "proxy_r_class": behavior["proxy_r_class"],
        "event_scope": event_scope,
        "source_bound": bool(event_scope),
        "candidate_use_allowed_now": behavior["review_action"] == "FOLLOW",
        "runtime_candidate_use_permitted": behavior["review_action"] == "FOLLOW",
        "live_effect": False,
        "broker_operation": False,
        "paid_api_or_vendor_call": False,
        "runtime_trading_or_live_broker_effect": False,
        "runtime_effect_now": "main_orch24_source_accepted_shadow_runtime",
        "batch_wave_id": WAVE_ID,
        "source_artifact": _path_text(source_path),
        "source_file_sha256": source_sha,
        "source_line_no": line_no,
        "source_row_id": source_row.get("row_id"),
        "candidate_id": source_row.get("candidate_id"),
        "source_payload_hash": _sha256_text(json.dumps(source_row, sort_keys=True)),
        "r_metrics": metrics,
        "original_action_class": source_row.get("action_class"),
        "branch_decision": source_row.get("branch_decision"),
        "current_action": source_row.get("current_action"),
        "implementation_decision": source_row.get("implementation_decision"),
        "coverage_status": source_row.get("coverage_status"),
        "data_requirement_state": source_row.get("data_requirement_state"),
        "decision_evidence": source_row.get("decision_evidence"),
        "scoring_boundary": source_row.get("scoring_boundary"),
        "next_action": source_row.get("next_action"),
        "primitive_family": source_row.get("primitive_family"),
        "after_proxy_r": _float(source_row.get("after_proxy_r")),
        "before_proxy_r": _float(source_row.get("before_proxy_r")),
        "source_accepted_action_reclass_status": source_row.get(
            "source_accepted_action_reclass_status"
        ),
        "source_accepted_branch_label_repair_status": source_row.get(
            "source_accepted_branch_label_repair_status"
        ),
        "source_accepted_degraded_redesign_status": source_row.get(
            "source_accepted_degraded_redesign_status"
        ),
    }
    runtime.update(event_scope)
    return {key: value for key, value in runtime.items() if value not in (None, "", {}, [])}


def build_rows() -> list[dict[str, Any]]:
    source_path = _source_path(DEGRADED_REDESIGN_SOURCE)
    source_sha = _sha256_file(source_path)
    runtime_rows: list[dict[str, Any]] = []
    for line_no, row in enumerate(_read_jsonl(source_path), start=1):
        if not _is_target_row(row):
            continue
        behavior = _behavior(row)
        session, candidate_primitive, horizon = _candidate_parts(row.get("candidate_id"))
        primitive = _norm(row.get("primitive_family")) or candidate_primitive
        scope = _base_scope(
            symbol=_norm(row.get("symbol")),
            side=_norm(row.get("side")),
            route_session=session,
            primitive=primitive,
            source_component=behavior["source_component"],
            horizon=horizon,
        )
        proxy = _float(row.get("after_proxy_r"))
        metrics = {
            key: value
            for key, value in {
                "proxy_score": _metric(proxy, source_field="after_proxy_r"),
                "cost_adjusted_simulated_r": _metric(proxy, source_field="after_proxy_r"),
                "effective_n": _metric(1, source_field="source_accepted_target_row"),
            }.items()
            if value is not None
        }
        runtime_rows.append(
            _runtime_row(
                line_no=line_no,
                source_path=source_path,
                source_sha=source_sha,
                source_row=row,
                behavior=behavior,
                event_scope=scope,
                metrics=metrics,
            )
        )
    return runtime_rows


def _counter(rows: list[dict[str, Any]], field: str) -> dict[str, int]:
    return dict(
        sorted(Counter(_norm(row.get(field)) for row in rows if _norm(row.get(field))).items())
    )


def _blank_anchor_counts(rows: list[dict[str, Any]]) -> dict[str, int]:
    return {field: sum(1 for row in rows if not _norm(row.get(field))) for field in ANCHOR_FIELDS}


def _source_artifacts(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    runtime_rows_by_source = Counter(Path(row["source_artifact"]).name for row in rows)
    artifacts: list[dict[str, Any]] = []
    for unit_id, name, git_blob_hash in SOURCE_ARTIFACTS:
        path = _source_path(name)
        role = (
            "primary_runtime_rows"
            if name == DEGRADED_REDESIGN_SOURCE
            else "supporting_source_accepted_repair_evidence"
        )
        artifacts.append(
            {
                "unit_id": unit_id,
                "name": name,
                "path": _path_text(path),
                "hash": git_blob_hash,
                "hash_algorithm": "git_blob",
                "sha256": _sha256_file(path),
                "row_count": _source_row_count(path),
                "runtime_rows_read": int(runtime_rows_by_source.get(name, 0)),
                "source_role": role,
            }
        )
    return artifacts


def build_summary(rows: list[dict[str, Any]]) -> dict[str, Any]:
    artifacts = _source_artifacts(rows)
    coverage = {
        "symbols": _counter(rows, "symbol"),
        "source_symbols": _counter(rows, "source_symbol"),
        "markets": _counter(rows, "market"),
        "timeframes": _counter(rows, "timeframe"),
        "sessions": _counter(rows, "route_session"),
        "route_families": _counter(rows, "route_family"),
        "primitives": _counter(rows, "primitive"),
        "horizons": _counter(rows, "horizon_id"),
        "sides": _counter(rows, "side"),
        "source_components": _counter(rows, "source_component"),
        "action_classes": _counter(rows, "action_class"),
        "source_roles": _counter(rows, "source_role"),
        "source_groups": _counter(rows, "source_group"),
        "system_surfaces": _counter(rows, "system_surface"),
        "entry_variants": _counter(rows, "entry_variant"),
        "target_stop_order_classes": _counter(rows, "target_stop_order_class"),
    }
    proxy_values = [
        float(row["after_proxy_r"])
        for row in rows
        if isinstance(row.get("after_proxy_r"), (int, float))
    ]
    source_acquisition_required_rows = sum(
        1
        for row in rows
        if row.get("r_evidence_class")
        == "MAIN_ORCH24_SOURCE_ACCEPTED_DEGRADED_REDESIGN_EXACT_REPAIR_REQUIRED"
    )
    positive_proxy_rows = sum(1 for value in proxy_values if value > 0)
    return {
        "schema_version": "gtos_vnext_main_orch24_source_accepted_runtime_summary_v1",
        "wave_id": WAVE_ID,
        "evidence_family": EVIDENCE_FAMILY,
        "source_name": SOURCE_NAME,
        "runtime_rows_path": _path_text(OUTPUT_ROWS),
        "runtime_summary_path": _path_text(OUTPUT_SUMMARY),
        "runtime_row_count": len(rows),
        "runtime_rows_with_event_scope": sum(1 for row in rows if row.get("event_scope")),
        "runtime_rows_without_event_scope": sum(1 for row in rows if not row.get("event_scope")),
        "runtime_source_rows_represented": sum(
            int(item["runtime_rows_read"]) for item in artifacts
        ),
        "wave_source_rows_counted": sum(int(item["row_count"]) for item in artifacts),
        "support_rows_represented": sum(
            int(item["row_count"])
            for item in artifacts
            if item["source_role"] != "primary_runtime_rows"
        ),
        "selected_open_unit_count": len(SOURCE_ARTIFACTS),
        "row_count_unknown_unit_count": 0,
        "source_acquisition_required_rows": source_acquisition_required_rows,
        "positive_proxy_rows": positive_proxy_rows,
        "positive_proxy_sum": round(sum(value for value in proxy_values if value > 0), 6),
        "decision_counts": _counter(rows, "review_action"),
        "r_evidence_class_counts": _counter(rows, "r_evidence_class"),
        "action_class_counts": _counter(rows, "action_class"),
        "source_component_counts": _counter(rows, "source_component"),
        "source_role_counts": _counter(rows, "source_role"),
        "source_group_counts": _counter(rows, "source_group"),
        "source_kind_counts": _counter(rows, "source_kind"),
        "system_surface_counts": _counter(rows, "system_surface"),
        "proxy_r_class_counts": _counter(rows, "proxy_r_class"),
        "coverage_counts": coverage,
        "blank_anchor_counts": _blank_anchor_counts(rows),
        "candidate_use_allowed_now_rows": sum(
            1 for row in rows if row.get("candidate_use_allowed_now") is True
        ),
        "runtime_candidate_use_permitted_rows": sum(
            1 for row in rows if row.get("runtime_candidate_use_permitted") is True
        ),
        "live_effect_rows": sum(1 for row in rows if row.get("live_effect") is True),
        "broker_operation_rows": sum(1 for row in rows if row.get("broker_operation") is True),
        "paid_api_or_vendor_call_rows": sum(
            1 for row in rows if row.get("paid_api_or_vendor_call") is True
        ),
        "runtime_trading_or_live_broker_effect_rows": sum(
            1
            for row in rows
            if row.get("runtime_trading_or_live_broker_effect") is True
        ),
        "source_artifacts": artifacts,
    }


def write_outputs(*, check: bool = False) -> int:
    rows = build_rows()
    summary = build_summary(rows)
    rows_payload = "".join(json.dumps(row, sort_keys=True) + "\n" for row in rows)
    summary_payload = json.dumps(summary, indent=2, sort_keys=True) + "\n"

    if check:
        current_rows = OUTPUT_ROWS.read_text(encoding="utf-8") if OUTPUT_ROWS.exists() else ""
        current_summary = (
            OUTPUT_SUMMARY.read_text(encoding="utf-8") if OUTPUT_SUMMARY.exists() else ""
        )
        if current_rows != rows_payload or current_summary != summary_payload:
            print("Generated Main Orch24 source-accepted runtime artifacts are stale.")
            return 1
        print(
            "Main Orch24 source-accepted runtime artifacts are current: "
            f"{len(rows)} rows."
        )
        return 0

    ROUTE_DIR.mkdir(parents=True, exist_ok=True)
    OUTPUT_ROWS.write_text(rows_payload, encoding="utf-8")
    OUTPUT_SUMMARY.write_text(summary_payload, encoding="utf-8")
    print(f"Wrote {OUTPUT_ROWS} ({len(rows)} rows)")
    print(f"Wrote {OUTPUT_SUMMARY}")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="verify outputs are current")
    args = parser.parse_args()
    return write_outputs(check=args.check)


if __name__ == "__main__":
    raise SystemExit(main())
