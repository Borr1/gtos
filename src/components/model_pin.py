"""Model-id pinning + drift alert (T1.4).

Captures the exact model identifier served by the Anthropic API on each
evaluation call and compares it against the last pinned value. Emits a
Telegram alert AND updates the pin when the served identifier changes.

Why this exists
---------------
We call ``claude-sonnet-4-6`` but don't capture whatever resolved snapshot
(e.g. ``claude-sonnet-4-6-20260101``) Anthropic routes us to. If Anthropic
silently updates the served model, behavior could drift with no visible
cause. This module records the served id per call and alerts on change.

Pin persistence
---------------
Pin state lives at ``knowledge_base/meta/model_pin.json``. Rationale for this
path (vs extending an existing state file):
  - ``knowledge_base/meta/`` already holds durable cross-session state
    (``autocorrelation_baseline.json``, ``equity_peak_state.json``).
  - Single-purpose file; trivial to inspect or blow away if the pin needs
    to be re-seeded.
  - No other file on disk has a natural "per-model-id" schema to extend.

Failure policy
--------------
THIS IS ADDITIVE MONITORING — it MUST NEVER block the trading pipeline.
All file IO, JSON parsing, and Telegram calls are wrapped in broad
try/except. A corrupt pin file is treated as "no pin yet" (first-call-silent
path) rather than crashing or raising. If the notify path fails, the pin
still updates so we don't re-alert on the same drift.
"""

from __future__ import annotations

import json
import logging
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)


# Module-level path constant — tests MUST monkeypatch this via
#   monkeypatch.setattr(model_pin, "PIN_PATH", tmp_path / "model_pin.json")
# to avoid writing into the production pin under the project root.
PIN_PATH: Path = Path("knowledge_base/meta/model_pin.json")


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _load_pin() -> Optional[dict]:
    """Read the pin file. Returns None on missing or corrupt file."""
    try:
        if not PIN_PATH.exists():
            return None
        with open(PIN_PATH, "r", encoding="utf-8") as f:
            data = json.load(f)
        if not isinstance(data, dict):
            logger.warning("model_pin: pin file is not a JSON object - ignoring")
            return None
        return data
    except (OSError, json.JSONDecodeError) as exc:
        logger.warning("model_pin: could not read pin file (%s) - treating as unpinned", exc)
        return None
    except Exception as exc:  # defensive
        logger.warning("model_pin: unexpected error reading pin file (%s)", exc)
        return None


def _save_pin(data: dict) -> bool:
    """Write the pin file atomically-ish. Returns False on failure."""
    try:
        PIN_PATH.parent.mkdir(parents=True, exist_ok=True)
        tmp_path = PIN_PATH.with_suffix(PIN_PATH.suffix + ".tmp")
        with open(tmp_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
        os.replace(tmp_path, PIN_PATH)
        return True
    except Exception as exc:
        logger.warning("model_pin: could not write pin file (%s) - drift detection may miss events", exc)
        return False


def _emit_drift_alert(requested: str, old: str, new: str, response_id: Optional[str]) -> None:
    """Send Telegram alert on model drift. Swallows every failure."""
    try:
        # Import lazily so a misconfigured notifier can never break the analyze path.
        from src.notifications import notify_alert
        msg = (
            f"MODEL DRIFT DETECTED\n"
            f"Requested: {requested}\n"
            f"Previous served: {old}\n"
            f"New served: {new}\n"
            f"Response id: {response_id or 'unknown'}\n"
            f"Investigate: Anthropic may have rerouted the alias."
        )
        notify_alert(msg)
    except Exception as exc:
        logger.warning("model_pin: drift alert notify failed (%s)", exc)


def record_served_model(
    requested_model: str,
    served_model: Optional[str],
    response_id: Optional[str] = None,
) -> dict:
    """Record the served model for this evaluation; alert on drift.

    Returns a dict describing what happened; callers may ignore it. Return
    values:
        {"status": "skipped", "reason": "..."}   — bad input
        {"status": "pinned_first_time", ...}     — no prior pin, silently pinned
        {"status": "no_drift", ...}              — served matches pin
        {"status": "drift", from: ..., to: ...}  — drift, alert attempted

    This function NEVER raises. The return value is for tests/diagnostics.
    """
    # Guard bad inputs — SDK could in theory return None / empty string.
    if not served_model or not isinstance(served_model, str):
        return {"status": "skipped", "reason": "no_served_model"}

    try:
        pin = _load_pin()
        now = _now_iso()

        if pin is None or not pin.get("pinned_model"):
            # First call ever (or corrupt pin) — seed silently, no alert.
            new_pin = {
                "pinned_model": served_model,
                "requested_model": requested_model,
                "first_seen_at": now,
                "pinned_at": now,
                "last_seen_at": now,
                "last_response_id": response_id,
                "drift_history": [],
            }
            _save_pin(new_pin)
            logger.info("model_pin: first-call pin established (%s)", served_model)
            return {"status": "pinned_first_time", "pinned_model": served_model}

        prior_served = pin.get("pinned_model")
        if prior_served == served_model:
            # Happy path — just bump last_seen. A write failure here is non-fatal.
            pin["last_seen_at"] = now
            pin["last_response_id"] = response_id
            pin["requested_model"] = requested_model
            _save_pin(pin)
            return {"status": "no_drift", "pinned_model": served_model}

        # Drift — update pin FIRST so repeated drifts don't re-alert on the
        # same old value, THEN fire the alert.
        drift_event = {
            "at": now,
            "from": prior_served,
            "to": served_model,
            "requested_model": requested_model,
            "response_id": response_id,
        }
        history = pin.get("drift_history") or []
        if not isinstance(history, list):
            history = []
        history.append(drift_event)

        pin["pinned_model"] = served_model
        pin["requested_model"] = requested_model
        pin["pinned_at"] = now
        pin["last_seen_at"] = now
        pin["last_response_id"] = response_id
        pin["drift_history"] = history
        _save_pin(pin)

        logger.warning(
            "model_pin: DRIFT - requested=%s served=%s (was %s)",
            requested_model, served_model, prior_served,
        )
        # Belt-and-suspenders: _emit_drift_alert already swallows notify_alert
        # exceptions internally, but wrap the outer call too so a patched-broken
        # emitter (or ImportError) can never escape and mask the drift status.
        try:
            _emit_drift_alert(requested_model, prior_served, served_model, response_id)
        except Exception as exc:
            logger.warning("model_pin: drift alert emission failed (%s)", exc)

        return {
            "status": "drift",
            "from": prior_served,
            "to": served_model,
            "response_id": response_id,
        }
    except Exception as exc:
        # Truly unreachable given inner try/excepts, but belt-and-suspenders:
        # the trading pipeline MUST NOT be affected by this monitor.
        logger.warning("model_pin: record_served_model swallowed unexpected error (%s)", exc)
        return {"status": "skipped", "reason": f"unexpected_error: {exc}"}
