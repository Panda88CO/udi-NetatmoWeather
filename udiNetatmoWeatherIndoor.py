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

from udiNetatmoCommon import getValidName, getValidAddress, convert_temp_unit, rfstate2ISY, battery2ISY, trend2ISY


#from nodes.controller import Controller
#from udi_interface import logging, Custom, Interface
'''
id = 'indoor'

drivers = [
            {'driver' : 'CLITEMP', 'value': 0,  'uom':4}, 
            {'driver' : 'CO2LVL', 'value': 0,  'uom':54}, 
            {'driver' : 'CLIHUM', 'value': 0,  'uom':22}, 
            {'driver' : 'GV3', 'value': 0,  'uom':4}, 
            {'driver' : 'GV4', 'value': 0,  'uom':4}, 
            {'driver' : 'GV5', 'value': 0,  'uom':25}, 
            {'driver' : 'GV6', 'value': 0,  'uom':151}, 
            {'driver' : 'GV7', 'value': 0,  'uom':51}, 
            {'driver' : 'GV8', 'value': 99,  'uom':25},          
            {'driver' : 'ST', 'value': 0,  'uom':2}, 
            ]
'''

class udiN_WeatherIndoor(udi_interface.Node):
    def __init__(self, polyglot, primary, address, name, NetatmoWeather, home, module):
        super().__init__(polyglot, primary, address, name)
        self.poly = polyglot
        self.weather= NetatmoWeather
        self.module = {'module_id':module, 'type':'INDOOR', 'home_id':home }
        #self.type = 'INDOOR'
        #self.home = home
        self.primary = primary
        self.address = address
        self.name = name        
        self.n_queue = []
        self.id = 'indoor'
        self.drivers = [
            {'driver' : 'CLITEMP', 'value': 0,  'uom':4}, 
            {'driver' : 'CO2LVL', 'value': 0,  'uom':54}, 
            {'driver' : 'CLIHUM', 'value': 0,  'uom':22}, 
            {'driver' : 'GV3', 'value': 0,  'uom':4}, 
            {'driver' : 'GV4', 'value': 0,  'uom':4}, 
            {'driver' : 'GV5', 'value': 99,  'uom':25}, 
            {'driver' : 'GV6', 'value': 0,  'uom':151}, 
            {'driver' : 'GV7', 'value': 99,  'uom':25}, 
            {'driver' : 'GV8', 'value': 99,  'uom':25},          
            {'driver' : 'ST', 'value': 0,  'uom':2}, 
            ]

        
        self.poly.subscribe(self.poly.START, self.start, address)
        #self.poly.subscribe(self.poly.STOP, self.stop)
        self.poly.subscribe(self.poly.ADDNODEDONE, self.node_queue)

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
    '''
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
    '''  

    def start(self):
        logging.debug('Executing NetatmoWeatherIndoor start')
        self.updateISYdrivers()        


   
        
    def updateISYdrivers(self):
        logging.debug('updateISYdrivers')
        data = self.weather.get_module_data(self.module)
        logging.debug('Indoor module data: {}'.format(data))
        if self.node is not None:
            if self.weather.get_online(self.module):
                self.node.setDriver('ST', 1)
                if convert_temp_unit(self.weather.temp_unit) == 1:
                    self.node.setDriver('CLITEMP', round(self.weather.get_temperature_C(self.module),1), True, False, 4 )
                    self.node.setDriver('GV3', round(self.weather.get_min_temperature_C(self.module),1), True, False, 4 )
                    self.node.setDriver('GV4', round(self.weather.get_max_temperature_C(self.module),1), True, False, 4 )
                else:
                    self.node.setDriver('CLITEMP', (round(self.weather.get_temperature_C(self.module)*9/5+32,1)), True, False, 17 )
                    self.node.setDriver('GV3', (round(self.weather.get_min_temperature_C(self.module)*9/5+32,1)), True, False, 17 )
                    self.node.setDriver('GV4', (round(self.weather.get_max_temperature_C(self.module)*9/5+32,1)), True, False, 17 )                     
                self.node.setDriver('CO2LVL', self.weather.get_co2(self.module), True, False, 54)
                self.node.setDriver('CLIHUM', self.weather.get_humidity(self.module), True, False, 51)
 
                temp_trend = self.weather.get_temp_trend(self.module)
                self.node.setDriver('GV5', trend2ISY(temp_trend))

                #hum_trend= self.weather.get_hum_trend(self.module)
                #self.node.setDriver('GV9', trend_val)
                self.node.setDriver('GV6', self.weather.get_time_stamp(self.module) , True, False, 151)

                bat_state, bat_lvl  = self.weather.get_battery_info(self.module)    
                self.node.setDriver('GV7', battery2ISY(bat_state), True, False, 25 )           
                rf1, rf2 = self.weather.get_rf_info(self.module) 
                self.node.setDriver('GV8', rfstate2ISY(rf1), True, False, 25  )
                #self.node.setDriver('ERR', 0)                     

            else:
                self.node.setDriver('CLITEMP', 99, True, False, 25 )
                self.node.setDriver('GV3', 99, True, False, 25 )
                self.node.setDriver('GV4', 99, True, False, 25 )
                self.node.setDriver('CO2LVL', 99, True, False, 25 )
                self.node.setDriver('CLIHUM', 99, True, False, 25 )
                self.node.setDriver('GV5', 99, True, False, 25 )
                self.node.setDriver('GV6', 99, True, False, 25 )
                self.node.setDriver('GV7', 99, True, False, 25 )
                self.node.setDriver('GV8', 99, True, False, 25 )
                self.node.setDriver('ST', 0) 
                #self.node.setDriver('ERR', 1)                     



    def update(self, command = None):
        self.weather.update_weather_info_cloud(self.module['home_id'])
        self.weather.update_weather_info_instant(self.module['home_id'])
        self.updateISYdrivers()


    commands = {        
                'UPDATE': update,
                'QUERY' : update, 
                }
