$ErrorActionPreference = "Continue"
$repo = "host-local\redacted_host\repo"
$bo = Join-Path $repo "src\components\ultimate_book\book_owner.py"
Write-Output "BOOK_OWNER_BYTES $((Get-Item $bo).Length)"
Write-Output "BOOK_OWNER_SHA256 $((Get-FileHash $bo -Algorithm SHA256).Hash)"
$hb = Join-Path $repo "pipeline_state\ultimate_book\operator\heartbeat.json"
Write-Output "HEARTBEAT_PATH $hb"
if (Test-Path $hb) { Get-Content $hb -Raw }
Write-Output "PROCS"
Get-CimInstance Win32_Process -Filter "Name='python.exe'" | Where-Object { $_.CommandLine -match 'run_book' } | ForEach-Object {
  $cl = $_.CommandLine
  if ($cl.Length -gt 260) { $cl = $cl.Substring(0, 260) }
  Write-Output ("PID {0} {1}" -f $_.ProcessId, $cl)
}
Write-Output "TRADE_RECORDS"
$tr = Join-Path $repo "pipeline_state\ultimate_book\operator\trade_records"
if (Test-Path $tr) {
  Get-ChildItem $tr | Where-Object { $_.Name -match '294088097|294092360' } | ForEach-Object {
    Write-Output ("{0} {1} {2}" -f $_.Name, $_.Length, $_.LastWriteTime.ToUniversalTime().ToString("o"))
  }
}
