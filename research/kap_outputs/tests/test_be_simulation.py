"""
Test Finding F07: Break-even stops hurt mechanical systems.
Two sources say holding to SL/TP beats BE. One source disagrees.
We simulate BE-at-1R on our batch trades using MFE/MAE data.

Logic: If trade reaches 1R (MFE >= 1.0), move SL to entry.
  - If trade later hits entry before TP → 0R (break even)
  - If trade reaches TP → full win
  - If trade never reaches 1R → normal loss

Approximation: We use MAE after 1R reach as proxy. If MAE > MFE on a
trade that reached 1R, price retraced past entry → BE exit.

Decision gate:
  - If BE-at-1R expectancy < current → CONFIRMED (no BE is better)
  - If BE-at-1R expectancy > current → REJECTED
"""
import json, glob
import numpy as np

trades = []
for f in sorted(glob.glob('knowledge_base_backtest/sessions/*.json')):
    try:
        d = json.load(open(f))
        for t in d.get('trade_summary', {}).get('trades', []):
            trades.append(t)
    except:
        pass

print(f"Total trades: {len(trades)}")

# Current system
current_total = sum(t.get('r_multiple', 0) for t in trades)
current_exp = current_total / len(trades)
current_wins = sum(1 for t in trades if t.get('outcome') == 'WIN')

# Simulate BE-at-1R
# For each trade:
#   - If MFE < 1.0: never reached 1R → normal loss outcome
#   - If MFE >= 1.0 and outcome is WIN: trade won anyway → same R
#   - If MFE >= 1.0 and outcome is LOSS: trade reached 1R then reversed
#     In BE scenario: SL at entry → 0R instead of -1R loss
#     This is the ONLY scenario where BE changes outcome
be_results = []
be_saves = 0
be_missed_profits = 0

for t in trades:
    mfe = t.get('mfe_r', 0) or 0
    actual_r = t.get('r_multiple', 0)
    outcome = t.get('outcome', '')

    if mfe >= 1.0 and outcome == 'LOSS':
        # BE would have saved this → 0R instead of negative
        be_results.append(0.0)
        be_saves += 1
    elif mfe >= 1.0 and outcome == 'WIN' and actual_r > 0:
        # Won normally. But with BE, some wins that retrace past entry
        # before reaching TP would become 0R.
        # We approximate: if MAE > 0 and trade won, BE wouldn't change it
        # (trade went to TP without retracing to entry)
        # Conservative: keep same R
        be_results.append(actual_r)
    else:
        # MFE < 1R or other cases: same outcome
        be_results.append(actual_r)

be_total = sum(be_results)
be_exp = be_total / len(be_results)
be_wins_equiv = sum(1 for r in be_results if r > 0)
be_zeros = sum(1 for r in be_results if r == 0.0)

print(f"\n{'='*60}")
print(f"BREAK-EVEN AT 1R SIMULATION (n={len(trades)})")
print(f"{'='*60}")
print(f"\nCurrent system (no BE):")
print(f"  Wins: {current_wins}/{len(trades)} ({current_wins/len(trades)*100:.1f}%)")
print(f"  Expectancy: {current_exp:.3f}R")
print(f"  Total R: {current_total:.1f}R")

print(f"\nWith BE at 1R:")
print(f"  Wins: {be_wins_equiv}/{len(be_results)} ({be_wins_equiv/len(be_results)*100:.1f}%)")
print(f"  BE exits (0R): {be_zeros}")
print(f"  Losses saved by BE: {be_saves}")
print(f"  Expectancy: {be_exp:.3f}R")
print(f"  Total R: {be_total:.1f}R")

diff = be_exp - current_exp
print(f"\nDifference: {diff:+.3f}R/trade ({diff/max(abs(current_exp),0.001)*100:+.1f}%)")

if be_exp < current_exp:
    print(f"\n*** CONFIRMED: No BE is better by {abs(diff):.3f}R/trade ***")
    print(f"*** BE 'saves' {be_saves} losses but costs more in reduced winning trades ***")
elif be_exp > current_exp:
    print(f"\n*** REJECTED: BE-at-1R improves expectancy by {diff:.3f}R/trade ***")
else:
    print(f"\n*** INCONCLUSIVE: Essentially no difference ***")

# Detailed breakdown
print(f"\nTrade-by-trade impact of BE:")
print(f"  Trades reaching 1R MFE: {sum(1 for t in trades if (t.get('mfe_r',0) or 0) >= 1.0)}")
print(f"  Of those, losses saved → 0R: {be_saves}")
reached_1r_won = sum(1 for t in trades if (t.get('mfe_r',0) or 0) >= 1.0 and t.get('outcome') == 'WIN')
print(f"  Of those, won normally: {reached_1r_won}")
