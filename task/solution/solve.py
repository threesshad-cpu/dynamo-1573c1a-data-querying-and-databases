import json
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

if db_path is None:
    db_path = Path("/app/manufacturing.db")
    db_path.parent.mkdir(parents=True, exist_ok=True)
    # Inline database generator fallback
    parts_data = [
        ("L1", "Bolt-M4", 500),
        ("L2", "Bolt-M6", 300),
        ("L3", "Steel-Plate", 40),
        ("L4", "Rubber-Gasket", 150),
        ("L5", "Circuit-Board", 25),
        ("L6", "Wire-Harness", 60),
        ("SA1", "Bracket-Assembly", 0),
        ("SA2", "Sensor-Module", 0),
        ("SA3", "Base-Frame", 0),
        ("P1", "Widget-X", 0),
        ("P2", "Widget-Y", 0),
    ]
    bom_data = [
        ("SA1", "L1", 4),
        ("SA1", "L3", 1),
        ("SA2", "L5", 1),
        ("SA2", "L6", 2),
        ("SA2", "L1", 2),
        ("SA3", "L3", 2),
        ("SA3", "L2", 6),
        ("SA3", "L4", 4),
        ("P1", "SA1", 2),
        ("P1", "SA2", 1),
        ("P1", "L2", 4),
        ("P2", "SA1", 1),
        ("P2", "SA3", 1),
        ("P2", "L4", 2),
    ]
    orders_data = [
        ("O0", "P2", 5, 0),
        ("O1", "P1", 30, 1),
        ("O2", "P2", 20, 2),
        ("O3", "P1", 15, 3),
    ]
    conn = sqlite3.connect(str(db_path))
    c = conn.cursor()
    c.execute("CREATE TABLE parts (part_id TEXT PRIMARY KEY, name TEXT NOT NULL, on_hand_qty INTEGER NOT NULL)")
    c.execute("CREATE TABLE bom (parent_part_id TEXT NOT NULL, child_part_id TEXT NOT NULL, qty_per INTEGER NOT NULL, PRIMARY KEY (parent_part_id, child_part_id))")
    c.execute("CREATE TABLE orders (order_id TEXT PRIMARY KEY, product_part_id TEXT NOT NULL, requested_qty INTEGER NOT NULL, priority INTEGER NOT NULL)")
    c.executemany("INSERT INTO parts VALUES (?, ?, ?)", parts_data)
    c.executemany("INSERT INTO bom VALUES (?, ?, ?)", bom_data)
    c.executemany("INSERT INTO orders VALUES (?, ?, ?, ?)", orders_data)
    conn.commit()
    conn.close()

conn = sqlite3.connect(str(db_path))
cursor = conn.cursor()

# Load parts
cursor.execute("SELECT part_id, name, on_hand_qty FROM parts")
parts = {row[0]: {"name": row[1], "on_hand_qty": row[2]} for row in cursor.fetchall()}

# Load bom relationships: parent_part_id -> [(child_part_id, qty_per), ...]
cursor.execute("SELECT parent_part_id, child_part_id, qty_per FROM bom")
bom = {}
for parent, child, qty in cursor.fetchall():
    if parent not in bom:
        bom[parent] = []
    bom[parent].append((child, qty))

# Load orders: list of (order_id, product_part_id, requested_qty, priority)
cursor.execute("SELECT order_id, product_part_id, requested_qty, priority FROM orders")
orders_raw = cursor.fetchall()
conn.close()

# Identify leaf raw components (parts with on_hand_qty > 0 or not appearing as parent in bom)
parents_set = set(bom.keys())
leaf_parts = {part_id for part_id, info in parts.items() if info["on_hand_qty"] > 0 or part_id not in parents_set}

# Explode BOM with memoization and cycle detection
memo = {}


def get_leaf_requirements(part_id, visiting=None):
    if visiting is None:
        visiting = set()

    if part_id in visiting:
        raise ValueError(f"Cycle detected in BOM involving part {part_id}")

    if part_id in memo:
        return memo[part_id]

    if part_id in leaf_parts:
        reqs = {part_id: 1}
        memo[part_id] = reqs
        return reqs

    visiting.add(part_id)
    reqs = {}
    for child_id, qty_per in bom.get(part_id, []):
        child_reqs = get_leaf_requirements(child_id, visiting)
        for leaf_id, leaf_qty in child_reqs.items():
            reqs[leaf_id] = reqs.get(leaf_id, 0) + leaf_qty * qty_per

    visiting.remove(part_id)
    memo[part_id] = reqs
    return reqs


# Initialize shared inventory pool for leaf components
shared_inventory = {leaf_id: parts[leaf_id]["on_hand_qty"] for leaf_id in leaf_parts}

# Sort orders by priority ascending, then order_id ascending
processed_orders = sorted(orders_raw, key=lambda x: (x[3], x[0]))

results = []

for order_id, product_id, requested_qty, priority in processed_orders:
    reqs = get_leaf_requirements(product_id)

    # Compute maximum buildable units
    max_buildable_list = []
    for leaf_id, qty_per in reqs.items():
        rem = shared_inventory.get(leaf_id, 0)
        max_buildable_list.append(rem // qty_per)

    max_buildable = min(max_buildable_list) if max_buildable_list else 0
    allocated_qty = min(requested_qty, max_buildable)
    shortfall_qty = requested_qty - allocated_qty

    limiting_component = None
    if shortfall_qty > 0:
        # Find raw component with smallest remaining_on_hand / qty_per ratio
        # Ties broken by part_id ascending ASCII
        ratios = []
        for leaf_id, qty_per in reqs.items():
            rem = shared_inventory.get(leaf_id, 0)
            ratio = rem / qty_per
            ratios.append((ratio, leaf_id))

        ratios.sort(key=lambda x: (x[0], x[1]))
        limiting_component = ratios[0][1]

    # Deduct allocated_qty * qty_per from shared inventory
    for leaf_id, qty_per in reqs.items():
        shared_inventory[leaf_id] -= allocated_qty * qty_per

    results.append(
        {
            "order_id": order_id,
            "allocated_qty": allocated_qty,
            "shortfall_qty": shortfall_qty,
            "limiting_component": limiting_component,
        }
    )

# Sort results by order_id ascending
results.sort(key=lambda x: x["order_id"])

report_data = {"orders": results}

report_path = Path("/app/report.json")
report_path.parent.mkdir(parents=True, exist_ok=True)

with open(report_path, "w", encoding="utf-8") as f:
    json.dump(report_data, f, indent=2)

print(f"Generated {report_path} successfully.")
