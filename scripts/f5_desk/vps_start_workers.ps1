# Supervisor-friendly start for the three Free Trial demo observers + relay.
# Detached. Idempotent. Never initializes C:\MT5\FTMO or logins 0 / 0.
# Chair entry alongside judgment/fleet/mirror/mirror_fanout.py.
$ErrorActionPreference = "Stop"

function Resolve-RepoRoot {
    param([string]$Start)
    $cursor = Get-Item -LiteralPath $Start
    while ($null -ne $cursor) {
        if (Test-Path -LiteralPath (Join-Path $cursor.FullName "judgment\fleet\worker_plan.py")) {
            return $cursor.FullName
        }
        $cursor = $cursor.Parent
    }
    throw "repo root with judgment/fleet/worker_plan.py not found from $Start"
}

$here = $PSScriptRoot
if (-not $here) { $here = (Get-Location).Path }
$Repo = Resolve-RepoRoot $here
if ($env:GTOS_REPO) { $Repo = $env:GTOS_REPO }

$PyCandidates = @(
    $env:GTOS_PYTHON,
    "C:\Users\MSI\Documents\ai-trading-agent\.venv-gtos\Scripts\python.exe",
    "host-local\redacted_host\repo\.venv\Scripts\python.exe",
    (Get-Command python -ErrorAction SilentlyContinue | Select-Object -ExpandProperty Source)
) | Where-Object { $_ }
$Py = $PyCandidates | Where-Object { $_ -and (Test-Path -LiteralPath $_) } | Select-Object -First 1
if (-not $Py) { $Py = "python" }

$env:PYTHONPATH = $Repo
Set-Location $Repo

$planJson = & $Py (Join-Path $Repo "judgment\fleet\worker_plan.py") --json
if ($LASTEXITCODE -ne 0 -or -not $planJson) {
    throw "worker_plan.py failed"
}
$plan = $planJson | ConvertFrom-Json
if ($plan.place_on_challenge) {
    throw "refusing plan with place_on_challenge=true"
}

$runDir = Join-Path $Repo "judgment\fleet\mirror\run"
$logDir = Join-Path $Repo "judgment\fleet\mirror\logs"
New-Item -ItemType Directory -Force -Path $runDir | Out-Null
New-Item -ItemType Directory -Force -Path $logDir | Out-Null

function Test-PidAlive {
    param([int]$ProcessId)
    if ($ProcessId -le 0) { return $false }
    $proc = Get-Process -Id $ProcessId -ErrorAction SilentlyContinue
    return $null -ne $proc
}

function Read-PidFile {
    param([string]$Path)
    if (-not (Test-Path -LiteralPath $Path)) { return 0 }
    $raw = (Get-Content -LiteralPath $Path -ErrorAction SilentlyContinue | Select-Object -First 1)
    if (-not $raw) { return 0 }
    $parsed = 0
    if ([int]::TryParse($raw.Trim(), [ref]$parsed)) { return $parsed }
    return 0
}

function Start-DetachedWorker {
    param($Spec)
    $pidFile = [string]$Spec.pid_path
    $logFile = [string]$Spec.log_path
    $existing = Read-PidFile $pidFile
    if (Test-PidAlive $existing) {
        Write-Output ("ALREADY_UP id={0} pid={1}" -f $Spec.id, $existing)
        return
    }
    $argv = @($Spec.argv)
    if ($argv.Count -lt 2) { throw "bad argv for $($Spec.id)" }
    $exe = [string]$argv[0]
    $argList = @($argv | Select-Object -Skip 1)
    $joined = ($argList | ForEach-Object {
            if ($_ -match '\s') { '"' + $_ + '"' } else { $_ }
        }) -join ' '
    if ($joined -match '0|0|\\MT5\\FTMO\\terminal') {
        throw "refusing Challenge-shaped command for $($Spec.id)"
    }
    $proc = Start-Process -FilePath $exe -ArgumentList $argList -WorkingDirectory $Repo `
        -WindowStyle Hidden -RedirectStandardOutput $logFile -RedirectStandardError "$logFile.err" `
        -PassThru
    Set-Content -LiteralPath $pidFile -Value ([string]$proc.Id) -Encoding ascii
    Write-Output ("STARTED id={0} pid={1} log={2}" -f $Spec.id, $proc.Id, $logFile)
}

Start-DetachedWorker $plan.relay
foreach ($worker in $plan.workers) {
    Start-DetachedWorker $worker
}

Write-Output ("PLAN_OK targets={0} outbox={1} place_on_challenge=false" -f ($plan.targets -join ','), $plan.outbox)
