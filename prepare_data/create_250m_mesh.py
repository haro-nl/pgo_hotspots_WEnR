# script to create 250 m mesh polygon shapefile based on top-left coordinates
# Hans Roelofsen, WEnR, 20/03/1019

import os
import numpy as np
import geopandas as gp
import rasterio as rio
from shapely import geometry
import pandas as pd

from utils import pgo

def create_250m_hok(xy):
    # return X,Y coordinates of 125m sided square with vertices (a, b, c, d), clockwise starting from point a, topleft
    # input xy must be x, y of vertex a, ie. topleft point, so that:
    # vertex a: xmin, ymax
    # vertex b: xmax, ymax
    # vertex c: xmax, ymin
    # vertex d: xmin, ymin

    xtopleft, ytopleft = xy
    xmin, xmax = xtopleft, xtopleft + 250
    ymin, ymax = ytopleft - 250, ytopleft
    return [(xmin, ymax), (xmax, ymax), (xmax, ymin), (xmin, ymin)]


asc = rio.open(os.path.join(r'd:\hotspot_working\a_broedvogels\SNL_grids', 'Heide.asc'))  #Example ASCII dataset
specs = pgo.get_specs(r'd:\hotspot_working\a_broedvogels\SNL_grids', 'Heide.asc')
vals = np.reshape(asc.read(1), newshape=np.product(asc.shape), order='C').astype(np.int32)

db = pd.DataFrame({'hok': vals})
db['row'] = np.array([[i] * specs['NCOLS'] for i in range(0, specs['NROWS'])]).reshape(np.product(asc.shape))
db['col'] = np.array([i for i in range(0, specs['NCOLS'])] * specs['NROWS']).reshape(np.product(asc.shape))
# note that coordinates are calculated for the row,col indices, which means they apply to the cell top-left!
db['x_rd'] = db.apply(lambda x: ((x.col, x.row) * asc.affine)[0], axis=1).astype(np.int32)
db['y_rd'] = db.apply(lambda x: ((x.col, x.row) * asc.affine)[1], axis=1).astype(np.int32)


hok250 = gp.GeoDataFrame(crs={"init": "epsg:28992"})
hok250['topleftx'] = db['x_rd']
hok250['toplefty'] = db['y_rd']
hok250['geometry'] = hok250.apply(lambda row: geometry.Polygon(create_250m_hok((row['topleftx'], row['toplefty']))),
                                  axis=1)
hok250['ID'] = hok250.apply(lambda row: '{0}_{1}'.format(row['topleftx'], row['toplefty']), axis=1)

# read provincies and join to the hokken
prov = gp.read_file(r'd:\NL\provincies_2018\poly\provincies_2018.shp')

hok_prov = gp.sjoin(left_df=hok250, right_df=prov, op='intersects', how='left')

print(hok_prov.head())
print(hok_prov.shape)
print(hok250.shape)


# hok_prov.to_file(r'd:\hotspot_working\shp_250mgrid\hok250m_fullextent.shp')
