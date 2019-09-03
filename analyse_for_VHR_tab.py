#======================================================================================================================#
# Script for analysing PGO hotspot data and delivering in rich-table format with hok_ids as rows and nested columns as:
# hok_id|Soortgroep      |snl_type_areaal|provincie
#          \Periode
#             \Soortlijst
#             <n soorten>
#
# Soortlijst is here restricted to VHR soorten. SNL type is irrelavant
#
# By Hans Roelofsen, WEnR, 29/04/2019
#
#======================================================================================================================#

import os
import geopandas as gp
import pandas as pd
import warnings
import numpy as np

from utils import pgo

#======================================================================================================================#
# define data selection and specification of difference map categories
soort = 'all'  #['all', 'vlinder', 'vogel', 'vaatplant']  # one of: vlinder, vaatplant, vogel, all
soort_lijst = ['VHR']  # iterable of soortenlijsten: SNL, Bijl1, EcoSysLijst, VHR
periodes = ['1994-2001', '2002-2009', '2010-2017']  # select  from '2010-2017', '1994-2001', '2002-2009'
labels = periodes

#======================================================================================================================#
# specify output
out_dir = r'd:\hotspot_working\z_out\20190619'
print_table = False
print_shp = False
print_all_tables = True

holder = []

#======================================================================================================================#
# start of analysis
query = 'periode in {0} & ' \
        'soortgroep in {1} & soortlijst in {2}'.format(periodes, pgo.parse_soort_sel(soort), soort_lijst)
dat_sel = pgo.query_all_obs(query)

if dat_sel.empty:
    print('\tNo records remaining for criteria groep={0}, '
          'soortlijst={1} and periodes={2}'.format(soort, soort_lijst, ', '.join([p for p in periodes])))
else:
    print('\tFound {0} records complying to query'.format(dat_sel.shape[0]))

#==================================================================================================================#
# create pivot table with stats per hok_id
dat_piv = pd.pivot_table(data=dat_sel, index='hok_id', columns=['periode', 'soortgroep', 'soortlijst'], values='n',
                         aggfunc='sum', dropna=False)
dat_piv.replace(0.0, np.NaN, inplace=True)

print('\tcontaining {0} cells with observations'.format(dat_piv.shape[0]))
del dat_sel

# Join to df with count and area beheertypen per cell
snl_per_cell = pgo.get_snl_hokids('all', 0)  ## Note, this retrieves ALL 250m hokken!
if set(dat_piv.index) - set(snl_per_cell['hok_id']):
    warnings.warn('\tBeware, there are cells(s) with observations, but not marked as belonging to the SNL type(s)!')
dat_piv2 = pd.merge(dat_piv, snl_per_cell, how='left', left_index=True, right_on='hok_id')

del snl_per_cell

# Reduce colnames to 10 chars max, taking into account nested colnames
col_short = {'2010-2017': '1017', '1994-2001': '9401', '2002-2009': '0209', 'vogel': 'Vo', 'vlinder': 'Vl',
             'vaatplant': 'Pl', 'SNL': 'SNL', 'Bijl1': 'B1', 'cap': 'c', 'tot': 't'}
colnames = dat_piv.columns.tolist()
new_colnames = []
for col in colnames:
    if isinstance(col, tuple):
        tup_items = []
        for x in col:
            try:
                tup_items.append(col_short[x])
            except KeyError:
                tup_items.append(x)
        new_colnames.append(''.join(x for x in tup_items))
    else:
        new_colnames.append(col)
dat_piv.rename(columns=dict(zip(colnames, new_colnames)), inplace=True)

#==================================================================================================================#
# Generate output as requested

# out base name
out_base_name = 'SNL-all_Srt-{0}_Lst-{1}_P{2}_{3}'.format(soort, ''.join([x for x in soort_lijst]),
                                                         '-'.join([p for p in periodes]),
                                                         pgo.get_timestring('brief'))

if print_table:
    with open(os.path.join(out_dir, out_base_name + '.csv'), 'w') as f:
        # header
        f.write('# Tabulated extract PGO Hotspots data, '
                'by Hans Roelofsen, {0}, WEnR team B&B.\n'.format(pgo.get_timestring('full')))
        f.write('# Query from PGO data was: {0}\n'.format(query))

        # write table with soorten count per hok
        float64cols = [k for k, v in dat_piv.dtypes.astype(str).to_dict().items() if v == 'float64']
        f.write(dat_piv.fillna(9999).astype(dtype=dict(zip(float64cols, [np.int32]*len(float64cols)))).to_csv(sep=';', header=True, index=False))

        print('\twritten to table at {0}'.format(pgo.get_timestring('full')))

if print_shp:
    hokken = pgo.get_250m_hokken()  # geodataframe of 250m hokken
    dat_gdf = pd.merge(left=dat_piv, right=hokken, left_on='hok_id', right_on='ID', how='inner')
    dat_gdf = gp.GeoDataFrame(dat_gdf, crs={"init": "epsg:28992"})

    dat_gdf.to_file(os.path.join(out_dir, 'shp', out_base_name + '.shp'))
    print('\twritten to shapefile at {0}'.format(pgo.get_timestring('full')))

if print_all_tables:
    holder.append(dat_piv)

if print_all_tables:

    dat_out = pd.concat(holder)
    out_name = 'SNL-all_Srt-{0}_Lst-{1}_P{2}_{3}'.format(soort, ''.join([x for x in soort_lijst]),
                                                         '-'.join([p for p in periodes]), pgo.get_timestring('brief'))
    with open(os.path.join(out_dir, out_base_name + '.csv'), 'w') as f:
        # header
        f.write('# Tabulated extract PGO Hotspots data, '
                'by Hans Roelofsen, {0}, WEnR team B&B.\n'.format(pgo.get_timestring('full')))
        f.write('# Query from PGO data was: {0}\n'.format(query))

        # write table with soorten count per hok
        float64cols = [k for k, v in dat_out.dtypes.astype(str).to_dict().items() if v == 'float64']
        f.write(dat_out.fillna(9999).astype(dtype=dict(zip(float64cols, [np.int32] * len(float64cols)))).to_csv(sep=';',
                                                                                                                header=True,
                                                                                                                index=False))
        print('\twritten to table at {0}'.format(pgo.get_timestring('full')))


