# KB cycle 73 — VELOCITY of the deep target (resolves the owner's "trades take forever" concern)

The deep-target win (c71/c72) raises EV/trade but HOLDS LONGER (run to 6-8R or time out at maxbars=80). The
owner's ORIGINAL complaint was the opposite ("TP too far, takes forever, small returns"). Honest check: does
the higher EV compensate the longer hold? Computed mean R, mean bars-to-exit, and R-PER-BAR (EV velocity) per
target depth, both sleeves, SEALED. `CYCLE73_VELOCITY.json`.

## RESULT — the deep target is FASTER per unit time, not slower (R-per-bar RISES with depth).
METALS H4 (sealed n=181): 2R mean-R 0.227 / 11.3 bars / R-per-bar 0.0201 → 4R 0.449/16.3/0.0275 → 6R
0.598/20.1/0.0297 → 8R 0.820/22.1/**0.0371**. Holds ~2× longer but EV rises ~3.6× → R-per-bar nearly DOUBLES.
US_EQUITY D1 (sealed n=293): 3R 0.279/19.1/0.0146 → 6R 0.411/28.5/0.0144 (flat) → 8R 0.520/30.2/0.0172 → 10R
0.609/31.3/**0.0195**. Flat 3R→6R then rising; deeper is flat-to-better on velocity.

## INTERPRETATION (reconciles the owner's instinct with the data)
- The owner's instinct pointed at the right PROBLEM (the fixed target was suboptimal) but the data-correct fix
  is the OPPOSITE of "tighter": the 2R/3R target was too CLOSE — it capped the fat-tail runners. The "takes
  forever for small returns" feeling at 2R is because 2R has LOW EV (0.227) for its hold → low R-per-bar.
- The deep target produces MORE return per unit time (higher R-per-bar) AND more total EV AND is
  downside-neutral (c71) AND lifts the safe base to 2.0% (c71 sizing). It wins on every axis the owner cares
  about — return, velocity, risk.
- The ONLY tradeoff is WIN-RATE (0.42→0.23 at 8R: fewer, bigger winners) — a variance/psychology profile, not
  an EV or speed cost. The −1R downside is unchanged.

## DISPOSITION
Confirms the deep target on the velocity axis too — it is not a speed sacrifice, it is a speed GAIN. Strengthens
the c71/c72 deploy candidate. (The win-rate drop argues for the regime-conditional depth cell — shallower in
chop keeps more winners where the tail won't pay — now under test in wf_85847b95-57b.)

**Files.** `CYCLE73_velocity.py`, `KNOWLEDGE_BASE/validation/CYCLE73_VELOCITY.json`.


---
## CORRECTION (cycle 75): R-per-bar is the WRONG deployment metric. At vol-matched/iso-ruin the deep target is SLOWER, not faster (higher variance -> size down). See KB_cycle75.
