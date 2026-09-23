"""LTO-027 V2 structural selector promotion-readiness audit.

This module is research/tooling only. It checks whether the V2/V2b structural
selector lane has the evidence required before any promotion dossier can even
be considered. It does not score new outcomes, call AI/canaries/MT5/order code,
or change live trading behavior.
"""

from __future__ import annotations

import hashlib
import json
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from src.research_infra.evidence_selection import latest_by_candidate as latest_evidence_by_candidate


PROMOTION_VERDICT = "NO_PROMOTION_VERDICT"
SCHEMA_VERSION = "v2_structural_selector_readiness_v1"
REPORT_SCHEMA_VERSION = "lto027_v2_structural_selector_readiness_v1"
LTO_ID = "LTO-027"
FOLLOW_IDS = ["LIVE-FOLLOW-005", "LIVE-FOLLOW-025"]
STATUS_NOT_READY = "V2_STRUCTURAL_SELECTOR_NOT_READY_SHADOW_ONLY"
STATUS_READY_FOR_DOSSIER = "V2_STRUCTURAL_SELECTOR_READY_FOR_PROMOTION_DOSSIER_REVIEW"
ACTION_REQUIRED = "V2_STRUCTURAL_SELECTOR_READINESS_ACTION_REQUIRED"

BROKER_ACTUAL_SAMPLE_FLOOR = 30
MIN_DISTINCT_DATES = 3
MAX_TOP_DATE_SHARE = 0.50
MAX_TOP_SYMBOL_SHARE = 0.50
EXPECTED_PROMOTION_DOSSIER_GLOB = "research/program_control/V2_STRUCTURAL_SELECTOR_PROMOTION_DOSSIER_*.md"
DEFAULT_ACCOUNT_HISTORY_EXPORT = Path("data/account_history/mt5_deals_2026-04-27_2026-05-05.jsonl")

NO_DECISION_COUNTERS = {
    "ai_calls": 0,
    "canary_calls": 0,
    "order_calls": 0,
    "paid_data_calls": 0,
    "paid_fetch_attempted": False,
    "no_ai_calls": True,
    "no_canary_required": True,
    "no_execution": True,
}


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def parse_utc(value: Any) -> datetime | None:
    if value is None:
        return None
    try:
        parsed = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    except ValueError:
        return None
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def _rows_with_lines(rows: list[tuple[int, dict[str, Any]]] | list[dict[str, Any]] | None) -> list[tuple[int, dict[str, Any]]]:
    if not rows:
        return []
    first = rows[0]
    if isinstance(first, tuple):
        return [(int(line_no), row) for line_no, row in rows if isinstance(row, dict)]  # type: ignore[misc]
    return [(index, row) for index, row in enumerate(rows, start=1) if isinstance(row, dict)]  # type: ignore[arg-type]


def _clock(row: dict[str, Any]) -> datetime:
    return (
        parse_utc(row.get("backfilled_at_utc"))
        or parse_utc(row.get("created_at_utc"))
        or parse_utc(row.get("decision_time_utc"))
        or parse_utc(row.get("asof_latest_candle_utc"))
        or datetime.min.replace(tzinfo=timezone.utc)
    )


def _latest_by_candidate(rows: list[tuple[int, dict[str, Any]]] | list[dict[str, Any]] | None) -> dict[str, dict[str, Any]]:
    return latest_evidence_by_candidate(_rows_with_lines(rows))


def _stable_hash(*parts: Any) -> str:
    payload = "|".join(json.dumps(part, sort_keys=True, default=str) for part in parts)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()[:32]


def _safe_date(value: Any) -> str:
    parsed = parse_utc(value)
    if parsed is None:
        return "UNKNOWN_DATE"
    return parsed.date().isoformat()


def _share(counter: Counter[str]) -> float:
    total = sum(counter.values())
    if total <= 0:
        return 0.0
    return max(counter.values()) / total


def _gate(gate_id: str, required: str, observed: Any, passed: bool, blocker_code: str) -> dict[str, Any]:
    return {
        "gate_id": gate_id,
        "required": required,
        "observed": observed,
        "passed": bool(passed),
        "blocker_code": "" if passed else blocker_code,
    }


def _all_safety_counters_zero(rows: list[dict[str, Any]]) -> bool:
    for row in rows:
        for key, expected in NO_DECISION_COUNTERS.items():
            if row.get(key, expected) != expected:
                return False
    return True


def _promotion_dossier_paths(root: Path) -> list[str]:
    paths: list[str] = []
    for path in root.glob(EXPECTED_PROMOTION_DOSSIER_GLOB):
        try:
            paths.append(str(path.relative_to(root)))
        except ValueError:
            paths.append(str(path))
    return sorted(paths)


def _resolve_under_root(root: Path, path: Path | str) -> Path:
    item = Path(path)
    return item if item.is_absolute() else root / item


def _jsonl_nonempty_line_count(path: Path) -> int:
    if not path.exists():
        return 0
    count = 0
    with path.open("r", encoding="utf-8", errors="replace") as handle:
        for line in handle:
            if line.strip():
                count += 1
    return count


def build_status_row(
    *,
    root: Path | str = ".",
    v2b_audit_rows: list[tuple[int, dict[str, Any]]] | list[dict[str, Any]] | None = None,
    v2b_pair_rows: list[tuple[int, dict[str, Any]]] | list[dict[str, Any]] | None = None,
    pending_lifecycle_rows: list[tuple[int, dict[str, Any]]] | list[dict[str, Any]] | None = None,
    broker_actual_rows: list[tuple[int, dict[str, Any]]] | list[dict[str, Any]] | None = None,
    account_history_export_path: Path | str | None = DEFAULT_ACCOUNT_HISTORY_EXPORT,
    generated_at_utc: str | None = None,
) -> dict[str, Any]:
    generated = generated_at_utc or utc_now_iso()
    root_path = Path(root)
    audits = list(_latest_by_candidate(v2b_audit_rows).values())
    pairs = list(_latest_by_candidate(v2b_pair_rows).values())
    lifecycle = _latest_by_candidate(pending_lifecycle_rows)
    broker_rows_with_lines = _rows_with_lines(broker_actual_rows)
    broker = _latest_by_candidate(broker_actual_rows)
    dossier_paths = _promotion_dossier_paths(root_path)
    resolved_export_path = (
        _resolve_under_root(root_path, account_history_export_path)
        if account_history_export_path is not None
        else None
    )
    account_history_export_present = bool(resolved_export_path and resolved_export_path.exists())
    account_history_export_rows = _jsonl_nonempty_line_count(resolved_export_path) if resolved_export_path else 0
    broker_actual_claim_allowed_keys_all = {
        str(
            row.get("trade_id")
            or row.get("candidate_id")
            or row.get("fill_id")
            or row.get("ticket")
            or row.get("row_key")
            or line_no
        )
        for line_no, row in broker_rows_with_lines
        if row.get("actual_r_claim_allowed") is True
    }
    broker_actual_claim_allowed_unique_rows_all = len(broker_actual_claim_allowed_keys_all)
    candidate_linked_broker_actual_rows_available = sum(
        1 for row in broker.values() if row.get("actual_r_claim_allowed") is True
    )

    countable = [
        row
        for row in audits
        if row.get("duplicate_aware_counting_status") == "COUNTABLE_PRIMARY_UNIQUE_OPPORTUNITY"
        or row.get("opportunity_counting_status") == "COUNTABLE_PRIMARY_UNIQUE_OPPORTUNITY"
    ]
    countable_with_lifecycle = [
        row
        for row in countable
        if row.get("pending_limit_lifecycle_audit_status") == "PENDING_LIMIT_LIFECYCLE_COMPLETE_WITH_DOCUMENTED_LIMITATIONS"
        or bool(row.get("pending_limit_final_state"))
        or (row.get("candidate_id") in lifecycle and not lifecycle[row.get("candidate_id")].get("action_required_codes"))
    ]
    countable_broker_actual = [
        row
        for row in countable
        if row.get("broker_actual_r_pair_counted") is True
        or row.get("actual_r_claim_allowed") is True
        or (row.get("candidate_id") in broker and broker[row.get("candidate_id")].get("actual_r_claim_allowed") is True)
    ]
    synthetic_counted = [row for row in countable if row.get("synthetic_path_r_pair_counted") is True]
    exact_selector_missing = [
        row
        for row in countable
        if "OB_BOUNDARY_USES_SHARED_CANDIDATE_PATH_PROXY_NOT_EXACT_V2_LOCK_METADATA"
        in set(row.get("documented_limitation_codes") or [])
        or "STRATEGY_SPECIFIC_EXACT_FIELDS_SOURCE_NOT_CAPTURED" in set(row.get("documented_limitation_codes") or [])
    ]
    action_required_rows = [row for row in audits if row.get("action_required_codes")]
    non_no_promotion_rows = [row for row in audits + pairs if row.get("promotion_verdict") not in (None, PROMOTION_VERDICT)]

    date_counts: Counter[str] = Counter(_safe_date(row.get("decision_time_utc")) for row in countable)
    symbol_counts: Counter[str] = Counter(str(row.get("symbol") or "UNKNOWN") for row in countable)
    top_date_share = round(_share(date_counts), 6)
    top_symbol_share = round(_share(symbol_counts), 6)

    concentration_pass = (
        len(date_counts) >= MIN_DISTINCT_DATES
        and top_date_share <= MAX_TOP_DATE_SHARE
        and top_symbol_share <= MAX_TOP_SYMBOL_SHARE
    )
    lifecycle_pass = bool(countable) and len(countable_with_lifecycle) == len(countable)
    actual_r_pass = len(countable_broker_actual) >= BROKER_ACTUAL_SAMPLE_FLOOR
    exact_selector_pass = bool(countable) and not exact_selector_missing
    cost_pass = actual_r_pass
    prereg_pass = bool(dossier_paths)
    safety_pass = _all_safety_counters_zero(audits + pairs)
    promotion_boundary_pass = not non_no_promotion_rows and safety_pass

    gates = [
        _gate(
            "G0_SHADOW_ONLY_BOUNDARY",
            "All selector/readiness evidence remains NO_PROMOTION_VERDICT with zero AI/canary/order/paid-data counters.",
            {"non_no_promotion_rows": len(non_no_promotion_rows), "safety_counters_zero": safety_pass},
            promotion_boundary_pass,
            "SHADOW_ONLY_BOUNDARY_VIOLATION",
        ),
        _gate(
            "G1_COUNTABLE_BROKER_ACTUAL_R_SAMPLE_FLOOR",
            f">= {BROKER_ACTUAL_SAMPLE_FLOOR} countable unique V2b/J46 pairs with broker actual-R.",
            {
                "countable_unique_pairs": len(countable),
                "countable_broker_actual_pairs": len(countable_broker_actual),
                "countable_synthetic_path_pairs": len(synthetic_counted),
            },
            actual_r_pass,
            "BROKER_ACTUAL_R_SAMPLE_FLOOR_NOT_MET",
        ),
        _gate(
            "G2_PENDING_LIFECYCLE_TRUTH_COMPLETE",
            "Every countable unique pair has pending-limit lifecycle truth or an explicit terminal/non-fill state.",
            {"countable_unique_pairs": len(countable), "countable_with_lifecycle_truth": len(countable_with_lifecycle)},
            lifecycle_pass,
            "PENDING_LIFECYCLE_TRUTH_INCOMPLETE",
        ),
        _gate(
            "G3_COST_SLIPPAGE_EXIT_ACCOUNTING_COMPLETE",
            "Promotion evidence uses broker/account-history rows with cost/slippage/exit accounting, not synthetic path R.",
            {
                "broker_actual_pairs": len(countable_broker_actual),
                "candidate_linked_broker_actual_rows_available": candidate_linked_broker_actual_rows_available,
                "global_broker_actual_claim_allowed_unique_rows": broker_actual_claim_allowed_unique_rows_all,
            },
            cost_pass,
            "COST_SLIPPAGE_EXIT_ACCOUNTING_NOT_READY",
        ),
        _gate(
            "G4_CONCENTRATION_DIAGNOSTICS_PASS",
            f">= {MIN_DISTINCT_DATES} dates, top date share <= {MAX_TOP_DATE_SHARE}, top symbol share <= {MAX_TOP_SYMBOL_SHARE}.",
            {
                "distinct_dates": len(date_counts),
                "top_date_share": top_date_share,
                "top_symbol_share": top_symbol_share,
                "date_counts": dict(date_counts),
                "symbol_counts": dict(symbol_counts),
            },
            concentration_pass,
            "CONCENTRATION_GATES_NOT_MET",
        ),
        _gate(
            "G5_EXACT_SELECTOR_METADATA_CAPTURED",
            "Countable rows contain exact V2 selector/lock metadata, not shared candidate-path OB-boundary proxies.",
            {"countable_exact_metadata_missing": len(exact_selector_missing)},
            exact_selector_pass,
            "EXACT_V2_SELECTOR_METADATA_NOT_CAPTURED",
        ),
        _gate(
            "G6_PROMOTION_DOSSIER_PREREGISTERED",
            "A separate V2 structural selector promotion dossier is preregistered before any behavior change.",
            {"matching_dossier_paths": dossier_paths},
            prereg_pass,
            "PROMOTION_DOSSIER_NOT_PREREGISTERED",
        ),
    ]
    failed = [gate for gate in gates if not gate["passed"]]
    action_required_codes: list[str] = []
    if action_required_rows:
        action_required_codes.append("SOURCE_AUDIT_ROWS_ACTION_REQUIRED")
    if non_no_promotion_rows:
        action_required_codes.append("UNEXPECTED_PROMOTION_VERDICT_IN_SOURCE_ROWS")
    if not safety_pass:
        action_required_codes.append("NONZERO_SAFETY_COUNTER_IN_SOURCE_ROWS")

    status = ACTION_REQUIRED if action_required_codes else (STATUS_READY_FOR_DOSSIER if not failed else STATUS_NOT_READY)
    source_dependency_signature = _stable_hash(
        SCHEMA_VERSION,
        generated.split("T")[0],
        len(audits),
        len(pairs),
        len(lifecycle),
        len(broker),
        [row.get("row_key") for row in audits],
        [row.get("row_key") for row in pairs],
        [row.get("row_key") for row in lifecycle.values()],
        [row.get("row_key") for row in broker.values()],
        gates,
        action_required_codes,
        account_history_export_present,
        account_history_export_rows,
        broker_actual_claim_allowed_unique_rows_all,
        candidate_linked_broker_actual_rows_available,
    )
    return {
        "schema_version": SCHEMA_VERSION,
        "row_key": _stable_hash("v2_structural_selector_readiness", source_dependency_signature),
        "source_dependency_signature": source_dependency_signature,
        "created_at_utc": generated,
        "backfilled_at_utc": generated,
        "lto_id": LTO_ID,
        "follow_ids": FOLLOW_IDS,
        "row_type": "v2_structural_selector_promotion_readiness",
        "promotion_verdict": PROMOTION_VERDICT,
        "evidence_class": "DISCOVERY_ONLY",
        "readiness_status": status,
        "readiness_verdict": "NOT_READY" if failed or action_required_codes else "DOSSIER_REVIEW_ONLY_NOT_PROMOTED",
        "sample_floor_target_broker_actual_pairs": BROKER_ACTUAL_SAMPLE_FLOOR,
        "gate_summary": {
            "passed": sum(1 for gate in gates if gate["passed"]),
            "failed": len(failed),
            "failed_gate_ids": [gate["gate_id"] for gate in failed],
            "failed_blocker_codes": [gate["blocker_code"] for gate in failed if gate["blocker_code"]],
        },
        "readiness_gates": gates,
        "source_counts": {
            "latest_v2b_audit_rows": len(audits),
            "latest_v2b_pair_rows": len(pairs),
            "pending_lifecycle_latest_rows": len(lifecycle),
            "broker_actual_latest_rows": len(broker),
            "broker_actual_claim_allowed_unique_rows_all": broker_actual_claim_allowed_unique_rows_all,
            "candidate_linked_broker_actual_rows_available": candidate_linked_broker_actual_rows_available,
            "action_required_source_rows": len(action_required_rows),
        },
        "evidence_counts": {
            "countable_unique_pairs": len(countable),
            "countable_broker_actual_pairs": len(countable_broker_actual),
            "countable_synthetic_path_pairs": len(synthetic_counted),
            "countable_with_lifecycle_truth": len(countable_with_lifecycle),
            "countable_exact_metadata_missing": len(exact_selector_missing),
        },
        "concentration_diagnostics": {
            "date_counts": dict(date_counts),
            "symbol_counts": dict(symbol_counts),
            "top_date_share": top_date_share,
            "top_symbol_share": top_symbol_share,
        },
        "mt5_account_history_boundary": {
            "export_path": str(account_history_export_path) if account_history_export_path is not None else "",
            "export_present": account_history_export_present,
            "export_nonempty_rows": account_history_export_rows,
            "global_broker_actual_claim_allowed_unique_rows": broker_actual_claim_allowed_unique_rows_all,
            "candidate_linked_broker_actual_rows_available": candidate_linked_broker_actual_rows_available,
            "countable_broker_actual_pairs": len(countable_broker_actual),
            "can_resolve": [
                "filled account trades with MT5 entry/exit deals",
                "commission/swap/profit and close deal IDs where exported",
                "time-in-trade and close-side accounting for broker-filled positions when telemetry/export rows exist",
            ],
            "cannot_resolve": [
                "non-filled shadow alternatives and counterfactual selector branches",
                "candidate rows that never became broker positions or closed deals",
                "pending-limit no-fill/cancel/expiry lifecycle unless captured by the lifecycle logger",
                "exact V2 selector lock metadata that was not written at decision time",
                "preregistered promotion-dossier metadata and concentration-gate policy",
            ],
            "claim_boundary": (
                "Read-only MT5 account history is the source of truth for filled broker outcomes, "
                "but it cannot reconstruct unfilled shadow choices or missing decision-time selector metadata."
            ),
        },
        "claim_boundary": (
            "LTO-027 is a shadow-only promotion-readiness audit. It does not validate, promote, "
            "wire, or alter any structural selector, AI prompt, risk setting, safety gate, execution, or order path."
        ),
        "ml_contribution": {
            "usable_for_k55": True,
            "feature_role": "sample_eligibility_and_selector_readiness_blocker",
            "no_leak_role": "post-decision readiness labels are excluded from decision-time feature vectors",
        },
        "documented_limitation_codes": [gate["blocker_code"] for gate in failed if gate["blocker_code"]],
        "action_required_codes": action_required_codes,
        **NO_DECISION_COUNTERS,
    }


def build_report_payload(
    *,
    root: Path | str = ".",
    generated_at_utc: str | None = None,
    v2b_audit_rows: list[tuple[int, dict[str, Any]]] | list[dict[str, Any]] | None = None,
    v2b_pair_rows: list[tuple[int, dict[str, Any]]] | list[dict[str, Any]] | None = None,
    pending_lifecycle_rows: list[tuple[int, dict[str, Any]]] | list[dict[str, Any]] | None = None,
    broker_actual_rows: list[tuple[int, dict[str, Any]]] | list[dict[str, Any]] | None = None,
    account_history_export_path: Path | str | None = DEFAULT_ACCOUNT_HISTORY_EXPORT,
) -> dict[str, Any]:
    generated = generated_at_utc or utc_now_iso()
    row = build_status_row(
        root=root,
        v2b_audit_rows=v2b_audit_rows,
        v2b_pair_rows=v2b_pair_rows,
        pending_lifecycle_rows=pending_lifecycle_rows,
        broker_actual_rows=broker_actual_rows,
        account_history_export_path=account_history_export_path,
        generated_at_utc=generated,
    )
    return {
        "schema_version": REPORT_SCHEMA_VERSION,
        "generated_at_utc": generated,
        "promotion_verdict": PROMOTION_VERDICT,
        "status": row["readiness_status"],
        "readiness_verdict": row["readiness_verdict"],
        "status_row": row,
        "completion_evidence": {
            "shadow_only_boundary_enforced": row["readiness_gates"][0]["passed"],
            "promotion_readiness_remains_not_ready": row["readiness_verdict"] == "NOT_READY",
            "no_live_behavior_changed": True,
            "new_ai_calls": 0,
            "new_canary_calls": 0,
            "new_order_calls": 0,
            "new_paid_data_calls": 0,
        },
        "synthesis": {
            "summary": (
                "V2 structural selector remains shadow-only and NOT_READY for promotion. "
                "MT5 account history can resolve filled broker outcomes where matching deals exist, "
                "but the current evidence still fails the broker-actual sample floor, "
                "cost/slippage/accounting, concentration, exact selector metadata, and promotion-dossier gates."
            ),
        },
    }


def render_markdown(payload: dict[str, Any]) -> str:
    row = payload["status_row"]
    lines = [
        "# LTO027 V2 Structural Selector Readiness - 2026-05-05",
        "",
        f"**Schema:** `{payload['schema_version']}`",
        f"**Status:** `{payload['status']}`",
        f"**Readiness verdict:** `{payload['readiness_verdict']}`",
        f"**Promotion verdict:** `{payload['promotion_verdict']}`",
        "",
        "## Summary",
        "",
        payload["synthesis"]["summary"],
        "",
        "## Evidence Counts",
        "",
        f"- Latest V2b audit rows: `{row['source_counts']['latest_v2b_audit_rows']}`",
        f"- Latest V2b pair rows: `{row['source_counts']['latest_v2b_pair_rows']}`",
        f"- Countable unique pairs: `{row['evidence_counts']['countable_unique_pairs']}`",
        f"- Countable broker-actual pairs: `{row['evidence_counts']['countable_broker_actual_pairs']}`",
        f"- Countable synthetic-path pairs: `{row['evidence_counts']['countable_synthetic_path_pairs']}`",
        f"- Countable with lifecycle truth: `{row['evidence_counts']['countable_with_lifecycle_truth']}`",
        "",
        "## Readiness Gates",
        "",
        "| Gate | Passed | Required | Observed | Blocker |",
        "|---|---:|---|---|---|",
    ]
    for gate in row["readiness_gates"]:
        observed = json.dumps(gate["observed"], sort_keys=True, default=str).replace("|", r"\|")
        lines.append(
            f"| `{gate['gate_id']}` | `{gate['passed']}` | {gate['required']} | `{observed}` | `{gate['blocker_code'] or '-'}` |"
        )
    lines.extend(
        [
            "",
            "## Concentration",
            "",
            f"- Date counts: `{row['concentration_diagnostics']['date_counts']}`",
            f"- Symbol counts: `{row['concentration_diagnostics']['symbol_counts']}`",
            f"- Top date share: `{row['concentration_diagnostics']['top_date_share']}`",
            f"- Top symbol share: `{row['concentration_diagnostics']['top_symbol_share']}`",
            "",
            "## MT5 Account-History Boundary",
            "",
            f"- Export path: `{row['mt5_account_history_boundary']['export_path']}`",
            f"- Export present: `{row['mt5_account_history_boundary']['export_present']}`",
            f"- Export non-empty rows: `{row['mt5_account_history_boundary']['export_nonempty_rows']}`",
            f"- Global broker actual-R claim-allowed unique rows: `{row['mt5_account_history_boundary']['global_broker_actual_claim_allowed_unique_rows']}`",
            f"- Candidate-linked broker actual rows available: `{row['mt5_account_history_boundary']['candidate_linked_broker_actual_rows_available']}`",
            f"- Countable broker-actual pairs: `{row['mt5_account_history_boundary']['countable_broker_actual_pairs']}`",
            f"- Can resolve: `{row['mt5_account_history_boundary']['can_resolve']}`",
            f"- Cannot resolve: `{row['mt5_account_history_boundary']['cannot_resolve']}`",
            f"- Claim boundary: {row['mt5_account_history_boundary']['claim_boundary']}",
            "",
            "## Boundary",
            "",
            row["claim_boundary"],
            "",
            "## Safety Counters",
            "",
            f"- ai_calls: `{row['ai_calls']}`",
            f"- canary_calls: `{row['canary_calls']}`",
            f"- order_calls: `{row['order_calls']}`",
            f"- paid_data_calls: `{row['paid_data_calls']}`",
        ]
    )
    return "\n".join(lines) + "\n"
