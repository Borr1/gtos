# Daily read-only swap snapshot. Pins each terminal. Never mints, never orders.
# Registered as GTOS_SWAP_SNAPSHOT (00:20 broker wall ~ 21:20 UTC in US DST).
[CmdletBinding()]
param()
$ErrorActionPreference = 'Stop'
$py = 'C:\Users\MSI\Documents\ai-trading-agent\.venv-gtos\Scripts\python.exe'
$script = 'host-local\redacted_host\repo\scripts\capture_broker_swap_table.py'
$outDir = 'C:\Users\trader\gtos\grok-jobs\outbox'
& $py $script capture --account FTMO --terminal-path 'C:\MT5\FTMO\terminal64.exe' --expect-server FTMO --out (Join-Path $outDir 'ftmo_swap_series.jsonl')
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
& $py $script capture --account redacted_account --terminal-path 'C:\MT5\redacted_account\terminal64.exe' --expect-server redacted_account --out (Join-Path $outDir 'fn_swap_series.jsonl')
exit $LASTEXITCODE
