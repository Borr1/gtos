# Chair VPS entry. Delegates to scripts/f5_desk/vps_start_workers.ps1.
$ErrorActionPreference = "Stop"
$desk = Join-Path $PSScriptRoot "..\..\..\scripts\f5_desk\vps_start_workers.ps1"
& $desk @args
