#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Ed Mountjoy
#

import subprocess as sp
import os
import pandas as pd

def get_conditional_top_loci(sumstats, in_plink, temp_dir,
        maf=0.01,
        cojo_p=5e-8,
        cojo_window=500,
        cojo_collinear=0.9
    ):
    ''' Uses GCTA-cojo to perform conditional analysis
    Args:

    '''

    # Extract filename prefix and chrom number
    chrom = str(sumstats.head(1)['chrom'].values[0])
    file_pref = make_file_name_prefix(sumstats.head(1))
    gcta_in = os.path.join(temp_dir, '{0}.gcta_format.tsv'.format(file_pref))
    gcta_out = os.path.join(temp_dir, '{0}.gcta_out'.format(file_pref))

    # Write sumstats
    sumstat_to_gcta(sumstats, gcta_in, p_threshold=cojo_p)

    # Construct command
    cmd = [
           'gcta64 --bfile {0}'.format(in_plink.format(chrom=chrom)),
           '--chr {0}'.format(chrom),
           '--maf {0}'.format(maf),
           '--cojo-p {0}'.format(cojo_p),
           '--cojo-wind {0}'.format(cojo_window),
           '--cojo-collinear {0}'.format(cojo_collinear),
           '--cojo-file {0}'.format(gcta_in),
           '--cojo-slct',
           '--out {0}'.format(gcta_out)
           ]

    # Run command
    fnull = open(os.devnull, 'w')
    cp = sp.run(' '.join(cmd), shell=True, stdout=fnull, stderr=sp.STDOUT)
    assert cp.returncode == 0

    # Read results (if they exist)
    gcta_res = '{0}.jma.cojo'.format(gcta_out)
    if os.path.exists(gcta_res):
        selected_snps = pd.read_csv(gcta_res, sep='\t', header=0)['SNP'] \
                          .str.replace(':', '_')
    else:
        selected_snps = []

    # Filter and return selected variants
    top_loci = sumstats.loc[sumstats['variant_id'].isin(selected_snps), :]

    return top_loci

def perfrom_conditional_adjustment(sumstats, in_plink, temp_dir, index_var,
        chrom, condition_on):
    ''' Uses GCTA-cojo to perform conditional analysis
    Args:
        sumstats (pd.df)
        in_plink (str)
        temp_dir (str)
        index_var (str)
        chrom (str)
        condition_on (list): list of variants to condition on
    Return:
        pd.df of conditionally adjusted summary stats
    '''
    # Extract filename prefix and chrom number
    file_pref = make_file_name_prefix(sumstats.head(1))
    gcta_in = os.path.join(temp_dir, '{0}.{1}.gcta_format.tsv'.format(
        file_pref,
        index_var))
    gcta_out = os.path.join(temp_dir, '{0}.{1}.gcta_out'.format(
        file_pref,
        index_var))

    # Write sumstats
    sumstat_to_gcta(sumstats, gcta_in)

    # Write a conditional list
    gcta_cond = os.path.join(temp_dir, '{0}.{1}.cond_list.txt'.format(
        file_pref,
        index_var))
    write_cond_list(condition_on, gcta_cond)

    # Constuct command
    cmd =  [
        'gcta64 --bfile {0}'.format(in_plink.format(chrom=chrom)),
        '--chr {0}'.format(chrom),
        '--cojo-file {0}'.format(gcta_in),
        '--cojo-cond {0}'.format(gcta_cond),
        '--out {0}'.format(gcta_out)
    ]

    # Run command
    fnull = open(os.devnull, 'w')
    cp = sp.run(' '.join(cmd), shell=True, stdout=fnull, stderr=sp.STDOUT)
    assert cp.returncode == 0

    # Read output
    gcta_res = '{0}.cma.cojo'.format(gcta_out)
    cond_res = pd.read_csv(gcta_res, sep='\t', header=0)

    # Merge to sumstats
    sumstat_cond = merge_conditional_w_sumstats(sumstats, cond_res)

    return sumstat_cond

def merge_conditional_w_sumstats(sumstats, cond_res):
    ''' Adds the results of the conditional analysis as columns to the
        summary stats
    Args:
        sumstats (pd.df)
        cond_res (pd.df)
    Returns:
        pd.df of sumstats
    '''
    # Make a variant_id key on the conditional results
    cond_res['variant_id'] = cond_res['SNP'].str.replace(':', '_')
    # Merge
    merged = pd.merge(
        sumstats,
        cond_res.loc[:, ['variant_id', 'bC', 'bC_se', 'pC']],
        on='variant_id',
        how='inner'
    )
    return merged.rename(columns={
        'bC':'beta_cond',
        'bC_se':'se_cond',
        'pC':'pval_cond',
    })

def write_cond_list(cond_list, outf):
    ''' Write a list of variants to a file
    '''
    with open(outf, 'w') as out_h:
        for var in cond_list:
            out_h.write(var.replace('_', ':') + '\n')
    return outf

def sumstat_to_gcta(sumstats, outf, p_threshold=None):
    ''' Writes a sumstat df as a GCTA compliant file
    Args:
        sumstats (pd.df)
        outf (str): location to write to
        min_p (float): only write rows with p < p_threshold
    '''
    # Make temp dir if it doesn't exist
    os.makedirs(os.path.split(outf)[0], exist_ok=True)

    # Rename and extract required columns
    outdata = sumstats.rename(
        columns={"variant_id":"SNP",
                 "alt_al":"A1",
                 "ref_al":"A2",
                 "eaf":"freq",
                 "beta":"b",
                 "pval":"p",
                 "n_samples":"N"})
    outdata = outdata.loc[:, ["SNP", "A1", "A2", "freq", "b", "se", "p", "N"]]

    # Remove rows where p > p_threshold
    if p_threshold:
        outdata = outdata.loc[outdata['p'] <= p_threshold, :]

    # Convert SNP name to match plink file
    outdata['SNP'] = outdata['SNP'].str.replace('_', ':')

    # Save
    outdata.to_csv(outf, sep='\t', index=None)

    return 0

def make_file_name_prefix(row):
    ''' Takes a row of the sumstat dataframe and creates a unique file prefix
    Args:
        row (dask Series)
    Return:
        str
    '''
    cols = ['study_id', 'cell_id', 'group_id', 'trait_id', 'chrom']
    pref = '_'.join([str(x) for x in row[cols].values[0]])
    return pref
