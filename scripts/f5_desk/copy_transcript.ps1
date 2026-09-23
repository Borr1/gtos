$ErrorActionPreference='Continue'
$t = 'host-local\.cursor\projects\C-Users-Administrator-redacted_host-repo\agent-transcripts'
Write-Output '=== transcripts ==='
Get-ChildItem $t -Recurse -File -ErrorAction SilentlyContinue | Sort-Object LastWriteTime -Descending | Select-Object -First 15 FullName,Length,LastWriteTime | Format-Table -AutoSize -Wrap
Write-Output '=== chat jsonl sizes ==='
Get-ChildItem 'host-local\.cursor\chats\f75e6b2678e9890587586781bca68d9f' -Recurse -File | Sort-Object Length -Descending | Select-Object -First 15 FullName,Length,LastWriteTime | Format-Table -AutoSize -Wrap
