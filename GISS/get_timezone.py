from datetime import datetime
from timezonefinder import TimezoneFinder
from pytz import timezone
import argparse

parser = argparse.ArgumentParser()

parser.add_argument('-lat', '--latitude', nargs=1, required=True)
parser.add_argument('-lon', '-long', '--longitude', nargs=1, required=True)
#parser.add_argument('-dst')

args = parser.parse_args()

lat = 0
lon = 0

for k,v in vars(args).items():
    if (k == 'latitude'):
        lat = float(v[0])
        if (lat > 90 or lat < -90):
            print('latitude {} is invalid')
            exit()
    if (k == 'longitude'):
        lon = float(v[0])
        if (lon > 360 or lon < -360):
            lon = lon % 360
        if (lon > 180):
            lon = 360 - lon

tf = TimezoneFinder()
tz_loc = tf.timezone_at(lat=lat, lng=lon)
utc = timezone(tz_loc).localize(datetime(2007, 1, 1)).strftime('%z')
utc_int = int(utc[:3])
print(utc_int)
