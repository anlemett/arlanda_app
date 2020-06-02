import numpy as np
import pandas as pd

import fuel
import geopy.distance

from shapely.geometry import Point
from shapely.geometry.polygon import Polygon

from constants import *
import plot

import time


def get_all_tracks(csv_input_file):

    df = pd.read_csv(csv_input_file, sep=' ',
                     names=['flightId', 'sequence', 'segmentId', 'origin', 'destination', 'aircraftType', 'beginTime', 'endTime',
                           'beginAltitude', 'endAltitude', 'status', 'callsign', 'beginDate', 'endDate', 'beginLat', 'beginLon',
                           'endLat', 'endLon', 'segmentLength', 'segmentParityColor', 'beginTimestamp', 'endTimestamp'],
                     index_col=[0,1],
                     dtype={'flightId':int, 'sequence':int, 'beginTime':int, 'endTime':int, 'beginDate':str, 'endDate':str})
    return df


def get_tracks_by_callsign(tracks_df, callsign):

    df = tracks_df

    print(len(df.groupby(level='flightId')))
    if callsign:
        df = df[(df['callsign'] == callsign)]

    print(len(df.groupby(level='flightId')))
    return df


def get_tracks_by_date(tracks_df, date_begin_str, date_end_str):
    
    df = tracks_df.copy()
    
    print(len(df.groupby(level='flightId')))
    
    df = df[(df['endDate'] >= date_begin_str) & (df['endDate'] <= date_end_str)]
    
    print(len(df.groupby(level='flightId')))
    return df


def get_tracks_by_time(tracks_df, timestamp_begin, timestamp_end):

    #time_start = time.time()
    
    df = tracks_df.copy()
    
    print(len(df.groupby(level='flightId')))

    for flight_id, flight_id_group in df.groupby(level='flightId'):

        if (df.loc[flight_id].tail(1)['endTimestamp'].item() < timestamp_begin) | (df.loc[flight_id].tail(1)['endTimestamp'].item() > timestamp_end):
            df = df.drop(flight_id, level='flightId')

    print(len(df.groupby(level='flightId')))
    
    #print((time.time()-time_start)/60)
    return df


def get_domestic_tracks(tracks_df):

    df = tracks_df[tracks_df['origin'].str.startswith("ES")]
    return df


def get_international_tracks(tracks_df):

    df = tracks_df[~tracks_df['origin'].str.startswith("ES")]
    return df


def get_stat(csv_input_file):
    df = pd.read_csv(csv_input_file, sep=' ',
                     names = ['endDate', 'number_of_flights', 'arrival_delayed_15_min_flights_number', 'enroute_delayed_15_min_flights_number',
                              'total_departure_delay', 'average_departure_delay', 'total_arrival_delay', 'average_arrival_delay',
                              'total_enroute_delay', 'average_enroute_delay', 'total_add_time_TMA', 'average_add_time'],
                     index_col=[0],
                     dtype={'flightId':int, 'endDate':str, 'endTime':str, 'departure_delay':int, 'arrival_delay':int, 'add_time':int})

    return df


def calculate_fuel_inside_TMA(tracks_df, fuel_csv_filename, fuel_png_filename, vfe_csv_filename):
    fuel_consumption_df = pd.DataFrame()
    timestamps_df = pd.DataFrame()
    vfe_df = pd.DataFrame(columns=['date', 'number_of_levels', 'time_on_levels', 'kpi19_2'])

    for flight_id, new_df in tracks_df.groupby(level='flightId'):

        fuel_sum = 0
        t_sum = 0
        aircraft_type = new_df.ix[(flight_id, 1)]['aircraftType']
        fuel_consumption_lst = [0]
        timestamps_lst = [0]

        entry_point_index = get_entry_point_index(flight_id, new_df)

        print("entry_point_index")
        print(entry_point_index)

        number_of_levels = 0
        time_on_levels = 0

        v = []

        for seq, row in new_df.groupby(level='sequence'):
            coords_1 = (row.ix[(flight_id, seq)]['beginLat'], row.ix[(flight_id, seq)]['beginLon'])
            coords_2 = (row.ix[(flight_id, seq)]['endLat'], row.ix[(flight_id, seq)]['endLon'])
            #s = geopy.distance.geodesic(coords_1, coords_2).m
            s = row.ix[(flight_id, seq)]['segmentLength'] * 1852   #nautical miles to meters

            t = row.ix[(flight_id, seq)]['endTimestamp'] - row.ix[(flight_id, seq)]['beginTimestamp']
            v.append(s/t)

        v_df = pd.DataFrame()
        v_df['speed'] = v
        v2_df = v_df.rolling(10).median().fillna(method='bfill').fillna(method='ffill')

        descent = 'true'
        for seq, row in new_df.groupby(level='sequence'):
            if seq < entry_point_index:
                continue

            h = row.ix[(flight_id, seq)]['beginAltitude']

            t = row.ix[(flight_id, seq)]['endTimestamp'] - row.ix[(flight_id, seq)]['beginTimestamp']
            t_sum = t_sum + t
            timestamps_lst.append(t_sum)

            if row.ix[(flight_id, seq)]['endAltitude'] < row.ix[(flight_id, seq)]['beginAltitude']:
                descent = 'true'
            else:
                if descent == 'true':
                    number_of_levels = number_of_levels + 1
                descent = 'false'
                time_on_levels = time_on_levels + t

            v = v2_df.iloc[seq-1]['speed']
            fuel_consumption = fuel.calculate_fuel(aircraft_type, h, v, descent)
            #print("fuel_consumption [kg/s]")
            #print(fuel_consumption)
            #print("time [s]")
            #print(t)
            fuel_sum += fuel_consumption*t
            fuel_consumption_lst.append(round(fuel_sum,3))
        #print("Fuel consumption [kg]:")
        #print(round(fuel_sum,3))
        #print("Total time [s]:")
        #print(t_sum)
        #print("Number of levels:")
        #print(number_of_levels)
        #print("Time spent on levels [s]:")
        #print(time_on_levels)

        number_of_levels_str = str(number_of_levels)
        time_on_levels_str= str(time_on_levels)

        kpi19_2 = time_on_levels / t_sum *100
        kpi19_2_str = "{0:.1f}".format(kpi19_2)

        vfe_df = vfe_df.append({'date': row.ix[(flight_id, seq)]['endDate'], 'number_of_levels': number_of_levels_str, 'time_on_levels': time_on_levels_str, 'kpi19_2': kpi19_2_str}, ignore_index=True)

        fuel_consumption_col_df = pd.DataFrame()
        fuel_consumption_col_df[row.ix[(flight_id, seq)]['endDate']] = fuel_consumption_lst
        fuel_consumption_df = pd.concat([fuel_consumption_df, fuel_consumption_col_df], axis=1, sort=False)

        timestamps_col_df = pd.DataFrame()
        timestamps_col_df[row.ix[(flight_id, seq)]['endDate']] = timestamps_lst
        timestamps_df = pd.concat([timestamps_df, timestamps_col_df], axis=1, sort=False)

    fuel_consumption_df.to_csv(fuel_csv_filename, sep=' ', encoding='utf-8')
    plot.save_fuel_plot(fuel_png_filename, fuel_consumption_df, timestamps_df)
    vfe_df.to_csv(vfe_csv_filename, sep=' ', encoding='utf-8', float_format='%.6f', header=True, index=False)


def get_entry_point_index(flight_id, new_df):
    for seq, row in new_df.groupby(level='sequence'):

        segmentId = row.ix[(flight_id, seq)]['segmentId']

        if segmentId.startswith('HMR') or segmentId.startswith('NILUG') or segmentId.startswith('XILAN') or segmentId.startswith('ELTOK'):
            return seq

    for seq, row in new_df.groupby(level='sequence'):
        if (check_TMA_contains_point(Point(row.ix[(flight_id, seq)]['beginLon'], row.ix[(flight_id, seq)]['beginLat']))):
            return seq

    return 0


def check_TMA_contains_point(point):

    lons_lats_vect = np.column_stack((TMA_lon, TMA_lat)) # Reshape coordinates
    polygon = Polygon(lons_lats_vect) # create polygon

    return polygon.contains(point)  # check if polygon contains point
    #print(point.within(polygon)) # check if a point is in the polygon
