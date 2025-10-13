import numpy as np

rank_hierarchy = {
    "superkingdom": 0.5,
    "kingdom": 1,
    "subkingdom": 1.5,
    "phylum": 2,
    "subphylum": 2.5,
    "class": 3,
    "subclass": 3.5,
    "order": 4,
    "suborder": 4.5,
    "superfamily": 4.75,
    "family": 5,
    "subfamily": 5.5,
    "genus": 6,
    "subgenus": 6.5,
    "section": 6.7,
    "species group": 6.8, 
    "species": 7,
    "subspecies": 7.5,
    "strain": 8,
}

anchor_ranks = {"tribe", "forma", "clade", "no rank"}

def add_root_node(tax_parent_map, tax_children_map, tax_2_rank_string_map, tax_2_normalised_rank_value_map, filtered_rank_abundances_dict, verbose = False):
    """
    Add a "root" node to the taxonomy maps and make it the parent of all nodes
    that don't have a parent in the dataset.
    
    Args:
        tax_parent_map: Dictionary mapping tax IDs to their parent tax IDs
        tax_children_map: Dictionary mapping tax IDs to lists of their child tax IDs
        tax_2_rank_string_map: Dictionary mapping tax IDs to their rank strings
        tax_2_normalised_rank_value_map: Dictionary mapping tax IDs to their normalized rank values
        filtered_rank_abundances_dict: Dictionary with rank-based abundance data
    
    Returns:
        Updated versions of all input dictionaries
    """
    # Create a special root node ID
    root_id = "root"
    
    # Get all taxa IDs from filtered_rank_abundances_dict
    all_taxa = set()
    for rank, taxa_dict in filtered_rank_abundances_dict.items():
        all_taxa.update(taxa_dict.keys())
    
    # Add root node to the rank maps with the lowest possible rank value
    tax_2_rank_string_map[root_id] = "root"
    
    # Set the root's normalized rank value to be lower than any existing value
    min_rank_value = min(tax_2_normalised_rank_value_map.values(), default=0)
    tax_2_normalised_rank_value_map[root_id] = min_rank_value - 0.1  # Place it below all others
    
    # Initialize root's children list
    tax_children_map[root_id] = []
    
    # Find all nodes without parents in the dataset
    orphan_nodes = []
    for taxid in all_taxa:
        if taxid not in tax_parent_map or tax_parent_map[taxid] not in all_taxa:
            orphan_nodes.append(taxid)
    if verbose:
        print(f"Found {len(orphan_nodes)} nodes without parents in the dataset")
    
    # Make the root node the parent of all orphan nodes
    for taxid in orphan_nodes:
        tax_parent_map[taxid] = root_id
        tax_children_map[root_id].append(taxid)
    
    # Add the root node to filtered_rank_abundances_dict
    if "root" not in filtered_rank_abundances_dict:
        filtered_rank_abundances_dict["root"] = {}
    filtered_rank_abundances_dict["root"][root_id] = 0  # Assign zero abundance
    
    return tax_parent_map, tax_children_map, tax_2_rank_string_map, tax_2_normalised_rank_value_map, filtered_rank_abundances_dict

def normalise_rank_hierarchy(rank_hierarchy, min_val=0, max_val=1, verbose = False):
    values = list(rank_hierarchy.values())
    current_min = 0
    current_max = max(values)
    
    # avoid division by zero if all values are the same
    if current_max == current_min:
        return {k: min_val for k in rank_hierarchy}
    
    normalised_dict = {}
    range_size = max_val - min_val
    
    # apply min-max normalisation
    for rank, value in rank_hierarchy.items():
        normalised_value = min_val + range_size * (value - current_min) / (current_max - current_min)
        normalised_dict[rank] = normalised_value
        
    return normalised_dict

def calculate_anchor_point(tax_id, tax_rank_map, tax_parent_map, tax_children_map, normalised_rank_hierarchy, verbose = False):
    # if the taxon already has a defined rank, return it
    if tax_rank_map[tax_id].lower() in normalised_rank_hierarchy:
        return normalised_rank_hierarchy[tax_rank_map[tax_id].lower()]
    
    # find closest parent with a defined rank
    parent_rank_value = None
    closest_parent_id = None
    current_id = tax_id
    
    while current_id in tax_parent_map:
        parent_id = tax_parent_map[current_id]
        parent_rank = tax_rank_map.get(parent_id, "").lower()
        if parent_rank in normalised_rank_hierarchy:
            parent_rank_value = normalised_rank_hierarchy[parent_rank]
            closest_parent_id = parent_id
            break
        current_id = parent_id
    
    # default parent value if no parent with defined rank is found
    if parent_rank_value is None:
        parent_rank_value = 0  # Start of hierarchy
        # Find the root node (node with no parent)
        root_id = tax_id
        while root_id in tax_parent_map:
            root_id = tax_parent_map[root_id]
        closest_parent_id = root_id
    
    # find closest child with a defined rank using queue for breadth-first search
    child_rank_value = None
    closest_child_id = None
    queue = []
    visited = set()
    
    # add immediate children to queue
    if tax_id in tax_children_map:
        for child_id in tax_children_map[tax_id]:
            queue.append(child_id)
            visited.add(child_id)
    
    # process queue until we find a child with defined rank
    while queue and child_rank_value is None:
        current_child = queue.pop(0)
        child_rank = tax_rank_map.get(current_child, "").lower()
        
        if child_rank in normalised_rank_hierarchy:
            child_rank_value = normalised_rank_hierarchy[child_rank]
            closest_child_id = current_child
            break
            
        # add this child's children to the queue
        if current_child in tax_children_map:
            for next_child in tax_children_map[current_child]:
                if next_child not in visited:
                    queue.append(next_child)
                    visited.add(next_child)
    
    # if no child with defined rank is found, use max rank value
    max_rank_value = max(normalised_rank_hierarchy.values())
    if child_rank_value is None:
        child_rank_value = max_rank_value
        closest_child_id = None  # No suitable child found
    
    # Update parent-child relationships
    if closest_parent_id is not None:
        # Update the parent map to include this taxon's parent
        tax_parent_map[tax_id] = closest_parent_id
        
        # Update the children map to include this taxon as a child of the parent
        if closest_parent_id not in tax_children_map:
            tax_children_map[closest_parent_id] = []
        if tax_id not in tax_children_map[closest_parent_id]:
            tax_children_map[closest_parent_id].append(tax_id)
    
    # If a closest child was found, update the relationships
    if closest_child_id is not None:
        # Update the parent map to set this taxon as the parent of the child
        tax_parent_map[closest_child_id] = tax_id
        
        # Update the children map to include the child in this taxon's children
        if tax_id not in tax_children_map:
            tax_children_map[tax_id] = []
        if closest_child_id not in tax_children_map[tax_id]:
            tax_children_map[tax_id].append(closest_child_id)
    if verbose:
        print(f"Anchor taxa={tax_id}, parent={closest_parent_id}, child={closest_child_id}")
    
    # return the average of parent and child rank values
    return (parent_rank_value + child_rank_value) / 2, tax_parent_map, tax_children_map

def create_filtered_rank_abundances_dict(ncbi_taxonomy, df_ids, verbose = False):
    rank_abundances_dict = {}
    tax_parent_map = {}
    tax_children_map = {}
    tax_2_rank_string_map = {}
    tax_2_normalised_rank_value_map = {}

    # anchor points to create numbers for
    anchor_point_ranks = {"tribe", "forma", "clade", "no rank"}

    # define all ranks in our dataset
    all_ranks_in_data = set(item.get('TaxRank', '').lower() for item in ncbi_taxonomy)
    if verbose:
        print(f"All ranks in ncbi_taxonomy: {all_ranks_in_data}")

    # create a dictionary of taxon IDs and their parent IDs
    for item in ncbi_taxonomy:
        rank = item.get('TaxRank', '').lower() if item.get('TaxRank') else "no rank"
        tax_id = item['TaxID']
        parent_id = item.get('ParentTaxID')

        tax_2_rank_string_map[tax_id] = rank

        if rank not in rank_abundances_dict:
            rank_abundances_dict[rank] = {}
        rank_abundances_dict[rank][tax_id] = 0

        if parent_id:
            tax_parent_map[tax_id] = parent_id
            if parent_id not in tax_children_map:
                tax_children_map[parent_id] = []
            tax_children_map[parent_id].append(tax_id)
            
    # create a set of all relevant taxa
    all_relevant_taxa = set()
    parent_taxa = set()

    if verbose:
        print(f"Number of IDs in df_ids: {len(df_ids)}")

    # add all relevant taxa and their parents to the set
    for tax_id in df_ids:
        all_relevant_taxa.add(tax_id)
        current_id = tax_id
        while current_id in tax_parent_map:
            parent_id = tax_parent_map[current_id]
            all_relevant_taxa.add(parent_id)
            parent_taxa.add(parent_id)
            current_id = parent_id
    if verbose:
        print(f"Total relevant taxa including parents: {len(all_relevant_taxa)}")

    # add missing ranks to the rank dictionary
    missing_ranks = set()
    for tax_id in parent_taxa:
        if tax_id in tax_2_rank_string_map:
            rank = tax_2_rank_string_map[tax_id].lower()
            if rank not in rank_abundances_dict:
                rank_abundances_dict[rank] = {}
                if verbose:
                    print(f"Added missing rank: {rank}")
            if tax_id not in rank_abundances_dict[rank]:
                rank_abundances_dict[rank][tax_id] = 0
        else:
            missing_ranks.add(tax_id)
            tax_2_rank_string_map[tax_id] = "no rank"
            if "no rank" not in rank_abundances_dict:
                rank_abundances_dict["no rank"] = {}
            rank_abundances_dict["no rank"][tax_id] = 0
            if verbose:
                print(f"Added tax_id {tax_id} as 'no rank'")
    
    if missing_ranks:
        if verbose:
            print(f"Could not find ranks for {len(missing_ranks)} taxa")
    
    # add all IDs to the rank dictionary
    for tax_id in df_ids:
        found = False
        for rank, id_dict in rank_abundances_dict.items():
            if tax_id in id_dict:
                id_dict[tax_id] += 1
                found = True
        if not found:
            if verbose:
                print(f"Warning: Tax ID {tax_id} not found in any rank dictionary")

    # filter out *ranks* with no IDs
    if verbose:
        print(f"Ranks before filtering: {list(rank_abundances_dict.keys())}")
    filtered_rank_abundances_dict = {}
    for rank, id_dict in rank_abundances_dict.items():
        filtered_ids = {}
        for tax_id, count in id_dict.items():
            if count > 0 or tax_id in all_relevant_taxa:
                filtered_ids[tax_id] = count
        if filtered_ids:
            filtered_rank_abundances_dict[rank] = filtered_ids
    if verbose:
        print(f"Ranks after filtering: {list(filtered_rank_abundances_dict.keys())}")

    # sort ranks by hierarchy
    sorted_ranks = sorted(
        [rank for rank in filtered_rank_abundances_dict.keys()],
        key=lambda r: tax_2_normalised_rank_value_map.get(r, 999)
    )
    if verbose:
        print(f"Sorted ranks for aggregation: {sorted_ranks}")

    # aggregate counts from children to parents
    for i in range(len(sorted_ranks) - 1, 0, -1):
        current_rank = sorted_ranks[i]
        for tax_id, count in list(filtered_rank_abundances_dict[current_rank].items()):
            if tax_id in tax_parent_map:
                parent_id = tax_parent_map[tax_id]
                parent_rank = tax_2_rank_string_map.get(parent_id, "").lower()
                if parent_id not in all_relevant_taxa:
                    if verbose:
                        print(f"Warning: Parent {parent_id} of {tax_id} not in relevant taxa")
                parent_found = False
                for rank, id_dict in filtered_rank_abundances_dict.items():
                    if parent_id in id_dict:
                        children_counts = len(tax_children_map.get(parent_id, []))
                        if children_counts == 0:
                            children_counts = 1
                        child_weight = count / children_counts
                        id_dict[parent_id] += child_weight
                        parent_found = True
                        break
                if not parent_found and parent_rank:
                    if verbose:
                        print(f"Parent {parent_id} (rank: {parent_rank}) of {tax_id} not found in filtered_rank_dict")
    
    # print number of taxa in each rank
    for rank, id_dict in filtered_rank_abundances_dict.items():
        if verbose:
            print(f"Rank '{rank}' has {len(id_dict)} taxa with non-zero counts")

    # normalised distances to use for visualisation
    normalised_rank_hierarchy = normalise_rank_hierarchy(rank_hierarchy, verbose = verbose)
    
    # init normalized rank values for standard ranks
    for tax_id in tax_2_rank_string_map:
        rank = tax_2_rank_string_map[tax_id].lower()
        if rank in normalised_rank_hierarchy:
            tax_2_normalised_rank_value_map[tax_id] = normalised_rank_hierarchy[rank]
    
    # add root node to handle orphan nodes
    tax_parent_map, tax_children_map, tax_2_rank_string_map, tax_2_normalised_rank_value_map, filtered_rank_abundances_dict = add_root_node(
        tax_parent_map, tax_children_map, tax_2_rank_string_map, tax_2_normalised_rank_value_map, filtered_rank_abundances_dict, verbose = verbose
    )
    
    # calculate anchor points for special ranks
    for tax_id in tax_2_rank_string_map:
        rank = tax_2_rank_string_map[tax_id].lower()
        if rank in anchor_point_ranks and tax_id not in tax_2_normalised_rank_value_map:
            if verbose:
                print(f"Calculating anchor point for taxon {tax_id} which is a {tax_2_rank_string_map[tax_id]}")
            anchor_value, tax_parent_map, tax_children_map = calculate_anchor_point(
                tax_id, tax_2_rank_string_map, tax_parent_map, tax_children_map, normalised_rank_hierarchy, verbose = verbose
            )
            tax_2_normalised_rank_value_map[tax_id] = anchor_value

    return filtered_rank_abundances_dict, tax_parent_map, tax_children_map, tax_2_rank_string_map, tax_2_normalised_rank_value_map


def create_qvalue_dict(filtered_rank_abundances_dict, results_df, verbose = False):
    filtered_rank_dict_qvalues = dict()
    for rank, tax_dicts in filtered_rank_abundances_dict.items():
        filtered_rank_dict_qvalues[rank] = dict()
        for tax_id, count in tax_dicts.items():
            q_value = results_df[rank][tax_id]['q_value']
            # this prevents inf values
            if q_value == 0:
                q_value = 1/100000 # since max is 1/100000 samples
            filtered_rank_dict_qvalues[rank][tax_id] = -np.log10(q_value)
    return filtered_rank_dict_qvalues
