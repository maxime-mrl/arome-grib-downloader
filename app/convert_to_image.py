# based from architecture-performance.fr/ap_blog/fetching-arome-weather-forecasts-and-plotting-temperatures

import os
import pygrib
import matplotlib.pyplot as plt
import numpy as np
import geopandas as gpd
from shapely.geometry import Polygon

# arome runs are splitted into different time ranges up to 51h
arome_time_ranges = [ '00H06H', '07H12H', '13H18H', '19H24H', '25H30H', '31H36H', '37H42H', '43H48H', '48H51H' ]

# read all gribs and open them in grbs array
files = os.listdir(os.path.join(os.getcwd(), "data"))
grbs = []
for file in files:
    file_path = os.path.join(os.getcwd(), "data", file)
    grbs.append(pygrib.open(file_path))

# 3d array w/ numpy
arrays = []
grb_hours = grbs[0].select(name='Temperature', level=10)
for idx in range(len(grb_hours)):
    temper = np.copy(grb_hours[idx].values[::-1,])  # revert first axis
    arrays.append(temper - 273.15) # append to array in celsius
temperatures = np.stack(arrays, axis=2)

# create map
grb = grbs[0][351]
lats, lons = grb.latlons()  # WGS84 projection
# assume that the grid is a uniform Catesian 801 x 601 grid.
shape = lats.shape
x = np.linspace(lons.min(), lons.max(), shape[1])
y = np.linspace(lats.min(), lats.max(), shape[0])
X, Y = np.meshgrid(x, y)
print(X)
# compute ratio
ratio = (lats.max() - lats.min()) / (lons.max() - lons.min()) 
size_int = 20
fig_size = (size_int, int(round(ratio * size_int)))


# https://www.naturalearthdata.com/downloads/10m-cultural-vectors/10m-admin-0-countries/
world = gpd.read_file(os.path.join(os.getcwd(), "countries", "ne_10m_admin_0_countries.shp"))
ax = world.plot(color='white', edgecolor='black')

# select map aera
bb_polygon = Polygon([
    (lons.min(), lats.min()),
    (lons.max(), lats.min()),
    (lons.max(), lats.max()),
    (lons.min(), lats.max())
])
bbox = gpd.GeoDataFrame(geometry=[bb_polygon], crs="EPSG:4326")
france = gpd.overlay(world, bbox, how='intersection')
france.plot(color='white', edgecolor='black')

for k in range(temperatures.shape[2]):
    fig, ax = plt.subplots(figsize=fig_size)
    CS = ax.contourf(X, Y, temperatures[:,:,k], levels=np.arange(10, 30), cmap='jet')
    france.geometry.boundary.plot(ax=ax, color=None, edgecolor='k',linewidth=2, alpha=0.25)
    cbar = fig.colorbar(CS)
    plt.savefig(os.path.join(os.getcwd(), "results",  f'temperature_{str(k).zfill(2)}.png'))