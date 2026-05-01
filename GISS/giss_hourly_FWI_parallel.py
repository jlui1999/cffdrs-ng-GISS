# multiprocessor-enabled version of giss_hourly_FWI.py

from multiprocessing import Pool

import os, subprocess

from giss_config import *
from giss_utils import fwi_calc

subprocess.call(["mkdir",
                "-p",
                "{}/{}/{}".format(projectDir, regionName, fwiFolder)
                 ])

init_from_args = False
if (init_ffmc is not None and init_dmc is not None and init_dc is not None):
    try:
        init_ffmc = float(init_ffmc)
        init_dmc = float(init_dmc)
        init_dc = float(init_dc)
        init_from_args = True
    except:
        print("Listed starting codes from config file do not seem to be all numbers")

if __name__ == '__main__':
    counter = 0
    fwi_args = []
    inputfile = "{}/{}/{}".format(projectDir, regionName, pointLocations)
    with open(inputfile, mode='r') as ifile:
        for line in ifile:
            counter += 1
            if (line[0] == '#'):
                continue
            iline = line.strip().split('#')[0].split(',')
            station_id = iline[0]
            indata = "{}/{}/{}/{}_{}.csv".format(projectDir, regionName, convertedFolder, convertedPrefix, station_id)
            if (not os.path.isfile(indata)):
                print("Line {}: {} does not exist or is an invalid file, skipping...".format(counter, indata))
            else:
                fwi_out = "{}/{}/{}/{}_{}.csv".format(projectDir, regionName, fwiFolder, fwiPrefix, station_id)
                if len(iline) == 3:
                    if (init_from_args):
                        fwi_args.append((indata, fwi_out, init_ffmc, init_dmc, init_dc))
                    else:
                        fwi_args.append((indata, fwi_out, None, None, None))
                elif len(iline) == 6:
                    try:
                        fwi_args.append((indata, fwi_out, float(iline[2]), float(iline[3]), float(iline[4])))
                    except:
                        print("Line {}: Listed starting codes do not seem to be all numbers, skipping...".format(counter))
                else:
                    print("Line {}: Invalid number of arguments, skipping...".format(counter))

    if (do_multiprocess):
        pool = Pool()
        pool.starmap(fwi_calc, fwi_args)
        pool.close()
        pool.join()
    else:
        for fargs in fwi_args:
            fwi_calc(*fargs)
