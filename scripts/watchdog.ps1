<#
.SYNOPSIS
    GTOS Watchdog - checks and restarts trading agent processes.
.DESCRIPTION
    For each production instrument, checks if the orchestrator process is alive
    by reading the PID lock file. If dead or missing, restarts the process.
    Also monitors the displacement logger process.

    Trading hours aware (local time, UTC+8):
      Active:  07:45 - 23:59 and 00:00 - 01:15
      Dead:    01:15 - 07:45 (kills all processes)
      Weekend: Saturday after 01:15 through Sunday (kills all processes)

    Idempotent - safe to run repeatedly from Task Scheduler.
#>

$ErrorActionPreference = "Continue"

# Profile + mode env-var parameterization (2026-05-31).
# Defaults match the current redacted_account vNext production contract.
# Override GTOS_PROFILE/GTOS_MODE only for an explicit non-production drill.
if (-not $env:GTOS_PROFILE) { $env:GTOS_PROFILE = "redacted_account" }
if (-not $env:GTOS_MODE)    { $env:GTOS_MODE    = "live" }
if (-not $env:GTOS_RUNTIME_ROLE) { $env:GTOS_RUNTIME_ROLE = "primary_full" }
if (-not $env:GTOS_RUNTIME_NAMESPACE) {
    switch ($env:GTOS_PROFILE.ToLowerInvariant()) {
        "redacted_account" { $env:GTOS_RUNTIME_NAMESPACE = "redacted_account_live_bee34003" }
        "ftmo" { $env:GTOS_RUNTIME_NAMESPACE = "operator_profile" }
        "operator_profile" { $env:GTOS_RUNTIME_NAMESPACE = "operator_profile" }
    }
}
if (-not $env:GTOS_MT5_TERMINAL_PATH) {
    switch ($env:GTOS_PROFILE.ToLowerInvariant()) {
        "redacted_account" { $env:GTOS_MT5_TERMINAL_PATH = "C:\Program Files\MetaTrader 5\terminal64.exe" }
        "ftmo" { $env:GTOS_MT5_TERMINAL_PATH = "C:\MT5\FTMO\terminal64.exe" }
        "operator_profile" { $env:GTOS_MT5_TERMINAL_PATH = "C:\MT5\FTMO\terminal64.exe" }
    }
}
if (-not $env:GTOS_NOTIFICATION_QUEUE_PATH) {
    switch ($env:GTOS_PROFILE.ToLowerInvariant()) {
        "redacted_account" { $env:GTOS_NOTIFICATION_QUEUE_PATH = "pipeline_state\redacted_account_live_bee34003\notification_queue.jsonl" }
        "ftmo" { $env:GTOS_NOTIFICATION_QUEUE_PATH = "pipeline_state\operator_profile\notification_queue.jsonl" }
        "operator_profile" { $env:GTOS_NOTIFICATION_QUEUE_PATH = "pipeline_state\operator_profile\notification_queue.jsonl" }
    }
}
$RuntimeNamespace = $env:GTOS_RUNTIME_NAMESPACE
$NamespacePrefix = if ($RuntimeNamespace) { "${RuntimeNamespace}_" } else { "" }
$NamespaceSuffix = if ($RuntimeNamespace) { "_${RuntimeNamespace}" } else { "" }
$TerminalPath = $env:GTOS_MT5_TERMINAL_PATH
$NotificationQueuePath = $env:GTOS_NOTIFICATION_QUEUE_PATH
$NotificationQueueLockName = if ($RuntimeNamespace) { ".notification_queue_worker_${RuntimeNamespace}.lock" } else { ".notification_queue_worker.lock" }
$RuntimeRole = $env:GTOS_RUNTIME_ROLE

# --- Configuration ---
$ProjectDir  = "C:\Users\MSI\Documents\ai-trading-agent"
$PythonExe   = "C:\PROGRA~1\Python313\python.exe"
$LockDir     = Join-Path $ProjectDir "knowledge_base\meta"
$LogDir      = if ($RuntimeNamespace) { Join-Path $ProjectDir "logs\${RuntimeNamespace}" } else { Join-Path $ProjectDir "logs" }
$WatchdogLog = Join-Path $LogDir "watchdog.log"
$HardProductionHaltFlag = Join-Path $ProjectDir "pipeline_state\GTOS_HARD_PRODUCTION_HALT.flag"
$ResearchHaltFlag = Join-Path $ProjectDir "pipeline_state\RESEARCH_RUNTIME_HALT.flag"
$AutostartDisabledFlag = Join-Path $ProjectDir "knowledge_base\meta\AUTOSTART_DISABLED.flag"
$RuntimeHaltFlags = @($HardProductionHaltFlag, $ResearchHaltFlag, $AutostartDisabledFlag)
$ActiveRuntimeHaltFlags = @($RuntimeHaltFlags | Where-Object { Test-Path $_ })

if ($ActiveRuntimeHaltFlags.Count -gt 0) {
    if (-not (Test-Path $LogDir)) {
        New-Item -ItemType Directory -Path $LogDir -Force | Out-Null
    }
    $ts = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    $activeHaltText = ($ActiveRuntimeHaltFlags -join ", ")
    Add-Content -Path $WatchdogLog -Value "${ts}  Atomic runtime halt/autostart disable present (${activeHaltText}) - watchdog exiting without launches." -Encoding UTF8
    Write-Host "${ts}  Atomic runtime halt/autostart disable present (${activeHaltText}) - watchdog exiting without launches."
    exit 0
}

# Trading hours (local time, UTC+8)
# Earliest KZ: Tokyo 00:00 UTC = 08:00 local
# Latest KZ:   XAUUSD NY 17:00 UTC = 01:00 local (next day)
# Dead zone: 01:15 to 07:44 local
$DeadZoneStart = 75    # 01:15 in minutes
$DeadZoneEnd   = 465   # 07:45 in minutes
$TickCaptureProgressStaleMinutes = 10
$M1CaptureProgressStaleMinutes = 3

# Symbol to log file mapping (matches start_all.bat).
# 2026-05-27 vNext production replacement: Stage03 verified 24 broker-native
# eligible symbols. Do not let the older live fleet cap watchdog
# supervision or tick capture startup.
$SymbolMap = [ordered]@{
    "AUDJPY"    = "audjpy.log"
    "AUDUSD"    = "audusd.log"
    "BTCUSD"    = "btcusd.log"
    "CHFJPY"    = "chfjpy.log"
    "ETHUSD"    = "ethusd.log"
    "EURGBP"    = "eurgbp.log"
    "EURJPY"    = "eurjpy.log"
    "EURUSD"    = "eurusd.log"
    "GBPJPY"    = "gbpjpy.log"
    "GBPUSD"    = "gbpusd.log"
    "GER40"     = "ger40.log"
    "JP225"     = "jp225.log"
    "NAS100"    = "nas100.log"
    "NZDUSD"    = "nzdusd.log"
    "SPX500"    = "spx500.log"
    "UK100"     = "uk100.log"
    "UKOIL_cash" = "ukoil.log"
    "US30_cash" = "us30.log"
    "USDCAD"    = "usdcad.log"
    "USDCHF"    = "usdchf.log"
    "USDJPY"    = "usdjpy.log"
    "USOIL_cash" = "usoil.log"
    "XAGUSD"    = "xagusd.log"
    "XAUUSD"    = "xauusd.log"
}

# Tick-capture daemon symbol → broker MT5 alias mapping.
# Defined here (rather than later, near the daemon-launch loop) so
# Stop-AllTradingProcesses can iterate $TickSymbolMap.Keys during the
# OUTSIDE TRADING HOURS path (called BEFORE the launch loop, which sits
# later in main flow). Ensures every Stage08 vNext tick daemon is reaped on
# weekend / dead-zone wakeups without a separate hardcoded old-live list.
# The ``--mt5-symbol`` arg routes API calls; ``--symbol`` controls the
# storage path so files stay broker-agnostic.
$TickSymbolMap = [ordered]@{
    "AUDJPY"    = "AUDJPY"
    "AUDUSD"    = "AUDUSD"
    "BTCUSD"    = "BTCUSD"
    "CHFJPY"    = "CHFJPY"
    "ETHUSD"    = "ETHUSD"
    "EURGBP"    = "EURGBP"
    "EURJPY"    = "EURJPY"
    "EURUSD"    = "EURUSD"
    "GBPJPY"    = "GBPJPY"
    "GBPUSD"    = "GBPUSD"
    "GER40"     = "GER30"
    "JP225"     = "JP225"
    "NAS100"    = "NDX100"
    "NZDUSD"    = "NZDUSD"
    "SPX500"    = "SPX500"
    "UK100"     = "UK100"
    "UKOIL_cash" = "UKOUSD"
    "US30_cash" = "US30"
    "USDCAD"    = "USDCAD"
    "USDCHF"    = "USDCHF"
    "USDJPY"    = "USDJPY"
    "USOIL_cash" = "USOUSD"
    "XAGUSD"    = "XAGUSD"
    "XAUUSD"    = "XAUUSD"
}

# --- Helpers ---
function Write-Log {
    param([string]$Message)
    $ts = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    $line = "${ts}  ${Message}"
    Write-Host $line
    Add-Content -Path $WatchdogLog -Value $line -Encoding UTF8
}

$script:WatchdogInstanceLock = $null
function Acquire-WatchdogInstanceLock {
    $instanceLockName = if ($RuntimeNamespace) { ".watchdog_${RuntimeNamespace}.lock" } else { ".watchdog.lock" }
    $instanceLockPath = Join-Path $LockDir $instanceLockName
    try {
        if (-not (Test-Path $LogDir))  { New-Item -ItemType Directory -Path $LogDir  -Force | Out-Null }
        if (-not (Test-Path $LockDir)) { New-Item -ItemType Directory -Path $LockDir -Force | Out-Null }
        $script:WatchdogInstanceLock = [System.IO.File]::Open(
            $instanceLockPath,
            [System.IO.FileMode]::OpenOrCreate,
            [System.IO.FileAccess]::ReadWrite,
            [System.IO.FileShare]::None
        )
        $payload = "pid=$PID utc=$((Get-Date).ToUniversalTime().ToString('o'))`n"
        $bytes = [System.Text.Encoding]::UTF8.GetBytes($payload)
        $script:WatchdogInstanceLock.SetLength(0)
        $script:WatchdogInstanceLock.Write($bytes, 0, $bytes.Length)
        $script:WatchdogInstanceLock.Flush()
        return $true
    } catch [System.IO.IOException] {
        Write-Log "  [WATCHDOG_LOCK] another watchdog instance is active for namespace ${RuntimeNamespace}; exiting to prevent duplicate launches"
        return $false
    } catch {
        Write-Log "  [WATCHDOG_LOCK] failed to acquire instance lock: $($_.Exception.Message); continuing fail-open"
        return $true
    }
}

if (-not (Acquire-WatchdogInstanceLock)) {
    exit 0
}

function Test-ProcessAlive {
    param([int]$ProcessId)
    try {
        $proc = Get-Process -Id $ProcessId -ErrorAction Stop
        if ($null -ne $proc -and -not $proc.HasExited) {
            return $true
        }
        return $false
    } catch {
        return $false
    }
}

function Get-ProcessCommandLine {
    param([int]$ProcessId)
    try {
        $proc = Get-CimInstance Win32_Process -Filter "ProcessId = $ProcessId" -ErrorAction Stop
        if ($null -eq $proc -or [string]::IsNullOrWhiteSpace($proc.CommandLine)) {
            return ""
        }
        return [string]$proc.CommandLine
    } catch {
        return ""
    }
}

function Test-ProcessCommandLine {
    param(
        [int]$ProcessId,
        [string[]]$RequiredSubstrings
    )

    if (-not (Test-ProcessAlive -ProcessId $ProcessId)) {
        return $false
    }

    $cmd = Get-ProcessCommandLine -ProcessId $ProcessId
    if ([string]::IsNullOrWhiteSpace($cmd)) {
        return $false
    }

    foreach ($needle in $RequiredSubstrings) {
        if ($cmd -notlike "*$needle*") {
            return $false
        }
    }
    return $true
}

function Test-EnvTruthy {
    param([string]$Value)
    if ([string]::IsNullOrWhiteSpace($Value)) { return $false }
    return @("1", "true", "yes", "y", "on") -contains $Value.Trim().ToLowerInvariant()
}

function Get-FreePhysicalMemoryPct {
    try {
        $os = Get-CimInstance Win32_OperatingSystem
        $totalKb = [double]$os.TotalVisibleMemorySize
        $freeKb = [double]$os.FreePhysicalMemory
        if ($totalKb -le 0) { return $null }
        return [math]::Round(($freeKb / $totalKb) * 100.0, 2)
    } catch {
        return $null
    }
}

# 2026-04-28 sibling-daemon-stability fix: read a lock file that may have
# been written by a python daemon with a UTF-8 BOM (legacy watchdog wrote
# the cmd.exe PID via Set-Content -Encoding UTF8, which prepends a BOM).
# Trim BOM + whitespace before int parse so old + new lock formats both work.
function Read-LockPid {
    param([string]$Path)
    if (-not (Test-Path $Path)) { return 0 }
    try {
        $raw = Get-Content $Path -Raw -ErrorAction Stop
        if ($null -eq $raw) { return 0 }
        # Strip UTF-8 BOM (0xFEFF in PowerShell-decoded form) + whitespace.
        $clean = $raw.TrimStart([char]0xFEFF).Trim()
        if ([string]::IsNullOrEmpty($clean)) { return 0 }
        return [int]$clean
    } catch {
        return 0
    }
}

# Wait for a python daemon to claim its own self-written lock after launch.
# The shared mt5_daemon_runtime.acquire_single_instance_lock helper writes
# the python PID into the lock file; the watchdog reads the result.
#
# This eliminates the Windows cmd.exe-PID confusion that caused 76+ ghost
# restarts of TICK_CAP_XAUUSD between 2026-04-27 and 2026-04-28: the lock
# file used to hold cmd.exe's PID, which separated from the python child
# unpredictably, leaving the watchdog convinced the daemon was dead while
# python piled up orphans.
function Wait-ForDaemonLock {
    param(
        [string]$LockPath,
        [int]$LaunchPidHint,
        [int]$TimeoutSeconds = 30
    )
    $deadline = (Get-Date).AddSeconds($TimeoutSeconds)
    while ((Get-Date) -lt $deadline) {
        $current = Read-LockPid -Path $LockPath
        # We accept the lock as claimed when the daemon-owned PID is set and
        # alive. Direct Python launches use the same PID as the launch hint;
        # cmd-wrapper launches still write the child Python PID here.
        if ($current -gt 0) {
            if (Test-ProcessAlive -ProcessId $current) {
                return $current
            }
        }
        Start-Sleep -Milliseconds 500
    }
    return 0
}

function Wait-ForOrchestratorLock {
    param(
        [string]$LockPath,
        [string]$Symbol,
        [int]$LaunchPidHint,
        [int]$TimeoutSeconds = 30
    )
    $deadline = (Get-Date).AddSeconds($TimeoutSeconds)
    while ((Get-Date) -lt $deadline) {
        if (Test-Path $LockPath) {
            try {
                $data = Get-Content $LockPath -Raw | ConvertFrom-Json
                $current = [int]$data.pid
                if ($current -gt 0) {
                    if (Test-ProcessCommandLine -ProcessId $current -RequiredSubstrings @("run_agent.py", "--symbol ${Symbol}")) {
                        return $current
                    }
                }
            } catch {
                # Process may be writing the JSON lock; retry until timeout.
            }
        }
        Start-Sleep -Milliseconds 500
    }
    return 0
}

function Start-DetachedCommand {
    param(
        [string]$CommandBody,
        [string]$Tag
    )
    $trimmedCommand = $CommandBody.Trim()
    $directPattern = '^cd /d\s+(?<workdir>.+?)\s+&&\s+(?<exe>\S*python(?:\.exe)?)\s+(?<args>.*?)(?:\s+>>\s+"?[^"]+"?\s+2>&1)?$'
    if ($trimmedCommand -match $directPattern) {
        try {
            $psi = New-Object System.Diagnostics.ProcessStartInfo
            $psi.FileName = $Matches["exe"]
            $psi.Arguments = $Matches["args"].Trim()
            $psi.WorkingDirectory = $Matches["workdir"].Trim('"')
            $psi.WindowStyle = [System.Diagnostics.ProcessWindowStyle]::Hidden
            $psi.CreateNoWindow = $true
            $psi.UseShellExecute = $false
            $proc = [System.Diagnostics.Process]::Start($psi)
            if ($null -ne $proc) {
                return [int]$proc.Id
            }
            Write-Log "  [${Tag}] direct python launch returned null"
        } catch {
            Write-Log "  [${Tag}] direct python launch failed: $($_.Exception.Message)"
        }
    }

    $fullCommand = "cmd.exe /c ${CommandBody}"
    try {
        # Use the Win32_Process API for persistent daemons so the launched
        # cmd/python process survives after this watchdog process exits.
        # The deprecated wmic.exe CLI is not reliable on all Windows builds.
        $startup = ([wmiclass]"Win32_ProcessStartup").CreateInstance()
        $startup.ShowWindow = 0
        $creator = [wmiclass]"Win32_Process"
        $result = $creator.Create($fullCommand, $ProjectDir, $startup)
        if ($null -ne $result -and [int]$result.ReturnValue -eq 0 -and [int]$result.ProcessId -gt 0) {
            return [int]$result.ProcessId
        }
        $rv = if ($null -ne $result) { [string]$result.ReturnValue } else { "null" }
        Write-Log "  [${Tag}] Win32_Process launch failed (return=${rv})"
    } catch {
        Write-Log "  [${Tag}] Win32_Process launch threw: $($_.Exception.Message)"
    }

    try {
        $psi = New-Object System.Diagnostics.ProcessStartInfo
        $psi.FileName = "cmd.exe"
        $psi.Arguments = "/c ${CommandBody}"
        $psi.WindowStyle = [System.Diagnostics.ProcessWindowStyle]::Hidden
        $psi.CreateNoWindow = $true
        $proc = [System.Diagnostics.Process]::Start($psi)
        if ($null -ne $proc) {
            return [int]$proc.Id
        }
        Write-Log "  [${Tag}] FAILED - Process.Start returned null"
    } catch {
        Write-Log "  [${Tag}] FAILED - $($_.Exception.Message)"
    }
    return 0
}

function Test-AnyActiveTradeAcrossFleet {
    <#
    .SYNOPSIS
    Returns $true if MT5 reports any open position. Used to defer the
    dead-zone Stop-AllTradingProcesses path so an active trade is not
    orphaned to broker-side TP/SL only. Without an orchestrator, current
    vNext dynamic lifecycle management, partial/BE runner management,
    and ticket-bound reconciliation cannot fire.
    .NOTES
    Live-discovered 2026-04-29 NAS100 ticket 234432798: trade entered
    15:15 UTC, NY KZ ended 16:00, watchdog dead-zone started 17:15 and
    killed the orchestrator before the scheduled management checks. The
    trade ran free at
    broker only, briefly recovered to ~breakeven, then dropped sharply
    and SL'd at 20:15 UTC. With this guard the orch would have stayed
    alive past dead-zone and managed the close (likely BE).

    Fail-open: ANY error in the MT5 query returns False so a broken
    check doesn't permanently block dead-zone cleanup. Cost of an
    unmanaged orphan once is bounded by broker SL; cost of a permanent
    cleanup defer is fleet-wide drift.
    #>
    try {
        $py = "import MetaTrader5 as mt5; ok=mt5.initialize(); p=mt5.positions_get() if ok else None; print(len(p) if p else 0); mt5.shutdown()"
        $output = & python -c $py 2>$null
        if ($output -and ($output -match '^\d+\s*$')) {
            return ([int]$output.Trim() -gt 0)
        }
    } catch {
        # Fail-open: proceed with normal dead-zone behavior.
    }
    return $false
}

function Test-TradingHours {
    $now = Get-Date
    $dayOfWeek = $now.DayOfWeek
    $timeMinutes = $now.Hour * 60 + $now.Minute

    # Sunday: always off
    if ($dayOfWeek -eq 'Sunday') { return $false }

    # Saturday after 01:15: off (Friday NY session ended)
    # Saturday 00:00-01:14: still alive (tail end of Friday session)
    if ($dayOfWeek -eq 'Saturday' -and $timeMinutes -ge $DeadZoneStart) { return $false }

    # Weekday/early-Saturday dead zone: 01:15 to 07:44
    if ($timeMinutes -ge $DeadZoneStart -and $timeMinutes -lt $DeadZoneEnd) {
        return $false
    }

    return $true
}

function Stop-AllTradingProcesses {
    Write-Log "  Stopping all trading processes (outside trading hours)..."
    $killed = 0

    foreach ($symbol in $SymbolMap.Keys) {
        $lockFile = Join-Path $LockDir ".orchestrator_${NamespacePrefix}${symbol}.lock"
        if (Test-Path $lockFile) {
            try {
                $lockData = Get-Content $lockFile -Raw | ConvertFrom-Json
                $lockPid = [int]$lockData.pid
                if (Test-ProcessAlive -ProcessId $lockPid) {
                    Stop-Process -Id $lockPid -Force -ErrorAction SilentlyContinue
                    Write-Log "    [${symbol}] Killed PID ${lockPid}"
                    $killed++
                }
            } catch {
                Write-Log "    [${symbol}] Lock file error: $($_.Exception.Message)"
            }
            Remove-Item $lockFile -Force -ErrorAction SilentlyContinue
        }
    }

    # Kill displacement logger
    # 2026-04-28 fix: lock-PID is now the python daemon's own PID (claimed
    # via mt5_daemon_runtime), not the cmd.exe wrapper. Read-LockPid handles
    # both old (BOM-prefixed) and new lock formats so dead-zone cleanup
    # works during the rolling deployment window.
    $dispLock = Join-Path $LockDir ".displacement_logger.lock"
    if (Test-Path $dispLock) {
        $dispPid = Read-LockPid -Path $dispLock
        if ($dispPid -gt 0) {
            try {
                if (Test-ProcessAlive -ProcessId $dispPid) {
                    Stop-Process -Id $dispPid -Force -ErrorAction SilentlyContinue
                    Write-Log "    [DISPLACEMENT] Killed PID ${dispPid}"
                    $killed++
                }
            } catch {
                Write-Log "    [DISPLACEMENT] Lock cleanup error: $($_.Exception.Message)"
            }
        }
        Remove-Item $dispLock -Force -ErrorAction SilentlyContinue
    }

    # Kill tick-capture daemons (one per symbol).
    # Iterate $TickSymbolMap.Keys (defined at top of script) so every
    # supervised vNext symbol is reaped without separate hardcoded list updates.
    foreach ($tsym in $TickSymbolMap.Keys) {
        $tcLock = Join-Path $LockDir ".tick_capture_${tsym}${NamespaceSuffix}.lock"
        if (Test-Path $tcLock) {
            $tcPid = Read-LockPid -Path $tcLock
            if ($tcPid -gt 0) {
                try {
                    if (Test-ProcessAlive -ProcessId $tcPid) {
                        Stop-Process -Id $tcPid -Force -ErrorAction SilentlyContinue
                        Write-Log "    [TICK_CAP_${tsym}] Killed PID ${tcPid}"
                        $killed++
                    }
                } catch {
                    Write-Log "    [TICK_CAP_${tsym}] Lock cleanup error: $($_.Exception.Message)"
                }
            }
            Remove-Item $tcLock -Force -ErrorAction SilentlyContinue
        }
    }

    # Kill continuous M1 bar capture daemon.
    $m1Lock = Join-Path $LockDir ".m1_capture_all${NamespaceSuffix}.lock"
    if (Test-Path $m1Lock) {
        $m1Pid = Read-LockPid -Path $m1Lock
        if ($m1Pid -gt 0) {
            try {
                if (Test-ProcessAlive -ProcessId $m1Pid) {
                    Stop-Process -Id $m1Pid -Force -ErrorAction SilentlyContinue
                    Write-Log "    [M1_CAPTURE] Killed PID ${m1Pid}"
                    $killed++
                }
            } catch {
                Write-Log "    [M1_CAPTURE] Lock cleanup error: $($_.Exception.Message)"
            }
        }
        Remove-Item $m1Lock -Force -ErrorAction SilentlyContinue
    }

    # Kill heartbeat monitor (T1.1)
    $hbLock = Join-Path $LockDir ".heartbeat_monitor.lock"
    if (Test-Path $hbLock) {
        $hbPid = Read-LockPid -Path $hbLock
        if ($hbPid -gt 0) {
            try {
                if (Test-ProcessAlive -ProcessId $hbPid) {
                    Stop-Process -Id $hbPid -Force -ErrorAction SilentlyContinue
                    Write-Log "    [HEARTBEAT] Killed PID ${hbPid}"
                    $killed++
                }
            } catch {
                Write-Log "    [HEARTBEAT] Lock cleanup error: $($_.Exception.Message)"
            }
        }
        Remove-Item $hbLock -Force -ErrorAction SilentlyContinue
    }

    # Kill notification queue worker (2026-04-28)
    $nqLock = Join-Path $LockDir $NotificationQueueLockName
    if (Test-Path $nqLock) {
        try {
            $nqPid = [int](Get-Content $nqLock -Raw).Trim()
            if (Test-ProcessAlive -ProcessId $nqPid) {
                Stop-Process -Id $nqPid -Force -ErrorAction SilentlyContinue
                Write-Log "    [NOTIFICATION_QUEUE] Killed PID ${nqPid}"
                $killed++
            }
        } catch {
            Write-Log "    [NOTIFICATION_QUEUE] Lock cleanup error: $($_.Exception.Message)"
        }
        Remove-Item $nqLock -Force -ErrorAction SilentlyContinue
    }

    Write-Log "  Stopped ${killed} process(es)"
}

function Invoke-SecondaryExecutionFollowerRole {
    Write-Log "=== Watchdog secondary_execution_follower role: supervising single target-account follower ==="
    Write-Log "  Skipping run_agent fleet, tick_capture fleet, m1_capture, displacement logger, heartbeat monitor, and notification queue worker for secondary role."

    $followerLock = Join-Path $LockDir ".dual_broker_execution_follower_${RuntimeNamespace}.lock"
    $followerLog = Join-Path $LogDir "dual_broker_execution_follower.log"
    $intentLog = if ($env:GTOS_DUAL_BROKER_INTENT_LOG) {
        $env:GTOS_DUAL_BROKER_INTENT_LOG
    } else {
        "pipeline_state\dual_broker\canonical_trade_intents.jsonl"
    }
    $sourceNamespace = if ($env:GTOS_DUAL_BROKER_SOURCE_RUNTIME_NAMESPACE) {
        $env:GTOS_DUAL_BROKER_SOURCE_RUNTIME_NAMESPACE
    } else {
        "redacted_account_live_bee34003"
    }
    $followerPid = Read-LockPid -Path $followerLock
    $required = @(
        "dual_broker_execution_follower.py",
        "--profile $($env:GTOS_PROFILE)",
        "--runtime-namespace ${RuntimeNamespace}",
        "--source-runtime-namespace ${sourceNamespace}",
        "--terminal-path"
    )
    $alive = ($followerPid -gt 0) -and (Test-ProcessCommandLine -ProcessId $followerPid -RequiredSubstrings $required)

    if ($alive) {
        Write-Log "  [DUAL_FOLLOWER] OK - PID ${followerPid} alive"
        return
    }

    if ($followerPid -gt 0) {
        Write-Log "  [DUAL_FOLLOWER] DEAD/STALE - PID ${followerPid} requires restart..."
    } else {
        Write-Log "  [DUAL_FOLLOWER] NOT RUNNING - Starting..."
    }
    Remove-Item $followerLock -Force -ErrorAction SilentlyContinue

    $orderArg = ""
    if (Test-EnvTruthy -Value $env:GTOS_DUAL_BROKER_FOLLOWER_ORDER_ENABLED) {
        $orderArg = " --order-enabled"
    }
    $replayArg = ""
    if (Test-EnvTruthy -Value $env:GTOS_DUAL_BROKER_FOLLOWER_REPLAY_EXISTING) {
        $replayArg = " --replay-existing"
    }

    $cmd = "cd /d ${ProjectDir} && ${PythonExe} scripts\dual_broker_execution_follower.py --mode $($env:GTOS_MODE) --profile $($env:GTOS_PROFILE) --runtime-namespace ${RuntimeNamespace} --source-runtime-namespace ${sourceNamespace} --terminal-path ""${TerminalPath}"" --intent-log ""${intentLog}""${orderArg}${replayArg} >> ""${followerLog}"" 2>&1"
    $launcherPid = Start-DetachedCommand -CommandBody $cmd -Tag "DUAL_FOLLOWER"
    if ($launcherPid -gt 0) {
        $claimedPid = Wait-ForDaemonLock -LockPath $followerLock -LaunchPidHint $launcherPid -TimeoutSeconds 30
        if ($claimedPid -gt 0) {
            Write-Log "  [DUAL_FOLLOWER] STARTED - python PID ${claimedPid} (launcher PID ${launcherPid})"
        } else {
            Write-Log "  [DUAL_FOLLOWER] WARN - launcher PID ${launcherPid} started but python did not claim lock within 30s; will recheck next cycle"
        }
    } else {
        Write-Log "  [DUAL_FOLLOWER] FAILED - detached launch returned no PID"
    }
}

function Get-DualBrokerSourceNamespace {
    if ($env:GTOS_DUAL_BROKER_SOURCE_RUNTIME_NAMESPACE) {
        return $env:GTOS_DUAL_BROKER_SOURCE_RUNTIME_NAMESPACE
    }
    return "redacted_account_live_bee34003"
}

function Get-DualBrokerIntentLog {
    if ($env:GTOS_DUAL_BROKER_INTENT_LOG) {
        return $env:GTOS_DUAL_BROKER_INTENT_LOG
    }
    return "pipeline_state\dual_broker\canonical_trade_intents.jsonl"
}

function Test-DualBrokerPrimaryBridgeEnabled {
    if ($env:GTOS_DUAL_BROKER_BRIDGE_ENABLED) {
        return (Test-EnvTruthy -Value $env:GTOS_DUAL_BROKER_BRIDGE_ENABLED)
    }
    return ($RuntimeRole -eq "primary_full" -and $RuntimeNamespace -eq "redacted_account_live_bee34003")
}

function Invoke-DualBrokerTradeRecordProjectorBridge {
    if (-not (Test-DualBrokerPrimaryBridgeEnabled)) { return }

    $sourceNamespace = Get-DualBrokerSourceNamespace
    $sourceProfile = if ($env:GTOS_DUAL_BROKER_SOURCE_PROFILE) { $env:GTOS_DUAL_BROKER_SOURCE_PROFILE } else { "redacted_account" }
    $sourceRoot = if ($env:GTOS_DUAL_BROKER_SOURCE_ROOT) { $env:GTOS_DUAL_BROKER_SOURCE_ROOT } else { "knowledge_base\redacted_account_live_bee34003\trade_records" }
    $intentLog = Get-DualBrokerIntentLog
    $dualLogDir = Join-Path $ProjectDir "logs\dual_broker"
    if (-not (Test-Path $dualLogDir)) { New-Item -ItemType Directory -Path $dualLogDir -Force | Out-Null }
    $projectorLog = Join-Path $dualLogDir "trade_record_projector.log"
    $projectorLock = Join-Path $LockDir ".dual_broker_trade_record_projector_${sourceNamespace}.lock"
    $projectorPid = Read-LockPid -Path $projectorLock
    $required = @(
        "dual_broker_trade_record_projector.py",
        "--source-root",
        "--intent-log",
        "--source-profile ${sourceProfile}",
        "--source-runtime-namespace ${sourceNamespace}"
    )
    $alive = ($projectorPid -gt 0) -and (Test-ProcessCommandLine -ProcessId $projectorPid -RequiredSubstrings $required)

    if ($alive) {
        Write-Log "  [DUAL_PROJECTOR] OK - PID ${projectorPid} alive"
        $script:healthy++
        return
    }

    if ($projectorPid -gt 0) {
        if (Test-ProcessAlive -ProcessId $projectorPid) {
            Write-Log "  [DUAL_PROJECTOR] STALE COMMAND - PID ${projectorPid} mismatch. Restarting..."
            Stop-Process -Id $projectorPid -Force -ErrorAction SilentlyContinue
        } else {
            Write-Log "  [DUAL_PROJECTOR] DEAD - PID ${projectorPid} gone. Restarting..."
        }
    } else {
        Write-Log "  [DUAL_PROJECTOR] NOT RUNNING - Starting..."
    }
    Remove-Item $projectorLock -Force -ErrorAction SilentlyContinue

    $cmd = "cd /d ${ProjectDir} && ${PythonExe} scripts\dual_broker_trade_record_projector.py --source-root ""${sourceRoot}"" --intent-log ""${intentLog}"" --source-profile ${sourceProfile} --source-runtime-namespace ${sourceNamespace} >> ""${projectorLog}"" 2>&1"
    $launcherPid = Start-DetachedCommand -CommandBody $cmd -Tag "DUAL_PROJECTOR"
    if ($launcherPid -gt 0) {
        $claimedPid = Wait-ForDaemonLock -LockPath $projectorLock -LaunchPidHint $launcherPid -TimeoutSeconds 30
        if ($claimedPid -gt 0) {
            Write-Log "  [DUAL_PROJECTOR] STARTED - python PID ${claimedPid} (launcher PID ${launcherPid})"
            $script:restarted++
        } else {
            Write-Log "  [DUAL_PROJECTOR] WARN - launcher PID ${launcherPid} started but python did not claim lock within 30s; will recheck next cycle"
            $script:restarted++
        }
    } else {
        Write-Log "  [DUAL_PROJECTOR] FAILED - detached launch returned no PID"
    }
}

function Invoke-DualBrokerExecutionFollowerBridge {
    if (-not (Test-DualBrokerPrimaryBridgeEnabled)) { return }

    $sourceNamespace = Get-DualBrokerSourceNamespace
    $targetNamespace = if ($env:GTOS_DUAL_BROKER_TARGET_RUNTIME_NAMESPACE) { $env:GTOS_DUAL_BROKER_TARGET_RUNTIME_NAMESPACE } else { "operator_profile" }
    $targetProfile = if ($env:GTOS_DUAL_BROKER_TARGET_PROFILE) { $env:GTOS_DUAL_BROKER_TARGET_PROFILE } else { "operator_profile" }
    $targetTerminalPath = if ($env:GTOS_DUAL_BROKER_TARGET_TERMINAL_PATH) { $env:GTOS_DUAL_BROKER_TARGET_TERMINAL_PATH } else { "C:\MT5\FTMO\terminal64.exe" }
    $intentLog = Get-DualBrokerIntentLog
    $targetLogDir = Join-Path $ProjectDir "logs\${targetNamespace}"
    if (-not (Test-Path $targetLogDir)) { New-Item -ItemType Directory -Path $targetLogDir -Force | Out-Null }
    $followerLog = Join-Path $targetLogDir "dual_broker_execution_follower.log"
    $followerLock = Join-Path $LockDir ".dual_broker_execution_follower_${targetNamespace}.lock"
    $followerPid = Read-LockPid -Path $followerLock
    $orderEnabled = $true
    if ($env:GTOS_DUAL_BROKER_FOLLOWER_ORDER_ENABLED) {
        $orderEnabled = Test-EnvTruthy -Value $env:GTOS_DUAL_BROKER_FOLLOWER_ORDER_ENABLED
    }
    $orderArg = if ($orderEnabled) { " --order-enabled" } else { "" }
    $required = @(
        "dual_broker_execution_follower.py",
        "--profile ${targetProfile}",
        "--runtime-namespace ${targetNamespace}",
        "--source-runtime-namespace ${sourceNamespace}",
        "--terminal-path",
        "--intent-log",
        "--replay-existing",
        "--reprocess-failed-intents",
        "--live-recovery-window-seconds 1800"
    )
    if ($orderEnabled) { $required += "--order-enabled" }
    $alive = ($followerPid -gt 0) -and (Test-ProcessCommandLine -ProcessId $followerPid -RequiredSubstrings $required)

    if ($alive) {
        Write-Log "  [DUAL_FOLLOWER_PRIMARY_BRIDGE] OK - PID ${followerPid} alive"
        $script:healthy++
        return
    }

    if ($followerPid -gt 0) {
        if (Test-ProcessAlive -ProcessId $followerPid) {
            Write-Log "  [DUAL_FOLLOWER_PRIMARY_BRIDGE] STALE COMMAND - PID ${followerPid} mismatch. Restarting..."
            Stop-Process -Id $followerPid -Force -ErrorAction SilentlyContinue
        } else {
            Write-Log "  [DUAL_FOLLOWER_PRIMARY_BRIDGE] DEAD - PID ${followerPid} gone. Restarting..."
        }
    } else {
        Write-Log "  [DUAL_FOLLOWER_PRIMARY_BRIDGE] NOT RUNNING - Starting..."
    }
    Remove-Item $followerLock -Force -ErrorAction SilentlyContinue

    $liveRecoveryArg = " --replay-existing --reprocess-failed-intents --live-recovery-window-seconds 1800"
    $cmd = "cd /d ${ProjectDir} && ${PythonExe} scripts\dual_broker_execution_follower.py --mode $($env:GTOS_MODE) --profile ${targetProfile} --runtime-namespace ${targetNamespace} --source-runtime-namespace ${sourceNamespace} --terminal-path ""${targetTerminalPath}"" --intent-log ""${intentLog}""${orderArg}${liveRecoveryArg} >> ""${followerLog}"" 2>&1"
    $launcherPid = Start-DetachedCommand -CommandBody $cmd -Tag "DUAL_FOLLOWER_PRIMARY_BRIDGE"
    if ($launcherPid -gt 0) {
        $claimedPid = Wait-ForDaemonLock -LockPath $followerLock -LaunchPidHint $launcherPid -TimeoutSeconds 30
        if ($claimedPid -gt 0) {
            Write-Log "  [DUAL_FOLLOWER_PRIMARY_BRIDGE] STARTED - python PID ${claimedPid} (launcher PID ${launcherPid})"
            $script:restarted++
        } else {
            Write-Log "  [DUAL_FOLLOWER_PRIMARY_BRIDGE] WARN - launcher PID ${launcherPid} started but python did not claim lock within 30s; will recheck next cycle"
            $script:restarted++
        }
    } else {
        Write-Log "  [DUAL_FOLLOWER_PRIMARY_BRIDGE] FAILED - detached launch returned no PID"
    }
}

# --- Main ---

# Ensure directories exist
if (-not (Test-Path $LogDir))  { New-Item -ItemType Directory -Path $LogDir  -Force | Out-Null }
if (-not (Test-Path $LockDir)) { New-Item -ItemType Directory -Path $LockDir -Force | Out-Null }

# Load .env early so weekend / dead-zone hooks (e.g. calendar staleness)
# have access to TELEGRAM_BOT_TOKEN + TELEGRAM_CHAT_ID even when the rest
# of the watchdog short-circuits to clean-up. The previous load was at the
# top of the in-trading-hours branch only, which left the Sunday refresh
# hook unauthenticated. Idempotent (only sets unset env vars).
$envFile = Join-Path $ProjectDir ".env"
if (Test-Path $envFile) {
    Get-Content $envFile | ForEach-Object {
        if ($_ -match '^\s*([^#][^=]+?)\s*=\s*(.+)\s*$') {
            $envKey = $Matches[1].Trim()
            $envVal = $Matches[2].Trim()
            if (-not [System.Environment]::GetEnvironmentVariable($envKey, "Process")) {
                [System.Environment]::SetEnvironmentVariable($envKey, $envVal, "Process")
            }
        }
    }
}

$RuntimeRole = $env:GTOS_RUNTIME_ROLE
if ($RuntimeRole -eq "secondary_execution_follower") {
    Invoke-SecondaryExecutionFollowerRole
    exit 0
}

# --- Economic-Calendar Staleness Monitor (always-on, even on weekends) ---
# Hoisted ABOVE Test-TradingHours so Sunday + dead-zone wakeups still fire
# the staleness check. The calendar is operator-maintained on a weekly
# cadence (typically Sunday evening ahead of Tokyo open Monday); without
# this hoist the alerter went silent every Sunday — exactly when the
# operator most needs the reminder. The check is pure file-stat + JSON read,
# touches no MT5 / trading state, and is gated by a once-per-UTC-day marker
# so it does not spam during long staleness windows.
#
# Note: the script's own 24h cooldown (knowledge_base/meta/calendar_staleness_state.json)
# provides the second-layer rate-limit. The marker file below is a watchdog-side
# optimization to skip re-running the script entirely once we've already run it
# today; if the script returns exit=2 (queue subsystem unavailable) the marker
# is intentionally NOT written so the next watchdog tick retries.
function Invoke-CalendarStalenessHook {
    param([string]$Tag = "CAL_STALE")
    try {
        $calMarkerFile = Join-Path $LockDir "calendar_staleness_last_run.utcdate"
        $calTodayUtc   = (Get-Date).ToUniversalTime().ToString("yyyy-MM-dd")
        $calShouldRun  = $true
        if (Test-Path $calMarkerFile) {
            $calLastRun = (Get-Content $calMarkerFile -Raw -ErrorAction SilentlyContinue)
            if ($null -ne $calLastRun) {
                $calLastRun = $calLastRun.Trim()
                if ($calLastRun -eq $calTodayUtc) { $calShouldRun = $false }
            }
        }
        if (-not $calShouldRun) { return }
        $calScript = Join-Path $ProjectDir "scripts\refresh_economic_calendar.py"
        $calLog    = Join-Path $LogDir "calendar_staleness.log"
        $calArgs   = "/c cd /d ${ProjectDir} && ${PythonExe} ${calScript} >> ""${calLog}"" 2>&1"
        $calPsi    = New-Object System.Diagnostics.ProcessStartInfo
        $calPsi.FileName       = "cmd.exe"
        $calPsi.Arguments      = $calArgs
        $calPsi.WindowStyle    = [System.Diagnostics.ProcessWindowStyle]::Hidden
        $calPsi.CreateNoWindow = $true
        $calProc = [System.Diagnostics.Process]::Start($calPsi)
        if ($null -ne $calProc) {
            $calCompleted = $calProc.WaitForExit(30000)
            if (-not $calCompleted) {
                try { $calProc.Kill() } catch {}
                Write-Log "  [${Tag}] TIMEOUT - killed after 30s, retry next heartbeat"
            } else {
                $calExit = $calProc.ExitCode
                if ($calExit -eq 0) {
                    Write-Log "  [${Tag}] OK"
                    $calTodayUtc | Set-Content -Path $calMarkerFile -Encoding UTF8
                } elseif ($calExit -eq 1) {
                    Write-Log "  [${Tag}] Alert needed but Telegram creds missing"
                    $calTodayUtc | Set-Content -Path $calMarkerFile -Encoding UTF8
                } elseif ($calExit -eq 2) {
                    Write-Log "  [${Tag}] Queue enqueue failed - retry next heartbeat"
                } else {
                    Write-Log "  [${Tag}] UNEXPECTED exit=${calExit}"
                }
            }
        } else {
            Write-Log "  [${Tag}] FAILED - Process.Start returned null"
        }
    } catch {
        Write-Log "  [${Tag}] FAILED - $($_.Exception.Message)"
    }
}

function Get-DaemonProgressAgeSeconds {
    param([string]$Name)
    $hbPath = Join-Path $ProjectDir "pipeline_state\daemon_heartbeat_${Name}.json"
    if (-not (Test-Path $hbPath)) { return $null }
    try {
        $data = Get-Content $hbPath -Raw -ErrorAction Stop | ConvertFrom-Json
        $stamp = $data.last_progress_utc
        if ([string]::IsNullOrWhiteSpace([string]$stamp)) { return $null }
        $dt = [DateTimeOffset]::Parse([string]$stamp).ToUniversalTime()
        return ([DateTimeOffset]::UtcNow - $dt).TotalSeconds
    } catch {
        return $null
    }
}

function Get-DaemonHeartbeatAgeSeconds {
    param([string]$Name)
    $hbPath = Join-Path $ProjectDir "pipeline_state\daemon_heartbeat_${Name}.json"
    if (-not (Test-Path $hbPath)) { return $null }
    try {
        $data = Get-Content $hbPath -Raw -ErrorAction Stop | ConvertFrom-Json
        $stamp = $data.liveness_utc
        if ([string]::IsNullOrWhiteSpace([string]$stamp)) { $stamp = $data.utc }
        if ([string]::IsNullOrWhiteSpace([string]$stamp)) { return $null }
        $dt = [DateTimeOffset]::Parse([string]$stamp).ToUniversalTime()
        return ([DateTimeOffset]::UtcNow - $dt).TotalSeconds
    } catch {
        return $null
    }
}

function Invoke-NotificationQueueDeadZoneAudit {
    param(
        [string]$Tag = "NOTIFICATION_DEAD_ZONE",
        [bool]$UseDailyMarker = $true
    )
    try {
        $nqDzMarkerFile = Join-Path $LockDir "notification_queue_dead_zone_last_run.utcdate"
        $nqDzTodayUtc   = (Get-Date).ToUniversalTime().ToString("yyyy-MM-dd")
        $nqDzShouldRun  = $true
        if ($UseDailyMarker -and (Test-Path $nqDzMarkerFile)) {
            $nqDzLastRun = (Get-Content $nqDzMarkerFile -Raw -ErrorAction SilentlyContinue)
            if ($null -ne $nqDzLastRun) {
                $nqDzLastRun = $nqDzLastRun.Trim()
                if ($nqDzLastRun -eq $nqDzTodayUtc) { $nqDzShouldRun = $false }
            }
        }
        if (-not $nqDzShouldRun) { return }
        $nqDzScript = Join-Path $ProjectDir "scripts\audit_notification_queue_dead_zone.py"
        $nqDzLog    = Join-Path $LogDir "notification_queue_dead_zone.log"
        $nqDzArgs   = "/c cd /d ${ProjectDir} && ${PythonExe} ${nqDzScript} --queue-path ""${NotificationQueuePath}"" --lock-path ""knowledge_base\meta\${NotificationQueueLockName}"" >> ""${nqDzLog}"" 2>&1"
        $nqDzPsi    = New-Object System.Diagnostics.ProcessStartInfo
        $nqDzPsi.FileName       = "cmd.exe"
        $nqDzPsi.Arguments      = $nqDzArgs
        $nqDzPsi.WindowStyle    = [System.Diagnostics.ProcessWindowStyle]::Hidden
        $nqDzPsi.CreateNoWindow = $true
        $nqDzProc = [System.Diagnostics.Process]::Start($nqDzPsi)
        if ($null -ne $nqDzProc) {
            $nqDzCompleted = $nqDzProc.WaitForExit(60000)
            if (-not $nqDzCompleted) {
                try { $nqDzProc.Kill() } catch {}
                Write-Log "  [${Tag}] TIMEOUT - killed after 60s, retry next heartbeat"
            } else {
                $nqDzExit = $nqDzProc.ExitCode
                if ($nqDzExit -eq 0) {
                    Write-Log "  [${Tag}] OK"
                    if ($UseDailyMarker) { $nqDzTodayUtc | Set-Content -Path $nqDzMarkerFile -Encoding UTF8 }
                } elseif ($nqDzExit -eq 1) {
                    Write-Log "  [${Tag}] ACTION_REQUIRED - see research/program_control/LTO037_NOTIFICATION_QUEUE_DEAD_ZONE_STATUS_2026-05-05.md"
                } else {
                    Write-Log "  [${Tag}] UNEXPECTED exit=${nqDzExit}"
                }
            }
        } else {
            Write-Log "  [${Tag}] FAILED - Process.Start returned null"
        }
    } catch {
        Write-Log "  [${Tag}] FAILED - $($_.Exception.Message)"
    }
}

function Invoke-StorageRetentionAudit {
    param([string]$Tag = "STORAGE_RETENTION")
    try {
        $storageMarkerFile = Join-Path $LockDir "storage_retention_last_run.utcdate"
        $storageTodayUtc   = (Get-Date).ToUniversalTime().ToString("yyyy-MM-dd")
        $storageShouldRun  = $true
        if (Test-Path $storageMarkerFile) {
            $storageLastRun = (Get-Content $storageMarkerFile -Raw -ErrorAction SilentlyContinue)
            if ($null -ne $storageLastRun) {
                $storageLastRun = $storageLastRun.Trim()
                if ($storageLastRun -eq $storageTodayUtc) { $storageShouldRun = $false }
            }
        }
        if (-not $storageShouldRun) { return }
        $storageScript = Join-Path $ProjectDir "scripts\audit_storage_retention.py"
        $storageLog    = Join-Path $LogDir "storage_retention.log"
        $storageArgs   = "/c cd /d ${ProjectDir} && ${PythonExe} ${storageScript} --dry-run >> ""${storageLog}"" 2>&1"
        $storagePsi    = New-Object System.Diagnostics.ProcessStartInfo
        $storagePsi.FileName       = "cmd.exe"
        $storagePsi.Arguments      = $storageArgs
        $storagePsi.WindowStyle    = [System.Diagnostics.ProcessWindowStyle]::Hidden
        $storagePsi.CreateNoWindow = $true
        $storageProc = [System.Diagnostics.Process]::Start($storagePsi)
        if ($null -ne $storageProc) {
            $storageCompleted = $storageProc.WaitForExit(120000)
            if (-not $storageCompleted) {
                try { $storageProc.Kill() } catch {}
                Write-Log "  [${Tag}] TIMEOUT - killed after 120s, retry next heartbeat"
            } else {
                $storageExit = $storageProc.ExitCode
                if ($storageExit -eq 0) {
                    Write-Log "  [${Tag}] OK"
                    $storageTodayUtc | Set-Content -Path $storageMarkerFile -Encoding UTF8
                } elseif ($storageExit -eq 1) {
                    Write-Log "  [${Tag}] ACTION_REQUIRED - see research/program_control/LTO038_STORAGE_RETENTION_STATUS_2026-05-05.md"
                } else {
                    Write-Log "  [${Tag}] UNEXPECTED exit=${storageExit}"
                }
            }
        } else {
            Write-Log "  [${Tag}] FAILED - Process.Start returned null"
        }
    } catch {
        Write-Log "  [${Tag}] FAILED - $($_.Exception.Message)"
    }
}

function Invoke-LiveMonitoringMaintenance {
    param([string]$Tag = "LIVE_MAINTENANCE")
    try {
        $freeMemoryPct = Get-FreePhysicalMemoryPct
        $minFreeMemoryPct = 25.0
        if ($null -ne $freeMemoryPct -and $freeMemoryPct -lt $minFreeMemoryPct) {
            Write-Log "  [${Tag}] SKIP - free physical memory ${freeMemoryPct}% < ${minFreeMemoryPct}%; preserving live trading footprint"
            return
        }
        if (Test-EnvTruthy -Value $env:GTOS_SUPPRESS_LIVE_MONITORING_MAINTENANCE_WITH_DUAL_BROKER) {
            $dualBrokerBridge = Get-CimInstance Win32_Process | Where-Object {
                $_.Name -eq 'python.exe' -and
                $_.CommandLine -notlike '*pytest*' -and
                (
                    $_.CommandLine -like '*dual_broker_trade_record_projector.py*' -or
                    $_.CommandLine -like '*dual_broker_execution_follower.py*'
                )
            }
            if ($dualBrokerBridge) {
                $dualIds = ($dualBrokerBridge | ForEach-Object { [string]$_.ProcessId }) -join ","
                Write-Log "  [${Tag}] SKIP - explicit dual-broker maintenance suppression active PID(s)=${dualIds}; suppressing widening maintenance"
                return
            }
        }
        $existingMaintenance = Get-CimInstance Win32_Process | Where-Object {
            $_.CommandLine -like '*run_live_monitoring_maintenance.py*' -or
            $_.CommandLine -like '*follow_live_candidate_paths.py*'
        }
        if ($existingMaintenance) {
            $existingIds = ($existingMaintenance | ForEach-Object { [string]$_.ProcessId }) -join ","
            Write-Log "  [${Tag}] SKIP - maintenance/follow process already running PID(s)=${existingIds}"
            return
        }
        $maintMarkerFile = Join-Path $LockDir "live_monitoring_maintenance_last_run.utcdate"
        $maintNowUtc     = (Get-Date).ToUniversalTime()
        $maintIntervalMinutes = 30
        $maintShouldRun  = $true
        if (Test-Path $maintMarkerFile) {
            $maintLastRun = (Get-Content $maintMarkerFile -Raw -ErrorAction SilentlyContinue)
            if ($null -ne $maintLastRun) {
                $maintLastRun = $maintLastRun.Trim()
                try {
                    $maintLastRunUtc = ([DateTime]::Parse($maintLastRun)).ToUniversalTime()
                    $maintAgeMinutes = ($maintNowUtc - $maintLastRunUtc).TotalMinutes
                    if ($maintAgeMinutes -lt $maintIntervalMinutes) { $maintShouldRun = $false }
                } catch {
                    $maintShouldRun = $true
                }
            }
        }
        if (-not $maintShouldRun) { return }
        $maintScript = Join-Path $ProjectDir "scripts\run_live_monitoring_maintenance.py"
        $maintLog    = Join-Path $LogDir "live_monitoring_maintenance.log"
        $maintPsi    = New-Object System.Diagnostics.ProcessStartInfo
        $maintPsi.FileName       = $PythonExe
        $maintPsi.Arguments      = """${maintScript}"" --max-hours 24 --step-timeout-seconds 900 --skip-live-pulse --skip-shadow-observer-once"
        $maintPsi.WorkingDirectory = $ProjectDir
        $maintPsi.WindowStyle    = [System.Diagnostics.ProcessWindowStyle]::Hidden
        $maintPsi.CreateNoWindow = $true
        $maintPsi.UseShellExecute = $false
        $maintPsi.RedirectStandardOutput = $true
        $maintPsi.RedirectStandardError = $true
        $maintProc = New-Object System.Diagnostics.Process
        $maintProc.StartInfo = $maintPsi
        [void]$maintProc.Start()
        if ($null -ne $maintProc) {
            $maintStdout = $maintProc.StandardOutput.ReadToEndAsync()
            $maintStderr = $maintProc.StandardError.ReadToEndAsync()
            $maintCompleted = $maintProc.WaitForExit(900000)
            if (-not $maintCompleted) {
                try { $maintProc.Kill() } catch {}
                try { $maintProc.WaitForExit(5000) } catch {}
                try {
                    Add-Content -Path $maintLog -Value $maintStdout.Result -Encoding UTF8
                    Add-Content -Path $maintLog -Value $maintStderr.Result -Encoding UTF8
                } catch {}
                Write-Log "  [${Tag}] TIMEOUT - killed after 900s, retry next heartbeat"
            } else {
                $maintProc.WaitForExit()
                try {
                    Add-Content -Path $maintLog -Value $maintStdout.Result -Encoding UTF8
                    Add-Content -Path $maintLog -Value $maintStderr.Result -Encoding UTF8
                } catch {
                    Write-Log "  [${Tag}] log append failed: $($_.Exception.Message)"
                }
                $maintExit = $maintProc.ExitCode
                if ($maintExit -eq 0) {
                    Write-Log "  [${Tag}] OK"
                    $maintNowUtc.ToString("o") | Set-Content -Path $maintMarkerFile -Encoding UTF8
                } elseif ($maintExit -eq 1) {
                    Write-Log "  [${Tag}] ACTION_REQUIRED - see pipeline_state/live_monitoring_maintenance_state.json"
                    $maintNowUtc.ToString("o") | Set-Content -Path $maintMarkerFile -Encoding UTF8
                } else {
                    Write-Log "  [${Tag}] UNEXPECTED exit=${maintExit}"
                }
            }
        } else {
            Write-Log "  [${Tag}] FAILED - Process.Start returned null"
        }
    } catch {
        Write-Log "  [${Tag}] FAILED - $($_.Exception.Message)"
    }
}

$OutsideTradingHoursWithActiveTrade = $false

# Check trading hours FIRST
if (-not (Test-TradingHours)) {
    # Active-trade defer (2026-04-29): if any orchestrator has an open MT5
    # position, skip the cleanup path so the orchestrator keeps running
    # through dead zone and manages the trade through close. Without this,
    # late-session fills can lose vNext dynamic lifecycle management and
    # ticket-bound reconciliation; broker TP/SL becomes the only protection.
    # Live-discovered cost: NAS100 ticket 234432798
    # = -$103.56 SL hit instead of likely BE close.
    if (Test-AnyActiveTradeAcrossFleet) {
        $OutsideTradingHoursWithActiveTrade = $true
        Write-Log "=== Watchdog: outside trading hours but ACTIVE TRADE detected - supervising live management stack ==="
        Write-Log "  Cleanup is deferred, and dead orchestrator/support processes will be restarted for ticket-bound management."
        Write-Log "  New-entry gates remain governed by runtime/session permissions; this branch prevents unmanaged open exposure."
    }
    if (-not $OutsideTradingHoursWithActiveTrade) {
        Write-Log "=== Watchdog: OUTSIDE TRADING HOURS - cleaning up ==="
        Stop-AllTradingProcesses
        Invoke-NotificationQueueDeadZoneAudit -Tag "NOTIFICATION_DEAD_ZONE_OFFHOURS" -UseDailyMarker $false
        # Sunday + dead-zone calendar staleness check. Operator-maintained
        # ForexFactory data is typically refreshed Sunday evening; this hook
        # makes sure the reminder arrives even when no trading process is up.
        Invoke-CalendarStalenessHook -Tag "CAL_STALE_OFFHOURS"
        Write-Log "=== Watchdog: Done (will restart processes when trading hours resume) ==="
        exit 0
    }
}

if ($OutsideTradingHoursWithActiveTrade) {
    Write-Log "=== Watchdog check started (outside-hours active-trade management mode) ==="
} else {
    Write-Log "=== Watchdog check started ==="
}

# --- Git working-tree drift check ---
# Warn (don't fail) when uncommitted changes exist in code-bearing paths. A
# watchdog respawn will run whatever Python files are on disk, not what's in
# git HEAD, so uncommitted working-tree edits get silently promoted to live.
# This happened once (pre-AI gate direction-aware upgrade, commit a84abde).
# Focus on src/, scripts/, prompts/, config/, tests/, run_agent.py — not
# logs/, knowledge_base/, pipeline_state/, shadow_logs/ (runtime churn).
try {
    $gitExe = "git"
    $gitStatus = & $gitExe -C $ProjectDir status --porcelain 2>$null
    if ($LASTEXITCODE -eq 0 -and $null -ne $gitStatus) {
        $driftPaths = @()
        foreach ($line in $gitStatus) {
            # Porcelain v1 format: "XY path" (cols 1-2 = status, col 3 = space, rest = path).
            # Strip status prefix; keep the trailing path (may contain spaces).
            if ($line.Length -lt 4) { continue }
            $path = $line.Substring(3).Trim('"')
            # Renames: "orig -> new" — take the destination.
            if ($path -match " -> ") { $path = ($path -split " -> ", 2)[1] }
            if ($path -match "^(src/|scripts/|prompts/|config/|tests/|run_agent\.py)") {
                $driftPaths += $path
            }
        }
        if ($driftPaths.Count -gt 0) {
            Write-Log "WARNING: uncommitted changes in working tree -- live code may differ from git HEAD. Consider committing before next respawn."
            foreach ($p in $driftPaths) { Write-Log "  drift: ${p}" }
        }
    }
} catch {
    # git unavailable or other error — non-fatal, skip silently.
}

# .env is loaded earlier (above Test-TradingHours) so weekend / dead-zone
# hooks have access to TELEGRAM_* + ANTHROPIC_API_KEY too. The early load
# is idempotent so no second load is needed here.

$restarted = 0
$healthy   = 0

# --- Trading agent processes ---
foreach ($symbol in $SymbolMap.Keys) {
    $lockFile = Join-Path $LockDir ".orchestrator_${NamespacePrefix}${symbol}.lock"
    $logFile  = Join-Path $LogDir $SymbolMap[$symbol]
    $alive    = $false
    $lockPid  = 0

    # Check lock file
    if (Test-Path $lockFile) {
        try {
            $lockData = Get-Content $lockFile -Raw | ConvertFrom-Json
            $lockPid = [int]$lockData.pid
            $alive = Test-ProcessCommandLine -ProcessId $lockPid -RequiredSubstrings @(
                "run_agent.py",
                "--symbol ${symbol}",
                "--mode $($env:GTOS_MODE)",
                "--profile $($env:GTOS_PROFILE)",
                "--runtime-namespace ${RuntimeNamespace}",
                "--terminal-path"
            )
        } catch {
            Write-Log "  [${symbol}] Lock file corrupt - treating as dead"
            $alive = $false
        }
    }

    if ($alive) {
        Write-Log "  [${symbol}] OK - PID ${lockPid} alive"
        $healthy++
    } else {
        # Graceful-shutdown marker check (2026-04-29):
        # When an orch shuts down with "all KZ complete, no active trade"
        # it writes pipeline_state/.orch_shutdown_{SYMBOL}.json with a
        # ``valid_until_utc`` ~= the next dead-zone exit. Without this
        # check, the watchdog respawns immediately, the orch boots, sees
        # "all KZ complete" again, shuts down → respawn loop every 15
        # min until next dead zone. Honor the marker; skip respawn until
        # ``valid_until_utc`` passes.
        $shutdownMarker = Join-Path $ProjectDir "pipeline_state\.orch_shutdown_${symbol}.json"
        $skipRespawn = $false
        if (Test-Path $shutdownMarker) {
            try {
                $markerData = Get-Content $shutdownMarker -Raw | ConvertFrom-Json
                # Coerce to UTC-aware DateTime: [datetime]::Parse returns
                # Kind=Local on Singapore (UTC+8) systems while UtcNow is
                # Kind=Utc. .NET DateTime comparison is Kind-blind (compares
                # raw ticks), so without ToUniversalTime() the marker
                # effectively expires +8h late — would suppress next-day
                # Tokyo (00:00-03:00 UTC) and London (07:00-09:30 UTC)
                # respawns for USDJPY/GBPJPY/GBPUSD. (Caught by review-
                # agent post-merge; one-line fix.)
                $validUntil = [datetime]::Parse($markerData.valid_until_utc).ToUniversalTime()
                $nowUtc = [datetime]::UtcNow
                if ($nowUtc -lt $validUntil) {
                    Write-Log "  [${symbol}] GRACEFUL SHUTDOWN MARKER active until $($validUntil.ToString('yyyy-MM-ddTHH:mm:ssZ')) - skipping respawn"
                    $skipRespawn = $true
                } else {
                    Write-Log "  [${symbol}] graceful shutdown marker expired - removing + respawning"
                    Remove-Item $shutdownMarker -Force -ErrorAction SilentlyContinue
                }
            } catch {
                Write-Log "  [${symbol}] shutdown marker corrupt ($($_.Exception.Message)) - ignoring + respawning"
                Remove-Item $shutdownMarker -Force -ErrorAction SilentlyContinue
            }
        }

        if ($skipRespawn) { continue }

        if ($lockPid -gt 0) {
            if (Test-ProcessAlive -ProcessId $lockPid) {
                Write-Log "  [${symbol}] STALE COMMAND - PID ${lockPid} mode/profile mismatch. Restarting..."
                Stop-Process -Id $lockPid -Force -ErrorAction SilentlyContinue
            } else {
                Write-Log "  [${symbol}] DEAD - PID ${lockPid} gone. Restarting..."
            }
            Remove-Item $lockFile -Force -ErrorAction SilentlyContinue
        } else {
            Write-Log "  [${symbol}] NOT RUNNING - no lock file. Starting..."
        }

        $cmd = "cd /d ${ProjectDir} && ${PythonExe} run_agent.py --symbol ${symbol} --mode $($env:GTOS_MODE) --profile $($env:GTOS_PROFILE) --runtime-namespace ${RuntimeNamespace} --terminal-path ""${TerminalPath}"" >> ""${logFile}"" 2>&1"
        $launcherPid = Start-DetachedCommand -CommandBody $cmd -Tag $symbol
        if ($launcherPid -gt 0) {
            $claimedPid = Wait-ForOrchestratorLock -LockPath $lockFile -Symbol $symbol -LaunchPidHint $launcherPid -TimeoutSeconds 30
            if ($claimedPid -gt 0) {
                Write-Log "  [${symbol}] STARTED - python PID ${claimedPid} (launcher PID ${launcherPid})"
                $restarted++
            } else {
                Write-Log "  [${symbol}] WARN - launcher PID ${launcherPid} started but orchestrator did not claim a live lock within 30s; will recheck next cycle"
                $restarted++
            }
        }
    }
}

# --- Displacement Logger ---
# 2026-04-28 fix: lock-file reads accept the python daemon's own PID (written
# by ``mt5_daemon_runtime.acquire_single_instance_lock`` at startup), NOT the
# cmd.exe wrapper PID. This eliminates the Windows orphan-python pile-up bug.
$dispLock = Join-Path $LockDir ".displacement_logger.lock"
$dispLog  = Join-Path $LogDir "displacement.log"
$dispPid  = Read-LockPid -Path $dispLock
$dispAlive = ($dispPid -gt 0) -and (Test-ProcessCommandLine -ProcessId $dispPid -RequiredSubstrings @("displacement_logger.py", "--continuous"))

if ($dispAlive) {
    Write-Log "  [DISPLACEMENT] OK - PID ${dispPid} alive"
    $healthy++
} else {
    if ($dispPid -gt 0) {
        Write-Log "  [DISPLACEMENT] DEAD - PID ${dispPid} gone. Restarting..."
    } else {
        Write-Log "  [DISPLACEMENT] NOT RUNNING - Starting..."
    }
    Remove-Item $dispLock -Force -ErrorAction SilentlyContinue

    try {
        $cmd = "cd /d ${ProjectDir} && ${PythonExe} scripts/displacement_logger.py --continuous >> ""${dispLog}"" 2>&1"
        $launcherPid = Start-DetachedCommand -CommandBody $cmd -Tag "DISPLACEMENT"
        if ($launcherPid -gt 0) {
            # Wait up to 30s for the python child to claim its self-written lock.
            $claimedPid = Wait-ForDaemonLock -LockPath $dispLock -LaunchPidHint $launcherPid -TimeoutSeconds 30
            if ($claimedPid -gt 0) {
                Write-Log "  [DISPLACEMENT] STARTED - python PID ${claimedPid} (launcher PID ${launcherPid})"
                $restarted++
            } else {
                Write-Log "  [DISPLACEMENT] WARN - launcher PID ${launcherPid} started but python did not claim lock within 30s; will recheck next cycle"
                $restarted++
            }
        }
    } catch {
        Write-Log "  [DISPLACEMENT] FAILED - $($_.Exception.Message)"
    }
}

# --- Tick Capture Daemons (one process per symbol, persistent) ---
# Streams MT5 ticks into per-day Parquet files under data/ticks/{SYMBOL}/.
# These are observational-only — never gate trades. The tick-features
# extractor reads them on M15 close (additive to data_ingestion).
#
# Stale-tick detection: each daemon writes
# pipeline_state/daemon_heartbeat_tick_capture_{SYMBOL}.json on successful
# flush. A live PID with stale progress is restarted; PID-only checks missed
# this exact failure mode when MT5 stayed connected but copy_ticks_from stopped
# advancing.
#
# $TickSymbolMap is defined at the top of the script (alongside $SymbolMap)
# so Stop-AllTradingProcesses can iterate it during the OUTSIDE-TRADING-HOURS
# cleanup path, which runs BEFORE this launch loop ever executes.
foreach ($tsym in $TickSymbolMap.Keys) {
    $tcLock  = Join-Path $LockDir ".tick_capture_${tsym}${NamespaceSuffix}.lock"
    $tcLog   = Join-Path $LogDir  "tick_capture_${tsym}.log"
    $tcPid   = Read-LockPid -Path $tcLock
    $tcAlive = ($tcPid -gt 0) -and (Test-ProcessCommandLine -ProcessId $tcPid -RequiredSubstrings @("src.components.tick_capture", "--symbol ${tsym}", "--runtime-namespace ${RuntimeNamespace}", "--terminal-path"))

    if ($tcAlive) {
        $heartbeatAge = Get-DaemonHeartbeatAgeSeconds -Name "tick_capture_${tsym}${NamespaceSuffix}"
        $progressAge = Get-DaemonProgressAgeSeconds -Name "tick_capture_${tsym}${NamespaceSuffix}"
        $staleSeconds = $TickCaptureProgressStaleMinutes * 60
        if ($null -eq $heartbeatAge) {
            Write-Log "  [TICK_CAP_${tsym}] STALE - PID ${tcPid} alive but no liveness heartbeat. Restarting..."
            Stop-Process -Id $tcPid -Force -ErrorAction SilentlyContinue
            $tcAlive = $false
        } elseif ($heartbeatAge -gt $staleSeconds) {
            Write-Log "  [TICK_CAP_${tsym}] STALE - PID ${tcPid} alive but liveness heartbeat age $([math]::Round($heartbeatAge, 1))s > ${staleSeconds}s. Restarting..."
            Stop-Process -Id $tcPid -Force -ErrorAction SilentlyContinue
            $tcAlive = $false
        } elseif ($null -ne $progressAge -and $progressAge -gt $staleSeconds) {
            Write-Log "  [TICK_CAP_${tsym}] STALE - PID ${tcPid} alive but data progress age $([math]::Round($progressAge, 1))s > ${staleSeconds}s. Restarting..."
            Stop-Process -Id $tcPid -Force -ErrorAction SilentlyContinue
            $tcAlive = $false
        } else {
            $progressText = if ($null -eq $progressAge) { "no data-progress timestamp" } else { "data progress age $([math]::Round($progressAge, 1))s" }
            Write-Log "  [TICK_CAP_${tsym}] OK - PID ${tcPid} alive, liveness age $([math]::Round($heartbeatAge, 1))s, ${progressText}"
            $healthy++
        }
    }

    if (-not $tcAlive) {
        if ($tcPid -gt 0) {
            Write-Log "  [TICK_CAP_${tsym}] DEAD/STALE - PID ${tcPid} requires restart..."
        } else {
            Write-Log "  [TICK_CAP_${tsym}] NOT RUNNING - Starting..."
        }
        Remove-Item $tcLock -Force -ErrorAction SilentlyContinue
        try {
            $brokerSym = $TickSymbolMap[$tsym]
            # Tick capture is an always-on observational daemon. Some broker
            # CFDs/indices/oil symbols can be legitimately quote-stale while
            # the global watchdog window is active; keep the process alive and
            # let the checkpoint classify daemon-alive/no-new-broker-tick
            # instead of crash-looping on startup freshness.
            $tickFreshnessArg = " --skip-tick-freshness-check"
            $tcArgs = "cd /d ${ProjectDir} && ${PythonExe} -m src.components.tick_capture --symbol ${tsym} --mt5-symbol ${brokerSym} --runtime-namespace ${RuntimeNamespace} --terminal-path ""${TerminalPath}""${tickFreshnessArg} >> ""${tcLog}"" 2>&1"
            $launcherPid = Start-DetachedCommand -CommandBody $tcArgs -Tag "TICK_CAP_${tsym}"
            if ($launcherPid -gt 0) {
                # Wait up to 30s for the python child to claim its self-written
                # lock. Fresh-tick + symbol_select retries can take up to ~31s
                # in the worst case (5 attempts, exponential backoff 1->16s),
                # but a healthy startup completes in <2s.
                $claimedPid = Wait-ForDaemonLock -LockPath $tcLock -LaunchPidHint $launcherPid -TimeoutSeconds 30
                if ($claimedPid -gt 0) {
                    Write-Log "  [TICK_CAP_${tsym}] STARTED - python PID ${claimedPid} (launcher PID ${launcherPid})"
                    $restarted++
                } else {
                    Write-Log "  [TICK_CAP_${tsym}] WARN - launcher PID ${launcherPid} started but python did not claim lock within 30s; will recheck next cycle"
                    $restarted++
                }
            }
        } catch {
            Write-Log "  [TICK_CAP_${tsym}] FAILED - $($_.Exception.Message)"
        }
    }
}

# --- M1 Capture Daemon (all vNext symbols, persistent) ---
# Persists closed MT5 M1 bars under data/m1/{SYMBOL}/. This is data-only:
# trading decisions remain in the orchestrators, but vNext forward
# intelligence now has a continuous LTF bar feed instead of relying only on
# M15-close records plus tick sidecars.
$m1Lock = Join-Path $LockDir ".m1_capture_all${NamespaceSuffix}.lock"
$m1Log  = Join-Path $LogDir "m1_capture.log"
$m1Pid  = Read-LockPid -Path $m1Lock
$m1Alive = ($m1Pid -gt 0) -and (Test-ProcessCommandLine -ProcessId $m1Pid -RequiredSubstrings @("src.components.m1_capture", "--profile $($env:GTOS_PROFILE)", "--runtime-namespace ${RuntimeNamespace}", "--terminal-path"))

if ($m1Alive) {
    $m1HeartbeatAge = Get-DaemonHeartbeatAgeSeconds -Name "m1_capture_all${NamespaceSuffix}"
    $m1ProgressAge = Get-DaemonProgressAgeSeconds -Name "m1_capture_all${NamespaceSuffix}"
    $m1StaleSeconds = $M1CaptureProgressStaleMinutes * 60
    if ($null -eq $m1HeartbeatAge) {
        Write-Log "  [M1_CAPTURE] STALE - PID ${m1Pid} alive but no liveness heartbeat. Restarting..."
        Stop-Process -Id $m1Pid -Force -ErrorAction SilentlyContinue
        $m1Alive = $false
    } elseif ($m1HeartbeatAge -gt $m1StaleSeconds) {
        Write-Log "  [M1_CAPTURE] STALE - PID ${m1Pid} alive but liveness heartbeat age $([math]::Round($m1HeartbeatAge, 1))s > ${m1StaleSeconds}s. Restarting..."
        Stop-Process -Id $m1Pid -Force -ErrorAction SilentlyContinue
        $m1Alive = $false
    } elseif ($null -ne $m1ProgressAge -and $m1ProgressAge -gt $m1StaleSeconds) {
        Write-Log "  [M1_CAPTURE] STALE - PID ${m1Pid} alive but data progress age $([math]::Round($m1ProgressAge, 1))s > ${m1StaleSeconds}s. Restarting..."
        Stop-Process -Id $m1Pid -Force -ErrorAction SilentlyContinue
        $m1Alive = $false
    } else {
        $m1ProgressText = if ($null -eq $m1ProgressAge) { "no data-progress timestamp" } else { "data progress age $([math]::Round($m1ProgressAge, 1))s" }
        Write-Log "  [M1_CAPTURE] OK - PID ${m1Pid} alive, liveness age $([math]::Round($m1HeartbeatAge, 1))s, ${m1ProgressText}"
        $healthy++
    }
}

if (-not $m1Alive) {
    if ($m1Pid -gt 0) {
        Write-Log "  [M1_CAPTURE] DEAD/STALE - PID ${m1Pid} requires restart..."
    } else {
        Write-Log "  [M1_CAPTURE] NOT RUNNING - Starting..."
    }
    Remove-Item $m1Lock -Force -ErrorAction SilentlyContinue
    try {
        $cmd = "cd /d ${ProjectDir} && ${PythonExe} -m src.components.m1_capture --profile $($env:GTOS_PROFILE) --runtime-namespace ${RuntimeNamespace} --terminal-path ""${TerminalPath}"" >> ""${m1Log}"" 2>&1"
        $launcherPid = Start-DetachedCommand -CommandBody $cmd -Tag "M1_CAPTURE"
        if ($launcherPid -gt 0) {
            $claimedPid = Wait-ForDaemonLock -LockPath $m1Lock -LaunchPidHint $launcherPid -TimeoutSeconds 30
            if ($claimedPid -gt 0) {
                Write-Log "  [M1_CAPTURE] STARTED - python PID ${claimedPid} (launcher PID ${launcherPid})"
                $restarted++
            } else {
                Write-Log "  [M1_CAPTURE] WARN - launcher PID ${launcherPid} started but python did not claim lock within 30s; will recheck next cycle"
                $restarted++
            }
        }
    } catch {
        Write-Log "  [M1_CAPTURE] FAILED - $($_.Exception.Message)"
    }
}

# --- Heartbeat Monitor (T1.1, persistent — restarts on death) ---
# Detects silent orchestrator crashes; flattens open positions only when
# config.heartbeat.flatten_enabled=true (ships DISABLED, log-only).
$hbLock = Join-Path $LockDir ".heartbeat_monitor.lock"
$hbLog  = Join-Path $LogDir "heartbeat_monitor.log"
$hbPid  = Read-LockPid -Path $hbLock
$hbAlive = ($hbPid -gt 0) -and (Test-ProcessCommandLine -ProcessId $hbPid -RequiredSubstrings @("src.safety.heartbeat_monitor"))

if ($hbAlive) {
    Write-Log "  [HEARTBEAT] OK - PID ${hbPid} alive"
    $healthy++
} else {
    if ($hbPid -gt 0) {
        Write-Log "  [HEARTBEAT] DEAD - PID ${hbPid} gone. Restarting..."
    } else {
        Write-Log "  [HEARTBEAT] NOT RUNNING - Starting..."
    }
    Remove-Item $hbLock -Force -ErrorAction SilentlyContinue
    try {
        $cmd = "cd /d ${ProjectDir} && ${PythonExe} -m src.safety.heartbeat_monitor >> ""${hbLog}"" 2>&1"
        $launcherPid = Start-DetachedCommand -CommandBody $cmd -Tag "HEARTBEAT"
        if ($launcherPid -gt 0) {
            $claimedPid = Wait-ForDaemonLock -LockPath $hbLock -LaunchPidHint $launcherPid -TimeoutSeconds 30
            if ($claimedPid -gt 0) {
                Write-Log "  [HEARTBEAT] STARTED - python PID ${claimedPid} (launcher PID ${launcherPid})"
                $restarted++
            } else {
                Write-Log "  [HEARTBEAT] WARN - launcher PID ${launcherPid} started but python did not claim lock within 30s; will recheck next cycle"
                $restarted++
            }
        }
    } catch {
        Write-Log "  [HEARTBEAT] FAILED - $($_.Exception.Message)"
    }
}

# --- Notification Queue Worker (2026-04-28, persistent — restarts on death) ---
# Drains the account-scoped notification queue forever. Producers (cron
# scripts + orchestrators) only append rows; this worker is the authoritative
# Telegram dispatcher. Pre-2026-04-28 the queue was drained by a daemon
# thread lazily started inside whichever process happened to call
# notify_alert(); short-lived cron scripts (correlation_shock_monitor,
# api_refusal_monitor, no_data_alert_monitor) exited before the daemon
# thread polled, leaving HIGH alerts undelivered with retry_count=0. The
# worker process closes that gap.
$nqLock = Join-Path $LockDir $NotificationQueueLockName
$nqLog  = Join-Path $LogDir "notification_queue_worker.log"
$nqAlive = $false
$nqPid   = 0

if (Test-Path $nqLock) {
    try {
        $nqPid = [int](Get-Content $nqLock -Raw).Trim()
        $nqAlive = Test-ProcessCommandLine -ProcessId $nqPid -RequiredSubstrings @("src.utils.notification_queue", "--worker", "--queue-path", $NotificationQueuePath, "--runtime-namespace ${RuntimeNamespace}")
    } catch {
        $nqAlive = $false
    }
}

if ($nqAlive) {
    Write-Log "  [NOTIFICATION_QUEUE] OK - PID ${nqPid} alive"
    $healthy++
} else {
    Write-Log "  [NOTIFICATION_QUEUE] NOT RUNNING - Starting..."
    Remove-Item $nqLock -Force -ErrorAction SilentlyContinue
    try {
        $cmd = "cd /d ${ProjectDir} && ${PythonExe} -m src.utils.notification_queue --worker --queue-path ""${NotificationQueuePath}"" --runtime-namespace ${RuntimeNamespace} >> ""${nqLog}"" 2>&1"
        $launcherPid = Start-DetachedCommand -CommandBody $cmd -Tag "NOTIFICATION_QUEUE"
        if ($launcherPid -gt 0) {
            $claimedPid = Wait-ForDaemonLock -LockPath $nqLock -LaunchPidHint $launcherPid -TimeoutSeconds 30
            if ($claimedPid -gt 0) {
                Write-Log "  [NOTIFICATION_QUEUE] STARTED - python PID ${claimedPid} (launcher PID ${launcherPid})"
                $restarted++
            } else {
                Write-Log "  [NOTIFICATION_QUEUE] WARNING - launch PID ${launcherPid}; no live worker lock after 30s"
            }
        } else {
            Write-Log "  [NOTIFICATION_QUEUE] FAILED - detached launch returned no PID"
        }
    } catch {
        Write-Log "  [NOTIFICATION_QUEUE] FAILED - $($_.Exception.Message)"
    }
}

# --- Dual-Broker Bridge/Follower (lightweight secondary execution surface) ---
Invoke-DualBrokerTradeRecordProjectorBridge | Out-Null
Invoke-DualBrokerExecutionFollowerBridge | Out-Null

# --- API Refusal Monitor (non-blocking, fire and check exit code) ---
try {
    $refusalScript = Join-Path $ProjectDir "scripts\api_refusal_monitor.py"
    $refusalLog = Join-Path $LogDir "api_refusal_monitor.log"
    $monArgs = "/c cd /d ${ProjectDir} && ${PythonExe} ${refusalScript} >> ""${refusalLog}"" 2>&1"
    $monPsi = New-Object System.Diagnostics.ProcessStartInfo
    $monPsi.FileName = "cmd.exe"
    $monPsi.Arguments = $monArgs
    $monPsi.WindowStyle = [System.Diagnostics.ProcessWindowStyle]::Hidden
    $monPsi.CreateNoWindow = $true
    $monProc = [System.Diagnostics.Process]::Start($monPsi)
    if ($null -ne $monProc) {
        $monProc.WaitForExit(30000)
        $monExit = $monProc.ExitCode
        if ($monExit -eq 0) {
            Write-Log "  [API_REFUSAL] OK"
        } elseif ($monExit -eq 1) {
            Write-Log "  [API_REFUSAL] Alert needed but Telegram creds missing"
        } elseif ($monExit -eq 2) {
            Write-Log "  [API_REFUSAL] Telegram HTTP failed"
        } else {
            Write-Log "  [API_REFUSAL] exit=${monExit}"
        }
    }
} catch {
    Write-Log "  [API_REFUSAL] FAILED - $($_.Exception.Message)"
}

# --- No-Data Alert Monitor (T1.7, per-symbol tick-liveness check) ---
# Fires Telegram alert if a symbol's log file stops updating during its KZ.
# Closes the gap between API monitoring, between-KZ pending-limit monitoring,
# and heartbeat-flatten monitors — this one is
# per-symbol, log-mtime based, and KZ-gated.
try {
    $noDataScript = Join-Path $ProjectDir "scripts\no_data_alert_monitor.py"
    $noDataLog    = Join-Path $LogDir "no_data_alert_monitor.log"
    $ndArgs = "/c cd /d ${ProjectDir} && ${PythonExe} ${noDataScript} >> ""${noDataLog}"" 2>&1"
    $ndPsi = New-Object System.Diagnostics.ProcessStartInfo
    $ndPsi.FileName = "cmd.exe"
    $ndPsi.Arguments = $ndArgs
    $ndPsi.WindowStyle = [System.Diagnostics.ProcessWindowStyle]::Hidden
    $ndPsi.CreateNoWindow = $true
    $ndProc = [System.Diagnostics.Process]::Start($ndPsi)
    if ($null -ne $ndProc) {
        $ndProc.WaitForExit(30000)
        $ndExit = $ndProc.ExitCode
        if ($ndExit -eq 0) {
            Write-Log "  [NO_DATA] OK"
        } elseif ($ndExit -eq 1) {
            Write-Log "  [NO_DATA] Alert needed but Telegram creds missing"
        } elseif ($ndExit -eq 2) {
            Write-Log "  [NO_DATA] Telegram HTTP failed"
        } else {
            Write-Log "  [NO_DATA] exit=${ndExit}"
        }
    }
} catch {
    Write-Log "  [NO_DATA] FAILED - $($_.Exception.Message)"
}

# --- OB Continuation Monitor (once per UTC day, fire and check exit code) ---
try {
    $obMarkerFile = Join-Path $LockDir "ob_continuation_last_run.utcdate"
    $obTodayUtc   = (Get-Date).ToUniversalTime().ToString("yyyy-MM-dd")
    $obShouldRun  = $true
    if (Test-Path $obMarkerFile) {
        $obLastRun = (Get-Content $obMarkerFile -Raw -ErrorAction SilentlyContinue)
        if ($null -ne $obLastRun) {
            $obLastRun = $obLastRun.Trim()
            if ($obLastRun -eq $obTodayUtc) { $obShouldRun = $false }
        }
    }
    if ($obShouldRun) {
        $obScript = Join-Path $ProjectDir "scripts\ob_continuation_monitor.py"
        $obLog    = Join-Path $LogDir "ob_continuation.log"
        $obArgs   = "/c cd /d ${ProjectDir} && ${PythonExe} ${obScript} >> ""${obLog}"" 2>&1"
        $obPsi    = New-Object System.Diagnostics.ProcessStartInfo
        $obPsi.FileName       = "cmd.exe"
        $obPsi.Arguments      = $obArgs
        $obPsi.WindowStyle    = [System.Diagnostics.ProcessWindowStyle]::Hidden
        $obPsi.CreateNoWindow = $true
        $obProc = [System.Diagnostics.Process]::Start($obPsi)
        if ($null -ne $obProc) {
            $obCompleted = $obProc.WaitForExit(120000)
            if (-not $obCompleted) {
                try { $obProc.Kill() } catch {}
                Write-Log "  [OB_MONITOR] TIMEOUT - killed after 120s, retry next heartbeat"
            } else {
                $obExit = $obProc.ExitCode
                if ($obExit -eq 0) {
                    Write-Log "  [OB_MONITOR] OK"
                    $obTodayUtc | Set-Content -Path $obMarkerFile -Encoding UTF8
                } elseif ($obExit -eq 1) {
                    Write-Log "  [OB_MONITOR] ALARM - see shadow_logs/ob_continuation_daily.csv"
                    $obTodayUtc | Set-Content -Path $obMarkerFile -Encoding UTF8
                } elseif ($obExit -eq 2) {
                    Write-Log "  [OB_MONITOR] FAILED - exit=2, retry next heartbeat"
                } else {
                    Write-Log "  [OB_MONITOR] UNEXPECTED exit=${obExit}"
                }
            }
        } else {
            Write-Log "  [OB_MONITOR] FAILED - Process.Start returned null"
        }
    }
} catch {
    Write-Log "  [OB_MONITOR] FAILED - $($_.Exception.Message)"
}

# --- LTO-022 Session-volatility / sweep status audit (once per UTC day) ---
# Pure CSV/status audit. It appends explicit no-event rows for the previous UTC
# date when the H25/H16 monitor lanes are quiet, then writes a JSONL status row
# so missing CSV rows are not confused with no-event sessions.
try {
    $svsMarkerFile = Join-Path $LockDir "session_volatility_sweep_status_last_run.utcdate"
    $svsTodayUtc   = (Get-Date).ToUniversalTime().ToString("yyyy-MM-dd")
    $svsShouldRun  = $true
    if (Test-Path $svsMarkerFile) {
        $svsLastRun = (Get-Content $svsMarkerFile -Raw -ErrorAction SilentlyContinue)
        if ($null -ne $svsLastRun) {
            $svsLastRun = $svsLastRun.Trim()
            if ($svsLastRun -eq $svsTodayUtc) { $svsShouldRun = $false }
        }
    }
    if ($svsShouldRun) {
        $svsScript = Join-Path $ProjectDir "scripts\audit_session_volatility_sweep_status.py"
        $svsLog    = Join-Path $LogDir "session_volatility_sweep_status.log"
        $svsArgs   = "/c cd /d ${ProjectDir} && ${PythonExe} ${svsScript} >> ""${svsLog}"" 2>&1"
        $svsPsi    = New-Object System.Diagnostics.ProcessStartInfo
        $svsPsi.FileName       = "cmd.exe"
        $svsPsi.Arguments      = $svsArgs
        $svsPsi.WindowStyle    = [System.Diagnostics.ProcessWindowStyle]::Hidden
        $svsPsi.CreateNoWindow = $true
        $svsProc = [System.Diagnostics.Process]::Start($svsPsi)
        if ($null -ne $svsProc) {
            $svsCompleted = $svsProc.WaitForExit(60000)
            if (-not $svsCompleted) {
                try { $svsProc.Kill() } catch {}
                Write-Log "  [SESSION_VOL_SWEEP] TIMEOUT - killed after 60s, retry next heartbeat"
            } else {
                $svsExit = $svsProc.ExitCode
                if ($svsExit -eq 0) {
                    Write-Log "  [SESSION_VOL_SWEEP] OK"
                    $svsTodayUtc | Set-Content -Path $svsMarkerFile -Encoding UTF8
                } elseif ($svsExit -eq 1) {
                    Write-Log "  [SESSION_VOL_SWEEP] ACTION_REQUIRED - see research/program_control/LTO022_SESSION_VOLATILITY_SWEEP_STATUS_2026-05-05.md"
                } else {
                    Write-Log "  [SESSION_VOL_SWEEP] UNEXPECTED exit=${svsExit}"
                }
            }
        } else {
            Write-Log "  [SESSION_VOL_SWEEP] FAILED - Process.Start returned null"
        }
    }
} catch {
    Write-Log "  [SESSION_VOL_SWEEP] FAILED - $($_.Exception.Message)"
}

# --- LTO-037 Notification queue dead-zone status audit (once per UTC day) ---
# Pure status audit. It classifies the queue worker as RUNNING, expected
# dead-zone-stopped, or unexpectedly stopped during an active window; it never
# sends notifications or starts workers. Off-hours cleanup invokes the same
# audit without the daily marker so expected dead-zone stop rows are captured.
Invoke-NotificationQueueDeadZoneAudit -Tag "NOTIFICATION_DEAD_ZONE" -UseDailyMarker $true
Invoke-StorageRetentionAudit -Tag "STORAGE_RETENTION"
Invoke-LiveMonitoringMaintenance -Tag "LIVE_MAINTENANCE"

# --- CUSUM on CANDIDATE rate (T1.5, once per UTC day, fire and check exit code) ---
try {
    $crMarkerFile = Join-Path $LockDir "cusum_candidate_rate_last_run.utcdate"
    $crTodayUtc   = (Get-Date).ToUniversalTime().ToString("yyyy-MM-dd")
    $crShouldRun  = $true
    if (Test-Path $crMarkerFile) {
        $crLastRun = (Get-Content $crMarkerFile -Raw -ErrorAction SilentlyContinue)
        if ($null -ne $crLastRun) {
            $crLastRun = $crLastRun.Trim()
            if ($crLastRun -eq $crTodayUtc) { $crShouldRun = $false }
        }
    }
    if ($crShouldRun) {
        $crScript = Join-Path $ProjectDir "scripts\cusum_candidate_rate_monitor.py"
        $crLog    = Join-Path $LogDir "cusum_candidate_rate.log"
        $crArgs   = "/c cd /d ${ProjectDir} && ${PythonExe} ${crScript} >> ""${crLog}"" 2>&1"
        $crPsi    = New-Object System.Diagnostics.ProcessStartInfo
        $crPsi.FileName       = "cmd.exe"
        $crPsi.Arguments      = $crArgs
        $crPsi.WindowStyle    = [System.Diagnostics.ProcessWindowStyle]::Hidden
        $crPsi.CreateNoWindow = $true
        $crProc = [System.Diagnostics.Process]::Start($crPsi)
        if ($null -ne $crProc) {
            $crCompleted = $crProc.WaitForExit(60000)
            if (-not $crCompleted) {
                try { $crProc.Kill() } catch {}
                Write-Log "  [CUSUM_CR] TIMEOUT - killed after 60s, retry next heartbeat"
            } else {
                $crExit = $crProc.ExitCode
                if ($crExit -eq 0) {
                    Write-Log "  [CUSUM_CR] OK"
                    $crTodayUtc | Set-Content -Path $crMarkerFile -Encoding UTF8
                } elseif ($crExit -eq 1) {
                    Write-Log "  [CUSUM_CR] ALARM - see shadow_logs/cusum_candidate_rate_daily.csv"
                    $crTodayUtc | Set-Content -Path $crMarkerFile -Encoding UTF8
                } elseif ($crExit -eq 2) {
                    Write-Log "  [CUSUM_CR] FAILED - exit=2, retry next heartbeat"
                } else {
                    Write-Log "  [CUSUM_CR] UNEXPECTED exit=${crExit}"
                }
            }
        } else {
            Write-Log "  [CUSUM_CR] FAILED - Process.Start returned null"
        }
    }
} catch {
    Write-Log "  [CUSUM_CR] FAILED - $($_.Exception.Message)"
}

# --- Correlation Shock Monitor (T1.6, once per UTC day, fire and check exit code) ---
# Rolling-50 Pearson on M15 returns across portfolio_risk correlation groups.
# Telegram-only alert; never touches positions.
try {
    $csMarkerFile = Join-Path $LockDir "correlation_shock_last_run.utcdate"
    $csTodayUtc   = (Get-Date).ToUniversalTime().ToString("yyyy-MM-dd")
    $csShouldRun  = $true
    if (Test-Path $csMarkerFile) {
        $csLastRun = (Get-Content $csMarkerFile -Raw -ErrorAction SilentlyContinue)
        if ($null -ne $csLastRun) {
            $csLastRun = $csLastRun.Trim()
            if ($csLastRun -eq $csTodayUtc) { $csShouldRun = $false }
        }
    }
    if ($csShouldRun) {
        $csScript = Join-Path $ProjectDir "scripts\correlation_shock_monitor.py"
        $csLog    = Join-Path $LogDir "correlation_shock.log"
        $csArgs   = "/c cd /d ${ProjectDir} && ${PythonExe} ${csScript} >> ""${csLog}"" 2>&1"
        $csPsi    = New-Object System.Diagnostics.ProcessStartInfo
        $csPsi.FileName       = "cmd.exe"
        $csPsi.Arguments      = $csArgs
        $csPsi.WindowStyle    = [System.Diagnostics.ProcessWindowStyle]::Hidden
        $csPsi.CreateNoWindow = $true
        $csProc = [System.Diagnostics.Process]::Start($csPsi)
        if ($null -ne $csProc) {
            $csCompleted = $csProc.WaitForExit(60000)
            if (-not $csCompleted) {
                try { $csProc.Kill() } catch {}
                Write-Log "  [CORR_SHOCK] TIMEOUT - killed after 60s, retry next heartbeat"
            } else {
                $csExit = $csProc.ExitCode
                if ($csExit -eq 0) {
                    Write-Log "  [CORR_SHOCK] OK"
                    $csTodayUtc | Set-Content -Path $csMarkerFile -Encoding UTF8
                } elseif ($csExit -eq 1) {
                    Write-Log "  [CORR_SHOCK] ALARM - alert enqueued (worker dispatches asynchronously; see correlation_shock.log)"
                    $csTodayUtc | Set-Content -Path $csMarkerFile -Encoding UTF8
                } elseif ($csExit -eq 2) {
                    Write-Log "  [CORR_SHOCK] FAILED - exit=2, retry next heartbeat"
                } else {
                    Write-Log "  [CORR_SHOCK] UNEXPECTED exit=${csExit}"
                }
            }
        } else {
            Write-Log "  [CORR_SHOCK] FAILED - Process.Start returned null"
        }
    }
} catch {
    Write-Log "  [CORR_SHOCK] FAILED - $($_.Exception.Message)"
}

# --- Monthly Decay Shadow Monitor (once per UTC Monday, fire and check exit code) ---
# Detects edge decay at month/week granularity (complement to OB continuation
# which is rolling-50 trades). Fires rc=1 when a HIGH alert triggers (WR drop
# >15pp, Exp drop >0.25R, or 3 consecutive weeks <breakeven). CEO reviews
# the generated markdown report under research/monthly_decay_monitor/.
#
# Gated DISABLED by default — the CEO enables this block manually after
# reviewing the first few weeks of live trade data post-FTMO-paid-challenge
# (Monday 2026-04-27 onward). Remove the "if ($false)" guard to enable.
if ($false) {
    try {
        $mdMarkerFile = Join-Path $LockDir "monthly_decay_last_run.utcweek"
        $mdTodayUtc   = (Get-Date).ToUniversalTime()
        # ISO 8601 week string (YYYY-WNN).
        $mdCulture    = [System.Globalization.CultureInfo]::InvariantCulture
        $mdRules      = [System.Globalization.CalendarWeekRule]::FirstFourDayWeek
        $mdWeek       = $mdCulture.Calendar.GetWeekOfYear($mdTodayUtc, $mdRules, [DayOfWeek]::Monday)
        $mdWeekKey    = "{0}-W{1:D2}" -f $mdTodayUtc.Year, $mdWeek
        $mdShouldRun  = $true
        # Only run on Monday (day-of-week 1 in ISO).
        if ($mdTodayUtc.DayOfWeek -ne [DayOfWeek]::Monday) { $mdShouldRun = $false }
        if ($mdShouldRun -and (Test-Path $mdMarkerFile)) {
            $mdLastRun = (Get-Content $mdMarkerFile -Raw -ErrorAction SilentlyContinue)
            if ($null -ne $mdLastRun) {
                $mdLastRun = $mdLastRun.Trim()
                if ($mdLastRun -eq $mdWeekKey) { $mdShouldRun = $false }
            }
        }
        if ($mdShouldRun) {
            $mdScript = Join-Path $ProjectDir "scripts\monthly_decay_monitor.py"
            $mdLog    = Join-Path $LogDir "monthly_decay.log"
            $mdYM     = "{0}-{1:D2}" -f $mdTodayUtc.Year, $mdTodayUtc.Month
            $mdOut    = Join-Path $ProjectDir ("research\monthly_decay_monitor\" + $mdYM + "_report.md")
            $mdArgs   = "/c cd /d ${ProjectDir} && ${PythonExe} ${mdScript} --output ""${mdOut}"" >> ""${mdLog}"" 2>&1"
            $mdPsi    = New-Object System.Diagnostics.ProcessStartInfo
            $mdPsi.FileName       = "cmd.exe"
            $mdPsi.Arguments      = $mdArgs
            $mdPsi.WindowStyle    = [System.Diagnostics.ProcessWindowStyle]::Hidden
            $mdPsi.CreateNoWindow = $true
            $mdProc = [System.Diagnostics.Process]::Start($mdPsi)
            if ($null -ne $mdProc) {
                $mdCompleted = $mdProc.WaitForExit(120000)
                if (-not $mdCompleted) {
                    try { $mdProc.Kill() } catch {}
                    Write-Log "  [MONTHLY_DECAY] TIMEOUT - killed after 120s, retry next Monday"
                } else {
                    $mdExit = $mdProc.ExitCode
                    if ($mdExit -eq 0) {
                        Write-Log "  [MONTHLY_DECAY] OK - no alerts ($mdOut)"
                        $mdWeekKey | Set-Content -Path $mdMarkerFile -Encoding UTF8
                    } elseif ($mdExit -eq 1) {
                        Write-Log "  [MONTHLY_DECAY] ALARM - HIGH alert(s) raised, see $mdOut"
                        $mdWeekKey | Set-Content -Path $mdMarkerFile -Encoding UTF8
                    } else {
                        Write-Log "  [MONTHLY_DECAY] UNEXPECTED exit=${mdExit}"
                    }
                }
            } else {
                Write-Log "  [MONTHLY_DECAY] FAILED - Process.Start returned null"
            }
        }
    } catch {
        Write-Log "  [MONTHLY_DECAY] FAILED - $($_.Exception.Message)"
    }
}

# --- Economic-Calendar Staleness Monitor (Issue #15, 2026-04-28; refactored 2026-04-29) ---
# Daily check on data/news_calendar.json + data/economic_calendar.csv age.
# Routes Telegram alert through the persistent notification queue (HIGH
# priority), not direct urllib — the live host has a self-signed cert in
# its trust store that breaks direct SSL verification, so direct urllib
# always returned [SSL: CERTIFICATE_VERIFY_FAILED] and the alert never
# reached the operator. The queue's _default_transport bypasses this.
# DOES NOT auto-fetch data — calendar is operator-maintained per CLAUDE.md.
# Cooldown of 24h baked into the script's state file. Once-per-UTC-day
# marker pattern matches OB_MONITOR / CUSUM_CR / CORR_SHOCK above.
#
# Same helper is also called from the OUTSIDE-TRADING-HOURS branch above so
# Sunday + dead-zone wakeups still fire the staleness check.
Invoke-CalendarStalenessHook -Tag "CAL_STALE"

Write-Log ("=== Watchdog complete: {0} healthy, {1} restarted ===" -f $healthy, $restarted)
