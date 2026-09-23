#!/usr/bin/env python3
"""l1_lib — shared loaders + the exact cell walk used by every l1 pass."""
from __future__ import annotations
import gzip, json, os, math

HERE = os.path.dirname(os.path.abspath(__file__))
TOUCH = os.path.join(HERE, "l1_TOUCH_INDEX_V1.jsonl.gz")

FAV = [0.1, 0.25, 0.5, 0.75, 1.0, 1.25, 1.5, 1.75, 2.0, 2.25, 2.5, 3.0, 3.5, 4.0, 5.0, 6.0, 8.0, 10.0]
ADV = [0.25, 0.5, 0.75, 1.0, 1.25, 1.5, 1.75, 2.0, 2.5, 3.0]
FI = {v: i for i, v in enumerate(FAV)}
AI = {v: i for i, v in enumerate(ADV)}

T_GRID = [0.5, 0.75, 1.0, 1.25, 1.5, 2.0, 2.5, 3.0, 4.0, 5.0]
S_GRID = [0.5, 0.75, 1.0, 1.25, 1.5, 2.0]


def load(path=TOUCH):
    with gzip.open(path, "rt") as fh:
        return [json.loads(l) for l in fh if l.strip()]


def cell(rec, T, S, conv="r"):
    """Exact first-touch exit for target +T / stop -S under fill convention conv
    ('r'=REAL, 's'=STRICT, 'b'=BLIND). Ties inside a bar go to the STOP.
    Returns (r, reason, exit_bar_index_0based_or_None)."""
    tf = rec.get("tf_" + conv)
    if tf is None:
        return 0.0, "no_fill", None
    ta = rec["ta_" + conv]
    iT = tf[FI[T]] if T is not None else None
    iS = ta[AI[S]] if S is not None else None
    if iS is not None and (iT is None or iS <= iT):
        return -S, "stop", iS
    if iT is not None:
        return T, "target", iT
    return rec["cls_end"], "path_end", rec["n"] - 1


def mean(xs):
    xs = list(xs)
    return sum(xs) / len(xs) if xs else float("nan")


def q(xs, p):
    xs = sorted(x for x in xs if x is not None)
    if not xs:
        return float("nan")
    i = p * (len(xs) - 1)
    lo, hi = int(math.floor(i)), int(math.ceil(i))
    return xs[lo] if lo == hi else xs[lo] + (xs[hi] - xs[lo]) * (i - lo)


def stats(xs):
    xs = [x for x in xs if x is not None]
    n = len(xs)
    if n == 0:
        return {"n": 0}
    m = sum(xs) / n
    sd = (sum((x - m) ** 2 for x in xs) / n) ** 0.5 if n > 1 else 0.0
    return {"n": n, "mean": round(m, 6), "sd": round(sd, 6),
            "p05": round(q(xs, .05), 6), "p25": round(q(xs, .25), 6),
            "median": round(q(xs, .5), 6), "p75": round(q(xs, .75), 6),
            "p90": round(q(xs, .90), 6), "p95": round(q(xs, .95), 6),
            "min": round(min(xs), 6), "max": round(max(xs), 6)}


def pop(recs, which):
    if which == "ALL":
        return recs
    if which == "TAKEABLE":
        return [r for r in recs if r["born"] != "born_past_stop"]
    if which == "TAKEABLE_FIRSTEM":
        return [r for r in recs if r["born"] != "born_past_stop" and r["first_em"]]
    if which == "PASTSTOP":
        return [r for r in recs if r["born"] == "born_past_stop"]
    raise ValueError(which)
