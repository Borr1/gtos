$ErrorActionPreference='Continue'
$dir='host-local\AppData\Local\cursor-agent\versions\2026.08.31-4057e58'
Write-Output '---dir---'
if (Test-Path $dir) { Get-ChildItem $dir | Select-Object Name,Length | Format-Table -AutoSize } else { Write-Output 'dir missing' }
Write-Output '---proc---'
Get-CimInstance Win32_Process -Filter "ProcessId=11956" | ForEach-Object { $_.CommandLine }
Write-Output '---search---'
Get-ChildItem 'host-local\AppData\Local\cursor-agent' -Recurse -ErrorAction SilentlyContinue |
  Where-Object { $_.Name -match '^(agent|cursor-agent)\.(exe|cmd|ps1)$' } |
  Select-Object -First 20 FullName,Length
Write-Output '---path---'
Get-Command agent,cursor-agent -ErrorAction SilentlyContinue | Format-List Name,Source
