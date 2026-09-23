#!/usr/bin/env python3
"""Lane FD verification recompute — FA-continuation Phase A2 (Fable verifier).

Recomputes Session FD's claimed numbers from RAW inputs only:
  * CP February S0R0 compact pool (24,239 rows, gz)  — commission-named raw input
  * CP February full missed-opportunity ledger (129,165 rows, plain jsonl)
  * CJ January full missed-opportunity ledger (153,425 rows, plain jsonl)
  * CJ January compact pool (27,658 rows, gz)
  * CP February arm receipt (commission repair report)

It does NOT read Sol's REPRODUCTION_AND_BIAS.json numbers to produce any figure;
Sol receipts are treated as CLAIMS. February is read attribution-only under
owner_mandate_20260801. March and live-forward paths are refused.

Streaming line-by-line; accumulators only; peak memory well under 1.5 GB.

FD's re-decode rule (read from Sol's committed builder
research/operations/wave19_sol_repair_2026_08_01/defects/analyze_decision_defects.py:219-258,
implemented here independently):
  rows with symbol in {GER40, UKOIL_cash, USOIL_cash} and cost_r == 0.12 (abs 1e-12):
    redecoded = spread_r + expected_slippage_r + swap_cost_r + commission_r  (all 4 required)
    delta     = 0.12 - redecoded            (recorded minus redecoded)
    corrected_net = opportunity_net_proxy_r + delta   (scoreable rows only)
    sign flip when (net > 0) != (corrected_net > 0)
"""

from __future__ import annotations

import gzip
import hashlib
import json
import math
import resource
import sys
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

OUT_DIR = Path(__file__).resolve().parent
TARGET = ("GER40", "UKOIL_cash", "USOIL_cash")
PLACEHOLDER = {"BTCUSD": 0.0001, "UKOIL_cash": 0.0258, "USOIL_cash": 0.027}

FEB_POOL = Path(
    "/Users/borr/GTOSActive/worktrees/wave18-true-utc-factory-20260801/docs/audits/"
    "fable5-vision-audit-20260725/phase18/receipts/pools/CP_FEBRUARY_S0R0_POOL_V1.jsonl.gz"
)
FEB_POOL_W19 = Path(
    "/Users/borr/GTOSActive/worktrees/wave19-broad-forensic-20260801/docs/audits/"
    "fable5-vision-audit-20260725/phase18/receipts/pools/CP_FEBRUARY_S0R0_POOL_V1.jsonl.gz"
)
FEB_LEDGER = Path(
    "/Users/borr/GTOSActive/worktrees/wave18-true-utc-factory-20260801/research/operations/"
    "final_moonshot_ultimate_system_denominator_to_deployment_execution_2026_06_20/"
    "attempt_5_typed_sparse/CP_FEBRUARY_TRUE_UTC_S0R0_V1/"
    "CP_FEBRUARY_TRUE_UTC_S0R0_V1_MISSED_OPPORTUNITY_LEDGER.jsonl"
)
JAN_POOL = Path(
    "/Users/borr/GTOSActive/worktrees/wave16-rematerialization-20260731/docs/audits/"
    "fable5-vision-audit-20260725/phase16/receipts/pools/CJ_RECLOCKED_S0R0_POOL_V1.jsonl.gz"
)
JAN_LEDGER = Path(
    "/Users/borr/GTOSActive/worktrees/wave16-rematerialization-20260731/research/operations/"
    "final_moonshot_ultimate_system_denominator_to_deployment_execution_2026_06_20/"
    "attempt_5_typed_sparse/CJ_RECLOCKED_S0R0_V7/CJ_RECLOCKED_S0R0_V7_MISSED_OPPORTUNITY_LEDGER.jsonl"
)
ARM_RECEIPT = Path(
    "/Users/borr/GTOSActive/worktrees/wave18-true-utc-factory-20260801/docs/audits/"
    "fable5-vision-audit-20260725/phase18/receipts/CP_FEBRUARY_ARM_S0R0_V1.json"
)

for p in (FEB_POOL, FEB_POOL_W19, FEB_LEDGER, JAN_POOL, JAN_LEDGER, ARM_RECEIPT):
    text = str(p).lower()
    if any(tok in text for tok in ("2026-03", "march", "live-forward", "live_forward")):
        raise SystemExit(f"forbidden path: {p}")
    if not p.is_file():
        raise SystemExit(f"missing raw input: {p}")


def num(value):
    try:
        out = float(value)
    except (TypeError, ValueError):
        return None
    return out if math.isfinite(out) else None


def is_scoreable(row) -> bool:
    return bool(
        row.get("missed_opportunity_non_executable_diagnostic_scoreable") is True
        or row.get("missed_opportunity_r_scoreability_status")
        == "diagnostic_opportunity_r_scoreable"
    )


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(4 * 1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


class Acc:
    """Per-window accumulator shared by ledger and pool scans."""

    def __init__(self, month_prefix: str):
        self.month_prefix = month_prefix
        self.rows = 0
        self.scoreable_rows = 0
        self.month_violations = 0
        # flat 0.12 on the three target symbols
        self.fb = {
            s: {
                "physical_rows": 0,
                "scoreable_rows": 0,
                "complete_component_rows": 0,
                "recorded_cost_r_sum": 0.0,
                "redecoded_cost_r_sum": 0.0,
                "scoreable_recorded_net_r_sum": 0.0,
                "scoreable_redecoded_net_r_sum": 0.0,
                "scoreable_sign_flips": 0,
                "scoreable_zero_boundary_rows": 0,
                "scoreable_component_incomplete_rows": 0,
            }
            for s in TARGET
        }
        # flat 0.12 anywhere (scope check: is the 3-symbol restriction complete?)
        self.flat012_by_symbol = Counter()
        # cost_missing miss_reason
        self.cost_missing_by_symbol = Counter()
        # spread placeholders + constancy
        self.sym = {
            s: {
                "rows": 0,
                "scoreable_rows": 0,
                "spread_at_template_rows": 0,
                "scoreable_spread_at_template_rows": 0,
                "spread_distinct": set(),
                "spread_min": None,
                "spread_max": None,
                "cost_distinct": set(),
            }
            for s in PLACEHOLDER
        }
        for s in TARGET:
            if s not in self.sym:
                self.sym[s] = {
                    "rows": 0,
                    "scoreable_rows": 0,
                    "spread_at_template_rows": 0,
                    "scoreable_spread_at_template_rows": 0,
                    "spread_distinct": set(),
                    "spread_min": None,
                    "spread_max": None,
                    "cost_distinct": set(),
                }
        # schema field presence (FD-02 evidence)
        self.pretrade_key_present = 0
        self.pretrade_non_null = 0

    def eat(self, row):
        self.rows += 1
        t = str(row.get("decision_time_utc") or row.get("decision_time") or "")
        if t and not t.startswith(self.month_prefix):
            self.month_violations += 1
        scoreable = is_scoreable(row)
        if scoreable:
            self.scoreable_rows += 1

        if "pretrade_cost_packet_status" in row:
            self.pretrade_key_present += 1
            if row.get("pretrade_cost_packet_status") is not None:
                self.pretrade_non_null += 1

        symbol = str(row.get("symbol") or "")
        cost = num(row.get("cost_r"))
        reason = str(row.get("miss_reason") or "")
        if "cost_missing" in reason:
            self.cost_missing_by_symbol[symbol] += 1

        if cost is not None and abs(cost - 0.12) <= 1e-12:
            self.flat012_by_symbol[symbol] += 1

        if symbol in self.sym:
            st = self.sym[symbol]
            st["rows"] += 1
            if scoreable:
                st["scoreable_rows"] += 1
            spread = num(row.get("spread_r"))
            if spread is not None:
                if len(st["spread_distinct"]) < 200000:
                    st["spread_distinct"].add(spread)
                st["spread_min"] = (
                    spread if st["spread_min"] is None else min(st["spread_min"], spread)
                )
                st["spread_max"] = (
                    spread if st["spread_max"] is None else max(st["spread_max"], spread)
                )
                template = PLACEHOLDER.get(symbol)
                if template is not None and abs(spread - template) <= 1e-12:
                    st["spread_at_template_rows"] += 1
                    if scoreable:
                        st["scoreable_spread_at_template_rows"] += 1
            if cost is not None and len(st["cost_distinct"]) < 200000:
                st["cost_distinct"].add(cost)

        if symbol in self.fb and cost is not None and abs(cost - 0.12) <= 1e-12:
            fb = self.fb[symbol]
            fb["physical_rows"] += 1
            if scoreable:
                fb["scoreable_rows"] += 1
            comps = [
                num(row.get("spread_r")),
                num(row.get("expected_slippage_r")),
                num(row.get("swap_cost_r")),
                num(row.get("commission_r")),
            ]
            if all(v is not None for v in comps):
                redecoded = sum(comps)
                delta = cost - redecoded
                fb["complete_component_rows"] += 1
                fb["recorded_cost_r_sum"] += cost
                fb["redecoded_cost_r_sum"] += redecoded
                net = num(row.get("opportunity_net_proxy_r"))
                if scoreable and net is not None:
                    corrected = net + delta
                    fb["scoreable_recorded_net_r_sum"] += net
                    fb["scoreable_redecoded_net_r_sum"] += corrected
                    if (net > 0) != (corrected > 0):
                        fb["scoreable_sign_flips"] += 1
                    if net == 0.0 or corrected == 0.0:
                        fb["scoreable_zero_boundary_rows"] += 1
            elif scoreable:
                fb["scoreable_component_incomplete_rows"] += 1

    def result(self):
        fb_total_phys = sum(v["physical_rows"] for v in self.fb.values())
        fb_total_score = sum(v["scoreable_rows"] for v in self.fb.values())
        rec = sum(v["scoreable_recorded_net_r_sum"] for v in self.fb.values())
        red = sum(v["scoreable_redecoded_net_r_sum"] for v in self.fb.values())
        flips = sum(v["scoreable_sign_flips"] for v in self.fb.values())
        out = {
            "rows": self.rows,
            "scoreable_rows": self.scoreable_rows,
            "month_violations": self.month_violations,
            "pretrade_cost_packet_status": {
                "key_present_rows": self.pretrade_key_present,
                "non_null_rows": self.pretrade_non_null,
            },
            "flat_0p12_target_symbols": {
                s: {
                    **{
                        k: (round(v, 9) if isinstance(v, float) else v)
                        for k, v in self.fb[s].items()
                    },
                    "recorded_mean_cost_r": (
                        round(
                            self.fb[s]["recorded_cost_r_sum"]
                            / self.fb[s]["complete_component_rows"],
                            9,
                        )
                        if self.fb[s]["complete_component_rows"]
                        else None
                    ),
                    "redecoded_mean_cost_r": (
                        round(
                            self.fb[s]["redecoded_cost_r_sum"]
                            / self.fb[s]["complete_component_rows"],
                            9,
                        )
                        if self.fb[s]["complete_component_rows"]
                        else None
                    ),
                    "scoreable_net_delta_r": round(
                        self.fb[s]["scoreable_redecoded_net_r_sum"]
                        - self.fb[s]["scoreable_recorded_net_r_sum"],
                        9,
                    ),
                }
                for s in TARGET
            },
            "flat_0p12_totals": {
                "physical_rows": fb_total_phys,
                "scoreable_rows": fb_total_score,
                "scoreable_recorded_net_r_sum": round(rec, 9),
                "scoreable_redecoded_net_r_sum": round(red, 9),
                "scoreable_net_r_delta_after_redecode": round(red - rec, 9),
                "scoreable_sign_flips": flips,
            },
            "flat_0p12_all_symbols": dict(self.flat012_by_symbol.most_common()),
            "cost_missing_miss_reason_by_symbol": dict(
                self.cost_missing_by_symbol.most_common()
            ),
            "cost_missing_miss_reason_total": sum(self.cost_missing_by_symbol.values()),
            "symbol_constancy": {
                s: {
                    "rows": st["rows"],
                    "scoreable_rows": st["scoreable_rows"],
                    "template_spread_r": PLACEHOLDER.get(s),
                    "spread_at_template_rows": st["spread_at_template_rows"],
                    "scoreable_spread_at_template_rows": st[
                        "scoreable_spread_at_template_rows"
                    ],
                    "spread_distinct_count": len(st["spread_distinct"]),
                    "spread_min": st["spread_min"],
                    "spread_max": st["spread_max"],
                    "cost_distinct_count": len(st["cost_distinct"]),
                    "cost_distinct_values_if_small": (
                        sorted(st["cost_distinct"])
                        if len(st["cost_distinct"]) <= 5
                        else None
                    ),
                }
                for s, st in sorted(self.sym.items())
            },
        }
        return out


def scan_jsonl(path: Path, month_prefix: str, gz: bool):
    acc = Acc(month_prefix)
    digest = hashlib.sha256()
    if gz:
        with path.open("rb") as raw:
            for chunk in iter(lambda: raw.read(4 * 1024 * 1024), b""):
                digest.update(chunk)
        opener = gzip.open(path, "rt", encoding="utf-8")
        with opener as handle:
            for line in handle:
                if not line.strip():
                    continue
                acc.eat(json.loads(line))
    else:
        with path.open("rb") as handle:
            for rawline in handle:
                digest.update(rawline)
                if not rawline.strip():
                    continue
                acc.eat(json.loads(rawline))
    out = acc.result()
    out["source"] = {
        "path": str(path),
        "bytes": path.stat().st_size,
        "sha256": digest.hexdigest(),
    }
    return out


def main():
    started = datetime.now(timezone.utc).isoformat()
    result = {
        "schema": "gtos.phase19.fa_a2_verify.fd_recompute.v1",
        "verifier": "fable_a2_lane_fd",
        "started_utc": started,
        "february_provenance": "owner_mandate_20260801",
        "february_use": "defect attribution only",
        "march_or_live_forward_read": False,
    }

    sys.stderr.write("[1/5] Feb pool...\n")
    result["feb_pool"] = scan_jsonl(FEB_POOL, "2026-02", gz=True)
    result["feb_pool_wave19_copy_sha256"] = sha256_file(FEB_POOL_W19)

    sys.stderr.write("[2/5] Jan pool...\n")
    result["jan_pool"] = scan_jsonl(JAN_POOL, "2026-01", gz=True)

    sys.stderr.write("[3/5] arm receipt...\n")
    receipt = json.loads(ARM_RECEIPT.read_text())
    rep = receipt.get("repair_report", {}).get("commission_broker_true_gated", {})
    result["feb_arm_receipt"] = {
        "path": str(ARM_RECEIPT),
        "sha256": sha256_file(ARM_RECEIPT),
        "calls": rep.get("calls"),
        "applied": rep.get("applied"),
        "unpriced": rep.get("unpriced"),
        "per_symbol_target": {
            s: rep.get("per_symbol", {}).get(s) for s in TARGET
        },
    }

    sys.stderr.write("[4/5] Feb full ledger (1.2 GB)...\n")
    result["feb_ledger"] = scan_jsonl(FEB_LEDGER, "2026-02", gz=False)

    sys.stderr.write("[5/5] Jan full ledger (1.3 GB)...\n")
    result["jan_ledger"] = scan_jsonl(JAN_LEDGER, "2026-01", gz=False)

    result["finished_utc"] = datetime.now(timezone.utc).isoformat()
    result["peak_rss_bytes"] = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    out_path = OUT_DIR / "FD_RECOMPUTE_RAW.json"
    out_path.write_text(json.dumps(result, indent=1, sort_keys=True) + "\n")
    sys.stderr.write(f"written {out_path}\n")
    print(
        json.dumps(
            {
                "feb_pool_rows": result["feb_pool"]["rows"],
                "feb_ledger_rows": result["feb_ledger"]["rows"],
                "jan_pool_rows": result["jan_pool"]["rows"],
                "jan_ledger_rows": result["jan_ledger"]["rows"],
                "feb_ledger_delta": result["feb_ledger"]["flat_0p12_totals"][
                    "scoreable_net_r_delta_after_redecode"
                ],
                "feb_ledger_flips": result["feb_ledger"]["flat_0p12_totals"][
                    "scoreable_sign_flips"
                ],
                "feb_pool_delta": result["feb_pool"]["flat_0p12_totals"][
                    "scoreable_net_r_delta_after_redecode"
                ],
                "feb_pool_flips": result["feb_pool"]["flat_0p12_totals"][
                    "scoreable_sign_flips"
                ],
                "peak_rss_mb": round(result["peak_rss_bytes"] / 1e6, 1),
            }
        )
    )


if __name__ == "__main__":
    main()
