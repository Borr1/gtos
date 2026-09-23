# CONTRACT V2 nightly study (task GTOS_F5_STUDY, 22:05 UTC = after the FTMO day resets at 22:00Z).
# Challenge LIVE=0 only. Verification 0 is quarantined.
# Chair retargeted VPS f5_study LIVE and this launcher; GitHub pin so it cannot drift back.
# Read-only MT5 in the VPS impl. This launcher never broker-sends. redacted_account is out of scope.
$ErrorActionPreference = 'Continue'
$LIVE = 0
$VERIFY_QUARANTINED = 0
if ($env:F5_STUDY_LOGIN -and [string]$env:F5_STUDY_LOGIN -eq [string]$VERIFY_QUARANTINED) {
  throw "F5_STUDY_LOGIN=0 is quarantined. Challenge LIVE is 0."
}
if ($env:LIVE -and [string]$env:LIVE -eq [string]$VERIFY_QUARANTINED) {
  throw "LIVE=0 is quarantined. Challenge LIVE is 0."
}
$env:LIVE = "$LIVE"
$env:F5_STUDY_LIVE = "$LIVE"
$env:F5_STUDY_LOGIN = "$LIVE"

$repoDesk = $PSScriptRoot
$py  = if ($env:F5_STUDY_PYTHON) { $env:F5_STUDY_PYTHON } else { 'C:\Users\MSI\Documents\ai-trading-agent\.venv-gtos\Scripts\python.exe' }
$src = if ($env:F5_STUDY_SRC) { $env:F5_STUDY_SRC } else { 'C:\Users\trader\redacted_host' }
$day = (Get-Date).ToUniversalTime().ToString('yyyy-MM-dd')
$out = if ($env:F5_STUDY_OUT) { $env:F5_STUDY_OUT } else { "host-local\Desktop\fable-pack\nightly\$day" }
New-Item -ItemType Directory -Force -Path $out | Out-Null

$study = if (Test-Path "$repoDesk\f5_study.py") { "$repoDesk\f5_study.py" } else { "$src\f5_study.py" }
$refused = if (Test-Path "$src\f5_refused_cf.py") { "$src\f5_refused_cf.py" } else { $null }
$decide = if (Test-Path "$repoDesk\decide.py") { "$repoDesk\decide.py" } elseif (Test-Path "$src\decide.py") { "$src\decide.py" } else { $null }

& $py $study --login $LIVE --src $src --out $out *> "$out\f5_study.log"
if ($refused) {
  & $py $refused *> "$out\f5_refused_cf.log"
}
if (Test-Path "$src\f5_study.json") {
  Copy-Item "$src\f5_study.json" "$out\f5_study.json" -ErrorAction SilentlyContinue
}
Copy-Item "$src\f5_refused_cf.json" "$out\f5_refused_cf.json" -ErrorAction SilentlyContinue
Copy-Item "host-local\redacted_host\repo\pipeline_state\ultimate_book\operator\judgment\JUDGE-MEMORY.md" "$out\JUDGE-MEMORY.md" -ErrorAction SilentlyContinue
# J7 (Fable 5.1): KEEP/RELAX/OFF at n≥40 and R>2·SE. CHAIR reads this at 07:00 ICT.
if ($decide) {
  & $py $decide $out $src *> "$out\decide.log"
}
"$day nightly study written LIVE=$LIVE" | Out-File "$out\DONE.txt"
