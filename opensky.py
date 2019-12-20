import numpy as np
import pandas as pd

import fuel
import geopy.distance

from shapely.geometry import Point
from shapely.geometry.polygon import Polygon

from constants import *
import plot


def get_all_tracks(csv_input_file):

    df = pd.read_csv(csv_input_file, sep=' ',
                    names = ['flightId', 'sequence', 'beginDate', 'callsign', 'icao24', 'endDate', 'time', 'timestamp',
                             'lat', 'lon', 'baroAltitude', 'aircraftType', 'origin'],
                    index_col=[0,1],
                    dtype={'flightId':int, 'sequence':int, 'time':str, 'timestamp':int, 'beginDate':str, 'endDate':str})

    return df


def get_tracks_by_callsign(tracks_df, callsign):

    df = tracks_df

    if callsign:
        df = df[(df['callsign'] == callsign)]

    return df


def get_tracks_by_time(all_tracks_df, timestamp_begin, timestamp_end):

    df = all_tracks_df.copy()

    for flight_id, flight_id_group in df.groupby(level='flightId'):

        if (df.loc[flight_id].tail(1)['timestamp'].item() < timestamp_begin) | (df.loc[flight_id].tail(1)['timestamp'].item() > timestamp_end):
            df = df.drop(flight_id, level='flightId')


    return df


def get_domestic_tracks(tracks_df):

    df = tracks_df[tracks_df['origin'].str.startswith("ES")]
    return df


def get_international_tracks(tracks_df):

    df = tracks_df[~tracks_df['origin'].str.startswith("ES")]
    return df


def get_all_states(csv_input_file):

    df = pd.read_csv(csv_input_file, sep=' ', index_col=[0,1],
                    names = ['flightId', 'sequence', 'altitude', 'velocity', 'beginDate'],
                    dtype={'flightId':int, 'sequence':int, 'altitude':float, 'velocity':float, 'beginDate':str})
    
    return df


def get_states(tracks_df, all_states_df):

    states_df = pd.DataFrame(columns=['flightId', 'sequence', 'altitude', 'velocity', 'beginDate'])

    all_states_df.reset_index(level=all_states_df.index.names, inplace=True)

    flight_id_num = len(tracks_df.groupby(level='flightId'))
    count = 1
    for flight_id, flight_id_group in tracks_df.groupby(level='flightId'):
        
        print(flight_id)

        print(flight_id_num, count)
        count = count + 1
        flight_id_states_df = all_states_df[(all_states_df['flightId']==flight_id)]
        states_df = pd.concat([states_df, flight_id_states_df], axis=0, sort=False)

    all_states_df.set_index(['flightId', 'sequence'], inplace=True)
    states_df.set_index(['flightId', 'sequence'], inplace=True)

    return states_df


def get_stat(csv_input_file):
    df = pd.read_csv(csv_input_file, sep=' ',
                     names = ['date', 'number_of_flights', 'number_of_level_flights', 'total_number_of_levels', 'average_number_of_levels',
                            'total_time_on_levels', 'average_time_on_levels', 'total_distance_on_levels', 'average_distance_on_levels'],
                     index_col=[0],
                     dtype={'date':str})

    return df


def calculate_fuel_inside_TMA_states(tracks_opensky_df, states_opensky_df, fuel_csv_filename, fuel_png_filename, vfe_csv_filename):
    fuel_consumption_df = pd.DataFrame()
    timestamps_df = pd.DataFrame()
    vfe_df = pd.DataFrame(columns=['date', 'number_of_levels', 'time_on_levels', 'kpi19_2'])

    states_opensky_df.reset_index(level=states_opensky_df.index.names, inplace=True)

    for flight_id, new_df in tracks_opensky_df.groupby(level='flightId'):

        flight_id_states_df = states_opensky_df[['flight_id']==flight_id]

        new_altitude = flight_id_states_df.altitude.rolling(10).median().bfill().ffill()
        flight_id_states_df.drop(['altitude'], axis=1)
        flight_id_states_df['altitude'] = new_altitude

        new_velocity = flight_id_states_df.velocity.rolling(10).median().bfill().ffill()
        flight_id_states_df.drop(['velocity'], axis=1)
        flight_id_states_df['velocity'] = new_velocity

        flight_id_states_df.set_index(['sequence'], inplace=True)

        fuel_sum = 0
        t_sum = 0
        aircraft_type = new_df.ix[(flight_id, 1)]['aircraftType']
        fuel_consumption_lst = [0]
        timestamps_lst = [0]

        number_of_levels = 0
        time_on_levels = 0

        descent = 'true'
        altitude1 = 0
        for seq, row in flight_id_states_df.iterrows():
            if seq == 0:
                altitude1 = row['altitude']
                continue

            h = row['altitude']
            t_sum = t_sum + 1
            timestamps_lst.append(t_sum)

            if row['altitude'] < altitude1:
                descent = 'true'
            else:
                if descent == 'true':
                    number_of_levels = number_of_levels + 1
                descent = 'false'
                time_on_levels = time_on_levels + 1

            v = row['velocity']
            fuel_consumption = fuel.calculate_fuel(aircraft_type, h, v, descent)

            fuel_sum += fuel_consumption
            fuel_consumption_lst.append(round(fuel_sum,3))

        number_of_levels_str = str(number_of_levels)
        time_on_levels_str= str(time_on_levels)

        kpi19_2 = time_on_levels / t_sum *100
        kpi19_2_str = "{0:.1f}".format(kpi19_2)

        vfe_df = vfe_df.append({'date': new_df.ix[(flight_id, seq)]['date'], 'number_of_levels': number_of_levels_str, 'time_on_levels': time_on_levels_str, 'kpi19_2': kpi19_2_str}, ignore_index=True)

        fuel_consumption_col_df = pd.DataFrame()
        fuel_consumption_col_df[new_df.ix[(flight_id, seq)]['date']] = fuel_consumption_lst
        fuel_consumption_df = pd.concat([fuel_consumption_df, fuel_consumption_col_df], axis=1, sort=False)

        timestamps_col_df = pd.DataFrame()
        timestamps_col_df[new_df.ix[(flight_id, seq)]['date']] = timestamps_lst
        timestamps_df = pd.concat([timestamps_df, timestamps_col_df], axis=1, sort=False)

    fuel_consumption_df.to_csv(fuel_csv_filename, sep=' ', encoding='utf-8')
    plot.save_fuel_plot(fuel_png_filename, fuel_consumption_df, timestamps_df)
    vfe_df.to_csv(vfe_csv_filename, sep=' ', encoding='utf-8', float_format='%.6f', header=True, index=False)


def calculate_fuel_inside_TMA_tracks(tracks_opensky_df, fuel_csv_filename, fuel_png_filename, vfe_csv_filename):
    fuel_consumption_df = pd.DataFrame()
    timestamps_df = pd.DataFrame()
    vfe_df = pd.DataFrame(columns=['date', 'number_of_levels', 'time_on_levels', 'kpi19_2'])

    for flight_id, new_df in tracks_opensky_df.groupby(level='flightId'):
        fuel_sum = 0
        t_sum = 0
        aircraft_type = new_df.ix[(flight_id, 1)]['aircraftType']
        fuel_consumption_lst = [0]
        timestamps_lst = [0]

        entry_point_index = get_entry_point_index(flight_id, new_df)
        print("Entry point index:")
        print(entry_point_index)

        number_of_levels = 0
        time_on_levels = 0

        v = []

        for seq, row in new_df.groupby(level='sequence'):
            if seq == 0:
                continue
            coords_1 = (new_df.ix[(flight_id, seq-1)]['lat'], new_df.ix[(flight_id, seq-1)]['lon'])
            coords_2 = (new_df.ix[(flight_id, seq)]['lat'], new_df.ix[(flight_id, seq)]['lon'])

            s = geopy.distance.geodesic(coords_1, coords_2).m
            t = new_df.ix[(flight_id, seq)]['timestamp'] - new_df.ix[(flight_id, seq-1)]['timestamp']

            v.append(s/t)

        v_df = pd.DataFrame()
        v_df['speed'] = v
        v2_df = v_df.rolling(10).median().fillna(method='bfill').fillna(method='ffill')

        descent = 'true'
        for seq, row in new_df.groupby(level='sequence'):
            if seq == 0:
                continue
            if seq < entry_point_index:
                continue

            h = new_df.ix[(flight_id, seq)]['baroAltitude']

            t = new_df.ix[(flight_id, seq)]['timestamp'] - new_df.ix[(flight_id, seq-1)]['timestamp']

            t_sum = t_sum + t
            timestamps_lst.append(t_sum)

            if new_df.ix[(flight_id, seq)]['baroAltitude'] < new_df.ix[(flight_id, seq-1)]['baroAltitude']:
                descent = 'true'
            else:
                if descent == 'true':
                    number_of_levels = number_of_levels + 1
                descent = 'false'
                time_on_levels = time_on_levels + t

            v = v2_df.iloc[seq-entry_point_index]['speed']
            fuel_consumption = fuel.calculate_fuel(aircraft_type, h, v, descent)
            #print("fuel_consumption kg/s")
            #print(fuel_consumption)
            #print("time")
            #print(t)
            fuel_sum += fuel_consumption*t
            fuel_consumption_lst.append(round(fuel_sum,3))
            #fuel_sum_str = "{0:.3f}".format(fuel_sum)
            #fuel_consumption_lst.append(fuel_sum_str)
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

        vfe_df = vfe_df.append({'date': row.ix[(flight_id, seq)]['date'], 'number_of_levels': number_of_levels_str, 'time_on_levels': time_on_levels_str, 'kpi19_2': kpi19_2_str}, ignore_index=True)

        fuel_consumption_col_df = pd.DataFrame()
        fuel_consumption_col_df[row.ix[(flight_id, seq)]['date']] = fuel_consumption_lst
        fuel_consumption_df = pd.concat([fuel_consumption_df, fuel_consumption_col_df], axis=1, sort=False)

        timestamps_col_df = pd.DataFrame()
        timestamps_col_df[row.ix[(flight_id, seq)]['date']] = timestamps_lst
        timestamps_df = pd.concat([timestamps_df, timestamps_col_df], axis=1, sort=False)

    fuel_consumption_df.to_csv(fuel_csv_filename, sep=' ', encoding='utf-8')
    plot.save_fuel_plot(fuel_png_filename, fuel_consumption_df, timestamps_df)
    vfe_df.to_csv(vfe_csv_filename, sep=' ', encoding='utf-8', float_format='%.6f', header=True, index=False)


def get_entry_point_index(flight_id, new_df):
    for seq, row in new_df.groupby(level='sequence'):
        if (check_TMA_contains_point(Point(row.ix[(flight_id, seq)]['lon'], row.ix[(flight_id, seq)]['lat']))):
            return seq
    return 0


def check_TMA_contains_point(point):

    lons_lats_vect = np.column_stack((TMA_lon, TMA_lat)) # Reshape coordinates
    polygon = Polygon(lons_lats_vect) # create polygon

    return polygon.contains(point)  # check if polygon contains point
    #print(point.within(polygon)) # check if a point is in the polygon
