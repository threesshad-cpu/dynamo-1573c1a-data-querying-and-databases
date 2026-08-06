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

    Dataset: L3 Steel-Plate=37 on-hand; SA1->L3 scrap_rate=5.5%.
    Order sequence by priority: O0(P2x8), O1(P1x10), O2(P3x15), O3(P2x20), O4(P1x25).

    O0 (P2 x 8): SA1 stock=8 covers all 8 SA1 needed (no explosion), SA3 x 8 consumes
    L3=16 (8*2, no scrap). Fully allocated. limiting_component=None.

    O1 (P1 x 10, batch=5): needs 20 SA1 (SA1 stock=0 post-O0); gross L3 per ceil scrap=
    ceil(20 * 1 * 1.055) = ceil(21.1) = 22 > L3_remaining=21 -> can only build 5 P1
    (10 SA1, ceil(10*1.055)=ceil(10.55)=11 <= 21). limiting=L3 (min ratio).

    O2 (P3 x 15, batch=2): max=14; P3->SA4->SA2 path. 5 SA4 prebuilt consumed, 9 SA4
    exploded; 9 SA2 exploded; L5 ratio 16/11 = 1.45 is binding. limiting=L5.

    O3 (P2 x 20): L3 exhausted after O1; all batch sizes fail. limiting=L3.

    O4 (P1 x 25): L3 still 0; all fail. limiting=L3.

    Scrap sensitivity: replacing math.ceil with math.floor gives O1 allocated_qty=10
    (floor(21.1)=21 <= 21 succeeds) -- a fundamentally wrong answer, caught by this test.
    """
    with open(REPORT_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)
    m = {x["order_id"]: x for x in data["orders"]}

    assert (
        m["O0"]["allocated_qty"] == 8
        and m["O0"]["shortfall_qty"] == 0
        and m["O0"]["limiting_component"] is None
    )
    assert (
        m["O1"]["allocated_qty"] == 5
        and m["O1"]["shortfall_qty"] == 5
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
        and m["O4"]["limiting_component"] == "L3"
    )
