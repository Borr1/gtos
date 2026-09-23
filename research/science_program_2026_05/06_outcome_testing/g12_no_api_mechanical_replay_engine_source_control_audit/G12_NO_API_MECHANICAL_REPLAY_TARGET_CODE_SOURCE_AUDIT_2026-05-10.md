# Target Code Source Audit

- status=PASS
- promotion_verdict=NO_PROMOTION_VERDICT
- validation_safe=false outcome_review_opened=false live_effect=false

```json
{
  "actionable_pattern_hits": [],
  "artifact_family": "target_builder_verifier_test_source_audit",
  "changes_live_trading_behavior": false,
  "credentials_touched": false,
  "evidence_class": "G12_SOURCE_CONTROL_AUDIT_ONLY",
  "generated_at_utc": "2026-05-10T21:10:26+00:00",
  "import_records": [
    {
      "forbidden_imports": [],
      "imports": [
        "__future__",
        "argparse",
        "collections",
        "csv",
        "dataclasses",
        "datetime",
        "hashlib",
        "json",
        "math",
        "os",
        "pathlib",
        "statistics",
        "subprocess",
        "typing"
      ],
      "path": "research\\science_program_2026_05\\06_outcome_testing\\no_api_mechanical_replay_engine_from_source_universe\\build_no_api_mechanical_replay_engine_from_source_universe_2026_05_10.py"
    },
    {
      "forbidden_imports": [],
      "imports": [
        "__future__",
        "argparse",
        "json",
        "pathlib",
        "typing"
      ],
      "path": "research\\science_program_2026_05\\06_outcome_testing\\no_api_mechanical_replay_engine_from_source_universe\\verify_no_api_mechanical_replay_engine_from_source_universe_2026_05_10.py"
    },
    {
      "forbidden_imports": [],
      "imports": [
        "__future__",
        "csv",
        "datetime",
        "importlib",
        "json",
        "pathlib",
        "sys"
      ],
      "path": "research\\science_program_2026_05\\06_outcome_testing\\no_api_mechanical_replay_engine_from_source_universe\\test_no_api_mechanical_replay_engine_from_source_universe_2026_05_10.py"
    }
  ],
  "issues": [],
  "live_effect": false,
  "local_git_rev_parse_only": true,
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
  "pattern_hits_reviewed_as_declarative_or_policy": [
    {
      "line": 1982,
      "path": "research\\science_program_2026_05\\06_outcome_testing\\no_api_mechanical_replay_engine_from_source_universe\\build_no_api_mechanical_replay_engine_from_source_universe_2026_05_10.py",
      "pattern": "remote_push",
      "snippet": ", AI/API, paid vendor, prompt/config/risk/safety, remote, credential, or live behavior surface was opened."
    },
    {
      "line": 2061,
      "path": "research\\science_program_2026_05\\06_outcome_testing\\no_api_mechanical_replay_engine_from_source_universe\\build_no_api_mechanical_replay_engine_from_source_universe_2026_05_10.py",
      "pattern": "remote_push",
      "snippet": "API/paid/broker-account/prompt/config/risk/safety/remote/credential surface.\",             \"evidence\": \"no"
    },
    {
      "line": 90,
      "path": "research\\science_program_2026_05\\06_outcome_testing\\no_api_mechanical_replay_engine_from_source_universe\\build_no_api_mechanical_replay_engine_from_source_universe_2026_05_10.py",
      "pattern": "credential",
      "snippet": "h\": False,     \"opens_registry_edit\": False,     \"credentials_touched\": False,     \"changes_live_trading_behav"
    },
    {
      "line": 1963,
      "path": "research\\science_program_2026_05\\06_outcome_testing\\no_api_mechanical_replay_engine_from_source_universe\\build_no_api_mechanical_replay_engine_from_source_universe_2026_05_10.py",
      "pattern": "credential",
      "snippet": "ng, promotion, live behavior, paid/vendor access, credentials, remotes, broker account/order/history/deal/posi"
    },
    {
      "line": 1982,
      "path": "research\\science_program_2026_05\\06_outcome_testing\\no_api_mechanical_replay_engine_from_source_universe\\build_no_api_mechanical_replay_engine_from_source_universe_2026_05_10.py",
      "pattern": "credential",
      "snippet": ", paid vendor, prompt/config/risk/safety, remote, credential, or live behavior surface was opened.\",          "
    },
    {
      "line": 2061,
      "path": "research\\science_program_2026_05\\06_outcome_testing\\no_api_mechanical_replay_engine_from_source_universe\\build_no_api_mechanical_replay_engine_from_source_universe_2026_05_10.py",
      "pattern": "credential",
      "snippet": "d/broker-account/prompt/config/risk/safety/remote/credential surface.\",             \"evidence\": \"no-leak audit"
    },
    {
      "line": 85,
      "path": "research\\science_program_2026_05\\06_outcome_testing\\no_api_mechanical_replay_engine_from_source_universe\\build_no_api_mechanical_replay_engine_from_source_universe_2026_05_10.py",
      "pattern": "live_restart",
      "snippet": "ns_live_trading_behavior\": False,     \"opens_live_restart\": False,     \"opens_paid_api_or_databento_route\":"
    },
    {
      "line": 52,
      "path": "research\\science_program_2026_05\\06_outcome_testing\\no_api_mechanical_replay_engine_from_source_universe\\build_no_api_mechanical_replay_engine_from_source_universe_2026_05_10.py",
      "pattern": "prompt_config_risk_safety",
      "snippet": "= (     \"research/science_program_2026_05/04_goal_prompts/\"     \"G12_NO_API_MECHANICAL_REPLAY_ENGINE_SOURCE_"
    },
    {
      "line": 1914,
      "path": "research\\science_program_2026_05\\06_outcome_testing\\no_api_mechanical_replay_engine_from_source_universe\\build_no_api_mechanical_replay_engine_from_source_universe_2026_05_10.py",
      "pattern": "prompt_config_risk_safety",
      "snippet": "account_history_calls\": 0,         \"prompt_config_risk_safety_changes\": 0,         \"projection_only_boun"
    },
    {
      "line": 1964,
      "path": "research\\science_program_2026_05\\06_outcome_testing\\no_api_mechanical_replay_engine_from_source_universe\\build_no_api_mechanical_replay_engine_from_source_universe_2026_05_10.py",
      "pattern": "prompt_config_risk_safety",
      "snippet": "ry/deal/position use, \"         \"or prompt/config/risk/safety changes; independently audit the no-api me"
    },
    {
      "line": 1982,
      "path": "research\\science_program_2026_05\\06_outcome_testing\\no_api_mechanical_replay_engine_from_source_universe\\build_no_api_mechanical_replay_engine_from_source_universe_2026_05_10.py",
      "pattern": "prompt_config_risk_safety",
      "snippet": "oker actual-R, AI/API, paid vendor, prompt/config/risk/safety, remote, credential, or live behavior surf"
    },
    {
      "line": 2061,
      "path": "research\\science_program_2026_05\\06_outcome_testing\\no_api_mechanical_replay_engine_from_source_universe\\build_no_api_mechanical_replay_engine_from_source_universe_2026_05_10.py",
      "pattern": "prompt_config_risk_safety",
      "snippet": "result/live/API/paid/broker-account/prompt/config/risk/safety/remote/credential surface.\",             \""
    },
    {
      "line": 87,
      "path": "research\\science_program_2026_05\\06_outcome_testing\\no_api_mechanical_replay_engine_from_source_universe\\build_no_api_mechanical_replay_engine_from_source_universe_2026_05_10.py",
      "pattern": "broker_account_order_history",
      "snippet": "_or_databento_route\": False,     \"opens_mt5_order_account_history_behavior\": False,     \"opens_remote_push\": False,"
    },
    {
      "line": 104,
      "path": "research\\science_program_2026_05\\06_outcome_testing\\no_api_mechanical_replay_engine_from_source_universe\\build_no_api_mechanical_replay_engine_from_source_universe_2026_05_10.py",
      "pattern": "broker_account_order_history",
      "snippet": "xpectancy\",     \"profit\",     \"loss_amount\",     \"account_history\",     \"deal\",     \"position\", )   KILL_ZONES_UTC:"
    },
    {
      "line": 1913,
      "path": "research\\science_program_2026_05\\06_outcome_testing\\no_api_mechanical_replay_engine_from_source_universe\\build_no_api_mechanical_replay_engine_from_source_universe_2026_05_10.py",
      "pattern": "broker_account_order_history",
      "snippet": "       \"paid_vendor_calls\": 0,         \"mt5_order_account_history_calls\": 0,         \"prompt_config_risk_safety_cha"
    },
    {
      "line": 46,
      "path": "research\\science_program_2026_05\\06_outcome_testing\\no_api_mechanical_replay_engine_from_source_universe\\verify_no_api_mechanical_replay_engine_from_source_universe_2026_05_10.py",
      "pattern": "credential",
      "snippet": "ens_remote_push\",     \"opens_registry_edit\",     \"credentials_touched\",     \"changes_live_trading_behavior\", ]"
    },
    {
      "line": 249,
      "path": "research\\science_program_2026_05\\06_outcome_testing\\no_api_mechanical_replay_engine_from_source_universe\\verify_no_api_mechanical_replay_engine_from_source_universe_2026_05_10.py",
      "pattern": "credential",
      "snippet": "e,         \"opens_registry_edit\": False,         \"credentials_touched\": False,         \"changes_live_trading_b"
    },
    {
      "line": 41,
      "path": "research\\science_program_2026_05\\06_outcome_testing\\no_api_mechanical_replay_engine_from_source_universe\\verify_no_api_mechanical_replay_engine_from_source_universe_2026_05_10.py",
      "pattern": "live_restart",
      "snippet": "   \"opens_live_trading_behavior\",     \"opens_live_restart\",     \"opens_paid_api_or_databento_route\",     \"o"
    },
    {
      "line": 244,
      "path": "research\\science_program_2026_05\\06_outcome_testing\\no_api_mechanical_replay_engine_from_source_universe\\verify_no_api_mechanical_replay_engine_from_source_universe_2026_05_10.py",
      "pattern": "live_restart",
      "snippet": "ive_trading_behavior\": False,         \"opens_live_restart\": False,         \"opens_paid_api_or_databento_rou"
    },
    {
      "line": 43,
      "path": "research\\science_program_2026_05\\06_outcome_testing\\no_api_mechanical_replay_engine_from_source_universe\\verify_no_api_mechanical_replay_engine_from_source_universe_2026_05_10.py",
      "pattern": "broker_account_order_history",
      "snippet": "aid_api_or_databento_route\",     \"opens_mt5_order_account_history_behavior\",     \"opens_remote_push\",     \"opens_re"
    },
    {
      "line": 56,
      "path": "research\\science_program_2026_05\\06_outcome_testing\\no_api_mechanical_replay_engine_from_source_universe\\verify_no_api_mechanical_replay_engine_from_source_universe_2026_05_10.py",
      "pattern": "broker_account_order_history",
      "snippet": "actual_r\",     \"win_rate\",     \"expectancy\",     \"account_history\",     \"deal\",     \"position\", }  PLACEHOLDER_TERM"
    },
    {
      "line": 246,
      "path": "research\\science_program_2026_05\\06_outcome_testing\\no_api_mechanical_replay_engine_from_source_universe\\verify_no_api_mechanical_replay_engine_from_source_universe_2026_05_10.py",
      "pattern": "broker_account_order_history",
      "snippet": "databento_route\": False,         \"opens_mt5_order_account_history_behavior\": False,         \"opens_remote_push\": Fa"
    }
  ],
  "promotion_verdict": "NO_PROMOTION_VERDICT",
  "route_id": "G12_NO_API_MECHANICAL_REPLAY_ENGINE_SOURCE_CONTROL_AUDIT",
  "schema_version": "g12_no_api_mechanical_replay_source_control_audit_v1",
  "source_files": [
    "research\\science_program_2026_05\\06_outcome_testing\\no_api_mechanical_replay_engine_from_source_universe\\build_no_api_mechanical_replay_engine_from_source_universe_2026_05_10.py",
    "research\\science_program_2026_05\\06_outcome_testing\\no_api_mechanical_replay_engine_from_source_universe\\verify_no_api_mechanical_replay_engine_from_source_universe_2026_05_10.py",
    "research\\science_program_2026_05\\06_outcome_testing\\no_api_mechanical_replay_engine_from_source_universe\\test_no_api_mechanical_replay_engine_from_source_universe_2026_05_10.py"
  ],
  "status": "PASS",
  "subprocess_usage": [],
  "validation_safe": false
}
```
