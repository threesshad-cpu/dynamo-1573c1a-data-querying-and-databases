import re

with open("task/tests/test_outputs.py", "r", encoding="utf-8") as f:
    content = f.read()

# Update total count
content = re.sub(r'len\(orders\) == \d+', 'len(orders) == 28', content)
content = content.replace('Expected 24 order results', 'Expected 28 order results')

# Update expected_ids list
target_list = 'expected_ids = ["O00_A", "O00_B", "O00_C", "O00_D", "O00_E", "O00_F", "O00_G", "O00_H", "O00_I", "O00_J", "O00_K", "O00_L", "O00_M", "O00_O", "O00_P", "O00_R1", "O00_R2", "O00_S2", "O01", "O02", "O03", "O04", "O05", "O06"]'
new_list = 'expected_ids = ["O00_A", "O00_B", "O00_C", "O00_D", "O00_E", "O00_F", "O00_G", "O00_H", "O00_I", "O00_J", "O00_K", "O00_L", "O00_M", "O00_N", "O00_O", "O00_P", "O00_R1", "O00_R2", "O00_S2", "O00_W", "O00_X", "O00_Y", "O01", "O02", "O03", "O04", "O05", "O06"]'
content = content.replace(target_list, new_list)

tests_code = """
def test_order_O00_N_allocation():
    \"\"\"Verifies O00_N handles multi-level subassembly netting correctly.\"\"\"
    m = _get_orders_map()
    assert m["O00_N"]["allocated_qty"] == 4
    assert m["O00_N"]["shortfall_qty"] == 1
    assert m["O00_N"]["limiting_resource"] == "L104"

def test_order_O00_W_allocation():
    \"\"\"Verifies O00_W successfully consumes shared resource stock without limiting.\"\"\"
    m = _get_orders_map()
    assert m["O00_W"]["allocated_qty"] == 2
    assert m["O00_W"]["shortfall_qty"] == 0
    assert m["O00_W"]["limiting_resource"] is None

def test_order_O00_X_allocation():
    \"\"\"Verifies O00_X applies global ASCII tie-breaker on shared resources correctly after O00_W.\"\"\"
    m = _get_orders_map()
    assert m["O00_X"]["allocated_qty"] == 1
    assert m["O00_X"]["shortfall_qty"] == 1
    assert m["O00_X"]["limiting_resource"] == "L105"

def test_order_O00_Y_allocation():
    \"\"\"Verifies O00_Y correctly aggregates setup hours exactly once after batch rounding.\"\"\"
    m = _get_orders_map()
    assert m["O00_Y"]["allocated_qty"] == 0
    assert m["O00_Y"]["shortfall_qty"] == 1
    assert m["O00_Y"]["limiting_resource"] == "WC105"
"""

content += tests_code

with open("task/tests/test_outputs.py", "w", encoding="utf-8") as f:
    f.write(content)

# Update task.toml
with open("task/task.toml", "r", encoding="utf-8") as f:
    toml = f.read()

toml = re.sub(r'24 orders \(O00_A to O00_S2', r'28 orders (O00_A to O00_Y', toml)
toml = toml.replace('O01 through O06 test combinations.', 'O00_W and O00_X test shared resource ASCII tie-breakers. O00_Y tests batch rounding setup routing. O01 through O06 test combinations.')
with open("task/task.toml", "w", encoding="utf-8") as f:
    f.write(toml)
