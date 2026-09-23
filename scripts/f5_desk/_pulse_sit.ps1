$procs = Get-CimInstance Win32_Process | Where-Object { $_.CommandLine -like '*operator*' -or $_.CommandLine -like '*run_f5_ftmo*' }
$procs | ForEach-Object { "{0} ppid={1} name={2}" -f $_.ProcessId, $_.ParentProcessId, $_.Name }
Write-Host '---CMDLINE---'
$procs | ForEach-Object {
  $cl = $_.CommandLine
  if ($cl.Length -gt 350) { $cl = $cl.Substring(0,350) }
  "{0} {1}" -f $_.ProcessId, $cl
}
Write-Host '---TASK---'
Get-ScheduledTask -TaskName GTOS_F5_FTMO | Select-Object TaskName,State | Format-List
Write-Host '---VERIFY_TAIL---'
Get-Content host-local\redacted_host\repo\shadow_logs\f5_verification.log -Tail 8
Write-Host '---GOV---'
$g = 'host-local\redacted_host\repo\pipeline_state\ultimate_book\operator\governor.json'
if (Test-Path $g) { Get-Content $g -TotalCount 50 } else { Write-Host 'no governor.json' }
Write-Host '---READY---'
Get-ChildItem host-local\redacted_host\repo\pipeline_state\ultimate_book\operator -Filter '*ready*' -ErrorAction SilentlyContinue | Select-Object Name,LastWriteTime
Write-Host '---SLATE---'
$s = 'host-local\redacted_host\repo\pipeline_state\ultimate_book\operator\judgment\state\latest_slate.json'
if (Test-Path $s) { Get-Content $s -TotalCount 30; Write-Host ('slate_mtime ' + (Get-Item $s).LastWriteTimeUtc.ToString('o')) } else { Write-Host 'no latest_slate' }
