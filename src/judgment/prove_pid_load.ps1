$ErrorActionPreference = "Continue"
$repo = "host-local\redacted_host\repo"
Write-Output "UTC $((Get-Date).ToUniversalTime().ToString('o'))"
$hb = Join-Path $repo "pipeline_state\ultimate_book\operator\heartbeat.json"
Write-Output "HEARTBEAT"
if (Test-Path $hb) { Get-Content $hb -Raw } else { Write-Output "MISSING_HEARTBEAT" }
$st = Join-Path $repo "pipeline_state\ultimate_book\operator\judgment\unique_loader_stamp.json"
Write-Output "STAMP $st"
if (Test-Path $st) { Get-Content $st -Raw } else { Write-Output "MISSING_STAMP" }
$gs = Join-Path $repo "judgment\astra\lab\a1\gold_seats_live.json"
Write-Output "GOLD_SEATS $gs"
if (Test-Path $gs) { Get-Content $gs -Raw } else { Write-Output "MISSING_GOLD_SEATS_STAMP" }
$bo = Join-Path $repo "src\components\ultimate_book\book_owner.py"
Write-Output "BOOK_OWNER_BYTES $((Get-Item $bo).Length)"
Write-Output "BOOK_OWNER_SHA256 $((Get-FileHash $bo -Algorithm SHA256).Hash)"
Write-Output "PROCS"
Get-CimInstance Win32_Process -Filter "Name='python.exe'" | Where-Object { $_.CommandLine -match 'run_book' } | ForEach-Object {
  $ns = "other"
  if ($_.CommandLine -match 'operator') { $ns = "F5" }
  elseif ($_.CommandLine -match 'redacted_account') { $ns = "FN" }
  elseif ($_.CommandLine -match 'FTMO_Trial') { $ns = "friend_a" }
  elseif ($_.CommandLine -match 'FTMO_redacted_account') { $ns = "redacted_account" }
  elseif ($_.CommandLine -match 'FTMO_redacted_account') { $ns = "redacted_account" }
  Write-Output ("{0} PID {1}" -f $ns, $_.ProcessId)
}
$tr = Join-Path $repo "pipeline_state\ultimate_book\operator\trade_records"
Write-Output "TICKETS"
foreach ($t in @("294088097","294092360")) {
  $p = Join-Path $tr ($t + ".json")
  if (-not (Test-Path $p)) { Write-Output "$t MISSING"; continue }
  $j = Get-Content $p -Raw | ConvertFrom-Json
  $life = $j.trade_lifecycle_status
  if (-not $life) { $life = $j.lifecycle_status }
  if (-not $life) { $life = $j.status }
  Write-Output ("{0} life={1} mtime={2}" -f $t, $life, (Get-Item $p).LastWriteTime.ToUniversalTime().ToString("o"))
}
