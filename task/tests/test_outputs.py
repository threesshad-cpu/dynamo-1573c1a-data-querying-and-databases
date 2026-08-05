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
    orders = data.get("orders", [])
    assert len(orders) == 5
    expected_keys = {
        "order_id",
        "allocated_qty",
        "shortfall_qty",
        "limiting_component",
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
        assert x["limiting_component"] is None or isinstance(
            x["limiting_component"], str
        )


def test_output_sorting():
    """Verify that orders in /app/report.json are sorted by order_id."""
    with open(REPORT_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)
    expected_ids = ["O0", "O1", "O2", "O3", "O4"]
    assert [x["order_id"] for x in data["orders"]] == expected_ids


def test_order_allocations():
    """Verify sequential shared-inventory allocation results."""
    with open(REPORT_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)
    m = {x["order_id"]: x for x in data["orders"]}

    assert (
        m["O0"]["allocated_qty"] == 12
        and m["O0"]["shortfall_qty"] == 0
        and m["O0"]["limiting_component"] is None
    )
    assert (
        m["O1"]["allocated_qty"] == 0
        and m["O1"]["shortfall_qty"] == 30
        and m["O1"]["limiting_component"] == "L3"
    )
    assert (
        m["O2"]["allocated_qty"] == 14
        and m["O2"]["shortfall_qty"] == 1
        and m["O2"]["limiting_component"] == "L8"
    )
    assert (
        m["O3"]["allocated_qty"] == 0
        and m["O3"]["shortfall_qty"] == 20
        and m["O3"]["limiting_component"] == "L3"
    )
    assert (
        m["O4"]["allocated_qty"] == 0
        and m["O4"]["shortfall_qty"] == 25
        and m["O4"]["limiting_component"] == "L3"
    )
