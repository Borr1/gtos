# Source Hash Deferral Manifest

Route: `GTOS_LOCAL_RESEARCH_DATA_CATALOG_IMPLEMENTATION_ROUTE`
Terminal decision: `ACCEPT_AS_LOCAL_RESEARCH_DATA_CATALOG_TOOLING`
Promotion posture: `NO_PROMOTION_VERDICT`
Required flags: `validation_safe=false`, `outcome_review_opened=false`, `live_effect=false`

## Summary

```json
{
  "artifact_family": "source_hash_deferral_manifest",
  "changes_live_trading_behavior": false,
  "credentials_touched": false,
  "generated_at_utc": "2026-05-10T09:31:31Z",
  "hash_size_limit_bytes": 8388608,
  "hashed_file_count": 1076,
  "hashed_files": [
    {
      "absolute_path": "C:\\tmp\\gtos_otb\\NOFILLTICKRECOVERY\\data\\DXY_D1.csv",
      "catalog_row_id": "LCAT-000001",
      "sha256": "7da2e65e61087b2235fe2a5d6678b56f716a2a6d913be78b663faf1f0fdc23b9",
      "size_bytes": 20017,
      "source_family": "local_research_data"
    },
    {
      "absolute_path": "C:\\tmp\\gtos_otb\\NOFILLTICKRECOVERY\\data\\EURUSD_D1.csv",
      "catalog_row_id": "LCAT-000002",
      "sha256": "cc0dbe2373b9ce94dabb295729e17ad24350281b57d03a9c3d807b3a5c2d60d5",
      "size_bytes": 30108,
      "source_family": "local_research_data"
    },
    {
      "absolute_path": "C:\\tmp\\gtos_otb\\NOFILLTICKRECOVERY\\data\\EURUSD_H1.csv",
      "catalog_row_id": "LCAT-000003",
      "sha256": "17e289eeec2cd1fe9b91723f97c8bb74f0865b8de855027def35e7425b16cd96",
      "size_bytes": 828266,
      "source_family": "local_research_data"
    },
    {
      "absolute_path": "C:\\tmp\\gtos_otb\\NOFILLTICKRECOVERY\\data\\EURUSD_H4.csv",
      "catalog_row_id": "LCAT-000004",
      "sha256": "7c696ae7aa2386f771959485e5af5bf6a51edebfcdc44340a72b15d72b186202",
      "size_bytes": 209541,
      "source_family": "local_research_data"
    },
    {
      "absolute_path": "C:\\tmp\\gtos_otb\\NOFILLTICKRECOVERY\\data\\EURUSD_M15.csv",
      "catalog_row_id": "LCAT-000005",
      "sha256": "d56405a0a11016b368312deca3b59361c14206ca8694c9a372e46451096139f8",
      "size_bytes": 3273362,
      "source_family": "local_research_data"
    },
    {
      "absolute_path": "C:\\tmp\\gtos_otb\\NOFILLTICKRECOVERY\\data\\EURUSD_M5.csv",
      "catalog_row_id": "LCAT-000006",
      "sha256": "41a2d240cfacb029c3f268dca8936d0fb4f3aa9e03d8238c006aab5afd6a3e83",
      "size_bytes": 5291443,
      "source_family": "local_research_data"
    },
    {
      "absolute_path": "C:\\tmp\\gtos_otb\\NOFILLTICKRECOVERY\\data\\GBPUSD_D1.csv",
      "catalog_row_id": "LCAT-000007",
      "sha256": "8722fa67d7b8f70ddc5a856169a80252276f692554e1f732850d8b3a1065aafc",
      "size_bytes": 177741,
      "source_family": "local_research_data"
    },
    {
      "absolute_path": "C:\\tmp\\gtos_otb\\NOFILLTICKRECOVERY\\data\\GBPUSD_H1.csv",
      "catalog_row_id": "LCAT-000008",
      "sha256": "6e24d801081439a611d5d93c61324ae56d9c55279eec75163e325a7ee92c57e8",
      "size_bytes": 1165745,
      "source_family": "local_research_data"
    },
    {
      "absolute_path": "C:\\tmp\\gtos_otb\\NOFILLTICKRECOVERY\\data\\GBPUSD_H4.csv",
      "catalog_row_id": "LCAT-000009",
      "sha256": "81ad64a3d3ad1b351f03a5fa558a9e5ef8b0c227e122961d1c3dc65039834b90",
      "size_bytes": 580221,
      "source_family": "local_research_data"
    },
    {
      "absolute_path": "C:\\tmp\\gtos_otb\\NOFILLTICKRECOVERY\\data\\GBPUSD_M15.csv",
      "catalog_row_id": "LCAT-000010",
      "sha256": "b9df02945dc0b53a8440ed85ddd47d8c94a081cb0071be5aa445acb604ac70f7",
      "size_bytes": 2903066,
      "source_family": "local_research_data"
    },
    {
      "absolute_path": "C:\\tmp\\gtos_otb\\NOFILLTICKRECOVERY\\data\\GBPUSD_M5.csv",
      "catalog_row_id": "LCAT-000011",
      "sha256": "b4571cf13f78561345964d3106854e190ed895f53eb34267a9f808c6346aa65f",
      "size_bytes": 19603,
      "source_family": "local_research_data"
    },
    {
      "absolute_path": "C:\\tmp\\gtos_otb\\NOFILLTICKRECOVERY\\data\\NAS100_D1.csv",
      "catalog_row_id": "LCAT-000012",
      "sha256": "04b7f6b49e67f7575ffa6d7ee64d0cac2e331fb8baaad9cdc8e9d247d09b439c",
      "size_bytes": 28780,
      "source_family": "local_research_data"
    },
    {
      "absolute_path": "C:\\tmp\\gtos_otb\\NOFILLTICKRECOVERY\\data\\NAS100_H1.csv",
      "catalog_row_id": "LCAT-000013",
      "sha256": "b8a028cf1714367f673b3309b801e0903f4583129a1dc2f772c1c5d7a6adc78e",
      "size_bytes": 744327,
      "source_family": "local_research_data"
    },
    {
      "absolute_path": "C:\\tmp\\gtos_otb\\NOFILLTICKRECOVERY\\data\\NAS100_H4.csv",
      "catalog_row_id": "LCAT-000014",
      "sha256": "f6ed040030a8e55579e84c8c6b56b4bee65d4dede9674b8a75c4c573cd8926c3",
      "size_bytes": 197086,
      "source_family": "local_research_data"
    },
    {
      "absolute_path": "C:\\tmp\\gtos_otb\\NOFILLTICKRECOVERY\\data\\NAS100_M15.csv",
      "catalog_row_id": "LCAT-000015",
      "sha256": "ba1e450066659bece6c5374f81b66c58ec78e412db5ada13ef6bf8aae7f03a96",
      "size_bytes": 2934918,
      "source_family": "local_research_data"
    },
    {
      "absolute_path": "C:\\tmp\\gtos_otb\\NOFILLTICKRECOVERY\\data\\NAS100_M5.csv",
      "catalog_row_id": "LCAT-000016",
      "sha256": "88cd6d26393a202a2fcca903463ec58287e206e52aed4620ffb57803ffceefd4",
      "size_bytes": 5301737,
      "source_family": "local_research_data"
    },
    {
      "absolute_path": "C:\\tmp\\gtos_otb\\NOFILLTICKRECOVERY\\data\\XAGUSD_D1.csv",
      "catalog_row_id": "LCAT-000017",
      "sha256": "55b7bb9275ed99c5f37838c70dbefef3025d0a4f1c9406a3ccd8f8c9723949c5",
      "size_bytes": 26899,
      "source_family": "local_research_data"
    },
    {
      "absolute_path": "C:\\tmp\\gtos_otb\\NOFILLTICKRECOVERY\\data\\XAGUSD_H1.csv",
      "catalog_row_id": "LCAT-000018",
      "sha256": "8f9dac30640c47b2c8ae8de60f3e680404aa22e3dce4b81c39347e0698755b30",
      "size_bytes": 723400,
      "source_family": "local_research_data"
    },
    {
      "absolute_path": "C:\\tmp\\gtos_otb\\NOFILLTICKRECOVERY\\data\\XAGUSD_H4.csv",
      "catalog_row_id": "LCAT-000019",
      "sha256": "3cdc3e58284f866ef95012cd7989b8fc7ec8d89535150fda0de32979f62445c7",
      "size_bytes": 189481,
      "source_family": "local_research_data"
    },
    {
      "absolute_path": "C:\\tmp\\gtos_otb\\NOFILLTICKRECOVERY\\data\\XAGUSD_M15.csv",
      "catalog_row_id": "LCAT-000020",
      "sha256": "f80f7ebb87b065f73d20c7f55a95245f8c0d8640f75d1410bd5e1afcac4ce506",
      "size_bytes": 2850025,
      "source_family": "local_research_data"
    },
    {
      "absolute_path": "C:\\tmp\\gtos_otb\\NOFILLTICKRECOVERY\\data\\XAGUSD_M5.csv",
      "catalog_row_id": "LCAT-000021",
      "sha256": "5efd8120a22cd2c99daefe27f41becb1093faccb7de31636aa1000c484e7be45",
      "size_bytes": 4729418,
      "source_family": "local_research_data"
    },
    {
      "absolute_path": "C:\\tmp\\gtos_otb\\NOFILLTICKRECOVERY\\data\\XAUUSD_D1.csv",
      "catalog_row_id": "LCAT-000022",
      "sha256": "fce7d961f04583957f4d7c86eb15420464a79f8610eb2fc66781bf2ebbf34d99",
      "size_bytes": 3872,
      "source_family": "local_research_data"
    },
    {
      "absolute_path": "C:\\tmp\\gtos_otb\\NOFILLTICKRECOVERY\\data\\XAUUSD_H1.csv",
      "catalog_row_id": "LCAT-000023",
      "sha256": "cd15facd79121b6a68cea6f1f96881aa4916e44c06805f6613e45b64078766b5",
      "size_bytes": 12582,
      "source_family": "local_research_data"
    },
    {
      "absolute_path": "C:\\tmp\\gtos_otb\\NOFILLTICKRECOVERY\\data\\XAUUSD_H4.csv",
      "catalog_row_id": "LCAT-000024",
      "sha256": "e2975ab7cee83617719ff9776cea41f31771fa69288fbd858345a0578d66631a",
      "size_bytes": 7613,
      "source_family": "local_research_data"
    },
    {
      "absolute_path": "C:\\tmp\\gtos_otb\\NOFILLTICKRECOVERY\\data\\XAUUSD_M15.csv",
      "catalog_row_id": "LCAT-000025",
      "sha256": "7293d55a8cc1371550fee51f8b3e1a8bda0615583c55fe2c7ec1f4c4b81d83be",
      "size_bytes": 43229,
      "source_family": "local_research_data"
    },
    {
      "absolute_path": "C:\\tmp\\gtos_otb\\NOFILLTICKRECOVERY\\data\\XAUUSD_M5.csv",
      "catalog_row_id": "LCAT-000026",
      "sha256": "cb3a59f34909e69e00dc0a6524624a68f1f185c3d0558e417be3890262d55f44",
      "size_bytes": 18529,
      "source_family": "local_research_data"
    },
    {
      "absolute_path": "C:\\tmp\\gtos_otb\\NOFILLTICKRECOVERY\\data\\economic_calendar.csv",
      "catalog_row_id": "LCAT-000027",
      "sha256": "e82537e05053b9ccbfd0279d884f364a0089daff02a9a731a1a90685fcaae5ce",
      "size_bytes": 1602,
      "source_family": "local_research_data"
    },
    {
      "absolute_path": "C:\\tmp\\gtos_otb\\NOFILLTICKRECOVERY\\data\\news_calendar.json",
      "catalog_row_id": "LCAT-000028",
      "sha256": "569ee7742e395740df0e5ddcbf3fcead19bf26ca2b93ed55d004bfaa263b105d",
      "size_bytes": 4013,
      "source_family": "local_research_data"
    },
    {
      "absolute_path": "C:\\tmp\\gtos_otb\\NOFILLTICKRECOVERY\\data\\external\\validation\\expanded_oos_full_unblocking\\sierra_6b_to_gbpusd_pilot_20260504\\raw_ohlc_prequential_events_20260503T205250Z.jsonl",
      "catalog_row_id": "LCAT-000029",
      "sha256": "3bc61bef9c6ecfd6df9f1696cfcdd2718371803120da966fa0c592b4b37fc634",
      "size_bytes": 91368,
      "source_family": "local_external_or_vendor_cache"
    },
    {
      "absolute_path": "C:\\tmp\\gtos_otb\\NOFILLTICKRECOVERY\\data\\external\\validation\\expanded_oos_full_unblocking\\sierra_6b_to_gbpusd_pilot_20260504\\raw_ohlc_prequential_replay_20260503T205251Z.json",
      "catalog_row_id": "LCAT-000030",
      "sha256": "00ab983d39b0adead0c0ffe19c43860008d3467009a8973ddc49329ab886acab",
      "size_bytes": 28052,
      "source_family": "local_external_or_vendor_cache"
    },
    {
      "absolute_path": "C:\\tmp\\gtos_otb\\NOFILLTICKRECOVERY\\data\\external\\validation\\expanded_oos_full_unblocking\\sierra_6j_to_usdjpy_pilot_20260504\\raw_ohlc_prequential_events_20260503T205250Z.jsonl",
      "catalog_row_id": "LCAT-000031",
      "sha256": "57f61464fb7d8aed2b43e26513b93a18aee517c0052f24fdec7ab07eaddc4c2e",
      "size_bytes": 97535,
      "source_family": "local_external_or_vendor_cache"
    },
    {
      "absolute_path": "C:\\tmp\\gtos_otb\\NOFILLTICKRECOVERY\\data\\external\\validation\\expanded_oos_full_unblocking\\sierra_6j_to_usdjpy_pilot_20260504\\raw_ohlc_prequential_replay_20260503T205251Z.json",
      "catalog_row_id": "LCAT-000032",
      "sha256": "ad5cc93186be2c239f1dc40a81434707ac0abb7b61e791fb9ea5ed06ce16e7fd",
      "size_bytes": 28042,
      "source_family": "local_external_or_vendor_cache"
    },
    {
      "absolute_path": "C:\\tmp\\gtos_otb\\NOFILLTICKRECOVERY\\data\\external\\validation\\expanded_oos_full_unblocking\\sierra_nq_to_nas100_pilot_20260504\\raw_ohlc_prequential_events_20260503T202913Z.jsonl",
      "catalog_row_id": "LCAT-000033",
      "sha256": "c59cb178376bbb3e24d5587c47f2d98b33d8db014203fd76b5bbce74f2d04513",
      "size_bytes": 77834,
      "source_family": "local_external_or_vendor_cache"
    },
    {
      "absolute_path": "C:\\tmp\\gtos_otb\\NOFILLTICKRECOVERY\\data\\external\\validation\\expanded_oos_full_unblocking\\sierra_nq_to_nas100_pilot_20260504\\raw_ohlc_prequential_replay_20260503T202915Z.json",
      "catalog_row_id": "LCAT-000034",
      "sha256": "66212e3b5c3ba7c8bb5a0e027df0e55e3cfba87e039c45583542d8f1a87d3d57",
      "size_bytes": 28101,
      "source_family": "local_external_or_vendor_cache"
    },
    {
      "absolute_path": "C:\\tmp\\gtos_otb\\NOFILLTICKRECOVERY\\data\\external\\validation\\expanded_oos_full_unblocking\\sierra_si_to_xagusd_pilot_20260504\\raw_ohlc_prequential_events_20260503T205250Z.jsonl",
      "catalog_row_id": "LCAT-000035",
      "sha256": "be053ea527394169cfcecc2f9bbc3f5712ffc11f474df9c89c5b4311fc1beefa",
      "size_bytes": 73638,
      "source_family": "local_external_or_vendor_cache"
    },
    {
      "absolute_path": "C:\\tmp\\gtos_otb\\NOFILLTICKRECOVERY\\data\\external\\validation\\expanded_oos_full_unblocking\\sierra_si_to_xagusd_pilot_20260504\\raw_ohlc_prequential_replay_20260503T205252Z.json",
      "catalog_row_id": "LCAT-000036",
      "sha256": "51e14f26e7682d87d2a4ecfb69ec4ea9c868a56d97f1e44c26a893c0302227d9",
      "size_bytes": 28733,
      "source_family": "local_external_or_vendor_cache"
    },
    {
      "absolute_path": "C:\\tmp\\gtos_otb\\NOFILLTICKRECOVERY\\data\\external\\validation\\expanded_oos_full_unblocking\\sierra_si_xagusd_v2_mtf_pilot_20260504\\path_scaling_v2_structural_levels\\raw_ohlc_path_scaling_v2_structural_levels_20260503T205339Z.json",
      "catalog_row_id": "LCAT-000037",
      "sha256": "7e5582d9c7e1dd7691f6d5f6c544dcc07c451992c3fdacf974da6628eeeb4a65",
      "size_bytes": 104394,
      "source_family": "local_external_or_vendor_cache"
    },
    {
      "absolute_path": "C:\\tmp\\gtos_otb\\NOFILLTICKRECOVERY\\data\\external\\validation\\expanded_oos_full_unblocking\\sierra_si_xagusd_v2_mtf_pilot_20260504\\path_scaling_v2_structural_levels\\raw_ohlc_path_scaling_v2_structural_levels_events_20260503T205337Z.jsonl",
      "catalog_row_id": "LCAT-000038",
      "sha256": "438074c74d48ee7b229f5811d279d9be4957b34817062df14ff60e1168870197",
      "size_bytes": 63942,
      "source_family": "local_external_or_vendor_cache"
    },
    {
      "absolute_path": "C:\\tmp\\gtos_otb\\NOFILLTICKRECOVERY\\data\\external\\validation\\expanded_oos_full_unblocking\\sierra_xauusd_scid_to_xauusd_pilot_20260504\\raw_ohlc_prequential_events_20260503T204511Z.jsonl",
      "catalog_row_id": "LCAT-000039",
      "sha256": "ccf8f4633c04aeaa56f2cc85d780f7a4f765f36c7529cd435784e9860d55bada",
      "size_bytes": 77104,
      "source_family": "local_external_or_vendor_cache"
    },
    {
      "absolute_path": "C:\\tmp\\gtos_otb\\NOFILLTICKRECOVERY\\data\\external\\validation\\expanded_oos_full_unblocking\\sierra_xauusd_scid_to_xauusd_pilot_20260504\\raw_ohlc_prequential_replay_20260503T204512Z.json",
      "catalog_row_id": "LCAT-000040",
      "sha256": "2f89b9b22c75d349e79c3bf34545cbbc5144454c8de5ddd5d61f0d88f2365c8b",
      "size_bytes": 28824,
      "source_family": "local_external_or_vendor_cache"
    },
    {
      "absolute_path": "C:\\tmp\\gtos_otb\\NOFILLTICKRECOVERY\\data\\external\\validation\\expanded_oos_full_unblocking\\sierra_xauusd_scid_v2_mtf_pilot_20260504\\path_scaling_v2_structural_levels\\raw_ohlc_path_scaling_v2_structural_levels_20260503T204612Z.json",
      "catalog_row_id": "LCAT-000041",
      "sha256": "367fa351faf46cf7e951e2adcc1aaf55eff7f1c158b6a22a1cfe28914efe7ddd",
      "size_bytes": 113667,
      "source_family": "local_external_or_vendor_cache"
    },
    {
      "absolute_path": "C:\\tmp\\gtos_otb\\NOFILLTICKRECOVERY\\data\\external\\validation\\expanded_oos_full_unblocking\\sierra_xauusd_scid_v2_mtf_pilot_20260504\\path_scaling_v2_structural_levels\\raw_ohlc_path_scaling_v2_structural_levels_events_20260503T204606Z.jsonl",
      "catalog_row_id": "LCAT-000042",
      "sha256": "9777f339f94c713329a89364c6584c7ea7a2acddf5c6cb7b1812c893d984a5c6",
      "size_bytes": 336479,
      "source_family": "local_external_or_vendor_cache"
    },
    {
      "absolute_path": "C:\\tmp\\gtos_otb\\NOFILLTICKRECOVERY\\data\\external\\validation\\expanded_oos_full_unblocking\\sierra_ym_to_us30_cash_pilot_20260504\\raw_ohlc_prequential_events_20260503T204727Z.jsonl",
      "catalog_row_id": "LCAT-000043",
      "sha256": "d5ee79d060f0acd9a52850acbef9cdb8f2196e6caa2a427ea9dce406cc71d570",
      "size_bytes": 51679,
      "source_family": "local_external_or_vendor_cache"
    },
    {
      "absolute_path": "C:\\tmp\\gtos_otb\\NOFILLTICKRECOVERY\\data\\external\\validation\\expanded_oos_full_unblocking\\sierra_ym_to_us30_cash_pilot_20260504\\raw_ohlc_prequential_replay_20260503T204728Z.json",
      "catalog_row_id": "LCAT-000044",
      "sha256": "09ac3561215d4747c00f0a74a8afecb965608f4ba9f5dde2d089d82fe2b1155a",
      "size_bytes": 28788,
      "source_family": "local_external_or_vendor_cache"
    },
    {
      "absolute_path": "C:\\tmp\\gtos_otb\\NOFILLTICKRECOVERY\\data\\external\\validation\\expanded_oos_full_unblocking\\sierra_ym_us30_cash_v2_mtf_pilot_20260504\\path_scaling_v2_structural_levels\\raw_ohlc_path_scaling_v2_structural_levels_20260503T204801Z.json",
      "catalog_row_id": "LCAT-000045",
      "sha256": "a7d5b06a8937138a04f19716a130b38d94e3008d1a311346411594a4befba252",
      "size_bytes": 104112,
      "source_family": "local_external_or_vendor_cache"
    },
    {
      "absolute_path": "C:\\tmp\\gtos_otb\\NOFILLTICKRECOVERY\\data\\external\\validation\\expanded_oos_full_unblocking\\sierra_ym_us30_cash_v2_mtf_pilot_20260504\\path_scaling_v2_structural_levels\\raw_ohlc_path_scaling_v2_structural_levels_events_20260503T204759Z.jsonl",
      "catalog_row_id": "LCAT-000046",
      "sha256": "ea4c4da537282206f0764344af809844cb97e3425f398752536b4918b98bf5a3",
      "size_bytes": 64470,
      "source_family": "local_external_or_vendor_cache"
    },
    {
      "absolute_path": "C:\\tmp\\gtos_otb\\NOFILLTICKRECOVERY\\data\\gold_standard\\README.md",
      "catalog_row_id": "LCAT-000047",
      "sha256": "6407742cb5029a8f21b485724679bda9fdddbc2f1c9aa0414be4968b94609c0a",
      "size_bytes": 1968,
      "source_family": "local_research_data"
    },
    {
      "absolute_path": "C:\\tmp\\gtos_otb\\NOFILLTICKRECOVERY\\data\\historical\\GBPJPY_D1.csv",
      "catalog_row_id": "LCAT-000048",
      "sha256": "9d4e94e05972f9e84aad17814c1056763d0d2f5fabec0d106dfc2a5db75b5cf7",
      "size_bytes": 169315,
      "source_family": "local_research_data"
    },
    {
      "absolute_path": "C:\\tmp\\gtos_otb\\NOFILLTICKRECOVERY\\data\\historical\\GBPJPY_H1.csv",
      "catalog_row_id": "LCAT-000049",
      "sha256": "d609a2de318c4065deb9983b81ad79a98b8fd458bcd5440d81307b3756e3cdad",
      "size_bytes": 1258966,
      "source_family": "local_research_data"
    },
    {
      "absolute_path": "C:\\tmp\\gtos_otb\\NOFILLTICKRECOVERY\\data\\historical\\GBPJPY_H4.csv",
      "catalog_row_id": "LCAT-000050",
      "sha256": "c7d44abc0488ae7be739e57249396fcaf85b599d6683a7777eddfb24cbd42e0b",
      "size_bytes": 625431,
      "source_family": "local_research_data"
    },
    {
      "absolute_path": "C:\\tmp\\gtos_otb\\NOFILLTICKRECOVERY\\data\\historical\\GBPJPY_M15.csv",
      "catalog_row_id": "LCAT-000051",
      "sha256": "3f6eb1b6acf5604a9ea4980c0a9cce79b00b0a0a07aa97900bf9f294a1899ea7",
      "size_bytes": 6231610,
      "source_family": "local_research_data"
    },
    {
      "absolute_path": "C:\\tmp\\gtos_otb\\NOFILLTICKRECOVERY\\data\\historical\\GBPUSD_D1.csv",
      "catalog_row_id": "LCAT-000052",
      "sha256": "8722fa67d7b8f70ddc5a856169a80252276f692554e1f732850d8b3a1065aafc",
      "size_bytes": 177741,
      "source_family": "local_research_data"
    },
    {
      "absolute_path": "C:\\tmp\\gtos_otb\\NOFILLTICKRECOVERY\\data\\historical\\GBPUSD_H1.csv",
      "catalog_row_id": "LCAT-000053",
      "sha256": "6e24d801081439a611d5d93c61324ae56d9c55279eec75163e325a7ee92c57e8",
      "size_bytes": 1165745,
      "source_family": "local_research_data"
    },
    {
      "absolute_path": "C:\\tmp\\gtos_otb\\NOFILLTICKRECOVERY\\data\\historical\\GBPUSD_H4.csv",
      "catalog_row_id": "LCAT-000054",
      "sha256": "81ad64a3d3ad1b351f03a5fa558a9e5ef8b0c227e122961d1c3dc65039834b90",
      "size_bytes": 580221,
      "source_family": "local_research_data"
    },
    {
      "absolute_path": "C:\\tmp\\gtos_otb\\NOFILLTICKRECOVERY\\data\\historical\\GBPUSD_M15.csv",
      "catalog_row_id": "LCAT-000055",
      "sha256": "b9df02945dc0b53a8440ed85ddd47d8c94a081cb0071be5aa445acb604ac70f7",
      "size_bytes": 2903066,
      "source_family": "local_research_data"
    },
    {
      "absolute_path": "C:\\tmp\\gtos_otb\\NOFILLTICKRECOVERY\\data\\historical\\NZDUSD_D1.csv",
      "catalog_row_id": "LCAT-000056",
      "sha256": "780a3c27537b47982d6410833b790e5db2fa99df0dd5ea0fc1840e864005fa1e",
      "size_bytes": 166818,
      "source_family": "local_research_data"
    },
    {
      "absolute_path": "C:\\tmp\\gtos_otb\\NOFILLTICKRECOVERY\\data\\historical\\NZDUSD_H1.csv",
      "catalog_row_id": "LCAT-000057",
      "sha256": "47e60f057476058faeb0dc8a45b24cf28364574bd672f2b86a02758fef81d297",
      "size_bytes": 1228980,
      "source_family": "local_research_data"
    },
    {
      "absolute_path": "C:\\tmp\\gtos_otb\\NOFILLTICKRECOVERY\\data\\historical\\NZDUSD_H4.csv",
      "catalog_row_id": "LCAT-000058",
      "sha256": "5c1b2e1df7b0492cf208223352f55dbc892d24206718a4f82f2dc63b5f388138",
      "size_bytes": 618296,
      "source_family": "local_research_data"
    },
    {
      "absolute_path": "C:\\tmp\\gtos_otb\\NOFILLTICKRECOVERY\\data\\historical\\NZDUSD_M15.csv",
      "catalog_row_id": "LCAT-000059",
      "sha256": "436252af07b6a0195defae41264b73937f6f1f8d98bc25e2b8dc9231a4c6b231",
      "size_bytes": 6069374,
      "source_family": "local_research_data"
    },
    {
      "absolute_path": "C:\\tmp\\gtos_otb\\NOFILLTICKRECOVERY\\data\\historical\\US30_cash_D1.csv",
      "catalog_row_id": "LCAT-000060",
      "sha256": "0ac093c69c17403c7f35d657c4029ff55948f9ba8c59014897f5d7f7a3399315",
      "size_bytes": 113053,
      "source_family": "local_research_data"
    },
    {
      "absolute_path": "C:\\tmp\\gtos_otb\\NOFILLTICKRECOVERY\\data\\historical\\US30_cash_H1.csv",
      "catalog_row_id": "LCAT-000061",
      "sha256": "ecdfa99f7f13e86702aaa1546b082dc871f44266af70e38e6af7ddb227eba371",
      "size_bytes": 1219611,
      "source_family": "local_research_data"
    },
    {
      "absolute_path": "C:\\tmp\\gtos_otb\\NOFILLTICKRECOVERY\\data\\historical\\US30_cash_H4.csv",
      "catalog_row_id": "LCAT-000062",
      "sha256": "4ba5078d94b793c8f890557aff28dcf70a26d76f9c1c1b3914dcea38f6e074d3",
      "size_bytes": 607424,
      "source_family": "local_research_data"
    },
    {
      "absolute_path": "C:\\tmp\\gtos_otb\\NOFILLTICKRECOVERY\\data\\historical\\US30_cash_M15.csv",
      "catalog_row_id": "LCAT-000063",
      "sha256": "f9ceccc23cc2aaf0e42317e240fc92ca15dc48a57a59a9ec66dc71a200160af5",
      "size_bytes": 5988496,
      "source_family": "local_research_data"
    },
    {
      "absolute_path": "C:\\tmp\\gtos_otb\\NOFILLTICKRECOVERY\\data\\historical\\USDJPY_D1.csv",
      "catalog_row_id": "LCAT-000064",
      "sha256": "0ef0fd30b1d91611f959c43d5e9fabb9c0938fcaa30e696601c57549f9336a27",
      "size_bytes": 176916,
      "source_family": "local_research_data"
    },
    {
      "absolute_path": "C:\\tmp\\gtos_otb\\NOFILLTICKRECOVERY\\data\\historical\\USDJPY_H1.csv",
      "catalog_row_id": "LCAT-000065",
      "sha256": "7b49c7820881b0cd5d8968087f4560eb8002b089edec2e8453a7321a97619be1",
      "size_bytes": 1165554,
      "source_family": "local_research_data"
    },
    {
      "absolute_path": "C:\\tmp\\gtos_otb\\NOFILLTICKRECOVERY\\data\\historical\\USDJPY_H4.csv",
      "catalog_row_id": "LCAT-000066",
      "sha256": "6329aa8233334e79953d9ac9223f610c52992eb2e700be4be8b5b387a155e1cc",
      "size_bytes": 580802,
      "source_family": "local_research_data"
    },
    {
      "absolute_path": "C:\\tmp\\gtos_otb\\NOFILLTICKRECOVERY\\data\\historical\\USDJPY_M15.csv",
      "catalog_row_id": "LCAT-000067",
      "sha256": "1bec25612c2d2df700c2d5ecdb8a2e1b0183b3f7c203f3a40f50044733038371",
      "size_bytes": 2905317,
      "source_family": "local_research_data"
    },
    {
      "absolute_path": "C:\\tmp\\gtos_otb\\NOFILLTICKRECOVERY\\data\\historical\\XAUUSD_D1.csv",
      "catalog_row_id": "LCAT-000068",
      "sha256": "f0f6978e8ebae4be6a1adb44a0cbba34e9b3b759a79ff4b663038e2e167114ab",
      "size_bytes": 38755,
      "source_family": "local_research_data"
    },
    {
      "absolute_path": "C:\\tmp\\gtos_otb\\NOFILLTICKRECOVERY\\data\\historical\\XAUUSD_H1.csv",
      "catalog_row_id": "LCAT-000069",
      "sha256": "c52f73add578ac25c7c97a1e15d6d2e0a5b091e50b7526212555b972c6a35888",
      "size_bytes": 868331,
      "source_family": "local_research_data"
    },
    {
      "absolute_path": "C:\\tmp\\gtos_otb\\NOFILLTICKRECOVERY\\data\\historical\\XAUUSD_H4.csv",
      "catalog_row_id": "LCAT-000070",
      "sha256": "8558570b84823b38342ef45b26d029e69129c38ca21dccf02e65411b16c590d8",
      "size_bytes": 270816,
      "source_family": "local_research_data"
    },
    {
      "absolute_path": "C:\\tmp\\gtos_otb\\NOFILLTICKRECOVERY\\data\\historical\\XAUUSD_M1.csv",
      "catalog_row_id": "LCAT-000071",
      "sha256": "e76034fc472b62bcb4968c40aea8e5f94b318d96b6ebaad6e3324be96847b79b",
      "size_bytes": 5645375,
      "source_family": "local_research_data"
    },
    {
      "absolute_path": "C:\\tmp\\gtos_otb\\NOFILLTICKRECOVERY\\data\\historical\\XAUUSD_M15.csv",
      "catalog_row_id": "LCAT-000072",
      "sha256": "7409fb9e48bb6b5d39dfaeb5e26cf446b0ec864caa4d29978d0a874bd37d1ccd",
      "size_bytes": 2768718,
      "source_family": "local_research_data"
    },
    {
      "absolute_path": "C:\\tmp\\gtos_otb\\NOFILLTICKRECOVERY\\data\\historical\\XAUUSD_M5.csv",
      "catalog_row_id": "LCAT-000073",
      "sha256": "358ae52806decee2967d301c006449144c3a6d8dd991c997512955f1c3b43d61",
      "size_bytes": 5670559,
      "source_family": "local_research_data"
    },
    {
      "absolute_path": "C:\\tmp\\gtos_otb\\NOFILLTICKRECOVERY\\data\\historical_2022_2023\\GBPUSD_D1.csv",
      "catalog_row_id": "LCAT-000074",
      "sha256": "312b5bef55da81290eb2cb27d3a5968fd6b9cadcdef19706a9e1aa04ebbeb581",
      "size_bytes": 32841,
      "source_family": "local_research_data"
    },
    {
      "absolute_path": "C:\\tmp\\gtos_otb\\NOFILLTICKRECOVERY\\data\\historical_2022_2023\\GBPUSD_H1.csv",
      "catalog_row_id": "LCAT-000075",
      "sha256": "25d213d97efd714d51e438b9f5d1add776d467a9dc44325ffb140ecd6a704028",
      "size_bytes": 758433,
      "source_family": "local_research_data"
    },
    {
      "absolute_path": "C:\\tmp\\gtos_otb\\NOFILLTICKRECOVERY\\data\\historical_2022_2023\\GBPUSD_H4.csv",
      "catalog_row_id": "LCAT-000076",
      "sha256": "0ab0a4064139aa0951d30ff6b15e121911797b2311c202721587ac0d001207f9",
      "size_bytes": 193746,
      "source_family": "local_research_data"
    },
    {
      "absolute_path": "C:\\tmp\\gtos_otb\\NOFILLTICKRECOVERY\\data\\historical_2022_2023\\GBPUSD_M15.csv",
      "catalog_row_id": "LCAT-000077",
      "sha256": "272e857aa5dae7aedc5a6bffac1a5c1fc671dc0a570d56d5f5f1dbec5ab2df2e",
      "size_bytes": 2616184,
      "source_family": "local_research_data"
    },
    {
      "absolute_path": "C:\\tmp\\gtos_otb\\NOFILLTICKRECOVERY\\data\\historical_2022_2023\\NAS100_D1.csv",
      "catalog_row_id": "LCAT-000078",
      "sha256": "6a3d4d7a27ec7db564f82bb43e344a1bd207f462292140d9abe2ec151634653d",
      "size_bytes": 21214,
      "source_family": "local_research_data"
    },
    {
      "absolute_path": "C:\\tmp\\gtos_otb\\NOFILLTICKRECOVERY\\data\\historical_2022_2023\\NAS100_H1.csv",
      "catalog_row_id": "LCAT-000079",
      "sha256": "f49a1c6874d0c36fe5ffe31ad3035620da5ac8a12309092ad53312e82f1aa446",
      "size_bytes": 448795,
      "source_family": "local_research_data"
    },
    {
      "absolute_path": "C:\\tmp\\gtos_otb\\NOFILLTICKRECOVERY\\data\\historical_2022_2023\\NAS100_H4.csv",
      "catalog_row_id": "LCAT-000080",
      "sha256": "59aab076ebf2cb3872f6969f19919591e9701b8a945a0b711224efebe58d6f88",
      "size_bytes": 123725,
      "source_family": "local_research_data"
    },
    {
      "absolute_path": "C:\\tmp\\gtos_otb\\NOFILLTICKRECOVERY\\data\\historical_2022_2023\\NAS100_M15.csv",
      "catalog_row_id": "LCAT-000081",
      "sha256": "fd87af6e1f6c0fb790cdab8ad57a178e6a65b7dc709781808d9d6622fad6ca41",
      "size_bytes": 1298557,
      "source_family": "local_research_data"
    },
    {
      "absolute_path": "C:\\tmp\\gtos_otb\\NOFILLTICKRECOVERY\\data\\historical_2022_2023\\USDJPY_D1.csv",
      "catalog_row_id": "LCAT-000082",
      "sha256": "4c7565edd7b9503ff3f1ccedc72938664d9d96de72a74f2442c9b285780f1acc",
      "size_bytes": 32919,
      "source_family": "local_research_data"
    },
    {
      "absolute_path": "C:\\tmp\\gtos_otb\\NOFILLTICKRECOVERY\\data\\historical_2022_2023\\USDJPY_H1.csv",
      "catalog_row_id": "LCAT-000083",
      "sha256": "e8965c3210cef50afe851354703dd5b63cd6694145d31f0974cc262963c9e636",
      "size_bytes": 759194,
      "source_family": "local_research_data"
    },
    {
      "absolute_path": "C:\\tmp\\gtos_otb\\NOFILLTICKRECOVERY\\data\\historical_2022_2023\\USDJPY_H4.csv",
      "catalog_row_id": "LCAT-000084",
      "sha256": "61329a742e53acd60e072d830a5476bf1748f91619bc2eeea6fecc0ccdf5959c",
      "size_bytes": 193980,
      "source_family": "local_research_data"
    },
    {
      "absolute_path": "C:\\tmp\\gtos_otb\\NOFILLTICKRECOVERY\\data\\historical_2022_2023\\USDJPY_M15.csv",
      "catalog_row_id": "LCAT-000085",
      "sha256": "8e9576a3bbcdf00dbffaaf528c7f52e904639d29f7b1967b0ce0c06dd7046ddc",
      "size_bytes": 2618295,
      "source_family": "local_research_data"
    },
    {
      "absolute_path": "C:\\tmp\\gtos_otb\\NOFILLTICKRECOVERY\\data\\historical_2022_2023\\XAGUSD_D1.csv",
      "catalog_row_id": "LCAT-000086",
      "sha256": "07ddc3d9b2a4027c14e494d8f2cd4d2836045064cdb4e07e37e31d60f75667e2",
      "size_bytes": 29968,
      "source_family": "local_research_data"
    },
    {
      "absolute_path": "C:\\tmp\\gtos_otb\\NOFILLTICKRECOVERY\\data\\historical_2022_2023\\XAGUSD_H1.csv",
      "catalog_row_id": "LCAT-000087",
      "sha256": "104c4d992f77fe9f9f9b47efa39775a10a2751295ee6f09e35eba4a084beaed5",
      "size_bytes": 640466,
      "source_family": "local_research_data"
    },
    {
      "absolute_path": "C:\\tmp\\gtos_otb\\NOFILLTICKRECOVERY\\data\\historical_2022_2023\\XAGUSD_H4.csv",
      "catalog_row_id": "LCAT-000088",
      "sha256": "0d311fd5fb2d4f5f86bfa14983168f5f06d64a16afe514d5f78d80bbbf0ec4ea",
      "size_bytes": 176763,
      "source_family": "local_research_data"
    },
    {
      "absolute_path": "C:\\tmp\\gtos_otb\\NOFILLTICKRECOVERY\\data\\historical_2022_2023\\XAGUSD_M15.csv",
      "catalog_row_id": "LCAT-000089",
      "sha256": "e61b6d79a115f6316c944acc814a11066d9be20fa2941f046760d76341b30542",
      "size_bytes": 2522520,
      "source_family": "local_research_data"
    },
    {
      "absolute_path": "C:\\tmp\\gtos_otb\\NOFILLTICKRECOVERY\\data\\historical_2022_2023\\XAUUSD_D1.csv",
      "catalog_row_id": "LCAT-000090",
      "sha256": "d40633811d002848b107cead59e35fc95ddf77822d915069de404c86e6e4f511",
      "size_bytes": 32480,
      "source_family": "local_research_data"
    },
    {
      "absolute_path": "C:\\tmp\\gtos_otb\\NOFILLTICKRECOVERY\\data\\historical_2022_2023\\XAUUSD_H1.csv",
      "catalog_row_id": "LCAT-000091",
      "sha256": "1172c5b6ad961ee9f97d77e293da6b6ab9b5dca5760d109f8040ff705f0d0049",
      "size_bytes": 723927,
      "source_family": "local_research_data"
    },
    {
      "absolute_path": "C:\\tmp\\gtos_otb\\NOFILLTICKRECOVERY\\data\\historical_2022_2023\\XAUUSD_H4.csv",
      "catalog_row_id": "LCAT-000092",
      "sha256": "066538178d09f2bd1a8e030e390eb902506b14118e4a1be130377fb479329f0a",
      "size_bytes": 191895,
      "source_family": "local_research_data"
    },
    {
      "absolute_path": "C:\\tmp\\gtos_otb\\NOFILLTICKRECOVERY\\data\\historical_2022_2023\\XAUUSD_M15.csv",
      "catalog_row_id": "LCAT-000093",
      "sha256": "b831f0010cae009a270622321f71e5a1dcbe156ee2ed3b0a9ec2c315e1b1bae4",
      "size_bytes": 2757794,
      "source_family": "local_research_data"
    },
    {
      "absolute_path": "C:\\tmp\\gtos_otb\\NOFILLTICKRECOVERY\\data\\historical_2022_2023\\trade_cohort.csv",
      "catalog_row_id": "LCAT-000094",
      "sha256": "fad64baede6ac09cc70a1600a46ef70bb2cf5e1d5ab56e3bdadace0d95dcaeb0",
      "size_bytes": 305404,
      "source_family": "local_research_data"
    },
    {
      "absolute_path": "C:\\tmp\\gtos_otb\\NOFILLTICKRECOVERY\\data\\historical_2022_2023\\trade_cohort.jsonl",
      "catalog_row_id": "LCAT-000095",
      "sha256": "7480f2faadd75123c555100ac88be6911645262205997bec16d68a79ffc00ec3",
      "size_bytes": 2225450,
      "source_family": "local_research_data"
    },
    {
      "absolute_path": "C:\\tmp\\gtos_otb\\NOFILLTICKRECOVERY\\data\\historical_2022_2023\\trade_cohort_missing_symbols_2026-05-03.csv",
      "catalog_row_id": "LCAT-000096",
      "sha256": "4496a9949d62214aca9ca749c5bbf3a52b3a2f17a904f212e666b71b5d4c46b4",
      "size_bytes": 87151,
      "source_family": "local_research_data"
    },
    {
      "absolute_path": "C:\\tmp\\gtos_otb\\NOFILLTICKRECOVERY\\data\\historical_2022_2023\\trade_cohort_missing_symbols_2026-05-03.jsonl",
      "catalog_row_id": "LCAT-000097",
      "sha256": "c4769abc9f89205b2f817fb043c5e6e7590841d781b0866eaa8140351ef9be48",
      "size_bytes": 544242,
      "source_family": "local_research_data"
    },
    {
      "absolute_path": "C:\\tmp\\gtos_otb\\NOFILLTICKRECOVERY\\data\\historical_2026\\AUDJPY_D1.csv",
      "catalog_row_id": "LCAT-000098",
      "sha256": "3656087b80178d88d95cabb071682011bbec5829447aaadecc80d885ff5730de",
      "size_bytes": 4099,
      "source_family": "local_research_data"
    },
    {
      "absolute_path": "C:\\tmp\\gtos_otb\\NOFILLTICKRECOVERY\\data\\historical_2026\\AUDJPY_H1.csv",
      "catalog_row_id": "LCAT-000099",
      "sha256": "487c00ae72face53dec761de86085f0f8a3040f5bdb04e593ea0e6ce2643eb96",
      "size_bytes": 111742,
      "source_family": "local_research_data"
    },
    {
      "absolute_path": "C:\\tmp\\gtos_otb\\NOFILLTICKRECOVERY\\data\\historical_2026\\AUDJPY_H4.csv",
      "catalog_row_id": "LCAT-000100",
      "sha256": "dc0f57e524f9ea977715f6a842b21a1b6e1cbd8ebb07d36b0ce14f32150cc36c",
      "size_bytes": 28436,
      "source_family": "local_research_data"
    },
    {
      "absolute_path": "C:\\tmp\\gtos_otb\\NOFILLTICKRECOVERY\\data\\historical_2026\\AUDJPY_M15.csv",
      "catalog_row_id": "LCAT-000101",
      "sha256": "85a9b50da7a2eb76ff7a01d4dc1f9ce048b572ee8def2f587a543240323725bb",
      "size_bytes": 443670,
      "source_family": "local_research_data"
    },
    {
      "absolute_path": "C:\\tmp\\gtos_otb\\NOFILLTICKRECOVERY\\data\\historical_2026\\AUDUSD_D1.csv",
      "catalog_row_id": "LCAT-000102",
      "sha256": "0b0c7968615294f6c8474e0505dcbcec17495f84e4dc3fe98e2ad16da26545b0",
      "size_bytes": 4072,
      "source_family": "local_research_data"
    },
    {
      "absolute_path": "C:\\tmp\\gtos_otb\\NOFILLTICKRECOVERY\\data\\historical_2026\\AUDUSD_H1.csv",
      "catalog_row_id": "LCAT-000103",
      "sha256": "52f6ec5a9089be518fef48d29833473e030f5525af318084a622ded9a4e07996",
      "size_bytes": 110719,
      "source_family": "local_research_data"
    },
    {
      "absolute_path": "C:\\tmp\\gtos_otb\\NOFILLTICKRECOVERY\\data\\historical_2026\\AUDUSD_H4.csv",
      "catalog_row_id": "LCAT-000104",
      "sha256": "f7391fab3751b86a2514bed33977c92375cedd6212c4a7a6bc51fb77484c9288",
      "size_bytes": 28064,
      "source_family": "local_research_data"
    },
    {
      "absolute_path": "C:\\tmp\\gtos_otb\\NOFILLTICKRECOVERY\\data\\historical_2026\\AUDUSD_M15.csv",
      "catalog_row_id": "LCAT-000105",
      "sha256": "bd09aa18aea6ec1681867473450a1aa06f3c39d88b19e4d5fbcff0ce19275eac",
      "size_bytes": 437911,
      "source_family": "local_research_data"
    },
    {
      "absolute_path": "C:\\tmp\\gtos_otb\\NOFILLTICKRECOVERY\\data\\historical_2026\\BTCUSD_D1.csv",
      "catalog_row_id": "LCAT-000106",
      "sha256": "2395bd5e6ca51e234b5eae6eeb4485b8429e293b482561c177e5080a875f4053",
      "size_bytes": 6234,
      "source_family": "local_research_data"
    },
    {
      "absolute_path": "C:\\tmp\\gtos_otb\\NOFILLTICKRECOVERY\\data\\historical_2026\\BTCUSD_H1.csv",
      "catalog_row_id": "LCAT-000107",
      "sha256": "cbd02e75097095971358d4dcef3bd8c11b4374cb0bcb7ecddb85fe51ffaedc52",
      "size_bytes": 165108,
      "source_family": "local_research_data"
    },
    {
      "absolute_path": "C:\\tmp\\gtos_otb\\NOFILLTICKRECOVERY\\data\\historical_2026\\BTCUSD_H4.csv",
      "catalog_row_id": "LCAT-000108",
      "sha256": "e14db3524c0490d9ed3d2f3c927f84f8ca83b6e5eb5fe53dd8c2ca346ca9fc77",
      "size_bytes": 42378,
      "source_family": "local_research_data"
    },
    {
      "absolute_path": "C:\\tmp\\gtos_otb\\NOFILLTICKRECOVERY\\data\\historical_2026\\BTCUSD_M15.csv",
      "catalog_row_id": "LCAT-000109",
      "sha256": "0067a165343ef6d8801902a15955bf21fbb37badd72f2001c71bb6b7096778a1",
      "size_bytes": 650704,
      "source_family": "local_research_data"
    },
    {
      "absolute_path": "C:\\tmp\\gtos_otb\\NOFILLTICKRECOVERY\\data\\historical_2026\\CHFJPY_D1.csv",
      "catalog_row_id": "LCAT-000110",
      "sha256": "b1a5bf8571cd051d31fd1fe01a89d8c0c8cecbcc437c917f46ca85ce70476a6e",
      "size_bytes": 4113,
      "source_family": "local_research_data"
    },
    {
      "absolute_path": "C:\\tmp\\gtos_otb\\NOFILLTICKRECOVERY\\data\\historical_2026\\CHFJPY_H1.csv",
      "catalog_row_id": "LCAT-000111",
      "sha256": "1f88c0b35936129957c17606d815dcdc6bbaab3a8e7a7da6c01c23eaa4c94d7d",
      "size_bytes": 111757,
      "source_family": "local_research_data"
    },
    {
      "absolute_path": "C:\\tmp\\gtos_otb\\NOFILLTICKRECOVERY\\data\\historical_2026\\CHFJPY_H4.csv",
      "catalog_row_id": "LCAT-000112",
      "sha256": "e17790a2600f815dc5b648ee8adf39edcf4f1a57dc9426b47c9bbd7e395c1a96",
      "size_bytes": 28468,
      "source_family": "local_research_data"
    },
    {
      "absolute_path": "C:\\tmp\\gtos_otb\\NOFILLTICKRECOVERY\\data\\historical_2026\\CHFJPY_M15.csv",
      "catalog_row_id": "LCAT-000113",
      "sha256": "a023c6b42289955501690e3e651d722493a02afdabc0d069b13327214d329558",
      "size_bytes": 443350,
      "source_family": "local_research_data"
    },
    {
      "absolute_path": "C:\\tmp\\gtos_otb\\NOFILLTICKRECOVERY\\data\\historical_2026\\ETHUSD_D1.csv",
      "catalog_row_id": "LCAT-000114",
      "sha256": "454495f2f03b497d253338f4242bf812ed8539c02ddf1aa78496222f14ad1fc7",
      "size_bytes": 5753,
      "source_family": "local_research_data"
    },
    {
      "absolute_path": "C:\\tmp\\gtos_otb\\NOFILLTICKRECOVERY\\data\\historical_2026\\ETHUSD_H1.csv",
      "catalog_row_id": "LCAT-000115",
      "sha256": "16485d018bda89a772792ae82b975c9ebc869a072ae0a63e3d6325c7a9b0111f",
      "size_bytes": 152794,
      "source_family": "local_research_data"
    },
    {
      "absolute_path": "C:\\tmp\\gtos_otb\\NOFILLTICKRECOVERY\\data\\historical_2026\\ETHUSD_H4.csv",
      "catalog_row_id": "LCAT-000116",
      "sha256": "5859fc33ec5b889042f83d3812e9468bdeff19ba9a6f726a693846c5f051c8b4",
      "size_bytes": 39524,
      "source_family": "local_research_data"
    },
    {
      "absolute_path": "C:\\tmp\\gtos_otb\\NOFILLTICKRECOVERY\\data\\historical_2026\\ETHUSD_M15.csv",
      "catalog_row_id": "LCAT-000117",
      "sha256": "dec1a8a8c0ac4706da9ab03064fbdc1c9faff728af9498c76fb01ba244cff8ab",
      "size_bytes": 603589,
      "source_family": "local_research_data"
    },
    {
      "absolute_path": "C:\\tmp\\gtos_otb\\NOFILLTICKRECOVERY\\data\\historical_2026\\EURGBP_D1.csv",
      "catalog_row_id": "LCAT-000118",
      "sha256": "07077b7ab3f48be033dec897145f80d484c7256bdfdff21ecb536b6381b59aff",
      "size_bytes": 4047,
      "source_family": "local_research_data"
    },
    {
      "absolute_path": "C:\\tmp\\gtos_otb\\NOFILLTICKRECOVERY\\data\\historical_2026\\EURGBP_H1.csv",
      "catalog_row_id": "LCAT-000119",
      "sha256": "e1125c74c316fec758c16109818eff6e06b0dd3faf2c652d233ecd4fa4359c53",
      "size_bytes": 111580,
      "source_family": "local_research_data"
    },
    {
      "absolute_path": "C:\\tmp\\gtos_otb\\NOFILLTICKRECOVERY\\data\\historical_2026\\EURGBP_H4.csv",
      "catalog_row_id": "LCAT-000120",
      "sha256": "a507fd444d34c88475d43f42862af9f11e435ba6afba3225fb5cf0a5f42e0c93",
      "size_bytes": 28229,
      "source_family": "local_research_data"
    },
    {
      "absolute_path": "C:\\tmp\\gtos_otb\\NOFILLTICKRECOVERY\\data\\ticks\\README.md",
      "catalog_row_id": "LCAT-000121",
      "sha256": "5d39bfb408bb06f6a6d264ab7fa05de90a843c15f0b778841014c72591cc0e63",
      "size_bytes": 5376,
      "source_family": "mt5_tick_control_file"
    },
    {
      "absolute_path": "C:\\tmp\\gtos_otb\\NOFILLTICKRECOVERY\\shadow_logs\\canary_restart_governance_status.jsonl",
      "catalog_row_id": "LCAT-000122",
      "sha256": "e4ec1f07030444ffe6983e36432c9fead5102b4bdd66b656abd848581e137eeb",
      "size_bytes": 8453,
      "source_family": "shadow_log_source_control"
    },
    {
      "absolute_path": "C:\\tmp\\gtos_otb\\NOFILLTICKRECOVERY\\shadow_logs\\candidate_mso_snapshot_joins.jsonl",
      "catalog_row_id": "LCAT-000125",
      "sha256": "205cb1a95eace166d57a337025cd2e503a1880bb7d703bfa4858e4c51917e9e7",
      "size_bytes": 250212,
      "source_family": "shadow_log_source_control"
    },
    {
      "absolute_path": "C:\\tmp\\gtos_otb\\NOFILLTICKRECOVERY\\shadow_logs\\candidate_path_contract_audit.jsonl",
      "catalog_row_id": "LCAT-000126",
      "sha256": "a57f61333dafeaf73a841784ea1927b05860198a0ac6edeed08f3844a34d239f",
      "size_bytes": 5172490,
      "source_family": "shadow_log_source_control"
    },
    {
      "absolute_path": "C:\\tmp\\gtos_otb\\NOFILLTICKRECOVERY\\shadow_logs\\candidate_registry_audit.jsonl",
      "catalog_row_id": "LCAT-000128",
      "sha256": "1183d41f8af0914d1d398c1bda2d1cf6b9147f88c0c24e10a178a9697d78b5b0",
      "size_bytes": 439794,
      "source_family": "shadow_log_source_control"
    },
    {
      "absolute_path": "C:\\tmp\\gtos_otb\\NOFILLTICKRECOVERY\\shadow_logs\\context_control_ledger.jsonl",
      "catalog_row_id": "LCAT-000130",
      "sha256": "9df7b5a3190c5eaddf0463f0a20d00151e3559342a630cb95844267c3cf69ecd",
      "size_bytes": 683478,
      "source_family": "shadow_log_source_control"
    },
    {
      "absolute_path": "C:\\tmp\\gtos_otb\\NOFILLTICKRECOVERY\\shadow_logs\\continuation_no_retrace_candidates.jsonl",
      "catalog_row_id": "LCAT-000131",
      "sha256": "6e0638b56a6ee70629dacd7bae94aefab249ef7c7232c6c3dc5bd0c3818d22bb",
      "size_bytes": 162403,
      "source_family": "shadow_log_source_control"
    },
    {
      "absolute_path": "C:\\tmp\\gtos_otb\\NOFILLTICKRECOVERY\\shadow_logs\\continuation_no_retrace_resolutions.jsonl",
      "catalog_row_id": "LCAT-000132",
      "sha256": "026257a77b6a0918424b711a7c9c40c46c778eba72fe21b5bcfad9e7069540f7",
      "size_bytes": 481204,
      "source_family": "shadow_log_source_control"
    },
    {
      "absolute_path": "C:\\tmp\\gtos_otb\\NOFILLTICKRECOVERY\\shadow_logs\\cusum_candidate_rate_daily.csv",
      "catalog_row_id": "LCAT-000133",
      "sha256": "d1fdb1734e745e25e154d75881df7a2a22bdfb3e8b294e19940899ef97dc6795",
      "size_bytes": 1449,
      "source_family": "shadow_log_source_control"
    },
    {
      "absolute_path": "C:\\tmp\\gtos_otb\\NOFILLTICKRECOVERY\\shadow_logs\\d1_bias_lag.jsonl",
      "catalog_row_id": "LCAT-000134",
      "sha256": "ef4db1499b39010345eb70f122319d77f462c95a8125921638b6a1cea6580521",
      "size_bytes": 112900,
      "source_family": "shadow_log_source_control"
    },
    {
      "absolute_path": "C:\\tmp\\gtos_otb\\NOFILLTICKRECOVERY\\shadow_logs\\d1_bias_lag_recovery.jsonl",
      "catalog_row_id": "LCAT-000135",
      "sha256": "c587923050cc1915e88b291f4c4b8075cb2083db9c8ded6ea5848359111d704b",
      "size_bytes": 9355,
      "source_family": "shadow_log_source_control"
    },
    {
      "absolute_path": "C:\\tmp\\gtos_otb\\NOFILLTICKRECOVERY\\shadow_logs\\databento_live_budget_ledger.jsonl",
      "catalog_row_id": "LCAT-000136",
      "sha256": "27c560f3efd1090ec6924229430a990263f8d96129e58bfe84367e0ed80cf1a5",
      "size_bytes": 4581,
      "source_family": "shadow_log_source_control"
    },
    {
      "absolute_path": "C:\\tmp\\gtos_otb\\NOFILLTICKRECOVERY\\shadow_logs\\databento_live_confluence.jsonl",
      "catalog_row_id": "LCAT-000137",
      "sha256": "001fd5fdf3b20d28e2a1fe4577f7ff550bd74fa0cf77b6bcd7199ff139a9fd86",
      "size_bytes": 12682,
      "source_family": "shadow_log_source_control"
    },
    {
      "absolute_path": "C:\\tmp\\gtos_otb\\NOFILLTICKRECOVERY\\shadow_logs\\databento_live_trigger_decisions.jsonl",
      "catalog_row_id": "LCAT-000138",
      "sha256": "c756c7f5b304be84cf9dbc0fb476f2a5db2eb22226e030a5c1b8ddd68e945fc5",
      "size_bytes": 332195,
      "source_family": "shadow_log_source_control"
    },
    {
      "absolute_path": "C:\\tmp\\gtos_otb\\NOFILLTICKRECOVERY\\shadow_logs\\decision_layer_diagnostics_join.jsonl",
      "catalog_row_id": "LCAT-000139",
      "sha256": "fdd555da8d593d27312119a5ce0726c86c41df2353252e7dc4348a547e0b4c82",
      "size_bytes": 1227750,
      "source_family": "shadow_log_source_control"
    },
    {
      "absolute_path": "C:\\tmp\\gtos_otb\\NOFILLTICKRECOVERY\\shadow_logs\\direction_emission_xau_audit.jsonl",
      "catalog_row_id": "LCAT-000140",
      "sha256": "967fdff0ae7b741e8f1d0e8a0d6b8edf5d718312b0f9d1011338d26c0ab98879",
      "size_bytes": 102182,
      "source_family": "shadow_log_source_control"
    },
    {
      "absolute_path": "C:\\tmp\\gtos_otb\\NOFILLTICKRECOVERY\\shadow_logs\\displacement_events.jsonl",
      "catalog_row_id": "LCAT-000141",
      "sha256": "d77803f48d602a6e12f32eaa03cfc78121231403d4625969c5250e1f104abf7b",
      "size_bytes": 55730,
      "source_family": "shadow_log_source_control"
    },
    {
      "absolute_path": "C:\\tmp\\gtos_otb\\NOFILLTICKRECOVERY\\shadow_logs\\drawdown_state_changes.jsonl",
      "catalog_row_id": "LCAT-000142",
      "sha256": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
      "size_bytes": 0,
      "source_family": "shadow_log_source_control"
    },
    {
      "absolute_path": "C:\\tmp\\gtos_otb\\NOFILLTICKRECOVERY\\shadow_logs\\dumb_baseline_hypotheticals.jsonl",
      "catalog_row_id": "LCAT-000143",
      "sha256": "fd2cb9ee1876942b40e5b7648fd0b109f1e42fb3f0f7cddeb1eb7b15000b0662",
      "size_bytes": 11987,
      "source_family": "shadow_log_source_control"
    },
    {
      "absolute_path": "C:\\tmp\\gtos_otb\\NOFILLTICKRECOVERY\\shadow_logs\\equity_read_anomalies.jsonl",
      "catalog_row_id": "LCAT-000144",
      "sha256": "0e6809452a3bfd8ab26c1fc01975fe997b01e8cbab6bef6c7e535ee75e08bd67",
      "size_bytes": 10646,
      "source_family": "shadow_log_source_control"
    },
    {
      "absolute_path": "C:\\tmp\\gtos_otb\\NOFILLTICKRECOVERY\\shadow_logs\\es_mes_preregistration_status.jsonl",
      "catalog_row_id": "LCAT-000145",
      "sha256": "ac1535dc783ef18500c0779e84434f1ca17063c1109a63218294a44cb1cbca1e",
      "size_bytes": 32568,
      "source_family": "shadow_log_source_control"
    },
    {
      "absolute_path": "C:\\tmp\\gtos_otb\\NOFILLTICKRECOVERY\\shadow_logs\\exit_management_shadow_status.jsonl",
      "catalog_row_id": "LCAT-000146",
      "sha256": "5ad9ef49b75ff90d2ef32cd1fec581543c74256fbb0a88a8745f1d38ce854f5c",
      "size_bytes": 806533,
      "source_family": "shadow_log_source_control"
    },
    {
      "absolute_path": "C:\\tmp\\gtos_otb\\NOFILLTICKRECOVERY\\shadow_logs\\expired_poi_revalidation.jsonl",
      "catalog_row_id": "LCAT-000147",
      "sha256": "a013f9a988a2634ef4b05738cfc58738cb815709a4413a8181e0ff1a4aa1f3a8",
      "size_bytes": 5180,
      "source_family": "shadow_log_source_control"
    },
    {
      "absolute_path": "C:\\tmp\\gtos_otb\\NOFILLTICKRECOVERY\\shadow_logs\\external_source_blocker_status.jsonl",
      "catalog_row_id": "LCAT-000148",
      "sha256": "e9e9721bafe950d449515f3008554426c36978ecc4240da473e51d2c7ffdd723",
      "size_bytes": 829764,
      "source_family": "shadow_log_source_control"
    },
    {
      "absolute_path": "C:\\tmp\\gtos_otb\\NOFILLTICKRECOVERY\\shadow_logs\\fn_smoke_20260420_084920.json",
      "catalog_row_id": "LCAT-000149",
      "sha256": "335de55f9bd5db047e54a88b56430eeb533f2932e86455212ea4694eeb371f46",
      "size_bytes": 2329,
      "source_family": "shadow_log_source_control"
    },
    {
      "absolute_path": "C:\\tmp\\gtos_otb\\NOFILLTICKRECOVERY\\shadow_logs\\fn_smoke_20260420_085002.json",
      "catalog_row_id": "LCAT-000150",
      "sha256": "d2ac7f8c5d2a8733f8f498601c7c4ce821f9ee21519e057fc31d660dbbfc41eb",
      "size_bytes": 2435,
      "source_family": "shadow_log_source_control"
    },
    {
      "absolute_path": "C:\\tmp\\gtos_otb\\NOFILLTICKRECOVERY\\shadow_logs\\fn_smoke_20260420_091430.json",
      "catalog_row_id": "LCAT-000151",
      "sha256": "2786a231a17f054550283273d449bf2cf0218594fa78c6fa08431f95192135a4",
      "size_bytes": 2455,
      "source_family": "shadow_log_source_control"
    },
    {
      "absolute_path": "C:\\tmp\\gtos_otb\\NOFILLTICKRECOVERY\\shadow_logs\\fn_smoke_20260420_091722.json",
      "catalog_row_id": "LCAT-000152",
      "sha256": "1f2667f75d340718eba7ab98d3676aa65bed24b85494903e0dfe0c5ac9b117b7",
      "size_bytes": 2455,
      "source_family": "shadow_log_source_control"
    },
    {
      "absolute_path": "C:\\tmp\\gtos_otb\\NOFILLTICKRECOVERY\\shadow_logs\\fn_smoke_20260420_092228.json",
      "catalog_row_id": "LCAT-000153",
      "sha256": "c0148f9cb344482ac2ae8834253315cf09d52512b862e40d68ad53e62f921def",
      "size_bytes": 3359,
      "source_family": "shadow_log_source_control"
    },
    {
      "absolute_path": "C:\\tmp\\gtos_otb\\NOFILLTICKRECOVERY\\shadow_logs\\fn_smoke_20260420_093645.json",
      "catalog_row_id": "LCAT-000154",
      "sha256": "63303d2b0bf41548fa4cf23fbd1083821b766bf2d219546c63a91f46e95f9b53",
      "size_bytes": 2487,
      "source_family": "shadow_log_source_control"
    },
    {
      "absolute_path": "C:\\tmp\\gtos_otb\\NOFILLTICKRECOVERY\\shadow_logs\\fn_smoke_20260420_094825.json",
      "catalog_row_id": "LCAT-000155",
      "sha256": "775b52c06552ec75687bca48fe22a4857adfe99c929ac4ea2a9e8e8c59e10c1d",
      "size_bytes": 3400,
      "source_family": "shadow_log_source_control"
    },
    {
      "absolute_path": "C:\\tmp\\gtos_otb\\NOFILLTICKRECOVERY\\shadow_logs\\fn_smoke_20260427_084407.json",
      "catalog_row_id": "LCAT-000156",
      "sha256": "dbad7414e6393de8d7873674ca4f2b71cdffb70b50a7dfc24147225e23236651",
      "size_bytes": 3463,
      "source_family": "shadow_log_source_control"
    },
    {
      "absolute_path": "C:\\tmp\\gtos_otb\\NOFILLTICKRECOVERY\\shadow_logs\\fn_smoke_20260427_084506.json",
      "catalog_row_id": "LCAT-000157",
      "sha256": "76fd5051bd2e2758db36ccdc3e86abb41ea70f456c37bbad84b63507fc89c140",
      "size_bytes": 4693,
      "source_family": "shadow_log_source_control"
    },
    {
      "absolute_path": "C:\\tmp\\gtos_otb\\NOFILLTICKRECOVERY\\shadow_logs\\fvg_ob_confluence.jsonl",
      "catalog_row_id": "LCAT-000158",
      "sha256": "d0a8b7f1f5f1df3344cfee9ba9cd5b7371792236d9c184aaf800df63ea55206b",
      "size_bytes": 250834,
      "source_family": "shadow_log_source_control"
    },
    {
      "absolute_path": "C:\\tmp\\gtos_otb\\NOFILLTICKRECOVERY\\shadow_logs\\gbpjpy_proxy_gap_status.jsonl",
      "catalog_row_id": "LCAT-000161",
      "sha256": "4ccf498d1aa03cbdba5f312af3c66e2400b2089868e5ac88d44ddf38ee172e68",
      "size_bytes": 28956,
      "source_family": "shadow_log_source_control"
    },
    {
      "absolute_path": "C:\\tmp\\gtos_otb\\NOFILLTICKRECOVERY\\shadow_logs\\heartbeat_flatten_events.jsonl",
      "catalog_row_id": "LCAT-000162",
      "sha256": "f71fc4d03f426f01b7f9c86cf11b6a206f44357f98fdcac9358bea3a8e38e807",
      "size_bytes": 199300,
      "source_family": "shadow_log_source_control"
    },
    {
      "absolute_path": "C:\\tmp\\gtos_otb\\NOFILLTICKRECOVERY\\shadow_logs\\j46_j49_exit_comparator_audit.jsonl",
      "catalog_row_id": "LCAT-000163",
      "sha256": "812a6aae9415d7d3a7d511873219af3028d01e32691932ef997c5fdb5e0c0e83",
      "size_bytes": 7813705,
      "source_family": "shadow_log_source_control"
    },
    {
      "absolute_path": "C:\\tmp\\gtos_otb\\NOFILLTICKRECOVERY\\shadow_logs\\j46_j49_shadow_outcomes.jsonl",
      "catalog_row_id": "LCAT-000164",
      "sha256": "21ae7b923daccc769d2da04fb97480df5a6d7bb03ebd1763cb57f5c9c655845f",
      "size_bytes": 2360,
      "source_family": "shadow_log_source_control"
    },
    {
      "absolute_path": "C:\\tmp\\gtos_otb\\NOFILLTICKRECOVERY\\shadow_logs\\liquidity_distance_log.jsonl",
      "catalog_row_id": "LCAT-000165",
      "sha256": "86c423334efce8ebfd15d0622ff1ace7c3db9d4fc6d067c0cae53ba04438cfbc",
      "size_bytes": 217361,
      "source_family": "shadow_log_source_control"
    },
    {
      "absolute_path": "C:\\tmp\\gtos_otb\\NOFILLTICKRECOVERY\\shadow_logs\\live_monitor.jsonl",
      "catalog_row_id": "LCAT-000169",
      "sha256": "494ac2d093185e693de0793c00ac9c78773f240409db2efac451fbe08a91f048",
      "size_bytes": 3427078,
      "source_family": "shadow_log_source_control"
    },
    {
      "absolute_path": "C:\\tmp\\gtos_otb\\NOFILLTICKRECOVERY\\shadow_logs\\live_monitor_alerts.jsonl",
      "catalog_row_id": "LCAT-000170",
      "sha256": "cca4163fc610b17a440ca96a8dfb5ca96d4907657ff44f2f5545aadd50cdfd99",
      "size_bytes": 29556,
      "source_family": "shadow_log_source_control"
    },
    {
      "absolute_path": "C:\\tmp\\gtos_otb\\NOFILLTICKRECOVERY\\shadow_logs\\live_monitoring_maintenance_runs.jsonl",
      "catalog_row_id": "LCAT-000171",
      "sha256": "405b79e64312179ba27e439b4376a4c20e9404d7db3dc05c3148a8dd339030b3",
      "size_bytes": 2224863,
      "source_family": "shadow_log_source_control"
    },
    {
      "absolute_path": "C:\\tmp\\gtos_otb\\NOFILLTICKRECOVERY\\shadow_logs\\lto_blocked_lane_status.jsonl",
      "catalog_row_id": "LCAT-000173",
      "sha256": "c12bf28c011dda5cc4cd1cf7d6bdc74381a5be9d0984004d9e87b5e5c61a4cb3",
      "size_bytes": 2375,
      "source_family": "shadow_log_source_control"
    },
    {
      "absolute_path": "C:\\tmp\\gtos_otb\\NOFILLTICKRECOVERY\\shadow_logs\\m15_choch_diagnostic_audit.jsonl",
      "catalog_row_id": "LCAT-000174",
      "sha256": "6a8bc975236beb1f69814a32b26e5939456d24702749369ffce1db31ad9c1520",
      "size_bytes": 649990,
      "source_family": "shadow_log_source_control"
    },
    {
      "absolute_path": "C:\\tmp\\gtos_otb\\NOFILLTICKRECOVERY\\shadow_logs\\malformed_responses.jsonl",
      "catalog_row_id": "LCAT-000175",
      "sha256": "8f22898aad05e74f8b23d04dc3a2f1c861b51d9543ba47ee6de233510a88145c",
      "size_bytes": 12341,
      "source_family": "shadow_log_source_control"
    },
    {
      "absolute_path": "C:\\tmp\\gtos_otb\\NOFILLTICKRECOVERY\\shadow_logs\\missed_opportunity_shadow.jsonl",
      "catalog_row_id": "LCAT-000177",
      "sha256": "ca9e5b1d25f6274e536dffc91610f64a6840365a3aff071e7ef8e2c820e0c5a5",
      "size_bytes": 7607024,
      "source_family": "shadow_log_source_control"
    },
    {
      "absolute_path": "C:\\tmp\\gtos_otb\\NOFILLTICKRECOVERY\\shadow_logs\\ml_shadow_status.jsonl",
      "catalog_row_id": "LCAT-000179",
      "sha256": "a5acc8e48d974b58db9901e91cf20ee014b8cc4993b0c91e34d5be5a468ce6c9",
      "size_bytes": 146390,
      "source_family": "shadow_log_source_control"
    },
    {
      "absolute_path": "C:\\tmp\\gtos_otb\\NOFILLTICKRECOVERY\\shadow_logs\\nas100_orderflow_adverse_selection_status.jsonl",
      "catalog_row_id": "LCAT-000180",
      "sha256": "72a047029b2bca100d268bb9c117b45b832e8cb2d6e36590c4f6697b1692074b",
      "size_bytes": 134808,
      "source_family": "shadow_log_source_control"
    },
    {
      "absolute_path": "C:\\tmp\\gtos_otb\\NOFILLTICKRECOVERY\\shadow_logs\\notification_queue_dead_zone_status.jsonl",
      "catalog_row_id": "LCAT-000181",
      "sha256": "3eb64cbf8d4a62e2e5c82a942400bf4a9b18ef7f586636817f08814565980cf7",
      "size_bytes": 22000,
      "source_family": "shadow_log_source_control"
    },
    {
      "absolute_path": "C:\\tmp\\gtos_otb\\NOFILLTICKRECOVERY\\shadow_logs\\ob_continuation_daily.csv",
      "catalog_row_id": "LCAT-000182",
      "sha256": "4ea3390cd1c5244e96679b64be60929148b9405acea13784a6a8828bc4d8f2de",
      "size_bytes": 5162,
      "source_family": "shadow_log_source_control"
    },
    {
      "absolute_path": "C:\\tmp\\gtos_otb\\NOFILLTICKRECOVERY\\shadow_logs\\orderflow_primitives_status.jsonl",
      "catalog_row_id": "LCAT-000184",
      "sha256": "f7044bfd096a872504d7c0a0b1e019ff1b1a81e27c162593b01be62bcfcec13c",
      "size_bytes": 400003,
      "source_family": "shadow_log_source_control"
    },
    {
      "absolute_path": "C:\\tmp\\gtos_otb\\NOFILLTICKRECOVERY\\shadow_logs\\partial_close_backtest.jsonl",
      "catalog_row_id": "LCAT-000185",
      "sha256": "6712a2b9f71d6c7d3b80bb79452bf3b8814873909d4e389d7381631a5a1624aa",
      "size_bytes": 23591,
      "source_family": "shadow_log_source_control"
    },
    {
      "absolute_path": "C:\\tmp\\gtos_otb\\NOFILLTICKRECOVERY\\shadow_logs\\partial_close_backtest_exact_only.jsonl",
      "catalog_row_id": "LCAT-000186",
      "sha256": "de0885ec8662ac0bcfc30d007cd8dbe3a2c08722678d99c1a92035c31a42ede3",
      "size_bytes": 5922,
      "source_family": "shadow_log_source_control"
    },
    {
      "absolute_path": "C:\\tmp\\gtos_otb\\NOFILLTICKRECOVERY\\shadow_logs\\pending_limit_lifecycle.jsonl",
      "catalog_row_id": "LCAT-000187",
      "sha256": "f0c45eb94d70b94e9e4eb6aebcb4943f3864a7f1cdb37c6003631337e8b9ad49",
      "size_bytes": 461124,
      "source_family": "shadow_log_source_control"
    },
    {
      "absolute_path": "C:\\tmp\\gtos_otb\\NOFILLTICKRECOVERY\\shadow_logs\\pending_limit_lifecycle_audit.jsonl",
      "catalog_row_id": "LCAT-000188",
      "sha256": "a639889d645a232f032fe40adca6f114b48b3a23df9e487fbb7901c456ce6c13",
      "size_bytes": 261922,
      "source_family": "shadow_log_source_control"
    },
    {
      "absolute_path": "C:\\tmp\\gtos_otb\\NOFILLTICKRECOVERY\\shadow_logs\\pending_limit_lifecycle_join_backfill.jsonl",
      "catalog_row_id": "LCAT-000189",
      "sha256": "0a146d00f936b85aa730f9e209d1b6ffb1cc387070944420d634c3aff5f504a0",
      "size_bytes": 528146,
      "source_family": "shadow_log_source_control"
    },
    {
      "absolute_path": "C:\\tmp\\gtos_otb\\NOFILLTICKRECOVERY\\shadow_logs\\prefill_delivery_path.jsonl",
      "catalog_row_id": "LCAT-000190",
      "sha256": "16b04e67a69ba90608516f0a276cd7ef4396bc111606cac651dedb241fd823f7",
      "size_bytes": 249181,
      "source_family": "shadow_log_source_control"
    },
    {
      "absolute_path": "C:\\tmp\\gtos_otb\\NOFILLTICKRECOVERY\\shadow_logs\\proximity_shadow_log.jsonl",
      "catalog_row_id": "LCAT-000193",
      "sha256": "979c398eda2a53eef25406e42449ec31dd3c363ec0523d14ecec768d47b3c165",
      "size_bytes": 156032,
      "source_family": "shadow_log_source_control"
    },
    {
      "absolute_path": "C:\\tmp\\gtos_otb\\NOFILLTICKRECOVERY\\shadow_logs\\proxy_blocker_status.jsonl",
      "catalog_row_id": "LCAT-000194",
      "sha256": "52c6fc31b4051fd493561b5cf1aa543fa37cf9b3e440c07abd569b0a1034e838",
      "size_bytes": 134603,
      "source_family": "shadow_log_source_control"
    },
    {
      "absolute_path": "C:\\tmp\\gtos_otb\\NOFILLTICKRECOVERY\\shadow_logs\\regime_classifications.jsonl",
      "catalog_row_id": "LCAT-000195",
      "sha256": "59ac2b2b26f4eff418e90a4dc5f595d30f565192cafaaf0bf85e809c9f1c028a",
      "size_bytes": 694802,
      "source_family": "shadow_log_source_control"
    },
    {
      "absolute_path": "C:\\tmp\\gtos_otb\\NOFILLTICKRECOVERY\\shadow_logs\\s79_side_aware_risk_context.jsonl",
      "catalog_row_id": "LCAT-000197",
      "sha256": "2a78699a0f45792cf6c16f6451fe98be8e342822b1cac808d060279380eacf99",
      "size_bytes": 483803,
      "source_family": "shadow_log_source_control"
    },
    {
      "absolute_path": "C:\\tmp\\gtos_otb\\NOFILLTICKRECOVERY\\shadow_logs\\session_volatility_log.csv",
      "catalog_row_id": "LCAT-000198",
      "sha256": "716e7ed9bdce0cccf6ba863fd72b06e01e1192b02bb791ba8532e73986490a35",
      "size_bytes": 1210,
      "source_family": "shadow_log_source_control"
    },
    {
      "absolute_path": "C:\\tmp\\gtos_otb\\NOFILLTICKRECOVERY\\shadow_logs\\session_volatility_sweep_status.jsonl",
      "catalog_row_id": "LCAT-000199",
      "sha256": "a13ee19fa7d778ffd1c1286d5c28b0fbbba69ddf8fd25dff8118d3dd53145c34",
      "size_bytes": 21123,
      "source_family": "shadow_log_source_control"
    },
    {
      "absolute_path": "C:\\tmp\\gtos_otb\\NOFILLTICKRECOVERY\\shadow_logs\\shadow_observer_hardening_status.jsonl",
      "catalog_row_id": "LCAT-000200",
      "sha256": "550aeb07295dadb3ac7dd26917d3a625cc456f10d21bc1bd1316c81de6c202fa",
      "size_bytes": 1023705,
      "source_family": "shadow_log_source_control"
    },
    {
      "absolute_path": "C:\\tmp\\gtos_otb\\NOFILLTICKRECOVERY\\shadow_logs\\shadow_observer_status.jsonl",
      "catalog_row_id": "LCAT-000201",
      "sha256": "43ef3e1443f8571ea922476854b48c88568457e2349d15183bbcbae7309ae7e6",
      "size_bytes": 3550203,
      "source_family": "shadow_log_source_control"
    },
    {
      "absolute_path": "C:\\tmp\\gtos_otb\\NOFILLTICKRECOVERY\\shadow_logs\\shadow_observer_tick_enrichment.jsonl",
      "catalog_row_id": "LCAT-000202",
      "sha256": "201e166b60ed1a11602a459dc2633c477476fff5346646531e082743c463cd06",
      "size_bytes": 145107,
      "source_family": "shadow_log_source_control"
    },
    {
      "absolute_path": "C:\\tmp\\gtos_otb\\NOFILLTICKRECOVERY\\shadow_logs\\sierra_6b_si_depth_policy_status.jsonl",
      "catalog_row_id": "LCAT-000203",
      "sha256": "abc46d121097efd849256e798f03834a96721119f984b281b01d0a6c2004ba61",
      "size_bytes": 8188,
      "source_family": "shadow_log_source_control"
    },
    {
      "absolute_path": "C:\\tmp\\gtos_otb\\NOFILLTICKRECOVERY\\shadow_logs\\sierra_confluence_source_status.jsonl",
      "catalog_row_id": "LCAT-000204",
      "sha256": "2ef44ab5d69ed3f3556965e52991b865008e37534eba6316af269de062a94b96",
      "size_bytes": 282678,
      "source_family": "shadow_log_source_control"
    },
    {
      "absolute_path": "C:\\tmp\\gtos_otb\\NOFILLTICKRECOVERY\\shadow_logs\\sierra_depth_enrichment_status.jsonl",
      "catalog_row_id": "LCAT-000205",
      "sha256": "9fee06c1067321b2ee65da8fc522a66c042a2e61989f3ba7677a1a0dad581a2c",
      "size_bytes": 267716,
      "source_family": "shadow_log_source_control"
    },
    {
      "absolute_path": "C:\\tmp\\gtos_otb\\NOFILLTICKRECOVERY\\shadow_logs\\sierra_depth_feature_snapshots.jsonl",
      "catalog_row_id": "LCAT-000206",
      "sha256": "e3332f991a1d075881d4434d819cb895d52b8efdca946ae04b9273e85d5a668e",
      "size_bytes": 775124,
      "source_family": "shadow_log_source_control"
    },
    {
      "absolute_path": "C:\\tmp\\gtos_otb\\NOFILLTICKRECOVERY\\shadow_logs\\sierra_proxy_registry_status.jsonl",
      "catalog_row_id": "LCAT-000207",
      "sha256": "4d4dcaa8aed424f9ec997b5e9ebdf4d8a0b72c1596d53f96dc7f224212d26ccc",
      "size_bytes": 4748121,
      "source_family": "shadow_log_source_control"
    },
    {
      "absolute_path": "C:\\tmp\\gtos_otb\\NOFILLTICKRECOVERY\\shadow_logs\\sl_beyond_ob_decisions.jsonl",
      "catalog_row_id": "LCAT-000208",
      "sha256": "6ac23db82fbe361cf37dc5b1f99c424b13fbb59423551f2cbdffbeb73bfc9bbe",
      "size_bytes": 121628,
      "source_family": "shadow_log_source_control"
    },
    {
      "absolute_path": "C:\\tmp\\gtos_otb\\NOFILLTICKRECOVERY\\shadow_logs\\slippage.jsonl",
      "catalog_row_id": "LCAT-000209",
      "sha256": "0b2ca6047809394efae7f5cc3c5beb96185d92de23740a056d08623a4ac2e9c9",
      "size_bytes": 1070,
      "source_family": "shadow_log_source_control"
    },
    {
      "absolute_path": "C:\\tmp\\gtos_otb\\NOFILLTICKRECOVERY\\shadow_logs\\storage_retention_status.jsonl",
      "catalog_row_id": "LCAT-000210",
      "sha256": "39cdbb1652d19ff2035607b6dcd98364d9d1ced291628b8281c5c45c91a44b32",
      "size_bytes": 143361,
      "source_family": "shadow_log_source_control"
    },
    {
      "absolute_path": "C:\\tmp\\gtos_otb\\NOFILLTICKRECOVERY\\shadow_logs\\strategy_follow_candidates.jsonl",
      "catalog_row_id": "LCAT-000211",
      "sha256": "79a78b9c8bc4f521de6a774d1519a90446fe6e731ef6626c6d9a1e126ee27e57",
      "size_bytes": 2461794,
      "source_family": "shadow_log_source_control"
    },
    {
      "absolute_path": "C:\\tmp\\gtos_otb\\NOFILLTICKRECOVERY\\shadow_logs\\structure_detector_backfill_2022_2023.jsonl",
      "catalog_row_id": "LCAT-000213",
      "sha256": "519a5ea6ab9550183acf77ba22e5e77d8edd645923dede76a27c18656a55cb90",
      "size_bytes": 5518263,
      "source_family": "shadow_log_source_control"
    },
    {
      "absolute_path": "C:\\tmp\\gtos_otb\\NOFILLTICKRECOVERY\\shadow_logs\\structure_detector_backfill_2026.jsonl",
      "catalog_row_id": "LCAT-000214",
      "sha256": "9c3913d6efa0ab57e95ecef1231829ffcd109f7e4ec5c556792e62e8429e783f",
      "size_bytes": 1323973,
      "source_family": "shadow_log_source_control"
    },
    {
      "absolute_path": "C:\\tmp\\gtos_otb\\NOFILLTICKRECOVERY\\shadow_logs\\structure_detector_divergences.jsonl",
      "catalog_row_id": "LCAT-000215",
      "sha256": "5a84a44648aa030add5d81549a42b8ef9c8f4de4abf583b61fda80564bd2de94",
      "size_bytes": 136023,
      "source_family": "shadow_log_source_control"
    },
    {
      "absolute_path": "C:\\tmp\\gtos_otb\\NOFILLTICKRECOVERY\\shadow_logs\\sweep_divergence_log.csv",
      "catalog_row_id": "LCAT-000216",
      "sha256": "c19adb6a7a08b7318a5c7710cb81cb3f06687b0e144143837da1f22a26ea1496",
      "size_bytes": 979,
      "source_family": "shadow_log_source_control"
    },
    {
      "absolute_path": "C:\\tmp\\gtos_otb\\NOFILLTICKRECOVERY\\shadow_logs\\touch_count_gate_decisions.jsonl",
      "catalog_row_id": "LCAT-000217",
      "sha256": "81de75d58aac0da8362581db3fc181267782347ffa4413460d5a338a60851ef0",
      "size_bytes": 29758,
      "source_family": "shadow_log_source_control"
    },
    {
      "absolute_path": "C:\\tmp\\gtos_otb\\NOFILLTICKRECOVERY\\shadow_logs\\trade_index_lifecycle_audit.jsonl",
      "catalog_row_id": "LCAT-000218",
      "sha256": "2a234fb618c0a38ffa66e15e64981e7c520d46b2ddb8d6abc2babe283e54fa2a",
      "size_bytes": 930106,
      "source_family": "shadow_log_source_control"
    },
    {
      "absolute_path": "C:\\tmp\\gtos_otb\\NOFILLTICKRECOVERY\\shadow_logs\\v2_structural_selector_readiness.jsonl",
      "catalog_row_id": "LCAT-000219",
      "sha256": "74ce5a2a4422757a6e5ca7318903d9a26c610ae4c291bc601ca7c97b49da30fb",
      "size_bytes": 756772,
      "source_family": "shadow_log_source_control"
    },
    {
      "absolute_path": "C:\\tmp\\gtos_otb\\NOFILLTICKRECOVERY\\shadow_logs\\v2b_forward_pairs.jsonl",
      "catalog_row_id": "LCAT-000222",
      "sha256": "1ab66f998e12d68f9cabf0897c2e0ce4984f26a78464c52fe4bc89532192546e",
      "size_bytes": 237883,
      "source_family": "shadow_log_source_control"
    },
    {
      "absolute_path": "C:\\tmp\\gtos_otb\\NOFILLTICKRECOVERY\\shadow_logs\\xagusd_fresh_ob_late_ny.jsonl",
      "catalog_row_id": "LCAT-000223",
      "sha256": "50ca99f876709a1c76c06d0ca74c6a24b7dab6a62a1ae9641b90e10a081e369d",
      "size_bytes": 113707,
      "source_family": "shadow_log_source_control"
    },
    {
      "absolute_path": "C:\\tmp\\gtos_otb\\NOFILLTICKRECOVERY\\shadow_logs\\xauusd_same_market_extension_status.jsonl",
      "catalog_row_id": "LCAT-000224",
      "sha256": "1dc3928b72b5744705282136fdcbd8b62ab0906b655e7ddd188d6199b881caed",
      "size_bytes": 568076,
      "source_family": "shadow_log_source_control"
    },
    {
      "absolute_path": "C:\\tmp\\gtos_otb\\NOFILLTICKRECOVERY\\shadow_logs\\.contaminated_backup\\drawdown_state_changes_pre_2026-04-17.jsonl",
      "catalog_row_id": "LCAT-000225",
      "sha256": "1e7d3d7d0d76aa9ae3349045ba6b6837af2e218f243b1beefc07bd8a6d5ea9b3",
      "size_bytes": 65917,
      "source_family": "shadow_log_source_control"
    },
    {
      "absolute_path": "C:\\tmp\\gtos_otb\\NOFILLTICKRECOVERY\\exports\\ftmo_spread_check.json",
      "catalog_row_id": "LCAT-000226",
      "sha256": "4108ee44a2d01a12418fc2551d9505fb21add3a4838e6e709019fdf69b1cfd91",
      "size_bytes": 4076,
      "source_family": "owner_or_tool_export"
    },
    {
      "absolute_path": "C:\\tmp\\gtos_otb\\NOFILLTICKRECOVERY\\exports\\reasoning_text_mining_findings.json",
      "catalog_row_id": "LCAT-000227",
      "sha256": "311c0e38ae8ca2bad3be25b30a7d42f6d4728079b09b7706fb7dd727f6bb4f14",
      "size_bytes": 701,
      "source_family": "owner_or_tool_export"
    },
    {
      "absolute_path": "C:\\tmp\\gtos_otb\\NOFILLTICKRECOVERY\\exports\\candle_redownload\\GBPUSD_D1.csv",
      "catalog_row_id": "LCAT-000228",
      "sha256": "2835f639cb79a998db5586d13f8780876877eedca8f4236780156d5b9a1a2e39",
      "size_bytes": 34654,
      "source_family": "owner_or_tool_export"
    },
    {
      "absolute_path": "C:\\tmp\\gtos_otb\\NOFILLTICKRECOVERY\\exports\\candle_redownload\\GBPUSD_H1.csv",
      "catalog_row_id": "LCAT-000229",
      "sha256": "c47d3715ba3c98387b9fba0a62e40b7419445149f70ef6aa9a573bd9fdaa6ffa",
      "size_bytes": 938675,
      "source_family": "owner_or_tool_export"
    },
    {
      "absolute_path": "C:\\tmp\\gtos_otb\\NOFILLTICKRECOVERY\\exports\\candle_redownload\\GBPUSD_H4.csv",
      "catalog_row_id": "LCAT-000230",
      "sha256": "c6d80dfcf063e000bc2b5b155c64396c38d8421eb28636d0f0c9e6df7d622d3b",
      "size_bytes": 236906,
      "source_family": "owner_or_tool_export"
    },
    {
      "absolute_path": "C:\\tmp\\gtos_otb\\NOFILLTICKRECOVERY\\exports\\candle_redownload\\GBPUSD_M15.csv",
      "catalog_row_id": "LCAT-000231",
      "sha256": "f9e21276b493077a2b0c722b361e6d0d2cb4824fc141b756dec7ff7fab7f97d3",
      "size_bytes": 3714551,
      "source_family": "owner_or_tool_export"
    },
    {
      "absolute_path": "C:\\tmp\\gtos_otb\\NOFILLTICKRECOVERY\\exports\\candle_redownload\\XAUUSD_D1.csv",
      "catalog_row_id": "LCAT-000232",
      "sha256": "1812d48d0dd043380980b43208c685bbff50c3af6907a9b4330565b3ab60ea3b",
      "size_bytes": 32212,
      "source_family": "owner_or_tool_export"
    },
    {
      "absolute_path": "C:\\tmp\\gtos_otb\\NOFILLTICKRECOVERY\\exports\\candle_redownload\\candle_export_summary.json",
      "catalog_row_id": "LCAT-000233",
      "sha256": "47de8c674af39e0b44ed45525f669f093c2e492ddc2456260a841147e833fc16",
      "size_bytes": 2935,
      "source_family": "owner_or_tool_export"
    },
    {
      "absolute_path": "C:\\tmp\\gtos_otb\\NOFILLTICKRECOVERY\\exports\\mt5_data_dump\\GBPUSD_M1_recent.csv",
      "catalog_row_id": "LCAT-000234",
      "sha256": "fe8e976a3e3473bfb7d1c70ed97b2b621adca83c9f19d7b45d581be3889a7f0e",
      "size_bytes": 7636290,
      "source_family": "owner_or_tool_export"
    },
    {
      "absolute_path": "C:\\tmp\\gtos_otb\\NOFILLTICKRECOVERY\\exports\\mt5_data_dump\\XAUUSD_M1_recent.csv",
      "catalog_row_id": "LCAT-000235",
      "sha256": "37a01399c462dc8160f04502085f307c5fcb42e422507b78827fbc78bb109403",
      "size_bytes": 7245921,
      "source_family": "owner_or_tool_export"
    },
    {
      "absolute_path": "C:\\tmp\\gtos_otb\\NOFILLTICKRECOVERY\\exports\\mt5_data_dump\\economic_calendar_summary.json",
      "catalog_row_id": "LCAT-000236",
      "sha256": "346c1a12fc1b2c3cf8cc94bf85677518ea41f51391cdbc865c09b0e04d8b00aa",
      "size_bytes": 478,
      "source_family": "owner_or_tool_export"
    },
    {
      "absolute_path": "C:\\tmp\\gtos_otb\\NOFILLTICKRECOVERY\\exports\\mt5_data_dump\\hourly_volatility_profile.json",
      "catalog_row_id": "LCAT-000237",
      "sha256": "2fc57f154b4d23903bb3f6556135be984c58f69b745334cbf6ec65f6cd036b7b",
      "size_bytes": 41134,
      "source_family": "owner_or_tool_export"
    },
    {
      "absolute_path": "C:\\tmp\\gtos_otb\\NOFILLTICKRECOVERY\\exports\\mt5_data_dump\\m1_data_summary.json",
      "catalog_row_id": "LCAT-000238",
      "sha256": "2473fe3381ae172f11c0309d58e6240c481d24ccac808265705cf79888c30fd2",
      "size_bytes": 1714,
      "source_family": "owner_or_tool_export"
    },
    {
      "absolute_path": "C:\\tmp\\gtos_otb\\NOFILLTICKRECOVERY\\exports\\mt5_data_dump\\tick_data_availability.json",
      "catalog_row_id": "LCAT-000239",
      "sha256": "4a3163384718b2d904a437f3a04a58596a968d4178ee9b0953b2181adc7e8c0a",
      "size_bytes": 3821,
      "source_family": "owner_or_tool_export"
    },
    {
      "absolute_path": "C:\\tmp\\gtos_otb\\NOFILLTICKRECOVERY\\exports\\mt5_data_dump\\trade_entry_spreads.json",
      "catalog_row_id": "LCAT-000240",
      "sha256": "646bb232442495cb8c4f0868775b42d1cf7ffa74bc5df4f63b43374fcc3b3ab8",
      "size_bytes": 128,
      "source_family": "owner_or_tool_export"
    },
    {
      "absolute_path": "C:\\tmp\\gtos_otb\\NOFILLTICKRECOVERY\\exports\\multi_instrument\\AUDUSD_D1.csv",
      "catalog_row_id": "LCAT-000241",
      "sha256": "3830bd5ca0f53bff5e6ff1a5f15656094179cc0e872e4c5cb2a488089da88005",
      "size_bytes": 166870,
      "source_family": "owner_or_tool_export"
    },
    {
      "absolute_path": "C:\\tmp\\gtos_otb\\NOFILLTICKRECOVERY\\exports\\multi_instrument\\AUDUSD_H1.csv",
      "catalog_row_id": "LCAT-000242",
      "sha256": "fba5b0b2b32a0b98ca9206d3b3d336a694666817614fa86f45acf1cf084bbb1b",
      "size_bytes": 1229727,
      "source_family": "owner_or_tool_export"
    },
    {
      "absolute_path": "C:\\tmp\\gtos_otb\\NOFILLTICKRECOVERY\\exports\\multi_instrument\\AUDUSD_H4.csv",
      "catalog_row_id": "LCAT-000243",
      "sha256": "07bc8ed0b8fd86583682dbbace724d50afcd11d733daf5ace099712b52830055",
      "size_bytes": 619405,
      "source_family": "owner_or_tool_export"
    },
    {
      "absolute_path": "C:\\tmp\\gtos_otb\\NOFILLTICKRECOVERY\\exports\\multi_instrument\\EURJPY_D1.csv",
      "catalog_row_id": "LCAT-000244",
      "sha256": "082994b36fb334a425f32cee4ade988882ab6a69a4c75c6ae5aa8625bc757a37",
      "size_bytes": 168818,
      "source_family": "owner_or_tool_export"
    },
    {
      "absolute_path": "C:\\tmp\\gtos_otb\\NOFILLTICKRECOVERY\\exports\\multi_instrument\\EURJPY_H1.csv",
      "catalog_row_id": "LCAT-000245",
      "sha256": "cb90d14c8b62d993ef43bf2f49fd73829b01644f65d4577797eb8accdb3655aa",
      "size_bytes": 1242552,
      "source_family": "owner_or_tool_export"
    },
    {
      "absolute_path": "C:\\tmp\\gtos_otb\\NOFILLTICKRECOVERY\\exports\\multi_instrument\\EURJPY_H4.csv",
      "catalog_row_id": "LCAT-000246",
      "sha256": "60e5acf19005b278de78d1f5b6fbe23f2a96fd39692ce394bc32576eed364646",
      "size_bytes": 624889,
      "source_family": "owner_or_tool_export"
    },
    {
      "absolute_path": "C:\\tmp\\gtos_otb\\NOFILLTICKRECOVERY\\exports\\multi_instrument\\EURUSD_D1.csv",
      "catalog_row_id": "LCAT-000247",
      "sha256": "7abb8b391e3bf6e58e129f416333596b7b35393d552d16255f396b9a71ebb897",
      "size_bytes": 172828,
      "source_family": "owner_or_tool_export"
    },
    {
      "absolute_path": "C:\\tmp\\gtos_otb\\NOFILLTICKRECOVERY\\exports\\multi_instrument\\EURUSD_H1.csv",
      "catalog_row_id": "LCAT-000248",
      "sha256": "acf7b4e93d90a6e67f1107bdd1bfda658fc3d46989d8bcf735316a8f80145364",
      "size_bytes": 1262939,
      "source_family": "owner_or_tool_export"
    },
    {
      "absolute_path": "C:\\tmp\\gtos_otb\\NOFILLTICKRECOVERY\\exports\\multi_instrument\\EURUSD_H4.csv",
      "catalog_row_id": "LCAT-000249",
      "sha256": "66b32aac4c4d28927c03be9075dc1168285450880a141be6c2381b35ecd4c06a",
      "size_bytes": 637818,
      "source_family": "owner_or_tool_export"
    },
    {
      "absolute_path": "C:\\tmp\\gtos_otb\\NOFILLTICKRECOVERY\\exports\\multi_instrument\\EURUSD_M15.csv",
      "catalog_row_id": "LCAT-000250",
      "sha256": "54ef4a2234026fa92f2ce569ffeba1187146090ddc68049cbb1fcf260431611f",
      "size_bytes": 3133903,
      "source_family": "owner_or_tool_export"
    },
    {
      "absolute_path": "C:\\tmp\\gtos_otb\\NOFILLTICKRECOVERY\\exports\\multi_instrument\\GBPJPY_D1.csv",
      "catalog_row_id": "LCAT-000251",
      "sha256": "7976b90504924dbc7babda5f40126b46b429b357a076c50baeb595974df5e646",
      "size_bytes": 169320,
      "source_family": "owner_or_tool_export"
    },
    {
      "absolute_path": "C:\\tmp\\gtos_otb\\NOFILLTICKRECOVERY\\exports\\multi_instrument\\GBPJPY_H1.csv",
      "catalog_row_id": "LCAT-000252",
      "sha256": "e680a8ed7296351f4151b1da0c6220c42510641aff57aa49e6d1252d671fbf79",
      "size_bytes": 1244019,
      "source_family": "owner_or_tool_export"
    },
    {
      "absolute_path": "C:\\tmp\\gtos_otb\\NOFILLTICKRECOVERY\\exports\\multi_instrument\\GBPJPY_H4.csv",
      "catalog_row_id": "LCAT-000253",
      "sha256": "56fbfa4f3b20b2e5c8a277ba520039d409699b9f0bfc625a2b6a1c4130a24188",
      "size_bytes": 625436,
      "source_family": "owner_or_tool_export"
    },
    {
      "absolute_path": "C:\\tmp\\gtos_otb\\NOFILLTICKRECOVERY\\exports\\multi_instrument\\GBPJPY_M15.csv",
      "catalog_row_id": "LCAT-000254",
      "sha256": "374062872c0948eda68618a3e0ebf8b4c2878f4f6f235e2fd49adce3878511dc",
      "size_bytes": 6172349,
      "source_family": "owner_or_tool_export"
    },
    {
      "absolute_path": "C:\\tmp\\gtos_otb\\NOFILLTICKRECOVERY\\exports\\multi_instrument\\GBPUSD_D1.csv",
      "catalog_row_id": "LCAT-000255",
      "sha256": "80308a3599b9c40e492f663e5b49557711c77b8839e25145fff5c35b94d27733",
      "size_bytes": 184106,
      "source_family": "owner_or_tool_export"
    },
    {
      "absolute_path": "C:\\tmp\\gtos_otb\\NOFILLTICKRECOVERY\\exports\\multi_instrument\\GBPUSD_H1.csv",
      "catalog_row_id": "LCAT-000256",
      "sha256": "d0c018b828a983719d877328fbe30b3ae14f58ae948f8a2a3a44ca38f014485f",
      "size_bytes": 1328773,
      "source_family": "owner_or_tool_export"
    },
    {
      "absolute_path": "C:\\tmp\\gtos_otb\\NOFILLTICKRECOVERY\\exports\\multi_instrument\\GBPUSD_H4.csv",
      "catalog_row_id": "LCAT-000257",
      "sha256": "e362e789825e39f675bb2828ea099f6c4e9df7bb73d5dc2ef4c8df1f104d9b62",
      "size_bytes": 667461,
      "source_family": "owner_or_tool_export"
    },
    {
      "absolute_path": "C:\\tmp\\gtos_otb\\NOFILLTICKRECOVERY\\exports\\multi_instrument\\GBPUSD_M15.csv",
      "catalog_row_id": "LCAT-000258",
      "sha256": "059edb9a1712b688802ef573c57c1940771b264adfe5e7f512869c3f16200f3c",
      "size_bytes": 3306698,
      "source_family": "owner_or_tool_export"
    },
    {
      "absolute_path": "C:\\tmp\\gtos_otb\\NOFILLTICKRECOVERY\\exports\\multi_instrument\\NZDUSD_D1.csv",
      "catalog_row_id": "LCAT-000259",
      "sha256": "4a17831108a199671b09dbc9418a1296142bc2d68be535bf4d2c97c823716857",
      "size_bytes": 166823,
      "source_family": "owner_or_tool_export"
    },
    {
      "absolute_path": "C:\\tmp\\gtos_otb\\NOFILLTICKRECOVERY\\exports\\multi_instrument\\NZDUSD_H1.csv",
      "catalog_row_id": "LCAT-000260",
      "sha256": "0243f9c466743606578e35d1003962ecd9b73435d371defe351ca4c6aafbfe5f",
      "size_bytes": 1228985,
      "source_family": "owner_or_tool_export"
    },
    {
      "absolute_path": "C:\\tmp\\gtos_otb\\NOFILLTICKRECOVERY\\exports\\multi_instrument\\NZDUSD_H4.csv",
      "catalog_row_id": "LCAT-000261",
      "sha256": "f5101e69b07c1ae1025de183fef658466fd85b24b3edf9d9620bd9727e74d535",
      "size_bytes": 618301,
      "source_family": "owner_or_tool_export"
    },
    {
      "absolute_path": "C:\\tmp\\gtos_otb\\NOFILLTICKRECOVERY\\exports\\multi_instrument\\NZDUSD_M15.csv",
      "catalog_row_id": "LCAT-000262",
      "sha256": "19b292d2e86bb3a7b1541f80fd4e5ef5bc02bcf21467598288868cdf47931413",
      "size_bytes": 6069379,
      "source_family": "owner_or_tool_export"
    },
    {
      "absolute_path": "C:\\tmp\\gtos_otb\\NOFILLTICKRECOVERY\\exports\\multi_instrument\\US30.cash_M15.csv",
      "catalog_row_id": "LCAT-000263",
      "sha256": "ecca14562033e51a6e64dc6d68f56a5e9e15a22bc9def3ad43c6c01ce92c4a89",
      "size_bytes": 6530280,
      "source_family": "owner_or_tool_export"
    },
    {
      "absolute_path": "C:\\tmp\\gtos_otb\\NOFILLTICKRECOVERY\\exports\\multi_instrument\\US30_M15.csv",
      "catalog_row_id": "LCAT-000264",
      "sha256": "ecca14562033e51a6e64dc6d68f56a5e9e15a22bc9def3ad43c6c01ce92c4a89",
      "size_bytes": 6530280,
      "source_family": "owner_or_tool_export"
    },
    {
      "absolute_path": "C:\\tmp\\gtos_otb\\NOFILLTICKRECOVERY\\exports\\multi_instrument\\US30_cash_D1.csv",
      "catalog_row_id": "LCAT-000265",
      "sha256": "8c89e15f36867167e5e0c83440702eb13faa991bd63ad55f6c70d3ac6a81eeb3",
      "size_bytes": 106191,
      "source_family": "owner_or_tool_export"
    },
    {
      "absolute_path": "C:\\tmp\\gtos_otb\\NOFILLTICKRECOVERY\\exports\\multi_instrument\\US30_cash_H1.csv",
      "catalog_row_id": "LCAT-000266",
      "sha256": "2775571ce3c1b89948134e54b9c54102e4ad5a1d9abc2232758af20da0a47fae",
      "size_bytes": 1324934,
      "source_family": "owner_or_tool_export"
    },
    {
      "absolute_path": "C:\\tmp\\gtos_otb\\NOFILLTICKRECOVERY\\exports\\multi_instrument\\US30_cash_H4.csv",
      "catalog_row_id": "LCAT-000267",
      "sha256": "587d1c66751f1ffc762dc8077837d41229488342da36516f4f81eb72287196e4",
      "size_bytes": 661261,
      "source_family": "owner_or_tool_export"
    },
    {
      "absolute_path": "C:\\tmp\\gtos_otb\\NOFILLTICKRECOVERY\\exports\\multi_instrument\\US30_cash_M15.csv",
      "catalog_row_id": "LCAT-000268",
      "sha256": "ecca14562033e51a6e64dc6d68f56a5e9e15a22bc9def3ad43c6c01ce92c4a89",
      "size_bytes": 6530280,
      "source_family": "owner_or_tool_export"
    },
    {
      "absolute_path": "C:\\tmp\\gtos_otb\\NOFILLTICKRECOVERY\\exports\\multi_instrument\\US500_cash_D1.csv",
      "catalog_row_id": "LCAT-000269",
      "sha256": "f6e8aeb3ee136c7d35ba4742b7777a2d0290264aeacd98334e93204bfff9d363",
      "size_bytes": 114166,
      "source_family": "owner_or_tool_export"
    },
    {
      "absolute_path": "C:\\tmp\\gtos_otb\\NOFILLTICKRECOVERY\\exports\\multi_instrument\\US500_cash_H1.csv",
      "catalog_row_id": "LCAT-000270",
      "sha256": "dd2c28db32c2b2a61d31682e05b2939c40dec7678b990b9dc78a11d7c50968fa",
      "size_bytes": 1224719,
      "source_family": "owner_or_tool_export"
    },
    {
      "absolute_path": "C:\\tmp\\gtos_otb\\NOFILLTICKRECOVERY\\exports\\multi_instrument\\US500_cash_H4.csv",
      "catalog_row_id": "LCAT-000271",
      "sha256": "da87e51c6c9b76efac0bfecf7e86f3b1ee740a5afd62e1077c6602565485b2a1",
      "size_bytes": 543481,
      "source_family": "owner_or_tool_export"
    },
    {
      "absolute_path": "C:\\tmp\\gtos_otb\\NOFILLTICKRECOVERY\\exports\\multi_instrument\\USDCAD_D1.csv",
      "catalog_row_id": "LCAT-000272",
      "sha256": "b7a2eaa167a61f2742327cf6ea6c9f58f030759952c20d4842c2d625d6252a06",
      "size_bytes": 182912,
      "source_family": "owner_or_tool_export"
    },
    {
      "absolute_path": "C:\\tmp\\gtos_otb\\NOFILLTICKRECOVERY\\exports\\multi_instrument\\USDCAD_H1.csv",
      "catalog_row_id": "LCAT-000273",
      "sha256": "13068f937ddd959639292d37ff976d931e4c10d5e3d4bf0bab9f147b6c85be2c",
      "size_bytes": 1340523,
      "source_family": "owner_or_tool_export"
    },
    {
      "absolute_path": "C:\\tmp\\gtos_otb\\NOFILLTICKRECOVERY\\exports\\multi_instrument\\USDCAD_H4.csv",
      "catalog_row_id": "LCAT-000274",
      "sha256": "3100d7afa50238006cb1d54ec6dc9d61d1e032db51b426b7b30ba3316dd81b38",
      "size_bytes": 672627,
      "source_family": "owner_or_tool_export"
    },
    {
      "absolute_path": "C:\\tmp\\gtos_otb\\NOFILLTICKRECOVERY\\exports\\multi_instrument\\USDJPY_D1.csv",
      "catalog_row_id": "LCAT-000275",
      "sha256": "0922d8d5954d82bd7be87b3ebfa61d0a7012f074e9a033de964cef31805fac08",
      "size_bytes": 167585,
      "source_family": "owner_or_tool_export"
    },
    {
      "absolute_path": "C:\\tmp\\gtos_otb\\NOFILLTICKRECOVERY\\exports\\multi_instrument\\USDJPY_H1.csv",
      "catalog_row_id": "LCAT-000276",
      "sha256": "54fd259115aac4767afb547c89a16d1575bdd9be9006a6b6f8140ff14a39029c",
      "size_bytes": 1231694,
      "source_family": "owner_or_tool_export"
    },
    {
      "absolute_path": "C:\\tmp\\gtos_otb\\NOFILLTICKRECOVERY\\exports\\multi_instrument\\USDJPY_H4.csv",
      "catalog_row_id": "LCAT-000277",
      "sha256": "3dd61ac124e62b281bb28014f185a6b71c7b705c5a53c66dcf60c49e9ae34190",
      "size_bytes": 621084,
      "source_family": "owner_or_tool_export"
    },
    {
      "absolute_path": "C:\\tmp\\gtos_otb\\NOFILLTICKRECOVERY\\exports\\multi_instrument\\USDJPY_M15.csv",
      "catalog_row_id": "LCAT-000278",
      "sha256": "769e1df3b978dccf21e68d61544d5d763a5682e839101ccc1ab4f7fd97390f5f",
      "size_bytes": 3050977,
      "source_family": "owner_or_tool_export"
    },
    {
      "absolute_path": "C:\\tmp\\gtos_otb\\NOFILLTICKRECOVERY\\exports\\multi_instrument\\USOIL_cash_D1.csv",
      "catalog_row_id": "LCAT-000279",
      "sha256": "b0824d47b66a06703470150e8289e47d06cfba40a8a30fceb6bacc6fa050dc39",
      "size_bytes": 68835,
      "source_family": "owner_or_tool_export"
    },
    {
      "absolute_path": "C:\\tmp\\gtos_otb\\NOFILLTICKRECOVERY\\exports\\multi_instrument\\USOIL_cash_H1.csv",
      "catalog_row_id": "LCAT-000280",
      "sha256": "66976e3b24cd164b1a0978419551b95bca927265d61679da503a202263900e57",
      "size_bytes": 1163798,
      "source_family": "owner_or_tool_export"
    },
    {
      "absolute_path": "C:\\tmp\\gtos_otb\\NOFILLTICKRECOVERY\\exports\\multi_instrument\\USOIL_cash_H4.csv",
      "catalog_row_id": "LCAT-000281",
      "sha256": "c57cca56980a60f8e00b5ca3ae144d16a207b67d5922db12ea3b9fb65ea69dc4",
      "size_bytes": 479258,
      "source_family": "owner_or_tool_export"
    },
    {
      "absolute_path": "C:\\tmp\\gtos_otb\\NOFILLTICKRECOVERY\\exports\\multi_instrument\\XAGUSD_D1.csv",
      "catalog_row_id": "LCAT-000282",
      "sha256": "b5d84011d7908f563b877d0573954feb397c570a25f027e8c3e882e7d5d30562",
      "size_bytes": 158187,
      "source_family": "owner_or_tool_export"
    },
    {
      "absolute_path": "C:\\tmp\\gtos_otb\\NOFILLTICKRECOVERY\\exports\\multi_instrument\\XAGUSD_H1.csv",
      "catalog_row_id": "LCAT-000283",
      "sha256": "1cfbb6935c68a977af10dbec2afd519c4eece3aa2a87ced479a32828d23ceb19",
      "size_bytes": 1170507,
      "source_family": "owner_or_tool_export"
    },
    {
      "absolute_path": "C:\\tmp\\gtos_otb\\NOFILLTICKRECOVERY\\exports\\multi_instrument\\XAGUSD_H4.csv",
      "catalog_row_id": "LCAT-000284",
      "sha256": "cb122c9cdf9f016b03fff30f4700044fa1d2081e54d553d1509720ba755dbbe9",
      "size_bytes": 588449,
      "source_family": "owner_or_tool_export"
    },
    {
      "absolute_path": "C:\\tmp\\gtos_otb\\NOFILLTICKRECOVERY\\exports\\multi_instrument\\XAGUSD_M15.csv",
      "catalog_row_id": "LCAT-000285",
      "sha256": "da8c548412bee2a02a5afa1421661b1391cd2df089de2242a36259a24401c7e8",
      "size_bytes": 2902491,
      "source_family": "owner_or_tool_export"
    },
    {
      "absolute_path": "C:\\tmp\\gtos_otb\\NOFILLTICKRECOVERY\\exports\\multi_instrument\\XAUUSD_D1.csv",
      "catalog_row_id": "LCAT-000286",
      "sha256": "2e9781367fef55fda36ad26fe85284132e4d948e4a909e709c14238fb33d0a35",
      "size_bytes": 170107,
      "source_family": "owner_or_tool_export"
    },
    {
      "absolute_path": "C:\\tmp\\gtos_otb\\NOFILLTICKRECOVERY\\exports\\multi_instrument\\XAUUSD_H1.csv",
      "catalog_row_id": "LCAT-000287",
      "sha256": "6066607243a4cec4e9cf6fa9984dccf1db5fb49aa690eec380ba3b6491817a57",
      "size_bytes": 1245978,
      "source_family": "owner_or_tool_export"
    },
    {
      "absolute_path": "C:\\tmp\\gtos_otb\\NOFILLTICKRECOVERY\\exports\\multi_instrument\\XAUUSD_H4.csv",
      "catalog_row_id": "LCAT-000288",
      "sha256": "1350221fa694ed8c393e6e1feb3ba00e1ce178564c02a5cddd7a6d836832913d",
      "size_bytes": 627906,
      "source_family": "owner_or_tool_export"
    },
    {
      "absolute_path": "C:\\tmp\\gtos_otb\\NOFILLTICKRECOVERY\\exports\\multi_instrument\\XAUUSD_M15.csv",
      "catalog_row_id": "LCAT-000289",
      "sha256": "64e39bba7b6c6c4faa635e3089a12ca883b0f9006a2d8369c7028184ba6305d6",
      "size_bytes": 3115490,
      "source_family": "owner_or_tool_export"
    },
    {
      "absolute_path": "C:\\tmp\\gtos_otb\\NOFILLTICKRECOVERY\\exports\\multi_instrument\\align_injection_design.md",
      "catalog_row_id": "LCAT-000290",
      "sha256": "9bebfa11eb17fe0fa0e8df2480f0ce65c5e284e3a2659600b23191a0ea1e99ea",
      "size_bytes": 1280,
      "source_family": "owner_or_tool_export"
    },
    {
      "absolute_path": "C:\\tmp\\gtos_otb\\NOFILLTICKRECOVERY\\exports\\multi_instrument\\bearish_gold_dates.txt",
      "catalog_row_id": "LCAT-000291",
      "sha256": "390f1d9b5d7b56e958553c815b97a3c73ac6053ba3e3539b5653cf9b66123008",
      "size_bytes": 600,
      "source_family": "owner_or_tool_export"
    },
    {
      "absolute_path": "C:\\tmp\\gtos_otb\\NOFILLTICKRECOVERY\\exports\\multi_instrument\\correlation_sizing_design.md",
      "catalog_row_id": "LCAT-000292",
      "sha256": "4d79b7bd4ebbef5022152506111f9e9413a6846e82078e48209735c010ee5d17",
      "size_bytes": 1662,
      "source_family": "owner_or_tool_export"
    },
    {
      "absolute_path": "C:\\tmp\\gtos_otb\\NOFILLTICKRECOVERY\\exports\\multi_instrument\\extraction_summary.json",
      "catalog_row_id": "LCAT-000293",
      "sha256": "9e62e3f9cc48230b8b45b0b3476131114ce72cf96afea5ed1bf3db418889fbaf",
      "size_bytes": 10232,
      "source_family": "owner_or_tool_export"
    },
    {
      "absolute_path": "C:\\tmp\\gtos_otb\\NOFILLTICKRECOVERY\\exports\\multi_instrument\\screening_results\\AUDUSD_detail.json",
      "catalog_row_id": "LCAT-000294",
      "sha256": "78dd993f6b8ae8e2994cc84002cabe5b3d2d0201a4cae03b15595a873d7feead",
      "size_bytes": 10347,
      "source_family": "owner_or_tool_export"
    },
    {
      "absolute_path": "C:\\tmp\\gtos_otb\\NOFILLTICKRECOVERY\\exports\\multi_instrument\\screening_results\\EURJPY_detail.json",
      "catalog_row_id": "LCAT-000295",
      "sha256": "c26528861d70c06cb44ddb877d467daf1712053c15808eed960770734dd3666b",
      "size_bytes": 10364,
      "source_family": "owner_or_tool_export"
    },
    {
      "absolute_path": "C:\\tmp\\gtos_otb\\NOFILLTICKRECOVERY\\exports\\multi_instrument\\screening_results\\EURUSD_detail.json",
      "catalog_row_id": "LCAT-000296",
      "sha256": "6e5749a347dfbdfa6bc1aa3cc5f54a32797fa951eea433bc0a676ba0a448d2b2",
      "size_bytes": 10351,
      "source_family": "owner_or_tool_export"
    },
    {
      "absolute_path": "C:\\tmp\\gtos_otb\\NOFILLTICKRECOVERY\\exports\\multi_instrument\\screening_results\\GBPJPY_detail.json",
      "catalog_row_id": "LCAT-000297",
      "sha256": "5776f278666344581cbed01c2cae41143c570490dc1bb64ae4d5b05ac37a194f",
      "size_bytes": 10366,
      "source_family": "owner_or_tool_export"
    },
    {
      "absolute_path": "C:\\tmp\\gtos_otb\\NOFILLTICKRECOVERY\\exports\\multi_instrument\\screening_results\\GBPUSD_detail.json",
      "catalog_row_id": "LCAT-000298",
      "sha256": "ca953aeb16fbd4b0f6e15a051c7ac6e7eaf3d215b68a9a8d90246cb035ad6486",
      "size_bytes": 10356,
      "source_family": "owner_or_tool_export"
    },
    {
      "absolute_path": "C:\\tmp\\gtos_otb\\NOFILLTICKRECOVERY\\exports\\multi_instrument\\screening_results\\NZDUSD_detail.json",
      "catalog_row_id": "LCAT-000299",
      "sha256": "191072665007ac80849fa6a61b120a53d306b0c3e2efac2919a2dd34f78f431f",
      "size_bytes": 10359,
      "source_family": "owner_or_tool_export"
    },
    {
      "absolute_path": "C:\\tmp\\gtos_otb\\NOFILLTICKRECOVERY\\exports\\multi_instrument\\screening_results\\US30_cash_detail.json",
      "catalog_row_id": "LCAT-000300",
      "sha256": "4160076bc62ba6d540e574b463d81d34cca2f567168fd3b9f6a680c044a348d7",
      "size_bytes": 10374,
      "source_family": "owner_or_tool_export"
    },
    {
      "absolute_path": "C:\\tmp\\gtos_otb\\NOFILLTICKRECOVERY\\exports\\multi_instrument\\screening_results\\US500_cash_detail.json",
      "catalog_row_id": "LCAT-000301",
      "sha256": "67df0799eeea708d93d10ea4b0d10a3882a8a91e46d25b9b88ea878da1a1f1d2",
      "size_bytes": 10380,
      "source_family": "owner_or_tool_export"
    },
    {
      "absolute_path": "C:\\tmp\\gtos_otb\\NOFILLTICKRECOVERY\\exports\\multi_instrument\\screening_results\\USDCAD_detail.json",
      "catalog_row_id": "LCAT-000302",
      "sha256": "d0814ae2ebef1a1f576d740720f80b74d53bcaa96ec3486c28b259d2ebdb0784",
      "size_bytes": 10367,
      "source_family": "owner_or_tool_export"
    },
    {
      "absolute_path": "C:\\tmp\\gtos_otb\\NOFILLTICKRECOVERY\\exports\\multi_instrument\\screening_results\\USDJPY_detail.json",
      "catalog_row_id": "LCAT-000303",
      "sha256": "157d4838f43b3bb2e2e5b600d7af521e7f7d08001f447221b822c2ee0a269c7b",
      "size_bytes": 10369,
      "source_family": "owner_or_tool_export"
    },
    {
      "absolute_path": "C:\\tmp\\gtos_otb\\NOFILLTICKRECOVERY\\exports\\multi_instrument\\screening_results\\USOIL_cash_detail.json",
      "catalog_row_id": "LCAT-000304",
      "sha256": "5ec8d82bcf4533bef84a4d8faa1708f06d8cb2983c4b6a1febf6b3212e43f9f0",
      "size_bytes": 10367,
      "source_family": "owner_or_tool_export"
    },
    {
      "absolute_path": "C:\\tmp\\gtos_otb\\NOFILLTICKRECOVERY\\exports\\multi_instrument\\screening_results\\XAGUSD_detail.json",
      "catalog_row_id": "LCAT-000305",
      "sha256": "5e889f82c2231e33711237bff63c07a2a338a74ef4e93bcc7682e005e17bf29b",
      "size_bytes": 10351,
      "source_family": "owner_or_tool_export"
    },
    {
      "absolute_path": "C:\\tmp\\gtos_otb\\NOFILLTICKRECOVERY\\data\\external\\validation\\expanded_oos_full_unblocking\\sierra_6b_to_gbpusd_pilot_20260504\\raw_ohlc_prequential_events_20260503T205250Z.jsonl",
      "catalog_row_id": "LCAT-000306",
      "sha256": "3bc61bef9c6ecfd6df9f1696cfcdd2718371803120da966fa0c592b4b37fc634",
      "size_bytes": 91368,
      "source_family": "local_external_or_vendor_cache"
    },
    {
      "absolute_path": "C:\\tmp\\gtos_otb\\NOFILLTICKRECOVERY\\data\\external\\validation\\expanded_oos_full_unblocking\\sierra_6b_to_gbpusd_pilot_20260504\\raw_ohlc_prequential_replay_20260503T205251Z.json",
      "catalog_row_id": "LCAT-000307",
      "sha256": "00ab983d39b0adead0c0ffe19c43860008d3467009a8973ddc49329ab886acab",
      "size_bytes": 28052,
      "source_family": "local_external_or_vendor_cache"
    },
    {
      "absolute_path": "C:\\tmp\\gtos_otb\\NOFILLTICKRECOVERY\\data\\external\\validation\\expanded_oos_full_unblocking\\sierra_6j_to_usdjpy_pilot_20260504\\raw_ohlc_prequential_events_20260503T205250Z.jsonl",
      "catalog_row_id": "LCAT-000308",
      "sha256": "57f61464fb7d8aed2b43e26513b93a18aee517c0052f24fdec7ab07eaddc4c2e",
      "size_bytes": 97535,
      "source_family": "local_external_or_vendor_cache"
    },
    {
      "absolute_path": "C:\\tmp\\gtos_otb\\NOFILLTICKRECOVERY\\data\\external\\validation\\expanded_oos_full_unblocking\\sierra_6j_to_usdjpy_pilot_20260504\\raw_ohlc_prequential_replay_20260503T205251Z.json",
      "catalog_row_id": "LCAT-000309",
      "sha256": "ad5cc93186be2c239f1dc40a81434707ac0abb7b61e791fb9ea5ed06ce16e7fd",
      "size_bytes": 28042,
      "source_family": "local_external_or_vendor_cache"
    },
    {
      "absolute_path": "C:\\tmp\\gtos_otb\\NOFILLTICKRECOVERY\\data\\external\\validation\\expanded_oos_full_unblocking\\sierra_nq_to_nas100_pilot_20260504\\raw_ohlc_prequential_events_20260503T202913Z.jsonl",
      "catalog_row_id": "LCAT-000310",
      "sha256": "c59cb178376bbb3e24d5587c47f2d98b33d8db014203fd76b5bbce74f2d04513",
      "size_bytes": 77834,
      "source_family": "local_external_or_vendor_cache"
    },
    {
      "absolute_path": "C:\\tmp\\gtos_otb\\NOFILLTICKRECOVERY\\data\\external\\validation\\expanded_oos_full_unblocking\\sierra_nq_to_nas100_pilot_20260504\\raw_ohlc_prequential_replay_20260503T202915Z.json",
      "catalog_row_id": "LCAT-000311",
      "sha256": "66212e3b5c3ba7c8bb5a0e027df0e55e3cfba87e039c45583542d8f1a87d3d57",
      "size_bytes": 28101,
      "source_family": "local_external_or_vendor_cache"
    },
    {
      "absolute_path": "C:\\tmp\\gtos_otb\\NOFILLTICKRECOVERY\\data\\external\\validation\\expanded_oos_full_unblocking\\sierra_si_to_xagusd_pilot_20260504\\raw_ohlc_prequential_events_20260503T205250Z.jsonl",
      "catalog_row_id": "LCAT-000312",
      "sha256": "be053ea527394169cfcecc2f9bbc3f5712ffc11f474df9c89c5b4311fc1beefa",
      "size_bytes": 73638,
      "source_family": "local_external_or_vendor_cache"
    },
    {
      "absolute_path": "C:\\tmp\\gtos_otb\\NOFILLTICKRECOVERY\\data\\external\\validation\\expanded_oos_full_unblocking\\sierra_si_to_xagusd_pilot_20260504\\raw_ohlc_prequential_replay_20260503T205252Z.json",
      "catalog_row_id": "LCAT-000313",
      "sha256": "51e14f26e7682d87d2a4ecfb69ec4ea9c868a56d97f1e44c26a893c0302227d9",
      "size_bytes": 28733,
      "source_family": "local_external_or_vendor_cache"
    },
    {
      "absolute_path": "C:\\tmp\\gtos_otb\\NOFILLTICKRECOVERY\\data\\external\\validation\\expanded_oos_full_unblocking\\sierra_si_xagusd_v2_mtf_pilot_20260504\\path_scaling_v2_structural_levels\\raw_ohlc_path_scaling_v2_structural_levels_20260503T205339Z.json",
      "catalog_row_id": "LCAT-000314",
      "sha256": "7e5582d9c7e1dd7691f6d5f6c544dcc07c451992c3fdacf974da6628eeeb4a65",
      "size_bytes": 104394,
      "source_family": "local_external_or_vendor_cache"
    },
    {
      "absolute_path": "C:\\tmp\\gtos_otb\\NOFILLTICKRECOVERY\\data\\external\\validation\\expanded_oos_full_unblocking\\sierra_si_xagusd_v2_mtf_pilot_20260504\\path_scaling_v2_structural_levels\\raw_ohlc_path_scaling_v2_structural_levels_events_20260503T205337Z.jsonl",
      "catalog_row_id": "LCAT-000315",
      "sha256": "438074c74d48ee7b229f5811d279d9be4957b34817062df14ff60e1168870197",
      "size_bytes": 63942,
      "source_family": "local_external_or_vendor_cache"
    },
    {
      "absolute_path": "C:\\tmp\\gtos_otb\\NOFILLTICKRECOVERY\\data\\external\\validation\\expanded_oos_full_unblocking\\sierra_xauusd_scid_to_xauusd_pilot_20260504\\raw_ohlc_prequential_events_20260503T204511Z.jsonl",
      "catalog_row_id": "LCAT-000316",
      "sha256": "ccf8f4633c04aeaa56f2cc85d780f7a4f765f36c7529cd435784e9860d55bada",
      "size_bytes": 77104,
      "source_family": "local_external_or_vendor_cache"
    },
    {
      "absolute_path": "C:\\tmp\\gtos_otb\\NOFILLTICKRECOVERY\\data\\external\\validation\\expanded_oos_full_unblocking\\sierra_xauusd_scid_to_xauusd_pilot_20260504\\raw_ohlc_prequential_replay_20260503T204512Z.json",
      "catalog_row_id": "LCAT-000317",
      "sha256": "2f89b9b22c75d349e79c3bf34545cbbc5144454c8de5ddd5d61f0d88f2365c8b",
      "size_bytes": 28824,
      "source_family": "local_external_or_vendor_cache"
    },
    {
      "absolute_path": "C:\\tmp\\gtos_otb\\NOFILLTICKRECOVERY\\data\\external\\validation\\expanded_oos_full_unblocking\\sierra_xauusd_scid_v2_mtf_pilot_20260504\\path_scaling_v2_structural_levels\\raw_ohlc_path_scaling_v2_structural_levels_20260503T204612Z.json",
      "catalog_row_id": "LCAT-000318",
      "sha256": "367fa351faf46cf7e951e2adcc1aaf55eff7f1c158b6a22a1cfe28914efe7ddd",
      "size_bytes": 113667,
      "source_family": "local_external_or_vendor_cache"
    },
    {
      "absolute_path": "C:\\tmp\\gtos_otb\\NOFILLTICKRECOVERY\\data\\external\\validation\\expanded_oos_full_unblocking\\sierra_xauusd_scid_v2_mtf_pilot_20260504\\path_scaling_v2_structural_levels\\raw_ohlc_path_scaling_v2_structural_levels_events_20260503T204606Z.jsonl",
      "catalog_row_id": "LCAT-000319",
      "sha256": "9777f339f94c713329a89364c6584c7ea7a2acddf5c6cb7b1812c893d984a5c6",
      "size_bytes": 336479,
      "source_family": "local_external_or_vendor_cache"
    },
    {
      "absolute_path": "C:\\tmp\\gtos_otb\\NOFILLTICKRECOVERY\\data\\external\\validation\\expanded_oos_full_unblocking\\sierra_ym_to_us30_cash_pilot_20260504\\raw_ohlc_prequential_events_20260503T204727Z.jsonl",
      "catalog_row_id": "LCAT-000320",
      "sha256": "d5ee79d060f0acd9a52850acbef9cdb8f2196e6caa2a427ea9dce406cc71d570",
      "size_bytes": 51679,
      "source_family": "local_external_or_vendor_cache"
    },
    {
      "absolute_path": "C:\\tmp\\gtos_otb\\NOFILLTICKRECOVERY\\data\\external\\validation\\expanded_oos_full_unblocking\\sierra_ym_to_us30_cash_pilot_20260504\\raw_ohlc_prequential_replay_20260503T204728Z.json",
      "catalog_row_id": "LCAT-000321",
      "sha256": "09ac3561215d4747c00f0a74a8afecb965608f4ba9f5dde2d089d82fe2b1155a",
      "size_bytes": 28788,
      "source_family": "local_external_or_vendor_cache"
    },
    {
      "absolute_path": "C:\\tmp\\gtos_otb\\NOFILLTICKRECOVERY\\data\\external\\validation\\expanded_oos_full_unblocking\\sierra_ym_us30_cash_v2_mtf_pilot_20260504\\path_scaling_v2_structural_levels\\raw_ohlc_path_scaling_v2_structural_levels_20260503T204801Z.json",
      "catalog_row_id": "LCAT-000322",
      "sha256": "a7d5b06a8937138a04f19716a130b38d94e3008d1a311346411594a4befba252",
      "size_bytes": 104112,
      "source_family": "local_external_or_vendor_cache"
    },
    {
      "absolute_path": "C:\\tmp\\gtos_otb\\NOFILLTICKRECOVERY\\data\\external\\validation\\expanded_oos_full_unblocking\\sierra_ym_us30_cash_v2_mtf_pilot_20260504\\path_scaling_v2_structural_levels\\raw_ohlc_path_scaling_v2_structural_levels_events_20260503T204759Z.jsonl",
      "catalog_row_id": "LCAT-000323",
      "sha256": "ea4c4da537282206f0764344af809844cb97e3425f398752536b4918b98bf5a3",
      "size_bytes": 64470,
      "source_family": "local_external_or_vendor_cache"
    },
    {
      "absolute_path": "C:\\tmp\\gtos_otb\\NOFILLTICKRECOVERY\\research\\science_program_2026_05\\06_outcome_testing\\OTG0_COMPLETION_AUDIT_2026-05-07.json",
      "catalog_row_id": "LCAT-000324",
      "sha256": "3baecb56c4de5049576554150f2c0ffda0c7e15dd7127a46632c8e625f6fcabc",
      "size_bytes": 12766,
      "source_family": "research_route_artifact"
    },
    {
      "absolute_path": "C:\\tmp\\gtos_otb\\NOFILLTICKRECOVERY\\research\\science_program_2026_05\\06_outcome_testing\\OTG0_COMPLETION_AUDIT_2026-05-07.md",
      "catalog_row_id": "LCAT-000325",
      "sha256": "5f043e865617dc0abc9f6658164272420c7972c9b30f2e4334d5a3daaa5a990e",
      "size_bytes": 5845,
      "source_family": "research_route_artifact"
    },
    {
      "absolute_path": "C:\\tmp\\gtos_otb\\NOFILLTICKRECOVERY\\research\\science_program_2026_05\\06_outcome_testing\\OTG0_FOLLOWUP_GOAL_PROMPTS_2026-05-07.json",
      "catalog_row_id": "LCAT-000326",
      "sha256": "fd11c8f0c69f12c8dafcda5f63dc901c4e6236fb4ed61acce70204ff49790bde",
      "size_bytes": 9085,
      "source_family": "research_route_artifact"
    },
    {
      "absolute_path": "C:\\tmp\\gtos_otb\\NOFILLTICKRECOVERY\\research\\science_program_2026_05\\06_outcome_testing\\OTG0_FOLLOWUP_GOAL_PROMPTS_2026-05-07.md",
      "catalog_row_id": "LCAT-000327",
      "sha256": "de587fc14052733557d222ef1dc5fc0730da689c761a411ba938494a2d777bfb",
      "size_bytes": 4387,
      "source_family": "research_route_artifact"
    },
    {
      "absolute_path": "C:\\tmp\\gtos_otb\\NOFILLTICKRECOVERY\\research\\science_program_2026_05\\06_outcome_testing\\OTG0_FROZEN_COHORT_PACKET_MANIFEST_2026-05-07.json",
      "catalog_row_id": "LCAT-000328",
      "sha256": "d66c8aab004283afe4291dd5f9194797d689466301f67708ecd30ed7d2283fa7",
      "size_bytes": 545223,
      "source_family": "research_route_artifact"
    },
    {
      "absolute_path": "C:\\tmp\\gtos_otb\\NOFILLTICKRECOVERY\\research\\science_program_2026_05\\06_outcome_testing\\OTG0_FROZEN_COHORT_PACKET_MANIFEST_2026-05-07.md",
      "catalog_row_id": "LCAT-000329",
      "sha256": "1fd18655acc0b8bede984d2e7f71b0bec5c312440c0f396cbd1faa897fb40a4b",
      "size_bytes": 12181,
      "source_family": "research_route_artifact"
    },
    {
      "absolute_path": "C:\\tmp\\gtos_otb\\NOFILLTICKRECOVERY\\research\\science_program_2026_05\\06_outcome_testing\\OTG0_OUTCOME_TESTING_CONTROL_RULES_2026-05-07.json",
      "catalog_row_id": "LCAT-000330",
      "sha256": "14c595be104f632b9c0c659a5c2c2d85e50057862324bc2c6f4e317d95d6ea39",
      "size_bytes": 14884,
      "source_family": "research_route_artifact"
    },
    {
      "absolute_path": "C:\\tmp\\gtos_otb\\NOFILLTICKRECOVERY\\research\\science_program_2026_05\\06_outcome_testing\\OTG0_OUTCOME_TESTING_CONTROL_RULES_2026-05-07.md",
      "catalog_row_id": "LCAT-000331",
      "sha256": "64019a2f70f8c2b165ba5fffe0b0e22186f3b9a4b47ccc936626af50a251c084",
      "size_bytes": 5908,
      "source_family": "research_route_artifact"
    },
    {
      "absolute_path": "C:\\tmp\\gtos_otb\\NOFILLTICKRECOVERY\\research\\science_program_2026_05\\06_outcome_testing\\OTG0_PREREG_CLASSIFICATION_LEDGER_2026-05-07.json",
      "catalog_row_id": "LCAT-000332",
      "sha256": "20b1702ebe354e40450ec4a0b86c49a84dd7d2777d638281f6d1d6cb09cffe85",
      "size_bytes": 67209,
      "source_family": "research_route_artifact"
    },
    {
      "absolute_path": "C:\\tmp\\gtos_otb\\NOFILLTICKRECOVERY\\research\\science_program_2026_05\\06_outcome_testing\\OTG0_PREREG_CLASSIFICATION_LEDGER_2026-05-07.md",
      "catalog_row_id": "LCAT-000333",
      "sha256": "c64dbf9fda1c9661b844b4cd4f841b91320cb4ae23f7453f1b183e22bfce5d28",
      "size_bytes": 9075,
      "source_family": "research_route_artifact"
    },
    {
      "absolute_path": "C:\\tmp\\gtos_otb\\NOFILLTICKRECOVERY\\research\\science_program_2026_05\\06_outcome_testing\\OTL1_LIFECYCLE_NO_FILL_PACKET_AUDIT_2026-05-07.json",
      "catalog_row_id": "LCAT-000334",
      "sha256": "c99574f6a231955b6ad707168b8bfa5ee813af0738ab2841ba867ffe5b96351a",
      "size_bytes": 13331,
      "source_family": "research_route_artifact"
    },
    {
      "absolute_path": "C:\\tmp\\gtos_otb\\NOFILLTICKRECOVERY\\research\\science_program_2026_05\\06_outcome_testing\\OTL1_LIFECYCLE_NO_FILL_PACKET_AUDIT_2026-05-07.md",
      "catalog_row_id": "LCAT-000335",
      "sha256": "81f53c5594deb5fbb1cbdede29c4726687a97d89dc21d68310298b4ff9c98549",
      "size_bytes": 17528,
      "source_family": "research_route_artifact"
    },
    {
      "absolute_path": "C:\\tmp\\gtos_otb\\NOFILLTICKRECOVERY\\research\\science_program_2026_05\\06_outcome_testing\\README_2026-05-07.md",
      "catalog_row_id": "LCAT-000336",
      "sha256": "9248a2c58778eb053179a989dbfa15a7f46aaf1f0782733fd2c6228462aff80a",
      "size_bytes": 699,
      "source_family": "research_route_artifact"
    },
    {
      "absolute_path": "C:\\tmp\\gtos_otb\\NOFILLTICKRECOVERY\\research\\science_program_2026_05\\06_outcome_testing\\build_otg0_control_artifacts_2026_05_07.py",
      "catalog_row_id": "LCAT-000337",
      "sha256": "8f62bfb6b22526f8b7ca91b36c7300756a646e7a1bdf2ddab2a80d6d18ca41e4",
      "size_bytes": 54831,
      "source_family": "research_route_artifact"
    },
    {
      "absolute_path": "C:\\tmp\\gtos_otb\\NOFILLTICKRECOVERY\\research\\science_program_2026_05\\06_outcome_testing\\cnr061_geometry_horizon_sidecar\\CNR061_CONTEXT_CONTINUITY_AND_INSTRUCTION_COVERAGE_2026-05-08.json",
      "catalog_row_id": "LCAT-000338",
      "sha256": "78c5ef23c994403239477b37f19091ca0ba38ffee1c44f2eb99c8142860250c6",
      "size_bytes": 3284,
      "source_family": "research_route_artifact"
    },
    {
      "absolute_path": "C:\\tmp\\gtos_otb\\NOFILLTICKRECOVERY\\research\\science_program_2026_05\\06_outcome_testing\\cnr061_geometry_horizon_sidecar\\CNR061_CONTEXT_CONTINUITY_AND_INSTRUCTION_COVERAGE_2026-05-08.md",
      "catalog_row_id": "LCAT-000339",
      "sha256": "1ac22939335a38a0c1cb8ef0074d5cb9b13e6b4f6f406ef38d42609f9f1ea10f",
      "size_bytes": 3492,
      "source_family": "research_route_artifact"
    },
    {
      "absolute_path": "C:\\tmp\\gtos_otb\\NOFILLTICKRECOVERY\\research\\science_program_2026_05\\06_outcome_testing\\cnr061_geometry_horizon_sidecar\\CNR061_EXACT_BLOCKER_OR_IMPOSSIBILITY_LEDGER_2026-05-08.json",
      "catalog_row_id": "LCAT-000340",
      "sha256": "e5c4e4985f4f26786a477cc95e607d082f037c743fda866d8337ca8a53ed3ce2",
      "size_bytes": 161191,
      "source_family": "research_route_artifact"
    },
    {
      "absolute_path": "C:\\tmp\\gtos_otb\\NOFILLTICKRECOVERY\\research\\science_program_2026_05\\06_outcome_testing\\cnr061_geometry_horizon_sidecar\\CNR061_EXACT_BLOCKER_OR_IMPOSSIBILITY_LEDGER_2026-05-08.md",
      "catalog_row_id": "LCAT-000341",
      "sha256": "c4f8fb8a6f760c79675e603a48566d29c7af61c88356962249243a7cab6fb0dc",
      "size_bytes": 161566,
      "source_family": "research_route_artifact"
    },
    {
      "absolute_path": "C:\\tmp\\gtos_otb\\NOFILLTICKRECOVERY\\research\\science_program_2026_05\\06_outcome_testing\\cnr061_geometry_horizon_sidecar\\CNR061_G12_REAUDIT_READY_PROPOSAL_2026-05-08.json",
      "catalog_row_id": "LCAT-000342",
      "sha256": "31e3a3e008d17a52d2b1545c50f0c8739dab0b1701af90eb3e2ee2fc94223a1a",
      "size_bytes": 1868,
      "source_family": "research_route_artifact"
    },
    {
      "absolute_path": "C:\\tmp\\gtos_otb\\NOFILLTICKRECOVERY\\research\\science_program_2026_05\\06_outcome_testing\\cnr061_geometry_horizon_sidecar\\CNR061_G12_REAUDIT_READY_PROPOSAL_2026-05-08.md",
      "catalog_row_id": "LCAT-000343",
      "sha256": "bb148f1a3730b789feb80553a43990faef239a83b0469b8bf554dabd80a3d963",
      "size_bytes": 2205,
      "source_family": "research_route_artifact"
    },
    {
      "absolute_path": "C:\\tmp\\gtos_otb\\NOFILLTICKRECOVERY\\research\\science_program_2026_05\\06_outcome_testing\\cnr061_geometry_horizon_sidecar\\CNR061_GEOMETRY_HORIZON_SIDECAR_COMPLETION_AUDIT_2026-05-08.json",
      "catalog_row_id": "LCAT-000344",
      "sha256": "36c171012876fd3e708c8791f0092787a4f15c5c43f43bfd7a92b8c4868882b9",
      "size_bytes": 5977,
      "source_family": "research_route_artifact"
    },
    {
      "absolute_path": "C:\\tmp\\gtos_otb\\NOFILLTICKRECOVERY\\research\\science_program_2026_05\\06_outcome_testing\\cnr061_geometry_horizon_sidecar\\CNR061_GEOMETRY_HORIZON_SIDECAR_COMPLETION_AUDIT_2026-05-08.md",
      "catalog_row_id": "LCAT-000345",
      "sha256": "e20efbe40849bbd4274d83096cc1e6f399bd49a6fef8e4d0dc3574ca3574c396",
      "size_bytes": 6318,
      "source_family": "research_route_artifact"
    },
    {
      "absolute_path": "C:\\tmp\\gtos_otb\\NOFILLTICKRECOVERY\\research\\science_program_2026_05\\06_outcome_testing\\cnr061_geometry_horizon_sidecar\\CNR061_GEOMETRY_HORIZON_SIDECAR_GOAL_PROMPT_2026-05-08.md",
      "catalog_row_id": "LCAT-000346",
      "sha256": "92e7d73b7d050d8c7ebef7815685f97c0381d2080d8c6fa964fbad02a39c52d3",
      "size_bytes": 9846,
      "source_family": "research_route_artifact"
    },
    {
      "absolute_path": "C:\\tmp\\gtos_otb\\NOFILLTICKRECOVERY\\research\\science_program_2026_05\\06_outcome_testing\\cnr061_geometry_horizon_sidecar\\CNR061_GEOMETRY_HORIZON_SIDECAR_PACKET_2026-05-08.json",
      "catalog_row_id": "LCAT-000347",
      "sha256": "ac3b3765ed605957a54d7d06f079a076d9d7c8b04a14e44f1c9f5e92f86fd2b6",
      "size_bytes": 67952,
      "source_family": "research_route_artifact"
    },
    {
      "absolute_path": "C:\\tmp\\gtos_otb\\NOFILLTICKRECOVERY\\research\\science_program_2026_05\\06_outcome_testing\\cnr061_geometry_horizon_sidecar\\CNR061_GEOMETRY_HORIZON_SIDECAR_PACKET_2026-05-08.jsonl",
      "catalog_row_id": "LCAT-000348",
      "sha256": "1c522252249cb6cf045ac83f5a3b4251615a10d538d88965066fa7c9b289803c",
      "size_bytes": 56542,
      "source_family": "research_route_artifact"
    },
    {
      "absolute_path": "C:\\tmp\\gtos_otb\\NOFILLTICKRECOVERY\\research\\science_program_2026_05\\06_outcome_testing\\cnr061_geometry_horizon_sidecar\\CNR061_NOLEAK_DUPLICATE_AUDIT_2026-05-08.json",
      "catalog_row_id": "LCAT-000349",
      "sha256": "8f9d84082004c6ce2d41463f1c2afd71e5179a26e9f59fda2a3359521d6ac109",
      "size_bytes": 1808,
      "source_family": "research_route_artifact"
    },
    {
      "absolute_path": "C:\\tmp\\gtos_otb\\NOFILLTICKRECOVERY\\research\\science_program_2026_05\\06_outcome_testing\\cnr061_geometry_horizon_sidecar\\CNR061_NOLEAK_DUPLICATE_AUDIT_2026-05-08.md",
      "catalog_row_id": "LCAT-000350",
      "sha256": "a880839a15fa6ac19751b18cc45b5567d85c9e5d9a60ada4be04a6c73a5854ac",
      "size_bytes": 2106,
      "source_family": "research_route_artifact"
    },
    {
      "absolute_path": "C:\\tmp\\gtos_otb\\NOFILLTICKRECOVERY\\research\\science_program_2026_05\\06_outcome_testing\\cnr061_geometry_horizon_sidecar\\CNR061_SOURCE_JOIN_MAP_2026-05-08.json",
      "catalog_row_id": "LCAT-000351",
      "sha256": "60ebcd0c75adc9836f79aaeb9ff53c93cd45e8947823cafc426ff6bab5aece4b",
      "size_bytes": 3078,
      "source_family": "research_route_artifact"
    },
    {
      "absolute_path": "C:\\tmp\\gtos_otb\\NOFILLTICKRECOVERY\\research\\science_program_2026_05\\06_outcome_testing\\cnr061_geometry_horizon_sidecar\\CNR061_SOURCE_JOIN_MAP_2026-05-08.md",
      "catalog_row_id": "LCAT-000352",
      "sha256": "6ec847ee6b12a24d03553d5c6ccaa1f1e540fb33f18d687721a8d513665140db",
      "size_bytes": 3358,
      "source_family": "research_route_artifact"
    },
    {
      "absolute_path": "C:\\tmp\\gtos_otb\\NOFILLTICKRECOVERY\\research\\science_program_2026_05\\06_outcome_testing\\cnr061_geometry_horizon_sidecar\\CNR061_SOURCE_SEARCH_AND_HASH_LEDGER_2026-05-08.json",
      "catalog_row_id": "LCAT-000353",
      "sha256": "9b6739b76c3c7c61434da15c502b2d0f6cfa23d1b1a8d76baecb596010e4c744",
      "size_bytes": 44260,
      "source_family": "research_route_artifact"
    },
    {
      "absolute_path": "C:\\tmp\\gtos_otb\\NOFILLTICKRECOVERY\\research\\science_program_2026_05\\06_outcome_testing\\cnr061_geometry_horizon_sidecar\\CNR061_SOURCE_SEARCH_AND_HASH_LEDGER_2026-05-08.md",
      "catalog_row_id": "LCAT-000354",
      "sha256": "dd4c0d2a5be240e782634a07f9ce12431a8536b980a9dd088f8c408d6ea3aac6",
      "size_bytes": 44563,
      "source_family": "research_route_artifact"
    },
    {
      "absolute_path": "C:\\tmp\\gtos_otb\\NOFILLTICKRECOVERY\\research\\science_program_2026_05\\06_outcome_testing\\cnr061_geometry_horizon_sidecar\\build_cnr061_geometry_horizon_sidecar_2026_05_08.py",
      "catalog_row_id": "LCAT-000355",
      "sha256": "2e6c325a6190b0d453d268979c9e7f20df5f23f78db2235d9fa940411eea2d40",
      "size_bytes": 47958,
      "source_family": "research_route_artifact"
    },
    {
      "absolute_path": "C:\\tmp\\gtos_otb\\NOFILLTICKRECOVERY\\research\\science_program_2026_05\\06_outcome_testing\\cnr061_geometry_horizon_sidecar\\test_cnr061_geometry_horizon_sidecar_2026_05_08.py",
      "catalog_row_id": "LCAT-000356",
      "sha256": "43fbfe1a683a22d582d8923ef9e0ac30d4e62153779117ead74fed6587b56a0c",
      "size_bytes": 2421,
      "source_family": "research_route_artifact"
    },
    {
      "absolute_path": "C:\\tmp\\gtos_otb\\NOFILLTICKRECOVERY\\research\\science_program_2026_05\\06_outcome_testing\\cnr061_geometry_horizon_sidecar\\verify_cnr061_geometry_horizon_sidecar_2026_05_08.py",
      "catalog_row_id": "LCAT-000357",
      "sha256": "084a21fbe3d6ad55abe0ec27f2b85b6517e0efad20c028075ec074aea9774075",
      "size_bytes": 8747,
      "source_family": "research_route_artifact"
    },
    {
      "absolute_path": "C:\\tmp\\gtos_otb\\NOFILLTICKRECOVERY\\research\\science_program_2026_05\\06_outcome_testing\\cnr_geometry_decay_residual_control\\CNR_CONTEXT_CONTINUITY_AND_INSTRUCTION_COVERAGE_2026-05-08.json",
      "catalog_row_id": "LCAT-000358",
      "sha256": "3a6c2ca39bc27ebc6959cac44b6ffbc326951ff8184fdc0d5e02c18c26fd77d0",
      "size_bytes": 5081,
      "source_family": "research_route_artifact"
    },
    {
      "absolute_path": "C:\\tmp\\gtos_otb\\NOFILLTICKRECOVERY\\research\\science_program_2026_05\\06_outcome_testing\\cnr_geometry_decay_residual_control\\CNR_CONTEXT_CONTINUITY_AND_INSTRUCTION_COVERAGE_2026-05-08.md",
      "catalog_row_id": "LCAT-000359",
      "sha256": "214cd2dc86e2a9b209c9524a0485a49ade376ba9bb2d5604a1a8840f4a854620",
      "size_bytes": 5356,
      "source_family": "research_route_artifact"
    },
    {
      "absolute_path": "C:\\tmp\\gtos_otb\\NOFILLTICKRECOVERY\\research\\science_program_2026_05\\06_outcome_testing\\cnr_geometry_decay_residual_control\\CNR_GEOMETRY_DECAY_INPUT_ROW_MATRIX_2026-05-08.jsonl",
      "catalog_row_id": "LCAT-000360",
      "sha256": "8294e74c306abfb7cb1f9546710ff71214804815a339997c987ff53a72a3ade5",
      "size_bytes": 439654,
      "source_family": "research_route_artifact"
    },
    {
      "absolute_path": "C:\\tmp\\gtos_otb\\NOFILLTICKRECOVERY\\research\\science_program_2026_05\\06_outcome_testing\\cnr_geometry_decay_residual_control\\CNR_GEOMETRY_DECAY_RESIDUAL_CONTROL_COMPLETION_AUDIT_2026-05-08.json",
      "catalog_row_id": "LCAT-000361",
      "sha256": "7c71263bc2b590ba6f7de6156e9795c1c300ee34edb8c98964c39939ee224774",
      "size_bytes": 6192,
      "source_family": "research_route_artifact"
    },
    {
      "absolute_path": "C:\\tmp\\gtos_otb\\NOFILLTICKRECOVERY\\research\\science_program_2026_05\\06_outcome_testing\\cnr_geometry_decay_residual_control\\CNR_GEOMETRY_DECAY_RESIDUAL_CONTROL_COMPLETION_AUDIT_2026-05-08.md",
      "catalog_row_id": "LCAT-000362",
      "sha256": "43277cd3e75ce99cec08962cee26a96d8365ac1413378acac4ce9804da44adcc",
      "size_bytes": 6464,
      "source_family": "research_route_artifact"
    },
    {
      "absolute_path": "C:\\tmp\\gtos_otb\\NOFILLTICKRECOVERY\\research\\science_program_2026_05\\06_outcome_testing\\cnr_geometry_decay_residual_control\\CNR_GEOMETRY_DECAY_RESIDUAL_CONTROL_GOAL_PROMPT_2026-05-08.md",
      "catalog_row_id": "LCAT-000363",
      "sha256": "e45a7d58c88c2ca040a387ad280bbe1d860dfcb317da9496c65d5039c544e248",
      "size_bytes": 11927,
      "source_family": "research_route_artifact"
    },
    {
      "absolute_path": "C:\\tmp\\gtos_otb\\NOFILLTICKRECOVERY\\research\\science_program_2026_05\\06_outcome_testing\\cnr_geometry_decay_residual_control\\CNR_GEOMETRY_DECAY_RESIDUAL_CONTROL_PREREG_2026-05-08.json",
      "catalog_row_id": "LCAT-000364",
      "sha256": "7ec544a416319d366fec7c026161d17f7bebddf816c88200837bf117eee418dd",
      "size_bytes": 4492,
      "source_family": "research_route_artifact"
    },
    {
      "absolute_path": "C:\\tmp\\gtos_otb\\NOFILLTICKRECOVERY\\research\\science_program_2026_05\\06_outcome_testing\\cnr_geometry_decay_residual_control\\CNR_GEOMETRY_DECAY_RESIDUAL_CONTROL_PREREG_2026-05-08.md",
      "catalog_row_id": "LCAT-000365",
      "sha256": "69f10c8bd3e8b02f5f0c21755659575610311361c25183e71f6cc6a1e4aa7b70",
      "size_bytes": 4794,
      "source_family": "research_route_artifact"
    },
    {
      "absolute_path": "C:\\tmp\\gtos_otb\\NOFILLTICKRECOVERY\\research\\science_program_2026_05\\06_outcome_testing\\cnr_geometry_decay_residual_control\\CNR_MARKET_ENTRY_INVALIDITY_GATE_SPEC_2026-05-08.json",
      "catalog_row_id": "LCAT-000366",
      "sha256": "30356eb9837454d2343d220d25faa7b6c53bfcfe2d912d2b34993542dc545d17",
      "size_bytes": 3050,
      "source_family": "research_route_artifact"
    },
    {
      "absolute_path": "C:\\tmp\\gtos_otb\\NOFILLTICKRECOVERY\\research\\science_program_2026_05\\06_outcome_testing\\cnr_geometry_decay_residual_control\\CNR_MARKET_ENTRY_INVALIDITY_GATE_SPEC_2026-05-08.md",
      "catalog_row_id": "LCAT-000367",
      "sha256": "61397553e29c4cd5d6480e8be2e052fd926cc1bbcc2867aee872f61c33864cdb",
      "size_bytes": 3291,
      "source_family": "research_route_artifact"
    },
    {
      "absolute_path": "C:\\tmp\\gtos_otb\\NOFILLTICKRECOVERY\\research\\science_program_2026_05\\06_outcome_testing\\cnr_geometry_decay_residual_control\\CNR_NEXT_ROUTE_BLOCKER_DECISION_LEDGER_2026-05-08.json",
      "catalog_row_id": "LCAT-000368",
      "sha256": "cc819f69aea3321a6fd26ec05dba6683c2d06454ea1dce7131812de2cc3516e1",
      "size_bytes": 8388,
      "source_family": "research_route_artifact"
    },
    {
      "absolute_path": "C:\\tmp\\gtos_otb\\NOFILLTICKRECOVERY\\research\\science_program_2026_05\\06_outcome_testing\\cnr_geometry_decay_residual_control\\CNR_NEXT_ROUTE_BLOCKER_DECISION_LEDGER_2026-05-08.md",
      "catalog_row_id": "LCAT-000369",
      "sha256": "b9bd5b6af459b6c7c2e8e9f177db479330625baf9c244727df52b1d08c4537ce",
      "size_bytes": 8684,
      "source_family": "research_route_artifact"
    },
    {
      "absolute_path": "C:\\tmp\\gtos_otb\\NOFILLTICKRECOVERY\\research\\science_program_2026_05\\06_outcome_testing\\cnr_geometry_decay_residual_control\\CNR_NOLEAK_DUPLICATE_SAMPLE_AUDIT_2026-05-08.json",
      "catalog_row_id": "LCAT-000370",
      "sha256": "798e5af02c55ddd85b8d67aeca7ecd7861657bdacb43708b532ceb238c596d55",
      "size_bytes": 3532,
      "source_family": "research_route_artifact"
    },
    {
      "absolute_path": "C:\\tmp\\gtos_otb\\NOFILLTICKRECOVERY\\research\\science_program_2026_05\\06_outcome_testing\\cnr_geometry_decay_residual_control\\CNR_NOLEAK_DUPLICATE_SAMPLE_AUDIT_2026-05-08.md",
      "catalog_row_id": "LCAT-000371",
      "sha256": "e64a9939757a16331858d5a67b6c0d6c3b41f177b9bd8bccd1d2ce75332e9ada",
      "size_bytes": 3790,
      "source_family": "research_route_artifact"
    },
    {
      "absolute_path": "C:\\tmp\\gtos_otb\\NOFILLTICKRECOVERY\\research\\science_program_2026_05\\06_outcome_testing\\cnr_geometry_decay_residual_control\\CNR_RESIDUAL_R_FIELD_AND_BIN_SPEC_2026-05-08.json",
      "catalog_row_id": "LCAT-000372",
      "sha256": "29c11536f2fffd3fbf30d7b19650e6cfe04c997397c0811cdbe040f51556e2a0",
      "size_bytes": 3337,
      "source_family": "research_route_artifact"
    },
    {
      "absolute_path": "C:\\tmp\\gtos_otb\\NOFILLTICKRECOVERY\\research\\science_program_2026_05\\06_outcome_testing\\cnr_geometry_decay_residual_control\\CNR_RESIDUAL_R_FIELD_AND_BIN_SPEC_2026-05-08.md",
      "catalog_row_id": "LCAT-000373",
      "sha256": "d02d0404bb5eb709e1e897b88484fc411b94fe344ab317f5fb4e411c8aaf8569",
      "size_bytes": 3619,
      "source_family": "research_route_artifact"
    },
    {
      "absolute_path": "C:\\tmp\\gtos_otb\\NOFILLTICKRECOVERY\\research\\science_program_2026_05\\06_outcome_testing\\cnr_geometry_decay_residual_control\\CNR_SOURCE_SEARCH_AND_HASH_LEDGER_2026-05-08.json",
      "catalog_row_id": "LCAT-000374",
      "sha256": "78759e1606d00fca76a173259c6ce838847c91dae77443d4dd3dc62a2f6a9e5d",
      "size_bytes": 33542,
      "source_family": "research_route_artifact"
    },
    {
      "absolute_path": "C:\\tmp\\gtos_otb\\NOFILLTICKRECOVERY\\research\\science_program_2026_05\\06_outcome_testing\\cnr_geometry_decay_residual_control\\CNR_SOURCE_SEARCH_AND_HASH_LEDGER_2026-05-08.md",
      "catalog_row_id": "LCAT-000375",
      "sha256": "0760e5902687eeb0b02046b6b52ac8ffea2bd82143954881fc12f7c131117de1",
      "size_bytes": 33824,
      "source_family": "research_route_artifact"
    },
    {
      "absolute_path": "C:\\tmp\\gtos_otb\\NOFILLTICKRECOVERY\\research\\science_program_2026_05\\06_outcome_testing\\cnr_geometry_decay_residual_control\\build_cnr_geometry_decay_residual_control_2026_05_08.py",
      "catalog_row_id": "LCAT-000376",
      "sha256": "d6f2a95f6d063aa2b9ee21d1c00c287862fad561f30ecc3ab321a8b613d33fe2",
      "size_bytes": 58861,
      "source_family": "research_route_artifact"
    },
    {
      "absolute_path": "C:\\tmp\\gtos_otb\\NOFILLTICKRECOVERY\\research\\science_program_2026_05\\06_outcome_testing\\cnr_geometry_decay_residual_control\\test_cnr_geometry_decay_residual_control_2026_05_08.py",
      "catalog_row_id": "LCAT-000377",
      "sha256": "de5582e4c2c02e16d246fb2b9a034f7822a8d0f88a91a4e32a6dbeb3fe237377",
      "size_bytes": 3555,
      "source_family": "research_route_artifact"
    },
    {
      "absolute_path": "C:\\tmp\\gtos_otb\\NOFILLTICKRECOVERY\\research\\science_program_2026_05\\06_outcome_testing\\cnr_geometry_decay_residual_control\\verify_cnr_geometry_decay_residual_control_2026_05_08.py",
      "catalog_row_id": "LCAT-000378",
      "sha256": "5ea1b8c82325fd4c2cb5ba1f8a6ed0f391f969ae0f2424d3576039df6a15359d",
      "size_bytes": 8558,
      "source_family": "research_route_artifact"
    },
    {
      "absolute_path": "C:\\tmp\\gtos_otb\\NOFILLTICKRECOVERY\\research\\science_program_2026_05\\06_outcome_testing\\cnr_next_model_control_pack\\CNR061_NO_TERMINAL_TIMEBOX_LIFECYCLE_PACKET_2026-05-08.json",
      "catalog_row_id": "LCAT-000379",
      "sha256": "eb715b7927c2dc2694322c8dfea058efb5f42c971f989ab10a442628ce5df615",
      "size_bytes": 2900,
      "source_family": "research_route_artifact"
    },
    {
      "absolute_path": "C:\\tmp\\gtos_otb\\NOFILLTICKRECOVERY\\research\\science_program_2026_05\\06_outcome_testing\\cnr_next_model_control_pack\\CNR061_NO_TERMINAL_TIMEBOX_LIFECYCLE_PACKET_2026-05-08.md",
      "catalog_row_id": "LCAT-000380",
      "sha256": "8e0c27a7c38283b1601ca659d546f8525080be0ceaa7067a2724edb460b56226",
      "size_bytes": 3123,
      "source_family": "research_route_artifact"
    },
    {
      "absolute_path": "C:\\tmp\\gtos_otb\\NOFILLTICKRECOVERY\\research\\science_program_2026_05\\06_outcome_testing\\cnr_next_model_control_pack\\CNR061_NO_TERMINAL_TIMEBOX_LIFECYCLE_PACKET_2026-05-08_ROWS.jsonl",
      "catalog_row_id": "LCAT-000381",
      "sha256": "89ad396b2d980eed75eee9ff747c73b074c3bfecc28a1b2b4f7961f49751e6f6",
      "size_bytes": 17542,
      "source_family": "research_route_artifact"
    },
    {
      "absolute_path": "C:\\tmp\\gtos_otb\\NOFILLTICKRECOVERY\\research\\science_program_2026_05\\06_outcome_testing\\cnr_next_model_control_pack\\CNR_E2_E3_E4_TIMING_PREREGISTRATION_2026-05-08.json",
      "catalog_row_id": "LCAT-000382",
      "sha256": "1d350e1cdb88baf7af3ba2f0a6f7b9b2bbae65378b2c36958bb93de22ba277c7",
      "size_bytes": 4958,
      "source_family": "research_route_artifact"
    },
    {
      "absolute_path": "C:\\tmp\\gtos_otb\\NOFILLTICKRECOVERY\\research\\science_program_2026_05\\06_outcome_testing\\cnr_next_model_control_pack\\CNR_E2_E3_E4_TIMING_PREREGISTRATION_2026-05-08.md",
      "catalog_row_id": "LCAT-000383",
      "sha256": "e37a2b2820e6a56c8ab47678d5c7c458e34a28f1894d981a56278c1b2fb9c2f1",
      "size_bytes": 5173,
      "source_family": "research_route_artifact"
    },
    {
      "absolute_path": "C:\\tmp\\gtos_otb\\NOFILLTICKRECOVERY\\research\\science_program_2026_05\\06_outcome_testing\\cnr_next_model_control_pack\\CNR_NEXT_MODEL_BLOCKER_AND_ROUTE_LEDGER_2026-05-08.json",
      "catalog_row_id": "LCAT-000384",
      "sha256": "e1ced510ae46f3b9d74d343cfe4fa4ab31c80bc0f5368a32a18fe937ae9af517",
      "size_bytes": 7102,
      "source_family": "research_route_artifact"
    },
    {
      "absolute_path": "C:\\tmp\\gtos_otb\\NOFILLTICKRECOVERY\\research\\science_program_2026_05\\06_outcome_testing\\cnr_next_model_control_pack\\CNR_NEXT_MODEL_BLOCKER_AND_ROUTE_LEDGER_2026-05-08.md",
      "catalog_row_id": "LCAT-000385",
      "sha256": "1f43616c08c43088cd8a0005f522dc682e1c433337265cc32db541f8ba47384d",
      "size_bytes": 7321,
      "source_family": "research_route_artifact"
    },
    {
      "absolute_path": "C:\\tmp\\gtos_otb\\NOFILLTICKRECOVERY\\research\\science_program_2026_05\\06_outcome_testing\\cnr_next_model_control_pack\\CNR_NEXT_MODEL_COMPLETION_AUDIT_2026-05-08.json",
      "catalog_row_id": "LCAT-000386",
      "sha256": "e0a7ff2fe9162bbf06df5cc7d4125e11315d68009d80f1197677afda7634c1dd",
      "size_bytes": 10106,
      "source_family": "research_route_artifact"
    },
    {
      "absolute_path": "C:\\tmp\\gtos_otb\\NOFILLTICKRECOVERY\\research\\science_program_2026_05\\06_outcome_testing\\cnr_next_model_control_pack\\CNR_NEXT_MODEL_COMPLETION_AUDIT_2026-05-08.md",
      "catalog_row_id": "LCAT-000387",
      "sha256": "b2cf198047b9b955a1da2caa6061dc294a33f720db667f8e8f28ceb8a2645456",
      "size_bytes": 10390,
      "source_family": "research_route_artifact"
    },
    {
      "absolute_path": "C:\\tmp\\gtos_otb\\NOFILLTICKRECOVERY\\research\\science_program_2026_05\\06_outcome_testing\\cnr_next_model_control_pack\\CNR_NEXT_MODEL_CONTEXT_ANCHOR_2026-05-08.json",
      "catalog_row_id": "LCAT-000388",
      "sha256": "f8f668995e0bcf0415fd549a4661775f578960146326e9c93f7f907e4d683140",
      "size_bytes": 14515,
      "source_family": "research_route_artifact"
    },
    {
      "absolute_path": "C:\\tmp\\gtos_otb\\NOFILLTICKRECOVERY\\research\\science_program_2026_05\\06_outcome_testing\\cnr_next_model_control_pack\\CNR_NEXT_MODEL_CONTEXT_ANCHOR_2026-05-08.md",
      "catalog_row_id": "LCAT-000389",
      "sha256": "30b58ce11c3f31db0191bb2b8115841ff3574e19d003e7d601d8946d0a3e8960",
      "size_bytes": 14724,
      "source_family": "research_route_artifact"
    },
    {
      "absolute_path": "C:\\tmp\\gtos_otb\\NOFILLTICKRECOVERY\\research\\science_program_2026_05\\06_outcome_testing\\cnr_next_model_control_pack\\CNR_NEXT_MODEL_CONTROL_PACK_GOAL_PROMPT_2026-05-08.md",
      "catalog_row_id": "LCAT-000390",
      "sha256": "32dda7996aaaab3402ee860fb76a8a3426c30bf52aa8eceb97f963fad3972cd7",
      "size_bytes": 13468,
      "source_family": "research_route_artifact"
    },
    {
      "absolute_path": "C:\\tmp\\gtos_otb\\NOFILLTICKRECOVERY\\research\\science_program_2026_05\\06_outcome_testing\\cnr_next_model_control_pack\\CNR_NEXT_MODEL_G12_AUDIT_PROMPT_PACK_2026-05-08.md",
      "catalog_row_id": "LCAT-000391",
      "sha256": "63a77309bd2a1f76a30ad060e5bd28da9b3631a6460eeb17cbdf7d228cfafd81",
      "size_bytes": 1514,
      "source_family": "research_route_artifact"
    },
    {
      "absolute_path": "C:\\tmp\\gtos_otb\\NOFILLTICKRECOVERY\\research\\science_program_2026_05\\06_outcome_testing\\cnr_next_model_control_pack\\CNR_T1_T2_T3_TARGET_PREREGISTRATION_2026-05-08.json",
      "catalog_row_id": "LCAT-000392",
      "sha256": "206f27b2eeb42a27c3afeae347317d359456e16168abff933524765b16027b39",
      "size_bytes": 4137,
      "source_family": "research_route_artifact"
    },
    {
      "absolute_path": "C:\\tmp\\gtos_otb\\NOFILLTICKRECOVERY\\research\\science_program_2026_05\\06_outcome_testing\\cnr_next_model_control_pack\\CNR_T1_T2_T3_TARGET_PREREGISTRATION_2026-05-08.md",
      "catalog_row_id": "LCAT-000393",
      "sha256": "599c3b75b8c84a370796bb8794e1289817685e9b4c2c0cdbe707402f24cf328a",
      "size_bytes": 4352,
      "source_family": "research_route_artifact"
    },
    {
      "absolute_path": "C:\\tmp\\gtos_otb\\NOFILLTICKRECOVERY\\research\\science_program_2026_05\\06_outcome_testing\\cnr_next_model_control_pack\\CNR_TIMING_TARGET_NOLEAK_DUPLICATE_SAMPLEFLOOR_AUDIT_2026-05-08.json",
      "catalog_row_id": "LCAT-000394",
      "sha256": "ed387eeaab2aabbf740e8fa3edf6a9a18e5b6c687c28ca9aba8196f822f33d92",
      "size_bytes": 3060,
      "source_family": "research_route_artifact"
    },
    {
      "absolute_path": "C:\\tmp\\gtos_otb\\NOFILLTICKRECOVERY\\research\\science_program_2026_05\\06_outcome_testing\\cnr_next_model_control_pack\\CNR_TIMING_TARGET_NOLEAK_DUPLICATE_SAMPLEFLOOR_AUDIT_2026-05-08.md",
      "catalog_row_id": "LCAT-000395",
      "sha256": "7ad2854b3991ba43c0ea2cf04a89cfea1264e8d8d46abfb1b541f392bd076fe1",
      "size_bytes": 3294,
      "source_family": "research_route_artifact"
    },
    {
      "absolute_path": "C:\\tmp\\gtos_otb\\NOFILLTICKRECOVERY\\research\\science_program_2026_05\\06_outcome_testing\\cnr_next_model_control_pack\\CNR_TIMING_TARGET_SOURCE_CONTRACTS_2026-05-08.json",
      "catalog_row_id": "LCAT-000396",
      "sha256": "ff94c2c86c3c76302bf7f4dc15175d8a7832d578a666f9c85c1dbfb144da9c7f",
      "size_bytes": 229593,
      "source_family": "research_route_artifact"
    },
    {
      "absolute_path": "C:\\tmp\\gtos_otb\\NOFILLTICKRECOVERY\\research\\science_program_2026_05\\06_outcome_testing\\cnr_next_model_control_pack\\CNR_TIMING_TARGET_SOURCE_CONTRACTS_2026-05-08.md",
      "catalog_row_id": "LCAT-000397",
      "sha256": "cd57f90ee925c439c65f71f1fd704632690b98983cf809d9657a5a518603a922",
      "size_bytes": 229807,
      "source_family": "research_route_artifact"
    },
    {
      "absolute_path": "C:\\tmp\\gtos_otb\\NOFILLTICKRECOVERY\\research\\science_program_2026_05\\06_outcome_testing\\cnr_next_model_control_pack\\CNR_XAGUSD_RESIDUAL_TARGET_FORENSICS_2026-05-08.json",
      "catalog_row_id": "LCAT-000398",
      "sha256": "d00021090007fade6e95f4ca131bf120bd01f6eaac1583fed278cfef593d9048",
      "size_bytes": 4702,
      "source_family": "research_route_artifact"
    },
    {
      "absolute_path": "C:\\tmp\\gtos_otb\\NOFILLTICKRECOVERY\\research\\science_program_2026_05\\06_outcome_testing\\cnr_next_model_control_pack\\CNR_XAGUSD_RESIDUAL_TARGET_FORENSICS_2026-05-08.md",
      "catalog_row_id": "LCAT-000399",
      "sha256": "286833b42afbc5060e151cef12c46879adbed567da31372ef120998f02a343e5",
      "size_bytes": 4918,
      "source_family": "research_route_artifact"
    },
    {
      "absolute_path": "C:\\tmp\\gtos_otb\\NOFILLTICKRECOVERY\\research\\science_program_2026_05\\06_outcome_testing\\cnr_next_model_control_pack\\build_cnr_next_model_control_pack_2026_05_08.py",
      "catalog_row_id": "LCAT-000400",
      "sha256": "3f2a6cccfcec1cce0e367d833d27b288dbb931a0d3de90835a77d0110b4c7534",
      "size_bytes": 53954,
      "source_family": "research_route_artifact"
    },
    {
      "absolute_path": "C:\\tmp\\gtos_otb\\NOFILLTICKRECOVERY\\research\\science_program_2026_05\\06_outcome_testing\\cnr_next_model_control_pack\\test_cnr_next_model_control_pack_2026_05_08.py",
      "catalog_row_id": "LCAT-000401",
      "sha256": "5c81d92e165140b19017e373396a0818c6cc01fab57bfbcdb2fd4f642fade471",
      "size_bytes": 7422,
      "source_family": "research_route_artifact"
    },
    {
      "absolute_path": "C:\\tmp\\gtos_otb\\NOFILLTICKRECOVERY\\research\\science_program_2026_05\\06_outcome_testing\\cnr_next_model_control_pack\\verify_cnr_next_model_control_pack_2026_05_08.py",
      "catalog_row_id": "LCAT-000402",
      "sha256": "f97caaf565e07ab62e6ee1874f70c215e7d7efa1fb3d03e7e682f7f92d7ba191",
      "size_bytes": 11011,
      "source_family": "research_route_artifact"
    },
    {
      "absolute_path": "C:\\tmp\\gtos_otb\\NOFILLTICKRECOVERY\\research\\science_program_2026_05\\06_outcome_testing\\cnr_source_field_packet_builder\\CNR_SOURCE_FIELD_ANTI_BOXING_REVIEW_2026-05-07.json",
      "catalog_row_id": "LCAT-000403",
      "sha256": "08740ba95afca3a6c6c23839ac3a5098d2301f89e320d9282585bf5a30943153",
      "size_bytes": 105339,
      "source_family": "research_route_artifact"
    },
    {
      "absolute_path": "C:\\tmp\\gtos_otb\\NOFILLTICKRECOVERY\\research\\science_program_2026_05\\06_outcome_testing\\cnr_source_field_packet_builder\\CNR_SOURCE_FIELD_ANTI_BOXING_REVIEW_2026-05-07.md",
      "catalog_row_id": "LCAT-000404",
      "sha256": "75a20b09148696527b681160e92d233e580dca52f485ac6e8c756e55d51936a8",
      "size_bytes": 105538,
      "source_family": "research_route_artifact"
    },
    {
      "absolute_path": "C:\\tmp\\gtos_otb\\NOFILLTICKRECOVERY\\research\\science_program_2026_05\\06_outcome_testing\\cnr_source_field_packet_builder\\CNR_SOURCE_FIELD_CAPTURE_LEDGER_2026-05-07.json",
      "catalog_row_id": "LCAT-000405",
      "sha256": "7801d46b0fe5ac54102e7902d49861c48e1bafe42d0baf450fb07e4c063cd1b8",
      "size_bytes": 3959,
      "source_family": "research_route_artifact"
    },
    {
      "absolute_path": "C:\\tmp\\gtos_otb\\NOFILLTICKRECOVERY\\research\\science_program_2026_05\\06_outcome_testing\\cnr_source_field_packet_builder\\CNR_SOURCE_FIELD_CAPTURE_LEDGER_2026-05-07.md",
      "catalog_row_id": "LCAT-000406",
      "sha256": "42dcebe46abaeb084cd2d9d3c7d96257f32d84610abe564e49bbfc3e4cbe47d6",
      "size_bytes": 4154,
      "source_family": "research_route_artifact"
    },
    {
      "absolute_path": "C:\\tmp\\gtos_otb\\NOFILLTICKRECOVERY\\research\\science_program_2026_05\\06_outcome_testing\\cnr_source_field_packet_builder\\CNR_SOURCE_FIELD_COMPLETION_AUDIT_2026-05-07.json",
      "catalog_row_id": "LCAT-000407",
      "sha256": "a59a47f3ecb50fca426dbb8a828ae76108c0e4f300814f2d4706aa2d9c2e1409",
      "size_bytes": 13046,
      "source_family": "research_route_artifact"
    },
    {
      "absolute_path": "C:\\tmp\\gtos_otb\\NOFILLTICKRECOVERY\\research\\science_program_2026_05\\06_outcome_testing\\cnr_source_field_packet_builder\\CNR_SOURCE_FIELD_COMPLETION_AUDIT_2026-05-07.md",
      "catalog_row_id": "LCAT-000408",
      "sha256": "3e138814c293aff669dbf6949b7480336f60b8558bf36c663e4ca08da5a935f4",
      "size_bytes": 13243,
      "source_family": "research_route_artifact"
    },
    {
      "absolute_path": "C:\\tmp\\gtos_otb\\NOFILLTICKRECOVERY\\research\\science_program_2026_05\\06_outcome_testing\\cnr_source_field_packet_builder\\CNR_SOURCE_FIELD_DATA_EXTRACTION_LEDGER_2026-05-07.json",
      "catalog_row_id": "LCAT-000409",
      "sha256": "dcf7d34017633ea3a41b18bbabce6ca904b84a07196e5da9be467c5e12388020",
      "size_bytes": 216358,
      "source_family": "research_route_artifact"
    },
    {
      "absolute_path": "C:\\tmp\\gtos_otb\\NOFILLTICKRECOVERY\\research\\science_program_2026_05\\06_outcome_testing\\cnr_source_field_packet_builder\\CNR_SOURCE_FIELD_DATA_EXTRACTION_LEDGER_2026-05-07.md",
      "catalog_row_id": "LCAT-000410",
      "sha256": "5fc6bada127e16c1ad19bc6d812078a51d8f7ddad75ac9976d647d50620bc6fd",
      "size_bytes": 216561,
      "source_family": "research_route_artifact"
    },
    {
      "absolute_path": "C:\\tmp\\gtos_otb\\NOFILLTICKRECOVERY\\research\\science_program_2026_05\\06_outcome_testing\\cnr_source_field_packet_builder\\CNR_SOURCE_FIELD_DUPLICATE_DENOMINATOR_REPORT_2026-05-07.json",
      "catalog_row_id": "LCAT-000411",
      "sha256": "bcdc81bd3fe9c8f6a85459cc95ed60b31bdf58e256dee780a14480bec17f7975",
      "size_bytes": 1723,
      "source_family": "research_route_artifact"
    },
    {
      "absolute_path": "C:\\tmp\\gtos_otb\\NOFILLTICKRECOVERY\\research\\science_program_2026_05\\06_outcome_testing\\cnr_source_field_packet_builder\\CNR_SOURCE_FIELD_DUPLICATE_DENOMINATOR_REPORT_2026-05-07.md",
      "catalog_row_id": "LCAT-000412",
      "sha256": "920387bb2060bab41e1fc4639aac456c01c828159e0887537aa0971ae995fd2d",
      "size_bytes": 1932,
      "source_family": "research_route_artifact"
    },
    {
      "absolute_path": "C:\\tmp\\gtos_otb\\NOFILLTICKRECOVERY\\research\\science_program_2026_05\\06_outcome_testing\\cnr_source_field_packet_builder\\CNR_SOURCE_FIELD_MULTITIMEFRAME_EVIDENCE_MAP_2026-05-07.json",
      "catalog_row_id": "LCAT-000413",
      "sha256": "bfc78a1adbb0be03db22fd1cf4dbaa8c7b66698aeb15b7083d372d1b60b2737d",
      "size_bytes": 1867,
      "source_family": "research_route_artifact"
    },
    {
      "absolute_path": "C:\\tmp\\gtos_otb\\NOFILLTICKRECOVERY\\research\\science_program_2026_05\\06_outcome_testing\\cnr_source_field_packet_builder\\CNR_SOURCE_FIELD_MULTITIMEFRAME_EVIDENCE_MAP_2026-05-07.md",
      "catalog_row_id": "LCAT-000414",
      "sha256": "d5222d5de2c37b39fd8308d44d91b0ae9b1101e5f27f69297c99a1ff8ea969cd",
      "size_bytes": 2075,
      "source_family": "research_route_artifact"
    },
    {
      "absolute_path": "C:\\tmp\\gtos_otb\\NOFILLTICKRECOVERY\\research\\science_program_2026_05\\06_outcome_testing\\cnr_source_field_packet_builder\\CNR_SOURCE_FIELD_NEXT_G12_AUDIT_PROMPT_PACK_2026-05-07.md",
      "catalog_row_id": "LCAT-000415",
      "sha256": "a00bfe9a875482ae828d29e0b4ff7620a175da2c601926404333fabb1f2d271f",
      "size_bytes": 2555,
      "source_family": "research_route_artifact"
    },
    {
      "absolute_path": "C:\\tmp\\gtos_otb\\NOFILLTICKRECOVERY\\research\\science_program_2026_05\\06_outcome_testing\\cnr_source_field_packet_builder\\CNR_SOURCE_FIELD_NOLEAK_FORBIDDEN_FIELD_SCAN_2026-05-07.json",
      "catalog_row_id": "LCAT-000416",
      "sha256": "cf166d7abda15cd32686771e395348927cdbbd92ea8fd5b61d4e29a96f65eb6d",
      "size_bytes": 1215,
      "source_family": "research_route_artifact"
    },
    {
      "absolute_path": "C:\\tmp\\gtos_otb\\NOFILLTICKRECOVERY\\research\\science_program_2026_05\\06_outcome_testing\\cnr_source_field_packet_builder\\CNR_SOURCE_FIELD_NOLEAK_FORBIDDEN_FIELD_SCAN_2026-05-07.md",
      "catalog_row_id": "LCAT-000417",
      "sha256": "99113db6cc772d894a2b244d062b7d6c63a7c7ea6c561efc933fd7ac302d7876",
      "size_bytes": 1424,
      "source_family": "research_route_artifact"
    },
    {
      "absolute_path": "C:\\tmp\\gtos_otb\\NOFILLTICKRECOVERY\\research\\science_program_2026_05\\06_outcome_testing\\cnr_source_field_packet_builder\\CNR_SOURCE_FIELD_PACKET_BUILDER_CONTEXT_ANCHOR_2026-05-07.json",
      "catalog_row_id": "LCAT-000418",
      "sha256": "eb8933423147161d226fa4305674e7513fa6f79d46d8761598c7d9117cc4538e",
      "size_bytes": 4563,
      "source_family": "research_route_artifact"
    },
    {
      "absolute_path": "C:\\tmp\\gtos_otb\\NOFILLTICKRECOVERY\\research\\science_program_2026_05\\06_outcome_testing\\cnr_source_field_packet_builder\\CNR_SOURCE_FIELD_PACKET_BUILDER_CONTEXT_ANCHOR_2026-05-07.md",
      "catalog_row_id": "LCAT-000419",
      "sha256": "60dc78204074ab0010a760fc6159982844621a3971a12131cdabaeb3b046c39e",
      "size_bytes": 3838,
      "source_family": "research_route_artifact"
    },
    {
      "absolute_path": "C:\\tmp\\gtos_otb\\NOFILLTICKRECOVERY\\research\\science_program_2026_05\\06_outcome_testing\\cnr_source_field_packet_builder\\CNR_SOURCE_FIELD_PACKET_BUILDER_GOAL_PROMPT_2026-05-07.md",
      "catalog_row_id": "LCAT-000420",
      "sha256": "4511b51ffd8e4c69cc2aea4faa5ebab17e7b221d9d6dcd33a8fa56ef114112bf",
      "size_bytes": 10624,
      "source_family": "research_route_artifact"
    },
    {
      "absolute_path": "C:\\tmp\\gtos_otb\\NOFILLTICKRECOVERY\\research\\science_program_2026_05\\06_outcome_testing\\cnr_source_field_packet_builder\\CNR_SOURCE_FIELD_PACKET_MANIFEST_2026-05-07.json",
      "catalog_row_id": "LCAT-000421",
      "sha256": "bfe31c2fb87a19b0139431e0eed5cb1926afffe6986ab395f56cf6e3d2c3b6e3",
      "size_bytes": 4717,
      "source_family": "research_route_artifact"
    },
    {
      "absolute_path": "C:\\tmp\\gtos_otb\\NOFILLTICKRECOVERY\\research\\science_program_2026_05\\06_outcome_testing\\cnr_source_field_packet_builder\\CNR_SOURCE_FIELD_PACKET_MANIFEST_2026-05-07.md",
      "catalog_row_id": "LCAT-000422",
      "sha256": "b853d952ef982decfd9a73a74dd41340c77fb60954644d88a346b1a664423f93",
      "size_bytes": 4913,
      "source_family": "research_route_artifact"
    },
    {
      "absolute_path": "C:\\tmp\\gtos_otb\\NOFILLTICKRECOVERY\\research\\science_program_2026_05\\06_outcome_testing\\cnr_source_field_packet_builder\\CNR_SOURCE_FIELD_SAMPLE_FLOOR_AND_EXPANSION_REPORT_2026-05-07.json",
      "catalog_row_id": "LCAT-000424",
      "sha256": "70608a18c3f0837f070787e792cd1b71042c1618b8327eecf738f56c2384094c",
      "size_bytes": 3693,
      "source_family": "research_route_artifact"
    },
    {
      "absolute_path": "C:\\tmp\\gtos_otb\\NOFILLTICKRECOVERY\\research\\science_program_2026_05\\06_outcome_testing\\cnr_source_field_packet_builder\\CNR_SOURCE_FIELD_SAMPLE_FLOOR_AND_EXPANSION_REPORT_2026-05-07.md",
      "catalog_row_id": "LCAT-000425",
      "sha256": "aa2e5e900e159c455824b3351008aff9be040e5e144817fc325e62941908c098",
      "size_bytes": 3907,
      "source_family": "research_route_artifact"
    },
    {
      "absolute_path": "C:\\tmp\\gtos_otb\\NOFILLTICKRECOVERY\\research\\science_program_2026_05\\06_outcome_testing\\cnr_source_field_packet_builder\\CNR_SOURCE_FIELD_SOURCE_HASH_MANIFEST_2026-05-07.json",
      "catalog_row_id": "LCAT-000426",
      "sha256": "2e4b7219a8cb0a6636421e284bb397d02fcc7fff380f8fabae58c9aed8f1bf8c",
      "size_bytes": 32284,
      "source_family": "research_route_artifact"
    },
    {
      "absolute_path": "C:\\tmp\\gtos_otb\\NOFILLTICKRECOVERY\\research\\science_program_2026_05\\06_outcome_testing\\cnr_source_field_packet_builder\\CNR_SOURCE_FIELD_SOURCE_HASH_MANIFEST_2026-05-07.md",
      "catalog_row_id": "LCAT-000427",
      "sha256": "bc7a96fc779170e94c80942d25ba60aade828d6ee42a9e75b45a601f81561d54",
      "size_bytes": 32485,
      "source_family": "research_route_artifact"
    },
    {
      "absolute_path": "C:\\tmp\\gtos_otb\\NOFILLTICKRECOVERY\\research\\science_program_2026_05\\06_outcome_testing\\cnr_source_field_packet_builder\\CNR_SOURCE_FIELD_VERIFICATION_RESULTS_2026-05-07.json",
      "catalog_row_id": "LCAT-000428",
      "sha256": "1269472592e759502e2641b946778383a7d2bd3239ff4daf16d6ae24f8985ae6",
      "size_bytes": 2339,
      "source_family": "research_route_artifact"
    },
    {
      "absolute_path": "C:\\tmp\\gtos_otb\\NOFILLTICKRECOVERY\\research\\science_program_2026_05\\06_outcome_testing\\cnr_source_field_packet_builder\\CNR_SOURCE_FIELD_VERIFICATION_RESULTS_2026-05-07.md",
      "catalog_row_id": "LCAT-000429",
      "sha256": "3a37ef4c9bfad4f5bf80790a0b93fbc7fd68c085b0ceae490cb14bd571d2bc99",
      "size_bytes": 2559,
      "source_family": "research_route_artifact"
    },
    {
      "absolute_path": "C:\\tmp\\gtos_otb\\NOFILLTICKRECOVERY\\research\\science_program_2026_05\\06_outcome_testing\\cnr_source_field_packet_builder\\build_cnr_source_field_packet_builder_2026_05_07.py",
      "catalog_row_id": "LCAT-000430",
      "sha256": "28e36e00b68f8104dd00d6597098aaa62db6b67a6aa893f6f14676730d9b2761",
      "size_bytes": 60320,
      "source_family": "research_route_artifact"
    },
    {
      "absolute_path": "C:\\tmp\\gtos_otb\\NOFILLTICKRECOVERY\\research\\science_program_2026_05\\06_outcome_testing\\cnr_source_field_packet_builder\\test_cnr_source_field_packet_builder_2026_05_07.py",
      "catalog_row_id": "LCAT-000431",
      "sha256": "d44af85e53feffbe3470881f4d0f305b7d68bd4ef00723b4a5171dd3f0581e04",
      "size_bytes": 2183,
      "source_family": "research_route_artifact"
    },
    {
      "absolute_path": "C:\\tmp\\gtos_otb\\NOFILLTICKRECOVERY\\research\\science_program_2026_05\\06_outcome_testing\\cnr_source_field_packet_builder\\verify_cnr_source_field_packet_builder_2026_05_07.py",
      "catalog_row_id": "LCAT-000432",
      "sha256": "20a341750304c8a5755335f1779c8ffda3066897ebdba90bfd799b76aa4325fe",
      "size_bytes": 10618,
      "source_family": "research_route_artifact"
    },
    {
      "absolute_path": "C:\\tmp\\gtos_otb\\NOFILLTICKRECOVERY\\research\\science_program_2026_05\\06_outcome_testing\\cnr_t3_lifecycle_expansion_source_packet\\CNR_T3_BLOCKER_AND_IMPOSSIBILITY_LEDGER_2026-05-08.json",
      "catalog_row_id": "LCAT-000433",
      "sha256": "1f6e7ead32dba5fe5a40bcceffe8c733316e8b0b9ea3ef23f045eeb42e92c25e",
      "size_bytes": 170165,
      "source_family": "research_route_artifact"
    },
    {
      "absolute_path": "C:\\tmp\\gtos_otb\\NOFILLTICKRECOVERY\\research\\science_program_2026_05\\06_outcome_testing\\cnr_t3_lifecycle_expansion_source_packet\\CNR_T3_BLOCKER_AND_IMPOSSIBILITY_LEDGER_2026-05-08.md",
      "catalog_row_id": "LCAT-000434",
      "sha256": "a069fc94a4b2310cd2a5af686932e0c0a4136bfb223167fa374929183473d861",
      "size_bytes": 73659,
      "source_family": "research_route_artifact"
    },
    {
      "absolute_path": "C:\\tmp\\gtos_otb\\NOFILLTICKRECOVERY\\research\\science_program_2026_05\\06_outcome_testing\\cnr_t3_lifecycle_expansion_source_packet\\CNR_T3_COMPLETION_AUDIT_2026-05-08.json",
      "catalog_row_id": "LCAT-000435",
      "sha256": "de1ee0c89999e5daefc166fe0140be495f013c8ed42da8239b605dbd33a6ca16",
      "size_bytes": 7947,
      "source_family": "research_route_artifact"
    },
    {
      "absolute_path": "C:\\tmp\\gtos_otb\\NOFILLTICKRECOVERY\\research\\science_program_2026_05\\06_outcome_testing\\cnr_t3_lifecycle_expansion_source_packet\\CNR_T3_COMPLETION_AUDIT_2026-05-08.md",
      "catalog_row_id": "LCAT-000436",
      "sha256": "a4b0fb32416dde9caf2fc6cd7123db595e3ca4691a00db87d113b40a00d873a8",
      "size_bytes": 4417,
      "source_family": "research_route_artifact"
    },
    {
      "absolute_path": "C:\\tmp\\gtos_otb\\NOFILLTICKRECOVERY\\research\\science_program_2026_05\\06_outcome_testing\\cnr_t3_lifecycle_expansion_source_packet\\CNR_T3_CONTEXT_ANCHOR_2026-05-08.json",
      "catalog_row_id": "LCAT-000437",
      "sha256": "424595b2e759bf96961bed292c0ae109c6c64ed89481106bcdab0a898a35c014",
      "size_bytes": 18740,
      "source_family": "research_route_artifact"
    },
    {
      "absolute_path": "C:\\tmp\\gtos_otb\\NOFILLTICKRECOVERY\\research\\science_program_2026_05\\06_outcome_testing\\cnr_t3_lifecycle_expansion_source_packet\\CNR_T3_CONTEXT_ANCHOR_2026-05-08.md",
      "catalog_row_id": "LCAT-000438",
      "sha256": "bc683d021a609fed285b299c1a045117a158bb2dbee55b538619848da461a8a1",
      "size_bytes": 7975,
      "source_family": "research_route_artifact"
    },
    {
      "absolute_path": "C:\\tmp\\gtos_otb\\NOFILLTICKRECOVERY\\research\\science_program_2026_05\\06_outcome_testing\\cnr_t3_lifecycle_expansion_source_packet\\CNR_T3_FROZEN_LIFECYCLE_CONTRACT_2026-05-08.json",
      "catalog_row_id": "LCAT-000439",
      "sha256": "41802e5ac8eca2ea83e8f67576400f79d9ec5fbecd345df2d302dbd5d4d76beb",
      "size_bytes": 3894,
      "source_family": "research_route_artifact"
    },
    {
      "absolute_path": "C:\\tmp\\gtos_otb\\NOFILLTICKRECOVERY\\research\\science_program_2026_05\\06_outcome_testing\\cnr_t3_lifecycle_expansion_source_packet\\CNR_T3_FROZEN_LIFECYCLE_CONTRACT_2026-05-08.md",
      "catalog_row_id": "LCAT-000440",
      "sha256": "2bd9e0bc703b52fc05cb04c3930ac46d53f4535ca307af89cc673e69975c457b",
      "size_bytes": 2291,
      "source_family": "research_route_artifact"
    },
    {
      "absolute_path": "C:\\tmp\\gtos_otb\\NOFILLTICKRECOVERY\\research\\science_program_2026_05\\06_outcome_testing\\cnr_t3_lifecycle_expansion_source_packet\\CNR_T3_G12_AUDIT_PROMPT_PACK_2026-05-08.md",
      "catalog_row_id": "LCAT-000441",
      "sha256": "8c322ae6f130d4befffc5bd91a2aac4b886233de52421c3c05492682050053bf",
      "size_bytes": 2357,
      "source_family": "research_route_artifact"
    },
    {
      "absolute_path": "C:\\tmp\\gtos_otb\\NOFILLTICKRECOVERY\\research\\science_program_2026_05\\06_outcome_testing\\cnr_t3_lifecycle_expansion_source_packet\\CNR_T3_LIFECYCLE_EXPANSION_SOURCE_PACKET_GOAL_PROMPT_2026-05-08.md",
      "catalog_row_id": "LCAT-000442",
      "sha256": "b597cff832e1d3078b9d0e6a493ad6c1e4ec5e83f14aa2cb01a0aca61bc7fd07",
      "size_bytes": 13095,
      "source_family": "research_route_artifact"
    },
    {
      "absolute_path": "C:\\tmp\\gtos_otb\\NOFILLTICKRECOVERY\\research\\science_program_2026_05\\06_outcome_testing\\cnr_t3_lifecycle_expansion_source_packet\\CNR_T3_LIFECYCLE_FORENSICS_AND_LEARNING_2026-05-08.json",
      "catalog_row_id": "LCAT-000443",
      "sha256": "8c68733e3be5d3fac1123370aade84e46ca694e8f60801be5fb6f62eff64d01a",
      "size_bytes": 3021,
      "source_family": "research_route_artifact"
    },
    {
      "absolute_path": "C:\\tmp\\gtos_otb\\NOFILLTICKRECOVERY\\research\\science_program_2026_05\\06_outcome_testing\\cnr_t3_lifecycle_expansion_source_packet\\CNR_T3_LIFECYCLE_FORENSICS_AND_LEARNING_2026-05-08.md",
      "catalog_row_id": "LCAT-000444",
      "sha256": "7d84b8c92f9ae78f545e8fe0c936e4d97716540e63af5051de1bc0401de9c41a",
      "size_bytes": 2421,
      "source_family": "research_route_artifact"
    },
    {
      "absolute_path": "C:\\tmp\\gtos_otb\\NOFILLTICKRECOVERY\\research\\science_program_2026_05\\06_outcome_testing\\cnr_t3_lifecycle_expansion_source_packet\\CNR_T3_LIFECYCLE_PACKET_2026-05-08.json",
      "catalog_row_id": "LCAT-000445",
      "sha256": "079bcb461b6b3bc59948ebc400c6dce2a73f18a3b58da9b0c6fb10eecfe48e3b",
      "size_bytes": 1366,
      "source_family": "research_route_artifact"
    },
    {
      "absolute_path": "C:\\tmp\\gtos_otb\\NOFILLTICKRECOVERY\\research\\science_program_2026_05\\06_outcome_testing\\cnr_t3_lifecycle_expansion_source_packet\\CNR_T3_LIFECYCLE_PACKET_2026-05-08.md",
      "catalog_row_id": "LCAT-000446",
      "sha256": "4ff6a75013044a4789f4dce2c4a5702eb7d177fda5158fabb0936408bb361788",
      "size_bytes": 607,
      "source_family": "research_route_artifact"
    },
    {
      "absolute_path": "C:\\tmp\\gtos_otb\\NOFILLTICKRECOVERY\\research\\science_program_2026_05\\06_outcome_testing\\cnr_t3_lifecycle_expansion_source_packet\\CNR_T3_LIFECYCLE_PACKET_2026-05-08_ROWS.jsonl",
      "catalog_row_id": "LCAT-000447",
      "sha256": "00e63cb7ab87174eae25a5e3aec2fb81600fda2f3aa95d1fc91ae93bee544bef",
      "size_bytes": 15164,
      "source_family": "research_route_artifact"
    },
    {
      "absolute_path": "C:\\tmp\\gtos_otb\\NOFILLTICKRECOVERY\\research\\science_program_2026_05\\06_outcome_testing\\cnr_t3_lifecycle_expansion_source_packet\\CNR_T3_NOLEAK_DUPLICATE_SAMPLEFLOOR_AUDIT_2026-05-08.json",
      "catalog_row_id": "LCAT-000448",
      "sha256": "4d48113920e83d93a4a536f2ddf985ad098c0d67a3b15eb4f14d5086d5c5eb15",
      "size_bytes": 2140,
      "source_family": "research_route_artifact"
    },
    {
      "absolute_path": "C:\\tmp\\gtos_otb\\NOFILLTICKRECOVERY\\research\\science_program_2026_05\\06_outcome_testing\\cnr_t3_lifecycle_expansion_source_packet\\CNR_T3_NOLEAK_DUPLICATE_SAMPLEFLOOR_AUDIT_2026-05-08.md",
      "catalog_row_id": "LCAT-000449",
      "sha256": "dc1d7a10d232589beb7f05fc165e31028537e2b80e0830c986670d8492471c4f",
      "size_bytes": 503,
      "source_family": "research_route_artifact"
    },
    {
      "absolute_path": "C:\\tmp\\gtos_otb\\NOFILLTICKRECOVERY\\research\\science_program_2026_05\\06_outcome_testing\\cnr_t3_lifecycle_expansion_source_packet\\CNR_T3_NO_TERMINAL_CANDIDATE_INVENTORY_2026-05-08.json",
      "catalog_row_id": "LCAT-000450",
      "sha256": "e730720d8af12b124056d59625ee2bb891773bade441074cd8ec040ac88a921f",
      "size_bytes": 456682,
      "source_family": "research_route_artifact"
    },
    {
      "absolute_path": "C:\\tmp\\gtos_otb\\NOFILLTICKRECOVERY\\research\\science_program_2026_05\\06_outcome_testing\\cnr_t3_lifecycle_expansion_source_packet\\CNR_T3_NO_TERMINAL_CANDIDATE_INVENTORY_2026-05-08.md",
      "catalog_row_id": "LCAT-000451",
      "sha256": "db88c3a5a96925bc81dba61c54113f75d6aa87e55c68fe36e1b148c4eb379710",
      "size_bytes": 80792,
      "source_family": "research_route_artifact"
    },
    {
      "absolute_path": "C:\\tmp\\gtos_otb\\NOFILLTICKRECOVERY\\research\\science_program_2026_05\\06_outcome_testing\\cnr_t3_lifecycle_expansion_source_packet\\CNR_T3_SEARCHED_ROOT_AND_SOURCE_HASH_LEDGER_2026-05-08.json",
      "catalog_row_id": "LCAT-000452",
      "sha256": "b5a9df7abbce14159ee2fc896cae1a923b06493d9d54e7600b788bff88e84377",
      "size_bytes": 18634,
      "source_family": "research_route_artifact"
    },
    {
      "absolute_path": "C:\\tmp\\gtos_otb\\NOFILLTICKRECOVERY\\research\\science_program_2026_05\\06_outcome_testing\\cnr_t3_lifecycle_expansion_source_packet\\CNR_T3_SEARCHED_ROOT_AND_SOURCE_HASH_LEDGER_2026-05-08.md",
      "catalog_row_id": "LCAT-000453",
      "sha256": "676107410b27a31426b11cab959ff2c6a42aaf77b119dee4d3089905c311d402",
      "size_bytes": 6635,
      "source_family": "research_route_artifact"
    },
    {
      "absolute_path": "C:\\tmp\\gtos_otb\\NOFILLTICKRECOVERY\\research\\science_program_2026_05\\06_outcome_testing\\cnr_t3_lifecycle_expansion_source_packet\\build_cnr_t3_lifecycle_expansion_source_packet_2026_05_08.py",
      "catalog_row_id": "LCAT-000454",
      "sha256": "1143afa7b672b3c942dfcefa93b2c36427149dad778833c1c0976a01d41a206b",
      "size_bytes": 75388,
      "source_family": "research_route_artifact"
    },
    {
      "absolute_path": "C:\\tmp\\gtos_otb\\NOFILLTICKRECOVERY\\research\\science_program_2026_05\\06_outcome_testing\\cnr_t3_lifecycle_expansion_source_packet\\test_cnr_t3_lifecycle_expansion_source_packet_2026_05_08.py",
      "catalog_row_id": "LCAT-000455",
      "sha256": "888ca1f29d0eb826364de194b9d4631ea190209cd1a2710b29fc3a1add8ba9bc",
      "size_bytes": 4200,
      "source_family": "research_route_artifact"
    },
    {
      "absolute_path": "C:\\tmp\\gtos_otb\\NOFILLTICKRECOVERY\\research\\science_program_2026_05\\06_outcome_testing\\cnr_t3_lifecycle_expansion_source_packet\\verify_cnr_t3_lifecycle_expansion_source_packet_2026_05_08.py",
      "catalog_row_id": "LCAT-000456",
      "sha256": "68599e7039b8c2a03367bfc3a039b1877751430abb2ed68427d931e11ecf0865",
      "size_bytes": 8797,
      "source_family": "research_route_artifact"
    },
    {
      "absolute_path": "C:\\tmp\\gtos_otb\\NOFILLTICKRECOVERY\\research\\science_program_2026_05\\06_outcome_testing\\cnr_timing_model_preregistration\\CNR_TIMING_MODEL_ANTI_BOXING_REVIEW_2026-05-07.json",
      "catalog_row_id": "LCAT-000457",
      "sha256": "e35fa288994a6c2c159bfe540937e46ed1629fe795a9e54ebe34323bcd7d8b4b",
      "size_bytes": 64633,
      "source_family": "research_route_artifact"
    },
    {
      "absolute_path": "C:\\tmp\\gtos_otb\\NOFILLTICKRECOVERY\\research\\science_program_2026_05\\06_outcome_testing\\cnr_timing_model_preregistration\\CNR_TIMING_MODEL_ANTI_BOXING_REVIEW_2026-05-07.md",
      "catalog_row_id": "LCAT-000458",
      "sha256": "527ba44682acbe729a2f369ec6fadfcd185df6944fd4409641531f31f32696c1",
      "size_bytes": 64848,
      "source_family": "research_route_artifact"
    },
    {
      "absolute_path": "C:\\tmp\\gtos_otb\\NOFILLTICKRECOVERY\\research\\science_program_2026_05\\06_outcome_testing\\cnr_timing_model_preregistration\\CNR_TIMING_MODEL_BLOCKER_AND_SAMPLE_FLOOR_LEDGER_2026-05-07.json",
      "catalog_row_id": "LCAT-000459",
      "sha256": "9e115801a49ae5aa4dcb843f968c77dad32e3e8a0605f854a77bf86c66779fb3",
      "size_bytes": 3112,
      "source_family": "research_route_artifact"
    },
    {
      "absolute_path": "C:\\tmp\\gtos_otb\\NOFILLTICKRECOVERY\\research\\science_program_2026_05\\06_outcome_testing\\cnr_timing_model_preregistration\\CNR_TIMING_MODEL_BLOCKER_AND_SAMPLE_FLOOR_LEDGER_2026-05-07.md",
      "catalog_row_id": "LCAT-000460",
      "sha256": "7ccb317bc33f9cf8ec1059aff109882201e518f43496614511cc07673cee358c",
      "size_bytes": 3340,
      "source_family": "research_route_artifact"
    },
    {
      "absolute_path": "C:\\tmp\\gtos_otb\\NOFILLTICKRECOVERY\\research\\science_program_2026_05\\06_outcome_testing\\cnr_timing_model_preregistration\\CNR_TIMING_MODEL_COMPLETION_AUDIT_2026-05-07.json",
      "catalog_row_id": "LCAT-000461",
      "sha256": "482940194047219f586cf518b5cccd6817c79a75f53386c886651b77fa946c57",
      "size_bytes": 16828,
      "source_family": "research_route_artifact"
    },
    {
      "absolute_path": "C:\\tmp\\gtos_otb\\NOFILLTICKRECOVERY\\research\\science_program_2026_05\\06_outcome_testing\\cnr_timing_model_preregistration\\CNR_TIMING_MODEL_COMPLETION_AUDIT_2026-05-07.md",
      "catalog_row_id": "LCAT-000462",
      "sha256": "540c31fa363b74bbc462a9760491c41c529ad9c3b3303ce2332a7e3560212f86",
      "size_bytes": 17041,
      "source_family": "research_route_artifact"
    },
    {
      "absolute_path": "C:\\tmp\\gtos_otb\\NOFILLTICKRECOVERY\\research\\science_program_2026_05\\06_outcome_testing\\cnr_timing_model_preregistration\\CNR_TIMING_MODEL_CONTEXT_ANCHOR_2026-05-07.json",
      "catalog_row_id": "LCAT-000463",
      "sha256": "248a7bf70b881940a8a52d4d8a132c39c5f596fc24df5e4513753c422f509143",
      "size_bytes": 69038,
      "source_family": "research_route_artifact"
    },
    {
      "absolute_path": "C:\\tmp\\gtos_otb\\NOFILLTICKRECOVERY\\research\\science_program_2026_05\\06_outcome_testing\\cnr_timing_model_preregistration\\CNR_TIMING_MODEL_CONTEXT_ANCHOR_2026-05-07.md",
      "catalog_row_id": "LCAT-000464",
      "sha256": "957d35b6cadc0310f2f55b463b8c9b9a14d4d21270cf9c490377736f3f48c817",
      "size_bytes": 69249,
      "source_family": "research_route_artifact"
    },
    {
      "absolute_path": "C:\\tmp\\gtos_otb\\NOFILLTICKRECOVERY\\research\\science_program_2026_05\\06_outcome_testing\\cnr_timing_model_preregistration\\CNR_TIMING_MODEL_CORRECT_DIRECTION_FAILURE_ANATOMY_2026-05-07.json",
      "catalog_row_id": "LCAT-000465",
      "sha256": "5fe803121c4811417217e6fb5944d3c0b13650e4a980d213396d6ce357d9c7eb",
      "size_bytes": 4239,
      "source_family": "research_route_artifact"
    },
    {
      "absolute_path": "C:\\tmp\\gtos_otb\\NOFILLTICKRECOVERY\\research\\science_program_2026_05\\06_outcome_testing\\cnr_timing_model_preregistration\\CNR_TIMING_MODEL_CORRECT_DIRECTION_FAILURE_ANATOMY_2026-05-07.md",
      "catalog_row_id": "LCAT-000466",
      "sha256": "ca68a8cb963debe76454804aaaf74adf555845e0dd861a3d0efc0cc4e2ccdcce",
      "size_bytes": 4677,
      "source_family": "research_route_artifact"
    },
    {
      "absolute_path": "C:\\tmp\\gtos_otb\\NOFILLTICKRECOVERY\\research\\science_program_2026_05\\06_outcome_testing\\cnr_timing_model_preregistration\\CNR_TIMING_MODEL_DATA_EXPANSION_PLAN_2026-05-07.json",
      "catalog_row_id": "LCAT-000467",
      "sha256": "7827a37ee4ff2f52b9edc78f7376ce48a5214c9f086b0a7d4ade89618b320b6f",
      "size_bytes": 92336,
      "source_family": "research_route_artifact"
    },
    {
      "absolute_path": "C:\\tmp\\gtos_otb\\NOFILLTICKRECOVERY\\research\\science_program_2026_05\\06_outcome_testing\\cnr_timing_model_preregistration\\CNR_TIMING_MODEL_DATA_EXPANSION_PLAN_2026-05-07.md",
      "catalog_row_id": "LCAT-000468",
      "sha256": "4b31175f07702cfe8aa11700782ddb9316ddeed62d6f317ecc845ef427dd9426",
      "size_bytes": 92552,
      "source_family": "research_route_artifact"
    },
    {
      "absolute_path": "C:\\tmp\\gtos_otb\\NOFILLTICKRECOVERY\\research\\science_program_2026_05\\06_outcome_testing\\cnr_timing_model_preregistration\\CNR_TIMING_MODEL_LATENCY_CAPTURE_SPEC_2026-05-07.json",
      "catalog_row_id": "LCAT-000469",
      "sha256": "62fe9a6006a0f680761ae1ca362e8420b5275a4248029a78d3b2880d43b44a8f",
      "size_bytes": 2354,
      "source_family": "research_route_artifact"
    },
    {
      "absolute_path": "C:\\tmp\\gtos_otb\\NOFILLTICKRECOVERY\\research\\science_program_2026_05\\06_outcome_testing\\cnr_timing_model_preregistration\\CNR_TIMING_MODEL_LATENCY_CAPTURE_SPEC_2026-05-07.md",
      "catalog_row_id": "LCAT-000470",
      "sha256": "d60f30c6a623c71cbb5c8d448cb4064151db326af0c41ca422a2fbdc15bb4236",
      "size_bytes": 2571,
      "source_family": "research_route_artifact"
    },
    {
      "absolute_path": "C:\\tmp\\gtos_otb\\NOFILLTICKRECOVERY\\research\\science_program_2026_05\\06_outcome_testing\\cnr_timing_model_preregistration\\CNR_TIMING_MODEL_MULTITIMEFRAME_EVIDENCE_MAP_2026-05-07.json",
      "catalog_row_id": "LCAT-000471",
      "sha256": "12e91c50336cace4c5d2f1f360b17be6a962e7591f9794a6ec3c4739d20311b0",
      "size_bytes": 65268,
      "source_family": "research_route_artifact"
    },
    {
      "absolute_path": "C:\\tmp\\gtos_otb\\NOFILLTICKRECOVERY\\research\\science_program_2026_05\\06_outcome_testing\\cnr_timing_model_preregistration\\CNR_TIMING_MODEL_MULTITIMEFRAME_EVIDENCE_MAP_2026-05-07.md",
      "catalog_row_id": "LCAT-000472",
      "sha256": "dfbf2f9425c6734c58b038d2b942e5d0813e5b0535dc4b7df9d3ff2168e5b2c5",
      "size_bytes": 65492,
      "source_family": "research_route_artifact"
    },
    {
      "absolute_path": "C:\\tmp\\gtos_otb\\NOFILLTICKRECOVERY\\research\\science_program_2026_05\\06_outcome_testing\\cnr_timing_model_preregistration\\CNR_TIMING_MODEL_NEXT_PACKET_PLAN_2026-05-07.json",
      "catalog_row_id": "LCAT-000473",
      "sha256": "6b13b2e91026f52c1542c47f9fc1ea53f07addde831718755c23b450cb75b68d",
      "size_bytes": 1858,
      "source_family": "research_route_artifact"
    },
    {
      "absolute_path": "C:\\tmp\\gtos_otb\\NOFILLTICKRECOVERY\\research\\science_program_2026_05\\06_outcome_testing\\cnr_timing_model_preregistration\\CNR_TIMING_MODEL_NEXT_PACKET_PLAN_2026-05-07.md",
      "catalog_row_id": "LCAT-000474",
      "sha256": "12b8bec38fafdcf4d7464768a3adab5df0e490deff056fc223691de68fbaac10",
      "size_bytes": 2071,
      "source_family": "research_route_artifact"
    },
    {
      "absolute_path": "C:\\tmp\\gtos_otb\\NOFILLTICKRECOVERY\\research\\science_program_2026_05\\06_outcome_testing\\cnr_timing_model_preregistration\\CNR_TIMING_MODEL_NOLEAK_DUPLICATE_LABEL_POLICY_2026-05-07.json",
      "catalog_row_id": "LCAT-000475",
      "sha256": "7ca944c774580f6ac57cbbcd487c5ffc29d3ce4a8dcbc3ebf81dffd9ca002718",
      "size_bytes": 2384,
      "source_family": "research_route_artifact"
    },
    {
      "absolute_path": "C:\\tmp\\gtos_otb\\NOFILLTICKRECOVERY\\research\\science_program_2026_05\\06_outcome_testing\\cnr_timing_model_preregistration\\CNR_TIMING_MODEL_NOLEAK_DUPLICATE_LABEL_POLICY_2026-05-07.md",
      "catalog_row_id": "LCAT-000476",
      "sha256": "4236a03da113c5ee9334e598269deac56e535fdca42e30326a50b0d3ed2fa357",
      "size_bytes": 2610,
      "source_family": "research_route_artifact"
    },
    {
      "absolute_path": "C:\\tmp\\gtos_otb\\NOFILLTICKRECOVERY\\research\\science_program_2026_05\\06_outcome_testing\\cnr_timing_model_preregistration\\CNR_TIMING_MODEL_PREREGISTRATION_2026-05-07.json",
      "catalog_row_id": "LCAT-000477",
      "sha256": "699b3aa27a48488a7e70a517d26df267278af6fc284efda56d1af52e65c9f00d",
      "size_bytes": 21556,
      "source_family": "research_route_artifact"
    },
    {
      "absolute_path": "C:\\tmp\\gtos_otb\\NOFILLTICKRECOVERY\\research\\science_program_2026_05\\06_outcome_testing\\cnr_timing_model_preregistration\\CNR_TIMING_MODEL_PREREGISTRATION_2026-05-07.md",
      "catalog_row_id": "LCAT-000478",
      "sha256": "1ffcdb90cef8c7b8dc1523acc25bb22618d492bb6c98e8068685910c738ec09c",
      "size_bytes": 21998,
      "source_family": "research_route_artifact"
    },
    {
      "absolute_path": "C:\\tmp\\gtos_otb\\NOFILLTICKRECOVERY\\research\\science_program_2026_05\\06_outcome_testing\\cnr_timing_model_preregistration\\CNR_TIMING_MODEL_PREREGISTRATION_GOAL_PROMPT_2026-05-07.md",
      "catalog_row_id": "LCAT-000479",
      "sha256": "52194222025379f4db73d6d7a7713ef550df2fe74a4388fe0c7e0bdadf0547e7",
      "size_bytes": 26292,
      "source_family": "research_route_artifact"
    },
    {
      "absolute_path": "C:\\tmp\\gtos_otb\\NOFILLTICKRECOVERY\\research\\science_program_2026_05\\06_outcome_testing\\cnr_timing_model_preregistration\\CNR_TIMING_MODEL_RECURSIVE_AMBIGUITY_LEDGER_2026-05-07.json",
      "catalog_row_id": "LCAT-000480",
      "sha256": "23a2ddc94cb0f6290f5c0104d1384385151a445978a083a1f470ea9462eaa558",
      "size_bytes": 3035,
      "source_family": "research_route_artifact"
    },
    {
      "absolute_path": "C:\\tmp\\gtos_otb\\NOFILLTICKRECOVERY\\research\\science_program_2026_05\\06_outcome_testing\\cnr_timing_model_preregistration\\CNR_TIMING_MODEL_RECURSIVE_AMBIGUITY_LEDGER_2026-05-07.md",
      "catalog_row_id": "LCAT-000481",
      "sha256": "18db95a6bd0ad0fc6f92137701444be30279db9cd8ac8b3cec2c9b0de1c22f95",
      "size_bytes": 3258,
      "source_family": "research_route_artifact"
    },
    {
      "absolute_path": "C:\\tmp\\gtos_otb\\NOFILLTICKRECOVERY\\research\\science_program_2026_05\\06_outcome_testing\\cnr_timing_model_preregistration\\CNR_TIMING_MODEL_SOURCE_FIELD_CONTRACT_2026-05-07.json",
      "catalog_row_id": "LCAT-000482",
      "sha256": "50a83c4a3bf9a921205faf6717d706fc3cb1bf9145d088b82a6997109b0db83a",
      "size_bytes": 95063,
      "source_family": "research_route_artifact"
    },
    {
      "absolute_path": "C:\\tmp\\gtos_otb\\NOFILLTICKRECOVERY\\research\\science_program_2026_05\\06_outcome_testing\\cnr_timing_model_preregistration\\CNR_TIMING_MODEL_SOURCE_FIELD_CONTRACT_2026-05-07.md",
      "catalog_row_id": "LCAT-000483",
      "sha256": "da6d0a8a9e7c6f689ebc71900ae94a5bc0b2ba4c9d5d7da67beb6f6e434c17e6",
      "size_bytes": 95281,
      "source_family": "research_route_artifact"
    },
    {
      "absolute_path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\data\\DXY_D1.csv",
      "catalog_row_id": "LCAT-000484",
      "sha256": "7da2e65e61087b2235fe2a5d6678b56f716a2a6d913be78b663faf1f0fdc23b9",
      "size_bytes": 20017,
      "source_family": "local_research_data"
    },
    {
      "absolute_path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\data\\EURUSD_D1.csv",
      "catalog_row_id": "LCAT-000485",
      "sha256": "cc0dbe2373b9ce94dabb295729e17ad24350281b57d03a9c3d807b3a5c2d60d5",
      "size_bytes": 30108,
      "source_family": "local_research_data"
    },
    {
      "absolute_path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\data\\EURUSD_H1.csv",
      "catalog_row_id": "LCAT-000486",
      "sha256": "17e289eeec2cd1fe9b91723f97c8bb74f0865b8de855027def35e7425b16cd96",
      "size_bytes": 828266,
      "source_family": "local_research_data"
    },
    {
      "absolute_path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\data\\EURUSD_H4.csv",
      "catalog_row_id": "LCAT-000487",
      "sha256": "7c696ae7aa2386f771959485e5af5bf6a51edebfcdc44340a72b15d72b186202",
      "size_bytes": 209541,
      "source_family": "local_research_data"
    },
    {
      "absolute_path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\data\\EURUSD_M15.csv",
      "catalog_row_id": "LCAT-000488",
      "sha256": "d56405a0a11016b368312deca3b59361c14206ca8694c9a372e46451096139f8",
      "size_bytes": 3273362,
      "source_family": "local_research_data"
    },
    {
      "absolute_path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\data\\EURUSD_M5.csv",
      "catalog_row_id": "LCAT-000489",
      "sha256": "41a2d240cfacb029c3f268dca8936d0fb4f3aa9e03d8238c006aab5afd6a3e83",
      "size_bytes": 5291443,
      "source_family": "local_research_data"
    },
    {
      "absolute_path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\data\\GBPUSD_D1.csv",
      "catalog_row_id": "LCAT-000490",
      "sha256": "8722fa67d7b8f70ddc5a856169a80252276f692554e1f732850d8b3a1065aafc",
      "size_bytes": 177741,
      "source_family": "local_research_data"
    },
    {
      "absolute_path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\data\\GBPUSD_H1.csv",
      "catalog_row_id": "LCAT-000491",
      "sha256": "c53974580ab455d7c3aa9093652826b271c6728ffce5bcaa91e60e18f0a0da0b",
      "size_bytes": 1165502,
      "source_family": "local_research_data"
    },
    {
      "absolute_path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\data\\GBPUSD_H4.csv",
      "catalog_row_id": "LCAT-000492",
      "sha256": "81ad64a3d3ad1b351f03a5fa558a9e5ef8b0c227e122961d1c3dc65039834b90",
      "size_bytes": 580221,
      "source_family": "local_research_data"
    },
    {
      "absolute_path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\data\\GBPUSD_M15.csv",
      "catalog_row_id": "LCAT-000493",
      "sha256": "6d104e8d62e9ea893dc3b705e6f392114619b9108bcfc3b0ae678db3b29c9d58",
      "size_bytes": 2902096,
      "source_family": "local_research_data"
    },
    {
      "absolute_path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\data\\GBPUSD_M5.csv",
      "catalog_row_id": "LCAT-000494",
      "sha256": "b4571cf13f78561345964d3106854e190ed895f53eb34267a9f808c6346aa65f",
      "size_bytes": 19603,
      "source_family": "local_research_data"
    },
    {
      "absolute_path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\data\\NAS100_D1.csv",
      "catalog_row_id": "LCAT-000495",
      "sha256": "04b7f6b49e67f7575ffa6d7ee64d0cac2e331fb8baaad9cdc8e9d247d09b439c",
      "size_bytes": 28780,
      "source_family": "local_research_data"
    },
    {
      "absolute_path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\data\\NAS100_H1.csv",
      "catalog_row_id": "LCAT-000496",
      "sha256": "b8a028cf1714367f673b3309b801e0903f4583129a1dc2f772c1c5d7a6adc78e",
      "size_bytes": 744327,
      "source_family": "local_research_data"
    },
    {
      "absolute_path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\data\\NAS100_H4.csv",
      "catalog_row_id": "LCAT-000497",
      "sha256": "f6ed040030a8e55579e84c8c6b56b4bee65d4dede9674b8a75c4c573cd8926c3",
      "size_bytes": 197086,
      "source_family": "local_research_data"
    },
    {
      "absolute_path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\data\\NAS100_M15.csv",
      "catalog_row_id": "LCAT-000498",
      "sha256": "ba1e450066659bece6c5374f81b66c58ec78e412db5ada13ef6bf8aae7f03a96",
      "size_bytes": 2934918,
      "source_family": "local_research_data"
    },
    {
      "absolute_path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\data\\NAS100_M5.csv",
      "catalog_row_id": "LCAT-000499",
      "sha256": "88cd6d26393a202a2fcca903463ec58287e206e52aed4620ffb57803ffceefd4",
      "size_bytes": 5301737,
      "source_family": "local_research_data"
    },
    {
      "absolute_path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\data\\XAGUSD_D1.csv",
      "catalog_row_id": "LCAT-000500",
      "sha256": "55b7bb9275ed99c5f37838c70dbefef3025d0a4f1c9406a3ccd8f8c9723949c5",
      "size_bytes": 26899,
      "source_family": "local_research_data"
    },
    {
      "absolute_path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\data\\XAGUSD_H1.csv",
      "catalog_row_id": "LCAT-000501",
      "sha256": "8f9dac30640c47b2c8ae8de60f3e680404aa22e3dce4b81c39347e0698755b30",
      "size_bytes": 723400,
      "source_family": "local_research_data"
    },
    {
      "absolute_path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\data\\XAGUSD_H4.csv",
      "catalog_row_id": "LCAT-000502",
      "sha256": "3cdc3e58284f866ef95012cd7989b8fc7ec8d89535150fda0de32979f62445c7",
      "size_bytes": 189481,
      "source_family": "local_research_data"
    },
    {
      "absolute_path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\data\\XAGUSD_M15.csv",
      "catalog_row_id": "LCAT-000503",
      "sha256": "f80f7ebb87b065f73d20c7f55a95245f8c0d8640f75d1410bd5e1afcac4ce506",
      "size_bytes": 2850025,
      "source_family": "local_research_data"
    },
    {
      "absolute_path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\data\\XAGUSD_M5.csv",
      "catalog_row_id": "LCAT-000504",
      "sha256": "5efd8120a22cd2c99daefe27f41becb1093faccb7de31636aa1000c484e7be45",
      "size_bytes": 4729418,
      "source_family": "local_research_data"
    },
    {
      "absolute_path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\data\\XAUUSD_D1.csv",
      "catalog_row_id": "LCAT-000505",
      "sha256": "fce7d961f04583957f4d7c86eb15420464a79f8610eb2fc66781bf2ebbf34d99",
      "size_bytes": 3872,
      "source_family": "local_research_data"
    },
    {
      "absolute_path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\data\\XAUUSD_H1.csv",
      "catalog_row_id": "LCAT-000506",
      "sha256": "cd15facd79121b6a68cea6f1f96881aa4916e44c06805f6613e45b64078766b5",
      "size_bytes": 12582,
      "source_family": "local_research_data"
    },
    {
      "absolute_path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\data\\XAUUSD_H4.csv",
      "catalog_row_id": "LCAT-000507",
      "sha256": "e2975ab7cee83617719ff9776cea41f31771fa69288fbd858345a0578d66631a",
      "size_bytes": 7613,
      "source_family": "local_research_data"
    },
    {
      "absolute_path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\data\\XAUUSD_M15.csv",
      "catalog_row_id": "LCAT-000508",
      "sha256": "7293d55a8cc1371550fee51f8b3e1a8bda0615583c55fe2c7ec1f4c4b81d83be",
      "size_bytes": 43229,
      "source_family": "local_research_data"
    },
    {
      "absolute_path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\data\\XAUUSD_M5.csv",
      "catalog_row_id": "LCAT-000509",
      "sha256": "cb3a59f34909e69e00dc0a6524624a68f1f185c3d0558e417be3890262d55f44",
      "size_bytes": 18529,
      "source_family": "local_research_data"
    },
    {
      "absolute_path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\data\\economic_calendar.csv",
      "catalog_row_id": "LCAT-000510",
      "sha256": "a8656473535dd47a7e72c3aab04c6f51fa1be29891973d783e48d89474d53dd2",
      "size_bytes": 1572,
      "source_family": "local_research_data"
    },
    {
      "absolute_path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\data\\news_calendar.json",
      "catalog_row_id": "LCAT-000511",
      "sha256": "04050615d70e43cbcdce1619ba8e7afeb18fb8630e0cefcd2b69ffeb5f74c136",
      "size_bytes": 3972,
      "source_family": "local_research_data"
    },
    {
      "absolute_path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\data\\external\\features\\GBPJPY\\phase3_m15_candidate_gap_external_v1_20260501T005921Z.jsonl",
      "catalog_row_id": "LCAT-000514",
      "sha256": "ea10783f03feb861a4c856c5bacdb68ccd253c0d3354abaee437dc69d8f52123",
      "size_bytes": 1549414,
      "source_family": "local_external_or_vendor_cache"
    },
    {
      "absolute_path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\data\\external\\features\\GBPUSD\\phase3_m15_candidate_gap_external_v1_20260501T005921Z.jsonl",
      "catalog_row_id": "LCAT-000521",
      "sha256": "3a1f9c61a3738d62328af86036fe4bb190c9d4e451eac58f5b85d7cda8033f43",
      "size_bytes": 1557200,
      "source_family": "local_external_or_vendor_cache"
    },
    {
      "absolute_path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\data\\external\\features\\GBPUSD\\smoke_phase3_m15_20260430T235137Z.jsonl",
      "catalog_row_id": "LCAT-000522",
      "sha256": "a5a196a0b2e369fc080dcd72c0d3f77eeff50295a011c12f1ca8a85a1733df8f",
      "size_bytes": 117120,
      "source_family": "local_external_or_vendor_cache"
    },
    {
      "absolute_path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\data\\external\\features\\NAS100\\phase3_m15_candidate_gap_external_v1_20260501T005921Z.jsonl",
      "catalog_row_id": "LCAT-000529",
      "sha256": "e0cfa063a3690499e04860637dc536eb2ab83333a591ec8813cc173173e75861",
      "size_bytes": 1485988,
      "source_family": "local_external_or_vendor_cache"
    },
    {
      "absolute_path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\data\\external\\features\\NAS100\\smoke_phase3_m15_20260430T235137Z.jsonl",
      "catalog_row_id": "LCAT-000530",
      "sha256": "372cfb51519676dcfa78029b226bea3e5b3e69f983e0e440e67178278b24a9ce",
      "size_bytes": 117120,
      "source_family": "local_external_or_vendor_cache"
    },
    {
      "absolute_path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\data\\external\\features\\US30_CASH\\phase3_m15_candidate_gap_external_v1_20260501T005921Z.jsonl",
      "catalog_row_id": "LCAT-000537",
      "sha256": "4007bc531ddfb385ce746e7b31f22c14ef83b97d96fcec9ceb9dc4c92385fd71",
      "size_bytes": 1486368,
      "source_family": "local_external_or_vendor_cache"
    },
    {
      "absolute_path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\data\\external\\features\\US30_CASH\\smoke_phase3_m15_20260430T235137Z.jsonl",
      "catalog_row_id": "LCAT-000538",
      "sha256": "df281e38a5d1c340871c95893cd387b69e781db45223ce27f019b0b8d0bf41bb",
      "size_bytes": 117125,
      "source_family": "local_external_or_vendor_cache"
    },
    {
      "absolute_path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\data\\external\\features\\USDJPY\\phase3_m15_candidate_gap_external_v1_20260501T005921Z.jsonl",
      "catalog_row_id": "LCAT-000541",
      "sha256": "45f6ee9e0f961e5279b19246f492a5b244baf80ea7766641f1b62e1ce4a51df9",
      "size_bytes": 1557200,
      "source_family": "local_external_or_vendor_cache"
    },
    {
      "absolute_path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\data\\external\\features\\XAGUSD\\phase3_m15_candidate_gap_external_v1_20260501T005921Z.jsonl",
      "catalog_row_id": "LCAT-000548",
      "sha256": "2a76bb6aada41da18f59a2a228edae6ca793b61e48c7f46a40c282faed2e5419",
      "size_bytes": 1716660,
      "source_family": "local_external_or_vendor_cache"
    },
    {
      "absolute_path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\data\\external\\features\\XAGUSD\\smoke_phase3_m15_20260430T235137Z.jsonl",
      "catalog_row_id": "LCAT-000549",
      "sha256": "67fb16abbf4e28ebf2b546d8044a6c01d78b64a6b01c734a65049fed08e06216",
      "size_bytes": 117120,
      "source_family": "local_external_or_vendor_cache"
    },
    {
      "absolute_path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\data\\external\\features\\XAUUSD\\20260430T221000Z.json",
      "catalog_row_id": "LCAT-000550",
      "sha256": "27bf10c8df5e8666fd81dd5c597aff816d8458b9ddc4fd2568b3dde3b9965ada",
      "size_bytes": 1613,
      "source_family": "local_external_or_vendor_cache"
    },
    {
      "absolute_path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\data\\external\\features\\XAUUSD\\20260430T225000Z.json",
      "catalog_row_id": "LCAT-000551",
      "sha256": "8b080b96cbf6bd4afee0285bb3d6adc279bc866c697af9b5e9e54f13b3b6e4eb",
      "size_bytes": 37731,
      "source_family": "local_external_or_vendor_cache"
    },
    {
      "absolute_path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\data\\external\\features\\XAUUSD\\phase3_m15_candidate_gap_external_v1_20260501T005921Z.jsonl",
      "catalog_row_id": "LCAT-000558",
      "sha256": "0242c0547c2b1d433dccb438a7a1ccbf304392d6a89622575f18084a2a09d3c4",
      "size_bytes": 2189768,
      "source_family": "local_external_or_vendor_cache"
    },
    {
      "absolute_path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\data\\external\\features\\XAUUSD\\smoke_phase3_m15_20260430T235137Z.jsonl",
      "catalog_row_id": "LCAT-000559",
      "sha256": "847312778969e2f53065cb2c7128b906da56ab4d5b471e6506005bfaa55978ed",
      "size_bytes": 117120,
      "source_family": "local_external_or_vendor_cache"
    },
    {
      "absolute_path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\data\\external\\normalized\\cftc_cot\\disagg_combined_20260430T220916Z.jsonl",
      "catalog_row_id": "LCAT-000560",
      "sha256": "ecf30a74d1a8791055eb3ca456049ca31660d1c83b10983dccfeead4b4bfa477",
      "size_bytes": 10271,
      "source_family": "local_external_or_vendor_cache"
    },
    {
      "absolute_path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\data\\external\\normalized\\cftc_cot\\disagg_combined_20260430T234727Z.jsonl",
      "catalog_row_id": "LCAT-000561",
      "sha256": "9ea15dda54673845b3e8eb8e4b5bde0343242dd911c763a8919da2c976567960",
      "size_bytes": 100146,
      "source_family": "local_external_or_vendor_cache"
    },
    {
      "absolute_path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\data\\external\\normalized\\cftc_cot\\disagg_combined_20260501T000733Z.jsonl",
      "catalog_row_id": "LCAT-000562",
      "sha256": "ed95cb998071f6386633ae4b44d2921c1aacb8f48a5c732174fbdf4bbf20063b",
      "size_bytes": 120816,
      "source_family": "local_external_or_vendor_cache"
    },
    {
      "absolute_path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\data\\external\\normalized\\flashalpha_gex\\DIA_gex_20260430T224718Z.jsonl",
      "catalog_row_id": "LCAT-000563",
      "sha256": "690c1306fa8eac711352d67b0bb97033c8ef3d2dfe202d5ba044fff0dcd68a82",
      "size_bytes": 364,
      "source_family": "local_external_or_vendor_cache"
    },
    {
      "absolute_path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\data\\external\\normalized\\flashalpha_gex\\DIA_gex_20260430T234828Z.jsonl",
      "catalog_row_id": "LCAT-000564",
      "sha256": "40b35cf475ec9be4973a03c91715af34eba202b2c3581023b8c4a756a7d01059",
      "size_bytes": 364,
      "source_family": "local_external_or_vendor_cache"
    },
    {
      "absolute_path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\data\\external\\normalized\\flashalpha_gex\\DIA_gex_20260501T001141Z.jsonl",
      "catalog_row_id": "LCAT-000565",
      "sha256": "8030ec3b2626bfea5c6817c7e566822f2de2acf73bf7b89385c1ce7ba6066386",
      "size_bytes": 377,
      "source_family": "local_external_or_vendor_cache"
    },
    {
      "absolute_path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\data\\external\\normalized\\flashalpha_gex\\GLD_gex_20260430T224721Z.jsonl",
      "catalog_row_id": "LCAT-000566",
      "sha256": "32761840948b1dc6a00d4dd20da1c61c4771f678f32e02ac855a0127e320b5da",
      "size_bytes": 367,
      "source_family": "local_external_or_vendor_cache"
    },
    {
      "absolute_path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\data\\external\\normalized\\flashalpha_gex\\GLD_gex_20260430T234832Z.jsonl",
      "catalog_row_id": "LCAT-000567",
      "sha256": "002965e92cb928cc893250dd9094121e1f2a7d0095eb2605a3dc76579be60ad6",
      "size_bytes": 367,
      "source_family": "local_external_or_vendor_cache"
    },
    {
      "absolute_path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\data\\external\\normalized\\flashalpha_gex\\GLD_gex_20260501T001144Z.jsonl",
      "catalog_row_id": "LCAT-000568",
      "sha256": "2e806e263172f378ce9e8814dde5f9520522b7d751864b5f0dc577baa6b2305a",
      "size_bytes": 366,
      "source_family": "local_external_or_vendor_cache"
    },
    {
      "absolute_path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\data\\external\\normalized\\flashalpha_gex\\QQQ_gex_20260430T224718Z.jsonl",
      "catalog_row_id": "LCAT-000569",
      "sha256": "e72baaccc64eaa97e51d131af6a949698626338b8ee98fc276d70bc0d1f1c333",
      "size_bytes": 365,
      "source_family": "local_external_or_vendor_cache"
    },
    {
      "absolute_path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\data\\external\\normalized\\flashalpha_gex\\QQQ_gex_20260430T234825Z.jsonl",
      "catalog_row_id": "LCAT-000570",
      "sha256": "a8d6dfe56110ca0c32794bd60803f873ca3aff45a18d14936e42e7ad04d2064a",
      "size_bytes": 365,
      "source_family": "local_external_or_vendor_cache"
    },
    {
      "absolute_path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\data\\external\\normalized\\flashalpha_gex\\QQQ_gex_20260501T001140Z.jsonl",
      "catalog_row_id": "LCAT-000571",
      "sha256": "68c59da8e59f7304609af759c8d0a99c1ff75b0495c40c7a285cdf7899a5189a",
      "size_bytes": 364,
      "source_family": "local_external_or_vendor_cache"
    },
    {
      "absolute_path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\data\\external\\normalized\\flashalpha_gex\\SLV_gex_20260430T224723Z.jsonl",
      "catalog_row_id": "LCAT-000572",
      "sha256": "845fd4785c62d11e6fd79afd446344fc83d9798394646521e82b2085e206735d",
      "size_bytes": 365,
      "source_family": "local_external_or_vendor_cache"
    },
    {
      "absolute_path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\data\\external\\normalized\\flashalpha_gex\\SLV_gex_20260430T234834Z.jsonl",
      "catalog_row_id": "LCAT-000573",
      "sha256": "d7d915206271110f1fc93b17cdd16794cb101e3c574288935d332ad7d90629a5",
      "size_bytes": 377,
      "source_family": "local_external_or_vendor_cache"
    },
    {
      "absolute_path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\data\\external\\normalized\\flashalpha_gex\\SLV_gex_20260501T001145Z.jsonl",
      "catalog_row_id": "LCAT-000574",
      "sha256": "e8e9e9628dc2dbe7d8424b10c4a86294a46ac2f10cc2be66f146df29e9bf9a1a",
      "size_bytes": 365,
      "source_family": "local_external_or_vendor_cache"
    },
    {
      "absolute_path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\data\\external\\normalized\\flashalpha_gex\\SPY_gex_20260430T224720Z.jsonl",
      "catalog_row_id": "LCAT-000575",
      "sha256": "6df49e2440b2fb4dfa017e7decf9219bc7b0d3d44c75f41d99ba0dc326a90d7a",
      "size_bytes": 364,
      "source_family": "local_external_or_vendor_cache"
    },
    {
      "absolute_path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\data\\external\\normalized\\flashalpha_gex\\SPY_gex_20260430T234830Z.jsonl",
      "catalog_row_id": "LCAT-000576",
      "sha256": "b7f1f5839b23063647426c455ec203e50b038408161bd511aa924ea1c504ac63",
      "size_bytes": 363,
      "source_family": "local_external_or_vendor_cache"
    },
    {
      "absolute_path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\data\\external\\normalized\\flashalpha_gex\\SPY_gex_20260501T001143Z.jsonl",
      "catalog_row_id": "LCAT-000577",
      "sha256": "9b2cc5414a0792fb908d65b15a102202805f3b701bbdc5d42c43d087da10c103",
      "size_bytes": 364,
      "source_family": "local_external_or_vendor_cache"
    },
    {
      "absolute_path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\data\\external\\normalized\\fred\\DFII10_observations_20260430T234725Z.jsonl",
      "catalog_row_id": "LCAT-000578",
      "sha256": "a87b433462372ded399dd7ed962bac5301a1eb059393010470ce0c0ed1588150",
      "size_bytes": 235716,
      "source_family": "local_external_or_vendor_cache"
    },
    {
      "absolute_path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\data\\external\\normalized\\fred\\DFII10_observations_20260501T000731Z.jsonl",
      "catalog_row_id": "LCAT-000579",
      "sha256": "a7a46df13aa975101594d99b5a97b456d569acee591b160b9d05cf9f3567189f",
      "size_bytes": 354156,
      "source_family": "local_external_or_vendor_cache"
    },
    {
      "absolute_path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\data\\external\\normalized\\fred\\DGS10_observations_20260430T220916Z.jsonl",
      "catalog_row_id": "LCAT-000580",
      "sha256": "fa15cd8ec91de758cff914435fe15f8f8533dae36c60d1e61cec81b33f8086de",
      "size_bytes": 4365,
      "source_family": "local_external_or_vendor_cache"
    },
    {
      "absolute_path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\data\\external\\normalized\\fred\\DGS10_observations_20260430T234724Z.jsonl",
      "catalog_row_id": "LCAT-000581",
      "sha256": "8d48b733b561d57218ccf1f90b8695b5cae9d1585261699be27f50b4a7da480c",
      "size_bytes": 234526,
      "source_family": "local_external_or_vendor_cache"
    },
    {
      "absolute_path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\data\\external\\normalized\\fred\\DGS10_observations_20260501T000730Z.jsonl",
      "catalog_row_id": "LCAT-000582",
      "sha256": "5c2854cb0f19021dca9b0202249b1bd425712db22f47193394074898433d3d9c",
      "size_bytes": 352966,
      "source_family": "local_external_or_vendor_cache"
    },
    {
      "absolute_path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\data\\external\\normalized\\fred\\DGS2_observations_20260430T234724Z.jsonl",
      "catalog_row_id": "LCAT-000583",
      "sha256": "840ad232007705216c1dfb4c4d1b7b4650db8e5b98d704882227c4f1cc2d4ca9",
      "size_bytes": 233387,
      "source_family": "local_external_or_vendor_cache"
    },
    {
      "absolute_path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\data\\external\\normalized\\fred\\DGS2_observations_20260501T000730Z.jsonl",
      "catalog_row_id": "LCAT-000584",
      "sha256": "e4cc2262bc993a8fc9368707dfd10e6eca13401459c4ba55722c0075eadc5f45",
      "size_bytes": 351827,
      "source_family": "local_external_or_vendor_cache"
    },
    {
      "absolute_path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\data\\external\\normalized\\fred\\DTWEXBGS_observations_20260430T234726Z.jsonl",
      "catalog_row_id": "LCAT-000585",
      "sha256": "c8fb196c6859db4c454d3d6d71a2e8a47213857aed53b1f7a1d81d4b9bf83d66",
      "size_bytes": 241566,
      "source_family": "local_external_or_vendor_cache"
    },
    {
      "absolute_path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\data\\external\\normalized\\fred\\DTWEXBGS_observations_20260501T000732Z.jsonl",
      "catalog_row_id": "LCAT-000586",
      "sha256": "07f1055791470e274d0bdfce1ea4c11e34440aee4a3fa2742e5b9c2eaf9f3fe9",
      "size_bytes": 359691,
      "source_family": "local_external_or_vendor_cache"
    },
    {
      "absolute_path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\data\\external\\normalized\\fred\\GVZCLS_observations_20260430T234726Z.jsonl",
      "catalog_row_id": "LCAT-000587",
      "sha256": "bd9ccbe4f403f01e8e08d8e97becefd89ae1555b0bce5f4f83f327bb3af960a4",
      "size_bytes": 236735,
      "source_family": "local_external_or_vendor_cache"
    },
    {
      "absolute_path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\data\\external\\normalized\\fred\\GVZCLS_observations_20260501T000732Z.jsonl",
      "catalog_row_id": "LCAT-000588",
      "sha256": "b791f8dc873062b052e8fca6c27a817d9aa19bd6f7fc1f1fed0c193c26b70807",
      "size_bytes": 355175,
      "source_family": "local_external_or_vendor_cache"
    },
    {
      "absolute_path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\data\\external\\normalized\\fred\\T10YIE_observations_20260430T234725Z.jsonl",
      "catalog_row_id": "LCAT-000589",
      "sha256": "38434c9014184510f69a576379dcac95015decbc9c62c6f32798186fc4b04f63",
      "size_bytes": 235869,
      "source_family": "local_external_or_vendor_cache"
    },
    {
      "absolute_path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\data\\external\\normalized\\fred\\T10YIE_observations_20260501T000731Z.jsonl",
      "catalog_row_id": "LCAT-000590",
      "sha256": "978344106a334b085933a95fd27957fdf25fa01f3ab710fd44cbdcc1bad7b1e1",
      "size_bytes": 354414,
      "source_family": "local_external_or_vendor_cache"
    },
    {
      "absolute_path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\data\\external\\normalized\\fred\\VIXCLS_observations_20260430T234726Z.jsonl",
      "catalog_row_id": "LCAT-000591",
      "sha256": "e6fc00ad0d31d609023239303880451870708f41499daf6d39217309d3eabaa1",
      "size_bytes": 236741,
      "source_family": "local_external_or_vendor_cache"
    },
    {
      "absolute_path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\data\\external\\normalized\\fred\\VIXCLS_observations_20260501T000732Z.jsonl",
      "catalog_row_id": "LCAT-000592",
      "sha256": "373b877a3a0e1d3ec7cc4d485ab1a4e9efa286415a19ce0bd195bcac44e9af7a",
      "size_bytes": 355181,
      "source_family": "local_external_or_vendor_cache"
    },
    {
      "absolute_path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\data\\external\\normalized\\lbma_calendar\\fix_calendar_20260430T220916Z.jsonl",
      "catalog_row_id": "LCAT-000593",
      "sha256": "deb6415b4290f2e52ccf34a0f4daa09e70730dca61cd904c70609d24a8bf64bb",
      "size_bytes": 698,
      "source_family": "local_external_or_vendor_cache"
    },
    {
      "absolute_path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\data\\external\\normalized\\lbma_calendar\\fix_calendar_20260430T234700Z.jsonl",
      "catalog_row_id": "LCAT-000594",
      "sha256": "949785c362f3b003a52ebfc916842409062e3376fdf63a5ab8d0a88d80aa0616",
      "size_bytes": 184925,
      "source_family": "local_external_or_vendor_cache"
    },
    {
      "absolute_path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\data\\external\\normalized\\lbma_calendar\\fix_calendar_20260430T234825Z.jsonl",
      "catalog_row_id": "LCAT-000595",
      "sha256": "949785c362f3b003a52ebfc916842409062e3376fdf63a5ab8d0a88d80aa0616",
      "size_bytes": 184925,
      "source_family": "local_external_or_vendor_cache"
    },
    {
      "absolute_path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\data\\external\\normalized\\lbma_calendar\\fix_calendar_20260501T000949Z.jsonl",
      "catalog_row_id": "LCAT-000596",
      "sha256": "24a433cbaaf20a28611d843ff563fe258af0dd0593f65af0ada1dcecc4d1507d",
      "size_bytes": 103244,
      "source_family": "local_external_or_vendor_cache"
    },
    {
      "absolute_path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\data\\external\\normalized\\wgc\\gold_demand_trends_20260430T225431Z.jsonl",
      "catalog_row_id": "LCAT-000597",
      "sha256": "0dee188de0c70951a456d54e08b307c8acc5a8bb04198bd1314cd7d1af9c54ae",
      "size_bytes": 5589049,
      "source_family": "local_external_or_vendor_cache"
    },
    {
      "absolute_path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\data\\external\\normalized\\wgc\\gold_demand_trends_20260430T234945Z.jsonl",
      "catalog_row_id": "LCAT-000598",
      "sha256": "5e4012fcdb512325bfc574eef585d8e1507d0d8b65d549633bc724f6335b71d1",
      "size_bytes": 5589049,
      "source_family": "local_external_or_vendor_cache"
    },
    {
      "absolute_path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\data\\external\\normalized\\wgc\\gold_etf_flows_20260430T224531Z.jsonl",
      "catalog_row_id": "LCAT-000599",
      "sha256": "d5372ca263dd0ebfc1b5a36230659725f3bd97a9e6451c336b673423e2c74341",
      "size_bytes": 50229,
      "source_family": "local_external_or_vendor_cache"
    },
    {
      "absolute_path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\data\\external\\normalized\\wgc\\gold_etf_flows_20260430T234945Z.jsonl",
      "catalog_row_id": "LCAT-000600",
      "sha256": "76abf4d657e0e96d9dc207fc8f03f568c6cf55aae29f8a44f0a23c1df3b14492",
      "size_bytes": 50229,
      "source_family": "local_external_or_vendor_cache"
    },
    {
      "absolute_path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\data\\external\\raw\\cftc_cot\\disagg_combined_20260430T220916Z.json",
      "catalog_row_id": "LCAT-000601",
      "sha256": "6e643c1aac981c97c3472f0113f7fe670431e63f287bd36aefe64f15104b6356",
      "size_bytes": 136287,
      "source_family": "local_external_or_vendor_cache"
    },
    {
      "absolute_path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\data\\external\\raw\\cftc_cot\\disagg_combined_20260430T220916Z.json.meta.json",
      "catalog_row_id": "LCAT-000602",
      "sha256": "5215bb87e7493e9fe4834e9a9b7f60e29c1736e1081a8b8d4b8d77b8cdd71f28",
      "size_bytes": 335,
      "source_family": "local_external_or_vendor_cache"
    },
    {
      "absolute_path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\data\\external\\raw\\cftc_cot\\disagg_combined_20260430T234727Z.json.meta.json",
      "catalog_row_id": "LCAT-000604",
      "sha256": "1b82104908f4bc30cd662b9c8490e835781eef7a7a59eda8436283e7a695dab5",
      "size_bytes": 338,
      "source_family": "local_external_or_vendor_cache"
    },
    {
      "absolute_path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\data\\external\\raw\\cftc_cot\\disagg_combined_20260501T000733Z.json.meta.json",
      "catalog_row_id": "LCAT-000606",
      "sha256": "ed5dca0849afb9972bc11ddbb3a7daa1bed280ab04e01e7a499f6723c048f9b2",
      "size_bytes": 338,
      "source_family": "local_external_or_vendor_cache"
    },
    {
      "absolute_path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\data\\external\\raw\\databento\\GLBX.MDP3\\mbo\\GLBX.MDP3.mbo.NQ.v.0.2026-04-28T00_00_00_00_00_2026-04-28T17_00_00_00_00.full.dbn.zst.meta.json",
      "catalog_row_id": "LCAT-000607",
      "sha256": "1f6ecc901f8aa0a150ecd68737fd5a10a56dc6fcaaaf97238eae4656b62e4cee",
      "size_bytes": 667,
      "source_family": "local_external_or_vendor_cache"
    },
    {
      "absolute_path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\data\\external\\raw\\databento\\GLBX.MDP3\\mbo\\GLBX.MDP3.mbo.NQ.v.0.2026-04-29T00_00_00_00_00_2026-04-29T17_00_00_00_00.full.dbn.zst.meta.json",
      "catalog_row_id": "LCAT-000608",
      "sha256": "e56804138e835eb45b226d7b01c416826aedf4b79f3068dcffcf33c0d9c054d7",
      "size_bytes": 666,
      "source_family": "local_external_or_vendor_cache"
    },
    {
      "absolute_path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\data\\external\\raw\\databento\\GLBX.MDP3\\mbo\\GLBX.MDP3.mbo.NQ.v.0.2026-05-01T00_00_00_00_00_2026-05-01T08_15_00_00_00.full.dbn.zst.meta.json",
      "catalog_row_id": "LCAT-000609",
      "sha256": "f32a2e94dd243ae4735a63f4a87f0729303b76dcf31148458731ed47e0690277",
      "size_bytes": 664,
      "source_family": "local_external_or_vendor_cache"
    },
    {
      "absolute_path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\data\\external\\raw\\databento\\GLBX.MDP3\\mbp-1\\GLBX.MDP3.mbp-1.GC.v.0.2026-04-17T12_15_00_00_00_2026-04-17T14_30_00_00_00.full.dbn.zst.meta.json",
      "catalog_row_id": "LCAT-000610",
      "sha256": "1e813d04becf830a22d3e5633d1ddedad488c8c3b9c6a0842de8a45847d4bce5",
      "size_bytes": 669,
      "source_family": "local_external_or_vendor_cache"
    },
    {
      "absolute_path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\data\\external\\raw\\databento\\GLBX.MDP3\\mbp-1\\GLBX.MDP3.mbp-1.NQ.v.0.2026-04-28T06_15_00_00_00_2026-04-28T11_30_00_00_00.full.dbn.zst.meta.json",
      "catalog_row_id": "LCAT-000611",
      "sha256": "8e47d0a892721b944e7e64ee4a585e948fc18740ef4cce80f44bef4af00b7b84",
      "size_bytes": 670,
      "source_family": "local_external_or_vendor_cache"
    },
    {
      "absolute_path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\data\\external\\raw\\databento\\GLBX.MDP3\\mbp-1\\GLBX.MDP3.mbp-1.NQ.v.0.2026-04-28T12_15_00_00_00_2026-04-28T18_00_00_00_00.full.dbn.zst.meta.json",
      "catalog_row_id": "LCAT-000612",
      "sha256": "a5e73e42fe0230348a9f9951d40a350b0bdf0b403b0c57b8eb9b2b433419e399",
      "size_bytes": 671,
      "source_family": "local_external_or_vendor_cache"
    },
    {
      "absolute_path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\data\\external\\raw\\databento\\GLBX.MDP3\\mbp-1\\GLBX.MDP3.mbp-1.NQ.v.0.2026-04-29T12_15_00_00_00_2026-04-29T18_00_00_00_00.full.dbn.zst.meta.json",
      "catalog_row_id": "LCAT-000613",
      "sha256": "844324bde7df98c9cfeb38deafd1711bc2d3adf81ba4f46535696762518c8271",
      "size_bytes": 671,
      "source_family": "local_external_or_vendor_cache"
    },
    {
      "absolute_path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\data\\external\\raw\\databento\\GLBX.MDP3\\mbp-10\\GLBX.MDP3.mbp-10.6B.v.0.2026-04-17T06_15_00_00_00_2026-04-17T09_00_00_00_00.full.dbn.zst.meta.json",
      "catalog_row_id": "LCAT-000614",
      "sha256": "a6c934a465b148d370532d139480ddd116d052c4bd07c784c6335e7b84f40cf6",
      "size_bytes": 671,
      "source_family": "local_external_or_vendor_cache"
    },
    {
      "absolute_path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\data\\external\\raw\\databento\\GLBX.MDP3\\mbp-10\\GLBX.MDP3.mbp-10.6B.v.0.2026-04-17T07_00_00_00_00_2026-04-17T08_15_00_00_00.full.dbn.zst.meta.json",
      "catalog_row_id": "LCAT-000615",
      "sha256": "caae7f6565dc23e3667454cf47be7c55c65d24ab16e621faae8ec475ac7bfbbc",
      "size_bytes": 671,
      "source_family": "local_external_or_vendor_cache"
    },
    {
      "absolute_path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\data\\external\\raw\\databento\\GLBX.MDP3\\mbp-10\\GLBX.MDP3.mbp-10.6B.v.0.2026-04-17T09_30_00_00_00_2026-04-17T15_15_00_00_00.full.dbn.zst.meta.json",
      "catalog_row_id": "LCAT-000616",
      "sha256": "a56fcc8d4b22213816f7222b0da580fedaa3fa04953ce74371c5efe950cc0341",
      "size_bytes": 673,
      "source_family": "local_external_or_vendor_cache"
    },
    {
      "absolute_path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\data\\external\\raw\\databento\\GLBX.MDP3\\mbp-10\\GLBX.MDP3.mbp-10.6B.v.0.2026-04-17T12_30_00_00_00_2026-04-17T14_30_00_00_00.full.dbn.zst.meta.json",
      "catalog_row_id": "LCAT-000617",
      "sha256": "61ccc04c0a8dc1423c765eada28281341b9aab9470b80cf27f00e57e54ade2b9",
      "size_bytes": 673,
      "source_family": "local_external_or_vendor_cache"
    },
    {
      "absolute_path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\data\\external\\raw\\databento\\GLBX.MDP3\\mbp-10\\GLBX.MDP3.mbp-10.6B.v.0.2026-04-29T06_15_00_00_00_2026-04-29T16_30_00_00_00.full.dbn.zst.meta.json",
      "catalog_row_id": "LCAT-000618",
      "sha256": "b7990c569c38a5df301cac95c4235cb113bd6315a341c3cc0f6c488be552d5e1",
      "size_bytes": 672,
      "source_family": "local_external_or_vendor_cache"
    },
    {
      "absolute_path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\data\\external\\raw\\databento\\GLBX.MDP3\\mbp-10\\GLBX.MDP3.mbp-10.6B.v.0.2026-04-29T07_00_00_00_00_2026-04-29T08_15_00_00_00.full.dbn.zst.meta.json",
      "catalog_row_id": "LCAT-000619",
      "sha256": "42f3a16cf8bf64c20747c65aae19d9759b7e4dd03b61e69f7ae18b820c16307f",
      "size_bytes": 671,
      "source_family": "local_external_or_vendor_cache"
    },
    {
      "absolute_path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\data\\external\\raw\\databento\\GLBX.MDP3\\mbp-10\\GLBX.MDP3.mbp-10.6B.v.0.2026-04-29T09_00_00_00_00_2026-04-29T15_45_00_00_00.full.dbn.zst.meta.json",
      "catalog_row_id": "LCAT-000620",
      "sha256": "ebe0511c3da69da9e797f2b923de18566b97b4a4983c9c3a4f7e77aea6e53e58",
      "size_bytes": 673,
      "source_family": "local_external_or_vendor_cache"
    },
    {
      "absolute_path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\data\\external\\raw\\databento\\GLBX.MDP3\\mbp-10\\GLBX.MDP3.mbp-10.GC.v.0.2026-04-17T06_15_00_00_00_2026-04-17T11_30_00_00_00.full.dbn.zst.meta.json",
      "catalog_row_id": "LCAT-000621",
      "sha256": "486c7b968f5bddc98e318a93624d90ed98f5c615e1cdbe3f3198fec7a731baa8",
      "size_bytes": 673,
      "source_family": "local_external_or_vendor_cache"
    },
    {
      "absolute_path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\data\\external\\raw\\databento\\GLBX.MDP3\\mbp-10\\GLBX.MDP3.mbp-10.GC.v.0.2026-04-17T12_15_00_00_00_2026-04-17T13_45_00_00_00.full.dbn.zst.meta.json",
      "catalog_row_id": "LCAT-000622",
      "sha256": "7e8b84bd3a244848f0d587a1edb27d2c161a9efb957f9f6430967d92567bd867",
      "size_bytes": 673,
      "source_family": "local_external_or_vendor_cache"
    },
    {
      "absolute_path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\data\\external\\raw\\databento\\GLBX.MDP3\\mbp-10\\GLBX.MDP3.mbp-10.GC.v.0.2026-04-17T12_15_00_00_00_2026-04-17T14_30_00_00_00.full.dbn.zst.meta.json",
      "catalog_row_id": "LCAT-000623",
      "sha256": "16cd69d5779a510685d30d2f29af2e75cc0a8aca495494c80615edfc6988885c",
      "size_bytes": 674,
      "source_family": "local_external_or_vendor_cache"
    },
    {
      "absolute_path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\data\\external\\raw\\databento\\GLBX.MDP3\\mbp-10\\GLBX.MDP3.mbp-10.GC.v.0.2026-04-19T15_15_00_00_00_2026-04-19T18_00_00_00_00.full.dbn.zst.meta.json",
      "catalog_row_id": "LCAT-000624",
      "sha256": "8abcf69deafd24154d112a3deb0efca47167f63caf7ff7b2192263bf4579cc67",
      "size_bytes": 649,
      "source_family": "local_external_or_vendor_cache"
    },
    {
      "absolute_path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\data\\external\\raw\\databento\\GLBX.MDP3\\mbp-10\\GLBX.MDP3.mbp-10.GC.v.0.2026-05-01T07_00_00_00_00_2026-05-01T09_15_00_00_00.full.dbn.zst.meta.json",
      "catalog_row_id": "LCAT-000625",
      "sha256": "86025a68eceeb896dc1cde46bceaac980bf67eb989c92988ca094f29dfcadd7a",
      "size_bytes": 672,
      "source_family": "local_external_or_vendor_cache"
    },
    {
      "absolute_path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\data\\external\\raw\\databento\\GLBX.MDP3\\mbp-10\\GLBX.MDP3.mbp-10.GC.v.0.2026-05-01T07_15_00_00_00_2026-05-01T08_30_00_00_00.full.dbn.zst.meta.json",
      "catalog_row_id": "LCAT-000626",
      "sha256": "3a580130f66ef07d5b4d2d3fe9dd2f77eaf42f096b408fec15a30591641c8ec9",
      "size_bytes": 672,
      "source_family": "local_external_or_vendor_cache"
    },
    {
      "absolute_path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\data\\external\\raw\\databento\\GLBX.MDP3\\mbp-10\\GLBX.MDP3.mbp-10.GC.v.0.2026-05-01T13_15_00_00_00_2026-05-01T16_00_00_00_00.full.dbn.zst.meta.json",
      "catalog_row_id": "LCAT-000627",
      "sha256": "01a0f3c6b128c52073006f5db84cd5b9f727bcd9b7e07e5b69355d55210dda26",
      "size_bytes": 673,
      "source_family": "local_external_or_vendor_cache"
    },
    {
      "absolute_path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\data\\external\\raw\\databento\\GLBX.MDP3\\mbp-10\\GLBX.MDP3.mbp-10.NQ.v.0.2026-04-28T06_15_00_00_00_2026-04-28T11_30_00_00_00.full.dbn.zst.meta.json",
      "catalog_row_id": "LCAT-000628",
      "sha256": "4ab57921ad22602a5529e81457c8557be3eb2ad1431955eb238a318eaab4b82d",
      "size_bytes": 674,
      "source_family": "local_external_or_vendor_cache"
    },
    {
      "absolute_path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\data\\external\\raw\\databento\\GLBX.MDP3\\mbp-10\\GLBX.MDP3.mbp-10.NQ.v.0.2026-04-28T06_30_00_00_00_2026-04-28T10_00_00_00_00.full.dbn.zst.meta.json",
      "catalog_row_id": "LCAT-000629",
      "sha256": "1095de58a6b9635ff36b77a5b0d935d1a1f2b2d6aac92b49ad6d7aa085dd29ab",
      "size_bytes": 674,
      "source_family": "local_external_or_vendor_cache"
    },
    {
      "absolute_path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\data\\external\\raw\\databento\\GLBX.MDP3\\mbp-10\\GLBX.MDP3.mbp-10.NQ.v.0.2026-04-28T12_15_00_00_00_2026-04-28T18_00_00_00_00.full.dbn.zst.meta.json",
      "catalog_row_id": "LCAT-000630",
      "sha256": "6c16a7c92269718a7a96c20cab48475f0cc208032f4f4c1ea92d8bbe16f31e63",
      "size_bytes": 676,
      "source_family": "local_external_or_vendor_cache"
    },
    {
      "absolute_path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\data\\external\\raw\\databento\\GLBX.MDP3\\mbp-10\\GLBX.MDP3.mbp-10.NQ.v.0.2026-04-28T13_45_00_00_00_2026-04-28T15_00_00_00_00.full.dbn.zst.meta.json",
      "catalog_row_id": "LCAT-000631",
      "sha256": "47c8937649211b61029c190284fbd4b9e25aa2e26d3cac8ea2d9e40e25048124",
      "size_bytes": 675,
      "source_family": "local_external_or_vendor_cache"
    },
    {
      "absolute_path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\data\\external\\raw\\databento\\GLBX.MDP3\\mbp-10\\GLBX.MDP3.mbp-10.NQ.v.0.2026-04-29T06_15_00_00_00_2026-04-29T11_30_00_00_00.full.dbn.zst.meta.json",
      "catalog_row_id": "LCAT-000632",
      "sha256": "23ed7c04c9e8898efd14b6a12ae6b0254e797ba7fff69160fff843e6606ded06",
      "size_bytes": 674,
      "source_family": "local_external_or_vendor_cache"
    },
    {
      "absolute_path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\data\\external\\raw\\databento\\GLBX.MDP3\\mbp-10\\GLBX.MDP3.mbp-10.NQ.v.0.2026-04-29T12_15_00_00_00_2026-04-29T18_00_00_00_00.full.dbn.zst.meta.json",
      "catalog_row_id": "LCAT-000633",
      "sha256": "1c5e59d4c69270449f1a19e243bacf86e7ec3cd252820254bb5b3c40817f76c9",
      "size_bytes": 676,
      "source_family": "local_external_or_vendor_cache"
    },
    {
      "absolute_path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\data\\ticks\\README.md",
      "catalog_row_id": "LCAT-000634",
      "sha256": "5d39bfb408bb06f6a6d264ab7fa05de90a843c15f0b778841014c72591cc0e63",
      "size_bytes": 5376,
      "source_family": "mt5_tick_control_file"
    },
    {
      "absolute_path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\data\\ticks\\GBPJPY\\.state.json",
      "catalog_row_id": "LCAT-000635",
      "sha256": "9fc4968eb90482207888fc6512de918a99c4f8544c21e6e7753c8fafed52cc5c",
      "size_bytes": 175,
      "source_family": "mt5_tick_control_file"
    },
    {
      "absolute_path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\data\\ticks\\GBPJPY\\2026-04-28.parquet",
      "catalog_row_id": "LCAT-000636",
      "sha256": "5d88d8dd5522cc2811ee0be7e40a9506cb447ffb216ba895f8007d4078840e03",
      "size_bytes": 3882626,
      "source_family": "mt5_tick_parquet"
    },
    {
      "absolute_path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\data\\ticks\\GBPJPY\\2026-04-29.parquet",
      "catalog_row_id": "LCAT-000637",
      "sha256": "b5743bd709386acfaef06a985ed8cbaa2a05823ef726d903122412f9530e699a",
      "size_bytes": 4176378,
      "source_family": "mt5_tick_parquet"
    },
    {
      "absolute_path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\data\\ticks\\GBPJPY\\2026-04-30.parquet",
      "catalog_row_id": "LCAT-000638",
      "sha256": "072cf6c1fbe4d6554147b40c8dc89d4e70c0aa6941e68fc6055abd4185a4e953",
      "size_bytes": 6350848,
      "source_family": "mt5_tick_parquet"
    },
    {
      "absolute_path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\data\\ticks\\GBPJPY\\2026-05-01.parquet",
      "catalog_row_id": "LCAT-000639",
      "sha256": "b9df5a699d33f434fcb65ed85c8c54c292758e5627c1b60fbfd13e54e9a60112",
      "size_bytes": 4354929,
      "source_family": "mt5_tick_parquet"
    },
    {
      "absolute_path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\data\\ticks\\GBPJPY\\2026-05-03.parquet",
      "catalog_row_id": "LCAT-000640",
      "sha256": "98fea9903d26e966a30337a4b3070faaf1435b22fea769cdc76966594f84070c",
      "size_bytes": 145311,
      "source_family": "mt5_tick_parquet"
    },
    {
      "absolute_path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\data\\ticks\\GBPJPY\\2026-05-04.parquet",
      "catalog_row_id": "LCAT-000641",
      "sha256": "4e2d512fb980b2437e56e939b28cb6dae7a9fd4cf863536cfc59a4126da77fe1",
      "size_bytes": 4856218,
      "source_family": "mt5_tick_parquet"
    },
    {
      "absolute_path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\data\\ticks\\GBPJPY\\2026-05-05.parquet",
      "catalog_row_id": "LCAT-000642",
      "sha256": "fa2b64a91ed38e54c7a1b57683e5a7991a86db8a9c9b37a72b312e7fc39d5c02",
      "size_bytes": 3892480,
      "source_family": "mt5_tick_parquet"
    },
    {
      "absolute_path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\data\\ticks\\GBPJPY\\2026-05-06.parquet",
      "catalog_row_id": "LCAT-000643",
      "sha256": "f94cd1ba695b36c099fe50cfb926937d0af8057a5255b73fd00587b58f75fe3e",
      "size_bytes": 5377035,
      "source_family": "mt5_tick_parquet"
    },
    {
      "absolute_path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\data\\ticks\\GBPJPY\\2026-05-07.parquet",
      "catalog_row_id": "LCAT-000644",
      "sha256": "f751df902df2646cd827b949d5eef6593ef942fff3e6e29fd8b864d268a47576",
      "size_bytes": 4477088,
      "source_family": "mt5_tick_parquet"
    },
    {
      "absolute_path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\data\\ticks\\GBPJPY\\2026-05-08.parquet",
      "catalog_row_id": "LCAT-000645",
      "sha256": "36b148930a4699756ec08d0dd9b86c58c47e12c75d270366ba008999a839adc8",
      "size_bytes": 3193990,
      "source_family": "mt5_tick_parquet"
    },
    {
      "absolute_path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\data\\ticks\\GBPUSD\\.state.json",
      "catalog_row_id": "LCAT-000646",
      "sha256": "49afdfb3ee0bacf969827c3569adaeb2b53775b2240e303700cdb37398926df9",
      "size_bytes": 176,
      "source_family": "mt5_tick_control_file"
    },
    {
      "absolute_path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\data\\ticks\\GBPUSD\\2026-04-28.parquet",
      "catalog_row_id": "LCAT-000647",
      "sha256": "a07590a474ff878894f4193ef146adb2287b9c54c752bc9d5324a750d65b5d8c",
      "size_bytes": 2638946,
      "source_family": "mt5_tick_parquet"
    },
    {
      "absolute_path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\data\\ticks\\GBPUSD\\2026-04-29.parquet",
      "catalog_row_id": "LCAT-000648",
      "sha256": "2826714cd35678979c088f37af609b58fb51f024ac9c3ad40213bfc01268fb83",
      "size_bytes": 2811846,
      "source_family": "mt5_tick_parquet"
    },
    {
      "absolute_path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\data\\ticks\\GBPUSD\\2026-04-30.parquet",
      "catalog_row_id": "LCAT-000649",
      "sha256": "0b96cac6286cf60b40f855a368ad15be6d591d52c59075669f41f458dd1965d5",
      "size_bytes": 3926086,
      "source_family": "mt5_tick_parquet"
    },
    {
      "absolute_path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\data\\ticks\\GBPUSD\\2026-05-01.parquet",
      "catalog_row_id": "LCAT-000650",
      "sha256": "54acfb5661213e2bc2820a35668c9100f3c81274ede725bf15a46e649eb1937b",
      "size_bytes": 2680981,
      "source_family": "mt5_tick_parquet"
    },
    {
      "absolute_path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\data\\ticks\\GBPUSD\\2026-05-03.parquet",
      "catalog_row_id": "LCAT-000651",
      "sha256": "41a55e9e5c472a74222d994cd2a514c17da38e0330ee7b645fad84a0174a090e",
      "size_bytes": 70932,
      "source_family": "mt5_tick_parquet"
    },
    {
      "absolute_path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\data\\ticks\\GBPUSD\\2026-05-04.parquet",
      "catalog_row_id": "LCAT-000652",
      "sha256": "e53ce9b0e348f58afa17257c292d88e32162147cfba7054b90240c218fd653d7",
      "size_bytes": 3059442,
      "source_family": "mt5_tick_parquet"
    },
    {
      "absolute_path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\data\\ticks\\GBPUSD\\2026-05-05.parquet",
      "catalog_row_id": "LCAT-000653",
      "sha256": "27f383d3d19247d0dd0d96a2c52dedf2c9460e2274250ef9ce5595006430897c",
      "size_bytes": 2664822,
      "source_family": "mt5_tick_parquet"
    },
    {
      "absolute_path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\data\\ticks\\GBPUSD\\2026-05-06.parquet",
      "catalog_row_id": "LCAT-000654",
      "sha256": "55b7b9f7273f80d56b480a5c48979b61ea19974fc7fcded6435f7677ab135233",
      "size_bytes": 3262893,
      "source_family": "mt5_tick_parquet"
    },
    {
      "absolute_path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\data\\ticks\\GBPUSD\\2026-05-07.parquet",
      "catalog_row_id": "LCAT-000655",
      "sha256": "377357096e4baa3946d6de7ead974846fee2f179afff1851ceabce6755adbcb7",
      "size_bytes": 3037698,
      "source_family": "mt5_tick_parquet"
    },
    {
      "absolute_path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\data\\ticks\\GBPUSD\\2026-05-08.parquet",
      "catalog_row_id": "LCAT-000656",
      "sha256": "6407ab7826d04a88a0bb884154287fc8fec6eda9c115de5f3bbd0358cb2e52d1",
      "size_bytes": 2336361,
      "source_family": "mt5_tick_parquet"
    },
    {
      "absolute_path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\data\\ticks\\NAS100\\.state.json",
      "catalog_row_id": "LCAT-000657",
      "sha256": "83c6f8c46a60ca6a41d8df6193e46a0f6fe323b4c324db991f1b71eda472b95b",
      "size_bytes": 177,
      "source_family": "mt5_tick_control_file"
    },
    {
      "absolute_path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\data\\ticks\\NAS100\\2026-05-03.parquet",
      "catalog_row_id": "LCAT-000663",
      "sha256": "41996c1de550993f124120b821d9495c0ffde06d5c0c04b36676a2112766e208",
      "size_bytes": 649819,
      "source_family": "mt5_tick_parquet"
    },
    {
      "absolute_path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\data\\ticks\\US30_cash\\.state.json",
      "catalog_row_id": "LCAT-000669",
      "sha256": "4ef6fd9a5d165ea4a37662afd3b9616c62b3cb07be75157ba9a9c6d30b5d7be5",
      "size_bytes": 178,
      "source_family": "mt5_tick_control_file"
    },
    {
      "absolute_path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\data\\ticks\\US30_cash\\2026-04-27.parquet",
      "catalog_row_id": "LCAT-000670",
      "sha256": "0094c8fad341d46f95eb03059bad3c461962b838229e80507146fc4814c3a0a1",
      "size_bytes": 3006706,
      "source_family": "mt5_tick_parquet"
    },
    {
      "absolute_path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\data\\ticks\\US30_cash\\2026-04-28.parquet",
      "catalog_row_id": "LCAT-000671",
      "sha256": "bc108446336a02abcfe44f42623ab55ef6ba35d5fcb0b47377ab74dc0b2552ab",
      "size_bytes": 4000945,
      "source_family": "mt5_tick_parquet"
    },
    {
      "absolute_path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\data\\ticks\\US30_cash\\2026-04-29.parquet",
      "catalog_row_id": "LCAT-000672",
      "sha256": "3705b44cc7f98ba93d5190605a831f7b511a339e9a0773a8286d1e35ff7848d6",
      "size_bytes": 4270230,
      "source_family": "mt5_tick_parquet"
    },
    {
      "absolute_path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\data\\ticks\\US30_cash\\2026-04-30.parquet",
      "catalog_row_id": "LCAT-000673",
      "sha256": "9c9b7af82710ad5bd6fd01671df3361bbe26951349f1c56af018fa108509169c",
      "size_bytes": 4021074,
      "source_family": "mt5_tick_parquet"
    },
    {
      "absolute_path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\data\\ticks\\US30_cash\\2026-05-01.parquet",
      "catalog_row_id": "LCAT-000674",
      "sha256": "393c13260cff952dd63609e9e2371ca7d39810ded73a001c8b7a344c94fcb658",
      "size_bytes": 2987584,
      "source_family": "mt5_tick_parquet"
    },
    {
      "absolute_path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\data\\ticks\\US30_cash\\2026-05-03.parquet",
      "catalog_row_id": "LCAT-000675",
      "sha256": "8e74ba26952a91cbff3762abeae3fc93a2b81066607de4df9850ce7bfdc98c42",
      "size_bytes": 91467,
      "source_family": "mt5_tick_parquet"
    },
    {
      "absolute_path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\data\\ticks\\US30_cash\\2026-05-04.parquet",
      "catalog_row_id": "LCAT-000676",
      "sha256": "2ecfe1c8dcc9577854c124943dea26127d1476dc916f93aceb83674a0c610f5e",
      "size_bytes": 4216308,
      "source_family": "mt5_tick_parquet"
    },
    {
      "absolute_path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\data\\ticks\\US30_cash\\2026-05-05.parquet",
      "catalog_row_id": "LCAT-000677",
      "sha256": "41e8f26d7a7c7390b2d66801141e9543134a6bc68de3d6fa2b2560fe14235731",
      "size_bytes": 2955639,
      "source_family": "mt5_tick_parquet"
    },
    {
      "absolute_path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\data\\ticks\\US30_cash\\2026-05-06.parquet",
      "catalog_row_id": "LCAT-000678",
      "sha256": "eb90e21f12aef7564a6f2995fc8a051eb27a61057326e3c5ccf4b5c3132f69fb",
      "size_bytes": 3945958,
      "source_family": "mt5_tick_parquet"
    },
    {
      "absolute_path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\data\\ticks\\US30_cash\\2026-05-07.parquet",
      "catalog_row_id": "LCAT-000679",
      "sha256": "2b4f929d4e168bd171a3e698d17bdf7324110dfd06ae67b9583c2f335eab5c5e",
      "size_bytes": 4392715,
      "source_family": "mt5_tick_parquet"
    },
    {
      "absolute_path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\data\\ticks\\US30_cash\\2026-05-08.parquet",
      "catalog_row_id": "LCAT-000680",
      "sha256": "bfed917d099ba990458319e4c607e405e3a53de458be13d9dc893be011fc4cd6",
      "size_bytes": 2608082,
      "source_family": "mt5_tick_parquet"
    },
    {
      "absolute_path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\data\\ticks\\USDJPY\\.state.json",
      "catalog_row_id": "LCAT-000681",
      "sha256": "9abffcfcead0d1f9b103c14dc2e0aebd75f889979ecf9f540af0f16601ec66dc",
      "size_bytes": 175,
      "source_family": "mt5_tick_control_file"
    },
    {
      "absolute_path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\data\\ticks\\USDJPY\\2026-04-28.parquet",
      "catalog_row_id": "LCAT-000682",
      "sha256": "773425a07596ee476feb3d53a68884878835b32d62fa0225a5f32d6ae937369c",
      "size_bytes": 2092028,
      "source_family": "mt5_tick_parquet"
    },
    {
      "absolute_path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\data\\ticks\\USDJPY\\2026-04-29.parquet",
      "catalog_row_id": "LCAT-000683",
      "sha256": "8a1cdbc8276c119eb48f3e5931d3343103e985ac5f7154c6147d1035e50211c9",
      "size_bytes": 2296748,
      "source_family": "mt5_tick_parquet"
    },
    {
      "absolute_path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\data\\ticks\\USDJPY\\2026-04-30.parquet",
      "catalog_row_id": "LCAT-000684",
      "sha256": "a48099563df87d2b2654ccae9c235917024dbbf32817eed5997880d15c544bce",
      "size_bytes": 3908592,
      "source_family": "mt5_tick_parquet"
    },
    {
      "absolute_path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\data\\ticks\\USDJPY\\2026-05-01.parquet",
      "catalog_row_id": "LCAT-000685",
      "sha256": "7d13dd73d30a2fb5964b14e688d9aa9a4425828f6901067c1f04e36321430456",
      "size_bytes": 2768379,
      "source_family": "mt5_tick_parquet"
    },
    {
      "absolute_path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\data\\ticks\\USDJPY\\2026-05-03.parquet",
      "catalog_row_id": "LCAT-000686",
      "sha256": "d57a351952233e8e6e5e64c473a6f50c84f779139e6099f29068756686a119a4",
      "size_bytes": 85195,
      "source_family": "mt5_tick_parquet"
    },
    {
      "absolute_path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\data\\ticks\\USDJPY\\2026-05-04.parquet",
      "catalog_row_id": "LCAT-000687",
      "sha256": "424c3d9ee4279fd8c258b061f335a25b32b74e88dab8f71abb12016126f50338",
      "size_bytes": 2766553,
      "source_family": "mt5_tick_parquet"
    },
    {
      "absolute_path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\data\\ticks\\USDJPY\\2026-05-05.parquet",
      "catalog_row_id": "LCAT-000688",
      "sha256": "7316926c90065e3f0d8c3c8b49d38544a82dd82cc0536cc35d415e93c82dad76",
      "size_bytes": 1934862,
      "source_family": "mt5_tick_parquet"
    },
    {
      "absolute_path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\data\\ticks\\USDJPY\\2026-05-06.parquet",
      "catalog_row_id": "LCAT-000689",
      "sha256": "b00d0d06697b1da4c2f2f14f63dd4730fd4ad6d9ce331199a1975b7744d9114d",
      "size_bytes": 3269873,
      "source_family": "mt5_tick_parquet"
    },
    {
      "absolute_path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\data\\ticks\\USDJPY\\2026-05-07.parquet",
      "catalog_row_id": "LCAT-000690",
      "sha256": "35e8dfbf40c65e5b3600ba9a0bc6957283a2f52e2bace10f3b6daf6d0dc0773c",
      "size_bytes": 2351787,
      "source_family": "mt5_tick_parquet"
    },
    {
      "absolute_path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\data\\ticks\\USDJPY\\2026-05-08.parquet",
      "catalog_row_id": "LCAT-000691",
      "sha256": "6da61afc29cddac966b94fa9498e03b19a3ab4ad51ffbc7f88cd4a93b81a2035",
      "size_bytes": 1467416,
      "source_family": "mt5_tick_parquet"
    },
    {
      "absolute_path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\data\\ticks\\XAGUSD\\.state.json",
      "catalog_row_id": "LCAT-000692",
      "sha256": "739d258dfc1df09306ea16452adc79d0ab267e3942cb78edee224e33add65661",
      "size_bytes": 185,
      "source_family": "mt5_tick_control_file"
    },
    {
      "absolute_path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\data\\ticks\\XAGUSD\\2026-04-28.parquet",
      "catalog_row_id": "LCAT-000693",
      "sha256": "7bb5d77fc85d9c8d249f3687ee978290cdf8fcfdadd6cbbf6b4331e308f35165",
      "size_bytes": 3665217,
      "source_family": "mt5_tick_parquet"
    },
    {
      "absolute_path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\data\\ticks\\XAGUSD\\2026-04-29.parquet",
      "catalog_row_id": "LCAT-000694",
      "sha256": "b7e59e9bdf81a9e8c2208c5a8dba7865f41ddeef8940db390279f2a249d9703d",
      "size_bytes": 3726586,
      "source_family": "mt5_tick_parquet"
    },
    {
      "absolute_path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\data\\ticks\\XAGUSD\\2026-04-30.parquet",
      "catalog_row_id": "LCAT-000695",
      "sha256": "10681eda541456addd6297317620fd2723e6beb20b8752661314b148aa17c7a8",
      "size_bytes": 3737748,
      "source_family": "mt5_tick_parquet"
    },
    {
      "absolute_path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\data\\ticks\\XAGUSD\\2026-05-01.parquet",
      "catalog_row_id": "LCAT-000696",
      "sha256": "e980bdafeaa5b8a6e8baad0efaf3b812a4966e0b7b225135f2e50b5bef67b31d",
      "size_bytes": 2847558,
      "source_family": "mt5_tick_parquet"
    },
    {
      "absolute_path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\data\\ticks\\XAGUSD\\2026-05-03.parquet",
      "catalog_row_id": "LCAT-000697",
      "sha256": "a69a16b6f9f0ed379e2b8be11b67cddbf0abd447b495cfd801c962a1d08f6e05",
      "size_bytes": 232959,
      "source_family": "mt5_tick_parquet"
    },
    {
      "absolute_path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\data\\ticks\\XAGUSD\\2026-05-04.parquet",
      "catalog_row_id": "LCAT-000698",
      "sha256": "fe80b36da79fe2491eb488c77d20f4e734435752715228e1199f7f76055a7868",
      "size_bytes": 3589112,
      "source_family": "mt5_tick_parquet"
    },
    {
      "absolute_path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\data\\ticks\\XAGUSD\\2026-05-05.parquet",
      "catalog_row_id": "LCAT-000699",
      "sha256": "ad451c922db79a8643e32b7b9c5f55e6d5cd417834ef0fbf5b20b5799d004237",
      "size_bytes": 2892270,
      "source_family": "mt5_tick_parquet"
    },
    {
      "absolute_path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\data\\ticks\\XAGUSD\\2026-05-06.parquet",
      "catalog_row_id": "LCAT-000700",
      "sha256": "c824a97a603940424ad43dc1a1263ae998053b5df262d3c3ab53dd83ccdab36e",
      "size_bytes": 3842206,
      "source_family": "mt5_tick_parquet"
    },
    {
      "absolute_path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\data\\ticks\\XAGUSD\\2026-05-07.parquet",
      "catalog_row_id": "LCAT-000701",
      "sha256": "8ebddb40495ed226d54552e186d9db4f3615ee98042aa3a187f6de3ba4006a0a",
      "size_bytes": 4146287,
      "source_family": "mt5_tick_parquet"
    },
    {
      "absolute_path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\data\\ticks\\XAGUSD\\2026-05-08.parquet",
      "catalog_row_id": "LCAT-000702",
      "sha256": "c71cda79751781fa126e8cd1fd39c7fc1b72288ab286c449963b1e5fd93689af",
      "size_bytes": 3317773,
      "source_family": "mt5_tick_parquet"
    },
    {
      "absolute_path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\data\\ticks\\XAUUSD\\.state.json",
      "catalog_row_id": "LCAT-000703",
      "sha256": "9c8a1ebaad3bbdfc4ee7a1ee44c34cea53981a242e48c281bffe7efd2101b92a",
      "size_bytes": 186,
      "source_family": "mt5_tick_control_file"
    },
    {
      "absolute_path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\data\\ticks\\XAUUSD\\2026-05-01.parquet",
      "catalog_row_id": "LCAT-000707",
      "sha256": "ed0773d4ded22a853c0aa40d6ee5503d37fb27f95c5958977ef129c82a837ae0",
      "size_bytes": 7322672,
      "source_family": "mt5_tick_parquet"
    },
    {
      "absolute_path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\data\\ticks\\XAUUSD\\2026-05-03.parquet",
      "catalog_row_id": "LCAT-000708",
      "sha256": "0911ab624dc038992e3f3ac5d7c5e70bc9bcc498cf61c1388035f795b599a6f3",
      "size_bytes": 664233,
      "source_family": "mt5_tick_parquet"
    },
    {
      "absolute_path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\data\\ticks\\XAUUSD\\2026-05-05.parquet",
      "catalog_row_id": "LCAT-000710",
      "sha256": "9a361078f8448d8d69aacbf3905d38d291282ce223d269fe033b0e6eb9814a0f",
      "size_bytes": 6788510,
      "source_family": "mt5_tick_parquet"
    },
    {
      "absolute_path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\data\\ticks\\XAUUSD\\2026-05-06.parquet",
      "catalog_row_id": "LCAT-000711",
      "sha256": "fdec881196886808c90aa25d6a91d99c5f1105274ecbd435e442f63bcac59439",
      "size_bytes": 1883513,
      "source_family": "mt5_tick_parquet"
    },
    {
      "absolute_path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\data\\ticks\\XAUUSD\\2026-05-08.parquet",
      "catalog_row_id": "LCAT-000713",
      "sha256": "12d52f0b1773433dc9e91efbb617b840de649675de083dad6e8d7c848610b30a",
      "size_bytes": 7351114,
      "source_family": "mt5_tick_parquet"
    },
    {
      "absolute_path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\shadow_logs\\.d1_bias_lag_state.json",
      "catalog_row_id": "LCAT-000714",
      "sha256": "07210a70d4dff1d4e22aa37f9f6678e57d2eb782c4ddd77608170a390dd3b028",
      "size_bytes": 516,
      "source_family": "shadow_log_source_control"
    },
    {
      "absolute_path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\shadow_logs\\.displacement_state.json",
      "catalog_row_id": "LCAT-000715",
      "sha256": "ae09cd93ca5b90ee5bbe14d77a338f3df4565d77a0e29af4b40818337abc4cf4",
      "size_bytes": 163,
      "source_family": "shadow_log_source_control"
    },
    {
      "absolute_path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\shadow_logs\\.dumb_baseline_state.GBPJPY.json",
      "catalog_row_id": "LCAT-000716",
      "sha256": "43e55f72da45b4b30e2c37b6c08e9bf5a3f0a76733028494d3e30efb10c6e6fd",
      "size_bytes": 84,
      "source_family": "shadow_log_source_control"
    },
    {
      "absolute_path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\shadow_logs\\.dumb_baseline_state.GBPUSD.json",
      "catalog_row_id": "LCAT-000717",
      "sha256": "1d2592cab8a8f1269cc8eeebbdaea23b89a0bb7b791a84bc43c3f4a263213b17",
      "size_bytes": 84,
      "source_family": "shadow_log_source_control"
    },
    {
      "absolute_path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\shadow_logs\\.dumb_baseline_state.NAS100.json",
      "catalog_row_id": "LCAT-000718",
      "sha256": "b081f4608fe993f461816f3f34e20b3527f0a8729d488695b45685a4d5031e88",
      "size_bytes": 84,
      "source_family": "shadow_log_source_control"
    },
    {
      "absolute_path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\shadow_logs\\.dumb_baseline_state.US30_cash.json",
      "catalog_row_id": "LCAT-000719",
      "sha256": "9fb5bc79a180a23ca7d6b044d00ce551c9aa68a02db100c16effe106a43edb80",
      "size_bytes": 84,
      "source_family": "shadow_log_source_control"
    },
    {
      "absolute_path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\shadow_logs\\.dumb_baseline_state.USDJPY.json",
      "catalog_row_id": "LCAT-000720",
      "sha256": "c9f8d0e2df5577775e3d7f3c694fbdadf0fcb3f3b0d19c0a2d4e09e83882d7a0",
      "size_bytes": 84,
      "source_family": "shadow_log_source_control"
    },
    {
      "absolute_path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\shadow_logs\\.dumb_baseline_state.XAGUSD.json",
      "catalog_row_id": "LCAT-000721",
      "sha256": "21d142523aacf7395a825a8f09448ed498238cec1385334cc7c7c720f98dc1be",
      "size_bytes": 74,
      "source_family": "shadow_log_source_control"
    },
    {
      "absolute_path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\shadow_logs\\.dumb_baseline_state.XAUUSD.json",
      "catalog_row_id": "LCAT-000722",
      "sha256": "feac62bd6d5a77d778b4e0ce7035f59fd4fac2b3057f545ec21fd9b6a0d1a1ba",
      "size_bytes": 798,
      "source_family": "shadow_log_source_control"
    },
    {
      "absolute_path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\shadow_logs\\.dumb_baseline_state.json",
      "catalog_row_id": "LCAT-000723",
      "sha256": "b9d66d778751cdcbaabc361a15f0a28314c28b6b5f9bc70253acc2e0f1fc5219",
      "size_bytes": 1364,
      "source_family": "shadow_log_source_control"
    },
    {
      "absolute_path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\shadow_logs\\canary_restart_governance_status.jsonl",
      "catalog_row_id": "LCAT-000724",
      "sha256": "e4ec1f07030444ffe6983e36432c9fead5102b4bdd66b656abd848581e137eeb",
      "size_bytes": 8453,
      "source_family": "shadow_log_source_control"
    },
    {
      "absolute_path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\shadow_logs\\candidate_mso_snapshot_joins.jsonl",
      "catalog_row_id": "LCAT-000727",
      "sha256": "205cb1a95eace166d57a337025cd2e503a1880bb7d703bfa4858e4c51917e9e7",
      "size_bytes": 250212,
      "source_family": "shadow_log_source_control"
    },
    {
      "absolute_path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\shadow_logs\\candidate_path_contract_audit.jsonl",
      "catalog_row_id": "LCAT-000728",
      "sha256": "a57f61333dafeaf73a841784ea1927b05860198a0ac6edeed08f3844a34d239f",
      "size_bytes": 5172490,
      "source_family": "shadow_log_source_control"
    },
    {
      "absolute_path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\shadow_logs\\candidate_registry_audit.jsonl",
      "catalog_row_id": "LCAT-000730",
      "sha256": "1183d41f8af0914d1d398c1bda2d1cf6b9147f88c0c24e10a178a9697d78b5b0",
      "size_bytes": 439794,
      "source_family": "shadow_log_source_control"
    },
    {
      "absolute_path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\shadow_logs\\context_control_ledger.jsonl",
      "catalog_row_id": "LCAT-000732",
      "sha256": "9df7b5a3190c5eaddf0463f0a20d00151e3559342a630cb95844267c3cf69ecd",
      "size_bytes": 683478,
      "source_family": "shadow_log_source_control"
    },
    {
      "absolute_path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\shadow_logs\\continuation_no_retrace_candidates.jsonl",
      "catalog_row_id": "LCAT-000733",
      "sha256": "6e0638b56a6ee70629dacd7bae94aefab249ef7c7232c6c3dc5bd0c3818d22bb",
      "size_bytes": 162403,
      "source_family": "shadow_log_source_control"
    },
    {
      "absolute_path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\shadow_logs\\continuation_no_retrace_resolutions.jsonl",
      "catalog_row_id": "LCAT-000734",
      "sha256": "026257a77b6a0918424b711a7c9c40c46c778eba72fe21b5bcfad9e7069540f7",
      "size_bytes": 481204,
      "source_family": "shadow_log_source_control"
    },
    {
      "absolute_path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\shadow_logs\\cusum_candidate_rate_daily.csv",
      "catalog_row_id": "LCAT-000735",
      "sha256": "d1fdb1734e745e25e154d75881df7a2a22bdfb3e8b294e19940899ef97dc6795",
      "size_bytes": 1449,
      "source_family": "shadow_log_source_control"
    },
    {
      "absolute_path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\shadow_logs\\d1_bias_lag.jsonl",
      "catalog_row_id": "LCAT-000736",
      "sha256": "ef4db1499b39010345eb70f122319d77f462c95a8125921638b6a1cea6580521",
      "size_bytes": 112900,
      "source_family": "shadow_log_source_control"
    },
    {
      "absolute_path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\shadow_logs\\d1_bias_lag_recovery.jsonl",
      "catalog_row_id": "LCAT-000737",
      "sha256": "daad9f5c9c7c7d4cff83b648988424bc135962993b091218cf99c6fc9bfc0bc1",
      "size_bytes": 9352,
      "source_family": "shadow_log_source_control"
    },
    {
      "absolute_path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\shadow_logs\\databento_live_budget_ledger.jsonl",
      "catalog_row_id": "LCAT-000738",
      "sha256": "27c560f3efd1090ec6924229430a990263f8d96129e58bfe84367e0ed80cf1a5",
      "size_bytes": 4581,
      "source_family": "shadow_log_source_control"
    },
    {
      "absolute_path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\shadow_logs\\databento_live_confluence.jsonl",
      "catalog_row_id": "LCAT-000739",
      "sha256": "001fd5fdf3b20d28e2a1fe4577f7ff550bd74fa0cf77b6bcd7199ff139a9fd86",
      "size_bytes": 12682,
      "source_family": "shadow_log_source_control"
    },
    {
      "absolute_path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\shadow_logs\\databento_live_trigger_decisions.jsonl",
      "catalog_row_id": "LCAT-000740",
      "sha256": "c756c7f5b304be84cf9dbc0fb476f2a5db2eb22226e030a5c1b8ddd68e945fc5",
      "size_bytes": 332195,
      "source_family": "shadow_log_source_control"
    },
    {
      "absolute_path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\shadow_logs\\decision_layer_diagnostics_join.jsonl",
      "catalog_row_id": "LCAT-000741",
      "sha256": "fdd555da8d593d27312119a5ce0726c86c41df2353252e7dc4348a547e0b4c82",
      "size_bytes": 1227750,
      "source_family": "shadow_log_source_control"
    },
    {
      "absolute_path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\shadow_logs\\direction_emission_xau_audit.jsonl",
      "catalog_row_id": "LCAT-000742",
      "sha256": "967fdff0ae7b741e8f1d0e8a0d6b8edf5d718312b0f9d1011338d26c0ab98879",
      "size_bytes": 102182,
      "source_family": "shadow_log_source_control"
    },
    {
      "absolute_path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\shadow_logs\\displacement_events.jsonl",
      "catalog_row_id": "LCAT-000743",
      "sha256": "d77803f48d602a6e12f32eaa03cfc78121231403d4625969c5250e1f104abf7b",
      "size_bytes": 55730,
      "source_family": "shadow_log_source_control"
    },
    {
      "absolute_path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\shadow_logs\\drawdown_state_changes.jsonl",
      "catalog_row_id": "LCAT-000744",
      "sha256": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
      "size_bytes": 0,
      "source_family": "shadow_log_source_control"
    },
    {
      "absolute_path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\shadow_logs\\dumb_baseline_hypotheticals.jsonl",
      "catalog_row_id": "LCAT-000745",
      "sha256": "fd2cb9ee1876942b40e5b7648fd0b109f1e42fb3f0f7cddeb1eb7b15000b0662",
      "size_bytes": 11987,
      "source_family": "shadow_log_source_control"
    },
    {
      "absolute_path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\shadow_logs\\equity_read_anomalies.jsonl",
      "catalog_row_id": "LCAT-000746",
      "sha256": "0e6809452a3bfd8ab26c1fc01975fe997b01e8cbab6bef6c7e535ee75e08bd67",
      "size_bytes": 10646,
      "source_family": "shadow_log_source_control"
    },
    {
      "absolute_path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\shadow_logs\\es_mes_preregistration_status.jsonl",
      "catalog_row_id": "LCAT-000747",
      "sha256": "ac1535dc783ef18500c0779e84434f1ca17063c1109a63218294a44cb1cbca1e",
      "size_bytes": 32568,
      "source_family": "shadow_log_source_control"
    },
    {
      "absolute_path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\shadow_logs\\exit_management_shadow_status.jsonl",
      "catalog_row_id": "LCAT-000748",
      "sha256": "5ad9ef49b75ff90d2ef32cd1fec581543c74256fbb0a88a8745f1d38ce854f5c",
      "size_bytes": 806533,
      "source_family": "shadow_log_source_control"
    },
    {
      "absolute_path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\shadow_logs\\expired_poi_revalidation.jsonl",
      "catalog_row_id": "LCAT-000749",
      "sha256": "a013f9a988a2634ef4b05738cfc58738cb815709a4413a8181e0ff1a4aa1f3a8",
      "size_bytes": 5180,
      "source_family": "shadow_log_source_control"
    },
    {
      "absolute_path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\shadow_logs\\external_source_blocker_status.jsonl",
      "catalog_row_id": "LCAT-000750",
      "sha256": "e9e9721bafe950d449515f3008554426c36978ecc4240da473e51d2c7ffdd723",
      "size_bytes": 829764,
      "source_family": "shadow_log_source_control"
    },
    {
      "absolute_path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\shadow_logs\\fn_smoke_20260420_084920.json",
      "catalog_row_id": "LCAT-000751",
      "sha256": "335de55f9bd5db047e54a88b56430eeb533f2932e86455212ea4694eeb371f46",
      "size_bytes": 2329,
      "source_family": "shadow_log_source_control"
    },
    {
      "absolute_path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\shadow_logs\\fn_smoke_20260420_085002.json",
      "catalog_row_id": "LCAT-000752",
      "sha256": "d2ac7f8c5d2a8733f8f498601c7c4ce821f9ee21519e057fc31d660dbbfc41eb",
      "size_bytes": 2435,
      "source_family": "shadow_log_source_control"
    },
    {
      "absolute_path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\shadow_logs\\fn_smoke_20260420_091430.json",
      "catalog_row_id": "LCAT-000753",
      "sha256": "2786a231a17f054550283273d449bf2cf0218594fa78c6fa08431f95192135a4",
      "size_bytes": 2455,
      "source_family": "shadow_log_source_control"
    },
    {
      "absolute_path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\shadow_logs\\fn_smoke_20260420_091722.json",
      "catalog_row_id": "LCAT-000754",
      "sha256": "1f2667f75d340718eba7ab98d3676aa65bed24b85494903e0dfe0c5ac9b117b7",
      "size_bytes": 2455,
      "source_family": "shadow_log_source_control"
    },
    {
      "absolute_path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\shadow_logs\\fn_smoke_20260420_092228.json",
      "catalog_row_id": "LCAT-000755",
      "sha256": "c0148f9cb344482ac2ae8834253315cf09d52512b862e40d68ad53e62f921def",
      "size_bytes": 3359,
      "source_family": "shadow_log_source_control"
    },
    {
      "absolute_path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\shadow_logs\\fn_smoke_20260420_093645.json",
      "catalog_row_id": "LCAT-000756",
      "sha256": "63303d2b0bf41548fa4cf23fbd1083821b766bf2d219546c63a91f46e95f9b53",
      "size_bytes": 2487,
      "source_family": "shadow_log_source_control"
    },
    {
      "absolute_path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\shadow_logs\\fn_smoke_20260420_094825.json",
      "catalog_row_id": "LCAT-000757",
      "sha256": "775b52c06552ec75687bca48fe22a4857adfe99c929ac4ea2a9e8e8c59e10c1d",
      "size_bytes": 3400,
      "source_family": "shadow_log_source_control"
    },
    {
      "absolute_path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\shadow_logs\\fn_smoke_20260427_084407.json",
      "catalog_row_id": "LCAT-000758",
      "sha256": "dbad7414e6393de8d7873674ca4f2b71cdffb70b50a7dfc24147225e23236651",
      "size_bytes": 3463,
      "source_family": "shadow_log_source_control"
    },
    {
      "absolute_path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\shadow_logs\\fn_smoke_20260427_084506.json",
      "catalog_row_id": "LCAT-000759",
      "sha256": "76fd5051bd2e2758db36ccdc3e86abb41ea70f456c37bbad84b63507fc89c140",
      "size_bytes": 4693,
      "source_family": "shadow_log_source_control"
    },
    {
      "absolute_path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\shadow_logs\\fvg_ob_confluence.jsonl",
      "catalog_row_id": "LCAT-000760",
      "sha256": "d0a8b7f1f5f1df3344cfee9ba9cd5b7371792236d9c184aaf800df63ea55206b",
      "size_bytes": 250834,
      "source_family": "shadow_log_source_control"
    },
    {
      "absolute_path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\shadow_logs\\gbpjpy_proxy_gap_status.jsonl",
      "catalog_row_id": "LCAT-000763",
      "sha256": "3d11e6363414d035704e6bca87a672259e8fc8197f33b9e4b6465f64328fe0c5",
      "size_bytes": 28944,
      "source_family": "shadow_log_source_control"
    },
    {
      "absolute_path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\shadow_logs\\heartbeat_flatten_events.jsonl",
      "catalog_row_id": "LCAT-000764",
      "sha256": "f71fc4d03f426f01b7f9c86cf11b6a206f44357f98fdcac9358bea3a8e38e807",
      "size_bytes": 199300,
      "source_family": "shadow_log_source_control"
    },
    {
      "absolute_path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\shadow_logs\\heartbeat_throttle_state.json",
      "catalog_row_id": "LCAT-000765",
      "sha256": "4feb33258d5c2c9cb2fbee5c34fbef721e4234dcf4dbd0facd719946b62f55af",
      "size_bytes": 54,
      "source_family": "shadow_log_source_control"
    },
    {
      "absolute_path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\shadow_logs\\j46_j49_exit_comparator_audit.jsonl",
      "catalog_row_id": "LCAT-000766",
      "sha256": "812a6aae9415d7d3a7d511873219af3028d01e32691932ef997c5fdb5e0c0e83",
      "size_bytes": 7813705,
      "source_family": "shadow_log_source_control"
    },
    {
      "absolute_path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\shadow_logs\\j46_j49_shadow_outcomes.jsonl",
      "catalog_row_id": "LCAT-000767",
      "sha256": "21ae7b923daccc769d2da04fb97480df5a6d7bb03ebd1763cb57f5c9c655845f",
      "size_bytes": 2360,
      "source_family": "shadow_log_source_control"
    },
    {
      "absolute_path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\shadow_logs\\j46_j49_shadow_outcomes.pretty.json",
      "catalog_row_id": "LCAT-000768",
      "sha256": "e89a3b94a4bd2461fdc1b6c78a3de65339889cec4fc8ab5f14d6231b13cf031b",
      "size_bytes": 970,
      "source_family": "shadow_log_source_control"
    },
    {
      "absolute_path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\shadow_logs\\liquidity_distance_log.jsonl",
      "catalog_row_id": "LCAT-000769",
      "sha256": "86c423334efce8ebfd15d0622ff1ace7c3db9d4fc6d067c0cae53ba04438cfbc",
      "size_bytes": 217361,
      "source_family": "shadow_log_source_control"
    },
    {
      "absolute_path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\shadow_logs\\live_mechanical_strategy_shadow_outcomes.jsonl",
      "catalog_row_id": "LCAT-000772",
      "sha256": "f8559222ea79430d375088a0be4f4c8518e7096cff7fc9cb2fb8c1333104cf17",
      "size_bytes": 134,
      "source_family": "shadow_log_source_control"
    },
    {
      "absolute_path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\shadow_logs\\live_monitor.jsonl",
      "catalog_row_id": "LCAT-000773",
      "sha256": "494ac2d093185e693de0793c00ac9c78773f240409db2efac451fbe08a91f048",
      "size_bytes": 3427078,
      "source_family": "shadow_log_source_control"
    },
    {
      "absolute_path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\shadow_logs\\live_monitor_alerts.jsonl",
      "catalog_row_id": "LCAT-000774",
      "sha256": "cca4163fc610b17a440ca96a8dfb5ca96d4907657ff44f2f5545aadd50cdfd99",
      "size_bytes": 29556,
      "source_family": "shadow_log_source_control"
    },
    {
      "absolute_path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\shadow_logs\\live_monitoring_maintenance_runs.jsonl",
      "catalog_row_id": "LCAT-000775",
      "sha256": "405b79e64312179ba27e439b4376a4c20e9404d7db3dc05c3148a8dd339030b3",
      "size_bytes": 2224863,
      "source_family": "shadow_log_source_control"
    },
    {
      "absolute_path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\shadow_logs\\lto_blocked_lane_status.jsonl",
      "catalog_row_id": "LCAT-000777",
      "sha256": "33878d39260f454ca733387f38cfe710e16e7768cea142d7a68efbf6f9dee4f5",
      "size_bytes": 2372,
      "source_family": "shadow_log_source_control"
    },
    {
      "absolute_path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\shadow_logs\\m15_choch_diagnostic_audit.jsonl",
      "catalog_row_id": "LCAT-000778",
      "sha256": "6a8bc975236beb1f69814a32b26e5939456d24702749369ffce1db31ad9c1520",
      "size_bytes": 649990,
      "source_family": "shadow_log_source_control"
    },
    {
      "absolute_path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\shadow_logs\\malformed_responses.jsonl",
      "catalog_row_id": "LCAT-000779",
      "sha256": "8f22898aad05e74f8b23d04dc3a2f1c861b51d9543ba47ee6de233510a88145c",
      "size_bytes": 12341,
      "source_family": "shadow_log_source_control"
    },
    {
      "absolute_path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\shadow_logs\\missed_opportunity_shadow.jsonl",
      "catalog_row_id": "LCAT-000781",
      "sha256": "ca9e5b1d25f6274e536dffc91610f64a6840365a3aff071e7ef8e2c820e0c5a5",
      "size_bytes": 7607024,
      "source_family": "shadow_log_source_control"
    },
    {
      "absolute_path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\shadow_logs\\ml_shadow_predictions.jsonl",
      "catalog_row_id": "LCAT-000782",
      "sha256": "9168481abd4ef5f1a68cd7af615191adac4fe988b31b61a0a8fe4a72cba7c16c",
      "size_bytes": 134,
      "source_family": "shadow_log_source_control"
    },
    {
      "absolute_path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\shadow_logs\\ml_shadow_status.jsonl",
      "catalog_row_id": "LCAT-000783",
      "sha256": "a5acc8e48d974b58db9901e91cf20ee014b8cc4993b0c91e34d5be5a468ce6c9",
      "size_bytes": 146390,
      "source_family": "shadow_log_source_control"
    },
    {
      "absolute_path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\shadow_logs\\nas100_orderflow_adverse_selection_status.jsonl",
      "catalog_row_id": "LCAT-000784",
      "sha256": "72a047029b2bca100d268bb9c117b45b832e8cb2d6e36590c4f6697b1692074b",
      "size_bytes": 134808,
      "source_family": "shadow_log_source_control"
    },
    {
      "absolute_path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\shadow_logs\\notification_queue_dead_zone_status.jsonl",
      "catalog_row_id": "LCAT-000785",
      "sha256": "662e4b53f66ebe321390c5afb269f117aad69ad68fe59ab673fff6064ae9783a",
      "size_bytes": 23857,
      "source_family": "shadow_log_source_control"
    },
    {
      "absolute_path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\shadow_logs\\ob_continuation_daily.csv",
      "catalog_row_id": "LCAT-000786",
      "sha256": "4ea3390cd1c5244e96679b64be60929148b9405acea13784a6a8828bc4d8f2de",
      "size_bytes": 5162,
      "source_family": "shadow_log_source_control"
    },
    {
      "absolute_path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\shadow_logs\\orderflow_primitives_status.jsonl",
      "catalog_row_id": "LCAT-000788",
      "sha256": "f7044bfd096a872504d7c0a0b1e019ff1b1a81e27c162593b01be62bcfcec13c",
      "size_bytes": 400003,
      "source_family": "shadow_log_source_control"
    },
    {
      "absolute_path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\shadow_logs\\partial_close_backtest.jsonl",
      "catalog_row_id": "LCAT-000789",
      "sha256": "6712a2b9f71d6c7d3b80bb79452bf3b8814873909d4e389d7381631a5a1624aa",
      "size_bytes": 23591,
      "source_family": "shadow_log_source_control"
    },
    {
      "absolute_path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\shadow_logs\\partial_close_backtest_exact_only.jsonl",
      "catalog_row_id": "LCAT-000790",
      "sha256": "de0885ec8662ac0bcfc30d007cd8dbe3a2c08722678d99c1a92035c31a42ede3",
      "size_bytes": 5922,
      "source_family": "shadow_log_source_control"
    },
    {
      "absolute_path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\shadow_logs\\pending_limit_lifecycle.jsonl",
      "catalog_row_id": "LCAT-000791",
      "sha256": "f0c45eb94d70b94e9e4eb6aebcb4943f3864a7f1cdb37c6003631337e8b9ad49",
      "size_bytes": 461124,
      "source_family": "shadow_log_source_control"
    },
    {
      "absolute_path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\shadow_logs\\pending_limit_lifecycle_audit.jsonl",
      "catalog_row_id": "LCAT-000792",
      "sha256": "a639889d645a232f032fe40adca6f114b48b3a23df9e487fbb7901c456ce6c13",
      "size_bytes": 261922,
      "source_family": "shadow_log_source_control"
    },
    {
      "absolute_path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\shadow_logs\\pending_limit_lifecycle_join_backfill.jsonl",
      "catalog_row_id": "LCAT-000793",
      "sha256": "0a146d00f936b85aa730f9e209d1b6ffb1cc387070944420d634c3aff5f504a0",
      "size_bytes": 528146,
      "source_family": "shadow_log_source_control"
    },
    {
      "absolute_path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\shadow_logs\\prefill_delivery_path.jsonl",
      "catalog_row_id": "LCAT-000794",
      "sha256": "16b04e67a69ba90608516f0a276cd7ef4396bc111606cac651dedb241fd823f7",
      "size_bytes": 249181,
      "source_family": "shadow_log_source_control"
    },
    {
      "absolute_path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\shadow_logs\\proximity_shadow_log.jsonl",
      "catalog_row_id": "LCAT-000797",
      "sha256": "979c398eda2a53eef25406e42449ec31dd3c363ec0523d14ecec768d47b3c165",
      "size_bytes": 156032,
      "source_family": "shadow_log_source_control"
    },
    {
      "absolute_path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\shadow_logs\\proxy_blocker_status.jsonl",
      "catalog_row_id": "LCAT-000798",
      "sha256": "52c6fc31b4051fd493561b5cf1aa543fa37cf9b3e440c07abd569b0a1034e838",
      "size_bytes": 134603,
      "source_family": "shadow_log_source_control"
    },
    {
      "absolute_path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\shadow_logs\\regime_classifications.jsonl",
      "catalog_row_id": "LCAT-000799",
      "sha256": "59ac2b2b26f4eff418e90a4dc5f595d30f565192cafaaf0bf85e809c9f1c028a",
      "size_bytes": 694802,
      "source_family": "shadow_log_source_control"
    },
    {
      "absolute_path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\shadow_logs\\s79_side_aware_risk_context.jsonl",
      "catalog_row_id": "LCAT-000801",
      "sha256": "2a78699a0f45792cf6c16f6451fe98be8e342822b1cac808d060279380eacf99",
      "size_bytes": 483803,
      "source_family": "shadow_log_source_control"
    },
    {
      "absolute_path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\shadow_logs\\session_volatility_log.csv",
      "catalog_row_id": "LCAT-000802",
      "sha256": "716e7ed9bdce0cccf6ba863fd72b06e01e1192b02bb791ba8532e73986490a35",
      "size_bytes": 1210,
      "source_family": "shadow_log_source_control"
    },
    {
      "absolute_path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\shadow_logs\\session_volatility_sweep_status.jsonl",
      "catalog_row_id": "LCAT-000803",
      "sha256": "a13ee19fa7d778ffd1c1286d5c28b0fbbba69ddf8fd25dff8118d3dd53145c34",
      "size_bytes": 21123,
      "source_family": "shadow_log_source_control"
    },
    {
      "absolute_path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\shadow_logs\\shadow_observer_hardening_status.jsonl",
      "catalog_row_id": "LCAT-000804",
      "sha256": "550aeb07295dadb3ac7dd26917d3a625cc456f10d21bc1bd1316c81de6c202fa",
      "size_bytes": 1023705,
      "source_family": "shadow_log_source_control"
    },
    {
      "absolute_path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\shadow_logs\\shadow_observer_status.jsonl",
      "catalog_row_id": "LCAT-000805",
      "sha256": "43ef3e1443f8571ea922476854b48c88568457e2349d15183bbcbae7309ae7e6",
      "size_bytes": 3550203,
      "source_family": "shadow_log_source_control"
    },
    {
      "absolute_path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\shadow_logs\\shadow_observer_tick_enrichment.jsonl",
      "catalog_row_id": "LCAT-000806",
      "sha256": "201e166b60ed1a11602a459dc2633c477476fff5346646531e082743c463cd06",
      "size_bytes": 145107,
      "source_family": "shadow_log_source_control"
    },
    {
      "absolute_path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\shadow_logs\\sierra_6b_si_depth_policy_status.jsonl",
      "catalog_row_id": "LCAT-000807",
      "sha256": "64d40ae5542642d9747a70ac6c683db3c26a735cdc3e4f2bf5f13ff400a1f5ad",
      "size_bytes": 8185,
      "source_family": "shadow_log_source_control"
    },
    {
      "absolute_path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\shadow_logs\\sierra_confluence_source_status.jsonl",
      "catalog_row_id": "LCAT-000808",
      "sha256": "2ef44ab5d69ed3f3556965e52991b865008e37534eba6316af269de062a94b96",
      "size_bytes": 282678,
      "source_family": "shadow_log_source_control"
    },
    {
      "absolute_path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\shadow_logs\\sierra_depth_enrichment_status.jsonl",
      "catalog_row_id": "LCAT-000809",
      "sha256": "9fee06c1067321b2ee65da8fc522a66c042a2e61989f3ba7677a1a0dad581a2c",
      "size_bytes": 267716,
      "source_family": "shadow_log_source_control"
    },
    {
      "absolute_path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\shadow_logs\\sierra_depth_feature_snapshots.jsonl",
      "catalog_row_id": "LCAT-000810",
      "sha256": "e3332f991a1d075881d4434d819cb895d52b8efdca946ae04b9273e85d5a668e",
      "size_bytes": 775124,
      "source_family": "shadow_log_source_control"
    },
    {
      "absolute_path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\shadow_logs\\sierra_proxy_registry_status.jsonl",
      "catalog_row_id": "LCAT-000811",
      "sha256": "4d4dcaa8aed424f9ec997b5e9ebdf4d8a0b72c1596d53f96dc7f224212d26ccc",
      "size_bytes": 4748121,
      "source_family": "shadow_log_source_control"
    },
    {
      "absolute_path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\shadow_logs\\sl_beyond_ob_decisions.jsonl",
      "catalog_row_id": "LCAT-000812",
      "sha256": "6ac23db82fbe361cf37dc5b1f99c424b13fbb59423551f2cbdffbeb73bfc9bbe",
      "size_bytes": 121628,
      "source_family": "shadow_log_source_control"
    },
    {
      "absolute_path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\shadow_logs\\slippage.jsonl",
      "catalog_row_id": "LCAT-000813",
      "sha256": "0b2ca6047809394efae7f5cc3c5beb96185d92de23740a056d08623a4ac2e9c9",
      "size_bytes": 1070,
      "source_family": "shadow_log_source_control"
    },
    {
      "absolute_path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\shadow_logs\\storage_retention_status.jsonl",
      "catalog_row_id": "LCAT-000814",
      "sha256": "39cdbb1652d19ff2035607b6dcd98364d9d1ced291628b8281c5c45c91a44b32",
      "size_bytes": 143361,
      "source_family": "shadow_log_source_control"
    },
    {
      "absolute_path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\shadow_logs\\strategy_follow_candidates.jsonl",
      "catalog_row_id": "LCAT-000815",
      "sha256": "79a78b9c8bc4f521de6a774d1519a90446fe6e731ef6626c6d9a1e126ee27e57",
      "size_bytes": 2461794,
      "source_family": "shadow_log_source_control"
    },
    {
      "absolute_path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\shadow_logs\\structure_detector_backfill_2022_2023.jsonl",
      "catalog_row_id": "LCAT-000817",
      "sha256": "519a5ea6ab9550183acf77ba22e5e77d8edd645923dede76a27c18656a55cb90",
      "size_bytes": 5518263,
      "source_family": "shadow_log_source_control"
    },
    {
      "absolute_path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\shadow_logs\\structure_detector_backfill_2026.jsonl",
      "catalog_row_id": "LCAT-000818",
      "sha256": "9c3913d6efa0ab57e95ecef1231829ffcd109f7e4ec5c556792e62e8429e783f",
      "size_bytes": 1323973,
      "source_family": "shadow_log_source_control"
    },
    {
      "absolute_path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\shadow_logs\\structure_detector_divergences.jsonl",
      "catalog_row_id": "LCAT-000819",
      "sha256": "5a84a44648aa030add5d81549a42b8ef9c8f4de4abf583b61fda80564bd2de94",
      "size_bytes": 136023,
      "source_family": "shadow_log_source_control"
    },
    {
      "absolute_path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\shadow_logs\\sweep_divergence_log.csv",
      "catalog_row_id": "LCAT-000820",
      "sha256": "c19adb6a7a08b7318a5c7710cb81cb3f06687b0e144143837da1f22a26ea1496",
      "size_bytes": 979,
      "source_family": "shadow_log_source_control"
    },
    {
      "absolute_path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\shadow_logs\\touch_count_gate_decisions.jsonl",
      "catalog_row_id": "LCAT-000821",
      "sha256": "81de75d58aac0da8362581db3fc181267782347ffa4413460d5a338a60851ef0",
      "size_bytes": 29758,
      "source_family": "shadow_log_source_control"
    },
    {
      "absolute_path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\shadow_logs\\trade_index_lifecycle_audit.jsonl",
      "catalog_row_id": "LCAT-000822",
      "sha256": "2a234fb618c0a38ffa66e15e64981e7c520d46b2ddb8d6abc2babe283e54fa2a",
      "size_bytes": 930106,
      "source_family": "shadow_log_source_control"
    },
    {
      "absolute_path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\shadow_logs\\v2_structural_selector_readiness.jsonl",
      "catalog_row_id": "LCAT-000823",
      "sha256": "74ce5a2a4422757a6e5ca7318903d9a26c610ae4c291bc601ca7c97b49da30fb",
      "size_bytes": 756772,
      "source_family": "shadow_log_source_control"
    },
    {
      "absolute_path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\shadow_logs\\v2b_forward_pairs.jsonl",
      "catalog_row_id": "LCAT-000826",
      "sha256": "1ab66f998e12d68f9cabf0897c2e0ce4984f26a78464c52fe4bc89532192546e",
      "size_bytes": 237883,
      "source_family": "shadow_log_source_control"
    },
    {
      "absolute_path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\shadow_logs\\xagusd_fresh_ob_late_ny.jsonl",
      "catalog_row_id": "LCAT-000827",
      "sha256": "50ca99f876709a1c76c06d0ca74c6a24b7dab6a62a1ae9641b90e10a081e369d",
      "size_bytes": 113707,
      "source_family": "shadow_log_source_control"
    },
    {
      "absolute_path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\shadow_logs\\xauusd_same_market_extension_status.jsonl",
      "catalog_row_id": "LCAT-000828",
      "sha256": "1dc3928b72b5744705282136fdcbd8b62ab0906b655e7ddd188d6199b881caed",
      "size_bytes": 568076,
      "source_family": "shadow_log_source_control"
    },
    {
      "absolute_path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\shadow_logs\\.contaminated_backup\\drawdown_state_changes_pre_2026-04-17.jsonl",
      "catalog_row_id": "LCAT-000829",
      "sha256": "1e7d3d7d0d76aa9ae3349045ba6b6837af2e218f243b1beefc07bd8a6d5ea9b3",
      "size_bytes": 65917,
      "source_family": "shadow_log_source_control"
    },
    {
      "absolute_path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\exports\\ftmo_spread_check.json",
      "catalog_row_id": "LCAT-000830",
      "sha256": "4108ee44a2d01a12418fc2551d9505fb21add3a4838e6e709019fdf69b1cfd91",
      "size_bytes": 4076,
      "source_family": "owner_or_tool_export"
    },
    {
      "absolute_path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\exports\\reasoning_text_mining_findings.json",
      "catalog_row_id": "LCAT-000831",
      "sha256": "311c0e38ae8ca2bad3be25b30a7d42f6d4728079b09b7706fb7dd727f6bb4f14",
      "size_bytes": 701,
      "source_family": "owner_or_tool_export"
    },
    {
      "absolute_path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\exports\\candle_redownload\\GBPUSD_D1.csv",
      "catalog_row_id": "LCAT-000832",
      "sha256": "2835f639cb79a998db5586d13f8780876877eedca8f4236780156d5b9a1a2e39",
      "size_bytes": 34654,
      "source_family": "owner_or_tool_export"
    },
    {
      "absolute_path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\exports\\candle_redownload\\GBPUSD_H1.csv",
      "catalog_row_id": "LCAT-000833",
      "sha256": "c47d3715ba3c98387b9fba0a62e40b7419445149f70ef6aa9a573bd9fdaa6ffa",
      "size_bytes": 938675,
      "source_family": "owner_or_tool_export"
    },
    {
      "absolute_path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\exports\\candle_redownload\\GBPUSD_H4.csv",
      "catalog_row_id": "LCAT-000834",
      "sha256": "c6d80dfcf063e000bc2b5b155c64396c38d8421eb28636d0f0c9e6df7d622d3b",
      "size_bytes": 236906,
      "source_family": "owner_or_tool_export"
    },
    {
      "absolute_path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\exports\\candle_redownload\\GBPUSD_M15.csv",
      "catalog_row_id": "LCAT-000835",
      "sha256": "f9e21276b493077a2b0c722b361e6d0d2cb4824fc141b756dec7ff7fab7f97d3",
      "size_bytes": 3714551,
      "source_family": "owner_or_tool_export"
    },
    {
      "absolute_path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\exports\\candle_redownload\\XAUUSD_D1.csv",
      "catalog_row_id": "LCAT-000836",
      "sha256": "1812d48d0dd043380980b43208c685bbff50c3af6907a9b4330565b3ab60ea3b",
      "size_bytes": 32212,
      "source_family": "owner_or_tool_export"
    },
    {
      "absolute_path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\exports\\candle_redownload\\candle_export_summary.json",
      "catalog_row_id": "LCAT-000837",
      "sha256": "47de8c674af39e0b44ed45525f669f093c2e492ddc2456260a841147e833fc16",
      "size_bytes": 2935,
      "source_family": "owner_or_tool_export"
    },
    {
      "absolute_path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\exports\\mt5_data_dump\\GBPUSD_M1_recent.csv",
      "catalog_row_id": "LCAT-000838",
      "sha256": "fe8e976a3e3473bfb7d1c70ed97b2b621adca83c9f19d7b45d581be3889a7f0e",
      "size_bytes": 7636290,
      "source_family": "owner_or_tool_export"
    },
    {
      "absolute_path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\exports\\mt5_data_dump\\XAUUSD_M1_recent.csv",
      "catalog_row_id": "LCAT-000839",
      "sha256": "37a01399c462dc8160f04502085f307c5fcb42e422507b78827fbc78bb109403",
      "size_bytes": 7245921,
      "source_family": "owner_or_tool_export"
    },
    {
      "absolute_path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\exports\\mt5_data_dump\\economic_calendar_summary.json",
      "catalog_row_id": "LCAT-000840",
      "sha256": "346c1a12fc1b2c3cf8cc94bf85677518ea41f51391cdbc865c09b0e04d8b00aa",
      "size_bytes": 478,
      "source_family": "owner_or_tool_export"
    },
    {
      "absolute_path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\exports\\mt5_data_dump\\hourly_volatility_profile.json",
      "catalog_row_id": "LCAT-000841",
      "sha256": "2fc57f154b4d23903bb3f6556135be984c58f69b745334cbf6ec65f6cd036b7b",
      "size_bytes": 41134,
      "source_family": "owner_or_tool_export"
    },
    {
      "absolute_path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\exports\\mt5_data_dump\\m1_data_summary.json",
      "catalog_row_id": "LCAT-000842",
      "sha256": "2473fe3381ae172f11c0309d58e6240c481d24ccac808265705cf79888c30fd2",
      "size_bytes": 1714,
      "source_family": "owner_or_tool_export"
    },
    {
      "absolute_path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\exports\\mt5_data_dump\\tick_data_availability.json",
      "catalog_row_id": "LCAT-000843",
      "sha256": "4a3163384718b2d904a437f3a04a58596a968d4178ee9b0953b2181adc7e8c0a",
      "size_bytes": 3821,
      "source_family": "owner_or_tool_export"
    },
    {
      "absolute_path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\exports\\mt5_data_dump\\trade_entry_spreads.json",
      "catalog_row_id": "LCAT-000844",
      "sha256": "646bb232442495cb8c4f0868775b42d1cf7ffa74bc5df4f63b43374fcc3b3ab8",
      "size_bytes": 128,
      "source_family": "owner_or_tool_export"
    },
    {
      "absolute_path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\exports\\multi_instrument\\AUDUSD_D1.csv",
      "catalog_row_id": "LCAT-000845",
      "sha256": "3830bd5ca0f53bff5e6ff1a5f15656094179cc0e872e4c5cb2a488089da88005",
      "size_bytes": 166870,
      "source_family": "owner_or_tool_export"
    },
    {
      "absolute_path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\exports\\multi_instrument\\AUDUSD_H1.csv",
      "catalog_row_id": "LCAT-000846",
      "sha256": "fba5b0b2b32a0b98ca9206d3b3d336a694666817614fa86f45acf1cf084bbb1b",
      "size_bytes": 1229727,
      "source_family": "owner_or_tool_export"
    },
    {
      "absolute_path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\exports\\multi_instrument\\AUDUSD_H4.csv",
      "catalog_row_id": "LCAT-000847",
      "sha256": "07bc8ed0b8fd86583682dbbace724d50afcd11d733daf5ace099712b52830055",
      "size_bytes": 619405,
      "source_family": "owner_or_tool_export"
    },
    {
      "absolute_path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\exports\\multi_instrument\\EURJPY_D1.csv",
      "catalog_row_id": "LCAT-000848",
      "sha256": "082994b36fb334a425f32cee4ade988882ab6a69a4c75c6ae5aa8625bc757a37",
      "size_bytes": 168818,
      "source_family": "owner_or_tool_export"
    },
    {
      "absolute_path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\exports\\multi_instrument\\EURJPY_H1.csv",
      "catalog_row_id": "LCAT-000849",
      "sha256": "cb90d14c8b62d993ef43bf2f49fd73829b01644f65d4577797eb8accdb3655aa",
      "size_bytes": 1242552,
      "source_family": "owner_or_tool_export"
    },
    {
      "absolute_path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\exports\\multi_instrument\\EURJPY_H4.csv",
      "catalog_row_id": "LCAT-000850",
      "sha256": "60e5acf19005b278de78d1f5b6fbe23f2a96fd39692ce394bc32576eed364646",
      "size_bytes": 624889,
      "source_family": "owner_or_tool_export"
    },
    {
      "absolute_path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\exports\\multi_instrument\\EURUSD_D1.csv",
      "catalog_row_id": "LCAT-000851",
      "sha256": "7abb8b391e3bf6e58e129f416333596b7b35393d552d16255f396b9a71ebb897",
      "size_bytes": 172828,
      "source_family": "owner_or_tool_export"
    },
    {
      "absolute_path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\exports\\multi_instrument\\EURUSD_H1.csv",
      "catalog_row_id": "LCAT-000852",
      "sha256": "acf7b4e93d90a6e67f1107bdd1bfda658fc3d46989d8bcf735316a8f80145364",
      "size_bytes": 1262939,
      "source_family": "owner_or_tool_export"
    },
    {
      "absolute_path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\exports\\multi_instrument\\EURUSD_H4.csv",
      "catalog_row_id": "LCAT-000853",
      "sha256": "66b32aac4c4d28927c03be9075dc1168285450880a141be6c2381b35ecd4c06a",
      "size_bytes": 637818,
      "source_family": "owner_or_tool_export"
    },
    {
      "absolute_path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\exports\\multi_instrument\\EURUSD_M15.csv",
      "catalog_row_id": "LCAT-000854",
      "sha256": "54ef4a2234026fa92f2ce569ffeba1187146090ddc68049cbb1fcf260431611f",
      "size_bytes": 3133903,
      "source_family": "owner_or_tool_export"
    },
    {
      "absolute_path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\exports\\multi_instrument\\GBPJPY_D1.csv",
      "catalog_row_id": "LCAT-000855",
      "sha256": "7976b90504924dbc7babda5f40126b46b429b357a076c50baeb595974df5e646",
      "size_bytes": 169320,
      "source_family": "owner_or_tool_export"
    },
    {
      "absolute_path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\exports\\multi_instrument\\GBPJPY_H1.csv",
      "catalog_row_id": "LCAT-000856",
      "sha256": "e680a8ed7296351f4151b1da0c6220c42510641aff57aa49e6d1252d671fbf79",
      "size_bytes": 1244019,
      "source_family": "owner_or_tool_export"
    },
    {
      "absolute_path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\exports\\multi_instrument\\GBPJPY_H4.csv",
      "catalog_row_id": "LCAT-000857",
      "sha256": "56fbfa4f3b20b2e5c8a277ba520039d409699b9f0bfc625a2b6a1c4130a24188",
      "size_bytes": 625436,
      "source_family": "owner_or_tool_export"
    },
    {
      "absolute_path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\exports\\multi_instrument\\GBPJPY_M15.csv",
      "catalog_row_id": "LCAT-000858",
      "sha256": "374062872c0948eda68618a3e0ebf8b4c2878f4f6f235e2fd49adce3878511dc",
      "size_bytes": 6172349,
      "source_family": "owner_or_tool_export"
    },
    {
      "absolute_path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\exports\\multi_instrument\\GBPUSD_D1.csv",
      "catalog_row_id": "LCAT-000859",
      "sha256": "80308a3599b9c40e492f663e5b49557711c77b8839e25145fff5c35b94d27733",
      "size_bytes": 184106,
      "source_family": "owner_or_tool_export"
    },
    {
      "absolute_path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\exports\\multi_instrument\\GBPUSD_H1.csv",
      "catalog_row_id": "LCAT-000860",
      "sha256": "d0c018b828a983719d877328fbe30b3ae14f58ae948f8a2a3a44ca38f014485f",
      "size_bytes": 1328773,
      "source_family": "owner_or_tool_export"
    },
    {
      "absolute_path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\exports\\multi_instrument\\GBPUSD_H4.csv",
      "catalog_row_id": "LCAT-000861",
      "sha256": "e362e789825e39f675bb2828ea099f6c4e9df7bb73d5dc2ef4c8df1f104d9b62",
      "size_bytes": 667461,
      "source_family": "owner_or_tool_export"
    },
    {
      "absolute_path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\exports\\multi_instrument\\GBPUSD_M15.csv",
      "catalog_row_id": "LCAT-000862",
      "sha256": "059edb9a1712b688802ef573c57c1940771b264adfe5e7f512869c3f16200f3c",
      "size_bytes": 3306698,
      "source_family": "owner_or_tool_export"
    },
    {
      "absolute_path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\exports\\multi_instrument\\NZDUSD_D1.csv",
      "catalog_row_id": "LCAT-000863",
      "sha256": "4a17831108a199671b09dbc9418a1296142bc2d68be535bf4d2c97c823716857",
      "size_bytes": 166823,
      "source_family": "owner_or_tool_export"
    },
    {
      "absolute_path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\exports\\multi_instrument\\NZDUSD_H1.csv",
      "catalog_row_id": "LCAT-000864",
      "sha256": "0243f9c466743606578e35d1003962ecd9b73435d371defe351ca4c6aafbfe5f",
      "size_bytes": 1228985,
      "source_family": "owner_or_tool_export"
    },
    {
      "absolute_path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\exports\\multi_instrument\\NZDUSD_H4.csv",
      "catalog_row_id": "LCAT-000865",
      "sha256": "f5101e69b07c1ae1025de183fef658466fd85b24b3edf9d9620bd9727e74d535",
      "size_bytes": 618301,
      "source_family": "owner_or_tool_export"
    },
    {
      "absolute_path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\exports\\multi_instrument\\NZDUSD_M15.csv",
      "catalog_row_id": "LCAT-000866",
      "sha256": "19b292d2e86bb3a7b1541f80fd4e5ef5bc02bcf21467598288868cdf47931413",
      "size_bytes": 6069379,
      "source_family": "owner_or_tool_export"
    },
    {
      "absolute_path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\exports\\multi_instrument\\US30.cash_M15.csv",
      "catalog_row_id": "LCAT-000867",
      "sha256": "ecca14562033e51a6e64dc6d68f56a5e9e15a22bc9def3ad43c6c01ce92c4a89",
      "size_bytes": 6530280,
      "source_family": "owner_or_tool_export"
    },
    {
      "absolute_path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\exports\\multi_instrument\\US30_M15.csv",
      "catalog_row_id": "LCAT-000868",
      "sha256": "ecca14562033e51a6e64dc6d68f56a5e9e15a22bc9def3ad43c6c01ce92c4a89",
      "size_bytes": 6530280,
      "source_family": "owner_or_tool_export"
    },
    {
      "absolute_path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\exports\\multi_instrument\\US30_cash_D1.csv",
      "catalog_row_id": "LCAT-000869",
      "sha256": "8c89e15f36867167e5e0c83440702eb13faa991bd63ad55f6c70d3ac6a81eeb3",
      "size_bytes": 106191,
      "source_family": "owner_or_tool_export"
    },
    {
      "absolute_path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\exports\\multi_instrument\\US30_cash_H1.csv",
      "catalog_row_id": "LCAT-000870",
      "sha256": "2775571ce3c1b89948134e54b9c54102e4ad5a1d9abc2232758af20da0a47fae",
      "size_bytes": 1324934,
      "source_family": "owner_or_tool_export"
    },
    {
      "absolute_path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\exports\\multi_instrument\\US30_cash_H4.csv",
      "catalog_row_id": "LCAT-000871",
      "sha256": "587d1c66751f1ffc762dc8077837d41229488342da36516f4f81eb72287196e4",
      "size_bytes": 661261,
      "source_family": "owner_or_tool_export"
    },
    {
      "absolute_path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\exports\\multi_instrument\\US30_cash_M15.csv",
      "catalog_row_id": "LCAT-000872",
      "sha256": "ecca14562033e51a6e64dc6d68f56a5e9e15a22bc9def3ad43c6c01ce92c4a89",
      "size_bytes": 6530280,
      "source_family": "owner_or_tool_export"
    },
    {
      "absolute_path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\exports\\multi_instrument\\US500_cash_D1.csv",
      "catalog_row_id": "LCAT-000873",
      "sha256": "f6e8aeb3ee136c7d35ba4742b7777a2d0290264aeacd98334e93204bfff9d363",
      "size_bytes": 114166,
      "source_family": "owner_or_tool_export"
    },
    {
      "absolute_path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\exports\\multi_instrument\\US500_cash_H1.csv",
      "catalog_row_id": "LCAT-000874",
      "sha256": "dd2c28db32c2b2a61d31682e05b2939c40dec7678b990b9dc78a11d7c50968fa",
      "size_bytes": 1224719,
      "source_family": "owner_or_tool_export"
    },
    {
      "absolute_path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\exports\\multi_instrument\\US500_cash_H4.csv",
      "catalog_row_id": "LCAT-000875",
      "sha256": "da87e51c6c9b76efac0bfecf7e86f3b1ee740a5afd62e1077c6602565485b2a1",
      "size_bytes": 543481,
      "source_family": "owner_or_tool_export"
    },
    {
      "absolute_path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\exports\\multi_instrument\\USDCAD_D1.csv",
      "catalog_row_id": "LCAT-000876",
      "sha256": "b7a2eaa167a61f2742327cf6ea6c9f58f030759952c20d4842c2d625d6252a06",
      "size_bytes": 182912,
      "source_family": "owner_or_tool_export"
    },
    {
      "absolute_path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\exports\\multi_instrument\\USDCAD_H1.csv",
      "catalog_row_id": "LCAT-000877",
      "sha256": "13068f937ddd959639292d37ff976d931e4c10d5e3d4bf0bab9f147b6c85be2c",
      "size_bytes": 1340523,
      "source_family": "owner_or_tool_export"
    },
    {
      "absolute_path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\exports\\multi_instrument\\USDCAD_H4.csv",
      "catalog_row_id": "LCAT-000878",
      "sha256": "3100d7afa50238006cb1d54ec6dc9d61d1e032db51b426b7b30ba3316dd81b38",
      "size_bytes": 672627,
      "source_family": "owner_or_tool_export"
    },
    {
      "absolute_path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\exports\\multi_instrument\\USDJPY_D1.csv",
      "catalog_row_id": "LCAT-000879",
      "sha256": "0922d8d5954d82bd7be87b3ebfa61d0a7012f074e9a033de964cef31805fac08",
      "size_bytes": 167585,
      "source_family": "owner_or_tool_export"
    },
    {
      "absolute_path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\exports\\multi_instrument\\USDJPY_H1.csv",
      "catalog_row_id": "LCAT-000880",
      "sha256": "54fd259115aac4767afb547c89a16d1575bdd9be9006a6b6f8140ff14a39029c",
      "size_bytes": 1231694,
      "source_family": "owner_or_tool_export"
    },
    {
      "absolute_path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\exports\\multi_instrument\\USDJPY_H4.csv",
      "catalog_row_id": "LCAT-000881",
      "sha256": "3dd61ac124e62b281bb28014f185a6b71c7b705c5a53c66dcf60c49e9ae34190",
      "size_bytes": 621084,
      "source_family": "owner_or_tool_export"
    },
    {
      "absolute_path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\exports\\multi_instrument\\USDJPY_M15.csv",
      "catalog_row_id": "LCAT-000882",
      "sha256": "769e1df3b978dccf21e68d61544d5d763a5682e839101ccc1ab4f7fd97390f5f",
      "size_bytes": 3050977,
      "source_family": "owner_or_tool_export"
    },
    {
      "absolute_path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\exports\\multi_instrument\\USOIL_cash_D1.csv",
      "catalog_row_id": "LCAT-000883",
      "sha256": "b0824d47b66a06703470150e8289e47d06cfba40a8a30fceb6bacc6fa050dc39",
      "size_bytes": 68835,
      "source_family": "owner_or_tool_export"
    },
    {
      "absolute_path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\exports\\multi_instrument\\USOIL_cash_H1.csv",
      "catalog_row_id": "LCAT-000884",
      "sha256": "66976e3b24cd164b1a0978419551b95bca927265d61679da503a202263900e57",
      "size_bytes": 1163798,
      "source_family": "owner_or_tool_export"
    },
    {
      "absolute_path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\exports\\multi_instrument\\USOIL_cash_H4.csv",
      "catalog_row_id": "LCAT-000885",
      "sha256": "c57cca56980a60f8e00b5ca3ae144d16a207b67d5922db12ea3b9fb65ea69dc4",
      "size_bytes": 479258,
      "source_family": "owner_or_tool_export"
    },
    {
      "absolute_path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\exports\\multi_instrument\\XAGUSD_D1.csv",
      "catalog_row_id": "LCAT-000886",
      "sha256": "b5d84011d7908f563b877d0573954feb397c570a25f027e8c3e882e7d5d30562",
      "size_bytes": 158187,
      "source_family": "owner_or_tool_export"
    },
    {
      "absolute_path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\exports\\multi_instrument\\XAGUSD_H1.csv",
      "catalog_row_id": "LCAT-000887",
      "sha256": "1cfbb6935c68a977af10dbec2afd519c4eece3aa2a87ced479a32828d23ceb19",
      "size_bytes": 1170507,
      "source_family": "owner_or_tool_export"
    },
    {
      "absolute_path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\exports\\multi_instrument\\XAGUSD_H4.csv",
      "catalog_row_id": "LCAT-000888",
      "sha256": "cb122c9cdf9f016b03fff30f4700044fa1d2081e54d553d1509720ba755dbbe9",
      "size_bytes": 588449,
      "source_family": "owner_or_tool_export"
    },
    {
      "absolute_path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\exports\\multi_instrument\\XAGUSD_M15.csv",
      "catalog_row_id": "LCAT-000889",
      "sha256": "da8c548412bee2a02a5afa1421661b1391cd2df089de2242a36259a24401c7e8",
      "size_bytes": 2902491,
      "source_family": "owner_or_tool_export"
    },
    {
      "absolute_path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\exports\\multi_instrument\\XAUUSD_D1.csv",
      "catalog_row_id": "LCAT-000890",
      "sha256": "2e9781367fef55fda36ad26fe85284132e4d948e4a909e709c14238fb33d0a35",
      "size_bytes": 170107,
      "source_family": "owner_or_tool_export"
    },
    {
      "absolute_path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\exports\\multi_instrument\\XAUUSD_H1.csv",
      "catalog_row_id": "LCAT-000891",
      "sha256": "6066607243a4cec4e9cf6fa9984dccf1db5fb49aa690eec380ba3b6491817a57",
      "size_bytes": 1245978,
      "source_family": "owner_or_tool_export"
    },
    {
      "absolute_path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\exports\\multi_instrument\\XAUUSD_H4.csv",
      "catalog_row_id": "LCAT-000892",
      "sha256": "1350221fa694ed8c393e6e1feb3ba00e1ce178564c02a5cddd7a6d836832913d",
      "size_bytes": 627906,
      "source_family": "owner_or_tool_export"
    },
    {
      "absolute_path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\exports\\multi_instrument\\XAUUSD_M15.csv",
      "catalog_row_id": "LCAT-000893",
      "sha256": "64e39bba7b6c6c4faa635e3089a12ca883b0f9006a2d8369c7028184ba6305d6",
      "size_bytes": 3115490,
      "source_family": "owner_or_tool_export"
    },
    {
      "absolute_path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\exports\\multi_instrument\\align_injection_design.md",
      "catalog_row_id": "LCAT-000894",
      "sha256": "9bebfa11eb17fe0fa0e8df2480f0ce65c5e284e3a2659600b23191a0ea1e99ea",
      "size_bytes": 1280,
      "source_family": "owner_or_tool_export"
    },
    {
      "absolute_path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\exports\\multi_instrument\\bearish_gold_dates.txt",
      "catalog_row_id": "LCAT-000895",
      "sha256": "390f1d9b5d7b56e958553c815b97a3c73ac6053ba3e3539b5653cf9b66123008",
      "size_bytes": 600,
      "source_family": "owner_or_tool_export"
    },
    {
      "absolute_path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\exports\\multi_instrument\\correlation_sizing_design.md",
      "catalog_row_id": "LCAT-000896",
      "sha256": "4d79b7bd4ebbef5022152506111f9e9413a6846e82078e48209735c010ee5d17",
      "size_bytes": 1662,
      "source_family": "owner_or_tool_export"
    },
    {
      "absolute_path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\exports\\multi_instrument\\extraction_summary.json",
      "catalog_row_id": "LCAT-000897",
      "sha256": "9e62e3f9cc48230b8b45b0b3476131114ce72cf96afea5ed1bf3db418889fbaf",
      "size_bytes": 10232,
      "source_family": "owner_or_tool_export"
    },
    {
      "absolute_path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\exports\\multi_instrument\\screening_results\\AUDUSD_detail.json",
      "catalog_row_id": "LCAT-000898",
      "sha256": "78dd993f6b8ae8e2994cc84002cabe5b3d2d0201a4cae03b15595a873d7feead",
      "size_bytes": 10347,
      "source_family": "owner_or_tool_export"
    },
    {
      "absolute_path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\exports\\multi_instrument\\screening_results\\EURJPY_detail.json",
      "catalog_row_id": "LCAT-000899",
      "sha256": "c26528861d70c06cb44ddb877d467daf1712053c15808eed960770734dd3666b",
      "size_bytes": 10364,
      "source_family": "owner_or_tool_export"
    },
    {
      "absolute_path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\exports\\multi_instrument\\screening_results\\EURUSD_detail.json",
      "catalog_row_id": "LCAT-000900",
      "sha256": "6e5749a347dfbdfa6bc1aa3cc5f54a32797fa951eea433bc0a676ba0a448d2b2",
      "size_bytes": 10351,
      "source_family": "owner_or_tool_export"
    },
    {
      "absolute_path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\exports\\multi_instrument\\screening_results\\GBPJPY_detail.json",
      "catalog_row_id": "LCAT-000901",
      "sha256": "5776f278666344581cbed01c2cae41143c570490dc1bb64ae4d5b05ac37a194f",
      "size_bytes": 10366,
      "source_family": "owner_or_tool_export"
    },
    {
      "absolute_path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\exports\\multi_instrument\\screening_results\\GBPUSD_detail.json",
      "catalog_row_id": "LCAT-000902",
      "sha256": "ca953aeb16fbd4b0f6e15a051c7ac6e7eaf3d215b68a9a8d90246cb035ad6486",
      "size_bytes": 10356,
      "source_family": "owner_or_tool_export"
    },
    {
      "absolute_path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\exports\\multi_instrument\\screening_results\\NZDUSD_detail.json",
      "catalog_row_id": "LCAT-000903",
      "sha256": "191072665007ac80849fa6a61b120a53d306b0c3e2efac2919a2dd34f78f431f",
      "size_bytes": 10359,
      "source_family": "owner_or_tool_export"
    },
    {
      "absolute_path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\exports\\multi_instrument\\screening_results\\US30_cash_detail.json",
      "catalog_row_id": "LCAT-000904",
      "sha256": "4160076bc62ba6d540e574b463d81d34cca2f567168fd3b9f6a680c044a348d7",
      "size_bytes": 10374,
      "source_family": "owner_or_tool_export"
    },
    {
      "absolute_path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\exports\\multi_instrument\\screening_results\\US500_cash_detail.json",
      "catalog_row_id": "LCAT-000905",
      "sha256": "67df0799eeea708d93d10ea4b0d10a3882a8a91e46d25b9b88ea878da1a1f1d2",
      "size_bytes": 10380,
      "source_family": "owner_or_tool_export"
    },
    {
      "absolute_path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\exports\\multi_instrument\\screening_results\\USDCAD_detail.json",
      "catalog_row_id": "LCAT-000906",
      "sha256": "d0814ae2ebef1a1f576d740720f80b74d53bcaa96ec3486c28b259d2ebdb0784",
      "size_bytes": 10367,
      "source_family": "owner_or_tool_export"
    },
    {
      "absolute_path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\exports\\multi_instrument\\screening_results\\USDJPY_detail.json",
      "catalog_row_id": "LCAT-000907",
      "sha256": "157d4838f43b3bb2e2e5b600d7af521e7f7d08001f447221b822c2ee0a269c7b",
      "size_bytes": 10369,
      "source_family": "owner_or_tool_export"
    },
    {
      "absolute_path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\exports\\multi_instrument\\screening_results\\USOIL_cash_detail.json",
      "catalog_row_id": "LCAT-000908",
      "sha256": "5ec8d82bcf4533bef84a4d8faa1708f06d8cb2983c4b6a1febf6b3212e43f9f0",
      "size_bytes": 10367,
      "source_family": "owner_or_tool_export"
    },
    {
      "absolute_path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\exports\\multi_instrument\\screening_results\\XAGUSD_detail.json",
      "catalog_row_id": "LCAT-000909",
      "sha256": "5e889f82c2231e33711237bff63c07a2a338a74ef4e93bcc7682e005e17bf29b",
      "size_bytes": 10351,
      "source_family": "owner_or_tool_export"
    },
    {
      "absolute_path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\data\\external\\features\\GBPJPY\\phase3_m15_candidate_gap_external_v1_20260501T005921Z.jsonl",
      "catalog_row_id": "LCAT-000912",
      "sha256": "ea10783f03feb861a4c856c5bacdb68ccd253c0d3354abaee437dc69d8f52123",
      "size_bytes": 1549414,
      "source_family": "local_external_or_vendor_cache"
    },
    {
      "absolute_path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\data\\external\\features\\GBPUSD\\phase3_m15_candidate_gap_external_v1_20260501T005921Z.jsonl",
      "catalog_row_id": "LCAT-000919",
      "sha256": "3a1f9c61a3738d62328af86036fe4bb190c9d4e451eac58f5b85d7cda8033f43",
      "size_bytes": 1557200,
      "source_family": "local_external_or_vendor_cache"
    },
    {
      "absolute_path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\data\\external\\features\\GBPUSD\\smoke_phase3_m15_20260430T235137Z.jsonl",
      "catalog_row_id": "LCAT-000920",
      "sha256": "a5a196a0b2e369fc080dcd72c0d3f77eeff50295a011c12f1ca8a85a1733df8f",
      "size_bytes": 117120,
      "source_family": "local_external_or_vendor_cache"
    },
    {
      "absolute_path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\data\\external\\features\\NAS100\\phase3_m15_candidate_gap_external_v1_20260501T005921Z.jsonl",
      "catalog_row_id": "LCAT-000927",
      "sha256": "e0cfa063a3690499e04860637dc536eb2ab83333a591ec8813cc173173e75861",
      "size_bytes": 1485988,
      "source_family": "local_external_or_vendor_cache"
    },
    {
      "absolute_path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\data\\external\\features\\NAS100\\smoke_phase3_m15_20260430T235137Z.jsonl",
      "catalog_row_id": "LCAT-000928",
      "sha256": "372cfb51519676dcfa78029b226bea3e5b3e69f983e0e440e67178278b24a9ce",
      "size_bytes": 117120,
      "source_family": "local_external_or_vendor_cache"
    },
    {
      "absolute_path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\data\\external\\features\\US30_CASH\\phase3_m15_candidate_gap_external_v1_20260501T005921Z.jsonl",
      "catalog_row_id": "LCAT-000935",
      "sha256": "4007bc531ddfb385ce746e7b31f22c14ef83b97d96fcec9ceb9dc4c92385fd71",
      "size_bytes": 1486368,
      "source_family": "local_external_or_vendor_cache"
    },
    {
      "absolute_path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\data\\external\\features\\US30_CASH\\smoke_phase3_m15_20260430T235137Z.jsonl",
      "catalog_row_id": "LCAT-000936",
      "sha256": "df281e38a5d1c340871c95893cd387b69e781db45223ce27f019b0b8d0bf41bb",
      "size_bytes": 117125,
      "source_family": "local_external_or_vendor_cache"
    },
    {
      "absolute_path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\data\\external\\features\\USDJPY\\phase3_m15_candidate_gap_external_v1_20260501T005921Z.jsonl",
      "catalog_row_id": "LCAT-000939",
      "sha256": "45f6ee9e0f961e5279b19246f492a5b244baf80ea7766641f1b62e1ce4a51df9",
      "size_bytes": 1557200,
      "source_family": "local_external_or_vendor_cache"
    },
    {
      "absolute_path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\data\\external\\features\\XAGUSD\\phase3_m15_candidate_gap_external_v1_20260501T005921Z.jsonl",
      "catalog_row_id": "LCAT-000946",
      "sha256": "2a76bb6aada41da18f59a2a228edae6ca793b61e48c7f46a40c282faed2e5419",
      "size_bytes": 1716660,
      "source_family": "local_external_or_vendor_cache"
    },
    {
      "absolute_path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\data\\external\\features\\XAGUSD\\smoke_phase3_m15_20260430T235137Z.jsonl",
      "catalog_row_id": "LCAT-000947",
      "sha256": "67fb16abbf4e28ebf2b546d8044a6c01d78b64a6b01c734a65049fed08e06216",
      "size_bytes": 117120,
      "source_family": "local_external_or_vendor_cache"
    },
    {
      "absolute_path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\data\\external\\features\\XAUUSD\\20260430T221000Z.json",
      "catalog_row_id": "LCAT-000948",
      "sha256": "27bf10c8df5e8666fd81dd5c597aff816d8458b9ddc4fd2568b3dde3b9965ada",
      "size_bytes": 1613,
      "source_family": "local_external_or_vendor_cache"
    },
    {
      "absolute_path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\data\\external\\features\\XAUUSD\\20260430T225000Z.json",
      "catalog_row_id": "LCAT-000949",
      "sha256": "8b080b96cbf6bd4afee0285bb3d6adc279bc866c697af9b5e9e54f13b3b6e4eb",
      "size_bytes": 37731,
      "source_family": "local_external_or_vendor_cache"
    },
    {
      "absolute_path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\data\\external\\features\\XAUUSD\\phase3_m15_candidate_gap_external_v1_20260501T005921Z.jsonl",
      "catalog_row_id": "LCAT-000956",
      "sha256": "0242c0547c2b1d433dccb438a7a1ccbf304392d6a89622575f18084a2a09d3c4",
      "size_bytes": 2189768,
      "source_family": "local_external_or_vendor_cache"
    },
    {
      "absolute_path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\data\\external\\features\\XAUUSD\\smoke_phase3_m15_20260430T235137Z.jsonl",
      "catalog_row_id": "LCAT-000957",
      "sha256": "847312778969e2f53065cb2c7128b906da56ab4d5b471e6506005bfaa55978ed",
      "size_bytes": 117120,
      "source_family": "local_external_or_vendor_cache"
    },
    {
      "absolute_path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\data\\external\\normalized\\cftc_cot\\disagg_combined_20260430T220916Z.jsonl",
      "catalog_row_id": "LCAT-000958",
      "sha256": "ecf30a74d1a8791055eb3ca456049ca31660d1c83b10983dccfeead4b4bfa477",
      "size_bytes": 10271,
      "source_family": "local_external_or_vendor_cache"
    },
    {
      "absolute_path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\data\\external\\normalized\\cftc_cot\\disagg_combined_20260430T234727Z.jsonl",
      "catalog_row_id": "LCAT-000959",
      "sha256": "9ea15dda54673845b3e8eb8e4b5bde0343242dd911c763a8919da2c976567960",
      "size_bytes": 100146,
      "source_family": "local_external_or_vendor_cache"
    },
    {
      "absolute_path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\data\\external\\normalized\\cftc_cot\\disagg_combined_20260501T000733Z.jsonl",
      "catalog_row_id": "LCAT-000960",
      "sha256": "ed95cb998071f6386633ae4b44d2921c1aacb8f48a5c732174fbdf4bbf20063b",
      "size_bytes": 120816,
      "source_family": "local_external_or_vendor_cache"
    },
    {
      "absolute_path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\data\\external\\normalized\\flashalpha_gex\\DIA_gex_20260430T224718Z.jsonl",
      "catalog_row_id": "LCAT-000961",
      "sha256": "690c1306fa8eac711352d67b0bb97033c8ef3d2dfe202d5ba044fff0dcd68a82",
      "size_bytes": 364,
      "source_family": "local_external_or_vendor_cache"
    },
    {
      "absolute_path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\data\\external\\normalized\\flashalpha_gex\\DIA_gex_20260430T234828Z.jsonl",
      "catalog_row_id": "LCAT-000962",
      "sha256": "40b35cf475ec9be4973a03c91715af34eba202b2c3581023b8c4a756a7d01059",
      "size_bytes": 364,
      "source_family": "local_external_or_vendor_cache"
    },
    {
      "absolute_path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\data\\external\\normalized\\flashalpha_gex\\DIA_gex_20260501T001141Z.jsonl",
      "catalog_row_id": "LCAT-000963",
      "sha256": "8030ec3b2626bfea5c6817c7e566822f2de2acf73bf7b89385c1ce7ba6066386",
      "size_bytes": 377,
      "source_family": "local_external_or_vendor_cache"
    },
    {
      "absolute_path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\data\\external\\normalized\\flashalpha_gex\\GLD_gex_20260430T224721Z.jsonl",
      "catalog_row_id": "LCAT-000964",
      "sha256": "32761840948b1dc6a00d4dd20da1c61c4771f678f32e02ac855a0127e320b5da",
      "size_bytes": 367,
      "source_family": "local_external_or_vendor_cache"
    },
    {
      "absolute_path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\data\\external\\normalized\\flashalpha_gex\\GLD_gex_20260430T234832Z.jsonl",
      "catalog_row_id": "LCAT-000965",
      "sha256": "002965e92cb928cc893250dd9094121e1f2a7d0095eb2605a3dc76579be60ad6",
      "size_bytes": 367,
      "source_family": "local_external_or_vendor_cache"
    },
    {
      "absolute_path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\data\\external\\normalized\\flashalpha_gex\\GLD_gex_20260501T001144Z.jsonl",
      "catalog_row_id": "LCAT-000966",
      "sha256": "2e806e263172f378ce9e8814dde5f9520522b7d751864b5f0dc577baa6b2305a",
      "size_bytes": 366,
      "source_family": "local_external_or_vendor_cache"
    },
    {
      "absolute_path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\data\\external\\normalized\\flashalpha_gex\\QQQ_gex_20260430T224718Z.jsonl",
      "catalog_row_id": "LCAT-000967",
      "sha256": "e72baaccc64eaa97e51d131af6a949698626338b8ee98fc276d70bc0d1f1c333",
      "size_bytes": 365,
      "source_family": "local_external_or_vendor_cache"
    },
    {
      "absolute_path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\data\\external\\normalized\\flashalpha_gex\\QQQ_gex_20260430T234825Z.jsonl",
      "catalog_row_id": "LCAT-000968",
      "sha256": "a8d6dfe56110ca0c32794bd60803f873ca3aff45a18d14936e42e7ad04d2064a",
      "size_bytes": 365,
      "source_family": "local_external_or_vendor_cache"
    },
    {
      "absolute_path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\data\\external\\normalized\\flashalpha_gex\\QQQ_gex_20260501T001140Z.jsonl",
      "catalog_row_id": "LCAT-000969",
      "sha256": "68c59da8e59f7304609af759c8d0a99c1ff75b0495c40c7a285cdf7899a5189a",
      "size_bytes": 364,
      "source_family": "local_external_or_vendor_cache"
    },
    {
      "absolute_path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\data\\external\\normalized\\flashalpha_gex\\SLV_gex_20260430T224723Z.jsonl",
      "catalog_row_id": "LCAT-000970",
      "sha256": "845fd4785c62d11e6fd79afd446344fc83d9798394646521e82b2085e206735d",
      "size_bytes": 365,
      "source_family": "local_external_or_vendor_cache"
    },
    {
      "absolute_path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\data\\external\\normalized\\flashalpha_gex\\SLV_gex_20260430T234834Z.jsonl",
      "catalog_row_id": "LCAT-000971",
      "sha256": "d7d915206271110f1fc93b17cdd16794cb101e3c574288935d332ad7d90629a5",
      "size_bytes": 377,
      "source_family": "local_external_or_vendor_cache"
    },
    {
      "absolute_path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\data\\external\\normalized\\flashalpha_gex\\SLV_gex_20260501T001145Z.jsonl",
      "catalog_row_id": "LCAT-000972",
      "sha256": "e8e9e9628dc2dbe7d8424b10c4a86294a46ac2f10cc2be66f146df29e9bf9a1a",
      "size_bytes": 365,
      "source_family": "local_external_or_vendor_cache"
    },
    {
      "absolute_path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\data\\external\\normalized\\flashalpha_gex\\SPY_gex_20260430T224720Z.jsonl",
      "catalog_row_id": "LCAT-000973",
      "sha256": "6df49e2440b2fb4dfa017e7decf9219bc7b0d3d44c75f41d99ba0dc326a90d7a",
      "size_bytes": 364,
      "source_family": "local_external_or_vendor_cache"
    },
    {
      "absolute_path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\data\\external\\normalized\\flashalpha_gex\\SPY_gex_20260430T234830Z.jsonl",
      "catalog_row_id": "LCAT-000974",
      "sha256": "b7f1f5839b23063647426c455ec203e50b038408161bd511aa924ea1c504ac63",
      "size_bytes": 363,
      "source_family": "local_external_or_vendor_cache"
    },
    {
      "absolute_path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\data\\external\\normalized\\flashalpha_gex\\SPY_gex_20260501T001143Z.jsonl",
      "catalog_row_id": "LCAT-000975",
      "sha256": "9b2cc5414a0792fb908d65b15a102202805f3b701bbdc5d42c43d087da10c103",
      "size_bytes": 364,
      "source_family": "local_external_or_vendor_cache"
    },
    {
      "absolute_path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\data\\external\\normalized\\fred\\DFII10_observations_20260430T234725Z.jsonl",
      "catalog_row_id": "LCAT-000976",
      "sha256": "a87b433462372ded399dd7ed962bac5301a1eb059393010470ce0c0ed1588150",
      "size_bytes": 235716,
      "source_family": "local_external_or_vendor_cache"
    },
    {
      "absolute_path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\data\\external\\normalized\\fred\\DFII10_observations_20260501T000731Z.jsonl",
      "catalog_row_id": "LCAT-000977",
      "sha256": "a7a46df13aa975101594d99b5a97b456d569acee591b160b9d05cf9f3567189f",
      "size_bytes": 354156,
      "source_family": "local_external_or_vendor_cache"
    },
    {
      "absolute_path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\data\\external\\normalized\\fred\\DGS10_observations_20260430T220916Z.jsonl",
      "catalog_row_id": "LCAT-000978",
      "sha256": "fa15cd8ec91de758cff914435fe15f8f8533dae36c60d1e61cec81b33f8086de",
      "size_bytes": 4365,
      "source_family": "local_external_or_vendor_cache"
    },
    {
      "absolute_path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\data\\external\\normalized\\fred\\DGS10_observations_20260430T234724Z.jsonl",
      "catalog_row_id": "LCAT-000979",
      "sha256": "8d48b733b561d57218ccf1f90b8695b5cae9d1585261699be27f50b4a7da480c",
      "size_bytes": 234526,
      "source_family": "local_external_or_vendor_cache"
    },
    {
      "absolute_path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\data\\external\\normalized\\fred\\DGS10_observations_20260501T000730Z.jsonl",
      "catalog_row_id": "LCAT-000980",
      "sha256": "5c2854cb0f19021dca9b0202249b1bd425712db22f47193394074898433d3d9c",
      "size_bytes": 352966,
      "source_family": "local_external_or_vendor_cache"
    },
    {
      "absolute_path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\data\\external\\normalized\\fred\\DGS2_observations_20260430T234724Z.jsonl",
      "catalog_row_id": "LCAT-000981",
      "sha256": "840ad232007705216c1dfb4c4d1b7b4650db8e5b98d704882227c4f1cc2d4ca9",
      "size_bytes": 233387,
      "source_family": "local_external_or_vendor_cache"
    },
    {
      "absolute_path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\data\\external\\normalized\\fred\\DGS2_observations_20260501T000730Z.jsonl",
      "catalog_row_id": "LCAT-000982",
      "sha256": "e4cc2262bc993a8fc9368707dfd10e6eca13401459c4ba55722c0075eadc5f45",
      "size_bytes": 351827,
      "source_family": "local_external_or_vendor_cache"
    },
    {
      "absolute_path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\data\\external\\normalized\\fred\\DTWEXBGS_observations_20260430T234726Z.jsonl",
      "catalog_row_id": "LCAT-000983",
      "sha256": "c8fb196c6859db4c454d3d6d71a2e8a47213857aed53b1f7a1d81d4b9bf83d66",
      "size_bytes": 241566,
      "source_family": "local_external_or_vendor_cache"
    },
    {
      "absolute_path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\data\\external\\normalized\\fred\\DTWEXBGS_observations_20260501T000732Z.jsonl",
      "catalog_row_id": "LCAT-000984",
      "sha256": "07f1055791470e274d0bdfce1ea4c11e34440aee4a3fa2742e5b9c2eaf9f3fe9",
      "size_bytes": 359691,
      "source_family": "local_external_or_vendor_cache"
    },
    {
      "absolute_path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\data\\external\\normalized\\fred\\GVZCLS_observations_20260430T234726Z.jsonl",
      "catalog_row_id": "LCAT-000985",
      "sha256": "bd9ccbe4f403f01e8e08d8e97becefd89ae1555b0bce5f4f83f327bb3af960a4",
      "size_bytes": 236735,
      "source_family": "local_external_or_vendor_cache"
    },
    {
      "absolute_path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\data\\external\\normalized\\fred\\GVZCLS_observations_20260501T000732Z.jsonl",
      "catalog_row_id": "LCAT-000986",
      "sha256": "b791f8dc873062b052e8fca6c27a817d9aa19bd6f7fc1f1fed0c193c26b70807",
      "size_bytes": 355175,
      "source_family": "local_external_or_vendor_cache"
    },
    {
      "absolute_path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\data\\external\\normalized\\fred\\T10YIE_observations_20260430T234725Z.jsonl",
      "catalog_row_id": "LCAT-000987",
      "sha256": "38434c9014184510f69a576379dcac95015decbc9c62c6f32798186fc4b04f63",
      "size_bytes": 235869,
      "source_family": "local_external_or_vendor_cache"
    },
    {
      "absolute_path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\data\\external\\normalized\\fred\\T10YIE_observations_20260501T000731Z.jsonl",
      "catalog_row_id": "LCAT-000988",
      "sha256": "978344106a334b085933a95fd27957fdf25fa01f3ab710fd44cbdcc1bad7b1e1",
      "size_bytes": 354414,
      "source_family": "local_external_or_vendor_cache"
    },
    {
      "absolute_path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\data\\external\\normalized\\fred\\VIXCLS_observations_20260430T234726Z.jsonl",
      "catalog_row_id": "LCAT-000989",
      "sha256": "e6fc00ad0d31d609023239303880451870708f41499daf6d39217309d3eabaa1",
      "size_bytes": 236741,
      "source_family": "local_external_or_vendor_cache"
    },
    {
      "absolute_path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\data\\external\\normalized\\fred\\VIXCLS_observations_20260501T000732Z.jsonl",
      "catalog_row_id": "LCAT-000990",
      "sha256": "373b877a3a0e1d3ec7cc4d485ab1a4e9efa286415a19ce0bd195bcac44e9af7a",
      "size_bytes": 355181,
      "source_family": "local_external_or_vendor_cache"
    },
    {
      "absolute_path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\data\\external\\normalized\\lbma_calendar\\fix_calendar_20260430T220916Z.jsonl",
      "catalog_row_id": "LCAT-000991",
      "sha256": "deb6415b4290f2e52ccf34a0f4daa09e70730dca61cd904c70609d24a8bf64bb",
      "size_bytes": 698,
      "source_family": "local_external_or_vendor_cache"
    },
    {
      "absolute_path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\data\\external\\normalized\\lbma_calendar\\fix_calendar_20260430T234700Z.jsonl",
      "catalog_row_id": "LCAT-000992",
      "sha256": "949785c362f3b003a52ebfc916842409062e3376fdf63a5ab8d0a88d80aa0616",
      "size_bytes": 184925,
      "source_family": "local_external_or_vendor_cache"
    },
    {
      "absolute_path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\data\\external\\normalized\\lbma_calendar\\fix_calendar_20260430T234825Z.jsonl",
      "catalog_row_id": "LCAT-000993",
      "sha256": "949785c362f3b003a52ebfc916842409062e3376fdf63a5ab8d0a88d80aa0616",
      "size_bytes": 184925,
      "source_family": "local_external_or_vendor_cache"
    },
    {
      "absolute_path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\data\\external\\normalized\\lbma_calendar\\fix_calendar_20260501T000949Z.jsonl",
      "catalog_row_id": "LCAT-000994",
      "sha256": "24a433cbaaf20a28611d843ff563fe258af0dd0593f65af0ada1dcecc4d1507d",
      "size_bytes": 103244,
      "source_family": "local_external_or_vendor_cache"
    },
    {
      "absolute_path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\data\\external\\normalized\\wgc\\gold_demand_trends_20260430T225431Z.jsonl",
      "catalog_row_id": "LCAT-000995",
      "sha256": "0dee188de0c70951a456d54e08b307c8acc5a8bb04198bd1314cd7d1af9c54ae",
      "size_bytes": 5589049,
      "source_family": "local_external_or_vendor_cache"
    },
    {
      "absolute_path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\data\\external\\normalized\\wgc\\gold_demand_trends_20260430T234945Z.jsonl",
      "catalog_row_id": "LCAT-000996",
      "sha256": "5e4012fcdb512325bfc574eef585d8e1507d0d8b65d549633bc724f6335b71d1",
      "size_bytes": 5589049,
      "source_family": "local_external_or_vendor_cache"
    },
    {
      "absolute_path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\data\\external\\normalized\\wgc\\gold_etf_flows_20260430T224531Z.jsonl",
      "catalog_row_id": "LCAT-000997",
      "sha256": "d5372ca263dd0ebfc1b5a36230659725f3bd97a9e6451c336b673423e2c74341",
      "size_bytes": 50229,
      "source_family": "local_external_or_vendor_cache"
    },
    {
      "absolute_path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\data\\external\\normalized\\wgc\\gold_etf_flows_20260430T234945Z.jsonl",
      "catalog_row_id": "LCAT-000998",
      "sha256": "76abf4d657e0e96d9dc207fc8f03f568c6cf55aae29f8a44f0a23c1df3b14492",
      "size_bytes": 50229,
      "source_family": "local_external_or_vendor_cache"
    },
    {
      "absolute_path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\data\\external\\raw\\cftc_cot\\disagg_combined_20260430T220916Z.json",
      "catalog_row_id": "LCAT-000999",
      "sha256": "6e643c1aac981c97c3472f0113f7fe670431e63f287bd36aefe64f15104b6356",
      "size_bytes": 136287,
      "source_family": "local_external_or_vendor_cache"
    },
    {
      "absolute_path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\data\\external\\raw\\cftc_cot\\disagg_combined_20260430T220916Z.json.meta.json",
      "catalog_row_id": "LCAT-001000",
      "sha256": "5215bb87e7493e9fe4834e9a9b7f60e29c1736e1081a8b8d4b8d77b8cdd71f28",
      "size_bytes": 335,
      "source_family": "local_external_or_vendor_cache"
    },
    {
      "absolute_path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\data\\external\\raw\\cftc_cot\\disagg_combined_20260430T234727Z.json.meta.json",
      "catalog_row_id": "LCAT-001002",
      "sha256": "1b82104908f4bc30cd662b9c8490e835781eef7a7a59eda8436283e7a695dab5",
      "size_bytes": 338,
      "source_family": "local_external_or_vendor_cache"
    },
    {
      "absolute_path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\data\\external\\raw\\cftc_cot\\disagg_combined_20260501T000733Z.json.meta.json",
      "catalog_row_id": "LCAT-001004",
      "sha256": "ed5dca0849afb9972bc11ddbb3a7daa1bed280ab04e01e7a499f6723c048f9b2",
      "size_bytes": 338,
      "source_family": "local_external_or_vendor_cache"
    },
    {
      "absolute_path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\data\\external\\raw\\databento\\GLBX.MDP3\\mbo\\GLBX.MDP3.mbo.NQ.v.0.2026-04-28T00_00_00_00_00_2026-04-28T17_00_00_00_00.full.dbn.zst.meta.json",
      "catalog_row_id": "LCAT-001005",
      "sha256": "1f6ecc901f8aa0a150ecd68737fd5a10a56dc6fcaaaf97238eae4656b62e4cee",
      "size_bytes": 667,
      "source_family": "local_external_or_vendor_cache"
    },
    {
      "absolute_path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\data\\external\\raw\\databento\\GLBX.MDP3\\mbo\\GLBX.MDP3.mbo.NQ.v.0.2026-04-29T00_00_00_00_00_2026-04-29T17_00_00_00_00.full.dbn.zst.meta.json",
      "catalog_row_id": "LCAT-001006",
      "sha256": "e56804138e835eb45b226d7b01c416826aedf4b79f3068dcffcf33c0d9c054d7",
      "size_bytes": 666,
      "source_family": "local_external_or_vendor_cache"
    },
    {
      "absolute_path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\data\\external\\raw\\databento\\GLBX.MDP3\\mbo\\GLBX.MDP3.mbo.NQ.v.0.2026-05-01T00_00_00_00_00_2026-05-01T08_15_00_00_00.full.dbn.zst.meta.json",
      "catalog_row_id": "LCAT-001007",
      "sha256": "f32a2e94dd243ae4735a63f4a87f0729303b76dcf31148458731ed47e0690277",
      "size_bytes": 664,
      "source_family": "local_external_or_vendor_cache"
    },
    {
      "absolute_path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\data\\external\\raw\\databento\\GLBX.MDP3\\mbp-1\\GLBX.MDP3.mbp-1.GC.v.0.2026-04-17T12_15_00_00_00_2026-04-17T14_30_00_00_00.full.dbn.zst.meta.json",
      "catalog_row_id": "LCAT-001008",
      "sha256": "1e813d04becf830a22d3e5633d1ddedad488c8c3b9c6a0842de8a45847d4bce5",
      "size_bytes": 669,
      "source_family": "local_external_or_vendor_cache"
    },
    {
      "absolute_path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\data\\external\\raw\\databento\\GLBX.MDP3\\mbp-1\\GLBX.MDP3.mbp-1.NQ.v.0.2026-04-28T06_15_00_00_00_2026-04-28T11_30_00_00_00.full.dbn.zst.meta.json",
      "catalog_row_id": "LCAT-001009",
      "sha256": "8e47d0a892721b944e7e64ee4a585e948fc18740ef4cce80f44bef4af00b7b84",
      "size_bytes": 670,
      "source_family": "local_external_or_vendor_cache"
    },
    {
      "absolute_path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\data\\external\\raw\\databento\\GLBX.MDP3\\mbp-1\\GLBX.MDP3.mbp-1.NQ.v.0.2026-04-28T12_15_00_00_00_2026-04-28T18_00_00_00_00.full.dbn.zst.meta.json",
      "catalog_row_id": "LCAT-001010",
      "sha256": "a5e73e42fe0230348a9f9951d40a350b0bdf0b403b0c57b8eb9b2b433419e399",
      "size_bytes": 671,
      "source_family": "local_external_or_vendor_cache"
    },
    {
      "absolute_path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\data\\external\\raw\\databento\\GLBX.MDP3\\mbp-1\\GLBX.MDP3.mbp-1.NQ.v.0.2026-04-29T12_15_00_00_00_2026-04-29T18_00_00_00_00.full.dbn.zst.meta.json",
      "catalog_row_id": "LCAT-001011",
      "sha256": "844324bde7df98c9cfeb38deafd1711bc2d3adf81ba4f46535696762518c8271",
      "size_bytes": 671,
      "source_family": "local_external_or_vendor_cache"
    },
    {
      "absolute_path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\data\\external\\raw\\databento\\GLBX.MDP3\\mbp-10\\GLBX.MDP3.mbp-10.6B.v.0.2026-04-17T06_15_00_00_00_2026-04-17T09_00_00_00_00.full.dbn.zst.meta.json",
      "catalog_row_id": "LCAT-001012",
      "sha256": "a6c934a465b148d370532d139480ddd116d052c4bd07c784c6335e7b84f40cf6",
      "size_bytes": 671,
      "source_family": "local_external_or_vendor_cache"
    },
    {
      "absolute_path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\data\\external\\raw\\databento\\GLBX.MDP3\\mbp-10\\GLBX.MDP3.mbp-10.6B.v.0.2026-04-17T07_00_00_00_00_2026-04-17T08_15_00_00_00.full.dbn.zst.meta.json",
      "catalog_row_id": "LCAT-001013",
      "sha256": "caae7f6565dc23e3667454cf47be7c55c65d24ab16e621faae8ec475ac7bfbbc",
      "size_bytes": 671,
      "source_family": "local_external_or_vendor_cache"
    },
    {
      "absolute_path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\data\\external\\raw\\databento\\GLBX.MDP3\\mbp-10\\GLBX.MDP3.mbp-10.6B.v.0.2026-04-17T09_30_00_00_00_2026-04-17T15_15_00_00_00.full.dbn.zst.meta.json",
      "catalog_row_id": "LCAT-001014",
      "sha256": "a56fcc8d4b22213816f7222b0da580fedaa3fa04953ce74371c5efe950cc0341",
      "size_bytes": 673,
      "source_family": "local_external_or_vendor_cache"
    },
    {
      "absolute_path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\data\\external\\raw\\databento\\GLBX.MDP3\\mbp-10\\GLBX.MDP3.mbp-10.6B.v.0.2026-04-17T12_30_00_00_00_2026-04-17T14_30_00_00_00.full.dbn.zst.meta.json",
      "catalog_row_id": "LCAT-001015",
      "sha256": "61ccc04c0a8dc1423c765eada28281341b9aab9470b80cf27f00e57e54ade2b9",
      "size_bytes": 673,
      "source_family": "local_external_or_vendor_cache"
    },
    {
      "absolute_path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\data\\external\\raw\\databento\\GLBX.MDP3\\mbp-10\\GLBX.MDP3.mbp-10.6B.v.0.2026-04-29T06_15_00_00_00_2026-04-29T16_30_00_00_00.full.dbn.zst.meta.json",
      "catalog_row_id": "LCAT-001016",
      "sha256": "b7990c569c38a5df301cac95c4235cb113bd6315a341c3cc0f6c488be552d5e1",
      "size_bytes": 672,
      "source_family": "local_external_or_vendor_cache"
    },
    {
      "absolute_path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\data\\external\\raw\\databento\\GLBX.MDP3\\mbp-10\\GLBX.MDP3.mbp-10.6B.v.0.2026-04-29T07_00_00_00_00_2026-04-29T08_15_00_00_00.full.dbn.zst.meta.json",
      "catalog_row_id": "LCAT-001017",
      "sha256": "42f3a16cf8bf64c20747c65aae19d9759b7e4dd03b61e69f7ae18b820c16307f",
      "size_bytes": 671,
      "source_family": "local_external_or_vendor_cache"
    },
    {
      "absolute_path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\data\\external\\raw\\databento\\GLBX.MDP3\\mbp-10\\GLBX.MDP3.mbp-10.6B.v.0.2026-04-29T09_00_00_00_00_2026-04-29T15_45_00_00_00.full.dbn.zst.meta.json",
      "catalog_row_id": "LCAT-001018",
      "sha256": "ebe0511c3da69da9e797f2b923de18566b97b4a4983c9c3a4f7e77aea6e53e58",
      "size_bytes": 673,
      "source_family": "local_external_or_vendor_cache"
    },
    {
      "absolute_path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\data\\external\\raw\\databento\\GLBX.MDP3\\mbp-10\\GLBX.MDP3.mbp-10.GC.v.0.2026-04-17T06_15_00_00_00_2026-04-17T11_30_00_00_00.full.dbn.zst.meta.json",
      "catalog_row_id": "LCAT-001019",
      "sha256": "486c7b968f5bddc98e318a93624d90ed98f5c615e1cdbe3f3198fec7a731baa8",
      "size_bytes": 673,
      "source_family": "local_external_or_vendor_cache"
    },
    {
      "absolute_path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\data\\external\\raw\\databento\\GLBX.MDP3\\mbp-10\\GLBX.MDP3.mbp-10.GC.v.0.2026-04-17T12_15_00_00_00_2026-04-17T13_45_00_00_00.full.dbn.zst.meta.json",
      "catalog_row_id": "LCAT-001020",
      "sha256": "7e8b84bd3a244848f0d587a1edb27d2c161a9efb957f9f6430967d92567bd867",
      "size_bytes": 673,
      "source_family": "local_external_or_vendor_cache"
    },
    {
      "absolute_path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\data\\external\\raw\\databento\\GLBX.MDP3\\mbp-10\\GLBX.MDP3.mbp-10.GC.v.0.2026-04-17T12_15_00_00_00_2026-04-17T14_30_00_00_00.full.dbn.zst.meta.json",
      "catalog_row_id": "LCAT-001021",
      "sha256": "16cd69d5779a510685d30d2f29af2e75cc0a8aca495494c80615edfc6988885c",
      "size_bytes": 674,
      "source_family": "local_external_or_vendor_cache"
    },
    {
      "absolute_path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\data\\external\\raw\\databento\\GLBX.MDP3\\mbp-10\\GLBX.MDP3.mbp-10.GC.v.0.2026-04-19T15_15_00_00_00_2026-04-19T18_00_00_00_00.full.dbn.zst.meta.json",
      "catalog_row_id": "LCAT-001022",
      "sha256": "8abcf69deafd24154d112a3deb0efca47167f63caf7ff7b2192263bf4579cc67",
      "size_bytes": 649,
      "source_family": "local_external_or_vendor_cache"
    },
    {
      "absolute_path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\data\\external\\raw\\databento\\GLBX.MDP3\\mbp-10\\GLBX.MDP3.mbp-10.GC.v.0.2026-05-01T07_00_00_00_00_2026-05-01T09_15_00_00_00.full.dbn.zst.meta.json",
      "catalog_row_id": "LCAT-001023",
      "sha256": "86025a68eceeb896dc1cde46bceaac980bf67eb989c92988ca094f29dfcadd7a",
      "size_bytes": 672,
      "source_family": "local_external_or_vendor_cache"
    },
    {
      "absolute_path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\data\\external\\raw\\databento\\GLBX.MDP3\\mbp-10\\GLBX.MDP3.mbp-10.GC.v.0.2026-05-01T07_15_00_00_00_2026-05-01T08_30_00_00_00.full.dbn.zst.meta.json",
      "catalog_row_id": "LCAT-001024",
      "sha256": "3a580130f66ef07d5b4d2d3fe9dd2f77eaf42f096b408fec15a30591641c8ec9",
      "size_bytes": 672,
      "source_family": "local_external_or_vendor_cache"
    },
    {
      "absolute_path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\data\\external\\raw\\databento\\GLBX.MDP3\\mbp-10\\GLBX.MDP3.mbp-10.GC.v.0.2026-05-01T13_15_00_00_00_2026-05-01T16_00_00_00_00.full.dbn.zst.meta.json",
      "catalog_row_id": "LCAT-001025",
      "sha256": "01a0f3c6b128c52073006f5db84cd5b9f727bcd9b7e07e5b69355d55210dda26",
      "size_bytes": 673,
      "source_family": "local_external_or_vendor_cache"
    },
    {
      "absolute_path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\data\\external\\raw\\databento\\GLBX.MDP3\\mbp-10\\GLBX.MDP3.mbp-10.NQ.v.0.2026-04-28T06_15_00_00_00_2026-04-28T11_30_00_00_00.full.dbn.zst.meta.json",
      "catalog_row_id": "LCAT-001026",
      "sha256": "4ab57921ad22602a5529e81457c8557be3eb2ad1431955eb238a318eaab4b82d",
      "size_bytes": 674,
      "source_family": "local_external_or_vendor_cache"
    },
    {
      "absolute_path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\data\\external\\raw\\databento\\GLBX.MDP3\\mbp-10\\GLBX.MDP3.mbp-10.NQ.v.0.2026-04-28T06_30_00_00_00_2026-04-28T10_00_00_00_00.full.dbn.zst.meta.json",
      "catalog_row_id": "LCAT-001027",
      "sha256": "1095de58a6b9635ff36b77a5b0d935d1a1f2b2d6aac92b49ad6d7aa085dd29ab",
      "size_bytes": 674,
      "source_family": "local_external_or_vendor_cache"
    },
    {
      "absolute_path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\data\\external\\raw\\databento\\GLBX.MDP3\\mbp-10\\GLBX.MDP3.mbp-10.NQ.v.0.2026-04-28T12_15_00_00_00_2026-04-28T18_00_00_00_00.full.dbn.zst.meta.json",
      "catalog_row_id": "LCAT-001028",
      "sha256": "6c16a7c92269718a7a96c20cab48475f0cc208032f4f4c1ea92d8bbe16f31e63",
      "size_bytes": 676,
      "source_family": "local_external_or_vendor_cache"
    },
    {
      "absolute_path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\data\\external\\raw\\databento\\GLBX.MDP3\\mbp-10\\GLBX.MDP3.mbp-10.NQ.v.0.2026-04-28T13_45_00_00_00_2026-04-28T15_00_00_00_00.full.dbn.zst.meta.json",
      "catalog_row_id": "LCAT-001029",
      "sha256": "47c8937649211b61029c190284fbd4b9e25aa2e26d3cac8ea2d9e40e25048124",
      "size_bytes": 675,
      "source_family": "local_external_or_vendor_cache"
    },
    {
      "absolute_path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\data\\external\\raw\\databento\\GLBX.MDP3\\mbp-10\\GLBX.MDP3.mbp-10.NQ.v.0.2026-04-29T06_15_00_00_00_2026-04-29T11_30_00_00_00.full.dbn.zst.meta.json",
      "catalog_row_id": "LCAT-001030",
      "sha256": "23ed7c04c9e8898efd14b6a12ae6b0254e797ba7fff69160fff843e6606ded06",
      "size_bytes": 674,
      "source_family": "local_external_or_vendor_cache"
    },
    {
      "absolute_path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\data\\external\\raw\\databento\\GLBX.MDP3\\mbp-10\\GLBX.MDP3.mbp-10.NQ.v.0.2026-04-29T12_15_00_00_00_2026-04-29T18_00_00_00_00.full.dbn.zst.meta.json",
      "catalog_row_id": "LCAT-001031",
      "sha256": "1c5e59d4c69270449f1a19e243bacf86e7ec3cd252820254bb5b3c40817f76c9",
      "size_bytes": 676,
      "source_family": "local_external_or_vendor_cache"
    },
    {
      "absolute_path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\data\\external\\raw\\databento\\GLBX.MDP3\\mbp-10\\GLBX.MDP3.mbp-10.NQ.v.0.2026-04-29T13_45_00_00_00_2026-04-29T15_15_00_00_00.full.dbn.zst.meta.json",
      "catalog_row_id": "LCAT-001032",
      "sha256": "96e3c315d851c65ecf860ac00f4a1aa620eaf533f557068ac1ec7be19c0c43e6",
      "size_bytes": 675,
      "source_family": "local_external_or_vendor_cache"
    },
    {
      "absolute_path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\data\\external\\raw\\databento\\GLBX.MDP3\\mbp-10\\GLBX.MDP3.mbp-10.NQ.v.0.2026-04-30T12_45_00_00_00_2026-04-30T18_00_00_00_00.full.dbn.zst.meta.json",
      "catalog_row_id": "LCAT-001033",
      "sha256": "c628e4560c9a8cac02142d0e157a3562a4a24e885157c9e79d9d38b178fba366",
      "size_bytes": 676,
      "source_family": "local_external_or_vendor_cache"
    },
    {
      "absolute_path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\data\\external\\raw\\databento\\GLBX.MDP3\\mbp-10\\GLBX.MDP3.mbp-10.NQ.v.0.2026-05-01T07_00_00_00_00_2026-05-01T09_15_00_00_00.full.dbn.zst.meta.json",
      "catalog_row_id": "LCAT-001034",
      "sha256": "c9853bcba3a0f607fe814aa89940fc8e8a019c74ccb0c624eb4d57feaf484df2",
      "size_bytes": 673,
      "source_family": "local_external_or_vendor_cache"
    },
    {
      "absolute_path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\data\\external\\raw\\databento\\GLBX.MDP3\\mbp-10\\GLBX.MDP3.mbp-10.NQ.v.0.2026-05-01T07_15_00_00_00_2026-05-01T08_30_00_00_00.full.dbn.zst.meta.json",
      "catalog_row_id": "LCAT-001035",
      "sha256": "ff1e2ba93270c27f5e6b760f371a7eded7713c7a920cb94f97822a733b85c1cf",
      "size_bytes": 672,
      "source_family": "local_external_or_vendor_cache"
    },
    {
      "absolute_path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\data\\external\\raw\\databento\\GLBX.MDP3\\mbp-10\\GLBX.MDP3.mbp-10.SI.v.0.2026-05-01T07_00_00_00_00_2026-05-01T09_30_00_00_00.full.dbn.zst.meta.json",
      "catalog_row_id": "LCAT-001036",
      "sha256": "ad6fe86172d0c694fe2eae9e2ce107abafc60739606584547e021f3b722543ec",
      "size_bytes": 672,
      "source_family": "local_external_or_vendor_cache"
    },
    {
      "absolute_path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\data\\external\\raw\\databento\\GLBX.MDP3\\mbp-10\\GLBX.MDP3.mbp-10.SI.v.0.2026-05-01T07_15_00_00_00_2026-05-01T08_45_00_00_00.full.dbn.zst.meta.json",
      "catalog_row_id": "LCAT-001037",
      "sha256": "251175c000bac413291f90daac69dae282cecc5b5c52ef2f9e43fa2bda3b5c9b",
      "size_bytes": 671,
      "source_family": "local_external_or_vendor_cache"
    },
    {
      "absolute_path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\data\\external\\raw\\databento\\GLBX.MDP3\\mbp-10\\GLBX.MDP3.mbp-10.SI.v.0.2026-05-01T12_15_00_00_00_2026-05-01T16_00_00_00_00.full.dbn.zst.meta.json",
      "catalog_row_id": "LCAT-001038",
      "sha256": "846d38dfbc489269a0a355c0211019abf5e72f8c590e783af621814320e485eb",
      "size_bytes": 673,
      "source_family": "local_external_or_vendor_cache"
    },
    {
      "absolute_path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\data\\external\\raw\\databento\\GLBX.MDP3\\mbp-10\\GLBX.MDP3.mbp-10.SI.v.0.2026-05-01T12_30_00_00_00_2026-05-01T17_15_00_00_00.full.dbn.zst.meta.json",
      "catalog_row_id": "LCAT-001039",
      "sha256": "eff9811bf91d4b795bc8d529e928c35bb8d6038c0e83ba0ff7c7cd744e6cdd3b",
      "size_bytes": 673,
      "source_family": "local_external_or_vendor_cache"
    },
    {
      "absolute_path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\data\\external\\raw\\databento\\GLBX.MDP3\\mbp-10\\GLBX.MDP3.mbp-10.YM.v.0_ES.v.0.2026-04-17T07_15_00_00_00_2026-04-17T11_30_00_00_00.full.dbn.zst.meta.json",
      "catalog_row_id": "LCAT-001040",
      "sha256": "64a3e77d3cd0595d1ef2b52b98fa86a3a7fe08e42b4313534ac68beef43c3b3c",
      "size_bytes": 697,
      "source_family": "local_external_or_vendor_cache"
    },
    {
      "absolute_path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\data\\external\\raw\\databento\\GLBX.MDP3\\mbp-10\\GLBX.MDP3.mbp-10.YM.v.0_ES.v.0.2026-04-17T12_45_00_00_00_2026-04-17T17_00_00_00_00.full.dbn.zst.meta.json",
      "catalog_row_id": "LCAT-001041",
      "sha256": "d140c706ae87d8d5766122fd3ad23ffbc2b1740ba318fa9b71911a6c8aebf2a0",
      "size_bytes": 698,
      "source_family": "local_external_or_vendor_cache"
    },
    {
      "absolute_path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\data\\external\\raw\\databento\\GLBX.MDP3\\mbp-10\\GLBX.MDP3.mbp-10.YM.v.0_ES.v.0.2026-04-17T14_45_00_00_00_2026-04-17T16_00_00_00_00.full.dbn.zst.meta.json",
      "catalog_row_id": "LCAT-001042",
      "sha256": "50dbd0692bc72ffc9e6bec40dd834386cbf90fd64cfd6a06da176637740fd058",
      "size_bytes": 698,
      "source_family": "local_external_or_vendor_cache"
    },
    {
      "absolute_path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\data\\external\\raw\\databento\\GLBX.MDP3\\mbp-10\\GLBX.MDP3.mbp-10.YM.v.0_ES.v.0.2026-04-28T08_00_00_00_00_2026-04-28T11_30_00_00_00.full.dbn.zst.meta.json",
      "catalog_row_id": "LCAT-001043",
      "sha256": "3c905de133f1b5acc1e2b7f9704199f705ffb3e3ccf0a16ceb58efbbf62a0422",
      "size_bytes": 697,
      "source_family": "local_external_or_vendor_cache"
    },
    {
      "absolute_path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\data\\external\\raw\\databento\\GLBX.MDP3\\mbp-10\\GLBX.MDP3.mbp-10.YM.v.0_ES.v.0.2026-04-28T12_45_00_00_00_2026-04-28T17_00_00_00_00.full.dbn.zst.meta.json",
      "catalog_row_id": "LCAT-001044",
      "sha256": "40cbeb5335d42aa5df4bef7c07efe744b51f67fe366ee6fe0eec954afd0b2c2f",
      "size_bytes": 699,
      "source_family": "local_external_or_vendor_cache"
    },
    {
      "absolute_path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\data\\external\\raw\\databento\\GLBX.MDP3\\mbp-10\\GLBX.MDP3.mbp-10.YM.v.0_ES.v.0.2026-04-29T07_15_00_00_00_2026-04-29T11_30_00_00_00.full.dbn.zst.meta.json",
      "catalog_row_id": "LCAT-001045",
      "sha256": "ce13eaf87a63834e28ca0e44aa4ced77a109c345e13a31a431b68bad045cb0fe",
      "size_bytes": 697,
      "source_family": "local_external_or_vendor_cache"
    },
    {
      "absolute_path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\data\\external\\raw\\databento\\GLBX.MDP3\\mbp-10\\GLBX.MDP3.mbp-10.YM.v.0_ES.v.0.2026-04-29T13_15_00_00_00_2026-04-29T17_00_00_00_00.full.dbn.zst.meta.json",
      "catalog_row_id": "LCAT-001046",
      "sha256": "151ea8f761ac9cebd2233d254289fab0bb39a07ce1b9d15888a30a4f0391e898",
      "size_bytes": 699,
      "source_family": "local_external_or_vendor_cache"
    },
    {
      "absolute_path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\data\\external\\raw\\databento\\GLBX.MDP3\\mbp-10\\GLBX.MDP3.mbp-10.YM.v.0_ES.v.0.2026-04-30T12_45_00_00_00_2026-04-30T17_00_00_00_00.full.dbn.zst.meta.json",
      "catalog_row_id": "LCAT-001047",
      "sha256": "dac137e487f3e6e774cbad4e6c291bfeb0dbe293b2e0108af08ad3cb8d939822",
      "size_bytes": 699,
      "source_family": "local_external_or_vendor_cache"
    },
    {
      "absolute_path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\data\\external\\raw\\databento\\GLBX.MDP3\\mbp-10\\GLBX.MDP3.mbp-10.YM.v.0_ES.v.0.2026-05-01T07_15_00_00_00_2026-05-01T11_30_00_00_00.full.dbn.zst.meta.json",
      "catalog_row_id": "LCAT-001048",
      "sha256": "8a3b89b7e535b36b0993433b8e30cbdf744363dbb9e2e9c571f9b7a51b4179d9",
      "size_bytes": 697,
      "source_family": "local_external_or_vendor_cache"
    },
    {
      "absolute_path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\data\\external\\raw\\databento\\GLBX.MDP3\\mbp-10\\GLBX.MDP3.mbp-10.YM.v.0_ES.v.0.2026-05-01T12_45_00_00_00_2026-05-01T16_00_00_00_00.full.dbn.zst.meta.json",
      "catalog_row_id": "LCAT-001049",
      "sha256": "34677340880739b0b8922d3c57bef62521d455bab9b8dccd6cac5314c82b736b",
      "size_bytes": 699,
      "source_family": "local_external_or_vendor_cache"
    },
    {
      "absolute_path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\data\\external\\raw\\databento\\GLBX.MDP3\\trades\\GLBX.MDP3.trades.6B.v.0.2026-04-17T06_15_00_00_00_2026-04-17T09_00_00_00_00.full.dbn.zst.meta.json",
      "catalog_row_id": "LCAT-001050",
      "sha256": "dde06cec01943de0f3ef0c1e34a05a02ade0d500e2c037d2445480df43905ec4",
      "size_bytes": 667,
      "source_family": "local_external_or_vendor_cache"
    },
    {
      "absolute_path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\data\\external\\raw\\databento\\GLBX.MDP3\\trades\\GLBX.MDP3.trades.6B.v.0.2026-04-17T07_00_00_00_00_2026-04-17T08_15_00_00_00.full.dbn.zst.meta.json",
      "catalog_row_id": "LCAT-001051",
      "sha256": "f3d53fffb14f37f8b83b79655f3c4db24e1cb5bdb4247389eee1f83878687db9",
      "size_bytes": 665,
      "source_family": "local_external_or_vendor_cache"
    },
    {
      "absolute_path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\data\\external\\raw\\databento\\GLBX.MDP3\\trades\\GLBX.MDP3.trades.6B.v.0.2026-04-17T07_00_00_00_00_2026-04-17T09_00_00_00_00.full.dbn.zst.meta.json",
      "catalog_row_id": "LCAT-001052",
      "sha256": "ca5b64df856b5820d545f676c9fdf4c331e3be69db31e03f9356519436b8615f",
      "size_bytes": 667,
      "source_family": "local_external_or_vendor_cache"
    },
    {
      "absolute_path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\data\\external\\raw\\databento\\GLBX.MDP3\\trades\\GLBX.MDP3.trades.6B.v.0.2026-04-17T09_30_00_00_00_2026-04-17T15_15_00_00_00.full.dbn.zst.meta.json",
      "catalog_row_id": "LCAT-001053",
      "sha256": "417e89c7ec44e08978285de24cbaefeef108bebfd5dacb40148814db450cd42c",
      "size_bytes": 669,
      "source_family": "local_external_or_vendor_cache"
    },
    {
      "absolute_path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\data\\external\\raw\\databento\\GLBX.MDP3\\trades\\GLBX.MDP3.trades.6B.v.0.2026-04-17T12_30_00_00_00_2026-04-17T14_30_00_00_00.full.dbn.zst.meta.json",
      "catalog_row_id": "LCAT-001054",
      "sha256": "8bb03c447ae8500fd4338d34711ab860d8d2da17044625069a27843dfbf04a3a",
      "size_bytes": 668,
      "source_family": "local_external_or_vendor_cache"
    },
    {
      "absolute_path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\data\\external\\raw\\databento\\GLBX.MDP3\\trades\\GLBX.MDP3.trades.6B.v.0.2026-04-17T12_30_00_00_00_2026-04-17T15_15_00_00_00.full.dbn.zst.meta.json",
      "catalog_row_id": "LCAT-001055",
      "sha256": "cfa37f0a08f577573dc249cc98a20bc1ed22e54ba53714dc8948dd01ebf66009",
      "size_bytes": 668,
      "source_family": "local_external_or_vendor_cache"
    },
    {
      "absolute_path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\data\\external\\raw\\databento\\GLBX.MDP3\\trades\\GLBX.MDP3.trades.6B.v.0.2026-04-29T06_15_00_00_00_2026-04-29T16_30_00_00_00.full.dbn.zst.meta.json",
      "catalog_row_id": "LCAT-001056",
      "sha256": "1324c23472579ff95e7ab64cb603f145151b32ee494b8be7f9d15ad21c9c1be3",
      "size_bytes": 667,
      "source_family": "local_external_or_vendor_cache"
    },
    {
      "absolute_path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\data\\external\\raw\\databento\\GLBX.MDP3\\trades\\GLBX.MDP3.trades.6B.v.0.2026-04-29T07_00_00_00_00_2026-04-29T08_15_00_00_00.full.dbn.zst.meta.json",
      "catalog_row_id": "LCAT-001057",
      "sha256": "e18f94ca479a534ddfda4bb84d21fa536933db50f7c10419c5e5d842fa1e4f71",
      "size_bytes": 666,
      "source_family": "local_external_or_vendor_cache"
    },
    {
      "absolute_path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\data\\external\\raw\\databento\\GLBX.MDP3\\trades\\GLBX.MDP3.trades.6B.v.0.2026-04-29T07_00_00_00_00_2026-04-29T16_30_00_00_00.full.dbn.zst.meta.json",
      "catalog_row_id": "LCAT-001058",
      "sha256": "12c24e2a82e676523c8b2385445ab312aa56ec822fcc8892670d8870643b5268",
      "size_bytes": 668,
      "source_family": "local_external_or_vendor_cache"
    },
    {
      "absolute_path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\data\\external\\raw\\databento\\GLBX.MDP3\\trades\\GLBX.MDP3.trades.6B.v.0.2026-04-29T09_00_00_00_00_2026-04-29T15_45_00_00_00.full.dbn.zst.meta.json",
      "catalog_row_id": "LCAT-001059",
      "sha256": "a82cc8b7614c2434a2a08ad1d43c63b4ad198f6128a58896f2fef905d91cd6a2",
      "size_bytes": 667,
      "source_family": "local_external_or_vendor_cache"
    },
    {
      "absolute_path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\data\\external\\raw\\databento\\GLBX.MDP3\\trades\\GLBX.MDP3.trades.6J.v.0.2026-01-22T07_00_00_00_00_2026-01-22T17_00_00_00_00.full.dbn.zst.meta.json",
      "catalog_row_id": "LCAT-001060",
      "sha256": "7d03f537942e469ba9bee6b30051483b761673780c94b218f3d697828720a8cd",
      "size_bytes": 669,
      "source_family": "local_external_or_vendor_cache"
    },
    {
      "absolute_path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\data\\external\\raw\\databento\\GLBX.MDP3\\trades\\GLBX.MDP3.trades.6J.v.0.2026-02-12T07_00_00_00_00_2026-02-12T17_00_00_00_00.full.dbn.zst.meta.json",
      "catalog_row_id": "LCAT-001061",
      "sha256": "82c285afb04383160981ce96575c12c32cd474553bb561b30b127f7013c1dd1d",
      "size_bytes": 670,
      "source_family": "local_external_or_vendor_cache"
    },
    {
      "absolute_path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\data\\external\\raw\\databento\\GLBX.MDP3\\trades\\GLBX.MDP3.trades.6J.v.0.2026-03-06T07_00_00_00_00_2026-03-06T17_00_00_00_00.full.dbn.zst.meta.json",
      "catalog_row_id": "LCAT-001062",
      "sha256": "25628817bc6bd048b67a3e3153cffee1a58daa5ac9b30a81003aeb5083d395f3",
      "size_bytes": 670,
      "source_family": "local_external_or_vendor_cache"
    },
    {
      "absolute_path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\data\\external\\raw\\databento\\GLBX.MDP3\\trades\\GLBX.MDP3.trades.6J.v.0.2026-03-09T07_00_00_00_00_2026-03-09T17_00_00_00_00.full.dbn.zst.meta.json",
      "catalog_row_id": "LCAT-001063",
      "sha256": "0c2517d311cf9b75847a69b15f4549e64dada5463103594fd434d9dcfce42fb6",
      "size_bytes": 669,
      "source_family": "local_external_or_vendor_cache"
    },
    {
      "absolute_path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\data\\external\\raw\\databento\\GLBX.MDP3\\trades\\GLBX.MDP3.trades.6J.v.0.2026-03-16T07_00_00_00_00_2026-03-16T17_00_00_00_00.full.dbn.zst.meta.json",
      "catalog_row_id": "LCAT-001064",
      "sha256": "fea09f0086403a348163f835c10985409567f09156e91fa55132dc2b157696b4",
      "size_bytes": 669,
      "source_family": "local_external_or_vendor_cache"
    },
    {
      "absolute_path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\data\\external\\raw\\databento\\GLBX.MDP3\\trades\\GLBX.MDP3.trades.6J.v.0.2026-04-02T07_00_00_00_00_2026-04-02T17_00_00_00_00.full.dbn.zst.meta.json",
      "catalog_row_id": "LCAT-001065",
      "sha256": "4e570d8b3dcf776cebd71eea2e9bed447462078d178fc0cbf3bc80397d56b497",
      "size_bytes": 669,
      "source_family": "local_external_or_vendor_cache"
    },
    {
      "absolute_path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\data\\external\\raw\\databento\\GLBX.MDP3\\trades\\GLBX.MDP3.trades.ALL_SYMBOLS.2026-04-24T00_30_2026-05-01T16_00.limit100.dbn.zst.meta.json",
      "catalog_row_id": "LCAT-001066",
      "sha256": "c8801da4243299f9d04e907b189734fd6295e765df23e4a4ae66eea3c17d0a2d",
      "size_bytes": 626,
      "source_family": "local_external_or_vendor_cache"
    },
    {
      "absolute_path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\data\\external\\raw\\databento\\GLBX.MDP3\\trades\\GLBX.MDP3.trades.ES.v.0_NQ.v.0_GC.v.0_YM.v.0_CL.v.0.2026-01-15T00_00_2026-01-16T00_00.full.dbn.zst.meta.json",
      "catalog_row_id": "LCAT-001067",
      "sha256": "3fc9da543ccfbd58e9e366780d7a779ef77d63bed46889691e8ab99542e90005",
      "size_bytes": 733,
      "source_family": "local_external_or_vendor_cache"
    },
    {
      "absolute_path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\data\\external\\raw\\databento\\GLBX.MDP3\\trades\\GLBX.MDP3.trades.ES.v.0_NQ.v.0_GC.v.0_YM.v.0_CL.v.0.2026-02-12T00_00_2026-02-13T00_00.full.dbn.zst.meta.json",
      "catalog_row_id": "LCAT-001068",
      "sha256": "78371d2707f3b163a0daf1c5aea1583d685609c59db8ae6e1e290170ff27b961",
      "size_bytes": 733,
      "source_family": "local_external_or_vendor_cache"
    },
    {
      "absolute_path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\data\\external\\raw\\databento\\GLBX.MDP3\\trades\\GLBX.MDP3.trades.ES.v.0_NQ.v.0_GC.v.0_YM.v.0_CL.v.0.2026-03-13T00_00_2026-03-14T00_00.full.dbn.zst.meta.json",
      "catalog_row_id": "LCAT-001069",
      "sha256": "94436c9ac7fbf54de2aea020f7782b894b2e7c066fc0609822dba3836c279ad6",
      "size_bytes": 733,
      "source_family": "local_external_or_vendor_cache"
    },
    {
      "absolute_path": "C:\\tmp\\gtos_otb\\G0FWDCAPREADY\\AGENTS.md",
      "catalog_row_id": "LCAT-001070",
      "sha256": "21c3221e3c018793a40f264e52d7265d0e69aee892995fbaff70cc300fdaf257",
      "size_bytes": 37009,
      "source_family": "prior_worktree_lead"
    },
    {
      "absolute_path": "C:\\tmp\\gtos_otb\\G0FWDCAPREADY\\CEO_DIRECTIVE_COMPLETION_REPORT.md",
      "catalog_row_id": "LCAT-001071",
      "sha256": "706d0daa25113fec220d8c0409dbdbf14b61b9701e4edf4b4478f0bcef64d269",
      "size_bytes": 1662,
      "source_family": "prior_worktree_lead"
    },
    {
      "absolute_path": "C:\\tmp\\gtos_otb\\G0FWDCAPREADY\\CLAUDE.md",
      "catalog_row_id": "LCAT-001072",
      "sha256": "9bc018176b05a258e684d21806c0cbdfa56202a4452d3b8f97d3f9b144f8e419",
      "size_bytes": 33556,
      "source_family": "prior_worktree_lead"
    },
    {
      "absolute_path": "C:\\tmp\\gtos_otb\\G0FWDCAPREADY\\COMPREHENSIVE_STATUS_REPORT.md",
      "catalog_row_id": "LCAT-001073",
      "sha256": "d064ba59f4f457baf1ef62cb0e8ab72021f01cc77e4700b7868eb9c7fc452144",
      "size_bytes": 7472,
      "source_family": "prior_worktree_lead"
    },
    {
      "absolute_path": "C:\\tmp\\gtos_otb\\G0FWDCAPREADY\\CORRECTED_INTELLIGENCE_BRIEF_APRIL7.md",
      "catalog_row_id": "LCAT-001074",
      "sha256": "511d024e24349ed81465a5a4fbb8e84bf26ad1f1eacf45a84b31206c04f1c968",
      "size_bytes": 5032,
      "source_family": "prior_worktree_lead"
    },
    {
      "absolute_path": "C:\\tmp\\gtos_otb\\G0FWDCAPREADY\\DATA_VERIFICATION_MATRIX.md",
      "catalog_row_id": "LCAT-001075",
      "sha256": "4d27b5a73345aabbf39157a4b6df3f4258ef3fbbc826a3a9a1a794ba925a8f74",
      "size_bytes": 11668,
      "source_family": "prior_worktree_lead"
    },
    {
      "absolute_path": "C:\\tmp\\gtos_otb\\G0FWDCAPREADY\\DIVERGENCE_SAMPLER_REPORT.md",
      "catalog_row_id": "LCAT-001076",
      "sha256": "daa2156a77cca897820b6f0053ff78a81f7da99744bcba79af4a5a9d4720f2a0",
      "size_bytes": 8642,
      "source_family": "prior_worktree_lead"
    },
    {
      "absolute_path": "C:\\tmp\\gtos_otb\\G0FWDCAPREADY\\EMPTY_SYMBOL_FIX_REPORT.md",
      "catalog_row_id": "LCAT-001077",
      "sha256": "2b428e699c350b043a441c291020c1d1bcf665849c07e1a4a087cbf6d8132249",
      "size_bytes": 8973,
      "source_family": "prior_worktree_lead"
    },
    {
      "absolute_path": "C:\\tmp\\gtos_otb\\G0FWDCAPREADY\\EVIDENCE_LOCATION_REPORT_APRIL7.md",
      "catalog_row_id": "LCAT-001078",
      "sha256": "83104313d994152c2b00d40e3a37223490167e495f558acb85cc3a841a9aa9d5",
      "size_bytes": 4718,
      "source_family": "prior_worktree_lead"
    },
    {
      "absolute_path": "C:\\tmp\\gtos_otb\\G0FWDCAPREADY\\EXECUTIVE_SUMMARY_APRIL7_IMPROVEMENTS.md",
      "catalog_row_id": "LCAT-001079",
      "sha256": "0032d7e874dd93acca432f5572fcda25a79cddac53ac2aa9fa7dd9f2615118b5",
      "size_bytes": 5121,
      "source_family": "prior_worktree_lead"
    },
    {
      "absolute_path": "C:\\tmp\\gtos_otb\\G0FWDCAPREADY\\F2.3_HANDOFF.md",
      "catalog_row_id": "LCAT-001080",
      "sha256": "c313d95a1acbf1b7d60a3e0e3399902b2d3eab908ea8b4164694246fdde8e46c",
      "size_bytes": 8507,
      "source_family": "prior_worktree_lead"
    },
    {
      "absolute_path": "C:\\tmp\\gtos_otb\\G0FWDCAPREADY\\GUARANTEED_IMPROVEMENTS_VALIDATION_MATRIX.md",
      "catalog_row_id": "LCAT-001081",
      "sha256": "55ea09ce2aacd475a2f0cbebd9ddde7c84ce3f16b75510d9677150f194619307",
      "size_bytes": 7667,
      "source_family": "prior_worktree_lead"
    },
    {
      "absolute_path": "C:\\tmp\\gtos_otb\\G0FWDCAPREADY\\IMPLEMENTATION_SUMMARY.md",
      "catalog_row_id": "LCAT-001082",
      "sha256": "312f95fd5ab90cdf541a3befe7e292fa69a0d6e00b8d3652744bfbe3ec6a26a5",
      "size_bytes": 7769,
      "source_family": "prior_worktree_lead"
    },
    {
      "absolute_path": "C:\\tmp\\gtos_otb\\G0FWDCAPREADY\\KNOWLEDGE_INVESTMENT_REMOVAL_CHECKLIST.md",
      "catalog_row_id": "LCAT-001083",
      "sha256": "379d9d4f37463ec6cf44aa20fac1eafb76d79d32bc55f1bdeb068ead7a4e030b",
      "size_bytes": 2490,
      "source_family": "prior_worktree_lead"
    },
    {
      "absolute_path": "C:\\tmp\\gtos_otb\\G0FWDCAPREADY\\LIVE_CANDIDATE_INVERTED_TP_ANALYSIS.md",
      "catalog_row_id": "LCAT-001084",
      "sha256": "b87b03ee6f95c3e02130938360303b2125f392e64d29daca79e8901344d7fd6c",
      "size_bytes": 6253,
      "source_family": "prior_worktree_lead"
    },
    {
      "absolute_path": "C:\\tmp\\gtos_otb\\G0FWDCAPREADY\\MERGE_NOTES.md",
      "catalog_row_id": "LCAT-001085",
      "sha256": "dc55f828c8d5622a1361797f17647f13bf5d5fcb14a82e97be6b55c1cac571fb",
      "size_bytes": 7698,
      "source_family": "prior_worktree_lead"
    },
    {
      "absolute_path": "C:\\tmp\\gtos_otb\\G0FWDCAPREADY\\ORCHESTRATION_STATUS_REPORT_20260407.md",
      "catalog_row_id": "LCAT-001086",
      "sha256": "a13c3323ef102ed8be185af3aeece1b637ba79d30c3d6f54801edb4371325758",
      "size_bytes": 9245,
      "source_family": "prior_worktree_lead"
    },
    {
      "absolute_path": "C:\\tmp\\gtos_otb\\G0FWDCAPREADY\\PHASE1_SYNTHESIS.md",
      "catalog_row_id": "LCAT-001087",
      "sha256": "31f9998218722de5a2ce658520cc3496d8ca391e273e94314dc11754f87948c7",
      "size_bytes": 19995,
      "source_family": "prior_worktree_lead"
    },
    {
      "absolute_path": "C:\\tmp\\gtos_otb\\G0FWDCAPREADY\\README.md",
      "catalog_row_id": "LCAT-001088",
      "sha256": "4034c8a7f9eac366256e7850dd597b699538731a5fc23a6f2932cd415aa6c090",
      "size_bytes": 2312,
      "source_family": "prior_worktree_lead"
    },
    {
      "absolute_path": "C:\\tmp\\gtos_otb\\G0FWDCAPREADY\\RED_TEAM_100_PERCENT.md",
      "catalog_row_id": "LCAT-001089",
      "sha256": "9277da81c85664a1142e18f05ccc1c49b1b08f88b5ebafeb4c4883d64fcb2f82",
      "size_bytes": 7668,
      "source_family": "prior_worktree_lead"
    },
    {
      "absolute_path": "C:\\tmp\\gtos_otb\\G0FWDCAPREADY\\TP_INVERSION_BUG_REPORT.md",
      "catalog_row_id": "LCAT-001090",
      "sha256": "0cc6638e9da994bd3bc4c6caba4c5420281a59680dd0cc87c9a99110fdd3a65c",
      "size_bytes": 4516,
      "source_family": "prior_worktree_lead"
    },
    {
      "absolute_path": "C:\\tmp\\gtos_otb\\G0FWDCAPREADY\\ULTRAPLAN_APR9_2026.md",
      "catalog_row_id": "LCAT-001091",
      "sha256": "265aec8a0357ec260a944e8ce835acff676c6019849f90a33990ebe0e1fed5bb",
      "size_bytes": 30066,
      "source_family": "prior_worktree_lead"
    },
    {
      "absolute_path": "C:\\tmp\\gtos_otb\\G0FWDCAPREADY\\WAVE1_F2.1_REPORT.md",
      "catalog_row_id": "LCAT-001092",
      "sha256": "47651750d0135e6c1eabe4a28fdc34cba4f75de621f91b2e9340fa7beb2a195a",
      "size_bytes": 19127,
      "source_family": "prior_worktree_lead"
    },
    {
      "absolute_path": "C:\\tmp\\gtos_otb\\G0FWDCAPREADY\\WAVE1_R1_REPORT.md",
      "catalog_row_id": "LCAT-001093",
      "sha256": "c065835fba41af1310bc689f154338d9c07179c35e39085e51daeaf21f12565a",
      "size_bytes": 24157,
      "source_family": "prior_worktree_lead"
    },
    {
      "absolute_path": "C:\\tmp\\gtos_otb\\G0FWDCAPREADY\\WAVE1_R2_REPORT.md",
      "catalog_row_id": "LCAT-001094",
      "sha256": "e4dc7aaa0b10fef9336c10bcc54b371491d44da2b32ba729f8eec13c4737ca98",
      "size_bytes": 13253,
      "source_family": "prior_worktree_lead"
    },
    {
      "absolute_path": "C:\\tmp\\gtos_otb\\G0FWDCAPREADY\\WAVE1_R3_REPORT.md",
      "catalog_row_id": "LCAT-001095",
      "sha256": "c21f1175c65e19be76bc7852db90e9ee9cb6990414f6f98e914037d0c1e731e3",
      "size_bytes": 9694,
      "source_family": "prior_worktree_lead"
    },
    {
      "absolute_path": "C:\\tmp\\gtos_otb\\G0FWDCAPREADY\\WAVE1_R4_REPORT.md",
      "catalog_row_id": "LCAT-001096",
      "sha256": "9fdd908676800f304e35d30783e5833934e9b3751ceadeb057fc21b708eba1cc",
      "size_bytes": 7468,
      "source_family": "prior_worktree_lead"
    },
    {
      "absolute_path": "C:\\tmp\\gtos_otb\\G0FWDCAPREADY\\WAVE1_R5_REPORT.md",
      "catalog_row_id": "LCAT-001097",
      "sha256": "9ef0fd20e9d46c66a75ef064e05985c0f69abbc41494ef3a2f2dbad72f711446",
      "size_bytes": 7894,
      "source_family": "prior_worktree_lead"
    },
    {
      "absolute_path": "C:\\tmp\\gtos_otb\\G0FWDCAPREADY\\WAVE1_R6_REPORT.md",
      "catalog_row_id": "LCAT-001098",
      "sha256": "615fe9850a284d62038adb1563a77ce089f8d0ff63b9a10f0f34193f963eaa21",
      "size_bytes": 6995,
      "source_family": "prior_worktree_lead"
    },
    {
      "absolute_path": "C:\\tmp\\gtos_otb\\G0FWDCAPREADY\\WAVE2_F2_SWEEP_REPORT.md",
      "catalog_row_id": "LCAT-001099",
      "sha256": "14c825a4066376eef48f9898e0a1a4af7dc723c3913c0bf83f1cfeebdb6a879c",
      "size_bytes": 10858,
      "source_family": "prior_worktree_lead"
    },
    {
      "absolute_path": "C:\\tmp\\gtos_otb\\G0FWDCAPREADY\\WAVE2_F3_SYNTHESIS_REPORT.md",
      "catalog_row_id": "LCAT-001100",
      "sha256": "fee66d495d97c376ab560541635f70c5fe6e83fbb760ab92d6fe6454a64acaa8",
      "size_bytes": 17578,
      "source_family": "prior_worktree_lead"
    },
    {
      "absolute_path": "C:\\tmp\\gtos_otb\\G0FWDCAPREADY\\XAUUSD_M1.csv",
      "catalog_row_id": "LCAT-001101",
      "sha256": "e76034fc472b62bcb4968c40aea8e5f94b318d96b6ebaad6e3324be96847b79b",
      "size_bytes": 5645375,
      "source_family": "prior_worktree_lead"
    },
    {
      "absolute_path": "C:\\tmp\\gtos_otb\\G0FWDCAPREADY\\XAUUSD_M5.csv",
      "catalog_row_id": "LCAT-001102",
      "sha256": "358ae52806decee2967d301c006449144c3a6d8dd991c997512955f1c3b43d61",
      "size_bytes": 5670559,
      "source_family": "prior_worktree_lead"
    },
    {
      "absolute_path": "C:\\tmp\\gtos_otb\\G0FWDCAPREADY\\_f3_aggregator.py",
      "catalog_row_id": "LCAT-001103",
      "sha256": "8b1b33f07785a07abe8731ffcf1556dbb991ea277e64aaec21a21a56aa0f0b62",
      "size_bytes": 13779,
      "source_family": "prior_worktree_lead"
    },
    {
      "absolute_path": "C:\\tmp\\gtos_otb\\G0FWDCAPREADY\\asba.txt",
      "catalog_row_id": "LCAT-001104",
      "sha256": "1e5f738f37d40a12a2f8d601810277809aa9c4c3b174c213466e56fb24a87c33",
      "size_bytes": 354,
      "source_family": "prior_worktree_lead"
    },
    {
      "absolute_path": "C:\\tmp\\gtos_otb\\G0FWDCAPREADY\\autocorrelation_baselines.md",
      "catalog_row_id": "LCAT-001105",
      "sha256": "9702c4608ca472df0d85fbc2ccd9b3aefa6f5e32bba1ccda5e3813033ee1970d",
      "size_bytes": 2055,
      "source_family": "prior_worktree_lead"
    },
    {
      "absolute_path": "C:\\tmp\\gtos_otb\\G0FWDCAPREADY\\decomposition_raw_results.json",
      "catalog_row_id": "LCAT-001106",
      "sha256": "ea0e6ff763b67dd001da8998cf5d60a6daafe077251479b5735db88a354c4cf7",
      "size_bytes": 9167,
      "source_family": "prior_worktree_lead"
    },
    {
      "absolute_path": "C:\\tmp\\gtos_otb\\G0FWDCAPREADY\\decomposition_real_mso_test.md",
      "catalog_row_id": "LCAT-001107",
      "sha256": "2f60837f0109131729254f69fef82d2f0784a4ca68069d14b197c4d9533bf04d",
      "size_bytes": 6466,
      "source_family": "prior_worktree_lead"
    },
    {
      "absolute_path": "C:\\tmp\\gtos_otb\\G0FWDCAPREADY\\defaults_and_tests_audit.md",
      "catalog_row_id": "LCAT-001108",
      "sha256": "dba606459e91cdbbf955745f184fa45d4bae56b57b29d6bd28fbab993ce58e29",
      "size_bytes": 11942,
      "source_family": "prior_worktree_lead"
    },
    {
      "absolute_path": "C:\\tmp\\gtos_otb\\G0FWDCAPREADY\\demo_infrastructure.py",
      "catalog_row_id": "LCAT-001109",
      "sha256": "72ef77a51fed819cfd16a34d8ed5928f56c1ce9735538bb654286cff6ace646b",
      "size_bytes": 6144,
      "source_family": "prior_worktree_lead"
    },
    {
      "absolute_path": "C:\\tmp\\gtos_otb\\G0FWDCAPREADY\\devils_advocate_test_results.md",
      "catalog_row_id": "LCAT-001110",
      "sha256": "40a1e43c7ff6281faaa549f63679208cf0d551e9914aa1a5c04d2cd6bc7a7ce4",
      "size_bytes": 4677,
      "source_family": "prior_worktree_lead"
    },
    {
      "absolute_path": "C:\\tmp\\gtos_otb\\G0FWDCAPREADY\\dst_effect_analysis.md",
      "catalog_row_id": "LCAT-001111",
      "sha256": "93ab199436cf2451b53d4e10621b840f7e64d4c9e9c3c0f8d4b68c39e7c16a8c",
      "size_bytes": 2956,
      "source_family": "prior_worktree_lead"
    },
    {
      "absolute_path": "C:\\tmp\\gtos_otb\\G0FWDCAPREADY\\empirical_analysis_summary.md",
      "catalog_row_id": "LCAT-001112",
      "sha256": "9e2a1748bd6dcace4b50dffe2a72d78ff774bd86ac2b250435d9ec589d288fb8",
      "size_bytes": 10825,
      "source_family": "prior_worktree_lead"
    },
    {
      "absolute_path": "C:\\tmp\\gtos_otb\\G0FWDCAPREADY\\enhanced_inverted_analysis.py",
      "catalog_row_id": "LCAT-001113",
      "sha256": "72ec37a745fd7e196c0741b80f4495ce36bf09550a73b20224e555ba0d361bba",
      "size_bytes": 15051,
      "source_family": "prior_worktree_lead"
    },
    {
      "absolute_path": "C:\\tmp\\gtos_otb\\G0FWDCAPREADY\\enhanced_inverted_analysis_results.json",
      "catalog_row_id": "LCAT-001114",
      "sha256": "4a59328817f60ee75bf66bf0e84a402decb00e4aeccf4a59c942872122fc7c30",
      "size_bytes": 6777,
      "source_family": "prior_worktree_lead"
    },
    {
      "absolute_path": "C:\\tmp\\gtos_otb\\G0FWDCAPREADY\\export_mt5_data.py",
      "catalog_row_id": "LCAT-001115",
      "sha256": "aed0ffdbe7cb8c32a006ee9e75083c1e55e3a6007a0ff10bca57884df5bb4ae2",
      "size_bytes": 5087,
      "source_family": "prior_worktree_lead"
    },
    {
      "absolute_path": "C:\\tmp\\gtos_otb\\G0FWDCAPREADY\\extract_multi.py",
      "catalog_row_id": "LCAT-001116",
      "sha256": "0ad8c4e3f2d2f3fc602aaf987a620ec21e132b771b058c5794db6e5db396752c",
      "size_bytes": 3576,
      "source_family": "prior_worktree_lead"
    },
    {
      "absolute_path": "C:\\tmp\\gtos_otb\\G0FWDCAPREADY\\extract_multi_instrument.py",
      "catalog_row_id": "LCAT-001117",
      "sha256": "c5fa6fe7299007b27c22f8e5386350aad4704b688c36fa962fbd9e77abd0f472",
      "size_bytes": 6455,
      "source_family": "prior_worktree_lead"
    },
    {
      "absolute_path": "C:\\tmp\\gtos_otb\\G0FWDCAPREADY\\gold_expertise_injection_report.md",
      "catalog_row_id": "LCAT-001118",
      "sha256": "9b6948617fdef2c0bb1b50c3e1934afbe913ba4fe991359a3e46ab7026f7e153",
      "size_bytes": 4799,
      "source_family": "prior_worktree_lead"
    },
    {
      "absolute_path": "C:\\tmp\\gtos_otb\\G0FWDCAPREADY\\intelligence_priority_action_plan_20260407.md",
      "catalog_row_id": "LCAT-001119",
      "sha256": "7ea434f6a963c366362d0d48fbba5fe960a48872e0dbab0433ebf305e030902b",
      "size_bytes": 9434,
      "source_family": "prior_worktree_lead"
    },
    {
      "absolute_path": "C:\\tmp\\gtos_otb\\G0FWDCAPREADY\\intelligence_red_team_cross_reference_report.md",
      "catalog_row_id": "LCAT-001120",
      "sha256": "3cf6faa3a9ce6b87d0f078c36e9fc28efb8eebb1714f936fcdfc857bf8ae0763",
      "size_bytes": 11825,
      "source_family": "prior_worktree_lead"
    },
    {
      "absolute_path": "C:\\tmp\\gtos_otb\\G0FWDCAPREADY\\intra_candle_execution_results.json",
      "catalog_row_id": "LCAT-001121",
      "sha256": "4e083e8f31c58c317b66f4d742ad22c258120da2b91e01602e49cf1606d8cd71",
      "size_bytes": 977,
      "source_family": "prior_worktree_lead"
    },
    {
      "absolute_path": "C:\\tmp\\gtos_otb\\G0FWDCAPREADY\\intra_candle_execution_sim.py",
      "catalog_row_id": "LCAT-001122",
      "sha256": "3cf7005acf0b6a94f4bf1c9ca868045521199babeb13bcf5d0db488cd6f23607",
      "size_bytes": 23101,
      "source_family": "prior_worktree_lead"
    },
    {
      "absolute_path": "C:\\tmp\\gtos_otb\\G0FWDCAPREADY\\intra_candle_execution_simulation.md",
      "catalog_row_id": "LCAT-001123",
      "sha256": "5866e80ca1f0e68b6091fc888237246f30f72dfb8e8e4d6a063b66c2b38768d1",
      "size_bytes": 5354,
      "source_family": "prior_worktree_lead"
    },
    {
      "absolute_path": "C:\\tmp\\gtos_otb\\G0FWDCAPREADY\\intra_candle_missed_setups_analysis.md",
      "catalog_row_id": "LCAT-001124",
      "sha256": "5a3fe5471a36a9fde9a8a814538962e253ce553a8a86d50bdc97da0801e831a9",
      "size_bytes": 3386,
      "source_family": "prior_worktree_lead"
    },
    {
      "absolute_path": "C:\\tmp\\gtos_otb\\G0FWDCAPREADY\\inverted_tp_sl_analysis.py",
      "catalog_row_id": "LCAT-001125",
      "sha256": "b273b02e9dd24c8df578ef04db991270e60901ba22d88c52210b5f1c6eedf804",
      "size_bytes": 13640,
      "source_family": "prior_worktree_lead"
    },
    {
      "absolute_path": "C:\\tmp\\gtos_otb\\G0FWDCAPREADY\\inverted_tp_sl_analysis_results.json",
      "catalog_row_id": "LCAT-001126",
      "sha256": "b16b1a8a471b283d6ab85c0d16bd2eb7b829283328db1173c242ec1ec6d9f7a2",
      "size_bytes": 287806,
      "source_family": "prior_worktree_lead"
    },
    {
      "absolute_path": "C:\\tmp\\gtos_otb\\G0FWDCAPREADY\\layer3_wiring_change_report.md",
      "catalog_row_id": "LCAT-001127",
      "sha256": "0198544f55a6da4b4c22c6b20913e0e4d12c6f8285c057a79e8420f39c1e2a64",
      "size_bytes": 7137,
      "source_family": "prior_worktree_lead"
    },
    {
      "absolute_path": "C:\\tmp\\gtos_otb\\G0FWDCAPREADY\\mechanical_backtest.py",
      "catalog_row_id": "LCAT-001128",
      "sha256": "98be7551fca297e7f4024a1d595b8e5fa1ec647f08082aadf9ca33b8d1e2f8a6",
      "size_bytes": 23905,
      "source_family": "prior_worktree_lead"
    },
    {
      "absolute_path": "C:\\tmp\\gtos_otb\\G0FWDCAPREADY\\mechanical_backtest_results.json",
      "catalog_row_id": "LCAT-001129",
      "sha256": "469e0cb520f9c2b1d7c0e0f3ce22f9467ebe4d8382ed62e42497ee8f04917ccb",
      "size_bytes": 216584,
      "source_family": "prior_worktree_lead"
    },
    {
      "absolute_path": "C:\\tmp\\gtos_otb\\G0FWDCAPREADY\\mechanical_vs_ai_comparison.md",
      "catalog_row_id": "LCAT-001130",
      "sha256": "5141804c15c6f9a94d9e56ae438f72268c27380d5850e5e198aa52ef0cf5a788",
      "size_bytes": 7314,
      "source_family": "prior_worktree_lead"
    },
    {
      "absolute_path": "C:\\tmp\\gtos_otb\\G0FWDCAPREADY\\opus_full_86_comparison.md",
      "catalog_row_id": "LCAT-001131",
      "sha256": "0e3a7b7c51acae1e823e6d18a32cdac515f7173dcf2408c8baa76a21bda02af9",
      "size_bytes": 6779,
      "source_family": "prior_worktree_lead"
    },
    {
      "absolute_path": "C:\\tmp\\gtos_otb\\G0FWDCAPREADY\\opus_regular_full_86.md",
      "catalog_row_id": "LCAT-001132",
      "sha256": "096dc264e063c00aed8c6dd57dacf7717f6050a5151973d5623e00ac76775440",
      "size_bytes": 4597,
      "source_family": "prior_worktree_lead"
    },
    {
      "absolute_path": "C:\\tmp\\gtos_otb\\G0FWDCAPREADY\\opus_vs_sonnet_comparison.md",
      "catalog_row_id": "LCAT-001133",
      "sha256": "bcc0160572cb28f2822ed727ef318860d2d811d7119ba1efff7d5151dcb04dd5",
      "size_bytes": 7122,
      "source_family": "prior_worktree_lead"
    },
    {
      "absolute_path": "C:\\tmp\\gtos_otb\\G0FWDCAPREADY\\opus_vs_sonnet_with_memory.md",
      "catalog_row_id": "LCAT-001134",
      "sha256": "0eef466b1b09fd959aa9f013a95a9e46ea44c89ec5c5f3618f794adf06d77886",
      "size_bytes": 9933,
      "source_family": "prior_worktree_lead"
    },
    {
      "absolute_path": "C:\\tmp\\gtos_otb\\G0FWDCAPREADY\\pattern1_events.json",
      "catalog_row_id": "LCAT-001135",
      "sha256": "016ebdbc9e237ea5817f3b1c6d06b003d5ebb07f72c775ab82cc4d054530d3a3",
      "size_bytes": 47509,
      "source_family": "prior_worktree_lead"
    },
    {
      "absolute_path": "C:\\tmp\\gtos_otb\\G0FWDCAPREADY\\per_instrument_subperiod_splits.md",
      "catalog_row_id": "LCAT-001136",
      "sha256": "f35e986af1a2dc28ae4bd7095f0f80bbd5a973f043c022396ed5a073811ac25e",
      "size_bytes": 2381,
      "source_family": "prior_worktree_lead"
    },
    {
      "absolute_path": "C:\\tmp\\gtos_otb\\G0FWDCAPREADY\\per_step_evaluation_analysis.md",
      "catalog_row_id": "LCAT-001137",
      "sha256": "85a0f8fcae2d029dab5d69768c0eb66b21faaa7603f79f53c500bba3806450d8",
      "size_bytes": 3665,
      "source_family": "prior_worktree_lead"
    },
    {
      "absolute_path": "C:\\tmp\\gtos_otb\\G0FWDCAPREADY\\pre_monday_verification_results.md",
      "catalog_row_id": "LCAT-001138",
      "sha256": "97ae20731e64caa6a05eb23acbb8092113ad61089dc15397c5b2057276a99226",
      "size_bytes": 3842,
      "source_family": "prior_worktree_lead"
    },
    {
      "absolute_path": "C:\\tmp\\gtos_otb\\G0FWDCAPREADY\\pressure_test.py",
      "catalog_row_id": "LCAT-001139",
      "sha256": "91e5e6af3fcf3448e0ed3ef4b2fb68319bca133871e8fefef28790e73878528d",
      "size_bytes": 8387,
      "source_family": "prior_worktree_lead"
    },
    {
      "absolute_path": "C:\\tmp\\gtos_otb\\G0FWDCAPREADY\\prompt_feature_inventory.md",
      "catalog_row_id": "LCAT-001140",
      "sha256": "d2cc39cbefaf9692616649667720e45c4b14c267b9d40400d114cb3084ccdf64",
      "size_bytes": 23982,
      "source_family": "prior_worktree_lead"
    },
    {
      "absolute_path": "C:\\tmp\\gtos_otb\\G0FWDCAPREADY\\quick_reference_card.md",
      "catalog_row_id": "LCAT-001141",
      "sha256": "0a5e7db08d43c3ae0ffa32e5d70165c53b32b8422c3720d65c47f3179748bf89",
      "size_bytes": 7565,
      "source_family": "prior_worktree_lead"
    },
    {
      "absolute_path": "C:\\tmp\\gtos_otb\\G0FWDCAPREADY\\r_multiple_analysis.md",
      "catalog_row_id": "LCAT-001142",
      "sha256": "8ef0f41a154d26e4a41a3ac64c23c5fca546e7204d4ea9bed0bab6da0b3839f3",
      "size_bytes": 3721,
      "source_family": "prior_worktree_lead"
    },
    {
      "absolute_path": "C:\\tmp\\gtos_otb\\G0FWDCAPREADY\\reasoning_text_mining.md",
      "catalog_row_id": "LCAT-001143",
      "sha256": "036f3e9bb8b91291edfd10cc6441cde765c69c63498b94c2578f6e5ebf95985b",
      "size_bytes": 2722,
      "source_family": "prior_worktree_lead"
    },
    {
      "absolute_path": "C:\\tmp\\gtos_otb\\G0FWDCAPREADY\\regime_tagging.py",
      "catalog_row_id": "LCAT-001144",
      "sha256": "00292b74913c555fd53f0d95ad8898c5e786f407647aae9ca8dd8567d9777a60",
      "size_bytes": 14701,
      "source_family": "prior_worktree_lead"
    },
    {
      "absolute_path": "C:\\tmp\\gtos_otb\\G0FWDCAPREADY\\regime_tagging_results.md",
      "catalog_row_id": "LCAT-001145",
      "sha256": "e8bed26310e4baa8d46086095eb2b0a69021ad3b5a569cecd99ccca4c5f30724",
      "size_bytes": 7568,
      "source_family": "prior_worktree_lead"
    },
    {
      "absolute_path": "C:\\tmp\\gtos_otb\\G0FWDCAPREADY\\requirements.txt",
      "catalog_row_id": "LCAT-001146",
      "sha256": "ff6cc2a63d657ee5f0b79a8ec55a47e7aef018df4f7c0feae3fb7a0f71308df7",
      "size_bytes": 844,
      "source_family": "prior_worktree_lead"
    },
    {
      "absolute_path": "C:\\tmp\\gtos_otb\\G0FWDCAPREADY\\run_agent.py",
      "catalog_row_id": "LCAT-001147",
      "sha256": "92d0cb559c5cf85a3b86368fe45c5088ff5d0869f4eb283eb27a80dfaea58b70",
      "size_bytes": 3435,
      "source_family": "prior_worktree_lead"
    },
    {
      "absolute_path": "C:\\tmp\\gtos_otb\\G0FWDCAPREADY\\run_comprehensive_tests.py",
      "catalog_row_id": "LCAT-001148",
      "sha256": "0267415c20942333304b0fbbdac44133183a35eda12e6fcad4206ef9cba2091b",
      "size_bytes": 3745,
      "source_family": "prior_worktree_lead"
    },
    {
      "absolute_path": "C:\\tmp\\gtos_otb\\G0FWDCAPREADY\\session_engineering_report.md",
      "catalog_row_id": "LCAT-001149",
      "sha256": "3aaeda017451df2db02ad5a6fd448d23dd0e021bf394b5d4cc78979b194f6c47",
      "size_bytes": 16708,
      "source_family": "prior_worktree_lead"
    },
    {
      "absolute_path": "C:\\tmp\\gtos_otb\\G0FWDCAPREADY\\signal_activation_audit.md",
      "catalog_row_id": "LCAT-001150",
      "sha256": "f5b0e3bc54b358310c6e9be48d450fcc745cc3001e403f900cdeb88e6c74ba94",
      "size_bytes": 12182,
      "source_family": "prior_worktree_lead"
    },
    {
      "absolute_path": "C:\\tmp\\gtos_otb\\G0FWDCAPREADY\\skills-lock.json",
      "catalog_row_id": "LCAT-001151",
      "sha256": "50a054221fd4de8c4e435f77cba58e9db7619522bc810f24eed4e474ccd3482b",
      "size_bytes": 266,
      "source_family": "prior_worktree_lead"
    },
    {
      "absolute_path": "C:\\tmp\\gtos_otb\\G0FWDCAPREADY\\test_a_momentum_baseline_results.md",
      "catalog_row_id": "LCAT-001152",
      "sha256": "35dbd48f4fca2ca787bdd79c42c4bc3392b7cb99bc4f744d1add96ae86945e79",
      "size_bytes": 4702,
      "source_family": "prior_worktree_lead"
    },
    {
      "absolute_path": "C:\\tmp\\gtos_otb\\G0FWDCAPREADY\\test_a_rerun_real_bos_results.md",
      "catalog_row_id": "LCAT-001153",
      "sha256": "96b5aeb5a2c54b90f209f86fa8cb5e391cfb1399b98a94b47f2bc6108cb8ad58",
      "size_bytes": 5725,
      "source_family": "prior_worktree_lead"
    },
    {
      "absolute_path": "C:\\tmp\\gtos_otb\\G0FWDCAPREADY\\test_b_results.md",
      "catalog_row_id": "LCAT-001154",
      "sha256": "0f9d98df80125432dc7410c864aedd85b08ea887840e841adc7b87b830565036",
      "size_bytes": 7493,
      "source_family": "prior_worktree_lead"
    },
    {
      "absolute_path": "C:\\tmp\\gtos_otb\\G0FWDCAPREADY\\.vscode\\extensions.json",
      "catalog_row_id": "LCAT-001155",
      "sha256": "a70ac0b99f9d1e27670add4c3e435a928263027ab046b48c034f794956f3281b",
      "size_bytes": 694,
      "source_family": "prior_worktree_lead"
    },
    {
      "absolute_path": "C:\\tmp\\gtos_otb\\G0FWDCAPREADY\\.vscode\\settings.json",
      "catalog_row_id": "LCAT-001156",
      "sha256": "10f831ea032a6511e59b3169c1109f0000274ddfffad38e90ed7963f56699ed8",
      "size_bytes": 2961,
      "source_family": "prior_worktree_lead"
    },
    {
      "absolute_path": "C:\\tmp\\gtos_otb\\G0FWDCAPREADY\\.vscode\\tasks.json",
      "catalog_row_id": "LCAT-001157",
      "sha256": "9027d7503483fed30a6eacd44ea29cb2af464a2435545790447718890d57fa6f",
      "size_bytes": 3345,
      "source_family": "prior_worktree_lead"
    },
    {
      "absolute_path": "C:\\tmp\\gtos_otb\\G0FWDCAPREADY\\agents\\CEO_DIRECTIVE_NO_FABRICATION.md",
      "catalog_row_id": "LCAT-001158",
      "sha256": "ffdc0010f2de72d17786cb5771ba8dead50257c37949ccd5f8f383ff28eb15b3",
      "size_bytes": 1782,
      "source_family": "prior_worktree_lead"
    },
    {
      "absolute_path": "C:\\tmp\\gtos_otb\\G0FWDCAPREADY\\agents\\KAP_AGENT_0_SCOUT.md",
      "catalog_row_id": "LCAT-001159",
      "sha256": "e45af222c7aa43b87124ede60fb8bf8e17ccdbdf5c2731b29a78c0fdbd0de459",
      "size_bytes": 10538,
      "source_family": "prior_worktree_lead"
    },
    {
      "absolute_path": "C:\\tmp\\gtos_otb\\G0FWDCAPREADY\\agents\\KAP_AGENT_1_EXTRACTOR.md",
      "catalog_row_id": "LCAT-001160",
      "sha256": "26816c20d2f03d09c963f6dadb5c6a2c2e586c31354acd4ea54ab9259b76093b",
      "size_bytes": 10789,
      "source_family": "prior_worktree_lead"
    },
    {
      "absolute_path": "C:\\tmp\\gtos_otb\\G0FWDCAPREADY\\agents\\KAP_AGENT_2_COMPREHENSION.md",
      "catalog_row_id": "LCAT-001161",
      "sha256": "0edce8f155a6ecc2f1e84a17bfa29673593f38db3e42ac2e794657f97858abec",
      "size_bytes": 17703,
      "source_family": "prior_worktree_lead"
    },
    {
      "absolute_path": "C:\\tmp\\gtos_otb\\G0FWDCAPREADY\\agents\\KAP_AGENT_3_FILTER.md",
      "catalog_row_id": "LCAT-001162",
      "sha256": "b1563b760c5ffcd7ade96f138d9f9908eb910e7cce97df3f4b72221115667605",
      "size_bytes": 14043,
      "source_family": "prior_worktree_lead"
    },
    {
      "absolute_path": "C:\\tmp\\gtos_otb\\G0FWDCAPREADY\\agents\\KAP_AGENT_4_STRATEGIST.md",
      "catalog_row_id": "LCAT-001163",
      "sha256": "a1a7b7fd0b88dfa6d1a80a923d9cab5cbc044dfef573ed45493d1cd4373b0588",
      "size_bytes": 18625,
      "source_family": "prior_worktree_lead"
    },
    {
      "absolute_path": "C:\\tmp\\gtos_otb\\G0FWDCAPREADY\\agents\\KAP_COMPLETE_WORKFLOW.md",
      "catalog_row_id": "LCAT-001164",
      "sha256": "c684e6fa52a76bb915356765a94bc21dda59af799e56ce7cb4debf73e1c6cccb",
      "size_bytes": 4001,
      "source_family": "prior_worktree_lead"
    },
    {
      "absolute_path": "C:\\tmp\\gtos_otb\\G0FWDCAPREADY\\agents\\KAP_IMPLEMENTATION_AGENT.md",
      "catalog_row_id": "LCAT-001165",
      "sha256": "989a1326c9b27bb9b00183e4021fad0fb9ed4298840dd3d1438a4af9f2a03f78",
      "size_bytes": 9581,
      "source_family": "prior_worktree_lead"
    },
    {
      "absolute_path": "C:\\tmp\\gtos_otb\\G0FWDCAPREADY\\agents\\KAP_MASTER_LAUNCHER.md",
      "catalog_row_id": "LCAT-001166",
      "sha256": "b0ca0b2eab18d7e84171431900db59f106c4f19ca1d6d33b8602cfb116c55264",
      "size_bytes": 5067,
      "source_family": "prior_worktree_lead"
    },
    {
      "absolute_path": "C:\\tmp\\gtos_otb\\G0FWDCAPREADY\\agents\\KAP_STRATEGIC_REVIEWER.md",
      "catalog_row_id": "LCAT-001167",
      "sha256": "7c649a91e1da24bf6d47ddaf7993d66c6a4cc5050180461a6a9d12197e2af40e",
      "size_bytes": 7993,
      "source_family": "prior_worktree_lead"
    },
    {
      "absolute_path": "C:\\tmp\\gtos_otb\\G0FWDCAPREADY\\agents\\ZETA_RED_TEAM-2.md",
      "catalog_row_id": "LCAT-001168",
      "sha256": "5d994b1eb210b895fc5677427e46a7bf086dcfb9f8988cee695075070c60ca7c",
      "size_bytes": 11771,
      "source_family": "prior_worktree_lead"
    },
    {
      "absolute_path": "C:\\tmp\\gtos_otb\\G0FWDCAPREADY\\analysis\\prescreen_kill_details.json",
      "catalog_row_id": "LCAT-001169",
      "sha256": "bcbfef63c24f75fa5e161a31325bbca56cc3982221cd0dafc850a587d6a4b612",
      "size_bytes": 4876201,
      "source_family": "prior_worktree_lead"
    },
    {
      "absolute_path": "C:\\tmp\\gtos_otb\\G0FWDCAPREADY\\analysis\\prescreen_killed_dates.csv",
      "catalog_row_id": "LCAT-001170",
      "sha256": "36e60747a69d6385ccd11bd26d02d848cac97fae3dd9c4c65db5a7c9ffc6243a",
      "size_bytes": 18150,
      "source_family": "prior_worktree_lead"
    },
    {
      "absolute_path": "C:\\tmp\\gtos_otb\\G0FWDCAPREADY\\analysis\\prescreen_loosening_report.md",
      "catalog_row_id": "LCAT-001171",
      "sha256": "e26c44ed6f9c1f23922a21f0c5220116206ba3b55f34934ee5b12017d679e64b",
      "size_bytes": 13947,
      "source_family": "prior_worktree_lead"
    },
    {
      "absolute_path": "C:\\tmp\\gtos_otb\\G0FWDCAPREADY\\archive\\financial_planning\\CEO_KNOWLEDGE_ACQUISITION_EXECUTIVE_SUMMARY.md",
      "catalog_row_id": "LCAT-001172",
      "sha256": "12c3ef21b61956999795b40ab9b240969ec529b5bf32e0df7f98be2021ffde8a",
      "size_bytes": 10853,
      "source_family": "prior_worktree_lead"
    },
    {
      "absolute_path": "C:\\tmp\\gtos_otb\\G0FWDCAPREADY\\config\\agent_config.yaml",
      "catalog_row_id": "LCAT-001173",
      "sha256": "b353d960086d174d42eb3e898ba7787175d3bd634387a02059b30bfdf35222e4",
      "size_bytes": 47316,
      "source_family": "prior_worktree_lead"
    },
    {
      "absolute_path": "C:\\tmp\\gtos_otb\\G0FWDCAPREADY\\config\\shadow_observer_registry.yaml",
      "catalog_row_id": "LCAT-001174",
      "sha256": "1b8000c5283edd48f7f68d7d1b521d76a080f6f531d92cced9527f3b898733c0",
      "size_bytes": 5793,
      "source_family": "prior_worktree_lead"
    },
    {
      "absolute_path": "C:\\tmp\\gtos_otb\\G0FWDCAPREADY\\config\\profiles\\README.md",
      "catalog_row_id": "LCAT-001175",
      "sha256": "801b5321412b3d477a4610df84f2b8598bf50416309099b12e319f50edeebe8c",
      "size_bytes": 1366,
      "source_family": "prior_worktree_lead"
    },
    {
      "absolute_path": "C:\\tmp\\gtos_otb\\G0FWDCAPREADY\\config\\profiles\\ftmo.yaml",
      "catalog_row_id": "LCAT-001176",
      "sha256": "aab6659c258fb071d55ca4a74cdff19c6538469723535e92e4a96c7b59f7a6ed",
      "size_bytes": 2155,
      "source_family": "prior_worktree_lead"
    },
    {
      "absolute_path": "C:\\tmp\\gtos_otb\\G0FWDCAPREADY\\config\\profiles\\redacted_account.yaml",
      "catalog_row_id": "LCAT-001177",
      "sha256": "d43dd9ae5e428a9df85631d4612d0737a18484a2268bf7db8a31b0946566371b",
      "size_bytes": 7285,
      "source_family": "prior_worktree_lead"
    },
    {
      "absolute_path": "C:\\tmp\\gtos_otb\\G0FWDCAPREADY\\data\\DXY_D1.csv",
      "catalog_row_id": "LCAT-001178",
      "sha256": "7da2e65e61087b2235fe2a5d6678b56f716a2a6d913be78b663faf1f0fdc23b9",
      "size_bytes": 20017,
      "source_family": "prior_worktree_lead"
    },
    {
      "absolute_path": "C:\\tmp\\gtos_otb\\G0FWDCAPREADY\\data\\EURUSD_D1.csv",
      "catalog_row_id": "LCAT-001179",
      "sha256": "cc0dbe2373b9ce94dabb295729e17ad24350281b57d03a9c3d807b3a5c2d60d5",
      "size_bytes": 30108,
      "source_family": "prior_worktree_lead"
    },
    {
      "absolute_path": "C:\\tmp\\gtos_otb\\G0FWDCAPREADY\\data\\EURUSD_H1.csv",
      "catalog_row_id": "LCAT-001180",
      "sha256": "17e289eeec2cd1fe9b91723f97c8bb74f0865b8de855027def35e7425b16cd96",
      "size_bytes": 828266,
      "source_family": "prior_worktree_lead"
    },
    {
      "absolute_path": "C:\\tmp\\gtos_otb\\G0FWDCAPREADY\\data\\EURUSD_H4.csv",
      "catalog_row_id": "LCAT-001181",
      "sha256": "7c696ae7aa2386f771959485e5af5bf6a51edebfcdc44340a72b15d72b186202",
      "size_bytes": 209541,
      "source_family": "prior_worktree_lead"
    },
    {
      "absolute_path": "C:\\tmp\\gtos_otb\\G0FWDCAPREADY\\data\\EURUSD_M15.csv",
      "catalog_row_id": "LCAT-001182",
      "sha256": "d56405a0a11016b368312deca3b59361c14206ca8694c9a372e46451096139f8",
      "size_bytes": 3273362,
      "source_family": "prior_worktree_lead"
    },
    {
      "absolute_path": "C:\\tmp\\gtos_otb\\G0FWDCAPREADY\\data\\EURUSD_M5.csv",
      "catalog_row_id": "LCAT-001183",
      "sha256": "41a2d240cfacb029c3f268dca8936d0fb4f3aa9e03d8238c006aab5afd6a3e83",
      "size_bytes": 5291443,
      "source_family": "prior_worktree_lead"
    },
    {
      "absolute_path": "C:\\tmp\\gtos_otb\\G0FWDCAPREADY\\data\\GBPUSD_D1.csv",
      "catalog_row_id": "LCAT-001184",
      "sha256": "8722fa67d7b8f70ddc5a856169a80252276f692554e1f732850d8b3a1065aafc",
      "size_bytes": 177741,
      "source_family": "prior_worktree_lead"
    },
    {
      "absolute_path": "C:\\tmp\\gtos_otb\\G0FWDCAPREADY\\data\\GBPUSD_H1.csv",
      "catalog_row_id": "LCAT-001185",
      "sha256": "6e24d801081439a611d5d93c61324ae56d9c55279eec75163e325a7ee92c57e8",
      "size_bytes": 1165745,
      "source_family": "prior_worktree_lead"
    },
    {
      "absolute_path": "C:\\tmp\\gtos_otb\\G0FWDCAPREADY\\data\\GBPUSD_H4.csv",
      "catalog_row_id": "LCAT-001186",
      "sha256": "81ad64a3d3ad1b351f03a5fa558a9e5ef8b0c227e122961d1c3dc65039834b90",
      "size_bytes": 580221,
      "source_family": "prior_worktree_lead"
    },
    {
      "absolute_path": "C:\\tmp\\gtos_otb\\G0FWDCAPREADY\\data\\GBPUSD_M15.csv",
      "catalog_row_id": "LCAT-001187",
      "sha256": "b9df02945dc0b53a8440ed85ddd47d8c94a081cb0071be5aa445acb604ac70f7",
      "size_bytes": 2903066,
      "source_family": "prior_worktree_lead"
    },
    {
      "absolute_path": "C:\\tmp\\gtos_otb\\G0FWDCAPREADY\\data\\GBPUSD_M5.csv",
      "catalog_row_id": "LCAT-001188",
      "sha256": "b4571cf13f78561345964d3106854e190ed895f53eb34267a9f808c6346aa65f",
      "size_bytes": 19603,
      "source_family": "prior_worktree_lead"
    },
    {
      "absolute_path": "C:\\tmp\\gtos_otb\\G0FWDCAPREADY\\data\\NAS100_D1.csv",
      "catalog_row_id": "LCAT-001189",
      "sha256": "04b7f6b49e67f7575ffa6d7ee64d0cac2e331fb8baaad9cdc8e9d247d09b439c",
      "size_bytes": 28780,
      "source_family": "prior_worktree_lead"
    },
    {
      "absolute_path": "C:\\tmp\\gtos_otb\\G0FWDCAPREADY\\data\\NAS100_H1.csv",
      "catalog_row_id": "LCAT-001190",
      "sha256": "b8a028cf1714367f673b3309b801e0903f4583129a1dc2f772c1c5d7a6adc78e",
      "size_bytes": 744327,
      "source_family": "prior_worktree_lead"
    },
    {
      "absolute_path": "C:\\tmp\\gtos_otb\\G0FWDCAPREADY\\data\\NAS100_H4.csv",
      "catalog_row_id": "LCAT-001191",
      "sha256": "f6ed040030a8e55579e84c8c6b56b4bee65d4dede9674b8a75c4c573cd8926c3",
      "size_bytes": 197086,
      "source_family": "prior_worktree_lead"
    },
    {
      "absolute_path": "C:\\tmp\\gtos_otb\\G0FWDCAPREADY\\data\\NAS100_M15.csv",
      "catalog_row_id": "LCAT-001192",
      "sha256": "ba1e450066659bece6c5374f81b66c58ec78e412db5ada13ef6bf8aae7f03a96",
      "size_bytes": 2934918,
      "source_family": "prior_worktree_lead"
    },
    {
      "absolute_path": "C:\\tmp\\gtos_otb\\G0FWDCAPREADY\\data\\NAS100_M5.csv",
      "catalog_row_id": "LCAT-001193",
      "sha256": "88cd6d26393a202a2fcca903463ec58287e206e52aed4620ffb57803ffceefd4",
      "size_bytes": 5301737,
      "source_family": "prior_worktree_lead"
    },
    {
      "absolute_path": "C:\\tmp\\gtos_otb\\G0FWDCAPREADY\\data\\XAGUSD_D1.csv",
      "catalog_row_id": "LCAT-001194",
      "sha256": "55b7bb9275ed99c5f37838c70dbefef3025d0a4f1c9406a3ccd8f8c9723949c5",
      "size_bytes": 26899,
      "source_family": "prior_worktree_lead"
    },
    {
      "absolute_path": "C:\\tmp\\gtos_otb\\G0FWDCAPREADY\\data\\XAGUSD_H1.csv",
      "catalog_row_id": "LCAT-001195",
      "sha256": "8f9dac30640c47b2c8ae8de60f3e680404aa22e3dce4b81c39347e0698755b30",
      "size_bytes": 723400,
      "source_family": "prior_worktree_lead"
    },
    {
      "absolute_path": "C:\\tmp\\gtos_otb\\G0FWDCAPREADY\\data\\XAGUSD_H4.csv",
      "catalog_row_id": "LCAT-001196",
      "sha256": "3cdc3e58284f866ef95012cd7989b8fc7ec8d89535150fda0de32979f62445c7",
      "size_bytes": 189481,
      "source_family": "prior_worktree_lead"
    },
    {
      "absolute_path": "C:\\tmp\\gtos_otb\\G0FWDCAPREADY\\data\\XAGUSD_M15.csv",
      "catalog_row_id": "LCAT-001197",
      "sha256": "f80f7ebb87b065f73d20c7f55a95245f8c0d8640f75d1410bd5e1afcac4ce506",
      "size_bytes": 2850025,
      "source_family": "prior_worktree_lead"
    },
    {
      "absolute_path": "C:\\tmp\\gtos_otb\\G0FWDCAPREADY\\data\\XAGUSD_M5.csv",
      "catalog_row_id": "LCAT-001198",
      "sha256": "5efd8120a22cd2c99daefe27f41becb1093faccb7de31636aa1000c484e7be45",
      "size_bytes": 4729418,
      "source_family": "prior_worktree_lead"
    },
    {
      "absolute_path": "C:\\tmp\\gtos_otb\\G0FWDCAPREADY\\data\\XAUUSD_D1.csv",
      "catalog_row_id": "LCAT-001199",
      "sha256": "fce7d961f04583957f4d7c86eb15420464a79f8610eb2fc66781bf2ebbf34d99",
      "size_bytes": 3872,
      "source_family": "prior_worktree_lead"
    },
    {
      "absolute_path": "C:\\tmp\\gtos_otb\\G0FWDCAPREADY\\data\\XAUUSD_H1.csv",
      "catalog_row_id": "LCAT-001200",
      "sha256": "cd15facd79121b6a68cea6f1f96881aa4916e44c06805f6613e45b64078766b5",
      "size_bytes": 12582,
      "source_family": "prior_worktree_lead"
    }
  ],
  "large_file_deferral_count": 124,
  "large_file_deferrals": [
    {
      "absolute_path": "C:\\tmp\\gtos_otb\\NOFILLTICKRECOVERY\\shadow_logs\\candidate_features_log.jsonl",
      "catalog_row_id": "LCAT-000123",
      "exact_next_action": "run_dedicated_owner_approved_hash_manifest_for_large_file_before_consumption",
      "large_file_hash_deferral_id": "DEFERRAL-0001",
      "size_bytes": 9948352,
      "source_family": "shadow_log_source_control"
    },
    {
      "absolute_path": "C:\\tmp\\gtos_otb\\NOFILLTICKRECOVERY\\shadow_logs\\candidate_ltf_path_order.jsonl",
      "catalog_row_id": "LCAT-000124",
      "exact_next_action": "run_dedicated_owner_approved_hash_manifest_for_large_file_before_consumption",
      "large_file_hash_deferral_id": "DEFERRAL-0002",
      "size_bytes": 10146567,
      "source_family": "shadow_log_source_control"
    },
    {
      "absolute_path": "C:\\tmp\\gtos_otb\\NOFILLTICKRECOVERY\\shadow_logs\\candidate_path_follow.jsonl",
      "catalog_row_id": "LCAT-000127",
      "exact_next_action": "run_dedicated_owner_approved_hash_manifest_for_large_file_before_consumption",
      "large_file_hash_deferral_id": "DEFERRAL-0003",
      "size_bytes": 15356876,
      "source_family": "shadow_log_source_control"
    },
    {
      "absolute_path": "C:\\tmp\\gtos_otb\\NOFILLTICKRECOVERY\\shadow_logs\\context_control_audit.jsonl",
      "catalog_row_id": "LCAT-000129",
      "exact_next_action": "run_dedicated_owner_approved_hash_manifest_for_large_file_before_consumption",
      "large_file_hash_deferral_id": "DEFERRAL-0004",
      "size_bytes": 11327662,
      "source_family": "shadow_log_source_control"
    },
    {
      "absolute_path": "C:\\tmp\\gtos_otb\\NOFILLTICKRECOVERY\\shadow_logs\\fvg_ob_confluence_audit.jsonl",
      "catalog_row_id": "LCAT-000159",
      "exact_next_action": "run_dedicated_owner_approved_hash_manifest_for_large_file_before_consumption",
      "large_file_hash_deferral_id": "DEFERRAL-0005",
      "size_bytes": 25149615,
      "source_family": "shadow_log_source_control"
    },
    {
      "absolute_path": "C:\\tmp\\gtos_otb\\NOFILLTICKRECOVERY\\shadow_logs\\fvg_ob_confluence_resolutions.jsonl",
      "catalog_row_id": "LCAT-000160",
      "exact_next_action": "run_dedicated_owner_approved_hash_manifest_for_large_file_before_consumption",
      "large_file_hash_deferral_id": "DEFERRAL-0006",
      "size_bytes": 11143455,
      "source_family": "shadow_log_source_control"
    },
    {
      "absolute_path": "C:\\tmp\\gtos_otb\\NOFILLTICKRECOVERY\\shadow_logs\\live_candidate_opportunity_clusters.jsonl",
      "catalog_row_id": "LCAT-000166",
      "exact_next_action": "run_dedicated_owner_approved_hash_manifest_for_large_file_before_consumption",
      "large_file_hash_deferral_id": "DEFERRAL-0007",
      "size_bytes": 19020727,
      "source_family": "shadow_log_source_control"
    },
    {
      "absolute_path": "C:\\tmp\\gtos_otb\\NOFILLTICKRECOVERY\\shadow_logs\\live_candidate_strategy_rollups.jsonl",
      "catalog_row_id": "LCAT-000167",
      "exact_next_action": "run_dedicated_owner_approved_hash_manifest_for_large_file_before_consumption",
      "large_file_hash_deferral_id": "DEFERRAL-0008",
      "size_bytes": 45070558,
      "source_family": "shadow_log_source_control"
    },
    {
      "absolute_path": "C:\\tmp\\gtos_otb\\NOFILLTICKRECOVERY\\shadow_logs\\live_mechanical_strategy_shadow_outcomes.jsonl",
      "catalog_row_id": "LCAT-000168",
      "exact_next_action": "run_dedicated_owner_approved_hash_manifest_for_large_file_before_consumption",
      "large_file_hash_deferral_id": "DEFERRAL-0009",
      "size_bytes": 192616615,
      "source_family": "shadow_log_source_control"
    },
    {
      "absolute_path": "C:\\tmp\\gtos_otb\\NOFILLTICKRECOVERY\\shadow_logs\\live_structural_strategy_metadata.jsonl",
      "catalog_row_id": "LCAT-000172",
      "exact_next_action": "run_dedicated_owner_approved_hash_manifest_for_large_file_before_consumption",
      "large_file_hash_deferral_id": "DEFERRAL-0010",
      "size_bytes": 13431644,
      "source_family": "shadow_log_source_control"
    },
    {
      "absolute_path": "C:\\tmp\\gtos_otb\\NOFILLTICKRECOVERY\\shadow_logs\\mechanical_context_diagnostics_join.jsonl",
      "catalog_row_id": "LCAT-000176",
      "exact_next_action": "run_dedicated_owner_approved_hash_manifest_for_large_file_before_consumption",
      "large_file_hash_deferral_id": "DEFERRAL-0011",
      "size_bytes": 12654760,
      "source_family": "shadow_log_source_control"
    },
    {
      "absolute_path": "C:\\tmp\\gtos_otb\\NOFILLTICKRECOVERY\\shadow_logs\\ml_shadow_predictions.jsonl",
      "catalog_row_id": "LCAT-000178",
      "exact_next_action": "run_dedicated_owner_approved_hash_manifest_for_large_file_before_consumption",
      "large_file_hash_deferral_id": "DEFERRAL-0012",
      "size_bytes": 112126173,
      "source_family": "shadow_log_source_control"
    },
    {
      "absolute_path": "C:\\tmp\\gtos_otb\\NOFILLTICKRECOVERY\\shadow_logs\\opportunity_lifecycle_audit.jsonl",
      "catalog_row_id": "LCAT-000183",
      "exact_next_action": "run_dedicated_owner_approved_hash_manifest_for_large_file_before_consumption",
      "large_file_hash_deferral_id": "DEFERRAL-0013",
      "size_bytes": 10573700,
      "source_family": "shadow_log_source_control"
    },
    {
      "absolute_path": "C:\\tmp\\gtos_otb\\NOFILLTICKRECOVERY\\shadow_logs\\prefill_delivery_path_audit.jsonl",
      "catalog_row_id": "LCAT-000191",
      "exact_next_action": "run_dedicated_owner_approved_hash_manifest_for_large_file_before_consumption",
      "large_file_hash_deferral_id": "DEFERRAL-0014",
      "size_bytes": 28308732,
      "source_family": "shadow_log_source_control"
    },
    {
      "absolute_path": "C:\\tmp\\gtos_otb\\NOFILLTICKRECOVERY\\shadow_logs\\prefill_delivery_path_resolutions.jsonl",
      "catalog_row_id": "LCAT-000192",
      "exact_next_action": "run_dedicated_owner_approved_hash_manifest_for_large_file_before_consumption",
      "large_file_hash_deferral_id": "DEFERRAL-0015",
      "size_bytes": 11243784,
      "source_family": "shadow_log_source_control"
    },
    {
      "absolute_path": "C:\\tmp\\gtos_otb\\NOFILLTICKRECOVERY\\shadow_logs\\regime_decay_outcome_join.jsonl",
      "catalog_row_id": "LCAT-000196",
      "exact_next_action": "run_dedicated_owner_approved_hash_manifest_for_large_file_before_consumption",
      "large_file_hash_deferral_id": "DEFERRAL-0016",
      "size_bytes": 11310367,
      "source_family": "shadow_log_source_control"
    },
    {
      "absolute_path": "C:\\tmp\\gtos_otb\\NOFILLTICKRECOVERY\\shadow_logs\\strategy_follow_evaluations.jsonl",
      "catalog_row_id": "LCAT-000212",
      "exact_next_action": "run_dedicated_owner_approved_hash_manifest_for_large_file_before_consumption",
      "large_file_hash_deferral_id": "DEFERRAL-0017",
      "size_bytes": 11497601,
      "source_family": "shadow_log_source_control"
    },
    {
      "absolute_path": "C:\\tmp\\gtos_otb\\NOFILLTICKRECOVERY\\shadow_logs\\v2b_forward_pair_resolution_audit.jsonl",
      "catalog_row_id": "LCAT-000220",
      "exact_next_action": "run_dedicated_owner_approved_hash_manifest_for_large_file_before_consumption",
      "large_file_hash_deferral_id": "DEFERRAL-0018",
      "size_bytes": 32315168,
      "source_family": "shadow_log_source_control"
    },
    {
      "absolute_path": "C:\\tmp\\gtos_otb\\NOFILLTICKRECOVERY\\shadow_logs\\v2b_forward_pair_resolutions.jsonl",
      "catalog_row_id": "LCAT-000221",
      "exact_next_action": "run_dedicated_owner_approved_hash_manifest_for_large_file_before_consumption",
      "large_file_hash_deferral_id": "DEFERRAL-0019",
      "size_bytes": 11654060,
      "source_family": "shadow_log_source_control"
    },
    {
      "absolute_path": "C:\\tmp\\gtos_otb\\NOFILLTICKRECOVERY\\research\\science_program_2026_05\\06_outcome_testing\\cnr_source_field_packet_builder\\CNR_SOURCE_FIELD_PACKET_ROWS_2026-05-07.jsonl",
      "catalog_row_id": "LCAT-000423",
      "exact_next_action": "run_dedicated_owner_approved_hash_manifest_for_large_file_before_consumption",
      "large_file_hash_deferral_id": "DEFERRAL-0020",
      "size_bytes": 31373220,
      "source_family": "research_route_artifact"
    },
    {
      "absolute_path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\data\\external\\features\\GBPJPY\\phase3_m15_2022_2026_external_v1_20260501T013833Z.jsonl",
      "catalog_row_id": "LCAT-000512",
      "exact_next_action": "run_dedicated_owner_approved_hash_manifest_for_large_file_before_consumption",
      "large_file_hash_deferral_id": "DEFERRAL-0021",
      "size_bytes": 389258024,
      "source_family": "local_external_or_vendor_cache"
    },
    {
      "absolute_path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\data\\external\\features\\GBPJPY\\phase3_m15_2025_2026_external_v5_20260501T004212Z.jsonl",
      "catalog_row_id": "LCAT-000513",
      "exact_next_action": "run_dedicated_owner_approved_hash_manifest_for_large_file_before_consumption",
      "large_file_hash_deferral_id": "DEFERRAL-0022",
      "size_bytes": 54524286,
      "source_family": "local_external_or_vendor_cache"
    },
    {
      "absolute_path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\data\\external\\features\\GBPUSD\\phase3_m15_2022_2026_external_v1_20260501T013833Z.jsonl",
      "catalog_row_id": "LCAT-000515",
      "exact_next_action": "run_dedicated_owner_approved_hash_manifest_for_large_file_before_consumption",
      "large_file_hash_deferral_id": "DEFERRAL-0023",
      "size_bytes": 389258092,
      "source_family": "local_external_or_vendor_cache"
    },
    {
      "absolute_path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\data\\external\\features\\GBPUSD\\phase3_m15_2025_2026_external_v1_20260501T000418Z.jsonl",
      "catalog_row_id": "LCAT-000516",
      "exact_next_action": "run_dedicated_owner_approved_hash_manifest_for_large_file_before_consumption",
      "large_file_hash_deferral_id": "DEFERRAL-0024",
      "size_bytes": 11658816,
      "source_family": "local_external_or_vendor_cache"
    },
    {
      "absolute_path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\data\\external\\features\\GBPUSD\\phase3_m15_2025_2026_external_v2_20260501T000914Z.jsonl",
      "catalog_row_id": "LCAT-000517",
      "exact_next_action": "run_dedicated_owner_approved_hash_manifest_for_large_file_before_consumption",
      "large_file_hash_deferral_id": "DEFERRAL-0025",
      "size_bytes": 54539857,
      "source_family": "local_external_or_vendor_cache"
    },
    {
      "absolute_path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\data\\external\\features\\GBPUSD\\phase3_m15_2025_2026_external_v3_20260501T000956Z.jsonl",
      "catalog_row_id": "LCAT-000518",
      "exact_next_action": "run_dedicated_owner_approved_hash_manifest_for_large_file_before_consumption",
      "large_file_hash_deferral_id": "DEFERRAL-0026",
      "size_bytes": 54539857,
      "source_family": "local_external_or_vendor_cache"
    },
    {
      "absolute_path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\data\\external\\features\\GBPUSD\\phase3_m15_2025_2026_external_v4_20260501T004047Z.jsonl",
      "catalog_row_id": "LCAT-000519",
      "exact_next_action": "run_dedicated_owner_approved_hash_manifest_for_large_file_before_consumption",
      "large_file_hash_deferral_id": "DEFERRAL-0027",
      "size_bytes": 54539857,
      "source_family": "local_external_or_vendor_cache"
    },
    {
      "absolute_path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\data\\external\\features\\GBPUSD\\phase3_m15_2025_2026_external_v5_20260501T004212Z.jsonl",
      "catalog_row_id": "LCAT-000520",
      "exact_next_action": "run_dedicated_owner_approved_hash_manifest_for_large_file_before_consumption",
      "large_file_hash_deferral_id": "DEFERRAL-0028",
      "size_bytes": 54539857,
      "source_family": "local_external_or_vendor_cache"
    },
    {
      "absolute_path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\data\\external\\features\\NAS100\\phase3_m15_2022_2026_external_v1_20260501T013833Z.jsonl",
      "catalog_row_id": "LCAT-000523",
      "exact_next_action": "run_dedicated_owner_approved_hash_manifest_for_large_file_before_consumption",
      "large_file_hash_deferral_id": "DEFERRAL-0029",
      "size_bytes": 283585832,
      "source_family": "local_external_or_vendor_cache"
    },
    {
      "absolute_path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\data\\external\\features\\NAS100\\phase3_m15_2025_2026_external_v1_20260501T000418Z.jsonl",
      "catalog_row_id": "LCAT-000524",
      "exact_next_action": "run_dedicated_owner_approved_hash_manifest_for_large_file_before_consumption",
      "large_file_hash_deferral_id": "DEFERRAL-0030",
      "size_bytes": 11052288,
      "source_family": "local_external_or_vendor_cache"
    },
    {
      "absolute_path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\data\\external\\features\\NAS100\\phase3_m15_2025_2026_external_v2_20260501T000914Z.jsonl",
      "catalog_row_id": "LCAT-000525",
      "exact_next_action": "run_dedicated_owner_approved_hash_manifest_for_large_file_before_consumption",
      "large_file_hash_deferral_id": "DEFERRAL-0031",
      "size_bytes": 51702752,
      "source_family": "local_external_or_vendor_cache"
    },
    {
      "absolute_path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\data\\external\\features\\NAS100\\phase3_m15_2025_2026_external_v3_20260501T000956Z.jsonl",
      "catalog_row_id": "LCAT-000526",
      "exact_next_action": "run_dedicated_owner_approved_hash_manifest_for_large_file_before_consumption",
      "large_file_hash_deferral_id": "DEFERRAL-0032",
      "size_bytes": 51702752,
      "source_family": "local_external_or_vendor_cache"
    },
    {
      "absolute_path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\data\\external\\features\\NAS100\\phase3_m15_2025_2026_external_v4_20260501T004047Z.jsonl",
      "catalog_row_id": "LCAT-000527",
      "exact_next_action": "run_dedicated_owner_approved_hash_manifest_for_large_file_before_consumption",
      "large_file_hash_deferral_id": "DEFERRAL-0033",
      "size_bytes": 51702752,
      "source_family": "local_external_or_vendor_cache"
    },
    {
      "absolute_path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\data\\external\\features\\NAS100\\phase3_m15_2025_2026_external_v5_20260501T004212Z.jsonl",
      "catalog_row_id": "LCAT-000528",
      "exact_next_action": "run_dedicated_owner_approved_hash_manifest_for_large_file_before_consumption",
      "large_file_hash_deferral_id": "DEFERRAL-0034",
      "size_bytes": 51702752,
      "source_family": "local_external_or_vendor_cache"
    },
    {
      "absolute_path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\data\\external\\features\\US30_CASH\\phase3_m15_2022_2026_external_v1_20260501T013833Z.jsonl",
      "catalog_row_id": "LCAT-000531",
      "exact_next_action": "run_dedicated_owner_approved_hash_manifest_for_large_file_before_consumption",
      "large_file_hash_deferral_id": "DEFERRAL-0035",
      "size_bytes": 283600326,
      "source_family": "local_external_or_vendor_cache"
    },
    {
      "absolute_path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\data\\external\\features\\US30_CASH\\phase3_m15_2025_2026_external_v1_20260501T000418Z.jsonl",
      "catalog_row_id": "LCAT-000532",
      "exact_next_action": "run_dedicated_owner_approved_hash_manifest_for_large_file_before_consumption",
      "large_file_hash_deferral_id": "DEFERRAL-0036",
      "size_bytes": 11061407,
      "source_family": "local_external_or_vendor_cache"
    },
    {
      "absolute_path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\data\\external\\features\\US30_CASH\\phase3_m15_2025_2026_external_v2_20260501T000914Z.jsonl",
      "catalog_row_id": "LCAT-000533",
      "exact_next_action": "run_dedicated_owner_approved_hash_manifest_for_large_file_before_consumption",
      "large_file_hash_deferral_id": "DEFERRAL-0037",
      "size_bytes": 51696591,
      "source_family": "local_external_or_vendor_cache"
    },
    {
      "absolute_path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\data\\external\\features\\US30_CASH\\phase3_m15_2025_2026_external_v3_20260501T000956Z.jsonl",
      "catalog_row_id": "LCAT-000534",
      "exact_next_action": "run_dedicated_owner_approved_hash_manifest_for_large_file_before_consumption",
      "large_file_hash_deferral_id": "DEFERRAL-0038",
      "size_bytes": 51696591,
      "source_family": "local_external_or_vendor_cache"
    },
    {
      "absolute_path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\data\\external\\features\\US30_CASH\\phase3_m15_2025_2026_external_v4_20260501T004047Z.jsonl",
      "catalog_row_id": "LCAT-000535",
      "exact_next_action": "run_dedicated_owner_approved_hash_manifest_for_large_file_before_consumption",
      "large_file_hash_deferral_id": "DEFERRAL-0039",
      "size_bytes": 51696591,
      "source_family": "local_external_or_vendor_cache"
    },
    {
      "absolute_path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\data\\external\\features\\US30_CASH\\phase3_m15_2025_2026_external_v5_20260501T004212Z.jsonl",
      "catalog_row_id": "LCAT-000536",
      "exact_next_action": "run_dedicated_owner_approved_hash_manifest_for_large_file_before_consumption",
      "large_file_hash_deferral_id": "DEFERRAL-0040",
      "size_bytes": 51696591,
      "source_family": "local_external_or_vendor_cache"
    },
    {
      "absolute_path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\data\\external\\features\\USDJPY\\phase3_m15_2022_2026_external_v1_20260501T013833Z.jsonl",
      "catalog_row_id": "LCAT-000539",
      "exact_next_action": "run_dedicated_owner_approved_hash_manifest_for_large_file_before_consumption",
      "large_file_hash_deferral_id": "DEFERRAL-0041",
      "size_bytes": 389258095,
      "source_family": "local_external_or_vendor_cache"
    },
    {
      "absolute_path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\data\\external\\features\\USDJPY\\phase3_m15_2025_2026_external_v5_20260501T004212Z.jsonl",
      "catalog_row_id": "LCAT-000540",
      "exact_next_action": "run_dedicated_owner_approved_hash_manifest_for_large_file_before_consumption",
      "large_file_hash_deferral_id": "DEFERRAL-0042",
      "size_bytes": 54539855,
      "source_family": "local_external_or_vendor_cache"
    },
    {
      "absolute_path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\data\\external\\features\\XAGUSD\\phase3_m15_2022_2026_external_v1_20260501T013833Z.jsonl",
      "catalog_row_id": "LCAT-000542",
      "exact_next_action": "run_dedicated_owner_approved_hash_manifest_for_large_file_before_consumption",
      "large_file_hash_deferral_id": "DEFERRAL-0043",
      "size_bytes": 421958084,
      "source_family": "local_external_or_vendor_cache"
    },
    {
      "absolute_path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\data\\external\\features\\XAGUSD\\phase3_m15_2025_2026_external_v1_20260501T000418Z.jsonl",
      "catalog_row_id": "LCAT-000543",
      "exact_next_action": "run_dedicated_owner_approved_hash_manifest_for_large_file_before_consumption",
      "large_file_hash_deferral_id": "DEFERRAL-0044",
      "size_bytes": 11050624,
      "source_family": "local_external_or_vendor_cache"
    },
    {
      "absolute_path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\data\\external\\features\\XAGUSD\\phase3_m15_2025_2026_external_v2_20260501T000914Z.jsonl",
      "catalog_row_id": "LCAT-000544",
      "exact_next_action": "run_dedicated_owner_approved_hash_manifest_for_large_file_before_consumption",
      "large_file_hash_deferral_id": "DEFERRAL-0045",
      "size_bytes": 51694799,
      "source_family": "local_external_or_vendor_cache"
    },
    {
      "absolute_path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\data\\external\\features\\XAGUSD\\phase3_m15_2025_2026_external_v3_20260501T000956Z.jsonl",
      "catalog_row_id": "LCAT-000545",
      "exact_next_action": "run_dedicated_owner_approved_hash_manifest_for_large_file_before_consumption",
      "large_file_hash_deferral_id": "DEFERRAL-0046",
      "size_bytes": 56380985,
      "source_family": "local_external_or_vendor_cache"
    },
    {
      "absolute_path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\data\\external\\features\\XAGUSD\\phase3_m15_2025_2026_external_v4_20260501T004047Z.jsonl",
      "catalog_row_id": "LCAT-000546",
      "exact_next_action": "run_dedicated_owner_approved_hash_manifest_for_large_file_before_consumption",
      "large_file_hash_deferral_id": "DEFERRAL-0047",
      "size_bytes": 62939330,
      "source_family": "local_external_or_vendor_cache"
    },
    {
      "absolute_path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\data\\external\\features\\XAGUSD\\phase3_m15_2025_2026_external_v5_20260501T004212Z.jsonl",
      "catalog_row_id": "LCAT-000547",
      "exact_next_action": "run_dedicated_owner_approved_hash_manifest_for_large_file_before_consumption",
      "large_file_hash_deferral_id": "DEFERRAL-0048",
      "size_bytes": 62939330,
      "source_family": "local_external_or_vendor_cache"
    },
    {
      "absolute_path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\data\\external\\features\\XAUUSD\\phase3_m15_2022_2026_external_v1_20260501T013833Z.jsonl",
      "catalog_row_id": "LCAT-000552",
      "exact_next_action": "run_dedicated_owner_approved_hash_manifest_for_large_file_before_consumption",
      "large_file_hash_deferral_id": "DEFERRAL-0049",
      "size_bytes": 521962755,
      "source_family": "local_external_or_vendor_cache"
    },
    {
      "absolute_path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\data\\external\\features\\XAUUSD\\phase3_m15_2025_2026_external_v1_20260501T000418Z.jsonl",
      "catalog_row_id": "LCAT-000553",
      "exact_next_action": "run_dedicated_owner_approved_hash_manifest_for_large_file_before_consumption",
      "large_file_hash_deferral_id": "DEFERRAL-0050",
      "size_bytes": 11055616,
      "source_family": "local_external_or_vendor_cache"
    },
    {
      "absolute_path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\data\\external\\features\\XAUUSD\\phase3_m15_2025_2026_external_v2_20260501T000914Z.jsonl",
      "catalog_row_id": "LCAT-000554",
      "exact_next_action": "run_dedicated_owner_approved_hash_manifest_for_large_file_before_consumption",
      "large_file_hash_deferral_id": "DEFERRAL-0051",
      "size_bytes": 66370665,
      "source_family": "local_external_or_vendor_cache"
    },
    {
      "absolute_path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\data\\external\\features\\XAUUSD\\phase3_m15_2025_2026_external_v3_20260501T000956Z.jsonl",
      "catalog_row_id": "LCAT-000555",
      "exact_next_action": "run_dedicated_owner_approved_hash_manifest_for_large_file_before_consumption",
      "large_file_hash_deferral_id": "DEFERRAL-0052",
      "size_bytes": 70994824,
      "source_family": "local_external_or_vendor_cache"
    },
    {
      "absolute_path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\data\\external\\features\\XAUUSD\\phase3_m15_2025_2026_external_v4_20260501T004047Z.jsonl",
      "catalog_row_id": "LCAT-000556",
      "exact_next_action": "run_dedicated_owner_approved_hash_manifest_for_large_file_before_consumption",
      "large_file_hash_deferral_id": "DEFERRAL-0053",
      "size_bytes": 77420380,
      "source_family": "local_external_or_vendor_cache"
    },
    {
      "absolute_path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\data\\external\\features\\XAUUSD\\phase3_m15_2025_2026_external_v5_20260501T004212Z.jsonl",
      "catalog_row_id": "LCAT-000557",
      "exact_next_action": "run_dedicated_owner_approved_hash_manifest_for_large_file_before_consumption",
      "large_file_hash_deferral_id": "DEFERRAL-0054",
      "size_bytes": 77420380,
      "source_family": "local_external_or_vendor_cache"
    },
    {
      "absolute_path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\data\\external\\raw\\cftc_cot\\disagg_combined_20260430T234727Z.json",
      "catalog_row_id": "LCAT-000603",
      "exact_next_action": "run_dedicated_owner_approved_hash_manifest_for_large_file_before_consumption",
      "large_file_hash_deferral_id": "DEFERRAL-0055",
      "size_bytes": 325461396,
      "source_family": "local_external_or_vendor_cache"
    },
    {
      "absolute_path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\data\\external\\raw\\cftc_cot\\disagg_combined_20260501T000733Z.json",
      "catalog_row_id": "LCAT-000605",
      "exact_next_action": "run_dedicated_owner_approved_hash_manifest_for_large_file_before_consumption",
      "large_file_hash_deferral_id": "DEFERRAL-0056",
      "size_bytes": 325461396,
      "source_family": "local_external_or_vendor_cache"
    },
    {
      "absolute_path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\data\\ticks\\NAS100\\2026-04-27.parquet",
      "catalog_row_id": "LCAT-000658",
      "exact_next_action": "run_dedicated_owner_approved_hash_manifest_for_large_file_before_consumption",
      "large_file_hash_deferral_id": "DEFERRAL-0057",
      "size_bytes": 11859172,
      "source_family": "mt5_tick_parquet"
    },
    {
      "absolute_path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\data\\ticks\\NAS100\\2026-04-28.parquet",
      "catalog_row_id": "LCAT-000659",
      "exact_next_action": "run_dedicated_owner_approved_hash_manifest_for_large_file_before_consumption",
      "large_file_hash_deferral_id": "DEFERRAL-0058",
      "size_bytes": 15891143,
      "source_family": "mt5_tick_parquet"
    },
    {
      "absolute_path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\data\\ticks\\NAS100\\2026-04-29.parquet",
      "catalog_row_id": "LCAT-000660",
      "exact_next_action": "run_dedicated_owner_approved_hash_manifest_for_large_file_before_consumption",
      "large_file_hash_deferral_id": "DEFERRAL-0059",
      "size_bytes": 14176528,
      "source_family": "mt5_tick_parquet"
    },
    {
      "absolute_path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\data\\ticks\\NAS100\\2026-04-30.parquet",
      "catalog_row_id": "LCAT-000661",
      "exact_next_action": "run_dedicated_owner_approved_hash_manifest_for_large_file_before_consumption",
      "large_file_hash_deferral_id": "DEFERRAL-0060",
      "size_bytes": 18022394,
      "source_family": "mt5_tick_parquet"
    },
    {
      "absolute_path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\data\\ticks\\NAS100\\2026-05-01.parquet",
      "catalog_row_id": "LCAT-000662",
      "exact_next_action": "run_dedicated_owner_approved_hash_manifest_for_large_file_before_consumption",
      "large_file_hash_deferral_id": "DEFERRAL-0061",
      "size_bytes": 11914727,
      "source_family": "mt5_tick_parquet"
    },
    {
      "absolute_path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\data\\ticks\\NAS100\\2026-05-04.parquet",
      "catalog_row_id": "LCAT-000664",
      "exact_next_action": "run_dedicated_owner_approved_hash_manifest_for_large_file_before_consumption",
      "large_file_hash_deferral_id": "DEFERRAL-0062",
      "size_bytes": 15119257,
      "source_family": "mt5_tick_parquet"
    },
    {
      "absolute_path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\data\\ticks\\NAS100\\2026-05-05.parquet",
      "catalog_row_id": "LCAT-000665",
      "exact_next_action": "run_dedicated_owner_approved_hash_manifest_for_large_file_before_consumption",
      "large_file_hash_deferral_id": "DEFERRAL-0063",
      "size_bytes": 11479489,
      "source_family": "mt5_tick_parquet"
    },
    {
      "absolute_path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\data\\ticks\\NAS100\\2026-05-06.parquet",
      "catalog_row_id": "LCAT-000666",
      "exact_next_action": "run_dedicated_owner_approved_hash_manifest_for_large_file_before_consumption",
      "large_file_hash_deferral_id": "DEFERRAL-0064",
      "size_bytes": 15555785,
      "source_family": "mt5_tick_parquet"
    },
    {
      "absolute_path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\data\\ticks\\NAS100\\2026-05-07.parquet",
      "catalog_row_id": "LCAT-000667",
      "exact_next_action": "run_dedicated_owner_approved_hash_manifest_for_large_file_before_consumption",
      "large_file_hash_deferral_id": "DEFERRAL-0065",
      "size_bytes": 16924674,
      "source_family": "mt5_tick_parquet"
    },
    {
      "absolute_path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\data\\ticks\\NAS100\\2026-05-08.parquet",
      "catalog_row_id": "LCAT-000668",
      "exact_next_action": "run_dedicated_owner_approved_hash_manifest_for_large_file_before_consumption",
      "large_file_hash_deferral_id": "DEFERRAL-0066",
      "size_bytes": 9234536,
      "source_family": "mt5_tick_parquet"
    },
    {
      "absolute_path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\data\\ticks\\XAUUSD\\2026-04-28.parquet",
      "catalog_row_id": "LCAT-000704",
      "exact_next_action": "run_dedicated_owner_approved_hash_manifest_for_large_file_before_consumption",
      "large_file_hash_deferral_id": "DEFERRAL-0067",
      "size_bytes": 9555776,
      "source_family": "mt5_tick_parquet"
    },
    {
      "absolute_path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\data\\ticks\\XAUUSD\\2026-04-29.parquet",
      "catalog_row_id": "LCAT-000705",
      "exact_next_action": "run_dedicated_owner_approved_hash_manifest_for_large_file_before_consumption",
      "large_file_hash_deferral_id": "DEFERRAL-0068",
      "size_bytes": 10721491,
      "source_family": "mt5_tick_parquet"
    },
    {
      "absolute_path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\data\\ticks\\XAUUSD\\2026-04-30.parquet",
      "catalog_row_id": "LCAT-000706",
      "exact_next_action": "run_dedicated_owner_approved_hash_manifest_for_large_file_before_consumption",
      "large_file_hash_deferral_id": "DEFERRAL-0069",
      "size_bytes": 9827605,
      "source_family": "mt5_tick_parquet"
    },
    {
      "absolute_path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\data\\ticks\\XAUUSD\\2026-05-04.parquet",
      "catalog_row_id": "LCAT-000709",
      "exact_next_action": "run_dedicated_owner_approved_hash_manifest_for_large_file_before_consumption",
      "large_file_hash_deferral_id": "DEFERRAL-0070",
      "size_bytes": 9679772,
      "source_family": "mt5_tick_parquet"
    },
    {
      "absolute_path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\data\\ticks\\XAUUSD\\2026-05-07.parquet",
      "catalog_row_id": "LCAT-000712",
      "exact_next_action": "run_dedicated_owner_approved_hash_manifest_for_large_file_before_consumption",
      "large_file_hash_deferral_id": "DEFERRAL-0071",
      "size_bytes": 10667719,
      "source_family": "mt5_tick_parquet"
    },
    {
      "absolute_path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\shadow_logs\\candidate_features_log.jsonl",
      "catalog_row_id": "LCAT-000725",
      "exact_next_action": "run_dedicated_owner_approved_hash_manifest_for_large_file_before_consumption",
      "large_file_hash_deferral_id": "DEFERRAL-0072",
      "size_bytes": 9948352,
      "source_family": "shadow_log_source_control"
    },
    {
      "absolute_path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\shadow_logs\\candidate_ltf_path_order.jsonl",
      "catalog_row_id": "LCAT-000726",
      "exact_next_action": "run_dedicated_owner_approved_hash_manifest_for_large_file_before_consumption",
      "large_file_hash_deferral_id": "DEFERRAL-0073",
      "size_bytes": 10146567,
      "source_family": "shadow_log_source_control"
    },
    {
      "absolute_path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\shadow_logs\\candidate_path_follow.jsonl",
      "catalog_row_id": "LCAT-000729",
      "exact_next_action": "run_dedicated_owner_approved_hash_manifest_for_large_file_before_consumption",
      "large_file_hash_deferral_id": "DEFERRAL-0074",
      "size_bytes": 15356876,
      "source_family": "shadow_log_source_control"
    },
    {
      "absolute_path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\shadow_logs\\context_control_audit.jsonl",
      "catalog_row_id": "LCAT-000731",
      "exact_next_action": "run_dedicated_owner_approved_hash_manifest_for_large_file_before_consumption",
      "large_file_hash_deferral_id": "DEFERRAL-0075",
      "size_bytes": 11327662,
      "source_family": "shadow_log_source_control"
    },
    {
      "absolute_path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\shadow_logs\\fvg_ob_confluence_audit.jsonl",
      "catalog_row_id": "LCAT-000761",
      "exact_next_action": "run_dedicated_owner_approved_hash_manifest_for_large_file_before_consumption",
      "large_file_hash_deferral_id": "DEFERRAL-0076",
      "size_bytes": 25149615,
      "source_family": "shadow_log_source_control"
    },
    {
      "absolute_path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\shadow_logs\\fvg_ob_confluence_resolutions.jsonl",
      "catalog_row_id": "LCAT-000762",
      "exact_next_action": "run_dedicated_owner_approved_hash_manifest_for_large_file_before_consumption",
      "large_file_hash_deferral_id": "DEFERRAL-0077",
      "size_bytes": 11143455,
      "source_family": "shadow_log_source_control"
    },
    {
      "absolute_path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\shadow_logs\\live_candidate_opportunity_clusters.jsonl",
      "catalog_row_id": "LCAT-000770",
      "exact_next_action": "run_dedicated_owner_approved_hash_manifest_for_large_file_before_consumption",
      "large_file_hash_deferral_id": "DEFERRAL-0078",
      "size_bytes": 19020727,
      "source_family": "shadow_log_source_control"
    },
    {
      "absolute_path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\shadow_logs\\live_candidate_strategy_rollups.jsonl",
      "catalog_row_id": "LCAT-000771",
      "exact_next_action": "run_dedicated_owner_approved_hash_manifest_for_large_file_before_consumption",
      "large_file_hash_deferral_id": "DEFERRAL-0079",
      "size_bytes": 45070558,
      "source_family": "shadow_log_source_control"
    },
    {
      "absolute_path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\shadow_logs\\live_structural_strategy_metadata.jsonl",
      "catalog_row_id": "LCAT-000776",
      "exact_next_action": "run_dedicated_owner_approved_hash_manifest_for_large_file_before_consumption",
      "large_file_hash_deferral_id": "DEFERRAL-0080",
      "size_bytes": 13431644,
      "source_family": "shadow_log_source_control"
    },
    {
      "absolute_path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\shadow_logs\\mechanical_context_diagnostics_join.jsonl",
      "catalog_row_id": "LCAT-000780",
      "exact_next_action": "run_dedicated_owner_approved_hash_manifest_for_large_file_before_consumption",
      "large_file_hash_deferral_id": "DEFERRAL-0081",
      "size_bytes": 12654760,
      "source_family": "shadow_log_source_control"
    },
    {
      "absolute_path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\shadow_logs\\opportunity_lifecycle_audit.jsonl",
      "catalog_row_id": "LCAT-000787",
      "exact_next_action": "run_dedicated_owner_approved_hash_manifest_for_large_file_before_consumption",
      "large_file_hash_deferral_id": "DEFERRAL-0082",
      "size_bytes": 10573700,
      "source_family": "shadow_log_source_control"
    },
    {
      "absolute_path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\shadow_logs\\prefill_delivery_path_audit.jsonl",
      "catalog_row_id": "LCAT-000795",
      "exact_next_action": "run_dedicated_owner_approved_hash_manifest_for_large_file_before_consumption",
      "large_file_hash_deferral_id": "DEFERRAL-0083",
      "size_bytes": 28308732,
      "source_family": "shadow_log_source_control"
    },
    {
      "absolute_path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\shadow_logs\\prefill_delivery_path_resolutions.jsonl",
      "catalog_row_id": "LCAT-000796",
      "exact_next_action": "run_dedicated_owner_approved_hash_manifest_for_large_file_before_consumption",
      "large_file_hash_deferral_id": "DEFERRAL-0084",
      "size_bytes": 11243784,
      "source_family": "shadow_log_source_control"
    },
    {
      "absolute_path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\shadow_logs\\regime_decay_outcome_join.jsonl",
      "catalog_row_id": "LCAT-000800",
      "exact_next_action": "run_dedicated_owner_approved_hash_manifest_for_large_file_before_consumption",
      "large_file_hash_deferral_id": "DEFERRAL-0085",
      "size_bytes": 11310367,
      "source_family": "shadow_log_source_control"
    },
    {
      "absolute_path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\shadow_logs\\strategy_follow_evaluations.jsonl",
      "catalog_row_id": "LCAT-000816",
      "exact_next_action": "run_dedicated_owner_approved_hash_manifest_for_large_file_before_consumption",
      "large_file_hash_deferral_id": "DEFERRAL-0086",
      "size_bytes": 11497601,
      "source_family": "shadow_log_source_control"
    },
    {
      "absolute_path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\shadow_logs\\v2b_forward_pair_resolution_audit.jsonl",
      "catalog_row_id": "LCAT-000824",
      "exact_next_action": "run_dedicated_owner_approved_hash_manifest_for_large_file_before_consumption",
      "large_file_hash_deferral_id": "DEFERRAL-0087",
      "size_bytes": 32315168,
      "source_family": "shadow_log_source_control"
    },
    {
      "absolute_path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\shadow_logs\\v2b_forward_pair_resolutions.jsonl",
      "catalog_row_id": "LCAT-000825",
      "exact_next_action": "run_dedicated_owner_approved_hash_manifest_for_large_file_before_consumption",
      "large_file_hash_deferral_id": "DEFERRAL-0088",
      "size_bytes": 11654060,
      "source_family": "shadow_log_source_control"
    },
    {
      "absolute_path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\data\\external\\features\\GBPJPY\\phase3_m15_2022_2026_external_v1_20260501T013833Z.jsonl",
      "catalog_row_id": "LCAT-000910",
      "exact_next_action": "run_dedicated_owner_approved_hash_manifest_for_large_file_before_consumption",
      "large_file_hash_deferral_id": "DEFERRAL-0089",
      "size_bytes": 389258024,
      "source_family": "local_external_or_vendor_cache"
    },
    {
      "absolute_path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\data\\external\\features\\GBPJPY\\phase3_m15_2025_2026_external_v5_20260501T004212Z.jsonl",
      "catalog_row_id": "LCAT-000911",
      "exact_next_action": "run_dedicated_owner_approved_hash_manifest_for_large_file_before_consumption",
      "large_file_hash_deferral_id": "DEFERRAL-0090",
      "size_bytes": 54524286,
      "source_family": "local_external_or_vendor_cache"
    },
    {
      "absolute_path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\data\\external\\features\\GBPUSD\\phase3_m15_2022_2026_external_v1_20260501T013833Z.jsonl",
      "catalog_row_id": "LCAT-000913",
      "exact_next_action": "run_dedicated_owner_approved_hash_manifest_for_large_file_before_consumption",
      "large_file_hash_deferral_id": "DEFERRAL-0091",
      "size_bytes": 389258092,
      "source_family": "local_external_or_vendor_cache"
    },
    {
      "absolute_path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\data\\external\\features\\GBPUSD\\phase3_m15_2025_2026_external_v1_20260501T000418Z.jsonl",
      "catalog_row_id": "LCAT-000914",
      "exact_next_action": "run_dedicated_owner_approved_hash_manifest_for_large_file_before_consumption",
      "large_file_hash_deferral_id": "DEFERRAL-0092",
      "size_bytes": 11658816,
      "source_family": "local_external_or_vendor_cache"
    },
    {
      "absolute_path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\data\\external\\features\\GBPUSD\\phase3_m15_2025_2026_external_v2_20260501T000914Z.jsonl",
      "catalog_row_id": "LCAT-000915",
      "exact_next_action": "run_dedicated_owner_approved_hash_manifest_for_large_file_before_consumption",
      "large_file_hash_deferral_id": "DEFERRAL-0093",
      "size_bytes": 54539857,
      "source_family": "local_external_or_vendor_cache"
    },
    {
      "absolute_path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\data\\external\\features\\GBPUSD\\phase3_m15_2025_2026_external_v3_20260501T000956Z.jsonl",
      "catalog_row_id": "LCAT-000916",
      "exact_next_action": "run_dedicated_owner_approved_hash_manifest_for_large_file_before_consumption",
      "large_file_hash_deferral_id": "DEFERRAL-0094",
      "size_bytes": 54539857,
      "source_family": "local_external_or_vendor_cache"
    },
    {
      "absolute_path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\data\\external\\features\\GBPUSD\\phase3_m15_2025_2026_external_v4_20260501T004047Z.jsonl",
      "catalog_row_id": "LCAT-000917",
      "exact_next_action": "run_dedicated_owner_approved_hash_manifest_for_large_file_before_consumption",
      "large_file_hash_deferral_id": "DEFERRAL-0095",
      "size_bytes": 54539857,
      "source_family": "local_external_or_vendor_cache"
    },
    {
      "absolute_path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\data\\external\\features\\GBPUSD\\phase3_m15_2025_2026_external_v5_20260501T004212Z.jsonl",
      "catalog_row_id": "LCAT-000918",
      "exact_next_action": "run_dedicated_owner_approved_hash_manifest_for_large_file_before_consumption",
      "large_file_hash_deferral_id": "DEFERRAL-0096",
      "size_bytes": 54539857,
      "source_family": "local_external_or_vendor_cache"
    },
    {
      "absolute_path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\data\\external\\features\\NAS100\\phase3_m15_2022_2026_external_v1_20260501T013833Z.jsonl",
      "catalog_row_id": "LCAT-000921",
      "exact_next_action": "run_dedicated_owner_approved_hash_manifest_for_large_file_before_consumption",
      "large_file_hash_deferral_id": "DEFERRAL-0097",
      "size_bytes": 283585832,
      "source_family": "local_external_or_vendor_cache"
    },
    {
      "absolute_path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\data\\external\\features\\NAS100\\phase3_m15_2025_2026_external_v1_20260501T000418Z.jsonl",
      "catalog_row_id": "LCAT-000922",
      "exact_next_action": "run_dedicated_owner_approved_hash_manifest_for_large_file_before_consumption",
      "large_file_hash_deferral_id": "DEFERRAL-0098",
      "size_bytes": 11052288,
      "source_family": "local_external_or_vendor_cache"
    },
    {
      "absolute_path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\data\\external\\features\\NAS100\\phase3_m15_2025_2026_external_v2_20260501T000914Z.jsonl",
      "catalog_row_id": "LCAT-000923",
      "exact_next_action": "run_dedicated_owner_approved_hash_manifest_for_large_file_before_consumption",
      "large_file_hash_deferral_id": "DEFERRAL-0099",
      "size_bytes": 51702752,
      "source_family": "local_external_or_vendor_cache"
    },
    {
      "absolute_path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\data\\external\\features\\NAS100\\phase3_m15_2025_2026_external_v3_20260501T000956Z.jsonl",
      "catalog_row_id": "LCAT-000924",
      "exact_next_action": "run_dedicated_owner_approved_hash_manifest_for_large_file_before_consumption",
      "large_file_hash_deferral_id": "DEFERRAL-0100",
      "size_bytes": 51702752,
      "source_family": "local_external_or_vendor_cache"
    },
    {
      "absolute_path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\data\\external\\features\\NAS100\\phase3_m15_2025_2026_external_v4_20260501T004047Z.jsonl",
      "catalog_row_id": "LCAT-000925",
      "exact_next_action": "run_dedicated_owner_approved_hash_manifest_for_large_file_before_consumption",
      "large_file_hash_deferral_id": "DEFERRAL-0101",
      "size_bytes": 51702752,
      "source_family": "local_external_or_vendor_cache"
    },
    {
      "absolute_path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\data\\external\\features\\NAS100\\phase3_m15_2025_2026_external_v5_20260501T004212Z.jsonl",
      "catalog_row_id": "LCAT-000926",
      "exact_next_action": "run_dedicated_owner_approved_hash_manifest_for_large_file_before_consumption",
      "large_file_hash_deferral_id": "DEFERRAL-0102",
      "size_bytes": 51702752,
      "source_family": "local_external_or_vendor_cache"
    },
    {
      "absolute_path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\data\\external\\features\\US30_CASH\\phase3_m15_2022_2026_external_v1_20260501T013833Z.jsonl",
      "catalog_row_id": "LCAT-000929",
      "exact_next_action": "run_dedicated_owner_approved_hash_manifest_for_large_file_before_consumption",
      "large_file_hash_deferral_id": "DEFERRAL-0103",
      "size_bytes": 283600326,
      "source_family": "local_external_or_vendor_cache"
    },
    {
      "absolute_path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\data\\external\\features\\US30_CASH\\phase3_m15_2025_2026_external_v1_20260501T000418Z.jsonl",
      "catalog_row_id": "LCAT-000930",
      "exact_next_action": "run_dedicated_owner_approved_hash_manifest_for_large_file_before_consumption",
      "large_file_hash_deferral_id": "DEFERRAL-0104",
      "size_bytes": 11061407,
      "source_family": "local_external_or_vendor_cache"
    },
    {
      "absolute_path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\data\\external\\features\\US30_CASH\\phase3_m15_2025_2026_external_v2_20260501T000914Z.jsonl",
      "catalog_row_id": "LCAT-000931",
      "exact_next_action": "run_dedicated_owner_approved_hash_manifest_for_large_file_before_consumption",
      "large_file_hash_deferral_id": "DEFERRAL-0105",
      "size_bytes": 51696591,
      "source_family": "local_external_or_vendor_cache"
    },
    {
      "absolute_path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\data\\external\\features\\US30_CASH\\phase3_m15_2025_2026_external_v3_20260501T000956Z.jsonl",
      "catalog_row_id": "LCAT-000932",
      "exact_next_action": "run_dedicated_owner_approved_hash_manifest_for_large_file_before_consumption",
      "large_file_hash_deferral_id": "DEFERRAL-0106",
      "size_bytes": 51696591,
      "source_family": "local_external_or_vendor_cache"
    },
    {
      "absolute_path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\data\\external\\features\\US30_CASH\\phase3_m15_2025_2026_external_v4_20260501T004047Z.jsonl",
      "catalog_row_id": "LCAT-000933",
      "exact_next_action": "run_dedicated_owner_approved_hash_manifest_for_large_file_before_consumption",
      "large_file_hash_deferral_id": "DEFERRAL-0107",
      "size_bytes": 51696591,
      "source_family": "local_external_or_vendor_cache"
    },
    {
      "absolute_path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\data\\external\\features\\US30_CASH\\phase3_m15_2025_2026_external_v5_20260501T004212Z.jsonl",
      "catalog_row_id": "LCAT-000934",
      "exact_next_action": "run_dedicated_owner_approved_hash_manifest_for_large_file_before_consumption",
      "large_file_hash_deferral_id": "DEFERRAL-0108",
      "size_bytes": 51696591,
      "source_family": "local_external_or_vendor_cache"
    },
    {
      "absolute_path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\data\\external\\features\\USDJPY\\phase3_m15_2022_2026_external_v1_20260501T013833Z.jsonl",
      "catalog_row_id": "LCAT-000937",
      "exact_next_action": "run_dedicated_owner_approved_hash_manifest_for_large_file_before_consumption",
      "large_file_hash_deferral_id": "DEFERRAL-0109",
      "size_bytes": 389258095,
      "source_family": "local_external_or_vendor_cache"
    },
    {
      "absolute_path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\data\\external\\features\\USDJPY\\phase3_m15_2025_2026_external_v5_20260501T004212Z.jsonl",
      "catalog_row_id": "LCAT-000938",
      "exact_next_action": "run_dedicated_owner_approved_hash_manifest_for_large_file_before_consumption",
      "large_file_hash_deferral_id": "DEFERRAL-0110",
      "size_bytes": 54539855,
      "source_family": "local_external_or_vendor_cache"
    },
    {
      "absolute_path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\data\\external\\features\\XAGUSD\\phase3_m15_2022_2026_external_v1_20260501T013833Z.jsonl",
      "catalog_row_id": "LCAT-000940",
      "exact_next_action": "run_dedicated_owner_approved_hash_manifest_for_large_file_before_consumption",
      "large_file_hash_deferral_id": "DEFERRAL-0111",
      "size_bytes": 421958084,
      "source_family": "local_external_or_vendor_cache"
    },
    {
      "absolute_path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\data\\external\\features\\XAGUSD\\phase3_m15_2025_2026_external_v1_20260501T000418Z.jsonl",
      "catalog_row_id": "LCAT-000941",
      "exact_next_action": "run_dedicated_owner_approved_hash_manifest_for_large_file_before_consumption",
      "large_file_hash_deferral_id": "DEFERRAL-0112",
      "size_bytes": 11050624,
      "source_family": "local_external_or_vendor_cache"
    },
    {
      "absolute_path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\data\\external\\features\\XAGUSD\\phase3_m15_2025_2026_external_v2_20260501T000914Z.jsonl",
      "catalog_row_id": "LCAT-000942",
      "exact_next_action": "run_dedicated_owner_approved_hash_manifest_for_large_file_before_consumption",
      "large_file_hash_deferral_id": "DEFERRAL-0113",
      "size_bytes": 51694799,
      "source_family": "local_external_or_vendor_cache"
    },
    {
      "absolute_path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\data\\external\\features\\XAGUSD\\phase3_m15_2025_2026_external_v3_20260501T000956Z.jsonl",
      "catalog_row_id": "LCAT-000943",
      "exact_next_action": "run_dedicated_owner_approved_hash_manifest_for_large_file_before_consumption",
      "large_file_hash_deferral_id": "DEFERRAL-0114",
      "size_bytes": 56380985,
      "source_family": "local_external_or_vendor_cache"
    },
    {
      "absolute_path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\data\\external\\features\\XAGUSD\\phase3_m15_2025_2026_external_v4_20260501T004047Z.jsonl",
      "catalog_row_id": "LCAT-000944",
      "exact_next_action": "run_dedicated_owner_approved_hash_manifest_for_large_file_before_consumption",
      "large_file_hash_deferral_id": "DEFERRAL-0115",
      "size_bytes": 62939330,
      "source_family": "local_external_or_vendor_cache"
    },
    {
      "absolute_path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\data\\external\\features\\XAGUSD\\phase3_m15_2025_2026_external_v5_20260501T004212Z.jsonl",
      "catalog_row_id": "LCAT-000945",
      "exact_next_action": "run_dedicated_owner_approved_hash_manifest_for_large_file_before_consumption",
      "large_file_hash_deferral_id": "DEFERRAL-0116",
      "size_bytes": 62939330,
      "source_family": "local_external_or_vendor_cache"
    },
    {
      "absolute_path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\data\\external\\features\\XAUUSD\\phase3_m15_2022_2026_external_v1_20260501T013833Z.jsonl",
      "catalog_row_id": "LCAT-000950",
      "exact_next_action": "run_dedicated_owner_approved_hash_manifest_for_large_file_before_consumption",
      "large_file_hash_deferral_id": "DEFERRAL-0117",
      "size_bytes": 521962755,
      "source_family": "local_external_or_vendor_cache"
    },
    {
      "absolute_path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\data\\external\\features\\XAUUSD\\phase3_m15_2025_2026_external_v1_20260501T000418Z.jsonl",
      "catalog_row_id": "LCAT-000951",
      "exact_next_action": "run_dedicated_owner_approved_hash_manifest_for_large_file_before_consumption",
      "large_file_hash_deferral_id": "DEFERRAL-0118",
      "size_bytes": 11055616,
      "source_family": "local_external_or_vendor_cache"
    },
    {
      "absolute_path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\data\\external\\features\\XAUUSD\\phase3_m15_2025_2026_external_v2_20260501T000914Z.jsonl",
      "catalog_row_id": "LCAT-000952",
      "exact_next_action": "run_dedicated_owner_approved_hash_manifest_for_large_file_before_consumption",
      "large_file_hash_deferral_id": "DEFERRAL-0119",
      "size_bytes": 66370665,
      "source_family": "local_external_or_vendor_cache"
    },
    {
      "absolute_path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\data\\external\\features\\XAUUSD\\phase3_m15_2025_2026_external_v3_20260501T000956Z.jsonl",
      "catalog_row_id": "LCAT-000953",
      "exact_next_action": "run_dedicated_owner_approved_hash_manifest_for_large_file_before_consumption",
      "large_file_hash_deferral_id": "DEFERRAL-0120",
      "size_bytes": 70994824,
      "source_family": "local_external_or_vendor_cache"
    },
    {
      "absolute_path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\data\\external\\features\\XAUUSD\\phase3_m15_2025_2026_external_v4_20260501T004047Z.jsonl",
      "catalog_row_id": "LCAT-000954",
      "exact_next_action": "run_dedicated_owner_approved_hash_manifest_for_large_file_before_consumption",
      "large_file_hash_deferral_id": "DEFERRAL-0121",
      "size_bytes": 77420380,
      "source_family": "local_external_or_vendor_cache"
    },
    {
      "absolute_path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\data\\external\\features\\XAUUSD\\phase3_m15_2025_2026_external_v5_20260501T004212Z.jsonl",
      "catalog_row_id": "LCAT-000955",
      "exact_next_action": "run_dedicated_owner_approved_hash_manifest_for_large_file_before_consumption",
      "large_file_hash_deferral_id": "DEFERRAL-0122",
      "size_bytes": 77420380,
      "source_family": "local_external_or_vendor_cache"
    },
    {
      "absolute_path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\data\\external\\raw\\cftc_cot\\disagg_combined_20260430T234727Z.json",
      "catalog_row_id": "LCAT-001001",
      "exact_next_action": "run_dedicated_owner_approved_hash_manifest_for_large_file_before_consumption",
      "large_file_hash_deferral_id": "DEFERRAL-0123",
      "size_bytes": 325461396,
      "source_family": "local_external_or_vendor_cache"
    },
    {
      "absolute_path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\data\\external\\raw\\cftc_cot\\disagg_combined_20260501T000733Z.json",
      "catalog_row_id": "LCAT-001003",
      "exact_next_action": "run_dedicated_owner_approved_hash_manifest_for_large_file_before_consumption",
      "large_file_hash_deferral_id": "DEFERRAL-0124",
      "size_bytes": 325461396,
      "source_family": "local_external_or_vendor_cache"
    }
  ],
  "live_effect": false,
  "opens_live_restart": false,
  "opens_live_trading_behavior": false,
  "opens_mt5_order_account_history_behavior": false,
  "opens_paid_api_or_databento_route": false,
  "opens_promotion": false,
  "opens_registry_edit": false,
  "opens_remote_push": false,
  "opens_result_scoring": false,
  "opens_validation": false,
  "outcome_review_opened": false,
  "promotion_verdict": "NO_PROMOTION_VERDICT",
  "route_id": "GTOS_LOCAL_RESEARCH_DATA_CATALOG_IMPLEMENTATION_ROUTE",
  "schema_version": "gtos_local_research_data_catalog_implementation_route_v1",
  "sensitive_path_not_opened_count": 13,
  "sensitive_paths_not_opened": [
    {
      "path": "C:\\tmp\\gtos_otb\\NOFILLTICKRECOVERY\\data\\account_history\\mt5_deals_2026-04-27_2026-05-05.jsonl",
      "read_action": "not_opened",
      "root_id": "current_worktree_data_root",
      "skip_reason": "sensitive_path_fragment:account_history"
    },
    {
      "path": "C:\\tmp\\gtos_otb\\NOFILLTICKRECOVERY\\shadow_logs\\account_pnl_truth_reconciliation.jsonl",
      "read_action": "not_opened",
      "root_id": "current_worktree_shadow_logs",
      "skip_reason": "sensitive_path_fragment:account_pnl"
    },
    {
      "path": "C:\\tmp\\gtos_otb\\NOFILLTICKRECOVERY\\shadow_logs\\account_truth_reconciliation_status.jsonl",
      "read_action": "not_opened",
      "root_id": "current_worktree_shadow_logs",
      "skip_reason": "sensitive_path_fragment:account_truth"
    },
    {
      "path": "C:\\tmp\\gtos_otb\\NOFILLTICKRECOVERY\\shadow_logs\\broker_actual_r_audit.jsonl",
      "read_action": "not_opened",
      "root_id": "current_worktree_shadow_logs",
      "skip_reason": "sensitive_path_fragment:broker_actual_r"
    },
    {
      "path": "C:\\tmp\\gtos_otb\\NOFILLTICKRECOVERY\\shadow_logs\\daily_pnl.json",
      "read_action": "not_opened",
      "root_id": "current_worktree_shadow_logs",
      "skip_reason": "sensitive_path_fragment:daily_pnl"
    },
    {
      "path": "C:\\tmp\\gtos_otb\\NOFILLTICKRECOVERY\\shadow_logs\\daily_pnl_history.jsonl",
      "read_action": "not_opened",
      "root_id": "current_worktree_shadow_logs",
      "skip_reason": "sensitive_path_fragment:daily_pnl"
    },
    {
      "path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\data\\account_history\\mt5_deals_2026-04-27_2026-05-05.jsonl",
      "read_action": "not_opened",
      "root_id": "absolute_main_data_root",
      "skip_reason": "sensitive_path_fragment:account_history"
    },
    {
      "path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\shadow_logs\\account_pnl_truth_reconciliation.jsonl",
      "read_action": "not_opened",
      "root_id": "absolute_main_shadow_logs",
      "skip_reason": "sensitive_path_fragment:account_pnl"
    },
    {
      "path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\shadow_logs\\account_truth_reconciliation_status.jsonl",
      "read_action": "not_opened",
      "root_id": "absolute_main_shadow_logs",
      "skip_reason": "sensitive_path_fragment:account_truth"
    },
    {
      "path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\shadow_logs\\broker_actual_r_audit.jsonl",
      "read_action": "not_opened",
      "root_id": "absolute_main_shadow_logs",
      "skip_reason": "sensitive_path_fragment:broker_actual_r"
    },
    {
      "path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\shadow_logs\\daily_pnl.json",
      "read_action": "not_opened",
      "root_id": "absolute_main_shadow_logs",
      "skip_reason": "sensitive_path_fragment:daily_pnl"
    },
    {
      "path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\shadow_logs\\daily_pnl_history.jsonl",
      "read_action": "not_opened",
      "root_id": "absolute_main_shadow_logs",
      "skip_reason": "sensitive_path_fragment:daily_pnl"
    },
    {
      "path": "C:\\tmp\\gtos_otb\\G0FWDCAPREADY\\data\\account_history\\mt5_deals_2026-04-27_2026-05-05.jsonl",
      "read_action": "not_opened",
      "root_id": "prior_worktree_root",
      "skip_reason": "sensitive_path_fragment:account_history"
    }
  ],
  "terminal_decision": "ACCEPT_AS_LOCAL_RESEARCH_DATA_CATALOG_TOOLING",
  "validation_safe": false
}
```
