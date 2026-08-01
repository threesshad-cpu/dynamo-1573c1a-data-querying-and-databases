import json
import os

REPORT_PATH = "/app/report.json"


def _load_report():
    assert os.path.exists(REPORT_PATH), f"{REPORT_PATH} does not exist"
    with open(REPORT_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def test_file_exists_and_not_symlink():
    """Verifies report.json exists and is a regular file."""
    assert os.path.exists(REPORT_PATH), "report.json missing"
    assert not os.path.islink(REPORT_PATH), "report.json must not be symlink"


def test_report_schema_and_keys():
    """Verifies schema and required keys."""
    data = _load_report()
    assert "orders" in data and isinstance(data["orders"], list)
    assert len(data["orders"]) == 4
    keys = {"order_id", "allocated_qty", "shortfall_qty", "limiting_component"}
    for item in data["orders"]:
        assert isinstance(item, dict)
        assert not (keys - set(item.keys()))


def test_output_sorting():
    """Verifies orders list is sorted by order_id ascending."""
    data = _load_report()
    assert [x["order_id"] for x in data["orders"]] == ["O0", "O1", "O2", "O3"]


def test_order_O0_allocation():
    """Verifies allocation for order O0."""
    data = _load_report()
    by_id = {x["order_id"]: x for x in data["orders"]}
    o = by_id["O0"]
    assert o["allocated_qty"] == 5 and o["shortfall_qty"] == 0 and o["limiting_component"] is None


def test_order_O1_allocation():
    """Verifies allocation for order O1."""
    data = _load_report()
    by_id = {x["order_id"]: x for x in data["orders"]}
    o = by_id["O1"]
    assert o["allocated_qty"] == 12 and o["shortfall_qty"] == 18 and o["limiting_component"] == "L3"


def test_order_O2_allocation():
    """Verifies allocation for order O2."""
    data = _load_report()
    by_id = {x["order_id"]: x for x in data["orders"]}
    o = by_id["O2"]
    assert o["allocated_qty"] == 0 and o["shortfall_qty"] == 20 and o["limiting_component"] == "L3"


def test_order_O3_allocation():
    """Verifies allocation for order O3."""
    data = _load_report()
    by_id = {x["order_id"]: x for x in data["orders"]}
    o = by_id["O3"]
    assert o["allocated_qty"] == 0 and o["shortfall_qty"] == 15 and o["limiting_component"] == "L3"
