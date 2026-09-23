---
name: vps-python
description: Run Python on the GTOS Windows VPS over SSH. Use whenever a host read or patch would otherwise be a PowerShell one-liner.
---

# VPS Python

`ssh -o ControlMaster=no -o ControlPath=none gtos-vps`. Remote shell is PowerShell. The local shell eats `$`. Do not send a remote one-liner that contains `$`.

Write a `.py` file, `scp` it to `host-local\AppData\Local\Temp\`, run `C:\Users\MSI\Documents\ai-trading-agent\.venv-gtos\Scripts\python.exe`. Host tree: `host-local\redacted_host\repo`.
