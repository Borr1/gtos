"""Session LM — owner-manual-move support, patched against the HOST lineage copy.

Borhen 2026-08-05: "if i make a move on my ftmo account it should reflect on the book,
my manual moves should be allowed and 'normal' to have."
"""
import sys, hashlib, pathlib

SRC = pathlib.Path("/tmp/lm_host/execution_host.py")
DST = pathlib.Path("/tmp/lm_host/execution_patched.py")
t = SRC.read_bytes().decode("utf-8")
assert hashlib.sha256(SRC.read_bytes()).hexdigest() == \
    "d0d367877dfb6cde52f886a93623238dfaa788e5d7f14b8e19451e3c62938445", "wrong base file"

def sub(old, new, why, count=1):
    n = t.count(old)
    assert n == count, f"[{why}] expected {count} occurrence(s), found {n}"
    return t.replace(old, new, count)

# ---------------------------------------------------------------- 1. TradeState fields
OLD = """    gtos_vnext_book_native_exit_management: bool = False


@dataclass"""
NEW = '''    gtos_vnext_book_native_exit_management: bool = False
    # --- Owner (manual) protective-level overrides -------------------------------------
    # Borhen, 2026-08-05: "if i make a move on my ftmo account it should reflect on the
    # book, my manual moves should be allowed and 'normal' to have."  The BROKER is the
    # truth for SL/TP.  ``_reconcile_broker_protective_levels`` re-reads both every
    # management tick, adopts whatever is live, and records who set it so the learning
    # lane can tell an owner-steered outcome from the sleeve's own.
    #
    # ``sl_distance`` is deliberately NOT rewritten when the owner moves a stop: it is
    # the SIZING basis (the definition of 1R) and every downstream R computation is
    # anchored to it.  Keeping it fixed is what makes ``owner_sl_implied_risk_ratio``
    # meaningful.
    book_intended_sl: float = 0.0
    book_intended_tp: float = 0.0
    broker_sl_last_seen: float = 0.0
    broker_tp_last_seen: float = 0.0
    owner_sl_override_active: bool = False
    owner_tp_override_active: bool = False
    owner_sl_price: float = 0.0
    owner_tp_price: float = 0.0
    owner_override_first_seen_utc: str = ""
    owner_override_events: int = 0
    owner_sl_risk_exceeds_sized: bool = False
    owner_sl_implied_risk_ratio: float = 0.0


@dataclass'''
t = sub(OLD, NEW, "TradeState fields")

# ------------------------------------------------- 2. reconciler + tolerance helpers
OLD = """    def check_and_manage_trade(self, current_candle: dict) -> Optional[str]:
        \"\"\"Manage an open position: check TP hits + manage partials/scale-out."""
NEW = '''    # Relative tolerance for comparing two protective price levels.  Tight enough that
    # a one-tick move is always seen (BTCUSD @ 100k -> 0.01), loose enough to absorb
    # float round-tripping through the terminal.
    PROTECTIVE_LEVEL_REL_TOL = 1e-7

    def _protective_level_differs(self, a, b) -> bool:
        try:
            a = float(a or 0.0)
            b = float(b or 0.0)
        except (TypeError, ValueError):
            return False
        if a == 0.0 and b == 0.0:
            return False
        scale = max(abs(a), abs(b), 1.0)
        return abs(a - b) > max(scale * self.PROTECTIVE_LEVEL_REL_TOL, 1e-9)

    def _reconcile_broker_protective_levels(self, trade: TradeState, position) -> None:
        """Adopt the broker's live SL/TP as truth, recording who set them.

        Owner directive (Borhen, 2026-08-05): a protective level that differs from the
        one the book last set is a legitimate OWNER move, not an anomaly.  The book
        adopts it, stamps its provenance, and manages around it from then on.  It is
        never silently reverted -- the never-worsen guard in ``_modify_sl`` is what
        enforces that on the write side.

        The directive does not cover RISK, so this method does not decide it either.
        A WIDENED stop can push the position past the cash risk it was sized for, and
        on a prop account an unbudgeted loss is the fatal kind.  That case is WARNED
        and recorded -- never silently re-tightened (which would fight the owner) and
        never silently accepted unrecorded (which would hide a real exposure change).
        The governor's breach-flatten is untouched and remains the backstop.
        """
        try:
            broker_sl = float(getattr(position, "sl", 0.0) or 0.0)
            broker_tp = float(getattr(position, "tp", 0.0) or 0.0)
        except (TypeError, ValueError):
            return

        # Seed the book's own intent once.  SL seeds from the book's state (set in the
        # ENTRY request, so it is authoritative and catches an owner move made before
        # the first management tick).  TP seeds from the broker, because the book's
        # own TP lives in take_profit_1 or take_profit_2 depending on policy and
        # guessing wrong would manufacture a false override on the very first tick.
        if trade.book_intended_sl <= 0.0 and float(trade.stop_loss or 0.0) > 0.0:
            trade.book_intended_sl = float(trade.stop_loss)
        if trade.book_intended_tp <= 0.0 and broker_tp > 0.0:
            trade.book_intended_tp = broker_tp

        trade.broker_sl_last_seen = broker_sl
        trade.broker_tp_last_seen = broker_tp
        now_iso = datetime.now(timezone.utc).isoformat()

        # ---- stop loss ----------------------------------------------------------
        if broker_sl > 0.0 and self._protective_level_differs(broker_sl, trade.book_intended_sl):
            first_sight = not trade.owner_sl_override_active
            changed = first_sight or self._protective_level_differs(broker_sl, trade.owner_sl_price)
            previous = trade.owner_sl_price if trade.owner_sl_override_active else trade.book_intended_sl
            trade.owner_sl_override_active = True
            trade.owner_sl_price = broker_sl

            # Signed risk: only a stop on the LOSS side counts as risk.  A stop moved
            # PAST entry into profit has negative risk distance and must never warn --
            # that is exactly what the owner did on 2026-08-04.
            if trade.direction == "LONG":
                risk_distance = float(trade.entry_price or 0.0) - broker_sl
            else:
                risk_distance = broker_sl - float(trade.entry_price or 0.0)
            sized = float(trade.sl_distance or 0.0)
            ratio = (risk_distance / sized) if sized > 0 else 0.0
            exceeds = bool(sized > 0 and risk_distance > sized * (1.0 + 1e-6))
            trade.owner_sl_implied_risk_ratio = ratio
            trade.owner_sl_risk_exceeds_sized = exceeds

            # The book now reflects the owner's move.
            trade.stop_loss = broker_sl
            if trade.direction == "LONG":
                trade.sl_at_breakeven = broker_sl >= float(trade.entry_price or 0.0)
            else:
                trade.sl_at_breakeven = broker_sl <= float(trade.entry_price or 0.0)

            if changed:
                trade.owner_override_events += 1
                if not trade.owner_override_first_seen_utc:
                    trade.owner_override_first_seen_utc = now_iso
                trade.partial_close_events.append({
                    "type": "OWNER_PROTECTIVE_LEVEL_ADOPTED",
                    "time": now_iso,
                    "ticket": trade.ticket,
                    "level": "SL",
                    "book_intended_sl": trade.book_intended_sl,
                    "previous_observed_sl": previous,
                    "broker_sl": broker_sl,
                    "direction": trade.direction,
                    "entry_price": trade.entry_price,
                    "sized_sl_distance": sized,
                    "owner_sl_implied_risk_ratio": ratio,
                    "owner_sl_risk_exceeds_sized": exceeds,
                    "adopted": True,
                    "reverted": False,
                    "provenance_contract_version": "owner_manual_override_provenance_v1",
                })
                if exceeds:
                    logger.warning(
                        "OWNER STOP WIDENS RISK BEYOND SIZED AMOUNT -- ticket %s %s %s: "
                        "broker SL %.5f implies %.4fR against the %.5f sized stop distance "
                        "(entry %.5f). The book is ADOPTING it as instructed and will NOT "
                        "re-tighten. Governor breach-flatten remains the backstop.",
                        trade.ticket, self.symbol, trade.direction,
                        broker_sl, ratio, sized, float(trade.entry_price or 0.0),
                    )
                else:
                    logger.info(
                        "Owner stop adopted -- ticket %s %s: broker SL %.5f (book had %.5f), "
                        "%.4fR of the sized stop distance; within sized risk.",
                        trade.ticket, self.symbol, broker_sl,
                        trade.book_intended_sl, ratio,
                    )
        elif broker_sl > 0.0:
            # Broker agrees with the book: any prior override has been superseded by a
            # book-set level, so stop attributing the exit to the owner.
            trade.owner_sl_override_active = False
            trade.stop_loss = broker_sl

        # ---- take profit --------------------------------------------------------
        if broker_tp > 0.0 and self._protective_level_differs(broker_tp, trade.book_intended_tp):
            changed = (not trade.owner_tp_override_active) or self._protective_level_differs(
                broker_tp, trade.owner_tp_price
            )
            previous = trade.owner_tp_price if trade.owner_tp_override_active else trade.book_intended_tp
            trade.owner_tp_override_active = True
            trade.owner_tp_price = broker_tp
            if changed:
                trade.owner_override_events += 1
                if not trade.owner_override_first_seen_utc:
                    trade.owner_override_first_seen_utc = now_iso
                trade.partial_close_events.append({
                    "type": "OWNER_PROTECTIVE_LEVEL_ADOPTED",
                    "time": now_iso,
                    "ticket": trade.ticket,
                    "level": "TP",
                    "book_intended_tp": trade.book_intended_tp,
                    "previous_observed_tp": previous,
                    "broker_tp": broker_tp,
                    "adopted": True,
                    "reverted": False,
                    "provenance_contract_version": "owner_manual_override_provenance_v1",
                })
                logger.info(
                    "Owner take-profit adopted -- ticket %s %s: broker TP %.5f (book had %.5f).",
                    trade.ticket, self.symbol, broker_tp, trade.book_intended_tp,
                )
        elif broker_tp > 0.0:
            trade.owner_tp_override_active = False

    def check_and_manage_trade(self, current_candle: dict) -> Optional[str]:
        """Manage an open position: check TP hits + manage partials/scale-out.'''
t = sub(OLD, NEW, "reconciler insert")

# ------------------------------------------------- 3. call the reconciler each tick
OLD = """        trade.position_confirmed = True
        trade.current_volume = our_position.volume

        tick = self.mt5.get_tick(self.symbol)"""
NEW = """        trade.position_confirmed = True
        trade.current_volume = our_position.volume

        # The broker's SL/TP are the truth. Adopt any owner-made move BEFORE any exit
        # logic reads trade.stop_loss this tick, so every downstream decision sees the
        # protection that is actually live. (Borhen, 2026-08-05.)
        self._reconcile_broker_protective_levels(trade, our_position)

        tick = self.mt5.get_tick(self.symbol)"""
t = sub(OLD, NEW, "reconciler call")

# ------------------------------------------------- 4. never-worsen guard in _modify_sl
OLD = """            diagnostic["failure_reason"] = "position_ticket_not_found_before_modify"
            self._record_sltp_modify_diagnostic(trade=trade, diagnostic=diagnostic)
            logger.error("SL modify aborted: %s", diagnostic)
            return False
        try:
            self._runtime_halt_snapshot(
                "modify_sl","""
NEW = '''            diagnostic["failure_reason"] = "position_ticket_not_found_before_modify"
            self._record_sltp_modify_diagnostic(trade=trade, diagnostic=diagnostic)
            logger.error("SL modify aborted: %s", diagnostic)
            return False

        # NEVER write a stop worse than the one that is LIVE at the broker.
        #
        # This is the single choke point for every book-initiated SL write, so one
        # guard here covers _move_sl_to_breakeven (which had NO worsening check at
        # all), _move_sl_to_dynamic_r (whose own check compared against the book's
        # remembered stop rather than the broker's), and any future caller.
        #
        # Two independent reasons it belongs here:
        #   1. SAFETY, regardless of who set the live stop -- the book widening its
        #      own protection on an open position is never correct.
        #   2. The owner directive of 2026-08-05 -- a stop Borhen tightened by hand
        #      must survive the book's own break-even/trailing step. Before this
        #      guard, a break-even move would have reverted a manually locked-in
        #      profit back to entry.
        #
        # ``_sl_modify_reduces_or_preserves_risk`` reads ``position.sl`` (broker
        # truth) and permits setting a stop where none exists. Returning False is a
        # well-handled outcome: _move_sl_to_breakeven explicitly does NOT close the
        # position on modify failure (its BUG #28 contract).
        if not self._sl_modify_reduces_or_preserves_risk(target_position, new_sl):
            diagnostic = self._sltp_modify_diagnostic(
                request=request,
                result=None,
                modify_kind="SL",
                modify_reason=modify_reason or "modify_sl",
                attempt=0,
                positions_before=positions,
                positions_after=positions,
            )
            diagnostic["failure_reason"] = "sl_modify_would_worsen_live_broker_stop"
            diagnostic["broker_live_sl"] = float(getattr(target_position, "sl", 0.0) or 0.0)
            diagnostic["requested_sl"] = float(new_sl or 0.0)
            diagnostic["owner_sl_override_active"] = bool(
                getattr(trade, "owner_sl_override_active", False)
            )
            diagnostic["guard_contract_version"] = "never_worsen_live_broker_stop_v1"
            self._record_sltp_modify_diagnostic(trade=trade, diagnostic=diagnostic)
            if trade is not None:
                trade.partial_close_events.append({
                    "type": "SL_MODIFY_REFUSED_WOULD_WORSEN_LIVE_STOP",
                    "time": datetime.now(timezone.utc).isoformat(),
                    "ticket": ticket,
                    "requested_sl": float(new_sl or 0.0),
                    "broker_live_sl": diagnostic["broker_live_sl"],
                    "modify_reason": modify_reason or "modify_sl",
                    "owner_sl_override_active": diagnostic["owner_sl_override_active"],
                    "provenance_contract_version": "owner_manual_override_provenance_v1",
                })
            logger.warning(
                "SL modify REFUSED (would worsen the live broker stop): ticket %s %s "
                "requested %.5f but broker holds %.5f (owner_override=%s, reason=%s). "
                "Keeping the better stop.",
                ticket, self.symbol, float(new_sl or 0.0),
                diagnostic["broker_live_sl"],
                diagnostic["owner_sl_override_active"],
                modify_reason or "modify_sl",
            )
            return False
        try:
            self._runtime_halt_snapshot(
                "modify_sl",'''
t = sub(OLD, NEW, "never-worsen guard")

# ------------------------------------------------- 5. record book intent on success
OLD = """        if result.success:
            return True
        if self._retcode_no_changes(result) and self._sltp_request_already_matches_position(
            target_position,
            request,
            modify_kind="SL",
        ):
            diagnostic = self._sltp_modify_diagnostic("""
NEW = """        if result.success:
            # The book set this level itself -- record that, so the next reconcile
            # tick does not mistake the book's own move for an owner override.
            if trade is not None:
                trade.book_intended_sl = float(new_sl or 0.0)
                trade.owner_sl_override_active = False
            return True
        if self._retcode_no_changes(result) and self._sltp_request_already_matches_position(
            target_position,
            request,
            modify_kind="SL",
        ):
            diagnostic = self._sltp_modify_diagnostic("""
t = sub(OLD, NEW, "book intent SL")

# ------------------------------------------------- 6. exit provenance at close
OLD = """    def _record_close(self, reason: str):
        if self.active_trade:
            self.active_trade.partial_close_events.append({
                "type": f"CLOSE_{reason.upper()}",
                "time": datetime.now(timezone.utc).isoformat(),
            })"""
NEW = '''    def _record_close(self, reason: str):
        if self.active_trade:
            t = self.active_trade
            owner_set = bool(t.owner_sl_override_active or t.owner_tp_override_active)
            self.active_trade.partial_close_events.append({
                "type": f"CLOSE_{reason.upper()}",
                "time": datetime.now(timezone.utc).isoformat(),
                # --- exit-level provenance -------------------------------------------
                # ``broker_closed`` alone cannot distinguish a stop the BOOK set from a
                # stop a HUMAN moved -- MT5 reports DEAL_REASON_SL for both. Without
                # this block an owner-steered exit is credited to the sleeve as if it
                # were the sleeve's own performance, which silently contaminates the
                # forward record. Additive only: the existing reconciliation semantics
                # of ``reason`` are unchanged.
                "exit_level_provenance": "owner_modified" if owner_set else "book_set",
                "exit_stop_matches_book_intent": not bool(t.owner_sl_override_active),
                "owner_sl_override_active": bool(t.owner_sl_override_active),
                "owner_tp_override_active": bool(t.owner_tp_override_active),
                "book_intended_sl": float(t.book_intended_sl or 0.0),
                "book_intended_tp": float(t.book_intended_tp or 0.0),
                "broker_sl_last_seen": float(t.broker_sl_last_seen or 0.0),
                "broker_tp_last_seen": float(t.broker_tp_last_seen or 0.0),
                "owner_sl_price": float(t.owner_sl_price or 0.0),
                "owner_tp_price": float(t.owner_tp_price or 0.0),
                "owner_override_events": int(t.owner_override_events or 0),
                "owner_override_first_seen_utc": t.owner_override_first_seen_utc or "",
                "owner_sl_risk_exceeds_sized": bool(t.owner_sl_risk_exceeds_sized),
                "owner_sl_implied_risk_ratio": float(t.owner_sl_implied_risk_ratio or 0.0),
                "provenance_contract_version": "owner_manual_override_provenance_v1",
            })'''
t = sub(OLD, NEW, "exit provenance")

DST.write_bytes(t.encode("utf-8"))
print("patched OK")
print("  bytes:", DST.stat().st_size, " (was 454116, delta", DST.stat().st_size - 454116, ")")
print("  sha256:", hashlib.sha256(DST.read_bytes()).hexdigest())

# ---------------------------------------------------- 7. skip futile BE retries + false page
t2 = DST.read_bytes().decode("utf-8")
OLD7 = '''        old_stop_loss = trade.stop_loss
        for attempt in range(1, self.SL_MODIFY_MAX_ATTEMPTS + 1):
            success = self._modify_sl(
                ticket,
                trade.entry_price,
                trade=trade,
                modify_reason="sl_to_breakeven",
            )'''
NEW7 = '''        old_stop_loss = trade.stop_loss
        # If the stop that is LIVE at the broker is already at-or-better than
        # break-even, this move has nothing to do. Attempting it anyway would burn
        # three refusals against the never-worsen guard and then page the owner with
        # "broker rejection requires human investigation" -- which would be false,
        # and on an account where the owner moves his own stops it would page him
        # for doing so. Same outcome, no noise.
        live_position = next(
            (p for p in (self.mt5.get_positions(self.symbol) or []) if p.ticket == ticket),
            None,
        )
        if live_position is not None and not self._sl_modify_reduces_or_preserves_risk(
            live_position, trade.entry_price
        ):
            live_sl = float(getattr(live_position, "sl", 0.0) or 0.0)
            trade.sl_at_breakeven = True
            trade.stop_loss = live_sl
            trade.partial_close_events.append({
                "type": "SL_TO_BREAKEVEN_SKIPPED_LIVE_STOP_ALREADY_BETTER",
                "time": datetime.now(timezone.utc).isoformat(),
                "ticket": ticket,
                "breakeven_target": float(trade.entry_price or 0.0),
                "broker_live_sl": live_sl,
                "owner_sl_override_active": bool(
                    getattr(trade, "owner_sl_override_active", False)
                ),
                "provenance_contract_version": "owner_manual_override_provenance_v1",
            })
            logger.info(
                "SL->BE skipped for ticket %s %s: the live broker stop %.5f is already "
                "at or better than break-even %.5f (owner_override=%s). Keeping it.",
                ticket, self.symbol, live_sl, float(trade.entry_price or 0.0),
                bool(getattr(trade, "owner_sl_override_active", False)),
            )
            return
        for attempt in range(1, self.SL_MODIFY_MAX_ATTEMPTS + 1):
            success = self._modify_sl(
                ticket,
                trade.entry_price,
                trade=trade,
                modify_reason="sl_to_breakeven",
            )'''
n = t2.count(OLD7)
assert n == 1, f"[BE skip] expected 1 occurrence, found {n}"
DST.write_bytes(t2.replace(OLD7, NEW7, 1).encode("utf-8"))
print("BE-skip patch applied; bytes:", DST.stat().st_size,
      "sha256:", hashlib.sha256(DST.read_bytes()).hexdigest())
