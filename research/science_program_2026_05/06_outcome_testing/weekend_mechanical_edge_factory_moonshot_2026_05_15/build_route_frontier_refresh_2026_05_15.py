#!/usr/bin/env python3
"""Refresh weekend moonshot route/frontier status.

This script summarizes the route families already touched in the first sprint
and keeps next-route selection tied to explicit evidence boundaries. It does
not validate edge, performance, live-readiness, or promotion.
"""

from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any


ROUTE_DIR = Path(__file__).resolve().parent
STAMP = "2026-05-15"
ROUTE_ID = "WEEKEND_MECHANICAL_EDGE_FACTORY_ABSOLUTE_NORTH_STAR_60H"

RESULT_PATH = ROUTE_DIR / f"ROUTE_FRONTIER_REFRESH_RESULT_{STAMP}.json"
STATUS_LEDGER = ROUTE_DIR / f"ROUTE_FAMILY_STATUS_LEDGER_{STAMP}.jsonl"
NEXT_ROUTE_QUEUE = ROUTE_DIR / f"NEXT_ROUTE_QUEUE_{STAMP}.jsonl"
SUMMARY_PATH = ROUTE_DIR / f"ROUTE_FRONTIER_REFRESH_SUMMARY_{STAMP}.md"

SAFE_FLAGS = {
    "NO_PROMOTION_VERDICT": True,
    "validation_safe": False,
    "outcome_review_opened": False,
    "live_effect": False,
}


def read_json(name: str) -> dict[str, Any]:
    path = ROUTE_DIR / name
    return json.loads(path.read_text(encoding="utf-8"))


def read_json_optional(name: str) -> dict[str, Any] | None:
    path = ROUTE_DIR / name
    if not path.exists():
        return None
    return json.loads(path.read_text(encoding="utf-8"))


def assert_safe(name: str, payload: dict[str, Any]) -> None:
    flags = payload.get("safe_flags") or {}
    if flags != SAFE_FLAGS:
        raise AssertionError(f"{name} safe flags are not closed: {flags}")


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    with path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, sort_keys=True) + "\n")


def main() -> int:
    generated_utc = datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")

    source = read_json(f"DATA_SOURCE_INVENTORY_PARENT_{STAMP}.json")
    shadow = read_json(f"PARENT_SHADOW_MECHANICAL_EDGE_FACTORY_RESULT_{STAMP}.json")
    nofill = read_json(f"NOFILL_ENTRY_GEOMETRY_DESIGN_RESULT_{STAMP}.json")
    ohlc = read_json(f"HISTORICAL_OHLC_GTOS_REPLAY_CONTRACT_RESULT_{STAMP}.json")
    haz001 = read_json(f"HAZ001_READY8_INTEGRATION_PACKET_RESULT_{STAMP}.json")
    verifier = read_json(f"WEEKEND_MOONSHOT_INITIAL_VERIFICATION_RESULT_{STAMP}.json")
    tick_source = read_json_optional(f"TICK_SIERRA_SOURCE_CONTRACT_RESULT_{STAMP}.json")
    tick_route_c = read_json_optional(f"TICK_M15_ROUTE_C_SYNTHESIS_RESULT_{STAMP}.json")

    for name, payload in [
        ("DATA_SOURCE_INVENTORY_PARENT", source),
        ("PARENT_SHADOW_MECHANICAL_EDGE_FACTORY_RESULT", shadow),
        ("NOFILL_ENTRY_GEOMETRY_DESIGN_RESULT", nofill),
        ("HISTORICAL_OHLC_GTOS_REPLAY_CONTRACT_RESULT", ohlc),
        ("HAZ001_READY8_INTEGRATION_PACKET_RESULT", haz001),
    ]:
        assert_safe(name, payload)
    if tick_source is not None:
        assert_safe("TICK_SIERRA_SOURCE_CONTRACT_RESULT", tick_source)
    if tick_route_c is not None:
        assert_safe("TICK_M15_ROUTE_C_SYNTHESIS_RESULT", tick_route_c)

    family_totals = source.get("family_totals", {})
    family_bytes = source.get("family_bytes", {})
    shadow_counts = shadow["counts"]
    nofill_counts = nofill["counts"]
    ohlc_counts = ohlc["counts"]
    haz001_counts = haz001["counts"]

    tick_route_counts = tick_route_c["counts"] if tick_route_c else {}
    tick_source_counts = tick_source["counts"] if tick_source else {}
    tick_route_status = (
        "DEVELOPMENT_RESIDUAL_QUEUE_DONE"
        if tick_route_c
        else "NEXT_ROUTE_CANDIDATE"
    )
    tick_route_boundary = (
        tick_route_c["claim_boundary"]
        if tick_route_c
        else "Only source availability has been established; no tick/SCID orderflow primitive is scored in this sprint yet."
    )
    tick_route_next_gate = (
        tick_route_c["next_required_gate"]
        if tick_route_c
        else "Build source-contracted primitive factory with no broker/API calls and with duplicate/time/session controls."
    )

    status_rows = [
        {
            "route_family_id": "source_truth_and_inventory",
            "frontier_id": "FRONTIER-0001",
            "status": "FOUNDATION_DONE",
            "evidence_class": "READ_ONLY_SOURCE_INVENTORY",
            "counts": {
                "file_count_total": sum(family_totals.values()),
                "tick_data_files": family_totals.get("tick_data", 0),
                "sierra_scid_files": family_totals.get("sierra_scid", 0),
                "shadow_log_files": family_totals.get("shadow_log", 0),
                "research_artifact_files": family_totals.get("research_artifact", 0),
            },
            "bytes": {
                "tick_data": family_bytes.get("tick_data", 0),
                "sierra_scid": family_bytes.get("sierra_scid", 0),
                "shadow_log": family_bytes.get("shadow_log", 0),
            },
            "boundary": "Inventory only; large/binary market data still requires route-specific source contracts and parsers.",
            "next_gate": "Use targeted source contracts before tick/SCID extraction.",
            "safe_flags": SAFE_FLAGS,
        },
        {
            "route_family_id": "shadow_strategy_challenger_ecology",
            "frontier_id": "FRONTIER-0003",
            "status": "DESCRIPTIVE_SCREEN_DONE",
            "evidence_class": shadow["evidence_class"],
            "counts": {
                "strategy_rollup_rows": shadow_counts["strategy_rollup_rows"],
                "path_descriptor_rows": shadow_counts["path_descriptor_rows"],
                "failure_intelligence_rows": shadow_counts["failure_intelligence_rows"],
                "hypothesis_rows": shadow_counts["hypothesis_rows"],
            },
            "boundary": shadow["claim_boundary"],
            "next_gate": "Terminal/unresolved separation plus duplicate-effective-N before any old-vs-new comparison.",
            "safe_flags": SAFE_FLAGS,
        },
        {
            "route_family_id": "nofill_execution_geometry",
            "frontier_id": "FRONTIER-0004",
            "status": "DESIGN_PACKET_DONE",
            "evidence_class": nofill["evidence_class"],
            "counts": {
                "nofill_tp_area_rows": nofill_counts["nofill_tp_area_rows"],
                "nofill_group_rows": nofill_counts["nofill_group_rows"],
                "branch_spec_rows": nofill_counts["branch_spec_rows"],
                "capture_requirement_rows": nofill_counts["capture_requirement_rows"],
            },
            "boundary": nofill["claim_boundary"],
            "next_gate": "Decision-time bid/ask, candidate geometry, ordering, cost, and lifecycle capture before strategy projection.",
            "safe_flags": SAFE_FLAGS,
        },
        {
            "route_family_id": "historical_ohlc_route_a",
            "frontier_id": "FRONTIER-0002",
            "status": "FROZEN_REPLAY_CONTRACTS_READY",
            "evidence_class": ohlc["evidence_class"],
            "counts": {
                "contract_rows": ohlc_counts["contract_rows"],
                "cluster_binding_rows": ohlc_counts["cluster_binding_rows"],
                "blocker_rows": ohlc_counts["blocker_rows"],
            },
            "boundary": ohlc["claim_boundary"],
            "open_blockers": ohlc["open_blockers"],
            "next_gate": "Future/sealed holdout plus entry/cost/fillability model before any strategy result.",
            "safe_flags": SAFE_FLAGS,
        },
        {
            "route_family_id": "haz001_ready8_route_b",
            "frontier_id": "FRONTIER-0003",
            "status": "RETEST_DESIGN_ONLY_ADV_RESIDUAL_ZERO",
            "evidence_class": haz001["evidence_class"],
            "counts": {
                "source_binding_rows": haz001_counts["source_binding_rows"],
                "branch_queue_rows": haz001_counts["branch_queue_rows"],
                "blocker_rows": haz001_counts["blocker_rows"],
            },
            "boundary": haz001["claim_boundary"],
            "open_blockers": haz001["open_blockers"],
            "next_gate": "Do not open target result review unless future/sealed packet exists; ADV overlay currently preserves zero HAZ001 residual.",
            "safe_flags": SAFE_FLAGS,
        },
        {
            "route_family_id": "tick_sierra_orderflow_route_c",
            "frontier_id": "FRONTIER-0002",
            "status": tick_route_status,
            "evidence_class": tick_route_c["evidence_class"] if tick_route_c else "SOURCE_AVAILABLE_NO_PRIMITIVE_SCREEN_YET",
            "counts": {
                "tick_data_files": tick_source_counts.get("tick_parquet_files", family_totals.get("tick_data", 0)),
                "tick_rows_total": tick_source_counts.get("tick_rows_total"),
                "sierra_scid_files": tick_source_counts.get("sierra_scid_files", family_totals.get("sierra_scid", 0)),
                "sierra_depth_files": tick_source_counts.get("sierra_depth_files", family_totals.get("sierra_depth", 0)),
                "primitive_event_rows": tick_route_counts.get("primitive_event_rows"),
                "target_event_rows": tick_route_counts.get("target_event_rows"),
                "placebo_control_rows": tick_route_counts.get("placebo_control_rows"),
                "residual_descriptor_rows": tick_route_counts.get("residual_descriptor_rows"),
                "residual_blocker_rows": tick_route_counts.get("residual_blocker_rows"),
            },
            "bytes": {
                "tick_data": family_bytes.get("tick_data", 0),
                "sierra_scid": family_bytes.get("sierra_scid", 0),
                "sierra_depth": family_bytes.get("sierra_depth", 0),
            },
            "boundary": tick_route_boundary,
            "next_gate": tick_route_next_gate,
            "safe_flags": SAFE_FLAGS,
        },
        {
            "route_family_id": "risk_allocation_and_portfolio_router",
            "frontier_id": "FRONTIER-0005",
            "status": "DEFERRED_UNTIL_ENTRY_EVIDENCE",
            "evidence_class": "ROUTE_SELECTION_ONLY",
            "counts": {},
            "boundary": "Validated risk/policy artifacts can inform later allocation, but they do not create a new mechanical entry edge here.",
            "next_gate": "Return after a source-safe entry or filter candidate has sealed/future evidence.",
            "safe_flags": SAFE_FLAGS,
        },
    ]

    next_rows = [
        {
            "queue_id": "NEXT-ROUTE-001",
            "route_family_id": "tick_sierra_orderflow_route_c",
            "status": "blocked_on_full_permutation_concentration_and_sealed_forward_packet" if tick_route_c else "ready_to_start",
            "why": "Route C now has source contracts, M15 descriptors, development target movement, neighbor/rotated placebo controls, and residual descriptor blockers." if tick_route_c else "Local tick and Sierra sources are large and available; Worker C literature routes OFI/queue pressure/CVD into measurable mechanical descriptors.",
            "first_artifact": "tick_route_c_full_permutation_concentration_and_sealed_forward_packet" if tick_route_c else "tick_sierra_source_contract_and_primitive_schema",
            "must_not_do": [
                "no live MT5 calls",
                "no paid/vendor/API calls",
                "no strategy-performance claim from neutral microstructure movement",
            ],
            "required_controls": tick_route_c["open_blockers"] if tick_route_c else [
                "source hash/as-of manifest",
                "symbol/session/day coverage ledger",
                "duplicate-effective-N",
                "neighbor or shuffled-time placebo where labels exist",
                "cost/spread boundary before R/PnL language",
            ],
            "safe_flags": SAFE_FLAGS,
        },
        {
            "queue_id": "NEXT-ROUTE-002",
            "route_family_id": "historical_ohlc_route_a",
            "status": "blocked_until_sealed_or_future_packet",
            "why": "Six current-fleet/session OHLC candidates survived discovery controls and were frozen into replay/source contracts.",
            "first_artifact": "sealed_or_future_replay_packet_design_for_6_contracts",
            "must_not_do": [
                "no in-sample rerun as validation",
                "no entry signal claim without geometry/fill model",
            ],
            "required_controls": ohlc["open_blockers"],
            "safe_flags": SAFE_FLAGS,
        },
        {
            "queue_id": "NEXT-ROUTE-003",
            "route_family_id": "shadow_strategy_challenger_ecology",
            "status": "ready_for_terminal_state_repair",
            "why": "The shadow screen found useful challenger/failure intelligence but also blocked scorer states and unresolved terminal separation.",
            "first_artifact": "duplicate_collapsed_terminal_unresolved_strategy_comparison_contract",
            "must_not_do": [
                "no old-vs-new claim until unresolved rows are separated",
                "no top-N truncation of material strategy rows",
            ],
            "required_controls": [
                "same-denominator incumbent comparison",
                "terminal/unresolved separation",
                "duplicate-effective-N",
                "concentration by symbol/session/regime/strategy",
            ],
            "safe_flags": SAFE_FLAGS,
        },
        {
            "queue_id": "NEXT-ROUTE-004",
            "route_family_id": "nofill_execution_geometry",
            "status": "blocked_on_capture_fields_for_strategy_projection",
            "why": "No-fill-to-TP-area path behavior is frequent, but current rows lack enough decision-time geometry/cost truth for a strategy projection.",
            "first_artifact": "capture_upgrade_contract_for_entry_geometry_shadowing",
            "must_not_do": [
                "no synthetic pending-order lifecycle as proof",
                "no fillability-adjusted edge claim from path labels alone",
            ],
            "required_controls": [
                "decision_time_price",
                "candidate_geometry",
                "path_ordering",
                "spread_slippage_commission",
            ],
            "safe_flags": SAFE_FLAGS,
        },
        {
            "queue_id": "NEXT-ROUTE-005",
            "route_family_id": "haz001_ready8_route_b",
            "status": "blocked_until_future_or_sealed_target_packet",
            "why": "HAZ001 imported as neutral movement/retest design only; READY8 ADV overlay preserved zero HAZ001 residual.",
            "first_artifact": "future_or_sealed_haz001_retest_packet_only_after_source_repair",
            "must_not_do": [
                "no target-result review opening now",
                "no promotion or live-readiness language",
            ],
            "required_controls": haz001["open_blockers"],
            "safe_flags": SAFE_FLAGS,
        },
        {
            "queue_id": "NEXT-ROUTE-006",
            "route_family_id": "risk_allocation_and_portfolio_router",
            "status": "deferred",
            "why": "Risk allocation can amplify a confirmed entry/filter edge, but current new sprint outputs are still discovery/design/source-contract packets.",
            "first_artifact": "none_until_entry_candidate_survives_sealed_controls",
            "must_not_do": [
                "no allocation optimization before entry/filter candidate evidence",
                "no financial recommendation",
            ],
            "required_controls": [
                "source-safe entry/filter candidate",
                "sealed or forward evidence",
                "challenge objective constraints",
            ],
            "safe_flags": SAFE_FLAGS,
        },
    ]

    write_jsonl(STATUS_LEDGER, status_rows)
    write_jsonl(NEXT_ROUTE_QUEUE, next_rows)

    result = {
        "schema": "route_frontier_refresh_result_v1",
        "route_id": ROUTE_ID,
        "generated_utc": generated_utc,
        "safe_flags": SAFE_FLAGS,
        "counts": {
            "route_family_status_rows": len(status_rows),
            "next_route_queue_rows": len(next_rows),
        },
        "verifier_ok_at_input": bool(verifier.get("ok")),
        "next_route_recommendation": "tick_route_c_full_permutation_concentration_and_sealed_forward_packet" if tick_route_c else "tick_sierra_orderflow_route_c",
        "claim_boundary": "Route/frontier refresh only. It selects source-safe next work and does not validate edge, R/PnL, expectancy, live-readiness, or promotion.",
    }
    RESULT_PATH.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    summary = [
        "# Route Frontier Refresh",
        "",
        f"Generated UTC: `{generated_utc}`",
        "",
        "Safe flags: `NO_PROMOTION_VERDICT`, `validation_safe=false`, `outcome_review_opened=false`, `live_effect=false`",
        "",
        "Evidence class: route/frontier refresh only. No edge, R/PnL, live-readiness, or promotion verdict.",
        "",
        "## Current Route State",
        "",
        f"- Source inventory foundation done: `{sum(family_totals.values())}` files; tick files `{family_totals.get('tick_data', 0)}`, Sierra SCID files `{family_totals.get('sierra_scid', 0)}`.",
        f"- Shadow screen done: `{shadow_counts['strategy_rollup_rows']}` strategy rollup rows and `{shadow_counts['path_descriptor_rows']}` path descriptor rows.",
        f"- No-fill design packet done: `{nofill_counts['nofill_tp_area_rows']}` no-fill-to-TP-area rows, `{nofill_counts['branch_spec_rows']}` future branch specs.",
        f"- OHLC route A frozen: `{ohlc_counts['contract_rows']}` GTOS replay contracts, `{ohlc_counts['blocker_rows']}` blocker rows.",
        f"- HAZ001 route B integrated: `{haz001_counts['branch_queue_rows']}` deconcentrated branch rows, ADV residual preserved count `0`.",
        "",
        "## Next Route",
        "",
        f"- `tick_sierra_orderflow_route_c` status: `{tick_route_status}`.",
        f"- Next gate: `{tick_route_next_gate}`.",
        "",
    ]
    SUMMARY_PATH.write_text("\n".join(summary), encoding="utf-8")

    print(json.dumps({"ok": True, "result": str(RESULT_PATH), "status_rows": len(status_rows), "queue_rows": len(next_rows)}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
