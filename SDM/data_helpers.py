import random

import pandas as pd
import numpy as np
import torch
import tifffile as tiff

from torch.utils.data import Dataset

elith_data_dir = 'data/Records/'
valavi_bg_dir = 'data/Valavi_DataS1/background_50k/'
rasters_dir = 'data/Environment'

region_list = ['AWT', 'CAN', 'NSW', 'NZ', 'SA', 'SWI','ECOPAL']
group_dictionary = {
    'AWT': ['bird', 'plant'],
    'CAN': [],
    'NSW': ['ba', 'db', 'nb', 'ot', 'ou', 'rt', 'ru', 'sr'],
    'NZ': [],
    'SA': [],
    'SWI': [],
    'ECOPAL': []
}

# Covariates of Elith et al. 2020
covariate_dictionary = {
    'AWT': ['bc01', 'bc04', 'bc05', 'bc06', 'bc12', 'bc15', 'bc17', 'bc20', 'bc31', 'bc33', 'slope', 'topo', 'tri'],
    'CAN': ['alt', 'asp2', 'ontprec', 'ontprec4', 'ontprecsd', 'ontslp', 'onttemp', 'onttempsd', 'onttmin4', 'ontveg', 'watdist'],
    'NSW': ['cti', 'disturb', 'mi', 'rainann', 'raindq', 'rugged', 'soildepth', 'soilfert', 'solrad', 'tempann', 'tempmin', 'topo', 'vegsys'],
    'NZ': ['age', 'deficit', 'dem', 'hillshade', 'mas', 'mat', 'r2pet', 'rain', 'slope', 'sseas', 'toxicats', 'tseas', 'vpd'],
    'SA': ['sabio1', 'sabio2', 'sabio4', 'sabio5', 'sabio6', 'sabio7', 'sabio12', 'sabio15', 'sabio17', 'sabio18',],
    'SWI': ['bcc', 'calc', 'ccc', 'ddeg', 'nutri', 'pday', 'precyy', 'sfroyy', 'slope', 'sradyy', 'swb', 'tavecc', 'topo'],
    "ECOPAL": [
    "bio01", "bio02", "bio03", "bio04", "bio07", "bio12", "bio13", "bio14", "bio15",
    "bio18", "bio19", "slope", "aspect", "hillshade","tri","watdist","landcover"]

}

# Covariates of Valavi et al. 2022
valavi_covariate_dictionary = {
    'AWT': ['bc04', 'bc05', 'bc06', 'bc12', 'bc15', 'slope', 'topo', 'tri'],
    'CAN': ['alt', 'asp2', 'ontprec', 'ontslp', 'onttemp', 'ontveg', 'watdist'],
    'NSW': ['cti', 'disturb', 'mi', 'rainann', 'raindq', 'rugged', 'soildepth', 'soilfert', 'solrad', 'tempann', 'topo', 'vegsys'],
    'NZ': ['age', 'deficit', 'hillshade', 'mas', 'mat', 'r2pet', 'slope', 'sseas', 'toxicats', 'tseas', 'vpd'],
    'SA': ['sabio12', 'sabio15', 'sabio17', 'sabio18', 'sabio2', 'sabio4', 'sabio5', 'sabio6'],
    'SWI': ['bcc', 'calc', 'ccc', 'ddeg', 'nutri', 'pday', 'precyy', 'sfroyy', 'slope', 'sradyy', 'swb', 'topo'],
    "ECOPAL": [
    "bio01", "bio02", "bio03", "bio04", "bio07", "bio12", "bio13", "bio14", "bio15",
    "bio18", "bio19", "slope", "aspect", "hillshade","tri","watdist","landcover"]

}

# Same for Valavi et al. 2022 and Elith et al. 2020
categorical_covariates = { 
    'AWT': [],
    'CAN': ['ontveg'], 
    'NSW': ['vegsys'], 
    'NZ': [], #'age', 'toxicats' are ordinal variables -> no one hot encoding
    'SA': [],
    'SWI': [], #'calc' is binary, no need to one hot encode
    'ECOPAL': []
}

covariate_dictionary['ECOPAL'] = valavi_covariate_dictionary['ECOPAL']
categorical_covariates['ECOPAL'] = []
group_dictionary['ECOPAL'] = []

class SpeciesDataset(Dataset):

    def __init__(self, x, y, bg):
        self.x = x
        self.y = y
        self.bg = bg
        self.length = len(self.x)
        self.num_bg = len(self.bg)
    
    def __getitem__(self, idx):
        idx_bg = random.randint(0, self.num_bg - 1)
        return self.x[idx], self.y[idx], self.bg[idx_bg]
    
    def __len__(self):
        return self.length
    
    
def get_data_one_region(region, co_occurrence=True, valavi=False):
    """Get data for a given region. Co_occurence equals to True implies that species presences 
        at the same location are merged. Valavi equals to True implies that the covariates of 
        Valavi et al. 2022 are used."""
    
    covs = get_covariates(region, valavi=valavi)
    cat_covs = categorical_covariates[region]
    
    # Get presence-only occurrence records
    train = pd.read_csv(elith_data_dir + 'train_po/' + region + 'train_po.csv')
    train = train[['spid'] + covs + ["x", "y"]].reset_index(drop=True)
    
    # One hot encoding of categorical variables to obtain x_train (covariates)
    x_train = pd.get_dummies(train, columns=cat_covs).drop(["spid"], axis=1)
    if co_occurrence:
        # Merge species at same location (same covariates by definition)
        x_train = x_train.groupby(["x", "y"]).mean().reset_index()
    coordinates_train = x_train[["x", "y"]].to_numpy()
    x_train = x_train.drop(["x", "y"], axis=1)
    x_train = x_train.to_numpy()
    
    # Encode the presence into a binary vector to obtain y_train
    y_train = pd.get_dummies(train, columns=['spid']).drop(covs, axis=1)
    if co_occurrence:
        # Merge species at same location
        y_train = y_train.groupby(["x", "y"]).sum().reset_index()
    y_train = y_train.drop(["x", "y"], axis=1)
    y_train = y_train.to_numpy().clip(0, 1)
    
    # Get random background points
    bg = pd.read_csv(valavi_bg_dir + region + '.csv')
    coordinates_bg = bg[['x', 'y']].values
    bg = pd.get_dummies(bg[covs], columns=cat_covs).to_numpy()
    
    # Presence-absence and covariates
    groups = group_dictionary[region]
    if len(groups) > 0:
        test_pa_list = []
        test_env_list = []
        for group in groups:
            test_pa_list.append(pd.read_csv(elith_data_dir + 'test_pa/' + region + 'test_pa_' + group + '.csv'))
            test_env_list.append(pd.read_csv(elith_data_dir + 'test_env/' + region + 'test_env_' + group + '.csv'))
        test_pa = pd.concat(test_pa_list)
        test_env = pd.concat(test_env_list)
    else:
        test_pa = pd.read_csv(elith_data_dir + 'test_pa/' + region + 'test_pa.csv')
        test_env = pd.read_csv(elith_data_dir + 'test_env/' + region + 'test_env.csv')

    # Ensure consistent siteids between test_env and test_pa
    # Merge test_env and test_pa on 'siteid' using an inner merge to keep only siteids present in both dataframes
    test_data = pd.merge(test_env, test_pa, on='siteid', how='inner')
    test_data = test_data.sort_values('siteid')

    # Extract x_test, y_test, and coordinates_test from the merged dataframe
    x_test = np.array(pd.get_dummies(test_data[covs], columns=cat_covs))
    y_test = np.array(test_data[get_species_list(region, remove=False)])
    coordinates_test = np.array(test_data[["x", "y"]])
    
    return x_train, y_train, coordinates_train, x_test, y_test, coordinates_test, bg, coordinates_bg



def one_hot_covariates(x, region, valavi=False):
    """One-hot encodes the covariates of the given region. Valavi equals to True
       implies that the covariates of Valavi et al. 2022 are used."""
    
    covs = get_covariates(region, valavi=valavi)
    cat_covs = categorical_covariates[region]
    
    x = pd.DataFrame(x, columns=covs)
    x = pd.get_dummies(x, columns=cat_covs).to_numpy()
    
    return x


def get_species_list(region, remove=True):
    """Returns the list of species for the given region."""
    species = list(pd.read_csv(elith_data_dir + 'train_po/' + region + 'train_po.csv')['spid'].unique())
    if region == 'NSW' and remove: 
        species.remove('nsw30') # species with only 2 occurrences in train
    return species


def get_covariates(region, valavi=True):
    """Returns the list of covariates for a given region."""
    
    if valavi:
        covs = valavi_covariate_dictionary[region]
    else:
        covs = covariate_dictionary[region]
    
    return covs


def get_rasters(region, valavi=False):
    """Get rasters of the given region. 
    
    :returns rasters: numpy array of shape #covariates x height x width"""
    
    rasters = []
    raster_files_paths = [f'{rasters_dir}/{region}/{covariate}.tif' for covariate in get_covariates(region, valavi=valavi)]
    for raster_file_path in raster_files_paths:
        rasters.append(np.array(tiff.imread(raster_file_path)))
    
    rasters = np.stack(rasters)
    
    return rasters
    

def get_all_bg(rasters):
    """Get all the point locations of the raster. 
    
    :returns bg_points: numpy array of shape #locations x #covariates"""

    # Heuristic: we consider the first pixel of the first covariate 
    # as being outside of the polygon. It has been verified for the 6 regions.
    mask = np.logical_not(rasters[0] == rasters[0, 0, 0])
    
    bg_points = rasters[:, mask].swapaxes(0, 1)
        
    return bg_points
