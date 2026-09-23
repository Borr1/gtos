$ErrorActionPreference = "Continue"
$repo = "host-local\redacted_host\repo"
Write-Output "UTC $((Get-Date).ToUniversalTime().ToString('o'))"
$hb = Join-Path $repo "pipeline_state\ultimate_book\operator\heartbeat.json"
Write-Output "HEARTBEAT"
if (Test-Path $hb) { Get-Content $hb -Raw } else { Write-Output "MISSING_HEARTBEAT" }
$st = Join-Path $repo "pipeline_state\ultimate_book\operator\judgment\unique_loader_stamp.json"
Write-Output "STAMP"
if (Test-Path $st) {
  Write-Output ("stamp_mtime={0}" -f (Get-Item $st).LastWriteTime.ToUniversalTime().ToString("o"))
  Get-Content $st -Raw
} else { Write-Output "MISSING_STAMP" }
Write-Output "STAMP_PIDS"
Get-ChildItem (Join-Path $repo "pipeline_state\ultimate_book\operator\judgment") -Filter "unique_loader_stamp*.json" | ForEach-Object {
  Write-Output ("{0} {1}" -f $_.LastWriteTime.ToUniversalTime().ToString("o"), $_.Name)
}
$bo = Join-Path $repo "src\components\ultimate_book\book_owner.py"
Write-Output ("BOOK_OWNER_BYTES {0}" -f (Get-Item $bo).Length)
Write-Output ("BOOK_OWNER_SHA256 {0}" -f (Get-FileHash $bo -Algorithm SHA256).Hash)
Write-Output "PROCS"
Get-CimInstance Win32_Process -Filter "Name='python.exe'" | Where-Object { $_.CommandLine -match 'run_book' } | ForEach-Object {
  $ns = "other"
  if ($_.CommandLine -match 'operator') { $ns = "F5" }
  elseif ($_.CommandLine -match 'redacted_account') { $ns = "FN" }
  elseif ($_.CommandLine -match 'FTMO_Trial') { $ns = "SH" }
  elseif ($_.CommandLine -match 'FTMO_redacted_account') { $ns = "redacted_account" }
  elseif ($_.CommandLine -match 'FTMO_redacted_account') { $ns = "redacted_account" }
  Write-Output ("{0} PID {1}" -f $ns, $_.ProcessId)
}
Write-Output "TICKETS"
$tr = Join-Path $repo "pipeline_state\ultimate_book\operator\trade_records"
foreach ($t in @("294088097","294092360")) {
  $p = Join-Path $tr ($t + ".json")
  if (-not (Test-Path $p)) { Write-Output "$t MISSING"; continue }
  $j = Get-Content $p -Raw | ConvertFrom-Json
  $life = $j.trade_lifecycle_status
  if (-not $life) { $life = $j.lifecycle_status }
  Write-Output ("{0} life={1}" -f $t, $life)
}
Write-Output "DONE"
