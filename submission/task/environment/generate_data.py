import sqlite3
from pathlib import Path

parts_data = [
    # Leaf raw materials
    ("L1", "Bolt-M4", 350, 1),
    ("L2", "Bolt-M6", 300, 1),
    ("L3", "Steel-Plate", 95, 1),
    ("L4", "Rubber-Gasket", 150, 1),
    ("L5", "Circuit-Board", 31, 1),
    ("L6", "Wire-Harness", 58, 1),
    ("L7", "LED-Display", 30, 1),
    ("L8", "Power-Unit", 40, 1),
    ("SUB_L3", "Alloy-Plate", 30, 1),     # Substitute for L3 (ratio 2.0: 1 L3 needs 2 SUB_L3)
    ("SUB_L6", "Flex-Cable", 10, 1),      # Substitute for L6 (ratio 1.0: 1 L6 needs 1 SUB_L6)

    # Sub-assemblies
    ("SA1", "Bracket-Assembly", 4, 5),
    ("SA2", "Sensor-Module", 2, 4),
    ("SA3", "Base-Frame", 0, 6),
    ("SA4", "Control-Panel", 2, 5),

    # Finished products
    ("P1", "Widget-X", 0, 5),
    ("P2", "Widget-Y", 0, 4),
    ("P3", "Widget-Z", 0, 2),
]

bom_data = [
    # parent, child, qty_per, scrap_rate_pct, setup_scrap_qty
    ("SA1", "L1", 4, 0.0, 2),
    ("SA1", "L3", 1, 5.5, 1),
    ("SA2", "L5", 1, 0.0, 0),
    ("SA2", "L6", 2, 5.0, 1),
    ("SA2", "L1", 2, 0.0, 0),
    ("SA3", "L3", 2, 0.0, 0),
    ("SA3", "L2", 6, 0.0, 2),
    ("SA3", "L4", 4, 2.5, 0),
    ("SA4", "SA2", 1, 0.0, 0),
    ("SA4", "L7", 1, 0.0, 0),
    ("P1", "SA1", 2, 0.0, 0),
    ("P1", "SA2", 1, 0.0, 0),
    ("P1", "L2", 4, 0.0, 0),
    ("P2", "SA1", 1, 0.0, 0),
    ("P2", "SA3", 1, 0.0, 0),
    ("P2", "L4", 2, 0.0, 0),
    ("P3", "SA4", 1, 0.0, 0),
    ("P3", "L8", 1, 0.0, 0),
]

workcenters_data = [
    ("WC1", "Stamping-Press", 50.0),
    ("WC2", "Assembly-Line", 23.0),
    ("WC3", "Testing-Station", 18.0),
]

routing_data = [
    # parent, workcenter, setup_hours, run_hours_per_unit
    ("SA1", "WC1", 1.0, 0.2),
    ("SA2", "WC2", 0.5, 0.3),
    ("SA3", "WC1", 1.5, 0.4),
    ("SA4", "WC3", 0.8, 0.25),
    ("P1", "WC2", 2.0, 0.5),
    ("P2", "WC1", 1.0, 0.3),
    ("P3", "WC3", 1.2, 0.6),
]

substitutes_data = [
    # primary_part_id, substitute_part_id, qty_ratio, preference_rank
    ("L3", "SUB_L3", 2.0, 1),
    ("L6", "SUB_L6", 1.0, 1),
]

orders_data = [
    ("O01", "P2", 14, 1),
    ("O02", "P1", 30, 2),
    ("O03", "P3", 15, 3),
    ("O04", "P2", 20, 4),
    ("O05", "P1", 25, 5),
    ("O06", "P3", 25, 6),
    ("O07", "P2", 20, 7),
    ("O08", "P1", 15, 8),
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
    except Exception:
        pass

    local_db = Path(__file__).resolve().parent.parent / "data" / "manufacturing.db"
    create_database(local_db)
