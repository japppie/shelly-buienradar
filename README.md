# Shelly-Buienradar
Sluit zonnescherm als het regent of als het gaat regenen in de komende 20 minuten.
Voeg je lattitude en longitude coordinaten toe in je .env file
Voor automatische checks heb je een (gratis) Modal account nodig op modal.com, in Modal kan je jouw secrets toevoegen zodat je geen local .env meer nodig hebt.

# .env file example:
AUTH_KEY = <jouw authentication key van shelly>
API_URL = <jouw shelly api url, lijkt op: https://shelly-XX-eu.shelly.cloud/device/relay/roller/control>
TEST_URL = <jouw shelly test url, lijkt op: https://shelly-XX-eu.shelly.cloud/device/status>
DEVICE_ID = <jouw shelly device ID>
lat = jouw lattitude coordinaten, als een float met maximaal 2 decimalen (12.34)
lon = jouw longitude coordinaten, float met 2 decimalen (12.34)

p.s.: lat en lon coordinaten kan je in met Google Maps vinden.