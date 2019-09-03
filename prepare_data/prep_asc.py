# Script to convert ASCII grid data to database format. Used for PLANT and VOGEL data
# Hans Roelofsen, WEnR, 25/03/2019


import os
import pandas as pd
import datetime
import pickle
import geopandas as gp

from utils import pgo

# Run for all ascii files in vaatplanten
vaatplant_dir = r'd:\hotspot_working\b_vaatplanten\Soortenrijkdom'
i = 0
with open(os.path.join(vaatplant_dir, 'vaatplant_all_snl.csv'), 'w') as f:
    for file in os.listdir(vaatplant_dir):
        if file.endswith('asc') and file.startswith('vaatplant') and os.path.isfile(os.path.join(vaatplant_dir, file))\
                and 'SNL' in file:
            print('{0} in progress'.format(file))
            foo = pgo.ascii_species_grid_to_pd(vaatplant_dir, file)
            print('\tDone with {0} rows at {1}'.format(foo.shape[0], datetime.datetime.now().strftime("%H:%M:%S")))
            # holder.append(foo)
            if i == 0:
                f.write('# Deze tabel bevat alle informatie uit alle *SNL*.asc bestanden '
                        'in d:\hotspot_working\b_vaatplanten\Soortenrijkdom\n')
                f.write('# Deze bestanden zijn gebasseerd op de data levering van Kampichler 11 juni 2019\n')
                f.write('# Hans Roelofsen, WEnR BB, 04 Jul 2019\n')
                f.write(foo.to_csv(sep=';', header=True, index=False))
            else:
                f.write(foo.to_csv(sep=';', header=False, index=False))
            i = + 1
        else:
            print('{0} is not a valid input'.format(file))
            continue

# df_all = pd.concat(holder)
# df_all.to_csv(os.path.join(vaatplant_dir, 'vaatplant_all3.csv'), index=False, sep=';')
# del df_all

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
df_all.to_csv(os.path.join(vogel_dir, 'vogel_all4.csv'), index=False, sep=';')

# Run for all SNL grids
snl_dir = r'd:\hotspot_working\a_broedvogels\SNL_grids'
for file in os.listdir(snl_dir):
    if file.endswith('asc') and os.path.isfile(os.path.join(snl_dir, file)):
        print('{0} in progress'.format(file))
        foo = pgo.ascii_snl_grid_to_pd(snl_dir, file)
        foo.to_pickle(os.path.join(snl_dir, 'augurken', os.path.splitext(file)[0] + '.pkl'))

# 250m hok <-> provincie pandas dataframe to pkl
prov = gp.read_file(r'd:\hotspot_working\shp_250mgrid\hok250m_prov2018.shp')
prov.rename(columns={'ID': 'hok_id'}, inplace=True)
prov.drop(['topleftx', 'toplefty', 'geometry'], axis=1).to_pickle(os.path.join(snl_dir, 'augurken', 'provincien2.pkl'))