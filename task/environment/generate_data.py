from pathlib import Path


ttl_content = """@prefix ex: <http://example.org/entity/> .
@prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .
@prefix xsd: <http://www.w3.org/2001/XMLSchema#> .

# Top-level parents
ex:P1 a ex:Company ; rdfs:label "Apex Global Holdings" ;
    ex:hasSanction [ ex:category "Financial" ; ex:effectiveDate "2025-01-01" ; ex:expirationDate "2027-12-31" ] ;
    ex:hasSanction [ ex:category "Trade" ; ex:effectiveDate "2024-05-01" ; ex:expirationDate "2026-07-29" ] ;
    ex:hasSanction [ ex:category "Legacy" ; ex:effectiveDate "2024-01-01" ; ex:expirationDate "2026-07-28" ] .

ex:P2 a ex:Company ; rdfs:label "Sovereign Trust" ;
    ex:hasSanction [ ex:category "Defense" ; ex:effectiveDate "2025-06-01" ; ex:expirationDate "2028-01-01" ] .

ex:P3 a ex:Company ; rdfs:label "Clean Energy Inc" ;
    ex:hasSanction [ ex:category "Environmental" ; ex:effectiveDate "2026-07-29" ; ex:expirationDate "2026-12-31" ] .

# Corporate entities: 17 subsidiaries, intentionally arranged as overlapping cycles,
# deep chains, and converging parallel paths.
ex:E101 a ex:Company ; rdfs:label "Alpha Subsidiary" .
ex:E102 a ex:Company ; rdfs:label "Beta Logistics" .
ex:E103 a ex:Company ; rdfs:label "Gamma Shipping" .
ex:E104 a ex:Company ; rdfs:label "Delta Energy Services" ; ex:exemptFromInheritance true .
ex:E105 a ex:Company ; rdfs:label "Epsilon Maritime" .
ex:E106 a ex:Company ; rdfs:label "Zeta Components" .
ex:E107 a ex:Company ; rdfs:label "Eta Infrastructure" .
ex:E108 a ex:Company ; rdfs:label "Theta Networks" .
ex:E109 a ex:Company ; rdfs:label "Iota Trading" .
ex:E110 a ex:Company ; rdfs:label "Kappa Materials" .
ex:E111 a ex:Company ; rdfs:label "Lambda Systems" .
ex:E112 a ex:Company ; rdfs:label "Mu Analytics" .
ex:E113 a ex:Company ; rdfs:label "Nu Services" .
ex:E114 a ex:Company ; rdfs:label "Xi Distribution" .
ex:E115 a ex:Company ; rdfs:label "Omicron Ventures" .
ex:E116 a ex:Company ; rdfs:label "Pi Manufacturing" .
ex:E117 a ex:Company ; rdfs:label "Rho Terminal" .

# Parent entry points
ex:P1 ex:owns [ ex:target ex:E101 ; ex:percentage 0.42 ] .
ex:P1 ex:owns [ ex:target ex:E104 ; ex:percentage 0.18 ] .
ex:P1 ex:owns [ ex:target ex:E109 ; ex:percentage 0.16 ] .

ex:P2 ex:owns [ ex:target ex:E103 ; ex:percentage 0.38 ] .
ex:P2 ex:owns [ ex:target ex:E107 ; ex:percentage 0.30 ] .
ex:P2 ex:owns [ ex:target ex:E112 ; ex:percentage 0.12 ] .

ex:P3 ex:owns [ ex:target ex:E105 ; ex:percentage 0.28 ] .
ex:P3 ex:owns [ ex:target ex:E110 ; ex:percentage 0.22 ] .
ex:P3 ex:owns [ ex:target ex:E115 ; ex:percentage 0.20 ] .

# Overlapping 3-node cycle
ex:E101 ex:owns [ ex:target ex:E102 ; ex:percentage 0.18 ] .
ex:E102 ex:owns [ ex:target ex:E103 ; ex:percentage 0.22 ] .
ex:E103 ex:owns [ ex:target ex:E101 ; ex:percentage 0.15 ] .

# Intersecting 4-node cycle
ex:E104 ex:owns [ ex:target ex:E105 ; ex:percentage 0.25 ] .
ex:E105 ex:owns [ ex:target ex:E106 ; ex:percentage 0.20 ] .
ex:E106 ex:owns [ ex:target ex:E107 ; ex:percentage 0.30 ] .
ex:E107 ex:owns [ ex:target ex:E104 ; ex:percentage 0.12 ] .

# Intersecting 5-node cycle
ex:E107 ex:owns [ ex:target ex:E108 ; ex:percentage 0.18 ] .
ex:E108 ex:owns [ ex:target ex:E109 ; ex:percentage 0.24 ] .
ex:E109 ex:owns [ ex:target ex:E110 ; ex:percentage 0.16 ] .
ex:E110 ex:owns [ ex:target ex:E111 ; ex:percentage 0.20 ] .
ex:E111 ex:owns [ ex:target ex:E107 ; ex:percentage 0.10 ] .

# Parallel paths and deeper transitive chains
ex:E102 ex:owns [ ex:target ex:E108 ; ex:percentage 0.14 ] .
ex:E103 ex:owns [ ex:target ex:E108 ; ex:percentage 0.11 ] .
ex:E104 ex:owns [ ex:target ex:E109 ; ex:percentage 0.13 ] .
ex:E106 ex:owns [ ex:target ex:E109 ; ex:percentage 0.17 ] .
ex:E109 ex:owns [ ex:target ex:E112 ; ex:percentage 0.30 ] .
ex:E110 ex:owns [ ex:target ex:E112 ; ex:percentage 0.18 ] .
ex:E108 ex:owns [ ex:target ex:E113 ; ex:percentage 0.12 ] .
ex:E112 ex:owns [ ex:target ex:E113 ; ex:percentage 0.35 ] .
ex:E113 ex:owns [ ex:target ex:E114 ; ex:percentage 0.30 ] .
ex:E111 ex:owns [ ex:target ex:E114 ; ex:percentage 0.14 ] .
ex:E114 ex:owns [ ex:target ex:E115 ; ex:percentage 0.25 ] .
ex:E115 ex:owns [ ex:target ex:E116 ; ex:percentage 0.24 ] .
ex:E113 ex:owns [ ex:target ex:E116 ; ex:percentage 0.08 ] .
ex:E114 ex:owns [ ex:target ex:E117 ; ex:percentage 0.26 ] .
ex:E116 ex:owns [ ex:target ex:E117 ; ex:percentage 0.20 ] .
"""

ttl_path = Path("/app/data/corporate_graph.ttl")
alt_paths = [
    Path("/tmp/corporate_graph.ttl"),
    Path("/data/corporate_graph.ttl"),
    Path(__file__).resolve().parent.parent / "data" / "corporate_graph.ttl",
    ttl_path,
]

for p in alt_paths:
    try:
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(ttl_content, encoding="utf-8")
        print(f"Generated {p} successfully.")
    except Exception as e:
        print(f"Note: Could not write to {p}: {e}")
