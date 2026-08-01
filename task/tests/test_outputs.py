import json
import os

REPORT_PATH = "/app/report.json"


def _load_report():
    assert os.path.exists(REPORT_PATH), f"{REPORT_PATH} does not exist"
    with open(REPORT_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def test_file_exists_and_not_symlink():
    """Verifies that /app/report.json exists and is a regular file (not a symlink)."""
    assert os.path.exists(REPORT_PATH), "report.json does not exist"
    assert not os.path.islink(REPORT_PATH), "report.json must not be a symlink"


def test_report_schema_and_keys():
    """Verifies that report.json contains the 'orders' list and each item has all required keys."""
    data = _load_report()
    assert "orders" in data, "Missing 'orders' key in report.json"
    assert isinstance(data["orders"], list), "'orders' must be a list"
    assert len(data["orders"]) == 4, f"Expected 4 orders, got {len(data['orders'])}"

    required_keys = {"order_id", "allocated_qty", "shortfall_qty", "limiting_component"}
    for idx, order in enumerate(data["orders"]):
        assert isinstance(order, dict), f"Order at index {idx} is not an object"
        missing = required_keys - set(order.keys())
        assert not missing, f"Order at index {idx} missing keys: {missing}"


def test_output_sorting():
    """Verifies that the 'orders' list is sorted by order_id in ascending order."""
    data = _load_report()
    order_ids = [item["order_id"] for item in data["orders"]]
    expected_order = ["O0", "O1", "O2", "O3"]
    assert order_ids == expected_order, f"Expected order_id sorting {expected_order}, got {order_ids}"


def test_order_O0_allocation():
    """Verifies allocation and shortfall metrics for order O0 (P2, requested 5, priority 0)."""
    data = _load_report()
    by_id = {item["order_id"]: item for item in data["orders"]}
    assert "O0" in by_id, "Missing order O0"
    o0 = by_id["O0"]

    assert o0["allocated_qty"] == 5, f"Expected allocated_qty 5 for O0, got {o0['allocated_qty']}"
    assert o0["shortfall_qty"] == 0, f"Expected shortfall_qty 0 for O0, got {o0['shortfall_qty']}"
    assert o0["limiting_component"] is None, f"Expected limiting_component null for O0, got {o0['limiting_component']}"


def test_order_O1_allocation():
    """Verifies allocation, shortfall, and bottleneck component for order O1 (P1, requested 30, priority 1)."""
    data = _load_report()
    by_id = {item["order_id"]: item for item in data["orders"]}
    assert "O1" in by_id, "Missing order O1"
    o1 = by_id["O1"]

    assert o1["allocated_qty"] == 12, f"Expected allocated_qty 12 for O1, got {o1['allocated_qty']}"
    assert o1["shortfall_qty"] == 18, f"Expected shortfall_qty 18 for O1, got {o1['shortfall_qty']}"
    assert o1["limiting_component"] == "L3", f"Expected limiting_component 'L3' for O1, got {o1['limiting_component']}"


def test_order_O2_allocation():
    """Verifies allocation, shortfall, and bottleneck component for order O2 (P2, requested 20, priority 2)."""
    data = _load_report()
    by_id = {item["order_id"]: item for item in data["orders"]}
    assert "O2" in by_id, "Missing order O2"
    o2 = by_id["O2"]

    assert o2["allocated_qty"] == 0, f"Expected allocated_qty 0 for O2, got {o2['allocated_qty']}"
    assert o2["shortfall_qty"] == 20, f"Expected shortfall_qty 20 for O2, got {o2['shortfall_qty']}"
    assert o2["limiting_component"] == "L3", f"Expected limiting_component 'L3' for O2, got {o2['limiting_component']}"


def test_order_O3_allocation():
    """Verifies allocation, shortfall, and bottleneck component for order O3 (P1, requested 15, priority 3)."""
    data = _load_report()
    by_id = {item["order_id"]: item for item in data["orders"]}
    assert "O3" in by_id, "Missing order O3"
    o3 = by_id["O3"]

    assert o3["allocated_qty"] == 0, f"Expected allocated_qty 0 for O3, got {o3['allocated_qty']}"
    assert o3["shortfall_qty"] == 15, f"Expected shortfall_qty 15 for O3, got {o3['shortfall_qty']}"
    assert o3["limiting_component"] == "L3", f"Expected limiting_component 'L3' for O3, got {o3['limiting_component']}"
