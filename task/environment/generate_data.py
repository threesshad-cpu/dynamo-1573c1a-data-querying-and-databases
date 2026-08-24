import sqlite3
from pathlib import Path

# Dataset focuses on interacting MRP mechanics:
# 1. Batch Rounding
# 2. Parent/Sub-Assembly Netting
# 3. Aggregated BOM Explosion
# 4. Deterministic Substitution
# 5. Gross Limiting Resource
# 6. Cancellation without state consumption
# 7. Multi-order state carried through deeper shared BOM branches
# 8. Multi-parent deep BOM with shared sub-assembly production and capacity

parts_data = [
    ("L1", "Bolt", 200, 10), ("L2", "Plate", 50, 5), ("L3", "Wire", 15, 1),
    ("L4", "Plastic", 25, 1), ("L_TIE", "Tie-Break Leaf", 17, 1),
    ("L_CANCEL", "Cancellation-Test Leaf", 2, 1), ("SA_LIMIT", "Limiting Subassembly", 2, 3),
    ("SUB_L3_A", "Wire-Alloy", 12, 1), ("SUB_L3_B", "Wire-Copper", 8, 1),
    ("SUB_SHARED", "Shared-Substitute", 20, 1), ("SA1", "Frame", 3, 2), ("SA2", "Module", 0, 4),
    ("L5", "Composite Leaf", 30, 2), ("L6", "Fastener Leaf", 20, 1),
    ("L7", "Cancellation Leaf", 2, 1), ("SUB5A", "Composite Substitute A", 9, 1),
    ("SUB5B", "Composite Substitute B", 7, 1), ("SA3", "Deep Frame", 3, 3),
    ("SA4", "Deep Module", 2, 2),
    ("L8", "Deep Capacity Leaf", 100, 1), ("L9", "Deep Shared Leaf", 100, 1),
    ("SA5", "Multi-Parent Frame", 1, 2), ("SA6", "Multi-Parent Module", 0, 1),
    ("P1", "Product-BatchNet", 0, 1), ("P2", "Product-Aggregate", 0, 1),
    ("P3", "Product-Subst", 0, 1), ("P4", "Product-Limit", 0, 1),
    ("P5", "Product-Stateful", 0, 1), ("P_B", "Product-SubstTie", 0, 1),
    ("P_CANCEL", "Product-Cancel", 0, 1), ("P_AFTER", "Product-AfterCancel", 0, 1),
    ("P6", "Product-DeepCascade", 0, 1), ("P7", "Product-CrossOrder", 0, 1),
    ("P8", "Product-SubstituteCascade", 0, 1), ("P11", "Product-DeepCancel", 0, 1),
    ("P12", "Product-DeepAfterCancel", 0, 1),
    ("P13", "Product-MultiParentCapacity", 0, 1), ("P14", "Product-AfterDeepCancel", 0, 1),
]

bom_data = [
    ("P1", "SA1", 1, 0.0, 0), ("SA1", "L1", 4, 5.0, 2),
    ("P2", "SA1", 1, 0.0, 0), ("P2", "SA2", 2, 0.0, 0),
    ("SA2", "SA1", 1, 0.0, 1), ("SA2", "L2", 3, 3.0, 1),
    ("P3", "L3", 5, 0.0, 0), ("P4", "SA_LIMIT", 1, 0.0, 0),
    ("SA_LIMIT", "L4", 5, 0.0, 0), ("P4", "L_TIE", 5, 0.0, 0),
    ("P5", "L4", 1, 0.0, 0), ("P_B", "SUB_L3_B", 1, 0.0, 0),
    ("P_CANCEL", "L_CANCEL", 1, 0.0, 0), ("P_AFTER", "L_CANCEL", 1, 0.0, 0),
    ("SA3", "L5", 3, 10.0, 1), ("SA3", "L6", 1, 0.0, 0),
    ("SA4", "SA3", 1, 0.0, 0), ("SA4", "L6", 2, 5.0, 1),
    ("P6", "SA4", 1, 0.0, 0), ("P6", "SA3", 1, 0.0, 0), ("P6", "L5", 2, 0.0, 0),
    ("P7", "SA4", 1, 0.0, 0), ("P7", "L5", 5, 0.0, 0), ("P8", "L5", 6, 0.0, 0),
    ("P11", "L7", 1, 0.0, 0), ("P12", "L7", 1, 0.0, 0),
    ("P13", "SA5", 2, 0.0, 0), ("P13", "SA6", 1, 0.0, 0),
    ("SA6", "SA5", 1, 0.0, 0), ("SA6", "L9", 2, 0.0, 0),
    ("SA5", "L8", 3, 0.0, 1), ("P14", "L9", 1, 0.0, 0),
]

workcenters_data = [
    ("WC1", "Assembly", 80.0), ("WC2", "Testing", 100.0), ("WC_TIE", "Tie-Break WC", 17.0),
    ("WC3", "Deep Assembly", 50.0), ("WC4", "Deep Testing", 35.0),
    ("WC5", "Multi-Parent Assembly", 17.5), ("WC6", "Multi-Parent Testing", 100.0),
]

routing_data = [
    ("SA1", "WC1", 5.0, 1.0), ("SA2", "WC2", 10.0, 2.0), ("P1", "WC1", 2.0, 0.5),
    ("P2", "WC1", 3.0, 1.0), ("P3", "WC2", 1.0, 1.0), ("P4", "WC_TIE", 0.0, 5.0),
    ("P5", "WC1", 0.0, 1.0), ("P_B", "WC1", 0.0, 1.0), ("SA3", "WC3", 4.0, 1.5),
    ("SA4", "WC4", 3.0, 2.0), ("P6", "WC3", 1.0, 0.5), ("P7", "WC4", 1.0, 1.0),
    ("P8", "WC3", 0.0, 1.0), ("P11", "WC4", 0.0, 1.0), ("P12", "WC4", 0.0, 1.0),
    ("SA5", "WC5", 1.0, 1.0), ("SA6", "WC6", 1.0, 1.0), ("P13", "WC5", 0.0, 0.2),
    ("P14", "WC6", 0.0, 1.0),
]

substitutes_data = [
    ("L2", "SUB_SHARED", 1.0, 1), ("L3", "SUB_L3_A", 2.5, 1),
    ("L3", "SUB_L3_B", 1.0, 1), ("L3", "SUB_SHARED", 1.0, 1),
    ("L5", "SUB5A", 1.5, 1), ("L5", "SUB5B", 1.0, 1),
]

orders_data = [
    ("O1", "P1", 12, 10), ("O2", "P2", 10, 20), ("O3", "P3", 10, 30),
    ("O3b", "P_B", 10, 35), ("O4", "P4", 6, 40), ("O5", "P5", 15, 50),
    ("O6C", "P_CANCEL", 5, 60), ("O7", "P_AFTER", 2, 70), ("O8", "P6", 4, 80),
    ("O9", "P7", 6, 90), ("OA", "P8", 8, 100), ("OB", "P11", 5, 110), ("OC", "P12", 2, 120),
    ("O10C", "P13", 10, 130), ("O11", "P14", 100, 140),
]


def create_database(db_path: Path):
    db_path.parent.mkdir(parents=True, exist_ok=True)
    if db_path.exists():
        db_path.unlink()
    conn = sqlite3.connect(str(db_path))
    cursor = conn.cursor()
    cursor.execute("""CREATE TABLE parts (part_id TEXT PRIMARY KEY, name TEXT NOT NULL, on_hand_qty INTEGER NOT NULL, batch_size INTEGER NOT NULL)""")
    cursor.execute("""CREATE TABLE bom (parent_part_id TEXT NOT NULL, child_part_id TEXT NOT NULL, qty_per INTEGER NOT NULL, scrap_rate_pct REAL NOT NULL, setup_scrap_qty INTEGER NOT NULL, PRIMARY KEY (parent_part_id, child_part_id))""")
    cursor.execute("""CREATE TABLE workcenters (workcenter_id TEXT PRIMARY KEY, name TEXT NOT NULL, available_hours REAL NOT NULL)""")
    cursor.execute("""CREATE TABLE routing (parent_part_id TEXT NOT NULL, workcenter_id TEXT NOT NULL, setup_hours REAL NOT NULL, run_hours_per_unit REAL NOT NULL, PRIMARY KEY (parent_part_id, workcenter_id))""")
    cursor.execute("""CREATE TABLE substitutes (primary_part_id TEXT NOT NULL, substitute_part_id TEXT NOT NULL, qty_ratio REAL NOT NULL, preference_rank INTEGER NOT NULL, PRIMARY KEY (primary_part_id, substitute_part_id))""")
    cursor.execute("""CREATE TABLE orders (order_id TEXT PRIMARY KEY, product_part_id TEXT NOT NULL, requested_qty INTEGER NOT NULL, priority INTEGER NOT NULL)""")
    cursor.executemany("INSERT INTO parts VALUES (?, ?, ?, ?)", parts_data)
    cursor.executemany("INSERT INTO bom VALUES (?, ?, ?, ?, ?)", bom_data)
    cursor.executemany("INSERT INTO workcenters VALUES (?, ?, ?)", workcenters_data)
    cursor.executemany("INSERT INTO routing VALUES (?, ?, ?, ?)", routing_data)
    cursor.executemany("INSERT INTO substitutes VALUES (?, ?, ?, ?)", substitutes_data)
    cursor.executemany("INSERT INTO orders VALUES (?, ?, ?, ?)", orders_data)
    conn.commit()
    conn.close()
    print(f"Generated SQLite DB at {db_path}")


if __name__ == "__main__":
    app_db = Path("/app/manufacturing.db")
    try:
        create_database(app_db)
    except (PermissionError, OSError):
        pass
    local_db = Path(__file__).resolve().parent.parent / "data" / "manufacturing.db"
    create_database(local_db)
