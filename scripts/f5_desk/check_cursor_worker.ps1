Write-Output '---out---'
Get-Content 'host-local\redacted_host\repo\judgment\live\cursor-worker.out.log' -ErrorAction SilentlyContinue
Write-Output '---err---'
Get-Content 'host-local\redacted_host\repo\judgment\live\cursor-worker.err.log' -ErrorAction SilentlyContinue
Write-Output '---pid 3956---'
Get-Process -Id 3956 -ErrorAction SilentlyContinue | Format-List Id,ProcessName,StartTime
Write-Output '---node---'
Get-Process node -ErrorAction SilentlyContinue | Format-Table Id,ProcessName,StartTime -AutoSize
