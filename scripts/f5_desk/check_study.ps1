$ErrorActionPreference='Continue'
Write-Output '=== WEEK_STUDY ==='
Get-ChildItem 'host-local\Desktop\WEEK_STUDY.md','host-local\gtos-ops\cursor-chair\WEEK_STUDY.md','host-local\redacted_host\repo\judgment\live\cursor-mill\WEEK_STUDY.md' -ErrorAction SilentlyContinue | Format-Table FullName,Length,LastWriteTime
Write-Output '=== chair_last ==='
Get-Content 'host-local\redacted_host\repo\judgment\live\cursor-mill\chair_last.md' -Raw
Write-Output '=== 11956 ==='
Get-Process -Id 11956 -ErrorAction SilentlyContinue | Format-Table Id,CPU,StartTime
