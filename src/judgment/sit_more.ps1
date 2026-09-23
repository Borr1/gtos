$ErrorActionPreference = "Continue"
$repo = "host-local\redacted_host\repo"
Write-Output "UTC $((Get-Date).ToUniversalTime().ToString('o'))"
Write-Output "=== F5_CREATE ==="
Get-CimInstance Win32_Process -Filter "ProcessId=6228" | ForEach-Object {
  Write-Output ("pid=6228 create={0}" -f $_.CreationDate)
}
Get-CimInstance Win32_Process -Filter "ProcessId=7688" | ForEach-Object {
  Write-Output ("pid=7688 create={0}" -f $_.CreationDate)
}
Write-Output "=== FN ==="
$fn = Get-CimInstance Win32_Process -Filter "Name='python.exe'" | Where-Object { $_.CommandLine -match 'redacted_account' }
if (-not $fn) { Write-Output "FN_NONE" }
$fn | ForEach-Object { Write-Output ("FN PID={0} PPID={1}" -f $_.ProcessId, $_.ParentProcessId) }
Write-Output "=== PID5852 ==="
Get-CimInstance Win32_Process -Filter "ProcessId=5852" | ForEach-Object {
  Write-Output ("pid=5852 create={0} cl={1}" -f $_.CreationDate, $_.CommandLine)
}
Write-Output "=== UNIQUE_APPLY_IN_JSONL ==="
$jl = Join-Path $repo "pipeline_state\ultimate_book\operator\judgment\judge_2026-09-21.jsonl"
if (Test-Path $jl) {
  Write-Output ("jsonl_bytes={0} mtime={1}" -f (Get-Item $jl).Length, (Get-Item $jl).LastWriteTime.ToUniversalTime().ToString("o"))
  Select-String -Path $jl -Pattern "unique_apply|unique_loader|UNIQUE_APPLY" | Select-Object -Last 8 | ForEach-Object { $_.Line.Substring(0, [Math]::Min(400, $_.Line.Length)) }
} else { Write-Output "NO_JSONL" }
Write-Output "=== NEWS_SPINE ==="
$ns = Join-Path $repo "src\judgment\news_spine.py"
Write-Output ("news_spine_bytes={0}" -f (Get-Item $ns).Length)
Write-Output "=== PERSIST ==="
Select-String -Path (Join-Path $repo "src\judgment\gold_priors.py") -Pattern "persistence" | Select-Object -First 6 | ForEach-Object { $_.Line.Trim() }
Write-Output "=== TICKETS ==="
$tr = Join-Path $repo "pipeline_state\ultimate_book\operator\trade_records"
foreach ($t in @("294088097","294092360")) {
  $p = Join-Path $tr ($t + ".json")
  if (-not (Test-Path $p)) { Write-Output "$t MISSING"; continue }
  $j = Get-Content $p -Raw | ConvertFrom-Json
  $life = $j.trade_lifecycle_status
  if (-not $life) { $life = $j.lifecycle_status }
  Write-Output ("{0} life={1}" -f $t, $life)
}
Write-Output "=== BOOK_OWNER_HITS ==="
$bo = Join-Path $repo "src\components\ultimate_book\book_owner.py"
Write-Output ("sha={0} bytes={1}" -f (Get-FileHash $bo -Algorithm SHA256).Hash, (Get-Item $bo).Length)
Write-Output "DONE"
