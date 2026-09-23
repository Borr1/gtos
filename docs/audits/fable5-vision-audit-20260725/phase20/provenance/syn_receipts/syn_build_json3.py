"""SYNTHESIS part 3 — candidate book (12) + mx cohort (14) + sizing-only (1) + machinery (2)."""
from __future__ import annotations
import json, os, pickle
P = os.path.dirname(os.path.abspath(__file__)); PROV = os.path.dirname(P); PH20 = os.path.dirname(PROV)
V = pickle.load(open(f"{P}/_v_broad.pkl","rb"))
def add(n,l,v,c,pr,o,b,pa,g,li,r,e):
    V[n]=dict(name=n,lane=l,verdict=v,klass=c,premise=pr,origin=o,claimed_at_birth=b,parameters=pa,geometry=g,lifecycle=li,repairable=r,evidence=e)
S2D=f"{PROV}/S2_REGISTRY_DOSSIERS.md"; S2R=f"{PROV}/s2_receipts/S2_REGISTRY_DOSSIER_V1.json"
X1=f"{PROV}/x1_receipts/X1_VERDICTS_V1.json"; X1C=f"{PROV}/x1_receipts/X1_CEILING_V1.json"
X2=f"{PROV}/x2_receipts/X2_PROVENANCE_PATTERN_V1.json"
CB0="b8e5f3a9e (2026-06-18, 'vps: package a8 ultimate book minimal branch'), ACTIVATED THE SAME DAY by 71713ff8e — zero days between birth and activation (x2)."
CUB=("Its confidence weight traces to research/operations/final_moonshot_principal_full_system_audit_2026_06_17/"
     "CORRECTED_UNIFIED_BOOK_MC_AUDIT.json, which HAS NEVER EXISTED IN THIS REPOSITORY ON ANY REF.")
MX0=("96f53b63d ('vps: package conditioned expansion parity') — BORN AND ACTIVATED IN THE SAME COMMIT "
     "(ultimate_book_include_market_expansion_book: true, config/agent_config.yaml:1284), on the same day the curated snapshot "
     "recorded the package as 'materially built as a default-off code/research package, but not live authority' with five "
     "requirements MX-READINESS-REQ-001..005 open by name (.context/00_core/research_current_state.md:513-517, never closed).")
MXP=("Shared: TARGET_R 2.0, ATR_REVERSION_MULT 1.25, VOLUME_Z_THRESHOLD 2.0, DONCHIAN_WINDOW 20, RISK_WINDOW 14 "
     "(market_expansion_d1.py). One constant set for eight volume-surge sleeves across indices and FX with no per-class "
     "derivation. None has ever changed value (x2: 24 of 24 constants across six sleeve modules never moved).")
MXG=("D1 clock matches the D1 premise. Horizon 7,680 M15 bars = 80 D1 bars = 1,920 h after AQ's unit repair; realised median "
     "hold 3 D1 bars and frac_over_live_horizon 0.0000 on all ten that trade — the horizon is INERT.")

# ---------------- CANDIDATE BOOK ----------------
add("vol_compression","s2","SOUND_BUT_TOO_SMALL","candidate_book",
 "After a stretch of unusually quiet daily ranges, the first daily close that breaks the prior 20-day high or low starts a directional move.",
 CB0, "Confidence 0.40. "+CUB,
 "D1 20-bar channel, 80-D1-bar horizon, 3.0R target. Its own docstring's negative control (coil breakout without the vol-state = "
 "NULL every split) is the design note.",
 "D1 clock, 1,920 h declared horizon, realised median hold 9 D1 bars, p90 35, frac_over_live_horizon 0.0000. Exits stop 65.0% / "
 "target 33.3% / maxbars 1.8%. Median MFE +1.40 R against a 3.0 R target only 33.3% ever reach. It is AU's ladder CONTROL sleeve: "
 "monotone RISING to h=20 with h=1 its worst cell, the opposite shape to the mis-scaled mx cohort. Ceiling +78.05 bps at h*=320, "
 "CI [-200.14,+343.82].",
 "391 trades, 43.4/yr on three symbols, 2018-2026. Positive at every cost band; only failing gate is significance.",
 "THE REPAIR IS SAMPLE, NOT CONTRACT. (1) STOP DOUBLE-COUNTING IT: its BTC/ETH leg is 100% contained in the mx Donchian sleeves, "
 "so the estate counts one BTC daily-breakout hypothesis as two family members at two confidence weights in two corr-clusters. "
 "Merge them into one declared member with per-symbol carriers. (2) BROADEN THE SURFACE ON THE SAME RULE — its own docstring says "
 "'the mega-factory may extend (XRP 2017+)' and the D1 archive carries ADAUSD, DOTUSD, LTCUSD, XRPUSD, DASHUSD, AVAUSD with deep "
 "history. A sample repair with a pre-declared rule and no new parameters — the only kind of failure more data can fix.",
 f"{S2D}; {S2R}; {X1C}")

add("asian_fade","s2","GEOMETRY_WRONG","candidate_book",
 "The Asian session builds a range; the first break of that range during London or New York that shows a rejection wick is a false "
 "break and gets faded back toward the range.",
 CB0+" Two of its cited artifacts (CMAP_SRMR_ASIANFADE_VERDICT.md, CMAP_SRMR_CORRECT_PLACEBO.json) resolve to NO FILE at HEAD (x2).",
 "Birth claim rests on 3,198 EURUSD trades over 2014-2026. Confidence 0.40. "+CUB,
 "STOP_K 0.6 ATR; TRAIL_GAP 0.5 shared with metal_session_reversion; 48-bar (12 h) horizon.",
 "THE SHARPEST PREMISE-VS-CONTRACT MISMATCH IN THE SLEEVE ESTATE, AND IT IS SELF-DECLARED. The docstring says the trade 'needs to "
 "ride the return move'. Measured: median hold ONE M15 bar, p90 ONE M15 bar, 95.8% of 1,319 trades resolved inside the bar they "
 "entered on; frac_over_live_horizon 0.0000; median MAE -0.93 R. The 0.6-ATR stop sits inside one M15 bar of the sleeve's own "
 "noise, so BOTH the trail (arm 0.5, gap 0.5) and the 12-hour horizon are dead letters. Exits split trail 51.9% / stop 48.1%, but "
 "a 'trail' that fires in the first fifteen minutes is a stop with extra steps.",
 "1,319 trades, 439.7/yr, 2024-01 onward only. AU: its published economics DO describe its live contract (true restamp error "
 "+0.0000 R/day); the defect is the contract itself, not the labelling.",
 "THE IDEA IS A DOCUMENTED EFFECT AND THE CONTRACT IS THE DEFECT. (1) WIDEN THE STOP UNTIL THE TRADE OUTLIVES ITS ENTRY BAR — a "
 "stop ladder at 1.0/1.5/2.0 ATR on the same entries is a pure re-labelling of stored intents through walkforward.exits.replay "
 "(the exact operation AD did for 1,631 cells), costs no machine time beyond a walk, and is the ONLY way to find out whether the "
 "reversion the docstring describes exists, because the current contract cannot observe it. (2) BEFORE ANY OF IT, FETCH DEEP M15 — "
 "do not adjudicate a 2014-2026 claim on 2.5 years. Worth: unknown by construction, and THAT IS THE POINT — the current geometry "
 "makes the claim untestable, which is strictly worse than a measured negative.",
 f"{S2D}; {S2R}; {X2}")

add("metal_session_reversion","s2","GEOMETRY_WRONG","candidate_book",
 "Each New York session, gold and silver that stretch a long way from the session open — while the higher-timeframe regime is NOT "
 "up — snap back toward it.",
 CB0, "Confidence 0.40. "+CUB+" Its own docstring flags 2015/2016 as negative years.",
 "STOP_K 0.8 ATR; TRAIL_GAP 0.5 (shared with asian_fade); 24 M15 bars (6 h) horizon.",
 "Same shape as asian_fade and for the same reason. Realised median hold ONE M15 bar; 82.7% resolved inside the entry bar; "
 "frac_over_live_horizon 0.001; median MAE -0.75 R against a 0.8-ATR stop. A 'session anchor reversion' whose natural timescale is "
 "the remainder of the NY session is being decided in fifteen minutes. AU: construction_artifact 0.3054, true restamp_error "
 "-0.0004 — so like asian_fade the published economics DO describe its live contract.",
 "837 trades, 279.0/yr. It is one of only two GEOMETRY_WRONG verdicts in the whole estate with measurable signal at x1's "
 "contract-free instrument (max signed t 2.83, tags TOO_SHORT + TOO_TIGHT) — but its ceiling CI [-58.65,+95.56] includes zero.",
 "The same stop-width repair as asian_fade and the same deep-M15 precondition, but the prognosis is worse and the evidence says so "
 "plainly: AD's exit sweep found NO cell on this sleeve that clears expectancy, 0 of 5 folds positive, p 0.9998. That is not a "
 "contract failing to express an edge; that is no edge in this window. Honest sequencing: (1) fetch deep M15, (2) re-run the stop "
 "ladder on the 2015-2026 window its birth claims, (3) if the negative years its own docstring flags are the whole story, retire "
 "it. Until then it should not be called a promotion candidate — its registry status string still says promotion_candidate and "
 "nothing supports that word.",
 f"{S2D}; {S2R}; {X1}")

add("asia_pdl_fade","s2","GEOMETRY_WRONG","candidate_book",
 "During the Asian session, price that pierces the prior day's low and then closes back above it has swept resting stops and "
 "reverses — buy the reclaim.",
 CB0, "Confidence 0.25, status promotion_candidate_recency_oos_watch_natgas_split_applied. "+CUB,
 "ASIA_HI 6, PIERCE 0.05, STOP_BUF 0.10, TARGET_R 3.0 — ALL FOUR shared with liq_asia_up_low_metal (x2's liquidity-sweep clone "
 "pair). The stop is wick-derived: a sweep that barely pierces gives a tiny stop.",
 "THE ONE FAMILY IN THE ESTATE WHERE THE OWNER'S HYPOTHESIS IS CONFIRMED AT BOTH MECHANISMS AND THERE IS SOMETHING TO CAPTURE. "
 "Declared horizon 32 M15 bars (8 h); realised median hold 4 bars, p90 38, 12.2% exceed the horizon. x1 tags it TOO_SHORT AND "
 "TOO_TIGHT: its drift peaks at h*=320 trading hours while its contract closes it in ~1 h, and its cost_r is 0.358. Its CEILING "
 "IS +78.03 bps [+18.45,+141.44] — CI EXCLUDES ZERO, on 2,761 trades over 194 days. Cost bands move R/day by 0.98 (flat -0.0873 "
 "-> high -1.0649), a swing nothing else in the estate comes near.",
 "2,827 trades, 942.3/yr across 30 symbols — the estate's dominant co-firing source; exits stop 69.4% / target 28.1% / maxbars 2.5%; "
 "median MFE +1.27 R against a 3.0 R target only 28.9% reach.",
 "THE DEFECT IS THAT THE STOP IS AN ACCIDENT OF THE SWEEPING BAR, AND THE CURE IS TO STOP DERIVING IT THAT WAY — the same "
 "conclusion lane g3 reached independently for cross_asset_lead_lag and structural_distance_extreme. Repair: floor the stop at a "
 "fixed ATR multiple (max(wick + 0.10*ATR, k*ATR)), sweep k, and RE-LABEL THE STORED INTENTS — no generator re-run, no new data. "
 "Second: its cluster assignment (liquidity_sweep, ONE cluster for thirty instruments spanning FX, metals, crypto, energy and "
 "indices) makes it a single risk unit that can hold thirty correlated positions. WORTH: the band spread says cost is ~1 R/day of "
 "the answer, and it is the ONLY sleeve outside the armed set whose contract-free ceiling interval excludes zero — the wave's one "
 "unambiguous 'sound idea wearing the wrong contract'.",
 f"{S2D}; {S2R}; {X1}; {X1C}")

add("liq_asia_up_low_metal","s2","IDEA_WRONG","candidate_book",
 "In metals only, during the Asian session, in a prior-day up regime and a low intraday-vol state, a swept-and-reclaimed prior-day "
 "high or low reverses.",
 CB0, "496 birth trades, of which this archive can see 157. Confidence 0.25. "+CUB,
 "ASIA_HI 6, PIERCE 0.05, STOP_BUF 0.10, TARGET_R 3.0 — four of four inherited from asia_pdl_fade. Its two extra gates (D1-up, "
 "low-vol) were chosen in-sample on 496 trades.",
 "Declared horizon 16 M15 bars (4 h) — the shortest in the candidate book; median hold 3 bars, p90 18, 11.5% exceed it. Median MFE "
 "+1.38 R against a 3.0 R target reached by 30.6%; median MAE -1.26 R. AU prices its short horizon at +0.0866 R/day IN ITS FAVOUR "
 "— the live 16-bar contract beats the published 80-bar walk. So the geometry is NOT the problem. Its cost_r is 0.877 — THE "
 "HIGHEST IN THE ESTATE: it pays 0.877 R per trade in toll before the trade has an opinion.",
 "157 gated trades, 52.3/yr. Signal at own hold -0.070x.",
 "READ THE VERDICT PRECISELY: the SWEEP-RECLAIM premise is not refuted — its parent carries it. What is refuted is that this is a "
 "DISTINCT MECHANISM deserving its own registry row, its own 0.25 confidence and its own corr-cluster. DEMOTE IT TO A CONDITION ON "
 "ITS PARENT: if the D1-up + low-vol pair is real it is a quality flag on asia_pdl_fade's metals rows and can be tested as one on "
 "the parent's 2,827-row population instead of on 157 — a strictly stronger test, no new data, no new code. That also deletes a "
 "registry row, deletes a corr-cluster, and removes one of the three groups whose collapse moves the Kelly-lite multiplier. If it "
 "does not survive as a flag on the parent, it was never a sleeve.",
 f"{S2D}; {S2R}; {X1}")

add("ny_crypto_momentum","s2","UNDETERMINED","candidate_book",
 "When the New York session's crypto move has been clean and one-directional, and volatility is not low, the move continues into "
 "the session close.",
 CB0, "Birth: +0.2017 R pooled with a correct random-entry null at p=0.0007 on roughly three times the sample the gate can see. "
 "Confidence 0.35. "+CUB,
 "DE_THRESH 0.50, STOP_MULT 1.3, VOL_LO 0.34, VOL_WIN 480, WINDOW 12, DECISION_MIN 0, VOL_HI 0.67 — SEVEN constants identical to "
 "ny_index_momentum and kz_london_crypto_low; only DECISION_HOUR and MAXBARS are genuinely per-cell (x2's killzone triplet). "
 "final_target_r None and broker_take_profit_mode none — correct for a hold-to-close idea.",
 "THE ONE CANDIDATE SLEEVE WHOSE HORIZON ACTUALLY BINDS, AND IT BINDS AS DESIGNED. Declared 20 M15 bars = hold to ~22:00 session "
 "close; realised median hold 8 bars, p90 80, 37.0% hit the horizon (exit_mix maxbars 24.7%). AU prices the live 20-bar contract "
 "at +0.2032 R/day BETTER than the published 80-bar walk. The geometry matches the premise; that is not where it fails.",
 "559 trades, 186.3/yr, 2024-2026 only. Ratified gate: -0.248 R/day, p 0.4858, 2 of 5 folds positive.",
 "I WILL NOT CALL THIS IDEA WRONG ON 2.5 YEARS OF DATA WHEN ITS BIRTH CLAIM RESTS ON THREE TIMES THE SAMPLE AND THE RIGHT NULLS. "
 "THE REPAIR IS A DATA FETCH — deep M15 history, the same unblock as the rest of the candidate book; AV_DEEP_H4_INGEST_V1.json "
 "already built exactly this harness for H4 and nothing equivalent has been scoped for M15. Second, before any re-test: this "
 "sleeve, kz_london_crypto_low and ny_index_momentum are ONE RULE with seven shared constants at three (session, asset-class) "
 "cells and must be declared as one family with three cells — otherwise the multiplicity bill triple-counts a single hypothesis, "
 "which is precisely why significance is the binding gate on 13 of 15 sleeves in this lane.",
 f"{S2D}; {S2R}; {X2}")

add("kz_london_crypto_low","s2","IDEA_WRONG","candidate_book",
 "The same clean-directional-move continuation as ny_crypto_momentum, but at the London 12:00 decision bar and only when "
 "volatility is LOW.",
 CB0, "Its own birth note conceded the drift null was marginal at p~0.085 and that the original weight was 'weak additive'. "
 "Confidence 0.10. "+CUB,
 "Six of its nine constants are ny_crypto_momentum's.",
 "Declared 32 M15 bars (8 h) hold-to-London-close; realised median hold 10 bars, p90 80, 23.4% reach the horizon. No fixed target, "
 "correct for the idea. AU prices the live 32-bar contract at +0.2322 R/day BETTER than the published 80-bar walk — THE LARGEST "
 "published-understates-live gap in the estate. So its contract is right and its published number is the wrong one. Its ceiling is "
 "-7.45 bps [-12.28,-1.89] — CI EXCLUDES ZERO ON THE NEGATIVE SIDE.",
 "286 trades, 95.3/yr. 42.7% of its trades are the same symbol-day-side as orb_crypto_london, which trades the same two coins in "
 "the overlapping London window.",
 "TWO INDEPENDENT REASONS, WHICH IS WHY THIS ONE GETS A HARDER VERDICT THAN ITS NY SIBLING. (1) It fails every core gate at its own "
 "best exit cell — expectancy included, 2 of 5 folds, p 0.66 — so unlike ny_crypto_momentum this is not a short-window ambiguity. "
 "(2) It is not a distinct object. Retire it as a sleeve and re-declare it as a CELL of the killzone family, which costs nothing, "
 "removes a registry row, and makes the family's multiplicity bill honest. At confidence 0.10 the direct sizing effect is small; "
 "the value is that it stops a single hypothesis being counted three times in a family where significance is the gate that kills "
 "everything.",
 f"{S2D}; {S2R}; {X1C}")

add("orb_crypto_london","s2","UNDETERMINED","candidate_book",
 "Build the London opening range on crypto; the first bar that closes beyond it continues in that direction, when volatility is low "
 "and the higher timeframe is trending.",
 CB0, "Birth claim 2,375-2,706 trades — and THE TWO PUBLISHED VERSIONS OF THAT CLAIM DISAGREE WITH EACH OTHER: a reader of "
 "candidate_registry.py and a reader of orb_crypto_london.py get different numbers for the same sleeve. Confidence 0.35. "+CUB,
 "80 M15 bars (20 h) horizon, 2.0R target.",
 "Declared 80 M15 bars — the longest M15 horizon in the book, and the ONLY candidate sleeve whose MAXBARS equals AA's walk horizon, "
 "so its published and live numbers agree exactly (restamp_error 0.0000). Realised median hold 13 bars, p90 38, "
 "frac_over_live_horizon 0.0000: the 20-hour horizon never binds. Median MFE +1.16 R against a 2.0 R target reached by 35.5%. Its "
 "geometry is the one thing that does NOT need repair.",
 "858 trades, 286.0/yr on two coins, 49% long, 2024-2026 only. Cost band moves it by only 0.14 R/day, so unlike asia_pdl_fade this "
 "is not a stop-geometry problem.",
 "Not adjudicable: the gated window is 2.5 years against a birth claim of ~2,500 trades. Sequencing: (1) deep M15 fetch — the same "
 "unblock as the rest of the candidate book; (2) reconcile the two birth tuples or strike both at source; (3) declare the crypto "
 "continuation family ONCE (this, ny_crypto_momentum, kz_london_crypto_low) instead of three times. Its clean geometry makes it the "
 "control for any horizon work on its siblings.",
 f"{S2D}; {S2R}")

add("vss_fxcross_london_up_low","s2","UNDETERMINED","candidate_book",
 "JPY crosses and EURGBP that compress into a narrow box during London, in a prior-day up regime and a low-vol state, break out of "
 "the box and run.",
 CB0, "860 birth trades and an out-of-sample daily mean of +0.001194. Its own author labelled it oos_decay_watch. Confidence 0.12. "+CUB,
 "TWELVE free parameters — a box-breakout with a squeeze percentile, a vol percentile, a D1 regime gate and two SMAs. Stop 1.0 ATR "
 "and target 2.0 ATR are genuine parameters rather than structure, which is unusual here and defensible.",
 "Declared 48 M15 bars (12 h); realised median hold 3 bars, p90 7, frac_over_live_horizon 0.0000 — the horizon never binds, and "
 "27.6% of trades are decided inside the entry bar. Exits stop 58.8% / target 41.2% with NO maxbars exits at all — the cleanest "
 "resolution profile in the lane. Median MFE +1.36 R against a 2.0 R target reached by 41.6%.",
 "308 gated trades, 102.7/yr, 2.5 years.",
 "Twelve free parameters on 860 birth trades is a sleeve that was fitted, but 308 trades on 2.5 years makes 'the idea is wrong' "
 "overreach. THE PROPORTIONATE REPAIR IS NOT MORE MEASUREMENT — IT IS PARAMETER REDUCTION BEFORE ANY RE-TEST: ask whether the plain "
 "20-bar box breakout in London on these five crosses carries anything at all. That is a nested-model test on the same rows, costs "
 "one walk, and would tell you whether there is a sleeve here or four filters on noise. Until then it should not be sized: at 0.12 "
 "confidence and 103 trades/year it cannot move the book either way, so the only thing it currently contributes is one more member "
 "to the family bill that is killing everything else.",
 f"{S2D}; {S2R}")

add("vol_squeeze","s2","STALE","candidate_book_quarantined",
 "Indices that compress into a low-ATR regime and then print an expansion bar with a large body, in the higher-timeframe trend "
 "direction, keep going.",
 CB0+" Quarantined for fourteen months with no redesign scheduled.",
 "Quarantined for a book-level correlated-risk drag on indices. Its cited generator does not exist.",
 "H4 clock, structural stop plus 0.3 ATR, 3R target, no declared time stop.",
 "NOT MEASURABLE: it is not in CANDIDATE_BUILT, so active_specs can never return it, and it produced zero rows in the estate walk.",
 "Zero rows anywhere, ever.",
 "Its quarantine reason is the most interesting thing about it and it is now diagnosable: it was dropped for an index "
 "correlated-risk drag, and this lane measured that the governor's cluster keying is what makes index sleeves collide (US30_cash "
 "sits in four clusters, UK100 and GER40 in four each). So the honest question is whether vol_squeeze was a bad sleeve or a victim "
 "of a clustering defect, and it is answerable at ZERO COST by re-running the book MC with index sleeves in ONE cluster. That said: "
 "it has never emitted a row and its cited generator does not exist. DELETE IT unless the cluster question is actually going to be "
 "asked — in which case preserve its docstring's negative control (coil breakout without the vol-state = NULL every split) as the "
 "design note it is.",
 f"{S2D}; {S2R}")

add("ny_index_momentum","s2","STALE","candidate_book_quarantined",
 "The same clean-directional NY continuation as ny_crypto_momentum, on stock indices, restricted to a mid-volatility state.",
 CB0, "Its own leave-one-out says the book improved when it was dropped.",
 "NINE constants, seven of them ny_crypto_momentum's, inherited unmodified onto a different asset class with a different session "
 "structure — the same category of transfer lane g4 found when the H4 microstructure book was ported onto an M15 clock.",
 "Not measurable: not in CANDIDATE_BUILT, zero rows in the estate walk.",
 "Zero rows on either live namespace and in every estate artifact.",
 "DELETE IT. Three independent reasons, each sufficient: it is a nine-constant clone of a sleeve that is itself unresolved; its own "
 "leave-one-out says the book improved when it was dropped; and it has produced zero rows anywhere. There is nothing to repair "
 "because there is no distinct hypothesis — if the killzone-continuation rule is ever re-tested on deep M15, indices are a CELL of "
 "that test, not a sleeve. Keeping it costs a registry import, a catalogue row, a family member in every multiplicity count that "
 "enumerates CANDIDATE_NAMES, and a reader's time. THE CLEAREST DELETION IN THE ESTATE.",
 f"{S2D}; {S2R}")

add("structural_retest","s2","STALE","candidate_book_quarantined",
 "A structural break (order block, breaker, displacement, sweep or FVG) that is retested continues in the higher-timeframe regime "
 "direction — fired only in verified (class, session, regime, vol) cells.",
 CB0+" Shares ATR_STOP_FLOOR 0.25 and STOP_BUF 0.10 with metals.py and metals_ob_micro.py (x2's metals triplet).",
 "Per-trade edge at birth +0.057 to +0.143 R — an edge smaller than a typical M15 cost. Its own daily-unit audit then measured it "
 "NEGATIVE on every split (-0.071 R daily mean), which is the level that decides a book.",
 "Fixed 2R with a 32-bar M15 time stop.",
 "Not measurable: not in CANDIDATE_BUILT, zero rows in the estate walk.",
 "Zero rows anywhere.",
 "A COMPLETED KILL, not an open question, and unlike vol_squeeze the reason is not a clustering artifact. The only reason to keep "
 "the file is that its three verified cells are a written statement of where a retest mechanic was thought to work, and lane g1's "
 "forensic on the POI families makes that statement worth preserving as prose. RECOMMENDATION: delete the module and the catalogue "
 "row, and lift the three-cell table into the g1 dossier as historical intelligence first, exactly as the cleanup policy "
 "prescribes ('extract useful intelligence into current summaries before deleting').",
 f"{S2D}; {S2R}")

# ---------------- mx COHORT ----------------
def mx(name, verdict, premise, birth, geom, life, repair):
    add(name,"s2",verdict,"market_expansion_mx",premise,MX0,birth,MXP,geom,life,repair,f"{S2D}; {S2R}; {X1}; {X1C}")

mx("mx_btcusd_d1_donchian_20_breakout","SOUND_BUT_TOO_SMALL",
 "Bitcoin that closes above its own prior 20-day high keeps going.",
 "THE ESTATE'S ONLY GENERATOR THAT HAS EVER CLEARED ITS OWN RATIFIED STANDARD — and the admission was REVERSED SIX DAYS LATER. "
 "Raw p 0.0106, 4 of 5 chronological folds positive, +0.53 R/trade OOS at target_5R. Wave 10 measured that the admission DECAYS "
 "chronologically: recent folds +0.198 R/day against +1.504 in the early ones (13.2%).",
 "Median hold 3 D1 bars, p90 10, horizon inert at 80. 82.3% of trades hold past 24 h, which is why AQ's time-stop unit repair was "
 "worth +0.2722 R/day here — the largest positive repair delta in the cohort. Median MFE +1.52 R, the highest in the cohort; 45.3% "
 "reach 2R, which is what makes the 5R target cell coherent rather than fitted. AU's ladder puts its best cell at h=40. x1: signal "
 "at its own 72 h hold +146.74 vs a 58.92 bps toll = 2.49x, ceiling +203.17 bps [+32.62,+397.30] — CI EXCLUDES ZERO.",
 "318 trades, 31.8/yr. ARMED FTMO 2026-07-31 at confidence 0.025; DISARMED 2026-08-05 by owner instruction (host commit 2fa77722d, "
 "--tags and --frontier-exits removed, no config byte moved so the token digest is unchanged) after A1b's corrected permutation "
 "null flipped it ADMIT -> REJECT (q 0.048 -> 0.129 at mid).",
 "THE IDEA DID NOT MOVE; THE MULTIPLICITY POSTURE DID. This lane's contract-free instrument reads it 2.49x, positive and CI-clean "
 "from 72 h — the directional content is real and the disarm was a governance call on the family bill, not a finding about the "
 "setup. LANE DISAGREEMENT, RECORDED: s1 filed SOUND, s2 filed SOUND_BUT_TOO_SMALL; this synthesis takes s2's, because the binding "
 "constraint is size and bill rather than idea or geometry, and at registry confidence 0.025 the arming was economically inert by "
 "design. Two things stay on its file: (1) it is the estate's proof that an INHERITED TARGET is a real defect — 2R rejects, 5R "
 "admits, and the difference IS the admission; (2) AQ's want = budget + 64 hazard: at the repaired 7,680-bar time stop an open mx_* "
 "position requests 7,744 M15 bars per tick and the stop degrades to INERT if the terminal returns fewer. Cleared at 7,800 bars on "
 "both terminals, but it must be re-measured before any mx_* sleeve is armed again. Merging it with mx_ethusd and vol_compression "
 "into one declared member shrinks the family bill that is the only thing it fails on.")

mx("mx_ethusd_d1_donchian_20_breakout","SOUND_BUT_TOO_SMALL",
 "Ether that closes above its own prior 20-day high keeps going.",
 "5 of 5 chronological folds positive, +0.426 R/trade OOS at target_5R, raw p 0.0308. Only failing gate is significance.",
 "Median hold 3 D1 bars, p90 10; horizon inert at 80. Median MFE +1.40 R; 41.8% reach 2R. AQ's repair from the 1-bar accident was "
 "worth +0.0674 R/day — positive, so it wanted a LONGER hold — and AU's ladder then found the optimum at 10 bars (+0.0838 vs "
 "+0.0240 at 80 and -0.0434 at 1). It is the one mx sleeve whose declared short horizon is a genuine intermediate rather than a "
 "return to h=1. x1 ceiling +250.81 bps [+16.52,+494.20] — CI EXCLUDES ZERO.",
 "311 trades, 31.1/yr.",
 "A DECLARATION REPAIR WITH NO CODE AND NO DATA: collapse mx_btcusd + mx_ethusd + vol_compression into a single 'crypto D1 channel "
 "breakout' member with a per-symbol breadth check. That is the shape AF's coherence test (dispersion ratio < 1 AND all members "
 "positive) was built for and which this trio might actually pass — the two mx members are 5/5 and 4/5 folds positive and "
 "vol_compression is positive at all four cost bands. It converts three marginal singletons into one member with three carriers, "
 "which is the only structure in this estate that has ever cleared a family bill.")

mx("mx_avausd_d1_donchian_20_breakout","UNDETERMINED",
 "Avalanche that closes above its own prior 20-day high keeps going.",
 "THE LOWEST RAW p OF ANY mx SLEEVE — 0.0030, better than mx_btcusd's 0.0106 — with 5 of 5 positive folds and q 0.2001. And the "
 "estate CANNOT evaluate it at the ratified rule because only 34 of its 189 trades fall on RECORDED eras.",
 "Median hold 3 D1 bars, p90 14; horizon inert. Median MFE +1.31 R; 39.7% reach 2R. Its best exit cell is the ONLY trail cell to "
 "win anywhere in the cohort (trail_a1_g0.5_prod) — a different geometry from every other mx sleeve, and it was not followed up.",
 "189 trades, 31.5/yr. NOT_EVALUABLE at the ratified population rule. redacted_account cannot trade AVAUSD, so it can only ever be a "
 "single-account sleeve.",
 "THE MOST INTERESTING UNRESOLVED CELL IN THE COHORT AND NOBODY HAS SAID SO. Three things follow. (1) The right question is a "
 "COVERAGE question, not an economics one: why does AVAUSD have 155 of 189 trades outside RECORDED, and is that a property of the "
 "instrument's era coverage rather than of the sleeve? Answerable from POPULATION_RULE_V1.json's own conditions in under a session. "
 "(2) Its winning cell is a TRAIL, unique in the cohort, and no one asked whether the trail is the reason or an artifact of 189 rows. "
 "(3) I am DELIBERATELY NOT calling this sound: a p of 0.0030 on the one cell the ratified rule cannot see is exactly the shape of a "
 "false positive, and saying so is more useful than promoting it.")

mx("mx_nzdjpy_d1_donchian_20_breakout","IDEA_WRONG",
 "NZD/JPY that closes above its own prior 20-day high keeps going.",
 "Longest history (2007-2026), largest sample (503 trades, 349 gated), most exit cells swept — and ZERO of five chronological "
 "folds positive, p 0.9701, failure on every core gate including expectancy.",
 "Longest realised hold in the cohort — median 4 D1 bars, p90 10 — with the horizon still inert at 80. Median MFE +1.18 R, the "
 "second-lowest; only 35.0% reach 2R. Its best exit cell is partial_1.5R_be and it is negative there too. x1: IR -0.0709, RATIO "
 "-2.250 — the worst mx reading, and its ceiling is negative at every horizon.",
 "503 trades, 25.1/yr, 2007-2026.",
 "NOT REPAIRABLE AND IT SHOULD BE SAID PLAINLY, BECAUSE THIS IS THE COHORT'S BEST TEST OF ITS OWN PREMISE. A 20-day channel "
 "breakout on a carry-driven FX cross is not the same object as one on crypto, and the measurement says so. The useful consequence "
 "is not for this sleeve but for the family: the cohort's three DONCHIAN members split cleanly by asset class (BTC 4/5 folds, ETH "
 "5/5, AVAUSD 5/5 but unevaluable — all crypto; NZDJPY 0/5 — FX). PRESCRIPTION: retire it from the 12-policy, and stop describing "
 "the Donchian rule as instrument-agnostic — it is a crypto rule with an FX member attached, and the FX member is the control that "
 "proves it.")

mx("mx_cadjpy_d1_volume_surge_reversal","IDEA_WRONG",
 "CAD/JPY that moves on abnormally high daily volume reverses the next day.",
 "286 trades over nineteen years; fails expectancy at p 0.89. AU returned MEASURED_BUT_NOT_PRESCRIBED at h=20 because every cell "
 "is negative.",
 "Median hold 3 D1 bars, p90 12; horizon inert. Median MFE +1.04 R — the lowest but one in the cohort; only 37.4% reach 2R and "
 "33.2% never reach 0.5 R. AQ's repair was worth +0.0523 R/day (positive), so it wanted the longer hold.",
 "286 trades, 15.1/yr.",
 "THE PREMISE HAS A CATEGORY PROBLEM BEFORE IT HAS AN ECONOMICS PROBLEM: 'volume surge' on a JPY cross is a tick-update count, and "
 "VOLUME_Z_THRESHOLD=2.0 was set once for all eight volume-surge sleeves across indices and FX with no per-class derivation. There "
 "is no repair worth buying — fixing the volume proxy would require a real volume series that does not exist for an FX cross. "
 "RETIRE IT WITH mx_nzdjpy, and note the pattern for the record: BOTH jpy_fx cluster members fail on every gate while the "
 "indices_context volume-surge members do not, which is exactly what you would expect if the volume proxy carries information on an "
 "exchange-traded index and none on a cross.")

for nm, lbl in (("mx_ger40_cash_d1_volume_surge_reversal","GER40"),
                ("mx_jp225_cash_d1_volume_surge_reversal","JP225"),
                ("mx_us30_cash_d1_volume_surge_reversal","US30")):
    mx(nm,"SOUND_BUT_TOO_SMALL",
     f"The {lbl} cash index that moves on abnormally high daily volume reverses the next day.",
     "Positive at all four cost bands, 4 of 5 folds positive, fails on SIGNIFICANCE ALONE — but fires ~16 times a year on one "
     "instrument, so no amount of contract work changes the answer: sample-starved, not broken.",
     "Median hold 3 D1 bars, p90 9, horizon inert at 80. Median MFE +1.20/+1.47/+1.20 R across the trio; 2R reached by "
     "36.4%/42.7%/38.0%. AQ's repair was NEGATIVE for ger40 (-0.1234) and us30 (-0.0837) and POSITIVE for jp225 (+0.0412) — two of "
     "three want the first day only and one wants the full research horizon, ON THE SAME RULE AND THE SAME CONSTANTS. That split is "
     "the cleanest evidence in the cohort that the horizon is a per-instrument property the shared machinery cannot express.",
     "110-121 trades each, 15.7-18.3/yr each.",
     "THE ONE REPAIR THAT IS BOTH CHEAP AND PRINCIPLED IS A POOLING REPAIR, NOT A PER-SLEEVE ONE. Eight of the fourteen mx sleeves "
     "are the identical volume-surge rule with identical constants; six are cash indices. Declaring 'D1 volume-surge reversal on "
     "cash indices' as ONE member with six carriers, pooled, is a single hypothesis with ~100 trades a year instead of six "
     "hypotheses with sixteen each — the only structure that can clear a family bill on this rule. AF's coherence test is the "
     "existing instrument for deciding whether that pooling is legitimate and IT HAS NEVER BEEN RUN ON THE mx COHORT. If the pooled "
     "member is built, its horizon must be a DECLARED property of the pool, not inherited.")

for nm, lbl, mfe, r2r, delta in (("mx_us100_cash_d1_atr_mean_reversion","US100","+0.88 R (the LOWEST in the cohort)","26.8%","-0.5913"),
                                 ("mx_us500_cash_d1_atr_mean_reversion","US500","+1.15 R","29.8%","-0.5567")):
    mx(nm,"SOUND_BUT_TOO_SMALL",
     f"The {lbl} cash index whose previous daily return exceeded 1.25x its own recent average true range reverses the next day.",
     "Eleven trades a year. AU declared a one-day horizon for both at time_stop_m15(1,'D1'), wired and default-off.",
     f"Median hold 3 D1 bars, p90 9-10; horizon inert at 80. Median MFE {mfe}; 2R reached by {r2r} — the two worst rates of the ten. "
     f"AQ's repair from the 1-bar accident was worth {delta} R/day — by far the largest NEGATIVE deltas in the cohort, so both "
     "sleeves are strongly better on a ONE-DAY hold and AU declared exactly that.",
     "67-71 trades each, ~11/yr each.",
     "The horizon question has been asked and answered for this pair and the answer is unusually clean — one day, declared, wired, "
     "default-off, worth +0.59 and +0.56 R/day against the 80-bar contract. What cannot be repaired at this scale is the sample. "
     "TWO OBSERVATIONS. (1) THE ONE-DAY RESULT IS THE MOST INTERESTING THING IN THE COHORT and it is not being read that way: a "
     "mean-reversion entry whose entire value is in the first day, with the second day actively giving it back, is a statement "
     "about how long the reversion lives — and it is the same shape lane g2 found on the at-market broad families (the extreme "
     "reverts within one bar) at a different timescale. (2) The coupling AD documented — these two sleeves read the stop distance "
     "in their entry signal — means the usual stop-ladder repair is INVALID here and any future work must re-run the generator, not "
     "re-label. Anyone who forgets that will produce a look-ahead artifact and call it an improvement.")

for nm, lbl in (("mx_eu50_cash_d1_volume_surge_reversal","EURO STOXX 50"),
                ("mx_fra40_cash_d1_volume_surge_reversal","CAC 40")):
    mx(nm,"UNDETERMINED",
     f"The {lbl} cash index reverses the day after an abnormally high-volume daily move.",
     "These two carried 22% of their own book's birth evidence — the highest exact-M1 event count and the highest ordered mean R — "
     "and have ZERO rows in every modern artifact.",
     "UNKNOWN. Not measurable from anything on this machine: no archive series exists for EU50.cash or FRA40.cash.",
     "0 trades in every estate artifact. Live-configured at 0.03 confidence each.",
     "THE ESTATE HAS TWO LIVE-CONFIGURED SLEEVES IT CANNOT MEASURE AND THEY CARRIED 22% OF THEIR OWN BOOK'S BIRTH EVIDENCE. That "
     "combination is the single most uncomfortable fact in the mx cohort, because it means the market-expansion book's strongest "
     "birth members are precisely the ones no later measurement has touched. THE REPAIR IS A DATA FETCH, not a sealed window: D1 "
     "series for two FTMO index CFDs, the cheapest possible acquisition, and it would let EXIT_FRONTIER, AQ and AU all recompute "
     "with no new code. Until then neither sleeve should appear in any published count of 'measured' market-expansion members and "
     "the cohort's aggregates should be stated as TEN OF TWELVE. Second: nobody has checked whether the FTMO EU50/FRA40 daily bars "
     "even align with the exchange session the volume-surge rule assumes — the same fixed-UTC-versus-exchange-session defect lane "
     "g4 found in session_open_range_break.")

for nm, lbl in (("mx_aus200_cash_d1_volume_surge_reversal","ASX 200"),
                ("mx_spn35_cash_d1_volume_surge_reversal","IBEX 35")):
    mx(nm,"STALE",
     f"The {lbl} cash index reverses the day after an abnormally high-volume daily move.",
     "NEGATIVE in their own birth ledger after swap.",
     "Not measurable: no archive series, no profile mapping, so the resolver produces a name that is on neither broker.",
     "0 rows anywhere. They are the two rows that make registry.py declare 34 SleeveSpecs while the system runs 32.",
     "DELETE BOTH. Four independent reasons and any one is sufficient: negative in their own birth ledger after swap; excluded by "
     "the only policy any configuration selects; no archive series so no gate can ever score them; and no profile mapping so the "
     "resolver produces a name on neither broker. Every reader who counts the registry has to discover the 34-vs-32 discrepancy for "
     "themselves. The one thing worth keeping before deletion is the collision record — mx_aus200_cash_d1_volume_surge_reversal "
     "beat mx_aus200_cash_d1_atr_mean_reversion on repaired full-book delta, which is a genuine piece of evidence hygiene worth one "
     "line in the cohort's design note.")

# ---------------- SIZING-ONLY ----------------
add("session_leadlag_genuine","x2","IMPLEMENTATION_WRONG","registered_for_sizing_no_generator",
 "A session lead-lag effect between two different symbols.",
 "Registered for SIZING at confidence 0.15 in CLEAN4_REGISTRY (admission.py:265-277) with a generator module present "
 "(src/components/ultimate_book/sleeves/session_leadlag.py) that sleeves/registry.py NEVER IMPORTS.",
 "A claimed forward +0.46 R on n=390, additive on the vol-matched stress MC, Sharpe 0.1522 -> 0.1586. Its cited artifact "
 "AA_ESTATE_WALK_RESULT.md resolves to NO FILE at HEAD.",
 "Unknown — it can never fire.",
 "Unmeasurable.",
 "A 33rd SLEEVE NOBODY HAS COUNTED. It can be SIZED and can NEVER FIRE. Because CANDIDATE_BOOK_V1 is built from active_specs it is "
 "not a family member, so its look is NOT BILLED — the estate took a look and did not pay for it. Its blocker is real and "
 "documented: the generator contract (registry.py:37) hands one symbol plus at most one same-symbol aux feed, and this sleeve needs "
 "a cross-symbol channel (supply.py -> LIVE_WIRING_GAP).",
 "EITHER remove it from CLEAN4_REGISTRY (it cannot contribute) OR extend the generator contract to a cross-symbol channel and then "
 "declare and bill the look. Doing neither is the current state and it is the worst of the three: a sizing weight with no possible "
 "generator output and an unbilled look.",
 f"{PROV}/x2_receipts/X2_WHY_DID_WE_BUILD_THESE.md; src/components/ultimate_book/admission.py:265-277")

# ---------------- MACHINERY ----------------
add("__machinery_POI_shared","g1","IMPLEMENTATION_WRONG","shared_machinery",
 "One code path proposes a resting limit at a price level all three POI families believe price will return to and react from.",
 "Introduced whole in 954f5a1573b73615324500d78d316f3a78709096 (2026-07-12), a 2,845-file commit titled 'chore(storage): establish "
 "non-iCloud GTOS hot workspace snapshot', +1,342 lines to src/components/broader_origin_generators.py. Absent at 86cccd08 "
 "(2026-06-15). No design note, no cited research, no test named, no A/B, and no branch carries a granular version.",
 "NOTHING. The specification survives (src/prompts/primary_analyzer_prompt.py + ADR-006) and is detailed; the code implements 0 of "
 "its per-family conditions.",
 "Entry = (zone_low + zone_high)/2 for all three (:1774), where both written specs that name an entry name the NEAR edge. "
 "Proximity 1.0% of price. Stop buffers applied to M15 ATR where ADR-006 defines them in H1 ATR (measured ratio 2.091, n=102,507). "
 "risk.sl_buffer_breaker_atr_multiplier: 0.5 and risk.sl_buffer_min_ticks: 5 are never read by any broad-V4 code.",
 "Measured on the M1 tape with the stop held fixed and only the entry moved: near-edge fills 28.8/11.6/36.4% at 11.20/14.82/13.63 "
 "bps; the shipped MIDPOINT 22.5/6.8/29.1% at 7.39/9.14/7.93 bps; far edge 17.9/4.1/24.5% at 3.18/3.27/2.01 bps. The midpoint "
 "optimises NEITHER leg — it forfeits 20-41% of the near edge's fills and still carries 2.3-4.0x the far edge's risk distance. "
 "Nothing in the repository argues for it.",
 "1,066,352 POI emissions over eight windows collapse to a few thousand zones for two of three families (candidate identity keys on "
 "poi_id when present and on candle_open_utc when not; only fvg_fill sets poi_id, so ~260,741 distinct candidate identities exist "
 "for 7,922 actual zones). Of 212,164 symbol-instants carrying any POI candidate, 31.2% carry 2+ families and 45.8% carry a LONG "
 "and a SHORT on the same symbol at the same instant — the port also deleted the design's deterministic 3-level tiebreaker, turning "
 "'one winner per bar' into a two-sided book.",
 "THE PORT IS THE ROOT CAUSE AND IT WAS INVISIBLE. Repairs, cheapest first: (1) the far-side R gate is ALREADY WIRED AND OFF — "
 "broad_origin_emission_contract.py has DEFAULT_MAX_ADMISSION_GAP_R = None and its own docstring names the right value; setting "
 "gtos_vnext_runtime.broad_origin_poi_max_admission_gap_r = target_rr removes 84.3%/91.6%/62.3% of the three families' emissions "
 "with no new code. (2) restore near-edge entry. (3) fix the ATR timeframe conversion. (4) read the two unread risk keys. (5) carry "
 "the two validated quality gates off the LLM path (gate1.touch_count_reject_threshold: 2, evidence 72.7% vs 31.5%; "
 "filters.max_gap_pct: 1.5). (6) restore the tiebreaker. HONEST CAVEAT, which is r2's own: none of this saves the families — the "
 "correctly-formed resting-limit book still books -0.24981 R/fill. Do it because ~90% of the estate's POI candidate volume, and "
 "every multiplicity bill computed over that volume, is an artifact.",
 f"{PROV}/G1_THREE_POI_FAMILIES_DOSSIER.md; {PH20}/SESSION_R2_GENERATOR_REPAIR.md; {PROV}/G1_FILL.json")

add("__machinery_mx_shared","s2","IMPLEMENTATION_WRONG","shared_machinery",
 "One D1 code path proposes three rules — a 20-day Donchian breakout, a volume-surge reversal, and an ATR mean reversion — computed "
 "on the last completed daily bar and entered at the next daily open.",
 MX0, "All 21 of its own research routes closed promotion_ready: false with five named requirements open, and the config was set "
 "true the same day.",
 MXP,
 MXG+" Entry timing is deliberate and CORRECT ('signal from the latest completed D1 bar, intent stamped for the next D1 "
 "session/open'), which avoids the entry-at-the-extreme defect lane g2 found across the broad-origin families.",
 "10 of 14 sleeves produce rows; 2 have no archive series; 2 have neither series nor profile mapping. Registry declares 34 "
 "SleeveSpecs while the system runs 32.",
 "THE VERDICT IS ABOUT WIRING AND GOVERNANCE, NOT ABOUT THE THREE RULES — Donchian breakout, volume-surge reversal and ATR mean "
 "reversion are all documented effects and the D1 clock is right for all three. What is wrong is that a book whose every artifact "
 "says NOT PROMOTED, with five requirements open by name and never closed, is true in config and carries 0.30 of registry "
 "confidence weight for a measured +0.022 %/month. Three repairs, cheapest first: (1) CLOSE OR CITE MX-READINESS-REQ-001..005 — "
 "they ARE published at .context/00_core/research_current_state.md:513-517 and NOTHING AT HEAD CLOSES THEM; half a session of "
 "archaeology and the highest-value item here. (2) VENDOR THE EVIDENCE OR DELETE THE CLAIM — the 21 routes are on two VPS branches "
 "HEAD cannot reach; 41425481e already set the precedent. (3) RENAME OR RE-KEY activation_weight_now: a field that reads 0.0 on "
 "every sleeve that is being sized is a trap, the same class of unit-vs-value confusion AQ found in time_stop_bars.",
 f"{S2D}; {S2R}; src/components/ultimate_book/sleeves/market_expansion_d1.py; .context/00_core/research_current_state.md:513-517")

pickle.dump(V, open(f"{P}/_v_broad.pkl","wb"))
import collections
c=collections.Counter(v["verdict"] for k,v in V.items() if not k.startswith("__"))
print("generator records:", sum(1 for k in V if not k.startswith("__")), "machinery:", sum(1 for k in V if k.startswith("__")))
for k,n in c.most_common(): print(f"  {k:24s} {n}")
