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
    assert len(orders) == 10, "Expected 10 order results in report"
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
    expected_ids = ["O01", "O02", "O03", "O04", "O05", "O06", "O07", "O08", "O09", "O10"]
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
    """Verify O02 allocation (P1 x 30, batch=5): Assembly line WC2 available hours (23.0) restrict build to 25 units. alloc=25, sf=5, limiting=WC2."""
    m = _get_orders_map()
    assert m["O02"]["allocated_qty"] == 25
    assert m["O02"]["shortfall_qty"] == 5
    assert m["O02"]["limiting_resource"] == "WC2"


def test_order_O03_allocation():
    """Verify O03 allocation (P3 x 15, batch=2): Tied minimum fulfillment ratio (0.50) between L5 and WC2, tie-broken by ASCII order to L5. alloc=2, sf=13, limiting=L5."""
    m = _get_orders_map()
    assert m["O03"]["allocated_qty"] == 2
    assert m["O03"]["shortfall_qty"] == 13
    assert m["O03"]["limiting_resource"] == "L5"


def test_order_O04_allocation():
    """Verify O04 allocation (P2 x 20, batch=4): Restricted by Steel-Plate L3 inventory. alloc=4, sf=16, limiting=L3."""
    m = _get_orders_map()
    assert m["O04"]["allocated_qty"] == 4
    assert m["O04"]["shortfall_qty"] == 16
    assert m["O04"]["limiting_resource"] == "L3"


def test_order_O05_allocation():
    """Verify O05 allocation (P1 x 25, batch=5): Restricted by Steel-Plate L3 inventory. alloc=0, sf=25, limiting=L3."""
    m = _get_orders_map()
    assert m["O05"]["allocated_qty"] == 0
    assert m["O05"]["shortfall_qty"] == 25
    assert m["O05"]["limiting_resource"] == "L3"


def test_order_O06_allocation():
    """Verify O06 allocation (P3 x 25, batch=2): Restricted by Circuit-Board L5 inventory. alloc=0, sf=25, limiting=L5."""
    m = _get_orders_map()
    assert m["O06"]["allocated_qty"] == 0
    assert m["O06"]["shortfall_qty"] == 25
    assert m["O06"]["limiting_resource"] == "L5"


def test_order_O07_allocation():
    """Verify O07 allocation (P2 x 20, batch=4): Restricted by Steel-Plate L3 inventory. alloc=0, sf=20, limiting=L3."""
    m = _get_orders_map()
    assert m["O07"]["allocated_qty"] == 0
    assert m["O07"]["shortfall_qty"] == 20
    assert m["O07"]["limiting_resource"] == "L3"


def test_order_O08_allocation():
    """Verify O08 allocation (P1 x 15, batch=5): Restricted by Steel-Plate L3 inventory. alloc=0, sf=15, limiting=L3."""
    m = _get_orders_map()
    assert m["O08"]["allocated_qty"] == 0
    assert m["O08"]["shortfall_qty"] == 15
    assert m["O08"]["limiting_resource"] == "L3"


def test_order_O09_allocation():
    """Verify O09 allocation (P4 x 5, batch=3): Dual-workcenter routing on WC1+WC3 both exceed capacity equally. Tied minimum fulfillment ratio (0.50) between WC1 and WC3, tie-broken by ASCII order to WC1. alloc=0, sf=5, limiting=WC1."""
    m = _get_orders_map()
    assert m["O09"]["allocated_qty"] == 0
    assert m["O09"]["shortfall_qty"] == 5
    assert m["O09"]["limiting_resource"] == "WC1"


def test_order_O10_allocation():
    """Verify O10 allocation (P3 x 4, batch=2): Circuit-Board L5 and Assembly-Line WC2 tied at ratio 0.50 after sequential pool depletion. Tie-broken by ASCII order to L5. alloc=0, sf=4, limiting=L5."""
    m = _get_orders_map()
    assert m["O10"]["allocated_qty"] == 0
    assert m["O10"]["shortfall_qty"] == 4
    assert m["O10"]["limiting_resource"] == "L5"

