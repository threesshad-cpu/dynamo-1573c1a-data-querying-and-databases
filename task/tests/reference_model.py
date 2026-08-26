import math
import sqlite3
from pathlib import Path

DB_PATH = Path("/app/manufacturing.db")
if not DB_PATH.exists():
    DB_PATH = Path(__file__).resolve().parent.parent / "environment" / "manufacturing.db"


def compute_reference(db_path=DB_PATH):
    con = sqlite3.connect(str(db_path))
    cur = con.cursor()
    parts = {r[0]: {"batch": r[3], "stock": r[2]} for r in cur.execute("SELECT part_id,name,on_hand_qty,batch_size FROM parts")}
    bom = {}
    for p, c, q, s, setup in cur.execute("SELECT parent_part_id,child_part_id,qty_per,scrap_rate_pct,setup_scrap_qty FROM bom"):
        bom.setdefault(p, []).append((c, q, s, setup))
    workcenters = {r[0]: r[2] for r in cur.execute("SELECT workcenter_id,name,available_hours FROM workcenters")}
    routing = {}
    for p, w, setup, run in cur.execute("SELECT parent_part_id,workcenter_id,setup_hours,run_hours_per_unit FROM routing"):
        routing.setdefault(p, []).append((w, setup, run))
    substitutes = {}
    for p, s, ratio, rank in cur.execute("SELECT primary_part_id,substitute_part_id,qty_ratio,preference_rank FROM substitutes ORDER BY preference_rank,substitute_part_id"):
        substitutes.setdefault(p, []).append((s, ratio, rank))
    orders = list(cur.execute("SELECT order_id,product_part_id,requested_qty,priority FROM orders"))
    con.close()
    leaves = {p for p in parts if p not in bom}

    def allocate(demand, inv, consumed):
        remaining = {}
        for leaf, qty in demand.items():
            if qty <= 0:
                continue
            use = min(qty, inv.get(leaf, 0) - consumed.get(leaf, 0))
            consumed[leaf] = consumed.get(leaf, 0) + use
            remaining[leaf] = qty - use
        if not any(remaining.values()):
            return True
        needed = sorted(x for x, q in remaining.items() if q > 0)
        solutions = []

        def search(i, state, alloc):
            if i == len(needed):
                solutions.append((state, list(alloc)))
                return
            leaf = needed[i]
            options = substitutes.get(leaf, [])

            def split(j, left, current, chosen):
                if left == 0:
                    search(i + 1, current, chosen)
                    return
                if j == len(options):
                    return
                sub, ratio, rank = options[j]
                max_units = min(left, math.floor(max(0, current.get(sub, 0)) / ratio))
                for units in range(max_units, -1, -1):
                    nxt = dict(current)
                    nxt[sub] = nxt.get(sub, 0) - units * ratio
                    picked = list(chosen)
                    if units:
                        picked.append((leaf, sub, units, rank))
                    split(j + 1, left - units, nxt, picked)

            split(0, remaining[leaf], state, alloc)

        initial = {p: inv.get(p, 0) - consumed.get(p, 0) for p in parts}
        search(0, initial, [])
        if not solutions:
            return False

        def score(item):
            _, allocation = item
            total_rank = sum(units * rank for _, _, units, rank in allocation)
            totals = {leaf: 0 for leaf in needed}
            for leaf, _, units, _ in allocation:
                totals[leaf] += units
            primary = tuple(totals[leaf] for leaf in needed)
            detail = tuple(sorted((rank, sub, leaf, -units) for leaf, sub, units, rank in allocation))
            return total_rank, primary, detail

        best = min(solutions, key=score)[1]
        for leaf, sub, units, _ in best:
            ratio = next(r for s, r, _ in substitutes[leaf] if s == sub)
            consumed[sub] = consumed.get(sub, 0) + units * ratio
        return True

    def simulate(product, target, inv, capacity, previous_wcs):
        if target == 0:
            return True, {}, {}, {}, {}, {}
        snapshot = dict(inv)
        consumed = {p: 0 for p in parts}
        created = {p: 0 for p in parts}
        used_wc = {w: 0.0 for w in workcenters}
        gross_leaf = {p: 0 for p in leaves}
        gross_wc = {w: 0.0 for w in workcenters}
        need = {product: target}

        while True:
            active = {p: q for p, q in need.items() if p in bom and q > 0}
            if not active:
                break
            roots = []
            for p in active:
                if not any(p != other and p in [c[0] for c in bom.get(other, ())] for other in active):
                    roots.append(p)
            parent = sorted(roots)[0]
            qty = need.pop(parent)
            primary = min(qty, snapshot.get(parent, 0) - consumed[parent])
            consumed[parent] += primary
            remain = qty - primary

            if remain and parent in substitutes:
                def sub_key(x):
                    sub, _, rank = x
                    return rank, -(snapshot.get(sub, 0) - consumed.get(sub, 0)), sub
                for sub, ratio, _ in sorted(substitutes[parent], key=sub_key):
                    available = snapshot.get(sub, 0) - consumed.get(sub, 0)
                    units = min(remain, math.floor(max(0, available) / ratio))
                    if units:
                        consumed[sub] += units * ratio
                        remain -= units
                    if not remain:
                        break

            if remain:
                batch = parts[parent]["batch"]
                build = math.ceil(remain / batch) * batch
                created[parent] += build - remain
                for workcenter, setup, run in routing.get(parent, ()):
                    setup_eff = 0.0 if workcenter in previous_wcs else setup
                    hours = setup_eff + build * run
                    used_wc[workcenter] += hours
                    gross_wc[workcenter] += hours
                for child, qty_per, scrap, setup_scrap in bom.get(parent, ()):
                    gross = setup_scrap + math.ceil(build * qty_per * (1 + scrap / 100.0))
                    need[child] = need.get(child, 0) + gross

        leaf_demand = {p: q for p, q in need.items() if q > 0}
        for leaf, qty in leaf_demand.items():
            gross_leaf[leaf] = gross_leaf.get(leaf, 0) + qty
        if not allocate(leaf_demand, snapshot, consumed):
            return False, consumed, created, used_wc, gross_leaf, gross_wc
        if any(h > capacity.get(w, 0) + 1e-9 for w, h in used_wc.items()):
            return False, consumed, created, used_wc, gross_leaf, gross_wc
        return True, consumed, created, used_wc, gross_leaf, gross_wc

    inventory = {p: v["stock"] for p, v in parts.items()}
    capacity = dict(workcenters)
    previous_wcs = set()
    result = []

    for order_id, product, requested, _priority in sorted(orders, key=lambda x: x[3]):
        batch = parts[product]["batch"]
        low, high = 0, requested // batch
        best = None
        while low <= high:
            mid = (low + high) // 2
            ok, consumed, created, used, _, _ = simulate(product, mid * batch, inventory, capacity, previous_wcs)
            if ok:
                best = (mid * batch, consumed, created, used)
                low = mid + 1
            else:
                high = mid - 1

        allocated = best[0] if best else 0
        shortfall = requested - allocated
        limiting = None
        if shortfall:
            _, _, _, _, leaf_req, wc_req = simulate(product, allocated + batch, inventory, capacity, previous_wcs)
            ratios = []
            for leaf, required in leaf_req.items():
                if required > 0:
                    available = inventory.get(leaf, 0)
                    for sub, ratio, _ in substitutes.get(leaf, ()):
                        available += math.floor(max(0, inventory.get(sub, 0)) / ratio)
                    ratios.append((available / required, leaf))
            for workcenter, required in wc_req.items():
                if required > 0:
                    ratios.append((capacity.get(workcenter, 0) / required, workcenter))
            constrained = [x for x in ratios if x[0] < 1.0 - 1e-9]
            if constrained:
                limiting = min(constrained, key=lambda x: (x[0], x[1]))[1]

        if requested > 0 and allocated / requested < 0.5:
            allocated = 0
            shortfall = requested
            best = None

        if best:
            _, consumed, created, used = best
            for p, qty in consumed.items():
                inventory[p] -= qty
            for p, qty in created.items():
                inventory[p] += qty
            for workcenter, hours in used.items():
                capacity[workcenter] -= hours
            previous_wcs = {w for w, hours in used.items() if hours > 0}
        else:
            previous_wcs = set()

        result.append({"order_id": order_id, "allocated_qty": allocated, "shortfall_qty": shortfall, "limiting_resource": limiting})

    return sorted(result, key=lambda x: x["order_id"])
