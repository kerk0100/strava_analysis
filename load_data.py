# Access refresh token and extracting data
from re import A
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
# import plotly
from plotly.offline import plot
# from plotly.graph_objs import Scatter
from pathlib import Path

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

csv.field_size_limit(sys.maxsize)

# loads activities from strava, save to txt file
# function run when user logs in
def load(id,secret,refresh):

    auth_url = "https://www.strava.com/oauth/token"
    activites_url = "https://www.strava.com/api/v3/athlete/activities/"
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
    with open('static/data/data.csv', 'w') as f:
        writer = csv.writer(f)
        writer.writerow(activity_data)
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
def get_data():
    # load activities from txt file
    with open('static/data/data.txt', 'rb') as f:
        activities = pickle.load(f)
    column_names = ["id","name", "type", "distance", "month", "year", "total_elevation_gain", "has_heartrate", "average_heartrate", "average_speed"]
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
                elif m == "average_heartrate":
                    if i["has_heartrate"] == False:
                        avg_hr = 0
                    else:
                        avg_hr = i["average_heartrate"]
                    metric_list.append(avg_hr)
                else:
                    metric_list.append(i[m])
            df.loc[df.shape[0]] = metric_list
    return df

# trying a different way to filter data
# loads data into df, then filters to build graph
def graph_data(year_list, a_type):
    pio.templates.default = "plotly_white"
    data_file = Path("static/data/graph_df.csv")
    if data_file.exists() == False:
        df = get_data()
        df.to_csv("static/data/graph_df.csv", index=False)
        months = ["01", "02", "03", "04", "05", "06", "07", "08", "09", "10", "11", "12"]
    else:
        df = pd.read_csv("static/data/graph_df.csv")
        months = ["1", "2", "3", "4", "5", "6", "7", "8", "9", "10", "11", "12"]

    df_t = df[["year", "month", "type", "distance"]]
    if a_type != "All":
        df_line = df_t[(df_t["type"] == a_type)]
    else:
        df_line = df_t
    df_line = df_line.astype({"year": str, "month": str})
    df_graph = pd.DataFrame(columns = ["year", "month", "distance"])
    # years that user specified (graphs.html)
    years = year_list
    for y in years:
        for mon in months:
            temp = df_line
            df_temp = temp.loc[df_line['year'] == y]
            df_temp = df_temp.loc[df_line['month'] == mon]
            total = df_temp["distance"].sum()
            temp_list = [y, mon, total]
            df_graph.loc[df_graph.shape[0]] = temp_list
    title = a_type + ": Distance per month, separated by year"
    fig = px.scatter(df_graph, x="month", y="distance", color="year", color_discrete_map= {'2018': 'black','2019': '#f7d0b5','2020': "#FC6100",'2021': '#243856','2022': '#909090'})
    
    fig.update_traces(marker=dict(size=20),
                  selector=dict(mode='markers'))
    fig.update_layout(title_text=title, title_x=0.5)

    hr_speed_graph = hr_graph(df, years, a_type)
    bar_fig = year_dist_graph(df_line, years, a_type)
    heart_rate_graph = plot(hr_speed_graph, output_type='div')
    bar_graph = plot(bar_fig, output_type='div')
    graph = plot(fig, output_type='div')
    return graph, bar_graph, heart_rate_graph


def year_dist_graph(df_line, years, a_type):
    df_graph = pd.DataFrame(columns = ["year", "distance"])
    for y in years:
        temp = df_line
        df_temp = temp.loc[df_line['year'] == y]
        total = df_temp["distance"].sum()
        temp_list = [y, total]
        df_graph.loc[df_graph.shape[0]] = temp_list
    title = a_type + ": Distance per year"
    fig = px.bar(df_graph, x="distance", y="year", orientation='h', color="year", color_discrete_map= {'2018': 'black','2019': '#f7d0b5','2020': "#FC6100",'2021': '#243856','2022': '#909090'})
    fig.update_layout(title_text=title, title_x=0.5)
    return fig

def hr_graph(df, years, a_type):
    pio.templates.default = "plotly_white"
    df_t = df[["year", "type", "average_heartrate", "average_speed"]]
    if a_type != "All":
        df_line = df_t[(df_t["type"] == a_type)]
        df_line = speed_units(df_line, a_type)
    else:
        df_line = df_t
    df_line = df_line.astype({"year": str})
    df_line = df_line[df_line['year'].isin(years)]
    # df_line = df_line[df_line.average_heartrate != 0]
    df_line = df_line[df_line.average_speed != 0]
    outliers = df_line.average_heartrate.quantile(0.32)
    df_line = df_line[df_line.average_heartrate > outliers]
    title = a_type + ": Average Speed to Average HR"
    fig = px.scatter(df_line, x="average_speed", y="average_heartrate", color="year", color_discrete_map= {'2018': 'black','2019': '#f7d0b5','2020': "#FC6100",'2021': '#243856','2022': '#909090'})
    fig.update_layout(xaxis_title="Avg Speed", yaxis_title="Avg HR", title_text=title, title_x=0.5)
    return fig
# TODO: fix! not accurately calculating pace... :(
def speed_units(df_line, a_type):
    if a_type == 'Run':
        df_line["average_speed"] = df_line["average_speed"].apply(lambda x: x * (50/3))
    return df_line

def find_activity(id_1, id_2, activity_data):
    activity_1 = 0
    activity_2 = 0
    for page in activity_data:
        # iterate through each activity on page 
        for i in page:
            # checks to see if the type of activity matches the user's filter input
            if i["id"]== id_1:
                activity_1 = i
            if i["id"] == id_2:
                activity_2 = i
    if activity_1 != 0 and activity_2 != 0:
        if activity_1["end_latlng"] == activity_2["end_latlng"]:
            result = "Correct"
            return result
        else:
            result = "Not Correct"
            return result
            
    else:
        result = "The id value(s) entered are not valid. Please try again. Use the filtering page to find the correct activity ID."
        return result    



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
    # TODO: change join to merge instead (better wording)
    # TODO: Avg pace per time of day --> graph
