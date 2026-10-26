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
version = '1.0.2'

class NetatmoController(udi_interface.Node):
    id = 'CONTROLLER'
    drivers = [
        {'driver': 'ST', 'value': 0, 'uom': 2, 'name': 'NodeServer Online'},
    ]

    def __init__(self, polyglot, primary, address, name):
        super(NetatmoController, self).__init__(polyglot, primary, address, name)
        logging.debug('NetatmoController Initializing')
        logging.setLevel(10)
        self.poly = polyglot


        self.accessTokenEn = True
        self.accessToken = None
        self.nodeDefineDone = False
        self.configDone = False
        self.name = name
        self.primary = primary
        self.address = address
        self.temp_unit = 0
        self.nodes_in_db = self.poly.getNodesFromDb()
        self.myNetatmo = NetatmoWeather(self.poly)
        self.hb  = 0
        #logging.debug('testing 1')
        #self.customParameters = Custom(self.poly, 'customparams')
        self.Notices = Custom(self.poly, 'notices')
        self.n_queue = []
        #logging.debug('drivers : {}'.format(self.drivers))
        self.poly.subscribe(self.poly.STOP, self.stopHandler)
        self.poly.subscribe(self.poly.START, self.start, address)
        self.poly.subscribe(self.poly.CUSTOMPARAMS, self.myNetatmo.customParamsHandler)
        #self.poly.subscribe(self.poly.CUSTOMDATA, self.myNetatmo.customDataHandler)
        self.poly.subscribe(self.poly.CUSTOMNS, self.myNetatmo.customNsHandler)
        self.poly.subscribe(self.poly.OAUTH, self.myNetatmo.oauthHandler)
        self.poly.subscribe(self.poly.CONFIGDONE, self.configDoneHandler)
        self.poly.subscribe(self.poly.ADDNODEDONE, self.node_queue)
        self.poly.subscribe(self.poly.POLL, self.systemPoll)

        #logging.debug('testing 2')

        self.poly.addNode(self)
        self.wait_for_node_done(self.address)
        self.node = self.poly.getNode(self.address)
        self.nodes_in_db = self.poly.getNodesFromDb()
        self.poly.updateProfile()
        self.poly.ready()

    def node_queue(self, data):
        if data and 'address' in data:
            self.n_queue.append(data['address'])

    def wait_for_node_done(self, address=None, timeout=15):
        start_time = time.time()
        while time.time() - start_time < timeout:
            if address is None:
                if len(self.n_queue) > 0:
                    return self.n_queue.pop(0)
            elif address in self.n_queue:
                self.n_queue.remove(address)
                return True
            time.sleep(0.1)
        if address:
            logging.warning('Timeout waiting for node {} to be added'.format(address))
        return False

    def getValidName(self, name):
        name = bytes(name, 'utf-8').decode('utf-8','ignore')
        return re.sub(r"[^A-Za-z0-9_ ]", "", name)

    # remove all illegal characters from node address
    def getValidAddress(self, name):
        name = bytes(name, 'utf-8').decode('utf-8','ignore')
        tmp = re.sub(r"[^A-Za-z0-9_]", "", name.lower())
        logging.debug('getValidAddress {}'.format(tmp))
        return tmp[:14]
    

    def convert_temp_unit(self, tempStr):
        if tempStr.capitalize()[:1] == 'F':
            return(1)
        elif tempStr.capitalize()[:1] == 'C':
            return(0)
   
    def heartbeat(self):
        logging.debug('heartbeat: ' + str(self.hb))
        self.node.setDriver('ST', 1)
        if self.hb == 0:
            self.reportCmd('DON',2)
            self.hb = 1
        else:
            self.reportCmd('DOF',2)
            self.hb = 0

        

    def start(self):
        logging.info('Executing start')
        while not (self.configDone and self.myNetatmo.customParamsDone() and self.myNetatmo.customNsDone()):
            time.sleep(1)
            logging.debug('Waiting for config to complete: configDone={}, customParams={}, customNs={}'.format(
                self.configDone, self.myNetatmo.customParamsDone(), self.myNetatmo.customNsDone()))

        while not self.myNetatmo.authendicated():
            logging.warning('Access token is not yet available. Please authenticate.')
            self.poly.Notices['auth'] = 'Please initiate authentication in PG3 UI'
            time.sleep(5)            

        self.poly.Notices.clear()    

        self.home_ids = self.myNetatmo.get_homes()
        if not self.home_ids:
            logging.warning('No Netatmo homes or stations discovered.')
            self.nodeDefineDone = True
            return

        self.temp_unit = self.convert_temp_unit(self.myNetatmo.temp_unit)
        logging.debug('TEMP_UNIT: {}'.format(self.temp_unit))

        if self.node is not None:
            self.node.setDriver('ST', 1, True, True)

        # Pre-fetch weather data so cache is ready before nodes are added
        for home in self.home_ids:
            logging.info('Pre-fetching weather data for home {}'.format(home))
            self.myNetatmo.update_weather_info_cloud(home)
            self.myNetatmo.update_weather_info_instant(home)

        self.addNodes()

    def addNodes(self):
        logging.info('Adding selected weather stations in serialized sequence')
        self.homes_list = []
        primary_node_list = ['controller']

        for home in self.home_ids:
            logging.debug('Adding from {}'.format(home))
            home_name = self.home_ids[home]['name']
            main_modules = self.myNetatmo.get_main_modules(home)
            logging.debug('main modules {} {} '.format(home, main_modules))
            for m_module in main_modules:
                logging.debug('{} Evaluating MAIN module {} - {}'.format(home_name, m_module, main_modules))
                mod_name = main_modules[m_module]['name']
                node_name = self.getValidName(home_name + '_' + mod_name)
                node_address = self.getValidAddress(m_module)
                tmp_module = {'home': home, 'main_module': m_module}
                logging.debug('Module {} enabled = {}'.format(node_name, self.myNetatmo.main_module_enabled(node_name)))
                if self.myNetatmo.main_module_enabled(node_name):
                    if home not in self.homes_list:
                        self.homes_list.append(home)

                    logging.info('Adding Main Station node: {} ({})'.format(node_name, node_address))
                    main_node = udiNetatmoWeatherMain(self.poly, node_address, node_address, node_name, self.myNetatmo, tmp_module)
                    self.wait_for_node_done(node_address)
                    primary_node_list.append(node_address)

                    # Add subnodes sequentially for this station
                    main_node.addSubNodes(primary_node_list)

        # Remove extra nodes from database no longer used
        self.nodes_in_db = self.poly.getNodesFromDb()
        logging.debug('Checking for nodes not used - active primary list: {}'.format(primary_node_list))
        for node in self.nodes_in_db:
            if node.get('primaryNode') not in primary_node_list and node.get('address') != 'controller':
                logging.info('Removing obsolete node: {} ({})'.format(node.get('name'), node.get('address')))
                self.poly.delNode(node['address'])

        self.nodeDefineDone = True
        logging.info('All nodes successfully initialized. System ready.')

    
    def configDoneHandler(self):
        # We use this to discover devices, or ask to authenticate if user has not already done so
        self.poly.Notices.clear()
        logging.info('configDoneHandler called')
        #self.myNetatmo.updateOauthConfig()
        self.nodes_in_db = self.poly.getNodesFromDb()
        logging.debug('Nodes in Nodeserver - before cleanup: {} - {}'.format(len(self.nodes_in_db),self.nodes_in_db))
        self.configDone = True
        
        #res = self.myNetatmo.get_home_info()
        #logging.debug('retrieved get_home_info data {}'.format(res))

        #res = self.myNetatmo.get_weather_info()
        #logging.debug('retrieved get_weather_info data {}'.format(res))

        #res = self.myNetatmo.get_weather_info2()
        #logging.debug('retrieved get_weather_info2 data2 {}'.format(res))

        #self.poly.discoverDevices()

    '''
    def addNodeDoneHandler(self, data):
        self.n_queue.append(data['address'])
        # We will automatically query the device after discovery
        #self.poly.addNodeDoneHandler(node)
        #self.nodeDefineDone = True
        #pass
    '''
    def systemPoll (self, polltype):
        if self.nodeDefineDone:
            logging.info('System Poll executing: {}'.format(polltype))
            nodes = self.poly.nodes()
            #logging.debug('nodes : {}'.format(nodes))
            try:
                if 'longPoll' in polltype:
                    #Keep token current
                    #self.node.setDriver('GV0', self.temp_unit, True, True)
                    
                    #self.myNetatmo.refresh_token()
                    for home in self.homes_list:
                        self.myNetatmo.update_weather_info_cloud(home)
                        self.myNetatmo.update_weather_info_instant(home)


                    #nodes = self.poly.getNodes()
                    for nde in nodes:
                        if nde.address != 'controller':   # but not the setup node
                            logging.debug('updating node {} data'.format(nde))
                            nde.updateISYdrivers()
                                                
                if 'shortPoll' in polltype:
                    self.heartbeat()
                    #self.myNetatmo.refresh_token()
                    for home in self.homes_list:
                        self.myNetatmo.update_weather_info_instant(home)
                    for nde in nodes:
                        if nde.address != 'controller':   # but not the setup node
                            logging.debug('updating node {} data'.format(nde))
                            nde.updateISYdrivers()                   
            except Exception as e:
                    logging.error('Exeption occcured : {}'.format(e))
   
                
        else:
            logging.info('System Poll - Waiting for all nodes to be added')
 

    def stopHandler(self):
        # Set nodes offline
        for node in self.poly.nodes():
            if hasattr(node, 'setOffline'):
                #node.setDriver('ERR', 1)
                node.setOffline()
        self.poly.stop()

    def update(self, command=None):
        if self.nodeDefineDone:
            logging.info('update executing')
            nodes = self.poly.nodes()
            try:
                for home in self.homes_list:
                    self.myNetatmo.update_weather_info_cloud(home)
                    self.myNetatmo.update_weather_info_instant(home)
                for nde in nodes:
                    if nde.address != 'controller':   # but not the setup node
                        logging.debug('updating node {} data'.format(nde))
                        nde.updateISYdrivers()
                                            
            except Exception as e:
                    logging.error('Exeption occcured : {}'.format(e))
    id = 'CONTROLLER'
    drivers =  [ {'driver': 'ST', 'value':0, 'uom':2, 'name': 'NodeServer Online'}, ]
    commands = { 
        'UPDATE': update, 
        'QUERY': update,
    }

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
        #polyglot.updateProfile()

        # Implements the API calls & Handles the oAuth authentication & token renewals
        #myNetatmo = NetatmoWeather(polyglot)

        # then you need to create the controller node
        NetatmoController(polyglot, 'controller', 'controller', 'Netatmo Weather')

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



