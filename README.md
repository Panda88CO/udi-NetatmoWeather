
# Netatmo Weather Station NodeServer

Netatmo Weather Station NodeServer for PG3, PG3x
MIT license.

This node server integrated the Netatmo Weather Station. You will need account access to your Netatmo via the Netatmo Developer API, and create an App on their developer site to get a Client ID and a Client Secret. As part of the integration one will need to Autheticate when starting the node server the first time from the PG3(x) web interface (will switch to diffent website to allow authentication)


## Installation

1. Backup Your ISY in case of problems!
   * Really, do the backup, please
2. Go to the Polyglot Store in the UI and install.
3. Add NodeServer in Polyglot Web
   * After the install completes, Polyglot will reboot your ISY, you can watch the status in the main polyglot log.
4. Once your ISY is back up open the Admin Console.
5. Configure the node server with your account username and password.

### Node Settings
The settings for this node are:

#### Short Poll
   * Query Weather Station instantaneous data. The default is 5 minutes as the server only updates every 10 minutes.
#### Long Poll
   * Query Weather Station all data. Netatmo data is updated every 15 min or so.  The default is 30 minutes.

#### Client ID
   * Your Netatmo App Client ID

#### Client Secret
   * Your Netatmo App Client Secret
###

## Requirements

1. Polyglot V2 itself should be run on Raspian Stretch.
  To check your version, ```cat /etc/os-release``` and the first line should look like
  ```PRETTY_NAME="Raspbian GNU/Linux 9 (stretch)"```. It is possible to upgrade from Jessie to
  Stretch, but I would recommend just re-imaging the SD card.  Some helpful links:
   * https://www.raspberrypi.org/blog/raspbian-stretch/
   * https://linuxconfig.org/raspbian-gnu-linux-upgrade-from-jessie-to-raspbian-stretch-9
2. This has only been tested with ISY 5.0.13 so it is not guaranteed to work with any other version.

# Upgrading

Open the Polyglot web page, go to nodeserver store and click "Update" for "Netatmo-Weather Statipn".

For Polyglot 2.0.35, hit "Cancel" in the update window so the profile will not be updated and ISY rebooted.  The install procedure will properly handle this for you.  This will change with 2.0.36, for that version you will always say "No" and let the install procedure handle it for you as well.

Then restart the Netatmo Weather Station NodeServer by selecting it in the Polyglot dashboard and select Control -> Restart, then watch the log to make sure everything goes well.

The Netatmo Weather Station NodeServer keeps track of the version number and when a profile rebuild is necessary.  The profile/version.txt will contain the Netatmo Weather Station profile_version which is updated in server.json when the profile should be rebuilt.

# Release Notes

- 1.0.0 06/21/2021
   - Initial version published to github
- 1.1.0 06/26/2021
   - Added "Query All" Command to NodeServer
