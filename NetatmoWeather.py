
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


    def get_weather_info_cloud (self, dev_id=None):
        #logging.debug('get_weather_info_cloud')
        if dev_id:
            dev_id = urllib.parse.quote_plus(dev_id )
            api_str = '/getstationsdata?device_id='+str(dev_id)+'&get_favorites=false'
        else:
            api_str = '/getstationsdata'
        data = self._callApi('GET', api_str )
        logging.debug(data)
        return(data)
