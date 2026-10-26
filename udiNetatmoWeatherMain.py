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
#id = 'main_netatmo'

'''
      <st id="ST" editor="bool" />
      <st id="CLITEMP" editor="temperature" />
      <st id="GV1" editor="co2" />
      <st id="GV2" editor="humidity" />
      <st id="GV3" editor="noise" />
      <st id="GV4" editor="pressure" />
      <st id="GV5" editor="pressure" />
      <st id="GV6" editor="temperature" />
      <st id="GV7" editor="temperature" />
      <st id="GV8" editor="trend" />
      <st id="GV9" editor="trend" />
      <st id="GV10" editor="t_timestamp" />
      <st id="GV11" editor="wifi_rf_status" />
    </sts>
'''
class udiNetatmoWeatherMain(udi_interface.Node):
    id = 'MAINUNIT'
    drivers = [
        {'driver' : 'ST', 'value': 0,  'uom':2, 'name': 'Connected'}, 
        {'driver' : 'CLITEMP', 'value': 99,  'uom':25, 'name': 'Temperature'}, 
        {'driver' : 'CO2LVL', 'value': 99,  'uom':25, 'name': 'CO2'}, 
        {'driver' : 'CLIHUM', 'value': 0,  'uom':51, 'name': 'Humidity'}, 
        {'driver' : 'GV3', 'value': 0,  'uom':12, 'name': 'Noise'}, 
        {'driver' : 'BARPRES', 'value': 0,  'uom':117, 'name': 'Pressure'}, 
        {'driver' : 'GV5', 'value': 0,  'uom':117, 'name': 'Absolute Pressure'}, 
        {'driver' : 'GV6', 'value': 0,  'uom':4, 'name': 'Min Temperature'}, 
        {'driver' : 'GV7', 'value': 0,  'uom':4, 'name': 'Max Temperature'}, 
        {'driver' : 'GV8', 'value': 99,  'uom':25, 'name': 'Temperature Trend'}, 
        {'driver' : 'GV9', 'value': 99,  'uom':25, 'name': 'Pressure Trend'}, 
        {'driver' : 'GV11', 'value': 99,  'uom':25, 'name': 'Wi-Fi Status'},         
        {'driver' : 'TIME', 'value': 0,  'uom':151, 'name': 'Time of last data'},
    ]

    def __init__(self, polyglot, primary, address, name, NetatmoWeather, module_info, controller=None):
        super().__init__(polyglot, primary, address, name)
        self.MAIN_modules = ['NAMain']
        self.OUTDOOR_modules = ['NAModule1']
        self.WIND_modules = ['NAModule2']
        self.RAIN_modules = ['NAModule3']
        self.INDOOR_modules = ['NAModule4']
        self.poly = polyglot
        self.controller = controller or self.poly.getNode('controller')
        self.n_queue = []
        self.poly.subscribe(self.poly.ADDNODEDONE, self.node_queue)
        self.module = {'module_id':module_info['main_module'], 'type':'MAIN', 'home_id':module_info['home'] }
        logging.debug('self.module = {}'.format(self.module))
        self.primary = primary
        self.address = address
        self.name = name

        self.weather = NetatmoWeather
        #self.home_id = module_info['home']
        #self.main_module_id = module_info['main_module']

        self.Parameters = Custom(self.poly, 'customparams')
        self.Notices = Custom(self.poly, 'notices')
        self.poly.subscribe(self.poly.START, self.start, address)
        #self.poly.subscribe(self.poly.STOP, self.stop)

        self.poly.addNode(self)
        self.wait_for_node_done(self.address)
        
        self.node = self.poly.getNode(address)
        logging.info('Start {} main module Node'.format(self.name))
        self.updateISYdrivers()

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
    
    def rfstate2ISY(self, rf_state):
        if rf_state is None:
            return 99
        if rf_state.lower() == 'full':
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
    
    def trend2ISY (self, trend):
        if trend is None:
            return 99
        if trend == 'stable':
            return(0)
        elif trend == 'up':
            return(1)
        elif trend =='down':
            return(2)
        else:
            logging.error('unsupported temperature trend: {}'.format(trend))
            return(99)    


    def convert_temp_unit(self, tempStr):
        if tempStr.capitalize()[:1] == 'F':
            return(1)
        elif tempStr.capitalize()[:1] == 'C':
            return(0)
        
    


    def start(self):
        logging.debug('Executing NetatmoWeatherMain start')
        self.update()

    def stop(self):
        pass

    def addSubNodes(self, primary_node_list=None):
        logging.debug('self.module {}'.format(self.module))
        logging.debug('Adding subnodes to {}'.format(self.module['module_id']))
        sub_modules = self.weather.get_sub_modules(self.module['home_id'], self.module['module_id'])
        logging.debug('System sub modules: {}'.format(sub_modules))
        if sub_modules:
            for s_module in sub_modules:
                logging.debug('s_module: {}'.format(s_module))
                module = self.weather.get_module_info(self.module['home_id'], s_module)
                logging.debug('module: {}'.format(module))
                if not module:
                    continue
                if 'name' in module:
                    api_name = self.getValidName(module['name'])
                else:
                    api_name = self.getValidName(module['id'])
                address = self.getValidAddress(module['id'])

                if self.controller and hasattr(self.controller, 'resolve_node_name'):
                    name = self.controller.resolve_node_name(address, api_name)
                else:
                    name = api_name

                logging.debug(' types: {} {}'.format(module.get('type'), self.INDOOR_modules))

                if module.get('type') in self.INDOOR_modules:
                    udiN_WeatherIndoor(self.poly, self.primary, address, name, self.weather, self.module['home_id'], s_module, controller=self.controller)
                elif module.get('type') in self.OUTDOOR_modules:
                    udiN_WeatherOutdoor(self.poly, self.primary, address, name, self.weather, self.module['home_id'], s_module, controller=self.controller)
                elif module.get('type') in self.WIND_modules:
                    udiN_WeatherWind(self.poly, self.primary, address, name, self.weather, self.module['home_id'], s_module, controller=self.controller)
                elif module.get('type') in self.RAIN_modules:
                    udiN_WeatherRain(self.poly, self.primary, address, name, self.weather, self.module['home_id'], s_module, controller=self.controller)
                else:
                    logging.error('Unknown module type encountered: {}'.format(module.get('type')))
                    continue

                if primary_node_list is not None:
                    primary_node_list.append(address)

        self.updateISYdrivers()

    def addNodes(self):
        self.addSubNodes()
                
    def update(self, command = None):
        self.weather.update_weather_info_cloud(self.module['home_id'])
        self.weather.update_weather_info_instant(self.module['home_id'])
        self.updateISYdrivers()

   
        
    def updateISYdrivers(self):
        logging.debug('updateISYdrivers')
        data = self.weather.get_module_data(self.module)
        logging.debug('Main module data: {}'.format(data))
        if self.node is not None:
            if self.weather.get_online(self.module):
                self.node.setDriver('ST', 1)
                logging.debug('TempUnit = {} {}'.format(self.weather.temp_unit, self.convert_temp_unit(self.weather.temp_unit)))
                temp = self.weather.get_temperature_C(self.module)
                min_temp = self.weather.get_min_temperature_C(self.module)
                max_temp = self.weather.get_max_temperature_C(self.module)
                if self.convert_temp_unit(self.weather.temp_unit) == 0:
                    if temp is not None:
                        self.node.setDriver('CLITEMP', round(temp, 1), True, False, 4)
                    if min_temp is not None:
                        self.node.setDriver('GV6', round(min_temp, 1), True, False, 4)
                    if max_temp is not None:
                        self.node.setDriver('GV7', round(max_temp, 1), True, False, 4)
                else:
                    if temp is not None:
                        self.node.setDriver('CLITEMP', round(temp * 9 / 5 + 32, 1), True, False, 17)
                    if min_temp is not None:
                        self.node.setDriver('GV6', round(min_temp * 9 / 5 + 32, 1), True, False, 17)
                    if max_temp is not None:
                        self.node.setDriver('GV7', round(max_temp * 9 / 5 + 32, 1), True, False, 17)
                co2 = self.weather.get_co2(self.module)
                if co2 is not None:
                    self.node.setDriver('CO2LVL', co2, True, False, 54)
                hum = self.weather.get_humidity(self.module)
                if hum is not None:
                    self.node.setDriver('CLIHUM', hum, True, False, 51)
                noise = self.weather.get_noise(self.module)
                if noise is not None:
                    self.node.setDriver('GV3', round(noise, 0), True, False, 12)
                pres = self.weather.get_pressure(self.module)
                if pres is not None:
                    self.node.setDriver('BARPRES', round(pres, 0), True, False, 117)
                abs_pres = self.weather.get_abs_pressure(self.module)
                if abs_pres is not None:
                    self.node.setDriver('GV5', round(abs_pres, 0), True, False, 117)

                temp_trend = self.weather.get_temp_trend(self.module)
                self.node.setDriver('GV8', self.trend2ISY(temp_trend))

                pres_trend = self.weather.get_pressure_trend(self.module)
                self.node.setDriver('GV9', self.trend2ISY(pres_trend))
                time_stamp = self.weather.get_time_stamp(self.module)
                if time_stamp is not None:
                    try:
                        ts_val = int(time_stamp)
                        if ts_val > 0:
                            self.node.setDriver('TIME', ts_val, True, False, 151)
                    except (ValueError, TypeError):
                        pass
                rf1, rf2 = self.weather.get_rf_info(self.module) 
                self.node.setDriver('GV11', self.rfstate2ISY(rf1) )
                #self.node.setDriver('ERR', 0)    
            else:
                self.node.setDriver('CLITEMP', 99, True, False, 25 )
                self.node.setDriver('GV6', 99, True, False, 25 )
                self.node.setDriver('GV7', 99, True, False, 25 )
                self.node.setDriver('CO2LVL', 99, True, False, 25 )
                self.node.setDriver('CLIHUM', 99, True, False, 25 )
                self.node.setDriver('GV3', 99, True, False, 25 )
                self.node.setDriver('BARPRES', 99, True, False, 25 )
                self.node.setDriver('GV5', 99, True, False, 25 )
                self.node.setDriver('GV8', 99, True, False, 25 )
                self.node.setDriver('GV9', 99, True, False, 25 )
                self.node.setDriver('GV11', 99, True, False, 25 )
                self.node.setDriver('ST', 0) 
                #self.node.setDriver('ERR', 1)                     



    commands = {        
                'UPDATE': update,
                }

        
