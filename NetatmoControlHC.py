
#!/usr/bin/env python3

from  NetatmoOauthDev import NetatmoCloud 
import urllib.parse

from oauth import OAuth

try:
    from udi_interface import LOGGER, Custom, OAuth
    logging = udi_interface.LOGGER
    Custom = udi_interface.Custom
except ImportError:
    import logging
    logging.basicConfig(level=logging.DEBUG)
    


class NetatmoControlHC (NetatmoCloud):
    def __init__(self):
        super().__init__()
        self.instant_data = {}
        self.cloud_data = {}
        self.control_data = {}
        self.dev_list = ['BNS', 'OTH', 'OTM', 'NRV', 'BNMH', 'BNTH', 'BNFC','BNTR']
        self.gateway_list = ['BNS', 'OTH', 'BNMH']
        self.module_list = [ 'OTM', 'NRV', 'BNTH', 'BNFC','BNTR']


        



    def update_HC_info(self, home_id):
        '''update_HC_info'''        

