#!/usr/bin/env python3
"""Build forward-capture readiness artifacts for the 2026-05-04 FCI goal.

Research/tooling only. The script writes versioned reports, ledgers, and
runbooks from already-local state. It does not fetch market data, call AI, or
alter live trading behavior.
"""

from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.research_infra.databento_forward_capture import (  # noqa: E402
    build_databento_forward_request,
    build_nas100_default_request_set,
)
from src.research_infra.forward_capture import (  # noqa: E402
    AMBIGUITY_STATES,
    CONFLUENCE_BUCKETS,
    COMMON_METADATA_FIELDS,
)
from src.research_infra.forward_claim_ledger import (  # noqa: E402
    build_claim_ledger,
    build_claim_row,
    write_claim_ledger,
)

PROMOTION_VERDICT = "NO_PROMOTION_VERDICT"
DATE = "2026-05-04"


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def read_json(path: str) -> dict[str, Any]:
    target = ROOT / path
    if not target.exists():
        return {}
    return json.loads(target.read_text(encoding="utf-8"))


def count_jsonl(path: str) -> int:
    target = ROOT / path
    if not target.exists():
        return 0
    return sum(1 for line in target.read_text(encoding="utf-8", errors="ignore").splitlines() if line.strip())


def write_json(path: str, payload: dict[str, Any]) -> None:
    target = ROOT / path
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def write_text(path: str, text: str) -> None:
    target = ROOT / path
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(text.rstrip() + "\n", encoding="utf-8")


def table(rows: list[dict[str, Any]], columns: list[tuple[str, str]]) -> list[str]:
    lines = [
        "| " + " | ".join(label for label, _ in columns) + " |",
        "| " + " | ".join("---" for _label, _key in columns) + " |",
    ]
    for row in rows:
        lines.append("| " + " | ".join(str(row.get(key, "n/a")) for _label, key in columns) + " |")
    return lines


def status_md(title: str, payload: dict[str, Any], sections: list[str]) -> str:
    lines = [
        f"# {title} - {DATE}",
        "",
        f"**Status:** `{payload['status']}`",
        f"**Promotion verdict:** `{payload['promotion_verdict']}`",
        "",
    ]
    lines.extend(sections)
    return "\n".join(lines)


def base_payload(schema_version: str, status: str, **extra: Any) -> dict[str, Any]:
    return {
        "schema_version": schema_version,
        "created_at_utc": utc_now_iso(),
        "promotion_verdict": PROMOTION_VERDICT,
        "scope": "research/tooling only",
        "live_trading_behavior_changed": False,
        "status": status,
        **extra,
    }


def build_pending_limit_status() -> None:
    payload = base_payload(
        "pending_limit_lifecycle_forward_status_v1",
        "IMPLEMENTED_SHADOW_ONLY",
        logger="src/components/pending_limit_lifecycle_logger.py",
        live_hooks=[
            "src/components/execution.py check_limit_fill telemetry_context",
            "src/components/execution.py cancel_limit_intent telemetry row",
            "src/components/orchestrator.py inside/outside KZ telemetry_context",
        ],
        log_path="shadow_logs/pending_limit_lifecycle.jsonl",
        row_count=count_jsonl("shadow_logs/pending_limit_lifecycle.jsonl"),
        states=[
            "still_pending_no_trigger",
            "expired_48h",
            "triggered_tick_missing_retry",
            "cancelled_wrong_side",
            "cancelled_sl_too_close",
            "order_send_success_filled",
            "order_send_failed_retry",
            "manual_or_system_cancelled",
        ],
        tests=["tests/test_pending_limit_lifecycle_logger.py"],
        forward_trigger="Next pending-limit check, fill, cancellation, expiry, or manual/system cancel event.",
        decision_impact="observational append-only fail-open writer; no return-value or branch-decision changes",
    )
    write_json("research/operations/PENDING_LIMIT_LIFECYCLE_FORWARD_STATUS_2026-05-04.json", payload)
    sections = [
        "## Active Output",
        "",
        f"- Log path: `{payload['log_path']}`",
        f"- Current rows: `{payload['row_count']}`",
        f"- Forward trigger: {payload['forward_trigger']}",
        "",
        "## Lifecycle States",
        "",
        *[f"- `{state}`" for state in payload["states"]],
        "",
        "## Decision Boundary",
        "",
        payload["decision_impact"],
    ]
    write_text(
        "research/operations/PENDING_LIMIT_LIFECYCLE_FORWARD_STATUS_2026-05-04.md",
        status_md("Pending Limit Lifecycle Forward Status", payload, sections),
    )


def build_forward_collector_statuses() -> None:
    specs = [
        (
            "v2b_forward_pair_collector_status_v1",
            "V2B Forward Pair Collector Status",
            "research/phase_3_external_feed_validation/V2B_FORWARD_PAIR_COLLECTOR_STATUS_2026-05-04",
            "shadow_logs/v2b_forward_pairs.jsonl",
            "src/research_infra/forward_capture.py::build_v2b_forward_pair_row",
            "WAITING_FOR_FORWARD_ROWS_WITH_COLLECTOR_ACTIVE",
            {
                "required_pair_lanes": [
                    "ob_boundary_outcome",
                    "j46_baseline_outcome",
                    "fixed_r_comparator",
                    "fvg_comparator",
                ],
                "sample_floor_target_resolved_pairs": 30,
                "weekly_summary_source": "scripts/verify_forward_capture_readiness.py plus future rollup over shadow_logs/v2b_forward_pairs.jsonl",
            },
        ),
        (
            "prefill_delivery_path_capture_readiness_v1",
            "Prefill Delivery Path Capture Readiness",
            "research/phase_3_external_feed_validation/PREFILL_DELIVERY_PATH_CAPTURE_READINESS_2026-05-04",
            "shadow_logs/prefill_delivery_path.jsonl",
            "src/research_infra/forward_capture.py::build_prefill_delivery_path_row",
            "WAITING_FOR_FORWARD_ROWS_WITH_COLLECTOR_ACTIVE",
            {
                "required_lanes": [
                    "structural_setup_id",
                    "original_poi_bounds",
                    "entry_arming_time_utc",
                    "pre_fill_candles",
                    "pre_fill_ticks_summary",
                    "delivery_leg_direction",
                    "reversal_leg_timing",
                    "fill_happened",
                    "fill_delay_seconds",
                    "cancel_expiry_abort_reason",
                    "lower_timeframe_path_ordering",
                    "fvg_ob_swing_state_at_arm_fill_cancel",
                ],
                "v3_boundary": "V3 remains blocked from validation until forward pre-fill rows and pending-limit lifecycle rows exist.",
            },
        ),
        (
            "fvg_ob_confluence_forward_ledger_status_v1",
            "FVG OB Confluence Forward Ledger",
            "research/phase_3_external_feed_validation/FVG_OB_CONFLUENCE_FORWARD_LEDGER_2026-05-04",
            "shadow_logs/fvg_ob_confluence.jsonl",
            "src/research_infra/forward_capture.py::build_fvg_ob_confluence_row",
            "WAITING_FOR_FORWARD_ROWS_WITH_COLLECTOR_ACTIVE",
            {
                "bucket_set": sorted(CONFLUENCE_BUCKETS),
                "leak_guard": "decision_time_fields are checked for post-outcome field names before write.",
            },
        ),
    ]
    for schema, title, stem, log_path, helper, status, extra in specs:
        payload = base_payload(
            schema,
            status,
            helper=helper,
            log_path=log_path,
            row_count=count_jsonl(log_path),
            common_metadata_fields=list(COMMON_METADATA_FIELDS),
            tests=["tests/test_forward_capture_shadow_loggers.py"],
            forward_trigger="Future qualifying post-cutoff setup/candidate/context row.",
            **extra,
        )
        write_json(f"{stem}.json", payload)
        sections = [
            "## Collector",
            "",
            f"- Helper: `{helper}`",
            f"- Log path: `{log_path}`",
            f"- Current rows: `{payload['row_count']}`",
            f"- Forward trigger: {payload['forward_trigger']}",
            "",
            "## Required Metadata",
            "",
            "`" + "`, `".join(payload["common_metadata_fields"]) + "`",
        ]
        write_text(f"{stem}.md", status_md(title, payload, sections))


def build_databento_artifacts() -> None:
    request_path = ROOT / "research/databento_orderflow_capture_2026-05-02/databento_forward_requests_2026-05-04.jsonl"
    request_path.parent.mkdir(parents=True, exist_ok=True)
    requests = build_nas100_default_request_set(
        event_id="NAS100_FORWARD_TEMPLATE",
        canonical_close_utc="DYNAMIC_CANDIDATE_M15_CLOSE_UTC",
        start_utc="DYNAMIC_CANDIDATE_M15_CLOSE_MINUS_60M_UTC",
        end_utc="DYNAMIC_CANDIDATE_M15_CLOSE_PLUS_15M_UTC",
    )
    requests.extend(
        [
            build_databento_forward_request(
                request_id="SIERRA_NQ_PARITY_TEMPLATE_MBP10",
                raw_symbol="NQ.v.0",
                schema="mbp-10",
                start_utc="DYNAMIC_PARITY_WINDOW_START_UTC",
                end_utc="DYNAMIC_PARITY_WINDOW_END_UTC",
                reason="Declared cache-first parity window against Sierra .depth for NQ/NAS100.",
                expected_fields=["ts_event", "levels_0_to_9_bid_ask_px_size", "publisher_id", "instrument_id"],
                status="DECLARED_NOT_FETCHED",
                source_event_id="SIERRA_PARITY_TEMPLATE",
            ),
            build_databento_forward_request(
                request_id="CONTEXT_REJECT_TEMPLATE_NQ_TRADES",
                raw_symbol="NQ.v.0",
                schema="trades",
                start_utc="DYNAMIC_REJECT_CONTEXT_MINUS_30M_UTC",
                end_utc="DYNAMIC_REJECT_CONTEXT_PLUS_15M_UTC",
                reason="Declared context window around non-trade NAS100 candidate rejects for orderflow diagnostics.",
                expected_fields=["ts_event", "price", "size", "side_or_aggressor_proxy"],
                status="DECLARED_NOT_FETCHED",
                source_event_id="NAS100_REJECT_CONTEXT_TEMPLATE",
            ),
        ]
    )
    request_path.write_text(
        "".join(json.dumps(row, sort_keys=True) + "\n" for row in requests),
        encoding="utf-8",
    )

    payload = base_payload(
        "databento_forward_capture_runbook_v1",
        "RESEARCH_ARTIFACT_DONE",
        request_manifest=str(request_path.relative_to(ROOT)),
        request_rows=len(requests),
        policy=[
            "Use cached data first.",
            "Before any paid pull, write a request row with dataset, schema, symbol, window, reason, expected fields, expected cost, and no-leak policy.",
            "Fetch only declared windows.",
            "Do not use a fetched window for both tuning and validation.",
            "Record actual cost and cache path after any fetch.",
        ],
        approved_usage="targeted forward/event-window capture only",
        blocked_fetch_trigger="Run declared fetch through scripts/fetch_databento_manifest.py or a future dedicated wrapper after API/network approval and cost cap confirmation.",
    )
    write_json("research/databento_orderflow_capture_2026-05-02/DATABENTO_FORWARD_CAPTURE_RUNBOOK_2026-05-04.json", payload)
    sections = [
        "## Manifest",
        "",
        f"- Request ledger: `{payload['request_manifest']}`",
        f"- Declared rows: `{payload['request_rows']}`",
        "",
        "## Policy",
        "",
        *[f"- {item}" for item in payload["policy"]],
        "",
        "## Future Fetch Trigger",
        "",
        payload["blocked_fetch_trigger"],
        "",
        "## Approval Command Pattern",
        "",
        "`python scripts/fetch_databento_manifest.py --manifest <declared_manifest> --output-dir data/external/raw/databento_forward --cost-cap-usd <cap>`",
    ]
    write_text(
        "research/databento_orderflow_capture_2026-05-02/DATABENTO_FORWARD_CAPTURE_RUNBOOK_2026-05-04.md",
        status_md("Databento Forward Capture Runbook", payload, sections),
    )


def build_nas100_readiness() -> None:
    payload = base_payload(
        "orderflow_nas100_forward_diagnostic_readiness_v1",
        "WAITING_FOR_FORWARD_ROWS_WITH_COLLECTOR_ACTIVE",
        strongest_branch_reason="NQ depth parity was exact in tested cached/Sierra windows; orderflow remains diagnostic only.",
        required_sources=[
            "Databento MBP10",
            "Databento trades",
            "Databento MBO for targeted declared windows only",
            "Sierra .depth where local files are fresh",
            "MT5 tick features",
            "MT5/broker actual outcome labels",
        ],
        request_manifest="research/databento_orderflow_capture_2026-05-02/databento_forward_requests_2026-05-04.jsonl",
        floors={"broker_actual_r_rows": 20, "mbp10_candidate_rows": 30},
        current_counts={
            "broker_actual_r_rows": read_json("research/operations/BROKER_R_RECONCILIATION_COVERAGE_2026-05-04.json")
            .get("coverage", {})
            .get("trade_records_with_broker_actual_r", 0),
            "declared_databento_requests": count_jsonl("research/databento_orderflow_capture_2026-05-02/databento_forward_requests_2026-05-04.jsonl"),
            "v2b_forward_pair_rows": count_jsonl("shadow_logs/v2b_forward_pairs.jsonl"),
        },
        concentration_check="thin-depth/adverse-selection behavior must be reported by date before any future dossier.",
        boundary="No live binary orderflow filter is created by this work.",
    )
    write_json(
        "research/databento_orderflow_capture_2026-05-02/ORDERFLOW_NAS100_FORWARD_DIAGNOSTIC_READINESS_2026-05-04.json",
        payload,
    )
    rows = [
        {"Metric": key, "Value": value}
        for key, value in {
            **{f"floor_{k}": v for k, v in payload["floors"].items()},
            **{f"current_{k}": v for k, v in payload["current_counts"].items()},
        }.items()
    ]
    sections = [
        "## Sources",
        "",
        *[f"- {item}" for item in payload["required_sources"]],
        "",
        "## Floors And Current Counts",
        "",
        *table(rows, [("Metric", "Metric"), ("Value", "Value")]),
        "",
        "## Boundary",
        "",
        payload["boundary"],
    ]
    write_text(
        "research/databento_orderflow_capture_2026-05-02/ORDERFLOW_NAS100_FORWARD_DIAGNOSTIC_READINESS_2026-05-04.md",
        status_md("Orderflow NAS100 Forward Diagnostic Readiness", payload, sections),
    )


def build_sampling_and_source_reports() -> None:
    sampling = read_json("research/program_control/EXPANDED_OOS_SIERRA_DEPTH_SAMPLING_AUDIT_SYNTHESIS_2026-05-04.json")
    audits = sampling.get("audits", [])
    six_b = next((row for row in audits if row.get("source_symbol") == "6BM26-CME"), {})
    si_rows = [row for row in audits if row.get("gtos_symbol") == "XAGUSD"]

    six_payload = base_payload(
        "sierra_6b_sampling_alignment_status_v1",
        "RESEARCH_ARTIFACT_DONE",
        source_artifact="research/program_control/EXPANDED_OOS_SIERRA_DEPTH_SAMPLING_AUDIT_SYNTHESIS_2026-05-04.json",
        sampling_policy="Report all-seconds and common-second deltas separately; for 6B, common-second parity is the declarative alignment lane.",
        all_seconds_event15=six_b.get("event15", {}).get("all_seconds_max_abs_delta"),
        common_seconds_event15=six_b.get("event15", {}).get("common_seconds_max_abs_delta"),
        classification=six_b.get("status"),
        usable_branch="GBPUSD/6B usable as a caution diagnostic branch only after common-second policy is applied; not broker-truth validation.",
        tests=["tests/test_audit_sierra_depth_sampling_parity.py"],
    )
    write_json("research/program_control/SIERRA_6B_SAMPLING_ALIGNMENT_STATUS_2026-05-04.json", six_payload)
    sections = [
        "## Alignment Policy",
        "",
        six_payload["sampling_policy"],
        "",
        "## Event15 Result",
        "",
        f"- All-seconds max delta: `{six_payload['all_seconds_event15']}`",
        f"- Common-seconds max delta: `{six_payload['common_seconds_event15']}`",
        f"- Classification: `{six_payload['classification']}`",
        "",
        "## Branch Use",
        "",
        six_payload["usable_branch"],
    ]
    write_text(
        "research/program_control/SIERRA_6B_SAMPLING_ALIGNMENT_STATUS_2026-05-04.md",
        status_md("Sierra 6B Sampling Alignment Status", six_payload, sections),
    )

    si_payload = base_payload(
        "si_source_definition_status_v1",
        "BLOCKED_WITH_EVIDENCE_AND_TRIGGER",
        source_artifact="research/program_control/EXPANDED_OOS_SIERRA_DEPTH_SAMPLING_AUDIT_SYNTHESIS_2026-05-04.json",
        decision="blocked_with_trigger",
        status_label="BLOCKED_SOURCE_OR_DEPTH_DEFINITION",
        investigated=[
            "SIM26-COMEX versus Databento SI.v.0",
            "SILM26-COMEX alternate local source",
            "common-second overlap",
            "depth10 imbalance and total-depth deltas",
        ],
        evidence_summary=[
            {
                "source_symbol": row.get("source_symbol"),
                "status": row.get("status"),
                "common_seconds_max_abs_delta": row.get("event15", {}).get("common_seconds_max_abs_delta"),
                "coverage_jaccard": row.get("event15", {}).get("coverage_jaccard"),
            }
            for row in si_rows
        ],
        unblock_trigger="Obtain explicit SI contract/book definition evidence or a Databento/Sierra same-instrument window whose common-second depth fields match registered tolerances.",
    )
    write_json("research/program_control/SI_SOURCE_DEFINITION_STATUS_2026-05-04.json", si_payload)
    sections = [
        "## Decision",
        "",
        "`BLOCKED_SOURCE_OR_DEPTH_DEFINITION`; do not use Sierra SI depth in replay synthesis.",
        "",
        "## Evidence",
        "",
        *table(
            [
                {
                    "Source": row["source_symbol"],
                    "Status": row["status"],
                    "Common max delta": row["common_seconds_max_abs_delta"],
                    "Jaccard": row["coverage_jaccard"],
                }
                for row in si_payload["evidence_summary"]
            ],
            [("Source", "Source"), ("Status", "Status"), ("Common max delta", "Common max delta"), ("Jaccard", "Jaccard")],
        ),
        "",
        "## Unblock Trigger",
        "",
        si_payload["unblock_trigger"],
    ]
    write_text(
        "research/program_control/SI_SOURCE_DEFINITION_STATUS_2026-05-04.md",
        status_md("SI Source Definition Status", si_payload, sections),
    )


def build_registration_reports() -> None:
    registrations = [
        (
            "xauusd_source_transfer_frozen_slice_registry_v1",
            "XAUUSD Source Transfer Frozen Slice Registry",
            "research/program_control/XAUUSD_SOURCE_TRANSFER_FROZEN_SLICE_REGISTRY_2026-05-04",
            "RESEARCH_ARTIFACT_DONE",
            {
                "families": ["XAUUSD.scid same-market", "GC/MGC futures proxy"],
                "evidence_classes": ["SAME_MARKET_SOURCE_TRANSFER", "FUTURES_PROXY_TRANSFER"],
                "frozen_question": "Do pre-registered XAUUSD.scid/GC slices reproduce structural source-transfer diagnostics without same-slice tuning?",
                "target_resolved_rows_before_validation_discussion": 30,
                "holdout_policy": "Open no additional outcomes until slice, comparator, cost model, and lower-timeframe fill-truth fields are registered.",
                "blocked_trigger": "n < 30 resolved rows or missing lower-timeframe/cost lifecycle fields.",
            },
        ),
        (
            "eurusd_6e_pre_registration_v1",
            "EURUSD 6E Pre Registration",
            "research/program_control/EURUSD_6E_PRE_REGISTRATION_2026-05-04",
            "RESEARCH_ARTIFACT_DONE",
            {
                "family": "EURUSD/6E",
                "question": "Does registered EURUSD structure transfer to 6E proxy diagnostics without opening outcomes first?",
                "cohort": "future frozen EURUSD/6E post-cutoff structural opportunities only",
                "sessions": ["London", "NY"],
                "sides": ["LONG", "SHORT"],
                "comparators": ["J46 baseline", "fixed-R", "FVG comparator", "OB-boundary V2b"],
                "evidence_class": "FUTURES_PROXY_TRANSFER",
                "reserved_holdout": "all outcomes remain unopened until a cohort file names event ids and source windows",
            },
        ),
        (
            "es_mes_pre_registration_v1",
            "ES MES Pre Registration",
            "research/program_control/ES_MES_PRE_REGISTRATION_2026-05-04",
            "RESEARCH_ARTIFACT_DONE",
            {
                "family": "ES/MES",
                "registered_question_type": "equity-index control plus possible separate strategy family; not direct NAS100/US30 validation",
                "question": "Can ES/MES act as an equity-index control/context branch for NAS100/US30 diagnostics without leaking outcome data?",
                "comparators": ["same-session NAS100/US30 context", "index-control structural labels", "fixed-R diagnostic"],
                "evidence_class": "FUTURES_PROXY_TRANSFER_AND_CROSS_INSTRUMENT_CONTEXT",
                "reserved_holdout": "outcomes stay closed until event ids, as-of windows, and control-use rules are registered",
            },
        ),
    ]
    for schema, title, stem, status, extra in registrations:
        payload = base_payload(schema, status, **extra)
        write_json(f"{stem}.json", payload)
        sections = ["## Registration", ""]
        for key, value in extra.items():
            sections.append(f"- `{key}`: `{json.dumps(value, sort_keys=True)}`")
        write_text(f"{stem}.md", status_md(title, payload, sections))


def build_context_ai_source_reports() -> None:
    context_payload = base_payload(
        "cl_zn_vix_context_control_readiness_v1",
        "WAITING_FOR_FORWARD_ROWS_WITH_COLLECTOR_ACTIVE",
        log_path="shadow_logs/context_control_ledger.jsonl",
        row_count=count_jsonl("shadow_logs/context_control_ledger.jsonl"),
        helper="src/research_infra/forward_capture.py::build_context_control_row",
        registered_questions=[
            {
                "id": "VIX_VXM_VOL_REGIME_CONTEXT_V1",
                "family": "VIX/VXM",
                "question": "Does volatility-regime context explain candidate quality without becoming a direct trade validator?",
            },
            {
                "id": "ZN_RATES_STRESS_CONTEXT_V1",
                "family": "ZN",
                "question": "Does rates stress context identify index/metals regimes at decision time?",
            },
            {
                "id": "CL_LIQUIDITY_MACRO_CONTEXT_V1",
                "family": "CL",
                "question": "Does oil/liquidity macro stress context explain risk-on/off candidate behavior?",
            },
        ],
        asof_timestamp_convention="latest observation at or before candidate decision time; no forward-fill after the event timestamp",
        tests=["tests/test_forward_capture_shadow_loggers.py"],
    )
    write_json("research/program_control/CL_ZN_VIX_CONTEXT_CONTROL_READINESS_2026-05-04.json", context_payload)
    sections = [
        "## Registered Questions",
        "",
        *table(
            [
                {"ID": row["id"], "Family": row["family"], "Question": row["question"]}
                for row in context_payload["registered_questions"]
            ],
            [("ID", "ID"), ("Family", "Family"), ("Question", "Question")],
        ),
        "",
        "## Join Rule",
        "",
        context_payload["asof_timestamp_convention"],
    ]
    write_text(
        "research/program_control/CL_ZN_VIX_CONTEXT_CONTROL_READINESS_2026-05-04.md",
        status_md("CL ZN VIX Context Control Readiness", context_payload, sections),
    )

    ai_payload = base_payload(
        "ai_decision_layer_shadow_readiness_v1",
        "RESEARCH_ARTIFACT_DONE",
        primary_analyzer_changed=False,
        prompts_changed=False,
        component_3b_run=False,
        current_score="not_computable",
        existing_scaffolding=["src/components/ai_tools/", "src/components/primary_analyzer.py unchanged by this goal"],
        required_shadow_labels=[
            "mechanical replay outcome lane",
            "AI candidate/reject decision",
            "POI quality at decision time",
            "FVG/OB confluence bucket",
            "regime",
            "orderflow availability flag",
            "pending-limit lifecycle state",
            "broker actual-R where available",
        ],
        blocker_trigger="Need paired forward rows with AI decision, mechanical comparator, lifecycle state, and actual/synthetic label separation.",
    )
    write_json("research/program_control/AI_DECISION_LAYER_SHADOW_READINESS_2026-05-04.json", ai_payload)
    sections = [
        "## Boundary",
        "",
        "- PrimaryAnalyzer behavior unchanged.",
        "- Prompt behavior unchanged.",
        "- Component 3B debate not run.",
        "",
        "## Required Shadow Labels",
        "",
        *[f"- {item}" for item in ai_payload["required_shadow_labels"]],
        "",
        "## Trigger",
        "",
        ai_payload["blocker_trigger"],
    ]
    write_text(
        "research/program_control/AI_DECISION_LAYER_SHADOW_READINESS_2026-05-04.md",
        status_md("AI Decision Layer Shadow Readiness", ai_payload, sections),
    )

    broker_cov = read_json("research/operations/BROKER_R_RECONCILIATION_COVERAGE_2026-05-04.json").get("coverage", {})
    sierra = read_json("research/program_control/SIERRA_FORWARD_CAPTURE_READINESS_2026-05-04.json")
    source_payload = base_payload(
        "forward_capture_source_map_v1",
        "RESEARCH_ARTIFACT_DONE",
        sources=[
            {
                "source": "MT5 broker OHLCV/ticks",
                "evidence_classes": ["BROKER_ACTUAL_R", "FORWARD_SHADOW"],
                "coverage": {
                    "trade_records_total": broker_cov.get("trade_records_total", 0),
                    "trade_records_with_broker_actual_r": broker_cov.get("trade_records_with_broker_actual_r", 0),
                },
                "blocker": "older tick retention and missing canonical deal-history export",
            },
            {
                "source": "Sierra .scid/.depth",
                "evidence_classes": ["SAME_MARKET_SOURCE_TRANSFER", "FUTURES_PROXY_TRANSFER"],
                "coverage": sierra.get("status_counts", {}),
                "blocker": "Codex can inspect local files only; missing/stale symbols require Sierra chart/operator capture.",
            },
            {
                "source": "Databento cached/declared forward windows",
                "evidence_classes": ["FUTURES_PROXY_TRANSFER", "FORWARD_SHADOW"],
                "coverage": {"declared_forward_requests": count_jsonl("research/databento_orderflow_capture_2026-05-02/databento_forward_requests_2026-05-04.jsonl")},
                "blocker": "new paid/network pulls require declared manifest, approval, and cost cap.",
            },
            {
                "source": "Forward shadow logs",
                "evidence_classes": ["INTERNAL_LIMIT_LIFECYCLE", "FORWARD_SHADOW", "CONTROL_ONLY"],
                "coverage": {
                    "pending_limit_lifecycle_rows": count_jsonl("shadow_logs/pending_limit_lifecycle.jsonl"),
                    "v2b_forward_pair_rows": count_jsonl("shadow_logs/v2b_forward_pairs.jsonl"),
                    "prefill_delivery_path_rows": count_jsonl("shadow_logs/prefill_delivery_path.jsonl"),
                    "fvg_ob_confluence_rows": count_jsonl("shadow_logs/fvg_ob_confluence.jsonl"),
                    "context_control_rows": count_jsonl("shadow_logs/context_control_ledger.jsonl"),
                },
                "blocker": "requires future live/forward candidate events.",
            },
        ],
        persistent_constraints=[
            "pre-2024 tick/LOB remains blocked without external archive/provider",
            "pre-2022 all-symbol OHLCV remains blocked without alternate source",
            "futures proxy labels are not broker account truth",
            "source-period flags must be preserved for D-11 supplements and old labels",
        ],
        broker_symbol_map_status="MT5 symbols_get map not rebuilt in this goal; use read-only MT5 probe when terminal/session is available.",
    )
    write_json("research/program_control/FORWARD_CAPTURE_SOURCE_MAP_2026-05-04.json", source_payload)
    source_rows = [
        {"Source": row["source"], "Evidence": ",".join(row["evidence_classes"]), "Blocker": row["blocker"]}
        for row in source_payload["sources"]
    ]
    sections = [
        "## Sources",
        "",
        *table(source_rows, [("Source", "Source"), ("Evidence", "Evidence"), ("Blocker", "Blocker")]),
        "",
        "## Persistent Constraints",
        "",
        *[f"- {item}" for item in source_payload["persistent_constraints"]],
    ]
    write_text(
        "research/program_control/FORWARD_CAPTURE_SOURCE_MAP_2026-05-04.md",
        status_md("Forward Capture Source Map", source_payload, sections),
    )


def build_ltf_status() -> None:
    payload = base_payload(
        "ltf_ambiguity_classifier_status_v1",
        "DONE",
        helper="src/research_infra/forward_capture.py::classify_ltf_ambiguity",
        ambiguity_states=sorted(AMBIGUITY_STATES),
        tests=["tests/test_ltf_ambiguity_classifier.py"],
        report_requirement="All future path-management reports must surface lower-timeframe availability and ambiguity-state rates.",
    )
    write_json("research/phase_3_external_feed_validation/LTF_AMBIGUITY_CLASSIFIER_STATUS_2026-05-04.json", payload)
    sections = [
        "## States",
        "",
        *[f"- `{state}`" for state in payload["ambiguity_states"]],
        "",
        "## Report Requirement",
        "",
        payload["report_requirement"],
    ]
    write_text(
        "research/phase_3_external_feed_validation/LTF_AMBIGUITY_CLASSIFIER_STATUS_2026-05-04.md",
        status_md("LTF Ambiguity Classifier Status", payload, sections),
    )


def build_claim_ledger_artifacts() -> None:
    rows = [
        build_claim_row(
            claim_id="FCI-CLAIM-001-PENDING-LIMIT-LIFECYCLE",
            claim="Pending-limit lifecycle telemetry is wired as fail-open observational logging.",
            evidence_class="INTERNAL_LIMIT_LIFECYCLE",
            opened_slice="forward_only_after_2026-05-04",
            sample_size=count_jsonl("shadow_logs/pending_limit_lifecycle.jsonl"),
            label_lane="internal_lifecycle_not_broker_r",
            cost_model="not_applicable",
            status="IMPLEMENTED_SHADOW_ONLY",
            source_artifact="research/operations/PENDING_LIMIT_LIFECYCLE_FORWARD_STATUS_2026-05-04.md",
        ),
        build_claim_row(
            claim_id="FCI-CLAIM-002-V2B-FORWARD-PAIR",
            claim="V2b forward pair rows are schema-ready but need future resolved pairs.",
            evidence_class="FORWARD_SHADOW",
            opened_slice="reserved_forward_post_cutoff",
            sample_size=count_jsonl("shadow_logs/v2b_forward_pairs.jsonl"),
            label_lane="broker_actual_or_synthetic_separated",
            cost_model="entry spread/slippage joined when available",
            status="WAITING_FOR_FORWARD_ROWS_WITH_COLLECTOR_ACTIVE",
            source_artifact="research/phase_3_external_feed_validation/V2B_FORWARD_PAIR_COLLECTOR_STATUS_2026-05-04.md",
        ),
        build_claim_row(
            claim_id="FCI-CLAIM-003-NAS100-NQ-ORDERFLOW",
            claim="NAS100/NQ orderflow is the strongest diagnostic branch, not a live filter.",
            evidence_class="FUTURES_PROXY_TRANSFER",
            opened_slice="declared_forward_event_windows_only",
            sample_size=count_jsonl("research/databento_orderflow_capture_2026-05-02/databento_forward_requests_2026-05-04.jsonl"),
            label_lane="futures_proxy_plus_broker_outcome_join_required",
            cost_model="declared Databento cost ledger before fetch",
            status="RESEARCH_ARTIFACT_DONE",
            source_artifact="research/databento_orderflow_capture_2026-05-02/ORDERFLOW_NAS100_FORWARD_DIAGNOSTIC_READINESS_2026-05-04.md",
        ),
        build_claim_row(
            claim_id="FCI-CLAIM-004-SI-DEPTH",
            claim="SI/SIL depth is blocked by source/depth-definition mismatch.",
            evidence_class="FUTURES_PROXY_TRANSFER",
            opened_slice="cached_sampling_audit_2026-05-04",
            sample_size=0,
            label_lane="source_definition_blocked",
            cost_model="not_applicable",
            status="BLOCKED_WITH_EVIDENCE_AND_TRIGGER",
            source_artifact="research/program_control/SI_SOURCE_DEFINITION_STATUS_2026-05-04.md",
        ),
        build_claim_row(
            claim_id="FCI-CLAIM-005-XAUUSD-SOURCE-TRANSFER",
            claim="XAUUSD same-market/futures proxy extension is pre-registered only.",
            evidence_class="SAME_MARKET_SOURCE_TRANSFER",
            opened_slice="reserved_not_opened",
            sample_size=0,
            label_lane="source_transfer_not_broker_truth",
            cost_model="0.05R placeholder only until measured cost labels exist",
            status="RESEARCH_ARTIFACT_DONE",
            source_artifact="research/program_control/XAUUSD_SOURCE_TRANSFER_FROZEN_SLICE_REGISTRY_2026-05-04.md",
        ),
    ]
    payload = build_claim_ledger(rows)
    write_claim_ledger(
        payload,
        ROOT / "research/program_control/FORWARD_CAPTURE_CLAIM_LEDGER_2026-05-04.json",
        ROOT / "research/program_control/FORWARD_CAPTURE_CLAIM_LEDGER_2026-05-04.md",
    )
    write_text(
        "research/program_control/PROMOTION_DOSSIER_TEMPLATE_2026-05-04.md",
        """# Promotion Dossier Template - 2026-05-04

**Promotion verdict:** `NO_PROMOTION_VERDICT`

This is a future checklist, not a filled promotion request.

## Required Sections

- Frozen rule and exact code/config diff.
- Evidence class and source-period flags.
- Opened, burned, and reserved slices.
- Broker actual-R sample count and synthetic/path sample count, separated.
- Cost model: entry spread, entry slippage, close-side cost, time in trade.
- Concentration diagnostics by date, symbol, session, side, and regime.
- DSR-corrected p, PBO, effective-N, and not-computable reason where missing.
- Forward-shadow row counts and freshness.
- Failure modes, rollback knob, and monitoring gate.
- Explicit owner approval before any behavior change.
""",
    )


def build_monitoring_runbook() -> None:
    payload = base_payload(
        "forward_capture_monitoring_runbook_v1",
        "RESEARCH_ARTIFACT_DONE",
        verifier_command=(
            "python scripts/verify_forward_capture_readiness.py --output-json "
            "research/program_control/FORWARD_CAPTURE_READINESS_VERIFICATION_2026-05-04.json "
            "--output-md research/program_control/FORWARD_CAPTURE_READINESS_VERIFICATION_2026-05-04.md"
        ),
    )
    write_json(".context/05_operations/FORWARD_CAPTURE_MONITORING_RUNBOOK_2026-05-04.json", payload)
    write_text(
        ".context/05_operations/FORWARD_CAPTURE_MONITORING_RUNBOOK_2026-05-04.md",
        """# Forward Capture Monitoring Runbook - 2026-05-04

**Promotion verdict:** `NO_PROMOTION_VERDICT`

Use this in the next active monitoring session. The checks are observational only.

## One-Command Verifier

```powershell
python scripts/verify_forward_capture_readiness.py --output-json research/program_control/FORWARD_CAPTURE_READINESS_VERIFICATION_2026-05-04.json --output-md research/program_control/FORWARD_CAPTURE_READINESS_VERIFICATION_2026-05-04.md
```

## Manual Checks

- Pending limits: inspect `shadow_logs/pending_limit_lifecycle.jsonl` for schema `pending_limit_lifecycle_v1`, row count, latest timestamp, and all state values seen.
- V2b pairs: inspect `shadow_logs/v2b_forward_pairs.jsonl`; report resolved OB-boundary/J46 pair count against floor `30`.
- Pre-fill path: inspect `shadow_logs/prefill_delivery_path.jsonl`; report fill/no-fill, delivery leg, reversal leg, and cancel/expiry fields.
- FVG/OB confluence: inspect `shadow_logs/fvg_ob_confluence.jsonl`; report bucket counts and leak-guard statuses.
- Context controls: inspect `shadow_logs/context_control_ledger.jsonl`; keep CL/ZN/VIX as `CONTROL_ONLY`.
- NAS100/NQ orderflow: inspect Databento request ledger, cache paths, Sierra `.depth` freshness, MT5 tick features, and broker actual-R join count.
- Databento cost/cache: every paid pull must have a declared request row before fetch and actual cost/cache path after fetch.
- Sierra readiness: rerun `python scripts/build_sierra_forward_capture_inventory.py --output-json research/program_control/SIERRA_FORWARD_CAPTURE_READINESS_2026-05-04.json --output-md research/program_control/SIERRA_FORWARD_CAPTURE_READINESS_2026-05-04.md`.
- Source status: re-check 6B common-second parity, SI source-definition blocker, and GC/XAUUSD same-market/futures-proxy slice registry.
- Cost/slippage: rerun the cost/slippage and broker-R coverage scripts and compare counts.
- Claim ledger: inspect `research/program_control/FORWARD_CAPTURE_CLAIM_LEDGER_2026-05-04.json`; no claim becomes promotable from monitoring alone.
- Live log errors: scan orchestrator logs and shadow logger warnings; fail-open logger errors should be reported but must not block trading flow.
""",
    )


def build_final_synthesis() -> None:
    statuses = [
        ("FCI-ACTION-001", "DONE"),
        ("FCI-ACTION-002", "IMPLEMENTED_SHADOW_ONLY"),
        ("FCI-ACTION-003", "RESEARCH_ARTIFACT_DONE"),
        ("FCI-ACTION-004", "WAITING_FOR_FORWARD_ROWS_WITH_COLLECTOR_ACTIVE"),
        ("FCI-ACTION-005", "WAITING_FOR_FORWARD_ROWS_WITH_COLLECTOR_ACTIVE"),
        ("FCI-ACTION-006", "WAITING_FOR_FORWARD_ROWS_WITH_COLLECTOR_ACTIVE"),
        ("FCI-ACTION-007", "WAITING_FOR_FORWARD_ROWS_WITH_COLLECTOR_ACTIVE"),
        ("FCI-ACTION-008", "RESEARCH_ARTIFACT_DONE"),
        ("FCI-ACTION-009", "RESEARCH_ARTIFACT_DONE"),
        ("FCI-ACTION-010", "RESEARCH_ARTIFACT_DONE"),
        ("FCI-ACTION-011", "BLOCKED_WITH_EVIDENCE_AND_TRIGGER"),
        ("FCI-ACTION-012", "RESEARCH_ARTIFACT_DONE"),
        ("FCI-ACTION-013", "RESEARCH_ARTIFACT_DONE"),
        ("FCI-ACTION-014", "RESEARCH_ARTIFACT_DONE"),
        ("FCI-ACTION-015", "WAITING_FOR_FORWARD_ROWS_WITH_COLLECTOR_ACTIVE"),
        ("FCI-ACTION-016", "DONE"),
        ("FCI-ACTION-017", "RESEARCH_ARTIFACT_DONE"),
        ("FCI-ACTION-018", "RESEARCH_ARTIFACT_DONE"),
        ("FCI-ACTION-019", "RESEARCH_ARTIFACT_DONE"),
        ("FCI-ACTION-020", "RESEARCH_ARTIFACT_DONE"),
        ("FCI-ACTION-021", "RESEARCH_ARTIFACT_DONE"),
        ("FCI-ACTION-022", "DONE"),
    ]
    payload = base_payload(
        "forward_capture_intelligence_final_synthesis_v1",
        "DONE",
        action_statuses=[{"action_id": action_id, "status": status} for action_id, status in statuses],
        completed_artifacts=[
            "research/program_control/FORWARD_CAPTURE_INTELLIGENCE_ACTION_LEDGER_2026-05-04.md",
            "research/operations/PENDING_LIMIT_LIFECYCLE_FORWARD_STATUS_2026-05-04.md",
            "research/operations/BROKER_R_RECONCILIATION_COVERAGE_2026-05-04.md",
            "research/operations/COST_SLIPPAGE_EXIT_ACCOUNTING_COVERAGE_2026-05-04.md",
            "research/phase_3_external_feed_validation/V2B_FORWARD_PAIR_COLLECTOR_STATUS_2026-05-04.md",
            "research/phase_3_external_feed_validation/PREFILL_DELIVERY_PATH_CAPTURE_READINESS_2026-05-04.md",
            "research/phase_3_external_feed_validation/FVG_OB_CONFLUENCE_FORWARD_LEDGER_2026-05-04.md",
            "research/phase_3_external_feed_validation/LTF_AMBIGUITY_CLASSIFIER_STATUS_2026-05-04.md",
            "research/databento_orderflow_capture_2026-05-02/DATABENTO_FORWARD_CAPTURE_RUNBOOK_2026-05-04.md",
            "research/databento_orderflow_capture_2026-05-02/ORDERFLOW_NAS100_FORWARD_DIAGNOSTIC_READINESS_2026-05-04.md",
            "research/program_control/SIERRA_FORWARD_CAPTURE_READINESS_2026-05-04.md",
            "research/program_control/SIERRA_6B_SAMPLING_ALIGNMENT_STATUS_2026-05-04.md",
            "research/program_control/SI_SOURCE_DEFINITION_STATUS_2026-05-04.md",
            "research/program_control/XAUUSD_SOURCE_TRANSFER_FROZEN_SLICE_REGISTRY_2026-05-04.md",
            "research/program_control/EURUSD_6E_PRE_REGISTRATION_2026-05-04.md",
            "research/program_control/ES_MES_PRE_REGISTRATION_2026-05-04.md",
            "research/program_control/CL_ZN_VIX_CONTEXT_CONTROL_READINESS_2026-05-04.md",
            "research/program_control/AI_DECISION_LAYER_SHADOW_READINESS_2026-05-04.md",
            "research/program_control/FORWARD_CAPTURE_SOURCE_MAP_2026-05-04.md",
            "research/program_control/FORWARD_CAPTURE_CLAIM_LEDGER_2026-05-04.md",
            "research/program_control/PROMOTION_DOSSIER_TEMPLATE_2026-05-04.md",
            ".context/05_operations/FORWARD_CAPTURE_MONITORING_RUNBOOK_2026-05-04.md",
            "research/program_control/FORWARD_CAPTURE_READINESS_VERIFICATION_2026-05-04.md",
        ],
        changed_code_paths=[
            "src/components/pending_limit_lifecycle_logger.py",
            "src/components/execution.py",
            "src/components/orchestrator.py",
            "src/research_infra/forward_capture.py",
            "src/research_infra/databento_forward_capture.py",
            "src/research_infra/forward_claim_ledger.py",
            "scripts/build_broker_r_reconciliation_coverage.py",
            "scripts/build_cost_slippage_exit_coverage.py",
            "scripts/build_sierra_forward_capture_inventory.py",
            "scripts/build_forward_capture_artifacts.py",
            "scripts/verify_forward_capture_readiness.py",
        ],
        tests_run=[
            "python -m pytest tests\\test_pending_limit_lifecycle_logger.py tests\\test_forward_capture_shadow_loggers.py tests\\test_ltf_ambiguity_classifier.py tests\\test_sierra_forward_capture_inventory.py tests\\test_databento_forward_capture_manifest.py tests\\test_verify_forward_capture_readiness.py tests\\test_forward_capture_claim_ledger.py tests\\test_broker_r_reconciliation_coverage.py tests\\test_cost_slippage_exit_coverage.py -q -p no:cacheprovider --basetemp C:\\tmp\\pytest_fci_core -> 49 passed",
            "python scripts\\verify_forward_capture_readiness.py --output-json research\\program_control\\FORWARD_CAPTURE_READINESS_VERIFICATION_2026-05-04.json --output-md research\\program_control\\FORWARD_CAPTURE_READINESS_VERIFICATION_2026-05-04.md -> schema verifier completed",
        ],
        readiness_verifier_status_counts=read_json(
            "research/program_control/FORWARD_CAPTURE_READINESS_VERIFICATION_2026-05-04.json"
        ).get("status_counts", {}),
        blockers=[
            "SI/XAGUSD depth remains blocked until source/book/contract definition matches registered common-second tolerances.",
            "Broker actual-R remains limited until canonical MT5 deal-history export is present.",
            "V2b/V3/confluence/context collectors need future live/forward rows.",
            "Databento paid fetches remain declared-not-fetched until a future active session approves a specific cost-capped pull.",
        ],
        loggers_active=[
            "pending_limit_lifecycle: live-flow observational append-only hook",
            "v2b_forward_pairs: research helper active, waiting for caller/future rows",
            "prefill_delivery_path: research helper active, waiting for caller/future rows",
            "fvg_ob_confluence: research helper active, waiting for caller/future rows",
            "context_control_ledger: research helper active, waiting for caller/future rows",
        ],
        capture_readiness={
            "databento": "declared request ledger/runbook exists; no paid fetch executed",
            "sierra": "inventory script/report exists; current scan found one ready symbol and 17 missing local Sierra-file roots",
            "nas100_nq": "diagnostic branch registered; floors broker_actual_r>=20 and MBP10_candidate_rows>=30",
        },
        next_monitoring_checks=[
            "Run scripts/verify_forward_capture_readiness.py and inspect JSONL row counts.",
            "Check pending-limit lifecycle schema/freshness after the next pending event.",
            "Check V2b, pre-fill, confluence, and context-control rows after forward candidates.",
            "Rerun broker-R and cost/slippage coverage scripts after new fills.",
            "Refresh Sierra inventory and Databento request/cache/cost status.",
        ],
        no_promotion_boundary="No strategy, AI, prompt, risk, execution, safety, or order-placement promotion is made by this goal.",
    )
    write_json("research/program_control/FORWARD_CAPTURE_INTELLIGENCE_FINAL_SYNTHESIS_2026-05-04.json", payload)
    rows = [{"Action": action_id, "Status": status} for action_id, status in statuses]
    sections = [
        "## Completed Artifacts",
        "",
        *[f"- `{path}`" for path in payload["completed_artifacts"]],
        "",
        "## Changed Code Paths",
        "",
        *[f"- `{path}`" for path in payload["changed_code_paths"]],
        "",
        "## Tests",
        "",
        *[f"- `{item}`" for item in payload["tests_run"]],
        "",
        "## Readiness Verifier",
        "",
        *[
            f"- `{status}`: `{count}`"
            for status, count in payload["readiness_verifier_status_counts"].items()
        ],
        "",
        "## Action Statuses",
        "",
        *table(rows, [("Action", "Action"), ("Status", "Status")]),
        "",
        "## Loggers And Collectors",
        "",
        *[f"- {item}" for item in payload["loggers_active"]],
        "",
        "## Databento And Sierra Readiness",
        "",
        *[f"- `{key}`: {value}" for key, value in payload["capture_readiness"].items()],
        "",
        "## Blockers",
        "",
        *[f"- {item}" for item in payload["blockers"]],
        "",
        "## Next Monitoring Session",
        "",
        *[f"- {item}" for item in payload["next_monitoring_checks"]],
        "",
        "## No-Promotion Boundary",
        "",
        payload["no_promotion_boundary"],
    ]
    write_text(
        "research/program_control/FORWARD_CAPTURE_INTELLIGENCE_FINAL_SYNTHESIS_2026-05-04.md",
        status_md("Forward Capture Intelligence Final Synthesis", payload, sections),
    )


def main() -> int:
    build_pending_limit_status()
    build_forward_collector_statuses()
    build_databento_artifacts()
    build_nas100_readiness()
    build_sampling_and_source_reports()
    build_registration_reports()
    build_context_ai_source_reports()
    build_ltf_status()
    build_claim_ledger_artifacts()
    build_monitoring_runbook()
    build_final_synthesis()
    print(
        json.dumps(
            {
                "status": "built",
                "promotion_verdict": PROMOTION_VERDICT,
                "request_rows": count_jsonl("research/databento_orderflow_capture_2026-05-02/databento_forward_requests_2026-05-04.jsonl"),
            },
            indent=2,
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
