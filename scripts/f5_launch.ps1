# F5 launcher.
# Contract fields pass through. A missing field stays empty.
$ErrorActionPreference = 'Stop'
$F5   = 'host-local\redacted_host\repo'
$PY   = 'C:\Users\MSI\Documents\ai-trading-agent\.venv-gtos\Scripts\python.exe'
$CONTRACT = 'host-local\redacted_host\launch_contracts\operator.json'

$TAGS = $null
$FLOOR_MODE = $null
$SIZE = $null
$NOTIONAL = $null
$FRIDAY = $null
$WEEKEND_FLAT = $null
$RETRY = $null
$POLL = $null
$NAMESPACE = $null
$PROFILE = $null
$TERMINAL = $null

function ConvertTo-LaunchFact {
  param($Value)
  if ($null -eq $Value) { return $null }
  $text = [string]$Value
  if ($text.Length -eq 0) { return $null }
  return $text
}

$c = $null
if (Test-Path -LiteralPath $CONTRACT) {
  $c = Get-Content -LiteralPath $CONTRACT -Raw -Encoding UTF8 | ConvertFrom-Json
  $bound = $c.token_bound
  $argvBound = $c.argv_bound
  if ($bound) {
    $TAGS = ConvertTo-LaunchFact $bound.selected_tags_csv
    $FLOOR_MODE = ConvertTo-LaunchFact $bound.q1_mode
    $SIZE = ConvertTo-LaunchFact $bound.f5_minimal_size_usd
    $NOTIONAL = ConvertTo-LaunchFact $bound.f5_notional_initial_usd
  }
  if ($argvBound) {
    $FRIDAY = ConvertTo-LaunchFact $argvBound.f5_friday_new_risk_cutoff_utc
    $WEEKEND_FLAT = ConvertTo-LaunchFact $argvBound.f5_weekend_flat_utc
    $RETRY = ConvertTo-LaunchFact $argvBound.transient_retry_cap
    $POLL = ConvertTo-LaunchFact $argvBound.poll_seconds
  }
  $NAMESPACE = ConvertTo-LaunchFact $c.namespace
  $PROFILE = ConvertTo-LaunchFact $c.profile
  $TERMINAL = ConvertTo-LaunchFact $c.terminal_path
}

$FLAG = Join-Path $F5 'pipeline_state\ULTIMATE_BOOK_KILL_ftmo_f5.flag'
$LOG  = Join-Path $F5 'shadow_logs\f5_verification.log'
$tokenDir = $null
if ($c) { $tokenDir = ConvertTo-LaunchFact $c.token_dir }
if ($tokenDir) { $env:GTOS_ACTIVATION_TOKEN_DIR = $tokenDir }
$env:GTOS_PROFILE = $null
# Jev Alive + Policy C APPLY — Challenge f5-live ONLY. Do not set on W7/FN.
$env:GTOS_JEV_MAX_CALLS = "500000"
$env:GTOS_JEV_ALIVE_SHADOW = "1"
$env:GTOS_JEV_APPLY_LIVE = "1"
$env:GTOS_JEV_FLUID_GATES_SHADOW = "1"
$env:GTOS_JEV_SLEEVE_SELECT_SHADOW = '1'

$env:GTOS_JEV_FLUID_GATES_APPLY = "1"
$env:GTOS_JEV_POLICY_C_APPLY = "1"
$env:GTOS_JEV_POLICY_C_SHADOW_EVAL = "1"
$env:GTOS_JEV_PLACE_APPLY = "1"
$env:GTOS_JEV_DIG_C_SHADOW = "1"
$env:GTOS_JEV_DIG_C_APPLY = "1"
$env:GTOS_JEV_FANOUT_DEDUP = "1"
$env:GTOS_JEV_TRAIN_HARVEST_SHADOW = "1"
$env:GTOS_JEV_TRAIN_HARVEST_CALL = "1"
$env:GTOS_JEV_CONF_ORDER_CONSUME = "1"

$env:GTOS_JEV_PLACE_ENSEMBLE = "1"  # Owner unlock 20260921 place/remint/flatten Choice
$env:GTOS_JEV_EVERYWHERE_SHADOW = "1"
$env:GTOS_JEV_A1_LOG = "1"
$env:GTOS_JEV_A1_OBSERVE_EVERY = "1"
# Owner 2026-09-21 all-the-way: measured rungs already on host. Persist 0.00.
# Missing key still fail-closed. Friend feedback LABEL never places.
$env:GTOS_JEV_ISOLATED_15M_REENTRY = "1"
$env:GTOS_JEV_DAILY_LOOP = "1"
$env:GTOS_JEV_COMMAND_CENTER = "1"
$env:GTOS_JEV_HIST_APPLY = "1"
$env:GTOS_JEV_REMAINING_IFS = "1"
$env:GTOS_JEV_FRIEND_FEEDBACK = "1"
$env:GTOS_JEV_LEARN_LOOP = "1"
$env:GTOS_JEV_TRAINED_MODELS = "1"
$env:GTOS_JEV_X_DIG = "1"
$env:GTOS_JEV_GOLD_SLEEVE = "1"
$env:GTOS_JEV_EXEC_GOV_NEWS = "1"
$env:GTOS_JEV_SLEEVE_SELECT_LIVE = "1"
$env:GTOS_JEV_CA_SIZE_APPLY = "1"  # Chair APPLY 2026-09-21 ca_size hist
$env:GTOS_JEV_FEATURE_LABEL_STORE = "1"
# Prefer Admin judgment + sleeves on PYTHONPATH
$env:PYTHONPATH = $F5

Set-Location $F5
New-Item -ItemType Directory -Force -Path (Split-Path $LOG) | Out-Null
$ErrorActionPreference = 'Continue'
$a = @('run_book.py')
if ($TERMINAL) {
  $a += @('--terminal-path', $TERMINAL)
}
if ($NAMESPACE) {
  $a += @('--namespace', $NAMESPACE)
}
if ($PROFILE) {
  $a += @('--profile', $PROFILE)
}
$a += @('--kill-flag', $FLAG)
if ($TAGS) {
  $a += @('--tags', $TAGS)
}
if ($FLOOR_MODE) {
  $a += @('--risk-unit-floor-mode', $FLOOR_MODE)
}
if ($TAGS) {
  $a += @('--risk-unit-floor', $TAGS)
}
$a += '--event-clock-shadow'
if ($SIZE) {
  $a += @('--f5-minimal-size-usd', $SIZE)
}
if ($NOTIONAL) {
  $a += @('--f5-notional-initial-usd', $NOTIONAL)
}
if ($FRIDAY) {
  $a += @('--f5-friday-new-risk-cutoff-utc', $FRIDAY)
}
if ($WEEKEND_FLAT) {
  $a += @('--f5-weekend-flat-utc', $WEEKEND_FLAT)
}
$a += '--frozen-intent-reprice'
if ($RETRY) {
  $a += @('--transient-retry-cap', $RETRY)
}
if ($POLL) {
  $a += @('--poll-seconds', $POLL)
}
& $PY $a *>> $LOG
