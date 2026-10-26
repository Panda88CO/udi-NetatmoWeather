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


class udiN_WeatherWind(udi_interface.Node):
    id = 'WIND'
    drivers = [ 
        {'driver' : 'ST', 'value': 0,  'uom':48, 'name': 'Wind'},
        {'driver' : 'GV1', 'value': 0,  'uom':76, 'name': 'Wind Angle'},
        {'driver' : 'GV2', 'value': 0,  'uom':48, 'name': 'Gust Strength'},
        {'driver' : 'GV3', 'value': 0,  'uom':76, 'name': 'Gust Angle'},
        {'driver' : 'GV4', 'value': 0,  'uom':48, 'name': 'Max Wind Strength'},
        {'driver' : 'GV5', 'value': 0,  'uom':76, 'name': 'Max Wind Angle'},
        {'driver' : 'GV7', 'value': 99,  'uom':25, 'name': 'Battery'},
        {'driver' : 'GV8', 'value': 99,  'uom':25, 'name': 'RF Status'},                
        {'driver' : 'GV9', 'value': 0,  'uom':2, 'name': 'Connected'},   
        {'driver' : 'TIME', 'value': 0,  'uom':151, 'name': 'Time of last data'},
    ]

    def __init__(self, polyglot, primary, address, name, NetatmoWeather, home,  module):
        super().__init__(polyglot, primary, address, name)

        self.poly = polyglot
        self.weather = NetatmoWeather
        self.module = {'module_id':module, 'type':'WIND', 'home_id':home }
        self.primary = primary
        self.address = address
        self.name = name        
  
        self.n_queue = []
        self.poly.subscribe(self.poly.ADDNODEDONE, self.node_queue)

        self.poly.addNode(self)
        self.wait_for_node_done(self.address)
        self.node = self.poly.getNode(address)
        logging.info('Start {} Wind Node'.format(self.name))  
        self.updateISYdrivers()
        self.nodeDefineDone = True
    
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
        elif tempStr.capitalize()[:1] == 'K':
            return(0)
        

    def start(self):
        logging.debug('Executing NetatmoWeatherWind start')
        self.updateISYdrivers()
        
        #self.addNodes()

    def update(self, command = None):
        self.weather.update_weather_info_cloud(self.module['home_id'])
        self.weather.update_weather_info_instant(self.module['home_id'])
        self.updateISYdrivers()

    def rfstate2ISY(self, rf_state):
        if rf_state is None:
            return 99
        if rf_state.lower() == 'full' or rf_state.lower() == 'high':
            rf = 0
        elif rf_state.lower() == 'medium':
            rf = 1
        elif rf_state.lower() == 'low':
            rf = 2
        else:
            rf= 99
            logging.error('Unsupported RF state {}'.format(rf_state))
        return(rf)
    

    def battery2ISY(self, batlvl):
        if batlvl is None:
            return 99
        if batlvl == 'max':
            state = 0
        elif batlvl == 'full':
            state = 1
        elif batlvl == 'high':
            state = 2
        elif batlvl == 'medium':
            state = 3
        elif batlvl == 'low':
            state = 4
        elif batlvl == 'very low':
            state = 5
        else:
            state = 99
        return(state)
    

    def updateISYdrivers(self):
        logging.debug('updateISYdrivers')
        data = self.weather.get_module_data(self.module)
        logging.debug('Wind module data: {}'.format(data))
        if self.node is not None:
            if self.weather.get_online(self.module):
                self.node.setDriver('GV9', 1)
              
                wind_str = self.weather.get_wind_strength(self.module)
                if wind_str is not None:
                    self.node.setDriver('ST', wind_str, True, False, 48)
                wind_ang = self.weather.get_wind_angle(self.module)
                if wind_ang is not None:
                    self.node.setDriver('GV1', wind_ang, True, False, 76)
                gust_str = self.weather.get_gust_strength(self.module)
                if gust_str is not None:
                    self.node.setDriver('GV2', gust_str, True, False, 48)
                gust_ang = self.weather.get_gust_angle(self.module)
                if gust_ang is not None:
                    self.node.setDriver('GV3', gust_ang, True, False, 76)
                max_str = self.weather.get_max_wind_strength(self.module)
                if max_str is not None:
                    self.node.setDriver('GV4', max_str, True, False, 48)
                max_ang = self.weather.get_max_wind_angle(self.module)
                if max_ang is not None:
                    self.node.setDriver('GV5', max_ang, True, False, 76)

                time_stamp = self.weather.get_time_stamp(self.module)
                if time_stamp is not None:
                    try:
                        ts_val = int(time_stamp)
                        if ts_val > 0:
                            self.node.setDriver('TIME', ts_val, True, False, 151)
                    except (ValueError, TypeError):
                        pass
                
                bat_state, bat_lvl  = self.weather.get_battery_info(self.module)    
                self.node.setDriver('GV7', self.battery2ISY(bat_state), True, False, 25 )     
                rf1, rf2 = self.weather.get_rf_info(self.module) 
                self.node.setDriver('GV8', self.rfstate2ISY(rf1), True, False, 25 )
                #self.node.setDriver('ERR', 0)
            else:
                self.node.setDriver('ST', 99, True, False, 25 )
                self.node.setDriver('GV1', 99, True, False, 25 )
                self.node.setDriver('GV2', 99, True, False, 25 )
                self.node.setDriver('GV3', 99, True, False, 25 )
                self.node.setDriver('GV4', 99, True, False, 25 )
                self.node.setDriver('GV5', 99, True, False, 25 )
                self.node.setDriver('GV7', 99, True, False, 25 )
                self.node.setDriver('GV8', 99, True, False, 25 )                 
                self.node.setDriver('GV9', 0)
                #self.node.setDriver('ERR', 1)
       
    commands = {        
        'UPDATE': update,
        'QUERY' : update, 
        }
         
