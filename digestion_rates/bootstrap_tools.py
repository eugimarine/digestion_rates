# AUTOGENERATED! DO NOT EDIT! File to edit: ../03_Boostrap_correlation.ipynb.

# %% auto 0
__all__ = ['sample_cells', 'fill_not_found_sequences', 'digestion_profile_matrix', 'fast_digestion_profile',
           'bootstrap_population_filling', 'bootstrap_population', 'correlate_sequence',
           'cross_correlation_on_all_sequences', 'gmean_filter', 'single_iteration_bootstrap_cc', 'iter_bootstrap_cc',
           'average_results_bootstrap', 'aggregate_results_bootstrap']

# %% ../03_Boostrap_correlation.ipynb 4
import pandas as pd
import numpy as np
from scipy.signal import correlate, correlation_lags
import itertools

# %% ../03_Boostrap_correlation.ipynb 13
def sample_cells(df, metadata, n_sample):
    selected_cells = np.random.choice(metadata['cb_encode'], size=n_sample)
    subsampled_df = df.set_index('cb_encode').loc[selected_cells,:].reset_index()
    subsampled_meta = metadata.set_index('cb_encode').loc[selected_cells,:]
    return selected_cells, subsampled_meta, subsampled_df


# %% ../03_Boostrap_correlation.ipynb 15
def fill_not_found_sequences(df, metadata):
    comb_seq_cb = pd.MultiIndex.from_tuples(itertools.product(df['seq'].unique(), metadata['cb_encode']), names= ('seq', 'cb_encode'))
    filled = df.set_index(['seq', 'cb_encode']).reindex(comb_seq_cb)
    filled.reset_index(level=0, inplace=True)
    filled['counts'] = filled['counts'].fillna(0)
    filled = filled.fillna(metadata.set_index('cb_encode').to_dict()).reset_index()
    return filled

# %% ../03_Boostrap_correlation.ipynb 17
def digestion_profile_matrix(df, aggregation='mean'):
    averages = df.groupby(['seq','log_units_mnase']).aggregate(aggregation).reset_index()
    averages = averages.sort_values('log_units_mnase').reset_index(drop=True)
    dig_matrix = averages.pivot(index='seq', columns='log_units_mnase', values='counts').fillna(0)
    return dig_matrix


# %% ../03_Boostrap_correlation.ipynb 20
def fast_digestion_profile(df, metadata):
    """ create digestion profile without filling 0 in the original dataframe.
    This is done by summing the counts per seq and log_units_mnase and divide by the number of
    cells per mnase"""
    count_cell_per_mnase = metadata.groupby('log_units_mnase')['log_units_mnase'].count()


    sum_counts = df.groupby(['seq','log_units_mnase'])['counts'].sum()
    multi_df2 = df.set_index(['seq','log_units_mnase'])
    # avg_count = (sum_counts / count_cell_per_mnase).reset_index()

    multi_df2['avg_count'] = (sum_counts / count_cell_per_mnase)
    dig_matrix = multi_df2.groupby(level=[0,1])['avg_count'].mean().to_frame().unstack().fillna(0).loc[:, 'avg_count']
    return dig_matrix


# %% ../03_Boostrap_correlation.ipynb 22
def bootstrap_population_filling(seqcell, pop, samples_size, metadata):
    all_g0 = seqcell.loc[seqcell['sort_population']==pop]
    sampled, g0_boot = sample_cells(all_g0, samples_size)
    filled_df = fill_not_found_sequences(g0_boot, metadata)
    g0_digprof = digestion_profile_matrix(g0_boot)
    return g0_digprof

# %% ../03_Boostrap_correlation.ipynb 23
def bootstrap_population(seqcell, pop, samples_size, metadata):
    df_pop = seqcell.loc[seqcell['sort_population']==pop]
    metadata_pop = metadata.loc[metadata['sort_population']==pop]
    sampled, metadata, df = sample_cells(df_pop, metadata_pop, samples_size)
    digprof = fast_digestion_profile(df, metadata)
    return digprof

# %% ../03_Boostrap_correlation.ipynb 25
def correlate_sequence(row, other, seq_name):
    try:
        other_row = other.loc[seq_name, :]
        cc = correlate(row, other_row, "full")
        return cc
    except KeyError:
        return np.array([np.nan] * other.shape[1]*2-1)

# %% ../03_Boostrap_correlation.ipynb 27
def cross_correlation_on_all_sequences(g0_profile, inter_profile):
    
    range_values = correlation_lags(g0_profile.shape[1], inter_profile.shape[1])
    corr_df_shape = (g0_profile.shape[0], range_values.shape[0])
    
    corr_df = pd.DataFrame(np.zeros(corr_df_shape), index=g0_profile.index, columns=range_values)

    for nm,row in g0_profile.iterrows():
        corr = correlate_sequence(row, inter_profile, nm)
        corr_df.loc[nm, :] = corr
    corr_df = corr_df.dropna()
    return corr_df


# %% ../03_Boostrap_correlation.ipynb 32
def gmean_filter(pop1_digmatrix, pop2_digmatrix, threshold):
    gm_score = (pop1_digmatrix.mean(axis=1) * pop2_digmatrix.mean(axis=1)).dropna()
    i = gm_score.index[gm_score>threshold]
    return gm_score, i
    

# %% ../03_Boostrap_correlation.ipynb 35
def single_iteration_bootstrap_cc(seqcell, populations, samples_bootstrap, metadata, threshold=1):
    g0_digprof = bootstrap_population(seqcell, populations[0], samples_bootstrap, metadata)
    inter_digprof = bootstrap_population(seqcell, populations[1], samples_bootstrap, metadata)

    # filter low mean counts
    gmean, idx = gmean_filter(g0_digprof, inter_digprof, threshold=threshold)
    g0_digprof = g0_digprof.loc[idx, :]
    inter_digprof = inter_digprof.loc[idx, :]
    
    # pearson coefficient
    ddof = g0_digprof.shape[1] -1
    g0_digprof = g0_digprof.sub(g0_digprof.mean(axis=1), axis=0).div(g0_digprof.std(axis=1, ddof=ddof), axis=0)
    inter_digprof = inter_digprof.sub(inter_digprof.mean(axis=1), axis=0).div(inter_digprof.std(axis=1, ddof=ddof), axis=0)
    
    cc = cross_correlation_on_all_sequences(g0_digprof, inter_digprof)
    return cc


# %% ../03_Boostrap_correlation.ipynb 38
def iter_bootstrap_cc(seqcell, metadata, populations= [0,1], samples_bootstrap=200, n_iter=100, threshold=1):    
    cross_correlations = []

    for _ in range(n_iter):
        cc = single_iteration_bootstrap_cc(seqcell, populations, samples_bootstrap, metadata, threshold=threshold)
        cross_correlations.append(cc)
        
    return cross_correlations


# %% ../03_Boostrap_correlation.ipynb 40
def average_results_bootstrap(cross_correlations):
    cat_correlations = pd.concat(cross_correlations, axis=0, join='inner')
    mean_cc = cat_correlations.groupby(cat_correlations.index).mean()
    se_cc = cat_correlations.groupby(cat_correlations.index).sem()
    max_cc = mean_cc.idxmax(axis = 1)
    return mean_cc, se_cc, max_cc

# %% ../03_Boostrap_correlation.ipynb 44
def aggregate_results_bootstrap(cross_correlations, aggregations=['mean', 'var'], min_obs=1):
    cat_correlations = pd.concat(cross_correlations, axis=0, join='inner')
    group_seq = cat_correlations.groupby(cat_correlations.index)
    # filter sequences with low observation
    count_sequences = group_seq.count().iloc[:,1]
    sequences_to_keep = count_sequences.index[count_sequences > min_obs]
    agg_cc = group_seq.aggregate(aggregations)
    return agg_cc.loc[sequences_to_keep, :]
