"""Session BB — append this session's repair rows to the append-only queue.

    python3 docs/audits/fable5-vision-audit-20260725/phase13/receipts/bb_repair_rows.py
    ... --dry-run

Append-only and union-merged at the train (agreement §3). Every figure is READ from a
committed artifact rather than transcribed, and the script dies if an artifact is missing —
a repair row quoting a number nobody can reproduce is worse than no row.
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
from pathlib import Path

REPO = Path(__file__).resolve().parents[5]
HERE = Path(__file__).resolve().parent
P6 = REPO / "docs/audits/fable5-vision-audit-20260725/phase6/receipts"
QUEUE = P6 / "REPAIR_QUEUE_APPEND.jsonl"

FILL = HERE / "BB_FILL_TRUTH_V1.json"
RANK = HERE / "BB_SUPPLY_RANK_V1.json"
ADV = HERE / "BB_ADVERSARIAL_V1.json"


def load(p: Path) -> dict:
    if not p.is_file():
        raise SystemExit(f"missing artifact {p.relative_to(REPO)} — run its driver first")
    return json.loads(p.read_text(encoding="utf-8"))


def rows() -> list[dict]:
    f, r, a = load(FILL), load(RANK), load(ADV)
    now = dt.datetime.now(dt.timezone.utc).isoformat()
    occ = f["occupancy_armed_four"]
    cad = f["cadence"]["book"]
    out: list[dict] = []

    def row(**kw):
        out.append({"appended_utc": now, "session": "BB", **kw})

    row(
        priority="HIGH",
        component="mc_firm_rules / recost_w7_validation — the calendar clock",
        finding=("every published `median_calendar_days_to_pass` and `%/mo` divides by (or "
                 "multiplies by) a book-day count built from a per-sleeve day sum with NO "
                 "placement guard, and the live path holds one open position per broker "
                 "symbol across the whole book. On the armed four's archive walk the "
                 "correction is 1.333x."),
        action=("re-derive `book_days` per MC variant by running recost_w7_validation's "
                "cached trades through walkforward.book_replay's placement gates, then "
                "restate BOOKS_MC_V1's calendar columns. Arithmetic on committed caches, no "
                "new data. DIRECTION is certain; MAGNITUDE on the W7 cache population is "
                "NOT what BB measured — do not transfer 1.333x as a factor."),
        evidence={
            "source": "BB_FILL_TRUTH_V1.json, BB_ADVERSARIAL_V1.json::A5_calendar_claim_scope",
            "archive_book_day_density": cad["archive"]["FULL_SURFACE_book_day_density"],
            "live_book_day_density": cad["live_equivalent"]["FULL_SURFACE_book_day_density"],
            "ratio_on_the_archive_walk": a["A5_calendar_claim_scope"]["measured_here"]["ratio"],
            "divisor_site": "scripts/mc_firm_rules.py:622-624 and :417",
            "guard_sites": "book_owner.py:1727-1735, :1793-1802, :1807-1811, :1823-1850",
        },
        cost="~0.25 session",
    )

    row(
        priority="HIGH",
        component="research labelling — every per-sleeve fill/frequency figure",
        finding=("archive DECISION counts are not fills. The armed four's 869 archive "
                 "decisions are 590 live-equivalent fills; `sub_xvol_pullback` — the "
                 "highest per-trade gross R in the book — loses 60.2 % and fires about "
                 "five times a year live."),
        action=("stamp every per-sleeve frequency claim with whether it is a DECISION count "
                "or a FILL count. `walkforward.book_replay` already models the gates; the "
                "missing piece was applying it to cadence, which BB_FILL_TRUTH_V1.json now "
                "does for the armed set and `bb_supply_rank.py --stage fire` does for any "
                "candidate."),
        evidence={
            "source": "BB_FILL_TRUTH_V1.json",
            "book": {"archive_decisions": occ["n_archive_decisions"],
                     "live_equivalent_fills": occ["n_live_equivalent_fills"],
                     "suppression_frac": occ["suppression_frac"],
                     "by_reason": occ["suppressed_by_reason"]},
            "per_sleeve_suppression": {s: v["suppression_frac"]
                                       for s, v in occ["per_sleeve"].items()},
            "cross_validated_by": ("walkforward.book_replay.replay_book — 579=579 full "
                                   "archive, 115=115 full-surface window"),
        },
        cost="done",
    )

    fire = r["fire_rate"]["candidates"].get("ny_index_momentum") or {}
    mid = r["gate_at_ratified_rule"]["arms"]["mid"]["verdicts"].get("ny_index_momentum") or {}
    row(
        priority="MEDIUM",
        component="sleeves/registry.py — the LIVE_WIRING_GAP, priced",
        finding=("`ny_index_momentum` is the estate's only candidate that adds material "
                 "cadence AND is not negative at the ratified rule, and it cannot reach a "
                 "book at all: the production sizer fails closed on `unknown_sleeve` for "
                 "every one of its candidates."),
        action=("AK's REGISTRY_EDIT_PROPOSAL is the edit (one SleeveSpec). It is an "
                "owner decision and this row is NOT a recommendation to arm — the sleeve "
                "fails `significance` at the ratified rule. Registry-edit safe order per "
                "AK: confidence weight first, spec second."),
        evidence={
            "source": "BB_SUPPLY_RANK_V1.json",
            "marginal_fills_per_week": fire.get("MARGINAL_fills_per_week"),
            "armed_four_fills_per_week": r["fire_rate"]["armed_four_baseline"]["fills_per_week"],
            "oos_mean_r_per_day_RECORDED_mid": mid.get("pooled_oos_mean_r"),
            "p_raw": mid.get("p_raw"), "verdict": mid.get("verdict"),
            "failing_core_gates": mid.get("failing_core_gates"),
            "placed_through_the_production_sizer": 0,
            "sizer_reason": "unit:fail_closed:unknown_sleeve:ny_index_momentum",
        },
        cost="one line + the owner decision",
    )

    a2 = a["A2_cost_vs_edge"]
    row(
        priority="MEDIUM",
        component="cost geometry — Session AY's lane",
        finding=("the high-supply candidates' deficit does not survive as a PER-DECISION "
                 "effect. Spearman(marginal fills/week, OOS R/day) is -0.214 (p 0.267) and "
                 "the per-trade restatement is +0.015 (p 0.938), so what looks like 'the "
                 "fast sleeves have no edge' is at least partly 'a per-DAY expectancy "
                 "charges frequency times cost'."),
        action=("re-price the top marginal suppliers at AY's repaired spread/era geometry "
                "before concluding the estate has no affordable cadence. This corrects "
                "BB's own first-draft claim of an estate-wide anti-correlation."),
        evidence={
            "source": "BB_ADVERSARIAL_V1.json::A2_cost_vs_edge",
            "n_candidates": a2["n_candidates"],
            "spearman_per_day": a2["spearman_marginal_fills_vs_oos_r_per_DAY"],
            "spearman_per_trade_lower_bound":
                a2["spearman_marginal_fills_vs_oos_r_per_TRADE_lower_bound"],
        },
        cost="inside AY",
    )

    q = f["quiet_alarm"]
    row(
        priority="LOW",
        component="telemetry / command center (Session BC)",
        finding=("`CANARY_OPERATOR_PAGE.md` says long silences are normal without saying "
                 "how long normal is, so the operator has no threshold to act on."),
        action=("adopt `scripts/book_silence_check.py` — warn at 15 silent WEEKDAY "
                "sessions, alert at 22, thresholds read from the receipt at run time. "
                "Re-run bb_fill_truth.py whenever --tags changes: the thresholds are a "
                "property of the armed SET."),
        evidence={
            "source": "BB_FILL_TRUTH_V1.json::quiet_alarm",
            "recommendation": q["RECOMMENDATION"],
            "measured_window": q["window"],
            "book_days": q["book_days"], "max_observed_gap": q["gap_sessions"]["max"],
            "limit": ("the p99 sits one session beyond the archive's maximum observed gap; "
                      "it is not a well-estimated 99th percentile and the tool says so"),
        },
        cost="done — importable, tested, default-inert",
    )
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    a = ap.parse_args()
    rs = rows()
    before = sum(1 for _ in QUEUE.open(encoding="utf-8")) if QUEUE.is_file() else 0
    if not a.dry_run:
        with QUEUE.open("a", encoding="utf-8") as fh:
            for r in rs:
                fh.write(json.dumps(r, sort_keys=True) + "\n")
    print(f"{'would append' if a.dry_run else 'appended'} {len(rs)} row(s); "
          f"queue {before} -> {before + (0 if a.dry_run else len(rs))}")
    for r in rs:
        print(f"  [{r['priority']:6s}] {r['component']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
