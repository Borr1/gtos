$ErrorActionPreference='Continue'
$mill='host-local\redacted_host\repo\judgment\live\cursor-mill'
if (-not (Test-Path "$mill\WEEK_STUDY_PROMPT.md")) {
  Copy-Item -Force 'host-local\gtos-ops\cursor-chair\WEEK_STUDY_PROMPT.md' "$mill\WEEK_STUDY_PROMPT.md"
}
$wake = @{
  ts = (Get-Date).ToUniversalTime().ToString('o')
  kind = 'study'
  path = 'host-local\gtos-ops\cursor-chair\WEEK_STUDY_PROMPT.md'
  word = 'Read WEEK_STUDY_PROMPT.md. Dump WEEK_STUDY.md to Desktop, gtos-ops\cursor-chair, and cursor-mill. Do not flatten. Keep sitting after.'
} | ConvertTo-Json -Compress
Set-Content -Path "$mill\chair_wake.json" -Value $wake -Encoding UTF8
Write-Output 'wake written'
Get-Item "$mill\WEEK_STUDY_PROMPT.md","$mill\inbox.jsonl","$mill\chair_wake.json" | Format-Table Name,Length,LastWriteTime
Write-Output '---inbox last---'
Get-Content "$mill\inbox.jsonl" -Tail 3
Write-Output '---agent 11956---'
Get-Process -Id 11956 -ErrorAction SilentlyContinue | Format-List Id,ProcessName,StartTime
$agent = 'host-local\AppData\Local\cursor-agent\versions\2026.08.31-4057e58\cursor-agent.exe'
if (-not (Test-Path $agent)) {
  $agent = (Get-ChildItem 'host-local\AppData\Local\cursor-agent\versions' -Directory | Sort-Object LastWriteTime -Descending | Select-Object -First 1).FullName + '\cursor-agent.exe'
}
Write-Output "agent=$agent"
$prompt = @'
OWNER STUDY. You are the VPS F5 Cursor chair. Read host-local\gtos-ops\cursor-chair\WEEK_STUDY_PROMPT.md and host-local\gtos-ops\cursor-chair\CHAIR.md. Read judgment\live\cursor-mill\ (inbox, chair_last, bets, x_since, WEEK_STUDY_PROMPT). Read MT5 sit if needed. Dump EVERYTHING you learned this week: judgments, missed objects, environment limits, what you could not do, candidate/trade/shadow notes, BE/trail/take-cut, dual-chair with Grok, webhook lag, -$1500 new-risk, US30 re-entry chain, gold 180274922 chair-take vs TP 4428. Write host-local\Desktop\WEEK_STUDY.md AND host-local\redacted_host\repo\judgment\live\cursor-mill\WEEK_STUDY.md AND host-local\gtos-ops\cursor-chair\WEEK_STUDY.md. Do NOT flatten. Do NOT remint. Do NOT kill the sitting agent. Then stop.
'@
$log = 'host-local\gtos-ops\cursor-chair\week_study_agent.log'
$arg = @('--print','--force','--yolo','--trust','--workspace','host-local\redacted_host\repo','--model','cursor-grok-4.6-xhigh',$prompt)
$p = Start-Process -FilePath $agent -ArgumentList $arg -RedirectStandardOutput $log -RedirectStandardError ($log + '.err') -PassThru -WindowStyle Hidden
"started pid=$($p.Id) log=$log"
Get-Content $log -Tail 5 -ErrorAction SilentlyContinue
