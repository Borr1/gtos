#!/usr/bin/env python3
"""Watchdog end-to-end verification — read-only health audit.

Purpose
-------
Three watchdog integrations remain active in ``scripts/watchdog.ps1``: the
prop-firm profile (commits ``23c083f`` / ``78680ec``), the OB continuation
monitor (``1827871``), and the API refusal monitor (``b0c2ece``). Each was
reviewed in isolation, but they have never been observed running together
through a full clean UTC-day cycle.

This script is a one-command, read-only audit that verifies each integration
is wired AND producing its expected artifact with fresh, well-formed content.
It is designed to run from the CEO's workstation after a 1-day observation
window and at any point afterward for drift detection. Offline-capable (no
MT5, no Anthropic API, no network).

Read-only contract
------------------
* Never writes to ``shadow_logs/``, ``knowledge_base/``, ``pipeline_state/``,
  or ``logs/``.
* Never runs any of the underlying monitors. Inspects artifacts only.
* Never contacts MT5, Anthropic, or Telegram.

Failure-mode distinction
------------------------
Per the three canonical failure modes the CEO asked for:

* ``ABSENT``   — the artifact path does not exist (or symlink points nowhere)
* ``STALE``    — the artifact exists but its mtime is older than the per-
                 integration freshness threshold (weekend/holiday-aware)
* ``MALFORMED``— the artifact exists but is empty, unparseable, or missing
                 required top-level fields

All three resolve to per-check ``FAIL``. ``PASS`` requires freshness AND well-
formedness. ``WARN`` is reserved for benign gaps such as an api_refusal
heartbeat stale inside the watchdog daily dead zone at local 01:15-07:45 UTC+8
per ``scripts/watchdog.ps1:7-12``.

Exit codes
----------
    0 — every integration PASS (WARN allowed)
    1 — one or more integration FAIL
    2 — script error (unhandled exception, argparse error, etc.)

CLI
---
    python scripts/watchdog_e2e_verify.py
    python scripts/watchdog_e2e_verify.py --json
    python scripts/watchdog_e2e_verify.py --verbose
    python scripts/watchdog_e2e_verify.py --ob-stale-hours 30

Test-isolation discipline
-------------------------
All paths + thresholds live on module-level constants so tests can redirect
them via ``monkeypatch.setattr(_mod, "WATCHDOG_PS1", tmp_path / "wd.ps1")``.
Writing under the real ``shadow_logs/`` from a pytest process would trigger
the ``ProductionWriteError`` guard in ``tests/conftest.py``.
"""
from __future__ import annotations

import argparse
import csv
import json
import logging
import os
import re
import sys
from dataclasses import dataclass, field, asdict
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Callable, Optional


# ---------------------------------------------------------------------------
# Project-root importability + logging
# ---------------------------------------------------------------------------


_PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT))


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)-8s %(message)s",
)
logger = logging.getLogger(__name__)

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")


# ---------------------------------------------------------------------------
# Module-level constants — tests monkeypatch these on the module object.
# ---------------------------------------------------------------------------


# Artifact paths — one per integration.
OB_CSV: Path = _PROJECT_ROOT / "shadow_logs" / "ob_continuation_daily.csv"
OB_MARKER: Path = _PROJECT_ROOT / "knowledge_base" / "meta" / "ob_continuation_last_run.utcdate"
API_REFUSAL_STATE: Path = _PROJECT_ROOT / "shadow_logs" / "api_refusal_alert_state.json"
API_REFUSAL_LOG: Path = _PROJECT_ROOT / "logs" / "api_refusal_monitor.log"
WATCHDOG_LOG: Path = _PROJECT_ROOT / "logs" / "watchdog.log"
MALFORMED_LOG: Path = _PROJECT_ROOT / "shadow_logs" / "malformed_responses.jsonl"
WATCHDOG_PS1: Path = _PROJECT_ROOT / "scripts" / "watchdog.ps1"
redacted_account_YAML: Path = _PROJECT_ROOT / "config" / "profiles" / "redacted_account.yaml"

# Freshness thresholds (hours). Defaults picked so a clean weekend overnight
# never alarms while any real stall ≤1 heartbeat is caught.
DEFAULT_OB_STALE_HOURS: float = 30.0       # once/UTC-day, allow sched slip
DEFAULT_API_REFUSAL_STALE_HOURS: float = 1.0  # watchdog fires api_refusal every ~15m
# Note: the api_refusal heartbeat sits idle during the watchdog daily dead zone
# (local 01:15-07:45 UTC+8 = UTC 17:15-23:45 of the prior UTC day per
# ``scripts/watchdog.ps1:7-12``). Inside that window, STALE is downgraded to
# WARN via ``_is_watchdog_dead_zone`` — mirrors the weekend-leniency pattern.
DEFAULT_WATCHDOG_HEARTBEAT_STALE_HOURS: float = 1.0  # watchdog.log writes every ~15m

# Weekend leniency — if weekend_close is ``>= 48h`` ago, STALE degrades to
# WARN. Rationale: Friday 17:15 UTC close → Monday 07:00 UTC reopen is close
# to ~60h of no market activity for a market-dependent artifact.
WEEKEND_LENIENCY_HOURS: float = 48.0

# Watchdog daily dead zone (per ``scripts/watchdog.ps1:26-31``):
#   Local UTC+8 01:15-07:45 → UTC 17:15-23:45 (of the prior UTC day).
# Artifacts that are only touched during the watchdog's active window
# (e.g., ``logs/api_refusal_monitor.log``) are naturally stale during this
# block. ``_is_watchdog_dead_zone`` returns True inside the window so
# ``_classify_freshness`` can downgrade STALE → WARN.
_WATCHDOG_LOCAL_OFFSET_HOURS: int = 8      # UTC+8 operator machine
_WATCHDOG_DEAD_START_LOCAL_MINS: int = 75   # 01:15 local
_WATCHDOG_DEAD_END_LOCAL_MINS: int = 465    # 07:45 local

# Required top-level fields for well-formedness checks.
_OB_CSV_REQUIRED_FIELDS: tuple[str, ...] = (
    "date_utc", "scope", "window_size", "continuation_count", "total_count",
    "rate_pct", "alarm_fired", "insufficient_sample",
)
_redacted_account_REQUIRED_FIELDS: tuple[str, ...] = (
    "profile_name", "risk", "drawdown_reduction",
)

# Watchdog.ps1 substrings that must be present for each integration's wiring
# to be considered "in place". Substring match because the .ps1 is not Python-
# parseable and the exact quoting/spacing varies.
_WATCHDOG_HOOK_SUBSTRINGS: dict[str, tuple[str, ...]] = {
    "ob_continuation": ("ob_continuation_monitor",),
    "api_refusal": ("api_refusal_monitor",),
    # The watchdog now launches with env-var parameterization but defaults the
    # env vars to the current redacted_account live production contract. All pieces
    # are required; a persisted GTOS_MODE=demo override can otherwise make
    # the scheduler supervise the wrong process fleet.
    "redacted_account": (
        'GTOS_PROFILE = "redacted_account"',
        'GTOS_MODE    = "live"',
        'GTOS_RUNTIME_NAMESPACE = "redacted_account_live_bee34003"',
        'GTOS_MT5_TERMINAL_PATH = "C:\\Program Files\\MetaTrader 5\\terminal64.exe"',
        'GTOS_NOTIFICATION_QUEUE_PATH = "pipeline_state\\redacted_account_live_bee34003\\notification_queue.jsonl"',
        "--profile $($env:GTOS_PROFILE)",
        "--mode $($env:GTOS_MODE)",
        "--runtime-namespace ${RuntimeNamespace}",
        "--terminal-path",
        "--queue-path",
        "${NotificationQueuePath}",
        ".notification_queue_worker_${RuntimeNamespace}.lock",
    ),
}
_WATCHDOG_HOOK_ALTERNATIVES: dict[str, tuple[tuple[str, ...], ...]] = {
    "redacted_account": (
        (
            "--profile redacted_account",
            "--mode live",
            "--runtime-namespace redacted_account_live_bee34003",
            "--terminal-path",
            "--queue-path",
            "pipeline_state\\redacted_account_live_bee34003\\notification_queue.jsonl",
        ),
        _WATCHDOG_HOOK_SUBSTRINGS["redacted_account"],
    ),
}


# ---------------------------------------------------------------------------
# Result types
# ---------------------------------------------------------------------------


Status = str  # "PASS" | "FAIL" | "WARN" (kept as str for easy JSON)


@dataclass
class CheckResult:
    """Single sub-check inside an integration's audit.

    ``result`` is a Status string (``PASS`` / ``FAIL`` / ``WARN``); ``detail``
    is a short operator-readable sentence explaining what was observed.
    """
    name: str
    result: Status
    detail: str


@dataclass
class IntegrationReport:
    integration: str
    status: Status
    checks: list[CheckResult] = field(default_factory=list)
    age_hours: Optional[float] = None
    artifact_path: Optional[str] = None


# ---------------------------------------------------------------------------
# Helpers — time, file inspection
# ---------------------------------------------------------------------------


def _now_utc() -> datetime:
    """Wall-clock UTC. Split out so tests can monkeypatch a fixed ``now``."""
    return datetime.now(timezone.utc)


def _mtime_utc(path: Path) -> Optional[datetime]:
    """Return a UTC-aware datetime for ``path`` mtime, or None if unreadable.

    Uses ``os.path.getmtime`` with explicit ``tz=timezone.utc`` per the MT5
    preflight rule #5 (never use naive fromtimestamp).
    """
    try:
        ts = os.path.getmtime(path)
    except (FileNotFoundError, OSError):
        return None
    return datetime.fromtimestamp(ts, tz=timezone.utc)


def _age_hours(path: Path, now: Optional[datetime] = None) -> Optional[float]:
    """Return artifact age in hours, or None if mtime unavailable."""
    m = _mtime_utc(path)
    if m is None:
        return None
    now = now or _now_utc()
    return (now - m).total_seconds() / 3600.0


def _resolved_exists(path: Path) -> bool:
    """True iff ``path`` resolves to an existing file. Broken symlinks → False.

    Uses ``exists()`` which follows symlinks — a dangling symlink (pointing at
    a deleted target) returns False. That's the semantics we want: ABSENT.
    """
    try:
        return path.exists() and path.is_file()
    except OSError:
        return False


def _file_size(path: Path) -> Optional[int]:
    """Return file size in bytes, or None if unreadable."""
    try:
        return os.path.getsize(path)
    except (FileNotFoundError, OSError):
        return None


def _is_market_closed(now: Optional[datetime] = None) -> bool:
    """Return True iff this tool's weekend-closure window is active.

    Aligned with the watchdog's operational window (``scripts/watchdog.ps1:7-12``):
    the workstation is UTC+8 and Saturday after local 01:15 (= Friday 17:15
    UTC) is the first moment the watchdog considers "outside trading hours"
    for the weekend. Reopen stays at Sunday 21:00 UTC (close to real FX spot
    reopen) so we don't mask real Monday-open stalls with leniency.

    ``weekday()``: Mon=0 … Sun=6, so Fri=4, Sat=5, Sun=6.
    """
    now = now or _now_utc()
    wd = now.weekday()
    if wd == 5:  # Saturday — always closed
        return True
    if wd == 4 and (now.hour > 17 or (now.hour == 17 and now.minute >= 15)):
        return True  # Friday from 17:15 UTC onward
    if wd == 6 and now.hour < 21:  # Sunday before 21:00 UTC
        return True
    return False


def _last_market_close_utc(now: Optional[datetime] = None) -> datetime:
    """Approximate the last Friday-17:15-UTC close relative to ``now``.

    Paired with ``_is_market_closed`` — both share the Friday 17:15 UTC
    boundary so weekend-leniency age math uses the same anchor the tool
    uses to decide "is the market closed right now".
    """
    now = now or _now_utc()
    days_back = (now.weekday() - 4) % 7
    candidate = (now - timedelta(days=days_back)).replace(
        hour=17, minute=15, second=0, microsecond=0,
    )
    if candidate > now:
        candidate = candidate - timedelta(days=7)
    return candidate


def _is_weekend_leniency_active(
    now: Optional[datetime] = None,
    leniency_hours: Optional[float] = None,
) -> bool:
    """Return True iff the market is currently closed AND the closure has
    lasted at least ``leniency_hours`` hours. The leniency-hours threshold
    is deliberately liberal (default 48h) so short Friday-evening gaps
    (5-10h past close) don't suppress alarms — only full weekend closures
    where a market-dependent artifact physically could not be updated.

    ``leniency_hours=None`` (the default) reads the module constant at call
    time so tests can ``monkeypatch.setattr(_mod, "WEEKEND_LENIENCY_HOURS", X)``.
    """
    now = now or _now_utc()
    if leniency_hours is None:
        leniency_hours = WEEKEND_LENIENCY_HOURS
    if not _is_market_closed(now):
        return False
    close = _last_market_close_utc(now)
    if close > now:
        return False
    age = (now - close).total_seconds() / 3600.0
    return age >= leniency_hours


def _is_watchdog_dead_zone(now: Optional[datetime] = None) -> bool:
    """Return True iff ``now`` falls inside the watchdog's daily dead zone.

    Per ``scripts/watchdog.ps1:26-31`` the operator workstation is UTC+8 and
    the watchdog kills all processes between local 01:15 and 07:45. In UTC
    that maps to the 17:15 → 23:45 window of the prior UTC day. Artifacts
    whose mtime depends on a live watchdog run (e.g. the api_refusal
    heartbeat log) will naturally stall for ~6.5h every trading weekday.

    Used by ``_classify_freshness`` to downgrade STALE → WARN for the
    api_refusal heartbeat, mirroring the weekend-leniency pattern.
    """
    now = now or _now_utc()
    # Convert UTC to operator-local (UTC+8) and test minutes-since-midnight
    # against the dead-zone window. ``%`` handles the day-boundary wrap so
    # UTC 17:15 (Sunday) → local 01:15 (Monday) lands in the dead zone.
    local = now + timedelta(hours=_WATCHDOG_LOCAL_OFFSET_HOURS)
    local_minutes = local.hour * 60 + local.minute
    return _WATCHDOG_DEAD_START_LOCAL_MINS <= local_minutes < _WATCHDOG_DEAD_END_LOCAL_MINS


# ---------------------------------------------------------------------------
# Generic classifiers
# ---------------------------------------------------------------------------


def _classify_freshness(
    path: Path,
    threshold_hours: float,
    now: Optional[datetime] = None,
    weekend_lenient: bool = False,
    dead_zone_lenient: bool = False,
) -> CheckResult:
    """Classify an artifact's freshness as PASS / WARN / FAIL.

    * If the file is missing ⇒ ABSENT ⇒ FAIL
    * If age ≤ threshold ⇒ PASS
    * If age > threshold AND weekend_lenient AND weekend is active ⇒ WARN
    * If age > threshold AND dead_zone_lenient AND watchdog dead zone
      active ⇒ WARN (for artifacts the watchdog only touches during its
      active window — see ``_is_watchdog_dead_zone``)
    * If age > threshold otherwise ⇒ STALE ⇒ FAIL
    """
    if not _resolved_exists(path):
        return CheckResult(
            name="freshness",
            result="FAIL",
            detail=f"ABSENT: {path} does not exist (expected fresh artifact)",
        )
    age = _age_hours(path, now=now)
    if age is None:
        return CheckResult(
            name="freshness",
            result="FAIL",
            detail=f"ABSENT: mtime unreadable at {path}",
        )
    if age <= threshold_hours:
        return CheckResult(
            name="freshness",
            result="PASS",
            detail=f"Age {age:.1f}h ≤ threshold {threshold_hours:.1f}h",
        )
    # Stale.
    if weekend_lenient and _is_weekend_leniency_active(now=now):
        return CheckResult(
            name="freshness",
            result="WARN",
            detail=(
                f"STALE: age {age:.1f}h > threshold {threshold_hours:.1f}h, "
                f"but weekend leniency active (market closed >48h) — WARN"
            ),
        )
    if dead_zone_lenient and _is_watchdog_dead_zone(now=now):
        return CheckResult(
            name="freshness",
            result="WARN",
            detail=(
                f"STALE: age {age:.1f}h > threshold {threshold_hours:.1f}h, "
                f"but watchdog dead zone active (local 01:15-07:45 UTC+8) — WARN"
            ),
        )
    return CheckResult(
        name="freshness",
        result="FAIL",
        detail=f"STALE: age {age:.1f}h > threshold {threshold_hours:.1f}h",
    )


def _check_watchdog_wiring(hook_key: str) -> CheckResult:
    """Return a CheckResult asserting a watchdog hook appears in ``WATCHDOG_PS1``.

    Each accepted hook definition is a tuple of substrings that must all be
    present. Some hooks also define alternatives for backward compatibility.
    Distinguishes ABSENT vs MISSING-HOOK.
    """
    required_sets = _WATCHDOG_HOOK_ALTERNATIVES.get(
        hook_key, (_WATCHDOG_HOOK_SUBSTRINGS[hook_key],),
    )
    ps1 = Path(WATCHDOG_PS1)
    if not _resolved_exists(ps1):
        return CheckResult(
            name="watchdog_wiring",
            result="FAIL",
            detail=f"ABSENT: watchdog.ps1 not found at {ps1}",
        )
    try:
        # Encoding is forgiving — PowerShell scripts on Windows are commonly
        # UTF-8 with or without BOM. ``errors='replace'`` keeps us from
        # crashing on a stray byte.
        text = ps1.read_text(encoding="utf-8", errors="replace")
    except OSError as exc:
        return CheckResult(
            name="watchdog_wiring",
            result="FAIL",
            detail=f"Cannot read {ps1}: {exc}",
        )
    for required in required_sets:
        missing = [needle for needle in required if needle not in text]
        if not missing:
            return CheckResult(
                name="watchdog_wiring",
                result="PASS",
                detail=f"watchdog.ps1 contains required substrings {required!r}",
            )
    all_expected = sorted({needle for required in required_sets for needle in required})
    return CheckResult(
        name="watchdog_wiring",
        result="FAIL",
        detail=f"watchdog.ps1 missing accepted hook pattern(s) {all_expected!r} (wiring drift)",
    )


def _latest_watchdog_tag_line(tag: str) -> Optional[str]:
    """Return the latest watchdog.log line containing ``tag``, newest first."""
    wd_log = Path(WATCHDOG_LOG)
    if not _resolved_exists(wd_log):
        return None
    try:
        lines = wd_log.read_text(encoding="utf-8", errors="replace").splitlines()
    except OSError:
        return None
    for line in reversed(lines[-1000:]):
        if tag in line:
            return line
    return None


# ---------------------------------------------------------------------------
# Per-integration checks
# ---------------------------------------------------------------------------


def check_ob_continuation(
    stale_hours: float = DEFAULT_OB_STALE_HOURS,
    now: Optional[datetime] = None,
) -> IntegrationReport:
    """Audit the OB continuation monitor integration (#1 primary decay metric).

    Artifact: ``shadow_logs/ob_continuation_daily.csv``
    Wiring: ``scripts/watchdog.ps1`` once-per-UTC-day marker
    """
    now = now or _now_utc()
    csv_path = Path(OB_CSV)
    checks: list[CheckResult] = []

    # (1) Watchdog wiring
    checks.append(_check_watchdog_wiring("ob_continuation"))

    # (2) Freshness — weekend-lenient because the monitor runs off historical
    #     data which only updates on market days.
    checks.append(_classify_freshness(
        csv_path, stale_hours, now=now, weekend_lenient=True,
    ))

    # (3) Well-formed: parseable CSV with required columns including the
    #     insufficient_sample column added in handoff 24.
    if _resolved_exists(csv_path):
        size = _file_size(csv_path)
        if size == 0:
            checks.append(CheckResult(
                name="well_formed",
                result="FAIL",
                detail="MALFORMED: CSV file is 0 bytes",
            ))
        else:
            try:
                with open(csv_path, "r", encoding="utf-8", newline="") as fh:
                    reader = csv.DictReader(fh)
                    fieldnames = reader.fieldnames or []
                    missing = [f for f in _OB_CSV_REQUIRED_FIELDS if f not in fieldnames]
                    if missing:
                        checks.append(CheckResult(
                            name="well_formed",
                            result="FAIL",
                            detail=(
                                f"MALFORMED: CSV missing required columns: {missing} "
                                f"(found: {fieldnames})"
                            ),
                        ))
                    else:
                        # Count rows — 0 data rows is suspicious but not malformed.
                        row_count = sum(1 for _ in reader)
                        checks.append(CheckResult(
                            name="well_formed",
                            result="PASS",
                            detail=(
                                f"CSV parseable with {row_count} data rows, "
                                f"all required columns present"
                            ),
                        ))
            except (OSError, csv.Error) as exc:
                checks.append(CheckResult(
                    name="well_formed",
                    result="FAIL",
                    detail=f"MALFORMED: CSV unparseable: {exc}",
                ))
    else:
        # Freshness check already reported ABSENT; don't duplicate as FAIL.
        checks.append(CheckResult(
            name="well_formed",
            result="FAIL",
            detail="SKIPPED (artifact absent; see freshness check)",
        ))

    return IntegrationReport(
        integration="ob_continuation_monitor",
        status=_rollup(checks),
        checks=checks,
        age_hours=_age_hours(csv_path, now=now),
        artifact_path=str(csv_path),
    )


def check_api_refusal(
    stale_hours: float = DEFAULT_API_REFUSAL_STALE_HOURS,
    now: Optional[datetime] = None,
) -> IntegrationReport:
    """Audit the API refusal monitor integration.

    Per ``scripts/api_refusal_monitor.py`` + the watchdog block, the monitor:
        * is invoked every ~15 min by watchdog.ps1 (fire-and-exit-code)
        * reads ``shadow_logs/malformed_responses.jsonl`` (input corpus)
        * writes ``shadow_logs/api_refusal_alert_state.json`` ONLY on alert
        * watchdog redirects its stdout to ``logs/api_refusal_monitor.log``
          every run (even on exit 0 → log is touched)

    Freshness signal: ``logs/api_refusal_monitor.log`` mtime. This is the
    heartbeat — it's touched on every watchdog run whether or not there's
    a refusal to report. The alert state JSON file is OPTIONAL — present
    only when a real alert was fired.
    """
    now = now or _now_utc()
    checks: list[CheckResult] = []

    # (1) Watchdog wiring
    checks.append(_check_watchdog_wiring("api_refusal"))

    # (2) Freshness: we use the log file as heartbeat proxy. The watchdog
    #     appends to it every ~15 min while trading hours are active; in the
    #     daily dead zone (local 01:15-07:45 UTC+8 per watchdog.ps1:7-12) the
    #     watchdog's ``Test-TradingHours`` returns early and nothing touches
    #     the log — so use dead_zone_lenient to downgrade STALE → WARN there,
    #     and weekend_lenient for the full weekend closure.
    log_path = Path(WATCHDOG_LOG)
    checks.append(_classify_freshness(
        log_path, stale_hours, now=now,
        weekend_lenient=True, dead_zone_lenient=True,
    ))

    latest_api_line = _latest_watchdog_tag_line("[API_REFUSAL]")
    if latest_api_line is None:
        checks.append(CheckResult(
            name="watchdog_status_line",
            result="FAIL",
            detail="MALFORMED: watchdog.log has no [API_REFUSAL] status line",
        ))
    elif re.search(r"\[API_REFUSAL\]\s+OK\b", latest_api_line):
        checks.append(CheckResult(
            name="watchdog_status_line",
            result="PASS",
            detail=f"Latest API refusal watchdog status OK: {latest_api_line}",
        ))
    else:
        checks.append(CheckResult(
            name="watchdog_status_line",
            result="FAIL",
            detail=f"Latest API refusal watchdog status is not OK: {latest_api_line}",
        ))

    # (3) Input corpus present (malformed_responses.jsonl). Empty is OK —
    #     zero refusals is the happy path. Missing file is also OK because
    #     the monitor handles it gracefully (returns empty list). So this is
    #     INFORMATIONAL only — never a FAIL.
    malf_path = Path(MALFORMED_LOG)
    if not _resolved_exists(malf_path):
        checks.append(CheckResult(
            name="input_corpus",
            result="PASS",
            detail=f"INFO: {malf_path} absent — monitor handles this gracefully",
        ))
    else:
        size = _file_size(malf_path) or 0
        checks.append(CheckResult(
            name="input_corpus",
            result="PASS",
            detail=f"{malf_path.name} present, {size} bytes",
        ))

    # (4) Optional state file — if present, validate top-level shape.
    state_path = Path(API_REFUSAL_STATE)
    if _resolved_exists(state_path):
        size = _file_size(state_path) or 0
        if size == 0:
            checks.append(CheckResult(
                name="alert_state_shape",
                result="WARN",
                detail="Alert state JSON is 0 bytes — monitor may have crashed mid-write",
            ))
        else:
            try:
                data = json.loads(state_path.read_text(encoding="utf-8"))
                if not isinstance(data, dict):
                    checks.append(CheckResult(
                        name="alert_state_shape",
                        result="FAIL",
                        detail=f"MALFORMED: alert state root is {type(data).__name__}, expected dict",
                    ))
                else:
                    checks.append(CheckResult(
                        name="alert_state_shape",
                        result="PASS",
                        detail=f"Alert state valid JSON dict with keys {sorted(data.keys())}",
                    ))
            except (OSError, json.JSONDecodeError, UnicodeDecodeError) as exc:
                checks.append(CheckResult(
                    name="alert_state_shape",
                    result="FAIL",
                    detail=f"MALFORMED: alert state unparseable: {exc}",
                ))
    else:
        checks.append(CheckResult(
            name="alert_state_shape",
            result="PASS",
            detail="INFO: alert state file absent — normal (only written on alert)",
        ))

    return IntegrationReport(
        integration="api_refusal_monitor",
        status=_rollup(checks),
        checks=checks,
        age_hours=_age_hours(log_path, now=now),
        artifact_path=str(log_path),
    )


def check_redacted_account_profile(
    now: Optional[datetime] = None,
) -> IntegrationReport:
    """Audit the redacted_account profile integration (commits ``23c083f`` / ``78680ec``).

    Structural only — no freshness (profile is a static config file). Three
    sub-checks: (a) YAML exists + parses + has required fields, (b) watchdog
    passes ``--profile redacted_account``, (c) profile loader can resolve it.
    """
    checks: list[CheckResult] = []

    # (1) YAML presence + shape
    yaml_path = Path(redacted_account_YAML)
    if not _resolved_exists(yaml_path):
        checks.append(CheckResult(
            name="yaml_exists",
            result="FAIL",
            detail=f"ABSENT: {yaml_path} does not exist",
        ))
    else:
        try:
            import yaml  # stdlib-equivalent in GTOS (PyYAML)
            data = yaml.safe_load(yaml_path.read_text(encoding="utf-8"))
            if not isinstance(data, dict):
                checks.append(CheckResult(
                    name="yaml_exists",
                    result="FAIL",
                    detail=f"MALFORMED: YAML root is {type(data).__name__}, expected dict",
                ))
            else:
                missing = [f for f in _redacted_account_REQUIRED_FIELDS if f not in data]
                if missing:
                    checks.append(CheckResult(
                        name="yaml_exists",
                        result="FAIL",
                        detail=f"MALFORMED: missing fields {missing}",
                    ))
                else:
                    name = data.get("profile_name", "<unnamed>")
                    risk_pct = data.get("risk", {}).get("risk_per_trade_pct")
                    checks.append(CheckResult(
                        name="yaml_exists",
                        result="PASS",
                        detail=(
                            f"YAML parseable, profile_name={name!r}, "
                            f"risk.risk_per_trade_pct={risk_pct}"
                        ),
                    ))
        except ImportError as exc:
            checks.append(CheckResult(
                name="yaml_exists",
                result="FAIL",
                detail=f"PyYAML not importable: {exc}",
            ))
        except Exception as exc:
            # yaml.YAMLError and any OS/Unicode errors land here.
            checks.append(CheckResult(
                name="yaml_exists",
                result="FAIL",
                detail=f"MALFORMED: YAML load failed: {exc}",
            ))

    # (2) Watchdog.ps1 wiring
    checks.append(_check_watchdog_wiring("redacted_account"))

    # (3) Profile loader can resolve the profile without raising.
    try:
        from src.utils.config import apply_profile_overrides
        # Minimal base config — profile overlay merges on top. We don't load
        # the real agent_config to stay offline and avoid coupling to schema
        # drift; the loader just needs a dict argument.
        base: dict = {"risk": {}, "drawdown_reduction": {}}
        merged = apply_profile_overrides(base, "redacted_account")
        if not isinstance(merged, dict):
            checks.append(CheckResult(
                name="loader_resolves",
                result="FAIL",
                detail=f"apply_profile_overrides returned {type(merged).__name__}, not dict",
            ))
        else:
            merged_risk = merged.get("risk", {}).get("risk_per_trade_pct")
            checks.append(CheckResult(
                name="loader_resolves",
                result="PASS",
                detail=(
                    f"apply_profile_overrides('redacted_account') OK, "
                    f"merged risk_per_trade_pct={merged_risk}"
                ),
            ))
    except ImportError as exc:
        checks.append(CheckResult(
            name="loader_resolves",
            result="FAIL",
            detail=f"src.utils.config.apply_profile_overrides import failed: {exc}",
        ))
    except Exception as exc:
        checks.append(CheckResult(
            name="loader_resolves",
            result="FAIL",
            detail=f"apply_profile_overrides('redacted_account') raised: {type(exc).__name__}: {exc}",
        ))

    return IntegrationReport(
        integration="redacted_account_profile",
        status=_rollup(checks),
        checks=checks,
        age_hours=None,  # static file — not freshness-based
        artifact_path=str(yaml_path),
    )


# ---------------------------------------------------------------------------
# Rollup + summary
# ---------------------------------------------------------------------------


def _rollup(checks: list[CheckResult]) -> Status:
    """Return the worst status across sub-checks.

    Ordering (worst → best): FAIL > WARN > PASS. If no checks, FAIL (defensive
    — silent pass with zero evidence is never what we want).
    """
    if not checks:
        return "FAIL"
    results = {c.result for c in checks}
    if "FAIL" in results:
        return "FAIL"
    if "WARN" in results:
        return "WARN"
    return "PASS"


def _overall(reports: list[IntegrationReport]) -> Status:
    statuses = {r.status for r in reports}
    if "FAIL" in statuses:
        return "FAIL"
    if "WARN" in statuses:
        return "WARN"
    return "PASS"


def run_all_checks(
    ob_stale_hours: float = DEFAULT_OB_STALE_HOURS,
    api_refusal_stale_hours: float = DEFAULT_API_REFUSAL_STALE_HOURS,
    now: Optional[datetime] = None,
) -> list[IntegrationReport]:
    """Execute all active integration audits with the given thresholds. Never
    raises — per-integration errors are captured as FAIL sub-checks.
    """
    now = now or _now_utc()
    reports: list[IntegrationReport] = []
    audits: list[tuple[str, Callable[[], IntegrationReport]]] = [
        ("ob_continuation_monitor",
         lambda: check_ob_continuation(stale_hours=ob_stale_hours, now=now)),
        ("api_refusal_monitor",
         lambda: check_api_refusal(stale_hours=api_refusal_stale_hours, now=now)),
        ("redacted_account_profile",
         lambda: check_redacted_account_profile(now=now)),
    ]
    for name, fn in audits:
        try:
            reports.append(fn())
        except Exception as exc:
            # Defensive: any uncaught exception inside a check becomes a FAIL
            # with a diagnostic. The tool itself never exits 2 just because
            # a sub-check blew up.
            reports.append(IntegrationReport(
                integration=name,
                status="FAIL",
                checks=[CheckResult(
                    name="audit_exception",
                    result="FAIL",
                    detail=f"Uncaught exception in audit: {type(exc).__name__}: {exc}",
                )],
                age_hours=None,
                artifact_path=None,
            ))
    return reports


# ---------------------------------------------------------------------------
# Presentation
# ---------------------------------------------------------------------------


def _format_summary(reports: list[IntegrationReport], verbose: bool = False) -> str:
    """Human-readable report. One-liner per integration + overall rollup.

    ``verbose`` prints every sub-check detail indented under each integration.
    """
    lines: list[str] = []
    lines.append("=" * 72)
    lines.append("GTOS WATCHDOG END-TO-END VERIFY")
    lines.append("=" * 72)
    for rep in reports:
        age_str = (
            f" [age {rep.age_hours:.1f}h]" if rep.age_hours is not None else ""
        )
        # Leading short result label per integration. Surface the worst
        # sub-check detail so the one-liner matches the rollup status —
        # otherwise the header could say FAIL but quote a PASS sub-check
        # (misleading on wiring-first integrations).
        pri = {"FAIL": 0, "WARN": 1, "PASS": 2}
        if rep.checks:
            worst = sorted(rep.checks, key=lambda c: pri.get(c.result, 3))[0]
            summary_detail = worst.detail
        else:
            summary_detail = "(no checks)"
        lines.append(f"[{rep.status:4s}] {rep.integration}{age_str}: {summary_detail}")
        if verbose:
            for chk in rep.checks:
                lines.append(f"        - [{chk.result}] {chk.name}: {chk.detail}")
            if rep.artifact_path:
                lines.append(f"        artifact: {rep.artifact_path}")
    lines.append("-" * 72)
    # Counts for operator triage.
    counts = {"PASS": 0, "WARN": 0, "FAIL": 0}
    for rep in reports:
        counts[rep.status] = counts.get(rep.status, 0) + 1
    overall = _overall(reports)
    lines.append(
        f"WATCHDOG E2E: {overall} "
        f"(PASS={counts['PASS']} WARN={counts['WARN']} FAIL={counts['FAIL']})"
    )
    lines.append("=" * 72)
    return "\n".join(lines)


def _reports_to_dict(reports: list[IntegrationReport]) -> dict:
    """Return a JSON-serializable dict for --json output."""
    return {
        "overall": _overall(reports),
        "generated_at_utc": _now_utc().isoformat(),
        "counts": {
            "PASS": sum(1 for r in reports if r.status == "PASS"),
            "WARN": sum(1 for r in reports if r.status == "WARN"),
            "FAIL": sum(1 for r in reports if r.status == "FAIL"),
        },
        "integrations": [
            {
                "integration": r.integration,
                "status": r.status,
                "age_hours": r.age_hours,
                "artifact_path": r.artifact_path,
                "checks": [asdict(c) for c in r.checks],
            }
            for r in reports
        ],
    }


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def _parse_args(argv: Optional[list[str]] = None) -> argparse.Namespace:
    p = argparse.ArgumentParser(
        description="GTOS watchdog end-to-end verification (read-only).",
    )
    p.add_argument(
        "--json", action="store_true",
        help="Emit machine-readable JSON instead of human summary.",
    )
    p.add_argument(
        "--verbose", action="store_true",
        help="Print every sub-check detail under each integration.",
    )
    p.add_argument(
        "--ob-stale-hours", type=float, default=DEFAULT_OB_STALE_HOURS,
        help=f"OB continuation CSV staleness threshold (default: {DEFAULT_OB_STALE_HOURS}h).",
    )
    p.add_argument(
        "--api-refusal-stale-hours", type=float, default=DEFAULT_API_REFUSAL_STALE_HOURS,
        help=(
            f"API refusal heartbeat staleness threshold "
            f"(default: {DEFAULT_API_REFUSAL_STALE_HOURS}h). Inside the watchdog "
            f"daily dead zone (local 01:15-07:45 UTC+8) STALE is downgraded "
            f"to WARN -- the watchdog does not touch the heartbeat during that "
            f"~6.5h block."
        ),
    )
    return p.parse_args(argv)


def main(argv: Optional[list[str]] = None) -> int:
    try:
        args = _parse_args(argv)
    except SystemExit as exc:
        # argparse already printed the error; propagate its exit code.
        return int(exc.code) if isinstance(exc.code, int) else 2

    try:
        reports = run_all_checks(
            ob_stale_hours=args.ob_stale_hours,
            api_refusal_stale_hours=args.api_refusal_stale_hours,
        )
    except Exception as exc:
        # Truly unrecoverable — run_all_checks shouldn't raise, but if it
        # does we exit 2 per the script-error contract.
        logger.exception("Unrecoverable error during audit: %s", exc)
        return 2

    if args.json:
        print(json.dumps(_reports_to_dict(reports), indent=2, sort_keys=True))
    else:
        print(_format_summary(reports, verbose=args.verbose))

    overall = _overall(reports)
    # Exit 0 when overall is PASS or WARN (WARN is "acceptable" per spec —
    # weekend leniency etc.). Exit 1 only on FAIL.
    return 1 if overall == "FAIL" else 0


if __name__ == "__main__":
    sys.exit(main())
