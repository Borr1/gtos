"""A4 Stage 2.5 — build the realized-R join CSV from cohort manifest.

For each of the 11 cohort records, derive realized_r and outcome from the
appropriate data source (trade_record final_outcome, M1 fill simulation,
or WAVE1_R2_REPORT cross-reference).

Output: a4_realized_r_join.csv
"""

from __future__ import annotations

import csv
import json
from datetime import datetime
from pathlib import Path

REPO = Path(r"C:\Users\MSI\Documents\ai-trading-agent")
OUT_DIR = REPO / ".claude" / "worktrees" / "agent-ae5e6ce714eaff374" / "research" / "a4_trending_bull_replay_2026-04-28"
COHORT_MANIFEST = REPO / ".claude" / "worktrees" / "agent-a3b7a108632e7293d" / "research" / "a4_trending_bull_replay_2026-04-28" / "a4_cohort_manifest.csv"
TRADE_RECORDS = REPO / "knowledge_base" / "trade_records" / "XAUUSD"

# Load M1 fill sim results
SIM_RESULTS = OUT_DIR / "fill_simulation_m1_results.json"

# Outcome bands
def outcome_label(r):
    if r is None:
        return "UNKNOWN"
    if abs(r) <= 0.05:
        return "BE"
    if r > 0.05:
        return "WIN"
    return "LOSS"


def main():
    with open(SIM_RESULTS, encoding="utf-8") as fh:
        sim = json.load(fh)

    rows = []
    with open(COHORT_MANIFEST, encoding="utf-8") as fh:
        rdr = csv.DictReader(fh)
        for rec in rdr:
            tid = rec["trade_id"]
            candle_time = rec["candle_time_utc"]
            mso_path = rec["mso_path"]

            # Load the trade record JSON to read final_outcome.
            trade_record = TRADE_RECORDS / f"{tid}.json"
            if not trade_record.exists():
                rows.append({
                    "trade_id": tid,
                    "candle_time_utc": candle_time,
                    "realized_r": "",
                    "outcome": "UNKNOWN",
                    "r_source": "no_trade_record_file",
                    "notes": f"trade record file not found: {trade_record}",
                })
                continue

            with open(trade_record, encoding="utf-8") as f:
                td = json.load(f)
            final_outcome = td.get("decision_pipeline", {}).get("final_outcome")
            execution = td.get("execution")

            if final_outcome == "REJECTED_L2":
                rows.append({
                    "trade_id": tid,
                    "candle_time_utc": candle_time,
                    "realized_r": "",
                    "outcome": "NEVER_FILLED",
                    "r_source": "trade_record_pipeline_rejected_l2",
                    "notes": f"Pipeline rejected at L2 (sl_beyond_ob); no order placed by GTOS.",
                })
            elif final_outcome == "REJECTED_GATE1_SAFETY":
                rows.append({
                    "trade_id": tid,
                    "candle_time_utc": candle_time,
                    "realized_r": "",
                    "outcome": "NEVER_FILLED",
                    "r_source": "trade_record_pipeline_rejected_gate1",
                    "notes": f"Pipeline rejected at Gate1 safety; no order placed by GTOS.",
                })
            elif final_outcome == "LIMIT_PLACED":
                # Use M1 fill sim
                if tid not in sim:
                    rows.append({
                        "trade_id": tid,
                        "candle_time_utc": candle_time,
                        "realized_r": "",
                        "outcome": "UNKNOWN",
                        "r_source": "no_sim_data",
                        "notes": "LIMIT_PLACED but no M1 sim result",
                    })
                    continue

                s = sim[tid]
                outcome = s.get("outcome")
                rr = s.get("realized_r")
                if outcome == "NEVER_FILLED":
                    rows.append({
                        "trade_id": tid,
                        "candle_time_utc": candle_time,
                        "realized_r": "",
                        "outcome": "NEVER_FILLED",
                        "r_source": "m1_fill_sim_2026-04-28",
                        "notes": "Limit placed but never touched in 192 M15 (48h) window",
                    })
                else:
                    base_label = "WIN" if outcome == "FILLED_WIN" else ("LOSS" if outcome == "FILLED_LOSS" else outcome_label(rr))
                    note_extra = ""
                    if tid == "2026-04-16_ny_1316":
                        # Cross-reference WAVE1_R2_REPORT
                        note_extra = (
                            " Cross-reference WAVE1_R2_REPORT.md sec 3.5: live broker reported "
                            "fill 04-17 01:00 → -1R; M1 forward-replay also reports -1R via "
                            "earlier 04-16 16:52 fill (intra-bar timing differs but R outcome same)."
                        )
                    rows.append({
                        "trade_id": tid,
                        "candle_time_utc": candle_time,
                        "realized_r": f"{rr:.4f}" if rr is not None else "",
                        "outcome": base_label,
                        "r_source": "m1_fill_sim_2026-04-28" + (" + WAVE1_R2_REPORT" if tid == "2026-04-16_ny_1316" else ""),
                        "notes": f"M1 forward-replay: filled {s.get('fill_time')}@{s.get('fill_price')}, "
                                 f"exit {s.get('exit_time')}@{s.get('exit_price')} ({s.get('exit_reason')})." + note_extra,
                    })
            else:
                # Some other final_outcome (e.g. EXECUTED, but execution is null in cohort)
                rows.append({
                    "trade_id": tid,
                    "candle_time_utc": candle_time,
                    "realized_r": "",
                    "outcome": "UNKNOWN",
                    "r_source": f"trade_record_final_outcome_{final_outcome}",
                    "notes": f"Unhandled final_outcome={final_outcome}; execution={execution}",
                })

    # Write CSV
    out_csv = OUT_DIR / "a4_realized_r_join.csv"
    cols = ["trade_id", "candle_time_utc", "realized_r", "outcome", "r_source", "notes"]
    with open(out_csv, "w", encoding="utf-8", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=cols)
        w.writeheader()
        for r in rows:
            w.writerow(r)
    print(f"Wrote {out_csv}")
    print(f"Rows: {len(rows)}")
    for r in rows:
        print(f"  {r['trade_id']}  outcome={r['outcome']}  r={r['realized_r']}  src={r['r_source']}")


if __name__ == "__main__":
    main()
