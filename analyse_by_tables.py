# script for analysing PGO data on vlinders, planten en vogels.
# Hans Roelofsen, WEnR, 11 maart 2019

import pandas as pd
import os

from utils import pgo

dat = pgo.get_all_obs()

out_dir = r'd:\hotspot_working\output'

# all
all_piv= pd.pivot_table(data=dat, index='snl', columns='n', values='hok_id', aggfunc=lambda x: len(x.unique()))
print(all_piv.head())
all_piv.to_csv(os.path.join(out_dir, 'all_piv.txt'), sep=';')

# vlinders
vli_piv= pd.pivot_table(data=dat.loc[dat['soort'] == 'vlinder', :], index='snl', columns='n', values='hok_id',
                        aggfunc=lambda x: len(x.unique()))
vli_piv.to_csv(os.path.join(out_dir, 'vli_piv.txt'), sep=';')

# planten
pla_piv = pd.pivot_table(data=dat.loc[dat['soort'] == 'plant', :], index='snl', columns='n', values='hok_id',
                        aggfunc=lambda x: len(x.unique()))
pla_piv.to_csv(os.path.join(out_dir, 'pla_piv.txt'), sep=';')

# vogels
vog_piv = pd.pivot_table(data=dat.loc[dat['soort'] == 'vogel', :], index='snl', columns='n', values='hok_id',
                        aggfunc=lambda x: len(x.unique()))
vog_piv.to_csv(os.path.join(out_dir, 'vog_piv.txt'), sep=';')

# per groep
grp_piv = pd.pivot_table(data=dat, index='soort', columns='periode', values='hok_id', aggfunc=lambda x: len(x.unique()))
grp_piv.to_csv(os.path.join(out_dir, 'pergroep.txt'), sep=';')