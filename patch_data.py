import sys

with open("task/environment/generate_data.py", "r") as f:
    lines = f.readlines()

new_lines = []
for line in lines:
    if '("SUB_L10", "Sub-Trap-Plate", 14, 1)' in line:
        line = line.replace("14", "5")
    if '("L13", "Trap-Metal", 14, 1)' in line:
        line = line.replace("14", "25")
    
    if '("P9", "Product-9", 0, 1),' in line:
        new_lines.append(line)
        new_lines.append('    ("P10", "Test-Setup", 0, 1),\n')
        new_lines.append('    ("L14", "Test-Setup-Leaf", 100, 1),\n')
        continue

    if '("SA8", "L13", 1, 12.5, 2),' in line:
        new_lines.append(line)
        new_lines.append('    ("P10", "L14", 1, 0.0, 0),\n')
        continue

    if '("WC4", "Trap-Station", 2.75),' in line:
        new_lines.append(line)
        new_lines.append('    ("WC5", "Setup-Test", 10.0),\n')
        continue

    if '("SA6", "WC4", 0.5, 0.2),' in line:
        new_lines.append(line)
        new_lines.append('    ("P10", "WC5", 2.0, 9.0),\n')
        continue

    if '("O00_E", "P9", 9, 4),' in line:
        new_lines.append(line)
        new_lines.append('    ("O00_F", "P8", 1, 5),\n')
        new_lines.append('    ("O00_G", "P10", 1, 6),\n')
        continue

    new_lines.append(line)

with open("task/environment/generate_data.py", "w") as f:
    f.writelines(new_lines)
