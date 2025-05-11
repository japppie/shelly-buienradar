# Shelly-Buienradar
Sluit zonnescherm als het regent of als het gaat regenen in de komende 20 minuten én als de windkracht hoger is dan bft 4.
Voeg je lattitude en longitude coordinaten toe in je .env file
Voor automatische checks heb je een (gratis) Modal account nodig op modal.com, in Modal kan je jouw secrets toevoegen zodat je geen local .env meer nodig hebt.

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