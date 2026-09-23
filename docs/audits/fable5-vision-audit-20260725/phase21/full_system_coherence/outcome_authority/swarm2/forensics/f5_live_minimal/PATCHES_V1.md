# F5 — the exact seams, with before/after

All line numbers read at HEAD `ef8533e1c` in
`/Users/borr/GTOSActive/worktrees/claude-opus5-architecture-audit-20260725`.
**H1 membership check run 2026-08-12 against R2 (43 bound paths):** every file below is
**FREE** — `src/components/execution.py`, `src/components/ultimate_book/{book_engine,book_owner,
order_router,execution_packets,admission,launcher}.py`, `run_book.py`,
`scripts/run_book_supervisor.ps1`, `config/live_armed_set.json`. The only bound paths this
package comes near are `config/agent_config.yaml` (BOUND, and reads DRIFTED in this worktree)
and `config/profiles/operator_profile.yaml` (BOUND, clean) — **and the package edits
neither**, so there is no re-seal and no token re-mint. `config/profiles/redacted_account.yaml` is
bound by neither contract.

Everything is behind `--f5-minimal-size-usd`. With the flag absent, every hunk below is a
no-op and the default path is byte-identical to production. That property is what P4 tests.

---

## P1 — `run_book.py`: the flags (new, ~line 157, beside `--spread-geometry-floor`)

```python
    p.add_argument("--f5-minimal-size-usd", type=float, default=None,
                   help="MINIMAL-SIZE EXPERIMENT. Run every decision at the NOMINAL dial and place "
                        "at this fixed dollar risk per trade. Absent = off (production sizing).")
    p.add_argument("--f5-notional-initial-usd", type=float, default=100000.0,
                   help="Starting equity of the NOTIONAL ledger the governor reads.")
```

**There is deliberately NO loss-budget flag.** Owner decision, 2026-08-12: *"there should be no
limit set as i'll be there to witness it so that we dont kill or suffocate the system."* The
experiment runs inside the firm's own guards and the production governor exactly as the armed
book does — the daily-loss guard, the max-DD band, the breach flatten, the kill flag and the
activation token are all untouched and none is bypassed. What replaces the budget is
**visibility**: `scripts/f5_status.py` (§P9) and the `real_pnl_usd_cumulative` the ledger keeps
for reporting only.

Threading, mirroring `--vol-level-tilt` exactly (`run_book.py:597` → `BookOwner`):

```python
                              vol_level_tilt=args.vol_level_tilt,
                              frontier_exits=frontier_exits,
                              spread_geometry_floor=spread_geometry_floor,
+                             minimal_size=minimal_size_cfg,
```

built just above, next to the `parse_frontier_exits` block (`run_book.py:528-556`), so a bad
value refuses at launch rather than degrading silently every tick:

```python
    from src.components.ultimate_book.minimal_size import MinimalSizeConfig
    minimal_size_cfg = MinimalSizeConfig(
        enabled=args.f5_minimal_size_usd is not None,
        target_risk_usd=float(args.f5_minimal_size_usd or 0.0),
        notional_initial_usd=float(args.f5_notional_initial_usd),
    )
    minimal_size_cfg.validate()      # raises -> the worker never starts mis-sized
```

and a banner at launch, beside the `--frontier-exits` banner (`run_book.py:643-658`), because
**a book whose command line you cannot read is a book you cannot trust** (CLAUDE.md §4: check
the command line, not the heartbeat):

```python
    if minimal_size_cfg.enabled:
        log.warning("F5 MINIMAL SIZE ARMED: decisions at NOMINAL dial, lots at $%.2f/trade; "
                    "notional ledger $%.0f; magic %d; NO loss budget (owner-directed)",
                    minimal_size_cfg.target_risk_usd, minimal_size_cfg.notional_initial_usd,
                    magic_for_namespace(args.namespace))
```

---

## P2 — `execution.py:3445`: the scalar, at the LAST possible step

**Before**

```python
3445:        risk_amount = account_balance * (risk_pct / 100)
3446:        require_broker_geometry = self._vnext_requires_verified_broker_geometry(trade_params)
```

**After**

```python
3445:        risk_amount = account_balance * (risk_pct / 100)
     +      # ---- F5 minimal-size seam (default OFF) -------------------------------------
     +      # This is the LAST step at which money size is decided. Everything that decides
     +      # WHETHER to trade has already run at nominal: admission + the 4% gross cap +
     +      # the governor (before open_trade was called), the pre-trade cost model (:3407)
     +      # and Execution Manager V4 (:3411), both of which received `risk_pct` unchanged.
     +      f5_nominal_risk_amount = risk_amount
     +      if self._f5_scaler is not None:
     +          risk_amount = self._f5_scaler.scaled_risk_amount(risk_amount, trade_params)
3446:        require_broker_geometry = self._vnext_requires_verified_broker_geometry(trade_params)
```

`self._f5_scaler` is `None` unless injected; `ExecutionEngine.__init__` gains
`f5_scaler=None`, passed down from `book_owner._exec_engine`.

**Do not move this earlier.** At `:3407` the pre-trade cost model would then price a $10 trade
and its cost-veto would behave differently; at `:3411` Execution Manager V4's blocks would
change. Both are decision surfaces.

---

## P3 — `execution.py:3474-3479`: shed → round up

**Before** (this is the sampling-bias hazard)

```python
3469:        if require_broker_geometry and sym_info is not None:
3470:            try:
3471:                _vmin = float(sym_info.volume_min)
...
3474:            if _vmin is not None and _vmin > 0 and float(lots) < _vmin:
3475:                logger.warning(
3476:                    "vNext book unit below broker min lot -> breadth unit shed (NOT retried): "
3477:                    "%.6f < volume_min %.6f (%s)", float(lots), _vmin, self.symbol)
3478:                self._last_open_trade_block_reason = f"below_min_lot:{float(lots):.4f}<{_vmin:.4f}"
3479:                return None
```

**After**

```python
3474:            if _vmin is not None and _vmin > 0 and float(lots) < _vmin:
     +              if self._f5_scaler is not None and self._f5_scaler.round_up_enabled:
     +                  # F5: NEVER shed. Shedding here deletes exactly the expensive-stop
     +                  # instruments (BTCUSD, XAGUSD, XAUUSD, ETHUSD on FTMO; those plus the
     +                  # 10x-contract indices on redacted_account) and the surviving sample answers
     +                  # no cost question. Round up and RECORD the inflation instead.
     +                  from .ultimate_book.minimal_size import round_up_to_min_lot
     +                  lots, _f5_prov = round_up_to_min_lot(float(lots), sym_info)
     +                  self._f5_last_round_up = _f5_prov
     +                  if _f5_prov.get("f5_round_up") not in ("applied", "not_needed"):
     +                      self._last_open_trade_block_reason = (
     +                          f"f5_round_up_refused:{_f5_prov.get('f5_round_up')}")
     +                      return None
     +              else:
3475-3479:              ... unchanged shed ...
```

Then, at the existing `pre_send_cash_risk_amount` computation (`execution.py:3490`), stamp the
realised size onto `trade_params` so the packet and trade record carry it:

```python
     +      if self._f5_scaler is not None:
     +          trade_params["f5_nominal_risk_usd"]  = float(f5_nominal_risk_amount)
     +          trade_params["f5_intended_risk_usd"] = float(self._f5_scaler.last.get("f5_intended_risk_usd"))
     +          trade_params["f5_actual_risk_usd"]   = float(pre_send_cash_risk_amount or 0.0)
     +          trade_params["f5_round_up"]          = getattr(self, "_f5_last_round_up", None)
```

`pre_send_cash_risk_amount` is the broker's own `order_calc_profit` on the NORMALIZED volume —
it is the true realised risk, not an estimate, and it is what makes the reweighting exact.

---

## P4 — `book_engine.py`: the three notional surfaces

### P4a — equity (`book_engine.py:783-788`)

```python
     def _equity(self) -> Optional[float]:
+        if self._f5_ledger is not None:
+            return float(self._f5_ledger.equity())          # N1
         try:
             eq = self._mt5.get_account_equity()
```

### P4b — open risk (`book_engine.py:860`)

```python
     def _open_risk_pct(self, equity: float) -> float:
+        if self._f5_ledger is not None:
+            return float(self._f5_ledger.open_risk_pct())   # N2 -- the 4% cap must bind
         try:
```

**This is the hunk that makes the experiment valid.** Without it the cap sees ~0.0002 instead
of ~0.02 and the book runs 20+ concurrent units where production runs 2
(`F_LAW_AND_LADDER_V1.json` → `max_concurrent_units_by_dial["2.0%"] = 2.0`).

### P4c — the daily baseline (`book_engine.py:975`, `:906`)

```python
             dsb = self._governor.reconstruct_day_start_balance(self._mt5, now)
+            if self._f5_ledger is not None:
+                dsb = self._f5_ledger.day_start_balance(
+                    self._governor.reset_window_date(now))   # N3
             if dsb is None and self._deal_capable():
```

`reset_window_date` is already the broker-correct reset-window key
(`governor_state.py:274-277`), so the notional day rolls on the same clock the firm uses.

---

## P5 — `book_owner.py`: the epoch and the close hook

### P5a — WITHDRAWN (owner decision, 2026-08-12)

An earlier draft placed a real-money cumulative/daily loss brake here. **It is removed.** No
`--f5-loss-budget-usd`, no `real_budget_verdict`, no `latch_permanent_standdown`, no automatic
stand-down on a cumulative-loss threshold. The production guards below are untouched and remain
the only brakes: the governor's soft daily stop (−3 %), `breach_flatten_check` (−4 % daily /
−9 % DD), the firm's own −5 % / −10 % lines, the per-account kill flag, and the activation token.

The ledger still accumulates `real_pnl_usd_cumulative` — **for the operator view, not for a
gate.** Nothing reads it to make a decision.

### P5b — the notional epoch (requirement 3), where `breach_flatten_check` is consumed

`book_engine.breach_flatten_check` (`:918-947`) already returns
`{flatten, block_entries, reason, metrics}` off the governor state — which, under P4, is the
NOTIONAL state. So the notional breach fires the real flatten path unchanged, and F5 only adds
the epoch roll after it:

```python
+        if self._f5_ledger is not None and bf and bf.get("flatten"):
+            closed = self._f5_ledger.open_new_epoch(bf.get("reason") or "notional_breach")
+            self._f5_capture.emit("f5_notional_standdown", {
+                "epoch_closed": closed, "governor_metrics": bf.get("metrics"),
+                "new_epoch": self._f5_ledger.snapshot()["epoch"]})
```

Order matters: **flatten runs first (production behaviour, observed), then the ledger resets
(collection survives).** The event is numbered and written before the reset takes effect.

### P5c — the close hook, beside `_write_trade_record` (`book_owner.py:3238`)

```python
+        if self._f5_ledger is not None and close_action:
+            row = self._f5_ledger.on_close(
+                ticket=ticket,
+                broker_net_pnl_usd=float(rec.get("broker_net_profit") or 0.0))
+            self._f5_capture.emit("f5_trade_closed", row)
```

and the open hook, where the placement ledger is appended (`placement_ledger.py:245` caller):

```python
+        if self._f5_ledger is not None and result.get("placed"):
+            tp = result["trade_params"]
+            self._f5_ledger.on_open(
+                ticket=result["trade_state"].ticket, sleeve=intent.sleeve, symbol=intent.symbol,
+                nominal_risk_usd=tp.get("f5_nominal_risk_usd"),
+                actual_risk_usd=tp.get("f5_actual_risk_usd"),
+                intended_risk_usd=tp.get("f5_intended_risk_usd"),
+                decision_day=_dday)
+            self._f5_capture.emit("f5_fill", {**{k: tp.get(k) for k in
+                ("f5_nominal_risk_usd","f5_intended_risk_usd","f5_actual_risk_usd","f5_round_up")},
+                "ticket": result["trade_state"].ticket, "candidate_id": tp.get("candidate_id"),
+                "sleeve": intent.sleeve, "symbol": intent.symbol, "broker_mutation": True})
```

---

## P6 — the capture gap that is NOT a seam: rejected candidates

`admission.py` is 1,962 lines and **writes nothing to disk** (its only `json.dumps` is a `print`
in a `__main__` block at `:1867`). Skips reach disk as `unit_skipped` packets, but
`_runtime_learning_skip_row` (`book_owner.py:944`) carries no score and no rank — so "we saw 9,
took 2, here is why 3 lost to 6" cannot be reconstructed from today's logs. This is the one
genuinely new record F5 needs. It is pure observation, downstream of every decision:

```python
+        if self._f5_capture is not None:
+            self._f5_capture.emit("f5_slate", {
+                "decision_bar_iso": dbar, "decision_day": _dday,
+                "n_intents": len(intents),
+                "units": [{"cluster": u.get("cluster"), "sleeve_members": u.get("sleeve_members"),
+                           "confidence": u.get("confidence"), "sized": u.get("sized"),
+                           "reason": u.get("reason"),
+                           "risk_pct_per_trade": u.get("risk_pct_per_trade"),
+                           "unit_risk_pct": u.get("unit_risk_pct"),
+                           "overlays_applied": u.get("overlays_applied")} for u in decision_units],
+                "governor": {"allow": gov.allow, "cap_mult": gov.cap_mult,
+                             "available_gross_risk_pct": gov.available_gross_risk_pct,
+                             "reason": gov.reason},
+                "skipped": summary.get("skipped"),
+                "broker_mutation": False})
```

`SizedUnit.reason` already carries `gross_risk_cap_would_exceed` and the overlay tags
(`admission.py:1408-1414`, the D5 fix), so the shed reason and the conviction provenance both
survive into the record without a single new computation.

---

## P7 — tests that must ship with it

| test | what it pins |
|---|---|
| `test_f5_default_path_byte_identical` | with the flag absent, `open_trade` produces the same `lots`, the same `trade_params` keys and the same block reasons as `HEAD~` on a frozen fixture set |
| `test_f5_scalar_is_last` | with the flag on, the pre-trade cost model and Execution Manager V4 both receive the NOMINAL `risk_pct` (assert on the recorded call args, not on source text) |
| `test_f5_gross_cap_still_binds` | with the flag on at $10 and 3 open units, `_open_risk_pct` returns the NOMINAL sum and the 4th unit is shed `gross_risk_cap_would_exceed` — the differential test against a broker-volume-derived open risk shows the cap would NOT have bound |
| `test_f5_round_up_never_sheds` | every symbol in the 24-symbol surface at a $1 target places at `volume_min`, none returns `below_min_lot`, and `f5_lot_inflation` is recorded |
| `test_f5_round_up_grid` | the rounded lot is on the `volume_step` grid and `>= volume_min` for all 42 traded specs |
| `test_f5_epoch_resets_and_logs` | a notional breach flattens, emits `f5_notional_standdown` with the closed epoch, increments the epoch, and resets notional equity — and does NOT reset `real_pnl_usd_cumulative` |
| `test_f5_real_budget_is_not_resettable` | after `latch_permanent_standdown`, an epoch roll does not clear it and the next cycle still refuses |
| `test_f5_capture_has_namespace` | every emitted row carries `namespace` and `account_login` (the defect `shadow_logs/slippage.jsonl` has) |
| `test_f5_armed_set_unchanged` | `src.safety.armed_set.armed_sleeves()` is unaffected by the flag |

---

# ADDENDUM — two decision surfaces on ONE account (added 2026-08-12, owner venue change)

The experiment now runs on **both funded accounts, alongside the armed three-sleeve book**. Two
`run_book.py` workers per account. Namespace isolation already covers every FILE surface. It
covers **no BROKER surface**, and that is where the hazard is.

## A0 — what namespace already isolates (verified, no change needed)

| state | path | isolated? |
|---|---|---|
| single-instance lock | `pipeline_state/ultimate_book/<ns>/run_book.lock` (`run_book.py:343-345`) | **yes** — two namespaces coexist by construction |
| PID file | `…/<ns>/run_book.pid` (`run_book.py:358-369`) | yes |
| heartbeat | `…/<ns>/heartbeat.json` (`launcher.py:172-200`) | yes |
| **conviction ledger** | `…/<ns>/firing_sleeves.json` (`running_conviction_state.py:16, 34-37`) | **yes** — the `na = max(na, override)` hazard (`admission.py:1188`) cannot cross namespaces |
| placement ledger | `…/<ns>/placed_decisions.jsonl` (`placement_ledger.py:245`) | yes |
| trade records | `…/<ns>/trade_records/<ticket>.json` (`book_owner.py:3238`) | yes |
| governor state | `…/<ns>/{high_water,day_anchor}.json` (`governor_state.py:54-57`) | yes |
| supervisor liveness | `Test-BookRunning` matches `*--namespace <ns>*` | yes — a third/fourth row needs no guard change |

Two shared writers to fix by configuration, not code: `shadow_logs/ultimate_book_launcher.jsonl`
already stamps `namespace` (`launcher.py:235`); **`shadow_logs/slippage.jsonl` stamps nothing** —
give the F5 workers their own console log and rely on the F5 capture's `namespace` field.

## A1 — what namespace does NOT isolate: the broker sees ONE book

`MAGIC_NUMBER = 20260401` is a single module constant (`src/mt5/mt5_interface.py:58`) and every
position read filters on it:

| reader | file:line | consequence on the ARMED book if the experiment shares the magic |
|---|---|---|
| `RealMT5.get_open_positions` | `mt5_real.py:358` | feeds `book_engine._open_risk_pct:860`. **Fail-closed hazard:** that function returns the FULL 4 % cap if ANY position has `sl == 0`, `price_open == 0`, or an unreadable `value_per_point` (`book_engine.py:878-884`). One experiment position on a symbol without instrument config — and `CLAUDE.md` §4 records redacted_account silently skipping **13 symbol/sleeve pairs on missing instrument config** — makes the ARMED book read `gross_risk_cap_exhausted` and **stop opening any unit at all**, silently. |
| `RealMT5.get_positions(symbol)` | `mt5_real.py:335` | same-symbol lifecycle (`max_open_same_symbol_tickets: 1`, `agent_config.yaml:97`): an experiment position on BTCUSD blocks the ARMED `crypto` sleeve, and vice versa |
| `cross_instrument_correlation_gate` | `:501-503, 518, 542` | ≥2 correlated same-direction open positions **halve** the armed size; ≥3 **reject** it. The experiment routinely holds correlated positions. |
| `book_owner._position_exposures` | `:537-545` | classifies as "book position" on `comment.startswith("W7:")` **or** ledger **or** magic. The ledger is per-namespace, but the other two are shared → the armed book **adopts and exit-manages** experiment positions. `_manageable_pairs` calls `active_specs(None, …)` **not** intersected with `--tags` (`book_owner.py:2680`), so it adopts sleeves it is not even armed for. |
| `book_owner._alert_out_of_universe` | `:2436` | `is_w7 = magic == MAGIC_NUMBER or cmt.startswith("W7:")` → alert storm |

**Left shared, this is a live-behaviour change on real armed money, in five places, three of
which are silent.** It is not acceptable and it does not need to be accepted.

## A2 — the fix: the magic is a function of the namespace

One idea, mechanical everywhere. `src/mt5/mt5_interface.py`:

```python
MAGIC_NUMBER = 20260401                     # unchanged: the armed book's identity
MAGIC_F5_MINIMAL = 0                 # the minimal-size experiment's identity

_NAMESPACE_MAGIC = {
    "operator":       MAGIC_F5_MINIMAL,
    "redacted_account_f5_minimal": MAGIC_F5_MINIMAL,
}

def magic_for_namespace(namespace: str | None) -> int:
    """The broker-side identity of a decision surface. A pure function of the namespace, which is
    already the uniqueness key for the lock, the ledgers, the supervisor and the activation
    context -- so it cannot be set wrong independently of everything else, the way a free
    environment variable could."""
    return _NAMESPACE_MAGIC.get(str(namespace or ""), MAGIC_NUMBER)
```

Then replace the module-constant reads with an instance attribute resolved once at construction:

| file | sites | change |
|---|---|---|
| `src/mt5/mt5_real.py` | `:335`, `:358` | `RealMT5.__init__(..., magic: int = MAGIC_NUMBER)`; filters become `p.magic == self._magic` |
| `src/components/execution.py` | `:3542`, `:8106`, `:8260`, `:8314`, `:8432`, `:8506`, `:8580`, `:8645` | `"magic": self._magic` |
| `src/components/execution.py` | the two `order_comment` sites | prefix from `self._comment_prefix` (`"W7:"` armed, `"F5:"` experiment), still `[:16]` — MT5 truncates comments to 16 chars |
| `src/components/cross_instrument_correlation_gate.py` | `:518`, `:542` | compare against the caller's magic, passed in |
| `src/components/ultimate_book/book_owner.py` | `:542`, `:2436` | `magic == self._magic` and `cmt.startswith(self._comment_prefix)` |

`run_book.py` resolves it once — `magic = magic_for_namespace(args.namespace)` — and passes it to
`RealMT5` and to `BookOwner`. **Nothing about the armed workers changes**: their namespace is not
in `_NAMESPACE_MAGIC`, so `magic_for_namespace` returns `20260401` and every comparison is the
one it makes today.

After this, `mt5_real.py:358` returns **zero** experiment positions to an armed worker, which
closes all five rows of A1 at the source — the gross-cap read, the same-symbol gate, the
correlation gate, adoption, and the out-of-universe alert — because all five consume that one
filtered list.

## A3 — the coupling that CANNOT be isolated, and the honest report

**Real account equity is one number and both books read it.** Under the F5 design the
experiment's governor reads the notional ledger, so the experiment is isolated *from* the armed
book. The reverse is not isolable: the armed book's `_equity()` returns broker equity, which
includes the experiment's realised P&L. It is one account; no design fixes that.

**Quantified, from the code.** `admission._governor_decision` (`:1338-1356`):
`dd = (dd_ref - equity) / dd_ref` where `dd_ref = governor_static_initial_balance`, **default
100 000.0** (`book_engine.py:202, 209` → `governor_state.py:60, 298`). Then

```
dd <= 0.07                 -> cap_mult = 1.0            (no effect at all)
0.07 < dd < 0.10           -> cap_mult = 1 - (dd - 0.07)/0.03
```

So on a $100,000 reference the knee is at **equity $93,000**, and inside the band the slope is
`1/(0.03 x 100000)` per dollar — **$100 of experiment loss = 3.33 percentage points of the armed
book's size.** Above $93,000 the cost is **exactly zero**, not small.

| account | equity 2026-08-11 | dd vs $100k ref | `cap_mult` today | distance to the $93,000 knee | verdict |
|---|---:|---:|---:|---:|---|
| FTMO | $108,342.47 | −8.34 % | **1.0000** | **$15,342.47** | **no coupling at any plausible experiment size** |
| redacted_account | $96,229.28 | +3.77 % | **1.0000** | **$3,229.28** | **no coupling today; a tripwire, not a blocker** |

**This is a tripwire to instrument, not a reason to refuse.** `scripts/f5_status.py` prints
`to_derisk_knee_usd` per account on every read and flags `COUPLED` the moment it goes negative.

**One host read settles it and belongs in step zero.** The live redacted_account receipt
(`swarm/three_sleeve_receipts/FN_SIZE_CAP_V1.json`) records `size_cap_multiplier 0.622928,
reason derisking_into_maxdd_wall`, which is *not* what a $100,000 reference and $96,229 equity
produce (that gives 1.0). Either the host's `governor_static_initial_balance` is not 100,000, or
the receipt is from a different equity moment. Read the host's value and the live governor block
before starting; if redacted_account really is at 0.6229 then it is **already inside the band** and
every experiment dollar there costs 3.33 pp of armed size — still the owner's call, but he must
make it knowing that.

## A4 — the proof, by test, not by reading

| test | asserts |
|---|---|
| `test_f5_magic_is_namespace_derived` | `magic_for_namespace("operator_profile") == 20260401`, `…("operator") == 0`, and an unknown namespace returns the armed magic |
| `test_f5_armed_book_cannot_see_experiment_positions` | a fake `positions_get` returning a mixed list; the armed `RealMT5.get_open_positions()` returns **only** magic-20260401 rows and `_open_risk_pct` is numerically identical to the no-experiment case |
| `test_f5_open_risk_fail_closed_not_triggered_by_f5` | an experiment position with `sl == 0` (the fail-closed trigger at `book_engine.py:878-884`) leaves the armed book's `_open_risk_pct` unchanged — **the silent-shutdown case** |
| `test_f5_correlation_gate_ignores_experiment` | three correlated experiment positions do not halve or reject an armed unit |
| `test_f5_same_symbol_gate_ignores_experiment` | an experiment BTCUSD position does not block the armed `crypto` sleeve |
| `test_f5_adoption_ignores_experiment` | `_position_exposures` returns `[]` for an `F5:`-commented, magic-0 position, on all three clauses |
| **`test_f5_conviction_ledger_is_namespace_isolated`** | writing 20 firing sleeves to `…/operator/firing_sleeves.json` leaves `…/operator_profile/` untouched, and the armed book's `na` (`admission.py:1188`) is unchanged — **run it as a filesystem test on real paths, not a mock** |
| `test_f5_comment_prefix_fits_mt5` | `f"F5:{sleeve}"[:16]` is what is sent, and no armed comment starts `F5:` |
| `test_f5_two_workers_lock_independently` | both `…/<ns>/run_book.lock` files acquire simultaneously |

`test_f5_conviction_ledger_is_namespace_isolated` and
`test_f5_open_risk_fail_closed_not_triggered_by_f5` are the two that must pass before the
ceremony. The rest can follow.
