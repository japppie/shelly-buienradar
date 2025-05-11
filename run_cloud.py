import modal
import os
import time

# Define the Modal function and app with required packages
app = modal.App("shelly_automation")


@app.function(
    secrets=[modal.Secret.from_name("shelly-secret")],
    schedule=modal.Cron("*/6 7-23 * * *"),  # Every 6 minutes between 07:00 and 23:00
    image=modal.Image.debian_slim().pip_install("requests", "python-dotenv"),
)
def scheduled_task():
    import requests

    # Shelly Cloud API configuration
    API_URL = os.environ["API_URL"]
    TEST_URL = os.environ["TEST_URL"]
    DEVICE_ID = os.environ["DEVICE_ID"]
    AUTH_KEY = os.environ["SHELLY_AUTH"]
    WEERLIVE_KEY = os.environ["WEERLIVE_KEY"]
    buienradar_url = f"https://gadgets.buienradar.nl/data/raintext/?lat={os.environ['lat']}&lon={os.environ['lon']}"

    def _check_device_status():
        """Check the current position of the sunscreen device via Shelly Cloud API.

        Makes a GET request to the Shelly Cloud API to retrieve the current position
        of the sunscreen device. The position is returned as an integer value.

        Returns:
            int: The current position of the sunscreen (0-100).
                 Returns 100 if there's an error in the API call (safest default).

        Note:
            Position values:
            - 0: Fully closed
            - 100: Fully open
            - Values in between represent partial positions
        """
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
        url = f"https://weerlive.nl/api/weerlive_api_v2.php?key={WEERLIVE_KEY}&locatie=Arnhem"
        response = requests.get(url)
        response.raise_for_status()
        data = response.json()
        huidige_windbft = data["liveweer"][0]["windbft"]
        print(f"Huidige windkracht bft: {huidige_windbft}")
        return huidige_windbft

    def _check_buienradar():
        """Fetch and parse rain forecast data from Buienradar API.

        Makes a GET request to the Buienradar API to retrieve rain forecast data for the configured
        location. The data is parsed from a text format where each line contains a rain intensity
        value and a timestamp, separated by a pipe character.

        Returns:
            list: A list of integers representing rain intensity values for the next 5 time periods.
                  Returns None if there's an error fetching or parsing the data.

        Note:
            The rain intensity values are integers where:
            - 0: No rain
            - Higher values indicate more intense rain
            The function only processes the first 5 time periods from the forecast.
        """
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
        """Analyze rain forecast values to determine current and upcoming rain conditions.

        This function takes a list of rain intensity values and checks two conditions:
        1. If it's currently raining by checking the first two time periods
        2. If it will rain soon by calculating the average of the next three time periods

        Args:
            rain_values (list): A list of integers representing rain intensity values
                              for 5 consecutive time periods. Each value represents
                              the rain intensity where 0 means no rain and higher
                              values indicate more intense rain.

        Returns:
            bool: True if either:
                  - It is currently raining (any value > 0 in first 2 periods), or
                  - It will rain soon (average of next 3 periods > 10)
                 False otherwise.

        Note:
            The function assumes the input list contains exactly 5 values, where:
            - First 2 values represent current/very near future
            - Last 3 values represent upcoming forecast
        """
        # Check if it's currently raining (first 2 time periods)
        rain_now = any(value > 0 for value in rain_values[:2])

        # Check if it will rain soon (next 3 time periods)
        average_rain_soon = sum(rain_values[2:5]) / len(rain_values[2:5])
        rain_soon = average_rain_soon > 10

        print(f"Is it raining? {rain_now > 0}")
        print(f"Will it rain soon? {rain_soon}")

        return rain_now or rain_soon

    def _close_sunscreen():
        """Send a request to close the sunscreen device via the Shelly Cloud API.

        Makes a POST request to the Shelly Cloud API to close the sunscreen device.
        The request includes the device ID and authentication key. A 2-second delay
        is added before making the request to ensure proper timing between API calls.

        Returns:
            None

        Note:
            The function prints status messages to indicate whether the operation
            was successful or if any errors occurred during the process.
        """
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

    windbft = _check_windbft()
    rain_values = _check_buienradar()  # check buienradar
    raining = _check_rain(rain_values)  # check rain
    sunscreen_status = _check_device_status()  # check if sunscreen is open or closed

    if windbft > 4 and raining and sunscreen_status > 0:
        _close_sunscreen()


if __name__ == "__main__":
    with app.run():
        scheduled_task()
