# gtos_token_verify_probe.ps1 â€” scheduled verify of the three activation
# bindings. STAGED â€” this file deploys nothing, registers nothing, mints
# nothing, and never writes a token. The orchestrator carries it at
# tonight's blossom restart ceremony.
#
# WHY (2026-08-18, TOKEN-DIGEST-INCIDENT): F5 ran digest-dead for ~3 days
# (129 refusals mislabeled timeout_no_fill); both production tokens were
# digest-dead vs the 08-13 cluster-envelope config edit that skipped the
# remint. Third silent-gate class incident. A 6-hour verify pages a
# mismatch within hours instead of a forensic dig within days.
#
# WHAT IT DOES, once per invocation:
#   1. Reads the RUNNING operator worker CommandLine (CIM). Launch-
#      contract args come from that argv so a future --tags ceremony cannot
#      silently break the probe's basis. If argv is unreadable: the Python
#      engine emits UNKNOWN and we alert â€” we do not guess tags.
#   2. Optionally reads the two production worker CommandLines (namespace /
#      repo discovery only; prod verifies are config-only).
#   3. Calls scripts/gtos_token_verify_probe.py (read-only verify_token).
#   4. Python appends one JSONL row; on any valid:false / UNKNOWN it sends
#      ONE alert through the monitor_books notifier path.
#
# WHAT IT WILL NEVER DO: mint, revoke, rewrite, or delete a token; start,
# stop, or restart a book; edit config; register a scheduled task; invent
# --tags / --f5-minimal-size-usd from a ceremony pack.
#
# PRIOR ART: scripts/f5_keepalive_watchdog.ps1 (CIM CommandLine, word-
# bounded namespace, $PSScriptRoot-empty fallback) and
# .tools/monitor_books.py:send (the alert path).
#
# =============================== DEPLOY-NOTE (tonight's ceremony) ===============================
# STAGED ONLY. Do not run Register-ScheduledTask from this file. The
# orchestrator carries the probe at the blossom restart (F5 host first).
# Production books are verified read-only against their own token dir +
# config; they are not restarted for this probe.
#
#  0. Confirm host paths (2026-08-18 known; VERIFY before first fire):
#        F5  repo      host-local\redacted_host\repo
#        F5  token dir host-local\.gtos\activation-f5
#        Prod repo     C:\Users\MSI\Documents\ai-trading-agent
#                      (override -ProdRepo if the running FTMO worker's
#                      CommandLine names a different tree)
#        Prod token    host-local\.gtos\activation
#
#  1. Carry these files onto the F5 tree (checkout from tonight's tip,
#     leave dirty config/agent_config.yaml alone):
#        scripts/gtos_token_verify_probe.ps1
#        scripts/gtos_token_verify_probe.py
#        scripts/gtos_token_verify_probe_task.xml
#
#  2. DRY-RUN once by hand (no alert, still writes the JSONL row):
#        powershell -ExecutionPolicy Bypass -File `
#          host-local\redacted_host\repo\scripts\gtos_token_verify_probe.ps1 -DryRun
#     Read shadow_logs\token_verify_probe.jsonl. F5 row must not be UNKNOWN
#     if the worker is up. valid:true is log-only; valid:false / UNKNOWN
#     would have alerted without -DryRun.
#
#  3. REGISTER (orchestrator only; 6 h; IgnoreNew; no mint rights needed):
#        $script = "host-local\redacted_host\repo\scripts\gtos_token_verify_probe.ps1"
#        $act = New-ScheduledTaskAction -Execute "powershell.exe" -Argument `
#          "-NoProfile -ExecutionPolicy Bypass -File `"$script`""
#        $trg = New-ScheduledTaskTrigger -Once -At (Get-Date) `
#                 -RepetitionInterval (New-TimeSpan -Hours 6)
#        $set = New-ScheduledTaskSettingsSet `
#                 -ExecutionTimeLimit (New-TimeSpan -Minutes 10) `
#                 -MultipleInstances IgnoreNew `
#                 -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries `
#                 -StartWhenAvailable
#        Register-ScheduledTask -TaskName GTOS_TOKEN_VERIFY_PROBE `
#          -Action $act -Trigger $trg -Settings $set `
#          -Description "Read-only 6h verify of F5+prod activation tokens; never mints"
#
#     Equivalent XML (not imported by this script): 
#     scripts/gtos_token_verify_probe_task.xml
#
#  4. ROLLBACK: Unregister-ScheduledTask GTOS_TOKEN_VERIFY_PROBE. Tokens,
#     configs, and books are untouched. The JSONL log stays.
# ============================================================================================

[CmdletBinding()]
param(
    [switch]$DryRun,
    [string]$F5Repo = $(
        if ($PSScriptRoot) { Split-Path -Parent $PSScriptRoot }
        elseif ($MyInvocation.MyCommand.Path) { Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path) }
        else { "host-local\redacted_host\repo" }
    ),
    [string]$ProdRepo = "C:\Users\MSI\Documents\ai-trading-agent",
    [string]$F5TokenDir = "host-local\.gtos\activation-f5",
    [string]$ProdTokenDir = "host-local\.gtos\activation",
    [string]$F5Namespace = "operator",
    [string]$ProdFtmoNamespace = "operator_profile",
    [string]$ProdFnNamespace = "redacted_account_live_bee34003",
    [string]$Python = ""
)

$ErrorActionPreference = "Continue"
$VERSION = "gtos_token_verify_probe_v1"

function Get-WorkerCommandLine([string]$Namespace) {
    $nsPattern = "--namespace\s+{0}(\s|$)" -f [regex]::Escape($Namespace)
    $matches = @(Get-CimInstance Win32_Process -Filter "Name='python.exe'" -ErrorAction SilentlyContinue |
        Where-Object {
            $_.CommandLine -and
            $_.CommandLine -match 'run_book\.py' -and
            $_.CommandLine -match $nsPattern
        })
    if ($matches.Count -eq 0) { return $null }
    # Prefer a CommandLine that actually carries run_book.py as a token;
    # launcher+child both match, either is fine â€” they share argv.
    return [string]$matches[0].CommandLine
}

function Resolve-Python([string]$Repo) {
    if ($Python -and (Test-Path -LiteralPath $Python)) { return $Python }
    $candidates = @(
        (Get-Command python.exe -ErrorAction SilentlyContinue | Select-Object -ExpandProperty Source),
        "host-local\AppData\Local\Programs\Python\Python312\python.exe",
        "C:\Python312\python.exe"
    )
    foreach ($c in $candidates) {
        if ($c -and (Test-Path -LiteralPath $c)) { return $c }
    }
    return "python.exe"
}

$f5Cl   = Get-WorkerCommandLine $F5Namespace
$ftmoCl = Get-WorkerCommandLine $ProdFtmoNamespace
$fnCl   = Get-WorkerCommandLine $ProdFnNamespace
$py     = Resolve-Python $F5Repo
$engine = Join-Path $F5Repo "scripts\gtos_token_verify_probe.py"

if (-not (Test-Path -LiteralPath $engine)) {
    Write-Error "probe engine missing: $engine (staged file not carried?)"
    exit 2
}

# Task XML historically omitted WorkingDirectory (Task Scheduler then
# uses System32). Relative notification_queue.jsonl must bind the F5
# tree, not System32. Engine also pins the queue path; this is the
# wrapper belt.
Set-Location -LiteralPath $F5Repo

$argv = @(
    $engine,
    "--f5-token-dir", $F5TokenDir,
    "--f5-repo", $F5Repo,
    "--prod-token-dir", $ProdTokenDir,
    "--prod-repo", $ProdRepo
)
if ($f5Cl)   { $argv += @("--f5-command-line", $f5Cl) }
if ($ftmoCl) { $argv += @("--prod-ftmo-command-line", $ftmoCl) }
if ($fnCl)   { $argv += @("--prod-fn-command-line", $fnCl) }
if ($DryRun) { $argv += "--dry-run" }

# Empty F5 CommandLine is deliberate: the engine then emits UNKNOWN
# instead of guessing tags. Do not substitute a ceremony pack here.
Write-Output ("{0} {1} f5_argv_present={2} dry_run={3}" -f (Get-Date).ToUniversalTime().ToString("o"), $VERSION, [bool]$f5Cl, [bool]$DryRun)
& $py @argv
exit $LASTEXITCODE

