#!/usr/bin/env python3
"""Acceptance harness: the forward-shadow's live path equals the research path.

Three modes, all read-only:

``--mode shadow-packets`` (the lane's acceptance test)
    Takes N days of the shadow's own decision-packet JSONL (plus its outcome
    log) and re-scores them decision-for-decision through the COMMITTED
    research pipeline: the frozen r2 scorer's ``feature_row`` rebuilds every
    model row from the logged raw candidate fields, the frozen JSON model
    re-predicts, and the frozen ``select(policy="market_top_abstain")``
    re-selects — general lane on all rows, scoped lane on the
    liquidity_sweep_reclaim restriction (bar-3).  Any feature, prediction, or
    selection divergence is a failure.

``--mode generation-probe`` (mainline-vs-frozen generator drift check)
    Regenerates candidates for chosen decision windows of a SEALED February
    day using MAINLINE production code over the frozen lane sources (offline,
    no MT5), and diffs the rule-consumed candidate surface against the sealed
    root's rows — the same consumed-field identity the rule's V1_1 amendment
    validated (6488/6488) when the execution layer changed.

``--mode model-golden``
    Re-checks the pure-python predictor against the committed sklearn golden
    fixture (also enforced in the test suite).

Run on the research Mac (frozen worktree + /private/tmp estate + lane hold
present).  Exit code 0 == parity holds.
"""

from __future__ import annotations

import argparse
import csv
import gzip
import importlib.util
import json
import math
import sys
from collections import Counter
from datetime import datetime, timedelta, timezone
from pathlib import Path
from types import SimpleNamespace
from typing import Any, Iterator, Mapping

HERE = Path(__file__).resolve()
MY_REPO = HERE.parents[7]
OA = HERE.parents[1]
R2_SCORER = OA / "w21_score_feb_market_top_r2.py"
ARTIFACT_PATH = HERE.parent / "SHADOW_RIDGE_MODEL_V1.json"
FIXTURE_PATH = HERE.parent / "GOLDEN_PARITY_FIXTURE_V1.json.gz"
HOLD = Path("/Users/borr/GTOSActive/lane-inputs-true-utc-hold-20260805")
MANIFEST_DIR = (
    HOLD
    / ".hermes/evidence/phase16/cj-rematerialization/LANE_INPUTS_TRUE_UTC_V1/manifests"
)
FEB_ROOT = Path("/private/tmp/w21-market-top-feb-r2")

LSR_FAMILY = "liquidity_sweep_reclaim"
FEATURE_TOLERANCE = 1e-9
PREDICTION_TOLERANCE = 1e-9

# The candidate surface the frozen rule consumes (V1_1 amendment,
# rule_consumed_fields_identical) — the generation probe diffs exactly these.
GENERATION_CONSUMED_FIELDS = (
    "symbol",
    "side",
    "origin_family",
    "session_bucket",
    "entry_price",
    "stop_loss",
    "take_profit_1",
    "risk_reward_ratio",
)


def load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def iter_jsonl(path: Path) -> Iterator[dict[str, Any]]:
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if line:
                yield json.loads(line)


def values_equal(a: Any, b: Any) -> bool:
    a_nan = isinstance(a, float) and math.isnan(a)
    b_nan = isinstance(b, float) and math.isnan(b)
    if a_nan or b_nan:
        return a_nan and b_nan
    if a is None or b is None:
        return a is None and b is None
    if isinstance(a, float) or isinstance(b, float):
        try:
            return abs(float(a) - float(b)) <= FEATURE_TOLERANCE
        except (TypeError, ValueError):
            return False
    return a == b


# ---------------------------------------------------------------------------
# shadow-packets mode
# ---------------------------------------------------------------------------


def run_shadow_packets(args) -> dict[str, Any]:
    # Import the shadow's own predictor FIRST (this repo), then purge `src`
    # bindings so the frozen research chain owns every later src.* import.
    sys.path.insert(0, str(MY_REPO))
    from src.research_infra.wave21_forward_shadow.ridge_artifact import load_model

    sys.path.remove(str(MY_REPO))
    for name in [n for n in list(sys.modules) if n == "src" or n.startswith("src.")]:
        del sys.modules[name]
    s2 = load_module("w21_score_feb_r2_frozen_for_parity", R2_SCORER)
    r = s2.r

    namespace = Path(args.packets).resolve()
    # Under the prequential daily refit each packet names the model that made
    # it (model_artifact_sha256): resolve every artifact — the committed V1
    # plus the namespace's dated dailies — and score each packet with ITS model.
    models_by_sha: dict[str, Any] = {}
    for candidate_path in [
        Path(args.model) if args.model else ARTIFACT_PATH,
        *sorted((namespace / "models").glob("SHADOW_RIDGE_DAILY_*.json")),
    ]:
        if candidate_path and Path(candidate_path).is_file():
            loaded = load_model(candidate_path)
            models_by_sha[loaded.artifact_sha256] = loaded
    default_model = load_model(args.model or ARTIFACT_PATH)

    packet_dir = namespace / "decision_packets"
    outcome_path = namespace / "order_outcomes.jsonl"
    packet_files = sorted(packet_dir.glob("*.jsonl"))
    if args.days:
        packet_files = packet_files[-int(args.days):]
    if not packet_files:
        raise SystemExit(f"no decision packets under {packet_dir}")

    outcomes: dict[str, dict[str, Any]] = {}
    if outcome_path.is_file():
        for row in iter_jsonl(outcome_path):
            if row.get("final") is True:
                outcomes[str(row.get("candidate_occurrence_key"))] = row

    def number(value: Any) -> float:
        try:
            out = float(value)
        except (TypeError, ValueError):
            return math.nan
        return out if math.isfinite(out) else math.nan

    def research_row(candidate: Mapping[str, Any]) -> dict[str, Any] | None:
        raw = dict(candidate["raw"])
        key = str(raw.get("canonical_replay_candidate_instance_key") or "")
        if not key.startswith("candidate_occurrence_") or len(key) != 85:
            return None
        # The shadow writes null for NaN (allow_nan=False JSONL); the research
        # number() treats null exactly as NaN, so raw passes through directly.
        submission = datetime.fromisoformat(raw["decision_time_utc"])
        expiry = datetime.fromisoformat(raw["limit_first_expiry_utc"])
        risk = abs(number(raw.get("entry_price")) - number(raw.get("stop_loss")))
        outcome = outcomes.get(key)
        deductible = sum(
            number(raw.get(field))
            for field in ("expected_slippage_r", "swap_cost_r", "commission_r")
            if not math.isnan(number(raw.get(field)))
        )
        label = {
            "candidate_occurrence_key": key,
            "decision_window_id": str(raw["decision_window_id"]),
            "trading_day": str(raw["trading_day"]),
            "label_span_start_utc": submission.isoformat(),
            "label_span_end_utc": (
                outcome.get("label_span_end_utc") if outcome else None
            ),
            "lifecycle_label_status": (
                outcome.get("lifecycle_label_status") if outcome else "SHADOW_PENDING"
            ),
            "cost_label_status": (
                outcome.get("cost_label_status") if outcome else "SHADOW_PENDING"
            ),
            "terminal_net_r": outcome.get("terminal_net_r") if outcome else None,
            "deductible_cost_r": deductible,
            "predecision_geometry_valid": bool(submission < expiry and risk > 0),
        }
        return s2.feature_row(raw, label)

    report: dict[str, Any] = {
        "mode": "shadow-packets",
        "namespace": str(namespace),
        "packet_files": [str(path) for path in packet_files],
        "model_artifact_sha256": default_model.artifact_sha256,
        "models_resolved": {
            sha[:16]: str(m.training_binding.get("mode", "flat_v1"))
            for sha, m in models_by_sha.items()
        },
        "packet_model_sha_unresolved": 0,
        "windows": 0,
        "candidates": 0,
        "eligible": 0,
        "feature_mismatches": [],
        "prediction_max_abs_diff": 0.0,
        "prediction_mismatches": 0,
        "occurrence_key_shape_failures": 0,
        "lanes": {},
    }

    lane_rows: dict[str, list[dict[str, Any]]] = {"general": [], "scoped_lsr": []}
    lane_predictions: dict[str, list[float]] = {"general": [], "scoped_lsr": []}
    logged_selection_by_window: dict[str, dict[str, Any]] = {}

    packets = []
    for path in packet_files:
        packets.extend(iter_jsonl(path))
    packets.sort(key=lambda row: str(row.get("decision_time_utc")))

    for packet in packets:
        report["windows"] += 1
        window_id = str(packet["decision_window_id"])
        logged_selection_by_window[window_id] = packet.get("selection") or {}
        packet_sha = str(packet.get("model_artifact_sha256") or "")
        model = models_by_sha.get(packet_sha)
        if model is None:
            model = default_model
            if packet_sha:
                report["packet_model_sha_unresolved"] += 1
        for candidate in packet.get("candidates") or ():
            report["candidates"] += 1
            rebuilt = research_row(candidate)
            if rebuilt is None:
                report["occurrence_key_shape_failures"] += 1
                continue
            logged_features = candidate.get("features")
            if candidate.get("eligible"):
                report["eligible"] += 1
                if isinstance(logged_features, Mapping):
                    for name in list(r.CAT) + list(r.NUM):
                        logged = logged_features.get(name)
                        logged = (
                            math.nan
                            if logged is None and name in set(r.NUM)
                            else logged
                        )
                        if not values_equal(rebuilt.get(name), logged):
                            report["feature_mismatches"].append(
                                {
                                    "window": window_id,
                                    "key": rebuilt["candidate_occurrence_key"],
                                    "feature": name,
                                    "research": repr(rebuilt.get(name)),
                                    "shadow": repr(logged),
                                }
                            )
                prediction = model.predict_row(rebuilt)
                logged_prediction = candidate.get("predicted_net_r")
                if logged_prediction is not None:
                    diff = abs(prediction - float(logged_prediction))
                    report["prediction_max_abs_diff"] = max(
                        report["prediction_max_abs_diff"], diff
                    )
                    if diff > PREDICTION_TOLERANCE:
                        report["prediction_mismatches"] += 1
                lane_rows["general"].append(rebuilt)
                lane_predictions["general"].append(prediction)
                if rebuilt["origin_family"] == LSR_FAMILY:
                    lane_rows["scoped_lsr"].append(rebuilt)
                    lane_predictions["scoped_lsr"].append(prediction)

    # Frozen selection replay per lane over the whole stream (occupancy is
    # causal inside s2.select: ordered by window start, ends from label span
    # or expiry — the outcome-joined rows carry exactly that).
    for lane in ("general", "scoped_lsr"):
        selected, dispositions = s2.select(
            lane_rows[lane], lane_predictions[lane], policy="market_top_abstain"
        )
        research_by_window = {
            row["decision_window_id"]: row["candidate_occurrence_key"]
            for row in selected
        }
        agreement = {"match": 0, "mismatch": 0, "detail": []}
        for window_id, logged in logged_selection_by_window.items():
            lane_logged = (logged or {}).get(lane)
            logged_key = (
                str(lane_logged["candidate_occurrence_key"]) if lane_logged else None
            )
            research_key = research_by_window.get(window_id)
            if logged_key == research_key:
                agreement["match"] += 1
            else:
                agreement["mismatch"] += 1
                if len(agreement["detail"]) < 40:
                    agreement["detail"].append(
                        {
                            "window": window_id,
                            "shadow": logged_key,
                            "research": research_key,
                        }
                    )
        report["lanes"][lane] = {
            "research_selected": len(selected),
            "research_dispositions": dispositions,
            "window_agreement": agreement,
        }

    report["pass"] = bool(
        not report["feature_mismatches"]
        and report["prediction_mismatches"] == 0
        and report["occurrence_key_shape_failures"] == 0
        and report["packet_model_sha_unresolved"] == 0
        and all(
            lane["window_agreement"]["mismatch"] == 0
            for lane in report["lanes"].values()
        )
    )
    return report


# ---------------------------------------------------------------------------
# generation-probe mode
# ---------------------------------------------------------------------------


class OfflineManifestAdapter:
    """MT5-shaped closed-bar source over the frozen lane CSVs (probe only)."""

    def __init__(self, frames_by_symbol: Mapping[str, Mapping[str, list[dict]]]):
        self.frames = frames_by_symbol
        self.asof: datetime | None = None
        self._tf_names = {1: "M1", 15: "M15", 16385: "H1", 16388: "H4", 16408: "D1"}
        self._by_broker_symbol = {}

    def register_broker_symbol(self, broker_symbol: str, canonical: str) -> None:
        self._by_broker_symbol[broker_symbol] = canonical

    def get_candles(self, symbol: str, timeframe: int, count: int) -> list[dict]:
        from src.research_infra.completed_bar_witness import (
            observed_successor_closed_bar_rows_until,
        )

        canonical = self._by_broker_symbol.get(symbol, symbol)
        tf_name = self._tf_names[int(timeframe)]
        rows = self.frames[canonical][tf_name]
        witnessed = observed_successor_closed_bar_rows_until(
            rows,
            timeframe=tf_name,
            asof=self.asof,
            max_rows=int(count),
            attach_witness=True,
        )
        return [dict(row) for row in witnessed]

    def get_tick(self, symbol: str = "XAUUSD"):
        return None

    def get_ticks_range(self, *_args, **_kwargs):
        return []

    def get_positions(self, *_args, **_kwargs):
        return []


def run_generation_probe(args) -> dict[str, Any]:
    # MAINLINE production code drives generation here — that is the point.
    sys.path.insert(0, str(MY_REPO))
    from src.components.broader_origin_generators import (
        generate_live_broader_origin_candidates,
    )
    from src.components.data_ingestion import ingest_live_data
    from src.components.market_state import compute_market_state
    from src.research_infra import v4_timewarp_simulated_live_research_loop as timewarp
    from src.research_infra.replay_compact_event_sink import ReplayCompactEventSink
    from src.research_infra.wave21_forward_shadow.decision_transforms import (
        apply_dynamic_target_geometry,
        apply_ledger_session_aliases,
        mint_occurrence_identity,
        stamp_preselector_admission,
    )
    from src.research_infra.wave21_forward_shadow.mt5_read_only import (
        aggregate_h1_rows_from_m15_rows,
    )
    from src.research_infra.wave21_forward_shadow.runner_config import (
        ShadowRunnerConfig,
        build_decision_config,
    )

    day = args.day
    manifest = json.loads((MANIFEST_DIR / "february_2026.json").read_text())
    frames: dict[str, dict[str, list[dict]]] = {}
    for entry in manifest["bar_sources"]:
        tf = entry["timeframe"]
        if tf not in {"D1", "H4", "M15"}:
            continue
        path = HOLD / entry["repo_relpath"]
        with path.open(newline="", encoding="utf-8") as handle:
            rows = [
                {
                    "time": row["time"],
                    "time_utc": row["time"],
                    "open": float(row["open"]),
                    "high": float(row["high"]),
                    "low": float(row["low"]),
                    "close": float(row["close"]),
                    "volume": float(row.get("volume") or 0.0),
                }
                for row in csv.DictReader(handle)
            ]
        frames.setdefault(entry["symbol"], {})[tf] = rows
    for symbol, by_tf in frames.items():
        by_tf["H1"] = aggregate_h1_rows_from_m15_rows(by_tf["M15"], symbol=symbol)

    runner_config = ShadowRunnerConfig(
        repo_root=MY_REPO,
        namespace_dir=MY_REPO / "shadow_logs" / "funnel_shadow",
        model_artifact_path=ARTIFACT_PATH,
    )
    decision_config, fingerprints = build_decision_config(
        runner_config, load_config=timewarp.load_config
    )
    adapter = OfflineManifestAdapter(frames)
    for symbol in timewarp.GTOS_24_SYMBOL_SURFACE:
        adapter.register_broker_symbol(timewarp.ftmo_symbol(symbol), symbol)

    summary = json.loads((FEB_ROOT / day / "run_summary.json").read_text())
    sink = ReplayCompactEventSink.open_sealed(
        root=FEB_ROOT / day / "compact_events",
        expected_authority_root_sha256=summary["authority_root_sha256"],
    )
    sealed_rows = list(sink.ledger("missed"))
    sealed_by_window: dict[str, list[dict]] = {}
    for row in sealed_rows:
        sealed_by_window.setdefault(str(row["decision_time_utc"]), []).append(row)
    window_times = sorted(sealed_by_window)
    if args.windows:
        stride = max(1, len(window_times) // int(args.windows))
        window_times = window_times[::stride][: int(args.windows)]

    report: dict[str, Any] = {
        "mode": "generation-probe",
        "day": day,
        "config_fingerprints": fingerprints,
        "windows_probed": 0,
        "sealed_candidates": 0,
        "mainline_candidates": 0,
        "occurrence_key_matches": 0,
        "consumed_field_matches": 0,
        "population_mismatch_windows": [],
        "field_mismatches": [],
        "feature_mismatches": [],
    }

    for window_time in window_times:
        asof = datetime.fromisoformat(window_time)
        adapter.asof = asof
        raw_by_symbol: dict[str, Any] = {}
        mso_by_symbol: dict[str, Any] = {}
        sealed = sealed_by_window[window_time]
        # Probe the FULL 24-symbol surface, not just symbols with sealed
        # candidates — a mainline-only candidate on a quiet symbol must count
        # as a population mismatch, not slip through unprobed.
        symbols_in_window = sorted(timewarp.GTOS_24_SYMBOL_SURFACE)
        for symbol in symbols_in_window:
            symbol_config = timewarp.replay_symbol_config(decision_config, symbol)
            market_state_cfg = symbol_config.setdefault("market_state", {})
            market_state_cfg["side_effect_writes_enabled"] = False
            market_state_cfg["structure_shadow_log_enabled"] = False
            raw = ingest_live_data(adapter, symbol_config, now_utc=asof)
            raw_by_symbol[symbol] = raw
            mso_by_symbol[symbol] = compute_market_state(raw, symbol_config)
        cross_asset = {"raw_data_by_symbol": raw_by_symbol}
        mainline_by_key: dict[str, dict] = {}
        mainline_by_candidate_id: dict[str, dict] = {}
        mainline_all: list[dict] = []
        for symbol in symbols_in_window:
            generated = generate_live_broader_origin_candidates(
                dict(raw_by_symbol[symbol]),
                mso_by_symbol[symbol],
                decision_config,
                symbol,
                timewarp.derive_session(symbol, asof),
                cross_asset_raw_data=cross_asset,
                now_utc=asof,
            )
            enriched = timewarp.enrich_candidates_with_predecision_market_snapshot(
                generated, raw_by_symbol[symbol], asof_utc=asof.isoformat()
            )
            for candidate in enriched:
                # Same post-generation chain the shadow runner applies (the
                # sealed rows are post-dynamic-geometry with minted identity).
                candidate = dict(candidate)
                candidate.setdefault("decision_time_utc", asof.isoformat())
                candidate = stamp_preselector_admission(candidate)
                candidate = apply_dynamic_target_geometry(
                    candidate, config=decision_config
                )
                candidate = apply_ledger_session_aliases(
                    candidate, decision_time_utc=asof.isoformat()
                )
                candidate = mint_occurrence_identity(
                    candidate, decision_time_utc=asof.isoformat()
                )
                mainline_all.append(candidate)
                key = str(
                    candidate.get("canonical_replay_candidate_instance_key") or ""
                )
                if key:
                    mainline_by_key[key] = candidate
                cid = str(candidate.get("candidate_id") or "")
                if cid:
                    mainline_by_candidate_id[cid] = candidate

        report["windows_probed"] += 1
        report["sealed_candidates"] += len(sealed)
        report["mainline_candidates"] += len(mainline_all)
        if len(sealed) != len(mainline_all):
            report["population_mismatch_windows"].append(
                {
                    "window": window_time,
                    "sealed": len(sealed),
                    "mainline": len(mainline_all),
                    "sealed_families": dict(
                        Counter(str(row["origin_family"]) for row in sealed)
                    ),
                    "mainline_families": dict(
                        Counter(str(row["origin_family"]) for row in mainline_all)
                    ),
                }
            )
        for sealed_row in sealed:
            key = str(sealed_row.get("canonical_replay_candidate_instance_key") or "")
            twin = mainline_by_key.get(key)
            if twin is not None:
                report["occurrence_key_matches"] += 1
            else:
                # Identity preimage may legitimately differ across generator
                # generations; the consumed-surface comparison still binds via
                # the stable legacy candidate_id join.
                twin = mainline_by_candidate_id.get(
                    str(sealed_row.get("candidate_id") or "")
                )
            if twin is None:
                report.setdefault("unjoined_sealed_candidates", 0)
                report["unjoined_sealed_candidates"] += 1
                continue
            fields_match = True
            for field in GENERATION_CONSUMED_FIELDS:
                if not values_equal(sealed_row.get(field), twin.get(field)):
                    fields_match = False
                    if len(report["field_mismatches"]) < 60:
                        report["field_mismatches"].append(
                            {
                                "window": window_time,
                                "key": key,
                                "field": field,
                                "sealed": repr(sealed_row.get(field)),
                                "mainline": repr(twin.get(field)),
                            }
                        )
            sealed_features = sealed_row.get("predecision_features") or {}
            twin_features = twin.get("predecision_features") or {}
            for name, sealed_value in sealed_features.items():
                if not values_equal(sealed_value, twin_features.get(name)):
                    fields_match = False
                    if len(report["feature_mismatches"]) < 60:
                        report["feature_mismatches"].append(
                            {
                                "window": window_time,
                                "key": key,
                                "feature": name,
                                "sealed": repr(sealed_value),
                                "mainline": repr(twin_features.get(name)),
                            }
                        )
            if fields_match:
                report["consumed_field_matches"] += 1

    report["pass"] = bool(
        report["windows_probed"] > 0
        and not report["population_mismatch_windows"]
        and not report["field_mismatches"]
        and not report["feature_mismatches"]
        and not report.get("unjoined_sealed_candidates")
        and report["consumed_field_matches"] == report["sealed_candidates"]
    )
    report["occurrence_key_identity_preserved"] = bool(
        report["occurrence_key_matches"] == report["sealed_candidates"]
    )
    return report


# ---------------------------------------------------------------------------
# model-golden mode
# ---------------------------------------------------------------------------


def run_model_golden(args) -> dict[str, Any]:
    sys.path.insert(0, str(MY_REPO))
    from src.research_infra.wave21_forward_shadow.ridge_artifact import load_model

    model = load_model(args.model or ARTIFACT_PATH)
    with gzip.open(args.fixture or FIXTURE_PATH, "rt", encoding="utf-8") as handle:
        fixture = json.load(handle)
    if fixture["artifact_sha256"] != model.artifact_sha256:
        raise SystemExit(
            "fixture was produced for a different artifact: "
            f"{fixture['artifact_sha256']} != {model.artifact_sha256}"
        )
    max_diff = 0.0
    for row, expected in zip(fixture["rows"], fixture["sklearn_predictions"]):
        got = model.predict_row(row)
        max_diff = max(max_diff, abs(got - float(expected)))
    return {
        "mode": "model-golden",
        "rows": len(fixture["rows"]),
        "sklearn_version_at_fit": fixture["sklearn_version"],
        "max_abs_diff": max_diff,
        "pass": bool(max_diff < 1e-9 and len(fixture["rows"]) >= 1000),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--mode",
        required=True,
        choices=["shadow-packets", "generation-probe", "model-golden"],
    )
    parser.add_argument("--packets", help="shadow namespace dir (shadow-packets)")
    parser.add_argument("--days", type=int, default=0, help="last N packet days")
    parser.add_argument("--day", default="2026-02-03", help="sealed day (probe)")
    parser.add_argument("--windows", type=int, default=4, help="windows to probe")
    parser.add_argument("--model", default=None)
    parser.add_argument("--fixture", default=None)
    parser.add_argument("--out", default=None, help="write the JSON report here")
    args = parser.parse_args()

    if args.mode == "shadow-packets":
        if not args.packets:
            parser.error("--packets required for shadow-packets")
        report = run_shadow_packets(args)
    elif args.mode == "generation-probe":
        report = run_generation_probe(args)
    else:
        report = run_model_golden(args)

    text = json.dumps(report, indent=2, sort_keys=True, default=str)
    if args.out:
        Path(args.out).write_text(text + "\n", encoding="utf-8")
    print("SHADOW_PARITY=" + json.dumps(
        {k: v for k, v in report.items() if k not in {"packet_files"}},
        sort_keys=True,
        default=str,
    )[:4000], flush=True)
    return 0 if report.get("pass") else 1


if __name__ == "__main__":
    raise SystemExit(main())
