import pandas as pd

from config import *

def get_metar_df(filename):
    metar_df = pd.read_csv(filename, sep=',', names=['date', 'time', 'metar'], dtype=str)
    return metar_df

def calculate_snow(metar_df):

    snow_df = pd.DataFrame(columns=['date', 'snow'])

    metar_df.set_index(['date'], inplace=True)

    for date, new_df in metar_df.groupby(level='date'):

        count = len(new_df[new_df['metar'].str.contains("SN")])

        #create df with date and snow count
        snow_df =snow_df.append({'date': date, 'snow': count}, ignore_index=True)

    filename = "snow_by_day_" + year + "_" + month + ".csv"
    #snow_df.to_csv(filename, sep=' ', encoding='utf-8')
    return snow_df

def get_grib_df(filename):
    grib_df = pd.read_csv(filename, sep=' ', names=['date', 'lat', 'lon', 'visibility', 'cape', 'gust'], dtype = {'date': str})
    return grib_df
