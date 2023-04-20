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
import polyline
import folium
import statsmodels
from pymongo import MongoClient
from datetime import datetime
import math

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

csv.field_size_limit(sys.maxsize)

client = MongoClient("mongodb+srv://strava:stravaApp@cluster0.gkglgwv.mongodb.net/strava?retryWrites=true&w=majority")


# client.strava["activity_data"].update_one({'Device Name ID': "here"},
#                                                    {'$set': {'Legend Label': "here"}}, upsert=True)

# for i in requests.get("https://www.strava.com/api/v3/athlete/activities?access_token=630143d68935ae5f338ac65a206de35cd2d48493").json():
#     print(i)
# client["activity_data"].update(i, upsert=True)

# loads activities from strava, save to txt file
# function run when user logs in

def load(id, secret, refresh):
    auth_url = "https://www.strava.com/oauth/token"
    activites_url = "https://www.strava.com/api/v3/athlete/activities/"
    # https://www.strava.com/api/v3/athlete/activities?access_token=ba743fe5186a9da5b3f88cd334cd076730c00b6e
    payload = {
        'client_id': str(id),
        'client_secret': str(secret),
        'refresh_token': str(refresh),
        'grant_type': "refresh_token",
        'f': 'json'
    }

    res = requests.post(auth_url, data=payload, verify=False)
    # access_token = res.json()['access_token']
    access_token = '7cbcca320898f9c61d4127096ca4c5d1e737cb0e'
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
def distance(dist, type, operand, column_names, start_date, end_date):
    headers = [x.upper().replace("_", " ") for x in column_names]
    activity_table = pd.DataFrame(columns=headers)

    if operand != "--":
        cursor = client.strava["activity_data"].find({'type': type, 'distance': {operand: dist}})
        results = list(cursor)

        for result in results:
            activity = {}
            for header, column in zip(headers, column_names):
                activity[header] = result[str(column)]
            activity_table = activity_table.append(activity, ignore_index=True)
    activity_table['AVERAGE SPEED'] = activity_table['AVERAGE SPEED'].apply(lambda x: str(round(math.floor(1/(x*0.06)) +
                                                                                                float("0." + str(1/(x*0.06)).split('.')[1])*60/100, 2)) + ' min/km' if x > 0 else x)
    return activity_table


# -----------------------------
def get_data():
    # load activities from txt file
    with open('static/data/data.txt', 'rb') as f:
        activities = pickle.load(f)
    column_names = ["id", "name", "type", "distance", "month", "year", "total_elevation_gain", "has_heartrate",
                    "average_heartrate", "average_speed", "moving_time"]
    df = pd.DataFrame(columns=column_names)

    # iterate through each page of activities
    for page in activities:
        # iterate through each activity on page
        for i in page:
            metric_list = []
            for m in column_names:
                if m == "month":
                    month = get_month(i["start_date_local"])
                    metric_list.append(month)
                elif m == "year":
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


# loads data into df, then filters to build graph
def graph_data(years, a_type):
    years = [datetime.strptime(y, '%Y').year for y in years]
    pio.templates.default = "simple_white"
    distance_sums = list(client.strava['activity_data'].aggregate([{'$group': {'_id': {'month': {'$month': "$date"},
                                                                                       'year': {'$year': "$date"},
                                                                                       'type': '$type'},
                                                                               'distance': {'$sum': "$distance"}}}]))
    distance_sums = pd.DataFrame(distance_sums)
    distance_sums = pd.concat([distance_sums.drop(['_id'], axis=1), distance_sums['_id'].apply(pd.Series)], axis=1)
    distance_sums = distance_sums[distance_sums['type'] != 'Swim']
    distance_sums = distance_sums[distance_sums['year'].isin(years)]
    if a_type != "All":
        distance_sums = distance_sums[distance_sums['type'] == a_type]
        distance_sums = distance_sums.drop('type', axis=1)
    distance_sums['year'] = distance_sums['year'].astype('str')

    hr_data = list(client.strava['activity_data'].find({}, {'year': {'$year': "$date"}, "type": '$type',
                                                            "average_heartrate": '$average_heartrate',
                                                            "average_speed": '$average_speed',
                                                            "moving_time": '$moving_time',
                                                            "distance": '$distance'}))
    hr_data = pd.DataFrame(hr_data)
    hr_data = hr_data[hr_data['year'].isin(years)]
    hr_data['year'] = hr_data['year'].astype('str')
    if a_type != "All":
        hr_data = hr_data[hr_data['type'] == a_type]
        hr_data = hr_data.drop('type', axis=1)

    year_sums = list(client.strava['activity_data'].aggregate(
        [{'$group': {'_id': {'year': {'$year': "$date"}, 'type': '$type'}, 'distance': {'$sum': "$distance"}}}]))
    year_sums = pd.DataFrame(year_sums)
    year_sums = pd.concat([year_sums.drop(['_id'], axis=1), year_sums['_id'].apply(pd.Series)], axis=1)
    year_sums = year_sums[year_sums['year'].isin(years)]
    year_sums = year_sums[year_sums['type'] != 'Swim']
    if a_type != "All":
        year_sums = year_sums[year_sums['type'] == a_type]
    year_sums['year'] = year_sums['year'].astype('str')

    title = a_type + ": Distance per month, separated by year"
    fig = px.scatter(distance_sums, x="month", y="distance", color="year", color_discrete_map={'2018': '#000000',
                                                                                               '2019': '#f7d0b5',
                                                                                               '2020': "#642C20",
                                                                                               '2021': '#243856',
                                                                                               '2022': '#909090',
                                                                                               '2023': '#FC6100'})

    fig.update_traces(marker=dict(size=20),
                      selector=dict(mode='markers'))
    fig.update_layout(title_text=title, title_x=0.5)

    hr_speed_graph = hr_graph(hr_data, a_type)
    year_graph = year_dist_graph(year_sums, a_type)

    heart_rate_graph = plot(hr_speed_graph, output_type='div')
    bar_graph = plot(year_graph, output_type='div')
    graph = plot(fig, output_type='div')
    return graph, bar_graph, heart_rate_graph


def year_dist_graph(year_sums, a_type):
    title = a_type + ": Distance per year"
    fig = px.bar(year_sums, x="distance", y="year", orientation='h', color="year",
                 color_discrete_map={'2018': 'black', '2019': '#f7d0b5', '2020': "#642C20", '2021': '#243856',
                                     '2022': '#909090', '2023': '#FC6100'})
    fig.update_layout(title_text=title, title_x=0.5)
    return fig


def hr_graph(df, a_type):
    pio.templates.default = "plotly_white"
    df = df[df.average_speed != 0]
    outliers = df.average_heartrate.quantile(0.32)
    df = df[df.average_heartrate > outliers]
    title = a_type + ": Average Speed to Average HR"
    # trendline="ols"
    fig = px.scatter(df, x="average_speed", y="average_heartrate", color="year", trendline="ols",
                     color_discrete_map={'2018': 'black', '2019': '#f7d0b5', '2020': "#642C20", '2021': '#243856',
                                         '2022': '#909090', '2023': '#FC6100'})
    if a_type == 'Run':
        x_name = "Avg Speed: min/km"
    else:
        x_name = "Avg Speed: km/h"
    fig.update_layout(xaxis_title=x_name, yaxis_title="Avg HR", title_text=title, title_x=0.5)
    return fig


# TODO: fix! not accurately calculating pace... :(
def speed_units(df_line, a_type):
    if a_type == 'Run':
        df_line["average_speed"] = df_line["average_speed"].apply(speed_func)
    else:
        df_line["average_speed"] = df_line["average_speed"].apply(lambda x: x * (3.6))
    return df_line


def speed_func(x):
    if x != 0:
        return 1 / x * (50 / 3)
    else:
        return 0


def find_activity(id_1, id_2, activity_data):
    activity_1 = 0
    activity_2 = 0
    id_1 = str(id_1)
    id_2 = str(id_2)
    for page in activity_data:
        # iterate through each activity on page 
        for i in page:
            # checks to see if the type of activity matches the user's filter input
            if str(i["id"]) == id_1:
                activity_1 = i
            if str(i["id"]) == id_2:
                activity_2 = i
    if activity_1 != 0 and activity_2 != 0:
        # figure out what to do with activity ID, add in condition if end time and start time are 10 min apart & 111m apart
        # TODO: check if its a ride or a run, then add metrics accordingly
        if (abs(activity_1["end_latlng"][0] - activity_2["start_latlng"][0]) < 0.001) and \
                (abs(activity_1["end_latlng"][1] - activity_2["start_latlng"][1]) < 0.001) and \
                (activity_1["type"] == activity_2["type"]):
            coef_time_1 = activity_1['elapsed_time'] / (activity_1['elapsed_time'] + activity_2['elapsed_time'])
            coef_time_2 = activity_2['elapsed_time'] / (activity_1['elapsed_time'] + activity_2['elapsed_time'])

            print(coef_time_1)
            print(coef_time_2)
            activity_1['name'] = activity_1["name"] + " + " + activity_2["name"]
            activity_1['athlete_count'] = max(activity_1['athlete_count'], activity_2['athlete_count'])
            metrics = ['distance', 'moving_time', 'elapsed_time', 'total_elevation_gain', 'achievement_count',
                       'kudos_count', 'comment_count', 'photo_count', 'pr_count', 'total_photo_count']
            for m in metrics:
                activity_1[m] += activity_2[m]

            avg_metrics = ['average_speed', 'max_speed', 'average_heartrate', 'average_cadence', 'suffer_score']
            for am in avg_metrics:
                try:
                    if am == 'average_heartrate':
                        if activity_1['has_heartrate'] == False and activity_2['has_heartrate'] == False:
                            continue
                        if activity_1['has_heartrate'] == False:
                            activity_1['has_heartrate'] = activity_2['has_heartrate']
                        if activity_2['has_heartrate'] == False:
                            activity_1['has_heartrate'] = activity_1['has_heartrate']
                        else:
                            activity_1[am] = coef_time_1 * activity_1[am] + coef_time_2 * activity_2[am]
                        activity_1['max_heartrate'] = max(activity_1['max_heartrate'], activity_2['max_heartrate'])
                    else:
                        activity_1[am] = coef_time_1 * activity_1[am] + coef_time_2 * activity_2[am]
                except:
                    continue
            if activity_1['elev_high']:
                activity_1['elev_high'] = max(activity_1['elev_high'], activity_2['elev_high'])
            if activity_1['elev_low']:
                activity_1['elev_low'] = min(activity_1['elev_low'], activity_2['elev_low'])

            map_1 = activity_1['map']['summary_polyline']
            map_2 = activity_2['map']['summary_polyline']
            poly_decode_1 = polyline.decode(map_1)
            poly_decode_2 = polyline.decode(map_2)
            poly_decode = poly_decode_1 + poly_decode_2
            poly_encode = polyline.encode(poly_decode)
            activity_1['map']['summary_polyline'] = poly_encode
            sum_lat = 0
            sum_lon = 0
            max_lon = 0
            min_lon = 100000
            count = 0
            for l in poly_decode:
                count += 1
                if l[0] > max_lon:
                    max_lon = l[0]
                if l[0] < min_lon:
                    min_lon = l[0]
                sum_lat += l[0]
                sum_lon += l[1]
            avg_lat = sum_lat / count
            avg_lon = sum_lon / count
            m = folium.Map(location=[avg_lat, avg_lon], zoom_start=11)

            loc = poly_decode

            folium.PolyLine(loc,
                            color='#FC6100',
                            weight=5,
                            opacity=1).add_to(m)
            folium.TileLayer('Stamen Terrain').add_to(m)

            act_list = [activity_1['name'], 'Distance: ' + str(activity_1['distance'] / 1000) + ' km',
                        'Elev. gain: ' + str(activity_1['total_elevation_gain']) + ' m',
                        'Avg HR: ' + str(round(activity_1['average_heartrate'], 2)) + ' bpm']

            # {'id': 6468508817, 'upload_id': 6877595631, 'upload_id_str': '6877595631', 'external_id': '61d37417b30fe6795f7ad43e.fit'}
            # {'id': 6468509184, 'upload_id': 6877596021, 'upload_id_str': '6877596021', 'external_id': '61d3741dff187d526c7a936d.fit'}
            return m, act_list
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
    # histogram of number of 1km runs, 2km runs, etc...
    # TODO: change "--" to "all" when choosing operand and activity
    # TODO: filter based on elevation
    # TODO: fix running pace, decimal places, right now they are in 100 -> convert to 60 (divide by 60)
    # TODO: find new gif for loading page, and fix formatting to maintain size of login form
    # TODO: change join to merge instead (better wording)
    # TODO: Avg pace per time of day --> graph
    # TODO: map of world with photos taken at each location for the activities
    # TODO: Add regression line to avg speed/HR graph
    # TODO: add line between dots in monthly distance 
    # TODO: -- isolate out elevation
    # TODO: isolate environment - compare metrics with matched rides/activities
    # TODO: add that if the activities are reloaded in, the graph_data.csv file is deleted so it can be regenerated
