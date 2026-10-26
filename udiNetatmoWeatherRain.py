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

class udiN_WeatherRain(udi_interface.Node):
    id = 'RAIN'
    drivers = [
        {'driver' : 'ST', 'value': 0,  'uom':82, 'name': 'Rain'}, 
        {'driver' : 'GV1', 'value': 0,  'uom':82, 'name': 'Sum Rain 1h'}, 
        {'driver' : 'GV2', 'value': 0,  'uom':82, 'name': 'Sum Rain 24h'}, 
        {'driver' : 'GV4', 'value': 99,  'uom':25, 'name': 'Battery'}, 
        {'driver' : 'GV5', 'value': 99,  'uom':25, 'name': 'RF Status'}, 
        {'driver' : 'GV9', 'value': 0,  'uom':2, 'name': 'Connected'}, 
        {'driver' : 'TIME', 'value': 0,  'uom':151, 'name': 'Time of last data'}, 
    ]

    def __init__(self, polyglot, primary, address, name, NetatmoWeather, home, module, controller=None):
        super().__init__(polyglot, primary, address, name)

        self.poly = polyglot
        self.controller = controller
        self.weather = NetatmoWeather
        self.module = {'module_id':module, 'type':'RAIN', 'home_id':home }
        self.primary = primary
        self.address = address
        self.name = name
        
        self.n_queue = []
        self.poly.subscribe(self.poly.ADDNODEDONE, self.node_queue)

        self.poly.addNode(self)
        self.wait_for_node_done(self.address)
        self.node = self.poly.getNode(address)
        logging.info('Start {} Rain Node'.format(self.name))  
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
    
    

    def start(self):
        logging.debug('Executing NetatmoWeatherRain start')
        self.updateISYdrivers()

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
        logging.debug('Rain module data: {}'.format(data))
        if self.node is not None:
            if self.weather.get_online(self.module):
                self.node.setDriver('GV9', 1)
              
                rain = self.weather.get_rain(self.module)
                if rain is not None:
                    self.node.setDriver('ST', rain, True, False, 82)
                rain_1h = self.weather.get_rain_1hour(self.module)
                if rain_1h is not None:
                    self.node.setDriver('GV1', rain_1h, True, False, 82)
                rain_24h = self.weather.get_rain_24hours(self.module)
                if rain_24h is not None:
                    self.node.setDriver('GV2', rain_24h, True, False, 82)

                time_stamp = self.weather.get_time_stamp(self.module)
                if time_stamp is not None:
                    try:
                        ts_val = int(time_stamp)
                        if ts_val > 0:
                            self.node.setDriver('TIME', ts_val, True, False, 151)
                    except (ValueError, TypeError):
                        pass
                
                bat_state, bat_lvl  = self.weather.get_battery_info(self.module)    
                self.node.setDriver('GV4', self.battery2ISY(bat_state), True, False, 25 )     
                rf1, rf2 = self.weather.get_rf_info(self.module) 
                self.node.setDriver('GV5', self.rfstate2ISY(rf1), True, False, 25 )
                #self.node.setDriver('ERR', 0)
            else:
                self.node.setDriver('ST', 99, True, False, 25 )
                self.node.setDriver('GV1', 99, True, False, 25 )
                self.node.setDriver('GV2', 99, True, False, 25 )
                self.node.setDriver('GV4', 99, True, False, 25 )
                self.node.setDriver('GV5', 99, True, False, 25 )
                self.node.setDriver('GV9', 0)
                #self.node.setDriver('ERR', 1)


    commands = {        
                'UPDATE': update,
                'QUERY' : update, 
                }


       
                


