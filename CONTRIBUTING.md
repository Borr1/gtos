# Contributing

Anyone can read this repository, run it, and change their own copy. That freedom is the point.

A change to **this** repository is a pull request. GitHub requires a pull request into `main`, a linear history, and no force-push and no deletion. No second review is required. Only `@Borr1` has write access, so only that account can merge. Anyone can open a pull request. Agents that ship here act under that account. There are no other collaborators.

Open an issue to:

- propose an improvement
- sound an alarm when the system is wrong, stale, or off the market
- show a fact the code should start using

The aim of those reports is the same: converge on the market and follow the value where it is.

## What a merged pull request does

A merge here updates this public projection. It does not update the live host.

The live system has one source, the private Origin repository `borr/gtos`. The host deploys only from that `main`, by the coordinator's manual `git pull --ff-only`. This GitHub repository is not a remote of that host. A pull request merged here reaches the live system only when the coordinator carries the change onto Origin, merges it there, and fast-forwards the host.

## Projection

`ORIGIN_SHA` is the Origin commit this tree was projected from. After each Origin merge, the coordinator rebuilds this tree from the coordinator store. The exporter and the scrub stay in that store. They are not in this repository. The scrub removes live identifiers before the push. The public commit message names the Origin sha.

If you are the coordinator: run the sync from the coordinator store, with Borr1's GitHub credential, from a machine we control. Do not point the live host at this remote.
