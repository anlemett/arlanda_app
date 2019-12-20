from constants import *
import pandas as pd
import numpy as np

import ddr
import opensky

#TODO:
#from threading import Lock
#lock = Lock()

#import matplotlib
#matplotlib.use('Agg')
#import matplotlib.pyplot as plt

#def callback():
#    # ... (process data)
#    with lock:
#        fig = pyplot.figure()
#        # ... (draw stuff)
#        fig.savefile(path)


def make_traj_lat_ddr_plot(plt, tracks_df, color):

    for flight_id, new_df in tracks_df.groupby(level='flightId'):
        lon = []
        lat = []
        for seq, row in new_df.groupby(level='sequence'):
            lon.append(row.ix[(flight_id, seq)]['endLon'])
            lat.append(row.ix[(flight_id, seq)]['endLat'])
               
        plt.plot(lon, lat, color=color, linewidth=3)


def make_traj_lat_opensky_plot(plt, tracks_df, color):

    for flight_id, new_df in tracks_df.groupby(level='flightId'):
        lon = []
        lat = []
        for seq, row in new_df.groupby(level='sequence'):
            lon.append(row.ix[(flight_id, seq)]['lon'])
            lat.append(row.ix[(flight_id, seq)]['lat'])
        
        plt.plot(lon, lat, color=color, linewidth=3)


def make_TMA_plot(plt):

    plt.plot(TMA_lon, TMA_lat, color="blue")
    plt.plot(rwy1_lon,rwy1_lat, color="red")
    plt.plot(rwy2_lon,rwy2_lat, color="red")
    plt.plot(rwy3_lon,rwy3_lat, color="red")
    #plt.plot(rwy4_lon,rwy4_lat, color="red")

    plt.plot(HMR_lon, HMR_lat, 'ro')
    plt.plot(NILUG_lon, NILUG_lat, 'ro')
    plt.plot(XILAN_lon, XILAN_lat, 'ro')
    plt.plot(ELTOK_lon, ELTOK_lat, 'ro')


def save_traj_lat_plots(full_filename_lat, full_filename_lat_zoom, full_filename_lat_zoom2, is_ddr_m1, is_ddr_m3, is_opensky,
                    TMA_tracks_m1_df, TMA_tracks_m3_df, TMA_tracks_opensky_df):
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    import matplotlib.patches as mpatches

    min_lon = min(TMA_lon)
    min_lat = min(TMA_lat)
    max_lon = max(TMA_lon)
    max_lat = max(TMA_lat)
    
    tracks_df = pd.DataFrame()

    plt.figure(figsize=(9,6))
        
    tracks_df = TMA_tracks_m1_df
    if is_ddr_m1:
        make_traj_lat_ddr_plot(plt, TMA_tracks_m1_df, DDR_M1_PLOT_COLOR)
                
    if is_ddr_m3:
        make_traj_lat_ddr_plot(plt, TMA_tracks_m3_df, DDR_M3_PLOT_COLOR)
        tracks_df = TMA_tracks_m3_df

    if is_opensky:
        make_traj_lat_opensky_plot(plt, TMA_tracks_opensky_df, OPENSKY_PLOT_COLOR)
        tracks_df = TMA_tracks_opensky_df

    make_TMA_plot(plt)
    
    plt.axis('equal')
    plt.axis([min_lon, max_lon, min_lat, max_lat])
    
    ax = plt.gca()
    
    m1_color_patch = mpatches.Patch(color=DDR_M1_ALTITUDES_COLOR, label='DDR m1')
    m3_color_patch = mpatches.Patch(color=DDR_M3_ALTITUDES_COLOR, label='DDR m3')
    opensky_tracks_color_patch = mpatches.Patch(color=OPENSKY_ALTITUDES_COLOR, label='Opensky tracks')
    
    handles = []
    if is_ddr_m1:
        handles += [m1_color_patch]
    if is_ddr_m3:
        handles += [m3_color_patch]
    if is_opensky:
        handles += [opensky_tracks_color_patch]
    
    plt.legend(handles=handles, fontsize=20, loc="best")

    plt.savefig(full_filename_lat)

  
    zoom_min_lon = 17.6
    zoom_min_lat = 59.45
    zoom_max_lon = 18.3
    zoom_max_lat = 59.85
    
    plt.axis([zoom_min_lon, zoom_max_lon, zoom_min_lat, zoom_max_lat])
    plt.savefig(full_filename_lat_zoom)


    zoom_min_lon = 17.9
    zoom_min_lat = 59.6
    zoom_max_lon = 18.0
    zoom_max_lat = 59.7
    
    plt.axis([zoom_min_lon, zoom_max_lon, zoom_min_lat, zoom_max_lat])

    plt.grid(color='gray', linestyle='-', linewidth=1)
    plt.savefig(full_filename_lat_zoom2)


    plt.gcf().clear() 
    
  
def make_traj_vert_plot(plt, is_ddr_m1, is_ddr_m3, is_opensky, 
                        tracks_ddr_m1_df, tracks_ddr_m3_df, tracks_opensky_df, states_opensky_df):
    plt.figure(figsize=(9,6))
    plt.xlabel('Time [sec]', fontsize=25)
    plt.ylabel('Altitude [m]', fontsize=25)
    
    plt.tick_params(labelsize=15)
    
    #DDR m1
    for flight_id, flight_id_group in tracks_ddr_m1_df.groupby(level='flightId'):
        ddr_m1_altitudes = []
        ddr_m1_times = []

        ddr_m1_timestamp1 = flight_id_group.loc[flight_id].head(1)['beginTimestamp'].item()
        for seq, row in flight_id_group.groupby(level='sequence'):
            ddr_m1_times.append(row.loc[(flight_id, seq)]['beginTimestamp'] - ddr_m1_timestamp1)
            ddr_m1_altitudes.append(row.loc[(flight_id, seq)]['beginAltitude'])

            #plt.plot(ddr_m1_times, ddr_m1_altitudes, color=color_ddr_m1, linewidth = 4)


        ddr_m3_altitudes = []
        ddr_m3_times = []
        
        if is_ddr_m3:
            try:
                #DDR m3
                flight_tracks_ddr_m3_df = tracks_ddr_m3_df.loc[(flight_id,), :]
                        
                ddr_m3_timestamp1 = flight_tracks_ddr_m3_df.head(1)['beginTimestamp'].item()
                for seq, row in flight_tracks_ddr_m3_df.groupby(level='sequence'):
                    ddr_m3_times.append(row['beginTimestamp'].item() - ddr_m3_timestamp1)
                    ddr_m3_altitudes.append(row['beginAltitude'].item())

                #plt.plot(ddr_m3_times, ddr_m3_altitudes, color=color_ddr_m3, linewidth = 4)
            except KeyError:
                print("No ddr m3 tracks data")
            except:
                print("Exception in ddr m3 tracks reading")
        

        flight_tracks_opensky_df = pd.DataFrame()
        if is_opensky:
            #Opensky tracks
            
            try:
        
                flight_tracks_opensky_df = tracks_opensky_df.loc[(flight_id,), :]
      
                opensky_timestamp1 = flight_tracks_opensky_df.head(1)['timestamp'].item()
    
                opensky_tracks_altitudes_df = flight_tracks_opensky_df['baroAltitude']
                opensky_tracks_timestamps_df = flight_tracks_opensky_df['timestamp']
                opensky_tracks_times_df = opensky_tracks_timestamps_df - opensky_timestamp1
        
                #plt.plot(opensky_tracks_times_df, opensky_tracks_altitudes_df, color='red', linewidth=1)
        
                #opensky_tracks_altitudes_rolled_df = opensky_tracks_altitudes_df.rolling(5).median().fillna(method='bfill').fillna(method='ffill')        
                #plt.plot(opensky_tracks_times_df, opensky_tracks_altitudes_rolled_df, color='darkred', linewidth=1)
        
                opensky_tracks_fixed_altitudes = []

                prev_t = 0
                prev_altitude = flight_tracks_opensky_df.head(1)['baroAltitude'].item()
        
                for seq, row in flight_tracks_opensky_df.groupby(level='sequence'):
            
                    t = row['timestamp'].item() - opensky_timestamp1
                                    
                    if ((t-prev_t) < 10) and (abs(row['baroAltitude'].item() - prev_altitude) > 900) or \
                    (prev_t > 0) and (abs(row['baroAltitude'].item() - prev_altitude) > 3000) or \
                    (prev_t > 0) and (row['baroAltitude'].item() > 10000):     #to remove altitude fluctuations
                        opensky_tracks_fixed_altitudes.append(prev_altitude)
                
                    else:
                        opensky_tracks_fixed_altitudes.append(row['baroAltitude'].item())
                        prev_altitude = row['baroAltitude'].item()
                
                    prev_t = t

                plt.plot(opensky_tracks_times_df, opensky_tracks_fixed_altitudes, color=OPENSKY_ALTITUDES_COLOR, linewidth=4)
                
            except KeyError:
                print("No tracks data")
            except:
                print("Exception in tracks reading")


            flight_states_opensky_df = pd.DataFrame()

            #Opensky States
            try:
                flight_states_opensky_df = states_opensky_df.loc[(flight_id,), :]
                
                print(flight_id)
                print(flight_states_opensky_df)
        
                if not flight_states_opensky_df.empty:
                    opensky_states_altitudes = []
                    opensky_states_times = []
                    opensky_states_fixed_altitudes = []

                    t = 0
                    prev_altitude = flight_states_opensky_df.head(1)['altitude'].item()

                    for seq, row in flight_states_opensky_df.groupby(level='sequence'):
            
                        t = t + 1
                        opensky_states_times.append(t)
                        
                        opensky_states_altitudes.append(row['altitude'].item())
            
                        if abs(row['altitude'].item() - prev_altitude) > 900:     #to remove altitude fluctuations
                            opensky_states_fixed_altitudes.append(prev_altitude)
                            continue
            
                        opensky_states_fixed_altitudes.append(row['altitude'].item())

                        prev_altitude = row['altitude'].item()
            
                    plt.plot(opensky_states_times, opensky_states_fixed_altitudes, color=OPENSKY_STATES_ALTITUDES_COLOR, linewidth=4)
                    #plt.plot(opensky_states_times, opensky_states_altitudes, color='black', linewidth=4)
                    
            except KeyError:
                print("No states data")
            except:
                print("Exception in states reading")
        
        if is_opensky and (not flight_states_opensky_df.empty):
            
            if is_ddr_m1:            
            # Move ddr m1:
            
                time_shift = 0
 
                j = len(ddr_m1_altitudes) - 1
                  
                while (ddr_m1_altitudes[j] < opensky_states_fixed_altitudes[-1]) and (j>=0):
                    j = j - 1

                i = len(opensky_states_fixed_altitudes) - 1
                while (opensky_states_fixed_altitudes[i] < ddr_m1_altitudes[j]) and (i>=0):
                    i = i - 1
                    time_shift = abs(opensky_states_times[i]-ddr_m1_times[j])
            
                ddr_m1_times = [x + time_shift for x in ddr_m1_times]
                       
                plt.plot(ddr_m1_times, ddr_m1_altitudes, color=DDR_M1_ALTITUDES_COLOR, linewidth = 4)
  

            if is_ddr_m3:
            # Move ddr m3:
                time_shift = 0            
                j = len(ddr_m3_altitudes) - 1
                while (ddr_m3_altitudes[j] < opensky_states_fixed_altitudes[-1]) and (j>=0):
                    j = j - 1

                i = len(opensky_states_fixed_altitudes) - 1
                while (opensky_states_fixed_altitudes[i] < ddr_m3_altitudes[j]) and (i>=0):
                    i = i - 1
                    time_shift = abs(opensky_states_times[i]-ddr_m3_times[j])
            
                ddr_m3_times = [x + time_shift for x in ddr_m3_times]

                plt.plot(ddr_m3_times, ddr_m3_altitudes, color=DDR_M3_ALTITUDES_COLOR, linewidth = 4)

        else: #no opensky
            #should we allign m1 and m3?    
            if is_ddr_m1: # only ddr m1
                print("is_ddr_m1, no opensky")
                plt.plot(ddr_m1_times, ddr_m1_altitudes, color=DDR_M1_ALTITUDES_COLOR, linewidth = 4)
            if is_ddr_m3: # only ddr m3
                print("is_ddr_m3, no opensky")
                plt.plot(ddr_m3_times, ddr_m3_altitudes, color=DDR_M3_ALTITUDES_COLOR, linewidth = 4)
                                

def save_traj_vert_plot(full_filename, is_ddr_m1, is_ddr_m3, is_opensky,
                                    tracks_ddr_m1_df, tracks_ddr_m3_df, tracks_opensky_df, states_opensky_df):
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    import matplotlib.patches as mpatches

    make_traj_vert_plot(plt, is_ddr_m1, is_ddr_m3, is_opensky, tracks_ddr_m1_df, tracks_ddr_m3_df, tracks_opensky_df, states_opensky_df)
    
    m1_color_patch = mpatches.Patch(color=DDR_M1_ALTITUDES_COLOR, label='DDR m1')
    m3_color_patch = mpatches.Patch(color=DDR_M3_ALTITUDES_COLOR, label='DDR m3')
    opensky_tracks_color_patch = mpatches.Patch(color=OPENSKY_ALTITUDES_COLOR, label='Opensky tracks')
    opensky_states_color_patch = mpatches.Patch(color=OPENSKY_STATES_ALTITUDES_COLOR, label='Opensky states')
    
    handles = []
    if is_ddr_m1:
        handles += [m1_color_patch]
    if is_ddr_m3:
        handles += [m3_color_patch]
    if is_opensky:
        handles += [opensky_tracks_color_patch, opensky_states_color_patch]
    
    plt.legend(handles=handles, fontsize=20, loc="upper right")

    plt.savefig(full_filename)

    plt.gcf().clear()




def make_fuel_plot(plt, fuel_consumption_df, timestamps_df ):

    timestamps = []
    fuel = []

    for i, column in enumerate(fuel_consumption_df):
        fuel.append(list(fuel_consumption_df[column]))

    for i, column in enumerate(timestamps_df):
        timestamps = list(timestamps_df[column])
        plt.plot(timestamps, fuel[i], label = column)


    ax = plt.gca()
    ax.set_xlim(xmin=0)
    ax.set_ylim(ymin=0)

    plt.xlabel('time [s]')
    plt.ylabel('fuel consumption [kg]')
    
    plt.grid(color='gray', linestyle='-', linewidth=1)


def save_fuel_plot(full_filename, fuel_consumption_df, timestamps_df):
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt

    make_fuel_plot(plt, fuel_consumption_df, timestamps_df)

    plt.savefig(full_filename)

    plt.gcf().clear()


