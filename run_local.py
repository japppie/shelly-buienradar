import requests
import statistics
import json
import time

from dotenv import load_dotenv
import os

load_dotenv()
# Shelly Cloud API configuration
API_URL = os.getenv("API_URL")
TEST_URL = os.getenv("TEST_URL")
DEVICE_ID = os.getenv("DEVICE_ID")
AUTH_KEY = os.getenv("AUTH_KEY")
lat = float(os.getenv("lat"))
lon = float(os.getenv("lon"))

url = f"https://gadgets.buienradar.nl/data/raintext/?lat={lat}&lon={lon}"
response = requests.get(url)
raindata = response.text

rain_dict = {}
for line in raindata.splitlines()[:5]:
    value, timecode = line.split("|")
    rain_dict[str(timecode.strip())] = int(value.strip())

rain_values = list(rain_dict.values())
median_value = statistics.median(rain_values[1:5])

if rain_values[0] > 5:
    rain = True
elif median_value > 15:
    rain = True
else:
    rain = False

def check_device_status():
    params = {
        "id": DEVICE_ID,
        "auth_key": AUTH_KEY
    }
    response = requests.get(TEST_URL, params=params)
    if response.status_code == 200:
        result = response.json()
        # print(f"Device status: {result}")
        zonnescherm = float(result['data']['device_status']['cover:0']['current_pos'])
        return zonnescherm
    else:
        print(f"Something went wrong: {response.status_code} - {response.text}")

def send_roller_command(direction):
    data = {
        "direction": direction,
        "id": DEVICE_ID,
        "auth_key": AUTH_KEY
    }
    response = requests.post(API_URL, data=data)
    if response.status_code == 200:
        result = response.json()
        if result.get("isok"):
            print(f"Roller is {direction}ed!")
        else:
            print(f"Something went wrong: {result}")
    else:
        print(f"Something went wrong: {response.status_code} - {response.text}")

zonnescherm = check_device_status()
print(f'Zonnescherm staat op {zonnescherm}%')
time.sleep(2)

if rain and zonnescherm > 0:
    send_roller_command("close")