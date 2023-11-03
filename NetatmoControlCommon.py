
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
    


class NetatmoControlCommon (NetatmoCloud):
    def __init__(self):
        super().__init__()
        self.instant_data = {}
        self.cloud_data = {}
        self.control_data = {}

    def get_type_devices(self, home_id, dev_list):
        '''get_type_modules'''
        res_dict = {}
        home_modules = self.get_home_status(home_id)
        if 'modules' in home_modules:
            for module in home_modules['modules']:
                if home_modules[module]['type'] in dev_list:
                    res_dict[module] = home_modules[module]
        return(res_dict)



    def merge_data_str(self, data):
        '''merge_data_str'''
        if data == 'ts':
            data_str = 'time_stamp'
        if data == 'time_utc':
            data_str = 'time_stamp'
        elif data == 'last_seen':
            data_str = 'time_stamp'

        elif data == 'AbsolutePressure':
            data_str = 'absolute_pressure'

        elif data == 'reachable':
            data_str = 'online'

        else:
            data_str = data.lower()
        return(data_str)