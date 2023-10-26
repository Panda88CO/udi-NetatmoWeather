#!/usr/bin/env python3

"""
Polyglot v3 node server
Copyright (C) 2023 Universal Devices

MIT License
"""

import sys
import time
import traceback
try:
    import udi_interface
    logging = udi_interface.LOGGER
    Custom = udi_interface.Custom
except ImportError:
    import logging
    logging.basicConfig(level=logging.DEBUG)

from NetatmoOauth import NetatmoCloud
#from nodes.controller import Controller
#from udi_interface import logging, Custom, Interface

polyglot = None
myNetatmo = None
controller = None
class NetatmoController(udi_interface.Node):
    def __init__(self, polyglot, primary, address, name, myNetatmo):
        super(NetatmoController, self).__init__(polyglot, primary, address, name)
        logging.setLevel(10)
        self.poly = polyglot
        self.accessToken = None
        self.myNetatmo = myNetatmo
        self.poly.subscribe(polyglot.STOP, self.stopHandler)
        self.poly.subscribe(self.poly.START, self.start, address)
        self.poly.subscribe(polyglot.CUSTOMDATA, self.myNetatmo.customDataHandler)
        self.poly.subscribe(polyglot.CUSTOMNS, self.myNetatmo.customNsHandler)
        self.poly.subscribe(polyglot.CUSTOMPARAMS, self.myNetatmo.customParamsHandler)
        self.poly.subscribe(polyglot.OAUTH, self.oauthHandler)
        self.poly.subscribe(polyglot.CONFIGDONE, self.configDoneHandler)
        self.poly.subscribe(polyglot.ADDNODEDONE, self.addNodeDoneHandler)
        self.poly.subscribe(self.poly.POLL, self.systemPoll)

        self.poly.updateProfile()
        self.poly.ready()
        self.poly.addNode(self)


    def start(self):
        logging.debug('Executing start')
        self.accessToken = self.myNetatmo.getAccessToken()
        while self.accessToken is None:
            time.sleep(2)
            logging.debug('Waiting to retrieve access token')
            
        logging.debug('AccessToken = {}'.format(self.accessToken))
        res = self.myNetatmo.get_home_info()
        logging.debug('retrieved data {}'.format(res))

    def configDoneHandler(self):
        # We use this to discover devices, or ask to authenticate if user has not already done so
        self.poly.Notices.clear()
        self.myNetatmo.updateOauthConfig()
        accessToken = self.myNetatmo._refreshAccessToken()

        if accessToken is None:
            logging.info('Access token is not yet available. Please authenticate.')
            polyglot.Notices['auth'] = 'Please initiate authentication'
            return
        
        res = self.myNetatmo.get_home_info()
        logging.debug('retrieved data {}'.format(res))

        res = self.myNetatmo.get_weather_info()
        logging.debug('retrieved data {}'.format(res))


        #self.poly.discoverDevices()

    def oauthHandler(self, token):
        # When user just authorized, we need to store the tokens
        logging.debug('oauthHandler starting')
        self.myNetatmo.oauthHandler(token)
        accessToken = self.myNetatmo.getAccessToken()
        logging.debug('AccessToekn obtained {}'.format(accessToken))

        # Then proceed with device discovery
        self.configDoneHandler()


    def addNodeDoneHandler(self, node):
        # We will automatically query the device after discovery
        self.poly.addNodeDoneHandler(node)
        self.nodeDefineDone = True

    def systemPoll (self, polltype):
        if self.nodeDefineDone:
            logging.info('System Poll executing: {}'.format(polltype))

            if 'longPoll' in polltype:
                #Keep token current
                #self.node.setDriver('GV0', self.temp_unit, True, True)
                try:
                    self.myNetatmo.refresh_token()
                    self.blink.refresh_data()
                    nodes = self.poly.getNodes()
                    for nde in nodes:
                        if nde != 'setup':   # but not the setup node
                            logging.debug('updating node {} data'.format(nde))
                            nodes[nde].updateISYdrivers()
                         
                except Exception as e:
                    logging.debug('Exeption occcured : {}'.format(e))
   
                
            if 'shortPoll' in polltype:
                self.heartbeat()
                self.myNetatmo.refresh_token()
        else:
            logging.info('System Poll - Waiting for all nodes to be added')


    def stopHandler(self):
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
        logging.info('Starting Netatmo Controller')
        polyglot = udi_interface.Interface([])
        #polyglot.start('0.2.31')

        polyglot.start({ 'version': '0.0.2', 'requestId': True })

        # Show the help in PG3 UI under the node's Configuration option
        polyglot.setCustomParamsDoc()

        # Update the profile files
        polyglot.updateProfile()

        # Implements the API calls & Handles the oAuth authentication & token renewals
        myNetatmo = NetatmoCloud(polyglot)

        # then you need to create the controller node
        NetatmoController(polyglot, 'controller', 'controller', 'Netatmo', myNetatmo)

        # subscribe to the events we want
        # polyglot.subscribe(polyglot.POLL, pollHandler)

        # We can start receive events
        polyglot.ready()

        # Just sit and wait for events
        polyglot.runForever()

    except (KeyboardInterrupt, SystemExit):
        sys.exit(0)

    except Exception:
        logging.error(f"Error starting Nodeserver: {traceback.format_exc()}")
        polyglot.stop()



