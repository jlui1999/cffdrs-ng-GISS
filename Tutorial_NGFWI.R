#### Next Generation Fire Weather Index System (FWI2025) Getting Started ####
# February 2025 (Last updated April 2025)
#
# This script was designed to go with the Getting Started Tutorial to inform
# users how to use scripts associated with FWI2025. Follow along
# with the 'Getting Started Tutorial' documentation on the CFFDRS2025 webpages:
# https://cffdrs.github.io/website_en/tutorials
# This tutorial will demonstrate how to generate FWI2025 outputs based on an
# input from a .csv. The method will differ if using another source file type or
# if integrating code into existing fire management systems. This tutorial
# assumes the user has working level knowledge of R.
##############################################################################

### Load libraries - ensure you have the necessary libraries installed ###
# Run install.packages() to install any you are missing
library(lubridate)
library(data.table)
library(lutz)

args = commandArgs(trailingOnly=TRUE)
print(args)
numargs = length(args)
if (numargs < 2) {
  print('Usage: Rscript Tutorial_NGFWI.R <data file> <output file> [ffmc] [dmc] [dc]')
  quit()
}

datafile = args[1]
outputfile = args[2]

if.initializeCodes = FALSE
if (numargs == 5) {
  ffmc = args[3]
  dmc = args[4]
  dc = args[5]
  if.initializeCodes = TRUE
}

Rpath = Sys.getenv("R_Fire")
Rpath

if (Rpath=="") {
  cat("Please set environment variable R_Fire to the path to your FireWeather directory")
  quit()
}

### Load FWI2025 functions ###
# NG_FWI.r and util.r files contain the functions necessary to calculate FWI2025.
# For the source() function to work, the working directory must match the
# file location where these two files are stored.

# Check your current working directory
getwd()
# If the working directory is different from where you saved the NG-CFFDRS scripts,
# change the working directory with setwd() to that folder.
# setwd("\\")

# Load the source files containing the variables and functions to calculate FWI2025.
source(paste0(Rpath, "/NG_FWI.r"))
source(paste0(Rpath, "/util.r"))
source(paste0(Rpath, "/daily_summaries.R"))

### Load the input weather station file ###
# Specify the file path if wx_prf.csv is not in working directory
#data <- read.csv('wx_prf.csv')
data <- read.csv(datafile)

# Print the column names, data should contain the following 11 columns:
# id, lat, long, yr, mon, day, hr, temp, rh, ws, prec
names(data)

### Find the timezone ###
# The 'lutz' library has functions to get the timezone of the weather station
# based on latitude and longitude. First, make a dataframe of stations with
# unique ID, latitude, and longitude.
stations <- unique(data[c("id", "lat", "long")])
# Print the unique station IDs and coordinates. For this dataset the only station
# is at Petawawa Research Forest (PRF).
stations

# Find the timezone based on latitude and longitude, this can take some time.
# You may need to download the package 'sf' for method = "accurate".
tz_loc <- tz_lookup_coords(stations$lat, stations$long, method = "accurate")
# Print the timezone location. PRF is equivalent to "America/Toronto".
tz_loc

### Find the UTC offset ###

# The UTC timezone offset is a required input for the FWI2025 function.
# Since weather data is normally collected using standard time (not daylight time),
# the date is set to January 1. Using dates from the dataset (during the summer fire
# season) gives the UTC offset for daylight time which is off by 1.
utc <- tz_offset("2007-01-01", tz_loc)[[5]]
# Print utc offset, for this tutorial, "PRF" is in Eastern Time (EST), so UTC -5
utc

### Calculate hourly FWI System outputs with FWI2025 ###
# hFWI() is the function that calculates hourly FWI codes in FWI2025. It can
# handle multiple stations and years/fire seasons (not shown in this tutorial).
# Make sure to specify the corresponding UTC offsets for different stations.
# Default starting FWI codes are: ffmc_old = 85, dmc_old = 6, dc_old = 15
if (if.initializeCodes) {
  data_fwi <- hFWI(data, utc, ffmc_old=ffmc, dmc_old=dmc, dc_old=dc)
} else {
  data_fwi <- hFWI(data, utc)
}

# Output is a data TABLE, with FWI calculations appended after the input columns.
# Save the output as a .csv file (overrides any data in any preexisting file).
#write.csv(data_fwi, "wx_prf_fwi_R.csv")
write.csv(data_fwi, outputfile)

# View a simple summary of the standard FWI components.
standard_components <- c("ffmc", "dmc", "dc", "isi", "bui", "fwi")
View(summary(data_fwi[, ..standard_components]))

### Calculate daily summaries ###
# Calculate outputs like peak burn time and number of hours of spread potential.
report <- generate_daily_summaries(data_fwi)

# View a simple summary of the daily report (convert values to numeric class first).
daily_components <- c("peak_time", "duration", "peak_isi_smoothed", "dsr")
View(summary(apply(report[daily_components], 2, as.numeric)))

# From here, the outputs can be converted to any datatype for further analysis or
# plotted for visualization.

