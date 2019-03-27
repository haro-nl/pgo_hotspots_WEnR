# script to map species count per cell for PGO data.
# Hans Roelofsen, WEnR 21 maart 2019

import os
import datetime
import numpy as np
import pandas as pd

from utils import pgo

#======================================================================================================================#
# define data selection and specification of difference map categories
soort = 'all'  # one of: vlinder, vaatplant, vogel, all
snl_types = ['Heide']#, 'HalfnatuurlijkGrasland', 'OpenDuin', 'Heide', 'Bos', 'Moeras']  # iterable of SNL beheercodes OR  EcosysteemType naam
soort_lijst = ['EcoSysLijst']  # iterable of soortenlijsten: SNL, EXTRA, EcoSysLijst
periodes = ['2002-2009', '2010-2017']  # select two from '2010-2017', '1994-2001', '2002-2009'
labels = periodes

# categories of difference between periodes
diff_cats = [range(-1000, -1), range(-1, 2), range(2, 1000)]
diff_labs = ['-2 of nog minder', '-1, 0 of 1', '2 of nog meer']
diff_colors = ['red', 'white', 'green']

# cap Annex 1 soorten to 2 max per cell?
max_2_annex1 = True

# ecosysteemtype are compiled from individual beheertypes?
eco_from_beheer_types = False  # may only be True when snl_types contains Ecosysteemtypes, not beheertypes!

# soorten per 250m hok worden gerapporteerd als: sum OR mean
hok_stat = 'sum'

#======================================================================================================================#
# specify output
out_dir = r'd:\hotspot_working\z_out\20190327'
print_diff_map = True
print_table = True
print_shp = True

#======================================================================================================================#
# get geospatial data
hokken = pgo.get_250m_hokken()

#======================================================================================================================#
# Analyse per snl type

for snl in snl_types:

    print('\n{0} in progress at {1}'.format(snl, pgo.get_timestring('full')))

    #==================================================================================================================#
    # compile ecosysteemtype from individual beheertypes, if requested
    if eco_from_beheer_types:
        snl_list = pgo.ecosys_2_beheer(snl)  # list of beheertypes that together make the ecosysteemtype
                                             # raises warning when snl is not an ecosysteemtype but returns [snl]
    else:
        snl_list = [snl]

    # ==================================================================================================================#
    # formulate data query and get data
    query = 'snl in {0} & periode in {1} & ' \
            'soortgroep in {2} & soortlijst in {3}'.format(snl_list, periodes, pgo.parse_soort_sel(soort), soort_lijst)
    dat_sel = pgo.query_all_obs(query)

    if dat_sel.empty:
        print('\tNo records remaining for criteria groep={0}, '
              'snl_types={1} and periodes={2}'.format(soort, snl, ', '.join([p for p in periodes])))
        continue
    else:
        print('\tFound {0} records complying to query'.format(dat_sel.shape[0]))

    # Cap Bijlage1 soorten to 2 per cell
    if max_2_annex1:
        dat_sel['n'] = dat_sel.apply(lambda row: pgo.max2(row['soortlijst'], row['n']), axis=1)

    # create pivot table and calculate differences and difference category per cell
    # dat_piv = pd.pivot_table(data=dat_sel, index='hok_id', columns='periode', values='n', aggfunc={'n':[np.mean, np.sum, 'count']})
    dat_piv = pd.pivot_table(data=dat_sel, index='hok_id', columns='periode', values='n', aggfunc=hok_stat)
    periode_col_names = [hok_stat + '_' + p for p in periodes]
    dat_piv.rename(columns=dict(zip(periodes, periode_col_names)), inplace=True)
    dat_piv.dropna(axis=0, how='any', subset=periode_col_names, inplace=True)
    dat_piv['sp_count_diff'] = dat_piv.apply(lambda row: np.subtract(row[periode_col_names[1]],
                                                                     row[periode_col_names[0]]), axis=1)
    dat_piv['diff_cat'] = dat_piv['sp_count_diff'].apply(pgo.classifier, args=(diff_cats, diff_labs))

    # merge to the geodataframe to get a spatial object
    hok_comparison = set(dat_piv.index) - set(hokken['ID'])  # set of elements in dat_piv.index BUT NOT IN hokken['id']
    if hok_comparison:
        raise Exception('{0} 250m hokken zijn bekend in de database, maar niet in de '
                        'shapefile: {1}'.format(len(hok_comparison), '\n'.join([hok for hok in hok_comparison])))
    hok_piv = pd.merge(left=hokken, right=dat_piv, how='inner', left_on='ID', right_index=True)

    # histogram of period differences
    diff_piv = pd.pivot_table(data=dat_piv, index='sp_count_diff', values=periode_col_names[0], aggfunc='count')
    diff_piv.rename(columns={periode_col_names[0]: 'count'})

    # out base name
    out_base_name = '{0}_Srt-{1}_Lst-{2}_Diff{3}_{4}'.format(snl, soort, ''.join([x for x in soort_lijst]),
                                                          '-'.join([p for p in periodes]), pgo.get_timestring('brief'))

    if print_diff_map:
        map_title = 'Toe/Afname van {0} aantal {1} in {2}\n gedurende {3}'.format(hok_stat,
                                                                                          ', '.join([s for s in pgo.parse_soort_sel(soort)]),
                                                                                          snl,
                                                                                          ':'.join([x for x in labels]))
        pgo.diff_to_png(gdf=hok_piv, col='diff_cat', cats=dict(zip(diff_labs, diff_colors)), title=map_title,
                        background=False, background_cells=hokken, out_dir=out_dir, out_name=out_base_name + '.png',
                        comment='Created Hans Roelofsen WEnR at {0}'.format(pgo.get_timestring('full')))
        print('\tprinted to map at {0}'.format(pgo.get_timestring('full')))

    if print_table:
        with open(os.path.join(out_dir, out_base_name + '.csv'), 'w') as f:
            # header
            f.write('# Tabulated extract PGO Hotspots data, '
                    'by Hans Roelofsen, {0}, WEnR team B&B.\n'.format(pgo.get_timestring('full')))
            f.write('# Query from PGO data was: {0}\n'.format(query))
            if max_2_annex1:
                f.write('Bijlage 1 soorten were capped to 2 per cell\n')

            # write table with soorten count per hok
            f.write(dat_piv.fillna(9999).astype(dtype=dict(zip(periode_col_names+ ['sp_count_diff'],
                                                               [np.int32]*3))).to_csv(sep=';', header=True, index=True))

            # write table with histogram differences count between periodes
            f.write('######\n')
            f.write(diff_piv.fillna(0).astype(np.int32).to_csv(sep=';', header=True, index=True))

            print('\twritten to table at {0}'.format(pgo.get_timestring('full')))

    if print_shp:
        hok_piv.to_file(os.path.join(out_dir, 'shp', out_base_name+'.shp'))