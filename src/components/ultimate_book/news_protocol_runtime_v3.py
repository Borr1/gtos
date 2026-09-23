"""Source-local news decision at each writer boundary, no broker access."""
from __future__ import annotations
from datetime import datetime, timezone
import importlib.util
from pathlib import Path


def current_event_decision(repo_root, symbol, *, prior=None, now=None):
    now = now or datetime.now(timezone.utc)
    result = {"status": "UNKNOWN", "checked_at_utc": now.isoformat(),
              "applied": False, "symbol": symbol}
    try:
        root = Path(repo_root)
        path = root / "scripts" / "f5_desk" / "event_state.py"
        spec = importlib.util.spec_from_file_location("_writer_event_state_v3", path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        snap = module.committed_snapshot(root / "judgment" / "live" / "event_registry_v1.json")
        exclusions = module.active_exclusions(now=now, symbol=symbol, snapshot=snap)
        result.update(status="PARTIAL" if snap["issues"] else "OBSERVED", event_version=snap["event_version"],
                      event_registry_sha256=snap["sha256"], event_registry_path=snap["path"],
                      event_registry_n_events=snap["n_events"], issues=snap["issues"],
                      active_exclusions=exclusions)
        prior_sha = prior.get("event_registry_sha256") if isinstance(prior, dict) else None
        prior_ver = prior.get("event_version") if isinstance(prior, dict) else None
        result["exclusions_present"] = bool(exclusions)
        result["snapshot_drift"] = bool(
            (prior_sha and prior_sha != snap["sha256"])
            or (prior_ver and prior_ver != snap["event_version"])
        )
    except Exception as exc:
        result.update(error=repr(exc), fail_open=True)
    return result


def is_f5_new_risk_request(request):
    return (request.get("magic") == 0 and request.get("action") in (1, 5)
            and not request.get("position") and not request.get("position_by"))


def filter_t60_before_admission(intents, meta, request, *, now):
    """Remove only extra old-bar work before it can change portfolio sizing.

    Every rejection retains candidate identity and reason. This does not replace
    current generators, actual admission, geometry, costs or the writer ledger.
    """
    from math import isfinite
    def symbol_key(value):
        value = str(value or "").strip().upper()
        if value.endswith(".CASH"):
            value = value[:-5]
        return value.replace(".", "").replace("_", "").replace(" ", "")
    metadata = {(m.get("tag"), m.get("symbol")): m for m in meta}
    frozen_inventory = request.get("frozen_inventory") or {}
    frozen_rows = frozen_inventory.get("rows") or []
    kept, skipped = [], []
    for intent in intents:
        if intent.sleeve not in set(request.get("reevaluation_only_tags", [])):
            kept.append(intent)
            continue
        m = metadata.get((intent.sleeve, intent.symbol), {})
        dbar = m.get("decision_bar_iso") or getattr(intent, "decision_day", None)
        reason = None
        frozen = [r for r in frozen_rows if r.get("sleeve") == intent.sleeve and r.get("symbol") == intent.symbol and r.get("decision_bar_iso") == dbar]
        if symbol_key(intent.symbol) not in set(request["affected_symbols"]):
            reason = "news_t60_extra_cycle_outside_event_scope"
        elif request.get("spent_inventory_status") != "OBSERVED":
            reason = "news_t60_spent_identity_unavailable"
        elif frozen_inventory.get("status") != "OBSERVED":
            reason = "news_t60_frozen_inventory_unavailable"
        elif len(frozen) > 1:
            reason = "news_t60_frozen_identity_ambiguous"
        else:
            row = frozen[0] if frozen else None
            try:
                if row:
                    expiry = datetime.fromisoformat(str(row.get("expires_at_utc")).replace("Z", "+00:00"))
                    if expiry.tzinfo is None or not row.get("is_open") or now >= expiry:
                        reason = "news_t60_frozen_terminal_or_expired"
                    for k in ("ticket", "origin_ticket", "spent_ticket", "order_ticket"):
                        identity = (row.get("annotations") or {}).get(k)
                        if identity is not None and int(identity) in set(request["spent_forbidden"]):
                            reason = "news_t60_spent_ticket_forbidden"
                level = row.get("frozen_entry") if row else getattr(intent, "entry_price", None)
                if reason is None and row is None and level is None:
                    reason = "news_t60_no_unexpired_native_level_no_market_chase"
                if reason is None and (not isfinite(float(level)) or float(level) <= 0):
                    reason = "news_t60_level_or_expiry_unavailable"
            except (TypeError, ValueError):
                reason = "news_t60_level_or_expiry_unavailable"
        if reason is None:
            kept.append(intent)
        else:
            skipped.append({"symbol": intent.symbol, "sleeve": intent.sleeve,
                "decision_bar_iso": dbar, "candidate_id": m.get("candidate_id"),
                "reason": reason, "news_t60_request_keys": request["request_keys"],
                "terminal_stage": "before_admission"})
    return kept, skipped
