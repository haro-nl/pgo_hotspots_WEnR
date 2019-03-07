import os
import numpy as np
import rasterio as rio
import pandas as pd
import datetime

asc_in = r'd:\hotspot_working\vaatplanten\Soortenrijkdom\vaatplant_Bos_1994-2001.asc'

# save image specs to dict

def get_specs(dir_in, asc_in):
    specs = {}
    with open(os.path.join(dir_in, asc_in), 'r') as f:
        for line in f.readlines():
            if not line.startswith('-9999'):
                specs[line.split(' ')[0]] = line.split(' ')[1]
    for k,v in specs.items():
        specs[k] = np.int32(np.float32(v))
    return specs

def ascii_grid_to_pd(dir_in, asc_in):
    groep, snl, periode = os.path.splitext(asc_in)[0].split('_')

    specs = get_specs(dir_in, asc_in)
    asc = rio.open(os.path.join(dir_in, asc_in))

    vals = np.reshape(asc.read(1), newshape=np.product(asc.shape), order='C').astype(np.int16)

    db = pd.DataFrame({'n_{0}'.format(groep): vals, 'snl':snl, 'periode':periode})
    db['row'] = np.array([[i] * specs['NCOLS'] for i in range(0, specs['NROWS'])]).reshape(np.product(asc.shape))
    db['col'] = np.array([i for i in range(0, specs['NCOLS'])] * specs['NROWS']).reshape(np.product(asc.shape))
    db.drop(db.loc[(db['n_{0}'.format(groep)] == specs['NODATA_value']) | (db['n_{0}'.format(groep)] == 0)].index,
            axis=0, inplace=True)
    db['x_rd'] = db.apply(lambda x: ((x.col, x.row) * asc.affine)[0], axis=1).astype(np.int32)
    db['y_rd'] = db.apply(lambda x: ((x.col, x.row) * asc.affine)[1], axis=1).astype(np.int32)
    db['hok_id'] = db.apply(lambda x: str(x.x_rd) + '_' + str(x.y_rd), axis=1)
    return db

holder = []

vaatplant_dir = r'd:\hotspot_working\broedvogels\Soortenrijkdom'
for file in os.listdir(vaatplant_dir):
    if file.endswith('asc') and file.startswith('broedvogel'):
        print('{0} in progress'.format(file))
        foo = ascii_grid_to_pd(vaatplant_dir, file)
        print('\tDone with {0} rows at {1}'.format(foo.shape[0], datetime.datetime.now().strftime("%H:%M:%S")))
        holder.append(foo)

df_all = pd.concat(holder)
df_all.to_csv(os.path.join(vaatplant_dir, '{0}_all.csv'.format(XXX)), index=False, sep=';')


#TODO voor dagvlinders:
# col_row = ~affine *(easting, northing), afgerond naar beneden!
# dan: cellID =  {0}_{1}.format(a * (col,row)[0], a*(col,row)[1])

