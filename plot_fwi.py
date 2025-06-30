# make FWI output plots

import pandas as pd
import numpy as np
import argparse, os
import matplotlib.pyplot as plt

parser = argparse.ArgumentParser()

parser.add_argument('-i', '--input', nargs=1, required=True, help='Name of csv file of FWI output')
parser.add_argument('-o', '--output', nargs=1, required=True, help='Name of output file of FWI output (PDF or PNG)')
parser.add_argument('--name', nargs=1, help='Name of the station')
parser.add_argument('-m', '--mode', nargs=1, help='Plot type: 1=hourly FWI, 2=max daily FWI, 3=rolling stats (specify period)')
parser.add_argument('--period', nargs=5, help='Period for rolling statistics <starting month> <starting day> <ending month> <ending day> <number of days in rolling average>')

args = parser.parse_args()

inputfile = None
outputfile = None
outputfile_format = None
station_name = ''
plot_mode = 1

HOURLY_FWI = 1
MAX_DAILY_FWI = 2
ROLLING_STATS = 3

for k,v in vars(args).items():
    #print (k,v)
    if (k == 'input'):
        if (not os.path.isfile(v[0])):
            print("Specified file {} does not exist, exiting...".format(v[0]))
            exit(1)
        else:
            inputfile = v[0]
    if (k == 'output'):
        outputfile = v[0]
        outputfile_format = outputfile.split('.')[-1].lower()
        if (outputfile_format != 'png' and outputfile_format != 'pdf'):
            print("Output file format {} not recognized, exiting...".format(outputfile_format))
            exit(2)
    if (k == 'name'):
        if (v is not None):
            station_name = v[0]
    if (k == 'mode'):
        if (v is not None):
            plot_mode = v[0]
            if (plot_mode > 3 or plot_mode < 1):
                print("Invalid plotting mode {}".format(plot_mode))
                exit(3)

class fwi_data:
    def __init__(self, csvfile, station_name):
        self.name = station_name
        self.df = pd.read_csv(csvfile)
        self.id = self.df['id'].iloc[0]
        self.df.rename(columns={'yr': 'year', 'mon': 'month', 'hr': 'hour'}, inplace=True)
        self.df['full_date'] = pd.to_datetime(self.df[['year', 'month', 'day', 'hour']])

    def plot1(self, outputfile):
        do_plot_setup(self.id, self.name)
        plt.plot(self.df['full_date'], self.df['fwi'])
        plt.gca().set_ylim(bottom=0)
        plt.savefig(outputfile)

def do_plot_setup(station_id, station_name):
    fig = plt.figure(figsize=(20, 7))
    plt.title("{} {}".format(station_id, station_name), fontsize=20)
    plt.xlabel("Date", fontsize=15)
    fig.autofmt_xdate(rotation=45)
    plt.ylabel("Fire Weather Index", fontsize=15)


test = fwi_data(inputfile, station_name)
test.plot1(outputfile)
