
# Netatmo Weather Station NodeServer

This is the Netatmo Weather Station NodeServer for the [Universal Devices ISY994i / IoX](https://www.universal-devices.com/) [Polyglot interface](http://www.universal-devices.com/developers/polyglot/docs/) with [Polyglot V2](https://github.com/Einstein42/udi-polyglotv2).  
(c) 2021 Daniel Caldentey  
MIT license.

This node server is intended to interact with the [Netatmo Weather Station](https://www.netatmo.com/en-us/weather). It can track the status of all modules connected to a single Weather Station. You will need account access to your Netatmo via the Netatmo Developer API, and create an App on their developer site ([dev.netatmo.com](https://dev.netatmo.com)) to get a Client ID and a Client Secret.

Currently, only one Weather Station is supported per node server instance.

## Installation

1. Backup your ISY in case of problems.
2. Go to the Polyglot Store in the UI and install.
3. Add NodeServer in Polyglot Web.
   * After the install completes, Polyglot will reboot your ISY; you can watch the status in the main polyglot log.
4. Once your ISY is back up, open the Admin Console.
5. Configure the node server with your account credentials (`ClientID`, `ClientSecret`).

### Node Settings
The settings for this node are:

#### Short Poll
* Query Weather Station status. The default is 600 seconds (10 minutes) as Netatmo servers update online data approximately every 10 minutes.

#### Long Poll
* Not used (default: 1200 seconds).

#### Custom Parameters
* **ClientID**: Your Netatmo App Client ID from [dev.netatmo.com](https://dev.netatmo.com).
* **ClientSecret**: Your Netatmo App Client Secret from [dev.netatmo.com](https://dev.netatmo.com).

## Running Tests

An automated test suite using Python's standard `unittest` framework is included in the `tests/` directory:

```bash
python3 -m unittest discover -s tests -v
```

## Upgrading

Open the Polyglot web page, go to the nodeserver store and click "Update" for "Netatmo Weather Station".

Then restart the Netatmo Weather Station NodeServer by selecting it in the Polyglot dashboard and clicking **Control -> Restart**, then monitor the log to verify startup.

The Netatmo Weather Station NodeServer tracks version numbers and determines when a profile rebuild is necessary via `profile/version.txt` and `server.json`.

# Release Notes

- 1.0.0 06/21/2021
   - Initial version published to github
- 1.1.0 06/26/2021
   - Added "Query All" Command to NodeServer
- 1.3.0 10/23/2026
   - Standardized profile definitions to uppercase alphanumeric without special characters or reserved words
   - Fixed negative temperature rounding bug in round_half_up
   - Deterministic hardware-based addressing for indoor modules
   - Robust error and auth failure handling in shortPoll
   - Decoupled polyinterface with standalone fallback stub and comprehensive test suite
- 1.4.0 10/23/2026
   - Migrated to Polyglot v3 (udi_interface)
   - Updated driver dictionaries with human-readable names from profile NLS
   - Fixed executable mapping in server.json
