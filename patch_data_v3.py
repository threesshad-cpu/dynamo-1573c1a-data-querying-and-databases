import sys

with open("task/environment/generate_data.py", "r") as f:
    lines = f.readlines()

new_lines = []
for line in lines:
    # Add new parts
    if '("P13", "Trap-Sub-Int2", 0, 1),' in line:
        new_lines.append(line)
        new_lines.append('    ("P15", "Trap-SA-Lim", 0, 1),\n')
        new_lines.append('    ("P16", "Trap-WC-Batch", 0, 1),\n')
        new_lines.append('    ("P17", "Trap-Scrap-Ceil", 0, 1),\n')
        new_lines.append('    ("SA10", "Trap-SA-Lim-SA", 1, 1),\n')
        new_lines.append('    ("SA11", "Trap-WC-Batch-SA", 0, 5),\n')
        new_lines.append('    ("L20", "Trap-SA-Lim-Leaf", 100, 1),\n')
        new_lines.append('    ("L21", "Trap-Scrap-Leaf", 1, 1),\n')
        continue

    # Add BOM entries
    if '("P13", "L17", 1, 0.0, 0),' in line:
        new_lines.append(line)
        new_lines.append('    ("P15", "SA10", 1, 0.0, 0),\n')
        new_lines.append('    ("SA10", "L20", 1, 0.0, 0),\n')
        new_lines.append('    ("P16", "SA11", 1, 0.0, 0),\n')
        new_lines.append('    ("P17", "L21", 1, 1.0, 0),\n')
        continue

    # Add Workcenters
    if '("WC6", "Trap-Initial-WC", 8.2),' in line:
        new_lines.append(line)
        new_lines.append('    ("WC10", "Trap-SA-Lim-WC", 2.0),\n')
        new_lines.append('    ("WC11", "Trap-WC-Batch-WC", 4.0),\n')
        continue

    # Add Routing
    if '("P11", "WC6", 5.0, 2.0),' in line:
        new_lines.append(line)
        new_lines.append('    ("P15", "WC10", 0.0, 1.0),\n')
        new_lines.append('    ("SA11", "WC11", 0.0, 1.0),\n')
        continue

    # Add Orders
    if '("O00_J", "P13", 1, 9),' in line:
        new_lines.append(line)
        new_lines.append('    ("O00_K", "P15", 3, 20),\n')
        new_lines.append('    ("O00_L", "P16", 1, 21),\n')
        new_lines.append('    ("O00_M", "P17", 1, 22),\n')
        continue

    new_lines.append(line)

with open("task/environment/generate_data.py", "w") as f:
    f.writelines(new_lines)
