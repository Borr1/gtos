@echo off
cd /d host-local\redacted_host\repo
"C:\Users\MSI\Documents\ai-trading-agent\.venv-gtos\Scripts\python.exe" scripts\f5_harvest\f5_tripwires.py --repo-root host-local\redacted_host\repo >> pipeline_state\ultimate_book\operator\tripwires.log 2>&1
