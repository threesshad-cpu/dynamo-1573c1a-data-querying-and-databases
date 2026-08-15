import re
with open('task/environment/generate_data.py', 'r') as f:
    text = f.read()

# Remove duplicate L22
text = re.sub(r'(\(\"L22\", \"Trap-WC-Batch-Leaf\", 100, 1\),\s*){2,}', r'\1', text)

# Remove duplicate SA11 -> L22
text = re.sub(r'(\(\"SA11\", \"L22\", 1, 0\.0, 0\),\s*){2,}', r'\1', text)

with open('task/environment/generate_data.py', 'w') as f:
    f.write(text)
