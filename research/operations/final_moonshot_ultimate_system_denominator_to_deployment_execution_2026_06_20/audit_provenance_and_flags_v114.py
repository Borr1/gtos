#!/usr/bin/env python3
"""B0 baseline audit for V114 ultimate-system repair sequencing.

This script is intentionally behavior-neutral.  It streams existing V110B and
V111 broad replay ledgers and writes compact counts that later batches can move
without re-reading multi-GB artifacts in the main session.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable, Mapping


ROUTE_DIR = Path(__file__).resolve().parent

RUN_PREFIXES = {
    "V110B": (
        "BROAD_LIVE_AS_IF_REPLAY_V110B_ROUTER_ORIGIN_ROLE_SCOPE_REPAIR_"
        "20260601_20260619_REPAIRED_ONLY_COMPACT_FULLGRID"
    ),
    "V111": (
        "BROAD_LIVE_AS_IF_REPLAY_V111_SCHEDULER_FILLABILITY_TRUTH_REPAIR_"
        "20260601_20260619_REPAIRED_ONLY_COMPACT_FULLGRID"
    ),
}

LEDGER_SUFFIXES = {
    "candidate_index": "CANDIDATE_INDEX_LEDGER.jsonl",
    "order": "ORDER_LEDGER.jsonl",
    "trade": "TRADE_LEDGER.jsonl",
}

AUDIT_OUTPUT = "AUDIT_PROVENANCE_AND_FLAGS_V114.json"
BROKER_COST_OUTPUT = "BROKER_COST_REFUSAL_HISTOGRAM_V111.json"


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def boolish(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    if value is None:
        return False
    if isinstance(value, (int, float)):
        return value != 0
    return str(value).strip().lower() in {"1", "true", "yes", "y", "on", "passed", "pass", "allowed", "eligible"}


def number(value: Any) -> float | None:
    if value in (None, ""):
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def first_present(*values: Any) -> Any:
    for value in values:
        if value not in (None, "", [], {}):
            return value
    return None


def mapping(value: Any) -> Mapping[str, Any]:
    return value if isinstance(value, Mapping) else {}


def parse_dt(value: Any) -> datetime | None:
    if value in (None, ""):
        return None
    text = str(value).strip()
    if not text:
        return None
    if text.endswith("Z"):
        text = text[:-1] + "+00:00"
    try:
        parsed = datetime.fromisoformat(text)
    except ValueError:
        return None
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def json_dumps_key(parts: Iterable[Any]) -> str:
    return json.dumps([str(part or "") for part in parts], separators=(",", ":"), sort_keys=False)


def ledger_path(prefix: str, suffix: str) -> Path:
    return ROUTE_DIR / f"{prefix}_{suffix}"


def file_sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def iter_jsonl(path: Path) -> Iterable[dict[str, Any]]:
    with path.open("r", encoding="utf-8") as handle:
        for line_no, line in enumerate(handle, 1):
            line = line.strip()
            if not line:
                continue
            try:
                row = json.loads(line)
            except json.JSONDecodeError as exc:
                raise RuntimeError(f"{path}:{line_no}: invalid JSONL: {exc}") from exc
            if isinstance(row, dict):
                yield row


def materialized_flag(row: Mapping[str, Any]) -> bool:
    return any(
        boolish(row.get(key))
        for key in (
            "selector_action_materialized_from_scheduler",
            "scheduler_materialization_selector_action_materialized",
            "materialized_selector_action_from_scheduler",
            "selector_materialization_applied",
            "selector_finalizer_replay_override_applied",
            "source_bound_router_refusal_open_reduced_materialization_applied",
        )
    )


def original_selector_action(row: Mapping[str, Any]) -> Any:
    return first_present(
        row.get("scheduler_materialization_original_selector_action"),
        row.get("original_selector_action"),
        row.get("raw_selector_action"),
        row.get("selector_action_origin"),
    )


def effective_selector_action(row: Mapping[str, Any]) -> Any:
    return first_present(
        row.get("effective_selector_action"),
        row.get("scheduler_materialization_selector_action"),
        row.get("selector_action"),
    )


def fill_floor_authority(row: Mapping[str, Any]) -> Mapping[str, Any]:
    candidates = (
        row.get("selector_reduce_risk_package_fill_floor_authority"),
        row.get("package_fill_floor_authority"),
        row.get("risk_finalizer_package_fill_floor_authority"),
    )
    for candidate in candidates:
        if isinstance(candidate, Mapping):
            return candidate
    score_components = mapping(row.get("score_components"))
    candidate = score_components.get("selector_reduce_risk_package_fill_floor_authority")
    return candidate if isinstance(candidate, Mapping) else {}


def unresolved_fill_floor_failures(authority: Mapping[str, Any]) -> list[Any]:
    value = first_present(
        authority.get("authority_failures"),
        authority.get("unresolved_failures"),
        authority.get("unresolved_package_fill_floor_failures"),
    )
    if isinstance(value, list):
        return value
    if isinstance(value, tuple):
        return list(value)
    if value in (None, ""):
        return []
    return [value]


def raw_fill_floor_failures(authority: Mapping[str, Any]) -> list[Any]:
    value = first_present(
        authority.get("failures"),
        authority.get("raw_failures"),
        authority.get("raw_package_fill_floor_failures"),
    )
    if isinstance(value, list):
        return value
    if isinstance(value, tuple):
        return list(value)
    if value in (None, ""):
        return []
    return [value]


def replacement_reallocation_eligible(row: Mapping[str, Any]) -> Any:
    quality = mapping(row.get("replacement_reallocation_quality"))
    return first_present(
        quality.get("eligible_for_reallocation_promotion"),
        row.get("replacement_reallocation_quality_eligible"),
        row.get("eligible_for_reallocation_promotion"),
    )


def nested_cost_packet(row: Mapping[str, Any]) -> Mapping[str, Any]:
    for key in (
        "pretrade_broker_net_cost_packet",
        "broker_net_pretrade_cost_packet",
        "normalized_pretrade_cost_packet",
        "pretrade_cost_packet",
    ):
        value = row.get(key)
        if isinstance(value, Mapping):
            return value
    return {}


def cost_refused(row: Mapping[str, Any]) -> bool:
    packet = nested_cost_packet(row)
    status = str(first_present(row.get("pretrade_cost_packet_status"), packet.get("status")) or "").upper()
    return (
        status == "REFUSED"
        or boolish(row.get("broker_net_pretrade_cost_packet_refused"))
        or boolish(row.get("broker_cost_packet_refused"))
        or boolish(packet.get("refused"))
    )


def cost_refusal_reason(row: Mapping[str, Any]) -> str:
    return "|".join(cost_refusal_reasons(row))


def listish(value: Any) -> list[Any]:
    if value in (None, "", [], {}):
        return []
    if isinstance(value, (list, tuple, set)):
        return list(value)
    return [value]


def normalize_refusal_family(reason: Any) -> str:
    text = str(reason or "").strip()
    if not text:
        return "unknown_refusal_reason"
    return text.split(":", 1)[0] or "unknown_refusal_reason"


def cost_refusal_reasons(row: Mapping[str, Any]) -> list[str]:
    packet = nested_cost_packet(row)
    raw_reasons = first_present(
        row.get("pretrade_cost_refusal_reasons"),
        row.get("broker_net_pretrade_cost_refusal_reasons"),
        row.get("broker_cost_refusal_reasons"),
        packet.get("refusal_reasons"),
        packet.get("reasons"),
    )
    reasons = [
        str(item).strip()
        for item in listish(raw_reasons)
        if item not in (None, "")
    ]
    if reasons:
        return reasons
    reason = first_present(
        row.get("broker_cost_executable_block_reason"),
        row.get("pretrade_cost_packet_refusal_reason"),
        row.get("broker_net_pretrade_cost_refusal_reason"),
        row.get("broker_net_cost_refusal_reason"),
        row.get("pretrade_cost_packet_rejection_reason"),
        row.get("cost_refusal_reason"),
        row.get("cost_block_reason"),
        packet.get("refusal_reason"),
        packet.get("reason"),
        packet.get("block_reason"),
    )
    reasons = [
        str(item).strip()
        for item in listish(reason)
        if item not in (None, "")
    ]
    return reasons or ["unknown_refusal_reason"]


def spread_floor_source(row: Mapping[str, Any]) -> str:
    packet = nested_cost_packet(row)
    return str(
        first_present(
            row.get("spread_floor_source"),
            row.get("tick_spread_floor_source"),
            row.get("broker_cost_spread_floor_source"),
            row.get("measured_tick_spread_floor_source"),
            packet.get("spread_floor_source"),
            packet.get("tick_spread_floor_source"),
            packet.get("measured_tick_spread_floor_source"),
            "unknown_spread_floor_source",
        )
    )


def spread_floor_source_status(row: Mapping[str, Any]) -> str:
    source = spread_floor_source(row)
    if not source or source == "unknown_spread_floor_source":
        return "missing_spread_floor_source"
    return "present_spread_floor_source"


def cost_quality_source(row: Mapping[str, Any]) -> str:
    packet = nested_cost_packet(row)
    return str(
        first_present(
            row.get("cost_quality_source"),
            row.get("broker_cost_quality_source"),
            row.get("broker_calibrated_cost_source"),
            packet.get("cost_quality_source"),
            packet.get("broker_cost_quality_source"),
            packet.get("cost_source"),
            "missing_cost_quality_source",
        )
    )


def session_key(row: Mapping[str, Any]) -> str:
    return str(
        first_present(
            row.get("session"),
            row.get("route_session"),
            row.get("authority_session"),
            row.get("kill_zone"),
            "unknown_session",
        )
    )


def audit_run(run_id: str, prefix: str) -> dict[str, Any]:
    ledgers: dict[str, dict[str, Any]] = {}
    aggregate = {
        "rows": 0,
        "selector_action_origin_effective_mismatch_rows": 0,
        "selector_action_origin_effective_mismatch_without_materialized_flag_rows": 0,
        "stale_cap_release_zero_risk_rows": 0,
        "expired_unfilled_fallback_starved_rows": 0,
        "r_accounting_drift_rows": 0,
        "raw_failure_poisoning_rows": 0,
        "replacement_reallocation_quality_eligible_histogram": Counter(),
    }
    examples: dict[str, list[dict[str, Any]]] = defaultdict(list)

    for ledger_name, suffix in LEDGER_SUFFIXES.items():
        path = ledger_path(prefix, suffix)
        ledger_stats: dict[str, Any] = {
            "path": str(path.relative_to(ROUTE_DIR)),
            "exists": path.exists(),
            "rows": 0,
            "selector_action_origin_effective_mismatch_rows": 0,
            "selector_action_origin_effective_mismatch_without_materialized_flag_rows": 0,
            "stale_cap_release_zero_risk_rows": 0,
            "expired_unfilled_fallback_starved_rows": 0,
            "r_accounting_drift_rows": 0,
            "raw_failure_poisoning_rows": 0,
            "replacement_reallocation_quality_eligible_histogram": Counter(),
        }
        if not path.exists():
            ledgers[ledger_name] = ledger_stats
            continue
        ledger_stats["sha256"] = file_sha256(path)
        for row in iter_jsonl(path):
            ledger_stats["rows"] += 1
            aggregate["rows"] += 1

            original = original_selector_action(row)
            effective = effective_selector_action(row)
            if original not in (None, "") and effective not in (None, "") and str(original) != str(effective):
                ledger_stats["selector_action_origin_effective_mismatch_rows"] += 1
                aggregate["selector_action_origin_effective_mismatch_rows"] += 1
                if not materialized_flag(row):
                    ledger_stats["selector_action_origin_effective_mismatch_without_materialized_flag_rows"] += 1
                    aggregate["selector_action_origin_effective_mismatch_without_materialized_flag_rows"] += 1
                    if len(examples["provenance_collapse"]) < 10:
                        examples["provenance_collapse"].append(
                            {
                                "run": run_id,
                                "ledger": ledger_name,
                                "candidate_id": row.get("candidate_id"),
                                "decision_time_utc": row.get("decision_time_utc"),
                                "selector_action_origin": original,
                                "effective_selector_action": effective,
                                "selector_action": row.get("selector_action"),
                            }
                        )

            approved = number(first_present(row.get("approved_risk_pct"), row.get("scheduler_approved_risk_pct"), row.get("final_approved_risk_pct")))
            if boolish(row.get("risk_cap_released_for_package_fill_floor")) and (approved is None or approved <= 0):
                ledger_stats["stale_cap_release_zero_risk_rows"] += 1
                aggregate["stale_cap_release_zero_risk_rows"] += 1

            if ledger_name == "order":
                order_status = str(row.get("order_status") or "")
                fill_status = str(row.get("fill_status") or "")
                expired = order_status == "expired_unfilled" or fill_status == "expired_unfilled"
                fallback_time = parse_dt(first_present(row.get("fallback_time_utc"), row.get("guarded_market_fallback_time_utc")))
                expiry = parse_dt(row.get("expiry_utc"))
                fallback_status = str(row.get("guarded_market_fallback_status") or "")
                if expired and ((fallback_time is not None and expiry is not None and fallback_time >= expiry) or fallback_status == "eligible"):
                    ledger_stats["expired_unfilled_fallback_starved_rows"] += 1
                    aggregate["expired_unfilled_fallback_starved_rows"] += 1
                    if len(examples["fallback_starved_expiry"]) < 10:
                        examples["fallback_starved_expiry"].append(
                            {
                                "run": run_id,
                                "candidate_id": row.get("candidate_id"),
                                "decision_time_utc": row.get("decision_time_utc"),
                                "order_status": order_status,
                                "fill_status": fill_status,
                                "fallback_time_utc": first_present(row.get("fallback_time_utc"), row.get("guarded_market_fallback_time_utc")),
                                "expiry_utc": row.get("expiry_utc"),
                                "guarded_market_fallback_status": fallback_status,
                            }
                        )

            if ledger_name == "trade":
                gross = number(row.get("gross_r"))
                cost = number(first_present(row.get("expected_cost_r"), row.get("cost_r")))
                net = number(first_present(row.get("net_proxy_r"), row.get("net_r")))
                if gross is not None and cost is not None and net is not None and abs(gross - cost - net) > 0.000001:
                    ledger_stats["r_accounting_drift_rows"] += 1
                    aggregate["r_accounting_drift_rows"] += 1
                    if len(examples["r_accounting_drift"]) < 10:
                        examples["r_accounting_drift"].append(
                            {
                                "run": run_id,
                                "candidate_id": row.get("candidate_id"),
                                "decision_time_utc": row.get("decision_time_utc"),
                                "gross_r": gross,
                                "expected_cost_r": cost,
                                "net_proxy_r": net,
                                "drift": gross - cost - net,
                            }
                        )

            authority = fill_floor_authority(row)
            if authority:
                raw_failures = raw_fill_floor_failures(authority)
                unresolved = unresolved_fill_floor_failures(authority)
                if raw_failures and raw_failures != unresolved and not unresolved:
                    ledger_stats["raw_failure_poisoning_rows"] += 1
                    aggregate["raw_failure_poisoning_rows"] += 1

            eligible = replacement_reallocation_eligible(row)
            eligible_key = str(eligible if eligible not in (None, "") else "missing")
            ledger_stats["replacement_reallocation_quality_eligible_histogram"][eligible_key] += 1
            aggregate["replacement_reallocation_quality_eligible_histogram"][eligible_key] += 1

        for key in (
            "replacement_reallocation_quality_eligible_histogram",
        ):
            ledger_stats[key] = dict(sorted(ledger_stats[key].items()))
        ledgers[ledger_name] = ledger_stats

    aggregate["replacement_reallocation_quality_eligible_histogram"] = dict(
        sorted(aggregate["replacement_reallocation_quality_eligible_histogram"].items())
    )
    return {
        "run_id": run_id,
        "prefix": prefix,
        "aggregate": aggregate,
        "ledgers": ledgers,
        "examples": examples,
    }


def broker_cost_refusal_histogram(prefix: str) -> dict[str, Any]:
    path = ledger_path(prefix, LEDGER_SUFFIXES["candidate_index"])
    rows = 0
    refused_rows = 0
    refused_reason_instances = 0
    histogram: Counter[str] = Counter()
    examples: dict[str, list[dict[str, Any]]] = defaultdict(list)
    if not path.exists():
        return {"path": str(path.relative_to(ROUTE_DIR)), "exists": False}
    for row in iter_jsonl(path):
        rows += 1
        if not cost_refused(row):
            continue
        refused_rows += 1
        reasons = cost_refusal_reasons(row)
        refused_reason_instances += len(reasons)
        for reason in reasons:
            key_parts = (
                row.get("symbol") or "unknown_symbol",
                session_key(row),
                normalize_refusal_family(reason),
                spread_floor_source(row),
                spread_floor_source_status(row),
                cost_quality_source(row),
            )
            key = json_dumps_key(key_parts)
            histogram[key] += 1
            if len(examples[key]) < 3:
                examples[key].append(
                    {
                        "candidate_id": row.get("candidate_id"),
                        "decision_time_utc": row.get("decision_time_utc"),
                        "symbol": row.get("symbol"),
                        "session": session_key(row),
                        "reason": reason,
                        "reason_family": normalize_refusal_family(reason),
                        "all_reasons": reasons,
                        "spread_floor_source": spread_floor_source(row),
                        "spread_floor_source_status": spread_floor_source_status(row),
                        "cost_quality_source": cost_quality_source(row),
                        "pretrade_cost_packet_status": row.get("pretrade_cost_packet_status"),
                        "candidate_cost_r_fallback_is_authority": row.get("candidate_cost_r_fallback_is_authority"),
                    }
                )
    items = []
    for key, count in histogram.most_common():
        (
            symbol,
            session,
            reason_family,
            source,
            source_status,
            quality_source,
        ) = json.loads(key)
        items.append(
            {
                "symbol": symbol,
                "session": session,
                "refusal_reason_family": reason_family,
                "spread_floor_source": source,
                "spread_floor_source_status": source_status,
                "cost_quality_source": quality_source,
                "count": count,
                "examples": examples[key],
            }
        )
    return {
        "path": str(path.relative_to(ROUTE_DIR)),
        "exists": True,
        "sha256": file_sha256(path),
        "rows": rows,
        "refused_rows": refused_rows,
        "refused_reason_instances": refused_reason_instances,
        "histogram_rows": len(items),
        "histogram": items,
    }


def main() -> int:
    global ROUTE_DIR
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--route-dir", type=Path, default=ROUTE_DIR)
    parser.add_argument("--audit-output", default=AUDIT_OUTPUT)
    parser.add_argument("--broker-cost-output", default=BROKER_COST_OUTPUT)
    args = parser.parse_args()

    ROUTE_DIR = args.route_dir.resolve()

    runs = {run_id: audit_run(run_id, prefix) for run_id, prefix in RUN_PREFIXES.items()}
    audit = {
        "schema_version": "v114_b0_provenance_and_flags_audit_v1",
        "generated_at_utc": utc_now(),
        "route": str(ROUTE_DIR),
        "runs": runs,
    }
    audit_path = ROUTE_DIR / args.audit_output
    audit_path.write_text(json.dumps(audit, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    broker_hist = {
        "schema_version": "v114_b0_broker_cost_refusal_histogram_v1",
        "generated_at_utc": audit["generated_at_utc"],
        "run_id": "V111",
        "prefix": RUN_PREFIXES["V111"],
        "candidate_index": broker_cost_refusal_histogram(RUN_PREFIXES["V111"]),
    }
    broker_path = ROUTE_DIR / args.broker_cost_output
    broker_path.write_text(json.dumps(broker_hist, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    print(json.dumps({"audit_output": str(audit_path), "broker_cost_output": str(broker_path)}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
