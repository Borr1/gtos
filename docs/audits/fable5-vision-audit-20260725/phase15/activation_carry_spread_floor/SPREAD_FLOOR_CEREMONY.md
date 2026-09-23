# Ceremony — carry and arm the generation-side spread-geometry floor

Session CE (B2300–B2349). **This session arms nothing.** The orchestrator executes every step
below; Borhen decides the scope. The package is `phase15/activation_carry_spread_floor/`.

Authority: OD-HISTORICAL-FIRST (2026-07-31) §3 — *a measured, controls-clean improvement to an
armed sleeve must not sleep behind a default-off flag; built-but-unarmed is a DEFECT state.*
Evidence: `phase13/SESSION_AY_SPREAD_GEOMETRY_RESULT.md` and
`phase13/AY_SPREAD_FLOOR_ACTIVATION_DOSSIER.md`. Read AY's dossier §0 first — it establishes
that **the live books already refuse these trades at the send layer**, so the decision on the
table is whether to refuse them *earlier*, at generation.

---

## 0. The two corrections this package makes to what was believed before it

**0.1 The host's `book_engine.py` is NOT the lineage's, and building against the lineage would
have failed preflight on a funded machine.** `book_engine.py` reads like a path no ceremony has
written — Session AZ's manifest does not mention it, Session S's does not carry it — but
**Session AC's activation carry has it as `copy_order: 3`**, and that carry landed on
2026-07-29 12:37–12:39Z (8 of 9 files at after-hashes; `phase8/receipts/VPS_CEREMONY_COMPLETED.md`
§"What was actually left to do"). The host is at AC's after-bytes, **37,838 B / `b6a9ef7d…`**,
not the lineage's 36,498 B / `187f35a4…`. This build's first pass had it wrong; the manifest is
correct and `--check preflight` proves it against the host's own bytes.

**0.2 `src/utils/broker_clock.py` IS on the host, and BA-H1 is therefore already retired.**
Session BA's handoff item 2 says *"carry `src/utils/broker_clock.py` to the VPS before this
policy is ever armed"*, citing its absence at the 2026-07-26 export. It was carried **twice**
since — by Session S (`phase4/packet_carry`, `copy_order: 1`) and again by Session AC
(`phase5/activation_carry`, `copy_order: 1`) — and it is **committed on the host branch** at
`118071eaa`, specifically because it was an untracked load-bearing file a `git clean` would
have deleted. Host bytes `0f97bbb64bc55b02…`, 23,842 B, **byte-identical to mainline HEAD**.
That precondition is closed; see `phase15/CE_WEEKEND_POLICY_RECOMMENDATION.md`.

---

## 1. What is carried, in this order, and why the order is the safety argument

| # | path | host before | after | kind |
|---|---|---|---|---|
| 1 | `src/components/ultimate_book/spread_geometry.py` | **absent** | `1ea1b6bc…` (12,759 B) | NEW, mainline byte-identical |
| 2 | `src/components/ultimate_book/book_engine.py` | `b6a9ef7d…` (37,838 B) | `42c1bd6c…` (42,740 B) | host file + 3 anchored edits |
| 3 | `src/components/ultimate_book/book_owner.py` | `c6e762e9…` (226,002 B) | `b7a82dc3…` (227,316 B) | host file + 3 anchored edits |
| 4 | `run_book.py` | `c416f420…` (22,596 B) | `39ddfd51…` (27,310 B) | host file + 3 anchored edits |

Full hashes in `MANIFEST.json`. **Neither `book_engine.py` nor `book_owner.py` may be copied
from mainline** — mainline's are 58,727 B and 254,834 B against the host's 37,838 and 226,002,
and the difference is waves 5–14 whose import closure this host has never been checked for.
Session AZ made that argument for `book_owner.py`; it holds identically for `book_engine.py`.

**Files 1 and 2 are INERT on their own.** A ceremony interrupted after either has changed
nothing: nothing imports `spread_geometry`, and the engine's new kwarg defaults to `None`.
Files 3 and 4 are where the ordering bites, and `verify_carry.py --check deps` names each:

- `book_owner.py` **ahead of** `book_engine.py` → `UltimateBookLiveEngine()` receives an
  unexpected `spread_geometry_floor=` kwarg → **TypeError at STARTUP on both namespaces**,
  into a supervisor restart loop in which `manage_open_positions` never runs. This is the worst
  state this carry can produce.
- `run_book.py` ahead of `spread_geometry.py` → ImportError at launch.
- `run_book.py` ahead of `book_owner.py` → TypeError at launch.

**No config byte moves.** Both activation tokens bind a config digest; this carry writes only
`.py` files, so `config_digest=ffe16657feaf` (FTMO) and `e184a81d3b1b` (redacted_account) cannot
move. **No R2-bound path is touched** — 43 bound paths checked at session start and end: 2
UNHYDRATED-LFS, 0 drifted.

---

## 2. The exact ceremony

### 2.1 Preflight (before touching anything)

```powershell
cd C:\Users\MSI\Documents\ai-trading-agent
& .\.venv-gtos\Scripts\python.exe `
  docs\audits\fable5-vision-audit-20260725\phase15\activation_carry_spread_floor\verify_carry.py `
  --check preflight
```

Expect `RESULT: PASS` with all four rows at their expected before-bytes. **A row reading
`UNRECOGNISED` means something moved that file since this package was built — stop and
re-derive; do not copy over it.**

### 2.2 Backup, then carry — both kill flags HELD, both books flat

Hold `pipeline_state\ULTIMATE_BOOK_KILL_ftmo.flag` and `…_fn.flag` first. Back up the three
modified files (AZ's ceremony shape: a timestamped `gtos-*-backup-*` directory with a
`BACKUP_MANIFEST.json` recording each `.before` sha256). Then copy **in `copy_order`**,
sha256-verifying each on the host before the next:

1. `files\spread_geometry.py` → `src\components\ultimate_book\spread_geometry.py`
2. `files\book_engine.py` → `src\components\ultimate_book\book_engine.py`
3. `files\book_owner.py` → `src\components\ultimate_book\book_owner.py`
4. `files\run_book.py` → `run_book.py`

host-admin transfer: ≤2,800-char base64 chunks via `Add-Content -NoNewline` (the 8,191-char command
ceiling). `book_owner.py` is 227 KB — that is ~110 chunks; budget for it.

### 2.3 Verify the carry, before any restart

```powershell
& .\.venv-gtos\Scripts\python.exe docs\...\verify_carry.py --check all
```

`postflight` + `deps` + `imports` + `behaviour`. Expect `RESULT: PASS`. The behaviour gates
prove, against the host's own `config/agent_config.yaml`, that: the floor resolves to **0.10**
for both REPAIR sleeves (the send gate's own limit, inherited not typed); the per-sleeve
override is honoured (`fx_jpy` → 0.35); the NEUTRAL sleeves are not evaluated at all and no
tick is fetched for them; `mx_btcusd`'s frontier contract still renders `target_5R`; the
frontier and floor selections compose without overwriting each other; a refused intent does
**not** enter the day's conviction count (`na` 2 vs 1 on the same day, in throwaway ledgers);
and every fail-open parse shape is refused at launch.

This whole gate set was exercised **before the ceremony** against a reconstructed host tree
(lineage + the S, AC and AZ carries, each verified at its own manifest's after-hashes) —
receipt `receipts/DRY_RUN_RECONSTRUCTED_HOST.txt`, 45 `ok`, 0 FAIL, plus a proven rollback.
Session AC's verifier could never be run before it met a funded machine; this one has been.

### 2.4 Arm — the supervisor line, per account

`scripts\run_book_supervisor.ps1:140` is where `--tags` is set. The floor goes beside it,
**per account**:

```
--spread-geometry-floor sub_mid_dn_revert,sub_xvol_pullback
```

**Restart at a decision-day boundary, or delete that namespace's
`pipeline_state\ultimate_book\<ns>\firing_sleeves.json` first** (B365). `RunningConvictionLedger`
persists a per-day union and `admission.py` takes `na = max(na, override)` — monotone upward —
so restarting mid-day inherits the day's already-counted set and defers the floor's whole
conviction benefit to tomorrow. Both accounts' armed sets already include both REPAIR sleeves
(`crypto, energy_agri, sub_xvol_pullback, sub_mid_dn_revert`; FTMO also carries
`mx_btcusd_d1_donchian_20_breakout`).

### 2.5 The line that PROVES the floor armed

In the launcher's own output at startup, one WARNING **per named sleeve**:

```
SPREAD-GEOMETRY FLOOR IS ON for sub_mid_dn_revert at spread_r <= 0.1000 (inherited from the
send gate's own limit). Intents whose live spread exceeds that fraction of their own stop are
refused AT GENERATION, so they never enter the day's running conviction count. This changes
WHICH TRADES this book proposes.
```

**Absent ⇒ the flag did not take.** Two further reads, both in the cycle telemetry:
`generation.spread_geometry_floor` → `{evaluated, refused, sleeves}` (`evaluated == 0` on a day
the sleeve fired means the floor is not seeing intents), and `generation_skips` rows whose
`reason` starts `spread_geometry_floor:`, each carrying its own `spread_r`, `spread_price`,
`stop_dist` and `limit`.

---

## 3. Expected economics — on the recent-fold basis, which changes the recommendation

AY's dossier recommends **ARM `sub_mid_dn_revert`** and calls `sub_xvol_pullback` the owner's
call. **On the basis the estate ratified for anything that will be sized (wave-11 §1: recent
folds, not the full-window mean) that ordering inverts, and nobody had computed it.** AY
published the recent-fold *levels* (§3.1) but never the *delta* against them:

| armed sleeve | pooled Δ R/day (mid) | recent-fold Δ R/day (mid) | recent Δ as % of pooled | over limit | dropped |
|---|---:|---:|---:|---:|---:|
| `sub_mid_dn_revert` | **+0.4260** | **+0.0410** | **10 %** | 46.9 % | 249 |
| `sub_xvol_pullback` | **+0.2644** | **+0.2559** | **97 %** | 7.7 % | 6 of 85 |

(`dropped` is `n_dropped_by_live_contract` at mid. For `sub_mid_dn_revert` the scored `n`
differs between arms — 325 control against 208 filtered — because `era_population.apply` runs
per arm after the drop, so a "N of M" for that row would be comparing two different
denominators. For `sub_xvol_pullback` the calendar and the scored sample are identical, which
is why its row can be stated as a fraction.)

Recomputed here from `AY_SLEEVE_VERDICT_V1.json` → `recent_two_folds_mean_r_{control,live_contract}`,
which reproduce AY §3.1's published levels exactly (0.568 → 0.609 and 1.264 → 1.520). The
pattern holds at every band: `sub_mid_dn_revert`'s recent-fold ratio is 0.13 / 0.10 / 0.05 at
low / mid / high, `sub_xvol_pullback`'s is 1.50 / 0.97 / 0.97.

**Both readings are true and they answer different questions.** The pooled Δ is the evidence
that the effect is real — and it survives all three of AY's controls (beats every one of 20
random-drop seeds, negative inverse-cheapest, at ≥2 of 3 bands). The recent-fold Δ is the
**planning number**, and it is the one that belongs in a size decision, exactly as
`mx_btcusd` is planned at +0.198 R/day rather than its +0.982 full-window mean.

**Read together with §1.1 of AY's dossier — the conviction-count half, which does not depend on
either number.** A doomed intent inflates the day's Kelly-lite multiplier for every *other*
sleeve by up to **+25.227 %** (measured, 16 contaminated account-days on this host's own
export, 3 of which moved the multiplier; `na 1→2` is **+32.487 %**). That benefit is the same
whether the floor improves a sleeve's expectancy or not.

### Recommendation

| sleeve | recommend | why |
|---|---|---|
| `sub_xvol_pullback` | **ARM** | the repair survives into the recent folds at 97 % of its pooled size (+0.256 R/day), REPAIR at 2 of 3 bands, **identical fold calendar** (so its fold table is comparable, unlike the other's), and its `maxbars` share moves 0.047 → 0.051 |
| `sub_mid_dn_revert` | **ARM, at the recent-fold number** | REPAIR at 2 of 3 bands and by far the most engaged (46.9 % over limit ⇒ most of §1.1's conviction benefit comes from here), but plan it at **+0.041 R/day**, not +0.426. Its fold calendar moves ~4 years under the filter, so a fold-by-fold comparison is not available |
| `energy_agri`, `crypto` | **do not arm** | NEUTRAL — inside the 20-seed random envelope at every band. Arming them buys only §1.1 at the cost of a live-behaviour change with no economic support |

This is a change of *emphasis* from AY's dossier, not a contradiction of it: AY recommends
arming `sub_mid_dn_revert` and leaves `sub_xvol_pullback` to the owner; the recent-fold basis
says arm both, and expect the economics to come from the second while the conviction repair
comes from the first.

---

## 4. What it costs, stated honestly

1. **It refuses trades an armed book takes today**, at generation instead of at send. For
   `sub_mid_dn_revert` that is 46.9 % of its archive trades — not a trim, a different sleeve.
   The send gate already refuses them, so the *placed* population should be unchanged. **That
   equivalence is an inference, not a measurement** — §5 stop condition 3 is how it gets
   measured rather than assumed.
2. **`sub_xvol_pullback`'s whole gain rests on 6 dropped trades of 85.** It beats all 20 random
   seeds, which is the strongest statement 20 seeds can make, and it is still six trades.
3. **Neither REPAIR admits.** Both still REJECT at the ratified family. This is a fidelity
   repair, not an admission, and no sentence anywhere should read otherwise.
4. **ON, the floor adds one `get_tick` per candidate intent per tick** on the generation path —
   a broker interaction that does not exist today. Zero when OFF.
5. **Naming a sleeve refuses more than "over the limit", by fail-closed design.** An
   unreadable, crossed or absent quote, a non-positive stop, or any exception inside the floor
   refuses that intent. On a symbol whose quote cannot be read, an opted-in sleeve proposes
   nothing that tick. That matches the authoritative gate's own
   `missing_current_quote_spread_or_sl_distance`, and it is a real behaviour change to accept.
6. **`empirical_p_vs_random = 0.0476` is the resolution floor of a 20-seed null (1/21)**, not a
   measured value, and it is the same on all three bands because the seeds are shared. Read
   `beats_every_random` as the statement.
7. **The controls are matched on the drop count BEFORE the population rule runs**, not on the
   scored sample: at mid, live n 208 against random mean 173.9 and inverse 137, from identical
   284-row pre-population kept-lists. That widens the null and makes "beats every random"
   *harder*, but it is not what "matched control" naturally reads as.

---

## 5. Stop conditions — disarm if any is observed

1. **`spread_geometry_floor_quote_unavailable` on more than ~5 % of evaluated legs over a
   week.** The floor fails closed on an unreadable quote, so a persistent quote-read fault
   would silently thin the sleeve. This is the flag's most likely failure mode and it is why
   the telemetry counts *evaluated* as well as *refused*.
2. **Any `spread_geometry_floor_error:` row.** An internal fault refuses the intent and names
   the exception. One is a bug report; a stream is a disarm.
3. **The refused-leg count does not roughly match the `cost_screen_spread_r` skips the same
   sleeve produced before the change.** §4.1's equivalence is an inference: the floor reads the
   tick at GENERATION, the screen reads it at SEND, seconds apart. A systematic gap means one
   of them is not measuring what this page assumes. **The single most useful thing to watch in
   week one.**
4. **`sub_mid_dn_revert`'s realised R/day over 30 book-days falls below its pre-change trailing
   figure by more than its own random envelope (±0.12 R/day at mid).** At ~7 book-days/month
   that is a slow check, not a trigger — and note §3: the recent-fold expectation for this
   sleeve is +0.041 R/day, which 30 book-days cannot resolve. Treat it as a guard against a
   large adverse move, not as a test of the repair.

## 6. Rollback

Restore the three `.before` files from the backup, delete `spread_geometry.py`, restart at a
decision-day boundary, then:

```powershell
& .\.venv-gtos\Scripts\python.exe docs\...\verify_carry.py --check rollback
```

**There is no state to unwind.** The floor writes nothing, holds nothing and touches no
position; it only declines to emit an intent. A position already open is unaffected — the floor
runs in `_generate_intents` and every exit path reads the trade record. Rollback is strictly
safer than the arming. Proven on the reconstructed tree in
`receipts/DRY_RUN_RECONSTRUCTED_HOST.txt`.

Removing only the `--spread-geometry-floor` argument (leaving the code carried) is also a
complete rollback of *behaviour*: default `{}` is byte-identical to today, which
`--check behaviour` gate (b) asserts directly.

## 7. What this ceremony does not claim

- It does not claim the floor makes any sleeve admissible. Nothing admits.
- It does not claim the *placed* population is unchanged. It should be, and §5.3 is how that
  gets measured.
- It does not touch the send-layer limits. `selected_cell_pretrade_max_spread_r` lives in an
  R2-bound file whose bytes are hashed into both activation tokens; this package reads it at
  run time and never writes it — which is exactly why the selection is a launcher argument and
  the threshold is not.
- It carries no generator constant change. `AY_GENERATOR_STOP_SURVEY_V1.json` measures why: an
  ATR stop floor is not a spread floor.
