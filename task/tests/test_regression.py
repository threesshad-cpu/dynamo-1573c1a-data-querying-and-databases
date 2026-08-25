import pytest
import sqlite3
from pathlib import Path
from tests.reference_model import process_order, simulate_production_run

class MockDB:
    def __init__(self):
        self.parts = {}
        self.bom = {}
        self.workcenters = {}
        self.routing = {}
        self.substitutes = {}
        self.orders = []
        self.leaf_parts = set()

    def add_part(self, part_id, on_hand_qty, batch_size, is_leaf=True):
        self.parts[part_id] = {"on_hand_qty": on_hand_qty, "batch_size": batch_size}
        if is_leaf:
            self.leaf_parts.add(part_id)

    def add_bom(self, parent_id, child_id, qty_per, scrap_rate_pct=0.0, setup_scrap_qty=0):
        self.bom.setdefault(parent_id, []).append((child_id, qty_per, scrap_rate_pct, setup_scrap_qty))
        if parent_id in self.leaf_parts:
            self.leaf_parts.remove(parent_id)

    def add_workcenter(self, wc_id, available_hours):
        self.workcenters[wc_id] = available_hours

    def add_routing(self, parent_id, wc_id, setup_hours, run_hours_per_unit):
        self.routing.setdefault(parent_id, []).append((wc_id, setup_hours, run_hours_per_unit))

    def add_substitute(self, primary_id, substitute_id, qty_ratio, preference_rank):
        self.substitutes.setdefault(primary_id, []).append((substitute_id, qty_ratio, preference_rank))
        # Ensure ordered correctly for tests
        self.substitutes[primary_id].sort(key=lambda x: (x[2], x[0]))

def test_basic_netting():
    db = MockDB()
    db.add_part("Product", 0, 1, is_leaf=False)
    db.add_part("SubAssembly", 5, 1, is_leaf=False)
    db.add_part("Leaf", 10, 1)
    db.add_bom("Product", "SubAssembly", 1)
    db.add_bom("SubAssembly", "Leaf", 2)

    # Order 10 units. We have 5 SA. We need 5 more SA.
    # 5 SA require 10 Leaf. We have exactly 10 Leaf.
    # So we can build exactly 10 Product.
    inv_state = {"Product": 0, "SubAssembly": 5, "Leaf": 10}
    wc_state = {}
    res = process_order(db, "O1", "Product", 10, inv_state, wc_state)
    assert res["allocated_qty"] == 10
    assert res["shortfall_qty"] == 0
    assert res["limiting_resource"] is None

def test_scrap():
    db = MockDB()
    db.add_part("Product", 0, 1, is_leaf=False)
    db.add_part("Leaf", 25, 1)
    db.add_bom("Product", "Leaf", 1, scrap_rate_pct=10.0, setup_scrap_qty=5)

    # 10 units. Gross = 5 + ceil(10 * 1 * 1.1) = 5 + 11 = 16.
    # We have 25, so we can easily build 10.
    inv_state = {"Product": 0, "Leaf": 16}
    res = process_order(db, "O1", "Product", 10, inv_state, {})
    assert res["allocated_qty"] == 10
    assert res["limiting_resource"] is None

    # But we can't build 15. 15 -> 5 + ceil(15 * 1.1) = 5 + 17 = 22. Wait, 16 is less than 22.
    res2 = process_order(db, "O2", "Product", 15, inv_state, {})
    assert res2["allocated_qty"] < 15
    assert res2["limiting_resource"] == "Leaf"

def test_multi_level_bom_and_shared_substitutes():
    db = MockDB()
    db.add_part("Product", 0, 1, is_leaf=False)
    db.add_part("Leaf1", 0, 1)
    db.add_part("Sub1", 10, 1) # Ratio 2:1 -> gives 5 equivalent
    db.add_part("Sub2", 10, 1) # Ratio 1:1 -> gives 10 equivalent
    
    db.add_bom("Product", "Leaf1", 1)
    db.add_substitute("Leaf1", "Sub1", 2.0, 1)
    db.add_substitute("Leaf1", "Sub2", 1.0, 2)

    inv_state = {"Product": 0, "Leaf1": 0, "Sub1": 10, "Sub2": 10}
    res = process_order(db, "O1", "Product", 10, inv_state, {})
    assert res["allocated_qty"] == 10
    # Consumes 5 equivalent from Sub1 (10 units) and 5 from Sub2 (5 units)
    assert res["inv_cons"]["Sub1"] == 10
    assert res["inv_cons"]["Sub2"] == 5

def test_lexicographic_tie_break():
    db = MockDB()
    db.add_part("Product", 0, 1, is_leaf=False)
    db.add_part("Leaf_A", 10, 1)
    db.add_part("Leaf_B", 10, 1)
    db.add_bom("Product", "Leaf_A", 2)
    db.add_bom("Product", "Leaf_B", 2)
    
    # 10 units -> need 20 of each. Ratio = 10/20 = 0.5 for both.
    # Tie break should pick "Leaf_A".
    inv_state = {"Product": 0, "Leaf_A": 10, "Leaf_B": 10}
    res = process_order(db, "O1", "Product", 10, inv_state, {})
    assert res["limiting_resource"] == "Leaf_A"

def test_preference_rank_tie_break():
    db = MockDB()
    db.add_part("Product", 0, 1, is_leaf=False)
    db.add_part("Leaf", 0, 1)
    db.add_part("Sub_B", 10, 1)
    db.add_part("Sub_A", 10, 1)
    
    db.add_bom("Product", "Leaf", 1)
    db.add_substitute("Leaf", "Sub_B", 1.0, 1)
    db.add_substitute("Leaf", "Sub_A", 1.0, 1)
    
    # Sub_A should be picked over Sub_B due to ID tiebreaker since rank is equal
    inv_state = {"Product": 0, "Leaf": 0, "Sub_A": 10, "Sub_B": 10}
    res = process_order(db, "O1", "Product", 5, inv_state, {})
    assert res["inv_cons"]["Sub_A"] == 5
    assert res["inv_cons"]["Sub_B"] == 0

def test_stateful_depletion():
    db = MockDB()
    db.add_part("Product", 0, 1, is_leaf=False)
    db.add_part("Leaf", 15, 1)
    db.add_bom("Product", "Leaf", 1)
    
    inv_state = {"Product": 0, "Leaf": 15}
    # First order
    res1 = process_order(db, "O1", "Product", 10, inv_state, {})
    assert res1["allocated_qty"] == 10
    
    # Manually update state
    inv_state["Leaf"] -= res1["inv_cons"]["Leaf"]
    
    # Second order
    res2 = process_order(db, "O2", "Product", 10, inv_state, {})
    assert res2["allocated_qty"] == 5
    assert res2["limiting_resource"] == "Leaf"

def test_cancellation():
    db = MockDB()
    db.add_part("Product", 0, 1, is_leaf=False)
    db.add_part("Leaf", 4, 1)
    db.add_bom("Product", "Leaf", 1)
    
    inv_state = {"Product": 0, "Leaf": 4}
    # Request 10, can only build 4 (which is < 50% of 10) -> Cancel
    res = process_order(db, "O1", "Product", 10, inv_state, {})
    assert res["allocated_qty"] == 0
    assert res["shortfall_qty"] == 10
    assert res["limiting_resource"] == "Leaf"
