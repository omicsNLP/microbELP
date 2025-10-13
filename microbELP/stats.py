import math
from math import ceil
import numpy as np
import pandas as pd
from scipy import interpolate
from statsmodels.stats.multitest import multipletests


def randsample(population, k, replace=True, weights=None, verbose = False):
    """Python equivalent of MATLAB's randsample function.
    
    Args:
        population: Integer range (will create range(1, population+1)) or array-like of values to sample from
        k: Number of samples to draw
        replace: Whether to sample with replacement (default: True)
        weights: Optional probability weights for each item in population
    
    Returns:
        Array of sampled values
    """
    # Handle case where population is an integer (common MATLAB usage)
    if isinstance(population, int):
        population = np.arange(1, population+1)
    
    # Ensure k is an integer
    k = int(math.ceil(k))
    
    # Ensure weights sum to 1 if provided
    if weights is not None:
        weights = np.array(weights) / np.sum(weights)
    
    # Sample using numpy's choice function
    return np.random.choice(population, size=k, replace=replace, p=weights)


def empirical_sampling_comparison(background_rank_dict, domain_rank_dict, n_samp=1000, fdr_method='storey', verbose = False):
    """Comparing counts per rank between background and domain microbiomes with FDR Bonferroni procedure.
    
    Args:
        background_rank_dict: Dictionary with ranks as keys, and dictionaries of {taxon_id: count} as values
        domain_rank_dict: Dictionary with the same structure as background_rank_dict
        n_samp: Number of resamplings (precision of empirical p-value)
        fdr_method: Method for multiple testing correction ('storey' or 'bh')
        
    Returns:
        Dictionary with the same structure as domain_rank_dict but with q-values and enrichment info
    """
    results = {}
    significance_threshold = 0.05
    
    # Process each taxonomic rank
    for rank in domain_rank_dict:
        if verbose:
            print(f"Processing rank: {rank}")

        if rank not in background_rank_dict:
            continue
        
        # original
        ## Check if any taxa are present for this rank
        #if not domain_rank_dict[rank] or not background_rank_dict[rank]:
        #    results[rank] = {}
        #    continue
        # Check if any taxa are present for this rank (only skip if literally empty)
        if not domain_rank_dict[rank].keys() or not background_rank_dict[rank].keys():
            results[rank] = {}
            continue

        # Get domain data for this rank
        domain_ids = domain_rank_dict[rank]
        domain_counts = sum(domain_ids.values())
        
        # original
        # Handle zero counts case for domain
        #if domain_counts == 0:
        #    # Skip this rank if no counts at all
        #    results[rank] = {}
        #    continue
        domain_counts = sum(domain_ids.values())
        if domain_counts == 0:
            # Instead of skipping, use a small epsilon value to prevent division by zero
            domain_counts = 1e-10  # Very small number to prevent division by zero
            # Or set all fractions to equal values
            domain_fracs = {tax_id: 1.0/len(domain_ids) for tax_id in domain_ids}
        else:
            domain_fracs = {tax_id: count/domain_counts for tax_id, count in domain_ids.items()}
            
        domain_fracs = {tax_id: count/domain_counts for tax_id, count in domain_ids.items()}

        # Get background data for this rank based on domain ids
        domain_ids_list = list(domain_ids.keys())
        n_ids = len(domain_ids_list)
        background_ids = {tax_id: background_rank_dict[rank].get(tax_id, 0) for tax_id in domain_ids_list}
        background_counts = sum(background_ids.values())
        
        # Handle zero counts case for background
        if background_counts == 0:
            # Use uniform distribution if all background counts are zero
            background_fracs = {tax_id: 1.0/len(background_ids) for tax_id in background_ids}
        else:
            background_fracs = {tax_id: count/background_counts for tax_id, count in background_ids.items()}
        
        # Prepare sampling
        weights = np.array([background_fracs[tax_id] for tax_id in domain_ids_list])
        
        # Ensure weights sum to 1 to prevent ValueError
        if np.sum(weights) > 0:
            weights = weights / np.sum(weights)
        else:
            # Use uniform distribution if all weights are zero
            weights = np.ones(len(weights)) / len(weights)
        
        # Check if background and domain are the same set
        is_same_set = all(abs(background_ids.get(tax_id, 0) - domain_ids.get(tax_id, 0)) < 1e-10 
                          for tax_id in domain_ids_list)
        
        # Pre-allocate array for tracking counts >= observed for all taxa at once
        observed_counts = np.array([domain_ids[tax_id] for tax_id in domain_ids_list])
        counts_geq_observed = np.zeros(n_ids, dtype=np.int32)
        
        # Create a translation array from sample index to taxon ID
        indices = np.arange(n_ids)
        
        # Convert domain_counts to integer to avoid TypeError
        int_domain_counts = ceil(domain_counts)
        
        # Perform sampling - do all simulations at once
        for j in range(n_samp):
            if is_same_set:
                # Equal weight sampling if background = domain
                samples = np.random.choice(indices, size=int_domain_counts, replace=True)
            else:
                # Sample using background weights
                samples = np.random.choice(indices, size=int_domain_counts, replace=True, p=weights)
            
            # Use numpy's bincount for faster counting
            bin_counts = np.bincount(samples, minlength=n_ids)
            
            # Vectorised comparison
            counts_geq_observed += (bin_counts >= observed_counts)
        
        # Calculate empirical p-values for all taxa at once
        p_values = (counts_geq_observed + 1) / (n_samp + 1)
        
        # Adjust for multiple testing once outside the loop
        if fdr_method.lower() == 'storey':
            q_values = storey_tibshirani_fdr(p_values, verbose = verbose)
            # For consistency with multipletests return format
            rejected = q_values <= significance_threshold
        else:
            rejected, q_values, _, _ = multipletests(p_values, method='fdr_bh')
        
        # Calculate results for each taxon
        rank_results = {}
        for i, tax_id in enumerate(domain_ids_list):
            expected_count = background_fracs.get(tax_id, 0) * domain_counts
            # Avoid division by zero in enrichment calculation
            bg_frac = max(background_fracs.get(tax_id, 1e-10), 1e-10)
            enrichment = (domain_fracs.get(tax_id, 0) / bg_frac)
            
            rank_results[tax_id] = {
                'domain_count': domain_ids[tax_id],
                'domain_fraction': domain_fracs[tax_id],
                'background_count': background_ids.get(tax_id, 0),
                'background_fraction': background_fracs.get(tax_id, 0),
                'expected_count': math.ceil(expected_count),
                'enrichment': enrichment,
                'p_value': p_values[i],
                'q_value': q_values[i],
                'significant': rejected[i]
            }
        
        results[rank] = rank_results
 
    return results


def storey_tibshirani_fdr(p_values, lambda_range=None, pi0_method="smoother", verbose=False):
    """Calculate q-values using Storey-Tibshirani procedure.
    
    Args:
        pvalues: array-like of p-values
        lambda_range: range of lambda values to estimate pi0, default is np.arange(0, 0.9, 0.05)
        pi0_method: method for pi0 estimation ("smoother" or "bootstrap")
        verbose: whether to print intermediate results

    Returns:
        qvalues: array of q-values
    """
    
    # Convert pvalues to numpy array
    p_values = np.asarray(p_values)
    
    # Default lambda range if not provided
    if lambda_range is None:
        lambda_range = np.arange(0, 0.9, 0.05)
    
    # Number of p-values
    m = float(len(p_values))
    
    # Calculate pi0 estimates for different lambda values
    pi0_lambda = np.ones(len(lambda_range))
    for i, lambda_val in enumerate(lambda_range):
        pi0_lambda[i] = np.mean(p_values >= lambda_val) / (1 - lambda_val)
        if verbose:
            print(f"λ = {lambda_val:.2f}, π0 = {pi0_lambda[i]:.3f}")
    
    # Determine pi0 based on the chosen method
    if pi0_method == "smoother":
        # Fit a cubic spline to the data
        if len(lambda_range) > 1:
            smooth_spline = interpolate.splrep(lambda_range, pi0_lambda, k=min(3, len(lambda_range)-1))
            pi0 = interpolate.splev(lambda_range[-1], smooth_spline)
        else:
            pi0 = pi0_lambda[0]
    elif pi0_method == "bootstrap":
        # Bootstrap method (simplified)
        min_pi0 = min(pi0_lambda)
        mse = np.zeros(len(lambda_range))
        for i in range(100):  # Bootstrap iterations
            p_boot = np.random.choice(p_values, size=len(p_values), replace=True)
            for j, lambda_val in enumerate(lambda_range):
                pi0_boot = np.mean(p_boot >= lambda_val) / (1 - lambda_val)
                mse[j] += (pi0_boot - min_pi0)**2
        pi0 = pi0_lambda[np.argmin(mse/100)]
    else:
        raise ValueError("pi0_method must be 'smoother' or 'bootstrap'")
    
    # Ensure pi0 is in [0,1]
    pi0 = min(pi0, 1)
    
    if verbose:
        print(f"Estimated π0 = {pi0:.3f}")
    
    # Sort p-values in ascending order
    indices = np.argsort(p_values)
    p_values_sorted = p_values[indices]
    
    # Calculate q-values
    m = float(len(p_values))
    q_values_sorted = pi0 * p_values_sorted * m / np.arange(1, m+1)
    
    # Ensure q-values are monotonically increasing from right to left
    for i in range(int(m)-2, -1, -1):
        q_values_sorted[i] = min(q_values_sorted[i], q_values_sorted[i+1])
    
    # Restore original order
    q_values = np.empty_like(q_values_sorted)
    q_values[indices] = q_values_sorted
    
    return q_values


def transform_results_to_dataframe(results, taxonomy_data, verbose = False):
    """Transform the nested results dictionary into a DataFrame using existing taxonomy data
    
    Args:
        results: Dictionary of results from empirical_sampling_comparison
        taxonomy_data: List of dicts with taxonomy information
        
    Returns:
        DataFrame with columns: tax_id, rank, name1, name2, aggcount, qvalue
    """
    # Create a lookup dictionary for taxonomy data
    tax_lookup = {}
    for entry in taxonomy_data:
        tax_id = entry['TaxID']
        # To make sure that first (== common) names are used
        if tax_id in tax_lookup:
            continue
        tax_lookup[tax_id] = {
            'name1': entry['CleanName'],
            'name2': entry.get('OriginalName', ''),  # Use Original as name2
            'rank': entry['TaxRank']
        }
    
    rows = []
    
    for rank, taxa in results.items():
        for tax_id, stats in taxa.items():
            # Get taxonomy info, use defaults if not found
            tax_info = tax_lookup.get(tax_id, {'name1': '', 'name2': '', 'rank': rank})
            
            rows.append({
                'tax_id': tax_id,
                'rank': rank,
                'name1': tax_info['name1'],
                'name2': tax_info['name2'],
                'agg_count': stats['domain_count'],
                'q_value': stats['q_value']
            })
    
    # Create DataFrame
    df = pd.DataFrame(rows)
    
    # Sort by qvalue and aggcount
    df = df.sort_values(['q_value', 'agg_count'], ascending=[True, False])
    
    return df
