"""``cost_r`` -- the one function that owns every cost number in GTOS.

    cost_r(symbol, account, holding_hours, *, sl_distance_price, ...) -> CostBreakdown

backed by the versioned ``BROKER_TRUE_COSTS_V1.json``. Nothing downstream should compute
a cost any other way.

Two departures from the signature in `SESSION_J_BROKER_TRUTH.md`, both forced by
measurement rather than preference
----------------------------------------------------------------------------------
**1. `sl_distance_price` is required, not optional.** Every cost in this system is a
price-unit or cash drag divided by the trade's stop distance -- that is how the live
engine already computes spread (`broker_net_cost_engine.py:293-294`) and swap
(`:357-360`). Commission is no different:

    commission_r = commission_usd_per_lot / (sl_distance_price * usd_per_price_unit_per_lot)

so commission in R is a property of *the trade*, not of the instrument. USDJPY and GBPJPY
pay the identical $5.00/lot round turn; the 2.1x gap between their R values in
`GATE_G1B_RECEIPT.md` §5.2a (0.1948 vs 0.0927) is entirely stop distance. There is no
defensible default stop, so the layer refuses rather than inventing one -- inventing a
plausible cost number with no basis is exactly what F38 was.

**2. `holding_hours` alone cannot price swap.** Swap is charged per **rollover crossing**,
not per elapsed hour. Measured in the live rows: swap is present on a 2.20 h hold and
absent on a 24.30 h hold (74 of 300 rows carry nonzero swap). Pass `entry_utc` and the
crossings are counted exactly against the broker's own wall clock, including the
triple-swap weekday from `swap_rollover3days`; omit it and the swap term degrades to
[MODELLED] with the assumption stated. The coverage class carries the difference.

Wave-21 evidence repairs add three more fail-closed bindings: a non-USD-profit cash-per-lot
commission uses the latest captured D1 close completed strictly before entry (zero and
notional-bp R do not consume FX); entry slippage is an exact-account/profile-symbol
displacement in PRICE units divided by this trade's stop; and a fill-anchored quote-side
gross may exclude an additional spread deduction only with hash/time/account/symbol-bound
geometry evidence. Missing consumed inputs are NOT_EVALUABLE, never the 2026 snapshot,
pooled constant-R slippage, or zero spread.

Sign convention: costs are positive.
"""

from __future__ import annotations

import hashlib
import json
import math
from enum import Enum
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from functools import lru_cache
from pathlib import Path

from src.costs.artifact_authority import (
    CostInputAuthorityError,
    read_current_file_bytes,
)
from src.costs.coverage import Coverage, Measure, weakest
from src.costs.symbols import resolve_account_symbol
from src.utils.broker_clock import resolve_rule, utc_to_broker_naive

__all__ = [
    "BrokerTrueCosts",
    "CostBreakdown",
    "cost_r",
    "load_broker_true_costs",
    "component_sum_r",
    "elapsed_holding_hours",
    "SpreadAccounting",
    "SpreadGeometryEvidence",
    "VerifiedQuoteGeometryReceipt",
    "QUOTE_GEOMETRY_ROW_SCHEMA",
    "QUOTE_GEOMETRY_APPROVED_RISK_ROW_SCHEMA",
    "APPROVED_PRE_SUBMISSION_RISK_DENOMINATOR_BASIS",
    "legacy_class_cost_r",
    "DEFAULT_ARTIFACT",
]

REPO = Path(__file__).resolve().parents[2]
DEFAULT_ARTIFACT = (
    REPO / "research/operations/broker_truth_layer_2026_07_27/BROKER_TRUE_COSTS_V1.json"
)

# Measured same-class transfer error (BROKER_TRUE_COSTS_V1.json class_fallback_schedule):
# redacted_account metals 0.518%, crypto 0.017%, FX/jpy/index 0.000%; FTMO crypto 0.663%.
# A 5% band is comfortably outside every measured disagreement and still two orders of
# magnitude tighter than the x0.5/x2 default.
_CLASS_TRANSFER_BAND = (0.95, 1.05)
_CLASS_TRANSFER_BAND_PROVENANCE = (
    "measured same-class commission disagreement <=0.663% across every class with >=2 "
    "measured symbols (BROKER_TRUE_COSTS_V1.json:class_fallback_schedule)"
)


#: A commission schedule no measurement on THIS account supports, taken from a NAMED peer
#: and signed by a person. It is deliberately a different `kind` from the resolved schedule
#: it carries, because the generator's automatic class fallback already writes the resolved
#: kind directly (`USOIL.cash`: `kind: per_lot`, `coverage: TRANSFERRED`,
#: `transferred_from: "redacted_account USOUSD (MEASURED, 3 round turns)"`). That shape is correct
#: for a transfer the *build* derived from a measured class median. It is the wrong shape for
#: a transfer a *person* decided to make where the class has no measured member at all,
#: because nothing in it records who decided, when, or why -- and a decision without those
#: three fields is indistinguishable from a fitted number six months later.
#:
#: So: `peer_transfer` resolves to the same arithmetic and can never resolve to a stronger
#: coverage class than TRANSFERRED (`_check_peer_transfer_coverage`). The signature travels
#: in `detail["commission"]["peer_transfer"]` and in the `Measure`'s `transferred_from`.
PEER_TRANSFER = "peer_transfer"

#: Every field a signed transfer must carry. Absence of any one is a refusal, not a default:
#: the whole point of the kind is that the number cannot exist without its signature.
PEER_TRANSFER_REQUIRED = (
    "resolved_kind",     # the schedule shape the peer measured: zero / per_lot / notional_bp
    "value",             # the peer's value, in the units that kind implies
    "from_account",      # which account the measurement was taken on
    "from_symbols",      # which instruments, named, non-empty
    "from_coverage",     # the source's own coverage class -- MEASURED, or say otherwise
    "authorized_by",     # who signed it. A person or an owner ratification, never a session
    "rationale",         # why these peers price this instrument
    "signed_utc",        # when
)

#: A peer transfer may resolve to any schedule shape the layer already prices, and nothing
#: else. `unknown` and `peer_transfer` are excluded so a transfer cannot chain or resolve to
#: a refusal.
PEER_TRANSFER_RESOLVABLE = ("zero", "per_lot", "notional_bp")

QUOTE_GEOMETRY_ROW_SCHEMA = "gtos.costs.quote_geometry_authority.v1"
QUOTE_GEOMETRY_APPROVED_RISK_ROW_SCHEMA = (
    "gtos.costs.quote_geometry_authority.v2"
)
APPROVED_PRE_SUBMISSION_RISK_DENOMINATOR_BASIS = (
    "approved_pre_submission_entry_stop_distance"
)
_QUOTE_GEOMETRY_BASE_FIELDS = frozenset({
    "schema",
    "trade_id",
    "account",
    "symbol",
    "entry_utc",
    "side",
    "gross_basis",
    "gross_includes_spread",
    "source_status",
    "bid_price",
    "ask_price",
    "entry_fill_price",
    "stop_price",
    "spread_price",
    "coverage",
})
_QUOTE_GEOMETRY_APPROVED_RISK_FIELDS = frozenset({
    "risk_denominator_basis",
    "approved_entry_price",
    "approved_stop_price",
    "approved_risk_distance",
})
_QUOTE_GEOMETRY_COVERAGE_FIELDS = {
    Coverage.MEASURED.value: frozenset(),
    Coverage.TRANSFERRED.value: frozenset({"transferred_from"}),
    Coverage.MODELLED.value: frozenset({"owner", "asof"}),
}


class SpreadAccounting(str, Enum):
    """Whether the gross return has already paid the bid/ask geometry."""

    EXPLICIT_COMPONENT = "explicit_component"
    QUOTE_GEOMETRY = "quote_geometry"


@dataclass(frozen=True)
class SpreadGeometryEvidence:
    """Locator for one hash-bound quote-geometry authority row.

    Values are deliberately not carried on this object.  The cost layer resolves the
    exact physical JSONL line, hashes the complete source bytes, then validates trade,
    account, profile symbol, time, side, gross basis, bid/ask, fill, stop and risk-
    denominator geometry.  A caller-created object containing plausible values
    therefore cannot turn an additional spread deduction into zero or silently rebase R.

    ``row_index`` is the zero-based physical line number in the JSONL source.
    """

    source_path: str | Path
    source_sha256: str
    row_index: int
    trade_id: str

    def __post_init__(self) -> None:
        if not str(self.source_path).strip():
            raise ValueError("geometry evidence source_path is required")
        digest = self.source_sha256.lower()
        if len(digest) != 64 or any(c not in "009abcdef" for c in digest):
            raise ValueError("geometry evidence source_sha256 must be a 64-character hex digest")
        if isinstance(self.row_index, bool) or not isinstance(self.row_index, int):
            raise TypeError("geometry evidence row_index must be an integer")
        if self.row_index < 0:
            raise ValueError("geometry evidence row_index must be nonnegative")
        if not isinstance(self.trade_id, str) or not self.trade_id.strip():
            raise ValueError("geometry evidence trade_id is required")
        if self.trade_id != self.trade_id.strip():
            raise ValueError("geometry evidence trade_id may not have surrounding whitespace")


@dataclass(frozen=True)
class VerifiedQuoteGeometryReceipt(SpreadGeometryEvidence):
    """One A1-resolved entry/exit quote pair; never an arbitrary path rescan."""

    source_authority_root_sha256: str
    exit_source: SpreadGeometryEvidence
    entry_row_sha256: str
    exit_row_sha256: str
    entry_utc: str
    entry_bid_price: float
    entry_ask_price: float
    exit_utc: str
    exit_bid_price: float
    exit_ask_price: float
    _resolver_token: object = field(repr=False, compare=False)

    def __post_init__(self) -> None:
        super().__post_init__()
        hashes = (
            self.source_authority_root_sha256,
            self.entry_row_sha256,
            self.exit_row_sha256,
        )
        if any(
            not isinstance(value, str)
            or len(value) != 64
            or any(character not in "009abcdef" for character in value)
            for value in hashes
        ):
            raise CostTruthError(
                "verified quote receipt needs lowercase SHA-256 bindings"
            )
        if (
            type(self.exit_source) is not SpreadGeometryEvidence
            or self.trade_id != self.exit_source.trade_id
        ):
            raise CostTruthError("verified quote entry/exit locators disagree")
        entry = _geometry_timestamp(self.entry_utc, "entry_utc")
        exit_ = _geometry_timestamp(self.exit_utc, "exit_utc")
        for prefix, bid_value, ask_value in (
            ("entry", self.entry_bid_price, self.entry_ask_price),
            ("exit", self.exit_bid_price, self.exit_ask_price),
        ):
            bid = _strict_nonnegative(bid_value, f"{prefix}_bid_price")
            ask = _strict_nonnegative(ask_value, f"{prefix}_ask_price")
            if bid <= 0 or ask <= 0 or ask < bid:
                raise CostTruthError(f"verified quote {prefix} bid/ask is invalid")
        if exit_ < entry:
            raise CostTruthError("verified quote exit precedes entry")
        if type(self._resolver_token) is not object:
            raise CostTruthError("verified quote receipt resolver token is invalid")


class CostTruthError(RuntimeError):
    """Raised rather than guessing. Absence of a cost is never zero."""


@dataclass(frozen=True)
class CostBreakdown:
    """The four components plus their total. Every field is a `Measure`."""

    symbol: str
    account: str
    commission_r: Measure
    swap_r: Measure
    spread_r: Measure
    slippage_r: Measure
    total_r: Measure
    detail: dict
    attributed_spread_r: Measure | None = None

    def as_dict(self) -> dict:
        return {
            "symbol": self.symbol,
            "account": self.account,
            "commission_r": self.commission_r.as_dict(),
            "swap_r": self.swap_r.as_dict(),
            "spread_r": self.spread_r.as_dict(),
            "slippage_r": self.slippage_r.as_dict(),
            "total_r": self.total_r.as_dict(),
            "attributed_spread_r": (
                self.attributed_spread_r.as_dict() if self.attributed_spread_r else None
            ),
            "detail": self.detail,
        }


class BrokerTrueCosts:
    """Loaded ``BROKER_TRUE_COSTS_V1.json`` with instrument lookup."""

    def __init__(
        self,
        doc: dict,
        source: Path | None = None,
        *,
        artifact_sha256: str | None = None,
    ):
        self.doc = doc
        self.source = source
        self.artifact_sha256 = artifact_sha256
        self.version = doc.get("version")
        self.schema = doc.get("schema")

    @property
    def accounts(self) -> list[str]:
        return sorted(self.doc.get("accounts", {}))

    def resolve_instrument(self, account: str, symbol: str) -> tuple[str, dict]:
        acct = self.doc.get("accounts", {}).get(account)
        if acct is None:
            raise CostTruthError(
                f"no broker truth for account {account!r}. Known: {self.accounts}. "
                "Broker truth exists for exactly two live accounts."
            )
        instruments = acct["instruments"]
        resolved = resolve_account_symbol(account, symbol, instruments)
        if resolved is None:
            raise CostTruthError(
                f"no broker truth for {symbol!r} on {account}. It is not in that broker's "
                f"quotable universe ({len(acct['instruments'])} symbols). A missing "
                "instrument is unpriced, not free."
            )
        return resolved, instruments[resolved]

    def instrument(self, account: str, symbol: str) -> dict:
        return self.resolve_instrument(account, symbol)[1]

    def symbols(self, account: str) -> list[str]:
        return sorted(self.doc["accounts"][account]["instruments"])


def _is_tracked_by_git(path: Path) -> bool:
    """True when git tracks `path`. Called only when the file is ABSENT, where it means
    "committed but not materialised by this worktree's sparse-checkout".

    Sparse-checkout lies: a committed file can be absent with `git status` clean. Distinguishing
    that from a genuinely missing artifact is the difference between a one-second fix and a
    re-capture. Never raises -- a git that is missing, slow, or unhappy just means "cannot tell",
    and the caller falls back to the generic message.
    """
    try:
        import subprocess

        target = path if path.is_absolute() else (Path.cwd() / path)
        # The nearest ancestor that EXISTS. `path.parent` is usually the very directory sparse
        # checkout left out, so running git there fails and the check silently answers "cannot
        # tell" -- which is how the first version of this function returned False for the exact
        # artifact it was written to recognise.
        cwd = next((p for p in target.parents if p.is_dir()), Path.cwd())
        out = subprocess.run(
            ["git", "ls-files", "--error-unmatch", "--", str(target)],
            cwd=str(cwd), capture_output=True, text=True, timeout=10,
        )
        return out.returncode == 0 and bool(out.stdout.strip())
    except Exception:  # noqa: BLE001
        return False


@lru_cache(maxsize=4)
def _parse_broker_truth_cached(
    path_str: str, artifact_sha256: str, data: bytes
) -> BrokerTrueCosts:
    try:
        doc = json.loads(data)
    except (json.JSONDecodeError, UnicodeDecodeError) as exc:
        raise CostTruthError(f"broker truth artifact is not valid JSON at {path_str}") from exc
    return BrokerTrueCosts(
        doc,
        source=Path(path_str),
        artifact_sha256=artifact_sha256,
    )


def load_broker_true_costs(path: Path | str | None = None) -> BrokerTrueCosts:
    path = Path(path or DEFAULT_ARTIFACT)
    if not path.is_file():
        # Session BD (B2095). This message used to say "Build it with
        # `scripts/build_broker_true_costs.py`" unconditionally, and the artifact is COMMITTED --
        # so on a fresh worktree it told three sessions in a row (AR B1473, AS handoff 6, BD) to
        # re-run a broker-truth capture when the real answer was one `git sparse-checkout add`.
        # AS: *"the fix is one line in the profile and it saves the next worktree a failed run that
        # reads like an expensive measurement."* The line landed in
        # `scripts/gtos_hydrate_test_data.py`; what did not land is this message, which is what a
        # session actually reads at the moment it is stuck -- after a ~25 s substrate build.
        if _is_tracked_by_git(path):
            raise CostTruthError(
                f"broker truth artifact {path} is COMMITTED but not checked out -- this worktree's "
                f"sparse-checkout has not materialised it. Do NOT re-run the broker-truth capture; "
                f"the bytes are in git. Hydrate with `python3 scripts/gtos_hydrate_test_data.py` "
                f"(preferred, it carries the whole known set) or "
                f"`git sparse-checkout add {path.parent}`."
            )
        raise CostTruthError(
            f"broker truth artifact not found at {path}, and git does not track it. Build it with "
            "`python3 scripts/build_broker_true_costs.py -o <path>`. If you expected it to be "
            "committed, check `git ls-files` -- a sparse-excluded file reports differently and "
            "this message would have said so."
        )
    try:
        current = read_current_file_bytes(path, label="broker truth artifact")
    except CostInputAuthorityError as exc:
        raise CostTruthError(str(exc)) from exc
    return _parse_broker_truth_cached(
        str(current.path), current.sha256, current.data
    )


# --------------------------------------------------------------------------- helpers


def _usd_per_price_unit_per_lot(rec: dict) -> float:
    upu = rec.get("usd_per_price_unit_per_lot")
    if not upu:
        raise CostTruthError(
            f"{rec.get('broker_path')} has no usable trade_tick_value/trade_tick_size, so "
            "no cash-to-R conversion is possible for it."
        )
    return float(upu)


def _strict_nonnegative(value: float, name: str) -> float:
    """Finite, non-boolean cost component validation before exact summation."""
    if isinstance(value, bool):
        raise CostTruthError(f"{name} must be a finite nonnegative number, not bool")
    try:
        out = float(value)
    except (TypeError, ValueError):
        raise CostTruthError(f"{name} must be a finite nonnegative number, got {value!r}") from None
    if not math.isfinite(out) or out < 0:
        raise CostTruthError(f"{name} must be finite and nonnegative, got {value!r}")
    return out


def _same_geometry_price(left: float, right: float) -> bool:
    """Tight equality for independently serialized quote prices."""
    return math.isclose(
        float(left),
        float(right),
        rel_tol=1e-12,
        abs_tol=1e-12,
    )


def _geometry_timestamp(value: object, field: str) -> datetime:
    if not isinstance(value, str) or not value.strip():
        raise CostTruthError(f"geometry authority row needs non-empty {field}")
    try:
        parsed = datetime.fromisoformat(value.strip().replace("Z", "+00:00"))
    except ValueError:
        raise CostTruthError(
            f"geometry authority row {field} is not an ISO-8601 timestamp: {value!r}"
        ) from None
    if parsed.tzinfo is None:
        raise CostTruthError(f"geometry authority row {field} must be timezone-aware")
    return parsed.astimezone(timezone.utc)


def _validate_geometry_row_shape(row: dict) -> str:
    """Return the exact closed geometry schema or refuse mixed authority fields."""

    schema = row.get("schema")
    if schema == QUOTE_GEOMETRY_ROW_SCHEMA:
        required = _QUOTE_GEOMETRY_BASE_FIELDS
    elif schema == QUOTE_GEOMETRY_APPROVED_RISK_ROW_SCHEMA:
        required = (
            _QUOTE_GEOMETRY_BASE_FIELDS | _QUOTE_GEOMETRY_APPROVED_RISK_FIELDS
        )
    else:
        raise CostTruthError(
            f"unsupported quote-geometry row schema {schema!r}; expected "
            f"{QUOTE_GEOMETRY_ROW_SCHEMA!r} or "
            f"{QUOTE_GEOMETRY_APPROVED_RISK_ROW_SCHEMA!r}"
        )
    coverage_fields = _QUOTE_GEOMETRY_COVERAGE_FIELDS.get(
        row.get("coverage"), frozenset()
    )
    expected = required | coverage_fields
    missing = sorted(expected - row.keys())
    unknown = sorted(row.keys() - expected)
    if missing or unknown:
        parts = []
        if missing:
            parts.append(f"missing={missing}")
        if unknown:
            parts.append(f"unknown_or_mixed={unknown}")
        raise CostTruthError(
            f"quote-geometry row does not match closed schema {schema!r}: "
            + "; ".join(parts)
        )
    return schema


def _require_active_quote_resolver(
    receipt: VerifiedQuoteGeometryReceipt,
    resolver: object | None,
) -> None:
    """Require the run-local A1 resolver that issued this exact receipt."""

    # Lazy import avoids an import cycle: A1 owns the resolver and imports this
    # module's receipt type, while the cost layer checks the one concrete issuer
    # only when that alternate path is actually used.
    from src.research_infra.lane_rematerialization import LaneQuoteSourceResolver

    if type(resolver) is not LaneQuoteSourceResolver:
        raise CostTruthError("active A1 quote resolver is required")
    validator = getattr(
        resolver,
        "_validate_verified_quote_geometry_receipt_for_cost",
        None,
    )
    if not callable(validator):
        raise CostTruthError("active A1 quote resolver is required")
    try:
        valid = validator(receipt)
    except Exception as exc:
        raise CostTruthError(f"A1 quote resolver rejected receipt: {exc}") from exc
    if valid is not True:
        raise CostTruthError("A1 quote resolver rejected receipt")


def _resolve_geometry_authority(
    evidence: SpreadGeometryEvidence,
    *,
    account: str,
    resolved_symbol: str,
    entry_utc: datetime,
    entry_price: float | None,
    side: str,
    sl_distance_price: float,
    verified_quote_geometry_resolver: object | None = None,
) -> tuple[float, Coverage, str, dict, dict]:
    """Resolve and validate one physical quote-geometry source row.

    Returns ``(observed_spread_price, coverage, provenance, measure_kwargs,
    detail)``.  Every field that licenses exactly-once spread accounting is
    re-derived from the source bytes; the locator itself carries no price or
    accounting claim.
    """
    if type(evidence) is not VerifiedQuoteGeometryReceipt:
        raw_path = Path(evidence.source_path)
        path = raw_path if raw_path.is_absolute() else REPO / raw_path
        try:
            source_bytes = path.read_bytes()
        except OSError as exc:
            raise CostTruthError(
                f"quote-geometry source {path} is not resolvable: {exc}; NOT_EVALUABLE"
            ) from exc
        actual_sha256 = hashlib.sha256(source_bytes).hexdigest()
        if actual_sha256 != evidence.source_sha256.lower():
            raise CostTruthError(
                f"quote-geometry source hash mismatch for {path}: evidence binds "
                f"{evidence.source_sha256.lower()}, actual bytes are {actual_sha256}; "
                "NOT_EVALUABLE"
            )
        try:
            lines = source_bytes.decode("utf-8").splitlines()
        except UnicodeDecodeError as exc:
            raise CostTruthError(f"quote-geometry source {path} is not UTF-8 JSONL") from exc
        if evidence.row_index >= len(lines):
            raise CostTruthError(
                f"quote-geometry row_index {evidence.row_index} is outside {path} "
                f"({len(lines)} physical lines); NOT_EVALUABLE"
            )
        try:
            row = json.loads(lines[evidence.row_index])
        except json.JSONDecodeError as exc:
            raise CostTruthError(
                f"quote-geometry line {evidence.row_index} in {path} is not JSON"
            ) from exc
        provenance = (
            f"{path} sha256={actual_sha256} row_index={evidence.row_index} "
            f"trade_id={evidence.trade_id}"
        )
        authority_detail = {
            "source_path": str(path),
            "source_sha256": actual_sha256,
            "row_index": evidence.row_index,
        }
    else:
        receipt = evidence
        _require_active_quote_resolver(
            receipt,
            verified_quote_geometry_resolver,
        )
        raise CostTruthError("approved_order_geometry_authority_missing")
    if not isinstance(row, dict):
        raise CostTruthError("quote-geometry authority row must be a JSON object")
    geometry_schema = _validate_geometry_row_shape(row)
    if row.get("trade_id") != evidence.trade_id:
        raise CostTruthError(
            f"quote-geometry row trade_id {row.get('trade_id')!r} does not match "
            f"locator {evidence.trade_id!r}"
        )
    if row.get("account") != account:
        raise CostTruthError(
            f"quote-geometry row account {row.get('account')!r} does not match {account!r}"
        )
    row_symbol = row.get("symbol")
    if not isinstance(row_symbol, str) or resolve_account_symbol(
        account, row_symbol, {resolved_symbol}
    ) != resolved_symbol:
        raise CostTruthError(
            f"quote-geometry row symbol {row_symbol!r} is not the exact profile-declared "
            f"identity for {account} {resolved_symbol!r}"
        )
    if entry_utc.tzinfo is None:
        raise CostTruthError(
            "quote_geometry requires timezone-aware entry_utc to bind observed spread time"
        )
    observed_utc = _geometry_timestamp(row.get("entry_utc"), "entry_utc")
    if observed_utc != entry_utc.astimezone(timezone.utc):
        raise CostTruthError(
            f"quote-geometry row time {observed_utc.isoformat()} does not match "
            f"entry_utc {entry_utc.isoformat()}"
        )
    if row.get("gross_basis") != "fill_anchored_quote_geometry":
        raise CostTruthError(
            "quote-geometry row gross_basis must be 'fill_anchored_quote_geometry'"
        )
    if row.get("gross_includes_spread") is not True:
        raise CostTruthError(
            "quote-geometry row must explicitly state gross_includes_spread=true"
        )
    if row.get("source_status") != "captured":
        raise CostTruthError(
            "quote-geometry row source_status must be exactly 'captured'"
        )

    bid = _strict_nonnegative(row.get("bid_price"), "geometry bid_price")
    ask = _strict_nonnegative(row.get("ask_price"), "geometry ask_price")
    fill = _strict_nonnegative(row.get("entry_fill_price"), "geometry entry_fill_price")
    stop = _strict_nonnegative(row.get("stop_price"), "geometry stop_price")
    reported_spread = _strict_nonnegative(
        row.get("spread_price"), "geometry spread_price"
    )
    if bid <= 0 or ask <= 0 or fill <= 0 or stop <= 0:
        raise CostTruthError("quote-geometry bid/ask/fill/stop prices must be positive")
    if ask < bid:
        raise CostTruthError(f"quote-geometry ask_price {ask} is below bid_price {bid}")
    physical_spread = ask - bid
    if not _same_geometry_price(reported_spread, physical_spread):
        raise CostTruthError(
            f"quote-geometry spread_price {reported_spread} does not reconcile to "
            f"ask-bid {physical_spread}"
        )
    normalized_side = str(side).upper()
    row_side = str(row.get("side") or "").upper()
    long_side = normalized_side in {"LONG", "BUY"}
    short_side = normalized_side in {"SHORT", "SELL"}
    if not (long_side or short_side):
        raise CostTruthError(f"trade side {side!r} is not LONG/BUY/SHORT/SELL")
    if row_side not in ({"LONG", "BUY"} if long_side else {"SHORT", "SELL"}):
        raise CostTruthError(
            f"quote-geometry row side {row.get('side')!r} does not match trade side {side!r}"
        )
    side_quote = ask if long_side else bid
    if not _same_geometry_price(fill, side_quote):
        raise CostTruthError(
            f"quote-geometry entry fill {fill} does not equal the transacted "
            f"{'ask' if long_side else 'bid'} {side_quote}"
        )
    if entry_price is None or not _same_geometry_price(float(entry_price), fill):
        raise CostTruthError(
            f"quote-geometry entry fill {fill} does not match caller entry_price "
            f"{entry_price!r}"
        )
    if (long_side and stop >= fill) or (short_side and stop <= fill):
        raise CostTruthError(
            f"quote-geometry stop {stop} is on the wrong side of entry fill {fill}"
        )
    row_stop_distance = abs(fill - stop)
    risk_denominator_basis = row.get("risk_denominator_basis")
    risk_basis_detail: dict = {}
    if geometry_schema == QUOTE_GEOMETRY_ROW_SCHEMA:
        # Legacy v1 rows define R directly from actual fill-to-stop geometry.
        if not _same_geometry_price(row_stop_distance, sl_distance_price):
            raise CostTruthError(
                f"quote-geometry fill/stop distance {row_stop_distance} does not match "
                f"sl_distance_price {sl_distance_price}"
            )
    else:
        if risk_denominator_basis != (
            APPROVED_PRE_SUBMISSION_RISK_DENOMINATOR_BASIS
        ):
            raise CostTruthError(
                "unsupported risk_denominator_basis "
                f"{risk_denominator_basis!r}; expected "
                f"{APPROVED_PRE_SUBMISSION_RISK_DENOMINATOR_BASIS!r}"
            )
        approved_entry = _strict_nonnegative(
            row.get("approved_entry_price"), "geometry approved_entry_price"
        )
        approved_stop = _strict_nonnegative(
            row.get("approved_stop_price"), "geometry approved_stop_price"
        )
        approved_risk = _strict_nonnegative(
            row.get("approved_risk_distance"), "geometry approved_risk_distance"
        )
        if approved_entry <= 0 or approved_stop <= 0 or approved_risk <= 0:
            raise CostTruthError(
                "quote-geometry approved entry/stop/risk prices must be positive"
            )
        if (long_side and approved_stop >= approved_entry) or (
            short_side and approved_stop <= approved_entry
        ):
            raise CostTruthError(
                f"quote-geometry approved stop {approved_stop} is on the wrong side "
                f"of approved entry {approved_entry}"
            )
        approved_geometry_distance = abs(approved_entry - approved_stop)
        if not _same_geometry_price(approved_geometry_distance, approved_risk):
            raise CostTruthError(
                f"quote-geometry approved entry/stop distance "
                f"{approved_geometry_distance} does not match "
                f"approved_risk_distance {approved_risk}"
            )
        if not _same_geometry_price(approved_risk, sl_distance_price):
            raise CostTruthError(
                f"quote-geometry approved_risk_distance {approved_risk} does not "
                f"match sl_distance_price {sl_distance_price}"
            )
        if not _same_geometry_price(approved_stop, stop):
            raise CostTruthError(
                f"quote-geometry approved_stop_price {approved_stop} does not match "
                f"actual stop_price {stop}"
            )
        risk_basis_detail = {
            "authority_schema": geometry_schema,
            "risk_denominator_basis": risk_denominator_basis,
            "approved_entry_price": approved_entry,
            "approved_stop_price": approved_stop,
            "approved_risk_distance": approved_risk,
            "actual_fill_stop_distance": row_stop_distance,
        }

    try:
        coverage = Coverage(row.get("coverage"))
    except ValueError:
        raise CostTruthError(
            f"quote-geometry row coverage {row.get('coverage')!r} is invalid"
        ) from None
    measure_kwargs: dict = {}
    if coverage is Coverage.TRANSFERRED:
        transferred_from = row.get("transferred_from")
        if not isinstance(transferred_from, str) or not transferred_from.strip():
            raise CostTruthError(
                "transferred quote-geometry authority must name transferred_from"
            )
        measure_kwargs["transferred_from"] = transferred_from
    elif coverage is Coverage.MODELLED:
        owner, asof = row.get("owner"), row.get("asof")
        if not all(isinstance(v, str) and v.strip() for v in (owner, asof)):
            raise CostTruthError(
                "modelled quote-geometry authority must carry owner and asof"
            )
        measure_kwargs.update(owner=owner, asof=asof)

    detail = {
        **authority_detail,
        "trade_id": evidence.trade_id,
        "entry_utc": observed_utc.isoformat(),
        "side": row_side,
        "bid_price": bid,
        "ask_price": ask,
        "entry_fill_price": fill,
        "stop_price": stop,
        "reported_spread_price": reported_spread,
        "gross_basis": row["gross_basis"],
        "gross_includes_spread": True,
        "coverage": coverage.value,
        **risk_basis_detail,
    }
    provenance = f"{provenance}; observed_utc={observed_utc.isoformat()}"
    return physical_spread, coverage, provenance, measure_kwargs, detail


def component_sum_r(
    spread_r: float,
    expected_slippage_r: float,
    swap_cost_r: float,
    commission_r: float,
) -> float:
    """FD-authoritative component identity, including left-to-right float order.

    Complete rows must remain exactly ``spread + slippage + swap + commission``.
    ``math.fsum`` and algebraic reordering are intentionally not used because they
    change the serialized float on known FD rows.
    """
    spread = _strict_nonnegative(spread_r, "spread_r")
    slippage = _strict_nonnegative(expected_slippage_r, "expected_slippage_r")
    swap = _strict_nonnegative(swap_cost_r, "swap_cost_r")
    commission = _strict_nonnegative(commission_r, "commission_r")
    return spread + slippage + swap + commission


def elapsed_holding_hours(entry_utc: datetime, exit_utc: datetime) -> float:
    """Wall-clock elapsed hold; never infer it from the count of trading bars."""
    if entry_utc.tzinfo is None or exit_utc.tzinfo is None:
        raise CostTruthError("entry_utc and exit_utc must be timezone-aware")
    seconds = (exit_utc - entry_utc).total_seconds()
    if seconds < 0:
        raise CostTruthError(f"exit_utc {exit_utc} precedes entry_utc {entry_utc}")
    return seconds / 3600.0


def _coverage_of(block: dict) -> Coverage:
    return Coverage(block["coverage"])


def _check_peer_transfer_coverage(block: dict) -> None:
    """A signed transfer is never MEASURED. Refuse before the value is ever read.

    This is the anti-laundering guard and it is a separate function so it can be called from
    both the arithmetic path and the `Measure` construction path: a block that resolves fine
    and then reports `MEASURED` would put a transferred number into the class the whole
    coverage system exists to keep clean (`coverage.py:13-17`).
    """
    cov = block.get("coverage")
    if cov != Coverage.TRANSFERRED.value:
        raise CostTruthError(
            f"a {PEER_TRANSFER!r} commission must declare coverage TRANSFERRED, got "
            f"{cov!r}. A transfer is by definition not an observation on this instrument; "
            "recording one as MEASURED is the F38 defect wearing a signature."
        )


def _resolve_peer_transfer(block: dict) -> tuple[dict, dict]:
    """Validate a signed peer transfer and return (resolved_block, signature_detail).

    The resolved block is the same block with `kind`/`value` replaced by what the peer
    measured, so the arithmetic below is shared rather than duplicated -- a second copy of
    the notional-bp formula is a second place for it to be wrong.
    """
    _check_peer_transfer_coverage(block)
    t = block.get("transfer")
    if not isinstance(t, dict):
        raise CostTruthError(
            f"a {PEER_TRANSFER!r} commission needs a `transfer` block carrying "
            f"{list(PEER_TRANSFER_REQUIRED)}; got {type(t).__name__}."
        )
    missing = [k for k in PEER_TRANSFER_REQUIRED
               if t.get(k) is None or (isinstance(t[k], str) and not t[k].strip())]
    if missing:
        raise CostTruthError(
            f"signed peer transfer is missing {missing}. Every field is required: a "
            "transfer without a signer, a date, named source instruments and a stated "
            "rationale is an unattributable number, which is what this kind exists to "
            "prevent."
        )
    syms = t["from_symbols"]
    if not (isinstance(syms, (list, tuple)) and syms and all(
            isinstance(s, str) and s.strip() for s in syms)):
        raise CostTruthError(
            f"`from_symbols` must be a non-empty list of instrument names; got {syms!r}."
        )
    rk = t["resolved_kind"]
    if rk not in PEER_TRANSFER_RESOLVABLE:
        raise CostTruthError(
            f"`resolved_kind` {rk!r} is not one this layer prices "
            f"{PEER_TRANSFER_RESOLVABLE}. A transfer may not resolve to 'unknown' (that is "
            f"a refusal, not a schedule) nor to {PEER_TRANSFER!r} (transfers do not chain)."
        )
    # `from_coverage` must BECOME a Coverage and travel through `weakest()`, not merely be
    # present. Found by an adversarial pass over this very mechanism (Session AP): the first
    # version presence-checked the field and then read the emitted coverage off the BLOCK, so a
    # transfer declaring `from_coverage: MODELLED` (strength 2) emitted TRANSFERRED (strength 1)
    # -- a coverage UPGRADE, the exact inverse of `coverage.weakest`'s "class travels into every
    # result computed from it" rule -- and `from_coverage: "VIBES"` priced. Transferring from a
    # modelled peer is legitimate; recording the result as better-grounded than its source is
    # not.
    try:
        src_cov = Coverage(str(t["from_coverage"]).strip().upper())
    except ValueError:
        raise CostTruthError(
            f"`from_coverage` {t['from_coverage']!r} is not a coverage class; expected one of "
            f"{[c.value for c in Coverage]}. A transfer whose source's grounding cannot be "
            "read cannot have its own grounding computed, and defaulting it would be the "
            "upgrade this check exists to stop."
        ) from None
    emitted = weakest(Coverage.TRANSFERRED, src_cov)
    resolved = {**block, "kind": rk, "value": t["value"], "coverage": emitted.value}
    if emitted is Coverage.MODELLED:
        # A MODELLED Measure cannot be built without owner+asof (`coverage.py:133-137`), and
        # the signature already carries both under different names.
        resolved.setdefault("owner", t["authorized_by"])
        resolved.setdefault("asof", t["signed_utc"])
    detail = {k: t[k] for k in PEER_TRANSFER_REQUIRED}
    detail["emitted_coverage"] = emitted.value
    detail["emitted_coverage_basis"] = (
        f"weakest(TRANSFERRED, from_coverage={src_cov.value}) -- a transfer is never stronger "
        f"than its source")
    return resolved, detail


def _measure_from(block: dict, value: float, unit: str, extra_prov: str = "") -> Measure:
    if block.get("kind") == PEER_TRANSFER:
        # A `peer_transfer` is a COMMISSION construct and nothing else. Also found by that
        # adversarial pass: `_resolve_peer_transfer` was reachable only from
        # `commission_usd_per_lot`, so a `kind: "peer_transfer"` block in the spread, swap or
        # slippage slot carried NONE of the eight required fields and priced end to end -- the
        # validation was a property of one call site rather than of the kind. Refusing here
        # makes it a property of the kind: the commission path replaces `kind` with the
        # resolved schedule before this function ever sees it, so a `peer_transfer` block
        # arriving here has bypassed `_resolve_peer_transfer` by construction.
        raise CostTruthError(
            f"a {PEER_TRANSFER!r} block reached the Measure layer unresolved. This kind is "
            "valid in the `commission` slot only, where `_resolve_peer_transfer` validates "
            "its signature and rewrites `kind` to the schedule the peer measured. In any "
            "other slot it would be an unvalidated, unsigned transfer wearing a signed "
            "kind's name."
        )
    cov = _coverage_of(block)
    prov = block.get("provenance", "")
    if extra_prov:
        prov = f"{prov}; {extra_prov}" if prov else extra_prov
    kwargs = {}
    if cov is Coverage.TRANSFERRED:
        src = block.get("transferred_from")
        if not (isinstance(src, str) and src.strip()):
            # Struck 2026-07-30 (Session AP): this used to read
            # `block.get("transferred_from") or "unnamed class peer"`. That default is the
            # laundering hole `Measure.__post_init__` exists to close, reopened one layer
            # up: `Measure` refuses a TRANSFERRED value with no named source, and this line
            # handed it a name that names nothing. Every TRANSFERRED block in every shipped
            # artifact carries a real `transferred_from` -- 353 of 353 in V1 and V1_1, 355 of
            # 355 in V1_2 -- so no data relied on the default; only a future unsigned transfer
            # could have. (The 353 figure alone was Session AP's and it excluded the artifact
            # AP itself shipped; an adversarial pass caught the omission and the corrected
            # count is stronger, not weaker.)
            raise CostTruthError(
                "a TRANSFERRED cost block must name `transferred_from`; got "
                f"{src!r}. 'the band is wider and says from what' -- an unnamed peer is "
                "not a source, and substituting one is F38 with better manners."
            )
        kwargs["transferred_from"] = src
        kwargs["band_mult"] = _CLASS_TRANSFER_BAND
        kwargs["band_provenance"] = _CLASS_TRANSFER_BAND_PROVENANCE
    if cov is Coverage.MODELLED:
        kwargs["owner"] = block.get("owner") or "Session J (Stage 1.1)"
        kwargs["asof"] = block.get("asof") or "2026-07-27"
    return Measure(value=value, coverage=cov, provenance=prov, unit=unit, n=block.get("n_round_turns"), **kwargs)


def commission_usd_per_lot(rec: dict, entry_price: float | None) -> tuple[float, dict]:
    """Round-turn commission in account currency per lot, from the fitted schedule."""
    block = rec["commission"]
    kind = block.get("kind")
    detail = {"kind": kind}
    if kind == PEER_TRANSFER:
        resolved, tdetail = _resolve_peer_transfer(block)
        usd, inner = commission_usd_per_lot({**rec, "commission": resolved}, entry_price)
        return usd, {**detail, **inner, "kind": kind, "resolved_kind": resolved["kind"],
                     "peer_transfer": tdetail}
    if kind == "zero":
        return 0.0, detail
    if kind == "per_lot":
        return float(block["value"]), detail
    if kind == "notional_bp":
        cs = (rec.get("spec") or {}).get("trade_contract_size")
        px = entry_price
        if px is None:
            spread = rec.get("spread_price") or {}
            px = spread.get("mid_price_median")
            detail["price_source"] = "measured median mid (entry_price not supplied)"
        else:
            detail["price_source"] = "caller entry_price"
        if not cs or not px:
            raise CostTruthError(
                f"notional-bp commission needs trade_contract_size and a price; have "
                f"contract={cs!r} price={px!r}."
            )
        detail["contract_size"] = cs
        detail["price"] = px
        return float(block["value"]) / 1e4 * float(cs) * float(px), detail
    raise CostTruthError(
        f"commission schedule for this instrument is {kind!r} -- it is UNKNOWN, not zero. "
        "Charging zero here is exactly the F38 defect."
    )


def _mt5_dow(day: datetime) -> int:
    """MT5 ENUM_DAY_OF_WEEK: Sunday=0 .. Saturday=6. Python weekday(): Monday=0."""
    return (day.weekday() + 1) % 7


def rollover_nights(
    entry_utc: datetime,
    holding_hours: float,
    *,
    server: str,
    rollover3days_weekday: int | None,
) -> tuple[float, dict]:
    """Count swap-charged nights over the hold, on the broker's own wall clock.

    A night is charged at each broker-wall midnight crossed. Saturday and Sunday
    midnights are not charged -- the weekend is collected on the triple-swap weekday
    (`swap_rollover3days`, MT5 weekday numbering), which counts as three.
    """
    rule = resolve_rule(server)
    start = utc_to_broker_naive(entry_utc, rule)
    end = utc_to_broker_naive(entry_utc + timedelta(hours=float(holding_hours)), rule)
    nights = 0.0
    crossed: list[str] = []
    day = (start + timedelta(days=1)).replace(hour=0, minute=0, second=0, microsecond=0)
    while day <= end:
        dow = _mt5_dow(day)
        if dow in (0, 6):  # Sunday / Saturday: market shut, no separate charge
            weight = 0.0
        elif rollover3days_weekday is not None and dow == int(rollover3days_weekday):
            weight = 3.0
        else:
            weight = 1.0
        if weight:
            crossed.append(f"{day.date().isoformat()}x{weight:g}")
        nights += weight
        day += timedelta(days=1)
    return nights, {"nights_charged": nights, "crossings": crossed, "basis": "broker_wall_midnight"}


def swap_price_drag_per_night(
    rec: dict,
    side: str,
    entry_price: float | None,
    *,
    credit_favourable: bool = False,
) -> tuple[float, dict]:
    """Swap for one night, in price units. Positive = a cost.

    By default this is ADVERSE swap only: a swap the broker PAYS returns 0.0. That is a
    modelling choice, not a measurement, and it is the research half of the B9 defect -- the
    live counterpart is `broker_net_cost_engine._swap_cost_packet`'s `elif swap >= 0` branch.
    `detail["credit_price_per_night"]` now always reports what the clamp discards (>= 0), so the
    number is visible to every caller without any of them changing behaviour.

    `credit_favourable=True` returns the signed value instead -- NEGATIVE on a favourable side.
    Opt-in, because a negative cost term propagates into admission arithmetic; see
    `B9_CARRY_AS_ALPHA_V1.md`.
    """
    spec = rec.get("spec") or {}
    swap_field = "swap_long" if side.upper() in ("LONG", "BUY") else "swap_short"
    raw = spec.get(swap_field)
    mode = spec.get("swap_mode")
    detail = {"swap_field": swap_field, "swap_raw": raw, "swap_mode": mode}
    if raw is None or mode is None:
        raise CostTruthError(f"swap unavailable: swap_mode={mode!r} {swap_field}={raw!r}")

    signed = float(raw)
    favourable = signed >= 0
    # A favourable side must never be made to RAISE where it used to return 0.0 silently: the
    # default path stays byte-for-byte what it was, and an unconvertible credit is reported as
    # `credit_price_per_night: None` rather than an exception. Ask for the credit
    # (`credit_favourable=True`) and the same gap becomes fatal, because then it is the answer.
    def _convert() -> float:
        magnitude = abs(signed)
        if int(mode) == 1:  # points
            point = spec.get("point")
            if not point:
                raise CostTruthError("swap mode 1 needs `point`")
            return magnitude * float(point)
        if int(mode) in (5, 6):  # annual interest percentage of price
            px = entry_price or (rec.get("spread_price") or {}).get("mid_price_median")
            if not px:
                raise CostTruthError("swap modes 5/6 need a price")
            detail["price"] = px
            detail["days_per_year"] = 360.0
            return float(px) * (magnitude / 100.0) / 360.0
        raise CostTruthError(
            f"swap_mode {mode} is currency-denominated; it needs post-sizing volume "
            "conversion and is a source gap here (same limitation as "
            "broker_net_cost_engine._swap_cost_packet)."
        )

    if favourable:
        detail["note"] = "favourable or zero swap -> no cost"
        if credit_favourable:
            credit = _convert()
            detail["credit_price_per_night"] = credit
            return -credit, detail
        try:
            detail["credit_price_per_night"] = _convert()
        except CostTruthError as exc:
            detail["credit_price_per_night"] = None
            detail["credit_source_gap"] = str(exc)
        return 0.0, detail

    detail["credit_price_per_night"] = 0.0
    return _convert(), detail


# --------------------------------------------------------------------------- the API


def cost_r(
    symbol: str,
    account: str,
    holding_hours: float,
    *,
    sl_distance_price: float,
    entry_price: float | None = None,
    side: str = "LONG",
    entry_utc: datetime | None = None,
    spread_percentile: str = "p50",
    spread_session: str | None = None,
    spread_band: str | None = None,
    spread_vol_state: int | None = None,
    spread_composition: str | None = None,
    spread_era_exponent: float | None = None,
    spread_require_decidable: bool = False,
    spread_accounting: SpreadAccounting | str = SpreadAccounting.EXPLICIT_COMPONENT,
    geometry_spread_price: float | None = None,
    geometry_spread_evidence: SpreadGeometryEvidence | None = None,
    verified_quote_geometry_resolver: object | None = None,
    spread_model: "SpreadModel | None" = None,
    historical_fx: "HistoricalFxRates | None" = None,
    slippage_model: "SlippageModel | None" = None,
    costs: BrokerTrueCosts | None = None,
) -> CostBreakdown:
    """Round-trip cost of one trade, in R, with a coverage class on every term.

    Parameters
    ----------
    sl_distance_price:
        R denominator in price units.  Legacy quote-geometry rows require this to equal
        ``abs(actual fill - stop)``.  A row explicitly bound to
        ``approved_pre_submission_entry_stop_distance`` instead validates it against the
        approved entry/stop geometry, so favorable post-submission fill movement does not
        silently rebase R.
    holding_hours:
        Expected hold. Used for swap only.
    entry_utc:
        Entry instant. When given, swap rollovers are counted exactly on the broker's
        wall clock and the swap term stays at its source coverage; when omitted the swap
        term degrades to [MODELLED].
    spread_percentile:
        Which measured percentile of the quoted spread to charge (`p50` default,
        `p95` for a stress read).
    spread_session:
        Optional `asia` / `london` / `ny` to use that session's measured spread.
    spread_band:
        ``"low"`` / ``"mid"`` / ``"high"``. **Opt-in, and it changes two things.**

        Left at ``None`` this function behaves exactly as before: a flat 37-day tick
        snapshot charged to every instant, and a hard refusal for the 137 FTMO symbols
        that snapshot never covered.

        Set, and spread comes from ``spread_model_v1`` instead: the same tick anchor
        scaled by that quarter's **measured era ratio** and by an hour-of-week /
        volatility multiplier. That does two jobs at once. It sizes the look-ahead that
        every deep-history number in this estate carries -- EURUSD's spread in 2000-2003
        was **50x** what the snapshot charges, XAUUSD's in 2020-2024 was **0.18x**, so
        the bias is first-order and it does not even have a consistent sign. And it turns
        "no measured spread" from a refusal into a band: thirteen more symbols become
        priceable because the bar archive recorded their spread when the tick archive
        never covered them.

        A sleeve that survives at ``high`` is robust to the look-ahead. One that flips
        between bands has that fact for its repair row instead of a silently optimistic
        pass.
    spread_vol_state:
        Optional volatility-state quintile (0-4) for the intraweek term. Point-in-time
        trailing state by default -- see `spread_model.vol_kind`.
    spread_require_decidable:
        Refuse the trade outright when its era band is too wide for the spread model's own
        decidability rule, instead of pricing it and stamping the coverage MODELLED. Only
        meaningful with ``spread_band`` set; ignored on the flat snapshot, which has no era
        term to be undecidable about.

        Default ``False`` -- the pre-2026-07-30 behaviour, and note what that behaviour
        actually was: an undecidable ``RECORDED`` era priced as ``coverage=MEASURED`` on a
        band spanning 204,058x. The coverage half of that is repaired in ``spread_model``
        regardless of this flag; this flag is the stronger response, for a caller who wants
        the trade out of the population rather than merely labelled.
    spread_accounting:
        ``explicit_component`` charges the spread term against a gross return simulated
        without quote-side geometry. ``quote_geometry`` is for a fill-anchored gross that
        already paid the spread; it requires hash/time/account/symbol-bound
        ``geometry_spread_evidence``. The observed spread is attributed at its own authority
        while the additional charged spread is exactly zero. It need not equal a model
        percentile: transacted spread is time-varying.
    """
    if not sl_distance_price or float(sl_distance_price) <= 0:
        raise CostTruthError(
            "sl_distance_price must be > 0. Every cost here is a price/cash drag divided "
            "by the stop distance; there is no defensible default stop, and inventing one "
            "is the F38 failure mode."
        )
    holding_hours = _strict_nonnegative(holding_hours, "holding_hours")
    try:
        accounting = SpreadAccounting(spread_accounting)
    except ValueError:
        raise CostTruthError(
            f"spread_accounting must be one of {[m.value for m in SpreadAccounting]}, "
            f"got {spread_accounting!r}"
        ) from None
    truth = costs or load_broker_true_costs()
    resolved_symbol, rec = truth.resolve_instrument(account, symbol)
    sl = float(sl_distance_price)
    detail: dict = {
        "artifact_version": truth.version,
        "broker_true_costs_artifact_sha256": truth.artifact_sha256,
        "requested_symbol": symbol,
        "resolved_broker_symbol": resolved_symbol,
        "sl_distance_price": sl,
        "instrument_class": rec.get("instrument_class"),
        "traded_in_export_window": rec.get("traded_in_export_window"),
    }

    # --- commission -------------------------------------------------------------
    usd_per_lot, cdetail = commission_usd_per_lot(rec, entry_price)
    cblock = rec["commission"]
    if cblock.get("kind") == PEER_TRANSFER:
        # Resolve before measuring: `_measure_from` refuses an unresolved `peer_transfer` by
        # design (see its guard), because in every other cost slot such a block would be an
        # unvalidated transfer wearing a signed kind's name. Here the validation has already
        # run inside `commission_usd_per_lot`; resolving again is one dict rebuild and it keeps
        # the refusal a genuine property of the Measure layer rather than a call-site
        # convention.
        cblock, _ = _resolve_peer_transfer(cblock)
    snapshot_upu = _usd_per_price_unit_per_lot(rec)
    upu = snapshot_upu
    fx_rate = None
    profit_currency = str((rec.get("spec") or {}).get("currency_profit") or "")
    commission_kind = cblock.get("kind")
    # Only a cash-per-lot numerator consumes a historical USD-per-price-unit
    # denominator.  Price-domain spread/slippage/swap are already divided directly by
    # the stop.  A measured-zero commission is identically zero, and a notional-bp
    # numerator contains the same profit-currency conversion as its denominator, so
    # their R ratio cancels exactly.  Requiring an unused D1 rate for either case would
    # turn a decidable row into NOT_EVALUABLE without changing one result bit.
    if profit_currency and profit_currency != "USD" and commission_kind == "per_lot":
        if entry_utc is None:
            raise CostTruthError(
                f"{resolved_symbol} profit is denominated in {profit_currency}; entry_utc "
                "is required because its cash-per-lot commission consumes a date-indexed "
                "USD-per-price-unit conversion. "
                "The 2026 symbol-spec snapshot is not a historical default; NOT_EVALUABLE."
            )
        contract_size = (rec.get("spec") or {}).get("trade_contract_size")
        if not contract_size or float(contract_size) <= 0:
            raise CostTruthError(
                f"{resolved_symbol} needs trade_contract_size for historical "
                f"{profit_currency}/USD conversion; NOT_EVALUABLE"
            )
        from src.costs.fx_conversion import FxConversionError, load_historical_fx

        fx = historical_fx or load_historical_fx()
        try:
            fx_rate = fx.rate_at(
                profit_currency,
                entry_utc,
                server=truth.doc["accounts"][account]["server"],
            )
        except FxConversionError as exc:
            raise CostTruthError(str(exc)) from exc
        upu = float(contract_size) / fx_rate.profit_currency_per_usd
        if not math.isfinite(upu) or upu <= 0:
            raise CostTruthError(
                f"historical FX produced invalid USD-per-price-unit {upu!r} for "
                f"{resolved_symbol}"
            )
    detail["usd_per_price_unit_per_lot"] = upu
    detail["usd_per_price_unit_snapshot"] = snapshot_upu
    if profit_currency and profit_currency != "USD" and commission_kind in {
        "zero", "notional_bp"
    }:
        detail["pnl_conversion"] = {
            "profit_currency": profit_currency,
            "historical_fx_required": False,
            "component_consumers": [],
            "basis": (
                "zero commission is identically 0R; USD-per-price-unit is not consumed"
                if commission_kind == "zero"
                else "notional-bp profit-currency numerator and USD-per-price-unit "
                "denominator cancel exactly in R; stable snapshot-paired ratio used"
            ),
            "price_domain_components": ["spread_r", "slippage_r", "swap_r"],
            "price_domain_basis": "price displacement divided directly by stop distance",
        }
    if fx_rate is not None:
        detail["fx_conversion"] = {
            "profit_currency": profit_currency,
            "profit_currency_per_usd": fx_rate.profit_currency_per_usd,
            "source_pair": fx_rate.source_pair,
            "source_broker_date": fx_rate.source_broker_date,
            "source_completed_utc": fx_rate.source_completed_utc,
            "entry_broker_date": fx_rate.entry_broker_date,
            "staleness_days": fx_rate.staleness_days,
            "coverage": fx_rate.coverage.value,
            "provenance": fx_rate.provenance,
            "artifact_sha256": fx_rate.artifact_sha256,
            "cost_inputs_manifest_sha256": fx_rate.manifest_sha256,
            "component_consumers": ["commission_r"],
        }
    detail["commission"] = {**cdetail, "usd_per_lot_round_turn": usd_per_lot}
    commission_value_r = usd_per_lot / (sl * upu)
    commission = _measure_from(
        cblock,
        commission_value_r,
        "R",
        extra_prov=f"{usd_per_lot:.6g} USD/lot / ({sl:g} price * {upu:g} USD per price unit per lot)",
    )
    if fx_rate is not None:
        combined = weakest(commission.coverage, fx_rate.coverage)
        combined_kwargs: dict = {}
        if combined is Coverage.TRANSFERRED:
            sources = [
                source
                for source in (
                    commission.transferred_from,
                    f"historical {fx_rate.source_pair} D1 close",
                )
                if source
            ]
            combined_kwargs["transferred_from"] = "; ".join(sources)
        elif combined is Coverage.MODELLED:
            combined_kwargs.update(
                owner=commission.owner or "Wave 21 historical FX conversion",
                asof=commission.asof or "2026-08-08",
            )
        # Rebuild even when the enum class is unchanged. A TRANSFERRED commission
        # combined with TRANSFERRED FX still consumes both authorities, and retaining
        # only the commission's provenance/band would silently discard the denominator's
        # weaker source.
        commission = Measure(
            value=commission.value,
            coverage=combined,
            provenance=f"{commission.provenance}; {fx_rate.provenance}",
            unit=commission.unit,
            n=commission.n,
            **combined_kwargs,
        )

    # --- spread -----------------------------------------------------------------
    sblock = rec.get("spread_price")
    if spread_band is not None:
        # spread_model_v1: era-aware, banded, and priceable where the snapshot is not.
        from src.costs.spread_model import (
            DEFAULT_COMPOSITION,
            SpreadModelError,
            spread_price as _sm_price,
        )

        comp = spread_composition or DEFAULT_COMPOSITION
        try:
            est = _sm_price(symbol, account, entry_utc, band=spread_band,
                            vol_state=spread_vol_state, composition=comp,
                            era_exponent=spread_era_exponent,
                            require_decidable=bool(spread_require_decidable),
                            model=spread_model)
        except SpreadModelError as e:
            raise CostTruthError(
                f"spread_model[{comp}] cannot price {symbol} on {account}: {e}"
            ) from e
        detail["spread"] = {
            "spread_price": est.spread_price,
            "band": spread_band,
            "source": f"spread_model[{est.composition}]",
            "composition": est.composition,
            "era": est.era,
            "era_ratio": est.era_ratio,
            "era_class": est.era_class,
            "intraweek_mult": est.intraweek_mult,
            "decidable": est.decidable,
            "crossings_charged": 1,
            **est.detail,
        }
        spread = Measure(
            value=est.spread_price / sl,
            coverage=est.coverage,
            provenance=f"{est.provenance}; {est.spread_price:.6g} price / {sl:g} stop, one crossing",
            unit="R",
            **({"transferred_from":
                f"spread_model[{est.composition}] era {est.era} [{est.era_class}]"}
               if est.coverage is Coverage.TRANSFERRED else {}),
            **({"owner": "Session AG (spread model), Session AH (composition)",
                "asof": "2026-07-30"}
               if est.coverage is Coverage.MODELLED else {}),
        )
        sblock = sblock or {"coverage": est.coverage.value}
    elif not sblock:
        raise CostTruthError(
            f"no measured spread for {symbol} on {account}: that symbol has no file in the "
            "tick archive. Its spread is unmeasured, not zero. Pass `spread_band=` to "
            "price it from spread_model_v1 as a band instead of refusing."
        )
    table = (sblock.get("by_session") or {}).get(spread_session) if spread_session else (
        sblock.get("percentiles") if spread_band is None else None)
    if spread_band is None:
        if not table:
            raise CostTruthError(f"no spread percentiles for session {spread_session!r}")
        if spread_percentile not in table:
            raise CostTruthError(
                f"spread percentile {spread_percentile!r} not measured; have {sorted(table)}"
            )
        spread_price = float(table[spread_percentile])
        detail["spread"] = {
            "spread_price": spread_price,
            "percentile": spread_percentile,
            "session": spread_session or "all",
            "crossings_charged": 1,
        }
        spread = _measure_from(
            sblock,
            spread_price / sl,
            "R",
            extra_prov=f"{spread_percentile}={spread_price:g} price / {sl:g} stop, one crossing",
        )

    # A quote-side walk has already paid an OBSERVED physical spread in its fill
    # geometry. The model percentile stays diagnostic; transacted spread is allowed to
    # differ. What must reconcile is identity + authority + exactly-once accounting.
    model_spread = spread
    model_spread_price = float(detail["spread"]["spread_price"])
    attributed_spread: Measure | None = None
    if accounting is SpreadAccounting.QUOTE_GEOMETRY:
        evidence = geometry_spread_evidence
        if not isinstance(evidence, SpreadGeometryEvidence):
            raise CostTruthError(
                "quote_geometry requires SpreadGeometryEvidence bound to resolvable source "
                "bytes, row_index and trade_id; a bare zero or spread price is ambiguous "
                "and NOT_EVALUABLE"
            )
        if entry_utc is None:
            raise CostTruthError(
                "quote_geometry requires timezone-aware entry_utc to bind observed spread time"
            )
        if geometry_spread_price is not None:
            raise CostTruthError(
                "geometry_spread_price is not an authority and may not accompany "
                "quote_geometry; the physical spread is derived from the bound row's ask-bid"
            )
        (
            observed_price,
            observed_coverage,
            observed_provenance,
            observed_kwargs,
            observed_detail,
        ) = _resolve_geometry_authority(
            evidence,
            account=account,
            resolved_symbol=resolved_symbol,
            entry_utc=entry_utc,
            entry_price=entry_price,
            side=side,
            sl_distance_price=sl,
            verified_quote_geometry_resolver=verified_quote_geometry_resolver,
        )
        attributed_spread = Measure(
            value=observed_price / sl,
            coverage=observed_coverage,
            provenance=(
                f"observed fill-geometry spread {observed_price:g} price / {sl:g} stop; "
                f"{observed_provenance}"
            ),
            unit="R",
            n=1,
            **observed_kwargs,
        )
        spread = attributed_spread.scaled(
            0.0,
            provenance=(
                f"attributed observed spread {observed_price:g} already paid by the "
                "hash-bound fill-anchored quote geometry; additional deduction is zero"
            ),
        )
    elif geometry_spread_price is not None or geometry_spread_evidence is not None:
        raise CostTruthError(
            "geometry spread evidence is only valid with spread_accounting='quote_geometry'; "
            "explicit-component gross must not carry an implicit geometry adjustment"
        )
    detail["spread"].update({
        "accounting": accounting.value,
        "model_spread_price": model_spread_price,
        "model_spread_r": model_spread.value,
        "physical_spread_r": (
            attributed_spread.value if attributed_spread is not None else model_spread.value
        ),
        "attributed_geometry_spread_r": (
            attributed_spread.as_dict() if attributed_spread is not None else None
        ),
        "charged_spread_r": spread.value,
        "observed_geometry_spread_price": (
            observed_price if attributed_spread is not None else None
        ),
        "geometry_authority": observed_detail if attributed_spread is not None else None,
        "crossings_charged": 0 if attributed_spread is not None else 1,
    })

    # --- swap -------------------------------------------------------------------
    spec = rec.get("spec") or {}
    drag, sw_detail = swap_price_drag_per_night(rec, side, entry_price)
    if entry_utc is not None:
        nights, ndetail = rollover_nights(
            entry_utc,
            holding_hours,
            server=truth.doc["accounts"][account]["server"],
            rollover3days_weekday=spec.get("swap_rollover3days"),
        )
        swap = _measure_from(
            rec["swap"],
            drag * nights / sl,
            "R",
            extra_prov=f"{nights:g} charged night(s) counted on broker wall clock",
        )
    else:
        nights = holding_hours / 24.0
        ndetail = {
            "nights_charged": nights,
            "basis": "holding_hours/24 -- no entry instant supplied",
        }
        swap = Measure(
            value=drag * nights / sl,
            coverage=Coverage.MODELLED,
            provenance=(
                f"{rec['swap'].get('provenance', '')}; nights approximated as "
                "holding_hours/24 with no weekend or triple-swap adjustment because "
                "entry_utc was not supplied"
            ),
            unit="R",
            owner="Session J (Stage 1.1)",
            asof="2026-07-27",
        )
    detail["swap"] = {**sw_detail, **ndetail, "price_drag_per_night": drag}

    # --- slippage ---------------------------------------------------------------
    from src.costs.slippage_model import SlippageModelError, load_slippage_model

    sm = slippage_model or load_slippage_model()
    try:
        sl_est = sm.estimate(account, resolved_symbol)
    except SlippageModelError as exc:
        raise CostTruthError(str(exc)) from exc
    slippage_kwargs: dict = {}
    if sl_est.coverage is Coverage.TRANSFERRED:
        slippage_kwargs["transferred_from"] = f"slippage sample {sl_est.canonical_symbol}"
    elif sl_est.coverage is Coverage.MODELLED:
        slippage_kwargs.update(owner="Wave 21 cost truth", asof="2026-08-08")
    slippage = Measure(
        value=sl_est.expected_adverse_price / sl,
        coverage=sl_est.coverage,
        provenance=(
            f"{sl_est.provenance}; expected adverse entry displacement "
            f"{sl_est.expected_adverse_price:.12g} price / {sl:g} stop"
        ),
        unit="R",
        n=sl_est.n,
        **slippage_kwargs,
    )
    detail["slippage"] = {
        "expected_adverse_price": sl_est.expected_adverse_price,
        "canonical_symbol": sl_est.canonical_symbol,
        "n": sl_est.n,
        "coverage": sl_est.coverage.value,
        "artifact_sha256": sl_est.artifact_sha256,
        "cost_inputs_manifest_sha256": sl_est.manifest_sha256,
        **sl_est.detail,
    }

    total_value = component_sum_r(
        spread.value,
        slippage.value,
        swap.value,
        commission.value,
    )
    total_cov = weakest(commission.coverage, swap.coverage, spread.coverage, slippage.coverage)
    weakest_term = min(
        (("commission", commission), ("swap", swap), ("spread", spread), ("slippage", slippage)),
        key=lambda kv: -kv[1].coverage.strength,
    )[0]
    total_kwargs: dict = {}
    if total_cov is Coverage.TRANSFERRED:
        total_kwargs["transferred_from"] = f"weakest term: {weakest_term}"
    if total_cov is Coverage.MODELLED:
        total_kwargs["owner"] = "Session J (Stage 1.1)"
        total_kwargs["asof"] = "2026-07-27"
    total = Measure(
        value=total_value,
        coverage=total_cov,
        provenance=(
            "FD identity: spread + expected_slippage + swap + commission, evaluated "
            "left-to-right; coverage is the weakest "
            f"component's ({weakest_term}), per the class-travels rule"
        ),
        unit="R",
        **total_kwargs,
    )
    return CostBreakdown(
        symbol=symbol,
        account=account,
        commission_r=commission,
        swap_r=swap,
        spread_r=spread,
        slippage_r=slippage,
        total_r=total,
        detail=detail,
        attributed_spread_r=attributed_spread,
    )


ACCOUNT_BY_SERVER = {
    "ftmo-server3": "FTMO",
    "ftmo-server": "FTMO",
    "ftmo": "FTMO",
    "redacted_account-server 2": "redacted_account",
    "redacted_account-server2": "redacted_account",
    "redacted_account": "redacted_account",
}
ACCOUNT_BY_NAMESPACE = {
    "operator_profile": "FTMO",
    "redacted_account_live_bee34003": "redacted_account",
}


def account_for(*, server: str | None = None, namespace: str | None = None) -> str:
    """Resolve a broker-truth account key. Fails closed, never guesses.

    Mirrors `broker_clock.resolve_rule`'s posture deliberately: an unrecognised server is
    an error, not a default, because the two accounts have materially different costs
    (BTCUSD quoted spread differs 22x between them).
    """
    if namespace:
        hit = ACCOUNT_BY_NAMESPACE.get(str(namespace).strip())
        if hit:
            return hit
    if server:
        hit = ACCOUNT_BY_SERVER.get(str(server).strip().lower())
        if hit:
            return hit
    raise CostTruthError(
        f"cannot resolve a broker-truth account from server={server!r} namespace={namespace!r}. "
        f"Known servers: {sorted(set(ACCOUNT_BY_SERVER))}. Register it and measure its costs; "
        "do not fall back to another account's schedule."
    )


def commission_usd_per_lot_for_packet(
    symbol: str,
    *,
    server: str | None = None,
    namespace: str | None = None,
    entry_price: float | None = None,
    costs: BrokerTrueCosts | None = None,
) -> float | None:
    """Adapter for `broker_net_cost_engine` (the OD-J1 prepared change).

    Returns round-turn commission in account currency per lot, or **None** when it cannot
    be determined. None is the correct failure mode: the engine's `total_cost_r` is
    already `None` when a component is unavailable (`:577-578`) and a `None` total refuses
    the packet. Returning `0.0` on an unknown instrument is the F38 defect itself.
    """
    try:
        truth = costs or load_broker_true_costs()
        account = account_for(server=server, namespace=namespace)
        rec = truth.instrument(account, symbol)
        return commission_usd_per_lot(rec, entry_price)[0]
    except CostTruthError:
        return None


def legacy_class_cost_r(symbol: str, account: str, *, costs: BrokerTrueCosts | None = None) -> Measure:
    """The deployed `ULTIMATE_REAL_COST_MAP.json` value for this symbol's class.

    This is the F39 comparator, not a cost to charge. The two F39 readings differ in what
    this number contained:

    * **spread-only** -- the map was a spread proxy, so commission was never in the
      baseline and the W7 result is optimistic by the full commission.
    * **commission-inclusive** -- the map was `spread + commission`
      (`KB7_tick_lib.py:22`, `KB7_tick_truth.py:59-63` both say so), so removing its
      "over-charge" dropped a commission proxy, and the W7 result is optimistic by
      commission net of whatever share the map already carried.

    The record does not settle which, because the map has **no generator** in git history
    (enters at `450a275f8` as a JSON-only diff). Stage 1.2 publishes both as a band; this
    function supplies the term both readings need.
    """
    truth = costs or load_broker_true_costs()
    rec = truth.instrument(account, symbol)
    klass = rec.get("instrument_class")
    legacy = truth.doc.get("legacy_class_cost_map", {})
    values = legacy.get("values", {})
    key = "fx" if klass == "jpy_fx" and "jpy_fx" not in values else klass
    if key not in values:
        key = "_global_median"
    if key not in values:
        raise CostTruthError(f"no legacy class cost for class {klass!r}")
    return Measure(
        value=float(values[key]),
        coverage=Coverage.MODELLED,
        provenance=f"{legacy.get('provenance')} (class key {key!r})",
        unit="R",
        owner="W7 deploy pass (ULTIMATE_REAL_COST_MAP.json, no generator in git)",
        asof="2026-06-10",
    )
