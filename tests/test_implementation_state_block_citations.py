"""Every `B<n>` block citation must resolve to a block that exists.

A ghost reference points at a fact that has moved. `B58` was cited 34 times across 17 files —
including `CLAUDE.md`, `AGENTS.md` and four session prompts — and no B58 block has ever existed in
any revision of `IMPLEMENTATION_STATE.md`. Nobody noticed for two waves, because a dangling citation
reads exactly like a live one: the reader believes there is evidence behind it and never checks.

That is the same class as the vacuous tests this session removed — a signal that says "checked"
where nothing was checked — so it gets the same treatment: a mechanism that catches the class rather
than a one-time fix of the instances.

The allowlist below is the point. It can SHRINK (fix a ghost, remove its entry) but it cannot
silently GROW: adding a citation to a non-existent block fails this test, and the only way to make it
pass is to state the ghost explicitly in the allowlist with a reason someone has to read.
"""
from __future__ import annotations

import collections
import pathlib
import re

REPO = pathlib.Path(__file__).resolve().parents[1]
STATE = REPO / "docs/audits/fable5-vision-audit-20260725/IMPLEMENTATION_STATE.md"

#: A block definition. Two written forms, both real, and the second was invisible until 2026-07-29.
#:
#:   `### B99e — ...`      an ATX heading (waves 1-3, most sessions)
#:   `**B220 — ...**`      a bold lead-in at the start of a paragraph
#:
#: Session P wrote **all 22** of its blocks (B200-B221) in the second form under a single
#: `## B200–B219` section heading, so `_defined_blocks` saw exactly one of them. Nothing noticed,
#: because B201-B219 sat inside the in-flight wave range and B220-B221 sat above the ceiling — two
#: exemptions covering for a parser gap rather than for unwritten work. It surfaced only when
#: Session T's B320+ raised the ceiling and B220/B221 fell out of both.
#:
#: Recognising both forms is the honest repair: those blocks ARE written, and rewriting 22
#: paragraphs of merged prose to satisfy a regex would be the wrong direction.
#:
#: **Found independently by Sessions S and T on the same day, byte-identical regex, different
#: reasoning** — S from P's blocks, T from its own ceiling — and by Session R from the third side
#: (R kept the parser and widened the exemption instead). That is wave 3's failure mode #4 repeating:
#: three sessions paid for one discovery. Recorded here rather than in a report so the next reader of
#: this file knows the fix has three authors. Session Q and Session R also write bold-form blocks, so
#: after wave-4 integration this regex is what makes B230-B244 and B260-B289 visible at all.
_BLOCK_HEADER = re.compile(r"^(?:#{2,4}\s+|\*\*)(B\d+[a-z]?)\b", re.M)

#: A lead-in that defines MORE THAN ONE id: `**B274/B275 — ...**`.
#:
#: Session R wrote one block for a pair of findings that share a single refutation, and labelled the
#: two halves `[B274]` and `[B275]` inside it. That is a reasonable thing to write. A single-id
#: parser defines B274, leaves B275 undefined, and B275 then reads as a citation to evidence that
#: does not exist — a ghost manufactured by the reader, not by the writer. Found at wave-4
#: integration (Session U, B352) the moment `_BLOCK_HEADER` learned the bold form and R's section
#: became visible at all.
#:
#: Same principle as the bold form above: the blocks ARE written, so teach the parser the shape
#: rather than rewrite the prose.
_BLOCK_HEADER_MULTI = re.compile(r"^(?:#{2,4}\s+|\*\*)(B\d+[a-z]?(?:/B\d+[a-z]?)+)\b", re.M)

#: A lead-in that defines a RUN of ids: `**B1668–B1670 — receipts.**`.
#:
#: Third instance of the same class as the two above, and the third time the honest repair is to
#: teach the parser a shape the file already uses rather than rewrite prose. Sessions AV and AW
#: both wrote receipt/declaration blocks this way — one paragraph covering a small run — so
#: `B1669`, `B1670`, `B1784` and `B1785` were defined in the document and invisible to the
#: scanner. Found by Session AW (B1750-B1785): the moment its own blocks raised the ceiling past
#: B1670, `WAVE_11_WORKING_AGREEMENT.md`'s citation of B1670 fell out of the forward-allocation
#: exemption and read as a ghost, when the block was written 200 lines above it.
#:
#: TWO restrictions, and both are load-bearing:
#:
#: 1. **Bold form only.** `## B1750–B1799 — Session AW` is a section heading announcing an
#:    ALLOCATION, not a definition of fifty blocks. Sixteen such headings exist; expanding them
#:    would define ~700 ids nobody wrote and make this whole file vacuous.
#: 2. **The dash must be set CLOSE.** `**B215 — B200's conclusion was too strong**` is prose
#:    about an earlier block, and it is *descending*; a spaced dash is never a range in this
#:    document. Three bold lead-ins have that shape and none may expand. The `lo < hi` guard
#:    below is the belt to that braces.
#:
#: Verified against the file at the time of writing: the tight bold form matches exactly five
#: runs (B1618-B1622, B1634-B1646, B1653-B1660, B1668-B1670, B1783-B1785), all genuine.
_BLOCK_HEADER_RUN = re.compile(r"^\*\*(B\d+)[–—-](B\d+)\b", re.M)

#: A citation. Bounded on the left so route names like `V122_FABLE_B0_PROVENANCE` do not match, and
#: on the right so `B7_5` (the campaign, not a block) does not read as block `B7`.
_CITATION = re.compile(r"(?<![0-9A-Za-z_])(B\d+[a-z]?)(?![0-9A-Za-z_])")

#: A range boundary, e.g. `B80–B89` or `B140-B149`. The upper bound of an ALLOCATED range is allowed
#: to be unused — a session that finishes early does not owe the numbering a filler block.
_RANGE = re.compile(r"(?<![0-9A-Za-z_])B\d+[a-z]?\s*[–—-]\s*(B\d+[a-z]?)(?![0-9A-Za-z_])")

#: Paths excluded from the scan, each for a stated reason.
_EXEMPT_PREFIXES = (
    ".git/",
    # Generated pre-replay briefs, archived. They use `B0`/`B3`/`B7_5` as CAMPAIGN-PHASE labels from a
    # different vocabulary that predates this block index entirely.
    ".context/context_os/",
    # Route evidence with its own `B0..Bn` build-phase vocabulary (PORTFOLIO_BUILD_W*.md). Scanning it
    # would report every build phase as a dangling block citation — a probe finding its own noise.
    "research/operations/",
    # Third-review reader receipts, several of which DESCRIBE the B58 ghost and must be able to name it.
    "docs/audits/fable5-vision-audit-20260725/third_review_receipts/",
)

#: Known dangling citations, each with why it is still here. MUST SHRINK, NEVER GROW.
KNOWN_GHOSTS: dict[str, str] = {
    "B0": (
        "Not a citation to evidence — a WAVE20 preregistration NODE ID. "
        "`phase20/WAVE20_SCIENCE_PREREGISTRATION.md` names its DAG nodes G0/S0/B0/B1/O1/C0/N1/"
        "F1/K1/P1, and the three session result docs that landed with the wave-20 chain "
        "(SESSION_HK_CRITICAL_PATH_PREFLIGHT_RESULT.md, SESSION_HL_P1_ADAPTER_BUILDER_RESULT.md, "
        "SESSION_HP_P1_UPSTREAM_FALSIFIER_REDUCTION_RESULT.md) cite the node by its bare name. "
        "This collision was PREDICTED before landing (FA_CONTINUATION_VERIFIED_STATE.md §7 "
        "node-id note) with exactly this remedy prescribed: an exemption with a stated reason, "
        "the same class as the archived pre-replay briefs — never a hand-edit of the frozen "
        "prereg. Later forensic docs write the node as `WAVE20_B0` to stay out of this "
        "scanner's vocabulary. Delete this entry if a real B0 evidence block is ever allocated "
        "(it should never be: block numbering started at B1)."
    ),
    "B2086": (
        "Not a citation to evidence — a SELF-CORRECTION. "
        "`phase13/SESSION_BD_LIVE_DEBT_SWEEP_RESULT.md` §6 records verbatim that three of "
        "Session BD's commit messages named block ranges written *before* the blocks were "
        "(`B2050-B2085`, `B2086-B2093`, `B2094-B2095`), that the authoritative numbering is "
        "**B2050 to B2075 contiguous**, and that git history is immutable so the wrong strings "
        "stay. The result doc quotes the wrong ranges IN ORDER TO CORRECT THEM, which the "
        "scanner cannot distinguish from a reference. Same shape as B1976 (a verbatim commit "
        "subject inside BB's receipt fence). Surfaced 2026-07-31 when Session CA wrote to "
        "B2149 and moved the ceiling past BD's tail — the exact failure mode AU's B1593 "
        "amendment describes. Delete this entry if a real B2086 is ever allocated."
    ),
    "B2094": (
        "See B2086 — the same self-correcting sentence names both numbers."
    ),
    "B410": (
        "Not a citation. WAVE_4_WORKING_AGREEMENT.md \u00a74 writes \"The gap `B410+` is deliberate "
        "slack, not an allocation\" \u2014 it names a number precisely to say nothing occupies it. "
        "The guard cannot distinguish a reference to evidence from a statement that a range is "
        "reserved-and-empty, so this is the intended use of KNOWN_GHOSTS rather than a defect in "
        "either document. Delete this entry if a real B410 is ever allocated."
    ),
    "B69a": (
        "Not a citation. WAVE_2_WORKING_AGREEMENT.md uses B69a/B69b as ILLUSTRATIVE EXAMPLES of the "
        "letter-suffix convention, and the numbering note in IMPLEMENTATION_STATE.md quotes them "
        "while recording that they are not ghosts."
    ),
    "B69b": (
        "See B69a — the same illustrative pair, used to show that two sessions sharing a number "
        "disambiguate with letter suffixes rather than renumbering."
    ),
    "B58": (
        "Skipped in the wave-2 renumbering; the per-account daily-loss-reset content it is always "
        "cited for lives in B56. Repointed in CLAUDE.md, AGENTS.md and IMPLEMENTATION_STATE.md's "
        "B91 on 2026-07-27. The remaining holders include four session prompts that were being "
        "executed at that moment; editing a prompt underneath a running session is a worse defect "
        "than the dangling citation. Resolved for readers by the numbering note at the head of "
        "IMPLEMENTATION_STATE.md."
    ),
    "B2086": (
        "Not an evidence citation, and BD said so first. Surfaced 2026-07-31 (CC, B2200-B2228) "
        "when this session's blocks moved the ceiling past BD's floor. Two sources, both "
        "legitimate: `phase13/SESSION_BD_AB.md:110` embeds a gtos-ab-receipt-v1 fence whose "
        "metadata quotes a commit subject VERBATIM ('B2086-B2093'), and the fence is "
        "self-contained evidence that must not be edited (same shape as B1976); and "
        "`SESSION_BD_LIVE_DEBT_SWEEP_RESULT.md:304` names the range precisely to record that it "
        "does NOT resolve -- BD's own correction paragraph, 'do not cite a block number until "
        "the block exists'. The authoritative numbering is B2050-B2075 contiguous. Delete this "
        "entry if a real B2086 is ever allocated."
    ),
    "B2094": (
        "Same paragraph, same correction: `SESSION_BD_LIVE_DEBT_SWEEP_RESULT.md:305` quotes the "
        "commit-message range 'B2094-B2095' in the act of saying it resolves to nothing. See "
        "B2086. Delete this entry if a real B2094 is ever allocated."
    ),
    "B1976": (
        "Not an evidence citation. SESSION_BB_AB.md embeds its gtos-ab-receipt-v1 fence, whose "
        "metadata quotes a commit subject verbatim: 'B1976-B1999'. The subject named the range "
        "BB planned for its second deliverable; the fence is self-contained evidence and must "
        "not be edited (the self-containment guard exists precisely so its bytes are the "
        "capture's bytes). Delete this entry if that receipt is ever regenerated through the "
        "tool with a resolvable subject."
    ),
    "B59": (
        "Same wave-2 renumbering gap. Cited once, in a third-review reader receipt that is "
        "DESCRIBING the gap."
    ),
    # CB independently added B2086/B2094 entries here (it raised the ceiling the same day CA
    # did); CA's copies above survive the union — one key, one reason, per the dict's own rule.
    # B230 was here, added by Session R (B278) while Session Q's blocks sat on an unmerged branch.
    # Q merged at wave-4 integration, B230 is defined, and R's own entry said this was the moment to
    # delete it. Deleted 2026-07-29 (Session U). The allowlist shrank, which is the only direction
    # it is allowed to move.
    "B1786": (
        "Not a citation, and the same asymmetry as B1484 — surfaced 2026-07-30 (AY, B1841) when "
        "AY's blocks moved the ceiling past AW's floor. `phase12/receipts/SESSION_AW_AB.md:76` "
        "reads **B1786–B1799 is cited nowhere as an individual token**: AW naming a range "
        "precisely to record that nothing occupies it, in the note retiring its own in-flight "
        "entry. `_RANGE` exempts a range's UPPER bound and not its lower, so the sentence "
        "asserting the range is empty is itself read as a citation of its first member. The "
        "sentence is true and the guard is right not to guess; this is what KNOWN_GHOSTS is for. "
        "Delete this entry if a real B1786 is ever allocated."
    ),
    "B1484": (
        "Not a citation. `phase11/SESSION_AR_CONDITIONING_TO_SIZING_RESULT.md:790` reads "
        "**B1484-B1499 unused.** — it names a number precisely to say nothing occupies it, which is "
        "the same shape as B410. `_RANGE` exempts a range's UPPER bound (a session that finishes "
        "early owes the numbering no filler block) and not its lower, so the lower bound of an "
        "explicitly-empty range reads as a ghost. Added 2026-07-30 (AU, B1593) when AU's ceiling "
        "moved past AR's floor and made AR's whole tail visible to the scanner. Delete this entry if "
        "a real B1484 is ever allocated."
    ),
    "B410": (
        "Not a citation and never will be a block. WAVE_4_WORKING_AGREEMENT.md:79 says of it "
        "verbatim: 'The gap B410+ is deliberate slack, not an allocation.' It reads as a dangling "
        "citation only because `_CITATION` cannot see that the sentence around it is a DENIAL that "
        "the block exists. It was invisible while the ceiling sat above 410 and surfaced the moment "
        "wave 5 wrote past it — see the note on IN_FLIGHT_WAVE_RANGES below, which is the same "
        "failure. Delete this entry if that sentence is ever reworded to avoid the literal token."
    ),
}


def _tracked_markdown() -> list[pathlib.Path]:
    out = []
    for p in REPO.rglob("*.md"):
        rel = p.relative_to(REPO).as_posix()
        if any(rel.startswith(x) for x in _EXEMPT_PREFIXES):
            continue
        out.append(p)
    return sorted(out)


def _defined_blocks() -> set[str]:
    text = STATE.read_text()
    defined = set(_BLOCK_HEADER.findall(text))
    for run in _BLOCK_HEADER_MULTI.findall(text):
        defined.update(run.split("/"))
    for lo, hi in _BLOCK_HEADER_RUN.findall(text):
        lo_n, hi_n = int(lo[1:]), int(hi[1:])
        # A descending or equal pair is prose, not a run. `**B240 — B161's ... **` would only
        # reach here through a typography change, and the cheapest place to refuse it is here.
        if lo_n < hi_n:
            defined.update(f"B{n}" for n in range(lo_n, hi_n + 1))
    return defined


def _num(cid: str) -> int:
    return int(re.match(r"B(\d+)", cid).group(1))


def _is_block_shaped(cid: str, defined: set[str]) -> bool:
    """Reject prose that merely looks like a block id.

    `B29s` (a plural) and `B5x` (a wildcard) match the citation pattern but are not references.
    Rather than hardcode which letters are real, derive the allowed suffixes from the suffixes the
    defined blocks ACTUALLY use — so the rule maintains itself as the numbering grows.
    """
    suffix = cid[1:].lstrip("009")
    if not suffix:
        return True
    used = {b[1:].lstrip("009") for b in defined} - {""}
    return suffix in used


def _citations(defined: set[str] | None = None) -> dict[str, list[str]]:
    """id -> repo-relative files citing it, excluding range bounds and prose look-alikes."""
    defined = _defined_blocks() if defined is None else defined
    found: dict[str, list[str]] = collections.defaultdict(list)
    for p in _tracked_markdown():
        try:
            text = p.read_text()
        except (OSError, UnicodeDecodeError):
            continue
        range_bounds = set(_RANGE.findall(text))
        for cid in set(_CITATION.findall(text)):
            if cid in range_bounds or not _is_block_shaped(cid, defined):
                continue
            found[cid].append(p.relative_to(REPO).as_posix())
    return found


#: The block range allocated to the wave currently in flight, per WAVE_3_WORKING_AGREEMENT.md §6
#: ("Wave 3 runs B100–B149"). Sessions inside a wave run in PARALLEL and write their blocks out of
#: order, so "above the highest written block" is the wrong model — Session M wrote B140–B149 while
#: B100–B139 were still unwritten by four sibling sessions. Ids inside this range are allocations, not
#: dangling evidence claims. **Retire this constant when the wave lands**; `test_the_in_flight_wave_range_is_declared_and_shrinking`
#: fails once every id in it is written, which is the signal to do so.
#: Advanced 2026-07-28 at wave-3 integration (B187), from (100, 149). Every block in B100–B149 had
#: landed, so the old range excused nothing and this test — correctly — went red.
#:
#: Became a LIST of (range, agreement) pairs 2026-07-29 (Session R, B273), because one tuple cannot
#: express two disjoint in-flight waves, and each range must name the document that declares it —
#: a single module-level pointer goes stale the moment two waves overlap.
#:
#: **Collapsed back to ONE entry at wave-4 integration (Session U, B352), and the reason is that
#: everything the other entries covered is now WRITTEN.** R needed `(200, 221)` because
#: `_defined_blocks` could not see P's bold-form blocks; `_BLOCK_HEADER` can see them now, so
#: B200–B221 are defined and an exemption for them would be a hole, not a courtesy. R's `(260, 349)`
#: and S's and T's `(230, 349)` covered Q/R/S/T, all four of which merged in this session. What is
#: genuinely in flight is Session V (`B380–B409`, branch `phase4/armed-set-mc`, unmerged), and
#: Session U's own `B350–B379`, which are written as they are used.
#:
#: The retirement rule is unchanged and is what forces this: an entry whose every block is written
#: makes `test_the_in_flight_wave_range_is_declared_and_shrinking` go red. Do not widen a range to
#: silence it — drop the entry.
#: RETIRED 2026-07-29 (Session Y): ``((380, 409), "WAVE_4_WORKING_AGREEMENT.md")`` — V merged, and
#: with wave 5 writing past B443 that entry sat below the ceiling exempting nothing, which the DEAD
#: check below exists to catch.
#:
#: **This list is the wave's own responsibility and it was not handed over.** Both of this module's
#: range tests were ALREADY RED at `82f8e02dc` before Session Y appended a line — verified by
#: restoring HEAD's `IMPLEMENTATION_STATE.md` and re-running. The mechanism is worth stating because
#: it will recur every wave: a session lands blocks, the ceiling rises past a *later* session's
#: allocation, and that allocation stops being covered by the "above the ceiling" exemption on a
#: commit that never mentions it. Session W landing B420-B449 is what pushed X's B450 under the
#: ceiling. **Whoever raises the ceiling owns this list**, not whoever trips over it next.
#: Wave 6 added an entry on 2026-07-29 (Session AB, B672), and the mechanism worked exactly as
#: designed. AB wrote B650–B671 while Session AA's B600–B649 were still unwritten on a sibling
#: branch. That raised the ceiling past AA's allocation, so `B600` — cited by
#: `WAVE_6_WORKING_AGREEMENT.md` §6 and `phase6/SESSION_AA_ESTATE_WALK.md` — stopped being a
#: forward reference and became a dangling one, and this test went red in AB's full-suite A/B.
#: The citation is not wrong; the ceiling model is, for parallel waves, which is the whole reason
#: this constant exists. AG's `B700–B749` needs no entry: it sits above the ceiling either way.
#: RETIRED 2026-07-30 (Session AD, B755): ``((600, 649), "WAVE_6_WORKING_AGREEMENT.md")`` — AA
#: merged at `1f10eb637` and AG wrote to B720, so that entry sat below the ceiling exempting
#: nothing. Session AE dropped the same dead entry independently on its own branch, for the same
#: reason, in the same hour — the mechanism is now well enough understood that two sessions repair
#: it without coordinating.
#:
#: Wave-7 train merge, 2026-07-30 (orchestrator). AD, AF, AE and AT all landed in one train, so
#: this list is resolved from the MERGED state rather than from either branch's vantage. The three
#: wave-7 ranges all came out DEAD by this file's own check — each session's unwritten tail
#: (AD wrote B750–B757 of 799, AF B800–B818 of 849, AE B850–B883 of 899) is cited nowhere as an
#: individual token; the agreement's `B750–B799` form is a RANGE declaration, and `_RANGE` upper
#: bounds are excused without needing an in-flight entry. So the only honest entry left is AK's
#: PRE-DECLARATION: allocated in `WAVE_7_WORKING_AGREEMENT.md` §5, un-launched, entirely above the
#: ceiling today (B912), and it starts working the moment a wave-8 sibling writes past B950.
#: Whoever raises the ceiling past 950 owns this list — the mechanism above, unchanged.
#: RETIRED 2026-07-30 (Session AK, B980): ``((950, 999), "WAVE_7_WORKING_AGREEMENT.md")`` — AK
#: launched and wrote B950–B979, which raised the ceiling to B979 and made its own entry DEAD by the
#: check below (nothing in 950–999 is cited-but-unwritten at or under the ceiling). The rule is "drop
#: it", not "widen it", and the mechanism found it on the first run after the blocks landed.
#:
#: Replaced by the two wave-8 siblings, both PRE-DECLARATIONS in the docstring's own sense: AH's
#: ``B1000–B1049`` and AI's ``B1050–B1099`` are declared as single allocations in
#: ``WAVE_8_WORKING_AGREEMENT.md`` §5, both sit entirely above the B979 ceiling today, and both
#: start working the moment a sibling writes past 1000. **Whoever raises the ceiling owns this
#: list** — AK raised it from B912 to B979 and is therefore the session that owes these two entries,
#: exactly as the mechanism above describes. AK's own range needed no successor entry: its unwritten
#: tail B980–B999 is cited nowhere as an individual token, and the agreement's ``B950–B999`` form is
#: a RANGE declaration, whose upper bound ``_RANGE`` already excuses.
#: Wave-9 pre-declarations, 2026-07-30 (orchestrator, at the wave-8 train merge). All three
#: wave-8 entries came out DEAD at the merged state — every session's unwritten tail is cited
#: nowhere as an individual token — and wave 9 (AL `B1150–B1199`, AM `B1200–B1249`,
#: `WAVE_9_WORKING_AGREEMENT.md` §5) was commissioned in the same resolution, so these two sit
#: above the B1101 ceiling as PRE-DECLARATIONS and start working when a sibling writes past them.
#: **AL's ``B1150–B1199`` entry was RETIRED by AL itself, 2026-07-30, and the mechanism is what
#: retired it.** AL wrote B1150–B1169, which raised the ceiling to B1169 — above its own range's
#: floor — and it cites no unwritten block inside 1150–1199, so its entry became DEAD in the
#: docstring's exact sense: below the ceiling and exempting nothing the ceiling does not already
#: exempt, i.e. a hole waiting for a typo. `test_the_in_flight_wave_range_is_declared_and_shrinking`
#: caught it on the first run after the blocks landed and named the remedy in its own assertion
#: message ("Drop it"), which is the whole point of the ACTIVE / PRE-DECLARATION / DEAD split
#: Session U's adversarial pass added. AL's unwritten tail B1170–B1199 needs no successor entry for
#: the same reason AK's did not: it is cited nowhere as an individual token, and the agreement's
#: ``B1150–B1199`` form is a RANGE declaration whose upper bound ``_RANGE`` already excuses.
#: AM's entry stays — it sits entirely above B1169 and is still a live pre-declaration.
#:
#: **AO's ``B1300–B1349`` entry was RETIRED by AO itself, 2026-07-30, by the same mechanism that
#: retired AL's** — and this time the retirement was predictable from the agreement rather than a
#: surprise. AO wrote B1300–B1343, raising the ceiling from B1241 to B1343, so its own entry fell
#: below the ceiling while citing no unwritten block inside 1300–1349: DEAD in the docstring's exact
#: sense. The test caught it on the first run after the blocks landed and named the remedy in its
#: assertion message. AO's unwritten tail B1344–B1349 needs no successor entry for the reason AK's
#: and AL's did not: it is cited nowhere as an individual token, and ``B1300–B1349`` is a RANGE
#: declaration whose upper bound ``_RANGE`` already excuses.
#:
#: **AN's entry changes CLASS rather than going away, and that is why AO owns this list.**
#: `WAVE_10_WORKING_AGREEMENT.md` §5 says "whoever raises the ceiling past a sibling owns
#: `IN_FLIGHT_WAVE_RANGES`", and B1343 is past AN's 1250–1299. Before AO's blocks landed AN's entry
#: was a PRE-DECLARATION (1250 > the B1241 ceiling); it is now **ACTIVE** — it sits below the
#: ceiling and does real work, exempting the individual-token citations of AN's own unwritten blocks
#: that `phase10/SESSION_AN_POPULATION_RULE.md` makes. It must stay until AN's blocks land, and it
#: is the entry a future session should check first: the moment AN writes past its own floor and
#: stops citing an unwritten token inside its range, the same test will call it DEAD too.
IN_FLIGHT_WAVE_RANGES: list[tuple[tuple[int, int], str]] = [
    # AM's (1200, 1249) retired at the wave-9 train merge — B1241 landed, tail uncited (DEAD).
    # AN's (1250, 1299) retired here: B1250-B1266 are written, which puts the range at or below
    # the block ceiling while exempting nothing the ceiling does not already exempt — DEAD by this
    # test's own definition, and the remedy it names is to drop the entry. Same retirement AL made.
    # AO's (1300, 1349) retired at the wave-10 train merge — B1300-B1349 are written (DEAD).
    # AP's (1350, 1399) retired at the wave-11 train merge — B1350-B1385 written (DEAD).
    # AQ's (1400, 1449) and AR's (1450, 1499) retired at the wave-11 train merge — B1400-B1453
    # and B1450-B1499 are written (AQ borrowed B1450-B1453 from AR's floor; both sets exist, DEAD).
    # AMENDED 2026-07-30 (AU, B1593): that retirement said "written" and meant "written SOMEWHERE".
    # B1454-B1483 are written in AR's RESULT DOC and were never in IMPLEMENTATION_STATE.md, which the
    # guard could not see while they sat above the B1453 ceiling. AU wrote to B1592, the ceiling
    # moved, and 23 of them became dangling in one commit. Resolved by an index-pointer lead-in in
    # IMPLEMENTATION_STATE.md, not by re-authoring AR's findings. A range retired on "the blocks are
    # written" should be retired on WHERE they are written. (AV independently hit the same case and
    # restored AR's entry as ACTIVE on its branch; at the train merge AU's index-pointer resolution
    # governs, so the entry stays retired.)
    # AU's (1550, 1599) retired by its own author: B1550-B1593 are written. AS's (1500, 1549)
    # retired at the wave-12 train merge — B1500-B1548 are written. AV's (1600, 1649) retired by
    # its own author — B1600-B1670 are written. AV OVERRAN its range into AW's pre-declared
    # (1650, 1699); AW had not started, so AW is RENUMBERED to (1750, 1799) at the train merge.
    # AW's (1750, 1799) retired by its own author, 2026-07-30, by the same mechanism that retired
    # AL's and AO's: B1750-B1785 are written in IMPLEMENTATION_STATE.md (not merely in a result
    # doc — AU's B1593 amendment is the reason that distinction is spelled out), which puts the
    # range at or below the ceiling while it cites no unwritten token inside itself. DEAD in this
    # test's exact sense. Its tail B1786-B1799 needs no successor entry for the reason AK's, AL's
    # and AO's did not: cited nowhere as an individual token, and `B1750–B1799` is a RANGE
    # declaration whose upper bound `_RANGE` already excuses.
    # AX's (1700, 1749) retired at the wave-12b train merge — B1700-B1749 written (DEAD).
    # The whole run-all wave retired at the wave-13 train merge (2026-07-31): AY B1800-B1841,
    # AZ B1850-B1899, BA B1900-B1913, BB B1950-B1999, BC B2000-B2049, BD B2050-B2075 are all
    # written in IMPLEMENTATION_STATE.md — DEAD entries per this test's definition, dropped per
    # its own remedy. Uncited tails need no successor entries.
    # CA's (2100, 2149) and CB's (2150, 2199) retired at the wave-14 train merge, 2026-07-31:
    # B2100-B2149 and B2150-B2164 are written in IMPLEMENTATION_STATE.md (not merely in result
    # docs — AU's B1593 amendment is why that distinction is spelled out), so both ranges sit at
    # or below the ceiling while citing no unwritten token — including their own LOWER bounds,
    # which `_RANGE` does not excuse (B1786's lesson, re-learned by Session CC on its unmerged
    # branch where the siblings' blocks did not yet exist: there the entries had to stay ACTIVE,
    # here they are DEAD; the class of an entry is a property of the tree, not of the session).
    # CB's tail B2165-B2199 needs no successor entry: cited nowhere as an individual token, and
    # `B2150–B2199`'s upper bound `_RANGE` already excuses. CC's own (2200, 2249) is dead the
    # same way — B2200 is defined. Both CA and CB independently surfaced BD's B2086/B2094; one
    # KNOWN_GHOSTS entry each survives the union (CA's wording, first merged).
    # CD's (2250, 2299) was CC's PRE-DECLARATION, changed CLASS to ACTIVE at CE's ceiling raise
    # (B2250 cited as an individual token in six files), and is now retired BY ITS OWN AUTHOR,
    # 2026-07-31: B2250-B2274 are written in IMPLEMENTATION_STATE.md — not merely in a result
    # doc, AU's B1593 distinction — so the range sits at or below the ceiling while citing no
    # unwritten token inside itself, including its own LOWER bound, which `_RANGE` does not
    # excuse (B1786). DEAD in this test's exact sense, dropped per its own remedy. Its tail
    # needs no successor entry: cited nowhere as an individual token, and `B2250–B2299` is a
    # RANGE declaration whose upper bound `_RANGE` already excuses.
    # CD's branch, seeing an empty table, also built the `NO_WAVE_IN_FLIGHT` declared-empty
    # mechanism (kept below — a genuine improvement); on merged main the table was never empty:
    # CE's own (2300, 2349) retired by its author the same day; CF/CG/CH/CI follow.
    ((2350, 2399), "WAVE_11_WORKING_AGREEMENT.md"),  # CF — symbol-rename watchdog (wave 15)
    # CG's own (2400, 2449) retired when B2400-B2401 landed: like AY/AL/AO/AW, writing its
    # lower bound moved the allocation at or below the ceiling while it exempts no unwritten
    # individual-token citation. The range declaration still excuses the uncited tail.
    # CH's own (2450, 2499) is RETIRED by its own author, 2026-07-31. B2450-B2467 are
    # written in IMPLEMENTATION_STATE.md; the unused tail is cited only as a range boundary,
    # which `_RANGE` already handles, so keeping this entry would be a DEAD exemption.
    # CI's own (2500, 2549) is RETIRED by its own author: B2500 is now written in
    # IMPLEMENTATION_STATE.md, which puts the range at or below the ceiling while it cites no
    # unwritten individual token inside itself. Its tail needs no exemption unless a later document
    # cites one of those ids individually; the allocation range's upper bound is already excluded by
    # `_RANGE`, exactly as for CE above.
    # CJ's own (2550, 2599) is RETIRED at its merge, 2026-08-01: B2550+ are written in
    # IMPLEMENTATION_STATE.md (CJ's branch removed the row silently; this comment records why).
    # The uncited tail is covered by `_RANGE`, exactly as for CE/CK above.
    # CM's own (2700, 2749) is RETIRED by its author, 2026-08-01: B2700-B2716 are written in
    # IMPLEMENTATION_STATE.md. The unused tail is cited only as an allocation range, whose upper
    # bound `_RANGE` already excludes it; retaining the entry would be a DEAD exemption.
    # CN's own (2750, 2799) is RETIRED by its author: B2750-B2762 and the result doc are
    # committed, while the uncited tail is already covered by the allocation-range exemption.
    # CO's own (2800, 2849) is RETIRED by its own author, 2026-08-01. B2800-B2813 are
    # written in IMPLEMENTATION_STATE.md, so the range is at or below the ceiling and its
    # unused tail is cited only as a range boundary, already handled by `_RANGE`.
    # CQ's own (2900, 2949) is RETIRED by its own author, 2026-08-01. B2900-B2913 are
    # written in IMPLEMENTATION_STATE.md, so the range is at or below the ceiling and its
    # unused tail is cited only as a range boundary, already handled by `_RANGE`.
    # CR's own (2950, 2999) is RETIRED by its own author, 2026-08-01. B2950-B2964 are
    # written in IMPLEMENTATION_STATE.md; the uncited tail needs no exemption because the
    # allocation range's upper-bound rule already covers it.
    # CS's own (3000, 3049) is RETIRED by its author, 2026-08-01: B3000-B3015 are
    # written in IMPLEMENTATION_STATE.md. The unused tail is cited only as an allocation
    # range boundary, which `_RANGE` already excludes; retaining the entry would be DEAD.
    # FA's (3050, 3099) is RETIRED by Session FG, 2026-08-01: the official Sol continuation
    # writes B3050-B3056 in IMPLEMENTATION_STATE.md. Its unused tail is cited only through the
    # allocation range, whose upper bound is already excluded by `_RANGE`; retaining the row
    # would now be a DEAD exemption.
    # CK's (2600, 2649) retired by its own author, 2026-07-31: B2600-B2613 are
    # written in IMPLEMENTATION_STATE.md, so its entry is now DEAD by this
    # test's definition and its uncited tail needs no successor exemption.
    # CL's (2650, 2699) retired by its own author, 2026-08-01: B2650-B2688 are written in
    # IMPLEMENTATION_STATE.md. The range is at or below the ceiling and exempts no unwritten
    # individual token, so retaining it would be a DEAD hole; the uncited tail is already
    # covered by the allocation range's upper-bound rule.
]

#: Set when `IN_FLIGHT_WAVE_RANGES` is legitimately empty: no wave is in flight, and the emptiness
#: is a decision rather than neglect. Clear it in the same commit that adds the next wave's range.
#: An empty table with this unset is the vacuous-loop hazard the test refuses.
#: Set ONLY when the table above is deliberately empty (a wave has landed and none is open).
#: CD authored this mechanism on a branch where the table WAS empty; at the wave-14b train
#: merge the table never emptied — wave 15 (CF/CG/CH/CI) was already in flight on main — so
#: the sentinel is cleared and the ranges above carry the exemptions.
NO_WAVE_IN_FLIGHT: str = ""


def _in_flight(n: int) -> bool:
    return any(lo <= n <= hi for (lo, hi), _ in IN_FLIGHT_WAVE_RANGES)


def _declared_as_one_range(lo: int, hi: int, agreement: str) -> bool:
    """Is `B{lo}`–`{hi}` declared in `agreement` as a SINGLE allocation?

    **This replaced a hole, so read the history before loosening it again.**

    Session T's rule asked, per endpoint, "does this number appear anywhere in the agreement?"
    (`re.search(rf"(?<![0-9])B?{n}(?![0-9])", agreement)`). Session U applied it to BOTH endpoints,
    which R and S had deliberately not done — both required the LOWER bound with a literal `B`
    prefix and loosened only the upper one, because the table writes ``R `B260–289``` and a literal
    `f"B{hi}"` fails on a range that IS declared.

    An adversarial pass on that synthesis found what the loosening cost. `WAVE_4_WORKING_AGREEMENT.md`
    contains 57 of the integers 0–999 somewhere in its text — section numbers, percentages, counts —
    and 31 of them have no `B{n}` anywhere. So `((71, 969), "WAVE_4_WORKING_AGREEMENT.md")` passed
    **all eight tests in this file** while exempting every unwritten citation from B71 to B969. The
    blanket-hole control below only catches ranges straddling B56 or B58; that one cleared both.

    The repair is not to restore R's asymmetric rule but to assert what the guard actually means:
    the exemption must be traceable to **one row of the allocation table**, not to two numbers that
    happen to appear in the same document. Both spellings of the upper bound are still accepted, so
    this asserts the table's content and not its typography — which was T's point, and it survives.
    """
    dash = r"[–—-]"                      # en dash, em dash, hyphen
    return bool(re.search(rf"(?<![0-9])B{lo}\s*{dash}\s*B?{hi}(?![0-9])", agreement))


def _forward_allocations(defined: set[str]) -> set[str]:
    """Block ids that are ALLOCATED but not yet written, so citing them is not a dangling claim.

    Two sources: ids above the highest written block, and ids inside a declared in-flight wave
    range. Both self-tighten — once a block is written it is `defined`, and the exemption stops
    applying to it.
    """
    ceiling = max(_num(b) for b in defined)
    return {cid for cid in _citations(defined)
            if _num(cid) > ceiling or (_in_flight(_num(cid)) and cid not in defined)}


def test_the_block_index_is_readable_at_all():
    """Positive control. Everything below is a negative result unless this holds."""
    defined = _defined_blocks()
    assert len(defined) > 90, f"only {len(defined)} blocks parsed; the header regex has drifted"
    for expected in ("B1", "B56", "B57", "B60", "B91", "B99e"):
        assert expected in defined, f"{expected} should be a defined block"
    assert "B58" not in defined, "a B58 block now exists — delete its KNOWN_GHOSTS entry"
    # One control per written form, so a regression in any of the three is a named failure rather
    # than a silent shrinking of the block index.
    assert "B220" in defined, "bold-form blocks are not being parsed (`**B220 — ...**`)"
    for half in ("B274", "B275"):
        assert half in defined, f"{half} of the combined `**B274/B275**` lead-in is not parsed"


def test_the_run_form_expands_and_the_three_near_misses_do_not():
    """`**B1668–B1670 — ...**` defines three blocks. Three lookalikes must define none.

    The expansion is the only rule in this file that can make the scanner see blocks nobody
    wrote, so it is pinned against the exact shapes it must refuse — a section heading (which
    would define ~700 ids across sixteen headings), a spaced prose dash, and a descending pair.
    """
    defined = _defined_blocks()
    for cid in ("B1668", "B1669", "B1670"):
        assert cid in defined, f"{cid} of the `**B1668–B1670**` run lead-in is not parsed"

    def expand(text: str) -> set[str]:
        out: set[str] = set()
        for lo, hi in _BLOCK_HEADER_RUN.findall(text):
            if int(lo[1:]) < int(hi[1:]):
                out.update(f"B{n}" for n in range(int(lo[1:]), int(hi[1:]) + 1))
        return out

    assert expand("**B1668–B1670 — receipts.**") == {"B1668", "B1669", "B1670"}
    assert expand("## B1750–B1799 — Session AW, the separability mine") == set(), (
        "a section heading announces an ALLOCATION; expanding it would define fifty blocks "
        "nobody wrote"
    )
    assert expand("**B215 — B200's conclusion was too strong, and is corrected.**") == set(), (
        "a spaced dash is prose about an earlier block, never a range"
    )
    assert expand("**B240–B161 — descending, therefore not a run**") == set()


def test_the_citation_scanner_can_see_a_citation_it_should_find():
    """Positive control for the scanner: a probe that finds nothing must be proven not broken."""
    cites = _citations()
    assert "B56" in cites, "scanner found no B56 citation; it cannot see what it searches for"
    assert any(f == "CLAUDE.md" for f in cites["B56"]), "CLAUDE.md cites B56 and should be seen"


def test_no_new_dangling_block_citations():
    """The rule. A citation to a block that does not exist is a claim with nothing behind it."""
    defined = _defined_blocks()
    forward = _forward_allocations(defined)
    dangling = {cid: files for cid, files in _citations(defined).items() if cid not in defined}
    unexpected = {cid: files for cid, files in dangling.items()
                  if cid not in KNOWN_GHOSTS and cid not in forward}
    assert not unexpected, (
        "new dangling block citation(s) — each points at evidence that does not exist:\n"
        + "\n".join(f"  {cid}: cited in {sorted(files)}" for cid, files in sorted(unexpected.items()))
        + "\n\nFix the citation, or add it to KNOWN_GHOSTS with a reason."
    )


def test_the_forward_allocation_exemption_is_not_a_blanket_hole():
    """The exemption must cover allocated-but-unwritten ids only, not everything above some number.

    Without this control `_forward_allocations` would be an unbounded escape hatch and any typo'd
    high-numbered citation would pass. Both sources are bounded: one by the highest WRITTEN block,
    one by the declared wave range. Both close by themselves as blocks land.
    """
    defined = _defined_blocks()
    ceiling = max(_num(b) for b in defined)
    forward = _forward_allocations(defined)
    assert all(_num(c) > ceiling or _in_flight(_num(c)) for c in forward)
    assert ceiling >= 99, f"block ceiling {ceiling} is implausibly low; the header regex has drifted"
    # A WRITTEN block can never be excused as an allocation, inside a wave range or outside it.
    assert not (forward & defined), f"written blocks excused as allocations: {sorted(forward & defined)}"
    assert "B56" not in forward and "B58" not in forward
    # B58 sits below every declared wave range, so no range can be what is excusing it.
    assert not _in_flight(_num("B58"))


def test_the_in_flight_wave_range_is_declared_and_shrinking():
    """The wave exemption must be retired when the wave lands, or it becomes a permanent hole."""
    defined = _defined_blocks()
    assert IN_FLIGHT_WAVE_RANGES or NO_WAVE_IN_FLIGHT, (
        "IN_FLIGHT_WAVE_RANGES is empty and NO_WAVE_IN_FLIGHT is unset, so every assertion below "
        "is vacuous. Either declare the next wave's range, or set NO_WAVE_IN_FLIGHT to the reason "
        "and the date. Do NOT leave a loop that checks nothing."
    )
    ceiling = max(_num(b) for b in defined)
    cited = _citations(defined)
    for (lo, hi), agreement_name in IN_FLIGHT_WAVE_RANGES:
        agreement = (REPO / "docs/audits/fable5-vision-audit-20260725" / agreement_name).read_text()
        assert _declared_as_one_range(lo, hi, agreement), (
            f"the in-flight range B{lo}-B{hi} is not declared as a single allocation in "
            f"{agreement_name}; an undeclared exemption is not an exemption, it is a hole"
        )
        unwritten = [n for n in range(lo, hi + 1) if f"B{n}" not in defined]
        assert unwritten, (
            f"every block in B{lo}-B{hi} is now written, so that wave has landed. "
            f"Drop its entry from IN_FLIGHT_WAVE_RANGES — an exemption that outlives its wave "
            "silently excuses real ghosts."
        )
        # An entry must be doing one of exactly two jobs, and it must be visible which.
        #   ACTIVE          — it exempts a citation the ceiling does not already exempt.
        #   PRE-DECLARATION — it sits entirely above the ceiling, so the ceiling covers it today and
        #                     the entry starts working the moment that wave writes its first block.
        # Anything else is a DEAD entry: below the ceiling and exempting nothing, i.e. a hole
        # waiting for a typo. Found by an adversarial pass on Session U's own synthesis, which
        # asserted only that the list was non-empty and so could not tell ACTIVE from inert.
        does_work = {c for c in cited
                     if lo <= _num(c) <= hi and c not in defined and _num(c) <= ceiling}
        assert does_work or lo > ceiling, (
            f"in-flight range B{lo}-B{hi} is DEAD: it sits at or below the block ceiling (B{ceiling}) "
            "and exempts nothing the ceiling does not already exempt. Drop it."
        )


def test_the_ghost_allowlist_shrinks_and_never_grows():
    """A stale allowlist entry is itself a false-green: it reports a known problem that is gone."""
    defined = _defined_blocks()
    dangling = set(_citations(defined)) - defined
    stale = sorted(set(KNOWN_GHOSTS) - dangling)
    assert not stale, (
        f"KNOWN_GHOSTS lists {stale}, which no longer appear as dangling citations. "
        "Delete the entries — an allowlist that outlives its problem trains readers to ignore it."
    )
    for cid, reason in KNOWN_GHOSTS.items():
        assert len(reason) > 40, f"{cid}'s allowlist reason is too thin to be worth reading"


def test_b58_is_resolved_for_readers_by_the_numbering_note():
    """B58 stays cited in files this session must not edit, so the note is the actual repair.

    Asserted behaviourally — the note must name the ghost, say where its content really lives, and be
    near the top of the file where a reader chasing a citation will land — rather than by grepping
    for one magic substring, which would pass against a note that says nothing useful.
    """
    head = STATE.read_text()[:6000]
    assert "no block B58" in head or "There is no block B58" in head
    assert "B56" in head, "the note must say where B58's content actually lives"
    assert "B89" in head, "the note must record why B89 is NOT a ghost, or the next sweep re-chases it"


def test_the_high_traffic_briefings_carry_no_dangling_citation():
    """The two root briefings are read at the start of every session; they get the strict rule."""
    defined = _defined_blocks()
    forward = _forward_allocations(defined)
    for name in ("CLAUDE.md", "AGENTS.md"):
        text = (REPO / name).read_text()
        bounds = set(_RANGE.findall(text))
        bad = sorted({c for c in _CITATION.findall(text)
                      if c not in defined and c not in bounds and c not in forward
                      and _is_block_shaped(c, defined)})
        assert not bad, f"{name} cites non-existent block(s): {bad}"

    # Control: both files must actually cite blocks, or the assertion above is vacuous.
    for name in ("CLAUDE.md", "AGENTS.md"):
        text = (REPO / name).read_text()
        assert {c for c in _CITATION.findall(text) if c in defined}, f"{name} cites no known block"


def test_no_wave_in_flight_is_declared_or_the_table_is_populated():
    """Exactly one of the two states, and never both.

    A range in the table means a wave is open; `NO_WAVE_IN_FLIGHT` means none is. Both set at
    once is a contradiction that would let a stale declaration outlive the wave it names, which
    is the same class of hole `IN_FLIGHT_WAVE_RANGES` itself exists to close.
    """
    if IN_FLIGHT_WAVE_RANGES:
        assert not NO_WAVE_IN_FLIGHT, (
            "NO_WAVE_IN_FLIGHT is set while ranges are declared. Clear it in the commit that "
            f"opened {IN_FLIGHT_WAVE_RANGES[0][0]}."
        )
    else:
        assert NO_WAVE_IN_FLIGHT, "the table is empty and nobody said why"
        assert len(NO_WAVE_IN_FLIGHT) > 120, (
            "NO_WAVE_IN_FLIGHT must carry the date, the session and the reason -- a one-word "
            "value is the neglect this constant exists to distinguish itself from"
        )
