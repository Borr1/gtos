"""SYNTHESIS — build SLEEVE_FORENSIC_V1.json from the eight lane receipts.

One record per generator (51) plus two shared-machinery records. Every economic
number is JOINED from a lane receipt, never retyped: X1 (geometry/ceiling),
S1 (armed discriminator), S2 (registry geometry), SYN (irrelevant-by-construction),
R2 (emission census). Verdicts and prose come from the lane dossiers.
"""
from __future__ import annotations
import json, os, datetime

P = os.path.dirname(os.path.abspath(__file__))
PROV = os.path.dirname(P)
PH20 = os.path.dirname(PROV)

X1V = json.load(open(f"{PROV}/x1_receipts/X1_VERDICTS_V1.json"))["rows"]
X1C = json.load(open(f"{PROV}/x1_receipts/X1_CEILING_V1.json"))["rows"]
S1  = json.load(open(f"{PROV}/s1_receipts/S1_DISCRIMINATOR_V1.json"))["rows"]
S2  = json.load(open(f"{PROV}/s2_receipts/S2_REGISTRY_DOSSIER_V1.json"))["sleeves"]
SYN = json.load(open(f"{P}/SYN_IRRELEVANT_V1.json"))
R2  = json.load(open(f"{PH20}/receipts/r2/R2_CENSUS_V1.json"))["families"]

# ---- verdicts, from the lane dossiers (lane -> verdict -> repairability) -------
V = {}
def add(name, lane, verdict, cls, premise, origin, birth, params, geom, life, repair, ev):
    V[name] = dict(name=name, lane=lane, verdict=verdict, klass=cls, premise=premise,
                   origin=origin, claimed_at_birth=birth, parameters=params,
                   geometry=geom, lifecycle=life, repairable=repair, evidence=ev)

BOG = "src/components/broader_origin_generators.py"
STAGE13 = ("research/science_program_2026_05/06_outcome_testing/"
           "vnext_moonshot_production_replacement_activation_2026_05_26/"
           "VNEXT_REPLACEMENT_STAGE13_FULL_MOONSHOT_PRODUCTION_SELECTOR_SUMMARY_2026-05-26.json")
REG = ("research/science_program_2026_05/06_outcome_testing/"
       "vnext_moonshot_substrate_dynamic_execution_repair_2026_05_26/"
       "VNEXT_MOONSHOT_UNIVERSAL_CANDIDATE_ORIGIN_REGISTRY_2026-05-26.jsonl")

# ---------------- BROAD: the three POI frameworks (g1) -----------------------
add("current_fvg_fill","g1","IDEA_WRONG","broad_origin_POI",
 "Price retraces into the fair-value gap left by an aggressive move and then resumes in that move's direction.",
 "String present in the repo's first commit 436c16bd (2026-03-29); framework narrative 744c908a (2026-03-30); "
 "ported into the broad-V4 generator 2026-07-12 in 954f5a1573b73615324500d78d316f3a78709096, a 2,845-file commit "
 "titled 'chore(storage): establish non-iCloud GTOS hot workspace snapshot' with no design note.",
 "Its founding evidence was never about a standalone entry: it is a +7-20pp quality FEATURE on the order-block retest "
 "(2026-03-30 spec F4-A). Tested as a feature here it reproduces at +5.02pp (42.06% vs 37.05% at 1.5R, p 0.101, 4/6 months).",
 "Proximity 1.0% of price (an API-cost prescreen, provenance in commit 2be9fced); entry at zone midpoint; "
 "stop buffer applied to M15 ATR where ADR-006 defines it in H1 ATR (ratio measured 2.091). "
 "0 of its own spec's 4 conditions (F1-F4) are implemented.",
 "Zone age at emission median 12.25 h, p95 171.5 h against its own spec's 3 h recency window (23.6% conform). "
 "Fill to 1.5R-or-stop: median 7 min. Stop 7.42 bps.",
 "700,947 emissions collapse to 20,900 POI identities; 84.28% target-through, 76.76% off-session, 96.80% irrelevant by construction.",
 "REPAIRABLE AS A FEATURE, NOT AS A FAMILY. Demote to a boolean on current_ob_retest — the form its own evidence supports. "
 "Worth: removes 57.9% of the estate's POI emission volume and the multiplicity that rides on it. It still misses "
 "economically: cost-true breakeven at 1.5R is 47.2%, the conditioned cohort reaches 42.06%.",
 f"{PROV}/G1_THREE_POI_FAMILIES_DOSSIER.md; {PROV}/G1_FEATURE.json; {PROV}/G1_CENSUS.json")

add("current_ob_retest","g1","SOUND_BUT_TOO_SMALL","broad_origin_POI",
 "After a structural break, price returns to the last balanced zone before the break and continues in the break's direction.",
 "Hand-written framework narrative in 744c908a (2026-03-30, 'Multi-framework PA (4 setups)'); ported into the broad-V4 "
 "generator 2026-07-12 in 954f5a15, the same one-line 'chore(storage)' commit.",
 "Founding study: first-touch continuation 72.7% on n=23,575 vs 31.5% on n=82,572 for touch-2+. Its trade contract was "
 "target 1.25xATR / stop 0.5xATR (2.5R) over 20 H1 bars.",
 "Proximity 1.0%; entry at zone midpoint where the spec says near edge ('Do NOT use the current candle close price'); "
 "ATR key defined in M15 so this family alone is conformant. Touch filter (gate1.touch_count_reject_threshold: 2) stranded on the LLM path.",
 "Zone age at emission median 33.50 h, p95 191.5 h; only 26.9% are <=10 H1 bars old. Shipped contract 1.5R resolved in a "
 "median 33 min against a founding contract of 2.5R over 20 H1 bars. Stop 9.13 bps.",
 "270,354 emissions for 5,296 zones (~38x identity inflation); 91.55% target-through, 65.26% off-session, 97.01% irrelevant by construction.",
 "REPAIRABLE IN COHORT, NOT IN SIZE. (a) age gate <=10 H1 bars (costs 73.1% of emissions, restores the cohort the evidence "
 "describes); (b) carry the touch filter across; (c) restore near-edge entry (+71% relative fill at 1.6x risk distance); "
 "(d) restore the 2.5R/20-H1-bar geometry. What it will NOT fix: at 9.13 bps the toll is 0.181 R/fill and cost-true "
 "breakeven at 1.5R is 47.2%. This idea's home is a contract where one R is 44-436 bps, not 9.",
 f"{PROV}/G1_THREE_POI_FAMILIES_DOSSIER.md; {PROV}/G1_CENSUS.json")

add("current_breaker_re_entry","g1","GEOMETRY_WRONG","broad_origin_POI",
 "An order block that failed and was traded through flips polarity: the zone that was demand now acts as supply and holds on re-entry.",
 "Added 2026-04-25 by 64d05b8950c4e338358002a09933db980379221d, 'feat(breaker_re_entry): activate explicit framework "
 "alongside ob_retest for FTMO challenge' — 1,798 lines, 17 verification tests, 9 canary fixtures. Ported 2026-07-12 in 954f5a15.",
 "The best-argued of the three at birth (explicit tests and fixtures), but no return, sample or out-of-sample split was offered.",
 "risk.sl_buffer_breaker_atr_multiplier: 0.5 EXISTS in config and is read by NO broad-V4 code; the family therefore gets "
 "23.9% of its specified stop. risk.sl_buffer_min_ticks: 5 likewise never read. Entry at midpoint where B-PARAMS says near edge.",
 "Zone age at emission median 68.25 h, p95 192.8 h — the oldest of the three; only 1.3% are <=5 h. BreakerBlock "
 "(src/models/market_state_models.py:65-75) carries NO invalidation field, so a zone price has blown through is still emitted.",
 "95,051 emissions; 26.19% born already past their own stop, 62.32% target-through, 65.62% off-session, 95.55% irrelevant by construction.",
 "THE MOST REPAIRABLE FAMILY IN THE BROAD LANE. Remove the born-past-stop bin and the honestly-formed resting limits show "
 "MFE/MAE 1.033/1.082/1.091/1.111 at 120/480/1440/4320 min — ABOVE the at-market reference at every horizon, n=3,433. "
 "Its -0.391 whole-family reading is an artifact of the 26% born past stop. Repairs, all already specified: read the "
 "0.5 H1-ATR buffer (4.18x wider stop); add an invalidation field; set poi_state_required. r2 has already landed the "
 "past-stop refusal and the family moves -0.36457 -> -0.04011 R/emission. Still economically negative at 7.9 bps.",
 f"{PROV}/G1_THREE_POI_FAMILIES_DOSSIER.md; {PH20}/receipts/r2/R2_CENSUS_V1.json; {PH20}/SESSION_R2_GENERATOR_REPAIR.md")

# ---------------- BROAD: continuation / break (g2) ---------------------------
add("displacement_continuation","g2","PARAMETERS_WRONG","broad_origin_production",
 "A bar that travels far and closes with a large body relative to recent range is an impulse, and price keeps moving in the impulse's direction.",
 "Registry d6f09c5a2 (2026-05-26, 'research: build moonshot dynamic execution substrate checkpoint'); implementation and "
 "activation 69d000fb3 (2026-05-27, 'vnext: activate moonshot production replacement'). Block " + BOG + ":769-787.",
 "STAGE13 replay summary capped at 240 replayed rows = 1.67% of available executable rows; the activation allowlist kept "
 "only in-sample-positive cells, so the count with negative expectancy is ZERO by construction.",
 "Displacement threshold 1.5 x ATR14, stop 0.25 x ATR14 (a constant shared with 6 other modules), target from the global "
 "risk.min_rr = 1.5 sanity floor. None was chosen for this family; none has an out-of-sample record.",
 "Clock is RIGHT (M15, matching its own birth spec). Entry instant is wrong: its trigger selects bars closing at the 0.861 "
 "quantile of their own range, so it buys the high; mean adverse excursion reaches the FULL stop inside 2 h.",
 "39,517 emissions; 54.66% off-session, 2.22% stale, 54.93% irrelevant by construction. Realised p(target first) 0.397 against a 0.400 breakeven.",
 "Three priced parameter repairs: (1) enter one M15 bar later, +0.3859 bps/trade uniformly; (2) raise displacement 1.5 -> 2.5 "
 "(monotone, better at every horizon 2-24 h, emissions 63,595 -> 11,314); (3) choose a target instead of inheriting min_rr. "
 "Combined ~+0.68 bps against a 3.156 bps toll — not enough to trade, and the ceiling is negative at every horizon.",
 f"{PROV}/g2/G2_DOSSIERS.md; {PROV}/g2/G2_TRIGGER.json; {PROV}/g2/G2_DELAY.json")

add("regime_transition_break","g2","GEOMETRY_WRONG","broad_origin_production",
 "When a market crosses from not-trending into a strong trend and simultaneously breaks its recent range high, it keeps going.",
 "Registry d6f09c5a2 (2026-05-26); implementation and activation 69d000fb3 (2026-05-27). Registry row STAGE05-ORIGIN-010.",
 "Its own birth registry REQUIRED H1/H4/D1 OHLC + regime_classifier_state. It shipped on M15 — 16x to 96x too fast, and the "
 "violation is written in the artifact that authorised it. STAGE13 gave it 240 rows = 0.26% of available; at family level it "
 "was already measured NEGATIVE on all nine exit policies.",
 "Trend-score thresholds <0.75 -> >=2.0 over a 5-hour lookback; stop 0.10 x ATR14 (shared with session_open_range_break and "
 "three sleeve modules); target = min_rr. Never validated out of sample.",
 "CATASTROPHIC AND SELF-DECLARED. Its 'transition' is the 5-hour trend score jumping between two ADJACENT 15-minute bars. "
 "Trigger bar median range 2.442 x ATR50 — the largest in the module — and entry sits at the 0.890 quantile of that bar's own "
 "range. It is a single-largest-bar detector wearing a regime name, and it buys the high.",
 "2,320 emissions; 46.34% off-session, 46.34% irrelevant by construction. Realised p(target first) 0.397 vs 0.400 breakeven — "
 "calibrated to lose by 0.3 pp before one basis point of cost. Accumulation 2h->320h = 0.170x. 92.6% of its emissions duplicate "
 "another family's same-symbol same-bar same-side proposal.",
 "Three repairs, priced. (1) ENTRY INSTANT — enter one bar later: +2.2949 bps/trade averaged over five horizons, flipping the "
 "sign at three of five and recovering 0.75 of its entire 3.070 bps toll, for 15 minutes. (2) DROP THE TRANSITION CLAUSE — the "
 "clean-room ablation without it has a 1-bar loss 6.3x smaller and a 16-hour figure 1.5x larger: the clause that gives the family "
 "its name is the value-destroying part. (3) Move to the registry's own H1/H4/D1 clock — NOT_EVALUABLE here (n=218 at H4). "
 "Best post-repair capture/toll ~1.26x with no CI excluding zero: a real repair on a family that remains untradeable.",
 f"{PROV}/g2/G2_DOSSIERS.md; {PROV}/g2/G2_TRIGGER.json; {PROV}/g2/G2_DELAY.json; {REG}")

add("volatility_compression_expansion","g2","GEOMETRY_WRONG","broad_origin_production",
 "After a period of compressed volatility, the first bar that expands and breaks the recent range starts a directional move.",
 "First named as a gap 2026-05-12 (a191f5be1/d01d30c25); registered d6f09c5a2 (2026-05-26); implemented and activated "
 "69d000fb3 (2026-05-27). Block " + BOG + ":797-833.",
 "STAGE13's 240-row cap = 4.32% of available executable rows; kept only in-sample-positive cells. Lane09 Meta-Selector V2 "
 "(13c038130, 2026-06-01) issued it a REDUCE verdict five days after it shipped and nothing acted on it.",
 "20-bar channel and squeeze percentile inherited whole; stop 0.20 x ATR14; target = min_rr. Its live D1 sibling "
 "vol_compression uses plateau-validated parameters on the same premise; none of them was carried across.",
 "THE NATURAL EXPERIMENT, AND THE MISMATCH IS 96x. The live sibling gives the same premise a prior-20-D1-BAR channel "
 "(20 trading days) and a 1,920-hour horizon; this family gives it a prior-20-M15-BAR channel (5 HOURS) and is scored inside "
 "2 hours, by which point 86.9% of its trades have not resolved.",
 "5,341 emissions; 80.79% off-session — the highest in the estate — and 80.79% irrelevant by construction. Realised p(target "
 "first) 0.368 against a 0.400 breakeven. Accumulation 2h->320h = -11.60x, a SIGN FLIP: the only family whose signal inverts with holding.",
 "REPAIR AS REPLACEMENT, NOT ADJUSTMENT. Its one apparent exception (+22.169 bps at 16 h inside configured sessions) dies on "
 "its own concentration audit: 90.0% from two crude symbols on 99 of 1,026 rows, 43.2% from a single day. Killed here so nobody "
 "finds it again. Repairs: restrict generation to the sessions admission accepts (81% of output is thrown away); fix the "
 "BTCUSD/ETHUSD name collision; delete the squeeze and expansion clauses (measurably value-destroying relative to the breakout "
 "they wrap) — at which point it is a plain 20-bar breakout with no distinguishing content. The PREMISE is not dead; its D1 "
 "sibling carries it. The M15 instantiation should be retired.",
 f"{PROV}/g2/G2_DOSSIERS.md; {PROV}/g2/G2_SESS.json; {PROV}/g2/G2_CURVE.json")

# ---------------- BROAD: reversion / extreme (g3) ----------------------------
add("structural_distance_extreme","g3","GEOMETRY_WRONG","broad_origin_production",
 "After price closes within 3% of its own 50-bar high (or low), it reverts back into the range.",
 "NAME: d6f09c5a2 (2026-05-26) in src/research/universal_candidate_origin_registry.py — one of 16 rows in a COVERAGE-BOXING "
 "registry, not a strategy. GEOMETRY: 69d000fb3 (2026-05-27). Never changed since; only five commits have ever touched the file.",
 "NO EDGE CLAIM AT BIRTH — a coverage argument: boxes_out_if_missing='geometry extremes remain prompt context instead of "
 "candidate origins', activation_status='research_registry_only_no_runtime_candidate_generation_change', default_off=true. "
 "STAGE13 then reported +1.196255 R/trade at an 83.7% win rate over 53,415 rows — 18x the best subsequent measurement and the "
 "opposite sign. Never retracted.",
 "pos50 >= 0.97 (arbitrary); stop = bar.high + 0.25 x ATR14 — a COPIED constant that is a buffer in liquidity_sweep_reclaim "
 "(28.3% of its stop) and IS the stop here (71.0%), because pos50>=0.97 forces the wick term near zero by construction. "
 "Target = min_rr. _atr is mean(high-low), not true range, so it cannot see a gap.",
 "Premise is a reversion idea with no natural timescale; contract is a 3.05 bps stop / 6.09 bps target on an M15 clock. "
 "MEDIAN TIME TO RESOLUTION 5 MINUTES; median time to stop 3 minutes. The median trade lives and dies inside one third of the "
 "M15 bar that generated it.",
 "23,923 emissions; 64.42% off-session, 64.42% irrelevant by construction. past_stop and duplicate rates are essentially zero "
 "(1.46%) — for THIS family Borhen's 'already irrelevant' is precisely false at the order level and precisely true at the gate level.",
 "Shipped contract is SIGNIFICANTLY VALUE-DESTROYING: -0.2505 bps/trade [-0.4145,-0.0807], 1 of 5 quarters positive. Deleting "
 "the take-profit flips it to +0.4118 [+0.0750,+0.7814], 4 of 5 quarters — a +0.6623 bps repair on identical rows. AND THE "
 "REPAIR DOES NOT MAKE IT TRADEABLE: +0.41 bps against a 3.02 bps toll is 7.3x short. Widening the stop is worth ZERO "
 "(+0.0329 bps [-0.3460,+0.4349] on 28,268 paired rows). Strike the STAGE13 birth claim at source; do not enable or size it.",
 f"{PROV}/G3_REVERSION_AND_EXTREME_DOSSIERS.md; {PROV}/g3_receipts/a15_final.py; {PROV}/g3_receipts/a17_paired.py")

add("liquidity_sweep_reclaim","g3","GEOMETRY_WRONG","broad_origin_production",
 "Price runs the prior 20-bar high, fails, and closes back inside the range; the trapped breakout buyers become fuel for the move down.",
 "d6f09c5a2 (2026-05-26), same coverage-boxing registry. Generator built the next day, 69d000fb3 (2026-05-27), " + BOG + ":713-745.",
 "The registry that commissioned it SPECIFIED M1/M5/M15 data and an EVENT-TIME clock. The generator reads M15 CLOSES ONLY and "
 "fires on bar_close. Both requirements its own specification named were dropped and nothing records the decision. STAGE13 "
 "reported +0.20175 R/trade over 100,326 rows — 7x the best subsequent measurement.",
 "20-bar lookback; sweep wick + 0.25 x ATR14 buffer (the copied constant; here it is 28.3% of the stop and the wick is 70.2%, "
 "so this is the one structurally-derived stop in the lane); target = min_rr.",
 "THE MISMATCH IN MINUTES: the premise is a 1-to-5-MINUTE event (a stop run and an immediate reclaim); the detector resolution "
 "is 15 MINUTES (both legs must fall inside one M15 bar); realised median time to resolution 25 minutes; and the contract has "
 "NO time stop at all. The detector is 3-15x coarser than the event it looks for.",
 "43,751 emissions; 59.98% off-session, 60.09% irrelevant by construction. 100% resting-at-market with 0% past-stop and 0% "
 "target-through — structurally the cleanest emitter in the broad estate.",
 "Delete the fixed take-profit: +0.5110 bps [+0.3059,+0.7127] at 2 h and +1.4958 [+0.7927,+2.1450] at 24 h, taking it from "
 "significantly negative to significantly positive (+0.9163 [+0.245,+1.641], 4/5 quarters). THEN BUILD THE DETECTOR ON M1/M5 AS "
 "ITS OWN FOUNDING REGISTRY SPECIFIED — this is UNPRICED and it is the one unpriced thing in the broad estate worth pricing, "
 "because every measurement so far tests the M15 transcription of the idea and none tests the idea. Ceiling as it stands "
 "+0.92 bps against a 3.02 bps toll: a research question, not a book.",
 f"{PROV}/G3_REVERSION_AND_EXTREME_DOSSIERS.md; {PROV}/g3_receipts/a15_final.py; {REG}")

add("range_extreme_reversion","g3","PARAMETERS_WRONG","broad_origin_production",
 "A close in the outer quartile of the recent range drifts back toward the middle of it over the next one to two hours.",
 "NOT from the 2026-05-26 registry. Added later citing ULTIMATE_ORIGIN_DISCOVERY_MINE_V2 in its own source_fields (" + BOG + ":677). "
 "That artifact is NOT ON DISK ANYWHERE at HEAD; it exists only in git at "
 "research/operations/final_moonshot_v4_ultimate_mechanical_edge_2026_06_10/ULTIMATE_ORIGIN_DISCOVERY_MINE_V2.json (86cccd08d, 41425481e).",
 "THE ONLY GENUINE DISCOVERY ARTIFACT BEHIND ANY BROAD FAMILY. The miner scanned every M15 bar-close across a 46-symbol year, "
 "used day-clustered t across symbol-days, Benjamini-Hochberg Q=0.05 over all cells, an effect floor net of a measured spread "
 "proxy, and ONE out-of-time confirmation on pre-registered survivors — materially the rule the estate ratified six weeks later.",
 "Implements _prior_high/_prior_low(50) EXCLUSIVE where the mine used _close_position(...,48) INCLUSIVE. The exclusive form "
 "makes range_pos UNBOUNDED: min -1.684, max +3.403, with 9.04% of 276,246 emissions outside [0,1] — impossible under the cited "
 "definition, and 5.61% are breakouts being faded as range extremes. Thrust cap where the mine used a band.",
 "The mine's own geometry is a 1-2 h naked drift. The shipped contract is a fixed 2R target with no horizon. The two parameter "
 "deviations are HARMLESS IN EFFECT (in-[0,1] +0.0655 vs outside -0.0239) — which is itself the finding: the parameters do not "
 "match the evidence and it does not matter, because there is nothing there to protect.",
 "ZERO emissions in 27,658 (January) and 0 in 24,239 (February). It is gated on runtime_cfg.get('moonshot_mined_origin_families_enabled', "
 "False) (" + BOG + ":312-314) and that key is absent from config/agent_config.yaml and every profile. Fourteen months wired, never run.",
 "Implement the mine's own predicate (_close_position(series,index,48) already exists three lines away), restore thrust as a band, "
 "and give it the 1-2 h naked-drift horizon its evidence actually has. MEASURED CEILING: +0.3040 bps at 2 h and +1.1546 "
 "[+0.2127,+2.2113] at 24 h with 5/5 quarters — the single best cell anywhere in the g3 lane, 1 of 42 tested, and still 1.87 bps "
 "short of the 3.02 bps toll. DO NOT ENABLE IT. The value of the repair is that it retires a fourteen-month-old unmeasured claim "
 "sitting in production source. The estate needs a register of wired-but-never-enabled generators; this is the entry that proves it.",
 f"{PROV}/G3_REVERSION_AND_EXTREME_DOSSIERS.md; {BOG}:312-314,:677; {PROV}/g3_receipts/a15_final.py")

# ---------------- BROAD: schedule / cross-asset / microstructure (g4) --------
add("session_open_range_break","g4","GEOMETRY_WRONG","broad_origin_production",
 "After a session opens, the first N minutes define a range and the first decisive close outside it starts the day's directional move.",
 "d6f09c5a (2026-05-26) registry row STAGE05-ORIGIN-009 (category session_clock, status not_first_class_candidate_origin); "
 "activated one day later by 69d000fb (2026-05-27).",
 "NOT_FOUND. No research artifact anywhere justifies the idea with a return — searched git log -S across 8,992 commits on all "
 "refs, research/science_program_2026_05/, research/operations/**, .context/02_session_handoffs/, and a whole-tree rg. What "
 "exists is a MEASURED NEGATIVE on its own 240-row smoke (-0.11190 R, negative on 7 of 9 exit policies), shipped one day later.",
 "Session windows are fixed UTC HH:MM constants; range length 30 min is an accident of 'range_start_index + 1'; stop 0.10 x "
 "ATR14 (the copied buffer, also in regime_transition_break at :832/:850); target = min_rr = 2.0R.",
 "THREE mismatches. (1) WINDOW: constants are fixed UTC while every session they name moves on a DST calendar. Only 33 of 213 "
 "exchange-instrument emissions (15.5%) have an opening range containing their own cash open; 34.3% break out BEFORE their own "
 "market opens; NAS100|ny and SPX500|ny ranges are 60 min early. (2) TARGET: contract asks 2.0R, median MFE is 0.659R and only "
 "9.5% of paths reach +2R within 2 h. (3) HOLD: mean R goes -0.0170 at 5 min to -0.1576 at 120 min, monotone.",
 "8,195 emissions; 0.00% off-session (it only fires inside its own windows), 0.00% stale — the ONLY broad family with a 0% "
 "irrelevant-by-construction rate. Its waste is not in the emission, it is in the window definition. 39.6% fire on the very "
 "first bar it is possible to fire on.",
 "Cheapest first: (1) anchor windows to exchange-local session opens via zoneinfo — recovers the 84.5% of exchange-instrument "
 "emissions whose range is not an opening range and removes the twice-yearly one-hour drift; a table and a tz lookup, no new "
 "data. (2) DECLARE the range length. (3) set the target from the family's own excursion. (4) do NOT lengthen the hold. "
 "WORTH: the entire same-cell residual is [-3.0,+4.0] bps against a 3.78 bps toll, so a repair must move gross by ~4 bps to "
 "matter and only (1) is that large — and it changes WHICH POPULATION is sampled rather than the size of an existing effect. "
 "A cheap re-measurement of a question nobody has asked, not a rescue.",
 f"{PROV}/G4_SCHEDULE_CROSSASSET_MICROSTRUCTURE.md; {PROV}/G4_SCHEDULE_V1.json; {PROV}/G4_FINAL_V1.json")

add("cross_asset_lead_lag","g4","PARAMETERS_WRONG","broad_origin_production",
 "When a leading instrument makes a large move and its correlated partner has not yet moved, the partner catches up.",
 "d6f09c5a (2026-05-26) registry row STAGE05-ORIGIN-014 (category cross_market_context, status risk_gate_context); activated "
 "69d000fb (2026-05-27). Same coverage-map provenance: boxes_out_if_missing='cross-asset context can only size/block, not "
 "originate candidates'.",
 "No return, sample or citation offered at birth. NOT_FOUND for any post-birth validation. Documented in the literature "
 "(Chan 1992 lead-lag, Hasbrouck information shares) — but at a sub-second-to-few-minutes half-life in liquid markets.",
 "Leader move threshold, lag_response <= 0.5 ATR admission gate, stop = the qualifying bar's own low/high +/- 0.25 x ATR14 "
 "(the copied buffer). LOOK-AHEAD: NONE, and conservatively so — the leader bar's information is complete a full bar before the decision.",
 "THE GATE BUILDS THE STOP THAT KILLS IT. The stop is anchored to the qualifying bar while the admission gate requires that bar "
 "to have barely moved, so close-minus-low is small BY THE CONDITION THAT QUALIFIES THE SETUP: the more strongly a candidate "
 "qualifies, the tighter its stop. Median stop 5.94 bps, mean toll 5.5508 bps = 0.93x the ENTIRE risk distance; mean cost_r 0.806; "
 "18.9% of emissions carry cost > 1.0 R before anything happens. Mean MAE at bar 15 is -1.0044 R: the stop is one M15 bar of ordinary noise.",
 "21,678 emissions; 62.20% off-session, 4.54% stale, 62.68% irrelevant by construction.",
 "THE PREMISE IS REFUTED AT ITS OWN TIMESCALE: the share moving in the leader's direction is 44.9%/46.7%/46.3%/48.4%/48.3% at "
 "5/15/30/60/120 min — BELOW A COIN FLIP AT EVERY HORIZON. Repairs: (1) DECOUPLE THE STOP FROM THE QUALIFYING BAR (highest-value "
 "change in the g4 lane; at 1.5 ATR the toll falls to roughly a quarter on the FX legs); (2) delete NAS100, SPX500, ETHUSD "
 "(cost_r 3.40/3.66/1.79); (3) test the premise at its own timescale on the 263,894,769 verified ticks at "
 "/Users/borr/GTOSActive/vps-ticks-20260726/ — cheap, and it settles whether the 15-minute residual is the dead tail of a real "
 "effect. Repairs 1-2 make it MEASURABLE; only 3 can make it RIGHT, and it may come back refuted.",
 f"{PROV}/G4_SCHEDULE_CROSSASSET_MICROSTRUCTURE.md; {PROV}/G4_FINAL_V1.json")

add("microstructure_absorption_reversal","g4","IMPLEMENTATION_WRONG","broad_origin_production",
 "At a range extreme, a bar with large volume and a small range is a limit wall absorbing the push, so fade it.",
 "Mined 2026-06-12/13. Birth artifacts research/operations/final_moonshot_v4_ultimate_mechanical_edge_2026_06_10/"
 "ULTIMATE_MICROSTRUCTURE_{MINE_V1,VERIFICATION,GOLIVE_BOOK}.json — ALL DELETED FROM HEAD, recoverable at 86cccd08d.",
 "THE BEST BIRTH EVIDENCE IN THE ESTATE: 356 cells tested, 19 BH survivors, a 10-setup go-live book with per-symbol breadth, "
 "subperiod stability, bootstrap p05, 2x cost stress and an untouched-2026 validation split; validated +0.14 to +0.74 R/trade OOS. "
 "Every candidate is stamped mined_family_evidence='ULTIMATE_MICROSTRUCTURE_GOLIVE_BOOK' (" + BOG + ":586) and THAT STRING "
 "RESOLVES TO NO FILE AT HEAD.",
 "2.5 x ATR, 48 and 20 carried onto an M15 series unchanged from an H4 spec. bar.volume on FX/CFDs is MT5 tick_volume — a count "
 "of price updates, not traded size: a proxy of a proxy, which the go-live book itself names as reason (3) that live will underperform.",
 "THE DOCSTRING SAYS 'Reconciles to research microstructure_engine.py'. IT DOES NOT, ON SIX DECLARED COUNTS: timeframe H4 -> M15; "
 "trend conditioning dropped (all 10 book cells are trend-conditional); relv >= 1.5 gate computed but never gated on; entry "
 "debounce dropped; 10-cell restriction dropped (it emits on both sides for every symbol); exit contract replaced (+12/+24 H4 bars "
 "and vol_exhaust -> target_rr on a 2.5 x M15 ATR stop). Only the two detector predicates and the number 2.5 survive.",
 "ZERO emissions in 27,658 (January) and 0 in 24,239 (February). Its enable key moonshot_microstructure_origins_enabled "
 "(" + BOG + ":316) appears in exactly one file in the repository — the generator that reads it.",
 "(a) DO NOT FLIP THE FLAG ON THE CURRENT CODE — the six defects compound in the same direction (more emissions, smaller stops, "
 "no conditioning). (b) Port it properly, which needs an H4 series generate_live_broader_origin_candidates does not have "
 "(timeframe='M15' hardcoded at " + BOG + ":293) — that is a new generator, not a patch — or delete it under the cleanup policy. "
 "(c) CHEAPEST FIRST STEP, half a session: restore the three deleted artifacts from 86cccd08d so the provenance stamp resolves, "
 "and record the six-way divergence beside the code. WORTH: the largest per-trade claim attached to any dormant family in this "
 "estate and the only one with bootstrap p05, breadth counts and cost stress behind it.",
 f"{PROV}/G4_SCHEDULE_CROSSASSET_MICROSTRUCTURE.md; {PROV}/G4_LIFECYCLE_V1.json; {BOG}:293,:316,:586")

add("microstructure_vdelta_divergence","g4","IMPLEMENTATION_WRONG","broad_origin_production",
 "A new range extreme printed while the last three bars' signed volume runs the other way is exhaustion, so fade it.",
 "Identical to its sibling: mined 2026-06-12/13, same three artifacts, all deleted from HEAD, recoverable at 86cccd08d, same "
 "dangling provenance stamp at " + BOG + ":586.",
 "S5 is the detector the go-live book leans on hardest: 3 of its 10 cells are S5 (index|short|24|fixed, jpy_fx|short|24|vol_exhaust, "
 "metals|short|24|vol_exhaust). The book wrote its own haircuts down — size off the validated 0.14 R, not the 0.58 headline, and "
 "prune the thin silver legs — which is more than any other family in the broad estate did.",
 "Same H4 constants on an M15 series. vdacc weights tick-update counts by body-to-range ratio: a signed ACTIVITY proxy, not signed order flow.",
 "Same six-way divergence as S4, plus one of its own: the 3-bar signed-volume window is 45 MINUTES where the spec means 12 HOURS, "
 "measured against a range extreme also compressed from 8 days to 12 hours.",
 "ZERO emissions in 27,658 (January) and 0 in 24,239 (February). Same absent enable key.",
 "Identical to S4: do not flip the flag on this code; port properly (needs an H4 series the generator does not have) or delete; "
 "as the half-session first step restore the three birth artifacts and record the divergence beside the code. If ported, size off "
 "the validated 0.14 R (jpy_fx short) and prune the thin silver legs — the book already says so.",
 f"{PROV}/G4_SCHEDULE_CROSSASSET_MICROSTRUCTURE.md; {BOG}:293,:316,:586")

json.dump({"partial":True}, open("/dev/null","w"))
import pickle; pickle.dump(V, open(f"{P}/_v_broad.pkl","wb"))
print("broad records:", len(V))
