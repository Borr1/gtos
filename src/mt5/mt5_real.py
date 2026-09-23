"""Real MT5 connection. Only works on Windows with MT5 terminal running.

Broker server-time offset (added 2026-04-28)
--------------------------------------------
MT5 brokers report tick / candle / deal timestamps in **broker server time**,
not UTC. redacted_account-Server 2 runs UTC+3, FTMO-Server 3 runs UTC+2, etc. The
older code at line 48 wrote ``datetime.fromtimestamp(tick.time, tz=timezone.utc)``
which silently re-labelled broker-localized seconds as UTC. Downstream
consumers that compared ``TickData.time`` to ``datetime.now(tz=timezone.utc)``
saw spurious ``+offset`` skew.

The wrapper now self-detects the broker offset on first ``get_tick`` call
(or via ``detect_broker_offset_seconds`` if a caller wires it explicitly)
and SUBTRACTS it from the broker timestamp before constructing the
timezone-aware datetime. ``TickData.time`` is now always true UTC.

The same offset applies to ``copy_rates_*`` and ``history_deals_get`` —
those still emit broker-time epochs. Existing call sites that consume
TickData.time bid/ask/spread (the dominant majority) are unaffected by
this change because they don't compare time to UTC; the few that do are
now correct.
"""

from datetime import datetime, timezone, timedelta
from typing import Optional

from .mt5_interface import (
    MT5Interface,
    TickData,
    PositionInfo,
    OrderResult,
    MAGIC_NUMBER,
    ORDER_SEND_NONE_RETCODE,
)
from src.safety.activation_token import (
    PositionsUnavailable,
    account_digest,
    enforce_broker_mutation_authorized,
    strict_positions_provider,
)

# Plausible broker-server UTC offset band for the deployed props (FTMO ~UTC+2/+3 CET/EET, redacted_account
# ~UTC+3 EET) with DST + margin. A tick-derived offset outside this band is a stale/closed-market quote
# and must NOT be latched (else the daily-loss reset window + deal queries are mis-timed all process-life).
BROKER_OFFSET_MIN_SECONDS = -3600    # -1h
BROKER_OFFSET_MAX_SECONDS = 18000    # +5h
# Re-detect the broker offset on a slow cadence so a LONG-running process self-corrects across a DST
# change (EET<->EEST on the last Sun of Mar/Oct) instead of latching the summer +3 for the whole life
# and mis-timing the daily-loss reset window after Oct 25. Re-detection is plausibility-guarded (a bad/
# stale tick is rejected, keeping the prior offset), so a periodic re-arm is safe.
BROKER_OFFSET_REDETECT_SECONDS = 6 * 3600    # 6h -> self-corrects within 6h of a DST flip


class RealMT5(MT5Interface):
    """Real MT5 connection via MetaTrader5 Python package (Windows only)."""

    def __init__(self, terminal_path: Optional[str] = None, portable: bool = False,
                 magic: int = MAGIC_NUMBER):
        self._connected = False
        self._terminal_path = terminal_path
        self._portable = bool(portable)
        # THE BROKER-SIDE IDENTITY OF THIS WORKER. Default = the armed book's magic, so every
        # existing construction site is byte-identical. A second decision surface on the SAME
        # account passes its own (see `mt5_interface.magic_for_namespace`), and the two position
        # filters below are then the ONE place that keeps the two books from seeing each other:
        # every consumer in the live book path -- `book_engine._open_risk_pct`, the same-symbol
        # guard, adoption, the out-of-universe alert, the residual-after-partial resolver --
        # reads positions through `get_positions`/`get_open_positions` and nothing else.
        self._magic = int(magic)
        self._mt5 = None
        # Broker server-time offset relative to UTC, in integer seconds.
        # Detected lazily on first successful ``get_tick`` call (avoids a
        # forced probe on connect for callers that don't need timestamp
        # accuracy). 0 = UTC broker (or detection deferred).
        self._broker_offset_seconds: int = 0
        self._broker_offset_detected: bool = False
        self._broker_offset_detected_at: float = 0.0   # time.monotonic() of the last successful detection
        self._tick_symbol_select_attempted: set[str] = set()

    def connect(self) -> bool:
        import MetaTrader5 as mt5
        self._mt5 = mt5

        kwargs = {}
        if self._terminal_path:
            kwargs["path"] = self._terminal_path
        if self._portable:
            kwargs["portable"] = True

        if not mt5.initialize(**kwargs):
            return False

        self._connected = True
        return True

    def get_broker_offset_seconds(self) -> int:
        """Return the cached broker server-time offset relative to UTC.

        Detection is lazy — if no tick has been read yet the value is 0
        (caller may pre-warm via ``detect_broker_offset_seconds`` from
        ``mt5_daemon_runtime``). Once detected, the value is cached for
        the lifetime of this wrapper instance.
        """
        return self._broker_offset_seconds

    def _detect_offset_from_tick(self, tick) -> None:
        """Lazy one-shot offset detection from a successful tick read.

        Called inside ``get_tick`` when ``self._broker_offset_detected``
        is False. Computes ``tick.time - utc_now``, rounds to nearest
        1800s (handles 30-min offsets), zero-buckets values within 60s.
        Same algorithm as ``mt5_daemon_runtime.detect_broker_offset_seconds``
        but inlined here so this module has no dependency on the runtime
        helper (avoiding a circular import at module load).
        """
        try:
            if not self._tick_has_positive_quote(tick):
                return
            broker_epoch = float(tick.time)
            utc_epoch = datetime.now(tz=timezone.utc).timestamp()
            raw = broker_epoch - utc_epoch
            rounded = round(raw / 1800.0) * 1800
            # PLAUSIBILITY GUARD (prop-breach-class): a market-closed/weekend/holiday/maintenance restart
            # returns a STALE tick whose time is hours old, so raw (= true_offset + staleness) rounds to a
            # grossly wrong bucket and would LATCH for the whole process — corrupting the daily-loss reset
            # window, decision-bar stamping, and deal-history queries (the hard-halt failure class). These
            # prop MT5 servers sit at UTC+1..+3 (CET/CEST/EET/EEST). Reject any detected offset outside a
            # sane band and DO NOT latch, so a later FRESH (open-market) tick sets it instead. (The sibling
            # mt5_daemon_runtime.detect_broker_offset_seconds guards the same way.)
            if not (BROKER_OFFSET_MIN_SECONDS <= rounded <= BROKER_OFFSET_MAX_SECONDS):
                return  # leave _broker_offset_detected False; retry on the next (hopefully fresh) tick
            self._broker_offset_seconds = 0 if abs(rounded) < 60 else int(rounded)
        except Exception:  # noqa: BLE001 — detection must never fail get_tick
            return  # do NOT latch a bad/zero offset on error; retry next tick
        self._broker_offset_detected = True
        try:
            import time as _t
            self._broker_offset_detected_at = _t.monotonic()   # stamp for the periodic DST re-detect
        except Exception:
            self._broker_offset_detected_at = 0.0

    def _repair_offset_if_tick_is_future(self, tick) -> None:
        """Recover from any too-low cached offset using a fresh broker tick.

        A periodic re-detection can encounter a stale but still plausible closed-market
        quote. For example, a two-hour-old quote from a UTC+3 server looks like UTC+1 and
        passes the broad plausibility band. A later fresh quote is then hours in the
        future *after the cached offset is subtracted*. Correct immediately instead of
        retaining that poisoned non-zero offset until the next six-hour re-detection.
        """
        if not self._broker_offset_detected:
            return
        try:
            if not self._tick_has_positive_quote(tick):
                return
            broker_epoch = float(tick.time)
            utc_epoch = datetime.now(tz=timezone.utc).timestamp()
            normalized_epoch = broker_epoch - self._broker_offset_seconds
            if normalized_epoch - utc_epoch <= 600:
                return
            raw = broker_epoch - utc_epoch
            rounded = round(raw / 1800.0) * 1800
            if not (BROKER_OFFSET_MIN_SECONDS <= rounded <= BROKER_OFFSET_MAX_SECONDS):
                return
            repaired = 0 if abs(rounded) < 60 else int(rounded)
            if repaired == self._broker_offset_seconds:
                return
            self._broker_offset_seconds = repaired
            import time as _t
            self._broker_offset_detected_at = _t.monotonic()
        except Exception:  # noqa: BLE001 - timestamp repair must never fail get_tick
            return

    def _repair_offset_if_latest_rate_is_future(self, symbol: str, rates) -> None:
        """Give a fresh tick a chance to repair a poisoned offset before conversion.

        ``get_candles`` normally does not read a tick once an offset is cached. A
        forming bar whose normalized open is materially in the future proves that the
        cached offset is too low; reading this symbol's tick activates the same guarded
        repair used by ``get_tick`` without adding a tick call to the healthy path.
        """
        try:
            if not self._broker_offset_detected or rates is None or len(rates) == 0:
                return
            latest_epoch = float(rates[-1][0])
            utc_epoch = datetime.now(tz=timezone.utc).timestamp()
            normalized_epoch = latest_epoch - self._broker_offset_seconds
            if normalized_epoch - utc_epoch > 60:
                self.get_tick(symbol)
        except Exception:  # noqa: BLE001 - timestamp repair must never fail candle reads
            return

    @staticmethod
    def _tick_has_positive_quote(tick) -> bool:
        try:
            broker_epoch = float(getattr(tick, "time", 0) or 0)
            bid = float(getattr(tick, "bid", 0.0) or 0.0)
            ask = float(getattr(tick, "ask", 0.0) or 0.0)
        except (TypeError, ValueError):
            return False
        return broker_epoch > 0 and bid > 0 and ask > 0 and ask >= bid

    def _attempt_symbol_select_for_tick(self, symbol: str) -> bool:
        if not symbol or symbol in self._tick_symbol_select_attempted:
            return False
        symbol_info = getattr(self._mt5, "symbol_info", None)
        symbol_select = getattr(self._mt5, "symbol_select", None)
        if not callable(symbol_info) or not callable(symbol_select):
            return False
        try:
            info = symbol_info(symbol)
            if info is None:
                return False
            self._tick_symbol_select_attempted.add(symbol)
            if bool(getattr(info, "visible", False)):
                return False
            return bool(symbol_select(symbol, True))
        except Exception:  # noqa: BLE001 - market-watch selection is best effort
            return False

    def disconnect(self):
        if self._connected and self._mt5:
            self._mt5.shutdown()
            self._connected = False

    def is_connected(self) -> bool:
        if not self._connected or not self._mt5:
            return False
        info = self._mt5.terminal_info()
        return info is not None

    def broker_link_connected(self) -> bool:
        """True if the terminal holds a live link to the BROKER / trade server (terminal_info().connected).

        Distinct from is_connected(), which only confirms the terminal PROCESS is up (terminal_info() is
        non-None). A terminal can be running yet DROPPED from the trade server (network blip, broker
        maintenance, session expiry) -> orders + fresh ticks/deals are impossible, but terminal-liveness
        alone judged it 'connected' (a silent trade-blind state — MACRO-RES-02). Returns False on any
        uncertainty (FAIL-SAFE: an unverifiable link is treated as down so the launcher alerts + reconnects
        rather than trading blind)."""
        try:
            if not self._connected or not self._mt5:
                return False
            info = self._mt5.terminal_info()
            if info is None:
                return False
            return bool(getattr(info, "connected", False))
        except Exception:
            return False

    def _broker_epoch_to_utc(self, broker_epoch: float) -> datetime:
        """Convert a broker-localized epoch (seconds) to a true-UTC datetime.

        Subtracts ``self._broker_offset_seconds`` so the returned datetime
        is timezone-aware UTC matching ``datetime.now(tz=timezone.utc)``.
        """
        return datetime.fromtimestamp(
            broker_epoch - self._broker_offset_seconds,
            tz=timezone.utc,
        )

    def get_tick(self, symbol: str = "XAUUSD") -> Optional[TickData]:
        tick = self._mt5.symbol_info_tick(symbol)
        if tick is None or not self._tick_has_positive_quote(tick):
            if self._attempt_symbol_select_for_tick(symbol):
                tick = self._mt5.symbol_info_tick(symbol)
        if tick is None or not self._tick_has_positive_quote(tick):
            return None
        # Offset detection: lazy on the first tick, then periodically RE-armed so a long-running process
        # SELF-CORRECTS across a DST change (a latched summer +3 would otherwise mis-time the daily-loss
        # reset window all winter). A bad/stale tick is rejected by the detector's plausibility guard, so the
        # prior offset is retained until a fresh open-market tick re-confirms it.
        import time as _t
        if self._broker_offset_detected and (
                _t.monotonic() - self._broker_offset_detected_at) > BROKER_OFFSET_REDETECT_SECONDS:
            self._broker_offset_detected = False
        if not self._broker_offset_detected:
            self._detect_offset_from_tick(tick)
        else:
            self._repair_offset_if_tick_is_future(tick)
        return TickData(
            bid=tick.bid, ask=tick.ask,
            time=self._broker_epoch_to_utc(tick.time),
            spread_cents=(tick.ask - tick.bid) * 100,
        )

    def get_candles(self, symbol: str, timeframe: int, count: int) -> list[dict]:
        if not self._broker_offset_detected:
            # Candle epochs are broker-localized too. Warm the same offset
            # detector used by get_tick() before converting bar timestamps so
            # callers that fetch candles first after a restart still receive
            # true UTC candle times.
            self.get_tick(symbol)
        rates = self._mt5.copy_rates_from_pos(symbol, timeframe, 0, count)
        if rates is None:
            return []
        self._repair_offset_if_latest_rate_is_future(symbol, rates)
        return [
            {
                "time": self._broker_epoch_to_utc(r[0]).isoformat(),
                "open": r[1], "high": r[2], "low": r[3],
                "close": r[4], "volume": r[5],
            }
            for r in rates
        ]

    def get_candles_range(self, symbol: str, timeframe: int, date_from, date_to) -> list[dict]:
        if not self._broker_offset_detected:
            self.get_tick(symbol)
        rates = self._mt5.copy_rates_range(symbol, timeframe, date_from, date_to)
        if rates is None:
            return []
        return [
            {
                "time": self._broker_epoch_to_utc(r[0]).isoformat(),
                "open": r[1], "high": r[2], "low": r[3],
                "close": r[4], "volume": r[5],
            }
            for r in rates
        ]

    def get_ticks_range(self, symbol: str, date_from: datetime, date_to: datetime) -> list[dict]:
        """Return historical bid/ask ticks for a UTC range using read-only MT5 APIs."""
        if not self._broker_offset_detected:
            self.get_tick(symbol)
        query_from = date_from + timedelta(seconds=self._broker_offset_seconds)
        query_to = date_to + timedelta(seconds=self._broker_offset_seconds)
        flags = getattr(self._mt5, "COPY_TICKS_ALL", 0)
        ticks = self._mt5.copy_ticks_range(symbol, query_from, query_to, flags)
        if ticks is None:
            return []
        rows: list[dict] = []
        for tick in ticks:
            time_msc = getattr(tick, "time_msc", None)
            if time_msc:
                ts_utc = datetime.fromtimestamp(
                    (float(time_msc) / 1000.0) - self._broker_offset_seconds,
                    tz=timezone.utc,
                )
            else:
                ts_utc = self._broker_epoch_to_utc(getattr(tick, "time", 0))
            rows.append(
                {
                    "ts_utc": ts_utc.isoformat(),
                    "time_msc": int(time_msc or 0),
                    "bid": float(getattr(tick, "bid", 0.0) or 0.0),
                    "ask": float(getattr(tick, "ask", 0.0) or 0.0),
                    "last": float(getattr(tick, "last", 0.0) or 0.0),
                    "volume": float(getattr(tick, "volume", 0.0) or 0.0),
                    "volume_real": float(getattr(tick, "volume_real", 0.0) or 0.0),
                    "flags": int(getattr(tick, "flags", 0) or 0),
                }
            )
        return rows

    def get_positions(self, symbol: str = "XAUUSD") -> list[PositionInfo]:
        if not self._broker_offset_detected:
            # Position open times are broker-localized epochs, same as ticks,
            # bars, and deals. Startup reconciliation can call get_positions()
            # before the first explicit tick read, so warm the offset here
            # before converting p.time to UTC.
            self.get_tick(symbol)
        positions = self._mt5.positions_get(symbol=symbol)
        if positions is None:
            return []
        return [
            PositionInfo(
                ticket=p.ticket, symbol=p.symbol, type=p.type,
                volume=p.volume, price_open=p.price_open,
                sl=p.sl, tp=p.tp, profit=p.profit,
                magic=p.magic, comment=p.comment,
                time=self._broker_epoch_to_utc(p.time),
            )
            for p in positions
            if p.magic == self._magic
        ]

    def get_open_positions(self) -> list[PositionInfo]:
        """ALL open book positions across symbols (MAGIC-filtered), one round-trip. Used by the live
        gross-open-risk sum for the running 4% cap. Read-only; never places/modifies."""
        if not self._broker_offset_detected:
            try:
                self.get_tick("XAUUSD")
            except Exception:
                pass
        positions = self._mt5.positions_get()
        if positions is None:
            return []
        return [
            PositionInfo(
                ticket=p.ticket, symbol=p.symbol, type=p.type,
                volume=p.volume, price_open=p.price_open,
                sl=p.sl, tp=p.tp, profit=p.profit,
                magic=p.magic, comment=p.comment,
                time=self._broker_epoch_to_utc(p.time),
            )
            for p in positions
            if p.magic == self._magic
        ]

    def get_symbol_value_per_point(self, symbol: str) -> "float | None":
        """Account-currency value per 1.0 price unit per 1.0 lot = trade_tick_value / trade_tick_size.
        None if unavailable. Cached (static per symbol). For the worst-case-stop open-risk sum."""
        cache = getattr(self, "_vpp_cache", None)
        if cache is None:
            cache = self._vpp_cache = {}
        if symbol in cache:
            return cache[symbol]
        try:
            info = self._mt5.symbol_info(symbol)
            vpp = (info.trade_tick_value / info.trade_tick_size) if (info and info.trade_tick_size) else None
        except Exception:
            vpp = None
        # Cache ONLY a trustworthy (positive) value. A transient MT5 reconnect/incomplete-sync can return
        # a symbol record with zeroed/None numeric fields -> vpp computes to 0/None; caching that would
        # poison this symbol for the whole process lifetime (the cache is membership-keyed, so it would be
        # returned forever), silently under-counting the live gross-open-risk sum and LOOSENING the 4% cap.
        # Return the bad read so the caller still skips it, but let a later good read populate the cache.
        if isinstance(vpp, (int, float)) and vpp > 0:
            cache[symbol] = vpp
        return vpp

    def get_account_balance(self) -> float:
        info = self._mt5.account_info()
        return info.balance if info else 0.0

    def get_account_login(self) -> "int | None":
        """Return the connected broker login for namespaced observability rows.

        This is deliberately a read-only convenience rather than part of order authority.  The
        MetaTrader5 package exposes ``account_info()``; callers must not guess a nonexistent
        adapter-level ``get_account_info()`` method and silently stamp every live row with ``None``.
        """
        try:
            info = self._mt5.account_info()
            login = getattr(info, "login", None) if info is not None else None
            return int(login) if login is not None else None
        except Exception:
            return None

    def get_account_equity(self) -> float:
        info = self._mt5.account_info()
        return info.equity if info else 0.0

    def get_margin_mode(self) -> str:
        info = self._mt5.account_info()
        if info and info.margin_mode == 0:
            return "netting"
        return "hedging"

    def set_activation_context(
        self,
        *,
        namespace: str | None = None,
        config_digest_sha256: str | None = None,
        require_namespace_binding: bool = False,
        require_config_digest_binding: bool = False,
    ) -> None:
        """Declare which namespace/config this adapter is running under.

        A token may bind either. A binding the token declares and this process
        cannot answer is a **denial**, not a pass, so an entrypoint that trades
        under a namespace must say so here or its own token will refuse it. F5
        sets both ``require_*`` flags: unlike legacy non-F5 callers, an unbound
        token is then also a denial. Risk-reducing requests return before these
        checks and remain available with no token at all.
        """

        self._activation_namespace = namespace or None
        self._activation_config_digest = config_digest_sha256 or None
        self._activation_require_namespace_binding = bool(require_namespace_binding)
        self._activation_require_config_digest_binding = bool(require_config_digest_binding)

    @strict_positions_provider
    def positions_for_activation(self, symbol: str = "") -> list:
        """Positions as the BROKER sees them — for the activation gate only.

        ``get_positions`` is the wrong reader for an authorization decision, in
        three ways that all point the same direction: they make a live position
        look absent, and an absent position turns a close into "new exposure".

        * It **masks a failed read as an empty list** (line 321-322:
          ``if positions is None: return []``). ``MetaTrader5.positions_get``
          signals failure with ``None``, so a transient IPC/terminal hiccup was
          indistinguishable from a flat account. This method raises
          ``PositionsUnavailable`` instead, which the gate treats as *unverified*
          and therefore lets the close through.
        * It **filters by magic** (line 333). The gate's question is "does this
          ticket exist at the broker", not "does this book own it" — a position
          adopted from an earlier deployment, opened by hand, or carrying a
          changed magic must still be closable.
        * It is **called with the request's symbol**, so a broker-suffixed or
          mis-resolved symbol could hide the position. This reads the whole
          account in one round-trip; ``symbol`` is accepted and ignored to keep
          the provider signature.

        Returns the raw broker records. The gate reads ``ticket``/``type``/
        ``volume``/``sl`` off them by attribute, exactly as it does for
        ``PositionInfo``, so no conversion is needed — and no conversion means
        no second place for a filter to reappear.
        """

        module = self._mt5
        if module is None:
            raise PositionsUnavailable("MT5 module not initialised")
        try:
            positions = module.positions_get()
        except Exception as exc:  # noqa: BLE001 — surface as unavailability, not a crash
            raise PositionsUnavailable(f"positions_get raised: {exc!r}") from exc
        if positions is None:
            raise PositionsUnavailable("positions_get returned None — the broker read failed")
        return list(positions)

    def account_login_sha256(self) -> "str | None":
        """The connected account's login digest, using the same convention the
        profiles carry in ``broker_profile.expected_account.login_sha256``.
        Cached: the login cannot change without a reconnect."""

        cached = getattr(self, "_account_login_sha256", None)
        if cached:
            return cached
        module = getattr(self, "_mt5", None)
        if module is None:
            return None
        try:
            info = module.account_info()
            login = getattr(info, "login", None) if info is not None else None
        except Exception:  # noqa: BLE001 — identity unavailable is a denial, not a crash
            return None
        if not login:
            return None
        digest = account_digest(login)
        self._account_login_sha256 = digest
        return digest

    def order_send(self, request: dict) -> OrderResult:
        # THE ACTIVATION CHOKE POINT.
        #
        # Every broker mutation the engine performs arrives here: execution.py's
        # four direct sites, its one `executor.submit(self.mt5.order_send, ...)`
        # site (invisible to any AST census keyed on a Call node, C2 — and
        # covered automatically by a check inside the callee), and anything
        # added later. Exposure-increasing requests need a valid activation
        # token for THIS account; risk-reducing ones never do, so an expired
        # token can never trap the account in an open position.
        #
        # The provider is `positions_for_activation`, NOT `get_positions`: the
        # latter masks a failed broker read as `[]`, which made a close look
        # like new exposure and refused it — the never-strand invariant failing
        # in exactly the state it exists for (B101).
        enforce_broker_mutation_authorized(
            request,
            account_login_sha256=self.account_login_sha256(),
            positions_provider=self.positions_for_activation,
            namespace=getattr(self, "_activation_namespace", None),
            config_digest_sha256=getattr(self, "_activation_config_digest", None),
            require_namespace_binding=getattr(
                self, "_activation_require_namespace_binding", False
            ),
            require_config_digest_binding=getattr(
                self, "_activation_require_config_digest_binding", False
            ),
        )
        result = self._mt5.order_send(request)
        if result is None:
            # Not TRADE_RETCODE_DONE. Callers must backoff; never stamp disk
            # closed from this wrapper (WEEK-STUDY-4 ghost-10011 close storm).
            return OrderResult(retcode=ORDER_SEND_NONE_RETCODE, order=0, volume=0, price=0,
                               comment="MT5 returned None")
        return OrderResult(
            retcode=result.retcode, order=result.order,
            volume=result.volume, price=result.price,
            comment=result.comment,
            deal=getattr(result, "deal", None),
            request_id=getattr(result, "request_id", None),
            retcode_external=getattr(result, "retcode_external", None),
        )

    def get_history_deals(self, from_date: datetime, to_date: datetime,
                          symbol: str = "XAUUSD") -> list[dict] | None:
        if not self._broker_offset_detected:
            self.get_tick(symbol)
        query_from = from_date + timedelta(seconds=self._broker_offset_seconds)
        query_to = to_date + timedelta(seconds=self._broker_offset_seconds)
        deals = self._mt5.history_deals_get(query_from, query_to, group=f"*{symbol}*")
        if deals is None:
            return None
        # Returns ``time`` as a UTC-aware datetime (broker offset subtracted via
        # ``_broker_epoch_to_utc``) and adds ``position_id`` + ``entry`` fields
        # so callers can match deals to a specific trade and distinguish opens
        # (entry==0, DEAL_ENTRY_IN) from closes (entry==1, DEAL_ENTRY_OUT).
        # Used by orchestrator._finalize_exit on broker_closed events to
        # recover the actual close price/time when MT5 (TP/SL/external) has
        # already closed the position before the orchestrator's M15 detection.
        return [
            {
                "ticket": d.ticket,
                "order": d.order,
                "position_id": getattr(d, "position_id", 0),
                "entry": getattr(d, "entry", 0),
                "time": self._broker_epoch_to_utc(d.time),
                "type": d.type,
                "volume": d.volume,
                "price": d.price,
                "profit": d.profit,
                "commission": getattr(d, "commission", None),
                "swap": getattr(d, "swap", None),
                "fee": getattr(d, "fee", None),
                "reason": getattr(d, "reason", None),
                "external_id": getattr(d, "external_id", None),
                "magic": d.magic,
                "comment": d.comment,
            }
            for d in deals
        ]

    def get_account_history_deals(self, from_date: datetime, to_date: datetime) -> list[dict]:
        """ALL realized deals across EVERY symbol in [from_date, to_date] (NO symbol-group filter, unlike
        get_history_deals). Used by the book governor to reconstruct the server-day start BALANCE
        (= current balance - realized closed P&L since the reset-window boundary) so the daily-loss
        baseline excludes floating P&L and survives a mid-day restart. Read-only; never places/modifies.
        ``time`` is UTC-aware (broker offset removed); ``entry``==1 marks a close (DEAL_ENTRY_OUT)."""
        if not self._broker_offset_detected:
            try:
                self.get_tick("XAUUSD")
            except Exception:
                pass
        query_from = from_date + timedelta(seconds=self._broker_offset_seconds)
        query_to = to_date + timedelta(seconds=self._broker_offset_seconds)
        deals = self._mt5.history_deals_get(query_from, query_to)
        # MT5 returns None on a FETCH ERROR but an empty tuple () on a genuine no-deals window. Propagate
        # the error as None so the governor's day-start-balance reconstruction FAILS CLOSED (blocks new
        # entries) instead of mistaking a failed fetch for "zero realized P&L" and trusting a wrong daily
        # baseline (the masking that defeats the fail-closed). Genuine no-deals -> [] -> realized 0.
        if deals is None:
            return None
        return [
            {
                "ticket": d.ticket,
                "order": getattr(d, "order", None),
                "position_id": getattr(d, "position_id", 0),
                "entry": getattr(d, "entry", 0),
                "time": self._broker_epoch_to_utc(d.time),
                "type": d.type,
                "volume": d.volume,
                "price": d.price,
                "profit": d.profit,
                "commission": getattr(d, "commission", None),
                "swap": getattr(d, "swap", None),
                "fee": getattr(d, "fee", None),
                "magic": d.magic,
                "comment": d.comment,
            }
            for d in deals
        ]
