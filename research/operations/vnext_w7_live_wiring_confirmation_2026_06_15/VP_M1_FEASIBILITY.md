# vp_euidx_pocgrav — M1 Feasibility Correction

Date: 2026-06-15. The build-spec flagged vp_euidx_pocgrav as a HARD blocker ("live H4 feed has no M1
volume"). Probing the live terminal corrects this: it is an ARCHITECTURE gap, not a DATA gap.

## Live probe result (FTMO, `.tools/probe_m1_volume_feasibility.py`)

```
GER40  GER40.cash  M1 bars=20000 span~20.9d  first=2026-05-25  last=2026-06-15  tick_volume>0: 20000/20000 (100%)  real_volume>0: 0  distinct UTC days: 16
UK100  UK100.cash  M1 bars=20000 span~23.9d  first=2026-05-22  last=2026-06-15  tick_volume>0: 20000/20000 (100%)  real_volume>0: 0  distinct UTC days: 16
```

The live feed supplies M1 bars with non-zero **tick_volume** (~16 trading days deep) for both EU index
symbols. `real_volume` is 0 — normal for CFDs. The route engine uses tick volume:
`volume_profile.py:56` — *"v is TICK VOLUME (the standard FX/CFD volume proxy)"*. So the data the sleeve
needs IS available live.

## Corrected status

vp_euidx_pocgrav is **buildable from the live feed**, not blocked. Required work (medium):
1. M1-fetch seam: the bar_provider/engine must fetch M1 (with tick_volume) for vp symbols, in addition
   to the H4 decision bars. The current engine fetches a single timeframe per sleeve.
2. Vendor `volume_profile.py` (load_m1 adapted from CSV to the live M1 fetch, daily_profiles,
   build_day_profile, _value_area, _find_nodes, prior_profile_at, nearest_node_state) — pure compute
   except the M1 source.
3. Correct warmup: 200 H4 + ≥1 prior full UTC day of M1 (ideally ~20 days for the prior-20-day median
   bin-width). 16 days are present now and accrue forward.

## Caveats (unchanged)

- Edge confidence is forward-only-flagged (route M1 history since 2024; thin validation). conf 0.30,
  cluster `volprofile`, on_surface GER40/UK100 only.
- 16 distinct days is near the route's prior-20-day bin-width window; the first ~4 sessions use a
  shorter median. Acceptable and self-correcting as M1 accrues.

## Net

No sleeve in the 11-sleeve book is impossible from the live FTMO feed. The full book is buildable:
1-3 (substrate x2 + ob_micro) on the existing H4 feed (in progress); 4-5 (JPY) need an M15+session seam;
6 (vp) needs an M1+volume seam + volume_profile vendoring. Whether to build the M1 path now vs. defer is
a priority call given vp's forward-only edge flag — surfaced for the owner.
