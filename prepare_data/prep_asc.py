# Script to convert ASCII grid data to database format. Used for PLANT and VOGEL data
# Hans Roelofsen, WEnR, 25/03/2019


import os
import numpy as np
import rasterio as rio
import pandas as pd
import datetime

asc_in = r'd:\hotspot_working\vaatplanten\Soortenrijkdom\vaatplant_Bos_1994-2001.asc'

def get_specs(dir_in, asc_in):
    # Return specs of ASC grid file as a dictionary
    specs = {}
    with open(os.path.join(dir_in, asc_in), 'r') as f:
        for line in f.readlines():
            if not line.startswith('-9999'):
                specs[line.split(' ')[0]] = line.split(' ')[1]
    for k,v in specs.items():
        specs[k] = np.int32(np.float32(v))
    return specs

def ascii_grid_to_pd(dir_in, asc_in):
    # Convert ascii grid to pandas dataframe
    groep, snl, soortlijst, periode = os.path.splitext(asc_in)[0].split('_')

    specs = get_specs(dir_in, asc_in)
    asc = rio.open(os.path.join(dir_in, asc_in))

    # reshape grid nrows*ncols to list of length nrows*ncols
    # order = 'C' means that values are read per row, ie last index changes fastest!
    vals = np.reshape(asc.read(1), newshape=np.product(asc.shape), order='C').astype(np.int16)

    db = pd.DataFrame({'n': vals, 'soortgroep': groep, 'snl':snl, 'periode':periode, 'soortlijst':soortlijst})
    # row indices range from 0 up to and including specs['NROWS'] -1
    # col indices range from 0 up to and including specs['NCOLS'] -1
    # although row, col indices are integers (ie 'blocks'), note that row, col (0,0) refers to cell top-left in
    # Cartesian space
    db['row'] = np.array([[i] * specs['NCOLS'] for i in range(0, specs['NROWS'])]).reshape(np.product(asc.shape))
    db['col'] = np.array([i for i in range(0, specs['NCOLS'])] * specs['NROWS']).reshape(np.product(asc.shape))
    db.drop(db.loc[(db['n'] == specs['NODATA_value']) | (db['n'] == 0)].index, axis=0, inplace=True)
    # note that coordinates are calculated for the row,col indices, which means they apply to the cell top-left!
    db['x_rd'] = db.apply(lambda x: ((x.col, x.row) * asc.affine)[0], axis=1).astype(np.int32)
    db['y_rd'] = db.apply(lambda x: ((x.col, x.row) * asc.affine)[1], axis=1).astype(np.int32)
    db['hok_id'] = db.apply(lambda x: str(x.x_rd) + '_' + str(x.y_rd), axis=1)
    return db

# Run for all ascii files in vaatplanten
vaatplant_dir = r'd:\hotspot_working\b_vaatplanten\Soortenrijkdom'
holder = []
for file in os.listdir(vaatplant_dir):
    if file.endswith('asc') and file.startswith('vaatplant') and os.path.isfile(os.path.join(vaatplant_dir, file)):
        print('{0} in progress'.format(file))
        foo = ascii_grid_to_pd(vaatplant_dir, file)
        print('\tDone with {0} rows at {1}'.format(foo.shape[0], datetime.datetime.now().strftime("%H:%M:%S")))
        holder.append(foo)
    else:
        print('{0} is not a valid input'.format(file))
        continue

df_all = pd.concat(holder)
df_all.to_csv(os.path.join(vaatplant_dir, 'vaatplant_all2.csv'), index=False, sep=';')
del df_all

# Run for all ascii files in broedvogels
vogel_dir = r'd:\hotspot_working\a_broedvogels\Soortenrijkdom\Species_richness'
holder = []
for file in os.listdir(vogel_dir):

    if file.endswith('asc') and file.startswith('vogel') and os.path.isfile(os.path.join(vogel_dir, file)):
        print('{0} in progress'.format(file))
        foo = ascii_grid_to_pd(vogel_dir, file)
        print('\tDone with {0} rows at {1}'.format(foo.shape[0], datetime.datetime.now().strftime("%H:%M:%S")))
        holder.append(foo)
    else:
        print('{0} is not a valid input'.format(file))
        continue


df_all = pd.concat(holder)
df_all.to_csv(os.path.join(vogel_dir, 'vogel_all2.csv'), index=False, sep=';')



