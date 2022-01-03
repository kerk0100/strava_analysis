# Access refresh token and extracting data
import requests
import urllib3
import json
import operator
import csv
import sys
import pickle
import pandas as pd
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

csv.field_size_limit(sys.maxsize)

# loads activities from strava
def load(id,secret,refresh):

    auth_url = "https://www.strava.com/oauth/token"
    activites_url = "https://www.strava.com/api/v3/athlete/activities"
    # 'client_id': "75915",
    # 'client_secret': 'b4643a48bc4f66df4dab4a90d700f2b880dca4bf',
    # 'refresh_token': 'e31b4e175850de6dce0393d64fd7c0e2023b6f54',
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

    while i < 7:
        param = {'per_page': 200, 'page': i}
        activity_data.append(requests.get(activites_url, headers=header, params=param).json())
        i = i + 1
    with open('static/data/data.txt', 'wb') as f:
        pickle.dump(activity_data, f)
    print(activity_data)

    return activity_data

# filters activities by distance specified by user
def distance(dist, type, operand, activity_data, metrics):
    # activities = []
    column_names = metrics
    df = pd.DataFrame(columns = column_names)
    
    ops = {
        ">": operator.gt,
        "<": operator.lt,
        "=": operator.eq
    }
    if operand != "--":
        op_func = ops[operand]
    for page in activity_data:
        for i in page:
            # TODO: let user choose what metrics they want to see
            # TODO: option to save output to csv for further analysis
            # TODO: 3 years in sport, compare years
            # filters through types, or processes all if user didn't select a type
            if i["type"]== type or type == "--":
                # rounding so that output is to the nearest .1 km for equals operand
                if operand == "=":
                    round_dist = round(i["distance"], -2)
                else:
                    round_dist = i["distance"]
                if operand == "--" or op_func(round_dist, dist):
                    metric_list = []
                    for m in column_names:
                        if m == 'distance':
                            if type == 'Swim':
                                km = str(i["distance"]) + " m"
                            else:
                                km = str(round(i["distance"] / 1000, 2)) + " km"
                            
                            metric_list.append(km)
                        elif m == 'moving_time':
                            time = str(round(i["moving_time"] / 60, 2)) + " min"
                            metric_list.append(time)
                        elif m == 'average_speed':
                            if i["type"] == "Run":
                                avg_speed = str(round((i["moving_time"] / i["distance"]) * (50/3), 2)) + " min/km"
                            elif i["type"] == "Ride":
                                avg_speed = str(round(i["average_speed"] * 3.6, 2)) + " km/h"
                            else:
                                avg_speed = i["average_speed"]
                            metric_list.append(avg_speed)
                            
                        else:
                            metric_list.append(i[m])
                    df.loc[df.shape[0]] = metric_list
    return df

# uncomment to run output in terminal --> with command: python load_data.py
# client_id =  "75915"
# client_secret = "b4643a48bc4f66df4dab4a90d700f2b880dca4bf"
# refresh_token = "e31b4e175850de6dce0393d64fd7c0e2023b6f54"

# load(client_id, client_secret, refresh_token)