"""Canonical Sierra source/proxy registry for shadow-only orderflow rows.

The registry is intentionally explicit: every Sierra feature row should say
which source it came from, how close that source is to the broker symbol, and
what it is allowed to mean. This prevents a captured local file from becoming
an implied trade signal.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any

PROMOTION_VERDICT = "NO_PROMOTION_VERDICT"

VALIDATED_PROXY = "VALIDATED_PROXY"
SAME_MARKET_SOURCE_TRANSFER = "SAME_MARKET_SOURCE_TRANSFER"
FUTURES_PROXY_TRANSFER = "FUTURES_PROXY_TRANSFER"
CONTROL_ONLY = "CONTROL_ONLY"
SOURCE_DEFINITION_BLOCKED = "SOURCE_DEFINITION_BLOCKED"
NO_REGISTERED_PROXY = "NO_REGISTERED_PROXY"


@dataclass(frozen=True)
class SierraProxyRegistryEntry:
    symbol: str
    broker_symbol: str
    sierra_root: str | None
    futures_symbol: str | None
    tick_size: float | None
    proxy_class: str
    source_status: str
    parity_status: str
    interpretation_status: str
    allowed_use: str
    claim_boundary: str
    depth_interpretation_allowed: bool
    scid_interpretation_allowed: bool
    control_only: bool = False
    notes: str = ""

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)

    @property
    def has_depth_source(self) -> bool:
        return bool(self.sierra_root and self.futures_symbol and self.tick_size)


def _entry(
    symbol: str,
    broker_symbol: str,
    sierra_root: str | None,
    futures_symbol: str | None,
    tick_size: float | None,
    proxy_class: str,
    source_status: str,
    parity_status: str,
    interpretation_status: str,
    allowed_use: str,
    claim_boundary: str,
    *,
    depth_interpretation_allowed: bool,
    scid_interpretation_allowed: bool,
    control_only: bool = False,
    notes: str = "",
) -> SierraProxyRegistryEntry:
    return SierraProxyRegistryEntry(
        symbol=symbol,
        broker_symbol=broker_symbol,
        sierra_root=sierra_root,
        futures_symbol=futures_symbol,
        tick_size=tick_size,
        proxy_class=proxy_class,
        source_status=source_status,
        parity_status=parity_status,
        interpretation_status=interpretation_status,
        allowed_use=allowed_use,
        claim_boundary=claim_boundary,
        depth_interpretation_allowed=depth_interpretation_allowed,
        scid_interpretation_allowed=scid_interpretation_allowed,
        control_only=control_only,
        notes=notes,
    )


SIERRA_PROXY_REGISTRY: dict[str, SierraProxyRegistryEntry] = {
    "NAS100": _entry(
        "NAS100",
        "NDX100",
        "NQM26-CME",
        "NQ.v.0",
        0.25,
        VALIDATED_PROXY,
        "LOCAL_SIERRA_DEPTH_CAPTURED",
        "DATABENTO_MBP10_PARITY_EXACT_ON_REGISTERED_NQ_PILOT",
        "USABLE_AS_REGISTERED_NQ_DEPTH_CONTEXT",
        "predecision_nq_mbp10_depth_context_shadow_only",
        "NQ futures depth can be used as registered NAS100 context; it is not broker CFD liquidity and not a live filter.",
        depth_interpretation_allowed=True,
        scid_interpretation_allowed=True,
    ),
    "US30": _entry(
        "US30",
        "US30",
        "YMM26-CBOT",
        "YM.v.0",
        1.0,
        VALIDATED_PROXY,
        "LOCAL_SIERRA_DEPTH_CAPTURED",
        "DATABENTO_MBP10_PARITY_EXACT_ON_REGISTERED_YM_BATCH",
        "USABLE_AS_REGISTERED_YM_DEPTH_CONTEXT",
        "predecision_ym_mbp10_depth_context_shadow_only",
        "YM futures depth can be used as registered US30 context; broker CFD liquidity is not directly observed.",
        depth_interpretation_allowed=True,
        scid_interpretation_allowed=True,
    ),
    "US30_cash": _entry(
        "US30_cash",
        "US30_cash",
        "YMM26-CBOT",
        "YM.v.0",
        1.0,
        VALIDATED_PROXY,
        "LOCAL_SIERRA_DEPTH_CAPTURED",
        "DATABENTO_MBP10_PARITY_EXACT_ON_REGISTERED_YM_BATCH",
        "USABLE_AS_REGISTERED_YM_DEPTH_CONTEXT",
        "predecision_ym_mbp10_depth_context_shadow_only",
        "YM futures depth can be used as registered US30_cash context; broker CFD liquidity is not directly observed.",
        depth_interpretation_allowed=True,
        scid_interpretation_allowed=True,
    ),
    "XAUUSD": _entry(
        "XAUUSD",
        "XAUUSD",
        "GCM26-COMEX",
        "GC.v.0",
        0.1,
        SAME_MARKET_SOURCE_TRANSFER,
        "LOCAL_SIERRA_DEPTH_CAPTURED",
        "DATABENTO_MBP10_PARITY_NEAR_MATCH_GC_SMALL_FIELD_DELTAS",
        "CAUTION_CONTEXT_ONLY_UNTIL_GC_PARITY_BOUNDS_REGISTERED",
        "gold_futures_market_condition_context_shadow_only",
        "GC futures context is useful for market awareness but cannot be treated as spot XAU broker book truth.",
        depth_interpretation_allowed=False,
        scid_interpretation_allowed=True,
    ),
    "XAGUSD": _entry(
        "XAGUSD",
        "XAGUSD",
        "SIM26-COMEX",
        "SI.v.0",
        0.005,
        SOURCE_DEFINITION_BLOCKED,
        "LOCAL_SIERRA_DEPTH_CAPTURED",
        "SOURCE_DEPTH_DEFINITION_BLOCKED_SI",
        "BLOCKED_DO_NOT_TREAT_AS_DATABENTO_EQUIVALENT",
        "source_status_only_until_si_depth_definition_is_registered",
        "SI depth rows are preserved but not interpreted until the SI/SIL source and sampling definition is closed.",
        depth_interpretation_allowed=False,
        scid_interpretation_allowed=False,
    ),
    "USDJPY": _entry(
        "USDJPY",
        "USDJPY",
        "6JM26-CME",
        "6J.v.0",
        0.0000005,
        FUTURES_PROXY_TRANSFER,
        "LOCAL_SIERRA_DEPTH_CAPTURED",
        "FUTURES_PROXY_REVIEW_OPEN_6J",
        "CONTEXT_ONLY_UNTIL_PROXY_VALIDATED",
        "yen_futures_context_only_until_transfer_validated",
        "6J is inverse yen futures context, not USDJPY spot broker liquidity; transfer tests must pass before use.",
        depth_interpretation_allowed=False,
        scid_interpretation_allowed=True,
    ),
    "GBPUSD": _entry(
        "GBPUSD",
        "GBPUSD",
        "6BM26-CME",
        "6B.v.0",
        0.0001,
        FUTURES_PROXY_TRANSFER,
        "LOCAL_SIERRA_DEPTH_CAPTURED",
        "SAMPLING_POLICY_ALIGNMENT_REQUIRED_6B",
        "CAUTION_CONTEXT_ONLY_UNTIL_COMMON_SECOND_POLICY_APPLIED",
        "gbp_futures_context_only_with_common_second_alignment",
        "6B can provide GBP futures context, but feature comparisons require common-second sampling alignment first.",
        depth_interpretation_allowed=False,
        scid_interpretation_allowed=True,
    ),
    "EURUSD": _entry(
        "EURUSD",
        "EURUSD",
        "6EM26-CME",
        "6E.v.0",
        0.00005,
        FUTURES_PROXY_TRANSFER,
        "LOCAL_SIERRA_DEPTH_CAPTURED",
        "FUTURES_PROXY_REVIEW_OPEN_6E",
        "CONTEXT_ONLY_UNTIL_PROXY_VALIDATED",
        "euro_futures_context_only_until_transfer_validated",
        "6E is futures context for EURUSD, not spot broker liquidity; transfer tests are required before use.",
        depth_interpretation_allowed=False,
        scid_interpretation_allowed=True,
    ),
    "GBPJPY": _entry(
        "GBPJPY",
        "GBPJPY",
        None,
        None,
        None,
        NO_REGISTERED_PROXY,
        "NO_REGISTERED_SIERRA_PROXY_FOR_SYMBOL",
        "SOURCE_BLOCKED",
        "BLOCKED_NO_PROXY",
        "no_sierra_orderflow_use",
        "GBPJPY needs a pre-registered two-book or weighted proxy design before external orderflow interpretation.",
        depth_interpretation_allowed=False,
        scid_interpretation_allowed=False,
    ),
    "GER40": _entry(
        "GER40",
        "GER40",
        None,
        None,
        None,
        NO_REGISTERED_PROXY,
        "NO_REGISTERED_SIERRA_PROXY_FOR_SYMBOL",
        "SOURCE_BLOCKED",
        "BLOCKED_NO_PROXY",
        "no_sierra_orderflow_use",
        "No registered Sierra/Databento proxy exists for GER40 in the current GTOS source map.",
        depth_interpretation_allowed=False,
        scid_interpretation_allowed=False,
    ),
    "UK100": _entry(
        "UK100",
        "UK100",
        None,
        None,
        None,
        NO_REGISTERED_PROXY,
        "NO_REGISTERED_SIERRA_PROXY_FOR_SYMBOL",
        "SOURCE_BLOCKED",
        "BLOCKED_NO_PROXY",
        "no_sierra_orderflow_use",
        "No registered Sierra/Databento proxy exists for UK100 in the current GTOS source map.",
        depth_interpretation_allowed=False,
        scid_interpretation_allowed=False,
    ),
    "CL": _entry(
        "CL",
        "CL",
        "CLM26-NYMEX",
        "CL.v.0",
        0.01,
        CONTROL_ONLY,
        "LOCAL_SIERRA_DEPTH_CAPTURED",
        "CONTROL_SOURCE_ONLY",
        "CONTROL_ONLY_NOT_TARGET_CONFLUENCE",
        "macro_liquidity_control_only",
        "CL can be logged as a context/control source, not as direct confluence for a GTOS target symbol.",
        depth_interpretation_allowed=False,
        scid_interpretation_allowed=True,
        control_only=True,
    ),
    "ZN": _entry(
        "ZN",
        "ZN",
        "ZNM26-CBOT",
        "ZN.v.0",
        1.0 / 64.0,
        CONTROL_ONLY,
        "LOCAL_SIERRA_DEPTH_CAPTURED",
        "CONTROL_SOURCE_ONLY",
        "CONTROL_ONLY_NOT_TARGET_CONFLUENCE",
        "rates_liquidity_control_only",
        "ZN can be logged as a rates context/control source, not as direct confluence for a GTOS target symbol.",
        depth_interpretation_allowed=False,
        scid_interpretation_allowed=True,
        control_only=True,
    ),
    "VXM": _entry(
        "VXM",
        "VXM",
        "VXM26-CFE",
        "VX.v.0",
        0.05,
        CONTROL_ONLY,
        "LOCAL_SIERRA_SCID_CAPTURED",
        "CONTROL_SOURCE_ONLY",
        "CONTROL_ONLY_NOT_TARGET_CONFLUENCE",
        "volatility_control_only",
        "VXM/VIX context can be logged as volatility control evidence, not direct GTOS target liquidity.",
        depth_interpretation_allowed=False,
        scid_interpretation_allowed=True,
        control_only=True,
    ),
}


def default_entry(symbol: str, broker_symbol: str | None = None) -> SierraProxyRegistryEntry:
    return _entry(
        symbol,
        broker_symbol or symbol,
        None,
        None,
        None,
        NO_REGISTERED_PROXY,
        "NO_REGISTERED_SIERRA_PROXY_FOR_SYMBOL",
        "SOURCE_BLOCKED",
        "BLOCKED_NO_PROXY",
        "no_sierra_orderflow_use",
        "No registered Sierra source/proxy exists for this symbol.",
        depth_interpretation_allowed=False,
        scid_interpretation_allowed=False,
    )


def registry_entry(symbol: str, broker_symbol: str | None = None) -> SierraProxyRegistryEntry:
    return SIERRA_PROXY_REGISTRY.get(symbol, default_entry(symbol, broker_symbol))


def sierra_proxy_by_symbol() -> dict[str, dict[str, Any]]:
    return {
        symbol: {
            "root": entry.sierra_root,
            "futures_symbol": entry.futures_symbol,
            "tick_size": entry.tick_size,
        }
        for symbol, entry in SIERRA_PROXY_REGISTRY.items()
        if entry.has_depth_source
    }


def sierra_source_status_by_symbol() -> dict[str, dict[str, Any]]:
    return {
        symbol: {
            "source_status": entry.source_status,
            "parity_status": entry.parity_status,
            "interpretation_status": entry.interpretation_status,
            "proxy_class": entry.proxy_class,
            "allowed_use": entry.allowed_use,
            "claim_boundary": entry.claim_boundary,
            "depth_interpretation_allowed": entry.depth_interpretation_allowed,
            "scid_interpretation_allowed": entry.scid_interpretation_allowed,
            "control_only": entry.control_only,
        }
        for symbol, entry in SIERRA_PROXY_REGISTRY.items()
    }


def registry_rows() -> list[dict[str, Any]]:
    return [entry.as_dict() for entry in sorted(SIERRA_PROXY_REGISTRY.values(), key=lambda item: item.symbol)]
