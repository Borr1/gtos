from __future__ import annotations

import importlib.util
import json
from pathlib import Path


MODULE_PATH = Path(__file__).with_name(
    "build_vnext_production_change_stage01_decision_surfaces_2026_05_25.py"
)
spec = importlib.util.spec_from_file_location("vnext_prod_stage01", MODULE_PATH)
stage01 = importlib.util.module_from_spec(spec)
assert spec.loader is not None
spec.loader.exec_module(stage01)


def main() -> int:
    result_path = stage01.REPO_ROOT / stage01.STAGE01_VERIFICATION_RESULT_PATH
    ledger_path = stage01.REPO_ROOT / stage01.DECISION_SURFACE_LEDGER_PATH
    state_path = stage01.REPO_ROOT / stage01.STATE_PATH
    result = json.loads(result_path.read_text(encoding="utf-8"))
    groups = [json.loads(line) for line in ledger_path.read_text(encoding="utf-8").splitlines() if line.strip()]
    summary = stage01.summarize_groups(groups)
    failures = stage01.verify(groups, summary)
    state = json.loads(state_path.read_text(encoding="utf-8"))
    if state["first_incomplete_invariant"] != "STAGE_02_PROMOTION_IMPLEMENTATION":
        failures.append("route state first incomplete invariant is not STAGE_02")
    if result.get("ok") is not True:
        failures.append("recorded Stage01 result is not ok")
    output = {
        "route_id": stage01.ROUTE_ID,
        "ok": not failures,
        "failures": failures,
        "ledger_path": stage01.rel(ledger_path),
        "group_count": summary["group_count"],
        "decision_map_row_count": summary["decision_map_row_count"],
        "first_incomplete_invariant": state["first_incomplete_invariant"],
    }
    print(json.dumps(output, indent=2, sort_keys=True))
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
