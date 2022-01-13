# Access refresh token and extracting data
import requests
import urllib3
import json
import operator
import csv
import sys
import pickle
import pandas as pd
# import streamlit as st
import time
import plotly.express as px
import plotly.io as pio
import plotly
from plotly.offline import plot
from plotly.graph_objs import Scatter

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

csv.field_size_limit(sys.maxsize)

# loads activities from strava, save to txt file
# function run when user logs in
def load(id,secret,refresh):

    auth_url = "https://www.strava.com/oauth/token"
    activites_url = "https://www.strava.com/api/v3/athlete/activities"
    payload = {
        'client_id': str(id),
        'client_secret': str(secret),
        'refresh_token': str(refresh),
        'grant_type': "refresh_token",
        'f': 'json'
    }

    res = requests.post(auth_url, data=payload, verify=False)
    access_token = res.json()['access_token']
    print("Access Token = {}\n".format(access_token))

    header = {'Authorization': 'Bearer ' + access_token}

    i = 1

    activity_data = []
    # TODO: change this to dynamic (i.e. won't work if user's activities exceed 7 pages - won't include all activities)
    while i < 7:
        param = {'per_page': 200, 'page': i}
        # save each page to list
        activity_data.append(requests.get(activites_url, headers=header, params=param).json())
        i = i + 1
    # save all activities to txt file (note: do to pickle, the file is unreadable)
    with open('static/data/data.txt', 'wb') as f:
        pickle.dump(activity_data, f)
    return activity_data

# -----------------------------   
# Helper Functions
# ----------------------------- 

# removes time and excess characters from start_date_local key
def format_date(date):
    temp = date.split('T')
    return temp[0]

# determines whether an activity is within the specified timeframe(s) (inputted by user) 
def validate_date(a_date, s_date, e_date):
    act_date = time.strptime(a_date, "%Y-%m-%d")
    if (s_date == 0 and e_date == 0):
        output = True
    elif e_date == 0:
        output = act_date >= s_date
    elif s_date == 0:
        output = act_date <= e_date
    else:
        output = (act_date <= e_date and act_date >= s_date)
    return output

# outputs whether the activity meets operand activity (e.g. is distance greater
# than what the user specified)
def check_op(operand, round_dist, dist):
    ops = {
        ">": operator.gt,
        "<": operator.lt,
        "=": operator.eq
    }
    if operand != "--":
        op_func = ops[operand]
    # if user inputs "all" then this condition will always be true
    if operand == "--":
        output = True
    else:
        output = op_func(round_dist, dist)
    return output

# returns the month from start_date_local key
def get_month(date):
    f_date = format_date(date)
    month = f_date.split("-")
    m = month[1]
    return m

# returns the year from start_date_local key
def get_year(date):
    f_date = format_date(date)
    year = f_date.split("-")
    y = year[0]
    return y

# ----------------------------- 

# filters activities by criteria specified by user, function run from filtering page
def distance(dist, type, operand, activity_data, metrics, start_date, end_date):
    column_names = metrics
    df = pd.DataFrame(columns = column_names)
    # iterate through each page extracted from strava
    for page in activity_data:
        # iterate through each activity on page 
        for i in page:
            # checks to see if the type of activity matches the user's filter input
            if i["type"]== type or type == "--":
                # rounding so that output is to the nearest .1 km for equals operand
                if operand == "=":
                    round_dist = round(i["distance"], -2)
                else:
                    round_dist = i["distance"]
                # checks to see if the activity is within the user's specified timeframe(s)
                if validate_date(format_date(i["start_date_local"]),start_date, end_date):
                    if check_op(operand, round_dist, dist):
                        # generating one row in df (i.e. 1 activity)
                        metric_list = []
                        # iterate through metrics specified by user (e.g. name of activity)
                        for m in column_names:
                            if m == 'distance':
                                # shows swim in meters but all other activities in km
                                if type == 'Swim':
                                    km = str(i["distance"]) + " m"
                                else:
                                    km = str(round(i["distance"] / 1000, 2)) + " km"
                                
                                metric_list.append(km)
                            # changing units of moving time from seconds to min
                            elif m == 'moving_time':
                                time = str(round(i["moving_time"] / 60, 2)) + " min"
                                metric_list.append(time)
                            # show running in min/km, but all other sports in km/h
                            elif m == 'average_speed':
                                if i["type"] == "Run":
                                    if i["distance"] != 0:
                                        avg_speed = str(round((i["moving_time"] / i["distance"]) * (50/3), 2)) + " min/km"
                                else:
                                    avg_speed = str(round(i["average_speed"] * 3.6, 2)) + " km/h"
                                metric_list.append(avg_speed)  
                            # show date in YYYY-MM-DD format
                            elif m == 'start_date_local':
                                date = format_date(i[m])
                                metric_list.append(date) 
                            else:
                                metric_list.append(i[m])
                        # insert activity in first row of dataframe
                        # this displays the data from most recent, to least recent
                        df.loc[df.shape[0]] = metric_list
    df = df.rename({'start_date_local': 'Date'}, axis=1)
    return df

# ----------------------------- 

# trying a different way to filter data
# loads data into df, then filters to build graph
def graph_data(year_list):
    pio.templates.default = "plotly_white"
    # load activities from txt file
    with open('static/data/data.txt', 'rb') as f:
        activities = pickle.load(f)
    column_names = ["id","name", "type", "distance", "month", "year", "total_elevation_gain"]
    df = pd.DataFrame(columns = column_names)

    # iterate through each page of activities
    for page in activities:
        # iterate through each activity on page
        for i in page:
            metric_list = []
            for m in column_names:
                if m == "month":
                    month = get_month(i["start_date_local"])
                    metric_list.append(month)
                elif m =="year":
                    year = get_year(i["start_date_local"])
                    metric_list.append(year)
                elif m == "distance":
                    # save distance in km not m
                    dist = i["distance"] / 1000
                    metric_list.append(dist)
                else:
                    metric_list.append(i[m])
            df.loc[df.shape[0]] = metric_list

    df_t = df[["year", "month", "type", "distance"]]
    df_line = df_t[(df_t["type"] == "Run")]
    df_graph = pd.DataFrame(columns = ["year", "month", "distance"])
    # years that user specified (graphs.html)
    years = year_list
    months = ["01", "02", "03", "04", "05", "06", "07", "08", "09", "10", "11", "12"]
    for y in years:
        for mon in months:
            df_temp = df_line[(df_line["year"]==y) & (df_line["month"]==mon)]
            total = df_temp["distance"].sum()
            temp_list = [y, mon, total]
            df_graph.loc[df_graph.shape[0]] = temp_list


    template = "plotly_white"

    # fig = px.scatter(df,
    #                 x="month", y="distance", color="type",
    #                 log_x=True, size_max=60,
    #                 template=template, title="Strava Analysis")
    # fig.show()

    fig = px.scatter(df_graph, x="month", y="distance", color="year")
    fig.update_traces(marker=dict(size=20),
                  selector=dict(mode='markers'))
    # graphJSON = json.dumps(fig, cls=plotly.utils.PlotlyJSONEncoder)
    # fig.show()
    graph = plot(fig, output_type='div')
    return graph


# List of TODOs:
    # TODO: option to save output to csv for further analysis
    # TODO: 3 years in sport, compare years --> years in sport
        # per sport total distance, average speed per sport, total elevation gain per sport
        # each year, different colour, per month distance over 3 years (x axis is months, y axis is distance), per sport
        # histogram of number of 1km runs, 2km runs, etc...
    # TODO: change "--" to "all" when choosing operand and activity
    # TODO: filter based on elevation
    # TODO: fix running pace, decimal places, right now they are in 100 -> convert to 60 (divide by 60)
    # TODO: find new gif for loading page, and fix formatting to maintain size of login form
