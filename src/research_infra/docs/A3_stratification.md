# A3 — Per-Month Per-Session Per-Regime [Per-Side] Stratification

**Status:** Implemented (research-only; no production wiring). F2 added the
optional 4th axis (side) on 2026-04-26.
**Owner:** Decay-diagnostic research program.
**Falsifiability:** `pytest tests/research_infra/test_stratification.py -v` passes (95 tests).
**Out of scope:** AI calls, prompt edits, production-config edits.

## Why this exists

The headline decay metric for an instrument hides the underlying mechanism. A
single number ("XAUUSD H1→H2 WR 64.5% → 24.0%") cannot answer "Is the NY
session collapsing in trending regimes? Is London quietly dying in range
regimes? Is the LONG cohort the entire story?" — and those distinctions
matter for the prompt / gate fix that follows.

A3 stratifies realized-R outcomes across up to four orthogonal axes —
**month**, **session**, **regime**, and (F2) **side** — and surfaces the
(instrument, session, regime[, side]) combinations whose month-over-month
WR shifts cross a configurable threshold. The output is the input strata
for **A6 (Bayesian decay attribution)** and the supporting evidence for
any subsequent gate / prompt change.

## CLI: `--no-side-stratification`

The runner ships side-stratified by default per F2. Pass
`--no-side-stratification` to fall back to the legacy 3-axis schema —
useful for any caller that consumed the historical `strata.jsonl` rows and
isn't ready for the new `side` column. The flag is the only thing that
changes the output shape; pass-through helpers (`coverage_summary`,
`stratified_to_rows`, `find_change_points`) auto-detect which mode they
were given.

The default `--output-dir` is `research/decay_diagnostic/A3_stratification_side`
so re-running does not clobber the legacy 3-axis output at
`research/decay_diagnostic/A3_stratification`.

## Axes

### Month
`YYYY-MM` bucket from the trade's `candle_close_time`. Calendar months in
UTC.

### Session
One of `Asia` / `London` / `NY` / `Off`.

The classification is taken from the per-instrument kill-zone schedule in
`config/agent_config.yaml` (`market.kill_zones.{tokyo,london,ny}`) — the
windows are stamped in **UTC** and do **not** shift across DST boundaries.
The London open is 07:00 UTC in January (GMT) and 07:00 UTC in April (BST),
even though London local time interprets those instants as 07:00 and 08:00
respectively. This is consistent with the production config + the
production permissions gate.

Mapping:
- `tokyo` zone name → `Asia` label
- `london` zone name → `London` label
- `ny` zone name → `NY` label
- anything else (or no match) → `Off`

Window semantics: **inclusive** lower bound, **exclusive** upper bound.
A trade at exactly `end_utc` is `Off` (matches the production gate).

Cross-midnight windows (rare; e.g. NZDUSD-style `22:00 → 02:00`) are
handled by the function but no production instrument currently uses one.

### Regime
One of:
- `trending_bull`
- `trending_bear`
- `range`
- `reversal`
- `unclear`
- `UNTAGGED`

The label is read from the structure-detector divergence shadow log
(`shadow_logs/structure_detector_divergences.jsonl`) **plus** any sibling
archive / backfill files the loader walks automatically (see "Loader
contract" below). The lookup floors the trade's UTC timestamp to the
start of its enclosing H4 window (`00 / 04 / 08 / 12 / 16 / 20` UTC)
and queries `(symbol, timeframe="H4", h4_start_iso) → production_label`
from the log, preferring `production_label` then `v2_direction` then
`v1_direction`.

Detector labels (`bullish` / `bearish` / `transitional` / `insufficient_data`)
are normalized to the brief's labels:

| Raw label              | Normalized |
| ---------------------- | ---------- |
| `bullish`              | `trending_bull` |
| `bearish`              | `trending_bear` |
| `transitional`         | `range` |
| `chop`                 | `range` |
| `reversal_in_progress` | `reversal` |
| `insufficient_data`    | `unclear` |
| `unclear`              | `unclear` |
| (anything else)        | `UNTAGGED` |

#### Loader contract (multi-file)

`assign_regime` / `_load_structure_log` consume **every** structure-log
file in the live log's directory plus the conventional archive
directory. Specifically, given a seed path
`shadow_logs/structure_detector_divergences.jsonl`, the loader walks:

1. The seed path itself (live divergence log).
2. Every same-directory sibling whose basename starts with one of
   `structure_detector_divergences` or `structure_detector_backfill`
   AND ends in `.jsonl` or `.jsonl.gz`. This handles:
    - The current live `.jsonl`.
    - Rotated `.jsonl.gz` archives the `RotatingJsonlWriter` left in
      `shadow_logs/` (older deployments dropped them next to the live log).
    - The offline backfill at
      `shadow_logs/structure_detector_backfill_2026.jsonl`.
3. Every file in
   `research/archive/structure_detector_divergences/` matching the same
   suffix patterns. The default rotation policy stores rolled archives
   here. The loader walks up from the live log to find the project root
   marker (`pyproject.toml`) and then resolves the archive directory.
4. Files de-duplicate by resolved path; on key collisions
   (`(symbol, tf, ts)` already present), the last-loaded entry wins —
   matching the production "latest write wins" semantics.

`gzip.open(..., "rt", encoding="utf-8")` is used for `.gz` files. Both
file types share the same row schema (`ts`, `symbol`, `timeframe`,
`production_label` or `v2_direction` / `v1_direction`) so no separate
parser is needed.

A truncated / corrupt `.gz` produces a single `WARNING` log and
contributes zero rows to the merged map — the rest of the load
continues. We never raise out of the loader; A3 always falls back to
UNTAGGED rather than dying mid-CLI.

The CLI's `_resolve_structure_log` returns the seed path; selection
order is:
1. `shadow_logs/structure_detector_divergences.jsonl` (live).
2. `shadow_logs/structure_detector_backfill_2026.jsonl` (offline backfill).
3. `research/archive/structure_detector_divergences/<newest>.jsonl`
   (rotated archive when nothing in `shadow_logs/`).
4. `None` — every regime is UNTAGGED.

#### Backfill workflow

The live shadow log only writes rows on V1↔V2 **divergence** —
agreement windows are not logged. Worse, the detector only started
running on a given instrument from when the shadow logger was wired
in; trades older than that fall outside the live log's coverage
entirely. Without intervention, every trade's H4 window has no logged
row and the regime collapses to UNTAGGED.

The offline backfill closes that gap. Run from the project root:

```
python scripts/research/backfill_v2_regime.py
```

This:

1. Reads `data/historical_2026/{instrument}_H4.csv` for each instrument
   in A3's 9-instrument fleet (EURUSD, GBPUSD, GBPJPY, GER40, NAS100,
   UK100, USDJPY, XAGUSD, XAUUSD; broker-suffixed variants like
   `US30_cash` are also tried automatically).
2. For each H4 boundary that has a complete prior 80-candle lookback
   (matching `data.lookback.H4` in `config/agent_config.yaml`), runs:
    - `detect_swings(min_bars=2)` — same as production.
    - `identify_structure(...)` — v1.
    - `identify_structure_v2(..., dead_zone_divisor=8)` — v2 with the
      production divisor.
3. Writes one row per H4 boundary to
   `shadow_logs/structure_detector_backfill_2026.jsonl` in the same
   schema the live shadow logger emits (with `mode="backfill"`,
   `source="backfill_v2_regime"`, `production_label = v2.direction`).
4. Idempotent on a fixed input — re-running produces the same JSONL.

The output file is gitignored (`shadow_logs/` is in `.gitignore:29`)
and is treated as a regenerable artifact: re-run after a CSV refresh
or detector parameter change. After the F6 OHLCV extension to
2025-10, the backfill emits ~7,100 rows / ~2.6 MB across the 9
instruments × ~790 H4 boundaries each (2025-10-20 → 2026-04-24 — the
window after the 80-H4 lookback warm-up; pre-2025-10-20 H4
boundaries are inside the warm-up because the OHLCV starts
2025-10-01). Before the F6 extension this was ~3,571 rows over Jan 21
→ Apr 24, 2026.

Pre-backfill trades (anything older than 2025-10-20) remain UNTAGGED
until the backfill range is widened further. The CLI surfaces a
2026-window UNTAGGED fraction in the report so a reader can see
what's resolved vs what's still blind.

If `structure_log_path` is `None` at the API level, every trade
returns `UNTAGGED` without raising — useful for unit tests and any
analysis that wants to ignore the regime axis.

### Side (F2)

One of:
- `LONG`
- `SHORT`
- `UNKNOWN`
- `AGGREGATE` (sentinel — only present in legacy 3-axis mode)

Resolution order (`resolve_side` helper):

1. Explicit `direction` field on the trade dict — case-insensitive match
   against `LONG` / `SHORT` / `BUY` / `SELL`. `BUY → LONG`, `SELL → SHORT`
   (FTMO unified-CSV exports use the broker-side verb).
2. Entry-vs-SL inference — when `direction` is missing or unparseable,
   compare `entry_price` (or `open_price`) against `sl_price` (or
   `stop_loss`):

   - `entry > sl` → `LONG`
   - `entry < sl` → `SHORT`
   - equal / either missing / NaN → `UNKNOWN`

3. Otherwise → `UNKNOWN`. The CLI surfaces the rate as part of coverage.

The fallback inference is realized-R-correct on filled trades because the
order's planted endpoints disambiguate cleanly: a LONG always plants SL
below entry and vice-versa.

In legacy 3-axis mode (`stratify(..., side_stratified=False)`), every
stratum carries `side="AGGREGATE"` and the serializer drops the field.
The `long_n` / `short_n` per-row counters still reflect explicit direction
so the historical schema is bit-identical.

## Change-point detection

A `(instrument, session, regime[, side])` family is checked across
consecutive calendar months. A pair is flagged when:

1. `|wr_after - wr_before| >= delta_pp_threshold / 100` (default 15pp)
2. `n_before >= min_n` AND `n_after >= min_n` (default 10)
3. Months are consecutive (`YYYY-MM` adjacent in calendar order — year
   rollover supported).

`find_change_points` auto-detects whether the strata were produced
side-stratified — if any key carries a non-`AGGREGATE` side, the family
is `(instrument, session, regime, side)`; otherwise it is the legacy
`(instrument, session, regime)`. The serialized `ChangePoint` row drops
the `side` field when it's `AGGREGATE` so legacy consumers see no schema
change.

The raw p-value is from a **two-sided two-proportion z-test** on the win
counts. The statistic is computed in pure Python (no scipy) using the
pooled-variance formula and `math.erfc` for the normal CDF — the
precision is sufficient for the Bonferroni-corrected α = 0.05 we care
about.

The Bonferroni correction multiplies each raw p-value by the **family
size** — the number of `(instrument, session, regime)` strata pairs that
satisfy the WR-shift + min-n gates. Strata that do not satisfy these
gates are excluded from the family count to avoid over-correcting.

Output is sorted by descending `|delta_pp|`, breaking ties on `bonf_p`.

## Outputs

The CLI (`scripts/research/run_a3_stratification.py`) writes three files
into `--output-dir`:

### `strata.jsonl`
One row per `(instrument, month, session, regime[, side])` stratum.

Side-stratified mode (default after F2):

```json
{
  "instrument": "XAUUSD",
  "month": "2026-03",
  "session": "London",
  "regime": "trending_bull",
  "side": "LONG",
  "n": 14,
  "wins": 9,
  "wr": 0.6428,
  "exp_r": 0.43,
  "mean_r": 0.43,
  "total_r": 6.0,
  "long_n": 14,
  "short_n": 0
}
```

Legacy 3-axis mode (`--no-side-stratification`) — bit-identical to the
historical schema; the `side` field is omitted entirely:

```json
{
  "instrument": "XAUUSD",
  "month": "2026-03",
  "session": "London",
  "regime": "trending_bull",
  "n": 14,
  "wins": 9,
  "wr": 0.6428,
  "exp_r": 0.43,
  "mean_r": 0.43,
  "total_r": 6.0,
  "long_n": 14,
  "short_n": 0
}
```

`mean_r` is an alias for `exp_r`; both are the simple mean of
`r_multiple` over the bucket. `long_n` / `short_n` reflect explicit
direction in both modes (a UNKNOWN-side trade in legacy mode increments
neither counter).

### `change_points.json`
List of identified WR shifts, sorted by `|delta_pp|` descending:

```json
{
  "min_n": 10,
  "delta_pp_threshold": 15.0,
  "family_size": 8,
  "change_points": [
    {
      "instrument": "XAUUSD",
      "session": "NY",
      "regime": "trending_bull",
      "month_before": "2026-02",
      "month_after": "2026-03",
      "wr_before": 0.65,
      "wr_after": 0.20,
      "delta_pp": -45.0,
      "n_before": 20,
      "n_after": 15,
      "raw_p": 0.0034,
      "bonf_p": 0.0272,
      "family_size": 8
    }
  ],
  "generated_at": "2026-04-26T12:00:00+00:00"
}
```

### `report.md`
Human-readable markdown with:
- Change-points table (matches the brief's verdict format; gains a Side
  column in side-stratified mode)
- F2 verdict block — `Side-stratified change points (LONG breakdown)`
  panel + `SHORT cells with n >= 10` panel + `H2-2026 LONG breakdown`
  panel; only emitted in side-stratified mode
- Stratum-coverage summary (total strata, strata ≥ `min_n`, UNTAGGED %,
  UNKNOWN-side %)
- Per-instrument heatmap-friendly tables — gain a Side column in
  side-stratified mode

## Trade data sources

The CLI loads trades from every available source and dedupes on
`(symbol, candle_close_time, r_multiple)`:

1. **`research/**/all_results.json`** — primary source. Modern backtest
   slices write the canonical schema (`candle_time` ISO-8601 UTC,
   `r_multiple`, `direction`, `symbol`).

2. **`knowledge_base/index/_trade_index.json`** — historical trade index.
   Per-day entries; the CLI synthesizes `candle_close_time` from the
   recorded `kill_zone` start time so the month + session bucket is
   correct, but the exact UTC time is approximate. Acceptable for
   month-level stratification; not for intra-session analysis.

3. **`research/b_deep_audit_2026-04-19/phase1/_delta_scratch/trades_unified.csv`**
   — historical CSV. Same per-day approximation as the trade index.

The dedupe key is the `(symbol, candle_close_time, r_multiple)` triple,
so rows that overlap between the index and the slices collapse cleanly.

## Constraints + falsifiability

- DST tests cover the 2026-03-08 (US→EDT) and 2026-03-29 (UK→BST)
  boundaries on every relevant kill-zone edge — no session reclassifies.
- `Off`-hours trades are reported as their own session and never folded
  into Asia / London / NY.
- Bonferroni correction is applied across the full strata family.
- F2 backwards-compat: every legacy 3-axis test still passes; new
  `TestStratifyBackwardsCompat` covers the schema-stability guarantees.
- `pytest tests/research_infra/test_stratification.py -v` passes
  (95 tests including DST, planted change-point recovery, side
  resolution, side-stratified change points, and legacy-mode
  schema bit-identity).

## Open questions for follow-up

- **Regime UNTAGGED fraction.** With the offline backfill in place
  (`structure_detector_backfill_2026.jsonl`, ~7,100 H4 rows for 9
  instruments from 2025-10-20 → 2026-04-24 after the F6 OHLCV
  extension), the 2026-window UNTAGGED fraction is **0.0% (0/284
  trades)**. Total UNTAGGED across the entire trade-index population
  (which extends back to 2024-03) is **26.3% (108/411 trades)** —
  these are pre-2025-10-20 trades that fall outside the current
  backfill window. Before the F6 extension the comparable numbers
  were 18.3% / 43.6% (the warm-up gap covered Jan 2 → Jan 20, 2026
  trades inside the 2026 window plus all pre-2026 trades).
- **Pre-2025-10 backfill widening.** The current backfill is bounded
  by the `data/historical_2026/` CSVs (now 2025-10-01 → 2026-04-24
  after F6). To close the residual ~91 pre-2025-10 UNTAGGED trades
  (mostly Q1-Q3 2025), extend the OHLCV to 2024-09 or earlier via the
  same `scripts/research/extract_ohlcv_history.py` and re-run
  `backfill_v2_regime.py`.
- **Cross-instrument strata pooling.** A3 currently treats each
  instrument independently. A6 may pool across correlated instruments
  (XAU / XAG / NAS100); the stratifier already produces per-instrument
  rows so a pooling step on top of the JSONL is straightforward.
- **Sub-month change-point detection.** The brief's spec is monthly. If
  a regime shift lands mid-month, the WR boundary blurs. A weekly
  variant of `find_change_points` is a follow-up if signal warrants.
- **Change-point sensitivity.** With UNTAGGED no longer absorbing every
  trade, individual (instrument, session, regime) cells are inherently
  smaller. Default `min_n=10` may now be too strict — a `--min-n 5`
  re-run surfaces ~5 candidate transitions on the new strata. Re-tune
  the default once cell sizes reach steady state with a wider CSV
  range.
