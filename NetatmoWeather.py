
#!/usr/bin/env python3
from  NetatmoOauth import NetatmoCloud 
import urllib.parse

#from oauth import OAuth
try:
    import udi_interface
    logging = udi_interface.LOGGER
    Custom = udi_interface.Custom
except ImportError:
    import logging
    logging.basicConfig(level=logging.DEBUG)



class NetatmoWeather (NetatmoCloud):
    def __init__(self, polyglot):
        super().__init__(polyglot)
        logging.info('NetatmoWeather initializing')
        self.poly = polyglot
        self._dev_list  = ['NAMain', 'NAModule1', 'NAModule2', 'NAModule3', 'NAModule4']

        self.instant_data = {}
        self.cloud_data = {}
        self.weather_data = {}
        self.MAIN_modules = ['NAMain']
        self.OUTDOOR_modules = ['NAModule1']
        self.WIND_modules = ['NAModule2']
        self.RAIN_modules = ['NAModule3']
        self.INDOOR_modules = ['NAModule4']
        self.scope = "read_station"

    # should not be necesary - filtered by token    
    #def get_weather_stations (self):
    #    logging.debug('get_weather_stations')
    #    all_systems = 


    def update_weather_info_cloud (self, home_id):
        ''' Polls latest data stored in cloud - more data available'''
        logging.debug('get_weather_info_cloud')
        try:
            tmp = self.get_modules(home_id)
            logging.debug('tmp = {}'.format(tmp))
            self.cloud_data[home_id] = {}
            for dev_id in tmp:
                if tmp[dev_id]['type'] in self.MAIN_modules:
                    
                    dev_id_str = urllib.parse.quote_plus(dev_id )

                    api_str = '/getstationsdata?device_id='+str(dev_id_str)+'&get_favorites=false'
                    
                    temp_data = self._callApi('GET', api_str )

                    logging.debug('dev Id {}, data: {} '.format(dev_id, temp_data))

                    #test = self._callApi('GET', '/getstationsdata' )
                    #logging.debug(temp_data)

                    if temp_data['status'] == 'ok':
                        if len(temp_data['body']['devices'] ) == 1:
                            temp_data = temp_data['body']['devices'][0]  # there should only be 1 dev_id
                        else:
                            logging.error('Code only handles 1st main weather station : {} found'.format(len(temp_data['body']['devices'])))
                            logging.error('Processing first one')
                            temp_data = temp_data['body']['devices'][0]

                        self.cloud_data[home_id] = {}
                        self.cloud_data[home_id]['MAIN'] = {}
                        self.cloud_data[home_id]['INDOOR'] = {}
                        self.cloud_data[home_id]['OUTDOOR'] = {}
                        self.cloud_data[home_id]['RAIN'] = {}
                        self.cloud_data[home_id]['WIND'] = {}

                        self.cloud_data[home_id]['MAIN'][dev_id] = temp_data['dashboard_data']
                        self.cloud_data[home_id]['MAIN'][dev_id] ['reachable'] = temp_data['reachable']
                        self.cloud_data[home_id]['MAIN'][dev_id] ['data_type'] = temp_data['data_type']

                        for module in range(0,len(temp_data['modules'])):
                            mod = temp_data['modules'][module]
                            self.cloud_data[home_id][self.module_type(mod['type'])][mod['_id']] = mod['dashboard_data']
                            self.cloud_data[home_id][self.module_type(mod['type'])][mod['_id']]['data_type'] = mod['data_type']
                self.merge_data()         
            return(self.cloud_data)
        except Exception as e:
            logging.error('update_weather_info_cloud failed : {}'.format(e))
            return({})


    def module_type (self, type):
        if type in self.MAIN_modules:
            return('MAIN')
        elif type in self.OUTDOOR_modules:
            return('OUTDOOR')
        elif type in self.INDOOR_modules:
            return('INDOOR')
        elif type in self.RAIN_modules:
            return('RAIN')
        elif type in self.WIND_modules:
            return('WIND')                    


    def update_weather_info_instant(self, home_id):
        '''Polls latest data - within 10 sec '''
        logging.debug('update_weather_info_instant')
        tmp = self.get_home_status(home_id)
        if home_id not in self.instant_data:
            self.instant_data[home_id] = {}
            self.instant_data[home_id]['MAIN'] = {}
            self.instant_data[home_id]['OUTDOOR'] = {}
            self.instant_data[home_id]['INDOOR'] = {}
            self.instant_data[home_id]['RAIN'] = {}
            self.instant_data[home_id]['WIND'] = {}
        if 'modules' in tmp:
            for module in tmp['modules']:
                #self.instant_data[home_id][module] = tmp['modules'][module]
                self.instant_data[home_id][self.module_type(tmp['modules'][module]['type'])][module] = tmp['modules'][module]
        else:
            self.instant_data[home_id] = {}
        self.merge_data()
        return(self.instant_data)
    
    def merge_data_str(self, data):
        '''merge_data_str'''
        if data == 'ts':
            data_str = 'time_stamp'
        if data == 'time_utc':
            data_str = 'time_stamp'               
        elif data == 'AbsolutePressure':
            data_str = 'absolute_pressure'
        elif data == 'reachable':
            data_str = 'online'

        else:
            data_str = data.lower()
        return(data_str)


    def merge_data(self):
        '''Merges/combines cloud data and instant data '''
        logging.debug('merge_data')
        instant_data = self.instant_data != {}
        cloud_data = self.cloud_data != {}

        if cloud_data and instant_data:
            for home_id in self.cloud_data:
                for module_type in self.cloud_data[home_id]:
                    for module_adr in self.cloud_data[home_id][module_type]:
                        # data exists so data must exist for weather_data
                        inst_mod_adr = self.instant_data[home_id][module_type][module_adr]
                        cloud_mod_adr = self.cloud_data[home_id][module_type][module_adr]
                        if cloud_mod_adr['time_utc'] > inst_mod_adr ['ts']:
                            for data in inst_mod_adr:
                                data_str = self.merge_data_str(data)
                                self.weather_data[home_id][module_type][module_adr][data_str] =inst_mod_adr[data]
                            for data in cloud_mod_adr:
                                data_str = self.merge_data_str(data)                               
                                self.weather_data[home_id][module_type][module_adr][data_str] =cloud_mod_adr[data]
                        else:
                            for data in cloud_mod_adr:
                                data_str = self.merge_data_str(data)                            
                                self.weather_data[home_id][module_type][module_adr][data_str] =cloud_mod_adr[data]
                            for data in inst_mod_adr:
                                data_str = self.merge_data_str(data)
                                self.weather_data[home_id][module_type][module_adr][data_str] =inst_mod_adr[data]
        elif cloud_data: # instant_data must be False
            for home_id in self.cloud_data:
                for module_type in self.cloud_data[home_id]:
                    for module_adr in self.cloud_data[home_id][module_type]:
                        if home_id not in self.weather_data:
                            self.weather_data[home_id] = {}       
                        if module_type not in self.weather_data[home_id]:
                            self.weather_data[home_id][module_type]= {}
                        if module_adr not in self.weather_data[home_id][module_type]:
                            self.weather_data[home_id][module_type][module_adr]= {}
                                # check who has leastes data - process older first
                        cloud_mod_adr = self.cloud_data[home_id][module_type][module_adr]
                        for data in cloud_mod_adr:
                            data_str = self.merge_data_str(data)
                            self.weather_data[home_id][module_type][module_adr][data_str] =cloud_mod_adr[data]

        else: # cloud_data must be False
            for home_id in self.instant_data:
                for module_type in self.instant_data[home_id]:
                    for module_adr in self.instant_data[home_id][module_type]:
                        if home_id not in self.weather_data:
                            self.weather_data[home_id] = {}       
                        if module_type not in self.weather_data[home_id]:
                            self.weather_data[home_id][module_type]= {}
                        if module_adr not in self.weather_data[home_id][module_type]:
                            self.weather_data[home_id][module_type][module_adr]= {}
                                # check who has leastes data - process older first
                        inst_mod_adr = self.instant_data[home_id][module_type][module_adr]
                        for data in inst_mod_adr:
                            data_str = self.merge_data_str(data)
                            self.weather_data[home_id][module_type][module_adr][data_str] =inst_mod_adr[data]
        logging.debug('merge_data complete')


    def get_homes(self):
        '''get_homes'''

        tmp = self.get_homes_info()
        self.weather_in_homes = {}
        for home_id in tmp:
            found = False
            for mod_type in tmp[home_id]['module_types']:
                if mod_type in  self._dev_list:
                    found = True
            if found:
                self.weather_in_homes[home_id] = tmp[home_id]
        return(self.weather_in_homes)

    def get_main_modules(self, home_id):
        '''get_main_modules '''
        tmp = self._get_modules(home_id, self.MAIN_modules)
        logging.debug('get_main_modules {}'.format(tmp))
        return(self._get_modules(home_id, self.MAIN_modules))
    

    def get_indoor_modules(self, home_id):
        '''get_indoor_modules '''
        return(self._get_modules(home_id, self.INDOOR_modules))        


    def get_outdoor_modules(self, home_id):
        '''get_outdoor_modules '''
        return(self._get_modules(home_id, self.OUTDOOR_modules))    
    
    
    def get_rain_modules(self, home_id):
        '''get_rain_modules '''
        return(self._get_modules(home_id,self.RAIN_modules))    


    def get_wind_modules(self, home_id):
        '''get_wind_modules '''
        return(self._get_modules(home_id, self.WIND_modules))    


    def _get_weather_data(self, home_id, dev_id, mod_type):
        '''Get data function'''
        if home_id in self.weather_data:
            if mod_type in self.weather_data[home_id]:
                if dev_id in self.weather_data[home_id][mod_type]:
                    return(self.weather_data[home_id][mod_type][dev_id])
        else:
            logging.error('No data fouond for {0} {1}'.format(home_id, dev_id))
    '''
    def get_main_module_data(self, home_id, dev_id):
        #Get data from main module
        logging.debug('get_main_module_data')
        #data_list = ['Temperature', 'CO2', 'Humidity', 'Noise', 'Pressure', 'AbsolutePressure', 'min_temp', 'max_temp', 'date_max_temp', 'date_min_temp', 'temp_trend', 'reachable']
        return(self._get_weather_data(home_id, dev_id, 'MAIN'))
    '''    

    def get_module_data(self, module):
        logging.debug('get_indoor_module_data')
        #data_list = ['temperature', 'co2', 'humidity', 'last_seen', 'battery_state', 'ts']
        return(self._get_weather_data(module['home_id'], module['module_id'], module['type']))
               
    '''
    def get_outdoor_module_data(self, home_id, dev_id=None):
        logging.debug('get_outdoor_module_data')
        #data_list = ['temperature', 'co2', 'humidity', 'last_seen', 'battery_state', 'ts']
        return(self._get_weather_data(home_id, dev_id, 'OUTDOOR'))

    def get_rain_module_data(self, home_id, dev_id=None):
        logging.debug('get_rain_module_data')
        #data_list = ['rain', 'sum_rain_1', 'sum_rail_24', 'last_seen', 'battery_state', 'ts']
        return(self._get_weather_data(home_id, dev_id, 'RAIN'))

    def get_wind_module_data(self, home_id, dev_id=None):
        logging.debug('get_wind_module_data')
        #data_list = ['wind_strength', 'wind_angle', 'wind+gust', 'wind_gust_angle', 'last_seen', 'battery_state', 'ts']
        return(self._get_weather_data(home_id, dev_id, 'WIND'))
    '''

    def get_temperature_C(self, module):
        try:
            logging.debug('get_temperature_C {} {} {} {}'.format(self.weather_data[module['home_id']][module['type']][module['dev_id']]['temperature'],module['home_id'], module['type'], module['dev_id'] ))
            return(self.weather_data[module['home_id']][module['type']][module['dev_id']]['temperature'])       
        except Exception as e:
            logging.error('get_temperature_C exception; {}'.format(e))
            return(None)
    def get_max_temperature_C (self, module):
        try:
            logging.debug('get_max_temperature_C {} {} {} {}'.format(self.weather_data[module['home_id']][module['type']][module['dev_id']]['temp_max'],module['home_id'], module['type'], module['dev_id'] ))
            return(self.weather_data[module['home_id']][module['type']][module['dev_id']]['temp_max'])       
        except Exception as e:
            logging.error('get_max_temperature_C exception; {}'.format(e))
            return(None)

    def get_min_temerature_C(self, module):
        try:
            logging.debug('get_min_temerature_C {} {} {} {}'.format(self.weather_data[module['home_id']][module['type']][module['dev_id']]['temp_min'],module['home_id'], module['type'], module['dev_id'] ))
            return(self.weather_data[module['home_id']][module['type']][module['dev_id']]['temp_min'])       
        except Exception as e:
            logging.error('get_min_temerature_C exception; {}'.format(e))
            return(None)

    def get_co2(self, module):
        try:
            logging.debug('get_co2 {} {} {} {}'.format(self.weather_data[module['home_id']][module['type']][module['dev_id']]['co2'],module['home_id'], module['type'], module['dev_id'] ))
            return(self.weather_data[module['home_id']][module['type']][module['dev_id']]['co2'])       
        except Exception as e:
            logging.error('get_co2 exception; {}'.format(e))
            return(None)


    def get_humidity(self, module):
        try:
            logging.debug('get_humidity {} {} {} {}'.format(self.weather_data[module['home_id']][module['type']][module['dev_id']]['temp_trend'],module['home_id'], module['type'], module['dev_id'] ))
            return(self.weather_data[module['home_id']][module['type']][module['dev_id']]['humidity'])       
        except Exception as e:
            logging.error('get_humidity exception; {}'.format(e))
            return(None)
     
    def get_temp_trend(self, module):
        try:
            trend = self.weather_data[module['home_id']][module['type']][module['dev_id']]['temp_trend'])
            if trend == 'stable':
                return(trend, 0)
            elif trend == 'up':
                return(trend, 1)
            elif trend =='down':
                return(trend, -1)
            else:
                logging.error('unsupported temperature trend: {}'.format(trend))
                return(trend, None)       
        except Exception as e:
            logging.error('get_temp_trend exception; {}'.format(e))
            return( None, None)
        
    def get_battery_info(self, module):
        try:
            bat1 = self.weather_data[module['home_id']][module['type']][module['dev_id']]['battery_state']
            if bat1 == 'max':
                state = 0
            elif bat1 == 'full':
                state = 1
            elif bat1 == 'high':
                state = 2
            elif bat1 == 'medium':
                state = 3
            elif bat1 == 'low':
                state = 4
            elif bat1 == 'very low':
                state = 5
            else:
                state = 99

            bat2 = self.weather_data[module['home_id']][module['type']][module['dev_id']]['battery_level']
            return (state, bat1, bat2)
        except Exception as e:
            logging.error('get_battery_info exception; {}'.format(e))
            return( None, None)
        
    def get_rf_info(self, module):
        try:
            if 'rf_state' in self.weather_data[module['home_id']][module['type']][module['dev_id']]
                rf1 = self.weather_data[module['home_id']][module['type']][module['dev_id']]['rf_state']
            if 'wifi_state'
            rf2 = -self.weather_data[module['home_id']][module['type']][module['dev_id']]['rf_strength']
        except Exception as e:
            logging.error('get_rf_info exception; {}'.format(e))
            return(None)

    def get_online(self, module):
        try:
            logging.debug('get_online {} {} {} {}'.format(self.weather_data[module['home_id']][module['type']][module['dev_id']]['online'],module['home_id'], module['type'], module['dev_id'] ))
            return(self.weather_data[module['home_id']][module['type']][module['dev_id']]['online'])       
        except:
            return(None)


