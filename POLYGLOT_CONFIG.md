## Netatmo WeatherStation NodeServer Configuration

#### Configuration Parameters:

- key: `shortPoll`, value: Refresh rate in seconds (default: 600). Keep in mind that Netatmo only updates its online information every 10 minutes.
- key: `longPoll`, value: Not used (default: 1200).

#### Custom Configuration Parameters:

- key: `ClientID`, value: Client ID from Netatmo developer app at dev.netatmo.com (required)
- key: `ClientSecret`, value: Client Secret from Netatmo developer app at dev.netatmo.com (required)
