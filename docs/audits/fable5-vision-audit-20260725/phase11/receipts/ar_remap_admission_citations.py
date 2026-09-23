"""Session AR — remap every LIVE-CODE `admission.py:NNNN` citation my own edit invalidated.

    python3 docs/audits/fable5-vision-audit-20260725/phase11/receipts/ar_remap_admission_citations.py [--apply]

THE PROBLEM I CREATED
---------------------
CLAUDE.md's engineering rules say to cite `file:line` for production-state claims, and the estate
took that seriously: `admission.py` is cited by line from **61 places in live code** (`src/`,
`scripts/`, `tests/`) and ~102 more in committed receipts. Adding lines to the middle of it silently
invalidates every citation below the insertion — including citations no session in this wave wrote.
An adversarial pass found one: `book_replay.py:67` cited `admission.py:1313-1317` for the OPS-03
profit-target de-risk, which was correct at the merge-base and is not any more.

Mitigation already applied: the 76-line VOL_LEVEL_TILT comment block was moved to the END of
`admission.py`, which cut the shift from +82…+121 to +11…+49. This file repairs what remains.

WHY THIS IS SAFE, WHICH IS THE ONLY REASON TO AUTOMATE IT
---------------------------------------------------------
A line-number remap that guesses is worse than a stale citation, because a stale one at least fails
visibly when a reader opens the file. So the map is built from `difflib.SequenceMatcher` **equal
blocks only** — a line that CHANGED has no image and is reported rather than rewritten — and every
rewrite is then verified by **exact text identity**: the old file's line N and the new file's line
N' must be byte-identical strings. Anything that cannot be verified that way is printed and left
alone.

SCOPE, AND WHAT IS DELIBERATELY NOT TOUCHED
-------------------------------------------
`src/`, `scripts/`, `tests/` and AR's own `phase11/` artifacts — live code and my own work.

**Committed receipts under `docs/audits/.../phase1..phase10/` are NOT rewritten.** They are other
sessions' sealed evidence, and a citation in AN's or AO's result doc is a record of what was true
when that session measured it. Editing them would falsify a historical record to tidy a line number.
The shift table is published instead, so a reader of an older receipt can add the offset.
"""

from __future__ import annotations

import argparse
import difflib
import re
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[5]
TARGET = "src/components/ultimate_book/admission.py"
#: Live code and AR's own MEASUREMENT artifacts. Sealed receipts are excluded on purpose.
SCAN_DIRS = ("src", "scripts", "tests",
             "docs/audits/fable5-vision-audit-20260725/phase11")
EXTRA_FILES = ("run_book.py",)
#: EXCLUDED even inside phase11, and the reason is the same one that protects other sessions'
#: receipts. `VOL_LEVEL_TILT_DECLARATION_V1.json` and its writer were committed at `592b5be95` in a
#: commit containing NO economics, precisely so that "declared before it was priced" is a property of
#: git history. Rewriting a citation inside them afterwards changes the declaration's own sha256 and
#: destroys the only thing the early commit was for. A stale line citation in a time-sealed
#: declaration is CORRECT: it records what was true when the declaration was made. The first run of
#: this file rewrote them and the change was reverted to the committed bytes.
SEALED = ("VOL_LEVEL_TILT_DECLARATION_V1.json", "ar_tilt_declaration.py")
CITE = re.compile(r"(admission\.py:)(\d{3,4})(?:-(\d{3,4}))?")
#: `admission.py:1038-1040, :1170-1171` — a bare `:NNNN` only counts on a line that already names
#: admission.py, and only AFTER the first full citation on that line.
BARE = re.compile(r"(?<![\w.:/])(:)(\d{4})(?:-(\d{4}))?")


def build_map() -> tuple[dict[int, int], list[str], list[str]]:
    base = subprocess.run(["git", "merge-base", "HEAD", "main"], cwd=REPO,
                          capture_output=True, text=True).stdout.strip()
    old = subprocess.run(["git", "show", f"{base}:{TARGET}"], cwd=REPO,
                         capture_output=True, text=True).stdout.split("\n")
    new = (REPO / TARGET).read_text().split("\n")
    sm = difflib.SequenceMatcher(None, old, new, autojunk=False)
    m: dict[int, int] = {}
    for tag, i1, i2, j1, j2 in sm.get_opcodes():
        if tag != "equal":
            continue
        for k in range(i2 - i1):
            m[i1 + k + 1] = j1 + k + 1      # 1-indexed
    return m, old, new


def remap_line(n: int, m: dict[int, int], old: list[str], new: list[str]) -> int | None:
    """The new line number, or None when it cannot be VERIFIED by exact text identity."""
    j = m.get(n)
    if j is None or not (1 <= n <= len(old)) or not (1 <= j <= len(new)):
        return None
    return j if old[n - 1] == new[j - 1] else None


def already_remapped(p: Path, base: str) -> bool:
    """Has this file's citation set already been rewritten against the current `admission.py`?

    THE BUG THIS EXISTS FOR, and it is a real one this file shipped with. `sub_full` reads the
    citation's CURRENT value and treats it as an OLD line number. That is correct exactly once: on
    a second run the citations already hold NEW numbers, so remapping them again shifts them a
    SECOND time and silently points every one of them at the wrong code. The first `--apply` was
    verified correct (every rewritten citation points at byte-identical code to what it pointed at
    before); a second would have destroyed that quietly.

    The guard needs no state file: `git` already knows. If the file's citation values differ from
    its own merge-base version's, it has been remapped and must not be remapped again.
    """
    try:
        was = subprocess.run(["git", "show", f"{base}:{p.relative_to(REPO).as_posix()}"],
                             cwd=REPO, capture_output=True, text=True)
        if was.returncode != 0:
            #  A file that did not exist at the merge-base cannot hold merge-base-era citations, so
            #  there is nothing to remap: its author wrote it against a recent state of the file.
            #  Treated as already-correct rather than as remappable — the opposite of the tracked
            #  case, and the reason is the same, that a second shift is silent and destructive.
            return True
        return (sorted(CITE.findall(was.stdout)) != sorted(CITE.findall(p.read_text())))
    except (OSError, ValueError):
        return False


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true", help="write the files (default: dry run)")
    ap.add_argument("--force", action="store_true",
                    help="override the already-remapped refusal (you almost certainly do not "
                         "want this: a second pass double-shifts every citation)")
    args = ap.parse_args()
    m, old, new = build_map()
    _base = subprocess.run(["git", "merge-base", "HEAD", "main"], cwd=REPO,
                           capture_output=True, text=True).stdout.strip()
    print(f"{TARGET}: {len(old)} -> {len(new)} lines; {len(m)} lines have a verified image")

    files: list[Path] = []
    for d in SCAN_DIRS:
        files += [p for p in (REPO / d).rglob("*")
                  if p.is_file() and p.suffix in (".py", ".md", ".json", ".yaml", ".txt")]
    files += [REPO / f for f in EXTRA_FILES]

    n_files = n_cites = n_moved = n_guarded = 0
    unmapped: list[str] = []
    for p in sorted(set(files)):
        if p.resolve() == (REPO / TARGET).resolve() or p.name == Path(__file__).name:
            continue
        if p.name in SEALED:
            print(f"  SKIP (time-sealed) {p.relative_to(REPO)}")
            continue
        if not args.force and already_remapped(p, _base):
            n_guarded += 1
            continue
        try:
            text = p.read_text()
        except (UnicodeDecodeError, OSError):
            continue
        if "admission.py:" not in text:
            continue
        out_lines, changed = [], False
        for line in text.split("\n"):
            if "admission.py:" not in line:
                out_lines.append(line)
                continue
            head_end = line.index("admission.py:")

            def sub_full(mo: re.Match) -> str:
                nonlocal changed
                a, b = int(mo.group(2)), mo.group(3)
                ja = remap_line(a, m, old, new)
                if ja is None:
                    unmapped.append(f"{p.relative_to(REPO)}: admission.py:{mo.group(2)}"
                                    f"{'-' + b if b else ''} (line {a} has no verified image)")
                    return mo.group(0)
                jb = remap_line(int(b), m, old, new) if b else None
                if b and jb is None:
                    unmapped.append(f"{p.relative_to(REPO)}: admission.py:{a}-{b} "
                                    f"(end line {b} has no verified image)")
                    return mo.group(0)
                if ja == a and (not b or jb == int(b)):
                    return mo.group(0)
                changed = True
                return f"{mo.group(1)}{ja}" + (f"-{jb}" if b else "")

            new_line = CITE.sub(sub_full, line)

            def sub_bare(mo: re.Match) -> str:
                nonlocal changed
                if mo.start() < head_end:            # before the first admission.py mention
                    return mo.group(0)
                a, b = int(mo.group(2)), mo.group(3)
                ja = remap_line(a, m, old, new)
                jb = remap_line(int(b), m, old, new) if b else None
                if ja is None or (b and jb is None):
                    return mo.group(0)
                if ja == a and (not b or jb == int(b)):
                    return mo.group(0)
                changed = True
                return f":{ja}" + (f"-{jb}" if b else "")

            #  only on lines whose citation target is unambiguously admission.py
            if new_line.count("admission.py:") == 1 and ".py:" not in new_line.replace(
                    "admission.py:", "", 1):
                new_line = BARE.sub(sub_bare, new_line)
            out_lines.append(new_line)
        if changed:
            n_files += 1
            body = "\n".join(out_lines)
            n_here = sum(1 for a, b in zip(text.split("\n"), out_lines) if a != b)
            n_moved += n_here
            print(f"  {'WRITE' if args.apply else 'would fix'} {p.relative_to(REPO)}  "
                  f"({n_here} line(s))")
            if args.apply:
                p.write_text(body)
        n_cites += text.count("admission.py:")

    print(f"\n{n_cites} citation mentions scanned; {n_moved} line(s) in {n_files} file(s) "
          f"{'rewritten' if args.apply else 'would be rewritten'}")
    if n_guarded:
        print(f"{n_guarded} file(s) SKIPPED by the idempotency guard — their citations already "
              f"differ from their merge-base version, so they have been remapped once and a "
              f"second pass would double-shift them. See `already_remapped`.")
    if unmapped:
        print(f"\n{len(unmapped)} citation(s) could NOT be verified and were left alone "
              f"(a stale citation fails visibly; a guessed one does not):")
        for u in sorted(set(unmapped))[:25]:
            print("   ", u)
    print("\nNOT TOUCHED, deliberately: committed receipts under phase1..phase10 — other "
          "sessions' sealed evidence. The shift table is published in SESSION_AR_AB.md instead.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
