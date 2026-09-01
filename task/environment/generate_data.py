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
# 9. Global shared-substitute contention across two or more primary leaves
# 10. Fractional substitute ratios, multi-leaf matching, and batch/cancellation interactions
# 11. Late-order regression families combining global matching, batch capacity, and generated subassembly stock

parts_data = [
    ("L1", "Bolt", 200, 10), ("L2", "Plate", 50, 5), ("L3", "Wire", 15, 1),
    ("L4", "Plastic", 25, 1), ("L_TIE", "Tie-Break Leaf", 17, 1),
    ("L_CANCEL", "Cancellation-Test Leaf", 2, 1), ("SA_LIMIT", "Limiting Subassembly", 2, 3),
    ("SUB_L3_A", "Wire-Alloy", 65, 1), ("SUB_L3_B", "Wire-Copper", 15, 1),
    ("SUB_SHARED", "Shared-Substitute", 21, 1), ("SA1", "Frame", 3, 2), ("SA2", "Module", 0, 4),
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
    ("L_NEW", "New Leaf", 0, 1), ("SUB_NEW_A", "New Sub A", 5, 1), ("SUB_NEW_B", "New Sub B", 5, 1),
    ("P_NEW_1", "Product New 1", 0, 1), ("P_NEW_2", "Product New 2", 0, 1),
    ("P_SCRAP", "Product Scrap", 0, 1), ("L_SCRAP", "Leaf Scrap", 13, 1),
    ("L15", "Leaf 15", 5, 1), ("P15", "Product 15", 0, 1),
    ("L15b", "Leaf 15b", 49, 1), ("P15b", "Product 15b", 0, 1),
    ("P16", "Product 16", 0, 1), ("L16", "Leaf 16", 1000, 1),
    ("L17", "Leaf 17", 0, 1), ("SUB_L17", "Sub 17", 14, 1), ("P17", "Product 17", 0, 1),
    ("L18A", "Leaf 18A", 23, 1), ("P18", "Product 18", 0, 1),
    ("L23A", "Shared Allocation Leaf", 0, 1), ("L23B", "Constrained Allocation Leaf", 0, 1),
    ("SUB23_SHARED", "Shared Substitute 23", 1, 1), ("SUB23_A", "Private Substitute 23", 1, 1),
    ("P23", "Product Shared-Contention", 0, 1),
    ("L24A", "Fractional Flexible Leaf", 1, 1), ("L24B", "Fractional Constrained Leaf", 0, 1),
    ("SUB24", "Fractional Shared Stock", 5, 1), ("P24", "Product Fractional Contention", 0, 1),
    ("L25A", "Ranked Constrained Leaf", 0, 1), ("L25B", "Ranked Flexible Leaf", 0, 1),
    ("SUB25", "Ranked Shared Stock", 3, 1), ("SUB25_PRIVATE", "Ranked Private Fallback", 1, 1),
    ("P25", "Product Ranked Contention", 0, 1),
    ("L26A", "Three-Way Flexible Leaf", 0, 1), ("L26B", "Three-Way Constrained B", 0, 1),
    ("L26C", "Three-Way Constrained C", 0, 1), ("SUB26", "Three-Way Shared Stock", 2, 1),
    ("SUB26_PRIVATE", "Three-Way Private Fallback", 1, 1), ("P26", "Product Three-Way Matching", 0, 1),
    ("L27A", "Batch Flexible Leaf", 1, 1), ("L27B", "Batch Constrained Leaf", 0, 1),
    ("SUB27", "Batch Shared Stock", 3, 1), ("P27", "Product Batch Contention", 0, 2),
    ("L28A", "Deep Shared Leaf A", 0, 1), ("L28B", "Deep Shared Leaf B", 0, 1),
    ("SUB28", "Deep Shared Stock", 3, 1), ("SUB28_PRIVATE", "Deep Private Fallback", 1, 1),
    ("SA28A", "Deep Shared Assembly A", 0, 1), ("SA28B", "Deep Shared Assembly B", 0, 1),
    ("P28", "Product Deep Shared Contention", 0, 1),
    ("L35A", "Late Matching Leaf A", 3, 1), ("L35B", "Late Matching Leaf B", 0, 1),
    ("SUB35", "Late Shared Substitute", 6, 1), ("SUB35P", "Late Private Fallback", 2, 1),
    ("SA35", "Late Matching Assembly", 0, 1), ("P35", "Late Matching Product", 0, 1),
    ("L36A", "Late Deep Leaf A", 0, 1), ("L36B", "Late Deep Leaf B", 0, 1),
    ("SUB36", "Late Deep Shared Substitute", 5, 1), ("SUB36P", "Late Deep Private Fallback", 1, 1),
    ("SA36A", "Late Deep Assembly A", 0, 1), ("SA36B", "Late Deep Assembly B", 0, 1), ("P36", "Late Deep Product", 0, 2),
    ("L37", "Late Capacity Leaf", 5, 1), ("P37", "Late Capacity Product", 0, 2),
    ("SA38", "Late Stock Assembly", 1, 2), ("L38", "Late Scrap Leaf", 10, 1),
    ("SUB38", "Late Scrap Substitute", 6, 1), ("P38", "Late Stock Product", 0, 1),
    ("P43", "Setup Waiver Product", 0, 1),
    ("L45", "Tie-Breaker Leaf", 0, 1), ("SUB45_A", "Tie-Breaker Sub A", 2, 1),
    ("SUB45_B", "Tie-Breaker Sub B", 5, 1), ("P45", "Tie-Breaker Product", 0, 1),
    ("P46", "Tie-Breaker Target Product", 0, 1),
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
    ("P_NEW_1", "L_NEW", 1, 0.0, 0), ("P_NEW_2", "SUB_NEW_B", 1, 0.0, 0),
    ("P_SCRAP", "L_SCRAP", 1, 20.0, 5),
    ("P15", "L15", 1, 0.0, 0), ("P15b", "L15b", 1, 0.0, 0),
    ("P16", "L16", 1, 0.0, 0), ("P17", "L17", 1, 0.0, 0),
    ("P18", "L18A", 3, 0.0, 0),
    ("P23", "L23A", 1, 0.0, 0), ("P23", "L23B", 1, 0.0, 0),
    ("P24", "L24A", 1, 0.0, 0), ("P24", "L24B", 1, 0.0, 0),
    ("P25", "L25A", 1, 0.0, 0), ("P25", "L25B", 1, 0.0, 0),
    ("P26", "L26A", 1, 0.0, 0), ("P26", "L26B", 1, 0.0, 0), ("P26", "L26C", 1, 0.0, 0),
    ("P27", "L27A", 1, 0.0, 0), ("P27", "L27B", 1, 0.0, 0),
    ("P28", "SA28A", 1, 0.0, 0), ("P28", "SA28B", 1, 0.0, 0),
    ("SA28A", "L28A", 2, 0.0, 0), ("SA28B", "L28B", 2, 0.0, 0),
    ("P35", "SA35", 1, 0.0, 0), ("SA35", "L35A", 2, 10.0, 1), ("SA35", "L35B", 1, 0.0, 0),
    ("P36", "SA36A", 1, 0.0, 0), ("P36", "SA36B", 1, 0.0, 0),
    ("SA36A", "L36A", 2, 0.0, 0), ("SA36B", "L36B", 1, 0.0, 0),
    ("P37", "L37", 1, 0.0, 0),
    ("P38", "SA38", 2, 0.0, 0), ("SA38", "L38", 3, 20.0, 1),
    ("P45", "L45", 3, 0.0, 0), ("P46", "SUB45_B", 4, 0.0, 0),
]

workcenters_data = [
    ("WC1", "Assembly", 80.0), ("WC2", "Testing", 100.0), ("WC_TIE", "Tie-Break WC", 17.0),
    ("WC3", "Deep Assembly", 50.0), ("WC4", "Deep Testing", 35.0),
    ("WC5", "Multi-Parent Assembly", 17.5), ("WC6", "Multi-Parent Testing", 100.0),
    ("WC10", "Tie Break 10", 5.0), ("WC2_B", "Tie Break 2", 5.0), ("WC18", "WC 18", 53.67),
    ("WC35", "Late Matching Cell", 20.0), ("WC36", "Late Deep Cell", 30.0),
    ("WC37", "Late Capacity Cell", 5.5), ("WC38", "Late Stock Cell", 30.0),
    ("WC43", "Setup Waiver Cell", 11.0),
]

routing_data = [
    ("SA1", "WC1", 5.0, 1.0), ("SA2", "WC2", 10.0, 2.0), ("P1", "WC1", 2.0, 0.5),
    ("P2", "WC1", 3.0, 1.0), ("P3", "WC2", 1.0, 1.0), ("P4", "WC_TIE", 0.0, 5.0),
    ("P5", "WC1", 0.0, 1.0), ("P_B", "WC1", 0.0, 1.0), ("SA3", "WC3", 4.0, 1.5),
    ("SA4", "WC4", 3.0, 2.0), ("P6", "WC3", 1.0, 0.5), ("P7", "WC4", 1.0, 1.0),
    ("P8", "WC3", 0.0, 1.0), ("P11", "WC4", 0.0, 1.0), ("P12", "WC4", 0.0, 1.0),
    ("SA5", "WC5", 1.0, 1.0), ("SA6", "WC6", 1.0, 1.0), ("P13", "WC5", 0.0, 0.2),
    ("P14", "WC6", 0.0, 1.0), ("P16", "WC10", 0.0, 1.0), ("P16", "WC2_B", 0.0, 1.0),
    ("P18", "WC18", 0.0, 7.0),
    ("SA35", "WC35", 2.0, 1.0), ("P35", "WC35", 1.0, 0.5),
    ("SA36A", "WC36", 1.0, 0.5), ("SA36B", "WC36", 1.0, 0.5), ("SA36B", "WC1", 1.0, 1.0),
    ("P37", "WC37", 2.0, 1.0),
    ("P38", "WC38", 2.0, 1.0),
    ("P43", "WC43", 5.0, 2.0),
]

substitutes_data = [
    ("L2", "SUB_SHARED", 1.0, 1), ("L3", "SUB_L3_A", 2.5, 1),
    ("L3", "SUB_L3_B", 1.0, 1), ("L3", "SUB_SHARED", 1.0, 1),
    ("L5", "SUB5A", 1.5, 1), ("L5", "SUB5B", 1.0, 1),
    ("L_NEW", "SUB_NEW_A", 1.0, 1), ("L_NEW", "SUB_NEW_B", 1.0, 1), ("L17", "SUB_L17", 1.5, 1),
    ("L23A", "SUB23_SHARED", 1.0, 1), ("L23A", "SUB23_A", 1.0, 2), ("L23B", "SUB23_SHARED", 1.0, 1),
    ("L24A", "SUB24", 2.0, 1), ("L24B", "SUB24", 1.5, 1),
    ("L25A", "SUB25", 1.0, 1), ("L25B", "SUB25", 2.0, 2), ("L25B", "SUB25_PRIVATE", 1.0, 3),
    ("L26A", "SUB26", 1.0, 1), ("L26A", "SUB26_PRIVATE", 1.0, 2), ("L26B", "SUB26", 1.0, 1), ("L26C", "SUB26", 1.0, 1),
    ("L27A", "SUB27", 1.0, 1), ("L27B", "SUB27", 1.0, 1),
    ("L28A", "SUB28", 1.0, 1), ("L28A", "SUB28_PRIVATE", 1.0, 2), ("L28B", "SUB28", 1.0, 1),
    ("L35A", "SUB35", 1.0, 1), ("L35A", "SUB35P", 1.0, 2), ("L35B", "SUB35", 1.0, 1),
    ("L36A", "SUB36", 1.0, 1), ("L36A", "SUB36P", 1.0, 2), ("L36B", "SUB36", 1.0, 1),
    ("L38", "SUB38", 1.5, 1),
    ("L45", "SUB45_A", 1.0, 1), ("L45", "SUB45_B", 1.0, 1),
]

orders_data = [
    ("O1", "P1", 12, 10), ("O2", "P2", 10, 20), ("O3", "P3", 10, 30),
    ("O3_N1", "P_NEW_1", 5, 31), ("O3_N2", "P_NEW_2", 5, 32), ("O3b", "P_B", 10, 35),
    ("O4", "P4", 6, 40), ("O5", "P5", 15, 50), ("O6C", "P_CANCEL", 5, 60),
    ("O7", "P_AFTER", 2, 70), ("O8", "P6", 4, 80), ("O9", "P7", 6, 90), ("OA", "P8", 8, 100),
    ("OB", "P11", 5, 110), ("OC", "P12", 2, 120), ("O10C", "P13", 10, 130), ("O11", "P14", 100, 140),
    ("O12", "P_SCRAP", 10, 150), ("O15", "P15", 10, 160), ("O15b", "P15b", 100, 165),
    ("O16", "P16", 10, 170), ("O17", "P17", 10, 180), ("O18", "P18", 10, 190),
    ("O23", "P23", 1, 200), ("O24", "P24", 3, 210), ("O25", "P25", 2, 220),
    ("O26", "P26", 2, 230), ("O27", "P27", 5, 240), ("O28", "P28", 2, 250),
    ("O29", "P23", 2, 260), ("O30", "P24", 4, 270), ("O31", "P25", 3, 280),
    ("O32", "P26", 3, 290), ("O33", "P27", 5, 300), ("O34", "P28", 3, 310),
    ("O35", "P35", 3, 320), ("O36", "P35", 2, 321), ("O37", "P36", 2, 330), ("O38", "P36", 2, 331),
    ("O39", "P37", 4, 340), ("O40", "P37", 4, 341), ("O41", "P38", 2, 350), ("O42", "P38", 1, 351),
    ("O43", "P43", 1, 360), ("O44", "P43", 2, 361),
    ("O45", "P45", 1, 370), ("O46", "P46", 1, 371),
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