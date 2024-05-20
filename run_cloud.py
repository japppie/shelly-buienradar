import modal
import statistics
import os
import time
from dotenv import load_dotenv

# Define the Modal function and app with required packages
app = modal.App('shelly_automation')

@app.function(
    secrets=[modal.Secret.from_name("shelly-secret")],
    schedule=modal.Cron("*/6 * * * *"),  # Every 6 minutes
    image=modal.Image.debian_slim().pip_install("requests", "python-dotenv")
)
def scheduled_task():
    import requests
    load_dotenv()
    
    # Shelly Cloud API configuration
    API_URL = os.environ["API_URL"]
    TEST_URL = os.environ["TEST_URL"]
    DEVICE_ID = os.environ["DEVICE_ID"]
    AUTH_KEY = os.environ["SHELLY_AUTH"]

    lat = os.environ["lat"]
    lon = os.environ["lon"]
    buienradar_url = f"https://gadgets.buienradar.nl/data/raintext/?lat={lat}&lon={lon}"

    def check_rain_and_control_blind():
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
        print(rain_dict)

        rain_values = list(rain_dict.values())
        median_value = statistics.median(rain_values[0:5])

        rain_now = rain_values[0] > 5
        rain_soon = median_value > 15
        print(f'Is it raining? {rain_now}')
        print(f'Will it rain soon? {rain_soon}')
        rain = rain_now or rain_soon

        params = {
            "id": DEVICE_ID,
            "auth_key": AUTH_KEY
        }
        try:
            response = requests.get(TEST_URL, params=params)
            response.raise_for_status()
            result = response.json()
            zonnescherm = float(result['data']['device_status']['cover:0']['current_pos'])
        except requests.RequestException as e:
            print(f"Error fetching device status: {e}")
            return

        if rain and zonnescherm > 0:
            data = {
                "direction": "close",
                "id": DEVICE_ID,
                "auth_key": AUTH_KEY
            }
            time.sleep(2)  # Er moet minimaal één seconde tussen twee calls zitten
            try:
                response = requests.post(API_URL, data=data)
                response.raise_for_status()
                result = response.json()
                if result.get("isok"):
                    print("Roller is closed!")
                else:
                    print(f"Something went wrong: {result}")
            except requests.RequestException as e:
                print(f"Error closing roller: {e}")

    check_rain_and_control_blind()

if __name__ == "__main__":
    with app.run():
        scheduled_task()