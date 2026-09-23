#!/usr/bin/env python3
"""FG1: content-fidelity check of the Sol integration branch (ba3c18ddf).

For each source branch:
  - enumerate owned paths (merge-base..tip name-only diff)
  - diff tip tree vs integration tree on those paths (properly split)
  - classify divergences: shared-path composition vs exclusive-path divergence
Also: per-commit patch-id pairing between the 66 source commits and the 66
cherry-picked commits on the integration branch, matched by subject.
"""
import subprocess, json, collections, sys

WT = "/Users/borr/GTOSActive/worktrees/wave19-sol-integration-20260801"
INTEG = "ba3c18ddf"
INTEG_BASE = "f8c05d0ac"

BRANCHES = [
    # (label, ref, expected_tip)
    ("CR", "phase19/ny-metals-capture", "47139bc35"),
    ("CS", "phase19/breaker-folds", "7f9ab73c2"),
    ("FB", "phase19/sol-grid", "6ef09b8f4"),
    ("FC", "phase19/sol-exit", "210307687"),
    ("FD", "phase19/sol-defects", "a7d9260ed"),
    ("FE", "phase19/sol-conditions", "674b81f61"),
    ("FF", "phase19/sol-composition", "9c95c28b7"),
]

def git(*args):
    r = subprocess.run(["git", "-C", WT] + list(args), capture_output=True, text=True)
    if r.returncode != 0:
        raise RuntimeError(f"git {args} failed: {r.stderr[:500]}")
    return r.stdout

out = {"branches": {}, "overlaps": {}, "patch_id": {}}

# --- per-branch owned paths and tree diff ---
owned = {}
tips = {}
for label, ref, exp in BRANCHES:
    tip = git("rev-parse", ref).strip()
    tips[label] = tip
    assert tip.startswith(exp), f"{label} tip {tip} != expected {exp}"
    mb = git("merge-base", ref, "phase19/sol-integration").strip()
    paths = [p for p in git("diff", "--name-only", mb, ref).splitlines() if p]
    owned[label] = set(paths)
    out["branches"][label] = {
        "ref": ref, "tip": tip[:9], "merge_base": mb[:9],
        "n_commits": int(git("rev-list", "--count", f"{mb}..{ref}").strip()),
        "n_owned_paths": len(paths),
    }

# overlap matrix
path_owners = collections.defaultdict(list)
for label, _, _ in BRANCHES:
    for p in owned[label]:
        path_owners[p].append(label)
shared = {p: os_ for p, os_ in path_owners.items() if len(os_) > 1}
out["overlaps"] = {p: sorted(v) for p, v in sorted(shared.items())}

for label, ref, _ in BRANCHES:
    paths = sorted(owned[label])
    div = [p for p in git("diff", "--name-only", ref, INTEG, "--", *paths).splitlines() if p]
    excl_div = [p for p in div if len(path_owners[p]) == 1]
    shared_div = [p for p in div if len(path_owners[p]) > 1]
    out["branches"][label]["diverging_paths_vs_integration"] = div
    out["branches"][label]["exclusive_path_divergence"] = excl_div
    out["branches"][label]["shared_path_divergence"] = shared_div

# --- composition check on shared paths ---
# For every shared path, verify that each owning branch's ADDED lines
# (mb..tip) are present in the integration version, line-by-line
# (necessary condition for "nothing dropped").
comp = {}
for p, owners in sorted(shared.items()):
    integ_lines = None
    try:
        integ_blob = git("show", f"{INTEG}:{p}")
        integ_lines = set(integ_blob.splitlines())
    except RuntimeError:
        comp[p] = {"error": "path missing in integration"}
        continue
    entry = {}
    for label in owners:
        ref = dict((l, r) for l, r, _ in BRANCHES)[label]
        mb = git("merge-base", ref, "phase19/sol-integration").strip()
        diff = git("diff", f"{mb}..{ref}", "--", p)
        added = [ln[1:] for ln in diff.splitlines()
                 if ln.startswith("+") and not ln.startswith("+++")]
        # ignore blank lines
        added = [a for a in added if a.strip()]
        missing = [a for a in added if a not in integ_lines]
        entry[label] = {"added_nonblank_lines": len(added), "missing_in_integration": len(missing),
                        "missing_sample": missing[:5]}
    comp[p] = entry
out["shared_path_composition"] = comp

# --- per-commit patch-id pairing ---
def patch_ids(rev_range, exclude=None):
    revs = [r for r in git("rev-list", "--reverse", rev_range).splitlines() if r]
    if exclude:
        revs = [r for r in revs if not r.startswith(exclude)]
    res = []
    for r in revs:
        show = subprocess.run(["git", "-C", WT, "show", r], capture_output=True, text=True)
        pid = subprocess.run(["git", "-C", WT, "patch-id", "--stable"],
                             input=show.stdout, capture_output=True, text=True)
        pidval = pid.stdout.split()[0] if pid.stdout.strip() else "EMPTY"
        subj = git("log", "-1", "--format=%s", r).strip()
        res.append({"sha": r[:9], "subject": subj, "patch_id": pidval})
    return res

src_commits = []
for label, ref, _ in BRANCHES:
    mb = git("merge-base", ref, "phase19/sol-integration").strip()
    for c in patch_ids(f"{mb}..{ref}"):
        c["branch"] = label
        src_commits.append(c)

integ_commits = patch_ids(f"{INTEG_BASE}..{INTEG}")
closing = [c for c in integ_commits if c["sha"].startswith(INTEG[:9])]
integ_cherry = [c for c in integ_commits if not c["sha"].startswith(INTEG[:9])]

out["patch_id"]["n_source_commits"] = len(src_commits)
out["patch_id"]["n_integration_commits_total"] = len(integ_commits)
out["patch_id"]["n_integration_cherrypicks"] = len(integ_cherry)
out["patch_id"]["closing_commit"] = closing

# match by subject
src_by_subj = collections.defaultdict(list)
for c in src_commits:
    src_by_subj[c["subject"]].append(c)

pairs, unmatched_integ, mismatched = [], [], []
for ic in integ_cherry:
    cands = src_by_subj.get(ic["subject"], [])
    if not cands:
        unmatched_integ.append(ic)
        continue
    sc = cands.pop(0)
    same = sc["patch_id"] == ic["patch_id"]
    pairs.append({"subject": ic["subject"], "src": sc["sha"], "branch": sc["branch"],
                  "integ": ic["sha"], "patch_id_match": same})
    if not same:
        mismatched.append(pairs[-1])
unmatched_src = [c for lst in src_by_subj.values() for c in lst]

out["patch_id"]["n_pairs_matched_by_subject"] = len(pairs)
out["patch_id"]["n_patch_id_equal"] = sum(1 for p in pairs if p["patch_id_match"])
out["patch_id"]["n_patch_id_differ"] = len(mismatched)
out["patch_id"]["mismatched_pairs"] = mismatched
out["patch_id"]["unmatched_integration_commits"] = unmatched_integ
out["patch_id"]["unmatched_source_commits"] = unmatched_src

print(json.dumps(out, indent=1))
