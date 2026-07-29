# Graph Semantic Transitive Ownership

## Overview
This task requires analyzing an RDF Turtle corporate knowledge graph (`/app/data/corporate_graph.ttl`) containing complex parent-subsidiary relationships and circular cross-holdings.

## Approach
- Parse RDF entity nodes and identify top-level parents versus target subsidiaries.
- Formulate the parent-to-subsidiary direct ownership matrix $P$ and subsidiary-to-subsidiary direct ownership matrix $C$.
- Compute the integrated effective ownership matrix $V$ using Brioschi matrix inversion $V = P (I - C)^{-1}$.
- Filter active parent sanctions as of `2026-07-29` and propagate inherited sanction risk to subsidiaries with effective ownership $\ge 0.25$.
- Enforce explicit exemption rules (`ex:exemptFromInheritance true`).
- Format and write sorted entity risk results to `/app/report.json`.

## Environment
- Python 3.13 slim with `rdflib`, `networkx`, `numpy`, `pytest`, and `pytest-json-ctrf`.
- Pre-populated `/app/data/corporate_graph.ttl`.

## Verification
- Automated pytest assertions verify the existence of `/app/report.json`, correctness of matrix calculations (within 0.0001 precision), sorting, sanction categories, total count, and exemption exclusions.
