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
    assert set(data.keys()) == {"orders"}, "Top-level object must have exactly one key: 'orders'"
    orders = data.get("orders", [])
    assert len(orders) == 7
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
    expected_ids = ["O0", "O1", "O2", "O3", "O4", "O5", "O6"]
    assert [x["order_id"] for x in data["orders"]] == expected_ids


def test_order_allocations():
    """Verify sequential shared-inventory allocation results.

    Dataset: L1=320, L3=95, L5=31, L6=58; SA1(stock=4, bs=5), SA2(stock=2, bs=4), SA4(stock=2, bs=5).
    Seven production orders processed in ascending priority order.

    Sub-assembly lot sizing constraint:
    When exploding net sub-assembly demand N > 0, build_qty = ceil(N / batch_size) * batch_size.
    Excess produced sub-assemblies (build_qty - N) are credited to on-hand inventory.

    O0 (P2 x 12): SA1 stock=4 covers 4 of 12; 8 SA1 exploded. SA1 batch_size=5 -> build 10 SA1.
    2 SA1 excess credited to inventory (SA1 stock becomes 2). L3=ceil(10*1.055)=11 from SA1 + 24 from 12 SA3 = 35 total.
    L1 from 10 SA1 = 40. Fully allocated (alloc=12, sf=0, limiting=None).

    O1 (P1 x 30, batch=5): SA1 stock=2, SA2 stock=2.
    Allocates 25 P1 (needs 50 SA1, 25 SA2).
    50 SA1 -> 2 stock used, 48 exploded. SA1 bs=5 -> build 50 SA1. 2 SA1 excess credited.
    25 SA2 -> 2 stock used, 23 exploded. SA2 bs=4 -> build 24 SA2. 1 SA2 excess credited.
    L3=ceil(50*1.055)=53 (<= 60 remaining). L5=24 (<= 31 remaining). L6=ceil(24*2.1)=51 (<= 58 remaining).
    Allocates 25 P1 (alloc=25, sf=5, limiting=L3).

    O2 (P3 x 15, batch=2): SA4 stock=2, bs=5. L5 remaining = 7. L6 remaining = 7.
    Allocates 2 P3 (needs 2 SA4 -> 2 stock used, 0 exploded).
    Tries 4 P3 (needs 4 SA4 -> 2 stock used, 2 exploded). SA4 bs=5 -> build 5 SA4.
    5 SA4 needs 5 SA2 -> 2 SA2 used (1 excess from O1 + 1 stock), 3 exploded. SA2 bs=4 -> build 4 SA2.
    4 SA2 needs 4 L5, 4*2.1=9 L6 > 7 L6 remaining -> FAILS due to L6 restriction.
    Allocates 2 P3 (alloc=2, sf=13, limiting=L6).

    O3 (P2 x 20): alloc=0, sf=20, limiting=L3.
    O4 (P1 x 25): alloc=0, sf=25, limiting=L3.
    O5 (P3 x 25): alloc=0, sf=25, limiting=L6.
    O6 (P2 x 20): alloc=0, sf=20, limiting=L3.

    Sensitivity:
    - Ignoring sub-assembly batch_size changes O2 allocated_qty from 2 to 6.
    - Ignoring leftover sub-assembly stock changes O4 limiting_component from L3 to L6.
    - Using floor instead of ceil for scrap changes O1 limiting_component from L3 to L1.
    """
    with open(REPORT_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)
    m = {x["order_id"]: x for x in data["orders"]}

    assert (
        m["O0"]["allocated_qty"] == 12
        and m["O0"]["shortfall_qty"] == 0
        and m["O0"]["limiting_component"] is None
    )
    assert (
        m["O1"]["allocated_qty"] == 25
        and m["O1"]["shortfall_qty"] == 5
        and m["O1"]["limiting_component"] == "L3"
    )
    assert (
        m["O2"]["allocated_qty"] == 2
        and m["O2"]["shortfall_qty"] == 13
        and m["O2"]["limiting_component"] == "L6"
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
    assert (
        m["O5"]["allocated_qty"] == 0
        and m["O5"]["shortfall_qty"] == 25
        and m["O5"]["limiting_component"] == "L6"
    )
    assert (
        m["O6"]["allocated_qty"] == 0
        and m["O6"]["shortfall_qty"] == 20
        and m["O6"]["limiting_component"] == "L3"
    )
