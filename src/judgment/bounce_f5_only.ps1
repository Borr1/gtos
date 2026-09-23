# Bounce Challenge writer only. Never FN. Never flatten. Never remint.
$ErrorActionPreference = "Continue"
function Get-BookProcs {
  Get-CimInstance Win32_Process -Filter "Name='python.exe' OR Name='pythonw.exe' OR Name='powershell.exe'" |
    Where-Object { $_.CommandLine }
}
function Show-Books {
  param($tag)
  Write-Output "=== $tag ==="
  Get-BookProcs | Where-Object {
    $_.CommandLine -match 'run_book|f5_launch|redacted_account|ftmo_f5|redacted_account|ftmo_redacted_account|ftmo_redacted_account'
  } | ForEach-Object {
    $cl = $_.CommandLine
    if ($cl.Length -gt 220) { $cl = $cl.Substring(0, 220) }
    Write-Output ("{0} {1}" -f $_.ProcessId, $cl)
  }
}
Show-Books "before"
$f5 = Get-BookProcs | Where-Object {
  $_.CommandLine -match 'operator' -or
  $_.CommandLine -match 'f5_launch' -or
  ($_.CommandLine -match 'run_book' -and $_.CommandLine -match 'activation-f5' -and $_.CommandLine -notmatch 'activation-f5-')
}
# Narrow: Challenge ns or f5_launch. Never friends, never FN.
$kill = Get-BookProcs | Where-Object {
  ($_.CommandLine -match 'operator') -or
  ($_.CommandLine -match 'f5_launch\.ps1') -or
  ($_.CommandLine -match 'scripts\\f5_launch')
}
$ids = @($kill | ForEach-Object { $_.ProcessId } | Sort-Object -Unique)
Write-Output ("KILL " + ($ids -join ","))
foreach ($id in $ids) {
  try { Stop-Process -Id $id -Force -ErrorAction Stop; Write-Output "STOP $id" }
  catch { Write-Output "STOP_FAIL $id $($_.Exception.Message)" }
}
Start-Sleep -Seconds 2
$still = Get-BookProcs | Where-Object { $_.CommandLine -match 'operator' }
Write-Output ("STILL_F5 " + @($still | ForEach-Object { $_.ProcessId }).Count)
Write-Output "END_SUPERVISOR"
& schtasks.exe /End /TN "\GTOS_W7_BookSupervisor"
Start-Sleep -Seconds 2
Write-Output "RUN_SUPERVISOR"
& schtasks.exe /Run /TN "\GTOS_W7_BookSupervisor"
$up = $false
for ($i = 1; $i -le 30; $i++) {
  Start-Sleep -Seconds 2
  $now = @(Get-BookProcs | Where-Object { $_.CommandLine -match 'operator' })
  if ($now.Count -ge 1) {
    Write-Output ("UP i=$i n=$($now.Count)")
    $now | ForEach-Object {
      $cl = $_.CommandLine
      if ($cl.Length -gt 220) { $cl = $cl.Substring(0, 220) }
      Write-Output ("{0} {1}" -f $_.ProcessId, $cl)
    }
    $up = $true
    break
  }
  Write-Output "WAIT i=$i n=0"
}
if (-not $up) { Write-Output "FAIL_NOT_UP"; exit 2 }
Show-Books "after"
exit 0
