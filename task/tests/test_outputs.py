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
    assert len(orders) == 28, "Expected 28 order results in report"
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
    expected_ids = ["O00_A", "O00_B", "O00_C", "O00_D", "O00_E", "O00_F", "O00_G", "O00_H", "O00_I", "O00_J", "O00_K", "O00_L", "O00_M", "O00_N", "O00_O", "O00_P", "O00_R1", "O00_R2", "O00_S2", "O00_W", "O00_X", "O00_Y", "O01", "O02", "O03", "O04", "O05", "O06"]
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
    """Verify O02 allocation (P1 x 30, batch=5): Processed AFTER O03 due to priority ordering."""
    m = _get_orders_map()
    assert m["O02"]["allocated_qty"] == 25
    assert m["O02"]["shortfall_qty"] == 5
    assert m["O02"]["limiting_resource"] == "WC2"


def test_order_O03_allocation():
    """Verify O03 allocation (P3 x 15, batch=2): Processed BEFORE O02 due to priority ordering. alloc=14, sf=1, limiting=None."""
    m = _get_orders_map()
    assert m["O03"]["allocated_qty"] == 14
    assert m["O03"]["shortfall_qty"] == 1
    assert m["O03"]["limiting_resource"] is None


def test_order_O04_allocation():
    """Verify O04 allocation (P2 x 20, batch=4): SA1 requires SA2 which needs L5 — fully depleted by O01+O03. alloc=4, sf=16, limiting=WC2."""
    m = _get_orders_map()
    assert m["O04"]["allocated_qty"] == 4
    assert m["O04"]["shortfall_qty"] == 16
    assert m["O04"]["limiting_resource"] == "WC2"


def test_order_O05_allocation():
    """Verify O05 allocation (P4 x 5, batch=3): Dual-workcenter routing on WC1+WC3 after prior WC consumption. alloc=0, sf=5, limiting=WC3."""
    m = _get_orders_map()
    assert m["O05"]["allocated_qty"] == 0
    assert m["O05"]["shortfall_qty"] == 5
    assert m["O05"]["limiting_resource"] == "WC3"


def test_order_O06_allocation():
    """Verify O06 allocation (P3 x 8, batch=2): Uses excess SA4 from O03 lot rounding."""
    m = _get_orders_map()
    assert m["O06"]["allocated_qty"] == 2
    assert m["O06"]["shortfall_qty"] == 6
    assert m["O06"]["limiting_resource"] == "WC2"

def test_order_O00_A_allocation():
    """Verifies that O00_A fails allocation due to L10 shortage with the correct limiting resource."""
    m = _get_orders_map()
    assert m["O00_A"]["allocated_qty"] == 0
    assert m["O00_A"]["shortfall_qty"] == 3
    assert m["O00_A"]["limiting_resource"] == "L10"


def test_order_O00_B_allocation():
    """Verifies that O00_B is successfully allocated fully."""
    m = _get_orders_map()
    assert m["O00_B"]["allocated_qty"] == 10
    assert m["O00_B"]["shortfall_qty"] == 0
    assert m["O00_B"]["limiting_resource"] is None


def test_order_O00_C_allocation():
    """Verifies that O00_C is successfully allocated fully (or fails if agent missed the tie-breaker)."""
    m = _get_orders_map()
    assert m["O00_C"]["allocated_qty"] == 3
    assert m["O00_C"]["shortfall_qty"] == 0
    assert m["O00_C"]["limiting_resource"] is None


def test_order_O00_D_allocation():
    """Verifies that O00_D is successfully allocated fully."""
    m = _get_orders_map()
    assert m["O00_D"]["allocated_qty"] == 1
    assert m["O00_D"]["shortfall_qty"] == 0
    assert m["O00_D"]["limiting_resource"] is None


def test_order_O00_E_allocation():
    """Verifies that O00_E is successfully allocated fully."""
    m = _get_orders_map()
    assert m["O00_E"]["allocated_qty"] == 9
    assert m["O00_E"]["shortfall_qty"] == 0
    assert m["O00_E"]["limiting_resource"] is None


def test_order_O00_F_allocation():
    """Verifies that O00_F fails allocation due to scrap rate requirement on L13."""
    m = _get_orders_map()
    assert m["O00_F"]["allocated_qty"] == 0
    assert m["O00_F"]["shortfall_qty"] == 1
    assert m["O00_F"]["limiting_resource"] == "L13"


def test_order_O00_G_allocation():
    """Verifies that O00_G fails allocation due to setup and run hours on WC5."""
    m = _get_orders_map()
    assert m["O00_G"]["allocated_qty"] == 0
    assert m["O00_G"]["shortfall_qty"] == 1
    assert m["O00_G"]["limiting_resource"] == "WC5"

def test_order_O00_H_allocation():
    """Verifies that O00_H fails with correct limiting resource, distinguishing INITIAL vs LEFTOVER calculation."""
    m = _get_orders_map()
    assert m["O00_H"]["allocated_qty"] == 1
    assert m["O00_H"]["shortfall_qty"] == 1
    assert m["O00_H"]["limiting_resource"] == "L15"


def test_order_O00_I_allocation():
    """Verifies O00_I allocates correctly with substitute integer conversion constraints."""
    m = _get_orders_map()
    assert m["O00_I"]["allocated_qty"] == 2
    assert m["O00_I"]["shortfall_qty"] == 1
    assert m["O00_I"]["limiting_resource"] == "L16"


def test_order_O00_J_allocation():
    """Verifies O00_J consumes leftover substitute correctly if O00_I did not over-consume."""
    m = _get_orders_map()
    assert m["O00_J"]["allocated_qty"] == 1
    assert m["O00_J"]["shortfall_qty"] == 0
    assert m["O00_J"]["limiting_resource"] is None

def test_order_O00_K_allocation():
    """Verifies O00_K correctly ignores Sub-Assemblies when finding limiting resources."""
    m = _get_orders_map()
    assert m["O00_K"]["allocated_qty"] == 2
    assert m["O00_K"]["shortfall_qty"] == 1
    assert m["O00_K"]["limiting_resource"] == "WC10"


def test_order_O00_L_allocation():
    """Verifies O00_L applies batch size rounding to child sub-assembly run hours."""
    m = _get_orders_map()
    assert m["O00_L"]["allocated_qty"] == 0
    assert m["O00_L"]["shortfall_qty"] == 1
    assert m["O00_L"]["limiting_resource"] == "WC11"


def test_order_O00_M_allocation():
    """Verifies O00_M applies math.ceil() on the scrap percentage calculation."""
    m = _get_orders_map()
    assert m["O00_M"]["allocated_qty"] == 0
    assert m["O00_M"]["shortfall_qty"] == 1
    assert m["O00_M"]["limiting_resource"] == "L21"

def test_order_O00_O_allocation():
    """Verifies O00_O builds inventory for O00_P netting."""
    m = _get_orders_map()
    assert m["O00_O"]["allocated_qty"] == 3
    assert m["O00_O"]["shortfall_qty"] == 0
    assert m["O00_O"]["limiting_resource"] is None

def test_order_O00_P_allocation():
    """Verifies O00_P properly nets out available sub-assemblies before computing limiting_resource."""
    m = _get_orders_map()
    assert m["O00_P"]["allocated_qty"] == 0
    assert m["O00_P"]["shortfall_qty"] == 1
    assert m["O00_P"]["limiting_resource"] == "WC30"

def test_order_O00_R1_R2_allocation():
    """Verifies correct integer consumption of substitute stock leaving exact leftovers."""
    m = _get_orders_map()
    assert m["O00_R1"]["allocated_qty"] == 1
    assert m["O00_R1"]["shortfall_qty"] == 0
    assert m["O00_R1"]["limiting_resource"] is None
    assert m["O00_R2"]["allocated_qty"] == 1
    assert m["O00_R2"]["shortfall_qty"] == 0
    assert m["O00_R2"]["limiting_resource"] is None

def test_order_O00_S2_allocation():
    """Verifies Level-Order (BFS) aggregation of demand before calculating routing batch setup hours."""
    m = _get_orders_map()
    assert m["O00_S2"]["allocated_qty"] == 1
    assert m["O00_S2"]["shortfall_qty"] == 0
    assert m["O00_S2"]["limiting_resource"] is None



def test_order_O00_N_allocation():
    """Verifies O00_N handles multi-level subassembly netting correctly."""
    m = _get_orders_map()
    assert m["O00_N"]["allocated_qty"] == 4
    assert m["O00_N"]["shortfall_qty"] == 1
    assert m["O00_N"]["limiting_resource"] == "L104"

def test_order_O00_W_allocation():
    """Verifies O00_W successfully consumes shared resource stock without limiting."""
    m = _get_orders_map()
    assert m["O00_W"]["allocated_qty"] == 2
    assert m["O00_W"]["shortfall_qty"] == 0
    assert m["O00_W"]["limiting_resource"] is None

def test_order_O00_X_allocation():
    """Verifies O00_X applies global ASCII tie-breaker on shared resources correctly after O00_W."""
    m = _get_orders_map()
    assert m["O00_X"]["allocated_qty"] == 1
    assert m["O00_X"]["shortfall_qty"] == 1
    assert m["O00_X"]["limiting_resource"] == "L105"

def test_order_O00_Y_allocation():
    """Verifies O00_Y correctly aggregates setup hours exactly once after batch rounding."""
    m = _get_orders_map()
    assert m["O00_Y"]["allocated_qty"] == 0
    assert m["O00_Y"]["shortfall_qty"] == 1
    assert m["O00_Y"]["limiting_resource"] == "WC105"
