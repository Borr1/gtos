"""Write known original stops onto trade records. Never overwrite a kept orig."""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

_REPO = Path(__file__).resolve().parents[2]
if str(_REPO) not in sys.path:
    sys.path.insert(0, str(_REPO))

from scripts.f5_desk import chair_ledger, common

SEED = {
    "179105152": 53570.32,
    "179079162": 26397.66,
    "179108943": 1.16598,
}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo-root", type=Path, default=_REPO)
    args = parser.parse_args(argv)
    repo = Path(args.repo_root)
    path = chair_ledger.orig_path(repo)
    existing = chair_ledger.load_orig_ledger(path)
    for ticket, sl in SEED.items():
        if ticket not in existing:
            existing[ticket] = sl
    common.write_json_atomic(path, {"tickets": existing, "updated_utc": common.iso_utc()})
    wrote = []
    skipped = []
    missing = []
    for ticket, sl in existing.items():
        rec = repo / "pipeline_state" / "ultimate_book" / common.NAMESPACE / "trade_records" / f"{ticket}.json"
        if not rec.is_file():
            missing.append(ticket)
            continue
        if chair_ledger.write_trade_record_orig(repo, ticket, sl):
            wrote.append(ticket)
        else:
            skipped.append(ticket)
    print({"ledger": existing, "wrote": wrote, "skipped_already": skipped, "missing_record": missing})
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
