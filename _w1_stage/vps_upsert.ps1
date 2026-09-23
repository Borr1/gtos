$ErrorActionPreference = 'Continue'
$stage = 'host-local\redacted_host\repo\_w1_stage'
$cal = Join-Path $stage 'f5_high_calendar.json'
$spine = Join-Path $stage 'official_high_spine.json'
$brief = Join-Path $stage 'news_brief.json'
$targets = @(
  @{ src=$cal; dst='host-local\redacted_host\repo\judgment\state\f5_high_calendar.json' },
  @{ src=$cal; dst='host-local\redacted_host\repo\pipeline_state\ultimate_book\operator\judgment\state\f5_high_calendar.json' },
  @{ src=$cal; dst='host-local\redacted_host\repo\data\news\f5_high_calendar.json' },
  @{ src=$spine; dst='host-local\redacted_host\repo\data\official_high_spine.json' },
  @{ src=$brief; dst='host-local\redacted_host\repo\judgment\live\news_brief.json' },
  @{ src=$brief; dst='host-local\redacted_host\repo\data\news_brief.json' },
  @{ src=$brief; dst='host-local\redacted_host\repo\pipeline_state\ultimate_book\operator\judgment\live\news_brief.json' }
)
$ok = @()
$failed = @()
foreach ($t in $targets) {
  try {
    $dir = Split-Path -Parent $t.dst
    if (-not (Test-Path $dir)) { New-Item -ItemType Directory -Path $dir -Force | Out-Null }
    Copy-Item -Path $t.src -Destination $t.dst -Force
    if (Test-Path $t.dst) { $ok += $t.dst; Write-Output ("OK " + $t.dst) } else { $failed += $t.dst; Write-Output ("FAIL_MISSING " + $t.dst) }
  } catch {
    $failed += $t.dst
    Write-Output ("FAIL " + $t.dst + " :: " + $_.Exception.Message)
  }
}
Write-Output '---READBACK---'
foreach ($p in @(
  'host-local\redacted_host\repo\judgment\state\f5_high_calendar.json',
  'host-local\redacted_host\repo\data\official_high_spine.json',
  'host-local\redacted_host\repo\data\news\f5_high_calendar.json',
  'host-local\redacted_host\repo\judgment\live\news_brief.json'
)) {
  if (Test-Path $p) {
    $j = Get-Content -Raw -Path $p | ConvertFrom-Json
    $stamp = $j.updated_utc
    if (-not $stamp) { $stamp = $j.spine_updated_utc }
    if (-not $stamp) { $stamp = $j.as_of_utc }
    Write-Output ("STAMP " + $stamp + " :: " + $p)
  } else {
    Write-Output ("NOFILE " + $p)
  }
}
# intel-layer outside root — probe only
$intel = 'C:\Users\trader'
Write-Output ('TRADER_EXISTS ' + (Test-Path $intel))
Write-Output ('OK_COUNT ' + $ok.Count)
Write-Output ('FAIL_COUNT ' + $failed.Count)
