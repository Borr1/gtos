$ErrorActionPreference='Continue'
Write-Output '=== chair_last ==='
Get-Content 'host-local\redacted_host\repo\judgment\live\cursor-mill\chair_last.md' -Raw
Write-Output '=== wake ==='
Get-Content 'host-local\redacted_host\repo\judgment\live\cursor-mill\chair_wake.json' -Raw
Write-Output '=== study files ==='
Get-ChildItem 'host-local\Desktop\WEEK_STUDY*','host-local\gtos-ops\cursor-chair\WEEK_STUDY*','host-local\redacted_host\repo\judgment\live\cursor-mill\WEEK_STUDY*' -ErrorAction SilentlyContinue | Format-Table FullName,Length,LastWriteTime
Write-Output '=== wrapper ==='
Get-Content 'host-local\gtos-ops\cursor-chair\week_study_run.cmd' -Raw
Write-Output '=== node kids ==='
Get-CimInstance Win32_Process | Where-Object { $_.Name -match 'node|cmd' -and $_.CommandLine -match 'cursor-agent|WEEK_STUDY|index.js' } | ForEach-Object { "$($_.ProcessId) $($_.CommandLine.Substring(0,[Math]::Min(220,$_.CommandLine.Length)))" }
