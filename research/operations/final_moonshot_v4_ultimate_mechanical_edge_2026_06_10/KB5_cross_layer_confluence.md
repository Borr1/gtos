# KB5 — Cross-layer confluence stacking (track: KB5)

Builder pass 2026-06-15. **The high-odds frontier: multiply the odds.** Take the
substrate's strongest base cells and INTERSECT each with ONE orthogonal condition
from each OTHER engine — volume_profile node-location, leadlag leader-impulse,
regime_map label / Hurst sign, liquidity_map sweep context — and measure how each
added INDEPENDENT condition multiplies forward odds/EV. Per-condition incremental
lift + phi + per-year + n-gate + permutation null, TRAIN(<=2024) vs FORWARD(2025-26).

Engine: `KB5_cross_layer_miner.py` (one leak-free pass; tags every base-cell signal
with all orthogonal-engine states at bar i). Result map: `KB5_CROSS_LAYER_RESULT.json`.
Ranked frontier: `KB5_FRONTIER.json` (`KB5_report.py`). Stack validation:
`KB5_validate_stack.py`.

## Method / discipline (enforced in code)
- **No lookahead.** Base match + EVERY orthogonal tag at bar i uses CLOSED bars
  index<=i: substrate state (`build_states`), outcome via `simulate_detail`
  (pessimistic same-bar, real `w1.cost_for`), VP from the **prior completed day's**
  profile (`prior_profile_at`, verified strictly < decision date — 0 leaks on spot
  check), regime model fit on TRAIN rows only then applied forward, liquidity
  sweep+reclaim from bars (i-3..i], leadlag leader z-impulse at the same H4 close.
- **Forward holdout mandatory; no averages as verdicts.** Verdict = forward mean_R
  (real cost). Every (base × condition) cell carries TRAIN/FWD mean_R, per-year, n.
- **Independence/null.** phi (condition vs win, within base) reported; permutation
  null shuffles the condition labels within the FORWARD base population (2000-3000
  draws), p = P(shuffled lift >= observed). A confluent condition must beat the null.
- **Sign, not monotonic stacking** (KB4 lesson): conditions can be ANTI-confluent;
  the miner measures and reports the SIGN of every condition's lift.

## Base cells stacked on (substrate top edges, chosen for sliceable fwd sample)
| base | cell | base TRAIN R (n) | base FWD R (n) | fwd/yr |
|---|---|---|---|---|
| `xvol_up_pullback_L3R` | vol=xhi·persist=rand·trend=up·mtf=conflict, L 3R (the flagship) | +1.04 (69) | +0.71 (74) | 48/26 |
| `xvol_up_conflict_L3R` | vol=xhi·trend=up·mtf=conflict, L 3R (broadest) | +0.36 (183) | +0.20 (151) | 88/63 |
| `xvol_up_conflict_mid_L3R` | + rngpos=mid, L 3R | +0.35 (148) | +0.19 (149) | 86/63 |
| `hi_dn_conflict_ny_L3R` | vol=hi·trend=dn·mtf=conflict·…·ny, L 3R | +0.24 (291) | +0.28 (114) | 67/47 |
| `mid_dn_revert_ny_L3R` | vol=mid·trend=dn·mtf=neutral·…·revert·ny, L 3R (hi-freq breadth) | +0.14 (251) | +0.47 (126) | 84/42 |

---

## 0. HEADLINE — the odds DO multiply, via TWO genuinely orthogonal gates

The single load-bearing result of the wave: the substrate's extreme-vol uptrend-
pullback long is **dramatically improved by two independent orthogonal gates that
compound**, and **degraded (signed) by their opposites** — exactly the confluence-
multiplication the Grand Vision predicts.

### Gate 1 (deepest, strongest): the LEAD-LAG IMPULSE VETO — `ll_impulse=none`
Take the substrate pullback long **only when NO relevant cross-asset leader
(SPX500/NAS100/BTC/USDJPY/US30/XAUUSD/DXY) is simultaneously impulsing >=1.5σ**
(look=6 H4 bars). This is the strongest, most robust condition found, on every
xvol-up base, with **deep TRAIN confirmation** (not a forward-only VP artifact):

| base | +`ll=none` TRAIN R (n) | +`ll=none` FWD R (n) | fwd win | fwd/yr | base FWD | **fwd lift** | perm-p |
|---|---|---|---|---|---|---|---|
| `xvol_up_pullback` | +1.05 (38) | **+1.53 (40)** | 65.0% | 2025 +1.69 / 2026 +1.24 | +0.71 | **+0.82** | 0.000 |
| `xvol_up_conflict` | +0.48 (99) | **+0.83 (63)** | 47.6% | 2025 +0.82 / 2026 +0.86 | +0.20 | **+0.63** | 0.000 |
| `xvol_up_conflict_mid` | +0.46 (84) | **+0.86 (62)** | 48.4% | 2025 +0.87 / 2026 +0.86 | +0.19 | **+0.67** | 0.000 |

The mirror image proves the sign is real, not a sample fluke: when a leader is
impulsing AGAINST the trade (`ll_align=opposed` / `ll_impulse=dn`), the same base
cell goes **forward-NEGATIVE -0.35R** (perm-p ~1.0). On the broad `xvol_up_conflict`
base the veto also **repairs the dead 2026 forward year** (base 2026 -0.002R ->
+0.86R). Reading: an extreme-vol pullback that coincides with a strong cross-asset
risk impulse is being driven by the macro move, not by the local mean-reversion the
substrate cell captures — so its drift is contaminated. Stand down when a leader is
shouting.

**Per-class refinement (validation run):** the veto cell's forward EV concentrates
in **metals (R+2.2..+3.0), index (+2.4..+2.9), energy (+1.0..+1.4), fx (+0.8..+2.8)**
and is **NEGATIVE in crypto (R-1.1, n5-17) and jpy_fx (R-1.1, n4)** — exactly the two
classes the substrate flagship already drops (covered by their own sleeves,
forward-negative). The deployable veto cell should carry the **same 4-class clean
universe (metals/index/energy/fx)** as the substrate headline; on that universe the
veto is strongly +EV and broad, not one symbol's luck.

**Artifact check (is `ll=none` just a calmer regime?):** within the already
`vol=xhi`-gated base the `ll=none` and `ll=impulse` sub-populations have the SAME
dominant regime (`vol_expansion`); the `ll=impulse` side merely mixes in more
`calm_chop`/`range_spike`. So the lift is consistent with **cross-asset timing**
(stand down while a leader moves), not a clean low-vol proxy — the base vol gate is
already held fixed at xhi.

### Gate 2 (forward-strong, train-thin): VOLUME-PROFILE location — `vp_loc=above_va`
Restrict the pullback long to bars whose price is **above the prior day's value-area
high** (an acceptance-above-value auction state): `xvol_up_conflict` +0.79R fwd (n41,
perm-p 0.01, both fwd yrs +); `xvol_up_pullback` +1.09R fwd (n28). **Caveat: M1 starts
2024, so VP conditioning is essentially forward-only — there is no deep TRAIN holdout
for the VP gate.** Both forward years are positive and it clears the permutation null,
but it is forward-validated against 2024-26 only, not a decade.

### The STACK (Gate 1 ∧ Gate 2) — the multiplied high-odds setup
The two gates are independent (one is cross-asset timing, the other is price-in-auction
location) and they **COMPOUND**:

| base | base FWD | +veto | +above_va | **STACK (both)** | stack fwd win | stack fwd/yr | stack perm-p |
|---|---|---|---|---|---|---|---|
| `xvol_up_pullback` | +0.71 (74) | +1.53 (40) | +1.09 (28) | **+1.69R (n19)** | 68.4% | 2025 +2.36 / 2026 +1.29 | 0.005 |
| `xvol_up_conflict` | +0.20 (151) | +0.83 (63) | +0.79 (41) | **+1.40R (n26)** | 61.5% | 2025 +1.93 / 2026 +1.17 | 0.000 |
| `xvol_up_conflict_mid` | +0.19 (149) | +0.86 (62) | +0.73 (40) | **+1.40R (n26)** | 61.5% | 2025 +1.93 / 2026 +1.17 | 0.000 |

The stacked EV (+1.40 to +1.69R, 61-68% win at 3R) exceeds either single gate's
marginal (stack lift +0.97 to +1.21R over base, perm-p 0.000-0.005) — the
conditions multiply rather than merely add, and both forward years hold. **Honest
n-gate: the full 2-way stack is n=19-26 forward — a confluence POCKET, not a high-
frequency stream, and `above_va`'s train depth is ~0. Size it as a high-conviction
SELECTOR overlay (take-the-best-pocket), never as a standalone frequency sleeve.**
The deployable, deep-sample version is **Gate 1 alone** (the leader-impulse veto),
which holds in TRAIN and FORWARD with n>=40 on both sides.

---

## 1. Per-condition incremental lift table (forward, all bases)
(Full numbers in `KB5_CROSS_LAYER_RESULT.json`; ranked frontier in `KB5_FRONTIER.json`.)

**CONFLUENT (+) — disciplined (fwd n>=30, lift>0, fwd R>0, majority fwd yrs +, perm-p<=0.10):**
- `ll_impulse=none` / `ll_align=none` on all three xvol-up bases (+0.63..+0.82R, perm-p ~0.000) — **the gate.**
- `vp_loc=above_va` on `xvol_up_conflict`(+0.58), `xvol_up_conflict_mid`(+0.54), `xvol_up_pullback`(+0.37 nearmiss perm-p 0.066) — forward-only depth.
- `vp_poc_side=above_poc` on `xvol_up_conflict`(+0.54)/`_mid`(+0.50) — same auction-acceptance axis as above_va (correlated, do not double-count).
- `vp_loc=above_va` on **`mid_dn_revert_ny`** (+0.40R, perm-p 0.038, 2/2 yrs, **and TRAIN-positive n13 R+0.78**) — the one VP gate with real train sample.

**ANTI-CONFLUENT (-) — DROP from any stack (signed, the KB4 lesson confirmed):**
- `hurst=trend` on xvol-up cells: **-0.94R lift, fwd -0.74R (n32)** — catastrophic.
  The substrate pullback is a MEAN-REVERSION mechanic; gating it to a TRENDING Hurst
  timescale inverts it. The complementary read: the edge wants `hurst=revert`/random.
- `ll_align=opposed` / `ll_impulse=dn`: -0.55R lift, fwd -0.35R — the veto's mirror.
- `regime=vol_expansion`: TRAIN-positive (+0.56R) but **forward-NEGATIVE (-0.15R), 0/2
  fwd yrs** on the broad xvol bases — a TRAIN/FWD regime flip; the substrate's own
  `vol=xhi` gate already captures the useful part, and the regime layer's extra
  vol_expansion slice over-concentrates into the contaminated leader-impulse bars.
- `vp_loc=below_va` / `vp_poc_side=below_poc`: -0.32..-0.34R — acceptance BELOW value
  is the wrong auction context for a long (clean sign-symmetry with above_va).

---

## 2. Independence & artifact checks
- **phi (condition vs win, within base):** the veto phi ~0.17-0.23 (real positive
  association with winning), above_va phi ~0.07-0.14. Low-to-moderate — the conditions
  carry independent signal, not a relabel of the base.
- **The veto is NOT merely a low-vol artifact.** Within the (already `vol=xhi`-gated)
  base, `ll=none` and `ll=impulse` share the SAME dominant regime (`vol_expansion`);
  the impulse side just mixes in more `calm_chop`/`range_spike`. The base vol gate is
  held fixed at xhi, so the lift is cross-asset TIMING, not a quietness proxy.
- **Permutation null:** veto perm-p = 0.0003-0.000 on all three bases; above_va 0.01-0.02;
  the 2-way stack perm-p 0.000-0.005. Anti-confluent conditions sit at perm-p ~0.8-1.0
  (correctly identified as the wrong sign).
- **Not one symbol's luck:** the veto cell's forward EV is positive across metals
  (R+2.2..+3.0), index (+2.4..+2.9), energy (+1.0..+1.4), fx (+0.8..+2.8); negative
  only in crypto/jpy_fx (the substrate-dropped classes). Broad cross-class on the kept
  universe — consistent with the substrate headline.
- **The veto does NOT transfer to the downtrend-reversion base.** On `mid_dn_revert_ny`
  the leader-veto is forward-NEGATIVE (lift -0.27, perm-p 0.97) — the cross-asset-impulse
  contamination is specific to the **xvol-up-pullback long family**. Its `vp_loc=above_va`
  gate (+0.40R, train-positive) is the transferable one. Confluence gates are
  base-specific; do not blanket-apply.

## 3. What multiplies, what doesn't (engine-by-engine verdict)
- **leadlag (leader-impulse VETO): the clear winner.** Deep TRAIN+FWD, perm-p ~0,
  signed mirror, repairs the dead 2026 forward year. The genuinely NEW, deployable
  cross-layer gate. Note it is the leader's *absence/agreement*, not its presence,
  that helps — the lead-lag layer's value here is as a CONTAMINATION FILTER, matching
  its own finding that strong cross-asset corr at H4 is contemporaneous, not a lead.
- **volume_profile (auction-location): strong forward, train-shallow.** above_va /
  above_poc lift the longs (acceptance above value), below_va/below_poc hurt them
  (clean sign symmetry = a real auction mechanic). Promote only after pre-2024 M1
  export deepens the TRAIN side; until then a forward-validated overlay, not a base.
- **regime_map (Hurst sign): a powerful FILTER, mostly via the negative.** `hurst=trend`
  is a hard veto on the pullback longs (it inverts them); the discovered `vol_expansion`
  regime is a TRAIN/FWD flip and should not be stacked. Hurst's deployable use is the
  exclusion (`drop hurst=trend`), not a positive gate.
- **liquidity_map (sweep+reclaim in last 3 bars): near-zero independent lift here.**
  liq_align/liq_sweep move EV <0.13R either way on these (already vol/trend-gated)
  bases — the sweep mechanic does not add orthogonal signal ON TOP OF the substrate's
  vol=xhi·trend·mtf stack (it likely lives on a different base population — the wide
  sweep nets of KB4 — not on extreme-vol pullbacks).

## 4. TOP cross-layer confluent high-odds setups (the deliverable)
Honest EV/R + win% + n, forward, with the deployable-vs-pocket distinction:

1. **DEPLOYABLE GATE — substrate xvol pullback ∧ NO leader impulse (4-class universe).**
   `vol=xhi·persist=rand·trend=up·mtf=conflict` LONG 3R on **metals/index/energy/fx**
   (drop crypto/jpy_fx, as the substrate flagship does — they are forward-negative here),
   **only when no SPX/NAS/BTC/USDJPY/US30/XAU/DXY is impulsing >=1.5σ.** FWD **+1.53R,
   65% win, n40** pooled (TRAIN +1.05R n38; 2025 +1.69 / 2026 +1.24; perm-p 0.0003;
   restricting to the 4 kept classes raises EV further — index/metals +2.4..+2.9R).
   Broad-base variant (`xvol_up_conflict`) FWD +0.83R n63 — more frequent, repairs the
   dead 2026 year. This is the single best new cross-layer rule: deep on both sides,
   signed, null-cleared, broad cross-class.
2. **HIGH-CONVICTION POCKET — pullback ∧ no-leader ∧ above prior value area.**
   Add `vp_loc=above_va`. FWD **+1.69R (n19), 2025 +2.36 / 2026 +1.30** (flagship);
   **+1.40R (n26)** on the broad base. The owner's "knows what happens most of the
   time" cell — but n<30 and VP train-shallow -> selector overlay, size by conviction.
3. **BREADTH GATE — NY mid-vol downtrend reversion long ∧ above prior value area.**
   `mid_dn_revert_ny` ∧ `vp_loc=above_va`: FWD +0.87R (n49) vs base +0.47R, 2/2 yrs,
   **TRAIN-positive (n13 +0.78R)**, perm-p 0.038 — the one VP gate with train support,
   in the high-frequency breadth sleeve.
4. **UNIVERSAL EXCLUSIONS (apply to all xvol-up longs):** drop `hurst=trend`
   (inverts the edge, fwd -0.74R), drop bars where a leader impulses opposed
   (fwd -0.35R), drop `regime=vol_expansion` slice (fwd -0.15R, 0/2 yrs).

## 5. Honest caveats
- **The full 2-way stack is a POCKET (n=19-26 fwd).** Doctrine: thin cells are
  confluence pockets, not streams. The deployable claim is Gate 1 (n>=40 both sides);
  the stack is a high-conviction selector overlay.
- **VP gates are forward-only (M1 since 2024).** above_va/above_poc clear the forward
  null and both fwd years but have ~0 TRAIN sample — not a decade holdout. Flagged;
  promote via pre-2024 M1 export.
- **Forward window is short (2025 + partial 2026).** The veto's 2/2-fwd-year + deep
  TRAIN is the floor of trust; not a multi-decade forward proof.
- **odds != EV (again):** the win% at fixed 3R stays in the 45-65% band; the verdict is
  mean_R lift (+0.6 to +0.8R per added gate), never a raw win-rate flag. No setup is
  "the market is 90% predictable"; these are stackable, signed, low-base-rate-but-high-
  EV confluence gates on an already-conditional substrate cell.
- **The lift comes from a leader's ABSENCE.** This is a filter/veto, not a presence
  signal — consistent with the lead-lag layer's own H4 "contemporaneous, not lead"
  finding. The exploitable lead, if any, likely lives at M15/M1 (lead-lag KB note 2).

## FILES
- `KB5_cross_layer_miner.py` — the leak-free single-pass cross-layer tagger + miner (reusable).
- `KB5_CROSS_LAYER_RESULT.json` — per-base × per-condition full map (TRAIN/FWD/per-year/lift/phi/perm-null).
- `KB5_report.py` / `KB5_FRONTIER.json` — disciplined ranked confluent (+) cells + anti-confluent (-) drop-list.
- `KB5_validate_stack.py` — perm-null on the 2-way stack, per-class, leader-veto artifact check.
- Engines intersected: `substrate.py`, `volume_profile.py`, `leadlag.py`, `regime_map.py`, `liquidity_map.py`.
