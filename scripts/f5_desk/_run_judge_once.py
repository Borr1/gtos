import os, sys
os.chdir(r"host-local\redacted_host\repo")
sys.path.insert(0, r"host-local\redacted_host\repo")
from scripts.f5_desk.judge_daemon import main
sys.argv = ["judge_daemon.py", "--once", "--max-calls-per-day", "200"]
raise SystemExit(main())
