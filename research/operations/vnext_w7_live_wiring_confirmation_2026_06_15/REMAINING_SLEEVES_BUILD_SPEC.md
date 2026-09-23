# W7 Remaining-Sleeves Build Spec (evidence-backed, [RAN]-verified)

Date: 2026-06-15. Source agent: max-rigor route investigation. Route = `research/operations/
final_moonshot_v4_ultimate_mechanical_edge_2026_06_10/`. Admission authority = `src/components/
ultimate_book/admission.py`. This is the PORT CONTRACT for the 6 sleeves not yet in src.

## Port order (easiest/highest-confidence first; H4-only first cycle = 1-3)

1. **sub_xvol_pullback** (substrate, conf 0.45) — H4, PER-SYMBOL. Oracle `KB5_fold_new_sleeves.py:47-54`
   → `SUBSTRATE_corrcheck.materialize_cell` + `substrate.build_states/cell_coords/outcome`.
   Cell `g1.0_3.0|dir=1|depth4|vol=xhi|trend=up|mtf=conflict|persist=rand`. Fire iff: vr≥1.6,
   slope50>1.5, mtf_align=-1 (conflict), -0.10<ac60<0.10. dir FIXED +1. stop=1.0·ATR14, target=3.0·stop
   (1:3R). Warmup 210 H4 (cluster `substrate`). LIVE NUANCE: compute state at i=n-1 WITHOUT the
   `+MAXBARS+5=295` batch guard. on_surface (admission.py:214-218) minus W7-dropped NATGAS_cash/HEATOIL_c
   = 18 syms. cluster `substrate`. [RAN] real cell_coords MATCH → dir+1 stop6.2938 target18.8813.
2. **sub_mid_dn_revert** (substrate, conf 0.20) — SAME engine as #1; depth-7 cell
   `vol=mid(0.85≤vr<1.15 per route _bucket_vr)|trend=dn(slope50<-1.5)|mtf=neutral(0)|rngpos=mid(0.25-0.75)|
   comp=norm(0.7-1.3)|persist=revert(ac60≤-0.10)|session=ny(hour≥16 UTC)`. dir FIXED +1. stop=1.0·ATR,
   target=3.0·stop. [CORRECTION: an earlier draft glossed vol=mid as 1.15-1.6; the route _bucket_vr maps
   [0.85,1.15)->mid and [1.15,1.6)->hi. The vendored code follows the route (parity-verified).]
   Oracle `KB5_fold_new_sleeves.py:56-60`. on_surface admission.py:230-235 minus dropped = 21 syms.
   cluster `substrate` (shares the unit with #1). [RAN] real build_states match seed2 i250 → dir+1
   stop5.2133 target15.6400. NOTE: W6 vp-acceptance refinement (admission.py:323-329) OFF by default.
3. **metals_ob_micro** (metals, conf 0.30) — H4. Oracle `INTEG_portfolio_build.py:122-141` + detector
   `csb_commodity_setups.py:80-108` (`sig_ob`). vol_gate atr≥1.2·SMA100; htf_trend(lb=30); OB retest
   over k∈[i-2..i-8]; dir=htf_trend sign. THEN gen-gates: ac60≥0.20 AND DEDUP drop if FVG fired same
   (sym,date,dir) for ANY ac (i≥121). stop=max((c-min(l,ob_bot))+0.10a, 0.25a); target_dist=None
   (exit via exit_state_d). Warmup 200 H4 (cluster `metals`). on_surface admission.py:181-183 = 6 metals
   (XAU/XAG + EUR/AUD crosses). cluster `metals` (shares unit w/ core+softband). [RAN] real sig_ob fired
   i229 dir+1 stop29.7753; exit_state_d R+1.0229 win_partial. Reuses atr14/autocorr/vol_ratio/
   exit_state_d/htf_trend (all in src); vendor only sig_ob+vol_gate_ok. Dedup at BATCH layer.
4. **fx_jpy** (jpy, conf 0.15, status train-FALSIFIED breadth) — **M15** + session. Oracle
   `INTEG_portfolio_build.py:217-235`. At 4th London M15 bar (hour≥8): dir=sign(close[iw]-open[i0]).
   stop=1.0·ATR(M15), target=2.5·ATR. One trade/sym/day. on_surface GBPJPY,USDJPY. cluster `jpy`.
   NEEDS M15 feed + session-aware invocation + TZ-correct session gate.
5. **fx_jpy_ny** (jpy, conf 0.15, status forward-only) — **M15** + NY session. Oracle
   `INTEG_portfolio_build_w2.py:172-179` → `kb2_new_breadth.session_open_mom`. 4th NY M15 bar (hour≥15):
   gates |impulse|≥1.0·ATR AND trend20 align; dir=sign(impulse). stop=1.0·ATR, target=2.5·ATR.
   on_surface GBPJPY,USDJPY. cluster `jpy` (shares unit w/ #4). Reuses #4's M15/session seam.
6. **vp_euidx_pocgrav** (volprofile, conf 0.30, status M1-forward-only) — **HARD BLOCKER**. Oracle
   `KB5_fold_new_sleeves.py:64-97`. H4 decision but needs PRIOR-DAY M1 VOLUME PROFILE
   (`volume_profile.daily_profiles`/`load_m1`). Fire iff |d_poc_atr|≥2.0 AND not in_va AND vr≥1.2 AND
   target=|price-priorPOC|≥0.8·stop. dir=-1 if price>POC else +1. stop=1.0·ATR. on_surface GER40,UK100.
   cluster `volprofile`. WARMUP["volprofile"]=100 is WRONG (needs 200 H4 + ≥1 prior M1 day). [RAN] real
   _vp_pocgrav_rows GER40 → 33 signals; i206 dir-1 stop50.912 target467.073. **Cannot port until the
   runtime adds an M1+volume fetch + vendors volume_profile.py.**

## BLOCKERS (go-live intelligence)

1. **vp_euidx_pocgrav — HARD M1-data blocker.** Live H4 feed has no M1/volume path. Needs M1+volume
   fetch for GER40/UK100 + vendored volume_profile engine + corrected warmup. Route data forward-only.
2. **fx_jpy/fx_jpy_ny — M15 feed + session timing + timezone.** Need M15 feed + per-day session-window
   invocation (NOT H4 latest-bar). Session-hour gates (≥8 London / ≥15 NY) are clock-dependent — must
   run on the research M15 export timezone, not naive UTC (verify bridge TZ vs FTMO server→UTC +179min).
   Both sleeves are statistically marginal (0.15: one FALSIFIED-in-train, one forward-only).
3. **metals_ob_micro — cross-sleeve dedup (soft).** Suppress OB intents colliding with an FVG signal on
   sym+day+dir (any ac). Wire at the batch/admission layer.
4. **Substrate live-warmup nuance (soft).** Compute single-bar state without the `+MAXBARS+5` forward
   guard so the `substrate=210` warmup applies.
5. **on_surface > 27-universe:** NATGAS_cash + HEATOIL_c in the substrate registry tuples are W7-DROPPED
   → filter via `filter_w7_dropped_symbols`. No other on_surface symbol is outside the 27.

## Build decision

- **Now:** port 1-3 (substrate×2 + ob_micro) — faithful, parity-tested, zero new data feeds. Brings the
  book to 8/11 sleeves (~88% of weight) on the existing H4 live feed.
- **Next:** build the M15+session seam, port 4-5 (small, flagged — buildable but low edge).
- **Deferred (owner decision on priority):** vp_euidx_pocgrav needs a new M1 volume-profile data path;
  it is forward-only-flagged. Build the M1 path or defer — a scope/priority call for the owner.
- Deployment of any sleeve remains gated by the owner (triple-gate + include_clean3 flag), default-off.
