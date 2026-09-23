#!/usr/bin/env python3
"""Phase 0 T1 — the LIVE-REALISTIC fill arm, with no change to the labeler.

`resolve_post_submission_m1_lifecycle` refuses the submission bar as causal and
fills MARKET at the OPEN of the *first complete successor* M1 bar, i.e. 60 s after
the decision instant. A live book places its order at the decision instant and is
filled within about a second.

That difference is obtainable without touching the resolver: hand it a submission
time one minute EARLIER. The submission bar then becomes the pre-decision minute and
the first complete successor becomes the DECISION minute, so the modelled fill is the
executable-side open at the decision instant. Expiry, horizon, barriers, spreads,
quote sides and every censoring rule are unchanged.

Three arms per candidate:
  orig_live  original contract, decision-instant fill
  inv_live   inverted contract, decision-instant fill
and the paired 60 s arms already computed by p0_walk.py.
"""
from __future__ import annotations

import bisect
import datetime as dt
import gzip
import json
import os
import pickle
import sys
import time
from pathlib import Path

sys.path.insert(0, "/private/tmp/phase0-inversion")
import p0_walk as W  # noqa: E402

from src.research_infra.walkforward.quote_side import (  # noqa: E402
    BarQuote,
    resolve_post_submission_m1_lifecycle,
)

OUT = Path("/private/tmp/phase0-inversion")
MINUTE = dt.timedelta(minutes=1)
T0 = time.time()


def log(**kw):
    print(json.dumps({"t": round(time.time() - T0, 1), **kw}, sort_keys=True), flush=True)


def walk_live(raw, sources, *, inverted: bool):
    symbol = str(raw["symbol"])
    source, times, bars, spreads = sources[symbol]
    decision = W.m._utc(str(raw["decision_time_utc"]))
    submission = decision - MINUTE  # so the DECISION minute is the first successor
    expiry = W.m._utc(str(raw["limit_first_expiry_utc"]))
    start = max(0, bisect.bisect_right(times, submission) - 1)
    end = min(len(times), bisect.bisect_left(times, expiry) + 1)
    entry = float(raw["entry_price"])
    stop = float(raw["stop_loss"])
    target = float(raw["take_profit_1"])
    direction = 1 if str(raw["side"]).upper() == "LONG" else -1
    if inverted:
        direction, stop, target = -direction, target, stop
    risk = abs(entry - stop)
    return resolve_post_submission_m1_lifecycle(
        bars[start:end],
        m1_open_times_utc=times[start:end],
        direction=direction,
        proposed_order_type="MARKET",
        submission_or_ack_time_utc=submission,
        expiry_utc=expiry,
        required_horizon_utc=expiry,
        approved_entry_price=entry,
        approved_stop_price=stop,
        approved_target_price=target,
        approved_risk_distance=risk,
        m1_price_basis=BarQuote.BID,
        spread_by_bar=spreads[start:end],
        source_interval_verified=True,
        symbol_spec_hash_sha256=W.m.SPEC_SHA256,
        spread_source_hash_sha256=W.m.SPREAD_SHA256,
    )


def main():
    months = sys.argv[1].split(",") if len(sys.argv) > 1 else list(W.WINDOWS)
    families = set(W.MARKET_FAMILIES)
    for month in months:
        window_id, root, expected_root, days = W.WINDOWS[month]
        _root_sha, sources = W.r3.load_m1_sources(
            W.MANIFEST_DIR / f"{window_id}.json", expected_root
        )
        log(stage="m1_loaded", month=month)
        out = []
        for day in days:
            for raw in W.raw_rows_for(root, day):
                if str(raw["origin_family"]) not in families:
                    continue
                if W.m._order_type(raw) != "MARKET":
                    continue
                entry = float(raw["entry_price"])
                risk = abs(entry - float(raw["stop_loss"]))
                risk_inv = abs(entry - float(raw["take_profit_1"]))
                deductible = sum(
                    float(raw.get(field) or 0.0)
                    for field in ("expected_slippage_r", "swap_cost_r", "commission_r")
                )
                row = {"key": str(raw["canonical_replay_candidate_instance_key"])}
                for name, inverted, unit in (
                    ("orig_live", False, risk),
                    ("inv_live", True, risk_inv),
                ):
                    res = walk_live(raw, sources, inverted=inverted)
                    status = res.lifecycle_label_status
                    gross = (
                        float(res.terminal_gross_r)
                        if status.startswith("RESOLVED_FILLED_")
                        else None
                    )
                    ded = deductible * (risk / unit) if unit > 0 else None
                    row[name] = {
                        "status": status,
                        "state": res.terminal_state,
                        "gross": gross,
                        "net": None if gross is None else gross - ded,
                        "fill_price": res.modelled_fill_price,
                    }
                out.append(row)
            log(stage="day", month=month, day=day, n=len(out))
        del sources
        with gzip.open(OUT / f"live_{month}.pkl.gz", "wb") as fh:
            pickle.dump(out, fh, protocol=5)
        log(stage="month_written", month=month, n=len(out))


if __name__ == "__main__":
    main()
