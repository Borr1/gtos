"""Contracts for the watchdog correlation-shock monitor hook.

These tests parse ``scripts/watchdog.ps1`` without executing it. Running the
watchdog can launch processes; the runtime contract here is the scheduled hook
surface and marker semantics.
"""

from __future__ import annotations

import re
from pathlib import Path


WATCHDOG = Path("scripts/watchdog.ps1")


def _correlation_shock_section() -> str:
    text = WATCHDOG.read_text(encoding="utf-8")
    match = re.search(
        r"# --- Correlation Shock Monitor.*?# --- Monthly Decay Shadow Monitor",
        text,
        flags=re.S,
    )
    assert match is not None, "correlation-shock watchdog section not found"
    return match.group(0)


def test_watchdog_runs_correlation_shock_monitor_once_per_utc_day():
    section = _correlation_shock_section()

    assert "correlation_shock_last_run.utcdate" in section
    assert "correlation_shock_monitor.py" in section
    assert "correlation_shock.log" in section
    assert 'ToUniversalTime().ToString("yyyy-MM-dd")' in section
    assert "$csLastRun -eq $csTodayUtc" in section
    assert "WaitForExit(60000)" in section


def test_watchdog_marks_success_and_alarm_but_retries_failures():
    section = _correlation_shock_section()

    ok_branch = re.search(
        r"if \(\$csExit -eq 0\).*?\$csTodayUtc \| Set-Content",
        section,
        flags=re.S,
    )
    alarm_branch = re.search(
        r"elseif \(\$csExit -eq 1\).*?\$csTodayUtc \| Set-Content",
        section,
        flags=re.S,
    )
    failed_branch = re.search(
        r"elseif \(\$csExit -eq 2\)(?P<body>.*?)else \{",
        section,
        flags=re.S,
    )

    assert ok_branch is not None
    assert alarm_branch is not None
    assert failed_branch is not None
    assert "Set-Content" not in failed_branch.group("body")


def test_watchdog_runs_correlation_shock_hidden_and_alert_only():
    section = _correlation_shock_section()

    assert "WindowStyle]::Hidden" in section
    assert "$csPsi.CreateNoWindow = $true" in section
    assert "Telegram-only alert; never touches positions." in section
