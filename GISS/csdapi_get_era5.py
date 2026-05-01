# Script for downloading weather data from ERA5 from a list of lat/lon coordinates
# Setting up csdapi: https://cds.climate.copernicus.eu/how-to-api
# ERA5 dataset: https://cds.climate.copernicus.eu/datasets/reanalysis-era5-land-timeseries?tab=overview

import cdsapi, subprocess 
from giss_config import *

subprocess.call(["mkdir",
                "-p",
                "{}/{}/{}".format(projectDir, regionName, downloadedFolder)
                 ])

client = cdsapi.Client()

with open("{}/{}/{}".format(projectDir, regionName, pointLocations)) as f:
    counter = 0
    for line in f:
        counter += 1
        if (line[0] == '#'):
            continue
        latlon = line.strip().split('#')[0].split(',')
        if (len(latlon) != 3):
            print("Line {}: does not have three entries, skipping...")
            continue
        station_id = latlon[0]
        lat = float(latlon[1])
        lon = float(latlon[2])
        request = {
            "variable": variableRequest,
            "location": {"longitude": lon, "latitude": lat},
            "date": ["{}/{}".format(start_date, end_date)],
            "data_format": "csv"
        }

        target = "{}/{}/{}/{}_{}.zip".format(projectDir, regionName, downloadedFolder, downloadedPrefix, station_id)

        client.retrieve(dataset, request, target)

