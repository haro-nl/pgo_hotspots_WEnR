# Script to convert ASCII grid data to database format. Used for PLANT and VOGEL data
# Hans Roelofsen, WEnR, 25/03/2019


import os
import numpy as np
import rasterio as rio
import pandas as pd
import datetime

from utils import pgo

# Run for all ascii files in vaatplanten
vaatplant_dir = r'd:\hotspot_working\b_vaatplanten\Soortenrijkdom'
holder = []
for file in os.listdir(vaatplant_dir):
    if file.endswith('asc') and file.startswith('vaatplant') and os.path.isfile(os.path.join(vaatplant_dir, file)):
        print('{0} in progress'.format(file))
        foo = pgo.ascii_species_grid_to_pd(vaatplant_dir, file)
        print('\tDone with {0} rows at {1}'.format(foo.shape[0], datetime.datetime.now().strftime("%H:%M:%S")))
        holder.append(foo)
    else:
        print('{0} is not a valid input'.format(file))
        continue

df_all = pd.concat(holder)
df_all.to_csv(os.path.join(vaatplant_dir, 'vaatplant_all2.csv'), index=False, sep=';')
del df_all

# # Run for all ascii files in broedvogels
vogel_dir = r'd:\hotspot_working\a_broedvogels\Soortenrijkdom\Species_richness'
holder = []
for file in os.listdir(vogel_dir):

    if file.endswith('asc') and file.startswith('vogel') and os.path.isfile(os.path.join(vogel_dir, file)):
        print('{0} in progress'.format(file))
        foo = pgo.ascii_species_grid_to_pd(vogel_dir, file)
        print('\tDone with {0} rows at {1}'.format(foo.shape[0], datetime.datetime.now().strftime("%H:%M:%S")))
        holder.append(foo)
    else:
        print('{0} is not a valid input'.format(file))
        continue

df_all = pd.concat(holder)
df_all.to_csv(os.path.join(vogel_dir, 'vogel_all2.csv'), index=False, sep=';')

# Run for all SNL grids
snl_dir = r'd:\hotspot_working\a_broedvogels\SNL_grids'
for file in os.listdir(snl_dir):
    if file.endswith('asc') and os.path.isfile(os.path.join(snl_dir, file)):
        print('{0} in progress'.format(file))
        foo = ascii_snl_grid_to_pd(snl_dir, file)
        foo.to_pickle(os.path.join(snl_dir, 'augurken', os.path.splitext(file)[0] + '.pkl'))
