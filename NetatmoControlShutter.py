
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
    


class NetatmoControlShutter (NetatmoCloud):
    def __init__(self):
        super().__init__()
        self.instant_data = {}
        self.cloud_data = {}
        self.control_data = {}

        self.dev_list = ['NLG', 'NLGS', 'NLV', 'NLLV', 'NLD', 'NLIV', 'Z3V', 'NLAV', 'BNMH', 'BNAB', 'BNAS', 'BNMS']
        self.gateway_list = ['NLG', 'NLGS',  'BNMH']
        self.module_list = [ 'NLV', 'NLLV', 'NLD', 'NLIV', 'Z3V', 'NLAV', 'BNAB', 'BNAS', 'BNMS']


    def update_roller_shutter_info(self, home_id):
        '''update_HC_info'''        
        