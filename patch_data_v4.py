import sys

with open("task/environment/generate_data.py", "r") as f:
    lines = f.readlines()

new_lines = []
for line in lines:
    if '("L21", "Trap-Scrap-Leaf", 1, 1),' in line:
        new_lines.append(line)
        new_lines.append('    ("L22", "Trap-WC-Batch-Leaf", 100, 1),\n')
        continue

    if '("P17", "L21", 1, 1.0, 0),' in line:
        new_lines.append(line)
        new_lines.append('    ("SA11", "L22", 1, 0.0, 0),\n')
        continue

    new_lines.append(line)

with open("task/environment/generate_data.py", "w") as f:
    f.writelines(new_lines)
