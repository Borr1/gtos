# Read-only evidence capture for Session CL's zero-mutation pass-surface ceremony.
param(
  [string]$OutFile = "HOST_PREFLIGHT.json"
)

$ErrorActionPreference = "Stop"
function Mark([string]$m) { Add-Content -Path "host-local\gtos-ceremonies\wave17-20260801\PROGRESS.txt" -Value ((Get-Date -Format o) + " " + $m) }
Mark "start"
$repo = "C:\Users\MSI\Documents\ai-trading-agent"
Set-Location $repo

function File-Record([string]$RelativePath) {
  Mark ("file-record " + $RelativePath)
  $path = Join-Path $repo $RelativePath
  if (-not (Test-Path -LiteralPath $path -PathType Leaf)) {
    return @{ path = $RelativePath; present = $false; sha256 = $null; bytes = $null }
  }
  $item = Get-Item -LiteralPath $path
  return @{
    path = $RelativePath
    present = $true
    sha256 = (Get-FileHash -Algorithm SHA256 -LiteralPath $path).Hash.ToLowerInvariant()
    bytes = [int64]$item.Length
  }
}

function Ledger-Record([string]$Namespace) {
  $relative = "pipeline_state\ultimate_book\$Namespace\firing_sleeves.json"
  return File-Record $relative
}

function Log-Proofs([string]$RelativePath) {
  Mark ("log-proofs " + $RelativePath)
  $path = Join-Path $repo $RelativePath
  if (-not (Test-Path -LiteralPath $path -PathType Leaf)) { return @() }
  $patterns = @(
    "BookLauncher starting: tfs=",
    "FRONTIER EXIT CONTRACT IS ON",
    "SPREAD-GEOMETRY FLOOR IS ON"
  )
  return @(Get-Content -LiteralPath $path -Tail 5000 | Where-Object {
    $line = $_
    @($patterns | Where-Object { $line.Contains($_) }).Count -gt 0
  } | ForEach-Object { "$_" })
}

Mark "pre-supervisor"
$supervisorPath = Join-Path $repo "scripts\run_book_supervisor.ps1"
$supervisorText = Get-Content -LiteralPath $supervisorPath -Raw
$booksStart = $supervisorText.IndexOf('$books = @(')
if ($booksStart -lt 0) {
  throw "cannot locate literal `$books block in host supervisor"
}
$booksEnd = $supervisorText.IndexOf('function Test-BookRunning', $booksStart)
if ($booksEnd -le $booksStart) {
  throw "cannot locate literal `$books block in host supervisor"
}
$booksBlock = $supervisorText.Substring($booksStart, $booksEnd - $booksStart)
$bookKeys = @([regex]::Matches($booksBlock, '(?m)(?<key>[A-Za-z_][A-Za-z0-9_]*)\s*=') |
  ForEach-Object { "$($_.Groups['key'].Value)" } | Sort-Object -Unique)
$sha = [Security.Cryptography.SHA256]::Create()
try {
  $booksBlockHashBytes = $sha.ComputeHash([Text.Encoding]::UTF8.GetBytes($booksBlock))
  $booksBlockHash = ([BitConverter]::ToString($booksBlockHashBytes)).Replace('-', '').ToLowerInvariant()
} finally {
  $sha.Dispose()
}

Mark "pre-cim"
$allPython = @(Get-CimInstance Win32_Process -Filter "Name='python.exe'" |
  Where-Object { $_.CommandLine -like "*run_book.py*" })
$namespaces = @("operator_profile", "redacted_account_live_bee34003")
$books = @{}
foreach ($ns in $namespaces) {
  $books[$ns] = @($allPython | Where-Object { $_.CommandLine -like "*--namespace $ns*" } |
    ForEach-Object {
      @{
        pid = [int]$_.ProcessId
        creation_date = if ($_.CreationDate) { $_.CreationDate.ToUniversalTime().ToString("o") } else { $null }
        command_line = $_.CommandLine
      }
    })
}

Mark "pre-git"
$gitHead = (& git rev-parse HEAD).Trim()
$gitBranch = (& git branch --show-current).Trim()
Mark "pre-record"
$record = @{
  schema = "gtos.phase17.cl.host_pass_surface_capture.v1"
  captured_at_utc = (Get-Date).ToUniversalTime().ToString("o")
  repo_root = $repo
  git_branch = $gitBranch
  git_head = $gitHead
  files = @{
    supervisor = File-Record "scripts\run_book_supervisor.ps1"
    agent_config = File-Record "config\agent_config.yaml"
    redacted_account_profile = File-Record "config\profiles\redacted_account.yaml"
    run_book = File-Record "run_book.py"
  }
  supervisor_books_block = $booksBlock
  supervisor_books_block_sha256 = $booksBlockHash
  supervisor_book_hashtable_keys = $bookKeys
  books = $books
  firing_ledgers = @{
    operator_profile = Ledger-Record "operator_profile"
    redacted_account_live_bee34003 = Ledger-Record "redacted_account_live_bee34003"
  }
  log_proofs = @{
    operator_profile = Log-Proofs "shadow_logs\run_book_console.log"
    redacted_account_live_bee34003 = Log-Proofs "shadow_logs\run_book_fn_console.log"
  }
}
Mark "pre-json"
$record | ConvertTo-Json -Depth 12 | Set-Content -LiteralPath $OutFile -Encoding utf8
Mark "done"
Write-Output "WROTE READ-ONLY HOST CAPTURE: $OutFile"
