"""B9 step 1 — verify the clamp at source and in the data, independently of Lane 5.

Three independent confirmations, each recorded as a receipt field:

  (a) SOURCE   — the two clamp branches, read from `origin/main` bytes, not the worktree.
  (b) DATA     — the sign census of `swap_cost_r` over the whole candidate cache.
  (c) CONFIG   — cross-validate: the symbol/sides whose cached mean swap_cost_r is exactly
                 0.0 must be exactly the non-negative-swap sides of the live profile table.

(c) is the one that matters: it proves the zeros are the CLAMP and not an absence of
overnight holds. If a symbol/side has zero cost because it never held overnight, it would
show zeros on BOTH sides; if it is the clamp, the zero side is precisely the favourable side.

Writes B9_CLAMP_EVIDENCE_V1.json next to this file.
"""
from __future__ import annotations

import collections
import gzip
import hashlib
import json
import pathlib
import pickle
import subprocess
import sys

HERE = pathlib.Path(__file__).resolve().parent
REPO = pathlib.Path("/Users/borr/GTOSActive/worktrees/claude-opus5-architecture-audit-20260725")
CACHE = pathlib.Path("/private/tmp/w21-puzzle-cache")
MONTHS = ("feb", "apr", "may", "jun", "jul")


def git_show(path: str) -> bytes:
    return subprocess.run(
        ["git", "show", f"origin/main:{path}"], cwd=REPO, capture_output=True, check=True
    ).stdout


def source_evidence() -> dict:
    out = {}
    for path, needle in (
        ("src/components/broker_net_cost_engine.py", "elif swap >= 0:"),
        ("src/costs/model.py", "if float(raw) >= 0:"),
    ):
        raw = git_show(path)
        lines = raw.decode().splitlines()
        hits = [i + 1 for i, ln in enumerate(lines) if needle in ln]
        ctx = {}
        for ln in hits:
            ctx[ln] = [f"{n}: {lines[n - 1]}" for n in range(ln, min(ln + 4, len(lines) + 1))]
        out[path] = {
            "sha256_origin_main": hashlib.sha256(raw).hexdigest(),
            "clamp_line_numbers": hits,
            "context": ctx,
        }
    return out


def load_rows():
    rows = []
    for m in MONTHS:
        rows += pickle.load(gzip.open(CACHE / f"rows_{m}.pkl.gz", "rb"))
    return rows


def num(x):
    try:
        v = float(x)
        return v if v == v else None
    except (TypeError, ValueError):
        return None


def profile_specs(rel: str) -> dict:
    import yaml

    d = yaml.safe_load((REPO / rel).read_text())
    out = {}
    for sym, v in (d.get("instruments") or {}).items():
        m = (v or {}).get("market") or {}
        if "swap_long" in m:
            out[sym] = m
    return out


def main() -> int:
    ev = {"source": source_evidence()}

    rows = load_rows()
    vals, by_ss = [], collections.defaultdict(list)
    for r in rows:
        v = num(r.get("swap_cost_r"))
        if v is None:
            continue
        vals.append(v)
        by_ss[(r.get("symbol"), r.get("side"))].append(v)
    ev["data"] = {
        "cache_rows_total": len(rows),
        "swap_cost_r_present": len(vals),
        "n_negative": sum(1 for v in vals if v < 0),
        "n_zero": sum(1 for v in vals if v == 0.0),
        "n_positive": sum(1 for v in vals if v > 0),
        "min": min(vals),
        "max": max(vals),
        "mean": sum(vals) / len(vals),
        "months": list(MONTHS),
    }

    ftmo = profile_specs("config/profiles/operator_profile.yaml")
    cross, agree, disagree = {}, 0, 0
    for (sym, side), vs in sorted(by_ss.items(), key=lambda kv: str(kv[0])):
        spec = ftmo.get(sym)
        if not spec:
            continue
        raw = spec.get("swap_long" if str(side).upper() in ("LONG", "BUY") else "swap_short")
        mean = sum(vs) / len(vs)
        favourable = raw is not None and float(raw) >= 0
        zero = mean == 0.0
        cross[f"{sym}|{side}"] = {
            "n": len(vs),
            "profile_swap": raw,
            "profile_side_is_favourable": favourable,
            "cache_mean_swap_cost_r": mean,
            "cache_mean_is_exactly_zero": zero,
            "consistent": favourable == zero,
        }
        agree += favourable == zero
        disagree += favourable != zero
    ev["config_cross_validation"] = {
        "account": "FTMO operator_profile",
        "symbol_sides_compared": agree + disagree,
        "consistent": agree,
        "inconsistent": disagree,
        "claim": (
            "a cached mean swap_cost_r of exactly 0.0 occurs if and only if the live "
            "profile's swap on that side is >= 0 -- i.e. the zeros are the clamp, not "
            "an absence of overnight holds"
        ),
        "detail": cross,
    }

    (HERE / "B9_CLAMP_EVIDENCE_V1.json").write_text(json.dumps(ev, indent=1, sort_keys=True))
    d = ev["data"]
    print(f"cache rows {d['cache_rows_total']}  swap_cost_r n={d['swap_cost_r_present']}")
    print(f"  negative={d['n_negative']}  zero={d['n_zero']}  positive={d['n_positive']}")
    print(f"  min={d['min']:+.6f} max={d['max']:+.6f} mean={d['mean']:+.6f}")
    c = ev["config_cross_validation"]
    print(f"config cross-validation: {c['consistent']}/{c['symbol_sides_compared']} consistent, {c['inconsistent']} inconsistent")
    for k, v in c["detail"].items():
        if not v["consistent"]:
            print("  INCONSISTENT", k, v)
    return 0


if __name__ == "__main__":
    sys.exit(main())
