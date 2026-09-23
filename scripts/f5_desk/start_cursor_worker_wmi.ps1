$ErrorActionPreference = 'Stop'
$Desk = 'host-local\redacted_host\repo'
$Log = 'host-local\redacted_host\repo\judgment\live\cursor-worker.log'
$Agent = 'host-local\AppData\Local\cursor-agent\agent.ps1'
New-Item -ItemType Directory -Force -Path (Split-Path $Log) | Out-Null
# Detached via cmd so the worker survives SSH. Verbose to the log.
$cmd = 'cmd.exe /c "powershell.exe -NoProfile -ExecutionPolicy Bypass -File `"host-local\AppData\Local\cursor-agent\agent.ps1`" worker start --name gtos-vps --worker-dir `"host-local\redacted_host\repo`" --idle-release-timeout 0 --verbose 1>> `"host-local\redacted_host\repo\judgment\live\cursor-worker.log`" 2>&1"'
$created = Invoke-CimMethod -ClassName Win32_Process -MethodName Create -Arguments @{
  CommandLine = $cmd
  CurrentDirectory = $Desk
}
if (-not $created -or $created.ReturnValue -ne 0) {
  Write-Output ("FAIL create rv=" + $(if ($created) { $created.ReturnValue } else { 'null' }))
  exit 3
}
$procId = [int]$created.ProcessId
Start-Sleep -Seconds 10
$alive = Get-Process -Id $procId -ErrorAction SilentlyContinue
Write-Output ("started pid=" + $procId + " alive=" + [bool]$alive + " wmi_rv=" + $created.ReturnValue)
Write-Output '---log---'
if (Test-Path $Log) { Get-Content $Log -Tail 50 }
