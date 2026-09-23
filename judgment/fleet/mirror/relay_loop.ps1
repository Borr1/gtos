while ($true) {
  & 'host-local\redacted_host\repo\.venv\Scripts\python.exe' 'host-local\redacted_host\repo\judgment\fleet\mirror\vps_relay_once.py' --live-dir 'host-local\redacted_host\repo\judgment\live' | Out-File -Append 'host-local\redacted_host\repo\judgment\fleet\mirror\logs\relay_loop.out.log'
  Start-Sleep -Seconds 30
}
