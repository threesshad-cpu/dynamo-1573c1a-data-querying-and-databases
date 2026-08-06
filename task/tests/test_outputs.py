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

    Dataset: L1=250, L3=90 (Steel-Plate), SA1->L3 scrap=5.5%.
    L1 (Bolt-M4) is a DIAMOND dependency: consumed via SA1 (4 per unit)
    AND via SA2 (2 per unit). P1 requires BOTH SA1 and SA2, so total L1
    per P1 = 2*4 + 1*2 = 10. Incorrect summation (e.g. taking max path)
    yields the wrong limiting_component.

    Order sequence by priority: O0(P2x12), O1(P1x30), O2(P3x15), O3(P2x20), O4(P1x25).

    O0 (P2 x 12): SA1 stock=8 covers 8 of 12 needed; 4 SA1 exploded.
    L3 from SA1: ceil(4*1.055)=ceil(4.22)=5. L3 from 12 SA3: 24. Total L3=29.
    L1 from 4 SA1: 4*4=16. Fully allocated; sf=0, limiting=None.
    Inventory after O0: L1=234, L3=61, SA1=0, SA2=4 (unchanged).

    O1 (P1 x 30, batch=5): SA1 stock=0, SA2 stock=4.
    Tries 30: 60 SA1. L3=ceil(63.3)=64 > 61 -> fail.
    Tries 25: 50 SA1. L3=ceil(52.75)=53 <= 61. L1=50*4=200, plus 21 SA2
    exploded (25-4=21). L1 from 21 SA2=42. Total L1=242 > 234 -> fail.
    Tries 20: 40 SA1. L3=ceil(42.2)=43 <= 61. L1=40*4=160, plus 16 SA2
    exploded (20-4=16). L1 from 16 SA2=32. Total L1=192 <= 234. Pass.
    allocated=20, shortfall=10.
    For next batch (25 P1): L1 ratio=234/242=0.967 vs L3 ratio=61/53=1.15.
    L1 ratio < L3 ratio -> limiting=L1.

    O2 (P3 x 15, batch=2): max=14. SA4 stock=5 (use 5, explode 9).
    SA2=4 used, then 5 more from 9 SA4 -> wait SA2 stock is 4 left (O1 used
    them all; after O1=20 P1 with 4 SA2 used and 16 exploded: SA2=0).
    So 9 SA4 exploded, 9 SA2 exploded from stock=0. L5=9, L1 from 9 SA2=18.
    All checks pass for 14 P3. sf=1. For next=16 P3: L5 consumed=9, available=16.
    L5 ratio=16/11=1.45. L1 from 11 SA2=22, available=42. L1 ratio=42/22=1.91.
    L5 < L1 -> limiting=L5.

    O3 (P2 x 20, batch=4): SA1 stock=0, SA3 stock=0.
    4 P2: 4 SA1 explode (L3=5, L1=16), 4 SA3 (L3=8). Total L3=13. L3=61-43=18.
    13 <= 18 pass. L1=16 <= 42. Also L4=ceil(4*4*1.025)+4*2=17+8=25, L4=76. Pass.
    allocated=4, shortfall=16.
    For next=8 P2: 8 SA1 (L3=ceil(8.44)=9, L1=32), 8 SA3 (L3=16, L4=ceil(32.8)=33,
    L2=48). Total L3=25 > 18 -> L3 ratio=18/25=0.72. Total L1=32, available=26.
    L1 ratio=26/32=0.813. L3 ratio(0.72) < L1 ratio(0.813) -> limiting=L3.

    O4 (P1 x 25, batch=5): L5 stock=25-9=16. L3=18-13=5 (after O3=4 P2).
    5 P1: 10 SA1 (L3=ceil(10.55)=11 > 5) -> fail. 0 P1.
    sf=25. For next=5 P1: L3=11 > 5. L3 ratio=5/11=0.455.
    L5 from 1 SA2 (5-4=1 exploded, SA2=0): L5=1, available=16. L5 ratio=16/1=16.
    L1=10*4+1*2=42, available=26-32=? wait let me recount.
    After O3=4 P2: L1=42-16=26. For 5 P1: L1=10*4+1*2=42, available=26. L1 ratio=26/42=0.619.
    L3 ratio=0.455 < L1 ratio=0.619 < L5 ratio=16 -> limiting=L3.

    Scrap sensitivity: ceil->floor changes O3 limiting_component from L3 to L1.
    The floor path: O0 uses L3=28 (floor(4.22)=4), leaving L3=62 after O0.
    O1=20 still (L3=43<=62, L1=192<=234). O3: for 8 P2, L3=25<=19... wait
    floor(42.2)=42, L3=62-42=20, for 8 P2 L3=25>20 still? Yes, floor path:
    after O1: L3=62-42=20. O3 for 8 P2: 8 SA1 floor(8.44)=8 L3, 8 SA3 L3=16. Total=24>20. fail.
    For 4 P2: 4 SA1 floor(4.22)=4 L3, 4 SA3 L3=8. Total=12<=20. pass.
    allocated=4, sf=16. For 8 P2: L3=12/24 ratio... actually floor changes which
    component is the bottleneck -- L1 becomes limiting instead of L3 for O3.
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
