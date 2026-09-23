# W7 ultimate_book supervisor — keeps BOTH account books alive (auto-restart on crash/exit) with
# single-instance-per-namespace (prevents a double-book = double-trade). Each book is an independent
# run_book.py process (own terminal/namespace/kill-flag/ledger/governor). If the supervisor itself
# dies the books keep running (separate processes); it only (re)starts a book whose process is gone.
#
# Open-position safety: the supervisor only ever STARTS a missing book; it never stops one, so it can
# never orphan an open position. Operator brakes remain the per-account kill flags + the halt flags.
#
#   powershell -ExecutionPolicy Bypass -File scripts\run_book_supervisor.ps1
$ErrorActionPreference = "Continue"
$repo = "C:\Users\MSI\Documents\ai-trading-agent"
$py   = "$repo\.venv-gtos\Scripts\python.exe"
$env:PYTHONPATH = $repo
Set-Location $repo

# ---- liveness heartbeat + self-log ----
# The supervisor can HANG (a Get-CimInstance/WMI call occasionally blocks indefinitely on Windows). The
# old guard only checked "is another supervisor PROCESS alive", so a hung-but-alive incumbent BLOCKED its
# own replacement: every 5-min scheduled-task fire saw the zombie alive and exited -> books/monitor stop
# being respawned with no self-heal (a real multi-hour monitoring outage). The incumbent now stamps a
# heartbeat each loop; a fresh fire reads it and TAKES OVER a stale (hung) incumbent. Self-log to a file
# too (the scheduled-task action has no stdout redirect, so Write-Output alone is lost).
$hbFile  = Join-Path $repo "pipeline_state\supervisor_heartbeat.json"
$logFile = Join-Path $repo "shadow_logs\book_supervisor.log"
$STALE_S = 120   # a healthy loop refreshes every ~35-40s; >120s (~3 missed loops) = hung

function Write-Hb {
  try {
    $dir = Split-Path $hbFile -Parent
    if (-not (Test-Path $dir)) { New-Item -ItemType Directory -Force -Path $dir | Out-Null }
    $rec = (@{ pid = $PID; ts = (Get-Date).ToUniversalTime().ToString("o") } | ConvertTo-Json -Compress)
    Set-Content -Path "$hbFile.tmp" -Value $rec -Encoding utf8 -NoNewline
    Move-Item -Path "$hbFile.tmp" -Destination $hbFile -Force
  } catch {}
}
function Log-Sup([string]$m) {
  $line = ("{0} {1}" -f (Get-Date -Format o), $m)
  Write-Output $line
  try { Add-Content -Path $logFile -Value $line -Encoding utf8 } catch {}
}

# SINGLE-INSTANCE guard (robust): yield to a HEALTHY senior incumbent, but TAKE OVER a hung one, and
# resolve concurrent fresh starts by total-order seniority so a race leaves EXACTLY ONE survivor.
# Match ONLY real "-File ...run_book_supervisor.ps1" launches (NOT diagnostic -Command shells whose
# text happens to contain a wildcard pattern with "-File*run_book_supervisor.ps1"), excluding self.
$selfPid   = $PID
$selfStart = (Get-CimInstance Win32_Process -Filter "ProcessId=$selfPid" -ErrorAction SilentlyContinue).CreationDate
$supervisorFilePattern = '(?i)(^|\s)-File\s+"?[^"]*run_book_supervisor\.ps1"?($|\s)'
$others    = @(Get-CimInstance Win32_Process -Filter "Name='powershell.exe'" -ErrorAction SilentlyContinue |
  Where-Object { $_.ProcessId -ne $selfPid -and $_.CommandLine -match $supervisorFilePattern })
$otherPids = @($others | ForEach-Object { $_.ProcessId })

$hbPid = $null; $hbAge = $null
if (Test-Path $hbFile) {
  try {
    $hb = Get-Content $hbFile -Raw -ErrorAction Stop | ConvertFrom-Json
    $hbPid = [int]$hb.pid
    $hbAge = ((Get-Date).ToUniversalTime() - ([datetime]$hb.ts).ToUniversalTime()).TotalSeconds
  } catch { $hbPid = $null; $hbAge = $null }
}

if ($hbPid -and ($otherPids -contains $hbPid) -and ($null -ne $hbAge) -and ($hbAge -gt $STALE_S)) {
  # (1) HUNG incumbent: heartbeat pid is an ALIVE supervisor but its heartbeat is STALE -> kill + take over.
  Log-Sup ("incumbent supervisor pid {0} heartbeat STALE ({1:n0}s > {2}s) -- HUNG; killing and taking over" -f $hbPid, $hbAge, $STALE_S)
  try { Stop-Process -Id $hbPid -Force -ErrorAction SilentlyContinue } catch {}
  Start-Sleep -Seconds 1
  $otherPids = @($otherPids | Where-Object { $_ -ne $hbPid })
  $others    = @($others    | Where-Object { $_.ProcessId -ne $hbPid })
}
elseif ($hbPid -and ($otherPids -contains $hbPid) -and ($null -ne $hbAge) -and ($hbAge -le $STALE_S)) {
  # (2) HEALTHY incumbent: heartbeat pid is an ALIVE supervisor and FRESH -> defer.
  Write-Output ("{0} healthy supervisor pid {1} running (hb {2:n0}s); single-instance exit" -f (Get-Date -Format o), $hbPid, $hbAge)
  exit 0
}
# (3) Race among fresh starts (no established/fresh incumbent): defer to a SENIOR (create_time, pid) sibling.
foreach ($o in $others) {
  $isSenior = ($o.CreationDate -lt $selfStart) -or (($o.CreationDate -eq $selfStart) -and ($o.ProcessId -lt $selfPid))
  if ($isSenior) {
    Write-Output ("{0} senior supervisor pid {1} starting; single-instance exit" -f (Get-Date -Format o), $o.ProcessId)
    exit 0
  }
}
Write-Hb   # claim incumbency immediately so a near-simultaneous sibling sees a fresh heartbeat

# ARMING. `tags` is the arming mechanism: there is no confidence_floor key anywhere in the tree and no
# floor can express the armed set (admission.py:218-219 -- sub_xvol_pullback is 0.45 while the killed
# metals_softband is 0.50). The DECLARED set, with a receipt per arming and disarming decision, lives in
# config/live_armed_set.json; src/safety/armed_set.py reconciles the two and
# tests/safety/test_armed_set_single_source.py fails the build if they ever drift apart. Change both in
# the same commit.
#
# `mx_btcusd_d1_donchian_20_breakout` was DISARMED on FTMO on 2026-08-05 by owner instruction (D-2
# CLOSED, host commit 2fa77722d, receipt phase19/receipts/vps_live_ops_20260805/MX_DISABLE_RECEIPT.md on
# branch ops/vps-live-mx-disable-20260805). The host was edited that day; THIS file was not, so for two
# days a book restarted from the committed launcher would have re-armed a sleeve the owner turned off.
# Carried here 2026-08-07. `--frontier-exits` went with it: the frontier contract existed only to run
# that sleeve's target_5R exit.
#
# Do NOT carry this file wholesale to the host. The host's copy is a different, larger file (19,495 B
# after the 2026-08-05 edit against 7,828 B here, books array at :140 not :86, spread-floor key named
# `floor` not `spreadFloor`). Carry individual argument changes, never the file.
#
# THE TWO F5 ROWS BELOW ARE A SECOND DECISION SURFACE PER ACCOUNT, NOT A CHANGE TO THE ARMED
# BOOK. They are new namespaces, so the supervisor simply starts two more workers (it never
# stops anything -- see the loop below); the two armed rows are untouched, not restarted, not
# re-tagged and not re-tokened. The F5 workers take their OWN broker identity
# (mt5_interface.magic_for_namespace -> magic 0, comment prefix "F5:") so the armed
# book cannot see their positions: book_engine._open_risk_pct returns the FULL gross-risk cap
# on ANY visible position with no stop loss or an unreadable value_per_point, which would make
# the armed book read gross_risk_cap_exhausted and stop opening units SILENTLY.
# Proof: tests/safety/test_f5_isolation.py.
#
# The 32-name --tags list is EXPLICIT and never omitted: run_book.py:383 treats an empty string
# as "all BUILT sleeves" (fail-open) and armed_set.py classifies that CRITICAL. The same 32
# names are declared for each F5 namespace in config/live_armed_set.json in the same commit,
# and tests/safety/test_armed_set_single_source.py fails the build if the two ever drift.
#
# frontier/spreadFloor/laneWeights are deliberately $null on the F5 rows: the experiment
# measures the RAW full system, so a per-sleeve overlay applied to 2 of 32 sleeves would make
# it neither the armed book nor the raw book. Turning one on later is a one-line launcher edit
# plus the matching declaration.
$books = @(
  @{ ns="operator_profile"; profile="operator_profile"; term="C:\MT5\FTMO\terminal64.exe"; kill="pipeline_state/ULTIMATE_BOOK_KILL_ftmo.flag"; log="shadow_logs\run_book_console.log"; tags="crypto,energy_agri,sub_xvol_pullback"; frontier=$null; spreadFloor="sub_mid_dn_revert,sub_xvol_pullback"; laneWeights="C:\ProgramData\GTOS\lane-weights\operator_profile.json"; laneWeightsKey="C:\ProgramData\GTOS\lane-weights\lane_weights.key" },
  @{ ns="redacted_account_live_bee34003"; profile="redacted_account"; term="C:\MT5\redacted_account\terminal64.exe"; kill="pipeline_state/ULTIMATE_BOOK_KILL_fn.flag"; log="shadow_logs\run_book_fn_console.log"; tags="crypto,energy_agri,sub_xvol_pullback"; frontier=$null; spreadFloor="sub_mid_dn_revert,sub_xvol_pullback"; laneWeights="C:\ProgramData\GTOS\lane-weights\redacted_account_live_bee34003.json"; laneWeightsKey="C:\ProgramData\GTOS\lane-weights\lane_weights.key" },
  # FTMO F5 row updated 2026-08-30 launch-contract bind: 51 tags, $250, q1 shadow floor,
  # event-clock-shadow, Friday 16:00 UTC cutoff, weekend flatten 20:30 UTC.
  # Live argv is still machine-local f5_launch.ps1; this row must match so a host
  # restart that (re)starts via THIS supervisor cannot silently drop floor/weekend.
  # Production rows untouched.
  # The old row here was the retired $10-era launch (32 tags incl. pulled fx_jpy/fx_jpy_ny/
  # ny_crypto_momentum) and lied to the armed_set reconciler.
  @{ ns="operator"; profile="operator_profile"; term="C:\MT5\FTMO\terminal64.exe"; kill="pipeline_state/ULTIMATE_BOOK_KILL_ftmo_f5.flag"; log="shadow_logs\run_book_ftmo_f5.log"; tags="crypto,dsp_bleed_accept_fresh_20low_second_push,dsp_climax_2atr_onto_20high_then_fade,dsp_climax_onto_20high_then_fade_cashhole,dsp_climax_onto_20high_then_fade_london,dsp_close_on_20low_not_a_cascade_then_up,dsp_expanding_two_bar_run_tokyo,dsp_expanding_up_staircase,dsp_first_cash_bar_spike_and_flush,dsp_high_vol_doji_after_reclaimed_flush_fx,dsp_huge_down_hold_then_spring,dsp_isolated_spike_high,dsp_london_bounce_fails_overnight_midpoint,dsp_london_two_up_into_20high_reverses,dsp_walked_high_accepted_through,dsp_weekend_gap_then_bleed_into_20low,dsp_wide_down_then_micro_bounce_then_through,energy_agri,idxrev,kz_london_crypto_low,liq_asia_up_low_metal,metal_session_reversion,metals_core,metals_ob_micro,metals_softband,mx_avausd_d1_donchian_20_breakout,mx_btcusd_d1_donchian_20_breakout,mx_cadjpy_d1_volume_surge_reversal,mx_ethusd_d1_donchian_20_breakout,mx_eu50_cash_d1_volume_surge_reversal,mx_fra40_cash_d1_volume_surge_reversal,mx_ger40_cash_d1_volume_surge_reversal,mx_jp225_cash_d1_volume_surge_reversal,mx_nzdjpy_d1_donchian_20_breakout,mx_us100_cash_d1_atr_mean_reversion,mx_us30_cash_d1_volume_surge_reversal,mx_us500_cash_d1_atr_mean_reversion,orb_crypto_london,sub_mid_dn_revert,sub_xvol_pullback,vol_compression,vp_euidx_pocgrav,vss_fxcross_london_up_low,xa_climax_spring,xa_huge_20_extreme,xa_isolated_opposite,xa_prior_huge,xa_second_leg,xa_wide_extreme,asian_fade_widen,orb_crypto_london_widen"; frontier=$null; spreadFloor=$null; laneWeights=$null; laneWeightsKey=$null; f5Size="250"; f5Notional="100000"; riskFloorMode="shadow"; riskFloor="crypto,dsp_bleed_accept_fresh_20low_second_push,dsp_climax_2atr_onto_20high_then_fade,dsp_climax_onto_20high_then_fade_cashhole,dsp_climax_onto_20high_then_fade_london,dsp_close_on_20low_not_a_cascade_then_up,dsp_expanding_two_bar_run_tokyo,dsp_expanding_up_staircase,dsp_first_cash_bar_spike_and_flush,dsp_high_vol_doji_after_reclaimed_flush_fx,dsp_huge_down_hold_then_spring,dsp_isolated_spike_high,dsp_london_bounce_fails_overnight_midpoint,dsp_london_two_up_into_20high_reverses,dsp_walked_high_accepted_through,dsp_weekend_gap_then_bleed_into_20low,dsp_wide_down_then_micro_bounce_then_through,energy_agri,idxrev,kz_london_crypto_low,liq_asia_up_low_metal,metal_session_reversion,metals_core,metals_ob_micro,metals_softband,mx_avausd_d1_donchian_20_breakout,mx_btcusd_d1_donchian_20_breakout,mx_cadjpy_d1_volume_surge_reversal,mx_ethusd_d1_donchian_20_breakout,mx_eu50_cash_d1_volume_surge_reversal,mx_fra40_cash_d1_volume_surge_reversal,mx_ger40_cash_d1_volume_surge_reversal,mx_jp225_cash_d1_volume_surge_reversal,mx_nzdjpy_d1_donchian_20_breakout,mx_us100_cash_d1_atr_mean_reversion,mx_us30_cash_d1_volume_surge_reversal,mx_us500_cash_d1_atr_mean_reversion,orb_crypto_london,sub_mid_dn_revert,sub_xvol_pullback,vol_compression,vp_euidx_pocgrav,vss_fxcross_london_up_low,xa_climax_spring,xa_huge_20_extreme,xa_isolated_opposite,xa_prior_huge,xa_second_leg,xa_wide_extreme,asian_fade_widen,orb_crypto_london_widen"; eventClock=$true; fridayCutoff="16:00"; weekendFlat="20:30"; frozenIntent=$true; transientRetryCap="3" }
  # redacted_account_f5_minimal row REMOVED 2026-08-25: that pair is DOWN BY DECISION (watchdog
  # contract, CEREMONY-RECEIPT-20260825) and its 7 skipped symbols do not exist on the FN
  # terminal. A committed row that re-arms a decided-down book on any supervisor restart is
  # a hazard wearing a config's clothes. Re-add deliberately with an owner word + receipt.
)

function Test-BookRunning([string]$ns) {
  $procs = Get-CimInstance Win32_Process -Filter "Name='python.exe'" |
           Where-Object { $_.CommandLine -like "*run_book.py*" -and $_.CommandLine -like "*--namespace $ns*" }
  return (@($procs).Count -gt 0)
}

function Test-MonitorRunning {
  $procs = Get-CimInstance Win32_Process -Filter "Name='python.exe'" |
           Where-Object { $_.CommandLine -like "*monitor_books.py*--loop*" }
  return (@($procs).Count -gt 0)
}

Log-Sup ("book supervisor starting (pid {0}; ns: {1})" -f $PID, ($books.ns -join ", "))
while ($true) {
  Write-Hb   # FIRST each loop: if the tick then hangs in a CIM call the heartbeat goes STALE -> a fresh fire takes over
  foreach ($b in $books) {
    if (-not (Test-BookRunning $b.ns)) {
      Log-Sup ("(re)starting book ns={0}" -f $b.ns)
      # Every OPTIONAL argument is added only when the row supplies one. The three that moved
      # from unconditional to conditional (--spread-geometry-floor, --lane-weights,
      # --lane-weights-key) are UNCHANGED for the two armed rows, which supply all three; a
      # $null on an F5 row would otherwise reach run_book.py as an empty string, and
      # parse_spread_geometry_floor REFUSES an empty string at launch by design (an empty
      # --tags is fail-open, so the parsers treat "" as an operator error, not as "none").
      $a = @("run_book.py", "--terminal-path", $b.term, "--namespace", $b.ns,
             "--profile", $b.profile, "--kill-flag", $b.kill, "--poll-seconds", "60",
             "--tags", $b.tags)
      if ($b.spreadFloor)    { $a += @("--spread-geometry-floor", $b.spreadFloor) }
      if ($b.laneWeights)    { $a += @("--lane-weights", $b.laneWeights) }
      if ($b.laneWeightsKey) { $a += @("--lane-weights-key", $b.laneWeightsKey) }
      if ($b.frontier) { $a += @("--frontier-exits", $b.frontier) }
      # F5 MINIMAL SIZE. Present on the two f5 rows only; absent everywhere else, which is what
      # keeps every seam inert for the armed books.
      if ($b.f5Size) { $a += @("--f5-minimal-size-usd", $b.f5Size,
                               "--f5-notional-initial-usd", $b.f5Notional) }
      # F5 launch-contract bind 2026-08-30: floor + weekend. Keys exist only on the
      # F5 row; production rows stay byte-identical (missing key => $null => skip).
      if ($b.riskFloorMode) { $a += @("--risk-unit-floor-mode", $b.riskFloorMode) }
      if ($b.riskFloor) { $a += @("--risk-unit-floor", $b.riskFloor) }
      if ($b.eventClock) { $a += @("--event-clock-shadow") }
      if ($b.fridayCutoff) { $a += @("--f5-friday-new-risk-cutoff-utc", $b.fridayCutoff) }
      if ($b.weekendFlat) { $a += @("--f5-weekend-flat-utc", $b.weekendFlat) }
      if ($b.frozenIntent) { $a += @("--frozen-intent-reprice") }
      if ($b.transientRetryCap) { $a += @("--transient-retry-cap", $b.transientRetryCap) }
      Start-Process -FilePath $py -ArgumentList $a -WorkingDirectory $repo -WindowStyle Hidden `
                    -RedirectStandardOutput $b.log -RedirectStandardError ($b.log + ".err")
      Start-Sleep -Seconds 3
    }
  }
  if (-not (Test-MonitorRunning)) {
    Log-Sup "(re)starting monitor daemon"
    Start-Process -FilePath $py -ArgumentList @(".tools\monitor_books.py", "--loop", "300") `
                  -WorkingDirectory $repo -WindowStyle Hidden `
                  -RedirectStandardOutput "shadow_logs\monitor_daemon.log" -RedirectStandardError "shadow_logs\monitor_daemon.err"
  }
  Start-Sleep -Seconds 30
}
