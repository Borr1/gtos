"""Exact-parity micro-benchmark of the two measured hot-path optimisations.

Runs the ORIGINAL and OPTIMISED implementations over real authority payloads
extracted from a sealed January S1R1 order ledger, asserts every digest is
byte-identical, and reports the speedup.
"""
import json, hashlib, time, sys, os
from collections.abc import Mapping, Sequence

NS = ("/Users/borr/GTOSActive/worktrees/replay-accel-engine-20260719/research/operations/"
      "final_moonshot_ultimate_system_denominator_to_deployment_execution_2026_06_20/"
      "attempt_5_typed_sparse/PHASE_D_JANUARY_S1R1_R1_20260724T195321Z")
PREFIX = "BROAD_LIVE_AS_IF_REPLAY_B7_5_2026_01_SELECTION_SIZING_S1R1_SOURCE_REPAIRED_R3_CAP_R2"

# ---- ORIGINAL (verbatim from moonshot_scheduler_v4_best_trade_allocator.py:668-681) ----
def orig_canonical(value):
    if isinstance(value, Mapping):
        return {str(k): orig_canonical(v)
                for k, v in sorted(value.items(), key=lambda p: str(p[0]))
                if v not in (None, "")}
    if isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray)):
        return [orig_canonical(v) for v in value if v not in (None, "")]
    if isinstance(value, float):
        return round(value, 12)
    return value

def orig_material(payload):
    return json.dumps(orig_canonical(payload), sort_keys=True,
                      separators=(",", ":"), default=str)

def orig_sha(payload):
    return hashlib.sha256(orig_material(payload).encode("utf-8")).hexdigest()

# ---- OPTIMISED: concrete-type fast path + one reused encoder ----
_ENCODER = json.JSONEncoder(sort_keys=True, separators=(",", ":"), default=str)

def opt_canonical(value):
    t = type(value)
    if t is dict:
        return {str(k): opt_canonical(v)
                for k, v in sorted(value.items(), key=lambda p: str(p[0]))
                if v not in (None, "")}
    if t is list:
        return [opt_canonical(v) for v in value if v not in (None, "")]
    if t is float:
        return round(value, 12)
    if t is str or t is int or t is bool or value is None:
        return value
    # fall back to the exact original semantics for every other type
    if isinstance(value, Mapping):
        return {str(k): opt_canonical(v)
                for k, v in sorted(value.items(), key=lambda p: str(p[0]))
                if v not in (None, "")}
    if isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray)):
        return [opt_canonical(v) for v in value if v not in (None, "")]
    if isinstance(value, float):
        return round(value, 12)
    return value

def opt_material(payload):
    return _ENCODER.encode(opt_canonical(payload))

def opt_sha(payload):
    return hashlib.sha256(opt_material(payload).encode("utf-8")).hexdigest()

# ---- real payloads ----
payloads = []
path = f"{NS}/{PREFIX}_ORDER_LEDGER.jsonl"
with open(path) as fh:
    for i, line in enumerate(fh):
        row = json.loads(line)
        ra = row.get("risk_authority")
        if isinstance(ra, dict):
            payloads.append(ra)
        sc = row.get("scheduler_candidate_decision_inputs")
        if isinstance(sc, dict):
            payloads.append(sc)
print(f"real authority payloads extracted from {os.path.basename(path)}: {len(payloads)}")

# ---- exact parity over every payload ----
mismatch = 0
for p in payloads:
    if orig_sha(p) != opt_sha(p):
        mismatch += 1
print(f"digest mismatches: {mismatch} / {len(payloads)}  ->  "
      f"{'EXACT PARITY' if mismatch == 0 else 'PARITY BROKEN'}")
if mismatch:
    sys.exit(1)

# ---- timing ----
def bench(fn, n=3):
    best = None
    for _ in range(n):
        t0 = time.perf_counter()
        for p in payloads:
            fn(p)
        dt = time.perf_counter() - t0
        best = dt if best is None else min(best, dt)
    return best

a = bench(orig_sha)
b = bench(opt_sha)
total_bytes = sum(len(orig_material(p)) for p in payloads)
print(f"\noriginal : {a:8.3f}s for {len(payloads)} payloads ({total_bytes/1e6:.1f} MB canonical)")
print(f"optimised: {b:8.3f}s")
print(f"speedup  : {a/b:.2f}x   ({100*(1-b/a):.1f}% of this stage removed)")

# split the two contributions
def orig_can_only(p): orig_canonical(p)
def opt_can_only(p): opt_canonical(p)
ca = bench(orig_can_only); cb = bench(opt_can_only)
print(f"\n  canonicalise only : {ca:.3f}s -> {cb:.3f}s  ({ca/cb:.2f}x)   [concrete-type fast path]")
enc_a = bench(lambda p: json.dumps(orig_canonical(p), sort_keys=True, separators=(",",":"), default=str))
enc_b = bench(lambda p: _ENCODER.encode(orig_canonical(p)))
print(f"  encode only       : {enc_a:.3f}s -> {enc_b:.3f}s  ({enc_a/enc_b:.2f}x)   [reused JSONEncoder]")
