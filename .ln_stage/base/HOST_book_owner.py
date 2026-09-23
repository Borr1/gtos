"""UltimateBookOwner — the cross-symbol book driver (one process owns the whole book).

This sidesteps the per-symbol-process impedance: it runs the engine (cross-symbol generation +
admission in ONE process, so the correlated-unit sizing + 4% gross cap are correct), then for each
realized unit pairs it with its TradeIntent(s) and routes each to a per-symbol ExecutionEngine via the
order_router. Cross-process file-locked shared state is not needed in this single-process design.

DEFAULT-OFF + fail-closed: when the ultimate_book triple-gate is off, the bridge returns shadow-only
(runtime_effect_now=False) -> the owner logs would_units and places NOTHING. open_trade inherits the
halt guard, so while any halt flag is present nothing sends even if mis-invoked. The owner NEVER raises.
"""
from __future__ import annotations

import logging
from datetime import datetime, timedelta, timezone
from typing import Any, Callable, Optional

from .book_engine import UltimateBookLiveEngine, _TF_MINUTES
from .bridge import config_bool_value
from .order_router import UltimateBookOrderRouter
from .symbol_map import build_broker_symbol_resolver
from .placement_ledger import PlacementLedger
from .admission import cluster_of, resolve_market_expansion_sleeves
from .runtime_learning_packet import (
    DEFAULT_LOG_PATH as RUNTIME_LEARNING_PACKET_DEFAULT_LOG_PATH,
    SCHEMA_VERSION as RUNTIME_LEARNING_PACKET_SCHEMA_VERSION,
    RuntimeLearningPacketWriter,
    build_runtime_learning_packet,
    stable_hash,
)
from .packet_economics import build_economics_block
from .packet_guard import GuardedPacketWriter
from src.components.ai_companion.control_state import AICompanionRuntimeGate

_log = logging.getLogger(__name__)

# Placement-failure reasons (surfaced by execution.open_trade via _last_open_trade_block_reason, or by the
# router) that are TRANSIENT broker/IO hiccups — a momentary order_send timeout/None, a broker requote, a
# fleeting order_calc_profit/symbol_info read miss. These can succeed on a retry, so a decision bar that hit
# one must NOT be consumed: the next tick re-runs the SAME bar (re-attempting the leg) while the placed-leg
# idempotency ledger + active_trade/_broker_holds guards prevent any double-place. Deterministic declines
# (cost_screen_*, vnext_policy:*, geometry_unavailable, exec_mgr_v4:* geometry gaps) are NOT here — they will
# never clear on retry, so retrying would only spam. Matched as a prefix of the reason string.
_TRANSIENT_PLACE_REASON_PREFIXES = (
    "open_trade_returned_none",     # opaque None (treat as transient: a broker/IO miss left no specific code)
    "order_rejected:",              # broker sent the order back (requote/off-quotes/timeout_no_fill/price moved)
    "no_tick_data",                 # the entry tick read came back empty for this attempt
    "cash_risk_unverified",         # broker order_calc_profit returned None this attempt (often transient)
    "lot_size_unverified",          # broker lot/geometry verification read missed this attempt
    "lot_normalize_failed",
    "filling_mode_unresolved",      # symbol_info filling-mode read missed this attempt
    "deviation_unresolved",         # symbol_info deviation read missed this attempt
    "timeout_no_position",          # safe_place_order diagnostic: timed out, no matching position adopted
    "order_send_exception",         # safe_place_order diagnostic: order_send raised (transient broker/IPC)
)

# Broker reject comments that are TERMINAL for the identical request (insufficient funds, invalid
# stops/volume, trading disabled) -> re-sending the SAME order would just fail again, so do NOT keep the bar.
_TERMINAL_BROKER_REJECT_MARKERS = (
    "no money", "not enough money", "insufficient", "invalid stops", "invalid volume",
    "invalid price", "invalid order", "trade disabled", "trade is disabled", "market closed",
    "autotrading disabled", "trade not allowed",
)


def _is_transient_place_failure(reason) -> bool:
    """True when a non-placement `reason` is a transient broker/IO hiccup worth retrying on the next tick
    (leave the decision bar unconsumed). Terminal broker rejects (no money / invalid stops / market closed)
    return False so we don't retry an identical doomed request every tick."""
    if not reason:
        return False
    text = str(reason).strip().lower()
    if not any(text.startswith(p) for p in _TRANSIENT_PLACE_REASON_PREFIXES):
        return False
    if text.startswith("order_rejected:") and any(m in text for m in _TERMINAL_BROKER_REJECT_MARKERS):
        return False
    return True


def _default_engine_factory(base_config, mt5):
    """Build a per-symbol ExecutionEngine from the symbol-merged live config (lazy, cached)."""
    from src.utils.config import apply_instrument_overrides
    from src.components.execution import ExecutionEngine

    def factory(symbol: str):
        cfg = apply_instrument_overrides(dict(base_config), symbol)
        return ExecutionEngine(mt5, cfg)
    return factory


def _bridge_telemetry(decision) -> dict:
    """Compact bridge decision fields for launcher JSONL monitoring."""
    return {
        "runtime_effect_now": bool(getattr(decision, "runtime_effect_now", False)),
        "candidate_use_allowed_now": bool(getattr(decision, "candidate_use_allowed_now", False)),
        "decision_status": getattr(decision, "decision_status", None),
        "reason": getattr(decision, "reason", None),
        "profile": getattr(decision, "profile", None),
        "enabled": bool(getattr(decision, "enabled", False)),
        "apply_to_execution": bool(getattr(decision, "apply_to_execution", False)),
        "live_activation_allowed_by_config": bool(getattr(decision, "live_activation_allowed_by_config", False)),
        "live_broker_authority": bool(getattr(decision, "live_broker_authority", False)),
        "broad_selector_disable_required": bool(getattr(decision, "broad_selector_disable_required", False)),
        "broad_selector_apply_to_execution": bool(getattr(decision, "broad_selector_apply_to_execution", False)),
        "include_clean3": bool(getattr(decision, "include_clean3", False)),
        "include_clean4": bool(getattr(decision, "include_clean4", False)),
        "include_candidate_book": bool(getattr(decision, "include_candidate_book", False)),
        "candidate_book_profile": getattr(decision, "candidate_book_profile", None),
        "candidate_book_sleeves": list(getattr(decision, "candidate_book_sleeves", ()) or ()),
        "candidate_book_sleeve_count": len(list(getattr(decision, "candidate_book_sleeves", ()) or ())),
        "include_market_expansion_book": bool(getattr(decision, "include_market_expansion_book", False)),
        "market_expansion_profile": getattr(decision, "market_expansion_profile", None),
        "market_expansion_policy": getattr(decision, "market_expansion_policy", None),
        "market_expansion_sleeves": list(getattr(decision, "market_expansion_sleeves", ()) or ()),
        "market_expansion_sleeve_count": len(list(getattr(decision, "market_expansion_sleeves", ()) or ())),
        "kelly_lite": bool(getattr(decision, "kelly_lite", False)),
        "kelly_conservative": bool(getattr(decision, "kelly_conservative", False)),
        "kelly_running_count": bool(getattr(decision, "kelly_running_count", False)),
        "sqrt_n_pooling": bool(getattr(decision, "sqrt_n_pooling", False)),
        "stress_derisk": bool(getattr(decision, "stress_derisk", False)),
        "derisk_mode": getattr(decision, "derisk_mode", None),
        "overlays": bool(getattr(decision, "overlays", False)),
        "vp_acceptance": bool(getattr(decision, "vp_acceptance", False)),
        "drop_w7_symbols": bool(getattr(decision, "drop_w7_symbols", False)),
        "learning_rerate_active": bool(getattr(decision, "learning_rerate_active", False)),
        "learning_gated_sleeves": list(getattr(decision, "learning_gated_sleeves", ()) or ()),
        "metals_confluence_gate": bool(getattr(decision, "metals_confluence_gate", False)),
        "symbol_damage_guard": bool(getattr(decision, "symbol_damage_guard", False)),
        "damage_quarantined_symbols": list(getattr(decision, "damage_quarantined_symbols", ()) or ()),
        "dropped_symbols": list(getattr(decision, "dropped_symbols", ()) or ()),
        "n_candidates_in": int(getattr(decision, "n_candidates_in", 0) or 0),
        "n_candidates_after_drop": int(getattr(decision, "n_candidates_after_drop", 0) or 0),
        "would_new_entries_allowed": bool(getattr(decision, "would_new_entries_allowed", False)),
        "would_total_risk_pct": float(getattr(decision, "would_total_risk_pct", 0.0) or 0.0),
        "would_units": list(getattr(decision, "would_units", []) or []),
        "realized_units": list(getattr(decision, "realized_units", []) or []),
        "governor": getattr(decision, "governor", None),
    }


class UltimateBookOwner:
    def __init__(self, base_config: dict, mt5, repo_root: str, namespace: str = "operator_profile",
                 engine_factory: Optional[Callable[[str], Any]] = None,
                 frontier_exits: tuple = (), spread_geometry_floor=None):
        # `frontier_exits` is a SET OF SLEEVE NAMES reached from `run_book.py --frontier-exits`
        # (Session AU, B1550; carried by Session AZ, B1850). It is not a boolean because the two
        # target-override sleeves are in opposite live states -- `mx_btcusd` is not in either
        # account's `--tags` today, while `sub_xvol_pullback` IS armed at 3R on both accounts --
        # so one switch would force a ceremony to change armed money in order to make the
        # admission's own contract runnable. It reaches the PLACEMENT path (the router) and the
        # ADOPT-rehydration path, and nothing else. It is an explicit constructor argument and
        # NOT a config key: `config/agent_config.yaml` and `config/profiles/redacted_account.yaml` are
        # both hashed into a live activation token's config digest, so a key in either would
        # stop the armed book placing until the token was re-minted. Default () ==
        # byte-identical to what this host runs today.
        # `spread_geometry_floor` is the second of the same shape, reached from `run_book.py
        # --spread-geometry-floor` (Session AY, B1810; carried by Session CE, B2300). It is a
        # PER-SLEEVE MAP rather than a boolean because AY-1 measured the repair sleeve by
        # sleeve at the ratified rule and it is a REPAIR on two of the armed sleeves
        # (`sub_mid_dn_revert` +0.426 R/day, `sub_xvol_pullback` +0.264), NEUTRAL on the other
        # two (`crypto`, `energy_agri` -- inside the random-drop envelope at every band) and a
        # NO-OP on seven of the estate. One boolean would force the two NEUTRAL sleeves to be
        # armed with the two REPAIRs. It reaches GENERATION only -- the send-layer gate it
        # mirrors already exists on this host and is untouched. It is a constructor argument
        # and NOT a config key for the same reason `frontier_exits` is: both
        # `config/agent_config.yaml` and `config/profiles/redacted_account.yaml` are hashed into a
        # live activation token's config digest. Default {} == byte-identical to what this
        # host runs today.
        self.base_config = base_config or {}
        self._frontier_exits = tuple(frontier_exits or ())
        self._spread_geometry_floor = dict(spread_geometry_floor or {})
        self._mt5 = mt5
        self._repo_root = repo_root
        self._namespace = namespace
        rt = (self.base_config.get("gtos_vnext_runtime", self.base_config))
        # the canonical->broker map lives on the full merged config (instruments[].market.mt5_symbol),
        # NOT the gtos_vnext_runtime subtree -> build it from base_config and inject into the engine.
        self._broker_symbol = build_broker_symbol_resolver(self.base_config)
        self.engine = UltimateBookLiveEngine(rt, mt5, repo_root, namespace=namespace,
                                             broker_symbol=self._broker_symbol,
                                             spread_geometry_floor=self._spread_geometry_floor)
        self.router = UltimateBookOrderRouter(self.base_config, namespace=namespace,
                                              frontier_exits=self._frontier_exits)
        self._engine_factory = engine_factory or _default_engine_factory(self.base_config, mt5)
        # Per-(symbol, sleeve) execution engines. A symbol can be held by several sleeves at once
        # (XAUUSD: metals_core + metals_softband + metals_ob_micro; GBPJPY/USDJPY: fx_jpy + fx_jpy_ny;
        # GER40/UK100: idxrev + vp_euidx). Each ExecutionEngine is single-position, so keying by symbol
        # alone made a 2nd same-symbol order overwrite active_trade and silently orphan the first ticket
        # from exit management. Keying by (symbol, sleeve) gives each sleeve's position its own lifecycle.
        self._exec_engines: dict[tuple[str, str], Any] = {}
        # idempotency: each (sleeve, symbol, decision_bar) places at most once, so the launcher can
        # tick repeatedly without double-placing. Persists under pipeline_state/ultimate_book/<ns>/.
        self._ledger = PlacementLedger(repo_root, namespace, cluster_resolver=cluster_of)
        # COMP-2 one-unit-per-(cluster,day) cap: bound a correlation cluster to ONE realized unit per day
        # (the envelope the dial was certified on) by blocking a LATER-bar same-cluster re-fire. Default ON
        # for the certified risk envelope; the 'jpy' cluster is exempt while the owner's JPY-cross live trial
        # is measuring BOTH the London (fx_jpy) and NY (fx_jpy_ny) sessions (same cluster).
        try:
            self._cluster_cap_on = config_bool_value(
                rt.get("ultimate_book_one_unit_per_cluster_per_day", True),
                True,
            )
        except (TypeError, ValueError):
            self._cluster_cap_on = True
        _exempt = rt.get("ultimate_book_cluster_cap_exempt_clusters", ["jpy"])
        self._cluster_cap_exempt = set(_exempt) if isinstance(_exempt, (list, tuple, set)) else {"jpy"}
        # reject-notification dedup: a cost/spread-blocked leg is re-attempted EVERY ~60s tick on the
        # same decision bar (correct — a transient spread can clear), but the OWNER must not get a reject
        # card every minute. Push at most ONE reject per (sleeve, symbol, decision_bar, reason).
        self._notified_rejects: set = set()
        # OPEN-position breach FLATTEN latch (MACRO-EMRG-03): set by manage_open_positions when the account
        # nears the prop-fatal daily-loss / static max-DD floor -> run_cycle goes observe-only (no NEW
        # entries) while set. _breach_ticks gives hysteresis (require N consecutive confirmed-breach ticks
        # so a transient equity wick cannot trigger a flatten).
        self._breach_block = False
        self._breach_ticks = 0
        self._breach_alerted = False
        self._oou_alerted: set = set()   # out-of-universe W7 tickets already alerted (dedup)
        self._absent_ticket_observations: dict[int, int] = {}
        try:
            self._breach_confirm = max(1, int(rt.get("ultimate_book_flatten_confirm_ticks", 2)))
        except (TypeError, ValueError):
            self._breach_confirm = 2
        self._runtime_learning_packet_enabled = config_bool_value(
            rt.get("ultimate_book_runtime_learning_packet_enabled", False),
            False,
        )
        self._runtime_learning_packet_log_enabled = config_bool_value(
            rt.get(
                "ultimate_book_runtime_learning_packet_log_enabled",
                self._runtime_learning_packet_enabled,
            ),
            self._runtime_learning_packet_enabled,
        )
        self._runtime_learning_packet_log_path = str(
            rt.get(
                "ultimate_book_runtime_learning_packet_log_path",
                RUNTIME_LEARNING_PACKET_DEFAULT_LOG_PATH,
            )
            or RUNTIME_LEARNING_PACKET_DEFAULT_LOG_PATH
        )
        self._runtime_learning_writer = None
        if self._runtime_learning_packet_enabled and self._runtime_learning_packet_log_enabled:
            self._runtime_learning_writer = RuntimeLearningPacketWriter(
                self._repo_root,
                self._runtime_learning_packet_log_path,
            )
        # Spread observed by the pre-send cost screen, keyed (sleeve, symbol, decision_bar_iso).
        # The screen already computes spread_r for every leg it evaluates but historically only
        # surfaced it inside a refusal *string* when the leg failed, so `spread_r` was null on all
        # 99,112 live packets. Recording the number here is what makes it emittable.
        self._spread_observations: dict[tuple, dict] = {}
        try:
            self._broker_exit_history_lookup_attempts = max(
                1, int(rt.get("broker_exit_history_lookup_attempts", 5) or 5)
            )
        except (TypeError, ValueError):
            self._broker_exit_history_lookup_attempts = 5
        try:
            self._broker_exit_history_lookup_sleep_seconds = max(
                0.0, float(rt.get("broker_exit_history_lookup_sleep_seconds", 0.25) or 0.25)
            )
        except (TypeError, ValueError):
            self._broker_exit_history_lookup_sleep_seconds = 0.25
        self._entry_reconciliation_repair_last_attempt_utc: dict[int, datetime] = {}
        self._exit_reconciliation_repair_last_attempt_utc: dict[int, datetime] = {}
        self._ai_companion_gate = AICompanionRuntimeGate(self.base_config, repo_root, namespace)
        self._prune_old_trade_records()   # state-unbounded-growth: sweep dead (long-closed) trade records

    def _live_broker_authority(self) -> bool:
        """Return whether this book may mutate broker state.

        False keeps reads, adoption, intent generation, launcher logs,
        runtime-learning packets, and local trade-record observations alive,
        but suppresses order placement, SL/TP modification, close, and flatten
        calls from this book runtime.
        """
        rt = self.base_config.get("gtos_vnext_runtime", self.base_config) or {}
        return config_bool_value(
            rt.get("ultimate_book_live_broker_authority", False),
            False,
        )

    def _exec_engine(self, symbol: str, sleeve: str):
        key = (symbol, sleeve)
        if key not in self._exec_engines:
            self._exec_engines[key] = self._engine_factory(symbol)
        return self._exec_engines[key]

    @staticmethod
    def _sleeve_comment(sleeve: str) -> str:
        # mirror execution.py order_comment = f"W7:{_sleeve}"[:16] (MT5 truncates comments to 16 chars)
        return f"W7:{sleeve}"[:16]

    @staticmethod
    def _entry_too_late(now: datetime, bar_iso: Optional[str], tf, frac: float) -> bool:
        """True if `now` is past the placement freshness window for a decision bar -> a restart-late CHASE.

        A supervised/cold restart spanning a bar close re-generates that bar's signal and would place it
        HOURS late at a chased price (the validated edge enters AT the close). Normal cycles fire within ~1
        poll of the close, so a gate at `frac * bar_period` past the close only bites a restart-late entry.
        Fail-OPEN (return False) on a missing/unknown bar or timeframe so a live timely entry is never blocked."""
        try:
            per = _TF_MINUTES.get(tf)
            if not per or not bar_iso:
                return False
            bar_close = datetime.fromisoformat(bar_iso) + timedelta(minutes=per)
            return ((now - bar_close).total_seconds() / 60.0) > float(frac) * per
        except Exception:
            return False

    def _broker_holds(self, symbol: str, sleeve: str) -> bool:
        """True if the broker already has an open W7:{sleeve} position on `symbol` — a definitive
        anti-duplicate guard for the case where manage_open_positions FAILED to adopt it (a transient
        broker error left the engine's active_trade None while the position is still open). Best-effort;
        any error -> False (the active_trade guard + idempotency ledger remain the primary protection)."""
        try:
            get_pos = getattr(self._mt5, "get_positions", None)
            if not callable(get_pos):
                return False
            want = self._sleeve_comment(sleeve)
            for p in (get_pos(self._broker_symbol(symbol)) or []):
                if (getattr(p, "comment", "") or "") == want:
                    return True
        except Exception:
            return False
        return False

    def _broker_position_protection(self, ticket: Any, broker_symbol: str | None = None) -> dict[str, Any]:
        """Read current broker-side protection for an open position without mutating broker state."""
        if ticket in (None, "", 0):
            return {}
        try:
            ticket_i = int(ticket)
        except (TypeError, ValueError):
            return {}
        positions = []
        get_positions = getattr(self._mt5, "get_positions", None)
        if callable(get_positions) and broker_symbol:
            try:
                positions.extend(list(get_positions(broker_symbol) or []))
            except Exception:
                return {}
        if not positions:
            get_open = getattr(self._mt5, "get_open_positions", None)
            if callable(get_open):
                try:
                    positions.extend(list(get_open() or []))
                except Exception:
                    return {}
        for position in positions:
            try:
                if int(getattr(position, "ticket", 0) or 0) != ticket_i:
                    continue
            except (TypeError, ValueError):
                continue
            out: dict[str, Any] = {}
            for attr, key in (
                ("sl", "broker_position_sl"),
                ("tp", "broker_position_tp"),
                ("price_open", "broker_position_price_open"),
                ("price_current", "broker_position_price_current"),
            ):
                value = getattr(position, attr, None)
                if value is not None:
                    out[key] = value
            return out
        return {}

    @staticmethod
    def _broker_symbol_key(symbol: Any) -> str:
        return str(symbol or "").upper().replace(".", "").replace("_", "").strip()

    def _broker_symbol_keys_for_canonical(self, symbol: str) -> set[str]:
        keys = {self._broker_symbol_key(symbol)}
        try:
            keys.add(self._broker_symbol_key(self._broker_symbol(symbol)))
        except Exception:
            pass
        return {key for key in keys if key}

    def _same_broker_symbol_open_exposures(
        self,
        symbol: str,
        *,
        open_positions_snapshot: list | None = None,
    ) -> list | None:
        """Return open GTOS/book positions already using this broker symbol.

        The placement path used to guard only the exact (symbol, sleeve). Different sleeves can resolve to
        the same broker symbol (for example US30_cash -> US30), so a second sleeve could unintentionally
        open the opposite side while the first ticket was still live. This guard is intentionally scoped to
        book/GTOS positions only and returns None only when a real broker position accessor exists but the
        read is unavailable, so tests/mocks without position APIs do not become globally fail-closed.
        """
        get_open = getattr(self._mt5, "get_open_positions", None)
        positions = []
        source_seen = False
        if open_positions_snapshot is None:
            if callable(get_open):
                open_positions_snapshot = self._open_book_positions_snapshot()
                if open_positions_snapshot is None:
                    return None
                source_seen = True
                positions.extend(list(open_positions_snapshot or []))
        else:
            source_seen = True
            positions.extend(list(open_positions_snapshot or []))
        get_positions = getattr(self._mt5, "get_positions", None)
        if callable(get_positions):
            try:
                fresh_positions = get_positions(self._broker_symbol(symbol))
            except Exception:
                return None
            source_seen = True
            positions.extend(list(fresh_positions or []))
        elif not source_seen:
            return []
        try:
            from src.mt5.mt5_interface import MAGIC_NUMBER
        except Exception:
            MAGIC_NUMBER = None
        keys = self._broker_symbol_keys_for_canonical(symbol)
        exposures = []
        seen_tickets = set()
        for p in positions:
            psym = getattr(p, "symbol", None)
            if self._broker_symbol_key(psym) not in keys:
                continue
            ticket = getattr(p, "ticket", None)
            dedupe_key = ticket if ticket not in (None, 0, "") else id(p)
            if dedupe_key in seen_tickets:
                continue
            seen_tickets.add(dedupe_key)
            comment = getattr(p, "comment", "") or ""
            magic = getattr(p, "magic", None)
            ledger_pair = self._ledger.sleeve_symbol_for_ticket(ticket) if ticket not in (None, 0) else None
            is_book_position = (
                comment.startswith("W7:")
                or ledger_pair is not None
                or (MAGIC_NUMBER is not None and magic == MAGIC_NUMBER)
            )
            if is_book_position:
                exposures.append(p)
        return exposures

    def _tick(self, symbol: str):
        # the intent carries the CANONICAL symbol; cross to the broker under its mt5_symbol
        try:
            return self._mt5.get_tick(self._broker_symbol(symbol))
        except Exception:
            return None

    def _profile_supports_symbol(self, symbol: str) -> bool:
        from src.utils.config import resolve_instrument_config_key

        base_symbol = (self.base_config.get("market", {}) or {}).get("symbol", "XAUUSD")
        return symbol == base_symbol or resolve_instrument_config_key(self.base_config, symbol) is not None

    def _candidate_book_sleeves(self) -> tuple[str, ...]:
        rt = self.base_config.get("gtos_vnext_runtime", self.base_config) or {}
        raw = rt.get("ultimate_book_candidate_book_sleeves", [])
        if raw is None:
            return ()
        if isinstance(raw, str):
            return (raw,) if raw else ()
        if isinstance(raw, (list, tuple, set)):
            return tuple(str(item) for item in raw if str(item))
        return ()

    def _market_expansion_sleeves(self) -> tuple[str, ...]:
        rt = self.base_config.get("gtos_vnext_runtime", self.base_config) or {}
        raw = rt.get("ultimate_book_market_expansion_sleeves", [])
        if raw is None:
            explicit = ()
        elif isinstance(raw, str):
            explicit = (raw,) if raw else ()
        elif isinstance(raw, (list, tuple, set)):
            explicit = tuple(str(item) for item in raw if str(item))
        else:
            explicit = ()
        policy = str(rt.get("ultimate_book_market_expansion_policy", "explicit_allowlist") or "explicit_allowlist")
        resolved, error = resolve_market_expansion_sleeves(policy=policy, explicit_sleeves=explicit)
        return () if error else resolved

    def _manageable_symbols(self) -> list[str]:
        """All active-sleeve on_surface symbols THAT HAVE AN INSTRUMENT CONFIG on this profile.

        A position can only be open on a symbol the broker/profile actually carries, so symbols absent
        from config['instruments'] (e.g. the metals crosses / agri legs that the redacted_account follower
        lacks) can never have a managed position — building their per-symbol ExecutionEngine would only
        raise 'No instrument config' every tick. We filter them out (silently, but logged ONCE so the
        reduced per-profile breadth is intentional + visible, not a silent error storm)."""
        cached = getattr(self, "_manageable_cache", None)
        if cached is not None:
            return cached
        from .sleeves.registry import active_specs
        rt = self.base_config.get("gtos_vnext_runtime", self.base_config) or {}
        include_candidate_book = config_bool_value(rt.get("ultimate_book_include_candidate_book", False), False)
        include_market_expansion_book = config_bool_value(
            rt.get("ultimate_book_include_market_expansion_book", False),
            False,
        )
        candidate_sleeves = self._candidate_book_sleeves()
        expansion_sleeves = self._market_expansion_sleeves()
        all_syms = sorted({
            s
            for spec in active_specs(
                None,
                include_candidate_book=include_candidate_book,
                candidate_book_sleeves=candidate_sleeves or None,
                include_market_expansion_book=include_market_expansion_book,
                market_expansion_sleeves=expansion_sleeves or None,
            )
            for s in (spec.on_surface or [])
        })
        present, absent = [], []
        for s in all_syms:
            if self._profile_supports_symbol(s):
                present.append(s)
            else:
                absent.append(s)
        if absent:
            _log.info("book[%s]: %d on_surface symbols have no instrument config on this profile -> "
                      "not generated/managed here (intentional reduced breadth): %s",
                      self._namespace, len(absent), ", ".join(absent))
        self._manageable_cache = present
        return present

    def _runtime_learning_status(self, packets: int = 0, error: Any | None = None) -> dict:
        status = {
            "enabled": bool(self._runtime_learning_packet_enabled),
            "log_enabled": bool(self._runtime_learning_packet_log_enabled),
            "log_path": self._runtime_learning_packet_log_path,
            "schema": RUNTIME_LEARNING_PACKET_SCHEMA_VERSION,
            "packets": int(packets or 0),
        }
        if error is not None:
            status["error"] = repr(error)
        return status

    def _runtime_learning_bridge_context(self, decision=None) -> dict:
        if decision is not None:
            return _bridge_telemetry(decision)
        rt = self.base_config.get("gtos_vnext_runtime", self.base_config) or {}
        broad_live = config_bool_value(rt.get("selector_v4_enabled", False), False) and config_bool_value(
            rt.get("selector_v4_apply_to_execution", False),
            False,
        )
        live_broker_authority = config_bool_value(
            rt.get("ultimate_book_live_broker_authority", False),
            False,
        )
        effect_now = (
            config_bool_value(rt.get("ultimate_book_enabled", False), False)
            and config_bool_value(rt.get("ultimate_book_apply_to_execution", False), False)
            and config_bool_value(rt.get("ultimate_book_live_activation_allowed", False), False)
            and live_broker_authority
            and not broad_live
        )
        return {
            "runtime_effect_now": effect_now,
            "enabled": config_bool_value(rt.get("ultimate_book_enabled", False), False),
            "apply_to_execution": config_bool_value(rt.get("ultimate_book_apply_to_execution", False), False),
            "live_activation_allowed_by_config": config_bool_value(
                rt.get("ultimate_book_live_activation_allowed", False),
                False,
            ),
            "live_broker_authority": live_broker_authority,
            "broad_selector_apply_to_execution": broad_live,
            "profile": rt.get("ultimate_book_profile"),
            "candidate_book_profile": rt.get("ultimate_book_candidate_book_profile"),
            "include_candidate_book": config_bool_value(rt.get("ultimate_book_include_candidate_book", False), False),
            "candidate_book_sleeves": list(self._candidate_book_sleeves()),
            "include_market_expansion_book": config_bool_value(
                rt.get("ultimate_book_include_market_expansion_book", False),
                False,
            ),
            "market_expansion_profile": rt.get("ultimate_book_market_expansion_profile"),
            "market_expansion_policy": rt.get("ultimate_book_market_expansion_policy"),
            "market_expansion_sleeves": list(self._market_expansion_sleeves()),
            "kelly_lite": config_bool_value(rt.get("ultimate_book_kelly_lite", False), False),
            "kelly_conservative": config_bool_value(rt.get("ultimate_book_kelly_conservative", False), False),
            "kelly_running_count": config_bool_value(rt.get("ultimate_book_kelly_running_count", False), False),
            "sqrt_n_pooling": config_bool_value(rt.get("ultimate_book_sqrt_n_pooling", False), False),
            "stress_derisk": config_bool_value(rt.get("ultimate_book_stress_derisk", False), False),
            "derisk_mode": rt.get("ultimate_book_derisk_mode"),
            "overlays": config_bool_value(rt.get("ultimate_book_overlays", False), False),
            "vp_acceptance": config_bool_value(rt.get("ultimate_book_vp_acceptance", False), False),
            "drop_w7_symbols": config_bool_value(rt.get("ultimate_book_drop_w7_symbols", False), False),
            "learning_rerate_active": bool(rt.get("ultimate_book_learning_rerate")),
            "metals_confluence_gate": config_bool_value(
                rt.get("ultimate_book_metals_confluence_gate", False),
                False,
            ),
            "symbol_damage_guard": config_bool_value(rt.get("ultimate_book_symbol_damage_guard", False), False),
        }

    @staticmethod
    def _runtime_learning_skip_context(decision: Any, intents: Any, meta: Any) -> dict[tuple[str, str, str], dict]:
        meta_by_pair: dict[tuple[str, str], dict] = {}
        for item in meta or []:
            if not isinstance(item, dict):
                continue
            sleeve = str(item.get("tag") or item.get("sleeve") or "")
            symbol = str(item.get("symbol") or "")
            if sleeve and symbol:
                meta_by_pair[(sleeve, symbol)] = item
        unit_by_sleeve: dict[str, dict] = {}
        for unit in (
            list(getattr(decision, "realized_units", []) or [])
            + list(getattr(decision, "would_units", []) or [])
        ):
            if not isinstance(unit, dict):
                continue
            members = unit.get("sleeve_members") or []
            for sleeve in members:
                unit_by_sleeve.setdefault(str(sleeve), unit)
        out: dict[tuple[str, str, str], dict] = {}
        for intent in intents or []:
            sleeve = str(getattr(intent, "sleeve", "") or "")
            symbol = str(getattr(intent, "symbol", "") or "")
            if not sleeve or not symbol:
                continue
            meta_row = meta_by_pair.get((sleeve, symbol), {})
            dbar = str(
                meta_row.get("decision_bar_iso")
                or getattr(intent, "decision_bar_iso", None)
                or getattr(intent, "decision_day", None)
                or ""
            )
            decision_day = str(getattr(intent, "decision_day", "") or dbar[:10] or "")
            unit = unit_by_sleeve.get(sleeve, {})
            candidate_id = unit.get("candidate_id") if isinstance(unit, dict) else None
            members = unit.get("sleeve_members") if isinstance(unit, dict) else []
            direction = UltimateBookOwner._runtime_learning_direction_label(
                getattr(intent, "direction", None)
            )
            cluster = UltimateBookOwner._resolve_runtime_cluster(unit=unit, sleeve=sleeve)
            candidate_specific = (
                candidate_id
                and (
                    len(members or []) == 1
                    or (f"::{symbol}::" in str(candidate_id) and str(candidate_id).endswith(f"::{sleeve}"))
                )
            )
            ctx = {
                "symbol": symbol,
                "sleeve": sleeve,
                "direction": direction,
                "decision_bar_iso": dbar,
                "decision_day": decision_day,
                "timeframe": meta_row.get("timeframe"),
                "cluster": cluster,
            }
            if candidate_specific:
                ctx["candidate_id"] = candidate_id
            else:
                derived_candidate_id = UltimateBookOwner._runtime_learning_candidate_id(
                    cluster=cluster,
                    symbol=symbol,
                    decision_day=decision_day,
                    direction=direction,
                    sleeve=sleeve,
                )
                if derived_candidate_id:
                    ctx["candidate_id"] = derived_candidate_id
            out[(sleeve, symbol, dbar)] = ctx
        return out

    @staticmethod
    def _runtime_learning_direction_label(direction: Any) -> str | None:
        if direction in (None, ""):
            return None
        if isinstance(direction, (int, float)):
            if float(direction) > 0:
                return "LONG"
            if float(direction) < 0:
                return "SHORT"
        text = str(direction).strip()
        if not text:
            return None
        upper = text.upper()
        if upper in {"1", "+1", "BUY", "LONG"}:
            return "LONG"
        if upper in {"-1", "SELL", "SHORT"}:
            return "SHORT"
        return upper

    @staticmethod
    def _runtime_learning_candidate_id(
        *,
        cluster: Any,
        symbol: Any,
        decision_day: Any,
        direction: Any,
        sleeve: Any,
    ) -> str | None:
        if any(value in (None, "") for value in (cluster, symbol, decision_day, direction, sleeve)):
            return None
        return f"W7_BOOK::{cluster}::{symbol}::{str(decision_day)[:10]}::{direction}::{sleeve}"

    @staticmethod
    def _cluster_from_candidate_id(candidate_id: Any) -> str | None:
        text = str(candidate_id or "")
        parts = text.split("::")
        if len(parts) >= 6 and parts[0] == "W7_BOOK" and parts[1]:
            return parts[1]
        return None

    @staticmethod
    def _resolve_runtime_cluster(
        *,
        unit: dict | None = None,
        sleeve: Any = None,
        candidate_id: Any = None,
    ) -> str | None:
        if isinstance(unit, dict):
            value = unit.get("cluster")
            if value not in (None, ""):
                return str(value)
            value = UltimateBookOwner._cluster_from_candidate_id(unit.get("candidate_id"))
            if value:
                return value
        value = UltimateBookOwner._cluster_from_candidate_id(candidate_id)
        if value:
            return value
        if sleeve not in (None, ""):
            value = cluster_of(str(sleeve))
            if value:
                return str(value)
        return None

    @staticmethod
    def _runtime_learning_admission_members(unit: dict, skip_context: dict | None) -> list[dict]:
        if not isinstance(unit, dict) or not isinstance(skip_context, dict):
            return []
        members = {str(item) for item in (unit.get("sleeve_members") or []) if str(item)}
        if not members:
            return []
        out = []
        for (_sleeve, _symbol, _dbar), ctx in sorted(skip_context.items()):
            if not isinstance(ctx, dict) or str(ctx.get("sleeve") or "") not in members:
                continue
            out.append({
                key: ctx.get(key)
                for key in (
                    "candidate_id",
                    "symbol",
                    "sleeve",
                    "direction",
                    "decision_bar_iso",
                    "decision_day",
                    "timeframe",
                    "cluster",
                )
                if ctx.get(key) is not None
            })
        return out

    @staticmethod
    def _runtime_learning_skip_row(skip: Any, skip_context: dict | None = None) -> dict:
        if isinstance(skip, dict):
            row = dict(skip)
        else:
            row = {"reason": str(skip)}
            text = str(skip)
            if ":" in text:
                symbol, reason = text.split(":", 1)
                if symbol:
                    row.setdefault("symbol", symbol)
                row["reason"] = reason or text
        if isinstance(skip_context, dict):
            key = (
                str(row.get("sleeve") or ""),
                str(row.get("symbol") or ""),
                str(row.get("decision_bar_iso") or ""),
            )
            ctx = skip_context.get(key)
            if isinstance(ctx, dict):
                for field in (
                    "candidate_id",
                    "cluster",
                    "decision_day",
                    "direction",
                    "timeframe",
                ):
                    if ctx.get(field) is not None:
                        row.setdefault(field, ctx.get(field))
                row.setdefault(
                    "admission_unit_members",
                    [
                        {
                            key: ctx.get(key)
                            for key in (
                                "candidate_id",
                                "symbol",
                                "sleeve",
                                "direction",
                                "decision_bar_iso",
                                "decision_day",
                                "timeframe",
                                "cluster",
                            )
                            if ctx.get(key) is not None
                        }
                    ],
                )
                row.setdefault("admission_unit_member_count", len(row.get("admission_unit_members") or []))
        if row.get("reason") == "profile_missing_instrument_config":
            row.setdefault("candidate_context_status", "not_generated_profile_missing_instrument")
            row.setdefault("source_completeness_status", "profile_missing_instrument_config_no_candidate_identity")
        row.setdefault("skip_reason", row.get("reason"))
        return row

    @staticmethod
    def _runtime_learning_ticket_hash(ticket: Any) -> str | None:
        if ticket in (None, "", 0):
            return None
        return stable_hash(ticket, prefix="ticket")

    @staticmethod
    def _price_tolerance(*values: Any) -> float:
        nums: list[float] = []
        for value in values:
            if value in (None, ""):
                continue
            try:
                nums.append(abs(float(value)))
            except (TypeError, ValueError):
                continue
        ref = max(nums) if nums else 0.0
        if ref >= 1000.0:
            return 0.02
        if ref >= 100.0:
            return 0.01
        if ref >= 10.0:
            return 0.001
        return 0.0001

    @staticmethod
    def _price_matches(left: float | None, right: float | None, tolerance: float) -> bool:
        return left is not None and right is not None and abs(left - right) <= tolerance

    @staticmethod
    def _broker_protection_reconciliation(record: dict, execution: dict) -> dict[str, Any]:
        planned_entry = UltimateBookOwner._closed_record_float(record, "entry_price")
        planned_sl = UltimateBookOwner._closed_record_float(record, "stop_loss")
        planned_tp = UltimateBookOwner._closed_record_float(record, "take_profit_1")
        broker_open = UltimateBookOwner._closed_record_float(record, "broker_position_price_open")
        broker_sl = UltimateBookOwner._closed_record_float(record, "broker_position_sl")
        broker_tp = UltimateBookOwner._closed_record_float(record, "broker_position_tp")
        tolerance = UltimateBookOwner._price_tolerance(planned_entry, planned_sl, planned_tp, broker_open, broker_sl, broker_tp)

        planned_delta_sl = planned_sl - planned_entry if planned_sl is not None and planned_entry is not None else None
        planned_delta_tp = planned_tp - planned_entry if planned_tp is not None and planned_entry is not None else None
        fill_adjusted_sl = broker_open + planned_delta_sl if broker_open is not None and planned_delta_sl is not None else None
        fill_adjusted_tp = broker_open + planned_delta_tp if broker_open is not None and planned_delta_tp is not None else None
        planned_risk = abs(planned_sl - planned_entry) if planned_sl is not None and planned_entry is not None else None
        planned_target_r = (
            abs(planned_tp - planned_entry) / planned_risk
            if planned_tp is not None and planned_entry is not None and planned_risk not in (None, 0.0)
            else None
        )
        target_sign = (
            1.0
            if planned_tp is not None and planned_entry is not None and planned_tp > planned_entry
            else -1.0
            if planned_tp is not None and planned_entry is not None and planned_tp < planned_entry
            else None
        )
        broker_risk = abs(broker_sl - broker_open) if broker_sl is not None and broker_open is not None else None
        broker_risk_adjusted_tp = (
            broker_open + target_sign * planned_target_r * broker_risk
            if broker_open is not None
            and target_sign is not None
            and planned_target_r is not None
            and broker_risk not in (None, 0.0)
            else None
        )

        def _leg_status(
            *,
            leg: str,
            planned: float | None,
            broker: float | None,
            fill_adjusted: float | None,
            broker_risk_adjusted: float | None = None,
        ) -> str:
            if broker is None or broker == 0.0:
                if planned is None or planned == 0.0:
                    return f"broker_{leg}_absent_as_planned"
                return f"missing_broker_current_{leg}"
            if planned is None or planned == 0.0:
                return f"broker_current_{leg}_present_without_planned_geometry"
            if UltimateBookOwner._price_matches(planned, broker, tolerance):
                return f"matches_planned_{leg}"
            if UltimateBookOwner._price_matches(fill_adjusted, broker, tolerance):
                return f"matches_fill_adjusted_{leg}"
            if UltimateBookOwner._price_matches(broker_risk_adjusted, broker, tolerance):
                return f"matches_broker_risk_adjusted_{leg}"
            return f"differs_from_planned_{leg}"

        sl_status = _leg_status(
            leg="stop_loss",
            planned=planned_sl,
            broker=broker_sl,
            fill_adjusted=fill_adjusted_sl,
        )
        tp_status = _leg_status(
            leg="take_profit",
            planned=planned_tp,
            broker=broker_tp,
            fill_adjusted=fill_adjusted_tp,
            broker_risk_adjusted=broker_risk_adjusted_tp,
        )
        statuses = {sl_status, tp_status}
        if all(status.startswith("broker_") and status.endswith("_absent_as_planned") for status in statuses):
            overall = "broker_current_protection_unavailable"
        elif any(status.startswith("differs_from_planned_") for status in statuses):
            overall = "broker_current_differs_from_planned_protection"
        elif any(status.startswith("matches_broker_risk_adjusted_") for status in statuses):
            overall = "broker_current_matches_broker_risk_adjusted_or_planned_protection"
        elif any(status.startswith("matches_fill_adjusted_") for status in statuses):
            overall = "broker_current_matches_fill_adjusted_or_planned_protection"
        elif any(status.startswith("matches_planned_") for status in statuses):
            overall = "broker_current_matches_planned_protection"
        else:
            overall = "broker_current_protection_captured_without_full_planned_geometry"
        return {
            "broker_position_protection_reconciliation_status": overall,
            "broker_position_stop_loss_status": sl_status,
            "broker_position_take_profit_status": tp_status,
            "broker_position_planned_entry_price": planned_entry,
            "broker_position_planned_stop_loss": planned_sl,
            "broker_position_planned_take_profit": planned_tp,
            "broker_position_fill_price": broker_open,
            "broker_position_fill_adjusted_stop_loss": fill_adjusted_sl,
            "broker_position_fill_adjusted_take_profit": fill_adjusted_tp,
            "broker_position_broker_risk_adjusted_take_profit": broker_risk_adjusted_tp,
            "broker_position_planned_target_r": planned_target_r,
            "broker_position_price_tolerance": tolerance,
        }

    @staticmethod
    def _runtime_learning_trade_context(
        *,
        ticket: Any = None,
        trade_params: dict | None = None,
        record: dict | None = None,
        broker_symbol: str | None = None,
        placed_at_utc: str | None = None,
        management_checked_at_utc: str | None = None,
        policy_clock: dict | None = None,
    ) -> dict:
        tp = dict(trade_params or {})
        if not tp and isinstance(record, dict):
            inst = record.get("instrumentation")
            if isinstance(inst, dict):
                tp = dict(inst)
        ctx: dict[str, Any] = {}
        ticket_hash = UltimateBookOwner._runtime_learning_ticket_hash(ticket)
        if ticket_hash:
            ctx["ticket_hash_sha256"] = ticket_hash
        if broker_symbol:
            ctx["broker_symbol"] = broker_symbol
        if placed_at_utc:
            ctx["placement_observed_at_utc"] = placed_at_utc
        if management_checked_at_utc:
            ctx["management_checked_at_utc"] = management_checked_at_utc
        if isinstance(record, dict):
            ctx["trade_record_status"] = (
                "reconstructed_native_policy"
                if record.get("reconstructed_from_sleeve_identity")
                else "persisted_trade_record"
            )
            for key in ("decision_bar_iso", "decision_day", "cluster", "candidate_id"):
                if record.get(key) is not None:
                    ctx[key] = record.get(key)
            if record.get("runtime_learning_joinability_status") is not None:
                ctx["trade_record_joinability_status"] = record.get("runtime_learning_joinability_status")
            if record.get("trade_lifecycle_status") is not None:
                ctx["trade_lifecycle_status"] = record.get("trade_lifecycle_status")
            if record.get("closed_at_utc") is not None:
                ctx["closed_at_utc"] = record.get("closed_at_utc")
            if record.get("last_management_checked_at_utc") is not None:
                ctx["last_management_checked_at_utc"] = record.get("last_management_checked_at_utc")
            if record.get("close_action") is not None:
                ctx["close_action"] = record.get("close_action")
            if record.get("rehydration_status") is not None:
                ctx["rehydration_status"] = record.get("rehydration_status")
            if record.get("rehydration_error") is not None:
                ctx["rehydration_error"] = record.get("rehydration_error")
            execution = record.get("execution")
            if isinstance(execution, dict):
                if not ctx.get("ticket_hash_sha256") and execution.get("ticket_hash_sha256"):
                    ctx["ticket_hash_sha256"] = execution.get("ticket_hash_sha256")
                ctx.setdefault("broker_symbol", execution.get("broker_symbol") or broker_symbol)
                for key in (
                    "broker_position_sl",
                    "broker_position_tp",
                    "broker_position_price_open",
                    "broker_position_price_current",
                    "broker_position_protection_reconciliation_status",
                    "broker_position_stop_loss_status",
                    "broker_position_take_profit_status",
                    "broker_position_planned_entry_price",
                    "broker_position_planned_stop_loss",
                    "broker_position_planned_take_profit",
                    "broker_position_fill_price",
                    "broker_position_fill_adjusted_stop_loss",
                    "broker_position_fill_adjusted_take_profit",
                    "broker_position_broker_risk_adjusted_take_profit",
                    "broker_position_planned_target_r",
                    "broker_position_price_tolerance",
                ):
                    if execution.get(key) is not None:
                        ctx[key] = execution.get(key)
                if execution.get("placed_at_utc") is not None:
                    ctx.setdefault("placement_observed_at_utc", execution.get("placed_at_utc"))
                if not UltimateBookOwner._missingish_ticket(execution.get("broker_entry_deal_ticket")):
                    ctx["broker_entry_deal_hash_sha256"] = stable_hash(
                        execution.get("broker_entry_deal_ticket"),
                        prefix="deal_ticket",
                    )
                for key in (
                    "entry_reconciliation_status",
                    "broker_fill_time_utc",
                    # `_iso_from_deal_time_near_reference` (:2818-2852) will shift a broker deal
                    # time by up to +/-6 WHOLE HOURS to snap it to a local reference. The offset
                    # is computed and stored on the execution record (:3055-3056) and then read by
                    # nobody -- it appears in 0 of the 99,112 live packets. So for every packet in
                    # the corpus it is impossible to tell a raw broker timestamp from one that was
                    # silently moved six hours to agree with our clock, which is the
                    # broker-time-labelled-as-UTC hazard in its most subtle form: the agreement
                    # that licenses the label is partly manufactured by the label's own producer.
                    # Emitting it makes the adjustment auditable; packet_economics downgrades the
                    # entry provenance to `transferred` whenever it fired.
                    "broker_fill_time_alignment_offset_seconds",
                    "broker_entry_source_status",
                ):
                    if execution.get(key) is not None:
                        ctx[key] = execution.get(key)
                for key in (
                    "exit_reconciliation_status",
                    "exit_reconciliation_attempted",
                    "exit_reconciliation_source_status",
                    "broker_exit_time_utc",
                    "broker_exit_price",
                    "broker_exit_profit",
                    "broker_exit_commission",
                    "broker_exit_swap",
                    "broker_exit_fee",
                    "broker_entry_commission",
                    "broker_entry_swap",
                    "broker_position_sl",
                    "broker_position_tp",
                    "broker_position_price_open",
                    "broker_position_price_current",
                    "broker_position_protection_reconciliation_status",
                    "broker_position_stop_loss_status",
                    "broker_position_take_profit_status",
                    "broker_position_planned_entry_price",
                    "broker_position_planned_stop_loss",
                    "broker_position_planned_take_profit",
                    "broker_position_fill_price",
                    "broker_position_fill_adjusted_stop_loss",
                    "broker_position_fill_adjusted_take_profit",
                    "broker_position_broker_risk_adjusted_take_profit",
                    "broker_position_planned_target_r",
                    "broker_position_price_tolerance",
                    "broker_position_deal_count",
                    "broker_position_entry_deal_count",
                    "broker_position_exit_deal_count",
                    "broker_position_accounting_coverage_status",
                    "broker_position_aggregate_profit",
                    "broker_position_aggregate_commission",
                    "broker_position_aggregate_swap",
                    "broker_position_aggregate_fee",
                    "broker_position_realized_pnl",
                    "broker_realized_pnl_source",
                    "broker_realized_pnl",
                ):
                    if execution.get(key) is not None:
                        ctx[key] = execution.get(key)
                missing_exit_fields = execution.get("exit_reconciliation_missing_fields")
                if not isinstance(missing_exit_fields, list):
                    missing_exit_fields = []
                else:
                    missing_exit_fields = list(missing_exit_fields)
                if (
                    execution.get("exit_reconciliation_status") == "RECONCILED_FROM_ACCOUNT_HISTORY"
                    and UltimateBookOwner._missingish_ticket(execution.get("broker_exit_order_ticket"))
                    and "broker_exit_order_ticket" not in missing_exit_fields
                ):
                    missing_exit_fields.append("broker_exit_order_ticket")
                if missing_exit_fields:
                    ctx["exit_reconciliation_missing_fields"] = missing_exit_fields
                for raw_key, out_key, prefix in (
                    ("broker_exit_deal_ticket", "broker_exit_deal_hash_sha256", "deal_ticket"),
                    ("broker_exit_order_ticket", "broker_exit_order_hash_sha256", "order_ticket"),
                    ("broker_exit_position_id", "broker_exit_position_hash_sha256", "position_ticket"),
                ):
                    if not UltimateBookOwner._missingish_ticket(execution.get(raw_key)):
                        ctx[out_key] = stable_hash(execution.get(raw_key), prefix=prefix)
            if record.get("broker_real_entry_label_ready") is not None:
                ctx["broker_real_entry_label_ready"] = record.get("broker_real_entry_label_ready")
            for key in (
                "exit_reconciliation_status",
                "exit_reconciliation_attempted",
                "exit_reconciliation_source_status",
                "exit_reconciliation_missing_fields",
                "broker_exit_time_utc",
                "broker_exit_price",
                "broker_exit_profit",
                "broker_exit_commission",
                "broker_exit_swap",
                "broker_exit_fee",
                "broker_position_deal_count",
                "broker_position_entry_deal_count",
                "broker_position_exit_deal_count",
                "broker_position_accounting_coverage_status",
                "broker_position_aggregate_profit",
                "broker_position_aggregate_commission",
                "broker_position_aggregate_swap",
                "broker_position_aggregate_fee",
                "broker_position_realized_pnl",
                "broker_realized_pnl_source",
                "broker_realized_pnl",
            ):
                if record.get(key) is not None:
                    ctx[key] = record.get(key)
            for raw_key, out_key, prefix in (
                ("broker_exit_deal_ticket", "broker_exit_deal_hash_sha256", "deal_ticket"),
                ("broker_exit_order_ticket", "broker_exit_order_hash_sha256", "order_ticket"),
                ("broker_exit_position_id", "broker_exit_position_hash_sha256", "position_ticket"),
            ):
                if not UltimateBookOwner._missingish_ticket(record.get(raw_key)):
                    ctx[out_key] = stable_hash(record.get(raw_key), prefix=prefix)
            if (
                ctx.get("exit_reconciliation_status") == "RECONCILED_FROM_ACCOUNT_HISTORY"
                and ctx.get("broker_exit_order_hash_sha256") in (None, "")
            ):
                missing_exit_fields = ctx.get("exit_reconciliation_missing_fields")
                if not isinstance(missing_exit_fields, list):
                    missing_exit_fields = []
                else:
                    missing_exit_fields = list(missing_exit_fields)
                if "broker_exit_order_ticket" not in missing_exit_fields:
                    missing_exit_fields.append("broker_exit_order_ticket")
                ctx["exit_reconciliation_missing_fields"] = missing_exit_fields
        elif trade_params:
            ctx["trade_record_status"] = "runtime_trade_params"

        for key in (
            "candidate_id",
            "decision_time_utc",
            "asof_utc",
            "entry_price",
            "stop_loss",
            "take_profit_1",
            "risk_pct_override",
            "direction",
            "gtos_vnext_dynamic_policy_selected",
            "gtos_vnext_execution_policy_id",
            "gtos_vnext_dynamic_be_trigger_r",
            "gtos_vnext_dynamic_partial_close_ratio",
            "gtos_vnext_dynamic_trail_gap_r",
            "gtos_vnext_dynamic_time_stop_bars",
            "gtos_vnext_dynamic_final_target_r",
            "gtos_vnext_dynamic_broker_take_profit_mode",
            "gtos_vnext_dynamic_no_broker_take_profit",
            "gtos_vnext_book_native_exit_management",
            "gtos_vnext_source_event_hash",
            "gtos_vnext_selector_v4_packet_hash",
            "gtos_vnext_scheduler_v4_packet_hash",
            "gtos_vnext_selected_cell_id",
            "gtos_vnext_selected_cell_risk_pct",
            "gtos_vnext_selected_cell_nominal_risk_pct",
            "gtos_vnext_selected_cell_risk_policy_identity_status",
            "pretrade_spread_r",
            "pretrade_expected_slippage_r",
            "pretrade_total_cost_r",
        ):
            if key in tp and tp.get(key) is not None:
                ctx[key] = tp.get(key)
        has_ticket_hash = bool(ctx.get("ticket_hash_sha256"))
        has_candidate = bool(ctx.get("candidate_id"))
        has_decision = bool(ctx.get("decision_bar_iso") or ctx.get("decision_time_utc") or ctx.get("asof_utc"))
        if has_ticket_hash and has_candidate and has_decision:
            computed_joinability_status = "ticket_candidate_decision_policy_joinable"
        elif has_ticket_hash and has_decision:
            computed_joinability_status = "ticket_decision_policy_joinable"
        elif has_ticket_hash:
            computed_joinability_status = "ticket_policy_joinable"
        else:
            computed_joinability_status = "partial_join_context"
        status_rank = {
            "partial_join_context": 0,
            "ticket_policy_joinable": 1,
            "ticket_decision_policy_joinable": 2,
            "ticket_candidate_decision_policy_joinable": 3,
        }
        record_joinability_status = ctx.get("trade_record_joinability_status")
        if (
            isinstance(record_joinability_status, str)
            and status_rank.get(record_joinability_status, -1) <= status_rank[computed_joinability_status]
        ):
            ctx["joinability_status"] = record_joinability_status
        else:
            ctx["joinability_status"] = computed_joinability_status
        ctx.update(UltimateBookOwner._runtime_learning_policy_clock_context(policy_clock))
        return ctx

    @staticmethod
    def _runtime_learning_policy_clock_context(policy_clock: dict | None) -> dict:
        if not isinstance(policy_clock, dict):
            return {}
        ctx = {"policy_clock_diagnostic": dict(policy_clock)}
        field_map = {
            "status": "policy_clock_status",
            "checked_at_utc": "policy_clock_checked_at_utc",
            "entry_time_utc": "policy_clock_entry_time_utc",
            "clock_source": "policy_clock_source",
            "time_stop_bars": "policy_clock_time_stop_bars",
            "elapsed_m15_bars": "policy_clock_elapsed_m15_bars",
            "bars_until_due": "policy_clock_bars_until_due",
            "overdue_bars": "policy_clock_overdue_bars",
            "close_attempted": "policy_clock_close_attempted",
            "close_result": "policy_clock_close_result",
            "close_reason": "policy_clock_close_reason",
            "targetless": "policy_clock_targetless",
            "vnext_time_stop_active": "policy_clock_vnext_time_stop_active",
            "error": "policy_clock_error",
        }
        for src, dst in field_map.items():
            if src in policy_clock and policy_clock.get(src) is not None:
                ctx[dst] = policy_clock.get(src)
        return ctx

    def _broker_server_name(self) -> Optional[str]:
        """The MT5 server string, needed to count swap nights on the broker's own clock.

        Read from the live account when available, else the profile config. Returns None rather
        than guessing -- `rollover_nights_crossed` fails closed on an unknown server, which is the
        correct outcome: a guessed offset is silent and survives every test. Never raises.
        """
        for getter in ("get_account_server", "get_server"):
            try:
                fn = getattr(self._mt5, getter, None)
                if callable(fn):
                    value = fn()
                    if value:
                        return str(value)
            except Exception:  # noqa: BLE001
                pass
        # Config fallbacks, in order of authority. `mt5.server` is FIRST for historical reasons and
        # is measured to be ABSENT on both live profiles -- `mt5` carries only portable/terminal_*
        # keys. The live server name lives under `broker_profile`. Without these two extra
        # fallbacks, `_broker_server_name` returns None on the VPS for both namespaces, every
        # `rollover_nights` on every live packet reads `unavailable`, and the carry silently
        # delivers holding time WITHOUT the swap-night count -- which is half of what it exists to
        # record, since swap is the largest single broker cost for eight of eleven sleeves.
        # Both live values (`FTMO-Server3`, `redacted_account-Server 2`) are registered rules in
        # `broker_clock`, so the count works the moment the name resolves.
        # Neither getter above is defined anywhere in either lineage; they are kept for a future
        # adapter, not because they fire. Found by an adversarial pass.
        for source, key in (
            (self.base_config.get("mt5"), "server"),
            (self.base_config.get("broker_profile"), "server"),
            ((self.base_config.get("broker_profile") or {}).get("expected_account"), "server"),
        ):
            try:
                # Duck-typed rather than `isinstance(..., Mapping)`: this module imports only
                # Any/Callable/Optional from typing, and a bare `Mapping` here is a NameError at
                # runtime that no syntax check catches.
                value = source.get(key) if hasattr(source, "get") else None
                if value:
                    return str(value)
            except Exception:  # noqa: BLE001
                continue
        return None

    def _runtime_learning_economics(self, row: dict) -> Optional[dict]:
        """Build the optional economics block for one outcome row. Never raises.

        Holding time is the reason this exists. Session N measured the W7 book's dominant
        remaining uncertainty and it is carry: at one night of average carry the book of record
        passes at P=0.951 and makes 1.97 %/month; run every trade to its structural horizon and
        that becomes P=0.450 and 0.13 %/month. Nothing in 99,112 live packets distinguishes those
        two worlds, because holding time was only ever *derivable* -- from a poll-loop observation
        of the close, on 98 of 151 closes -- and never recorded as a measurement with a stated
        provenance and a broker-clock night count.
        """
        try:
            return build_economics_block(row, server=self._broker_server_name())
        except Exception:  # noqa: BLE001 - observability must never raise into the book
            return None

    def _append_runtime_learning_packets(self, summary: dict, packets: list[dict]) -> None:
        if not self._runtime_learning_packet_enabled:
            summary["runtime_learning"] = self._runtime_learning_status(0)
            return
        if not self._runtime_learning_writer:
            # `packet_enabled: true` + `packet_log_enabled: false` is a supported config and leaves
            # the writer None (:223-228). Falling through would hand the guard a None writer, fail
            # every packet as `unrecorded`, and feed that count to
            # ai_companion/supervisor.py:517 -> :709 -> :734-741, which raises an integrity issue
            # and issues `pause_new_entries` for every namespace. A logging switch must never be
            # able to stop the books.
            summary["runtime_learning"] = self._runtime_learning_status(0)
            return
        # Built per call, not cached, so replacing `_runtime_learning_writer` (which tests and
        # operational tooling do) still governs where packets land.
        guard = GuardedPacketWriter(self._runtime_learning_writer)
        # The guard never raises and never silently drops: valid packets are written, invalid ones
        # are quarantined to a sidecar AND leave a `packet_rejected` marker in the main log so the
        # hole is visible to a reader of that log alone. The previous implementation raised out of
        # `append_many` on the FIRST invalid packet -- which discarded the whole cycle's batch --
        # and recorded the casualties only in this cycle summary, where nothing downstream of the
        # packet log could ever see them.
        report = guard.append_many(packets)
        status = self._runtime_learning_status(report.accepted)
        status["packet_guard"] = report.as_dict()
        # Preserved key names: src/components/ai_companion/supervisor.py:517,539-540 reads both,
        # and a silently-renamed field would degrade the companion's view without failing anything.
        status["packet_write_error_count"] = report.quarantined + report.unrecorded
        status["packet_write_errors"] = [
            {
                "index": issue.get("index"),
                "event_type": issue.get("event_type"),
                "error": ";".join(issue.get("issues") or []),
            }
            for issue in report.issues[-10:]
        ]
        summary["runtime_learning"] = status
        if not report.healthy:
            _log.warning(
                "book[%s]: runtime-learning guard refused %d/%d packets "
                "(unrecorded=%d, markers=%d); quarantine=%s; issues=%s",
                self._namespace,
                report.quarantined,
                report.submitted,
                report.unrecorded,
                report.markers_written,
                guard.quarantine_path,
                report.issues[-3:],
            )

    def _emit_cycle_runtime_learning(
        self,
        summary: dict,
        now: datetime,
        *,
        decision=None,
        place: bool = True,
    ) -> None:
        bridge = summary.get("bridge") or self._runtime_learning_bridge_context(decision)
        packets: list[dict] = []
        ts = now.isoformat()
        base_outcome = {
            "reason": summary.get("reason"),
            "bar_consumable": bool(summary.get("bar_consumable", True)),
            "runtime_effect_now": bool(summary.get("runtime_effect_now", False)),
            "source_completeness_status": "runtime_cycle_summary_observed",
        }
        skip_context = summary.get("skip_context") if isinstance(summary.get("skip_context"), dict) else {}
        if decision is None:
            packets.append(build_runtime_learning_packet(
                namespace=self._namespace,
                event_type="cycle_no_decision",
                ts=ts,
                bridge=bridge,
                outcome={**base_outcome, "placement_status": "no_decision"},
                source="book_owner.run_cycle",
            ))
        else:
            would_units = list(getattr(decision, "would_units", []) or [])
            if not would_units:
                packets.append(build_runtime_learning_packet(
                    namespace=self._namespace,
                    event_type="cycle_no_candidates",
                    ts=ts,
                    bridge=bridge,
                    outcome={**base_outcome, "placement_status": "no_candidates"},
                    source="book_owner.run_cycle",
                ))
            for unit in would_units:
                placement_status = (
                    "admitted" if bool(summary.get("runtime_effect_now")) and place else "shadow"
                )
                admission_members = self._runtime_learning_admission_members(unit, skip_context)
                single_member = admission_members[0] if len(admission_members) == 1 else {}
                candidate_id = unit.get("candidate_id") or single_member.get("candidate_id")
                outcome = {
                    **base_outcome,
                    "placement_status": placement_status,
                    "candidate_id": candidate_id,
                    "cluster": self._resolve_runtime_cluster(
                        unit=unit,
                        sleeve=single_member.get("sleeve"),
                        candidate_id=candidate_id,
                    ),
                    "admission_unit_members": admission_members,
                    "admission_unit_member_count": len(admission_members),
                }
                for key in ("symbol", "sleeve", "direction", "decision_bar_iso", "decision_day", "timeframe"):
                    if single_member.get(key) is not None:
                        outcome[key] = single_member.get(key)
                packets.append(build_runtime_learning_packet(
                    namespace=self._namespace,
                    event_type="unit_admitted" if placement_status == "admitted" else "unit_shadow",
                    ts=ts,
                    bridge=bridge,
                    unit=unit,
                    outcome=outcome,
                    source="book_owner.run_cycle",
                ))
        for skip in summary.get("skipped", []) or []:
            row = self._runtime_learning_skip_row(skip, skip_context)
            reason = row.get("reason") or row.get("skip_reason")
            row.update({
                "placement_status": "skipped",
                "transient_retry": bool(_is_transient_place_failure(reason)),
                "bar_consumable": bool(summary.get("bar_consumable", True)),
            })
            row.setdefault("source_completeness_status", "runtime_skip_summary_observed")
            self._attach_spread_observation(row)
            packets.append(build_runtime_learning_packet(
                namespace=self._namespace,
                event_type="unit_skipped",
                ts=ts,
                bridge=bridge,
                outcome=row,
                source="book_owner.run_cycle",
            ))
        for placed in summary.get("placed", []) or []:
            row = dict(placed)
            row.update({
                "placement_status": "placed",
                "cluster": row.get("cluster") or self._resolve_runtime_cluster(
                    sleeve=row.get("sleeve"),
                    candidate_id=row.get("candidate_id"),
                ),
                "source_completeness_status": "runtime_placement_summary_observed",
            })
            self._attach_spread_observation(row)
            packets.append(build_runtime_learning_packet(
                namespace=self._namespace,
                event_type="unit_placed",
                ts=ts,
                bridge=bridge,
                outcome=row,
                economics=self._runtime_learning_economics(row),
                source="book_owner.run_cycle",
            ))
        self._append_runtime_learning_packets(summary, packets)

    def _emit_management_runtime_learning(self, summary: dict, now: datetime) -> None:
        bridge = self._runtime_learning_bridge_context()
        packets: list[dict] = []
        ts = now.isoformat()
        rows = [
            ("position_adopted", summary.get("adopted", []) or []),
            ("position_managed", summary.get("managed", []) or []),
            ("position_out_of_universe", summary.get("out_of_universe", []) or []),
            ("position_management_error", summary.get("errors", []) or []),
        ]
        for event_type, items in rows:
            for item in items:
                row = dict(item)
                row.update({
                    "placement_status": event_type,
                    "source_completeness_status": "runtime_management_summary_observed",
                    "management_checked_at_utc": row.get("management_checked_at_utc") or ts,
                })
                packets.append(build_runtime_learning_packet(
                    namespace=self._namespace,
                    event_type=event_type,
                    ts=ts,
                    bridge=bridge,
                    outcome=row,
                    economics=self._runtime_learning_economics(row),
                    source="book_owner.manage_open_positions",
                ))
        for item in summary.get("closed", []) or []:
            row = dict(item)
            action = str(row.get("action", ""))
            event_type = "breach_flatten" if "flatten" in action else "position_closed"
            row.update({
                "placement_status": event_type,
                "source_completeness_status": "runtime_management_summary_observed",
                "management_checked_at_utc": row.get("management_checked_at_utc") or ts,
            })
            packets.append(build_runtime_learning_packet(
                namespace=self._namespace,
                event_type=event_type,
                ts=ts,
                bridge=bridge,
                outcome=row,
                economics=self._runtime_learning_economics(row),
                source="book_owner.manage_open_positions",
            ))
        self._append_runtime_learning_packets(summary, packets)

    def run_cycle(self, *, now_utc: Optional[datetime] = None, tags=None, place: bool = True) -> dict:
        """One book cycle. Returns a summary; NEVER raises and NEVER places while gated off/halted.

        place=False forces observe-only (evaluate + log would_units, never send) — the launcher passes
        this when the operator kill-switch or a halt flag is set, so the brake works even if the book is
        gated on. (open_trade also inherits the runtime-halt guard; this is defense in depth.)"""
        now = now_utc or datetime.now(timezone.utc)
        # breach-flatten latch (set by manage_open_positions) forces observe-only: while the account is in
        # a flattened breach state, NEVER open new entries (otherwise a flatten -> re-enter -> flatten churn).
        if getattr(self, "_breach_block", False):
            place = False
        # Spread observations are scoped to ONE cycle: the screen fills them during this cycle's
        # per-intent loop and _emit_cycle_runtime_learning drains them at the end of the same
        # cycle. Clearing here bounds a dict that would otherwise grow for the life of a process
        # that runs for months, and removes any chance of a later packet picking up an earlier
        # bar's measurement -- a wrong number wearing a "measured" label is worse than no number.
        self._spread_observations.clear()
        res = self.engine.evaluate(now_utc=now, tags=tags)
        summary = {"ok": res["ok"], "reason": res["reason"], "n_intents": res["n_intents"],
                   "runtime_effect_now": res["runtime_effect_now"], "placed": [], "shadow": 0,
                   "skipped": [], "bar_consumable": True}
        summary["skipped"].extend(res.get("generation_skips", []) or [])
        if not res["ok"] or res["decision"] is None:
            # bar-consumed-on-transient-failure: the engine did NOT evaluate (equity_unavailable /
            # day_baseline_unavailable / engine_exception — a momentary broker hiccup at the bar-close
            # tick). Do NOT let the launcher consume this decision bar, or that bar's signal is lost forever.
            summary["bar_consumable"] = False
            self._emit_cycle_runtime_learning(summary, now, decision=None, place=place)
            return summary
        decision = res["decision"]
        summary["bridge"] = _bridge_telemetry(decision)
        summary["skip_context"] = self._runtime_learning_skip_context(
            decision,
            res.get("intents", []),
            res.get("meta", []),
        )
        if isinstance(summary.get("bridge"), dict) and res.get("generation"):
            summary["bridge"]["broker_profile_generation"] = res.get("generation")
        ai_companion_snapshot = self._ai_companion_gate.snapshot(now)
        summary["ai_companion"] = ai_companion_snapshot
        if not res["runtime_effect_now"] or not place:
            summary["shadow"] = len(getattr(decision, "would_units", []) or [])
            if not place and res["runtime_effect_now"]:
                summary["skipped"].append("breach_flatten_block" if getattr(self, "_breach_block", False)
                                          else "kill_switch_or_halt_forced_observe_only")
            self._emit_cycle_runtime_learning(summary, now, decision=decision, place=place)
            return summary

        ai_state_pause = self._ai_companion_gate.control_state_issue_pause(ai_companion_snapshot)
        if ai_state_pause is not None:
            summary["shadow"] = len(getattr(decision, "would_units", []) or [])
            summary["bar_consumable"] = False
            summary["skipped"].append({
                "reason": f"ai_companion_control_state_issue:{ai_state_pause.reason}",
                "ai_companion_control_id": ai_state_pause.control_id,
                "ai_companion_control_type": ai_state_pause.type,
                "ai_companion_issues": ai_state_pause.control.get("issues", []),
            })
            self._emit_cycle_runtime_learning(summary, now, decision=decision, place=False)
            return summary

        ai_pause = self._ai_companion_gate.pause_new_entries(ai_companion_snapshot)
        if ai_pause is not None:
            summary["shadow"] = len(getattr(decision, "would_units", []) or [])
            summary["skipped"].append({
                "reason": f"ai_companion_pause_new_entries:{ai_pause.reason}",
                "ai_companion_control_id": ai_pause.control_id,
                "ai_companion_control_type": ai_pause.type,
            })
            self._emit_cycle_runtime_learning(summary, now, decision=decision, place=False)
            return summary

        gs = res["governor_state"]
        day_start = gs.equity / (1.0 + gs.realized_today_pct) if (1.0 + gs.realized_today_pct) else gs.equity
        # offset-aware server-local reset-window date (matches the governor's daily baseline), NOT a pure
        # UTC date — otherwise the headroom-snapshot window-id disagrees with its own day_start during
        # 21:00-24:00 UTC and mis-segments row-level day joins.
        reset_window_id = self.engine.reset_window_date(now)
        account_state = self.router.account_state(
            self._mt5, day_start_baseline=day_start, reset_window_id=reset_window_id)
        try:
            balance = float(self._mt5.get_account_balance())
        except Exception:
            balance = gs.equity
        if account_state is None:
            summary["skipped"].append("account_state_unavailable")
            summary["bar_consumable"] = False   # transient headroom-read failure -> retry this bar next tick
            self._emit_cycle_runtime_learning(summary, now, decision=decision, place=place)
            return summary
        open_positions_snapshot = self._open_book_positions_snapshot()
        placed_broker_symbol_keys: set[str] = set()
        attempted_transient_broker_symbol_keys: set[str] = set()

        intents = res["intents"]
        # (sleeve, symbol) -> the decision bar's UTC iso, for the idempotency key
        bar_of = {(m["tag"], m["symbol"]): m.get("decision_bar_iso") for m in res.get("meta", [])}
        tf_of = {(m["tag"], m["symbol"]): m.get("timeframe") for m in res.get("meta", [])}
        late_frac = float(self.engine.config.get("ultimate_book_max_entry_lateness_frac", 0.5) or 0.5)
        for unit in decision.realized_units:
            if not unit.get("sized") or unit.get("risk_pct_per_trade", 0) <= 0:
                continue
            members = set(unit.get("sleeve_members", []))
            # pair this cluster unit with its constituent intents; one order per intent at the unit risk
            for intent in intents:
                if intent.sleeve not in members:
                    continue
                # PER-INTENT ISOLATION: one intent's failure (e.g. an unexpected per-symbol engine
                # factory exception) must never abort the cycle or starve the
                # remaining intents on this bar. run_cycle NEVER raises (the launcher marks the bar
                # advanced after this returns; a raise here would re-run + re-fail the poison intent
                # every tick and permanently skip its siblings). Idempotency is preserved — an already
                # placed intent stays ledger-skipped on retry.
                dbar = None
                try:
                    dbar = bar_of.get((intent.sleeve, intent.symbol)) or intent.decision_day
                    if not self._profile_supports_symbol(intent.symbol):
                        summary["skipped"].append({
                            "symbol": intent.symbol,
                            "sleeve": intent.sleeve,
                            "decision_bar_iso": dbar,
                            "reason": "profile_missing_instrument_config",
                        })
                        continue
                    ai_cooldown = self._ai_companion_gate.cooldown_for(
                        ai_companion_snapshot,
                        symbol=intent.symbol,
                        sleeve=intent.sleeve,
                    )
                    if ai_cooldown is not None:
                        summary["skipped"].append({
                            "symbol": intent.symbol,
                            "sleeve": intent.sleeve,
                            "decision_bar_iso": dbar,
                            "reason": f"ai_companion_cooldown:{ai_cooldown.reason}",
                            "ai_companion_control_id": ai_cooldown.control_id,
                            "ai_companion_control_type": ai_cooldown.type,
                        })
                        continue
                    # IDEMPOTENCY: never place the same (sleeve, symbol, decision bar) twice
                    if self._ledger.already_placed(intent.sleeve, intent.symbol, dbar):
                        summary["skipped"].append({"symbol": intent.symbol, "sleeve": intent.sleeve,
                                                   "decision_bar_iso": dbar,
                                                   "reason": "already_placed_this_bar"})
                        continue
                    # ONE-UNIT-PER-SLEEVE-PER-DAY cap (sleeve-day-reentry-overrisk / COMP-2 same-sleeve):
                    # an H4 sleeve (crypto/idxrev) can re-fire on a LATER same-day bar after its first
                    # position closed; placing a 2nd full-size unit exceeds the validated daily-unit risk
                    # model (the 4% gross cap only bounds CONCURRENT, not sequential, risk). Enforce the
                    # validated one-entry-per-(sleeve,symbol)-per-day here (terminal -> no retry spam).
                    _dday = str(getattr(intent, "decision_day", "") or dbar or "")[:10]
                    if self._ledger.already_placed_today(intent.sleeve, intent.symbol, _dday):
                        summary["skipped"].append({"symbol": intent.symbol, "sleeve": intent.sleeve,
                                                   "decision_bar_iso": dbar,
                                                   "reason": "already_placed_today"})
                        continue
                    # ONE-UNIT-PER-(CLUSTER,DAY) cap (COMP-2): a correlation cluster that already placed its
                    # unit on an EARLIER bar today must not stack a 2nd full correlated unit on a later bar
                    # (same-bar members of one unit are allowed). Certified-envelope safety; jpy exempt for
                    # the live trial. dbar identifies THIS bar so same-bar unit members still place.
                    _cluster = self._resolve_runtime_cluster(unit=unit, sleeve=intent.sleeve)
                    if (self._cluster_cap_on and _cluster and _cluster not in self._cluster_cap_exempt
                            and self._ledger.cluster_placed_today_other_bar(_cluster, _dday, dbar)):
                        summary["skipped"].append({"symbol": intent.symbol, "sleeve": intent.sleeve,
                                                   "decision_bar_iso": dbar,
                                                   "reason": f"cluster_unit_already_placed_today:{_cluster}"})
                        continue
                    ai_risk = self._ai_companion_gate.risk_multiplier_for(
                        ai_companion_snapshot,
                        symbol=intent.symbol,
                        sleeve=intent.sleeve,
                    )
                    if ai_risk is not None and float(ai_risk.control.get("multiplier", 1.0)) <= 0.0:
                        summary["skipped"].append({
                            "symbol": intent.symbol,
                            "sleeve": intent.sleeve,
                            "decision_bar_iso": dbar,
                            "reason": f"ai_companion_zero_risk:{ai_risk.reason}",
                            "ai_companion_control_id": ai_risk.control_id,
                            "ai_companion_control_type": ai_risk.type,
                        })
                        continue
                    tick = self._tick(intent.symbol)
                    if tick is None:
                        summary["skipped"].append({"symbol": intent.symbol, "sleeve": intent.sleeve,
                                                   "decision_bar_iso": dbar,
                                                   "reason": "no_tick_transient"})
                        summary["bar_consumable"] = False
                        continue
                    # SESSION / TRADEABLE GATE (defense in depth): a closed cash market (index holiday,
                    # weekend edge, extended-hours mismatch) freezes the last tick. The broker would reject
                    # a closed-market order anyway, but skipping pre-send avoids trading a STALE signal and
                    # reject-noise. Fail-OPEN: only skip when the tick is DEFINITIVELY stale (>15 min) — an
                    # open market (even thin FX/index) updates within this; a missing timestamp or any error
                    # proceeds so a live market is never wrongly blocked.
                    tick_time = getattr(tick, "time", None)
                    if tick_time is not None:
                        try:
                            # stale-now-for-stale-tick-gate: measure age against a FRESH now (not the
                            # cycle-top `now`), so a slow cycle (broker/management work between the tick-top
                            # and here) cannot make a genuinely STALE closed-market tick read as fresh and
                            # slip a stale signal through.
                            age_s = (datetime.now(timezone.utc) - tick_time).total_seconds()
                            if age_s > 900:
                                summary["skipped"].append(
                                    {"symbol": intent.symbol, "sleeve": intent.sleeve,
                                     "decision_bar_iso": dbar,
                                     "reason": f"stale_tick_market_closed:{int(age_s)}s"})
                                continue
                        except Exception:
                            pass
                    ee = self._exec_engine(intent.symbol, intent.sleeve)
                    # POSITION GUARD: never place a 2nd order for a (symbol, sleeve) that already holds an
                    # open position — it would overwrite this engine's single active_trade and orphan the
                    # first ticket. (A different sleeve on the same symbol uses a different engine, so a
                    # legitimate multi-sleeve book on one symbol still places each leg.) manage_open_positions
                    # runs before run_cycle each tick, so active_trade reflects the live broker state.
                    if getattr(ee, "active_trade", None) is not None:
                        summary["skipped"].append({"symbol": intent.symbol, "sleeve": intent.sleeve,
                                                   "decision_bar_iso": dbar,
                                                   "reason": "sleeve_already_holds_symbol"})
                        continue
                    # BROKER-LEVEL guard (defense in depth): if adoption failed this restart (a transient
                    # broker error left ee.active_trade None while the W7:{sleeve} position is still open at
                    # the broker), a new decision bar would otherwise place a DUPLICATE. Check the broker
                    # directly before placing.
                    if self._broker_holds(intent.symbol, intent.sleeve):
                        summary["skipped"].append({"symbol": intent.symbol, "sleeve": intent.sleeve,
                                                   "decision_bar_iso": dbar,
                                                   "reason": "sleeve_already_holds_symbol_broker"})
                        continue
                    target_broker_keys = self._broker_symbol_keys_for_canonical(intent.symbol)
                    if placed_broker_symbol_keys.intersection(target_broker_keys):
                        summary["skipped"].append({"symbol": intent.symbol, "sleeve": intent.sleeve,
                                                   "decision_bar_iso": dbar,
                                                   "reason": "same_broker_symbol_already_placed_this_cycle"})
                        continue
                    if attempted_transient_broker_symbol_keys.intersection(target_broker_keys):
                        summary["skipped"].append({"symbol": intent.symbol, "sleeve": intent.sleeve,
                                                   "decision_bar_iso": dbar,
                                                   "reason": "same_broker_symbol_transient_attempt_this_cycle"})
                        continue
                    same_symbol_exposures = self._same_broker_symbol_open_exposures(
                        intent.symbol,
                        open_positions_snapshot=open_positions_snapshot,
                    )
                    if same_symbol_exposures is None:
                        summary["skipped"].append({"symbol": intent.symbol, "sleeve": intent.sleeve,
                                                   "decision_bar_iso": dbar,
                                                   "reason": "same_broker_symbol_position_source_unavailable_for_lifecycle_guard"})
                        summary["bar_consumable"] = False
                        continue
                    if same_symbol_exposures:
                        existing_symbols = sorted({
                            str(getattr(pos, "symbol", "") or "")
                            for pos in same_symbol_exposures
                            if getattr(pos, "symbol", None)
                        })
                        existing_comments = sorted({
                            str(getattr(pos, "comment", "") or "")
                            for pos in same_symbol_exposures
                            if getattr(pos, "comment", None)
                        })
                        summary["skipped"].append({"symbol": intent.symbol, "sleeve": intent.sleeve,
                                                   "decision_bar_iso": dbar,
                                                   "reason": "same_broker_symbol_open_position_lifecycle_guard",
                                                   "existing_broker_symbols": existing_symbols,
                                                   "existing_comments": existing_comments,
                                                   "existing_position_count": len(same_symbol_exposures)})
                        continue
                    # BAR-AGE GATE (no restart-late chase): a supervised/cold restart spanning a bar close
                    # re-generates that bar's signal; placing it hours late chases a price the validated edge
                    # never entered at. Past the freshness window -> SHADOW it (skip send, still recorded).
                    _bar_iso = bar_of.get((intent.sleeve, intent.symbol))
                    if self._entry_too_late(now, _bar_iso, tf_of.get((intent.sleeve, intent.symbol)), late_frac):
                        summary["skipped"].append({"symbol": intent.symbol, "sleeve": intent.sleeve,
                                                   "decision_bar_iso": dbar,
                                                   "reason": "stale_late_entry_after_restart"})
                        continue
                    # PRE-SEND COST SCREEN (root-cause of the opaque 'open_trade_returned_none' on JPY):
                    # a leg whose live spread eats more than selected_cell_pretrade_max_spread_r (0.10) of
                    # its R-unit (stop_dist) can NEVER clear execution.open_trade's ExecMgr-V4 cost gate
                    # (broker_net_cost_engine: spread_r = (ask-bid)/sl_distance). e.g. GBPJPY fx_jpy: a 2-pip
                    # spread on a 1.0xATR(M15) ~8.7-pip stop -> spread_r ~0.23 -> always refused. Attempting
                    # it is futile work surfaced as a scary 'Trade NOT placed'. Decline it HERE, cleanly,
                    # with the precise cost reason BEFORE building the order (identical outcome: no trade
                    # either way -> no strategy change; the authoritative gate still guards anything else).
                    cost_skip = self._spread_cost_screen(intent, tick)
                    if cost_skip is not None:
                        summary["skipped"].append({"symbol": intent.symbol, "sleeve": intent.sleeve,
                                                   "decision_bar_iso": dbar,
                                                   "reason": cost_skip})
                        rkey = (intent.sleeve, intent.symbol, dbar, cost_skip)
                        if rkey not in self._notified_rejects:
                            if len(self._notified_rejects) > 5000:
                                self._notified_rejects.clear()
                            self._notified_rejects.add(rkey)
                            self._notify_cost_skip(intent, cost_skip)
                        continue
                    adjusted_unit = self._ai_companion_gate.adjusted_unit(unit, ai_risk)
                    if ai_risk is not None:
                        summary.setdefault("ai_companion_risk_adjustments", []).append({
                            "symbol": intent.symbol,
                            "sleeve": intent.sleeve,
                            "decision_bar_iso": dbar,
                            "control_id": ai_risk.control_id,
                            "multiplier": float(ai_risk.control.get("multiplier", 1.0)),
                            "reason": ai_risk.reason,
                        })
                    unit_su = _UnitView(adjusted_unit)
                    result = self.router.place(ee, unit_su, intent, tick, account_state, balance)
                    if result["placed"]:
                        placed_broker_symbol_keys.update(target_broker_keys)
                        ticket = getattr(result.get("trade_state"), "ticket", None)
                        trade_params = result.get("trade_params") or {}
                        candidate_id = result.get("candidate_id") or trade_params.get("candidate_id")
                        placed_at = now.isoformat()
                        resolved_cluster = self._resolve_runtime_cluster(
                            unit=unit,
                            sleeve=intent.sleeve,
                            candidate_id=candidate_id,
                        )
                        try:
                            broker_symbol = self._broker_symbol(intent.symbol)
                        except Exception:
                            broker_symbol = None
                        ledger_row = self._ledger.record(
                            intent.sleeve,
                            intent.symbol,
                            dbar,
                            candidate_id=candidate_id,
                            ticket=ticket,
                            ts=placed_at,
                            decision_day=_dday,
                            cluster=resolved_cluster,
                            require_full_context=True,
                        )
                        # persist the exit-policy truth so a restarted process rehydrates the exact lifecycle
                        self._persist_trade_record(
                            ticket,
                            trade_params,
                            intent,
                            decision_bar_iso=dbar,
                            decision_day=_dday,
                            cluster=resolved_cluster,
                            placed_at_utc=placed_at,
                            broker_symbol=broker_symbol,
                        )
                        persisted_record = self._load_trade_record(ticket)
                        placed_row = {"symbol": intent.symbol, "sleeve": intent.sleeve,
                                      "decision_bar_iso": dbar,
                                      "decision_day": _dday,
                                      "cluster": resolved_cluster,
                                      "candidate_id": candidate_id}
                        if isinstance(ledger_row, dict):
                            for key in (
                                "placement_capture_contract_version",
                                "placement_source_completeness_status",
                                "placement_source_missing_fields",
                            ):
                                if ledger_row.get(key) is not None:
                                    placed_row[key] = ledger_row.get(key)
                        placed_row.update(self._runtime_learning_trade_context(
                            ticket=ticket,
                            trade_params=trade_params,
                            record=persisted_record,
                            broker_symbol=broker_symbol,
                            placed_at_utc=placed_at,
                        ))
                        summary["placed"].append(placed_row)
                        self._notify_placed(intent, unit_su, result)
                    else:
                        summary["skipped"].append({"symbol": intent.symbol, "sleeve": intent.sleeve,
                                                   "decision_bar_iso": dbar, "reason": result["reason"]})
                        # TRANSIENT-FAILURE RETRY (lost-signal-on-broker-hiccup): a momentary order_send
                        # timeout/None/requote must not permanently lose a once-per-bar (e.g. daily fx_jpy)
                        # signal. Leave the bar UNCONSUMED so the next ~60s tick re-attempts this leg — the
                        # placed-leg ledger + active_trade/_broker_holds guards make the retry double-place
                        # safe. Terminal declines (cost/geometry/no-money) stay consumed (no doomed retry).
                        if _is_transient_place_failure(result.get("reason")):
                            attempted_transient_broker_symbol_keys.update(target_broker_keys)
                            summary["bar_consumable"] = False
                        # notify the owner ONCE per blocked opportunity (dedup on the decision bar) — a
                        # routine spread/cost gate re-firing every tick must not spam the owner's phone.
                        rkey = (intent.sleeve, intent.symbol, dbar, str(result.get("reason")))
                        if rkey not in self._notified_rejects:
                            if len(self._notified_rejects) > 5000:
                                self._notified_rejects.clear()   # bound memory on a long-running process
                            self._notified_rejects.add(rkey)
                            self._notify_reject(intent, result.get("reason"))
                except Exception as e:
                    summary["skipped"].append({"symbol": getattr(intent, "symbol", "?"),
                                               "sleeve": getattr(intent, "sleeve", "?"),
                                               "decision_bar_iso": locals().get("dbar"),
                                               "reason": f"intent_exception:{e!r}"})
                    _log.warning("book[%s]: intent %s/%s raised in placement (isolated): %r",
                                 self._namespace, getattr(intent, "sleeve", "?"),
                                 getattr(intent, "symbol", "?"), e)
                    continue
        self._emit_cycle_runtime_learning(summary, now, decision=decision, place=place)
        return summary

    # ---------------- position management (every tick, halt-independent) ----------------
    def manage_open_positions(self, *, now_utc: Optional[datetime] = None) -> dict:
        """Rehydrate + manage every open book position. Management runs even while halted / gated off
        (halt blocks NEW sends only). NEVER raises.

        PER-(SYMBOL, SLEEVE): a symbol can carry several concurrent positions (one per sleeve). Each
        ticket is routed to its OWN engine via the W7:{sleeve} broker comment, so a symbol shared by
        several sleeves no longer collides on one active_trade slot. A leftover safety net adopts any
        magic-matched book position whose comment did not route (missing/mangled) so nothing is left
        unmanaged. Each adopted position then runs its own check_and_manage_trade off the live tick."""
        summary = {"managed": [], "adopted": [], "closed": [], "errors": []}
        pairs = self._manageable_pairs()
        sleeves_by_symbol: dict[str, list[str]] = {}
        for sym, sl in pairs:
            sleeves_by_symbol.setdefault(sym, []).append(sl)
        # one snapshot of all open book positions, mapped broker->canonical ({} if mt5 lacks the accessor)
        open_positions_snapshot = self._open_book_positions_snapshot()
        open_tickets = self._open_snapshot_ticket_set(open_positions_snapshot)
        absence_threshold = self._absence_reconcile_threshold(open_positions_snapshot)
        positions_by_canon = self._open_book_positions_by_canonical(
            sleeves_by_symbol.keys(),
            open_positions_snapshot=open_positions_snapshot,
        )
        claimed_tickets: set = set()

        for sym, sleeves in sleeves_by_symbol.items():
            try:
                held_tickets: set = set()
                # 1. comment-routed adoption: each sleeve's engine adopts ONLY its own W7:{sleeve} ticket
                for sl in sleeves:
                    ee = self._exec_engine(sym, sl)
                    if getattr(ee, "active_trade", None) is None:
                        reconcile = getattr(ee, "reconcile_on_startup", None)
                        if callable(reconcile):
                            try:
                                reconcile(comment_filter=self._sleeve_comment(sl))
                            except TypeError:
                                reconcile()   # back-compat engine without the comment_filter kwarg
                        if getattr(ee, "active_trade", None) is not None:
                            self._adopt_into_engine(ee, sym, sl, summary)
                    t = getattr(getattr(ee, "active_trade", None), "ticket", None)
                    if t is not None:
                        held_tickets.add(t)
                        claimed_tickets.add(t)
                # 2. leftover safety net: any magic-matched open position on this symbol NOT yet held
                #    (e.g. a missing/mangled comment) must NOT go unmanaged -> adopt into a free engine.
                for p in (positions_by_canon.get(sym, []) or []):
                    tkt = getattr(p, "ticket", None)
                    if tkt is None or tkt in held_tickets or tkt in claimed_tickets:
                        continue
                    # only adopt BOOK positions: a W7:* comment, a comment-stripped one, OR a ticket the
                    # book's OWN placement ledger recorded placing (definitively ours despite a legacy /
                    # mislabelled comment — the GER40 'GoldAgent_OBRete' orphan: book-placed by vp_euidx but
                    # tagged with the retired default comment, then unadoptable -> managed only by the broker
                    # SL/TP). A foreign comment that is NOT in our ledger stays foreign (legacy/manual) and
                    # is never managed — the book must not touch trades it did not place.
                    cmt = (getattr(p, "comment", "") or "")
                    ledger_pair = self._ledger.sleeve_symbol_for_ticket(tkt)
                    if cmt and not cmt.startswith("W7:") and ledger_pair is None:
                        continue
                    for sl in sleeves:
                        if ledger_pair is not None and ledger_pair != (sl, sym):
                            continue
                        if cmt.startswith("W7:") and cmt != self._sleeve_comment(sl):
                            continue
                        ee = self._exec_engine(sym, sl)
                        if getattr(ee, "active_trade", None) is not None:
                            continue
                        adopt = getattr(ee, "adopt_specific_position", None)
                        if callable(adopt) and adopt(p):
                            self._adopt_into_engine(ee, sym, sl, summary)
                            held_tickets.add(tkt)
                            claimed_tickets.add(tkt)
                        break
                # 3. manage every engine for this symbol that holds a position
                for sl in sleeves:
                    ee = self._exec_engine(sym, sl)
                    if getattr(ee, "active_trade", None) is not None:
                        if self._reconcile_absent_active_engine(
                            ee,
                            sym,
                            sl,
                            open_tickets,
                            absence_threshold,
                            summary,
                        ):
                            continue
                        self._manage_engine(ee, sym, sl, summary)
            except Exception as e:                                  # never break the loop
                summary["errors"].append({"symbol": sym, "error": repr(e)})
        # OUT-OF-UNIVERSE W7 position alert: a W7-magic position on a symbol NO active sleeve covers cannot
        # be adopted/managed by any engine and would ride silently on the broker SL/TP only -> surface it.
        self._alert_out_of_universe(summary)
        # If a restart happened after broker-side closure, no engine may be alive to observe
        # ``active_trade -> None``. Reconcile durable records against a confirmed open-position
        # snapshot so runtime-learning state does not leave old tickets looking open forever.
        self._reconcile_absent_trade_records(open_positions_snapshot, summary)
        # Revisit already-closed records whose first reconciliation was exit-only or missing fields. When
        # account history now proves fuller accounting, emit a corrected close packet with the same close
        # identity so runtime-learning advisory dedupe supersedes the stale packet without editing logs.
        self._repair_closed_trade_records(summary)
        # LAST-RESORT: flatten every open position + latch new entries OFF if the account nears the
        # prop-fatal daily-loss / static max-DD floor (runs AFTER adoption so every engine reflects the
        # live broker state). Default-off; enabled in the live config.
        now = now_utc or datetime.now(timezone.utc)
        self._apply_breach_flatten(now, summary)
        self._emit_management_runtime_learning(summary, now)
        return summary

    def _alert_out_of_universe(self, summary: dict) -> None:
        """Alert ONCE (per ticket) on a W7-magic open position whose symbol is OUTSIDE the active-sleeve
        universe (a leftover from a retired sleeve/symbol, a wrong-account fill, or a manual W7-tagged
        trade): no engine can manage it, so it would silently ride the broker SL/TP only. NEVER raises."""
        try:
            get_open = getattr(self._mt5, "get_open_positions", None)
            if not callable(get_open):
                return
            from src.mt5.mt5_interface import MAGIC_NUMBER
            manageable_broker: set = set()
            for (canon, _sl) in self._manageable_pairs():
                try:
                    manageable_broker.add(self._broker_symbol(canon))
                except Exception:
                    pass
            for p in (get_open() or []):
                tkt = getattr(p, "ticket", None)
                if tkt is None or tkt in self._oou_alerted:
                    continue
                cmt = (getattr(p, "comment", "") or "")
                is_w7 = (getattr(p, "magic", None) == MAGIC_NUMBER) or cmt.startswith("W7:")
                bsym = getattr(p, "symbol", None)
                if is_w7 and bsym not in manageable_broker:
                    if len(self._oou_alerted) > 5000:
                        self._oou_alerted.clear()
                    self._oou_alerted.add(tkt)
                    summary.setdefault("out_of_universe", []).append(
                        {"ticket": tkt, "symbol": bsym, "comment": cmt})
                    _log.warning("book[%s]: OUT-OF-UNIVERSE W7 position #%s %s (%r) — no active sleeve "
                                 "manages this symbol; broker SL/TP only", self._namespace, tkt, bsym, cmt)
                    self._send_card(f"[{self._account_label()}] ⚠️ Out-of-universe W7 position #{tkt} "
                                    f"{bsym} ({cmt}) — not managed by any sleeve (broker SL/TP only). "
                                    f"Investigate.")
        except Exception:
            pass

    def _open_book_positions_snapshot(self) -> list | None:
        """Return a broker-confirmed snapshot of all open book positions, or None when unavailable.

        A broker-link check, when the MT5 wrapper exposes one, prevents treating a disconnected
        terminal's empty/failed position read as evidence that every local trade record is closed.
        """
        try:
            broker_link = getattr(self._mt5, "broker_link_connected", None)
            if callable(broker_link) and not bool(broker_link()):
                return None
            get_open = getattr(self._mt5, "get_open_positions", None)
            if not callable(get_open):
                return None
            positions = get_open()
            if positions is None:
                return None
            return list(positions)
        except Exception:
            return None

    def _active_engine_tickets(self) -> set[int]:
        tickets: set[int] = set()
        for ee in list(self._exec_engines.values()):
            try:
                ticket = getattr(getattr(ee, "active_trade", None), "ticket", None)
                if ticket not in (None, 0):
                    tickets.add(int(ticket))
            except (TypeError, ValueError):
                continue
        return tickets

    @staticmethod
    def _open_snapshot_ticket_set(open_positions_snapshot: list | None) -> set[int] | None:
        if open_positions_snapshot is None:
            return None
        out: set[int] = set()
        for p in open_positions_snapshot:
            try:
                ticket = int(getattr(p, "ticket", 0) or 0)
            except (TypeError, ValueError):
                continue
            if ticket:
                out.add(ticket)
        return out

    @staticmethod
    def _absence_reconcile_threshold(open_positions_snapshot: list | None) -> int | None:
        if open_positions_snapshot is None:
            return None
        return 2 if len(open_positions_snapshot) == 0 else 1

    def _ticket_absence_confirmed(self, ticket: int, *, threshold: int) -> tuple[bool, int]:
        count = int(self._absent_ticket_observations.get(ticket, 0) or 0) + 1
        self._absent_ticket_observations[ticket] = count
        return count >= max(1, threshold), count

    def _reconcile_absent_active_engine(
        self,
        ee,
        sym: str,
        sleeve: str,
        open_tickets: set[int] | None,
        absence_threshold: int | None,
        summary: dict,
    ) -> bool:
        """Clear a local active_trade when read-only broker truth confirms the ticket is gone."""
        if open_tickets is None or absence_threshold is None:
            return False
        active = getattr(ee, "active_trade", None)
        ticket = getattr(active, "ticket", None)
        if ticket in (None, 0):
            return False
        try:
            ticket_i = int(ticket)
        except (TypeError, ValueError):
            return False
        if ticket_i in open_tickets:
            self._absent_ticket_observations.pop(ticket_i, None)
            return False
        confirmed, observed_count = self._ticket_absence_confirmed(
            ticket_i,
            threshold=absence_threshold,
        )
        if not confirmed:
            return False
        try:
            broker_symbol = self._broker_symbol(sym)
        except Exception:
            broker_symbol = None
        checked_at = datetime.now(timezone.utc).isoformat()
        record = self._load_trade_record(ticket_i)
        closed_record = self._mark_trade_record_closed(
            ticket_i,
            "broker_closed_absent_on_reconcile",
            checked_at,
            record=record,
            broker_symbol=broker_symbol,
            sleeve=sleeve,
            symbol=sym,
        )
        try:
            ee.active_trade = None
        except Exception:
            pass
        join_ctx = self._runtime_learning_trade_context(
            ticket=ticket_i,
            record=closed_record or record,
            broker_symbol=broker_symbol,
            management_checked_at_utc=checked_at,
        )
        row = {
            "symbol": sym,
            "sleeve": sleeve,
            "action": "broker_closed_absent_on_reconcile",
            "broker_mutation_allowed": False,
            "source_completeness_status": "active_trade_absent_from_confirmed_open_snapshot",
            "broker_position_absence_observation_count": observed_count,
            "broker_position_absence_required_confirmations": absence_threshold,
            **join_ctx,
        }
        summary.setdefault("closed", []).append(row)
        self._absent_ticket_observations.pop(ticket_i, None)
        return True

    def _reconcile_absent_trade_records(self, open_positions_snapshot: list | None, summary: dict) -> None:
        """Mark stale local trade records closed when broker-open truth no longer contains their ticket.

        This is local evidence repair only. A non-empty snapshot closes missing
        tickets immediately; an all-empty snapshot requires two consecutive
        observations so a transient broker read miss does not mark every record
        closed.
        """
        if open_positions_snapshot is None:
            return
        try:
            open_tickets = self._open_snapshot_ticket_set(open_positions_snapshot)
            if open_tickets is None:
                return
            absence_threshold = self._absence_reconcile_threshold(open_positions_snapshot)
            if absence_threshold is None:
                return
            active_tickets = self._active_engine_tickets()
            for path in sorted(self._trade_record_path().glob("*.json")):
                try:
                    ticket = int(path.stem)
                except (TypeError, ValueError):
                    continue
                if ticket in open_tickets:
                    self._absent_ticket_observations.pop(ticket, None)
                    continue
                if ticket in active_tickets:
                    continue
                confirmed, observed_count = self._ticket_absence_confirmed(
                    ticket,
                    threshold=absence_threshold,
                )
                if not confirmed:
                    continue
                record = self._load_trade_record(ticket)
                if not isinstance(record, dict):
                    continue
                if record.get("trade_lifecycle_status") == "closed":
                    self._absent_ticket_observations.pop(ticket, None)
                    continue
                symbol = record.get("symbol")
                sleeve = record.get("sleeve")
                execution = record.get("execution") if isinstance(record.get("execution"), dict) else {}
                broker_symbol = execution.get("broker_symbol")
                checked_at = datetime.now(timezone.utc).isoformat()
                closed_record = self._mark_trade_record_closed(
                    ticket,
                    "broker_closed_absent_on_reconcile",
                    checked_at,
                    record=record,
                    broker_symbol=broker_symbol,
                    sleeve=sleeve,
                    symbol=symbol,
                )
                join_ctx = self._runtime_learning_trade_context(
                    ticket=ticket,
                    record=closed_record or record,
                    broker_symbol=broker_symbol,
                    management_checked_at_utc=checked_at,
                )
                row = {
                    "symbol": symbol,
                    "sleeve": sleeve,
                    "action": "broker_closed_absent_on_reconcile",
                    "source_completeness_status": "trade_record_absent_from_confirmed_open_snapshot",
                    "broker_position_absence_observation_count": observed_count,
                    "broker_position_absence_required_confirmations": absence_threshold,
                    **join_ctx,
                }
                summary.setdefault("closed", []).append(row)
                self._absent_ticket_observations.pop(ticket, None)
        except Exception as e:
            summary.setdefault("errors", []).append(
                {"symbol": "*", "error": f"absent_trade_record_reconcile:{e!r}"}
            )

    def _repair_closed_trade_records(self, summary: dict) -> None:
        try:
            import json
            for path in sorted(self._trade_record_path().glob("*.json")):
                try:
                    ticket = int(path.stem)
                except (TypeError, ValueError):
                    continue
                try:
                    record = json.loads(path.read_text(encoding="utf-8"))
                except Exception:
                    continue
                if not isinstance(record, dict) or record.get("trade_lifecycle_status") != "closed":
                    continue
                record, changed = self._normalize_trade_record(ticket, record)
                if not changed:
                    continue
                self._record_closed_trade_daily_pnl(
                    ticket,
                    record,
                    record.get("close_action") or "broker_closed",
                )
                self._write_trade_record(ticket, record, context="closed trade-record reconciliation repair")
                execution = record.get("execution") if isinstance(record.get("execution"), dict) else {}
                checked_at = datetime.now(timezone.utc).isoformat()
                broker_symbol = execution.get("broker_symbol")
                join_ctx = self._runtime_learning_trade_context(
                    ticket=ticket,
                    record=record,
                    broker_symbol=broker_symbol,
                    management_checked_at_utc=checked_at,
                )
                summary.setdefault("closed", []).append({
                    "symbol": record.get("symbol"),
                    "sleeve": record.get("sleeve"),
                    "action": record.get("close_action") or "broker_closed",
                    "source_completeness_status": "closed_trade_record_account_history_repaired",
                    **join_ctx,
                })
        except Exception as e:
            summary.setdefault("errors", []).append(
                {"symbol": "*", "error": f"closed_trade_record_repair:{e!r}"}
            )

    def _flatten_flag_present(self) -> bool:
        """Operator FLATTEN brake: a shared pipeline_state/ULTIMATE_BOOK_FLATTEN.flag flattens BOTH books;
        a per-namespace .../<ns>/FLATTEN.flag flattens just this one. Sits beside the kill flag (which only
        blocks NEW entries) as the OPEN-position brake. Best-effort; any error -> False."""
        try:
            from pathlib import Path
            base = Path(self._repo_root) / "pipeline_state"
            return ((base / "ULTIMATE_BOOK_FLATTEN.flag").exists()
                    or (base / "ultimate_book" / (self._namespace or "book") / "FLATTEN.flag").exists())
        except Exception:
            return False

    def _flatten_all_engines(self, summary: dict, action: str) -> None:
        """Close every engine that still holds a position; record + isolate per-engine failures (retried
        next tick while the latch holds). NEVER raises."""
        if not self._live_broker_authority():
            summary.setdefault("managed", []).append({
                "symbol": "*",
                "sleeve": "*",
                "action": f"{action}_suppressed_live_broker_authority_false",
                "live_broker_authority": False,
                "broker_mutation_allowed": False,
                "source_completeness_status": "flatten_request_observed_broker_mutation_disabled",
            })
            return
        for (sym, sl), ee in list(self._exec_engines.items()):
            if getattr(ee, "active_trade", None) is None:
                continue
            active_before = getattr(ee, "active_trade", None)
            ticket = getattr(active_before, "ticket", None)
            record = self._load_trade_record(ticket) if ticket is not None else None
            try:
                broker_symbol = self._broker_symbol(sym)
            except Exception:
                broker_symbol = None
            checked_at = datetime.now(timezone.utc).isoformat()
            join_ctx = self._runtime_learning_trade_context(
                ticket=ticket,
                record=record,
                broker_symbol=broker_symbol,
                management_checked_at_utc=checked_at,
            )
            try:
                if ee.close_position(f"vnext_{action}"):
                    closed_record = self._mark_trade_record_closed(
                        ticket,
                        action,
                        checked_at,
                        record=record,
                        broker_symbol=broker_symbol,
                        sleeve=sl,
                        symbol=sym,
                    )
                    if closed_record is not None:
                        join_ctx.update(self._runtime_learning_trade_context(
                            ticket=ticket,
                            record=closed_record,
                            broker_symbol=broker_symbol,
                            management_checked_at_utc=checked_at,
                        ))
                    summary["closed"].append({"symbol": sym, "sleeve": sl, "action": action, **join_ctx})
                else:
                    summary["errors"].append({"symbol": sym, "sleeve": sl, "error": f"{action}_close_failed"})
            except Exception as e:
                summary["errors"].append({"symbol": sym, "sleeve": sl, "error": f"{action}:{e!r}"})

    def _apply_breach_flatten(self, now_utc, summary: dict) -> None:
        """Flatten every open book position + latch new entries OFF on either an OPERATOR FLATTEN flag
        (immediate) or a governor breach near the prop-fatal daily-loss / static max-DD floor (with N-tick
        hysteresis so a transient equity wick can't trigger). NEVER raises."""
        # (1) OPERATOR FLATTEN flag -> immediate, no hysteresis (an explicit operator request).
        if self._flatten_flag_present():
            self._breach_block = True
            self._flatten_all_engines(summary, "operator_flatten")
            if not self._live_broker_authority():
                if not self._breach_alerted:
                    self._breach_alerted = True
                    _log.warning(
                        "book[%s]: OPERATOR FLATTEN flag observed, but live broker authority is false "
                        "-> no broker mutation; new entries OFF",
                        self._namespace,
                    )
                return
            if not self._breach_alerted:
                self._breach_alerted = True
                _log.warning("book[%s]: OPERATOR FLATTEN flag -> all positions closed, new entries OFF",
                             self._namespace)
                self._send_card(f"[{self._account_label()}] 🛑 OPERATOR FLATTEN flag — all book positions "
                                f"CLOSED, new entries OFF (remove the flag to resume)")
            return
        # (2) governor breach.
        try:
            verdict = self.engine.breach_flatten_check(now_utc)
        except Exception:
            verdict = None
        if verdict is None:
            return   # disabled or unassessable -> leave the prior latch untouched (FAIL-SAFE)
        if not verdict.get("flatten"):
            self._breach_ticks = 0
            if self._breach_block:                      # breach/flag cleared -> re-enable placement
                self._breach_block = False
                self._breach_alerted = False
                _log.info("book[%s]: breach/flatten cleared -> placement re-enabled", self._namespace)
            return
        self._breach_ticks += 1
        if self._breach_ticks < self._breach_confirm:
            return   # wait for confirmation (hysteresis vs a transient equity wick)
        self._breach_block = True                       # latch new entries OFF (run_cycle reads this)
        self._flatten_all_engines(summary, "breach_flatten")
        if not self._live_broker_authority():
            if not self._breach_alerted:
                self._breach_alerted = True
                _log.warning(
                    "book[%s]: BREACH FLATTEN observed (%s), but live broker authority is false "
                    "-> no broker mutation; new entries OFF",
                    self._namespace,
                    verdict.get("reason"),
                )
            return
        if not self._breach_alerted:                    # alert ONCE per breach episode
            self._breach_alerted = True
            m = verdict.get("metrics", {})
            _log.warning("book[%s]: BREACH FLATTEN (%s) metrics=%s",
                         self._namespace, verdict.get("reason"), m)
            self._send_card(f"[{self._account_label()}] 🛑 BREACH FLATTEN — {verdict.get('reason')} "
                            f"(equity ${m.get('equity', 0):,.0f}); all book positions CLOSED, new entries OFF")

    def _adopt_into_engine(self, ee, sym: str, sleeve: str, summary: dict) -> None:
        """Record an adoption, flag the position book-native (so generic overlays do not override the
        sleeve's validated exit), and restore its persisted dynamic policy when a trade record exists."""
        ticket = getattr(ee.active_trade, "ticket", None)
        row = {"symbol": sym, "sleeve": sleeve, "ticket": ticket}
        try:
            ee.active_trade.gtos_vnext_book_native_exit_management = True
        except Exception:
            pass
        record = self._rehydrate_policy(ee, sleeve, sym)
        try:
            broker_symbol = self._broker_symbol(sym)
        except Exception:
            broker_symbol = None
        row.update(self._runtime_learning_trade_context(
            ticket=ticket,
            record=record,
            broker_symbol=broker_symbol,
        ))
        row.update(self._broker_position_protection(ticket, broker_symbol))
        summary["adopted"].append(row)

    def _manage_engine(self, ee, sym: str, sleeve: str, summary: dict) -> None:
        """Apply the time-stop + tick-driven exit management for one engine; record close + notify."""
        ts_action = None
        active_before = getattr(ee, "active_trade", None)
        ticket = getattr(active_before, "ticket", None)
        record = self._load_trade_record(ticket) if ticket is not None else None
        try:
            broker_symbol = self._broker_symbol(sym)
        except Exception:
            broker_symbol = None
        checked_at = datetime.now(timezone.utc).isoformat()
        broker_protection = self._broker_position_protection(ticket, broker_symbol)
        if getattr(ee, "active_trade", None) is not None:
            record = self._mark_trade_record_management_checked(
                ticket,
                checked_at,
                record=record,
                broker_symbol=broker_symbol,
                sleeve=sleeve,
                symbol=sym,
                broker_protection=broker_protection,
            ) or record
        join_ctx = self._runtime_learning_trade_context(
            ticket=ticket,
            record=record,
            broker_symbol=broker_symbol,
            management_checked_at_utc=checked_at,
        )
        if not self._live_broker_authority():
            managed_row = {
                "symbol": sym,
                "sleeve": sleeve,
                "action": "live_broker_authority_false_observe_only",
                "live_broker_authority": False,
                "broker_mutation_allowed": False,
                "source_completeness_status": "runtime_management_observed_broker_mutation_disabled",
                **join_ctx,
            }
            summary["managed"].append(managed_row)
            return
        try:
            ts_close = getattr(ee, "check_time_stop_and_close", None)
            if callable(ts_close):
                ts_action = ts_close()
            policy_clock = None
            get_clock = getattr(ee, "get_time_stop_clock_diagnostic", None)
            if callable(get_clock):
                policy_clock = get_clock()
            if policy_clock is None:
                policy_clock = getattr(ee, "_last_time_stop_clock_diagnostic", None)
            join_ctx.update(self._runtime_learning_policy_clock_context(policy_clock))
        except Exception as exc:  # noqa: BLE001 - management must continue, but the fault must be visible.
            policy_clock = {
                "schema_version": "gtos.vnext.time_stop_clock_diagnostic.v1",
                "checked_at_utc": checked_at,
                "status": "exception",
                "ticket": ticket,
                "error": repr(exc),
            }
            join_ctx.update(self._runtime_learning_policy_clock_context(policy_clock))
            error_row = {
                "symbol": sym,
                "sleeve": sleeve,
                "action": "time_stop_check_exception",
                "error": repr(exc),
                **join_ctx,
            }
            summary["errors"].append(error_row)
            _log.warning(
                "book[%s]: time-stop check failed for %s/%s ticket=%s: %r",
                self._namespace,
                sym,
                sleeve,
                ticket,
                exc,
            )
        # If the time-stop ALREADY closed the position, record THAT close (with its real reason) and do
        # NOT run check_and_manage_trade on a now-closed engine (which would relabel the close as a generic
        # no-op action and lose the time-stop reason).
        if getattr(ee, "active_trade", None) is None:
            close_action = ts_action or "vnext_time_stop"
            closed_record = self._mark_trade_record_closed(
                ticket,
                close_action,
                checked_at,
                record=record,
                broker_symbol=broker_symbol,
                sleeve=sleeve,
                symbol=sym,
            )
            if closed_record is not None:
                join_ctx.update(self._runtime_learning_trade_context(
                    ticket=ticket,
                    record=closed_record,
                    broker_symbol=broker_symbol,
                    management_checked_at_utc=checked_at,
                ))
            managed_row = {"symbol": sym, "sleeve": sleeve, "action": close_action, **join_ctx}
            summary["managed"].append(managed_row)
            summary["closed"].append(dict(managed_row))
            self._notify_closed(sym, close_action, closed_record=closed_record)
            return
        action = ee.check_and_manage_trade({})          # tick-driven exit management
        if getattr(ee, "active_trade", None) is not None:
            refreshed_protection = self._broker_position_protection(ticket, broker_symbol)
            if refreshed_protection:
                record = self._mark_trade_record_management_checked(
                    ticket,
                    checked_at,
                    record=record,
                    broker_symbol=broker_symbol,
                    sleeve=sleeve,
                    symbol=sym,
                    broker_protection=refreshed_protection,
                ) or record
                join_ctx.update(self._runtime_learning_trade_context(
                    ticket=ticket,
                    record=record,
                    broker_symbol=broker_symbol,
                    management_checked_at_utc=checked_at,
                ))
        managed_row = {"symbol": sym, "sleeve": sleeve, "action": action, **join_ctx}
        summary["managed"].append(managed_row)
        if getattr(ee, "active_trade", None) is None:
            closed_record = self._mark_trade_record_closed(
                ticket,
                action,
                checked_at,
                record=record,
                broker_symbol=broker_symbol,
                sleeve=sleeve,
                symbol=sym,
            )
            if closed_record is not None:
                managed_row.update(self._runtime_learning_trade_context(
                    ticket=ticket,
                    record=closed_record,
                    broker_symbol=broker_symbol,
                    management_checked_at_utc=checked_at,
                ))
            summary["closed"].append(dict(managed_row))
            self._notify_closed(sym, action, closed_record=closed_record)

    def _open_book_positions_by_canonical(self, canon_symbols, *, open_positions_snapshot=None) -> dict:
        """Snapshot all open book positions (magic-filtered) once, keyed by CANONICAL symbol. Returns {}
        when the mt5 lacks get_open_positions (mocks) -> the per-pair comment-routed reconcile still runs."""
        out: dict = {}
        try:
            if open_positions_snapshot is None:
                open_positions_snapshot = self._open_book_positions_snapshot()
            if open_positions_snapshot is None:
                return out
            b2c: dict[str, list[str]] = {}
            for c in canon_symbols:
                try:
                    b2c.setdefault(self._broker_symbol(c), []).append(c)
                except Exception:
                    pass
            for p in (open_positions_snapshot or []):
                for canon in (b2c.get(getattr(p, "symbol", None)) or []):
                    out.setdefault(canon, []).append(p)
        except Exception:
            pass
        return out

    def _manageable_pairs(self) -> list:
        """(canonical symbol, sleeve) pairs this profile can hold = each active sleeve x its on_surface
        symbols that have an instrument config on this profile. Cached. The redacted_account follower lacks some
        crosses/legs, so those (symbol, sleeve) pairs are dropped (a position can't exist on them here)."""
        cached = getattr(self, "_manageable_pairs_cache", None)
        if cached is not None:
            return cached
        from .sleeves.registry import active_specs
        rt = self.base_config.get("gtos_vnext_runtime", self.base_config) or {}
        include_candidate_book = config_bool_value(rt.get("ultimate_book_include_candidate_book", False), False)
        include_market_expansion_book = config_bool_value(
            rt.get("ultimate_book_include_market_expansion_book", False),
            False,
        )
        candidate_sleeves = self._candidate_book_sleeves()
        expansion_sleeves = self._market_expansion_sleeves()
        pairs = []
        for spec in active_specs(
            None,
            include_candidate_book=include_candidate_book,
            candidate_book_sleeves=candidate_sleeves or None,
            include_market_expansion_book=include_market_expansion_book,
            market_expansion_sleeves=expansion_sleeves or None,
        ):
            for s in (spec.on_surface or []):
                if self._profile_supports_symbol(s):
                    pairs.append((s, spec.tag))
        self._manageable_pairs_cache = pairs
        return pairs

    def _rehydrate_policy(self, ee, sleeve=None, symbol=None) -> dict | None:
        """After adopting an orphan, restore its vNext exit policy so management is the exact validated
        lifecycle (not generic). Prefer the persisted on-disk trade record; if it is MISSING
        (adopt-missing-record) reconstruct the sleeve's NATIVE policy from its identity (the W7:{sleeve}
        comment) so the adopted position keeps its validated time-stop / scale-out / target rather than
        degrading to the generic floor. Best-effort; NEVER raises."""
        try:
            ticket = getattr(getattr(ee, "active_trade", None), "ticket", None)
            rec = self._load_trade_record(ticket) if ticket is not None else None
            if rec is None and sleeve:
                from .execution_packets import native_policy_instrumentation
                rec = {"instrumentation": native_policy_instrumentation(
                           sleeve, frontier_exits=self._frontier_exits),
                       "execution": {"ticket": ticket}, "sleeve": sleeve, "symbol": symbol,
                       "reconstructed_from_sleeve_identity": True}
                _log.warning("book[%s]: ticket %s adopted with NO trade record -> rehydrated the '%s' "
                             "NATIVE exit policy from the W7 comment (time-stop/scale-out restored, not "
                             "the generic floor)", self._namespace, ticket, sleeve)
                self._persist_reconstructed_trade_record(ticket, rec)
            hyd = getattr(ee, "hydrate_vnext_dynamic_policy_from_record", None)
            if rec is not None and callable(hyd):
                rec = dict(rec)
                if self._live_broker_authority():
                    hydrated = bool(hyd(rec))
                else:
                    try:
                        hydrated = bool(hyd(rec, modify_broker_tp=False))
                    except TypeError:
                        rec["rehydration_status"] = (
                            "skipped_hydrator_without_read_only_kwarg_broker_authority_false"
                        )
                        return rec
                rec["rehydration_status"] = "hydrated" if hydrated else "hydrate_returned_false"
            elif rec is not None:
                rec = dict(rec)
                rec["rehydration_status"] = "hydrator_unavailable"
            elif sleeve:
                rec = {
                    "execution": {"ticket": ticket},
                    "sleeve": sleeve,
                    "symbol": symbol,
                    "rehydration_status": "missing_trade_record_native_reconstruction_unavailable",
                }
            return rec
        except Exception as exc:  # noqa: BLE001 - adoption must continue, but packets must show the fault.
            _log.warning(
                "book[%s]: ticket %s policy rehydration failed for %s/%s: %r",
                self._namespace,
                getattr(getattr(ee, "active_trade", None), "ticket", None),
                symbol,
                sleeve,
                exc,
            )
            return {
                "execution": {
                    "ticket": getattr(getattr(ee, "active_trade", None), "ticket", None),
                },
                "sleeve": sleeve,
                "symbol": symbol,
                "rehydration_status": "exception",
                "rehydration_error": repr(exc),
            }

    # ---------------- trade-record persistence (cross-restart policy rehydration) ----------------
    def _trade_record_path(self):
        from pathlib import Path
        d = Path(self._repo_root) / "pipeline_state" / "ultimate_book" / self._namespace / "trade_records"
        return d

    def _write_trade_record(self, ticket, record: dict, *, context: str = "trade-record persist") -> bool:
        if ticket in (None, 0) or not isinstance(record, dict):
            return False
        try:
            import json
            import os
            from pathlib import Path

            d = self._trade_record_path()
            d.mkdir(parents=True, exist_ok=True)
            p = Path(d) / f"{ticket}.json"
            tmp = Path(str(p) + ".tmp")
            tmp.write_text(json.dumps(record, default=str), encoding="utf-8")
            os.replace(str(tmp), str(p))
            return True
        except Exception as e:
            _log.warning("book[%s]: %s FAILED for ticket %s (%r); exit-policy "
                         "rehydration may fall back after a restart",
                         self._namespace, context, ticket, e)
            return False

    @staticmethod
    def _set_record_value(mapping: dict, key: str, value: Any) -> bool:
        if value in (None, ""):
            return False
        if mapping.get(key) in (None, ""):
            mapping[key] = value
            return True
        return False

    def _merge_entry_reconciliation_from_record(self, record: dict) -> bool:
        if not isinstance(record, dict):
            return False
        inst = record.get("instrumentation") if isinstance(record.get("instrumentation"), dict) else {}
        packet = inst.get("gtos_vnext_broker_order_lifecycle_capture_v4_packet")
        if not isinstance(packet, dict):
            packet = inst.get("broker_order_lifecycle_capture_v4")
        if not isinstance(packet, dict):
            return False
        deal = packet.get("deal_cost_reconciliation")
        if not isinstance(deal, dict):
            return False
        changed = False
        execution = record.get("execution")
        if not isinstance(execution, dict):
            execution = {}
            record["execution"] = execution
            changed = True
        changed = self._set_record_value(
            execution, "broker_entry_deal_ticket", deal.get("deal_ticket")
        ) or changed
        changed = self._set_record_value(
            execution, "broker_fill_time_utc", deal.get("broker_fill_time_utc")
        ) or changed
        changed = self._set_record_value(
            execution, "broker_entry_price", deal.get("broker_entry_price")
        ) or changed
        changed = self._set_record_value(
            execution, "broker_entry_commission", deal.get("commission")
        ) or changed
        changed = self._set_record_value(
            execution, "broker_entry_swap", deal.get("swap")
        ) or changed
        changed = self._set_record_value(
            execution, "broker_entry_source_status", deal.get("source_status")
        ) or changed
        changed = self._set_record_value(
            execution,
            "entry_reconciliation_status",
            deal.get("account_history_lookup_status") or packet.get("status"),
        ) or changed
        missing_fields = deal.get("missing_fields") or packet.get("missing_fields")
        if isinstance(missing_fields, list) and missing_fields and execution.get("broker_entry_missing_fields") in (None, ""):
            execution["broker_entry_missing_fields"] = list(missing_fields)
            changed = True
        changed = self._set_record_value(
            record,
            "entry_reconciliation_status",
            deal.get("account_history_lookup_status") or packet.get("status"),
        ) or changed
        if packet.get("broker_real_entry_label_ready") is not None and record.get("broker_real_entry_label_ready") is None:
            record["broker_real_entry_label_ready"] = bool(packet.get("broker_real_entry_label_ready"))
            changed = True
        if isinstance(packet.get("missing_fields"), list) and packet.get("missing_fields") and record.get("broker_real_missing_fields") in (None, ""):
            record["broker_real_missing_fields"] = list(packet.get("missing_fields"))
            changed = True
        return changed

    @staticmethod
    def _missingish_ticket(value: Any) -> bool:
        try:
            return value in (None, "", 0, "0")
        except Exception:
            return True

    @classmethod
    def _entry_reconciliation_missing_fields(cls, accounting: dict) -> list[str]:
        missing: list[str] = []
        if cls._missingish_ticket(accounting.get("broker_entry_deal_ticket")):
            missing.append("broker_entry_deal_ticket")
        if accounting.get("broker_fill_time_utc") in (None, ""):
            missing.append("broker_fill_time_utc")
        if accounting.get("broker_entry_price") in (None, ""):
            missing.append("broker_entry_price")
        if accounting.get("broker_entry_commission") is None:
            missing.append("commission")
        if accounting.get("broker_entry_swap") is None:
            missing.append("swap")
        return missing

    @staticmethod
    def _iso_from_deal_time_near_reference(
        value: Any,
        reference: datetime | None,
        *,
        max_shift_hours: int = 6,
        tolerance_minutes: int = 10,
    ) -> tuple[str | None, int | None]:
        iso = UltimateBookOwner._iso_from_deal_time(value)
        if not iso or reference is None:
            return iso, None
        try:
            dt = datetime.fromisoformat(str(iso).replace("Z", "+00:00"))
        except (TypeError, ValueError):
            return iso, None
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        dt = dt.astimezone(timezone.utc)
        ref = reference
        if ref.tzinfo is None:
            ref = ref.replace(tzinfo=timezone.utc)
        ref = ref.astimezone(timezone.utc)

        best = dt
        best_shift = 0
        best_distance = abs((dt - ref).total_seconds())
        for hours in range(-int(max_shift_hours), int(max_shift_hours) + 1):
            candidate = dt - timedelta(hours=hours)
            distance = abs((candidate - ref).total_seconds())
            if distance < best_distance:
                best = candidate
                best_shift = hours
                best_distance = distance
        if best_shift and best_distance <= int(tolerance_minutes) * 60:
            return best.isoformat(), best_shift * 3600
        return dt.isoformat(), None

    @staticmethod
    def _is_entry_deal_for_ticket(deal: Any, ticket: int) -> bool:
        try:
            entry = int(UltimateBookOwner._deal_value(deal, "entry", 0) or 0)
        except (TypeError, ValueError):
            entry = 0
        if entry not in {0}:
            return False
        for field in ("position_id", "order"):
            try:
                if int(UltimateBookOwner._deal_value(deal, field, 0) or 0) == int(ticket):
                    return True
            except (TypeError, ValueError):
                continue
        return False

    def _entry_reconciliation_window(self, record: dict) -> tuple[datetime | None, datetime | None, datetime | None]:
        inst = record.get("instrumentation") if isinstance(record.get("instrumentation"), dict) else {}
        packet = inst.get("gtos_vnext_broker_order_lifecycle_capture_v4_packet")
        if not isinstance(packet, dict):
            packet = inst.get("broker_order_lifecycle_capture_v4")
        order_obs = packet.get("order_send_observation") if isinstance(packet, dict) else {}
        if not isinstance(order_obs, dict):
            order_obs = {}
        execution = record.get("execution") if isinstance(record.get("execution"), dict) else {}
        order_send = self._parse_utc(order_obs.get("order_send_time_utc"))
        order_result = self._parse_utc(order_obs.get("order_result_time_utc"))
        placed = self._parse_utc(execution.get("placed_at_utc"))
        anchor = order_result or order_send or placed
        if not anchor:
            return None, None, None
        start = (order_send or anchor) - timedelta(minutes=5)
        end = (order_result or anchor) + timedelta(minutes=5)
        return start, end, anchor

    def _repair_entry_reconciliation_from_account_history(self, ticket: int, record: dict) -> bool:
        """Self-heal unresolved entry accounting once MT5 account history becomes available.

        This is read-only broker history inspection. It never sends, modifies, or closes orders.
        """
        if not isinstance(record, dict):
            return False
        try:
            ticket_i = int(ticket)
        except (TypeError, ValueError):
            return False
        execution = record.setdefault("execution", {})
        status = execution.get("entry_reconciliation_status") or record.get("entry_reconciliation_status")
        current_missing = self._entry_reconciliation_missing_fields(execution)
        if status == "RECONCILED_FROM_ACCOUNT_HISTORY" and not current_missing:
            return False

        now = datetime.now(timezone.utc)
        last_attempt = self._entry_reconciliation_repair_last_attempt_utc.get(ticket_i)
        if last_attempt and (now - last_attempt).total_seconds() < 900:
            return False
        self._entry_reconciliation_repair_last_attempt_utc[ticket_i] = now

        broker_symbol = execution.get("broker_symbol")
        if not broker_symbol and record.get("symbol") not in (None, ""):
            try:
                broker_symbol = self._broker_symbol(record.get("symbol"))
            except Exception:
                broker_symbol = record.get("symbol")
        if not broker_symbol:
            return False
        start_utc, end_utc, reference = self._entry_reconciliation_window(record)
        if not start_utc or not end_utc:
            return False

        def _find(deals: list[Any]) -> Any | None:
            for deal in deals or []:
                if self._is_entry_deal_for_ticket(deal, ticket_i):
                    return deal
            return None

        match = None
        source_status = "broker_real_symbol_history_entry_reconciled"
        recovery_window_used = False
        history_fetch_failed = False
        history_source_returned = False
        history_fetch_error = None
        get_symbol_deals = getattr(self._mt5, "get_history_deals", None)
        if callable(get_symbol_deals):
            try:
                deals = get_symbol_deals(start_utc, end_utc, broker_symbol)
            except Exception as exc:
                deals = None
                history_fetch_failed = True
                history_fetch_error = repr(exc)
            if deals is None:
                history_fetch_failed = True
                history_fetch_error = history_fetch_error or "get_history_deals_returned_none"
            else:
                history_source_returned = True
                match = _find(deals)
            if match is None:
                recovery_start = start_utc - timedelta(hours=6)
                recovery_end = end_utc + timedelta(hours=6)
                try:
                    deals = get_symbol_deals(recovery_start, recovery_end, broker_symbol)
                except Exception as exc:
                    deals = None
                    history_fetch_failed = True
                    history_fetch_error = repr(exc)
                if deals is None:
                    history_fetch_failed = True
                    history_fetch_error = history_fetch_error or "get_history_deals_returned_none"
                else:
                    history_source_returned = True
                    match = _find(deals)
                    if match is not None:
                        source_status = "broker_real_symbol_history_entry_reconciled_recovery_window"
                        recovery_window_used = True

        if match is None:
            get_all_deals = getattr(self._mt5, "get_account_history_deals", None)
            if callable(get_all_deals):
                recovery_start = start_utc - timedelta(hours=6)
                recovery_end = end_utc + timedelta(hours=6)
                try:
                    deals = get_all_deals(recovery_start, recovery_end)
                except Exception as exc:
                    deals = None
                    history_fetch_failed = True
                    history_fetch_error = repr(exc)
                if deals is None:
                    history_fetch_failed = True
                    history_fetch_error = history_fetch_error or "get_account_history_deals_returned_none"
                else:
                    history_source_returned = True
                    match = _find(deals)
                    if match is not None:
                        source_status = "broker_real_account_history_entry_reconciled_recovery_window"
                        recovery_window_used = True

        if match is None:
            if history_fetch_failed and not history_source_returned:
                execution["entry_reconciliation_status"] = "ACCOUNT_HISTORY_LOOKUP_FAILED"
                execution["broker_entry_source_status"] = "account_history_lookup_failed"
                execution["entry_reconciliation_repair_status"] = "ACCOUNT_HISTORY_LOOKUP_FAILED"
                execution["entry_reconciliation_repair_error"] = history_fetch_error
                record["entry_reconciliation_status"] = "ACCOUNT_HISTORY_LOOKUP_FAILED"
                record["broker_real_entry_label_ready"] = False
                record["broker_real_missing_fields"] = self._entry_reconciliation_missing_fields(execution)
                record["gtos_vnext_broker_entry_reconciliation_repair_v1_packet"] = {
                    "status": "ACCOUNT_HISTORY_LOOKUP_FAILED",
                    "missing_fields": record["broker_real_missing_fields"],
                    "error": history_fetch_error,
                }
                return True
            return False

        fill_time, fill_time_alignment_offset = self._iso_from_deal_time_near_reference(
            self._deal_value(match, "time"),
            reference,
        )
        deal_ticket = self._deal_value(match, "ticket")
        order_ticket = self._deal_value(match, "order")
        position_id = self._deal_value(match, "position_id")
        price = self._deal_value(match, "price")
        commission = self._deal_value(match, "commission")
        swap = self._deal_value(match, "swap")
        repaired_accounting = {
            "broker_entry_deal_ticket": deal_ticket,
            "broker_fill_time_utc": fill_time,
            "broker_entry_price": price,
            "broker_entry_commission": commission,
            "broker_entry_swap": swap,
        }
        missing_fields = self._entry_reconciliation_missing_fields(repaired_accounting)
        repaired_status = (
            "RECONCILED_FROM_ACCOUNT_HISTORY"
            if not missing_fields
            else "ACCOUNT_HISTORY_ENTRY_FOUND_INCOMPLETE"
        )

        execution.update(
            {
                "broker_entry_deal_ticket": deal_ticket,
                "broker_fill_time_utc": fill_time,
                "broker_entry_price": price,
                "broker_entry_commission": commission,
                "broker_entry_swap": swap,
                "broker_entry_source_status": source_status,
                "entry_reconciliation_status": repaired_status,
                "broker_entry_missing_fields": missing_fields,
                "entry_reconciliation_repair_status": repaired_status,
                "entry_reconciliation_repair_checked_at_utc": now.isoformat(),
                "entry_reconciliation_repair_source_status": source_status,
                "entry_reconciliation_repair_recovery_window_used": recovery_window_used,
                "entry_reconciliation_repair_match_keys": {
                    "matched_by": "position_id_or_order_ticket",
                    "ticket": deal_ticket,
                    "order": order_ticket,
                    "position_id": position_id,
                    "price": price,
                    "recovery_window_used": recovery_window_used,
                },
            }
        )
        if fill_time_alignment_offset is not None:
            execution["broker_fill_time_alignment_offset_seconds"] = fill_time_alignment_offset
        record["entry_reconciliation_status"] = repaired_status
        record["broker_real_entry_label_ready"] = not missing_fields
        record["broker_real_missing_fields"] = missing_fields
        record["gtos_vnext_broker_entry_reconciliation_repair_v1_packet"] = {
            "schema_version": "broker_entry_reconciliation_repair_v1",
            "component": "ultimate_book_trade_record_entry_reconciliation_repair",
            "generated_at_utc": now.isoformat(),
            "status": repaired_status,
            "runtime_effect_boundary": "read_only_account_history_no_broker_mutation",
            "identity": {
                "ticket": ticket_i,
                "symbol": record.get("symbol"),
                "broker_symbol": broker_symbol,
                "candidate_id": record.get("candidate_id"),
            },
            "lookup_window_start_utc": start_utc.isoformat(),
            "lookup_window_end_utc": end_utc.isoformat(),
            "source_status": source_status,
            "match_keys": execution["entry_reconciliation_repair_match_keys"],
            "missing_fields": missing_fields,
        }
        return True

    def _normalize_trade_record(self, ticket, record: dict) -> tuple[dict, bool]:
        """Backfill legacy trade records with durable runtime-learning join keys."""
        if not isinstance(record, dict):
            return record, False
        changed = False
        try:
            ticket_i = int(ticket)
        except (TypeError, ValueError):
            ticket_i = ticket

        execution = record.get("execution")
        if not isinstance(execution, dict):
            execution = {}
            record["execution"] = execution
            changed = True

        changed = self._set_record_value(execution, "ticket", ticket_i) or changed
        changed = self._set_record_value(
            execution, "ticket_hash_sha256", self._runtime_learning_ticket_hash(ticket_i)
        ) or changed
        if record.get("trade_lifecycle_status") in (None, "") and record.get("closed_at_utc") in (None, ""):
            record["trade_lifecycle_status"] = "open"
            changed = True

        row = None
        try:
            row = self._ledger.row_for_ticket(ticket_i)
        except Exception:
            row = None
        if isinstance(row, dict):
            for key in ("sleeve", "symbol", "decision_bar_iso", "decision_day", "cluster", "candidate_id"):
                changed = self._set_record_value(record, key, row.get(key)) or changed
            changed = self._set_record_value(execution, "placed_at_utc", row.get("ts")) or changed

        if record.get("decision_day") in (None, "") and record.get("decision_bar_iso"):
            record["decision_day"] = str(record.get("decision_bar_iso"))[:10]
            changed = True
        if record.get("cluster") in (None, "") and record.get("sleeve") not in (None, ""):
            changed = self._set_record_value(record, "cluster", cluster_of(record.get("sleeve"))) or changed
        if execution.get("broker_symbol") in (None, "") and record.get("symbol") not in (None, ""):
            try:
                changed = self._set_record_value(
                    execution, "broker_symbol", self._broker_symbol(record.get("symbol"))
                ) or changed
            except Exception:
                pass
        changed = self._merge_entry_reconciliation_from_record(record) or changed
        changed = self._repair_entry_reconciliation_from_account_history(ticket_i, record) or changed

        missing_exit_fields = execution.get("exit_reconciliation_missing_fields")
        if not isinstance(missing_exit_fields, list):
            missing_exit_fields = []
        else:
            missing_exit_fields = list(missing_exit_fields)
        if (
            execution.get("exit_reconciliation_status") == "RECONCILED_FROM_ACCOUNT_HISTORY"
            and self._missingish_ticket(execution.get("broker_exit_order_ticket"))
            and "broker_exit_order_ticket" not in missing_exit_fields
        ):
            missing_exit_fields.append("broker_exit_order_ticket")
            execution["exit_reconciliation_missing_fields"] = missing_exit_fields
            record["exit_reconciliation_missing_fields"] = missing_exit_fields
            changed = True
        if (
            record.get("exit_reconciliation_status") == "RECONCILED_FROM_ACCOUNT_HISTORY"
            and self._missingish_ticket(record.get("broker_exit_order_ticket"))
            and "broker_exit_order_ticket" not in missing_exit_fields
        ):
            missing_exit_fields.append("broker_exit_order_ticket")
            execution["exit_reconciliation_missing_fields"] = missing_exit_fields
            record["exit_reconciliation_missing_fields"] = missing_exit_fields
            changed = True

        changed = self._repair_exit_reconciliation_from_account_history(ticket_i, record) or changed

        inst = record.get("instrumentation") if isinstance(record.get("instrumentation"), dict) else {}
        has_ticket_hash = bool(execution.get("ticket_hash_sha256"))
        has_candidate = bool(record.get("candidate_id") or inst.get("candidate_id"))
        has_decision = bool(record.get("decision_bar_iso") or inst.get("decision_time_utc"))
        if has_ticket_hash and has_candidate and has_decision:
            status = "ticket_candidate_decision_policy_joinable"
        elif has_ticket_hash and has_decision:
            status = "ticket_decision_policy_joinable"
        elif has_ticket_hash:
            status = "ticket_policy_joinable"
        else:
            status = "partial_join_context"
        if record.get("runtime_learning_joinability_status") != status:
            record["runtime_learning_joinability_status"] = status
            changed = True
        return record, changed

    def _prune_old_trade_records(self, max_age_days: int = 60) -> None:
        """state-unbounded-growth: trade_records accumulate one file per placed trade. A book position
        closes within its time-stop budget (<=~53h), so a record file older than max_age_days is DEFINITELY
        a long-closed trade and is dead weight -> sweep it. Swept once at startup. NEVER raises."""
        try:
            import time
            d = self._trade_record_path()
            if not d.exists():
                return
            cutoff = time.time() - int(max_age_days) * 86400
            for f in d.glob("*.json"):
                try:
                    if f.stat().st_mtime < cutoff:
                        f.unlink()
                except OSError:
                    pass
        except Exception:
            pass

    def _persist_trade_record(
        self,
        ticket,
        trade_params: dict,
        intent,
        *,
        decision_bar_iso: str | None = None,
        decision_day: str | None = None,
        cluster: str | None = None,
        placed_at_utc: str | None = None,
        broker_symbol: str | None = None,
    ) -> None:
        """Persist the exit-policy truth for `ticket` so a restarted process can rehydrate the exact
        momentum/partial/etc. lifecycle after re-adopting the position. Best-effort; never raises."""
        if ticket in (None, 0):
            return
        try:
            record = {
                "instrumentation": dict(trade_params),
                "execution": {
                    "ticket": ticket,
                    "ticket_hash_sha256": self._runtime_learning_ticket_hash(ticket),
                    "broker_symbol": broker_symbol,
                    "placed_at_utc": placed_at_utc,
                },
                "sleeve": getattr(intent, "sleeve", None),
                "symbol": getattr(intent, "symbol", None),
                "decision_bar_iso": decision_bar_iso,
                "decision_day": decision_day,
                "cluster": cluster,
                "trade_lifecycle_status": "open",
                "opened_at_utc": placed_at_utc,
                "runtime_learning_joinability_status": "ticket_candidate_decision_policy_joinable",
            }
            record, _ = self._normalize_trade_record(ticket, record)
            self._write_trade_record(ticket, record)
        except Exception as e:
            # NOT idempotency-critical (the PlacementLedger already protects + logs loudly), but a silent
            # failure here means a post-restart adoption can't rehydrate the exact dynamic policy and falls
            # back to the native floor — make the disk/perms fault visible instead of swallowing it.
            _log.warning("book[%s]: trade-record persist FAILED for ticket %s (%r); exit-policy "
                         "rehydration will fall back to the native floor after a restart",
                         self._namespace, ticket, e)

    def _persist_reconstructed_trade_record(self, ticket, record: dict) -> None:
        """Persist a native-policy reconstruction so repeated restarts do not stay recordless forever."""
        if ticket in (None, 0):
            return
        try:
            from pathlib import Path

            d = self._trade_record_path()
            d.mkdir(parents=True, exist_ok=True)
            p = Path(d) / f"{ticket}.json"
            if p.exists():
                return
            record, _ = self._normalize_trade_record(ticket, record)
            self._write_trade_record(ticket, record, context="reconstructed trade-record persist")
        except Exception as e:
            _log.warning("book[%s]: reconstructed trade-record persist FAILED for ticket %s (%r)",
                         self._namespace, ticket, e)

    def _load_trade_record(self, ticket):
        try:
            import json
            from pathlib import Path
            p = Path(self._trade_record_path()) / f"{ticket}.json"
            if p.exists():
                record = json.loads(p.read_text(encoding="utf-8"))
                record, changed = self._normalize_trade_record(ticket, record)
                if changed:
                    self._write_trade_record(ticket, record, context="trade-record normalize persist")
                return record
        except Exception:
            pass
        return None

    @staticmethod
    def _deal_value(deal: Any, field: str, default: Any = None) -> Any:
        if isinstance(deal, dict):
            return deal.get(field, default)
        return getattr(deal, field, default)

    @staticmethod
    def _iso_from_deal_time(value: Any) -> str | None:
        if value in (None, ""):
            return None
        if isinstance(value, datetime):
            dt = value
        else:
            try:
                dt = datetime.fromtimestamp(float(value), tz=timezone.utc)
            except (TypeError, ValueError, OSError):
                return str(value)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt.astimezone(timezone.utc).isoformat()

    @staticmethod
    def _parse_utc(value: Any) -> datetime | None:
        if not value:
            return None
        if isinstance(value, datetime):
            dt = value
        else:
            try:
                dt = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
            except ValueError:
                return None
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt.astimezone(timezone.utc)

    def _exit_history_window(self, record: dict, closed_at_utc: str) -> tuple[datetime, datetime]:
        execution = record.get("execution") if isinstance(record.get("execution"), dict) else {}
        starts = [
            self._parse_utc(execution.get("placed_at_utc")),
            self._parse_utc(execution.get("broker_fill_time_utc")),
            self._parse_utc(record.get("closed_at_utc")),
            self._parse_utc(closed_at_utc),
        ]
        start = min([dt for dt in starts if dt is not None], default=datetime.now(timezone.utc))
        end = max(self._parse_utc(closed_at_utc) or datetime.now(timezone.utc), datetime.now(timezone.utc))
        return start - timedelta(minutes=10), end + timedelta(minutes=15)

    def _lookup_exit_deal_accounting(
        self,
        *,
        ticket: int,
        record: dict,
        broker_symbol: str | None,
        symbol: str | None,
        closed_at_utc: str,
    ) -> dict:
        """Read-only MT5 history lookup for the broker close deal tied to a book ticket."""
        start_utc, end_utc = self._exit_history_window(record, closed_at_utc)
        base = {
            "exit_reconciliation_status": "HISTORY_UNAVAILABLE",
            "exit_reconciliation_attempted": True,
            "exit_reconciliation_lookup_window_start_utc": start_utc.isoformat(),
            "exit_reconciliation_lookup_window_end_utc": end_utc.isoformat(),
            "exit_reconciliation_missing_fields": ["broker_exit_deal_ticket"],
        }
        reference_dt = self._parse_utc(closed_at_utc) or datetime.now(timezone.utc)

        def _is_exit_for_ticket(deal: Any) -> bool:
            try:
                position_id = int(self._deal_value(deal, "position_id", 0) or 0)
                entry = int(self._deal_value(deal, "entry", -1))
            except (TypeError, ValueError):
                return False
            return position_id == int(ticket) and entry in {1, 2, 3}

        def _is_position_deal_for_ticket(deal: Any) -> bool:
            try:
                position_id = int(self._deal_value(deal, "position_id", 0) or 0)
            except (TypeError, ValueError):
                return False
            return position_id == int(ticket)

        def _exit_candidates(deals: Any) -> list[Any]:
            try:
                iterable = list(deals or [])
            except TypeError:
                return []
            return [deal for deal in iterable if _is_exit_for_ticket(deal)]

        def _position_candidates(deals: Any) -> list[Any]:
            try:
                iterable = list(deals or [])
            except TypeError:
                return []
            return [deal for deal in iterable if _is_position_deal_for_ticket(deal)]

        def _position_entry_exit_counts(deals: list[Any]) -> tuple[int, int]:
            entry_count = 0
            exit_count = 0
            for deal in deals:
                try:
                    entry = int(self._deal_value(deal, "entry", -1))
                except (TypeError, ValueError):
                    continue
                if entry == 0:
                    entry_count += 1
                elif entry in {1, 2, 3}:
                    exit_count += 1
            return entry_count, exit_count

        def _deal_time_distance_seconds(deal: Any) -> float:
            dt = self._parse_utc(self._iso_from_deal_time(self._deal_value(deal, "time")))
            if dt is None:
                return float("inf")
            return abs((dt - reference_dt).total_seconds())

        def _select_exit_deal(candidates: list[Any]) -> tuple[Any | None, float | None]:
            if not candidates:
                return None, None
            selected = min(
                candidates,
                key=lambda deal: (
                    _deal_time_distance_seconds(deal),
                    str(self._iso_from_deal_time(self._deal_value(deal, "time")) or ""),
                    str(self._deal_value(deal, "ticket", "")),
                ),
            )
            return selected, _deal_time_distance_seconds(selected)

        def _sum_float(deals: list[Any], field: str) -> float | None:
            total = 0.0
            seen = False
            for deal in deals:
                try:
                    value = float(self._deal_value(deal, field, 0.0) or 0.0)
                except (TypeError, ValueError):
                    continue
                total += value
                seen = True
            return total if seen else None

        def _reconciled(
            deal: Any,
            *,
            source_status: str,
            candidate_deals: list[Any],
            position_deals: list[Any],
            nearest_distance_seconds: float | None,
        ) -> dict:
            profit = self._deal_value(deal, "profit", 0.0) or 0.0
            commission = self._deal_value(deal, "commission", 0.0) or 0.0
            swap = self._deal_value(deal, "swap", 0.0) or 0.0
            fee = self._deal_value(deal, "fee", 0.0) or 0.0
            deal_ticket = self._deal_value(deal, "ticket")
            order_ticket = self._deal_value(deal, "order")
            position_id = self._deal_value(deal, "position_id")
            missing_fields = []
            if self._missingish_ticket(deal_ticket):
                missing_fields.append("broker_exit_deal_ticket")
            if self._missingish_ticket(order_ticket):
                missing_fields.append("broker_exit_order_ticket")
            if self._missingish_ticket(position_id):
                missing_fields.append("broker_exit_position_id")
            try:
                realized = float(profit) + float(commission) + float(swap) + float(fee)
            except (TypeError, ValueError):
                realized = None
            aggregate_profit = _sum_float(candidate_deals, "profit")
            aggregate_commission = _sum_float(candidate_deals, "commission")
            aggregate_swap = _sum_float(candidate_deals, "swap")
            aggregate_fee = _sum_float(candidate_deals, "fee")
            aggregate_realized = None
            if any(value is not None for value in (
                aggregate_profit,
                aggregate_commission,
                aggregate_swap,
                aggregate_fee,
            )):
                aggregate_realized = sum(
                    value or 0.0
                    for value in (
                        aggregate_profit,
                        aggregate_commission,
                        aggregate_swap,
                        aggregate_fee,
                    )
                )
            position_profit = _sum_float(position_deals, "profit")
            position_commission = _sum_float(position_deals, "commission")
            position_swap = _sum_float(position_deals, "swap")
            position_fee = _sum_float(position_deals, "fee")
            position_entry_count, position_exit_count = _position_entry_exit_counts(position_deals)
            position_accounting_complete = position_entry_count > 0 and position_exit_count > 0
            position_coverage_status = (
                "entry_and_exit_deals_present"
                if position_accounting_complete
                else "partial_position_deals_missing_entry_or_exit"
                if position_deals
                else "no_position_deals"
            )
            position_realized = None
            if any(value is not None for value in (
                position_profit,
                position_commission,
                position_swap,
                position_fee,
            )):
                position_realized = sum(
                    value or 0.0
                    for value in (
                        position_profit,
                        position_commission,
                        position_swap,
                        position_fee,
                    )
                )
            broker_realized = (
                position_realized
                if position_realized is not None and position_accounting_complete
                else aggregate_realized if aggregate_realized is not None
                else realized
            )
            realized_source = (
                "position_aggregate_includes_entry_and_exit_deals"
                if position_realized is not None and position_accounting_complete
                else "exit_aggregate_only"
                if aggregate_realized is not None
                else "selected_exit_deal_only"
            )
            return {
                **base,
                "exit_reconciliation_status": "RECONCILED_FROM_ACCOUNT_HISTORY",
                "exit_reconciliation_source_status": source_status,
                "exit_reconciliation_missing_fields": missing_fields,
                "exit_reconciliation_match_keys": {
                    "matched_by": "position_id_and_exit_entry_nearest_close_time",
                    "position_id": position_id,
                    "order": order_ticket,
                    "ticket": deal_ticket,
                    "entry": self._deal_value(deal, "entry"),
                    "nearest_exit_time_distance_seconds": nearest_distance_seconds,
                },
                "broker_exit_deal_ticket": deal_ticket,
                "broker_exit_order_ticket": order_ticket,
                "broker_exit_position_id": position_id,
                "broker_exit_price": self._deal_value(deal, "price"),
                "broker_exit_time_utc": self._iso_from_deal_time(self._deal_value(deal, "time")),
                "broker_exit_profit": profit,
                "broker_exit_commission": commission,
                "broker_exit_swap": swap,
                "broker_exit_fee": fee,
                "broker_selected_exit_realized_pnl": realized,
                "broker_exit_position_deal_count": len(candidate_deals),
                "broker_exit_position_deal_tickets": [
                    self._deal_value(candidate, "ticket")
                    for candidate in candidate_deals
                    if not self._missingish_ticket(self._deal_value(candidate, "ticket"))
                ],
                "broker_exit_aggregate_profit": aggregate_profit,
                "broker_exit_aggregate_commission": aggregate_commission,
                "broker_exit_aggregate_swap": aggregate_swap,
                "broker_exit_aggregate_fee": aggregate_fee,
                "broker_position_deal_count": len(position_deals),
                "broker_position_deal_tickets": [
                    self._deal_value(candidate, "ticket")
                    for candidate in position_deals
                    if not self._missingish_ticket(self._deal_value(candidate, "ticket"))
                ],
                "broker_position_entry_deal_count": position_entry_count,
                "broker_position_exit_deal_count": position_exit_count,
                "broker_position_accounting_coverage_status": position_coverage_status,
                "broker_position_aggregate_profit": position_profit,
                "broker_position_aggregate_commission": position_commission,
                "broker_position_aggregate_swap": position_swap,
                "broker_position_aggregate_fee": position_fee,
                "broker_position_realized_pnl": position_realized,
                "broker_realized_pnl": broker_realized,
                "broker_realized_pnl_source": realized_source,
            }

        get_all_deals = getattr(self._mt5, "get_account_history_deals", None)
        if callable(get_all_deals):
            result = base
            for attempt in range(1, self._broker_exit_history_lookup_attempts + 1):
                try:
                    deals = get_all_deals(start_utc, end_utc)
                except Exception as exc:
                    return {
                        **base,
                        "exit_reconciliation_status": "LOOKUP_EXCEPTION",
                        "exit_reconciliation_error": repr(exc),
                        "exit_reconciliation_attempt_count": attempt,
                    }
                if deals is not None:
                    candidates = _exit_candidates(deals)
                    position_deals = _position_candidates(deals)
                    selected, nearest_distance_seconds = _select_exit_deal(candidates)
                    if selected is not None:
                        return {
                            **_reconciled(
                                selected,
                                source_status="broker_real_account_history_exit_reconciled",
                                candidate_deals=candidates,
                                position_deals=position_deals,
                                nearest_distance_seconds=nearest_distance_seconds,
                            ),
                            "exit_reconciliation_attempt_count": attempt,
                        }
                    result = {
                        **base,
                        "exit_reconciliation_status": "NO_EXIT_DEAL_FOUND",
                        "exit_reconciliation_source_status": "broker_real_account_history_checked",
                        "exit_reconciliation_attempt_count": attempt,
                    }
                if attempt < self._broker_exit_history_lookup_attempts and self._broker_exit_history_lookup_sleep_seconds > 0:
                    try:
                        import time
                        time.sleep(self._broker_exit_history_lookup_sleep_seconds)
                    except Exception:
                        pass
            return result

        get_symbol_deals = getattr(self._mt5, "get_history_deals", None)
        query_symbol = broker_symbol or symbol
        if callable(get_symbol_deals) and query_symbol:
            result = base
            for attempt in range(1, self._broker_exit_history_lookup_attempts + 1):
                try:
                    deals = get_symbol_deals(start_utc, end_utc, query_symbol)
                except Exception as exc:
                    return {
                        **base,
                        "exit_reconciliation_status": "LOOKUP_EXCEPTION",
                        "exit_reconciliation_error": repr(exc),
                        "exit_reconciliation_attempt_count": attempt,
                    }
                if deals is not None:
                    candidates = _exit_candidates(deals)
                    position_deals = _position_candidates(deals)
                    selected, nearest_distance_seconds = _select_exit_deal(candidates)
                    if selected is not None:
                        return {
                            **_reconciled(
                                selected,
                                source_status="broker_real_symbol_history_exit_reconciled",
                                candidate_deals=candidates,
                                position_deals=position_deals,
                                nearest_distance_seconds=nearest_distance_seconds,
                            ),
                            "exit_reconciliation_attempt_count": attempt,
                        }
                    result = {
                        **base,
                        "exit_reconciliation_status": "NO_EXIT_DEAL_FOUND",
                        "exit_reconciliation_source_status": "broker_real_symbol_history_checked",
                        "exit_reconciliation_attempt_count": attempt,
                    }
                if attempt < self._broker_exit_history_lookup_attempts and self._broker_exit_history_lookup_sleep_seconds > 0:
                    try:
                        import time
                        time.sleep(self._broker_exit_history_lookup_sleep_seconds)
                    except Exception:
                        pass
            return result

        return base

    def _apply_exit_reconciliation_result(
        self,
        record: dict,
        reconciliation: dict,
        *,
        ticket: int,
        broker_symbol: str | None,
        sleeve: str | None,
        symbol: str | None,
        action: str,
        closed_at_utc: str,
        already_has_selected_exit: bool,
    ) -> None:
        execution = record.setdefault("execution", {})
        mirrored_fields = {
            "broker_exit_deal_ticket",
            "broker_exit_order_ticket",
            "broker_exit_position_id",
            "broker_exit_price",
            "broker_exit_time_utc",
            "broker_exit_profit",
            "broker_exit_commission",
            "broker_exit_swap",
            "broker_exit_fee",
            "broker_selected_exit_realized_pnl",
            "broker_exit_position_deal_count",
            "broker_exit_position_deal_tickets",
            "broker_exit_aggregate_profit",
            "broker_exit_aggregate_commission",
            "broker_exit_aggregate_swap",
            "broker_exit_aggregate_fee",
            "broker_position_deal_count",
            "broker_position_deal_tickets",
            "broker_position_entry_deal_count",
            "broker_position_exit_deal_count",
            "broker_position_accounting_coverage_status",
            "broker_position_aggregate_profit",
            "broker_position_aggregate_commission",
            "broker_position_aggregate_swap",
            "broker_position_aggregate_fee",
            "broker_position_realized_pnl",
            "broker_realized_pnl_source",
            "broker_realized_pnl",
        }
        aggregate_fields = {
            "broker_exit_position_deal_count",
            "broker_exit_position_deal_tickets",
            "broker_exit_aggregate_profit",
            "broker_exit_aggregate_commission",
            "broker_exit_aggregate_swap",
            "broker_exit_aggregate_fee",
            "broker_position_deal_count",
            "broker_position_deal_tickets",
            "broker_position_entry_deal_count",
            "broker_position_exit_deal_count",
            "broker_position_accounting_coverage_status",
            "broker_position_aggregate_profit",
            "broker_position_aggregate_commission",
            "broker_position_aggregate_swap",
            "broker_position_aggregate_fee",
            "broker_position_realized_pnl",
            "broker_realized_pnl_source",
            "broker_realized_pnl",
        }
        if (
            already_has_selected_exit
            and reconciliation.get("exit_reconciliation_status") != "RECONCILED_FROM_ACCOUNT_HISTORY"
        ):
            return
        for key, value in reconciliation.items():
            if value is not None:
                should_update = (
                    not already_has_selected_exit
                    or key in aggregate_fields
                    or execution.get(key) in (None, "")
                )
                if should_update:
                    execution[key] = value
                if key in mirrored_fields and (
                    key in aggregate_fields
                    or record.get(key) in (None, "")
                    or not already_has_selected_exit
                ):
                    record[key] = value
        record["exit_reconciliation_status"] = reconciliation.get("exit_reconciliation_status")
        record["exit_reconciliation_attempted"] = reconciliation.get("exit_reconciliation_attempted")
        record["gtos_vnext_broker_exit_lifecycle_capture_v4_packet"] = {
            "schema_version": "broker_exit_lifecycle_capture_v4_packet_v1",
            "component": "broker_exit_lifecycle_capture_v4",
            "generated_at_utc": datetime.now(timezone.utc).isoformat(),
            "stage": "exit_reconciliation",
            "status": reconciliation.get("exit_reconciliation_status"),
            "evidence_class": "production_code_integration_broker_exit_lifecycle_capture_v4",
            "runtime_effect_boundary": "read_only_account_history_no_broker_mutation",
            "identity": {
                "ticket": ticket,
                "symbol": symbol,
                "broker_symbol": broker_symbol,
                "sleeve": sleeve,
                "close_action": action,
                "closed_at_utc": closed_at_utc,
            },
            "reconciliation": reconciliation,
        }

    def _merge_exit_reconciliation(
        self,
        record: dict,
        *,
        ticket: int,
        broker_symbol: str | None,
        sleeve: str | None,
        symbol: str | None,
        action: str,
        closed_at_utc: str,
    ) -> None:
        execution = record.setdefault("execution", {})
        aggregate_fields = {
            "broker_exit_position_deal_count",
            "broker_exit_position_deal_tickets",
            "broker_exit_aggregate_profit",
            "broker_exit_aggregate_commission",
            "broker_exit_aggregate_swap",
            "broker_exit_aggregate_fee",
            "broker_position_deal_count",
            "broker_position_deal_tickets",
            "broker_position_entry_deal_count",
            "broker_position_exit_deal_count",
            "broker_position_accounting_coverage_status",
            "broker_position_aggregate_profit",
            "broker_position_aggregate_commission",
            "broker_position_aggregate_swap",
            "broker_position_aggregate_fee",
            "broker_position_realized_pnl",
            "broker_realized_pnl_source",
            "broker_realized_pnl",
        }
        already_has_selected_exit = execution.get("broker_exit_deal_ticket") not in (None, "")
        if already_has_selected_exit and all(execution.get(field) not in (None, "") for field in aggregate_fields):
            return
        reconciliation = self._lookup_exit_deal_accounting(
            ticket=int(ticket),
            record=record,
            broker_symbol=broker_symbol,
            symbol=symbol,
            closed_at_utc=closed_at_utc,
        )
        self._apply_exit_reconciliation_result(
            record,
            reconciliation,
            ticket=ticket,
            broker_symbol=broker_symbol,
            sleeve=sleeve,
            symbol=symbol,
            action=action,
            closed_at_utc=closed_at_utc,
            already_has_selected_exit=already_has_selected_exit,
        )

    def _repair_exit_reconciliation_from_account_history(self, ticket: int, record: dict) -> bool:
        """Retry read-only exit reconciliation for closed records whose first lookup missed MT5 history."""
        if not isinstance(record, dict):
            return False
        try:
            ticket_i = int(ticket)
        except (TypeError, ValueError):
            return False
        if record.get("trade_lifecycle_status") != "closed":
            return False

        execution = record.setdefault("execution", {})
        status = execution.get("exit_reconciliation_status") or record.get("exit_reconciliation_status")
        already_has_selected_exit = execution.get("broker_exit_deal_ticket") not in (None, "")
        aggregate_fields = {
            "broker_exit_position_deal_count",
            "broker_exit_position_deal_tickets",
            "broker_exit_aggregate_profit",
            "broker_exit_aggregate_commission",
            "broker_exit_aggregate_swap",
            "broker_exit_aggregate_fee",
            "broker_position_deal_count",
            "broker_position_deal_tickets",
            "broker_position_entry_deal_count",
            "broker_position_exit_deal_count",
            "broker_position_accounting_coverage_status",
            "broker_position_aggregate_profit",
            "broker_position_aggregate_commission",
            "broker_position_aggregate_swap",
            "broker_position_aggregate_fee",
            "broker_position_realized_pnl",
            "broker_realized_pnl_source",
            "broker_realized_pnl",
        }
        if (
            status == "RECONCILED_FROM_ACCOUNT_HISTORY"
            and already_has_selected_exit
            and all(execution.get(field) not in (None, "") for field in aggregate_fields)
        ):
            return False
        if status == "RECONCILED_FROM_ACCOUNT_HISTORY" and not already_has_selected_exit:
            return False
        if status not in {
            None,
            "",
            "NO_EXIT_DEAL_FOUND",
            "HISTORY_UNAVAILABLE",
            "LOOKUP_EXCEPTION",
            "ACCOUNT_HISTORY_LOOKUP_FAILED",
        } and not already_has_selected_exit:
            return False

        closed_at_utc = record.get("closed_at_utc") or execution.get("closed_at_utc")
        if not closed_at_utc:
            return False
        now = datetime.now(timezone.utc)
        last_attempt = self._exit_reconciliation_repair_last_attempt_utc.get(ticket_i)
        if last_attempt and (now - last_attempt).total_seconds() < 900:
            return False
        self._exit_reconciliation_repair_last_attempt_utc[ticket_i] = now

        broker_symbol = execution.get("broker_symbol")
        symbol = record.get("symbol")
        if not broker_symbol and symbol not in (None, ""):
            try:
                broker_symbol = self._broker_symbol(symbol)
            except Exception:
                broker_symbol = symbol
        reconciliation = self._lookup_exit_deal_accounting(
            ticket=ticket_i,
            record=record,
            broker_symbol=broker_symbol,
            symbol=symbol,
            closed_at_utc=str(closed_at_utc),
        )
        if reconciliation.get("exit_reconciliation_status") != "RECONCILED_FROM_ACCOUNT_HISTORY":
            return False
        self._apply_exit_reconciliation_result(
            record,
            reconciliation,
            ticket=ticket_i,
            broker_symbol=broker_symbol,
            sleeve=record.get("sleeve"),
            symbol=symbol,
            action=record.get("close_action") or "broker_closed",
            closed_at_utc=str(closed_at_utc),
            already_has_selected_exit=already_has_selected_exit,
        )
        execution["exit_reconciliation_repair_status"] = reconciliation.get("exit_reconciliation_status")
        execution["exit_reconciliation_repair_checked_at_utc"] = now.isoformat()
        return True

    def _mark_trade_record_management_checked(
        self,
        ticket,
        checked_at_utc: str,
        *,
        record: dict | None = None,
        broker_symbol: str | None = None,
        sleeve: str | None = None,
        symbol: str | None = None,
        broker_protection: dict[str, Any] | None = None,
    ) -> dict | None:
        """Persist open-position management visibility without touching broker state."""
        if ticket in (None, 0):
            return record if isinstance(record, dict) else None
        try:
            rec = record if isinstance(record, dict) else self._load_trade_record(ticket)
            if not isinstance(rec, dict):
                return None
            rec, _ = self._normalize_trade_record(ticket, rec)
            if rec.get("trade_lifecycle_status") == "closed":
                return rec
            execution = rec.setdefault("execution", {})
            if broker_symbol:
                execution["broker_symbol"] = broker_symbol
            for key, value in (broker_protection or {}).items():
                if value is not None:
                    execution[key] = value
            if broker_protection:
                execution.update(self._broker_protection_reconciliation(rec, execution))
            self._set_record_value(rec, "sleeve", sleeve)
            self._set_record_value(rec, "symbol", symbol)
            rec["trade_lifecycle_status"] = "open"
            rec["last_management_checked_at_utc"] = checked_at_utc
            execution["last_management_checked_at_utc"] = checked_at_utc
            self._write_trade_record(ticket, rec, context="trade-record management-state persist")
            return rec
        except Exception as e:
            _log.debug(
                "book[%s]: trade-record management-state persist skipped for ticket %s (%r)",
                self._namespace,
                ticket,
                e,
            )
            return record if isinstance(record, dict) else None

    def _mark_trade_record_closed(
        self,
        ticket,
        action: str,
        closed_at_utc: str,
        *,
        record: dict | None = None,
        broker_symbol: str | None = None,
        sleeve: str | None = None,
        symbol: str | None = None,
    ) -> dict | None:
        """Persist an observed close lifecycle marker without touching broker state."""
        if ticket in (None, 0):
            return None
        try:
            rec = record if isinstance(record, dict) else self._load_trade_record(ticket)
            if not isinstance(rec, dict):
                rec = {"execution": {"ticket": ticket}}
            self._set_record_value(rec, "sleeve", sleeve)
            self._set_record_value(rec, "symbol", symbol)
            rec, _ = self._normalize_trade_record(ticket, rec)
            execution = rec.setdefault("execution", {})
            if broker_symbol:
                execution["broker_symbol"] = broker_symbol
            rec["trade_lifecycle_status"] = "closed"
            rec["close_action"] = action
            rec["closed_at_utc"] = closed_at_utc
            execution["closed_at_utc"] = closed_at_utc
            try:
                self._merge_exit_reconciliation(
                    rec,
                    ticket=int(ticket),
                    broker_symbol=broker_symbol or execution.get("broker_symbol"),
                    sleeve=sleeve or rec.get("sleeve"),
                    symbol=symbol or rec.get("symbol"),
                    action=action,
                    closed_at_utc=closed_at_utc,
                )
            except Exception as exc:
                execution["exit_reconciliation_status"] = "LOOKUP_EXCEPTION"
                execution["exit_reconciliation_error"] = repr(exc)
                rec["exit_reconciliation_status"] = "LOOKUP_EXCEPTION"
            self._record_closed_trade_daily_pnl(ticket, rec, action)
            self._write_trade_record(ticket, rec, context="trade-record close-state persist")
            return rec
        except Exception as e:
            _log.warning("book[%s]: trade-record close-state persist FAILED for ticket %s (%r)",
                         self._namespace, ticket, e)
            return record if isinstance(record, dict) else None

    # ---------------- notifications: clean owner-facing trade cards (best-effort; NEVER affect placement) ----
    # Readable strategy names (internal sleeve tags are for the logs, not the owner's phone).
    _SLEEVE_LABEL = {
        "metals_core": "Gold/Silver core", "metals_softband": "Gold/Silver softband",
        "metals_ob_micro": "Gold/Silver order-block", "crypto": "Crypto momentum", "energy_agri": "Oil",
        "idxrev": "Index reversion", "sub_xvol_pullback": "Substrate vol-pullback",
        "sub_mid_dn_revert": "Substrate mid-revert", "vp_euidx_pocgrav": "Index volume-profile",
        "fx_jpy": "JPY London", "fx_jpy_ny": "JPY NY",
    }

    def _send_card(self, text: str) -> None:
        """Send a clean message to Telegram (durable queue, NO 'SYSTEM ALERT' framing). Best-effort."""
        try:
            from src.utils.notification_queue import Level, send as _q
            _q(text, level=Level.HIGH)
        except Exception:
            try:
                from src.notifications import _send_async
                _send_async(text)
            except Exception:
                pass

    def _equity(self) -> float:
        try:
            return float(self._mt5.get_account_equity())
        except Exception:
            return 0.0

    def _account_label(self) -> str:
        ns = str(self._namespace or "")
        if ns.startswith("ftmo"):
            return "FTMO"
        if ns.startswith("redacted_account"):
            return "redacted_account"
        return ns or "book"

    @staticmethod
    def _g(x) -> str:
        return f"{x:,.5g}" if x else "?"

    def _notify_placed(self, intent, sized_unit, result) -> None:
        """A tight trade card: direction, symbol, strategy, levels, real risk %/$, expected reward R/$."""
        try:
            ts = result.get("trade_state")
            tpp = result.get("trade_params") or {}
            is_long = int(intent.direction) > 0
            sign = 1.0 if is_long else -1.0
            entry = float(getattr(ts, "entry_price", 0.0) or 0.0)
            sl = float(getattr(ts, "stop_loss", 0.0) or 0.0)
            stop = abs(entry - sl) or 1.0
            final_r = tpp.get("gtos_vnext_dynamic_final_target_r")
            if final_r is None:
                tp0 = float(getattr(ts, "take_profit_1", 0.0) or 0.0)
                final_r = abs(tp0 - entry) / stop if tp0 else 0.0
            final_r = float(final_r)
            broker_tp_mode = str(tpp.get("gtos_vnext_dynamic_broker_take_profit_mode") or "").strip().lower()
            no_broker_take_profit = (
                tpp.get("gtos_vnext_dynamic_no_broker_take_profit") is True
                or broker_tp_mode == "none"
                or not float(getattr(ts, "take_profit_1", 0.0) or 0.0)
            )
            tp_final = entry + sign * final_r * stop
            risk_pct = float(getattr(sized_unit, "risk_pct_per_trade", 0.0) or 0.0) * 100.0
            risk_usd = risk_pct / 100.0 * self._equity()
            reward_usd = risk_usd * final_r
            label = self._SLEEVE_LABEL.get(intent.sleeve, intent.sleeve)
            arrow = "🟢 LONG" if is_long else "🔴 SHORT"

            def _float_param(*names: str) -> Optional[float]:
                for name in names:
                    value = tpp.get(name)
                    if value is None:
                        continue
                    try:
                        return float(value)
                    except (TypeError, ValueError):
                        continue
                return None

            def _r_text(value: Optional[float]) -> Optional[str]:
                if value is None:
                    return None
                return f"{value:g}R"

            if no_broker_take_profit:
                level_line = f"entry {self._g(entry)} | SL {self._g(sl)} | broker TP none"
                policy = str(tpp.get("gtos_vnext_dynamic_policy_selected") or "native").replace("_", " ")
                native_parts = [f"native exit: {policy}; broker TP disabled"]
                trigger = _r_text(
                    _float_param(
                        "gtos_vnext_dynamic_trailing_trigger_r",
                        "gtos_vnext_dynamic_trail_trigger_r",
                        "gtos_vnext_dynamic_be_trigger_r",
                        "trigger_r",
                    )
                )
                gap = _r_text(
                    _float_param(
                        "gtos_vnext_dynamic_trailing_gap_r",
                        "gtos_vnext_dynamic_trail_gap_r",
                        "trail_gap_r",
                    )
                )
                time_stop = _float_param("gtos_vnext_dynamic_time_stop_bars", "time_stop_bars")
                if trigger is not None:
                    native_parts.append(f"trigger {trigger}")
                if gap is not None:
                    native_parts.append(f"trail gap {gap}")
                if time_stop is not None:
                    native_parts.append(f"time stop {time_stop:g} bars")
                reward_line = "; ".join(native_parts)
            else:
                level_line = f"entry {self._g(entry)} | SL {self._g(sl)} | TP {self._g(tp_final)}"
                reward_line = f"risk {risk_pct:.2f}% (~${risk_usd:,.0f}) -> reward {final_r:.2f}R (+${reward_usd:,.0f})"

            lines = [f"[{self._account_label()}] {arrow} {intent.symbol} · {label}",
                     level_line,
                     reward_line]
            if tpp.get("gtos_vnext_dynamic_policy_selected") == "partial_be_runner":
                trig = float(tpp.get("gtos_vnext_dynamic_be_trigger_r") or 0)
                lines.append(f"scale-out: take 50% @ {trig:.1f}R, runner to {final_r:.1f}R")
            self._send_card("\n".join(lines))
        except Exception:
            import logging
            logging.getLogger(__name__).warning("notify_placed failed (non-fatal)", exc_info=True)

    @staticmethod
    def _spread_observation_key(sleeve, symbol, decision_bar_iso) -> tuple:
        """Same key shape as _runtime_learning_skip_context, so the two join without a mapping."""
        return (
            str(sleeve) if sleeve else None,
            str(symbol) if symbol else None,
            str(decision_bar_iso) if decision_bar_iso else None,
        )

    def _record_spread_observation(self, intent, *, spread_r: float, spread_price: float,
                                   max_spread_r: float, stop_dist: float) -> None:
        """Store one measured spread observation. Best-effort; never raises into the screen."""
        try:
            key = self._spread_observation_key(
                getattr(intent, "sleeve", None),
                getattr(intent, "symbol", None),
                getattr(intent, "decision_bar_iso", None),
            )
            self._spread_observations[key] = {
                "spread_r": round(float(spread_r), 8),
                "spread_price": round(float(spread_price), 10),
                "spread_r_limit": round(float(max_spread_r), 8),
                "stop_dist": round(float(stop_dist), 10),
                "spread_observed_at_utc": datetime.now(timezone.utc).isoformat(),
                # Measured from a live tick at screen time -- not a config value, not a model.
                "spread_r_provenance": "measured",
                "spread_r_source": "book_owner._spread_cost_screen_live_tick",
            }
        except Exception:  # noqa: BLE001 - observability must never break the cost screen
            pass

    def _attach_spread_observation(self, row: dict) -> dict:
        """Attach the measured spread for this leg, if one was observed this cycle."""
        try:
            obs = self._spread_observations.get(
                self._spread_observation_key(
                    row.get("sleeve"), row.get("symbol"), row.get("decision_bar_iso")
                )
            )
            if obs:
                for key, value in obs.items():
                    row.setdefault(key, value)
        except Exception:  # noqa: BLE001
            pass
        return row

    def _spread_cost_screen(self, intent, tick) -> Optional[str]:
        """Deterministic pre-send mirror of the authoritative pretrade spread-cost gate
        (broker_net_cost_engine: spread_r = (ask-bid)/sl_distance vs selected_cell_pretrade_max_spread_r,
        default 0.10). Returns a precise refusal-reason string when this leg's live spread structurally
        exceeds the limit of its R-unit (intent.stop_dist) -- so the book declines it cleanly instead of
        attempting a futile order that open_trade's ExecMgr-V4 cost gate would block. Returns None when the
        leg passes OR the screen cannot be evaluated (fail OPEN -> defer to the authoritative gate)."""
        try:
            rd = float(getattr(intent, "stop_dist", 0.0) or 0.0)
            bid = float(getattr(tick, "bid", 0.0) or 0.0)
            ask = float(getattr(tick, "ask", 0.0) or 0.0)
            if rd <= 0 or bid <= 0 or ask <= 0 or ask < bid:
                return None                       # cannot evaluate -> let the authoritative gate decide
            rt = self.base_config.get("gtos_vnext_runtime", {}) or {}
            try:
                max_spread_r = float(rt.get("selected_cell_pretrade_max_spread_r", 0.10))
            except (TypeError, ValueError):
                max_spread_r = 0.10
            # per-sleeve override (matches the authoritative gate in broker_net_cost_engine): a tiny-stop
            # session sleeve (fx_jpy/fx_jpy_ny) on an owner-approved JPY-cross live trial runs a looser
            # ceiling, so the screen must NOT pre-block what the gate now allows.
            by_sleeve = rt.get("selected_cell_pretrade_max_spread_r_by_sleeve")
            sleeve = getattr(intent, "sleeve", None)
            if isinstance(by_sleeve, dict) and sleeve in by_sleeve:
                try:
                    max_spread_r = float(by_sleeve[sleeve])
                except (TypeError, ValueError):
                    pass
            spread_r = (ask - bid) / rd
            # Record the observation for EVERY evaluated leg, pass or fail. Recording only the
            # failures would build the spread record out of a refusal log, which is the
            # derive-don't-accumulate trap: the passing legs are most of the distribution and
            # their absence would read as "no spread" rather than "spread was fine".
            self._record_spread_observation(intent, spread_r=spread_r, spread_price=ask - bid,
                                            max_spread_r=max_spread_r, stop_dist=rd)
            if spread_r > max_spread_r:
                return (f"cost_screen_spread_r:{spread_r:.3f}>{max_spread_r:.3f} "
                        f"(spread {ask - bid:.4f} vs {getattr(intent,'sleeve','?')} stop {rd:.4f})")
            return None
        except Exception:
            return None                            # a screen error must never block the cycle

    def _notify_cost_skip(self, intent, reason) -> None:
        """EXPECTED cost decline (spread structurally too wide for the sleeve's stop) -> inform the owner
        once per decision bar as an ℹ️ note, NOT the ⚠️ 'Trade NOT placed' failure card."""
        try:
            label = self._SLEEVE_LABEL.get(getattr(intent, "sleeve", ""), getattr(intent, "sleeve", "?"))
            self._send_card(f"[{self._account_label()}] ℹ️ Skipped {getattr(intent,'symbol','?')} ({label}) — "
                            f"spread too wide for stop · {reason}")
        except Exception:
            pass

    def _notify_reject(self, intent, reason) -> None:
        try:
            label = self._SLEEVE_LABEL.get(getattr(intent, "sleeve", ""), getattr(intent, "sleeve", "?"))
            self._send_card(f"[{self._account_label()}] ⚠️ Trade NOT placed · {getattr(intent,'symbol','?')} ({label}) — {reason}")
        except Exception:
            pass

    @staticmethod
    def _closed_record_realized_pnl(record: dict | None) -> float | None:
        if not isinstance(record, dict):
            return None
        for source in (
            record,
            record.get("execution") if isinstance(record.get("execution"), dict) else None,
        ):
            if not isinstance(source, dict):
                continue
            for key in (
                "broker_realized_pnl",
                "broker_position_realized_pnl",
                "broker_selected_exit_realized_pnl",
            ):
                value = source.get(key)
                if value in (None, ""):
                    continue
                try:
                    return float(value)
                except (TypeError, ValueError):
                    continue
        return None

    @staticmethod
    def _closed_record_float(record: dict | None, *keys: str) -> float | None:
        if not isinstance(record, dict):
            return None
        sources = (
            record,
            record.get("execution") if isinstance(record.get("execution"), dict) else None,
            record.get("instrumentation") if isinstance(record.get("instrumentation"), dict) else None,
        )
        for source in sources:
            if not isinstance(source, dict):
                continue
            for key in keys:
                value = source.get(key)
                if value in (None, ""):
                    continue
                try:
                    return float(value)
                except (TypeError, ValueError):
                    continue
        return None

    @staticmethod
    def _closed_record_value(record: dict | None, *keys: str):
        if not isinstance(record, dict):
            return None
        sources = (
            record,
            record.get("execution") if isinstance(record.get("execution"), dict) else None,
            record.get("instrumentation") if isinstance(record.get("instrumentation"), dict) else None,
        )
        for source in sources:
            if not isinstance(source, dict):
                continue
            for key in keys:
                value = source.get(key)
                if value not in (None, ""):
                    return value
        return None

    @staticmethod
    def _minutes_between(start_value, end_value) -> float | None:
        if not start_value or not end_value:
            return None
        try:
            start = datetime.fromisoformat(str(start_value).replace("Z", "+00:00"))
            end = datetime.fromisoformat(str(end_value).replace("Z", "+00:00"))
            if start.tzinfo is None:
                start = start.replace(tzinfo=timezone.utc)
            if end.tzinfo is None:
                end = end.replace(tzinfo=timezone.utc)
            return (end.astimezone(timezone.utc) - start.astimezone(timezone.utc)).total_seconds() / 60.0
        except Exception:
            return None

    def _record_closed_trade_daily_pnl(self, ticket, record: dict | None, action: str) -> bool:
        if ticket in (None, 0) or not isinstance(record, dict):
            return False
        execution = record.setdefault("execution", {})
        if execution.get("daily_pnl_ledger_status") == "RECORDED_BROKER_NET":
            return False
        broker_net = self._closed_record_realized_pnl(record)
        if broker_net is None:
            execution["daily_pnl_ledger_status"] = "PENDING_BROKER_REALIZED_PNL"
            return False
        symbol = (
            record.get("symbol")
            or self._closed_record_value(record, "symbol")
            or self._closed_record_value(record, "broker_symbol")
            or "UNKNOWN"
        )
        trade_id = f"{self._namespace}:{symbol}:{ticket}"
        try:
            from src.notifications import record_trade_closed_pnl

            opened_at = (
                record.get("opened_at_utc")
                or self._closed_record_value(record, "placed_at_utc", "broker_fill_time_utc")
            )
            closed_at = record.get("closed_at_utc") or self._closed_record_value(record, "closed_at_utc")
            record_trade_closed_pnl(
                str(symbol),
                str(action or record.get("close_action") or "broker_closed"),
                actual_r=0.0,
                hold_minutes=self._minutes_between(opened_at, closed_at),
                trade_id=trade_id,
                entry_price=self._closed_record_float(record, "broker_entry_price", "entry_price") or 0.0,
                exit_price=self._closed_record_float(record, "broker_exit_price", "exit_price") or 0.0,
                vnext_context={
                    "runtime_namespace": self._namespace,
                    "ticket_hash_sha256": self._closed_record_value(record, "ticket_hash_sha256"),
                    "candidate_id": record.get("candidate_id"),
                    "broker_realized_pnl_source": self._closed_record_value(record, "broker_realized_pnl_source"),
                    "exit_reconciliation_status": record.get("exit_reconciliation_status"),
                    "close_action": action or record.get("close_action"),
                },
                broker_profit=self._closed_record_float(
                    record,
                    "broker_position_aggregate_profit",
                    "broker_exit_aggregate_profit",
                    "broker_exit_profit",
                ),
                broker_net_profit=broker_net,
                broker_deal_reconciled=record.get("exit_reconciliation_status") == "RECONCILED_FROM_ACCOUNT_HISTORY",
                broker_deal_id=self._closed_record_value(record, "broker_exit_deal_ticket"),
                broker_close_order_id=self._closed_record_value(record, "broker_exit_order_ticket"),
                broker_commission=self._closed_record_float(
                    record,
                    "broker_position_aggregate_commission",
                    "broker_exit_aggregate_commission",
                    "broker_exit_commission",
                ),
                broker_swap=self._closed_record_float(
                    record,
                    "broker_position_aggregate_swap",
                    "broker_exit_aggregate_swap",
                    "broker_exit_swap",
                ),
                broker_fee=self._closed_record_float(
                    record,
                    "broker_position_aggregate_fee",
                    "broker_exit_aggregate_fee",
                    "broker_exit_fee",
                ),
            )
            execution["daily_pnl_ledger_status"] = "RECORDED_BROKER_NET"
            execution["daily_pnl_ledger_trade_id"] = trade_id
            execution["daily_pnl_ledger_recorded_at_utc"] = datetime.now(timezone.utc).isoformat()
            execution["daily_pnl_ledger_broker_net_profit"] = broker_net
            return True
        except Exception as exc:  # noqa: BLE001
            execution["daily_pnl_ledger_status"] = "RECORD_FAILED"
            execution["daily_pnl_ledger_error"] = repr(exc)
            _log.warning(
                "book[%s]: daily PnL ledger record failed for ticket %s (%r)",
                self._namespace,
                ticket,
                exc,
            )
            return False

    def _notify_closed(self, symbol, action, *, closed_record: dict | None = None) -> None:
        try:
            # Prefer the exact ticket-bound reconciliation. The symbol-history fallback is only
            # best-effort and can race when two same-symbol positions close close together.
            pnl = self._closed_record_realized_pnl(closed_record)
            if pnl is None:
                pnl = self._recent_realized_pnl(symbol)
            pnl_str = f" · P&L ${pnl:,.0f}" if pnl is not None else ""
            verb = {"vnext_time_stop": "time-stop exit", "stop_loss": "stopped out",
                    "take_profit": "target hit"}.get(str(action), str(action))
            self._send_card(f"[{self._account_label()}] ⚪ Closed {symbol} — {verb}{pnl_str}")
        except Exception:
            pass

    def _recent_realized_pnl(self, symbol):
        try:
            broker = self._broker_symbol(symbol)
            import datetime as _dt
            import MetaTrader5 as _m
            now = _dt.datetime.now(_dt.timezone.utc)
            # MT5 interprets the history window in SERVER time (FTMO/FN = UTC+3), so a bare `now` upper
            # bound DROPS a just-now close (its server timestamp sorts after the bound) -> the close card
            # reported "P&L $0". Pad the upper bound +13h, mirroring monitor_books.py. AND take only the
            # CLOSE deal (entry==1 = DEAL_ENTRY_OUT): the OPEN deal carries profit 0 and, as the lone deal
            # in the unpadded window, was being returned as the realized P&L (the source of the bogus $0).
            deals = _m.history_deals_get(now - _dt.timedelta(hours=24), now + _dt.timedelta(hours=13),
                                         group=f"*{broker}*")
            if not deals:
                return None
            closes = [d for d in deals if getattr(d, "entry", 0) == 1]
            if not closes:
                return None
            last = max(closes, key=lambda d: d.time)
            position_id = getattr(last, "position_id", None)
            if position_id not in (None, "", 0, "0"):
                related = [d for d in deals if getattr(d, "position_id", None) == position_id]
                if related:
                    return sum(
                        float(getattr(d, "profit", 0) or 0)
                        + float(getattr(d, "swap", 0) or 0)
                        + float(getattr(d, "commission", 0) or 0)
                        + float(getattr(d, "fee", 0) or 0)
                        for d in related
                    )
            return (
                float(last.profit)
                + float(getattr(last, "swap", 0) or 0)
                + float(getattr(last, "commission", 0) or 0)
                + float(getattr(last, "fee", 0) or 0)
            )
        except Exception:
            return None


class _UnitView:
    """Adapt a realized-unit dict to the SizedUnit attribute interface the order_router expects."""
    def __init__(self, unit: dict):
        self.cluster = unit.get("cluster", "book")
        self.sleeve_members = unit.get("sleeve_members", [])
        self.n_trades = unit.get("n_trades", 1)
        self.confidence = unit.get("confidence")
        self.risk_pct_per_trade = unit.get("risk_pct_per_trade", 0.0)
        self.unit_risk_pct = unit.get("unit_risk_pct")
        self.sized = unit.get("sized", False)
        self.reason = unit.get("reason")
