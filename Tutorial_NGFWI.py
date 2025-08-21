#### Next Generation Fire Weather Index System (FWI2025) Getting Started ####
# April 2025
#
# This script was designed to go with the Getting Started Tutorial to inform
# users how to use scripts associated with FWI2025. Follow along
# with the 'Getting Started Tutorial' documentation on the CFFDRS2025 webpages:
# https://cffdrs.github.io/website_en/tutorials
# This tutorial will demonstrate how to generate FWI2025 outputs based on an
# input from a .csv. The method will differ if using another source file type or
# if integrating code into existing fire management systems. This tutorial
# assumes the user has a working level knowledge of Python.
##############################################################################

### Load packages - ensure you have the necessary packages installed ###
import pandas as pd
from datetime import datetime
from timezonefinder import TimezoneFinder
from pytz import timezone

### Load FWI2025 functions ###
# NG_FWI.py, util.py, and daily_summaries.py files contain the functions necessary
# to calculate FWI2025. For the import to work, the working directory
# must match the file location where these three files are stored.
from NG_FWI import hFWI
from daily_summaries import generate_daily_summaries

import sys

initializeCodes = False
if (len(sys.argv) < 3):
    print('Usage: python Tutorial_NGFWI.py <data file> <output file> [ffmc] [dmc] [dc]')
    exit()
elif (len(sys.argv) == 6):
    ffmc = float(sys.argv[3])
    dmc = float(sys.argv[4])
    dc = float(sys.argv[5])
    initializeCodes = True

datafile = sys.argv[1] 
outputfile = sys.argv[2]

# command line FWI starting codes will override starting codes read from file
if (not initializeCodes):
    with open(datafile, mode='r') as d:
        header = d.readline().strip()
        # the header may or may not have a starting FWI codes placed after the last row as a comment
        headerarr = header.split('#')
        if (len(headerarr) == 4):
            ffmc = float(headerarr[1])
            dmc = float(headerarr[2])
            dc = float(headerarr[3])
            initializeCodes = True

### Load the input weather station file ###
# Specify the file path if wx_prf.csv is not in working directory
data = pd.read_csv(datafile, comment='#')

# Print the first 5 rows, data should contain 11 columns:
#     id        lat       long    yr  mon  day  hr   temp     rh      ws  prec   
# 0  PRF  46.013925 -77.418044  2007    5   10   8  14.78  94.90  2.7324   0.0   
# 1  PRF  46.013925 -77.418044  2007    5   10   9  17.44  79.11  3.6663   0.0   
# 2  PRF  46.013925 -77.418044  2007    5   10  10  21.21  62.95  4.3590   0.0   
# 3  PRF  46.013925 -77.418044  2007    5   10  11  23.60  46.17  8.2100   0.0   
# 4  PRF  46.013925 -77.418044  2007    5   10  12  24.55  41.53  9.4200   0.0
print(data.head())

### Find the timezone ###
# First, make a dataframe of stations with unique ID, latitude, and longitude.
stations = data.loc[:, ['id', 'lat', 'long']].drop_duplicates()
# Print the unique station IDs and locations. For this dataset the only station
# is at Petawawa Research Forest (PRF).
print(stations)

# Find the timezone based on latitude and longitude
tf = TimezoneFinder()
tz_loc = tf.timezone_at(lat = stations.at[0, 'lat'], lng = stations.at[0, 'long'])
# Print timezone location. PRF is equivalent to "America/Toronto".
print(tz_loc)

### Find the UTC offset ###
# The UTC timezone offset is a required input for the FWI2025 function.
# Since weather data is normally collected using standard time (not daylight time),
# the date is set to January 1. Using dates from the dataset (during the summer fire
# season) gives the UTC offset for daylight time which is off by 1.
utc = timezone(tz_loc).localize(datetime(2007, 1, 1)).strftime('%z')
# Print utc offset, for this tutorial, "PRF" is in Eastern Time (EST), so UTC is
# '-0500'
print(utc)

# The UTC offset input is expected as integer hours, so we can set it to -5.
#utc = -5
utc = int(utc[:3])
print(utc)

### Calculate hourly FWI System outputs with FWI2025 ###
# hFWI() is the function that calculates hourly FWI codes in FWI2025. It can
# handle multiple stations and years/fire seasons (not shown in this tutorial).
# Make sure to specify the corresponding UTC offsets for different stations.
# Default starting FWI codes are: ffmc_old = 85, dmc_old = 6, dc_old = 15
if (initializeCodes):
    print("Starting FWI run with starting codes FFMC={}, DMC={}, DC={}".format(ffmc, dmc, dc))
    data_fwi = hFWI(data, utc, ffmc_old=ffmc, dmc_old=dmc, dc_old=dc)
else:
    data_fwi = hFWI(data, utc)

# Output is a dataframe, with first 11 columns being the same as input, now plus:
# percent_cured, date, timestamp, timezone, solrad, sunrise, sunset, sunlight_hours,
# ffmc, dmc, dc, isi, bui, fwi, dsr, gfmc, gsi, gfwi
# Save the output as a .csv file (overrides any data in any pre-existing file)
data_fwi.to_csv(outputfile)

# The last two rows for ffmc, dmc, dc, isi, bui, and fwi should look like this:
#            ffmc        dmc          dc       isi        bui       fwi
# 2621  80.266881  10.053992  212.841711  1.642292  17.984189  2.172703
# 2622  82.175898  10.311868  213.378111  2.146157  18.400630  3.174787
standard_components = ['ffmc', 'dmc', 'dc', 'isi', 'bui', 'fwi']
data_fwi.loc[:, standard_components].tail(2)

# Print a simple summary of the standard FWI components.
data_fwi.loc[:, standard_components].describe()

### Calculate daily summaries ###
# Calculate outputs like peak burn time and number of hours of spread potential.
report = generate_daily_summaries(data_fwi)

# Daily report is a data frame with columns:
# wstind, yr, mon, day, peak_time, duration, wind_speed_smoothed,
# peak_isi_smoothed, ffmc, dmc, dc, isi, bui, fwi, dsr, sunrise, sunset

# View a distribution of the hour of daily peak burn, which looks like this:
# peak_time
# 13     1
# 14     2
# 15     4
# 16    10
# 17    53
# 18    23
# 19    14
# 20     1
# 23     1
# Name: count, dtype: int64
print(report['peak_time'].value_counts().sort_index())

# From here, the outputs can be converted to any datatype for further analysis or
# plotted for visualization.
