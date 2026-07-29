An RDF corporate structure graph is stored in Turtle format at `/app/data/corporate_graph.ttl`. Analyze this knowledge graph to evaluate entity risk and effective indirect ownership as of `2026-07-29`.

Write your final output to `/app/report.json`.

1. Parse `/app/data/corporate_graph.ttl`. Extract top-level parent entities (entities with no incoming `ex:owns` relations) and all target subsidiary entities.
2. Calculate the total Effective Ownership percentage for each target subsidiary from all top-level parents:
   - For a directed path of ownership P = (e1 -> e2 -> ... -> ek), the path ownership percentage is the product of individual link percentages (product of percentage(ei, ei+1)).
   - If multiple paths exist between a top parent and a subsidiary, sum the effective ownership percentages across all non-cyclic simple paths.
   - Truncate path traversal if a cycle is encountered; do not re-visit any entity already present in the active traversal path.
3. Determine Inherited Sanctions for each subsidiary:
   - A subsidiary inherits a sanction category from a top-level parent if and only if the total effective ownership from that parent is >= 0.25 (25%) AND the parent has an active sanction in that category as of 2026-07-29 (where 2026-07-29 falls between ex:effectiveDate and ex:expirationDate inclusive).
   - Exception: If a subsidiary entity has the triple `ex:exemptFromInheritance true`, it does not inherit any sanctions regardless of ownership level.
4. Include in `high_risk_subsidiaries` only target subsidiaries where effective_ownership >= 0.25 and inherited_sanctions is non-empty.
5. Format `/app/report.json` strictly as:
   {
     "evaluation_date": "2026-07-29",
     "high_risk_subsidiaries": [
       {
         "entity_id": "http://example.org/entity/E102",
         "entity_name": "Alpha Logistics",
         "effective_ownership": 0.425,
         "inherited_sanctions": ["Financial", "Trade"]
       }
     ],
     "summary": {
       "total_entities_analyzed": 8,
       "flagged_subsidiaries_count": 1
     }
   }
6. Sorting and formatting rules:
   - `high_risk_subsidiaries` must be sorted by `effective_ownership` in descending order. If ownership values match, sort by `entity_id` in ascending ASCII order.
   - `effective_ownership` values must be rounded to 4 decimal places.
   - `inherited_sanctions` arrays must be sorted alphabetically in ascending ASCII order with no duplicate entries.
