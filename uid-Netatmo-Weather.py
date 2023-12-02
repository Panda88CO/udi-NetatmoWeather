#!/usr/bin/env python3

"""
Polyglot v3 node server
Copyright (C) 2023 Universal Devices

MIT License
"""


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
from  NetatmoWeather import NetatmoWeather
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
        self.nodeDefineDone = False
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

        self.Parameters = Custom(self.poly, 'customparams')
        self.Notices = Custom(self.poly, 'notices')

        self.poly.updateProfile()
        self.poly.ready()
        self.poly.addNode(self)

    def node_queue(self, data):
        self.n_queue.append(data['address'])

    def wait_for_node_done(self):
        while len(self.n_queue) == 0:
            time.sleep(0.1)
        self.n_queue.pop()



    def convert_temp_unit(self, tempStr):
        if tempStr.capitalize()[:1] == 'F':
            return(1)
        elif tempStr.capitalize()[:1] == 'K':
            return(0)
        

    def start(self):
        logging.debug('Executing start')
        self.accessToken = self.myNetatmo.getAccessToken()
        while self.accessToken is None:
            time.sleep(2)
            logging.debug('Waiting to retrieve access token')
            
        logging.debug('AccessToken = {}'.format(self.accessToken))
        res = self.myNetatmo.get_homes()
        logging.debug('retrieved data {}'.format(res))
        self.weather = NetatmoWeather()

        self.house_ids = self.weather.get_homes()
        if self.house_ids:
            self.node.setDriver('ST', 1, True, True)


        if 'TEMP_UNIT' in self.Parameters:
            self.temp_unit = self.convert_temp_unit(self.Parameters['TEMP_UNIT'])
        else:
            self.temp_unit = 0  
            self.Parameters['TEMP_UNIT'] = 'C'
            logging.debug('TEMP_UNIT: {}'.format(self.temp_unit ))

        self.addNodes()

    def addNodes(self):
        ''''''
        logging.info('Adding selected weather stations')

        self.enabled_list = []
        for house in self.house_ids:
            house_name = self.house_ids[house]['name']
            main_modules = self.weather.get_main_modules(house)
            for m_module in main_modules:
                mod_name = main_modules[m_module]
                node_name = house_name + '_'+ mod_name
                if node_name in self.Parameters:
                    if self.Parameters[node_name] == 1:
                        self.enabled_list.append(m_module)
                else:
                    self.Parameters[node_name] = 1 #enable by default
                    self.enabled_list.append(m_module)

        for nde in node_


    def configDoneHandler(self):
        # We use this to discover devices, or ask to authenticate if user has not already done so
        self.poly.Notices.clear()
        #self.myNetatmo.updateOauthConfig()
        #accessToken = self.myNetatmo._oAuthTokensRefresh()

        #if accessToken is None:
        #    logging.info('Access token is not yet available. Please authenticate.')
        #    polyglot.Notices['auth'] = 'Please initiate authentication'
        #    return
        
        res = self.myNetatmo.get_home_info()
        logging.debug('retrieved get_home_info data {}'.format(res))

        res = self.myNetatmo.get_weather_info()
        logging.debug('retrieved get_weather_info data {}'.format(res))

        res = self.myNetatmo.get_weather_info2()
        logging.debug('retrieved get_weather_info2 data2 {}'.format(res))

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
                    #self.blink.refresh_data()
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



