#!/bin/zsh
cd /Users/borr/GTOSActive/worktrees/wave19-broad-forensic-20260801/docs/audits/fable5-vision-audit-20260725/phase19/receipts/pbg
for M in 202510 202511 202512 202604 202605; do
  python3 pbg_run.py --month $M --min-rr 1.5 --workers 4 --out /tmp/f1/roster_$M > /tmp/f1/roster_$M.log 2>&1
  echo "DONE $M $(date)" >> /tmp/f1/roster_progress.txt
done
echo "ALLDONE" >> /tmp/f1/roster_progress.txt
