import os

for path in ['submission/task/environment/generate_data.py', 'task/environment/generate_data.py']:
    with open(path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 1. Add P1 -> SA2 edge
    if '("P1", "SA2", 2, 0.0, 0)' not in content:
        content = content.replace(
            '("P1", "SA1", 1, 0.0, 0),',
            '("P1", "SA1", 1, 0.0, 0),\n    ("P1", "SA2", 2, 0.0, 0),'
        )
    
    # 2. Change SA2 routing setup time to 5.0
    content = content.replace('("SA2", "WC2", 0.0, 0.3),', '("SA2", "WC2", 5.0, 0.3),')
    
    # 3. Change WC2 limit to 40.0
    content = content.replace('("WC2", 16.0, 15.0),', '("WC2", 40.0, 15.0),')
    content = content.replace('("WC2", 21.0, 15.0),', '("WC2", 40.0, 15.0),') # Just in case

    with open(path, 'w', encoding='utf-8') as f:
        f.write(content)

print('Trap applied.')
