import os

DEBUG = True
PORT = 8100
HOST = '127.0.0.1'

year = "2018"

BASE_DIR = os.path.abspath(os.path.dirname(__file__))

DOWNLOADS_DIR = os.path.join(BASE_DIR, 'downloads')

INPUT_DIR = os.path.join(BASE_DIR, os.path.join('data', 'input'))
OUTPUT_DIR = os.path.join(BASE_DIR, os.path.join('data', 'output'))
OUTPUT_PICTURES_DIR = os.path.join(BASE_DIR, os.path.join('static', 'pictures'))
STATIC_PICTURES_DIR = os.path.join('/', os.path.join('static', 'pictures'))

'''
TRACKS_TMA_DDR_M1_CSV = "tracks_TMA_ddr_m1_" + year + ".csv"
TRACKS_TMA_DDR_M3_CSV = "tracks_TMA_ddr_m3_" + year + ".csv"

TRACKS_TMA_OPENSKY_CSV = "tracks_TMA_opensky_" + year + ".csv"
STATES_TMA_OPENSKY = "states_TMA_opensky_" + year + "_"
'''

STAT_DDR_BY_DAY_CSV = "statistics_ddr_by_day_" + year + ".csv"
STAT_OPENSKY_BY_DAY_CSV = "statistics_opensky_by_day_" + year + ".csv"

METAR_CSV = "weather_metar_" + year + ".csv"
GRIB_CSV = "weather_grib_" + year + ".csv"

DDR_M1 = "ddr_m1"
DDR_M3 = "ddr_m3"
DDR = "ddr"
OPENSKY = "opensky"
DDR_M1_M3 = "ddr_m1_m3"
DDR_M1_OPENSKY = "ddr_m1_opensky"
DDR_M1_M3_OPENSKY = "ddr_m1_m3_opensky"
STAT = "stat"
FUEL = "fuel"
VFE = "vfe"
VP = "vertical_profile"
