# Session LN - pre-state capture. READ ONLY. Writes nothing, kills nothing, sends no order.
$ErrorActionPreference = 'Continue'
$ProgressPreference = 'SilentlyContinue'
$Root = 'C:\Users\MSI\Documents\ai-trading-agent'

function Get-Sha256Line($p) {
  if (Test-Path -LiteralPath $p) {
    $f = Get-Item -LiteralPath $p
    $h = (Get-FileHash -Algorithm SHA256 -LiteralPath $p).Hash.ToLower()
    "{0}  {1} B  {2}" -f $h, $f.Length, (Get-Date $f.LastWriteTimeUtc -Format s)
  } else { "ABSENT" }
}

"=== 0. CLOCK / IDENTITY ==="
"host_utc      : " + (Get-Date).ToUniversalTime().ToString('yyyy-MM-ddTHH:mm:ssZ')
"hostname      : " + $env:COMPUTERNAME
"whoami        : " + (whoami)
"root_exists   : " + (Test-Path -LiteralPath $Root)
"C:\GTOS       : " + (Test-Path -LiteralPath 'C:\GTOS') + "  (the OTHER tree - must NOT be edited)"
"root_has_runbook : " + (Test-Path -LiteralPath (Join-Path $Root 'run_book.py'))
"other_has_runbook: " + (Test-Path -LiteralPath 'C:\GTOS\run_book.py')

"`n=== 1. HOST GIT ==="
Push-Location $Root
"branch : " + (git rev-parse --abbrev-ref HEAD 2>&1)
"HEAD   : " + (git rev-parse HEAD 2>&1)
"log    :"
git log --oneline -6 2>&1 | ForEach-Object { "  $_" }
"dirty_count : " + ((git status --porcelain 2>&1 | Measure-Object).Count)
"tracked_modified :"
git status --porcelain 2>&1 | Where-Object { $_ -notmatch '^\?\?' } | ForEach-Object { "  $_" }
Pop-Location

"`n=== 2. CM DESTINATION (execution_packets.py) ==="
"expect before 06a301bff0db... / 38376 B"
"execution_packets.py : " + (Get-Sha256Line (Join-Path $Root 'src\components\ultimate_book\execution_packets.py'))

"`n=== 3. CN DESTINATIONS (7) ==="
"1 src\costs\coverage.py                    : " + (Get-Sha256Line (Join-Path $Root 'src\costs\coverage.py'))
"2 BROKER_TRUE_COSTS_V1.json                : " + (Get-Sha256Line (Join-Path $Root 'research\operations\broker_truth_layer_2026_07_27\BROKER_TRUE_COSTS_V1.json'))
"3 src\costs\model.py                       : " + (Get-Sha256Line (Join-Path $Root 'src\costs\model.py'))
"4 src\costs\__init__.py                    : " + (Get-Sha256Line (Join-Path $Root 'src\costs\__init__.py'))
"5 packet_economics.py (want cc8353ec4a12)  : " + (Get-Sha256Line (Join-Path $Root 'src\components\ultimate_book\packet_economics.py'))
"6 book_owner.py       (want cf6aa69d402b)  : " + (Get-Sha256Line (Join-Path $Root 'src\components\ultimate_book\book_owner.py'))
"7 broker_net_cost_engine.py (want 5b5053cf): " + (Get-Sha256Line (Join-Path $Root 'src\components\broker_net_cost_engine.py'))
"   src\costs dir exists : " + (Test-Path -LiteralPath (Join-Path $Root 'src\costs'))
"   broker_truth dir     : " + (Test-Path -LiteralPath (Join-Path $Root 'research\operations\broker_truth_layer_2026_07_27'))

"`n=== 4. LM-CARRIED PATHS (must be untouched by LN) ==="
"execution.py (want 91ed9873f1b8) : " + (Get-Sha256Line (Join-Path $Root 'src\components\execution.py'))
"tests\test_owner_manual_protective_moves.py : " + (Get-Sha256Line (Join-Path $Root 'tests\test_owner_manual_protective_moves.py'))

"`n=== 5. SUPERVISOR ==="
$sup = Join-Path $Root 'scripts\run_book_supervisor.ps1'
"run_book_supervisor.ps1 (want ff9299bdf4f0) : " + (Get-Sha256Line $sup)
"--- `$books array lines ---"
Select-String -LiteralPath $sup -Pattern 'tags\s*=' -SimpleMatch:$false | ForEach-Object { "  L{0}: {1}" -f $_.LineNumber, $_.Line.Trim() }
"--- frontier occurrences ---"
Select-String -LiteralPath $sup -Pattern 'frontier' | ForEach-Object { "  L{0}: {1}" -f $_.LineNumber, $_.Line.Trim() }
"--- mx occurrences (expect 0) ---"
$mx = @(Select-String -LiteralPath $sup -Pattern 'mx_btcusd_d1_donchian_20_breakout')
"  count = " + $mx.Count
"--- encoding probe ---"
$b = [IO.File]::ReadAllBytes($sup)
"  first4 bytes : " + (($b[0..3] | ForEach-Object { $_.ToString('x2') }) -join ' ')
"  LF count  : " + (@($b | Where-Object { $_ -eq 10 }).Count)
"  CRLF count: " + (([regex]::Matches([Text.Encoding]::ASCII.GetString($b), "`r`n")).Count)

"`n=== 6. CONFIG (token-bound, must NOT move) ==="
"config\agent_config.yaml                  : " + (Get-Sha256Line (Join-Path $Root 'config\agent_config.yaml'))
"config\profiles\operator_profile.yaml: " + (Get-Sha256Line (Join-Path $Root 'config\profiles\operator_profile.yaml'))
"config\profiles\redacted_account.yaml           : " + (Get-Sha256Line (Join-Path $Root 'config\profiles\redacted_account.yaml'))
"include_clean3 line:"
Select-String -LiteralPath (Join-Path $Root 'config\agent_config.yaml') -Pattern 'ultimate_book_include_clean3' | ForEach-Object { "  L{0}: {1}" -f $_.LineNumber, $_.Line.Trim() }
"three gates:"
Select-String -LiteralPath (Join-Path $Root 'config\agent_config.yaml') -Pattern 'ultimate_book_(apply_to_execution|live_activation_allowed|live_broker_authority)' | ForEach-Object { "  L{0}: {1}" -f $_.LineNumber, $_.Line.Trim() }

"`n=== 7. LIVE WORKER COMMAND LINES (the authority on what is armed) ==="
Get-CimInstance Win32_Process -Filter "Name='python.exe'" | ForEach-Object {
  "PID {0}  ppid {1}  created {2}" -f $_.ProcessId, $_.ParentProcessId, (Get-Date $_.CreationDate.ToUniversalTime() -Format s)
  "  CMD: " + $_.CommandLine
}
"--- powershell/wrapper processes ---"
Get-CimInstance Win32_Process -Filter "Name='powershell.exe'" | ForEach-Object {
  "PID {0}  ppid {1}  created {2}" -f $_.ProcessId, $_.ParentProcessId, (Get-Date $_.CreationDate.ToUniversalTime() -Format s)
  "  CMD: " + ($_.CommandLine -replace '\s+', ' ')
}

"`n=== 8. SCHEDULED TASK ==="
Get-ScheduledTask -TaskName 'GTOS_W7_BookSupervisor' -ErrorAction SilentlyContinue |
  ForEach-Object { "GTOS_W7_BookSupervisor state = " + $_.State }
(Get-ScheduledTaskInfo -TaskName 'GTOS_W7_BookSupervisor' -ErrorAction SilentlyContinue) |
  ForEach-Object { "  lastRun={0}  lastResult={1}  nextRun={2}" -f $_.LastRunTime, $_.LastTaskResult, $_.NextRunTime }

"`n=== 9. KILL FLAGS + HEARTBEATS + FIRING SLEEVES ==="
foreach ($f in @('ULTIMATE_BOOK_KILL_ftmo.flag','ULTIMATE_BOOK_KILL_fn.flag')) {
  "flag {0} : {1}" -f $f, (Test-Path -LiteralPath (Join-Path $Root "pipeline_state\$f"))
}
"any *.flag under pipeline_state:"
Get-ChildItem -LiteralPath (Join-Path $Root 'pipeline_state') -Filter *.flag -Recurse -ErrorAction SilentlyContinue |
  ForEach-Object { "  " + $_.FullName }
foreach ($ns in @('operator_profile','redacted_account_live_bee34003')) {
  $hb = Join-Path $Root "pipeline_state\ultimate_book\$ns\heartbeat.json"
  if (Test-Path -LiteralPath $hb) {
    $j = Get-Content -Raw -LiteralPath $hb
    "heartbeat $ns : $j"
    "   age_s = " + [math]::Round(((Get-Date).ToUniversalTime() - (Get-Item -LiteralPath $hb).LastWriteTimeUtc).TotalSeconds, 1)
  } else { "heartbeat $ns : ABSENT" }
  $fs = Join-Path $Root "pipeline_state\ultimate_book\$ns\firing_sleeves.json"
  if (Test-Path -LiteralPath $fs) { "firing_sleeves $ns : " + (Get-Content -Raw -LiteralPath $fs) }
  else { "firing_sleeves $ns : ABSENT" }
}

"`n=== 10. ACTIVATION TOKENS (F1 investigation) ==="
"token dirs present:"
foreach ($d in @('host-local\.gtos\activation','C:\Users\trader\.gtos\activation','C:\Users\MSI\.gtos\activation')) {
  "  {0} : {1}" -f $d, (Test-Path -LiteralPath $d)
  if (Test-Path -LiteralPath $d) {
    Get-ChildItem -LiteralPath $d -File -ErrorAction SilentlyContinue | ForEach-Object {
      "    - {0}  {1} B  {2}" -f $_.Name, $_.Length, (Get-Date $_.LastWriteTimeUtc -Format s)
    }
  }
}
"GTOS_ACTIVATION_TOKEN_DIR (machine) : " + [Environment]::GetEnvironmentVariable('GTOS_ACTIVATION_TOKEN_DIR','Machine')
"GTOS_ACTIVATION_TOKEN_DIR (user)    : " + [Environment]::GetEnvironmentVariable('GTOS_ACTIVATION_TOKEN_DIR','User')
"--- token file contents (payload only; no secret material is printed by design) ---"
foreach ($d in @('host-local\.gtos\activation','C:\Users\trader\.gtos\activation')) {
  if (Test-Path -LiteralPath $d) {
    Get-ChildItem -LiteralPath $d -Filter *.json -ErrorAction SilentlyContinue | ForEach-Object {
      "FILE " + $_.FullName
      (Get-Content -Raw -LiteralPath $_.FullName)
    }
  }
}

"`n=== 11. RECENT BOOK CONSOLE (last startup banner block) ==="
$log = Join-Path $Root 'shadow_logs\run_book_console.log'
if (Test-Path -LiteralPath $log) {
  "log size " + (Get-Item -LiteralPath $log).Length + " B, mtime " + (Get-Date (Get-Item -LiteralPath $log).LastWriteTimeUtc -Format s)
  Get-Content -LiteralPath $log -Tail 70 | ForEach-Object { "  $_" }
} else { "run_book_console.log ABSENT" }

"`n=== 12. LAUNCHER JSONL (last 6 cycles) ==="
$lj = Join-Path $Root 'shadow_logs\ultimate_book_launcher.jsonl'
if (Test-Path -LiteralPath $lj) { Get-Content -LiteralPath $lj -Tail 6 | ForEach-Object { "  $_" } } else { "ABSENT" }

"`n=== 13. CARRIED_STATE.json ==="
$cs = Join-Path $Root 'CARRIED_STATE.json'
if (Test-Path -LiteralPath $cs) { Get-Content -Raw -LiteralPath $cs } else { "ABSENT" }

"`n=== 14. DISK / RAM ==="
Get-PSDrive -PSProvider FileSystem | Where-Object { $_.Used -ne $null } |
  ForEach-Object { "  {0}: free {1} GB / used {2} GB" -f $_.Name, [math]::Round($_.Free/1GB,2), [math]::Round($_.Used/1GB,2) }
$os = Get-CimInstance Win32_OperatingSystem
"  RAM free {0} GB / total {1} GB" -f [math]::Round($os.FreePhysicalMemory/1MB,2), [math]::Round($os.TotalVisibleMemorySize/1MB,2)

"`n=== 15. PYTHON INTERPRETER ==="
$py = Join-Path $Root '.venv-gtos\Scripts\python.exe'
"venv python exists : " + (Test-Path -LiteralPath $py)
if (Test-Path -LiteralPath $py) { "  version: " + (& $py -c "import sys;print(sys.version.split()[0])" 2>&1) }

"`n=== 16. PACKAGE DIRS ALREADY ON HOST? ==="
foreach ($p in @('docs\audits\fable5-vision-audit-20260725\phase17\activation_carry_armed_fidelity',
                 'docs\audits\fable5-vision-audit-20260725\phase17\activation_carry_live_cost_truth',
                 'docs\audits\fable5-vision-audit-20260725\phase19')) {
  "  {0} : {1}" -f $p, (Test-Path -LiteralPath (Join-Path $Root $p))
}
"`n=== END PRESTATE ==="
