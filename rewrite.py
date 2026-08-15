import re
with open('task/tests/test_outputs.py', 'r', encoding='utf-8') as f:
    content = f.read()

parts = content.split('def test_order_O00_A_allocation():')
prefix = parts[0]
rest = 'def test_order_O00_A_allocation():' + parts[1]

o00_tests = re.findall(r'def test_order_O00_[a-zA-Z0-9_]+_allocation\(\):\n(?:    .*\n)*', rest)

combined_body = 'def test_order_O00_edge_cases():\n    """Combines all O00 edge case assertions to reduce pytest output."""\n    m = _get_orders_map()\n'
for t in o00_tests:
    lines = t.strip().split('\n')
    for line in lines:
        if line.startswith('def ') or 'm = _get_orders_map()' in line or '\"\"\"' in line:
            continue
        combined_body += line + '\n'

new_content = prefix + combined_body

with open('task/tests/test_outputs.py', 'w', encoding='utf-8') as f:
    f.write(new_content)
print("Done")
