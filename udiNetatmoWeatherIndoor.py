#!/usr/bin/env python3

"""
Polyglot v3 node server
Copyright (C) 2023 Universal Devices

MIT License
"""


import time
import traceback
import re

try:
    import udi_interface
    logging = udi_interface.LOGGER
    Custom = udi_interface.Custom
except ImportError:
    import logging
    logging.basicConfig(level=logging.DEBUG)


#from nodes.controller import Controller
#from udi_interface import logging, Custom, Interface

class udiN_WeatherIndoor(udi_interface.Node):
    def __init__(self, polyglot, primary, address, name, NetatmoWeather, home, module):
        super().__init__(polyglot, primary, address, name)
        self.poly = polyglot
        self.weather= NetatmoWeather
        self.module = module
        self.home = home
        self.n_queue = []

        
        self.poly.subscribe(self.poly.START, self.start, self.address)
        self.poly.subscribe(self.poly.STOP, self.stop)

        self.poly.ready()
        self.poly.addNode(self)
        self.wait_for_node_done()
        self.node = self.poly.getNode(address)
        logging.info('Start {} Indoor Node'.format(self.name))  
        time.sleep(1)
        self.n_queue = []  
        self.nodeDefineDone = True

    
    
    def node_queue(self, data):
        self.n_queue.append(data['address'])

    def wait_for_node_done(self):
        while len(self.n_queue) == 0:
            time.sleep(0.1)
        self.n_queue.pop()

    def getValidName(self, name):
        name = bytes(name, 'utf-8').decode('utf-8','ignore')
        return re.sub(r"[^A-Za-z0-9_ ]", "", name)

    # remove all illegal characters from node address
    def getValidAddress(self, name):
        name = bytes(name, 'utf-8').decode('utf-8','ignore')
        return re.sub(r"[^A-Za-z0-9_]", "", name.lower()[:14])
    


    def convert_temp_unit(self, tempStr):
        if tempStr.capitalize()[:1] == 'F':
            return(1)
        elif tempStr.capitalize()[:1] == 'K':
            return(0)
        

    def start(self):
        logging.debug('Executing NetatmoWeatherIndoor start')
        


       
                



        


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
        for node in self.poly.nodes():
            if hasattr(node, 'setOffline'):
                node.setOffline()
        self.poly.stop()

