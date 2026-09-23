from scripts import build_vnext_lane09_cross_lane_merge_dossier_production_package as lane09


def test_lane09_package_keeps_live_production_change_gated():
    payload = lane09.build_outputs(write=False, run_audits=False)
    package = payload["package"]

    assert package["live_production_change_ready"] is False
    assert package["forbidden_surfaces"]["broker_order_deal_position_action"] is False
    assert package["forbidden_surfaces"]["hidden_live_deployment"] is False


