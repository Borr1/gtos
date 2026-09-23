# Wave 3 Methodology Verification

Generated 2026-04-17 by independent verifier (third line of defense before live-trading restart). No files modified, only this report written.

## A. Per-report integrity (PRE-REG order, thresholds stated before results, verdict matches rule)

| Report | Status | One-line reason |
|---|---|---|
| Q-13.4 ORB | **PASS** | Section 1 hypotheses precede Section 4 results; KILL rule (WR<55% with 95% upper CI<60%) explicitly triggered by NY in_kz (WR=41.4%, Wilson_hi=53.1%, n=70). Spot-audit matches (London 55.7% n=61 / NY 41.4% n=70). |
| Q-13.5 Cross-asset | **PASS** | Pre-reg gate (|rho|>=0.10 AND Bonf p<0.004 AND sign>=0.55 at lag>=1) explicitly refused at lag 0; no pair passes. Spot-audit matches: max |rho| at k>=1 on M15 = 0.027 (US30 k=3). Verdict NULL is consistent. |
| Q-13.6 FVG | **PASS** | PROMOTE rule (IMPULSE vs ISOLATED delta>=+10pp, fill>=60%, p<0.025 on BOTH TFs) stated up front; observed deltas -0.8pp M15 and -8.4pp H1 (both wrong sign). KILL correct. Spot-audit matches. |
| Q-13.10 Volume | **PASS** | H1 (ratio>=1.2, p<0.025) fails at ratio=1.229 p=0.0750; 100% VPOC-OB co-location (10/10) correctly kills novelty. No threshold loosening. Spot-audit matches. |
| Q-14.9 + Q-14.11 | **PASS** | Q-14.9 per-question rule (prob>=60% AND p_raw*3<0.017) met exactly by k=6 too_far_down (60.3%, p_raw=0.0024 -> 0.0072<0.017). Joint Bonf passes too. Asymmetry caveat disclosed. Q-14.11 delta +12.8pp but p_raw=0.0766 correctly KILLED. Spot-audit matches. |
| Q-14.14 Microstructure | **PASS** | Pre-reg bar |rho|>=0.08 AND perm_p<0.0033 (Bonf 15); zero direction-prediction passers. 14 vol-to-vol passers explicitly labeled "not alpha" and NOT promoted. Audit-claim "close_loc_in_range M15 h=1 rho=-0.034" matches close_location_value row (-0.0345); note that globally the largest direction |rho| is actually H1 Corwin-Schultz sign_ret_3 at 0.0435 — does not affect report integrity since report prints all rows and promotes none. |
| Q-15 Math | **PASS** | Wavelet max |rho| = 0.0521 (Haar scale 2, nominal p=0.037, ESS-adj p=0.097) — both must pass Bonf 0.0125; FAIL correctly. Copula + coherence also FAIL at pre-registered gates. Notable self-caveat: early lookahead-contaminated run (|rho|=0.32) flagged and discarded; strictly-causal version used. Spot-audit matches. |
| Q-16 Adversarial | **PASS** | Q-16.1 n=19<20 -> UNDERPOWERED (no fabricated significance). Q-16.3 NY midSession 1.72× p<0.001 meets pre-reg 1.5× AND p<0.01 -> SIGNAL correct. Q-16.5 tercile gap -15.5pp, p=0.466 -> NO SIGNAL. No threshold loosened. Spot-audit (1.72× n=560) matches. |

No HARKing language found (the only "post-hoc" hits are negative declarations: "I will NOT report post-hoc lag choices").

## B. Q-14 broad MI narrative accuracy vs JSON

Narrative (`Q-14_broad_mi_discovery.md`) checked against raw JSON (`Q-14_broad_mi_discovery.json`):

- Top-30 dir_mi family counts: **VERIFIED**. 21 vol_regime + 8 flow + 1 range_compression = 30, zero shape. Matches narrative exactly.
- Top-30 ret_mi family counts: **VERIFIED**. 12 flow (volume/signed_tick_vol) + 6 range + 12 vol_regime = 30, zero shape. Narrative's "18 volume/range/signed_tick_vol" groups flow+range (12+6=18) matches.
- XAUUSD dir_mi passers: **VERIFIED**. 4 entries — vpin k=12 (MI=0.00339), rv50 k=12 (0.00288), vpin k=3 (0.00270), rv20 k=12 (0.00270). Narrative table matches exactly including perm_p values.
- VPIN subgroup: **VERIFIED**. n=29, low WR 0.80 (n=10), mid WR 0.556 (n=9), high WR 0.50 (n=10), Fisher odds 0.25, Fisher p=0.3498. Narrative "0.35" is correct rounding.
- Per-symbol passer counts: **VERIFIED**. US30=8, USDJPY=7, GBPJPY=6, GBPUSD=5, XAUUSD=4.
- Minor: narrative states ret_mi vol-regime MI range "0.07-0.10 bits" but actual max is 0.1153 (US30 atr14 k=1); flow/range stated "0.08-0.15" but min is 0.076 (GBPUSD signed_tick_vol k=1). These are rounding/wording looseness, not false claims — ranges are indicative, not binding.

**Narrative accuracy verdict: ACCURATE.** All structural claims and headline numbers map to JSON. Minor MI-range wording imprecision noted but non-material (no deployment decision hinges on exact bit range).

## C. Final recommendation

**Safe to cite** for all 8 Wave 3 reports and the Q-14 broad MI narrative. Three independent integrity properties hold across the set: (1) hypothesis sections precede results sections; (2) thresholds (alpha, effect size, Bonferroni divisor) declared before any result; (3) every verdict follows mechanically from its pre-registered rule without moving the goalposts. Spot-audited headline numbers all match underlying scripts/JSON.

Cautions to pass to CEO:
- Q-14.9 k=6 too_far_down is the only "PASS" in Wave 3 and is explicitly flagged as regime-bound (2026 bull tape); not deployment-ready without multi-instrument + multi-year replication.
- Q-16.3 NY session SIGNAL restates existing kill-zone schedule — not novel alpha.
- All 2026-window-only; no out-of-sample validation inside Wave 3.
