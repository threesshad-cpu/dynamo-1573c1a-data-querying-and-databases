import sqlite3
import math
import json
from pathlib import Path

class DatabaseState:
    def __init__(self, db_path):
        self.conn = sqlite3.connect(str(db_path))
        self.cursor = self.conn.cursor()
        
        self.cursor.execute("SELECT part_id, name, on_hand_qty, batch_size FROM parts")
        self.parts = {row[0]: {"on_hand_qty": row[2], "batch_size": row[3]} for row in self.cursor.fetchall()}
        
        self.cursor.execute("SELECT parent_part_id, child_part_id, qty_per, scrap_rate_pct, setup_scrap_qty FROM bom")
        self.bom = {}
        for p, c, q, s_pct, s_qty in self.cursor.fetchall():
            self.bom.setdefault(p, []).append((c, q, s_pct, s_qty))
            
        self.cursor.execute("SELECT workcenter_id, available_hours FROM workcenters")
        self.workcenters = {row[0]: row[1] for row in self.cursor.fetchall()}
        
        self.cursor.execute("SELECT parent_part_id, workcenter_id, setup_hours, run_hours_per_unit FROM routing")
        self.routing = {}
        for p, w, sh, rh in self.cursor.fetchall():
            self.routing.setdefault(p, []).append((w, sh, rh))
            
        self.cursor.execute("SELECT primary_part_id, substitute_part_id, qty_ratio, preference_rank FROM substitutes ORDER BY preference_rank ASC, substitute_part_id ASC")
        self.substitutes = {}
        for p, s, qr, pr in self.cursor.fetchall():
            self.substitutes.setdefault(p, []).append((s, qr, pr))
            
        self.cursor.execute("SELECT order_id, product_part_id, requested_qty, priority FROM orders ORDER BY priority ASC")
        self.orders = self.cursor.fetchall()
        
        self.parents_set = set(self.bom.keys())
        self.leaf_parts = {p for p in self.parts if p not in self.parents_set}

    def close(self):
        self.conn.close()

def simulate_production_run(db, product_id, target_units, inv_state, wc_state, last_order_wcs):
    if target_units == 0:
        return True, {}, {}, {}, {}, {}

    inv_snapshot = dict(inv_state)
    wc_consumed = {w: 0.0 for w in wc_state}
    inv_consumed = {p: 0 for p in db.parts}
    sub_created = {p: 0 for p in db.parts}

    needed_parts = {product_id: target_units}
    gross_leaf_demand = {p: 0 for p in db.leaf_parts}
    gross_wc_demand = {w: 0.0 for w in db.workcenters}

    while True:
        active_parents = {p: q for p, q in needed_parts.items() if p in db.bom and q > 0}
        if not active_parents:
            break

        top_level = []
        for p in active_parents:
            has_parent = False
            for other_p in active_parents:
                if other_p == p: continue
                children_of_other = [c[0] for c in db.bom.get(other_p, [])]
                if p in children_of_other:
                    has_parent = True
                    break
            if not has_parent:
                top_level.append(p)
                
        parent_id = sorted(top_level)[0]
        qty_needed = needed_parts.pop(parent_id)

        avail_primary = inv_snapshot.get(parent_id, 0) - inv_consumed[parent_id]
        use_primary = min(avail_primary, qty_needed)
        inv_consumed[parent_id] += use_primary
        rem_needed = qty_needed - use_primary

        if rem_needed > 0 and parent_id in db.substitutes:
            def sub_sort_key(sub_info):
                s_id, _, s_rank = sub_info
                avail = inv_snapshot.get(s_id, 0) - inv_consumed.get(s_id, 0)
                return (s_rank, -avail, s_id)
            for sub_id, ratio, rank in sorted(db.substitutes[parent_id], key=sub_sort_key):
                avail_sub = inv_snapshot.get(sub_id, 0) - inv_consumed[sub_id]
                buildable = math.floor(avail_sub / ratio)
                use_sub = min(rem_needed, buildable)
                if use_sub > 0:
                    inv_consumed[sub_id] += use_sub * ratio
                    rem_needed -= use_sub
                if rem_needed == 0:
                    break

        if rem_needed > 0:
            bs = db.parts[parent_id]["batch_size"]
            build_qty = math.ceil(rem_needed / bs) * bs
            sub_created[parent_id] += (build_qty - rem_needed)

            if parent_id in db.routing:
                for wc_id, setup_h, run_h in db.routing[parent_id]:
                    eff_setup = 0.0 if wc_id in last_order_wcs else setup_h
                    req_h = eff_setup + (build_qty * run_h)
                    wc_consumed[wc_id] += req_h
                    gross_wc_demand[wc_id] += req_h

            for child_id, qty_per, scrap_pct, setup_scrap in db.bom.get(parent_id, []):
                gross_qty = setup_scrap + math.ceil(build_qty * qty_per * (1.0 + scrap_pct / 100.0))
                needed_parts[child_id] = needed_parts.get(child_id, 0) + gross_qty

    for leaf_id, req_qty in needed_parts.items():
        if req_qty > 0:
            gross_leaf_demand[leaf_id] = gross_leaf_demand.get(leaf_id, 0) + req_qty

    from allocator import allocate_leaf_requirements
    
    remaining_leaves = {leaf_id: req_qty for leaf_id, req_qty in needed_parts.items() if req_qty > 0}
    for leaf_id, req_qty in list(remaining_leaves.items()):
        avail_prim = inv_snapshot.get(leaf_id, 0) - inv_consumed[leaf_id]
        use_prim = min(avail_prim, req_qty)
        inv_consumed[leaf_id] += use_prim
        remaining_leaves[leaf_id] -= use_prim
        
    leaf_feasible = allocate_leaf_requirements(db, remaining_leaves, inv_snapshot, inv_consumed)

    if not leaf_feasible:
        return False, inv_consumed, sub_created, wc_consumed, gross_leaf_demand, gross_wc_demand

    for wc_id, req_h in wc_consumed.items():
        if req_h > wc_state.get(wc_id, 0.0) + 1e-9:
            return False, inv_consumed, sub_created, wc_consumed, gross_leaf_demand, gross_wc_demand

    return True, inv_consumed, sub_created, wc_consumed, gross_leaf_demand, gross_wc_demand

def process_order(db, order_id, product_id, requested_qty, inv_state, wc_state, last_order_wcs):
    bs = db.parts[product_id]["batch_size"]
    
    allocated_qty = 0
    best_inv_cons = None
    best_sub_created = None
    best_wc_cons = None

    max_possible_batches = requested_qty // bs
    
    for batches in range(1, max_possible_batches + 1):
        target = batches * bs
        possible, inv_cons, sub_created, wc_cons, _, _ = simulate_production_run(
            db, product_id, target, inv_state, wc_state, last_order_wcs
        )
        if possible:
            allocated_qty = target
            best_inv_cons = inv_cons
            best_sub_created = sub_created
            best_wc_cons = wc_cons
        else:
            break

    shortfall_qty = requested_qty - allocated_qty
    limiting_resource = None

    if shortfall_qty > 0:
        next_target = allocated_qty + bs
        _, _, _, _, leaf_req, wc_req = simulate_production_run(
            db, product_id, next_target, inv_state, wc_state, last_order_wcs
        )
        ratios = []
        for leaf_id in db.leaf_parts:
            req = leaf_req.get(leaf_id, 0)
            if req > 0:
                eff_avail = inv_state.get(leaf_id, 0)
                if leaf_id in db.substitutes:
                    for sub_id, ratio, rank in db.substitutes[leaf_id]:
                        eff_avail += math.floor(inv_state.get(sub_id, 0) / ratio)
                ratio_val = eff_avail / req
                ratios.append((ratio_val, leaf_id))
                
        for wc_id in db.workcenters:
            req_h = wc_req.get(wc_id, 0.0)
            if req_h > 0:
                avail_h = wc_state.get(wc_id, 0.0)
                ratio_val = avail_h / req_h
                ratios.append((ratio_val, wc_id))
                
        constrained = [r for r in ratios if r[0] < 1.0 - 1e-9]
        if constrained:
            constrained.sort(key=lambda x: (x[0], x[1]))
            limiting_resource = constrained[0][1]

    if requested_qty > 0 and (allocated_qty / requested_qty) < 0.5:
        allocated_qty = 0
        shortfall_qty = requested_qty
        best_inv_cons = None
        best_sub_created = None
        best_wc_cons = None
        
    return {
        "order_id": order_id,
        "allocated_qty": allocated_qty,
        "shortfall_qty": shortfall_qty,
        "limiting_resource": limiting_resource,
        "inv_cons": best_inv_cons,
        "sub_created": best_sub_created,
        "wc_cons": best_wc_cons
    }

def run_all_orders(db_path):
    db = DatabaseState(db_path)
    inv_state = {p: db.parts[p]["on_hand_qty"] for p in db.parts}
    wc_state = {w: db.workcenters[w] for w in db.workcenters}
    
    results = {}
    last_order_wcs = set()
    for order_id, product_id, requested_qty, priority in db.orders:
        res = process_order(db, order_id, product_id, requested_qty, inv_state, wc_state, last_order_wcs)
        
        if res["inv_cons"]:
            for p, q in res["inv_cons"].items():
                inv_state[p] -= q
        if res["sub_created"]:
            for p, q in res["sub_created"].items():
                inv_state[p] += q
        if res["wc_cons"]:
            last_order_wcs = set(w for w, h in res["wc_cons"].items() if h > 0)
            for w, h in res["wc_cons"].items():
                wc_state[w] -= h
        else:
            last_order_wcs = set()
                
        results[order_id] = {
            "order_id": res["order_id"],
            "allocated_qty": res["allocated_qty"],
            "shortfall_qty": res["shortfall_qty"],
            "limiting_resource": res["limiting_resource"]
        }
    
    db.close()
    return results

if __name__ == "__main__":
    db_path = Path(__file__).resolve().parent.parent / "data" / "manufacturing.db"
    if not db_path.exists():
        db_path = Path("/app/manufacturing.db")
    res = run_all_orders(db_path)
    print(json.dumps(res, indent=2))
