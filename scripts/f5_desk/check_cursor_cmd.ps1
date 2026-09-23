$p = Get-CimInstance Win32_Process -Filter "ProcessId=11956"
if ($p) { Write-Output $p.Name; Write-Output $p.CommandLine; Write-Output $p.CreationDate } else { Write-Output '11956 gone' }
Write-Output '---cursor apps---'
Get-CimInstance Win32_Process | Where-Object { $_.Name -match 'Cursor|cursor' } | ForEach-Object { Write-Output ("{0} {1} {2}" -f $_.ProcessId, $_.Name, $_.CommandLine.Substring(0, [Math]::Min(180, $_.CommandLine.Length))) }
Write-Output '---worker out---'
Get-Content 'host-local\redacted_host\repo\judgment\live\cursor-worker.out.log' -ErrorAction SilentlyContinue
Write-Output '---watch tail---'
Get-Content 'host-local\redacted_host\repo\judgment\live\book_event_watch.log' -Tail 8
