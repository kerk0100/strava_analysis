import json

import requests
from pymongo import MongoClient
from datetime import datetime

# this page gets all user activities from strava API and saves them to mongoDB
# access token expires and will need to be refreshed (see get_data.py)

request_page_num = 1

activites_url = "https://www.strava.com/api/v3/athlete/activities/"
with open('strava_tokens.json', 'r') as tokens:
    data = json.load(tokens)
access_token = data['access_token']
header = {'Authorization': 'Bearer ' + access_token}

# connect to mongoDB
client = MongoClient("mongodb+srv://strava:stravaApp@cluster0.gkglgwv.mongodb.net/strava?retryWrites=true&w=majority")

while True:
    param = {'per_page': 200, 'page': request_page_num}
    # initial request, where we request the first page of activities
    activities = requests.get(activites_url, headers=header, params=param).json()
    print(request_page_num)

    if len(activities) == 0:
        print("DB updated.")
        break

    # save activity data to mongoDB
    for i in activities:
        activity = i
        if activity['type'] != "Swim":
            activity['distance'] = int(activity['distance'])/1000
        activity["date"] = datetime.strptime(activity.pop("start_date_local"), '%Y-%m-%dT%H:%M:%SZ')
        # dt = datetime.strptime(activity['date'], '%Y-%m-%dT%H:%M:%SZ')
        # activity["date"] = str(dt.year) + "-" + str(dt.month) + "-" + str(dt.day)
        # activity["month"] = dt.month
        # activity["year"] = dt.year
        # activity["day"] = dt.day
        client.strava["activity_data"].update_one({'id': activity['id']}, {'$set': activity}, upsert=True)
        client.strava["activity_data"].update_many({}, {"$unset": {'start_date': 1, 'start_date_local': 1}}, upsert=True)


    request_page_num += 1