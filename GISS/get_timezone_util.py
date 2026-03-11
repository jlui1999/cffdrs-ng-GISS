from datetime import datetime
from timezonefinder import TimezoneFinder
from pytz import timezone

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
