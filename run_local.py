import requests
import time
from dotenv import load_dotenv
import os

load_dotenv()
# Shelly Cloud API configuration
API_URL = os.getenv("API_URL")
TEST_URL = os.getenv("TEST_URL")
DEVICE_ID = os.getenv("DEVICE_ID")
AUTH_KEY = os.getenv("AUTH_KEY")
WEERLIVE_KEY = os.getenv("WEERLIVE_KEY")
lat = float(os.getenv("lat"))
lon = float(os.getenv("lon"))

buienradar_url = f"https://gadgets.buienradar.nl/data/raintext/?lat={os.environ['lat']}&lon={os.environ['lon']}"


def _check_device_status():
    params = {"id": DEVICE_ID, "auth_key": AUTH_KEY}
    response = requests.get(TEST_URL, params=params)
    if response.status_code == 200:
        result = response.json()
        # print(f"Device status: {result}")
        sunscreen_status = int(
            result["data"]["device_status"]["cover:0"]["current_pos"]
        )
        return sunscreen_status
    else:
        print(f"Something went wrong: {response.status_code} - {response.text}")
        return 100  # assume sunscreen is opened when there is an error (to be safe)


def _check_windbft():
    url = (
        f"https://weerlive.nl/api/weerlive_api_v2.php?key={WEERLIVE_KEY}&locatie=Arnhem"
    )
    response = requests.get(url)
    response.raise_for_status()
    data = response.json()
    huidige_windbft = data["liveweer"][0]["windbft"]
    print(f"Huidige windkracht bft: {huidige_windbft}")
    return huidige_windbft


def _check_buienradar():
    try:
        response = requests.get(buienradar_url)
        response.raise_for_status()
        raindata = response.text
    except requests.RequestException as e:
        print(f"Error fetching rain data: {e}")
        return

    rain_dict = {}
    for line in raindata.splitlines()[:5]:
        try:
            value, timecode = line.split("|")
            rain_dict[str(timecode.strip())] = int(value.strip())
        except ValueError as e:
            print(f"Error parsing rain data line: {line} - {e}")
            return
    print(f"\n\n{rain_dict}")

    return list(rain_dict.values())


def _check_rain(rain_values):
    # Check if it's currently raining (first 2 time periods)
    rain_now = any(value > 0 for value in rain_values[:2])

    # Check if it will rain soon (next 3 time periods)
    average_rain_soon = sum(rain_values[2:5]) / len(rain_values[2:5])
    rain_soon = average_rain_soon > 10

    print(f"Is it raining? {rain_now > 0}")
    print(f"Will it rain soon? {rain_soon}")

    return rain_now or rain_soon


def _close_sunscreen():
    data = {"direction": "close", "id": DEVICE_ID, "auth_key": AUTH_KEY}
    time.sleep(2)  # Er moet minimaal één seconde tussen twee calls zitten
    try:
        response = requests.post(API_URL, data=data)
        response.raise_for_status()
        result = response.json()
        if result.get("isok"):
            print("Sunscreen is closed!")
        else:
            print(f"Something went wrong: {result}")
    except requests.RequestException as e:
        print(f"Error closing sunscreen: {e}")


# rain_values = _check_buienradar()  # check buienradar
# raining = _check_rain(rain_values)  # check rain
# sunscreen_status = _check_device_status()  # check if sunscreen is open or closed

# if raining and sunscreen_status > 0:
#     _close_sunscreen()

windbft = _check_windbft()
print(windbft)
