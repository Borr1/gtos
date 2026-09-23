# Daily read-only M1 archive. Pins FTMO terminal. Never mints, never orders.
# Registered as GTOS_M1_ARCHIVE (00:25 broker wall ~ 21:25 UTC in US DST).
[CmdletBinding()]
param()
$ErrorActionPreference = 'Stop'
$py = 'C:\Users\MSI\Documents\ai-trading-agent\.venv-gtos\Scripts\python.exe'
$script = 'C:\Users\trader\gtos\m1_archive_daily.py'
$logDir = 'C:\Users\trader\gtos\m1_backfill'
& $py $script
$code = $LASTEXITCODE
if ($code -ne 0) {
    "$(Get-Date -Format o) exit=$code" | Add-Content (Join-Path $logDir 'ARCHIVE_ERR.log')
    exit $code
}
exit 0
