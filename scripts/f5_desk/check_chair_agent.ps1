Write-Output '---chair md---'
Get-Item 'host-local\gtos-ops\cursor-chair\CHAIR.md' -ErrorAction SilentlyContinue | Format-List FullName,Length,LastWriteTime
Write-Output '---ops dir---'
if (Test-Path 'host-local\gtos-ops\cursor-chair') {
  Get-ChildItem 'host-local\gtos-ops\cursor-chair' -Recurse -File | Sort-Object LastWriteTime -Descending | Select-Object -First 25 FullName,Length,LastWriteTime | Format-Table -AutoSize
} else { 'no gtos-ops cursor-chair' }
Write-Output '---agent data recent---'
$roots = @(
  'host-local\.cursor',
  'host-local\AppData\Local\cursor-agent',
  'host-local\gtos-ops'
)
foreach ($r in $roots) {
  if (Test-Path $r) {
    Write-Output ("root " + $r)
    Get-ChildItem $r -Recurse -File -ErrorAction SilentlyContinue | Where-Object { $_.LastWriteTime -gt (Get-Date).AddHours(-8) -and $_.Length -lt 5000000 -and $_.Extension -match 'md|json|jsonl|log|txt' } | Sort-Object LastWriteTime -Descending | Select-Object -First 15 FullName,Length,LastWriteTime | Format-Table -AutoSize
  }
}
