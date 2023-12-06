#!/usr/bin/env python3

"""
Polyglot v3 node server
Copyright (C) 2023 Universal Devices

MIT License
"""


import time
import traceback
import re
import sys

try:
    import udi_interface
    logging = udi_interface.LOGGER
    Custom = udi_interface.Custom
except ImportError:
    import logging
    logging.basicConfig(level=logging.DEBUG)

#from NetatmoOauth import NetatmoCloud
from NetatmoWeather import NetatmoWeather
from  udiNetatmoWeatherMain import udiNetatmoWeatherMain
#from nodes.controller import Controller
#from udi_interface import logging, Custom, Interface
version = '0.0.2'

#polyglot = None
#myNetatmo = None
#controller = None


class NetatmoController(udi_interface.Node):
    def __init__(self, polyglot, primary, address, name, myNetatmo):
        super(NetatmoController, self).__init__(polyglot, primary, address, name)
        logging.setLevel(10)
        self.poly = polyglot
        self.accessToken = None
        self.nodeDefineDone = False
        self.myNetatmo = myNetatmo
        self.name = name
        self.primary = primary
        self.address = address

        self.Parameters = Custom(self.poly, 'customparams')
        self.Notices = Custom(self.poly, 'notices')
        self.n_queue = []

        self.poly.subscribe(self.poly.STOP, self.stopHandler)
        self.poly.subscribe(self.poly.START, self.start, address)
        self.poly.subscribe(self.poly.CUSTOMDATA, self.myNetatmo.customDataHandler)
        self.poly.subscribe(self.poly.CUSTOMNS, self.myNetatmo.customNsHandler)
        self.poly.subscribe(self.poly.CUSTOMPARAMS, self.myNetatmo.customParamsHandler)
        self.poly.subscribe(self.poly.OAUTH, self.oauthHandler)
        self.poly.subscribe(self.poly.CONFIGDONE, self.configDoneHandler)
        self.poly.subscribe(self.poly.ADDNODEDONE, self.addNodeDoneHandler)
        self.poly.subscribe(self.poly.POLL, self.systemPoll)



        self.poly.addNode(self, conn_status='ST')
        self.wait_for_node_done()

        self.node = self.poly.getNode(self.address)
        logging.debug(' NOde: {}'.format(self.node))
        self.poly.updateProfile()
        self.poly.ready()
       

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
        logging.info('Executing start')
        #self.myNetatmo = NetatmoWeather(self.poly)
        self.accessToken = self.myNetatmo.getAccessToken()
        while self.accessToken is None:
            time.sleep(2)
            logging.debug('Waiting to retrieve access token')
            
        logging.debug('AccessToken = {}'.format(self.accessToken))
        res = self.myNetatmo.get_homes()
        logging.debug('retrieved data {}'.format(res))


        self.home_ids = self.myNetatmo.get_homes()
        if self.home_ids:
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
        selected = False
        self.enabled_list = []
        self.homes_list = []
        for home in self.home_ids:
            home_name = self.home_ids[home]['name']
            main_modules = self.myNetatmo.get_main_modules(home)
            for m_module in main_modules:
                mod_name = main_modules[m_module]['name']
                node_name = home_name + '_'+ mod_name
                tmp = {}
                tmp['home'] = home
                tmp['main_module'] = m_module
                if node_name in self.Parameters:
                    if self.Parameters[node_name] == 1:
                        self.enabled_list.append(tmp)
                        if tmp['home'] not in self.homes_list:
                            self.homes_list.append(tmp['home'])
                            self.myNetatmo.update_weather_info_cloud(home)
                            self.myNetatmo.update_weather_info_instant(home)
                        selected = True
                else:
                    self.Parameters[node_name] = 1 #enable by default
                    self.enabled_list.append(tmp)
                    if tmp['home'] not in self.homes_list:
                        self.homes_list.append(tmp['home'])
                        self.myNetatmo.update_weather_info_cloud(home)
                        self.myNetatmo.update_weather_info_instant(home)

        if not selected and len(self.home_ids > 1):
            self.poly.Notices['home_id'] = 'Check config to select which home/modules should be used (1 - used, 0 - not used) - then restart'
        else:
            for node_nbr in range(0,len(self.enabled_list)):
                module_info = self.enabled_list[node_nbr]
                if module_info['home'] not in self.homes_list:
                    self.homes_list.append(module_info['home'])
                module = self.myNetatmo.get_module_info(module_info['home'],module_info['main_module'])
                node_address = self.getValieAddress(module[id])
                node_name = self.getValidName(module['name'])
                if not udiNetatmoWeatherMain(self.poly, node_address, node_address, node_name, self.myNetatmo, module_info):
                    logging.error('Failed to create MAin Weather station: {}'.format(node_name))
                time.sleep(1)            



    def configDoneHandler(self):
        # We use this to discover devices, or ask to authenticate if user has not already done so
        self.poly.Notices.clear()
        self.myNetatmo.updateOauthConfig()
        accessToken = self.myNetatmo._oAuthTokensRefresh()
        logging.debug('configDoneHandler - accessToken {}'.format(accessToken))
        if accessToken is None:
            logging.info('Access token is not yet available. Please authenticate.')
            self.poly.Notices['auth'] = 'Please initiate authentication'
            return
        

        #res = self.myNetatmo.get_home_info()
        #logging.debug('retrieved get_home_info data {}'.format(res))

        #res = self.myNetatmo.get_weather_info()
        #logging.debug('retrieved get_weather_info data {}'.format(res))

        #res = self.myNetatmo.get_weather_info2()
        #logging.debug('retrieved get_weather_info2 data2 {}'.format(res))

        #self.poly.discoverDevices()

    def oauthHandler(self, token):
        # When user just authorized, we need to store the tokens
        logging.debug('oauthHandler starting')
        self.myNetatmo.oauthHandler(token)
        accessToken = self.myNetatmo.getAccessToken()
        logging.debug('AccessToken obtained {}'.format(accessToken))

        # Then proceed with device discovery
        self.configDoneHandler()


    def addNodeDoneHandler(self, node):
        # We will automatically query the device after discovery
        #self.poly.addNodeDoneHandler(node)
        self.nodeDefineDone = True

    def systemPoll (self, polltype):
        if self.nodeDefineDone:
            logging.info('System Poll executing: {}'.format(polltype))
            try:
                if 'longPoll' in polltype:
                    #Keep token current
                    #self.node.setDriver('GV0', self.temp_unit, True, True)
                    
                        self.myNetatmo.refresh_token()
                        for home in self.homes_list:
                            self.myNetatmo.update_weather_info_cloud(home)
                            self.myNetatmo.update_weather_info_instant(home)


                        nodes = self.poly.getNodes()
                        for nde in nodes:
                            if nde != 'controller':   # but not the setup node
                                logging.debug('updating node {} data'.format(nde))
                                nodes[nde].updateISYdrivers()
                                                
                if 'shortPoll' in polltype:
                    self.heartbeat()
                    self.myNetatmo.refresh_token()
                    for home in self.homes_list:
                        self.myNetatmo.update_weather_info_instant(home)
                    for nde in nodes:
                        if nde != 'controller':   # but not the setup node
                            logging.debug('updating node {} data'.format(nde))
                            nodes[nde].updateISYdrivers()                   
            except Exception as e:
                    logging.debug('Exeption occcured : {}'.format(e))
   
                
        else:
            logging.info('System Poll - Waiting for all nodes to be added')


    def stopHandler(self):
        # Set nodes offline
        for node in self.poly.nodes():
            if hasattr(node, 'setOffline'):
                node.setOffline()
        self.poly.stop()

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

        polyglot.start({ 'version': version, 'requestId': True })

        # Show the help in PG3 UI under the node's Configuration option
        polyglot.setCustomParamsDoc()

        # Update the profile files
        polyglot.updateProfile()

        # Implements the API calls & Handles the oAuth authentication & token renewals
        myNetatmo = NetatmoWeather(polyglot)

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



