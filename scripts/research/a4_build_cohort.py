#!/usr/bin/env python
"""A4 cohort builder — H2-2026 XAUUSD trending_bull CANDIDATEs.

Reads:
- knowledge_base/live_evaluations/XAUUSD/*.jsonl       (live AI emissions)
- knowledge_base/live_evaluations_h1_reconstructed/XAUUSD/*.jsonl (post-hoc)
- shadow_logs/structure_detector_backfill_2026.jsonl   (XAUUSD H4 regime time series)
- knowledge_base/trade_records/XAUUSD/*.json           (per-candidate MSO + prompt)

Writes:
- {out}/a4_cohort_manifest.csv with columns:
    trade_id, candle_time_utc, kill_zone, regime, regime_sample_ts,
    daily_bias_direction, setup_grade, framework, ai_decision_original,
    ai_direction_original, source, mso_path, has_full_mso,
    reconstructed_only, l2_fail_rule

Filter (matches A4 spec):
- symbol = XAUUSD
- 2026-03-15 <= candle_time <= 2026-04-27
- ai_decision == CANDIDATE
- regime == trending_bull   (mapped from structure_detector_backfill `bullish` → trending_bull)

Only records with `has_full_mso=True` are replay-eligible. Records without MSO
are listed in the manifest with reconstructed_only=True so the operator sees
the full cohort + the unreplayable subset.
"""
from __future__ import annotations

import argparse
import bisect
import csv
import glob
import json
import os
import sys
from collections import Counter
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
# Allow `--data-root` override so worktree agents can point at the parent repo
# (gitignored shadow_logs / live_evaluations are invisible from the worktree).
def _data_root_from_env_or_default() -> Path:
    env = os.environ.get("GTOS_DATA_ROOT")
    if env:
        return Path(env)
    return REPO_ROOT

# Module-level paths populated in main() after data_root is resolved.
LIVE_EVAL_DIR: Path = REPO_ROOT / "knowledge_base" / "live_evaluations" / "XAUUSD"
RECON_DIR: Path = REPO_ROOT / "knowledge_base" / "live_evaluations_h1_reconstructed" / "XAUUSD"
TRADE_REC_DIR: Path = REPO_ROOT / "knowledge_base" / "trade_records" / "XAUUSD"
STRUCT_BACKFILL: Path = REPO_ROOT / "shadow_logs" / "structure_detector_backfill_2026.jsonl"

H2_START = "2026-03-15"
H2_END = "2026-04-27"  # inclusive (live launch boundary)

# v2 structure direction → V1 regime classifier label
STRUCT_TO_REGIME = {
    "bullish": "trending_bull",
    "bearish": "trending_bear",
    "transitional": "chop",
}


def load_candidates() -> dict:
    """Load all H2-2026 XAUUSD CANDIDATEs from live + reconstructed evals.

    Live wins over reconstructed when both reference the same candle_time.
    Returns dict keyed by candle_time.
    """
    out: dict = {}

    # Live evaluations (have full grade/framework + matching trade record)
    for f in sorted(LIVE_EVAL_DIR.glob("*.jsonl")):
        for line in open(f, encoding="utf-8"):
            try:
                d = json.loads(line)
            except Exception:
                continue
            if d.get("decision") != "CANDIDATE":
                continue
            if d.get("symbol") != "XAUUSD":
                continue
            ct = d.get("candle_time", "")
            if not (ct.startswith("2026-") and H2_START <= ct[:10] <= H2_END):
                continue
            d["_source"] = "live_evaluations"
            d["_source_file"] = f.name
            out[ct] = d

    # Reconstructed (only fill gaps live didn't cover)
    for f in sorted(RECON_DIR.glob("*.jsonl")):
        for line in open(f, encoding="utf-8"):
            try:
                d = json.loads(line)
            except Exception:
                continue
            if d.get("decision") != "CANDIDATE":
                continue
            if d.get("symbol") != "XAUUSD":
                continue
            ct = d.get("candle_time", "")
            if not (ct.startswith("2026-") and H2_START <= ct[:10] <= H2_END):
                continue
            if ct in out:
                continue  # live wins
            d["_source"] = "live_evaluations_h1_reconstructed"
            d["_source_file"] = f.name
            out[ct] = d

    return out


def load_xau_h4_regime() -> list[tuple[str, str]]:
    """Return sorted [(ts, struct_label)] for XAUUSD H4."""
    out: list[tuple[str, str]] = []
    if not STRUCT_BACKFILL.exists():
        sys.stderr.write(f"WARNING: missing {STRUCT_BACKFILL}\n")
        return out
    for line in open(STRUCT_BACKFILL, encoding="utf-8"):
        try:
            r = json.loads(line)
        except Exception:
            continue
        if r.get("symbol") != "XAUUSD":
            continue
        if r.get("timeframe") != "H4":
            continue
        out.append((r["ts"], r.get("production_label", "unknown")))
    out.sort(key=lambda x: x[0])
    return out


def tag_regime(candle_time: str, regime_keys: list[str], regime_samples: list[tuple[str, str]]):
    """Find the most recent regime sample at or before candle_time."""
    idx = bisect.bisect_right(regime_keys, candle_time) - 1
    if idx < 0:
        return None, None
    sample = regime_samples[idx]
    return STRUCT_TO_REGIME.get(sample[1], sample[1]), sample[0]


def find_trade_record(candle_time: str, kill_zone: str) -> tuple[Path | None, bool]:
    """Find a trade_records/XAUUSD/*.json that matches this candidate.

    Returns (path, has_full_mso). Tries the canonical naming
    YYYY-MM-DD_kz_HHMM.json plus +/- 1-3 minute offsets (capture timing
    can drift up to a few seconds when the orchestrator wakes).
    """
    if not TRADE_REC_DIR.exists():
        return None, False
    date = candle_time[:10]
    hh = candle_time[11:13]
    mm = candle_time[14:16]
    try:
        m_int = int(mm)
    except ValueError:
        return None, False

    candidates = [(hh, mm)]
    for off in (-1, 1, -2, 2, -3, 3):
        new_m = m_int + off
        if 0 <= new_m < 60:
            candidates.append((hh, f"{new_m:02d}"))

    for h, m in candidates:
        f = TRADE_REC_DIR / f"{date}_{kill_zone}_{h}{m}.json"
        if not f.exists():
            continue
        try:
            d = json.load(open(f, encoding="utf-8"))
        except Exception:
            continue
        has_mso = bool(d.get("mso")) and bool(
            d.get("prompt", {}).get("system_prompt")
        ) and bool(d.get("prompt", {}).get("user_message"))
        return f, has_mso
    return None, False


def main() -> int:
    parser = argparse.ArgumentParser(description="Build A4 trending_bull cohort manifest")
    parser.add_argument(
        "--out-dir",
        default=str(REPO_ROOT / "research" / "a4_trending_bull_replay_2026-04-28"),
    )
    parser.add_argument(
        "--data-root",
        default=None,
        help="Repo root containing knowledge_base/ + shadow_logs/. "
             "Defaults to script-relative repo root or GTOS_DATA_ROOT env var.",
    )
    args = parser.parse_args()

    data_root = Path(args.data_root) if args.data_root else _data_root_from_env_or_default()
    global LIVE_EVAL_DIR, RECON_DIR, TRADE_REC_DIR, STRUCT_BACKFILL
    LIVE_EVAL_DIR = data_root / "knowledge_base" / "live_evaluations" / "XAUUSD"
    RECON_DIR = data_root / "knowledge_base" / "live_evaluations_h1_reconstructed" / "XAUUSD"
    TRADE_REC_DIR = data_root / "knowledge_base" / "trade_records" / "XAUUSD"
    STRUCT_BACKFILL = data_root / "shadow_logs" / "structure_detector_backfill_2026.jsonl"
    print(f"data_root: {data_root}", file=sys.stderr)

    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    candidates = load_candidates()
    print(f"H2-2026 XAUUSD CANDIDATEs: {len(candidates)}", file=sys.stderr)

    regime_samples = load_xau_h4_regime()
    regime_keys = [r[0] for r in regime_samples]
    print(f"XAUUSD H4 regime samples: {len(regime_samples)}", file=sys.stderr)

    rows = []
    for ct in sorted(candidates):
        c = candidates[ct]
        regime, regime_ts = tag_regime(ct, regime_keys, regime_samples)
        kill_zone = c.get("kill_zone") or ""
        # Trade record lookup
        rec_path, has_mso = find_trade_record(ct, kill_zone)
        # ai_direction comes from the trade record if available
        ai_dir = None
        ai_grade = c.get("setup_grade")
        ai_fw = c.get("framework")
        if rec_path:
            try:
                rec = json.load(open(rec_path, encoding="utf-8"))
                ai_dir = rec.get("decision_pipeline", {}).get("ai_direction")
                if not ai_grade:
                    ai_grade = rec.get("decision_pipeline", {}).get("ai_grade")
                if not ai_fw:
                    ai_fw = rec.get("decision_pipeline", {}).get("ai_framework")
            except Exception:
                pass

        rows.append({
            "trade_id": (rec_path.stem if rec_path
                         else f"XAUUSD_{ct.replace(':', '').replace('-', '_')[:19]}"),
            "candle_time_utc": ct,
            "kill_zone": kill_zone,
            "regime": regime,
            "regime_sample_ts": regime_ts,
            "daily_bias_direction": c.get("daily_bias_direction"),
            "setup_grade": ai_grade,
            "framework": ai_fw,
            "ai_decision_original": "CANDIDATE",
            "ai_direction_original": ai_dir,
            "source": c.get("_source"),
            "mso_path": str(rec_path) if rec_path else "",
            "has_full_mso": has_mso,
            "reconstructed_only": (
                c.get("_source") == "live_evaluations_h1_reconstructed"
                and not has_mso
            ),
            "l2_fail_rule": c.get("reconstructed_l2_fail_rule") or "",
        })

    # Sort: trending_bull first, then by time
    rows.sort(key=lambda r: (r["regime"] != "trending_bull", r["candle_time_utc"]))

    # Write FULL cohort manifest (all H2 CANDIDATEs)
    full_csv = out_dir / "a4_cohort_full.csv"
    with open(full_csv, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)

    # trending_bull-only manifest, with full MSO
    tb_replay = [r for r in rows if r["regime"] == "trending_bull" and r["has_full_mso"]]
    tb_csv = out_dir / "a4_cohort_manifest.csv"
    with open(tb_csv, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(tb_replay)

    # Diagnostic summary
    regime_dist = Counter(r["regime"] for r in rows)
    tb_total = sum(1 for r in rows if r["regime"] == "trending_bull")
    tb_replayable = sum(1 for r in rows if r["regime"] == "trending_bull" and r["has_full_mso"])
    by_kz = Counter(r["kill_zone"] for r in tb_replay)
    by_dir = Counter(r["ai_direction_original"] for r in tb_replay)

    summary = {
        "h2_window": [H2_START, H2_END],
        "total_candidates": len(rows),
        "regime_distribution": dict(regime_dist),
        "trending_bull_total": tb_total,
        "trending_bull_replayable": tb_replayable,
        "trending_bull_unreplayable": tb_total - tb_replayable,
        "tb_replayable_by_kill_zone": dict(by_kz),
        "tb_replayable_by_direction": dict(by_dir),
        "manifest_path": str(tb_csv),
        "full_path": str(full_csv),
    }
    summary_path = out_dir / "a4_cohort_summary.json"
    json.dump(summary, open(summary_path, "w", encoding="utf-8"), indent=2)

    print(json.dumps(summary, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
