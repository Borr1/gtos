"""The P1 adapter's docs/ copy is a FROZEN BINDING ARTIFACT — pin it, byte for byte.

A0 relocation (2/2), Session FA continuation. The adapter's live development home is
``src/research_infra/wave20_complete_path_shadow.py`` (tests exercise that copy). The
original path under ``docs/.../phase20/receipts/`` CANNOT be vacated or edited: the frozen
canonical P1 packet records it as a ``packet_tooling`` descriptor, and
``p1_upstream_packet_verifier._verify_descriptor_set`` re-hashes that path FROM THE WORKING
TREE on every packet verification — so a byte of drift (or an absent file) makes the
canonical packet unverifiable and blocks P1's scheduled-on-need execution.

If a declared evolution ever changes the src/ copy, THIS file is where the divergence is
made explicit: the docs/ pin must stay exactly as-is; the equality assertion below is then
replaced (in the same commit, with the declaring receipt cited) by a pin of the new src
sha256 — never by deleting the check.
"""

from __future__ import annotations

import hashlib
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
DOCS_COPY = (
    REPO
    / "docs/audits/fable5-vision-audit-20260725/phase20/receipts/"
    / "wave20_complete_path_shadow.py"
)
SRC_COPY = REPO / "src/research_infra/wave20_complete_path_shadow.py"


def _runner_constants():
    import re

    text = (REPO / "src/research_infra/p1_offline_complete_path_runner.py").read_text(
        encoding="utf-8"
    )
    sha = re.search(r'ADAPTER_SHA256 = "([0-9a-f]{64})"', text).group(1)
    size = int(re.search(r"ADAPTER_BYTES = ([\d_]+)", text).group(1).replace("_", ""))
    return sha, size


def test_docs_copy_is_pinned_to_the_frozen_packet_binding():
    payload = DOCS_COPY.read_bytes()
    sha, size = _runner_constants()
    assert len(payload) == size
    assert hashlib.sha256(payload).hexdigest() == sha


def test_src_live_home_matches_docs_frozen_copy():
    # Byte equality at adoption. A future declared evolution of the src copy replaces this
    # assertion with a pin of the new sha (same commit, receipt cited) — see module docstring.
    assert SRC_COPY.read_bytes() == DOCS_COPY.read_bytes()
