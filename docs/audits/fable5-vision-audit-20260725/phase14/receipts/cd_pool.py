"""Session CD -- stream a regenerated MISSED_OPPORTUNITY ledger into a poolable artifact.

Why this exists rather than `b7_5_diagnostic_pool`: that reader resolves the
SEALED arms through the route's cold-evidence resolver and is bound to their
paths. A regenerated arm lives in this worktree's own namespace, is plain JSONL,
and -- the operative constraint -- is **~8 GB per month arm**, which cannot stay
on disk while three more arms run. So this streams the ledger once, emits

  * the AW-comparable aggregate (`pool_summary`-shaped, plus the cost
    decomposition and the loss-concentration table), and
  * a compact per-row `*.jsonl.gz` carrying the declared column set,

after which the 8 GB route can be deleted and the pool is still mineable.

The column set is `b7_5_diagnostic_pool.FEATURE_FIELDS` plus the identity and
outcome columns, so anything AW's mine could ask of the sealed pool can be asked
of this one. Session CK found that the original compact projection discarded the
terminal/path provenance required for a geometry autopsy after the raw ledgers were
deleted. The scalar oracle fields and content-bound source pointer are now retained too;
the source path remains external rather than embedding every M1/tick row in the pool.
Fields are read through the same `_dig` dotted-path helper, so
`candidate_decision_quality.execution_fill_probability` resolves identically.

The cost decomposition is the point of the exercise. F38 says `commission_r` is
identically zero on the sealed pool; a regenerated arm under
`commission_broker_true` must show a non-zero column, and the size of that column
IS the repair's effect.
"""

from __future__ import annotations

import argparse
import gzip
import json
import math
import sys
from pathlib import Path
from typing import Any, Iterator

REPO = Path(__file__).resolve().parents[5]
sys.path.insert(0, str(REPO))

from src.research_infra import b7_5_diagnostic_pool as DP  # noqa: E402
from src.research_infra.train_engine import decision_semantics as SEM  # noqa: E402

#: Columns kept in the compact artifact, beyond the mine's own feature list.
EXTRA_COLUMNS = (
    "candidate_id",
    "symbol",
    "decision_time_utc",
    "opportunity_net_proxy_r",
    "missed_opportunity_r_scoreability_status",
    "missed_opportunity_non_executable_diagnostic_scoreable",
    "cost_r",
    "expected_cost_r",
    "spread_r",
    "commission_r",
    "swap_cost_r",
    "expected_slippage_r",
    "commission_r_broker_true_measured",
    "commission_r_repair_status",
    "swap_horizon_repair_status",
    "broker_pretrade_cost_executable",
    "pretrade_cost_packet_status",
    "entry_price",
    "stop_loss",
    "side",
    "final_blocker_class",
    "miss_reason",
    "selector_reason",
    # CK projection-contract repair: keep enough oracle state to measure first-touch
    # ambiguity and to content-bind a zero-replay path sidecar after raw-ledger deletion.
    "raw_gross_r",
    "raw_net_proxy_r",
    "raw_opportunity_close_reason",
    "policy_gross_r",
    "opportunity_gross_r",
    "opportunity_close_reason",
    "terminal_outcome",
    "counterfactual_order_close_time_utc",
    "target_first_touch_utc",
    "stop_first_touch_utc",
    "same_bar_ambiguity",
    "ambiguity_resolution",
    "terminal_r_diagnostic_outcome",
    "terminal_r_diagnostic_gross_r",
    "terminal_r_diagnostic_close_reason",
    "terminal_r_diagnostic_target_r",
    "path_source",
    "path_source_timeframe",
    "path_index_source_path",
    "path_index_source_sha256",
    "path_index_rows_returned",
    "path_row_count",
    "ordered_tick_truth_satisfied",
    *sorted(SEM.SEMANTIC_FIELDS),
)

#: Cost bands the loss-concentration table reports. AW's headline is the first.
COST_TAIL_BANDS = (1.0, 2.0, 5.0)


def _num(value: Any) -> float | None:
    try:
        out = float(value)
    except (TypeError, ValueError):
        return None
    return None if math.isnan(out) else out


def _is_scoreable(row: dict[str, Any]) -> bool:
    return bool(
        row.get("missed_opportunity_non_executable_diagnostic_scoreable") is True
        or str(row.get("missed_opportunity_r_scoreability_status") or "")
        == "diagnostic_opportunity_r_scoreable"
    )


#: Column renames when the rows come from AW's sealed reader rather than from a
#: raw regenerated ledger. `b7_5_diagnostic_pool.project()` names the outcome
#: `outcome_net_proxy_r`; a raw ledger row calls it `opportunity_net_proxy_r`.
#: Everything else this module reads is already named the same on both sides,
#: which is not a coincidence -- `cd_pool.EXTRA_COLUMNS` was built from that
#: reader's field list.
SEALED_RENAMES = {"outcome_net_proxy_r": "opportunity_net_proxy_r"}


def stream_sealed_arm(arm_id: str) -> Iterator[dict[str, Any]]:
    """Stream a SEALED arm of record through AW's reader, shaped like a raw row.

    This is what makes the frozen column of CD-3's delta table the sealed
    ARTIFACT rather than a re-run of it. The reader resolves the cold zstd
    shards in place through the route's own `RawOrColdResolver`, verifies each
    shard's hash as it inflates it, and copies nothing (H4).

    Every row it yields is already diagnostic-scoreable by construction -- the
    reader filters -- so the scoreability flag is stamped on rather than read,
    and `summarise` counts the same population on both sides.
    """

    from src.research_infra import b7_5_diagnostic_pool as pool

    spec = pool.ARMS[arm_id]
    for row in pool.iter_arm_rows(spec):
        out = dict(row)
        for old, new in SEALED_RENAMES.items():
            if old in out:
                out[new] = out.pop(old)
        out["missed_opportunity_non_executable_diagnostic_scoreable"] = True
        yield out


def stream_rows(path: Path) -> Iterator[dict[str, Any]]:
    opener = gzip.open if str(path).endswith(".gz") else open
    with opener(path, "rt", encoding="utf-8") as handle:  # type: ignore[operator]
        for line in handle:
            line = line.strip()
            if line:
                yield json.loads(line)


def project(row: dict[str, Any]) -> dict[str, Any]:
    """Raw ledger row -> compact pool row.

    A row that has ALREADY been projected (the `--sealed-arm` path streams
    through `b7_5_diagnostic_pool.project`) carries every field flat at the top
    level, so re-digging a dotted source on it would resolve `None` and quietly
    blank three columns that are sitting right there. Prefer the flat value when
    it exists; dig only when it does not.
    """

    row = SEM.normalize_evidence_row(row)
    out: dict[str, Any] = {}
    for field in DP.FEATURE_FIELDS:
        if field.source.startswith("derived:"):
            continue
        out[field.name] = (
            row[field.name] if field.name in row else DP._dig(row, field.source)
        )
    for name in EXTRA_COLUMNS:
        out.setdefault(name, row.get(name))
    # Regenerated missed-opportunity ledgers call this identity field
    # ``direction`` while the compact contract calls it ``side``.  Preserve the
    # canonical LONG/SHORT value instead of emitting a reader-incomplete null.
    if out.get("side") in (None, ""):
        direction = str(out.get("direction") or "").upper()
        if direction in {"LONG", "SHORT"}:
            out["side"] = direction
    return out


def summarise(
    path: Path,
    compact_out: Path | None,
    *,
    sealed_arm: str = "",
    limit: int = 0,
) -> dict[str, Any]:
    n_rows = 0
    scoreable = 0
    pos = neg = flat = 0
    pos_r = neg_r = 0.0
    unreadable = 0
    cost_sum = 0.0
    cost_n = 0
    authoritative_cost_sum = 0.0
    authoritative_cost_n = 0
    non_authoritative_legacy_fallback_rows = 0
    component_sums: dict[str, float] = {}
    component_n: dict[str, int] = {}
    tail_rows = {band: 0 for band in COST_TAIL_BANDS}
    tail_net = {band: 0.0 for band in COST_TAIL_BANDS}
    max_cost = 0.0
    gross_sum = 0.0
    gross_n = 0
    exact_endpoint_stop = exact_endpoint_target = 0
    terminal_outcome_stop = terminal_outcome_target = 0
    by_symbol: dict[str, dict[str, float]] = {}
    by_day: dict[str, dict[str, float]] = {}
    executable = {"true": 0, "false": 0, "unknown": 0}

    source = stream_sealed_arm(sealed_arm) if sealed_arm else stream_rows(path)
    handle = gzip.open(compact_out, "wt", encoding="utf-8") if compact_out else None
    try:
        for row in source:
            n_rows += 1
            if limit and n_rows > limit:
                n_rows -= 1
                break
            row = SEM.normalize_evidence_row(row)
            if not _is_scoreable(row):
                continue
            scoreable += 1
            if handle is not None:
                handle.write(json.dumps(project(row), default=str) + "\n")

            net = _num(row.get("opportunity_net_proxy_r"))
            if net is None:
                unreadable += 1
                continue
            if net > 0:
                pos += 1
                pos_r += net
            elif net < 0:
                neg += 1
                neg_r += net
            else:
                flat += 1

            cost = _num(row.get("recorded_cost_r"))
            if cost is None:
                cost = _num(row.get("cost_r"))
            if cost is not None:
                cost_sum += cost
                cost_n += 1
                max_cost = max(max_cost, cost)
                for band in COST_TAIL_BANDS:
                    if cost > band:
                        tail_rows[band] += 1
                        tail_net[band] += net
                gross = net + cost
                gross_sum += gross
                gross_n += 1
                if abs(gross + 1.0) < 1e-9:
                    exact_endpoint_stop += 1
                elif abs(gross - 2.0) < 1e-9:
                    exact_endpoint_target += 1

            authoritative_cost = _num(row.get("authoritative_cost_r"))
            if authoritative_cost is not None:
                authoritative_cost_sum += authoritative_cost
                authoritative_cost_n += 1
            if row.get("legacy_emitter_fallback_cost_r") is not None:
                non_authoritative_legacy_fallback_rows += 1

            terminal_outcome = str(row.get("terminal_outcome") or "")
            if terminal_outcome == "stop_reached_before_target":
                terminal_outcome_stop += 1
            elif terminal_outcome == "target_reached_before_stop":
                terminal_outcome_target += 1

            for name in (
                "spread_r",
                "commission_r",
                "swap_cost_r",
                "expected_slippage_r",
                "commission_r_broker_true_measured",
            ):
                value = _num(row.get(name))
                if value is not None:
                    component_sums[name] = component_sums.get(name, 0.0) + value
                    component_n[name] = component_n.get(name, 0) + 1

            symbol = str(row.get("symbol") or "")
            bucket = by_symbol.setdefault(symbol, {"n": 0, "net_r": 0.0, "cost_r": 0.0})
            bucket["n"] += 1
            bucket["net_r"] += net
            if cost is not None:
                bucket["cost_r"] += cost

            day = str(row.get("decision_time_utc") or "")[:10]
            dbucket = by_day.setdefault(day, {"n": 0, "net_r": 0.0})
            dbucket["n"] += 1
            dbucket["net_r"] += net

            flag = row.get("broker_pretrade_cost_executable")
            executable["true" if flag is True else "false" if flag is False else "unknown"] += 1
    finally:
        if handle is not None:
            handle.close()

    net_total = pos_r + neg_r
    mean_winner = pos_r / pos if pos else 0.0
    mean_loser = neg_r / neg if neg else 0.0
    denom = mean_winner - mean_loser
    return {
        "schema": "gtos.session_cd.pool_summary.v2",
        "source": ("sealed_arm:" + sealed_arm) if sealed_arm else "regenerated_ledger",
        "row_limit_applied": limit or None,
        "sealed_reader_note": (
            "rows streamed through b7_5_diagnostic_pool.iter_arm_rows, which yields "
            "only diagnostic-scoreable rows, so `rows` here is the SCOREABLE count "
            "and not the physical ledger row count"
        ) if sealed_arm else "",
        "ledger": str(path),
        "compact_artifact": str(compact_out) if compact_out else None,
        "rows": n_rows,
        "diagnostic_scoreable_rows": scoreable,
        "unreadable_proxy_rows": unreadable,
        "positive_rows": pos,
        "negative_rows": neg,
        "flat_rows": flat,
        "positive_net_r": round(pos_r, 8),
        "negative_net_r": round(neg_r, 8),
        "net_r": round(net_total, 8),
        "mean_r_per_row": round(net_total / scoreable, 8) if scoreable else None,
        "base_rate_positive": round(pos / scoreable, 6) if scoreable else None,
        "mean_winner_r": round(mean_winner, 8),
        "mean_loser_r": round(mean_loser, 8),
        # AW's bar: the precision a selector must reach before it earns one R.
        "breakeven_precision": round(-mean_loser / denom, 6) if denom else None,
        "gross": {
            "mean_gross_r": round(gross_sum / gross_n, 8) if gross_n else None,
            "n": gross_n,
            "exact_contract_endpoint_population": {
                "definition": (
                    "scoreable rows whose recorded gross proxy, calculated as "
                    "opportunity_net_proxy_r + recorded_cost_r, equals exactly "
                    "-1R or +2R within 1e-9"
                ),
                "n_stop": exact_endpoint_stop,
                "n_target": exact_endpoint_target,
                "hit_rate": (
                    round(
                        exact_endpoint_target
                        / (exact_endpoint_stop + exact_endpoint_target),
                        6,
                    )
                    if (exact_endpoint_stop + exact_endpoint_target)
                    else None
                ),
                "breakeven_hit_rate": round(1 / 3, 6),
            },
            "terminal_outcome_first_touch_population": {
                "definition": (
                    "scoreable rows classified by the recorded terminal_outcome "
                    "first-touch label, regardless of the realized gross proxy"
                ),
                "n_stop": terminal_outcome_stop,
                "n_target": terminal_outcome_target,
                "hit_rate": (
                    round(
                        terminal_outcome_target
                        / (terminal_outcome_stop + terminal_outcome_target),
                        6,
                    )
                    if (terminal_outcome_stop + terminal_outcome_target)
                    else None
                ),
                "breakeven_hit_rate": None,
            },
            "binary_population": {
                "deprecated_alias_of": "exact_contract_endpoint_population",
                "n_stop": exact_endpoint_stop,
                "n_target": exact_endpoint_target,
                "hit_rate": (
                    round(
                        exact_endpoint_target
                        / (exact_endpoint_stop + exact_endpoint_target),
                        6,
                    )
                    if (exact_endpoint_stop + exact_endpoint_target)
                    else None
                ),
                "breakeven_hit_rate": round(1 / 3, 6),
            },
        },
        "cost": {
            "mean_cost_r": round(cost_sum / cost_n, 8) if cost_n else None,
            "n": cost_n,
            "mean_cost_r_semantics": "recorded emitter value; may be non-authoritative",
            "recorded_mean_cost_r": round(cost_sum / cost_n, 8) if cost_n else None,
            "recorded_n": cost_n,
            "authoritative_mean_cost_r": (
                round(authoritative_cost_sum / authoritative_cost_n, 8)
                if authoritative_cost_n
                else None
            ),
            "authoritative_n": authoritative_cost_n,
            "non_authoritative_legacy_fallback_rows": (
                non_authoritative_legacy_fallback_rows
            ),
            "max_cost_r": round(max_cost, 6),
            "components_mean_r": {
                name: round(total / component_n[name], 8)
                for name, total in sorted(component_sums.items())
            },
            "components_n": dict(sorted(component_n.items())),
        },
        "loss_concentration": {
            "note": (
                "cost_r is the packet's total_cost_r (spread + slippage + swap, "
                "plus commission when the repair is on). A cost above 1 R means "
                "the proposed stop is narrower than the round-trip cost."
            ),
            "bands": {
                str(band): {
                    "rows": tail_rows[band],
                    "row_share": (
                        round(tail_rows[band] / scoreable, 6) if scoreable else None
                    ),
                    "net_r_in_band": round(tail_net[band], 4),
                    "share_of_pool_net_r": (
                        round(tail_net[band] / net_total, 6) if net_total else None
                    ),
                    "pool_net_r_without_band": round(net_total - tail_net[band], 4),
                    "mean_r_without_band": (
                        round(
                            (net_total - tail_net[band])
                            / max(scoreable - tail_rows[band], 1),
                            8,
                        )
                    ),
                }
                for band in COST_TAIL_BANDS
            },
        },
        "broker_pretrade_cost_executable": executable,
        "by_symbol": {
            symbol: {
                "n": int(row["n"]),
                "mean_net_r": round(row["net_r"] / row["n"], 6),
                "mean_cost_r": round(row["cost_r"] / row["n"], 6),
            }
            for symbol, row in sorted(by_symbol.items(), key=lambda kv: -kv[1]["n"])
        },
        "by_day": {
            day: {"n": int(row["n"]), "mean_net_r": round(row["net_r"] / row["n"], 6)}
            for day, row in sorted(by_day.items())
        },
        "n_days_negative": sum(1 for row in by_day.values() if row["net_r"] < 0),
        "n_days": len(by_day),
    }


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--ledger", default="")
    ap.add_argument(
        "--sealed-arm",
        default="",
        help="read a SEALED arm of record (S0R0/S1R0/S0R1/S1R1) through AW's reader "
             "instead of a regenerated ledger",
    )
    ap.add_argument("--limit", type=int, default=0, help="stop after N rows (smoke only)")
    ap.add_argument("--compact", default="", help="write a projected jsonl.gz here")
    ap.add_argument("--out", required=True)
    ap.add_argument("--label", default="")
    ns = ap.parse_args()

    if not ns.ledger and not ns.sealed_arm:
        ap.error("pass --ledger or --sealed-arm")
    summary = summarise(
        Path(ns.ledger) if ns.ledger else Path("."),
        Path(ns.compact) if ns.compact else None,
        sealed_arm=ns.sealed_arm,
        limit=ns.limit,
    )
    summary["label"] = ns.label
    Path(ns.out).write_text(json.dumps(summary, indent=1, default=str))
    print(
        json.dumps(
            {
                "label": ns.label,
                "scoreable": summary["diagnostic_scoreable_rows"],
                "net_r": summary["net_r"],
                "mean_r_per_row": summary["mean_r_per_row"],
                "base_rate": summary["base_rate_positive"],
                "breakeven_precision": summary["breakeven_precision"],
                "mean_cost_r": summary["cost"]["mean_cost_r"],
                "components": summary["cost"]["components_mean_r"],
                "gross": summary["gross"]["mean_gross_r"],
                "tail_1r": summary["loss_concentration"]["bands"]["1.0"],
            },
            indent=1,
            default=str,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
