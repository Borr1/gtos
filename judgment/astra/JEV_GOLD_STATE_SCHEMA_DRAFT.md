# Gold state schema draft — closed object for XAUUSD candidate scoring

**Date:** 2026-09-17  
**Status:** Draft of a **closed state object**. Not a live client. Not a NEWS invent.  
**Symbol:** `XAUUSD` first. Same shape should extend to `XAGUSD` / metals crosses later without changing question IDs.  
**Clock:** broker wall = `America/New_York + 7h` (`src/utils/broker_clock.py`). Never invent EET+3.  
**Account surface for any LIVE/Challenge shadow row:** login `0`, pass `$110k`, magic `0`, ns `operator`. Verification `0` quarantined.

This is the object Jev sees. Pair with [`JEV_ALIVE_ORGANISM_20260917.md`](JEV_ALIVE_ORGANISM_20260917.md) (which gate asks which question) and [`JEV_WHAT_IT_IS_RESEARCH.md`](JEV_WHAT_IT_IS_RESEARCH.md) (why primitives look like this).

Owner law this draft implements: *if a trade was wrong, a state was missing or a calculation was wrong.* The schema’s job is to make **missing** visible (`completeness.*`) so Jev can Noul `state_sufficient` instead of guessing.

---

## 0. Closed-object rules

1. **One JSON object per candidate (or per historical bar-fire).** Named fields. Path-reference in questions: `` `geometry.stop_atr` ``, `` `sessions.broker_hour` ``, `` `news.minutes_to_nearest_high` ``.
2. **No realized PnL on LIVE / as-of-open STUDY.** No `broker_net`, no later-won flag, no `exit_class` of a close that has not happened, no MFE/MAE. Those are **targets** on a later close-label row (composer `EXPOST_KEYS` spirit — leftover-ship `composer.py`, cited in V2 §2.9).
3. **Code fills facts. Jev never classifies a family the writer already knows.** `sleeve`, `family_class`, `ac60`, `plan_r` are numbers/enums from generators.
4. **News is fail-closed.** `news.spine_empty == true` means “we do not have a calendar,” **not** “there is no HIGH.” Do not hand-write FOMC/NFP/BOJ rows. Do not copy chat summaries into `news.events[]`.
5. **Empty ≠ zero.** A missing PDH is `levels.prior_day_high = null` + `completeness.levels = false`. A computed 0.0 distance is a real number.
6. **Clock block is mandatory.** `clock.as_of_utc` + `clock.broker_epoch` + `clock.rule`. Historical rows use the bar’s close, converted with `broker_clock.broker_epoch_to_utc`. Never trust a `_utc` column name without a `.timebase.json`.
7. **Schema version is pinned** so a 2-week slice and a 10-month slice are comparable.

```
schema: gtos.judgment.gold_state.v0
```

---

## 1. The object

Types below are TypeScript-ish for humans. A JSON Schema can be generated from this draft once Fable implements the assembler; do not treat this file as an already-wired `jev_admit_*` replacement. `jev_admit_v2` remains the F5 slate admit envelope. This object is the **XAUUSD body** that envelope (or a W7 intent envelope) should carry under `state.gold` / `state.market`.

```ts
type GoldStateV0 = {
  schema: "gtos.judgment.gold_state.v0";
  as_of_clock: "live_intent" | "as_of_open_study" | "as_of_close_illegal_for_live";

  identity: {
    candidate_id: string;            // required for LIVE; historical lab may use bar_iso|sleeve|side
    symbol: "XAUUSD";
    side: "long" | "short";
    sleeve: string;                  // metals_core | metals_softband | dsp_spring_* | …
    family_class:
      | "house_keep"
      | "house_hard_off"
      | "w7_metals"
      | "study"
      | "starve_watch"
      | "other_tagged"
      | "unknown";
    origin_organism: "w7_ultimate_book" | "f5_challenge" | "historical_lab";
    decision_day: string;            // YYYY-MM-DD in the clock the sleeve uses
    decision_bar_iso: string;
  };

  clock: {
    as_of_utc: string;               // ISO-8601
    broker_epoch: number | null;
    rule: "new_york_plus_7";
    weekday: 0 | 1 | 2 | 3 | 4 | 5 | 6; // Monday=0 or whatever the assembler documents — pick one and pin it
    weekday_name: "Mon" | "Tue" | "Wed" | "Thu" | "Fri" | "Sat" | "Sun";
    is_friday: boolean;
  };

  sessions: {
    broker_hour: number | null;      // server-local hour; metals A8 uses this (metals.py _a8_features)
    utc_hour: number | null;
    named:
      | "asia"
      | "london"
      | "ny"
      | "dead_21_00z"
      | "friday_cutoff"
      | "weekend"
      | "unknown";
    bars_since_session_open: number | null;   // wave21 PREDECISION_FEATURE_KEYS
    session_open_range_width_atr: number | null;
    // Windows below are LABELS for the named enum — they are NOT invented NEWS.
    // They come from existing session code, not from this draft.
    source:
      | "metals_a8_server_local"     // metals.py:156-163
      | "wave21_utc_session"         // feature_contract.py utc_session
      | "agent_config_legacy_utc"    // config/agent_config.yaml Asian 00-07 / London 07-09:30
      | "unassembled";
  };

  timeframes: {
    // Compact, leak-free, as-of-bar summaries. Not raw OHLC dumps (token waste).
    // Each TF: last closed bar + a few named distances. Code computes.
    m1?: TfSnap;                     // optional; omit if not assembled
    m5?: TfSnap;
    m15: TfSnap;                     // required for gold lab
    h1?: TfSnap;
    h4: TfSnap;                      // metals_core signal TF
    d1: TfSnap;
  };

  levels: {
    prior_day_high: number | null;
    prior_day_low: number | null;
    prior_week_high: number | null;
    prior_week_low: number | null;
    dist_to_prior_high20_atr: number | null;  // wave21
    dist_to_prior_low20_atr: number | null;
    fvg?: {
      gap_top: number;
      gap_bot: number;
      k_index: number;
      freshness_bars: number;        // metals A8 fvg_freshness_bars
      side: "bull" | "bear";
    } | null;
    sweep_depth_atr: number | null;
    poi?: {
      kind: string;
      age_hours: number | null;
      distance_to_midpoint_atr: number | null;
      distance_to_zone_atr: number | null;
      touch_count: number | null;
      mitigation_status: string | null;
    } | null;
    source: "wave21" | "metals_fvg" | "path_scaling_v2" | "unassembled";
  };

  news: {
    spine_id: string | null;         // hash of the exact calendar bytes used
    spine_extracted_utc: string | null;
    spine_empty: boolean;            // true → event questions ABSTAIN
    source:
      | "w7_news_filter_json"        // data/news_calendar.json via news_calendar.py
      | "w7_news_filter_csv"
      | "w7_news_filter_mt5"
      | "f5_official_high_spine"     // leftover-ship gtos.news.official_high_spine.v1 — NOT on this main
      | "unassembled";
    // ONLY events that exist in the named source. Never invented.
    events: Array<{
      datetime_utc: string;
      event: string;
      impact: "HIGH" | "MEDIUM" | "LOW" | string;
      currency: string;              // XAUUSD map on W7 is ["USD"] (news_calendar.py)
      minutes_from_as_of: number;    // signed: negative = already printed
    }>;
    minutes_to_nearest_high: number | null;   // null if spine_empty or no HIGH in source
    high_in_w7_window: boolean | null;        // W7 code window: T-15 .. T+2 (news_filter)
    high_in_f5_window: boolean | null;        // F5 leftover-ship: T-15 .. T+60 — only if that spine is present
    // Config facts so Jev cannot "remember" a different window than code.
    w7_pre_block_minutes: 15 | number;
    w7_post_block_minutes: 2 | number;
    f5_pre_block_minutes: 15 | number | null;
    f5_post_block_minutes: 60 | number | null;
  };

  sleeve_features: {
    // W7 metals (metals.py) — present when origin_organism is w7 or lab-on-metals
    ac60: number | null;
    vol_ratio: number | null;        // atr14 / SMA100(atr) == A8 atr_ratio
    htf_slope_norm: number | null;
    mom_20_atr: number | null;
    fvg_freshness_bars: number | null;
    session_hour: number | null;
    a8_k_of_4_pass: boolean | null;  // code: metals_confluence(); null if features missing
    intra_size: number | null;       // metals_softband only
    // F5 / DSP tags — present when origin is f5; otherwise omit or null
    tag: string | null;
    cluster: string | null;
  };

  geometry: {
    entry: number | null;
    stop: number | null;
    target: number | null;
    stop_dist: number | null;        // price units (W7 TradeIntent)
    target_dist: number | null;
    plan_r: number | null;           // |target-entry| / |entry-stop| — CODE
    stop_atr: number | null;
    target_atr: number | null;       // wave21; known 1.5-vs-2.0 defect — see completeness.geometry_atr_basis
    runner_r: number | null;         // metals _runner_R(vr): 4.0 / 3.0 / 2.5
    order_type: "MARKET" | "LIMIT" | null;
    atr14: number | null;
    trigger_bar_range_atr: number | null;
    trigger_bar_body_atr: number | null;
    compression_ratio_prior_bar: number | null;
    close_position_in_lookback_range: number | null;
  };

  cost: {
    spread_r: number | null;
    spread_r_of_stop: number | null;
    expected_slippage_r: number | null;
    swap_cost_r: number | null;
    commission_r: number | null;
    cost_r: number | null;           // wave21 composite if assembled
    cost_screen_would_refuse: boolean | null;
    source: "tick" | "wave21" | "symbol_class_table" | "unassembled";
  };

  occupancy: {
    symbol_open: boolean | null;
    symbol_pending: boolean | null;
    already_placed_today: boolean | null;     // W7: one unit per (sleeve, symbol, day)
    cluster_placed_today: boolean | null;
    isolated_reentry_legal: boolean | null;   // F5 writer integer; do not ask Jev to invent it
    same_sleeve_orig_stops_utc_day: number | null;
    two_stop_exhausted: boolean | null;
    minutes_since_flat: number | null;
  };

  governor: {
    allow_new: boolean | null;
    cap_mult: number | null;
    reason: string | null;
    realized_today_pct: number | null;  // LIVE book only; omit on historical lab unless simulating a book
    open_risk_pct: number | null;
  };

  surface: {
    us30_off: true;
    hard_off_families: Array<"bleed" | "orb_crypto" | "idxrev" | "xa_huge" | "mx_us30">;
    keep_families: Array<"spring" | "vss">;
    circuit: "2-stop";
    token_digest_matches: boolean | null;     // LIVE only; never store the token
  };

  completeness: {
    clock: boolean;
    sessions: boolean;
    timeframes_m15_h4_d1: boolean;
    levels: boolean;
    news_spine: boolean;             // false if spine_empty OR unassembled
    sleeve_features: boolean;
    geometry: boolean;
    geometry_atr_basis: "intent_price" | "wave21_atr" | "mixed_unverified" | "missing";
    cost: boolean;
    occupancy: boolean;
    state_sufficient_for_live: boolean;  // CODE pre-Noul: identity + geometry + clock + sleeve
    missing_fields: string[];        // dotted paths
  };
};

type TfSnap = {
  tf: "M1" | "M5" | "M15" | "H1" | "H4" | "D1";
  last_close: number;
  last_range: number;
  atr14: number | null;
  close_vs_close_n_atr: number | null;  // n = 8/20/30 depending on TF; document in assembler
  trend: -1 | 0 | 1 | null;             // metals htf_trend on H4; others if computed
  bars_available: number;
  source_path: string;                  // the CSV / pack this snap was built from
};
```

---

## 2. Where each block is assembled — disk only

Do not invent a new gold feed. Assemble from what exists, and mark `unassembled` when it does not.

| Block | On this `main` tree | Not on this tree |
|---|---|---|
| **OHLC M15** | `data/historical/XAUUSD_M15.csv` 2024-04-01 → 2026-04-17 (~48,360); `data/historical_2026/XAUUSD_M15.csv` 2025-10-01 → 2026-04-24 (~13,289); `exports/multi_instrument/XAUUSD_M15.csv` 2024-02-21 → 2026-04-02; Sierra pilot 2025-10-28 → 2026-05-01 | Tick archive `/Users/borr/GTOSActive/vps-ticks-20260726/` (external) |
| **OHLC D1** | `data/historical/XAUUSD_D1.csv` 2023-04-03 → 2026-03-30; `data/historical_2022_2023/XAUUSD_D1.csv` 2022-01-03 → 2024-02-20; `exports/multi_instrument/XAUUSD_D1.csv` **2014-08-20 → 2026-04-02** (longest committed) | — |
| **OHLC H4** | Research-measured 2015-01-02 → 2026-06-11, 17,653 bars — `research/operations/final_moonshot_v4_ultimate_mechanical_edge_2026_06_10/WAVE6_GOLD_SESSIONS_EVENTS_RESULT.json` (result, not a canonical CSV in this checkout) | Rebuild from M15 / D1 if the H4 CSV is absent |
| **Sleeve facts** | `src/components/ultimate_book/sleeves/metals.py` (`ac60`, FVG, A8, `_runner_R`); `admission.py` `_metals_confluence_pass` | F5 DSP tags: leftover-ship `minimal_size.py` |
| **Levels** | wave21 `feature_contract.py` `dist_to_prior_*`, `sweep_depth_atr`, `session_open_range_width_atr`; `scripts/run_raw_ohlc_path_scaling_v2_levels.py` (PDH/PDL/BOS); metals FVG gap | No `judgment/` gold-levels pack |
| **Sessions** | metals A8 server-local hour; wave21 `utc_session`; `broker_clock.py`; `data/historical_2026/*.timebase.json` | `data/sessions/` directory **missing** |
| **News** | `src/components/news_calendar.py` + `config/agent_config.yaml` `news_filter` (15 pre / **2** post, HIGH, XAUUSD→USD); `data/news_calendar.json` **week_of 2026-05-31 only** (2026-06-01→06-05); `data/economic_calendar.csv` same 5 days; `scripts/refresh_economic_calendar.py` is a **staleness monitor**, not a fetch | F5 `official_high_spine` / `NEWS_PROTOCOL` (V2 §8 GAP). **Do not invent a spine to fill the GAP.** |
| **Cost / geometry** | W7 `TradeIntent.stop_dist` / `target_dist`; wave21 `cost_r`, `spread_r`, `stop_distance_atr`, `target_distance_atr`; book `_spread_cost_screen` | Challenge replay has ex-post `sl`/`tp`/`R` — STUDY close only |
| **Occupancy** | W7 `book_owner.py` `already_placed_today`; F5 isolated-reentry integers on leftover-ship | Live slates not in git |

**WAVE6 note (do not over-read):** `WAVE6_GOLD_SESSIONS_EVENTS_RESULT.json` reports that once vol is gated, time/session/day-of-week **added nothing on that mechanical sleeve**. That is a finding about **static session buckets on that generator**, not a kill of Jev session Scores over a *complete* state (news + levels + multi-TF). The gold lab must treat WAVE6 as a **baseline to beat or confirm**, not as a reason to omit `sessions`.

---

## 3. Completeness predicates (code, before the call)

```
LIVE / as_of_open_study is evaluable only if:
  identity.candidate_id and symbol and side and sleeve
  clock.as_of_utc and clock.rule
  geometry.stop_dist or (geometry.entry and geometry.stop)
  completeness.timeframes_m15_h4_d1
  news.spine_empty is a boolean (assembled), not omitted
  no EXPOST keys

If completeness.state_sufficient_for_live is false:
  you MAY still call Jev with Noul state_sufficient (expect ~low)
  you may NOT use other answers for a fire disposition
```

`family_class == "unknown"` is a state defect (V2: replay ticket `292427064`). `state_sufficient` must go low.

---

## 4. Questions that belong on this object

Ask **together** (one request). Instructions must repeat the meaning; IDs are for code only. Reference paths with backticks.

| ID | Primitive | Instructions (intent) | Ignore when |
|---|---|---|---|
| `state_sufficient` | Noul | Do `completeness.missing_fields` and the named blocks contain enough to judge this XAUUSD fire as-of `clock.as_of_utc`? | — |
| `flow_stance` | Choice `with_flow \| against_flow \| no_clear_flow` | Given `timeframes.h4.trend`, `timeframes.d1.*`, `sleeve_features.htf_slope_norm`, `sleeve_features.mom_20_atr`, and `identity.side`, is this fire with the named flow, against it, or is flow unclear? | `state_sufficient` low |
| `flow_alignment` | Score 0–2 | Levels: 0 fighting named HTF/session flow; 1 mixed/rotating; 2 aligned. Use only named fields. | same |
| `session_fitness` | Score 0–2 | 0 dead/Friday-cutoff/wrong hour for this sleeve; 1 ordinary; 2 sleeve’s clean hour. Use `sessions.*` + `clock.is_friday`. | `sessions.source == unassembled` |
| `geometry_vs_tape` | Score 0–2 | 0 stop likely dies in the next 1–2 M15 prints given `geometry.*` + `timeframes.m15`; 1 ordinary house risk; 2 stop/target fit named vol. **Do not** define 1 as “house 1R/6R.” | geometry missing |
| `level_respect` | Score 0–2 | 0 firing through a named opposing PDH/PDL/FVG; 1 no relevant level; 2 holding/reclaiming a named supporting level. | `levels.source == unassembled` |
| `event_proximity` | Noul | Is a **named** HIGH in `news.events` inside the window the **code** uses (`news.high_in_w7_window` or `news.high_in_f5_window`)? | `news.spine_empty` → code skips or expects ~0.5 |
| `calendar_honest` | Noul | Is `news.spine_empty` false and `news.events` non-empty for this as-of? | — (consistency) |
| `cost_hurtful` | Noul | Is `cost.spread_r_of_stop` large enough vs `geometry.plan_r` / stop that this fire is cost-dominated? | cost unassembled |
| `a8_agrees` | Noul | Does `sleeve_features.a8_k_of_4_pass` agree with the named A8 fields (consistency, not a re-vote of the integer gate)? | not a metals sleeve |
| `admit` | Choice `admit \| abstain \| hard_refuse` | Given remaining intelligence (not house integers), would this fire still be scored admit? **Not** “will it profit.” | house_block / not enrolled |

**Do not ask on this LIVE object:** `toxic_remint`, exit_class, “will this hit TP,” flatten, remint, KEEP/OFF.

**Close-label (separate object, EXPOST allowed as targets):** keep V2 §4.3 nouns — `orig_stop | broker_tp | time_stop | breach_flatten | other`. `time_stop` is first-class. Challenge 45 proved the hole.

---

## 5. Example (illustrative shape — not a live ticket, not a NEWS invent)

```json
{
  "schema": "gtos.judgment.gold_state.v0",
  "as_of_clock": "as_of_open_study",
  "identity": {
    "candidate_id": "lab:XAUUSD:H4:2026-04-02T20:00:00Z:metals_core:long",
    "symbol": "XAUUSD",
    "side": "long",
    "sleeve": "metals_core",
    "family_class": "w7_metals",
    "origin_organism": "historical_lab",
    "decision_day": "2026-04-02",
    "decision_bar_iso": "2026-04-02T20:00:00Z"
  },
  "clock": {
    "as_of_utc": "2026-04-02T20:00:00Z",
    "broker_epoch": null,
    "rule": "new_york_plus_7",
    "weekday": 3,
    "weekday_name": "Thu",
    "is_friday": false
  },
  "sessions": {
    "broker_hour": null,
    "utc_hour": 20,
    "named": "unknown",
    "bars_since_session_open": null,
    "session_open_range_width_atr": null,
    "source": "unassembled"
  },
  "news": {
    "spine_id": null,
    "spine_extracted_utc": null,
    "spine_empty": true,
    "source": "unassembled",
    "events": [],
    "minutes_to_nearest_high": null,
    "high_in_w7_window": null,
    "high_in_f5_window": null,
    "w7_pre_block_minutes": 15,
    "w7_post_block_minutes": 2,
    "f5_pre_block_minutes": null,
    "f5_post_block_minutes": null
  },
  "completeness": {
    "clock": true,
    "sessions": false,
    "timeframes_m15_h4_d1": false,
    "levels": false,
    "news_spine": false,
    "sleeve_features": false,
    "geometry": false,
    "geometry_atr_basis": "missing",
    "cost": false,
    "occupancy": false,
    "state_sufficient_for_live": false,
    "missing_fields": [
      "timeframes",
      "levels",
      "news.events",
      "sleeve_features",
      "geometry"
    ]
  }
}
```

A row that looks like this is **legal as a fixture** for `state_sufficient → no`. It is **illegal** as a LIVE admit. The gold lab’s first job is to stop looking like this.

---

## 6. News honesty — the only calendar that exists on this clone

`data/news_calendar.json`:

- `week_of`: **2026-05-31**
- `updated_at`: **2026-06-01T10:20:43Z**
- `source`: ForexFactory weekly export (URL recorded in the file)
- Events: **2026-06-01 → 2026-06-05** HIGH only (ISM, Bailey, AUD GDP, Ueda, ADP, ISM Services, Bullock, CAD employment, NFP cluster)

W7 window math (`news_calendar.py:122-123`):  
`[current − post_block, current + pre_block]` with defaults **15 minutes before, 2 minutes after**.

F5 leftover-ship window (not on this tree): **T−15 .. T+60**. If that spine is not opened, `high_in_f5_window` stays `null` and `f5_*_minutes` stay `null`. **Do not fill them from memory.**

Historical gold slices whose as-of is **not** in 2026-06-01..05 have `spine_empty: true` on this clone until an operator refreshes a real calendar that covers that as-of. The lab still runs: event questions abstain; flow / session / geometry / levels still score.

`scripts/refresh_economic_calendar.py` does **not** fetch. It alerts. An empty refresh is not a spine.

---

## 7. Geometry ATR basis — do not mix silently

CLAUDE / wave-21: the live modelling defect where `target_distance_atr / stop_distance_atr = 1.5` on the feature frame while the order carries **2.0**. The gold object stores `completeness.geometry_atr_basis` so a Score cannot compare a 1.5 feature to a 2.0 order and call it “fit.”

- W7 metals intents: **price** `stop_dist` / `target_dist` (`_runner_R(vr) * sd`). Prefer these for metals lab.
- wave21 funnel rows: ATR-normalized fields. Use when the lab is on funnel candidates, and pin the basis.
- Mixed_unverified: illegal for LIVE.

---

## 8. What Fable implements next (assembler, not a send path)

1. A pure function `assemble_gold_state_v0(...)` in a **default-off** research module (not `book_owner`, not `open_trade`).
2. Unit tests:  
   - missing calendar → `spine_empty true`, `events []`;  
   - EXPOST keys rejected on `live_intent`;  
   - metals A8 fields round-trip from a fixture bar;  
   - `state_sufficient_for_live` false when M15/H4/D1 missing.
3. Emit one JSONL of assembled states for the **2-week** slice (organism lab plan) **before** any TypeSafe call.
4. Only then, with `TYPESAFE_API_KEY` in secrets, fan-out §4 questions. Log under `judgment/live/jev_sidecar/` or `judgment/astra/lab/gold/`.

No secrets in the JSONL. No broker mutation. No invented HIGH.
