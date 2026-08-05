import json
import math
import sqlite3
from pathlib import Path

# Locate manufacturing.db
db_candidates = [
    Path("/app/manufacturing.db"),
    Path("/tmp/manufacturing.db"),
    Path("/data/manufacturing.db"),
    Path(__file__).resolve().parent.parent / "data" / "manufacturing.db",
]

db_path = None
for candidate in db_candidates:
    if candidate.exists():
        db_path = candidate
        break

if db_path is None or not db_path.exists():
    db_path = Path("/app/manufacturing.db")

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
    "SELECT parent_part_id, child_part_id, qty_per, scrap_rate_pct FROM bom"
)
bom = {}
for parent, child, qty, scrap in cursor.fetchall():
    if parent not in bom:
        bom[parent] = []
    bom[parent].append((child, qty, scrap))

cursor.execute(
    "SELECT order_id, product_part_id, requested_qty, priority FROM orders"
)
orders_raw = cursor.fetchall()
conn.close()

# Identify leaf raw components (parts that never appear as a parent in bom)
parents_set = set(bom.keys())
leaf_parts = {part_id for part_id in parts if part_id not in parents_set}

# Current remaining inventory pool for all parts
inventory = {part_id: parts[part_id]["on_hand_qty"] for part_id in parts}


def get_requirements_for_units(product_id, target_units, inv_snapshot):
    """Simulate top-down BOM explosion consuming pre-built sub-assembly stock
    first."""
    needed_parts = {product_id: target_units}
    consumed_inv = {p: 0 for p in parts}

    while True:
        non_leaf_needed = {
            p: q for p, q in needed_parts.items()
            if p in bom and q > 0
        }
        if not non_leaf_needed:
            break

        for parent_id, qty_needed in non_leaf_needed.items():
            avail = inv_snapshot.get(parent_id, 0) - consumed_inv[parent_id]
            use_prebuilt = min(avail, qty_needed)
            consumed_inv[parent_id] += use_prebuilt
            qty_to_explode = qty_needed - use_prebuilt

            del needed_parts[parent_id]

            if qty_to_explode > 0:
                for child_id, qty_per, scrap_pct in bom.get(parent_id, []):
                    gross_qty = math.ceil(
                        qty_to_explode * qty_per * (1.0 + scrap_pct / 100.0)
                    )
                    needed_parts[child_id] = (
                        needed_parts.get(child_id, 0) + gross_qty
                    )

    # Check raw component sufficiency
    for leaf_id, raw_qty in needed_parts.items():
        avail = inv_snapshot.get(leaf_id, 0) - consumed_inv[leaf_id]
        if avail < raw_qty:
            return False, consumed_inv, needed_parts, leaf_id

    return True, consumed_inv, needed_parts, None


processed_orders = sorted(orders_raw, key=lambda x: (x[3], x[0]))
results = []

for order_id, product_id, requested_qty, priority in processed_orders:
    batch_size = parts[product_id]["batch_size"]
    max_batch_units = (requested_qty // batch_size) * batch_size

    allocated_qty = 0
    best_consumed = None
    best_needed = None
    limiting_component = None

    for u in range(max_batch_units, -1, -batch_size):
        possible, cons, needed, bottleneck = get_requirements_for_units(
            product_id, u, inventory
        )
        if possible:
            allocated_qty = u
            best_consumed = cons
            best_needed = needed
            break

    shortfall_qty = requested_qty - allocated_qty

    if shortfall_qty > 0:
        next_target = allocated_qty + batch_size
        _, _, needed_next, _ = get_requirements_for_units(
            product_id, next_target, inventory
        )

        ratios = []
        for leaf_id in leaf_parts:
            req = needed_next.get(leaf_id, 0)
            avail = inventory.get(leaf_id, 0)
            if req > 0:
                ratio = avail / req
                ratios.append((ratio, leaf_id))

        if ratios:
            ratios.sort(key=lambda x: (x[0], x[1]))
            limiting_component = ratios[0][1]

    if best_consumed:
        for p, qty in best_consumed.items():
            inventory[p] -= qty

    if best_needed:
        for p, qty in best_needed.items():
            inventory[p] -= qty

    results.append(
        {
            "order_id": order_id,
            "allocated_qty": allocated_qty,
            "shortfall_qty": shortfall_qty,
            "limiting_component": limiting_component,
        }
    )

results.sort(key=lambda x: x["order_id"])

report_data = {"orders": results}
report_path = Path("/app/report.json")
report_path.parent.mkdir(parents=True, exist_ok=True)

with open(report_path, "w", encoding="utf-8") as f:
    json.dump(report_data, f, indent=2)

print(f"Generated {report_path} successfully.")
