' GTOS Watchdog — hidden-window launcher
' Invoked by Task Scheduler task "GTOS_Watchdog" on the configured live
' supervision cadence. Current live default: every 1 min, with Task Scheduler
' enforcing a bounded execution time so a stuck run cannot block supervision.
' Purpose: run watchdog.bat with no visible console window.
'
' Run(strCmd, intWindowStyle, bWaitOnReturn)
'   intWindowStyle = 0  -> hidden
'   bWaitOnReturn  = True -> wait until watchdog.bat exits
'                           (so Task Scheduler reports the task as running
'                            for the full duration rather than completing instantly)
Set WshShell = CreateObject("WScript.Shell")
WshShell.Run """C:\Users\MSI\Documents\ai-trading-agent\scripts\watchdog.bat""", 0, True
Set WshShell = Nothing
