import os
import sys
import json
from pathlib import Path
import numpy as np
from rdflib import Graph, Namespace, RDF, RDFS

os.makedirs("/app", exist_ok=True)

ttl_path = Path("/app/data/corporate_graph.ttl")
if not ttl_path.exists():
    alt_path = Path(__file__).resolve().parent.parent / "data" / "corporate_graph.ttl"
    if alt_path.exists():
        ttl_path = alt_path

g = Graph()
g.parse(str(ttl_path), format="turtle")
EX = Namespace("http://example.org/entity/")

all_entities = sorted(list(set(g.subjects(RDF.type, EX.Company))))

has_incoming = set()
for s, p, o in g.triples((None, EX.owns, None)):
    target = g.value(o, EX.target)
    has_incoming.add(target)

top_parents = sorted([e for e in all_entities if e not in has_incoming])
subsidiaries = sorted([e for e in all_entities if e not in top_parents])

parent_idx = {p: i for i, p in enumerate(top_parents)}
sub_idx = {s: i for i, s in enumerate(subsidiaries)}

M = len(top_parents)
N = len(subsidiaries)

P = np.zeros((M, N), dtype=np.float64)
C = np.zeros((N, N), dtype=np.float64)

for s, p, o in g.triples((None, EX.owns, None)):
    target = g.value(o, EX.target)
    pct = float(g.value(o, EX.percentage))

    if s in parent_idx and target in sub_idx:
        P[parent_idx[s], sub_idx[target]] = pct
    elif s in sub_idx and target in sub_idx:
        C[sub_idx[s], sub_idx[target]] = pct

# Solve V = P * (I - C)^(-1)
I = np.eye(N, dtype=np.float64)
V = np.matmul(P, np.linalg.inv(I - C))

eval_date = "2026-07-29"
parent_sanctions = {}
for p in top_parents:
    sanctions = set()
    for _, _, s_node in g.triples((p, EX.hasSanction, None)):
        cat = str(g.value(s_node, EX.category))
        eff = str(g.value(s_node, EX.effectiveDate))
        exp = str(g.value(s_node, EX.expirationDate))
        if eff <= eval_date <= exp:
            sanctions.add(cat)
    parent_sanctions[p] = sanctions

high_risk = []
for j, sub in enumerate(subsidiaries):
    exempt = g.value(sub, EX.exemptFromInheritance)
    is_exempt = str(exempt).lower() == "true" if exempt else False

    label = str(g.value(sub, RDFS.label) or sub)
    total_effective_ownership = float(np.sum(V[:, j]))

    inherited_sanctions = set()
    for i, p in enumerate(top_parents):
        v_pj = float(V[i, j])
        if v_pj >= 0.25 and not is_exempt:
            inherited_sanctions.update(parent_sanctions.get(p, []))

    if total_effective_ownership >= 0.25 and len(inherited_sanctions) > 0:
        high_risk.append(
            {
                "entity_id": str(sub),
                "entity_name": label,
                "effective_ownership": round(total_effective_ownership, 4),
                "inherited_sanctions": sorted(list(inherited_sanctions)),
            }
        )

high_risk.sort(key=lambda x: (-x["effective_ownership"], x["entity_id"]))

report = {
    "evaluation_date": eval_date,
    "high_risk_subsidiaries": high_risk,
    "summary": {
        "total_entities_analyzed": len(all_entities),
        "flagged_subsidiaries_count": len(high_risk),
    },
}

with open("/app/report.json", "w") as f:
    json.dump(report, f, indent=2)

print("Generated /app/report.json successfully using Integrated Matrix Inversion.")
