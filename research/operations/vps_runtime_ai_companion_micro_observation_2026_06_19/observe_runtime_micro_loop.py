#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
import time
from collections import Counter, defaultdict
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any


ROUTE = Path(__file__).resolve().parent
REPO_ROOT = ROUTE.parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

PACKET_LOG = REPO_ROOT / "shadow_logs" / "ultimate_book_runtime_learning_packets.jsonl"
LAUNCHER_LOG = REPO_ROOT / "shadow_logs" / "ultimate_book_launcher.jsonl"
EXECUTION_LOG = REPO_ROOT / "shadow_logs" / "execution_manager_v4_decisions.jsonl"
LIFECYCLE_LOG = REPO_ROOT / "shadow_logs" / "broker_order_lifecycle_capture_v4.jsonl"
TRADE_RECORD_ROOT = REPO_ROOT / "pipeline_state" / "ultimate_book"

SAMPLE_LEDGER = ROUTE / "MICRO_OBSERVATION_SAMPLE_LEDGER.jsonl"
LATEST_STATUS = ROUTE / "MICRO_OBSERVATION_LATEST_STATUS.json"
SYNTHESIS_JSON = ROUTE / "MICRO_OBSERVATION_SYNTHESIS.json"
SYNTHESIS_MD = ROUTE / "MICRO_OBSERVATION_SYNTHESIS.md"


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def iso(dt: datetime) -> str:
    return dt.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")


def parse_dt(value: Any) -> datetime | None:
    if value in (None, ""):
        return None
    try:
        parsed = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    except ValueError:
        return None
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True, default=str) + "\n", encoding="utf-8")


def append_jsonl(path: Path, row: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8", newline="\n") as handle:
        handle.write(json.dumps(row, sort_keys=True, default=str, separators=(",", ":")) + "\n")


def rel(path: Path) -> str:
    try:
        return str(path.resolve().relative_to(REPO_ROOT))
    except ValueError:
        return str(path)


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def read_jsonl(path: Path) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    rows: list[dict[str, Any]] = []
    errors: list[dict[str, Any]] = []
    if not path.exists():
        return rows, [{"path": rel(path), "error": "missing_file"}]
    with path.open("r", encoding="utf-8-sig", errors="ignore") as handle:
        for line_no, line in enumerate(handle, start=1):
            text = line.strip()
            if not text:
                continue
            try:
                parsed = json.loads(text)
            except json.JSONDecodeError as exc:
                errors.append({"path": rel(path), "line": line_no, "error": str(exc)})
                continue
            if isinstance(parsed, dict):
                parsed["_line_no"] = line_no
                rows.append(parsed)
            else:
                errors.append({"path": rel(path), "line": line_no, "error": "non_object_json"})
    return rows, errors


def created_at(row: dict[str, Any]) -> datetime | None:
    for key in ("created_at_utc", "ts", "generated_at_utc", "management_checked_at_utc", "closed_at_utc"):
        dt = parse_dt(row.get(key))
        if dt:
            return dt
    return None


def rows_since(rows: list[dict[str, Any]], start: datetime) -> list[dict[str, Any]]:
    return [row for row in rows if (created_at(row) or datetime.min.replace(tzinfo=timezone.utc)) >= start]


def rows_after_line(rows: list[dict[str, Any]], last_line: int) -> list[dict[str, Any]]:
    return [row for row in rows if int(row.get("_line_no") or 0) > last_line]


def max_line(rows: list[dict[str, Any]]) -> int:
    return max((int(row.get("_line_no") or 0) for row in rows), default=0)


def compact_counts(counter: Counter) -> dict[str, int]:
    return {str(key): int(value) for key, value in sorted(counter.items(), key=lambda item: str(item[0]))}


def nested_field(row: dict[str, Any], key: str) -> Any:
    value = row.get(key)
    if value not in (None, ""):
        return value
    for parent_key in ("outcome", "instrumentation", "execution"):
        parent = row.get(parent_key)
        if isinstance(parent, dict):
            value = parent.get(key)
            if value not in (None, ""):
                return value
    return None


def trade_record_field(row: dict[str, Any], key: str) -> Any:
    value = row.get(key)
    if value not in (None, ""):
        return value
    for parent_key in ("instrumentation", "execution"):
        parent = row.get(parent_key)
        if isinstance(parent, dict):
            value = parent.get(key)
            if value not in (None, ""):
                return value
    if key == "sleeve":
        instrumentation = row.get("instrumentation")
        if isinstance(instrumentation, dict):
            details = instrumentation.get("gtos_vnext_source_event_details")
            if isinstance(details, dict) and details.get("sleeve") not in (None, ""):
                return details.get("sleeve")
    return None


def latest_by_namespace(rows: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    latest: dict[str, dict[str, Any]] = {}
    for row in rows:
        namespace = str(row.get("namespace") or row.get("runtime_namespace") or "unknown")
        dt = created_at(row)
        prior = latest.get(namespace)
        if prior is None or (dt and (parse_dt(prior.get("_observed_at")) or datetime.min.replace(tzinfo=timezone.utc)) <= dt):
            latest[namespace] = {
                "_observed_at": iso(dt) if dt else None,
                "line": row.get("_line_no"),
                "event_type": row.get("event_type") or row.get("action") or row.get("stage"),
                "symbol": nested_field(row, "symbol") or nested_field(row, "broker_symbol"),
                "sleeve": nested_field(row, "sleeve"),
                "reason": nested_field(row, "reason") or nested_field(row, "reject_reason") or nested_field(row, "skip_reason"),
                "management_action": nested_field(row, "management_action"),
                "placement_status": nested_field(row, "placement_status"),
            }
    return latest


def summarize_packets(rows: list[dict[str, Any]], errors: list[dict[str, Any]], start: datetime) -> dict[str, Any]:
    window = rows_since(rows, start)
    event_counts = Counter(row.get("event_type") for row in window)
    namespace_counts = Counter(row.get("namespace") for row in window)
    joinability_counts = Counter(
        str(
            nested_field(row, "trade_record_joinability_status")
            or nested_field(row, "joinability_status")
            or nested_field(row, "runtime_learning_joinability_status")
            or "missing"
        )
        for row in window
    )
    placement_status_counts = Counter(str(nested_field(row, "placement_status") or "missing") for row in window)
    validation_issues: list[dict[str, Any]] = []
    try:
        from src.components.ultimate_book.runtime_learning_packet import validate_runtime_learning_packet

        for row in window[-1000:]:
            ok, issues = validate_runtime_learning_packet({k: v for k, v in row.items() if k != "_line_no"})
            if not ok:
                validation_issues.append({"line": row.get("_line_no"), "issues": issues[:12]})
    except Exception as exc:
        validation_issues.append({"line": None, "issues": [f"validator_error:{exc!r}"]})
    return {
        "line_count": len(rows),
        "window_row_count": len(window),
        "parse_error_count": len(errors),
        "parse_errors_sample": errors[:5],
        "validation_issue_count": len(validation_issues),
        "validation_issues_sample": validation_issues[:10],
        "event_counts": compact_counts(event_counts),
        "namespace_counts": compact_counts(namespace_counts),
        "joinability_counts": compact_counts(joinability_counts),
        "placement_status_counts": compact_counts(placement_status_counts),
        "latest_by_namespace": latest_by_namespace(window[-200:]),
    }


def summarize_launcher(rows: list[dict[str, Any]], errors: list[dict[str, Any]], start: datetime) -> dict[str, Any]:
    window = rows_since(rows, start)
    reason_counts = Counter(str(row.get("reason") or "missing") for row in window)
    action_counts = Counter(str(row.get("action") or "missing") for row in window)
    namespace_counts = Counter(str(row.get("namespace") or "missing") for row in window)
    skipped_reasons = Counter()
    skipped_symbols = Counter()
    placed_symbols = Counter()
    placed_sleeves = Counter()
    broker_unsupported_symbols = Counter()
    governor_reasons = Counter()
    size_caps: list[float] = []
    available_risk: list[float] = []
    n_candidates_in = 0
    n_candidates_after_drop = 0
    n_intents = 0
    placed_count = 0
    cycles_with_candidates = 0
    cycles_with_placements = 0
    per_namespace_latest_bridge: dict[str, dict[str, Any]] = {}
    for row in window:
        n_intents += int(row.get("n_intents") or 0)
        bridge = row.get("bridge") if isinstance(row.get("bridge"), dict) else {}
        n_candidates_in += int(bridge.get("n_candidates_in") or 0)
        n_candidates_after_drop += int(bridge.get("n_candidates_after_drop") or 0)
        if int(bridge.get("n_candidates_in") or 0) > 0:
            cycles_with_candidates += 1
        governor = bridge.get("governor") if isinstance(bridge.get("governor"), dict) else {}
        if governor:
            governor_reasons[str(governor.get("reason") or "missing")] += 1
            try:
                size_caps.append(float(governor.get("size_cap_multiplier")))
            except (TypeError, ValueError):
                pass
            try:
                available_risk.append(float(governor.get("available_gross_risk_pct")))
            except (TypeError, ValueError):
                pass
        profile_generation = bridge.get("broker_profile_generation") if isinstance(bridge.get("broker_profile_generation"), dict) else {}
        for symbol in profile_generation.get("broker_unsupported_unique_symbols") or []:
            broker_unsupported_symbols[str(symbol)] += 1
        for skipped in row.get("skipped") or []:
            if isinstance(skipped, dict):
                skipped_reasons[str(skipped.get("reason") or "missing")] += 1
                skipped_symbols[str(skipped.get("symbol") or "missing")] += 1
        placed = [item for item in (row.get("placed") or []) if isinstance(item, dict)]
        placed_count += len(placed)
        if placed:
            cycles_with_placements += 1
        for item in placed:
            placed_symbols[str(item.get("symbol") or "missing")] += 1
            placed_sleeves[str(item.get("sleeve") or "missing")] += 1
        namespace = str(row.get("namespace") or "missing")
        per_namespace_latest_bridge[namespace] = {
            "ts": row.get("ts"),
            "reason": row.get("reason"),
            "n_intents": row.get("n_intents"),
            "n_candidates_in": bridge.get("n_candidates_in"),
            "n_candidates_after_drop": bridge.get("n_candidates_after_drop"),
            "governor": governor,
            "broker_profile_generation": {
                "profile_supported_symbol_slot_count": profile_generation.get("profile_supported_symbol_slot_count"),
                "broker_unsupported_symbol_slot_count": profile_generation.get("broker_unsupported_symbol_slot_count"),
                "broker_unsupported_unique_symbols": profile_generation.get("broker_unsupported_unique_symbols"),
            },
        }
    return {
        "line_count": len(rows),
        "window_row_count": len(window),
        "parse_error_count": len(errors),
        "parse_errors_sample": errors[:5],
        "action_counts": compact_counts(action_counts),
        "namespace_counts": compact_counts(namespace_counts),
        "reason_counts": compact_counts(reason_counts),
        "n_intents": n_intents,
        "n_candidates_in": n_candidates_in,
        "n_candidates_after_drop": n_candidates_after_drop,
        "placed_count": placed_count,
        "cycles_with_candidates": cycles_with_candidates,
        "cycles_with_placements": cycles_with_placements,
        "skipped_reason_counts": compact_counts(skipped_reasons),
        "skipped_symbol_counts": compact_counts(skipped_symbols),
        "placed_symbol_counts": compact_counts(placed_symbols),
        "placed_sleeve_counts": compact_counts(placed_sleeves),
        "broker_unsupported_symbol_counts": compact_counts(broker_unsupported_symbols),
        "governor_reason_counts": compact_counts(governor_reasons),
        "size_cap_multiplier_min": min(size_caps) if size_caps else None,
        "size_cap_multiplier_max": max(size_caps) if size_caps else None,
        "available_gross_risk_pct_min": min(available_risk) if available_risk else None,
        "available_gross_risk_pct_max": max(available_risk) if available_risk else None,
        "latest_bridge_by_namespace": per_namespace_latest_bridge,
    }


def summarize_execution(rows: list[dict[str, Any]], errors: list[dict[str, Any]], start: datetime) -> dict[str, Any]:
    window = rows_since(rows, start)
    action_counts = Counter(str(row.get("action") or "missing") for row in window)
    fatal_reasons = Counter()
    warning_reasons = Counter()
    symbols = Counter()
    selected_cells = Counter()
    total_costs: list[float] = []
    blocked_examples: list[dict[str, Any]] = []
    for row in window:
        identity = row.get("identity") if isinstance(row.get("identity"), dict) else {}
        symbols[str(identity.get("symbol") or row.get("symbol") or "missing")] += 1
        selected = row.get("selected_cell_context") if isinstance(row.get("selected_cell_context"), dict) else {}
        if selected.get("selected_cell_id"):
            selected_cells[str(selected.get("selected_cell_id"))] += 1
        for reason in row.get("fatal_reasons") or []:
            fatal_reasons[str(reason)] += 1
        for reason in row.get("warning_reasons") or []:
            warning_reasons[str(reason)] += 1
        cost_packet = row.get("pretrade_cost_model") if isinstance(row.get("pretrade_cost_model"), dict) else {}
        cost_context = row.get("cost_context") if isinstance(row.get("cost_context"), dict) else {}
        try:
            total_costs.append(float(cost_packet.get("total_cost_r")))
        except (TypeError, ValueError):
            pass
        if row.get("should_block") or row.get("action") == "block":
            blocked_examples.append(
                {
                    "line": row.get("_line_no"),
                    "generated_at_utc": row.get("generated_at_utc"),
                    "symbol": identity.get("symbol") or row.get("symbol"),
                    "candidate_id": identity.get("candidate_id"),
                    "fatal_reasons": row.get("fatal_reasons") or [],
                    "pretrade_cost_model_status": cost_context.get("pretrade_cost_model_status") or cost_packet.get("status"),
                    "total_cost_r": cost_packet.get("total_cost_r"),
                    "max_total_cost_r": cost_packet.get("max_total_cost_r"),
                    "spread_r": cost_packet.get("spread_r"),
                }
            )
    return {
        "line_count": len(rows),
        "window_row_count": len(window),
        "parse_error_count": len(errors),
        "parse_errors_sample": errors[:5],
        "action_counts": compact_counts(action_counts),
        "fatal_reason_counts": compact_counts(fatal_reasons),
        "warning_reason_counts": compact_counts(warning_reasons),
        "symbol_counts": compact_counts(symbols),
        "selected_cell_counts": compact_counts(selected_cells),
        "max_total_cost_r": max(total_costs) if total_costs else None,
        "blocked_examples": blocked_examples[-12:],
    }


def summarize_lifecycle(rows: list[dict[str, Any]], errors: list[dict[str, Any]], start: datetime) -> dict[str, Any]:
    window = rows_since(rows, start)
    stage_counts = Counter(str(row.get("stage") or "missing") for row in window)
    status_counts = Counter(str(row.get("status") or "missing") for row in window)
    runtime_namespace_counts = Counter(str(row.get("runtime_namespace") or "missing") for row in window)
    success_counts = Counter()
    broker_real_ready = Counter()
    for row in window:
        result = row.get("result") if isinstance(row.get("result"), dict) else {}
        if "success" in result:
            success_counts[str(result.get("success"))] += 1
        if "broker_real_entry_label_ready" in row:
            broker_real_ready[str(row.get("broker_real_entry_label_ready"))] += 1
    return {
        "line_count": len(rows),
        "window_row_count": len(window),
        "parse_error_count": len(errors),
        "parse_errors_sample": errors[:5],
        "stage_counts": compact_counts(stage_counts),
        "status_counts": compact_counts(status_counts),
        "runtime_namespace_counts": compact_counts(runtime_namespace_counts),
        "runtime_result_success_counts": compact_counts(success_counts),
        "broker_real_entry_label_ready_counts": compact_counts(broker_real_ready),
    }


def summarize_trade_records() -> dict[str, Any]:
    rows: list[dict[str, Any]] = []
    parse_errors: list[dict[str, Any]] = []
    if not TRADE_RECORD_ROOT.exists():
        return {"root": rel(TRADE_RECORD_ROOT), "row_count": 0, "parse_error_count": 0, "missing_root": True}
    for path in sorted(TRADE_RECORD_ROOT.glob("*/trade_records/*.json")):
        try:
            payload = read_json(path)
        except Exception as exc:
            parse_errors.append({"path": rel(path), "error": repr(exc)})
            continue
        if isinstance(payload, dict):
            payload["_path"] = rel(path)
            payload["_namespace"] = path.parents[1].name
            rows.append(payload)
    lifecycle_counts = Counter(str(row.get("trade_lifecycle_status") or row.get("status") or "missing") for row in rows)
    joinability_counts = Counter(
        str(
            trade_record_field(row, "trade_record_joinability_status")
            or trade_record_field(row, "joinability_status")
            or trade_record_field(row, "runtime_learning_joinability_status")
            or "missing"
        )
        for row in rows
    )
    nonclosed = [
        {
            "namespace": row.get("_namespace"),
            "path": row.get("_path"),
            "symbol": trade_record_field(row, "symbol"),
            "sleeve": trade_record_field(row, "sleeve"),
            "candidate_id": trade_record_field(row, "candidate_id"),
            "trade_lifecycle_status": row.get("trade_lifecycle_status"),
            "joinability_status": (
                trade_record_field(row, "trade_record_joinability_status")
                or trade_record_field(row, "joinability_status")
                or trade_record_field(row, "runtime_learning_joinability_status")
            ),
            "decision_bar_iso": trade_record_field(row, "decision_bar_iso"),
            "placement_observed_at_utc": trade_record_field(row, "placement_observed_at_utc"),
        }
        for row in rows
        if str(row.get("trade_lifecycle_status") or "").lower() not in {"closed", "broker_closed"}
    ]
    return {
        "root": rel(TRADE_RECORD_ROOT),
        "row_count": len(rows),
        "parse_error_count": len(parse_errors),
        "parse_errors_sample": parse_errors[:5],
        "lifecycle_counts": compact_counts(lifecycle_counts),
        "joinability_counts": compact_counts(joinability_counts),
        "nonclosed_count": len(nonclosed),
        "nonclosed_records": nonclosed[:25],
    }


def summarize_placement_ledgers() -> dict[str, Any]:
    try:
        from src.components.ultimate_book.placement_ledger import (
            PLACEMENT_CAPTURE_COMPLETE_STATUS,
            annotate_ticket_placement_completeness,
        )
    except Exception as exc:
        return {"error": repr(exc), "ok": False}
    rows: list[dict[str, Any]] = []
    errors: list[dict[str, Any]] = []
    for path in sorted(TRADE_RECORD_ROOT.glob("*/placed_decisions.jsonl")):
        ledger_rows, ledger_errors = read_jsonl(path)
        errors.extend(ledger_errors)
        for row in ledger_rows:
            material = {key: value for key, value in row.items() if key != "_line_no"}
            annotated = annotate_ticket_placement_completeness(material)
            rows.append(
                {
                    "namespace": path.parent.name,
                    "path": rel(path),
                    "line": row.get("_line_no"),
                    "symbol": annotated.get("symbol"),
                    "sleeve": annotated.get("sleeve"),
                    "candidate_id": annotated.get("candidate_id"),
                    "ticket": annotated.get("ticket"),
                    "decision_bar_iso": annotated.get("decision_bar_iso"),
                    "placement_source_completeness_status": annotated.get("placement_source_completeness_status"),
                    "placement_source_missing_fields": annotated.get("placement_source_missing_fields") or [],
                }
            )
    incomplete = [
        row for row in rows
        if row.get("placement_source_completeness_status") != PLACEMENT_CAPTURE_COMPLETE_STATUS
    ]
    return {
        "ledger_count": len(list(TRADE_RECORD_ROOT.glob("*/placed_decisions.jsonl"))),
        "row_count": len(rows),
        "parse_error_count": len(errors),
        "incomplete_ticket_row_count": len(incomplete),
        "incomplete_ticket_rows": incomplete[:20],
        "ok": not errors and not incomplete,
    }


def classify_observations(sample: dict[str, Any]) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    issues: list[dict[str, Any]] = []
    opportunities: list[dict[str, Any]] = []
    packet = sample["packet_log"]
    launcher = sample["launcher_log"]
    execution = sample["execution_manager"]
    lifecycle = sample["broker_lifecycle"]
    trade_records = sample["trade_records"]
    placement = sample["placement_ledgers"]

    if packet["parse_error_count"] or packet["validation_issue_count"]:
        issues.append({"id": "PACKET-INTEGRITY", "severity": "high", "detail": "Runtime-learning packet parse or validation issues present."})
    if placement.get("incomplete_ticket_row_count"):
        issues.append({"id": "PLACEMENT-CAPTURE", "severity": "high", "detail": "Incomplete ticket placement rows detected."})
    if trade_records.get("parse_error_count"):
        issues.append({"id": "TRADE-RECORD-PARSE", "severity": "medium", "detail": "Trade-record parse errors detected."})
    if lifecycle["parse_error_count"]:
        issues.append({"id": "BROKER-LIFECYCLE-PARSE", "severity": "medium", "detail": "Broker lifecycle log parse errors detected."})
    fatal_counts = execution.get("fatal_reason_counts") or {}
    if fatal_counts:
        opportunities.append(
            {
                "id": "AI-COST-GATE-REVIEW",
                "class": "ai_companion_candidate",
                "detail": "Execution Manager V4 blocked candidates; an AI companion can summarize cost-vs-edge context and propose source-bound research follow-up without overriding gates.",
                "evidence": fatal_counts,
            }
        )
    unsupported = launcher.get("broker_unsupported_symbol_counts") or {}
    if unsupported:
        opportunities.append(
            {
                "id": "AI-BROKER-SYMBOL-MAP-HYGIENE",
                "class": "ai_companion_candidate",
                "detail": "Repeated unsupported or missing-profile symbols are appearing in candidate generation; companion can rank whether to add broker profile support, exclude, or route to replay/source validation.",
                "evidence": unsupported,
            }
        )
    no_candidate_cycles = int((launcher.get("reason_counts") or {}).get("no_candidates_this_bar", 0))
    if no_candidate_cycles:
        opportunities.append(
            {
                "id": "AI-NO-CANDIDATE-STATE-EXPLANATION",
                "class": "selection_awareness",
                "detail": "Cycles with no candidates should be explained by market/session/regime state, not treated as blank time. Companion can build a causal digest of why no sleeve qualified.",
                "evidence": {"no_candidate_cycles": no_candidate_cycles},
            }
        )
    governor_counts = launcher.get("governor_reason_counts") or {}
    if "derisking_into_maxdd_wall" in governor_counts:
        opportunities.append(
            {
                "id": "AI-RISK-GOVERNOR-AWARENESS",
                "class": "risk_awareness",
                "detail": "The governor is repeatedly derisking near the max-drawdown wall. Companion can explain current opportunity throttling and detect when selection pressure is due to risk budget rather than signal absence.",
                "evidence": {
                    "count": governor_counts.get("derisking_into_maxdd_wall"),
                    "size_cap_multiplier_min": launcher.get("size_cap_multiplier_min"),
                    "available_gross_risk_pct_min": launcher.get("available_gross_risk_pct_min"),
                },
            }
        )
    joinability_counts = packet.get("joinability_counts") or {}
    if int(joinability_counts.get("ticket_policy_joinable", 0) or 0) > 0:
        opportunities.append(
            {
                "id": "AI-LEGACY-ATTRIBUTION-BOUNDARY",
                "class": "evidence_hygiene",
                "detail": "Legacy ticket-policy-only rows remain in management packets; companion should keep them separate from fully joinable candidate/decision/policy rows.",
                "evidence": {"ticket_policy_joinable": joinability_counts.get("ticket_policy_joinable")},
            }
        )
    if lifecycle.get("broker_real_entry_label_ready_counts"):
        opportunities.append(
            {
                "id": "AI-ENTRY-QUALITY-FORENSICS",
                "class": "learning_opportunity",
                "detail": "Broker-real entry lifecycle packets are available. Companion can turn reconciled fill, cost, and lifecycle evidence into replay/forward learning tasks.",
                "evidence": lifecycle.get("broker_real_entry_label_ready_counts"),
            }
        )
    return issues, opportunities


def collect_sample(start: datetime, prior_lines: dict[str, int], sample_index: int) -> dict[str, Any]:
    now = utc_now()
    packet_rows, packet_errors = read_jsonl(PACKET_LOG)
    launcher_rows, launcher_errors = read_jsonl(LAUNCHER_LOG)
    execution_rows, execution_errors = read_jsonl(EXECUTION_LOG)
    lifecycle_rows, lifecycle_errors = read_jsonl(LIFECYCLE_LOG)
    line_counts = {
        "packet": max_line(packet_rows),
        "launcher": max_line(launcher_rows),
        "execution": max_line(execution_rows),
        "lifecycle": max_line(lifecycle_rows),
    }
    deltas = {
        "packet_new_rows": len(rows_after_line(packet_rows, prior_lines.get("packet", 0))),
        "launcher_new_rows": len(rows_after_line(launcher_rows, prior_lines.get("launcher", 0))),
        "execution_new_rows": len(rows_after_line(execution_rows, prior_lines.get("execution", 0))),
        "lifecycle_new_rows": len(rows_after_line(lifecycle_rows, prior_lines.get("lifecycle", 0))),
    }
    sample = {
        "schema": "gtos.vps_runtime_ai_companion_micro_observation.sample.v1",
        "sample_index": sample_index,
        "observed_at_utc": iso(now),
        "window_start_utc": iso(start),
        "runtime_effect_boundary": "read_only_log_pipeline_state_parse_no_broker_mutation_no_order_action_no_runtime_reload",
        "source_paths": {
            "packet_log": rel(PACKET_LOG),
            "launcher_log": rel(LAUNCHER_LOG),
            "execution_manager_log": rel(EXECUTION_LOG),
            "broker_lifecycle_log": rel(LIFECYCLE_LOG),
            "trade_record_root": rel(TRADE_RECORD_ROOT),
        },
        "line_counts": line_counts,
        "line_deltas_since_prior_sample": deltas,
        "packet_log": summarize_packets(packet_rows, packet_errors, start),
        "launcher_log": summarize_launcher(launcher_rows, launcher_errors, start),
        "execution_manager": summarize_execution(execution_rows, execution_errors, start),
        "broker_lifecycle": summarize_lifecycle(lifecycle_rows, lifecycle_errors, start),
        "trade_records": summarize_trade_records(),
        "placement_ledgers": summarize_placement_ledgers(),
    }
    issues, opportunities = classify_observations(sample)
    sample["issues"] = issues
    sample["opportunities"] = opportunities
    sample["ok"] = not any(issue.get("severity") == "high" for issue in issues)
    return sample


def synthesize(samples: list[dict[str, Any]], start: datetime, end: datetime, requested_end: datetime) -> dict[str, Any]:
    issue_counts = Counter()
    opportunity_counts = Counter()
    packet_event_counts = Counter()
    launcher_reason_counts = Counter()
    skipped_reason_counts = Counter()
    execution_fatal_counts = Counter()
    placed_symbols = Counter()
    placed_sleeves = Counter()
    for sample in samples:
        for issue in sample.get("issues") or []:
            issue_counts[str(issue.get("id"))] += 1
        for opportunity in sample.get("opportunities") or []:
            opportunity_counts[str(opportunity.get("id"))] += 1
        packet_event_counts.update(sample.get("packet_log", {}).get("event_counts") or {})
        launcher_reason_counts.update(sample.get("launcher_log", {}).get("reason_counts") or {})
        skipped_reason_counts.update(sample.get("launcher_log", {}).get("skipped_reason_counts") or {})
        execution_fatal_counts.update(sample.get("execution_manager", {}).get("fatal_reason_counts") or {})
        placed_symbols.update(sample.get("launcher_log", {}).get("placed_symbol_counts") or {})
        placed_sleeves.update(sample.get("launcher_log", {}).get("placed_sleeve_counts") or {})
    latest = samples[-1] if samples else {}
    recommendations = [
        {
            "id": "AI_COMPANION_SELECTION_STATE_DIGEST",
            "priority": "high",
            "recommendation": "Build a read-only companion digest that explains every cycle as no-candidate, candidate-rejected, cost-blocked, admitted, placed, managed, or closed, with the causal reason and evidence path.",
        },
        {
            "id": "AI_COMPANION_COST_AND_SWAP_CONTEXT",
            "priority": "high",
            "recommendation": "Have the companion review cost/swap/spread blocks as research signals and produce symbol/session thresholds for later replay, without overriding Execution Manager V4.",
        },
        {
            "id": "AI_COMPANION_RISK_GOVERNOR_CONTEXT",
            "priority": "medium",
            "recommendation": "Surface when selection is being shaped by drawdown-wall derisking so low activity is not misread as lack of market opportunity.",
        },
        {
            "id": "AI_COMPANION_BROKER_PROFILE_QUEUE",
            "priority": "medium",
            "recommendation": "Queue repeated unsupported-symbol or missing-profile candidates into a broker-profile/source-validation lane.",
        },
        {
            "id": "AI_COMPANION_BROKER_REAL_LEARNING_QUEUE",
            "priority": "medium",
            "recommendation": "Transform reconciled lifecycle/fill/cost packets into forward-learning tasks for entry quality, time-stop behavior, and opportunity cost.",
        },
    ]
    return {
        "schema": "gtos.vps_runtime_ai_companion_micro_observation.synthesis.v1",
        "started_at_utc": iso(start),
        "ended_at_utc": iso(end),
        "requested_end_utc": iso(requested_end),
        "sample_count": len(samples),
        "runtime_effect_boundary": "read_only_log_pipeline_state_parse_no_broker_mutation_no_order_action_no_runtime_reload",
        "ok": latest.get("ok") if latest else False,
        "issue_counts": compact_counts(issue_counts),
        "opportunity_counts": compact_counts(opportunity_counts),
        "packet_event_counts_accumulated_across_samples": compact_counts(packet_event_counts),
        "launcher_reason_counts_accumulated_across_samples": compact_counts(launcher_reason_counts),
        "skipped_reason_counts_accumulated_across_samples": compact_counts(skipped_reason_counts),
        "execution_fatal_counts_accumulated_across_samples": compact_counts(execution_fatal_counts),
        "placed_symbol_counts_accumulated_across_samples": compact_counts(placed_symbols),
        "placed_sleeve_counts_accumulated_across_samples": compact_counts(placed_sleeves),
        "latest_status": latest,
        "recommendations": recommendations,
    }


def write_markdown(synthesis: dict[str, Any]) -> None:
    latest = synthesis.get("latest_status") or {}
    launcher = latest.get("launcher_log") or {}
    packet = latest.get("packet_log") or {}
    execution = latest.get("execution_manager") or {}
    trade_records = latest.get("trade_records") or {}
    placement = latest.get("placement_ledgers") or {}
    lines = [
        "# VPS Runtime AI Companion Micro Observation",
        "",
        f"Started: `{synthesis.get('started_at_utc')}`",
        f"Ended: `{synthesis.get('ended_at_utc')}`",
        f"Samples: `{synthesis.get('sample_count')}`",
        f"Runtime effect boundary: `{synthesis.get('runtime_effect_boundary')}`",
        f"OK: `{synthesis.get('ok')}`",
        "",
        "## Latest Stability",
        "",
        f"- Packet rows in window: `{packet.get('window_row_count')}`; parse errors: `{packet.get('parse_error_count')}`; validation issues: `{packet.get('validation_issue_count')}`.",
        f"- Launcher rows in window: `{launcher.get('window_row_count')}`; placed count: `{launcher.get('placed_count')}`; skipped reasons: `{launcher.get('skipped_reason_counts')}`.",
        f"- Execution Manager rows in window: `{execution.get('window_row_count')}`; fatal reasons: `{execution.get('fatal_reason_counts')}`.",
        f"- Trade records: `{trade_records.get('row_count')}` total, `{trade_records.get('nonclosed_count')}` nonclosed; joinability: `{trade_records.get('joinability_counts')}`.",
        f"- Placement ledgers: `{placement.get('row_count')}` rows, incomplete ticket rows: `{placement.get('incomplete_ticket_row_count')}`.",
        "",
        "## Observed Intelligence Themes",
        "",
    ]
    for key, value in synthesis.get("opportunity_counts", {}).items():
        lines.append(f"- `{key}` observed in `{value}` samples.")
    if not synthesis.get("opportunity_counts"):
        lines.append("- No repeated opportunity themes were classified.")
    lines.extend(["", "## AI Companion Recommendations", ""])
    for rec in synthesis.get("recommendations") or []:
        lines.append(f"- `{rec.get('priority')}` `{rec.get('id')}`: {rec.get('recommendation')}")
    lines.extend(["", "## Residual Issues", ""])
    if synthesis.get("issue_counts"):
        for key, value in synthesis.get("issue_counts", {}).items():
            lines.append(f"- `{key}` observed in `{value}` samples.")
    else:
        lines.append("- No high-severity read-only observation issues were classified.")
    lines.append("")
    SYNTHESIS_MD.write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description="Read-only one-hour GTOS runtime micro-observer.")
    parser.add_argument("--duration-minutes", type=float, default=60.0)
    parser.add_argument("--interval-seconds", type=float, default=60.0)
    parser.add_argument("--reset", action="store_true", help="Remove prior observer outputs before starting.")
    args = parser.parse_args()

    if args.reset:
        for path in (SAMPLE_LEDGER, LATEST_STATUS, SYNTHESIS_JSON, SYNTHESIS_MD):
            if path.exists():
                path.unlink()

    start = utc_now()
    requested_end = start + timedelta(minutes=args.duration_minutes)
    prior_lines = {"packet": 0, "launcher": 0, "execution": 0, "lifecycle": 0}
    samples: list[dict[str, Any]] = []
    sample_index = 0
    while True:
        sample_index += 1
        sample = collect_sample(start, prior_lines, sample_index)
        samples.append(sample)
        prior_lines = dict(sample["line_counts"])
        append_jsonl(SAMPLE_LEDGER, sample)
        write_json(LATEST_STATUS, sample)
        print(
            json.dumps(
                {
                    "sample_index": sample_index,
                    "observed_at_utc": sample["observed_at_utc"],
                    "ok": sample["ok"],
                    "packet_window_rows": sample["packet_log"]["window_row_count"],
                    "launcher_window_rows": sample["launcher_log"]["window_row_count"],
                    "opportunity_count": len(sample["opportunities"]),
                    "issue_count": len(sample["issues"]),
                },
                sort_keys=True,
            ),
            flush=True,
        )
        if utc_now() >= requested_end:
            break
        remaining = (requested_end - utc_now()).total_seconds()
        time.sleep(max(0.0, min(args.interval_seconds, remaining)))

    synthesis = synthesize(samples, start=start, end=utc_now(), requested_end=requested_end)
    write_json(SYNTHESIS_JSON, synthesis)
    write_markdown(synthesis)
    print(json.dumps({"ok": synthesis["ok"], "samples": synthesis["sample_count"], "synthesis": str(SYNTHESIS_JSON)}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
