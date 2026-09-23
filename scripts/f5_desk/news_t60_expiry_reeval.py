#!/usr/bin/env python3
"""Durable T+60 requests; the live launcher executes BookOwner.run_cycle.

This module does not approve entries or place orders. Only a receipt from the
actual generator/admission/current-geometry-and-cost route completes a request.
No five-minute recovery cliff, forced remint, lifetime extension or market chase.
"""
from __future__ import annotations
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from event_state import canonical_symbol, committed_snapshot, parse_utc
from news_t15_pending_cancel import _atomic_json

NAMESPACE = "operator"
MAGIC_F5 = 0
FORBIDDEN_SPENT_TICKETS = frozenset({180717112})
DEFAULT_RECEIPT_DIR = Path(r"host-local\redacted_host\repo\judgment\live\receipts\news_t60_reeval")
DEFAULT_STATE = DEFAULT_RECEIPT_DIR / "reevaluation_requests_v3.json"
SPENT_GLOBS = [
    Path(r"host-local\redacted_host\repo\judgment\live"),
    Path(r"host-local\redacted_host\repo\pipeline_state\ultimate_book\operator\judgment\dr"),
]


def load_spent_evidence():
    import re
    spent, files, issues = set(FORBIDDEN_SPENT_TICKETS), [], []
    for directory in SPENT_GLOBS:
        if not directory.exists():
            issues.append({"path": str(directory), "error": "spent_directory_unavailable"})
            continue
        for path in directory.glob("spent*"):
            if not path.is_file():
                continue
            try:
                raw = path.read_bytes()
                payload = json.loads(raw.decode("utf-8-sig"))
                match = re.search(r"spent[_-]?(\d+)", path.name, re.I)
                if match:
                    spent.add(int(match.group(1)))
                if isinstance(payload, dict):
                    for key in ("ticket", "spent_ticket", "order_ticket"):
                        if payload.get(key) is not None:
                            spent.add(int(payload[key]))
                    spent.update(int(v) for v in payload.get("tickets", []))
                files.append({"path": str(path), "sha256": hashlib.sha256(raw).hexdigest()})
            except Exception as exc:
                issues.append({"path": str(path), "error": repr(exc)})
    return {"status": "UNKNOWN" if issues else "OBSERVED", "tickets": sorted(spent), "files": files, "issues": issues}


def _utc_iso(now=None):
    return (now or datetime.now(timezone.utc)).astimezone(timezone.utc).isoformat()


def _event_key(event):
    # Changed event timing/scope is distinct even if an upstream occurrence ID was reused.
    payload = {k: event.get(k) for k in ("occurrence_id", "window_t60_end_utc", "affected_instruments")}
    return hashlib.sha256(json.dumps(payload, sort_keys=True).encode()).hexdigest()


def _load_state(path):
    if not path.exists():
        return {"schema": "gtos.news_t60_requests.v3", "completed": {}, "pending": {}}
    state = json.loads(path.read_text())
    if state.get("schema") != "gtos.news_t60_requests.v3" or not isinstance(state.get("completed"), dict) or not isinstance(state.get("pending"), dict):
        raise ValueError("t60_state_unavailable_or_invalid")
    return state


def events_at_t60_expiry(events, *, now=None, processed=None, issues=None, **_unused):
    now = now or datetime.now(timezone.utc)
    if now.tzinfo is None or now.utcoffset() is None:
        raise ValueError("t60_clock_timezone_missing")
    issues = issues if issues is not None else []
    result = []
    for event in events:
        try:
            if event.get("official_high") is not True:
                continue
            if not event.get("occurrence_id") or not isinstance(event.get("affected_instruments"), list) or not event["affected_instruments"]:
                raise ValueError("t60_event_identity_or_scope_unknown")
            if _event_key(event) not in (processed or set()) and parse_utc(event.get("window_t60_end_utc")) <= now:
                result.append(event)
        except (TypeError, ValueError, AttributeError) as exc:
            issues.append({"event": event, "error": repr(exc)})
    return result


def _frozen_candidates_from_book(book):
    frozen = getattr(book, "_frozen_intents", None)
    if frozen is None:
        return {"status": "UNKNOWN", "rows": [], "reason": "frozen_inventory_unavailable"}
    rows = []
    for key, item in frozen.items():
        if not callable(getattr(item, "as_row", None)):
            return {"status": "UNKNOWN", "rows": rows, "reason": "frozen_contract_projection_unavailable"}
        row = dict(item.as_row())
        row["key"] = list(key) if isinstance(key, tuple) else key
        row["is_open"] = bool(item.is_open)
        row["annotations"] = dict(getattr(item, "annotations", {}) or {})
        rows.append(row)
    return {"status": "OBSERVED", "rows": rows}


def reevaluate_at_expiry(*, now=None, events=None, event_version=None, frozen_candidates=None,
                         persist_dir=None, state_path=None, spent_tickets=None, **_unused):
    now = now or datetime.now(timezone.utc)
    path = Path(state_path or DEFAULT_STATE)
    receipt = {"schema": "gtos.news_t60_expiry_reeval.v3", "as_of_utc": _utc_iso(now),
               "event_version": event_version, "applied": False, "remint": False, "place": False,
               "n_admit_annotation": 0, "status": "UNKNOWN", "fail_open": False,
               "frozen_inventory": frozen_candidates}
    try:
        state = _load_state(path)
        spent = load_spent_evidence() if spent_tickets is None else {
            "status": "OBSERVED", "tickets": sorted(set(spent_tickets) | set(FORBIDDEN_SPENT_TICKETS)), "files": [], "issues": [], "source": "explicit_caller_fixture"}
        receipt["spent_inventory"] = spent
        if events is None:
            snap = committed_snapshot()
            events = snap["events"]
            receipt.update(event_version=snap["event_version"], registry_sha256=snap["sha256"], registry_path=snap["path"])
        receipt["issues"] = []
        expired = events_at_t60_expiry(events, now=now, processed=set(state["completed"]), issues=receipt["issues"])
        for event in expired:
            key = _event_key(event)
            state["pending"].setdefault(key, {"event": event, "requested_at_utc": _utc_iso(now),
                "registry_sha256": receipt.get("registry_sha256"), "event_version": receipt.get("event_version")})
        receipt["n_events_expired"] = len(expired)
        # A removed event remains pending: omission cannot silently acknowledge work.
        pending = state["pending"]
        if pending:
            receipt["request"] = {"request_keys": sorted(pending), "events": list(pending.values()),
                "affected_symbols": sorted({canonical_symbol(s) for p in pending.values() for s in p["event"]["affected_instruments"]}),
                "state_path": str(path), "receipt_dir": str(persist_dir or DEFAULT_RECEIPT_DIR),
                "requested_at_utc": _utc_iso(now), "frozen_inventory": frozen_candidates,
                "execution_path": "BookLauncher.tick -> BookOwner.run_cycle -> engine.evaluate -> normal per-intent admission/geometry/cost -> router.place",
                "spent_forbidden": spent["tickets"], "spent_inventory_status": spent["status"]}
            receipt["status"] = "REQUESTED_REAL_GENERATOR_CYCLE"
        else:
            receipt["status"] = "PARTIAL_NO_VALID_REQUEST_DUE" if receipt["issues"] else "NO_REQUEST_DUE"
        _atomic_json(path, state)
    except Exception as exc:
        receipt.update(status="UNKNOWN_RETRY", fail_open=True, error=repr(exc))
    return receipt


def complete_from_cycle(book, request, summary, *, now=None, place=False):
    """Called by the launcher AFTER its real run_cycle returned, never by a fake evaluator."""
    receipt = {"schema": "gtos.news_t60_generator_receipt.v3", "as_of_utc": _utc_iso(now),
               "request_keys": request["request_keys"], "applied": False,
               "status": "RETRY_REQUIRED", "place_enabled": bool(place),
               "evaluation": summary.get("news_t60_reevaluation"),
               "ok": summary.get("ok"), "bar_consumable": summary.get("bar_consumable"),
               "runtime_effect_now": summary.get("runtime_effect_now"),
               "generation": summary.get("generation"), "generation_terminals": summary.get("generation_terminals"),
               "n_intents": summary.get("n_intents"), "skipped": summary.get("skipped"),
               "current_cost_evaluations": summary.get("news_t60_cost_evaluations", []),
               "placed": summary.get("placed"), "reason": summary.get("reason")}
    path = Path(request["state_path"])
    state = _load_state(path)
    evaluation = summary.get("news_t60_reevaluation") or {}
    completed = (place and summary.get("ok") is True and summary.get("bar_consumable") is True
                 and summary.get("runtime_effect_now") is True
                 and evaluation.get("request_keys") == request["request_keys"]
                 and evaluation.get("generator_returned") is True
                 and evaluation.get("route_iteration_completed") is True
                 and evaluation.get("effective_place") is True
                 and not evaluation.get("route_errors"))
    scope = (summary.get("generation") or {}).get("news_t60_scope") or {}
    expected = scope.get("expected_slots")
    terminals = summary.get("generation_terminals")
    completed_keys = []
    coverage = []
    accepted_terminals = {"no_candidate", "candidate_emitted", "profile_unsupported", "spread_floor_refused", "entry_hour_deferred"}
    for key in request["request_keys"]:
        pending = state["pending"].get(key)
        event_symbols = {canonical_symbol(s) for s in (pending or {}).get("event", {}).get("affected_instruments", [])}
        valid = scope.get("status") == "OBSERVED" and isinstance(expected, list) and isinstance(terminals, list)
        rows = []
        if valid:
            for slot in expected:
                if canonical_symbol(slot.get("symbol")) not in event_symbols:
                    continue
                matches = [r for r in terminals if r.get("sleeve") == slot.get("sleeve") and r.get("symbol") == slot.get("symbol") and r.get("timeframe") == slot.get("timeframe")]
                observed = len(matches) == 1 and matches[0].get("terminal_status") in accepted_terminals
                rows.append({"slot": slot, "terminals": matches, "resolved": observed})
                valid = valid and observed
        unresolved_reasons = {"news_t60_spent_identity_unavailable", "news_t60_frozen_inventory_unavailable",
                              "news_t60_frozen_identity_ambiguous", "news_t60_level_or_expiry_unavailable"}
        unresolved_contracts = [r for r in scope.get("scope_rejections", [])
            if canonical_symbol(r.get("symbol")) in event_symbols and r.get("reason") in unresolved_reasons]
        if unresolved_contracts:
            valid = False
        coverage.append({"request_key": key, "resolved": bool(valid), "slots": rows,
                         "unresolved_contracts": unresolved_contracts,
                         "coverage_status": "OBSERVED" if valid else "INCOMPLETE_RETRY"})
        if completed and valid:
            completed_keys.append(key)
    receipt["generation_coverage"] = coverage
    receipt["completed_request_keys"] = completed_keys
    if completed_keys:
        receipt["status"] = "CURRENT_GENERATOR_ROUTE_EVALUATED" if len(completed_keys) == len(request["request_keys"]) else "PARTIAL_CURRENT_GENERATOR_ROUTE_EVALUATED"
    directory = Path(request["receipt_dir"])
    # Reuse UUID+fsync publication primitive, not its filename semantics.
    from uuid import uuid4
    receipt_path = directory / ("t60_cycle_" + uuid4().hex + ".json")
    receipt["receipt_path"] = str(receipt_path)
    _atomic_json(receipt_path, receipt)
    if completed_keys:
        for key in completed_keys:
            if key in state["pending"]:
                state["completed"][key] = {"receipt_path": str(receipt_path), "completed_at_utc": _utc_iso(now)}
                del state["pending"][key]
        _atomic_json(path, state)
    return receipt


def run_from_book(book, now=None):
    if str(getattr(book, "_namespace", "")) != NAMESPACE:
        return {"skipped": True, "reason": "namespace_not_f5", "applied": False}
    try:
        receipt = reevaluate_at_expiry(now=now, frozen_candidates=_frozen_candidates_from_book(book))
        import os
        receipt["writer_pid"] = os.getpid()
        receipt["writer_namespace"] = str(book._namespace)
        receipt["source_path"] = str(Path(__file__).resolve())
        receipt["source_sha256"] = hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
        _atomic_json(DEFAULT_RECEIPT_DIR / "last_poll_v3.json", receipt)
        return receipt
    except Exception as exc:
        return {"status": "UNKNOWN_RETRY", "fail_open": True, "error": repr(exc), "applied": False}
