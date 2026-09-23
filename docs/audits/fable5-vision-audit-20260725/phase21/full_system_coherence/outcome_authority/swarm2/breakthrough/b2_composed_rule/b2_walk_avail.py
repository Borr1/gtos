#!/usr/bin/env python3
"""B2 step 1: the composed decision statistic, walked forward day by day.

Frozen spec: B2_SPEC_V1.json (sha256 6d4ebdea10fd1b8249e9d94c62504d2e2ff80ff5eee98efe041d908dae82e62e)

For every trading day k in feb -> apr -> may -> jun -> jul, fit on the dev+January
bootstrap plus every day strictly before k:

  stage A  P(fill | x)      LogisticRegression(C=0.1) on resolved-eligible LIMIT rows
                            (MARKET is P=1.0 exactly, by contract)
  stage B  E[net | fill, x] Ridge(alpha=10.0) on resolved-eligible FILLED rows

  composed = p_fill * e_net_fill

Identical feature basis, preprocessing, and sample-weight rule to the shipped
ridge (w21_predecision_ridge.CAT/NUM/make_model/weights).  Also emits the
hierarchical Jeffreys cell fill probability (geometry_bound_outcome_model's
estimator) for arm A6.

Writes scores_daily.pkl.gz -> {occurrence_key: {...}}
"""
import gzip
import importlib.util
import json
import pickle
import sys
import time
from collections import Counter
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression, Ridge
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler

WT = Path("/Users/borr/GTOSActive/worktrees/wave21-full-system-coherence-20260809")
sys.path.insert(0, str(WT))
OA = WT / "docs/audits/fable5-vision-audit-20260725/phase21/full_system_coherence/outcome_authority"
CACHE = Path("/private/tmp/w21-puzzle-cache")
HERE = Path("/Users/borr/.claude/jobs/adb9e69b/tmp/b2")
import datetime as _dt
def _end(row):
    v = row.get("label_span_end_utc") or row.get("expiry_utc")
    return _dt.datetime.fromisoformat(str(v).replace("Z", "+00:00"))
def _daystart(day):
    return _dt.datetime.fromisoformat(day + "T00:00:00+00:00")
T0 = time.time()

RESOLVED_STATUS_TO_STATE = {
    "RESOLVED_NO_FILL": "NO_FILL",
    "RESOLVED_FILLED_TARGET": "TARGET",
    "RESOLVED_FILLED_STOP": "STOP",
    "RESOLVED_FILLED_TIME_STOP": "TIME_STOP",
}
MAX_COST_R = 0.20
JEFFREYS_MIN_ATTEMPTS = 100  # geometry_bound_outcome_model.LIMIT_MIN_RESOLVED_ATTEMPTS


def log(**kw):
    print(json.dumps({"t": round(time.time() - T0, 1), **kw}, sort_keys=True), flush=True)


def lm(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


# ---------------------------------------------------------------- feature basis
# CAT/NUM copied by import, not retyped, so the basis is provably identical.
_ridge_src = Path("/private/tmp/w21_predecision_ridge.py").read_text()
_ns: dict = {}
exec(
    _ridge_src[_ridge_src.index("CAT = ["): _ridge_src.index("def canonical_hash")],
    {"np": np},
    _ns,
)
CAT, NUM = _ns["CAT"], _ns["NUM"]
assert len(CAT) == 14 and len(NUM) == 29, (len(CAT), len(NUM))


def state_of(row):
    status = str(row.get("lifecycle_label_status") or "")
    if status in RESOLVED_STATUS_TO_STATE:
        return RESOLVED_STATUS_TO_STATE[status]
    if status.startswith("CENSORED_"):
        return None
    raise ValueError(f"unknown lifecycle status: {status!r}")


def finite(value):
    try:
        value = float(value)
    except (TypeError, ValueError):
        return None
    return value if np.isfinite(value) else None


def is_eligible(row):
    if not row.get("predecision_geometry_valid"):
        return False
    cost = finite(row.get("cost_r"))
    return cost is not None and cost <= MAX_COST_R


def frame(rows):
    data = pd.DataFrame([{key: row.get(key) for key in CAT + NUM} for row in rows])
    for key in CAT:
        data[key] = data[key].fillna("MISSING").astype(str)
    for key in NUM:
        data[key] = pd.to_numeric(data[key], errors="coerce")
    return data


def weights_from(window_ids):
    counts = Counter(window_ids)
    return np.asarray([1.0 / counts[w] for w in window_ids], dtype=float)


def pre():
    numeric = Pipeline([
        ("impute", SimpleImputer(strategy="constant", fill_value=0.0, add_indicator=True)),
        ("scale", StandardScaler()),
    ])
    return ColumnTransformer([
        ("cat", OneHotEncoder(handle_unknown="ignore"), CAT),
        ("num", numeric, NUM),
    ], sparse_threshold=0.3)


def make_ridge():
    return Pipeline([("pre", pre()), ("ridge", Ridge(alpha=10.0, solver="lsqr"))])


def make_logit():
    return Pipeline([
        ("pre", pre()),
        ("logit", LogisticRegression(C=0.1, solver="lbfgs", max_iter=1000)),
    ])


# ---------------------------------------------------------------- Jeffreys cells
def jeffreys_key(row, level):
    return (
        str(row["proposed_order_type"]),
        str(row["origin_family"]),
        str(row["utc_session"]),
    )[: level + 1]


def jeffreys_fill(tables, row):
    """Hierarchical Jeffreys P(fill): deepest cell with >=100 resolved attempts."""
    if row["proposed_order_type"] == "MARKET":
        return 1.0
    for level in (2, 1, 0):
        cell = tables.get((level, jeffreys_key(row, level)))
        if cell is not None and cell["attempts"] >= JEFFREYS_MIN_ATTEMPTS:
            return (2 * cell["fills"] + 1) / (2 * cell["attempts"] + 2)
    return None


def jeffreys_update(tables, rows):
    for row in rows:
        state = state_of(row)
        if state is None:
            continue
        for level in range(3):
            cell = tables.setdefault(
                (level, jeffreys_key(row, level)), {"attempts": 0, "fills": 0}
            )
            cell["attempts"] += 1
            if state != "NO_FILL":
                cell["fills"] += 1


# ---------------------------------------------------------------- the walk
def main():
    prereg = json.loads((OA / "JUNE_JULY_MARKET_TOP_CHOICE_PREREG_V1_3.json").read_text())
    tr = prereg["training"]
    day_order = [
        ("feb", tr["february_days"]),
        ("apr", tr["april_days"]),
        ("may", tr["may_days"]),
        ("jun", next(w["days"] for w in prereg["validation"]["windows"]
                     if w["window_id"] == "june_2026")),
        ("jul", next(w["days"] for w in prereg["validation"]["windows"]
                     if w["window_id"] == "july_2026")),
    ]

    with gzip.open(HERE / "bootstrap_rows.pkl.gz", "rb") as fh:
        bootstrap = pickle.load(fh)
    log(stage="bootstrap_loaded", rows=len(bootstrap))

    # accumulated training state, kept as per-day frames so no frame is rebuilt
    limit_frames, limit_y, limit_w = [], [], []
    fill_frames, fill_y, fill_w = [], [], []
    jeff: dict = {}

    def absorb(rows):
        """Append resolved-eligible rows to both training subsets."""
        res = [r for r in rows if is_eligible(r) and state_of(r) is not None]
        jeffreys_update(jeff, res)
        lim = [r for r in res if r["proposed_order_type"] == "LIMIT"]
        fil = [r for r in res if state_of(r) != "NO_FILL"]
        if lim:
            limit_frames.append(frame(lim))
            limit_y.extend(1 if state_of(r) != "NO_FILL" else 0 for r in lim)
            limit_w.extend(r["decision_window_id"] for r in lim)
        if fil:
            fill_frames.append(frame(fil))
            fill_y.extend(float(r.get("terminal_net_r") or 0.0) for r in fil)
            fill_w.extend(r["decision_window_id"] for r in fil)

    absorb(bootstrap)
    del bootstrap
    log(stage="bootstrap_absorbed", limit_rows=len(limit_y), fill_rows=len(fill_y))

    scores = {}
    holding: list = []   # resolved rows whose label span has not yet ended
    for month, days in day_order:
        with gzip.open(CACHE / f"rows_{month}.pkl.gz", "rb") as fh:
            month_rows = pickle.load(fh)
        by_day = {}
        for row in month_rows:
            by_day.setdefault(row["trading_day"], []).append(row)
        del month_rows

        for day in days:
            cutoff = _daystart(day)
            ready = [r for r in holding if _end(r) < cutoff]
            if ready:
                absorb(ready)
                holding = [r for r in holding if _end(r) >= cutoff]
            rows = by_day.get(day, [])
            test = [r for r in rows if is_eligible(r)]
            if test:
                t_fit = time.time()
                ltrain = pd.concat(limit_frames, ignore_index=True)
                ftrain = pd.concat(fill_frames, ignore_index=True)

                logit = make_logit()
                logit.fit(ltrain, np.asarray(limit_y, dtype=int),
                          logit__sample_weight=weights_from(limit_w))
                ridge = make_ridge()
                ridge.fit(ftrain, np.asarray(fill_y, dtype=float),
                          ridge__sample_weight=weights_from(fill_w))
                fit_s = time.time() - t_fit

                tframe = frame(test)
                p_fill = logit.predict_proba(tframe)[:, 1]
                e_net = ridge.predict(tframe)
                for i, row in enumerate(test):
                    market = row["proposed_order_type"] == "MARKET"
                    pf = 1.0 if market else float(p_fill[i])
                    en = float(e_net[i])
                    jf = jeffreys_fill(jeff, row)
                    scores[row["candidate_occurrence_key"]] = {
                        "p_fill": pf,
                        "p_fill_model": float(p_fill[i]),
                        "e_net_given_fill": en,
                        "composed": pf * en,
                        "jeffreys_fill": jf,
                        "composed_jeffreys": (jf * en) if jf is not None else None,
                    }
                log(stage="day", month=month, day=day, n_test=len(test),
                    limit_train=len(limit_y), fill_train=len(fill_y),
                    fit_s=round(fit_s, 1))
            holding.extend(r for r in rows
                           if is_eligible(r) and state_of(r) is not None)
        del by_day

    with gzip.open(HERE / "scores_avail.pkl.gz", "wb") as fh:
        pickle.dump(scores, fh, protocol=5)
    log(stage="DONE", n_scores=len(scores))


if __name__ == "__main__":
    main()
