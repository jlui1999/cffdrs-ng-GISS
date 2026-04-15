# EXAMPLE SCRIPT for downloading weather data from ERA5
# Setting up csdapi: https://cds.climate.copernicus.eu/how-to-api
# ERA5 dataset: https://cds.climate.copernicus.eu/datasets/reanalysis-era5-land-timeseries?tab=overview

import cdsapi
import netCDF4 as nc
import numpy as np

# bounding boxings for Spain and Portugal
#(-9.39288367353, 35.946850084, 3.03948408368, 43.7483377142)
#(-9.52657060387, 36.838268541, -6.3890876937, 42.280468655)

# download files based off of topology file, skipping points where specified variable is <0 (for example, land mask)
topo = "9ae80a6b2133fa0941092a7d564b9160.nc" # this is the ERA5 provided mask
topo_var = "lsm"

start_lat = 35.94
start_lon = -9.53
end_lat = 43.75
end_lon = 3.04

stride = 2

# originally a simple one, but meant for lat/lon so stuff like upside down latitude or longitudes that go from 0-360 also need to be accounted for
def find_nearest_sorted(array, value, qualifier=None):
    # reverse sorted
    if (array[0] > array[-1]):
        reverse = True
        array = array[::-1]
    else:
        reverse = False

    if (all(a >= 0 for a in array) and value < 0):
        lon360 = True
        value += 360
    else:
        lon360 = False
    # Find where the value would be inserted
    idx = np.searchsorted(array, value, side="left")

    # Boundary checks
    if (idx == 0):
        if (reverse):
            return len(array) - 1
        else:
            return idx
    if (idx == len(array) - 1):
        if (reverse):
            return idx
        else:
            return 0

    # Compare left and right neighbors to find the truly closest
    left = array[idx-1]
    right = array[idx]
    if qualifier is None:
        if abs(value - left) < abs(value - right):
            ret = idx-1
        else:
            ret = idx
    elif qualifier == 'larger':
        ret = idx
    elif qualifier == 'smaller':
        ret = idx-1

    if (reverse):
        ret = len(array) - ret - 1
    if (lon360):
        ret -= len(array)
    return ret

dataset = "reanalysis-era5-land-timeseries"
client = cdsapi.Client()

with nc.Dataset(topo, mode='r') as dataset:
    lat = dataset['latitude'][:]
    lon = dataset['longitude'][:]

    start_lat_idx = find_nearest_sorted(lat, start_lat, qualifier='smaller')
    start_lon_idx = find_nearest_sorted(lon, start_lon, qualifier='smaller')
    end_lat_idx = find_nearest_sorted(lat, end_lat, qualifier='larger')
    end_lon_idx = find_nearest_sorted(lon, end_lon, qualifier='larger')

    #print(start_lat_idx, start_lon_idx, end_lat_idx, end_lon_idx)
    #print(lat[start_lat_idx], lon[start_lon_idx], lat[end_lat_idx], lon[end_lon_idx])

    latrange = range(start_lat_idx, end_lat_idx+1, stride) if (start_lat_idx < end_lat_idx) else range(end_lat_idx, start_lat_idx+1, stride)
    lonrange = range(start_lon_idx, end_lon_idx+1, stride) if (start_lon_idx < end_lon_idx) else range(end_lon_idx, start_lon_idx+1, stride)

    #print(latrange)
    #print(lonrange)

    for i in latrange:
        for j in lonrange:
            print(i,j,lat[i],lon[j],dataset[topo_var][0,i,j] > 0)
            continue
            if (dataset[topo_var][0,i,j] > 0):
                request = {
                "variable": [
                    "2m_dewpoint_temperature",
                    "2m_temperature",
                    "total_precipitation",
                    "10m_u_component_of_wind",
                    "10m_v_component_of_wind"
                ],
                "location": {"longitude": lon[j], "latitude": lat[i]},
                "date": ["1950-01-01/2026-02-20"],
                "data_format": "csv"
                }
                client.retrieve(dataset, request).download()

exit()

# get just a grid, no checking for masks
start_lat = 36.00
start_lon = -9.5
end_lat = 43.75
end_lon = 3.00

lat = start_lat
while (lat <= end_lat):
    lon = start_lon
    while (lon <= end_lon):
        print (lat, lon)
        request = {
            "variable": [
                "2m_dewpoint_temperature",
                "2m_temperature",
                "total_precipitation",
                "10m_u_component_of_wind",
                "10m_v_component_of_wind"
            ],
            "location": {"longitude": lon, "latitude": lat},
            "date": ["1950-01-01/2026-02-20"],
            "data_format": "csv"
        }
        client.retrieve(dataset, request).download()
        lon += 0.25 # seems like ERA5 data is in one-tenths of a degree, so these are rounded up/down
    lat += 0.25

