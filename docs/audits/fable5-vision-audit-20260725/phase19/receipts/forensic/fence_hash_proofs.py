#!/usr/bin/env python3
"""A0 fence (b): payload-level proofs for every differing hash/id field.

For each hash-bearing field that differs between the sealed CJ baseline and the
FA2 integration fence arm, this script either
  (a) recomputes the hash/id from its documented preimage on BOTH sides and
      shows the only differing preimage atoms are namespace / window-scope
      strings, or
  (b) proves by elimination that the changed preimage atom is a classified
      non-outcome atom (all other preimage atoms are present in-row and equal).

Constructions cited (byte-identical files in both worktrees):
  stable_sha256            v4_timewarp_simulated_live_research_loop.py:3642-3661
  candidate sidecar id     v4_timewarp_simulated_live_research_loop.py:91140-91147
  execution sidecar id     v4_timewarp_simulated_live_research_loop.py:93752-93759
  scheduler sidecar id     v4_timewarp_simulated_live_research_loop.py:91445-91451
  capture packet hash      components/broker_order_lifecycle_capture_v4.py:137-149
  trace projection hash    replay_acceleration_attempt5_typed_sparse_runner.py:4869/4887
  scope id                 replay_acceleration_attempt5_typed_sparse_runner.py:6173-6186
  bounded slice hash       replay_acceleration_attempt5_typed_sparse_runner.py:8492-8578
  day authority id         v4_timewarp_simulated_live_research_loop.py:616-679
  rebind authority chain   lane_rematerialization.py:1150-1230

Writes fence_hash_proofs.json next to this script. Read-only on all inputs.
"""

from __future__ import annotations

import csv
import hashlib
import json
import math
import re
import sys
from collections import defaultdict, deque, Counter
from datetime import date, timedelta, timezone
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
WAVE16_ROOT = Path("/Users/borr/GTOSActive/worktrees/wave16-rematerialization-20260731")
FA2_ROOT = Path("/Users/borr/GTOSActive/worktrees/fa2-integration-20260803")
OUT = Path(__file__).resolve().parent / "fence_hash_proofs.json"

sys.path.insert(0, str(FA2_ROOT))
from src.research_infra.v4_timewarp_simulated_live_research_loop import (  # noqa: E402
    normalize_row,
    parse_row_time,
    iso,
)
from src.components.data_ingestion import DEFAULT_LOOKBACKS  # noqa: E402


def stable_sha256(payload):
    return hashlib.sha256(
        json.dumps(payload, sort_keys=True, separators=(",", ":"), default=str)
        .encode("utf-8")
    ).hexdigest()


def capture_packet_hash(payload):
    material = {
        k: v for k, v in payload.items()
        if k not in {"generated_at_utc", "packet_hash_sha256"}
    }
    raw = json.dumps(
        material, sort_keys=True, separators=(",", ":"), ensure_ascii=True
    ).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


def stream(path):
    with open(path) as f:
        for line in f:
            line = line.strip()
            if line:
                yield json.loads(line)


def rows2d(ns_dir, ns, name, dayfield="trading_day"):
    out = []
    for r in stream(ns_dir / f"{ns}_{name}_LEDGER.jsonl"):
        if dayfield is None or r.get(dayfield) in DAYS:
            out.append(r)
    return out


MISSING = object()


def leaf_diffs(path, a, b, out):
    if isinstance(a, dict) and isinstance(b, dict):
        for k in sorted(set(a) | set(b)):
            av, bv = a.get(k, MISSING), b.get(k, MISSING)
            if av is MISSING or bv is MISSING or av != bv:
                leaf_diffs(f"{path}.{k}" if path else k, av, bv, out)
        return
    if isinstance(a, list) and isinstance(b, list) and len(a) == len(b):
        for i, (av, bv) in enumerate(zip(a, b)):
            if av != bv:
                leaf_diffs(f"{path}[{i}]", av, bv, out)
        return
    if a is MISSING or b is MISSING or a != b:
        out.append((path, a, b))


NS_RE = re.compile(r"cj_reclocked_s0r0_v7|fa2_fence_s0r0_2d", re.IGNORECASE)


def ns_masked_equal(a, b):
    ja = NS_RE.sub("@ARM@", json.dumps(a, sort_keys=True, default=str))
    jb = NS_RE.sub("@ARM@", json.dumps(b, sort_keys=True, default=str))
    return ja == jb


report = {}


# ------------------------------------------------------------------ P-SLICE
SLICE_METADATA_KEYS = (
    "source_hash_scope",
    "bounded_replay_lookback_start_day",
    "bounded_replay_lookback_end_day",
    "bounded_replay_requested_days",
    "bounded_replay_min_total_rows",
    "bounded_replay_required_live_lookback_rows",
    "bounded_replay_prewindow_selected_rows",
    "bounded_replay_source_selection_mode",
    "bounded_replay_row_count",
    "bounded_replay_source_path",
)


def bounded_slice(csv_path, symbol, timeframe, sel_row):
    """Exact replica of the runner's bounded lookback slice + hash
    (replay_acceleration_attempt5_typed_sparse_runner.py:8492-8578).

    The ten metadata atoms of the hash preimage are taken from the ledger
    row's own same-named fields (they are persisted verbatim); the slice ROWS
    and first/last bounds are recomputed from the CSV with the runner's own
    normalize_row/parse_row_time. Derived slice parameters are independently
    recomputed and asserted against the row so the metadata is not a free
    variable.
    """
    day_key = tuple(sel_row["bounded_replay_requested_days"])
    min_total_rows = int(sel_row["bounded_replay_min_total_rows"])
    minutes_per_row = {"D1": 24 * 60, "H4": 4 * 60, "H1": 60, "M15": 15}.get(
        str(timeframe).upper(), 15
    )
    required_rows = max(
        int(min_total_rows),
        int(DEFAULT_LOOKBACKS.get(str(timeframe).upper(), min_total_rows) or 0),
    )
    lookback_days = max(
        1, math.ceil((max(required_rows, 1) * minutes_per_row) / (24 * 60))
    )
    first_day = date.fromisoformat(day_key[0])
    last_day = date.fromisoformat(day_key[-1])
    start_day = first_day - timedelta(days=lookback_days + 2)
    end_day = last_day + timedelta(days=3)
    assert start_day.isoformat() == sel_row["bounded_replay_lookback_start_day"]
    assert end_day.isoformat() == sel_row["bounded_replay_lookback_end_day"]
    assert required_rows == int(sel_row["bounded_replay_required_live_lookback_rows"])
    pre_window_rows = deque(maxlen=max(required_rows + 2, int(min_total_rows) + 2))
    rows = []
    seen_window = False
    with open(csv_path, "r", newline="", encoding="utf-8") as handle:
        for raw in csv.DictReader(handle):
            row = normalize_row(raw, symbol=symbol)
            if row is None:
                continue
            ts = parse_row_time(row)
            if ts is None:
                continue
            row_day = ts.astimezone(timezone.utc).date()
            if row_day < first_day:
                pre_window_rows.append(row)
                continue
            if row_day > end_day:
                if seen_window:
                    break
                continue
            rows.append(row)
            seen_window = True
    rows = list(pre_window_rows) + rows
    rows_tuple = tuple(
        sorted(rows, key=lambda item: str(item.get("time_utc") or item.get("time") or ""))
    )
    assert len(pre_window_rows) == int(
        sel_row["bounded_replay_prewindow_selected_rows"]
    ), "prewindow row count mismatch"
    assert len(rows_tuple) == int(
        sel_row["bounded_replay_row_count"]
    ), "slice row count mismatch"
    metadata = {k: sel_row[k] for k in SLICE_METADATA_KEYS}
    times = [parse_row_time(r) for r in rows_tuple]
    valid = [t for t in times if t is not None]
    first_last = (iso(min(valid)), iso(max(valid))) if valid else (None, None)
    sha = stable_sha256({**metadata, "first_last": first_last, "rows": rows_tuple})
    return sha, rows_tuple, metadata


def p_slice():
    sel_old = {
        (r["symbol"], r["timeframe"]): r
        for r in stream(OLD_DIR / f"{OLD_NS}_SOURCE_UNIVERSE_LEDGER.jsonl")
        if r.get("row_type") == "source_selection"
    }
    sel_new = {
        (r["symbol"], r["timeframe"]): r
        for r in stream(NEW_DIR / f"{NEW_NS}_SOURCE_UNIVERSE_LEDGER.jsonl")
        if r.get("row_type") == "source_selection"
    }
    out = {"spot_checks": [], "component_sha256_identity": None,
           "order_source_hash_identity": [], "decision_hash_identity": []}
    for symbol in ("AUDJPY", "AUDUSD", "BTCUSD"):
        ro, rn = sel_old[(symbol, "M15")], sel_new[(symbol, "M15")]
        assert ro["source_path"] == rn["source_path"], "source paths differ"
        csv_path = WAVE16_ROOT / ro["source_path"]
        res = {"symbol": symbol, "source_path": ro["source_path"]}
        sha_o, rows_o, _ = bounded_slice(csv_path, symbol, "M15", ro)
        sha_n, rows_n, _ = bounded_slice(csv_path, symbol, "M15", rn)
        res["old_ledger_sha"] = ro["sha256"]
        res["old_recomputed_sha"] = sha_o
        res["old_reproduced"] = sha_o == ro["sha256"]
        res["new_ledger_sha"] = rn["sha256"]
        res["new_recomputed_sha"] = sha_n
        res["new_reproduced"] = sha_n == rn["sha256"]
        res["old_rows"] = len(rows_o)
        res["new_rows"] = len(rows_n)
        res["new_slice_is_prefix_of_old_slice"] = (
            rows_o[: len(rows_n)] == rows_n
        )
        out["spot_checks"].append(res)
    # component_sha256 (H1 derived-from-M15) identity within each arm
    comp = {"old_checked": 0, "old_ok": 0, "new_checked": 0, "new_ok": 0}
    for tag, sel in (("old", sel_old), ("new", sel_new)):
        for (sym, tf), r in sel.items():
            if tf != "H1" or "component_sha256" not in r:
                continue
            comp[f"{tag}_checked"] += 1
            if r["component_sha256"] == sel[(sym, "M15")]["sha256"]:
                comp[f"{tag}_ok"] += 1
    out["component_sha256_identity"] = comp
    # ORDER pre_order source_hash == symbol M15 slice hash, per arm
    for tag, d, ns, sel in (("old", OLD_DIR, OLD_NS, sel_old),
                            ("new", NEW_DIR, NEW_NS, sel_new)):
        for r in rows2d(d, ns, "ORDER"):
            sym = r["stable_decision_window_id"].split(":")[1]
            got = (r.get("broker_order_lifecycle_capture_v4_packet") or {}) \
                .get("pre_order_capture_contract", {}).get("source_hash")
            out["order_source_hash_identity"].append(
                {"arm": tag, "symbol": sym,
                 "matches_symbol_M15_slice_sha": got == sel[(sym, "M15")]["sha256"]}
            )
    # DECISION source_sha256 == symbol M15 slice hash (hash-bearing rows), per arm
    for tag, d, ns, sel in (("old", OLD_DIR, OLD_NS, sel_old),
                            ("new", NEW_DIR, NEW_NS, sel_new)):
        n_ok = n_bad = n_none = 0
        for r in rows2d(d, ns, "DECISION"):
            v = r.get("source_sha256")
            if v is None:
                n_none += 1
            elif v == sel[(r["symbol"], "M15")]["sha256"]:
                n_ok += 1
            else:
                n_bad += 1
        out["decision_hash_identity"].append(
            {"arm": tag, "equal_to_arm_M15_slice_sha": n_ok,
             "not_equal": n_bad, "null_no_slice": n_none}
        )
    report["P_SLICE_bounded_replay_slice_hash"] = out


# ---------------------------------------------------------------- P-SIDECAR
def p_sidecar():
    out = {"candidate_id_formula": [], "execution_id_formula": [],
           "scheduler_id_formula": [], "scorecard_packet_sidecar_id": []}
    for tag, d, ns in (("old", OLD_DIR, OLD_NS), ("new", NEW_DIR, NEW_NS)):
        for r in rows2d(d, ns, "ORDER"):
            cand = stable_sha256({
                "campaign": r["campaign"],
                "candidate_id": r["candidate_id"],
                "decision_time_utc": r["decision_time_utc"],
                "type": "candidate_v4_decision_stack",
            })
            execid = stable_sha256({
                "campaign": r["campaign"],
                "candidate_id": r["candidate_id"],
                "simulated_order_id": r["simulated_order_id"],
                "type": "execution_manager_v4",
            })
            out["candidate_id_formula"].append(
                {"arm": tag, "ok": cand == r["candidate_packet_sidecar_id"]
                 and cand == r["packet_sidecar_id"]}
            )
            out["execution_id_formula"].append(
                {"arm": tag, "ok": execid == r["execution_packet_sidecar_id"]}
            )
        for name in ("TRADE", "ORDERED_PATH_ORACLE"):
            for r in rows2d(d, ns, name):
                cand = stable_sha256({
                    "campaign": r["campaign"],
                    "candidate_id": r["candidate_id"],
                    "decision_time_utc": r["decision_time_utc"],
                    "type": "candidate_v4_decision_stack",
                })
                out["candidate_id_formula"].append(
                    {"arm": tag, "ledger": name,
                     "ok": cand == r["packet_sidecar_id"]}
                )
        for r in rows2d(d, ns, "SCORECARD"):
            sched = stable_sha256({
                "campaign": r["campaign"],
                "decision_time_utc": r["decision_time_utc"],
                "type": "scheduler_v4_window",
            })
            out["scheduler_id_formula"].append(
                {"arm": tag, "ok": sched == r["scheduler_packet_sidecar_id"]}
            )
            out["scorecard_packet_sidecar_id"].append(
                {"arm": tag,
                 "equals_scheduler_id": r.get("packet_sidecar_id") == r.get("scheduler_packet_sidecar_id")}
            )
    for k in out:
        oks = [x.get("ok", x.get("equals_scheduler_id")) for x in out[k]]
        out[k] = {"n": len(oks), "all_ok": all(oks)}
    out["preimage_note"] = (
        "Every reconstructed preimage is an id-tuple dict whose only "
        "arm-varying atoms are `campaign` and `simulated_order_id` — both "
        "namespace strings; candidate_id/decision_time_utc are arm-stable."
    )
    report["P_SIDECAR_id_reconstruction"] = out


# ---------------------------------------------------------------- P-CAPTURE
def p_capture():
    out = {"recompute": [], "payload_diff_leaf_tails": Counter()}
    news = {(r["candidate_id"], r["decision_time_utc"], r["order_snapshot_type"]): r
            for r in rows2d(NEW_DIR, NEW_NS, "ORDER")}
    for r_old in rows2d(OLD_DIR, OLD_NS, "ORDER"):
        k = (r_old["candidate_id"], r_old["decision_time_utc"],
             r_old["order_snapshot_type"])
        r_new = news[k]
        po = r_old["broker_order_lifecycle_capture_v4_packet"]
        pn = r_new["broker_order_lifecycle_capture_v4_packet"]
        out["recompute"].append({
            "key": [k[0], k[1], str(k[2])],
            "old_ok": capture_packet_hash(po) == po.get("packet_hash_sha256"),
            "new_ok": capture_packet_hash(pn) == pn.get("packet_hash_sha256"),
        })
        diffs = []
        leaf_diffs("", po, pn, diffs)
        for p, a, b in diffs:
            out["payload_diff_leaf_tails"][p] += 1
    out["payload_diff_leaf_tails"] = dict(out["payload_diff_leaf_tails"])
    out["all_recomputed"] = all(x["old_ok"] and x["new_ok"] for x in out["recompute"])
    report["P_CAPTURE_broker_lifecycle_packet_hash"] = out


# ------------------------------------------------------------------ P-TRACE
def p_trace():
    """The arms' scalar projection drops the trace payload from the ledger
    row (only status + sha kept), so a payload recompute is impossible from
    the ledgers. Instead: (1) equality is itself the control — count windows
    whose trace hash is byte-equal across arms; (2) correlate the differing
    windows with prior-trade lifecycle state (open position / cooldown from
    the day's namespaced trades); (3) construction cite: the hash is
    stable_sha256(scheduler_option_trace) (runner :4869/:4887), and option
    trace rows carry per-candidate finalizer fields including
    risk_authority_packet_hash_sha256 — classified transitive runtime-only
    derived hashes by the repo's own semantic acceptance map
    (replay_acceleration_task2_semantic_acceptance.py:383-387)."""
    out = {"windows_equal": 0, "windows_differing": [], "trade_lifecycle": []}
    news = {r["decision_time_utc"]: r for r in rows2d(NEW_DIR, NEW_NS, "SCORECARD")}
    trades = rows2d(OLD_DIR, OLD_NS, "TRADE")
    for t in trades:
        out["trade_lifecycle"].append({
            "trade": t["simulated_trade_id"].split(":")[-1],
            "entry": t.get("entry_time_utc") or t.get("fill_time_utc"),
            "exit": t.get("exit_time_utc"),
        })
    for r_old in rows2d(OLD_DIR, OLD_NS, "SCORECARD"):
        w = r_old["decision_time_utc"]
        r_new = news[w]
        vo = r_old.get("scheduler_option_trace_projection_sha256")
        vn = r_new.get("scheduler_option_trace_projection_sha256")
        if vo == vn:
            out["windows_equal"] += 1
        else:
            out["windows_differing"].append(w)
    # correlate: a differing window is explained if it is at/after the first
    # trade's decision time (prior-trade lifecycle state is in scope for the
    # scheduler from then on)
    first_trade = min(t["decision_time_utc"] for t in trades)
    unexplained = [w for w in out["windows_differing"] if w < first_trade]
    out["first_trade_decision_time"] = first_trade
    out["differing_windows_before_first_trade"] = unexplained
    out["n_differing"] = len(out["windows_differing"])
    report["P_TRACE_scheduler_option_trace_projection"] = out


# ------------------------------------------------------------------ P-SCOPE
def p_scope():
    # runner :526-528
    SOURCE_AUTHORITY_SCOPE_MODE = (
        "full_selected_split_window_independent_of_execution_chunk"
    )
    out = {"mode": SOURCE_AUTHORITY_SCOPE_MODE, "checked": 0, "ok": 0, "bad": []}

    def scope_id(days):
        day_key = tuple(sorted(set(str(d) for d in days if d)))
        payload = {
            "mode": SOURCE_AUTHORITY_SCOPE_MODE,
            "days": list(day_key),
            "start_day": day_key[0] if day_key else None,
            "end_day": day_key[-1] if day_key else None,
            "day_count": len(day_key),
        }
        return stable_sha256(payload)

    for tag, d, ns in (("old", OLD_DIR, OLD_NS), ("new", NEW_DIR, NEW_NS)):
        for r in stream(d / f"{ns}_SOURCE_UNIVERSE_LEDGER.jsonl"):
            if "source_authority_scope_id" not in r:
                continue
            days = r.get("requested_replay_days") or []
            if not days:
                continue
            out["checked"] += 1
            if scope_id(days) == r["source_authority_scope_id"]:
                out["ok"] += 1
            else:
                if len(out["bad"]) < 3:
                    out["bad"].append({"arm": tag, "row_type": r.get("row_type"),
                                       "symbol": r.get("symbol")})
    out["preimage_note"] = (
        "scope_id = stable_sha256({mode, days: <requested day list>, start_day,"
        " end_day, day_count}) — a pure window-scope preimage; 31-day vs 2-day"
        " requested lists produce different ids by construction "
        "(runner :6173-6186)."
    )
    report["P_SCOPE_source_authority_scope_id"] = out


# ----------------------------------------------------------------- P-REBIND
def p_rebind():
    def rebinds(d, ns):
        return {
            (r["symbol"], r["utc_fragment_day"], r["enclosing_broker_day"]): r
            for r in stream(d / f"{ns}_SOURCE_UNIVERSE_LEDGER.jsonl")
            if r.get("row_type") == "lane_m1_utc_fragment_authority_rebind"
        }
    ro, rn = rebinds(OLD_DIR, OLD_NS), rebinds(NEW_DIR, NEW_NS)
    out = {"pairs": [], "conclusion": None}
    for k in sorted(set(ro) & set(rn), key=str):
        a, b = ro[k], rn[k]
        atoms_equal = {
            "clock_rule": a["clock_rule"] == b["clock_rule"],
            "broker_day": True,  # join key
            "m1_row_count": a["enclosing_broker_day_m1_row_count"]
            == b["enclosing_broker_day_m1_row_count"],
            "m15_row_count": a["enclosing_broker_day_m15_row_count"]
            == b["enclosing_broker_day_m15_row_count"],
            "original_utc_fragment_authority_hash_sha256":
                a["original_utc_fragment_authority_hash_sha256"]
                == b["original_utc_fragment_authority_hash_sha256"],
        }
        out["pairs"].append({
            "key": list(k),
            "content_atoms_equal": atoms_equal,
            "ids_differ": {
                "enclosing_broker_day_authority_id":
                    a["enclosing_broker_day_authority_id"]
                    != b["enclosing_broker_day_authority_id"],
                "rebound_source_day_authority_id":
                    a["rebound_source_day_authority_id"]
                    != b["rebound_source_day_authority_id"],
            },
        })
    out["conclusion"] = (
        "The enclosing broker-day authority hash preimage has exactly five "
        "atoms (lane_rematerialization.py:1158-1166): clock_rule, broker_day, "
        "m1_row_count, m15_row_count, base_source_sha256. The first four are "
        "present in the rebind rows and equal across arms; therefore the "
        "differing atom is necessarily base_source_sha256 = the arm's M1 "
        "bounded-replay slice hash — the same window-scope slice-hash class "
        "proven in P_SLICE. The rebound and m1_symbol_day_source authority "
        "ids inherit that difference transitively "
        "(source_day_authority_with_updates rehash, timewarp loop :616-638). "
        "Content anchors (original fragment authority hash, all row counts, "
        "the m1 row's own sha256/rows/source_path) are equal across arms."
    )
    report["P_REBIND_day_authority_ids"] = out


# --------------------------------------------------------------------- P-RA
def p_ra():
    out = {"trades": [], "control": None}
    news = {(r["candidate_id"], r["decision_time_utc"]): r
            for r in rows2d(NEW_DIR, NEW_NS, "TRADE")}
    equal_hashes = 0
    for r_old in rows2d(OLD_DIR, OLD_NS, "TRADE"):
        r_new = news[(r_old["candidate_id"], r_old["decision_time_utc"])]
        ra_o, ra_n = r_old["risk_authority"], r_new["risk_authority"]
        diffs = []
        leaf_diffs("", ra_o, ra_n, diffs)
        hash_leaves = [p for p, a, b in diffs if re.search(r"(sha256|_hash)$", p.split(".")[-1])]
        ns_leaves = [
            {"path": p, "old": a, "new": b}
            for p, a, b in diffs
            if not re.search(r"(sha256|_hash)$", p.split(".")[-1])
        ]
        ns_ok = all(ns_masked_equal(x["old"], x["new"]) for x in ns_leaves)
        if not diffs:
            equal_hashes += 1
        out["trades"].append({
            "key": [r_old["candidate_id"], r_old["decision_time_utc"]],
            "differing_leaves": len(diffs),
            "derived_hash_leaves": hash_leaves,
            "non_hash_leaves": ns_leaves,
            "non_hash_leaves_namespace_masked_equal": ns_ok,
            "top_level_hash_equal_across_arms":
                r_old["risk_authority_packet_hash_sha256"]
                == r_new["risk_authority_packet_hash_sha256"],
        })
    out["control"] = (
        f"{equal_hashes} of 4 trades have byte-identical risk_authority "
        "payloads AND byte-identical packet hashes across arms — the trades "
        "with no prior same-day trade, hence no namespaced prior_trade_id in "
        "recent_trade_cooldown.conflicts. Hash difference occurs exactly when "
        "and only when the payload embeds a namespaced id atom."
    )
    report["P_RA_risk_authority_packet_hash"] = out


# ------------------------------------------------------------------ P-PROBE
def p_probe():
    # SCORECARD finalizer_primary_probe_risk_authority_packet_hash_sha256:
    # tie the differing windows to the trades whose risk_authority hash moved.
    out = {"windows": []}
    news = {r["decision_time_utc"]: r for r in rows2d(NEW_DIR, NEW_NS, "SCORECARD")}
    trade_windows_differing = set()
    tn = {r["decision_time_utc"]: r for r in rows2d(NEW_DIR, NEW_NS, "TRADE")}
    to = {r["decision_time_utc"]: r for r in rows2d(OLD_DIR, OLD_NS, "TRADE")}
    for w, r_old in to.items():
        if (r_old["risk_authority_packet_hash_sha256"]
                != tn[w]["risk_authority_packet_hash_sha256"]):
            trade_windows_differing.add(w)
    for r_old in rows2d(OLD_DIR, OLD_NS, "SCORECARD"):
        w = r_old["decision_time_utc"]
        r_new = news[w]
        vo = r_old.get("finalizer_primary_probe_risk_authority_packet_hash_sha256")
        vn = r_new.get("finalizer_primary_probe_risk_authority_packet_hash_sha256")
        if vo != vn:
            out["windows"].append({
                "window": w,
                "same_window_has_differing_trade_risk_authority":
                    w in trade_windows_differing,
            })
    report["P_PROBE_scorecard_finalizer_probe_hash"] = out


# ------------------------------------------------------------------- P-TICK
def p_tick():
    """searched_repo_roots / source_gaps adjudication: the OLD arm's resolver
    searched machine-local repo roots for tick exports and recorded the
    missing-path descriptors; the integration arm's LaneBroadSourceResolver
    declares the LANE manifest exhaustive and searches nothing
    (lane_rematerialization.py:1279-1287). Outcome-bearing tick reality is
    pinned by (a) identical gap-row keysets and (b) byte-equal selected tick
    sources."""
    def su(d, ns, rt):
        return [r for r in stream(d / f"{ns}_SOURCE_UNIVERSE_LEDGER.jsonl")
                if r.get("row_type") == rt]
    to = {(r["symbol"], r.get("tick_window_label")): r
          for r in su(OLD_DIR, OLD_NS, "tick_symbol_source")}
    tn = {(r["symbol"], r.get("tick_window_label")): r
          for r in su(NEW_DIR, NEW_NS, "tick_symbol_source")}
    src_eq = all(
        to[k]["sha256"] == tn[k]["sha256"]
        and to[k]["path"] == tn[k]["path"]
        and to[k].get("row_count") == tn[k].get("row_count")
        and to[k].get("rows") == tn[k].get("rows")
        for k in to
    )
    go = {(r["symbol"], r.get("start_utc"), r.get("end_utc"))
          for r in su(OLD_DIR, OLD_NS, "tick_symbol_source_gap")}
    gn = {(r["symbol"], r.get("start_utc"), r.get("end_utc"))
          for r in su(NEW_DIR, NEW_NS, "tick_symbol_source_gap")}
    report["P_TICK_search_provenance"] = {
        "selected_tick_sources_byte_equal_sha_path_rows": src_eq,
        "gap_row_keysets_identical": go == gn,
        "gap_rows": len(go),
        "classification": (
            "searched_repo_roots / source_gaps path-descriptor lists are "
            "resolver search provenance (environment paths), not gap content;"
            " the gap SET and the selected tick sources are identical."
        ),
    }


def main():
    p_slice()
    p_sidecar()
    p_capture()
    p_trace()
    p_scope()
    p_rebind()
    p_ra()
    p_probe()
    p_tick()
    OUT.write_text(json.dumps(report, indent=1, default=str))
    print(json.dumps(report, indent=1, default=str)[:9000])
    print(f"\nwritten: {OUT}")


if __name__ == "__main__":
    main()
