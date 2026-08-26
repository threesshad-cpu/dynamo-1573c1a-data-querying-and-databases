import json
import math
import sqlite3
from pathlib import Path

# Locate manufacturing.db
db_path = Path("/app/manufacturing.db")
if not db_path.exists():
    local_fallback = (
        Path(__file__).resolve().parent.parent / "data" / "manufacturing.db"
    )
    if local_fallback.exists():
        db_path = local_fallback

conn = sqlite3.connect(str(db_path))
cursor = conn.cursor()

cursor.execute("SELECT part_id, name, on_hand_qty, batch_size FROM parts")
parts = {
    row[0]: {
        "name": row[1],
        "on_hand_qty": row[2],
        "batch_size": row[3],
    }
    for row in cursor.fetchall()
}

cursor.execute(
    "SELECT parent_part_id, child_part_id, qty_per, scrap_rate_pct, setup_scrap_qty FROM bom"
)
bom = {}
for parent, child, qty, scrap, setup_scrap in cursor.fetchall():
    if parent not in bom:
        bom[parent] = []
    bom[parent].append((child, qty, scrap, setup_scrap))

cursor.execute("SELECT workcenter_id, name, available_hours FROM workcenters")
workcenters = {
    row[0]: {
        "name": row[1],
        "available_hours": row[2],
    }
    for row in cursor.fetchall()
}

cursor.execute(
    "SELECT parent_part_id, workcenter_id, setup_hours, run_hours_per_unit FROM routing"
)
routing = {}
for parent, wc, setup_h, run_h in cursor.fetchall():
    if parent not in routing:
        routing[parent] = []
    routing[parent].append((wc, setup_h, run_h))

cursor.execute(
    "SELECT primary_part_id, substitute_part_id, qty_ratio, preference_rank FROM substitutes ORDER BY preference_rank ASC, substitute_part_id ASC"
)
substitutes = {}
for prim, sub, ratio, rank in cursor.fetchall():
    if prim not in substitutes:
        substitutes[prim] = []
    substitutes[prim].append((sub, ratio, rank))

cursor.execute(
    "SELECT order_id, product_part_id, requested_qty, priority FROM orders"
)
orders_raw = cursor.fetchall()
conn.close()

parents_set = set(bom.keys())
leaf_parts = {part_id for part_id in parts if part_id not in parents_set}


def allocate_leaf_requirements(leaf_demands, inv_snapshot, inv_consumed):
    remaining = {}
    for leaf_id, req_qty in leaf_demands.items():
        if req_qty <= 0:
            continue
        avail_primary = inv_snapshot.get(leaf_id, 0) - inv_consumed.get(leaf_id, 0)
        use_primary = min(avail_primary, req_qty)
        inv_consumed[leaf_id] = inv_consumed.get(leaf_id, 0) + use_primary
        remaining[leaf_id] = req_qty - use_primary

    if all(v == 0 for v in remaining.values()):
        return True

    leaves = sorted([leaf for leaf, rem in remaining.items() if rem > 0])
    
    leaf_choices = {}
    for leaf in leaves:
        choices = []
        if leaf in substitutes:
            for sub_id, ratio, rank in substitutes[leaf]:
                avail = inv_snapshot.get(sub_id, 0) - inv_consumed.get(sub_id, 0)
                choices.append((sub_id, ratio, rank, avail))
        leaf_choices[leaf] = choices

    valid_allocations = []
    
    def search(leaf_idx, current_alloc, current_inv):
        if leaf_idx == len(leaves):
            valid_allocations.append(list(current_alloc))
            return
            
        leaf = leaves[leaf_idx]
        rem = remaining[leaf]
        
        subs = list(leaf_choices[leaf])
        subs.sort(key=lambda x: (x[2], -current_inv.get(x[0], 0), x[0]))
        
        def partition_rem(sub_idx, rem_to_fill, sub_alloc, temp_inv):
            if rem_to_fill == 0:
                search(leaf_idx + 1, current_alloc + sub_alloc, temp_inv)
                return
            if sub_idx == len(subs):
                return
                
            sub_id, ratio, rank, _ = subs[sub_idx]
            avail_sub = temp_inv.get(sub_id, 0)
            max_primary_units = min(rem_to_fill, math.floor(avail_sub / ratio))
            
            for units in range(max_primary_units, -1, -1):
                next_inv = dict(temp_inv)
                next_inv[sub_id] -= units * ratio
                next_alloc = list(sub_alloc)
                if units > 0:
                    next_alloc.append((leaf, sub_id, units, rank))
                partition_rem(sub_idx + 1, rem_to_fill - units, next_alloc, next_inv)
                
        partition_rem(0, rem, [], current_inv)

    temp_inv = {p: inv_snapshot.get(p, 0) - inv_consumed.get(p, 0) for p in parts}
    search(0, [], temp_inv)
    
    if not valid_allocations:
        return False
        
    def score_alloc(alloc):
        total_rank = sum(units * rank for leaf, sub, units, rank in alloc)
        alloc_tuple = tuple(sorted([
            (rank, sub, leaf, -units) 
            for leaf, sub, units, rank in alloc if units > 0
        ]))
        return (total_rank, alloc_tuple)
        
    best_alloc = min(valid_allocations, key=score_alloc)
    
    for leaf, sub, units, rank in best_alloc:
        ratio = next(r for s, r, rnk in substitutes[leaf] if s == sub)
        inv_consumed[sub] = inv_consumed.get(sub, 0) + units * ratio
        
    return True





def simulate_explosion(product_id, target_units, current_inv, current_wc_hours, last_order_wcs):
    if target_units == 0:
        return True, {}, {}, {}, {}, {}

    inv_snapshot = dict(current_inv)
    wc_consumed = {w: 0.0 for w in workcenters}
    inv_consumed = {p: 0 for p in parts}
    sub_created = {p: 0 for p in parts}

    needed_parts = {product_id: target_units}

    gross_leaf_demand = {p: 0 for p in leaf_parts}
    gross_wc_demand = {w: 0.0 for w in workcenters}

    while True:
        active_parents = {
            p: q for p, q in needed_parts.items() if p in bom and q > 0
        }
        if not active_parents:
            break

        top_level = []
        for p in active_parents:
            has_parent = False
            for other_p in active_parents:
                if other_p == p:
                    continue
                children_of_other = [c[0] for c in bom.get(other_p, [])]
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

        if rem_needed > 0 and parent_id in substitutes:
            def sub_sort_key(sub_info):
                s_id, _, s_rank = sub_info
                avail = inv_snapshot.get(s_id, 0) - inv_consumed.get(s_id, 0)
                return (s_rank, -avail, s_id)
            for sub_id, ratio, rank in sorted(substitutes[parent_id], key=sub_sort_key):
                avail_sub = inv_snapshot.get(sub_id, 0) - inv_consumed.get(sub_id, 0)
                buildable = math.floor(avail_sub / ratio)
                use_sub_units = min(rem_needed, buildable)
                if use_sub_units > 0:
                    sub_qty_consumed = use_sub_units * ratio
                    inv_consumed[sub_id] += sub_qty_consumed
                    rem_needed -= use_sub_units
                if rem_needed == 0:
                    break

        if rem_needed > 0:
            bs = parts[parent_id]["batch_size"]
            build_qty = math.ceil(rem_needed / bs) * bs
            excess = build_qty - rem_needed
            sub_created[parent_id] += excess

            if parent_id in routing:
                for wc_id, setup_h, run_h in routing[parent_id]:
                    eff_setup = 0.0 if wc_id in last_order_wcs else setup_h
                    req_h = eff_setup + (build_qty * run_h)
                    wc_consumed[wc_id] += req_h
                    gross_wc_demand[wc_id] += req_h

            for child_id, qty_per, scrap_pct, setup_scrap in bom.get(
                parent_id, []
            ):
                gross_qty = setup_scrap + math.ceil(
                    build_qty * qty_per * (1.0 + scrap_pct / 100.0)
                )
                needed_parts[child_id] = (
                    needed_parts.get(child_id, 0) + gross_qty
                )

    for leaf_id, req_qty in needed_parts.items():
        if req_qty > 0:
            gross_leaf_demand[leaf_id] = gross_leaf_demand.get(leaf_id, 0) + req_qty

    leaf_feasible = allocate_leaf_requirements(
        {leaf_id: req_qty for leaf_id, req_qty in needed_parts.items() if req_qty > 0},
        inv_snapshot,
        inv_consumed,
    )

    if not leaf_feasible:
        return (
            False,
            inv_consumed,
            sub_created,
            wc_consumed,
            gross_leaf_demand,
            gross_wc_demand,
        )

    for wc_id, req_h in wc_consumed.items():
        if req_h > current_wc_hours.get(wc_id, 0.0) + 1e-9:
            return (
                False,
                inv_consumed,
                sub_created,
                wc_consumed,
                gross_leaf_demand,
                gross_wc_demand,
            )

    return (
        True,
        inv_consumed,
        sub_created,
        wc_consumed,
        gross_leaf_demand,
        gross_wc_demand,
    )


curr_inv = {p: parts[p]["on_hand_qty"] for p in parts}
curr_wc_hours = {w: workcenters[w]["available_hours"] for w in workcenters}

sorted_orders = sorted(orders_raw, key=lambda x: x[3])

results = []
last_order_wcs = set()
for order_id, product_id, requested_qty, priority in sorted_orders:
    bs = parts[product_id]["batch_size"]

    allocated_qty = 0
    best_inv_cons = None
    best_sub_created = None
    best_wc_cons = None

    low = 0
    high = requested_qty // bs

    while low <= high:
        mid = (low + high) // 2
        u = mid * bs
        possible, inv_cons, sub_created, wc_cons, _, _ = simulate_explosion(
            product_id, u, curr_inv, curr_wc_hours, last_order_wcs
        )
        if possible:
            allocated_qty = u
            best_inv_cons = inv_cons
            best_sub_created = sub_created
            best_wc_cons = wc_cons
            low = mid + 1
        else:
            high = mid - 1

    shortfall_qty = requested_qty - allocated_qty
    limiting_resource = None

    if shortfall_qty > 0:
        next_target = allocated_qty + bs
        _, _, _, _, leaf_req, wc_req = simulate_explosion(
            product_id, next_target, curr_inv, curr_wc_hours, last_order_wcs
        )

        ratios = []

        for leaf_id in leaf_parts:
            req = leaf_req.get(leaf_id, 0)
            if req > 0:
                eff_avail = curr_inv.get(leaf_id, 0)
                if leaf_id in substitutes:
                    for sub_id, ratio, rank in substitutes[leaf_id]:
                        eff_avail += math.floor(curr_inv.get(sub_id, 0) / ratio)
                ratio_val = eff_avail / req
                ratios.append((ratio_val, leaf_id))

        for wc_id in workcenters:
            req_h = wc_req.get(wc_id, 0.0)
            if req_h > 0:
                avail_h = curr_wc_hours.get(wc_id, 0.0)
                ratio_val = avail_h / req_h
                ratios.append((ratio_val, wc_id))

        constrained_ratios = [r for r in ratios if r[0] < 1.0 - 1e-9]
        if constrained_ratios:
            constrained_ratios.sort(key=lambda x: (x[0], x[1]))
            limiting_resource = constrained_ratios[0][1]

    if requested_qty > 0 and allocated_qty / requested_qty < 0.5:
        allocated_qty = 0
        shortfall_qty = requested_qty
        best_inv_cons = None
        best_sub_created = None
        best_wc_cons = None

    if best_inv_cons:
        for p, q in best_inv_cons.items():
            curr_inv[p] -= q
    if best_sub_created:
        for p, q in best_sub_created.items():
            curr_inv[p] += q
    if best_wc_cons:
        last_order_wcs = set(w for w, h in best_wc_cons.items() if h > 0)
        for w, h in best_wc_cons.items():
            curr_wc_hours[w] -= h
    else:
        last_order_wcs = set()

    results.append(
        {
            "order_id": order_id,
            "allocated_qty": allocated_qty,
            "shortfall_qty": shortfall_qty,
            "limiting_resource": limiting_resource,
        }
    )

results.sort(key=lambda x: x["order_id"])

report_data = {"orders": results}
written_file = None
for report_path in [
    Path("/app/report.json"),
    Path(__file__).resolve().parent.parent.parent / "report.json",
]:
    try:
        report_path.parent.mkdir(parents=True, exist_ok=True)
        results.sort(key=lambda x: x["order_id"])
        report_data = {"orders": results}
        with open(report_path, "w", encoding="utf-8") as f:
            json.dump(report_data, f, indent=2)
        if report_path.exists() and report_path.is_file():
            written_file = report_path
            break
    except (PermissionError, OSError):
        continue

if not written_file:
    raise RuntimeError(
        "Failed to generate report.json at /app/report.json or local fallback"
    )

print(f"Generated report successfully at {written_file}.")
