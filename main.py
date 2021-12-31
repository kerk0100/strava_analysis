# Access refresh token and extracting data
import requests
import urllib3
import json
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

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
# param = {'per_page': 200, 'page': 6}
# activity_data = requests.get(activites_url, headers=header, params=param).json()

i = 1

activity_data = []

while i < 7:
    param = {'per_page': 200, 'page': i}
    activity_data.append(requests.get(activites_url, headers=header, params=param).json())
    i = i + 1

# for page in activity_data: 
#     for i in page:
#         if i["type"]== 'Ride':
#             if i["distance"] > 40000:
#                 print(i["name"], i["distance"])

type = input("What activity would you like to view? ")
if type == 'Swim':
    dist = int(input("View " + str(type) +  " greater than what distance? "))
else:
    dist = int(input("View " + str(type) +  " greater than what distance? ")) * 1000

def distance(dist, type, activity_data):
    for page in activity_data:
        for i in page:
            if i["type"]== type:
                if i["distance"] > dist:
                    km = str(i["distance"] / 1000) + " km"
                    print(i["name"], km)

distance(dist, type, activity_data)
