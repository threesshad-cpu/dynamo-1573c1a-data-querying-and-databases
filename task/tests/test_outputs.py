import json
import os

REPORT_PATH = "/app/report.json"


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
    expected_ids = ["O01", "O02", "O03", "O04", "O05", "O06", "O07", "O08"]
    assert [x["order_id"] for x in data["orders"]] == expected_ids


def test_order_allocations():
    """Verify multi-level MRP allocation with routing, workcenter capacity, setup scrap, and substitute parts.

    Dataset: Eight production orders processed in ascending priority order (O01 to O08).

    - O01 (P2 x 12): Fully buildable. alloc=12, sf=0, limiting=None.
    - O02 (P1 x 30, batch=5): Assembly line WC2 available hours (40.0) restrict build to 25 units.
      alloc=25, sf=5, limiting=WC2.
    - O03 (P3 x 15, batch=2): Restricted by circuit board L5 inventory (drawing on substitutes).
      alloc=6, sf=9, limiting=L5.
    - O04 (P2 x 20, batch=4): Restricted by bolt L1 inventory. alloc=0, sf=20, limiting=L1.
    - O05 (P1 x 25, batch=5): Restricted by workcenter WC2. alloc=0, sf=25, limiting=WC2.
    - O06 (P3 x 25, batch=2): Restricted by leaf component L5. alloc=0, sf=25, limiting=L5.
    - O07 (P2 x 20, batch=4): Restricted by leaf component L1. alloc=0, sf=20, limiting=L1.
    - O08 (P1 x 15, batch=5): Restricted by workcenter WC2. alloc=0, sf=15, limiting=WC2.

    Sensitivity:
    - Ignoring workcenter routing capacity changes O02 allocated_qty from 25 to 30.
    - Ignoring substitute parts changes O03 allocation or bottleneck ratio.
    - Ignoring setup scrap changes component demand and bottleneck ratios.
    """
    with open(REPORT_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)
    m = {x["order_id"]: x for x in data["orders"]}

    assert (
        m["O01"]["allocated_qty"] == 12
        and m["O01"]["shortfall_qty"] == 0
        and m["O01"]["limiting_resource"] is None
    )
    assert (
        m["O02"]["allocated_qty"] == 25
        and m["O02"]["shortfall_qty"] == 5
        and m["O02"]["limiting_resource"] == "WC2"
    )
    assert (
        m["O03"]["allocated_qty"] == 6
        and m["O03"]["shortfall_qty"] == 9
        and m["O03"]["limiting_resource"] == "L5"
    )
    assert (
        m["O04"]["allocated_qty"] == 0
        and m["O04"]["shortfall_qty"] == 20
        and m["O04"]["limiting_resource"] == "L1"
    )
    assert (
        m["O05"]["allocated_qty"] == 0
        and m["O05"]["shortfall_qty"] == 25
        and m["O05"]["limiting_resource"] == "WC2"
    )
    assert (
        m["O06"]["allocated_qty"] == 0
        and m["O06"]["shortfall_qty"] == 25
        and m["O06"]["limiting_resource"] == "L5"
    )
    assert (
        m["O07"]["allocated_qty"] == 0
        and m["O07"]["shortfall_qty"] == 20
        and m["O07"]["limiting_resource"] == "L1"
    )
    assert (
        m["O08"]["allocated_qty"] == 0
        and m["O08"]["shortfall_qty"] == 15
        and m["O08"]["limiting_resource"] == "WC2"
    )
