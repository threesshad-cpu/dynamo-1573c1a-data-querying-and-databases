import json
import os
from pathlib import Path

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
    assert len(orders) == 47, "Expected 47 order results in report"
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
    """Verify the output exactly matches the precomputed static ground truth."""
    with open(REPORT_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)
    
    candidate_orders = {x["order_id"]: x for x in data["orders"]}
    
    reference_orders = {
        "O1": {"order_id": "O1", "allocated_qty": 12, "shortfall_qty": 0, "limiting_resource": None},
        "O10C": {"order_id": "O10C", "allocated_qty": 5, "shortfall_qty": 5, "limiting_resource": "WC5"},
        "O11": {"order_id": "O11", "allocated_qty": 90, "shortfall_qty": 10, "limiting_resource": "L9"},
        "O12": {"order_id": "O12", "allocated_qty": 6, "shortfall_qty": 4, "limiting_resource": "L_SCRAP"},
        "O15": {"order_id": "O15", "allocated_qty": 5, "shortfall_qty": 5, "limiting_resource": "L15"},
        "O15b": {"order_id": "O15b", "allocated_qty": 0, "shortfall_qty": 100, "limiting_resource": "L15b"},
        "O16": {"order_id": "O16", "allocated_qty": 5, "shortfall_qty": 5, "limiting_resource": "WC10"},
        "O17": {"order_id": "O17", "allocated_qty": 9, "shortfall_qty": 1, "limiting_resource": "L17"},
        "O18": {"order_id": "O18", "allocated_qty": 7, "shortfall_qty": 3, "limiting_resource": "L18A"},
        "O2": {"order_id": "O2", "allocated_qty": 10, "shortfall_qty": 0, "limiting_resource": None},
        "O23": {"order_id": "O23", "allocated_qty": 1, "shortfall_qty": 0, "limiting_resource": None},
        "O24": {"order_id": "O24", "allocated_qty": 2, "shortfall_qty": 1, "limiting_resource": None},
        "O25": {"order_id": "O25", "allocated_qty": 1, "shortfall_qty": 1, "limiting_resource": None},
        "O26": {"order_id": "O26", "allocated_qty": 1, "shortfall_qty": 1, "limiting_resource": None},
        "O27": {"order_id": "O27", "allocated_qty": 0, "shortfall_qty": 5, "limiting_resource": "L27B"},
        "O28": {"order_id": "O28", "allocated_qty": 1, "shortfall_qty": 1, "limiting_resource": "L28B"},
        "O29": {"order_id": "O29", "allocated_qty": 0, "shortfall_qty": 2, "limiting_resource": "L23A"},
        "O3": {"order_id": "O3", "allocated_qty": 6, "shortfall_qty": 4, "limiting_resource": "L3"},
        "O30": {"order_id": "O30", "allocated_qty": 0, "shortfall_qty": 4, "limiting_resource": "L24A"},
        "O31": {"order_id": "O31", "allocated_qty": 0, "shortfall_qty": 3, "limiting_resource": "L25A"},
        "O32": {"order_id": "O32", "allocated_qty": 0, "shortfall_qty": 3, "limiting_resource": "L26A"},
        "O33": {"order_id": "O33", "allocated_qty": 0, "shortfall_qty": 5, "limiting_resource": "L27B"},
        "O34": {"order_id": "O34", "allocated_qty": 0, "shortfall_qty": 3, "limiting_resource": "L28A"},
        "O35": {"order_id": "O35", "allocated_qty": 3, "shortfall_qty": 0, "limiting_resource": None},
        "O36": {"order_id": "O36", "allocated_qty": 0, "shortfall_qty": 2, "limiting_resource": "L35A"},
        "O37": {"order_id": "O37", "allocated_qty": 2, "shortfall_qty": 0, "limiting_resource": None},
        "O38": {"order_id": "O38", "allocated_qty": 0, "shortfall_qty": 2, "limiting_resource": "L36A"},
        "O39": {"order_id": "O39", "allocated_qty": 2, "shortfall_qty": 2, "limiting_resource": "WC37"},
        "O3_N1": {"order_id": "O3_N1", "allocated_qty": 5, "shortfall_qty": 0, "limiting_resource": None},
        "O3_N2": {"order_id": "O3_N2", "allocated_qty": 5, "shortfall_qty": 0, "limiting_resource": None},
        "O3b": {"order_id": "O3b", "allocated_qty": 0, "shortfall_qty": 10, "limiting_resource": "SUB_L3_B"},
        "O4": {"order_id": "O4", "allocated_qty": 3, "shortfall_qty": 3, "limiting_resource": "L_TIE"},
        "O40": {"order_id": "O40", "allocated_qty": 0, "shortfall_qty": 4, "limiting_resource": "WC37"},
        "O41": {"order_id": "O41", "allocated_qty": 1, "shortfall_qty": 1, "limiting_resource": "L38"},
        "O42": {"order_id": "O42", "allocated_qty": 0, "shortfall_qty": 1, "limiting_resource": "L38"},
        "O43": {"order_id": "O43", "allocated_qty": 0, "shortfall_qty": 1, "limiting_resource": "P43"},
        "O44": {"order_id": "O44", "allocated_qty": 0, "shortfall_qty": 2, "limiting_resource": "P43"},
        "O45": {"order_id": "O45", "allocated_qty": 1, "shortfall_qty": 0, "limiting_resource": None},
        "O46": {"order_id": "O46", "allocated_qty": 1, "shortfall_qty": 0, "limiting_resource": None},
        "O5": {"order_id": "O5", "allocated_qty": 10, "shortfall_qty": 5, "limiting_resource": "L4"},
        "O6C": {"order_id": "O6C", "allocated_qty": 0, "shortfall_qty": 5, "limiting_resource": "L_CANCEL"},
        "O7": {"order_id": "O7", "allocated_qty": 2, "shortfall_qty": 0, "limiting_resource": None},
        "O8": {"order_id": "O8", "allocated_qty": 4, "shortfall_qty": 0, "limiting_resource": None},
        "O9": {"order_id": "O9", "allocated_qty": 0, "shortfall_qty": 6, "limiting_resource": "L5"},
        "OA": {"order_id": "OA", "allocated_qty": 4, "shortfall_qty": 4, "limiting_resource": "L5"},
        "OB": {"order_id": "OB", "allocated_qty": 0, "shortfall_qty": 5, "limiting_resource": "L7"},
        "OC": {"order_id": "OC", "allocated_qty": 2, "shortfall_qty": 0, "limiting_resource": None}
    }
    
    assert len(candidate_orders) == len(reference_orders), "Order count mismatch between candidate and reference"
    
    for order_id, ref_res in reference_orders.items():
        assert order_id in candidate_orders, f"Missing order {order_id} in candidate output"
        cand_res = candidate_orders[order_id]
        
        # Verify semantics exactly
        assert cand_res["allocated_qty"] == ref_res["allocated_qty"], f"Mismatch in allocated_qty for order {order_id}: expected {ref_res['allocated_qty']}, got {cand_res['allocated_qty']}"
        assert cand_res["shortfall_qty"] == ref_res["shortfall_qty"], f"Mismatch in shortfall_qty for order {order_id}: expected {ref_res['shortfall_qty']}, got {cand_res['shortfall_qty']}"
        assert cand_res["limiting_resource"] == ref_res["limiting_resource"], f"Mismatch in limiting_resource for order {order_id}: expected {ref_res['limiting_resource']}, got {cand_res['limiting_resource']}"
