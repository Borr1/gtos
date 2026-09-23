#!/usr/bin/env python3
"""Permanently disabled legacy broad-replay entrypoint.

The executable S0R0 proof route moved to
``src.research_infra.replay_acceleration_attempt5_typed_sparse_runner``.
This path intentionally has no import or execution compatibility surface.
"""

from __future__ import annotations


def main() -> int:
    raise RuntimeError(
        "owner_override_legacy_replay_route_permanently_disabled_use_sealed_"
        "attempt5_typed_sparse_runner"
    )


if __name__ == "__main__":
    raise SystemExit(main())
