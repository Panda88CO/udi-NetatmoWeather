# Configuring a node server to use OAUTH2 authentication with external service
'''
We now have support in both the interface module and PG3/PG3x for node servers to
use OAUTH2 authentication with external oauth servers.

To enable the OAUTH2 functionality, edit your store entry and select the "Enable OAuth2" checkbox. 

If oauth functionality is enabled you will now see an "Authenticate" button
in your node server's detail page on the dashboard.

In addition, you need to supply the oauth configuration under "Oauth Configuration". 
The JSON need the following information:

```
{
  "name": "name of service - this can be anything",
  "client_id": "The oAuth client ID",
  "client_secret": "The oAuth secret",
  "auth_endpoint": "The URL of the oAuth authorization endpoint",
  "token_endpoint": "The URL of the token endpoing",
  "cloudlink": true
}
```

This information will be read from the node server store database when the
node server starts and sent to your node server via the CUSTOMNS event using
the key 'oauth'.

When the "Authenticate" button is pressed, PG3 will call the auth_endpoint 
and redirect the browser to the auth service to validate the user's credentials.
A valid authorization code will be returned and used to request the access_token
data.  PG3 will send the information returned from that request to the 
node server using the OAUTH event.

The node sever can now use that info to make authenticated requests and
refresh the token if necessary. 

With the current implementation, PG3 always uses cloudlink to redirect the
request for an authentication code.

# Sample code

As a general approach, we recommend to develop a class to interface with your external service. 
Your external service class would extend a generic oAuth class which will take care of the lower level
oAuth handling for you.

### oauth.py

We recommend to save this file as is to the lib folder of your node server as oauth.py.
Your external service class will use this.
'''

#!/usr/bin/env python3
"""
oAuth interface
Copyright (C) 2023 Universal Devices

MIT License
"""
import json
import requests
from datetime import timedelta, datetime
from udi_interface import LOGGER, Custom

'''
OAuth is the class to manage oauth tokens to an external service
'''
class OAuth:
    def __init__(self, polyglot):
        # self.customData.token contains the oAuth tokens
        self.customData = Custom(polyglot, 'customdata')

        # This is the oauth configuration from the node server store
        self.oauthConfig = {}

    # customData contains current oAuth tokens: self.customData['tokens']
    def _customDataHandler(self, data):
        LOGGER.debug(f"Received customData: { json.dumps(data) }")
        self.customData.load(data)

    # Gives us the oAuth config from the store
    def _customNsHandler(self, key, data):
        # LOGGER.info('CustomNsHandler {}'.format(key))
        if key == 'oauth':
            LOGGER.info('CustomNsHandler oAuth: {}'.format(json.dumps(data)))

            self.oauthConfig = data

            if self.oauthConfig.get('auth_endpoint') is None:
                LOGGER.error('oAuth configuration is missing auth_endpoint')

            if self.oauthConfig.get('token_endpoint') is None:
                LOGGER.error('oAuth configuration is missing token_endpoint')

            if self.oauthConfig.get('client_id') is None:
                LOGGER.error('oAuth configuration is missing client_id')

            if self.oauthConfig.get('client_secret') is None:
                LOGGER.error('oAuth configuration is missing client_secret')

    # User proceeded through oAuth authentication.
    # The authorization_code has already been exchanged for access_token and refresh_token by PG3
    def _oauthHandler(self, token):
        LOGGER.info('Authentication completed')
        LOGGER.debug('Received oAuth tokens: {}'.format(json.dumps(token)))
        self._saveToken(token)

    def _saveToken(self, token):
        # Add the expiry key, so that we can later check if the tokens are due to be expired
        token['expiry'] = (datetime.now() + timedelta(seconds=token['expires_in'])).isoformat()

        # This updates our copy of customData, but also sends it to PG3 for storage
        self.customData['token'] = token

    def _oAuthTokensRefresh(self):
        LOGGER.info('Refreshing oAuth tokens')
        LOGGER.debug(f"Token before: { self.customData.token }")
        data = {
            'grant_type': 'refresh_token',
            'refresh_token': self.customData.token['refresh_token'],
            'client_id': self.oauthConfig['client_id'],
            'client_secret': self.oauthConfig['client_secret']
        }

        try:
            response = requests.post(self.oauthConfig['token_endpoint'], data=data)
            response.raise_for_status()
            token = response.json()
            LOGGER.info('Refreshing oAuth tokens successful')
            LOGGER.debug(f"Token refresh result [{ type(token) }]: { token }")
            self._saveToken(token)

        except requests.exceptions.HTTPError as error:
            LOGGER.error(f"Failed to refresh oAuth token: { error }")
            # NOTE: If refresh tokens fails, we keep the existing tokens available.

    # Gets the access token, and refresh if necessary
    # Should be called only after config is done
    def getAccessToken(self):
        LOGGER.info('Getting access token')
        token = self.customData['token']

        if token is not None:
            expiry = token.get('expiry')

            LOGGER.info(f"Token expiry is { expiry }")
            # If expired or expiring in less than 60 seconds, refresh
            if expiry is None or datetime.fromisoformat(expiry) - timedelta(seconds=60) < datetime.now():
                LOGGER.info('Refresh tokens expired. Initiating refresh.')
                self._oAuthTokensRefresh()
            else:
                LOGGER.info('Refresh tokens is still valid, no need to refresh')

            return self.customData.token.get('access_token')
        else:
            return None

