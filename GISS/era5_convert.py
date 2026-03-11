import pandas as pd
import numpy as np
import argparse, os, subprocess
from get_timezone_util import get_timezone
import calendar
from datetime import datetime

parser = argparse.ArgumentParser()

parser.add_argument('-i', '--input', nargs=1, required=True, help='ZIP file of ERA5 data')
parser.add_argument('-o', '--output', nargs=1, help='Output csv file, if not specified filename will be placed in working directory and named based on lat/lon')
parser.add_argument('--from', nargs=1, help='Start year')
parser.add_argument('--to', nargs=1, help='End year')

args = parser.parse_args()

inputfile = None
outputfile = None
outdir_temp = None
start_year = 0
end_year = 0

for k,v in vars(args).items():
    if (k == 'input'):
        if (not os.path.isfile(v[0])):
            print("Specified file {} does not exist, exiting...".format(v[0]))
            exit(1)
        elif (v[0].split('.')[-1].lower() != 'zip' and v[0].split('.')[-1].lower() != 'txt'):
            print("Input file must be a zip or a txt file")
            exit(2)
        else:
            inputfile = v[0]
    if (k == 'output'):
        if v is not None:
            outputfile = v[0]
            if (outputfile.split('.')[-1].lower() != 'csv'):
                print("Output file must be a csv file")
    if (k == 'from'):
        if v is not None:
            start_year = int(v[0])
    if (k == 'to'):
        if v is not None:
            end_year = int(v[0])

# Teten's equation without the constant in the front
def tetens(temp):
    if (temp > 0):
        return np.exp(17.27 * temp / (temp + 237.3))
    else:
        return np.exp(21.875 * temp / (temp + 265.5))

vtetens = np.vectorize(tetens)

def do_conversion(inputfile, outputfile=None):
    # create a temp working directory to store unzipped files
    if outputfile is None:
        outdir_temp = "./{}".format(inputfile.split('/')[-1].split('.')[0])
    else:
        outdir_temp = "{}/{}".format("/".join(outputfile.split('/')[0:-1]), inputfile.split('/')[-1].split('.')[0])

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

    # convert to datetime format
    df['date'] = pd.to_datetime(df['valid_time'])

    # filter years
    if (start_year == 0 and end_year == 0):
        pass
    elif (start_year == 0):
        df = df[(df['date'] >= df['date'].iloc[0]) & (df['date'] < datetime(end_year+1, 1, 1))]
    elif (end_year == 0):
        df = df[(df['date'] >= datetime(start_year, 1, 1)) & (df['date'] <= df['date'].iloc[-1])]
    else:
        df = df[(df['date'] >= df['date'].iloc[0]) & (df['date'] <= df['date'].iloc[-1])]

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
        lon -= 180

    # generate an id and use as output file name if one is not provided already
    llat = 'N'
    llon = 'E'

    if (lat < 0):
        llat = 'S'
    if (lon < 0):
        llon = 'W'
    station_id = "{:.2f}{}{:.2f}{}".format(lat, llat, lon, llon)
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
    df['prec'] = df['tp'] * 1000
    df['ws'] = np.hypot(df['u10'], df['v10']) * 3.6
    df['rh'] = vtetens(df['d2m'] - 273.15) / vtetens(df['t2m'] - 273.15) * 100

    df.to_csv(outputfile, columns=['id', 'lat', 'long', 'timezone', 'yr', 'mon', 'day', 'hr', 'temp', 'rh', 'ws', 'prec'], index=False)
    print("Written to {}".format(outputfile))
    #subprocess.call(["rm", "-rf", outdir_temp])

do_conversion(inputfile, outputfile=outputfile)
