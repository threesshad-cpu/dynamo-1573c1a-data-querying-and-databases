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
    """Verify sequential shared-inventory allocation results.

    Dataset: L3 Steel-Plate=81 on-hand; SA1->L3 scrap_rate=5.5%.
    Order sequence by priority: O0(P2x12), O1(P1x30), O2(P3x15), O3(P2x20), O4(P1x25).

    O0 (P2 x 12): SA1 stock=8 covers 8 of 12 SA1 needed; 4 SA1 exploded.
    L3 from SA1: ceil(4*1*1.055)=ceil(4.22)=5. L3 from 12 SA3: 24. Total=29.
    L3 remaining after O0: 81-29=52. O0 fully allocated.

    O1 (P1 x 30, batch=5): needs 60 SA1 (SA1 stock=0). Tries 30 first:
    L3=ceil(60*1.055)=ceil(63.3)=64 > 52 -> fail. Tries 25:
    L3=ceil(50*1.055)=ceil(52.75)=53 > 52 -> fail. Tries 20:
    L3=ceil(40*1.055)=ceil(42.2)=43 <= 52 -> success. allocated=20, shortfall=10.
    For next batch=25: L3=ceil(52.75)=53, available=9 (81-29-43). L3 ratio=9/53=0.17.
    L5 ratio=9/25=0.36. L3 has smallest ratio -> limiting=L3.

    O2 (P3 x 15, batch=2): max=14. P3->SA4->SA2 path. 5 SA4 prebuilt consumed,
    9 SA4 exploded; 9 SA2 exploded (SA2 stock=0 post-O1); L5=9 consumed, available=9 exactly.
    allocated=14, shortfall=1. For next batch=16: L5 available=0, needed=11 -> ratio=0.
    limiting=L5.

    O3 (P2 x 20): L3 remaining=9 (81-29-43). All batch sizes need more L3.
    4 P2: ceil(4*1.055)=5 SA1-L3 + 8 SA3-L3 = 13 > 9 -> fail. allocated=0, shortfall=20.
    limiting=L3 (ratio 9/13=0.69, minimum among binding components).

    O4 (P1 x 25): L5=0 (all consumed by O2). 5 P1 needs 1 SA2 (exploded): L5=1 > 0 -> fail.
    allocated=0, shortfall=25. limiting=L5 (ratio 0/1=0, minimum).

    Scrap sensitivity: replacing math.ceil with math.floor changes 3 output fields:
    O1 gets allocated=25 (floor(52.75)=52 <= 53 L3 available via floor path),
    O2 gets allocated=8 (L5 depleted sooner), O4 limiting changes L5->L3.
    All three differences are caught by this test.
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
        m["O1"]["allocated_qty"] == 20
        and m["O1"]["shortfall_qty"] == 10
        and m["O1"]["limiting_component"] == "L3"
    )
    assert (
        m["O2"]["allocated_qty"] == 14
        and m["O2"]["shortfall_qty"] == 1
        and m["O2"]["limiting_component"] == "L5"
    )
    assert (
        m["O3"]["allocated_qty"] == 0
        and m["O3"]["shortfall_qty"] == 20
        and m["O3"]["limiting_component"] == "L3"
    )
    assert (
        m["O4"]["allocated_qty"] == 0
        and m["O4"]["shortfall_qty"] == 25
        and m["O4"]["limiting_component"] == "L5"
    )
