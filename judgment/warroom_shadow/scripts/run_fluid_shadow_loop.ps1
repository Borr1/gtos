# Challenge fluid-gate loop — SHADOW capture + APPLY flags for Challenge writer compose
# Chair 2026-09-20: keep APPLY=1 / POLICY_C=1 (owner full activation). Still never place from this script.
$ErrorActionPreference = "Continue"
$Ws = "host-local\redacted_host\repo\judgment\warroom_shadow"
$Py = "host-local\redacted_host\repo\.venv\Scripts\python.exe"
$Script = Join-Path $Ws "scripts\run_jev_fluid_gates_shadow.py"
$Sidecar = Join-Path $Ws "judgment\live\jev_sidecar"
$LogDir = Join-Path $Ws "scripts\logs"
New-Item -ItemType Directory -Force -Path $Sidecar,$LogDir | Out-Null

$env:PYTHONPATH = $Ws
$env:GTOS_JEV_FLUID_GATES_SHADOW = "1"
$env:GTOS_JEV_FLUID_GATES_APPLY = "1"
$env:GTOS_JEV_POLICY_C_APPLY = "1"
$env:GTOS_JEV_EVERYWHERE_SHADOW = "1"
$env:GTOS_JEV_FLUID_GATES_LOG_DIR = $Sidecar
$env:GTOS_DIG_MULTI_STAGE_GUARD_SHADOW = "1"

Set-Location $Ws
$stamp = Get-Date -Format "yyyyMMdd_HHmmss"
$out = Join-Path $LogDir "shadow_$stamp.out.log"
$err = Join-Path $LogDir "shadow_$stamp.err.log"
& $Py $Script --login 0 1> $out 2> $err
$code = $LASTEXITCODE
$line = "$(Get-Date -Format o) exit=$code shadow=1 apply=1 policy_c=1 sidecar=$Sidecar"
Add-Content -Path (Join-Path $LogDir "shadow_runner.log") -Value $line

$S16 = Join-Path $Ws "scripts\run_s16_prove.py"
$Fix = Join-Path $Ws "judgment\astra\lab\s16_prove_fixtures"
if (Test-Path $S16) {
  $env:GTOS_DIG_MULTI_STAGE_GUARD_SHADOW = "1"
  & $Py $S16 --offline --jev-fixture-mode --shadow --no-place --no-host-mesh --no-network --fixtures $Fix 1> (Join-Path $LogDir "s16_$stamp.out.log") 2> (Join-Path $LogDir "s16_$stamp.err.log")
  Add-Content -Path (Join-Path $LogDir "shadow_runner.log") -Value "$(Get-Date -Format o) s16_exit=$LASTEXITCODE"
}
exit $code