import numpy as np
from collections import defaultdict
import matplotlib.pyplot as plt
from matplotlib.colors import LinearSegmentedColormap
from matplotlib.lines import Line2D
from matplotlib.collections import LineCollection
import matplotlib.patches as mpatches

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
from microbELP.rank_counts import create_filtered_rank_abundances_dict
from microbELP.master_positions_handler import ensure_parent_relationships
from microbELP.master_positions_handler import create_abundance_legend
from microbELP.master_positions_handler import generate_master_positions

def plot_study_dataset_on_tree(
    base_tree_data, study_data, master_positions=None, 
    tax_name_map=None, figsize=(12, 12), output_file=None, 
    node_size=30, edge_width=1.5, surface_text=None,
    surface_text_size=10, abundance_threshold=None, verbose = False):
    """Plot a study dataset on an existing phylogenetic tree structure.
    
    Args:
        base_tree_data: Tuple containing base tree data (filtered_rank_abundances_dict, tax_parent_map, 
                      tax_children_map, tax_2_rank_string_map, tax_2_normalised_rank_value_map)
        study_data: Tuple containing study data in the same format as base_tree_data
        master_positions: Dictionary mapping tax IDs to their master positions
        tax_name_map: Optional dictionary mapping tax IDs to their names
        figsize: Size of the figure as a tuple (width, height)
        output_file: Optional file path to save the visualisation
        node_size: Size of the nodes
        edge_width: Width of the edges
        surface_text: Optional text to display below the tree
        surface_text_size: Size of the surface text
        abundance_threshold: Threshold for considering nodes as having high abundance
        
    Returns:
        Tuple containing (fig, ax) for further customisation
    """
    # Unpack data
    base_filtered_rank_dict, base_tax_parent_map, base_tax_children_map, \
        base_tax_2_rank_string_map, base_tax_2_normalised_rank_value_map = base_tree_data
    
    study_filtered_rank_dict, study_tax_parent_map, study_tax_children_map, \
        study_tax_2_rank_string_map, study_tax_2_normalised_rank_value_map = study_data
    
    # Set up figure
    fig, ax = plt.subplots(figsize=figsize)
    ax.set_aspect('equal')
    
    if tax_name_map is None:
        tax_name_map = {}
    
    # Define anchor ranks that should have grey nodes
    anchor_ranks = {"tribe", "forma", "clade", "no rank", "root"}
    
    # Get all taxa IDs from both datasets
    base_taxa = set()
    for rank, taxa_dict in base_filtered_rank_dict.items():
        base_taxa.update(taxa_dict.keys())
    
    study_taxa = set()
    for rank, taxa_dict in study_filtered_rank_dict.items():
        study_taxa.update(taxa_dict.keys())
    
    # Create combined set of all taxa
    all_taxa = base_taxa.union(study_taxa)
    
    # Create node positions dictionary using master positions
    node_positions = {}
    
    # If no master positions are provided, generate from base tree
    if master_positions is None:
        if verbose:
            print("Generating master positions from base tree")
        master_positions = generate_master_positions(base_tree_data)
    
    # Use positions for taxa that exist in master positions
    for taxid in all_taxa:
        if taxid in master_positions:
            node_positions[taxid] = master_positions[taxid].copy()
    
    # For taxa not in master positions, create new positions
    missing_taxa = all_taxa - set(node_positions.keys())
    if missing_taxa:
        if verbose:
            print(f"Warning: {len(missing_taxa)} taxa not found in master positions, assigning new positions")
        
        # Combine parent maps from both datasets
        combined_parent_map = {**base_tax_parent_map, **study_tax_parent_map}
        
        # Assign positions based on parent's position if possible
        for taxid in missing_taxa:
            if taxid in combined_parent_map and combined_parent_map[taxid] in node_positions:
                parent_id = combined_parent_map[taxid]
                parent_pos = node_positions[parent_id]
                
                # Get rank value from appropriate dataset
                if taxid in study_tax_2_normalised_rank_value_map:
                    rank_value = study_tax_2_normalised_rank_value_map[taxid]
                elif taxid in base_tax_2_normalised_rank_value_map:
                    rank_value = base_tax_2_normalised_rank_value_map[taxid]
                else:
                    rank_value = parent_pos['radius'] + 0.1
                
                # Assign position slightly offset from parent
                angle = parent_pos['angle'] + 0.1  # Small offset
                node_positions[taxid] = {
                    'angle': angle,
                    'radius': rank_value,
                    'x': rank_value * np.cos(angle),
                    'y': rank_value * np.sin(angle)
                }
    
    # Ensure all nodes have parent relationships for edge drawing
    # Combine parent and children maps
    combined_parent_map = {**base_tax_parent_map, **study_tax_parent_map}
    combined_children_map = defaultdict(list)
    
    # Populate combined children map
    for child, parent in combined_parent_map.items():
        if parent not in combined_children_map:
            combined_children_map[parent] = []
        if child not in combined_children_map[parent]:
            combined_children_map[parent].append(child)
    
    # Combine rank abundance dicts
    combined_rank_dict = defaultdict(dict)
    for rank, taxa_dict in base_filtered_rank_dict.items():
        for taxid, abundance in taxa_dict.items():
            combined_rank_dict[rank][taxid] = abundance
    
    for rank, taxa_dict in study_filtered_rank_dict.items():
        for taxid, abundance in taxa_dict.items():
            combined_rank_dict[rank][taxid] = abundance
    
    # Ensure parent relationships
    ensure_parent_relationships(
        node_positions, 
        combined_parent_map, 
        dict(combined_children_map), 
        dict(combined_rank_dict),
        verbose = verbose
    )
    
    # Get all ranks present in our data
    combined_rank_string_map = {**base_tax_2_rank_string_map, **study_tax_2_rank_string_map}
    unique_ranks = set(combined_rank_string_map.values())
    data_ranks = {rank.lower() for rank in unique_ranks}
    
    # Create an ordered list of ranks based on hierarchy
    ordered_ranks = []
    
    # Add standard ranks first, in hierarchy order
    for rank in sorted(rank_hierarchy.keys(), key=lambda r: rank_hierarchy[r]):
        if rank in data_ranks and rank not in anchor_ranks:
            # Find the corresponding rank from unique_ranks with correct capitalization
            matching_ranks = [r for r in unique_ranks if r.lower() == rank]
            if matching_ranks:
                ordered_ranks.extend(matching_ranks)
    
    # Setup for colouring by rank
    cmap = plt.cm.viridis
    
    # Create a mapping of ranks to colours
    rank_colours = {}
    
    # Assign colours from the colourmap to standard ranks
    if ordered_ranks:
        for i, rank in enumerate(ordered_ranks):
            # Normalise i to be between 0 and 1
            normalized_i = i / (len(ordered_ranks) - 1) if len(ordered_ranks) > 1 else 0
            rank_colours[rank] = cmap(normalized_i)
    
    # Add grey colour for anchor ranks
    for rank in unique_ranks:
        if rank.lower() in anchor_ranks:
            rank_colours[rank] = 'grey'
    
    # Get abundances from study dataset
    study_taxon_abundances = {}
    all_study_abundances = []
    
    for rank, taxa_dict in study_filtered_rank_dict.items():
        for taxid, abundance in taxa_dict.items():
            if taxid in all_taxa:
                study_taxon_abundances[taxid] = abundance
                all_study_abundances.append(abundance)
    
    # Calculate quartiles for edge colouring from study abundances
    if all_study_abundances:
        all_study_abundances.sort()
        q1_idx = int(len(all_study_abundances) * 0.25)
        q2_idx = int(len(all_study_abundances) * 0.5)
        q3_idx = int(len(all_study_abundances) * 0.75)
        
        q1 = all_study_abundances[q1_idx]
        q2 = all_study_abundances[q2_idx]
        q3 = all_study_abundances[q3_idx]
        
        # Set default abundance threshold if not provided
        if abundance_threshold is None:
            abundance_threshold = q3  # Default to the 75th percentile
    else:
        q1, q2, q3 = 0, 0, 0
        if abundance_threshold is None:
            abundance_threshold = 0
    
    # Create edge colourmap with more distinguished browns
    edge_colours = [
        '#291709',  # very dark brown - lowest abundance
        '#593D20',  # dark brown
        '#8B6B43',  # medium brown
        '#BEA27D'   # light brown - highest abundance
    ]
    edge_cmap = LinearSegmentedColormap.from_list('edge_cmap', edge_colours)
    
    # Function to get colour based on abundance quartile
    def get_quartile_colour(abundance, verbose = False):
        if abundance <= q1:
            return edge_cmap(0.125)  
        elif abundance <= q2:
            return edge_cmap(0.375)  
        elif abundance <= q3:
            return edge_cmap(0.625)  
        else:
            return edge_cmap(0.875)
    
    # Draw edges with different styles for base tree and study taxa
    base_lines = []
    base_line_colours = []
    study_lines = []
    study_line_colours = []
    
    for taxid, pos in node_positions.items():
        if taxid in combined_parent_map and combined_parent_map[taxid] in node_positions:
            parent_id = combined_parent_map[taxid]
            parent_pos = node_positions[parent_id]
            
            # Create straight line from parent to child
            start_point = (parent_pos['x'], parent_pos['y'])
            end_point = (pos['x'], pos['y'])
            
            # Check if this is a study taxon edge
            if taxid in study_taxa:
                study_lines.append([start_point, end_point])
                
                # Colour edge based on study taxon abundance
                abundance = study_taxon_abundances.get(taxid, 0)
                study_line_colours.append(get_quartile_colour(abundance))
            else:
                # This is a base tree edge, so grey it out
                base_lines.append([start_point, end_point])
                base_line_colours.append('lightgrey')
    
    # Plot base tree edges (greyed out)
    base_lc = LineCollection(base_lines, colors=base_line_colours, alpha=0.5, linewidths=edge_width)
    ax.add_collection(base_lc)
    
    # Plot study edges
    study_lc = LineCollection(study_lines, colors=study_line_colours, alpha=0.9, linewidths=edge_width+0.5)
    ax.add_collection(study_lc)
    
    # Draw nodes with different styles for base tree and study taxa
    base_node_xs = []
    base_node_ys = []
    base_node_colours = []
    
    study_node_xs = []
    study_node_ys = []
    study_node_colours = []
    
    # Track high abundance study nodes for labeling
    abundant_nodes = []
    
    # Track study taxa that weren't in the base tree for special highlighting
    new_study_taxa = study_taxa - base_taxa
    new_study_node_xs = []
    new_study_node_ys = []
    new_study_node_colours = []
    
    for taxid, pos in node_positions.items():
        x, y = pos['x'], pos['y']
        
        # Get node rank for colouring
        if taxid in study_tax_2_rank_string_map:
            node_rank = study_tax_2_rank_string_map.get(taxid, "unknown")
        else:
            node_rank = base_tax_2_rank_string_map.get(taxid, "unknown")
        
        # Get colour from rank or use grey for anchor ranks
        if node_rank.lower() in anchor_ranks:
            colour = 'grey'
        else:
            colour = rank_colours.get(node_rank, 'grey')
        
        if taxid in study_taxa:
            # Get abundance for this study taxon
            abundance = study_taxon_abundances.get(taxid, 0)
            
            # Track high-abundance nodes for labeling
            if abundance >= abundance_threshold:
                abundant_nodes.append((taxid, pos, abundance, node_rank, colour))
            
            # Check if this is a new study taxon (not in base tree)
            if taxid in new_study_taxa:
                new_study_node_xs.append(x)
                new_study_node_ys.append(y)
                new_study_node_colours.append(colour)
            else:
                # This is a study taxon that's also in the base tree
                study_node_xs.append(x)
                study_node_ys.append(y)
                study_node_colours.append(colour)
        else:
            # This is a base tree node, so grey it out
            base_node_xs.append(x)
            base_node_ys.append(y)
            base_node_colours.append('lightgrey')
    
    # Plot base tree nodes (greyed out)
    ax.scatter(base_node_xs, base_node_ys, s=node_size, c=base_node_colours, alpha=0.5, 
               edgecolors='lightgrey', linewidths=0.5)
    
    # Plot study nodes that also exist in base tree
    ax.scatter(study_node_xs, study_node_ys, s=node_size, c=study_node_colours, alpha=1.0, 
               edgecolors='black', linewidths=0.5, zorder=6)
    
    # Plot new study nodes with red outlines
    ax.scatter(new_study_node_xs, new_study_node_ys, s=node_size*1.2, c=new_study_node_colours, alpha=1.0, 
               edgecolors='red', linewidths=1.5, zorder=7)
    
    # Set plot limits based on node positions
    all_radii = [pos['radius'] for pos in node_positions.values()]
    if all_radii:
        max_radius = max(all_radii)
    else:
        max_radius = 1
    
    ax.set_xlim(-max_radius * 1.4, max_radius * 1.4)
    ax.set_ylim(-max_radius * 1.4, max_radius * 1.4)
    
    # Label high abundance study nodes (reuse code from original function)
    # This would need to be implemented similar to plot_phylogenetic_tree_with_master_positions
    
    # Turn off axis
    ax.axis('off')
    
    # Create taxonomy rank legend similar to the original visualization
    # First create a list of ranks to show in the legend, ordered by the hierarchy
    ranks_to_show = []
    
    # Add standard ranks first, in hierarchy order
    for rank in sorted(rank_hierarchy.keys(), key=lambda r: rank_hierarchy[r]):
        if rank in data_ranks and rank not in anchor_ranks:
            # Find the corresponding rank from unique_ranks with correct capitalization
            matching_ranks = [r for r in unique_ranks if r.lower() == rank]
            if matching_ranks:
                ranks_to_show.extend(matching_ranks)
    
    # Then add anchor ranks
    for rank in sorted(anchor_ranks):
        if rank in data_ranks:
            # Find the corresponding rank from unique_ranks with correct capitalization
            matching_ranks = [r for r in unique_ranks if r.lower() == rank]
            if matching_ranks:
                ranks_to_show.extend(matching_ranks)
    
    # Add any other ranks not in hierarchy or anchor_ranks
    other_ranks = [r for r in unique_ranks if r.lower() not in rank_hierarchy and r.lower() not in anchor_ranks]
    if other_ranks:
        ranks_to_show.extend(sorted(other_ranks))

    # Create taxonomy rank legend
    if ranks_to_show:
        # Number of columns needed - using 6 items per column
        num_items = len(ranks_to_show)
        num_columns = (num_items + 5) // 6  # Ceiling division for 6 items per column
        
        # Calculate position - place on left side
        legend_y_pos = 0.15  # Position both legends at same vertical position
        
        # Create a custom legend axis on the left side
        legend_height = 0.15  # Height remains the same
        legend_width = 0.35   # Slightly narrower to fit side by side
        
        # Position the legend axis at the left
        legend_ax = fig.add_axes([0.3 - legend_width/2, legend_y_pos, 
                                legend_width, legend_height])
        legend_ax.axis('off')  # Hide axes
        
        # Add bounding box with curved corners
        fancy_box = mpatches.FancyBboxPatch((0, 0), 1, 1, 
                                boxstyle="round,pad=0.02,rounding_size=0.02",
                                fill=False, edgecolor='black', linewidth=1)
        legend_ax.add_patch(fancy_box)
        
        # Add "Taxonomic Ranks" title
        legend_ax.text(0.5, 0.95, 'Taxonomic Ranks', ha='center', va='top', 
                    fontsize=10, fontweight='bold')
        
        # Calculate spacing - make items closer together
        col_width = 1.0 / num_columns
        row_height = 0.85 / 6  # 6 rows max, adjust to make closer
        
        # Add legend items in order, 6 per column
        for i, rank in enumerate(ranks_to_show):
            # Calculate position (column then row)
            col = i // 6  # Now 6 items per column
            row = i % 6
            
            # x position is centre of column
            x_pos = (col + 0.5) * col_width
            # y position counts from top down
            y_pos = 0.85 - (row + 0.5) * row_height
            
            colour = rank_colours.get(rank, 'grey')
            
            # Add coloured marker
            legend_ax.scatter([x_pos - 0.02], [y_pos], color=colour, s=50, 
                            edgecolors='black', linewidths=0.5)
            
            # Add text label - slightly closer to the marker
            legend_ax.text(x_pos + 0.015, y_pos, rank, ha='left', va='center', fontsize=7)
        
        # Track the bottom position for node type legend
        bottom_position = legend_y_pos
    else:
        bottom_position = 0
    
    # Add node type legend (study vs base tree)
    # Add custom legend for study vs base tree
    #legend_elements = [
    #    mpatches.Patch(facecolor='lightgrey', edgecolor='lightgrey', alpha=0.5, label='Base Tree'),
    #    mpatches.Patch(facecolor='cornflowerblue', edgecolor='black', alpha=1.0, label='Study Taxa'),
    #    mpatches.Patch(facecolor='cornflowerblue', edgecolor='red', alpha=1.0, label='New Study Taxa')
    #]

    legend_elements = [
        Line2D([0], [0], marker='o', color='w', markerfacecolor='lightgrey', 
            markeredgecolor='lightgrey', markersize=10, alpha=0.5, label='Base Tree'),
        Line2D([0], [0], marker='o', color='w', markerfacecolor='cornflowerblue', 
            markeredgecolor='black', markersize=10, alpha=1.0, label='Study Taxa'),
        Line2D([0], [0], marker='o', color='w', markerfacecolor='cornflowerblue', 
            markeredgecolor='red', markersize=10, alpha=1.0, label='New Study Taxa')
    ]
    
    ax.legend(handles=legend_elements, loc='upper right', framealpha=0.7)

    # Add abundance legend for study dataset
    create_abundance_legend(fig, ax, edge_cmap, bottom_position + 0.1, verbose = verbose)
    
    # Add surface text if provided
    if surface_text:
        surface_text_y = -0.05 * max_radius * 1.4
        text = ax.text(0, surface_text_y, surface_text, 
               ha='center', va='center', 
               fontsize=surface_text_size, 
               fontweight='bold', 
               bbox=dict(facecolor='white', edgecolor='black', boxstyle='round', 
                        alpha=0.4, pad=0.5),
               zorder=25)
    
    # Adjust layout
    plt.tight_layout()
    plt.subplots_adjust(bottom=0.25)
    
    # Save plot if requested
    if output_file:
        plt.savefig(output_file, dpi=300, bbox_inches='tight')
    
    return fig, ax


def load_study_dataset(ncbi_taxonomy, df_ids, verbose = False):
    return create_filtered_rank_abundances_dict(ncbi_taxonomy, df_ids, verbose = verbose)
