import os
import sys
import json
from pathlib import Path
import numpy as np
from rdflib import Graph, Namespace, RDF, RDFS

os.makedirs("/app", exist_ok=True)

ttl_candidates = [
    Path("/app/data/corporate_graph.ttl"),
    Path(__file__).resolve().parent.parent / "data" / "corporate_graph.ttl",
    Path("/tmp/corporate_graph.ttl"),
    Path("/data/corporate_graph.ttl"),
]

ttl_path = None
for candidate in ttl_candidates:
    if candidate.exists():
        ttl_path = candidate
        break

if ttl_path is None:
    ttl_path = Path("/app/data/corporate_graph.ttl")
    ttl_path.parent.mkdir(parents=True, exist_ok=True)
    ttl_content = """@prefix ex: <http://example.org/entity/> .
@prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .
@prefix xsd: <http://www.w3.org/2001/XMLSchema#> .

ex:P1 a ex:Company ; rdfs:label "Apex Global Holdings" ;
    ex:hasSanction [ ex:category "Financial" ; ex:effectiveDate "2025-01-01" ; ex:expirationDate "2027-12-31" ] ;
    ex:hasSanction [ ex:category "Trade" ; ex:effectiveDate "2024-05-01" ; ex:expirationDate "2026-12-31" ] .

ex:P2 a ex:Company ; rdfs:label "Sovereign Trust" ;
    ex:hasSanction [ ex:category "Defense" ; ex:effectiveDate "2025-06-01" ; ex:expirationDate "2028-01-01" ] .

ex:P3 a ex:Company ; rdfs:label "Clean Energy Inc" .

ex:E101 a ex:Company ; rdfs:label "Alpha Subsidiary" .
ex:E102 a ex:Company ; rdfs:label "Beta Logistics" .
ex:E103 a ex:Company ; rdfs:label "Gamma Shipping" .
ex:E104 a ex:Company ; rdfs:label "Delta Energy Services" ; ex:exemptFromInheritance true .
ex:E105 a ex:Company ; rdfs:label "Epsilon Maritime" .

ex:P1 ex:owns [ ex:target ex:E101 ; ex:percentage 0.60 ] .
ex:P1 ex:owns [ ex:target ex:E102 ; ex:percentage 0.20 ] .

ex:E101 ex:owns [ ex:target ex:E102 ; ex:percentage 0.50 ] .
ex:E102 ex:owns [ ex:target ex:E101 ; ex:percentage 0.10 ] .

ex:E101 ex:owns [ ex:target ex:E103 ; ex:percentage 0.40 ] .
ex:E102 ex:owns [ ex:target ex:E103 ; ex:percentage 0.30 ] .

ex:P2 ex:owns [ ex:target ex:E104 ; ex:percentage 0.80 ] .
ex:P2 ex:owns [ ex:target ex:E105 ; ex:percentage 0.15 ] .

ex:P3 ex:owns [ ex:target ex:E105 ; ex:percentage 0.50 ] .
"""
    ttl_path.write_text(ttl_content, encoding="utf-8")


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
    pct_val = g.value(o, EX.percentage)

    if target is None:
        raise ValueError(f"Malformed ex:owns triple for subject {s}: missing ex:target in node {o}")
    if pct_val is None:
        raise ValueError(f"Malformed ex:owns triple for subject {s}: missing ex:percentage in node {o}")

    try:
        pct = float(pct_val)
    except (ValueError, TypeError) as e:
        raise ValueError(f"Malformed ex:owns triple for subject {s}: invalid percentage '{pct_val}' in node {o}: {e}")

    if not (0.0 <= pct <= 1.0):
        raise ValueError(f"Malformed ex:owns triple for subject {s}: percentage {pct} out of bounds [0, 1] in node {o}")

    if s in parent_idx and target in sub_idx:
        P[parent_idx[s], sub_idx[target]] += pct
    elif s in sub_idx and target in sub_idx:
        C[sub_idx[s], sub_idx[target]] += pct

# Solve V = P * (I - C)^(-1) with conditioning guard and pseudo-inverse fallback
I = np.eye(N, dtype=np.float64)
matrix_diff = I - C

try:
    cond_num = np.linalg.cond(matrix_diff)
    if cond_num > 1e12:
        print(f"Warning: Matrix (I - C) is ill-conditioned (cond = {cond_num:.2e}). Falling back to pseudo-inverse (pinv).")
        inv_diff = np.linalg.pinv(matrix_diff)
    else:
        inv_diff = np.linalg.inv(matrix_diff)
except np.linalg.LinAlgError as e:
    print(f"Warning: Matrix (I - C) inversion failed ({e}). Falling back to pseudo-inverse (pinv).")
    inv_diff = np.linalg.pinv(matrix_diff)

V = np.matmul(P, inv_diff)

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
    if exempt is not None:
        if hasattr(exempt, "toPython") and isinstance(exempt.toPython(), bool):
            is_exempt = exempt.toPython()
        else:
            is_exempt = str(exempt).lower() in ("true", "1")
    else:
        is_exempt = False

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

report_path = Path("/app/report.json")
report_path.parent.mkdir(parents=True, exist_ok=True)
with open(report_path, "w") as f:
    json.dump(report, f, indent=2)

print(f"Generated {report_path} successfully using Integrated Matrix Inversion.")
