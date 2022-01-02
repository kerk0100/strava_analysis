# Access refresh token and extracting data
import requests
import urllib3
import json
import operator
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


def load():

    auth_url = "https://www.strava.com/oauth/token"
    activites_url = "https://www.strava.com/api/v3/athlete/activities"

    payload = {
        'client_id': "75915",
        'client_secret': 'b4643a48bc4f66df4dab4a90d700f2b880dca4bf',
        'refresh_token': 'e31b4e175850de6dce0393d64fd7c0e2023b6f54',
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

    return activity_data

# filters activities by distance specified by user
def distance(dist, type, operand, activity_data):
    activities = []
    
    ops = {
        ">": operator.gt,
        "<": operator.lt,
        "=": operator.eq
    }   
    op_func = ops[operand]
    for page in activity_data:
        for i in page:
            if i["type"]== type:
                if op_func(i["distance"], dist):
                # if i["distance"] > dist:
                    if type == 'Swim':
                        km = str(i["distance"]) + " m"
                    else:
                        km = str(i["distance"] / 1000) + " km"
                    result = i["name"] + " --> " + km
                    activities.append(result)
    return activities