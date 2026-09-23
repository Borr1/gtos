export const meta = {
  name: 'vps-operator-bundle',
  description: 'Build the on-VPS bundle: dual-MT5 live adapter (FTMO-primary/redacted_account-follower, replacing the bridge), the Claude-on-VPS deployment prompt, the active-operator toolkit (monitor/repair/learn per the charter), and the full-context bootstrap. Default-off, prepare-dont-flip.',
  phases: [
    { title: 'Build VPS Layer', detail: '4 tracks: dual-MT5 adapter, deployment prompt, operator toolkit, context bootstrap' },
    { title: 'Assemble', detail: 'single VPS_OPERATOR_BUNDLE the VPS Claude opens first' },
  ],
}

const REPO = '/Users/borr/Documents/gtos/repo/ai-trading-agent'
const ROUTE = REPO + '/research/operations/final_moonshot_v4_ultimate_mechanical_edge_2026_06_10'

const DOCTRINE = [
  'You are building the on-VPS operator bundle for GTOS go-live. Think hard. HARD GUARDRAILS:',
  '- DEFAULT-OFF / PREPARE-DONT-FLIP: nothing places a live order or connects to a real broker; creds/terminal handles are config placeholders; halt files remain the physical control; new behaviour default-off behind the triple-gate.',
  '- DO NOT modify production src/ or config/agent_config.yaml to change live behaviour; build in the route dir + GOLIVE_vps_deploy/; stage production changes as reviewed patches.',
  '- Architecture is FTMO-PRIMARY / redacted_account-FOLLOWER per DUAL_MT5_ARCHITECTURE.md (the VPS has TWO local MT5 terminals, NO research bridge; the bridge is dev-only). The resident VPS Claude operator has full authority for correctness/health/repair/learning, but the owner risk dial (1.25 to 1.5 pct, ceiling 2.0) + governor + halt files are bounds it MAINTAINS, never exceeds (per VPS_OPERATOR_CHARTER.md).',
  '- Everything tested + reversible; no fabricated numbers.',
].join('\n')

const TOOLS = [
  'ENVIRONMENT (absolute):',
  '- Repo root: ' + REPO + ' ; Route dir: ' + ROUTE,
  '- READ FIRST: DUAL_MT5_ARCHITECTURE.md, VPS_OPERATOR_CHARTER.md, GO_LIVE_PACKAGE.md, GO_LIVE_SEQUENCE.md, GOLIVE_runbook_readiness.md, PORTFOLIO_BUILD_W7_FINAL.md, ULTIMATE_GO_LIVE_DOSSIER.md, ULTIMATE_SYSTEM_SCORECARD.md, THE_GRAND_VISION.md.',
  '- Deploy surface: ultimate_book_live_package.py (deploy book + dials + Kelly-lite + sqrt-N + tick floors), ultimate_book_runtime_bridge.py (default-off admission bridge), GOLIVE_vps_deploy/ (systemd/docker/monitoring/kill-switch/adapters/bridge_adapter.py = the bridge adapter to SUPERSEDE for live), GOLIVE_preflight_verify.py.',
  '- Production MT5 contract to mirror: src/mt5/mt5_interface.py (MT5Interface). Persistent memory to fold into the bootstrap: memory/MEMORY.md, ultimate-edge-program-state.md, codebase-map.md, codebase-gotchas.md.',
  '- Python: /usr/bin/python3 has pytest+numpy. Prefix scratch with track key; write findings to the named file.',
].join('\n')

const SCHEMA = {
  type: 'object', additionalProperties: false,
  properties: {
    track: { type: 'string' }, status: { type: 'string', enum: ['ready', 'staged', 'blocked', 'infra'] },
    summary: { type: 'string' }, deliverables: { type: 'string' },
    ready_vs_blocked: { type: 'string' }, tests: { type: 'string' }, caveats: { type: 'string' },
  },
  required: ['track', 'status', 'summary', 'deliverables', 'ready_vs_blocked'],
}

const TRACKS = [
  { key: 'dual_mt5_adapter', title: 'Dual-MT5 live adapter (FTMO-primary / redacted_account-follower)',
    task: 'Replace the bridge-based live adapter (GOLIVE_vps_deploy/adapters/bridge_adapter.py) with a DUAL-MT5 adapter per DUAL_MT5_ARCHITECTURE.md, mirroring src/mt5/mt5_interface.MT5Interface: TWO terminal handles (FTMO + redacted_account); FTMO = PRIMARY (read OHLC/tick, feed the decision engine, execute); redacted_account = FOLLOWER (spec-translated mirror of each FTMO decision). Include: a per-broker symbol/spec/spread-floor map (handle .cash/.c/pro suffixes, contract size, digits); UTC clock normalization with a per-terminal startup offset check (chronological safety, the top watch item); independent per-account governor + DD; follower missing-symbol/large-slip/reject means skip that leg, never the primary; a primary-vs-follower parity ledger interface. Default-off, no live connect (creds/handles as placeholders), fail-closed, import side-effect-free. Tests (no broker). Report the adapter and how it supersedes the bridge adapter for live.' },
  { key: 'vps_deployment_prompt', title: 'The Claude-on-VPS deployment prompt/runbook',
    task: 'Write VPS_DEPLOYMENT_PROMPT.md = the exact literal prompt + runbook a fresh Claude Code session ON THE VPS executes to set up and launch everything (idempotent, fail-closed, each step verified). Steps: clone/pull repo; run git lfs pull and verify all required artifacts present (LFS-missing is a known failure mode, list the must-exist files); create venv + install GOLIVE_vps_deploy/config/requirements-vps.txt; set ENV from env.template (FTMO + redacted_account creds, both MT5 terminal paths); connect BOTH MT5 terminals READ-ONLY first, verify FTMO is primary, normalize both clocks to UTC and assert offsets; run GOLIVE_preflight_verify.py (must exit 0); on owner go, apply the canonical Phase A patch (disable broad selector + scheduler) and append the ultimate_book triple-gate block; start the FTMO account at 1.25 pct half-Kelly behind the gate; start the monitor and the operator loop. Include the operator continuous self-check cadence. Make it copy-paste runnable as a Claude prompt.' },
  { key: 'operator_toolkit', title: 'Active-operator toolkit (monitor/repair/learn)',
    task: 'Build the operator toolkit per VPS_OPERATOR_CHARTER.md so the resident VPS Claude actively OPERATES (default-off, runnable on the VPS): (a) health/memory/disk + data-freshness monitors on both terminals; (b) the two parity ledgers (live-vs-replay on primary; FTMO-vs-redacted_account follower) with divergence alerts; (c) NULL-GUARD + null-source diagnostic (any gate/feature/score null means fail-closed that candidate + log root cause); (d) TIMEZONE/CHRONOLOGICAL verifier (terminal offsets, bar order, sequence-of-elements); (e) LFS/missing-file + missing-parameter checker; (f) the standing improvement-miner wired to LIVE trades (continue the compounding loop); (g) alert + kill-switch hooks + escalation logic. PLUS OPERATOR_REPAIR_PLAYBOOK.md: per failure mode (timezone, sequence-order, null values, missing params, LFS, misbehavior-vs-spec) the detect then confirm-with-a-test then fix then forward-validate-before-it-affects-sizing procedure, staying within the safety envelope (never exceed the risk dial; escalate risk-increasing changes). Tests. Report the toolkit.' },
  { key: 'context_bootstrap', title: 'Full-context bootstrap for the VPS Claude',
    task: 'Assemble CLAUDE_VPS_BOOTSTRAP.md = the read-first index + a condensed but COMPLETE brief so a fresh Claude session on the VPS operates with full continuity (it must know everything this session knows). Cover: the method doctrine (no-averages / per-trade-intelligence / build-and-improve / forward-validate / leak-free / size-by-confidence); the program arc (waves 1-7 + the pivot from a small gold sleeve to the 11-sleeve substrate-derived book); the FINAL deploy book + the 1.25 to 1.5 pct dial; the dual-MT5 FTMO-primary architecture; the operator charter + authority bounds; the go-live package + flip sequence; the failure-mode watchlist; the scorecard as the standing loop controller; and an ordered pointer list to every key artifact + the persistent memory files. It must be sufficient for the VPS Claude to deploy + actively operate the system with full authority + context. Report the bootstrap outline.' },
]

phase('Build VPS Layer')
const built = await parallel(TRACKS.map(t => () =>
  agent(DOCTRINE + TOOLS + '\n\nYOUR TRACK: ' + t.title + '\n' + t.task +
        '\n\nWrite findings to ' + ROUTE + '/VPSOP_' + t.key + '.md and return the structured result.',
        { label: 'vpsop:' + t.key, phase: 'Build VPS Layer', schema: SCHEMA, model: 'opus', agentType: 'general-purpose' })
))
const ok = built.filter(Boolean)
log('VPS-operator layer built ' + ok.length + '/' + TRACKS.length + '. Assembling bundle...')

phase('Assemble')
const synth = await agent(DOCTRINE + TOOLS +
  '\n\nYOU ARE THE ASSEMBLER. Track results (JSON):\n' + JSON.stringify(ok, null, 1) +
  '\n\nAssemble VPS_OPERATOR_BUNDLE.md = the single index a fresh Claude session on the VPS opens FIRST: links the context bootstrap, the deployment prompt, the dual-MT5 adapter, the operator toolkit + repair playbook, the charter, and the architecture doc, in the order the VPS Claude uses them (load context, then deploy, then pre-flight, then operate). Verify: tests pass, nothing live-enabled, the dual-MT5 adapter supersedes the bridge adapter for live, FTMO-primary wiring is correct. State the final readiness: what is READY for the VPS Claude to deploy+operate vs what the owner must supply (host-local). Write VPS_OPERATOR_BUNDLE.md and return a dense summary.',
  { label: 'vpsop:assemble', phase: 'Assemble', model: 'opus', agentType: 'general-purpose' })

return { tracks: ok, bundle: synth }
