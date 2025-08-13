# make FWI output plots

import pandas as pd
import numpy as np
import argparse, os
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from datetime import datetime, timedelta

parser = argparse.ArgumentParser()

parser.add_argument('-i', '--input', nargs=1, required=True, help='Name of csv file of FWI output')
parser.add_argument('-o', '--output', nargs=1, required=True, help='Name of output file of FWI output (PDF or PNG)')
parser.add_argument('--name', nargs=1, help='Name of the station')
parser.add_argument('-m', '--mode', nargs=1, help='Plot type: hourly (hourly FWI), maxdaily (maximum daily FWI), rolling (daily rolling period, specify period in days)')
parser.add_argument('-p', '--period', nargs=1, help='Period for rolling statistics, number of days in rolling average')
parser.add_argument('--from', nargs=3, help='Date from where plot starts, separated by spaces YYYY MM DD')
parser.add_argument('--to', nargs=3, help='Date to where plot ends, separated by spaces YYYY MM DD')

args = parser.parse_args()

inputfile = None
outputfile = None
outputfile_format = None
startdate = None
enddate = None
period = None
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
            enddate = datetime(*time)


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

    def plothourly(self, outputfile, startdate, enddate):
        if (startdate is None):
            startdate = self.df.iloc[0]["full_date"]
        if (enddate is None):
            enddate = self.df.iloc[-1]["full_date"]
        do_plot_setup(self.id, self.name, extra=' (Hourly)')
        filtered_rows = self.df[(self.df['full_date'] >= startdate) & (self.df['full_date'] <= enddate)]
        plt.plot(filtered_rows['full_date'], filtered_rows['fwi'], color='red', linewidth=0.5)
        plt.gca().set_ylim(bottom=0)
        plt.savefig(outputfile)

    def plotmaxdaily(self, outputfile, startdate, enddate, plothourly=False):
        if (startdate is None):
            startdate = self.df.iloc[0]["full_date"]
        if (enddate is None):
            enddate = self.df.iloc[-1]["full_date"]
        do_plot_setup(self.id, self.name, extra=' (Max Daily)')
        maxdates, maxfwis = self.getmaxdailyfwi(startdate, enddate)
        if (plothourly):
            plt.step(maxdates, maxfwis, where='post', color='red', linewidth=2, label='Max Daily FWI')
            filtered_rows = self.df[(self.df['full_date'] >= startdate) & (self.df['full_date'] <= enddate)]
            plt.plot(filtered_rows['full_date'], filtered_rows['fwi'], color='red', linewidth=0.5, label='Hourly FWI')
            plt.legend(fontsize=20, framealpha=0.5)
        else:
            plt.plot(maxdates, maxfwis, color='red', linewidth=2)
        plt.gca().set_ylim(bottom=0)
        plt.savefig(outputfile)

    def plotrolling(self, outputfile, startdate, enddate, period):
        if (period is None or startdate is None or enddate is None):
            print("Invalid specification.")
            exit(4)
        do_plot_setup(self.id, self.name, extra=" (Rolling Period {} Days)".format(period))
        dates, p5, p25, p50, p75, p95, avgfwis = self.getrollingfwi(startdate, enddate, period)
        plt.fill_between(dates, p5, p95, color='0.95', label='95%')
        plt.fill_between(dates, p25, p75, color='0.85', label='IQR')
        plt.plot(dates, p50, color='black', label='mean')
        plt.plot(dates, avgfwis, color='red', linewidth=2, label='Daily Average FWI')
        plt.gca().set_ylim(bottom=0)
        plt.legend(fontsize=20, framealpha=0.5)
        plt.savefig(outputfile)

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

#       try:
#           idx = 0
#           while True:
#               datarow = self.df.iloc[idx]
#               year = datarow['year']
#               month = datarow['month']
#               day = datarow['day']
#               filtered_rows = self.df[(self.df['year'] == year) & (self.df['month'] == month) & (self.df['day'] == day)]
#               maxfwi = max(filtered_rows['fwi'])
#               datemaxfwi = datetime(year, month, day)

#               maxfwis.append(maxfwi)
#               dates.append(datemaxfwi)
#               idx += 24
#       except IndexError:
#           return dates, maxfwis

    # returns rolling FWI of all previous FWI periods in percentiles 5, 25, 50, 75, 95, along with the average FWI for the latest period
    def getrollingfwi(self, startdate, enddate, period):
        if (period is None or startdate is None or enddate is None):
            print("Invalid specification.")
            exit(4)
        period_startmon = startdate.month
        period_startday = startdate.day
        period_endmon = enddate.month
        period_endday = enddate.day
        period_length = period

#       # check if period is over new year
#       if (period_startmon > period_endmon):
#           newyear = True
#       else:
#           newyear = False

#       # check for period over new year in same month
#       if (period_startmon == period_endmon):
#           if (period_startday > period_endday):
#               newyear = True
#           else:
#               newyear = False

#       # check if period exists in last year(s) of data
#       lastyear = self.df['year'].iloc[-1]
#       if (len(self.df[(self.df['year'] == lastyear) & (self.df['month'] == period_endmon) & (self.df['day'] == period_endday)]) == 0):
#           print("Date {}-{}-{} does not seem to exist in data.".format(lastyear, period_endmon, period_endmon))
#           exit(6)
#       if (newyear):
#           if (len(self.df[(self.df['year'] == lastyear - 1) & (self.df['month'] == period_startmon) & (self.df['day'] == period_startday)]) == 0):
#               print("Date {}-{}-{} does not seem to exist in data.".format(lastyear-1, period_startmon, period_startmon))
#               exit(6)
#       else:
#           if (len(self.df[(self.df['year'] == lastyear) & (self.df['month'] == period_startmon) & (self.df['day'] == period_startday)]) == 0):
#               print("Date {}-{}-{} does not seem to exist in data.".format(lastyear, period_startmon, period_startmon))
#               exit(6)

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

#       if (newyear):
#           datefwi = datetime(lastyear-1, period_startmon, period_startday)
#       else:
#           datefwi = datetime(lastyear, period_startmon, period_startday)
#
#       enddate = datetime(lastyear, period_endmon, period_endday)
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


def do_plot_setup(station_id, station_name, extra=''):
    fig = plt.figure(figsize=(20, 10))
    plt.title("{} {} FWI{}".format(station_id, station_name, extra), fontsize=30)
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
    fwidataobj.plotrolling(outputfile, startdate, enddate, period)
else:
    print("Invalid mode {}".format(plot_mode))
    exit(7)
