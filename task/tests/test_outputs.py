import json
import os
from pathlib import Path
from tests.reference_model import run_all_orders

REPORT_PATH = os.environ.get("TEST_REPORT_PATH", "/app/report.json")
DB_PATH = Path("/app/manufacturing.db")
if not DB_PATH.exists():
    DB_PATH = Path(__file__).resolve().parent.parent / "data" / "manufacturing.db"

def test_file_exists_and_not_symlink():
    """Verify output format output artifact exists as a regular file."""
    assert os.path.exists(REPORT_PATH) and not os.path.islink(REPORT_PATH)

def test_report_schema_and_keys():
    """Verify the normative report schema, types, and 43-order cardinality."""
    with open(REPORT_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)
    assert set(data.keys()) == {"orders"}
    orders = data.get("orders", [])
    assert len(orders) == 43, "Expected 43 order results in report"
    expected_keys = {"order_id", "allocated_qty", "shortfall_qty", "limiting_resource"}
    for x in orders:
        assert isinstance(x, dict) and set(x.keys()) == expected_keys
        assert isinstance(x["order_id"], str)
        assert isinstance(x["allocated_qty"], int) and not isinstance(x["allocated_qty"], bool)
        assert isinstance(x["shortfall_qty"], int) and not isinstance(x["shortfall_qty"], bool)
        assert x["limiting_resource"] is None or isinstance(x["limiting_resource"], str)

def test_output_sorting():
    """Verify output format requires results sorted ascending by order_id."""
    with open(REPORT_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)
    actual_ids = [x["order_id"] for x in data["orders"]]
    expected_ids = sorted(actual_ids)
    assert actual_ids == expected_ids

def test_against_reference_model():
    """Independently compute the expected result from the database using a strict reference model."""
    with open(REPORT_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)
    
    candidate_orders = {x["order_id"]: x for x in data["orders"]}
    reference_orders = run_all_orders(DB_PATH)
    
    assert len(candidate_orders) == len(reference_orders), "Order count mismatch between candidate and reference"
    
    for order_id, ref_res in reference_orders.items():
        assert order_id in candidate_orders, f"Missing order {order_id} in candidate output"
        cand_res = candidate_orders[order_id]
        
        # Verify semantics exactly
        assert cand_res["allocated_qty"] == ref_res["allocated_qty"], f"Mismatch in allocated_qty for order {order_id}: expected {ref_res['allocated_qty']}, got {cand_res['allocated_qty']}"
        assert cand_res["shortfall_qty"] == ref_res["shortfall_qty"], f"Mismatch in shortfall_qty for order {order_id}: expected {ref_res['shortfall_qty']}, got {cand_res['shortfall_qty']}"
        assert cand_res["limiting_resource"] == ref_res["limiting_resource"], f"Mismatch in limiting_resource for order {order_id}: expected {ref_res['limiting_resource']}, got {cand_res['limiting_resource']}"
