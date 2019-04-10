# script to map species count per cell for PGO data.
# Hans Roelofsen, WEnR 21 maart 2019

import os
import numpy as np
import pandas as pd
import warnings

from utils import pgo

#======================================================================================================================#
# define data selection and specification of difference map categories
soort = 'all' #['all', 'vlinder', 'vogel', 'vaatplant']  # one of: vlinder, vaatplant, vogel, all
snl_types = ['N1705', 'N1402']  # snl_types = ['N0201', 'N0301', 'N0401', 'N0402', 'N0403', 'N0404', 'N0501', 'N0502', 'N0601', 'N0602', 'N0603', 'N0604', 'N0605', 'N0606', 'N0701', 'N0702', 'N0801', 'N0802', 'N0803', 'N0804', 'N0901', 'N1001', 'N1002', 'N1101', 'N1201', 'N1202', 'N1203', 'N1204', 'N1205', 'N1206', 'N1301', 'N1302', 'N1401', 'N1402', 'N1403', 'N1501', 'N1502', 'N1601', 'N1602', 'N1603', 'N1604', 'N1701', 'N1702', 'N1703', 'N1704', 'N1705', 'N1706', 'N1800', 'N1900']  #'HalfnatuurlijkGrasland', 'OpenDuin', 'Heide', 'Bos', 'Moeras']  # iterable of SNL beheercodes OR  EcosysteemType naam
soort_lijst = ['SNL', 'Bijl1']  # iterable of soortenlijsten: SNL, Bijl1, EcoSysLijst
periodes = ['1994-2001', '2002-2009', '2010-2017']  # select  from '2010-2017', '1994-2001', '2002-2009'
labels = periodes

# cap Annex 1 soorten to 2 max per cell?
max_2_annex1_per_cell = True

# ecosysteemtype are compiled from individual beheertypes?
eco_from_beheer_types = False  # pref only True when snl_types contains Ecosysteemtypes, not beheertypes!

# calculate mean species per SNL beheertype?
calculate_means = True

# calculate difference between periods? If True, based on means or sums? Also define categories for reporting diffs
calculate_differences = True
report_stat = 'sum'
diff_periodes = ['2002-2009', '2010-2017']
diff_cats = [range(-1000, -4), range(-4, 0),  range(0, 1), range(1, 5), range(5, 1000)]
diff_labs = ['-5 or less', '-4 t/m -1', '0', '1 t/m 4', '5 or more']
diff_colors = ['red', 'orange', 'lightgrey', 'lightgreen', 'darkgreen']

if report_stat == 'mean' and calculate_means is False:
    raise Exception('Set calculate_means to True when requesting means for reporting, you knob')

# report histogram with cell count with 1, 2, 3 ... n species?
cell_histogram = True

#======================================================================================================================#
# specify output
out_dir = r'd:\temptxt\test20190409'
print_diff_map = True
print_table = True
print_shp = False

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

    #==================================================================================================================#
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

    #==================================================================================================================#
    # Pivot data around hok IDs and cap Annex 1 soorten to 2 if requested

    dat_piv = pd.pivot_table(data=dat_sel, index='hok_id', columns=['periode', 'soortlijst'], values='n', aggfunc='sum')

    # Just Annex 1 data
    annex1_dat_all = dat_piv.xs('Bijl1', level=1, axis=1)  # only annex1 data per cell
    annex1_dat_mx2 = annex1_dat_all.where(annex1_dat_all < 2, 2)  # set to 2 where value <2 is False

    # Just SNL data
    snl_dat = dat_piv.xs('SNL', level=1, axis=1)

    if annex1_dat_all.shape != snl_dat.shape and all(annex1_dat_all.index == snl_dat.index):  # double check
        raise Exception('Somehow shapes of annex1 data and SNL data are not identical')

    # Add either full Annex 1 data or capped Annex 1 data to the SNL data
    if max_2_annex1_per_cell:
        cell_dat = snl_dat.add(annex1_dat_mx2, axis=1)
    else:
        cell_dat = snl_dat.add(annex1_dat_all, axis=1)

    cell_dat.rename(columns=dict(zip(periodes, ['sum_' + p for p in periodes])), inplace=True)

    print('\tcontaining {0} cells with observations'.format(dat_piv.shape[0]))

    # Join to df with count and area beheertypen per cell
    snl_per_cell = pgo.get_snl_hokids(snl_list, 0)
    if set(cell_dat.index) - set(snl_per_cell['hok_id']):
        warnings.warn('\tBeware, there are cells(s) with observations, but not marked as belonging to the SNL type(s)!')
    cell_dat = pd.merge(cell_dat, snl_per_cell, how='inner', left_index=True, right_on='hok_id')

    # clean-up
    del snl_per_cell, dat_piv, dat_sel, snl_dat, annex1_dat_all, annex1_dat_mx2

    #==================================================================================================================#
    # Optional calculations

    # calculate species count DIVIDED BY beheertype count, per periode, if requested
    if calculate_means:
        for periode in periodes:
            cell_dat['mean_{0}'.format(periode)] = cell_dat.apply(lambda row: np.divide(row['sum_{0}'.format(periode)],
                                                                                        row['snl_count']), axis=1)

    # Difference in sp count per cell between two periods. Calculate for the requested reporting stat
    if calculate_differences:
        report_col_names = [report_stat + '_' + p for p in diff_periodes]
        cell_dat.dropna(axis=0, how='any', subset=report_col_names, inplace=True)  # drop NAs, ie cells w/o obs in a period
        cell_dat['sp_count_diff'] = cell_dat.apply(lambda row: np.subtract(row[report_col_names[1]],
                                                                           row[report_col_names[0]]), axis=1)
        cell_dat['diff_cat'] = cell_dat['sp_count_diff'].apply(pgo.classifier, args=(diff_cats, diff_labs))

        # histogram of period differences
        diff_piv = pd.pivot_table(data=cell_dat, index='sp_count_diff', values=report_col_names[0], aggfunc='count')
        diff_piv.rename(columns={report_col_names[0]: 'count'}, inplace=True)

    # histogram of cell-count with X species in them, per periode
    if cell_histogram:
        cells_hist = pd.DataFrame(index=range(0, 1001))
        for periode in periodes:
            try:
                # histogram based on dataframe with NAs removed in the Periode data columns
                periode_hist = pd.pivot_table(data=cell_dat, index='sum_{0}'.format(periode), values='hok_id',
                                              aggfunc='count')
                cells_hist = pd.merge(left=cells_hist, right=pd.DataFrame(periode_hist), left_index=True,
                                      right_index=True, how='left')
                cells_hist.rename(columns={'hok_id': 'cell_count_{0}'.format(periode)}, inplace=True)
            except KeyError:  # a period may be absent if there are no observations
                continue
        cells_hist.dropna(axis=0, how='all', inplace=True)  # Drop rows without values

    if print_diff_map or print_shp:
        # create geospatial object if needed
        hokken = pgo.get_250m_hokken()  # geodataframe of 250m hokken

        # merge to the geodataframe to get a spatial object
        hok_comparison = set(cell_dat['hok_id']) - set(hokken['ID'])  # set of stuff in dat_piv.index BUT NOT IN hokken['id']
        if hok_comparison:
            raise Exception('{0} 250m hokken zijn bekend in de database, maar niet in de '
                            'shapefile: {1}'.format(len(hok_comparison), '\n'.join([str(hok) for hok in hok_comparison])))

        cell_gdf = pd.merge(left=hokken, right=cell_dat, how='inner', left_on='ID', right_on='hok_id')

    #==================================================================================================================#
    # Generate output as requested

    # out base name
    out_base_name = '{0}_Srt-{1}_Lst-{2}_Diff{3}_{4}'.format(snl, soort, ''.join([x for x in soort_lijst]),
                                                             '-'.join([p for p in periodes]),
                                                             pgo.get_timestring('brief'))

    if print_diff_map and calculate_differences:
        map_title = 'Toe/Afname van {0} ' \
                    'aantal {1} in {2}\n gedurende {3}'.format(report_stat,
                                                               ', '.join([s for s in pgo.parse_soort_sel(soort)]),
                                                               snl, ':'.join([x for x in labels]))
        pgo.diff_to_png(gdf=cell_gdf, col='diff_cat', cats=diff_labs, cat_cols=dict(zip(diff_labs, diff_colors)),
                        title=map_title, background=False, background_cells=hokken, out_dir=out_dir,
                        out_name=out_base_name + '.png',
                        comment='Created Hans Roelofsen WEnR at {0}'.format(pgo.get_timestring('full')))
        print('\tprinted to map at {0}'.format(pgo.get_timestring('full')))

    if print_shp:
        cell_gdf.to_file(os.path.join(out_dir, 'shp', out_base_name + '.shp'))
        print('\twritten to shapefile at {0}'.format(pgo.get_timestring('full')))

    if print_table:
        with open(os.path.join(out_dir, out_base_name + '.csv'), 'w') as f:
            f.write('# Tabulated extract PGO Hotspots data, '
                    'by Hans Roelofsen, {0}, WEnR team B&B.\n'.format(pgo.get_timestring('full')))
            f.write('# Query from PGO data was: {0}\n'.format(query))

            if max_2_annex1_per_cell:
                f.write('# Bijlage 1 soorten were capped to 2 per cell\n')

            if calculate_differences:
                f.write('# Difference statistics are derived from the {0} columns'
                        'between periodes {1} and {2}.\n'.format(report_stat, diff_periodes[0], diff_periodes[1]))

            # write table with soorten count per hok
            float64cols = [k for k,v in cell_dat.dtypes.astype(str).to_dict().items() if v == 'float64']
            f.write(cell_dat.fillna(9999).astype(dtype=dict(zip(float64cols, [np.int32]*len(float64cols)))).to_csv(sep=';', header=True, index=False))

            if calculate_differences:
                # write table with histogram differences count between periodes
                f.write('######\n')
                float64cols = [k for k,v in cell_dat.dtypes.astype(str).to_dict().items() if v == 'float64']
                # TODO: write as integers, not floats
                f.write(diff_piv.fillna(9999).to_csv(sep=';', header=True, index=True))

            if cell_histogram:
                f.write('######\n')
                float64cols = [k for k,v in cell_dat.dtypes.astype(str).to_dict().items() if v == 'float64']
                # TODO: write as integers, not floats
                f.write(cells_hist.fillna(9999).to_csv(sep=';', header=True, index=True))

            print('\twritten to table at {0}'.format(pgo.get_timestring('full')))
