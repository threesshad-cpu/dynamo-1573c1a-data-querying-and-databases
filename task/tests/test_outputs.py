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
    assert set(data.keys()) == {
        "orders"
    }, "Top-level object must have exactly one key: 'orders'"
    orders = data.get("orders", [])
    assert len(orders) == 4, "Expected 4 order results in report"
    expected_keys = {
        "order_id",
        "allocated_qty",
        "shortfall_qty",
        "limiting_resource",
    }
    for x in orders:
        assert isinstance(x, dict) and set(x.keys()) == expected_keys
        assert isinstance(x["order_id"], str)
        assert isinstance(x["allocated_qty"], int) and not isinstance(
            x["allocated_qty"], bool
        )
        assert isinstance(x["shortfall_qty"], int) and not isinstance(
            x["shortfall_qty"], bool
        )
        assert x["limiting_resource"] is None or isinstance(
            x["limiting_resource"], str
        )


def test_output_sorting():
    """Verify that orders in /app/report.json are sorted by order_id ascending."""
    with open(REPORT_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)
    expected_ids = ["O1", "O2", "O3", "O4"]
    assert [x["order_id"] for x in data["orders"]] == expected_ids


def _get_orders_map():
    with open(REPORT_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)
    return {x["order_id"]: x for x in data["orders"]}


def test_order_O1_batch_rounding_and_parent_netting():
    """
    Verify Order 1 correctly applies Batch Rounding and Parent/SA Netting.
    O1 requests 12 P1. P1 needs SA1 (batch 2).
    On-hand SA1 (3) is netted before propagation. 
    Remaining 9 SA1 rounds up to 10 SA1. 
    This results in enough inventory to fulfill all 12 units.
    """
    m = _get_orders_map()
    assert m["O1"]["allocated_qty"] == 12
    assert m["O1"]["shortfall_qty"] == 0
    assert m["O1"]["limiting_resource"] is None


def test_order_O2_aggregated_bom_explosion():
    """
    Verify Order 2 correctly aggregates BOM demand across multiple paths.
    P2 requires SA1 and SA2. SA2 also requires SA1.
    SA1 must be aggregated into a single manufacturing run to correctly apply setup hours and batching.
    The order is limited by L2 which is required by SA2.
    """
    m = _get_orders_map()
    assert m["O2"]["allocated_qty"] == 8
    assert m["O2"]["shortfall_qty"] == 2
    assert m["O2"]["limiting_resource"] == "L2"


def test_order_O3_deterministic_substitution():
    """
    Verify Order 3 correctly cascades through substitute parts deterministically.
    P3 requests 10, needs 5 L3 per unit (Total 50).
    L3 (15) + SUB_L3_A (12 units / 2.0 ratio = 6) + SUB_L3_B (8 units / 1.0 ratio = 8) = 29 equivalent units.
    29 / 5 = 5.8 (floored to 5 allocated). Shortfall is 5. Limiting resource is L3.
    """
    m = _get_orders_map()
    assert m["O3"]["allocated_qty"] == 5
    assert m["O3"]["shortfall_qty"] == 5
    assert m["O3"]["limiting_resource"] == "L3"


def test_order_O4_gross_limiting_resource_and_tie_break():
    """
    Verify Order 4 computes limiting resource using gross propagated requirement and ASCII tie-break.
    P4 requires L4 and L_TIE. L_TIE (100 / 500 = 0.2) is more constraining than L4 (30 / 50 = 0.6).
    """
    m = _get_orders_map()
    assert m["O4"]["allocated_qty"] == 1
    assert m["O4"]["shortfall_qty"] == 4
    assert m["O4"]["limiting_resource"] == "L_TIE"
