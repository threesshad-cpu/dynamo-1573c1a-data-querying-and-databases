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
    assert len(orders) == 6, "Expected 6 order results in report"
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
    expected_ids = ["O01", "O02", "O03", "O04", "O05", "O06"]
    assert [x["order_id"] for x in data["orders"]] == expected_ids


def _get_orders_map():
    with open(REPORT_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)
    return {x["order_id"]: x for x in data["orders"]}


def test_order_O01_allocation():
    """Verify O01 allocation (P2 x 14, batch=4): Floored build to batch multiple 12. alloc=12, sf=2, limiting=None."""
    m = _get_orders_map()
    assert m["O01"]["allocated_qty"] == 12
    assert m["O01"]["shortfall_qty"] == 2
    assert m["O01"]["limiting_resource"] is None


def test_order_O02_allocation():
    """Verify O02 allocation (P1 x 30, batch=5): Processed AFTER O03 due to order_id descending tie-breaker. alloc=0, sf=30, limiting=L5."""
    m = _get_orders_map()
    assert m["O02"]["allocated_qty"] == 0
    assert m["O02"]["shortfall_qty"] == 30
    assert m["O02"]["limiting_resource"] == "L5"


def test_order_O03_allocation():
    """Verify O03 allocation (P3 x 15, batch=2): Processed BEFORE O02 due to order_id descending tie-breaker. alloc=14, sf=1, limiting=None."""
    m = _get_orders_map()
    assert m["O03"]["allocated_qty"] == 14
    assert m["O03"]["shortfall_qty"] == 1
    assert m["O03"]["limiting_resource"] is None


def test_order_O04_allocation():
    """Verify O04 allocation (P2 x 20, batch=4): SA1 requires SA2 which needs L5 — fully depleted by O01+O03. alloc=0, sf=20, limiting=L5."""
    m = _get_orders_map()
    assert m["O04"]["allocated_qty"] == 0
    assert m["O04"]["shortfall_qty"] == 20
    assert m["O04"]["limiting_resource"] == "L5"


def test_order_O05_allocation():
    """Verify O05 allocation (P4 x 5, batch=3): Dual-workcenter routing on WC1+WC3 after prior WC consumption. alloc=0, sf=5, limiting=WC3."""
    m = _get_orders_map()
    assert m["O05"]["allocated_qty"] == 0
    assert m["O05"]["shortfall_qty"] == 5
    assert m["O05"]["limiting_resource"] == "WC3"


def test_order_O06_allocation():
    """Verify O06 allocation (P3 x 8, batch=2): Uses 3 excess SA4 from O03 lot rounding to build 2; next batch needs SA2 build requiring depleted L5. alloc=2, sf=6, limiting=L5."""
    m = _get_orders_map()
    assert m["O06"]["allocated_qty"] == 2
    assert m["O06"]["shortfall_qty"] == 6
    assert m["O06"]["limiting_resource"] == "L5"
