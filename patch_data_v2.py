import sys

with open("task/environment/generate_data.py", "r") as f:
    lines = f.readlines()

new_lines = []
for line in lines:
    # Add new parts
    if '("P10", "Test-Setup", 0, 1),' in line:
        new_lines.append(line)
        new_lines.append('    ("P11", "Trap-Initial", 0, 1),\n')
        new_lines.append('    ("P12", "Trap-Sub-Int1", 0, 1),\n')
        new_lines.append('    ("P13", "Trap-Sub-Int2", 0, 1),\n')
        new_lines.append('    ("L15", "Trap-Initial-Leaf", 9, 1),\n')
        new_lines.append('    ("L16", "Trap-Sub-Leaf1", 0, 1),\n')
        new_lines.append('    ("L17", "Trap-Sub-Leaf2", 0, 1),\n')
        new_lines.append('    ("SUB_L16", "Trap-Sub-Stock", 5, 1),\n')
        continue

    # Add BOM entries
    if '("P10", "L14", 1, 0.0, 0),' in line:
        new_lines.append(line)
        new_lines.append('    ("P11", "L15", 5, 0.0, 0),\n')
        new_lines.append('    ("P12", "L16", 1, 0.0, 0),\n')
        new_lines.append('    ("P13", "L17", 1, 0.0, 0),\n')
        continue

    # Add Workcenters
    if '("WC5", "Setup-Test", 10.0),' in line:
        new_lines.append(line)
        new_lines.append('    ("WC6", "Trap-Initial-WC", 8.2),\n')
        continue

    # Add Routing
    if '("P10", "WC5", 2.0, 9.0),' in line:
        new_lines.append(line)
        new_lines.append('    ("P11", "WC6", 5.0, 2.0),\n')
        continue

    # Add Substitutes
    if '("L12", "SUB_L12_B", 1.0, 2),' in line:
        new_lines.append(line)
        new_lines.append('    ("L16", "SUB_L16", 2.0, 1),\n')
        new_lines.append('    ("L17", "SUB_L16", 1.0, 1),\n')
        continue

    # Add Orders
    if '("O00_G", "P10", 1, 6),' in line:
        new_lines.append(line)
        new_lines.append('    ("O00_H", "P11", 2, 7),\n')
        new_lines.append('    ("O00_I", "P12", 3, 8),\n')
        new_lines.append('    ("O00_J", "P13", 1, 9),\n')
        continue

    new_lines.append(line)

with open("task/environment/generate_data.py", "w") as f:
    f.writelines(new_lines)
