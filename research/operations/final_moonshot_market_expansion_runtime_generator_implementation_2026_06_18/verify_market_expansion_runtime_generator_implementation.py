#!/usr/bin/env python3
"""Verify the market-expansion runtime-generator implementation route."""

from __future__ import annotations

import json
import sys
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parents[3]
ROUTE = Path(__file__).resolve().parent
SCHEMA_PREFIX = "gtos.final_moonshot.market_expansion_runtime_generator_implementation"

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.components.ultimate_book import admission, execution_packets as EP  # noqa: E402
from src.components.ultimate_book.bridge import DEFAULT_CONFIG  # noqa: E402
from src.components.ultimate_book.sleeves import candidate_registry, market_expansion_d1  # noqa: E402
from src.components.ultimate_book.sleeves.registry import (  # noqa: E402
    CANDIDATE_BUILT,
    MARKET_EXPANSION_BUILT,
    active_specs,
)


def utc_now() -> str:
    return datetime.now(UTC).isoformat()


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def write_json(path: Path, payload: Any) -> None:
    path.write_text(json.dumps(payload, indent=2, sort_keys=True, default=str) + "\n", encoding="utf-8")


def check(name: str, passed: bool, detail: dict[str, Any] | None = None) -> dict[str, Any]:
    return {"name": name, "passed": bool(passed), "detail": detail or {}}


def main() -> int:
    created_at = utc_now()
    result = load_json(ROUTE / "MARKET_EXPANSION_RUNTIME_GENERATOR_IMPLEMENTATION_RESULT.json")
    parity = load_jsonl(ROUTE / "RUNTIME_GENERATOR_PARITY_LEDGER.jsonl")
    detail = load_jsonl(ROUTE / "RUNTIME_GENERATOR_EVENT_PARITY_DETAIL.jsonl")
    timing = load_json(ROUTE / "D1_NEXT_OPEN_TIMING_CONTRACT_PROOF.json")
    broker = load_json(ROUTE / "BROKER_SESSION_SPEC_CAPTURE_MANIFEST.json")
    execution = load_json(ROUTE / "EXECUTION_PACKET_DRY_RUN_PROOF.json")
    zero = load_json(ROUTE / "ZERO_ACTIVE_BEHAVIOR_AUDIT.json")
    replay = load_json(ROUTE / "FULL_GENERATOR_BOOK_REPLAY_PROOF.json")
    saturation = load_json(ROUTE / "SATURATION_AUDIT.json")
    completion = load_json(ROUTE / "COMPLETION_AUDIT.json")
    focused = load_json(ROUTE / "FOCUSED_TEST_RESULT.json")
    decisions = load_jsonl(ROUTE / "IMPLEMENTATION_DECISION_LEDGER.jsonl")

    expansion_names = set(candidate_registry.MARKET_EXPANSION_DEFAULT_OFF_COLLISION_WINNER_NAMES)
    code_tags = set(market_expansion_d1.TAG_TO_RULE)
    runtime_tags = set(MARKET_EXPANSION_BUILT)
    parity_tags = {row["tag"] for row in parity}
    detail_status_counts: dict[str, int] = {}
    for row in detail:
        detail_status_counts[row["status"]] = detail_status_counts.get(row["status"], 0) + 1
    active_default = {spec.tag for spec in active_specs(None)}
    active_candidate = {spec.tag for spec in active_specs(None, include_candidate_book=True)}
    active_empty_expansion = {
        spec.tag
        for spec in active_specs(None, include_market_expansion_book=True, market_expansion_sleeves=[])
    }
    registry_default = set(admission.effective_registry())
    registry_candidate = set(admission.effective_registry(include_candidate_book=True))
    registry_empty_expansion = set(
        admission.effective_registry(include_market_expansion_book=True, market_expansion_sleeves=[])
    )

    checks = [
        check(
            "result_completion_saturation_focused_ok",
            result.get("ok") is True
            and completion.get("ok") is True
            and saturation.get("ok") is True
            and focused.get("ok") is True,
            {
                "result_ok": result.get("ok"),
                "completion_ok": completion.get("ok"),
                "saturation_ok": saturation.get("ok"),
                "focused_ok": focused.get("ok"),
            },
        ),
        check(
            "code_catalog_is_exact_14_and_separate_from_candidate_book",
            len(expansion_names) == len(code_tags) == len(runtime_tags) == 14
            and expansion_names == code_tags == runtime_tags == set(EP.MARKET_EXPANSION_TARGET2_SLEEVES)
            and not (expansion_names & set(CANDIDATE_BUILT)),
            {
                "expansion_names": len(expansion_names),
                "code_tags": len(code_tags),
                "runtime_tags": len(runtime_tags),
                "candidate_overlap": sorted(expansion_names & set(CANDIDATE_BUILT)),
            },
        ),
        check(
            "runtime_parity_all_rows_and_events",
            len(parity) == 14
            and parity_tags == expansion_names
            and all(row.get("all_parity_passed") is True for row in parity)
            and replay.get("generator_book_signal_replay_complete") is True
            and replay.get("total_recomputed_source_events") == replay.get("total_runtime_events") == replay.get("total_matched_events")
            and detail_status_counts == {"matched": replay.get("total_matched_events")},
            {
                "parity_rows": len(parity),
                "parity_pass_count": sum(1 for row in parity if row.get("all_parity_passed") is True),
                "detail_status_counts": detail_status_counts,
                "replay_counts": {
                    "source": replay.get("total_recomputed_source_events"),
                    "runtime": replay.get("total_runtime_events"),
                    "matched": replay.get("total_matched_events"),
                },
            },
        ),
        check(
            "d1_next_open_timing_contract",
            timing.get("runtime_now_preferred") is True
            and timing.get("calendar_plus_one_is_fallback_only") is True
            and timing.get("all_runtime_decision_days_match_source_entry_dates") is True
            and timing.get("weekend_or_holiday_skip_sample_count", 0) > 0,
            {
                "weekend_or_holiday_skip_sample_count": timing.get("weekend_or_holiday_skip_sample_count"),
                "sample": timing.get("weekend_or_holiday_skip_samples", [])[:3],
            },
        ),
        check(
            "bridge_capture_boundary_and_spec_status",
            broker.get("symbol_count") == 14
            and broker.get("account_info_read") is False
            and broker.get("symbol_select_called") is False
            and broker.get("broker_or_order_mutation") is False
            and broker.get("orderflow_used") is False
            and broker.get("symbol_info_captured_count", 0) in {0, 14},
            {
                "bridge_reachable": broker.get("bridge_reachable"),
                "bridge_error": broker.get("bridge_error"),
                "symbol_info_captured_count": broker.get("symbol_info_captured_count"),
                "stop_freeze_present_count": broker.get("stop_freeze_present_count"),
                "explicit_session_table_present_count": broker.get("explicit_session_table_present_count"),
            },
        ),
        check(
            "target2_execution_packets",
            execution.get("row_count") == 14
            and execution.get("target2_packet_ok_count") == 14
            and execution.get("all_target2_packets_ok") is True
            and execution.get("exit_profile_tags_match_selectable") is True,
            {
                "row_count": execution.get("row_count"),
                "target2_packet_ok_count": execution.get("target2_packet_ok_count"),
            },
        ),
        check(
            "zero_active_behavior",
            zero.get("zero_active_behavior_ok") is True
            and not (expansion_names & active_default)
            and not (expansion_names & active_candidate)
            and not (expansion_names & active_empty_expansion)
            and not (expansion_names & registry_default)
            and not (expansion_names & registry_candidate)
            and not (expansion_names & registry_empty_expansion)
            and DEFAULT_CONFIG["ultimate_book_include_market_expansion_book"] is False
            and result.get("activation_weight_now") == 0.0
            and result.get("live_authority") is False
            and result.get("deployment_ready") is False,
            {
                "zero_active_behavior_ok": zero.get("zero_active_behavior_ok"),
                "default_spec_overlap": sorted(expansion_names & active_default),
                "candidate_spec_overlap": sorted(expansion_names & active_candidate),
                "default_registry_overlap": sorted(expansion_names & registry_default),
                "candidate_registry_overlap": sorted(expansion_names & registry_candidate),
            },
        ),
        check(
            "forbidden_surfaces_and_decision_boundary",
            result.get("decision") == "MARKET_EXPANSION_RUNTIME_GENERATOR_IMPLEMENTED_DEFAULT_OFF_NOT_LIVE_AUTHORITY"
            and result.get("account_info_read") is False
            and result.get("orderflow_used") is False
            and result.get("broker_or_order_mutation") is False
            and result.get("config_or_live_activation_changed") is False
            and result.get("vps_process_touched") is False
            and completion.get("forbidden_surfaces_touched") == []
            and len(decisions) == 1,
            {
                "decision": result.get("decision"),
                "runtime_effect": result.get("runtime_effect"),
                "completion_forbidden_surfaces": completion.get("forbidden_surfaces_touched"),
            },
        ),
    ]
    ok = all(row["passed"] for row in checks)
    payload = {
        "schema": f"{SCHEMA_PREFIX}.verifier_result.v1",
        "created_at_utc": created_at,
        "ok": ok,
        "issue_count": sum(1 for row in checks if not row["passed"]),
        "checks": checks,
    }
    write_json(ROUTE / "MARKET_EXPANSION_RUNTIME_GENERATOR_IMPLEMENTATION_VERIFIER_RESULT.json", payload)
    print(json.dumps(payload, indent=2, sort_keys=True))
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
