import numpy as np
import pandas as pd
import statistics
from calendar import monthrange

from config import *

ddr_total_arrival_delays = 0
ddr_average_arrival_delay = 0
ddr_total_departure_delays = 0
ddr_average_departure_delay = 0
ddr_delayed_5_min_count = 0
ddr_delayed_15_min_count = 0

opensky_total_arrival_delays = 0
opensky_average_arrival_delay = 0
opensky_total_departure_delays = 0
opensky_average_departure_delay = 0
opensky_delayed_5_min_count = 0
opensky_delayed_15_min_count = 0

L_avg = 0
D_avg = 0
S_D = 0
T_avg = 0
S_T = 0
P = 0
kpi19_1 = 0
kpi19_2 = 0

#(first_day_weekday, number_of_days) = monthrange(int(year), int(month))
number_of_days = 31

def calculate_ddr_TMA_additional_time(TMA_track1_df, TMA_track2_df):
    TMA_ddr_m1_time_in_TMA_df = pd.DataFrame(columns=['flight_id', 'date', 'TMA_time'])
    TMA_ddr_m3_time_in_TMA_df = pd.DataFrame(columns=['flight_id', 'date', 'TMA_time'])

    # only 2 hours: from 11.00 to 13.00
    #TMA_track1_df = TMA_track1_df[(TMA_track1_df.endTime>=110000) & (TMA_track1_df.endTime<=130000)]


    for id, new_df in TMA_track1_df.groupby(level='flightId'):
        begin_timestamp = new_df['beginTimestamp'].values[0]
        end_timestamp = new_df['endTimestamp'].values[-1]
        time_TMA = end_timestamp - begin_timestamp
        date = new_df['beginDate'].values[0]
        #end_time = new_df['endTime'].values[-1]
        TMA_ddr_m1_time_in_TMA_df = TMA_ddr_m1_time_in_TMA_df.append({'flight_id': id, 'date': date, 'TMA_time': time_TMA}, ignore_index=True)

    for id, new_df in TMA_track2_df.groupby(level='flightId'):
        begin_time = new_df['beginTimestamp'].values[0].item(0)
        end_time = new_df['endTimestamp'].values[-1].item(0)
        time_TMA = end_time - begin_time
        date = new_df['beginDate'].values[0]
        TMA_ddr_m3_time_in_TMA_df = TMA_ddr_m3_time_in_TMA_df.append({'flight_id': id, 'date': date, 'TMA_time': time_TMA}, ignore_index=True)

    additional_time_df = pd.merge(TMA_ddr_m1_time_in_TMA_df, TMA_ddr_m3_time_in_TMA_df, on=['flight_id'], suffixes=["_L", "_R"])
    additional_time_df['add_time'] = additional_time_df['TMA_time_R'] - additional_time_df['TMA_time_L']
    additional_time_df['date'] = additional_time_df['date_L']
    additional_time_df = additional_time_df[['date', 'flight_id', 'add_time']]
    additional_time_df.reset_index(drop=True, inplace=True)
    
    
    additional_time_df.set_index(['date'], inplace=True)
    
    filename = "ddr_TMA_add_time_by_flight_" + year + "_" + month + ".csv"
    additional_time_df.to_csv(filename, sep=' ', encoding='utf-8', float_format='%.6f', header=None)


#    TMA_additional_time_by_day_df = pd.DataFrame(columns=['date', 'number_of_flights', 'total_add_time', 'average_add_time'])

#    for date, new_df in additional_time_df.groupby(level='date'):
        
#        number_of_flights = len(new_df)
        #print(date)
#        additional_time_day = np.array([])
#        additional_time_day = new_df.loc[new_df.add_time > 0, 'add_time']

#        total_additional_time_day = int(np.sum(additional_time_day))

 #       average_additional_time_day = int(total_additional_time_day/len(additional_time_day)) if additional_time_day.any() else 0

        #create df with date and total and average additional time
 #       TMA_additional_time_by_day_df = TMA_additional_time_by_day_df.append({'date': date, 'number_of_flights': number_of_flights, 
 #           'total_add_time': total_additional_time_day, 'average_add_time': average_additional_time_day}, ignore_index=True)


    # not all dates might be in ddr csv (as in aipril 2018), creating empty rows for missing dates
 #   (nrows, ncol) = TMA_additional_time_by_day_df.shape

 #   if nrows < number_of_days:
 #       date = "18" + month
 #       month_date_list = []
 #       for d in range(1,9):
 #           month_date_list.append(date + '0' + str(d))
 #       for d in range(10,number_of_days+1):
 #           month_date_list.append(date + str(d))
 #       df_dates_np = TMA_additional_time_by_day_df.iloc[:,0].values

 #       for d in month_date_list:
 #           if d not in df_dates_np:
 #               TMA_additional_time_by_day_df = TMA_additional_time_by_day_df.append({'date': d, 'number_of_flights': 0, 
 #                   'total_add_time': 0, 'average_add_time': 0
 #                   }, ignore_index=True)

 #       TMA_additional_time_by_day_df = TMA_additional_time_by_day_df.sort_values(by ='date' )

 #   TMA_additional_time_by_day_df.reset_index(drop=True, inplace=True)

    #filename = "ddr_TMA_add_time_by_day_2hours_" + year + "_" + month + ".csv"
#    filename = "ddr_TMA_add_time_by_day_" + year + "_" + month + ".csv"
#    TMA_additional_time_by_day_df.to_csv(filename, sep=' ', encoding='utf-8', float_format='%.6f', header=None)

#    return TMA_additional_time_by_day_df
    return additional_time_df


def calculate_ddr_delays(track1_df, track2_df):
    global ddr_total_arrival_delays, ddr_average_arrival_delay
    global ddr_total_departure_delays, ddr_average_departure_delay
    global ddr_delayed_5_min_count, ddr_delayed_15_min_count

    ddr_total_arrival_delays = 0
    ddr_average_arrival_delay = 0
    ddr_total_departure_delays = 0
    ddr_average_departure_delay = 0

    arrival_delays = np.array([])
    departure_delays = np.array([])

    arrival_delays_5_min = np.array([])
    arrival_delays_15_min = np.array([])

    ddr_m1_maxTimestamp_df = track1_df.groupby(level='flightId').tail(1)[['endDate', 'endTime', 'endTimestamp']]
    ddr_m3_maxTimestamp_df = track2_df.groupby(level='flightId').tail(1)[['endDate', 'endTimestamp']]

    arrival_delay_df = pd.merge(ddr_m1_maxTimestamp_df, ddr_m3_maxTimestamp_df, on=['flightId'], suffixes=["_L", "_R"])
    arrival_delay_df['delay'] = arrival_delay_df['endTimestamp_R'] - arrival_delay_df['endTimestamp_L']
    arrival_delay_df.set_index(['endDate_R'], inplace=True)

    # only 2 hours: from 11.00 to 13.00
    arrival_delay_2hours_df = arrival_delay_df[(arrival_delay_df.endTime>=110000) & (arrival_delay_df.endTime<=130000)]

    arrival_delays = arrival_delay_df.loc[arrival_delay_df.delay > 60, 'delay']
    arrival_delays_2hours = arrival_delay_2hours_df.loc[arrival_delay_2hours_df.delay > 60, 'delay']

    ddr_total_arrival_delays = int(np.sum(arrival_delays))
    ddr_average_arrival_delay = int(ddr_total_arrival_delays/len(arrival_delays)) if arrival_delays.any() else 0

    ddr_total_arrival_delays_2hours = int(np.sum(arrival_delays_2hours))
    ddr_average_arrival_delay_2hours = int(ddr_total_arrival_delays_2hours/len(arrival_delays_2hours)) if arrival_delays_2hours.any() else 0

    ddr_m1_minTimestamp_df = track1_df.groupby(level='flightId').head(1)[['beginTimestamp']]
    ddr_m3_minTimestamp_df = track2_df.groupby(level='flightId').head(1)[['beginTimestamp']]

    departure_delay_df = pd.merge(ddr_m1_minTimestamp_df, ddr_m3_minTimestamp_df, on=['flightId'], suffixes=["_L", "_R"])
    departure_delay_df['delay'] = departure_delay_df['beginTimestamp_R']- departure_delay_df['beginTimestamp_L']

    departure_delays = departure_delay_df.loc[departure_delay_df.delay > 60, 'delay']

    ddr_total_departure_delays = int(np.sum(departure_delays))
    ddr_average_departure_delay = int(ddr_total_departure_delays/len(departure_delays)) if departure_delays.any() else 0


    arrival_delays_5_min = arrival_delay_df.loc[arrival_delay_df.delay > 300, 'delay']
    arrival_delays_15_min = arrival_delay_df.loc[arrival_delay_df.delay > 900, 'delay']
    ddr_delayed_5_min_count = len(arrival_delays_5_min)
    ddr_delayed_15_min_count = len(arrival_delays_15_min)

    #Calculate percent of delayed flights by day

    filename = "ddr_delays_by_day_" + year + "_" + month + ".csv"

    #To calculate over the whole day uncomment the following 2 lines
    #arrival_delays = arrival_delays_2hours
    #filename = "ddr_delays_by_day_2hours_" + year + "_" + month + ".csv"


    arrival_delays_by_day_df = pd.DataFrame(columns=['date', 'number_of_flights', 'total_delay', 'average_delay', 'percent_delayed'])

    for date, new_df in arrival_delay_df.groupby(level='endDate_R'):
        number_of_flights = len(new_df)
        
        arrival_delays_day = np.array([])
        date_number_of_flights = len(new_df)
        arrival_delays_day = new_df.loc[new_df.delay > 60, 'delay']

        total_arrival_delays_day = int(np.sum(arrival_delays_day))

        average_arrival_delay_day = int(total_arrival_delays_day/date_number_of_flights) if date_number_of_flights!=0 else 0

        arrival_delays_15_min_day = new_df.loc[new_df.delay > 900, 'delay']
        percent_delayed_day = len(arrival_delays_15_min_day)/date_number_of_flights*100 if date_number_of_flights!=0 else 0

        #create the line for date
        arrival_delays_by_day_df = arrival_delays_by_day_df.append({'date': date, 'number_of_flights': number_of_flights,
            'total_delay': total_arrival_delays_day, 'average_delay': average_arrival_delay_day,
            'percent_delayed': percent_delayed_day}, ignore_index=True)

    # in case there are misssing dates (no delays that day), creating empty rows for missing dates
    (nrows, ncol) = arrival_delays_by_day_df.shape
    if nrows < number_of_days:
        date = "18" + month
        month_date_list = []
        for d in range(1,9):
            month_date_list.append(date + '0' + str(d))
        for d in range(10,number_of_days+1):
            month_date_list.append(date + str(d))
        df_dates_np = arrival_delays_by_day_df.iloc[:,0].values

        for d in month_date_list:
            if d not in df_dates_np:
                arrival_delays_by_day_df = arrival_delays_by_day_df.append({'date': d, 'number_of_flights': 0, 'total_delay': 0,
                    'average_delay': 0, 'percent_delayed': 0}, ignore_index=True)

        arrival_delays_by_day_df = arrival_delays_by_day_df.sort_values(by ='date' )
        arrival_delays_by_day_df.reset_index(drop=True, inplace=True)

    arrival_delays_by_day_df.to_csv(filename, sep=' ', encoding='utf-8', float_format='%.2f', header=None)
    return arrival_delays_by_day_df



def calculate_ddr_entrypoints_stat(track1_df, track2_df):

    #number_of_flights_m1 = len(tracks1)
    #number_of_flights_m3 = len(tracks2)

    NILUG_m1_count = len(track1_df[track1_df['segmentIds'].str.contains("NILUG'_")])
    XILAN_m1_count = len(track1_df[track1_df['segmentIds'].str.contains("XILAN'_")])
    HMR_m1_count = len(track1_df[track1_df['segmentIds'].str.contains("HMR'_")])
    ELTOK_m1_count = len(track1_df[track1_df['segmentIds'].str.contains("ELTOK'_")])
    #TODO: no entrypoint?

    NILUG_m3_count = len(track2_df[track1_df['segmentIds'].str.contains("NILUG'_")])
    XILAN_m3_count = len(track2_df[track1_df['segmentIds'].str.contains("XILAN'_")])
    HMR_m3_count = len(track2_df[track1_df['segmentIds'].str.contains("HMR'_")])
    ELTOK_m3_count = len(track2_df[track1_df['segmentIds'].str.contains("ELTOK'_")])

    #TODO:
    changed_entry_points_number = 0
    unchanged_entry_points_number = 0


    #print("number_of_flights_m1")
    #print(number_of_flights_m1)
    #print("number_of_flights_m3")
    #print(number_of_flights_m3)

    #AFR1462
    #print("Entry points in ddr m1")
    #print("HMR")
    #print(HMR_m1_count)
    #print("{0:.1f}".format((HMR_m1_count/number_of_flights_m1)*100)+'%')
    #print("NILUG")
    #print(NILUG_m1_count)
    #print("{0:.1f}".format((NILUG_m1_count/number_of_flights_m1)*100)+'%')
    #print("XILAN")
    #print(XILAN_m1_count)
    #print("{0:.1f}".format((XILAN_m1_count/number_of_flights_m1)*100)+'%')
    #print("ELTOK")
    #print(ELTOK_m1_count)
    #print("{0:.1f}".format((ELTOK_m1_count/number_of_flights_m1)*100)+'%')
    #print("Entry points m1 summa")
    #print(HMR_m1_count+NILUG_m1_count+XILAN_m1_count+ELTOK_m1_count)

    #print("Unchanged entry points number")
    #print(unchanged_entry_points_number)
    #print("Procents of unchanged entry points")
    #print("{0:.1f}".format((unchanged_entry_points_number/number_of_flights_m1)*100)+'%')

    #print("Changed entry points number")
    #print(changed_entry_points_number)
    #print("Procents of changed entry points")
    #print("{0:.1f}".format((changed_entry_points_number/number_of_flights_m1)*100)+'%')


def calculate_opensky_delays(track1_df, track2_df):
    global opensky_total_arrival_delays, opensky_average_arrival_delay
    global opensky_total_departure_delays, opensky_average_departure_delay
    global opensky_delayed_5_min_count, opensky_delayed_15_min_count

    opensky_total_arrival_delays = 0
    opensky_average_arrival_delay = 0
    opensky_total_departure_delays = 0
    opensky_average_departure_delay = 0

    arrival_delays = np.array([])
    departure_delays = np.array([])


    ddr_m1_maxTimestamp_df = track1_df.groupby(level='flightId').tail(1)[['endTimestamp']]
    opensky_low_alt = track2_df[track2_df['baroAltitude']<1000] #to remove height fluctuation in the end
    opensky_maxTimestamp_df = opensky_low_alt.groupby(level='flightId').tail(1)[['timestamp']]

    arrival_delay_df = pd.merge(ddr_m1_maxTimestamp_df, opensky_maxTimestamp_df, on=['flightId'])
    arrival_delay_df['delay'] = arrival_delay_df['timestamp']- arrival_delay_df['endTimestamp']

    arrival_delays = arrival_delay_df.loc[arrival_delay_df.delay > 60, 'delay']

    opensky_total_arrival_delays = int(np.sum(arrival_delays))
    opensky_average_arrival_delay = int(opensky_total_arrival_delays/len(arrival_delays)) if arrival_delays.any() else 0


    ddr_m1_minTimestamp_df = track1_df.groupby(level='flightId').head(1)[['beginTimestamp']]
    opensky_minTimestamp_df = track2_df.groupby(level='flightId').head(1)[['timestamp']]

    departure_delay_df = pd.merge(ddr_m1_minTimestamp_df, opensky_minTimestamp_df, on=['flightId'])
    departure_delay_df['delay'] = departure_delay_df['timestamp']- departure_delay_df['beginTimestamp']

    departure_delays = departure_delay_df.loc[departure_delay_df.delay > 60, 'delay']

    opensky_total_departure_delays = int(np.sum(departure_delays))
    opensky_average_departure_delay = int(opensky_total_departure_delays/len(departure_delays)) if departure_delays.any() else 0


    arrival_delays_5_min = arrival_delay_df.loc[arrival_delay_df.delay > 300, 'delay']
    arrival_delays_15_min = arrival_delay_df.loc[arrival_delay_df.delay > 900, 'delay']
    opensky_delayed_5_min_count = len(arrival_delays_5_min)
    opensky_delayed_15_min_count = len(arrival_delays_15_min)


def get_L_avg():
    global L_avg
    return L_avg

def get_D_avg():
    global D_avg
    return D_avg

def get_S_D():
    global S_D
    return S_D

def get_T_avg():
    global T_avg
    return T_avg

def get_S_T():
    global S_T
    return S_T

def get_P():
    global P
    return P

def get_kpi19_1():
    global kpi19_1
    return kpi19_1

def get_kpi19_2():
    global kpi19_2
    return kpi19_2

def get_ddr_total_arrival_delays():
    global ddr_total_arrival_delays
    return ddr_total_arrival_delays

def get_ddr_average_arrival_delay():
    global ddr_average_arrival_delay
    return ddr_average_arrival_delay

def get_ddr_total_departure_delays():
    global ddr_total_departure_delays
    return ddr_total_departure_delays

def get_ddr_average_departure_delay():
    global ddr_average_departure_delay
    return ddr_average_departure_delay

def get_opensky_total_arrival_delays():
    global opensky_total_arrival_delays
    return opensky_total_arrival_delays

def get_opensky_average_arrival_delay():
    global opensky_average_arrival_delay
    return opensky_average_arrival_delay

def get_opensky_total_departure_delays():
    global opensky_total_departure_delays
    return opensky_total_departure_delays

def get_opensky_average_departure_delay():
    global opensky_average_departure_delay
    return opensky_average_departure_delay

def get_ddr_delayed_5_min_count():
    global ddr_delayed_5_min_count
    return ddr_delayed_5_min_count

def get_ddr_delayed_15_min_count():
    global ddr_delayed_15_min_count
    return ddr_delayed_15_min_count

def get_opensky_delayed_5_min_count():
    global opensky_delayed_5_min_count
    return opensky_delayed_5_min_count

def get_opensky_delayed_15_min_count():
    global opensky_delayed_15_min_count
    return opensky_delayed_15_min_count


def calculate_vfe(tracks_opensky_df, states_opensky_df, full_vfe_csv_filename):
    global P, L_avg, D_avg, S_D, T_avg, S_T, kpi19_1, kpi19_2

    min_level_time = 30
    #Y/X = 300 feet per minute
    rolling_window_Y = (300*(min_level_time/60))/ 3.281 # feet to meters
    print(rolling_window_Y)

    #descent part ends at 1800 feet
    descent_end_altitude = 1800 / 3.281
    print(descent_end_altitude)

    vfe_df = pd.DataFrame(columns=['flight_id', 'date', 'time_end', 'number_of_levels', 'time_on_levels', 'time_on_levels_percent',
                                   'distance_on_levels', 'distance_on_levels_percent'])

    states_opensky_df.reset_index(level=states_opensky_df.index.names, inplace=True)

    number_of_levels_lst = []
    distance_on_levels_lst = []
    distance_on_levels_percent_lst = []
    time_on_levels_lst = []
    time_on_levels_percent_lst = []

    flight_id_num = len(tracks_opensky_df.groupby(level='flightId'))
    number_of_level_flights = 0

    count = 0
    for flight_id, new_df in tracks_opensky_df.groupby(level='flightId'):

        count = count + 1
        print(flight_id_num, count)

        l = len(new_df.index)
        time_end = new_df.ix[(flight_id, l)]['time']


        flight_id_states_df = states_opensky_df[(states_opensky_df['flightId']==flight_id)]

        flight_id_states_df.set_index(['sequence'], inplace=True)

        number_of_levels = 0

        time_sum = 0
        time_on_levels = 0
        time_on_level = 0

        distance_sum = 0
        distance_on_levels = 0
        distance_on_level = 0

        level = 'false'
        altitude1 = 0 # altitude at the beginning of rolling window
        altitude2 = 0 # altitude at the end of rolling window
        altitude_level_begin = 0 #not used
        altitude_level_end = 0   #can be removed

        seq_level_begin = 0
        seq_level_end = 0
        seq_min_level_time = 0

        df_length = len(flight_id_states_df)
        for seq, row in flight_id_states_df.iterrows():

            if (seq + min_level_time) >= df_length:
                break

            altitude1 = row['altitude']
            altitude2 = flight_id_states_df.ix[seq+min_level_time-1]['altitude']

            if altitude2 < descent_end_altitude:
                break

            time_sum = time_sum + 1
            distance_sum = distance_sum + row['velocity']

            if abs(altitude1 - altitude2) > 1000:
                continue

            if level == 'true':

                if seq < seq_level_end:
                    if altitude1 - altitude2 < rolling_window_Y: #extend the level
                        seq_level_end = seq_level_end + 1
                        altitude_level_end = altitude2
                    if seq < seq_min_level_time: # do not count first 30 seconds
                        continue
                    else:
                        time_on_level = time_on_level + 1
                        distance_on_level = distance_on_level + row['velocity']
                else: # level ends
                    if seq_level_end >= seq_min_level_time:
                        number_of_levels = number_of_levels + 1
                    level = 'false'
                    time_on_levels = time_on_levels + time_on_level
                    distance_on_levels = distance_on_levels + distance_on_level
                    time_on_level = 0
                    distance_on_level = 0
            else: #not level
                if altitude1 - altitude2 < rolling_window_Y: # level begins
                    level = 'true'
                    seq_level_begin = seq
                    seq_min_level_time = seq + min_level_time
                    seq_level_end = seq + min_level_time - 1
                    altitude_level_begin = altitude1
                    altitude_level_end = altitude2
                    time_on_level = time_on_level + 1
                    distance_on_level = distance_on_level + row['velocity']

        if (time_sum == 0) or (distance_sum == 0):
            continue
        if number_of_levels > 0:
            number_of_level_flights = number_of_level_flights + 1
        number_of_levels_str = str(number_of_levels)

        number_of_levels_lst.append(number_of_levels)

        # convert distance to NM and time to munutes
        distance_on_levels = distance_on_levels * 0.000539957   #meters to NM
        distance_sum = distance_sum * 0.000539957   #meters to NM
        time_on_levels = time_on_levels / 60    #seconds to minutes
        time_sum = time_sum /60   #seconds to minutes

        distance_on_levels_lst.append(distance_on_levels)
        distance_on_levels_str = "{0:.3f}".format(distance_on_levels)

        distance_on_levels_percent = distance_on_levels / distance_sum *100
        distance_on_levels_percent_lst.append(distance_on_levels_percent)
        distance_on_levels_percent_str = "{0:.1f}".format(distance_on_levels_percent)


        time_on_levels_lst.append(time_on_levels)
        time_on_levels_str = "{0:.3f}".format(time_on_levels)

        time_on_levels_percent = time_on_levels / time_sum *100
        time_on_levels_percent_lst.append(time_on_levels_percent)
        time_on_levels_percent_str = "{0:.1f}".format(time_on_levels_percent)

        date_str = tracks_opensky_df.ix[(flight_id, 1)]['date']
        vfe_df = vfe_df.append({'flight_id': flight_id, 'date': date_str, 'time_end': time_end, 'number_of_levels': number_of_levels_str,
                                'distance_on_levels': distance_on_levels_str, 'distance_on_levels_percent': distance_on_levels_percent_str,
                                'time_on_levels': time_on_levels_str, 'time_on_levels_percent': time_on_levels_percent_str}, ignore_index=True)

    vfe_df.to_csv(full_vfe_csv_filename, sep=' ', encoding='utf-8', float_format='%.1f', header=True, index=False)

    P = int(number_of_level_flights/count*100)
    L_avg = statistics.mean(number_of_levels_lst)
    D_avg = statistics.mean(distance_on_levels_lst)
    S_D = statistics.pstdev(distance_on_levels_lst)
    T_avg = statistics.mean(time_on_levels_lst)
    S_T = statistics.pstdev(time_on_levels_lst)
    kpi19_1 = int(statistics.mean(distance_on_levels_percent_lst))
    kpi19_2 = int(statistics.mean(time_on_levels_percent_lst))
