$ErrorActionPreference = "Continue"
$repo = "host-local\redacted_host\repo"
Write-Output "UTC $((Get-Date).ToUniversalTime().ToString('o'))"
Write-Output "=== HEARTBEAT ==="
$hb = Join-Path $repo "pipeline_state\ultimate_book\operator\heartbeat.json"
if (Test-Path $hb) { Get-Content $hb -Raw } else { Write-Output "MISSING_HEARTBEAT" }
Write-Output "=== RUN_BOOK_PID ==="
$rbp = Join-Path $repo "pipeline_state\ultimate_book\operator\run_book.pid"
if (Test-Path $rbp) { Get-Content $rbp -Raw } else { Write-Output "MISSING_RUN_BOOK_PID" }
Write-Output "=== INIT ==="
$init = Join-Path $repo "src\judgment\__init__.py"
$ii = Get-Item $init
Write-Output ("bytes={0} mtime={1}" -f $ii.Length, $ii.LastWriteTime.ToUniversalTime().ToString("o"))
Write-Output "INIT_HEAD"
Get-Content $init -TotalCount 20
Write-Output "INIT_TAIL"
Get-Content $init -Tail 40
Write-Output "=== UNIQUE_LOADER ==="
$ul = Join-Path $repo "src\judgment\unique_loader.py"
$ui = Get-Item $ul
Write-Output ("bytes={0} mtime={1} sha={2}" -f $ui.Length, $ui.LastWriteTime.ToUniversalTime().ToString("o"), (Get-FileHash $ul -Algorithm SHA256).Hash)
Write-Output "=== STAMP ==="
$st = Join-Path $repo "pipeline_state\ultimate_book\operator\judgment\unique_loader_stamp.json"
if (Test-Path $st) {
  Write-Output ("stamp_mtime={0}" -f (Get-Item $st).LastWriteTime.ToUniversalTime().ToString("o"))
  Get-Content $st -Raw
} else { Write-Output "MISSING_STAMP" }
Write-Output "=== GOLD_SEATS_STAMP ==="
$gs = Join-Path $repo "judgment\astra\lab\a1\gold_seats_live.json"
if (Test-Path $gs) {
  Write-Output ("gs_mtime={0}" -f (Get-Item $gs).LastWriteTime.ToUniversalTime().ToString("o"))
  $g = Get-Content $gs -Raw | ConvertFrom-Json
  Write-Output ("gs_pid={0} persist={1} hit={2} utc={3}" -f $g.pid, $g.persist, $g.hit_count, $g.utc)
} else { Write-Output "MISSING_GOLD_SEATS_STAMP" }
Write-Output "=== PROCS ==="
Get-CimInstance Win32_Process -Filter "Name='python.exe'" | ForEach-Object {
  $cl = $_.CommandLine
  if ($null -eq $cl) { $cl = "" }
  Write-Output ("PID={0} PPID={1} CL={2}" -f $_.ProcessId, $_.ParentProcessId, $cl)
}
Write-Output "=== BOOK_OWNER ==="
$bo = Join-Path $repo "src\components\ultimate_book\book_owner.py"
Write-Output ("bytes={0} sha={1}" -f (Get-Item $bo).Length, (Get-FileHash $bo -Algorithm SHA256).Hash)
Write-Output "=== JUDGMENT_DIR ==="
cmd /c dir /b "host-local\redacted_host\repo\src\judgment"
Write-Output "=== LATEST_A1 ==="
$a1 = Join-Path $repo "pipeline_state\ultimate_book\operator"
Get-ChildItem $a1 -Recurse -Filter "*a1*" -ErrorAction SilentlyContinue | Sort-Object LastWriteTime -Descending | Select-Object -First 8 | ForEach-Object {
  Write-Output ("{0} {1}" -f $_.LastWriteTime.ToUniversalTime().ToString("o"), $_.FullName)
}
Write-Output "=== CONSUME_TAIL ==="
$cons = Join-Path $repo "pipeline_state\ultimate_book\operator\judgment"
if (Test-Path $cons) {
  Get-ChildItem $cons | Sort-Object LastWriteTime -Descending | Select-Object -First 12 | ForEach-Object {
    Write-Output ("{0} {1} {2}" -f $_.LastWriteTime.ToUniversalTime().ToString("o"), $_.Length, $_.Name)
  }
}
Write-Output "DONE"
