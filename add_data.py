import json
import os
import time
import requests
from pymongo import MongoClient
from datetime import datetime
from static.default_values import *

# run this file to refresh access token
# this page gets all user activities from strava API and saves them to mongoDB

# get default values
client_id = client_id_lk
client_secret = client_secret_lk
redirect_uri = redirect_uri_lk


def request_token(client_id, client_secret, code):
    response = requests.post(url='https://www.strava.com/oauth/token',
                             data={'client_id': client_id,
                                   'client_secret': client_secret,
                                   'code': code,
                                   'grant_type': 'authorization_code'})
    return response


def write_token(tokens):

    with open('strava_tokens.json', 'w') as outfile:
        json.dump(tokens, outfile)


def get_token():

    with open('strava_tokens.json', 'r') as tokens:
        data = json.load(tokens)

    return data


if not os.path.exists('./strava_tokens.json'):
    request_url = f'http://www.strava.com/oauth/authorize?client_id={client_id}' \
                  f'&response_type=code&redirect_uri={redirect_uri}' \
                  f'&approval_prompt=force' \
                  f'&scope=profile:read_all,activity:read_all'

    print('Click here:', request_url)
    print('Please authorize the app and copy&paste below the generated code!')
    print('P.S: you can find the code in the URL')
    code = input('Insert the code from the url: ')

    tokens = request_token(client_id, client_secret, code)

    #Save json response as a variable
    strava_tokens = tokens.json()
    # Save tokens to file
    write_token(strava_tokens)


data = get_token()

if data['expires_at'] < time.time():
    new_tokens = request_token(client_id, client_secret, code)
    # Update the file
    write_token(new_tokens)

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
        client.strava["activity_data"].update_one({'id': activity['id']}, {'$set': activity}, upsert=True)
        client.strava["activity_data"].update_many({}, {"$unset": {'start_date': 1, 'start_date_local': 1}}, upsert=True)


    request_page_num += 1