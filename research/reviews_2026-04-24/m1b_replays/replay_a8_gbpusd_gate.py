"""
M1b Replay — A8 (per-instrument trading_enabled Gate 0.5)

Branch: worktree-agent-ad0a9ebd
Claim: Gate 0.5 is a NEW structural gate in permissions.py.  GBPUSD gets
trading_enabled=false (observer) while other 4 instruments get true.

Expected behavior:
  - GBPUSD CAND -> blocked at Gate 0.5 (new NO_TRADE outcome).
    Actually, in production GBPUSD already never places trades because
    (a) the pre-AI gate blocks most rows, and (b) even if a CAND emerges,
    the existing deployment.phase:3 live_micro + config would've allowed
    order placement on GBPUSD before this gate.  So Gate 0.5 CLOSES a gap.
  - Non-GBPUSD instruments: trading_enabled=true -> pass-through, no
    behavior change.

Replay:
  1. Run the branch's test_permissions.py.
  2. Load branch's permissions._reject_if_trading_disabled and branch's
     agent_config.yaml, then for each eval row in the 30-day window:
       - If symbol == 'GBPUSD' AND decision == 'CANDIDATE':
           new-behavior = NO_TRADE (Gate 0.5 blocks)
       - Otherwise: new-behavior = pass-through (no change)
  3. Count GBPUSD CAND rows that flip NO_TRADE under new gate.
  4. Count non-GBPUSD CAND rows that stay unchanged.

This is the ONLY branch of the five where flips are EXPECTED (for GBPUSD
only).
"""
from __future__ import annotations

import importlib.util
import json
import re
import subprocess
import sys
from datetime import date
from pathlib import Path

HERE = Path(__file__).resolve().parent
WORKTREE = Path(r"C:\Users\MSI\Documents\ai-trading-agent\.claude\worktrees\agent-ad0a9ebd")
MAIN_REPO = Path(r"C:\Users\MSI\Documents\ai-trading-agent")
EVAL_DIR = MAIN_REPO / "knowledge_base" / "live_evaluations"
WINDOW_START = date(2026, 3, 24)
WINDOW_END = date(2026, 4, 22)
OUTDIR = HERE / "outputs"
OUTDIR.mkdir(parents=True, exist_ok=True)


def run_branch_tests() -> dict:
    cmd = [sys.executable, "-m", "pytest", "tests/test_permissions.py",
           "-v", "--no-header", "-q", "--tb=no"]
    try:
        r = subprocess.run(cmd, cwd=WORKTREE, capture_output=True, text=True, timeout=180)
    except subprocess.TimeoutExpired:
        return {"error": "timeout"}
    stdout = r.stdout + "\n" + r.stderr
    passed = failed = 0
    m = re.search(r"(\d+)\s+passed", stdout)
    if m:
        passed = int(m.group(1))
    m = re.search(r"(\d+)\s+failed", stdout)
    if m:
        failed = int(m.group(1))
    return {"passed": passed, "failed": failed, "rc": r.returncode,
            "stdout_tail": "\n".join(stdout.splitlines()[-10:])}


def load_gate() -> callable:
    """Load the branch's _reject_if_trading_disabled function.

    Use a subprocess to cleanly execute in the branch's CWD so any `from
    src...` imports resolve against the branch's src tree, without polluting
    the parent session's sys.modules.  Then re-import the gate via a module
    spec referencing the branch path + added PYTHONPATH.
    """
    # The permissions module has `@dataclass` at module load which needs the
    # module to be findable in sys.modules.  Use importlib with the module
    # registered first.
    path = WORKTREE / "src" / "components" / "permissions.py"
    sys.path.insert(0, str(WORKTREE))
    try:
        spec = importlib.util.spec_from_file_location("_branch_permissions", path)
        mod = importlib.util.module_from_spec(spec)
        sys.modules["_branch_permissions"] = mod
        spec.loader.exec_module(mod)
    finally:
        sys.path.pop(0)
    return mod._reject_if_trading_disabled


def load_per_instrument_config() -> dict:
    """
    Extract the per-instrument trading_enabled flags from branch's
    agent_config.yaml.
    """
    import yaml
    cfg_path = WORKTREE / "config" / "agent_config.yaml"
    cfg = yaml.safe_load(cfg_path.read_text(encoding="utf-8"))
    instruments = cfg.get("instruments", {})
    flags = {}
    for sym, block in instruments.items():
        if isinstance(block, dict):
            flags[sym] = block.get("trading_enabled", True)
    return flags


def replay_gate_per_symbol(gate: callable, flags: dict) -> dict:
    """
    For each symbol with a flag, invoke the gate and check its verdict.
    Also invoke with flag missing (simulating a symbol the config doesn't
    list) — should default to ALLOW.
    """
    results = []
    # Symbols with explicit trading_enabled
    for sym, enabled in flags.items():
        fake_config = {"trading_enabled": enabled}
        denial = gate(fake_config, sym)
        blocked = denial is not None
        expected_block = not enabled
        ok = blocked == expected_block
        results.append({
            "symbol": sym, "trading_enabled": enabled,
            "expected_block": expected_block,
            "actual_block": blocked,
            "denial_gate": denial.gate if denial else None,
            "match": ok,
        })
    # Default case (no key)
    denial = gate({}, "UNKNOWN_SYMBOL")
    results.append({
        "symbol": "UNKNOWN_SYMBOL (no flag)",
        "trading_enabled": None,
        "expected_block": False,
        "actual_block": denial is not None,
        "denial_gate": denial.gate if denial else None,
        "match": denial is None,
    })
    return {
        "cases": len(results),
        "all_match": all(r["match"] for r in results),
        "results": results,
    }


def replay_against_eval_rows(gate: callable, flags: dict) -> dict:
    """
    Iterate every eval row in the window.  Simulate the per-symbol config
    loading via:
      config_for_sym = {"trading_enabled": flags.get(sym, True)}
    Then ask the gate what it does.

    For CAND rows specifically, compare new-behavior to historical decision.
    """
    counts = {
        "total_rows": 0,
        "cand_rows": 0,
        "gbpusd_cand": 0,
        "gbpusd_cand_blocked_new": 0,
        "non_gbpusd_cand": 0,
        "non_gbpusd_cand_blocked_new": 0,
        "non_gbpusd_cand_still_cand": 0,
    }
    per_symbol = {}
    flips = []
    for p in sorted(EVAL_DIR.rglob("*.jsonl")):
        try:
            fd = date.fromisoformat(p.stem)
        except Exception:
            continue
        if fd < WINDOW_START or fd > WINDOW_END:
            continue
        for line in p.read_text(encoding="utf-8", errors="ignore").splitlines():
            line = line.strip()
            if not line:
                continue
            try:
                row = json.loads(line)
            except Exception:
                continue
            counts["total_rows"] += 1
            sym = row.get("symbol", "?")
            per_symbol.setdefault(sym, {"total": 0, "cand": 0, "gate_blocks": 0})
            per_symbol[sym]["total"] += 1

            if row.get("decision") != "CANDIDATE":
                continue
            counts["cand_rows"] += 1
            per_symbol[sym]["cand"] += 1

            enabled = flags.get(sym, True)
            cfg = {"trading_enabled": enabled}
            denial = gate(cfg, sym)
            blocked = denial is not None

            if sym == "GBPUSD":
                counts["gbpusd_cand"] += 1
                if blocked:
                    counts["gbpusd_cand_blocked_new"] += 1
                    per_symbol[sym]["gate_blocks"] += 1
                    flips.append({
                        "symbol": sym, "ts": row.get("timestamp"),
                        "old_decision": "CANDIDATE", "new_decision": "NO_TRADE (gate 0.5)",
                    })
            else:
                counts["non_gbpusd_cand"] += 1
                if blocked:
                    counts["non_gbpusd_cand_blocked_new"] += 1
                    # CRITICAL: this should never happen
                else:
                    counts["non_gbpusd_cand_still_cand"] += 1

    return {
        "counts": counts,
        "per_symbol": per_symbol,
        "gbpusd_flip_sample": flips[:5],
        "flips_total": len(flips),
    }


def main() -> int:
    print("=" * 72)
    print("A8 REPLAY — GBPUSD trading_enabled Gate 0.5 (worktree-agent-ad0a9ebd)")
    print("=" * 72)

    print("\n[1/4] Running branch's test_permissions.py ...")
    tests = run_branch_tests()
    print(f"      passed={tests.get('passed')}  failed={tests.get('failed')}  rc={tests.get('rc')}")

    print("\n[2/4] Loading per-instrument trading_enabled flags ...")
    flags = load_per_instrument_config()
    print(f"      flags={flags}")

    print("\n[3/4] Synthetic per-symbol gate verification ...")
    gate = load_gate()
    inv = replay_gate_per_symbol(gate, flags)
    print(f"      cases={inv['cases']}  all_match={inv['all_match']}")
    for r in inv["results"]:
        print(f"         {r['symbol']:<28} enabled={r['trading_enabled']} blocked={r['actual_block']} ok={r['match']}")

    print("\n[4/4] Historical eval replay (30-day window) ...")
    live = replay_against_eval_rows(gate, flags)
    cts = live["counts"]
    print(f"      total_rows={cts['total_rows']} cand_rows={cts['cand_rows']}")
    print(f"      GBPUSD CAND: {cts['gbpusd_cand']} (blocked by new gate: {cts['gbpusd_cand_blocked_new']})")
    print(f"      non-GBPUSD CAND: {cts['non_gbpusd_cand']}")
    print(f"        blocked by new gate (should be 0): {cts['non_gbpusd_cand_blocked_new']}")
    print(f"        still CAND: {cts['non_gbpusd_cand_still_cand']}")
    print(f"      per-symbol: {live['per_symbol']}")
    if live['gbpusd_flip_sample']:
        print("      GBPUSD flips (sample):")
        for f in live['gbpusd_flip_sample']:
            print(f"         {f}")

    # EXPECTED:
    #  - Every GBPUSD CAND now blocked (gate 0.5 enforces observer mode)
    #  - Zero non-GBPUSD CAND blocked
    expected_gbpusd_all_blocked = (
        cts["gbpusd_cand"] == 0
        or cts["gbpusd_cand_blocked_new"] == cts["gbpusd_cand"]
    )
    non_gbpusd_safe = cts["non_gbpusd_cand_blocked_new"] == 0

    verdict = "EXPECTED_BEHAVIOR" if (
        tests.get("failed", 1) == 0
        and inv["all_match"]
        and expected_gbpusd_all_blocked
        and non_gbpusd_safe
    ) else "UNEXPECTED"

    result = {
        "branch": "worktree-agent-ad0a9ebd",
        "label": "A8 GBPUSD Gate 0.5",
        "tests": tests,
        "flags": flags,
        "synthetic_gate_verification": inv,
        "historical_replay": live,
        "verdict": verdict,
    }
    out = OUTDIR / "replay_a8_result.json"
    out.write_text(json.dumps(result, indent=2))
    print(f"\nResult file: {out}")
    print(f"\nVERDICT: {verdict}")
    return 0 if verdict == "EXPECTED_BEHAVIOR" else 1


if __name__ == "__main__":
    sys.exit(main())
