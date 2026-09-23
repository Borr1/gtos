$ErrorActionPreference = 'Continue'
Write-Output '---processes---'
Get-CimInstance Win32_Process -Filter "Name='node.exe'" | ForEach-Object {
  '{0} {1}' -f $_.ProcessId, $_.CommandLine
}
Write-Output '---starting worker---'
$agent = 'host-local\AppData\Local\cursor-agent\agent.ps1'
$arg = @(
  '-NoProfile','-ExecutionPolicy','Bypass','-File', $agent,
  'worker','start',
  '--name','gtos-vps',
  '--worker-dir','host-local\redacted_host\repo',
  '--idle-release-timeout','0'
)
$psi = New-Object System.Diagnostics.ProcessStartInfo
$psi.FileName = 'powershell.exe'
$psi.Arguments = ($arg -join ' ')
$psi.WorkingDirectory = 'host-local\redacted_host\repo'
$psi.UseShellExecute = $false
$psi.CreateNoWindow = $true
$psi.RedirectStandardOutput = $true
$psi.RedirectStandardError = $true
$logDir = 'host-local\redacted_host\repo\judgment\live'
if (-not (Test-Path $logDir)) { New-Item -ItemType Directory -Force -Path $logDir | Out-Null }
$psi.StandardOutputFileName = Join-Path $logDir 'cursor-worker.out.log'
$psi.StandardErrorFileName = Join-Path $logDir 'cursor-worker.err.log'
# ProcessStartInfo doesn't have StandardOutputFileName on older .NET; use Start-Process
$p = Start-Process -FilePath 'powershell.exe' -ArgumentList $arg -WorkingDirectory 'host-local\redacted_host\repo' -WindowStyle Hidden -PassThru -RedirectStandardOutput (Join-Path $logDir 'cursor-worker.out.log') -RedirectStandardError (Join-Path $logDir 'cursor-worker.err.log')
Write-Output ("started pid={0}" -f $p.Id)
Start-Sleep -Seconds 8
Write-Output '---log out---'
if (Test-Path (Join-Path $logDir 'cursor-worker.out.log')) { Get-Content (Join-Path $logDir 'cursor-worker.out.log') -TotalCount 40 }
Write-Output '---log err---'
if (Test-Path (Join-Path $logDir 'cursor-worker.err.log')) { Get-Content (Join-Path $logDir 'cursor-worker.err.log') -TotalCount 40 }
