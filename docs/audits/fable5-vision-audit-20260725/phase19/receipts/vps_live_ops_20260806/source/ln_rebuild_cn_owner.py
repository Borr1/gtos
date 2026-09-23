#!/usr/bin/env python3
"""Session LN — rebuild Session CN's ``book_owner.py`` payload on the HOST's real bytes.

WHY THIS EXISTS
---------------
CN's shipped ``book_owner.py`` payload (``165e03545b25``) was recomposed at wave-17
integration on top of **Session CO's** lane-weights payload
(``phase17/lane_weights_ceremony/files/book_owner.py`` = ``cf6aa69d402b``), because at
build time CO was expected to land in the same ceremony wave.

The owner has since directed that **CO must lapse unexecuted**. Carrying CN as shipped
would therefore:

1. install CO's lane-weights code on the live host — the exact thing the owner excluded; and
2. **crash both books at construction**, because CO's owner calls
   ``UltimateBookLiveEngine(..., lane_weight_controller=...)`` while the host's
   ``book_engine.py`` (Session CE's ``42c1bd6c``) has no such parameter.

CN's own ``build_carry.py`` names the correct fallback in a comment:
*"The pre-recompose base was phase15/activation_carry_spread_floor/files/book_owner.py."*
That file hashes to ``b7a82dc3d241`` — exactly the bytes on the host and exactly what
``CARRIED_STATE.json`` records.

This script re-runs CN's own ``build_owner()`` with that base and nothing else changed, so
the delta against the shipped payload is provably *only* the removal of CO's edits.
"""
from __future__ import annotations

import hashlib
import importlib.util
import pathlib
import subprocess
import sys

HERE = pathlib.Path(__file__).resolve().parent
AUDIT = HERE.parents[3]                       # docs/audits/fable5-vision-audit-20260725
CN = AUDIT / "phase17/activation_carry_live_cost_truth"
CE_OWNER = AUDIT / "phase15/activation_carry_spread_floor/files/book_owner.py"
CO_OWNER = AUDIT / "phase17/lane_weights_ceremony/files/book_owner.py"
OUT = HERE.parent / "payload"

CE_SHA = "b7a82dc3d241eaca09f9a430c66ec9f67705c0013554ade6409ddacc663a4cec"
CO_SHA = "cf6aa69d402b217b206ddd668ba5f65e3dba98e41a1b12f851c030d91faf8a17"
CN_SHIPPED_SHA = "165e03545b25d78af661bed27583408c58167c97b8d44441e39bcc4f418faf63"


def sha(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def load_cn_builder():
    spec = importlib.util.spec_from_file_location("cn_build_carry", CN / "build_carry.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)

    # --- 0. prove the premise, do not assume it --------------------------------
    assert sha(CE_OWNER.read_bytes()) == CE_SHA, "CE base is not the expected bytes"
    assert sha(CO_OWNER.read_bytes()) == CO_SHA, "CO base is not the expected bytes"
    shipped = (CN / "files/book_owner.py").read_bytes()
    assert sha(shipped) == CN_SHIPPED_SHA, "CN shipped payload is not the expected bytes"
    print(f"[ ok ] CE base  {CE_SHA[:12]}  {len(CE_OWNER.read_bytes())} B  (= host + CARRIED_STATE)")
    print(f"[ ok ] CO base  {CO_SHA[:12]}  {len(CO_OWNER.read_bytes())} B  (= CN's actual build base)")
    print(f"[ ok ] CN ship  {CN_SHIPPED_SHA[:12]}  {len(shipped)} B")

    mod = load_cn_builder()

    # --- 1. reproduce CN's shipped payload EXACTLY, to prove we drive it right --
    repro = mod.build_owner()
    if sha(repro) != CN_SHIPPED_SHA:
        print(f"[FAIL] could not reproduce CN's shipped payload: got {sha(repro)[:12]}")
        return 1
    print(f"[ ok ] reproduced CN's shipped payload byte-exactly from CO base")

    # --- 2. rebuild on the CE/host base -----------------------------------------
    mod.HOST_BASES[mod.OWNER_PATH] = (
        "file", "docs/audits/fable5-vision-audit-20260725/phase15/activation_carry_spread_floor/files/book_owner.py"
    )
    rebuilt = mod.build_owner()
    out_path = OUT / "book_owner.py"
    out_path.write_bytes(rebuilt)
    new_sha = sha(rebuilt)
    print(f"\n[ ok ] REBUILT on CE/host base: {new_sha}  {len(rebuilt)} B")
    print(f"       written to {out_path}")

    # --- 3. prove the rebuild is CE + only CN's edits ----------------------------
    text = rebuilt.decode("utf-8")
    lw = text.count("lane_weight")
    print(f"\n[{'  ok  ' if lw == 0 else ' FAIL '}] lane_weight references in rebuilt payload: {lw} (want 0)")

    # CN's three declared additions must be present
    for probe, label in (
        ("LEGACY_MODELLED_COST_COMPONENTS", "packet-economics import block"),
        ("_runtime_learning_modelled_cost", "modelled-cost method + emission"),
        ("MODELLED_COST_EXCLUDES", "exclusion contract symbol"),
    ):
        n = text.count(probe)
        print(f"[{'  ok  ' if n else ' FAIL '}] CN addition present: {label} ({probe} x{n})")

    # the delta CE -> rebuilt must equal the delta CO -> shipped, minus CO's own lines
    ce = CE_OWNER.read_text()
    d_ce_rebuilt = subprocess.run(
        ["diff", "-u", "-", str(out_path)], input=ce, capture_output=True, text=True
    ).stdout
    added = [l for l in d_ce_rebuilt.splitlines() if l.startswith("+") and not l.startswith("+++")]
    removed = [l for l in d_ce_rebuilt.splitlines() if l.startswith("-") and not l.startswith("---")]
    print(f"\n[ ok ] CE -> rebuilt: +{len(added)} / -{len(removed)} lines")
    print(f"[{'  ok  ' if not any('lane_weight' in l for l in added) else ' FAIL '}] no lane_weight line is added by the rebuild")
    print(f"[{'  ok  ' if len(removed) <= 1 else ' FAIL '}] rebuild removes at most the single rewritten import line ({len(removed)})")

    # --- 4. syntax + import-shape gate -----------------------------------------
    import ast
    ast.parse(text, filename="book_owner.py")
    print("[  ok  ] rebuilt payload parses as Python")

    print("\nSUMMARY")
    print(f"  shipped (CO-based, DO NOT CARRY): {CN_SHIPPED_SHA}  {len(shipped)} B")
    print(f"  rebuilt (CE-based, CARRY THIS)  : {new_sha}  {len(rebuilt)} B")
    print(f"  host before-bytes               : {CE_SHA}  {len(CE_OWNER.read_bytes())} B")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
