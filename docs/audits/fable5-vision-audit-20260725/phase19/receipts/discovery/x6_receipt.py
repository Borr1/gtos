import json, statistics
D="/Users/borr/GTOSActive/worktrees/wave19-broad-forensic-20260801/docs/audits/fable5-vision-audit-20260725/phase19/receipts/discovery"
depth=json.load(open('/tmp/x6/X6_DEPTH_V1.json'))
prof=json.load(open('/tmp/x6/X6_PROFILE_ftmo.json'))
iso_f=json.load(open('/tmp/x6/X6_ISOLATE_ftmo.json'))
iso_n=json.load(open('/tmp/x6/X6_ISOLATE_redacted_account.json'))
twod=json.load(open('/tmp/x6/X6_2D_SUMMARY.json'))
armed=json.load(open('/tmp/x6/X6_ARMED_SPREAD.json'))
lever=json.load(open('/tmp/x6/X6_LEVER_PRICE.json'))
out={
 "lane":"x6",
 "question":"could the live system actually run an M1-or-intrabar decision cadence",
 "generated_utc":"2026-08-06",
 "evidence_class":{
   "source_read":"file:line on this worktree at HEAD (phase19/broad-forensic)",
   "host_state":"[UNVERIFIED today] - no VPS touched. Host facts come from the read-only 2026-07-25 export and the 2026-07-26 depth probe.",
   "tick_measurements":"[MEASURED] 128,150,823 FTMO ticks + redacted_account, 2026-06-18..07-24. OUTSIDE January: used for MECHANISM only, never to score a January candidate."},
 "q1_what_happens_on_a_wake_with_no_new_bar":{
   "verdict":"the book already does a full broker-facing pass every 60 s and then declines to think",
   "poll":"run_book.py:99 --poll-seconds default 60.0; scripts/run_book_supervisor.ps1:109 passes '60' explicitly",
   "sequence_per_tick":[
     "launcher.py:268 _write_heartbeat",
     "launcher.py:269-272 kill/halt flags + brake transition alert",
     "launcher.py:282-309 connection health, reconnect, outage alert",
     "launcher.py:314 owner.manage_open_positions(now_utc=now) -- EVERY tick, halt-independent; adopts, rehydrates and applies exit policy off the LIVE tick",
     "launcher.py:319-324 _latest_closed_bar_iso(tf) per active timeframe (3 candles per reference symbol)",
     "launcher.py:325-327 if no timeframe advanced -> return {'action':'no_new_bar'} and run_cycle is NEVER called"],
   "the_gate":"launcher.py:323  `if iso is not None and iso != self._last_bar_by_tf.get(tf)`",
   "what_would_have_to_change":"one call site. An early-trigger evaluation inserted between launcher.py:316 and :318, or run_cycle extended with a forming-bar mode. Generation itself (book_engine._generate_intents) is already parameterised by spec.timeframe end to end.",
   "already_registered":"launcher.py:46-50 DEFAULT_REF_SYMBOL lists M1 (tf=1) as an ACTIVE decision timeframe and book_engine.py:22 _TF_MINUTES carries 1:1. The cadence is a parameter, not a rewrite."},
 "q2_components":{"see":"x6_RESULT.md table"},
 "q3_cost_is_the_spread_minute_aware_enough":{
   "instrument":"one observation per (symbol, broker-minute) = MEDIAN spread of that minute's ticks. Time-weighted, not tick-weighted: tick ARRIVAL RATE is itself +19.7% at the boundary, so a tick-weighted median would be contaminated by the effect being measured.",
   "hour_effect_removed":"each broker hour's 60 minute-cells normalised by THAT HOUR's own mean, so a rollover/session premium cannot contribute.",
   "pooled_all_symbols_ftmo":{
     "minute_of_hour_00_vs_bar_interior_pct":round(100*(iso_f["hour0"]/iso_f["interior"]-1),2),
     "pure_M15_close_premium_15_30_45_vs_interior_pct":round(100*(iso_f["m15_only"]/iso_f["interior"]-1),2),
     "hour_close_extra_pct":round(100*(iso_f["hour0"]/iso_f["m15_only"]-1),2)},
   "pooled_all_symbols_redacted_account":{
     "minute_of_hour_00_vs_bar_interior_pct":round(100*(iso_n["hour0"]/iso_n["interior"]-1),2),
     "pure_M15_close_premium_pct":round(100*(iso_n["m15_only"]/iso_n["interior"]-1),2)},
   "within_hour_min0_premium_hour_effect_divided_out":{
     "median_across_broker_hours_pct":round(100*(twod["median_premium"]-1),2),
     "hours_where_min0_is_wider":"22/22"},
   "armed_symbols_vs_the_rest":{
     "armed_median_premium_pct":round(100*(armed["armed_median_premium"]-1),2),
     "armed_h4_close_hours_median_pct":round(100*(armed["armed_h4_close_median_premium"]-1),2),
     "non_armed_median_premium_pct":5.74,
     "reading":"the bar-close spread premium is an FX phenomenon (USDJPY +50.8% at H4-close hours, GBPUSD +22.1%, AUDUSD +28.1%) and is essentially ABSENT on the armed surface (BTCUSD 0.00%, USOIL 0.00%, US30 0.00%, XAUUSD +0.49%). The exceptions are the silver crosses: XAGEUR +16.6%, XAGUSD +16.2%, XAGAUD +16.2%."},
   "price_of_the_wave_lever":{
     "method":"spread_r (January, per candidate) x saving_frac (mechanism, from ticks), matched on the candidate's own boundary minute",
     "n_priced":lever["n_priced"],
     "mean_r_per_trade":round(lever["mean_r_per_trade"],6),
     "executable_subset_spread_r_le_0p10":{"n":10399,"mean_r_per_trade":0.000457},
     "wave_lever_r_per_trade":0.0670,
     "spread_share_of_the_lever_pct":round(100*lever["mean_r_per_trade"]/0.0670,2),
     "verdict":"the hour-aware cost model is GOOD ENOUGH for this lever. Its blind spot is worth 0.0005 R/trade against a 0.0670 R/trade lever -- 0.77%. The 5-minute-delay lever is NOT a spread effect and cannot be captured by paying a better spread."}},
 "q4_data_is_M1_available_live":{
   "verdict":"YES, and it is not close",
   "source":"/Users/borr/GTOSActive/vps-ticks-20260726/MARKET_DATA_DEPTH_PROBE.json, 2026-07-26, both live terminals",
   "ftmo":depth["brokers"]["ftmo"]["summary"],
   "redacted_account":depth["brokers"]["redacted_account"]["summary"],
   "binding_constraint":"the CLIENT-side terminal setting maxbars=100000, not the broker. 100000/1440*7/5 = 97.2 days at 24x5 against a measured 98.6 / 98.2 day median -- the clamp IS the depth, and it is an operator setting.",
   "what_the_mission_actually_needs":"the CURRENT forming bar's interior only: 240 M1 bars for an H4 bar, 15 for an M15 bar. Against ~141,000 M1 bars available that is 3 orders of magnitude of headroom. Deep M1 history is not required and is not the question.",
   "already_exercised_live":"registry.py:58 vp_euidx_pocgrav declares aux_timeframe=TF_M1, aux_count=20000 and book_engine.py:626-628 fetches it per cycle. The sleeve was ported/registered 2026-06-15 and placed a live GER40 order (the 'GoldAgent_OBRete' orphan), so a 20,000-bar M1 pull has run on the live terminal.",
   "caveat":"per-symbol depth is not uniform: FTMO M1 min 72.9 days (the 24x7 crypto symbols, matching the 69.4-day 24x7 clamp). Any new cohort needs its own probe -- the same lesson as the F15 7,800-bar M15 probe."},
 "q5_risk_and_safety":{"see":"x6_RESULT.md - five findings, two of them silent"},
 "q6_biggest_blocker":"book_owner._entry_too_late (book_owner.py:397-410) with ultimate_book_max_entry_lateness_frac: 0.5 (config/agent_config.yaml:1390). The window is frac x bar_period, so an M1 decision grid gives 30 SECONDS against a 60-second poll -- roughly half of all entries are SHADOWED, and the skip reason is 'stale_late_entry_after_restart', which reads as a healthy restart guard. Fail-open by design, so nothing errors and no alert fires.",
 "artifacts":[f"{D}/x6_RESULT.md",f"{D}/x6_RESULT.json",f"{D}/X6_SPREAD_MINUTE_ftmo.json",
   f"{D}/X6_SPREAD_MINUTE_redacted_account.json",f"{D}/X6_ARMED_SPREAD.json",f"{D}/X6_LEVER_PRICE.json",
   f"{D}/X6_2D_SUMMARY.json",f"{D}/X6_DEPTH_V1.json",f"{D}/x6_spread_minute.py",
   f"{D}/x6_spread_2d.py",f"{D}/x6_price_lever.py",f"{D}/x6_armed.py"],
 "profiles":{"m15_offset_spread_profile_ftmo":prof["m15_offset_profile"],
             "m15_offset_ticks_per_min_profile_ftmo":prof["ticks_per_min_profile"],
             "minute_of_hour_spread_profile_ftmo":prof["minute_of_hour_profile"]},
}
json.dump(out,open(f"{D}/x6_RESULT.json","w"),indent=1)
print("wrote", f"{D}/x6_RESULT.json")
print(json.dumps(out["q3_cost_is_the_spread_minute_aware_enough"]["price_of_the_wave_lever"],indent=1))
