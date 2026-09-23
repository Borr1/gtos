#!/usr/bin/env python3
"""Independent behavioral verifier for the Wave-21 W7 current-truth outputs.

This verifier intentionally does not import ``w7_current_recost.py``.  It reopens the
source bytes with a separate stdlib CSV parser, independently applies broker-clock
conversion, reruns the production sleeve generators, reruns the production path walker,
spread/floor/cost implementations, and then checks the published ledgers and summaries.
That makes it evidence against a producer defect rather than a second arithmetic pass over
the producer's JSON.
"""

from __future__ import annotations

import collections
import copy
import csv
import datetime as dt
import gzip
import hashlib
import json
import math
import re
import statistics
import sys
from dataclasses import asdict
from pathlib import Path
from typing import Any, Mapping, Sequence

import yaml


REPO = Path(__file__).resolve().parents[5]
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(REPO))

from src.components.ultimate_book.admission import winsorize_R  # noqa: E402
from src.components.ultimate_book.execution_packets import (  # noqa: E402
    M15_BARS_PER,
    resolve_exit_profile,
)
from src.components.ultimate_book.primitives import Bar  # noqa: E402
from src.components.ultimate_book.sleeves import (  # noqa: E402
    crypto as crypto_generator,
    energy_agri as energy_generator,
    substrate as substrate_generator,
)
from src.components.ultimate_book.spread_geometry import resolve_floor_limit  # noqa: E402
from src.components.ultimate_book.symbol_map import build_broker_symbol_resolver  # noqa: E402
from src.costs import CostTruthError, cost_r, load_broker_true_costs  # noqa: E402
from src.costs.spread_model import (  # noqa: E402
    SpreadModelError,
    load_spread_model,
    spread_price,
)
from src.research_infra.walkforward.exits import ExitPolicy, PathResult, replay  # noqa: E402
from src.research_infra.walkforward.quote_side import BarQuote, replay_anchor  # noqa: E402
from src.safety.armed_set import (  # noqa: E402
    armed_sleeves,
    assert_consistent,
    declared_arming,
)
from src.utils.broker_clock import (  # noqa: E402
    broker_epoch_to_utc,
    broker_naive_to_utc,
    resolve_rule,
)
from src.utils.config import apply_profile_overrides  # noqa: E402


RESULT = HERE / "W7_CURRENT_RECOST_V1.json"
ROWS = HERE / "W7_CURRENT_ROWS_V1.jsonl.gz"
SOURCE_CELLS = HERE / "W7_CURRENT_SOURCE_CELLS_V1.jsonl"
PRIOR = HERE / "PRIOR_RECONCILIATION_V1.json"
MANIFEST = HERE / "W7_CURRENT_INPUT_MANIFEST_V1.json"
REPORT = HERE / "W7_CURRENT_REPORT_V1.md"
OUT = HERE / "W7_CURRENT_VERIFICATION_V1.json"
COSTS_PATH = (
    REPO
    / "research/operations/broker_truth_layer_2026_07_29/BROKER_TRUE_COSTS_V1_1.json"
)
SPREAD_PATH = REPO / "research/operations/spread_model_2026_07_29/SPREAD_MODEL_V1.json"

WINDOW_START = dt.date(2015, 2, 25)
WINDOW_END = dt.date(2026, 6, 12)
CALENDAR_DAYS = (WINDOW_END - WINDOW_START).days + 1
H4_DELTA = dt.timedelta(hours=4)
H4_MINUTES = 240
PRODUCTION_CLOSED_BARS = 259
RESEARCH_MAXBARS = 80
BANDS = ("low", "mid", "high")
SCORECARD_RECOMMENDATIONS = ("KEEP", "REPAIR", "RESEARCH_ONLY", "NE")
VALID_COVERAGE = {"MEASURED", "TRANSFERRED", "MODELLED", "NOT_EVALUABLE"}
QUOTE_MODEL = "H4_BID_OHLC_SCALAR_ENTRY_SPREAD_CONSERVATIVE_OPEN_GAP"
_EPOCH_TOKEN = re.compile(r"^[+-]?\d+(?:\.\d+)?$")

ACCOUNT_META = {
    "operator_profile": {"account": "FTMO", "server": "FTMO-Server3"},
    "redacted_account_live_bee34003": {
        "account": "redacted_account",
        "server": "redacted_account-Server 2",
    },
}
GENERATOR = {
    "crypto": crypto_generator.generate,
    "energy_agri": energy_generator.generate,
    "sub_xvol_pullback": substrate_generator.generate_sub_xvol_pullback,
    "sub_mid_dn_revert": substrate_generator.generate_sub_mid_dn_revert,
}
SURFACE = {
    "crypto": tuple(crypto_generator.ON_SURFACE),
    "energy_agri": tuple(energy_generator.ON_SURFACE),
    "sub_xvol_pullback": tuple(substrate_generator.XVOL_ON_SURFACE),
    "sub_mid_dn_revert": tuple(substrate_generator.MIDDN_ON_SURFACE),
}
EXPECTED_SUPPORTED_GAPS = {
    "operator_profile": {
        ("sub_mid_dn_revert", "CORN_c"),
        ("sub_mid_dn_revert", "COTTON_c"),
        ("sub_xvol_pullback", "CORN_c"),
        ("sub_xvol_pullback", "COTTON_c"),
        ("sub_xvol_pullback", "FRA40_cash"),
        ("sub_xvol_pullback", "EU50_cash"),
        ("sub_xvol_pullback", "US2000_cash"),
    },
    "redacted_account_live_bee34003": {
        ("sub_xvol_pullback", "FRA40_cash"),
        ("sub_xvol_pullback", "EU50_cash"),
        ("sub_xvol_pullback", "US2000_cash"),
    },
}


def sha(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def load_jsonl(path: Path, *, compressed: bool = False) -> list[dict]:
    opener = gzip.open if compressed else open
    with opener(path, "rt", encoding="utf-8") as fh:
        return [json.loads(line) for line in fh if line.strip()]


def check(condition: bool, label: str, failures: list[str]) -> None:
    if not condition and label not in failures and len(failures) < 250:
        failures.append(label)


def close(a: Any, b: Any, *, tol: float = 1e-10) -> bool:
    if a is None or b is None:
        return a is None and b is None
    return math.isclose(float(a), float(b), rel_tol=0.0, abs_tol=tol)


def independent_parse(path: Path) -> tuple[tuple[Bar, ...], tuple[dt.datetime, ...]]:
    """Parse source bytes without the producer's CsvBarSource implementation."""
    sidecar = Path(str(path) + ".timebase.json")
    meta = json.loads(sidecar.read_text())
    rule = None
    basis = meta.get("time_column_basis")
    if meta.get("timebase") == "broker_server_wall_clock":
        rule = resolve_rule(str(meta["broker"]))
    elif basis == "broker_server_local":
        rule = resolve_rule(str(meta["broker_clock_server"]))
    elif basis not in {"utc", "true_utc"}:
        raise ValueError(f"unrecognised sidecar basis for {path}: {meta}")

    bars: list[Bar] = []
    times: list[dt.datetime] = []
    opener = gzip.open if str(path).endswith(".gz") else open
    with opener(path, "rt", encoding="utf-8", newline="") as fh:
        for rec in csv.DictReader(fh):
            raw = str(rec.get("time") or "").strip()
            if not raw:
                continue
            if _EPOCH_TOKEN.fullmatch(raw):
                if rule is None:
                    stamp = dt.datetime.fromtimestamp(float(raw), tz=dt.timezone.utc)
                else:
                    stamp = broker_epoch_to_utc(float(raw), rule)
            else:
                parsed = dt.datetime.fromisoformat(raw.replace("Z", "+00:00"))
                if rule is None:
                    stamp = (
                        parsed.replace(tzinfo=dt.timezone.utc)
                        if parsed.tzinfo is None else parsed.astimezone(dt.timezone.utc)
                    )
                else:
                    stamp = broker_naive_to_utc(parsed.replace(tzinfo=None), rule)
            bars.append(Bar(
                float(rec["open"]), float(rec["high"]),
                float(rec["low"]), float(rec["close"]),
                float(rec.get("tick_volume") or rec.get("volume") or 0.0),
            ))
            times.append(stamp)
    order = sorted(range(len(times)), key=lambda idx: times[idx])
    bars = [bars[idx] for idx in order]
    times = [times[idx] for idx in order]
    if not bars or len(times) != len(set(times)):
        raise ValueError(f"empty or duplicate-time source: {path}")
    return tuple(bars), tuple(times)


def exit_policy(sleeve: str, frontier_exits: Sequence[str], stop: float,
                intent_target: float | None) -> tuple[ExitPolicy, dict]:
    prof = resolve_exit_profile(sleeve, frontier_exits=frontier_exits)
    own_bars = int(round(int(prof["time_stop_bars"]) / M15_BARS_PER["H4"]))
    if own_bars != RESEARCH_MAXBARS:
        raise ValueError(f"unexpected time stop: {sleeve}:{own_bars}")
    mode = str(prof["policy"])
    if prof.get("final_from_intent"):
        target = intent_target
    else:
        target = (
            float(prof["final_target_r"]) * stop
            if prof.get("final_target_r") is not None else None
        )
    partial_at = float(prof["trigger_r"]) if mode == "partial_be_runner" else None
    if mode not in {"partial_be_runner", "time_stop"}:
        raise ValueError(f"unsupported policy: {sleeve}:{mode}")
    policy = ExitPolicy(
        target_dist=target,
        maxbars=RESEARCH_MAXBARS,
        time_stop_bars=own_bars,
        partial_at_r=partial_at,
        partial_frac=float(prof.get("partial_close_ratio", 0.5)),
        be_stop_after_partial=bool(partial_at),
        label=f"current:{mode}",
    )
    return policy, {
        "resolved_profile": copy.deepcopy(prof),
        "time_stop_h4_bars": own_bars,
        "policy": mode,
    }


def gap_conservative(bars: Sequence[Bar], entry: float, direction: int, stop: float,
                     result: PathResult) -> tuple[float, dict[str, Any]]:
    j = int(result.exit_index)
    bar = bars[j]
    bank = float(result.detail.get("partial_banked_r", 0.0) or 0.0)
    taken = float(result.detail.get("partial_frac_taken", 0.0) or 0.0)

    def at_price(px: float) -> float:
        raw = ((px - entry) if direction > 0 else (entry - px)) / stop
        return bank + (1.0 - taken) * raw

    level_r = float(result.r_gross)
    if result.exit_reason == "stop":
        level = entry if taken else entry - direction * stop
        through = (direction > 0 and bar.o < level) or (direction < 0 and bar.o > level)
        if through:
            raw = at_price(float(bar.o))
            return raw, {
                "gap_leg": "breakeven_stop" if taken else "stop",
                "gap_fill_price": float(bar.o),
                "gap_level": float(level),
                "gap_delta_r_raw": raw - level_r,
            }
    return level_r, {
        "gap_leg": None,
        "gap_fill_price": None,
        "gap_level": None,
        "gap_delta_r_raw": 0.0,
    }


def weakest(*classes: str) -> str:
    order = {"MEASURED": 0, "TRANSFERRED": 1, "MODELLED": 2, "NOT_EVALUABLE": 3}
    return max(classes, key=lambda item: order[item])


def value_stats(rows: Sequence[dict], field: str) -> dict[str, Any]:
    values = [float(row[field]) for row in rows if row.get(field) is not None]
    return {
        "n": len(values),
        "mean": round(statistics.fmean(values), 6) if values else None,
        "sum": round(math.fsum(values), 6) if values else None,
    }


def concentration_view(rows: Sequence[dict], field: str, bucket: str) -> dict[str, Any]:
    grouped: dict[str, float] = collections.defaultdict(float)
    for row in rows:
        if row.get(field) is None:
            continue
        if bucket == "symbol":
            key = str(row["symbol_canonical"])
        elif bucket == "year":
            key = str(dt.datetime.fromisoformat(row["entry_utc"]).year)
        else:  # pragma: no cover - verifier misuse guard
            raise ValueError(bucket)
        grouped[key] += float(row[field])
    total_abs = math.fsum(abs(value) for value in grouped.values())
    ordered = sorted(grouped.items(), key=lambda item: (-abs(item[1]), item[0]))
    return {
        "hhi_absolute": (
            math.fsum((abs(value) / total_abs) ** 2 for value in grouped.values())
            if total_abs else None
        ),
        "top": ordered[0] if ordered else None,
        "top_share_abs_pct": (
            abs(ordered[0][1]) / total_abs * 100.0
            if ordered and total_abs else None
        ),
    }


def main() -> int:
    failures: list[str] = []
    assert_consistent()
    declaration = declared_arming()
    result = json.loads(RESULT.read_text())
    prior = json.loads(PRIOR.read_text())
    manifest = json.loads(MANIFEST.read_text())
    report = REPORT.read_text()
    rows = load_jsonl(ROWS, compressed=True)
    source_cells = load_jsonl(SOURCE_CELLS)

    # Artifact and authority closure.
    check(result["row_ledger"]["sha256"] == sha(ROWS), "row_ledger_sha", failures)
    check(result["source_cell_ledger"]["sha256"] == sha(SOURCE_CELLS),
          "source_cell_ledger_sha", failures)
    check(result["prior_reconciliation"]["sha256"] == sha(PRIOR), "prior_sha", failures)
    check(result["inputs"]["manifest_sha256"] == sha(MANIFEST), "manifest_sha", failures)
    check(manifest["source_cell_ledger"]["sha256"] == sha(SOURCE_CELLS),
          "manifest_source_cell_sha", failures)
    for rel, expected in manifest["committed_inputs"].items():
        path = REPO / rel
        check(path.is_file(), f"committed_input_present:{rel}", failures)
        if path.is_file():
            check(sha(path) == expected, f"committed_input_sha:{rel}", failures)

    check(result["status"] == "NOT_EVALUABLE_HIGHER_INFORMATION_STOP",
          "global_not_evaluable", failures)
    check(result["headline_status"] == "W7_NOT_EVALUABLE_HIGHER_INFORMATION_STOP",
          "headline_not_evaluable", failures)
    check(result["headline_eligible"] is False, "headline_ineligible", failures)
    check("W7_NOT_EVALUABLE_HIGHER_INFORMATION_STOP" in report,
          "report_not_evaluable_headline", failures)
    check("MODELLED" in report and "never `COMPLETE` or `MEASURED`" in report,
          "report_modelled_quote_boundary", failures)
    check("not** claimed as an unconditional occurrence" in report,
          "report_calendar_denominator_boundary", failures)
    check("first-fit" in report and "does not transfer" in report,
          "report_native_headroom_boundary", failures)
    check("decision ordinal" in report,
          "report_native_slot_conservation_boundary", failures)
    check(result["scope"]["selector_v4_decisions_measured"] is False,
          "selector_scope_false", failures)
    check(result["scope"]["scheduler_v4_decisions_measured"] is False,
          "scheduler_scope_false", failures)
    shim = result["native_flow_truth"]["execution_packet_selector_scheduler_fields"]
    check(shim["status"] == "COMPATIBILITY_SHIMS_NOT_SHARED_DECISIONS",
          "execution_packet_fields_are_shims", failures)
    check(result["native_flow_truth"]["overall_status"]
          == "NOT_EVALUABLE_NATIVE_GRAPH_INCOMPLETE", "native_graph_incomplete", failures)
    slot_conservation = result["native_flow_truth"][
        "production_wrapper_slot_conservation"
    ]
    check(slot_conservation["status"]
          == "NOT_EVALUABLE_NO_TYPED_DECISION_ORDINAL_TERMINALS",
          "native_wrapper_slot_conservation_ne", failures)
    check(slot_conservation[
        "full_scheduled_or_native_wrapper_opportunity_denominator_complete"
    ] is False, "native_wrapper_full_denominator_false", failures)

    # The source-cell ledger is a complete requested-cell roster, not an
    # occurrence denominator. Every account/sleeve/symbol appears exactly once, while
    # absent scheduled bars remain unknown because no symbol calendar is bound.
    expected_roster = {
        (namespace, sleeve, symbol)
        for namespace in declaration
        for sleeve in armed_sleeves(namespace)
        for symbol in SURFACE[sleeve]
    }
    actual_roster = {
        (row["namespace"], row["sleeve"], row["symbol_canonical"])
        for row in source_cells
    }
    check(len(actual_roster) == len(source_cells), "source_cell_duplicate", failures)
    check(actual_roster == expected_roster, "source_cell_roster_complete", failures)
    check(all(
        row["nominal_window_calendar_days_inclusive"] == CALENDAR_DAYS
        for row in source_cells
    ), "source_cell_nominal_calendar_window", failures)
    check(all(
        row["calendar_schedule_authority_status"]
        == "NOT_EVALUABLE_STREAM_SCHEDULE_UNBOUND"
        for row in source_cells
    ), "source_cell_schedule_unbound", failures)
    check(all(
        row["calendar_denominator_claimed_unconditional"] is False
        for row in source_cells
    ), "source_cell_calendar_not_claimed_unconditional", failures)

    missing_by_ns: dict[str, set[tuple[str, str]]] = collections.defaultdict(set)
    for cell in source_cells:
        status = cell["source_status"]
        check(status in {
            "LOADED_OBSERVED_ROWS_WITH_EMISSIONS",
            "LOADED_OBSERVED_ROWS_NO_EMISSION", "MISSING_SOURCE",
            "OUTSIDE_ACTIVE_PROFILE",
        }, f"source_cell_status:{status}", failures)
        if status == "LOADED_OBSERVED_ROWS_NO_EMISSION":
            check(cell["observed_candidate_emissions"] == 0,
                  "loaded_observed_rows_no_emission_is_zero", failures)
            check(cell["full_window_candidate_emissions"] is None,
                  "loaded_zero_not_full_window_noop", failures)
        if status.startswith("LOADED_OBSERVED_ROWS_"):
            check(cell["candidate_occurrence_completeness"]
                  == "OBSERVED_SOURCE_ROWS_PARTIAL_ONLY_SCHEDULE_UNBOUND",
                  "loaded_occurrence_partial", failures)
            check(cell["full_window_candidate_emissions"] is None,
                  "loaded_full_window_count_unknown", failures)
        if status == "MISSING_SOURCE":
            missing_by_ns[cell["namespace"]].add(
                (cell["sleeve"], cell["symbol_canonical"])
            )
            check(cell["profile_support_status"] == "SUPPORTED",
                  "missing_cell_is_supported", failures)
            check(cell["observed_candidate_emissions"] is None,
                  "missing_candidate_count_unknown", failures)
            check(cell["candidate_occurrence_completeness"]
                  == "NOT_EVALUABLE_MISSING_SOURCE_UNKNOWN_NOT_ZERO",
                  "missing_count_not_zero", failures)
        if status == "OUTSIDE_ACTIVE_PROFILE":
            check(cell["observed_candidate_emissions"] is None,
                  "outside_profile_candidate_count_null", failures)
    check(dict(missing_by_ns) == EXPECTED_SUPPORTED_GAPS,
          "exact_supported_gap_set_7_ftmo_3_fn", failures)
    check(result["source_gap_counts"] == {
        namespace: len(EXPECTED_SUPPORTED_GAPS[namespace])
        for namespace in sorted(EXPECTED_SUPPORTED_GAPS)
    }, "source_gap_counts_7_3", failures)
    check(result["aggregate_evaluation"]["missing_supported_source_cells"] == 10,
          "aggregate_missing_ten", failures)

    # Reopen and independently parse every external source.  The producer's parsed rows
    # are not trusted for this step.
    parsed: dict[tuple[str, str], tuple[tuple[Bar, ...], tuple[dt.datetime, ...]]] = {}
    parsed_rows = 0
    for source in manifest["external_series_consumed"]:
        path = Path(source["path"])
        sidecar = Path(source["sidecar"])
        check(path.is_file() and sha(path) == source["sha256"],
              f"external_source_sha:{path.name}", failures)
        check(sidecar.is_file() and sha(sidecar) == source["sidecar_sha256"],
              f"external_sidecar_sha:{path.name}", failures)
        bars, times = independent_parse(path)
        key = (source["namespace"], source["symbol_canonical"])
        parsed[key] = (bars, times)
        parsed_rows += len(times)
        check(len(times) == int(source["rows"]), f"independent_parse_rows:{key}", failures)
        check(times[0].isoformat() == source["first_true_utc"],
              f"independent_parse_first:{key}", failures)
        check(times[-1].isoformat() == source["last_true_utc"],
              f"independent_parse_last:{key}", failures)

    # Rerun each production generator for each loaded cell and compare occurrence
    # identities and values to the producer ledger before any quote/cost arithmetic.
    generated: dict[tuple, dict] = {}
    generator_bar_evaluations = 0
    for cell in source_cells:
        if not str(cell["source_status"]).startswith("LOADED_OBSERVED_ROWS_"):
            continue
        key = (cell["namespace"], cell["symbol_canonical"])
        bars, times = parsed[key]
        sleeve = str(cell["sleeve"])
        fn = GENERATOR[sleeve]
        seen: set[tuple[str, str, int]] = set()
        candidates = 0
        evaluations = 0
        for idx in range(PRODUCTION_CLOSED_BARS - 1, len(bars) - RESEARCH_MAXBARS):
            entry_utc = times[idx] + H4_DELTA
            if entry_utc.date() < WINDOW_START or entry_utc.date() > WINDOW_END:
                continue
            evaluations += 1
            intent = fn(
                cell["symbol_canonical"],
                bars[idx - PRODUCTION_CLOSED_BARS + 1:idx + 1],
                times[idx].date().isoformat(),
                bar_time=times[idx],
            )
            if intent is None:
                continue
            local_id = (cell["symbol_canonical"], times[idx].isoformat(), int(intent.direction))
            if local_id in seen:
                continue
            seen.add(local_id)
            candidate_id = (
                cell["namespace"], sleeve, cell["symbol_canonical"],
                times[idx].isoformat(), int(intent.direction),
            )
            generated[candidate_id] = {
                "source_index": idx,
                "entry_utc": entry_utc.isoformat(),
                "sl_distance_price": float(intent.stop_dist),
                "intent_target_dist": (
                    float(intent.target_dist) if intent.target_dist is not None else None
                ),
            }
            candidates += 1
        generator_bar_evaluations += evaluations
        check(evaluations == int(cell["observed_bar_evaluations"]),
              f"generator_bar_evaluations:{cell['source_cell_id']}", failures)
        check(candidates == int(cell["observed_candidate_emissions"]),
              f"generator_candidate_count:{cell['source_cell_id']}", failures)
        expected_status = (
            "LOADED_OBSERVED_ROWS_WITH_EMISSIONS"
            if candidates else "LOADED_OBSERVED_ROWS_NO_EMISSION"
        )
        check(cell["source_status"] == expected_status,
              f"generator_noop_status:{cell['source_cell_id']}", failures)

    triplets: dict[tuple, set[str]] = collections.defaultdict(set)
    rows_by_identity: dict[tuple, list[dict]] = collections.defaultdict(list)
    for row in rows:
        identity = (
            row["namespace"], row["sleeve"], row["symbol_canonical"],
            row["decision_bar_iso"], int(row["direction"]),
        )
        triplets[identity].add(row["band"])
        rows_by_identity[identity].append(row)
    check(set(triplets) == set(generated), "production_generator_identity_set", failures)
    check(all(bands == set(BANDS) for bands in triplets.values()),
          "three_band_triplets", failures)
    for identity, seed in generated.items():
        for row in rows_by_identity.get(identity, []):
            check(int(row["source_index"]) == seed["source_index"],
                  f"source_index:{identity}", failures)
            check(row["entry_utc"] == seed["entry_utc"], f"entry_utc:{identity}", failures)
            check(close(row["sl_distance_price"], seed["sl_distance_price"]),
                  f"stop_distance:{identity}", failures)
            check(close(row.get("intent_target_dist"), seed["intent_target_dist"]),
                  f"target_distance:{identity}", failures)

    # Independent production walker, floor, spread, and cost recomputation for every
    # published band row.
    costs = load_broker_true_costs(COSTS_PATH)
    spread_model = load_spread_model(SPREAD_PATH)
    base_cfg = yaml.safe_load((REPO / "config/agent_config.yaml").read_text()) or {}
    configs: dict[str, dict[str, Any]] = {}
    for namespace, arming in declaration.items():
        merged = apply_profile_overrides(copy.deepcopy(base_cfg), arming.profile)
        configs[namespace] = {
            "runtime": dict(merged.get("gtos_vnext_runtime") or {}),
            "resolver": build_broker_symbol_resolver(merged),
            "floor": {sleeve: None for sleeve in arming.spread_geometry_floor},
        }

    # Reopen the committed profile-merged config and declaration. The latest-host half
    # is deliberately only checked as a disclosed upstream observation: its durable
    # receipt is not present in this scoped lane, so it cannot create a live-parity claim.
    parity_by_namespace = result["native_flow_truth"]["runtime_parity"]
    check(set(parity_by_namespace) == set(declaration),
          "runtime_parity_namespace_roster", failures)
    host_frontiers = {
        "operator_profile": ["crypto"],
        "redacted_account_live_bee34003": [],
    }
    for namespace, arming in declaration.items():
        parity = parity_by_namespace[namespace]
        local = parity["local_committed_surface"]
        host = parity["latest_durable_host_observation"]
        runtime = configs[namespace]["runtime"]
        check(runtime.get("ultimate_book_include_clean3") is False,
              f"runtime_parity:{namespace}:merged_include_clean3_false", failures)
        check(local["include_clean3"] is False,
              f"runtime_parity:{namespace}:published_local_include_clean3", failures)
        check(local["effective_registry_intersection"] == ["crypto", "energy_agri"],
              f"runtime_parity:{namespace}:local_effective_registry", failures)
        check(local["frontier_exits"] == sorted(arming.frontier_exits),
              f"runtime_parity:{namespace}:local_frontier_declaration", failures)
        check(host["include_clean3"] is True,
              f"runtime_parity:{namespace}:host_include_clean3_observation", failures)
        check(host["effective_registry_intersection"] == [
            "crypto", "energy_agri", "sub_mid_dn_revert", "sub_xvol_pullback",
        ], f"runtime_parity:{namespace}:host_effective_registry_observation", failures)
        check(host["frontier_exits"] == host_frontiers[namespace],
              f"runtime_parity:{namespace}:host_frontier_observation", failures)
        check(host["artifact_binding_status"]
              == "UPSTREAM_INTEGRATION_RECEIPT_NOT_LOCAL_TO_THIS_SCOPED_LANE",
              f"runtime_parity:{namespace}:host_receipt_not_local", failures)
        check(parity["effective_registry_matches"] is False,
              f"runtime_parity:{namespace}:registry_mismatch", failures)
        check(parity["frontier_exit_selection_matches"]
              is (namespace == "redacted_account_live_bee34003"),
              f"runtime_parity:{namespace}:frontier_match", failures)
        check(parity["live_parity_claimed"] is False,
              f"runtime_parity:{namespace}:live_parity_false", failures)

    walker_rows = 0
    cost_rows = 0
    for row_no, row in enumerate(rows):
        prefix = f"behavior_row:{row_no}"
        namespace = row["namespace"]
        sleeve = row["sleeve"]
        bars, times = parsed[(namespace, row["symbol_canonical"])]
        idx = int(row["source_index"])
        direction = int(row["direction"])
        stop = float(row["sl_distance_price"])
        entry_utc = dt.datetime.fromisoformat(row["entry_utc"])
        symbol = configs[namespace]["resolver"](row["symbol_canonical"])
        check(symbol == row["symbol"], f"{prefix}:broker_symbol", failures)
        est = spread_price(
            symbol, ACCOUNT_META[namespace]["account"], entry_utc,
            band=row["band"], model=spread_model,
        )
        anchor = replay_anchor(float(bars[idx].c), direction, float(est.spread_price), BarQuote.BID)
        policy, contract = exit_policy(
            sleeve, declaration[namespace].frontier_exits, stop,
            row.get("intent_target_dist"),
        )
        level = replay(
            bars, idx, direction, stop_dist=stop, policy=policy, times=times,
            server=ACCOUNT_META[namespace]["server"], bar_minutes=H4_MINUTES,
        )
        quote = replay(
            bars, idx, direction, stop_dist=stop, policy=policy, times=times,
            server=ACCOUNT_META[namespace]["server"], bar_minutes=H4_MINUTES,
            entry_price=anchor,
        )
        gap_raw, gap = gap_conservative(bars, anchor, direction, stop, quote)
        walker_rows += 1
        check(row["quote_authority_status"] == "MODELLED",
              f"{prefix}:quote_status_modelled", failures)
        check(row["quote_lifecycle_coverage"] == "MODELLED",
              f"{prefix}:quote_coverage_modelled", failures)
        check(row["quote_lifecycle_model"] == QUOTE_MODEL,
              f"{prefix}:quote_model", failures)
        check(row["coverage"] not in {"MEASURED", "TRANSFERRED"},
              f"{prefix}:row_coverage_not_strengthened", failures)
        check(close(row["entry_bid_close"], bars[idx].c), f"{prefix}:bid_close", failures)
        check(close(row["entry_transacted"], anchor), f"{prefix}:entry_anchor", failures)
        check(close(row["spread_price"], est.spread_price), f"{prefix}:spread", failures)
        check(row["exit_contract"] == contract, f"{prefix}:exit_contract", failures)
        check(row["exit_reason_level"] == level.exit_reason,
              f"{prefix}:level_exit_reason", failures)
        check(row["exit_reason_quote"] == quote.exit_reason,
              f"{prefix}:quote_exit_reason", failures)
        check(int(row["exit_bar_offset_level"]) == int(level.exit_index) - idx,
              f"{prefix}:level_exit_index", failures)
        check(int(row["exit_bar_offset_quote"]) == int(quote.exit_index) - idx,
              f"{prefix}:quote_exit_index", failures)
        check(close(row["r_level_raw"], level.r_gross), f"{prefix}:level_r", failures)
        check(close(row["r_quote_raw"], quote.r_gross), f"{prefix}:quote_r", failures)
        check(close(row["r_quote_gap_raw"], gap_raw), f"{prefix}:gap_r", failures)
        check(row["gap"] == gap, f"{prefix}:gap_detail", failures)
        check(close(row["r_level_validation_clip"], winsorize_R(level.r_gross)),
              f"{prefix}:level_clip", failures)
        check(close(row["r_quote_gap_validation_clip"], winsorize_R(gap_raw)),
              f"{prefix}:gap_clip", failures)

        floor_limit = resolve_floor_limit(
            configs[namespace]["runtime"], sleeve, configs[namespace]["floor"]
        )
        spread_r = float(est.spread_price) / stop
        refused = floor_limit is not None and spread_r > float(floor_limit)
        check(close(row["floor_limit_r"], floor_limit), f"{prefix}:floor_limit", failures)
        check(row["floor_status"] == (
            "REFUSED" if refused else "SURVIVED" if floor_limit is not None else "NOT_APPLICABLE"
        ), f"{prefix}:floor_status", failures)

        level_exit = times[int(level.exit_index)] + H4_DELTA
        quote_exit = times[int(quote.exit_index)] + H4_DELTA
        level_hold = (level_exit - entry_utc).total_seconds() / 3600.0
        quote_hold = (quote_exit - entry_utc).total_seconds() / 3600.0
        side = "LONG" if direction > 0 else "SHORT"
        # Mirror the producer exactly (w7_current_recost.py:813-834): both cost_r
        # calls live under ONE refusal boundary.  Under the wave-21 fail-closed cost
        # authority a symbol/account without a reconciled slippage (or commission)
        # sample REFUSES rather than pricing; the producer emits a cost-NOT_EVALUABLE
        # row and this verifier must verify that refusal instead of crashing on it.
        try:
            c_level = cost_r(
                symbol, ACCOUNT_META[namespace]["account"], level_hold,
                sl_distance_price=stop, entry_price=float(bars[idx].c), side=side,
                entry_utc=entry_utc, spread_band=row["band"],
                spread_model=spread_model, costs=costs,
            )
            c = cost_r(
                symbol, ACCOUNT_META[namespace]["account"], quote_hold,
                sl_distance_price=stop, entry_price=anchor, side=side,
                entry_utc=entry_utc, spread_band=row["band"],
                spread_model=spread_model, costs=costs,
            )
        except (CostTruthError, SpreadModelError, KeyError, TypeError, ValueError) as exc:
            cost_rows += 1
            check(row["cost_authority_status"] == "NOT_EVALUABLE",
                  f"{prefix}:cost_refusal_status", failures)
            check(row["coverage"] == "NOT_EVALUABLE",
                  f"{prefix}:cost_refusal_coverage", failures)
            check(row["status"] == (
                "REFUSED_BY_CURRENT_FLOOR" if refused else "NOT_EVALUABLE"
            ), f"{prefix}:cost_refusal_row_status", failures)
            expected_suffix = (
                f"cost_unavailable:{type(exc).__name__}:{str(exc)[:180]}"
            )
            reason = str(row.get("reason") or "")
            check(reason.endswith(expected_suffix),
                  f"{prefix}:cost_refusal_reason", failures)
            check(reason.startswith("spread_geometry_floor:") == bool(refused),
                  f"{prefix}:cost_refusal_floor_prefix", failures)
            check("cost_components" not in row,
                  f"{prefix}:cost_refusal_no_components", failures)
            check("r_net_current_clip" not in row,
                  f"{prefix}:cost_refusal_no_net", failures)
            continue
        cost_rows += 1
        check(row["cost_authority_status"] == "COMPLETE",
              f"{prefix}:cost_complete_status", failures)
        expected_components = {
            "commission_r": c.commission_r,
            "swap_r": c.swap_r,
            "spread_r": c.spread_r,
            "slippage_r": c.slippage_r,
        }
        for name, measure in expected_components.items():
            actual = row["cost_components"][name]
            check(close(actual["value"], measure.value), f"{prefix}:{name}:value", failures)
            check(actual["coverage"] == measure.coverage.value,
                  f"{prefix}:{name}:coverage", failures)
        nonspread = math.fsum(float(expected_components[name].value) for name in (
            "commission_r", "swap_r", "slippage_r"
        ))
        current_net = float(winsorize_R(gap_raw)) - nonspread
        level_net = float(winsorize_R(level.r_gross)) - float(c_level.total_r.value)
        check(close(row["counterfactual_pre_floor_r_net_current_clip"], current_net),
              f"{prefix}:current_net", failures)
        check(close(row["counterfactual_pre_floor_r_net_level_all_cost_clip"], level_net),
              f"{prefix}:level_net", failures)
        expected_coverage = weakest(
            row["source_class"], "MODELLED", est.coverage.value,
            c.commission_r.coverage.value, c.swap_r.coverage.value,
            c.slippage_r.coverage.value,
        )
        check(row["coverage"] == expected_coverage, f"{prefix}:coverage", failures)
        if refused:
            check(row["status"] == "REFUSED_BY_CURRENT_FLOOR",
                  f"{prefix}:refused_status", failures)
            check("r_net_current_clip" not in row, f"{prefix}:refused_has_net", failures)
        else:
            check(row["status"] == "EVALUABLE", f"{prefix}:evaluable_status", failures)
            check(close(row["r_net_current_clip"], current_net),
                  f"{prefix}:survivor_net", failures)

    # Recompute result-bearing summary counts/means while enforcing that every level
    # above a blocked cell is NOT_EVALUABLE and every number is diagnostic-only.
    grouped: dict[tuple[str, str, str], list[dict]] = collections.defaultdict(list)
    cells_grouped: dict[tuple[str, str], list[dict]] = collections.defaultdict(list)
    for row in rows:
        grouped[(row["namespace"], row["band"], row["sleeve"])].append(row)
    for cell in source_cells:
        cells_grouped[(cell["namespace"], cell["sleeve"])].append(cell)
    for (namespace, band, sleeve), group in grouped.items():
        doc = result["accounts"][namespace]["bands"][band][sleeve]
        modelled = [row for row in group if row["quote_authority_status"] == "MODELLED"]
        costs_ok = [row for row in group if row["cost_authority_status"] == "COMPLETE"]
        survivors = [row for row in group if row["status"] == "EVALUABLE"]
        refused = [row for row in group if row["floor_status"] == "REFUSED"]
        missing = [
            cell for cell in cells_grouped[(namespace, sleeve)]
            if cell["source_status"] == "MISSING_SOURCE"
        ]
        expected_status = (
            "NOT_EVALUABLE_SUPPORTED_SOURCE_GAP"
            if missing else "NOT_EVALUABLE_STREAM_SCHEDULE_UNBOUND"
        )
        prefix = f"summary:{namespace}:{band}:{sleeve}"
        check(doc["evaluation_status"] == expected_status, f"{prefix}:status", failures)
        check(doc["headline_eligible"] is False, f"{prefix}:headline", failures)
        check(doc["n_emitted"] == len(group), f"{prefix}:emitted", failures)
        check(doc["quote_authority_complete"] == 0, f"{prefix}:quote_complete_zero", failures)
        check(doc["quote_authority_modelled"] == len(modelled),
              f"{prefix}:quote_modelled", failures)
        check(doc["cost_authority_complete"] == len(costs_ok),
              f"{prefix}:cost_complete", failures)
        check(doc["spread_floor_refused"] == len(refused), f"{prefix}:refused", failures)
        check(doc["conditional_survivor_evaluable"] == len(survivors),
              f"{prefix}:survivors", failures)
        expected_net_stats = value_stats(survivors, "r_net_current_clip")
        check(all(
            doc["metrics"]["r_net_current_clip"][key] == value
            for key, value in expected_net_stats.items()
        ), f"{prefix}:net_stats", failures)
        cell_doc = doc["source_cell_denominators"]
        check(cell_doc["missing_supported_cells"] == len(missing),
              f"{prefix}:missing_propagation", failures)
        check(cell_doc["full_window_candidate_emissions"] is None,
              f"{prefix}:full_window_count_unknown", failures)
        check(cell_doc["full_window_occurrence_status"]
              == "NOT_EVALUABLE_STREAM_SCHEDULE_UNBOUND",
              f"{prefix}:schedule_unbound", failures)
        if missing:
            check(result["accounts"][namespace]["band_status"][band]["evaluation_status"]
                  == "NOT_EVALUABLE_SUPPORTED_SOURCE_GAP",
                  f"{prefix}:band_propagation", failures)
            check(result["accounts"][namespace]["evaluation_status"]
                  == "NOT_EVALUABLE_SUPPORTED_SOURCE_GAP",
                  f"{prefix}:account_propagation", failures)
            historical = result["accounts"][namespace][
                "historical_published_separation_non_authoritative"
            ][sleeve]
            check(historical["current_sign"] == "NOT_EVALUABLE",
                  f"{prefix}:historical_sign_ne", failures)
            check(historical["current_exact_exit_cost_net_r"] is None,
                  f"{prefix}:historical_delta_ne", failures)

    # Independently project the owner-facing sleeve scorecard from the verified source
    # cells and row population. The scorecard may summarize these rows, but it may not
    # upgrade their source, schedule, quote/lifecycle, or native-graph authority.
    scorecard = result["sleeve_scorecard"]
    check(scorecard["allowed_recommendations"] == list(SCORECARD_RECOMMENDATIONS),
          "scorecard_recommendation_vocabulary", failures)
    check(scorecard["headline_eligible"] is False, "scorecard_headline_ineligible", failures)
    check(scorecard["arming_or_composition_change_authorized"] is False,
          "scorecard_no_arming", failures)
    cards = {
        (row["namespace"], row["sleeve"]): row
        for row in scorecard["rows"]
    }
    expected_cards = {
        (namespace, sleeve)
        for namespace in declaration
        for sleeve in armed_sleeves(namespace)
    }
    check(len(cards) == len(scorecard["rows"]), "scorecard_duplicate", failures)
    check(set(cards) == expected_cards, "scorecard_complete", failures)
    derived_recommendations: collections.Counter[str] = collections.Counter()
    for namespace, sleeve in sorted(expected_cards):
        card = cards[(namespace, sleeve)]
        card_prefix = f"scorecard:{namespace}:{sleeve}"
        cells = cells_grouped[(namespace, sleeve)]
        loaded = [
            row for row in cells
            if str(row["source_status"]).startswith("LOADED_OBSERVED_ROWS_")
        ]
        missing = [row for row in cells if row["source_status"] == "MISSING_SOURCE"]
        outside = [
            row for row in cells if row["source_status"] == "OUTSIDE_ACTIVE_PROFILE"
        ]
        expected_status = (
            "NOT_EVALUABLE_SUPPORTED_SOURCE_GAP"
            if missing else "NOT_EVALUABLE_STREAM_SCHEDULE_UNBOUND"
        )
        exit_mismatch = not card["runtime_parity"][
            "exit_contract_matches_latest_host_observation"
        ]
        expected_recommendation = (
            "NE" if (missing or exit_mismatch) else "RESEARCH_ONLY"
        )
        derived_recommendations[expected_recommendation] += 1
        check(card["evaluation_status"] == expected_status,
              f"{card_prefix}:evaluation", failures)
        check(card["recommendation"] == expected_recommendation,
              f"{card_prefix}:recommendation", failures)
        check(card["headline_eligible"] is False, f"{card_prefix}:headline", failures)
        check(card["native_graph_status"] == "NOT_EVALUABLE_NATIVE_GRAPH_INCOMPLETE",
              f"{card_prefix}:native_graph", failures)
        check(card["arming_or_composition_change_authorized"] is False,
              f"{card_prefix}:no_arming", failures)
        check(result["accounts"][namespace]["sleeve_scorecard"][sleeve] == card,
              f"{card_prefix}:account_projection", failures)

        coverage = card["coherent_source_coverage"]
        check(coverage["requested_cells"] == len(cells),
              f"{card_prefix}:requested_cells", failures)
        check(coverage["loaded_cells"] == len(loaded),
              f"{card_prefix}:loaded_cells", failures)
        check(coverage["missing_supported_cells"] == len(missing),
              f"{card_prefix}:missing_cells", failures)
        check(coverage["outside_active_profile_cells"] == len(outside),
              f"{card_prefix}:outside_cells", failures)
        check(coverage["calendar_denominator_claimed_unconditional"] is False,
              f"{card_prefix}:calendar_not_unconditional", failures)
        check(coverage["calendar_schedule_authority_status"]
              == "NOT_EVALUABLE_STREAM_SCHEDULE_UNBOUND",
              f"{card_prefix}:schedule_unbound", failures)

        activity = card["emissions_activity"]
        check(activity["observed_generator_bar_evaluations"] == sum(
            int(row["observed_bar_evaluations"]) for row in loaded
        ), f"{card_prefix}:observed_evaluations", failures)
        check(activity["observed_candidate_emissions"] == sum(
            int(row["observed_candidate_emissions"]) for row in loaded
        ), f"{card_prefix}:observed_emissions", failures)
        check(activity["full_window_candidate_emissions"] is None,
              f"{card_prefix}:full_window_unknown", failures)
        check(activity["full_window_candidate_count_unknown_not_zero"] is True,
              f"{card_prefix}:unknown_not_zero", failures)
        check({
            (row["source_cell_id"], row["symbol_canonical"])
            for row in card["missing_supported_source_cells"]
        } == {
            (row["source_cell_id"], row["symbol_canonical"])
            for row in missing
        }, f"{card_prefix}:missing_cell_identity", failures)

        for band in BANDS:
            group = grouped.get((namespace, band, sleeve), [])
            survivors = [row for row in group if row["status"] == "EVALUABLE"]
            diag = card["modelled_gross_net_diagnostics_by_band"][band]
            diag_prefix = f"{card_prefix}:{band}"
            check(diag["evaluation_status"] == expected_status,
                  f"{diag_prefix}:evaluation", failures)
            check(diag["quote_lifecycle_coverage"] == "MODELLED",
                  f"{diag_prefix}:quote_modelled", failures)
            check(diag["observed_emitted"] == len(group),
                  f"{diag_prefix}:emitted", failures)
            check(diag["current_floor_refusals"] == sum(
                row["floor_status"] == "REFUSED" for row in group
            ), f"{diag_prefix}:floor_refusals", failures)
            check(diag["cost_evaluable_survivors"] == len(survivors),
                  f"{diag_prefix}:survivors", failures)
            independent_stats = {
                "modelled_gross_all_observed_rows": value_stats(
                    group, "r_quote_gap_validation_clip"
                ),
                "modelled_counterfactual_net_all_observed_rows_pre_floor": value_stats(
                    group, "counterfactual_pre_floor_r_net_current_clip"
                ),
                "modelled_net_current_floor_survivors": value_stats(
                    survivors, "r_net_current_clip"
                ),
            }
            for field, expected in independent_stats.items():
                published = diag[field]
                check(all(published[key] == value for key, value in expected.items()),
                      f"{diag_prefix}:{field}:stats", failures)

            views = (
                (
                    "counterfactual_pre_floor", group,
                    "counterfactual_pre_floor_r_net_current_clip",
                ),
                ("current_floor_survivors", survivors, "r_net_current_clip"),
            )
            for view_name, view_rows, field in views:
                uncertainty = diag["uncertainty"][view_name]
                stats = value_stats(view_rows, field)
                valid_rows = [row for row in view_rows if row.get(field) is not None]
                check(uncertainty["n_trades"] == stats["n"],
                      f"{diag_prefix}:{view_name}:ci_n", failures)
                check(uncertainty["n_days"] == len({
                    dt.datetime.fromisoformat(row["entry_utc"]).date()
                    for row in valid_rows
                }), f"{diag_prefix}:{view_name}:ci_days", failures)
                check(close(uncertainty.get("point_mean"), stats["mean"], tol=1e-6),
                      f"{diag_prefix}:{view_name}:ci_point", failures)
                check(len(uncertainty["ci95"]) == 2,
                      f"{diag_prefix}:{view_name}:ci_shape", failures)
                for bucket, published_key in (
                    ("symbol", "by_symbol"), ("year", "by_entry_year")
                ):
                    derived = concentration_view(valid_rows, field, bucket)
                    published = diag["concentration"][view_name][published_key]
                    check(close(published["hhi_absolute"], derived["hhi_absolute"], tol=1e-6),
                          f"{diag_prefix}:{view_name}:{bucket}:hhi", failures)
                    top = published["top_absolute"]
                    if derived["top"] is None:
                        check(not top, f"{diag_prefix}:{view_name}:{bucket}:top_empty", failures)
                    else:
                        check(bool(top), f"{diag_prefix}:{view_name}:{bucket}:top_present", failures)
                        if top:
                            check(top[0]["name"] == derived["top"][0],
                                  f"{diag_prefix}:{view_name}:{bucket}:top_name", failures)
                            check(close(top[0]["sum_r"], derived["top"][1], tol=1e-6),
                                  f"{diag_prefix}:{view_name}:{bucket}:top_sum", failures)
                            check(close(
                                top[0]["share_abs_pct"],
                                derived["top_share_abs_pct"], tol=0.01,
                            ), f"{diag_prefix}:{view_name}:{bucket}:top_share", failures)

    expected_recommendation_counts = {
        recommendation: int(derived_recommendations.get(recommendation, 0))
        for recommendation in SCORECARD_RECOMMENDATIONS
    }
    check(scorecard["recommendation_counts"] == expected_recommendation_counts,
          "scorecard_recommendation_counts", failures)
    check(not derived_recommendations.get("KEEP") and not derived_recommendations.get("REPAIR"),
          "scorecard_no_partial_promotion", failures)

    check(result["aggregate_evaluation"]["evaluation_status"]
          == "NOT_EVALUABLE_SUPPORTED_SOURCE_GAP", "aggregate_propagation", failures)
    check(all(row["quote_authority_status"] not in {"COMPLETE", "MEASURED"} for row in rows),
          "no_complete_measured_quote_rows", failures)
    check(all(row["coverage"] in VALID_COVERAGE for row in rows),
          "valid_row_coverage", failures)
    check(prior["authoritative_current_comparator"] is False,
          "prior_not_authoritative", failures)

    receipt = {
        "schema": "gtos.wave21.w7_current_recost.verification.v2",
        "status": "PASS" if not failures else "FAIL",
        "failures": failures,
        "method": {
            "route_driver_imported": False,
            "source_parser": "independent_stdlib_csv_plus_broker_clock",
            "generator": "production_functions_reexecuted_for_every_loaded_source_cell",
            "walker": "production_replay_and_quote_anchor_reexecuted_for_every_row",
            "cost": "production_spread_floor_and_cost_r_reexecuted_for_every_row",
        },
        "inputs": {
            "verifier_sha256": sha(Path(__file__)),
            "driver_sha256": sha(HERE / "w7_current_recost.py"),
            "result_sha256": sha(RESULT),
            "rows_sha256": sha(ROWS),
            "source_cells_sha256": sha(SOURCE_CELLS),
            "prior_sha256": sha(PRIOR),
            "manifest_sha256": sha(MANIFEST),
            "report_sha256": sha(REPORT),
        },
        "checks": {
            "external_series_independently_parsed": len(parsed),
            "external_rows_independently_parsed": parsed_rows,
            "source_cells": len(source_cells),
            "loaded_observed_rows_no_emission_cells": sum(
                row["source_status"] == "LOADED_OBSERVED_ROWS_NO_EMISSION"
                for row in source_cells
            ),
            "supported_missing_cells": sum(
                row["source_status"] == "MISSING_SOURCE" for row in source_cells
            ),
            "generator_bar_evaluations": generator_bar_evaluations,
            "production_generator_candidate_identities": len(generated),
            "walker_rows_recomputed": walker_rows,
            "cost_rows_recomputed": cost_rows,
            "three_band_triplets": all(bands == set(BANDS) for bands in triplets.values()),
            "quote_lifecycle_never_complete_or_measured": all(
                row["quote_authority_status"] not in {"COMPLETE", "MEASURED"}
                for row in rows
            ),
            "supported_gap_propagation_fail_closed": not any(
                "propagation" in failure for failure in failures
            ),
        },
    }
    OUT.write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n")
    print(json.dumps(receipt, indent=2, sort_keys=True))
    return 0 if not failures else 1


if __name__ == "__main__":
    raise SystemExit(main())
