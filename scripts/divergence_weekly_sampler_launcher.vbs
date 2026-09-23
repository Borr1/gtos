' GTOS Divergence Weekly Sampler — hidden-window launcher.
' Invoked by Task Scheduler task "GTOS_DivergenceWeeklySampler" weekly.
' Purpose: run scripts/divergence_weekly_sample.py with no visible console,
' writing all stdout/stderr to logs/divergence_sampler.log.
'
' Run(strCmd, intWindowStyle, bWaitOnReturn)
'   intWindowStyle = 0  -> hidden
'   bWaitOnReturn  = True -> wait until python exits (so Task Scheduler
'                           reports the run as finished with an exit code)
Set WshShell = CreateObject("WScript.Shell")

ProjectDir = "C:\Users\MSI\Documents\ai-trading-agent"
PythonExe  = "C:\Python313\python.exe"
Script     = "scripts\divergence_weekly_sample.py"
LogFile    = ProjectDir & "\logs\divergence_sampler.log"

' Use cmd.exe to cd into the project dir + append stdout/stderr to the log.
' Keep git staging/commit disabled unless a human explicitly reruns with --git.
Cmd = "cmd.exe /c cd /d """ & ProjectDir & """ && """ & PythonExe & """ " & Script & " --no-git >> """ & LogFile & """ 2>&1"

WshShell.Run Cmd, 0, True
Set WshShell = Nothing
