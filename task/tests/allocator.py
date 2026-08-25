import math

def allocate_leaf_requirements(db, remaining, inv_snapshot, inv_consumed):
    # remaining: {leaf_id: units_still_needed}
    # we need to find an allocation of substitutes that satisfies 'remaining'
    # returns True and mutates inv_consumed, or False
    
    if all(v == 0 for v in remaining.values()):
        return True
        
    leaves = sorted([leaf for leaf, rem in remaining.items() if rem > 0])
    
    # Precompute possible choices for each leaf
    leaf_choices = {}
    for leaf in leaves:
        choices = []
        if leaf in db.substitutes:
            for sub_id, ratio, rank in db.substitutes[leaf]:
                avail = inv_snapshot.get(sub_id, 0) - inv_consumed.get(sub_id, 0)
                choices.append((sub_id, ratio, rank, avail))
        leaf_choices[leaf] = choices

    valid_allocations = []
    
    def search(leaf_idx, current_alloc, current_inv):
        if leaf_idx == len(leaves):
            valid_allocations.append(list(current_alloc))
            return
            
        leaf = leaves[leaf_idx]
        rem = remaining[leaf]
        
        # We need to fulfill 'rem' using a combination of substitutes.
        # Since a leaf can use multiple substitutes, we need to partition 'rem' across available subs.
        # To make exhaustive search simple, we can recursively assign units from each substitute.
        subs = leaf_choices[leaf]
        
        def partition_rem(sub_idx, rem_to_fill, sub_alloc, temp_inv):
            if rem_to_fill == 0:
                search(leaf_idx + 1, current_alloc + sub_alloc, temp_inv)
                return
            if sub_idx == len(subs):
                return # failed to fill
                
            sub_id, ratio, rank, _ = subs[sub_idx]
            avail_sub = temp_inv.get(sub_id, 0)
            max_primary_units = min(rem_to_fill, math.floor(avail_sub / ratio))
            
            for units in range(max_primary_units, -1, -1):
                next_inv = dict(temp_inv)
                next_inv[sub_id] -= units * ratio
                next_alloc = list(sub_alloc)
                if units > 0:
                    next_alloc.append((leaf, sub_id, units, rank))
                partition_rem(sub_idx + 1, rem_to_fill - units, next_alloc, next_inv)
                
        partition_rem(0, rem, [], current_inv)

    temp_inv = {p: inv_snapshot.get(p, 0) - inv_consumed.get(p, 0) for p in db.parts}
    search(0, [], temp_inv)
    
    if not valid_allocations:
        return False
        
    # We have valid full allocations. We must pick the one that:
    # 1. Minimizes total preference rank usage.
    # 2. Tie-break: lexicographically smallest primary-part allocation.
    
    def score_alloc(alloc):
        # alloc is a list of (leaf_id, sub_id, units, rank)
        total_rank = sum(units * rank for leaf, sub, units, rank in alloc)
        
        # To match "prefer lexicographically smallest primary-part allocation",
        # and favor concentrating the allocation greedily on the best substitutes,
        # we construct a tuple sorted by (rank, sub, leaf), with -units so that
        # larger unit allocations are considered mathematically smaller (better).
        alloc_tuple = tuple(sorted([
            (rank, sub, leaf, -units) 
            for leaf, sub, units, rank in alloc if units > 0
        ]))
        
        return (total_rank, alloc_tuple)
        
    best_alloc = min(valid_allocations, key=score_alloc)
    
    # Apply best_alloc to inv_consumed
    for leaf, sub, units, rank in best_alloc:
        ratio = next(r for s, r, rnk in db.substitutes[leaf] if s == sub)
        inv_consumed[sub] += units * ratio
        
    return True
