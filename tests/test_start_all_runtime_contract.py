"""Runtime contracts for the Windows autostart entrypoint.

The tests parse ``start_all.bat`` without executing it. Executing this file
would launch orchestrators; the contract we need here is the command surface:
halt/kill/weekend guard precedence plus profile-aligned run_agent calls.
"""

from __future__ import annotations

import re
from pathlib import Path


START_ALL = Path("start_all.bat")
WATCHDOG = Path("scripts/watchdog.ps1")
WATCHDOG_TASK_CONFIG = Path("scripts/configure_watchdog_task.ps1")
CURRENT_VNEXT_SYMBOLS = {
    "AUDJPY",
    "AUDUSD",
    "BTCUSD",
    "CHFJPY",
    "ETHUSD",
    "EURGBP",
    "EURJPY",
    "EURUSD",
    "GBPJPY",
    "GBPUSD",
    "GER40",
    "JP225",
    "NAS100",
    "NZDUSD",
    "SPX500",
    "UK100",
    "UKOIL_cash",
    "US30_cash",
    "USDCAD",
    "USDCHF",
    "USDJPY",
    "USOIL_cash",
    "XAGUSD",
    "XAUUSD",
}


def _start_all_text() -> str:
    return START_ALL.read_text(encoding="utf-8")


def test_start_all_guard_precedence_keeps_research_halt_and_disabled_above_force():
    text = _start_all_text()

    research_halt = text.index(
        'if exist "pipeline_state\\RESEARCH_RUNTIME_HALT.flag"'
    )
    disabled = text.index(
        'if exist "knowledge_base\\meta\\AUTOSTART_DISABLED.flag"'
    )
    day_of_week = text.index("for /f %%i in ('powershell -NoProfile")
    weekend_force = text.index(
        'if exist "knowledge_base\\meta\\AUTOSTART_FORCE.flag" goto :force'
    )
    run_label = re.search(r"(?m)^:run$", text)
    assert run_label is not None

    assert research_halt < disabled < day_of_week < weekend_force < run_label.start()


def test_start_all_defaults_to_redacted_account_live_but_keeps_runtime_override_knobs():
    text = _start_all_text()

    assert 'if "%GTOS_PROFILE%"=="" set "GTOS_PROFILE=redacted_account"' in text
    assert 'if "%GTOS_MODE%"==""    set "GTOS_MODE=live"' in text
    assert "GTOS_RUNTIME_NAMESPACE=redacted_account_live_bee34003" in text
    assert r"GTOS_MT5_TERMINAL_PATH=C:\Program Files\MetaTrader 5\terminal64.exe" in text
    assert "GTOS_NOTIFICATION_QUEUE_PATH=pipeline_state\\redacted_account_live_bee34003\\notification_queue.jsonl" in text
    assert "GTOS_LOG_ROOT=logs\\%GTOS_RUNTIME_NAMESPACE%" in text

    run_agent_commands = re.findall(r'run_agent\.py --symbol [^\r\n"]+', text)
    assert len(run_agent_commands) == len(CURRENT_VNEXT_SYMBOLS)
    for command in run_agent_commands:
        assert "--mode %GTOS_MODE%" in command
        assert "--profile %GTOS_PROFILE%" in command
        assert "--runtime-namespace %GTOS_RUNTIME_NAMESPACE%" in command
        assert "--terminal-path" in command


def test_start_all_supervises_current_vnext_symbol_fleet():
    text = _start_all_text()

    observed = set(
        re.findall(r"run_agent\.py --symbol ([A-Za-z0-9_]+)", text)
    )

    assert observed == CURRENT_VNEXT_SYMBOLS


def test_watchdog_defaults_to_current_redacted_account_live_contract():
    text = WATCHDOG.read_text(encoding="utf-8")

    assert 'if (-not $env:GTOS_PROFILE) { $env:GTOS_PROFILE = "redacted_account" }' in text
    assert 'if (-not $env:GTOS_MODE)    { $env:GTOS_MODE    = "live" }' in text
    assert '$env:GTOS_RUNTIME_NAMESPACE = "redacted_account_live_bee34003"' in text
    assert '$env:GTOS_MT5_TERMINAL_PATH = "C:\\Program Files\\MetaTrader 5\\terminal64.exe"' in text
    assert '$env:GTOS_NOTIFICATION_QUEUE_PATH = "pipeline_state\\redacted_account_live_bee34003\\notification_queue.jsonl"' in text
    assert "--mode $($env:GTOS_MODE)" in text
    assert "--profile $($env:GTOS_PROFILE)" in text
    assert "--runtime-namespace ${RuntimeNamespace}" in text
    assert "--terminal-path" in text


def test_watchdog_tick_capture_launches_in_daemon_liveness_mode():
    text = WATCHDOG.read_text(encoding="utf-8")

    assert "$tickFreshnessArg = \" --skip-tick-freshness-check\"" in text
    assert "function Get-DaemonHeartbeatAgeSeconds" in text
    assert "no liveness heartbeat" in text
    assert "data progress age" in text
    tick_launch = re.search(
        r"-m src\.components\.tick_capture --symbol \$\{tsym\} "
        r"--mt5-symbol \$\{brokerSym\} --runtime-namespace \$\{RuntimeNamespace\} "
        r'--terminal-path ""\$\{TerminalPath\}""\$\{tickFreshnessArg\}',
        text,
    )
    assert tick_launch is not None


def test_watchdog_uses_native_process_commandline_lookup_for_frequent_supervision():
    text = WATCHDOG.read_text(encoding="utf-8")

    assert 'Get-CimInstance Win32_Process -Filter "ProcessId = $ProcessId"' in text
    assert "psutil.Process" not in text
    assert "& $PythonExe -c $py $ProcessId" not in text


def test_watchdog_has_namespace_single_instance_lock_before_launches():
    text = WATCHDOG.read_text(encoding="utf-8")

    lock_pos = text.index("function Acquire-WatchdogInstanceLock")
    acquire_pos = text.index("if (-not (Acquire-WatchdogInstanceLock))")
    launch_loop_pos = text.index("# --- Trading agent processes ---")

    assert lock_pos < acquire_pos < launch_loop_pos
    assert ".watchdog_${RuntimeNamespace}.lock" in text
    assert "[System.IO.FileShare]::None" in text
    assert "exiting to prevent duplicate launches" in text


def test_watchdog_restarts_tick_capture_on_stale_liveness_or_data_progress():
    text = WATCHDOG.read_text(encoding="utf-8")
    match = re.search(
        r"# --- Tick Capture Daemons.*?# --- M1 Capture Daemon",
        text,
        flags=re.S,
    )
    assert match is not None
    tick_capture_section = match.group(0)

    assert 'Get-DaemonHeartbeatAgeSeconds -Name "tick_capture_${tsym}${NamespaceSuffix}"' in tick_capture_section
    assert 'Get-DaemonProgressAgeSeconds -Name "tick_capture_${tsym}${NamespaceSuffix}"' in tick_capture_section
    assert "$heartbeatAge -gt $staleSeconds" in tick_capture_section
    assert "$progressAge -gt $staleSeconds" in tick_capture_section
    assert "alive but data progress age" in tick_capture_section
    assert "Stop-Process -Id $tcPid -Force" in tick_capture_section


def test_watchdog_restarts_m1_capture_on_stale_liveness_or_data_progress():
    text = WATCHDOG.read_text(encoding="utf-8")
    match = re.search(
        r"# --- M1 Capture Daemon.*?# --- Heartbeat Monitor",
        text,
        flags=re.S,
    )
    assert match is not None
    m1_section = match.group(0)

    assert 'Get-DaemonHeartbeatAgeSeconds -Name "m1_capture_all${NamespaceSuffix}"' in m1_section
    assert 'Get-DaemonProgressAgeSeconds -Name "m1_capture_all${NamespaceSuffix}"' in m1_section
    assert "$m1HeartbeatAge -gt $m1StaleSeconds" in m1_section
    assert "$m1ProgressAge -gt $m1StaleSeconds" in m1_section
    assert "alive but data progress age" in m1_section
    assert "Stop-Process -Id $m1Pid -Force" in m1_section


def test_watchdog_task_helper_sets_frequent_bounded_scheduler_contract():
    text = WATCHDOG_TASK_CONFIG.read_text(encoding="utf-8")

    assert '[int]$IntervalMinutes = 1' in text
    assert "[int]$ExecutionLimitMinutes = 10" in text
    assert "[int]$RestartCount = 3" in text
    assert "watchdog_launcher.vbs" in text
    assert "-RepetitionInterval (New-TimeSpan -Minutes $IntervalMinutes)" in text
    assert "-ExecutionTimeLimit (New-TimeSpan -Minutes $ExecutionLimitMinutes)" in text
    assert "-MultipleInstances IgnoreNew" in text
    assert "-RestartCount $RestartCount" in text
    assert "Does not touch broker orders, positions, deals, or MT5" in text


def test_watchdog_live_maintenance_launches_without_cmd_wrapper():
    text = WATCHDOG.read_text(encoding="utf-8")
    match = re.search(
        r"function Invoke-LiveMonitoringMaintenance \{(?P<body>.*?)\n\}\n\n"
        r"\$OutsideTradingHoursWithActiveTrade",
        text,
        flags=re.S,
    )
    assert match is not None
    body = match.group("body")

    assert '$maintPsi.FileName       = $PythonExe' in body
    assert 'WorkingDirectory = $ProjectDir' in body
    assert 'RedirectStandardOutput = $true' in body
    assert 'RedirectStandardError = $true' in body
    assert '$maintPsi.FileName       = "cmd.exe"' not in body


def test_notification_queue_worker_is_account_scoped_in_start_all_and_watchdog():
    start_text = _start_all_text()
    watchdog_text = WATCHDOG.read_text(encoding="utf-8")

    assert "--worker --queue-path" in start_text
    assert "--runtime-namespace %GTOS_RUNTIME_NAMESPACE%" in start_text
    assert "%GTOS_NOTIFICATION_QUEUE_PATH%" in start_text
    assert ".notification_queue_worker_%GTOS_RUNTIME_NAMESPACE%.lock" in start_text

    assert "$NotificationQueueLockName" in watchdog_text
    assert "--queue-path" in watchdog_text
    assert "${NotificationQueuePath}" in watchdog_text
    assert "--runtime-namespace ${RuntimeNamespace}" in watchdog_text
    assert ".notification_queue_worker_${RuntimeNamespace}.lock" in watchdog_text


def test_secondary_execution_follower_role_skips_duplicate_full_fleet():
    start_text = _start_all_text()
    watchdog_text = WATCHDOG.read_text(encoding="utf-8")

    assert "GTOS_RUNTIME_ROLE=primary_full" in start_text
    assert ":secondary_follower" in start_text
    assert "secondary_execution_follower" in start_text
    assert "scripts\\dual_broker_execution_follower.py" in start_text
    assert "skipping run_agent fleet, tick_capture, m1_capture, and notification worker" in start_text

    assert 'GTOS_RUNTIME_ROLE = "primary_full"' in watchdog_text
    assert "Invoke-SecondaryExecutionFollowerRole" in watchdog_text
    assert "dual_broker_execution_follower.py" in watchdog_text
    assert "Skipping run_agent fleet, tick_capture fleet, m1_capture" in watchdog_text
    assert "--source-runtime-namespace ${sourceNamespace}" in watchdog_text


def test_primary_watchdog_supervises_only_lightweight_dual_broker_bridge():
    watchdog_text = WATCHDOG.read_text(encoding="utf-8")

    assert "Invoke-DualBrokerTradeRecordProjectorBridge" in watchdog_text
    assert "Invoke-DualBrokerExecutionFollowerBridge" in watchdog_text
    assert ".dual_broker_trade_record_projector_${sourceNamespace}.lock" in watchdog_text
    assert ".dual_broker_execution_follower_${targetNamespace}.lock" in watchdog_text
    assert "scripts\\dual_broker_trade_record_projector.py" in watchdog_text
    assert "scripts\\dual_broker_execution_follower.py" in watchdog_text
    assert "$orderEnabled = $true" in watchdog_text
    assert "--order-enabled" in watchdog_text
    assert "--replay-existing" in watchdog_text
    assert "--reprocess-failed-intents" in watchdog_text
    assert "--live-recovery-window-seconds 1800" in watchdog_text
    assert "operator_profile" in watchdog_text
    assert "run_agent.py --symbol ${symbol}" in watchdog_text


def test_watchdog_memory_gate_blocks_live_maintenance_overlap():
    watchdog_text = WATCHDOG.read_text(encoding="utf-8")

    assert "function Get-FreePhysicalMemoryPct" in watchdog_text
    assert "$minFreeMemoryPct = 25.0" in watchdog_text
    assert "preserving live trading footprint" in watchdog_text
    assert "GTOS_SUPPRESS_LIVE_MONITORING_MAINTENANCE_WITH_DUAL_BROKER" in watchdog_text
    assert "explicit dual-broker maintenance suppression active" in watchdog_text
    assert "suppressing widening maintenance" in watchdog_text
    assert "*run_live_monitoring_maintenance.py*" in watchdog_text
    assert "*follow_live_candidate_paths.py*" in watchdog_text
    assert "maintenance/follow process already running" in watchdog_text
