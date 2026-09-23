"""Immutable production expectations for the Wave 20 P1 packet verifier."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class _PacketExpectations:
    symbols: tuple[str, ...]
    total: int
    window_counts: tuple[tuple[str, int], ...]
    windows: tuple[tuple[str, tuple[str, str]], ...]
    state_count: int
    payload_count: int
    reused_candidate_ids: int
    rows_under_reused_candidate_ids: int
    source_payload_count: int
    source_root: Path
    repo_root: Path
    repo_authorities: tuple[tuple[str, str, int], ...]
    transitive_paths: tuple[str, ...]
    source_manifests: tuple[tuple[str, str], ...]
    evidence_lineage: tuple[tuple[str, str, str, str], ...]
    evidence_artifacts: tuple[tuple[str, tuple[tuple[str, str, int], ...]], ...]
    tooling_paths: tuple[str, ...]
    source_commit_bound_paths: tuple[str, ...]
    source_parent: str
    generator_path: str
    generator_sha256: str
    market_state_path: str
    market_state_sha256: str
    h1_reference_path: str
    h1_reference_sha256: str
    timebase_sha256: str
    m15_lookback: int
    h1_lookback: int
    minimum_closed_m15: int
    partial_h1_buckets: int
    referenced_partial_h1_buckets: int


_REPO_ROOT = Path(__file__).resolve().parents[2]
_SOURCE_ROOT = Path(
    "/Users/borr/GTOSActive/worktrees/wave16-rematerialization-20260731/"
    ".hermes/evidence/phase16/cj-rematerialization/LANE_INPUTS_TRUE_UTC_V1"
)
_SYMBOLS = (
    "AUDJPY", "AUDUSD", "BTCUSD", "CHFJPY", "ETHUSD", "EURGBP", "EURJPY",
    "EURUSD", "GBPJPY", "GBPUSD", "GER40", "JP225", "NAS100", "NZDUSD",
    "SPX500", "UK100", "UKOIL_cash", "US30_cash", "USDCAD", "USDCHF",
    "USDJPY", "USOIL_cash", "XAGUSD", "XAUUSD",
)
_REPO_AUTHORITIES = (
    ("src/__init__.py", "1bcd101c48c28c58352dd2211955e607bc83d821b626b007d7b5136bf3e638a2", 27),
    ("src/components/__init__.py", "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855", 0),
    ("src/components/broader_origin_generators.py", "6e274d22a72c945fa495c2b85408f0495acf6158caa2edb0d34bae108b859fba", 97_467),
    ("src/components/market_state.py", "c59e1d5ea2e4f2758129bca6b67b1ed86379e3278e5c0d44321542425fc680ee", 59_556),
    ("src/components/current_breaker_re_entry_repair.py", "465ae93d54ee532021f16963e0cc956f5fee26e5c79276d09a636c634cc7192b", 6_548),
    ("src/components/candidate_geometry.py", "d16c953346d067502d80013c03bc0d00dd9f314f31902f3bef3f86d43ec15855", 4_082),
    ("src/components/poi_state_contract.py", "7f24b0d8b9280b0a62c26a73f137c5437bfbf274cda114237ea648d0b60d10fc", 12_844),
    ("src/components/poi_execution_lifecycle.py", "224ee0a62b0e423f070ddca8198078056a4cb51b695b86077eab9146949a3351", 22_891),
    ("src/components/structure_detector_shadow_logger.py", "870fa9c17c83ba1ab693de77220eaa88824dee7a1eb1783e39303469071259b9", 14_719),
    ("src/models/market_state_models.py", "65c752ed3301ced7c3898643d178de1b2f7b8f62f6107e6227ec8722b45dc438", 6_355),
    ("src/models/__init__.py", "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855", 0),
    ("src/research_infra/__init__.py", "37700001021d71975d2d55ff3609a36da6d35ff16ff9c7a3e76e32dade133d9b", 806),
    ("src/research_infra/train_engine/__init__.py", "d9ae15c68e691d33c3ec5b869c6a575fe1bcd44ad91b9bf1b657272618698de6", 1_961),
    ("src/utils/__init__.py", "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855", 0),
    ("src/utils/file_io.py", "8b91a5e7808a5091b532cd4383a0869dc9760ae3668e050bbf0a02c5973a2704", 2_761),
    ("src/utils/jsonl_rotation.py", "50287ee4aa4e0c91ac0345f69d5a25355577d75571e943f78b2c2f4763d031a7", 24_387),
    ("src/utils/broker_clock.py", "0f97bbb64bc55b0213e47a018c2e884d83b2059b61de7941a171fd3cf2fef552", 23_842),
    ("src/research_infra/replay_acceleration_slice.py", "5736302c6a3efe32a40ca6e2f205448eb6ff7ab1a78f63e9b9c00ff54679008b", 76_957),
    ("src/research_infra/replay_acceleration_attempt5_typed_sparse_runner.py", "9733f402149dba5d65ac513476495b6c3e84a813cb8f3c0587238eeb5e3884c6", 834_619),
    ("src/research_infra/v4_timewarp_simulated_live_research_loop.py", "824cf572b33f96cf3ff00cb979d3c60035ce1e8623df03c30937162ffa30cc24", 4_220_159),
    ("config/agent_config.yaml", "175f6b3bc1a692a5c5add776845281ee92fad71e11074e0a3f38d72a619eff7d", 273_732),
    ("config/profiles/operator_profile.yaml", "ae9312e6c5c8e6b05f8e5eb5f9490166c44a1a3279b4eff5df10c3da2921e2b8", 58_294),
    ("config/profiles/redacted_account.yaml", "b856f0ee7f13c59dd407949c6937275da57c3e797ab2bae256755560bbd21305", 33_482),
    ("docs/audits/fable5-vision-audit-20260725/phase18/receipts/CQ_TRUE_UTC_S0R0_PATH_POOL_V1.json", "87e8a086565ef9a2fd20aca55b4ed575dc48cbd5f07bcf3ade2ada74f9882c85", 9_647),
    ("docs/audits/fable5-vision-audit-20260725/phase16/receipts/pools/CJ_RECLOCKED_S0R0_POOL_V1.jsonl.gz", "ee920fb0e28713f28cf85322d6b6494beef07c27235db9e6ba59dd6e5097fc8f", 5_696_917),
    ("docs/audits/fable5-vision-audit-20260725/phase18/receipts/pools/CQ_TRUE_UTC_S0R0_ORDERED_PATH_SIDECAR_V1.jsonl.gz", "ffa2a2151e79ab81202fab07706f859579e453e0b00784c1e69b381903e9ba61", 34_134_117),
    ("docs/audits/fable5-vision-audit-20260725/phase19/receipts/CS_APRIL_S0R0_POOL_V1.json", "8665b88e65902d2ee982f382a7d23ceaf045a2e8e7e657d644376d86c84f739c", 8_633),
    ("docs/audits/fable5-vision-audit-20260725/phase19/receipts/CS_APRIL_PATH_POOL_V1.json", "5fc38c24746763d943619f6b8b6e3ac9ffa64b34cbe0a8fb73a024556c88e102", 10_147),
    ("docs/audits/fable5-vision-audit-20260725/phase19/receipts/pools/CS_APRIL_S0R0_POOL_V1.jsonl.gz", "d587e99ebdbc0f56b3501719e05dfec45902e9013ee8c32392e344bc51c9e4d9", 5_504_482),
    ("docs/audits/fable5-vision-audit-20260725/phase19/receipts/pools/CS_APRIL_S0R0_ORDERED_PATH_SIDECAR_V1.jsonl.gz", "eccadb15d5e6a3a97b178b2e3267b79e5792feeca49f61c157ba86bca05ad2cd", 30_817_431),
    ("docs/audits/fable5-vision-audit-20260725/phase19/receipts/CS_MAY_S0R0_POOL_V1.json", "d126bbab4f1399945343c403c76be1c98ab38d4e249e1e3eeb0dc05575c6b38e", 8_404),
    ("docs/audits/fable5-vision-audit-20260725/phase19/receipts/CS_MAY_PATH_POOL_V1.json", "803cf08ce72f0ce6745f92f8b02a08ba796f51707fc98a611c57f8ab61d6c1e5", 9_371),
    ("docs/audits/fable5-vision-audit-20260725/phase19/receipts/pools/CS_MAY_S0R0_POOL_V1.jsonl.gz", "1bba6662644d0424ff5a360f987ddd81bb1b0f176b7547b6626853d166cb5633", 4_600_824),
    ("docs/audits/fable5-vision-audit-20260725/phase19/receipts/pools/CS_MAY_S0R0_ORDERED_PATH_SIDECAR_V1.jsonl.gz", "bdab3988ce6960a6e25b29a29ca4bd1498698c0495222191c34e00c0d6baf5b4", 26_415_775),
)
_TRANSITIVE = tuple(path for path, _, _ in _REPO_AUTHORITIES if path.startswith(("src/", "config/")))
_EVIDENCE_LINEAGE = (
    ("hg_preregistration", "6b72de84d27e10563da102237be46e5a0180c7d6", "7c494e73a5504615ff6ca917926760cf17697cff", "SOURCE_ANCESTOR_AND_IMMUTABLE_PREREGISTRATION_AUTHORITY"),
    ("hk_evidence_closeout", "11594419a197e278263565ac7677ecfc3e317c31", "a1cf205de52a7f279932e4436196a255ae5e7b9b", "AUTHORITY_ONLY_NOT_MERGED_OR_REBASED"),
    ("hl_evidence_closeout", "5c94d2caa8c0764fccd6fc8dc1f353a83d6ef094", "41534770fa338f12b34d79c9625fd406219a41fe", "AUTHORITY_ONLY_NOT_MERGED_OR_REBASED"),
    ("hm_evidence_closeout", "ec4555696b21e50a928106ebf0f9089f9a8f2538", "1c81f5cd384671a4a99ddcda49f9dfc6ef7bae51", "AUTHORITY_ONLY_NOT_MERGED_OR_REBASED"),
    ("hn_evidence_closeout", "97d4c7da1d67314e1474225b5d8484d782e5750e", "f59fbb829a5561b7e7b78bed324d67a8c01d6e74", "AUTHORITY_ONLY_EVIDENCE_CLOSEOUT_NOT_SOURCE_ANCESTRY"),
)
_EVIDENCE_ARTIFACTS = (
    ("hg_preregistration", (
        ("docs/audits/fable5-vision-audit-20260725/phase20/WAVE20_SCIENCE_PREREGISTRATION.md", "078209d0226bf428d0767e175293f23a72c11f91726b221a5c8cb6f8c71d3735", 26_164),
        ("docs/audits/fable5-vision-audit-20260725/phase20/receipts/WAVE20_SCIENCE_PREREGISTRATION.json", "684933c6641c31056146be0e4598d05b25676aa8e3b83ccc054e92ce0668e90b", 92_694),
    )),
    ("hk_evidence_closeout", (
        ("docs/audits/fable5-vision-audit-20260725/phase20/receipts/science/P1_IMPLEMENTATION_COMMISSION.json", "f46c376872aeea6a5c5c513c5575e090fcdf0d815c42493a95454c10bc6c4ec8", 20_503),
        ("docs/audits/fable5-vision-audit-20260725/phase20/receipts/SESSION_HK_COMPLETE.json", "b9aeac7fc8e7c77e63565bbfdb13f73bfc5cfd8280ef501dab7f009dcad02591", 8_086),
    )),
    ("hl_evidence_closeout", (
        ("docs/audits/fable5-vision-audit-20260725/phase20/receipts/science/P1_ADAPTER_IMPLEMENTATION.json", "c6b6975191a52fd43a2bc7ae4fb58b0736f09c9f795ca7710622b5d5fe885222", 10_963),
        ("docs/audits/fable5-vision-audit-20260725/phase20/receipts/science/P1_ADAPTER_SOURCE_CONFORMANCE.json", "6e2266875f8def65815fd39a911e856a7fb672e5cd6fa9f4be4878b21b2c14e8", 17_646),
        ("docs/audits/fable5-vision-audit-20260725/phase20/receipts/SESSION_HL_COMPLETE.json", "f3b8ebd52c8331d058266469536c4a535e5ac6bed073068f5b1fbc32f7da0afa", 7_537),
    )),
    ("hm_evidence_closeout", (
        ("docs/audits/fable5-vision-audit-20260725/phase20/receipts/science/P1_ADAPTER_INDEPENDENT_FALSIFICATION.json", "11f860b790e8aed897c6510b034b77166e1dbb50768f80c0941b8d93dbd81d80", 27_849),
        ("docs/audits/fable5-vision-audit-20260725/phase20/receipts/SESSION_HM_COMPLETE.json", "606eb58779d859b81ab43275d2c9ea8ba789977cf37aa66c06727d40c284c186", 6_628),
    )),
    ("hn_evidence_closeout", (
        ("docs/audits/fable5-vision-audit-20260725/phase20/SESSION_HN_CONTEXT_ANCHOR.md", "a55529791254999ca80b3ec3817a7b3124d8b70b91196c6a2f54ad9037d0ed93", 4_020),
        ("docs/audits/fable5-vision-audit-20260725/phase20/SESSION_HN_P1_UPSTREAM_RECONSTRUCTION_RESULT.md", "c711b706127670439295e7091d66c7136ed55bae03b14c0b35d69ce9de4d0755", 8_751),
        ("docs/audits/fable5-vision-audit-20260725/phase20/receipts/SESSION_HN_AB_RECEIPT.md", "f1b5c161f652b142e9436b016b313cfc72faa4c28c2513162a1c8e489654767c", 1_779),
        ("docs/audits/fable5-vision-audit-20260725/phase20/receipts/SESSION_HN_COMPLETE.json", "a9e66330d79ab611303d22ea4102a2d3b3d8c0627431264d52d7086c6f96da5f", 11_548),
        ("docs/audits/fable5-vision-audit-20260725/phase20/receipts/science/P1_INERT_PROFILE_SYMBOL_SNAPSHOT.json", "47fe19e1743a83ffd69fcb0c7948a76e8a2ac0ac1d7c5561996d1306f04e0d8a", 40_171),
        ("docs/audits/fable5-vision-audit-20260725/phase20/receipts/science/P1_INERT_ROUTE_PARAMETER_BUNDLE.json", "988a139e21bf8621a84ddafbfaff4cd9dfb39bcebf2ab6d9d228d9ffdffa4b52", 12_265),
        ("docs/audits/fable5-vision-audit-20260725/phase20/receipts/science/P1_SOURCE_SEARCH_AND_RECONSTRUCTION_LEDGER.json", "8e8c7f442feb92d3907c58bf0cb9aefe4d49a44fbe0579a3f021837b98313956", 44_305),
        ("docs/audits/fable5-vision-audit-20260725/phase20/receipts/science/P1_UPSTREAM_SOURCE_COVERAGE.json", "53816ef4dddae4758be86001eae200bb594210c53953dcdea3fed0cfb28dc020", 3_321),
        ("docs/audits/fable5-vision-audit-20260725/phase20/receipts/science/P1_UPSTREAM_SOURCE_PACKET_MANIFEST.json", "6ca34c80781de72acdcc2377f105be2895ce29932691e880a3469dfc2674f25d", 46_353),
    )),
)

_PRODUCTION_EXPECTATIONS = _PacketExpectations(
    symbols=_SYMBOLS,
    total=73_999,
    window_counts=(("january", 27_658), ("april", 25_056), ("may", 21_285)),
    windows=(("january", ("2026-01-01", "2026-01-30")), ("april", ("2026-04-01", "2026-04-30")), ("may", ("2026-05-01", "2026-05-30"))),
    state_count=52_803,
    payload_count=51,
    reused_candidate_ids=2_357,
    rows_under_reused_candidate_ids=17_206,
    source_payload_count=11,
    source_root=_SOURCE_ROOT,
    repo_root=_REPO_ROOT,
    repo_authorities=_REPO_AUTHORITIES,
    transitive_paths=_TRANSITIVE,
    source_manifests=(
        ("LANE_INPUT_REGISTRY.json", "6415ae522dc48cd85f33a5f35223ce375c07214ad4416df60502d2ec0f10b5de"),
        ("SOURCE_CATALOG.json", "a1a8c5d05a87d1e5a486bdcfea2b23ac082cdb899da51ec2f3e45a37269582e1"),
        ("manifests/january_2026.json", "74ee97e4d379854697920abd7a4ee22693dc2ab72b922e0756b1342053fa5fbc"),
        ("manifests/april_2026.json", "3940c286fed76489bc748cb58453f5172bd32da69c7900df2b5454ac34723344"),
        ("manifests/may_2026.json", "23ebf0592746c55811a5457d3d120460c80ed317c8a5a51637be4579238edf7f"),
    ),
    evidence_lineage=_EVIDENCE_LINEAGE,
    evidence_artifacts=_EVIDENCE_ARTIFACTS,
    tooling_paths=(
        "docs/audits/fable5-vision-audit-20260725/phase20/receipts/wave20_complete_path_shadow.py",
        "src/research_infra/_p1_upstream_packet_expectations.py",
        "src/research_infra/p1_upstream_m1_provenance_verifier.py",
        "src/research_infra/p1_upstream_packet_verifier.py",
        "src/research_infra/p1_upstream_reconstruction.py",
    ),
    source_commit_bound_paths=_TRANSITIVE + (
        "docs/audits/fable5-vision-audit-20260725/phase20/receipts/wave20_complete_path_shadow.py",
        "src/research_infra/_p1_upstream_packet_expectations.py",
        "src/research_infra/p1_upstream_m1_provenance_verifier.py",
        "src/research_infra/p1_upstream_packet_verifier.py",
        "src/research_infra/p1_upstream_reconstruction.py",
    ),
    source_parent="f59fbb829a5561b7e7b78bed324d67a8c01d6e74",
    generator_path="src/components/broader_origin_generators.py",
    generator_sha256="6e274d22a72c945fa495c2b85408f0495acf6158caa2edb0d34bae108b859fba",
    market_state_path="src/components/market_state.py",
    market_state_sha256="c59e1d5ea2e4f2758129bca6b67b1ed86379e3278e5c0d44321542425fc680ee",
    h1_reference_path="src/research_infra/replay_acceleration_slice.py",
    h1_reference_sha256="5736302c6a3efe32a40ca6e2f205448eb6ff7ab1a78f63e9b9c00ff54679008b",
    timebase_sha256="0f97bbb64bc55b0213e47a018c2e884d83b2059b61de7941a171fd3cf2fef552",
    m15_lookback=672,
    h1_lookback=168,
    minimum_closed_m15=51,
    partial_h1_buckets=120,
    referenced_partial_h1_buckets=46,
)
