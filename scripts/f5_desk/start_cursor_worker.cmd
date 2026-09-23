@echo off
cd /d host-local\redacted_host\repo
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "host-local\AppData\Local\cursor-agent\agent.ps1" worker start --name gtos-vps --worker-dir "host-local\redacted_host\repo" --idle-release-timeout 0 --verbose >> "host-local\redacted_host\repo\judgment\live\cursor-worker.log" 2>&1
