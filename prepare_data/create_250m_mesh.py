# script to create 250 m mesh polygon shapefile based on top-left coordinates
# Hans Roelofsen, WEnR, 20/03/1019

import os
import numpy as np
import geopandas as gp
from shapely import geometry

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


dat = pgo.get_all_obs()
hokken = list(set(dat['hok_id']))
hok_topleft_x = np.int32([id.split('_')[0] for id in hokken])
hok_topleft_y = np.int32([id.split('_')[1] for id in hokken])

hok250 = gp.GeoDataFrame(crs={"init": "epsg:28992"})
hok250['topleftx'] = hok_topleft_x
hok250['toplefty'] = hok_topleft_y
hok250['geometry'] = hok250.apply(lambda row: geometry.Polygon(create_250m_hok((row['topleftx'], row['toplefty']))),
                                  axis=1)
hok250['ID'] = hok250.apply(lambda row: '{0}_{1}'.format(row['topleftx'], row['toplefty']), axis=1)
print(hok250.head())
hok250.to_file(r'd:\hotspot_working\shp_250mgrid\hok250m.shp')
