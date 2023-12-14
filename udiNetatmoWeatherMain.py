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


from udiNetatmoWeatherIndoor import udiN_WeatherIndoor
from udiNetatmoWeatherOutdoor import udiN_WeatherOutdoor
from udiNetatmoWeatherRain import udiN_WeatherRain
from udiNetatmoWeatherWind import udiN_WeatherWind
#from nodes.controller import Controller
#from udi_interface import logging, Custom, Interface

class udiNetatmoWeatherMain(udi_interface.Node):
    def __init__(self, polyglot, primary, address, name, NetatmoWeather, module_info):
        super().__init__(polyglot, primary, address, name)
        self.MAIN_modules = ['NAMain']
        self.OUTDOOR_modules = ['NAModule1']
        self.WIND_modules = ['NAModule2']
        self.RAIN_modules = ['NAModule3']
        self.INDOOR_modules = ['NAModule4']
        self.n_queue = []

        
        self.primary = address
        self.poly = polyglot
        self.weather = NetatmoWeather
        self.home_id = module_info['home']
        self.main_module_id = module_info['main_module']

        self.Parameters = Custom(self.poly, 'customparams')
        self.Notices = Custom(self.poly, 'notices')
        self.poly.subscribe(self.poly.START, self.start, address)
        #self.poly.subscribe(self.poly.STOP, self.stop)
        self.poly.subscribe(self.poly.ADDNODEDONE, self.node_queue)

        polyglot.ready()
        self.poly.addNode(self)
        self.wait_for_node_done()
        
        self.node = self.poly.getNode(address)
        logging.info('Start {} main module Node'.format(self.name))  
        time.sleep(1)
        self.n_queue = []
        self.nodeDefineDone = False

    
    
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
        logging.debug('Executing NetatmoWeatherMain start')
        
        self.addNodes()

    def stop (self):
        pass
    
    def addNodes(self):
        '''addNodes'''
        logging.debug('Adding subnodes to {}'.format(self.main_module_id))
        sub_modules = self.weather.get_sub_modules(self.home_id, self.main_module_id)
        if sub_modules:
            for s_module in sub_modules:
                module = self.weather.get_module_info(self.home_id, s_module)
                if 'name' in module:
                    name = self.getValidName(module['name'])
                else:
                    name = self.getValidName(module['id'])
                address = self.getValidAddress(module['id'])

                if s_module['type'] == self.INDOOR_modules:
                    udiN_WeatherIndoor(self.poly, self.primary, address, name, self.weather, self.home_id, s_module)
                elif s_module['type'] == self.OUTDOOR_modules:
                    udiN_WeatherOutdoor(self.poly, self.primary, address, name, self.weather, self.home_id, s_module)
                elif s_module['type'] == self.WIND_modules:
                    udiN_WeatherWind(self.poly, self.primary, address, name, self.weather, self.home_id, s_module)
                elif s_module['type'] == self.RAIN_modules:
                    udiN_WeatherRain(self.poly, self.primary, address, name, self.weather, self.home_id, s_module)
                else:
                    logging.error('Unknown module type encountered: {}'.format(s_module['type']))
                



        
