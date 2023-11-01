
#!/usr/bin/env python3
from  NetatmoOauthDev import NetatmoCloud 
import urllib.parse

from oauth import OAuth
try:
    import udi_interface
    logging = udi_interface.LOGGER
    Custom = udi_interface.Custom
except ImportError:
    import logging
    logging.basicConfig(level=logging.DEBUG)



class NetatmoWeather (NetatmoCloud):
    def __init__(self):
        super().__init__()
        self.modules_possible = ['NAMain', 'NAModule1', 'NAModule2', 'NAModule3', 'NAModule4']
        self.instant_data = {}
        self.cloud_data = {}
        self.weather_data = {}
        self.MAIN_mod = 'NAMain'
        self.OUTDOOR_mod = 'NAModule1'
        self.WIND_mod = 'NAModule2'
        self.RAIN_mod = 'NAModule3'
        self.INDOOR_mod = 'NAModule4'

    # should not be necesary - filtered by token    
    #def get_weather_stations (self):
    #    logging.debug('get_weather_stations')
    #    all_systems = 


    def update_weather_info_cloud (self, home_id):
        ''' Polls latest data stored in cloud - more data available'''
        logging.debug('get_weather_info_cloud')
        tmp = self.get_module_info(home_id)
        self.cloud_data[home_id] = {}
        for dev_id in tmp:
            if tmp[dev_id]['type'] == self.MAIN_mod:
                
                dev_id_str = urllib.parse.quote_plus(dev_id )

                api_str = '/getstationsdata?device_id='+str(dev_id_str)+'&get_favorites=false'
                
                temp_data = self._callApi('GET', api_str )



                #test = self._callApi('GET', '/getstationsdata' )
                #logging.debug(temp_data)

                if temp_data['status'] == 'ok':
                    if len(temp_data['body']['devices'] ) == 1:
                        temp_data = temp_data['body']['devices'][0]  # there should only be 1 dev_id
                    else:
                        logging.error('Code only handles 1 main device per device_id (main station) - : {} found'.format(len(temp_data['body']['devices'])))
                        logging.error('Processing first one')
                        temp_data = temp_data['body']['devices'][0]

                    self.cloud_data[home_id] = {}
                    self.cloud_data[home_id][self.MAIN_mod] = {}
                    self.cloud_data[home_id][self.INDOOR_mod] = {}
                    self.cloud_data[home_id][self.OUTDOOR_mod] = {}
                    self.cloud_data[home_id][self.RAIN_mod] = {}
                    self.cloud_data[home_id][self.WIND_mod] = {}

                    self.cloud_data[home_id][self.MAIN_mod][dev_id] = temp_data['dashboard_data']
                    self.cloud_data[home_id][self.MAIN_mod][dev_id] ['reachable'] = temp_data['reachable']
                    self.cloud_data[home_id][self.MAIN_mod][dev_id] ['data_type'] = temp_data['data_type']

                    for module in range(0,len(temp_data['modules'])):
                        mod = temp_data['modules'][module]
                        self.cloud_data[home_id][mod['type']][mod['_id']] = mod['dashboard_data']
                        self.cloud_data[home_id][mod['type']][mod['_id']]['data_type'] = mod['data_type']

                  

                            #self.cloud_data[dev_id] = temp_data['body']


        
        #return(self.cloud_data is not None)
        return(self.cloud_data)
    
    def update_weather_info_instant(self, home_id):
        '''Polls latest data - within 10 sec '''
        logging.debug('update_weather_info_instant')
        tmp = self.get_home_status(home_id)
        if home_id not in self.instant_data:
            self.instant_data[home_id] = {}
            self.instant_data[home_id][self.MAIN_mod] = {}
            self.instant_data[home_id][self.OUTDOOR_mod] = {}
            self.instant_data[home_id][self.INDOOR_mod] = {}
            self.instant_data[home_id][self.RAIN_mod] = {}
            self.instant_data[home_id][self.WIND_mod] = {}
        if 'modules' in tmp:
            for module in tmp['modules']:
                #self.instant_data[home_id][module] = tmp['modules'][module]
                self.instant_data[home_id][tmp['modules'][module]['type']][module] = tmp['modules'][module]
        else:
            self.instant_data[home_id] = {}
            

    def merge_data(self):
        '''Merges/combines cloud data and instant data '''
        logging.debug('merge_data')
        for home_id in self.cloud_data:
            if home_id not in self.weather_data:
                self.weather_data[home_id] = {}
            for module_type in self.cloud_data[home_id]:
                if module_type not in self.weather_data[home_id]:
                    self.weather_data[home_id][module_type]= {}
                for module_adr in self.cloud_data[home_id][module_type]:
                    if module_adr not in self.weather_data[home_id][module_type]:
                        self.weather_data[home_id][module_type][module_adr]= {}                
                    # check who has leastes data - process older first
                    inst_mod_adr = self.instant_data[home_id][module_type][module_adr]
                    if module_adr['time_utc'] > inst_mod_adr ['ts']:
                        for data in inst_mod_adr:
                            if data == 'ts':
                                self.weather_data[home_id][module_type][module_adr]['time_stamp'] = inst_mod_adr['ts']
                            else:
                                self.weather_data[home_id][module_type][module_adr][data] =inst_mod_adr[data]



        NEED TO FINISH HERE


    def get_main_module_data(self, data):
        '''Get data from main module'''

        logging.debug('get_main_module_data')
        data_list = ['temperature', 'co2', 'humidity', 'noise', 'pressure', 'absolute_pressure', 'last_seen', 'ts']

        

    def get_indoor_module_data(self, home_id, dev_id=None):
        logging.debug('get_indoor_module_data')
        data_list = ['temperature', 'co2', 'humidity', 'last_seen', 'battery_state', 'ts']

    def get_outdoor_module_data(self, home_id, dev_id=None):
        logging.debug('get_outdoor_module_data')
        data_list = ['temperature', 'co2', 'humidity', 'last_seen', 'battery_state', 'ts']

    def get_rain_module_data(self, home_id, dev_id=None):
        logging.debug('get_rain_module_data')
        data_list = ['rain', 'sum_rain_1', 'sum_rail_24', 'last_seen', 'battery_state', 'ts']

    def get_wind_module_data(self, home_id, dev_id=None):
        logging.debug('get_wind_module_data')
        data_list = ['wind_strength', 'wind_angle', 'wind+gust', 'wind_gust_angle', 'last_seen', 'battery_state', 'ts']
