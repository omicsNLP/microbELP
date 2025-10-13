import os
import numpy as np
import pickle
import textwrap

import matplotlib.pyplot as plt
from matplotlib.colors import LinearSegmentedColormap
from matplotlib.patches import FancyBboxPatch
from matplotlib.collections import LineCollection
from matplotlib.transforms import Bbox

# for the abundance legend
from matplotlib.colors import ListedColormap, BoundaryNorm
from matplotlib.colorbar import ColorbarBase

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

def generate_master_positions(combined_data, output_file=None, verbose = False):
    # joram's approach
    """Generate master node positions for taxa from a combined microbiome dataset using depth-first approach.
    
    Args:
        combined_data: Tuple containing (filtered_rank_abundances_dict, tax_parent_map, 
                      tax_children_map, tax_2_rank_string_map, tax_2_normalised_rank_value_map)
        output_file: Optional file path to save the master positions
    Returns:
        Dictionary mapping tax IDs to their master positions
    """
    # unpack combined data
    filtered_rank_abundances_dict, tax_parent_map, tax_children_map, \
        tax_2_rank_string_map, tax_2_normalised_rank_value_map = combined_data
    
    # get all taxa IDs
    all_taxa = set()
    for rank, taxa_dict in filtered_rank_abundances_dict.items():
        all_taxa.update(taxa_dict.keys())
    
    # find root taxa (nodes with no parents in our dataset)
    root_taxa = [taxid for taxid in all_taxa if taxid not in tax_parent_map or tax_parent_map[taxid] not in all_taxa]
    
    # if no root found, use the taxon with the lowest normalised rank value
    if not root_taxa:
        min_rank_value = float('inf')
        for taxid in all_taxa:
            if taxid in tax_2_normalised_rank_value_map:
                rank_value = tax_2_normalised_rank_value_map[taxid]
                if rank_value < min_rank_value:
                    min_rank_value = rank_value
                    root_taxa = [taxid]
    
    # sort root taxa by rank value (kingdoms, etc.)
    root_taxa.sort(key=lambda taxid: tax_2_normalised_rank_value_map.get(taxid, float('inf')))
    
    # init tracking variables for depth-first ordering
    sorted_taxa = []  # will store the final depth-first ordering
    is_leaf_node = {}  # tracks whether each node is a leaf
    visited = set()  # tracks visited nodes to prevent duplicates

    # step 1-4: create depth-first ordering with duplicate prevention
    def depth_first_sort(taxid, verbose = False):
        # Skip if already processed
        if taxid in visited:
            return
        
        # Mark as visited and add to sorted list
        visited.add(taxid)
        sorted_taxa.append(taxid)
        
        # find children
        children = tax_children_map.get(taxid, [])
        children = [child for child in children if child in all_taxa]
        
        # if no children, mark as leaf node
        if not children:
            is_leaf_node[taxid] = True
            return
        
        # sort children by rank value
        children.sort(key=lambda child: tax_2_normalised_rank_value_map.get(child, float('inf')))
        
        # process each child depth-first
        for child in children:
            depth_first_sort(child)
        
        # not a leaf node
        is_leaf_node[taxid] = False
    
    """
    # step 1-4: create depth-first ordering
    def depth_first_sort(taxid):
        sorted_taxa.append(taxid)
        
        # find children
        children = tax_children_map.get(taxid, [])
        children = [child for child in children if child in all_taxa]
        
        # if no children, mark as leaf node
        if not children:
            is_leaf_node[taxid] = True
            return
        
        # sort children by rank value
        children.sort(key=lambda child: tax_2_normalised_rank_value_map.get(child, float('inf')))
        
        # process each child depth-first
        for child in children:
            depth_first_sort(child)
        
        # not a leaf node
        is_leaf_node[taxid] = False
    """

    # process each root taxon
    for root in root_taxa:
        depth_first_sort(root)
    
    # return sorted_taxa
    
    # find all leaf nodes in the sorted order
    leaf_nodes = [taxid for taxid in sorted_taxa if is_leaf_node.get(taxid, False)]

    # return leaf_nodes
    
    # step 5-6: assign angles to leaf nodes
    angle_per_leaf = 2 * np.pi / len(leaf_nodes)
    leaf_angles = {}
    
    #print(f"len leaf nodes {len(leaf_nodes)}")
    #print(f"angle leaf {angle_per_leaf}")
    for i, leaf in enumerate(leaf_nodes):
        leaf_angles[leaf] = i * angle_per_leaf
    
    #print(f"{leaf_angles['NCBI:txid9606']}")
    
    # step 7: assign angles to internal nodes (bottom-up)
    node_angles = leaf_angles.copy()

    # debugging
    #print(sorted_taxa[0:10])
    #plt.hist([v for k, v in leaf_angles.items()], bins=30)
    #plt.show()

    #return
    
    # process in reverse order (bottom-up)
    for taxid in reversed(sorted_taxa):
        if not is_leaf_node.get(taxid, True):
            # get children
            children = tax_children_map.get(taxid, [])
            children = [child for child in children if child in all_taxa and child in node_angles]
            
            if children:
                # find min and max angles of children
                child_angles = [node_angles[child] for child in children]
                
                # handle the case where angles wrap around the circle
                min_angle = min(child_angles)
                max_angle = max(child_angles)
                
                # check if angles wrap around the circle (gap > pi indicates wrap-around)
                if max_angle - min_angle > np.pi:
                    if verbose:
                        print(f"in angle adjustment statement")
                    # convert angles to handle the wrap-around
                    adjusted_angles = []
                    for angle in child_angles:
                        if angle > np.pi:
                            adjusted_angles.append(angle - 2 * np.pi)
                        else:
                            adjusted_angles.append(angle)
                    
                    min_angle = min(adjusted_angles)
                    max_angle = max(adjusted_angles)
                    
                    # calculate average angle, adjusting back if needed
                    avg_angle = (min_angle + max_angle) / 2
                    if avg_angle < 0:
                        avg_angle += 2 * np.pi
                else:
                    # simple average between min and max
                    avg_angle = (min_angle + max_angle) / 2
                
                node_angles[taxid] = avg_angle
    
    # create final node positions
    node_positions = {}
    for taxid in sorted_taxa:
        if taxid in tax_2_normalised_rank_value_map and taxid in node_angles:
            radius = tax_2_normalised_rank_value_map[taxid]
            angle = node_angles[taxid]
            
            node_positions[taxid] = {
                'angle': angle,
                'radius': radius,
                'x': radius * np.cos(angle),
                'y': radius * np.sin(angle)
            }
    
    # save master positions if output file provided
    if output_file:
        with open(output_file, 'wb') as f:
            pickle.dump(node_positions, f)
        if verbose:
            print(f"Master positions saved to {output_file}")
    
    return node_positions

def load_master_positions(file_path, verbose = False):
    with open(file_path, 'rb') as f:
        return pickle.load(f)

def plot_phylogenetic_tree_with_master_positions(
    filtered_rank_abundances_dict, tax_parent_map, tax_children_map, 
    tax_2_rank_string_map, tax_2_normalised_rank_value_map, master_positions,
    tax_name_map=None, figsize=(12, 12), output_file=None, 
    highlight_ids=None, node_size=30,
    edge_width=1.5, surface_text=None, surface_text_size=10,
    abundance_threshold=None, max_textbox_labels=10, verbose = False):
    """Plot phylogenetic tree using master node positions.
    
    Args:
        filtered_rank_abundances_dict: Dictionary with rank-based abundance data
        tax_parent_map: Dictionary mapping tax IDs to their parent tax IDs
        tax_children_map: Dictionary mapping tax IDs to lists of their child tax IDs
        tax_2_rank_string_map: Dictionary mapping tax IDs to their rank strings
        tax_2_normalised_rank_value_map: Dictionary mapping tax IDs to their normalised rank values
        master_positions: Dictionary mapping tax IDs to their master positions
        tax_name_map: Optional dictionary mapping tax IDs to their names
        figsize: Size of the figure as a tuple (width, height)
        output_file: Optional file path to save the visualisation
        highlight_ids: Optional list of tax IDs to highlight
        node_size: Size of the nodes
        max_labels: Maximum number of labels to show
        filtered_rank_dict_qvalues: Optional dictionary with q-values for significance
        significance_threshold: Threshold for significance
        edge_width: Width of the edges
        surface_text: Optional text to display below the tree
        surface_text_size: Size of the surface text
        abundance_threshold: Threshold for considering nodes as having high abundance
        max_textbox_labels: Maximum number of textbox labels to show
    Returns:
        Tuple containing (fig, ax) for further customisation
    """
    # set up figure
    fig, ax = plt.subplots(figsize=figsize)
    ax.set_aspect('equal')
    
    if tax_name_map is None:
        tax_name_map = {}
    
    # define anchor ranks that should have grey nodes
    anchor_ranks = {"tribe", "forma", "clade", "no rank", "root"}
    
    # define rank hierarchy for ordering in the legend
    # rank_hierarchy = rank_hierarchy
    
    # get all taxa IDs
    all_taxa = set()
    for rank, taxa_dict in filtered_rank_abundances_dict.items():
        all_taxa.update(taxa_dict.keys())
    
    # create node positions dictionary for this specific dataset using master positions
    node_positions = {}
    
    # only use positions for taxa that exist in this dataset
    for taxid in all_taxa:
        if taxid in master_positions:
            node_positions[taxid] = master_positions[taxid].copy()
    
    # for taxa in this dataset but not in master positions, create new positions
    missing_taxa = all_taxa - set(node_positions.keys())
    if missing_taxa:
        if verbose:
            print(f"Warning: {len(missing_taxa)} taxa not found in master positions, assigning new positions")
        
        # Assign positions based on parent's position if possible
        for taxid in missing_taxa:
            if taxid in tax_parent_map and tax_parent_map[taxid] in node_positions:
                parent_id = tax_parent_map[taxid]
                parent_pos = node_positions[parent_id]
                rank_value = tax_2_normalised_rank_value_map.get(taxid, parent_pos['radius'] + 0.1)
                
                # Assign position slightly offset from parent
                angle = parent_pos['angle'] + 0.1  # Small offset
                node_positions[taxid] = {
                    'angle': angle,
                    'radius': rank_value,
                    'x': rank_value * np.cos(angle),
                    'y': rank_value * np.sin(angle)
                }
    
    # ensure all nodes have parent relationships for edge drawing
    ensure_parent_relationships(node_positions, tax_parent_map, tax_children_map, filtered_rank_abundances_dict, verbose = verbose)
    
    # get all ranks present in our data
    unique_ranks = set(tax_2_rank_string_map.values())
    data_ranks = {rank.lower() for rank in unique_ranks}
    
    # create an ordered list of ranks based on hierarchy
    ordered_ranks = []
    
    # add standard ranks first, in hierarchy order
    for rank in sorted(rank_hierarchy.keys(), key=lambda r: rank_hierarchy[r]):
        if rank in data_ranks and rank not in anchor_ranks:
            # find corresponding rank from unique_ranks with correct capitalisation
            matching_ranks = [r for r in unique_ranks if r.lower() == rank]
            if matching_ranks:
                ordered_ranks.extend(matching_ranks)
    
    # setup for colouring by rank
    # Create viridis colourmap (not reversed)
    cmap = plt.cm.viridis
    
    # create a mapping of ranks to colours
    rank_colours = {}
    
    # assign colours from the colourmap to standard ranks
    # map from lowest rank (superkingdom) to highest (strain)
    if ordered_ranks:
        for i, rank in enumerate(ordered_ranks):
            # normalise i to be between 0 and 1
            normalised_i = i / (len(ordered_ranks) - 1) if len(ordered_ranks) > 1 else 0
            rank_colours[rank] = cmap(normalised_i)
    
    # add grey colour for anchor ranks
    for rank in unique_ranks:
        if rank.lower() in anchor_ranks:
            rank_colours[rank] = 'grey'
    
    # get all abundances to calculate quartiles
    all_abundances = []
    taxon_abundances = {}
    
    for rank, taxa_dict in filtered_rank_abundances_dict.items():
        for taxid, abundance in taxa_dict.items():
            if taxid in all_taxa:
                all_abundances.append(abundance)
                taxon_abundances[taxid] = abundance
    
    # calculate quartiles for edge colouring
    if all_abundances:
        all_abundances.sort()
        q1_idx = int(len(all_abundances) * 0.25)
        q2_idx = int(len(all_abundances) * 0.5)
        q3_idx = int(len(all_abundances) * 0.75)
        
        q1 = all_abundances[q1_idx]
        q2 = all_abundances[q2_idx]
        q3 = all_abundances[q3_idx]
        
        # set default abundance threshold if not provided
        if abundance_threshold is None:
            abundance_threshold = q3  # default to the 75th percentile
    else:
        q1, q2, q3 = 0, 0, 0
        if abundance_threshold is None:
            abundance_threshold = 0
    
    # create edge colourmap with more distinguished browns
    edge_colours = [
        '#291709',  # very dark brown - lowest abundance
        '#593D20',  # dark brown
        '#8B6B43',  # medium brown
        '#BEA27D'   # light brown - highest abundance
    ]
    edge_cmap = LinearSegmentedColormap.from_list('edge_cmap', edge_colours)
    
    # function to get colour based on abundance quartile - exactly match colourbar values below
    def get_quartile_colour(abundance, verbose = False):
        if abundance <= q1:
            return edge_cmap(0.125)  
        elif abundance <= q2:
            return edge_cmap(0.375)  
        elif abundance <= q3:
            return edge_cmap(0.625)  
        else:
            return edge_cmap(0.875)  
        
    # draw edges (this is now straight lines instead of curved)
    lines = []
    line_colours = []

    for taxid, pos in node_positions.items():
        if taxid in tax_parent_map and tax_parent_map[taxid] in node_positions:
            parent_id = tax_parent_map[taxid]
            parent_pos = node_positions[parent_id]
            
            # create straight line from parent to child
            start_point = (parent_pos['x'], parent_pos['y'])
            end_point = (pos['x'], pos['y'])
            
            # add straight line
            lines.append([start_point, end_point])
            
            # colour edge based on taxon abundance
            abundance = taxon_abundances.get(taxid, 0)
            line_colours.append(get_quartile_colour(abundance))
    
    # plot edges
    lc = LineCollection(lines, colors=line_colours, alpha=0.9, linewidths=edge_width)
    ax.add_collection(lc)
    
    # draw nodes
    node_xs = []
    node_ys = []
    node_colours = []
    
    abundant_nodes = []  # new list for high-abundance nodes
    
    # store the node's rank for legend
    node_rank_map = {}
    
    for taxid, pos in node_positions.items():
        x, y = pos['x'], pos['y']
        
        # get node rank for colouring
        node_rank = tax_2_rank_string_map.get(taxid, "unknown")
        node_rank_map[taxid] = node_rank
        
        # get colour from rank or use calculated colour for anchor ranks
        if node_rank.lower() in anchor_ranks:
            # For the visualisation, we'll use grey
            colour = 'grey'
        else:
            colour = rank_colours.get(node_rank, 'grey')
        
        # get abundance for this taxon
        abundance = taxon_abundances.get(taxid, 0)
        
        # identify high-abundance nodes
        if abundance >= abundance_threshold:
            abundant_nodes.append((taxid, pos, abundance, node_rank, colour))
        
        # store node attributes for scatter plot
        node_xs.append(x)
        node_ys.append(y)
        node_colours.append(colour)
        
        # highlight specific nodes if requested
        if highlight_ids and taxid in highlight_ids:
            circle = plt.Circle((x, y), node_size/200 * 1.2, fill=False, edgecolor='red', linewidth=1.5, zorder=10)
            ax.add_patch(circle)
    
    # plot nodes with uniform size
    ax.scatter(node_xs, node_ys, s=node_size, c=node_colours, alpha=1.0, zorder=5, edgecolors='black', linewidths=0.5)
    
    # set plot limits based on master positions
    all_radii = [pos['radius'] for pos in node_positions.values()]
    if all_radii:
        max_radius = max(all_radii)
    else:
        max_radius = 1
    
    ax.set_xlim(-max_radius * 1.4, max_radius * 1.4)  # Slightly increased to accommodate labels
    ax.set_ylim(-max_radius * 1.4, max_radius * 1.4)  # Slightly increased to accommodate labels
    
    # function to detect textbox overlaps
    def boxes_overlap(box1, box2, buffer=0.05, verbose = False):
        # add a small buffer around boxes
        box1_buffered = Bbox.from_bounds(
            box1.x0 - buffer, box1.y0 - buffer,
            box1.width + 2*buffer, box1.height + 2*buffer
        )
        return box1_buffered.overlaps(box2)
    
    # sort abundant nodes by abundance (highest first)
    abundant_nodes.sort(key=lambda x: x[2], reverse=True)
    
    # limit to max_textbox_labels
    nodes_to_label_textbox = abundant_nodes[:max_textbox_labels]
    
    # add radial labels for abundant nodes
    if nodes_to_label_textbox:
        # Define parameters for label placement
        base_label_offset = max_radius * 1.2  # fixed distance from tree edge
        node_label_fontsize = 6
        node_label_alpha = 0.45
        
        # Sort nodes by angle for easier neighbor detection
        nodes_to_label_textbox.sort(key=lambda x: x[1]['angle'])
        
        # First pass: identify nodes that are close in angle
        angle_groups = []
        current_group = []
        
        # Define threshold for considering nodes as "close" (in radians)
        angle_threshold = 0.4
        
        for i, (taxid, pos, abundance, node_rank, colour) in enumerate(nodes_to_label_textbox):
            if not current_group:
                current_group.append((i, pos['angle']))
            else:
                # Check if current node is close to the last one in the group
                last_idx, last_angle = current_group[-1]
                
                # Handle circular wrapping (comparing angles near 0 and 2π)
                angle_diff = abs(pos['angle'] - last_angle)
                if angle_diff > np.pi:
                    angle_diff = 2 * np.pi - angle_diff
                
                if angle_diff < angle_threshold:
                    current_group.append((i, pos['angle']))
                else:
                    # If not close, finish the current group and start a new one
                    if len(current_group) > 1:
                        angle_groups.append(current_group)
                    current_group = [(i, pos['angle'])]
                    
        # Don't forget the last group
        if len(current_group) > 1:
            angle_groups.append(current_group)
        
        # Second pass: create labels with adjusted offsets for grouped nodes
        label_rendered = []
        
        # Track indices of nodes that are in groups (will need offset)
        grouped_indices = set()
        for group in angle_groups:
            for idx, _ in group:
                grouped_indices.add(idx)
        
        # Create all labels
        for i, (taxid, pos, abundance, node_rank, colour) in enumerate(nodes_to_label_textbox):
            # Get name and position for this node
            name = tax_name_map.get(taxid, str(taxid))
            
            # Wrap long text to keep label width reasonable
            if len(name) > 20:  # Set threshold for text wrapping
                name = '\n'.join(textwrap.wrap(name, width=20))
                
            angle = pos['angle']
            
            # Determine label offset based on whether this node is part of a group
            current_offset = base_label_offset
            
            # If node is in a group, adjust its offset
            if i in grouped_indices:
                # Find which group this node belongs to
                for group in angle_groups:
                    group_indices = [idx for idx, _ in group]
                    if i in group_indices:
                        # Determine position in group
                        position_in_group = group_indices.index(i)
                        # Stagger the offsets - first node at base, others increasingly outward
                        # For 3+ nodes in a group, create a more gradual staggering
                        group_size = len(group)
                        if group_size <= 3:
                            offset_increment = 0.15 * max_radius
                        else:
                            offset_increment = 0.1 * max_radius
                        
                        current_offset = base_label_offset + (position_in_group * offset_increment)
                        break
            
            # Calculate label position with current offset
            label_x = current_offset * np.cos(angle)
            label_y = current_offset * np.sin(angle)
            
            # Calculate text rotation to align with radius
            text_angle = np.degrees(angle)
            if 90 < text_angle < 270:
                text_angle -= 180
            
            # Create text label
            label = ax.text(
                label_x, label_y, 
                f"{name}\nAbundance: {abundance:.1f}", 
                ha='center', va='center', 
                fontsize=node_label_fontsize,  
                rotation=text_angle,  # text aligned radially
                bbox=dict(
                    facecolor='white',  # white background
                    edgecolor=colour,    # edge colour based on taxonomic rank
                    boxstyle='round,pad=0.5',
                    alpha=node_label_alpha,  # quite transparent
                    linewidth=1.5,       # thicker edge
                    mutation_scale=20    # Consistent box size
                ),
                zorder=15
            )
            
            # Add to rendered list
            label_rendered.append(label)
    
    ax.axis('off')
    
    # create two separate legends - one for ranks, one for abundance quartiles
    
    # first create a list of ranks to show in the legend, ordered by the hierarchy
    ranks_to_show = []
    
    # add standard ranks first, in hierarchy order
    for rank in sorted(rank_hierarchy.keys(), key=lambda r: rank_hierarchy[r]):
        if rank in data_ranks and rank not in anchor_ranks:
            # Find the corresponding rank from unique_ranks with correct capitalisation
            matching_ranks = [r for r in unique_ranks if r.lower() == rank]
            if matching_ranks:
                ranks_to_show.extend(matching_ranks)
    
    # then add anchor ranks
    for rank in sorted(anchor_ranks):
        if rank in data_ranks:
            # Find the corresponding rank from unique_ranks with correct capitalisation
            matching_ranks = [r for r in unique_ranks if r.lower() == rank]
            if matching_ranks:
                ranks_to_show.extend(matching_ranks)
    
    # add any other ranks not in hierarchy or anchor_ranks
    other_ranks = [r for r in unique_ranks if r.lower() not in rank_hierarchy and r.lower() not in anchor_ranks]
    if other_ranks:
        ranks_to_show.extend(sorted(other_ranks))

    # after creating the rank legend
    if ranks_to_show:
        # Number of columns needed - using 6 items per column
        num_items = len(ranks_to_show)
        num_columns = (num_items + 5) // 6  # Ceiling division for 6 items per column
        
        # calculate position - place on left side
        legend_y_pos = 0.1  # position both legends at same vertical position
        
        # create a custom legend axis on the left side
        legend_height = 0.15  # height remains the same
        legend_width = 0.35   # slightly narrower to fit side by side
        
        # position the legend axis at the left
        legend_ax = fig.add_axes([0.3 - legend_width/2, legend_y_pos, 
                                legend_width, legend_height])
        legend_ax.axis('off')  # Hide axes
        
        # add bounding box with curved corners
        fancy_box = FancyBboxPatch((0, 0), 1, 1, 
                                boxstyle="round,pad=0.02,rounding_size=0.02",
                                fill=False, edgecolor='black', linewidth=1)
        legend_ax.add_patch(fancy_box)
        
        # add "Taxonomic Ranks" title
        legend_ax.text(0.5, 0.95, 'Taxonomic Ranks', ha='center', va='top', 
                    fontsize=10, fontweight='bold')
        
        # calculate spacing - make items closer together
        col_width = 1.0 / num_columns
        row_height = 0.85 / 6  # 6 rows max, adjust to make closer
        
        # add legend items in order, 6 per column
        for i, rank in enumerate(ranks_to_show):
            # calculate position (column then row)
            col = i // 6  # now 6 items per column
            row = i % 6
            
            # x position is centre of column
            x_pos = (col + 0.5) * col_width
            # y position counts from top down
            y_pos = 0.85 - (row + 0.5) * row_height
            
            colour = rank_colours.get(rank, 'grey')
            
            # add coloured marker
            legend_ax.scatter([x_pos - 0.02], [y_pos], color=colour, s=50, 
                            edgecolors='black', linewidths=0.5)
            
            # add text label - slightly closer to the marker
            legend_ax.text(x_pos + 0.015, y_pos, rank, ha='left', va='center', fontsize=7)
            
        # track the row count for each column to help with abundance legend positioning
        rank_rows = min(6, len(ranks_to_show))
        
        # store this axis to help with calculating positions for other legends
        rank_legend_ax = legend_ax
    else:
        rank_rows = 0
        rank_legend_ax = None

    # calculate bottom position for abundance legend
    if rank_legend_ax is not None:
        bottom_position = legend_y_pos # - 0.1  # NOTE: change this if want to adjust
    else:
        bottom_position = 0.3  # - (0.05 if surface_text else 0)
    
    # add surface text if provided (below the tree and above legends)
    if surface_text:
        # adjust surface_text_y based on max_radius to scale properly
        surface_text_y = -0.05 * max_radius * 1.4
        
        # add text with rectangular box at the bottom of the plot
        text = ax.text(0, surface_text_y, surface_text, 
               ha='center', va='center', 
               fontsize=surface_text_size, 
               fontweight='bold', 
               bbox=dict(facecolor='white', edgecolor='black', boxstyle='round', 
                        alpha=0.6, pad=0.5),
               zorder=25)
    
    # add custom abundance legend
    create_abundance_legend(fig, ax, edge_cmap, bottom_position + 0.1, verbose = verbose)
    
    # add proper spacing for both legends
    plt.tight_layout()
    plt.subplots_adjust(bottom=0.25)  # increase bottom margin to accommodate both legends
    
    # save plot if requested
    if output_file:
        plt.savefig(output_file, dpi=300, bbox_inches='tight')
    
    return fig, ax

def ensure_parent_relationships(node_positions, tax_parent_map, tax_children_map, filtered_rank_abundances_dict, verbose = False):
    """Ensure all nodes in node_positions have proper parent relationships. Call before drawing edges."""
    
    # get all taxa IDs from filtered_rank_abundances_dict
    all_taxa = set()
    for rank, taxa_dict in filtered_rank_abundances_dict.items():
        all_taxa.update(taxa_dict.keys())
    
    # identify nodes without parent relationships
    nodes_without_parents = []
    for taxid in node_positions:
        if taxid not in tax_parent_map or tax_parent_map[taxid] not in node_positions:
            nodes_without_parents.append(taxid)
    if verbose:
        print(f"Found {len(nodes_without_parents)} nodes without parent edges")
    
    # find root node(s) - should be the node(s) with the smallest radius
    potential_roots = sorted(
        [(taxid, pos['radius']) for taxid, pos in node_positions.items()],
        key=lambda x: x[1]
    )
    
    # use innermost node as the default parent for disconnected nodes
    if potential_roots:
        root_id = potential_roots[0][0]
        
        # add parent relationships for disconnected nodes
        for taxid in nodes_without_parents:
            pos = node_positions[taxid]
            
            # skip the root node itself
            if taxid == root_id:
                continue
                
            # find closest potential parent based on radius and angle
            closest_parent = None
            min_distance = float('inf')
            
            # look for nodes with a smaller radius (closer to centre)
            for parent_id, parent_pos in node_positions.items():
                if parent_pos['radius'] < pos['radius']:
                    # calculate angular distance (handle wrapping around 2pi)
                    angle_diff = abs(pos['angle'] - parent_pos['angle'])
                    if angle_diff > np.pi:
                        angle_diff = 2 * np.pi - angle_diff
                    
                    # weight by both radius difference and angle difference
                    radius_diff = pos['radius'] - parent_pos['radius']
                    distance = radius_diff + angle_diff * pos['radius']
                    
                    if distance < min_distance:
                        min_distance = distance
                        closest_parent = parent_id
            
            # if found a parent, establish the relationship
            if closest_parent is not None:
                tax_parent_map[taxid] = closest_parent
                
                # update children map as well
                if closest_parent not in tax_children_map:
                    tax_children_map[closest_parent] = []
                if taxid not in tax_children_map[closest_parent]:
                    tax_children_map[closest_parent].append(taxid)
            else:
                # if no better parent found, use the root as parent
                tax_parent_map[taxid] = root_id
                
                if root_id not in tax_children_map:
                    tax_children_map[root_id] = []
                if taxid not in tax_children_map[root_id]:
                    tax_children_map[root_id].append(taxid)
    
    return tax_parent_map, tax_children_map

def create_abundance_legend(fig, ax, edge_cmap, bottom_position, verbose = False):
    # create quartile colours (same exact positions as in get_quartile_colour)
    quartile_colours = [
        edge_cmap(0.125),  # Q1
        edge_cmap(0.375),  # Q2
        edge_cmap(0.625),  # Q3
        edge_cmap(0.875)   # Q4
    ]

    # create discrete colourmap with these colours
    discrete_cmap = ListedColormap(quartile_colours)

    # calculate position for the colourbar
    colourbar_width = 0.3  # fraction of figure width
    colourbar_height = 0.02  # fraction of figure height

    # create a new axis for the colourbar
    cax = fig.add_axes([
        0.7 - (colourbar_width/2),  # centre horizontally in the right box
        bottom_position,    # position below title
        colourbar_width,            # width
        colourbar_height            # height
    ])

    # define boundaries and normalisation
    bounds = [0, 1, 2, 3, 4]
    norm = BoundaryNorm(bounds, discrete_cmap.N)

    # create colourbar
    cb = ColorbarBase(
        cax, 
        cmap=discrete_cmap,
        norm=norm,
        boundaries=bounds,
        spacing='uniform',
        orientation='horizontal',
        ticks=[0.5, 1.5, 2.5, 3.5],
        drawedges=True
    )

    # set tick labels
    cb.set_ticklabels(['Lowest\nAbundance\n(Q1)', 'Low-Medium\nAbundance\n(Q2)', 
                       'Medium-High\nAbundance\n(Q3)', 'Highest\nAbundance\n(Q4)'], 
                      fontsize=8)

    # set label
    cb.set_label('Abundance Quartiles', fontweight='bold', fontsize=10, labelpad=5)

    return cax

def compare_microbiomes_with_master_positions(microbiome_data_list, labels=None, output_dir=None, master_positions=None, verbose = False):
    """Create multiple phylogenetic trees using same master positions for consistent node placement across all trees.
    
    Args:
        microbiome_data_list: List of tuples containing (filtered_rank_abundances_dict, tax_parent_map, 
                             tax_children_map, tax_2_rank_string_map, tax_2_normalised_rank_value_map)
                             for each microbiome
        labels: Optional list of labels for each microbiome
        output_dir: Optional directory to save the visualisations
        master_positions: Optional master positions dictionary. If not provided, it will be 
                         generated from the first microbiome in the list
                         
    Returns:
        Dictionary mapping microbiome labels to their figures
    """
    if not microbiome_data_list:
        raise ValueError("No microbiome data provided")
    
    # Generate master positions if not provided
    if master_positions is None:
        if verbose:
            print("Generating master positions from first microbiome")
        master_positions = generate_master_positions(microbiome_data_list[0], verbose = verbose)
    
    # Set default labels if not provided
    if labels is None:
        labels = [f"Microbiome {i+1}" for i in range(len(microbiome_data_list))]
    
    # Ensure output directory exists if provided
    if output_dir and not os.path.exists(output_dir):
        os.makedirs(output_dir)
    
    # Create visualisations for each microbiome
    figures = {}
    
    for i, (data, label) in enumerate(zip(microbiome_data_list, labels)):
        if verbose:
            print(f"Creating visualisation for {label}")
        
        # Unpack microbiome data
        filtered_rank_abundances_dict, tax_parent_map, tax_children_map, tax_2_rank_string_map, tax_2_normalised_rank_value_map = data
        
        # Set output file path if output_dir provided
        output_file = None
        if output_dir:
            output_file = os.path.join(output_dir, f"{label.replace(' ', '_')}.png")
        
        # Create visualisation with master positions
        fig, ax = plot_phylogenetic_tree_with_master_positions(
            filtered_rank_abundances_dict, tax_parent_map, tax_children_map, 
            tax_2_rank_string_map, tax_2_normalised_rank_value_map, master_positions,
            surface_text=label, output_file=output_file, verbose = verbose
        )
        
        figures[label] = (fig, ax)
    
    return figures
