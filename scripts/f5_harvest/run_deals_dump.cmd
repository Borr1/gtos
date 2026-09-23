@echo off
cd /d host-local\redacted_host\repo
"C:\Users\MSI\Documents\ai-trading-agent\.venv-gtos\Scripts\python.exe" scripts\f5_harvest\dump_f5_deals.py --out pipeline_state\ultimate_book\operator >> pipeline_state\ultimate_book\operator\deals_dump.log 2>&1
