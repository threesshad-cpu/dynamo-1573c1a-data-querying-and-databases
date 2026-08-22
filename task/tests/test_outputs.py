import json
import os

REPORT_PATH = os.environ.get("TEST_REPORT_PATH", "/app/report.json")


def test_file_exists_and_not_symlink():
    """Verify that /app/report.json exists and is a regular file."""
    assert os.path.exists(REPORT_PATH) and not os.path.islink(REPORT_PATH)


def test_report_schema_and_keys():
    """Verify exact schema keys and value types in report.json."""
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
    """Verify that orders in /app/report.json are sorted by order_id ascending."""
    with open(REPORT_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)
    expected_ids = ["O1", "O2", "O3", "O3b", "O4", "O5", "O6C", "O7", "O8", "O9", "O10", "O11", "O12"]
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
    """P6 reaches SA3 through both SA4 and a direct edge; shared demand must be aggregated."""
    m = _get_orders_map()
    assert m["O8"]["allocated_qty"] == 4
    assert m["O8"]["shortfall_qty"] == 0
    assert m["O8"]["limiting_resource"] is None


def test_order_O9_carries_deep_subassembly_state_forward():
    """O8 consumes all prebuilt SA4, forcing O9 to manufacture it and hit the shared L5 pool."""
    m = _get_orders_map()
    assert m["O9"]["allocated_qty"] == 0
    assert m["O9"]["shortfall_qty"] == 6
    assert m["O9"]["limiting_resource"] == "L5"


def test_order_O10_equal_rank_substitutes_and_batch_rounding():
    """O10 consumes L5 using both equal-rank substitutes in deterministic ID order."""
    m = _get_orders_map()
    assert m["O10"]["allocated_qty"] == 4
    assert m["O10"]["shortfall_qty"] == 4
    assert m["O10"]["limiting_resource"] == "L5"


def test_order_O11_deep_branch_cancellation():
    """O11 can build only 2/5, so Rule 6 cancels it and reports the constraining leaf."""
    m = _get_orders_map()
    assert m["O11"]["allocated_qty"] == 0
    assert m["O11"]["shortfall_qty"] == 5
    assert m["O11"]["limiting_resource"] == "L7"


def test_order_O12_proves_second_cancellation_is_side_effect_free():
    """O12 immediately reuses the L7 stock that O11 was forbidden to consume."""
    m = _get_orders_map()
    assert m["O12"]["allocated_qty"] == 2
    assert m["O12"]["shortfall_qty"] == 0
    assert m["O12"]["limiting_resource"] is None
