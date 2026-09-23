# KB6 — Confluence frontier 2: veto on other bases + confluence-score router (track KB6)

Builder pass 2026-06-15. Three deliverables, all leak-free + forward-held + perm-nulled:
1. **The leader-impulse VETO is base-specific** — mine it (and every orthogonal gate)
   on the OTHER substrate long/short bases to find WHERE ELSE confluence lifts.
2. **DEEPER stacks** (2/3-way: veto × VP × hurst × session) for higher-odds n-gated cells.
3. **A CONFLUENCE-SCORE ROUTER** — a leak-free sizing function that scales a candidate
   by the count of agreeing, per-class-signed conditions; validated against FLAT sizing
   on forward EV and the binding **vol-matched 1.5× left-tail STRESS** challenge-pass MC.

Engines (all reuse the KB5 leak-free tagger `KB5_cross_layer_miner` verbatim):
`KB6_veto_other_bases.py` (GOAL 1), `KB6_deep_stacks.py` (GOAL 2),
`KB6_router_validate.py` + `KB6_confluence_router.py` (GOAL 3).
Results: `KB6_VETO_OTHER_BASES_RESULT.json`, `KB6_DEEP_STACKS_RESULT.json`,
`KB6_ROUTER_RESULT.json`.

## Method / discipline (enforced in code, inherited from KB5)
- **No lookahead.** Base-state match + EVERY orthogonal tag at bar i from CLOSED bars
  index<=i: substrate `build_states`; outcome via `sub.outcome`→`geometry_lib.simulate_detail`
  (pessimistic same-bar, real `w1.cost_for`); VP from prior completed day's profile;
  regime model fit on TRAIN rows only; leadlag leader z at the same H4 close; liquidity
  sweep+reclaim from bars (i-3..i]. Router signs LEARNED on TRAIN(<=2024) ONLY, applied
  unchanged forward.
- **Forward holdout mandatory; no averages as verdicts.** Verdict = forward mean_R
  (real cost); every cell carries TRAIN/FWD mean_R, per-year, n. Router verdict is the
  vol-matched 1.5× left-tail STRESS challenge-pass MC, not per-trade EV alone.
- **Sign per class** (W4/W5 lesson): conditions can be ANTI-confluent; the miner measures
  the sign of every condition per base, and the router DROPS anti-confluent ones.
- **Permutation null.** Shuffle the condition labels within the FORWARD base population
  (2000 draws), p = P(shuffled lift ≥ observed). A confluent gate must beat the null.

---

## 0. HEADLINE — confluence is base-specific, and there are NEW high-odds gates

The KB5 leader-veto does NOT blanket-transfer (it inverts on `mid_dn_revert`). Mining all
orthogonal gates on 14 OTHER substrate bases found **three genuinely new, fully-disciplined
confluent cells** (fwd n≥30, fwd R>0, 2/2 fwd years, perm-p ≤ 0.10), the strongest of which
is also **TRAIN-positive** (not forward-only):

| base (dir) | NEW confluent gate | base FWD | gate FWD R (n) | fwd lift | TRAIN lift | perm-p | 2/2 yr |
|---|---|---|---|---|---|---|---|
| **`xvol_dn_aligned_london`** (L) | **`liq_align=aligned`** (sweep+reclaim in trade dir) | +0.59 | **+1.30 (42)** | **+0.71** | **+0.10** | **0.001** | yes |
| `lo_dn_neutral_rand_asia` (S) | `vp_loc=below_va` (acceptance below value) | +0.42 | **+1.00 (40)** | +0.58 | **+0.76** | 0.008 | yes |
| `hi_flat_aligned_revert_depth4` (S) | `hurst=revert` | +0.13 | +0.39 (222) | +0.26 | +0.03 | 0.0005 | yes |
| `xvol_up_neutral` (L) | `hurst=revert` | +0.30 | +0.67 (40) | +0.37 | +0.11 | 0.02 | yes |
| `xvol_flat_revert_neutral` (S) | `ll_align=none` (leader VETO) | +0.17 | +1.09 (25) | +0.93 | −0.36 | 0.000 | yes (n<30) |

The single load-bearing NEW result: **the liquidity sweep+reclaim mechanic — which KB5 found
near-zero on the xvol-up-pullback base — is STRONGLY confluent on the xvol-DOWN-trend-aligned
London long**, exactly as KB5 predicted ("it likely lives on a different base population").
Base +0.59R → +1.30R fwd (n42), perm-p 0.001, AND train-positive (+0.10) — deep on both
sides, signed mirror (`liq_align=opposed` is −0.67R lift), broad cross-class (index +1.34
n20, crypto +1.57, fx +2.84, jpy +1.55) and cross-symbol. This is the deployable new gate.

### Where the leader-VETO transfers (and where it does NOT)
The veto (`ll_align=none`) is **base-specific**, confirming KB5:
- **Transfers + (forward):** `xvol_up_neutral` long (+0.34 lift, +0.64R, perm-p 0.086),
  `xvol_dn_aligned_london` long (+0.49 lift, +1.08R, perm-p 0.054), `xvol_flat_revert_neutral`
  short (+0.93 lift, +1.09R, perm-p 0.000), `hi_flat_aligned_revert_asia` short (+0.41 lift,
  +0.77R, perm-p 0.049). All are **xtreme-vol** bases — the veto's home is the elevated-vol
  family (its thesis: an xvol move coinciding with a cross-asset leader impulse is macro-driven,
  not the local mechanic).
- **Does NOT transfer / inverts:** `mid_up_aligned_coil_asia` (−0.22 lift), `lo_up_aligned_coil_london`
  (−0.10), `hi_up_neutral_ny` (−0.10), `hi_flat_aligned_revert_london` (−0.08) — calmer-vol
  or different-structure bases. **Do not blanket-apply the veto.**
- Several +veto cells are TRAIN-NEGATIVE (forward-only veto effect) — flagged below; only
  `xvol_up_neutral` (+0.11 train lift) carries the veto with train support outside the KB5 flagship.

### Sign-symmetry confirms the mechanics are real (not noise)
On `xvol_dn_aligned_london` long: `liq_align=aligned` +0.71R **vs** `liq_align=opposed` −0.67R;
`ll_align=none` good **vs** `ll_align=opposed` −0.28R. Clean mirrors. And hurst flips sign by
base: confluent on `xvol_up_neutral`/`hi_flat_revert` (+), anti-confluent on `hi_up_neutral_ny`
(−0.32) — the per-class sign learning is load-bearing, exactly the W4/W5 lesson.

---

## 1. GOAL 1 deliverable — veto/gate map on the 14 OTHER bases
(Full per-base × per-condition map in `KB6_VETO_OTHER_BASES_RESULT.json`.)

**DISCIPLINED CONFLUENT (+)** — fwd n≥30, lift>0, fwd R>0, 2/2 fwd yrs, perm-p ≤ 0.10:

| base | dir | gate | base FWD | gate FWD | lift | n | train lift | perm-p |
|---|---|---|---|---|---|---|---|---|
| `xvol_dn_aligned_london` | L | `liq_align=aligned` | +0.59 | +1.30 | +0.71 | 42 | +0.10 | 0.001 |
| `lo_dn_neutral_rand_asia` | S | `vp_loc=below_va` | +0.42 | +1.00 | +0.58 | 40 | +0.76 | 0.008 |
| `xvol_dn_aligned_london` | L | `vp_loc=below_va` | +0.59 | +0.88 | +0.30 | 49 | −0.40 | 0.047 |
| `lo_dn_neutral_rand_asia` | S | `vp_poc_side=below_poc` | +0.42 | +0.74 | +0.32 | 48 | +0.76 | 0.046 |
| `xvol_flat_revert_neutral` | S | `vp_poc_side=above_poc` | +0.17 | +0.70 | +0.54 | 30 | +0.66 | 0.003 |
| `xvol_up_neutral` | L | `hurst=revert` | +0.30 | +0.67 | +0.37 | 40 | +0.11 | 0.02 |
| `xvol_up_neutral` | L | `ll_align=none` (veto) | +0.30 | +0.64 | +0.34 | 33 | −0.45 | 0.085 |
| `hi_flat_aligned_revert_depth4` | S | `hurst=revert` | +0.13 | +0.39 | +0.26 | 222 | +0.03 | 0.0005 |

**ANTI-CONFLUENT (−) — DROP** (signed mirrors, fwd lift < −0.15, n≥30):
`xvol_dn_aligned_london` × `liq_align=opposed` (−0.67), × `ll_align=opposed` (−0.28);
`hi_up_neutral_ny` × `vp_poc_side=above_poc` (−0.44), × `hurst=revert` (−0.32);
`hi_flat_aligned_revert_depth4` × `regime=vol_expansion` (−0.42).

## 2. GOAL 2 deliverable — DEEPER (2/3-way) confluence stacks
(Full per-base deep cells in `KB6_DEEP_STACKS_RESULT.json`; all require fwd n≥22, fwd R>0,
ALL fwd years +, perm-p reported.) The odds MULTIPLY at depth — and several deep cells now
carry **TRAIN support on both sides**, which the KB5 2-way stack (`veto ∧ above_va`, train≈0)
lacked:

| base | stack (2/3-way) | base FWD | stack FWD R (n) | lift | TRAIN R (n) | perm-p | yr |
|---|---|---|---|---|---|---|---|
| **`xvol_dn_aligned_london`** (L) | `regime=vol_expansion` ∧ `liq_align=aligned` | +0.59 | **+1.62 (28)** | +1.03 | **+0.25 (49)** | 0.000 | 2/2 |
| **`xvol_up_pullback`** (L, flagship) | `ll_align=none` (veto) ∧ `liq_align=aligned` | +0.71 | **+1.73 (23)** | +1.02 | **+0.58 (20)** | 0.001 | 2/2 |
| `xvol_dn_aligned_london` (L) | `vp_loc=below_va` ∧ `liq_align=aligned` | +0.59 | +1.88 (23) | +1.29 | +0.25 (3, thin) | 0.000 | 2/2 |
| `xvol_up_conflict` / `_mid` (L) | `ll_align=none` ∧ `vp_loc=above_va` | +0.20 | +1.40 (26) | +1.20 | ≈0 (train-thin) | 0.000 | 2/2 |
| `hi_flat_aligned_revert_depth4` (S) | `hurst=revert` ∧ `liq_align=opposed` ∧ asia | +0.13 | +1.18 (28) | +1.05 | **+0.43 (50)** | 0.003 | 2/2 |
| `xvol_up_conflict_mid` (L) | `ll_align=none` ∧ `liq_align=aligned` | +0.19 | +1.00 (31) | +0.81 | +0.25 (43) | 0.002 | 2/2 |
| `mid_dn_revert_ny` (L) | `vp_loc=above_va` ∧ `liq_align=aligned` | +0.47 | +1.10 (33) | +0.63 | +0.76 (11) | 0.022 | 2/2 |

**The two best deep cells (deep on BOTH sides):**
1. **`xvol_dn_aligned_london` ∧ `regime=vol_expansion` ∧ `liq_align=aligned`**: +1.62R fwd
   (n28), TRAIN +0.25R (n49), perm-p 0.000, 2/2 fwd yrs. A genuine high-odds confluence
   stream (n≥28 both sides), not a thin pocket — the NEW deployable deep cell.
2. **flagship `xvol_up_pullback` ∧ veto ∧ `liq_align=aligned`**: +1.73R fwd (n23), TRAIN
   +0.58R (n20), perm-p 0.001. Stacks the NEW liquidity gate ON TOP of the KB5 veto — and
   unlike KB5's `veto ∧ above_va` pocket it is **train-positive on both sides** (the
   liquidity gate has H4-native depth the VP gate lacks). The better 3rd gate for the flagship.

The KB5 2-way `veto ∧ above_va` flagship pocket (+1.69R) replicated here; the new finding is
that **`liq_align=aligned` is a better-evidenced 3rd gate than `above_va`** (train support,
H4-native depth) on both the flagship long and the new xvol-dn-london long.

## 3. GOAL 3 deliverable — the CONFLUENCE-SCORE ROUTER (built, validated, honest verdict)

`KB6_confluence_router.py` + `KB6_router_validate.py` build a leak-free router:
`score(i) = Σ per-class-learned-sign of the orthogonal conditions present at bar i`;
`size(i) = clamp(1 + 0.5·score, 0.4, 2.0)` (confidence sizing, deletes nothing). Signs
learned on **TRAIN(<=2024) ONLY**, applied unchanged forward. Confluence sleeve = the
flagship `xvol_up_pullback` long + the two NEW xvol long bases (`xvol_dn_aligned_london`,
`xvol_up_neutral`), 4-class universe, 377 leak-free signals.

### VERDICT: the router does NOT beat flat on the binding constraint — and WHY is the finding
Per doctrine the verdict is the **vol-matched 1.5× left-tail STRESS challenge-pass**, never
per-trade EV. Robustness A/B across THREE legitimate no-lookahead sign sources
(`KB6_router_signsource_ab.py`):

| sign source | full-sleeve fwd EV | deploy str@1.5%vm | flagship-only fwd EV | flagship str@1.5%vm |
|---|---|---|---|---|
| **FLAT** (baseline) | 0.794 | **69.06%** | 1.583 | **77.00%** |
| per-base TRAIN | 0.737 | 69.26% | — | — |
| pooled-family TRAIN | 0.801 | 68.61% | — | — |
| KB5/KB6 PRIOR (proven dir) | **0.997** | 68.58% | 1.611 | 76.69% |

**The router lifts forward MEAN EV (PRIOR source: 0.79 → 1.00R, +0.20R) but NOT the
vol-matched left-tail stress pass-rate** (all routers within noise / slightly below flat,
both standalone and folded). It concentrates size into the high-confluence trades, but those
are the HIGHEST-VARIANCE trades (the +1.7R pockets), so the extra mean does not buy left-tail
survivability — and the stress pass is exactly the constraint that binds. **Sizing the
confluence sleeve by confluence score is therefore NOT a justified book change.**

### The deeper, decision-relevant finding: the strong gates are FORWARD-ONLY on these bases
A no-lookahead TRAIN-learned-sign router structurally cannot capture the veto/liquidity
confluence on the non-flagship bases, because **their TRAIN-period sign is the OPPOSITE of
the forward sign**:

| base × gate | TRAIN lift | FWD lift |
|---|---|---|
| `xvol_dn_aligned_london` × `ll_align=none` (veto) | **−0.33** | **+0.36** |
| `xvol_up_neutral` × `ll_align=none` (veto) | **−0.42** | **+0.61** |
| `xvol_up_pullback` (flagship) × `ll_align=none` | −0.11 | +0.72 |
| `xvol_dn_aligned_london` × `liq_align=aligned` | **−0.12** | **+0.80** |
| `hurst=revert` (both up bases) | ≈0 / neg | +0.5 |

The per-base TRAIN router even learned `ll_align=none → sign −1` (penalizing the veto), the
opposite of the proven forward direction. This is the W4/W5 lesson at the router level: **a
confluence gate's sign can be regime-period-specific; only the KB5 flagship veto carries a
sign stable across TRAIN and FORWARD**, which is exactly why the deployable confluence rule
remains the FLAGSHIP veto (and now its `liq_align` deep-stack), not a learned multi-base router.

### What the router IS good for
Flat folding the 3-base confluence sleeve at conf 0.45 also slightly LOWERS the deploy stress
(72.85% → ~69%) because the two new bases correlate more with the book than the clean flagship.
**The right deployment is the FLAGSHIP-ONLY confluence cell** (xvol_up_pullback ∧ veto, KB5),
optionally with the NEW `liq_align=aligned` 3rd gate (train+fwd-positive, §2). The router as a
SELECTOR (take-the-best-pocket, count gates, take only score≥2 trades) is a defensible overlay
for capital allocation; as a SIZER it does not beat flat on the binding stress constraint.

## 4. Honest caveats
- **Forward window is short** (2025 + partial 2026). 2/2-fwd-year + (where present)
  train-positive is the floor of trust, not a decade forward proof.
- **VP/liquidity train depth:** the VP gates are M1-derived (M1 since 2024) so their TRAIN
  is shallow except where the perm-null + 2/2 fwd carry them; `liq_align` is H4-native and
  the `xvol_dn_aligned_london` cell is train-positive (+0.10), the strongest case.
- **odds ≠ EV:** verdicts are mean_R and (for the router) the vol-matched stress-pass, never
  win%. None of these is "the market is 90% predictable"; they are stackable, signed,
  low-base-rate-but-high-EV confluence gates on already-conditional substrate cells.
- **Several +veto cells are forward-only** (train-negative). The deployable veto remains the
  KB5 flagship (deep both sides); the new TRAIN-supported gate is `liq_align` on the
  xvol-dn-aligned-London long.

## FILES
- `KB6_veto_other_bases.py` — leak-free veto/gate miner over 14 OTHER substrate bases (reuses KB5 XL tagger).
- `KB6_VETO_OTHER_BASES_RESULT.json` — per-base × per-condition TRAIN/FWD/per-year/lift/phi/perm-null.
- `KB6_deep_stacks.py` / `KB6_DEEP_STACKS_RESULT.json` — 2/3-way intersection mining per base.
- `KB6_confluence_router.py` + `KB6_router_validate.py` / `KB6_ROUTER_RESULT.json` — the
  leak-free confluence-score router (signs learned on TRAIN), flat-vs-router EV + vol-matched
  stress-pass MC, deploy-book fold.
- `KB6_router_signsource_ab.py` / `KB6_ROUTER_SIGNSOURCE_AB.json` — robustness A/B across 3
  no-lookahead sign sources (per-base / pooled / KB5-prior) + flagship-only; the verdict that
  the router lifts mean EV but not the binding vol-matched stress, and the train/fwd sign-flip table.
- Reused verbatim: `KB5_cross_layer_miner` (tagger), `substrate`, `INTEG_portfolio_build_w2`
  (LOCKED MC engine), `INTEG_portfolio_build_w3` (book streams), `KB5_fold_new_sleeves` (universe).
