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
    assert len(orders) == 8, "Expected 8 order results in report"
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
    expected_ids = ["O1", "O2", "O3", "O3b", "O4", "O5", "O6C", "O7"]
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
    Verify Order 2 aggregates shared BOM demand and handles scrap cascading.
    P2 requests 10, needing 10 SA1 (direct) + 20 SA2.
    SA2 needs 21 SA1 (setup_scrap=1 + 20*1) and 63 L2 (setup_scrap=1 + ceil(60*1.03)=62).
    Total SA1 = 31, net 30 (1 on-hand from O1). Build 30 SA1.
    L2 has 50 units. Shortfall of 13 covered by SUB_SHARED (ratio 1.0).
    SUB_SHARED goes from 20 to 7. Fully allocates 10 P2.
    """
    m = _get_orders_map()
    assert m["O2"]["allocated_qty"] == 10
    assert m["O2"]["shortfall_qty"] == 0
    assert m["O2"]["limiting_resource"] is None


def test_order_O3_deterministic_substitution():
    """
    Verify Order 3 correctly cascades through substitute parts deterministically,
    including shared substitutes depleted by previous orders.
    P3 requests 10, needs 5 L3 per unit (Total 50).
    L3 (15) + SUB_L3_A (floor(12/2.5)=4) + SUB_L3_B (floor(8/1.0)=8) +
    SUB_SHARED (floor(7/1.0)=7, only 7 remaining after O2's larger L2 demand) = 34.
    34 / 5 = 6.8 (floored to 6 allocated). Shortfall is 4. Limiting resource is L3.
    """
    m = _get_orders_map()
    assert m["O3"]["allocated_qty"] == 6
    assert m["O3"]["shortfall_qty"] == 4
    assert m["O3"]["limiting_resource"] == "L3"


def test_order_O3b_substitute_tie_break():
    """
    Verify Order 3b correctly reflects inventory depleted by O3's substitute usage.
    O3 consumed all 8 SUB_L3_B (used as substitute for L3 at rank 1).
    P_B directly requires SUB_L3_B, so with 0 remaining, O3b allocates nothing.
    Shortfall = 10. Limiting resource is SUB_L3_B (ratio 0/1 = 0).
    """
    m = _get_orders_map()
    assert m["O3b"]["allocated_qty"] == 0
    assert m["O3b"]["shortfall_qty"] == 10
    assert m["O3b"]["limiting_resource"] == "SUB_L3_B"


def test_order_O4_gross_limiting_resource_and_tie_break():
    """
    Verify Order 4 computes limiting resource using gross propagated requirement (netting subassemblies) and ASCII tie-break.
    P4 requires SA_LIMIT, L_TIE (5), and WC_TIE (5h). SA_LIMIT needs L4 (5).
    Target 3 P4 needs 3 SA_LIMIT. On hand = 2. Net = 1. Batch = 3. Build = 3 SA_LIMIT (uses 15 L4).
    Available L4 = 25, so target 3 is possible.
    Target 4 P4 needs 4 SA_LIMIT. Net = 2. Build = 3 SA_LIMIT (uses 15 L4).
    Gross L4 = 15. Ratio = 25/15 = 1.66.
    Target 4 P4 needs 20 L_TIE and 20h WC_TIE.
    Available L_TIE = 17, WC_TIE = 17.0h.
    Ratios: L_TIE = 17/20 = 0.85, WC_TIE = 17.0/20 = 0.85.
    Tie between "L_TIE" and "WC_TIE". "L_TIE" comes first alphabetically.
    If an agent incorrectly calculates zero-inventory gross requirements, they will build 6 SA_LIMIT (30 L4) and incorrectly pick L4 (25/30 = 0.83 < 0.85).
    """
    m = _get_orders_map()
    assert m["O4"]["allocated_qty"] == 3
    assert m["O4"]["shortfall_qty"] == 3
    assert m["O4"]["limiting_resource"] == "L_TIE"


def test_order_O5_stateful_depletion():
    """
    Verify Order 5 correctly tracks shared workcenter depletion across orders.
    O4 consumed 15 L4, leaving 10 available (from 25).
    O5 requests 15 P5. P5 needs 1 L4 each (10 available) and WC1 hours (1.0/unit).
    After O1 (23h) and O2 (48h), WC1 has only 9 hours remaining.
    WC1 limits O5 to 9 units. 9/15=0.6>=0.5 so allocate 9.
    Limiting resource is WC1 (ratio 9/10 = 0.9, while L4 ratio is 10/10 = 1.0).
    """
    m = _get_orders_map()
    assert m["O5"]["allocated_qty"] == 9
    assert m["O5"]["shortfall_qty"] == 6
    assert m["O5"]["limiting_resource"] == "WC1"


def test_order_O6C_positive_partial_build_is_canceled_without_consumption():
    """
    Verify Rule 6 on an order whose maximum buildable quantity is positive but below 50%.
    O6C requests 5 P_CANCEL and only 2 L_CANCEL are available, so the maximum buildable
    quantity is 2/5 = 40%. The order must be canceled with allocated_qty=0,
    shortfall_qty=5, while still reporting L_CANCEL as the limiting resource.
    """
    m = _get_orders_map()
    assert m["O6C"]["allocated_qty"] == 0
    assert m["O6C"]["shortfall_qty"] == 5
    assert m["O6C"]["limiting_resource"] == "L_CANCEL"


def test_order_O7_proves_canceled_order_consumes_no_inventory():
    """
    Verify the cancellation has no side effects on later orders.
    O6C would consume both L_CANCEL units if its positive partial build were committed,
    but Rule 6 requires cancellation to consume nothing. O7 therefore still fulfills
    its request for 2 P_AFTER from the original 2-unit L_CANCEL stock.
    """
    m = _get_orders_map()
    assert m["O7"]["allocated_qty"] == 2
    assert m["O7"]["shortfall_qty"] == 0
    assert m["O7"]["limiting_resource"] is None
