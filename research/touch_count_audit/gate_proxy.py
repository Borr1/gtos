"""Compare gate semantics (max overlap touch) to logger semantics (nearest opp OB).

The A1 logger's `h1_opp_ob_touch_long/short` ranks by nearest entry-edge proximity.
The actual gate uses max(touch_count) across OBs whose [low, high] contains
entry_price. They differ when:
  (a) entry_price overlaps multiple OBs of correct direction, AND
  (b) the nearest-by-edge OB has a different touch_count than the max-touch OB.

The logger also captures `mso_h1_ob_touch_counts` (a list of all unmitigated OB
touch_counts in the H1 timeframe, regardless of direction). This is too
inclusive — the gate filters by direction. But max(this list) bounds the
gate's potential reach.

Bounds for A1:
  - upper-bound on gate reach: # CANDs where MAX(mso_h1_ob_touch_counts) >= 2
  - lower-bound on gate reach: # CANDs where direction-aware h1_opp_ob_touch >= 2
"""
import json
from collections import Counter

recs = []
with open('research/phase1_full_extraction/merged_data.jsonl') as f:
    for l in f:
        recs.append(json.loads(l))

filled = [r for r in recs if r.get('out_outcome') in ('WIN', 'LOSS', 'BE')]


def get_dir_touch(r):
    direction = r.get('out_direction') or r.get('ai_direction_evaluated')
    if direction == 'LONG':
        return r.get('h1_opp_ob_touch_long', -1)
    elif direction == 'SHORT':
        return r.get('h1_opp_ob_touch_short', -1)
    return r.get('h1_opp_ob_touch', -1)


print(f"A1 filled: {len(filled)}")

# Compare logger's direction-aware touch to max(mso_h1_ob_touch_counts)
table = []
discrepancies = 0
for r in filled:
    dir_t = get_dir_touch(r)
    tc_list = r.get('mso_h1_ob_touch_counts') or []
    max_t = max(tc_list) if tc_list else 'no_obs'
    is_disc = (dir_t != max_t) if isinstance(max_t, int) else False
    if is_disc:
        discrepancies += 1
    table.append((dir_t, max_t, is_disc))

# Distribution
print("\n(dir_aware_touch, max_h1_obs_touch_in_mso) — gate uses MATCHED OB only")
combos = Counter((d, m) for d, m, _ in table)
for (d, m), c in sorted(combos.items(), key=lambda x: (str(x[0][0]), str(x[0][1]))):
    print(f"  dir_t={d}, max_mso_t={m}: {c}")

# Now bound gate reach
print("\n--- Bound gate's reach ---")
gate_lower = sum(1 for d, _, _ in table if isinstance(d, int) and d >= 2)
gate_upper_ish = sum(1 for d, m, _ in table if (isinstance(d, int) and d >= 2) or
                     (isinstance(m, int) and m >= 2 and (not isinstance(d, int) or d < 2)))
print(f"Gate's lower-bound reach (dir_t>=2): {gate_lower}/{len(filled)} = {gate_lower/len(filled)*100:.1f}%")
print(f"Gate's upper-bound reach (dir_t>=2 OR max_mso_t>=2 — overcounts): {gate_upper_ish}/{len(filled)} = {gate_upper_ish/len(filled)*100:.1f}%")

# What's the realized R for the upper-bound?
upper_bound_rows = [r for r, (d, m, _) in zip(filled, table)
                    if (isinstance(d, int) and d >= 2) or
                       (isinstance(m, int) and m >= 2 and (not isinstance(d, int) or d < 2))]
ub_r = [r.get('out_r_multiple', 0) for r in upper_bound_rows]
ub_w = sum(1 for r in upper_bound_rows if r.get('out_outcome') == 'WIN')
print(f"\nUpper-bound rejected set realized: n={len(upper_bound_rows)}, "
      f"WR={ub_w/len(upper_bound_rows)*100 if upper_bound_rows else 0:.1f}%, "
      f"Exp={sum(ub_r)/len(ub_r) if ub_r else 0:+.3f}R, totR={sum(ub_r):+.2f}")

# Direction-aware (lower bound)
lower_bound_rows = [r for r, (d, _, _) in zip(filled, table) if isinstance(d, int) and d >= 2]
lb_r = [r.get('out_r_multiple', 0) for r in lower_bound_rows]
lb_w = sum(1 for r in lower_bound_rows if r.get('out_outcome') == 'WIN')
print(f"Lower-bound rejected set realized: n={len(lower_bound_rows)}, "
      f"WR={lb_w/len(lower_bound_rows)*100 if lower_bound_rows else 0:.1f}%, "
      f"Exp={sum(lb_r)/len(lb_r) if lb_r else 0:+.3f}R, totR={sum(lb_r):+.2f}")

# Discrepancy rate
print(f"\nDiscrepancy rate (dir_t != max_mso_t, ignoring no_obs): "
      f"{discrepancies}/{len(filled)} = {discrepancies/len(filled)*100:.1f}%")

# Show the discrepancy table — when dir_t < 2 but max_mso_t >= 2 the gate may STILL reject
# IFF there's an overlapping OB at touch>=2 of correct direction. We can't tell from logger
# alone (no per-OB direction info logged), but this captures upper-bound uncertainty.
print("\nBreakdown — direction-aware says PASS but max_mso says might-reject:")
might_reject = [(d, m) for d, m, _ in table if (isinstance(d, int) and d < 2) and
                (isinstance(m, int) and m >= 2)]
print(f"  Cases dir_t<2 AND max_mso_t>=2: {len(might_reject)}")

# Show fields for one such case
for r, (d, m, _) in zip(filled, table):
    if (isinstance(d, int) and d < 2) and (isinstance(m, int) and m >= 2):
        print(f"\nSample case: dir_t={d}, max_mso_t={m}, "
              f"direction={r.get('out_direction')}, "
              f"outcome={r.get('out_outcome')}, "
              f"R={r.get('out_r_multiple', 0)}")
        print(f"  mso_h1_ob_touch_counts: {r.get('mso_h1_ob_touch_counts')}")
        break
