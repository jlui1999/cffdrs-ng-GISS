from datetime import datetime
from timezonefinder import TimezoneFinder
from pytz import timezone
import pandas as pd
import numpy as np
import time

import sys, os
script_path = os.path.realpath(__file__)
source_dir = os.path.dirname(script_path)
sys.path.append("{}/../FWI/Python".format(source_dir))

from NG_FWI import hFWI

def get_timezone(lat, lon):
    assert lat < 90
    assert lat > -90
    if (lon > 360 or lon < -360):
        lon %= 360
    if (lon > 180):
        lon -= 360

    tf = TimezoneFinder()
    tz_loc = tf.timezone_at(lat=lat, lng=lon)
    utc = timezone(tz_loc).localize(datetime(2007, 1, 1)).strftime('%z')
    utc_int = int(utc[:3])
    return utc_int

# for a specified sorted array and target value, function finds the nearest value from the target array and returns the index of the closest value
# qualifer = None, nearest value
# qualifer = smaller, first value smaller than target value
# qualifer = larger, first value larger than target value
# originally a simple function, but meant for lat/lon so stuff like upside down latitude or longitudes that go from 0-360 also need to be accounted for
def find_nearest_sorted_latlon(array, value, qualifier=None):
    # reverse sorted
    if (array[0] > array[-1]):
        reverse = True
        array = array[::-1]
    else:
        reverse = False

    if (all(a >= 0 for a in array) and value < 0):
        lon360 = True
        value += 360
    else:
        lon360 = False
    # Find where the value would be inserted
    idx = np.searchsorted(array, value, side="left")

    # Boundary checks
    if (idx == 0):
        if (reverse):
            return len(array) - 1
        else:
            return idx
    if (idx == len(array) - 1):
        if (reverse):
            return idx
        else:
            return 0

    # Compare left and right neighbors to find the truly closest
    left = array[idx-1]
    right = array[idx]
    if qualifier is None:
        if abs(value - left) < abs(value - right):
            ret = idx-1
        else:
            ret = idx
    elif qualifier == 'larger':
        ret = idx
    elif qualifier == 'smaller':
        ret = idx-1

    if (reverse):
        ret = len(array) - ret - 1
    if (lon360):
        ret -= len(array)
    return ret

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
                try:
                    ffmc = float(headerarr[1])
                    dmc = float(headerarr[2])
                    dc = float(headerarr[3])
                    initializeCodes = True
                except:
                    print("Listed starting codes from {} do not seem to be all numbers".format(datafile))

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
