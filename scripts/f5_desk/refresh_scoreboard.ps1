# Chair / sit / night one-shot. Read-only. Does not take the judge lock.
param(
    [string]$RepoRoot = "host-local\redacted_host\repo",
    [string]$PythonExe = "C:\Users\MSI\Documents\ai-trading-agent\.venv-gtos\Scripts\python.exe"
)
& $PythonExe (Join-Path $RepoRoot "scripts\f5_desk\scoreboard.py") @args
exit $LASTEXITCODE
