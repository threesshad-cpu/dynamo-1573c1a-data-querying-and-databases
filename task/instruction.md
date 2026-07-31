An RDF corporate structure graph is stored in Turtle format at `/app/data/corporate_graph.ttl`. Analyze this knowledge graph to evaluate entity risk and integrated effective ownership as of `2026-07-29`.

Write your final output to `/app/report.json`.

### Requirements & Mathematical Model

1. **Entity Extraction:**
   - Parse `/app/data/corporate_graph.ttl`.
   - Identify top-level parent entities (entities with no incoming `ex:owns` relations) and target subsidiary entities.

2. **Integrated Effective Ownership Calculation:**
   - Top-level parent entities are entities with no incoming `ex:owns` relations. Target entities are subsidiary entities.
   - Calculate the **integrated effective ownership** percentage for each top-level parent entity in each target subsidiary entity, accounting for both direct ownership relations and indirect ownership passed through corporate cross-holdings and ownership cycles.
   - Direct holdings are specified via `ex:owns` triples containing `ex:target` and `ex:percentage`.
   - Integrated effective ownership must account for all transitive holding chains and circular cross-holdings between entities (where an entity's integrated effective ownership in a subsidiary combines direct ownership and indirect holdings through intermediate companies).
   - The total effective ownership of a target subsidiary is the sum of integrated effective ownerships held across all top-level parent entities.

3. **Inherited Sanctions & Exemption Rules:**
   - A subsidiary inherits a sanction category from a top-level parent $p$ if and only if the integrated effective ownership $V_{p,j} \ge 0.25$ (25%) AND parent $p$ has an active sanction in that category as of `2026-07-29` (where `2026-07-29` falls between `ex:effectiveDate` and `ex:expirationDate` inclusive).
   - **Exemption Rule:** If a subsidiary entity has the triple `ex:exemptFromInheritance true`, it does not inherit any sanctions regardless of ownership level and must be excluded from high-risk flagging.

4. **Filtering and Report Generation:**
   - Include in `high_risk_subsidiaries` only target subsidiaries where total effective ownership $\ge 0.25$ and `inherited_sanctions` is non-empty.

5. **JSON Output Schema (`/app/report.json`):**
   ```json
   {
     "evaluation_date": "2026-07-29",
     "high_risk_subsidiaries": [
       {
         "entity_id": "http://example.org/entity/E101",
         "entity_name": "Alpha Subsidiary",
         "effective_ownership": 0.6526,
         "inherited_sanctions": ["Financial", "Trade"]
       }
     ],
     "summary": {
       "total_entities_analyzed": 8,
       "flagged_subsidiaries_count": 1
     }
   }
   ```

6. **Sorting and Formatting Rules:**
   - `high_risk_subsidiaries` must be sorted by `effective_ownership` in descending order. If values match, sort by `entity_id` in ascending ASCII order.
   - `effective_ownership` values must be rounded to 4 decimal places.
   - `inherited_sanctions` arrays must be sorted alphabetically in ascending ASCII order with no duplicate entries.
