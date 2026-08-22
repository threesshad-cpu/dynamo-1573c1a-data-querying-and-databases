import json
import os

REPORT_PATH = os.environ.get("TEST_REPORT_PATH", "/app/report.json")


def test_file_exists_and_not_symlink():
    assert os.path.exists(REPORT_PATH) and not os.path.islink(REPORT_PATH)


def test_report_schema_and_keys():
    with open(REPORT_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)
    assert set(data.keys()) == {"orders"}
    orders = data.get("orders", [])
    assert len(orders) == 13, "Expected 13 order results in report"
    expected_keys = {"order_id", "allocated_qty", "shortfall_qty", "limiting_resource"}
    for x in orders:
        assert isinstance(x, dict) and set(x.keys()) == expected_keys
        assert isinstance(x["order_id"], str)
        assert isinstance(x["allocated_qty"], int) and not isinstance(x["allocated_qty"], bool)
        assert isinstance(x["shortfall_qty"], int) and not isinstance(x["shortfall_qty"], bool)
        assert x["limiting_resource"] is None or isinstance(x["limiting_resource"], str)


def test_output_sorting():
    with open(REPORT_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)
    expected_ids = ["O1", "O2", "O3", "O3b", "O4", "O5", "O6C", "O7", "O8", "O9", "OA", "OB", "OC"]
    assert [x["order_id"] for x in data["orders"]] == expected_ids


def _get_orders_map():
    with open(REPORT_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)
    return {x["order_id"]: x for x in data["orders"]}


def test_order_O1_batch_rounding_and_parent_netting():
    m = _get_orders_map()
    assert m["O1"]["allocated_qty"] == 12
    assert m["O1"]["shortfall_qty"] == 0
    assert m["O1"]["limiting_resource"] is None


def test_order_O2_aggregated_bom_explosion():
    m = _get_orders_map()
    assert m["O2"]["allocated_qty"] == 10
    assert m["O2"]["shortfall_qty"] == 0
    assert m["O2"]["limiting_resource"] is None


def test_order_O3_deterministic_substitution():
    m = _get_orders_map()
    assert m["O3"]["allocated_qty"] == 6
    assert m["O3"]["shortfall_qty"] == 4
    assert m["O3"]["limiting_resource"] == "L3"


def test_order_O3b_substitute_tie_break():
    m = _get_orders_map()
    assert m["O3b"]["allocated_qty"] == 0
    assert m["O3b"]["shortfall_qty"] == 10
    assert m["O3b"]["limiting_resource"] == "SUB_L3_B"


def test_order_O4_gross_limiting_resource_and_tie_break():
    m = _get_orders_map()
    assert m["O4"]["allocated_qty"] == 3
    assert m["O4"]["shortfall_qty"] == 3
    assert m["O4"]["limiting_resource"] == "L_TIE"


def test_order_O5_stateful_depletion():
    m = _get_orders_map()
    assert m["O5"]["allocated_qty"] == 9
    assert m["O5"]["shortfall_qty"] == 6
    assert m["O5"]["limiting_resource"] == "WC1"


def test_order_O6C_positive_partial_build_is_canceled_without_consumption():
    m = _get_orders_map()
    assert m["O6C"]["allocated_qty"] == 0
    assert m["O6C"]["shortfall_qty"] == 5
    assert m["O6C"]["limiting_resource"] == "L_CANCEL"


def test_order_O7_proves_canceled_order_consumes_no_inventory():
    m = _get_orders_map()
    assert m["O7"]["allocated_qty"] == 2
    assert m["O7"]["shortfall_qty"] == 0
    assert m["O7"]["limiting_resource"] is None


def test_order_O8_deep_shared_bom_aggregation():
    m = _get_orders_map()
    assert m["O8"]["allocated_qty"] == 4
    assert m["O8"]["shortfall_qty"] == 0
    assert m["O8"]["limiting_resource"] is None


def test_order_O9_carries_deep_subassembly_state_forward():
    m = _get_orders_map()
    assert m["O9"]["allocated_qty"] == 0
    assert m["O9"]["shortfall_qty"] == 6
    assert m["O9"]["limiting_resource"] == "L5"


def test_order_OA_equal_rank_substitutes_and_batch_rounding():
    m = _get_orders_map()
    assert m["OA"]["allocated_qty"] == 4
    assert m["OA"]["shortfall_qty"] == 4
    assert m["OA"]["limiting_resource"] == "L5"


def test_order_OB_deep_branch_cancellation():
    m = _get_orders_map()
    assert m["OB"]["allocated_qty"] == 0
    assert m["OB"]["shortfall_qty"] == 5
    assert m["OB"]["limiting_resource"] == "L7"


def test_order_OC_proves_second_cancellation_is_side_effect_free():
    m = _get_orders_map()
    assert m["OC"]["allocated_qty"] == 2
    assert m["OC"]["shortfall_qty"] == 0
    assert m["OC"]["limiting_resource"] is None
