"""live_evidence.py — the book-lane rerate producer (Stage 5, learning lane).

Turns the live book's **closed** positions into the per-sleeve `SleeveEvidence` that
`learning_actuator.recommend()` consumes, priced at broker truth.

Reading, not modelling — and why that is a departure from the brief
-------------------------------------------------------------------
Stage 5 says to price realized outcomes "through Session J's cost layer". Taken literally that
would be a step backwards for *realized* fills: the broker reports the commission, swap and fee it
actually charged, per deal, and a model of those numbers is strictly weaker evidence than the
numbers. So this producer **reads** realized cost and uses `src.costs.cost_r` for the two jobs a
model is actually better at:

* **reconciliation** — predicted vs realized cost per fill, which is the measured-cost-deviation
  tripwire Stage 3 wants, and which Session J already validated at 0.000535 R mean absolute error
  over 175 real deals (`COST_LAYER_RECONCILIATION.json`);
* **fallback** — when a position's broker accounting is incomplete, `cost_r` supplies the cost with
  its own coverage class attached.

What is never done is the third option: filling a missing cost with zero. That is F38 exactly, and
a rerate computed on gross R would re-learn it.

The R denominator, without needing volume
------------------------------------------
Realized R needs risk-in-cash at entry, and the packets carry no lot size. It is recoverable from
the position's own arithmetic, exactly and with no broker spec lookup: the position's realized
gross profit divided by the price distance it travelled **is** the cash value of one price unit for
that lot, so

    cash_per_price_unit = aggregate_profit / ((exit_price - fill_price) * direction)
    risk_cash           = |fill_price - fill_adjusted_stop| * cash_per_price_unit
    realized_net_R      = realized_pnl / risk_cash

Cross-checked on the record: a SPX500 `idxrev` short returns 0.7472 R by this derivation against
its own independently-recorded ``broker_position_planned_target_r`` of 0.75 — a field this
calculation never reads.

Only genuinely closed positions count
--------------------------------------
Session P published 71,969 still-open positions as completed holds — a 2.49x overstatement of the
one number OD-3 turns on — and its own refuter caught it. Admission here requires
``trade_lifecycle_status == "closed"`` **and** a broker exit deal (``broker_exit_time_utc``), and
every row that fails is counted and published rather than dropped silently.
"""
from __future__ import annotations

import gzip
import json
import math
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Iterable, Optional

from src.components.ultimate_book.learning_actuator import SleeveEvidence

REPO = Path(__file__).resolve().parents[3]
# V2 is Session AE's book-wide family-wise calibration; V1 is R's per-sleeve one, kept on disk
# because it is the evidence behind R's published table and superseding it is not deleting it.
# V2 lives under `docs/` deliberately: `research/operations/` is sparse-checkout-excluded, so an
# artifact there can be committed, absent from a working tree, and leave `git status` clean
# (WAVE_7_WORKING_AGREEMENT section 4). The fallback keeps a tree that has only V1 working.
CALIBRATION_V2 = REPO / "docs/audits/fable5-vision-audit-20260725/phase7/receipts/LIVE_EVIDENCE_CALIBRATION_V2.json"
CALIBRATION_V1 = REPO / "research/operations/learning_lane_2026_07_29/LIVE_EVIDENCE_CALIBRATION_V1.json"
DEFAULT_CALIBRATION = CALIBRATION_V2

NAMESPACE_TO_ACCOUNT = {
    "operator_profile": "FTMO",
    "redacted_account_live_bee34003": "redacted_account",
}

# Price agreement below this is treated as no measurable travel: the cash-per-price-unit bridge
# divides by it, so a scratch close is unpriceable rather than infinite.
MIN_PRICE_TRAVEL = 1e-9


@dataclass
class RealizedFill:
    """One closed live position, priced at broker truth."""
    sleeve: str
    account: str
    namespace: str
    symbol: str
    broker_symbol: Optional[str]
    direction: Optional[str]
    entry_utc: Optional[str]
    exit_utc: Optional[str]
    hold_hours: Optional[float]
    risk_px: float          # |fill - stop| in PRICE units; what cost_r needs as sl_distance_price
    entry_px: float
    risk_cash: float
    realized_pnl: float
    realized_net_r: float
    realized_cost_r: float
    gross_r: float
    commission: float
    swap: float
    fee: float
    cost_coverage: str
    accounting_status: Optional[str]

    def as_dict(self) -> dict:
        return dict(self.__dict__)


@dataclass
class ProducerReport:
    """What was admitted, what was not, and why. The gaps are the product, not an afterthought."""
    fills: list = field(default_factory=list)
    rejected: dict = field(default_factory=dict)
    rejected_examples: dict = field(default_factory=dict)
    total_rows: int = 0
    closed_rows: int = 0
    admitted_close_actions: dict = field(default_factory=dict)
    refused_close_actions: dict = field(default_factory=dict)
    admitted_dates: list = field(default_factory=list)
    refused_dates: list = field(default_factory=list)

    def reject(self, reason: str, row: dict) -> None:
        self.rejected[reason] = self.rejected.get(reason, 0) + 1
        self.rejected_examples.setdefault(reason, {
            "sleeve": row.get("sleeve"),
            "symbol": row.get("symbol"),
            "namespace": row.get("namespace"),
        })

    def coverage_note(self) -> dict:
        """Is the admitted set a fair sample of the live record? Published, because it is not.

        Two ways it is not, both measured rather than asserted: the refusals cluster on a CALENDAR
        BREAK (the B215 block), and they are OUTCOME-CORRELATED — take-profit closes are winners by
        construction, so refusing them biases the surviving evidence downward.
        """
        admitted = sorted(self.admitted_dates)
        refused = sorted(self.refused_dates)
        tp_adm = self.admitted_close_actions.get("tp1_full_close", 0)
        tp_ref = self.refused_close_actions.get("tp1_full_close", 0)
        return {
            "admitted_date_range": [admitted[0], admitted[-1]] if admitted else None,
            "refused_date_range": [refused[0], refused[-1]] if refused else None,
            "admitted_close_actions": dict(sorted(self.admitted_close_actions.items(),
                                                  key=lambda kv: -kv[1])),
            "refused_close_actions": dict(sorted(self.refused_close_actions.items(),
                                                 key=lambda kv: -kv[1])),
            "take_profit_closes_admitted": tp_adm,
            "take_profit_closes_refused": tp_ref,
            "sample_is_biased": bool(tp_ref and not tp_adm),
            "why": (
                "refusals cluster on a calendar break in exit reconciliation (B215) and exclude "
                "take-profit closes, which are winners by construction. The admitted set is a "
                "coverage-limited slice, not a random sample of the live record."
            ),
        }


def _f(row: dict, *names: str) -> Optional[float]:
    """First present, non-null, numeric field among `names`."""
    for n in names:
        v = row.get(n)
        if v is not None:
            try:
                return float(v)
            except (TypeError, ValueError):
                continue
    return None


def _parse_utc(s) -> Optional[datetime]:
    if not s or not isinstance(s, str):
        return None
    try:
        return datetime.fromisoformat(s.replace("Z", "+00:00"))
    except ValueError:
        return None


def iter_packets(path: Path | str) -> Iterable[dict]:
    """Stream a runtime-learning-packet JSONL(.gz). The file lives outside the repo."""
    p = Path(path)
    if not p.is_file():
        raise FileNotFoundError(
            f"no packet stream at {p}. The live record is an export artifact, not repo state; "
            "point --packets at a fresh export rather than assuming an empty live record."
        )
    opener = gzip.open if p.suffix == ".gz" else open
    with opener(p, "rt", encoding="utf-8", errors="replace") as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            try:
                yield json.loads(line)
            except ValueError:
                continue


def price_closed_position(row: dict) -> tuple[Optional[RealizedFill], Optional[str]]:
    """Price one `position_closed` packet at broker truth. Returns (fill, rejection_reason)."""
    o = row.get("outcome") or {}
    src = {**row, **o}  # the outcome block repeats and refines the top level

    if src.get("trade_lifecycle_status") != "closed":
        return None, "not_lifecycle_closed"
    if not src.get("broker_exit_time_utc"):
        # Renamed 2026-07-29 (B281). This said "still_open_or_unreconciled" and the first half was
        # simply wrong: a refuter checked all 61 and **every one is a completed hold** —
        # `trade_lifecycle_status == "closed"` and `closed_at_utc` present on 61/61, with close
        # actions `broker_closed` 47, `tp1_full_close` 8, `vnext_time_stop` 4. What they lack is the
        # broker deal-record JOIN: `exit_reconciliation_status` is None (never attempted) on 59.
        #
        # And it is not a per-row property. It is a calendar block, the same one as B215: before
        # 2026-06-24, 1 of 60 closed rows joins (1.7 %); from 2026-06-24 on, 89 of 91 (97.8 %).
        # **It is also outcome-correlated** — all 8 `tp1_full_close` rows, which are winners by
        # construction, are refused and none is admitted. So the admitted set is not a random sample
        # of the live record, and `report.coverage_note()` publishes that rather than leaving a
        # reader to infer a clean 89.
        return None, "no_broker_exit_deal_record_join"

    sleeve = src.get("sleeve")
    if not sleeve:
        return None, "no_sleeve_attribution"
    namespace = src.get("namespace") or ""
    account = NAMESPACE_TO_ACCOUNT.get(namespace)
    if account is None:
        return None, f"unmapped_namespace:{namespace or 'missing'}"

    # R is defined by the risk taken AT ENTRY. The stop that matters is therefore the one the trade
    # opened with, never the one it closed with.
    #
    # `broker_position_sl` is the LIVE stop at close -- after break-even moves and trailing. Using it
    # as a fallback (as the first version of this did) shrinks the denominator only on trades that
    # ran far enough to trail, i.e. only on WINNERS, so it inflates realized R one-sidedly. Measured
    # by a refuter over the 50 rows that carry it: 5 winners had a ratio below 0.9 (minimum 0.100)
    # and **zero losers** did, worst single row +0.878 R against a true +0.328 R, and the corpus mean
    # moved +0.0278 R with 82 % of the inflation in five trailed winners. It is excluded entirely.
    #
    # `fill_adjusted` is the planned stop shifted by the fill slippage, so it preserves the planned
    # risk DISTANCE exactly; where it is absent the planned pair gives the same distance. Both are
    # entry-time quantities. Only 2 of 151 packets carry the fill-adjusted pair.
    fill_price = _f(src, "broker_position_fill_price", "broker_position_price_open", "entry_price")
    stop = _f(src, "broker_position_fill_adjusted_stop_loss", "stop_loss", "broker_position_planned_stop_loss")
    planned_entry = _f(src, "entry_price", "broker_position_planned_entry_price")
    exit_price = _f(src, "broker_exit_price")
    if fill_price is None or stop is None or exit_price is None:
        return None, "missing_price_geometry"
    # Risk distance from the entry-time pair the stop belongs to, so a slipped fill never rescales R.
    risk_anchor = fill_price if src.get("broker_position_fill_adjusted_stop_loss") is not None else (
        planned_entry if planned_entry is not None else fill_price)

    direction = (src.get("direction") or "").upper()
    if direction not in ("LONG", "SHORT", "BUY", "SELL"):
        return None, "missing_direction"
    dirsign = 1.0 if direction in ("LONG", "BUY") else -1.0

    risk_px = abs(risk_anchor - stop)
    move_px = (exit_price - fill_price) * dirsign
    if risk_px <= MIN_PRICE_TRAVEL:
        return None, "zero_stop_distance"
    if abs(move_px) <= MIN_PRICE_TRAVEL:
        return None, "zero_price_travel_cash_bridge_undefined"

    # Profit and charges must come from the SAME accounting basis. Chosen atomically rather than
    # field-by-field: mixing a position-aggregate profit with exit-only charges would understate
    # cost, which is the F38 direction. Measured on the live export: the two bases never mix (50
    # rows carry the full position aggregate, 40 carry exit-deal fields only, 0 are mixed), and
    # `broker_position_aggregate_profit` is GROSS of charges on all 50 —
    # `aggregate_profit + commission + swap + fee == broker_realized_pnl` exactly. So using the
    # aggregate for the cash bridge and realized_pnl for the numerator does not double-count.
    if src.get("broker_position_aggregate_profit") is not None:
        basis, prefix = "position_aggregate", "broker_position_aggregate_"
    elif src.get("broker_exit_profit") is not None:
        # REFUSED, not admitted-and-labelled. Corrected 2026-07-29 (B280) after a refuter measured
        # what the exit-only basis actually omits: entry commission is **70.8 %** of total commission
        # on the rows that carry both legs ($350.49 of $495.26), and redacted_account is
        # `commission_charge_side: entry_only` (BROKER_TRUE_COSTS_V1.json), so its exit-only rows
        # report commission **exactly 0.0 on 18 of 18** — the entire charge invisible. Mean realized
        # cost across the two classes is 0.0889 R vs 0.0235 R, a 3.8x gap on the same symbols.
        #
        # Understated cost makes a live record look BETTER, which makes the gate fire LATER. For a
        # brake that is the fail-open direction, and it is F38 exactly: a missing cost is unpriced,
        # not free. These rows are published as a coverage refusal instead. `cost_r` could supply the
        # missing leg at a stated coverage class — that is the designed fallback and it is NOT wired
        # here, deliberately, because the same refuter measured this class at 0.0425 R against
        # 0.00298 R for complete rows, so the residual is a data gap and modelling over it would hide
        # the gap rather than close it.
        return None, "incomplete_accounting_exit_deal_only_entry_commission_missing"
    else:
        return None, "no_broker_gross_profit"

    gross_cash = _f(src, f"{prefix}profit")
    cash_per_px = gross_cash / move_px
    if cash_per_px <= 0:
        # profit must move with the trade; a negative bridge means the fields disagree
        return None, "inconsistent_profit_vs_price_travel"
    risk_cash = risk_px * cash_per_px

    commission = _f(src, f"{prefix}commission") or 0.0
    swap = _f(src, f"{prefix}swap") or 0.0
    fee = _f(src, f"{prefix}fee") or 0.0

    realized_pnl = _f(src, "broker_realized_pnl", "broker_position_realized_pnl")
    if realized_pnl is None:
        realized_pnl = gross_cash + commission + swap + fee

    entry_utc = src.get("broker_fill_time_utc") or src.get("decision_time_utc")
    exit_utc = src.get("broker_exit_time_utc")
    t0, t1 = _parse_utc(entry_utc), _parse_utc(exit_utc)
    hold_hours = (t1 - t0).total_seconds() / 3600.0 if (t0 and t1) else None

    coverage = "MEASURED" if (
        basis == "position_aggregate"
        and src.get("broker_position_accounting_coverage_status") == "entry_and_exit_deals_present"
    ) else "PARTIAL_EXIT_DEAL_ONLY"

    return RealizedFill(
        sleeve=sleeve,
        account=account,
        namespace=namespace,
        symbol=src.get("symbol") or "",
        broker_symbol=src.get("broker_symbol"),
        direction=direction,
        entry_utc=entry_utc,
        exit_utc=exit_utc,
        hold_hours=hold_hours,
        risk_px=risk_px,
        entry_px=fill_price,
        risk_cash=risk_cash,
        realized_pnl=realized_pnl,
        realized_net_r=realized_pnl / risk_cash,
        realized_cost_r=-(commission + swap + fee) / risk_cash,  # costs are positive drags
        gross_r=gross_cash / risk_cash,
        commission=commission,
        swap=swap,
        fee=fee,
        cost_coverage=coverage,
        accounting_status=src.get("broker_position_accounting_coverage_status"),
    ), None


def collect_realized_fills(packets: Iterable[dict]) -> ProducerReport:
    """Every closed, priceable live position, with a full account of what was refused."""
    rep = ProducerReport()
    for row in packets:
        rep.total_rows += 1
        if row.get("event_type") != "position_closed":
            continue
        rep.closed_rows += 1
        o = row.get("outcome") or {}
        closed_at = o.get("closed_at_utc") or row.get("closed_at_utc")
        close_action = o.get("close_action") or row.get("close_action")
        fill, reason = price_closed_position(row)
        if fill is None:
            rep.reject(reason or "unknown", row)
            rep.refused_close_actions[close_action] = rep.refused_close_actions.get(close_action, 0) + 1
            if closed_at:
                rep.refused_dates.append(str(closed_at)[:10])
            continue
        rep.fills.append(fill)
        rep.admitted_close_actions[close_action] = rep.admitted_close_actions.get(close_action, 0) + 1
        if closed_at:
            rep.admitted_dates.append(str(closed_at)[:10])
    return rep


# Survivor tiers from SURVIVOR_BOOK_V1.json that clear broker-true cost outright. The three
# conditional tiers turn on holding time, which no cache records (CLAUDE.md section 4), so they are
# NOT treated as survivors for the purpose of permitting a size-up.
_SURVIVING_TIERS = {"UNCONDITIONAL", "MEASURED_LIVE_CARRY", "CARRY_CONDITIONAL_LIVE_SUPPORTED"}


def _survives(tier: Optional[str]) -> Optional[bool]:
    """True/False for a known tier, None when the tier is unknown.

    REPORTING ONLY since 2026-07-30 (AE). This used to feed a size-up veto in the actuator, which
    existed because the backtest half was the legacy-cost CP4/CP5 replay. The backtest half is now
    Session AA's broker-true splits, so a sleeve killed by carry shows it in its own split means and
    the veto has nothing to contain. The label is still carried because a reader of a recommendation
    wants to see the survivor tier next to it, and because the regression tripwire that replaced the
    veto keys off it.
    """
    if not tier:
        return None
    return tier in _SURVIVING_TIERS


def _exit_order(r) -> tuple:
    """Sort key by exit time. Timestamped rows first and in time order; anything unparseable falls
    to the end in stable string order rather than raising on an aware/naive comparison."""
    ts = _parse_utc(r.exit_utc)
    return (0, ts.timestamp(), "") if ts is not None else (1, 0.0, str(r.exit_utc or ""))


def _day_blocks(rows: list) -> int:
    """Distinct trading days behind a set of live fills — the independent-observation count.

    Blocked on the ENTRY day, not the exit day: same-day entries share the market state that
    produced them, which is the dependence R measured (`sub_xvol_pullback` lag-1 rho 0.511 with up
    to 12 trades on one date). Exits of the same cohort scatter across later days and would
    over-count the evidence.

    The packets' `*_utc` fields are trusted as UTC here, which is the one place this repo says to be
    careful (`CLAUDE.md` section 4: bars and ticks are broker wall clock whatever the field is named).
    The exposure is bounded: a misassigned boundary can only merge or split two ADJACENT blocks, so
    the count moves by at most one per straddling cluster, and the count is compared against a bar
    of 30.
    """
    days = set()
    for r in rows:
        ts = _parse_utc(r.entry_utc) or _parse_utc(r.exit_utc)
        if ts is not None:
            days.add(ts.date().isoformat())
        elif r.entry_utc:
            days.add(str(r.entry_utc)[:10])
    return len(days) if days else len(rows)


def boundaries_at(cal: dict, n: int) -> tuple[Optional[float], Optional[float]]:
    """The (down-weight, gate) boundaries for a sleeve at exactly `n` live fills.

    Reads the precomputed table, and **evaluates the closed form beyond the table's end**.

    Why the second half matters. The table stops at the artifact's `n_max` (60). Looking the
    boundary up with a plain `.get(str(n))` returned `None` for `n > n_max`, which the rule reads as
    "not calibrated" -- so the 61st consecutive losing fill *removed* a gate the 60th had applied:

        58 stop-outs -> REFUTED_KILL / GATE / x0.0
        61 stop-outs -> UNCALIBRATED / INSUFFICIENT_EVIDENCE / x1.0

    More adverse evidence producing a less adverse verdict, and no possibility of the live gate ever
    firing again past 60 fills. Found by a refuter, 2026-07-29 (B276). The boundary is
    ``b_n = n*claim - c*sd*sqrt(n)`` and the artifact stores `claim_mean_r`, `sd_r`, `c_down` and
    `c_kill`, so there is no need to guess: it is evaluated exactly. If any parameter is missing the
    result is `None` for that boundary, and the rule then reports UNCALIBRATED rather than inventing
    one.
    """
    if not cal.get("calibrated"):
        return None, None
    n = int(n)
    if n <= 0:
        return None, None
    tbl_down = (cal.get("thresholds_down_r") or {}).get(str(n))
    tbl_kill = (cal.get("thresholds_kill_r") or {}).get(str(n))
    if tbl_down is not None or tbl_kill is not None:
        return tbl_down, tbl_kill
    claim, sd = cal.get("claim_mean_r"), cal.get("sd_r")
    if claim is None or sd is None:
        return None, None

    def _b(c):
        return None if c is None else float(claim) * n - float(c) * float(sd) * math.sqrt(n)

    return _b(cal.get("c_down")), _b(cal.get("c_kill"))


def load_calibration(path: Path | str | None = None) -> dict:
    """The calibration artifact: V2 if present, else R's V1, else refuse."""
    if path is not None:
        candidates = [Path(path)]
    else:
        candidates = [CALIBRATION_V2, CALIBRATION_V1]
    for p in candidates:
        if p.is_file():
            return json.loads(p.read_text())
    raise FileNotFoundError(
        f"no live-evidence calibration at any of {[str(c) for c in candidates]}. Build it with "
        "`python3 scripts/build_live_evidence_calibration.py`. Without it the live gate reports "
        "UNCALIBRATED rather than guessing a boundary."
    )


def build_sleeve_evidence(
    fills: list,
    *,
    account: str,
    calibration: dict,
    backtest: Optional[dict] = None,
) -> dict:
    """Per-sleeve `SleeveEvidence` for one account, live fields populated and boundaries attached.

    `backtest` optionally supplies the existing every-split evidence keyed by sleeve, so the
    returned objects carry both halves and `recommend()` sees the whole picture. Sleeves with live
    fills but no backtest entry still get an object — a live-only sleeve must be able to be gated.
    """
    by_sleeve: dict = {}
    for f in fills:
        if f.account != account:
            continue
        by_sleeve.setdefault(f.sleeve, []).append(f)

    acal = (calibration.get("accounts") or {}).get(account, {})
    out: dict = {}
    for sleeve, rows in sorted(by_sleeve.items()):
        # ORDER MATTERS NOW. The boundary is a first-passage boundary (R section 4 item 12, fixed in
        # `learning_actuator._first_passage`), so the rule needs the path, not just its endpoint.
        # Evidence arrives when a position CLOSES, so the sequence is by exit time.
        rows = sorted(rows, key=_exit_order)
        n = len(rows)
        mean_r = sum(r.realized_net_r for r in rows) / n
        base: SleeveEvidence = (backtest or {}).get(sleeve) or SleeveEvidence(sleeve)
        cal = acal.get(sleeve) or {}
        down, kill = boundaries_at(cal, n)
        coverages = {r.cost_coverage for r in rows}
        cost_coverage = "MEASURED" if coverages == {"MEASURED"} else "PARTIAL_EXIT_DEAL_ONLY"
        tier = cal.get("survivor_tier")
        out[sleeve] = SleeveEvidence(
            sleeve=sleeve,
            train_meanR=base.train_meanR, oos_meanR=base.oos_meanR, sealed_meanR=base.sealed_meanR,
            train_n=base.train_n, oos_n=base.oos_n, sealed_n=base.sealed_n,
            train_days=base.train_days, oos_days=base.oos_days, sealed_days=base.sealed_days,
            status=base.status, evidence_basis=base.evidence_basis,
            live_meanR=mean_r,
            live_n=n,
            live_day_blocks=_day_blocks(rows),
            live_r_series=tuple(r.realized_net_r for r in rows),
            live_boundary_curve=tuple(boundaries_at(cal, k) for k in range(1, n + 1)),
            live_gate_threshold_r=down,
            live_kill_threshold_r=kill,
            live_cost_coverage=cost_coverage,
            cost_true_survivor=_survives(tier),
            cost_true_tier=tier,
        )
    # Sleeves that are calibrated but never fired: emit them explicitly with live_n=0, so that
    # "no evidence" is visible in the output rather than being an absence a reader has to notice.
    for sleeve, cal in acal.items():
        if sleeve in out or not cal.get("calibrated"):
            continue
        base = (backtest or {}).get(sleeve) or SleeveEvidence(sleeve)
        tier = cal.get("survivor_tier")
        out[sleeve] = SleeveEvidence(
            sleeve=sleeve,
            train_meanR=base.train_meanR, oos_meanR=base.oos_meanR, sealed_meanR=base.sealed_meanR,
            train_n=base.train_n, oos_n=base.oos_n, sealed_n=base.sealed_n,
            train_days=base.train_days, oos_days=base.oos_days, sealed_days=base.sealed_days,
            status=base.status, evidence_basis=base.evidence_basis,
            live_meanR=None, live_n=0,
            cost_true_survivor=_survives(tier),
            cost_true_tier=tier,
        )
    # ...and sleeves with COST-TRUE BACKTEST evidence that neither fired live nor appear in the
    # calibration. Before AE the backtest half was seven hand-carried triples that were always a
    # subset of the calibrated set, so this case did not arise; AA's artifact carries 29 sleeves and
    # the calibration 11, and a sleeve the every-split bar would GATE must not disappear from the
    # recommendation because it has no live boundary.
    for sleeve, base in sorted((backtest or {}).items()):
        if sleeve in out:
            continue
        out[sleeve] = SleeveEvidence(
            sleeve=sleeve,
            train_meanR=base.train_meanR, oos_meanR=base.oos_meanR, sealed_meanR=base.sealed_meanR,
            train_n=base.train_n, oos_n=base.oos_n, sealed_n=base.sealed_n,
            train_days=base.train_days, oos_days=base.oos_days, sealed_days=base.sealed_days,
            status=base.status, evidence_basis=base.evidence_basis,
            live_meanR=None, live_n=0,
        )
    return out


def reconcile_cost(fill: RealizedFill, *, costs=None) -> dict:
    """Predicted (`cost_r`) vs realized cost for one fill. The tripwire input, not a substitute.

    **Only the charged terms are comparable.** ``cost_r().total_r`` is
    ``commission + swap + spread + slippage``, but a broker itemises only commission, swap and fee:
    spread and slippage are already inside the realized fill and exit prices, so they are counted
    in ``gross_r`` and cannot appear again as a charge. Comparing the full total against realized
    charges double-counts them — the first version of this function did exactly that and reported a
    0.0993 R mean absolute error, ~185x Session J's measured 0.000535 R, with the discrepancy being
    almost exactly the spread+slippage term it should never have included.

    Returns a dict with `status` so a symbol the cost layer cannot answer for becomes a published
    coverage fact rather than a silent zero.
    """
    from src.costs import CostTruthError, cost_r

    if fill.hold_hours is None:
        return {"status": "no_hold_time", "realized_cost_r": fill.realized_cost_r}
    entry_dt = _parse_utc(fill.entry_utc)
    for candidate in [c for c in (fill.broker_symbol, fill.symbol) if c]:
        try:
            b = cost_r(
                candidate,
                fill.account,
                fill.hold_hours,
                sl_distance_price=fill.risk_px,
                entry_price=fill.entry_px,
                side=fill.direction or "LONG",
                entry_utc=entry_dt,
                costs=costs,
            )
        except CostTruthError:
            continue
        except Exception:  # pragma: no cover - defensive: a reconciliation never breaks a rerate
            continue
        charged = b.commission_r.value + b.swap_r.value
        from src.costs import weakest
        return {
            "status": "reconciled",
            "symbol_resolved": candidate,
            "predicted_charged_r": charged,
            "predicted_commission_r": b.commission_r.value,
            "predicted_swap_r": b.swap_r.value,
            "predicted_total_r_incl_spread_slippage": b.total_r.value,
            "predicted_coverage": weakest(b.commission_r.coverage, b.swap_r.coverage).value,
            "realized_cost_r": fill.realized_cost_r,
            "abs_error_r": abs(charged - fill.realized_cost_r),
        }
    return {
        "status": "unpriceable_by_cost_layer",
        "symbols_tried": [c for c in (fill.broker_symbol, fill.symbol) if c],
        "realized_cost_r": fill.realized_cost_r,
        "note": "publish as a coverage gap; do not substitute a plausible number (F38)",
    }
