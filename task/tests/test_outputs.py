import json
import os

REPORT_PATH = os.environ.get("TEST_REPORT_PATH", "/app/report.json")


def test_file_exists_and_not_symlink():
    """Verify output format output artifact exists as a regular file."""
    assert os.path.exists(REPORT_PATH) and not os.path.islink(REPORT_PATH)


def test_report_schema_and_keys():
    """Verify the normative report schema, types, and 23-order cardinality."""
    with open(REPORT_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)
    assert set(data.keys()) == {"orders"}
    orders = data.get("orders", [])
    assert len(orders) == 23, "Expected 23 order results in report"
    expected_keys = {"order_id", "allocated_qty", "shortfall_qty", "limiting_resource"}
    for x in orders:
        assert isinstance(x, dict) and set(x.keys()) == expected_keys
        assert isinstance(x["order_id"], str)
        assert isinstance(x["allocated_qty"], int) and not isinstance(x["allocated_qty"], bool)
        assert isinstance(x["shortfall_qty"], int) and not isinstance(x["shortfall_qty"], bool)
        assert x["limiting_resource"] is None or isinstance(x["limiting_resource"], str)


def test_output_sorting():
    """Verify output format requires results sorted ascending by order_id."""
    with open(REPORT_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)
    expected_ids = ["O1", "O10C", "O11", "O12", "O15", "O15b", "O16", "O17", "O18", "O2", "O3", "O3_N1", "O3_N2", "O3b", "O4", "O5", "O6C", "O7", "O8", "O9", "OA", "OB", "OC"]
    # Verify the actual contract order below.
    assert [x["order_id"] for x in data["orders"]] == expected_ids


def _get_orders_map():
    with open(REPORT_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)
    return {x["order_id"]: x for x in data["orders"]}


def test_order_O1_batch_rounding_and_parent_netting():
    """Verify Rule 2 parent netting and Rule 3 batch rounding for O1."""
    m = _get_orders_map()
    assert m["O1"]["allocated_qty"] == 12
    assert m["O1"]["shortfall_qty"] == 0
    assert m["O1"]["limiting_resource"] is None


def test_order_O2_aggregated_bom_explosion():
    """Verify Rule 1 shared-demand aggregation across the O2 BOM DAG."""
    m = _get_orders_map()
    assert m["O2"]["allocated_qty"] == 10
    assert m["O2"]["shortfall_qty"] == 0
    assert m["O2"]["limiting_resource"] is None


def test_order_O3_deterministic_substitution():
    """Verify Rule 4 preference-ranked substitution for O3."""
    m = _get_orders_map()
    assert m["O3"]["allocated_qty"] == 6
    assert m["O3"]["shortfall_qty"] == 4
    assert m["O3"]["limiting_resource"] == "L3"


def test_order_O3_N1_substitute_tie_break():
    """Verify Rule 4 alphabetical tie-breaking among equal-rank substitutes for new coverage."""
    m = _get_orders_map()
    assert m["O3_N1"]["allocated_qty"] == 5
    assert m["O3_N1"]["shortfall_qty"] == 0
    assert m["O3_N1"]["limiting_resource"] is None


def test_order_O3_N2_substitute_tie_break():
    """Verify Rule 4 alphabetical tie-breaking side effect propagates to next order."""
    m = _get_orders_map()
    assert m["O3_N2"]["allocated_qty"] == 5
    assert m["O3_N2"]["shortfall_qty"] == 0
    assert m["O3_N2"]["limiting_resource"] is None


def test_order_O3b_substitute_tie_break():
    """Verify Rule 4 alphabetical tie-breaking among equal-rank substitutes."""
    m = _get_orders_map()
    assert m["O3b"]["allocated_qty"] == 0
    assert m["O3b"]["shortfall_qty"] == 10
    assert m["O3b"]["limiting_resource"] == "SUB_L3_B"


def test_order_O4_gross_limiting_resource_and_tie_break():
    """Verify Rule 5 gross limiting-resource ratio and deterministic tie-break."""
    m = _get_orders_map()
    assert m["O4"]["allocated_qty"] == 3
    assert m["O4"]["shortfall_qty"] == 3
    assert m["O4"]["limiting_resource"] == "L_TIE"


def test_order_O5_stateful_depletion():
    """Verify Rule 6 stateful inventory and workcenter depletion across orders."""
    m = _get_orders_map()
    assert m["O5"]["allocated_qty"] == 9
    assert m["O5"]["shortfall_qty"] == 6
    assert m["O5"]["limiting_resource"] == "WC1"


def test_order_O6C_positive_partial_build_is_canceled_without_consumption():
    """Verify the Rule 6 50-percent cancellation threshold for O6C."""
    m = _get_orders_map()
    assert m["O6C"]["allocated_qty"] == 0
    assert m["O6C"]["shortfall_qty"] == 5
    assert m["O6C"]["limiting_resource"] == "L_CANCEL"


def test_order_O7_proves_canceled_order_consumes_no_inventory():
    """Verify Rule 6 cancellation leaves inventory and capacity available to O7."""
    m = _get_orders_map()
    assert m["O7"]["allocated_qty"] == 2
    assert m["O7"]["shortfall_qty"] == 0
    assert m["O7"]["limiting_resource"] is None


def test_order_O8_deep_shared_bom_aggregation():
    """Verify Rule 1 aggregation through the deeper shared SA4-to-SA3 BOM."""
    m = _get_orders_map()
    assert m["O8"]["allocated_qty"] == 4
    assert m["O8"]["shortfall_qty"] == 0
    assert m["O8"]["limiting_resource"] is None


def test_order_O9_carries_deep_subassembly_state_forward():
    """Verify Rule 6 state carryover changes the later O9 allocation."""
    m = _get_orders_map()
    assert m["O9"]["allocated_qty"] == 0
    assert m["O9"]["shortfall_qty"] == 6
    assert m["O9"]["limiting_resource"] == "L5"


def test_order_OA_equal_rank_substitutes_and_batch_rounding():
    """Verify Rules 3 and 4 interact for equal-rank L5 substitutes in OA."""
    m = _get_orders_map()
    assert m["OA"]["allocated_qty"] == 4
    assert m["OA"]["shortfall_qty"] == 4
    assert m["OA"]["limiting_resource"] == "L5"


def test_order_OB_deep_branch_cancellation():
    """Verify Rule 6 cancellation propagates through the deeper O11 branch."""
    m = _get_orders_map()
    assert m["OB"]["allocated_qty"] == 0
    assert m["OB"]["shortfall_qty"] == 5
    assert m["OB"]["limiting_resource"] == "L7"


def test_order_OC_proves_second_cancellation_is_side_effect_free():
    """Verify a canceled deep-branch order does not consume state needed by OC."""
    m = _get_orders_map()
    assert m["OC"]["allocated_qty"] == 2
    assert m["OC"]["shortfall_qty"] == 0
    assert m["OC"]["limiting_resource"] is None


def test_order_O10C_multi_parent_bom_capacity_cancellation():
    """Verify one target reaches SA5 through both direct and nested parents, aggregates the SA5 run once, and DOES NOT cancel when WC5 permits exactly 5 of 10 units."""
    m = _get_orders_map()
    assert m["O10C"]["allocated_qty"] == 5
    assert m["O10C"]["shortfall_qty"] == 5
    assert m["O10C"]["limiting_resource"] == "WC5"


def test_order_O11_proves_O10C_consumed_state():
    """Verify the multi-parent order consumed L9 stock, limiting the immediate successor to 90 units."""
    m = _get_orders_map()
    assert m["O11"]["allocated_qty"] == 90
    assert m["O11"]["shortfall_qty"] == 10
    assert m["O11"]["limiting_resource"] == "L9"


def test_order_O12_scrap_formula():
    """Verify Rule 2 scrap formula application order."""
    m = _get_orders_map()
    assert m["O12"]["allocated_qty"] == 6
    assert m["O12"]["shortfall_qty"] == 4
    assert m["O12"]["limiting_resource"] == "L_SCRAP"

def test_order_O15_boundary_cancellation_50():
    """Verify an order at exactly 50 percent allocation does NOT cancel."""
    m = _get_orders_map()
    assert m["O15"]["allocated_qty"] == 5
    assert m["O15"]["shortfall_qty"] == 5
    assert m["O15"]["limiting_resource"] == "L15"

def test_order_O15b_boundary_cancellation_below_50():
    """Verify an order at 49 percent allocation DOES cancel."""
    m = _get_orders_map()
    assert m["O15b"]["allocated_qty"] == 0
    assert m["O15b"]["shortfall_qty"] == 100
    assert m["O15b"]["limiting_resource"] == "L15b"

def test_order_O16_lexicographical_tiebreaker():
    """Verify limiting resource tie-breaker correctly uses lexicographical string comparison (WC10 vs WC2_B)."""
    m = _get_orders_map()
    assert m["O16"]["allocated_qty"] == 5
    assert m["O16"]["shortfall_qty"] == 5
    assert m["O16"]["limiting_resource"] == "WC10"

def test_order_O17_substitute_floor_semantics():
    """Verify substitute quantity is determined using floor division."""
    m = _get_orders_map()
    assert m["O17"]["allocated_qty"] == 9
    assert m["O17"]["shortfall_qty"] == 1
    assert m["O17"]["limiting_resource"] == "L17"

def test_order_O18_near_equal_bottlenecks():
    """Verify limiting resource correctly identifies the true bottleneck based on exact fulfillment ratios."""
    m = _get_orders_map()
    assert m["O18"]["allocated_qty"] == 7
    assert m["O18"]["shortfall_qty"] == 3
    assert m["O18"]["limiting_resource"] == "L18A"
