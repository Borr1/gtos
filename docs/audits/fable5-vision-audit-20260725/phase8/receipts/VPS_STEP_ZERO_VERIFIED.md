# Step zero, executed and VERIFIED — the armed book is the three-sleeve book

**2026-07-30, orchestrator, direct read-only host-admin session over host-mesh
(host `redacted_host`, credentials from `~/.gtos/vps.env`, owner-directed).** First direct host
contact by the programme; every command read-only.

## The answer

`config/agent_config.yaml:1200` on the host:

    ultimate_book_include_clean3: true   # ON 2026-07-29: admits sub_xvol_pullback to the live path (OD-3)

The three gates at `:1161-1163` all `true` (ARMED 2026-07-29 comments). Config last write
**2026-07-29 12:54:30Z** — the arming write. Token file written 12:54:48Z, audit log present.

**Consequence:** the FTMO book generates all three armed sleeves. AI §2.3b's `[UNVERIFIED]`
resolves TRUE-side: 4.501 %/mo, P2 0.9172, the archive control and every redacted_account comparison
price the running book. CLAUDE.md's armed-set caveat is amended to `[VERIFIED]`.

## The rest of the recon (all read-only), and what it changes

| fact | reading | consequence |
|---|---|---|
| FTMO workers (2) command line | `--tags crypto,energy_agri,sub_xvol_pullback` | the §6 checklist's biggest hazard is currently clean |
| redacted_account workers (2) | no `--tags`; `ULTIMATE_BOOK_KILL_fn.flag` **present** | FN held down exactly as documented |
| supervisor | `GTOS_W7_BookSupervisor: Running`; spawns both books | restart path exists for the ceremony |
| host branch | `vps/ultimate-conditioned-expansion-minimal-2026-06-18` @ `4f2c851e6` | **includes `719e7b5f5` Stage 0.1: the activation-token gate at `RealMT5.order_send` IS deployed on the live lineage** |
| `src/utils/broker_clock.py` | **EXISTS on host** | the ceremony package's worst import hazard (§1: "does not exist on the VPS") is **stale — already satisfied** by the partial Stage-3 carry (`4f2c851e6` "inert half of the packet-emitter carry") |
| host working tree | dirty: `agent_config.yaml` (the arming edit), `run_book_supervisor.ps1` (the `--tags` edit), `src/components/execution.py`, LIVE_STATE + runtime churn | the arming edits are UNCOMMITTED on the host — the ceremony should commit them on the host branch first so a checkout can never silently disarm the book |
| disk | **9.3 GB free on C:** | monitor during owner's OS update; the ceremony's backups are small but the margin is thin |

## Standing

- The ceremony (C1–C4, C5 stays off) now needs a **delta re-check against the actual host
  state** before execution — `4f2c851e6` already carries part of what the package assumed absent.
- **All host mutations are HELD** while the owner installs an update on the VPS (his message,
  2026-07-30). The ceremony executes over host-admin after the host settles, with the package's
  backup/verify/one-book-at-a-time discipline unchanged.
