import netCDF4 as nc
import numpy as np
import subprocess
from giss_config import *
from giss_utils import find_nearest_sorted_latlon

subprocess.call(["mkdir",
                "-p",
                "{}/{}".format(projectDir, regionName)
                 ])

outfile = "{}/{}/{}".format(projectDir, regionName, pointLocations)

with nc.Dataset(topo, mode='r') as dataset, open(outfile, mode='w') as f:
    lat = dataset['latitude'][:]
    lon = dataset['longitude'][:]

    start_lat_idx = find_nearest_sorted_latlon(lat, start_lat, qualifier='smaller')
    start_lon_idx = find_nearest_sorted_latlon(lon, start_lon, qualifier='smaller')
    end_lat_idx = find_nearest_sorted_latlon(lat, end_lat, qualifier='larger')
    end_lon_idx = find_nearest_sorted_latlon(lon, end_lon, qualifier='larger')

    #print(start_lat_idx, start_lon_idx, end_lat_idx, end_lon_idx)
    #print(lat[start_lat_idx], lon[start_lon_idx], lat[end_lat_idx], lon[end_lon_idx])

    latrange = range(start_lat_idx, end_lat_idx+1, stride) if (start_lat_idx < end_lat_idx) else range(end_lat_idx, start_lat_idx+1, stride)
    lonrange = range(start_lon_idx, end_lon_idx+1, stride) if (start_lon_idx < end_lon_idx) else range(end_lon_idx, start_lon_idx+1, stride)

    #print(latrange)
    #print(lonrange)

    topo = dataset[topo_var][0,:,:]
    for i in latrange:
        for j in lonrange:
            if (topo[i,j] > 0):
                lat_i = lat[i]
                lon_j = lon[j]

                # adjust longitude to be -180 to 180 instead of 0 to 360
                if (lat_i > 90 or lat_i < -90):
                    print("latitude {} is invalid".format(lat))
                    continue
                if (lon_j > 360 or lon_j < -360):
                    lon_j %= 360
                if (lon_j > 180):
                    lon_j -= 360

                # generate a station id from lat/lon
                llat = 'N'
                llon = 'E'

                if (lat_i < 0):
                    llat = 'S'
                if (lon_j < 0):
                    llon = 'W'
                station_id = "{:.2f}{}_{:.2f}{}".format(abs(lat_i), llat, abs(lon_j), llon)
                f.write("{},{:.2f},{:.2f}\n".format(station_id,lat_i,lon_j))


