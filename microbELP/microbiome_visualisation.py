from microbELP.rank_counts import create_filtered_rank_abundances_dict, create_qvalue_dict
from microbELP.master_positions_handler import plot_phylogenetic_tree_with_master_positions, generate_master_positions
from microbELP.load_dic import load_dic
from microbELP.overlay import plot_study_dataset_on_tree
from microbELP.stats import empirical_sampling_comparison
import os
import glob
import json
import datetime
import numpy as np
import pandas as pd

def phylogenetic_tree_microbiome(input_path, 
                                 figure_text = '',
                                 ioa_filter = [], 
                                 output_image_path = './',
                                 save = False,
                                 verbose = False):
    if not isinstance(input_path, str):
        print('Parameter "input_path": Input error, this function only accepts a string path. The path can be a .csv, .tsv, or .txt file containing NCBI Taxonomy IDs, or a directory containing annotated files produced by the pipeline.')
        return None
    else:
        pass
    if not isinstance(figure_text, str):
        print('Parameter "figure_text": Input error, this function only accepts a string, which will be displayed in the centre of the generated figure (e.g., the study or dataset name).')
        return None
    else:
        pass
    if not isinstance(ioa_filter, list):
        print('Parameter "ioa_filter": Input error, this function only accepts a list of section identifiers (e.g., ["IAO:0000318", "IAO:0000319"]). Only used when providing a directory as input.')
        return None
    else:
        pass
    if not isinstance(output_image_path, str):
        print('Parameter "output_image_path": Input error, this function only accepts a string directory path where the output images will be saved. Images will be stored under a new subdirectory "microbiome_visualisation/".')
        return None
    else:
        pass
    if not isinstance(save, bool):
        print('Parameter "save": Input error, this function only accepts a boolean value (True/False) to specify whether to save the generated images automatically.')
        return None
    else:
        pass
    if not isinstance(verbose, bool):
        print('Parameter "verbose": Input error, this function only accepts a boolean value (True/False) to control whether detailed logs of the tree generation process are displayed.')
        return None
    else:
        pass
    if 'tsv' in input_path.lower():
        ioa_filter = []
    elif 'csv' in input_path.lower():
        ioa_filter = []
    elif 'txt' in input_path.lower():
        ioa_filter = []
    else:
        if input_path[-1] == '/':
            input_file = glob.glob(input_path + '*.json')
        else:
            input_file = glob.glob(input_path + '/*.json')
        for i in range(len(ioa_filter)):
            ioa_filter[i] = ioa_filter[i].lower()

    if save:
        if output_image_path[-1] == '/':
            pass
        else:
            output_image_path = output_image_path + '/'
        try:
            os.mkdir(output_image_path + 'microbiome_visualisation')
        except:
            pass

    now = datetime.datetime.now()
    formatted_date = now.strftime("%H%M%S_%d%m%Y")
    
    if 'csv' in input_path.lower(): 
        dataset = pd.read_csv(input_path, header=None)[0].tolist()
    elif 'tsv' in input_path.lower():
        dataset = pd.read_csv(input_path, header=None, sep='\t')[0].tolist()
    elif 'txt' in input_path.lower():
        with open(input_path, "r") as f:
            dataset = [line.strip() for line in f]
    else:
        dataset = []
        for z in range(len(input_file)):
            data = json.load(open(f'{input_file[z]}'))
            current_id = []
            for i in range(len(data['documents'][0]['passages'])):
                if ioa_filter == []:
                    current_id.append(i)
                else:
                    current = list(data['documents'][0]['passages'][i]['infons'].keys())
                    for j in range(len(current)):
                        if data['documents'][0]['passages'][i]['infons'][current[j]].lower() in ioa_filter:
                            current_id.append(i)
            current_id = list(np.unique(current_id))
            for i in range(len(current_id)):
                for j in range(len(data['documents'][0]['passages'][current_id[i]]['annotations'])):
                    if type(data['documents'][0]['passages'][current_id[i]]['annotations'][j]['infons']['identifier']) == str:
                        if '[' in data['documents'][0]['passages'][current_id[i]]['annotations'][j]['infons']['identifier']:
                            lower = 0
                            upper = 0
                            str_ = data['documents'][0]['passages'][current_id[i]]['annotations'][j]['infons']['identifier']
                            if str_.count('[') == 1 and str_.count(']') == 1:
                                for y in range(len(str_)):
                                    if str_[y] == '[':
                                        lower = y+1
                                    elif str_[y] == ']':
                                        upper = y
                                for y in range(len(str_[lower:upper].split())):
                                    dataset.append(str_[lower:upper].split()[y].replace("'", "").replace(',', ''))
                            else:
                                print('error')
                        else:
                            dataset.append(data['documents'][0]['passages'][current_id[i]]['annotations'][j]['infons']['identifier'])
                    else:
                        dataset.extend(data['documents'][0]['passages'][current_id[i]]['annotations'][j]['infons']['identifier'])

    
    ### generate master positions from combined microbiome data
    ncbi_taxonomy = load_dic()
    
    tax_id_2_name = {item['TaxID']: None for item in ncbi_taxonomy}
    tax_id_2_name = {item['TaxID']: item['CleanName'] for item in ncbi_taxonomy if tax_id_2_name.get(item['TaxID']) is None}
    
    ncbi_taxonomy = load_dic()
    combined_data = create_filtered_rank_abundances_dict(ncbi_taxonomy, dataset, verbose = verbose)
    master_positions = generate_master_positions(combined_data, verbose = verbose)
    
    
    microbiome1_filtered_dict, microbiome1_parent_map, microbiome1_children_map, \
        microbiome1_rank_map, microbiome1_norm_value_map = \
        create_filtered_rank_abundances_dict(ncbi_taxonomy, dataset, verbose = verbose)

    if save:
        fig, ax = plot_phylogenetic_tree_with_master_positions(
            microbiome1_filtered_dict, 
            microbiome1_parent_map, microbiome1_children_map,
            microbiome1_rank_map, microbiome1_norm_value_map, master_positions,
            tax_name_map=tax_id_2_name, figsize=(12, 12),
            surface_text=figure_text, output_file = output_image_path + 'microbiome_visualisation' + f'/{formatted_date}_phylogenetic_tree_microbiome.png',
            max_textbox_labels=5, edge_width=1, verbose = verbose
        )
    else:
        fig, ax = plot_phylogenetic_tree_with_master_positions(
            microbiome1_filtered_dict, 
            microbiome1_parent_map, microbiome1_children_map,
            microbiome1_rank_map, microbiome1_norm_value_map, master_positions,
            tax_name_map=tax_id_2_name, figsize=(12, 12),
            surface_text=figure_text,
            max_textbox_labels=5, edge_width=1, verbose = verbose
        )

def comparative_phylogenetic_tree_microbiome(back_input_path, 
                                             front_input_path, 
                                             ioa_filter = [], 
                                             back_text = '', 
                                             front_text = '',
                                             overlap_text = '',
                                             output_image_path = './', 
                                             save = False,
                                             verbose = False):
    if not isinstance(back_input_path, str):
        print('Parameter "back_input_path": Input error, this function only accepts a string path to the reference dataset or domain to compare against.')
        return None
    else:
        pass
    if not isinstance(front_input_path, str):
        print('Parameter "front_input_path": Input error, this function only accepts a string path to the dataset or domain to highlight over the reference.')
        return None
    else:
        pass
    if not isinstance(ioa_filter, list):
        print('Parameter "ioa_filter": Input error, this function only accepts a list of section identifiers (e.g., ["IAO:0000318", "IAO:0000319"]). Used when filtering annotated directory inputs.')
        return None
    else:
        pass
    if not isinstance(back_text, str):
        print('Parameter "back_text": Input error, this function only accepts a string. It is an optional label displayed in the generated figure (e.g., reference dataset name).')
        return None
    else:
        pass
    if not isinstance(front_text, str):
        print('Parameter "front_text": Input error, this function only accepts a string. It is an optional label displayed in the generated figure (e.g., highlighted dataset name).')
        return None
    else:
        pass
    if not isinstance(overlap_text, str):
        print('Parameter "overlap_text": Input error, this function only accepts a string. It is an optional label displayed in the figure to represent overlapping taxa or entities.')
        return None
    else:
        pass
    if not isinstance(output_image_path, str):
        print('Parameter "output_image_path": Input error, this function only accepts a string directory path where output images will be saved. Images will be stored under a new subdirectory "microbiome_visualisation/".')
        return None
    else:
        pass
    if not isinstance(save, bool):
        print('Parameter "save": Input error, this function only accepts a boolean (True/False) indicating whether to save the generated comparative images automatically.')
        return None
    else:
        pass
    if not isinstance(verbose, bool):
        print('Parameter "verbose": Input error, this function only accepts a boolean (True/False) indicating whether to display detailed logs during the comparative tree generation process.')
        return None
    else:
        pass
    ## First plot generation
    if 'tsv' in back_input_path.lower():
        ioa_filter = []
    elif 'csv' in back_input_path.lower():
        ioa_filter = []
    elif 'txt' in back_input_path.lower():
        ioa_filter = []
    else:
        if back_input_path[-1] == '/':
            input_file = glob.glob(back_input_path + '*.json')
        else:
            input_file = glob.glob(back_input_path + '/*.json')
        for i in range(len(ioa_filter)):
            ioa_filter[i] = ioa_filter[i].lower()

    if save:
        if output_image_path[-1] == '/':
            pass
        else:
            output_image_path = output_image_path + '/'
        try:
            os.mkdir(output_image_path + 'microbiome_visualisation')
        except:
            pass
            
    now = datetime.datetime.now()
    formatted_date = now.strftime("%H%M%S_%d%m%Y")
    
    if 'csv' in back_input_path.lower(): 
        general_dataset = pd.read_csv(back_input_path, header=None)[0].tolist()
    elif 'tsv' in back_input_path.lower():
        general_dataset = pd.read_csv(back_input_path, header=None, sep='\t')[0].tolist()
    elif 'txt' in back_input_path.lower():
        with open(back_input_path, "r") as f:
            general_dataset = [line.strip() for line in f]
    else:
        general_dataset = []
        for z in range(len(input_file)):
            data = json.load(open(f'{input_file[z]}'))
            current_id = []
            for i in range(len(data['documents'][0]['passages'])):
                if ioa_filter == []:
                    current_id.append(i)
                else:
                    current = list(data['documents'][0]['passages'][i]['infons'].keys())
                    for j in range(len(current)):
                        if data['documents'][0]['passages'][i]['infons'][current[j]].lower() in ioa_filter:
                            current_id.append(i)
            current_id = list(np.unique(current_id))
            for i in range(len(current_id)):
                for j in range(len(data['documents'][0]['passages'][current_id[i]]['annotations'])):
                    if type(data['documents'][0]['passages'][current_id[i]]['annotations'][j]['infons']['identifier']) == str:
                        if '[' in data['documents'][0]['passages'][current_id[i]]['annotations'][j]['infons']['identifier']:
                            lower = 0
                            upper = 0
                            str_ = data['documents'][0]['passages'][current_id[i]]['annotations'][j]['infons']['identifier']
                            if str_.count('[') == 1 and str_.count(']') == 1:
                                for y in range(len(str_)):
                                    if str_[y] == '[':
                                        lower = y+1
                                    elif str_[y] == ']':
                                        upper = y
                                for y in range(len(str_[lower:upper].split())):
                                    general_dataset.append(str_[lower:upper].split()[y].replace("'", "").replace(',', ''))
                            else:
                                print('error')
                        else:
                            general_dataset.append(data['documents'][0]['passages'][current_id[i]]['annotations'][j]['infons']['identifier'])
                    else:
                        general_dataset.extend(data['documents'][0]['passages'][current_id[i]]['annotations'][j]['infons']['identifier'])

    ncbi_taxonomy = load_dic()
    
    tax_id_2_name = {item['TaxID']: None for item in ncbi_taxonomy}
    tax_id_2_name = {item['TaxID']: item['CleanName'] for item in ncbi_taxonomy if tax_id_2_name.get(item['TaxID']) is None}
    
    ncbi_taxonomy = load_dic()
    general_combined_data = create_filtered_rank_abundances_dict(ncbi_taxonomy, general_dataset, verbose = verbose)
    master_positions = generate_master_positions(general_combined_data, verbose = verbose)
    
    
    microbiome1_filtered_dict, microbiome1_parent_map, microbiome1_children_map, \
        microbiome1_rank_map, microbiome1_norm_value_map = \
        create_filtered_rank_abundances_dict(ncbi_taxonomy, general_dataset, verbose = verbose)
    if save:
        fig, ax = plot_phylogenetic_tree_with_master_positions(
            microbiome1_filtered_dict, 
            microbiome1_parent_map, microbiome1_children_map,
            microbiome1_rank_map, microbiome1_norm_value_map, master_positions,
            tax_name_map=tax_id_2_name, figsize=(12, 12),
            surface_text=back_text, output_file = output_image_path + 'microbiome_visualisation' + f'/{formatted_date}_back_phylogenetic_tree_microbiome.png',
            max_textbox_labels=5, edge_width=1, verbose = verbose
        )
    else:
        fig, ax = plot_phylogenetic_tree_with_master_positions(
            microbiome1_filtered_dict, 
            microbiome1_parent_map, microbiome1_children_map,
            microbiome1_rank_map, microbiome1_norm_value_map, master_positions,
            tax_name_map=tax_id_2_name, figsize=(12, 12),
            surface_text=back_text,
            max_textbox_labels=5, edge_width=1, verbose = verbose
        )

    ## Second plot generation
    if 'tsv' in front_input_path.lower():
        pass
    elif 'csv' in front_input_path.lower():
        pass
    elif 'txt' in front_input_path.lower():
        pass
    else:
        if front_input_path[-1] == '/':
            input_file = glob.glob(front_input_path + '*.json')
        else:
            input_file = glob.glob(front_input_path + '/*.json')
    
    if 'csv' in front_input_path.lower(): 
        domain_dataset = pd.read_csv(front_input_path, header=None)[0].tolist()
    elif 'tsv' in front_input_path.lower():
        domain_dataset = pd.read_csv(front_input_path, header=None, sep='\t')[0].tolist()
    elif 'txt' in front_input_path.lower():
        with open(front_input_path, "r") as f:
            domain_dataset = [line.strip() for line in f]
    else:
        domain_dataset = []
        for z in range(len(input_file)):
            data = json.load(open(f'{input_file[z]}'))
            current_id = []
            for i in range(len(data['documents'][0]['passages'])):
                if ioa_filter == []:
                    current_id.append(i)
                else:
                    current = list(data['documents'][0]['passages'][i]['infons'].keys())
                    for j in range(len(current)):
                        if data['documents'][0]['passages'][i]['infons'][current[j]].lower() in ioa_filter:
                            current_id.append(i)
            current_id = list(np.unique(current_id))
            for i in range(len(current_id)):
                for j in range(len(data['documents'][0]['passages'][current_id[i]]['annotations'])):
                    if type(data['documents'][0]['passages'][current_id[i]]['annotations'][j]['infons']['identifier']) == str:
                        if '[' in data['documents'][0]['passages'][current_id[i]]['annotations'][j]['infons']['identifier']:
                            lower = 0
                            upper = 0
                            str_ = data['documents'][0]['passages'][current_id[i]]['annotations'][j]['infons']['identifier']
                            if str_.count('[') == 1 and str_.count(']') == 1:
                                for y in range(len(str_)):
                                    if str_[y] == '[':
                                        lower = y+1
                                    elif str_[y] == ']':
                                        upper = y
                                for y in range(len(str_[lower:upper].split())):
                                    domain_dataset.append(str_[lower:upper].split()[y].replace("'", "").replace(',', ''))
                            else:
                                print('error')
                        else:
                            domain_dataset.append(data['documents'][0]['passages'][current_id[i]]['annotations'][j]['infons']['identifier'])
                    else:
                        domain_dataset.extend(data['documents'][0]['passages'][current_id[i]]['annotations'][j]['infons']['identifier'])

    ncbi_taxonomy = load_dic()
    
    tax_id_2_name = {item['TaxID']: None for item in ncbi_taxonomy}
    tax_id_2_name = {item['TaxID']: item['CleanName'] for item in ncbi_taxonomy if tax_id_2_name.get(item['TaxID']) is None}
    
    ncbi_taxonomy = load_dic()
    combined_data = create_filtered_rank_abundances_dict(ncbi_taxonomy, domain_dataset, verbose = verbose)
    master_positions = generate_master_positions(combined_data, verbose = verbose)
    
    
    microbiome1_filtered_dict, microbiome1_parent_map, microbiome1_children_map, \
        microbiome1_rank_map, microbiome1_norm_value_map = \
        create_filtered_rank_abundances_dict(ncbi_taxonomy, domain_dataset, verbose = verbose)

    fig_2_text = ''
    if front_text != '':
        fig_2_text = front_text + ' (counts)'
    if save:
        fig, ax = plot_phylogenetic_tree_with_master_positions(
            microbiome1_filtered_dict, 
            microbiome1_parent_map, microbiome1_children_map,
            microbiome1_rank_map, microbiome1_norm_value_map, master_positions,
            tax_name_map=tax_id_2_name, figsize=(12, 12),
            surface_text=fig_2_text, output_file = output_image_path + 'microbiome_visualisation' + f'/{formatted_date}_front_counts_phylogenetic_tree_microbiome.png',
            max_textbox_labels=5, edge_width=1, verbose = verbose
        )
    else:
        fig, ax = plot_phylogenetic_tree_with_master_positions(
            microbiome1_filtered_dict, 
            microbiome1_parent_map, microbiome1_children_map,
            microbiome1_rank_map, microbiome1_norm_value_map, master_positions,
            tax_name_map=tax_id_2_name, figsize=(12, 12),
            surface_text=fig_2_text,
            max_textbox_labels=5, edge_width=1, verbose = verbose
        )
    
    ## Third plot generation
    microbiome1_filtered_dict, microbiome1_parent_map, microbiome1_children_map, \
        microbiome1_rank_map, microbiome1_norm_value_map = \
        create_filtered_rank_abundances_dict(ncbi_taxonomy, domain_dataset, verbose = verbose)
    empirical_results = empirical_sampling_comparison(
        general_combined_data[0], microbiome1_filtered_dict, n_samp=1000, fdr_method='storey')
    result_rank_qvalues_dict = create_qvalue_dict(microbiome1_filtered_dict, empirical_results)

    fig_3_text = ''
    if front_text != '':
        fig_3_text = front_text + ' (q-value)'

    if save:
        fig, ax = plot_phylogenetic_tree_with_master_positions(
            result_rank_qvalues_dict, 
            microbiome1_parent_map, microbiome1_children_map,
            microbiome1_rank_map, microbiome1_norm_value_map, master_positions,
            tax_name_map=tax_id_2_name, figsize=(12, 12),
            surface_text=fig_3_text, output_file = output_image_path + 'microbiome_visualisation' + f'/{formatted_date}_front_qvalues_phylogenetic_tree_microbiome.png',
            max_textbox_labels=5, edge_width=1, verbose = verbose
        )
    else:
        fig, ax = plot_phylogenetic_tree_with_master_positions(
            result_rank_qvalues_dict, 
            microbiome1_parent_map, microbiome1_children_map,
            microbiome1_rank_map, microbiome1_norm_value_map, master_positions,
            tax_name_map=tax_id_2_name, figsize=(12, 12),
            surface_text=fig_3_text,
            max_textbox_labels=5, edge_width=1, verbose = verbose
        )

    ## Fourth plot generation
    base_tree_data = create_filtered_rank_abundances_dict(ncbi_taxonomy, general_dataset)
    
    # create tax_id_2_name mapping
    tax_id_2_name = {item['TaxID']: None for item in ncbi_taxonomy}
    tax_id_2_name = {item['TaxID']: item['CleanName'] for item in ncbi_taxonomy if tax_id_2_name.get(item['TaxID']) is None}
    
    study_data = create_filtered_rank_abundances_dict(ncbi_taxonomy, domain_dataset)

    if save:
        # Plot study dataset on base tree
        fig, ax = plot_study_dataset_on_tree(
            base_tree_data=base_tree_data,
            study_data=study_data,
            tax_name_map=tax_id_2_name,  # add your taxonomy name mapping if available
            figsize=(12, 12),
            output_file=output_image_path + 'microbiome_visualisation' + f'/{formatted_date}_front_over_back_phylogenetic_tree_microbiome.png',
            surface_text=overlap_text,
            edge_width=1
        )
    else:
        # Plot study dataset on base tree
        fig, ax = plot_study_dataset_on_tree(
            base_tree_data=base_tree_data,
            study_data=study_data,
            tax_name_map=tax_id_2_name,  # add your taxonomy name mapping if available
            figsize=(12, 12),
            surface_text=overlap_text,
            edge_width=1
        )
