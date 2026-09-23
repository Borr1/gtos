$ErrorActionPreference = 'Continue'
$py = 'C:\Users\MSI\Documents\ai-trading-agent\.venv-gtos\Scripts\python.exe'
$repo = 'host-local\redacted_host\repo'
$ns = Join-Path $repo 'pipeline_state\ultimate_book\operator'
$live = Join-Path $repo 'judgment\live'
$outDir = Join-Path $live 'sit1220'
New-Item -ItemType Directory -Force -Path $outDir | Out-Null

Write-Output '===TASK==='
$t = Get-ScheduledTask -TaskName 'GTOS_F5_FTMO' -ErrorAction SilentlyContinue
if ($null -ne $t) {
  $i = Get-ScheduledTaskInfo -TaskName 'GTOS_F5_FTMO'
  Write-Output ("TASK State={0} LastResult={1} LastRun={2}" -f $t.State, $i.LastTaskResult, $i.LastRunTime)
} else {
  Write-Output 'TASK MISSING'
}

Write-Output '===PROCS==='
Get-CimInstance Win32_Process | Where-Object {
  $_.Name -match 'python' -and $_.CommandLine -and ($_.CommandLine -match 'operator' -or $_.CommandLine -match 'run_book.py')
} | ForEach-Object {
  $cmd = $_.CommandLine
  $frozen = $cmd -match '--frozen-intent-reprice'
  $nsHit = $cmd -match 'operator'
  $m = [regex]::Match($cmd, '--f5-minimal-size-usd\s+(\d+)')
  $sz = if ($m.Success) { $m.Groups[1].Value } else { '' }
  Write-Output ("PID={0} Parent={1} frozen={2} ns={3} size={4}" -f $_.ProcessId, $_.ParentProcessId, $frozen, $nsHit, $sz)
}

Write-Output '===HEARTBEAT==='
$hb = Join-Path $ns 'heartbeat.json'
if (Test-Path $hb) {
  $item = Get-Item $hb
  Write-Output ("hb mtime={0} size={1}" -f $item.LastWriteTime.ToString('s'), $item.Length)
  Get-Content $hb -Raw
} else { Write-Output 'MISSING heartbeat' }

Write-Output '===FUEL==='
$fuel = Join-Path $live '_sit_fuel.py'
if (Test-Path $fuel) {
  Push-Location $repo
  & $py $fuel 1> (Join-Path $outDir 'fuel_out.json') 2> (Join-Path $outDir 'fuel_err.txt')
  Write-Output ("FUEL_EXIT=$LASTEXITCODE bytes=$((Get-Item (Join-Path $outDir 'fuel_out.json') -EA SilentlyContinue).Length)")
  Pop-Location
} else { Write-Output 'MISSING _sit_fuel.py' }

Write-Output '===MFE==='
$mfeSrc = Join-Path $live '_sit1210_mfe.py'
$mfe = Join-Path $live '_sit1220_mfe.py'
if ((Test-Path $mfeSrc) -and -not (Test-Path $mfe)) { Copy-Item $mfeSrc $mfe -Force }
if (Test-Path $mfe) {
  Push-Location $repo
  & $py $mfe 1> (Join-Path $outDir 'mfe_out.json') 2> (Join-Path $outDir 'mfe_err.txt')
  Write-Output ("MFE_EXIT=$LASTEXITCODE bytes=$((Get-Item (Join-Path $outDir 'mfe_out.json') -EA SilentlyContinue).Length)")
  Pop-Location
} else { Write-Output 'MISSING mfe script' }

Write-Output '===CHAIR_SIT==='
$chair = Join-Path $repo 'scripts\f5_desk\chair_desk.py'
if ((Test-Path $py) -and (Test-Path $chair)) {
  & $py $chair sit --mt5 2>&1 | Out-String | Tee-Object -FilePath (Join-Path $outDir 'chair_sit.txt')
} else {
  Write-Output ("chair missing py={0} script={1}" -f (Test-Path $py), (Test-Path $chair))
}

Write-Output '===FILE_MTIMES==='
$paths = @(
  (Join-Path $ns 'heartbeat.json'),
  (Join-Path $ns 'judgment\state\latest_slate.json'),
  (Join-Path $ns 'judgment\state\chair_orig_sl.json'),
  (Join-Path $live 'latest.json'),
  (Join-Path $live 'status.json')
)
foreach ($p in $paths) {
  if (Test-Path $p) {
    $i = Get-Item $p
    Write-Output ("EXISTS {0} mtime={1} size={2}" -f $p, $i.LastWriteTime.ToString('s'), $i.Length)
  } else {
    Write-Output ("MISSING {0}" -f $p)
  }
}
Write-Output '===DONE==='
