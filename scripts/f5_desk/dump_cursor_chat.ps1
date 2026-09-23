$ErrorActionPreference='Continue'
$roots = @(
  'host-local\.cursor\chats\f75e6b2678e9890587586781bca68d9f',
  'host-local\.cursor\projects',
  'host-local\redacted_host\repo\.cursor'
)
foreach ($r in $roots) {
  Write-Output "=== $r ==="
  if (Test-Path $r) {
    Get-ChildItem $r -Recurse -ErrorAction SilentlyContinue |
      Where-Object { -not $_.PSIsContainer -and $_.Length -gt 0 } |
      Sort-Object LastWriteTime -Descending |
      Select-Object -First 25 FullName,Length,LastWriteTime
  } else { 'missing' }
}
Write-Output '=== mill chair_last mtime vs now ==='
Get-Item 'host-local\redacted_host\repo\judgment\live\cursor-mill\chair_last.md' | Format-List FullName,Length,LastWriteTime
Write-Output '=== judgment live ==='
Get-ChildItem 'host-local\redacted_host\repo\judgment\live' -File | Sort-Object LastWriteTime -Descending | Select-Object -First 20 Name,Length,LastWriteTime
