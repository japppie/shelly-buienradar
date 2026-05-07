# Shelly-Buienradar

Automate your Shelly sunscreen device based on real-time weather data!

This project automatically closes your sunscreen if it rains (or is about to rain in the next 20 minutes) and/or if the wind force exceeds 4 Bft. It leverages the Shelly Cloud API, Buienradar, and Weerlive to make intelligent, localized decisions.

## What it does

- **Checks Wind:** Uses the [Weerlive API](https://weerlive.nl/) to check the current wind force.
- **Checks Rain:** Uses [Buienradar](https://www.buienradar.nl/) rain forecast to detect current or upcoming rain.
- **Checks Sunscreen Status:** Uses the [Shelly Cloud API](https://control.shelly.cloud/) to see if the sunscreen is currently open.
- **Takes Action:** If the sunscreen is open and bad weather is detected (wind > 4 Bft or raining), it sends a command to safely close the sunscreen.

## Prerequisites

- A Shelly device connected to Shelly Cloud.
- A free [Weerlive API key](https://weerlive.nl/api/toegang/account.php).
- A free [Modal account](https://modal.com/) (optional, for cloud deployment).

## Setup & Installation

This project uses [`uv`](https://github.com/astral-sh/uv) as its package manager.

1. **Install uv:**
   Follow the instructions on the [uv documentation](https://docs.astral.sh/uv/getting-started/installation/).
2. **Install dependencies:**
   ```bash
   uv sync
   ```
3. **Configure Environment Variables:**
   Create a `.env` file in the root directory and add your credentials:
   ```ini
   # Shelly Cloud Configuration
   AUTH_KEY=my_auth_key
   API_URL=https://shelly-XX-eu.shelly.cloud/device/relay/roller/control
   TEST_URL=https://shelly-XX-eu.shelly.cloud/device/status
   DEVICE_ID=my_device_id

   # Weather APIs Configuration
   WEERLIVE_KEY=my_weerlive_key
   lat=52.3676
   lon=4.9041
   ```

### Finding your Shelly Credentials:
- **API_URL and AUTH_KEY:** `https://control.shelly.cloud/` > Settings > User Settings > Authorization Cloud Key
- **Device ID:** `https://control.shelly.cloud/` > My Dashboard > My Device > Settings > Device Information

## Running the Application

### Local Testing

To test the automation script locally on your machine:

```bash
uv run python run_local.py
```

### Cloud Deployment (Modal)

You can deploy this project to [Modal](https://modal.com/) to run it automatically on a schedule (e.g., every 6 minutes between 07:00 and 23:00).

1. First, set up your Modal token:
   ```bash
   uv run modal token new
   ```
2. Add your environment variables as a Secret in Modal named `shelly-secret`. You can do this via the Modal web interface.
3. Deploy the application:
   ```bash
   uv run modal deploy run_cloud.py
   ```

## Development

- **Linting & Formatting:** This project uses Ruff for fast linting and formatting.
  ```bash
  uv run ruff check .
  uv run ruff format .
  ```
- **Testing:** 100% test coverage using pytest.
  ```bash
  uv run pytest --cov=src/shelly_buienradar tests/
  ```
