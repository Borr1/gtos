# Halt semantics and runtime-control auditor

Generated: 2026-06-04T14:51:09.961282+00:00

Hard-halt flags exist, but broker truth shows manual flattening and halt sequencing were not sufficient as atomic runtime control. This route preserves the halt gap as a Wave 3 atomic halt requirement.

Material row coverage: runtime decisions `6187`, replacement snapshots `5149`, trade records `471`, pending lifecycle rows `877`, broker trade groups `91`.
