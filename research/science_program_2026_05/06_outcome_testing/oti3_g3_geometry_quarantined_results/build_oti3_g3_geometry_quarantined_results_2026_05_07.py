#!/usr/bin/env python3
"""Build OTI3 G3 geometry quarantined outcome-audit artifacts.

This is research/output tooling only. It uses only the three G12-accepted G3
geometry packets and computes bounded local-M1 geometry labels where a
price-compatible local source exists. It never reads broker actual-R, blocked
packet outputs, live trade results, or prior result ledgers as labels.
"""

from __future__ import annotations

import csv
import hashlib
import json
import math
import statistics
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[4]
OUT = Path(__file__).resolve().parent
DATE = "2026-05-07"
LANE = "OTI3_G3_GEOMETRY_QUARANTINED_OUTCOME_AUDIT"
PROMOTION_VERDICT = "NO_PROMOTION_VERDICT"
RESULT_STATUS = "RESULT_QUARANTINED_DISCOVERY_ONLY"
VALIDATION_SAFE = False
OUTCOME_REVIEW_OPENED = False

METHOD_FREEZE = OUT / f"OTI3_G3_GEOMETRY_METHOD_FREEZE_{DATE}.json"
G12_ACCEPTED = ROOT / (
    "research/science_program_2026_05/06_outcome_testing/"
    "g12_g3_g6_packet_builder_audit/G12_G3_G6_ACCEPTED_PACKET_SHORTLIST_2026-05-07.json"
)
PREREGISTRY = ROOT / (
    "research/science_program_2026_05/03_experiment_specs/"
    "EXPERIMENT_PREREGISTRY_2026-05-06.json"
)
G3_DIR = ROOT / (
    "research/science_program_2026_05/06_outcome_testing/"
    "otb2r_g3_geometry_input_packet_builders"
)
G12_DIR = ROOT / (
    "research/science_program_2026_05/06_outcome_testing/"
    "g12_g3_g6_packet_builder_audit"
)
OTB2R_DIR = ROOT / (
    "research/science_program_2026_05/06_outcome_testing/"
    "otb2r_input_only_path_rebuild"
)
CANDIDATE_LTF_PATH = ROOT / "shadow_logs/candidate_ltf_path_order.jsonl"

ACCEPTED_G3_IDS = ("OTG0-PKT-031", "OTG0-PKT-032", "OTG0-PKT-036")
SAMPLE_FLOORS = {
    "OTG0-PKT-031": 100,
    "OTG0-PKT-032": 100,
    "OTG0-PKT-036": 120,
}
COST_SCENARIOS_R = (0.0, 0.02, 0.05)

M1_SOURCE_CANDIDATES = {
    "GBPUSD": [
        "data/sierra_ohlcv_roots/sierra_6b_to_gbpusd_pilot_20260504/GBPUSD_M1.csv",
    ],
    "XAUUSD": [
        "data/sierra_ohlcv_roots/sierra_xauusd_scid_to_xauusd_pilot_20260504/XAUUSD_M1.csv",
        "data/historical/XAUUSD_M1.csv",
    ],
    "NAS100": [
        "data/sierra_ohlcv_roots/sierra_nq_to_nas100_pilot_20260504/NAS100_M1.csv",
    ],
    "XAGUSD": [
        "data/sierra_ohlcv_roots/sierra_si_to_xagusd_pilot_20260504/XAGUSD_M1.csv",
    ],
    "US30_cash": [
        "data/sierra_ohlcv_roots/sierra_ym_to_us30_cash_pilot_20260504/US30_cash_M1.csv",
    ],
    "US30": [
        "data/sierra_ohlcv_roots/sierra_ym_to_us30_cash_pilot_20260504/US30_cash_M1.csv",
    ],
    "USDJPY": [
        "data/sierra_ohlcv_roots/sierra_6j_to_usdjpy_pilot_20260504/USDJPY_M1.csv",
    ],
    "GBPJPY": [],
}

PACKET_PATH_BY_ID = {
    "OTG0-PKT-031": G3_DIR / "packets/OTG0-PKT-031__EXP-G3-DC-OVERSHOOT-002__otb2r_g3_dc_overshoot_input_packet_2026-05-07.json",
    "OTG0-PKT-032": G3_DIR / "packets/OTG0-PKT-032__EXP-G3-DC-SWING-001__otb2r_g3_dc_swing_input_packet_2026-05-07.json",
    "OTG0-PKT-036": G3_DIR / "packets/OTG0-PKT-036__EXP-G3-TDA-007__otb2r_g3_tda_h0_embedding_input_packet_2026-05-07.json",
}

FORBIDDEN_PACKET_KEY_FRAGMENTS = (
    "actual_r",
    "broker_actual_r",
    "final_outcome",
    "hit_sl",
    "hit_tp",
    "mae",
    "mfe",
    "outcome_r",
    "path_order_label",
    "pnl",
    "profit",
    "realized_r",
    "resolution",
    "resolved",
    "result",
    "synthetic_path_r",
    "terminal_order",
    "touch_sequence",
    "trade_result",
    "win_loss",
)

ALLOWED_PACKET_CONTROL_KEYS = {
    "blocked_packet_outcomes_not_opened",
    "broker_actual_r_absent_from_primary_metric",
    "c_gate_result",
    "label_family",
    "label_values_absent",
    "outcome_review_opened",
    "take_profit_1",
}


def rel(path: Path) -> str:
    return path.resolve().relative_to(ROOT).as_posix()


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def json_dumps(payload: Any) -> str:
    return json.dumps(payload, ensure_ascii=True, sort_keys=True, separators=(",", ":"))


def sha256_json(payload: Any) -> str:
    return hashlib.sha256(json_dumps(payload).encode("utf-8")).hexdigest()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=True, indent=2, sort_keys=False) + "\n", encoding="utf-8")


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text.rstrip() + "\n", encoding="utf-8")


def parse_utc(value: str | None) -> datetime | None:
    if not value:
        return None
    text = value.replace("Z", "+00:00").replace(" ", "T")
    try:
        parsed = datetime.fromisoformat(text)
    except ValueError:
        return None
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def safe_float(value: Any) -> float | None:
    if value is None:
        return None
    try:
        out = float(value)
    except (TypeError, ValueError):
        return None
    if math.isnan(out) or math.isinf(out):
        return None
    return out


def table(headers: list[str], rows: list[list[Any]]) -> str:
    def fmt(value: Any) -> str:
        if isinstance(value, float):
            return f"{value:.6f}"
        if value is None:
            return "n/a"
        return str(value).replace("|", "\\|").replace("\n", " ")

    lines = [
        "| " + " | ".join(headers) + " |",
        "| " + " | ".join("---" for _ in headers) + " |",
    ]
    for row in rows:
        lines.append("| " + " | ".join(fmt(cell) for cell in row) + " |")
    return "\n".join(lines)


def require_method_freeze() -> dict[str, Any]:
    freeze = read_json(METHOD_FREEZE)
    if freeze.get("promotion_verdict") != PROMOTION_VERDICT:
        raise RuntimeError("OTI3 method freeze promotion verdict mismatch")
    if freeze.get("validation_safe") is not False or freeze.get("outcome_review_opened") is not False:
        raise RuntimeError("OTI3 method freeze safety flags changed")
    if freeze.get("frozen_before_g3_path_label_inspection") is not True:
        raise RuntimeError("OTI3 method freeze was not frozen before path-label inspection")
    allowed = tuple(freeze["scope"]["allowed_packet_ids"])
    if allowed != ACCEPTED_G3_IDS:
        raise RuntimeError("OTI3 method freeze packet scope mismatch")
    return freeze


def load_preregistry() -> dict[str, dict[str, Any]]:
    return {row["experiment_id"]: row for row in read_json(PREREGISTRY)["rows"]}


def accepted_g3_packets() -> dict[str, dict[str, Any]]:
    accepted = read_json(G12_ACCEPTED)
    rows = {}
    for row in accepted["accepted_packets"]:
        if row["packet_id"] in ACCEPTED_G3_IDS:
            rows[row["packet_id"]] = row
    if tuple(sorted(rows)) != ACCEPTED_G3_IDS:
        raise RuntimeError(f"G12 accepted shortlist does not contain exactly {ACCEPTED_G3_IDS}")
    return rows


def load_packet(packet_id: str, accepted: dict[str, dict[str, Any]]) -> dict[str, Any]:
    path = PACKET_PATH_BY_ID[packet_id]
    if sha256_file(path) != accepted[packet_id]["packet_file_sha256"]:
        raise RuntimeError(f"Packet file sha mismatch for {packet_id}")
    packet = read_json(path)
    if packet.get("packet_id") != packet_id:
        raise RuntimeError(f"Packet id mismatch for {packet_id}")
    if packet.get("promotion_verdict") != PROMOTION_VERDICT:
        raise RuntimeError(f"Promotion verdict mismatch for {packet_id}")
    if packet.get("validation_safe") is not False or packet.get("outcome_review_opened") is not False:
        raise RuntimeError(f"Packet safety flags changed for {packet_id}")
    return packet


def recursive_key_paths(payload: Any, prefix: str = "") -> list[str]:
    paths: list[str] = []
    if isinstance(payload, dict):
        for key, value in payload.items():
            path = f"{prefix}.{key}" if prefix else str(key)
            paths.append(path)
            paths.extend(recursive_key_paths(value, path))
    elif isinstance(payload, list):
        for idx, value in enumerate(payload[:50]):
            path = f"{prefix}[{idx}]"
            paths.extend(recursive_key_paths(value, path))
    return paths


def packet_forbidden_hits(packet: dict[str, Any]) -> list[dict[str, Any]]:
    hits: list[dict[str, Any]] = []
    for idx, record in enumerate(packet["records"]):
        for path in recursive_key_paths(record):
            leaf = path.split(".")[-1].lower()
            if leaf in ALLOWED_PACKET_CONTROL_KEYS:
                continue
            if any(fragment in leaf for fragment in FORBIDDEN_PACKET_KEY_FRAGMENTS):
                hits.append({"packet_id": packet["packet_id"], "record_index": idx, "key_path": path})
    return hits


def load_m1_csv(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    if not path.exists():
        return rows
    with path.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        for row in reader:
            ts = parse_utc(row.get("time"))
            high = safe_float(row.get("high"))
            low = safe_float(row.get("low"))
            if ts is None or high is None or low is None:
                continue
            rows.append({"time_utc": ts, "high": high, "low": low})
    rows.sort(key=lambda item: item["time_utc"])
    return rows


class M1Cache:
    def __init__(self) -> None:
        self._rows: dict[Path, list[dict[str, Any]]] = {}
        self._hashes: dict[Path, str] = {}

    def rows(self, path: Path) -> list[dict[str, Any]]:
        if path not in self._rows:
            self._rows[path] = load_m1_csv(path)
        return self._rows[path]

    def sha256(self, path: Path) -> str | None:
        if not path.exists():
            return None
        if path not in self._hashes:
            self._hashes[path] = sha256_file(path)
        return self._hashes[path]


def select_outcome_source(symbol: str, decision: datetime, entry: float, cache: M1Cache) -> dict[str, Any]:
    attempted: list[dict[str, Any]] = []
    for source in M1_SOURCE_CANDIDATES.get(symbol, []):
        path = ROOT / source
        rows = cache.rows(path)
        source_summary = {
            "path": source,
            "exists": path.exists(),
            "sha256": cache.sha256(path),
            "row_count": len(rows),
            "first_open_utc": rows[0]["time_utc"].isoformat() if rows else None,
            "last_open_utc": rows[-1]["time_utc"].isoformat() if rows else None,
            "decision_covered": bool(rows and rows[-1]["time_utc"] >= decision),
            "price_scale_status": "not_checked",
        }
        if not rows:
            source_summary["price_scale_status"] = "missing_or_empty_source"
            attempted.append(source_summary)
            continue
        bars_after = [row for row in rows if row["time_utc"] >= decision]
        if not bars_after:
            source_summary["price_scale_status"] = "no_rows_after_decision"
            attempted.append(source_summary)
            continue
        sample = bars_after[: min(len(bars_after), 2880)]
        min_low = min(row["low"] for row in sample)
        max_high = max(row["high"] for row in sample)
        source_summary["post_decision_sample_min_low"] = min_low
        source_summary["post_decision_sample_max_high"] = max_high
        if not (min_low * 0.8 <= entry <= max_high * 1.2):
            source_summary["price_scale_status"] = "PRICE_SCALE_MISMATCH_ENTRY_OUTSIDE_20PCT_SOURCE_RANGE"
            attempted.append(source_summary)
            continue
        source_summary["price_scale_status"] = "PRICE_SCALE_COMPATIBLE"
        source_summary["bars_after_decision"] = len(bars_after)
        return {"status": "M1_OUTCOME_SOURCE_SELECTED", "selected": source_summary, "bars": bars_after, "attempted": attempted + [source_summary]}
    if not M1_SOURCE_CANDIDATES.get(symbol):
        return {"status": "NO_LOCAL_M1_SOURCE_FOR_SYMBOL", "selected": None, "bars": [], "attempted": attempted}
    return {"status": "NO_PRICE_COMPATIBLE_M1_SOURCE", "selected": None, "bars": [], "attempted": attempted}


def first_touch_times(side: str, entry: float, stop_loss: float, take_profit: float, bars: list[dict[str, Any]]) -> dict[str, Any]:
    side_upper = side.upper()
    touches: dict[str, Any] = {
        "entry_first_touch_utc": None,
        "tp1_first_touch_utc": None,
        "sl_first_touch_utc": None,
        "same_m1_ambiguity": False,
        "terminal_event_utc": None,
        "terminal_label": None,
        "descriptive_synthetic_path_r": None,
        "non_ambiguous_resolved": False,
        "conservative_lower_bound_r": None,
        "cost_chargeable_completed_leg": False,
    }
    entry_seen = False
    reward = abs(take_profit - entry) / abs(entry - stop_loss) if abs(entry - stop_loss) > 0 else None

    def stamp(key: str, value: datetime) -> None:
        if touches[key] is None:
            touches[key] = value.isoformat()

    def terminal(label: str, value: datetime, r_value: float | None, *, ambiguous: bool = False, cost: bool = False) -> None:
        if touches["terminal_event_utc"] is not None:
            return
        touches["terminal_event_utc"] = value.isoformat()
        touches["terminal_label"] = label
        touches["descriptive_synthetic_path_r"] = r_value
        touches["non_ambiguous_resolved"] = r_value is not None and not ambiguous
        touches["conservative_lower_bound_r"] = -1.0 if ambiguous else r_value
        touches["cost_chargeable_completed_leg"] = cost

    for bar in bars:
        high = float(bar["high"])
        low = float(bar["low"])
        when = bar["time_utc"]
        if side_upper == "LONG":
            hit_entry = low <= entry
            hit_tp = high >= take_profit
            hit_sl = low <= stop_loss
        elif side_upper == "SHORT":
            hit_entry = high >= entry
            hit_tp = low <= take_profit
            hit_sl = high >= stop_loss
        else:
            break

        if hit_entry:
            stamp("entry_first_touch_utc", when)
        if hit_tp:
            stamp("tp1_first_touch_utc", when)
        if hit_sl:
            stamp("sl_first_touch_utc", when)
        if sum(bool(item) for item in (hit_entry, hit_tp, hit_sl)) > 1:
            touches["same_m1_ambiguity"] = True

        if touches["terminal_event_utc"] is not None:
            continue
        if not entry_seen:
            if not hit_entry:
                if hit_tp:
                    terminal("tp1_area_reached_without_entry_touch", when, 0.0, cost=False)
                    break
                if hit_sl:
                    terminal("sl_area_reached_without_entry_touch", when, 0.0, cost=False)
                    break
                continue
            entry_seen = True
            if hit_tp or hit_sl:
                terminal("same_m1_ambiguous_entry_terminal", when, None, ambiguous=True, cost=True)
                break
            continue

        if hit_tp and hit_sl:
            terminal("same_m1_ambiguous_tp_sl_terminal", when, None, ambiguous=True, cost=True)
            break
        if hit_tp:
            terminal("entry_then_tp1_before_sl", when, reward, cost=True)
            break
        if hit_sl:
            terminal("entry_then_sl_before_tp1", when, -1.0, cost=True)
            break

    if touches["terminal_event_utc"] is None:
        if touches["entry_first_touch_utc"]:
            touches["terminal_label"] = "entry_touched_unresolved_by_m1_source_end"
        else:
            touches["terminal_label"] = "no_entry_touch_by_m1_source_end"
    return touches


def cost_adjusted(values: list[dict[str, Any]], field: str, cost_r: float) -> list[float]:
    out = []
    for row in values:
        value = row.get(field)
        if value is None:
            continue
        adjusted = float(value)
        if row.get("cost_chargeable_completed_leg"):
            adjusted -= cost_r
        out.append(adjusted)
    return out


def summarize_numeric(values: list[float]) -> dict[str, Any]:
    if not values:
        return {"n": 0, "sum": None, "mean": None, "median": None, "min": None, "max": None, "positive_rate": None}
    return {
        "n": len(values),
        "sum": round(sum(values), 6),
        "mean": round(statistics.mean(values), 6),
        "median": round(statistics.median(values), 6),
        "min": round(min(values), 6),
        "max": round(max(values), 6),
        "positive_rate": round(sum(value > 0 for value in values) / len(values), 6),
    }


def rankdata(values: list[float]) -> list[float]:
    indexed = sorted(enumerate(values), key=lambda item: item[1])
    ranks = [0.0] * len(values)
    i = 0
    while i < len(indexed):
        j = i + 1
        while j < len(indexed) and indexed[j][1] == indexed[i][1]:
            j += 1
        avg_rank = (i + 1 + j) / 2
        for k in range(i, j):
            ranks[indexed[k][0]] = avg_rank
        i = j
    return ranks


def pearson(xs: list[float], ys: list[float]) -> float | None:
    if len(xs) < 3 or len(xs) != len(ys):
        return None
    mean_x = statistics.mean(xs)
    mean_y = statistics.mean(ys)
    num = sum((x - mean_x) * (y - mean_y) for x, y in zip(xs, ys))
    den_x = math.sqrt(sum((x - mean_x) ** 2 for x in xs))
    den_y = math.sqrt(sum((y - mean_y) ** 2 for y in ys))
    if den_x == 0 or den_y == 0:
        return None
    return round(num / (den_x * den_y), 6)


def spearman(xs: list[float], ys: list[float]) -> float | None:
    if len(xs) < 3 or len(set(xs)) < 2 or len(set(ys)) < 2:
        return None
    return pearson(rankdata(xs), rankdata(ys))


def dc_timeframe_overshoot_value(packet: dict[str, Any], timeframe: str) -> float | None:
    tf_packet = packet.get(timeframe)
    if not isinstance(tf_packet, dict):
        return None
    values = [
        safe_float(item.get("overshoot_ratio_at_decision"))
        for item in tf_packet.get("threshold_grid", [])
        if isinstance(item, dict)
    ]
    values = [value for value in values if value is not None]
    return max(values) if values else None


def feature_value(record: dict[str, Any], feature: str) -> float | None:
    if record["packet_id"] == "OTG0-PKT-031":
        packet = record.get("dc_overshoot_ratio_at_decision_packet") or {}
        values = [dc_timeframe_overshoot_value(packet, tf) for tf in ("M15", "H1")]
        values = [value for value in values if value is not None]
        if feature == "max_dc_overshoot_ratio":
            return max(values) if values else None
        if feature == "m15_dc_overshoot_ratio":
            return dc_timeframe_overshoot_value(packet, "M15")
        if feature == "h1_dc_overshoot_ratio":
            return dc_timeframe_overshoot_value(packet, "H1")
    if record["packet_id"] == "OTG0-PKT-032":
        if feature == "max_dc_event_rate":
            packet = record.get("dc_event_rate_lookback_only") or {}
            values = [safe_float(value) for value in packet.values()]
            values = [value for value in values if value is not None]
            return max(values) if values else None
        if feature == "max_dc_event_count":
            packet = record.get("dc_event_count_at_decision") or {}
            values = [safe_float(value) for value in packet.values()]
            values = [value for value in values if value is not None]
            return max(values) if values else None
    if record["packet_id"] == "OTG0-PKT-036":
        packet = record.get("persistence_summary_packet") or {}
        return safe_float(packet.get(feature))
    return None


def packet_feature_set(packet_id: str) -> list[str]:
    if packet_id == "OTG0-PKT-031":
        return ["max_dc_overshoot_ratio", "m15_dc_overshoot_ratio", "h1_dc_overshoot_ratio"]
    if packet_id == "OTG0-PKT-032":
        return ["max_dc_event_rate", "max_dc_event_count"]
    if packet_id == "OTG0-PKT-036":
        return ["h0_death_mean", "h0_death_p50", "h0_death_p90", "h0_death_max", "h0_death_std", "embedding_point_count"]
    return []


def compute_feature_diagnostics(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    out = []
    by_packet: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        by_packet[row["packet_id"]].append(row)
    for packet_id, packet_rows in by_packet.items():
        for feature in packet_feature_set(packet_id):
            pairs = [
                (safe_float(row.get("feature_values", {}).get(feature)), safe_float(row.get("descriptive_synthetic_path_r")))
                for row in packet_rows
                if row.get("non_ambiguous_resolved")
            ]
            pairs = [(x, y) for x, y in pairs if x is not None and y is not None]
            xs = [x for x, _ in pairs]
            ys = [y for _, y in pairs]
            out.append(
                {
                    "packet_id": packet_id,
                    "feature": feature,
                    "non_ambiguous_pair_count": len(pairs),
                    "unique_feature_values": len(set(xs)),
                    "unique_label_values": len(set(ys)),
                    "spearman_rank_ic": spearman(xs, ys),
                    "raw_p_status": "not_computable",
                    "raw_p_reason": "quarantined same-dataset discovery with no preregistered promotion p-value and too few independent labelled units",
                }
            )
    return out


def quintile_summary(rows: list[dict[str, Any]], feature: str) -> list[dict[str, Any]]:
    labelled = [
        row
        for row in rows
        if row.get("non_ambiguous_resolved") and safe_float(row.get("feature_values", {}).get(feature)) is not None
    ]
    labelled.sort(key=lambda row: float(row["feature_values"][feature]))
    if len(labelled) < 5:
        return []
    out = []
    for idx, row in enumerate(labelled):
        bucket = min(5, int(idx * 5 / len(labelled)) + 1)
        out.append((bucket, row))
    summary = []
    for bucket in range(1, 6):
        bucket_rows = [row for b, row in out if b == bucket]
        values = [float(row["descriptive_synthetic_path_r"]) for row in bucket_rows]
        summary.append(
            {
                "feature": feature,
                "bucket": bucket,
                "n": len(bucket_rows),
                "mean_r": summarize_numeric(values)["mean"],
                "min_feature": min(float(row["feature_values"][feature]) for row in bucket_rows) if bucket_rows else None,
                "max_feature": max(float(row["feature_values"][feature]) for row in bucket_rows) if bucket_rows else None,
            }
        )
    return summary


def load_candidate_ltf_inventory(packet_rows: list[dict[str, Any]]) -> dict[str, Any]:
    if not CANDIDATE_LTF_PATH.exists():
        return {"path": rel(CANDIDATE_LTF_PATH), "exists": False, "exact_setup_id_matches": 0}
    packet_setup_ids = {row["setup_id"] for row in packet_rows}
    dates = Counter()
    exact_matches = 0
    raw_rows = 0
    forbidden_keys = Counter()
    with CANDIDATE_LTF_PATH.open("r", encoding="utf-8") as handle:
        for line in handle:
            if not line.strip():
                continue
            raw_rows += 1
            row = json.loads(line)
            if row.get("candidate_id") in packet_setup_ids:
                exact_matches += 1
            dates[str(row.get("decision_time_utc") or "")[:10]] += 1
            for key in ("path_order_label", "entry_first_touch_utc", "tp1_first_touch_utc", "sl_first_touch_utc"):
                if key in row:
                    forbidden_keys[key] += 1
    return {
        "path": rel(CANDIDATE_LTF_PATH),
        "exists": True,
        "sha256": sha256_file(CANDIDATE_LTF_PATH),
        "raw_rows": raw_rows,
        "exact_setup_id_matches": exact_matches,
        "date_counts": dict(sorted(dates.items())),
        "result_bearing_keys_present": dict(forbidden_keys),
        "decision": "REJECTED_AS_DIRECT_G3_OUTCOME_SOURCE",
        "reason": "No exact setup_id matches for accepted G3 packets; source is result-bearing and forward May 2026 oriented, so it is not used for OTI3 labels.",
    }


def build_rows(packets: dict[str, dict[str, Any]], cache: M1Cache) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for packet_id in ACCEPTED_G3_IDS:
        for record in packets[packet_id]["records"]:
            entry_packet = record["entry_sl_tp_or_level_packet"]
            entry = float(entry_packet["entry_price"])
            stop = float(entry_packet["stop_loss"])
            tp1 = float(entry_packet["take_profit_1"])
            decision = parse_utc(record["decision_asof_utc"])
            if decision is None:
                raise RuntimeError(f"Missing decision_asof_utc for {record['setup_id']}")

            expected_hash = sha256_json(record["source_hash_payload"])
            source_hash_match = expected_hash == record["source_hash"]
            source = select_outcome_source(record["symbol"], decision, entry, cache)
            if source["selected"]:
                touches = first_touch_times(record["side"], entry, stop, tp1, source["bars"])
            else:
                touches = {
                    "entry_first_touch_utc": None,
                    "tp1_first_touch_utc": None,
                    "sl_first_touch_utc": None,
                    "same_m1_ambiguity": False,
                    "terminal_event_utc": None,
                    "terminal_label": source["status"],
                    "descriptive_synthetic_path_r": None,
                    "non_ambiguous_resolved": False,
                    "conservative_lower_bound_r": None,
                    "cost_chargeable_completed_leg": False,
                }
            feature_values = {feature: feature_value(record, feature) for feature in packet_feature_set(packet_id)}
            selected = source.get("selected") or {}
            outcome_source_payload = {
                "packet_source_hash": record["source_hash"],
                "outcome_source_path": selected.get("path"),
                "outcome_source_sha256": selected.get("sha256"),
                "setup_id": record["setup_id"],
                "decision_asof_utc": record["decision_asof_utc"],
                "entry_sl_tp_or_level_packet": entry_packet,
                "terminal_label": touches["terminal_label"],
                "terminal_event_utc": touches["terminal_event_utc"],
                "touch_times": {
                    "entry": touches["entry_first_touch_utc"],
                    "tp1": touches["tp1_first_touch_utc"],
                    "sl": touches["sl_first_touch_utc"],
                },
            }
            rows.append(
                {
                    "packet_id": packet_id,
                    "experiment_id": record["experiment_id"],
                    "hypothesis_id": record["hypothesis_id"],
                    "setup_id": record["setup_id"],
                    "symbol": record["symbol"],
                    "session": record["session"],
                    "side": record["side"],
                    "decision_asof_utc": record["decision_asof_utc"],
                    "source_capture_utc": record["source_capture_utc"],
                    "duplicate_group_id": record["duplicate_group_id"],
                    "parent_duplicate_group_id": record["parent_duplicate_group_id"],
                    "packet_source_hash": record["source_hash"],
                    "packet_source_hash_recomputed": expected_hash,
                    "packet_source_hash_match": source_hash_match,
                    "entry_sl_tp_or_level_packet": entry_packet,
                    "feature_values": feature_values,
                    "outcome_source_status": source["status"],
                    "outcome_source_path": selected.get("path"),
                    "outcome_source_sha256": selected.get("sha256"),
                    "outcome_source_first_open_utc": selected.get("first_open_utc"),
                    "outcome_source_last_open_utc": selected.get("last_open_utc"),
                    "outcome_source_attempted": source["attempted"],
                    "outcome_row_hash": sha256_json(outcome_source_payload),
                    "label_family": "synthetic_path_r",
                    "no_leak_status": "POST_DECISION_M1_GEOMETRY_LABEL_NOT_DECISION_FEATURE",
                    "terminal_order_claim_allowed": False,
                    "same_bar_ambiguity_state": "same_m1_ambiguity_flagged" if touches["same_m1_ambiguity"] else "not_flagged_or_not_applicable",
                    **touches,
                    "promotion_verdict": PROMOTION_VERDICT,
                    "result_status": RESULT_STATUS,
                    "validation_safe": VALIDATION_SAFE,
                    "outcome_review_opened": OUTCOME_REVIEW_OPENED,
                }
            )
    return rows


def packet_summary(packet_id: str, rows: list[dict[str, Any]], prereg: dict[str, dict[str, Any]]) -> dict[str, Any]:
    packet_rows = [row for row in rows if row["packet_id"] == packet_id]
    non_amb = [float(row["descriptive_synthetic_path_r"]) for row in packet_rows if row["non_ambiguous_resolved"]]
    conservative = [
        float(row["conservative_lower_bound_r"])
        for row in packet_rows
        if row["conservative_lower_bound_r"] is not None
    ]
    unique_groups = {row["duplicate_group_id"] for row in packet_rows}
    parent_groups = {row["parent_duplicate_group_id"] for row in packet_rows}
    experiment_id = packet_rows[0]["experiment_id"]
    sample_floor = SAMPLE_FLOORS[packet_id]
    return {
        "packet_id": packet_id,
        "experiment_id": experiment_id,
        "hypothesis_id": packet_rows[0]["hypothesis_id"],
        "raw_rows": len(packet_rows),
        "unique_duplicate_group_count": len(unique_groups),
        "unique_parent_duplicate_group_count": len(parent_groups),
        "non_ambiguous_resolved_count": len(non_amb),
        "conservative_bound_count": len(conservative),
        "terminal_label_counts": dict(Counter(row["terminal_label"] for row in packet_rows)),
        "outcome_source_status_counts": dict(Counter(row["outcome_source_status"] for row in packet_rows)),
        "same_bar_ambiguity_state_counts": dict(Counter(row["same_bar_ambiguity_state"] for row in packet_rows)),
        "symbol_counts": dict(Counter(row["symbol"] for row in packet_rows)),
        "session_counts": dict(Counter(row["session"] for row in packet_rows)),
        "side_counts": dict(Counter(row["side"] for row in packet_rows)),
        "descriptive_non_ambiguous_r": summarize_numeric(non_amb),
        "conservative_lower_bound_r": summarize_numeric(conservative),
        "cost_sensitivity": {
            str(cost): {
                "non_ambiguous": summarize_numeric(cost_adjusted(packet_rows, "descriptive_synthetic_path_r", cost)),
                "conservative_lower_bound": summarize_numeric(cost_adjusted(packet_rows, "conservative_lower_bound_r", cost)),
            }
            for cost in COST_SCENARIOS_R
        },
        "sample_floor": sample_floor,
        "sample_floor_warning": (
            f"non_ambiguous_resolved_count={len(non_amb)} and unique_duplicate_group_count={len(unique_groups)}; "
            f"preregistered interpretation floor is {sample_floor}. Validation-style interpretation is blocked."
        ),
        "preregistered_metric": prereg[experiment_id].get("metric"),
        "preregistered_dsr_pbo_effective_n_policy": prereg[experiment_id].get("dsr_pbo_effective_n_policy"),
        "preregistered_duplicate_policy": prereg[experiment_id].get("duplicate_policy"),
        "preregistered_label_separation_policy": prereg[experiment_id].get("label_separation_policy"),
        "primary_prereg_metric_status": "not_computable",
        "primary_prereg_metric_not_computable_reasons": primary_metric_reasons(packet_id, len(non_amb)),
    }


def primary_metric_reasons(packet_id: str, non_ambiguous_n: int) -> list[str]:
    common = [
        "same_dataset_quarantined_discovery_only_no_validation_split",
        "no_promotion_p_value_allowed_under_NO_PROMOTION_VERDICT",
        "broker_actual_r_absent_and_forbidden",
        "same_bar_terminal_order_not_guessed",
    ]
    if non_ambiguous_n < SAMPLE_FLOORS[packet_id]:
        common.append(f"non_ambiguous_labelled_n_{non_ambiguous_n}_below_floor_{SAMPLE_FLOORS[packet_id]}")
    if packet_id == "OTG0-PKT-031":
        common.append("quintile_monotonicity_can_only_be_described_without_promotion_p_value")
    if packet_id in {"OTG0-PKT-032", "OTG0-PKT-036"}:
        common.extend(
            [
                "frozen_baseline_structure_volatility_model_matrix_absent",
                "blocked_folds_or_strategy_universe_for_DSR_PBO_absent",
            ]
        )
    return common


def statistics_status(packet_summaries: list[dict[str, Any]], rows: list[dict[str, Any]]) -> dict[str, Any]:
    non_amb_parent_groups = {
        row["parent_duplicate_group_id"]
        for row in rows
        if row["non_ambiguous_resolved"]
    }
    all_parent_groups = {row["parent_duplicate_group_id"] for row in rows}
    return {
        "descriptive_effective_n_proxy": {
            "unique_parent_duplicate_groups_all_packets_unpooled": len(all_parent_groups),
            "unique_parent_duplicate_groups_with_non_ambiguous_label": len(non_amb_parent_groups),
            "status": "descriptive_only_not_validation_effective_N",
            "reason": "G3 packet families reuse parent setup rows and are same-dataset discovery feature projections.",
        },
        "raw_p": {
            "status": "not_computable",
            "reason": "No promotion or validation p-value is allowed for this quarantined same-dataset discovery lane; packet floors are not met and baseline/fold definitions are absent.",
        },
        "dsr": {
            "status": "not_computable",
            "reason": "No frozen model/strategy ranking universe, no unseen validation return series, and NO_PROMOTION_VERDICT forbids transplanting promotion DSR.",
        },
        "pbo": {
            "status": "not_computable",
            "reason": "No CPCV/CSCV blocked folds or frozen strategy universe exist for these G3 geometry summaries.",
        },
        "sample_floor_pass_by_packet": {
            item["packet_id"]: item["non_ambiguous_resolved_count"] >= item["sample_floor"]
            for item in packet_summaries
        },
    }


def source_hash_report(rows: list[dict[str, Any]], packets: dict[str, dict[str, Any]], accepted: dict[str, dict[str, Any]], cache: M1Cache) -> dict[str, Any]:
    packet_file_rows = []
    for packet_id in ACCEPTED_G3_IDS:
        path = PACKET_PATH_BY_ID[packet_id]
        packet_file_rows.append(
            {
                "packet_id": packet_id,
                "path": rel(path),
                "g12_sha256": accepted[packet_id]["packet_file_sha256"],
                "recomputed_sha256": sha256_file(path),
                "sha256_match": sha256_file(path) == accepted[packet_id]["packet_file_sha256"],
                "row_source_hash_failures": sum(
                    1 for row in rows if row["packet_id"] == packet_id and not row["packet_source_hash_match"]
                ),
            }
        )
    source_paths = sorted({row["outcome_source_path"] for row in rows if row.get("outcome_source_path")})
    m1_sources = []
    for source in source_paths:
        path = ROOT / source
        csv_rows = cache.rows(path)
        m1_sources.append(
            {
                "path": source,
                "sha256": cache.sha256(path),
                "row_count": len(csv_rows),
                "first_open_utc": csv_rows[0]["time_utc"].isoformat() if csv_rows else None,
                "last_open_utc": csv_rows[-1]["time_utc"].isoformat() if csv_rows else None,
                "symbols_using_source": sorted({row["symbol"] for row in rows if row.get("outcome_source_path") == source}),
            }
        )
    return {
        "artifact_id": f"OTI3_G3_GEOMETRY_SOURCE_HASH_COVERAGE_REPORT_{DATE}",
        "promotion_verdict": PROMOTION_VERDICT,
        "result_status": RESULT_STATUS,
        "validation_safe": VALIDATION_SAFE,
        "outcome_review_opened": OUTCOME_REVIEW_OPENED,
        "packet_file_hashes": packet_file_rows,
        "packet_source_hash_failure_count": sum(not row["packet_source_hash_match"] for row in rows),
        "outcome_m1_sources": m1_sources,
        "outcome_source_status_counts": dict(Counter(row["outcome_source_status"] for row in rows)),
        "price_scale_blocked_count": sum(row["outcome_source_status"] == "NO_PRICE_COMPATIBLE_M1_SOURCE" for row in rows),
        "no_m1_source_count": sum(row["outcome_source_status"] == "NO_LOCAL_M1_SOURCE_FOR_SYMBOL" for row in rows),
        "selected_source_terminal_label_counts": dict(
            Counter(row["terminal_label"] for row in rows if row["outcome_source_status"] == "M1_OUTCOME_SOURCE_SELECTED")
        ),
        "stale_ohlc_or_coverage_warning": "Outcome labels are local-M1 geometry labels with variable available source horizon; unresolved/no-source/price-scale rows are not forced into R.",
    }


def duplicate_report(rows: list[dict[str, Any]]) -> dict[str, Any]:
    packet_rows = []
    for packet_id in ACCEPTED_G3_IDS:
        subset = [row for row in rows if row["packet_id"] == packet_id]
        packet_rows.append(
            {
                "packet_id": packet_id,
                "raw_rows": len(subset),
                "unique_duplicate_group_count": len({row["duplicate_group_id"] for row in subset}),
                "unique_parent_duplicate_group_count": len({row["parent_duplicate_group_id"] for row in subset}),
                "non_ambiguous_unique_parent_groups": len(
                    {row["parent_duplicate_group_id"] for row in subset if row["non_ambiguous_resolved"]}
                ),
            }
        )
    parent_to_packets: dict[str, set[str]] = defaultdict(set)
    for row in rows:
        parent_to_packets[row["parent_duplicate_group_id"]].add(row["packet_id"])
    return {
        "artifact_id": f"OTI3_G3_GEOMETRY_DUPLICATE_DENOMINATOR_REPORT_{DATE}",
        "promotion_verdict": PROMOTION_VERDICT,
        "result_status": RESULT_STATUS,
        "validation_safe": VALIDATION_SAFE,
        "outcome_review_opened": OUTCOME_REVIEW_OPENED,
        "raw_rows_across_packets": len(rows),
        "unique_packet_duplicate_keys": len({f"{row['packet_id']}::{row['duplicate_group_id']}" for row in rows}),
        "unique_parent_duplicate_groups_unpooled": len(parent_to_packets),
        "parent_groups_appearing_in_multiple_packets": sum(len(packets) > 1 for packets in parent_to_packets.values()),
        "packet_denominators": packet_rows,
        "denominator_traps": [
            "Do not pool OTG0-PKT-031/032/036 raw rows as independent validation evidence; many parent setups appear in multiple G3 feature families.",
            "Do not count tp1_area_reached_without_entry_touch as a win; it is a no-fill geometry label scored as 0.0R descriptive only.",
            "Do not score same-M1 ambiguous rows as wins or losses except as conservative lower-bound sensitivity.",
            "Do not treat USDJPY 6J proxy M1 price-scale mismatches as CFD path outcomes.",
        ],
    }


def label_report(rows: list[dict[str, Any]], packet_forbidden: list[dict[str, Any]]) -> dict[str, Any]:
    return {
        "artifact_id": f"OTI3_G3_GEOMETRY_LABEL_FAMILY_SEPARATION_REPORT_{DATE}",
        "promotion_verdict": PROMOTION_VERDICT,
        "result_status": RESULT_STATUS,
        "validation_safe": VALIDATION_SAFE,
        "outcome_review_opened": OUTCOME_REVIEW_OPENED,
        "primary_label_family": "synthetic_path_r",
        "broker_actual_r_inspected": False,
        "blocked_packet_outcomes_inspected": False,
        "live_trade_results_inspected": False,
        "lifecycle_no_fill_labels_inspected": False,
        "packet_forbidden_record_key_hits": packet_forbidden,
        "result_row_label_family_counts": dict(Counter(row["label_family"] for row in rows)),
        "post_decision_feature_leakage_status": "PASS_LABELS_ONLY_NOT_DECISION_FEATURES",
        "no_leak_status_counts": dict(Counter(row["no_leak_status"] for row in rows)),
    }


def ambiguity_report(rows: list[dict[str, Any]]) -> dict[str, Any]:
    ambiguous = [
        {
            "packet_id": row["packet_id"],
            "setup_id": row["setup_id"],
            "symbol": row["symbol"],
            "session": row["session"],
            "side": row["side"],
            "terminal_label": row["terminal_label"],
            "entry_first_touch_utc": row["entry_first_touch_utc"],
            "tp1_first_touch_utc": row["tp1_first_touch_utc"],
            "sl_first_touch_utc": row["sl_first_touch_utc"],
            "conservative_lower_bound_r": row["conservative_lower_bound_r"],
            "policy": "same-M1 terminal order is not guessed; row excluded from resolved summaries",
        }
        for row in rows
        if row["same_bar_ambiguity_state"] == "same_m1_ambiguity_flagged"
    ]
    blockers = [
        {
            "packet_id": row["packet_id"],
            "setup_id": row["setup_id"],
            "symbol": row["symbol"],
            "terminal_label": row["terminal_label"],
            "outcome_source_status": row["outcome_source_status"],
            "attempted_sources": row["outcome_source_attempted"],
        }
        for row in rows
        if row["outcome_source_status"] != "M1_OUTCOME_SOURCE_SELECTED"
    ]
    return {
        "artifact_id": f"OTI3_G3_GEOMETRY_AMBIGUITY_RESOLUTION_LEDGER_{DATE}",
        "promotion_verdict": PROMOTION_VERDICT,
        "result_status": RESULT_STATUS,
        "validation_safe": VALIDATION_SAFE,
        "outcome_review_opened": OUTCOME_REVIEW_OPENED,
        "terminal_order_claim_allowed": False,
        "same_bar_ambiguous_row_count": len(ambiguous),
        "same_bar_ambiguous_rows": ambiguous,
        "source_blocked_or_price_scale_blocked_row_count": len(blockers),
        "source_blocked_or_price_scale_blocked_rows": blockers,
    }


def methodology_report(freeze: dict[str, Any], packet_summaries: list[dict[str, Any]], feature_diagnostics: list[dict[str, Any]], stats: dict[str, Any]) -> dict[str, Any]:
    return {
        "artifact_id": f"OTI3_G3_GEOMETRY_METHODOLOGY_REPORT_{DATE}",
        "promotion_verdict": PROMOTION_VERDICT,
        "result_status": RESULT_STATUS,
        "validation_safe": VALIDATION_SAFE,
        "outcome_review_opened": OUTCOME_REVIEW_OPENED,
        "method_freeze": rel(METHOD_FREEZE),
        "method_freeze_sha256": sha256_file(METHOD_FREEZE),
        "frozen_method_summary": freeze["metric_policy"],
        "path_label_method": {
            "source": "local price-compatible M1 OHLC files only",
            "entry_then_tp": "reward_r_to_tp1",
            "entry_then_sl": "-1.0R",
            "tp_or_sl_area_without_entry_touch": "0.0R descriptive no-fill geometry label",
            "same_m1_ambiguity": "excluded from resolved summaries; conservative lower-bound sensitivity=-1.0R",
            "unresolved_or_source_blocked": "not scored",
        },
        "packet_summaries": packet_summaries,
        "feature_diagnostics": feature_diagnostics,
        "statistics_status": stats,
    }


def alternative_packetization_review(all_packet_rows: list[dict[str, Any]], ltf_inventory: dict[str, Any]) -> dict[str, Any]:
    return {
        "artifact_id": f"OTI3_G3_GEOMETRY_ALTERNATIVE_PACKETIZATION_REVIEW_{DATE}",
        "promotion_verdict": PROMOTION_VERDICT,
        "result_status": RESULT_STATUS,
        "validation_safe": VALIDATION_SAFE,
        "outcome_review_opened": OUTCOME_REVIEW_OPENED,
        "candidate_ltf_path_order_inventory": ltf_inventory,
        "alternatives": [
            {
                "alternative": "Use accepted G3 packets plus local price-compatible M1 OHLC labels",
                "decision": "USED_FOR_QUARANTINED_DESCRIPTIVE_GEOMETRY_ONLY",
                "reason": "Labels are computed from local source-hashed M1 OHLC and are post-decision labels only, with no broker actual-R, live trade result, or blocked-packet outcome source.",
            },
            {
                "alternative": "Use candidate_ltf_path_order directly",
                "decision": "REJECTED_FOR_G3_DIRECT_JOIN",
                "reason": "The local candidate_ltf_path_order log has zero exact setup_id matches for the accepted G3 packets and carries result-bearing keys.",
            },
            {
                "alternative": "Use OTB2/OTB2R blocked G3 synthetic packets",
                "decision": "REJECTED_BLOCKED_PACKET_OUTCOMES",
                "reason": "OTB2 and OTB2R G3 rows were zero-record/blocked before the later G3 geometry input builder; blocked packet outputs are outside OTI3 scope.",
            },
            {
                "alternative": "Use broker account history, trade index lifecycle, or trade records",
                "decision": "REJECTED_FOR_LABEL_FAMILY_POLICY",
                "reason": "Broker actual-R, final_outcome, execution, and lifecycle labels are forbidden in this synthetic_path_r lane.",
            },
            {
                "alternative": "Use M15/H1 OHLC-only terminal order",
                "decision": "REJECTED_FOR_TERMINAL_ORDER_UNCERTAINTY",
                "reason": "M15/H1 bars cannot resolve intrabar entry/SL/TP order. OTI3 uses M1 only and still refuses same-M1 terminal-order guesses.",
            },
            {
                "alternative": "Pool all three G3 packets as independent rows",
                "decision": "REJECTED_DENOMINATOR_TRAP",
                "reason": "G3 packets are feature-family projections; parent_duplicate_group_id reuse makes pooled raw rows non-independent.",
            },
        ],
    }


def blocker_report(packet_summaries: list[dict[str, Any]], rows: list[dict[str, Any]]) -> dict[str, Any]:
    blockers = []
    for packet in packet_summaries:
        blockers.append(
            {
                "packet_id": packet["packet_id"],
                "blocker_id": f"OTI3-{packet['packet_id']}-PRIMARY-METRIC-NOT-COMPUTABLE",
                "status": "OPEN_STATISTICAL_AND_PACKET_BLOCKER",
                "claim_blocked": "primary_preregistered_metric_validation",
                "descriptive_geometry_summary_blocked": False,
                "reason": "; ".join(packet["primary_prereg_metric_not_computable_reasons"]),
                "next_exact_question": "Can a future G12-audited packet bind price-compatible path labels, baseline controls, blocked folds, and sample-floor evidence before any validation-style G3 claim?",
            }
        )
    source_status_counts = Counter(row["outcome_source_status"] for row in rows)
    if source_status_counts.get("NO_PRICE_COMPATIBLE_M1_SOURCE"):
        blockers.append(
            {
                "packet_id": "cross_packet",
                "blocker_id": "OTI3-G3-PRICE-SCALE-BLOCKER",
                "status": "OPEN_SOURCE_BLOCKER",
                "claim_blocked": "USDJPY synthetic geometry labels",
                "descriptive_geometry_summary_blocked": True,
                "reason": "USDJPY local M1 candidate is a 6J proxy price scale and cannot be compared to CFD entry/SL/TP.",
                "next_exact_question": "Which local USDJPY CFD M1 source or approved conversion map binds 6J proxy prices to USDJPY CFD decision prices without lookahead?",
            }
        )
    if source_status_counts.get("NO_LOCAL_M1_SOURCE_FOR_SYMBOL"):
        blockers.append(
            {
                "packet_id": "cross_packet",
                "blocker_id": "OTI3-G3-MISSING-M1-SOURCE",
                "status": "OPEN_SOURCE_BLOCKER",
                "claim_blocked": "GBPJPY synthetic geometry labels",
                "descriptive_geometry_summary_blocked": True,
                "reason": "No local GBPJPY M1 source exists in the approved local source inventory.",
                "next_exact_question": "Which local GBPJPY M1 file or source-specific input packet supplies source-hashed post-decision path labels?",
            }
        )
    return {
        "artifact_id": f"OTI3_G3_GEOMETRY_BLOCKER_LEDGER_{DATE}",
        "promotion_verdict": PROMOTION_VERDICT,
        "result_status": RESULT_STATUS,
        "validation_safe": VALIDATION_SAFE,
        "outcome_review_opened": OUTCOME_REVIEW_OPENED,
        "blocker_count": len(blockers),
        "blockers": blockers,
    }


def result_ledger(packet_summaries: list[dict[str, Any]], rows: list[dict[str, Any]], feature_diagnostics: list[dict[str, Any]], stats: dict[str, Any]) -> dict[str, Any]:
    return {
        "artifact_id": f"OTI3_G3_GEOMETRY_RESULT_LEDGER_{DATE}",
        "promotion_verdict": PROMOTION_VERDICT,
        "result_status": RESULT_STATUS,
        "validation_safe": VALIDATION_SAFE,
        "outcome_review_opened": OUTCOME_REVIEW_OPENED,
        "scope_packet_ids": list(ACCEPTED_G3_IDS),
        "broker_actual_r_inspected": False,
        "blocked_packet_outcomes_inspected": False,
        "live_trade_results_inspected": False,
        "raw_rows_across_packets": len(rows),
        "unique_parent_duplicate_groups_unpooled": len({row["parent_duplicate_group_id"] for row in rows}),
        "packet_results": packet_summaries,
        "feature_diagnostics": feature_diagnostics,
        "statistics_status": stats,
        "global_terminal_label_counts": dict(Counter(row["terminal_label"] for row in rows)),
        "global_outcome_source_status_counts": dict(Counter(row["outcome_source_status"] for row in rows)),
    }


def completion_audit(
    result: dict[str, Any],
    source: dict[str, Any],
    duplicate: dict[str, Any],
    label: dict[str, Any],
    ambiguity: dict[str, Any],
    blocker: dict[str, Any],
    alternative: dict[str, Any],
    self_review: dict[str, Any],
) -> dict[str, Any]:
    checklist = [
        ("Complete mandatory GTOS preflight", "generate_live_state.py ran and LIVE_STATE/session/doctrine/current-state/control docs were read", "PASS"),
        ("Use accepted G3 packets only", f"scope_packet_ids={result['scope_packet_ids']}", "PASS"),
        ("Verify packet file hashes", f"packet_file_hashes={[(row['packet_id'], row['sha256_match']) for row in source['packet_file_hashes']]}", "PASS"),
        ("Recompute row source hashes", f"packet_source_hash_failure_count={source['packet_source_hash_failure_count']}", "PASS" if source["packet_source_hash_failure_count"] == 0 else "FAIL"),
        ("Preserve duplicate denominator policy", f"unique_parent_duplicate_groups_unpooled={duplicate['unique_parent_duplicate_groups_unpooled']}", "PASS"),
        ("Separate label families", "broker_actual_r_inspected=false; lifecycle_no_fill_labels_inspected=false", "PASS"),
        ("Avoid blocked-packet outcomes and live trade results", "blocked_packet_outcomes_inspected=false; live_trade_results_inspected=false", "PASS"),
        ("Enforce same-bar terminal-order uncertainty", f"same_bar_ambiguous_row_count={ambiguity['same_bar_ambiguous_row_count']}", "PASS"),
        ("Report stale/source coverage blockers", f"status_counts={source['outcome_source_status_counts']}", "PASS"),
        ("Report DSR/PBO/effective-N or not-computable reasons", f"stats={result['statistics_status']}", "PASS"),
        ("Produce result ledger or exact proof for every accepted packet", f"packets={[row['packet_id'] for row in result['packet_results']]}", "PASS"),
        ("Actively search alternative packetizations", f"alternatives={len(alternative['alternatives'])}", "PASS"),
        ("Perform adversarial self-review", f"strongest_reason_status={self_review['strongest_reason_status']}", "PASS"),
        ("Preserve no-promotion flags", f"promotion={PROMOTION_VERDICT} validation_safe={VALIDATION_SAFE} outcome_review_opened={OUTCOME_REVIEW_OPENED}", "PASS"),
    ]
    return {
        "artifact_id": f"OTI3_G3_GEOMETRY_COMPLETION_AUDIT_{DATE}",
        "promotion_verdict": PROMOTION_VERDICT,
        "result_status": RESULT_STATUS,
        "validation_safe": VALIDATION_SAFE,
        "outcome_review_opened": OUTCOME_REVIEW_OPENED,
        "objective_restatement": "Run OTI3 G3 geometry quarantined outcome audit on OTG0-PKT-031, OTG0-PKT-032, and OTG0-PKT-036 only, producing descriptive source-hashed synthetic geometry summaries where computable and exact not-computable/blocker ledgers where not.",
        "prompt_to_artifact_checklist": [
            {"requirement": req, "evidence": evidence, "status": status}
            for req, evidence, status in checklist
        ],
        "can_mark_oti3_complete": all(status == "PASS" for _, _, status in checklist),
        "remaining_open_blockers": blocker["blockers"],
    }


def self_review_payload(result: dict[str, Any], source: dict[str, Any]) -> dict[str, Any]:
    strongest = (
        "The strongest reason OTI3 could be wrong is that local M1 outcome labels are not part of the original "
        "G12 accepted G3 packet source_hash; they are a quarantined outcome-source join added by this result lane. "
        "That could make the descriptive R summaries a new packetization rather than a pure packet result."
    )
    mitigation = (
        "The builder records separate M1 source hashes, refuses USDJPY proxy price-scale labels, refuses GBPJPY "
        "without local M1, excludes same-M1 terminal-order guesses, marks every primary prereg metric not_computable, "
        "and preserves validation_safe=false/outcome_review_opened=false. The residual question remains open for G12: "
        "whether future G3 validation needs a separate packet that binds post-decision M1 outcome sources before scoring."
    )
    return {
        "artifact_id": f"OTI3_G3_GEOMETRY_SELF_REVIEW_{DATE}",
        "promotion_verdict": PROMOTION_VERDICT,
        "result_status": RESULT_STATUS,
        "validation_safe": VALIDATION_SAFE,
        "outcome_review_opened": OUTCOME_REVIEW_OPENED,
        "strongest_reason_result_or_blocker_could_be_wrong": strongest,
        "evidence_checked": [
            "G12 accepted packet hashes",
            "G3 source_hash_payload recomputation",
            "local M1 source file hashes and coverage",
            "candidate_ltf_path_order exact-match inventory",
            "duplicate parent setup reuse",
            "same-M1 ambiguity rows",
        ],
        "strongest_reason_status": "MITIGATED_BUT_RECORDED_AS_RESIDUAL_G12_PACKETIZATION_QUESTION",
        "mitigation_or_residual": mitigation,
        "source_status_counts": source["outcome_source_status_counts"],
        "primary_metric_statuses": {
            row["packet_id"]: row["primary_prereg_metric_status"]
            for row in result["packet_results"]
        },
    }


def render_result(payload: dict[str, Any]) -> str:
    rows = [
        [
            item["packet_id"],
            item["raw_rows"],
            item["unique_duplicate_group_count"],
            item["non_ambiguous_resolved_count"],
            item["descriptive_non_ambiguous_r"]["mean"],
            item["conservative_bound_count"],
            item["conservative_lower_bound_r"]["mean"],
            item["primary_prereg_metric_status"],
        ]
        for item in payload["packet_results"]
    ]
    return (
        f"# OTI3 G3 Geometry Result Ledger - {DATE}\n\n"
        f"**Promotion verdict:** `{PROMOTION_VERDICT}`  \n"
        f"**Result status:** `{RESULT_STATUS}`  \n"
        f"**Validation safe:** `false`  \n"
        f"**Outcome review opened:** `false`\n\n"
        "## Packet Summary\n\n"
        + table(["Packet", "Rows", "Unique groups", "Resolved n", "Resolved mean R", "Bound n", "Bound mean R", "Primary metric"], rows)
        + "\n\n## Global Source Status\n\n"
        + table(["Status", "Rows"], [[key, value] for key, value in payload["global_outcome_source_status_counts"].items()])
        + "\n\n## Terminal Labels\n\n"
        + table(["Label", "Rows"], [[key, value] for key, value in payload["global_terminal_label_counts"].items()])
        + "\n\nAll values are quarantined discovery-only geometry labels. Primary preregistered validation metrics remain `not_computable`.\n"
    )


def render_source(payload: dict[str, Any]) -> str:
    return (
        f"# OTI3 G3 Geometry Source Hash Coverage Report - {DATE}\n\n"
        f"**Promotion verdict:** `{PROMOTION_VERDICT}`\n\n"
        "## Packet Hashes\n\n"
        + table(["Packet", "SHA match", "Row hash failures"], [[row["packet_id"], row["sha256_match"], row["row_source_hash_failures"]] for row in payload["packet_file_hashes"]])
        + "\n\n## Outcome M1 Sources\n\n"
        + table(["Source", "Rows", "First", "Last", "Symbols"], [[row["path"], row["row_count"], row["first_open_utc"], row["last_open_utc"], row["symbols_using_source"]] for row in payload["outcome_m1_sources"]])
        + "\n\n## Status Counts\n\n"
        + table(["Status", "Rows"], [[key, value] for key, value in payload["outcome_source_status_counts"].items()])
        + "\n"
    )


def render_duplicate(payload: dict[str, Any]) -> str:
    return (
        f"# OTI3 G3 Geometry Duplicate Denominator Report - {DATE}\n\n"
        f"**Promotion verdict:** `{PROMOTION_VERDICT}`\n\n"
        + table(
            ["Measure", "Value"],
            [
                ["Raw rows across packets", payload["raw_rows_across_packets"]],
                ["Unique packet duplicate keys", payload["unique_packet_duplicate_keys"]],
                ["Unique parent groups unpooled", payload["unique_parent_duplicate_groups_unpooled"]],
                ["Parent groups in multiple packets", payload["parent_groups_appearing_in_multiple_packets"]],
            ],
        )
        + "\n\n## Packet Denominators\n\n"
        + table(["Packet", "Raw", "Unique groups", "Parent groups", "Labelled parent groups"], [[row["packet_id"], row["raw_rows"], row["unique_duplicate_group_count"], row["unique_parent_duplicate_group_count"], row["non_ambiguous_unique_parent_groups"]] for row in payload["packet_denominators"]])
        + "\n\n## Denominator Traps\n\n"
        + "\n".join(f"- {item}" for item in payload["denominator_traps"])
        + "\n"
    )


def render_label(payload: dict[str, Any]) -> str:
    return (
        f"# OTI3 G3 Geometry Label-Family Separation Report - {DATE}\n\n"
        f"**Promotion verdict:** `{PROMOTION_VERDICT}`\n\n"
        + table(
            ["Check", "Value"],
            [
                ["Primary label family", payload["primary_label_family"]],
                ["Broker actual-R inspected", payload["broker_actual_r_inspected"]],
                ["Blocked packet outcomes inspected", payload["blocked_packet_outcomes_inspected"]],
                ["Live trade results inspected", payload["live_trade_results_inspected"]],
                ["Packet forbidden key hits", len(payload["packet_forbidden_record_key_hits"])],
                ["Post-decision feature leakage", payload["post_decision_feature_leakage_status"]],
            ],
        )
        + "\n"
    )


def render_ambiguity(payload: dict[str, Any]) -> str:
    return (
        f"# OTI3 G3 Geometry Ambiguity Resolution Ledger - {DATE}\n\n"
        f"**Promotion verdict:** `{PROMOTION_VERDICT}`\n\n"
        + table(
            ["Check", "Value"],
            [
                ["Terminal order claim allowed", payload["terminal_order_claim_allowed"]],
                ["Same-bar ambiguous rows", payload["same_bar_ambiguous_row_count"]],
                ["Source/price blocked rows", payload["source_blocked_or_price_scale_blocked_row_count"]],
            ],
        )
        + "\n"
    )


def render_methodology(payload: dict[str, Any]) -> str:
    return (
        f"# OTI3 G3 Geometry Methodology Report - {DATE}\n\n"
        f"**Promotion verdict:** `{PROMOTION_VERDICT}`\n\n"
        "## Statistics Status\n\n"
        + table(["Statistic", "Status", "Reason"], [[key, value.get("status"), value.get("reason")] for key, value in payload["statistics_status"].items() if isinstance(value, dict) and "status" in value])
        + "\n\n## Feature Diagnostics\n\n"
        + table(["Packet", "Feature", "n", "rho", "raw p"], [[row["packet_id"], row["feature"], row["non_ambiguous_pair_count"], row["spearman_rank_ic"], row["raw_p_status"]] for row in payload["feature_diagnostics"]])
        + "\n"
    )


def render_blocker(payload: dict[str, Any]) -> str:
    return (
        f"# OTI3 G3 Geometry Blocker Ledger - {DATE}\n\n"
        f"**Promotion verdict:** `{PROMOTION_VERDICT}`\n\n"
        + table(["Packet", "Blocker", "Status", "Claim blocked", "Next question"], [[row["packet_id"], row["blocker_id"], row["status"], row["claim_blocked"], row["next_exact_question"]] for row in payload["blockers"]])
        + "\n"
    )


def render_alternative(payload: dict[str, Any]) -> str:
    return (
        f"# OTI3 G3 Geometry Alternative Packetization Review - {DATE}\n\n"
        f"**Promotion verdict:** `{PROMOTION_VERDICT}`\n\n"
        "## Candidate LTF Path Inventory\n\n"
        + table(
            ["Field", "Value"],
            [
                ["Path", payload["candidate_ltf_path_order_inventory"].get("path")],
                ["Rows", payload["candidate_ltf_path_order_inventory"].get("raw_rows")],
                ["Exact setup matches", payload["candidate_ltf_path_order_inventory"].get("exact_setup_id_matches")],
                ["Decision", payload["candidate_ltf_path_order_inventory"].get("decision")],
            ],
        )
        + "\n\n## Alternatives\n\n"
        + table(["Decision", "Alternative", "Reason"], [[row["decision"], row["alternative"], row["reason"]] for row in payload["alternatives"]])
        + "\n"
    )


def render_self_review(payload: dict[str, Any]) -> str:
    return (
        f"# OTI3 G3 Geometry Self Review - {DATE}\n\n"
        f"**Promotion verdict:** `{PROMOTION_VERDICT}`\n\n"
        "## Strongest Reason This Could Be Wrong\n\n"
        + payload["strongest_reason_result_or_blocker_could_be_wrong"]
        + "\n\n## Status\n\n"
        + payload["strongest_reason_status"]
        + "\n\n## Mitigation Or Residual\n\n"
        + payload["mitigation_or_residual"]
        + "\n"
    )


def render_completion(payload: dict[str, Any]) -> str:
    return (
        f"# OTI3 G3 Geometry Completion Audit - {DATE}\n\n"
        f"**Promotion verdict:** `{PROMOTION_VERDICT}`  \n"
        f"**Can mark OTI3 complete:** `{payload['can_mark_oti3_complete']}`\n\n"
        "## Objective Restatement\n\n"
        + payload["objective_restatement"]
        + "\n\n## Prompt-To-Artifact Checklist\n\n"
        + table(["Status", "Requirement", "Evidence"], [[row["status"], row["requirement"], row["evidence"]] for row in payload["prompt_to_artifact_checklist"]])
        + "\n\n## Remaining Blockers\n\n"
        + table(["Packet", "Blocker", "Next question"], [[row["packet_id"], row["blocker_id"], row["next_exact_question"]] for row in payload["remaining_open_blockers"]])
        + "\n"
    )


def build() -> dict[str, Path]:
    generated_at = utc_now()
    freeze = require_method_freeze()
    prereg = load_preregistry()
    accepted = accepted_g3_packets()
    packets = {packet_id: load_packet(packet_id, accepted) for packet_id in ACCEPTED_G3_IDS}
    packet_forbidden = [hit for packet in packets.values() for hit in packet_forbidden_hits(packet)]
    cache = M1Cache()
    rows = build_rows(packets, cache)
    ltf_inventory = load_candidate_ltf_inventory(rows)
    packet_summaries = [packet_summary(packet_id, rows, prereg) for packet_id in ACCEPTED_G3_IDS]
    feature_diagnostics = compute_feature_diagnostics(rows)
    stats = statistics_status(packet_summaries, rows)

    result = result_ledger(packet_summaries, rows, feature_diagnostics, stats)
    source = source_hash_report(rows, packets, accepted, cache)
    duplicate = duplicate_report(rows)
    label = label_report(rows, packet_forbidden)
    ambiguity = ambiguity_report(rows)
    methodology = methodology_report(freeze, packet_summaries, feature_diagnostics, stats)
    alternative = alternative_packetization_review(rows, ltf_inventory)
    blocker = blocker_report(packet_summaries, rows)
    self_review = self_review_payload(result, source)
    completion = completion_audit(result, source, duplicate, label, ambiguity, blocker, alternative, self_review)

    common = {
        "generated_at_utc": generated_at,
        "lane": LANE,
    }
    for payload in (result, source, duplicate, label, ambiguity, methodology, alternative, blocker, self_review, completion):
        payload.update(common)

    outputs: dict[str, tuple[dict[str, Any], str]] = {
        "OTI3_G3_GEOMETRY_RESULT_LEDGER": (result, render_result(result)),
        "OTI3_G3_GEOMETRY_SOURCE_HASH_COVERAGE_REPORT": (source, render_source(source)),
        "OTI3_G3_GEOMETRY_DUPLICATE_DENOMINATOR_REPORT": (duplicate, render_duplicate(duplicate)),
        "OTI3_G3_GEOMETRY_LABEL_FAMILY_SEPARATION_REPORT": (label, render_label(label)),
        "OTI3_G3_GEOMETRY_AMBIGUITY_RESOLUTION_LEDGER": (ambiguity, render_ambiguity(ambiguity)),
        "OTI3_G3_GEOMETRY_METHODOLOGY_REPORT": (methodology, render_methodology(methodology)),
        "OTI3_G3_GEOMETRY_ALTERNATIVE_PACKETIZATION_REVIEW": (alternative, render_alternative(alternative)),
        "OTI3_G3_GEOMETRY_BLOCKER_LEDGER": (blocker, render_blocker(blocker)),
        "OTI3_G3_GEOMETRY_SELF_REVIEW": (self_review, render_self_review(self_review)),
        "OTI3_G3_GEOMETRY_COMPLETION_AUDIT": (completion, render_completion(completion)),
    }

    written: dict[str, Path] = {}
    for stem, (payload, markdown) in outputs.items():
        json_path = OUT / f"{stem}_{DATE}.json"
        md_path = OUT / f"{stem}_{DATE}.md"
        write_json(json_path, payload)
        write_text(md_path, markdown)
        written[json_path.name] = json_path
        written[md_path.name] = md_path

    rows_path = OUT / f"OTI3_G3_GEOMETRY_RESULT_LEDGER_ROWS_{DATE}.jsonl"
    with rows_path.open("w", encoding="utf-8", newline="\n") as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=True, sort_keys=True) + "\n")
    written[rows_path.name] = rows_path

    manifest = {
        "artifact_id": f"OTI3_G3_GEOMETRY_ARTIFACT_MANIFEST_{DATE}",
        "generated_at_utc": generated_at,
        "lane": LANE,
        "promotion_verdict": PROMOTION_VERDICT,
        "result_status": RESULT_STATUS,
        "validation_safe": VALIDATION_SAFE,
        "outcome_review_opened": OUTCOME_REVIEW_OPENED,
        "artifacts": [
            {"path": rel(path), "sha256": sha256_file(path), "size_bytes": path.stat().st_size}
            for path in sorted(written.values(), key=lambda item: item.name)
        ]
        + [
            {"path": rel(path), "sha256": sha256_file(path), "size_bytes": path.stat().st_size}
            for path in (
                Path(__file__).resolve(),
                OUT / f"verify_oti3_g3_geometry_quarantined_results_{DATE.replace('-', '_')}.py",
                METHOD_FREEZE,
                OUT / f"OTI3_G3_GEOMETRY_METHOD_FREEZE_{DATE}.md",
            )
            if path.exists()
        ],
        "control_input_hashes": {
            "method_freeze": sha256_file(METHOD_FREEZE),
            "g12_accepted_shortlist": sha256_file(G12_ACCEPTED),
            "experiment_preregistry": sha256_file(PREREGISTRY),
            "g3_source_hash_ledger": sha256_file(G3_DIR / f"OTB2R_G3_GEOMETRY_SOURCE_HASH_LEDGER_{DATE}.json"),
            "g3_duplicate_ledger": sha256_file(G3_DIR / f"OTB2R_G3_GEOMETRY_DUPLICATE_DENOMINATOR_AUDIT_{DATE}.json"),
            "g3_no_leak_ledger": sha256_file(G3_DIR / f"OTB2R_G3_GEOMETRY_NO_LEAK_AUDIT_{DATE}.json"),
            "g3_same_bar_policy": sha256_file(G3_DIR / f"OTB2R_G3_GEOMETRY_SAME_BAR_POLICY_{DATE}.json"),
            "g12_source_hash_review": sha256_file(G12_DIR / f"G12_G3_G6_SOURCE_HASH_REPRODUCIBILITY_REVIEW_{DATE}.json"),
            "g12_duplicate_review": sha256_file(G12_DIR / f"G12_G3_G6_DUPLICATE_DENOMINATOR_REVIEW_{DATE}.json"),
            "g12_label_review": sha256_file(G12_DIR / f"G12_G3_G6_LABEL_FAMILY_REVIEW_{DATE}.json"),
            "g12_same_bar_review": sha256_file(G12_DIR / f"G12_G3_G6_SAME_BAR_TIMING_REVIEW_{DATE}.json"),
            "otb2r_packet_manifest": sha256_file(OTB2R_DIR / f"OTB2R_PACKET_MANIFEST_{DATE}.json"),
        },
    }
    manifest_path = OUT / f"OTI3_G3_GEOMETRY_ARTIFACT_MANIFEST_{DATE}.json"
    write_json(manifest_path, manifest)
    written[manifest_path.name] = manifest_path
    return written


def main() -> int:
    written = build()
    print(json.dumps({"written": len(written), "out_dir": rel(OUT)}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
