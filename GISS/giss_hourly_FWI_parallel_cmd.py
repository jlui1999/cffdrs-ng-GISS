# multiprocessor-enabled version of giss_hourly_FWI.py

from multiprocessing import Pool

import sys, os

from giss_utils import fwi_calc

if (len(sys.argv) < 2):
    print("Usage: python giss_hourly_FWI_multi.py <txt file>")
    print("Text file contains, per line, separated by commas: <weather data>,<output file>,[ffmc],[dmc],[dc]")
    exit(1)

if (len(sys.argv) == 6):
    try:
        init_ffmc = float(sys.argv[3])
        init_dmc = float(sys.argv[4])
        init_dc = float(sys.argv[5])
        init_from_args = True
    except:
        print("Listed starting values do not all appear to be numbers")
        exit(1)

inputdatafile = sys.argv[1]
if (not os.path.isfile(inputdatafile)):
    print("Specified file {} does not exist, exiting...".format(txtdatafile))
    exit(2)

if (inputdatafile.split('.')[-1].lower() != 'csv' and inputdatafile.split('.')[-1].lower() != 'txt'):
    print("Input file must be a .txt or .csv file")
    exit(3)

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
                    if (init_from_args):
                        fwi_args.append((iofiles[0], iofiles[1], init_ffmc, init_dmc, init_dc))
                    else:
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
