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

def query_all_obs(query):
    # returns pandas dataframe of all observations, file locations are hard-coded

    try:
        vlinder = pd.read_csv(r'd:\hotspot_working\c_vlinders\vlinder_all.txt', comment='#', sep=';')
        plant = pd.read_csv(r'd:\hotspot_working\b_vaatplanten\Soortenrijkdom\vaatplant_all2.csv', comment='#', sep=';')
        vogel = pd.read_csv(r'd:\hotspot_working\a_broedvogels\Soortenrijkdom\Species_richness\vogel_all2.csv', comment='#', sep=';')
        return pd.concat([vlinder.query(query), plant.query(query), vogel.query(query)])

    except OSError:
        raise Exception('You\'re trying to open a files that lives only on the laptop of Hans Roelofsen, bad luck son.')


def get_all_obs():
    # returns pandas dataframe of all observations, file locations are hard-coded

    try:
        vlinder = pd.read_csv(r'd:\hotspot_working\c_vlinders\vlinder_all.txt', comment='#', sep=';')
        plant = pd.read_csv(r'd:\hotspot_working\b_vaatplanten\Soortenrijkdom\vaatplant_all2.csv', comment='#', sep=';')
        vogel = pd.read_csv(r'd:\hotspot_working\a_broedvogels\Soortenrijkdom\Species_richness\vogel_all2.csv', comment='#', sep=';')
        return pd.concat([vogel, plant, vlinder])

    except OSError:
        raise Exception('You\'re trying to open a files that lives only on the laptop of Hans Roelofsen, bad luck son.')



def diff_to_png(gdf, title, comment, col, cats, background, background_cells, out_dir, out_name):
    # background images of Provincies - hardcoded.
    prov = gp.read_file(os.path.join(r'm:\a_Projects\Natuurwaarden\agpro\natuurwaarden\shp', 'provincies.shp'))

    fig = plt.figure(figsize=(8,10))
    ax = fig.add_subplot(111)
    ax.set_aspect('equal')
    plt.tick_params(axis='both', labelbottom=False, labeltop=False, labelleft=False, labelright=False)
    ax.set(title=title)
    ax.set(xlim=[0, 300000], ylim=[300000, 650000])

    prov.plot(ax=ax, color='lightgrey')

    if background:
        background_cells.plot(ax=ax, color='orange', linewidth=0)

    legend_patches = []
    for cat, color in cats.items():
        legend_patches.append(mpatches.Patch(label=cat, edgecolor='black', facecolor=color))

    for cat, colour in cats.items():
        sel = gdf.loc[gdf[col] == cat, :]
        # print('{0} df nrow: {1}'.format(cat, sel.shape[0]))
        sel.plot(ax=ax, linewidth=0, color=colour)

    ax.text(1000, 301000, comment, ha='left', va='center', size=6)

    plt.legend(handles=legend_patches, loc='upper left', fontsize='small', frameon=False, title='Toe/Afname')
    plt.savefig(os.path.join(out_dir, out_name))
    plt.close


def parse_soort_sel(x):
    soort_lists = {'vogel':['vogel'], 'vlinder':['vlinder'], 'vaatplant':['vaatplant'], 'all':['vogel', 'vlinder',
                                                                                           'vaatplant']}
    try:
        return soort_lists[x]
    except KeyError:
        raise Exception ('{0} is not a valid soort-selectie, choose one from vogel, vlinder, plant or all'.format(x))


def get_250m_hokken():
    # return GeoDataFrame of 250m hokken, assumes fixed location
    try:
        return gp.read_file(r'd:\hotspot_working\shp_250mgrid\hok250m.shp')
    except OSError:
        raise Exception('You\'re trying to open a shapefile that lives only on the laptop of Hans Roelofsen.')


def classifier(x, categories, labels):
    # returns corresponding label for numerical category containing x
    try:
        return labels[[np.int32(x) in range for range in categories].index(True)]
    except ValueError:
        raise Exception('Sorry, requested value {0} is not found in any of the ranges.'.format(x))


def max2(soortlijst, n):
    if soortlijst == 'Bijl1' and n > 2:
        return 2
    else:
        return n


def ecosys_2_beheer(snl_code):
    trans = {'Moeras': ['N0501', 'N0502', 'N0601', 'N0602'],
             'Heide': ['N0603', 'N0604', 'N0605', 'N0606', 'N0701', 'N0702'],
             'OpenDuin': ['N0801', 'N0802', 'N0803', 'N0804'],
             'HalfnatuurlijkGrasland': ['N0901', 'N1001', 'N1002', 'N1101', 'N1201', 'N1202', 'N1203', 'N1204', 'N1205', 'N1206', 'N1301', 'N1302'],
             'Bos': ['N1401', 'N1402', 'N1403', 'N1501', 'N1502', 'N1601', 'N1602', 'N1603', 'N1604', 'N1701', 'N1702', 'N1703', 'N1704', 'N1705', 'N1706']}

    try:
        return trans[snl_code]
    except KeyError:
        warnings.warn('\t{0} is not a valid ecosysteemtype naam, returning {0} as a list'.format(snl_code))
        return[snl_code]


def get_timestring(type):
    t0 = datetime.datetime.now()
    if type == 'full':
        return t0.strftime("%Y-%m-%d_%H:%M:%S")
    elif type == 'brief':
        return t0.strftime("%y%m%d-%H%M")
    else:
        return t0