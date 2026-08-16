import re

# 1. Update instruction.md
with open("task/instruction.md", "r", encoding="utf-8") as f:
    inst = f.read()

target = "The resource with the lowest ratio strictly below 1.0 is the `limiting_resource`. When `shortfall_qty == 0`"
repl = "The resource with the lowest ratio strictly below 1.0 is the `limiting_resource`. If multiple resources (including a mix of leaf components and workcenters) share the exact same minimum ratio, select the one with the ASCII-smallest resource ID (e.g. `L15` < `WC10`). When `shortfall_qty == 0`"
inst = inst.replace(target, repl)

with open("task/instruction.md", "w", encoding="utf-8") as f:
    f.write(inst)

# 2. Update generate_data.py
with open("task/environment/generate_data.py", "r", encoding="utf-8") as f:
    gen = f.read()

parts_add = """    ("P102", "Net-ML-Prod", 0, 1),
    ("SA103", "Net-ML-SA1", 3, 1),
    ("SA104", "Net-ML-SA2", 5, 1),
    ("L104", "Net-ML-Leaf", 8, 1),
    ("P103", "Shared-Prod1", 0, 1),
    ("P104", "Shared-Prod2", 0, 1),
    ("L105", "Shared-Leaf1", 3, 1),
    ("L106", "Shared-Leaf2", 10, 1),
    ("L107", "Shared-Leaf3", 1, 1),
    ("P105", "Batch-Route-Prod", 0, 1),
    ("SA105", "Batch-Route-SA", 0, 5),
    ("L108", "Batch-Route-Leaf", 100, 1),
]"""
gen = gen.replace("]", parts_add, 1) # replaces the first ] which closes parts_data

bom_add = """    ("P102", "SA103", 2, 0.0, 0),
    ("SA103", "SA104", 2, 0.0, 0),
    ("SA104", "L104", 1, 0.0, 0),
    ("P103", "L105", 1, 0.0, 0),
    ("P103", "L106", 1, 0.0, 0),
    ("P104", "L105", 1, 0.0, 0),
    ("P104", "L107", 1, 0.0, 0),
    ("P105", "SA105", 1, 0.0, 0),
    ("SA105", "L108", 1, 0.0, 0),
]"""
gen = gen.replace("]", bom_add, 1)

wc_add = """    ("WC105", "Batch-Route-WC", 15.0),
]"""
gen = gen.replace("]", wc_add, 1)

rout_add = """    ("SA105", "WC105", 10.0, 2.0),
]"""
gen = gen.replace("]", rout_add, 1)

sub_add = """]"""
gen = gen.replace("]", sub_add, 1) # no substitutes added

ord_add = """    ("O00_N", "P102", 5, 23),
    ("O00_W", "P103", 2, 30),
    ("O00_X", "P104", 2, 31),
    ("O00_Y", "P105", 1, 40),
]"""
gen = gen.replace("]", ord_add, 1)

with open("task/environment/generate_data.py", "w", encoding="utf-8") as f:
    f.write(gen)
