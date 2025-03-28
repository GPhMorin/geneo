import pandas as pd
import numpy as np
import cgeneo
from .extract import branching

# Describe a pedigree

def noind(gen):
    number_of_individuals = cgeneo.get_number_of_individuals(gen)
    return number_of_individuals

def nomen(gen):
    number_of_men = cgeneo.get_number_of_men(gen)
    return number_of_men

def nowomen(gen):
    number_of_women = cgeneo.get_number_of_women(gen)
    return number_of_women

def depth(gen):
    pedigree_depth = cgeneo.get_pedigree_depth(gen)
    return pedigree_depth

def min(gen, individuals):
    minima = cgeneo.get_min_ancestor_path_lengths(gen, individuals)
    df = pd.DataFrame([minima], index=['min'], columns=individuals, copy=False)
    return df

def mean(gen, individuals):
    means = cgeneo.get_mean_ancestor_path_lengths(gen, individuals)
    df = pd.DataFrame([means], index=['mean'], columns=individuals, copy=False)
    return df

max_ = max

def max(gen, individuals):
    maxima = cgeneo.get_max_ancestor_path_lengths(gen, individuals)
    df = pd.DataFrame([maxima], index=['max'], columns=individuals, copy=False)
    return df

def meangendepth(gen, **kwargs):
    pro = kwargs.get('pro', None)
    if pro is None:
        pro = cgeneo.get_proband_ids(gen)
    type = kwargs.get('type', 'MEAN')
    data = cgeneo.get_mean_pedigree_depths(gen, pro)
    if type == 'MEAN':
        return np.mean(data)
    elif type == 'IND':
        df = pd.DataFrame(data, index=pro, columns=['Exp.Gen.Depth'],
                          copy=False)
        return df

def get_generational_counts(gen, pro):
    current_gen = pro
    vctF = []
    vctDF = []

    while current_gen:
        founders = 0
        semi_founders = 0
        next_gen = []
        
        for ind in current_gen:
            father = gen[ind].father.ind
            mother = gen[ind].mother.ind
            
            if father == 0 and mother == 0:
                founders += 1
            elif (father == 0) != (mother == 0):  # Logical XOR for semi-founders
                semi_founders += 1
            
            # Collect parents for next generation
            if father != 0:
                next_gen.append(father)
            if mother != 0:
                next_gen.append(mother)
        
        vctF.append(founders)
        vctDF.append(semi_founders)
        current_gen = list(next_gen)

    return vctF, vctDF

def variance3V(gen, pro=None):
    if pro is None:
        pro = cgeneo.get_proband_ids(gen)
    N = len(pro)
    if N == 0:
        return 0.0

    vctF, vctDF = get_generational_counts(gen, pro)
    
    P = 0.0
    sum_sq = 0.0
    
    for genNo in range(len(vctF)):
        weight = N * (2 ** genNo)
        if weight == 0:
            continue
        
        # Founder contribution
        termF = (genNo * vctF[genNo]) / weight
        P += termF
        sum_sq += (genNo ** 2 * vctF[genNo]) / weight
        
        # Semi-founder contribution (0.5 weight)
        termDF = (genNo * vctDF[genNo] * 0.5) / weight
        P += termDF
        sum_sq += (genNo ** 2 * vctDF[genNo] * 0.5) / weight
    
    variance = sum_sq - (P ** 2)
    return variance

def meangendepthVar(gen, **kwargs):
    pro = kwargs.get('pro', None)
    if pro is None:
        pro = cgeneo.get_proband_ids(gen)
    type = kwargs.get('type', 'MEAN')
    if type == 'MEAN':
        variance = variance3V(gen, pro=pro)
        return variance
    elif type == 'IND':
        variances = [variance3V(branching(gen, pro=[ind])) for ind in pro]
        return pd.DataFrame(
            variances,
            columns=["Mean.Gen.Depth"],
            index=pro
        )
    
def nochildren(gen, individuals):
    number_of_children = cgeneo.get_number_of_children(gen, individuals)
    return number_of_children

def completeness(gen, **kwargs):
    pro = kwargs.get('pro', None)
    genNo = kwargs.get('genNo', None)
    type = kwargs.get('type', 'MEAN')
    if pro is None:
        pro = cgeneo.get_proband_ids(gen)
    if type == 'MEAN':
        data = cgeneo.compute_mean_completeness(gen, pro)
        pedigree_completeness = pd.DataFrame(
            data, columns=['mean'], copy=False)
    elif type == 'IND':
        data = cgeneo.compute_individual_completeness(gen, pro)
        pedigree_completeness = pd.DataFrame(
            data, columns=pro, copy=False)
    if genNo is None:
        return pedigree_completeness
    else:
        return pedigree_completeness.iloc[genNo, :]
    
def completenessVar(gen, **kwargs):
    """
    Computes the variance of the completeness index across probands for each generation.
    Matches R's var() calculation (sample variance) using ddof=1.
    """
    pro = kwargs.get('pro', None)
    genNo = kwargs.get('genNo', None)
    
    if pro is None:
        pro = cgeneo.get_proband_ids(gen)
    
    # Get individual completeness matrix (generations x probands)
    data = cgeneo.compute_individual_completeness(gen, pro)
    
    # Compute sample variance (matching R's var()) using ddof=1
    variances = np.var(data, axis=1, ddof=1)
    
    # Create DataFrame with generations as index
    generations = np.arange(data.shape[0])
    df = pd.DataFrame({'completeness.var': variances}, index=generations)
    
    # Filter specific generations if genNo is provided
    if genNo is not None:
        df = df.loc[genNo, :]
    
    return df

def implex(gen, **kwargs):
    pro = kwargs.get('pro', None)
    if pro is None:
        pro = cgeneo.get_proband_ids(gen)
    genNo = kwargs.get('genNo', None)
    type = kwargs.get('type', 'MEAN')
    onlyNewAnc = kwargs.get('onlyNewAnc', False)
    if type == 'MEAN':
        data = cgeneo.compute_mean_implex(gen, pro, onlyNewAnc)
        pedigree_implex = pd.DataFrame(
            data, columns=['mean'], copy=False)
    elif type == 'IND':
        data = cgeneo.compute_individual_implex(gen, pro, onlyNewAnc)
        pedigree_implex = pd.DataFrame(
            data, columns=pro, copy=False)
    if genNo is None:
        return pedigree_implex
    else:
        return pedigree_implex.iloc[genNo, :]
    
def implexVar(gen, **kwargs):
    """
    Computes the variance of the implex index across probands for each generation.
    Matches R's var() calculation (sample variance) using ddof=1.
    
    Parameters:
    - gen: The pedigree object
    - pro (list): List of proband IDs (default: all probands)
    - genNo (list): Specific generations to include (default: all)
    - onlyNewAnc (bool): Whether to count only new ancestors (default: False)
    
    Returns:
    - pd.DataFrame: Variance of implex per generation
    """
    pro = kwargs.get('pro', None)
    genNo = kwargs.get('genNo', None)
    only_new_anc = kwargs.get('onlyNewAnc', False)
    
    if pro is None:
        pro = cgeneo.get_proband_ids(gen)
    
    # Get individual implex matrix (generations x probands)
    data = cgeneo.compute_individual_implex(gen, pro, only_new_anc)
    
    # Compute sample variance (matching R's var()) using ddof=1
    variances = np.var(data, axis=0, ddof=1)
    
    # Create DataFrame with generations as index
    generations = np.arange(data.shape[1])
    df = pd.DataFrame({'implex.var': variances}, index=generations)
    
    # Filter specific generations if genNo is provided
    if genNo is not None:
        df = df.loc[genNo, :]
    
    return df

def occ(gen, **kwargs):
    pro = kwargs.get('pro', None)
    ancestors = kwargs.get('ancestors', None)
    if pro is None:
        pro = cgeneo.get_proband_ids(gen)
    if ancestors is None:
        ancestors = cgeneo.get_founder_ids(gen)
    typeOcc = kwargs.get('typeOcc', 'IND')
    if typeOcc == 'TOTAL':
        data = cgeneo.count_total_occurrences(gen, ancestors, pro)
        pedigree_occurrence = pd.DataFrame(
            data, index=ancestors, columns=['total'], copy=False)
    elif typeOcc == 'IND':
        data = cgeneo.count_individual_occurrences(gen, ancestors, pro)
        pedigree_occurrence = pd.DataFrame(
            data, index=ancestors, columns=pro, copy=False)
    return pedigree_occurrence

def rec(gen, **kwargs):
    pro = kwargs.get('pro', None)
    ancestors = kwargs.get('ancestors', None)
    if pro is None:
        pro = cgeneo.get_proband_ids(gen)
    if ancestors is None:
        ancestors = cgeneo.get_founder_ids(gen)
    data = cgeneo.count_coverage(gen, pro, ancestors)
    coverage = pd.DataFrame(
        data, index=ancestors, columns=['coverage'], copy=False)
    return coverage

def findDistance(gen, individuals, ancestor):
    distance = cgeneo.get_min_common_ancestor_path_length(
        gen, individuals[0], individuals[1], ancestor)
    return distance