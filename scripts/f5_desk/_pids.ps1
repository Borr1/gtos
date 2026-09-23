Get-CimInstance Win32_Process -Filter "Name='python.exe'" |
  Where-Object { $_.CommandLine -match 'operator|ultimate_book.launcher|book_owner' } |
  ForEach-Object { '{0}|{1}' -f $_.ProcessId, $_.CommandLine.Substring(0,[Math]::Min(180,$_.CommandLine.Length)) }
