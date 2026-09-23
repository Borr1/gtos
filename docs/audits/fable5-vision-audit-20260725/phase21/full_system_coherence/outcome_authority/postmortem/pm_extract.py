#!/usr/bin/env python3
"""Three-month postmortem — stage 1: population extraction + frozen-rule re-run with audit.

READ-ONLY over every input. Reuses the committed scorers' loaders byte-identically:
the module chain (r3b -> s2 -> ridge -> candidate_funnel -> january) is loaded from the
COMMITTED files, which self-bind to the wave21-full-system-coherence-20260809 worktree
whose code produced the sealed February R2 and April+May V1 results. Nothing here is a
new frozen rule; every output is a development/diagnostic receipt.

Writes (cache, not committed):
  CACHE/rows_{octnov,jan,feb,april,may}.jsonl.gz   one merged row per occurrence:
      full _lifecycle_row label + the frozen feature_row + raw extras
      (candidate_id, entry/stop/target, decision_time_utc, expiry).
  CACHE/predictions_{feb,aprmay}.jsonl.gz          per (day, occurrence) frozen-ridge
      prediction for every eligible occurrence, from the same prequential fits.
  CACHE/window_audit_{feb,aprmay}.jsonl.gz         one record per decision window of the
      main policy: ranked top-3, chosen key or disposition.
Writes (committed receipt):
  RECEIPTS/PM_RERUN_INTEGRITY_V1.json              proof the re-run reproduces both
      sealed results' selected sets exactly, plus population counters.
"""
from __future__ import annotations

import gzip
import hashlib
import importlib.util
import json
import math
import sys
import time
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path

import numpy as np

WT_NEW = Path(__file__).resolve().parents[7]
OA = WT_NEW / "docs/audits/fable5-vision-audit-20260725/phase21/full_system_coherence/outcome_authority"
RECEIPTS = OA / "postmortem"
CACHE = Path("/private/tmp/w21-postmortem-cache-20260811")
CACHE.mkdir(parents=True, exist_ok=True)

R3B_PATH = OA / "w21_score_aprmay_r3b.py"
FEB_RESULT_PATH = OA / "FEBRUARY_MARKET_TOP_CHOICE_VALIDATION_RESULT_R2.json"
APRMAY_RESULT_PATH = OA / "APRIL_MAY_MARKET_TOP_CHOICE_VALIDATION_RESULT_V1.json"
RULE_PATH = OA / "MARKET_TOP_CHOICE_VALIDATION_RULE_V1_1.json"
PREREG_PATH = OA / "APRIL_MAY_MARKET_TOP_CHOICE_PREREG_V1_6.json"


def load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


print(json.dumps({"stage": "loading_module_chain"}), flush=True)
r3b = load_module("pm_r3b", R3B_PATH)   # loads s2 (r2 scorer) and r (ridge) transitively
s2 = r3b.s2
r = r3b.r
m = r.m
j = r.j

FEB_ROOT = r3b.FEB_ROOT
NEW_ROOT = r3b.NEW_ROOT


def log(**kw):
    print(json.dumps({"t": round(time.time() - T0, 1), **kw}, sort_keys=True), flush=True)


T0 = time.time()


def clean(value):
    """JSON-safe: NaN/inf -> None, recursively."""
    if isinstance(value, float):
        return value if math.isfinite(value) else None
    if isinstance(value, dict):
        return {k: clean(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [clean(v) for v in value]
    return value


RAW_EXTRAS = (
    "candidate_id", "entry_price", "stop_loss", "take_profit_1",
    "decision_time_utc", "limit_first_expiry_utc",
)


def merged_row(raw, label, feat, month):
    extras = {k: raw.get(k) for k in RAW_EXTRAS}
    extras["month"] = month
    return {**label, **feat, **extras}


def write_rows(path: Path, rows):
    with gzip.open(path, "wt", encoding="utf-8") as fh:
        for row in rows:
            fh.write(json.dumps(clean(row), sort_keys=True) + "\n")
    log(wrote=str(path), rows=len(rows))


def read_rows(path: Path):
    with gzip.open(path, "rt", encoding="utf-8") as fh:
        return [json.loads(line) for line in fh]


# ---------------------------------------------------------------- Oct/Nov + January
def extract_octnov():
    out = CACHE / "rows_octnov.jsonl.gz"
    if out.is_file():
        log(skip="octnov", cached=True)
        return read_rows(out)
    rows = []
    for day, root, authority in j.INITIAL_RUNS:
        manifest_root, sources = m._source_bundle(day)
        m15b = r.initial_m15_bundle(day)
        sink = r.ReplayCompactEventSink.open_sealed(
            root=root, expected_authority_root_sha256=authority
        )
        for raw in sink.ledger("missed"):
            label = m._lifecycle_row(raw, manifest_root=manifest_root, sources=sources)
            feat = r.feature_row(raw, label, m15b)
            rows.append(merged_row(raw, label, feat, "octnov"))
        log(loaded=day, rows=len(rows))
    write_rows(out, rows)
    return rows


def extract_jan():
    out = CACHE / "rows_jan.jsonl.gz"
    if out.is_file():
        log(skip="jan", cached=True)
        return read_rows(out)
    manifest_root, sources = j.load_january_sources()
    m15b = r.january_m15_bundle()
    rows = []
    for day, authority in j.JAN_RUNS:
        sink = r.ReplayCompactEventSink.open_sealed(
            root=j.JAN_ROOT / day / "compact_events",
            expected_authority_root_sha256=authority,
        )
        for raw in sink.ledger("missed"):
            label = m._lifecycle_row(raw, manifest_root=manifest_root, sources=sources)
            feat = r.feature_row(raw, label, m15b)
            rows.append(merged_row(raw, label, feat, "jan"))
        log(loaded=day, rows=len(rows))
    write_rows(out, rows)
    return rows


# ---------------------------------------------------------------- Feb / April / May
def extract_month(month, root, days, manifest_name, expected_root):
    out = CACHE / f"rows_{month}.jsonl.gz"
    if out.is_file():
        log(skip=month, cached=True)
        return read_rows(out)
    manifest_root, sources = r3b.load_m1_sources(
        r3b.MANIFEST_DIR / manifest_name, expected_root
    )
    rows = []
    for day in days:
        # s2.load_day's exact internals (sealed sink -> _lifecycle_row -> feature_row),
        # inlined so the label dict is kept instead of recomputed.
        summary = json.loads((root / day / "run_summary.json").read_text(encoding="utf-8"))
        sink = s2.ReplayCompactEventSink.open_sealed(
            root=root / day / "compact_events",
            expected_authority_root_sha256=summary["authority_root_sha256"],
        )
        for raw in sink.ledger("missed"):
            label = m._lifecycle_row(raw, manifest_root=manifest_root, sources=sources)
            feat = s2.feature_row(raw, label)
            rows.append(merged_row(raw, label, feat, month))
        log(loaded=day, rows=len(rows))
    write_rows(out, rows)
    return rows


# ---------------------------------------------------------------- re-run with audit
def at(value):
    return datetime.fromisoformat(str(value).replace("Z", "+00:00"))


def select_with_audit(rows, predictions, *, policy):
    """s2.select, reproduced with per-window audit records. Selection semantics are
    asserted identical to s2.select by the caller."""
    by_window = defaultdict(list)
    for row, prediction in zip(rows, predictions):
        by_window[row["decision_window_id"]].append((float(prediction), row))
    ordered = sorted(
        by_window.values(),
        key=lambda values: (
            min(at(row["label_span_start_utc"]) for _, row in values),
            values[0][1]["decision_window_id"],
        ),
    )
    active, selected, dispositions, audit = {}, [], Counter(), []
    for candidates in ordered:
        decision_at = min(at(row["label_span_start_utc"]) for _, row in candidates)
        active = {sym: end for sym, end in active.items() if end > decision_at}
        available = [
            (prediction, -float(row["cost_r"]), row["candidate_occurrence_key"], row)
            for prediction, row in candidates
            if row["symbol"] not in active
            and (policy != "market_rerank" or row["proposed_order_type"] == "MARKET")
        ]
        window_id = candidates[0][1]["decision_window_id"]
        record = {
            "decision_window_id": window_id,
            "decision_at_utc": decision_at.isoformat(),
            "n_candidates": len(candidates),
            "n_available": len(available),
            "active_symbols": sorted(active),
        }
        if not available:
            dispositions["no_available_candidate"] += 1
            record["disposition"] = "no_available_candidate"
            audit.append(record)
            continue
        ranked = sorted(available, key=lambda item: item[:3], reverse=True)
        record["top3"] = [
            {
                "key": row["candidate_occurrence_key"],
                "pred": round(prediction, 6),
                "order_type": row["proposed_order_type"],
                "family": row["origin_family"],
                "symbol": row["symbol"],
                "side": row["side"],
                "session": row["utc_session"],
                "state": m.fit._state(row) or "CENSORED",
                "net": clean(float(row.get("terminal_net_r") or 0.0))
                if m.fit._state(row) is not None
                else None,
            }
            for prediction, _neg, _key, row in ranked[:3]
        ]
        prediction, _neg_cost, _key, row = ranked[0]
        if prediction < m.MIN_EXPECTED_NET_R:
            dispositions["top_below_0p10"] += 1
            record["disposition"] = "top_below_0p10"
            audit.append(record)
            continue
        if policy == "market_top_abstain" and row["proposed_order_type"] != "MARKET":
            dispositions["top_limit_abstain"] += 1
            record["disposition"] = "top_limit_abstain"
            audit.append(record)
            continue
        dispositions["trade"] += 1
        record["disposition"] = "trade"
        record["chosen_key"] = row["candidate_occurrence_key"]
        audit.append(record)
        selected.append(dict(row, predicted_net_r=prediction))
        active[row["symbol"]] = at(row["label_span_end_utc"] or row["expiry_utc"])
    return selected, dict(sorted(dispositions.items())), audit


def rerun(feb_rows_by_day, aprmay_rows_by_day, feb_days, aprmay_days):
    """The exact prequential flow of s2.main + r3b.main, recording predictions and audit."""
    octnov = extract_octnov()
    jan = extract_jan()
    jan_by_day = defaultdict(list)
    for row in jan:
        jan_by_day[row["trading_day"]].append(row)

    training = r.resolved_eligible(octnov)
    for day, _authority in j.JAN_RUNS:
        training.extend(r.resolved_eligible(jan_by_day[day]))
    log(stage="training_bootstrap", rows=len(training))

    prediction_sink = {"feb": [], "aprmay": []}
    audit_sink = {"feb": [], "aprmay": []}
    selected_main = {"feb": [], "aprmay": []}
    pooled_policy_rows = {
        "feb": defaultdict(list), "aprmay": defaultdict(list)
    }
    day_dispositions = {"feb": {}, "aprmay": {}}

    def score_day(tag, day, rows):
        test = r.eligible(rows)
        if test:
            model = r.make_model()
            train_y = np.asarray(
                [float(row.get("terminal_net_r") or 0.0) for row in training], dtype=float
            )
            model.fit(r.frame(training), train_y, ridge__sample_weight=r.weights(training))
            predictions = model.predict(r.frame(test))
        else:
            predictions = []
        for row, prediction in zip(test, predictions):
            prediction_sink[tag].append(
                {"day": day, "key": row["candidate_occurrence_key"], "pred": float(prediction)}
            )
        disp_by_policy = {}
        for policy in ("market_top_abstain", "mixed", "market_rerank"):
            frozen_sel, frozen_disp = s2.select(test, predictions, policy=policy)
            audited_sel, audited_disp, audit = select_with_audit(
                test, predictions, policy=policy
            )
            assert [row["candidate_occurrence_key"] for row in frozen_sel] == [
                row["candidate_occurrence_key"] for row in audited_sel
            ], f"audit selection diverged from frozen select: {tag} {day} {policy}"
            assert frozen_disp == audited_disp
            disp_by_policy[policy] = frozen_disp
            pooled_policy_rows[tag][policy].extend(frozen_sel)
            if policy == "market_top_abstain":
                selected_main[tag].extend(frozen_sel)
                for record in audit:
                    record["trading_day"] = day
                audit_sink[tag].extend(audit)
        day_dispositions[tag][day] = disp_by_policy
        training.extend(r.resolved_eligible(rows))
        log(scored=day, tag=tag, training=len(training),
            main=disp_by_policy["market_top_abstain"])

    for day in feb_days:
        score_day("feb", day, feb_rows_by_day[day])
    for day in aprmay_days:
        score_day("aprmay", day, aprmay_rows_by_day[day])

    return prediction_sink, audit_sink, selected_main, pooled_policy_rows, day_dispositions


def verify(selected_main):
    feb_sealed = json.loads(FEB_RESULT_PATH.read_text(encoding="utf-8"))
    aprmay_sealed = json.loads(APRMAY_RESULT_PATH.read_text(encoding="utf-8"))
    out = {}
    for tag, sealed in (("feb", feb_sealed), ("aprmay", aprmay_sealed)):
        sealed_sel = sealed["selected_candidates"]
        mine = selected_main[tag]
        keys_match = [row["candidate_occurrence_key"] for row in mine] == [
            row["candidate_occurrence_key"] for row in sealed_sel
        ]
        pred_max_delta = max(
            (
                abs(float(row["predicted_net_r"]) - float(sr["predicted_net_r"]))
                for row, sr in zip(mine, sealed_sel)
            ),
            default=None,
        ) if keys_match else None
        actual = round(
            sum(
                float(row.get("terminal_net_r") or 0.0)
                for row in mine
                if m.fit._state(row) is not None
            ),
            6,
        )
        out[tag] = {
            "n_selected_mine": len(mine),
            "n_selected_sealed": len(sealed_sel),
            "keys_match_in_order": keys_match,
            "max_abs_predicted_delta": pred_max_delta,
            "actual_net_r_mine": actual,
            "actual_net_r_sealed": sealed["pooled"]["market_top_abstain"]["actual_net_r"],
            "sealed_payload_sha256": sealed["payload_sha256"],
        }
    return out


def main():
    rule = json.loads(RULE_PATH.read_text(encoding="utf-8"))
    prereg = json.loads(PREREG_PATH.read_text(encoding="utf-8"))
    feb_days = list(rule["validation"]["days_in_order"])
    assert feb_days == list(prereg["training"]["february_days"]), (
        "rule days_in_order != prereg training february_days; training-state fidelity "
        "with the sealed April+May run would break"
    )
    windows = prereg["validation"]["windows"]
    april_days = next(w["days"] for w in windows if w["window_id"] == "april_2026")
    may_days = next(w["days"] for w in windows if w["window_id"] == "may_2026")
    feb_binding = prereg["bindings"]["february_manifest_root_sha256"]
    april_binding = next(w["manifest_root_sha256"] for w in windows if w["window_id"] == "april_2026")
    may_binding = next(w["manifest_root_sha256"] for w in windows if w["window_id"] == "may_2026")

    feb_rows = extract_month("feb", FEB_ROOT, feb_days, "february_2026.json", feb_binding)
    april_rows = extract_month("april", NEW_ROOT, april_days, "april_2026.json", april_binding)
    may_rows = extract_month("may", NEW_ROOT, may_days, "may_2026.json", may_binding)

    by_day = defaultdict(list)
    for row in feb_rows:
        by_day[row["trading_day"]].append(row)
    feb_by_day = {day: by_day[day] for day in feb_days}
    by_day = defaultdict(list)
    for row in april_rows + may_rows:
        by_day[row["trading_day"]].append(row)
    aprmay_by_day = {day: by_day[day] for day in april_days + may_days}

    predictions, audits, selected_main, pooled_rows, day_disp = rerun(
        feb_by_day, aprmay_by_day, feb_days, april_days + may_days
    )

    for tag in ("feb", "aprmay"):
        write_rows(CACHE / f"predictions_{tag}.jsonl.gz", predictions[tag])
        write_rows(CACHE / f"window_audit_{tag}.jsonl.gz", audits[tag])

    integrity = verify(selected_main)
    receipt = {
        "schema": "gtos.wave21.postmortem.rerun_integrity.v1",
        "status": "DEVELOPMENT_DIAGNOSTIC_REUSING_FROZEN_LOADERS_NOT_A_NEW_RULE",
        "module_chain": {
            "r3b": str(R3B_PATH),
            "r3b_sha256": hashlib.sha256(R3B_PATH.read_bytes()).hexdigest(),
            "note": "r3b -> committed r2 scorer -> /private/tmp ridge -> old-worktree "
                    "candidate_funnel; identical to the chain that produced both sealed results",
        },
        "cache_dir": str(CACHE),
        "integrity": integrity,
        "population": {
            month: len(read_rows(CACHE / f"rows_{month}.jsonl.gz"))
            for month in ("octnov", "jan", "feb", "april", "may")
        },
        "day_dispositions": day_disp,
    }
    receipt["payload_sha256"] = r3b.canonical_hash(receipt)
    out = RECEIPTS / "PM_RERUN_INTEGRITY_V1.json"
    out.write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    log(done=str(out), integrity=integrity)


if __name__ == "__main__":
    main()
