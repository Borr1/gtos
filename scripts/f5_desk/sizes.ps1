$ErrorActionPreference='Continue'
$t = 'host-local\.cursor\projects\C-Users-Administrator-redacted_host-repo\agent-transcripts'
Get-ChildItem $t -Recurse -Filter *.jsonl | ForEach-Object { '{0,12}  {1}  {2}' -f $_.Length, $_.LastWriteTime.ToString('yyyy-MM-dd HH:mm:ss'), $_.FullName }
Write-Output '---meta---'
Get-ChildItem 'host-local\.cursor\chats\f75e6b2678e9890587586781bca68d9f' -Recurse -Filter meta.json | ForEach-Object { $_.FullName; Get-Content $_.FullName -Raw }
