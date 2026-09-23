# KB — Cycle 24: clean_3 sleeves are cell-selection-suspect → honest correction of the cycle-8 "+14%"

Following cycle-23's discovery (substrate-cell-selected sleeves don't survive walk-forward selection), I
audited the book's 3 clean_3 substrate-derived sleeves. **Result: they carry the cell-selection-leak
signature, and the cycle-8 "+14% Sharpe" was substantially their selection-glow.**

## The clean_3 audit (per-split daily-R, the train-robustness lens)
| sleeve (conv) | train ≤2021 | WF 22-24 | sealed 25+ | read |
|---|---|---|---|---|
| sub_mid_dn_revert (0.20) | **−0.023 / n114** | +0.039 | +0.071 | **TRAIN-NEGATIVE** = loses before its selection window, wins after = leak signature |
| vp_euidx_pocgrav (0.30) | n=0 (no pre-2022) | +0.096 | +0.032 | no clean holdout; thin edge, in-window only |
| sub_xvol_pullback (0.45) | +0.625 / n15 | **−0.486 / n5** | +0.546 | WF-NEGATIVE + tiny n = unstable |
| (contrast) metals_core | +0.363 / n34 | +0.517 | +0.947 | genuinely TRAIN-ROBUST (the real edge) |

## The MC book correction (vol-matched locked MC, @1.25%)
- Bare W7 11-sleeve (cycle-1 baseline): **Sharpe 0.1446**.
- Cycle-8 refreshed (drop 2 decaying, +equity, KEEP clean_3): 0.1649 / 2.46%/mo.
- **Conservative honest (drop 2 decaying + 3 clean_3, +equity): 0.1460 / 2.18%/mo / P(pass) 0.9959 / 0% breach.**

**Dropping the suspect clean_3 returns the book to ≈ the bare baseline (0.146 vs 0.1446).** So the
genuinely-robust session change — add the certified equity sleeve, drop the 5 weak/suspect sleeves (2
decaying + 3 clean_3) — nets to ≈ NEUTRAL Sharpe. The +14% headline was largely clean_3 selection-window
glow (part of the same 3× regime-inflation the cycle-1 gauntlet flagged).

## HONEST DEPLOY RECOMMENDATION (revised, supersedes cycle-8's headline)
- **Recommended deploy = the CONSERVATIVE book**: the train-robust core (metals_core, metals_softband,
  crypto, energy_agri, fx_jpy, fx_jpy_ny) + `us_equity_momentum_long` @0.35×, DROP the 2 decaying
  (metals_ob_micro, idxrev) AND the 3 clean_3 (sub_xvol_pullback, vp_euidx_pocgrav, sub_mid_dn_revert).
  ≈ **0.146 daily Sharpe, ~2.2%/mo @1.25%, P(pass) 0.996, 0% breach.**
- The clean_3-included book (0.165 / 2.46%) is an OPTIMISTIC upper bound — its extra Sharpe is selection-glow
  and should NOT be sized to.
- This is fully consistent with the cycle-1 audit's honest band (~1.8–2.2%/mo). **The session did NOT
  materially raise the honest Sharpe.** Its value is: (1) the complete honest validation/edge-factory
  machine, (2) the one genuinely-certified new sleeve (equity), (3) KNOWING that 5 of the original 11
  sleeves are weak/decaying/selection-suspect — i.e. a cleaner, more honest, more defensible book at the
  same honest return.

## The meta-lesson
The cycle-8 refresh itself was, in part, fooled by the clean_3 selection-glow — the diversifier gate
credited their in-sample contribution. Only the cycle-23 walk-forward-selection lens (applied here) exposed
it. This is exactly why the machine now MANDATES walk-forward selection for selection-derived sleeves
(edge_factory.py). Honest construction means correcting your own prior cycle when a better control reveals
the truth — which is what this cycle did.
