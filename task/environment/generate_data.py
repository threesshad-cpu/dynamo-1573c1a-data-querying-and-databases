



import sqlite3
from pathlib import Path

parts_data = [
    # Leaf raw materials
    ("L1", "Bolt-M4", 350, 1),
    ("L2", "Bolt-M6", 300, 1),
    ("L3", "Steel-Plate", 55, 1),
    ("L4", "Rubber-Gasket", 150, 1),
    ("L5", "Circuit-Board", 12, 1),
    ("L6", "Wire-Harness", 58, 1),
    ("L7", "LED-Display", 30, 1),
    ("L8", "Power-Unit", 40, 1),
    ("SUB_L3", "Alloy-Plate", 18, 1),
    # Substitute for L3 (ratio 2.0: 1 L3 needs 2 SUB_L3)
    ("SUB_L6", "Flex-Cable", 10, 1),
    # Substitute for L6 (ratio 1.0: 1 L6 needs 1 SUB_L6)
    ("SUB_L5", "Alt-Board", 32, 1),
    # Substitute for L5 (ratio 2.0: 1 L5 needs 2 SUB_L5)

    # Sub-assemblies
    ("SA1", "Bracket-Assembly", 2, 4),
    ("SA2", "Sensor-Module", 2, 7),
    ("SA3", "Base-Frame", 0, 6),
    ("SA4", "Control-Panel", 2, 5),
    # Finished products
    ("P1", "Widget-X", 0, 5),
    ("P2", "Widget-Y", 0, 4),
    ("P3", "Widget-Z", 0, 2),
    ("P4", "Gadget-Q", 0, 3),
    ("L10", "Trap-Plate", 0, 1),
    ("L11", "Trap-Wire", 100, 1),
    ("L12", "Trap-Sensor", 0, 1),
    ("L13", "Trap-Metal", 25, 1),
    ("SUB_L10", "Sub-Trap-Plate", 5, 1),
    ("SUB_L12_A", "Sub-Sensor-A", 7, 1),
    ("SUB_L12_B", "Sub-Sensor-B", 10, 1),
    ("SA5", "Trap-Assembly", 0, 10),
    ("SA6", "Core-Assembly", 0, 5),
    ("SA8", "Trap-Sub-8", 0, 10),
    ("P5", "Trap-Product", 0, 2),
    ("P6", "Test-Pref", 0, 1),
    ("P7", "Test-Pref-Followup", 0, 1),
    ("P8", "Product-8", 0, 1),
    ("P9", "Product-9", 0, 1),
    ("P10", "Test-Setup", 0, 1),
    ("P11", "Trap-Initial", 0, 1),
    ("P12", "Trap-Sub-Int1", 0, 1),
    ("P13", "Trap-Sub-Int2", 0, 1),
    ("P15", "Trap-SA-Lim", 0, 1),
    ("P16", "Trap-WC-Batch", 0, 1),
    ("P17", "Trap-Scrap-Ceil", 0, 1),
    ("SA10", "Trap-SA-Lim-SA", 1, 1),
    ("SA11", "Trap-WC-Batch-SA", 0, 5),
    ("L20", "Trap-SA-Lim-Leaf", 100, 1),
    ("L21", "Trap-Scrap-Leaf", 1, 1),
    ("L22", "Trap-WC-Batch-Leaf", 100, 1),
    ("L15", "Trap-Initial-Leaf", 9, 1),
    ("L16", "Trap-Sub-Leaf1", 0, 1),
    ("L17", "Trap-Sub-Leaf2", 0, 1),
    ("SUB_L16", "Trap-Sub-Stock", 5, 1),
    ("SA30", "Net-SA", 0, 5),
    ("P18", "Tie-Break-Prod", 0, 1),
    ("P30", "Net-Prod", 0, 1),
    ("L14", "Test-Setup-Leaf", 100, 1),
    ("Z9", "Tie-Break-9", 10, 1),
    ("Z10", "Tie-Break-10", 10, 1),
    ("L30", "Net-Leaf", 109, 1),
    ("P40", "Float-Trap-Prod", 0, 1),
    ("P50", "Sub-Leftover-Prod1", 0, 1),
    ("P51", "Sub-Leftover-Prod2", 0, 1),
    ("L50", "Sub-Leftover-Leaf", 0, 1),
    ("SUB_50", "Sub-Leftover-Sub", 4, 1),
    ("P70", "DFS-Trap-Prod", 0, 1),
    ("SA70", "DFS-Trap-SA1", 0, 1),
    ("SA71", "DFS-Trap-SA2", 0, 1),
    ("SA72", "DFS-Trap-SA-Shared", 0, 1),
    ("L70", "DFS-Trap-Leaf", 100, 1),
    ("L40", "Float-Trap-Leaf", 10, 1),
    ("P80", "Sub-Blindspot-Prod", 0, 1),
    ("SA80", "Sub-Blindspot-SA", 0, 10),
    ("L80", "Sub-Blindspot-Leaf", 0, 1),
    ("L81", "Sub-Blindspot-Raw", 100, 1),
    ("P90", "Shared-Sub-Prod", 0, 1),
    ("L91", "Shared-Sub-L1", 0, 1),
    ("L92", "Shared-Sub-L2", 0, 1),
    ("SUB_90", "Shared-Sub", 1, 1),
]

bom_data = [
    # parent, child, qty_per, scrap_rate_pct, setup_scrap_qty
    ("SA1", "L1", 4, 0.0, 2),
    ("SA1", "SA2", 1, 0.0, 0),
    ("SA1", "L3", 1, 5.0, 3),
    ("SA2", "L5", 1, 0.0, 0),
    ("SA2", "L6", 2, 5.0, 1),
    ("SA2", "L1", 2, 0.0, 0),
    ("SA3", "L3", 2, 0.0, 0),
    ("SA3", "L2", 6, 0.0, 2),
    ("SA3", "L4", 4, 2.5, 0),
    ("SA4", "SA2", 1, 0.0, 0),
    ("SA4", "L7", 1, 0.0, 0),
    ("P1", "SA1", 1, 0.0, 0),
    ("P1", "SA2", 2, 0.0, 0),
    ("P1", "L2", 4, 0.0, 0),
    ("P2", "SA1", 1, 0.0, 0),
    ("P2", "SA3", 1, 0.0, 0),
    ("P2", "L4", 2, 0.0, 0),
    ("P3", "SA4", 1, 0.0, 0),
    ("P3", "L8", 1, 0.0, 0),
    ("P4", "L1", 1, 0.0, 0),
    ("P4", "L4", 1, 0.0, 0),
    ("P5", "SA5", 1, 0.0, 0),
    ("SA5", "SA6", 1, 0.0, 0),
    ("SA5", "L10", 2, 0.0, 0),
    ("SA6", "L11", 1, 0.0, 0),
    ("SA6", "L12", 1, 0.0, 0),
    ("P6", "L12", 1, 0.0, 0),
    ("P7", "SUB_L12_B", 1, 0.0, 0),
    ("P8", "SA8", 1, 0.0, 0),
    ("P9", "SA8", 1, 0.0, 0),
    ("SA8", "L13", 1, 12.5, 2),
    ("P10", "L14", 1, 0.0, 0),
    ("P11", "L15", 5, 0.0, 0),
    ("P12", "L16", 1, 0.0, 0),
    ("P13", "L17", 1, 0.0, 0),
    ("P15", "SA10", 1, 0.0, 0),
    ("SA10", "L20", 1, 0.0, 0),
    ("P16", "SA11", 1, 0.0, 0),
    ("P17", "L21", 1, 1.0, 0),
    ("SA11", "L22", 1, 0.0, 0),
    ("SA30", "L30", 10, 0.0, 0),
    ("P30", "SA30", 2, 0.0, 0),
    ("P18", "Z9", 1, 0.0, 0),
    ("P18", "Z10", 1, 0.0, 0),
    ("P50", "L50", 2, 0.0, 0),
    ("P51", "SUB_50", 1, 0.0, 0),
    ("P70", "SA70", 1, 0.0, 0),
    ("P70", "SA71", 1, 0.0, 0),
    ("SA70", "SA72", 1, 0.0, 0),
    ("SA71", "SA72", 1, 0.0, 0),
    ("SA72", "L70", 1, 0.0, 0),
    ("P40", "L40", 1, 0.0, 0),
    ("P80", "SA80", 1, 0.0, 0),
    ("P80", "L80", 1, 0.0, 0),
    ("SA80", "L81", 1, 0.0, 0),
    ("P90", "L91", 1, 0.0, 0),
    ("P90", "L92", 1, 0.0, 0),
]

workcenters_data = [
    ("WC1", "Stamping-Press", 50.0),
    ("WC2", "Assembly-Line", 21.0),
    ("WC3", "Testing-Station", 18.0),
    ("WC4", "Trap-Station", 2.75),
    ("WC5", "Setup-Test", 10.0),
    ("WC6", "Trap-Initial-WC", 8.2),
    ("WC10", "Trap-SA-Lim-WC", 2.0),
    ("WC11", "Trap-WC-Batch-WC", 4.0),
    ("WC30", "Net-WC", 33.0),
    ("WC31", "Net-WC31", 100.0),
    ("WC40", "Float-Trap-WC", 0.3),
    ("WC70", "DFS-Trap-WC", 15.0),
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
    ("P4", "WC1", 1.0, 11.0),
    ("P4", "WC3", 0.6, 10.2),
    ("P5", "WC4", 2.0, 1.0),
    ("SA5", "WC4", 1.0, 0.5),
    ("SA6", "WC4", 0.5, 0.2),
    ("P10", "WC5", 2.0, 9.0),
    ("P11", "WC6", 5.0, 2.0),
    ("P15", "WC10", 0.0, 1.0),
    ("SA11", "WC11", 0.0, 1.0),
    ("P30", "WC30", 0.0, 10.0),
    ("SA30", "WC31", 0.0, 1.0),
    ("P40", "WC40", 0.1, 0.2),
    ("SA72", "WC70", 10.0, 1.0),
]

substitutes_data = [
    # primary_part_id, substitute_part_id, qty_ratio, preference_rank
    ("L3", "SUB_L3", 2.0, 1),
    ("L6", "SUB_L6", 1.0, 1),
    ("L5", "SUB_L5", 2.0, 1),
    ("L10", "SUB_L10", 3.0, 1),
    ("L12", "SUB_L12_A", 2.0, 1),
    ("L12", "SUB_L12_B", 1.0, 2),
    ("L16", "SUB_L16", 2.0, 1),
    ("L17", "SUB_L16", 1.0, 1),
    ("L50", "SUB_50", 1.5, 1),
    ("SUB_L3", "L10", 2.0, 3),
    ("L80", "SA80", 1.0, 1),
    ("L91", "SUB_90", 1.0, 1),
    ("L92", "SUB_90", 1.0, 1),
]


orders_data = [
    ("O00_A", "P5", 3, 0),
    ("O00_B", "P6", 10, 1),
    ("O00_C", "P7", 3, 2),
    ("O00_D", "P8", 1, 3),
    ("O00_E", "P9", 9, 4),
    ("O00_F", "P8", 1, 5),
    ("O00_G", "P10", 1, 6),
    ("O00_H", "P11", 2, 7),
    ("O00_I", "P12", 3, 8),
    ("O00_J", "P13", 1, 9),
    ("O00_K", "P15", 3, 20),
    ("O00_L", "P16", 1, 21),
    ("O00_M", "P17", 1, 22),
    ("O00_N", "P18", 20, 23),
    ("O00_O", "P30", 3, 24),
    ("O00_P", "P30", 1, 25),
    ("O00_Q", "P40", 1, 994),
    ("O00_U", "P80", 1, 993),
    ("O00_V", "P90", 1, 992),
    ("O00_R1", "P51", 1, 991),
    ("O00_R2", "P51", 1, 990),
    ("O00_S2", "P70", 1, 989),
    ("O01", "P2", 14, 11),
    ("O02", "P1", 30, 12),
    ("O03", "P3", 15, 12),
    ("O04", "P2", 20, 14),
    ("O05", "P4", 5, 15),
    ("O06", "P3", 8, 16),
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
