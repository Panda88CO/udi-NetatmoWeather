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

'''
id = 'rain'
drivers = [
            {'driver' : 'GV0', 'value': 0,  'uom':82}, 
            {'driver' : 'GV1', 'value': 0,  'uom':82}, 
            {'driver' : 'GV2', 'value': 0,  'uom':82}, 
            {'driver' : 'GV3', 'value': 0,  'uom':12}, 
            {'driver' : 'GV4', 'value': 0,  'uom':151}, 
            {'driver' : 'GV5', 'value': 0,  'uom':51}, 
          
            {'driver' : 'ST', 'value': 0,  'uom':2}, 
            ]
'''

class udiN_WeatherRain(udi_interface.Node):
    def __init__(self, polyglot, primary, address, name, NetatmoWeather, home, module):
        super().__init__(polyglot, primary, address, name)

        self.weather = NetatmoWeather
        self.module = module
        self.home = home
        self.primary = primary
        self.address = address
        self.name = name
        self.id = 'rain'
        self.drivers = [
            {'driver' : 'GV0', 'value': 0,  'uom':82}, 
            {'driver' : 'GV1', 'value': 0,  'uom':82}, 
            {'driver' : 'GV2', 'value': 0,  'uom':82}, 
            {'driver' : 'GV3', 'value': 0,  'uom':12}, 
            {'driver' : 'GV4', 'value': 0,  'uom':151}, 
            {'driver' : 'GV5', 'value': 0,  'uom':51}, 
          
            {'driver' : 'ST', 'value': 0,  'uom':2}, 
            ]
        
        self.poly.subscribe(self.poly.START, self.start, address)
        #self.poly.subscribe(self.poly.STOP, self.stop)
        self.poly.subscribe(self.poly.ADDNODEDONE, self.node_queue)
        self.n_queue = []

        polyglot.ready()
        self.poly.addNode(self)
        self.wait_for_node_done()
        self.node = self.poly.getNode(address)
        logging.info('Start {} Rain Node'.format(self.name))  
        time.sleep(1)

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
        tmp = re.sub(r"[^A-Za-z0-9_]", "", name.lower())
        logging.debug('getValidAddress {}'.format(tmp))
        return tmp[:14]
    
    

    def convert_temp_unit(self, tempStr):
        if tempStr.capitalize()[:1] == 'F':
            return(1)
        elif tempStr.capitalize()[:1] == 'K':
            return(0)
        

    def start(self):
        logging.debug('Executing NetatmoWeatherRain start')
        self.updateISYdrivers()
        
    def update(self, command = None):
        self.weather.update_weather_info_cloud(self.home)
        self.weather.update_weather_info_instant(self.home)
        self.updateISYdrivers()


    def updateISYdrivers(self):
        logging.debug('updateISYdrivers')
        data = self.weather.get_rain_module_data(self.home, self.module)
        logging.debug('Rain module data: {}'.format(data))

    commands = {        
                'UPDATE': update,
                'QUERY' : update, 
                }


       
                


