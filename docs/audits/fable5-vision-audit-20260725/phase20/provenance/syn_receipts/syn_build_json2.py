"""SYNTHESIS part 2 — sleeve records + machinery records + assembly."""
from __future__ import annotations
import json, os, pickle, datetime, collections

P = os.path.dirname(os.path.abspath(__file__))
PROV = os.path.dirname(P); PH20 = os.path.dirname(PROV)
V = pickle.load(open(f"{P}/_v_broad.pkl","rb"))

def add(name, lane, verdict, cls, premise, origin, birth, params, geom, life, repair, ev):
    V[name] = dict(name=name, lane=lane, verdict=verdict, klass=cls, premise=premise,
                   origin=origin, claimed_at_birth=birth, parameters=params,
                   geometry=geom, lifecycle=life, repairable=repair, evidence=ev)

S1D = f"{PROV}/S1_ARMED_SLEEVES_DOSSIER.md"; S1R = f"{PROV}/s1_receipts/S1_DISCRIMINATOR_V1.json"
S2D = f"{PROV}/S2_REGISTRY_DOSSIERS.md"; S2R = f"{PROV}/s2_receipts/S2_REGISTRY_DOSSIER_V1.json"
X1  = f"{PROV}/x1_receipts/X1_VERDICTS_V1.json"; X1C = f"{PROV}/x1_receipts/X1_CEILING_V1.json"
SIX = ("All 51 generators enter git inside one of six bulk commits; ZERO has a birth commit whose message names the idea "
       "(x2, X2_BIRTH_COMMITS.txt, measured by git log --all --reverse -S<name> over 8,992 commits).")
CUB = ("research/operations/final_moonshot_principal_full_system_audit_2026_06_17/CORRECTED_UNIFIED_BOOK_MC_AUDIT.json — "
       "cited by candidate_registry.py as the source of EVERY confidence weight in the nine-sleeve candidate book, and "
       "IT HAS NEVER EXISTED IN THIS REPOSITORY ON ANY REF (s2, independently confirmed by x2's citation resolver).")

# ============================ CORE W7 (s1) ==================================
add("crypto","s1","SOUND","core_w7_armed",
 "After a strong run, a break of the prior 20-bar high/low on a market whose recent returns are positively autocorrelated keeps going.",
 "86cccd08d (2026-06-15), 793 files / +2,726,445 lines, 'deploy-live: lean branch = origin/main + live system + W7 deploy book "
 "+ VPS operator bundle'. " + SIX,
 "Published +0.751 R/trade. Cost-true OOS is now +0.0775 R — a -90% move in the headline with the direction intact. AE's "
 "cost-true lane is the only armed sleeve it would size UP (x1.08).",
 "Stop 2.00 x ATR14(H4) exactly (k measured 2.00 on 181 walked trades). No tuning constant in this module has ever changed "
 "value since its first appearance (x2, 24 of 24 constants across six sleeve modules).",
 "MATCHES ITS PREMISE. Premise timescale = ac60 over 60 H4 bars = 240 h. Realised median hold 52 h, p90 320 h; bars-to-MFE "
 "7 H4 = 28 h; MFE/|MAE| 2.035. Drift ladder +5.2/+37.4/+76.8/+282.5/+200.9/+484.8 bps at 4/8/24/72/160/320 h — it accumulates. "
 "Signal at its own 52 h hold +196.75 bps against a 54.99 bps toll = 3.58x.",
 "181 walked trades, 0 duplicates, 0 same-bar exits; exits 105 stop / 38 target / 38 maxbars; capture 28.1%. Mean archive "
 "spread_r 0.0044 against the live gate's 0.10 — the cheapest sleeve in the book relative to its stop.",
 "Nothing to repair. Two things to know: (1) plan against the cost-true +0.0775 R, not the published +0.751; (2) its "
 "net-vs-horizon curve is still rising at 320 h against a 52 h realised hold, so 'is the book cutting this winner short?' is a "
 "pre-registerable question worth ~+18 bps/trade at the 320 h argmax — but the carry model is linear-in-hours and the argmax is "
 "inside the CI, so it is a question, not a change. r1's quote-side repair costs it 23.5% of gross (+0.5673 -> +0.4339) on five "
 "trades of 181 — the largest single-sleeve move on armed money.",
 f"{S1D}; {S1R}; {X1}; {PH20}/SESSION_R1_QUOTE_SIDE_WALKER.md")

add("energy_agri","s1","SOUND","core_w7_armed",
 "Crude oil continuation pays in two near-disjoint states — an extreme volatility expansion or a flat trend — and the FVG-retest "
 "entry that works on gold works here too, but the persistence gate that powers gold destroys it.",
 "86cccd08d (2026-06-15), the same bulk commit. " + SIX,
 "KB +0.653/+0.911; registry +0.433 TRAIN; survivor book UNCONDITIONAL on both accounts. Its OOS/lifetime split (+0.6226 vs "
 "+0.047 R/trade) is the widest in the armed book and is the honest reason its confidence is 0.80 and not 1.00.",
 "Stop 1.31 x ATR14(H4). slope30 over 30 H4 bars. Never changed since birth.",
 "MATCHES ITS PREMISE, BUT THE PUBLISHED FIGURE DESCRIBES A DIFFERENT CONTRACT. Realised median hold 48 h, p90 259 h; "
 "bars-to-MFE 11 H4 = 44 h; MFE/|MAE| 2.188. Drift ladder +3.7/+47.7/+168.9/+497.5/+577.6/+368.2 bps — accumulates, peaks "
 "72-160 h. Signal at its 48 h hold +333.21 vs a 54.64 bps toll = 6.10x.",
 "67 walked trades — the thinnest armed sleeve; exits 40 stop / 22 target / 5 maxbars; capture 33.1%. Fixed cost 29.2 bps, the "
 "highest in the armed book.",
 "ONE REPAIR, AND IT IS A RESTATEMENT NOT A CODE CHANGE: republish this sleeve's economics at its live partial_be_runner exit "
 "instead of the plain exit. It is armed, and every figure the estate carries for it prices a contract the book does not run — "
 "worth 0.2302 R/day, measured, at every cost band (AU), corroborating AD 6.2's -0.308 R/day at n=67 through a second instrument. "
 "Its argmax at 160 h against a 48 h hold says the same thing from a second direction.",
 f"{S1D}; {S1R}; {X1C}")

add("sub_xvol_pullback","s1","SOUND","core_w7_armed",
 "In a strong up-regime with elevated volatility, when the short horizon disagrees with the long and persistence is neutral "
 "rather than trending, buying the dip with a wide target pays.",
 "86cccd08d (2026-06-15), the same bulk commit. " + SIX,
 "Highest per-trade gross R in the survivor book (1.30698 on n=90). Structurally absent from the live path until "
 "ultimate_book_include_clean3 was set true on 2026-07-29.",
 "Stop 1.00 x ATR14(H4) exactly. slope50 (200 h) and ac60 (240 h). Confidence 0.45 in admission.py:218-219 — the reason no "
 "confidence FLOOR can express the armed set, since metals_softband at 0.50 would be admitted by any floor low enough.",
 "BEST GEOMETRY-TO-PREMISE MATCH IN THE ESTATE. Realised hold 64 h, p90 165 h; bars-to-MFE 16 H4 = 64 h — MFE arrives EXACTLY "
 "at the realised hold; MFE/|MAE| 2.563 and capture 56.0%, both the highest in the estate. Drift ladder +53.5/+65.9/+121.9/"
 "+266.3/+501.5/+670.8 bps and the 95% day-block bootstrap CI EXCLUDES ZERO AT EVERY HORIZON — the only sleeve for which that "
 "is true. Signal at its own hold +242.24 vs a 28.45 bps toll = 8.51x, the highest in the estate.",
 "88 walked trades; exits 47 target / 37 stop / 4 maxbars — the horizon binds on 4.5%. Its ceiling at h*=320 h is +691.04 bps "
 "[+27.92,+1374.27]: CI EXCLUDES ZERO.",
 "NOTHING TO REPAIR, AND TWO THINGS BORHEN MUST SEE — described, not recommended. (1) Its train window is NEGATIVE (-0.190/-0.278 R) "
 "while its test window is +1.02/+1.37, on armed money (AU). [INFERENCE, flagged:] the two splits are different objects and the KB "
 "documented this shape in 2026-06 ('train EV concentrates in 2020 COVID vol n=25 +1.31; calm train years 2022-24 are thin and "
 "slightly negative'), so this lane reads it as documented regime-lumpiness rather than new information. What would SETTLE it is "
 "one join nobody has run: label AU's folds by realised volatility regime and check the negative folds are the calm ones. "
 "(2) Its frontier cell target_4R REJECTS at all four cost bands (p 0.0080 against a 0.002083 rank-1 bar), is wired default-off, "
 "and AU's handoff is 'do not propose it'. Also: at a declared family of m<=16 this sleeve ADMITS at alpha 0.10 (p 0.006099); at "
 "m>=17 it does not, and the estate now bills 59.",
 f"{S1D}; {S1R}; {X1C}; {PROV}/x2_receipts/X2_PROVENANCE_PATTERN_V1.json")

add("sub_mid_dn_revert","s1","SOUND_BUT_TOO_SMALL","core_w7_armed",
 "During the New York session, in a mid-volatility downtrend where price sits in the middle of its range, compression is normal "
 "and recent returns are mean-reverting, go LONG.",
 "86cccd08d (2026-06-15), the same bulk commit. " + SIX,
 "Folded at conf 0.20 on the estate's own MC ('mild stress drag -> keep at breadth conf 0.20, not higher'). AE's cost-true lane "
 "later demoted it from SIZE_UP x1.23 to HOLD_FLAG on a -0.0183 R OOS mean over 282 trades.",
 "Stop 1.00 x ATR14(H4) exactly — 44.07 bps, the second-narrowest in the armed book and only 4.5x the broad V4 family's 9.68, "
 "which is why it is the sleeve that proves stop WIDTH is not the discriminator.",
 "MATCHES, AND IT IS THE CHEAPEST CARRY IN THE BOOK. Realised hold 28 h, p90 99 h; bars-to-MFE 5 H4 = 20 h; MFE/|MAE| 1.702. "
 "Drift ladder +1.9/+9.6/+26.9/+63.0/+71.0/+72.2 bps, CI excludes zero from 8 h onward. Carry 0.068 bps/h, by far the cheapest. "
 "Signal at its own 28 h hold +29.95 vs a 6.33 bps toll = 4.73x.",
 "533 walked trades; exits 336 stop / 197 target / ZERO maxbars — the horizon never binds.",
 "NOT A REPAIR — A CALIBRATION NOTE. Its ratio (4.73x) is healthy but its absolute numbers are an order of magnitude below the "
 "rest of the armed book (+29.95 bps at hold against +196 to +333), which is exactly what conf 0.20 encodes. Two live facts: "
 "(1) the ratio and AE's cost-true mean disagree in SIGN and neither should be quoted without its population stamp "
 "(SLEEVE_DOSSIER_V1 rule R0); (2) its exit frontier on the RE-CLOCKED population moves from -0.106 R/day with expectancy FAILING "
 "to +0.092/+0.059/+0.008 with it PASSING, best cell time_stop_20 -> time_stop_40, so every pre-2026-07-30 figure for this sleeve "
 "is on the wrong clock.",
 f"{S1D}; {S1R}; {X1}")

add("metals_core","s1","GEOMETRY_WRONG","core_w7_pulled",
 "After a volatility expansion, when precious-metal returns are positively autocorrelated, price that retraces into the FVG left "
 "by an impulse and closes back in the higher-timeframe trend direction continues.",
 "86cccd08d (2026-06-15), the same bulk commit. Its 0.25 x ATR floor and 0.10 x ATR buffer (metals.py:33-34) are the two "
 "universal copied constants, shared with 7 and 8 modules respectively across BOTH code lineages (x2).",
 "Armed at confidence 1.00 — the highest in the estate — on a forward mean over n=49 metals trades in a single strong "
 "trend-persistence year. Its own KB says the companion OB variant's forward positive 'is carried by 2025, 2026 has only n=2 and "
 "is negative'.",
 "Stop 1.10 x ATR14(H4) = 105.03 bps. Mean archive spread_r 0.1247 against the live pre-trade gate's 0.10 "
 "(book_owner._spread_cost_screen :4685-4722; config/agent_config.yaml:715) — it sits AT the book's own refusal line.",
 "FOUR THINGS WERE WRONG. (1) The stop is at the book's own refusal line. (2) The exit keeps almost nothing: mean MFE 1.758 R, "
 "realised +0.195 R gross = 11.1% capture, the worst of any H4 sleeve. (3) IT DOES NOT ACCUMULATE: drift ladder "
 "-4.5/+1.8/+27.4/+17.4/+23.0/+75.8 bps, CI excluding zero at 24 h ONLY; net-of-cost is +4.5 bps at 24 h and NEGATIVE at every "
 "other horizon, argmax 24 h against a 36 h realised hold. (4) Signal at its own hold +24.92 vs a 27.22 bps toll = 0.92x — "
 "below one, on the sleeve that carried confidence 1.00.",
 "385 walked trades; capture 11.1%. Armed 2026-07-29 12:55, PULLED 14:25. AE's cost-true lane later landed on the same side "
 "(DOWN_WEIGHT x0.50 on a 232-trade/118-day OOS at -0.205 R).",
 "THE IDEA IS NOT WRONG AND THE LESSON IS NOT 'DISTRUST METALS'. The FVG-retest premise is the SAME premise energy_agri runs "
 "with a different state gate, and energy_agri measures 6.10x. Four things were wrong with the JUSTIFICATION and every one is a "
 "population or geometry problem: (a) n=49 in one year; (b) the cost model charged ZERO commission (F38) and credited tick "
 "erosion with the WRONG SIGN (F39); (c) its spread sits at the refusal line so a cost error of the size the estate actually had "
 "was enough to flip it; (d) it gives back 89% of what it reaches. REPAIR: an exit that keeps more of a 1.758 R excursion is "
 "worth up to 8x its current realised R and is the only lever large enough to matter; widening the stop would clear the gate but "
 "the drift ladder says there is nothing at 72 h+ to hold for. GENERALISABLE LESSON: confidence 1.00 was assigned on a per-trade "
 "forward mean, and the two things that killed it — cost-model direction and excursion capture — are invisible in a per-trade mean "
 "by construction.",
 f"{S1D}; {S1R}; {X1C}")

add("fx_jpy","s1","GEOMETRY_WRONG","core_w7_pulled",
 "JPY crosses show genuine intraday directional persistence off the London open that an H4 grid cannot see, because the whole "
 "move is inside one H4 bar: take the sign of the first London hour and ride it.",
 "86cccd08d (2026-06-15), the same bulk commit. " + SIX,
 "Confidence 0.15, honestly labelled. Session N measured that the broker charged swap on ZERO of its 32 live positions.",
 "Stop 0.99 x ATR14(M15) = 5.68 bps — SMALLER THAN THE BROAD V4 FAMILY'S 9.68 bps. config/agent_config.yaml:717-729 raises the "
 "spread ceiling to 0.35/0.45 FOR THIS SLEEVE BY NAME, stating in its own words that the ordinary GBPJPY spread 'is ~22% of that "
 "stop, which the global 0.10 spread / 0.15 total-cost gate CORRECTLY REFUSES'.",
 "THE GEOMETRY IS THE WHOLE FAILURE AND THE BOOK'S OWN GATE SAID SO BEFORE ANY OF THIS. Premise timescale is one session hour. "
 "Realised hold 0.8 h, p90 2.0 h; bars-to-MFE 2 M15 = 30 min; capture 4.4%. Drift at its own hold is -0.23 bps against a 1.33 bps "
 "toll = -0.17x. Ladder flat: -0.2/+0.0/+1.9/+1.3/+8.9/+9.2 bps — THE BROAD FAMILY'S SHAPE. The +9.2 bps at 320 h is real but "
 "UNREACHABLE under its own contract (a 2.5R target on a 5.7 bps stop is 14 bps of price; the time stop is 12 h).",
 "3,984 walked trades. Armed 2026-07-30 ~11:52, PULLED ~14:57 the same day on AV's evidence. Mean archive spread_r 0.1132 against "
 "the global 0.10 gate.",
 "THE PREMISE MAY WELL BE REAL AND THE CONTRACT CANNOT EXPRESS IT. At a 5.7 bps stop on a JPY cross the spread is 11-22% of R, so "
 "the sleeve is transacting inside its own noise the way the broad V4 family does — it is the estate's closest thing to a "
 "broad-V4-shaped sleeve on every axis (sub-10 bps stop, M15 clock, sub-hour hold, flat accumulation, spread comparable to R), and "
 "it failed in the same units and for the same reason. THAT IS THE STRONGEST SINGLE PIECE OF EVIDENCE THAT WAVE 19'S VERDICT IS "
 "ABOUT A CONTRACT CLASS AND NOT ABOUT ONE GENERATOR. A repair would have to give the idea a risk distance large enough that the "
 "spread is <10% of it — on a JPY cross at M15 that is a multi-ATR stop and therefore a different, unmeasured contract; or move it "
 "to a clock where ATR is 4.5x larger, which is a re-derivation. Its named repair (the meta-label filter) is measured EMPTY.",
 f"{S1D}; {S1R}; {X1}; config/agent_config.yaml:717-729")

add("metals_softband","s1","PARAMETERS_WRONG","core_w7_never_armed",
 "The same FVG-retest continuation as metals_core, but harvesting the persistence band the hard gate rejects (0.04 <= ac60 < 0.10), "
 "sized down by a ramp on ac and vr.",
 "86cccd08d (2026-06-15), the same bulk commit.",
 "No independent evidence: the band is DEFINED by what metals_core rejects. Confidence 0.50.",
 "Five size-ramp constants inherited whole, never swept. Stop 1.16 x ATR14(H4). The KB's own evidence for the ac60 gate is that "
 "EV is MONOTONE in the threshold — so a band strictly BELOW the validated threshold is, by the same evidence, the weakest part "
 "of the distribution.",
 "Realised hold 44 h, p90 320 h; MFE/|MAE| 1.929; capture 25.3%. Drift ladder +13.5/+9.6/+20.0/+20.3/+8.6/+64.2 bps — no monotone "
 "shape and no CI excluding zero at any horizon. Net-of-cost NEGATIVE at every horizon, argmax at 1 h. Signal at its own hold "
 "+20.15 against a 40.04 bps toll = 0.50x.",
 "237 walked trades. Mean archive spread_r 0.1083, over the live 0.10 gate.",
 "IT IS A RESIDUE, NOT A HYPOTHESIS. What would have to change: derive the band from its own forward evidence rather than from "
 "metals_core's complement, and sweep the five ramp constants that were inherited whole. What it would be worth: at 1.7% of the "
 "book's conf-weighted edge and a 0.50x ratio, essentially nothing — which is the honest reason to leave it alone rather than "
 "repair it. Its confidence of 0.50 is also the reason no confidence FLOOR can express the armed set.",
 f"{S1D}; {S1R}")

add("metals_ob_micro","s1","IDEA_WRONG","core_w7_never_armed",
 "The same continuation edge as the FVG retest, expressed on a different structure — an order block instead of a fair-value gap — "
 "restricted to the strong-persistence tail (ac60 >= 0.20) and deduplicated against the FVG entries.",
 "86cccd08d (2026-06-15). Shares ATR_STOP_FLOOR 0.25 and STOP_BUF 0.10 with metals.py and structural_retest.py (x2's metals triplet).",
 "Its own KB honesty section already said this: the forward positive is one year, n=2 in the following year, and the sleeve was "
 "kept explicitly under map-don't-kill rather than on its evidence. Confidence 0.30, default-off.",
 "Stop 1.13 x ATR14(H4).",
 "Realised hold 42 h, p90 320 h; MFE/|MAE| 1.300; capture -14.1% — IT GIVES BACK MORE THAN IT REACHES. Drift ladder "
 "-10.2/-36.0/-32.3/+27.2/-39.1/-61.2 bps — negative at five of six horizons, and the 8 h cell's CI EXCLUDES ZERO ON THE NEGATIVE "
 "SIDE. Signal at its own hold -9.96 against a 31.42 bps toll = -0.32x, the worst reading in the estate.",
 "34 walked trades over the whole archive — the honest limit on all of it. Mean archive spread_r 0.1107, over the live 0.10 gate.",
 "NOT REPAIRABLE AT THIS SIZE AND PROBABLY NOT WORTH REPAIRING. It contributes -0.7% of the book's conf-weighted edge, its capture "
 "is negative, and n=34 means no repair can be evaluated. Leave at conf 0.30 default-off or retire under the cleanup policy. NOTE "
 "that its premise — 'the SAME edge expressed on a different structure' — is exactly the claim the g1 lane refuted independently "
 "for current_ob_retest in the broad family: an order-block retest at an emitted age of days rather than hours is a cohort the "
 "founding study has almost no data on and what data exists says is far worse.",
 f"{S1D}; {S1R}; {PROV}/G1_THREE_POI_FAMILIES_DOSSIER.md")

add("idxrev","s1","IDEA_WRONG","core_w7_never_armed",
 "A failed breakout of the recent index range reverts: when a bar takes out the 16-bar high but closes back inside it, fade it.",
 "86cccd08d (2026-06-15), the same bulk commit.",
 "DEAD_BEFORE_COST on both accounts in SURVIVOR_BOOK_V1 — one of only two sleeves the estate had already written off before "
 "charging a broker cost.",
 "Stop 1.50 x ATR14(H4) = 73.11 bps; target 0.75R.",
 "THIS IS THE MEASUREMENT THAT ANSWERS BORHEN'S QUESTION. It is H4, its stop is 7.6x the broad V4 family's 9.68 bps, and its "
 "drift ladder is THE BROAD FAMILY'S SHAPE: +1.5/+1.5/+0.4/-4.4/+0.3/+2.9 bps. A wide stop on a slow clock does not manufacture "
 "accumulation. MFE/|MAE| 0.954 — BELOW ONE, the signature of a fade with a 0.75R target: it never gets ahead. Capture -0.4%. "
 "Signal at its own 16 h hold +0.94 against a 3.34 bps toll = 0.28x.",
 "5,597 walked trades — by far the largest sample in the core book, so none of this is small-n. Ceiling NEGATIVE at every horizon.",
 "NO REPAIR, AND ITS VALUE TO THE ESTATE IS AS A CONTROL RATHER THAN AS A SLEEVE. It is the cleanest available refutation of "
 "'the armed sleeves work because their stops are wide': same H4 clock as the armed four, a stop 7.6x the broad family's, a cost "
 "gate it passes easily, 5,597 trades, and a drift curve indistinguishable from the broad family's flat 0.19 bps. KEEP IT IN "
 "EVERY FUTURE COMPARISON as the negative control; the estate has been short of one.",
 f"{S1D}; {S1R}; {X1C}")

add("fx_jpy_ny","s1","SOUND_BUT_TOO_SMALL","core_w7_never_armed",
 "The same session-open momentum ride as fx_jpy but at the New York open, with two extra gates: the opening impulse must be at "
 "least 1.0 ATR and it must agree with the 20-bar M15 trend.",
 "86cccd08d (2026-06-15), the same bulk commit.",
 "Honestly labelled forward_only at conf 0.15 and never claimed more — nothing was over-sold. CARRY_CONDITIONAL_LIVE_SUPPORTED "
 "on both accounts.",
 "Stop 0.99 x ATR14(M15) = 7.63 bps. Its two extra gates (1.0-ATR impulse, 20-bar trend agreement) have NEVER been ablated, so it "
 "is not established that they do anything.",
 "Realised hold 0.8 h, p90 2.5 h; bars-to-MFE 2 M15 = 30 min; MFE/|MAE| 1.214; capture 3.4%. Drift ladder +0.0/+0.4/-1.2/-3.4/"
 "-2.6/+0.9 bps — flat and sign-unstable. Signal at its own hold +0.00 against a 1.32 bps toll = 0.00x: the sleeve is exactly a "
 "coin flip minus the spread.",
 "1,620 walked trades. Archive spread_r 0.0729 passes the global gate, but it too runs on the 0.35 by-name override.",
 "THE VERDICT IS FORMALLY 'TOO SMALL' AND OPERATIONALLY 'IDEA_WRONG HERE'. At 0.00x it has no measurable directional content at "
 "its own horizon. It inherits fx_jpy's entire geometry problem: a 7.6 bps stop on a JPY cross puts the spread at ~10% of R and "
 "the trade lives 48 minutes. Same repair statement as fx_jpy: this needs a risk distance large enough that the spread is a small "
 "fraction of it, which is a different contract on a different clock, not an adjustment. AE gates it to 0.00 on cost-true evidence "
 "and it should stay there.",
 f"{S1D}; {S1R}")

add("vp_euidx_pocgrav","s1+s2","UNDETERMINED","core_w7_unmeasured",
 "European index price gravitates back toward the prior day's volume-profile point of control when it is far from it and volatility is elevated.",
 "86cccd08d (2026-06-15). Its port provenance is the best in the registry.",
 "W7 cache: 341 trades 2024-01-03..2026-06-11, gross_r 0.29815, legacy charged cost 0.0638, published net 0.23435, at a 320 h "
 "structural horizon with 13.4 mean modelled nights. Folded as 'the frequency engine' at ~115 trades/yr.",
 "Its target is a measured move to a structural level rather than an R multiple, and its stop is one H4 ATR — a geometry that "
 "actually matches its premise, and the only sleeve of which that can be said without qualification.",
 "UNMEASURABLE ON ANY CURRENT SUBSTRATE. It produced ZERO trades in AQ's 32-sleeve archive walk (n_trades_by_sleeve = 0) because "
 "the walk has no M1 aux feed and the sleeve needs 20,000 M1 bars per decision. Its walk-forward gate verdict is NOT_EVALUABLE at n=0.",
 "Coverage MEASURED 341 / TRANSFERRED 0. It is the ONLY member of the live decision surface whose realised hold, excursion, "
 "capture, exit mix and accumulation curve are entirely unknown, and its only economics are a modelled-held-to-horizon figure on a "
 "cache. It carries 0.30 confidence, which feeds sizing and the Kelly-lite day count.",
 "THE GAP IS AN INSTRUMENT GAP, NOT AN EVIDENCE GAP, AND IT IS CHEAP TO CLOSE. (1) fetch prior-day M1 for GER40 and UK100 — "
 "AV_DEEP_H4_INGEST_V1.json already records the sleeve's exact aux requirement and is the harness for it, and "
 "/Users/borr/GTOSActive/repo/data/mt5_research_exports/bridge_ftmo_b7_4_m1_20260601_20260620 shows M1 bridge exports exist on "
 "this machine; then (2) run it through the same AQ/AD/AU pipeline as everything else. Until that happens the honest published "
 "statement is 'unmeasured' and it should not appear in any count of validated sleeves. This is the most valuable single missing "
 "measurement in the core book.",
 f"{S1D}; {S2D}; {S2R}")

pickle.dump(V, open(f"{P}/_v_broad.pkl","wb"))
print("records now:", len(V))
