"""Is `entry_trigger_level_on_tape`'s docstring right? Decide it with the module's own function.

Claim under test (quote_side.py:216-224): "on a BID tape a long's level is reached one spread
EARLY in tape terms ... it is the reason a limit book fills more often than an unshifted walk
believes."
"""
import sys; sys.path.insert(0, "/Users/borr/GTOSActive/worktrees/wave19-broad-forensic-20260801")
from src.research_infra.walkforward.quote_side import BarQuote, entry_trigger_level_on_tape as T

S = 1.0
rows = []
for name, direction, level, approach in (
    ("BUY LIMIT  (POI demand zone, market falling INTO it)",  +1, 100.0, "from above"),
    ("BUY STOP   (breakout, market rising INTO it)",          +1, 100.0, "from below"),
    ("SELL LIMIT (POI supply zone, market rising INTO it)",   -1, 100.0, "from below"),
    ("SELL STOP  (breakdown, market falling INTO it)",        -1, 100.0, "from above"),
):
    tape = T(level, direction, S, BarQuote.BID)
    if approach == "from above":
        verdict = ("LATER  / fills LESS often" if tape < level else
                   "EARLIER / fills MORE often" if tape > level else "unchanged")
    else:
        verdict = ("EARLIER / fills MORE often" if tape < level else
                   "LATER  / fills LESS often" if tape > level else "unchanged")
    rows.append((name, level, tape, approach, verdict))

w = max(len(r[0]) for r in rows)
print(f"{'order type':{w}s}  level  tape-trigger  approach     vs the unshifted walk")
for n, l, t, a, v in rows:
    print(f"{n:{w}s}  {l:5.1f}  {t:12.1f}  {a:11s}  {v}")
print()
print("The module's own test pins T(100,+1,1,BID) == 99.0 and T(100,-1,1,BID) == 100.0.")
print("A buy LIMIT therefore needs one MORE spread of decline: it fills LESS often, not more.")
print("The function is correct; the sentence that generalises it is not, and the broad V4 POI")
print("families (fvg_fill, ob_retest, breaker_re_entry) are exactly the buy/sell-LIMIT case.")
