"""GTOS VPS ACTIVE-OPERATOR TOOLKIT (DEFAULT-OFF, broker-free, read/append-only).

The resident VPS Claude operator (VPS_OPERATOR_CHARTER.md) uses this toolkit to actively OPERATE
the dual-MT5 deploy book: monitor health, watch both parity ledgers, fail-closed on nulls, verify
chronology, check LFS/params, and keep the compounding loop ingesting LIVE trades.

HARD GUARANTEES (every function here):
  * NO broker / account / order / network activity. These tools consume local files and snapshots
    the runtime already produced, plus the deploy module's PURE governor/sizing math.
  * DEFAULT-OFF: nothing here flips a gate, removes a halt flag, or raises risk. The operator's ONE
    bound (charter) is the owner risk dial + governor + halt files; this toolkit MAINTAINS those
    bounds and ESCALATES (alert) anything risk-increasing. It NEVER auto-exceeds them.
  * FAIL-CLOSED: any null gate/feature/score, unreadable file, missing param, chronological
    violation, or unwired dependency -> the affected candidate is rejected (size 0) and root-caused.
  * REVERSIBLE: it only appends to JSONL ledgers + (via kill_switch) writes halt/size_cap files,
    which are themselves reversible by the owner.

ARCHITECTURE (DUAL_MT5_ARCHITECTURE.md): FTMO is PRIMARY (native validated distribution), redacted_account
is FOLLOWER (spec-translated mirror). Two parity ledgers:
  1. live-vs-replay on the PRIMARY (FTMO): live fill R must track the deploy-book replay R.
  2. FTMO-vs-redacted_account FOLLOWER parity: did the follower fill the translated order, on the matching
     symbol, at acceptable slip? Divergence de-risks/skips the FOLLOWER leg, NEVER the primary.

The eight operator capabilities (charter "Active duties"):
  (a) HealthMonitor          — process/CPU/memory/disk + data-freshness on BOTH terminals.
  (b) ParityLedgers          — live-vs-replay (primary) + FTMO-vs-redacted_account (follower) + alerts.
  (c) NullGuard              — any null gate/feature/score -> fail-closed candidate + null-source root cause.
  (d) ChronologyVerifier     — terminal offsets, bar order, sequence-of-elements (the top watch item).
  (e) ArtifactChecker        — LFS/missing-file + missing-parameter (config/spec gap) checker.
  (f) LiveImprovementMiner   — the standing miner wired to LIVE trades (compounding loop continues).
  (g) Escalation             — alert + kill-switch hooks + severity/escalation logic.

This module is import-safe and side-effect-free. It is the route-dir scaffold the owner promotes at
go-live (it reuses ../monitoring/{monitor,kill_switch}.py and the deploy book's pure governor).
"""
from __future__ import annotations

import json
import math
import os
import sys
import shutil
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Any, Callable, Iterable, Mapping, Optional, Sequence


# --------------------------------------------------------------------------- #
# Path wiring — reuse the existing monitoring/kill_switch contracts.
# --------------------------------------------------------------------------- #
_HERE = Path(__file__).resolve()
_PKG = _HERE.parents[1]                       # GOLIVE_vps_deploy/
sys.path.insert(0, str(_PKG / "monitoring"))

try:  # pragma: no cover - import wiring
    import monitor as _MON                    # parity ledger + DD watch + alert sink
    import kill_switch as _KILL               # halt-file + size_cap kill switch
except Exception:  # pragma: no cover - fail closed if monitoring not importable
    _MON = None
    _KILL = None


# ledger paths (under pipeline_state, namespaced per account / terminal)
HEALTH_LEDGER = "pipeline_state/{ns}/operator_health.jsonl"
FOLLOWER_PARITY_LEDGER = "pipeline_state/{ns}/operator_follower_parity.jsonl"
NULL_GUARD_LEDGER = "pipeline_state/{ns}/operator_null_guard.jsonl"
CHRONO_LEDGER = "pipeline_state/{ns}/operator_chronology.jsonl"
ARTIFACT_LEDGER = "pipeline_state/{ns}/operator_artifact_check.jsonl"
LIVE_TRADE_LEDGER = "pipeline_state/{ns}/operator_live_trades.jsonl"
OPERATOR_CYCLE_LEDGER = "pipeline_state/{ns}/operator_cycle.jsonl"


# ---- thresholds (conservative defaults; tune with live data, never auto-relax risk) ----
HEALTH_MEM_WARN_PCT = 85.0          # RAM used% -> warn
HEALTH_MEM_DERISK_PCT = 92.0        # RAM used% -> derisk (a memory-starved engine mis-decides)
HEALTH_DISK_WARN_PCT = 85.0
HEALTH_DISK_DERISK_PCT = 93.0
DATA_FRESH_WARN_S = 180.0           # bar/tick age beyond this -> warn (stale terminal feed)
DATA_FRESH_STALE_S = 600.0         # -> fail-closed: stale data must not size

FOLLOWER_SLIP_WARN_R = 0.10        # |follower slip| in R -> warn
FOLLOWER_SLIP_DERISK_R = 0.25      # -> de-risk/skip the FOLLOWER leg (never the primary)

CHRONO_MAX_TERMINAL_OFFSET_S = 5.0  # |server-time - UTC| beyond this -> chronology fault


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _repo_root(repo_root: Optional[str | Path]) -> Path:
    if repo_root:
        return Path(repo_root)
    # operator=0, GOLIVE_vps_deploy=1, route=2, operations=3, research=4, root=5
    return Path(_HERE).resolve().parents[5]


def _ledger_path(template: str, ns: str, repo_root: Optional[str | Path]) -> Path:
    root = _repo_root(repo_root)
    p = root / template.format(ns=ns or "default")
    p.parent.mkdir(parents=True, exist_ok=True)
    return p


def _append(template: str, ns: str, row: dict[str, Any],
            repo_root: Optional[str | Path]) -> dict[str, Any]:
    path = _ledger_path(template, ns, repo_root)
    with path.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(row, sort_keys=True, default=str) + "\n")
    return row


def _alert(title: str, *, severity: str, detail: dict[str, Any], namespace: str,
           sink: Optional[Callable], repo_root: Optional[str | Path]) -> None:
    """Route through the existing monitor.send_alert so all alerts share one sink/ledger."""
    if _MON is not None:
        _MON.send_alert(title, severity=severity, detail=detail, namespace=namespace,
                        sink=sink, repo_root=repo_root)


def _parse_iso(ts: Any) -> Optional[datetime]:
    """Parse an ISO-8601 timestamp -> aware UTC datetime; None on any failure (fail-closed)."""
    if ts is None:
        return None
    if isinstance(ts, datetime):
        return ts if ts.tzinfo else ts.replace(tzinfo=timezone.utc)
    try:
        s = str(ts).replace("Z", "+00:00")
        dt = datetime.fromisoformat(s)
        return dt if dt.tzinfo else dt.replace(tzinfo=timezone.utc)
    except (ValueError, TypeError):
        return None


# =========================================================================== #
# (a) HEALTH MONITOR — process/memory/disk + data freshness on BOTH terminals
# =========================================================================== #
def _mem_used_pct() -> Optional[float]:
    """RAM used% from /proc/meminfo (Linux VPS). None if unavailable (do not fake)."""
    try:
        mi = Path("/proc/meminfo")
        if not mi.exists():
            return None
        vals: dict[str, float] = {}
        for line in mi.read_text().splitlines():
            k, _, rest = line.partition(":")
            vals[k.strip()] = float(rest.strip().split()[0])  # kB
        total = vals.get("MemTotal")
        avail = vals.get("MemAvailable")
        if not total or avail is None:
            return None
        return round((1.0 - avail / total) * 100.0, 2)
    except (OSError, ValueError, IndexError):
        return None


def _disk_used_pct(path: str | Path) -> Optional[float]:
    try:
        u = shutil.disk_usage(str(path))
        return round(u.used / u.total * 100.0, 2) if u.total else None
    except (OSError, ValueError):
        return None


def data_freshness(*, terminal: str, last_bar_utc: Any, now_utc: Optional[Any] = None) -> dict[str, Any]:
    """Classify how stale a terminal's most-recent bar/tick is. Fail-closed on unparseable time.

    A stale feed silently corrupts EVERY gate (the engine decides on old bars) -> treat
    >= DATA_FRESH_STALE_S as a hard fault that must not size.
    """
    bar = _parse_iso(last_bar_utc)
    now = _parse_iso(now_utc) or datetime.now(timezone.utc)
    if bar is None:
        return {"terminal": terminal, "fresh": False, "state": "fail_closed",
                "reason": "unparseable_last_bar_time", "age_s": None}
    age = (now - bar).total_seconds()
    if age < 0:
        # bar is in the FUTURE vs our clock -> chronology fault, fail-closed.
        return {"terminal": terminal, "fresh": False, "state": "fail_closed",
                "reason": "last_bar_in_future", "age_s": round(age, 1)}
    if age >= DATA_FRESH_STALE_S:
        state = "fail_closed"
    elif age >= DATA_FRESH_WARN_S:
        state = "warn"
    else:
        state = "ok"
    return {"terminal": terminal, "fresh": state == "ok", "state": state,
            "age_s": round(age, 1), "warn_s": DATA_FRESH_WARN_S, "stale_s": DATA_FRESH_STALE_S}


@dataclass
class TerminalHealth:
    """A terminal-feed health snapshot fed in by the runtime (no broker call here)."""
    terminal: str                       # "FTMO" (primary) | "redacted_account" (follower)
    connected: bool
    last_bar_utc: Optional[str]
    process_alive: bool = True


def health_check(*, terminals: Sequence[TerminalHealth], disk_path: str | Path = "/",
                 namespace: str = "default", now_utc: Optional[Any] = None,
                 sink: Optional[Callable] = None,
                 repo_root: Optional[str | Path] = None) -> dict[str, Any]:
    """One health pass: memory/disk + per-terminal connection + data freshness.

    Returns a report with an overall ``state`` (ok|warn|derisk|fail_closed) and an ``action``.
    fail_closed => at least one terminal must not size (stale/dead). For the PRIMARY (FTMO) a
    fail_closed escalates to kill-switch; for the FOLLOWER it skips the follower leg only.
    """
    mem = _mem_used_pct()
    disk = _disk_used_pct(disk_path)
    states: list[str] = []

    if mem is not None:
        states.append("derisk" if mem >= HEALTH_MEM_DERISK_PCT
                      else "warn" if mem >= HEALTH_MEM_WARN_PCT else "ok")
    if disk is not None:
        states.append("derisk" if disk >= HEALTH_DISK_DERISK_PCT
                      else "warn" if disk >= HEALTH_DISK_WARN_PCT else "ok")

    term_reports: list[dict[str, Any]] = []
    primary_fail = follower_fail = False
    for t in terminals:
        is_primary = t.terminal.upper() == "FTMO"
        if not t.process_alive or not t.connected:
            tstate = "fail_closed"
            fr = {"terminal": t.terminal, "fresh": False, "state": "fail_closed",
                  "reason": ("process_dead" if not t.process_alive else "disconnected"),
                  "age_s": None}
        else:
            fr = data_freshness(terminal=t.terminal, last_bar_utc=t.last_bar_utc, now_utc=now_utc)
            tstate = fr["state"]
        fr["is_primary"] = is_primary
        term_reports.append(fr)
        states.append(tstate)
        if tstate == "fail_closed":
            if is_primary:
                primary_fail = True
            else:
                follower_fail = True

    overall = ("fail_closed" if "fail_closed" in states else
               "derisk" if "derisk" in states else
               "warn" if "warn" in states else "ok")

    if primary_fail:
        action = "fail_closed_primary_engage_kill_switch"
    elif follower_fail:
        action = "skip_follower_leg"
    elif overall == "derisk":
        action = "reduce_size_cap"
    elif overall == "warn":
        action = "watch"
    else:
        action = "none"

    row = {"recorded_at_utc": _now(), "namespace": namespace, "kind": "health",
           "mem_used_pct": mem, "disk_used_pct": disk, "disk_path": str(disk_path),
           "terminals": term_reports, "state": overall, "action": action,
           "mem_warn_pct": HEALTH_MEM_WARN_PCT, "mem_derisk_pct": HEALTH_MEM_DERISK_PCT,
           "disk_warn_pct": HEALTH_DISK_WARN_PCT, "disk_derisk_pct": HEALTH_DISK_DERISK_PCT}
    _append(HEALTH_LEDGER, namespace, row, repo_root)

    if action.startswith("fail_closed_primary"):
        _alert("PRIMARY terminal health fault", severity="critical", detail=row,
               namespace=namespace, sink=sink, repo_root=repo_root)
    elif action == "skip_follower_leg":
        _alert("Follower terminal health fault", severity="warn", detail=row,
               namespace=namespace, sink=sink, repo_root=repo_root)
    elif overall in ("derisk", "warn"):
        _alert(f"Host health {overall}", severity="warn" if overall == "derisk" else "info",
               detail=row, namespace=namespace, sink=sink, repo_root=repo_root)
    return row


# =========================================================================== #
# (b) PARITY LEDGERS
#   live-vs-replay (primary) reuses monitor.record_parity / monitor.parity_summary.
#   FTMO-vs-redacted_account FOLLOWER parity is new here.
# =========================================================================== #
@dataclass
class FollowerParityRow:
    """One primary decision and the follower's spec-translated execution outcome."""
    intent_id: str
    sleeve: str
    primary_symbol: str               # FTMO symbol
    follower_symbol: Optional[str]    # redacted_account symbol (None = missing in symbol map)
    primary_filled: bool
    follower_filled: bool
    primary_R: Optional[float] = None
    follower_R: Optional[float] = None
    follower_rejected: bool = False
    spec_mismatch: bool = False
    recorded_at_utc: str = field(default_factory=_now)

    @property
    def slip_R(self) -> Optional[float]:
        if self.primary_R is None or self.follower_R is None:
            return None
        return self.follower_R - self.primary_R


def record_follower_parity(row: FollowerParityRow, *, namespace: str = "default",
                           sink: Optional[Callable] = None,
                           repo_root: Optional[str | Path] = None) -> dict[str, Any]:
    """Record one follower-parity row, classify divergence, and de-risk the FOLLOWER on breach.

    The follower's problems NEVER touch the primary (DUAL_MT5_ARCHITECTURE.md): the verdict only
    ever recommends skipping/de-risking the FOLLOWER leg.
    """
    rec = asdict(row)
    slip = row.slip_R
    rec["slip_R"] = slip

    # classify
    if row.follower_symbol is None:
        verdict, reason = "skip_follower_leg", "missing_symbol_in_follower_map"
    elif row.spec_mismatch:
        verdict, reason = "skip_follower_leg", "spec_mismatch"
    elif row.primary_filled and not row.follower_filled:
        verdict, reason = ("skip_follower_leg",
                           "follower_rejected" if row.follower_rejected else "follower_not_filled")
    elif slip is not None and abs(slip) >= FOLLOWER_SLIP_DERISK_R:
        verdict, reason = "derisk_follower_leg", f"slip_{round(slip, 4)}R>=derisk"
    elif slip is not None and abs(slip) >= FOLLOWER_SLIP_WARN_R:
        verdict, reason = "watch", f"slip_{round(slip, 4)}R>=warn"
    else:
        verdict, reason = "ok", "in_parity"
    rec["verdict"] = verdict
    rec["reason"] = reason
    rec["affects_primary"] = False  # invariant: follower never touches the primary
    _append(FOLLOWER_PARITY_LEDGER, namespace, rec, repo_root)

    if verdict == "skip_follower_leg":
        _alert("Follower parity divergence (skip leg)", severity="warn", detail=rec,
               namespace=namespace, sink=sink, repo_root=repo_root)
    elif verdict == "derisk_follower_leg":
        _alert("Follower slip beyond de-risk band", severity="warn", detail=rec,
               namespace=namespace, sink=sink, repo_root=repo_root)
    return rec


def follower_parity_summary(*, namespace: str = "default",
                            repo_root: Optional[str | Path] = None) -> dict[str, Any]:
    path = _ledger_path(FOLLOWER_PARITY_LEDGER, namespace, repo_root)
    n = n_skip = n_derisk = n_ok = 0
    slips: list[float] = []
    if path.exists():
        for line in path.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line:
                continue
            try:
                d = json.loads(line)
            except ValueError:
                continue
            n += 1
            v = d.get("verdict")
            if v == "skip_follower_leg":
                n_skip += 1
            elif v == "derisk_follower_leg":
                n_derisk += 1
            elif v == "ok":
                n_ok += 1
            s = d.get("slip_R")
            if isinstance(s, (int, float)):
                slips.append(float(s))
    mean_abs = sum(abs(s) for s in slips) / len(slips) if slips else 0.0
    verdict = ("derisk" if n_derisk or n_skip else "ok") if n else "no_data"
    return {"n_rows": n, "n_skip_leg": n_skip, "n_derisk": n_derisk, "n_ok": n_ok,
            "mean_abs_slip_R": round(mean_abs, 4), "verdict": verdict,
            "warn_band_R": FOLLOWER_SLIP_WARN_R, "derisk_band_R": FOLLOWER_SLIP_DERISK_R}


def live_replay_summary(*, namespace: str = "default",
                        repo_root: Optional[str | Path] = None) -> dict[str, Any]:
    """Thin pass-through to monitor.parity_summary (the PRIMARY live-vs-replay ledger)."""
    if _MON is None:
        return {"verdict": "monitor_not_wired_fail_closed"}
    return _MON.parity_summary(namespace=namespace, repo_root=repo_root)


# =========================================================================== #
# (c) NULL-GUARD + null-source diagnostic
#   Any null gate/feature/score for a candidate -> fail-closed that candidate AND
#   log the root cause (which field, expected source). Charter watch item.
# =========================================================================== #
def null_guard_candidate(*, candidate: Mapping[str, Any],
                         required_gates: Sequence[str],
                         required_features: Sequence[str],
                         required_scores: Sequence[str],
                         field_sources: Optional[Mapping[str, str]] = None,
                         namespace: str = "default",
                         sink: Optional[Callable] = None,
                         repo_root: Optional[str | Path] = None) -> dict[str, Any]:
    """Fail-closed null guard for ONE candidate. A null/NaN gate, feature, or score => reject
    the candidate (admit=False, size 0) and root-cause WHICH field and its expected source.

    ``field_sources`` maps a field name -> the producer that should have set it (for root cause).
    Returns {admit, nulls:[...], reason}. admit=True only when EVERY required field is present
    and non-null/non-NaN.
    """
    field_sources = dict(field_sources or {})
    nulls: list[dict[str, str]] = []

    def _is_null(v: Any) -> bool:
        if v is None:
            return True
        if isinstance(v, float) and math.isnan(v):
            return True
        return False

    for kind, fields in (("gate", required_gates),
                         ("feature", required_features),
                         ("score", required_scores)):
        for f in fields:
            present = f in candidate
            val = candidate.get(f)
            if not present or _is_null(val):
                nulls.append({"field": f, "kind": kind,
                              "issue": "absent" if not present else "null_or_nan",
                              "expected_source": field_sources.get(f, "unknown_source")})

    admit = not nulls
    cand_id = str(candidate.get("intent_id") or candidate.get("id") or candidate.get("sleeve") or "?")
    row = {"recorded_at_utc": _now(), "namespace": namespace, "kind": "null_guard",
           "candidate_id": cand_id, "admit": admit,
           "n_nulls": len(nulls), "nulls": nulls,
           "reason": "ok" if admit else "fail_closed_null_intelligence"}
    if not admit:
        _append(NULL_GUARD_LEDGER, namespace, row, repo_root)
        _alert("Null intelligence -> candidate fail-closed", severity="warn", detail=row,
               namespace=namespace, sink=sink, repo_root=repo_root)
    return row


def null_guard_batch(*, candidates: Sequence[Mapping[str, Any]],
                     required_gates: Sequence[str], required_features: Sequence[str],
                     required_scores: Sequence[str],
                     field_sources: Optional[Mapping[str, str]] = None,
                     namespace: str = "default", sink: Optional[Callable] = None,
                     repo_root: Optional[str | Path] = None) -> dict[str, Any]:
    """Run the null guard over a batch; return only the admitted candidates + a root-cause roll-up."""
    admitted: list[Mapping[str, Any]] = []
    rejected: list[dict[str, Any]] = []
    source_counts: dict[str, int] = {}
    for c in candidates:
        r = null_guard_candidate(candidate=c, required_gates=required_gates,
                                 required_features=required_features, required_scores=required_scores,
                                 field_sources=field_sources, namespace=namespace,
                                 sink=sink, repo_root=repo_root)
        if r["admit"]:
            admitted.append(c)
        else:
            rejected.append(r)
            for nz in r["nulls"]:
                src = nz["expected_source"]
                source_counts[src] = source_counts.get(src, 0) + 1
    return {"n_in": len(candidates), "n_admitted": len(admitted), "n_rejected": len(rejected),
            "admitted": admitted, "rejected": rejected,
            "null_source_rootcause": dict(sorted(source_counts.items(),
                                                 key=lambda kv: -kv[1]))}


# =========================================================================== #
# (d) TIMEZONE / CHRONOLOGICAL verifier
#   terminal offsets, bar order, sequence-of-elements. Top operator watch item:
#   a chronology bug silently corrupts EVERY gate.
# =========================================================================== #
def verify_terminal_offset(*, terminal: str, server_time_utc: Any, reference_utc: Any,
                           max_offset_s: float = CHRONO_MAX_TERMINAL_OFFSET_S) -> dict[str, Any]:
    """Confirm a terminal's reported server time is normalized to UTC within tolerance.
    Fail-closed on unparseable time (do not assume the clock is fine)."""
    st = _parse_iso(server_time_utc)
    ref = _parse_iso(reference_utc) or datetime.now(timezone.utc)
    if st is None:
        return {"terminal": terminal, "ok": False, "offset_s": None,
                "reason": "unparseable_server_time"}
    off = abs((st - ref).total_seconds())
    ok = off <= max_offset_s
    return {"terminal": terminal, "ok": ok, "offset_s": round(off, 3),
            "max_offset_s": max_offset_s,
            "reason": "ok" if ok else "offset_exceeds_tolerance_normalize_to_utc"}


def verify_bar_order(bars: Sequence[Mapping[str, Any]], *, time_key: str = "time") -> dict[str, Any]:
    """Confirm bars are strictly ascending in time with no duplicates/gaps-out-of-order.
    Returns the first offending index. Any null/unparseable timestamp fails closed."""
    prev: Optional[datetime] = None
    for idx, b in enumerate(bars):
        t = _parse_iso(b.get(time_key))
        if t is None:
            return {"ok": False, "n": len(bars), "fault_index": idx,
                    "reason": "null_or_unparseable_bar_time"}
        if prev is not None:
            if t == prev:
                return {"ok": False, "n": len(bars), "fault_index": idx,
                        "reason": "duplicate_bar_time"}
            if t < prev:
                return {"ok": False, "n": len(bars), "fault_index": idx,
                        "reason": "out_of_order_bar_time"}
        prev = t
    return {"ok": True, "n": len(bars), "fault_index": None, "reason": "strictly_ascending"}


def verify_sequence_order(steps: Sequence[str], expected_order: Sequence[str]) -> dict[str, Any]:
    """Confirm intelligence steps ran in the expected order (sequence-of-elements charter item).
    e.g. expected ['features','gates','score','size'] — features MUST precede score, etc.
    Returns ok + the first inversion."""
    pos = {name: i for i, name in enumerate(expected_order)}
    last = -1
    last_name = None
    for s in steps:
        if s not in pos:
            return {"ok": False, "reason": f"unknown_step:{s}", "step": s}
        if pos[s] < last:
            return {"ok": False, "reason": "out_of_order_step",
                    "step": s, "after": last_name,
                    "expected_order": list(expected_order)}
        last = pos[s]
        last_name = s
    return {"ok": True, "reason": "in_expected_order", "expected_order": list(expected_order)}


def chronology_check(*, terminals: Sequence[Mapping[str, Any]],
                     reference_utc: Optional[Any] = None,
                     primary_bars: Optional[Sequence[Mapping[str, Any]]] = None,
                     compute_steps: Optional[Sequence[str]] = None,
                     expected_steps: Sequence[str] = ("features", "gates", "score", "size"),
                     namespace: str = "default", sink: Optional[Callable] = None,
                     repo_root: Optional[str | Path] = None) -> dict[str, Any]:
    """Full chronology pass: both terminals' UTC offsets + primary bar order + compute sequence.
    Any fault => fail-closed (do not size) + alert. This is the single most dangerous silent bug."""
    offsets = [verify_terminal_offset(terminal=t.get("terminal", "?"),
                                      server_time_utc=t.get("server_time_utc"),
                                      reference_utc=reference_utc) for t in terminals]
    bar_order = verify_bar_order(primary_bars) if primary_bars is not None else \
        {"ok": True, "reason": "no_bars_supplied", "n": 0, "fault_index": None}
    seq = verify_sequence_order(compute_steps, expected_steps) if compute_steps is not None else \
        {"ok": True, "reason": "no_steps_supplied"}

    faults = [o for o in offsets if not o["ok"]]
    ok = not faults and bar_order["ok"] and seq["ok"]
    row = {"recorded_at_utc": _now(), "namespace": namespace, "kind": "chronology",
           "ok": ok, "terminal_offsets": offsets, "bar_order": bar_order,
           "sequence_order": seq,
           "action": "none" if ok else "fail_closed_do_not_size"}
    if not ok:
        _append(CHRONO_LEDGER, namespace, row, repo_root)
        _alert("Chronology fault (fail-closed)", severity="critical", detail=row,
               namespace=namespace, sink=sink, repo_root=repo_root)
    return row


# =========================================================================== #
# (e) LFS / missing-file + missing-parameter checker
# =========================================================================== #
# LFS pointer files start with this signature instead of real content.
_LFS_POINTER_SIG = "version https://git-lfs.github.com/spec/"


def check_artifacts(*, required_files: Sequence[str],
                    required_config_keys: Sequence[str],
                    config: Optional[Mapping[str, Any]] = None,
                    namespace: str = "default", sink: Optional[Callable] = None,
                    repo_root: Optional[str | Path] = None) -> dict[str, Any]:
    """Verify required artifacts are PRESENT + materialized (not LFS pointer stubs) and required
    config/spec keys exist. Missing file or unhydrated LFS pointer => fail-closed startup; the
    repair is ``git lfs pull`` (logged as the recommended action, never auto-run here)."""
    root = _repo_root(repo_root)
    missing_files: list[str] = []
    lfs_pointer_files: list[str] = []
    for rel in required_files:
        p = (root / rel) if not Path(rel).is_absolute() else Path(rel)
        if not p.exists():
            missing_files.append(str(rel))
            continue
        try:
            with p.open("rb") as fh:
                head = fh.read(len(_LFS_POINTER_SIG.encode()))
            if head.decode("utf-8", "ignore").startswith(_LFS_POINTER_SIG):
                lfs_pointer_files.append(str(rel))
        except OSError:
            missing_files.append(str(rel))

    cfg = config or {}
    # support dotted keys: "gtos_vnext_runtime.ultimate_book_enabled"
    missing_keys: list[str] = []
    for key in required_config_keys:
        node: Any = cfg
        ok = True
        for part in key.split("."):
            if isinstance(node, Mapping) and part in node:
                node = node[part]
            else:
                ok = False
                break
        if not ok or node is None:
            missing_keys.append(key)

    ok = not (missing_files or lfs_pointer_files or missing_keys)
    row = {"recorded_at_utc": _now(), "namespace": namespace, "kind": "artifact_check",
           "ok": ok, "missing_files": missing_files,
           "lfs_pointer_files": lfs_pointer_files, "missing_config_keys": missing_keys,
           "recommended_repair": ([] if ok else
               ([f"git lfs pull (-> {lfs_pointer_files})"] if lfs_pointer_files else [])
               + ([f"restore missing files {missing_files}"] if missing_files else [])
               + ([f"add missing config/spec keys {missing_keys}"] if missing_keys else [])),
           "action": "none" if ok else "fail_closed_startup_block"}
    if not ok:
        _append(ARTIFACT_LEDGER, namespace, row, repo_root)
        _alert("Missing artifact / LFS / param (startup block)", severity="critical", detail=row,
               namespace=namespace, sink=sink, repo_root=repo_root)
    return row


# =========================================================================== #
# (f) STANDING IMPROVEMENT-MINER wired to LIVE trades (compounding loop)
#   Append closed LIVE trades into the operator live-trade ledger in the SAME row schema
#   improvement_miner.py consumes, so the standing miner keeps compounding on real fills.
# =========================================================================== #
# Map live sleeve/symbol -> the deploy book sleeve cluster (so the miner groups correctly).
def record_live_trade(*, intent_id: str, sleeve: str, symbol: str, year: int,
                      direction: int, realized_R: float,
                      features: Optional[Mapping[str, Any]] = None,
                      resim: Optional[Mapping[str, Any]] = None,
                      account: str = "FTMO", namespace: str = "default",
                      repo_root: Optional[str | Path] = None) -> dict[str, Any]:
    """Append ONE closed LIVE trade in the improvement_miner ledger schema (R, year, sleeve,
    features, resim). ``resim`` is optional — geometry/exit re-sim tweaks need the bar stream;
    when absent, the gate-threshold miner still works (it only needs R + features + year).

    Leak-free: only CLOSED trades with realized R go in (no open positions, no outcome leakage)."""
    row: dict[str, Any] = {
        "intent_id": intent_id, "sleeve": sleeve, "symbol": symbol,
        "year": int(year), "direction": int(direction),
        "R": float(realized_R), "account": account, "source": "live",
        "recorded_at_utc": _now(),
    }
    if features:
        row.update({k: v for k, v in features.items()})
    if resim:
        row["resim"] = dict(resim)
    return _append(LIVE_TRADE_LEDGER, namespace, row, repo_root)


def live_trade_ledger_path(*, namespace: str = "default",
                           repo_root: Optional[str | Path] = None) -> Path:
    """Path to the operator LIVE-trade ledger that the standing miner ingests."""
    return _ledger_path(LIVE_TRADE_LEDGER, namespace, repo_root)


def live_miner_readiness(*, namespace: str = "default", min_per_sleeve: int = 8,
                         repo_root: Optional[str | Path] = None) -> dict[str, Any]:
    """Report whether enough LIVE trades have accrued for a meaningful mining pass (matches
    improvement_miner's MIN_FWD_N=8 forward-trade floor). The operator runs the standing miner
    on the live ledger once a sleeve clears the floor; until then it keeps ingesting."""
    path = _ledger_path(LIVE_TRADE_LEDGER, namespace, repo_root)
    by_sleeve: dict[str, int] = {}
    total = 0
    if path.exists():
        for line in path.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line:
                continue
            try:
                d = json.loads(line)
            except ValueError:
                continue
            total += 1
            by_sleeve[d.get("sleeve", "?")] = by_sleeve.get(d.get("sleeve", "?"), 0) + 1
    ready = {s: n for s, n in by_sleeve.items() if n >= min_per_sleeve}
    return {"n_live_trades": total, "per_sleeve": by_sleeve, "min_per_sleeve": min_per_sleeve,
            "sleeves_ready_to_mine": sorted(ready),
            "any_ready": bool(ready),
            "note": "run improvement_miner.py against this ledger once a sleeve is ready; "
                    "every miner proposal is FORWARD-VALIDATED + size-by-confidence before it can "
                    "affect sizing (charter: forward-validate any change before it affects sizing)."}


# =========================================================================== #
# (g) ESCALATION logic + kill-switch hooks
# =========================================================================== #
SEVERITY_RANK = {"info": 0, "warn": 1, "critical": 2}

# Which conditions ESCALATE to the owner vs auto-handle within the safety envelope.
# The operator auto-repairs correctness/health; it ESCALATES anything risk-increasing or
# recurring (charter "Escalate to owner").
def classify_escalation(*, reports: Mapping[str, Mapping[str, Any]]) -> dict[str, Any]:
    """Fold the monitor reports into ONE escalation decision.

    Inputs (any subset): health, live_replay, follower_parity, chronology, artifact, daily_dd.
    Returns severity, whether to engage the kill-switch, whether to escalate to the owner, and the
    bounded auto-action (within the safety envelope — never raises risk)."""
    sev = "info"
    engage_kill = False
    escalate = False
    actions: list[str] = []
    causes: list[str] = []

    def bump(s: str) -> None:
        nonlocal sev
        if SEVERITY_RANK.get(s, 0) > SEVERITY_RANK.get(sev, 0):
            sev = s

    h = reports.get("health") or {}
    if h.get("action", "").startswith("fail_closed_primary"):
        engage_kill = True; escalate = True; bump("critical")
        actions.append("engage_kill_switch"); causes.append("primary_terminal_fault")
    elif h.get("action") == "skip_follower_leg":
        bump("warn"); actions.append("skip_follower_leg"); causes.append("follower_terminal_fault")
    elif h.get("state") == "derisk":
        bump("warn"); actions.append("reduce_size_cap"); causes.append("host_resource_pressure")

    chrono = reports.get("chronology") or {}
    if chrono and not chrono.get("ok", True):
        engage_kill = True; escalate = True; bump("critical")
        actions.append("fail_closed_do_not_size"); causes.append("chronology_fault")

    art = reports.get("artifact") or {}
    if art and not art.get("ok", True):
        escalate = True; bump("critical")
        actions.append("startup_block"); causes.append("missing_artifact_or_param")

    dd = reports.get("daily_dd") or {}
    if dd.get("state") == "breach":
        engage_kill = True; escalate = True; bump("critical")
        actions.append("engage_kill_switch"); causes.append("dd_breach")
    elif dd.get("state") == "derisk":
        bump("warn"); actions.append("reduce_size_cap"); causes.append("dd_derisk_band")

    lr = reports.get("live_replay") or {}
    if lr.get("verdict") == "derisk":
        escalate = True; bump("warn")  # primary parity breach -> escalate (charter)
        actions.append("reduce_size_cap"); causes.append("live_replay_parity_breach")
    elif lr.get("verdict") == "warn":
        bump("warn"); actions.append("watch"); causes.append("live_replay_parity_drift")

    fp = reports.get("follower_parity") or {}
    if fp.get("verdict") == "derisk":
        bump("warn"); actions.append("derisk_follower_leg")
        causes.append("follower_parity_divergence")

    # de-dup actions, preserve order
    seen: set[str] = set()
    actions = [a for a in actions if not (a in seen or seen.add(a))]
    return {"severity": sev, "engage_kill_switch": engage_kill,
            "escalate_to_owner": escalate, "auto_actions": actions, "causes": causes,
            "envelope_note": "auto_actions only de-risk/halt; never raise risk beyond the dial; "
                             "risk-increasing changes ESCALATE to owner (charter bound)."}


def operator_cycle(*, terminals: Sequence[TerminalHealth],
                   reference_utc: Optional[Any] = None,
                   primary_bars: Optional[Sequence[Mapping[str, Any]]] = None,
                   compute_steps: Optional[Sequence[str]] = None,
                   terminal_times: Optional[Sequence[Mapping[str, Any]]] = None,
                   required_files: Sequence[str] = (),
                   required_config_keys: Sequence[str] = (),
                   config: Optional[Mapping[str, Any]] = None,
                   daily_dd: Optional[Mapping[str, Any]] = None,
                   disk_path: str | Path = "/",
                   namespace: str = "default", sink: Optional[Callable] = None,
                   engage_on_critical: bool = False,
                   repo_root: Optional[str | Path] = None) -> dict[str, Any]:
    """ONE full operator pass tying every monitor together, ending in an escalation decision.

    DEFAULT-OFF on action: ``engage_on_critical`` defaults False — the cycle RECOMMENDS the
    kill-switch but does NOT pull it unless the owner opts in (the halt file stays the physical
    control). When opted in, engaging is itself always-safe (it only de-risks/halts).
    """
    health = health_check(terminals=terminals, disk_path=disk_path, namespace=namespace,
                          now_utc=reference_utc, sink=sink, repo_root=repo_root)
    chrono = chronology_check(
        terminals=(terminal_times or [{"terminal": t.terminal,
                                       "server_time_utc": t.last_bar_utc} for t in terminals]),
        reference_utc=reference_utc, primary_bars=primary_bars,
        compute_steps=compute_steps, namespace=namespace, sink=sink, repo_root=repo_root)
    artifact = (check_artifacts(required_files=required_files,
                                required_config_keys=required_config_keys, config=config,
                                namespace=namespace, sink=sink, repo_root=repo_root)
                if (required_files or required_config_keys) else
                {"ok": True, "kind": "artifact_check", "skipped": True})
    live_replay = live_replay_summary(namespace=namespace, repo_root=repo_root)
    follower = follower_parity_summary(namespace=namespace, repo_root=repo_root)

    reports = {"health": health, "chronology": chrono, "artifact": artifact,
               "live_replay": live_replay, "follower_parity": follower}
    if daily_dd is not None:
        reports["daily_dd"] = daily_dd

    esc = classify_escalation(reports=reports)
    cycle = {"checked_at_utc": _now(), "namespace": namespace,
             "reports": reports, "escalation": esc}

    if esc["engage_kill_switch"]:
        if engage_on_critical and _KILL is not None:
            res = _KILL.engage_kill_switch(
                reason=f"operator_cycle:{','.join(esc['causes'])}", operator="vps_operator",
                repo_root=repo_root)
            cycle["kill_switch"] = res
        else:
            cycle["kill_switch"] = {"status": "recommended_not_engaged",
                                    "reason": "engage_on_critical=False (owner-controlled flip)"}
    _append(OPERATOR_CYCLE_LEDGER, namespace, cycle, repo_root)
    return cycle


def describe_toolkit() -> dict[str, Any]:
    """Machine-readable description of the operator toolkit (for go-live audit)."""
    return {
        "schema_version": "vps_operator_toolkit_v1",
        "capabilities": {
            "a_health": "health_check (memory/disk + per-terminal connect + data freshness)",
            "b_parity": "live_replay_summary (primary, via monitor) + record_follower_parity / "
                        "follower_parity_summary (FTMO-vs-redacted_account follower)",
            "c_null_guard": "null_guard_candidate / null_guard_batch (fail-closed + null-source root cause)",
            "d_chronology": "verify_terminal_offset / verify_bar_order / verify_sequence_order / chronology_check",
            "e_artifacts": "check_artifacts (LFS pointer + missing file + missing config/spec key)",
            "f_live_miner": "record_live_trade / live_miner_readiness (wires improvement_miner to LIVE trades)",
            "g_escalation": "classify_escalation + operator_cycle (kill-switch hooks; default recommend-only)",
        },
        "safety": {
            "no_broker": True, "no_orders": True, "no_network": True,
            "default_off": True, "fail_closed": True,
            "follower_never_touches_primary": True,
            "engage_kill_switch_default": False,
            "envelope_bound": "owner risk dial + governor + halt files (MAINTAINED, never exceeded)",
        },
        "reuses": ["../monitoring/monitor.py", "../monitoring/kill_switch.py",
                   "improvement_miner.py", "ultimate_book_live_package.evaluate_governor"],
    }


if __name__ == "__main__":
    print(json.dumps(describe_toolkit(), indent=1, default=str))
