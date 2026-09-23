"""UltimateBookLiveEngine — generation -> admission, default-off, exception-isolated.

Per book evaluation (driven on H4 closes by the orchestrator seam or the book-owner driver):
  1. run the ACTIVE sleeve generators across their on-surface symbols on the latest CLOSED bars
     -> list[TradeIntent] (the validated edge; sleeve-tagged), capturing each symbol's live price ctx;
  2. build the GovernorState from live equity + persisted high-water/day-anchor;
  3. call bridge.evaluate_vnext_ultimate_book_admission(config, intents, governor_state) -> decision
     (the triple-gate inside the bridge means: gates OFF -> shadow-only would_units, ZERO realized
     risk; gates ON + broad-selector clear -> realized_units carry the sized risk_pct_per_trade).
The order_router (separate, the FULL V4 route) consumes realized_units + the intents and places the
per-symbol orders. This engine NEVER places an order and NEVER raises into the caller (any failure ->
a safe no-op decision) so the live decision path is unaffected when the book errors or is off.
"""
from __future__ import annotations

import os
from datetime import datetime, timedelta, timezone
from typing import Any, Optional

# MT5 timeframe constant -> bar interval in minutes (book uses M1/M15/H1/H4/D1).
_TF_MINUTES = {1: 1, 5: 5, 15: 15, 30: 30, 16385: 60, 16388: 240, 16408: 1440}

from .bar_provider import get_closed_bars, candles_to_bars, decision_day_of, enough
from .governor_state import GovernorStateBuilder
from .running_conviction_state import RunningConvictionLedger
from .bridge import (
    DEFAULT_CONFIG as _BRIDGE_DEFAULTS,
    config_bool_value,
    evaluate_vnext_ultimate_book_admission,
)
from .sleeves.registry import active_specs
from .symbol_map import build_broker_symbol_resolver
from .admission import StressDeriskState, compute_stress_derisk_state, resolve_market_expansion_sleeves
from .edge_reconciler import closed_book_deals


def _candidate_book_sleeves(config: dict) -> tuple[str, ...]:
    raw = config.get(
        "ultimate_book_candidate_book_sleeves",
        _BRIDGE_DEFAULTS.get("ultimate_book_candidate_book_sleeves", []),
    )
    if raw is None:
        return ()
    if isinstance(raw, str):
        return (raw,) if raw else ()
    if isinstance(raw, (list, tuple, set)):
        return tuple(str(item) for item in raw if str(item))
    return ()


def _market_expansion_sleeves(config: dict) -> tuple[str, ...]:
    raw = config.get(
        "ultimate_book_market_expansion_sleeves",
        _BRIDGE_DEFAULTS.get("ultimate_book_market_expansion_sleeves", []),
    )
    if raw is None:
        explicit = ()
    elif isinstance(raw, str):
        explicit = (raw,) if raw else ()
    elif isinstance(raw, (list, tuple, set)):
        explicit = tuple(str(item) for item in raw if str(item))
    else:
        explicit = ()
    policy = str(config.get(
        "ultimate_book_market_expansion_policy",
        _BRIDGE_DEFAULTS.get("ultimate_book_market_expansion_policy", "explicit_allowlist"),
    ) or "explicit_allowlist")
    resolved, error = resolve_market_expansion_sleeves(policy=policy, explicit_sleeves=explicit)
    return () if error else resolved


class UltimateBookLiveEngine:
    def __init__(self, config: dict, mt5, repo_root: str, namespace: str = "ftmo_primary",
                 account: str = "A", bar_count: int = 260, broker_symbol=None):
        self.config = config or {}
        self._mt5 = mt5
        self._account = account
        self._bar_count = bar_count
        # Governor anchoring (broker-correct, config-overridable; deploy defaults below):
        #  - static_initial_balance: the broker max-DD floor is STATIC from the initial balance
        #    (FTMO/FN 100k => fixed 90k floor); the wall is pinned to this reference (max_dd_reference_equity)
        #    and BYPASSES the trailing high-water entirely — high_water is kept only as a >=equity invariant.
        #  - daily_reset_offset_hours: the STATIC fallback only. The reset window is resolved per
        #    account at runtime; see reset_rule below and GovernorStateBuilder._effective_offset_h.
        #  - reset_rule: THE ACCOUNT'S OWN daily-loss reset calendar, corrected 2026-07-26 (B56).
        #    The two firms do not share a rule and the difference is not cosmetic:
        #      redacted_account resets at 00:00 SERVER time (GMT+2/+3) -> no rule, the detected offset is it.
        #      FTMO       resets at 00:00 CE(S)T, which is NOT its server clock. FTMO's MT5 server
        #                 runs the US DST calendar while CE(S)T runs the EU one, so server midnight
        #                 is 1 h early normally and 2 h early for ~4 weeks a year.
        #    Sourced from the profile this account already ships -- the live FTMO profile
        #    config/profiles/operator_profile.yaml:87 declares
        #    `prop_safe_selector_daily_reset_timezone: Europe/Prague` and :104 records the firm's
        #    rule verbatim (`daily_reset_time: 00:00 CE(S)T`). Both FTMO profiles are
        #    decision-contract-bound (H1), so this READS the key rather than adding one; an account
        #    whose profile is silent (redacted_account.yaml) keeps server midnight, which is its rule.
        _gov_init_bal = self.config.get("governor_static_initial_balance", 100000.0)
        _gov_reset_off = self.config.get("governor_daily_reset_offset_hours", 3.0)
        _gov_reset_rule = (self.config.get("governor_daily_reset_rule")
                           or self.config.get("prop_safe_selector_daily_reset_timezone")
                           or None)
        self._governor = GovernorStateBuilder(
            repo_root, namespace=namespace,
            static_initial_balance=_gov_init_bal, daily_reset_offset_hours=_gov_reset_off,
            offset_provider=self._live_broker_offset_hours,
            reset_rule=_gov_reset_rule)
        # leak-free RUNNING per-day conviction count store (recovers the validated full-day Kelly-lite
        # convention without lookahead; engine-gated by ultimate_book_kelly_running_count, default OFF).
        self._running_conviction = RunningConvictionLedger(repo_root, namespace=namespace)
        # canonical (registry on_surface) -> broker mt5_symbol for the bar fetch. The caller (owner)
        # passes a resolver built from the merged profile; default identity for configs without an
        # instruments map (metals/crypto are identity anyway).
        self._broker_symbol = broker_symbol or build_broker_symbol_resolver(self.config)
        self._last_generation_telemetry: dict[str, object] = {}
        self._last_generation_skips: list[dict] = []
        self._stress_cache = None   # (server_date_key, StressDeriskState) — recomputed once per server-day

    def _stress_derisk_state(self, now):
        """Realized prior-day state for the reactive temporal de-risk overlay (consecutive-loss-day ladder
        + co-loss breaker), computed ONCE per server-day from the broker's closed BOOK deals and cached.
        Returns None when the overlay is OFF or no raw broker module is available (mocks). On real-broker
        read failure, fail safe to maximum reactive derisk instead of silently widening risk.
        Leak-free: compute_stress_derisk_state excludes today's in-progress server-day."""
        if not config_bool_value(
            self.config.get(
                "ultimate_book_stress_derisk",
                _BRIDGE_DEFAULTS.get("ultimate_book_stress_derisk", False),
            ),
            _BRIDGE_DEFAULTS.get("ultimate_book_stress_derisk", False),
        ):
            return None
        try:
            date_key = self.reset_window_date(now)
        except Exception:
            date_key = None
        cached = self._stress_cache
        if cached is not None and date_key is not None and cached[0] == date_key:
            return cached[1]
        state = None
        raw = None
        try:
            raw = getattr(self._mt5, "_mt5", None)   # the underlying MetaTrader5 module (None on mocks)
            if raw is not None:
                deals = closed_book_deals(raw, now, hours=192)   # 8 days: 5 trailing + margin
                try:
                    off = float(self._mt5.get_broker_offset_seconds()) / 3600.0
                except Exception:
                    off = float(self.config.get("governor_daily_reset_offset_hours", 3.0) or 0.0)
                state = compute_stress_derisk_state(deals, now, offset_hours=off)
        except Exception:
            if raw is not None:
                state = StressDeriskState(consecutive_loss_days=2, trailing_neg_frac=1.0)
            else:
                state = None
        self._stress_cache = (date_key, state)
        return state

    def _live_broker_offset_hours(self):
        """The live broker server-time offset in HOURS for the governor's DST-correct reset window, or None
        when the mt5 does not expose it (mocks) / before first detection (returns 0 -> the governor's band
        guard falls back to the static config offset until a real offset is detected from a live tick)."""
        try:
            fn = getattr(self._mt5, "get_broker_offset_seconds", None)
            if not callable(fn):
                return None
            secs = fn()
            return (float(secs) / 3600.0) if secs is not None else None
        except Exception:
            return None

    def _active_sleeve_names(self) -> set:
        """The sleeves in the ACTIVE book (effective registry), read with the SAME include flags
        convention the sizing path uses, so GENERATION, SIZING, and the Kelly conviction count share one
        source of truth. DF-1 fix: a sleeve dropped from the book (clean_3 when include_clean3=False) must
        not GENERATE — otherwise its phantom firing still inflates the Kelly-lite conviction count and
        over-sizes the real units even though it can never be sized or placed."""
        from .admission import effective_registry
        inc3 = config_bool_value(
            self.config.get("ultimate_book_include_clean3",
                            _BRIDGE_DEFAULTS.get("ultimate_book_include_clean3", True)),
            _BRIDGE_DEFAULTS.get("ultimate_book_include_clean3", True),
        )
        inc4 = config_bool_value(
            self.config.get("ultimate_book_include_clean4",
                            _BRIDGE_DEFAULTS.get("ultimate_book_include_clean4", False)),
            _BRIDGE_DEFAULTS.get("ultimate_book_include_clean4", False),
        )
        inc_candidates = config_bool_value(self.config.get(
            "ultimate_book_include_candidate_book",
            _BRIDGE_DEFAULTS.get("ultimate_book_include_candidate_book", False),
        ), _BRIDGE_DEFAULTS.get("ultimate_book_include_candidate_book", False))
        inc_expansion = config_bool_value(self.config.get(
            "ultimate_book_include_market_expansion_book",
            _BRIDGE_DEFAULTS.get("ultimate_book_include_market_expansion_book", False),
        ), _BRIDGE_DEFAULTS.get("ultimate_book_include_market_expansion_book", False))
        candidate_sleeves = _candidate_book_sleeves(self.config)
        expansion_sleeves = _market_expansion_sleeves(self.config)
        return set(effective_registry(
            include_clean3=inc3,
            include_clean4=inc4,
            include_candidate_book=inc_candidates,
            candidate_book_sleeves=candidate_sleeves or None,
            include_market_expansion_book=inc_expansion,
            market_expansion_sleeves=expansion_sleeves or None,
        ).keys())

    # ---------------- intent generation ----------------
    @staticmethod
    def _normalize_future_bar_times(
        times: list[datetime],
        *,
        now: datetime,
        interval_minutes: int | None,
    ) -> tuple[list[datetime], int | None]:
        """Repair broker-local bar timestamps that slipped through as UTC.

        The MT5 wrapper normally subtracts the broker offset. If a live worker
        starts with a bad zero offset, the latest "closed" bar can appear hours
        in the future and trigger early placement. When the skew is a plausible
        whole/half-hour broker offset, shift the full aligned time series back.
        Otherwise leave it unchanged so the future-bar fail-safe can skip it.
        """
        if not times or not interval_minutes:
            return times, None
        try:
            ref_now = now if now.tzinfo else now.replace(tzinfo=timezone.utc)
            ref_now = ref_now.astimezone(timezone.utc)
            latest = times[-1]
            if latest.tzinfo is None:
                latest = latest.replace(tzinfo=timezone.utc)
            latest = latest.astimezone(timezone.utc)
            bar_close = latest + timedelta(minutes=int(interval_minutes))
            future_seconds = (bar_close - ref_now).total_seconds()
            if future_seconds <= 60:
                return times, None
            max_fresh_seconds = max(120, 2 * int(interval_minutes) * 60)
            # Try real broker-server offsets, not the variable distance from leaked close to now.
            # Otherwise a late restart can subtract "just enough" to make a broker-local bar look
            # fresh while still stamping the wrong decision bar.
            for offset in range(1800, (5 * 3600) + 1, 1800):
                shifted = [
                    (t if t.tzinfo else t.replace(tzinfo=timezone.utc)).astimezone(timezone.utc)
                    - timedelta(seconds=offset)
                    for t in times
                ]
                shifted_close = shifted[-1] + timedelta(minutes=int(interval_minutes))
                future_after_shift = (shifted_close - ref_now).total_seconds()
                if future_after_shift > 0:
                    continue
                if (ref_now - shifted_close).total_seconds() <= max_fresh_seconds:
                    return shifted, offset
        except Exception:
            return times, None
        return times, None

    def _generate_intents(self, tags=None, now: Optional[datetime] = None) -> tuple[list, list[dict]]:
        now = now or datetime.now(timezone.utc)
        intents: list = []
        meta: list[dict] = []
        generation_skips: list[dict] = []
        # cache bars per (symbol, timeframe, count) so long-warmup candidates cannot be starved by a
        # shorter prior fetch on the same symbol/timeframe.
        bar_cache: dict[tuple[str, int, int], tuple[list, list]] = {}
        active_sleeves = self._active_sleeve_names()   # DF-1: only generate sleeves in the active book
        include_candidate_book = config_bool_value(self.config.get(
            "ultimate_book_include_candidate_book",
            _BRIDGE_DEFAULTS.get("ultimate_book_include_candidate_book", False),
        ), _BRIDGE_DEFAULTS.get("ultimate_book_include_candidate_book", False))
        include_market_expansion_book = config_bool_value(self.config.get(
            "ultimate_book_include_market_expansion_book",
            _BRIDGE_DEFAULTS.get("ultimate_book_include_market_expansion_book", False),
        ), _BRIDGE_DEFAULTS.get("ultimate_book_include_market_expansion_book", False))
        candidate_sleeves = _candidate_book_sleeves(self.config)
        expansion_sleeves = _market_expansion_sleeves(self.config)
        generation = {
            "active_spec_count": 0,
            "active_symbol_slot_count": 0,
            "profile_supported_symbol_slot_count": 0,
            "broker_unsupported_symbol_slot_count": 0,
            "broker_unsupported_unique_symbols": [],
            "broker_unsupported_skips": [],
        }
        unsupported_seen: set[str] = set()
        for spec in active_specs(
            tags,
            include_candidate_book=include_candidate_book,
            candidate_book_sleeves=candidate_sleeves or None,
            include_market_expansion_book=include_market_expansion_book,
            market_expansion_sleeves=expansion_sleeves or None,
        ):
            if spec.tag not in active_sleeves:
                continue   # sleeve dropped from the active book -> no phantom generation/conviction
            generation["active_spec_count"] += 1
            for symbol in spec.on_surface:
                generation["active_symbol_slot_count"] += 1
                supports = getattr(self._broker_symbol, "supports", None)
                if callable(supports) and not supports(symbol):
                    skip = {
                        "symbol": symbol,
                        "sleeve": spec.tag,
                        "cluster": spec.cluster,
                        "timeframe": spec.timeframe,
                        "reason": "profile_missing_instrument_config",
                    }
                    generation["broker_unsupported_symbol_slot_count"] += 1
                    unsupported_seen.add(symbol)
                    skips = generation["broker_unsupported_skips"]
                    if isinstance(skips, list) and len(skips) < 64:
                        skips.append(dict(skip))
                    generation_skips.append(skip)
                    continue
                generation["profile_supported_symbol_slot_count"] += 1
                broker_sym = self._broker_symbol(symbol)   # canonical -> broker for ALL fetches
                primary_count = max(int(self._bar_count), int(getattr(spec, "bar_count", 0) or 0))
                key = (symbol, spec.timeframe, primary_count)
                if key not in bar_cache:
                    # fetch under the BROKER name; meta + intent.symbol stay canonical for placement
                    bar_cache[key] = get_closed_bars(self._mt5, broker_sym, spec.timeframe, primary_count)
                bars, times = bar_cache[key]
                if not bars or not enough(bars, spec.cluster):
                    continue
                # DECISION-BAR RECENCY (chronological guard): the cycle is triggered by ONE reference
                # symbol's bar close, but each sleeve evaluates its OWN symbol's latest closed bar. If that
                # bar is grossly stale — the symbol's market is closed/holiday, its bar did not advance at
                # this trigger, or this is a cold post-restart read — acting on it is the ref-vs-sleeve
                # chronological hazard (e.g. trading a frozen index bar). Skip a bar whose close is older
                # than ~2 intervals. Fail-open if the interval is unknown.
                ivl = _TF_MINUTES.get(spec.timeframe)
                repaired_offset = None
                if ivl and times:
                    try:
                        times, repaired_offset = self._normalize_future_bar_times(
                            times,
                            now=now,
                            interval_minutes=ivl,
                        )
                        if repaired_offset:
                            bar_cache[key] = (bars, times)
                        bar_close = times[-1] + timedelta(minutes=ivl)
                        if (bar_close - now).total_seconds() > 0:
                            generation_skips.append({
                                "symbol": symbol,
                                "sleeve": spec.tag,
                                "reason": "future_decision_bar_time",
                                "decision_bar_iso": times[-1].isoformat(),
                                "bar_close_utc": bar_close.isoformat(),
                                "now_utc": now.isoformat(),
                            })
                            continue
                        if (now - bar_close).total_seconds() > 2 * ivl * 60:
                            continue
                    except Exception:
                        pass
                # optional SECONDARY feed (e.g. M1 for the vp volume profile); cached per (symbol, aux_tf)
                aux_bars, aux_times = None, None
                if spec.aux_timeframe and spec.aux_count > 0:
                    akey = (symbol, spec.aux_timeframe, spec.aux_count)
                    if akey not in bar_cache:
                        bar_cache[akey] = get_closed_bars(
                            self._mt5, broker_sym, spec.aux_timeframe, spec.aux_count)
                    aux_bars, aux_times = bar_cache[akey]
                    if aux_times and repaired_offset:
                        aux_times = [
                            (t if t.tzinfo else t.replace(tzinfo=timezone.utc)).astimezone(timezone.utc)
                            - timedelta(seconds=repaired_offset)
                            for t in aux_times
                        ]
                        bar_cache[akey] = (aux_bars, aux_times)
                day = decision_day_of(times[-1])
                try:
                    # bar_time = the decision bar's UTC datetime; bar_times = the full aligned series
                    # (JPY session logic); aux_bars/aux_times = the secondary feed (vp M1). Each
                    # generator reads only what it needs (the rest tolerate the extra kwargs via **_).
                    intent = spec.generator(symbol, bars, day, bar_time=times[-1], bar_times=times,
                                            aux_bars=aux_bars, aux_times=aux_times,
                                            runtime_now=now)
                except Exception:
                    intent = None     # a single sleeve error never kills the batch
                if intent is None:
                    continue
                intents.append(intent)
                meta.append({"symbol": symbol, "timeframe": spec.timeframe, "tag": spec.tag,
                             "last_close": bars[-1].c, "decision_day": day,
                             # the decision bar's UTC timestamp — the idempotency key granularity so a
                             # continuously-ticking launcher places each (sleeve, symbol, bar) ONCE.
                             "decision_bar_iso": times[-1].isoformat()})
        generation["broker_unsupported_unique_symbols"] = sorted(unsupported_seen)
        self._last_generation_telemetry = generation
        self._last_generation_skips = generation_skips
        return intents, meta

    # ---------------- equity / open-risk ----------------
    def _equity(self) -> Optional[float]:
        try:
            eq = self._mt5.get_account_equity()
            return float(eq) if isinstance(eq, (int, float)) and eq > 0 else None
        except Exception:
            return None

    def _governor_limits(self):
        """Build the governor limits from config (operator-tunable risk caps) while preserving the
        env-driven derisk_mode (band/smooth). Previously these YAML keys were INERT — the limits came only
        from DEFAULT_LIMITS, so editing config/agent_config.yaml did nothing (a latent safety footgun: an
        operator who tightened the gross cap or soft stop in YAML would silently get no effect). Current
        YAML values equal the dataclass defaults, so wiring is behavior-neutral until an operator changes
        them. derisk_mode still comes from GTOS_UB_DERISK_MODE so the smooth activation is unaffected."""
        from .admission import GovernorLimits
        d = GovernorLimits()

        def _g(key, default):
            try:
                v = self.config.get(key, None)
                return float(v) if v is not None else float(default)
            except (TypeError, ValueError):
                return float(default)
        return GovernorLimits(
            soft_daily_stop_pct=_g("ultimate_book_soft_daily_stop_pct", d.soft_daily_stop_pct),
            hard_daily_limit_pct=d.hard_daily_limit_pct,
            max_dd_limit_pct=d.max_dd_limit_pct,
            max_dd_entry_block_pct=_g(
                "ultimate_book_max_dd_entry_block_pct",
                self.config.get("ultimate_book_flatten_maxdd_pct", d.max_dd_entry_block_pct),
            ),
            derisk_start_dd_pct=_g("ultimate_book_derisk_start_dd_pct", d.derisk_start_dd_pct),
            gross_open_risk_cap_pct=_g("ultimate_book_gross_open_risk_cap_pct", d.gross_open_risk_cap_pct),
            # DF-6: derisk_mode was env-ONLY (GTOS_UB_DERISK_MODE), invisible to a YAML config audit and
            # fragile if .env is absent/reset. Read env FIRST (preserves the live .env=smooth), then fall
            # back to the YAML key, then "band". So the 2.0% dial's mandatory smooth guard is now declarable
            # in config, not solely an env var — and the admit_and_size interlock still fails closed on any
            # non-smooth value.
            derisk_mode=(os.environ.get("GTOS_UB_DERISK_MODE")
                         or self.config.get("ultimate_book_derisk_mode", "band")),
            # OPS-03 profit-target protect (owner: de-risk hard, keep trading once the challenge target hits)
            profit_target_pct=_g("ultimate_book_profit_target_pct", d.profit_target_pct),
            profit_target_derisk_mult=_g("ultimate_book_profit_target_derisk_mult", d.profit_target_derisk_mult),
        )

    @staticmethod
    def _joint_daily_limits(base, gs):
        """JOINT daily-loss gate: tighten the gross-open-risk cap so the day's ALREADY-REALIZED loss plus
        the worst-case NEW open stop cannot breach the -5% prop daily limit. The soft -3% stop and the 4%
        gross cap were INDEPENDENT, so worst-case = -3% realized + -4% open = -7% > the -5% limit (a
        prop-breach path). This shrinks the new-entry gross cap as the day's loss grows (and -> 0 near the
        limit); it NEVER widens it, so the validated full-size envelope (realized ~0) is unchanged."""
        from dataclasses import replace
        try:
            realized_loss = max(0.0, -float(getattr(gs, "realized_today_pct", 0.0) or 0.0))
            hard = float(getattr(base, "hard_daily_limit_pct", 0.05) or 0.05)
            buffer = 0.005   # keep worst-case daily loss a touch inside the hard limit
            room = max(0.0, hard - realized_loss - buffer)
            dyn_gross = min(float(base.gross_open_risk_cap_pct), room)
            if dyn_gross < float(base.gross_open_risk_cap_pct) - 1e-12:
                return replace(base, gross_open_risk_cap_pct=dyn_gross)
        except Exception:
            pass
        return base

    def reset_window_date(self, now_utc: Optional[datetime] = None) -> str:
        """The governor's offset-aware reset-window (server-local) date string, for provenance stamping
        consistent with the daily baseline (NOT a pure-UTC date)."""
        return self._governor.reset_window_date(now_utc)

    def _deal_capable(self) -> bool:
        """The live RealMT5 exposes balance + account-wide deal history; a bare test/mock mt5 may not.
        Only FAIL CLOSED on a missing daily baseline when the broker CAN supply it — so mocked mt5 keep
        the legacy equity-anchor path and are not spuriously blocked."""
        return (callable(getattr(self._mt5, "get_account_balance", None))
                and callable(getattr(self._mt5, "get_account_history_deals", None)))

    def _open_risk_pct(self, equity: float) -> float:
        """Live gross open risk = sum of worst-case-stop loss over CURRENTLY-OPEN book positions, as a
        fraction of equity, for the running 4% gross cap (the cap was previously inert because this
        defaulted to 0.0). Formula matches monitor_books.py: vol*|entry-sl|*value_per_point.

        FAIL-SAFE: test/mocked MT5 without accessors keeps legacy 0.0, but when a broker exposes open
        positions and any live risk input is unreadable, return the configured gross cap so entry
        admission fails closed instead of widening headroom at the drawdown wall."""
        try:
            if not equity or equity <= 0:
                return 0.0
            fail_closed_value = float(
                self.config.get("ultimate_book_gross_open_risk_cap_pct", 0.04) or 0.04
            )
            get_pos = getattr(self._mt5, "get_open_positions", None)
            vpp_fn = getattr(self._mt5, "get_symbol_value_per_point", None)
            if not callable(get_pos):
                return 0.0
            if not callable(vpp_fn):
                positions = get_pos() or []
                return fail_closed_value if positions else 0.0
            total = 0.0
            for p in (get_pos() or []):
                sl = getattr(p, "sl", 0.0) or 0.0
                po = getattr(p, "price_open", 0.0) or 0.0
                if not sl or not po:
                    return fail_closed_value
                vpp = vpp_fn(getattr(p, "symbol", None))
                if not vpp:
                    return fail_closed_value
                total += float(getattr(p, "volume", 0.0) or 0.0) * abs(po - sl) * float(vpp)
            return max(0.0, total / equity)
        except Exception:
            return float(self.config.get("ultimate_book_gross_open_risk_cap_pct", 0.04) or 0.04)

    # ---------------- open-position breach protection (MACRO-EMRG-03) ----------------
    def compute_governor_state(self, now_utc: Optional[datetime] = None):
        """Cheap GovernorState snapshot for the per-tick breach check (no generation/admission). Reuses the
        EXACT daily-baseline + DD primitives evaluate() uses, so the flatten check cannot diverge from the
        entry-side governor. Returns None when equity is unreadable or the daily baseline is untrustworthy
        on a deal-capable broker (FAIL-SAFE: an uncertain state must NOT trigger a flatten). NEVER raises."""
        now = now_utc or datetime.now(timezone.utc)
        try:
            eq = self._equity()
            if eq is None:
                return None
            dsb = self._governor.reconstruct_day_start_balance(self._mt5, now)
            if dsb is None and self._deal_capable():
                return None
            return self._governor.build(
                equity=eq, day_start_balance=dsb, open_risk_pct=self._open_risk_pct(eq), now_utc=now,
                circuit_breaker=config_bool_value(
                    self.config.get("ultimate_book_operator_circuit_breaker", False),
                    False,
                ))
        except Exception:
            return None

    def breach_flatten_check(self, now_utc: Optional[datetime] = None) -> Optional[dict]:
        """LAST-RESORT per-tick verdict: should OPEN positions be FLATTENED and new entries blocked because
        the account is near the prop-fatal daily-loss or the STATIC max-DD floor? This is the missing
        OPEN-position safety tier — the governor's soft/hard stops and de-risk band are ENTRY-side only.

        Default OFF (ultimate_book_flatten_on_breach) -> returns None, so existing configs/tests are
        unchanged; the LIVE config enables it. Thresholds sit BELOW the account-fatal limits (daily flatten
        at -4% vs the -5% prop limit; max-DD flatten at 9% vs the -10%/90k floor) so positions close with a
        buffer for slippage, NOT at the wall. FAIL-SAFE: an unassessable state (gs None) returns None
        (never flatten on uncertain data). Uses the same governor primitives as evaluate() (no divergence).
        Returns {flatten, block_entries, reason, metrics} or None. NEVER raises."""
        try:
            cfg = self.config
            if not config_bool_value(cfg.get("ultimate_book_flatten_on_breach", False), False):
                return None
            gs = self.compute_governor_state(now_utc)
            if gs is None:
                return None
            try:
                daily_thr = abs(float(cfg.get("ultimate_book_flatten_daily_loss_pct", 0.04)))
                maxdd_thr = abs(float(cfg.get("ultimate_book_flatten_maxdd_pct", 0.09)))
            except (TypeError, ValueError):
                daily_thr, maxdd_thr = 0.04, 0.09
            realized = float(getattr(gs, "realized_today_pct", 0.0) or 0.0)
            ref = float(getattr(gs, "max_dd_reference_equity", 0.0) or 0.0)
            dd = ((ref - gs.equity) / ref) if ref > 0 else 0.0
            reasons = []
            if realized <= -daily_thr:
                reasons.append(f"daily {realized * 100:.2f}% <= -{daily_thr * 100:.1f}%")
            if ref > 0 and dd >= maxdd_thr:
                reasons.append(f"maxDD {dd * 100:.2f}% >= {maxdd_thr * 100:.1f}%")
            return {"flatten": bool(reasons), "block_entries": bool(reasons),
                    "reason": ("; ".join(reasons) or None),
                    "metrics": {"realized_pct": realized, "dd": dd, "equity": gs.equity}}
        except Exception:
            return None

    # ---------------- the evaluation ----------------
    def evaluate(self, *, now_utc: Optional[datetime] = None, tags=None,
                 open_risk_pct: float = 0.0) -> dict:
        """Return {ok, decision, intents, meta, governor_state, reason}. NEVER raises."""
        now = now_utc or datetime.now(timezone.utc)
        try:
            intents, meta = self._generate_intents(tags, now)
            eq = self._equity()
            if eq is None:
                return self._safe("equity_unavailable", intents=intents, meta=meta)
            # broker-correct daily baseline: reconstruct the server-day start BALANCE from realized deals
            # (excludes floating P&L; survives a mid-day restart). If the broker CAN supply deal history
            # (live) but the reconstruction fails, FAIL CLOSED — a wrong baseline could let a -5% daily
            # breach slip past the soft stop (the hard-halt failure class). Test/mock mt5 without deal
            # history fall back to the legacy equity anchor (day_start_balance=None).
            dsb = self._governor.reconstruct_day_start_balance(self._mt5, now)
            if dsb is None and self._deal_capable():
                return self._safe("day_baseline_unavailable", intents=intents, meta=meta)
            # feed the LIVE open risk so the 4% gross cap actually binds (override only if a caller
            # passed an explicit open_risk_pct, e.g. a test); else compute it from open positions.
            gs = self._governor.build(equity=eq, day_start_balance=dsb,
                                      open_risk_pct=(open_risk_pct or self._open_risk_pct(eq)),
                                      now_utc=now,
                                      circuit_breaker=config_bool_value(
                                          self.config.get("ultimate_book_operator_circuit_breaker", False),
                                          False,
                                      ))
            decision = evaluate_vnext_ultimate_book_admission(
                config={"gtos_vnext_runtime": self.config}, intents=intents,
                governor_state=gs, account=self._account,
                limits=self._joint_daily_limits(self._governor_limits(), gs),
                n_active_override=self._running_conviction_override(intents),
                stress_state=self._stress_derisk_state(now))
            return {"ok": True, "decision": decision, "intents": intents, "meta": meta,
                    "governor_state": gs, "n_intents": len(intents),
                    "generation": dict(getattr(self, "_last_generation_telemetry", {}) or {}),
                    "generation_skips": list(getattr(self, "_last_generation_skips", []) or []),
                    "runtime_effect_now": getattr(decision, "runtime_effect_now", False),
                    "reason": getattr(decision, "decision_status", None)}
        except Exception as e:  # the book NEVER breaks the live path
            return self._safe(f"engine_exception:{e!r}")

    def _running_conviction_override(self, intents):
        """Leak-free RUNNING per-day distinct-firing-sleeve count for the Kelly-lite tilt, gated by
        ultimate_book_kelly_running_count (default OFF). Replicates the SAME pre-count filters the
        admission/bridge path applies (drop_w7 + vp_acceptance) BEFORE counting — CORRECTNESS-CRITICAL:
        counting a sleeve the full-day path would drop could push the running count ABOVE the full-day
        union and break the validated bound. NEVER raises; returns None (=> per-cycle fallback, the
        prior live behavior) when the flag is off, kelly_lite is off, there are no intents, or on error."""
        def _flag(key):
            return config_bool_value(
                self.config.get(key, _BRIDGE_DEFAULTS.get(key, False)),
                _BRIDGE_DEFAULTS.get(key, False),
            )
        try:
            if not _flag("ultimate_book_kelly_running_count") or not _flag("ultimate_book_kelly_lite"):
                return None
            from .admission import filter_w7_dropped_symbols, VP_ACCEPTANCE_BASE, VP_ACCEPTANCE_TAG
            kept, _ = filter_w7_dropped_symbols(intents, enabled=_flag("ultimate_book_drop_w7_symbols"))
            if _flag("ultimate_book_vp_acceptance"):
                kept = [it for it in kept
                        if not (it.sleeve == VP_ACCEPTANCE_BASE
                                and getattr(it, "vp_loc", None) != VP_ACCEPTANCE_TAG)]
            firing_by_day: dict[str, set] = {}
            for it in kept:
                firing_by_day.setdefault(it.decision_day, set()).add(it.sleeve)
            if not firing_by_day:
                return None
            return self._running_conviction.update_and_count(firing_by_day) or None
        except Exception:
            return None

    def _safe(self, reason: str, intents=None, meta=None) -> dict:
        return {"ok": False, "decision": None, "intents": intents or [], "meta": meta or [],
                "generation": dict(getattr(self, "_last_generation_telemetry", {}) or {}),
                "generation_skips": list(getattr(self, "_last_generation_skips", []) or []),
                "governor_state": None, "n_intents": 0, "runtime_effect_now": False, "reason": reason}
