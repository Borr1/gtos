#!/usr/bin/env python3
from __future__ import annotations

import json
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROUTE = Path(__file__).resolve().parent
REPO_ROOT = ROUTE.parents[2]
LAUNCHER_LOG = REPO_ROOT / "shadow_logs" / "ultimate_book_launcher.jsonl"
SYNTHESIS_JSON = ROUTE / "MICRO_OBSERVATION_SYNTHESIS.json"
DIGEST_JSON = ROUTE / "AI_COMPANION_CYCLE_DIGEST.json"
DIGEST_MD = ROUTE / "AI_COMPANION_CYCLE_DIGEST.md"

BOUNDARY = "read_only_log_pipeline_state_parse_no_broker_mutation_no_order_action_no_runtime_reload"


def parse_dt(value: Any) -> datetime | None:
    if value in (None, ""):
        return None
    try:
        dt = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    except ValueError:
        return None
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)


def iso(dt: datetime | None) -> str | None:
    if dt is None:
        return None
    return dt.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8-sig", errors="ignore") as handle:
        for line_no, line in enumerate(handle, start=1):
            text = line.strip()
            if not text:
                continue
            parsed = json.loads(text)
            if isinstance(parsed, dict):
                parsed["_line_no"] = line_no
                rows.append(parsed)
    return rows


def compact_counts(counter: Counter) -> dict[str, int]:
    return {str(key): int(value) for key, value in sorted(counter.items(), key=lambda item: str(item[0]))}


def classify_cycle(row: dict[str, Any]) -> str:
    placed = [item for item in (row.get("placed") or []) if isinstance(item, dict)]
    skipped = [item for item in (row.get("skipped") or []) if isinstance(item, dict)]
    skipped_reasons = [str(item.get("reason") or "missing") for item in skipped]
    bridge = row.get("bridge") if isinstance(row.get("bridge"), dict) else {}
    if placed:
        return "placed"
    if any(reason == "already_placed_today" for reason in skipped_reasons):
        if any(reason == "profile_missing_instrument_config" for reason in skipped_reasons):
            return "duplicate_protection_with_profile_hygiene"
        return "duplicate_protection"
    if any(reason.startswith("cost_screen_") for reason in skipped_reasons):
        if any(reason == "profile_missing_instrument_config" for reason in skipped_reasons):
            return "cost_screen_with_profile_hygiene"
        return "cost_screen"
    if int(bridge.get("n_candidates_in") or 0) == 0:
        return "no_candidates"
    if skipped and all(reason == "profile_missing_instrument_config" for reason in skipped_reasons):
        return "profile_missing_only"
    return str(row.get("reason") or bridge.get("decision_status") or "unknown")


def skipped_counts(row: dict[str, Any]) -> dict[str, int]:
    counter = Counter()
    for item in row.get("skipped") or []:
        if isinstance(item, dict):
            counter[str(item.get("reason") or "missing")] += 1
    return compact_counts(counter)


def extract_cycle(row: dict[str, Any]) -> dict[str, Any]:
    bridge = row.get("bridge") if isinstance(row.get("bridge"), dict) else {}
    governor = bridge.get("governor") if isinstance(bridge.get("governor"), dict) else {}
    profile_generation = (
        bridge.get("broker_profile_generation")
        if isinstance(bridge.get("broker_profile_generation"), dict)
        else {}
    )
    skipped = [item for item in (row.get("skipped") or []) if isinstance(item, dict)]
    placed = [item for item in (row.get("placed") or []) if isinstance(item, dict)]
    return {
        "ts": row.get("ts"),
        "line": row.get("_line_no"),
        "namespace": row.get("namespace"),
        "cycle_reason": row.get("reason"),
        "terminal_cause": classify_cycle(row),
        "n_candidates_in": bridge.get("n_candidates_in"),
        "n_candidates_after_drop": bridge.get("n_candidates_after_drop"),
        "n_intents": row.get("n_intents"),
        "placed_count": len(placed),
        "placed": placed,
        "skipped_count": len(skipped),
        "skipped_reason_counts": skipped_counts(row),
        "skipped": skipped,
        "governor": {
            "allow_new_entries": governor.get("allow_new_entries"),
            "reason": governor.get("reason"),
            "size_cap_multiplier": governor.get("size_cap_multiplier"),
            "available_gross_risk_pct": governor.get("available_gross_risk_pct"),
        },
        "broker_profile_generation": {
            "profile_supported_symbol_slot_count": profile_generation.get("profile_supported_symbol_slot_count"),
            "broker_unsupported_symbol_slot_count": profile_generation.get("broker_unsupported_symbol_slot_count"),
            "broker_unsupported_unique_symbols": profile_generation.get("broker_unsupported_unique_symbols") or [],
        },
    }


def build_digest() -> dict[str, Any]:
    synthesis = read_json(SYNTHESIS_JSON)
    start = parse_dt(synthesis.get("started_at_utc"))
    end = parse_dt(synthesis.get("ended_at_utc"))
    rows = []
    for row in read_jsonl(LAUNCHER_LOG):
        dt = parse_dt(row.get("ts"))
        if dt is None:
            continue
        if start and dt < start:
            continue
        if end and dt > end:
            continue
        rows.append(row)

    cycles = [extract_cycle(row) for row in rows]
    terminal_counts = Counter(cycle["terminal_cause"] for cycle in cycles)
    namespace_counts = Counter(cycle.get("namespace") or "missing" for cycle in cycles)
    unsupported_symbols = Counter()
    cost_events: list[dict[str, Any]] = []
    duplicate_events: list[dict[str, Any]] = []
    for cycle in cycles:
        for symbol in cycle["broker_profile_generation"].get("broker_unsupported_unique_symbols") or []:
            unsupported_symbols[str(symbol)] += 1
        for skipped in cycle.get("skipped") or []:
            reason = str(skipped.get("reason") or "")
            if reason.startswith("cost_screen_"):
                cost_events.append(
                    {
                        "ts": cycle.get("ts"),
                        "namespace": cycle.get("namespace"),
                        "symbol": skipped.get("symbol"),
                        "sleeve": skipped.get("sleeve"),
                        "decision_bar_iso": skipped.get("decision_bar_iso"),
                        "reason": reason,
                    }
                )
            if reason == "already_placed_today":
                duplicate_events.append(
                    {
                        "ts": cycle.get("ts"),
                        "namespace": cycle.get("namespace"),
                        "symbol": skipped.get("symbol"),
                        "sleeve": skipped.get("sleeve"),
                        "decision_bar_iso": skipped.get("decision_bar_iso"),
                        "reason": reason,
                    }
                )

    latest = synthesis.get("latest_status") if isinstance(synthesis.get("latest_status"), dict) else {}
    trade_records = latest.get("trade_records") if isinstance(latest.get("trade_records"), dict) else {}
    nonclosed_records = trade_records.get("nonclosed_records") or []
    active_record_normalization = [
        {
            "path": row.get("path"),
            "namespace": row.get("namespace"),
            "symbol": row.get("symbol"),
            "sleeve": row.get("sleeve"),
            "candidate_id": row.get("candidate_id"),
            "raw_trade_lifecycle_status": row.get("trade_lifecycle_status"),
            "companion_status": "active_nonclosed" if row.get("trade_lifecycle_status") in (None, "") else row.get("trade_lifecycle_status"),
            "joinability_status": row.get("joinability_status"),
        }
        for row in nonclosed_records
    ]

    digest = {
        "schema": "gtos.vps_runtime_ai_companion.cycle_digest.v1",
        "generated_at_utc": iso(datetime.now(timezone.utc)),
        "source_synthesis": str(SYNTHESIS_JSON.relative_to(REPO_ROOT)),
        "source_launcher_log": str(LAUNCHER_LOG.relative_to(REPO_ROOT)),
        "window_start_utc": synthesis.get("started_at_utc"),
        "window_end_utc": synthesis.get("ended_at_utc"),
        "runtime_effect_boundary": BOUNDARY,
        "ok": bool(synthesis.get("ok")) and not synthesis.get("issue_counts"),
        "issue_counts": synthesis.get("issue_counts") or {},
        "cycle_count": len(cycles),
        "namespace_counts": compact_counts(namespace_counts),
        "terminal_cause_counts": compact_counts(terminal_counts),
        "placed_count": sum(int(cycle.get("placed_count") or 0) for cycle in cycles),
        "cycles": cycles,
        "companion_queues": {
            "selection_state_digest": [
                {
                    "priority": "high",
                    "action": "Explain every scheduled cycle by terminal_cause, skipped rows, governor state, and placement count.",
                }
            ],
            "cost_screen_review": cost_events,
            "duplicate_protection_awareness": duplicate_events,
            "broker_profile_hygiene_symbols": compact_counts(unsupported_symbols),
            "risk_governor_awareness": [
                {
                    "ts": cycle.get("ts"),
                    "namespace": cycle.get("namespace"),
                    "size_cap_multiplier": cycle.get("governor", {}).get("size_cap_multiplier"),
                    "available_gross_risk_pct": cycle.get("governor", {}).get("available_gross_risk_pct"),
                    "reason": cycle.get("governor", {}).get("reason"),
                }
                for cycle in cycles
                if cycle.get("governor", {}).get("reason")
            ],
            "active_trade_record_lifecycle_normalization": active_record_normalization,
        },
    }
    return digest


def write_markdown(digest: dict[str, Any]) -> None:
    lines = [
        "# AI Companion Cycle Digest",
        "",
        f"Window: `{digest.get('window_start_utc')}` to `{digest.get('window_end_utc')}`",
        f"Runtime effect boundary: `{digest.get('runtime_effect_boundary')}`",
        f"OK: `{digest.get('ok')}`",
        "",
        "## Cycle Causes",
        "",
    ]
    for key, value in digest.get("terminal_cause_counts", {}).items():
        lines.append(f"- `{key}`: `{value}` cycles.")
    lines.extend(["", "## Companion Queues", ""])
    queues = digest.get("companion_queues", {})
    cost_events = queues.get("cost_screen_review") or []
    duplicate_events = queues.get("duplicate_protection_awareness") or []
    profile_symbols = queues.get("broker_profile_hygiene_symbols") or {}
    lifecycle = queues.get("active_trade_record_lifecycle_normalization") or []
    lines.append(f"- Cost-screen review events: `{len(cost_events)}`.")
    for event in cost_events:
        lines.append(
            f"  - `{event.get('namespace')}` `{event.get('symbol')}` `{event.get('sleeve')}` "
            f"`{event.get('decision_bar_iso')}`: `{event.get('reason')}`."
        )
    lines.append(f"- Duplicate-protection events: `{len(duplicate_events)}`.")
    for event in duplicate_events:
        lines.append(
            f"  - `{event.get('namespace')}` `{event.get('symbol')}` `{event.get('sleeve')}` "
            f"`{event.get('decision_bar_iso')}`: `{event.get('reason')}`."
        )
    lines.append(f"- Broker-profile hygiene symbols: `{profile_symbols}`.")
    lines.append(f"- Active/nonclosed lifecycle normalizations: `{len(lifecycle)}`.")
    for row in lifecycle:
        lines.append(
            f"  - `{row.get('namespace')}` `{row.get('symbol')}` `{row.get('sleeve')}` "
            f"raw=`{row.get('raw_trade_lifecycle_status')}` companion=`{row.get('companion_status')}`."
        )
    lines.extend(["", "## Boundary", ""])
    lines.append("- This digest is read-only and does not override gates, place orders, reload workers, or mutate broker state.")
    DIGEST_MD.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    digest = build_digest()
    DIGEST_JSON.write_text(json.dumps(digest, indent=2, sort_keys=True, default=str) + "\n", encoding="utf-8")
    write_markdown(digest)
    print(json.dumps({"ok": digest["ok"], "cycle_count": digest["cycle_count"], "path": str(DIGEST_JSON)}, sort_keys=True))
    return 0 if digest["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
