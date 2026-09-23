"""cost_true_splits.py — the actuator's backtest half, at broker truth instead of the legacy cost map.

WHAT THIS REPLACES
------------------
`learning_actuator.recommend()` scores a sleeve on its every-split evidence. Until this module that
evidence was seven hand-carried triples of the **CP4/CP5 replay** means, pasted into
`scripts/rerate_book_from_live.py`. Those numbers are priced by the legacy cost map — the one F38
found charged **zero commission** and F39 found credited tick erosion with the **wrong sign**. Session
R saw the problem, could not fix it (no cost-true splits existed) and bolted on a veto:
`cost_true_survivor is False` blocked any size-up. A veto is containment, not evidence.

Session AA's estate walk produced the replacement: `AA_SLEEVE_SPLITS_V1.json` — 29 sleeves (32 named,
3 with no generated trades) of **day-series net R at broker truth** (`BROKER_TRUE_COSTS_V1_1`), with
the walk-forward fold calendar and the four-term cost decomposition per day. This module turns that
artifact into `SleeveEvidence`.

THE PARTITION, AND WHY IT IS THIS ONE
-------------------------------------
AA emits an expanding-window walk-forward: 5 folds, each with its own `train_days` / `test_days` and
a 21-day embargo between them. Fold *k*'s train set is everything before fold *k*'s `oos_start`
minus the embargo, so the folds are nested and the test windows are disjoint and strictly ordered in
time. That maps onto the actuator's three splits exactly once:

  * **train**  = fold 1's `train_days` — the initial in-sample period, never tested against.
  * **oos**    = the union of `test_days` over folds 1..N-1 — the walk-forward out-of-sample.
  * **sealed** = fold N's `test_days` — the most recent forward slice, and the only one that is
                 out-of-sample for *every* earlier fold's fit.

`sealed` here means "the last forward fold", not a B7.5 sealed replay window and not the trainer
partition registry's `RESERVED_UNREAD`. It is named `sealed` because that is the slot in
`SleeveEvidence` it fills and the role it plays — the freshest evidence the sleeve could not have
been shaped by. Every day in all three sets is disjoint from the other two, asserted at load.

Days that fall in an embargo gap belong to no split and are dropped; that is the point of an
embargo. Measured: 0 dropped for 27 of 29 sleeves, 2 for `energy_agri`, 4 for `idxrev`.

DAY-BLOCKED n, AND WHY THE COUNT CHANGED
----------------------------------------
`MIN_N = 30` is a *sample* floor, and trades are not a sample of 30 independent things when they
cluster on days. R measured it on this very book: `sub_xvol_pullback`'s 90 validated trades sit on
33 dates with up to 12 on one day and lag-1 autocorrelation 0.511; `crypto`'s 104 on 67 dates,
rho 0.441. R applied the day-block correction to the live *null* and left the admission floor
counting raw trades — so a split could clear a 30-trade bar on 13 days.

Because AA's artifact is a **day** series, both sides can now be counted the same way, which is what
FOURTH_REVIEW section 4.2 asks for when it says the raise bar is "live n >= 30 (day-blocked, the same bar a
backtest split must clear)". Every split this module emits therefore carries both counts, and the
actuator admits on the day-blocked one. It changes verdicts, and the largest change is honest:
`sub_xvol_pullback` clears 30 trades on both its oos (35) and sealed (37) splits and clears 30 days
on neither (19 and 13), so it moves from a size-up to INSUFFICIENT_EVIDENCE. It is the sleeve
FOURTH_REVIEW's own concentration warning names.

WHAT THIS MODULE DOES NOT DO
----------------------------
It does not re-cost anything, re-simulate anything, or choose an exit. It sums a day series AA
already published and reports the fold membership it already published. The look-ahead AA declares
on that artifact (a 2026-06-18..07-24 spread snapshot charged to every era, so pre-2026 trades are
UNDER-costed) travels with the evidence into `SleeveEvidence.evidence_basis` and out into every
receipt, because a reader of a recommendation is entitled to it.
"""
from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

from src.components.ultimate_book.learning_actuator import SleeveEvidence

REPO = Path(__file__).resolve().parents[3]
DEFAULT_SPLITS = REPO / "docs/audits/fable5-vision-audit-20260725/phase6/receipts/AA_SLEEVE_SPLITS_V1.json"

SPLIT_NAMES = ("train", "oos", "sealed")


@dataclass(frozen=True)
class SplitStats:
    """One split of one sleeve, at broker truth."""
    split: str
    n_days: int
    n_trades: int
    net_r: float                      # total net R over the split
    mean_r: Optional[float]           # per TRADE, the unit the actuator's rule is written in
    mean_r_per_day: Optional[float]   # per DAY, the unit the day-blocked count belongs to
    first_day: Optional[str]
    last_day: Optional[str]
    cost_r: dict                      # commission/spread/slippage/swap totals in R

    def as_dict(self) -> dict:
        d = dict(self.__dict__)
        d["cost_r"] = dict(self.cost_r)
        return d


def load_splits(path: Path | str | None = None) -> dict:
    """Read `AA_SLEEVE_SPLITS_V1.json`. Refuses to guess if it is absent."""
    p = Path(path or DEFAULT_SPLITS)
    if not p.is_file():
        raise FileNotFoundError(
            f"no cost-true sleeve splits at {p}. This is Session AA's estate-walk artifact and it "
            "is the actuator's backtest evidence; the alternative is the legacy-cost CP4/CP5 "
            "numbers F38/F39 discredited, so there is no fallback and none is invented here."
        )
    doc = json.loads(p.read_text())
    schema = doc.get("schema")
    if schema != "gtos.walkforward.sleeve_splits.v1":
        raise ValueError(f"{p} is schema {schema!r}, not gtos.walkforward.sleeve_splits.v1")
    return doc


def partition_days(sleeve: dict) -> dict[str, list[str]]:
    """Fold calendar -> {'train': [...], 'oos': [...], 'sealed': [...]}, disjoint and ordered.

    Raises if the three sets overlap. They cannot, given an expanding walk-forward with disjoint
    test windows — but "cannot" is what a silent double-count always looks like beforehand, and a
    day counted in both train and sealed would let a sleeve pass the every-split bar on one
    observation wearing two hats.
    """
    folds = sleeve.get("folds") or []
    if len(folds) < 2:
        return {"train": [], "oos": [], "sealed": []}
    train = [str(d) for d in folds[0].get("train_days") or []]
    sealed = [str(d) for d in folds[-1].get("test_days") or []]
    oos: list[str] = []
    for f in folds[:-1]:
        oos.extend(str(d) for d in f.get("test_days") or [])
    a, b, c = set(train), set(oos), set(sealed)
    overlap = (a & b) | (a & c) | (b & c)
    if overlap:
        raise ValueError(
            f"fold calendar for {sleeve.get('sleeve') or '?'} puts {len(overlap)} day(s) in more "
            f"than one split (e.g. {sorted(overlap)[:3]}); the splits would double-count them"
        )
    return {"train": sorted(a), "oos": sorted(b), "sealed": sorted(c)}


def _stats(split: str, sleeve: dict, days: list[str]) -> SplitStats:
    net = sleeve.get("daily_net_r") or {}
    cnt = sleeve.get("daily_trade_counts") or {}
    comp = sleeve.get("daily_cost_components") or {}
    present = [d for d in days if d in net]
    total_r = sum(float(net[d]) for d in present)
    n_tr = sum(int(cnt.get(d, 0)) for d in present)
    cost: dict = {}
    for d in present:
        for k, v in (comp.get(d) or {}).items():
            if k == "n":
                continue
            cost[k] = cost.get(k, 0.0) + float(v)
    return SplitStats(
        split=split,
        n_days=len(present),
        n_trades=n_tr,
        net_r=round(total_r, 6),
        mean_r=(total_r / n_tr) if n_tr else None,
        mean_r_per_day=(total_r / len(present)) if present else None,
        first_day=present[0] if present else None,
        last_day=present[-1] if present else None,
        cost_r={k: round(v, 6) for k, v in sorted(cost.items())},
    )


def sleeve_splits(sleeve: dict) -> dict[str, SplitStats]:
    """Per-split broker-true statistics for one sleeve entry of the artifact."""
    days = partition_days(sleeve)
    return {s: _stats(s, sleeve, days[s]) for s in SPLIT_NAMES}


def _registry_status(name: str) -> str:
    """The research registry status string, if the runtime knows this sleeve.

    Decorative — `recommend()` puts it in the GATE reason and nothing keys off it. Imported lazily
    so a loader used in a research script never drags the live admission module in as a side effect.
    """
    try:
        from src.components.ultimate_book import admission as _adm
    except Exception:  # pragma: no cover - the status is a label, never a decision
        return ""
    for reg in ("SLEEVE_REGISTRY", "CLEAN3_REGISTRY", "CLEAN4_REGISTRY"):
        spec = getattr(_adm, reg, {}).get(name)
        if spec is not None:
            return getattr(spec, "status", "") or ""
    return ""


def build_cost_true_evidence(
    doc: dict | None = None,
    *,
    path: Path | str | None = None,
    statuses: Optional[dict] = None,
) -> dict[str, SleeveEvidence]:
    """Cost-true `SleeveEvidence` per sleeve, keyed by sleeve name.

    Sleeves the walk could not generate (`available: false`) are **omitted**, not emitted with
    zeros: an absent sleeve reports INSUFFICIENT_EVIDENCE downstream, whereas a sleeve carrying
    `mean_r = 0.0` on `n = 0` would read as a measured flat result and could be gated by the
    every-split bar. `vp_euidx_pocgrav` is the live case — redacted_account's fourth UNCONDITIONAL
    survivor, generating literally nothing today, and exactly the sleeve that must not be gated
    for being unmeasured.
    """
    doc = doc if doc is not None else load_splits(path)
    basis = f"cost_true:{doc.get('cost_artifact') or 'unknown'}"
    out: dict[str, SleeveEvidence] = {}
    for name, sleeve in sorted((doc.get("sleeves") or {}).items()):
        if not sleeve.get("available"):
            continue
        st = sleeve_splits(sleeve)
        status = (statuses or {}).get(name)
        if status is None:
            status = _registry_status(name)
        out[name] = SleeveEvidence(
            sleeve=name,
            train_meanR=st["train"].mean_r,
            oos_meanR=st["oos"].mean_r,
            sealed_meanR=st["sealed"].mean_r,
            train_n=st["train"].n_trades,
            oos_n=st["oos"].n_trades,
            sealed_n=st["sealed"].n_trades,
            train_days=st["train"].n_days,
            oos_days=st["oos"].n_days,
            sealed_days=st["sealed"].n_days,
            status=status,
            evidence_basis=basis,
        )
    return out


def evidence_table(doc: dict | None = None, *, path: Path | str | None = None) -> dict:
    """The full per-sleeve split detail, for receipts. Superset of `build_cost_true_evidence`."""
    doc = doc if doc is not None else load_splits(path)
    rows: dict = {}
    for name, sleeve in sorted((doc.get("sleeves") or {}).items()):
        if not sleeve.get("available"):
            rows[name] = {"available": False, "reason": sleeve.get("reason")}
            continue
        st = sleeve_splits(sleeve)
        rows[name] = {
            "available": True,
            "cost_basis": sleeve.get("cost_basis"),
            "n_trades_total": sleeve.get("n_trades"),
            "coverage": sleeve.get("coverage"),
            "splits": {s: st[s].as_dict() for s in SPLIT_NAMES},
        }
    return {
        "source": str(Path(path or DEFAULT_SPLITS)),
        "cost_artifact": doc.get("cost_artifact"),
        "cost_look_ahead": doc.get("cost_look_ahead"),
        "spec_sha256": doc.get("spec_sha256"),
        "sleeves": rows,
    }
