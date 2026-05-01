import pandas as pd
import numpy as np
import argparse, os, subprocess
from giss_utils import get_timezone
import calendar, time
from datetime import datetime
from multiprocessing import Pool
from giss_config import *

subprocess.call(["mkdir",
                "-p",
                "{}/{}/{}".format(projectDir, regionName, convertedFolder)
                 ])

# Teten's equation without the constant in the front
def tetens(temp):
    if (temp > 0):
        return np.exp(17.27 * temp / (temp + 237.3))
    else:
        return np.exp(21.875 * temp / (temp + 265.5))

vtetens = np.vectorize(tetens)

def do_conversion(inputfile, outputfile=None):
    start_time = time.perf_counter()
    # create a temp working directory to store unzipped files
    if outputfile is None:
        outdir_temp = "./{}".format(".".join(inputfile.split('/')[-1].split('.')[:-1]))
    else:
        outdir_temp = "{}/{}".format("/".join(outputfile.split('/')[0:-1]), ".".join(inputfile.split('/')[-1].split('.')[0:-1]))

    subprocess.call(["mkdir", "-p", outdir_temp])
    subprocess.call(["unzip", "-o", inputfile, "-d", outdir_temp])
    unzipped = os.listdir(outdir_temp)

    # read data and merge into single dataframe
    df = pd.read_csv("{}/{}".format(outdir_temp, unzipped[0]))
    df2 = pd.read_csv("{}/{}".format(outdir_temp, unzipped[1]))
    df3 = pd.read_csv("{}/{}".format(outdir_temp, unzipped[2]))

    # remove columns
    df2.drop(columns=['latitude', 'longitude'], inplace=True)
    df3.drop(columns=['latitude', 'longitude'], inplace=True)

    df = df.join(df2.set_index('valid_time'), on='valid_time')
    df = df.join(df3.set_index('valid_time'), on='valid_time')

    del df2
    del df3

    # check if data is actually present, downloaded era5 files can have no data at all
    if (df['t2m'].iloc[0] != df['t2m'].iloc[0]):
        print("{} seems to have no valid data, skipping...".format(inputfile))
        return

    # convert to datetime format
    df['date'] = pd.to_datetime(df['valid_time'])

    # filter years
    if (start_year == 0 and end_year == 0):
        pass
    elif (start_year == 0):
        df = df[(df['date'] < datetime(end_year+1, 1, 1))]
    elif (end_year == 0):
        df = df[(df['date'] >= datetime(start_year, 1, 1))]
    else:
        df = df[(df['date'] >= datetime(start_year, 1, 1)) & (df['date'] < datetime(end_year+1, 1, 1))]

    # there are now five data columns tp, u10, v10, d2m, t2m
    # tp = total percipitation (m)
    # u10 = 10m u component of wind (m/s)
    # v10 = 10m v component of wind (m/s)
    # d2m = 2m dewpoint temperature (K)
    # t2m = 2m temperature (K)

    # from this data, calculate four varibles for FWI input
    # temp = t2m - 273.15 (C)
    # rh = 100 * exp(17.27 * d2m/(237.3 + d2m)) / exp(17.27 * t2m/(237.3 + t2m)) (%) (using Tetens equation > 0C)
    # ws = sqrt(u10**2 + v10**2) / 1000 * 3600 (km/hr)
    # prec = tp * 1000 (mm)

    lat = df['latitude'].iloc[0]
    lon = df['longitude'].iloc[0]

    # also rename these
    df.rename(columns={'latitude': 'lat', 'longitude': 'long'}, inplace=True)

    if (lat > 90 or lat < -90):
        print("latitude {} is invalid".format(lat))
        exit(10)
    if (lon > 360 or lon < -360):
        lon %= 360
    if (lon > 180):
        lon -= 360

    # generate an id and use as output file name if one is not provided already
    llat = 'N'
    llon = 'E'

    if (lat < 0):
        llat = 'S'
    if (lon < 0):
        llon = 'W'
    station_id = "{:.2f}{}_{:.2f}{}".format(np.abs(lat), llat, np.abs(lon), llon)
    if outputfile is None:
        outputfile = "era5input_{}.csv".format(station_id)

    df['id'] = np.full(len(df), station_id)

    timezone = get_timezone(lat, lon)
    df['timezone'] = np.full(len(df), timezone)

    # new columns
    df['yr'] = df['date'].dt.year
    df['mon'] = df['date'].dt.month
    df['day'] = df['date'].dt.day
    df['hr'] = df['date'].dt.hour

    # conversions
    df['temp'] = df['t2m'] - 273.15
    df['prec'] = np.maximum(df['tp'] * 1000, 0)
    df['ws'] = np.maximum(np.hypot(df['u10'], df['v10']) * 3.6, 0)
    df['rh'] = np.minimum(vtetens(df['d2m'] - 273.15) / vtetens(df['t2m'] - 273.15) * 100, 100)


    df.to_csv(outputfile, columns=['id', 'lat', 'long', 'timezone', 'yr', 'mon', 'day', 'hr', 'temp', 'rh', 'ws', 'prec'], index=False)
    end_time = time.perf_counter()
    print("Converted {} to {}, time taken {:6f}s".format(inputfile, outputfile, end_time - start_time))
    subprocess.call(["rm", "-rf", outdir_temp])

if __name__ == '__main__':
    counter = 0
    conversion_args = []
    inputfile = "{}/{}/{}".format(projectDir, regionName, pointLocations)
    with open(inputfile, mode='r') as ifile:
        for line in ifile:
            counter += 1
            if (line[0] == '#'):
                continue
            iline = line.strip().split('#')[0].split(',')
            station_id = iline[0]
            inzipfile = "{}/{}/{}/{}_{}.zip".format(projectDir, regionName, downloadedFolder, downloadedPrefix, station_id)
            if (not os.path.isfile(inzipfile)):
                print("Line {}: {} does not exist or is an invalid file, skipping...".format(counter, inzipfile))
            else:
                converted_file = "{}/{}/{}/{}_{}.csv".format(projectDir, regionName, convertedFolder, convertedPrefix, station_id)
                conversion_args.append((inzipfile, converted_file))
    if (do_multiprocess):
        pool = Pool()
        pool.starmap(do_conversion, conversion_args)
        pool.close()
        pool.join()
    else:
        for cargs in conversion_args:
            do_conversion(*cargs)

