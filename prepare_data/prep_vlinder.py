# Prepare vlinder data for use.
# Hans Roelofsen, WEnR, 25*03*2019

import os
import numpy as np
import pandas as pd
import rasterio as rio

asc = rio.open(os.path.join(r'd:\hotspot_working\a_broedvogels\Soortenrijkdom\Species_richness',
                            'vogel_OpenDuin_EcoSysLijst_2010-2017.asc'))

vlinder_dir = r'd:\hotspot_working\c_vlinders'
vlinder_1ai = 'dagvl_sovon_snl_1ai.txt'  # SNL + Bijlage 1
vlinder_1aii = 'dagvl_sovon_snl_1aii.txt'  # VHR soorten
vlinder_2c = 'dagvl_sovon_2c.txt'  # Ecosysteemtype


# Note, vlinder x250, y250 = coordinates of cell-centre!
# Transform to cell top-left for harmonisation with vogel and plant data, ie X: subtract 125m, Y: add 125m
def add_hok_id(df):
    df['col'] = df.apply(lambda x: int(((x.x250, x.y250) * ~asc.affine)[0]), axis=1)
    df['row'] = df.apply(lambda x: int(((x.x250, x.y250) * ~asc.affine)[1]), axis=1)
    df['hok_id'] = df.apply(lambda x: str(np.subtract(x.x250, 125)) + '_' + str(np.add(x.y250, 125)), axis=1)
    return df

# vlinder_1ai.txt: bevat SNL soortenlijst plus Bijlage 1 soorten per SNL beheerstype
vl_1ai = pd.read_csv(os.path.join(vlinder_dir, vlinder_1ai), comment='#', sep=';', header=0)
vl_1ai = add_hok_id(vl_1ai)  # add hok IDs

vl_1ai_snl = vl_1ai.copy()  # copy for just the SNL soorten
vl_1ai_snl['soortlijst'] = 'SNL'
vl_1ai_snl.rename(columns={'SNL_BT': 'snl', 'N_KenmSrt': 'n'}, inplace=True)
vl_1ai_snl.drop(labels='N_Bijl1Srt', inplace=True, axis=1)
print(list(vl_1ai_snl))

vl_1ai_bijl1 = vl_1ai.copy()  # copy for just the Annex 1 soorten
vl_1ai_bijl1['soortlijst'] = 'Bijl1'
vl_1ai_bijl1.rename(columns={'SNL_BT': 'snl', 'N_Bijl1Srt': 'n'}, inplace=True)
vl_1ai_bijl1.drop(labels='N_KenmSrt', inplace=True, axis=1)
print(list(vl_1ai_bijl1))

# vlinder_1aii: bevat VHR soortenlijsten per cell
vl_1aii = pd.read_csv(os.path.join(vlinder_dir, vlinder_1aii), comment='#', sep=';', header=0)
vl_1aii = add_hok_id(vl_1aii)  # add hok IDs
vl_1aii['snl'] = 'geen'
vl_1aii['soortlijst'] = 'VHR'
vl_1aii.rename(columns={'N_HR_TypSrt': 'n'}, inplace=True)
print(list(vl_1aii))

# vlinder_2c: bevat Ecosysteemtype soortenlijst
vl_2c = pd.read_csv(os.path.join(vlinder_dir, vlinder_2c), comment='#', sep=';', header=0)
vl_2c = add_hok_id(vl_2c)
vl_2c['soortlijst'] = 'EcoSysType'
vl_2c.rename(columns={'ecosysteemtype_nm': 'snl', 'N_KenmSrt':'n'}, inplace=True)
vl_2c.drop(labels='N_Bijl1Srt', inplace=True, axis=1)
print(list(vl_2c))

vlinder_all = pd.concat([vl_1ai_snl, vl_1ai_bijl1, vl_1aii, vl_2c])
vlinder_all.drop(labels='id', axis=1, inplace=True)
vlinder_all.rename(columns={'x250': 'x_rd', 'y250': 'y_rd'}, inplace=True)
vlinder_all['soortgroep'] = 'vlinder'
vlinder_all.to_csv(os.path.join(vlinder_dir, 'vlinder_all_v2.txt'),
                   index=False, sep=';')
