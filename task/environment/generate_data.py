import sqlite3
from pathlib import Path

# Dataset focuses on 6 core mechanics:
# 1. Batch Rounding
# 2. Parent Netting
# 3. Aggregated BOM Explosion
# 4. Deterministic Substitution
# 5. Gross Limiting Resource
# 6. Cancellation without state consumption

parts_data = [
    # Leaf raw materials
    ("L1", "Bolt", 200, 10),
    ("L2", "Plate", 50, 5),
    ("L3", "Wire", 15, 1),
    ("L4", "Plastic", 25, 1),
    ("L_TIE", "Tie-Break Leaf", 17, 1),
    ("L_CANCEL", "Cancellation-Test Leaf", 2, 1),
    
    ("SA_LIMIT", "Limiting Subassembly", 2, 3),
    
    # Substitutes
    ("SUB_L3_A", "Wire-Alloy", 12, 1), # ratio 2.5, rank 1
    ("SUB_L3_B", "Wire-Copper", 8, 1),  # ratio 1.0, rank 1
    ("SUB_SHARED", "Shared-Substitute", 20, 1), # ratio 1.0, rank 1
    
    # Sub-assemblies
    ("SA1", "Frame", 3, 2),
    ("SA2", "Module", 0, 4),
    
    # Finished products
    ("P1", "Product-BatchNet", 0, 1),
    ("P2", "Product-Aggregate", 0, 1),
    ("P3", "Product-Subst", 0, 1),
    ("P4", "Product-Limit", 0, 1),
    ("P5", "Product-Stateful", 0, 1),
    ("P_B", "Product-SubstTie", 0, 1),
    ("P_CANCEL", "Product-Cancel", 0, 1),
    ("P_AFTER", "Product-AfterCancel", 0, 1),
]

bom_data = [
    # parent, child, qty_per, scrap_rate_pct, setup_scrap
    
    # P1: Tests Batch Rounding + Parent Netting
    # Requires SA1. We have 3 SA1s in stock.
    ("P1", "SA1", 1, 0.0, 0),
    ("SA1", "L1", 4, 5.0, 2), # 5% scrap, 2 setup scrap
    
    # P2: Tests Aggregated BOM Explosion
    # P2 requires both SA1 and SA2.
    # SA2 also requires SA1 (so SA1 appears in multiple paths)
    ("P2", "SA1", 1, 0.0, 0),
    ("P2", "SA2", 2, 0.0, 0),
    ("SA2", "SA1", 1, 0.0, 1),
    ("SA2", "L2", 3, 3.0, 1),
    
    # P3: Tests Deterministic Substitution
    ("P3", "L3", 5, 0.0, 0),
    
    # P4: Tests Gross Limiting Resource & ASCII tie-break
    ("P4", "SA_LIMIT", 1, 0.0, 0),
    ("SA_LIMIT", "L4", 5, 0.0, 0),
    ("P4", "L_TIE", 5, 0.0, 0),
    
    # P5: Tests Stateful Inventory Depletion
    ("P5", "L4", 1, 0.0, 0),
    
    # P_B: Tests Substitute Tie-Break Remaining Inventory
    ("P_B", "SUB_L3_B", 1, 0.0, 0),

    # P_CANCEL: deliberately buildable to 2/5 (<50%), so the order must cancel.
    # The later P_AFTER order proves cancellation consumes no inventory.
    ("P_CANCEL", "L_CANCEL", 1, 0.0, 0),
    ("P_AFTER", "L_CANCEL", 1, 0.0, 0),
]

workcenters_data = [
    ("WC1", "Assembly", 80.0),
    ("WC2", "Testing", 100.0),
    ("WC_TIE", "Tie-Break WC", 17.0),
]

routing_data = [
    # parent, wc, setup, run
    ("SA1", "WC1", 5.0, 1.0),
    ("SA2", "WC2", 10.0, 2.0),
    ("P1", "WC1", 2.0, 0.5),
    ("P2", "WC1", 3.0, 1.0),
    ("P3", "WC2", 1.0, 1.0),
    ("P4", "WC_TIE", 0.0, 5.0),
    ("P5", "WC1", 0.0, 1.0),
    ("P_B", "WC1", 0.0, 1.0),
]

substitutes_data = [
    # primary, substitute, ratio, rank
    ("L2", "SUB_SHARED", 1.0, 1), # L2 can use SUB_SHARED
    ("L3", "SUB_L3_A", 2.5, 1), # 1 L3 needs 2.5 SUB_L3_A
    ("L3", "SUB_L3_B", 1.0, 1), # both rank 1 to force ASCII tie-break
    ("L3", "SUB_SHARED", 1.0, 1), # L3 can also use SUB_SHARED
]

orders_data = [
    # order_id, product, requested_qty, priority
    ("O1", "P1", 12, 10),
    ("O2", "P2", 10, 20),
    ("O3", "P3", 10, 30),
    ("O3b", "P_B", 10, 35),
    ("O4", "P4", 6, 40),
    ("O5", "P5", 15, 50),
    ("O6C", "P_CANCEL", 5, 60),
    ("O7", "P_AFTER", 2, 70),
]

def create_database(db_path: Path):
    db_path.parent.mkdir(parents=True, exist_ok=True)
    if db_path.exists():
        db_path.unlink()

    conn = sqlite3.connect(str(db_path))
    cursor = conn.cursor()

    cursor.execute(
        """
        CREATE TABLE parts (
            part_id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            on_hand_qty INTEGER NOT NULL,
            batch_size INTEGER NOT NULL
        )
    """
    )

    cursor.execute(
        """
        CREATE TABLE bom (
            parent_part_id TEXT NOT NULL,
            child_part_id TEXT NOT NULL,
            qty_per INTEGER NOT NULL,
            scrap_rate_pct REAL NOT NULL,
            setup_scrap_qty INTEGER NOT NULL,
            PRIMARY KEY (parent_part_id, child_part_id)
        )
    """
    )

    cursor.execute(
        """
        CREATE TABLE workcenters (
            workcenter_id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            available_hours REAL NOT NULL
        )
    """
    )

    cursor.execute(
        """
        CREATE TABLE routing (
            parent_part_id TEXT NOT NULL,
            workcenter_id TEXT NOT NULL,
            setup_hours REAL NOT NULL,
            run_hours_per_unit REAL NOT NULL,
            PRIMARY KEY (parent_part_id, workcenter_id)
        )
    """
    )

    cursor.execute(
        """
        CREATE TABLE substitutes (
            primary_part_id TEXT NOT NULL,
            substitute_part_id TEXT NOT NULL,
            qty_ratio REAL NOT NULL,
            preference_rank INTEGER NOT NULL,
            PRIMARY KEY (primary_part_id, substitute_part_id)
        )
    """
    )

    cursor.execute(
        """
        CREATE TABLE orders (
            order_id TEXT PRIMARY KEY,
            product_part_id TEXT NOT NULL,
            requested_qty INTEGER NOT NULL,
            priority INTEGER NOT NULL
        )
    """
    )

    cursor.executemany("INSERT INTO parts VALUES (?, ?, ?, ?)", parts_data)
    cursor.executemany("INSERT INTO bom VALUES (?, ?, ?, ?, ?)", bom_data)
    cursor.executemany(
        "INSERT INTO workcenters VALUES (?, ?, ?)", workcenters_data
    )
    cursor.executemany("INSERT INTO routing VALUES (?, ?, ?, ?)", routing_data)
    cursor.executemany(
        "INSERT INTO substitutes VALUES (?, ?, ?, ?)", substitutes_data
    )
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

