# multiprocessor-enabled version of giss_hourly_FWI.py

import pandas as pd
from multiprocessing import Pool
import time

import sys, os
script_path = os.path.realpath(__file__)
source_dir = os.path.dirname(script_path)
sys.path.append("{}/../FWI/Python".format(source_dir))

from NG_FWI import hFWI
from daily_summaries import generate_daily_summaries

if (len(sys.argv) < 2):
    print("Usage: python giss_hourly_FWI_multi.py <txt file>")
    print("Text file contains, per line, separated by commas: <weather data>,<output file>,[ffmc],[dmc],[dc]")
    exit(1)

inputdatafile = sys.argv[1]
if (not os.path.isfile(inputdatafile)):
    print("Specified file {} does not exist, exiting...".format(txtdatafile))
    exit(2)

if (inputdatafile.split('.')[-1].lower() != 'csv' and inputdatafile.split('.')[-1].lower() != 'txt'):
    print("Input file must be a .txt or .csv file")
    exit(3)

def fwi_calc(datafile, outputfile, ffmc=None, dmc=None, dc=None):
    start_time = time.perf_counter()
    if (ffmc is None and dmc is None and dc is None):
        initializeCodes = False
    else:
        initializeCodes = True
    # FWI starting codes from .txt file will override starting codes read from .csv file
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

    data = pd.read_csv(datafile, comment='#')
    try:
        if (initializeCodes):
            print("Starting FWI run {} with starting codes FFMC={}, DMC={}, DC={}".format(datafile, ffmc, dmc, dc))
            data_fwi = hFWI(data, ffmc_old=ffmc, dmc_old=dmc, dc_old=dc, silent=True)
        else:
            data_fwi = hFWI(data, silent=True)
    except Exception as e:
        print("FWI conversion {} failed, {}".format(datafile, repr(e)))
        return

    data_fwi.to_csv(outputfile, index = False)
    end_time = time.perf_counter()
    print("FWI from {} calculated, outputted to {}, time taken {:6f}s".format(datafile, outputfile, end_time - start_time))

if __name__ == '__main__':
    counter = 0
    fwi_args = []
    with open(inputdatafile, mode='r') as ifile:
        for line in ifile:
            counter += 1
            if (line[0] == '#'):
                continue
            iofiles = line.strip().split(',')
            if (iofiles[0].split('.')[-1].lower() != 'csv' or not os.path.isfile(iofiles[0])):
                print("Line {}: {} does not exist or is an invalid file, skipping...".format(counter, iofiles[0]))
            else:
                if len(iofiles) == 1:
                    print("Line {}: No output file specified, skipping...".format(counter))
                elif len(iofiles) == 2:
                    fwi_args.append((iofiles[0], iofiles[1], None, None, None))
                elif len(iofiles) == 5:
                    try:
                        fwi_args.append((iofiles[0], iofiles[1], float(iofiles[2]), float(iofiles[3]), float(iofiles[4])))
                    except:
                        print("Line {}: Listed starting codes do not seem to be all numbers, skipping...".format(counter))
                else:
                    print("Line {}: Invalid number of arguments, skipping...".format(counter))

    pool = Pool()
    pool.starmap(fwi_calc, fwi_args)
    pool.close()
    pool.join()
