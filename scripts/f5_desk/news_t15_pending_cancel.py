#!/usr/bin/env python3
"""F5 writer-owned HIGH-window pending reconciliation. No flatten/remint.

Inventory unknown is retained; a REMOVE acknowledgement is not deletion proof.
Original order protection/quantity is persisted before the writer is invoked.
Pending cancellation continues throughout the exclusion window, including a
post-print recovery. History joins use order.position_id -> position.identifier.
"""
from __future__ import annotations
import json
import os
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional
from event_state import active_exclusions, canonical_symbol, committed_snapshot

MAGIC_F5, LOGIN_FTMO = 0, 0
SERVER_FTMO = "FTMO-Server3"
NAMESPACE = "operator"
TRADE_ACTION_REMOVE = 8
DEFAULT_RECEIPT_DIR = Path(r"host-local\redacted_host\repo\judgment\live\receipts\news_t15_cancel")
ORDER_FIELDS = ("ticket", "symbol", "type", "magic", "comment", "price_open", "sl", "tp",
                "volume_initial", "volume_current", "time_setup", "time_setup_msc",
                "time_expiration", "type_time", "position_id", "position_by_id", "state")
POSITION_FIELDS = ("ticket", "identifier", "symbol", "magic", "comment", "volume", "price_open", "sl", "tp")


def _utc_now():
    return datetime.now(timezone.utc)


def _utc_iso(dt=None):
    return (dt or _utc_now()).astimezone(timezone.utc).isoformat()


def _row(value, fields):
    return {k: value.get(k) if isinstance(value, dict) else getattr(value, k, None) for k in fields}


def _inventory(getter, *, fields, **kwargs):
    if not callable(getter):
        return {"status": "UNKNOWN", "rows": [], "error": "getter_unavailable"}
    try:
        values = getter(**kwargs)
        if values is None:
            raise ValueError("broker_returned_none")
        rows = [_row(v, fields) for v in values]
        if any(not r.get("ticket") for r in rows):
            raise ValueError("inventory_row_identity_missing")
        return {"status": "OBSERVED", "rows": rows}
    except Exception as exc:
        return {"status": "UNKNOWN", "rows": [], "error": repr(exc)}



def _saved_scope_error(saved):
    if not isinstance(saved, dict):
        return "saved_original_contract_missing_or_invalid"
    if (saved.get("account_login") != LOGIN_FTMO or saved.get("account_server") != SERVER_FTMO
            or saved.get("namespace") != NAMESPACE or saved.get("magic") != MAGIC_F5):
        return "saved_account_book_scope_missing_or_mismatch"
    if not isinstance(saved.get("ticket"), int) or saved["ticket"] <= 0 or not saved.get("symbol"):
        return "saved_order_identity_missing"
    return None


def _tracking_key(saved):
    return "%s@%s:%s:%s:%s" % (saved.get("account_login"), saved.get("account_server"),
        saved.get("namespace"), saved.get("magic"), saved.get("ticket"))


class _AccountEvidence:
    """Fresh account brackets around each broker read; any observed drift sticks.

    account_verified is only a caller brake. A boolean supplies no evidence.
    Terminal facts are usable only from the pinned login/server and saved book.
    MT5 exposes no transactional snapshot epoch: these are observed brackets,
    not a claim that an invisible switch-and-back cannot occur inside one call.
    """
    def __init__(self, account_reader, *, caller_verified, magic):
        self.reader = account_reader
        self.failed = caller_verified is not True or magic != MAGIC_F5
        self.observations = []
        self.failure = "caller_account_or_magic_unverified" if self.failed else None

    def observe(self, phase):
        row = {"phase": phase, "checked_at_utc": _utc_iso(), "expected_login": LOGIN_FTMO,
               "expected_server": SERVER_FTMO, "verified": False}
        if self.failed:
            row["error"] = self.failure or "prior_account_scope_failure"
            self.observations.append(row)
            return row
        try:
            if not callable(self.reader):
                raise ValueError("account_reader_unavailable")
            account = self.reader()
            if account is None:
                raise ValueError("account_reader_returned_none")
            actual = _row(account, ("login", "server"))
            row.update(observed_login=actual["login"], observed_server=actual["server"])
            if actual["login"] != LOGIN_FTMO or actual["server"] != SERVER_FTMO:
                raise ValueError("account_login_or_server_mismatch")
            row["verified"] = True
        except Exception as exc:
            self.failed = True
            self.failure = repr(exc)
            row["error"] = self.failure
        self.observations.append(row)
        return row

    def read(self, getter, *, fields, phase, **kwargs):
        before = self.observe(phase + ":before")
        if not before["verified"]:
            return {"status": "UNKNOWN", "rows": [], "error": "account_scope_unverified",
                    "account_before": before, "account_after": None}
        result = _inventory(getter, fields=fields, **kwargs)
        after = self.observe(phase + ":after")
        result["account_before"], result["account_after"] = before, after
        if not after["verified"]:
            result = {"status": "UNKNOWN", "rows": [], "error": "account_scope_changed_during_read",
                      "untrusted_row_count": len(result.get("rows", [])),
                      "account_before": before, "account_after": after}
        return result


def events_in_t15_cancel_window(events, *, now=None):
    return active_exclusions(now=now or _utc_now(), snapshot={"events": events, "issues": []})


def affected_symbol_set(events):
    return {canonical_symbol(s) for e in events for s in e.get("affected_instruments", [])}


def _ours(row, magic, prefix, symbols):
    return (row.get("magic") == magic and row.get("type") in (2, 3)
            and str(row.get("comment") or "").startswith(prefix)
            and canonical_symbol(row.get("symbol")) in symbols)


def list_native_pendings(orders_get, *, magic=MAGIC_F5, comment_prefix="F5:", symbol_filter=None,
                         account_reader=None, account_verified=False):
    evidence = _AccountEvidence(account_reader, caller_verified=account_verified, magic=magic)
    snap = evidence.read(orders_get, fields=ORDER_FIELDS, phase="list_pending")
    if snap["status"] != "OBSERVED":
        return [{"error": snap["error"], "inventory_status": "UNKNOWN"}]
    symbols = symbol_filter if symbol_filter is not None else {canonical_symbol(r["symbol"]) for r in snap["rows"]}
    return [r for r in snap["rows"] if _ours(r, magic, comment_prefix, symbols)]


def _atomic_json(path, obj):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_name(path.name + "." + uuid.uuid4().hex + ".tmp")
    with temp.open("xb") as f:
        f.write(json.dumps(obj, sort_keys=True, indent=2).encode())
        f.flush()
        os.fsync(f.fileno())
    os.replace(temp, path)


def _persist(receipt, persist_dir=None):
    directory = Path(persist_dir or DEFAULT_RECEIPT_DIR)
    path = directory / ("t15_" + uuid.uuid4().hex + ".json")
    receipt["receipt_path"] = str(path)
    _atomic_json(path, receipt)


def request_cancel_via_writer(order_send, ticket, *, dry_run=False, before_send=None):
    if dry_run:
        return {"cancelled": False, "dry_run": True, "ticket": ticket}
    try:
        authority = before_send() if callable(before_send) else {"allowed": False, "reason": "cancel_authority_unavailable"}
        if not authority.get("allowed"):
            return {"cancelled": False, "ticket": ticket, "not_sent": True, "authority": authority}
        result = order_send({"action": TRADE_ACTION_REMOVE, "order": int(ticket)})
        retcode = getattr(result, "retcode", None)
        return {"cancelled": False, "acknowledged": retcode in (10008, 10009),
                "ticket": ticket, "retcode": retcode,
                "broker_comment": getattr(result, "comment", None), "authority": authority}
    except Exception as exc:
        return {"cancelled": False, "ticket": ticket, "error": repr(exc)}


def _reconcile_order(saved, orders_get, positions_get, history_orders_get, history_deals_get=None,
                     *, account_reader=None, account_verified=False, account_evidence=None):
    """Account-bound facts only; never infer a position identity from order ticket."""
    scope_error = _saved_scope_error(saved)
    if scope_error:
        return {"cancelled": False, "terminal": False, "positions": [], "state": "UNRESOLVED",
                "exposure_status": "UNKNOWN_RETAIN_FOR_MANAGEMENT", "error": scope_error}
    evidence = account_evidence or _AccountEvidence(account_reader, caller_verified=account_verified, magic=saved["magic"])
    current = evidence.read(orders_get, fields=ORDER_FIELDS, phase="reconcile_orders")
    history = evidence.read(history_orders_get, fields=ORDER_FIELDS, phase="reconcile_history_orders", ticket=int(saved["ticket"]))
    positions = evidence.read(positions_get, fields=POSITION_FIELDS, phase="reconcile_positions")
    result = {"inventory": current, "history": history, "positions_status": positions["status"],
              "positions_error": positions.get("error"), "cancelled": False, "terminal": False,
              "positions": [], "state": "UNRESOLVED", "account_scope_verified": not evidence.failed}
    if evidence.failed:
        result.update(error="account_scope_unknown_or_changed", exposure_status="UNKNOWN_RETAIN_FOR_MANAGEMENT")
        return result
    matching = [r for r in history["rows"] if r["ticket"] == saved["ticket"]
                and r.get("magic") == saved.get("magic") and r.get("symbol") == saved.get("symbol")]
    if len(matching) > 1:
        result["error"] = "ambiguous_order_history"
        return result
    hist = matching[0] if matching else None
    position_id = hist.get("position_id") if hist else None
    if position_id:
        result["positions"] = [p for p in positions["rows"]
            if p.get("identifier") == position_id and p.get("magic") == saved.get("magic")
            and p.get("symbol") == saved.get("symbol")]
        result["historical_position_id"] = position_id
    present = [r for r in current["rows"] if r["ticket"] == saved["ticket"]]
    if present:
        result["state"] = "PENDING_PRESENT"
        result["current_pending"] = present[0]
        return result
    if current["status"] != "OBSERVED" or history["status"] != "OBSERVED" or hist is None:
        return result
    initial, remaining = hist.get("volume_initial"), hist.get("volume_current")
    filled = initial - remaining if isinstance(initial, (float, int)) and isinstance(remaining, (float, int)) and 0 <= remaining <= initial else None
    result.update(historical_volume_initial=initial, historical_volume_remaining=remaining, filled_volume=filled)
    exposure_resolved = False
    if position_id and positions["status"] == "OBSERVED":
        if result["positions"]:
            exposure_resolved = True  # Strictly joined open position goes to existing management.
            result["exposure_status"] = "OPEN_STRICTLY_JOINED_CONTINUE_MANAGEMENT"
        else:
            deals = evidence.read(history_deals_get, fields=("ticket", "order", "position_id", "entry", "volume", "symbol", "magic", "type"), phase="reconcile_history_deals", position=int(position_id))
            result["deal_history"] = deals
            scoped = [d for d in deals["rows"] if d.get("position_id") == position_id and d.get("symbol") == saved.get("symbol") and d.get("magic") == saved.get("magic")]
            own_entry = any(d.get("order") == saved["ticket"] and d.get("entry") == 0 for d in scoped)
            known_quantities = all(isinstance(d.get("volume"), (int, float)) and d["volume"] >= 0 and d.get("entry") in (0, 1, 3) for d in scoped)
            if deals["status"] == "OBSERVED" and own_entry and known_quantities:
                incoming = sum(d["volume"] for d in scoped if d["entry"] == 0)
                outgoing = sum(d["volume"] for d in scoped if d["entry"] in (1, 3))
                exposure_resolved = incoming > 0 and abs(incoming - outgoing) < 1e-8
                if exposure_resolved:
                    result["exposure_status"] = "CLOSED_BY_STRICT_DEAL_QUANTITY_PROOF"
    if evidence.failed:
        result.update(cancelled=False, terminal=False, positions=[], state="UNRESOLVED",
                      account_scope_verified=False, error="account_scope_unknown_or_changed",
                      exposure_status="UNKNOWN_RETAIN_FOR_MANAGEMENT")
        return result
    if hist.get("state") in (2, 6):
        result.update(state="CANCELLED_REMAINDER" if hist.get("state") == 2 else "EXPIRED_REMAINDER",
                      cancelled=hist.get("state") == 2,
                      terminal=(filled == 0 and not position_id) or exposure_resolved)
    elif hist.get("state") == 4:
        result.update(state="RACE_FILL", terminal=exposure_resolved)
    elif hist.get("state") == 5:
        result.update(state="REJECTED_ORDER", terminal=(filled == 0 and not position_id) or exposure_resolved)
    if not result["terminal"]:
        result.setdefault("exposure_status", "UNKNOWN_RETAIN_FOR_MANAGEMENT")
    return result


def reconcile_and_cancel(*, now=None, event_version=None, events=None, orders_get=None,
                         positions_get=None, history_orders_get=None, history_deals_get=None, order_send=None,
                         magic=MAGIC_F5, comment_prefix="F5:", dry_run=False, persist_dir=None,
                         account_verified=False, account_reader=None, decision_clock=None):
    now = now or _utc_now()
    injected_events = events is not None
    current_clock = decision_clock or _utc_now
    directory = Path(persist_dir or DEFAULT_RECEIPT_DIR)
    state_path = directory / "unresolved_v3.json"
    receipt = {"schema": "gtos.news_t15_pending_cancel.v4", "as_of_utc": _utc_iso(now),
               "namespace": NAMESPACE, "magic": magic, "event_version": event_version,
               "applied": False, "dry_run": dry_run, "n_events_in_window": 0,
               "n_pendings_seen": None, "n_cancelled": 0, "n_race_fill": 0,
               "attempts": [], "race_fills": [], "issues": [], "fail_open": False,
               "inventory_status": "NOT_READ", "account_verified": False,
               "caller_account_verified": account_verified, "account_login": LOGIN_FTMO, "account_server": SERVER_FTMO}
    try:
        if state_path.exists():
            state = json.loads(state_path.read_text())
            unresolved = state["unresolved"]
            if state.get("schema") not in {"news_cancel_unresolved.v3", "news_cancel_unresolved.v4"}:
                raise ValueError("unresolved_state_schema_unknown")
            if not isinstance(unresolved, dict):
                raise ValueError("unresolved_state_invalid")
        else:
            unresolved = {}
        if events is None:
            snap = committed_snapshot()
            events = snap["events"]
            receipt.update(event_version=snap["event_version"], registry_sha256=snap["sha256"], registry_path=snap["path"])
        snapshot = {"events": events, "issues": []}
        win = active_exclusions(now=now, snapshot=snapshot)
        receipt["issues"].extend(snapshot["issues"])
        receipt["events"] = win
        receipt["n_events_in_window"] = len(win)
        if not win and not unresolved:
            receipt["note"] = "no_active_window_or_unresolved_order"
            _persist(receipt, directory)
            return receipt
        evidence = _AccountEvidence(account_reader, caller_verified=account_verified, magic=magic)
        inventory = evidence.read(orders_get, fields=ORDER_FIELDS, phase="initial_orders")
        receipt["account_observations"] = evidence.observations
        receipt["account_verified"] = not evidence.failed
        receipt["inventory_status"] = inventory["status"]
        if inventory["status"] != "OBSERVED":
            receipt["issues"].append(inventory)
            receipt["note"] = "inventory_unknown_unresolved_retained"
            receipt["fail_open"] = True
            receipt["n_unresolved"] = len(unresolved)
            _persist(receipt, directory)
            return receipt
        symbols = affected_symbol_set(win)
        pending = [p for p in inventory["rows"] if _ours(p, magic, comment_prefix, symbols)]
        receipt["n_pendings_seen"] = len(pending)
        receipt["pendings_seen"] = pending
        for p in pending:
            p["account_login"], p["account_server"], p["namespace"] = LOGIN_FTMO, SERVER_FTMO, NAMESPACE
            # Reuse only an already-account-bound identity. A coincident legacy
            # or foreign ticket remains separate and cannot steal this contract.
            scope_fields = ("account_login", "account_server", "namespace", "magic", "ticket", "symbol")
            existing = []
            for stored_key, row in unresolved.items():
                original = row.get("saved_original_contract") if isinstance(row, dict) else None
                if (_saved_scope_error(original) is None
                        and all(original.get(field) == p.get(field) for field in scope_fields)):
                    existing.append(stored_key)
            if not existing:
                # Dictionary keys are labels, never identity evidence. Even an
                # invalid record occupying the canonical label must be retained.
                base_key = _tracking_key(p)
                key, suffix = base_key, 0
                while key in unresolved:
                    suffix += 1
                    key = base_key + "#native" + str(suffix)
                unresolved[key] = {"saved_original_contract": p, "first_seen_utc": _utc_iso(now)}
        terminal_keys = []
        for key, tracked in list(unresolved.items()):
            saved = tracked.get("saved_original_contract") if isinstance(tracked, dict) else None
            attempt = {"tracking_key": key, "ticket": saved.get("ticket") if isinstance(saved, dict) else None,
                       "saved_original_contract": saved, "event_version": receipt["event_version"],
                       "as_of_utc": _utc_iso(now), "occurrence_ids": [e.get("occurrence_id") for e in win]}
            scope_error = _saved_scope_error(saved)
            if scope_error:
                # Isolate an unbound/malformed record without rewriting it or
                # suppressing a separately observed current native contract.
                attempt["before"] = {"cancelled": False, "terminal": False, "positions": [],
                    "state": "UNRESOLVED", "exposure_status": "UNKNOWN_RETAIN_FOR_MANAGEMENT",
                    "error": scope_error}
                attempt["result"] = "UNRESOLVED"
                receipt["attempts"].append(attempt)
                receipt["issues"].append({"tracking_key": key, "error": scope_error,
                    "action": "retain_original_record_unresolved"})
                continue
            before = _reconcile_order(saved, orders_get, positions_get, history_orders_get, history_deals_get,
                                      account_evidence=evidence)
            attempt["before"] = before
            if before["state"] == "PENDING_PRESENT" and _ours(before["current_pending"], magic, comment_prefix, symbols):
                current = before["current_pending"]
                identity = ("ticket", "magic", "symbol", "type", "comment", "price_open", "sl", "tp", "volume_initial", "time_setup_msc")
                if any(current.get(k) != saved.get(k) for k in identity):
                    attempt["result"] = "ORDER_CONTRACT_CHANGED_RETAIN"
                elif any(saved.get(k) is None for k in ("sl", "tp", "volume_initial", "volume_current", "price_open")):
                    attempt["result"] = "ORIGINAL_CONTRACT_INCOMPLETE_NO_CANCEL"
                elif not account_verified:
                    attempt["result"] = "ACCOUNT_IDENTITY_UNVERIFIED_NO_CANCEL"
                else:
                    # Durable original and pending attempt exist before any broker mutation.
                    attempt["result"] = "CANCEL_REQUEST_PREPARED"
                    tracked["attempt"] = attempt
                    _atomic_json(state_path, {"schema": "news_cancel_unresolved.v4", "unresolved": unresolved})
                    _persist(attempt, directory)
                    def authorize_cancel():
                        latest = evidence.read(orders_get, fields=ORDER_FIELDS, phase="cancel_authority_orders")
                        matches = [row for row in latest["rows"] if row.get("ticket") == saved["ticket"]]
                        if latest["status"] != "OBSERVED" or len(matches) != 1:
                            return {"allowed": False, "reason": "pending_identity_unavailable_at_send"}
                        if any(matches[0].get(k) != saved.get(k) for k in identity):
                            return {"allowed": False, "reason": "pending_contract_changed_at_send"}
                        fresh = {"events": events, "issues": []} if injected_events else committed_snapshot()
                        at_send = current_clock()
                        exclusions = active_exclusions(now=at_send, symbol=saved["symbol"], snapshot=fresh)
                        send_account = evidence.observe("immediate_pre_cancel_send")
                        if not send_account["verified"]:
                            return {"allowed": False, "reason": "account_identity_changed_at_send", "account_observation": send_account}
                        return {"allowed": bool(exclusions), "reason": "active_high_window" if exclusions else "no_current_high_window",
                                "account_observation": send_account,
                                "checked_at_utc": _utc_iso(at_send), "registry_sha256": fresh.get("sha256"),
                                "event_version": fresh.get("event_version", event_version), "issues": fresh.get("issues"),
                                "occurrence_ids": [e.get("occurrence_id") for e in exclusions]}
                    attempt["response"] = request_cancel_via_writer(order_send, saved["ticket"], dry_run=dry_run, before_send=authorize_cancel)
                    after = before if dry_run else _reconcile_order(saved, orders_get, positions_get, history_orders_get, history_deals_get,
                                                                     account_evidence=evidence)
                    attempt["after"] = after
                    attempt["result"] = "DRY_RUN_WOULD_CANCEL" if dry_run else after["state"]
                    before = after
            else:
                attempt["result"] = before["state"]
            if before["cancelled"]:
                receipt["n_cancelled"] += 1
            if before["state"] == "RACE_FILL" or before["positions"]:
                race = {"order_ticket": saved["ticket"], "status": "RACE_FILL", "positions": before["positions"],
                        "position_id": before.get("historical_position_id"), "saved_original_contract": saved,
                        "flatten": False, "action": "leave_position_continue_management_law"}
                receipt["race_fills"].append(race)
                receipt["n_race_fill"] += 1
            receipt["attempts"].append(attempt)
            if before["terminal"]:
                terminal_keys.append(key)
            else:
                tracked["last_result"] = attempt["result"]
        final_account = evidence.observe("before_reconciliation_state_commit")
        receipt["account_verified"] = final_account["verified"]
        if final_account["verified"]:
            for key in terminal_keys:
                del unresolved[key]
        else:
            receipt["uncommitted_outcome_observations"] = {
                "n_cancelled": receipt["n_cancelled"], "race_fills": receipt["race_fills"]}
            receipt["n_cancelled"], receipt["n_race_fill"], receipt["race_fills"] = 0, 0, []
            receipt["inventory_status"] = "UNKNOWN_ACCOUNT_SCOPE"
            receipt["fail_open"] = True
            for attempt in receipt["attempts"]:
                attempt["observed_result"] = attempt["result"]
                attempt["result"] = "ACCOUNT_SCOPE_UNVERIFIED_OUTCOME_NOT_COMMITTED"
        receipt["n_unresolved"] = len(unresolved)
        receipt["note"] = "reconciled_with_unresolved" if unresolved else "reconciled"
        _persist(receipt, directory)
        # Never discard unresolved evidence before the terminal receipt is durable.
        _atomic_json(state_path, {"schema": "news_cancel_unresolved.v4", "unresolved": unresolved})
    except Exception as exc:
        receipt.update(fail_open=True, error=repr(exc), note="unknown_state_retained_no_invented_completion")
        try:
            _persist(receipt, directory)
        except Exception:
            pass
    return receipt


def run_from_book(book, now=None, *, dry_run=False):
    if str(getattr(book, "_namespace", "")) != NAMESPACE:
        return {"skipped": True, "reason": "namespace_not_f5", "applied": False}
    module = getattr(getattr(book, "_mt5", None), "_mt5", None)
    try:
        account = module.account_info()
        verified = (account is not None and account.login == LOGIN_FTMO
                    and account.server == SERVER_FTMO and int(book._magic) == MAGIC_F5)
    except Exception:
        verified = False
    return reconcile_and_cancel(now=now, orders_get=getattr(module, "orders_get", None),
        positions_get=getattr(module, "positions_get", None), history_orders_get=getattr(module, "history_orders_get", None),
        history_deals_get=getattr(module, "history_deals_get", None),
        order_send=getattr(getattr(book, "_mt5", None), "order_send", None),
        magic=int(getattr(book, "_magic", MAGIC_F5)), comment_prefix="F5:", dry_run=dry_run,
        account_verified=verified, account_reader=getattr(module, "account_info", None))
