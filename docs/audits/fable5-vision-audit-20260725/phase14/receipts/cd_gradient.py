"""Session CD, CD-5 -- the gradient pass: does the REPAIRED stack move the map?

AW mined the sealed pool and found **zero of 212 declared cells** with a positive
train mean, on any axis, at any cut. That result was measured on the OLD engine:
commission identically zero, swap priced over an 8-hour hold the path cannot
reach. This asks the same question of the regenerated pool and reports the
difference, which is the only honest way to know whether "no cell separates" was
a statement about the mechanism or about the cost model.

## What is declared here, before any cell is scored

* **The split.** Chronological. The pool's trading days, first 13 TRAIN, last 8
  HOLDOUT -- AW's rule, restated rather than re-chosen, because a random split
  over one month puts the same regime on both sides.
* **The cut rules.** Categorical level-wise with a minimum train count;
  numeric by TRAIN tertiles (q33/q67 computed on TRAIN only). One rule per kind,
  fixed in advance. AO's pair admission died on an undeclared median cut and the
  wave-11 agreement makes the cut RULE declarable, not just the axis.
* **The outcome.** Both `net` (`opportunity_net_proxy_r`, the pool's own column,
  which under a repaired arm already carries the repaired cost) and `gross`
  (`net + cost_r`). The gross view is the one that matters here: §0 finding 7
  says the deficit is pre-cost, and a cell that is gross-positive is the only
  kind that could ever survive a cost repair.

## What this DOES NOT do

It bills nothing. These are TRAIN/VAL looks on a VAL surface, logged to the
iteration ledger, and the sealed gate is not run. No cell that comes out of here
is an admission, a candidate, or a graduation -- if one ever looked like it, it
would need a declared family, a graduation, and the ratified rule, which is a
different act by a different session.
"""

from __future__ import annotations

import argparse
import collections
import gzip
import json
import math
from pathlib import Path
from typing import Any, Iterable

#: AW's split, restated.
N_TRAIN_DAYS = 13
#: AW's minimum cell sizes.
MIN_TRAIN_ROWS = 200
MIN_HOLDOUT_ROWS = 100

#: Categorical axes worth cutting. Chosen from the columns AW's own census found
#: informative (his best five cells) plus the ones a cost repair could plausibly
#: move. Declared here so the list is auditable rather than emergent.
CATEGORICAL_AXES = (
    "symbol",
    "final_blocker_class",
    "miss_reason",
    "selector_reason",
    "risk_finalizer_reason",
    "origin_family",
    "side",
    "broker_pretrade_cost_executable",
    "pretrade_cost_packet_status",
)

#: Numeric axes, cut at TRAIN tertiles.
NUMERIC_AXES = (
    "cost_r",
    "spread_r",
    "commission_r",
    "swap_cost_r",
    "entry_price",
)


def rows(path: Path) -> Iterable[dict[str, Any]]:
    opener = gzip.open if str(path).endswith(".gz") else open
    with opener(path, "rt", encoding="utf-8") as fh:  # type: ignore[operator]
        for line in fh:
            line = line.strip()
            if line:
                yield json.loads(line)


def _num(value: Any) -> float | None:
    try:
        out = float(value)
    except (TypeError, ValueError):
        return None
    return None if math.isnan(out) else out


def load(path: Path) -> list[dict[str, Any]]:
    out = []
    for row in rows(path):
        net = _num(row.get("opportunity_net_proxy_r"))
        if net is None:
            continue
        cost = _num(row.get("cost_r"))
        row["_net"] = net
        row["_gross"] = (net + cost) if cost is not None else None
        row["_day"] = str(row.get("decision_time_utc") or "")[:10]
        out.append(row)
    return out


def split(pool: list[dict[str, Any]]) -> tuple[set[str], set[str]]:
    days = sorted({r["_day"] for r in pool if r["_day"]})
    return set(days[:N_TRAIN_DAYS]), set(days[N_TRAIN_DAYS:])


def score(subset: list[dict[str, Any]], outcome: str) -> dict[str, Any]:
    values = [r[outcome] for r in subset if r.get(outcome) is not None]
    if not values:
        return {"n": 0, "mean": None, "precision": None, "day_positive_frac": None}
    by_day: dict[str, list[float]] = collections.defaultdict(list)
    for r in subset:
        if r.get(outcome) is not None:
            by_day[r["_day"]].append(r[outcome])
    day_means = [sum(v) / len(v) for v in by_day.values()]
    return {
        "n": len(values),
        "mean": round(sum(values) / len(values), 6),
        "precision": round(sum(1 for v in values if v > 0) / len(values), 6),
        "day_positive_frac": round(
            sum(1 for m in day_means if m > 0) / len(day_means), 6
        ),
        "n_days": len(day_means),
    }


def cells(pool: list[dict[str, Any]], train_days: set[str]) -> list[dict[str, Any]]:
    train = [r for r in pool if r["_day"] in train_days]
    out: list[dict[str, Any]] = []

    for axis in CATEGORICAL_AXES:
        counts = collections.Counter(str(r.get(axis)) for r in train)
        for level, n in counts.items():
            if n < MIN_TRAIN_ROWS:
                continue
            out.append(
                {
                    "axis": axis,
                    "kind": "categorical",
                    "cut": f"{axis}=={level}",
                    "match": (lambda a, lv: (lambda r: str(r.get(a)) == lv))(axis, level),
                }
            )

    for axis in NUMERIC_AXES:
        values = sorted(v for v in (_num(r.get(axis)) for r in train) if v is not None)
        if len(values) < MIN_TRAIN_ROWS * 3:
            continue
        q33 = values[len(values) // 3]
        q67 = values[2 * len(values) // 3]
        if q33 == q67:
            continue
        for label, lo, hi in (
            ("low", None, q33),
            ("mid", q33, q67),
            ("high", q67, None),
        ):
            out.append(
                {
                    "axis": axis,
                    "kind": "numeric_train_tertile",
                    "cut": f"{axis}:{label}"
                    + f" ({'' if lo is None else round(lo, 6)}"
                    + f"..{'' if hi is None else round(hi, 6)})",
                    "match": (
                        lambda a, l, h: (
                            lambda r: (
                                (v := _num(r.get(a))) is not None
                                and (l is None or v >= l)
                                and (h is None or v < h)
                            )
                        )
                    )(axis, lo, hi),
                }
            )
    return out


def run(pool: list[dict[str, Any]], label: str) -> dict[str, Any]:
    train_days, holdout_days = split(pool)
    train = [r for r in pool if r["_day"] in train_days]
    holdout = [r for r in pool if r["_day"] in holdout_days]
    declared = cells(pool, train_days)

    results = []
    for spec in declared:
        match = spec.pop("match")
        tr = [r for r in train if match(r)]
        ho = [r for r in holdout if match(r)]
        entry = dict(spec)
        for outcome in ("_net", "_gross"):
            entry[outcome.strip("_") + "_train"] = score(tr, outcome)
            entry[outcome.strip("_") + "_holdout"] = score(ho, outcome)
        results.append(entry)

    def funnel(outcome: str) -> dict[str, Any]:
        f1 = [
            c
            for c in results
            if (c[f"{outcome}_train"]["mean"] or -9) > 0
            and c[f"{outcome}_train"]["n"] >= MIN_TRAIN_ROWS
        ]
        f2 = [c for c in f1 if (c[f"{outcome}_holdout"]["mean"] or -9) > 0]
        f3 = [c for c in f2 if (c[f"{outcome}_holdout"]["day_positive_frac"] or 0) >= 0.5]
        return {
            "declared_cells": len(results),
            "F1_train_mean_positive": len(f1),
            "F2_holdout_mean_positive": len(f2),
            "F3_holdout_day_positive_ge_half": len(f3),
            "survivors": [c["cut"] for c in f3],
            "best_by_train_mean": sorted(
                (
                    {
                        "cut": c["cut"],
                        "train_n": c[f"{outcome}_train"]["n"],
                        "train_mean": c[f"{outcome}_train"]["mean"],
                        "train_precision": c[f"{outcome}_train"]["precision"],
                        "holdout_mean": c[f"{outcome}_holdout"]["mean"],
                    }
                    for c in results
                    if c[f"{outcome}_train"]["n"] >= MIN_TRAIN_ROWS
                ),
                key=lambda row: -(row["train_mean"] if row["train_mean"] is not None else -9),
            )[:10],
        }

    return {
        "label": label,
        "n_rows": len(pool),
        "train_days": sorted(train_days),
        "holdout_days": sorted(holdout_days),
        "baseline": {
            "net_train": score(train, "_net"),
            "net_holdout": score(holdout, "_net"),
            "gross_train": score(train, "_gross"),
            "gross_holdout": score(holdout, "_gross"),
        },
        "funnel_net": funnel("net"),
        "funnel_gross": funnel("gross"),
    }


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--pool", action="append", required=True,
                    help="label=path.jsonl.gz; repeat for each arm")
    ap.add_argument("--out", required=True)
    ns = ap.parse_args()

    payload: dict[str, Any] = {
        "schema": "gtos.session_cd.gradient_map.v1",
        "surface": "VAL",
        "disclosure": (
            "VAL is the survivor book's own selection surface. Ranking and "
            "gradient checks only; nothing here is an admission and nothing "
            "here bills the candidate family."
        ),
        "declared_before_scoring": {
            "split": f"chronological, first {N_TRAIN_DAYS} trading days TRAIN",
            "min_train_rows": MIN_TRAIN_ROWS,
            "min_holdout_rows": MIN_HOLDOUT_ROWS,
            "categorical_axes": list(CATEGORICAL_AXES),
            "numeric_axes": list(NUMERIC_AXES),
            "numeric_cut_rule": "TRAIN tertiles (q33/q67 computed on TRAIN only)",
            "outcomes": ["net = opportunity_net_proxy_r", "gross = net + cost_r"],
        },
        "maps": {},
    }
    for item in ns.pool:
        label, _, path = item.partition("=")
        pool = load(Path(path))
        payload["maps"][label] = run(pool, label)
        m = payload["maps"][label]
        print(
            f"{label:28s} rows={m['n_rows']:6d} "
            f"net_train={m['baseline']['net_train']['mean']:+.6f} "
            f"gross_train={m['baseline']['gross_train']['mean']:+.6f} "
            f"| F1net={m['funnel_net']['F1_train_mean_positive']:3d} "
            f"F1gross={m['funnel_gross']['F1_train_mean_positive']:3d} "
            f"of {m['funnel_net']['declared_cells']}"
        )
    Path(ns.out).write_text(json.dumps(payload, indent=1, default=str))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
