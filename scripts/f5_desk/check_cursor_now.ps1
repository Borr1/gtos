Write-Output '---time---'
Get-Date -Format 'yyyy-MM-dd HH:mm:ss'
Write-Output '---cursor processes---'
Get-CimInstance Win32_Process | Where-Object { $_.Name -match 'cursor|node' -and $_.CommandLine -match 'cursor-agent|worker start|agent.ps1' } | ForEach-Object { '{0} {1}' -f $_.ProcessId, $_.Name }
Write-Output '---handoff---'
Get-Item 'host-local\Desktop\CHAIR-HANDOFF.md','host-local\redacted_host\repo\CHAIR-HANDOFF.md' -ErrorAction SilentlyContinue | ForEach-Object { '{0} {1} {2}' -f $_.FullName, $_.Length, $_.LastWriteTime }
Write-Output '---worker log---'
$log='host-local\redacted_host\repo\judgment\live\cursor-worker.log'
if (Test-Path $log) { Get-Content $log -Tail 20 } else { 'no worker log' }
Write-Output '---inbox---'
$inbox='host-local\redacted_host\repo\judgment\live\cursor_inbox'
if (Test-Path $inbox) { Get-ChildItem $inbox | Select-Object -First 10 Name,LastWriteTime } else { 'no inbox' }
Write-Output '---recent live---'
Get-ChildItem 'host-local\redacted_host\repo\judgment\live' -File | Sort-Object LastWriteTime -Descending | Select-Object -First 12 Name,Length,LastWriteTime | Format-Table -AutoSize
