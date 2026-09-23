# `LIVE_DIVERGENCE_ROW_SCHEMA.md` — the live-trade row set

**Owner:** Session E (`phase1/w7-forensics`), Phase 1 item 2 / Gate G1b.
**Consumer:** Session F (`phase1/divergence-matrix`), Phase 1 item 4.
**Pushed:** 2026-07-26. Session F had not pushed a schema at the time this was written
(`git ls-remote --heads origin` showed no `phase1/divergence-matrix`), so per the wave tiebreak rule
this schema is the one to adopt.

**Status of this document:** the schema is frozen at v1 as published. Fields may be *added* (F should
tolerate unknown keys); existing field names and meanings will not change under F's feet. Any field
whose value could not be measured is emitted as `null` **plus** a sibling `*_status` code — never as a
zero, and never omitted. A missing key means a schema mismatch; a `null` means measured-as-unavailable.

---

## 1. What one row is

**One row = one closed broker position on one live account.** Not one order, not one deal, not one
GTOS candidate. The position (`position_id`) is the only identifier that exists on both sides of every
join available in this window, and it is the unit at which realized money is defined.

Rationale, and it is a constraint rather than a preference: the GTOS-side execution ledgers
(`execution_manager_v4_decisions`, `broker_order_lifecycle_capture_v4`, `slippage_runtime`) **died on
2026-07-02** (finding V3) and the lifecycle capture is **request-side only, 594 rows, no `order_result`**
(finding V2). Broker truth — `history_deals_get` + `history_orders_get` from the VPS export's
`09_mt5_api/` — is therefore the *primary* source for this row set, and the GTOS ledgers are joined in
as *optional enrichment*. A row exists because the broker says a position existed. Rows are never
created from GTOS-side records alone.

Row counts, per-account and per-family, live in the artifact's own manifest
(`LIVE_TRADE_ROWS_MANIFEST.json`) and are deliberately **not** restated here, so the two cannot drift
apart. An earlier revision of this document quoted counts before the generator had been run; they were
guesses and have been removed. Read the manifest.

The W7 era runs **2026-06-15 → 2026-07-02** — note that start date. It is three days earlier than the
"06-18" the audit text uses, because 06-18 is when the *candidate* and *market-expansion* books were
switched on, not when the book went live.

---

## 2. Files

| file | content |
|---|---|
| `docs/audits/fable5-vision-audit-20260725/phase1/w7_forensics/LIVE_TRADE_ROWS.jsonl` | one JSON object per line, one per closed position |
| `docs/audits/fable5-vision-audit-20260725/phase1/w7_forensics/LIVE_TRADE_ROWS_MANIFEST.json` | provenance, counts, reconciliation residual, coverage fractions |
| `scripts/w7_live_forensics.py` | the generator. Deterministic; re-run reproduces the rows byte-for-byte |

JSONL, UTF-8, no BOM, keys sorted, one object per line. (The VPS export's own JSONL files carry a
**UTF-8 BOM** because they were written by Windows PowerShell — read them with `encoding="utf-8-sig"`.
This artifact does not.)

---

## 3. Fields

### 3.1 Identity

| field | type | meaning |
|---|---|---|
| `schema_version` | str | `gtos.live_divergence_row.v1` |
| `account` | str | `ftmo` \| `redacted_account` |
| `account_login` | int | MT5 login. `531325516` (FTMO) / `0` (redacted_account) |
| `broker_server` | str | MT5 `account_info().server`, verbatim. The key `broker_clock.resolve_rule` takes |
| `position_id` | int | broker position id — **the row key**, unique within `account` |
| `entry_deal_ticket` | int | ticket of the opening deal |
| `exit_deal_tickets` | list[int] | tickets of every closing deal (partial closes produce more than one) |
| `entry_order_ticket` | int \| null | opening order ticket, from `history_orders_get` |
| `magic` | int | MT5 magic. `20260401` for the modern stack; see §5 |

### 3.2 Sleeve attribution — axis (a)

The broker deal `comment` carries the sleeve tag. This is the single most important discovery behind
this schema: **sleeve identity survives in broker truth**, so axis (a) does not depend on the dead
GTOS ledgers.

| field | type | meaning |
|---|---|---|
| `comment_raw` | str | the opening deal's `comment`, verbatim and untruncated-as-stored |
| `sleeve_tag` | str \| null | the part after `W7:`, e.g. `idxrev`. `null` for non-W7 rows |
| `sleeve_id` | str \| null | `sleeve_tag` resolved to its full config identifier, e.g. `metal_session` → `metal_session_reversion` |
| `sleeve_resolution` | str | `exact` \| `prefix_unique` \| `prefix_ambiguous` \| `unresolved` |
| `sleeve_family` | str | see the closed vocabulary below |
| `stack_era` | str | `w7_book` \| `pre_w7_fleet` \| `manual` \| `smoke` \| `unknown` |

**MT5 truncates the order comment to 16 characters.** `W7:` + 13 characters of sleeve name. So
`W7:kz_london_cry` is `kz_london_crypto_low` and `W7:metal_session` is `metal_session_reversion`.
`sleeve_resolution` records how the full name was recovered: `exact` when the stored comment is the
whole name, `prefix_unique` when exactly one configured sleeve has that 13-character prefix,
`prefix_ambiguous` when more than one does (then `sleeve_id` is `null` and the candidates are listed in
`sleeve_candidates`). No row silently guesses.

`sleeve_family` vocabulary — closed set, derived from `config/agent_config.yaml:1272-1294`:

- `core8` — the deployed core-8 book. `ultimate_book_include_clean3: false` dropped the three
  selection-glow sleeves on 2026-06-15; the config says "Live book = the core 8 sleeves"
- `candidate` — the nine-sleeve allowlist in `ultimate_book_candidate_book_sleeves`, switched **ON
  2026-06-18**
- `market_expansion` — `ultimate_book_include_market_expansion_book: true`, also **ON 2026-06-18**,
  allowlist resolved by the named policy `positive_weighted12_after_swap`
- `pre_w7_fleet` — the stack that traded before 2026-06-15 (`GoldAgent_*` comments). Present on both
  accounts and **must be excluded from any W7 denominator**
- `manual` — owner/operator actions (`owner_flatten`, `GTOS_EMERGENCY_C*`)
- `smoke` — connectivity tests (`FN_SMOKE`, `smoke_force_clos*`, `safety_trade_*`)
- `unattributed` — a W7-era position whose comment does not resolve to any configured sleeve

`stack_era` vocabulary, closed:  `w7_book` · `pre_w7_fleet` · `manual_mobile` · `manual` · `smoke` ·
`pre_w7_untagged` · `post_w7_broad` · `w7_window_untagged` · `unknown`.

**`manual_mobile` matters more than its row count suggests.** Three positions across both accounts were
placed **by hand from the MT5 phone app**, identified by `magic == 0` *and* opening deal `reason == 1`
(`DEAL_REASON_MOBILE`) *and* an empty comment *and* no stop at entry — a 1:1 correspondence, not a
single-field inference. Two of them are worth **+13,166.69** and are the only reason the FTMO account
closes positive. Treating them as system trades makes the W7 book look profitable when it lost 2.55 %.

**`magic` does not separate the eras — both carry `20260401`.** See §5.

`sleeve_family` is the axis-(a) partition. Rows tagged `pre_w7_fleet`, `manual` or `smoke` are **in the
file** — dropping them silently is exactly how the redacted_account denominator became a range — but carry
`in_w7_denominator: false`.

### 3.3 Instrument and side

| field | type | meaning |
|---|---|---|
| `broker_symbol` | str | the broker's own symbol string, verbatim (`US100.cash` on FTMO, `NDX100` on redacted_account) |
| `canonical_symbol` | str \| null | GTOS canonical name, for cross-broker and replay joins |
| `symbol_map_status` | str | `mapped` \| `unmapped` |
| `side` | str | `long` \| `short`, from the opening deal `type` (0=buy→long, 1=sell→short) |
| `volume` | float | opening volume in lots |
| `volume_closed` | float | total closed volume; `< volume` means a partial close is unaccounted |
| `trade_contract_size` | float \| null | the **broker's own** value for this symbol |
| `contract_size_cross_broker_equal` | bool \| null | false on 18 of 19 shared symbols (finding V4) — axis (d)'s mechanism |

`trade_contract_size` is per-broker on purpose. Finding V4 measured that 18 of 19 shared symbols
disagree between the two brokers, so any cross-broker comparison that assumes a shared contract size is
wrong for the indices. Sizing arithmetic must use the row's own value.

### 3.4 Time — read §4 before using any of these

| field | type | meaning |
|---|---|---|
| `entry_time_broker` | str | opening deal time as broker **server wall clock**, ISO-8601 **naive** (no offset) |
| `entry_time_utc` | str | the same instant in true UTC, via `broker_clock.broker_epoch_to_utc` |
| `exit_time_broker` | str | last closing deal, broker wall clock, naive |
| `exit_time_utc` | str | the same instant in true UTC |
| `holding_seconds` | int | `exit_time_utc − entry_time_utc` |
| `day_key_utc` | str | `YYYY-MM-DD` of `entry_time_utc`. What `decision_day_of` uses |
| `day_key_broker_server` | str | `YYYY-MM-DD` of `entry_time_broker`. redacted_account's P&L day |
| `day_key_ftmo_reset` | str | `YYYY-MM-DD` of the entry in **CE(S)T**. FTMO's P&L day |
| `broker_clock_offset_hours` | float | the resolved offset at this instant, e.g. `3.0` |
| `broker_clock_rule` | str | `new_york_plus_7` |

**Three day keys, deliberately.** The three disagree, they disagree by account, and collapsing them is
the defect B56/B58 repaired. FTMO's daily-loss window resets at **00:00 CE(S)T**; redacted_account's at
**00:00 server time**; `decision_day_of` is **UTC**. Any consumer aggregating P&L per day must state
which key it used. For FTMO-vs-redacted_account comparison on identical signals (axis (d)) use
`day_key_utc` — it is the only key that means the same thing on both accounts.

### 3.5 Economics — the reconciling core

| field | type | meaning |
|---|---|---|
| `entry_price` | float | opening deal price |
| `exit_price_vwap` | float | volume-weighted mean of closing deal prices |
| `gross_profit` | float | Σ `profit` over the position's deals, account currency (USD) |
| `commission` | float | Σ `commission` |
| `swap` | float | Σ `swap` |
| `fee` | float | Σ `fee` |
| `realized_net` | float | `gross_profit + commission + swap + fee`. **The reconciling quantity** |
| `pct_of_initial_balance` | float | `realized_net / 100000.0`. Both accounts are 100k challenges |

Sign convention: `commission`, `swap` and `fee` are stored **as the broker signs them** — negative when
they cost money. `realized_net` is therefore a plain sum, not a subtraction. Σ `realized_net` over all
rows **plus** the initial-balance deal equals the account's closing balance exactly; the residual is
published in the manifest and is the row set's own correctness proof. Do not reconstruct
`realized_net` from the other four fields with a different sign convention.

### 3.6 Risk and R — axis (b)

| field | type | meaning |
|---|---|---|
| `sl_price` | float \| null | stop-loss on the opening order, from `history_orders_get` |
| `tp_price` | float \| null | take-profit on the opening order |
| `risk_distance_price` | float \| null | `abs(entry_price − sl_price)` |
| `usd_per_price_unit_per_lot` | float \| null | money per one unit of price per lot — see below |
| `r_money_basis` | str | `solved_from_realized_pnl` \| `symbol_spec_tick_value` \| `unavailable` |
| `risk_at_entry_usd` | float \| null | `risk_distance_price × volume × usd_per_price_unit_per_lot` |
| `risk_pct_of_balance` | float \| null | `risk_at_entry_usd / 100000.0` — the **realized** risk, per trade |
| `realized_r` | float \| null | `realized_net / risk_at_entry_usd` — **net of cost** |
| `gross_r` | float \| null | `gross_profit / risk_at_entry_usd` — **price only** |
| `cost_r` | float \| null | `(commission + swap + fee) / risk_at_entry_usd` |
| `r_basis` | str | `broker_order_sl` \| `unavailable` |
| `sleeve_confidence` | float \| null | the sizer's multiplier — see the dial warning below |

`realized_r` is computed **from broker truth only** — realized net over the risk the broker itself
recorded on the order. It deliberately uses no GTOS-side intended-risk figure, because those are what is
under audit.

**Report `gross_r` and `cost_r` next to `realized_r`, always.** On this window the median stop-out is
−1.0691 R *net* but −1.0036 R *gross* — the fill at the stop is clean and the entire excess over a
modelled −1.00 R is commission and swap. Quoting only the net figure invites reading a cost as slippage,
which is a different defect with a different fix.

**`usd_per_price_unit_per_lot` is solved from each position's own realized P&L**, as
`profit / ((exit − entry) × direction × volume)`, falling back to the symbol spec's
`trade_tick_value / trade_tick_size`. This is not fastidiousness: **redacted_account quantises
`trade_tick_value` to 2 decimals**, making tv/ts wrong by **+5.5 % on GER30, +5.1 % on UK100 and −1.7 %
on JP225** — provable inside redacted_account's own file, since its GER30 spec gives 12.0000 where 10 × its own
EURUSD bid gives 11.3701. FTMO does not quantise. The solved factor equals tv/ts exactly for every
USD-profit symbol on both brokers and is the more accurate of the two elsewhere. **Do not size or
compute R from redacted_account's `trade_tick_value`.**

> ### The dial warning — read before comparing any risk field to 2.00 %
>
> `ultimate_book_profile: clean3_w7_ceiling_nom2p00` sets `base_risk_per_unit = 0.020`. **That is not
> the risk any unit expresses.** `src/components/ultimate_book/admission.py:1170-1171` is
> `unit_risk = base_risk_per_unit * conf * derisk_mult`, then `per_trade = unit_risk / n`, and the
> docstring at `:1038-1040` states the invariant: *"the correlated unit's worst-case simultaneous stop =
> base_risk_per_unit \* conf"*.
>
> So the comparator is **`0.020 × sleeve_confidence` per correlated unit**, and `0.020 × conf / n` per
> trade — never `0.020` against a single trade. An earlier revision of this schema's own receipt made
> exactly that error and reported a nonexistent 10–15× under-sizing defect. `sleeve_confidence` is on
> every row so the correct comparison is always available.

Every one of these is `null`-able with `r_basis: "unavailable"`. A position closed without a stop, or
whose order record is missing, has no R and says so.

### 3.7 Execution friction — axis (c), and it is partial by construction

| field | type | meaning |
|---|---|---|
| `entry_slippage_price` | float \| null | filled entry vs the order's requested price |
| `entry_slippage_r` | float \| null | the same, in R |
| `spread_at_entry` | float \| null | from the tick export, where the window is covered |
| `open_reason` | str | opening deal `reason`. `expert` for every book trade; `mobile` marks a hand trade |
| `close_reason` | str | the **last** closing deal's reason |
| `close_reasons_all` | list[str] | every distinct closing reason on the position |
| `hand_closed` | bool | **true if any close was `mobile`/`web`/`client`** — a human exit, not the sleeve's |

**`hand_closed` is load-bearing for any per-sleeve R claim.** One W7 position (FTMO 160425965, BTCUSD,
`kz_london_crypto_low`) was closed by hand for +304.37, which is **more than that sleeve's entire
result**: the sleeve is +258.79 with it and **−45.58** without. A hand exit's outcome is a human
decision, not the sleeve's edge. `MT5 ENUM_DEAL_REASON` is `CLIENT=0, MOBILE=1, WEB=2, EXPERT=3, SL=4,
TP=5` — getting slots 1/2/3 wrong silently relabels every EA close as a browser close, which is how this
hand exit stayed hidden through two drafts.
| `execution_ledger_covered` | bool | is this position inside the days where the GTOS execution ledgers were alive? |
| `execution_ledger_join_status` | str | `joined` \| `no_gtos_row` \| `ledger_dead_for_this_date` |
| `tick_coverage_status` | str | `covered` \| `outside_tick_export_window` \| `symbol_not_exported` |

**Axis (c) is partial and the fields say where.** The GTOS execution ledgers stopped on 2026-07-02 and
the lifecycle capture never recorded a fill, so slippage from GTOS records exists for only part of the
window. The tick export covers **2026-06-18 → 07-24**, which begins *three days after* the W7 window
opens on 06-15 — so tick-derived spread is unavailable for 06-15..06-17 by construction.
`tick_coverage_status` and `execution_ledger_join_status` carry that per row rather than leaving a
consumer to infer a zero. **A `null` in this group is never a zero cost.**

### 3.8 Denominator control

| field | type | meaning |
|---|---|---|
| `in_w7_denominator` | bool | is this row part of the W7 live result? |
| `denominator_exclusion_reason` | str \| null | why not, when false |
| `w7_window_start_basis` | str | how the window start was established for this account |

`in_w7_denominator` is true iff `stack_era == "w7_book"`. This is what pins the redacted_account window that
`SECOND_AUDIT.md:159-160` could only give as a range: the pre-halt fleet losses sitting on the same
account are `pre_w7_fleet` rows and are separable by comment, not by date guess. See the receipt for
the arithmetic and the residual.

---

## 4. Time base — the trap, stated once, plainly

**MT5 `history_deals_get().time` and `.time_msc` are broker *server wall clock*, expressed as a Unix
epoch.** Decoding them with `datetime.fromtimestamp(t, tz=timezone.utc)` yields a value that *claims*
UTC and is not — it is off by the server offset, `+3 h` in this window. This is finding F7, and the
tick export's `.timebase.json` sidecars carry the same warning for the same reason.

Both `*_broker` and `*_utc` fields are emitted so a consumer never has to convert, and the `*_broker`
fields are **naive** ISO strings with no offset suffix, so that attaching one is a visible act rather
than an accident. **Never trust a field because its name ends in `_utc`** — `broker_clock_rule` and
`broker_clock_offset_hours` are on every row so the conversion is auditable.

The conversion is `src/utils/broker_clock.broker_epoch_to_utc`, with `resolve_rule(broker_server)`.
Both servers resolve to `new_york_plus_7` (America/New_York + 7 h), measured over 81 weekly session
boundaries per broker. `resolve_rule` **fails closed** on an unregistered server; do not substitute a
hardcoded `+3`. The two calendars agree throughout this June/July window, but they disagree ~4 weeks a
year and a hardcoded offset is silently wrong in those weeks.

---

## 5. `magic` is not a sleeve key — do not join on it

`magic == 20260401` on 255 of 269 FTMO deals and 334 of 362 redacted_account deals. It is a **build stamp
shared by the pre-W7 fleet and the W7 book alike**, so it separates neither stack nor sleeve. Two
other values appear (`99887766`, `20260603`, `999001`, `24052026`) and none of them is a sleeve id.

Use `comment_raw` for sleeve identity and `stack_era` for the era split. `magic` is carried on each row
for provenance only.

Related trap, for anyone writing a filter over the deal set: **redacted_account's opening 100 k deposit is
deal type 4, not type 2** (finding V5). A balance-operation filter written against FTMO's shape
misclassifies a 100,000.00 row. The generator filters balance operations on `symbol == ""` rather than
on deal type, which is correct for both accounts.

---

## 6. What Session F should do with this

- Join on `(account, canonical_symbol, day_key_utc, sleeve_id, side)` for the replay-vs-live divergence
  matrix. `position_id` is unique but has no replay counterpart, so it is a provenance key, not a join key.
- Use `in_w7_denominator` to scope. A divergence matrix computed over the `pre_w7_fleet` rows is
  measuring the stack the go-live dossier ordered off — the two-stacks error, reproduced.
- Treat `realized_r` as the comparable economic quantity and `realized_net` as the reconciling one. Only
  `realized_net` sums to broker truth; `realized_r` is `null` wherever the broker recorded no stop.
- **Do not** fill a `null` with a zero. Every `null` has a `*_status` sibling naming the reason.
- Tolerate added fields. If a needed field is absent, say so on the branch rather than deriving it a
  second way — a second derivation is a second answer.
