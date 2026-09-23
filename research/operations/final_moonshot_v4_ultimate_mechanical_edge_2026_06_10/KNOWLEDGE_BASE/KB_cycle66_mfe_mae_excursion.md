# KB cycle 66 — MFE/MAE excursion geometry of the deployed metals setup (FOUNDATION for the geometry program)

**Owner hypothesis (2026-06-15):** the deployed stops/targets are TOO FAR → trades take forever, give back
the move, returns small. Tested with DATA on the EXACT deployed FVG-retest setup (wave4 entry/gate/sign,
structural stop, 482 walk-forward in-regime trades, WF full R +0.2264). Leak-free, pessimistic intrabar,
train(≤2021)/OOS(2022+)/SEALED(2025+) reported. `CYCLE66_MFE_MAE_EXCURSION.json`.

## RESULT — the hypothesis is CONFIRMED on both counts, and STABLE across train/OOS/sealed.

**(1) The structural stop (1.0R) is WIDER than the edge needs.** Among RUNNERS (trades reaching ≥1R MFE,
the ones a stop must keep), the adverse excursion BEFORE they run is small:
- pre-peak MAE median **~0.37–0.44R**, p75 **~0.72–0.77R**, p90 **~0.90R**; ~60% never exceed 0.5R against.
- → ~90% of runners survive a stop at ~0.9R; ~75% survive ~0.7R. The 1.0R structural stop carries dead
  width. A tighter stop shrinks the R-denominator → the SAME favorable move becomes a larger R-multiple →
  faster relative target reach + better R:R. (STABLE: median 0.37/0.37/0.44 train/OOS/sealed.)

**(2) Far targets are mostly unreached; the move peaks FAST then reverses.**
- reach fractions (OOS): 0.5R **75%**, 1R **62%**, 1.5R **51%**, 2R **43%**, 3R **33%**, 4R **31%**.
- MFE median **~1.5R**; **bars-to-MFE median = 5** (~1 day at H4). A fixed 2R+ target misses the ~57% that
  peak near 1–1.5R and reverse — exactly the owner's "TP too far / doesn't hit / takes forever."

**(3) The honest counter-weight — a fat right tail carries the trend expectancy.** MFE mean **3.5–4.4R**,
p90 **10–14R**: a minority run very far. So the data does NOT say "use tight targets" — it says **tighter
stop + fast partial near the typical MFE (~1–1.5R) + a runner for the tail.** (The deployed STATE_D exit
already gestures at this; the question is whether the GEOMETRY is optimally placed — next cycles.)

## IMPLICATIONS (to test via the machine, train→sealed, trial-budget-counted — NOT to assume)
- **Stop:** tighten toward the runner pre-peak MAE p75–p90 (~0.7–0.9R structural, or MAE-quantile / swing /
  ATR-based). Net-EV/Sharpe must improve OOS+sealed (c50 warning: exit/stop selection is leak-prone).
- **Target:** scale-out (partial ~1–1.5R where reach is ~50–60%, runner for the p90 tail) vs the fixed 2R.
- **Entry:** can a tighter/confluence-gated entry cut the pre-peak MAE further (so the stop can be tighter)?
- **The R-denominator is the lever:** the edge's MFE in PRICE is fixed; shrinking the stop (R-unit) is what
  makes targets "closer" in R and trades faster — but only if the tighter stop doesn't cut too many runners.
  The data says there's real room (p90 pre-MAE 0.9R < 1.0R stop), but the exact level must be machine-validated.

## DISCIPLINE
This is MEASUREMENT only (no optimization → no leak). The geometry optimization that follows is the most
overfit-prone work in the program (c50: naive train-best exit OOS −0.19) → every variant goes through the
validation machine on the SEALED slice at the full trial budget, and the principal re-derives the winner.

**Files.** `CYCLE66_mfe_mae_excursion.py`, `KNOWLEDGE_BASE/validation/CYCLE66_MFE_MAE_EXCURSION.json`.
