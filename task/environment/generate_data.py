import os

ttl_content = """@prefix ex: <http://example.org/entity/> .
@prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .
@prefix xsd: <http://www.w3.org/2001/XMLSchema#> .

# Top-level Parents
ex:P1 a ex:Company ; rdfs:label "Apex Global Holdings" ;
    ex:hasSanction [ ex:category "Financial" ; ex:effectiveDate "2025-01-01" ; ex:expirationDate "2027-12-31" ] ;
    ex:hasSanction [ ex:category "Trade" ; ex:effectiveDate "2024-05-01" ; ex:expirationDate "2026-12-31" ] .

ex:P2 a ex:Company ; rdfs:label "Sovereign Trust" ;
    ex:hasSanction [ ex:category "Defense" ; ex:effectiveDate "2025-06-01" ; ex:expirationDate "2028-01-01" ] .

ex:P3 a ex:Company ; rdfs:label "Clean Energy Inc" .

# Intermediate Entities & Subsidiaries
ex:E101 a ex:Company ; rdfs:label "Alpha Subsidiary" .
ex:E102 a ex:Company ; rdfs:label "Beta Logistics" .
ex:E103 a ex:Company ; rdfs:label "Gamma Shipping" .
ex:E104 a ex:Company ; rdfs:label "Delta Energy Services" ; ex:exemptFromInheritance true .
ex:E105 a ex:Company ; rdfs:label "Epsilon Maritime" .

# Holdings Graph with Circular Cross-Holding (E101 <-> E102)
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

os.makedirs("/app/data", exist_ok=True)
with open("/app/data/corporate_graph.ttl", "w") as f:
    f.write(ttl_content)

print("Generated /app/data/corporate_graph.ttl successfully.")
