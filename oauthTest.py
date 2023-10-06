
#!/usr/bin/env python3
"""
Polyglot v3 node server
Copyright (C) 2023 Universal Devices

MIT License
"""

import sys
import traceback
try:
    import udi_interface
    logging = udi_interface.LOGGER
    Custom = udi_interface.Custom
except ImportError:
    import logging
    logging.basicConfig(level=logging.DEBUG)

from NetatmoOauth import NetatmoCloud
from nodes.controller import Controller
#from udi_interface import logging, Custom, Interface

polyglot = None
myNetatmo = None
controller = None

def configDoneHandler():
    # We use this to discover devices, or ask to authenticate if user has not already done so
    polyglot.Notices.clear()

    accessToken = NetatmoCloud.getAccessToken()

    if accessToken is None:
        logging.info('Access token is not yet available. Please authenticate.')
        polyglot.Notices['auth'] = 'Please initiate authentication'
        return

    controller.discoverDevices()

def oauthHandler(token):
    # When user just authorized, we need to store the tokens
    NetatmoCloud.oauthHandler(token)

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

id = 'controller'

drivers = [
        {'driver': 'ST', 'value':0, 'uom':2},
        ]

if __name__ == "__main__":
    try:
        logging.info ('starting')
        polyglot = Interface([])
        polyglot.start({ 'version': '1.0.0', 'requestId': True })

        # Show the help in PG3 UI under the node's Configuration option
        polyglot.setCustomParamsDoc()

        # Update the profile files
        polyglot.updateProfile()

        # Implements the API calls & Handles the oAuth authentication & token renewals
        myNetatmo= NetatmoCloud(polyglot)

        # then you need to create the controller node
        controller = Controller(polyglot, 'controller', 'controller', 'Netatmo', myNetatmo)

        # subscribe to the events we want
        # polyglot.subscribe(polyglot.POLL, pollHandler)
        polyglot.subscribe(polyglot.STOP, stopHandler)
        polyglot.subscribe(polyglot.CUSTOMDATA, myNetatmo.customDataHandler)
        polyglot.subscribe(polyglot.CUSTOMNS, myNetatmo.customNsHandler)
        polyglot.subscribe(polyglot.CUSTOMPARAMS, myNetatmo.customParamsHandler)
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
        logging.error(f"Error starting Nodeserver: {traceback.format_exc()}")
        polyglot.stop()



