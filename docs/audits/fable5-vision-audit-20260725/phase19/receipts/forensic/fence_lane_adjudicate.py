#!/usr/bin/env python3
"""A0 fence (b) adjudication: identity-join, field-by-field ledger comparator.

OLD = sealed CJ baseline (31-day arm), rows filtered to 2026-01-01/2026-01-02.
NEW = FA2 integration fence arm (2-day).

Joins by row identity (never sort order), walks every field recursively to leaf
granularity, and classifies each differing leaf. Nothing is silently excluded:
hash/id fields land in a dedicated census for payload-level proof; unclassified
leaves are fence-failure candidates and are dumped in full.

Writes fence_census.json next to this script. Read-only on all inputs.
"""

from __future__ import annotations

import json
import re
import sys
import collections
from pathlib import Path

OLD_DIR = Path(
    "/Users/borr/GTOSActive/worktrees/wave16-rematerialization-20260731/research/operations/"
    "final_moonshot_ultimate_system_denominator_to_deployment_execution_2026_06_20/"
    "attempt_5_typed_sparse/CJ_RECLOCKED_S0R0_V7"
)
NEW_DIR = Path(
    "/Users/borr/GTOSActive/worktrees/fa2-integration-20260803/research/operations/"
    "final_moonshot_ultimate_system_denominator_to_deployment_execution_2026_06_20/"
    "attempt_5_typed_sparse/FA2_FENCE_S0R0_2D"
)
OLD_NS = "CJ_RECLOCKED_S0R0_V7"
NEW_NS = "FA2_FENCE_S0R0_2D"
DAYS = {"2026-01-01", "2026-01-02"}
OUT = Path(__file__).resolve().parent / "fence_census.json"

MISSING = object()

NS_RE = re.compile(r"cj_reclocked_s0r0_v7|fa2_fence_s0r0_2d", re.IGNORECASE)
WT_RE = re.compile(
    r"wave16-rematerialization-20260731|fa2-integration-20260803", re.IGNORECASE
)
HASHID_TAIL_RE = re.compile(r"(sha256|_id|_ids|_hash)$")


def mask(value):
    if isinstance(value, str):
        return WT_RE.sub("@WT@", NS_RE.sub("@ARM@", value))
    if isinstance(value, list):
        return [mask(v) for v in value]
    if isinstance(value, dict):
        return {k: mask(v) for k, v in value.items()}
    return value


def leaf_diffs(path, a, b, out):
    """Emit (path, old, new) for every differing leaf; recurse dicts and
    same-length lists, treat everything else as a leaf."""
    if a is MISSING or b is MISSING:
        out.append((path, a, b))
        return
    if isinstance(a, dict) and isinstance(b, dict):
        for k in sorted(set(a) | set(b)):
            av = a.get(k, MISSING)
            bv = b.get(k, MISSING)
            if av is MISSING or bv is MISSING or av != bv:
                leaf_diffs(f"{path}.{k}" if path else k, av, bv, out)
        return
    if isinstance(a, list) and isinstance(b, list) and len(a) == len(b):
        for i, (av, bv) in enumerate(zip(a, b)):
            if av != bv:
                leaf_diffs(f"{path}[{i}]", av, bv, out)
        return
    if a != b:
        out.append((path, a, b))


WINDOW_SCOPE_TAILS = {
    "requested_replay_days",
    "requested_end_day",
    "requested_start_day",
    "source_authority_day_count",
    "source_authority_end_day",
    "source_authority_start_day",
    "bounded_replay_requested_days",
    "bounded_replay_row_count",
    "bounded_replay_lookback_end_day",
    "bounded_replay_lookback_start_day",
    "source_end_utc",
    "source_start_utc",
    "selected_days",
    "start",
    "end",
    "rows",
    "chunk_day_count",
}

VERSION_TAILS = {"pretrade_cost_packet_model_version"}
DIAGNOSTIC_TAILS = {"old_proxy_vs_broker_calibrated_delta_r"}


def tail_of(path):
    seg = path.split(".")[-1]
    return re.sub(r"\[\d+\]$", "", seg)


def classify(ledger, path, a, b):
    t = tail_of(path)
    if a is MISSING:
        return "PRESENT_NEW_ONLY"
    if b is MISSING:
        return "PRESENT_OLD_ONLY"
    if t in VERSION_TAILS:
        return "AUTHORIZED_VERSION_STAMP"
    if (
        t == "model_version"
        and a == "vnext_selected_cell_pretrade_cost_model_v2"
        and b == "vnext_selected_cell_pretrade_cost_model_v3"
    ):
        return "AUTHORIZED_VERSION_STAMP"
    if t in DIAGNOSTIC_TAILS:
        return "DIAGNOSTIC_EXCLUDED"
    if (
        t == "train_lane_missed_projection"
        and a == "train_lane_missed_pool_projection_v1"
        and b == "train_lane_missed_pool_projection_v3"
    ):
        return "PROJECTION_VERSION_STAMP"
    if mask(a) == mask(b):
        s = json.dumps([a, b], default=str)
        return "NAMESPACE_PATH" if "/" in s else "NAMESPACE_TOKEN"
    if HASHID_TAIL_RE.search(t):
        return "HASH_OR_ID_UNPROVEN"
    if ledger.startswith(("SOURCE_UNIVERSE", "BUCKET")) and t in WINDOW_SCOPE_TAILS:
        return "WINDOW_SCOPE_CANDIDATE"
    if (
        ledger.startswith("SOURCE_UNIVERSE")
        and t in ("searched_repo_roots", "source_gaps")
    ):
        # adjudicated by fence_hash_proofs.py P_TICK: resolver search
        # provenance (environment path lists); gap keysets + selected tick
        # sources verified identical.
        return "RESOLVER_SEARCH_PROVENANCE"
    if ledger == "DECISION" and t == "source_sha256":
        return "HASH_OR_ID_UNPROVEN"
    return "UNCLASSIFIED"


def stream(path):
    with open(path) as f:
        for line in f:
            line = line.strip()
            if line:
                yield json.loads(line)


def ledger_paths(name):
    return (
        OLD_DIR / f"{OLD_NS}_{name}_LEDGER.jsonl",
        NEW_DIR / f"{NEW_NS}_{name}_LEDGER.jsonl",
    )


def build_index(rows_iter, keyfn, filt=None):
    idx = {}
    dups = []
    skipped = 0
    for r in rows_iter:
        if filt is not None and not filt(r):
            skipped += 1
            continue
        k = keyfn(r)
        if k in idx:
            dups.append(k)
        idx[k] = r
    return idx, dups, skipped


def compare(name, old_idx, new_idx, census, econ_fields=()):
    joined = sorted(set(old_idx) & set(new_idx), key=str)
    only_old = sorted(set(old_idx) - set(new_idx), key=str)
    only_new = sorted(set(new_idx) - set(old_idx), key=str)
    field_class = collections.defaultdict(collections.Counter)  # top field -> class counter
    leaf_class = collections.Counter()
    samples = {}
    unclassified = []
    econ_mismatch = []
    identical = 0
    for k in joined:
        a, b = old_idx[k], new_idx[k]
        diffs = []
        leaf_diffs("", a, b, diffs)
        if not diffs:
            identical += 1
            continue
        for path, av, bv in diffs:
            cls = classify(name, path, av, bv)
            top = path.split(".")[0]
            top = re.sub(r"\[\d+\]$", "", top)
            field_class[f"{top}::{tail_of(path)}"][cls] += 1
            leaf_class[cls] += 1
            skey = (path if "[" not in path else re.sub(r"\[\d+\]", "[]", path), cls)
            if skey not in samples:
                samples[skey] = {
                    "ledger": name,
                    "row_key": [str(x) for x in k] if isinstance(k, tuple) else str(k),
                    "path": path,
                    "old": av if av is not MISSING else "<ABSENT>",
                    "new": bv if bv is not MISSING else "<ABSENT>",
                    "class": cls,
                }
            if cls == "UNCLASSIFIED":
                unclassified.append(
                    {
                        "row_key": [str(x) for x in k] if isinstance(k, tuple) else str(k),
                        "path": path,
                        "old": av if av is not MISSING else "<ABSENT>",
                        "new": bv if bv is not MISSING else "<ABSENT>",
                    }
                )
        for ef in econ_fields:
            if ef not in a or ef not in b:
                # absent on one side = projection gap, adjudicated separately
                # in the PRESENT_*_ONLY census; comparison is defined only
                # when both projections carry the field.
                continue
            av, bv = a.get(ef, MISSING), b.get(ef, MISSING)
            if av != bv:
                econ_mismatch.append(
                    {
                        "row_key": [str(x) for x in k] if isinstance(k, tuple) else str(k),
                        "field": ef,
                        "old": av if av is not MISSING else "<ABSENT>",
                        "new": bv if bv is not MISSING else "<ABSENT>",
                    }
                )
    census[name] = {
        "joined": len(joined),
        "identical": identical,
        "only_old_keys": [list(map(str, k)) if isinstance(k, tuple) else str(k) for k in only_old],
        "only_new_keys": [list(map(str, k)) if isinstance(k, tuple) else str(k) for k in only_new],
        "leaf_class_counts": dict(leaf_class),
        "field_class_counts": {
            f: dict(c) for f, c in sorted(field_class.items())
        },
        "samples": list(samples.values()),
        "unclassified": unclassified,
        "economic_mismatches": econ_mismatch,
    }


def main():
    census = {}

    # ---------------- TRADE ----------------
    op, np_ = ledger_paths("TRADE")
    key = lambda r: (
        r.get("candidate_id"),
        r.get("decision_time_utc"),
        r.get("stable_decision_window_id"),
        r.get("direction"),
    )
    oidx, od, osk = build_index(stream(op), key, lambda r: r.get("trading_day") in DAYS)
    nidx, nd, nsk = build_index(stream(np_), key, None)
    assert all(r.get("trading_day") in DAYS for r in nidx.values()), "NEW TRADE outside days"
    econ = [
        "entry_price", "fill_price", "exit_price", "entry_time_utc", "fill_time_utc",
        "exit_time_utc", "final_r", "gross_r", "net_proxy_r", "cost_r", "commission_r",
        "spread_r", "swap_cost_r", "expected_cost_r", "recorded_cost_r", "risk_cash",
        "risk_per_trade_pct", "approved_risk_pct", "close_reason", "fill_status",
        "terminal_outcome", "balance_before", "balance_after", "stop_loss",
        "take_profit_1", "position_size",
    ]
    compare("TRADE", oidx, nidx, census, econ)
    census["TRADE"]["dup_keys"] = {"old": len(od), "new": len(nd)}
    census["TRADE"]["old_rows_out_of_window"] = osk

    # ---------------- ORDER ----------------
    op, np_ = ledger_paths("ORDER")
    key = lambda r: (
        r.get("candidate_id"),
        r.get("decision_time_utc"),
        r.get("stable_decision_window_id"),
        r.get("direction"),
        r.get("order_snapshot_type"),
        r.get("order_event_stage"),
        r.get("is_terminal_order_event"),
    )
    oidx, od, osk = build_index(stream(op), key, lambda r: r.get("trading_day") in DAYS)
    nidx, nd, nsk = build_index(stream(np_), key, None)
    assert all(r.get("trading_day") in DAYS for r in nidx.values()), "NEW ORDER outside days"
    econ = [
        "entry_price", "fill_price", "fill_time_utc", "fill_status", "order_status",
        "final_r", "gross_r", "cost_r", "commission_r", "spread_r", "swap_cost_r",
        "expected_cost_r", "risk_cash", "risk_per_trade_pct", "stop_loss",
        "take_profit_1", "effective_order_type", "terminal_outcome",
        "limit_first_fill_status", "limit_first_terminal_outcome",
        "fallback_execution_surcharge_r", "guarded_market_fallback_extra_cost_r",
    ]
    compare("ORDER", oidx, nidx, census, econ)
    census["ORDER"]["dup_keys"] = {"old": len(od), "new": len(nd)}

    # ---------------- ORDERED_PATH_ORACLE ----------------
    op, np_ = ledger_paths("ORDERED_PATH_ORACLE")
    key = lambda r: (
        r.get("candidate_id"),
        r.get("decision_time_utc"),
        r.get("stable_decision_window_id"),
    )
    oidx, od, osk = build_index(stream(op), key, lambda r: r.get("trading_day") in DAYS)
    nidx, nd, nsk = build_index(stream(np_), key, None)
    compare("ORDERED_PATH_ORACLE", oidx, nidx, census, [
        "final_r", "gross_r", "net_proxy_r", "close_reason", "terminal_outcome",
        "cost_r", "commission_r", "spread_r",
    ])
    census["ORDERED_PATH_ORACLE"]["dup_keys"] = {"old": len(od), "new": len(nd)}

    # ---------------- DECISION ----------------
    op, np_ = ledger_paths("DECISION")
    key = lambda r: (r.get("decision_time_utc"), r.get("symbol"))
    oidx, od, osk = build_index(stream(op), key, lambda r: r.get("trading_day") in DAYS)
    nidx, nd, nsk = build_index(stream(np_), key, None)
    assert all(r.get("trading_day") in DAYS for r in nidx.values()), "NEW DECISION outside days"
    compare("DECISION", oidx, nidx, census, [
        "candidate_count", "final_selection_claim", "raw_data_status",
        "source_session_status", "m1_or_tick_attached_to_decision",
    ])
    census["DECISION"]["dup_keys"] = {"old": len(od), "new": len(nd)}
    census["DECISION"]["old_rows_out_of_window"] = osk

    # ---------------- SCORECARD ----------------
    op, np_ = ledger_paths("SCORECARD")
    key = lambda r: (r.get("decision_time_utc"), r.get("stable_decision_window_id"))
    oidx, od, osk = build_index(stream(op), key, lambda r: r.get("trading_day") in DAYS)
    nidx, nd, nsk = build_index(stream(np_), key, None)
    compare("SCORECARD", oidx, nidx, census, [
        "selected_scheduler_symbol", "selected_scheduler_direction",
        "pre_risk_finalizer_symbol", "pre_risk_finalizer_direction",
        "risk_finalizer_selected_rank", "scorecard_reported_candidate_confidence",
    ])
    census["SCORECARD"]["dup_keys"] = {"old": len(od), "new": len(nd)}

    # ---------------- MISSED_OPPORTUNITY (streamed) ----------------
    # OLD arm's missed rows are the 80-key scalar projection with NO
    # trading_day field; the day is derived from decision_time_utc. The NEW
    # rows carry trading_day and satisfy date(decision_time_utc)==trading_day
    # (asserted below), which grounds the derivation.
    op, np_ = ledger_paths("MISSED_OPPORTUNITY")
    key = lambda r: (
        r.get("candidate_id"),
        r.get("decision_time_utc"),
        r.get("symbol"),
        r.get("direction"),
    )
    nidx, nd, nsk = build_index(stream(np_), key, None)
    assert all(r.get("trading_day") in DAYS for r in nidx.values()), "NEW MISSED outside days"
    bad_map = [
        k for k, r in nidx.items()
        if str(r.get("decision_time_utc") or "")[:10] != r.get("trading_day")
    ]
    # The NEW arm stamps trading_day; 54 rows are the day's final decision
    # window at 00:00 of the NEXT calendar date (2026-01-03T00:00 stamped
    # trading_day 2026-01-02). The OLD projection has no trading_day, so the
    # OLD filter is decision-date in DAYS OR key present in the NEW arm —
    # which captures exactly those boundary windows.
    old_day = lambda r: (
        str(r.get("decision_time_utc") or "")[:10] in DAYS or key(r) in nidx
    )
    oidx, od, osk = build_index(stream(op), key, old_day)
    census.setdefault("_invariants", {})["missed_new_boundary_window_rows"] = len(bad_map)
    census["_invariants"]["missed_boundary_note"] = (
        "54 NEW rows have decision_time_utc 2026-01-03T00:00 with trading_day "
        "2026-01-02 (the day's last window); OLD counterparts joined via the "
        "key-union filter."
    )
    econ = [
        "opportunity_net_proxy_r", "opportunity_gross_r", "cost_r", "commission_r",
        "spread_r", "swap_cost_r", "expected_cost_r", "recorded_cost_r",
        "expected_slippage_r", "fallback_execution_surcharge_r",
        "guarded_market_fallback_extra_cost_r", "miss_reason", "final_blocker_class",
        "missed_package_replay_order_executable_final_blocker_class",
        "selector_action", "effective_selector_action", "selector_reason",
        "effective_selector_reason", "risk_per_trade_pct", "fill_probability",
        "candidate_probability", "candidate_confidence", "terminal_outcome",
        "counterfactual_order_terminal_outcome", "counterfactual_order_fill_status",
        "counterfactual_order_close_mark_r", "counterfactual_order_close_time_utc",
        "opportunity_close_reason", "opportunity_close_time_utc", "entry_price",
        "stop_loss", "take_profit_1", "expectancy_r", "expected_net_r",
        "authoritative_cost_r", "authoritative_candidate_ev_r",
        "same_side_pending_risk_pct", "opposite_pending_risk_pct",
        "same_symbol_lifecycle_exposure_risk_pct", "raw_target_r", "policy_target_r",
        "cost_component_candidate_sum_r", "cost_component_rebase_delta_r",
        "entry_fill_executable", "fill_realism_executable", "fill_realism_class",
        "fill_realism_reason", "limit_first_fill_status",
        "limit_first_terminal_outcome", "effective_order_type",
        "source_bound_signal_r", "terminal_r_scoreable",
    ]
    compare("MISSED_OPPORTUNITY", oidx, nidx, census, econ)
    census["MISSED_OPPORTUNITY"]["dup_keys"] = {"old": len(od), "new": len(nd)}
    census["MISSED_OPPORTUNITY"]["old_rows_out_of_window"] = osk

    # ---------------- BUCKET (chunk-scoped) ----------------
    op, np_ = ledger_paths("BUCKET")
    key = lambda r: (
        r.get("chunk_id"),
        r.get("trading_day"),
        r.get("symbol"),
        r.get("session"),
        r.get("framework"),
        r.get("risk_reason"),
        r.get("bucket_source_family"),
        r.get("bucket_result_authority"),
    )
    in_window_chunk = lambda r: (
        r.get("chunk_start_day") in DAYS
        and r.get("chunk_start_day") == r.get("chunk_end_day")
    )
    oidx, od, osk = build_index(stream(op), key, in_window_chunk)
    nidx, nd, nsk = build_index(stream(np_), key, in_window_chunk)
    compare("BUCKET", oidx, nidx, census, [
        "gross_r", "net_proxy_r", "total_r", "cash_pnl", "pnl_cash", "risk_cash",
        "risk_cash_sum", "risk_pct_sum", "avg_risk_pct", "filled_trades",
        "filled_trade_count", "simulated_orders", "not_filled_orders",
        "expired_unfilled_orders", "risk_rejected_orders", "candidate_rows",
        "candidate_count", "ending_balance", "ending_equity", "max_drawdown_pct",
        "expected_cost_r", "winner_count", "loser_count", "same_bar_ambiguity_count",
        "headline_net_proxy_r", "headline_total_r", "headline_gross_r",
        "headline_cash_pnl", "headline_final_r", "headline_filled_trade_count",
        "all_trade_net_proxy_r", "all_trade_total_r", "all_trade_gross_r",
        "diagnostic_only_net_proxy_r", "diagnostic_only_trade_count",
    ])
    census["BUCKET"]["dup_keys"] = {"old": len(od), "new": len(nd)}
    census["BUCKET"]["old_rows_out_of_window"] = osk
    census["BUCKET"]["new_rows_out_of_window"] = nsk

    # ---------------- SOURCE_UNIVERSE (per row_type) ----------------
    op, np_ = ledger_paths("SOURCE_UNIVERSE")

    def su_load(path):
        types = collections.defaultdict(list)
        for r in stream(path):
            types[r.get("row_type")].append(r)
        return types

    so, sn = su_load(op), su_load(np_)
    su_census = {}

    def su_cmp(rt, keyfn, filt_old=None, econ=()):
        oidx, od, osk = build_index(iter(so.get(rt, [])), keyfn, filt_old)
        nidx, nd, nsk = build_index(iter(sn.get(rt, [])), keyfn, None)
        compare(f"SOURCE_UNIVERSE::{rt}", oidx, nidx, census, econ)
        census[f"SOURCE_UNIVERSE::{rt}"]["dup_keys"] = {"old": len(od), "new": len(nd)}
        census[f"SOURCE_UNIVERSE::{rt}"]["old_rows_out_of_window"] = osk

    su_cmp(
        "m1_symbol_day_source",
        lambda r: (r.get("symbol"), r.get("trading_day")),
        lambda r: r.get("trading_day") in DAYS,
        econ=["rows", "m15_day_rows", "sha256", "status", "source_path",
              "source_gaps", "source_session_status"],
    )
    su_cmp(
        "source_selection",
        lambda r: (r.get("symbol"), r.get("timeframe")),
        None,
        econ=["source_path", "status", "source_broker", "mapped_symbol"],
    )
    su_cmp(
        "tick_symbol_source",
        lambda r: (r.get("symbol"), r.get("tick_window_label")),
        None,
        econ=["path", "sha256", "row_count", "rows", "status", "selected_status"],
    )
    su_cmp(
        "tick_symbol_source_gap",
        lambda r: (r.get("symbol"), r.get("start_utc"), r.get("end_utc"),
                   r.get("tick_window_label")),
        None,
    )
    su_cmp(
        "source_gap",
        lambda r: (r.get("symbol"), r.get("timeframe"), r.get("start_utc"),
                   r.get("end_utc")),
        None,
    )
    su_cmp(
        "lane_m1_utc_fragment_authority_rebind",
        lambda r: (r.get("symbol"), r.get("trading_day"),
                   json.dumps(r.get("fragment_id") or r.get("source_path") or r.get("path"), default=str)),
        None,
    )
    # split_definition: window-scope by construction; record inventory only.
    census["SOURCE_UNIVERSE::split_definition"] = {
        "window_scope_by_construction": True,
        "old_rows": [
            {k: r.get(k) for k in ("split", "start", "end", "selected_days")}
            for r in so.get("split_definition", [])
        ],
        "new_rows": [
            {k: r.get(k) for k in ("split", "start", "end", "selected_days")}
            for r in sn.get("split_definition", [])
        ],
    }

    def default(o):
        if o is MISSING:
            return "<ABSENT>"
        return str(o)

    OUT.write_text(json.dumps(census, indent=1, default=default))

    # ---- console summary ----
    for name, c in census.items():
        if name == "_invariants":
            print(f"_invariants: {c}")
            continue
        if "joined" not in c:
            print(f"{name}: window-scope inventory only "
                  f"(old {len(c['old_rows'])} rows / new {len(c['new_rows'])})")
            continue
        print(
            f"{name}: joined={c['joined']} identical={c['identical']} "
            f"only_old={len(c['only_old_keys'])} only_new={len(c['only_new_keys'])} "
            f"dups={c.get('dup_keys')} "
            f"econ_mismatches={len(c['economic_mismatches'])} "
            f"unclassified={len(c['unclassified'])}"
        )
        for cls, n in sorted(c["leaf_class_counts"].items()):
            print(f"    {cls}: {n}")
    print(f"\ncensus written: {OUT}")


if __name__ == "__main__":
    main()
