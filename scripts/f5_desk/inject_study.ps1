$ErrorActionPreference='Continue'
$src='host-local\gtos-ops\cursor-chair\WEEK_STUDY_PROMPT.md'
Copy-Item -Force $src 'host-local\Desktop\WEEK_STUDY_PROMPT.md'
Copy-Item -Force $src 'host-local\redacted_host\repo\judgment\live\cursor-mill\WEEK_STUDY_PROMPT.md'
$inbox='host-local\redacted_host\repo\judgment\live\cursor-mill\inbox.jsonl'
$line='{"ts":"2026-09-01T22:45:00Z","seat":"owner","kind":"study","priority":true,"word":"WEEK_STUDY","note":"Owner 05:44 ICT: stop-not-flatten. Read WEEK_STUDY_PROMPT.md. Dump EVERYTHING you learned this week, limits, missed objects, repairs. Write Desktop\\WEEK_STUDY.md and cursor-mill\\WEEK_STUDY.md. Then keep sitting. Do not flatten."}'
Add-Content -Path $inbox -Value $line -Encoding UTF8
Write-Output 'inbox appended'
Get-Item $src,'host-local\Desktop\WEEK_STUDY_PROMPT.md' | Format-List FullName,Length,LastWriteTime
Write-Output '---chats---'
Get-ChildItem 'host-local\.cursor\chats' -Directory -ErrorAction SilentlyContinue | Select-Object -First 8 Name,LastWriteTime
Write-Output '---cli sessions---'
Get-ChildItem 'host-local\.cursor' -Recurse -Filter '*session*' -ErrorAction SilentlyContinue | Select-Object -First 10 FullName,LastWriteTime
