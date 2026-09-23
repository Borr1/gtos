# HIST-PROVE PLAN — news_join honesty (Challenge tape)

**session:** `11_host_events_news_join_honesty`  
**as_of_ict:** `2026-09-21T06:12:00+07:00`  
**gate:** no `GTOS_JEV_NEWS_JOIN_APPLY=1` until this plan produces a PASS receipt  
**place:** false this session · owner place path OPEN only after later prove

---

## 0. Module_ATR honesty (no invented ATR / regime)

| rule | how this plan obeys |
|---|---|
| Do **not** invent ATR | If `gold_state.geometry.atr14` from Challenge M15 snap is present, may cite it as **named**. Else `geometry_atr_basis=missing` / `intent_price` / `wave21_atr` as already stamped. Never synthesize ATR. |
| Do **not** merge R universes | Challenge hist uses **deals_since** R from `entry/exit/stop_dist` (named on tape). Module_ATR blotter is a **third lens** (`R_ATR`, `lens=Module_ATR`). |
| Module_ATR blotter path (found) | `/workspace/gtos/close_loop/war_room_20260920/blotter_Module_ATR_XAUUSD_dsp_three_fresh_lower_lows.jsonl` (5.8 MB). **Out of news_join scoring.** Do not add Module_ATR sumR to Challenge news counterfactuals. |
| Do **not** invent regime_tag | `regime_tag` stays PENDING / named from session 07. News_join hist does not fill regime. |
| Dig_3R / Edge_ATR / Module_ATR | Keep separate. Gap-inventory do-not: merge Dig3R Module_ATR lenses. |

If a row lacks `stop_dist`, **R is STATE_MISSING** for that row — skip it from sumR, do not impute ATR-R.

---

## 1. Challenge tapes (found — not invented)

| tape | path | n / facts |
|---|---|---|
| Host writer events | `_pr41_land/.../challenge_shadow_20260917/events_since_20260915.jsonl` | 7729 lines. t15=3337 t60=3337. READ=**0**. NOT_READ=3244 UNKNOWN=93. |
| Deals | `.../deals_since_20260909.jsonl` | **n=47** positions, 46 closed, 1 open. Named `stop_dist`, `cost_R`, `profit`. |
| Deals summary | `.../deals_summary.md` | W/L **6/40**; net USD **−4487.73** |
| Shadow pack | `.../shadow.jsonl` | **n=97** (open 1, slate 40, slate_skip 10, deal_close 46). Wave M: spine_empty false 97/97; calendar_honest false 10 / true 87. |
| HIGH spine | `data/news/f5_high_calendar_host_20260916.json` | 13 events, sha256 `5258c3ba…` |
| Slate fold | `slate_20260917T104105Z_bddc8ff9fad4a254.json` | f5_high_calendar 13 kept; official_high_spine 0; news_brief 0 |
| Live host `events.jsonl` | `shadow_logs/f5_minimal/operator/events.jsonl` | **MISSING on this box** |
| April `data/historical*` | — | **Forbidden** as Challenge-true |

Login `0` / ns `operator` only. Do not use redacted_account / W7 books.

---

## 2. Baseline metrics (this seat, deals tape)

Computed from named `entry/exit/stop_dist` on 46 closed deals (**not** Module_ATR `R_ATR`):

| metric | value |
|---|---|
| n (positions) | 47 |
| n closed with R | 46 |
| **sumR** | **−28.228** |
| **maxDD_R** (sequential) | **−33.637** |
| minR / maxR | −1.290 / +3.409 |
| fire rate | 47 fires on 2026-09-09..17 Challenge window (as pulled 2026-09-17T10:40:57Z) |
| USD net (summary) | −4487.73 |

Wave M shadow pack (labels, not R):

| metric | value |
|---|---|
| n | 97 |
| n_news_empty | **0** |
| calendar_honest | false 10 / true 87 |
| FLUID-NWS-005 spine_empty_honesty | false 97/97 (constant — not proved) |

These numbers are the **control**. Any news APPLY that changes fire rate must beat them on the **same** deals + same R definition.

---

## 3. Counterfactuals (shadow only)

Replay `scripts/jev_challenge_shadow.py` over `deals_since` + `events_since` + `f5_high_calendar`, with `GTOS_JEV_NEWS_JOIN_APPLY=0`.

For each closed deal as-of (`open_time_utc`):

1. `news_join = assemble_news_join(as_of, live=False)` using lab `DEFAULT_EVENTS` (research) **labelled as lab**, not live.
2. Stamp: `spine_empty`, `high_in_f5_window`, `calendar_honest` (Wave M rule), `host_news_inventory_status`, `news_join==STATE_MISSING?`.
3. Named Challenge R from stop_dist. If stop_dist missing → R STATE_MISSING, exclude from sumR.

**Buckets (do not invent empty as-ofs):**

| bucket | definition | expected on this tape |
|---|---|---|
| A JSON-only honest | no writer row within 6h, spine covering | ~87 shadow rows; Sep 9–14 deals |
| B writer unread | host source writer and status ≠ READ | ~10 shadow rows; Sep 15+ |
| C in F5 window | `high_in_f5_window=true` | measure; do not guess |
| D STATE_MISSING | no spine files and no writer | **should be 0** on this pack (spine present). If 0, do not fabricate. |

**Counterfactual policies (LABEL vs fire-rate):**

| id | policy | allowed now |
|---|---|---|
| P0 | current envelope: labels only; writer always prints | **control** |
| P1 | LABEL only (G1+G3): stamp calendar_honest; **no admit change** | shadow PASS if stamps match Wave M 10/87 |
| P2 | admit STAND when `event_proximity` true (F5 window) | **hist-only**. Compare sumR/DD/fire-rate vs P0 |
| P3 | admit STAND when `calendar_honest=false` | **hist-only**. Likely kills Sep 15+ (writer unread). Must not be APPLY without prove |
| P4 | size tilt from `event_join` (CA path) | belongs to session 06; here report-only |

P2/P3/P4 **must not** land APPLY from this session.

---

## 4. Pass bars (gate to APPLY)

News-join **honesty** (G1/G3/COMPLETE_STATE field) may Chair-land as **LABEL** when:

- `invented_news_protocol=false` on every row
- live resolve never swaps lab tape (`test_news_inventory_live` already)
- Wave M calendar_honest split reproduces (false on writer-unread, true on JSON-only)
- `spine_empty` stays false on covered Challenge as-ofs (do not invert)
- `news_join` is object on this pack (spine join real); STATE_MISSING only when both joins absent
- Jev dark → skip POST, code honesty unchanged, fire rate unchanged

News-join **fire-rate** (`GTOS_JEV_NEWS_JOIN_APPLY=1` or event_proximity as admit refuse) only if **all** hold:

| bar | threshold |
|---|---|
| n | ≥ 46 closed Challenge deals **or** a later longer pull of the **same** login/ns (do not pad with April) |
| sumR vs P0 | **strictly greater** (less negative) on same R definition |
| maxDD_R | not worse than P0 by > 0.5R without a Chair-named exception |
| fire rate | report n_fired / n_candidates; any drop must be explained by named HIGH window, not invented empty |
| Module_ATR | **not used** in the comparison |
| scoped symbols | if scoped, XAU and/or GBPJPY affinity only — do not silently globalize |
| place | still default-off until a **separate** place hist (session 14). This family is news honesty |

FLUID-NWS-005 APPLY is **blocked** until a real as-of sits outside 10d of a real spine event (G10). Wait. Do not invent that empty.

G2 (`inventory_status=READ`) is **Chair/host writer**, not a hist fixture. Hist may remain READ=0. Honesty PASS does not require inventing READ.

---

## 5. Replay command sketch (observe only)

```
cd /workspace/gtos/close_loop/war_room_20260920/_pr41_land/ai-trading-agent
GTOS_JEV_A1_CALL=1
GTOS_JEV_MAX_CALLS=500000
GTOS_JEV_NEWS_JOIN_SHADOW=1
GTOS_JEV_NEWS_JOIN_APPLY=0
GTOS_JEV_A1_LOG=1
# research default events (lab). Do NOT set live=True against missing events.jsonl.
python scripts/jev_challenge_shadow.py \
  --events judgment/astra/lab/challenge_shadow_20260917/events_since_20260915.jsonl
```

Do not `order_send`. Do not set `GTOS_JEV_SLEEVE_SELECT_APPLY=1`.

If TypeSafe key absent: still run code-only compose (`evaluate` skip). Honesty is `_calendar_honest`, not Jev.

---

## 6. What is MISSING (honest)

| item | status |
|---|---|
| Live VPS `events.jsonl` | MISSING on box |
| `inventory_status=READ` on Challenge tape | **0** |
| Uncovered Challenge as-of for NWS-005 | none on n=97 |
| NEWS_PROTOCOL organism file | MISSING (staged specs elsewhere, not live) |
| leftover-ship compose on this branch | MISSING |
| official_high_spine / news_brief events | 0 kept |
| Module_ATR as Challenge news R | **must stay unused** |
| Chair APPLY of G1 on VPS | not claimed |
| Longer Challenge tape after 2026-09-17 | not on this seat |

---

## 7. Chair gate (next)

1. Land G1 copy on Challenge if VPS tree still drops `extra=` (PR41 already has it).
2. Point `GTOS_JEV_HOST_EVENTS` at real writer tape when present.
3. Land G3 prompt (Jev matches APPLIED label).
4. Land `assemble_news_join` into COMPLETE_STATE (with session 10).
5. Run P1 LABEL replay → honesty receipt.
6. **Only then** consider P2 window-STAND hist. If P2 sumR/DD/fire-rate does not beat P0, **keep APPLY=0**.
7. G2 READ is host writer work. This session does not invent it.
