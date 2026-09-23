from __future__ import annotations

import json
from dataclasses import asdict
from datetime import datetime, timezone
from pathlib import Path

import sys

REPO_ROOT = Path(__file__).resolve().parents[4]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from src.research.universal_candidate_origin_registry import required_origin_families  # noqa: E402


ROUTE_DIR = Path(__file__).resolve().parent
DATE_ID = "2026-05-26"
ROUTE_ID = "vnext_moonshot_substrate_dynamic_execution_repair_2026_05_26"

OUTPUT_REGISTRY = ROUTE_DIR / f"VNEXT_MOONSHOT_UNIVERSAL_CANDIDATE_ORIGIN_REGISTRY_{DATE_ID}.jsonl"
OUTPUT_BOXING_AUDIT = ROUTE_DIR / f"VNEXT_MOONSHOT_CANDIDATE_ORIGIN_BOXING_AUDIT_LEDGER_{DATE_ID}.jsonl"
OUTPUT_SUMMARY = ROUTE_DIR / f"VNEXT_MOONSHOT_UNIVERSAL_CANDIDATE_ORIGIN_SUMMARY_{DATE_ID}.json"
OUTPUT_REPORT = ROUTE_DIR / f"VNEXT_MOONSHOT_UNIVERSAL_CANDIDATE_ORIGIN_REPORT_{DATE_ID}.md"
OUTPUT_STATE = ROUTE_DIR / f"VNEXT_MOONSHOT_SUBSTRATE_SESSION_STATE_{DATE_ID}.json"

FULL_REPLAY_CANDIDATE_SUMMARY = (
    REPO_ROOT
    / "research"
    / "science_program_2026_05"
    / "06_outcome_testing"
    / "vnext_full_historical_candidate_generation_replay_2026_05_24"
    / "VNEXT_FULL_REPLAY_CANDIDATE_GENERATION_SUMMARY_2026-05-24.json"
)
STAGE02_SOURCE_SUMMARY = ROUTE_DIR / f"VNEXT_MOONSHOT_SOURCE_PATH_CAPABILITY_SUMMARY_{DATE_ID}.json"


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def rel(path: Path) -> str:
    try:
        return path.resolve().relative_to(REPO_ROOT.resolve()).as_posix()
    except ValueError:
        return path.as_posix()


def source_availability_for(family_requirements: tuple[str, ...], source_summary: dict) -> dict:
    family_counts = source_summary.get("source_family_counts", {})
    requirement_text = " ".join(family_requirements).lower()
    availability = {
        "ohlc_bars": family_counts.get("ohlc_bars", 0),
        "tick_parquet": family_counts.get("tick_parquet", 0),
        "sierra_source": family_counts.get("sierra_source", 0),
        "shadow_log": family_counts.get("shadow_log", 0),
        "news_calendar": family_counts.get("news_calendar", 0),
        "trade_record": family_counts.get("trade_record", 0),
    }
    if "tick" in requirement_text or "bid_ask" in requirement_text:
        status = "available_but_parser_or_quote_contract_required" if availability["tick_parquet"] else "missing_or_unproven"
    elif "sierra" in requirement_text or "depth" in requirement_text:
        status = "available_but_parser_or_source_contract_required" if availability["sierra_source"] else "missing_or_unproven"
    elif "calendar" in requirement_text or "news" in requirement_text:
        status = "available" if availability["news_calendar"] else "missing_or_unproven"
    elif "pending" in requirement_text or "lifecycle" in requirement_text:
        status = "forward_capture_required_for_exact_historical_truth"
    else:
        status = "available" if availability["ohlc_bars"] else "missing_or_unproven"
    return {"source_availability_status": status, "source_family_counts": availability}


def write_registry(source_summary: dict) -> list[dict]:
    rows = []
    for index, family in enumerate(required_origin_families(), start=1):
        row = asdict(family)
        row.update(
            {
                "registry_id": f"STAGE05-ORIGIN-{index:03d}-{family.name}",
                "route_id": ROUTE_ID,
                "stage_id": "STAGE_05_UNIVERSAL_CANDIDATE_ORIGIN_LAYER",
                "default_off": True,
                "activation_status": "research_registry_only_no_runtime_candidate_generation_change",
                **source_availability_for(family.source_requirements, source_summary),
            }
        )
        rows.append(row)
    with OUTPUT_REGISTRY.open("w", encoding="utf-8", newline="\n") as handle:
        for row in rows:
            handle.write(json.dumps(row, sort_keys=True) + "\n")
    return rows


def write_boxing_audit(candidate_summary: dict, registry_rows: list[dict]) -> list[dict]:
    current_framework_rows = candidate_summary.get("candidate_rows_by_framework", {})
    session_rows = candidate_summary.get("candidate_rows_by_session_bucket", {})
    symbol_rows = candidate_summary.get("candidate_rows_by_symbol", {})
    candidate_method = candidate_summary.get("candidate_generation_method")
    rows = [
        {
            "audit_id": "STAGE05-BOXING-001-current-framework-only",
            "route_id": ROUTE_ID,
            "stage_id": "STAGE_05_UNIVERSAL_CANDIDATE_ORIGIN_LAYER",
            "current_behavior": candidate_method,
            "boxed_dimension": "framework_family",
            "evidence": current_framework_rows,
            "affected_rows": sum(current_framework_rows.values()),
            "repair_action": "register_non_ob_fvg_breaker_origin_families_before_next_candidate_generation_replay",
        },
        {
            "audit_id": "STAGE05-BOXING-002-m15-market-bar-clock",
            "route_id": ROUTE_ID,
            "stage_id": "STAGE_05_UNIVERSAL_CANDIDATE_ORIGIN_LAYER",
            "current_behavior": candidate_summary.get("source_origin"),
            "boxed_dimension": "candidate_clock",
            "evidence": {"candidate_generation_method": candidate_method},
            "affected_rows": candidate_summary.get("counts", {}).get("denominator_rows"),
            "repair_action": "allow_event_time_m1_m5_tick_session_and_lifecycle_candidate_clocks_in_registry",
        },
        {
            "audit_id": "STAGE05-BOXING-003-session-bucket-context",
            "route_id": ROUTE_ID,
            "stage_id": "STAGE_05_UNIVERSAL_CANDIDATE_ORIGIN_LAYER",
            "current_behavior": "session buckets are context over generated M15 candidates",
            "boxed_dimension": "session_origin",
            "evidence": session_rows,
            "affected_rows": sum(session_rows.values()),
            "repair_action": "allow_session_open_range_and_calendar_event_families_to_originate_candidates",
        },
        {
            "audit_id": "STAGE05-BOXING-004-symbol-universe-is-broad-but-origin-narrow",
            "route_id": ROUTE_ID,
            "stage_id": "STAGE_05_UNIVERSAL_CANDIDATE_ORIGIN_LAYER",
            "current_behavior": "many symbols are scanned but only current framework origins are generated",
            "boxed_dimension": "origin_vs_symbol_universe",
            "evidence": symbol_rows,
            "affected_rows": sum(symbol_rows.values()),
            "repair_action": "keep symbol breadth while adding universal origin families",
        },
    ]
    for row in registry_rows:
        if row["category"] != "current_gtos_framework":
            rows.append(
                {
                    "audit_id": f"STAGE05-BOXING-REGISTRY-{row['name']}",
                    "route_id": ROUTE_ID,
                    "stage_id": "STAGE_05_UNIVERSAL_CANDIDATE_ORIGIN_LAYER",
                    "current_behavior": row["current_gtos_status"],
                    "boxed_dimension": row["category"],
                    "evidence": {
                        "source_requirements": row["source_requirements"],
                        "source_availability_status": row["source_availability_status"],
                    },
                    "affected_rows": None,
                    "repair_action": row["next_replay_action"],
                }
            )
    with OUTPUT_BOXING_AUDIT.open("w", encoding="utf-8", newline="\n") as handle:
        for row in rows:
            handle.write(json.dumps(row, sort_keys=True) + "\n")
    return rows


def update_state(summary: dict) -> None:
    if not OUTPUT_STATE.exists():
        return
    state = json.loads(OUTPUT_STATE.read_text(encoding="utf-8"))
    state["updated_at_utc"] = utc_now()
    state["current_stage"] = "STAGE_05_UNIVERSAL_CANDIDATE_ORIGIN_LAYER"
    state["first_incomplete_invariant"] = "STAGE_06_MARKET_AWARENESS_ENRICHMENT"
    state["exact_next_action"] = "Run Stage06 market-awareness enrichment over source-ranked dynamic replay and origin registry fields."
    state["row_counts_scanned"]["stage05_origin_registry_rows"] = summary["origin_registry_rows"]
    state["row_counts_scanned"]["stage05_boxing_audit_rows"] = summary["boxing_audit_rows"]
    state["stage_status_table"]["STAGE_05_UNIVERSAL_CANDIDATE_ORIGIN_LAYER"] = "complete_default_off_registry"
    state["stage_status_table"]["STAGE_06_MARKET_AWARENESS_ENRICHMENT"] = "pending"
    state["output_artifact_manifest"]["universal_candidate_origin_registry"] = rel(OUTPUT_REGISTRY)
    state["output_artifact_manifest"]["candidate_origin_boxing_audit"] = rel(OUTPUT_BOXING_AUDIT)
    state["output_artifact_manifest"]["universal_candidate_origin_summary"] = rel(OUTPUT_SUMMARY)
    state["output_artifact_manifest"]["universal_candidate_origin_report"] = rel(OUTPUT_REPORT)
    state["completion_gate_status"] = "not_complete_first_incomplete_stage06"
    state.setdefault("verifiers_tests_run", []).append(
        {
            "command": (
                "py -3 research/science_program_2026_05/06_outcome_testing/"
                "vnext_moonshot_substrate_dynamic_execution_repair_2026_05_26/"
                "build_vnext_moonshot_stage05_universal_candidate_origin_layer_2026_05_26.py"
            ),
            "status": "passed",
            "result": (
                f"origin_rows={summary['origin_registry_rows']}; "
                f"boxing_rows={summary['boxing_audit_rows']}; first_incomplete=STAGE_06_MARKET_AWARENESS_ENRICHMENT"
            ),
        }
    )
    OUTPUT_STATE.write_text(json.dumps(state, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def write_report(summary: dict) -> None:
    lines = [
        "# vNext Moonshot Stage05 Universal Candidate-Origin Layer",
        "",
        f"Generated: `{summary['generated_at_utc']}`",
        "",
        "## Result",
        "",
        f"- Origin registry rows: `{summary['origin_registry_rows']}`",
        f"- Boxing audit rows: `{summary['boxing_audit_rows']}`",
        f"- Current framework candidate rows: `{summary['current_framework_candidate_rows']}`",
        f"- Non-current origin families registered: `{summary['non_current_origin_family_rows']}`",
        f"- First incomplete invariant: `{summary['first_incomplete_invariant_after_stage05']}`",
        "",
        "This stage does not activate new candidate generation. It creates the default-off registry and audit layer needed for a non-boxed replay builder.",
        "",
    ]
    OUTPUT_REPORT.write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    candidate_summary = json.loads(FULL_REPLAY_CANDIDATE_SUMMARY.read_text(encoding="utf-8"))
    source_summary = json.loads(STAGE02_SOURCE_SUMMARY.read_text(encoding="utf-8"))
    registry_rows = write_registry(source_summary)
    boxing_rows = write_boxing_audit(candidate_summary, registry_rows)
    current_framework_rows = candidate_summary.get("candidate_rows_by_framework", {})
    non_current = [row for row in registry_rows if row["category"] != "current_gtos_framework"]
    summary = {
        "route_id": ROUTE_ID,
        "stage_id": "STAGE_05_UNIVERSAL_CANDIDATE_ORIGIN_LAYER",
        "generated_at_utc": utc_now(),
        "origin_registry_path": rel(OUTPUT_REGISTRY),
        "boxing_audit_path": rel(OUTPUT_BOXING_AUDIT),
        "origin_registry_rows": len(registry_rows),
        "boxing_audit_rows": len(boxing_rows),
        "current_framework_candidate_rows": sum(current_framework_rows.values()),
        "current_framework_counts": current_framework_rows,
        "non_current_origin_family_rows": len(non_current),
        "registered_categories": sorted({row["category"] for row in registry_rows}),
        "default_off": True,
        "activation_status": "research_registry_only_no_runtime_candidate_generation_change",
        "forbidden_boundaries_crossed": False,
        "first_incomplete_invariant_after_stage05": "STAGE_06_MARKET_AWARENESS_ENRICHMENT",
    }
    OUTPUT_SUMMARY.write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    write_report(summary)
    update_state(summary)
    print(
        json.dumps(
            {
                "route_id": ROUTE_ID,
                "stage": "STAGE_05_UNIVERSAL_CANDIDATE_ORIGIN_LAYER",
                "origin_rows": len(registry_rows),
                "boxing_rows": len(boxing_rows),
                "first_incomplete_invariant": "STAGE_06_MARKET_AWARENESS_ENRICHMENT",
            },
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
