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

    Dataset: L1=250, L3=88 (Steel-Plate), SA1->L3 scrap=5.5%.
    Seven production orders processed in ascending priority order.

    L1 is a diamond dependency via two BOM paths for P1:
      SA1 (x2 per P1): L1 x4 per SA1 = 8 L1 per P1 via SA1
      SA2 (x1 per P1): L1 x2 per SA2 = 2 L1 per P1 via SA2
      Total L1 per P1 = 10 (must sum both paths, not take max).

    O0 (P2 x 12): SA1 stock=8 covers 8 of 12; 4 SA1 exploded.
    L3 = ceil(4*1.055)=5 from SA1 + 24 from 12 SA3 = 29 total.
    L1 from 4 SA1 = 16. L4 = ceil(48*1.025)+24 = 74. Full alloc.

    O1 (P1 x 30, batch=5): SA1 stock=0, SA2 stock=4.
    25 P1: 50 SA1 (L3=ceil(52.75)=53<=59, L1=200); 21 SA2 explode
    (25-4=21; L1=42, L5=21>25-0=25? 21<=25 OK). L1 total=242>234 FAIL.
    20 P1: 40 SA1 (L3=ceil(42.2)=43<=59); 16 SA2 explode (L1=32).
    L1=160+32=192<=234. Pass. allocated=20, sf=10.
    Bottleneck for next 25 P1: L1 ratio=234/242=0.967 < L3 ratio=59/53=1.11.
    limiting=L1.

    O2 (P3 x 15, batch=2): SA4 stock=5 (use 5, explode 9).
    SA2 stock=0 post-O1; explode 9 SA2. L5=9 consumed; L1=18 from SA2.
    14 P3 fully allocable. sf=1. Next batch (16 P3): L5 ratio=16/11=1.45
    < other ratios. limiting=L5.

    O3 (P2 x 20, batch=4): SA1 stock=0; 4 P2 explodes 4 SA1.
    L3 from SA1=ceil(4.22)=5; L3 from 4 SA3=8. Total L3=13 <= 16.
    L1 from 4 SA1=16 <= 24. 4 P2 fits. 8 P2: L3=ceil(8.44)+16=26 > 16 FAIL.
    allocated=4, sf=16. Next batch (8 P2): L3 ratio=16/26=0.615 < L1 ratio.
    limiting=L3.

    O4 (P1 x 25, batch=5): L5=9-9=0 (used by O2). SA1=0.
    5 P1: 10 SA1 (L3=ceil(10.55)=11 > 3 = L3 remaining after O3). FAIL.
    allocated=0, sf=25. Next 5 P1: L3=11>3, L5=5>0.
    L5 ratio=0/5=0 (minimum). limiting=L5.

    O5 (P3 x 25, batch=2): SA4 stock=0 (used by O2). L5=0.
    2 P3: SA4=2 explode (SA2=2 explode; L5=2>0). FAIL.
    allocated=0, sf=25. Next 2 P3: L5=2>0. L5 ratio=0/2=0. limiting=L5.

    O6 (P2 x 20, batch=4): SA1 stock=0. L3=3 remaining.
    4 P2: 4 SA1 explode (L3=5>3). FAIL. allocated=0, sf=20.
    Next 4 P2: L3=13>3. L3 ratio=3/13=0.231 < L1 ratio=8/16=0.5.
    limiting=L3.

    Scrap sensitivity: ceil->floor changes O3 and O6 limiting_component.
    floor path: O0 uses ceil(4*1.055)=5->4 L3, leaving L3=59 after O0.
    O1 still allocates 20 (43<=59 ceil; 42<=59 floor -- same). But after O1,
    L3 remaining under floor=59-42=17 (vs ceil 59-43=16).
    O3 for 4 P2: ceil L3=5+8=13<=16, floor L3=4+8=12<=17. Both fit alloc=4.
    For 8 P2: ceil L3=9+16=25>16 (limiting=L3). floor L3=8+16=24>17 (L3 ratio=17/24=0.708).
    Under floor, L1 ratio=8/16=0.5 < L3 ratio=0.708, so limiting=L1.
    Similarly O6: floor leaves more L3, but L1 becomes limiting first.
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
        and m["O1"]["limiting_component"] == "L1"
    )
    assert (
        m["O2"]["allocated_qty"] == 14
        and m["O2"]["shortfall_qty"] == 1
        and m["O2"]["limiting_component"] == "L5"
    )
    assert (
        m["O3"]["allocated_qty"] == 4
        and m["O3"]["shortfall_qty"] == 16
        and m["O3"]["limiting_component"] == "L3"
    )
    assert (
        m["O4"]["allocated_qty"] == 0
        and m["O4"]["shortfall_qty"] == 25
        and m["O4"]["limiting_component"] == "L5"
    )
    assert (
        m["O5"]["allocated_qty"] == 0
        and m["O5"]["shortfall_qty"] == 25
        and m["O5"]["limiting_component"] == "L5"
    )
    assert (
        m["O6"]["allocated_qty"] == 0
        and m["O6"]["shortfall_qty"] == 20
        and m["O6"]["limiting_component"] == "L3"
    )
