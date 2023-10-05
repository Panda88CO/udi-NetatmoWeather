
#!/usr/bin/env python3

### Your external service class
'''
Your external service class can be named anything you want, and the recommended location would be the lib folder.
It would look like this:

External service sample code
Copyright (C) 2023 Universal Devices

MIT License
'''
import requests
from udi_interface import LOGGER, Custom
from lib.oauth import OAuth

# Implements the API calls to your external service
# It inherits the OAuth class
class MyService(OAuth):
    yourApiEndpoint = 'https://api.netatmo.com'

    def __init__(self, polyglot):
        super().__init__(polyglot)

        self.poly = polyglot
        self.customParams = Custom(polyglot, 'customparams')
        LOGGER.info('External service connectivity initialized...')

    # The OAuth class needs to be hooked to these 3 handlers
    def customDataHandler(self, data):
        super()._customDataHandler(data)

    def customNsHandler(self, key, data):
        super()._customNsHandler(key, data)

    def oauthHandler(self, token):
        super()._oauthHandler(token)

    # Your service may need to access custom params as well...
    def customParamsHandler(self, data):
        self.customParams.load(data)
        # Example for a boolean field
        self.myParamBoolean = ('myParam' in self.customParams and self.customParams['myParam'].lower() == 'true')
        LOGGER.info(f"My param boolean: { self.myParamBoolean }")

    # Call your external service API
    def _callApi(self, method='GET', url=None, body=None):
        # When calling an API, get the access token (it will be refreshed if necessary)
        accessToken = self.getAccessToken()

        if accessToken is None:
            LOGGER.error('Access token is not available')
            return None

        if url is None:
            LOGGER.error('url is required')
            return None

        completeUrl = self.yourApiEndpoint + url

        headers = {
            'Authorization': f"Bearer { accessToken }"
        }

        if method in [ 'PATCH', 'POST'] and body is None:
            LOGGER.error(f"body is required when using { method } { completeUrl }")

        try:
            if method == 'GET':
                response = requests.get(completeUrl, headers=headers)
            elif method == 'DELETE':
                response = requests.delete(completeUrl, headers=headers)
            elif method == 'PATCH':
                response = requests.patch(completeUrl, headers=headers, json=body)
            elif method == 'POST':
                response = requests.post(completeUrl, headers=headers, json=body)
            elif method == 'PUT':
                response = requests.put(completeUrl, headers=headers)

            response.raise_for_status()
            try:
                return response.json()
            except requests.exceptions.JSONDecodeError:
                return response.text

        except requests.exceptions.HTTPError as error:
            LOGGER.error(f"Call { method } { completeUrl } failed: { error }")
            return None

    # Then implement your service specific APIs
    def getAllDevices(self):
        return self._callApi(url='/devices')

    def unsubscribe(self):
        return self._callApi(method='DELETE', url='/subscription')

    def getUserInfo(self):
        return self._callApi(url='/user/info')

### Main node server code


#!/usr/bin/env python3

"""
Polyglot v3 node server
Copyright (C) 2023 Universal Devices

MIT License
"""

import sys
import traceback
from udi_interface import LOGGER, Custom, Interface
from lib.myService import MyService
from nodes.controller import Controller


polyglot = None
myService = None
controller = None

def configDoneHandler():
    # We use this to discover devices, or ask to authenticate if user has not already done so
    polyglot.Notices.clear()

    accessToken = myService.getAccessToken()

    if accessToken is None:
        LOGGER.info('Access token is not yet available. Please authenticate.')
        polyglot.Notices['auth'] = 'Please initiate authentication'
        return

    controller.discoverDevices()

def oauthHandler(token):
    # When user just authorized, we need to store the tokens
    myService.oauthHandler(token)

    # Then proceed with device discovery
    configDoneHandler()


def addNodeDoneHandler(node):
    # We will automatically query the device after discovery
    controller.addNodeDoneHandler(node)

def stopHandler():
    # Set nodes offline
    for node in polyglot.nodes():
        if hasattr(node, 'setOffline'):
            node.setOffline()
    polyglot.stop()


if __name__ == "__main__":
    try:
        polyglot = Interface([])
        polyglot.start({ 'version': '1.0.0', 'requestId': True })

        # Show the help in PG3 UI under the node's Configuration option
        polyglot.setCustomParamsDoc()

        # Update the profile files
        polyglot.updateProfile()

        # Implements the API calls & Handles the oAuth authentication & token renewals
        myService = MyService(polyglot)

        # then you need to create the controller node
        controller = Controller(polyglot, 'controller', 'controller', 'Name', myService)

        # subscribe to the events we want
        # polyglot.subscribe(polyglot.POLL, pollHandler)
        polyglot.subscribe(polyglot.STOP, stopHandler)
        polyglot.subscribe(polyglot.CUSTOMDATA, myService.customDataHandler)
        polyglot.subscribe(polyglot.CUSTOMNS, myService.customNsHandler)
        polyglot.subscribe(polyglot.CUSTOMPARAMS, myService.customParamsHandler)
        polyglot.subscribe(polyglot.OAUTH, oauthHandler)
        polyglot.subscribe(polyglot.CONFIGDONE, configDoneHandler)
        polyglot.subscribe(polyglot.ADDNODEDONE, addNodeDoneHandler)

        # We can start receive events
        polyglot.ready()

        # Just sit and wait for events
        polyglot.runForever()

    except (KeyboardInterrupt, SystemExit):
        sys.exit(0)

    except Exception:
        LOGGER.error(f"Error starting Nodeserver: {traceback.format_exc()}")
        polyglot.stop()



