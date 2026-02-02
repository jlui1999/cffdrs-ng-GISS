# make FWI output plots

import pandas as pd
import numpy as np
import argparse, os
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from datetime import datetime, timedelta
import calendar

parser = argparse.ArgumentParser()

parser.add_argument('-i', '--input', nargs=1, required=True, help='Name of csv file of FWI output')
parser.add_argument('-o', '--output', nargs=1, required=True, help='Name of output file of FWI output (PDF or PNG)')
parser.add_argument('--name', nargs=1, help='Name of the station')
parser.add_argument('-m', '--mode', nargs=1, help='Plot type: default (hourly and maximum daily FWI), hourly (hourly FWI), maxdaily (maximum daily FWI), rolling (daily rolling period, specify period in days)')
parser.add_argument('-p', '--period', nargs=1, help='Period for rolling statistics, number of days in rolling average')
parser.add_argument('--from', nargs=3, help='Date from where plot starts, separated by spaces YYYY MM DD')
parser.add_argument('--to', nargs=3, help='Date to where plot ends, separated by spaces YYYY MM DD')
parser.add_argument('--season', nargs=1, help='Automatically sets date boundary of the plot to be the last specified season in data range; using DJF, MAM, JJA, SON will give seasons Dec 1-Feb 28/29, Mar 1-May 31, etc.; using winter, spring, summer, fall/autumn will give seasons using Mar 20, Jun 21, Sep 22, and Dec 21 as the boundaries.')
parser.add_argument('--all', action='store_true', help='Plot the entire date range (option ignored if either --from or --to are also given, not applicable to rolling plot)')
parser.add_argument('--dump-to-csv', action='store_true', help='Dumps percentile data from rolling plot to csv file, does not apply to other plot types')

args = parser.parse_args()

inputfile = None
outputfile = None
outputfile_format = None
startdate = None
enddate = None
period = None
season = None
plot_all = False
dump_csv = False
station_name = ''
plot_mode = 'default'

HOURLY_FWI = 'hourly'
MAX_DAILY_FWI = 'maxdaily'
ROLLING_STATS = 'rolling'
DEFAULT = 'default'

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
            if (plot_mode != HOURLY_FWI and plot_mode != MAX_DAILY_FWI and plot_mode != ROLLING_STATS and plot_mode != DEFAULT):
                print("Invalid plotting mode {}".format(plot_mode))
                exit(3)
    if (k == 'period'):
        if (v is not None):
            period = int(v[0])
    if (k == 'from'):
        if (v is not None):
            time = [ int(i) for i in v ]
            startdate = datetime(*time)
    if (k == 'to'):
        if (v is not None):
            time = [ int(i) for i in v ]
            enddate = datetime(*time, hour=23)
    if (k == 'all'):
        plot_all = v
    if (k == 'season'):
        if (v is not None):
            season = v[0].upper()
            if (season != 'DJF' and season != 'MAM' and season != 'JJA' and season != 'SON' and season != 'WINTER' and season != 'SPRING' and season != 'SUMMER' and season != 'AUTUMN' and season != 'FALL'):
                print("Invalid season {}".format(v[0]))
                exit(3)
    if (k == 'dump_to_csv'):
        dump_csv = v

if (plot_mode == ROLLING_STATS and period is None):
    print("Must specify period and starting and end dates for rolling statistics. --from <YYYY> <MM> <DD> --to <YYYY> <MM> <DD> --period <days>")
    exit(4)

class fwi_data:
    def __init__(self, csvfile, station_name):
        self.name = station_name
        self.df = pd.read_csv(csvfile)
        self.id = self.df['id'].iloc[0]
        self.df.rename(columns={'yr': 'year', 'mon': 'month', 'hr': 'hour'}, inplace=True)
        self.df['full_date'] = pd.to_datetime(self.df[['year', 'month', 'day', 'hour']])
        self.startyear = self.df['year'].iloc[0]
        self.endyear = self.df['year'].iloc[-1]

    def plothourly(self, outputfile, startdate, enddate):
        if (startdate is None and enddate is None):
            if (plot_all):
                startdate = self.df.iloc[0]["full_date"]
                enddate = self.df.iloc[-1]["full_date"]
            elif (season is not None):
                startdate, enddate = self.findLastSeason(season)
            else:
                startdate, enddate = self.findFireSeason()
        elif (startdate is None):
            startdate = self.df.iloc[0]["full_date"]
        elif (enddate is None):
            enddate = self.df.iloc[-1]["full_date"]
        do_plot_setup(self.id, self.name, extra=' (Hourly')
        filtered_rows = self.df[(self.df['full_date'] >= startdate) & (self.df['full_date'] <= enddate)]
        plt.plot(filtered_rows['full_date'], filtered_rows['fwi'], color='blue', linewidth=0.5)
        plt.gca().set_ylim(bottom=0)
        plt.savefig(outputfile)

    def plotmaxdaily(self, outputfile, startdate, enddate, plothourly=False):
        if (startdate is None and enddate is None):
            if (plot_all):
                startdate = self.df.iloc[0]["full_date"]
                enddate = self.df.iloc[-1]["full_date"]
            elif (season is not None):
                startdate, enddate = self.findLastSeason(season)
            else:
                startdate, enddate = self.findFireSeason()
        elif (startdate is None):
            startdate = self.df.iloc[0]["full_date"]
        elif (enddate is None):
            enddate = self.df.iloc[-1]["full_date"]
        do_plot_setup(self.id, self.name, extra=' (Max Daily)')
        maxdates, maxfwis = self.getmaxdailyfwi(startdate, enddate)
        if (plothourly):
            # need a dummy last day to get the step plot to look better
            maxdates.append(maxdates[-1] + timedelta(days=1))
            maxfwis.append(maxfwis[-1])
            plt.step(maxdates, maxfwis, where='post', color='red', linewidth=2, label='Max Daily FWI')
            filtered_rows = self.df[(self.df['full_date'] >= startdate) & (self.df['full_date'] <= enddate)]
            plt.plot(filtered_rows['full_date'], filtered_rows['fwi'], color='blue', linewidth=0.5, label='Hourly FWI')
            plt.legend(fontsize=20, framealpha=0.5)
        else:
            plt.plot(maxdates, maxfwis, color='red', linewidth=2)
        plt.gca().set_ylim(bottom=0)
        plt.savefig(outputfile)

    def plotrolling(self, outputfile, startdate, enddate, period, hourly=False, dump_csv=False):
        if (season is not None):
            startdate, enddate = self.findLastSeason(season)
        elif (period is None or startdate is None or enddate is None):
            startdate, enddate = self.findFireSeason()
        do_plot_setup(self.id, self.name, extra=" (Rolling Period {} Days)".format(period), subtitle="Climate reference period {} to {}".format(self.startyear, self.endyear))
        dates, p5, p25, p50, p75, p95, avgfwis = self.getrollingfwi(startdate, enddate, period, hourly=hourly)
        plt.fill_between(dates, p5, p95, color='0.95', label='95%')
        plt.fill_between(dates, p25, p75, color='0.85', label='IQR')
        plt.plot(dates, p50, color='black', label='mean')
        plt.plot(dates, avgfwis, color='red', linewidth=2, label='Daily Average FWI')
        plt.gca().set_ylim(bottom=0)
        plt.legend(fontsize=20, framealpha=0.5)
        plt.savefig(outputfile)

        if (dump_csv):
            csvdata = list(zip(dates, p5, p25, p50, p75, p95, avgfwis))
            with open(outputfile + '.csv', 'w') as outcsv:
                outcsv.write("date,5th percentile,25th,50th,75th,95th,fwi\n")
                for line in csvdata:
                    outcsv.write("{},{},{},{},{},{},{}\n".format(line[0].strftime("%Y%m%d%H"), *line[1:]))

    def getmaxdailyfwi(self, startdate, enddate):
        maxfwis = []
        dates = []
        if (startdate is None):
            startdate = self.df.iloc[0]["full_date"]
        if (enddate is None):
            enddate = self.df.iloc[-1]["full_date"]

        datefwi = startdate
        while (datefwi <= enddate):
            filtered_rows = self.df[(self.df['year'] == datefwi.year) & (self.df['month'] == datefwi.month) & (self.df['day'] == datefwi.day)]
            if (len(filtered_rows) == 0):
                maxfwi = np.nan
            else:
                maxfwi = max(filtered_rows['fwi'])

            maxfwis.append(maxfwi)
            dates.append(datefwi)

            datefwi += timedelta(days=1)

        return dates, maxfwis

    # returns the latest dates for specified season in the data range
    def findLastSeason(self, season):
        seasonDict = {
                'DJF' : [[12, 1], [2, 29]],
                'MAM' : [[3, 1], [5, 31]],
                'JJA' : [[6, 1], [8, 31]],
                'SON' : [[9, 1], [11, 30]],
                'WINTER' : [[12, 21], [3, 19]],
                'SPRING' : [[3, 20], [6, 20]],
                'SUMMER' : [[6, 21], [9, 21]],
                'AUTUMN' : [[9, 22], [12, 20]],
                'FALL' : [[9, 22], [12, 20]]
                }

        endyear = self.endyear
        enddate = datetime(endyear, *seasonDict[season][1], hour=23)
        if (self.df.iloc[-1]['full_date'] < enddate):
            endyear -= 1
            enddate = datetime(endyear, *seasonDict[season][1], hour=23)
        if (season == 'DJF' or season == 'WINTER'):
            startdate = datetime(endyear - 1, *seasonDict[season][0])
        else:
            startdate = datetime(endyear, *seasonDict[season][0])
        if (self.df.iloc[0]['full_date'] > startdate):
            print("Not enough data for a full specified season")
            exit(5)

        return startdate, enddate

    # returns the four months of the calculated fire season (max of rolling 4 month average) and return those four months of the specified year if it exists in the dataset
    # if no year is specifed, return the latest year with those months (including incomplete months)
    def findFireSeason(self, year=0):
        data_enddate = self.df.iloc[-1]["full_date"]
        avg_fwis = np.zeros(12)
        avg_fwis_4m = np.zeros(12)
        
        for i in range(12):
            filtered_rows = self.df[(self.df['month'] == i+1)]
            if (len(filtered_rows) == 0):
                continue
            avg_fwis[i] = np.average(filtered_rows['fwi'])
        #print (avg_fwis)

        for j in range(12):
            avg_fwis_4m[j] = np.average(avg_fwis[0:4])
            avg_fwis = np.roll(avg_fwis, -1)
        #print (avg_fwis_4m)

        fireseason_startmonth = np.argmax(avg_fwis_4m) + 1
        fireseason_endmonth = (fireseason_startmonth + 2) % 12 + 1

        if (year !=0):
            fireseason_startyear = year
            fireseason_endyear = year if (fireseason_endmonth > fireseason_startmonth) else year+1
        else:
            lendata = len(self.df[(self.df['year'] == data_enddate.year) & (self.df['month'] == fireseason_endmonth)])
            if (lendata > 0):
                fireseason_endyear = data_enddate.year
                fireseason_startyear = fireseason_endyear if (fireseason_endmonth > fireseason_startmonth) else fireseason_endyear-1
            else:
                # if no data in the end of the fire season in the last year of the data, try the previous year
                lendata2 = len(self.df[(self.df['year'] == data_enddate.year - 1) & (self.df['month'] == fireseason_endmonth)])
                if (lendata2 > 0):
                    fireseason_endyear = data_enddate.year - 1
                    fireseason_startyear = fireseason_endyear if (fireseason_endmonth > fireseason_startmonth) else fireseason_endyear-1
                else:
                    raise LookupError("No fire season found. Is there enough data?")
        startdate = datetime(fireseason_startyear, fireseason_startmonth, 1)
        enddate = datetime(fireseason_endyear, fireseason_endmonth, calendar.monthrange(fireseason_endyear, fireseason_endmonth)[1], hour=23)

        return startdate, enddate

    # returns rolling FWI of all previous FWI periods in percentiles 5, 25, 50, 75, 95, along with the average FWI for the latest period
    def getrollingfwi(self, startdate, enddate, period, hourly=False):
        if (period is None):
            print("Invalid specification.")
            exit(4)
        if (season is not None):
            startdate, enddate = self.findLastSeason(season)
        elif (startdate is None or enddate is None):
            startdate, enddate = self.findFireSeason()
        period_startmon = startdate.month
        period_startday = startdate.day
        period_endmon = enddate.month
        period_endday = enddate.day
        period_length = period

        # create a new dataframe with dummy year to better select rolling period
        df_temp = self.df[['full_date', 'fwi']].copy()
        df_temp['monthday'] = list(zip(df_temp['full_date'].dt.month, df_temp['full_date'].dt.day))

        averagefwi = []
        percentile95 = []
        percentile75 = []
        percentile50 = []
        percentile25 = []
        percentile5 = []

        dates = []

        datefwi = startdate
        
        rollingdateend = datetime(2000, period_startmon, period_startday)
        rollingdatestart = rollingdateend - timedelta(days=period_length)

        while (datefwi <= enddate):
            rollingdatestart_tuple = (rollingdatestart.month, rollingdatestart.day)
            rollingdateend_tuple = (rollingdateend.month, rollingdateend.day)

            if (rollingdatestart_tuple <= rollingdateend_tuple):
                filtered_rows = df_temp[(df_temp['monthday'] >= rollingdatestart_tuple) & (df_temp['monthday'] <= rollingdateend_tuple)]
            else: # crosses year boundary
                filtered_rows = df_temp[(df_temp['monthday'] >= rollingdatestart_tuple) | (df_temp['monthday'] <= rollingdateend_tuple)]
                
            filtered_rows_fwi = df_temp[(self.df['year'] == datefwi.year) & (self.df['month'] == datefwi.month) & (self.df['day'] == datefwi.day)]

            dates.append(datefwi)

            if (len(filtered_rows_fwi) == 0):
                averagefwi.append(np.nan)
            else:
                averagefwi.append(np.average(filtered_rows_fwi['fwi']))
            percentile95.append(np.percentile(filtered_rows['fwi'], 95))
            percentile75.append(np.percentile(filtered_rows['fwi'], 75))
            percentile50.append(np.percentile(filtered_rows['fwi'], 50))
            percentile25.append(np.percentile(filtered_rows['fwi'], 25))
            percentile5.append(np.percentile(filtered_rows['fwi'], 5))

            datefwi += timedelta(days=1)
            rollingdateend += timedelta(days=1)
            rollingdatestart += timedelta(days=1)

        return dates, percentile5, percentile25, percentile50, percentile75, percentile95, averagefwi


def do_plot_setup(station_id, station_name, extra='', subtitle=''):
    fig = plt.figure(figsize=(20, 10))
    plt.suptitle("{} {} FWI{}".format(station_id, station_name, extra), fontsize=30)
    plt.title(subtitle, fontsize=20)
    plt.xlabel("Date", fontsize=20)
    fig.autofmt_xdate(rotation=45)
    plt.ylabel("Fire Weather Index{}".format(extra), fontsize=20)
    plt.yticks(fontsize=15)
    plt.xticks(fontsize=15)
    plt.gca().xaxis.set_major_formatter(mdates.DateFormatter('%Y %b %d'))

fwidataobj = fwi_data(inputfile, station_name)

if (plot_mode == DEFAULT):
    fwidataobj.plotmaxdaily(outputfile, startdate, enddate, plothourly=True)
elif (plot_mode == HOURLY_FWI):
    fwidataobj.plothourly(outputfile, startdate, enddate)
elif (plot_mode == MAX_DAILY_FWI):
    fwidataobj.plotmaxdaily(outputfile, startdate, enddate)
elif (plot_mode == ROLLING_STATS):
    fwidataobj.plotrolling(outputfile, startdate, enddate, period, dump_csv=dump_csv)
else:
    print("Invalid mode {}".format(plot_mode))
    exit(7)
