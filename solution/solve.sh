#!/usr/bin/env bash
set -euo pipefail

python3 - << 'PYEOF'
import json
from rdflib import Graph, Namespace, RDF, RDFS

g = Graph()
g.parse("/app/data/corporate_graph.ttl", format="turtle")

EX = Namespace("http://example.org/entity/")

all_entities = set()
for s in g.subjects(RDF.type, EX.Company):
    all_entities.add(s)

raw_edges = {}
has_incoming = set()

for s, p, o in g.triples((None, EX.owns, None)):
    target = g.value(o, EX.target)
    pct = float(g.value(o, EX.percentage))
    if s not in raw_edges:
        raw_edges[s] = []
    raw_edges[s].append((target, pct))
    has_incoming.add(target)

# Prune cross-holding back-edges (where u->v and v->u exist, keep the dominant edge u->v)
edges = {}
for s, targets in raw_edges.items():
    edges[s] = []
    for target, pct in targets:
        # Check if reciprocal edge exists with higher percentage
        reciprocal_pct = 0.0
        if target in raw_edges:
            for r_target, r_pct in raw_edges[target]:
                if r_target == s:
                    reciprocal_pct = r_pct
                    break
        if reciprocal_pct > 0 and pct < reciprocal_pct:
            continue  # prune minority cross-holding back-edge
        edges[s].append((target, pct))

top_parents = [e for e in all_entities if e not in has_incoming]

def get_effective_ownership(parent, target):
    paths = []
    def dfs(curr, target_node, current_path, current_pct):
        if curr == target_node:
            paths.append(current_pct)
            return
        if curr not in edges:
            return
        for nxt, pct in edges[curr]:
            if nxt not in current_path:
                dfs(nxt, target_node, current_path + [nxt], current_pct * pct)

    dfs(parent, target, [parent], 1.0)
    return sum(paths)

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
subsidiaries = [e for e in all_entities if e not in top_parents]

for sub in subsidiaries:
    exempt = g.value(sub, EX.exemptFromInheritance)
    is_exempt = str(exempt).lower() == "true" if exempt else False
    
    label = str(g.value(sub, RDFS.label) or sub)
    total_effective_ownership = 0.0
    inherited_sanctions = set()
    
    for p in top_parents:
        eff_own = get_effective_ownership(p, sub)
        total_effective_ownership += eff_own
        if eff_own >= 0.25 and not is_exempt:
            inherited_sanctions.update(parent_sanctions.get(p, []))
            
    if total_effective_ownership >= 0.25 and len(inherited_sanctions) > 0:
        high_risk.append({
            "entity_id": str(sub),
            "entity_name": label,
            "effective_ownership": round(total_effective_ownership, 4),
            "inherited_sanctions": sorted(list(inherited_sanctions))
        })

high_risk.sort(key=lambda x: (-x["effective_ownership"], x["entity_id"]))

report = {
    "evaluation_date": eval_date,
    "high_risk_subsidiaries": high_risk,
    "summary": {
        "total_entities_analyzed": len(all_entities),
        "flagged_subsidiaries_count": len(high_risk)
    }
}

with open("/app/report.json", "w") as f:
    json.dump(report, f, indent=2)

print("Generated /app/report.json successfully.")
PYEOF
