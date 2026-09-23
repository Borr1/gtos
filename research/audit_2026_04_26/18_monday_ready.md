# AUDIT 18: MONDAY-READY (end-to-end checklist walkthrough)

## CRITICAL OPERATIONAL ISSUES

1. Pre-deploy checklist references HEAD `6b85287` (session 39 close); actual current HEAD is `df70694`. Step 2 will fail.

2. Watchdog `-Action stop-all` and `-profile ftmo` parameters DO NOT EXIST — checklist instructs commands that won't work. Need manual taskkill + python run_agent.py commands.

3. C.3 SPRT halt manual-mode workflow READY (CLI command + Telegram template).

4. 7-instrument vs 5-instrument `fn_smoke_trade.py` drift (XAGUSD/NAS100 not in DEFAULT_SYMBOLS).

5. `flatten_positions.py` referenced in emergency steps but DOES NOT EXIST.

6. operator_decision_playbook v3 listed in CLAUDE.md but file is v1 from Apr 11 (41 scenarios assume 5-instrument fleet).

## Total
10 issues ranked. Top 5 require pre-Monday fix.
