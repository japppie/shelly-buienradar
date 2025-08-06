# Shelly-Buienradar
Sluit zonnescherm als het regent of als het gaat regenen in de komende 20 minuten én als de windkracht hoger is dan bft 4.
Voeg je lattitude en longitude coordinaten toe in je .env file
Voor automatische checks heb je een (gratis) Modal account nodig op modal.com, in Modal kan je jouw secrets toevoegen zodat je geen local .env meer nodig hebt.

# Local Development Setup

1. **Install `uv`**:
   Follow the official installation instructions for `uv`: https://docs.astral.sh/uv/getting-started/installation/

2. **Create a virtual environment**:
   ```bash
   uv venv
   ```

3. **Activate the virtual environment**:
   ```bash
   source .venv/bin/activate
   ```

4. **Install dependencies**:
   ```bash
   uv pip install -e '.[dev]'
   ```
   This will install the project in editable mode with the development dependencies.

   The `requirements.txt` file is generated from `pyproject.toml` for use in the Modal environment. To regenerate it, run:
   ```bash
   uv pip compile pyproject.toml --all-extras -o requirements.txt
   ```

# .env file example:
```
AUTH_KEY=my_auth_key
API_URL=https://shelly-XX-eu.shelly.cloud/device/relay/roller/control 
TEST_URL=https://shelly-XX-eu.shelly.cloud/device/status
WEERLIVE_KEY=my_weerlive_key
DEVICE_ID=my_device_id
lat=12.34
lon=56.78
```


# Shelly API_URL en AUTH_KEY vind je op:
```
htps://control.shelly.cloud/ > settings > user settings > Authorization cloud key
```
Shelly device id vind je op:
```
https://control.shelly.cloud/ > My Dashboard > My Device > Settings > Device Information
```
Een API key voor Weerlive kan je gratis aanvragen op: https://weerlive.nl/api/toegang/account.php
lat en lon coordinaten kan je met Google Maps vinden.