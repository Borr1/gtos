$ErrorActionPreference = 'Continue'
$base = 'host-local\redacted_host\repo'
$paths = @{
  hb = "$base\pipeline_state\ultimate_book\operator\heartbeat.json"
  status = "$base\pipeline_state\ultimate_book\operator\status.json"
  latest = "$base\pipeline_state\ultimate_book\operator\latest.json"
  slate = "$base\pipeline_state\ultimate_book\operator\latest_slate.json"
  orig_live = "$base\judgment\live\chair_orig_sl.json"
  orig_state = "$base\pipeline_state\ultimate_book\operator\judgment\state\chair_orig_sl.json"
  recent_allows = "$base\pipeline_state\ultimate_book\operator\recent_allows.json"
}
$files = @{}
foreach ($k in $paths.Keys) {
  $p = $paths[$k]
  if (Test-Path $p) {
    $files[$k] = @{ exists = $true; mtime = (Get-Item $p).LastWriteTimeUtc.ToString('o'); bytes = (Get-Item $p).Length; path = $p }
  } else {
    $files[$k] = @{ exists = $false; path = $p }
  }
}
$taskRaw = (schtasks /Query /TN GTOS_F5_FTMO /FO LIST /V 2>&1 | Out-String)
$task = @{}
foreach ($line in ($taskRaw -split "`r?`n")) {
  $s = $line.Trim()
  foreach ($kk in @('Status:','Last Run Time:','Last Result:','Next Run Time:','Task Name:')) {
    if ($s.StartsWith($kk)) { $task[$kk.TrimEnd(':')] = $s.Substring($kk.Length).Trim() }
  }
}
$writers = @()
foreach ($p in (Get-CimInstance Win32_Process | Where-Object { $_.CommandLine -and ($_.CommandLine -match 'operator') })) {
  $c = $p.CommandLine
  $writers += @{
    pid = $p.ProcessId
    parent = $p.ParentProcessId
    name = $p.Name
    has_size_150 = [bool]($c -match 'f5-minimal-size-usd\s+150')
    has_size_250 = [bool]($c -match 'f5-minimal-size-usd\s+250')
    has_frozen = [bool]($c -match 'frozen-intent-reprice')
    cmd_tail = $c.Substring([Math]::Max(0, $c.Length - 300))
  }
}
$hb = $null
if (Test-Path $paths.hb) {
  try { $hb = Get-Content -Raw $paths.hb | ConvertFrom-Json } catch { $hb = @{ error = $_.Exception.Message } }
}
$status = $null
if (Test-Path $paths.status) {
  try { $status = Get-Content -Raw $paths.status | ConvertFrom-Json } catch { $status = @{ error = $_.Exception.Message } }
}
@{
  probe_utc = (Get-Date).ToUniversalTime().ToString('o')
  files = $files
  task = $task
  writers = $writers
  heartbeat = $hb
  status = $status
} | ConvertTo-Json -Compress -Depth 8
