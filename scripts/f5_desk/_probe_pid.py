import subprocess, sys
sys.stdout.reconfigure(encoding='utf-8')
code = r'''
$procs = Get-CimInstance Win32_Process
foreach ($p in $procs) {
  $cl = [string]$p.CommandLine
  if ($cl -like '*run_book.py*' -and $cl -like '*operator*') {
    Write-Output ('PID=' + $p.ProcessId + ' PPID=' + $p.ParentProcessId + ' CREATE=' + $p.CreationDate)
    Write-Output ('CL=' + $cl.Substring(0, [Math]::Min(280, $cl.Length)))
    Write-Output '---'
  }
}
'''
print(subprocess.check_output(['powershell','-NoProfile','-Command', code], text=True, encoding='utf-8', errors='replace')[:4000])
