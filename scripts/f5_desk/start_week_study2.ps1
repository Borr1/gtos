$ErrorActionPreference='Continue'
$cmd='host-local\AppData\Local\cursor-agent\versions\2026.08.31-4057e58\cursor-agent.cmd'
$ws='host-local\redacted_host\repo'
$log='host-local\gtos-ops\cursor-chair\week_study_agent.log'
$err='host-local\gtos-ops\cursor-chair\week_study_agent.err'
$promptFile='host-local\gtos-ops\cursor-chair\WEEK_STUDY_PROMPT.md'
$wrapper='host-local\gtos-ops\cursor-chair\week_study_run.cmd'
$inner = @"
@echo off
cd /d $ws
"$cmd" --print --force --yolo --trust --sandbox disabled --approve-mcps --workspace $ws --model cursor-grok-4.6-xhigh "OWNER STUDY now. Read $promptFile then dump WEEK_STUDY.md to Desktop, gtos-ops\cursor-chair, and $ws\judgment\live\cursor-mill. Keep sitting agent 11956 alive. Do not flatten. Do not remint. Then exit."
"@
Set-Content -Path $wrapper -Value $inner -Encoding ASCII
Start-Process -FilePath 'cmd.exe' -ArgumentList '/c',$wrapper -RedirectStandardOutput $log -RedirectStandardError $err -PassThru -WindowStyle Hidden | ForEach-Object { "started pid=$($_.Id)" }
Start-Sleep -Seconds 3
Write-Output '---log---'
if (Test-Path $log) { Get-Content $log -Tail 20 } else { 'no log yet' }
Write-Output '---err---'
if (Test-Path $err) { Get-Content $err -Tail 20 } else { 'no err yet' }
