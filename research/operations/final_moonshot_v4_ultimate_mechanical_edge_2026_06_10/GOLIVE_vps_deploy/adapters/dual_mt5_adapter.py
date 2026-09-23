"""GOLIVE_vps — DUAL-MT5 LIVE ADAPTER (scaffold, DEFAULT-OFF). NO BROKER. NO ORDERS ON IMPORT.

PURPOSE
=======
The VPS go-live transport. It SUPERSEDES the single-handle, bridge-based
``bridge_adapter.SiliconBridgeAdapter`` for live trading, implementing the
**FTMO-PRIMARY / redacted_account-FOLLOWER** architecture from ``DUAL_MT5_ARCHITECTURE.md``:

  * TWO local MT5 terminal handles (NO research bridge — the siliconmetatrader5 @
    :8001 bridge is DEV-ONLY for the research Mac). Each handle is a single-terminal
    ``bridge_adapter.BridgeAdapter`` (we REUSE the already-tested, gated transport
    seam — no duplicate connect/order code, one fail-closed gate path).
  * **FTMO = PRIMARY**: read OHLC/tick, feed the decision engine, EXECUTE here. FTMO
    is the system's native reference distribution (the whole deploy book was built and
    validated on FTMO data), so the live decision runs on the FTMO instance.
  * **redacted_account = FOLLOWER**: a spec-translated mirror of each FTMO decision. It does
    NOT re-decide. It replicates the primary's intent, translated to redacted_account's own
    symbol name / contract spec / spread floor, with its OWN independent governor + DD.

WHY THIS FILE (and not a production-src edit): per the go-live guardrails the live
adapter is built in the route dir + GOLIVE_vps_deploy/, default-off. At go-live the
owner promotes the reviewed adapter into ``src/mt5/`` alongside the production
``MT5Interface`` contract (this file mirrors that contract per-terminal) and supplies
two terminal paths + two sets of creds. Until then it is inert scaffolding.

HARD GUARANTEES (mirrors bridge_adapter + the charter safety envelope)
=====================================================================
- Importing this module performs ZERO network / broker / order / file-mutation work.
- No credentials in this file: each terminal's creds come from ENV (the VPS .env,
  gitignored). This file only names the ENV vars.
- ``connect()`` is fail-closed per terminal: each leg refuses unless the triple-gate
  is satisfied AND the local halt flags are clear AND the owner opted in.
- FOLLOWER ISOLATION (the core safety property): the follower (redacted_account) NEVER
  affects the primary. A follower missing-symbol / large-slip / reject / spec-mismatch
  / connect-failure SKIPS that follower leg and logs it — the primary executes
  regardless. One account breaching never forces the other (independent governors).
- CHRONOLOGICAL SAFETY (the top operator watch item): each terminal's server clock is
  normalized to UTC and an explicit per-terminal startup offset check is exposed; an
  out-of-tolerance offset FAILS CLOSED that terminal (a silent clock skew corrupts
  every session/persistence gate).
- The system is hard-halted. This scaffold prepares the seam; it does not flip it.
"""

from __future__ import annotations

import math
import os
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from typing import Any, Callable, Optional

# Reuse the already-tested single-terminal transport seam (gated, fail-closed).
# These imports are pure (no network/broker on import) — verified by bridge_adapter.
from bridge_adapter import (  # type: ignore
    BridgeAdapter,
    BridgeConfig,
    BridgeGateError,
    NullBridgeAdapter,
    OrderResult,
    PositionInfo,
    TickData,
    make_bridge_adapter,
    MAGIC_NUMBER,
)

__all__ = [
    "BrokerRole",
    "SymbolSpec",
    "BrokerSymbolMap",
    "FTMO_SYMBOL_MAP",
    "redacted_account_SYMBOL_MAP",
    "ClockOffsetCheck",
    "TerminalConfig",
    "DualMT5Config",
    "FollowerLegResult",
    "DualDecisionResult",
    "ParityLegRecord",
    "ParityLedgerSink",
    "DualMT5Adapter",
    "make_dual_mt5_adapter",
    "FOLLOWER_SKIP_REASONS",
]


# --------------------------------------------------------------------------- #
# Roles
# --------------------------------------------------------------------------- #
class BrokerRole:
    PRIMARY = "primary"      # FTMO — reads market data, runs the decision engine, executes
    FOLLOWER = "follower"    # redacted_account — spec-translated mirror of each primary decision


# Skip reasons a follower leg can be dropped for WITHOUT ever touching the primary.
FOLLOWER_SKIP_REASONS = (
    "follower_missing_symbol",
    "follower_symbol_untradeable",
    "follower_large_slippage",
    "follower_order_rejected",
    "follower_not_connected",
    "follower_spec_mismatch",
    "follower_clock_unsafe",
    "follower_governor_blocked",
    "follower_below_min_lot",   # notional-rescaled lot falls below the follower's min lot
)


# --------------------------------------------------------------------------- #
# Per-broker symbol / spec / spread-floor map
# --------------------------------------------------------------------------- #
@dataclass(frozen=True)
class SymbolSpec:
    """Per-broker contract spec for ONE canonical symbol.

    ``broker_symbol`` is the broker-native name (handles .cash / .c / pro / suffixes).
    ``spread_floor_r`` is the MEASURED per-broker round-trip tick-spread floor in R
    (the live sizer must never assume a fill cheaper than this on this broker). It is
    re-measured per broker because redacted_account spread can exceed FTMO (DUAL_MT5_ARCHITECTURE.md).
    ``None`` spread_floor => not directly measured on this broker -> the caller uses the
    canonical book floor (ultimate_book_live_package.TICK_SPREAD_FLOOR_R) as a fallback,
    and a follower leg with an UNVERIFIED floor above the untradeable wall is skipped.
    """
    canonical: str            # the book's canonical symbol (e.g. "XAUUSD")
    broker_symbol: str        # the broker-native symbol (e.g. "XAUUSD.pro")
    contract_size: float      # units per 1.0 lot (e.g. 100 oz for gold) — drives follower lot rescale
    digits: int               # price digits (pip/point precision)
    spread_floor_r: Optional[float] = None   # measured round-trip tick floor in R (per broker)
    tradeable: bool = True    # False => never mirror this symbol on this broker (illiquid/dropped)
    note: str = ""
    volume_min: float = 0.01  # broker min lot (follower legs below this after rescale are skipped)
    volume_step: float = 0.01 # broker lot step (follower lots floored to this — never over-risk)


@dataclass(frozen=True)
class BrokerSymbolMap:
    """Canonical -> broker-native spec map for one broker. Missing symbol => skip on follower."""
    broker: str
    specs: dict[str, SymbolSpec]

    def resolve(self, canonical: str) -> Optional[SymbolSpec]:
        return self.specs.get(canonical)

    def has(self, canonical: str) -> bool:
        return canonical in self.specs


# FTMO is the PRIMARY / native reference distribution. broker_symbol == canonical for
# the carriers (the book was built on FTMO names). spread floors are the MEASURED
# per-symbol bridge round-trip floors (ultimate_book_live_package.TICK_SPREAD_FLOOR_R,
# which were measured on the FTMO-fed siliconmetatrader5 bridge). contract_size/digits
# are the standard FTMO MT5 specs; the owner verifies them at startup against the live
# terminal (symbol_info) and the adapter fails closed on any mismatch.
# Full curated 27-symbol universe. contract_size/digits VERIFIED live on FTMO-Server3
# 2026-06-14 (VERIFIED_BROKER_SYMBOL_SPECS.json). FTMO is PRIMARY: it carries all 27.
FTMO_SYMBOL_MAP = BrokerSymbolMap(
    broker="ftmo",
    specs={
        # metals (metals_core / softband / ob_micro) — crosses are FTMO-only (FN lacks them)
        "XAUUSD":      SymbolSpec("XAUUSD", "XAUUSD", 100.0, 2, 0.0118, True, "primary native"),
        "XAGUSD":      SymbolSpec("XAGUSD", "XAGUSD", 5000.0, 3, 0.0408, True, "primary native"),
        "XAUEUR":      SymbolSpec("XAUEUR", "XAUEUR", 100.0, 2, None, True, "metals cross; EUR profit ccy"),
        "XAGEUR":      SymbolSpec("XAGEUR", "XAGEUR", 5000.0, 3, None, True, "metals cross"),
        "XAUAUD":      SymbolSpec("XAUAUD", "XAUAUD", 100.0, 2, None, True, "metals cross"),
        "XAGAUD":      SymbolSpec("XAGAUD", "XAGAUD", 5000.0, 3, None, True, "metals cross"),
        # crypto
        "BTCUSD":      SymbolSpec("BTCUSD", "BTCUSD", 1.0, 2, 0.0001, True, "primary native"),
        "ETHUSD":      SymbolSpec("ETHUSD", "ETHUSD", 10.0, 2, None, True, "FTMO contract 10 (FN=1 -> follower x10)"),
        "DASHUSD":     SymbolSpec("DASHUSD", "DASHUSD", 1000.0, 2, None, True, "FTMO-only crypto"),
        # energy + agri
        "USOIL_cash":  SymbolSpec("USOIL_cash", "USOIL.cash", 100.0, 3, 0.0270, True, "verified live 2026-06-14"),
        "UKOIL_cash":  SymbolSpec("UKOIL_cash", "UKOIL.cash", 100.0, 3, 0.0258, True, "verified live 2026-06-14"),
        "CORN_c":      SymbolSpec("CORN_c", "CORN.c", 1.0, 2, None, True, "FTMO-only agri"),
        "COTTON_c":    SymbolSpec("COTTON_c", "COTTON.c", 1.0, 2, None, True, "FTMO-only agri"),
        # jpy (fx_jpy / fx_jpy_ny / sub_mid_dn_revert)
        "USDJPY":      SymbolSpec("USDJPY", "USDJPY", 100000.0, 3, 0.0841, True, "primary native"),
        "GBPJPY":      SymbolSpec("GBPJPY", "GBPJPY", 100000.0, 3, None, True, "floor transfers from USDJPY"),
        "EURJPY":      SymbolSpec("EURJPY", "EURJPY", 100000.0, 3, None, True, "substrate jpy carrier"),
        "AUDJPY":      SymbolSpec("AUDJPY", "AUDJPY", 100000.0, 3, None, True, "substrate jpy carrier"),
        "CHFJPY":      SymbolSpec("CHFJPY", "CHFJPY", 100000.0, 3, None, True, "substrate jpy carrier"),
        # indices — FTMO contract 1 (FN=10 -> follower x0.1). FTMO native uses .cash + US-naming.
        "GER40":       SymbolSpec("GER40", "GER40.cash", 1.0, 2, None, True, "DAX40"),
        "UK100":       SymbolSpec("UK100", "UK100.cash", 1.0, 2, None, True, "FTSE100"),
        "SPX500":      SymbolSpec("SPX500", "US500.cash", 1.0, 2, None, True, "S&P500 (FTMO US500.cash)"),
        "NAS100":      SymbolSpec("NAS100", "US100.cash", 1.0, 2, None, True, "NASDAQ100 (FTMO US100.cash)"),
        "JP225":       SymbolSpec("JP225", "JP225.cash", 10.0, 2, None, True, "Nikkei (FTMO digits 2, FN digits 0)"),
        "US30_cash":   SymbolSpec("US30_cash", "US30.cash", 1.0, 2, None, True, "Dow"),
        "FRA40_cash":  SymbolSpec("FRA40_cash", "FRA40.cash", 1.0, 2, None, True, "CAC40"),
        "EU50_cash":   SymbolSpec("EU50_cash", "EU50.cash", 1.0, 2, None, True, "Euro Stoxx 50"),
        "US2000_cash": SymbolSpec("US2000_cash", "US2000.cash", 1.0, 2, None, True, "Russell 2000 (FTMO digits 2, FN digits 1)"),
    },
)

# redacted_account is the FOLLOWER. broker_symbol shows the DIFFERENT native naming this
# broker uses. contract_size / digits below are VERIFIED against the live redacted_account
# terminal (symbol_info) on 2026-06-14 (resident operator). Cross-broker note: FN names
# its oil USOUSD / UKOUSD (NOT USOIL.* / UKOIL.* — the earlier .c placeholders did not
# exist on FN, so the follower would have silently skipped oil forever). GBPJPY IS present
# on FN and is now mapped. spread_floor_r stays None: the round-trip floor in R must be
# re-measured per broker DURING MARKET HOURS (several FN symbols quoted spread 0 at the
# off-hours measurement), and the canonical book floor is the conservative fallback. An
# unverified follower floor at/above the untradeable wall is skipped. See
# VERIFIED_BROKER_SYMBOL_SPECS.json for the full live-measured spec table.
# redacted_account FOLLOWER map — 20 of 27 (live-verified FN-Server2 2026-06-14). The 7 FTMO-only
# symbols (XAUEUR/XAGEUR/XAUAUD/XAGAUD/DASHUSD/CORN_c/COTTON_c) are intentionally ABSENT: FN
# has no metals crosses / DASH / commodities, so those follower legs SKIP (missing-symbol,
# isolated — primary unaffected). Contract sizes that DIFFER from FTMO drive the follower lot
# rescale (follower_volume_for): ETHUSD FN=1 (FTMO 10); all indices FN=10 (FTMO 1). FN-native
# names differ (NDX100/SPX500/US30/GER30/EUSTX50/USOUSD/UKOUSD). digits: JP225 0, US2000 1.
redacted_account_SYMBOL_MAP = BrokerSymbolMap(
    broker="redacted_account",
    specs={
        "XAUUSD":      SymbolSpec("XAUUSD", "XAUUSD", 100.0, 2, None, True, "1:1 vs FTMO; spread ~3.1bps"),
        "XAGUSD":      SymbolSpec("XAGUSD", "XAGUSD", 5000.0, 3, None, True, "1:1 vs FTMO"),
        "BTCUSD":      SymbolSpec("BTCUSD", "BTCUSD", 1.0, 2, None, True, "1:1 vs FTMO"),
        "ETHUSD":      SymbolSpec("ETHUSD", "ETHUSD", 1.0, 2, None, True, "FN contract 1 vs FTMO 10 -> follower lots x10"),
        "USOIL_cash":  SymbolSpec("USOIL_cash", "USOUSD", 100.0, 3, None, True, "FN native USOUSD; 1:1 vs FTMO"),
        "UKOIL_cash":  SymbolSpec("UKOIL_cash", "UKOUSD", 100.0, 3, None, True, "FN native UKOUSD; 1:1 vs FTMO"),
        "USDJPY":      SymbolSpec("USDJPY", "USDJPY", 100000.0, 3, None, True, "1:1 vs FTMO"),
        "GBPJPY":      SymbolSpec("GBPJPY", "GBPJPY", 100000.0, 3, None, True, "1:1 vs FTMO"),
        "EURJPY":      SymbolSpec("EURJPY", "EURJPY", 100000.0, 3, None, True, "1:1 vs FTMO"),
        "AUDJPY":      SymbolSpec("AUDJPY", "AUDJPY", 100000.0, 3, None, True, "1:1 vs FTMO"),
        "CHFJPY":      SymbolSpec("CHFJPY", "CHFJPY", 100000.0, 3, None, True, "1:1 vs FTMO"),
        "GER40":       SymbolSpec("GER40", "GER30", 10.0, 2, None, True, "FN native GER30 (=DAX40); contract 10 -> follower x0.1"),
        "UK100":       SymbolSpec("UK100", "UK100", 10.0, 2, None, True, "contract 10 -> follower x0.1"),
        "SPX500":      SymbolSpec("SPX500", "SPX500", 10.0, 2, None, True, "contract 10 -> follower x0.1"),
        "NAS100":      SymbolSpec("NAS100", "NDX100", 10.0, 2, None, True, "FN native NDX100; contract 10 -> follower x0.1"),
        "JP225":       SymbolSpec("JP225", "JP225", 10.0, 0, None, True, "FN digits 0 (FTMO 2); contract 10 == FTMO 10"),
        "US30_cash":   SymbolSpec("US30_cash", "US30", 10.0, 2, None, True, "FN native US30; contract 10 -> follower x0.1"),
        "FRA40_cash":  SymbolSpec("FRA40_cash", "FRA40", 10.0, 2, None, True, "contract 10 -> follower x0.1"),
        "EU50_cash":   SymbolSpec("EU50_cash", "EUSTX50", 10.0, 2, None, True, "FN native EUSTX50; contract 10 -> follower x0.1"),
        "US2000_cash": SymbolSpec("US2000_cash", "US2000", 10.0, 1, None, True, "FN digits 1 (FTMO 2); contract 10 -> follower x0.1"),
    },
)


# --------------------------------------------------------------------------- #
# Clock / UTC normalization (chronological safety — TOP operator watch item)
# --------------------------------------------------------------------------- #
# A terminal whose server clock differs from UTC by more than this is UNSAFE: every
# bar-timing / session-gate / persistence feature is timezone-sensitive, and an
# undetected skew silently corrupts the gates. Fail closed beyond tolerance.
DEFAULT_CLOCK_TOLERANCE_SECONDS: float = 2.0


@dataclass(frozen=True)
class ClockOffsetCheck:
    """Result of comparing a terminal's reported server time to canonical UTC."""
    broker: str
    role: str
    terminal_utc: Optional[datetime]   # the terminal's tick/server time, interpreted as UTC
    reference_utc: datetime            # our canonical UTC reference at the same moment
    offset_seconds: Optional[float]    # terminal_utc - reference_utc (None if no time available)
    tolerance_seconds: float
    safe: bool                         # |offset| <= tolerance AND a time was actually read
    reason: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "broker": self.broker, "role": self.role,
            "terminal_utc": self.terminal_utc.isoformat() if self.terminal_utc else None,
            "reference_utc": self.reference_utc.isoformat(),
            "offset_seconds": self.offset_seconds,
            "tolerance_seconds": self.tolerance_seconds,
            "safe": self.safe, "reason": self.reason,
        }


def evaluate_clock_offset(
    *, broker: str, role: str,
    terminal_time: Optional[datetime],
    reference_utc: Optional[datetime] = None,
    tolerance_seconds: float = DEFAULT_CLOCK_TOLERANCE_SECONDS,
) -> ClockOffsetCheck:
    """Compare a terminal's reported time to canonical UTC. Fail-closed if no time read.

    ``terminal_time`` is the terminal's most recent tick/server time. Naive datetimes are
    interpreted as UTC (the adapter normalizes all broker times to UTC on read). The check
    is SAFE only when a time was actually available AND |offset| <= tolerance.
    """
    ref = reference_utc or datetime.now(timezone.utc)
    if ref.tzinfo is None:
        ref = ref.replace(tzinfo=timezone.utc)
    if terminal_time is None:
        return ClockOffsetCheck(broker, role, None, ref, None, tolerance_seconds,
                                False, "no_terminal_time_fail_closed")
    t = terminal_time if terminal_time.tzinfo else terminal_time.replace(tzinfo=timezone.utc)
    offset = (t - ref).total_seconds()
    safe = abs(offset) <= tolerance_seconds
    return ClockOffsetCheck(
        broker, role, t.astimezone(timezone.utc), ref, offset, tolerance_seconds,
        safe, "ok" if safe else f"clock_offset_{offset:.3f}s_exceeds_tol_{tolerance_seconds}s")


# --------------------------------------------------------------------------- #
# Per-terminal config + dual config
# --------------------------------------------------------------------------- #
@dataclass
class TerminalConfig:
    """Config for ONE terminal. Wraps a single-terminal BridgeConfig + role + symbol map.

    Creds are read from ENV by the wrapped BridgeConfig (per-terminal ENV var names so the
    two terminals never share credentials)."""
    role: str                          # BrokerRole.PRIMARY | BrokerRole.FOLLOWER
    bridge: BridgeConfig               # transport (creds via ENV, gates, host/port, terminal path)
    symbol_map: BrokerSymbolMap
    clock_tolerance_seconds: float = DEFAULT_CLOCK_TOLERANCE_SECONDS
    # follower-only: max acceptable slippage (in R) before a leg is skipped (never the primary).
    max_follower_slippage_r: float = 0.10

    @property
    def broker(self) -> str:
        return self.symbol_map.broker


def _default_ftmo_terminal() -> TerminalConfig:
    return TerminalConfig(
        role=BrokerRole.PRIMARY,
        bridge=BridgeConfig(
            transport="local_mt5",                 # VPS = local terminal, NOT the dev bridge
            env_login="GTOS_FTMO_MT5_LOGIN",
            env_password="GTOS_FTMO_MT5_PASSWORD",
            env_server="GTOS_FTMO_MT5_SERVER",
            profile_namespace="ftmo_primary",
        ),
        symbol_map=FTMO_SYMBOL_MAP,
    )


def _default_redacted_account_terminal() -> TerminalConfig:
    return TerminalConfig(
        role=BrokerRole.FOLLOWER,
        bridge=BridgeConfig(
            transport="local_mt5",
            env_login="GTOS_redacted_account_MT5_LOGIN",
            env_password="GTOS_redacted_account_MT5_PASSWORD",
            env_server="GTOS_redacted_account_MT5_SERVER",
            profile_namespace="redacted_account_follower",
        ),
        symbol_map=redacted_account_SYMBOL_MAP,
    )


@dataclass
class DualMT5Config:
    """Top-level dual config. DEFAULT-OFF: live_connect_allowed stays False on both
    terminals unless the owner opts in per terminal on the VPS."""
    primary: TerminalConfig = field(default_factory=_default_ftmo_terminal)
    follower: TerminalConfig = field(default_factory=_default_redacted_account_terminal)

    def __post_init__(self) -> None:
        # Architecture invariant: PRIMARY must be FTMO, FOLLOWER must be redacted_account.
        if self.primary.role != BrokerRole.PRIMARY:
            raise ValueError("primary terminal must have role=PRIMARY")
        if self.follower.role != BrokerRole.FOLLOWER:
            raise ValueError("follower terminal must have role=FOLLOWER")


# --------------------------------------------------------------------------- #
# Result + parity ledger contracts
# --------------------------------------------------------------------------- #
@dataclass
class FollowerLegResult:
    """Outcome of the follower (redacted_account) mirror of one primary decision."""
    mirrored: bool                      # True if the follower order was placed
    skipped: bool                       # True if the leg was skipped (never the primary)
    skip_reason: Optional[str]          # one of FOLLOWER_SKIP_REASONS when skipped
    broker_symbol: Optional[str]        # the translated follower symbol (if resolved)
    order_result: Optional[OrderResult]
    detail: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "mirrored": self.mirrored, "skipped": self.skipped,
            "skip_reason": self.skip_reason, "broker_symbol": self.broker_symbol,
            "order_result": _order_to_dict(self.order_result), "detail": self.detail,
        }


@dataclass
class DualDecisionResult:
    """Outcome of executing one decision across both terminals.

    The primary result is authoritative; the follower is best-effort and isolated."""
    canonical_symbol: str
    primary_executed: bool
    primary_order: Optional[OrderResult]
    follower: FollowerLegResult
    parity: "ParityLegRecord"

    def to_dict(self) -> dict[str, Any]:
        return {
            "canonical_symbol": self.canonical_symbol,
            "primary_executed": self.primary_executed,
            "primary_order": _order_to_dict(self.primary_order),
            "follower": self.follower.to_dict(),
            "parity": self.parity.to_dict(),
        }


@dataclass
class ParityLegRecord:
    """A primary-vs-follower parity record for ONE decision (the operator's watch ledger).

    Answers DUAL_MT5_ARCHITECTURE.md's parity question: for every FTMO decision, did
    redacted_account fill the translated order, at what slip, on the matching symbol?"""
    intent_id: str
    canonical_symbol: str
    primary_broker_symbol: Optional[str]
    follower_broker_symbol: Optional[str]
    primary_filled: bool
    follower_filled: bool
    follower_skip_reason: Optional[str]
    primary_price: Optional[float]
    follower_price: Optional[float]
    slippage_r: Optional[float]
    recorded_at_utc: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    @property
    def diverged(self) -> bool:
        """True if the follower did NOT match the primary (skip, no-fill, or symbol mismatch)."""
        if not self.primary_filled:
            return False  # primary didn't act -> nothing to mirror
        return (not self.follower_filled) or (self.follower_skip_reason is not None)

    def to_dict(self) -> dict[str, Any]:
        d = {
            "intent_id": self.intent_id, "canonical_symbol": self.canonical_symbol,
            "primary_broker_symbol": self.primary_broker_symbol,
            "follower_broker_symbol": self.follower_broker_symbol,
            "primary_filled": self.primary_filled, "follower_filled": self.follower_filled,
            "follower_skip_reason": self.follower_skip_reason,
            "primary_price": self.primary_price, "follower_price": self.follower_price,
            "slippage_r": self.slippage_r, "diverged": self.diverged,
            "recorded_at_utc": self.recorded_at_utc,
        }
        return d


# A parity sink is any callable that accepts a ParityLegRecord. The owner wires this to
# monitor.record_parity (FTMO-vs-redacted_account ledger) at go-live. Default: collect in-memory.
ParityLedgerSink = Callable[[ParityLegRecord], None]


def _order_to_dict(r: Optional[OrderResult]) -> Optional[dict[str, Any]]:
    if r is None:
        return None
    return {"retcode": r.retcode, "order": r.order, "volume": r.volume,
            "price": r.price, "comment": r.comment, "success": r.success}


# --------------------------------------------------------------------------- #
# The dual adapter
# --------------------------------------------------------------------------- #
class DualMT5Adapter:
    """FTMO-PRIMARY / redacted_account-FOLLOWER dual-terminal adapter (DEFAULT-OFF, fail-closed).

    Two single-terminal transports (each a ``bridge_adapter.BridgeAdapter``). The PRIMARY
    is the read/decide/execute surface; the FOLLOWER is a spec-translated, isolated mirror.

    Construction is side-effect-free: it builds the two transports (NullBridgeAdapter unless
    the owner opted each in) but does NOT connect. ``connect()`` connects the primary first;
    a follower connect failure does NOT prevent the primary from being live (the follower is
    best-effort by design).
    """

    def __init__(
        self, config: Optional[DualMT5Config] = None, *,
        gate_ok: Optional[Callable[[], bool]] = None,
        halt_clear: Optional[Callable[[], bool]] = None,
        parity_sink: Optional[ParityLedgerSink] = None,
        canonical_floor_lookup: Optional[Callable[[str], Optional[float]]] = None,
        untradeable_floor_r: float = 0.20,
    ) -> None:
        self.config = config or DualMT5Config()
        # Each terminal is gated independently; both share the SAME triple-gate + halt
        # callbacks (one runtime authority), but each refuses on its own creds.
        self._gate_ok = gate_ok or (lambda: False)
        self._halt_clear = halt_clear or (lambda: False)
        self.primary: BridgeAdapter = make_bridge_adapter(
            self.config.primary.bridge, gate_ok=self._gate_ok, halt_clear=self._halt_clear)
        self.follower: BridgeAdapter = make_bridge_adapter(
            self.config.follower.bridge, gate_ok=self._gate_ok, halt_clear=self._halt_clear)
        # Parity ledger sink (owner wires monitor.record_parity at go-live).
        self._parity_records: list[ParityLegRecord] = []
        self._parity_sink: ParityLedgerSink = parity_sink or self._parity_records.append
        # Canonical book floor fallback (ultimate_book_live_package.tick_spread_floor_for).
        self._canonical_floor_lookup = canonical_floor_lookup
        self._untradeable_floor_r = untradeable_floor_r

    # ---------------- connection (primary first; follower best-effort) ----------------
    def connect(self) -> dict[str, Any]:
        """Connect the primary, then attempt the follower. Returns a status dict.

        The primary MUST connect for the system to trade; the follower is best-effort.
        A NullBridgeAdapter (default-off) returns connected=False without raising, so the
        default config yields a clean 'not live' status rather than an error.
        """
        primary_connected = _safe_connect(self.primary)
        follower_connected = _safe_connect(self.follower)
        return {
            "primary": {"broker": self.config.primary.broker, "connected": primary_connected},
            "follower": {"broker": self.config.follower.broker, "connected": follower_connected,
                         "isolated": True},
            "live": primary_connected,   # 'live' tracks the PRIMARY only — follower never gates it
            "checked_at_utc": datetime.now(timezone.utc).isoformat(),
        }

    def disconnect(self) -> None:
        for a in (self.primary, self.follower):
            try:
                a.disconnect()
            except Exception:
                pass

    def is_primary_connected(self) -> bool:
        return self.primary.is_connected()

    def is_follower_connected(self) -> bool:
        return self.follower.is_connected()

    # ---------------- chronological safety (UTC offset, both terminals) ----------------
    def check_clocks(self, *, reference_utc: Optional[datetime] = None) -> dict[str, Any]:
        """Verify BOTH terminals' clocks against canonical UTC. Fail-closed per terminal.

        Reads each terminal's most recent tick time (already normalized to UTC by the
        underlying adapter) and compares to a single canonical reference. The PRIMARY being
        clock-unsafe makes the whole system unsafe (no safe decisions can be made); the
        FOLLOWER being clock-unsafe only skips follower legs (isolation preserved).
        """
        ref = reference_utc or datetime.now(timezone.utc)
        p_time = self._terminal_time(self.primary, self.config.primary)
        f_time = self._terminal_time(self.follower, self.config.follower)
        p = evaluate_clock_offset(
            broker=self.config.primary.broker, role=BrokerRole.PRIMARY, terminal_time=p_time,
            reference_utc=ref, tolerance_seconds=self.config.primary.clock_tolerance_seconds)
        f = evaluate_clock_offset(
            broker=self.config.follower.broker, role=BrokerRole.FOLLOWER, terminal_time=f_time,
            reference_utc=ref, tolerance_seconds=self.config.follower.clock_tolerance_seconds)
        return {
            "primary": p.to_dict(), "follower": f.to_dict(),
            "system_clock_safe": p.safe,            # primary gates the system
            "follower_clock_safe": f.safe,          # follower only gates follower legs
            "checked_at_utc": ref.isoformat(),
        }

    def _terminal_time(self, adapter: BridgeAdapter, tcfg: TerminalConfig) -> Optional[datetime]:
        """Read a terminal's current time via a representative tick (UTC-normalized).
        Returns None if not connected or no tick — caller treats None as fail-closed."""
        if not adapter.is_connected():
            return None
        sym = next(iter(tcfg.symbol_map.specs.values()), None)
        if sym is None:
            return None
        try:
            tick = adapter.get_tick(sym.broker_symbol)
        except Exception:
            return None
        return tick.time if tick else None

    # ---------------- primary market data (read OHLC/tick from FTMO) ----------------
    def get_primary_tick(self, canonical: str) -> Optional[TickData]:
        """Read a tick from the PRIMARY (FTMO) — the validated decision distribution."""
        spec = self.config.primary.symbol_map.resolve(canonical)
        if spec is None or not self.primary.is_connected():
            return None
        try:
            return self.primary.get_tick(spec.broker_symbol)
        except Exception:
            return None

    def get_primary_equity(self) -> float:
        return self.primary.get_account_equity() if self.primary.is_connected() else 0.0

    def get_follower_equity(self) -> float:
        return self.follower.get_account_equity() if self.follower.is_connected() else 0.0

    # ---------------- follower spec translation ----------------
    def translate_to_follower(self, canonical: str) -> tuple[Optional[SymbolSpec], Optional[str]]:
        """Resolve the follower-native spec for a canonical symbol.

        Returns (spec, skip_reason). skip_reason is set (spec None) when the symbol is
        missing on the follower, marked untradeable, or its spread floor is unverified AND
        the canonical book floor sits at/above the untradeable wall (re-measure required).
        """
        spec = self.config.follower.symbol_map.resolve(canonical)
        if spec is None:
            return None, "follower_missing_symbol"
        if not spec.tradeable:
            return None, "follower_symbol_untradeable"
        # spread floor: prefer the per-broker measured floor; else fall back to the
        # canonical book floor. An unverified follower floor at/above the wall is skipped.
        floor = spec.spread_floor_r
        if floor is None and self._canonical_floor_lookup is not None:
            floor = self._canonical_floor_lookup(canonical)
        if floor is not None and floor >= self._untradeable_floor_r:
            return None, "follower_symbol_untradeable"
        return spec, None

    def follower_volume_for(self, canonical: str, primary_volume: float) -> Optional[float]:
        """Notional-equivalent follower lot size (the cross-broker contract-size fix).

        The follower (redacted_account) contract_size differs from FTMO for several instruments
        (indices FN=10 vs FTMO=1; ETHUSD FN=1 vs FTMO=10), so copying the primary lot count
        verbatim would mis-size the follower by that ratio. Rescale by notional parity:

            follower_lots = primary_lots * (primary_contract_size / follower_contract_size)

        floored to the follower's lot step (never rounded UP -> never over-risks the follower).
        Returns None if either leg is unmapped or the rescaled lot falls below the follower's
        min lot (caller then SKIPS the follower leg with follower_below_min_lot — never the
        primary). For 1:1 carriers (same contract_size) this returns primary_volume unchanged.
        """
        p = self.config.primary.symbol_map.resolve(canonical)
        f = self.config.follower.symbol_map.resolve(canonical)
        if p is None or f is None or not f.contract_size or primary_volume <= 0:
            return None
        raw = primary_volume * (p.contract_size / f.contract_size)
        step = f.volume_step or 0.01
        lots = round(math.floor(round(raw / step, 9)) * step, 8)
        if lots < (f.volume_min or 0.01):
            return None
        return lots

    # ---------------- the core: execute one decision across both terminals ----------------
    def execute_decision(
        self, *, intent_id: str, canonical_symbol: str,
        primary_request: dict[str, Any],
        follower_request_builder: Optional[Callable[[SymbolSpec], dict[str, Any]]] = None,
    ) -> DualDecisionResult:
        """Execute a primary (FTMO) decision and mirror it on the follower (redacted_account).

        ``primary_request`` is the MT5 order request dict for the FTMO leg (the caller
        already sized it via the deploy book on FTMO data). ``follower_request_builder``
        maps the resolved follower SymbolSpec to the follower order request (spec-translated
        symbol / volume); if omitted, a minimal translation re-uses the primary request with
        the follower-native symbol substituted.

        FOLLOWER ISOLATION: any follower problem -> skip the follower leg and record it;
        the primary order is sent regardless of follower state. A follower exception NEVER
        propagates to the primary path.
        """
        # 1. PRIMARY (FTMO) — authoritative.
        primary_order = self._send_primary(primary_request)
        primary_filled = primary_order is not None and primary_order.success
        primary_symbol = primary_request.get("symbol")

        # 2. FOLLOWER (redacted_account) — best-effort, isolated. Only mirror a FILLED primary.
        if not primary_filled:
            leg = FollowerLegResult(
                mirrored=False, skipped=True, skip_reason=None, broker_symbol=None,
                order_result=None, detail={"note": "primary_not_filled_nothing_to_mirror"})
            parity = self._build_parity(intent_id, canonical_symbol, primary_symbol, None,
                                        primary_filled, leg, primary_order, None)
            self._record_parity(parity)
            return DualDecisionResult(canonical_symbol, primary_filled, primary_order, leg, parity)

        leg = self._mirror_to_follower(canonical_symbol, primary_request,
                                       primary_order, follower_request_builder)
        follower_price = leg.order_result.price if (leg.order_result and leg.mirrored) else None
        parity = self._build_parity(intent_id, canonical_symbol, primary_symbol,
                                    leg.broker_symbol, primary_filled, leg,
                                    primary_order, follower_price)
        self._record_parity(parity)
        return DualDecisionResult(canonical_symbol, primary_filled, primary_order, leg, parity)

    def _send_primary(self, request: dict[str, Any]) -> Optional[OrderResult]:
        """Send the primary order. Default-off NullBridgeAdapter returns a fail-closed result
        (retcode -1) — never an exception — so default config yields a clean no-op."""
        try:
            return self.primary.order_send(request)
        except BridgeGateError as e:
            return OrderResult(retcode=-1, order=0, volume=0.0, price=0.0,
                               comment=f"primary_gate_blocked:{e}")

    def _mirror_to_follower(
        self, canonical_symbol: str, primary_request: dict[str, Any],
        primary_order: OrderResult,
        follower_request_builder: Optional[Callable[[SymbolSpec], dict[str, Any]]],
    ) -> FollowerLegResult:
        """Mirror the (filled) primary decision onto the follower. ISOLATED: never raises."""
        # connectivity
        if not self.follower.is_connected():
            return FollowerLegResult(False, True, "follower_not_connected", None, None,
                                     {"note": "follower terminal not connected; primary unaffected"})
        # spec translation (missing-symbol / untradeable / unverified-floor)
        spec, skip_reason = self.translate_to_follower(canonical_symbol)
        if spec is None:
            return FollowerLegResult(False, True, skip_reason, None, None,
                                     {"canonical": canonical_symbol})
        # build the follower request (spec-translated symbol)
        if follower_request_builder is not None:
            try:
                follower_request = follower_request_builder(spec)
            except Exception as e:  # builder must never break the primary
                return FollowerLegResult(False, True, "follower_spec_mismatch", spec.broker_symbol,
                                         None, {"builder_error": repr(e)})
        else:
            # Notional-correct default builder (live-verified 2026-06-14 contract-size fix):
            # rescale the follower VOLUME by the contract ratio so index/ETH legs are not mis-sized
            # 10x. A below-min rescaled lot skips the follower leg (never over-risks; primary
            # untouched). 1:1 carriers (FX/metals/BTC/both oils) pass through unchanged.
            follower_request = dict(primary_request)
            follower_request["symbol"] = spec.broker_symbol
            prim_vol = primary_request.get("volume")
            if prim_vol is not None:
                fvol = self.follower_volume_for(canonical_symbol, float(prim_vol))
                if fvol is None:
                    return FollowerLegResult(False, True, "follower_below_min_lot", spec.broker_symbol,
                                             None, {"primary_volume": prim_vol,
                                                    "note": "notional-rescaled follower lot below min lot"})
                follower_request["volume"] = fvol
        # send the follower order, isolated
        try:
            res = self.follower.order_send(follower_request)
        except BridgeGateError as e:
            return FollowerLegResult(False, True, "follower_order_rejected", spec.broker_symbol,
                                     None, {"gate_error": repr(e)})
        except Exception as e:  # ANY transport error on the follower is contained
            return FollowerLegResult(False, True, "follower_order_rejected", spec.broker_symbol,
                                     None, {"transport_error": repr(e)})
        if not res.success:
            return FollowerLegResult(False, True, "follower_order_rejected", spec.broker_symbol,
                                     res, {"retcode": res.retcode, "comment": res.comment})
        # slippage check (in R) vs the primary fill — large slip => skip/flag, never primary
        slip_r = self._slippage_r(primary_request, primary_order, res)
        if slip_r is not None and slip_r > self.config.follower.max_follower_slippage_r:
            return FollowerLegResult(False, True, "follower_large_slippage", spec.broker_symbol,
                                     res, {"slippage_r": slip_r,
                                           "max": self.config.follower.max_follower_slippage_r})
        return FollowerLegResult(True, False, None, spec.broker_symbol, res,
                                 {"slippage_r": slip_r})

    def _slippage_r(self, primary_request: dict[str, Any],
                    primary_order: OrderResult, follower_order: OrderResult) -> Optional[float]:
        """Follower-vs-primary fill slippage expressed in R (uses the request's stop distance).

        R = |follower_price - primary_price| / stop_dist_price. Returns None if the stop
        distance is unavailable (caller then treats slip as unknown -> not a skip trigger)."""
        stop_dist = primary_request.get("stop_dist_price") or primary_request.get("stop_dist")
        if not stop_dist or stop_dist <= 0:
            return None
        if not primary_order.price or not follower_order.price:
            return None
        return abs(follower_order.price - primary_order.price) / float(stop_dist)

    # ---------------- parity ledger ----------------
    def _build_parity(self, intent_id: str, canonical: str,
                      primary_symbol: Optional[str], follower_symbol: Optional[str],
                      primary_filled: bool, leg: FollowerLegResult,
                      primary_order: Optional[OrderResult],
                      follower_price: Optional[float]) -> ParityLegRecord:
        return ParityLegRecord(
            intent_id=intent_id, canonical_symbol=canonical,
            primary_broker_symbol=primary_symbol, follower_broker_symbol=follower_symbol,
            primary_filled=primary_filled, follower_filled=leg.mirrored,
            follower_skip_reason=leg.skip_reason,
            primary_price=(primary_order.price if primary_order else None),
            follower_price=follower_price,
            slippage_r=leg.detail.get("slippage_r"))

    def _record_parity(self, record: ParityLegRecord) -> None:
        try:
            self._parity_sink(record)
        except Exception:
            # the parity sink must never break execution; keep the in-memory copy.
            self._parity_records.append(record)

    @property
    def parity_records(self) -> list[ParityLegRecord]:
        return list(self._parity_records)

    def parity_summary(self) -> dict[str, Any]:
        """Quick FTMO-vs-redacted_account divergence summary over the in-memory records."""
        recs = self._parity_records
        n = len(recs)
        diverged = [r for r in recs if r.diverged]
        slips = [r.slippage_r for r in recs if r.slippage_r is not None]
        return {
            "n_decisions": n,
            "n_primary_filled": sum(1 for r in recs if r.primary_filled),
            "n_follower_filled": sum(1 for r in recs if r.follower_filled),
            "n_diverged": len(diverged),
            "divergence_reasons": _count_reasons(diverged),
            "mean_slippage_r": round(sum(slips) / len(slips), 6) if slips else None,
            "max_slippage_r": round(max(slips), 6) if slips else None,
        }

    # ---------------- startup self-check ----------------
    def startup_self_check(self, *, reference_utc: Optional[datetime] = None) -> dict[str, Any]:
        """Operator startup gate (charter §Startup self-check). Verifies, without trading:
          - default-off / connect status (primary required, follower best-effort)
          - both clocks normalized to UTC within tolerance (chronological safety)
          - FTMO confirmed primary, redacted_account confirmed follower
          - per-broker symbol-map coverage of the primary universe (missing -> follower skip)
        Returns a green/blocked report; NEVER connects or trades on its own.
        """
        clocks = self.check_clocks(reference_utc=reference_utc)
        coverage = self.symbol_coverage()
        roles_ok = (self.config.primary.role == BrokerRole.PRIMARY
                    and self.config.follower.role == BrokerRole.FOLLOWER
                    and self.config.primary.broker == "ftmo"
                    and self.config.follower.broker == "redacted_account")
        primary_connected = self.is_primary_connected()
        # 'ready' means: roles correct AND (if primary live) its clock is safe. Default-off
        # (primary not connected) is a legitimate NOT-ready-but-not-broken state.
        green = roles_ok and (not primary_connected or clocks["system_clock_safe"])
        return {
            "default_off_primary_connected": primary_connected,
            "default_off_follower_connected": self.is_follower_connected(),
            "roles_ok_ftmo_primary_redacted_account_follower": roles_ok,
            "clocks": clocks,
            "symbol_coverage": coverage,
            "ready_to_enable": bool(green),
            "checked_at_utc": (reference_utc or datetime.now(timezone.utc)).isoformat(),
            "boundary": "no_broker_connect_no_order_in_self_check",
        }

    def symbol_coverage(self) -> dict[str, Any]:
        """Which primary-universe symbols the follower can mirror vs must skip."""
        prim = set(self.config.primary.symbol_map.specs.keys())
        mirrorable, skipped = [], {}
        for canonical in sorted(prim):
            spec, reason = self.translate_to_follower(canonical)
            if spec is not None:
                mirrorable.append(canonical)
            else:
                skipped[canonical] = reason
        return {
            "primary_universe": sorted(prim),
            "follower_mirrorable": mirrorable,
            "follower_skipped": skipped,
            "coverage_ratio": round(len(mirrorable) / len(prim), 4) if prim else 0.0,
        }


def _count_reasons(records: list[ParityLegRecord]) -> dict[str, int]:
    out: dict[str, int] = {}
    for r in records:
        key = r.follower_skip_reason or ("follower_no_fill" if not r.follower_filled else "ok")
        out[key] = out.get(key, 0) + 1
    return out


def _safe_connect(adapter: BridgeAdapter) -> bool:
    """Connect an adapter; the default NullBridgeAdapter returns False (no raise). A gated
    SiliconBridgeAdapter raises BridgeGateError until the owner clears all gates — we treat
    that as 'not connected' (default-off), never a crash."""
    try:
        return bool(adapter.connect())
    except BridgeGateError:
        return False


# --------------------------------------------------------------------------- #
# Factory — DEFAULT-OFF. Returns an adapter whose terminals are both Null unless
# the owner opted each in on its BridgeConfig (live_connect_allowed=True).
# --------------------------------------------------------------------------- #
def make_dual_mt5_adapter(
    config: Optional[DualMT5Config] = None, *,
    gate_ok: Optional[Callable[[], bool]] = None,
    halt_clear: Optional[Callable[[], bool]] = None,
    parity_sink: Optional[ParityLedgerSink] = None,
    canonical_floor_lookup: Optional[Callable[[str], Optional[float]]] = None,
) -> DualMT5Adapter:
    """Build the dual-MT5 adapter. DEFAULT-OFF: with the default config both terminals are
    NullBridgeAdapters (no connect, no orders). The Silicon/local adapter is only built per
    terminal when that terminal's BridgeConfig.live_connect_allowed is True AND the owner
    supplies gate_ok + halt_clear, and even then connect() re-checks all gates."""
    return DualMT5Adapter(
        config or DualMT5Config(), gate_ok=gate_ok, halt_clear=halt_clear,
        parity_sink=parity_sink, canonical_floor_lookup=canonical_floor_lookup)
