import os
import time
import requests


def get_config(is_cloud=False):
    """Retrieve configuration from environment variables."""
    if not is_cloud:
        from dotenv import load_dotenv

        load_dotenv()

    return {
        "api_url": os.environ.get("API_URL"),
        "test_url": os.environ.get("TEST_URL"),
        "device_id": os.environ.get("DEVICE_ID"),
        "auth_key": os.environ.get("AUTH_KEY") or os.environ.get("SHELLY_AUTH"),
        "weerlive_key": os.environ.get("WEERLIVE_KEY"),
        "lat": os.environ.get("lat"),
        "lon": os.environ.get("lon"),
    }


def fetch_with_retries(url, method="GET", params=None, data=None, retries=3):
    """Generic fetch function with retries and exponential backoff."""
    for i in range(retries):
        try:
            if method == "GET":
                response = requests.get(url, params=params, timeout=10)
            else:
                response = requests.post(url, data=data, timeout=10)

            response.raise_for_status()
            return response
        except requests.RequestException as e:
            print(f"Error fetching data from {url}: {e}")
            if hasattr(e, "response") and e.response is not None:
                print(f"Raw response content: {e.response.text}")

        if i < retries - 1:
            time.sleep(2 ** (i + 1))

    return None


def check_device_status(config):
    """Check the current position of the sunscreen device via Shelly Cloud API."""
    params = {"id": config["device_id"], "auth_key": config["auth_key"]}
    response = fetch_with_retries(config["test_url"], params=params)

    if response:
        try:
            result = response.json()
            sunscreen_status = int(
                result["data"]["device_status"]["cover:0"]["current_pos"]
            )
            return sunscreen_status
        except (KeyError, ValueError, requests.exceptions.JSONDecodeError) as e:
            print(f"Error parsing device status: {e}")

    print("Failed to check device status, assuming 100 (open) for safety.")
    return 100


def check_wind(config):
    """Fetch and return wind data from Weerlive."""
    url = f"https://weerlive.nl/api/weerlive_api_v2.php?key={config['weerlive_key']}&locatie=Arnhem"
    response = fetch_with_retries(url)

    if response:
        try:
            data = response.json()
            wind_bft = data["liveweer"][0]["windbft"]
            wind_kmh = data["liveweer"][0]["windkmh"]
            print(f"Huidige windkracht bft: {wind_bft} ({wind_kmh} km/h)")
            return wind_bft, wind_kmh
        except (KeyError, requests.exceptions.JSONDecodeError) as e:
            print(f"Error parsing wind data: {e}")

    print("Failed to fetch wind data.")
    return 0, 0


def check_buienradar(config):
    """Fetch and parse rain forecast data from Buienradar API."""
    url = f"https://gadgets.buienradar.nl/data/raintext/?lat={config['lat']}&lon={config['lon']}"
    response = fetch_with_retries(url)

    if response:
        raindata = response.text
        rain_dict = {}
        for line in raindata.splitlines()[:5]:
            try:
                value, timecode = line.split("|")
                rain_dict[str(timecode.strip())] = int(value.strip())
            except ValueError as e:
                print(f"Error parsing rain data line '{line}': {e}")
                return None

        print(f"Rain forecast: {rain_dict}")
        return list(rain_dict.values())

    print("Failed to fetch rain data.")
    return None


def check_rain(rain_values):
    """Analyze rain forecast values to determine current and upcoming rain conditions."""
    if not rain_values or len(rain_values) < 5:
        print("Not enough rain data available.")
        return False

    # Check if it's currently raining (first 2 time periods)
    rain_now = any(value > 0 for value in rain_values[:2])

    # Check if it will rain soon (next 3 time periods)
    average_rain_soon = sum(rain_values[2:5]) / len(rain_values[2:5])
    rain_soon = average_rain_soon > 10

    print(f"Is it raining? [{rain_now}]. Will it rain soon? [{rain_soon}]")

    return rain_now or rain_soon


def close_sunscreen(config):
    """Send a request to close the sunscreen device via the Shelly Cloud API."""
    data = {
        "direction": "close",
        "id": config["device_id"],
        "auth_key": config["auth_key"],
    }
    time.sleep(2)  # At least one second between two calls

    response = fetch_with_retries(config["api_url"], method="POST", data=data)
    if response:
        try:
            result = response.json()
            if result.get("isok"):
                print("Sunscreen is closed!")
                return True
            else:
                print(f"Something went wrong while closing: {result}")
        except requests.exceptions.JSONDecodeError as e:
            print(f"Error parsing close response: {e}")

    print("Failed to close sunscreen.")
    return False


def check_and_close_sunscreen(is_cloud=False):
    """Main function to run the logic: check weather and close if needed."""
    config = get_config(is_cloud=is_cloud)

    # Check if we have essential config
    if not all(
        [
            config["api_url"],
            config["test_url"],
            config["device_id"],
            config["auth_key"],
            config["weerlive_key"],
            config["lat"],
            config["lon"],
        ]
    ):
        print("Missing required configuration values. Check environment variables.")
        return

    rain_values = check_buienradar(config)
    raining = check_rain(rain_values) if rain_values else False

    wind_bft, _ = check_wind(config)

    sunscreen_status = check_device_status(config)

    if (wind_bft > 4 or raining) and sunscreen_status > 0:
        print("Conditions met (wind > 4 or raining) AND sunscreen is open. Closing...")
        close_sunscreen(config)
    else:
        print("Conditions not met or sunscreen already closed. Taking no action.")
