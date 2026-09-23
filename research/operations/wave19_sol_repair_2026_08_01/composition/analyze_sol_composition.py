#!/usr/bin/env python3
"""Session FF: streaming Sol eligibility/composition attribution.

The script reads only the commissioned January development and February
used-once attribution surfaces.  It never reads March, never calls a replay,
and never imports broker/runtime code.  Large JSONL ledgers are streamed once;
only compact counters, scoreable breaker/structural rows, and the 127 selected
probe identities are retained.

The hard-eligible set is deliberately *not* reconstructed from similarly named
surrogate fields.  The in-memory finalizer computed an exact set, but the
train-lane scalar projection discarded it in both commissioned arms.  This
analysis reports exact observable stages, explicit hard/rank bounds, and the
default-off emission repair that closes the gap for future arms.
"""

from __future__ import annotations

import collections
import gzip
import hashlib
import json
import math
from pathlib import Path
import random
from typing import Any, Iterable, Mapping, Sequence


OUT = Path(__file__).resolve().parent

ROUTE = (
    "research/operations/"
    "final_moonshot_ultimate_system_denominator_to_deployment_execution_2026_06_20/"
    "attempt_5_typed_sparse"
)
WINDOWS = {
    "january": {
        "root": Path("/Users/borr/GTOSActive/worktrees/wave16-rematerialization-20260731")
        / ROUTE
        / "CJ_RECLOCKED_S0R0_V7",
        "stem": "CJ_RECLOCKED_S0R0_V7",
        "pool": Path(
            "/Users/borr/GTOSActive/worktrees/wave19-broad-forensic-20260801/"
            "docs/audits/fable5-vision-audit-20260725/phase16/receipts/pools/"
            "CJ_RECLOCKED_S0R0_POOL_V1.jsonl.gz"
        ),
        "evidence_role": "JANUARY_DEVELOPMENT_FORENSIC",
    },
    "february": {
        "root": Path("/Users/borr/GTOSActive/worktrees/wave18-true-utc-factory-20260801")
        / ROUTE
        / "CP_FEBRUARY_TRUE_UTC_S0R0_V1",
        "stem": "CP_FEBRUARY_TRUE_UTC_S0R0_V1",
        "pool": Path(
            "/Users/borr/GTOSActive/worktrees/wave19-broad-forensic-20260801/"
            "docs/audits/fable5-vision-audit-20260725/phase18/receipts/pools/"
            "CP_FEBRUARY_S0R0_POOL_V1.jsonl.gz"
        ),
        "evidence_role": "USED_ONCE_VAL_ATTRIBUTION_ONLY_owner_mandate_20260801",
    },
}

IDENTITY_FIELDS = (
    "candidate_id",
    "decision_time_utc",
    "symbol",
    "side_or_direction",
)
RISK_BEARING_ACTIONS = {"trade", "reduce-risk", "open-reduced-risk"}
TENSION_FAMILIES = {"current_breaker_re_entry", "structural_distance_extreme"}
FVG = "current_fvg_fill"
BOOTSTRAP_ITERATIONS = 20_000
BOOTSTRAP_SEED = 20260801


class SourceTracker:
    """Physical-byte hash and row count for one source as it is consumed."""

    def __init__(self, path: Path, role: str) -> None:
        self.path = path
        self.role = role
        self.rows = 0
        self.digest = hashlib.sha256()
        self.compressed = path.suffix == ".gz"

    def record(self, physical_line: bytes) -> None:
        self.rows += 1
        self.digest.update(physical_line)

    def receipt(self) -> dict[str, Any]:
        return {
            "role": self.role,
            "path": str(self.path),
            "physical_bytes": self.path.stat().st_size,
            "rows_observed": self.rows,
            "sha256_scope": (
                "decompressed_jsonl_bytes" if self.compressed else "physical_file_bytes"
            ),
            "sha256": self.digest.hexdigest(),
            "read_only": True,
        }


SOURCE_TRACKERS: dict[str, SourceTracker] = {}


def iter_jsonl(path: Path, role: str) -> Iterable[dict[str, Any]]:
    if not path.is_file():
        raise FileNotFoundError(path)
    key = f"{role}:{path}"
    if key in SOURCE_TRACKERS:
        raise AssertionError(f"source unexpectedly read twice: {key}")
    tracker = SourceTracker(path, role)
    SOURCE_TRACKERS[key] = tracker
    opener = gzip.open if path.suffix == ".gz" else open
    with opener(path, "rb") as handle:
        for raw in handle:
            tracker.record(raw)
            row = json.loads(raw)
            if not isinstance(row, dict):
                raise TypeError(f"non-object JSONL row in {path}:{tracker.rows}")
            yield row


def ledger_path(spec: Mapping[str, Any], suffix: str) -> Path:
    return Path(spec["root"]) / f"{spec['stem']}_{suffix}.jsonl"


def side(row: Mapping[str, Any]) -> str:
    return str(row.get("side") or row.get("direction") or "").upper()


def identity(row: Mapping[str, Any]) -> tuple[str, str, str, str]:
    key = (
        str(row.get("candidate_id") or ""),
        str(row.get("decision_time_utc") or row.get("decision_time") or ""),
        str(row.get("symbol") or ""),
        side(row),
    )
    if not all(key):
        raise ValueError(f"incomplete composite identity: {key}")
    return key


def identity_json(key: tuple[str, str, str, str]) -> dict[str, str]:
    return dict(zip(IDENTITY_FIELDS, key))


def family(row: Mapping[str, Any]) -> str:
    value = (
        row.get("origin_family")
        or row.get("route_family")
        or row.get("framework")
        or "unknown"
    )
    text = str(value)
    return text.removeprefix("origin_")


def number(value: Any) -> float | None:
    if isinstance(value, bool):
        return None
    if isinstance(value, (int, float)) and math.isfinite(float(value)):
        return float(value)
    return None


def first_number(row: Mapping[str, Any], *keys: str) -> float | None:
    for key in keys:
        value = number(row.get(key))
        if value is not None:
            return value
    return None


def day_of(row: Mapping[str, Any]) -> str:
    return str(row.get("decision_time_utc") or row.get("decision_time") or "")[:10]


def quantile(sorted_values: Sequence[float], q: float) -> float | None:
    if not sorted_values:
        return None
    if len(sorted_values) == 1:
        return float(sorted_values[0])
    position = (len(sorted_values) - 1) * q
    lower = int(math.floor(position))
    upper = int(math.ceil(position))
    if lower == upper:
        return float(sorted_values[lower])
    weight = position - lower
    return float(sorted_values[lower] * (1.0 - weight) + sorted_values[upper] * weight)


def wilson_interval(successes: int, total: int, z: float = 1.95996398454) -> list[float] | None:
    if total <= 0:
        return None
    p = successes / total
    denominator = 1.0 + z * z / total
    center = (p + z * z / (2.0 * total)) / denominator
    half = (
        z
        * math.sqrt(p * (1.0 - p) / total + z * z / (4.0 * total * total))
        / denominator
    )
    return [round(max(0.0, center - half), 8), round(min(1.0, center + half), 8)]


def cluster_bootstrap_mean_ci(
    values_by_cluster: Mapping[str, Sequence[float]],
    *,
    seed_offset: int = 0,
) -> list[float] | None:
    groups = [list(values) for values in values_by_cluster.values() if values]
    if not groups:
        return None
    if len(groups) == 1:
        value = sum(groups[0]) / len(groups[0])
        return [round(value, 8), round(value, 8)]
    rng = random.Random(BOOTSTRAP_SEED + seed_offset)
    means: list[float] = []
    n_groups = len(groups)
    for _ in range(BOOTSTRAP_ITERATIONS):
        total = 0.0
        count = 0
        for _ in range(n_groups):
            group = groups[rng.randrange(n_groups)]
            total += sum(group)
            count += len(group)
        means.append(total / count)
    means.sort()
    return [
        round(quantile(means, 0.025) or 0.0, 8),
        round(quantile(means, 0.975) or 0.0, 8),
    ]


def value_stats(
    rows: Sequence[Mapping[str, Any]],
    *,
    value_keys: Sequence[str],
    seed_offset: int = 0,
) -> dict[str, Any]:
    values: list[float] = []
    by_day: dict[str, list[float]] = collections.defaultdict(list)
    for row in rows:
        value = first_number(row, *value_keys)
        if value is None:
            continue
        values.append(value)
        by_day[day_of(row)].append(value)
    values.sort()
    wins = sum(value > 0.0 for value in values)
    return {
        "rows": len(rows),
        "scoreable_n": len(values),
        "unscoreable_n": len(rows) - len(values),
        "sum_r": round(sum(values), 8),
        "mean_r": round(sum(values) / len(values), 8) if values else None,
        "median_r": round(quantile(values, 0.5) or 0.0, 8) if values else None,
        "mean_r_day_cluster_bootstrap_95ci": cluster_bootstrap_mean_ci(
            by_day, seed_offset=seed_offset
        ),
        "bootstrap_iterations": BOOTSTRAP_ITERATIONS,
        "bootstrap_unit": "decision_day_cluster",
        "wins": wins,
        "win_share": round(wins / len(values), 8) if values else None,
        "win_share_wilson_95ci": wilson_interval(wins, len(values)),
    }


def counter_json(counter: collections.Counter[Any]) -> dict[str, int]:
    return {str(key): int(value) for key, value in counter.most_common()}


def nested_counter_json(
    counter: Mapping[str, collections.Counter[Any]],
) -> dict[str, dict[str, int]]:
    return {key: counter_json(value) for key, value in counter.items()}


def cost_band(row: Mapping[str, Any]) -> str:
    value = first_number(row, "cost_r", "total_execution_cost_r", "expected_cost_r")
    if value is None:
        return "cost_missing"
    if value < 0.08:
        return "lt_0p08R"
    if value < 0.12:
        return "0p08_to_lt_0p12R"
    if value <= 0.15:
        return "0p12_to_0p15R"
    return "gt_0p15R"


def marketability_band(row: Mapping[str, Any]) -> str:
    value = row.get("limit_marketable_at_decision")
    if value is True:
        return "immediate_marketable"
    if value is False:
        return "passive_limit"
    return "marketability_unknown"


def compact_strata(
    rows: Sequence[Mapping[str, Any]],
    key_fn: Any,
    *,
    value_keys: Sequence[str],
    seed_base: int,
) -> dict[str, Any]:
    groups: dict[str, list[Mapping[str, Any]]] = collections.defaultdict(list)
    for row in rows:
        groups[str(key_fn(row))].append(row)
    return {
        key: value_stats(
            group,
            value_keys=value_keys,
            seed_offset=seed_base + index,
        )
        for index, (key, group) in enumerate(sorted(groups.items()))
    }


def load_small_ledgers(month: str, spec: Mapping[str, Any]) -> dict[str, Any]:
    accepted: dict[tuple[str, str, str, str], dict[str, Any]] = {}
    terminal: dict[tuple[str, str, str, str], dict[str, Any]] = {}
    order_status = collections.Counter()
    for row in iter_jsonl(ledger_path(spec, "ORDER_LEDGER"), f"{month}.order"):
        key = identity(row)
        status = str(row.get("order_status") or "unknown")
        order_status[status] += 1
        if status == "pending_accepted":
            if key in accepted:
                raise AssertionError(f"duplicate accepted probe: {key}")
            accepted[key] = row
        else:
            if key in terminal:
                raise AssertionError(f"duplicate terminal order: {key}")
            terminal[key] = row

    if set(accepted) != set(terminal):
        raise AssertionError(
            f"accepted/terminal composite mismatch {month}: "
            f"accepted_only={len(set(accepted)-set(terminal))}, "
            f"terminal_only={len(set(terminal)-set(accepted))}"
        )

    trades: dict[tuple[str, str, str, str], dict[str, Any]] = {}
    for row in iter_jsonl(ledger_path(spec, "TRADE_LEDGER"), f"{month}.trade"):
        key = identity(row)
        if key in trades:
            raise AssertionError(f"duplicate trade: {key}")
        trades[key] = row

    filled_keys = {
        key for key, row in terminal.items() if row.get("order_status") == "filled"
    }
    if filled_keys != set(trades):
        raise AssertionError(
            f"terminal fill/trade mismatch {month}: "
            f"filled_only={len(filled_keys-set(trades))}, "
            f"trade_only={len(set(trades)-filled_keys)}"
        )

    oracles: dict[tuple[str, str, str, str], dict[str, Any]] = {}
    for row in iter_jsonl(
        ledger_path(spec, "ORDERED_PATH_ORACLE_LEDGER"), f"{month}.ordered_path_oracle"
    ):
        key = identity(row)
        if key in oracles:
            raise AssertionError(f"duplicate ordered-path oracle: {key}")
        oracles[key] = row
    if set(oracles) != set(accepted):
        raise AssertionError(
            f"oracle/accepted mismatch {month}: "
            f"oracle_only={len(set(oracles)-set(accepted))}, "
            f"accepted_only={len(set(accepted)-set(oracles))}"
        )

    scorecards: dict[str, dict[str, Any]] = {}
    scorecard_status = collections.Counter()
    selected_probe_count = collections.Counter()
    occupancy = collections.Counter()
    candidate_sum = 0
    all_options_preserved_sum = 0
    order_executable_probe_sum = 0
    for row in iter_jsonl(
        ledger_path(spec, "SCORECARD_LEDGER"), f"{month}.scorecard"
    ):
        asof = str(row.get("decision_time_utc") or row.get("asof_utc") or "")
        if not asof or asof in scorecards:
            raise AssertionError(f"bad/duplicate scorecard asof {month}: {asof}")
        selected_n = int(row.get("risk_admitted_finalizer_selected_probe_count") or 0)
        open_n = int(row.get("open_position_count_seen") or 0)
        pending_n = int(row.get("pending_order_count_seen") or 0)
        candidate_n = int(row.get("candidate_count") or 0)
        scheduler_n = int(row.get("all_options_preserved_count") or 0)
        order_executable_n = int(
            row.get("risk_finalizer_order_executable_package_probe_count") or 0
        )
        status = str(row.get("risk_admitted_finalizer_status") or "unknown")
        candidate_sum += candidate_n
        all_options_preserved_sum += scheduler_n
        order_executable_probe_sum += order_executable_n
        scorecard_status[status] += 1
        selected_probe_count[selected_n] += 1
        occupancy[(open_n, pending_n, selected_n)] += 1
        scorecards[asof] = {
            "decision_time_utc": asof,
            "trading_day": str(row.get("trading_day") or asof[:10]),
            "candidate_count": candidate_n,
            "scheduler_option_count": scheduler_n,
            "selected_probe_count": selected_n,
            "status": status,
            "open_position_count_seen": open_n,
            "pending_order_count_seen": pending_n,
            "risk_finalizer_order_executable_package_probe_count": order_executable_n,
        }

    return {
        "accepted": accepted,
        "terminal": terminal,
        "trades": trades,
        "oracles": oracles,
        "order_status": order_status,
        "scorecards": scorecards,
        "scorecard_status": scorecard_status,
        "selected_probe_count": selected_probe_count,
        "occupancy": occupancy,
        "scorecard_candidate_sum": candidate_sum,
        "scorecard_all_options_preserved_sum": all_options_preserved_sum,
        "scorecard_order_executable_probe_sum": order_executable_probe_sum,
    }


def scan_full_missed(
    month: str,
    spec: Mapping[str, Any],
    accepted: Mapping[tuple[str, str, str, str], Mapping[str, Any]],
) -> dict[str, Any]:
    stages = ("pool", "cost_executable", "selector_pass", "scheduler_materialized")
    totals = collections.Counter()
    by_family = {stage: collections.Counter() for stage in stages}
    by_symbol = {stage: collections.Counter() for stage in stages}
    by_window = {stage: collections.Counter() for stage in stages}
    miss_reason = collections.Counter()
    risk_reason = collections.Counter()
    scheduler_disposition = collections.Counter()
    final_blocker = collections.Counter()
    scoreability = collections.Counter()
    pass_reason_surrogate = collections.Counter()
    direct_competition = collections.Counter()
    cost_missing = collections.Counter()
    cost_missing_family = collections.Counter()
    cost_missing_symbol = collections.Counter()
    cost_missing_session = collections.Counter()
    cost_missing_scoreability = collections.Counter()
    session_authority_family = collections.Counter()
    session_authority_symbol = collections.Counter()
    session_authority_reason = collections.Counter()
    session_authority_rows: list[dict[str, Any]] = []
    identities: set[tuple[str, str, str, str]] = set()
    candidate_id_counts = collections.Counter()

    # Selected probes were candidates at every preceding observable stage.
    for key, row in accepted.items():
        if key in identities:
            raise AssertionError(f"duplicate selected identity before missed scan: {key}")
        identities.add(key)
        candidate_id_counts[key[0]] += 1
        for stage in stages:
            totals[stage] += 1
            by_family[stage][family(row)] += 1
            by_symbol[stage][str(row.get("symbol"))] += 1
            by_window[stage][key[1]] += 1

    rows = 0
    for row in iter_jsonl(
        ledger_path(spec, "MISSED_OPPORTUNITY_LEDGER"), f"{month}.missed"
    ):
        rows += 1
        key = identity(row)
        if key in identities:
            raise AssertionError(f"terminal population composite collision {month}: {key}")
        identities.add(key)
        candidate_id_counts[key[0]] += 1
        fam = family(row)
        symbol = str(row.get("symbol") or "unknown")
        asof = key[1]

        cost_ok = row.get("broker_pretrade_cost_executable") is True
        selector_ok = cost_ok and str(row.get("effective_selector_action")) in RISK_BEARING_ACTIONS
        scheduler_ok = row.get("scheduler_materialization_status") == "scheduler_option_materialized"
        flags = {
            "pool": True,
            "cost_executable": cost_ok,
            "selector_pass": selector_ok,
            "scheduler_materialized": scheduler_ok,
        }
        for stage, enabled in flags.items():
            if enabled:
                totals[stage] += 1
                by_family[stage][fam] += 1
                by_symbol[stage][symbol] += 1
                by_window[stage][asof] += 1

        reason = str(row.get("miss_reason") or "unknown")
        risk = str(row.get("risk_finalizer_reason") or "unknown")
        disposition = str(row.get("scheduler_selection_disposition") or "unknown")
        blocker = str(
            row.get("missed_package_replay_order_executable_final_blocker_class")
            or row.get("final_blocker_class")
            or "unknown"
        )
        score = str(row.get("missed_opportunity_r_scoreability_status") or "unknown")
        miss_reason[reason] += 1
        risk_reason[risk] += 1
        scheduler_disposition[disposition] += 1
        final_blocker[blocker] += 1
        scoreability[score] += 1

        # These values look like admission reasons but are not the persisted
        # factorial hard-eligible bit.  Keep them only as a named surrogate to
        # prove why they cannot be substituted for the missing field.
        if risk in {
            "selector_reduce_risk_origin_preserved",
            "selector_open_reduced_risk_origin_preserved",
            "risk_authority_bound_and_headroom_available",
        }:
            pass_reason_surrogate[asof] += 1
        if reason == "scheduler_selected_competing_candidate":
            direct_competition[asof] += 1

        if "cost_missing" in reason:
            cost_missing[reason] += 1
            cost_missing_family[fam] += 1
            cost_missing_symbol[symbol] += 1
            cost_missing_session[str(row.get("authority_session") or row.get("session_bucket"))] += 1
            cost_missing_scoreability[score] += 1
        if blocker == "session_authority":
            session_authority_family[fam] += 1
            session_authority_symbol[symbol] += 1
            session_authority_reason[reason] += 1
            session_authority_rows.append(
                {
                    **identity_json(key),
                    "origin_family": fam,
                    "authority_session": row.get("authority_session"),
                    "session_bucket": row.get("session_bucket"),
                    "miss_reason": reason,
                    "risk_finalizer_reason": risk,
                    "scoreability_status": score,
                }
            )

    duplicate_candidate_ids = sum(count - 1 for count in candidate_id_counts.values() if count > 1)
    return {
        "missed_rows": rows,
        "composite_population_rows": len(identities),
        "composite_identity_unique": len(identities) == rows + len(accepted),
        "candidate_id_duplicate_excess_rows": duplicate_candidate_ids,
        "stage_totals": totals,
        "stage_by_family": by_family,
        "stage_by_symbol": by_symbol,
        "stage_by_window": by_window,
        "miss_reason": miss_reason,
        "risk_finalizer_reason": risk_reason,
        "scheduler_disposition": scheduler_disposition,
        "final_blocker": final_blocker,
        "scoreability": scoreability,
        "pass_reason_surrogate_by_window": pass_reason_surrogate,
        "direct_competition_by_window": direct_competition,
        "february_authority": {
            "cost_missing_total": sum(cost_missing.values()),
            "cost_missing_reasons": counter_json(cost_missing),
            "cost_missing_by_family": counter_json(cost_missing_family),
            "cost_missing_by_symbol": counter_json(cost_missing_symbol),
            "cost_missing_by_session": counter_json(cost_missing_session),
            "cost_missing_by_scoreability": counter_json(cost_missing_scoreability),
            "session_authority_total": len(session_authority_rows),
            "session_authority_by_family": counter_json(session_authority_family),
            "session_authority_by_symbol": counter_json(session_authority_symbol),
            "session_authority_by_reason": counter_json(session_authority_reason),
            "session_authority_rows": session_authority_rows,
        },
    }


def scan_scoreable_pool(month: str, spec: Mapping[str, Any]) -> dict[str, Any]:
    rows = 0
    family_counts = collections.Counter()
    tension_rows: dict[str, list[dict[str, Any]]] = collections.defaultdict(list)
    for row in iter_jsonl(Path(spec["pool"]), f"{month}.compact_scoreable_pool"):
        rows += 1
        fam = family(row)
        family_counts[fam] += 1
        if fam in TENSION_FAMILIES:
            tension_rows[fam].append(row)
    return {
        "rows": rows,
        "family_counts": family_counts,
        "tension_rows": tension_rows,
    }


def stage_entry(total: int, target: int) -> dict[str, Any]:
    return {
        "total_n": int(total),
        "target_n": int(target),
        "target_share": round(target / total, 12) if total else None,
    }


def build_enrichment(
    scans: Mapping[str, Mapping[str, Any]],
    small: Mapping[str, Mapping[str, Any]],
) -> dict[str, Any]:
    out: dict[str, Any] = {
        "schema": "gtos.wave19.session_ff.fvg_enrichment.v1",
        "identity_key": list(IDENTITY_FIELDS),
        "stage_order": [
            "pool",
            "cost_executable",
            "selector_pass",
            "scheduler_materialized",
            "hard_eligible_UNOBSERVED",
            "neutral_ranked_UNOBSERVED",
            "selected",
            "filled",
        ],
        "hard_rank_observability": {
            "status": "NOT_IDENTIFIABLE_FROM_PERSISTED_TRAIN_LANE_PROJECTION",
            "reason": (
                "The finalizer computed exact per-window hard-eligible counts, digests, "
                "and instance keys, but ledger_scalar_projection removed the nested "
                "risk_admitted_scheduler_finalizer container. risk_finalizer_reason is "
                "a non-equivalent surrogate and is not substituted."
            ),
            "repair": "default-off hard_eligibility_observability projection",
            "repair_status": "IMPLEMENTED_DEFAULT_OFF_NOT_BACKFILLED",
        },
        "windows": {},
    }
    for month in ("january", "february"):
        scan = scans[month]
        sm = small[month]
        totals = scan["stage_totals"]
        fam = scan["stage_by_family"]
        sym = scan["stage_by_symbol"]
        selected = sm["accepted"]
        trades = sm["trades"]
        selected_fvg = sum(family(row) == FVG for row in selected.values())
        filled_fvg = sum(family(row) == FVG for row in trades.values())
        selected_xau = sum(row.get("symbol") == "XAUUSD" for row in selected.values())
        filled_xau = sum(row.get("symbol") == "XAUUSD" for row in trades.values())
        filled_rows = list(trades.values())
        filled_fvg_rows = [row for row in filled_rows if family(row) == FVG]
        filled_non_fvg_rows = [row for row in filled_rows if family(row) != FVG]
        filled_xau_rows = [row for row in filled_rows if row.get("symbol") == "XAUUSD"]
        filled_non_xau_rows = [
            row for row in filled_rows if row.get("symbol") != "XAUUSD"
        ]

        exact_fvg = {
            stage: stage_entry(totals[stage], fam[stage][FVG])
            for stage in (
                "pool",
                "cost_executable",
                "selector_pass",
                "scheduler_materialized",
            )
        }
        exact_fvg["selected"] = stage_entry(len(selected), selected_fvg)
        exact_fvg["filled"] = stage_entry(len(trades), filled_fvg)
        exact_xau = {
            stage: stage_entry(totals[stage], sym[stage]["XAUUSD"])
            for stage in (
                "pool",
                "cost_executable",
                "selector_pass",
                "scheduler_materialized",
            )
        }
        exact_xau["selected"] = stage_entry(len(selected), selected_xau)
        exact_xau["filled"] = stage_entry(len(trades), filled_xau)

        def transitions(chain: Mapping[str, Mapping[str, Any]]) -> list[dict[str, Any]]:
            keys = list(chain)
            result = []
            for left, right in zip(keys, keys[1:]):
                a = chain[left]["target_share"]
                b = chain[right]["target_share"]
                result.append(
                    {
                        "from": left,
                        "to": right,
                        "share_enrichment_factor": round(b / a, 12) if a else None,
                    }
                )
            return result

        fvg_product = exact_fvg["filled"]["target_share"] / exact_fvg["pool"]["target_share"]
        xau_product = exact_xau["filled"]["target_share"] / exact_xau["pool"]["target_share"]
        out["windows"][month] = {
            "population_reconciliation": {
                "missed_rows": scan["missed_rows"],
                "selected_probes": len(selected),
                "pool_rows": totals["pool"],
                "scorecard_candidate_sum": sm["scorecard_candidate_sum"],
                "pool_equals_scorecard_candidate_sum": (
                    totals["pool"] == sm["scorecard_candidate_sum"]
                ),
                "scheduler_materialized_rows": totals["scheduler_materialized"],
                "scorecard_all_options_preserved_sum": sm[
                    "scorecard_all_options_preserved_sum"
                ],
                "scorecard_order_executable_probe_sum": sm[
                    "scorecard_order_executable_probe_sum"
                ],
                "scheduler_crosscheck_status": (
                    "NOT_EQUAL_BY_SCHEMA: missed.scheduler_materialization_status, "
                    "scorecard.all_options_preserved_count, and finalizer order-"
                    "executable probes are different populations"
                ),
                "composite_identity_unique": scan["composite_identity_unique"],
                "candidate_id_duplicate_excess_rows": scan[
                    "candidate_id_duplicate_excess_rows"
                ],
            },
            "current_fvg_fill": {
                "exact_observable_chain": exact_fvg,
                "transitions_across_observable_chain": transitions(exact_fvg),
                "pool_to_filled_enrichment_product": round(fvg_product, 12),
                "product_reproduces_filled_share": (
                    round(exact_fvg["pool"]["target_share"] * fvg_product, 12)
                    == exact_fvg["filled"]["target_share"]
                ),
                "hard_eligible_count_bounds": {
                    "total_n": [len(selected), totals["scheduler_materialized"]],
                    "target_n": [selected_fvg, fam["scheduler_materialized"][FVG]],
                    "semantics": "selected lower bound; scheduler-materialized upper bound",
                },
                "neutral_ranked_count_bounds": {
                    "total_n": [len(selected), totals["scheduler_materialized"]],
                    "target_n": [selected_fvg, fam["scheduler_materialized"][FVG]],
                    "semantics": "same bounds; exact hard pool/rank list was projected out",
                },
                "filled_outcome_context": {
                    "current_fvg_fill": executed_family_row(
                        filled_fvg_rows, len(filled_rows)
                    ),
                    "all_other_families": executed_family_row(
                        filled_non_fvg_rows, len(filled_rows)
                    ),
                    "scope": "descriptive executed outcomes; not a gate-fit population",
                },
            },
            "XAUUSD": {
                "exact_observable_chain": exact_xau,
                "transitions_across_observable_chain": transitions(exact_xau),
                "pool_to_filled_enrichment_product": round(xau_product, 12),
                "product_reproduces_filled_share": (
                    round(exact_xau["pool"]["target_share"] * xau_product, 12)
                    == exact_xau["filled"]["target_share"]
                ),
                "commission_focus": month == "february",
                "filled_outcome_context": {
                    "XAUUSD": executed_family_row(filled_xau_rows, len(filled_rows)),
                    "all_other_symbols": executed_family_row(
                        filled_non_xau_rows, len(filled_rows)
                    ),
                    "scope": "descriptive executed outcomes; not a rank-fit population",
                },
            },
        }

    out["causal_read"] = {
        "current_fvg_fill": (
            "Cost execution de-enriches FVG in both months and fill conversion "
            "de-enriches it again. The large enrichment lies between scheduler "
            "materialization and S0 selection, but the exact hard/rank partition "
            "needed to attribute that jump was discarded. No economic family gate "
            "is licensed from this evidence."
        ),
        "february_XAUUSD": (
            "Cost execution enriches XAUUSD and the scheduler-to-selection interval "
            "enriches it further. Fill conversion is small and positive. February "
            "XAUUSD is gross-positive while non-XAUUSD is gross-negative; both are "
            "net-negative after costs. S0 is an outcome-blind neutral hash, so the "
            "concentration is measured, not proof of a quality rank defect."
        ),
    }
    return out


def build_family_tension(
    pools: Mapping[str, Mapping[str, Any]],
    small: Mapping[str, Mapping[str, Any]],
) -> dict[str, Any]:
    result: dict[str, Any] = {
        "schema": "gtos.wave19.session_ff.family_tension.v1",
        "uncertainty": {
            "bootstrap_iterations": BOOTSTRAP_ITERATIONS,
            "bootstrap_seed": BOOTSTRAP_SEED,
            "bootstrap_unit": "decision_day_cluster",
            "binomial_interval": "Wilson 95%",
        },
        "choice_set_definition": (
            "Scoreable non-selected rows with the same origin family and exact "
            "decision_time_utc as each executed trade. Composite identity remains "
            "candidate_id + decision_time_utc + symbol + side."
        ),
        "windows": {},
    }
    seed_offset = 100
    for month in ("january", "february"):
        month_out: dict[str, Any] = {}
        trades_all = list(small[month]["trades"].values())
        for fam in sorted(TENSION_FAMILIES):
            pool_rows = list(pools[month]["tension_rows"].get(fam, []))
            executed_rows = [row for row in trades_all if family(row) == fam]
            peers_by_time: dict[str, list[dict[str, Any]]] = collections.defaultdict(list)
            for row in pool_rows:
                peers_by_time[str(row.get("decision_time_utc"))].append(row)
            matched_deltas: list[dict[str, Any]] = []
            unmatched: list[dict[str, str]] = []
            for trade in executed_rows:
                peers = peers_by_time.get(str(trade.get("decision_time_utc")), [])
                peer_values = [
                    value
                    for row in peers
                    for value in [first_number(row, "opportunity_net_proxy_r")]
                    if value is not None
                ]
                trade_net = first_number(trade, "net_r")
                if trade_net is None or not peer_values:
                    unmatched.append(identity_json(identity(trade)))
                    continue
                peer_mean = sum(peer_values) / len(peer_values)
                matched_deltas.append(
                    {
                        **identity_json(identity(trade)),
                        "executed_net_r": round(trade_net, 8),
                        "same_window_family_peer_n": len(peer_values),
                        "same_window_family_peer_mean_net_proxy_r": round(peer_mean, 8),
                        "executed_minus_peer_mean_r": round(trade_net - peer_mean, 8),
                    }
                )

            delta_rows = [
                {
                    "decision_time_utc": row["decision_time_utc"],
                    "delta": row["executed_minus_peer_mean_r"],
                }
                for row in matched_deltas
            ]
            delta_stats = value_stats(
                delta_rows,
                value_keys=("delta",),
                seed_offset=seed_offset,
            )
            seed_offset += 1
            pool_stats = value_stats(
                pool_rows,
                value_keys=("opportunity_net_proxy_r",),
                seed_offset=seed_offset,
            )
            seed_offset += 1
            executed_stats = value_stats(
                executed_rows,
                value_keys=("net_r",),
                seed_offset=seed_offset,
            )
            seed_offset += 1
            pool_mean = pool_stats["mean_r"]
            executed_mean = executed_stats["mean_r"]
            month_out[fam] = {
                "scoreable_nonselected_pool": pool_stats,
                "executed": executed_stats,
                "sign_tension": (
                    pool_mean is not None
                    and executed_mean is not None
                    and (pool_mean < 0.0 < executed_mean or executed_mean < 0.0 < pool_mean)
                ),
                "own_choice_set": {
                    "executed_with_scoreable_same_window_family_peers": len(matched_deltas),
                    "executed_without_scoreable_same_window_family_peers": len(unmatched),
                    "unmatched_executed_identities": unmatched,
                    "paired_delta_stats": delta_stats,
                    "paired_rows": matched_deltas,
                },
                "cost_strata": {
                    "pool": compact_strata(
                        pool_rows,
                        cost_band,
                        value_keys=("opportunity_net_proxy_r",),
                        seed_base=seed_offset + 10,
                    ),
                    "executed": compact_strata(
                        executed_rows,
                        cost_band,
                        value_keys=("net_r",),
                        seed_base=seed_offset + 20,
                    ),
                },
                "fillability_strata": {
                    "pool": compact_strata(
                        pool_rows,
                        marketability_band,
                        value_keys=("opportunity_net_proxy_r",),
                        seed_base=seed_offset + 30,
                    ),
                    "executed": compact_strata(
                        executed_rows,
                        marketability_band,
                        value_keys=("net_r",),
                        seed_base=seed_offset + 40,
                    ),
                },
                "executed_path_strata": compact_strata(
                    executed_rows,
                    lambda row: row.get("order_execution_path") or row.get("fill_realism_class") or "unknown",
                    value_keys=("net_r",),
                    seed_base=seed_offset + 50,
                ),
            }
            seed_offset += 100
        result["windows"][month] = month_out

    # Entry convention audit uses the selected oracle, not a guessed fill.
    convention = collections.Counter()
    for month in ("january", "february"):
        for key, trade in small[month]["trades"].items():
            oracle = small[month]["oracles"][key]
            entry = first_number(trade, "entry_price")
            fill = first_number(oracle, "fill_price", "fallback_fill_price", "entry_price")
            if entry is None or fill is None:
                convention["unresolved"] += 1
            elif math.isclose(entry, fill, rel_tol=0.0, abs_tol=1e-9):
                convention["entry_equals_executed_fill"] += 1
            else:
                convention["entry_differs_from_executed_fill"] += 1
    result["execution_convention_audit"] = counter_json(convention)
    result["verdict"] = (
        "The apparent positive executed breaker/structural signs are tiny-sample "
        "conditional slices, not a demonstrated family-ranking effect. S0 never "
        "uses outcomes, same-window peer coverage is sparse, and uncertainty must "
        "be read from the reported intervals. Entry-price convention is audited "
        "separately; any remaining difference is cost/path/choice-set composition."
    )
    return result


def mean_field(rows: Sequence[Mapping[str, Any]], *keys: str) -> float | None:
    values = [value for row in rows for value in [first_number(row, *keys)] if value is not None]
    return round(sum(values) / len(values), 8) if values else None


def observed_numeric_summary(
    rows: Sequence[Mapping[str, Any]], field: str
) -> dict[str, Any]:
    values = [value for row in rows for value in [number(row.get(field))] if value is not None]
    counts = collections.Counter(str(round(value, 9)) for value in values)
    return {
        "field": field,
        "observed_n": len(values),
        "missing_n": len(rows) - len(values),
        "minimum": round(min(values), 9) if values else None,
        "maximum": round(max(values), 9) if values else None,
        "distribution": counter_json(counts),
    }


def rate_table(
    accepted: Mapping[tuple[str, str, str, str], Mapping[str, Any]],
    terminal: Mapping[tuple[str, str, str, str], Mapping[str, Any]],
    key_fn: Any,
) -> dict[str, Any]:
    buckets: dict[str, list[tuple[str, str, str, str]]] = collections.defaultdict(list)
    for key, row in accepted.items():
        buckets[str(key_fn(row))].append(key)
    out = {}
    for bucket, keys in sorted(buckets.items()):
        filled = sum(terminal[key].get("order_status") == "filled" for key in keys)
        out[bucket] = {
            "selected_n": len(keys),
            "filled_n": filled,
            "fill_rate": round(filled / len(keys), 8),
            "fill_rate_wilson_95ci": wilson_interval(filled, len(keys)),
        }
    return out


def build_probe_conversion(small: Mapping[str, Mapping[str, Any]]) -> dict[str, Any]:
    out: dict[str, Any] = {
        "schema": "gtos.wave19.session_ff.probe_conversion.v1",
        "identity_key": list(IDENTITY_FIELDS),
        "windows": {},
    }
    global_class = collections.Counter()
    global_fallback_status = collections.Counter()
    global_fallback_reason = collections.Counter()
    for month in ("january", "february"):
        sm = small[month]
        accepted = sm["accepted"]
        terminal = sm["terminal"]
        trades = sm["trades"]
        oracles = sm["oracles"]
        unconverted: list[dict[str, Any]] = []
        classes = collections.Counter()
        fallback_status = collections.Counter()
        fallback_reason = collections.Counter()
        for key, terminal_row in terminal.items():
            status = str(terminal_row.get("order_status"))
            if status == "filled":
                continue
            accepted_row = accepted[key]
            oracle = oracles[key]
            if (
                status == "expired_unfilled"
                and oracle.get("entry_fill_authority_status")
                == "entry_not_touched_before_expiry"
            ):
                classification = "true_no_touch_expiry"
            elif status == "cancelled_replaced_by_scheduler_v4":
                classification = "same_symbol_lifecycle_replacement"
            else:
                classification = "unresolved_terminal_nonfill"
            classes[classification] += 1
            global_class[classification] += 1
            guarded_status = str(oracle.get("guarded_market_fallback_status") or "unknown")
            guarded_reason = str(oracle.get("guarded_market_fallback_reason") or "unknown")
            fallback_status[guarded_status] += 1
            fallback_reason[guarded_reason] += 1
            global_fallback_status[guarded_status] += 1
            global_fallback_reason[guarded_reason] += 1
            entry = {
                **identity_json(key),
                "origin_family": family(accepted_row),
                "session_bucket": accepted_row.get("session_bucket"),
                "terminal_order_status": status,
                "classification": classification,
                "created_time_utc": accepted_row.get("created_time_utc"),
                "terminal_event_time_utc": terminal_row.get("event_time_utc"),
                "expiry_utc": accepted_row.get("expiry_utc"),
                "order_execution_path": accepted_row.get("order_execution_path"),
                "limit_marketable_at_decision": accepted_row.get(
                    "limit_marketable_at_decision"
                ),
                "predecision_execution_fill_probability": accepted_row.get(
                    "execution_fill_probability"
                ),
                "predecision_entry_quality_fill_probability": accepted_row.get(
                    "entry_quality_fill_probability"
                ),
                "cost_r": first_number(accepted_row, "cost_r", "total_execution_cost_r"),
                "oracle_fill_status": oracle.get("fill_status"),
                "oracle_entry_fill_authority_status": oracle.get(
                    "entry_fill_authority_status"
                ),
                "oracle_limit_first_touch_utc": oracle.get("limit_first_entry_first_touch_utc"),
                "oracle_limit_first_touch_count": oracle.get(
                    "limit_first_passive_limit_queue_touch_count"
                ),
                "oracle_path_source": oracle.get("limit_first_path_source"),
                "oracle_guarded_fallback_status": oracle.get(
                    "guarded_market_fallback_status"
                ),
                "oracle_guarded_fallback_reason": oracle.get(
                    "guarded_market_fallback_reason"
                ),
                "late_market_fallback_refused": guarded_status == "not_eligible",
            }
            if classification == "same_symbol_lifecycle_replacement":
                old_order_id = str(accepted_row.get("simulated_order_id") or "")
                replacements = [
                    (other_key, other)
                    for other_key, other in accepted.items()
                    if old_order_id
                    in list(other.get("scheduler_option_pending_replacement_release_pending_ids") or [])
                ]
                if len(replacements) != 1:
                    raise AssertionError(
                        f"replacement binding expected one successor, got {len(replacements)}: {key}"
                    )
                replacement_key, replacement = replacements[0]
                replacement_trade = trades.get(replacement_key)
                counterfactual_gross = first_number(
                    oracle,
                    "selected_execution_policy_replay_final_r",
                    "exit_composition_selected_policy_gross_r",
                )
                counterfactual_cost = first_number(oracle, "cost_r", "total_execution_cost_r")
                entry["replacement"] = {
                    **identity_json(replacement_key),
                    "released_pending_order_id": old_order_id,
                    "replacement_order_id": replacement.get("simulated_order_id"),
                    "replacement_terminal_status": terminal[replacement_key].get(
                        "order_status"
                    ),
                    "replacement_fill_time_utc": terminal[replacement_key].get(
                        "fill_time_utc"
                    ),
                    "replacement_net_r": (
                        first_number(replacement_trade or {}, "net_r")
                    ),
                }
                entry["cancelled_fallback_counterfactual"] = {
                    "fill_time_utc": oracle.get("fallback_fill_time_utc"),
                    "gross_r": counterfactual_gross,
                    "cost_r": counterfactual_cost,
                    "net_r": (
                        round(counterfactual_gross - counterfactual_cost, 8)
                        if counterfactual_gross is not None
                        and counterfactual_cost is not None
                        else None
                    ),
                    "scope": "ordered-path counterfactual only; order was cancelled",
                }
            unconverted.append(entry)

        accepted_rows = list(accepted.values())
        filled_accepted = [
            accepted[key]
            for key, row in terminal.items()
            if row.get("order_status") == "filled"
        ]
        unfilled_accepted = [
            accepted[key]
            for key, row in terminal.items()
            if row.get("order_status") != "filled"
        ]
        path_outcomes = compact_strata(
            list(trades.values()),
            lambda row: row.get("order_execution_path") or "unknown",
            value_keys=("net_r",),
            seed_base=700 if month == "january" else 800,
        )
        filled_n = len(trades)
        out["windows"][month] = {
            "reconciliation": {
                "selected_probes": len(accepted),
                "terminal_orders": len(terminal),
                "filled_orders": filled_n,
                "trade_rows": len(trades),
                "unconverted": len(accepted) - filled_n,
                "selected_minus_unconverted_equals_trades": (
                    len(accepted) - (len(accepted) - filled_n) == len(trades)
                ),
                "order_status_counts": counter_json(sm["order_status"]),
            },
            "unconverted_class_counts": counter_json(classes),
            "unconverted_guarded_fallback_status_counts": counter_json(
                fallback_status
            ),
            "unconverted_guarded_fallback_reason_counts": counter_json(
                fallback_reason
            ),
            "all_unconverted_probes": sorted(
                unconverted,
                key=lambda row: (row["decision_time_utc"], row["candidate_id"]),
            ),
            "fill_conversion": {
                "overall": {
                    "selected_n": len(accepted),
                    "filled_n": filled_n,
                    "fill_rate": round(filled_n / len(accepted), 8),
                    "fill_rate_wilson_95ci": wilson_interval(filled_n, len(accepted)),
                },
                "by_family": rate_table(accepted, terminal, family),
                "by_symbol": rate_table(
                    accepted, terminal, lambda row: row.get("symbol") or "unknown"
                ),
                "by_order_execution_path": rate_table(
                    accepted,
                    terminal,
                    lambda row: row.get("order_execution_path") or "unknown",
                ),
                "by_marketable_at_decision": rate_table(
                    accepted, terminal, marketability_band
                ),
            },
            "predecision_filled_vs_unfilled": {
                "filled_n": len(filled_accepted),
                "unfilled_n": len(unfilled_accepted),
                "execution_fill_probability_mean": {
                    "filled": mean_field(filled_accepted, "execution_fill_probability"),
                    "unfilled": mean_field(unfilled_accepted, "execution_fill_probability"),
                },
                "entry_quality_fill_probability_mean": {
                    "filled": mean_field(filled_accepted, "entry_quality_fill_probability"),
                    "unfilled": mean_field(unfilled_accepted, "entry_quality_fill_probability"),
                },
                "cost_r_mean": {
                    "filled": mean_field(
                        filled_accepted, "cost_r", "total_execution_cost_r"
                    ),
                    "unfilled": mean_field(
                        unfilled_accepted, "cost_r", "total_execution_cost_r"
                    ),
                },
            },
            "filled_path_outcomes": path_outcomes,
            "economic_fill_selection_bias": {
                "status": "NOT_IDENTIFIABLE_FOR_TRUE_NO_TOUCH_LIMITS",
                "reason": (
                    "A no-touch limit has no post-fill entry time and therefore no "
                    "trade terminal R. Treating it as zero or entering at a later "
                    "market price would change the policy. The one cancelled guarded "
                    "fallback has an ordered-path counterfactual reported above."
                ),
                "mechanical_selection": (
                    "Passive fills condition on the path reaching/penetrating the limit; "
                    "path-stratified realized outcomes are descriptive, not a causal "
                    "estimate against unfilled orders."
                ),
            },
        }

    out["global_reconciliation"] = {
        "unconverted_total": sum(global_class.values()),
        "class_counts": counter_json(global_class),
        "unconverted_guarded_fallback_status_counts": counter_json(
            global_fallback_status
        ),
        "unconverted_guarded_fallback_reason_counts": counter_json(
            global_fallback_reason
        ),
        "late_market_fallback_refused_count": global_fallback_status["not_eligible"],
        "late_market_fallback_refusal_outcome_status": (
            "NOT_IDENTIFIABLE_WITHOUT_CHANGING_THE_ORDERED_POLICY"
        ),
        "true_no_touch_expiries": global_class["true_no_touch_expiry"],
        "lifecycle_replacements": global_class["same_symbol_lifecycle_replacement"],
    }
    return out


def occupancy_table(counter: collections.Counter[tuple[int, int, int]]) -> list[dict[str, int]]:
    return [
        {
            "open_position_count_seen": open_n,
            "pending_order_count_seen": pending_n,
            "selected_probe_count": selected_n,
            "window_count": count,
        }
        for (open_n, pending_n, selected_n), count in sorted(counter.items())
    ]


def build_capacity(
    scans: Mapping[str, Mapping[str, Any]],
    small: Mapping[str, Mapping[str, Any]],
) -> dict[str, Any]:
    out: dict[str, Any] = {
        "schema": "gtos.wave19.session_ff.capacity_census.v1",
        "hard_eligibility_observability": {
            "status": "MISSING_FROM_BOTH_PERSISTED_SCORECARD_LEDGERS",
            "required_exact_fields": [
                "b7_5_selection_sizing_factorial_hard_eligible_pool_count",
                "b7_5_selection_sizing_factorial_hard_eligible_pool_digest_sha256",
                "b7_5_selection_sizing_factorial_hard_eligible_instance_keys",
                "b7_5_factorial_hard_eligible_option_rows",
            ],
            "non_equivalent_surrogate_rejected": "risk_finalizer_reason",
            "repair": "train-engine default-off hard_eligibility_observability patch",
            "repair_status": "IMPLEMENTED_DEFAULT_OFF_NOT_BACKFILLED",
        },
        "windows": {},
    }
    for month in ("january", "february"):
        scan = scans[month]
        sm = small[month]
        selected = sm["accepted"]
        selected_rows = list(selected.values())
        selected_by_window = collections.Counter(key[1] for key in selected)
        selected_by_day = collections.Counter(key[1][:10] for key in selected)
        scheduler_by_window = scan["stage_by_window"]["scheduler_materialized"]
        selected_windows = set(selected_by_window)
        scheduler_windows = set(scheduler_by_window)
        no_selected_scheduler_windows = scheduler_windows - selected_windows
        pass_surrogate = scan["pass_reason_surrogate_by_window"]
        false_surrogate_windows = {
            window
            for window in pass_surrogate
            if window not in selected_windows
        }
        multi_selected = {
            window: count for window, count in selected_by_window.items() if count > 1
        }
        direct_competition = scan["direct_competition_by_window"]
        zero_probe_status = collections.Counter(
            card["status"]
            for card in sm["scorecards"].values()
            if card["selected_probe_count"] == 0
        )
        positive_probe_status = collections.Counter(
            card["status"]
            for card in sm["scorecards"].values()
            if card["selected_probe_count"] > 0
        )
        extra_slot_rows = [
            {
                **identity_json(identity(row)),
                "origin_family": family(row),
                "extra_slot_allowed": row.get(
                    "risk_finalizer_same_decision_cluster_side_package_extra_slot_allowed"
                ),
                "base_limit": row.get(
                    "risk_finalizer_same_decision_cluster_side_package_extra_slot_base_limit"
                ),
                "maximum_count": row.get(
                    "risk_finalizer_same_decision_cluster_side_package_extra_slot_max_count"
                ),
                "prior_count": row.get(
                    "risk_finalizer_same_decision_cluster_side_package_extra_slot_prior_count"
                ),
                "prior_risk_pct": row.get(
                    "risk_finalizer_same_decision_cluster_side_package_extra_slot_prior_risk_pct"
                ),
                "candidate_risk_pct": row.get(
                    "risk_finalizer_same_decision_cluster_side_package_extra_slot_candidate_risk_pct"
                ),
                "next_risk_pct": row.get(
                    "risk_finalizer_same_decision_cluster_side_package_extra_slot_next_risk_pct"
                ),
                "maximum_risk_pct": row.get(
                    "risk_finalizer_same_decision_cluster_side_package_extra_slot_max_risk_pct"
                ),
                "transfer_score": row.get(
                    "risk_finalizer_same_decision_cluster_side_package_extra_slot_transfer_score"
                ),
                "minimum_transfer_score": row.get(
                    "risk_finalizer_same_decision_cluster_side_package_extra_slot_min_transfer_score"
                ),
                "reason": row.get(
                    "risk_finalizer_same_decision_cluster_side_package_extra_slot_reason"
                ),
                "source_boundary": row.get(
                    "risk_finalizer_same_decision_cluster_side_package_extra_slot_source_boundary"
                ),
            }
            for row in selected_rows
            if row.get("risk_finalizer_same_decision_cluster_side_extra_slot_selected")
            is True
        ]
        out["windows"][month] = {
            "scorecard_windows": len(sm["scorecards"]),
            "selected_probe_count_distribution": counter_json(sm["selected_probe_count"]),
            "selected_probe_total": sum(
                count * windows for count, windows in sm["selected_probe_count"].items()
            ),
            "selected_probe_reconciles_order_accepts": (
                sum(count * windows for count, windows in sm["selected_probe_count"].items())
                == len(selected)
            ),
            "selected_windows": len(selected_windows),
            "multi_selected_windows": multi_selected,
            "maximum_selected_in_one_window": max(selected_by_window.values(), default=0),
            "selected_per_day": counter_json(selected_by_day),
            "maximum_selected_in_one_day": max(selected_by_day.values(), default=0),
            "scheduler_materialized": {
                "candidate_total": scan["stage_totals"]["scheduler_materialized"],
                "window_count": len(scheduler_windows),
                "windows_with_multiple_candidates": sum(
                    count > 1 for count in scheduler_by_window.values()
                ),
                "windows_with_candidates_but_no_selected_probe": len(
                    no_selected_scheduler_windows
                ),
            },
            "hard_eligible_bounds": {
                "candidate_total": [
                    len(selected),
                    scan["stage_totals"]["scheduler_materialized"],
                ],
                "eligible_window_count": [len(selected_windows), len(scheduler_windows)],
                "eligible_windows_without_selected_probe": [
                    0,
                    len(no_selected_scheduler_windows),
                ],
                "why_only_bounds": (
                    "selected candidates prove hard eligibility; scheduler materialized "
                    "candidates bound the superset. Exact in-memory hard flags were dropped."
                ),
            },
            "pass_reason_surrogate_falsification": {
                "surrogate_candidate_total": sum(pass_surrogate.values()) + len(selected),
                "surrogate_windows": len(set(pass_surrogate) | selected_windows),
                "surrogate_windows_without_selection": len(false_surrogate_windows),
                "conclusion": (
                    "The surrogate labels many no-selection windows and cannot be used "
                    "as the exact factorial hard-eligible bit."
                ),
            },
            "direct_competition_lower_bound": {
                "missed_rows_labeled_scheduler_selected_competing_candidate": sum(
                    direct_competition.values()
                ),
                "affected_windows": len(direct_competition),
                "semantics": (
                    "Exact observed competition after a selected candidate; not an exact "
                    "hard-cap bind count because the final hard pool was projected out."
                ),
            },
            "occupancy": {
                "open_pending_selected_cross": occupancy_table(sm["occupancy"]),
                "windows_with_open_positions": sum(
                    count
                    for (open_n, _pending_n, _selected_n), count in sm["occupancy"].items()
                    if open_n > 0
                ),
                "windows_with_pending_orders": sum(
                    count
                    for (_open_n, pending_n, _selected_n), count in sm["occupancy"].items()
                    if pending_n > 0
                ),
                "selected_windows_with_open_positions": sum(
                    count
                    for (open_n, _pending_n, selected_n), count in sm["occupancy"].items()
                    if open_n > 0 and selected_n > 0
                ),
                "selected_windows_with_pending_orders": sum(
                    count
                    for (_open_n, pending_n, selected_n), count in sm["occupancy"].items()
                    if pending_n > 0 and selected_n > 0
                ),
            },
            "selected_order_capacity_evidence": {
                "selected_rows": len(selected_rows),
                "daily_order_count_before": observed_numeric_summary(
                    selected_rows, "daily_accepted_risk_order_count_before"
                ),
                "daily_order_count_after": observed_numeric_summary(
                    selected_rows, "daily_accepted_risk_order_count_after"
                ),
                "daily_risk_pct_before": observed_numeric_summary(
                    selected_rows, "daily_accepted_risk_pct_before"
                ),
                "daily_risk_pct_after": observed_numeric_summary(
                    selected_rows, "daily_accepted_risk_pct_after"
                ),
                "daily_budget_exhausted_selected_rows": sum(
                    row.get("daily_risk_order_budget_exhausted") is True
                    for row in selected_rows
                ),
                "cluster_side_order_count_before": observed_numeric_summary(
                    selected_rows,
                    "same_decision_cluster_side_accepted_risk_order_count_before",
                ),
                "cluster_side_order_count_effective_after_pending_replacement": (
                    observed_numeric_summary(
                        selected_rows,
                        "same_decision_cluster_side_accepted_risk_order_count_effective_after_pending_replacement",
                    )
                ),
                "cluster_side_risk_pct_before": observed_numeric_summary(
                    selected_rows,
                    "same_decision_cluster_side_accepted_risk_pct_before",
                ),
                "cluster_side_cap_exhausted_selected_rows": sum(
                    row.get("same_decision_cluster_side_risk_order_cap_exhausted")
                    is True
                    for row in selected_rows
                ),
                "cluster_side_guard_blocked_selected_rows": sum(
                    row.get("same_decision_cluster_side_burst_guard_blocked") is True
                    for row in selected_rows
                ),
                "cluster_counts": counter_json(
                    collections.Counter(
                        str(
                            row.get("same_decision_cluster_side_risk_order_cluster")
                            or "unknown"
                        )
                        for row in selected_rows
                    )
                ),
                "open_risk_pct_before": observed_numeric_summary(
                    selected_rows, "open_risk_pct_before"
                ),
                "pending_risk_pct_before": observed_numeric_summary(
                    selected_rows, "pending_risk_pct_before"
                ),
                "selected_rows_with_pending_risk": sum(
                    (number(row.get("pending_risk_pct_before")) or 0.0) > 0.0
                    for row in selected_rows
                ),
                "finalizer_extra_slot_selected_rows": extra_slot_rows,
            },
            "exact_scorecard_stand_down_status": counter_json(sm["scorecard_status"]),
            "exact_zero_probe_stand_down_status": counter_json(zero_probe_status),
            "exact_positive_probe_status": counter_json(positive_probe_status),
            "exact_missed_finalizer_reasons": counter_json(scan["risk_finalizer_reason"]),
            "exact_scheduler_dispositions": counter_json(scan["scheduler_disposition"]),
            "one_position_per_window_verdict": (
                "NOT_A_STRICT_ONE_POSITION_CAP: the finalizer explicitly selected one "
                "January package extra-slot probe, yielding two same-cluster/side probes "
                "in one window within the configured count and risk ceilings. Exact "
                "frequency with which target count or hard headroom suppressed additional "
                "hard-eligible candidates is not identifiable from these projected scorecards."
            ),
        }
        if month == "february":
            out["windows"][month]["february_authority_census"] = scan[
                "february_authority"
            ]
    return out


def executed_family_row(rows: Sequence[Mapping[str, Any]], total: int) -> dict[str, Any]:
    scoreable = [row for row in rows if first_number(row, "net_r") is not None]
    net = [first_number(row, "net_r") for row in scoreable]
    gross = [first_number(row, "gross_r") for row in scoreable]
    costs = [
        first_number(row, "cost_r", "total_execution_cost_r", "expected_cost_r")
        for row in rows
    ]
    net_values = [value for value in net if value is not None]
    gross_values = [value for value in gross if value is not None]
    cost_values = [value for value in costs if value is not None]
    wins = sum(value > 0.0 for value in net_values)
    return {
        "n": len(rows),
        "share_of_executed": round(len(rows) / total, 12) if total else None,
        "scoreable_n": len(net_values),
        "unscoreable_n": len(rows) - len(net_values),
        "gross_r_sum": round(sum(gross_values), 8),
        "net_r_sum": round(sum(net_values), 8),
        "cost_r_sum_all_rows": round(sum(cost_values), 8),
        "net_r_mean": round(sum(net_values) / len(net_values), 8) if net_values else None,
        "wins": wins,
        "win_share": round(wins / len(net_values), 8) if net_values else None,
        "win_share_wilson_95ci": wilson_interval(wins, len(net_values)),
    }


def build_executed_family_table(
    small: Mapping[str, Mapping[str, Any]],
) -> dict[str, Any]:
    out: dict[str, Any] = {
        "schema": "gtos.wave19.session_ff.executed_family_table.v1",
        "authority": "raw TRADE_LEDGER physical rows joined by composite identity",
        "windows": {},
    }
    for month in ("january", "february"):
        rows = list(small[month]["trades"].values())
        groups: dict[str, list[dict[str, Any]]] = collections.defaultdict(list)
        for row in rows:
            groups[family(row)].append(row)
        table = {
            fam: executed_family_row(group, len(rows))
            for fam, group in sorted(groups.items())
        }
        total = executed_family_row(rows, len(rows))
        out["windows"][month] = {
            "trade_rows": len(rows),
            "families": table,
            "total": total,
            "family_count_sum": sum(row["n"] for row in table.values()),
            "family_count_reconciles": sum(row["n"] for row in table.values()) == len(rows),
        }
    out["crosscheck"] = {
        "january_current_fvg_fill_n": out["windows"]["january"]["families"][FVG]["n"],
        "february_current_fvg_fill_n": out["windows"]["february"]["families"][FVG]["n"],
        "expected_exact_counts": {"january": 21, "february": 42},
    }
    return out


def write_json(path: Path, payload: Mapping[str, Any]) -> None:
    path.write_text(json.dumps(payload, indent=1, sort_keys=True, default=str) + "\n")


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        while True:
            block = handle.read(1024 * 1024)
            if not block:
                break
            digest.update(block)
    return digest.hexdigest()


def main() -> None:
    small: dict[str, dict[str, Any]] = {}
    scans: dict[str, dict[str, Any]] = {}
    pools: dict[str, dict[str, Any]] = {}
    for month, spec in WINDOWS.items():
        small[month] = load_small_ledgers(month, spec)
        scans[month] = scan_full_missed(month, spec, small[month]["accepted"])
        pools[month] = scan_scoreable_pool(month, spec)

        if scans[month]["stage_totals"]["pool"] != small[month]["scorecard_candidate_sum"]:
            raise AssertionError(f"pool/scorecard denominator mismatch: {month}")
        diagnostic_scoreable = scans[month]["scoreability"][
            "diagnostic_opportunity_r_scoreable"
        ]
        if diagnostic_scoreable != pools[month]["rows"]:
            raise AssertionError(
                f"compact scoreable pool mismatch {month}: "
                f"{diagnostic_scoreable} != {pools[month]['rows']}"
            )

    outputs = {
        "FVG_ENRICHMENT.json": build_enrichment(scans, small),
        "FAMILY_TENSION.json": build_family_tension(pools, small),
        "PROBE_CONVERSION.json": build_probe_conversion(small),
        "CAPACITY_CENSUS.json": build_capacity(scans, small),
        "EXECUTED_FAMILY_TABLE.json": build_executed_family_table(small),
    }
    for name, payload in outputs.items():
        write_json(OUT / name, payload)

    manifest_path = OUT / "LOOK_MANIFEST.json"
    manifest = json.loads(manifest_path.read_text())
    manifest["analysis_status"] = "COMPLETE_ATTRIBUTION_NO_PROMOTION"
    manifest["source_inventory"] = [
        tracker.receipt()
        for _key, tracker in sorted(SOURCE_TRACKERS.items())
    ]
    manifest["denominator_checks"] = {
        month: {
            "pool_rows": scans[month]["stage_totals"]["pool"],
            "scorecard_candidate_sum": small[month]["scorecard_candidate_sum"],
            "scheduler_materialized_rows": scans[month]["stage_totals"][
                "scheduler_materialized"
            ],
            "scorecard_all_options_preserved_sum": small[month][
                "scorecard_all_options_preserved_sum"
            ],
            "scorecard_order_executable_probe_sum": small[month][
                "scorecard_order_executable_probe_sum"
            ],
            "selected_probes": len(small[month]["accepted"]),
            "filled_trades": len(small[month]["trades"]),
            "compact_scoreable_pool_rows": pools[month]["rows"],
        }
        for month in ("january", "february")
    }
    manifest["hard_eligibility_status"] = (
        "NOT_IDENTIFIABLE_FROM_EXISTING_PROJECTED_ARMS_"
        "REPAIR_IMPLEMENTED_DEFAULT_OFF_NOT_BACKFILLED"
    )
    manifest["outputs"] = {
        name: {
            "path": str(OUT / name),
            "bytes": (OUT / name).stat().st_size,
            "sha256": sha256_file(OUT / name),
        }
        for name in outputs
    }
    write_json(manifest_path, manifest)

    print(
        json.dumps(
            {
                "status": manifest["analysis_status"],
                "denominators": manifest["denominator_checks"],
                "output_files": sorted(outputs),
            },
            indent=1,
        )
    )


if __name__ == "__main__":
    main()
