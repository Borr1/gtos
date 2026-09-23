"""GOLIVE_vps — live monitoring + alerting (scaffold, read/append-only).

Four monitors, all local-file based (no broker calls of their own — they consume
fills/equity snapshots the runtime already writes, and the deploy module's pure
governor/sizing math):

  1. parity ledger      — live fill R vs the replay/module-expected R per intent.
                          Drift beyond a band -> de-risk recommendation + alert.
  2. daily-DD watch     — equity vs day-start baseline + high-water; compares
                          against the deploy module's GovernorLimits (soft -3%
                          daily stop, -5% hard, 7-10% max-DD de-risk band).
  3. governor breaker   — re-runs evaluate_governor() on the current account state
                          so monitoring and execution share ONE governor truth.
  4. owner alert hook   — pluggable sink (default: append to a JSONL + stderr).
                          Owner wires email/Telegram/push at go-live.

Parity is the contract that lets size step up: live fills MUST track the pessimistic
geometry_lib labeler the book was validated against before any size increase.
"""

from __future__ import annotations

import json
import os
import sys
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable, Optional

# ---- ledger / alert sink paths (under pipeline_state, namespaced per account) ----
PARITY_LEDGER = "pipeline_state/{ns}/golive_live_replay_parity_ledger.jsonl"
DD_WATCH_LEDGER = "pipeline_state/{ns}/golive_daily_dd_watch.jsonl"
ALERT_LEDGER = "pipeline_state/{ns}/golive_owner_alerts.jsonl"

# ---- drift bands (tune with live data; conservative defaults) ----
PARITY_DRIFT_WARN_R = 0.15    # mean |live-replay| R per fill -> warn
PARITY_DRIFT_DERISK_R = 0.30  # -> recommend de-risk (size_cap down)
PARITY_MIN_FILLS = 10         # need this many fills before drift is actionable


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _repo_root(repo_root: Optional[str | Path]) -> Path:
    if repo_root:
        return Path(repo_root)
    # monitoring=0, GOLIVE_vps_deploy=1, route=2, operations=3, research=4, root=5
    return Path(__file__).resolve().parents[5]


def _ledger_path(template: str, ns: str, repo_root: Optional[str | Path]) -> Path:
    root = _repo_root(repo_root)
    p = root / template.format(ns=ns or "default")
    p.parent.mkdir(parents=True, exist_ok=True)
    return p


# --------------------------------------------------------------------------- #
# 1. Live-vs-replay parity ledger
# --------------------------------------------------------------------------- #
@dataclass
class ParityRow:
    intent_id: str
    sleeve: str
    symbol: str
    live_R: float
    replay_R: float          # the deploy module / geometry_lib expected R
    recorded_at_utc: str = field(default_factory=_now)

    @property
    def drift_R(self) -> float:
        return self.live_R - self.replay_R


def record_parity(row: ParityRow, *, namespace: str = "default",
                  repo_root: Optional[str | Path] = None) -> dict[str, Any]:
    path = _ledger_path(PARITY_LEDGER, namespace, repo_root)
    rec = asdict(row); rec["drift_R"] = row.drift_R
    with path.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(rec, sort_keys=True) + "\n")
    return rec


def parity_summary(*, namespace: str = "default",
                   repo_root: Optional[str | Path] = None) -> dict[str, Any]:
    path = _ledger_path(PARITY_LEDGER, namespace, repo_root)
    drifts: list[float] = []
    if path.exists():
        for line in path.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line:
                continue
            try:
                drifts.append(float(json.loads(line)["drift_R"]))
            except (ValueError, KeyError):
                continue
    n = len(drifts)
    mean_abs = sum(abs(d) for d in drifts) / n if n else 0.0
    mean_signed = sum(drifts) / n if n else 0.0
    if n < PARITY_MIN_FILLS:
        verdict = "insufficient_fills"
    elif mean_abs >= PARITY_DRIFT_DERISK_R:
        verdict = "derisk"
    elif mean_abs >= PARITY_DRIFT_WARN_R:
        verdict = "warn"
    else:
        verdict = "ok"
    return {"n_fills": n, "mean_abs_drift_R": round(mean_abs, 4),
            "mean_signed_drift_R": round(mean_signed, 4), "verdict": verdict,
            "warn_band_R": PARITY_DRIFT_WARN_R, "derisk_band_R": PARITY_DRIFT_DERISK_R}


# --------------------------------------------------------------------------- #
# 2. Daily-DD watch (uses the deploy module governor limits)
# --------------------------------------------------------------------------- #
def daily_dd_watch(*, equity: float, day_start_balance: float, high_water: float,
                   namespace: str = "default",
                   limits: Optional[Any] = None,
                   repo_root: Optional[str | Path] = None) -> dict[str, Any]:
    """Compute daily loss % and max-DD %, classify against governor bands.
    ``limits`` is the deploy module's GovernorLimits (imported by the caller to keep
    one source of truth); falls back to the published FINAL-book defaults."""
    soft, hard, maxdd, derisk_start = 0.03, 0.05, 0.10, 0.07
    if limits is not None:
        soft = getattr(limits, "soft_daily_stop_pct", soft)
        hard = getattr(limits, "hard_daily_limit_pct", hard)
        maxdd = getattr(limits, "max_dd_limit_pct", maxdd)
        derisk_start = getattr(limits, "derisk_start_dd_pct", derisk_start)

    daily_loss = max(0.0, (day_start_balance - equity) / day_start_balance) if day_start_balance else 0.0
    dd = max(0.0, (high_water - equity) / high_water) if high_water else 0.0

    if daily_loss >= hard or dd >= maxdd:
        state = "breach"
    elif daily_loss >= soft or dd >= derisk_start:
        state = "derisk"
    else:
        state = "ok"

    row = {"recorded_at_utc": _now(), "equity": equity,
           "day_start_balance": day_start_balance, "high_water": high_water,
           "daily_loss_pct": round(daily_loss, 5), "max_dd_pct": round(dd, 5),
           "soft_daily_stop_pct": soft, "hard_daily_limit_pct": hard,
           "derisk_start_dd_pct": derisk_start, "max_dd_limit_pct": maxdd,
           "state": state}
    path = _ledger_path(DD_WATCH_LEDGER, namespace, repo_root)
    with path.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(row, sort_keys=True) + "\n")
    return row


# --------------------------------------------------------------------------- #
# 3. Governor circuit-breaker check (delegates to the deploy module if available)
# --------------------------------------------------------------------------- #
def governor_check(state: Any, *, evaluate_governor: Optional[Callable] = None,
                   limits: Optional[Any] = None) -> dict[str, Any]:
    """Run the SAME governor the execution path runs, so monitoring never disagrees
    with the live gate. Caller passes the deploy module's evaluate_governor +
    GovernorState. Fail-closed if not wired."""
    if evaluate_governor is None:
        return {"allow_new_entries": False, "reason": "governor_not_wired_fail_closed"}
    dec = evaluate_governor(state, limits=limits) if limits is not None else evaluate_governor(state)
    out = asdict(dec) if hasattr(dec, "__dataclass_fields__") else dict(dec)
    return out


# --------------------------------------------------------------------------- #
# 4. Owner alert hook (pluggable; default JSONL + stderr)
# --------------------------------------------------------------------------- #
def default_alert_sink(alert: dict[str, Any], *, namespace: str = "default",
                       repo_root: Optional[str | Path] = None) -> None:
    path = _ledger_path(ALERT_LEDGER, namespace, repo_root)
    with path.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(alert, sort_keys=True) + "\n")
    sys.stderr.write(f"[GTOS-ALERT] {alert.get('severity','?')} {alert.get('title','')}\n")


def send_alert(title: str, *, severity: str = "warn", detail: Optional[dict] = None,
               namespace: str = "default", sink: Optional[Callable] = None,
               repo_root: Optional[str | Path] = None) -> dict[str, Any]:
    """Emit an owner alert. The owner wires a real sink (email/Telegram/Slack/push)
    at go-live by passing ``sink=...``; default appends to a JSONL + stderr.

    A webhook can be wired purely via ENV without code changes: if
    ``GTOS_ALERT_WEBHOOK`` is set, the default sink could POST to it (left as a
    documented hook — no network call is made in this scaffold)."""
    alert = {"emitted_at_utc": _now(), "title": title, "severity": severity,
             "detail": detail or {}, "namespace": namespace,
             "webhook_env_present": bool(os.environ.get("GTOS_ALERT_WEBHOOK"))}
    (sink or default_alert_sink)(alert, namespace=namespace, repo_root=repo_root)
    return alert


# --------------------------------------------------------------------------- #
# Orchestration helper: one pass that ties the four monitors together.
# --------------------------------------------------------------------------- #
def run_monitor_cycle(*, equity: float, day_start_balance: float, high_water: float,
                      namespace: str = "default", limits: Optional[Any] = None,
                      repo_root: Optional[str | Path] = None,
                      sink: Optional[Callable] = None) -> dict[str, Any]:
    """Single monitoring pass: DD watch + parity summary + alert routing.
    Returns a combined report; emits an alert if any monitor is non-ok."""
    dd = daily_dd_watch(equity=equity, day_start_balance=day_start_balance,
                        high_water=high_water, namespace=namespace,
                        limits=limits, repo_root=repo_root)
    par = parity_summary(namespace=namespace, repo_root=repo_root)
    report = {"checked_at_utc": _now(), "namespace": namespace,
              "daily_dd": dd, "parity": par}
    # alert routing
    if dd["state"] == "breach":
        send_alert("FTMO DD breach", severity="critical", detail=dd,
                   namespace=namespace, sink=sink, repo_root=repo_root)
        report["action"] = "engage_kill_switch"
    elif dd["state"] == "derisk" or par["verdict"] == "derisk":
        send_alert("De-risk recommended", severity="warn",
                   detail={"dd": dd, "parity": par}, namespace=namespace,
                   sink=sink, repo_root=repo_root)
        report["action"] = "reduce_size_cap"
    elif par["verdict"] == "warn":
        send_alert("Parity drift warning", severity="info", detail=par,
                   namespace=namespace, sink=sink, repo_root=repo_root)
        report["action"] = "watch"
    else:
        report["action"] = "none"
    return report
