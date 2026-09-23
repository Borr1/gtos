#!/usr/bin/env python3
"""Session AV — repair-queue rows, appended to the shared append-only sidecar.

    python3 docs/audits/fable5-vision-audit-20260725/phase12/receipts/av_repair_rows.py

Writes `phase12/receipts/REPAIR_QUEUE_AV.json` (this session's authoritative copy, regenerated
in full) and APPENDS to `phase6/receipts/REPAIR_QUEUE_APPEND.jsonl` (shared, append-only,
union-merged at the train). AP §7.2's lesson is carried: a landed row is never rewritten --- a
correction is an errata row.
"""

from __future__ import annotations

import datetime as dt
import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[5]
AUD = REPO / "docs/audits/fable5-vision-audit-20260725"
SIDE = AUD / "phase6/receipts/REPAIR_QUEUE_APPEND.jsonl"
MINE = AUD / "phase12/receipts/REPAIR_QUEUE_AV.json"

ROWS = [
    {
        "sleeve": "fx_jpy",
        "prescription": "ARMED_SLEEVE_IS_NEGATIVE_ON_ITS_OWN_EXTENDED_COST_TRUE_STREAM",
        "is_primary": True,
        "verdict": "OWNER_DECISION",
        "component": "docs/audits/fable5-vision-audit-20260725/phase12/receipts/AV_METALABEL_FX_JPY_V1.json",
        "action": (
            "`fx_jpy` is ARMED on BOTH live accounts (five-sleeve expansion, 2026-07-30 "
            "~11:52Z). Re-derived over the matched FTMO M15 archive at the sleeve's OWN live "
            "exit contract (SLEEVE_EXIT_PROFILES: time_stop, final_target_r 2.5, "
            "time_stop_bars 48) and priced at broker truth, it is NEGATIVE at every cost band: "
            "gross +0.156 R/trade over 1,326 decisions, cost 0.251 R at mid, net -0.095; and "
            "at the ratified rule the gate reads -0.166 R/trade OOS on 862 scored-fold trades, "
            "p 0.994, ALL FIVE core gates failing, 1 of 5 chronological folds positive with "
            "the two most recent at -0.079 and -0.336. `regime_inflation` is False and "
            "`in_sample.mean_is_r` is -0.156, so IS and OOS agree in sign and there is no "
            "contamination story that rescues it. This is not 'unproven', it is measured "
            "negative, and it is on live money. The decision is Borhen's; the measurement is "
            "not."),
        "evidence": {
            "n_decisions": 1326,
            "window": "2024-01-02 .. 2026-07-24 (the matched FTMO M15 archive's whole span)",
            "gross_mean_r": 0.15603,
            "net_mean_r_by_band": {"flat": -0.07768, "low": -0.07942, "mid": -0.09520,
                                   "high": -0.11353},
            "gate_oos_r_per_trade_mid": -0.16611,
            "gate_p_raw_mid": 0.9943,
            "cost_decomposition_mid": {"commission": 0.09441, "spread": 0.13072,
                                       "swap": 0.0, "slippage": 0.02610},
            "reconciliation": ("1326/1326 identical decision bar, direction and stop distance "
                               "against AQ_ESTATE_TRADES_V2; 1323/1326 identical r_gross, and "
                               "all three differences are the live time stop the estate walk "
                               "did not apply"),
        },
        "margin": None,
    },
    {
        "sleeve": "fx_jpy",
        "prescription": "THE_ESTATE_STREAM_TRIPLE_COUNTS_EVERY_DECISION",
        "is_primary": True,
        "verdict": "DEFECT_IN_A_SHARED_ARTIFACT",
        "component": "docs/audits/fable5-vision-audit-20260725/phase11/receipts/AQ_ESTATE_TRADES_V2.json.gz",
        "action": (
            "`AQ_ESTATE_TRADES_V2.json.gz` carries **3,984 fx_jpy rows over 1,328 distinct "
            "(symbol, decision_day) decisions** --- exactly three rows for every decision, in "
            "all 1,328 cases. The cause is the generator's own `_CATCHUP_GRACE = 2` "
            "(`sleeves/fx_jpy.py:110`), which deliberately re-fires the SAME 4th-session-bar "
            "signal on the next two M15 bars so a bar missed during downtime can still be "
            "taken; a walk with no per-day cap keeps all three, and the live book takes one "
            "trade per symbol per day. They are NOT duplicates: the copies enter one and two "
            "bars later on the same signal, **36 % of decisions resolve differently across "
            "them**, and averaging them understates the sleeve's own gross by 2.27x "
            "(+0.0687 all-rows vs +0.1558 first-only). Every published fx_jpy n and per-trade "
            "figure sourced from this artifact is affected. FIX: de-duplicate on "
            "(symbol_canonical, decision_day), keeping the earliest decision_bar_iso. CHECK "
            "`fx_jpy_ny` and every other sleeve with a catch-up grace by the same test."),
        "evidence": {
            "rows": 3984, "distinct_decisions": 1328, "rows_per_decision": {"3": 1328},
            "within_day_r_disagreement_share": 0.3592,
            "gross_all_rows": 0.06871, "gross_first_only": 0.15578,
            "measured_by": "docs/audits/fable5-vision-audit-20260725/phase12/receipts/av_metalabel_fx_jpy.py --stage all",
        },
        "margin": None,
    },
    {
        "sleeve": None,
        "prescription": "THE_SAMPLE_CONSTRAINT_IS_TWO_CURRENCIES_AND_WIDTH_IS_EXHAUSTED",
        "is_primary": True,
        "verdict": "STANDARD_FOR_EVERY_FUTURE_DATA_ASK",
        "component": "docs/audits/fable5-vision-audit-20260725/phase12/receipts/AV_POOLING_CENSUS_V1.json",
        "action": (
            "'The family needs more sample' is two prescriptions bought with different money. "
            "The gate's null is a block sign-flip on the pooled DAILY series, so the "
            "resolution currency is distinct decision DAYS, not trades: a member firing on "
            "days its family already covers buys zero resolution. Measured over AF's 30 "
            "families at the ratified rule: the median member brings **31.8 %** of its own "
            "decision days as new blocks and 8 families are under 20 % "
            "(`fam_donchian_20_breakout_fx_h4` at **1.2 %**). Routing: CALENDAR_TIME_ONLY 13, "
            "NEITHER_REACHES 15 (p = 1.0, wrong sign --- no amount of data helps), BOTH 1, "
            "NOT_EVALUABLE_AT_RANK 1. **Width helps at most 1 of 30.** Every future 'more "
            "breadth' proposal should be priced against its family's marginal block yield "
            "before it is funded, and every data ask should state which currency it buys."),
        "evidence": {
            "families": 30, "all_reject": True,
            "median_share_of_days_unique_to_a_member": 0.3184,
            "roll_up": {"CALENDAR_TIME_ONLY": 13, "NEITHER_REACHES": 15, "BOTH": 1,
                        "NOT_EVALUABLE_AT_RANK": 1},
            "caveat": "census is pooled @ mid band only; the two coherent families carry the "
                      "full four-band table in AV_POOLING_HONESTY_V1.json",
        },
        "margin": None,
    },
    {
        "sleeve": None,
        "prescription": "THE_FVG_FAMILY_CANNOT_ADMIT_AT_RANK_1_AT_ANY_EFFECT_SIZE",
        "is_primary": False,
        "verdict": "REFINES_AN_EARLIER_ROUTING",
        "component": "docs/audits/fable5-vision-audit-20260725/phase12/receipts/AV_POOLING_HONESTY_V1.json",
        "action": (
            "AP §1.5 routed `fam_energy_fvg_retest_energy_h4` as 'the residual is sample' and "
            "asked for CORN.c / COTTON.c / HEATOIL.c bars. Measured at the ratified rule the "
            "constraint is narrower and harder: at **9 gate blocks** its p-floor is 0.00205 "
            "while the BH rank-1 bar is 0.000336, so **no effect size can admit at rank 1** "
            "and the report is NOT_EVALUABLE_AT_RANK, not a p (wave-11 §2). Only distinct "
            "decision DAYS change that. Its own arithmetic: 17.2x the data, +146 blocks, "
            "~16.5 more years at its measured 8.8 blocks/year. Pooling HELPS this family "
            "(p ratio 0.53) and HURTS `fam_volume_surge_reversal_index_d1` (1.42), so AO's "
            "pooling result reproduces on a second family and is not universal."),
        "evidence": {"n_blocks_gate": 9, "p_floor": 0.00205, "bh_rank1_bar": 0.0003355705,
                     "data_multiple_needed": 17.214, "blocks_per_year": 8.824,
                     "maxbars_share": 0.075},
        "margin": None,
    },
    {
        "sleeve": None,
        "prescription": "CSVBARSOURCE_WOULD_HAVE_DOUBLE_CORRECTED_A_TRUE_UTC_SIDECAR",
        "is_primary": True,
        "verdict": "FIXED_THIS_SESSION",
        "component": "src/research_infra/replay_policy/generation.py",
        "action": (
            "`CsvBarSource._rule_for` accepted `time_column_basis == 'utc'` only, while "
            "`src/utils/research_timebase.write_sidecar` --- the sanctioned writer, and the "
            "only one --- emits `'true_utc'`. A true-UTC sidecar written by the sanctioned "
            "tool therefore fell through to the broker-local branch and had a SECOND "
            "correction applied to already-UTC stamps: F7 reintroduced one layer up, by the "
            "repair. No such sidecar existed before 2026-07-30, so nothing had ever hit it "
            "--- which is why it survived. FIXED: both spellings accepted, the new "
            "`broker_server_local_eu_calendar_corrected` basis handled, and any unrecognised "
            "basis now RAISES rather than falling through. Pinned by "
            "tests/research_infra/test_av_timebase_per_file.py."),
        "evidence": {"before": "basis 'true_utc' -> broker-local branch -> second correction",
                     "after": "('utc','true_utc') -> encoding 'utc'; unknown basis -> GenerationError",
                     "tests": 26},
        "margin": None,
    },
    {
        "sleeve": None,
        "prescription": "DATA_HISTORICAL_IS_EU_CALENDAR_CORRECTED_AND_IS_TWO_CAPTURES_SPLICED",
        "is_primary": True,
        "verdict": "MEASURED_AND_DECLARED",
        "component": "docs/audits/fable5-vision-audit-20260725/phase12/receipts/AV_TIMEBASE_VERIFY_V1.json",
        "action": (
            "`research_timebase.py:96-103` says this repo's `data/historical/` is 'ALREADY "
            "corrected' and attributes the EU-calendar defect to the VPS copy. Measured per "
            "file: THIS copy carries it too --- its stamps are true UTC outside a US/EU DST "
            "disagreement window and exactly one hour fast inside one, ~5 weeks a year. "
            "Separately, the tree is TWO CAPTURES SPLICED: seven intraday files resolve only "
            "when truncated at 2026-04-03, and their tails sit on a different clock. Both are "
            "now declared: a third `time_column_basis` expresses the EU correction, sidecars "
            "carry `valid_from`/`valid_through`, and `CsvBarSource` drops out-of-window rows "
            "and reports the count on `describe()`. The comment's CONCLUSION (leave the "
            "directory unregistered, verify the specific copy, write it a sidecar) was right; "
            "its description of the repo copy was not."),
        "evidence": {"sidecars_written": 47, "eu_corrected_files": 18,
                     "splice_date": "2026-04-03",
                     "control": "data/historical_2026/ is a KNOWN broker-local export and the "
                                "probe never contradicts it (50 STAMP_BROKER_LOCAL, 0 wrong)"},
        "margin": None,
    },
    {
        "sleeve": None,
        "prescription": "THE_PRE_2024_H1_STAMP_WAS_NECESSARY_AND_NOT_SUFFICIENT",
        "is_primary": False,
        "verdict": "SUPERSEDES_AQ_HANDOFF_ITEM_7",
        "component": "docs/audits/fable5-vision-audit-20260725/phase12/receipts/AV_WIDEN_HOUR01_V1.json",
        "action": (
            "AQ handoff item 7 priced widening the ratified hour-01 convention as 'a timebase "
            "stamp, not a capture' --- '~2 extra years on 4 of 14 symbols for roughly a day of "
            "work'. The stamp is done and it is not enough, for two measured reasons. (1) Only "
            "**2** of the 4 named symbols can widen: GBPJPY and NZDUSD live in "
            "`data/historical/`, whose pre-2024 D1 stamps are bare DATES carrying no clock at "
            "all, and NZDUSD has no provable M15; a D1 decision bar AND an M15 entry bar are "
            "both required. (2) The pre-2024 repo archive is a **different PRICE capture** "
            "from the FTMO feed the convention was measured on --- 0.4-1.4 % of shared bars "
            "match to the last digit, median relative difference 2-5 bp, on timestamps that "
            "align exactly. So its rows cannot extend that measurement. The residual ask is "
            "unchanged in kind and now exact: **the matched FTMO intraday feed before "
            "2023-12-31**, for the 14 FX-D1 cohort symbols."),
        "evidence": {"close_exact_match_frac": {"GBPUSD_D1": 0.01444, "GBPUSD_M15": 0.0045,
                                                "USDJPY_D1": 0.00361, "USDJPY_M15": 0.0036},
                     "widened_rows_available": 393, "extra_calendar_days": 442,
                     "cross_feed_arm": "published as a SENSITIVITY, not admission-grade"},
        "margin": None,
    },
    {
        "sleeve": "vp_euidx_pocgrav",
        "prescription": "THE_AUX_DATA_IS_ALREADY_HERE_AND_ONLY_ITS_CLOCK_BLOCKS_IT",
        "is_primary": True,
        "verdict": "RESIDUAL_ASK_CLOSED_EXCEPT_ONE_DECLARATION",
        "component": "docs/audits/fable5-vision-audit-20260725/phase12/receipts/AV_DEEP_H4_INGEST_V1.json",
        "action": (
            "`vp_euidx_pocgrav` has been carried for waves as needing a GER40/UK100 M1 aux "
            "fetch. Counted from the files: `bridge_ftmo_b7_4_m1_20260601_20260620` holds "
            "**20,246** GER40 M1 bars and **20,237** UK100 M1 bars against the spec's own "
            "`aux_count = 20,000`, and `bridge_ftmo_b7_4_static_20250501_20260620` holds "
            "1,728 / 1,718 H4 bars against a 201-bar warmup. Nobody had checked. What blocks "
            "it is the CLOCK, not the bars: the M1 files span 19 days, which contains no US/EU "
            "DST disagreement window, so they cannot prove their basis from their own bytes "
            "and `CsvBarSource` refuses them. TWO WAYS OUT, and they are not equivalent: a "
            "longer M1 span (measured), or a declaration from the export's own provenance "
            "(ASSERTED, and it must say so in the sidecar's evidence field)."),
        "evidence": {"ger40_m1_bars": 20246, "uk100_m1_bars": 20237, "aux_count_required": 20000,
                     "h4_bars": {"GER40": 1728, "UK100": 1718}, "warmup_bars": 201,
                     "clock_verdict": {"GER40_M1": "REFUSE_SPAN_TOO_SHORT_TO_DISCRIMINATE",
                                       "UK100_M1": "REFUSE_SPAN_TOO_SHORT_TO_DISCRIMINATE"}},
        "margin": None,
    },
    {
        "sleeve": None,
        "prescription": "THE_V5_UNION_MERGE_LEFT_THE_RATCHET_FLOOR_NINE_MEMBERS_TOO_LOW",
        "is_primary": True,
        "verdict": "REPAIRED_IN_V6__ONE_HALF_STILL_OPEN",
        "component": "docs/audits/fable5-vision-audit-20260725/phase11/receipts/CANDIDATE_FAMILY_V5.json",
        "action": (
            "`CANDIDATE_FAMILY_V5`'s `CANDIDATE_BOOK_V1` carries **48 members (45 look_taken)** "
            "while its stored `high_water_size` / `high_water_looks` are **39 / 36**. The "
            "orchestrator's union merge appended AR's nine members and did not raise the "
            "marks. **No published number is wrong**: `effective_size()` is "
            "`max(high_water_size, len(members))`, so the bill read 48 anyway. But the "
            "high-water mark is the ONLY thing that stops a future withdrawal from shrinking a "
            "family, and at 39 the floor sat nine members below the looks actually taken --- a "
            "later session removing AR's nine would have dropped the bill to 39 and it would "
            "have looked lawful. That is precisely the curation the ratchet exists to prevent. "
            "REPAIRED in `CANDIDATE_FAMILY_V6.json` (53 / 50) as a side effect of the normal "
            "`max()` update. STILL OPEN: V5 carries **no history entry for Session AR**, so "
            "the declaration's own audit trail does not record who added those nine. Another "
            "session's history row is not mine to author. **Check every future union merge for "
            "both halves** --- the marks and the history."),
        "evidence": {"v5_members": 48, "v5_look_taken": 45,
                     "v5_high_water_size": 39, "v5_high_water_looks": 36,
                     "v6_high_water_size": 53, "v6_high_water_looks": 50,
                     "v5_history_entries": ["Session AL (wave 9)", "Session AO (wave 10)"],
                     "missing_history_entry_for": "Session AR (wave 11), which added the nine"},
        "margin": None,
    },
    {
        "sleeve": None,
        "prescription": "AR_BLOCKS_B1454_B1499_ARE_CITED_AND_UNWRITTEN",
        "is_primary": False,
        "verdict": "EXEMPTION_RESTORED__THE_BLOCKS_ARE_STILL_UNWRITTEN",
        "component": "docs/audits/fable5-vision-audit-20260725/IMPLEMENTATION_STATE.md",
        "action": (
            "`IMPLEMENTATION_STATE.md` contains **no B1454+ block**, while "
            "`phase11/SESSION_AR_CONDITIONING_TO_SIZING_RESULT.md` cites 40 of them "
            "individually. AR §6 says so itself: 'AN wrote its blocks into "
            "IMPLEMENTATION_STATE; AO did not. This follows AO, and carries the detail in its "
            "result doc.' The wave-11 train then retired AR's `IN_FLIGHT_WAVE_RANGES` entry on "
            "the note 'B1400-B1453 and B1450-B1499 are written (both sets exist)' --- and only "
            "B1450-B1453 exist, which are AQ's borrowed four. The entry read as retired only "
            "because every AR citation sat ABOVE the block ceiling and was exempt as a forward "
            "allocation; AV's blocks raised the ceiling to B1668 and they fell out of it. "
            "`(1450, 1499)` is RESTORED as ACTIVE with the correction recorded in the test's "
            "own comment. The exemption is a stopgap: **either AR's blocks land in "
            "`IMPLEMENTATION_STATE.md` or its result doc stops citing them as individual "
            "tokens**, and the same test will call the entry DEAD the moment one of those "
            "happens."),
        "evidence": {"blocks_defined_above_1400":
                     "1401-1406, 1416-1417, 1422-1426, 1429, 1436, 1443, 1447-1453",
                     "n_dangling_ar_citations": 40,
                     "rule": "WAVE_11_WORKING_AGREEMENT.md section 4 --- whoever raises the "
                             "ceiling past a sibling owns IN_FLIGHT_WAVE_RANGES"},
        "margin": None,
    },
    {
        "sleeve": None,
        "prescription": "A_FILTER_ON_A_PINNED_COORDINATE_IS_A_NO_OP_AND_MY_OWN_MODEL_HAD_TWO",
        "is_primary": False,
        "verdict": "SELF_CORRECTION",
        "component": "docs/audits/fable5-vision-audit-20260725/phase12/receipts/AV_METALABEL_FX_JPY_V1.json",
        "action": (
            "The wave-11 §2 identity-filter check, run at both layers on my own meta-label's "
            "13 features, found **2 pinned by construction**: `broker_hour` (the sleeve fires "
            "at exactly the 4th London session bar, so every trade shares one hour) and "
            "`session_impulse_atr` (target/stop is the fixed 2.5/1.0 geometry). Their weights "
            "are unidentified and they contribute nothing. Reported rather than silently "
            "dropped, because a reader has to be able to check what the model was given. Any "
            "future overlay should run the check on its OWN feature list before fitting."),
        "evidence": {"features": 13, "pinned": ["broker_hour", "session_impulse_atr"],
                     "oos_auc": 0.5233},
        "margin": None,
    },
]


def main() -> int:
    now = dt.datetime.now(dt.timezone.utc).isoformat()
    rows = [{**r, "session": "AV", "appended_utc": now} for r in ROWS]
    MINE.write_text(json.dumps(
        {"schema": "gtos.repair_queue.session_copy.v1", "session": "AV",
         "blocks": "B1600-B1670", "n_rows": len(rows),
         "note": ("this file is regenerated in full and is AUTHORITATIVE for AV's rows; the "
                  "shared sidecar is append-only and a landed row there is never rewritten "
                  "(AP §7.2) --- a correction is an errata row."),
         "rows": rows}, indent=2, sort_keys=True) + "\n")

    before = sum(1 for _ in SIDE.open()) if SIDE.is_file() else 0
    existing = set()
    if SIDE.is_file():
        for line in SIDE.open():
            try:
                d = json.loads(line)
            except json.JSONDecodeError:
                continue
            existing.add((d.get("session"), d.get("sleeve"), d.get("prescription")))
    appended = 0
    with SIDE.open("a") as fh:
        for r in rows:
            key = ("AV", r["sleeve"], r["prescription"])
            if key in existing:
                continue
            fh.write(json.dumps(r, sort_keys=True, default=str) + "\n")
            appended += 1
    after = sum(1 for _ in SIDE.open())
    collisions = [k for k in
                  ((r["sleeve"], r["prescription"]) for r in rows)
                  if any(e[1] == k[0] and e[2] == k[1] and e[0] != "AV" for e in existing)]
    print(f"REPAIR_QUEUE_AV.json: {len(rows)} rows")
    print(f"shared sidecar: {before} -> {after} (+{appended})")
    print(f"cross-session prescription collisions: {len(collisions)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
