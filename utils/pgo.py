# several helper functions for analysing and plotting PGO hotspot data
# Hans Roelofsen, 20/03/2019

import os
import warnings
import datetime
import numpy as np
import matplotlib.patches as mpatches
import matplotlib.pyplot as plt
import geopandas as gp
import pandas as pd
import pickle
import rasterio as rio


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


def ascii_species_grid_to_pd(dir_in, asc_in):
    # Convert ascii grid to pandas dataframe
    groep, snl, soortlijst, periode = os.path.splitext(asc_in)[0].split('_')

    specs = get_specs(dir_in, asc_in)
    asc = rio.open(os.path.join(dir_in, asc_in))

    # reshape grid nrows*ncols to list of length nrows*ncols
    # order = 'C' means that values are read per row, ie last index changes fastest!
    vals = np.reshape(asc.read(1), newshape=np.product(asc.shape), order='C').astype(np.int16)

    # new dataframe where:
    #  n = values read from the ascii grid
    #  soortgroep = groep, as inferred from file name
    #  snl = snl beheertype, as inferred from file name
    #  periode = periode to which data applies, as inferred from file name
    #  soortlijst = species list to which data applies, as inferred from file name
    db = pd.DataFrame({'n': vals, 'soortgroep': groep, 'snl':snl, 'periode':periode, 'soortlijst':soortlijst})

    # Add Row, Col indices to each row in the dataframe
    # row indices range from 0 up to and including specs['NROWS'] -1
    # col indices range from 0 up to and including specs['NCOLS'] -1
    # although row, col indices are integers (ie 'blocks'), note that row, col (0,0) refers to cell top-left in
    # Cartesian space
    db['row'] = np.array([[i] * specs['NCOLS'] for i in range(0, specs['NROWS'])]).reshape(np.product(asc.shape))
    db['col'] = np.array([i for i in range(0, specs['NCOLS'])] * specs['NROWS']).reshape(np.product(asc.shape))

    # drop rows where n is either zero or NoData
    db.drop(db.loc[(db['n'] == specs['NODATA_value']) | (db['n'] == 0)].index, axis=0, inplace=True)

    # Calculate Cartesian (ie RD New coordinates) based on the row, col indices, meaning that they refer to the
    # cell top-left!!
    db['x_rd'] = db.apply(lambda x: ((x.col, x.row) * asc.affine)[0], axis=1).astype(np.int32)
    db['y_rd'] = db.apply(lambda x: ((x.col, x.row) * asc.affine)[1], axis=1).astype(np.int32)
    db['hok_id'] = db.apply(lambda x: str(x.x_rd) + '_' + str(x.y_rd), axis=1)
    return db


def ascii_snl_grid_to_pd(dir_in, asc_in):
    specs = get_specs(dir_in, asc_in)
    asc = rio.open(os.path.join(dir_in, asc_in))

    # reshape grid nrows*ncols to list of length nrows*ncols
    # order = 'C' means that values are read per row, ie last index changes fastest!
    vals = np.reshape(asc.read(1), newshape=np.product(asc.shape), order='C').astype(np.int32)

    db = pd.DataFrame({'area_m2': vals})
    print(db.describe())
    # row indices range from 0 up to and including specs['NROWS'] -1
    # col indices range from 0 up to and including specs['NCOLS'] -1
    # although row, col indices are integers (ie 'blocks'), note that row, col (0,0) refers to cell top-left in
    # Cartesian space
    db['row'] = np.array([[i] * specs['NCOLS'] for i in range(0, specs['NROWS'])]).reshape(np.product(asc.shape))
    db['col'] = np.array([i for i in range(0, specs['NCOLS'])] * specs['NROWS']).reshape(np.product(asc.shape))
    db.drop(db.loc[(db['area_m2'] == specs['NODATA_value']) | (db['area_m2'] == 0)].index, axis=0, inplace=True)
    # note that coordinates are calculated for the row,col indices, which means they apply to the cell top-left!
    db['x_rd'] = db.apply(lambda x: ((x.col, x.row) * asc.affine)[0], axis=1).astype(np.int32)
    db['y_rd'] = db.apply(lambda x: ((x.col, x.row) * asc.affine)[1], axis=1).astype(np.int32)
    db['hok_id'] = db.apply(lambda x: str(x.x_rd) + '_' + str(x.y_rd), axis=1)

    return db.drop(['row', 'col', 'x_rd', 'y_rd'], axis=1)


def query_all_obs(query):
    # returns pandas dataframe of all observations, file locations are hard-coded

    relevant_cols = ['periode', 'snl', 'n', 'hok_id', 'soortlijst', 'soortgroep']

    try:
        vlinder = pd.read_csv(r'd:\hotspot_working\c_vlinders\vlinder_all_v2.txt', comment='#', sep=';',
                              usecols=relevant_cols)
        plant = pd.read_csv(r'd:\hotspot_working\b_vaatplanten\Soortenrijkdom\vaatplant_all2.csv', comment='#', sep=';',
                            usecols=relevant_cols)
        vogel = pd.read_csv(r'd:\hotspot_working\a_broedvogels\Soortenrijkdom\Species_richness\vogel_all3.csv',
                            comment='#', sep=';', usecols=relevant_cols)
        return pd.concat([vlinder.query(query), plant.query(query), vogel.query(query)])

    except OSError:
        raise Exception('You\'re trying to open a files that lives only on the laptop of Hans Roelofsen, bad luck son.')


def get_all_obs():
    # returns pandas dataframe of all observations, file locations are hard-coded

    warnings.warn('You\'re trying to load ALL observations (32.433.656 Vogels, 814.624 Vlinders and 2.818.828 Planten)'
                  ', that is probably a bad idea. Use query_all_obs instead')

    try:
        vlinder = pd.read_csv(r'd:\hotspot_working\c_vlinders\vlinder_all.txt', comment='#', sep=';')
        plant = pd.read_csv(r'd:\hotspot_working\b_vaatplanten\Soortenrijkdom\vaatplant_all2.csv', comment='#', sep=';')
        vogel = pd.read_csv(r'd:\hotspot_working\a_broedvogels\Soortenrijkdom\Species_richness\vogel_all2.csv',
                            comment='#', sep=';')
        return pd.concat([vogel, plant, vlinder])

    except OSError:
        raise Exception('You\'re trying to open a files that lives only on the laptop of Hans Roelofsen, bad luck son.')


def diff_to_png(gdf, title, comment, col, cats, cat_cols, background, background_cells, out_dir, out_name):
    # Plot map of difference categorieen

    # background images of Provincies - hardcoded.
    prov = gp.read_file(os.path.join(r'd:\NL\provincies', 'provincies.shp'))
    prov_grenzen = gp.read_file(r'd:\NL\provincie_grenzen\provincie_grenzen_v2.shp')

    fig = plt.figure(figsize=(8, 10))
    ax = fig.add_subplot(111)
    ax.set_aspect('equal')
    plt.tick_params(axis='both', labelbottom=False, labeltop=False, labelleft=False, labelright=False)
    ax.set(title=title)
    ax.set(xlim=[0, 300000], ylim=[300000, 650000])

    prov.plot(ax=ax, color='white')  # plot provincien as background

    if background:
        # plot background cells if requested
        background_cells.plot(ax=ax, color='orange', linewidth=0)

    legend_patches = []
    for cat in cats:
        # generate legend patches based on the *cat*egories and category_colors (cat_cols)
        legend_patches.append(mpatches.Patch(label=cat, edgecolor='black', facecolor=cat_cols[cat]))

    for cat in cats:
        # plot each category individually
        sel = gdf.loc[gdf[col] == cat, :]
        sel.plot(ax=ax, linewidth=0, color=cat_cols[cat], label=cat)

    prov_grenzen.plot(ax=ax, color='black')  # plot provinciegrenzen (again)

    ax.text(1000, 301000, comment, ha='left', va='center', size=6)
    plt.legend(handles=legend_patches, loc='upper left', fontsize='small', frameon=False, title='Toe/Afname')
    plt.savefig(os.path.join(out_dir, out_name))


def parse_soort_sel(x):
    # Function to parse a species selection to list, or list of all species when 'all' is requested
    soort_lists = {'vogel': ['vogel'], 'vlinder': ['vlinder'], 'vaatplant': ['vaatplant'], 'all': ['vogel', 'vlinder',
                                                                                                   'vaatplant']}
    try:
        return soort_lists[x]
    except KeyError:
        raise Exception('{0} is not a valid soort-selectie, choose one from vogel, vlinder, plant or all'.format(x))


def get_250m_hokken():
    # return GeoDataFrame of 250m hokken, assumes fixed location. Provincie is one of attributes
    try:
        return gp.read_file(r'd:\hotspot_working\shp_250mgrid\hok250m_fullextent.shp')
    except OSError:
        raise Exception('You\'re trying to open a shapefile that lives only on the laptop of Hans Roelofsen.')


def classifier(x, categories, labels):
    # returns corresponding label for numerical category containing x
    try:
        return labels[[np.int32(x) in cat_range for cat_range in categories].index(True)]
    except ValueError:
        raise Exception('Sorry, requested value {0} is not found in any of the ranges.'.format(x))


def ecosys_2_beheer(snl_code):
    trans = {'Moeras': ['N0501', 'N0502', 'N0601', 'N0602'],
             'Heide': ['N0603', 'N0604', 'N0605', 'N0606', 'N0701', 'N0702'],
             'OpenDuin': ['N0801', 'N0802', 'N0803', 'N0804'],
             'HalfnatuurlijkGrasland': ['N0901', 'N1001', 'N1002', 'N1101', 'N1201', 'N1202', 'N1203', 'N1204', 'N1205',
                                        'N1206', 'N1301', 'N1302'],
             'Bos': ['N1401', 'N1402', 'N1403', 'N1501', 'N1502', 'N1601', 'N1602', 'N1603', 'N1604', 'N1701', 'N1702',
                     'N1703', 'N1704', 'N1705', 'N1706']}

    try:
        return trans[snl_code]
    except KeyError:
        warnings.warn('\t{0} is not a valid ecosysteemtype naam, returning {0} as a list'.format(snl_code))
        return[snl_code]


def get_timestring(timetype):
    t0 = datetime.datetime.now()
    if timetype == 'full':
        return t0.strftime("%Y-%m-%d_%H:%M:%S")
    elif timetype == 'brief':
        return t0.strftime("%y%m%d-%H%M")
    else:
        return t0


def get_snl_hokids(snl, treshold):
    # function to get df of 250m hokken from *snl* beheertypes and/or ecosysteemtypes where the area exceeds *treshold*
    # returns df where: hok_id = hok_id, snl_count = aantal snl types aanwezig in hok
    # reads pickled PD dataframes of of snl type, hard-coded to Hans Roelofsen laptop

    # always iterate of the requested snl types
    if not isinstance(snl, list):
        snl = [snl]

    # read and concatenate all requested snl type pickles
    holder = []
    augurken_dir = r'd:\hotspot_working\a_broedvogels\SNL_grids\augurken'
    for snl_type in snl:
        with open(os.path.join(augurken_dir, snl_type + '.pkl'), 'rb') as handle:
            df = pickle.load(handle)
            holder.append(df.loc[df['area_m2'] >= treshold, :])
    snl_dat = pd.concat(holder)

    # Note: SNL grid data are already cleansed from cells with -9999 (NoData) and 0 sq m2 area. See prep_asc.py

    # read provincien
    with open(os.path.join(augurken_dir, 'provincien.pkl'), 'rb') as handle:
        prov = pickle.load(handle)

    # pivot on hok_id and report number of snl types per hok_id
    print('\t\tFound {0} cells from {1} SNL type(s) with area gte {2}'.format(len(set(snl_dat['hok_id'])),
                                                                              len(snl), str(treshold)))

    foo = pd.DataFrame(pd.pivot_table(data=snl_dat, index='hok_id', values='area_m2',
                                      aggfunc={'area_m2': ['count', 'sum']})).rename(columns={'count': 'snl_count',
                                                                                              'sum': 'snl_area_m2'})
    return pd.merge(left=foo, right=prov, left_index=True, right_on='hok_id', how='left')
