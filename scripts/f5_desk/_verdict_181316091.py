import json, os, subprocess, sys
REPO = r"host-local\redacted_host\repo"
mem = [
 "close 181316091 XAUUSD LONG dsp_descending_lows_accepted exit_class=orig_stop breach=false: entry 4465.77 20:46 ICT, orig SL 4459.21 / TP 4479.22, exit 4459.06 on broker SL (deal 169934270, [sl 4459.21]) 20:48 ICT, held 2m18s, -147.62 ~ -0.98R unit150; orig never moved, no chair touch",
 "XAUUSD flat after three dsp_descending_lows_accepted orig_stop closes today: 181295784 -150.72 (SL 4481.60), 181316091 -147.62 (SL 4459.21), 181349120 -150.20 (SL 4472.40) - same tag stopped three times in ~80m on gold; isolated re-entry after 15m still wanted, spent gold 180717112 stays spent, no remint",
 "book-event webhook delivery ran ~80m late: candidate for 181316091 arrived 15:06Z for a 13:46Z fill that had already stopped at 13:48Z - chair labelled from broker deals, not from the payload; candidate itself dead on arrival, no hold (no Warsh HIGH in T-15..T+60, next NFP 2026-09-04, and no three same-direction correlated names carrying gold)",
]
payload = {"verdicts": [], "manage": [], "memory": mem}
p = subprocess.run([sys.executable, REPO + r"\scripts\f5_desk\write_inbox_verdict.py", "--stdin"],
                   input=json.dumps(payload), capture_output=True, text=True, cwd=REPO,
                   env={**os.environ, "PYTHONPATH": REPO})
print("RC", p.returncode)
print(p.stdout.strip())
print(p.stderr.strip()[-1500:])
