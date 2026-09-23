# P0 shadow historical prove failure

- Verdict: FAIL (script failed immediately; no prove result produced)
- Command: `.venv\Scripts\python.exe scripts\run_p0_shadow_hooks_historical_prove.py --log-dir research\warroom_20260920\p0-shadow --score-out research\warroom_20260920\p0-shadow\scorecard.json --receipt-out research\warroom_20260920\p0-shadow\receipt.json`
- Error: `SyntaxError: invalid non-printable character U+FEFF` while parsing `src\judgment\policy_c_admit.py` line 1.
- No scorecard or receipt was invented or written.
- APPLY flags were not set; no order/remint/place/send performed.
