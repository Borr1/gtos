#!/usr/bin/env python3
"""Build Stage10 post-completion hardening artifacts for the vNext repair route.

This addendum is intentionally disk-only. It does not call paid APIs, does not
rerun Stage00-09, and treats Stage08 replay facts as frozen evidence.
"""

from __future__ import annotations

import hashlib
import json
import math
import subprocess
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable


ROUTE = Path(__file__).resolve().parent
REPO = ROUTE.parents[3]

DATE = "2026-05-25"
BEST_POLICY = "ACCOUNT_ABANDON_OR_RESTART"
FINAL_STATE = "replay_viable_pending_ai_source_validation"
ORIGINAL_STAGE08_STATE = "production_candidate_viable_after_repair"

STAGE08_DECISION_LEDGER = ROUTE / (
    "VNEXT_PRODUCTION_CANDIDATE_REPAIR_STAGE08_REPAIRED_REPLAY_DECISION_LEDGER_"
    f"{DATE}.jsonl"
)
STAGE08_SUMMARY = ROUTE / (
    "VNEXT_PRODUCTION_CANDIDATE_REPAIR_REPLAY_METRICS_SUMMARY_"
    f"{DATE}.json"
)
STAGE07_LEDGER = ROUTE / (
    "VNEXT_PRODUCTION_CANDIDATE_REPAIR_STAGE07_AI_POLICY_SUPERVISOR_REPAIR_LEDGER_"
    f"{DATE}.jsonl"
)
STAGE06_LEDGER = ROUTE / (
    "VNEXT_PRODUCTION_CANDIDATE_REPAIR_STAGE06_LTF_ENTRY_NOFILL_REPAIR_LEDGER_"
    f"{DATE}.jsonl"
)
DOSSIER = ROUTE / "VNEXT_PRODUCTION_CANDIDATE_REPAIR_DECISION_DOSSIER_2026-05-25.md"
COMPLETION_AUDIT = ROUTE / "VNEXT_PRODUCTION_CANDIDATE_REPAIR_COMPLETION_AUDIT_2026-05-25.json"
SESSION_STATE = ROUTE / "VNEXT_PRODUCTION_CANDIDATE_REPAIR_SESSION_STATE_2026-05-25.json"

AI_LEDGER_OUT = ROUTE / f"STAGE10_AI_SENSITIVITY_LEDGER_{DATE}.jsonl"
AI_SUMMARY_OUT = ROUTE / f"STAGE10_AI_SENSITIVITY_SUMMARY_{DATE}.json"
SOURCE_LEDGER_OUT = ROUTE / f"STAGE10_MISSING_SOURCE_LEDGER_{DATE}.jsonl"
PUSH_REPORT_OUT = ROUTE / f"STAGE10_PUSH_LFS_BLOCKERS_{DATE}.json"
ADDENDUM_REPORT_OUT = ROUTE / f"STAGE10_POST_COMPLETION_ADDENDUM_{DATE}.md"

REQUIRED_BRANCHES = (
    "AI_ACCEPTS_ALL_ELIGIBLE",
    "AI_REJECTS_ALL_CONTEXT_RECOVERY",
    "AI_ACCEPTS_ONLY_HIGH_QUALITY_PARTITIONS",
    "AI_ACCEPTANCE_PRECISION_BANDS",
    "MALFORMED_REPAIRED_THEN_SCHEMA_VALIDATED",
    "MALFORMED_DEMOTED_TO_NO_TRADE",
    "NO_PAID_DIAGNOSTIC_ZERO_OUTPUT",
)

METRIC_FIELDS = (
    "selected_rows",
    "total_proxy_r",
    "expectancy_r",
    "profit_factor",
    "win_rate",
    "pass_rate",
    "fail_rate",
    "account_loss_rate",
    "ev_per_attempt_usd",
    "ev_per_terminal_day_usd",
    "ai_calls_required",
    "ai_calls_saved",
    "missed_winners",
    "avoided_losers",
    "accepted_losers",
    "blocked_winners",
    "selected_only_coverage",
)


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def read_json(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def write_json(path: Path, payload: dict[str, Any]) -> None:
    with path.open("w", encoding="utf-8", newline="\n") as handle:
        json.dump(payload, handle, indent=2, sort_keys=True)
        handle.write("\n")


def stream_jsonl(path: Path) -> Iterable[dict[str, Any]]:
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if line:
                yield json.loads(line)


def write_jsonl(path: Path, rows: Iterable[dict[str, Any]]) -> None:
    with path.open("w", encoding="utf-8", newline="\n") as handle:
        for row in rows:
            handle.write(json.dumps(row, sort_keys=True))
            handle.write("\n")


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def safe_float(value: Any) -> float | None:
    if value is None:
        return None
    try:
        as_float = float(value)
    except (TypeError, ValueError):
        return None
    if math.isnan(as_float) or math.isinf(as_float):
        return None
    return as_float


def month_from_row(row: dict[str, Any]) -> str:
    month = row.get("month")
    if month:
        return str(month)
    as_of = row.get("as_of_utc") or row.get("timestamp_utc") or ""
    return str(as_of)[:7] if len(str(as_of)) >= 7 else "UNKNOWN"


def terminal_day(row: dict[str, Any]) -> str:
    as_of = str(row.get("as_of_utc") or row.get("timestamp_utc") or "")
    return as_of[:10] if len(as_of) >= 10 else "UNKNOWN"


def load_stage08_best_policy_rows() -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    all_rows: list[dict[str, Any]] = []
    selected_rows: list[dict[str, Any]] = []
    for row in stream_jsonl(STAGE08_DECISION_LEDGER):
        if row.get("policy") != BEST_POLICY:
            continue
        row["month"] = month_from_row(row)
        all_rows.append(row)
        if row.get("selected") is True:
            selected_rows.append(row)
    return all_rows, selected_rows


def load_stage07_attrs(candidate_ids: set[str]) -> dict[str, dict[str, Any]]:
    attrs: dict[str, dict[str, Any]] = {}
    for row in stream_jsonl(STAGE07_LEDGER):
        candidate_id = row.get("candidate_id")
        if candidate_id not in candidate_ids:
            continue
        attrs[candidate_id] = {
            "stage07_policy_branch": row.get("stage07_policy_branch"),
            "stage07_ai_policy_action": row.get("stage07_ai_policy_action"),
            "stage07_ai_role": row.get("stage07_ai_role"),
            "stage07_ai_call_required_for_production": row.get(
                "stage07_ai_call_required_for_production"
            ),
            "stage07_no_paid_call_diagnostic_only": row.get(
                "stage07_no_paid_call_diagnostic_only"
            ),
            "stage07_no_paid_call_status": row.get("stage07_no_paid_call_status"),
            "malformed_response_policy": row.get("malformed_response_policy"),
            "prompt_packet_sha256": row.get("prompt_packet_sha256"),
            "schema_contract": row.get("schema_contract"),
            "stage05_recovered_into_stream": row.get("stage05_recovered_into_stream"),
            "stage06_selected_stream": row.get("stage06_selected_stream"),
        }
    return attrs


def load_stage06_attrs(candidate_ids: set[str]) -> dict[str, dict[str, Any]]:
    attrs: dict[str, dict[str, Any]] = {}
    for row in stream_jsonl(STAGE06_LEDGER):
        candidate_id = row.get("candidate_id")
        if candidate_id not in candidate_ids:
            continue
        attrs[candidate_id] = {
            "path_source_mode": row.get("path_source_mode"),
            "path_source_status": row.get("path_source_status"),
            "path_source_timeframe": row.get("path_source_timeframe"),
            "path_source_window_complete": row.get("path_source_window_complete"),
            "source_complete_for_ltf_decision": row.get("source_complete_for_ltf_decision"),
            "stage06_ltf_action": row.get("stage06_ltf_action"),
            "stage06_repair_branch": row.get("stage06_repair_branch"),
            "terminal_outcome_scoring_only": row.get("terminal_outcome_scoring_only"),
            "simulated_r_scoring_only": row.get("simulated_r_scoring_only"),
            "path_row_id": row.get("path_row_id"),
        }
    return attrs


def enrich_with_stage07(rows: list[dict[str, Any]], attrs: dict[str, dict[str, Any]]) -> None:
    for row in rows:
        row["_stage07"] = attrs.get(row.get("candidate_id"), {})


def coverage_counts(rows: list[dict[str, Any]]) -> dict[str, dict[str, int]]:
    dimensions = ("symbol", "session", "side", "framework", "source_mode", "month")
    output: dict[str, dict[str, int]] = {}
    for dim in dimensions:
        counts = Counter(str(row.get(dim) or "UNKNOWN") for row in rows)
        output[dim] = dict(sorted(counts.items()))
    return output


def gross_metrics(rows: list[dict[str, Any]]) -> dict[str, Any]:
    perf_values = [safe_float(row.get("simulated_r_scoring_only")) for row in rows]
    perf = [value for value in perf_values if value is not None]
    gross_win = sum(value for value in perf if value > 0)
    gross_loss = -sum(value for value in perf if value < 0)
    wins = sum(1 for value in perf if value > 0)
    losses = sum(1 for value in perf if value < 0)
    neutral = sum(1 for value in perf if value == 0)
    total_r = sum(perf)
    return {
        "performance_rows": len(perf),
        "non_performance_rows": len(rows) - len(perf),
        "total_proxy_r": total_r,
        "expectancy_r": total_r / len(perf) if perf else None,
        "gross_win_r": gross_win,
        "gross_loss_r": gross_loss,
        "profit_factor": gross_win / gross_loss if gross_loss else None,
        "wins": wins,
        "losses": losses,
        "neutral": neutral,
        "win_rate": wins / (wins + losses) if (wins + losses) else None,
    }


def precision_band(metrics: dict[str, Any]) -> str:
    perf = metrics.get("performance_rows") or 0
    exp = metrics.get("expectancy_r")
    pf = metrics.get("profit_factor")
    wr = metrics.get("win_rate")
    if perf < 20 or exp is None:
        return "INSUFFICIENT_N"
    if exp >= 0.15 and (pf or 0) >= 1.30 and (wr or 0) >= 0.50:
        return "VERY_HIGH"
    if exp >= 0.05 and (pf or 0) >= 1.10:
        return "HIGH"
    if exp > 0 and (pf or 0) >= 1.0:
        return "POSITIVE_THIN"
    if exp >= -0.02:
        return "FLAT_OR_NOISY"
    return "NEGATIVE"


def estimate_branch_attempt_outcomes(
    rows: list[dict[str, Any]],
    fee_usd: float = 599.0,
    payout_usd: float = 8000.0,
) -> dict[str, Any]:
    """Simple post-prop-AI branch proxy, not a Stage08 rerun.

    The Stage08 exact prop-governor attempt facts are preserved for the accept-all
    branch. Other branches need a mechanically comparable sensitivity proxy from
    disk rows, so this function applies selected rows in time order with their
    recorded risk percentage and resets at pass/fail.
    """

    if not rows:
        return {
            "attempt_model": "post_prop_ai_branch_proxy",
            "attempts_started": 0,
            "passes": 0,
            "fails": 0,
            "open_attempts": 0,
            "pass_rate": 0.0,
            "fail_rate": 0.0,
            "account_loss_rate": 0.0,
            "avg_terminal_days": None,
            "ev_per_attempt_usd": 0.0,
            "ev_per_terminal_day_usd": 0.0,
        }

    sorted_rows = sorted(rows, key=lambda row: str(row.get("as_of_utc") or ""))
    balance = 100000.0
    initial_balance = 100000.0
    phase = 1
    phase_start = sorted_rows[0].get("as_of_utc")
    attempts = 1
    passes = 0
    fails = 0
    terminal_days: list[float] = []

    def finish_attempt(row: dict[str, Any], terminal: str) -> None:
        nonlocal balance, phase, phase_start
        start = str(phase_start or row.get("as_of_utc") or "")[:10]
        end = str(row.get("as_of_utc") or "")[:10]
        if start and end and start != "UNKNOWN" and end != "UNKNOWN":
            try:
                start_dt = datetime.fromisoformat(start)
                end_dt = datetime.fromisoformat(end)
                terminal_days.append(max((end_dt - start_dt).days + 1, 1))
            except ValueError:
                pass
        balance = initial_balance
        phase = 1
        phase_start = row.get("as_of_utc")

    for row in sorted_rows:
        r_value = safe_float(row.get("simulated_r_scoring_only"))
        if r_value is None:
            continue
        risk_pct = safe_float(row.get("risk_pct"))
        if risk_pct is None:
            risk_pct = 0.0
        balance += initial_balance * (risk_pct / 100.0) * r_value

        if balance <= 90000.0:
            fails += 1
            finish_attempt(row, "fail")
            attempts += 1
            continue
        if phase == 1 and balance >= 108000.0:
            phase = 2
            phase_start = row.get("as_of_utc")
            balance = initial_balance
            continue
        if phase == 2 and balance >= 105000.0:
            passes += 1
            finish_attempt(row, "pass")
            attempts += 1

    open_attempts = 1 if sorted_rows else 0
    denominator = passes + fails + open_attempts
    pass_rate = passes / denominator if denominator else 0.0
    fail_rate = fails / denominator if denominator else 0.0
    account_loss_rate = fails / denominator if denominator else 0.0
    ev_per_attempt = pass_rate * payout_usd - account_loss_rate * fee_usd
    avg_terminal_days = sum(terminal_days) / len(terminal_days) if terminal_days else None
    ev_per_day = ev_per_attempt / avg_terminal_days if avg_terminal_days else 0.0
    return {
        "attempt_model": "post_prop_ai_branch_proxy",
        "attempts_started": attempts,
        "passes": passes,
        "fails": fails,
        "open_attempts": open_attempts,
        "pass_rate": pass_rate,
        "fail_rate": fail_rate,
        "account_loss_rate": account_loss_rate,
        "avg_terminal_days": avg_terminal_days,
        "ev_per_attempt_usd": ev_per_attempt,
        "ev_per_terminal_day_usd": ev_per_day,
    }


def build_branch_metric(
    branch_name: str,
    selected_rows: list[dict[str, Any]],
    eligible_rows: list[dict[str, Any]],
    stage08_summary: dict[str, Any],
    exact_stage08: bool = False,
    ai_calls_required_override: int | None = None,
    reason: str | None = None,
) -> dict[str, Any]:
    selected_ids = {row.get("candidate_id") for row in selected_rows}
    blocked_rows = [row for row in eligible_rows if row.get("candidate_id") not in selected_ids]
    selected_metrics = gross_metrics(selected_rows)
    blocked_metrics = gross_metrics(blocked_rows)

    ai_calls_required = (
        ai_calls_required_override
        if ai_calls_required_override is not None
        else len(eligible_rows)
    )
    branch_calls_saved = max(len(eligible_rows) - ai_calls_required, 0)
    branch_rejection_saved = (
        len(eligible_rows) - len(selected_rows)
        if ai_calls_required == len(selected_rows)
        else 0
    )
    stage08_prop_saved = stage08_prop_ai_calls_saved(stage08_summary)
    ai_calls_saved_total = stage08_prop_saved + branch_calls_saved

    if exact_stage08:
        best = stage08_summary["policy_metrics"][BEST_POLICY]
        attempt_metrics = {
            "attempt_model": "stage08_exact_repaired_replay_facts",
            "attempts_started": best.get("attempts_started"),
            "passes": best.get("phase2_passes"),
            "fails": best.get("failed_attempts"),
            "open_attempts": best.get("open_attempts"),
            "pass_rate": best.get("pass_rate"),
            "fail_rate": best.get("account_loss_rate"),
            "account_loss_rate": best.get("account_loss_rate"),
            "avg_terminal_days": best.get("avg_terminal_days"),
            "ev_per_attempt_usd": stage08_reference_ev_per_attempt(stage08_summary, best),
            "ev_per_terminal_day_usd": best.get(
                "reference_ev_per_terminal_day_usd_fee599_payout8000"
            )
            or stage08_summary.get("best_policy_reference_fee_599_payout_8000", {}).get(
                "reference_ev_per_terminal_day_usd_fee599_payout8000"
            ),
        }
        selected_metrics["total_proxy_r"] = best.get("total_r")
        selected_metrics["expectancy_r"] = best.get("expectancy_r")
        selected_metrics["profit_factor"] = best.get("profit_factor")
        selected_metrics["win_rate"] = best.get("win_rate")
        selected_metrics["performance_rows"] = stage08_best_performance_rows(best)
    else:
        attempt_metrics = estimate_branch_attempt_outcomes(selected_rows)

    output = {
        "branch_name": branch_name,
        "branch_reason": reason,
        "selected_rows": len(selected_rows),
        "eligible_rows": len(eligible_rows),
        "selected_only_coverage_ratio": len(selected_rows) / len(eligible_rows)
        if eligible_rows
        else None,
        "selected_only_coverage": coverage_counts(selected_rows),
        "blocked_by_branch_rows": len(blocked_rows),
        "performance_rows": selected_metrics["performance_rows"],
        "non_performance_rows": selected_metrics["non_performance_rows"],
        "total_proxy_r": selected_metrics["total_proxy_r"],
        "expectancy_r": selected_metrics["expectancy_r"],
        "profit_factor": selected_metrics["profit_factor"],
        "win_rate": selected_metrics["win_rate"],
        "pass_rate": attempt_metrics["pass_rate"],
        "fail_rate": attempt_metrics["fail_rate"],
        "account_loss_rate": attempt_metrics["account_loss_rate"],
        "ev_per_attempt_usd": attempt_metrics["ev_per_attempt_usd"],
        "ev_per_terminal_day_usd": attempt_metrics["ev_per_terminal_day_usd"],
        "ai_calls_required": ai_calls_required,
        "ai_calls_saved": ai_calls_saved_total,
        "ai_calls_saved_by_stage08_prop": stage08_prop_saved,
        "ai_calls_saved_by_branch_no_call": branch_calls_saved,
        "ai_calls_saved_by_branch_rejection": branch_rejection_saved,
        "missed_winners": blocked_metrics["wins"],
        "avoided_losers": blocked_metrics["losses"],
        "accepted_losers": selected_metrics["losses"],
        "blocked_winners": blocked_metrics["wins"],
        "accepted_winners": selected_metrics["wins"],
        "paid_api_or_vendor_calls_made": 0,
        **attempt_metrics,
    }
    for key in METRIC_FIELDS:
        if key not in output:
            raise RuntimeError(f"branch metric missing required field {key}: {branch_name}")
    return output


def stage08_prop_ai_calls_saved(stage08_summary: dict[str, Any]) -> int:
    counts = stage08_summary.get("ai_call_counts", {})
    if "saved_by_best_prop_block_or_defer" in counts:
        return int(counts["saved_by_best_prop_block_or_defer"])
    policy = stage08_summary.get("policy_metrics", {}).get(BEST_POLICY, {})
    return int(policy.get("ai_calls_saved_by_prop_block_or_defer", 0))


def stage08_reference_ev_per_attempt(
    stage08_summary: dict[str, Any],
    best_policy_metrics: dict[str, Any],
) -> float | None:
    if best_policy_metrics.get("reference_expected_value_per_attempt_usd") is not None:
        return best_policy_metrics.get("reference_expected_value_per_attempt_usd")
    if best_policy_metrics.get("reference_ev_per_attempt_usd_fee599_payout8000") is not None:
        return best_policy_metrics.get("reference_ev_per_attempt_usd_fee599_payout8000")
    reference = stage08_summary.get("best_policy_reference_fee_599_payout_8000", {})
    return reference.get("reference_expected_value_per_attempt_usd")


def stage08_best_performance_rows(best_policy_metrics: dict[str, Any]) -> int | None:
    if best_policy_metrics.get("performance_rows") is not None:
        return int(best_policy_metrics["performance_rows"])
    total_r = safe_float(best_policy_metrics.get("total_r"))
    expectancy = safe_float(best_policy_metrics.get("expectancy_r"))
    if total_r is None or expectancy in (None, 0):
        return None
    return int(round(total_r / expectancy))


def is_context_recovery_row(row: dict[str, Any]) -> bool:
    attrs = row.get("_stage07", {})
    branch = str(attrs.get("stage07_policy_branch") or "")
    action = str(attrs.get("stage07_ai_policy_action") or row.get("stage07_ai_policy_action") or "")
    return (
        attrs.get("stage05_recovered_into_stream") is True
        or action == "CALL_AI_CONSTRAINED_VALIDATOR"
        or "recovered" in branch
        or "context" in branch
    )


def high_quality_partition_key(row: dict[str, Any]) -> tuple[str, str, str, str, str]:
    return (
        str(row.get("symbol") or "UNKNOWN"),
        str(row.get("session") or "UNKNOWN"),
        str(row.get("side") or "UNKNOWN"),
        str(row.get("framework") or "UNKNOWN"),
        str(row.get("source_mode") or "UNKNOWN"),
    )


def build_high_quality_rows(eligible_rows: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    grouped: dict[tuple[str, str, str, str, str], list[dict[str, Any]]] = defaultdict(list)
    for row in eligible_rows:
        grouped[high_quality_partition_key(row)].append(row)

    accepted_keys: set[tuple[str, str, str, str, str]] = set()
    partition_rows: list[dict[str, Any]] = []
    for key, rows in grouped.items():
        metrics = gross_metrics(rows)
        band = precision_band(metrics)
        source_mode = key[4]
        qualifies = (
            band in {"VERY_HIGH", "HIGH"}
            and source_mode != "MISSING_SOURCE"
            and (metrics.get("performance_rows") or 0) >= 20
        )
        if qualifies:
            accepted_keys.add(key)
        partition_rows.append(
            {
                "partition_key": {
                    "symbol": key[0],
                    "session": key[1],
                    "side": key[2],
                    "framework": key[3],
                    "source_mode": key[4],
                },
                "precision_band": band,
                "qualifies_high_quality_partition": qualifies,
                **metrics,
            }
        )

    return (
        [row for row in eligible_rows if high_quality_partition_key(row) in accepted_keys],
        {
            "partition_definition": (
                "symbol/session/side/framework/source_mode partitions with n>=20, "
                "band HIGH or VERY_HIGH, source_mode != MISSING_SOURCE"
            ),
            "accepted_partition_count": len(accepted_keys),
            "total_partition_count": len(grouped),
            "partition_rows": partition_rows,
        },
    )


def build_precision_band_rows(
    eligible_rows: list[dict[str, Any]],
    stage08_summary: dict[str, Any],
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for dimension in ("symbol", "session", "side", "framework", "source_mode", "month"):
        grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
        for row in eligible_rows:
            grouped[str(row.get(dimension) or "UNKNOWN")].append(row)
        for value, partition_rows in sorted(grouped.items()):
            metric = build_branch_metric(
                "AI_ACCEPTANCE_PRECISION_BANDS",
                partition_rows,
                eligible_rows,
                stage08_summary,
                ai_calls_required_override=len(partition_rows),
                reason=f"precision band by {dimension}={value}",
            )
            metric.update(
                {
                    "ledger_row_type": "precision_band_partition",
                    "partition_dimension": dimension,
                    "partition_value": value,
                    "precision_band": precision_band(gross_metrics(partition_rows)),
                }
            )
            rows.append(metric)
    return rows


def local_source_inventory() -> dict[str, list[str]]:
    roots = [
        REPO / "data",
        REPO / "research" / "science_program_2026_05",
    ]
    extensions = {".csv", ".parquet", ".scid", ".jsonl", ".json"}
    symbols = {"XAUUSD", "XAGUSD", "US30", "US30_cash", "NAS100", "USDJPY", "GBPJPY", "GBPUSD", "EURUSD"}
    inventory: dict[str, list[str]] = {symbol: [] for symbol in symbols}
    for root in roots:
        if not root.exists():
            continue
        for path in root.rglob("*"):
            if not path.is_file() or path.suffix.lower() not in extensions:
                continue
            text = str(path)
            upper = text.upper()
            for symbol in symbols:
                normalized = symbol.upper()
                if normalized in upper or normalized.replace("_CASH", "") in upper:
                    inventory[symbol].append(str(path.relative_to(REPO)))
    return {symbol: paths[:10] for symbol, paths in inventory.items() if paths}


def source_capture_status(row: dict[str, Any], inventory: dict[str, list[str]]) -> dict[str, Any]:
    symbol = str(row.get("symbol") or "UNKNOWN")
    paths = inventory.get(symbol, [])
    if not paths:
        return {
            "can_capture_from_existing_local_files": False,
            "local_source_capture_status": "no_existing_local_symbol_file_proof_in_scanned_roots",
            "local_source_candidate_paths": [],
        }

    month = str(row.get("month") or "")
    month_token = month.replace("-", "")
    matching_month = [path for path in paths if month in path or month_token in path]
    if matching_month:
        return {
            "can_capture_from_existing_local_files": False,
            "local_source_capture_status": (
                "local_symbol_month_file_present_but_candidate_window_unproven"
            ),
            "local_source_candidate_paths": matching_month[:5],
        }
    return {
        "can_capture_from_existing_local_files": False,
        "local_source_capture_status": "local_symbol_file_present_but_window_unproven",
        "local_source_candidate_paths": paths[:5],
    }


def build_source_resolution_ledger(
    eligible_rows: list[dict[str, Any]],
    stage06_attrs: dict[str, dict[str, Any]],
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    missing_rows = [
        row for row in eligible_rows if str(row.get("source_mode") or "") == "MISSING_SOURCE"
    ]
    inventory = local_source_inventory()
    ledger: list[dict[str, Any]] = []
    for row in missing_rows:
        candidate_id = row.get("candidate_id")
        r_value = safe_float(row.get("simulated_r_scoring_only"))
        source_attrs = stage06_attrs.get(candidate_id, {})
        capture = source_capture_status(row, inventory)
        ledger.append(
            {
                "candidate_id": candidate_id,
                "symbol": row.get("symbol"),
                "session": row.get("session"),
                "side": row.get("side"),
                "framework": row.get("framework"),
                "month": row.get("month"),
                "as_of_utc": row.get("as_of_utc"),
                "r_outcome": r_value,
                "terminal_outcome": row.get("terminal_outcome_scoring_only"),
                "source_mode": row.get("source_mode"),
                "source_requirement": "recover measurable entry/fill/outcome source before activation",
                "stage06_ltf_action": source_attrs.get("stage06_ltf_action"),
                "stage06_repair_branch": source_attrs.get("stage06_repair_branch"),
                "path_source_status": source_attrs.get("path_source_status"),
                "path_source_timeframe": source_attrs.get("path_source_timeframe"),
                "path_source_window_complete": source_attrs.get("path_source_window_complete"),
                "source_complete_for_ltf_decision": source_attrs.get(
                    "source_complete_for_ltf_decision"
                ),
                "path_row_id": source_attrs.get("path_row_id"),
                "must_exclude_before_activation": True,
                "exclusion_reason": (
                    "accepted row uses MISSING_SOURCE; replay can count it only as a "
                    "diagnostic denominator fact, not as broker-facing evidence"
                ),
                "exclude_selected_delta": -1,
                "exclude_performance_rows_delta": -1 if r_value is not None else 0,
                "exclude_total_proxy_r_delta": -r_value if r_value is not None else 0.0,
                **capture,
            }
        )

    excluded_selected = [row for row in eligible_rows if row.get("source_mode") != "MISSING_SOURCE"]
    summary = {
        "accepted_missing_source_rows": len(missing_rows),
        "must_exclude_before_activation_rows": sum(
            1 for row in ledger if row["must_exclude_before_activation"]
        ),
        "can_capture_from_existing_local_files_rows": sum(
            1 for row in ledger if row["can_capture_from_existing_local_files"]
        ),
        "missing_source_excluded_branch_selected_rows": len(excluded_selected),
        "missing_source_exclusion_delta_selected_rows": -len(missing_rows),
        "missing_source_exclusion_delta_total_proxy_r": sum(
            row["exclude_total_proxy_r_delta"] for row in ledger
        ),
    }
    return ledger, summary


def git_run(args: list[str]) -> tuple[int, str, str]:
    try:
        completed = subprocess.run(
            args,
            cwd=REPO,
            text=True,
            capture_output=True,
            check=False,
        )
    except FileNotFoundError as exc:
        return 127, "", str(exc)
    return completed.returncode, completed.stdout.strip(), completed.stderr.strip()


def git_attr_filter(path: Path) -> str:
    rel = str(path.relative_to(REPO))
    code, out, err = git_run(["git", "check-attr", "filter", "--", rel])
    if code != 0:
        return f"check-attr-error: {err or out}"
    if ":" in out:
        return out.rsplit(":", 1)[-1].strip()
    return out or "unspecified"


def git_tracked(path: Path) -> bool:
    rel = str(path.relative_to(REPO))
    code, out, _err = git_run(["git", "ls-files", "--", rel])
    return code == 0 and bool(out.strip())


def git_lfs_list() -> tuple[bool, set[str], str]:
    code, out, err = git_run(["git", "lfs", "ls-files"])
    if code != 0:
        return False, set(), err or out or "git lfs ls-files failed"
    paths = set()
    for line in out.splitlines():
        parts = line.split()
        if parts:
            paths.add(parts[-1])
    return True, paths, ""


def build_push_blocker_report() -> dict[str, Any]:
    lfs_available, lfs_paths, lfs_error = git_lfs_list()
    large_files = []
    for path in ROUTE.iterdir():
        if not path.is_file():
            continue
        size = path.stat().st_size
        if size <= 100_000_000:
            continue
        rel = str(path.relative_to(REPO))
        attr_filter = git_attr_filter(path)
        tracked = git_tracked(path)
        in_lfs = rel in lfs_paths
        if attr_filter == "lfs" and in_lfs:
            required_action = "lfs_tracked_ok_verify_remote_accepts_pointer"
            blocker = False
        elif attr_filter == "lfs" and not in_lfs:
            required_action = (
                "migrate_existing_blob_to_lfs_pointer_or_re-add_after_lfs_tracking; "
                "do_not_push_normal_blob"
            )
            blocker = True
        else:
            required_action = (
                "package_or_chunk_or_migrate_to_lfs_before_push; if already committed "
                "as a normal blob, rewrite/migrate history without deleting local artifact"
            )
            blocker = True
        large_files.append(
            {
                "path": rel,
                "size_bytes": size,
                "size_mb": round(size / 1_000_000, 3),
                "git_tracked": tracked,
                "git_attr_filter": attr_filter,
                "git_lfs_ls_files_available": lfs_available,
                "listed_by_git_lfs": in_lfs,
                "sha256": sha256_file(path),
                "normal_git_push_blocker": blocker,
                "required_pre_push_action": required_action,
            }
        )
    return {
        "generated_at_utc": utc_now_iso(),
        "route": str(ROUTE.relative_to(REPO)),
        "threshold_bytes": 100_000_000,
        "git_lfs_ls_files_available": lfs_available,
        "git_lfs_ls_files_error": lfs_error,
        "large_file_count": len(large_files),
        "normal_git_push_blocker_count": sum(
            1 for item in large_files if item["normal_git_push_blocker"]
        ),
        "large_files": sorted(large_files, key=lambda item: item["size_bytes"], reverse=True),
        "push_safety_verdict": (
            "BLOCK_PUSH_UNTIL_LFS_OR_EXTERNAL_ARTIFACT_PACKAGING_RESOLVED"
            if any(item["normal_git_push_blocker"] for item in large_files)
            else "NO_LARGE_FILE_PUSH_BLOCKER_DETECTED"
        ),
        "required_action_summary": (
            "Do not push until every >100MB route artifact is either represented by an "
            "LFS pointer in history, chunked below host limits with a manifest, or "
            "packaged in an external artifact store while preserving local checksums."
        ),
    }


def update_dossier(addendum_summary: dict[str, Any]) -> None:
    text = DOSSIER.read_text(encoding="utf-8")
    text = text.replace(
        f"Final state: `{ORIGINAL_STAGE08_STATE}`",
        f"Final state: `{FINAL_STATE}`",
    )
    marker = "## Stage10 Post-Completion Hardening Addendum"
    if marker in text:
        text = text[: text.index(marker)].rstrip() + "\n\n"
    block = f"""## Stage10 Post-Completion Hardening Addendum

Post-completion state: `{FINAL_STATE}`.

Stage08 replay facts remain frozen: best policy `{BEST_POLICY}` selected
22,270 rows, total R 2,434.896089846658, expectancy 0.11206775394,
PF 1.202010371798, pass rate 0.497753818509, and account loss rate
0.501347708895. The repair route is replay-viable, but it is not
broker-facing activation-ready.

The unresolved production dependencies are now explicit:

- AI validation is not paid-vendor validated. Stage10 modeled {addendum_summary["ai_branch_count"]} AI sensitivity rows from disk with zero paid API/vendor calls.
- Accepted `MISSING_SOURCE` rows remain unresolved: {addendum_summary["accepted_missing_source_rows"]} accepted rows must be source-captured or excluded before activation.
- Push safety is blocked until large artifacts are packaged, chunked, migrated to LFS, or otherwise removed from normal Git history without data loss. Large-file blockers detected: {addendum_summary["large_file_blocker_count"]}.

Therefore the correct post-completion state is
`{FINAL_STATE}`. Artifact existence and verifier success are not substitutes for
paid AI/source validation or push-safe artifact handling.
"""
    DOSSIER.write_text(text.rstrip() + "\n\n" + block, encoding="utf-8", newline="\n")


def update_json_state_files(stage08_summary_hash: str, artifact_paths: list[str]) -> None:
    for path in (COMPLETION_AUDIT, SESSION_STATE):
        if not path.exists():
            continue
        payload = read_json(path)
        payload.setdefault("stage10_post_completion_addendum", {})
        payload["stage10_post_completion_addendum"].update(
            {
                "status": "complete",
                "state": FINAL_STATE,
                "original_stage08_state_preserved": ORIGINAL_STAGE08_STATE,
                "stage08_summary_sha256_preserved": stage08_summary_hash,
                "no_paid_api_or_vendor_calls_made": True,
                "artifacts": artifact_paths,
            }
        )
        payload["active_invariant"] = FINAL_STATE
        payload["completion_gate_status"] = FINAL_STATE
        payload["final_state"] = FINAL_STATE
        payload["broker_facing_activation_ready"] = False
        payload["broker_facing_activation_readiness"] = (
            "blocked_pending_paid_ai_validation_source_resolution_and_push_safe_artifact_packaging"
        )
        payload["current_stage"] = "COMPLETE_WITH_STAGE10_POST_COMPLETION_ADDENDUM"
        if isinstance(payload.get("stage_status_table"), dict):
            payload["stage_status_table"]["STAGE_10_POST_COMPLETION_HARDENING_ADDENDUM"] = "complete"
        if isinstance(payload.get("output_artifact_paths"), list):
            for artifact in artifact_paths:
                if artifact not in payload["output_artifact_paths"]:
                    payload["output_artifact_paths"].append(artifact)
        payload["exact_next_action"] = (
            "Do not activate or push as-is. Resolve paid AI validation, capture or "
            "exclude accepted MISSING_SOURCE rows, and migrate/package >100MB route "
            "artifacts before broker-facing activation or remote push."
        )
        write_json(path, payload)


def make_report(
    stage08_summary: dict[str, Any],
    ai_summary: dict[str, Any],
    source_summary: dict[str, Any],
    push_report: dict[str, Any],
) -> str:
    best = stage08_summary["policy_metrics"][BEST_POLICY]
    selected_trades = best.get("selected_trades", best.get("allowed_trades"))
    performance_rows = stage08_best_performance_rows(best)
    lines = [
        "# Stage10 Post-Completion Hardening Addendum",
        "",
        f"Post-completion state: `{FINAL_STATE}`.",
        "",
        "## Scope",
        "",
        "This addendum reopens the completed repair route only for hardening. It does not rerun Stage00-09, does not overwrite Stage08 replay facts, and makes zero paid API/vendor calls.",
        "",
        "## Frozen Stage08 Replay Facts",
        "",
        f"- Best policy: `{BEST_POLICY}`",
        f"- Selected rows: {selected_trades:,}",
        f"- Performance rows: {performance_rows:,}",
        f"- Total R: {best['total_r']:.12f}",
        f"- Expectancy: {best['expectancy_r']:.12f}",
        f"- PF: {best['profit_factor']:.12f}",
        f"- WR: {best['win_rate']:.12f}",
        f"- Pass rate: {best['pass_rate']:.12f}",
        f"- Account loss rate: {best['account_loss_rate']:.12f}",
        "",
        "## AI Validation Sensitivity",
        "",
        "All AI branches are mechanical disk-only calibrations. They do not prove paid model acceptance.",
    ]
    for name in REQUIRED_BRANCHES:
        metric = ai_summary["branch_metrics"].get(name)
        if not metric:
            continue
        lines.extend(
            [
                "",
                f"### {name}",
                "",
                f"- Selected rows: {metric['selected_rows']:,}",
                f"- Total/proxy R: {metric['total_proxy_r'] if metric['total_proxy_r'] is not None else 'null'}",
                f"- Expectancy: {metric['expectancy_r'] if metric['expectancy_r'] is not None else 'null'}",
                f"- PF: {metric['profit_factor'] if metric['profit_factor'] is not None else 'null'}",
                f"- WR: {metric['win_rate'] if metric['win_rate'] is not None else 'null'}",
                f"- Pass rate: {metric['pass_rate']}",
                f"- Account loss rate: {metric['account_loss_rate']}",
                f"- EV/attempt: {metric['ev_per_attempt_usd']}",
                f"- EV/terminal day: {metric['ev_per_terminal_day_usd']}",
                f"- AI calls required: {metric['ai_calls_required']:,}",
                f"- AI calls saved: {metric['ai_calls_saved']:,}",
                f"- Missed winners: {metric['missed_winners']:,}",
                f"- Avoided losers: {metric['avoided_losers']:,}",
                f"- Accepted losers: {metric['accepted_losers']:,}",
                f"- Blocked winners: {metric['blocked_winners']:,}",
            ]
        )

    lines.extend(
        [
            "",
            "## Source Resolution",
            "",
            f"- Accepted MISSING_SOURCE rows: {source_summary['accepted_missing_source_rows']:,}",
            f"- Must exclude before activation: {source_summary['must_exclude_before_activation_rows']:,}",
            f"- Existing local files prove complete capture: {source_summary['can_capture_from_existing_local_files_rows']:,}",
            f"- Excluding unresolved source rows changes selected rows by {source_summary['missing_source_exclusion_delta_selected_rows']:,}",
            f"- Excluding unresolved source rows changes total/proxy R by {source_summary['missing_source_exclusion_delta_total_proxy_r']}",
            "",
            "## Push Safety",
            "",
            f"- Files over 100MB: {push_report['large_file_count']}",
            f"- Normal Git push blockers: {push_report['normal_git_push_blocker_count']}",
            f"- Verdict: `{push_report['push_safety_verdict']}`",
            "",
            "## Activation Readiness",
            "",
            f"Replay viability is preserved, but broker-facing activation readiness is `false`. The correct state is `{FINAL_STATE}` until paid AI validation, source handling, and push-safe artifact packaging are resolved.",
        ]
    )
    return "\n".join(lines) + "\n"


def main() -> None:
    stage08_summary = read_json(STAGE08_SUMMARY)
    stage08_summary_hash = sha256_file(STAGE08_SUMMARY)
    all_best_rows, eligible_rows = load_stage08_best_policy_rows()
    candidate_ids = {row["candidate_id"] for row in all_best_rows}
    stage07_attrs = load_stage07_attrs(candidate_ids)
    enrich_with_stage07(all_best_rows, stage07_attrs)
    enrich_with_stage07(eligible_rows, stage07_attrs)

    context_rejected_rows = [row for row in eligible_rows if not is_context_recovery_row(row)]
    high_quality_rows, high_quality_details = build_high_quality_rows(eligible_rows)
    missing_source_rows = [
        row for row in eligible_rows if str(row.get("source_mode") or "") == "MISSING_SOURCE"
    ]
    stage06_attrs = load_stage06_attrs({row["candidate_id"] for row in missing_source_rows})
    source_ledger, source_summary = build_source_resolution_ledger(eligible_rows, stage06_attrs)

    branch_rows: list[dict[str, Any]] = []
    branch_metrics = {
        "AI_ACCEPTS_ALL_ELIGIBLE": build_branch_metric(
            "AI_ACCEPTS_ALL_ELIGIBLE",
            eligible_rows,
            eligible_rows,
            stage08_summary,
            exact_stage08=True,
            reason="all Stage08 accepted best-policy rows pass AI validation",
        ),
        "AI_REJECTS_ALL_CONTEXT_RECOVERY": build_branch_metric(
            "AI_REJECTS_ALL_CONTEXT_RECOVERY",
            context_rejected_rows,
            eligible_rows,
            stage08_summary,
            ai_calls_required_override=len(context_rejected_rows),
            reason="reject Stage05 context-recovered/constrained-validator rows",
        ),
        "AI_ACCEPTS_ONLY_HIGH_QUALITY_PARTITIONS": build_branch_metric(
            "AI_ACCEPTS_ONLY_HIGH_QUALITY_PARTITIONS",
            high_quality_rows,
            eligible_rows,
            stage08_summary,
            ai_calls_required_override=len(high_quality_rows),
            reason=high_quality_details["partition_definition"],
        ),
        "MALFORMED_REPAIRED_THEN_SCHEMA_VALIDATED": build_branch_metric(
            "MALFORMED_REPAIRED_THEN_SCHEMA_VALIDATED",
            eligible_rows,
            eligible_rows,
            stage08_summary,
            exact_stage08=True,
            reason="all malformed/repairable responses are repaired then schema-validated",
        ),
        "MALFORMED_DEMOTED_TO_NO_TRADE": build_branch_metric(
            "MALFORMED_DEMOTED_TO_NO_TRADE",
            [],
            eligible_rows,
            stage08_summary,
            reason="all malformed/repairable responses demoted to no-trade",
        ),
        "NO_PAID_DIAGNOSTIC_ZERO_OUTPUT": build_branch_metric(
            "NO_PAID_DIAGNOSTIC_ZERO_OUTPUT",
            [],
            eligible_rows,
            stage08_summary,
            ai_calls_required_override=0,
            reason="diagnostic branch emits zero broker-facing output and makes no paid calls",
        ),
    }
    precision_rows = build_precision_band_rows(eligible_rows, stage08_summary)
    precision_family = build_branch_metric(
        "AI_ACCEPTANCE_PRECISION_BANDS",
        eligible_rows,
        eligible_rows,
        stage08_summary,
        exact_stage08=True,
        reason="family ledger reports symbol/session/side/framework/source-mode/month precision bands",
    )
    precision_family["precision_partition_rows"] = len(precision_rows)
    branch_metrics["AI_ACCEPTANCE_PRECISION_BANDS"] = precision_family

    for metric in branch_metrics.values():
        row = {"ledger_row_type": "branch_summary", **metric}
        branch_rows.append(row)
    branch_rows.extend(precision_rows)

    write_jsonl(AI_LEDGER_OUT, branch_rows)
    write_jsonl(SOURCE_LEDGER_OUT, source_ledger)

    push_report = build_push_blocker_report()
    write_json(PUSH_REPORT_OUT, push_report)

    ai_summary = {
        "generated_at_utc": utc_now_iso(),
        "route": str(ROUTE.relative_to(REPO)),
        "state": FINAL_STATE,
        "stage08_summary_sha256_preserved": stage08_summary_hash,
        "stage08_best_policy": BEST_POLICY,
        "stage08_candidate_universe_rows": stage08_summary["candidate_universe_rows"],
        "stage08_best_policy_stream_rows": len(all_best_rows),
        "stage08_best_policy_selected_rows": len(eligible_rows),
        "no_paid_api_or_vendor_calls_made": True,
        "required_branches": list(REQUIRED_BRANCHES),
        "branch_metrics": branch_metrics,
        "high_quality_partition_details": high_quality_details,
        "source_resolution_summary": source_summary,
        "precision_band_rows": len(precision_rows),
        "precision_band_dimensions": ["symbol", "session", "side", "framework", "source_mode", "month"],
        "artifact_paths": [
            str(AI_LEDGER_OUT.relative_to(REPO)),
            str(SOURCE_LEDGER_OUT.relative_to(REPO)),
            str(PUSH_REPORT_OUT.relative_to(REPO)),
            str(ADDENDUM_REPORT_OUT.relative_to(REPO)),
        ],
    }
    write_json(AI_SUMMARY_OUT, ai_summary)

    report = make_report(stage08_summary, ai_summary, source_summary, push_report)
    ADDENDUM_REPORT_OUT.write_text(report, encoding="utf-8", newline="\n")

    update_dossier(
        {
            "ai_branch_count": len(branch_rows),
            "accepted_missing_source_rows": source_summary["accepted_missing_source_rows"],
            "large_file_blocker_count": push_report["normal_git_push_blocker_count"],
        }
    )
    artifacts = [
        str(AI_LEDGER_OUT.relative_to(REPO)),
        str(AI_SUMMARY_OUT.relative_to(REPO)),
        str(SOURCE_LEDGER_OUT.relative_to(REPO)),
        str(PUSH_REPORT_OUT.relative_to(REPO)),
        str(ADDENDUM_REPORT_OUT.relative_to(REPO)),
    ]
    update_json_state_files(stage08_summary_hash, artifacts)

    print(
        json.dumps(
            {
                "state": FINAL_STATE,
                "eligible_rows": len(eligible_rows),
                "ai_ledger_rows": len(branch_rows),
                "accepted_missing_source_rows": source_summary["accepted_missing_source_rows"],
                "large_file_blockers": push_report["normal_git_push_blocker_count"],
                "paid_api_or_vendor_calls_made": 0,
            },
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
