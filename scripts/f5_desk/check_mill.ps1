Write-Output '---mill---'
$d='host-local\redacted_host\repo\judgment\live\cursor-mill'
if (Test-Path $d) {
  Get-ChildItem $d -Recurse -File | Sort-Object LastWriteTime -Descending | Select-Object FullName,Length,LastWriteTime | Format-Table -AutoSize
  Write-Output '---chair_last---'
  if (Test-Path (Join-Path $d 'chair_last.md')) { Get-Content (Join-Path $d 'chair_last.md') -TotalCount 80 }
  Write-Output '---inbox tail---'
  if (Test-Path (Join-Path $d 'inbox.jsonl')) { Get-Content (Join-Path $d 'inbox.jsonl') -Tail 8 }
  Write-Output '---x_since---'
  if (Test-Path (Join-Path $d 'x_since.json')) { Get-Content (Join-Path $d 'x_since.json') }
  Write-Output '---markets---'
  if (Test-Path (Join-Path $d 'markets.md')) { Get-Content (Join-Path $d 'markets.md') -TotalCount 40 }
} else { 'NO cursor-mill dir' }
Write-Output '---node cpu---'
Get-Process -Id 11956 -ErrorAction SilentlyContinue | Format-List Id,CPU,WorkingSet,StartTime
Write-Output '---wake---'
$w='host-local\redacted_host\repo\pipeline_state\ultimate_book\operator\judgment\state\chair_wake.json'
if (Test-Path $w) { Get-Item $w | Format-List FullName,Length,LastWriteTime }
