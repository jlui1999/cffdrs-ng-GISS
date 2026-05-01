import cdsapi
from giss_config import topo

dataset = "reanalysis-era5-land"
request = {
    "variable": ["land_sea_mask"],
    "data_format": "netcdf",
    "download_format": "unarchived"
}

client = cdsapi.Client()
client.retrieve(dataset, request, topo)
