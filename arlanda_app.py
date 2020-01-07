from config import (DEBUG, PORT, HOST,
                    INPUT_DIR, OUTPUT_DIR, OUTPUT_PICTURES_DIR,
                    DDR_M1, DDR_M3, OPENSKY, DDR_M1_M3, DDR_M1_OPENSKY, STAT, FUEL, VFE, VP 
                    )
from config import *
from constants import (TMA_timezone,
                       DDR_M1_PLOT_COLOR, DDR_M3_PLOT_COLOR, OPENSKY_PLOT_COLOR, 
                       DDR_M1_ALTITUDES_COLOR, DDR_M3_ALTITUDES_COLOR, OPENSKY_ALTITUDES_COLOR, OPENSKY_STATES_ALTITUDES_COLOR
                       #TMA_COLOR, RWYS_COLOR, ENTRY_POINTS_COLOR
                       )


import os, glob

from flask import (Flask, render_template, request, redirect, url_for)
import forms

from datetime import datetime, time, timedelta
import pytz

import pandas as pd
import numpy as np

import plot
import flight_stat
import ddr
import opensky
import weather


app = Flask(__name__)

app.config.from_object('config')

if not os.path.exists(INPUT_DIR):
    os.makedirs(INPUT_DIR)
if not os.path.exists(OUTPUT_DIR):
    os.makedirs(OUTPUT_DIR)
if not os.path.exists(OUTPUT_PICTURES_DIR):
    os.makedirs(OUTPUT_PICTURES_DIR)

TMA_all_tracks_m1_df = ddr.get_all_tracks(os.path.join(INPUT_DIR, TRACKS_TMA_DDR_M1_CSV))
TMA_all_tracks_m3_df = ddr.get_all_tracks(os.path.join(INPUT_DIR, TRACKS_TMA_DDR_M3_CSV))
TMA_all_tracks_opensky_df = opensky.get_all_tracks(os.path.join(INPUT_DIR, TRACKS_TMA_OPENSKY_CSV))
#TMA_all_states_opensky_df = opensky.get_all_states(os.path.join(INPUT_DIR, STATES_TMA_OPENSKY_CSV))

ddr_stat_by_day_df = ddr.get_stat(os.path.join(INPUT_DIR, STAT_DDR_BY_DAY_CSV))
opensky_stat_by_day_df = opensky.get_stat(os.path.join(INPUT_DIR, STAT_OPENSKY_BY_DAY_CSV))

TMA_tracks_m1_df = pd.DataFrame()
TMA_tracks_m3_df = pd.DataFrame()
TMA_tracks_opensky_df = pd.DataFrame()
TMA_states_opensky_df = pd.DataFrame()

#metar_df = weather.get_metar_df(os.path.join(INPUT_DIR, METAR_CSV))
#grib_df = weather.get_grib_df(os.path.join(INPUT_DIR, GRIB_CSV))



#TODO: make parameters instead of global:
callsign = ''
in_out = 'all'
date_begin = 0
date_end = 0
date_begin_str = ''
date_end_str = ''
is_ddr_m1 = False
is_ddr_m3 = False
is_opensky = False


@app.errorhandler(404)
def not_found(error):
    return render_template('404.html'), 404


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/trajectories/', methods=['GET', 'POST'])
def view_trajectories_form():
    global TMA_all_tracks_m1_df, TMA_tracks_m1_df
    global TMA_all_tracks_m3_df, TMA_tracks_m3_df
    global TMA_all_tracks_opensky_df, TMA_tracks_opensky_df, TMA_states_opensky_df
    global callsign, in_out, date_begin, date_end, date_begin_str, date_end_str, is_ddr_m1, is_ddr_m3, is_opensky
    form = forms.TrajectoriesForm(request.form)
    if request.method == 'POST' and form.validate():
        date_begin = form.date_begin.data
        date_end = form.date_end.data
        date_begin_str = date_begin.strftime("%Y%m%d")
        date_end_str = date_end.strftime("%Y%m%d")

        callsign = form.callsign.data
        #in_out = form.in_out.data

        local_tz = pytz.timezone(TMA_timezone)

        local_time_begin = local_tz.localize(datetime.combine(form.date_begin.data, time.min))
        utc_time_begin = local_time_begin.astimezone(pytz.utc)
        timestamp_begin = utc_time_begin.timestamp()
        local_time_end = local_tz.localize(datetime.combine(form.date_end.data, time.max))
        utc_time_end = local_time_end.astimezone(pytz.utc)
        timestamp_end = utc_time_end.timestamp()

        is_ddr_m1 = False
        is_ddr_m3 = False
        is_opensky = False

        if request.form.get('checkbox-ddr-m1'):
            is_ddr_m1 = True
            
        #get m1 data for vertical profile reference even if not checked
        TMA_tracks_m1_df = ddr.get_tracks_by_callsign(TMA_all_tracks_m1_df, callsign)
        TMA_tracks_m1_df = ddr.get_tracks_by_time(TMA_tracks_m1_df, timestamp_begin, timestamp_end)
            
        if request.form.get('checkbox-ddr-m3'):
            is_ddr_m3 = True
            TMA_tracks_m3_df = ddr.get_tracks_by_callsign(TMA_all_tracks_m3_df, callsign)
            TMA_tracks_m3_df = ddr.get_tracks_by_time(TMA_tracks_m3_df, timestamp_begin, timestamp_end)
            
        if request.form.get('checkbox-opensky'):       
            is_opensky = True
            TMA_tracks_opensky_df = opensky.get_tracks_by_callsign(TMA_all_tracks_opensky_df, callsign)
            TMA_tracks_opensky_df = opensky.get_tracks_by_time(TMA_tracks_opensky_df, timestamp_begin, timestamp_end)
        

            #TMA Opensky states
            month_begin = datetime.fromtimestamp(timestamp_begin).month
            month_end = datetime.fromtimestamp(timestamp_end).month
        
            TMA_states_opensky_df = pd.DataFrame()
        
            for month in range(month_begin, month_end+1):
            
                month_str = str(month) if month>9 else '0' + str(month)
                states_filename = STATES_TMA_OPENSKY + month_str + ".csv"
            
                TMA_all_states_opensky_month_df = opensky.get_all_states(os.path.join(INPUT_DIR, states_filename))
        
                TMA_states_opensky_month_df = opensky.get_states(TMA_tracks_opensky_df, TMA_all_states_opensky_month_df)
            
                TMA_states_opensky_df = pd.concat([TMA_states_opensky_df, TMA_states_opensky_month_df])
              

        #if ( in_out == "domestic"):
        #    TMA_tracks_m1_df = ddr.get_domestic_tracks(TMA_tracks_m1_df)
        #    TMA_tracks_m3_df = ddr.get_domestic_tracks(TMA_tracks_m3_df)
        #    df_opensky = opensky.get_domestic_tracks(df_opensky)
        #elif ( in_out == "international"):
        #    df_m1 = ddr.get_international_tracks(df_m1)
        #    df_m3 = ddr.get_international_tracks(df_m3)
        #    TMA_tracks_opensky_df = opensky.get_international_tracks(TMA_tracks_opensky_df)


        return redirect(url_for('view_trajectories_plot'))
    return render_template('form_trajectories.html', form=form)


@app.route('/trajectories/plot')
def view_trajectories_plot():
    global TMA_tracks_m1_df, TMA_tracks_m3_df
    global TMA_tracks_opensky_df, TMA_states_opensky_df
    global callsign, in_out, date_begin, date_end, date_begin_str, date_end_str
    global is_ddr_m1, is_ddr_m3, is_opensky

    filename_lat = 'traj_lat'
    
    if is_ddr_m1:
        filename_lat += '_' + DDR_M1
    if is_ddr_m3:
        filename_lat += '_' + DDR_M3
    if is_opensky:
        filename_lat += '_' + OPENSKY
        
    #filename_lat += '_' + in_out if in_out else ''
    filename_lat += '_' + callsign if callsign else ''
    filename_lat += '_' +  date_begin_str + '_' +  date_end_str if date_begin_str else ''

    filename_lat += '.png'
    
    filename_lat_zoom = filename_lat
    filename_lat_zoom += '_zoom.png'

    filename_lat_zoom2 = filename_lat
    filename_lat_zoom2 += '_zoom2.png'

    full_filename_lat = os.path.join(app.config['OUTPUT_PICTURES_DIR'], filename_lat)
    full_filename_lat_zoom = os.path.join(app.config['OUTPUT_PICTURES_DIR'], filename_lat_zoom)
    full_filename_lat_zoom2 = os.path.join(app.config['OUTPUT_PICTURES_DIR'], filename_lat_zoom2)

    plot.save_traj_lat_plots(full_filename_lat, full_filename_lat_zoom, full_filename_lat_zoom2, is_ddr_m1, is_ddr_m3, is_opensky,
                             TMA_tracks_m1_df, TMA_tracks_m3_df, TMA_tracks_opensky_df)

    full_filename_lat = os.path.join(app.config['STATIC_PICTURES_DIR'], filename_lat)
    full_filename_lat_zoom = os.path.join(app.config['STATIC_PICTURES_DIR'], filename_lat_zoom)
    full_filename_lat_zoom2 = os.path.join(app.config['STATIC_PICTURES_DIR'], filename_lat_zoom2)
    
   
    filename_vert = 'traj_vert'
    
    if is_ddr_m1:
        filename_vert += '_' + DDR_M1
    if is_ddr_m3:
        filename_vert += '_' + DDR_M3
    if is_opensky:
        filename_vert += '_' + OPENSKY

    #filename_vert += '_' + in_out if in_out else ''
    filename_vert += '_' + callsign if callsign else ''
    filename_vert += '_' +  date_begin_str + '_' +  date_end_str if date_begin_str else ''
    filename_vert += '.png'
        
    full_filename_vert = os.path.join(app.config['OUTPUT_PICTURES_DIR'], filename_vert)

    plot.save_traj_vert_plot(full_filename_vert, is_ddr_m1, is_ddr_m3, is_opensky,
                             TMA_tracks_m1_df, TMA_tracks_m3_df, TMA_tracks_opensky_df, TMA_states_opensky_df)

    full_filename_vert = os.path.join(app.config['STATIC_PICTURES_DIR'], filename_vert)



    return render_template('plots_trajectories.html',  date_begin = date_begin, date_end = date_end, callsign = callsign,
                           filename1 = full_filename_lat, filename2 = full_filename_vert,
                           filename3 = full_filename_lat_zoom, filename4 = full_filename_lat_zoom2)



@app.route('/ddr_m1/fuel/')
def view_ddr_m1_calculate_fuel_old():
    global TMA_tracks_m1_df
    global callsign, date_begin_str, date_end_str

    fuel_csv_filename = FUEL + '_' + DDR_M1 + '_' + callsign + '_' + date_begin_str + '_' + date_end_str + '.csv'
    full_fuel_csv_filename = os.path.join(app.config['OUTPUT_DIR'], fuel_csv_filename)
    fuel_png_filename = FUEL + '_' + DDR_M1 + '_' + callsign + '_' + date_begin_str + '_' + date_end_str + '.png'
    full_fuel_png_filename = os.path.join(app.config['OUTPUT_PICTURES_DIR'], fuel_png_filename)

    vfe_csv_filename = VFE + '_' + DDR_M1 + '_' + callsign + '_' + date_begin_str + '_' + date_end_str + '.csv'
    full_vfe_csv_filename = os.path.join(app.config['OUTPUT_DIR'], vfe_csv_filename)

    ddr.calculate_fuel_inside_TMA(TMA_tracks_m1_df, full_fuel_csv_filename, full_fuel_png_filename, full_vfe_csv_filename)

    return render_template('index.html')

@app.route('/ddr_m3/fuel/')
def view_ddr_m3_calculate_fuel_old():
    global tracks_m3_df
    global callsign, in_out, date_begin_str, date_end_str

    fuel_csv_filename = FUEL + '_' + DDR_M3 + '_' + callsign + '_' + date_begin_str + '_' + date_end_str + '.csv'
    full_fuel_csv_filename = os.path.join(app.config['OUTPUT_DIR'], fuel_csv_filename)
    fuel_png_filename = FUEL + '_' + DDR_M3 + '_' + callsign + '_' + date_begin_str + '_' + date_end_str + '.png'
    full_fuel_png_filename = os.path.join(app.config['OUTPUT_PICTURES_DIR'], fuel_png_filename)
    vfe_csv_filename = VFE + '_' + DDR_M3 + '_' + callsign + '_' + date_begin_str + '_' + date_end_str + '.csv'
    full_vfe_csv_filename = os.path.join(app.config['OUTPUT_DIR'], vfe_csv_filename)

    ddr.calculate_fuel_inside_TMA(TMA_tracks_m3_df, full_fuel_csv_filename, full_fuel_png_filename, full_vfe_csv_filename)
    return render_template('index.html')

@app.route('/opensky/fuel/')
def view_opensky_calculate_fuel_old():
    global TMA_tracks_opensky_df, TMA_all_states_opensky_df, TMA_states_opensky_df
    global callsign, date_begin_str, date_end_str

    states_opensky_df = opensky.get_states(tracks_opensky_df, all_states_opensky_df)

    fuel_csv_filename = FUEL + '_' + OPENSKY + '_' + callsign + '_' + date_begin_str + '_' + date_end_str + '.csv'
    full_fuel_csv_filename = os.path.join(app.config['OUTPUT_DIR'], fuel_csv_filename)
    fuel_png_filename = FUEL + '_' + OPENSKY + '_' + callsign + '_' + date_begin_str + '_' + date_end_str + '.png'
    full_fuel_png_filename = os.path.join(app.config['OUTPUT_PICTURES_DIR'], fuel_png_filename)
    vfe_csv_filename = VFE + '_' + OPENSKY + '_' + callsign + '_' + date_begin_str + '_' + date_end_str + '.csv'
    full_vfe_csv_filename = os.path.join(app.config['OUTPUT_DIR'], vfe_csv_filename)

    #opensky.calculate_fuel_inside_TMA_tracks(tracks_opensky_df, full_fuel_csv_filename, full_fuel_png_filename, full_vfe_csv_filename)
    opensky.calculate_fuel_inside_TMA_states(states_opensky_df, full_fuel_csv_filename, full_fuel_png_filename, full_vfe_csv_filename)

    return render_template('index.html')



@app.route('/statistics/', methods=['GET', 'POST'])
def view_statistics_form():
    global ddr_stat_by_day_df
    global opensky_stat_by_day_df
    global date_begin_str, date_end_str

    form = forms.StatForm(request.form)
    if request.method == 'POST' and form.validate():
        date_begin = form.date_begin.data
        date_end = form.date_end.data
        date_begin_str = date_begin.strftime("%y%m%d")
        date_end_str = date_end.strftime("%y%m%d")

        # DDR
        df = ddr_stat_by_day_df[(ddr_stat_by_day_df['endDate'] >= date_begin_str) & (ddr_stat_by_day_df['endDate'] <= date_end_str)]
        
        ddr_number_of_days = len(df)
        
        ddr_number_of_flights = int(np.sum(df['number_of_flights']))

        total_arrival_delay_str = ''
        average_arrival_delay_str = ''

        total_departure_delay_str = ''
        average_departure_delay_str = ''

        kpi14_1b_str = ''
        kpi14_2b_str = ''

        if ddr_number_of_flights != 0:

            total_arrival_delay = int(np.sum(df['total_arrival_delay']))
            average_arrival_delay = total_arrival_delay/ddr_number_of_flights

            total_arrival_delay_str = str(timedelta(seconds=total_arrival_delay))
            average_arrival_delay_str  = "{0:.1f}".format(average_arrival_delay/60)

            #arrival_delayed_5_min_flights_number = int(np.sum(df['arrival_delayed_5_min_flights_number']))
            #kpi14_1b = (ddr_number_of_flights - arrival_delayed_5_min_flights_number)/ddr_number_of_flights*100
            #kpi14_1b_str = "{0:.1f}".format(kpi14_1b)

            arrival_delayed_15_min_flights_number = int(np.sum(df['arrival_delayed_15_min_flights_number']))
            kpi14_2b = (ddr_number_of_flights - arrival_delayed_15_min_flights_number)/ddr_number_of_flights*100
            kpi14_2b_str = "{0:.1f}".format(kpi14_2b)

            total_departure_delay = int(np.sum(df['total_departure_delay']))
            average_departure_delay = total_departure_delay/ddr_number_of_flights

            total_departure_delay_str =  str(timedelta(seconds=total_departure_delay))
            average_departure_delay_str = "{0:.1f}".format(average_departure_delay/60)

            sum_average_add_time = int(np.sum(df['average_add_time']))
            average_add_time = sum_average_add_time/ddr_number_of_days

            average_add_time_str = "{0:.1f}".format(average_add_time/60)


        # OPENSKY
        df = opensky_stat_by_day_df[(opensky_stat_by_day_df['date'] >= date_begin_str) & (opensky_stat_by_day_df['date'] <= date_end_str)]
        
        opensky_number_of_days = len(df)
        
        opensky_number_of_flights = int(np.sum(df['number_of_flights']))
        
        perc_level_flights_str = ''
        average_number_of_levels_str = ''
        average_distance_flown_level_str = ''
        average_time_flown_level_str = ''

        if opensky_number_of_flights != 0:
            
            sum_of_flights = np.sum(df['number_of_flights'])
            sum_of_level_flights = np.sum(df['number_of_level_flights'])
            perc_level_flights = sum_of_level_flights/sum_of_flights*100
            perc_level_flights_str = "{0:.1f}".format(perc_level_flights)
            
            sum_of_average_number_of_levels = np.sum(df['average_number_of_levels'])
            average_number_of_levels = sum_of_average_number_of_levels/opensky_number_of_days
            average_number_of_levels_str = "{0:.1f}".format(average_number_of_levels)
            
            sum_of_average_distance_flown_level = np.sum(df['average_distance_on_levels'])
            average_distance_flown_level = sum_of_average_distance_flown_level/opensky_number_of_days            
            average_distance_flown_level_str = "{0:.1f}".format(average_distance_flown_level)

            sum_of_average_time_flown_level = np.sum(df['average_time_on_levels'])
            average_time_flown_level = sum_of_average_time_flown_level/opensky_number_of_days
            average_time_flown_level_str  = "{0:.1f}".format(average_time_flown_level)

        return render_template('statistics.html', date_begin = date_begin, date_end = date_end,
                                ddr_number_of_flights = ddr_number_of_flights,
                                total_arrival_delay = total_arrival_delay_str, average_arrival_delay = average_arrival_delay_str,
                                kpi14_2b = kpi14_2b_str,
                                total_departure_delay = total_departure_delay_str,
                                average_departure_delay = average_departure_delay_str,
                                average_add_time_in_TMA = average_add_time_str,
                                opensky_number_of_flights = opensky_number_of_flights, P = perc_level_flights_str, 
                                L_avg = average_number_of_levels_str, D_avg = average_distance_flown_level_str,
                                T_avg = average_time_flown_level_str                                
                                )

    return render_template('form_statistics.html', form=form)



def save_vfe_stat_old( number_of_flights, L_avg_str, D_avg_str, S_D_str, T_avg_str, S_T_str, P_str,
                   kpi19_1_str, kpi19_2_str ):

    global date_begin_str, date_end_str

    stat_vfe_filename = STAT + '_' + VFE + '.csv'
    stat_vfe_full_filename = os.path.join(app.config['OUTPUT_DIR'], stat_vfe_filename)

    stat_vfe_df = pd.DataFrame(columns=['date_begin', 'date_end', 'number_of_flights', 'L_avg', 'D_avg', 'S_D', 'T_avg', 'S_T',
                                        'P', 'kpi19_1', 'kpi19_2'])

    try:
        stat_vfe_df = pd.read_csv(stat_vfe_full_filename, sep = ' ',
                                dtype = { 'date_begin': str, 'date_end': str, 'number_of_flights': int, 'L_avg':str,
                                          'D_avg':str, 'S_D':str, 'T_avg':str, 'S_T':str, 'P':str, 'kpi19_1': str, 'kpi19_2': str })
    except:
        stat_vfe_df.to_csv(stat_vfe_full_filename, sep=' ', encoding='utf-8', float_format='%.1f', index=False)

    stat_vfe_df = stat_vfe_df.append({'date_begin': date_begin_str, 'date_end': date_end_str,
                                      'number_of_flights': number_of_flights, 'L_avg': L_avg_str,
                                      'D_avg': D_avg_str, 'S_D': S_D_str, 'T_avg': T_avg_str, 'S_T':S_T_str, 'P': P_str,
                                      'kpi19_1': kpi19_1_str, 'kpi19_2': kpi19_2_str}, ignore_index=True)

    stat_vfe_df.drop_duplicates(inplace=True)

    stat_vfe_df.to_csv(stat_vfe_full_filename, sep=' ', encoding='utf-8', float_format='%.1f', header=True, index=False)


def save_ddr_m1_ddr_m3_stat_old( total_arrival_delays_str, average_arrival_delay_str,
                             total_departure_delays_str, average_departure_delay_str,
                             kpi14_1b_str, kpi14_2b_str ):

    global callsign, in_out, date_begin_str, date_end_str

    stat_ddr_m1_m3_filename = STAT + '_' + DDR_M1_M3 + '.csv'
    stat_ddr_m1_m3_full_filename = os.path.join(app.config['OUTPUT_DIR'], stat_ddr_m1_m3_filename)

    stat_ddr_m1_m3_df = pd.DataFrame(columns=['date_begin', 'date_end', 'callsign', 'domestic_international',
                                            'total_arrival_delays', 'average_arrival_delay',
                                            'total_departure_delays', 'average_departure_delay', 'kpi14_1b', 'kpi14_2b'])

    try:
        stat_ddr_m1_m3_df = pd.read_csv(stat_ddr_m1_m3_full_filename, sep = ' ',
                                        dtype = { 'date_begin': str, 'date_end': str, 'callsign': str, 'domestic_international': str,
                                        'total_arrival_delays': str, 'average_arrival_delay': str,
                                        'total_departure_delays': str, 'average_departure_delay': str,
                                        'kpi14_1b': str, 'kpi14_2b': str })
    except:
        stat_ddr_m1_m3_df.to_csv(stat_ddr_m1_m3_full_filename, sep=' ', encoding='utf-8', float_format='%.6f', index=False)

    stat_ddr_m1_m3_df = stat_ddr_m1_m3_df.append({'date_begin': date_begin_str, 'date_end': date_end_str, 'callsign': callsign, 'domestic_international': in_out,
                              'total_arrival_delays': total_arrival_delays_str, 'average_arrival_delay': average_arrival_delay_str,
                              'total_departure_delays': total_departure_delays_str, 'average_departure_delay': average_departure_delay_str,
                              'kpi14_1b': kpi14_1b_str, 'kpi14_2b': kpi14_2b_str}, ignore_index=True)

    stat_ddr_m1_m3_df.drop_duplicates(inplace=True)

    stat_ddr_m1_m3_df.to_csv(stat_ddr_m1_m3_full_filename, sep=' ', encoding='utf-8', float_format='%.6f', header=True, index=False)


def save_ddr_m1_opensky_stat_old( total_arrival_delays_str, average_arrival_delay_str,
                              total_departure_delays_str, average_departure_delay_str,
                              kpi14_1b_str, kpi14_2b_str ):

    global callsign, in_out, date_begin_str, date_end_str

    stat_ddr_m1_opensky_filename = STAT + '_' + DDR_M1_OPENSKY + '.csv'
    stat_ddr_m1_opensky_full_filename = os.path.join(app.config['OUTPUT_DIR'], stat_ddr_m1_opensky_filename)

    stat_ddr_m1_opensky_df = pd.DataFrame(columns=['date_begin', 'date_end', 'callsign', 'domestic_international',
                                            'total_arrival_delays', 'average_arrival_delay',
                                            'total_departure_delays', 'average_departure_delay', 'kpi14_1b', 'kpi14_2b'])

    try:
        stat_ddr_m1_opensky_df = pd.read_csv(stat_ddr_m1_opensky_full_filename, sep = ' ',
                                        dtype = { 'date_begin': str, 'date_end': str, 'callsign': str, 'domestic_international': str,
                                        'total_arrival_delays': str, 'average_arrival_delay': str,
                                        'total_departure_delays': str, 'average_departure_delay': str,
                                        'kpi14_1b': str, 'kpi14_2b': str })
    except:
        stat_ddr_m1_opensky_df.to_csv(stat_ddr_m1_opensky_full_filename, sep=' ', encoding='utf-8', float_format='%.6f', index=False)

    stat_ddr_m1_opensky_df = stat_ddr_m1_opensky_df.append({'date_begin': date_begin_str, 'date_end': date_end_str,
                                'callsign': callsign, 'domestic_international': in_out,
                                'total_arrival_delays': total_arrival_delays_str, 'average_arrival_delay': average_arrival_delay_str,
                                'total_departure_delays': total_departure_delays_str, 'average_departure_delay': average_departure_delay_str,
                                'kpi14_1b': kpi14_1b_str, 'kpi14_2b': kpi14_2b_str}, ignore_index=True)

    stat_ddr_m1_opensky_df.drop_duplicates(inplace=True)

    stat_ddr_m1_opensky_df.to_csv(stat_ddr_m1_opensky_full_filename, sep=' ', encoding='utf-8', float_format='%.6f', header=True, index=False)



def remove_files(path):
    files = glob.glob(path + '*')
    for f in files:
        os.remove(f)


# No caching at all for API endpoints (to update pictures)
@app.after_request
def add_header(response):
    response.headers['Cache-Control'] = 'public, no-store, no-cache, must-revalidate, post-check=0, pre-check=0, max-age=0'
    response.headers['Pragma'] = 'no-cache'
    response.headers['Expires'] = '-1'
    return response


if __name__ == '__main__':
    app.run(debug=DEBUG, host=HOST, port=PORT)
