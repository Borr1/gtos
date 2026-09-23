#!/usr/bin/env python3
"""w0-dictionary — emit w0_DATA_DICTIONARY.md + w0_DICTIONARY.json from measured inputs."""
import gzip, json, os, sys, collections, datetime

ROOT="/Users/borr/GTOSActive/worktrees/wave19-broad-forensic-20260801"
D=os.path.join(ROOT,"docs/audits/fable5-vision-audit-20260725/phase19/receipts/discovery")
sys.path.insert(0,D)
import w0_dictionary_meta as META

POOL=os.path.join(ROOT,"docs/audits/fable5-vision-audit-20260725/phase16/receipts/pools/CJ_RECLOCKED_S0R0_POOL_V1.jsonl.gz")
PROF=json.load(open(os.path.join(D,"w0_POOL_PROFILE.json")))
T=os.environ.get("TMPDIR","/tmp")+"/w0d"
ENUMS=json.load(open(T+"/enums.json"))["fields"]
COSTGATE=json.load(open(T+"/costgate.json"))
OVER=json.load(open(T+"/overcharge.json"))
IDENT=json.load(open(T+"/ident.json"))
ASSETS=json.load(open(T+"/assets.json"))

F=PROF["fields"]; N=PROF["n"]
GROUP_ORDER=["identity","time","cost","belief","fill","admission","scheduler","geometry","context","outcome"]
GROUP_TITLE={"identity":"1.1 IDENTITY & MECHANISM","time":"1.2 TIME & SESSION","cost":"1.3 COST",
 "belief":"1.4 BELIEF / EV","fill":"1.5 FILL","admission":"1.6 ADMISSION & BLOCKING",
 "scheduler":"1.7 SCHEDULER","geometry":"1.8 GEOMETRY","context":"1.9 EXPOSURE CONTEXT","outcome":"1.10 OUTCOME"}

def rng(k):
    e=F[k]
    if "min" in e:
        if e.get("constant"): return f"const {e['min']:.6g}"
        return f"{e['min']:.5g} .. {e['max']:.5g} (mean {e['mean']:.5g})"
    if e["cardinality"]==0: return "(all null)"
    tops=(ENUMS.get(k) or {}).get("top") or [[str(t[0]),t[1],t[1]/N] for t in e["top"]]
    parts=[]
    for row in tops[:3]:
        v,c=str(row[0]),row[1]
        parts.append(f"{v[:26]} {c/N*100:.1f}%")
    tail=f" (+{e['cardinality']-len(parts)} more)" if e["cardinality"]>len(parts) else ""
    return "; ".join(parts)+tail

def cell(s):
    return str(s).replace("`","")

L=[]
w=L.append
w("# w0_DATA_DICTIONARY — the shared map for the wave-19 discovery swarm")
w("")
w(f"Generated {datetime.date.today().isoformat()} by `w0_dictionary_build.py` from the pool itself, from")
w("`src/` at this worktree's HEAD, and from the measurement receipts listed in §6.")
w("**Every number here was measured, not quoted.** Where this file contradicts the swarm brief, the")
w("contradiction is flagged inline with the measurement that settles it.")
w("")
w("---")
w("")
w("## 0. THE SIX THINGS TO READ FIRST")
w("")
w("These change how you must interpret every query you are about to run.")
w("")
w("**0.1 — The pool contains ZERO executed trades. It is 100% counterfactual, by construction.**")
w(f"The raw ledger `CJ_RECLOCKED_S0R0_V7_MISSED_OPPORTUNITY_LEDGER.jsonl` holds **153,425 rows**; the pool is the")
w(f"**{N:,} ({N/153425*100:.2f}%)** that pass the scoreability gate at")
w("`v4_timewarp_simulated_live_research_loop.py:28130-28140`. That gate requires `not headline_r_scoreable`,")
w("so a candidate that actually reached headline execution is **excluded**. `missed_opportunity_r_scoreability_status`")
w("is the constant `diagnostic_opportunity_r_scoreable` on all rows *because that is the filter*. Never describe this")
w("pool as \"what the system traded\".")
w("")
w("**0.2 — The binding cost gate is the SPREAD cap, not the 0.15 total.** The brief names")
w("`total_cost_r_exceeds_limit` vs `0.15`. There are **two independent limbs** in")
w("`broker_net_cost_engine.py:pretrade_cost_refusal_reasons` and the other one dominates:")
w("")
w("| limb | source | config | rows tripped |")
w("|---|---|---|---:|")
w("| `spread_r_exceeds_selected_cell_limit` | `broker_net_cost_engine.py:859-866` | `selected_cell_pretrade_max_spread_r: 0.10` (`config/agent_config.yaml:715`) | **17,258 (62.40%)** |")
w("| `total_cost_r_exceeds_limit` | `broker_net_cost_engine.py:923-927` | `selected_cell_pretrade_max_total_cost_r: 0.15` (`config/agent_config.yaml:716`) | 20,074 (72.58%) |")
w("")
j=COSTGATE["joint"]
w(f"Decomposing the **20,448 refusals**: spread-only **{j[str(('REFUSED', True, False))]}**, total-only **{j[str(('REFUSED', False, True))]}**, "
  f"**both {j[str(('REFUSED', True, True))]}**. The spread cap alone binds **{17258/20448*100:.1f}%** of all refusals, and spread is")
w("exactly the term measured overcharged 7.3-8.5x. Pricing that overcharge against the gates:")
w("")
w("| spread divided by | candidates PASSING both gates | share | vs shipped |")
w("|---|---:|---:|---:|")
for k in ["1.0","2.0","4.0","7.3","8.5","1000000000.0"]:
    v=OVER["ks"][k]; lbl="shipped (1.0x)" if k=="1.0" else ("spread -> 0 (bound)" if k.startswith("1e") or k=="1000000000.0" else k+"x")
    w(f"| {lbl} | {v['pass']:,} | {v['pass_share']*100:.2f}% | {v['pass']/7210:.2f}x |")
w("")
w("At the measured 7.3x the pass rate goes **26.07% -> 59.45%, a 2.28x increase** — which independently")
w("reproduces the established \"fixing costs makes the system trade ~2.2-2.4x MORE\" from twelve full")
w("month-replays. The gate model in this dictionary is therefore validated against known ground truth.")
w("")
w("**0.3 — `final_blocker_class` is a substring cascade with fixed precedence, not a causal attribution.**")
w("`moonshot_scheduler_v4_best_trade_allocator.py:14265-14349` tests reason text in a fixed order and returns the")
w("first match. `cost_authority` is checked **first**; `fill_realism` at `:14349` is the **fallthrough default**")
w("(so its 148 rows mean \"nothing matched\", not \"fill realism blocked it\"). A second classifier at")
w("`order_blocker_precedence.py:172-188` ranks `cost_authority` at **1**, second only to source authority, so")
w("whenever a candidate carries several co-blockers **cost wins the tie-break by construction**. The raw ledger's")
w("`package_replay_order_executable_final_co_blockers` (`v4_timewarp:13692`) is **not projected into the pool**, so")
w("the pool cannot tell you what else would have blocked a row. **Treat 73.93% as an upper bound on cost's causal role.**")
w("Use `miss_reason` (32 values) when you need causality.")
w("")
w("**0.4 — Only 29 of 78 fields are trustworthy. 19 carry no information at all.**")
tc=collections.Counter(v[3] for v in META.M.values())
w("")
w("| trust class | fields | meaning |")
w("|---|---:|---|")
for k in ["TRUST","CONTAMINATED","DEGENERATE","CONSTANT","DIAGNOSTIC","UNPOPULATED"]:
    w(f"| `{k}` | {tc[k]} | {META.TRUST_LEGEND[k]} |")
w("")
w("**0.5 — Five exact-duplicate column pairs, verified at 1e-12 over all 27,658 rows.** Using both members of a")
w("pair as \"two features\" is double-counting:")
w("`cost_r == expected_cost_r` | `candidate_ev_r == expectancy_r` | `fill_probability == entry_quality_fill_probability`")
w("| `execution_fill_probability == limit_fillability_probability` | `direction == side`.")
w("Three further families collapse 1:1: `origin_family == framework == route_family` and")
w("`session_bucket == authority_session == kill_zone`.")
w("")
w("**0.6 — `execution_fill_probability` is NOT a flat 0.92.** The brief states it is constant. Measured: **7,400")
w("distinct values**, range 0.0401..0.95, mean 0.8051, 152 nulls. `0.92` covers **19,452 rows (70.32%)** and is the")
w("value of the `limit_marketable` branch at `poi_execution_lifecycle.py:174-176`, not a global constant.")
w("What IS constant: `expected_slippage_r` (0.02), `candidate_confidence` (0.55), `source_completeness` (1.0),")
w("`fill_realism_executable`/`entry_fill_executable` (both True), `dynamic_geometry_policy`, `decision_timeframe`.")
w("")
w("---")
w("")
w("## 1. POOL SCHEMA — all 78 fields")
w("")
w(f"Source: `docs/audits/.../phase16/receipts/pools/CJ_RECLOCKED_S0R0_POOL_V1.jsonl.gz`, n = **{N:,}**, January 2026, true UTC.")
w("`null` = null rate. `card` = distinct non-null values. Source lines are `src/`-relative and were located")
w("against this worktree's HEAD.")
w("")
for g in GROUP_ORDER:
    ks=[k for k in PROF["fields"] if META.M.get(k,("",))[0]==g]
    if not ks: continue
    w(f"### {GROUP_TITLE[g]}")
    w("")
    w("| field | dtype | null | card | range / top | trust | written at |")
    w("|---|---|---:|---:|---|---|---|")
    for k in ks:
        e=F[k]; m=META.M[k]
        w(f"| `{k}` | {e['dtype'] or 'null'} | {e['null_rate']*100:.2f}% | {e['cardinality']} | {cell(rng(k))} | `{m[3]}` | {cell(m[2])} |")
    w("")
    for k in ks:
        m=META.M[k]
        w(f"**`{k}`** — {m[1]}")
        for fl in m[4]: w(f"  - {fl}")
        w("")
w("---")
w("")
w("## 2. TRUSTWORTHY vs CONTAMINATED")
w("")
w("### 2.1 The frozen-cost defect: exactly which fields inherit it")
w("")
w("The overcharge lives in **one** term — `spread_r` — computed at `broker_net_cost_engine.py:298-306` as")
w("`spread_r = |ask - bid| / sl_distance`. The division is correct; the `ask`/`bid` the replay feeds are not.")
w(f"`spread_r` is **mean 0.5642 R of a 0.6632 R total cost = 85.07%** of every charge in this pool.")
w("")
w("**Inherits the defect (do not quote as economics without restating cost):**")
w("")
w("| field | how it inherits |")
w("|---|---|")
w("| `spread_r` | is the defect |")
w("| `cost_r`, `expected_cost_r` | sum containing `spread_r` (`:700-706`) |")
w("| `broker_pretrade_diag_expected_cost_r` | same packet |")
w("| `old_proxy_vs_broker_calibrated_delta_r` | difference against the same packet |")
w("| `expected_net_r` | `candidate_ev_r` minus the contaminated cost; its −18.17 tail IS the overcharge |")
w("| `opportunity_net_proxy_r` | **the outcome column** — cost already subtracted |")
w("| `pretrade_cost_packet_status`, `broker_pretrade_cost_executable`, `final_blocker_class=='cost_authority'`, `selector_reason` cost limbs | the *verdicts* the defect produces |")
w("")
w("**Clean of it:**")
w("")
w("| field | why |")
w("|---|---|")
w("| `gross_r` (working set) | `= opportunity_net_proxy_r + cost_r`, the exact algebraic inverse of the engine's own subtraction (`w0_build_working_set_v2.py:301`). Adding back the identical `cost_r` cancels the error exactly. Pool gross mean **−0.2175 R**. |")
w("| `commission_r` (mean 0.0652 R), `swap_cost_r` (mean 0.0137 R) | broker-true terms, independent of the spread model |")
w("| all path geometry (`mfe_r`, `mae_r`, `bars_to_*`, `which_came_first`, `r_at_bar_*`) | measured off M1 bars, never touches the cost model |")
w("| all identity, time, session, geometry-price fields | pre-cost |")
w("")
w("### 2.2 Contamination that is NOT the cost model")
w("")
w("- **Belief calibration.** `candidate_probability` mean **0.7658** against a measured gross win rate of")
w("  **0.3468** — over-confident **2.21x**. Minimum predicted probability is **0.5843**: the generator never")
w("  emits a candidate it believes is worse than a coin flip. `candidate_ev_r` is **positive on every single")
w("  row** (min +0.3985) against a pool gross mean of −0.2175 R. Neither field ever sees a realized return.")
w("- **Fill fiction.** `fill_realism_executable` and `entry_fill_executable` are `True` on all 27,658 rows;")
w("  `fill_probability` is never validated. W0-F2 measured the cost: requiring the entry limit to actually")
w("  trade moves the pool **+0.0409 -> −0.2367 R/trade**, i.e. the fill-blind convention manufactures")
w("  **+0.2776 R/trade** of edge no limit order could capture.")
w("- **`limit_marketable_at_decision` is 85.19% NULL** (23,563 rows). The most important fill question in the")
w("  pool is unanswered on 6 of every 7 rows, and it is answered exactly on the 4,095 rows that reached")
w("  scheduler materialization.")
w("- **`policy_target_r` disagrees with the price geometry on 1,229 rows (4.44%)**, reaching 505R, while")
w("  `take_profit_1` implies exactly 2.0000R on every row. 85% of the disagreements are `current_breaker_re_entry`.")
w("")
w("---")
w("")
w("## 3. PATHS SCHEMA")
w("")
sc=ASSETS.get("docs/audits/fable5-vision-audit-20260725/phase18/receipts/pools/CQ_TRUE_UTC_S0R0_ORDERED_PATH_SIDECAR_V1.jsonl.gz",{})
w(f"`CQ_TRUE_UTC_S0R0_ORDERED_PATH_SIDECAR_V1.jsonl.gz` — **{sc.get('rows',0):,} rows, {sc.get('bytes',0)/1e6:.1f} MB gz, 12 fields.**")
w("")
w("| field | type | meaning |")
w("|---|---|---|")
for a,b,c in [("schema","str","`gtos-session-ck-ordered-path-sidecar-v1`"),
  ("arm_id","str","`S0R0`"),("candidate_id","str","join key part 1"),
  ("decision_time_utc","str","join key part 2"),("horizon_end_utc","str","decision_time + 2h"),
  ("symbol","str","instrument"),("side","str","LONG/SHORT"),
  ("source_timeframe","str","**`M1`** on every row"),
  ("source_path","str","e.g. `sources/bars/bridge_ftmo_m1_202601/BTCUSD_M1.csv`"),
  ("source_sha256","str","content hash of the bar file"),
  ("ordered_tick_source","null","**always null — there is no tick-level path anywhere in this asset**"),
  ("ordered_path_observations","list","the bars; each `{open, high, low, close, time_utc}`")]:
    w(f"| `{a}` | {b} | {c} |")
w("")
w("**Bar structure.** Each observation is OHLC + `time_utc`. **There is no volume, no bid/ask and no spread**,")
w("so no within-bar fill or slippage question can be answered from this asset — only price-touch questions.")
w("")
w("**Horizon.** The first bar is the M1 bar **after** the decision (decision 00:15:00 -> first bar 00:16:00) and the")
w("last is `decision_time + 2h`. Every path is **<= 120 M1 bars = a hard 2-hour cap**; 86.12% are exactly 120")
w("(mean 116.78, min 3, max 120). **No holding-time or time-stop question beyond 2h is answerable from this pool at all.**")
w("")
w("**Join.** Key is `(candidate_id, decision_time_utc)` — *not* `candidate_id`, which repeats (§0.5, W0-F1).")
w(f"**Coverage is total: 27,658 pool rows / 27,658 sidecar rows / 0 rows without a path / 0 duplicate keys /")
w("0 side-or-symbol mismatches** (`w0_WORKING_SET_BUILD_V2.json`).")
w("")
w("**Read the WORKING SET, not this file.** `w0_WORKING_SET.jsonl.gz` (128 cols = 78 pool + 50 derived) loads in")
w("**0.53 s**; `w0_R_PATHS.jsonl.gz` streams bar-level R in **0.68 s**. Streaming the raw 34 MB sidecar is the")
w("15-minute stall that killed four agents. Helper: `w0_ws.py` (`load()`, `key()`, `dedup()`, `walk()`, `bars_to_fav()`).")
w("")
w("---")
w("")
w("## 4. ASSET INVENTORY")
w("")
w("### 4.1 Pools and paths (measured row counts)")
w("")
w("| asset | rows | cols | size | window | status |")
w("|---|---:|---:|---:|---|---|")
AR=[("phase16/.../pools/CJ_RECLOCKED_S0R0_POOL_V1.jsonl.gz",27658,78,"5.70 MB","Jan 2026, TRUE UTC","**HEAVILY READ** — the swarm's primary substrate; T1/T2, funnel_jan, scorecard, calibration, w0 all read it"),
 ("phase18/.../pools/CQ_TRUE_UTC_S0R0_ORDERED_PATH_SIDECAR_V1.jsonl.gz",27658,12,"34.13 MB","Jan 2026, M1 bars","READ by w0 (fully consumed into the working set)"),
 ("phase19/discovery/w0_WORKING_SET.jsonl.gz",27658,128,"10.34 MB","Jan 2026","**BUILT BY WAVE 0 — read this**"),
 ("phase19/discovery/w0_R_PATHS.jsonl.gz",27658,10,"23.58 MB","Jan 2026","bar-level R arrays, built by wave 0"),
 ("phase18/.../pools/CP_FEBRUARY_S0R0_POOL_V1.jsonl.gz",24239,101,"5.34 MB","Feb 2026, TRUE UTC","**USED-ONCE VAL.** Wave 18 read it pre-outcome and it REJECTED broad V4 (0/20 positive days, precision 0.309 vs 0.606 breakeven). Not virgin. Do not re-spend."),
 ("phase18/.../pools/CQ_CURRENT_BREAKER_REPAIR_TRADES_V1.jsonl.gz",4263,24,"0.92 MB","Jan 2026","READ by CQ — the inverted-breaker candidate (+11.9 net R/trade TRAIN and Jan VAL)"),
 ("phase16/.../pools/CD_REPAIRED_POOL_S0R0_V1.jsonl.gz",28544,78,"5.89 MB","Jan 2026, **UTC+2 (pre-CJ clock)**","superseded by CJ; comparator only"),
 ("phase16/.../pools/CD_REPAIRED_POOL_S0R1_V1.jsonl.gz",28546,78,"5.89 MB","Jan 2026, UTC+2","sizing-switch arm, pre-clock"),
 ("phase16/.../pools/CD_REPAIRED_POOL_S1R0_V1.jsonl.gz",28552,78,"5.89 MB","Jan 2026, UTC+2","selection-switch arm, pre-clock"),
 ("phase16/.../pools/CD_REPAIRED_POOL_S1R1_V1.jsonl.gz",28553,78,"5.89 MB","Jan 2026, UTC+2","joint incumbent, pre-clock"),
 ("phase19/forensic/walk/WALK_2D_CANDIDATES.jsonl.gz",8448,24,"0.81 MB","2-day fixture","walk annex")]
for a,b,c,d,e,f_ in AR: w(f"| `{a}` | {b:,} | {c} | {d} | {e} | {f_} |")
w("")
w("**The raw ledger is NOT on this machine.** `CJ_RECLOCKED_S0R0_V7_MISSED_OPPORTUNITY_LEDGER.jsonl`")
w("(153,425 rows) is referenced by `phase16/receipts/CJ_RECLOCKED_POOL_S0R0_V1.json` at a path under")
w("`research/operations/final_moonshot_..._2026_06_20/attempt_5_typed_sparse/CJ_RECLOCKED_S0R0_V7/` that does not")
w("exist in any worktree. **The 125,767 non-scoreable rows are therefore unrecoverable without a re-run.**")
w("")
w("### 4.2 The four CD arms vs the one CJ arm — the clock")
w("")
w("The `CD_REPAIRED_*` pools are the **pre-re-clock** generation (sealed labels = true UTC + 2h, CJ, 54/54 weekly")
w("opens). `CJ_RECLOCKED_S0R0_POOL_V1` is the same S0R0 arm at true UTC and is the only re-clocked pool.")
w("**Row counts differ (28,544 vs 27,658)** because re-clocking moves candidates across session and day")
w("boundaries. Never pool a CD arm with the CJ arm, and never carry a CD-derived session/hour finding forward —")
w("the authoritative B_TIME map is `phase18/receipts/CP_TRUE_UTC_B_TIME_MAP_V1.json` (all 83 cells negative),")
w("which supersedes AW's.")
w("")
w("### 4.3 February carries 23 fields January does not")
w("")
w("`CP_FEBRUARY_S0R0_POOL_V1` has **101 fields to January's 78**, and every January field is present. The extra 23:")
w("")
w("`raw_gross_r`, `raw_net_proxy_r`, `raw_opportunity_close_reason`, `policy_gross_r`, `opportunity_gross_r`,")
w("`opportunity_close_reason`, `terminal_outcome`, `counterfactual_order_close_time_utc`, **`target_first_touch_utc`**,")
w("**`stop_first_touch_utc`**, **`same_bar_ambiguity`**, **`ambiguity_resolution`**, `terminal_r_diagnostic_outcome`,")
w("`terminal_r_diagnostic_gross_r`, `terminal_r_diagnostic_close_reason`, `terminal_r_diagnostic_target_r`,")
w("`path_source`, `path_source_timeframe`, `path_index_source_path`, `path_index_source_sha256`,")
w("`path_index_rows_returned`, `path_row_count`, `ordered_tick_truth_satisfied`.")
w("")
w("**February's pool carries first-touch timestamps and same-bar ambiguity resolution INLINE.** January needs the")
w("separate path sidecar to get the same thing. If you need a first-touch or ambiguity method validated, February")
w("is the pool that already answers it — but note February is used-once VAL and its economics are spent.")
w("")
w("### 4.4 Receipt directories")
w("")
w("| directory | contents | status |")
w("|---|---|---|")
for a,b,c in [
 ("`phase19/receipts/discovery/`","40 files — the wave-0 working set, helper, README, build receipts, and this dictionary","**the swarm's shared substrate**"),
 ("`phase19/receipts/forensic/t1/`","`T1_SCREENS_V1.json/.md`, `CELL_DECLARATION_V1.md`, 3 working scripts (`t1_screens.py`, `t1_fill_axis.py`, `t1_rcaps_frontier.py`)","READ — copy the scripts, they already stream the pool correctly"),
 ("`phase19/receipts/forensic/t2/`","the six January arms: `T2_ARM_{I..V}_ANALYSIS.json`, `T3_SWAP_ISO_ANALYSIS.json`, `T2_ARMS_V1.md`","READ — these answered \"is it defensible\", never \"where does the money go\""),
 ("`phase19/receipts/forensic/a1_cleanroom/`","19 files — A1 method-defect adjudication, corrected nulls","READ"),
 ("`phase19/receipts/forensic/a2_verify/`","40 files — recomputes, reconciliation, family-tension","READ"),
 ("`phase19/receipts/forensic/walk/`","`WALK_2D_ANNEX`, `WALK_2D_CANDIDATES.jsonl.gz` (8,448)","READ"),
 ("`research/operations/wave19_broad_forensic_2026_08_01/`","8 lanes: `funnel_jan` (12), `funnel_feb` (15), `scorecard` (13), `calibration` (8), `cartographer` (7), `priors` (6), `trades_jan` (6), `trades_feb` (9)","READ — see §5 note on `cartographer/DECISION_CYCLE_MAP.md`"),
 ("`phase19/receipts/march/` (worktree `fa2-integration-20260803`, branch `phase19/march-confirm`)","13 top-level + `analysis/` (7 arm analyses) + `arm_receipts/` (12 + six `*_LANE` dirs each with `LANE_RUN_RECEIPT.json` + `LANE_TRADE_TABLE.jsonl`)","READ — six March arms; corroborates the 7.3-8.5x spread overcharge independently"),
 ("`phase16/receipts/`","40 files incl. `CJ_PACKS_{JANUARY,FEBRUARY,APRIL,MAY}_*.json` and 4 `*_LANE` dirs","pack manifests"),
 ("`phase18/receipts/`","26 files incl. `CANDIDATE_FAMILY_V26/V27.json`, `CP_TRUE_UTC_B_TIME_MAP_V1.json`","the V27 family tip = the multiplicity bill")]:
    w(f"| {a} | {b} | {c} |")
w("")
w("### 4.5 What is still VIRGIN — Wave 2's fuel")
w("")
w("| window | pack | status |")
w("|---|---|---|")
w("| **January 2026** | `CJ_PACKS_JANUARY_V3.json` | SPENT — the substrate of this whole swarm |")
w("| **February 2026** | `CJ_PACKS_FEBRUARY_V2.json` | **USED ONCE (wave 18) and it REJECTED.** Economics spent. Method-validation use only. |")
w("| **March 2026** | six arms under `phase19/receipts/march/` | READ by the fa2 lane. Note CLAUDE.md's standing \"keep March outcome-unread\" was **overtaken** — March has been read. |")
w("| **April 2026** | `CJ_PACKS_APRIL_V2.json` | **ECONOMICS UNREAD — VIRGIN.** True-UTC lane pack exists. Wave 2 fuel. |")
w("| **May 2026** | `CJ_PACKS_MAY_V1.json` | **ECONOMICS UNREAD — VIRGIN.** True-UTC lane pack exists. Wave 2 fuel. |")
w("")
w("**April and May are the only two windows whose economics have never been read.** Session CS was")
w("commissioned to read them as CQ's two missing gate folds. **Do not spend them in Wave 1.**")
w("")
w("---")
w("")
w("## 5. THE DECISION PATH — generation to fill, in one page")
w("")
w("Ordered stages. `verdict field(s)` are the pool columns that record each stage's outcome, so you can")
w("navigate the funnel without re-reading source. **Survivor counts are measured over this pool** (n=27,658).")
w("")
w("| # | stage | source | verdict field(s) | measured |")
w("|---|---|---|---|---|")
ST=[("1","Candidate generation — origin family fires on an M15 bar","`components/broader_origin_generators.py` (`origin_family` :442, geometry :1909, session :1934-1944)","`origin_family`, `entry_price`, `stop_loss`, `take_profit_1`, `decision_time_utc`","27,658 candidates, 10 families, 24 symbols, 1,969 M15 windows"),
 ("2","Geometry contract — target fixed at 2R","`v4_timewarp:88504` (`raw_target_r`), `:88931` (`policy_target_r`)","`take_profit_1`, `policy_target_r`, `raw_target_r`","`take_profit_1` implies **exactly 2.0000R on all 27,658**; `policy_target_r` disagrees on 1,229 (4.44%)"),
 ("3","Belief attachment — probability and EV","`components/ultimate_candidate_package.py:1724-1727`, `:2985-2988`","`candidate_probability`, `candidate_ev_r`, `expectancy_r`, `candidate_confidence`","p mean **0.7658** vs measured 0.3468; EV **positive on every row**; confidence a constant 0.55 default"),
 ("4","**Broker pretrade cost packet** — the dominant gate","`components/broker_net_cost_engine.py`: spread `:298-306`, total `:700-706`, refusal reasons `:846-928`, status `:842`","`spread_r`, `cost_r`, `commission_r`, `swap_cost_r`, `pretrade_cost_packet_status`, `broker_pretrade_cost_executable`","**20,448 REFUSED (73.93%) / 7,210 PASSED**. Spread limb binds 84.4% of refusals"),
 ("5","Fill-quality attachment","`components/poi_execution_lifecycle.py:174-199` (`fill_probability`), `:407`, `:224` (`limit_marketable_at_decision`)","`fill_probability`, `execution_fill_probability`, `limit_fillability_probability`, `limit_marketable_at_decision`","`limit_marketable_at_decision` **85.19% null**; the two executable booleans are `True` on every row"),
 ("6","Selector V4 admission","`components/selector_v4.py`: EV limb `:3832`, cost limb `:3843`, sleeve `:3960`/`:4500`, off-session `:2556`/`:4412`, reason `:3592`","`selector_action`, `selector_reason`, `admission_risk_class`","reject **83.22%**; only **21 rows** reach `trade`. 73.61% of rejections are cost-derived"),
 ("7","Package authority — sleeve match and admission count","`components/live_decision_packet_v4.py:486`, `moonshot_scheduler_v4:6181`","`matched_sleeve_count`, `effective_admission_count`","matched mean 1.187 (max 5); effective **never exceeds 2**"),
 ("8","Scheduler materialization","`v4_timewarp:27855-27862`; window build `:78014`","`scheduler_materialization_status`, `scheduler_selection_disposition`","**4,095 materialized (14.81%)** — and this is exactly where the fill fields get written"),
 ("9","Scheduler allocation / veto","`moonshot_scheduler_v4:15525` (displacement), `v4_timewarp:41945-41963` (option status)","`effective_selector_action`, `effective_selector_reason`, `miss_reason`","3,899 generated-not-selected; **196** preselected-then-rejected-by-finalizer"),
 ("10","Risk finalizer","`v4_timewarp:28810` (rank), `:28813` (reason); marketable guard `moonshot_scheduler_v4:13397`, `:18189`","`risk_finalizer_rank`, `risk_finalizer_reason`","rank 1..149; 73.93% `broker_cost_authority_blocked_non_executable`, 14.81% `package_executable_authority_required_not_met`"),
 ("11","Order materialization","`v4_timewarp:88003`, `:88298`","`effective_order_type`, `candidate_lifecycle_action`","`limit` 23,106 / `none` **4,552 (16.46% never got an order type)**; `new_position` 4,512"),
 ("12","Fill realism classification","`v4_timewarp:60447-60448`","`fill_realism_class`, `fill_realism_executable`, `entry_fill_executable`","`passive_queue_confirmed` 21,052 / `source_safe_immediate_marketable` 6,606. **Both booleans True on every row — never tested against the path.**"),
 ("13","Blocker resolution (post-hoc)","cascade `moonshot_scheduler_v4:14265-14349`; precedence `order_blocker_precedence.py:172-188`; carried `v4_timewarp:13686`, `:15391`","`final_blocker_class`, `miss_reason`","cost_authority 73.93%; `fill_realism` is the **fallthrough default**; co-blockers **not projected**"),
 ("14","Counterfactual walk + scoreability","`v4_timewarp:92730`/`:93122` (net proxy), gate `:28130-28146`, status `:28156`","`opportunity_net_proxy_r`, `missed_opportunity_r_scoreability_status`","**153,425 ledger rows -> 27,658 pool rows (18.03%)**, all diagnostic, **zero executed**"),
 ("15","Path walk (sidecar, separate asset)","`CQ_TRUE_UTC_S0R0_ORDERED_PATH_SIDECAR_V1`; derived in `w0_build_working_set_v2.py`","`mfe_r`, `mae_r`, `which_came_first`, `bars_to_*`, `r_at_bar_*`","120 M1 bars max = **2h hard cap**; first touch target 24.40% / stop 50.60% / **neither 25.01%**")]
for a,b,c,d,e in ST: w(f"| {a} | {b} | {c} | {d} | {e} |")
w("")
w("**A deeper 596-line walkthrough already exists** at")
w("`research/operations/wave19_broad_forensic_2026_08_01/cartographer/DECISION_CYCLE_MAP.md` (launch chain,")
w("`evaluate_candidate_v4` at `v4_timewarp:67389`, `materialize_scheduler_window` at `:78014`,")
w("`allocate_decision_window` at `scheduler:27866`, `finalize_scheduler_risk_admitted_selection` at `:44810`,")
w("`simulate_order` at `:85822`). **This table is the index; that file is the manual.** Read it before")
w("proposing any change to a stage.")
w("")
w("### 5.1 Where the funnel actually loses candidates")
w("")
w("| after stage | survivors | lost | cumulative survival |")
w("|---|---:|---:|---:|")
for a,b,c,d in [("generated","27,658","—","100.00%"),("cost packet PASSED","7,210","20,448","26.07%"),
  ("scheduler materialized","4,095","3,115","14.81%"),("reached `new_position`","4,512","—","16.31%"),
  ("selector said `trade`","21","—","0.08%"),("actually executed","**0**","—","**0.00%**")]:
    w(f"| {a} | {b} | {c} | {d} |")
w("")
w("`new_position` (4,512) exceeds `scheduler_option_materialized` (4,095), so the two are not nested — the")
w("lifecycle action is written on a different branch from the scheduler status. Do not build a strict funnel")
w("out of these two columns.")
w("")
w("---")
w("")
w("## 6. PROVENANCE")
w("")
w("| receipt | what it holds |")
w("|---|---|")
for a,b in [("`w0_DICTIONARY.json`","machine-readable twin of this file: every field's profile, curated meaning, source line, trust class and flags"),
 ("`w0_POOL_PROFILE.json`","per-field dtype / null rate / cardinality / min / max / mean / median / p05 / p95 / top-6"),
 ("`w0_DICT_ENUMS.json`","full value distributions for all 27 categorical and low-cardinality fields"),
 ("`w0_DICT_COSTGATE.json`","the two-limb cost-gate decomposition (§0.2)"),
 ("`w0_DICT_OVERCHARGE.json`","pass-rate sweep over spread divisors 1x .. infinity (§0.2)"),
 ("`w0_DICT_IDENTITIES.json`","the exact-duplicate verification and the Jan/Feb schema diff"),
 ("`w0_DICT_SRCTRACE.json`","every field's writer/reader sites across all 677 files in `src/`"),
 ("`w0_DICT_ASSETS.json`","measured row counts and byte sizes for every pool and path asset"),
 ("`w0_dictionary_meta.py`","the curated meanings/flags table (editable source of §1)"),
 ("`w0_dictionary_build.py`","this generator"),
 ("`w0_dictionary_trace.py`","the `src/` tracer")]:
    w(f"| {a} | {b} |")
w("")
w("Upstream, not re-derived here: `w0_RESULT.md` (W0-F1..F4), `w0_WORKING_SET_README.md`,")
w("`w0_WORKING_SET_BUILD_V2.json` (31/31 validations).")
w("")
open(os.path.join(D,"w0_DATA_DICTIONARY.md"),"w").write("\n".join(L)+"\n")

# JSON twin
out={"schema":"gtos.wave19.w0_dictionary.v1","generated":datetime.date.today().isoformat(),
 "pool":{"path":"docs/audits/fable5-vision-audit-20260725/phase16/receipts/pools/CJ_RECLOCKED_S0R0_POOL_V1.jsonl.gz",
   "rows":N,"fields":78,"raw_ledger_rows":153425,"pool_share_of_ledger":round(N/153425,6),
   "population":"100% counterfactual; zero executed trades; filter v4_timewarp:28130-28140"},
 "trust_legend":META.TRUST_LEGEND,"trust_counts":dict(tc),
 "cost_gate":{"max_spread_r":0.10,"max_total_cost_r":0.15,
   "config":"config/agent_config.yaml:715-716","source":"broker_net_cost_engine.py:846-928",
   "rows_spread_over":17258,"rows_total_over":20074,"refused":20448,"passed":7210,
   "decomposition":COSTGATE["joint"],"overcharge_sweep":OVER["ks"]},
 "identities":IDENT["ident"],"feb_only_fields":IDENT["feb_only_fields"],
 "fields":{k:{"group":META.M[k][0],"meaning":META.M[k][1],"source":META.M[k][2],
   "trust":META.M[k][3],"flags":META.M[k][4],"profile":F[k],
   "enum":ENUMS.get(k,{}).get("top")} for k in F},
 "assets":ASSETS}
json.dump(out,open(os.path.join(D,"w0_DICTIONARY.json"),"w"),indent=1)
for src,dst in [("enums.json","w0_DICT_ENUMS.json"),("costgate.json","w0_DICT_COSTGATE.json"),
  ("overcharge.json","w0_DICT_OVERCHARGE.json"),("ident.json","w0_DICT_IDENTITIES.json"),
  ("trace.json","w0_DICT_SRCTRACE.json"),("assets.json","w0_DICT_ASSETS.json")]:
    json.dump(json.load(open(T+"/"+src)),open(os.path.join(D,dst),"w"),indent=1)
print("MD lines",len(L),"fields",len(out["fields"]))
