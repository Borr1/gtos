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

Sign convention: costs are positive.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from functools import lru_cache
from pathlib import Path

from src.costs.coverage import Coverage, Measure, weakest
from src.utils.broker_clock import resolve_rule, utc_to_broker_naive

__all__ = [
    "BrokerTrueCosts",
    "CostBreakdown",
    "cost_r",
    "load_broker_true_costs",
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

    def as_dict(self) -> dict:
        return {
            "symbol": self.symbol,
            "account": self.account,
            "commission_r": self.commission_r.as_dict(),
            "swap_r": self.swap_r.as_dict(),
            "spread_r": self.spread_r.as_dict(),
            "slippage_r": self.slippage_r.as_dict(),
            "total_r": self.total_r.as_dict(),
            "detail": self.detail,
        }


class BrokerTrueCosts:
    """Loaded ``BROKER_TRUE_COSTS_V1.json`` with instrument lookup."""

    def __init__(self, doc: dict, source: Path | None = None):
        self.doc = doc
        self.source = source
        self.version = doc.get("version")
        self.schema = doc.get("schema")

    @property
    def accounts(self) -> list[str]:
        return sorted(self.doc.get("accounts", {}))

    def instrument(self, account: str, symbol: str) -> dict:
        acct = self.doc.get("accounts", {}).get(account)
        if acct is None:
            raise CostTruthError(
                f"no broker truth for account {account!r}. Known: {self.accounts}. "
                "Broker truth exists for exactly two live accounts."
            )
        rec = acct["instruments"].get(symbol)
        if rec is None:
            raise CostTruthError(
                f"no broker truth for {symbol!r} on {account}. It is not in that broker's "
                f"quotable universe ({len(acct['instruments'])} symbols). A missing "
                "instrument is unpriced, not free."
            )
        return rec

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
def _load_cached(path_str: str) -> BrokerTrueCosts:
    path = Path(path_str)
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
    return BrokerTrueCosts(json.loads(path.read_text()), source=path)


def load_broker_true_costs(path: Path | str | None = None) -> BrokerTrueCosts:
    return _load_cached(str(path or DEFAULT_ARTIFACT))


# --------------------------------------------------------------------------- helpers


def _usd_per_price_unit_per_lot(rec: dict) -> float:
    upu = rec.get("usd_per_price_unit_per_lot")
    if not upu:
        raise CostTruthError(
            f"{rec.get('broker_path')} has no usable trade_tick_value/trade_tick_size, so "
            "no cash-to-R conversion is possible for it."
        )
    return float(upu)


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


def swap_price_drag_per_night(rec: dict, side: str, entry_price: float | None) -> tuple[float, dict]:
    """Adverse swap for one night, in price units. Zero when the swap is favourable."""
    spec = rec.get("spec") or {}
    swap_field = "swap_long" if side.upper() in ("LONG", "BUY") else "swap_short"
    raw = spec.get(swap_field)
    mode = spec.get("swap_mode")
    detail = {"swap_field": swap_field, "swap_raw": raw, "swap_mode": mode}
    if raw is None or mode is None:
        raise CostTruthError(f"swap unavailable: swap_mode={mode!r} {swap_field}={raw!r}")
    if float(raw) >= 0:
        detail["note"] = "favourable or zero swap -> no cost"
        return 0.0, detail
    adverse = abs(float(raw))
    if int(mode) == 1:  # points
        point = spec.get("point")
        if not point:
            raise CostTruthError("swap mode 1 needs `point`")
        return adverse * float(point), detail
    if int(mode) in (5, 6):  # annual interest percentage of price
        px = entry_price or (rec.get("spread_price") or {}).get("mid_price_median")
        if not px:
            raise CostTruthError("swap modes 5/6 need a price")
        detail["price"] = px
        detail["days_per_year"] = 360.0
        return float(px) * (adverse / 100.0) / 360.0, detail
    raise CostTruthError(
        f"swap_mode {mode} is currency-denominated; it needs post-sizing volume "
        "conversion and is a source gap here (same limitation as "
        "broker_net_cost_engine._swap_cost_packet)."
    )


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
    spread_model: "SpreadModel | None" = None,
    costs: BrokerTrueCosts | None = None,
) -> CostBreakdown:
    """Round-trip cost of one trade, in R, with a coverage class on every term.

    Parameters
    ----------
    sl_distance_price:
        ``abs(entry - stop)`` in price units. Required: R is defined by it.
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
    """
    if not sl_distance_price or float(sl_distance_price) <= 0:
        raise CostTruthError(
            "sl_distance_price must be > 0. Every cost here is a price/cash drag divided "
            "by the stop distance; there is no defensible default stop, and inventing one "
            "is the F38 failure mode."
        )
    truth = costs or load_broker_true_costs()
    rec = truth.instrument(account, symbol)
    sl = float(sl_distance_price)
    upu = _usd_per_price_unit_per_lot(rec)
    detail: dict = {
        "artifact_version": truth.version,
        "sl_distance_price": sl,
        "usd_per_price_unit_per_lot": upu,
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
    detail["commission"] = {**cdetail, "usd_per_lot_round_turn": usd_per_lot}
    commission = _measure_from(
        cblock,
        usd_per_lot / (sl * upu),
        "R",
        extra_prov=f"{usd_per_lot:.6g} USD/lot / ({sl:g} price * {upu:g} USD per price unit per lot)",
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
        nights = float(holding_hours) / 24.0
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
    slblock = rec["slippage"]
    slippage = _measure_from(
        slblock,
        float(slblock["value_r"]),
        "R",
        extra_prov="entry slippage measured in R at the live stop geometry; it does not "
        "rescale with sl_distance",
    )

    total_value = commission.value + swap.value + spread.value + slippage.value
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
            "sum of commission + swap + spread + slippage; coverage is the weakest "
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
