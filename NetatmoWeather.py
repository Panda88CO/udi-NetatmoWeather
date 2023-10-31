
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
        self.module_possible = ['NAMain', 'NAModule1', 'NAModule2', 'NAModule3', 'NAModule4']
        self.instant_data = {}
        self.cloud_data = {}

        self.MAIN_mod = 'NAMain'
        self.OUTDOOR_mod = 'NAModule1'
        self.WIND_mod = 'NAModule2'
        self.RAIN_mod = 'NAModule3'
        self.INDOOR_mod = 'NAModule4'

    def update_weather_info_cloud (self, dev_id=None):
        logging.debug('get_weather_info_cloud')
        if dev_id:
            dev_id = urllib.parse.quote_plus(dev_id )
            api_str = '/getstationsdata?device_id='+str(dev_id)+'&get_favorites=false'
        else:
            api_str = '/getstationsdata'
        temp_data = self._callApi('GET', api_str )
        logging.debug(temp_data)

        self.cloud_data
        #return(self.cloud_data is not None)
        return(self.cloud_data)
    
    def update_weather_info_instant(self, home_id):
        logging.debug('get_weather_info')
        self.instant_data = self.get_home_status(home_id)




    def get_main_module_data(self, home_id, dev_id=None):
        logging.debug('get_main_module_data')
        outdoor_m0d = 'NAModule1'

    def get_indoor_module_data(self, home_id, dev_id=None):
        logging.debug('get_indoor_module_data')


    def get_outdoor_module_data(self, home_id, dev_id=None):
        logging.debug('get_outdoor_module_data')


    def get_rain_module_data(self, home_id, dev_id=None):
        logging.debug('get_rain_module_data')


    def get_wind_module_data(self, home_id, dev_id=None):
        logging.debug('get_wind_module_data')