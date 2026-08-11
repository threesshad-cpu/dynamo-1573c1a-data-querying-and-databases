import os
for path in ['submission/task/environment/generate_data.py', 'task/environment/generate_data.py']:
    with open(path, 'r', encoding='utf-8') as f:
        content = f.read()
    content = content.replace('("SA2", "Sensor-Module", 2, 4),', '("SA2", "Sensor-Module", 2, 7),')
    content = content.replace('("WC2", 21.0, 15.0),', '("WC2", 16.0, 15.0),')
    with open(path, 'w', encoding='utf-8') as f:
        f.write(content)
