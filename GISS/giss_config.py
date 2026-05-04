projectDir = './JamesData/ERA5-Land-NGFWI/'
regionName = 'IberianPeninsulaGrid'

do_multiprocess = True # sets if parallel processing is performed on era5_convert.py and giss_hourly_FWI_parallel.py

# when running scripts, a folder named <projectDir>/<regionName>/<XYZFolder>/ will be created from the working folder

###############  get_landmask.py ###############
# downloads land mask provided by ERA5, set the name of the file here
# https://cds.climate.copernicus.eu/datasets/reanalysis-era5-land 'land_sea_mask'
topo = "era5_landmask.nc"  
topo_var = "lsm" # land mask variable

########## generate_grid_of_points.py ##########
# generate a list of grid points to download, based off of topography file, skipping points where specified variable is <0 (for example, land mask)
# bounding boxings for Spain and Portugal
#(-9.39288367353, 35.946850084, 3.03948408368, 43.7483377142)
#(-9.52657060387, 36.838268541, -6.3890876937, 42.280468655)
start_lat = 35.94
start_lon = -9.53
end_lat = 43.75
end_lon = 3.04
stride = 2 # step size of generated grid points if the generated grid has too many points, stride 2 skips every other cell on each dimension, reducing total number of points by a factor of 4
pointLocations = 'IberianPeninsulaGridLocations.csv' # if defining a custom-made point location, scripts will search for it in <projectDir>/<regionName>/<pointLocations> from the working folder

############## csdapi_get_era5.py ##############
# select variables and date range
start_date = '1950-01-01' # YYYY-MM-DD
end_date = '2026-02-20'
dataset = "reanalysis-era5-land-timeseries"
variableRequest = [ # List of variables to download
        "2m_dewpoint_temperature",
        "2m_temperature",
        "total_precipitation",
        "10m_u_component_of_wind",
        "10m_v_component_of_wind"
        ]
downloadedPrefix = "era5download"
downloadedFolder = "DownloadedData"

###############  era5_convert.py ###############
start_year = 1980 # specify range of conversion from era5 dataset
end_year = 2020
convertedPrefix = "era5converted"
convertedFolder = "ConvertedData"

#########  giss_hourly_FWI_parallel.py #########
# starting codes, specify None for all to use default codes specified by cffdrs (ffmc = 85, dmc = 6, dc = 15)
# if defined here, starting codes will override any starting codes defined in the list of points
init_ffmc = None
init_dmc = None
init_dc = None
fwiPrefix = "era5FWI"
fwiFolder = "FWIData"
