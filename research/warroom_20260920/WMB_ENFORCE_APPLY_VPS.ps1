# WMB_ENFORCE_APPLY_VPS.ps1 — Chair ENFORCE surface hard-off + stage 2-stop circuit
# Run ON VPS via Shell machineId 7cfa9657 (NOT host-mesh). PowerShell uses ; not &&
# Do NOT place/remint/flatten. Do NOT flip GTOS_JEV_SLEEVE_SELECT_APPLY.
$ErrorActionPreference = 'Continue'
$ts = (Get-Date).ToUniversalTime().ToString('o')
Write-Host "WMB_ENFORCE_START utc=$ts host=$env:COMPUTERNAME user=$env:USERNAME"

$Repo = 'host-local\redacted_host\repo'
$Launch = 'host-local\redacted_host\f5_launch.ps1'
$Contract = 'host-local\redacted_host\launch_contracts\operator.json'
$OffTags = @('xa_second_rth','kz_london_crypto_low')
$KeepNeedles = @(
  'vss_fxcross_london_up_low','metal_session_reversion',
  'sub_mid_dn_re_proxy_nzdusd_short_m15_atr','asian_fade',
  'sub_mid_dn_re_proxy_eurusd_short_m15_atr','dsp_spring','three_fresh'
)
$ExistingOff = @('mx_us30','idxrev','bleed','orb_crypto','xa_huge')

function Backup-File([string]$Path) {
  if (-not (Test-Path $Path)) { Write-Host "MISSING $Path"; return $false }
  $bak = "$Path.bak_wmb_enforce_20260921"
  if (-not (Test-Path $bak)) { Copy-Item $Path $bak -Force; Write-Host "BAK $bak" }
  return $true
}

# --- ENFORCE 1: strip tags from f5_launch.ps1 ---
if (Backup-File $Launch) {
  $raw = Get-Content -Raw $Launch
  $before = $raw
  foreach ($t in $OffTags) {
    # remove as CSV token (leading/trailing commas)
    $raw = [regex]::Replace($raw, "(?i)(?<=,|\")" + [regex]::Escape($t) + "(?=,|\")", '')
    $raw = [regex]::Replace($raw, '(?i),' + [regex]::Escape($t) + '(?=,|")', '')
    $raw = [regex]::Replace($raw, '(?i)(?<="|,)' + [regex]::Escape($t) + ',', '')
  }
  # collapse double commas
  while ($raw -match ',,') { $raw = $raw -replace ',,', ',' }
  if ($raw -ne $before) {
    Set-Content -Path $Launch -Value $raw -Encoding UTF8
    Write-Host "PATCHED f5_launch.ps1 removed $($OffTags -join ',')"
  } else {
    Write-Host "f5_launch.ps1 no token change (may already be off or different quoting) — will grep"
  }
  foreach ($t in $OffTags) {
    $hits = Select-String -Path $Launch -Pattern $t -SimpleMatch
    Write-Host ("LAUNCH_TAG {0} hits={1}" -f $t, @($hits).Count)
  }
}

# --- ENFORCE 1b: contract selected_tags_csv ---
if (Backup-File $Contract) {
  try {
    $j = Get-Content -Raw $Contract | ConvertFrom-Json
    $csv = $null
    if ($j.PSObject.Properties.Name -contains 'selected_tags_csv') { $csv = [string]$j.selected_tags_csv }
    elseif ($j.PSObject.Properties.Name -contains 'tags') { $csv = [string]$j.tags }
    if ($csv) {
      $parts = @($csv.Split(',') | ForEach-Object { $_.Trim() } | Where-Object { $_ -and ($OffTags -notcontains $_) })
      $new = [string]::Join(',', $parts)
      if ($j.PSObject.Properties.Name -contains 'selected_tags_csv') { $j.selected_tags_csv = $new }
      else { $j.tags = $new }
      ($j | ConvertTo-Json -Depth 12) | Set-Content -Path $Contract -Encoding UTF8
      Write-Host "PATCHED contract tags; off=$($OffTags -join ',')"
    } else {
      Write-Host "CONTRACT no selected_tags_csv/tags field — inspect keys: $($j.PSObject.Properties.Name -join ',')"
    }
  } catch {
    Write-Host "CONTRACT_PATCH_ERR $_"
  }
}

# --- ENFORCE 1c: judgment family.py hard-off cousins (shadow+admit labels) ---
$fam = Join-Path $Repo 'src\judgment\family.py'
if (-not (Test-Path $fam)) { $fam = Join-Path $Repo 'src\components\judgment\family.py' }
# also common wave path
$famCands = @(
  (Join-Path $Repo 'src\judgment\family.py'),
  (Join-Path $Repo 'judgment\family.py'),
  (Join-Path $Repo 'src\components\ultimate_book\..\..\judgment\family.py')
)
Get-ChildItem -Path $Repo -Recurse -Filter 'family.py' -ErrorAction SilentlyContinue |
  Where-Object { $_.FullName -match 'judgment' } |
  Select-Object -First 5 |
  ForEach-Object {
    Write-Host "FOUND_FAMILY $($_.FullName)"
    Backup-File $_.FullName | Out-Null
    $t = Get-Content -Raw $_.FullName
    if ($t -notmatch 'xa_second_rth') {
      $t2 = $t -replace 'if sl\.startswith\("xa_huge"\):\r?\n\s+return "xa_huge"',
        "if sl.startswith(`"xa_huge`") or sl.startswith(`"xa_second_rth`"):`r`n        return `"xa_huge`" if sl.startswith(`"xa_huge`") else `"xa_second_rth`""
      if ($t2 -ne $t) { Set-Content -Path $_.FullName -Value $t2 -Encoding UTF8; Write-Host "PATCHED family xa_second_rth $($_.FullName)" }
      else { Write-Host "FAMILY_PATCH_MANUAL_NEEDED $($_.FullName)" }
    } else { Write-Host "FAMILY already has xa_second_rth" }
  }

# --- ENFORCE 2: land two_stop_day_circuit.py into repo ---
$destDir = Join-Path $Repo 'src\components\ultimate_book'
$dest = Join-Path $destDir 'two_stop_day_circuit.py'
$researchDir = Join-Path $Repo 'research\warroom_20260920'
New-Item -ItemType Directory -Force -Path $researchDir | Out-Null
# Prefer content already staged beside this script if present
$staged = @(
  (Join-Path (Split-Path $MyInvocation.MyCommand.Path -Parent) 'two_stop_day_circuit.py'),
  'host-local\redacted_host\repo\research\warroom_20260920\two_stop_day_circuit.py'
)
# If missing, write minimal stub inline via here-string below after copy attempt

# --- Writer inventory (do not kill yet) ---
$procs = @(Get-CimInstance Win32_Process | Where-Object {
  $_.CommandLine -and $_.CommandLine -match 'run_book\.py' -and $_.CommandLine -match 'operator'
})
Write-Host ("WRITER_PROCS_BEFORE={0}" -f $procs.Count)
foreach ($p in $procs) {
  $cl = $p.CommandLine
  if ($cl.Length -gt 240) { $cl = $cl.Substring(0,240) }
  Write-Host ("PID={0} PPID={1} CMD={2}" -f $p.ProcessId, $p.ParentProcessId, $cl)
  foreach ($k in $KeepNeedles) {
    if ($p.CommandLine -match [regex]::Escape($k)) { Write-Host "  KEEP_OK $k" }
  }
  foreach ($t in $OffTags) {
    if ($p.CommandLine -match [regex]::Escape($t)) { Write-Host "  STILL_IN_ARGV $t" } else { Write-Host "  ARGV_OFF $t" }
  }
  if ($p.CommandLine -match 'GTOS_JEV_SLEEVE_SELECT_APPLY=1') { Write-Host '  WARN APPLY=1' }
}

# Sleeve-select must stay 0
$envLine = [Environment]::GetEnvironmentVariable('GTOS_JEV_SLEEVE_SELECT_APPLY','Machine')
Write-Host "ENV_GTOS_JEV_SLEEVE_SELECT_APPLY=$envLine"
Write-Host "WMB_ENFORCE_LAUNCH_DONE — recycle only if tags still in live argv; preserve 2 procs"
Write-Host "NEXT: if STILL_IN_ARGV, stop FTMO pair + Start-Process f5_launch.ps1; re-check argv"
